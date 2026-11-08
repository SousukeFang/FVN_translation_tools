from pathlib import Path

import pytest

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.lexer import RenPyLexer
from fvn_translator.models import UnitType
from fvn_translator.profiles import CustomTextSink, default_profile_registry
from fvn_translator.profiles.the_smoke_room import TheSmokeRoomProfile


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_smoke_room_detection_requires_title_and_case_sensitive_route_signature(tmp_path):
    profile = TheSmokeRoomProfile()
    _write(tmp_path, "game/options.rpy", 'define config.name = _("The Smoke Room")\n')
    assert not profile.detect(tmp_path).supported
    for name in profile.story_files:
        _write(tmp_path, f"game/{name}", "# Synthetic route\n")
    assert profile.detect(tmp_path).supported
    registry = default_profile_registry()
    assert registry.create("the-smoke-room").profile_id == profile.profile_id
    assert [item.profile_id for item in registry.all() if item.detect(tmp_path).supported] == [
        profile.profile_id
    ]
    rules = profile.get_file_rules()
    assert rules.categories["characters"] == ("game/script.rpy", "game/recolorsbase.rpy")
    assert "game/credits.rpy" in rules.categories["ui"]


def test_journal_values_and_rebuilds_round_trip_without_resource_or_control_values(tmp_path):
    source = tmp_path / "source"
    original = (
        "init python:\r\n"
        "    journal_entries = [\r\n"
        '        {"text": "{font=notes.ttf}A clue: [clue]{/font}", "image": "note_1"},\r\n'
        '        {"text": computed_value, "image": "note_2"},\r\n'
        '        {"caption": "Not a text field", "text": "Second clue"},\r\n'
        "    ]\r\n"
        "    def rebuild():\r\n"
        '        new_entries = journal_entries = [{"text": "Restored clue", "image": "note_3"}]\r\n'
        "        return new_entries\r\n"
        'define spoiler_message = "Continue to chapter [chapter]?"\r\n'
        'define jamesimage = "resource_image"\r\n'
        'default porterfirstchoice = "branch_key"\r\n'
        'define huxley1 = ""\r\n'
        "label investigate:\r\n"
        '    $ huxley1 = "The safe clue."\r\n'
        '    $ jamesimage = "other_resource"\r\n'
        '    $ porterfirstchoice = "other_branch"\r\n'
        '    $ unregistered_text = "Developer data"\r\n'
        '    $ other_journal = [{"text": "Unregistered dictionary"}]\r\n'
        '    $ murdochchoices = "ral"\r\n'
        '    $murdochchoices = "half an hour"\r\n'
        '    $ murdochchoices = "What should I say?"\r\n'
        '    $ investigorder = "next"\r\n'
    )
    path = source / "game/screens.rpy"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"\xef\xbb\xbf" + original.encode("utf-8"))
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "the-smoke-room"})
    units = adapter.extract(source, adapter.discover_files(source, config), config).units
    assert [unit.source_text for unit in units] == [
        "{font=notes.ttf}A clue: [clue]{/font}",
        "Second clue",
        "Restored clue",
        "Continue to chapter [chapter]?",
        "The safe clue.",
        "half an hour",
        "What should I say?",
        "next",
    ]
    assert all(unit.type == UnitType.UI_TEXT for unit in units)
    targets = [
        "{font=notes.ttf}线索：[clue]{/font}",
        "第二条线索",
        "恢复的线索",
        "继续第 [chapter] 章？",
        "安全的线索。",
        "半小时",
        "我该怎么说？",
        "接下来",
    ]
    for unit, target in zip(units, targets, strict=True):
        unit.target_text = target
    staging = tmp_path / "staging"
    adapter.apply(source, staging, units, config)
    assert not adapter.validate(staging, units, config).has_errors
    assert path.read_bytes() == b"\xef\xbb\xbf" + original.encode("utf-8")
    staged = (staging / "game/screens.rpy").read_bytes()
    assert staged.startswith(b"\xef\xbb\xbf")
    assert staged.count(b"\r\n") == original.count("\r\n")
    for preserved in ("note_1", "note_2", "note_3", "resource_image", "other_branch", '"ral"'):
        assert preserved.encode() in staged


def test_assignment_literals_use_ast_columns_and_ignore_code_inside_strings(tmp_path):
    source = tmp_path / "source"
    _write(
        source,
        "game/screens.rpy",
        "init python:\n"
        '    journal_entries = [{"注释": "值", "text": "Visible clue", "image": "resource"}]\n'
        "    documentation = \"huxley1 = 'Pretend value'\"\n"
        '    huxley10 = "Different variable"\n'
        '    huxley1 = get_text("Dynamic argument")\n'
        '    huxley1 = "Implicit " "concatenation"\n'
        '    huxley1["key"] = "Subscript is not the registered variable"\n'
        '    huxley1 = "Literal clue"\n',
    )
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "the-smoke-room"})
    units = adapter.extract(source, adapter.discover_files(source, config), config).units
    assert [unit.source_text for unit in units] == ["Visible clue", "Literal clue"]


def test_smoke_room_character_variants_notifications_menus_and_formatted_text(tmp_path):
    source = tmp_path / "source"
    _write(source, "game/recolorsbase.rpy", "define masked = Character('A stranger')\n")
    _write(
        source,
        "game/script.rpy",
        "label start:\n"
        '    masked smile "Good evening, [name]."\n'
        '    $ renpy.notify("Notebook updated.")\n'
        '    $ timer = Text("Seconds: %02d" % seconds, font="resource.ttf")\n'
        "    menu:\n"
        '        "Follow the clue" if ready:\n'
        "            jump investigate\n",
    )
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "the-smoke-room"})
    units = adapter.extract(source, adapter.discover_files(source, config), config).units
    assert [unit.source_text for unit in units] == [
        "A stranger",
        "Good evening, [name].",
        "Notebook updated.",
        "Seconds: %02d",
        "Follow the clue",
    ]
    assert [unit.type for unit in units] == [
        UnitType.CHARACTER_NAME,
        UnitType.DIALOGUE,
        UnitType.NOTIFICATION,
        UnitType.UI_TEXT,
        UnitType.MENU_CHOICE,
    ]
    for unit, target in zip(
        units,
        ["陌生人", "[name]，晚上好。", "笔记已更新。", "剩余秒数：%02d", "追查线索"],
        strict=True,
    ):
        unit.target_text = target
    staging = tmp_path / "staging"
    adapter.apply(source, staging, units, config)
    assert not adapter.validate(staging, units, config).has_errors
    assert "if ready:" in (staging / "game/script.rpy").read_text(encoding="utf-8")
    units[3].target_text = "剩余秒数：%d"
    assert adapter.validate(staging, units, config).has_errors


@pytest.mark.parametrize(
    "options",
    [{}, {"function": "Text", "assignment_target": "notes"}, {"assignment_target": "obj.notes"}],
)
def test_custom_sink_rejects_ambiguous_or_dynamic_assignment_locators(options):
    with pytest.raises(ValueError):
        CustomTextSink(**options)


def test_multiline_simple_renpy_strings_and_temporary_attributes_round_trip(tmp_path):
    source = tmp_path / "source"
    _write(source, "game/script.rpy", "define fox = Character('Fox')\n")
    original = (
        "label start:\n"
        '    "A physical line\n'
        'followed by another line."\n'
        '    fox @talking "Hello."\n'
        '    fox neutral @ talking -angry "Goodbye."\n'
    )
    _write(source, "game/commonroute.rpy", original)
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "the-smoke-room"})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert not result.issues
    assert [unit.source_text for unit in result.units] == [
        "A physical line followed by another line.",
        "Hello.",
        "Goodbye.",
        "Fox",
    ]
    assert result.units[1].adapter_data["speaker_attributes"] == ["@", "talking"]
    assert result.units[2].adapter_data["speaker_attributes"] == [
        "neutral",
        "@",
        "talking",
        "-angry",
    ]
    for unit, target in zip(
        result.units, ["第一行与第二行。", "你好。", "再见。", "Fox"], strict=True
    ):
        unit.target_text = target
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
    assert (source / "game/commonroute.rpy").read_text(encoding="utf-8") == original
    assert 'fox @talking "你好。"' in (staging / "game/commonroute.rpy").read_text(encoding="utf-8")


@pytest.mark.parametrize("valid_prefix", ["", "fox "])
def test_multiline_recovery_does_not_swallow_the_following_statement(valid_prefix):
    result = RenPyLexer().scan(f'"Broken\n{valid_prefix}"Valid"\n', "game/test.rpy")
    assert [issue.code for issue in result.issues] == ["RENPY_UNCLOSED_STRING"]
    assert [token.value for token in result.strings] == ["Valid"]


def test_physical_wrapping_normalizes_before_decoding_explicit_newline_and_not_python():
    from fvn_translator.adapters.renpy.parser import RenPyParser

    parsed = RenPyParser(custom_sinks=[CustomTextSink(assignment_target="notes")]).parse(
        "label start:\n"
        '    "First   line\\nSecond\n'
        '    physical line."\n'
        '    "Repeated   spaces."\n'
        "    menu:\n"
        '        "A choice\n'
        '         across lines":\n'
        "            pass\n"
        "init python:\n"
        '    notes = """Python\n'
        'text"""\n',
        "game/test.rpy",
    )
    assert not parsed.issues
    assert [node.token.value for node in parsed.nodes] == [
        "First line\nSecond physical line.",
        "Repeated spaces.",
        "A choice across lines",
        "Python\ntext",
    ]
    assert parsed.nodes[0].token.raw_content == "First   line\\nSecond\n    physical line."


def test_nested_menu_exit_restores_outer_choice_classification():
    from fvn_translator.adapters.renpy.parser import RenPyParser

    parsed = RenPyParser().parse(
        "label start:\n"
        "    menu:\n"
        '        "Outer caption"\n'
        '        "First outer choice":\n'
        "            menu:\n"
        '                "Inner choice":\n'
        '                    "Inner narration."\n'
        '        "Second outer choice" if available:\n'
        "            pass\n"
        '    "After the menu."\n',
        "game/test.rpy",
    )
    assert not parsed.issues
    assert [node.unit_type for node in parsed.nodes] == [
        UnitType.NARRATION,
        UnitType.MENU_CHOICE,
        UnitType.MENU_CHOICE,
        UnitType.NARRATION,
        UnitType.MENU_CHOICE,
        UnitType.NARRATION,
    ]
