import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fvn_translator.adapters.base import AdapterConfig, FVNAdapter
from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.core.errors import ApplyConflictError
from fvn_translator.core.hashing import file_hash
from fvn_translator.core.paths import ensure_within
from fvn_translator.models import ApplyStatus, Severity
from fvn_translator.storage import UnitRepository
from fvn_translator.validators import validate_unit

from .backup_service import BackupService
from .rollback_service import RollbackService


class ApplyService:
    def __init__(
        self, repository: UnitRepository, backup: BackupService, rollback: RollbackService
    ) -> None:
        self.repository = repository
        self.backup = backup
        self.rollback = rollback

    def apply(
        self,
        adapter: FVNAdapter,
        source_root: Path,
        staging_root: Path,
        config: AdapterConfig | None = None,
    ) -> str:
        adapter_config = config or AdapterConfig()
        units = self.repository.load()
        common_issues = [issue for unit in units for issue in validate_unit(unit)]
        if any(issue.severity == Severity.ERROR for issue in common_issues):
            raise ValueError("Common validation failed; source files were not changed")
        paths = sorted({str(unit.origin["path"]) for unit in units})
        expected = {
            str(unit.origin["path"]): str(unit.origin["file_fingerprint"]) for unit in units
        }
        for relative, fingerprint in expected.items():
            source_path = ensure_within(source_root, source_root / relative)
            if file_hash(source_path) != fingerprint:
                raise ApplyConflictError(f"Source changed after extraction: {relative}")
        result = adapter.apply(source_root, staging_root, units, adapter_config)
        report = adapter.validate(staging_root, units, adapter_config)
        if any(issue.severity == Severity.ERROR for issue in report.issues):
            raise ValueError("Adapter validation failed; source files were not changed")
        backup_id = self.backup.create(source_root, paths)
        journal_path = self.backup.backups_root.parent / "state" / "apply_journal.json"
        journal: dict[str, Any] = {
            "backup_id": backup_id,
            "status": "applying",
            "files": [{"path": relative, "status": "pending"} for relative in result.written_files],
        }
        atomic_write_json(journal_path, journal)
        try:
            for index, relative in enumerate(result.written_files):
                source = ensure_within(staging_root, staging_root / relative)
                target = ensure_within(source_root, source_root / relative)
                temporary = target.with_name(f".{target.name}.apply.tmp")
                shutil.copy2(source, temporary)
                os.replace(temporary, target)
                journal["files"][index]["status"] = "replaced"
                atomic_write_json(journal_path, journal)
        except Exception:
            self.rollback.rollback(backup_id, source_root)
            journal["status"] = "failed_and_restored"
            atomic_write_json(journal_path, journal)
            raise
        journal["status"] = "completed"
        atomic_write_json(journal_path, journal)
        for unit in units:
            unit.apply.status = ApplyStatus.APPLIED
            unit.apply.applied_at = datetime.now(UTC)
        self.repository.save(units)
        return backup_id
