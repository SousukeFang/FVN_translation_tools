from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

TAG_NAME = re.compile(r"^/?(?P<name>[A-Za-z#][\w#-]*)")
SELF_CLOSING = frozenset({"w", "p", "nw", "fast", "clear", "space", "vspace", "#"})
ProtectionSignature = dict[str, list[str]]


@dataclass(frozen=True, slots=True)
class ProtectionIssue:
    code: str
    message: str


def protection_signature(text: str, raw_text: str | None = None) -> ProtectionSignature:
    tags = _balanced_tokens(text, "{", "}", "{{")
    interpolations = _balanced_tokens(text, "[", "]", "[[")
    raw = raw_text if raw_text is not None else text
    escapes = _escape_tokens(raw)
    return {
        "tags": tags,
        "interpolations": interpolations,
        "escapes": escapes,
    }


def unique_protected_tokens(signature: ProtectionSignature) -> list[str]:
    result: list[str] = []
    for key in ("tags", "interpolations", "escapes"):
        for token in signature.get(key, []):
            value = str(token)
            if value not in result:
                result.append(value)
    return result


def compare_signatures(
    expected: ProtectionSignature, actual: ProtectionSignature
) -> list[ProtectionIssue]:
    issues: list[ProtectionIssue] = []
    for key, code in (
        ("tags", "RENPY_TEXT_TAG_MISMATCH"),
        ("interpolations", "RENPY_INTERPOLATION_MISMATCH"),
        ("escapes", "RENPY_ESCAPE_MISMATCH"),
    ):
        left = [str(item) for item in expected.get(key, [])]
        right = [str(item) for item in actual.get(key, [])]
        if left != right:
            issues.append(ProtectionIssue(code, f"{key} differ: expected {left!r}, got {right!r}"))
    expected_nesting = validate_tag_nesting([str(item) for item in expected.get("tags", [])])
    actual_nesting = validate_tag_nesting([str(item) for item in actual.get("tags", [])])
    if [item.message for item in actual_nesting] != [item.message for item in expected_nesting]:
        issues.extend(
            actual_nesting or [ProtectionIssue("RENPY_TEXT_TAG_NESTING", "Tag nesting changed")]
        )
    return issues


def validate_tag_nesting(tags: list[str]) -> list[ProtectionIssue]:
    stack: list[str] = []
    issues: list[ProtectionIssue] = []
    for token in tags:
        body = token[1:-1].strip()
        match = TAG_NAME.match(body)
        if not match:
            continue
        name = match.group("name").lower()
        if body.startswith("/"):
            if not stack or stack[-1] != name:
                issues.append(
                    ProtectionIssue("RENPY_TEXT_TAG_NESTING", f"Unexpected closing tag {token}")
                )
            else:
                stack.pop()
        elif name not in SELF_CLOSING:
            stack.append(name)
    for name in reversed(stack):
        issues.append(ProtectionIssue("RENPY_TEXT_TAG_NESTING", f"Unclosed tag {{{name}}}"))
    return issues


def semantic_escape_signature(text: str) -> list[str]:
    result: list[str] = []
    result.extend(["\\n"] * text.count("\n"))
    result.extend(["\\t"] * text.count("\t"))
    result.extend(["\\\\"] * text.count("\\"))
    return result


def _balanced_tokens(text: str, opening: str, closing: str, escaped: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    while index < len(text):
        if text.startswith(escaped, index):
            index += len(escaped)
            continue
        if text[index] != opening:
            index += 1
            continue
        end = index + 1
        depth = 1
        while end < len(text) and depth:
            if text[end] == opening:
                depth += 1
            elif text[end] == closing:
                depth -= 1
            end += 1
        if depth == 0:
            tokens.append(text[index:end])
            index = end
        else:
            index += 1
    return tokens


def _escape_tokens(raw: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    while index < len(raw):
        if raw.startswith(("%%", "{{", "[["), index):
            tokens.append(raw[index : index + 2])
            index += 2
            continue
        if raw[index] == "\\" and index + 1 < len(raw):
            tokens.append(raw[index : index + 2])
            index += 2
            continue
        index += 1
    return tokens


def signature_counts(signature: ProtectionSignature) -> dict[str, Counter[str]]:
    return {key: Counter(map(str, signature.get(key, []))) for key in signature}
