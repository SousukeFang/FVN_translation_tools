import json
from pathlib import Path
from zipfile import ZipFile

import pytest

from fvn_translator.adapters import AdapterConfig
from fvn_translator.adapters.base import ExtractionResult
from fvn_translator.adapters.demo import DemoAdapter
from fvn_translator.config import ProjectConfig
from fvn_translator.core.errors import ApplyConflictError
from fvn_translator.models import Issue, Severity, TranslationStatus
from fvn_translator.services import (
    ExtractionService,
    PatchService,
    ProjectService,
    ValidationService,
)
from fvn_translator.storage import UnitRepository, Workspace


def _project(tmp_path: Path) -> tuple[Path, Workspace, UnitRepository]:
    source = tmp_path / "source"
    source.mkdir()
    (source / "chapter.demo").write_text("[Fox] Hello.\n", encoding="utf-8")
    (source / "unchanged.demo").write_text("[Fox] Keep {i}this{/i}.\n", encoding="utf-8")
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(
            project_name="Example",
            source_root=source,
            source_language="en",
            target_language="ja",
            adapter_options={"source_version": "1.2"},
        ),
        adapter_version=DemoAdapter.adapter_version,
    )
    repository = UnitRepository(workspace.intermediate / "units.jsonl")
    ExtractionService(DemoAdapter(), repository).extract(source)
    units = repository.load()
    units[0].target_text = "こんにちは。"
    units[0].translation.status = TranslationStatus.TRANSLATED
    units[1].translation.status = TranslationStatus.SKIPPED
    repository.save(units)
    return source, workspace, repository


def test_patch_preserves_source_and_only_packages_changed_files(tmp_path: Path) -> None:
    source, workspace, repository = _project(tmp_path)
    before = {path.name: path.read_bytes() for path in source.iterdir()}
    extra = tmp_path / "font.ttf"
    extra.write_bytes(b"fixture font")
    archive_path = PatchService(workspace).build(
        DemoAdapter(),
        source,
        output_root=tmp_path / "output",
        extra_files={"game/font.ttf": extra},
        install_notes="游戏专属安装步骤。",
    )
    assert {path.name: path.read_bytes() for path in source.iterdir()} == before
    assert repository.load()[1].target_text == ""
    assert not workspace.lock_path.exists()
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == {
            "chapter.demo",
            "game/font.ttf",
            "README.md",
            "manifest.json",
        }
        assert archive.read("chapter.demo").decode("utf-8") == "[Fox] こんにちは。\n"
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["languages"] == {"source": "en", "target": "ja"}
        assert manifest["project"]["source_version"] == "1.2"
        assert manifest["coverage"]["translation_percent"] == 50.0
        assert manifest["coverage"]["skipped"] == 1
        assert manifest["validation"]["adapter"]["status"] == "passed"
        assert (
            manifest["files"][0]["source_fingerprint"] != manifest["files"][0]["target_fingerprint"]
        )
        assert manifest["files"][1]["source_fingerprint"] is None
    assert "游戏专属安装步骤。" in (archive_path.parent / "README.md").read_text(encoding="utf-8")
    assert (
        json.loads((archive_path.parent / "manifest.json").read_text(encoding="utf-8"))["files"]
        == manifest["files"]
    )


@pytest.mark.parametrize("status", ["pending", "failed", "in_progress"])
def test_incomplete_translation_is_rejected(tmp_path: Path, status: str) -> None:
    source, workspace, repository = _project(tmp_path)
    units = repository.load()
    units[0].translation.status = TranslationStatus(status)
    repository.save(units)
    with pytest.raises(ValueError, match="Translation is incomplete"):
        PatchService(workspace).build(DemoAdapter(), source, output_root=tmp_path / "output")
    assert not (tmp_path / "output").exists()
    assert not workspace.lock_path.exists()


def test_source_hash_conflict_is_rejected(tmp_path: Path) -> None:
    source, workspace, _ = _project(tmp_path)
    (source / "chapter.demo").write_text("[Fox] Changed.\n", encoding="utf-8")
    with pytest.raises(ApplyConflictError, match="Source changed after extraction"):
        PatchService(workspace).build(DemoAdapter(), source, output_root=tmp_path / "output")
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("relative", ["../outside", "C:/outside", "game\\outside", "chapter.demo"])
def test_extra_file_paths_and_collisions_are_rejected(tmp_path: Path, relative: str) -> None:
    source, workspace, _ = _project(tmp_path)
    extra = tmp_path / "extra"
    extra.write_bytes(b"extra")
    with pytest.raises(ValueError, match="relative path|collides"):
        PatchService(workspace).build(
            DemoAdapter(),
            source,
            output_root=tmp_path / "output",
            extra_files={relative: extra},
        )
    assert not (tmp_path / "output").exists()
    assert not (tmp_path / "outside").exists()


def test_extraction_error_is_rechecked_after_validation_overwrites_issues(tmp_path: Path) -> None:
    class ExtractionErrorAdapter(DemoAdapter):
        def extract(self, source_root, files, config) -> ExtractionResult:
            result = super().extract(source_root, files, config)
            result.issues.append(
                Issue(
                    issue_id="unparsed",
                    code="UNKNOWN_VISIBLE_TEXT",
                    severity=Severity.ERROR,
                    message="Visible text was not extracted",
                )
            )
            return result

    source, workspace, repository = _project(tmp_path)
    ValidationService(repository, workspace.intermediate / "issues.jsonl").validate()
    assert "UNKNOWN_VISIBLE_TEXT" not in (workspace.intermediate / "issues.jsonl").read_text()
    with pytest.raises(ValueError, match="Extraction failed"):
        PatchService(workspace).build(
            ExtractionErrorAdapter(), source, output_root=tmp_path / "output"
        )


def test_common_validation_and_missing_units_block_packaging(tmp_path: Path) -> None:
    source, workspace, repository = _project(tmp_path)
    units = repository.load()
    units[1].translation.status = TranslationStatus.TRANSLATED
    units[1].target_text = "内容"
    repository.save(units)
    with pytest.raises(ValueError, match="Common validation failed"):
        PatchService(workspace).build(DemoAdapter(), source, output_root=tmp_path / "output")
    repository.save(units[:1])
    with pytest.raises(ValueError, match="Extraction inventory changed"):
        PatchService(workspace).build(DemoAdapter(), source, output_root=tmp_path / "output")


def test_overlapping_source_and_staging_are_rejected(tmp_path: Path) -> None:
    source, _, _ = _project(tmp_path)
    workspace = Workspace(source / "workspace")
    with pytest.raises(ValueError, match="must not overlap"):
        PatchService(workspace).build(DemoAdapter(), source, output_root=tmp_path / "output")


def test_config_overrides_project_adapter_options(tmp_path: Path) -> None:
    source, workspace, _ = _project(tmp_path)
    archive = PatchService(workspace).build(
        DemoAdapter(),
        source,
        output_root=tmp_path / "output",
        config=AdapterConfig(options={"source_version": "1.3"}),
    )
    with ZipFile(archive) as zipped:
        assert json.loads(zipped.read("manifest.json"))["project"]["source_version"] == "1.3"
