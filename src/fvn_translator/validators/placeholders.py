import re

PLACEHOLDER = re.compile(
    r"\{/?[A-Za-z][^}]*\}|\[[A-Za-z_][^\]]*\]|"
    r"%(?P<mapping>\([^)]+\))?(?P<flags>[#0 +\-]*)"
    r"(?P<width>\d+|\*)?(?P<precision>\.(?:\d+|\*))?[diouxXeEfFgGcrs%]"
)


def extract_placeholders(text: str, *, printf_format: bool = False) -> list[str]:
    """Infer tokens without reading ordinary percentage prose as a space-flag format.

    A mapping key, width or precision makes a space-flag conversion explicit.
    Otherwise callers must identify printf semantics to recognize ``% s``.
    """
    result = []
    for match in PLACEHOLDER.finditer(text):
        if (
            not printf_format
            and " " in (match.group("flags") or "")
            and not any(match.group(key) for key in ("mapping", "width", "precision"))
        ):
            continue
        result.append(match.group())
    return result
