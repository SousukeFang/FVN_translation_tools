from datetime import datetime

from pydantic import Field

from .common import VersionedDocument, utc_now


class SceneSummary(VersionedDocument):
    schema_: str = Field(default="ftif-summary/v1", alias="schema", serialization_alias="schema")
    scene_id: str
    previous_summary: str = ""
    summary: str
    source_unit_ids: list[str]
    prompt_version: str
    created_at: datetime = Field(default_factory=utc_now)
