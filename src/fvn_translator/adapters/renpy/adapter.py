from __future__ import annotations

from pathlib import Path

from fvn_translator.adapters.base import (
    AdapterConfig,
    ApplyResult,
    DetectionResult,
    ExtractionResult,
    SourceFile,
    ValidationReport,
)
from fvn_translator.models import TranslationUnit
from fvn_translator.profiles import FVNProfile, ProfileRegistry, default_profile_registry

from .detector import detect_renpy
from .discovery import discover_renpy_files
from .extractor import RenPyExtractor
from .validator import RenPyValidator
from .writer import RenPyWriter, prepare_script_staging


class RenPyAdapter:
    adapter_id = "renpy"
    adapter_version = "1.0.0"
    supported_ftif_versions: tuple[str, ...] = ("v1",)

    def __init__(self, profiles: ProfileRegistry | None = None) -> None:
        self.profiles = profiles or default_profile_registry()
        self._selected_profile_id: str | None = None

    @property
    def selected_profile_id(self) -> str | None:
        return self._selected_profile_id

    def detect(self, source_root: Path) -> DetectionResult:
        return detect_renpy(source_root)

    def discover_files(self, source_root: Path, config: AdapterConfig) -> list[SourceFile]:
        profile = self._profile(source_root, config)
        rules = profile.get_file_rules() if profile else None
        language = config.options.get("target_language")
        return discover_renpy_files(
            source_root,
            rules,
            target_language=str(language) if language else None,
        )

    def extract(
        self, source_root: Path, files: list[SourceFile], config: AdapterConfig
    ) -> ExtractionResult:
        return RenPyExtractor(self._profile(source_root, config)).extract(source_root, files)

    def apply(
        self,
        source_root: Path,
        staging_root: Path,
        units: list[TranslationUnit],
        config: AdapterConfig,
    ) -> ApplyResult:
        prepare_full = bool(config.options.get("full_staging", False)) or bool(
            config.options.get("lint_enabled", False)
        )
        if not prepare_full:
            profile = self._profile(source_root, config)
            rules = profile.get_file_rules() if profile else None
            language = config.options.get("target_language")
            support_files = discover_renpy_files(
                source_root,
                rules,
                target_language=str(language) if language else None,
            )
            prepare_script_staging(
                source_root,
                staging_root,
                [source.relative_path for source in support_files],
            )
        written = RenPyWriter().write(
            source_root,
            staging_root,
            units,
            prepare_full_project=prepare_full,
        )
        return ApplyResult(written_files=written)

    def validate(
        self, staging_root: Path, units: list[TranslationUnit], config: AdapterConfig
    ) -> ValidationReport:
        profile = self._profile(staging_root, config)
        return RenPyValidator(profile).validate(staging_root, units, config)

    def _profile(self, source_root: Path, config: AdapterConfig) -> FVNProfile | None:
        requested = config.options.get("profile_id")
        if requested:
            profile = self.profiles.create(str(requested))
            self._selected_profile_id = profile.profile_id
            return profile
        if self._selected_profile_id:
            return self.profiles.create(self._selected_profile_id)
        matches = [
            profile for profile in self.profiles.all() if profile.detect(source_root).supported
        ]
        if len(matches) > 1:
            raise ValueError("Multiple FVN profiles matched; configure profile_id explicitly")
        if matches:
            self._selected_profile_id = matches[0].profile_id
            return matches[0]
        return None
