from pathlib import Path

from fvn_translator.adapters.base import AdapterConfig, FVNAdapter
from fvn_translator.models import Issue, ValidationStatus
from fvn_translator.storage import JSONLStore, UnitRepository
from fvn_translator.validators import validate_unit


class ValidationService:
    def __init__(self, repository: UnitRepository, issues_path: Path) -> None:
        self.repository = repository
        self.issues = JSONLStore(issues_path, Issue)

    def validate(
        self,
        *,
        adapter: FVNAdapter | None = None,
        staging_root: Path | None = None,
        config: AdapterConfig | None = None,
    ) -> list[Issue]:
        units = self.repository.load()
        issues = [issue for unit in units for issue in validate_unit(unit)]
        if adapter and staging_root:
            issues.extend(adapter.validate(staging_root, units, config or AdapterConfig()).issues)
        by_unit: dict[str, list[Issue]] = {}
        for issue in issues:
            if issue.unit_id:
                by_unit.setdefault(issue.unit_id, []).append(issue)
        for unit in units:
            own = by_unit.get(unit.unit_id, [])
            unit.validation.issue_ids = [item.issue_id for item in own]
            unit.validation.status = (
                ValidationStatus.FAILED
                if any(item.severity == "error" for item in own)
                else ValidationStatus.WARNING
                if own
                else ValidationStatus.PASSED
            )
        self.repository.save(units)
        self.issues.write(issues)
        return issues
