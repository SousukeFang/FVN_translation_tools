import asyncio
import json

from fvn_translator.adapters.demo import DemoAdapter
from fvn_translator.config import ProjectConfig
from fvn_translator.llm import MockProvider
from fvn_translator.services import (
    ApplyService,
    BackupService,
    EditingService,
    ExtractionService,
    ProjectService,
    RollbackService,
    SummaryService,
    TranslationPipelineService,
    TranslationService,
    ValidationService,
)
from fvn_translator.storage import CacheStore, RevisionStore, StateDatabase, UnitRepository


def test_complete_demo_pipeline(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    original = "[NARRATION] Quiet.\n[Fox] Hello {i}friend{/i}.\n"
    (source / "chapter.demo").write_text(original, encoding="utf-8")
    adapter = DemoAdapter()
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(project_name="test", source_root=source),
        adapter_version=adapter.adapter_version,
    )
    database = StateDatabase(workspace.state / "state.sqlite3")
    repository = UnitRepository(workspace.intermediate / "units.jsonl", database)
    assert ExtractionService(adapter, repository).extract(source) == 2
    translation = TranslationService(
        MockProvider(),
        repository,
        RevisionStore(workspace.intermediate / "revisions.jsonl"),
        CacheStore(database),
        workspace.runs,
    )
    summaries = asyncio.run(
        TranslationPipelineService(
            translation,
            SummaryService(MockProvider()),
            repository,
            workspace.intermediate / "scene_summaries.jsonl",
        ).run()
    )
    assert len(summaries) == 1
    units = repository.load()
    assert all(unit.target_text.startswith("译文：") for unit in units)
    EditingService(repository, RevisionStore(workspace.intermediate / "revisions.jsonl")).edit(
        units[0].unit_id, "安静。"
    )
    assert not ValidationService(repository, workspace.intermediate / "issues.jsonl").validate()
    rollback = RollbackService(workspace.backups)
    backup_id = ApplyService(repository, BackupService(workspace.backups), rollback).apply(
        adapter, source, workspace.staging
    )
    journal = json.loads((workspace.state / "apply_journal.json").read_text(encoding="utf-8"))
    assert journal["status"] == "completed"
    assert "安静。" in (source / "chapter.demo").read_text(encoding="utf-8")
    rollback.rollback(backup_id, source)
    assert (source / "chapter.demo").read_text(encoding="utf-8") == original
    assert len(RevisionStore(workspace.intermediate / "revisions.jsonl").read()) == 3
    database.close()
