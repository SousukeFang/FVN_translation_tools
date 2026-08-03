import asyncio
import shutil
from pathlib import Path

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.lint import RenPyLintRunner
from fvn_translator.config import ProjectConfig
from fvn_translator.llm import MockProvider
from fvn_translator.models import Severity
from fvn_translator.services import (
    ApplyService,
    BackupService,
    ExtractionService,
    ProjectService,
    RollbackService,
    SummaryService,
    TranslationPipelineService,
    TranslationService,
)
from fvn_translator.storage import CacheStore, RevisionStore, StateDatabase, UnitRepository


def test_remember_the_flowers_fixture_end_to_end_without_llm(tmp_path: Path) -> None:
    source = Path("tests/fixtures/remember_the_flowers/source")
    adapter = RenPyAdapter()
    config = AdapterConfig(options={"profile_id": "remember-the-flowers-ii"})
    first = adapter.extract(source, adapter.discover_files(source, config), config)
    for unit in first.units:
        unit.target_text = f"译文：{unit.source_text}"
    staging = tmp_path / "staging"
    applied = adapter.apply(source, staging, first.units, config)
    assert applied.written_files == ["game/options.rpy", "game/story/prologue.rpy"]
    assert not adapter.validate(staging, first.units, config).has_errors
    second = adapter.extract(staging, adapter.discover_files(staging, config), config)
    assert [unit.unit_id for unit in first.units] == [unit.unit_id for unit in second.units]
    assert [unit.target_text for unit in first.units] == [unit.source_text for unit in second.units]


def test_missing_sdk_is_reported_truthfully(tmp_path: Path) -> None:
    report = RenPyLintRunner().run(tmp_path, sdk_path=None, units=[])
    assert report.issues[0].code == "RENPY_LINT_NOT_RUN"
    assert report.issues[0].severity == Severity.WARNING


def test_public_pipeline_backup_apply_and_rollback(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(Path("tests/fixtures/remember_the_flowers/source"), source)
    originals = {path.relative_to(source): path.read_bytes() for path in source.rglob("*.rpy")}
    adapter = RenPyAdapter()
    project_config = ProjectConfig(
        project_name="rtf-test",
        source_root=source,
        adapter_id="renpy",
        adapter_options={"profile_id": "remember-the-flowers-ii"},
    )
    workspace = ProjectService().create(
        tmp_path / "workspace",
        project_config,
        adapter_version=adapter.adapter_version,
    )
    database = StateDatabase(workspace.state / "state.sqlite3")
    repository = UnitRepository(workspace.intermediate / "units.jsonl", database)
    config = AdapterConfig(options=project_config.adapter_options)
    assert ExtractionService(adapter, repository).extract(source, config) == 9
    translation = TranslationService(
        MockProvider(),
        repository,
        RevisionStore(workspace.intermediate / "revisions.jsonl"),
        CacheStore(database),
        workspace.runs,
    )
    asyncio.run(
        TranslationPipelineService(
            translation,
            SummaryService(MockProvider()),
            repository,
            workspace.intermediate / "scene_summaries.jsonl",
        ).run()
    )
    rollback = RollbackService(workspace.backups)
    backup_id = ApplyService(repository, BackupService(workspace.backups), rollback).apply(
        adapter, source, workspace.staging, config
    )
    assert "译文：" in (source / "game/story/prologue.rpy").read_text(encoding="utf-8")
    rollback.rollback(backup_id, source)
    assert {
        path.relative_to(source): path.read_bytes() for path in source.rglob("*.rpy")
    } == originals
    database.close()
