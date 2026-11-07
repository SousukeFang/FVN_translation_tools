"""Ren'Py's ordinary dialogue-string semantics, separate from Python literals."""

import re

RENPY_TEXT_ESCAPES = "renpy_text_escapes_v1"
RENPY_DEQUOTE = re.compile(r"\\(u([0-9a-fA-F]{1,4})|.)")


def dequote_renpy_escape(match: re.Match[str]) -> str:
    """Match Lexer.string in Ren'Py 8.5.2, including its unknown escapes."""
    character = match.group(1)
    if character in {"{", "[", "%"}:
        return character * 2
    if character == "n":
        return "\n"
    if character.startswith("u"):
        hexadecimal = match.group(2)
        # The original callback returns None for a bare \u; re.sub removes it.
        return chr(int(hexadecimal, 16)) if hexadecimal else ""
    return character


def decode_renpy_text_content(raw: str) -> str:
    """Decode a non-raw, non-triple Say/Menu literal, preserving explicit \n."""
    # Ren'Py's logical-line reader normalizes a source file's CRLF before string().
    normalized = re.sub(r"[ \n]+", " ", raw.replace("\r\n", "\n"))
    return RENPY_DEQUOTE.sub(dequote_renpy_escape, normalized)
