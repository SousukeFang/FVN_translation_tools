from fnmatch import fnmatch
from pathlib import Path

from fvn_translator.adapters.base import SourceFile
from fvn_translator.core.hashing import file_hash
from fvn_translator.profiles.base import FileDiscoveryRules

DEFAULT_EXCLUDES = (
    "**/.git/**",
    "game/cache/**",
    "game/saves/**",
    "**/backups/**",
    "**/staging/**",
)


def discover_renpy_files(
    source_root: Path,
    rules: FileDiscoveryRules | None = None,
    *,
    target_language: str | None = None,
) -> list[SourceFile]:
    rules = rules or FileDiscoveryRules()
    excludes = [*DEFAULT_EXCLUDES, *rules.exclude]
    if target_language:
        excludes.append(f"game/tl/{target_language}/**")
    found: list[SourceFile] = []
    game = source_root / "game"
    if not game.is_dir():
        return found
    for path in sorted(game.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".rpy":
            continue
        relative = path.relative_to(source_root).as_posix()
        if not _matches_any(relative, rules.include) or _matches_any(relative, excludes):
            continue
        data = path.read_bytes()
        bom = data.startswith(b"\xef\xbb\xbf")
        data.decode("utf-8-sig")
        newline = "\r\n" if b"\r\n" in data else "\n"
        found.append(
            SourceFile(
                relative_path=relative,
                fingerprint=file_hash(path),
                encoding="utf-8",
                newline=newline,
                has_bom=bom,
                size=len(data),
                category=_category(relative, rules),
            )
        )
    return found


def _matches_any(path: str, patterns: tuple[str, ...] | list[str]) -> bool:
    return any(_matches(path, pattern) for pattern in patterns)


def _matches(path: str, pattern: str) -> bool:
    if fnmatch(path, pattern):
        return True
    if "/**/" in pattern and fnmatch(path, pattern.replace("/**/", "/")):
        return True
    return pattern.endswith("/**") and (path == pattern[:-3] or path.startswith(pattern[:-2]))


def _category(path: str, rules: FileDiscoveryRules) -> str:
    for category, patterns in rules.categories.items():
        if _matches_any(path, patterns):
            return category
    return "other"
