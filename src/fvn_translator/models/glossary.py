from pydantic import Field

from .common import VersionedDocument


class GlossaryEntry(VersionedDocument):
    schema_: str = Field(default="ftif-glossary/v1", alias="schema", serialization_alias="schema")
    term_id: str
    source_term: str
    target_term: str = ""
    description: str = ""
    case_sensitive: bool = False
    evidence_unit_ids: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    confirmed: bool = False
    version: int = Field(default=1, ge=1)
