from uuid import uuid4

from fvn_translator.llm.base import LLMProvider
from fvn_translator.models import LLMRequest, SceneSummary, TranslationUnit


class SummaryService:
    def __init__(self, provider: LLMProvider) -> None:
        self.provider = provider

    async def summarize(
        self, scene_id: str, units: list[TranslationUnit], previous: str
    ) -> SceneSummary:
        request = LLMRequest(
            request_id=uuid4().hex,
            run_id="summary",
            batch_id=scene_id,
            task="summary",
            system_prompt="Summarize durable plot, relationship and terminology context concisely.",
            prompt_version="summary-v1",
            payload={
                "previous_summary": previous,
                "units": [
                    {
                        "unit_id": item.unit_id,
                        "source_text": item.source_text,
                        "target_text": item.target_text,
                    }
                    for item in units
                ],
            },
        )
        response = await self.provider.complete(request)
        summary = response.content.get("summary")
        if not isinstance(summary, str):
            raise ValueError("Summary response is missing summary")
        return SceneSummary(
            scene_id=scene_id,
            previous_summary=previous,
            summary=summary,
            source_unit_ids=[item.unit_id for item in units],
            prompt_version=request.prompt_version,
        )
