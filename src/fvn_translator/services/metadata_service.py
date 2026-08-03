from uuid import uuid4

from fvn_translator.llm.base import LLMProvider
from fvn_translator.models import Character, GlossaryEntry, LLMRequest, TranslationUnit
from fvn_translator.storage import MetadataRepository


class MetadataService:
    def __init__(
        self,
        provider: LLMProvider,
        characters: MetadataRepository[Character] | None = None,
        glossary: MetadataRepository[GlossaryEntry] | None = None,
    ) -> None:
        self.provider = provider
        self.characters = characters
        self.glossary = glossary

    async def extract(
        self, units: list[TranslationUnit], *, chunk_size: int = 100
    ) -> tuple[list[Character], list[GlossaryEntry]]:
        characters: dict[str, Character] = {}
        glossary: dict[str, GlossaryEntry] = {}
        for offset in range(0, len(units), chunk_size):
            chunk = units[offset : offset + chunk_size]
            request = LLMRequest(
                request_id=uuid4().hex,
                run_id="metadata",
                batch_id=str(offset),
                task="metadata",
                system_prompt=(
                    "Extract characters and terminology as structured JSON. "
                    "Keep conflicting candidates."
                ),
                prompt_version="metadata-v1",
                payload={
                    "units": [
                        {
                            "unit_id": item.unit_id,
                            "speaker": item.speaker,
                            "source_text": item.source_text,
                        }
                        for item in chunk
                    ]
                },
            )
            response = await self.provider.complete(request)
            for raw in response.content.get("characters", []):
                candidate = Character.model_validate(raw)
                existing = characters.get(candidate.character_id)
                if existing:
                    existing.evidence_unit_ids = sorted(
                        set(existing.evidence_unit_ids + candidate.evidence_unit_ids)
                    )
                else:
                    characters[candidate.character_id] = candidate
            for raw in response.content.get("glossary", []):
                candidate = GlossaryEntry.model_validate(raw)
                glossary.setdefault(candidate.term_id, candidate)
        character_values = list(characters.values())
        glossary_values = list(glossary.values())
        if self.characters:
            self.characters.save(character_values)
        if self.glossary:
            self.glossary.save(glossary_values)
        return character_values, glossary_values
