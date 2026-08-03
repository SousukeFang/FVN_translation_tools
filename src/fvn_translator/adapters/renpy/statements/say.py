import re

ATTRIBUTE_PREFIX = re.compile(r"^-?[A-Za-z_]\w*(?:\s+-?[A-Za-z_]\w*)*$")


def parse_say_prefix(prefix: str, disallowed: frozenset[str]) -> tuple[str, tuple[str, ...]] | None:
    if not ATTRIBUTE_PREFIX.fullmatch(prefix):
        return None
    parts = prefix.split()
    if not parts or parts[0].lower() in disallowed:
        return None
    return parts[0], tuple(parts[1:])
