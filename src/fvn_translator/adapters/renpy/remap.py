from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fvn_translator.models import TranslationUnit


class RemapStatus(StrEnum):
    UNCHANGED = "unchanged"
    MOVED = "moved"
    SOURCE_CHANGED = "source_changed"
    NEW = "new"
    DELETED = "deleted"
    CONFLICT = "conflict"


@dataclass(frozen=True, slots=True)
class UnitRemap:
    status: RemapStatus
    new_unit_id: str | None
    old_unit_id: str | None
    candidates: tuple[str, ...] = ()


def remap_units(
    old_units: list[TranslationUnit], new_units: list[TranslationUnit]
) -> list[UnitRemap]:
    unmatched_old = {unit.unit_id: unit for unit in old_units}
    results: list[UnitRemap] = []
    for new in new_units:
        candidates = _candidates(new, list(unmatched_old.values()))
        if not candidates:
            results.append(UnitRemap(RemapStatus.NEW, new.unit_id, None))
            continue
        if len(candidates) > 1:
            results.append(
                UnitRemap(
                    RemapStatus.CONFLICT,
                    new.unit_id,
                    None,
                    tuple(unit.unit_id for unit in candidates),
                )
            )
            continue
        old = candidates[0]
        unmatched_old.pop(old.unit_id, None)
        status = (
            RemapStatus.UNCHANGED
            if old.unit_id == new.unit_id and old.source_fingerprint == new.source_fingerprint
            else RemapStatus.MOVED
            if old.source_fingerprint == new.source_fingerprint
            else RemapStatus.SOURCE_CHANGED
        )
        results.append(UnitRemap(status, new.unit_id, old.unit_id))
    results.extend(
        UnitRemap(RemapStatus.DELETED, None, unit_id) for unit_id in sorted(unmatched_old)
    )
    return results


def _candidates(new: TranslationUnit, old_units: list[TranslationUnit]) -> list[TranslationUnit]:
    native_id = new.adapter_data.get("translation_id")
    if native_id:
        matched = [old for old in old_units if old.adapter_data.get("translation_id") == native_id]
        if matched:
            return matched
    statement = new.adapter_data.get("source_statement_fingerprint")
    matched = [
        old
        for old in old_units
        if old.adapter_data.get("source_statement_fingerprint") == statement
    ]
    if matched:
        return matched
    exact_position = [old for old in old_units if old.unit_id == new.unit_id]
    if exact_position:
        return exact_position
    return [
        old
        for old in old_units
        if old.source_fingerprint == new.source_fingerprint
        and old.adapter_data.get("previous_statement_fingerprint")
        == new.adapter_data.get("previous_statement_fingerprint")
        and old.adapter_data.get("next_statement_fingerprint")
        == new.adapter_data.get("next_statement_fingerprint")
    ]
