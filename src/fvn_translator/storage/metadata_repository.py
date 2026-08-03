import json
from pathlib import Path
from typing import Generic, TypeVar

from pydantic import BaseModel

from fvn_translator.core.atomic_io import atomic_write_json

ModelT = TypeVar("ModelT", bound=BaseModel)


class MetadataRepository(Generic[ModelT]):
    """Atomic repository for authoritative JSON arrays such as characters and glossary."""

    def __init__(self, path: Path, model: type[ModelT]) -> None:
        self.path = path
        self.model = model

    def load(self) -> list[ModelT]:
        if not self.path.exists():
            return []
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Expected a JSON array: {self.path}")
        return [self.model.model_validate(item) for item in payload]

    def save(self, values: list[ModelT]) -> None:
        atomic_write_json(
            self.path,
            [value.model_dump(mode="json", by_alias=True, exclude_none=True) for value in values],
        )

    def update(self, identifier: str, changes: dict[str, object], *, id_field: str) -> ModelT:
        values = self.load()
        for index, value in enumerate(values):
            if getattr(value, id_field) == identifier:
                payload = value.model_dump(by_alias=True)
                payload.update(changes)
                payload["version"] = int(payload.get("version", 0)) + 1
                values[index] = self.model.model_validate(payload)
                self.save(values)
                return values[index]
        raise KeyError(identifier)
