from dataclasses import dataclass, field

from fvn_translator.models import Issue, UnitType


@dataclass(frozen=True, slots=True)
class StringToken:
    start: int
    end: int
    content_start: int
    content_end: int
    start_line: int
    end_line: int
    start_column: int
    end_column: int
    prefix: str
    quote: str
    raw: str
    raw_content: str
    value: str


@dataclass(frozen=True, slots=True)
class CommentToken:
    start: int
    end: int
    line: int
    column: int
    text: str


@dataclass(slots=True)
class LexResult:
    strings: list[StringToken] = field(default_factory=list)
    comments: list[CommentToken] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)


@dataclass(slots=True)
class TextNode:
    kind: str
    unit_type: UnitType
    token: StringToken
    statement_start: int
    statement_end: int
    start_line: int
    end_line: int
    label: str
    scene_id: str
    statement_index: int
    text_role: str = "text"
    speaker: str | None = None
    speaker_attributes: tuple[str, ...] = ()
    explicit_display_name: str | None = None
    extends_index: int | None = None
    context: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class ParseResult:
    nodes: list[TextNode] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)
    structure_fingerprint: str = ""
