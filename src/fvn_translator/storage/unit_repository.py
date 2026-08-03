from pathlib import Path

from fvn_translator.core.hashing import file_hash
from fvn_translator.models import TranslationUnit

from .jsonl_store import JSONLStore
from .state_database import StateDatabase


class UnitRepository:
    def __init__(self, path: Path, database: StateDatabase | None = None) -> None:
        self.path = path
        self.store = JSONLStore(path, TranslationUnit)
        self.database = database

    def load(self) -> list[TranslationUnit]:
        units = self.store.read()
        if self.database and self.path.exists():
            current_hash = file_hash(self.path)
            if self.database.get_metadata("units_hash") != current_hash:
                self.database.rebuild(units, current_hash)
        return sorted(units, key=lambda value: value.sequence)

    def save(self, units: list[TranslationUnit]) -> None:
        ids = [unit.unit_id for unit in units]
        if len(ids) != len(set(ids)):
            raise ValueError("unit_id values must be unique")
        sequences = [unit.sequence for unit in units]
        if len(sequences) != len(set(sequences)):
            raise ValueError("sequence values must be unique")
        self.store.write(sorted(units, key=lambda value: value.sequence))
        if self.database:
            self.database.rebuild(units, file_hash(self.path))

    def update(self, changed: TranslationUnit) -> None:
        units = self.load()
        for index, unit in enumerate(units):
            if unit.unit_id == changed.unit_id:
                units[index] = changed
                self.save(units)
                return
        raise KeyError(changed.unit_id)
