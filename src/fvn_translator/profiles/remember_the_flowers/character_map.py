import re
from pathlib import Path

from fvn_translator.adapters.renpy.lexer import RenPyLexer
from fvn_translator.adapters.renpy.models import StringToken
from fvn_translator.profiles.base import CharacterDefinition

CHARACTER_LINE = re.compile(
    r"^\s*define\s+(?P<id>[A-Za-z_]\w*)\s*=\s*Character\s*\(", re.IGNORECASE
)


def load_character_map(source_root: Path) -> dict[str, CharacterDefinition]:
    path = source_root / "game/characters/names.rpy"
    if not path.is_file():
        return {}
    text = path.read_bytes().decode("utf-8-sig")
    scan = RenPyLexer().scan(text, "game/characters/names.rpy")
    tokens_by_line: dict[int, list[StringToken]] = {}
    for token in scan.strings:
        tokens_by_line.setdefault(token.start_line, []).append(token)
    result: dict[str, CharacterDefinition] = {}
    for number, line in enumerate(text.splitlines(), 1):
        match = CHARACTER_LINE.match(line)
        if not match:
            continue
        speaker_id = match.group("id")
        strings = tokens_by_line.get(number, [])
        argument_start = match.end()
        arguments = line[argument_start:]
        leading = arguments.lstrip()
        leading_start = argument_start + len(arguments) - len(leading)
        display = None
        name_match = re.match(r"name\s*=\s*", leading)
        if name_match:
            value_start = leading_start + name_match.end()
            display_token = next(
                (token for token in strings if token.start_column >= value_start), None
            )
            if display_token and not line[value_start : display_token.start_column].strip():
                display = display_token.value
        else:
            display_token = next(
                (token for token in strings if token.start_column >= leading_start), None
            )
            if display_token and not line[leading_start : display_token.start_column].strip():
                display = display_token.value
        if display == "":
            display = None
        result[speaker_id] = CharacterDefinition(
            speaker_id=speaker_id,
            display_name=display,
            status="resolved" if display else "unresolved",
            source_path="game/characters/names.rpy",
            source_line=number,
        )
    return result
