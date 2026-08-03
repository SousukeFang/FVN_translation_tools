def is_menu_choice_suffix(suffix: str) -> bool:
    return suffix.split("#", 1)[0].strip().endswith(":")
