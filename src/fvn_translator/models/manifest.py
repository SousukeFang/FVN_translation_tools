from datetime import datetime

from pydantic import Field

from .common import VersionedDocument, utc_now


class Manifest(VersionedDocument):
    schema_: str = Field(default="ftif-manifest/v1", alias="schema", serialization_alias="schema")
    project_id: str
    project_name: str
    source_language: str = "en"
    target_language: str = "zh-CN"
    source_format: str
    adapter_id: str
    adapter_version: str
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    source_root: str
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    schema_versions: dict[str, str] = Field(default_factory=lambda: {"ftif": "v1"})
