from pathlib import Path

from fvn_translator.adapters.base import ValidationReport
from fvn_translator.models import Issue, Severity, TranslationUnit
from fvn_translator.profiles.base import (
    CharacterDefinition,
    CustomTextSink,
    FileDiscoveryRules,
    ParseContext,
    ProfileDetectionResult,
    ProtectedTokenRules,
    SceneRules,
)

from .character_map import load_character_map
from .config import FILE_RULES, SCENE_RULES
from .custom_statements import CUSTOM_TEXT_SINKS
from .validation_rules import REQUIRED_PROJECT_FILES


class RememberTheFlowersProfile:
    profile_id = "remember-the-flowers-ii"
    profile_version = "1.0.0"
    engine_adapter_id = "renpy"

    def detect(self, source_root: Path) -> ProfileDetectionResult:
        options = source_root / "game/options.rpy"
        prologue = source_root / "game/story/prologue.rpy"
        if not options.is_file():
            return ProfileDetectionResult(supported=False, confidence=0, reason="options missing")
        text = options.read_bytes().decode("utf-8-sig", errors="replace")
        named = "Remember the Flowers - Part II" in text
        supported = named and prologue.is_file()
        return ProfileDetectionResult(
            supported=supported,
            confidence=1.0 if supported else 0.4 if named else 0.0,
            reason="config.name and story/prologue.rpy" if supported else "signature incomplete",
        )

    def get_file_rules(self) -> FileDiscoveryRules:
        return FILE_RULES

    def get_character_map(self, source_root: Path) -> dict[str, CharacterDefinition]:
        return load_character_map(source_root)

    def get_custom_text_sinks(self) -> list[CustomTextSink]:
        return list(CUSTOM_TEXT_SINKS)

    def get_scene_rules(self) -> SceneRules:
        return SCENE_RULES

    def get_protected_token_rules(self) -> ProtectedTokenRules:
        return ProtectedTokenRules()

    def enrich_unit(self, unit: TranslationUnit, context: ParseContext) -> TranslationUnit:
        return unit

    def validate_project(
        self, staging_root: Path, units: list[TranslationUnit]
    ) -> ValidationReport:
        staged_paths = {str(unit.origin["path"]) for unit in units}
        issues = []
        for relative in REQUIRED_PROJECT_FILES:
            if relative in staged_paths and not (staging_root / relative).is_file():
                issues.append(
                    Issue(
                        issue_id=f"rtf-required:{relative}",
                        code="RTF_REQUIRED_FILE_MISSING",
                        severity=Severity.ERROR,
                        message="Required project file is missing from staging",
                        path=relative,
                    )
                )
        return ValidationReport(issues=issues)
