import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.core.hashing import file_hash
from fvn_translator.core.paths import ensure_within


class BackupService:
    def __init__(self, backups_root: Path) -> None:
        self.backups_root = backups_root

    def create(self, source_root: Path, relative_paths: list[str]) -> str:
        backup_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ-") + uuid4().hex[:8]
        root = self.backups_root / backup_id
        records = []
        for relative in sorted(set(relative_paths)):
            source = ensure_within(source_root, source_root / relative)
            target = ensure_within(root / "files", root / "files" / relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            records.append({"path": relative, "hash": file_hash(target)})
        atomic_write_json(
            root / "backup.json",
            {"backup_id": backup_id, "created_at": datetime.now(UTC).isoformat(), "files": records},
        )
        return backup_id
