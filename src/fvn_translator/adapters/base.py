from pathlib import Path
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from fvn_translator.models import Issue, TranslationUnit


class AdapterModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AdapterConfig(AdapterModel):
    options: dict[str, Any] = Field(default_factory=dict)


class DetectionResult(AdapterModel):
    supported: bool
    confidence: float = Field(ge=0, le=1)
    reason: str = ""


class SourceFile(AdapterModel):
    relative_path: str
    fingerprint: str
    encoding: str = "utf-8"
    newline: str = "\n"
    has_bom: bool = False
    size: int = Field(default=0, ge=0)
    category: str = "other"
    extracted_unit_count: int = Field(default=0, ge=0)


class ExtractionResult(AdapterModel):
    units: list[TranslationUnit]
    files: list[SourceFile]
    issues: list[Issue] = Field(default_factory=list)


class ApplyResult(AdapterModel):
    written_files: list[str]


class ValidationReport(AdapterModel):
    issues: list[Issue]

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)


class FVNAdapter(Protocol):
    adapter_id: str
    adapter_version: str
    supported_ftif_versions: tuple[str, ...]

    def detect(self, source_root: Path) -> DetectionResult: ...
    def discover_files(self, source_root: Path, config: AdapterConfig) -> list[SourceFile]: ...
    def extract(
        self, source_root: Path, files: list[SourceFile], config: AdapterConfig
    ) -> ExtractionResult: ...
    def apply(
        self,
        source_root: Path,
        staging_root: Path,
        units: list[TranslationUnit],
        config: AdapterConfig,
    ) -> ApplyResult: ...
    def validate(
        self, staging_root: Path, units: list[TranslationUnit], config: AdapterConfig
    ) -> ValidationReport: ...
