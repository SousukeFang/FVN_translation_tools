import pytest

from fvn_translator.core.hashing import bytes_hash
from fvn_translator.models import TranslationStatus, TranslationUnit, UnitType
from fvn_translator.validators import validate_unit


def test_protected_tokens_must_survive() -> None:
    unit = TranslationUnit(
        unit_id="u",
        sequence=0,
        segment_id="a",
        type=UnitType.DIALOGUE,
        source_text="Go {i}now{/i}",
        target_text="现在走",
        source_fingerprint=bytes_hash(b"x"),
        protected_tokens=["{i}", "{/i}"],
    )
    unit.translation.status = TranslationStatus.TRANSLATED
    assert {issue.code for issue in validate_unit(unit)} == {"PROTECTED_TOKEN_CHANGED"}


@pytest.mark.parametrize("status", ["pending", "in_progress", "failed", "skipped"])
@pytest.mark.parametrize("explicit", [False, True])
def test_absent_draft_leaves_source_tokens_intact(status: str, explicit: bool) -> None:
    unit = TranslationUnit(
        unit_id="pending",
        sequence=0,
        segment_id="scene",
        type=UnitType.DIALOGUE,
        source_text="{i}Hello [player]{/i}",
        source_fingerprint=bytes_hash(b"source"),
        protected_tokens=["{i}", "[player]", "{/i}"],
        constraints={"placeholder_mode": "explicit"} if explicit else {},
    )
    unit.translation.status = TranslationStatus(status)
    assert validate_unit(unit) == []
    # A nonempty draft must still preserve tokens, even before it is completed.
    unit.target_text = "你好"
    assert {issue.code for issue in validate_unit(unit)} == {"PROTECTED_TOKEN_CHANGED"}


@pytest.mark.parametrize("status", ["translated", "reviewed"])
def test_completed_empty_target_still_fails(status: str) -> None:
    unit = TranslationUnit(
        unit_id="empty",
        sequence=0,
        segment_id="scene",
        type=UnitType.NARRATION,
        source_text="Hello",
        source_fingerprint=bytes_hash(b"source"),
    )
    unit.translation.status = TranslationStatus(status)
    assert {issue.code for issue in validate_unit(unit)} == {"TARGET_EMPTY"}
