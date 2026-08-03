import json
import os
import shutil
from pathlib import Path

from fvn_translator.core.hashing import file_hash
from fvn_translator.core.paths import ensure_within


class RollbackService:
    def __init__(self, backups_root: Path) -> None:
        self.backups_root = backups_root

    def rollback(self, backup_id: str, source_root: Path) -> list[str]:
        root = self.backups_root / backup_id
        manifest = json.loads((root / "backup.json").read_text(encoding="utf-8"))
        restored = []
        for record in manifest["files"]:
            backup = ensure_within(root / "files", root / "files" / record["path"])
            if file_hash(backup) != record["hash"]:
                raise ValueError(f"Backup is damaged: {record['path']}")
            target = ensure_within(source_root, source_root / record["path"])
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.rollback.tmp")
            shutil.copy2(backup, temporary)
            os.replace(temporary, target)
            restored.append(record["path"])
        return restored
