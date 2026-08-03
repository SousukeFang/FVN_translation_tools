from pathlib import Path


def ensure_within(root: Path, candidate: Path) -> Path:
    resolved_root = root.resolve()
    resolved = candidate.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError(f"Path escapes root: {candidate}")
    return resolved


def relative_posix(root: Path, path: Path) -> str:
    return ensure_within(root, path).relative_to(root.resolve()).as_posix()
