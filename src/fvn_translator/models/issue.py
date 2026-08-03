from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from .common import VersionedDocument, utc_now


class Severity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class Issue(VersionedDocument):
    schema_: str = Field(default="ftif-issue/v1", alias="schema", serialization_alias="schema")
    issue_id: str
    code: str
    severity: Severity
    message: str
    unit_id: str | None = None
    path: str | None = None
    line: int | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False
    created_at: datetime = Field(default_factory=utc_now)
