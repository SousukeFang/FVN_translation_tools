from fvn_translator.models import UnitType

SCREEN_KEYWORDS = {
    "text": UnitType.UI_TEXT,
    "label": UnitType.UI_TEXT,
    "tooltip": UnitType.UI_TEXT,
    "textbutton": UnitType.UI_BUTTON,
    "alt": UnitType.ACCESSIBILITY_TEXT,
}
