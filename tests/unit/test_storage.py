from fvn_translator.core.hashing import bytes_hash
from fvn_translator.models import TranslationUnit, UnitType
from fvn_translator.storage import StateDatabase, UnitRepository


def test_repository_rebuilds_database(tmp_path) -> None:
    database = StateDatabase(tmp_path / "state.sqlite3")
    repository = UnitRepository(tmp_path / "units.jsonl", database)
    unit = TranslationUnit(
        unit_id="u1",
        sequence=0,
        segment_id="a",
        type=UnitType.NARRATION,
        source_text="Hello",
        source_fingerprint=bytes_hash(b"Hello"),
    )
    repository.save([unit])
    database.connection.execute("DELETE FROM units")
    database.set_metadata("units_hash", "stale")
    assert repository.load()[0].unit_id == "u1"
    assert database.connection.execute("SELECT COUNT(*) FROM units").fetchone()[0] == 1
    database.close()
