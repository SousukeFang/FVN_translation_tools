import json
import os
import re
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath, PureWindowsPath
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

from fvn_translator.adapters.base import AdapterConfig, FVNAdapter
from fvn_translator.config import load_project_config
from fvn_translator.core.atomic_io import atomic_write_json, atomic_write_text
from fvn_translator.core.errors import ApplyConflictError
from fvn_translator.core.hashing import file_hash
from fvn_translator.core.paths import ensure_within
from fvn_translator.models import Issue, Severity, TranslationStatus
from fvn_translator.storage import UnitRepository, Workspace
from fvn_translator.validators import validate_unit


class PatchService:
    """Build a distributable patch without applying it to the source game."""

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    def build(
        self,
        adapter: FVNAdapter,
        source_root: Path,
        *,
        output_root: Path,
        config: AdapterConfig | None = None,
        extra_files: dict[str, Path] | None = None,
        install_notes: str = "",
    ) -> Path:
        source_root = source_root.resolve()
        output_root = output_root.resolve()
        staging_root = self.workspace.staging.resolve()
        if _overlap(source_root, staging_root) or _overlap(source_root, output_root):
            raise ValueError("Source, staging and output directories must not overlap")
        with self.workspace:
            return self._build(
                adapter,
                source_root,
                output_root,
                config,
                extra_files or {},
                install_notes,
            )

    def _build(
        self,
        adapter: FVNAdapter,
        source_root: Path,
        output_root: Path,
        config: AdapterConfig | None,
        extra_files: dict[str, Path],
        install_notes: str,
    ) -> Path:
        manifest_path = self.workspace.intermediate / "manifest.json"
        metadata = json.loads(manifest_path.read_text(encoding="utf-8"))
        options = {}
        project_path = self.workspace.root / "project.toml"
        if project_path.exists():
            project = load_project_config(project_path)
            metadata.update(
                project_name=project.project_name,
                source_language=project.source_language,
                target_language=project.target_language,
            )
            options.update(project.adapter_options)
        if config:
            options.update(config.options)
        options.setdefault("target_language", metadata["target_language"])
        adapter_config = AdapterConfig(options=options)
        units = UnitRepository(self.workspace.intermediate / "units.jsonl").load()
        if not units:
            raise ValueError("No extracted units to package")
        completed = {
            TranslationStatus.TRANSLATED,
            TranslationStatus.REVIEWED,
            TranslationStatus.SKIPPED,
        }
        unfinished = [unit.unit_id for unit in units if unit.translation.status not in completed]
        if unfinished:
            raise ValueError(f"Translation is incomplete: {len(unfinished)} unfinished units")

        expected: dict[str, str] = {}
        for unit in units:
            relative = _safe_relative(str(unit.origin["path"]))
            fingerprint = str(unit.origin["file_fingerprint"])
            if relative in expected and expected[relative] != fingerprint:
                raise ApplyConflictError(f"Conflicting source hashes: {relative}")
            expected[relative] = fingerprint
        for relative, fingerprint in expected.items():
            path = ensure_within(source_root, source_root / relative)
            if not path.is_file() or file_hash(path) != fingerprint:
                raise ApplyConflictError(f"Source changed after extraction: {relative}")

        # Re-extraction retains this gate even if validation replaced issues.jsonl.
        extraction = adapter.extract(
            source_root, adapter.discover_files(source_root, adapter_config), adapter_config
        )
        _reject_errors("Extraction", extraction.issues)
        if {unit.unit_id: unit.source_fingerprint for unit in extraction.units} != {
            unit.unit_id: unit.source_fingerprint for unit in units
        }:
            raise ValueError("Extraction inventory changed; extract the project again")

        rendered_units = [unit.model_copy(deep=True) for unit in units]
        for unit in rendered_units:
            if unit.translation.status == TranslationStatus.SKIPPED:
                unit.target_text = unit.source_text
        common_issues = [issue for unit in rendered_units for issue in validate_unit(unit)]
        _reject_errors("Common validation", common_issues)

        # A new staging directory avoids including files from earlier patch builds.
        staging = self.workspace.staging / f"patch-{uuid4().hex}"
        result = adapter.apply(source_root, staging, rendered_units, adapter_config)
        files: dict[str, tuple[Path, str]] = {}
        for value in result.written_files:
            relative = _safe_relative(value)
            path = ensure_within(staging, staging / relative)
            original = ensure_within(source_root, source_root / relative)
            if not original.is_file() or file_hash(path) != file_hash(original):
                files[relative] = (path, "translation")
        for value, extra in extra_files.items():
            relative = _safe_relative(value)
            if relative in files or relative in {"README.md", "manifest.json"}:
                raise ValueError(f"Extra file collides with a patch file: {relative}")
            destination = ensure_within(staging, staging / relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(extra, destination)
            files[relative] = (destination, "extra")
        report = adapter.validate(staging, rendered_units, adapter_config)
        _reject_errors("Adapter validation", report.issues)

        counts = {
            status.value: sum(unit.translation.status == status for unit in units)
            for status in sorted(completed)
        }
        file_list = []
        for relative, (path, kind) in sorted(files.items()):
            original = ensure_within(source_root, source_root / relative)
            file_list.append(
                {
                    "path": relative,
                    "kind": kind,
                    "source_fingerprint": file_hash(original) if original.is_file() else None,
                    "target_fingerprint": file_hash(path),
                    "size": path.stat().st_size,
                }
            )
        patch_manifest = {
            "schema": "fvn-translation-patch/v1",
            "created_at": datetime.now(UTC).isoformat(),
            "project": {
                "id": metadata["project_id"],
                "name": metadata["project_name"],
                "source_version": options.get("source_version"),
            },
            "languages": {
                "source": metadata["source_language"],
                "target": metadata["target_language"],
            },
            "adapter": {"id": adapter.adapter_id, "version": adapter.adapter_version},
            "schema_versions": metadata.get("schema_versions", {}),
            "coverage": {
                "total": len(units),
                **counts,
                "completion_percent": 100.0,
                "translation_percent": round(
                    100 * (len(units) - counts["skipped"]) / len(units), 2
                ),
            },
            "validation": {
                "extraction": _validation_record(extraction.issues),
                "common": _validation_record(common_issues),
                "adapter": _validation_record(report.issues),
            },
            "files": file_list,
        }
        source_version = options.get("source_version") or "以 manifest.json 中的源文件哈希为准"
        readme = (
            f"# {metadata['project_name']} 翻译补丁\n\n"
            f"语言：{metadata['source_language']} → {metadata['target_language']}\n\n"
            f"适用版本：{source_version}\n\n"
            f"完成 {len(units)} 个文本单元；译文 {len(units) - counts['skipped']} 个，"
            f"明确保留原文 {counts['skipped']} 个。\n\n"
            "ZIP 只包含有变化的脚本、显式添加的补充文件，以及本说明和 manifest.json。"
            "文件清单、源文件/补丁文件 SHA-256 和实际校验结果见 manifest.json。\n\n"
            "## 安装\n\n"
            "1. 关闭游戏，确认游戏版本与补丁对应。\n"
            "2. 备份游戏目录，至少备份清单中 source_fingerprint 非空的原文件。\n"
            "3. 将 ZIP 解压到临时目录，把清单中的文件按原目录结构复制至游戏根目录，"
            "同名文件选择覆盖。\n"
            "4. 启动游戏检查文本显示。\n\n"
            "## 回退\n\n"
            "关闭游戏，用备份恢复被覆盖的文件；移除清单中 source_fingerprint 为 null 的"
            "新增文件。也可以直接恢复整个游戏目录备份。\n"
        )
        if install_notes:
            readme += f"\n## 本游戏补充说明\n\n{install_notes.strip()}\n"
        output_root.mkdir(parents=True, exist_ok=True)
        readme_path = output_root / "README.md"
        patch_manifest_path = output_root / "manifest.json"
        atomic_write_text(readme_path, readme)
        atomic_write_json(patch_manifest_path, patch_manifest)
        name = re.sub(r"[^\w.-]+", "-", metadata["project_name"]).strip("-.") or "translation"
        language = re.sub(r"[^\w.-]+", "-", metadata["target_language"])
        archive_path = output_root / f"{name}-{language}-patch.zip"
        descriptor, temporary = tempfile.mkstemp(suffix=".zip.tmp", dir=output_root)
        os.close(descriptor)
        try:
            with ZipFile(temporary, "w", compression=ZIP_DEFLATED) as archive:
                for relative, (path, _) in sorted(files.items()):
                    archive.write(path, relative)
                archive.write(readme_path, "README.md")
                archive.write(patch_manifest_path, "manifest.json")
            os.replace(temporary, archive_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return archive_path


def _safe_relative(value: str) -> str:
    path = PurePosixPath(value)
    if (
        not value
        or "\\" in value
        or path.is_absolute()
        or PureWindowsPath(value).drive
        or any(part in {"", ".", ".."} for part in value.split("/"))
    ):
        raise ValueError(f"Expected a safe relative path: {value}")
    return path.as_posix()


def _overlap(first: Path, second: Path) -> bool:
    return first == second or first in second.parents or second in first.parents


def _reject_errors(stage: str, issues: list[Issue]) -> None:
    if any(issue.severity == Severity.ERROR for issue in issues):
        raise ValueError(f"{stage} failed; no patch was produced")


def _validation_record(issues: list[Issue]) -> dict[str, object]:
    return {
        "status": "warning" if issues else "passed",
        "error_count": sum(issue.severity == Severity.ERROR for issue in issues),
        "warning_count": sum(issue.severity == Severity.WARNING for issue in issues),
        "issues": [issue.model_dump(mode="json", by_alias=True) for issue in issues],
    }
