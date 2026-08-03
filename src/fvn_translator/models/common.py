from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(UTC)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class ExtensibleModel(BaseModel):
    model_config = ConfigDict(extra="allow", validate_assignment=True)


class VersionedDocument(StrictModel):
    schema_: str = Field(alias="schema", serialization_alias="schema")


JsonObject = dict[str, Any]
