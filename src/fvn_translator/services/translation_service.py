from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import cast
from uuid import uuid4

from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.core.hashing import stable_hash
from fvn_translator.llm.base import LLMProvider
from fvn_translator.llm.request_builder import translation_request
from fvn_translator.llm.response_parser import parse_translations
from fvn_translator.models import (
    Character,
    GlossaryEntry,
    RunState,
    RunStatus,
    TranslationStatus,
    TranslationUnit,
)
from fvn_translator.storage import CacheStore, RevisionStore, UnitRepository

ProgressCallback = Callable[[TranslationUnit, int, int], None]


class TranslationService:
    def __init__(
        self,
        provider: LLMProvider,
        repository: UnitRepository,
        revisions: RevisionStore,
        cache: CacheStore,
        runs_root: Path,
    ) -> None:
        self.provider = provider
        self.repository = repository
        self.revisions = revisions
        self.cache = cache
        self.runs_root = runs_root
        self.stop_requested = False

    def stop(self) -> None:
        self.stop_requested = True

    @staticmethod
    def batches(
        units: list[TranslationUnit], *, character_budget: int = 6000
    ) -> list[list[TranslationUnit]]:
        result: list[list[TranslationUnit]] = []
        current: list[TranslationUnit] = []
        size = 0
        for unit in units:
            if current and size + len(unit.source_text) > character_budget:
                result.append(current)
                current, size = [], 0
            current.append(unit)
            size += len(unit.source_text)
        if current:
            result.append(current)
        return result

    async def translate(
        self,
        *,
        characters: list[Character] | None = None,
        glossary: list[GlossaryEntry] | None = None,
        previous_summary: str = "",
        progress: ProgressCallback | None = None,
        unit_ids: set[str] | None = None,
    ) -> str:
        self.stop_requested = False
        run_id = uuid4().hex
        run_root = self.runs_root / run_id
        pending = [
            unit
            for unit in self.repository.load()
            if unit.translation.status in {TranslationStatus.PENDING, TranslationStatus.FAILED}
            and (unit_ids is None or unit.unit_id in unit_ids)
        ]
        run_state = RunState(
            run_id=run_id,
            provider=type(self.provider).__name__,
            total_units=len(pending),
        )
        atomic_write_json(run_root / "run.json", run_state.model_dump(mode="json"))
        completed = 0
        for batch_number, batch in enumerate(self.batches(pending)):
            if self.stop_requested:
                break
            batch_id = f"batch-{batch_number:05d}"
            request = translation_request(
                run_id=run_id,
                batch_id=batch_id,
                units=batch,
                characters=characters or [],
                glossary=glossary or [],
                previous_summary=previous_summary,
            )
            atomic_write_json(
                run_root / "requests" / f"{batch_id}.json",
                request.model_dump(mode="json"),
            )
            provider_identity = getattr(
                self.provider,
                "model",
                getattr(
                    getattr(self.provider, "config", None), "model", type(self.provider).__name__
                ),
            )
            cache_key = stable_hash(
                {
                    "provider": str(provider_identity),
                    "prompt": request.prompt_version,
                    "payload": request.payload,
                }
            )
            cached = self.cache.get(cache_key)
            try:
                if cached is None:
                    response = await self.provider.complete(request)
                    response_payload = response.model_dump(mode="json")
                    atomic_write_json(run_root / "responses" / f"{batch_id}.json", response_payload)
                    self.cache.set(cache_key, response_payload)
                    content = response.content
                    origin = "llm"
                else:
                    content = cast(dict[str, object], cached["content"])
                    origin = "cache"
                translations = parse_translations(content, [unit.unit_id for unit in batch])
            except Exception:
                run_state.status = RunStatus.FAILED
                run_state.updated_at = datetime.now(UTC)
                atomic_write_json(run_root / "run.json", run_state.model_dump(mode="json"))
                for unit in batch:
                    unit.translation.status = TranslationStatus.FAILED
                all_units = {unit.unit_id: unit for unit in self.repository.load()}
                all_units.update({unit.unit_id: unit for unit in batch})
                self.repository.save(list(all_units.values()))
                raise
            for unit in batch:
                before = unit.target_text
                unit.target_text = translations[unit.unit_id]
                unit.translation.status = TranslationStatus.TRANSLATED
                unit.translation.origin = origin
                unit.translation.translated_at = datetime.now(UTC)
                unit.revision += 1
                unit.updated_at = datetime.now(UTC)
                self.revisions.append(
                    unit_id=unit.unit_id, before=before, after=unit.target_text, origin=origin
                )
            all_units = {unit.unit_id: unit for unit in self.repository.load()}
            all_units.update({unit.unit_id: unit for unit in batch})
            self.repository.save(list(all_units.values()))
            run_state.completed_units += len(batch)
            run_state.updated_at = datetime.now(UTC)
            atomic_write_json(run_root / "run.json", run_state.model_dump(mode="json"))
            for unit in batch:
                completed += 1
                if progress:
                    progress(unit, completed, len(pending))
        run_state.status = RunStatus.STOPPED if self.stop_requested else RunStatus.COMPLETED
        run_state.updated_at = datetime.now(UTC)
        atomic_write_json(run_root / "run.json", run_state.model_dump(mode="json"))
        return run_id
