from uuid import NAMESPACE_URL, uuid5

from fvn_translator.models import Issue, Severity, TranslationUnit

from .placeholders import extract_placeholders


def validate_unit(unit: TranslationUnit) -> list[Issue]:
    issues: list[Issue] = []
    if unit.constraints.get("placeholder_mode") == "explicit":
        source = [
            token for token in unit.protected_tokens for _ in range(unit.source_text.count(token))
        ]
        target = [
            token for token in unit.protected_tokens for _ in range(unit.target_text.count(token))
        ]
    else:
        printf_format = unit.constraints.get("printf_format") is True
        source = extract_placeholders(unit.source_text, printf_format=printf_format)
        target = extract_placeholders(unit.target_text, printf_format=printf_format)
    # Explicit declarations remain authoritative even when automatic inference
    # deliberately declines an ambiguous token such as printf's ``% s``.
    declared_changed = any(
        unit.source_text.count(token) != unit.target_text.count(token)
        for token in unit.protected_tokens
    )
    if sorted(source) != sorted(target) or declared_changed:
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
