"""Validate checked-in JSON/JSONL examples against Pydantic source models."""

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fvn_translator.models import (  # noqa: E402
    Character,
    GlossaryEntry,
    Issue,
    Manifest,
    SceneSummary,
    TranslationUnit,
)

DOCUMENTS = {
    "manifest": ("ftif-manifest-v1.schema.json", Manifest),
    "unit": ("ftif-unit-v1.schema.json", TranslationUnit),
    "character": ("ftif-character-v1.schema.json", Character),
    "glossary": ("ftif-glossary-v1.schema.json", GlossaryEntry),
    "summary": ("ftif-summary-v1.schema.json", SceneSummary),
    "issue": ("ftif-issue-v1.schema.json", Issue),
}


def main() -> None:
    workspace = ROOT / "examples" / "demo_workspace" / "intermediate"
    schemas: dict[str, Draft202012Validator] = {}
    for name, (filename, _) in DOCUMENTS.items():
        payload = json.loads((ROOT / "Docs" / "schemas" / filename).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(payload)
        schemas[name] = Draft202012Validator(payload)

    manifest = json.loads((workspace / "manifest.json").read_text(encoding="utf-8"))
    Manifest.model_validate(manifest)
    schemas["manifest"].validate(manifest)
    for line in (workspace / "units.jsonl").read_text(encoding="utf-8").splitlines():
        if line:
            payload = json.loads(line)
            TranslationUnit.model_validate(payload)
            schemas["unit"].validate(payload)
    for filename, model, schema_name in (
        ("characters.json", Character, "character"),
        ("glossary.json", GlossaryEntry, "glossary"),
    ):
        for payload in json.loads((workspace / filename).read_text(encoding="utf-8")):
            model.model_validate(payload)
            schemas[schema_name].validate(payload)
    for filename, model, schema_name in (
        ("scene_summaries.jsonl", SceneSummary, "summary"),
        ("issues.jsonl", Issue, "issue"),
    ):
        for line in (workspace / filename).read_text(encoding="utf-8").splitlines():
            if line:
                payload = json.loads(line)
                model.model_validate(payload)
                schemas[schema_name].validate(payload)
    print("FTIF examples are valid")


if __name__ == "__main__":
    main()
