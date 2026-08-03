from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from fvn_translator.core.atomic_io import atomic_write_jsonl


class RevisionStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, *, unit_id: str, before: str, after: str, origin: str) -> dict[str, Any]:
        rows = self.read()
        revision = {
            "revision_id": uuid4().hex,
            "unit_id": unit_id,
            "before": before,
            "after": after,
            "origin": origin,
            "created_at": datetime.now(UTC).isoformat(),
        }
        rows.append(revision)
        atomic_write_jsonl(self.path, rows)
        return revision

    def read(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        import json

        return [
            json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line
        ]
