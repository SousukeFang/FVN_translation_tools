from __future__ import annotations

import re
from typing import TypedDict

from fvn_translator.core.hashing import bytes_hash
from fvn_translator.models import Issue, Severity, UnitType
from fvn_translator.profiles.base import CustomTextSink, SceneRules

from .lexer import RenPyLexer
from .models import ParseResult, StringToken, TextNode
from .statements import (
    SCREEN_KEYWORDS,
    TRANSLATION_FUNCTIONS,
    is_menu_choice_suffix,
    is_show_text,
    literal_argument_index,
    parse_say_prefix,
)

LABEL = re.compile(r"^\s*label\s+(?P<name>[A-Za-z_]\w*)\s*:")
SCREEN = re.compile(r"^\s*screen\s+[A-Za-z_]\w*")
PYTHON_BLOCK = re.compile(r"^\s*(?:init(?:\s+-?\d+)?\s+)?python(?:\s+early)?\s*:", re.IGNORECASE)
NON_TEXT_STATEMENTS = frozenset(
    {
        "background",
        "base_bar",
        "bottom_bar",
        "font",
        "foreground",
        "hover_background",
        "hover_color",
        "hover_foreground",
        "id",
        "idle",
        "idle_background",
        "idle_color",
        "insensitive",
        "insensitive_background",
        "insensitive_color",
        "layout",
        "left_bar",
        "right_bar",
        "selected_color",
        "selected_hover",
        "selected_idle",
        "size_group",
        "style_prefix",
        "thumb",
        "top_bar",
        "variant",
    }
)
DISALLOWED_SAY = frozenset(
    {
        "define",
        "default",
        "image",
        "play",
        "queue",
        "stop",
        "scene",
        "show",
        "hide",
        "with",
        "jump",
        "call",
        "return",
        "python",
        "init",
        "transform",
        "style",
        "camera",
        "voice",
        "sound",
        "audio",
        "window",
        "pause",
        "if",
        "elif",
        "while",
        "for",
        "key",
        "add",
        "use",
        "on",
        "timer",
        "vbox",
        "hbox",
        "frame",
        "button",
        "fixed",
        "viewport",
    }
)


class NodeBase(TypedDict):
    statement_start: int
    statement_end: int
    start_line: int
    end_line: int
    label: str
    scene_id: str
    statement_index: int


class RenPyParser:
    def __init__(
        self,
        *,
        custom_sinks: list[CustomTextSink] | None = None,
        scene_rules: SceneRules | None = None,
        allowed_speakers: set[str] | None = None,
    ) -> None:
        self.custom_sinks = custom_sinks or []
        self.scene_rules = scene_rules or SceneRules()
        self.allowed_speakers = allowed_speakers

    def parse(self, text: str, relative_path: str) -> ParseResult:
        lexed = RenPyLexer().scan(text, relative_path)
        result = ParseResult(issues=list(lexed.issues))
        line_starts = _line_starts(text)
        lines = text.splitlines(keepends=True)
        tokens_by_line: dict[int, list[StringToken]] = {}
        for token in lexed.strings:
            tokens_by_line.setdefault(token.start_line, []).append(token)
        comments = {token.line: token.text.strip() for token in lexed.comments}
        label = "<file>"
        scene_index = 0
        screen_indent: int | None = None
        menu_indent: int | None = None
        python_indent: int | None = None
        visible_index = 0
        previous_dialogue_index: int | None = None
        for line_number, raw_line in enumerate(lines, 1):
            line = raw_line.rstrip("\r\n")
            stripped = line.lstrip(" \t")
            indent = len(line) - len(stripped)
            if stripped and not stripped.startswith("#"):
                if screen_indent is not None and indent <= screen_indent and not SCREEN.match(line):
                    screen_indent = None
                if (
                    menu_indent is not None
                    and indent <= menu_indent
                    and not stripped.startswith("menu")
                ):
                    menu_indent = None
                if (
                    python_indent is not None
                    and indent <= python_indent
                    and not PYTHON_BLOCK.match(line)
                ):
                    python_indent = None
            label_match = LABEL.match(line)
            if label_match:
                label = label_match.group("name")
                scene_index = 0
            if SCREEN.match(line):
                screen_indent = indent
            if re.match(r"^\s*menu(?:\s+[^:]*)?\s*:", line):
                menu_indent = indent
            if PYTHON_BLOCK.match(line):
                python_indent = indent
            if re.match(r"^\s*scene\s+\S", line):
                scene_index += 1
            if self._structured_scene(comments.get(line_number, "")):
                scene_index += 1
            tokens = sorted(tokens_by_line.get(line_number, []), key=lambda item: item.start)
            if not tokens:
                continue
            statement_start = line_starts[line_number - 1]
            statement_end = _statement_end(text, line_starts, tokens)
            scene_id = f"{relative_path}:{label}:{scene_index}"
            classified = self._classify(
                text,
                line,
                tokens,
                statement_start,
                statement_end,
                line_number,
                label,
                scene_id,
                visible_index,
                screen_indent is not None and indent > screen_indent,
                menu_indent is not None and indent > menu_indent,
                python_indent is not None and indent > python_indent,
                previous_dialogue_index,
            )
            if classified:
                for node in classified:
                    if any(prefix in node.token.prefix.lower() for prefix in ("f", "b")):
                        result.issues.append(
                            Issue(
                                issue_id=(
                                    f"renpy-prefix:{relative_path}:"
                                    f"{node.token.start_line}:{node.token.start_column}"
                                ),
                                code="RENPY_UNSUPPORTED_STRING_PREFIX",
                                severity=Severity.WARNING,
                                message="f-string/bytes literals are unsafe translation targets",
                                path=relative_path,
                                line=node.token.start_line,
                            )
                        )
                        continue
                    node.statement_index = visible_index
                    result.nodes.append(node)
                    if node.unit_type in (UnitType.DIALOGUE, UnitType.DIALOGUE_EXTENSION):
                        previous_dialogue_index = len(result.nodes) - 1
                    visible_index += 1
            elif self._looks_like_visible_unknown(
                line,
                tokens,
                in_screen=screen_indent is not None and indent > screen_indent,
                in_python=python_indent is not None and indent > python_indent,
            ):
                result.issues.append(
                    Issue(
                        issue_id=f"renpy-unknown:{relative_path}:{line_number}",
                        code="RENPY_UNKNOWN_TEXT_SINK",
                        severity=Severity.WARNING,
                        message="String may be player-visible but its statement is not supported",
                        path=relative_path,
                        line=line_number,
                        details={"statement": line.strip()[:200]},
                    )
                )
        result.structure_fingerprint = structural_fingerprint(text, result.nodes)
        self._add_neighbors(result.nodes)
        return result

    def _classify(
        self,
        text: str,
        line: str,
        tokens: list[StringToken],
        statement_start: int,
        statement_end: int,
        line_number: int,
        label: str,
        scene_id: str,
        statement_index: int,
        in_screen: bool,
        in_menu: bool,
        in_python: bool,
        previous_dialogue_index: int | None,
    ) -> list[TextNode]:
        base: NodeBase = {
            "statement_start": statement_start,
            "statement_end": statement_end,
            "start_line": line_number,
            "end_line": max(token.end_line for token in tokens),
            "label": label,
            "scene_id": scene_id,
            "statement_index": statement_index,
        }
        stripped = line.lstrip(" \t")
        line_absolute = statement_start
        first = tokens[0]
        prefix = text[line_absolute : first.start].strip()
        if is_show_text(stripped) and first.start >= line_absolute + line.find("text"):
            return [TextNode(kind="show_text", unit_type=UnitType.SCREEN_TEXT, token=first, **base)]
        if in_screen:
            keyword = stripped.split(None, 1)[0] if stripped else ""
            if keyword in SCREEN_KEYWORDS and not (keyword == "label" and stripped.endswith(":")):
                return [
                    TextNode(
                        kind=f"screen_{keyword}",
                        unit_type=SCREEN_KEYWORDS[keyword],
                        token=first,
                        **base,
                    )
                ]
        if in_menu and prefix == "" and is_menu_choice_suffix(text[first.end : statement_end]):
            return [TextNode(kind="menu", unit_type=UnitType.MENU_CHOICE, token=first, **base)]
        function_nodes = self._function_nodes(text, tokens, base)
        if function_nodes:
            return function_nodes
        if in_python:
            return []
        if prefix == "" and len(tokens) >= 2:
            between = text[first.end : tokens[1].start]
            if not between.strip():
                return [
                    TextNode(
                        kind="say_explicit",
                        unit_type=UnitType.DIALOGUE,
                        token=tokens[1],
                        speaker=first.value,
                        explicit_display_name=first.value,
                        **base,
                    )
                ]
        if prefix == "":
            return [TextNode(kind="say", unit_type=UnitType.NARRATION, token=first, **base)]
        identifiers = prefix.split()
        if identifiers and identifiers[0] == "extend" and len(identifiers) == 1:
            return [
                TextNode(
                    kind="extend",
                    unit_type=UnitType.DIALOGUE_EXTENSION,
                    token=first,
                    extends_index=previous_dialogue_index,
                    **base,
                )
            ]
        say = parse_say_prefix(prefix, DISALLOWED_SAY)
        if say:
            speaker, attributes = say
            if self.allowed_speakers is not None and speaker not in self.allowed_speakers:
                return []
            return [
                TextNode(
                    kind="say",
                    unit_type=UnitType.DIALOGUE,
                    token=first,
                    speaker=speaker,
                    speaker_attributes=attributes,
                    **base,
                )
            ]
        return []

    def _function_nodes(
        self, text: str, tokens: list[StringToken], base: NodeBase
    ) -> list[TextNode]:
        sinks = [
            *(
                CustomTextSink(function=name, unit_type=UnitType.UI_TEXT)
                for name in TRANSLATION_FUNCTIONS
            ),
            *self.custom_sinks,
        ]
        nodes: list[TextNode] = []
        for token in tokens:
            for sink in sinks:
                argument = literal_argument_index(
                    text,
                    function=sink.function,
                    token=token,
                    statement_start=base["statement_start"],
                    statement_end=base["statement_end"],
                    strings=tokens,
                )
                if argument == sink.argument:
                    nodes.append(
                        TextNode(
                            kind="function",
                            unit_type=sink.unit_type,
                            token=token,
                            text_role=f"argument-{sink.argument}",
                            context={"function": sink.function},
                            **base,
                        )
                    )
                    break
        return nodes

    def _structured_scene(self, comment: str) -> bool:
        lowered = comment.lower()
        return any(lowered.startswith(f"{name}:") for name in self.scene_rules.structured_comments)

    @staticmethod
    def _looks_like_visible_unknown(
        line: str,
        tokens: list[StringToken],
        *,
        in_screen: bool,
        in_python: bool,
    ) -> bool:
        if in_screen or in_python:
            return False
        stripped = line.strip()
        if not stripped or stripped.startswith(
            (
                "#",
                "$",
                "define ",
                "default ",
                "image ",
                "play ",
                "style ",
                "use ",
                "add ",
                "if ",
                "elif ",
                "while ",
                "for ",
                "return ",
                "def ",
                "key ",
                "on ",
                "size ",
                "color ",
            )
        ):
            return False
        if not tokens:
            return False
        prefix = line[: tokens[0].start_column].strip()
        if not prefix or any(symbol in prefix for symbol in ("=", "(", ")", ".", "[", "]")):
            return False
        if prefix.split()[0] in NON_TEXT_STATEMENTS:
            return False
        return bool(re.fullmatch(r"[A-Za-z_]\w*(?:\s+\S+)*", prefix))

    @staticmethod
    def _add_neighbors(nodes: list[TextNode]) -> None:
        for index, node in enumerate(nodes):
            node.context["previous_statement_fingerprint"] = (
                bytes_hash(nodes[index - 1].token.raw.encode()) if index else None
            )
            node.context["next_statement_fingerprint"] = (
                bytes_hash(nodes[index + 1].token.raw.encode()) if index + 1 < len(nodes) else None
            )


def structural_fingerprint(text: str, nodes: list[TextNode]) -> str:
    rendered = text
    for node in sorted(nodes, key=lambda item: item.token.content_start, reverse=True):
        rendered = (
            rendered[: node.token.content_start]
            + "<FTIF_TEXT>"
            + rendered[node.token.content_end :]
        )
    return bytes_hash(rendered.encode("utf-8"))


def _line_starts(text: str) -> list[int]:
    starts = [0]
    starts.extend(index + 1 for index, char in enumerate(text) if char == "\n")
    return starts


def _statement_end(text: str, starts: list[int], tokens: list[StringToken]) -> int:
    last_line = max(token.end_line for token in tokens)
    return starts[last_line] if last_line < len(starts) else len(text)
