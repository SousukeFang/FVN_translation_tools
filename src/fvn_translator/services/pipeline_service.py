from pathlib import Path

from fvn_translator.models import SceneSummary
from fvn_translator.storage import JSONLStore, UnitRepository

from .summary_service import SummaryService
from .translation_service import ProgressCallback, TranslationService


class TranslationPipelineService:
    """Scene-ordered translation with a bounded rolling summary."""

    def __init__(
        self,
        translation: TranslationService,
        summary: SummaryService,
        repository: UnitRepository,
        summaries_path: Path,
    ) -> None:
        self.translation = translation
        self.summary = summary
        self.repository = repository
        self.summaries = JSONLStore(summaries_path, SceneSummary)

    async def run(self, *, progress: ProgressCallback | None = None) -> list[SceneSummary]:
        units = self.repository.load()
        scene_order: list[str] = []
        by_scene: dict[str, list[str]] = {}
        for unit in units:
            scene_id = unit.scene_id or unit.segment_id
            if scene_id not in by_scene:
                scene_order.append(scene_id)
                by_scene[scene_id] = []
            by_scene[scene_id].append(unit.unit_id)

        summaries = self.summaries.read()
        finished = {summary.scene_id for summary in summaries}
        previous = summaries[-1].summary if summaries else ""
        for scene_id in scene_order:
            if scene_id in finished:
                continue
            await self.translation.translate(
                previous_summary=previous,
                progress=progress,
                unit_ids=set(by_scene[scene_id]),
            )
            if self.translation.stop_requested:
                break
            translated = [
                unit for unit in self.repository.load() if unit.unit_id in by_scene[scene_id]
            ]
            scene_summary = await self.summary.summarize(scene_id, translated, previous)
            summaries.append(scene_summary)
            self.summaries.write(summaries)
            previous = scene_summary.summary
        return summaries
