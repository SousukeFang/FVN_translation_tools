from pydantic import Field

from .common import VersionedDocument


class Character(VersionedDocument):
    schema_: str = Field(default="ftif-character/v1", alias="schema", serialization_alias="schema")
    character_id: str
    names: list[str]
    description: str = ""
    speech_style: str = ""
    evidence_unit_ids: list[str] = Field(default_factory=list)
    confirmed: bool = False
    version: int = Field(default=1, ge=1)
