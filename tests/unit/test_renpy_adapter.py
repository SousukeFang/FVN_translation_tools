from pathlib import Path
from types import SimpleNamespace

import pytest

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.lexer import RenPyLexer
from fvn_translator.adapters.renpy.lint import RenPyLintRunner
from fvn_translator.adapters.renpy.protected_tokens import (
    compare_signatures,
    protection_signature,
)
from fvn_translator.adapters.renpy.remap import RemapStatus, remap_units
from fvn_translator.models import UnitType
from fvn_translator.profiles.remember_the_flowers import RememberTheFlowersProfile


def test_lexer_handles_comments_quotes_triples_and_locations() -> None:
    text = 'e "hash # and {a=\'quoted\'}" # comment\n"""multi\nline"""\n'
    result = RenPyLexer().scan(text, "game/test.rpy")
    assert not result.issues
    assert [token.value for token in result.strings] == [
        "hash # and {a='quoted'}",
        "multi\nline",
    ]
    assert result.strings[0].start_line == 1
    assert result.strings[1].end_line == 3
    assert result.comments[0].text.strip() == "comment"


def test_lexer_recovers_after_invalid_string() -> None:
    result = RenPyLexer().scan('"broken\n"valid"\n', "game/test.rpy")
    assert [issue.code for issue in result.issues] == ["RENPY_UNCLOSED_STRING"]
    assert result.strings[-1].value == "valid"


def test_f_string_is_reported_but_not_extracted() -> None:
    from fvn_translator.adapters.renpy.parser import RenPyParser

    parsed = RenPyParser().parse('label start:\n    f"Hello {name}"\n', "game/test.rpy")
    assert not parsed.nodes
    assert [issue.code for issue in parsed.issues] == ["RENPY_UNSUPPORTED_STRING_PREFIX"]


def test_generic_extraction_covers_supported_syntax() -> None:
    source = Path("tests/fixtures/renpy_generic/source")
    adapter = RenPyAdapter()
    files = adapter.discover_files(source, AdapterConfig())
    result = adapter.extract(source, files, AdapterConfig())
    assert not result.issues
    assert len(result.units) == 15
    assert [unit.type for unit in result.units[:8]] == [
        UnitType.NARRATION,
        UnitType.DIALOGUE,
        UnitType.DIALOGUE,
        UnitType.DIALOGUE,
        UnitType.DIALOGUE_EXTENSION,
        UnitType.SCREEN_TEXT,
        UnitType.MENU_CHOICE,
        UnitType.MENU_CHOICE,
    ]
    assert result.units[2].speaker == "eileen"
    assert result.units[2].adapter_data["speaker_attributes"] == ["angry"]
    assert result.units[4].adapter_data["extends_unit_id"] == result.units[3].unit_id
    assert "{i}" in result.units[0].protected_tokens
    assert "[player_name]" in result.units[0].protected_tokens


def test_profile_detection_character_map_and_real_samples() -> None:
    source = Path("tests/fixtures/remember_the_flowers/source")
    profile = RememberTheFlowersProfile()
    assert profile.detect(source).supported
    characters = profile.get_character_map(source)
    assert characters["Lan2"].display_name == "Lance"
    assert characters["centernar2"].status == "unresolved"
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": profile.profile_id})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert len(result.units) == 9
    touching = next(unit for unit in result.units if unit.source_text == "{i}Damnit...{/i}")
    assert touching.speaker == "Lan2"
    assert touching.adapter_data["speaker_attributes"] == [
        "EARS02",
        "M0104",
        "E1T306P6",
        "SWEAT",
    ]
    assert [unit.type for unit in result.units[-2:]] == [
        UnitType.NOTIFICATION,
        UnitType.INPUT_PROMPT,
    ]


def test_character_map_does_not_treat_keyword_resource_as_display_name(
    tmp_path: Path,
) -> None:
    from fvn_translator.profiles.remember_the_flowers.character_map import load_character_map

    names = tmp_path / "game/characters/names.rpy"
    names.parent.mkdir(parents=True)
    names.write_text(
        'define base = Character(ctc=Blink("images/ctc.webp"))\n'
        'define named = Character(name="Name", image="sprite")\n',
        encoding="utf-8",
    )
    characters = load_character_map(tmp_path)
    assert characters["base"].status == "unresolved"
    assert characters["named"].display_name == "Name"


def test_python_docstrings_are_not_extracted_but_translation_calls_are() -> None:
    from fvn_translator.adapters.renpy.parser import RenPyParser

    parsed = RenPyParser().parse(
        'init python:\n    """Developer documentation."""\n    title = _("Visible")\n',
        "game/code.rpy",
    )
    assert [node.token.value for node in parsed.nodes] == ["Visible"]


def test_profile_reports_unknown_say_like_statement(tmp_path: Path) -> None:
    source = tmp_path / "source"
    names = source / "game/characters/names.rpy"
    script = source / "game/story/prologue.rpy"
    options = source / "game/options.rpy"
    names.parent.mkdir(parents=True)
    script.parent.mkdir(parents=True)
    names.write_text('define fox = Character("Fox")\n', encoding="utf-8")
    options.write_text('define config.name = "Remember the Flowers - Part II"\n', encoding="utf-8")
    script.write_text('label start:\n    mystery "Visible?"\n', encoding="utf-8")
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "remember-the-flowers-ii"})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    assert not result.units
    assert [issue.code for issue in result.issues] == ["RENPY_UNKNOWN_TEXT_SINK"]


def test_custom_sink_can_select_nonzero_literal_argument() -> None:
    from fvn_translator.adapters.renpy.parser import RenPyParser
    from fvn_translator.profiles.base import CustomTextSink

    parsed = RenPyParser(
        custom_sinks=[CustomTextSink(function="visible", argument=1, unit_type=UnitType.UI_TEXT)]
    ).parse('$ visible("internal", "Player text")\n', "game/test.rpy")
    assert [node.token.value for node in parsed.nodes] == ["Player text"]


def test_round_trip_preserves_bom_crlf_and_structure(tmp_path: Path) -> None:
    source = tmp_path / "source"
    path = source / "game/script.rpy"
    path.parent.mkdir(parents=True)
    original = b'\xef\xbb\xbflabel start:\r\n    fox happy"Hello {i}[name]{/i}."\r\n'
    path.write_bytes(original)
    adapter = RenPyAdapter()
    config = AdapterConfig()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    unit = result.units[0]
    unit.target_text = "你好 {i}[name]{/i}。"
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    rendered = (staging / "game/script.rpy").read_bytes()
    assert rendered.startswith(b"\xef\xbb\xbf")
    assert b"\r\n" in rendered
    assert b'fox happy"' in rendered
    assert not adapter.validate(staging, result.units, config).has_errors


def test_writer_rejects_protected_token_loss(tmp_path: Path) -> None:
    source = tmp_path / "source"
    path = source / "game/script.rpy"
    path.parent.mkdir(parents=True)
    path.write_text('label start:\n    "Hello {i}[name]{/i}."\n', encoding="utf-8")
    adapter = RenPyAdapter()
    config = AdapterConfig()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    result.units[0].target_text = "你好。"
    with pytest.raises(ValueError, match="Protected content changed"):
        adapter.apply(source, tmp_path / "staging", result.units, config)


def test_full_staging_copies_nontranslated_project_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    script = source / "game/script.rpy"
    asset = source / "game/images/portrait.webp"
    script.parent.mkdir(parents=True)
    asset.parent.mkdir(parents=True)
    script.write_text('label start:\n    "Hello."\n', encoding="utf-8")
    asset.write_bytes(b"fixture-asset")
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"full_staging": True})
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert (staging / "game/images/portrait.webp").read_bytes() == b"fixture-asset"


def test_structure_validator_detects_control_flow_change(tmp_path: Path) -> None:
    source = Path("tests/fixtures/renpy_generic/source")
    adapter = RenPyAdapter()
    config = AdapterConfig()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    script = staging / "game/script.rpy"
    script.write_text(
        script.read_text(encoding="utf-8").replace("jump chosen", "jump altered"),
        encoding="utf-8",
    )
    codes = {issue.code for issue in adapter.validate(staging, result.units, config).issues}
    assert "RENPY_STRUCTURE_CHANGED" in codes


def test_lint_failure_is_parsed_and_linked(tmp_path: Path, monkeypatch) -> None:
    sdk = tmp_path / "sdk"
    sdk.mkdir()
    (sdk / "renpy.exe").write_bytes(b"fixture")
    source = Path("tests/fixtures/renpy_generic/source")
    adapter = RenPyAdapter()
    result = adapter.extract(
        source, adapter.discover_files(source, AdapterConfig()), AdapterConfig()
    )

    def fake_run(*args, **kwargs):
        return SimpleNamespace(
            returncode=1,
            stdout="game/script.rpy:3 lint problem",
            stderr="",
        )

    monkeypatch.setattr("fvn_translator.adapters.renpy.lint.subprocess.run", fake_run)
    report = RenPyLintRunner().run(tmp_path / "staging", sdk_path=sdk, units=result.units)
    assert report.issues[0].code == "RENPY_LINT_FAILED"
    assert report.issues[0].path == "game/script.rpy"
    assert report.issues[0].unit_id == result.units[0].unit_id


def test_protection_signature_preserves_order_and_duplicates() -> None:
    expected = protection_signature("{i}[name]{/i} [name]", r"{i}[name]{/i} [name]")
    actual = protection_signature("{i}[name]{/i}", r"{i}[name]{/i}")
    issues = compare_signatures(expected, actual)
    assert [issue.code for issue in issues] == ["RENPY_INTERPOLATION_MISMATCH"]


def test_incremental_remap_never_selects_ambiguous_candidate() -> None:
    source = Path("tests/fixtures/renpy_generic/source")
    adapter = RenPyAdapter()
    first = adapter.extract(
        source, adapter.discover_files(source, AdapterConfig()), AdapterConfig()
    )
    same = [unit.model_copy(deep=True) for unit in first.units]
    assert all(item.status == RemapStatus.UNCHANGED for item in remap_units(first.units, same))
    duplicate = first.units[0].model_copy(deep=True)
    duplicate.unit_id = "duplicate"
    conflict = remap_units([first.units[0], duplicate], [same[0]])[0]
    assert conflict.status == RemapStatus.CONFLICT
    assert set(conflict.candidates) == {first.units[0].unit_id, "duplicate"}
