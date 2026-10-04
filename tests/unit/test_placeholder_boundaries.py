import pytest

from fvn_translator.models import TranslationStatus, TranslationUnit, UnitType
from fvn_translator.validators import extract_placeholders, validate_unit


def _unit(source: str, target: str, **kwargs) -> TranslationUnit:
    unit = TranslationUnit(
        unit_id="synthetic",
        sequence=0,
        segment_id="synthetic",
        type=UnitType.NARRATION,
        source_text=source,
        target_text=target,
        source_fingerprint="sha256:synthetic",
        **kwargs,
    )
    unit.translation.status = TranslationStatus.TRANSLATED
    return unit


@pytest.mark.parametrize("text", ["% slope", "10% slope", "100% safe", "20% discount"])
def test_percentage_prose_does_not_infer_space_flag_conversions(text: str) -> None:
    assert extract_placeholders(text) == []
    assert not validate_unit(_unit(text, "坡度为10%。"))


def test_unambiguous_printf_formats_and_other_tokens_remain_inferred() -> None:
    text = "{i}[name]{/i}: %s %d % 8.2f % .2f % *.*f %(value) s %% %+#08.2f"
    assert extract_placeholders(text) == [
        "{i}",
        "[name]",
        "{/i}",
        "%s",
        "%d",
        "% 8.2f",
        "% .2f",
        "% *.*f",
        "%(value) s",
        "%%",
        "%+#08.2f",
    ]
    assert extract_placeholders("Value: % s", printf_format=True) == ["% s"]


@pytest.mark.parametrize("format_text", ["% 8.2f", "% .2f", "%(value) s"])
def test_inferred_space_flag_formats_cannot_be_removed(format_text: str) -> None:
    unit = _unit(f"Value: {format_text}", f"值：{format_text}")
    assert not validate_unit(unit)
    unit.target_text = "值："
    assert {issue.code for issue in validate_unit(unit)} == {"PROTECTED_TOKEN_CHANGED"}


def test_explicit_printf_semantics_protect_ambiguous_space_flag_format() -> None:
    unit = _unit("Value: % s", "值：% s", constraints={"printf_format": True})
    assert not validate_unit(unit)
    unit.target_text = "值："
    assert {issue.code for issue in validate_unit(unit)} == {"PROTECTED_TOKEN_CHANGED"}


def test_existing_declared_space_flag_token_is_not_silently_downgraded() -> None:
    unit = _unit(
        "Value: % s",
        "值：% s",
        protected_tokens=["% s"],
        constraints={"preserve_protected_tokens": True},
    )
    assert not validate_unit(unit)
    unit.target_text = "值："
    assert {issue.code for issue in validate_unit(unit)} == {"PROTECTED_TOKEN_CHANGED"}


def test_explicit_literal_mode_keeps_its_declared_scope() -> None:
    unit = _unit(
        "[Click here] % slope [name]",
        "点击这里，坡度 [name]",
        protected_tokens=["[name]"],
        constraints={"placeholder_mode": "explicit"},
    )
    assert not validate_unit(unit)
