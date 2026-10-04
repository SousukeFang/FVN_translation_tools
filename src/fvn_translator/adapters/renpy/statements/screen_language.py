import re

from fvn_translator.models import UnitType

SCREEN_KEYWORDS = {
    "text": UnitType.UI_TEXT,
    "label": UnitType.UI_TEXT,
    "tooltip": UnitType.UI_TEXT,
    "textbutton": UnitType.UI_BUTTON,
    "alt": UnitType.ACCESSIBILITY_TEXT,
}


def is_parenthesized_literal(before: str, after: str) -> bool:
    """Accept a literal-only grouping, followed by SL properties or a block."""
    opening = re.sub(r"\s+", "", before)
    if not opening or set(opening) != {"("}:
        return False
    remaining = after
    for _ in opening:
        remaining = remaining.lstrip()
        if not remaining.startswith(")"):
            return False
        remaining = remaining[1:]
    remaining = remaining.lstrip()
    if not remaining or remaining.startswith((":", "#")):
        return True
    property_name = re.match(r"([A-Za-z_]\w*)\s+", remaining)
    return bool(
        property_name
        and property_name[1]
        not in {
            "if",
            "else",
            "for",
            "in",
            "is",
            "not",
            "and",
            "or",
        }
    )
