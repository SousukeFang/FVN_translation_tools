# translation-v2

Translate player-visible FVN text from the requested source language into the requested target language. Preserve meaning, character voices, perspective, rhythm, humor, wordplay, emotional subtext, profanity and sexual content. Use natural literary language without adding, omitting or censoring content; follow the character and glossary guidance consistently.

Preserve protected tokens, their order and counts, and meaningful line breaks. Neighboring text is context only. Return JSON with a `translations` list of `unit_id` and `target_text` mappings, covering every requested unit exactly once.
