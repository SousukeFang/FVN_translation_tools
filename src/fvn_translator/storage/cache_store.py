import json
from datetime import UTC, datetime

from .state_database import StateDatabase


class CacheStore:
    def __init__(self, database: StateDatabase) -> None:
        self.database = database

    def get(self, key: str) -> dict[str, object] | None:
        row = self.database.connection.execute(
            "SELECT payload FROM cache WHERE cache_key=?", (key,)
        ).fetchone()
        return None if row is None else json.loads(row[0])

    def set(self, key: str, payload: dict[str, object]) -> None:
        with self.database.connection:
            self.database.connection.execute(
                "INSERT INTO cache(cache_key,payload,created_at) VALUES(?,?,?) "
                "ON CONFLICT(cache_key) DO UPDATE SET "
                "payload=excluded.payload,created_at=excluded.created_at",
                (key, json.dumps(payload, ensure_ascii=False), datetime.now(UTC).isoformat()),
            )
