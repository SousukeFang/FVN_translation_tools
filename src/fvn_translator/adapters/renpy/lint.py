from __future__ import annotations

import re
import subprocess
from pathlib import Path

from fvn_translator.adapters.base import ValidationReport
from fvn_translator.models import Issue, Severity, TranslationUnit

LINT_LOCATION = re.compile(r"(?P<path>[^\r\n:]+\.rpy):(?P<line>\d+)")


class RenPyLintRunner:
    def run(
        self,
        staging_root: Path,
        *,
        sdk_path: Path | None,
        units: list[TranslationUnit],
    ) -> ValidationReport:
        if sdk_path is None:
            return ValidationReport(
                issues=[
                    Issue(
                        issue_id="renpy-lint-not-run",
                        code="RENPY_LINT_NOT_RUN",
                        severity=Severity.WARNING,
                        message="Ren'Py SDK is not configured; engine lint was not run",
                    )
                ]
            )
        launcher = self._launcher(sdk_path)
        if launcher is None:
            return ValidationReport(
                issues=[
                    Issue(
                        issue_id="renpy-lint-launcher-missing",
                        code="RENPY_LINT_NOT_RUN",
                        severity=Severity.ERROR,
                        message=f"Ren'Py launcher not found in {sdk_path}",
                    )
                ]
            )
        completed = subprocess.run(
            [str(launcher), str(staging_root), "lint"],
            cwd=sdk_path,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=300,
            check=False,
        )
        combined = "\n".join((completed.stdout, completed.stderr)).strip()
        issues: list[Issue] = []
        if completed.returncode:
            matches = list(LINT_LOCATION.finditer(combined))
            if not matches:
                matches = [None]
            for index, match in enumerate(matches):
                path = match.group("path").replace("\\", "/") if match else None
                line = int(match.group("line")) if match else None
                unit_id = _unit_at(units, path, line)
                issues.append(
                    Issue(
                        issue_id=f"renpy-lint:{index}:{path or 'project'}:{line or 0}",
                        code="RENPY_LINT_FAILED",
                        severity=Severity.ERROR,
                        message="Ren'Py lint failed",
                        unit_id=unit_id,
                        path=path,
                        line=line,
                        details={
                            "command": [str(launcher), str(staging_root), "lint"],
                            "exit_code": completed.returncode,
                            "stdout": completed.stdout,
                            "stderr": completed.stderr,
                        },
                    )
                )
        return ValidationReport(issues=issues)

    @staticmethod
    def _launcher(sdk_path: Path) -> Path | None:
        for name in ("renpy.exe", "renpy.sh", "renpy"):
            candidate = sdk_path / name
            if candidate.is_file():
                return candidate
        return None


def _unit_at(units: list[TranslationUnit], path: str | None, line: int | None) -> str | None:
    if path is None or line is None:
        return None
    normalized = path.replace("\\", "/")
    for unit in units:
        origin_path = str(unit.origin.get("path", ""))
        if normalized.endswith(origin_path) and int(unit.origin.get("line", -1)) == line:
            return unit.unit_id
    return None
