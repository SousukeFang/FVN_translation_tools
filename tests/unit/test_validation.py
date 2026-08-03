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
