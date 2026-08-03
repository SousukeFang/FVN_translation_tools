from datetime import UTC, datetime

from fvn_translator.models import TranslationStatus
from fvn_translator.storage import RevisionStore, UnitRepository


class EditingService:
    def __init__(self, repository: UnitRepository, revisions: RevisionStore) -> None:
        self.repository = repository
        self.revisions = revisions

    def search(self, query: str) -> list[str]:
        normalized = query.casefold()
        return [
            unit.unit_id
            for unit in self.repository.load()
            if normalized in unit.source_text.casefold()
            or normalized in unit.target_text.casefold()
            or normalized in (unit.speaker or "").casefold()
        ]

    def edit(self, unit_id: str, target_text: str, *, origin: str = "human") -> None:
        unit = next((item for item in self.repository.load() if item.unit_id == unit_id), None)
        if unit is None:
            raise KeyError(unit_id)
        self.revisions.append(
            unit_id=unit_id, before=unit.target_text, after=target_text, origin=origin
        )
        unit.target_text = target_text
        unit.revision += 1
        unit.updated_at = datetime.now(UTC)
        unit.translation.status = (
            TranslationStatus.REVIEWED if origin == "human" else TranslationStatus.TRANSLATED
        )
        unit.translation.origin = origin
        unit.translation.translated_at = datetime.now(UTC)
        self.repository.update(unit)

    def mark_for_retranslation(self, unit_ids: list[str]) -> int:
        selected = set(unit_ids)
        units = self.repository.load()
        changed = 0
        for unit in units:
            if unit.unit_id in selected:
                unit.translation.status = TranslationStatus.PENDING
                changed += 1
        self.repository.save(units)
        return changed
