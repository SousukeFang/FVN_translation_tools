from collections import Counter


def compare_protected_tokens(source_tokens: list[str], target: str) -> tuple[bool, list[str]]:
    expected = Counter(source_tokens)
    actual = Counter(token for token in source_tokens if token in target)
    missing = list((expected - actual).elements())
    return not missing, missing
