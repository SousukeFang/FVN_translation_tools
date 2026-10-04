"""File-based translation tasks for an agent, without a provider or API call."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from fvn_translator.core.atomic_io import atomic_write_json, atomic_write_jsonl
from fvn_translator.core.errors import DataIntegrityError
from fvn_translator.core.hashing import stable_hash
from fvn_translator.llm.request_builder import (
    TRANSLATION_PROMPT_VERSION,
    translation_request,
)
from fvn_translator.llm.response_parser import parse_translations
from fvn_translator.models import (
    Character,
    GlossaryEntry,
    Manifest,
    Severity,
    TranslationStatus,
    TranslationUnit,
    ValidationStatus,
)
from fvn_translator.storage import MetadataRepository, RevisionStore, UnitRepository, Workspace
from fvn_translator.validators import validate_unit


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise DataIntegrityError(f"Expected a JSON object: {path}")
    return value


def _visible_unit(unit: TranslationUnit, *, context: bool = False) -> dict[str, Any]:
    value = {
        "unit_id": unit.unit_id,
        "sequence": unit.sequence,
        "scene_id": unit.scene_id or unit.segment_id,
        "type": unit.type.value,
        "speaker": unit.speaker,
        "source_fingerprint": unit.source_fingerprint,
        "source_text": unit.source_text,
        "context": unit.context,
        "protected_tokens": unit.protected_tokens,
    }
    if context and unit.target_text:
        value["target_text"] = unit.target_text
    return value


class AgentTranslationService:
    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.repository = UnitRepository(workspace.intermediate / "units.jsonl")
        self.revisions = RevisionStore(workspace.intermediate / "revisions.jsonl")
        self.commit_path = workspace.state / "agent_import.json"

    def _manifest(self) -> Manifest:
        return Manifest.model_validate_json(
            (self.workspace.intermediate / "manifest.json").read_text(encoding="utf-8")
        )

    def export_batches(
        self,
        output_root: Path,
        *,
        max_chars: int = 12000,
        context_units: int = 3,
        unit_ids: set[str] | None = None,
    ) -> list[Path]:
        """Export pending/failed units in sequence; the budget includes the task JSON.

        Adjacent scenes can share a task. An individual unit is never split, so one
        unusually long unit or its metadata can exceed the character budget.
        An explicit ID selection limits both requested units and adjacent context;
        units outside it retain their existing translation status and revisions.
        """
        if max_chars <= 0 or context_units < 0:
            raise ValueError("max_chars must be positive and context_units non-negative")
        with self.workspace:
            self._recover_import()
            manifest = self._manifest()
            units = self.repository.load()
            positions = {unit.unit_id: index for index, unit in enumerate(units)}
            if unit_ids is not None:
                unknown_ids = unit_ids.difference(positions)
                if unknown_ids:
                    raise DataIntegrityError(f"Unknown unit IDs: {', '.join(sorted(unknown_ids))}")
            pending = [
                unit
                for unit in units
                if unit.translation.status in {TranslationStatus.PENDING, TranslationStatus.FAILED}
                and (unit_ids is None or unit.unit_id in unit_ids)
            ]
            characters = MetadataRepository(
                self.workspace.intermediate / "characters.json", Character
            ).load()
            glossary = MetadataRepository(
                self.workspace.intermediate / "glossary.json", GlossaryEntry
            ).load()
            export_id = uuid4().hex
            output_root = output_root.resolve()

            def make_task(batch: list[TranslationUnit], number: int) -> dict[str, Any]:
                request = translation_request(
                    run_id=export_id,
                    batch_id=f"batch-{number:05d}",
                    units=batch,
                    characters=characters,
                    glossary=glossary,
                    previous_summary="",
                    source_language=manifest.source_language,
                    target_language=manifest.target_language,
                )
                start = positions[batch[0].unit_id]
                end = positions[batch[-1].unit_id] + 1
                return {
                    "schema": "fvn-agent-task/v1",
                    "export_id": export_id,
                    "batch_id": request.batch_id,
                    "project_id": manifest.project_id,
                    "source_language": manifest.source_language,
                    "target_language": manifest.target_language,
                    "prompt_version": TRANSLATION_PROMPT_VERSION,
                    "instructions": request.system_prompt,
                    "characters": request.payload["characters"],
                    "glossary": request.payload["glossary"],
                    "context_before": [
                        _visible_unit(unit, context=True)
                        for unit in units[max(0, start - context_units) : start]
                        if unit_ids is None or unit.unit_id in unit_ids
                    ],
                    "context_after": [
                        _visible_unit(unit, context=True)
                        for unit in units[end : end + context_units]
                        if unit_ids is None or unit.unit_id in unit_ids
                    ],
                    "units": [_visible_unit(unit) for unit in batch],
                }

            tasks: list[dict[str, Any]] = []
            current: list[TranslationUnit] = []
            for unit in pending:
                candidate = make_task([*current, unit], len(tasks))
                size = len(json.dumps(candidate, ensure_ascii=False, indent=2)) + 1
                if current and size > max_chars:
                    tasks.append(make_task(current, len(tasks)))
                    current = [unit]
                else:
                    current.append(unit)
            if current:
                tasks.append(make_task(current, len(tasks)))
            paths: list[Path] = []
            batches = []
            for task in tasks:
                path = output_root / "tasks" / f"{task['batch_id']}.json"
                atomic_write_json(path, task)
                paths.append(path)
                batches.append(
                    {
                        "batch_id": task["batch_id"],
                        "task_path": str(path),
                        "task_fingerprint": stable_hash(task),
                        "inputs": [
                            {
                                "unit_id": unit["unit_id"],
                                "source_fingerprint": unit["source_fingerprint"],
                                "input_fingerprint": stable_hash(unit),
                            }
                            for unit in task["units"]
                        ],
                    }
                )
            index = {
                "schema": "fvn-agent-export/v1",
                "export_id": export_id,
                "project_id": manifest.project_id,
                "source_language": manifest.source_language,
                "target_language": manifest.target_language,
                "batches": batches,
            }
            # The workspace copy remains authoritative if the agent edits its task folder.
            atomic_write_json(
                self.workspace.runs / "agent-exports" / export_id / "manifest.json", index
            )
            atomic_write_json(output_root / "manifest.json", index)
            return paths

    def import_batch(
        self, task_path: Path, response_path: Path, *, model: str | None = None
    ) -> int:
        """Validate a complete response before committing; identical imports return zero."""
        with self.workspace:
            self._recover_import()
            task = _read_json(task_path)
            export_id = str(task.get("export_id", ""))
            try:
                valid_export_id = UUID(export_id).hex
            except ValueError as exc:
                raise DataIntegrityError("Invalid agent export ID") from exc
            index = _read_json(
                self.workspace.runs / "agent-exports" / valid_export_id / "manifest.json"
            )
            batch = next(
                (row for row in index["batches"] if row["batch_id"] == task.get("batch_id")),
                None,
            )
            if batch is None or stable_hash(task) != batch["task_fingerprint"]:
                raise DataIntegrityError("Agent task changed after export or is not registered")
            manifest = self._manifest()
            for key in ("project_id", "source_language", "target_language"):
                if task[key] != getattr(manifest, key):
                    raise DataIntegrityError(f"Workspace {key} changed after export")
            expected_ids = [row["unit_id"] for row in batch["inputs"]]
            task_ids = [row["unit_id"] for row in task["units"]]
            if len(set(task_ids)) != len(task_ids) or task_ids != expected_ids:
                raise DataIntegrityError("Agent task unit IDs do not match the exported batch")
            response = _read_json(response_path)
            translations = parse_translations(response, expected_ids)
            units = self.repository.load()
            by_id = {unit.unit_id: unit for unit in units}
            changed: list[TranslationUnit] = []
            revisions: list[dict[str, Any]] = []
            now = datetime.now(UTC)
            for original in task["units"]:
                unit = by_id.get(original["unit_id"])
                if unit is None or _visible_unit(unit) != original:
                    raise DataIntegrityError(
                        f"Source or translation input changed after export: {original['unit_id']}"
                    )
                candidate = unit.model_copy(deep=True)
                candidate.target_text = translations[unit.unit_id]
                candidate.translation.status = TranslationStatus.TRANSLATED
                errors = [
                    issue for issue in validate_unit(candidate) if issue.severity == Severity.ERROR
                ]
                for token in unit.protected_tokens:
                    count = unit.source_text.count(token)
                    if count and candidate.target_text.count(token) != count:
                        raise DataIntegrityError(
                            f"Protected token changed: {unit.unit_id}: {token}"
                        )
                if errors:
                    raise DataIntegrityError(
                        f"Invalid translation: {unit.unit_id}: {errors[0].message}"
                    )
                if unit.target_text == candidate.target_text and unit.translation.status in {
                    TranslationStatus.TRANSLATED,
                    TranslationStatus.REVIEWED,
                }:
                    continue
                candidate.translation.origin = "imported"
                candidate.translation.model = model
                candidate.translation.prompt_version = task["prompt_version"]
                candidate.translation.translated_at = now
                candidate.validation.status = ValidationStatus.UNCHECKED
                candidate.validation.issue_ids = []
                candidate.revision += 1
                candidate.updated_at = now
                changed.append(candidate)
                revisions.append(
                    {
                        "revision_id": uuid4().hex,
                        "unit_id": unit.unit_id,
                        "before": unit.target_text,
                        "after": candidate.target_text,
                        "origin": "imported",
                        "model": model,
                        "created_at": now.isoformat(),
                    }
                )
            archive = self.workspace.runs / "agent-imports" / valid_export_id / task["batch_id"]
            atomic_write_json(archive / "task.json", task)
            atomic_write_json(archive / "responses" / f"{stable_hash(response)[7:]}.json", response)
            if changed:
                commit = {
                    "status": "pending",
                    "units": [unit.model_dump(mode="json", by_alias=True) for unit in changed],
                    "revisions": revisions,
                }
                # A durable intent lets the next locked operation finish both atomic files
                # after a crash between revisions.jsonl and units.jsonl.
                atomic_write_json(self.commit_path, commit)
                self._finish_commit(commit, units)
            return len(changed)

    def _recover_import(self) -> None:
        if self.commit_path.exists():
            commit = _read_json(self.commit_path)
            if commit["status"] == "pending":
                self._finish_commit(commit, self.repository.load())

    def _finish_commit(self, commit: dict[str, Any], units: list[TranslationUnit]) -> None:
        by_id = {unit.unit_id: unit for unit in units}
        for row in commit["units"]:
            candidate = TranslationUnit.model_validate(row)
            current = by_id.get(candidate.unit_id)
            if (
                current is None
                or _visible_unit(current) != _visible_unit(candidate)
                or current.revision not in {candidate.revision - 1, candidate.revision}
            ):
                raise DataIntegrityError(f"Cannot recover changed import: {candidate.unit_id}")
            by_id[candidate.unit_id] = candidate
        revisions = self.revisions.read()
        existing = {row["revision_id"] for row in revisions}
        revisions.extend(row for row in commit["revisions"] if row["revision_id"] not in existing)
        atomic_write_jsonl(self.revisions.path, revisions)
        self.repository.save(list(by_id.values()))
        atomic_write_json(self.commit_path, {"status": "completed"})
