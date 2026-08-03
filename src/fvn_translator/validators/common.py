from uuid import NAMESPACE_URL, uuid5

from fvn_translator.models import Issue, Severity, TranslationUnit

from .placeholders import extract_placeholders


def validate_unit(unit: TranslationUnit) -> list[Issue]:
    issues: list[Issue] = []
    source = extract_placeholders(unit.source_text)
    target = extract_placeholders(unit.target_text)
    if sorted(source) != sorted(target):
        issues.append(
            _issue(
                unit,
                "PROTECTED_TOKEN_CHANGED",
                Severity.ERROR,
                "Protected tags or placeholders changed",
                {"source": source, "target": target},
            )
        )
    if "“" in unit.target_text or "”" in unit.target_text:
        issues.append(
            _issue(
                unit, "SMART_QUOTE", Severity.WARNING, "Target contains typographic double quotes"
            )
        )
    if unit.translation.status in {"translated", "reviewed"} and not unit.target_text.strip():
        issues.append(
            _issue(unit, "TARGET_EMPTY", Severity.ERROR, "Translated unit has an empty target")
        )
    return issues


def _issue(
    unit: TranslationUnit,
    code: str,
    severity: Severity,
    message: str,
    details: dict[str, object] | None = None,
) -> Issue:
    identifier = str(uuid5(NAMESPACE_URL, f"{unit.unit_id}:{code}"))
    return Issue(
        issue_id=identifier,
        code=code,
        severity=severity,
        message=message,
        unit_id=unit.unit_id,
        path=unit.origin.get("path"),
        line=unit.origin.get("line"),
        details=details or {},
    )
