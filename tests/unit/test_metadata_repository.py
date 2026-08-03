from fvn_translator.models import Character
from fvn_translator.storage import MetadataRepository


def test_metadata_edit_increments_version(tmp_path) -> None:
    repository = MetadataRepository(tmp_path / "characters.json", Character)
    repository.save([Character(character_id="fox", names=["Fox"])])
    changed = repository.update(
        "fox", {"description": "Calm", "confirmed": True}, id_field="character_id"
    )
    assert changed.version == 2
    assert changed.confirmed
