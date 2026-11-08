from pathlib import Path

import pytest

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.parser import RenPyParser
from fvn_translator.adapters.renpy.protected_tokens import (
    compare_signatures,
    protection_signature,
)
from fvn_translator.adapters.renpy.text_codec import (
    RENPY_TEXT_ESCAPES,
    decode_renpy_text_content,
)
from fvn_translator.adapters.renpy.writer import encode_string_content
from fvn_translator.profiles import CustomTextSink


@pytest.mark.parametrize(
    ("raw", "decoded"),
    [
        (r"before\Tafter", "beforeTafter"),
        (r"before\iafter", "beforeiafter"),
        (r"before\’after", "before’after"),
        (r"before\tafter", "beforetafter"),
        (r"before\rafter", "beforerafter"),
        (r"before\nafter", "before\nafter"),
        (r"before\u4E2Dafter", "before中after"),
        (r"before\u4 after", "before\x04 after"),
        (r"before\u12345 after", "before\u12345 after"),
        (r"before\uZafter", "beforeZafter"),
        (r"before\U0001F600after", "beforeU0001F600after"),
        (r"before\x41after", "beforex41after"),
        (r"before\{color=red}after", "before{{color=red}after"),
        (r"before\[name]after", "before[[name]after"),
        (r"before\%after", "before%%after"),
        (r"before\"after", 'before"after'),
        (r"before\'after", "before'after"),
        (r"before\\after", "before\\after"),
        ("before   after", "before after"),
        ("before\n   after", "before after"),
        ("before\tafter", "before\tafter"),
        ("before\rafter", "before\rafter"),
        ("before\\\nafter", "before after"),
        (r"before\   after", "before after"),
        ("{{ [[ %%", "{{ [[ %%"),
    ],
)
def test_renpy_string_cases_proven_against_official_852_lexer(raw, decoded):
    assert decode_renpy_text_content(raw) == decoded


@pytest.mark.filterwarnings("ignore:invalid escape sequence:SyntaxWarning")
def test_codec_mode_is_only_set_for_ordinary_renpy_text_and_explicit_names():
    parsed = RenPyParser(
        custom_sinks=[CustomTextSink(function="visible"), CustomTextSink(assignment_target="notes")]
    ).parse(
        "label start:\n"
        '    "A\\Tvoice" "Hello\\i."\n'
        '    extend "More\\N."\n'
        "    menu:\n"
        '        "A\\Tchoice":\n'
        "            pass\n"
        '    r"Raw\\T  text"\n'
        '    """Triple\\T text"""\n'
        '    $ visible("Function\\T text")\n'
        '    $ notes = "Assignment\\T text"\n'
        "screen test():\n"
        '    text "Screen\\T text"\n',
        "game/test.rpy",
    )
    assert not parsed.issues
    assert [node.token.value for node in parsed.nodes] == [
        "ATvoice",
        "Helloi.",
        "MoreN.",
        "ATchoice",
        r"Raw\T  text",
        r"Triple\T text",
        r"Function\T text",
        r"Assignment\T text",
        r"Screen\T text",
    ]
    assert all(node.context.get("escape_mode") == RENPY_TEXT_ESCAPES for node in parsed.nodes[:4])
    assert all("escape_mode" not in node.context for node in parsed.nodes[4:])
    assert parsed.nodes[1].speaker == parsed.nodes[1].explicit_display_name == "ATvoice"


def test_meaningless_escape_spelling_is_ignored_only_with_explicit_new_mode():
    raw = r"word\T and \i"
    decoded = decode_renpy_text_content(raw)
    legacy = protection_signature(decoded, raw)
    semantic = protection_signature(decoded, raw, escape_mode=RENPY_TEXT_ESCAPES)
    assert legacy["escapes"] == [r"\T", r"\i"]
    assert semantic["escapes"] == []
    assert compare_signatures(legacy, protection_signature("译文", "译文"))
    assert not compare_signatures(
        semantic, protection_signature("译文", "译文", escape_mode=RENPY_TEXT_ESCAPES)
    )


@pytest.mark.parametrize(
    "raw",
    [r"\n", r"\u0009", "\t", r"\u000d", r"\\", r"\"", r"\%", r"\{", r"\["],
)
def test_rendered_newline_tab_cr_backslash_quotes_and_literal_escapes_stay_protected(raw):
    source = decode_renpy_text_content(raw)
    signature = protection_signature(source, raw, escape_mode=RENPY_TEXT_ESCAPES)
    assert signature["escapes"]
    assert compare_signatures(
        signature, protection_signature("", "", escape_mode=RENPY_TEXT_ESCAPES)
    )


def test_tags_and_interpolation_remain_strict_in_semantic_mode():
    original = protection_signature(
        "{i}Hello [name]{/i}", "{i}Hello [name]{/i}", escape_mode=RENPY_TEXT_ESCAPES
    )
    assert compare_signatures(
        original, protection_signature("Hello", "Hello", escape_mode=RENPY_TEXT_ESCAPES)
    )


def test_writer_round_trip_preserves_real_tabs_cr_multiple_spaces_and_literals():
    target = '  中文 "引号"，路径\\目录\t制表\r回车\n换行 {{ [[ %%  '
    rendered = encode_string_content(target, quote='"', escape_mode=RENPY_TEXT_ESCAPES)
    assert "\\u0009" in rendered and "\\u000d" in rendered
    assert "\\t" not in rendered
    assert decode_renpy_text_content(rendered) == target


def test_quotes_inside_interpolations_are_encoded_for_the_outer_renpy_literal():
    raw = r"Value [mapping[\"key\"]]"
    source = decode_renpy_text_content(raw)
    target = '值：[mapping["key"]]'
    rendered = encode_string_content(target, quote='"', escape_mode=RENPY_TEXT_ESCAPES)
    assert rendered == r"值：[mapping[\"key\"]]"
    assert decode_renpy_text_content(rendered) == target
    assert not compare_signatures(
        protection_signature(source, raw, escape_mode=RENPY_TEXT_ESCAPES),
        protection_signature(target, rendered, escape_mode=RENPY_TEXT_ESCAPES),
    )


def test_unknown_escape_translation_and_unchanged_raw_content_round_trip(tmp_path: Path):
    source = tmp_path / "source"
    (source / "game").mkdir(parents=True)
    original = 'label start:\n    "Unknown \\Tword with \\"quotes\\"."\n'
    path = source / "game/script.rpy"
    path.write_text(original, encoding="utf-8")
    adapter = RenPyAdapter()
    config = AdapterConfig()
    units = adapter.extract(source, adapter.discover_files(source, config), config).units
    assert len(units) == 1
    unit = units[0]
    assert unit.source_text == 'Unknown Tword with "quotes".'
    assert unit.adapter_data["escape_mode"] == RENPY_TEXT_ESCAPES
    assert r"\T" not in unit.protected_tokens
    staging = tmp_path / "unchanged"
    adapter.apply(source, staging, units, config)
    assert (staging / "game/script.rpy").read_bytes() == path.read_bytes()
    assert not adapter.validate(staging, units, config).has_errors
    unit.target_text = '未知词与"引号"。'
    staging = tmp_path / "translated"
    adapter.apply(source, staging, units, config)
    assert not adapter.validate(staging, units, config).has_errors
    assert r"\T" not in (staging / "game/script.rpy").read_text(encoding="utf-8")
    assert path.read_text(encoding="utf-8") == original
    unit.adapter_data.pop("escape_mode")
    unit.adapter_data["protection_signature"] = protection_signature(
        unit.source_text, unit.adapter_data["source_raw_content"]
    )
    with pytest.raises(ValueError, match="Protected content changed"):
        adapter.apply(source, tmp_path / "legacy", units, config)
