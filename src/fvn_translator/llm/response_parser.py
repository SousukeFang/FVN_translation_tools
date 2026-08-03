from collections.abc import Iterable

from fvn_translator.core.errors import ResponseFormatError


def parse_translations(content: dict[str, object], expected_ids: Iterable[str]) -> dict[str, str]:
    expected = set(expected_ids)
    rows = content.get("translations")
    if not isinstance(rows, list):
        raise ResponseFormatError("Response must contain a translations list")
    parsed: dict[str, str] = {}
    for row in rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("unit_id"), str)
            or not isinstance(row.get("target_text"), str)
        ):
            raise ResponseFormatError("Each translation needs string unit_id and target_text")
        identifier = row["unit_id"]
        if identifier not in expected:
            raise ResponseFormatError(f"Unknown unit_id: {identifier}")
        if identifier in parsed:
            raise ResponseFormatError(f"Duplicate unit_id: {identifier}")
        parsed[identifier] = row["target_text"]
    missing = expected - parsed.keys()
    if missing:
        raise ResponseFormatError(f"Missing unit_id values: {', '.join(sorted(missing))}")
    return parsed
