import asyncio
import json
from pathlib import Path

import pytest

from fvn_translator.config import ProjectConfig
from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.core.errors import (
    DataIntegrityError,
    ResponseFormatError,
    WorkspaceLockedError,
)
from fvn_translator.core.hashing import bytes_hash
from fvn_translator.llm import MockProvider
from fvn_translator.llm.request_builder import translation_request
from fvn_translator.models import (
    Character,
    GlossaryEntry,
    TranslationStatus,
    TranslationUnit,
    UnitType,
)
from fvn_translator.services import ProjectService, SummaryService, TranslationPipelineService
from fvn_translator.services.agent_translation_service import AgentTranslationService
from fvn_translator.services.translation_service import TranslationService
from fvn_translator.storage import (
    CacheStore,
    MetadataRepository,
    RevisionStore,
    StateDatabase,
    UnitRepository,
    Workspace,
)


@pytest.fixture
def workspace(tmp_path):
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(
            project_name="offline agent",
            source_root=tmp_path / "source",
            source_language="ja",
            target_language="fr",
        ),
        adapter_version="1",
    )
    texts = ["静かな朝。", "{i}こんにちは{/i} [name]。", "約束だよ。", "また明日。"]
    units = [
        TranslationUnit(
            unit_id=f"unit-{index}",
            sequence=index,
            segment_id="story",
            scene_id=f"scene-{index // 2}",
            type=UnitType.DIALOGUE,
            speaker="Fox",
            source_text=text,
            source_fingerprint=bytes_hash(text.encode()),
            protected_tokens=["{i}", "{/i}", "[name]"] if index == 1 else [],
            context={"semantic_role": "say"},
            adapter_data={"private": "adapter-secret"},
        )
        for index, text in enumerate(texts)
    ]
    UnitRepository(workspace.intermediate / "units.jsonl").save(units)
    MetadataRepository(workspace.intermediate / "characters.json", Character).save(
        [Character(character_id="fox", names=["Fox"], speech_style="gentle")]
    )
    MetadataRepository(workspace.intermediate / "glossary.json", GlossaryEntry).save(
        [GlossaryEntry(term_id="promise", source_term="約束", target_term="promesse")]
    )
    return workspace


def write_response(task_path: Path, path: Path, *, targets=None):
    task = json.loads(task_path.read_text(encoding="utf-8"))
    response = {
        "translations": [
            {
                "unit_id": row["unit_id"],
                "target_text": (targets or {}).get(row["unit_id"], row["source_text"]),
            }
            for row in task["units"]
        ]
    }
    atomic_write_json(path, response)
    return response


def test_export_budget_context_resume_and_private_boundary(workspace, tmp_path):
    service = AgentTranslationService(workspace)
    units = service.repository.load()
    units[0].translation.status = TranslationStatus.REVIEWED
    units[3].translation.status = TranslationStatus.FAILED
    service.repository.save(units)
    paths = service.export_batches(tmp_path / "tasks", max_chars=3600, context_units=1)
    task_units = []
    for path in paths:
        payload = path.read_text(encoding="utf-8")
        task = json.loads(payload)
        assert "adapter_data" not in payload and "adapter-secret" not in payload
        assert task["source_language"] == "ja"
        assert task["target_language"] == "fr"
        assert len(task["context_before"]) <= 1
        assert len(task["context_after"]) <= 1
        assert len(payload) <= 3600 or len(task["units"]) == 1
        assert task["characters"][0]["speech_style"] == "gentle"
        task_units.extend(task["units"])
    assert [row["unit_id"] for row in task_units] == ["unit-1", "unit-2", "unit-3"]
    assert {row["scene_id"] for row in task_units} == {"scene-0", "scene-1"}
    index = json.loads((tmp_path / "tasks" / "manifest.json").read_text())
    assert len(index["batches"]) == len(paths)
    assert index["batches"][0]["inputs"][0]["source_fingerprint"]
    assert index["batches"][0]["inputs"][0]["input_fingerprint"]


def test_import_atomic_batch_revision_and_idempotence(workspace, tmp_path, monkeypatch):
    service = AgentTranslationService(workspace)
    task = service.export_batches(tmp_path / "tasks", max_chars=20000)[0]
    response = tmp_path / "response.json"
    write_response(task, response, targets={"unit-0": "Un matin calme."})
    saves = []
    real_save = service.repository.save

    def save(units):
        saves.append(len(units))
        real_save(units)

    def append(**kwargs):
        pytest.fail("Imports must save revision rows together rather than append per unit")

    monkeypatch.setattr(service.repository, "save", save)
    monkeypatch.setattr(service.revisions, "append", append)
    assert service.import_batch(task, response, model="agent-model") == 4
    assert saves == [4]
    units = service.repository.load()
    assert units[0].target_text == "Un matin calme."
    assert all(unit.translation.origin == "imported" for unit in units)
    assert all(unit.translation.model == "agent-model" for unit in units)
    assert all(unit.revision == 1 for unit in units)
    assert len(service.revisions.read()) == 4
    before_units = service.repository.path.read_bytes()
    before_revisions = service.revisions.path.read_bytes()
    assert service.import_batch(task, response, model="agent-model") == 0
    assert service.repository.path.read_bytes() == before_units
    assert service.revisions.path.read_bytes() == before_revisions
    assert service.export_batches(tmp_path / "resumed") == []
    assert list((workspace.runs / "agent-imports").rglob("responses/*.json"))
    assert not workspace.lock_path.exists()


@pytest.mark.parametrize("failure", ["missing", "extra", "duplicate", "empty", "token"])
def test_bad_response_does_not_partially_commit(workspace, tmp_path, failure):
    service = AgentTranslationService(workspace)
    task = service.export_batches(tmp_path / "tasks", max_chars=20000)[0]
    response_path = tmp_path / "response.json"
    response = write_response(task, response_path, targets={"unit-0": "Un matin calme."})
    rows = response["translations"]
    if failure == "missing":
        rows.pop()
    elif failure == "extra":
        rows.append({"unit_id": "unknown", "target_text": "Bonjour."})
    elif failure == "duplicate":
        rows.append(rows[0])
    elif failure == "empty":
        rows[-1]["target_text"] = " "
    else:
        rows[1]["target_text"] = "Bonjour."
    atomic_write_json(response_path, response)
    before = service.repository.path.read_bytes()
    with pytest.raises((DataIntegrityError, ResponseFormatError)):
        service.import_batch(task, response_path)
    assert service.repository.path.read_bytes() == before
    assert service.revisions.read() == []
    assert not (workspace.runs / "agent-imports").exists()
    assert not workspace.lock_path.exists()


@pytest.mark.parametrize("change", ["task", "source", "fingerprint", "language"])
def test_changed_translation_input_is_rejected(workspace, tmp_path, change):
    service = AgentTranslationService(workspace)
    task = service.export_batches(tmp_path / "tasks", max_chars=20000)[0]
    response = tmp_path / "response.json"
    write_response(task, response)
    if change == "task":
        payload = json.loads(task.read_text())
        payload["target_language"] = "de"
        atomic_write_json(task, payload)
        # Editing the public manifest does not replace the workspace's registration.
        index = json.loads((task.parent.parent / "manifest.json").read_text())
        index["target_language"] = "de"
        atomic_write_json(task.parent.parent / "manifest.json", index)
    elif change == "language":
        manifest_path = workspace.intermediate / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["target_language"] = "de"
        atomic_write_json(manifest_path, manifest)
    else:
        units = service.repository.load()
        if change == "source":
            units[0].source_text = "changed without updating its fingerprint"
        else:
            units[0].source_fingerprint = "changed"
        service.repository.save(units)
    with pytest.raises(DataIntegrityError):
        service.import_batch(task, response)
    assert service.revisions.read() == []


def test_workspace_lock_is_respected(workspace, tmp_path):
    service = AgentTranslationService(workspace)
    task = service.export_batches(tmp_path / "tasks", max_chars=20000)[0]
    response = tmp_path / "response.json"
    write_response(task, response)
    other = Workspace(workspace.root)
    with other:
        with pytest.raises(WorkspaceLockedError):
            service.export_batches(tmp_path / "blocked")
        with pytest.raises(WorkspaceLockedError):
            service.import_batch(task, response)
    assert service.import_batch(task, response) == 4


def test_interrupted_import_recovers_without_duplicate_revisions(workspace, tmp_path, monkeypatch):
    service = AgentTranslationService(workspace)
    task = service.export_batches(tmp_path / "tasks", max_chars=20000)[0]
    response = tmp_path / "response.json"
    write_response(task, response)
    real_save = service.repository.save

    def fail_save(units):
        raise OSError("interrupted before units atomic replacement")

    monkeypatch.setattr(service.repository, "save", fail_save)
    with pytest.raises(OSError):
        service.import_batch(task, response, model="agent")
    assert len(service.revisions.read()) == 4
    assert all(unit.revision == 0 for unit in service.repository.load())
    monkeypatch.setattr(service.repository, "save", real_save)
    assert service.import_batch(task, response, model="agent") == 0
    assert len(service.revisions.read()) == 4
    assert all(unit.revision == 1 for unit in service.repository.load())
    assert all(unit.translation.model == "agent" for unit in service.repository.load())


def test_language_defaults_and_pipeline_propagation(workspace, tmp_path):
    class RecordingProvider(MockProvider):
        def __init__(self):
            self.requests = []

        async def complete(self, request):
            self.requests.append(request)
            return await super().complete(request)

    request = translation_request(
        run_id="test", batch_id="test", units=[], characters=[], glossary=[], previous_summary=""
    )
    assert request.payload["source_language"] == "en"
    assert request.payload["target_language"] == "zh-CN"
    database = StateDatabase(workspace.state / "test.sqlite3")
    provider = RecordingProvider()
    repository = UnitRepository(workspace.intermediate / "units.jsonl")
    pipeline = TranslationPipelineService(
        TranslationService(
            provider,
            repository,
            RevisionStore(workspace.intermediate / "revisions.jsonl"),
            CacheStore(database),
            workspace.runs,
        ),
        SummaryService(provider),
        repository,
        workspace.intermediate / "scene_summaries.jsonl",
    )
    asyncio.run(pipeline.run(source_language="ja", target_language="fr"))
    requests = [request for request in provider.requests if request.task == "translation"]
    assert len(requests) == 2
    assert all(request.payload["source_language"] == "ja" for request in requests)
    assert all(request.payload["target_language"] == "fr" for request in requests)
    assert all("from ja into fr" in request.system_prompt for request in requests)
    assert all("adapter_data" not in json.dumps(request.payload) for request in requests)
    database.close()
