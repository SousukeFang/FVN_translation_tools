import re

PLACEHOLDER = re.compile(
    r"\{/?[A-Za-z][^}]*\}|\[[A-Za-z_][^\]]*\]|"
    r"%(?:\([^)]+\))?[#0 +\-]?(?:\d+|\*)?(?:\.\d+)?[diouxXeEfFgGcrs%]"
)


def extract_placeholders(text: str) -> list[str]:
    return PLACEHOLDER.findall(text)
