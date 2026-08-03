from pathlib import Path
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field

from fvn_translator.adapters.base import ValidationReport
from fvn_translator.models import TranslationUnit, UnitType


class ProfileModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ProfileDetectionResult(ProfileModel):
    supported: bool
    confidence: float = Field(ge=0, le=1)
    reason: str = ""


class FileDiscoveryRules(ProfileModel):
    include: tuple[str, ...] = ("game/**/*.rpy",)
    exclude: tuple[str, ...] = ()
    categories: dict[str, tuple[str, ...]] = Field(default_factory=dict)


class CharacterDefinition(ProfileModel):
    speaker_id: str
    display_name: str | None = None
    status: str = "resolved"
    source_path: str | None = None
    source_line: int | None = None


class CustomTextSink(ProfileModel):
    function: str
    argument: int = Field(default=0, ge=0)
    unit_type: UnitType = UnitType.OTHER_VISIBLE_TEXT


class SceneRules(ProfileModel):
    primary_segment: str = "file"
    boundaries: tuple[str, ...] = ("label", "scene")
    structured_comments: tuple[str, ...] = ()


class ProtectedTokenRules(ProfileModel):
    extra_self_closing_tags: tuple[str, ...] = ()


class ParseContext(ProfileModel):
    relative_path: str
    label: str
    scene_id: str


class FVNProfile(Protocol):
    profile_id: str
    profile_version: str
    engine_adapter_id: str

    def detect(self, source_root: Path) -> ProfileDetectionResult: ...
    def get_file_rules(self) -> FileDiscoveryRules: ...
    def get_character_map(self, source_root: Path) -> dict[str, CharacterDefinition]: ...
    def get_custom_text_sinks(self) -> list[CustomTextSink]: ...
    def get_scene_rules(self) -> SceneRules: ...
    def get_protected_token_rules(self) -> ProtectedTokenRules: ...
    def enrich_unit(self, unit: TranslationUnit, context: ParseContext) -> TranslationUnit: ...
    def validate_project(
        self, staging_root: Path, units: list[TranslationUnit]
    ) -> ValidationReport: ...
