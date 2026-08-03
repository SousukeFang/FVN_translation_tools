import json
from hashlib import sha256
from pathlib import Path
from typing import Any


def bytes_hash(data: bytes) -> str:
    return f"sha256:{sha256(data).hexdigest()}"


def file_hash(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return bytes_hash(payload.encode("utf-8"))
