from __future__ import annotations

from fvn_translator.models import Issue, Severity

from .models import CommentToken, LexResult, StringToken


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    previous = text.rfind("\n", 0, offset)
    return line, offset if previous < 0 else offset - previous - 1


def decode_string_content(raw: str, *, raw_prefix: bool = False) -> str:
    if raw_prefix:
        return raw
    output: list[str] = []
    index = 0
    escapes = {"n": "\n", "r": "\r", "t": "\t", "\\": "\\", '"': '"', "'": "'"}
    while index < len(raw):
        if raw[index] == "\\" and index + 1 < len(raw):
            following = raw[index + 1]
            if following in escapes:
                output.append(escapes[following])
                index += 2
                continue
        output.append(raw[index])
        index += 1
    return "".join(output)


class RenPyLexer:
    """Stateful scanner for Ren'Py/Python string and comment boundaries."""

    _prefix_chars = frozenset("rRuUbBfF")

    def scan(self, text: str, path: str = "<memory>") -> LexResult:
        result = LexResult()
        index = 0
        length = len(text)
        stack: list[tuple[str, int]] = []
        while index < length:
            char = text[index]
            if char == "#":
                end = text.find("\n", index)
                if end < 0:
                    end = length
                line, column = _line_column(text, index)
                result.comments.append(
                    CommentToken(index, end, line, column, text[index + 1 : end])
                )
                index = end
                continue
            prefix_start = index
            quote_index = index
            if char in self._prefix_chars and (
                index == 0 or not self._is_identifier(text[index - 1])
            ):
                while quote_index < length and text[quote_index] in self._prefix_chars:
                    quote_index += 1
                if quote_index >= length or text[quote_index] not in "'\"":
                    quote_index = index
            if text[quote_index : quote_index + 1] in ("'", '"'):
                token, next_index, issue = self._scan_string(text, prefix_start, quote_index, path)
                if token:
                    result.strings.append(token)
                if issue:
                    result.issues.append(issue)
                index = max(next_index, index + 1)
                continue
            if char in "([{":
                stack.append((char, index))
            elif char in ")]}":
                expected = {")": "(", "]": "[", "}": "{"}[char]
                if stack and stack[-1][0] == expected:
                    stack.pop()
                else:
                    line, _ = _line_column(text, index)
                    result.issues.append(
                        self._issue(path, line, "RENPY_UNMATCHED_DELIMITER", f"Unmatched {char}")
                    )
            index += 1
        for opening, offset in stack:
            line, _ = _line_column(text, offset)
            result.issues.append(
                self._issue(path, line, "RENPY_UNCLOSED_DELIMITER", f"Unclosed {opening}")
            )
        return result

    def _scan_string(
        self, text: str, start: int, quote_index: int, path: str
    ) -> tuple[StringToken | None, int, Issue | None]:
        quote_char = text[quote_index]
        triple = text.startswith(quote_char * 3, quote_index)
        quote = quote_char * (3 if triple else 1)
        content_start = quote_index + len(quote)
        index = content_start
        braces = 0
        brackets = 0
        while index < len(text):
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char == "{" and not text.startswith("{{", index):
                braces += 1
            elif char == "}" and braces:
                braces -= 1
            elif char == "[" and not text.startswith("[[", index):
                brackets += 1
            elif char == "]" and brackets:
                brackets -= 1
            if braces == 0 and brackets == 0 and text.startswith(quote, index):
                end = index + len(quote)
                prefix = text[start:quote_index]
                raw_content = text[content_start:index]
                start_line, start_column = _line_column(text, start)
                end_line, end_column = _line_column(text, end)
                token = StringToken(
                    start=start,
                    end=end,
                    content_start=content_start,
                    content_end=index,
                    start_line=start_line,
                    end_line=end_line,
                    start_column=start_column,
                    end_column=end_column,
                    prefix=prefix,
                    quote=quote,
                    raw=text[start:end],
                    raw_content=raw_content,
                    value=decode_string_content(raw_content, raw_prefix="r" in prefix.lower()),
                )
                return token, end, None
            if not triple and char in "\r\n":
                break
            index += 1
        line, _ = _line_column(text, start)
        return (
            None,
            self._safe_boundary(text, index),
            self._issue(path, line, "RENPY_UNCLOSED_STRING", "Unclosed string literal"),
        )

    @staticmethod
    def _safe_boundary(text: str, index: int) -> int:
        boundary = text.find("\n", index)
        return len(text) if boundary < 0 else boundary + 1

    @staticmethod
    def _is_identifier(char: str) -> bool:
        return char.isalnum() or char == "_"

    @staticmethod
    def _issue(path: str, line: int, code: str, message: str) -> Issue:
        return Issue(
            issue_id=f"{code.lower()}:{path}:{line}",
            code=code,
            severity=Severity.ERROR,
            message=message,
            path=path,
            line=line,
        )
