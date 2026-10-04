from pathlib import Path

import pytest

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.models import UnitType
from fvn_translator.profiles import default_profile_registry
from fvn_translator.profiles.echo_project import EchoRoute65Profile, IntereaProfile, KhemiaProfile


def _write(source: Path, relative: str, text: str) -> None:
    path = source / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.mark.parametrize("factory", [EchoRoute65Profile, KhemiaProfile, IntereaProfile])
def test_echo_profiles_require_distinct_title_and_story_signature(tmp_path, factory) -> None:
    profile = factory()
    _write(tmp_path, "game/options.rpy", f'define config.name = _("{profile.title}")\n')
    assert not profile.detect(tmp_path).supported
    for filename in profile.story_files:
        _write(tmp_path, f"game/{filename}", 'label scene_start:\n    "Narration."\n')
    assert profile.detect(tmp_path).supported
    registry = default_profile_registry()
    assert registry.create(profile.profile_id).profile_id == profile.profile_id
    assert [item.profile_id for item in registry.all() if item.detect(tmp_path).supported] == [
        profile.profile_id
    ]


def test_profile_keeps_story_and_ui_while_rejecting_style_and_backend_strings(
    tmp_path: Path,
) -> None:
    _write(tmp_path, "game/script.rpy", "define fox = Character('Fox', color='#fff')\n")
    _write(
        tmp_path,
        "game/a1s1.rpy",
        'label start:\n    fox happy "Dialogue."\n    "Narration."\n'
        '    centered "Centered title."\n    narrator "Voiced narration."\n'
        '    extend "Continued."\n    menu:\n        "Visible choice":\n            pass\n',
    )
    _write(
        tmp_path,
        "game/screens.rpy",
        'style say_dialogue:\n    font "resource.ttf"\n    language "unicode"\n'
        '    layout "subtitle"\n    hover_color "#fff"\n'
        'screen main_menu():\n    textbutton _("Start") action Start()\n'
        '    text "Visible screen" style "resource_style"\n'
        '    text title layout "subtitle"\n',
    )
    _write(tmp_path, "game/gui.rpy", 'define gui.text_font = "resource.ttf"\n')
    _write(tmp_path, "game/options.rpy", 'define config.name = _("Khemia")\n')
    _write(tmp_path, "game/music_room/music_room.rpy", 'screen music():\n    text _("Music")\n')
    _write(
        tmp_path,
        "game/music_room/01_music_room_backend.rpy",
        '"""Developer documentation."""\n',
    )
    _write(tmp_path, "game/textbox_transitions.rpy", '"""Module documentation."""\n')
    _write(tmp_path, "game/tl/spanish/story.rpy", '"Existing translation."\n')
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "khemia"})
    files = adapter.discover_files(tmp_path, config)
    assert not any("backend" in file.relative_path for file in files)
    result = adapter.extract(tmp_path, files, config)
    assert [unit.source_text for unit in result.units] == [
        "Dialogue.",
        "Narration.",
        "Centered title.",
        "Voiced narration.",
        "Continued.",
        "Visible choice",
        "Music",
        "Khemia",
        "Start",
        "Visible screen",
        "Fox",
    ]
    title = next(unit for unit in result.units if unit.source_text == "Khemia")
    assert "Khemia" in title.protected_tokens
    assert next(unit for unit in result.units if unit.speaker == "narrator").type == (
        UnitType.NARRATION
    )
    assert next(unit for unit in result.units if unit.speaker == "centered").type == (
        UnitType.SCREEN_TEXT
    )


def test_multiline_character_definitions_and_visible_calls_round_trip(tmp_path: Path) -> None:
    source = tmp_path / "source"
    original = (
        "define fox = Character(\r\n"
        "    'Fox',\r\n"
        "    color='#fff', image='resource')\r\n"
        "init:\r\n"
        "    $ computer = Character(\r\n"
        "        color='#fff',\r\n"
        "        name='Computer', image='terminal')\r\n"
        "    $ nameless = Character(' ', image='unknown')\r\n"
        "label start:\r\n"
        '    fox "Hello."\r\n'
        '    computer "Ready."\r\n'
        "    $ reply = renpy.input(\r\n"
        '        "What is your name?")\r\n'
        "    $ renpy.notify(\r\n"
        '        "Saved.")\r\n'
    )
    script = source / "game/script.rpy"
    script.parent.mkdir(parents=True)
    script.write_bytes(b"\xef\xbb\xbf" + original.encode("utf-8"))
    profile = IntereaProfile()
    names = profile.get_character_map(source)
    assert names["fox"].display_name == "Fox"
    assert names["computer"].display_name == "Computer"
    assert names["nameless"].display_name is None
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "interea"})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert [unit.source_text for unit in result.units] == [
        "Fox",
        "Computer",
        "Hello.",
        "Ready.",
        "What is your name?",
        "Saved.",
    ]
    assert [unit.type for unit in result.units] == [
        UnitType.CHARACTER_NAME,
        UnitType.CHARACTER_NAME,
        UnitType.DIALOGUE,
        UnitType.DIALOGUE,
        UnitType.INPUT_PROMPT,
        UnitType.NOTIFICATION,
    ]
    for unit in result.units:
        unit.target_text = f"中文：{unit.source_text}"
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
    staged = (staging / "game/script.rpy").read_bytes()
    assert staged.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in staged
    assert b"image='resource'" in staged and b"image='terminal'" in staged


def test_route65_blank_name_context_does_not_create_translation_units(tmp_path: Path) -> None:
    _write(
        tmp_path,
        "game/script.rpy",
        "init:\n    $ k = Character(' ', show_who_window_style='say_karen')\n"
        "    $ ku = Character(' ', show_who_window_style='say_kud')\n"
        '# define fake = Character("Comment name")\n'
        "init python:\n    documentation = \"define fake2 = Character('String name')\"\n"
        'label start:\n    k "A bus driver speaks."\n    ku "A different person."\n',
    )
    profile = EchoRoute65Profile()
    names = profile.get_character_map(tmp_path)
    assert names["k"].display_name == "Karen"
    assert names["ku"].display_name == "Kudzu"
    assert "fake" not in names and "fake2" not in names
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "echo-route-65"})
    result = adapter.extract(tmp_path, adapter.discover_files(tmp_path, config), config)
    assert [unit.source_text for unit in result.units] == [
        "A bus driver speaks.",
        "A different person.",
    ]


def test_explicit_speaker_literal_is_translated_and_validated_with_dialogue(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _write(
        source,
        "game/script.rpy",
        'label start:\n    "An anonymous voice" "Hello."\n    extend "Still here."\n',
    )
    adapter = RenPyAdapter()
    config = AdapterConfig()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert [unit.type for unit in result.units] == [
        UnitType.CHARACTER_NAME,
        UnitType.DIALOGUE,
        UnitType.DIALOGUE_EXTENSION,
    ]
    name, dialogue, extension = result.units
    assert dialogue.adapter_data["explicit_display_name_unit_id"] == name.unit_id
    assert extension.adapter_data["extends_unit_id"] == dialogue.unit_id
    name.target_text = "一个匿名的声音"
    dialogue.target_text = "你好。"
    extension.target_text = "还在这里。"
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
    assert '"一个匿名的声音" "你好。"' in (staging / "game/script.rpy").read_text(encoding="utf-8")


def test_blank_explicit_name_does_not_link_to_a_previous_speaker(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _write(
        source,
        "game/script.rpy",
        'label start:\n    "A voice" "Hello."\n    " " "Different nameless voice."\n',
    )
    adapter = RenPyAdapter()
    config = AdapterConfig()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert len(result.units) == 3
    assert "explicit_display_name_unit_id" not in result.units[-1].adapter_data
    for unit, translated in zip(
        result.units, ["一个声音", "你好。", "另一道无名的声音。"], strict=True
    ):
        unit.target_text = translated
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
