from uuid import uuid4

from fvn_translator.models import Character, GlossaryEntry, LLMRequest, TranslationUnit

TRANSLATION_PROMPT_VERSION = "translation-v2"


def translation_instructions(source_language: str, target_language: str) -> str:
    return (
        f"Translate player-visible FVN text from {source_language} into {target_language}. "
        "Preserve the original meaning, character voices, narrative perspective, rhythm, "
        "humor, wordplay, emotional subtext, profanity and sexual content. "
        "Use natural literary language without additions, omissions or censorship. "
        "Follow the supplied character and glossary guidance consistently. "
        "Preserve protected tokens, their order and counts, and meaningful line breaks. "
        'Return JSON only: {"translations":[{"unit_id":"...","target_text":"..."}]}. '
        "Include every requested unit exactly once. Context is for reference only."
    )


def translation_request(
    *,
    run_id: str,
    batch_id: str,
    units: list[TranslationUnit],
    characters: list[Character],
    glossary: list[GlossaryEntry],
    previous_summary: str,
    source_language: str = "en",
    target_language: str = "zh-CN",
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
        system_prompt=translation_instructions(source_language, target_language),
        payload={
            "source_language": source_language,
            "target_language": target_language,
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
