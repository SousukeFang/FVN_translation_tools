import re

from fvn_translator.adapters.renpy.models import StringToken


def function_call_before(text: str, function: str) -> bool:
    return bool(re.search(rf"(?<![\w.]){re.escape(function)}\s*\(\s*$", text))


def literal_argument_index(
    text: str,
    *,
    function: str,
    token: StringToken,
    statement_start: int,
    statement_end: int,
    strings: list[StringToken],
) -> int | None:
    statement = text[statement_start:statement_end]
    pattern = re.compile(rf"(?<![\w.]){re.escape(function)}\s*\(")
    for match in reversed(list(pattern.finditer(statement))):
        opening = statement_start + match.end()
        if opening > token.start:
            continue
        argument = _argument_before(text, opening, token.start, strings)
        if argument is not None:
            return argument
    return None


def _argument_before(text: str, start: int, target: int, strings: list[StringToken]) -> int | None:
    by_start = {token.start: token for token in strings if token.start < target}
    depth = 0
    argument = 0
    index = start
    while index < target:
        string = by_start.get(index)
        if string:
            index = string.end
            continue
        char = text[index]
        if char in "([{":
            depth += 1
        elif char in ")]}":
            if depth == 0:
                return None
            depth -= 1
        elif char == "," and depth == 0:
            argument += 1
        index += 1
    return argument
