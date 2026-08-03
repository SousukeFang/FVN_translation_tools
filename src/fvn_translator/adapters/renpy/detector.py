from pathlib import Path

from fvn_translator.adapters.base import DetectionResult


def detect_renpy(source_root: Path) -> DetectionResult:
    game = source_root / "game"
    if not game.is_dir():
        return DetectionResult(supported=False, confidence=0, reason="game directory missing")
    rpy = any(path.suffix.lower() == ".rpy" for path in game.rglob("*"))
    options = (game / "options.rpy").is_file()
    confidence = 1.0 if rpy and options else 0.7 if rpy else 0.0
    return DetectionResult(
        supported=rpy,
        confidence=confidence,
        reason="game/options.rpy and .rpy files" if options else ".rpy files",
    )
