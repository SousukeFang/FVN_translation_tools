"""Generate the checked-in FTIF v1 JSON Schemas from Pydantic models."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fvn_translator.core.atomic_io import atomic_write_json  # noqa: E402
from fvn_translator.models import (  # noqa: E402
    Character,
    GlossaryEntry,
    Issue,
    Manifest,
    SceneSummary,
    TranslationUnit,
)

SCHEMAS = {
    "ftif-manifest-v1.schema.json": Manifest,
    "ftif-unit-v1.schema.json": TranslationUnit,
    "ftif-character-v1.schema.json": Character,
    "ftif-glossary-v1.schema.json": GlossaryEntry,
    "ftif-summary-v1.schema.json": SceneSummary,
    "ftif-issue-v1.schema.json": Issue,
}


def main() -> None:
    target = ROOT / "Docs" / "schemas"
    for name, model in SCHEMAS.items():
        schema = model.model_json_schema(by_alias=True)
        schema["$id"] = f"https://fvn-translator.local/schemas/{name}"
        atomic_write_json(target / name, schema)


if __name__ == "__main__":
    main()
