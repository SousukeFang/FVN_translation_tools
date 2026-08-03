from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from fvn_translator.adapters.base import AdapterConfig, SourceFile, ValidationReport
from fvn_translator.core.hashing import file_hash
from fvn_translator.models import Issue, Severity, TranslationUnit
from fvn_translator.profiles.base import FVNProfile

from .extractor import RenPyExtractor
from .lint import RenPyLintRunner
from .protected_tokens import compare_signatures


class RenPyValidator:
    def __init__(self, profile: FVNProfile | None = None) -> None:
        self.profile = profile

    def validate(
        self, staging_root: Path, units: list[TranslationUnit], config: AdapterConfig
    ) -> ValidationReport:
        issues: list[Issue] = []
        grouped: dict[str, list[TranslationUnit]] = defaultdict(list)
        for unit in units:
            grouped[str(unit.origin["path"])].append(unit)
        for relative in sorted(grouped):
            expected_units = grouped[relative]
            path = staging_root / relative
            if not path.is_file():
                issues.append(
                    self._issue("RENPY_FILE_MISSING", relative, 0, "Staging file missing")
                )
                continue
            data = path.read_bytes()
            try:
                data.decode("utf-8-sig")
            except UnicodeDecodeError:
                issues.append(self._issue("RENPY_ENCODING", relative, 0, "File is not UTF-8"))
                continue
            expected_bom = bool(expected_units[0].adapter_data.get("file_has_bom", False))
            if data.startswith(b"\xef\xbb\xbf") != expected_bom:
                issues.append(self._issue("RENPY_BOM_CHANGED", relative, 0, "UTF-8 BOM changed"))
            expected_newline = str(expected_units[0].adapter_data.get("file_newline", "\n"))
            actual_newline = "\r\n" if b"\r\n" in data else "\n"
            if actual_newline != expected_newline:
                issues.append(self._issue("RENPY_NEWLINE_CHANGED", relative, 0, "Newline changed"))
            source_file = SourceFile(
                relative_path=relative,
                fingerprint=file_hash(path),
                encoding="utf-8",
                newline=actual_newline,
                has_bom=data.startswith(b"\xef\xbb\xbf"),
                size=len(data),
            )
            speakers = {unit.speaker for unit in expected_units if unit.speaker}
            actual = RenPyExtractor(
                self.profile,
                allowed_speakers=speakers,
            ).extract(staging_root, [source_file])
            issues.extend(actual.issues)
            actual_by_id = {unit.unit_id: unit for unit in actual.units}
            for expected in expected_units:
                found = actual_by_id.get(expected.unit_id)
                if found is None:
                    issues.append(
                        self._issue(
                            "RENPY_UNIT_NOT_REEXTRACTED",
                            relative,
                            int(expected.origin["line"]),
                            "Translated unit could not be re-extracted",
                            expected.unit_id,
                        )
                    )
                    continue
                desired = expected.target_text or expected.source_text
                if found.source_text != desired:
                    issues.append(
                        self._issue(
                            "RENPY_TEXT_WRITE_MISMATCH",
                            relative,
                            int(expected.origin["line"]),
                            "Re-extracted text differs from target",
                            expected.unit_id,
                        )
                    )
                if found.speaker != expected.speaker or found.adapter_data.get(
                    "speaker_attributes"
                ) != expected.adapter_data.get("speaker_attributes"):
                    issues.append(
                        self._issue(
                            "RENPY_SAY_STRUCTURE_CHANGED",
                            relative,
                            int(expected.origin["line"]),
                            "Speaker or attributes changed",
                            expected.unit_id,
                        )
                    )
                expected_signature = dict(expected.adapter_data["protection_signature"])
                actual_signature = dict(found.adapter_data["protection_signature"])
                for problem in compare_signatures(expected_signature, actual_signature):
                    issues.append(
                        self._issue(
                            problem.code,
                            relative,
                            int(expected.origin["line"]),
                            problem.message,
                            expected.unit_id,
                        )
                    )
            actual_structure = (
                actual.units[0].adapter_data.get("file_structure_fingerprint")
                if actual.units
                else None
            )
            expected_structure = expected_units[0].adapter_data.get("file_structure_fingerprint")
            if actual_structure != expected_structure:
                issues.append(
                    self._issue(
                        "RENPY_STRUCTURE_CHANGED",
                        relative,
                        0,
                        "Non-translatable script structure changed",
                    )
                )
        if self.profile:
            issues.extend(self.profile.validate_project(staging_root, units).issues)
        if bool(config.options.get("lint_enabled", False)):
            sdk_value = config.options.get("sdk_path")
            sdk_path = Path(str(sdk_value)) if sdk_value else None
            issues.extend(
                RenPyLintRunner().run(staging_root, sdk_path=sdk_path, units=units).issues
            )
        return ValidationReport(issues=issues)

    @staticmethod
    def _issue(
        code: str,
        path: str,
        line: int,
        message: str,
        unit_id: str | None = None,
    ) -> Issue:
        return Issue(
            issue_id=f"{code.lower()}:{path}:{line}:{unit_id or 'file'}",
            code=code,
            severity=Severity.ERROR,
            message=message,
            unit_id=unit_id,
            path=path,
            line=line or None,
        )
