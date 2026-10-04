from pathlib import Path

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.parser import RenPyParser
from fvn_translator.models import UnitType
from fvn_translator.profiles.base import CustomTextSink
from fvn_translator.profiles.echo_project import ARoleToPlayProfile, IntereaProfile
from fvn_translator.validators import validate_unit


def _write(source: Path, relative: str, text: str) -> None:
    path = source / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\xef\xbb\xbf" + text.replace("\n", "\r\n").encode("utf-8"))


def test_phone_story_and_ui_round_trip_preserve_control_and_resource_fields(tmp_path: Path) -> None:
    source = tmp_path / "source"
    _write(source, "game/options.rpy", 'define config.name = _("A Role to Play")\n')
    _write(
        source,
        "game/script.rpy",
        'define m = Character("{image=gui/names/speaker_danny.png}")\n'
        'define nm = DynamicCharacter("player_name", color="#fff")\n',
    )
    _write(
        source,
        "game/Week1.rpy",
        'label start:\n    nm "A dynamic speaker."\n'
        '    $ switch_dialogue(name="Dad", dialogue=conversation)\n'
        '    $ msg("Read this {i}carefully{/i}, [player_name].", who=1, status="offline")\n'
        '    $ msg(None, pic="picture_id")\n'
        '    $ msg(None, choices={0: {"jump": "accepted", "name": "Accept"},\n'
        '        1: {"name": "Refuse", "jump": "refused"}})\n'
        '    $ chat.addmessage_pc([orc_img], "[orc]", "A chat message.")\n'
        '    $ person = Interlocutor(1, name="Dad", avatar="phone/icon/dad.png")\n',
    )
    _write(source, "game/Week2.rpy", 'label accepted:\n    m "Another line."\n')
    _write(
        source,
        "game/zmessenger.rpy",
        "screen messenger():\n"
        '    $ status = Text("%s members" % count, style="txt_status", color="#fff")\n'
        "image status_typing:\n"
        '    Text(person.name + " is typing", style="txt_status")\n'
        '    Text("offline", style="txt_status")\n',
    )
    _write(
        source,
        "game/zGallery.rpy",
        "init python:\n"
        '    items.append(GalleryItem("Sketch 1", ["picture_id"], "picture_id_thumb"))\n',
    )
    _write(source, "game/ActionEditor.rpy", 'screen editor():\n    text "Editor prompt"\n')
    _write(source, "game/testing_room.rpy", 'label debugTestRoom:\n    "Debug story."\n')
    _write(source, "game/zTesting_ground.rpy", '$ msg("Developer example.")\n')
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "a-role-to-play"})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert not result.issues
    texts = {unit.source_text for unit in result.units}
    assert texts == {
        "A dynamic speaker.",
        "Dad",
        "Read this {i}carefully{/i}, [player_name].",
        "Accept",
        "Refuse",
        "A chat message.",
        "Another line.",
        "A Role to Play",
        "{image=gui/names/speaker_danny.png}",
        "Sketch 1",
        "%s members",
        " is typing",
        "offline",
    }
    choices = [unit for unit in result.units if unit.type == UnitType.MENU_CHOICE]
    assert [unit.source_text for unit in choices] == ["Accept", "Refuse"]
    assert ARoleToPlayProfile().get_character_map(source)["nm"].status == "dynamic"
    assert "nm" not in IntereaProfile().get_character_map(source)
    assert all(unit.source_text != "player_name" for unit in result.units)
    originals = {path.relative_to(source): path.read_bytes() for path in source.rglob("*.rpy")}
    targets = {
        "A dynamic speaker.": "动态角色发言。",
        "Read this {i}carefully{/i}, [player_name].": "[player_name]，请{i}仔细{/i}阅读。",
        "Accept": "接受",
        "Refuse": "拒绝",
        "A chat message.": "聊天消息。",
        "Another line.": "另一句。",
        "Sketch 1": "草图 1",
        "%s members": "%s 名成员",
        " is typing": "正在输入",
        "offline": "离线",
    }
    for unit in result.units:
        unit.target_text = targets.get(unit.source_text, unit.source_text)
        assert not [issue for issue in validate_unit(unit) if issue.severity == "error"]
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
    assert originals == {
        path.relative_to(source): path.read_bytes() for path in source.rglob("*.rpy")
    }
    story = (staging / "game/Week1.rpy").read_bytes()
    assert story.startswith(b"\xef\xbb\xbf") and b"\r\n" in story
    for expected in (
        b'"jump": "accepted"',
        b'"jump": "refused"',
        b'pic="picture_id"',
        b'name="Dad"',
        b'avatar="phone/icon/dad.png"',
        b'status="offline"',
        b'"[orc]"',
    ):
        assert expected in story
    status = next(unit for unit in result.units if unit.source_text == "%s members")
    status.target_text = "成员"
    assert any(issue.severity == "error" for issue in validate_unit(status))
    avatar = next(unit for unit in result.units if unit.source_text == "Dad")
    avatar.target_text = "爸爸"
    assert ARoleToPlayProfile().validate_project(staging, result.units).has_errors


def test_registered_expression_sinks_skip_keys_paths_calls_and_format_values() -> None:
    parser = RenPyParser(
        custom_sinks=[
            CustomTextSink(function="msg", keyword="choices", dictionary_value_key="name"),
            CustomTextSink(function="Text", literal_fragments=True),
        ]
    )
    parsed = parser.parse(
        '$ msg(None, pic="path", choices={0:{"name":"第一项", "jump":"start"},\n'
        '    1:{"name":"Second", "meta":{"name":"metadata"}}, # comment with )\n'
        '    2:{"name":lookup("dynamic"), "jump":"other"}})\n'
        "image status:\n"
        '    Text(person.name + " suffix", style="ui", font="path.ttf")\n'
        '    Text("%s members" % "name", style="ui")\n'
        '    Text(lookup("dynamic"), style="ui")\n',
        "game/script.rpy",
    )
    assert not parsed.issues
    assert [node.token.value for node in parsed.nodes] == [
        "第一项",
        "Second",
        " suffix",
        "%s members",
    ]


def test_rendering_properties_are_not_reported_as_visible_unknown_sinks() -> None:
    parsed = RenPyParser(allowed_speakers={"m"}).parse(
        'style menu_button:\n    hover_sound "sound.ogg"\n    activate_sound "click.ogg"\n'
        '    hover_thumb "thumb.png"\n    focus_mask "mask"\n'
        'transform shadow:\n    blend "max"\n'
        'label start:\n    m "A line."\n',
        "game/screens.rpy",
    )
    assert not parsed.issues
    assert [node.token.value for node in parsed.nodes] == ["A line."]


def test_parenthesized_gallery_literals_round_trip_without_guessing_dynamic_text(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source"
    _write(
        source,
        "game/zGallery.rpy",
        "screen gallery():\n"
        '    text ("{size=+5}Page   [gallery_page]{/s}")\n'
        '    text ("{size=+5}Page   0{/s}")\n'
        '    text (("Nested literal")) style "gallery_style"\n'
        '    text (_("Wrapped label"))\n'
        '    text ("[title]"):\n        size 20\n'
        '    text (currentTrack[0]) font "resource.ttf"\n'
        '    text (("%d" % value) if value != 0 else "*")\n'
        '    text ("Dynamic prefix" + name)\n'
        '    text ("Indexed")[0]\n'
        '    text ("Formatted").format(value)\n'
        '    text ("Conditional") if enabled else "Hidden"\n',
    )
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "a-role-to-play"})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert not result.issues
    assert [unit.source_text for unit in result.units] == [
        "{size=+5}Page   [gallery_page]{/s}",
        "{size=+5}Page   0{/s}",
        "Nested literal",
        "Wrapped label",
    ]
    assert len({unit.unit_id for unit in result.units}) == 4
    for unit, target in zip(
        result.units,
        [
            "{size=+5}第   [gallery_page] 页{/s}",
            "{size=+5}第   0 页{/s}",
            "嵌套括号文本",
            "包装标签",
        ],
        strict=True,
    ):
        unit.target_text = target
    before = (source / "game/zGallery.rpy").read_bytes()
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
    assert (source / "game/zGallery.rpy").read_bytes() == before
    staged = (staging / "game/zGallery.rpy").read_bytes()
    assert b'text (currentTrack[0]) font "resource.ttf"' in staged
    assert b'text ("[title]"):' in staged
    assert b'text (("%d" % value) if value != 0 else "*")' in staged
    assert b'text ("Dynamic prefix" + name)' in staged
    assert b"{/s}" in staged
