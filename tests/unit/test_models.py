from fvn_translator.core.hashing import bytes_hash
from fvn_translator.models import TranslationUnit, UnitType


def test_unit_round_trip() -> None:
    unit = TranslationUnit(
        unit_id="u1",
        sequence=0,
        segment_id="a",
        type=UnitType.DIALOGUE,
        source_text="Hi",
        source_fingerprint=bytes_hash(b"Hi"),
    )
    restored = TranslationUnit.model_validate_json(unit.model_dump_json(by_alias=True))
    assert restored == unit
    assert restored.model_dump(by_alias=True)["schema"] == "ftif-unit/v1"
