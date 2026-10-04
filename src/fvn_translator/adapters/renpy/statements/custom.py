import ast
import re
from collections.abc import Iterator

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
    dictionary_value_key: str | None = None,
    literal_fragments: bool = False,
) -> int | None:
    statement = text[statement_start:statement_end]
    pattern = re.compile(rf"(?<![\w.]){re.escape(function)}\s*\(")
    for match in reversed(list(pattern.finditer(statement))):
        opening = statement_start + match.end()
        if opening > token.start:
            continue
        if any(string.start <= statement_start + match.start() < string.end for string in strings):
            continue
        if dictionary_value_key is not None or literal_fragments:
            argument = _expression_argument_index(
                text,
                opening,
                statement_end,
                token,
                strings,
                keyword=keyword,
                dictionary_value_key=dictionary_value_key,
                literal_fragments=literal_fragments,
            )
        else:
            argument = _argument_before(text, opening, token.start, strings, keyword=keyword)
        if argument is not None:
            return argument
    return None


def _expression_argument_index(
    text: str,
    opening: int,
    statement_end: int,
    token: StringToken,
    strings: list[StringToken],
    *,
    keyword: str | None,
    dictionary_value_key: str | None,
    literal_fragments: bool,
) -> int | None:
    """Locate registered literal expression fields without executing source code."""
    by_start = {string.start: string for string in strings}
    depth = 1
    end = opening
    while end < statement_end:
        string = by_start.get(end)
        if string:
            end = string.end
            continue
        if text[end] == "#":
            newline = text.find("\n", end, statement_end)
            end = statement_end if newline < 0 else newline + 1
            continue
        if text[end] == "(":
            depth += 1
        elif text[end] == ")":
            depth -= 1
            if depth == 0:
                break
        end += 1
    if depth:
        return None
    expression = "f" + text[opening - 1 : end + 1]
    try:
        parsed = ast.parse(expression, mode="eval").body
    except SyntaxError:
        return None
    if not isinstance(parsed, ast.Call):
        return None
    arguments = (
        [(0, argument.value) for argument in parsed.keywords if argument.arg == keyword]
        if keyword is not None
        else list(enumerate(parsed.args))
    )
    for index, argument in arguments:
        candidates = (
            _dictionary_values(argument, dictionary_value_key)
            if dictionary_value_key is not None
            else _literal_fragments(argument)
            if literal_fragments
            else iter(())
        )
        for candidate in candidates:
            # Python AST columns are UTF-8 byte offsets; FTIF uses character offsets.
            lines = expression.splitlines(keepends=True)
            line = lines[candidate.lineno - 1]
            character_column = len(line.encode("utf-8")[: candidate.col_offset].decode("utf-8"))
            relative = sum(map(len, lines[: candidate.lineno - 1])) + character_column
            if opening - 2 + relative == token.start:
                return index
    return None


def _dictionary_values(node: ast.AST, key: str) -> Iterator[ast.Constant]:
    """Select fields of dictionary records, e.g. choices[index]['name']."""
    if not isinstance(node, ast.Dict):
        return
    for record in node.values:
        if not isinstance(record, ast.Dict):
            continue
        for field, value in zip(record.keys, record.values, strict=True):
            if (
                isinstance(field, ast.Constant)
                and field.value == key
                and isinstance(value, ast.Constant)
                and isinstance(value.value, str)
            ):
                yield value


def _literal_fragments(node: ast.AST) -> Iterator[ast.Constant]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node
    elif isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
        yield from _literal_fragments(node.left)
        if isinstance(node.op, ast.Add):
            yield from _literal_fragments(node.right)


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
