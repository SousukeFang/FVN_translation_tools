import json
from pathlib import Path

import pytest

from fvn_translator.cli import build_parser, run_agent
from fvn_translator.config import ProjectConfig
from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.core.errors import DataIntegrityError
from fvn_translator.core.hashing import bytes_hash
from fvn_translator.models import TranslationStatus, TranslationUnit, UnitType
from fvn_translator.services import ProjectService
from fvn_translator.services.agent_translation_service import AgentTranslationService
from fvn_translator.storage import UnitRepository

SELECTED_PENDING_IDS = {"unit-1", "unit-5", "unit-7"}
SELECTED_IDS = SELECTED_PENDING_IDS | {"unit-3"}
OUTSIDE_IDS = {f"unit-{index}" for index in (0, 2, 4, 6, 8)}


@pytest.fixture
def selection_workspace(tmp_path):
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(
            project_name="offline selected agent units",
            source_root=tmp_path / "synthetic-source",
            source_language="en",
            target_language="fr",
        ),
        adapter_version="1",
    )
    units = []
    for index in range(9):
        unit_id = f"unit-{index}"
        marker = "ALLOWED" if unit_id in SELECTED_IDS else "OUTSIDE_SELECTION_SENTINEL"
        text = f"{marker}_{index}. " + "A synthetic line for selection testing. " * 5
        unit = TranslationUnit(
            unit_id=unit_id,
            sequence=index,
            segment_id="synthetic-story",
            scene_id=f"synthetic-scene-{index // 3}",
            type=UnitType.DIALOGUE,
            source_text=text,
            source_fingerprint=bytes_hash(text.encode()),
            context={"semantic_role": "say"},
            adapter_data={"private": "PRIVATE_ADAPTER_SENTINEL"},
        )
        if index == 3:
            unit.translation.status = TranslationStatus.REVIEWED
            unit.target_text = "Previously reviewed selected context."
        elif index == 5:
            unit.translation.status = TranslationStatus.FAILED
        units.append(unit)
    UnitRepository(workspace.intermediate / "units.jsonl").save(units)
    return workspace


def repository_lines(path: Path) -> dict[str, bytes]:
    return {
        json.loads(line)["unit_id"]: line for line in path.read_bytes().splitlines(keepends=True)
    }


def workspace_files(root: Path) -> dict[Path, bytes]:
    return {path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def export_arguments(workspace, output: Path, whitelist: Path | None = None):
    arguments = [
        "agent",
        "export",
        "--workspace",
        str(workspace.root),
        "--output",
        str(output),
        "--max-chars",
        "2500",
        "--context-units",
        "3",
    ]
    if whitelist is not None:
        arguments.extend(["--unit-ids-file", str(whitelist)])
    return build_parser().parse_args(arguments)


def test_selected_sparse_export_context_and_normal_cli_import(selection_workspace, tmp_path):
    workspace = selection_workspace
    service = AgentTranslationService(workspace)
    before_lines = repository_lines(service.repository.path)
    paths = service.export_batches(
        tmp_path / "tasks", max_chars=2500, context_units=3, unit_ids=SELECTED_IDS
    )
    assert len(paths) >= 2
    exported_ids = []
    reviewed_context = []
    responses = []
    for index, task_path in enumerate(paths):
        payload = task_path.read_text(encoding="utf-8")
        task = json.loads(payload)
        assert "OUTSIDE_SELECTION_SENTINEL" not in payload
        assert "PRIVATE_ADAPTER_SENTINEL" not in payload
        assert "adapter_data" not in payload
        assert len(payload) <= 2500 or len(task["units"]) == 1
        context = task["context_before"] + task["context_after"]
        assert len(task["context_before"]) <= 3
        assert len(task["context_after"]) <= 3
        assert {row["unit_id"] for row in context} <= SELECTED_IDS
        assert {row["unit_id"] for row in task["units"]} <= SELECTED_PENDING_IDS
        reviewed_context.extend(row for row in context if row["unit_id"] == "unit-3")
        exported_ids.extend(row["unit_id"] for row in task["units"])
        response_path = tmp_path / f"response-{index}.json"
        atomic_write_json(
            response_path,
            {
                "translations": [
                    {"unit_id": row["unit_id"], "target_text": f"Translated {row['unit_id']}."}
                    for row in task["units"]
                ]
            },
        )
        args = build_parser().parse_args(
            [
                "agent",
                "import",
                "--workspace",
                str(workspace.root),
                "--task",
                str(task_path),
                "--response",
                str(response_path),
                "--model",
                "offline-selected-agent",
            ]
        )
        assert run_agent(args) == {"imported": len(task["units"])}
        responses.append(args)

    assert exported_ids == ["unit-1", "unit-5", "unit-7"]
    assert reviewed_context
    assert all(
        row["target_text"] == "Previously reviewed selected context." for row in reviewed_context
    )
    manifest = json.loads((tmp_path / "tasks" / "manifest.json").read_text(encoding="utf-8"))
    assert [
        row["unit_id"] for batch in manifest["batches"] for row in batch["inputs"]
    ] == exported_ids
    after_lines = repository_lines(service.repository.path)
    for unit_id in OUTSIDE_IDS | {"unit-3"}:
        assert after_lines[unit_id] == before_lines[unit_id]
    for unit in service.repository.load():
        if unit.unit_id in SELECTED_PENDING_IDS:
            assert unit.translation.status == TranslationStatus.TRANSLATED
            assert unit.target_text == f"Translated {unit.unit_id}."
            assert unit.translation.origin == "imported"
            assert unit.translation.model == "offline-selected-agent"
            assert unit.revision == 1
        elif unit.unit_id in OUTSIDE_IDS:
            assert unit.translation.status == TranslationStatus.PENDING
            assert unit.target_text == ""
            assert unit.revision == 0
    revisions = service.revisions.read()
    assert len(revisions) == len(SELECTED_PENDING_IDS)
    assert {revision["unit_id"] for revision in revisions} == SELECTED_PENDING_IDS
    units_bytes = service.repository.path.read_bytes()
    revisions_bytes = service.revisions.path.read_bytes()
    for args in responses:
        assert run_agent(args) == {"imported": 0}
    assert service.repository.path.read_bytes() == units_bytes
    assert service.revisions.path.read_bytes() == revisions_bytes
    assert service.export_batches(tmp_path / "resumed", unit_ids=SELECTED_IDS) == []
    assert not workspace.lock_path.exists()


def test_default_export_keeps_all_pending_and_failed_units(selection_workspace, tmp_path):
    service = AgentTranslationService(selection_workspace)
    paths = service.export_batches(tmp_path / "default-tasks", max_chars=1, context_units=3)
    tasks = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert [row["unit_id"] for task in tasks for row in task["units"]] == [
        f"unit-{index}" for index in range(9) if index != 3
    ]
    assert any(
        row["unit_id"] == "unit-3"
        for task in tasks
        for row in task["context_before"] + task["context_after"]
    )
    assert any(
        "OUTSIDE_SELECTION_SENTINEL" in row["source_text"]
        for task in tasks
        for row in task["context_before"] + task["context_after"]
    )


def test_unknown_service_selection_rejected_before_writes(selection_workspace, tmp_path):
    workspace = selection_workspace
    before = workspace_files(workspace.root)
    output = tmp_path / "rejected-export"
    with pytest.raises((DataIntegrityError, ValueError), match="unknown-unit"):
        AgentTranslationService(workspace).export_batches(
            output, unit_ids={"unit-1", "unknown-unit"}
        )
    assert not output.exists()
    assert workspace_files(workspace.root) == before
    assert not workspace.lock_path.exists()


@pytest.mark.parametrize("ids", [["unit-5", "unit-3"], []])
def test_cli_export_uses_json_whitelist(selection_workspace, tmp_path, ids):
    whitelist = tmp_path / "unit-ids.json"
    atomic_write_json(whitelist, ids)
    output = tmp_path / "cli-tasks"
    args = export_arguments(selection_workspace, output, whitelist)
    result = run_agent(args)
    paths = [Path(path) for path in result["tasks"]]
    assert result["batches"] == len(paths)
    tasks = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    assert [row["unit_id"] for task in tasks for row in task["units"]] == (
        ["unit-5"] if ids else []
    )
    for path in paths:
        assert "OUTSIDE_SELECTION_SENTINEL" not in path.read_text(encoding="utf-8")
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest["batches"]) == len(paths)
    assert all(
        unit.translation.status == TranslationStatus.PENDING
        for unit in AgentTranslationService(selection_workspace).repository.load()
        if unit.unit_id in OUTSIDE_IDS
    )


@pytest.mark.parametrize(
    "value",
    [
        {"unit_ids": ["unit-1"]},
        42,
        "unit-1",
        None,
        ["unit-1", 7],
        [True],
        [["unit-1"]],
        [""],
        [" "],
        ["\t\n"],
        ["unit-1", "unit-1"],
    ],
    ids=[
        "object",
        "number",
        "string",
        "null",
        "nonstring-entry",
        "boolean-entry",
        "nested-array-entry",
        "empty-id",
        "space-id",
        "whitespace-id",
        "duplicate-id",
    ],
)
def test_cli_rejects_malformed_whitelists_before_writes(selection_workspace, tmp_path, value):
    workspace = selection_workspace
    whitelist = tmp_path / "malformed-unit-ids.json"
    atomic_write_json(whitelist, value)
    output = tmp_path / "rejected-cli-export"
    before = workspace_files(workspace.root)
    args = export_arguments(workspace, output, whitelist)
    with pytest.raises((DataIntegrityError, ValueError)):
        run_agent(args)
    assert not output.exists()
    assert workspace_files(workspace.root) == before
    assert not workspace.lock_path.exists()


def test_cli_parser_accepts_unit_ids_file_and_defaults_to_no_selection(
    selection_workspace, tmp_path
):
    output = tmp_path / "tasks"
    whitelist = tmp_path / "unit-ids.json"
    args = export_arguments(selection_workspace, output, whitelist)
    assert args.command == "agent"
    assert args.action == "export"
    assert args.unit_ids_file == whitelist
    assert args.max_chars == 2500
    assert args.context_units == 3
    assert export_arguments(selection_workspace, output).unit_ids_file is None
