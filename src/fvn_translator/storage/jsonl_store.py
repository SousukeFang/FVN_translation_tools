import json
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from fvn_translator.core.atomic_io import atomic_write_jsonl
from fvn_translator.core.errors import DataIntegrityError

ModelT = TypeVar("ModelT", bound=BaseModel)


class JSONLStore(Generic[ModelT]):
    def __init__(self, path: Path, model: type[ModelT]) -> None:
        self.path = path
        self.model = model

    def read(self) -> list[ModelT]:
        if not self.path.exists():
            return []
        values: list[ModelT] = []
        with self.path.open("r", encoding="utf-8") as stream:
            for number, line in enumerate(stream, 1):
                if not line.strip():
                    continue
                try:
                    values.append(self.model.model_validate_json(line))
                except (ValueError, json.JSONDecodeError) as exc:
                    raise DataIntegrityError(
                        f"Invalid JSONL at {self.path}:{number}", detail=str(exc)
                    ) from exc
        return values

    def write(self, values: list[ModelT]) -> None:
        atomic_write_jsonl(
            self.path,
            [value.model_dump(mode="json", by_alias=True, exclude_none=True) for value in values],
        )
