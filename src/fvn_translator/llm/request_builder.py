from uuid import uuid4

from fvn_translator.models import Character, GlossaryEntry, LLMRequest, TranslationUnit

TRANSLATION_PROMPT_VERSION = "translation-v1"


def translation_request(
    *,
    run_id: str,
    batch_id: str,
    units: list[TranslationUnit],
    characters: list[Character],
    glossary: list[GlossaryEntry],
    previous_summary: str,
) -> LLMRequest:
    speakers = {unit.speaker for unit in units if unit.speaker}
    relevant_characters = [item for item in characters if speakers.intersection(item.names)]
    relevant_terms = [
        item for item in glossary if any(item.source_term in unit.source_text for unit in units)
    ]
    return LLMRequest(
        request_id=uuid4().hex,
        run_id=run_id,
        batch_id=batch_id,
        task="translation",
        prompt_version=TRANSLATION_PROMPT_VERSION,
        system_prompt=(
            "Translate visible FVN text into Simplified Chinese. "
            "Preserve every protected token exactly. Return JSON: "
            "{translations:[{unit_id,target_text}]}. Never return or modify source files."
        ),
        payload={
            "previous_summary": previous_summary,
            "characters": [
                item.model_dump(mode="json", by_alias=True) for item in relevant_characters
            ],
            "glossary": [item.model_dump(mode="json", by_alias=True) for item in relevant_terms],
            "units": [
                {
                    "unit_id": unit.unit_id,
                    "speaker": unit.speaker,
                    "source_text": unit.source_text,
                    "protected_tokens": unit.protected_tokens,
                    "context": unit.context,
                }
                for unit in units
            ],
        },
    )
