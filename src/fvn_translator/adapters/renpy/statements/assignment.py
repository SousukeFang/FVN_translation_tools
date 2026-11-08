import ast
import re
from collections.abc import Iterator

from fvn_translator.adapters.renpy.models import StringToken


def literal_assignment_matches(
    text: str,
    *,
    target: str,
    token: StringToken,
    statement_start: int,
    statement_end: int,
    dictionary_value_key: str | None = None,
    literal_fragments: bool = False,
) -> bool:
    """Locate explicitly registered variable values without evaluating game code."""
    statement = text[statement_start:statement_end]
    leading = re.match(r"[ \t]*(?:(?:define|default)[ \t]+|\$[ \t]*)?", statement)
    assert leading is not None
    expression = statement[leading.end() :]
    assignment_prefix = expression.split("=", 1)[0]
    if target not in assignment_prefix and not re.match(
        rf"(?:[A-Za-z_]\w*\s*=\s*)*{re.escape(target)}\s*=", expression
    ):
        return False
    try:
        parsed = ast.parse(expression)
    except SyntaxError:
        return False
    if len(parsed.body) != 1 or not isinstance(parsed.body[0], ast.Assign):
        return False
    assignment = parsed.body[0]
    if not any(isinstance(item, ast.Name) and item.id == target for item in assignment.targets):
        return False
    candidates = (
        _dictionary_values(assignment.value, dictionary_value_key)
        if dictionary_value_key is not None
        else _literal_fragments(assignment.value, literal_fragments)
    )
    lines = expression.splitlines(keepends=True)
    for candidate in candidates:
        line = lines[candidate.lineno - 1]
        # AST positions count UTF-8 bytes, while the source token counts characters.
        column = len(line.encode("utf-8")[: candidate.col_offset].decode("utf-8"))
        start = statement_start + leading.end() + sum(map(len, lines[: candidate.lineno - 1]))
        end_line = candidate.end_lineno
        end_column = candidate.end_col_offset
        if end_line is None or end_column is None:
            continue
        end = statement_start + leading.end() + sum(map(len, lines[: end_line - 1]))
        end += len(lines[end_line - 1].encode("utf-8")[:end_column].decode("utf-8"))
        if start + column == token.start and end == token.end:
            return True
    return False


def _dictionary_values(node: ast.AST, key: str) -> Iterator[ast.Constant]:
    if not isinstance(node, (ast.List, ast.Tuple)):
        return
    for record in node.elts:
        if not isinstance(record, ast.Dict):
            continue
        for field, value in zip(record.keys, record.values, strict=True):
            if isinstance(field, ast.Constant) and field.value == key:
                yield from _literal_fragments(value, False)


def _literal_fragments(node: ast.AST, allow_fragments: bool) -> Iterator[ast.Constant]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        yield node
    elif (
        allow_fragments and isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod))
    ):
        yield from _literal_fragments(node.left, True)
        if isinstance(node.op, ast.Add):
            yield from _literal_fragments(node.right, True)
