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
    keyword: str | None = None,
) -> int | None:
    statement = text[statement_start:statement_end]
    pattern = re.compile(rf"(?<![\w.]){re.escape(function)}\s*\(")
    for match in reversed(list(pattern.finditer(statement))):
        opening = statement_start + match.end()
        if opening > token.start:
            continue
        argument = _argument_before(text, opening, token.start, strings, keyword=keyword)
        if argument is not None:
            return argument
    return None


def _argument_before(
    text: str,
    start: int,
    target: int,
    strings: list[StringToken],
    *,
    keyword: str | None = None,
) -> int | None:
    by_start = {token.start: token for token in strings if token.start < target}
    depth = 0
    argument = 0
    argument_start = start
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
            argument_start = index + 1
        index += 1
    leading = text[argument_start:target].strip()
    if keyword is not None:
        return 0 if re.fullmatch(rf"{re.escape(keyword)}\s*=", leading) else None
    if leading:
        return None
    return argument
