import json
import os
from pathlib import Path
from uuid import uuid4

from fvn_translator.core.atomic_io import atomic_write_json, atomic_write_text
from fvn_translator.core.errors import WorkspaceLockedError

DIRECTORIES = ("intermediate", "state", "runs", "backups", "staging", "logs", "exports")
INTERMEDIATE_FILES = (
    "units.jsonl",
    "characters.json",
    "glossary.json",
    "scene_summaries.jsonl",
    "issues.jsonl",
    "revisions.jsonl",
)


class Workspace:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.intermediate = self.root / "intermediate"
        self.state = self.root / "state"
        self.runs = self.root / "runs"
        self.backups = self.root / "backups"
        self.staging = self.root / "staging"
        self.lock_path = self.state / "workspace.lock"
        self._lock_owned = False

    @classmethod
    def create(cls, root: Path) -> "Workspace":
        workspace = cls(root)
        for directory in DIRECTORIES:
            (workspace.root / directory).mkdir(parents=True, exist_ok=True)
        for name in INTERMEDIATE_FILES:
            path = workspace.intermediate / name
            if not path.exists():
                atomic_write_text(path, "[]\n" if name.endswith(".json") else "")
        return workspace

    def acquire(self) -> None:
        self.state.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise WorkspaceLockedError(f"Workspace is already open: {self.root}") from exc
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump({"pid": os.getpid(), "token": uuid4().hex}, stream)
        self._lock_owned = True

    def release(self) -> None:
        if self._lock_owned and self.lock_path.exists():
            self.lock_path.unlink()
        self._lock_owned = False

    def write_manifest(self, payload: dict[str, object]) -> None:
        atomic_write_json(self.intermediate / "manifest.json", payload)

    def __enter__(self) -> "Workspace":
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()
