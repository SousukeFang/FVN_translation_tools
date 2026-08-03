from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from .common import StrictModel, VersionedDocument, utc_now


class UnitType(StrEnum):
    DIALOGUE = "dialogue"
    DIALOGUE_EXTENSION = "dialogue_extension"
    NARRATION = "narration"
    SCREEN_TEXT = "screen_text"
    MENU_CHOICE = "menu_choice"
    UI_TEXT = "ui_text"
    UI_BUTTON = "ui_button"
    CHARACTER_NAME = "character_name"
    NOTIFICATION = "notification"
    INPUT_PROMPT = "input_prompt"
    ACCESSIBILITY_TEXT = "accessibility_text"
    OTHER_VISIBLE_TEXT = "other_visible_text"


class TranslationStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    TRANSLATED = "translated"
    REVIEWED = "reviewed"
    SKIPPED = "skipped"
    FAILED = "failed"


class ValidationStatus(StrEnum):
    UNCHECKED = "unchecked"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ApplyStatus(StrEnum):
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    APPLY_FAILED = "apply_failed"


class TranslationState(StrictModel):
    status: TranslationStatus = TranslationStatus.PENDING
    origin: str | None = None
    provider: str | None = None
    model: str | None = None
    prompt_version: str | None = None
    translated_at: datetime | None = None


class ValidationState(StrictModel):
    status: ValidationStatus = ValidationStatus.UNCHECKED
    issue_ids: list[str] = Field(default_factory=list)


class ApplyState(StrictModel):
    status: ApplyStatus = ApplyStatus.NOT_APPLIED
    applied_at: datetime | None = None


class TranslationUnit(VersionedDocument):
    schema_: str = Field(default="ftif-unit/v1", alias="schema", serialization_alias="schema")
    unit_id: str
    sequence: int = Field(ge=0)
    segment_id: str
    scene_id: str | None = None
    type: UnitType
    speaker: str | None = None
    source_text: str
    target_text: str = ""
    source_fingerprint: str
    protected_tokens: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    origin: dict[str, Any] = Field(default_factory=dict)
    constraints: dict[str, Any] = Field(default_factory=dict)
    translation: TranslationState = Field(default_factory=TranslationState)
    validation: ValidationState = Field(default_factory=ValidationState)
    apply: ApplyState = Field(default_factory=ApplyState)
    adapter_data: dict[str, Any] = Field(default_factory=dict)
    revision: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validate_tokens(self) -> "TranslationUnit":
        if len(self.protected_tokens) != len(set(self.protected_tokens)):
            raise ValueError("protected_tokens must not contain duplicates")
        return self
