import sqlite3
from pathlib import Path

from fvn_translator.models import TranslationUnit


class StateDatabase:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA foreign_keys=ON")
        self._migrate()

    def _migrate(self) -> None:
        with self.connection:
            self.connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS units(
                    unit_id TEXT PRIMARY KEY, sequence INTEGER NOT NULL, segment_id TEXT NOT NULL,
                    scene_id TEXT, translation_status TEXT NOT NULL,
                    validation_status TEXT NOT NULL,
                    apply_status TEXT NOT NULL, revision INTEGER NOT NULL, payload TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS units_sequence ON units(sequence);
                CREATE INDEX IF NOT EXISTS units_scene ON units(scene_id, sequence);
                CREATE TABLE IF NOT EXISTS cache(
                    cache_key TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL
                );
                """
            )

    def get_metadata(self, key: str) -> str | None:
        row = self.connection.execute("SELECT value FROM metadata WHERE key=?", (key,)).fetchone()
        return None if row is None else str(row[0])

    def set_metadata(self, key: str, value: str) -> None:
        with self.connection:
            self.connection.execute(
                "INSERT INTO metadata(key,value) VALUES(?,?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )

    def rebuild(self, units: list[TranslationUnit], units_hash: str) -> None:
        rows = [
            (
                unit.unit_id,
                unit.sequence,
                unit.segment_id,
                unit.scene_id,
                unit.translation.status.value,
                unit.validation.status.value,
                unit.apply.status.value,
                unit.revision,
                unit.model_dump_json(by_alias=True, exclude_none=True),
            )
            for unit in units
        ]
        with self.connection:
            self.connection.execute("DELETE FROM units")
            self.connection.executemany("INSERT INTO units VALUES(?,?,?,?,?,?,?,?,?)", rows)
            self.connection.execute(
                "INSERT INTO metadata(key,value) VALUES('units_hash',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (units_hash,),
            )

    def close(self) -> None:
        self.connection.close()
