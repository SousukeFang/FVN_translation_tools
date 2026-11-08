"""Build a target-only byte delta from an explicit, revisioned Ren'Py FTIF whitelist.

This deterministic skill helper is separate from the full-project package command.
It never applies changes to the source game and never distributes source scripts.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import stat
import tempfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath, PureWindowsPath

from fvn_translator.adapters.base import AdapterConfig
from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.adapters.renpy.writer import encode_string_content
from fvn_translator.config import load_project_config
from fvn_translator.core.atomic_io import atomic_write_bytes, atomic_write_json, atomic_write_text
from fvn_translator.core.hashing import bytes_hash, file_hash
from fvn_translator.core.paths import ensure_within
from fvn_translator.models import Severity, TranslationStatus, TranslationUnit
from fvn_translator.storage import RevisionStore, UnitRepository, Workspace
from fvn_translator.validators import validate_unit

TEMPLATES = Path(__file__).with_name("renpy_delta_templates")
_RESERVED = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.IGNORECASE)


def safe_relative_path(value: str, *, game: bool = False) -> str:
    """Use the intersection of safe Windows and POSIX relative file paths."""
    parts = value.split("/")
    if (
        (game and not value.startswith("game/"))
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).drive
        or any(character in value for character in '\\<>:"|?*')
        or any(ord(character) < 32 for character in value)
        or any(part in {"", ".", ".."} or part.endswith((".", " ")) for part in parts)
        or any(_RESERVED.match(part) for part in parts)
    ):
        raise ValueError(f"Expected a safe relative path: {value}")
    return value


def safe_game_path(value: str) -> str:
    return safe_relative_path(value, game=True)


def regular_guard_file(source_root: Path, relative: str) -> Path:
    """Runtime version inputs must be ordinary files, never linked paths."""
    candidate = source_root / safe_relative_path(relative)
    for path in [candidate, *candidate.parents]:
        if path == source_root:
            break
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError("Runtime guard cannot use linked files or directories")
    path = ensure_within(source_root, candidate)
    if not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("Runtime guard must reference an ordinary file")
    return path


def _separate(first: Path, second: Path) -> bool:
    return first != second and first not in second.parents and second not in first.parents


def _identity(unit: TranslationUnit) -> tuple[object, ...]:
    # A unit ID/fingerprint alone cannot protect manually altered adapter offsets.
    return (
        unit.source_fingerprint,
        unit.source_text,
        unit.origin,
        unit.adapter_data,
        unit.type,
        unit.speaker,
        unit.protected_tokens,
        unit.constraints,
        unit.context,
    )


def _read_ids(path: Path) -> list[str]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item for item in value)
        or len(value) != len(set(value))
    ):
        raise ValueError("Whitelist must be a nonempty JSON array of unique unit IDs")
    return value


def build_delta(
    workspace: Workspace,
    *,
    source_root: Path,
    unit_ids: list[str],
    output_root: Path,
    patch_id: str,
    extra_files: dict[str, Path] | None = None,
    runtime_guard_paths: list[str] | None = None,
    install_notes: str = "",
) -> Path:
    """Create a fresh installer directory; return its target-only patch.json path."""
    source_root, output_root = source_root.resolve(), output_root.resolve()
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", patch_id)
        or patch_id.endswith(".")
        or _RESERVED.match(patch_id)
    ):
        raise ValueError("patch_id must contain 1-80 ASCII letters, digits, dots, _ or -")
    if not unit_ids or len(set(unit_ids)) != len(unit_ids):
        raise ValueError("Whitelist must contain nonempty, unique unit IDs")
    if not all(isinstance(value, str) and value for value in unit_ids):
        raise ValueError("Whitelist must contain nonempty, unique unit IDs")
    if (
        not _separate(source_root, output_root)
        or not _separate(workspace.root, output_root)
        or not _separate(workspace.root, source_root)
    ):
        raise ValueError("Source, workspace and output directories must not overlap")
    if output_root.exists():
        raise ValueError("Output directory already exists; choose a fresh build directory")
    with workspace:
        return _build_locked(
            workspace,
            source_root,
            unit_ids,
            output_root,
            patch_id,
            extra_files or {},
            runtime_guard_paths or [],
            install_notes,
        )


def _build_locked(
    workspace: Workspace,
    source_root: Path,
    unit_ids: list[str],
    output_root: Path,
    patch_id: str,
    extra_files: dict[str, Path],
    runtime_guard_paths: list[str],
    install_notes: str,
) -> Path:
    metadata = json.loads((workspace.intermediate / "manifest.json").read_text(encoding="utf-8"))
    project = load_project_config(workspace.root / "project.toml")
    if metadata["adapter_id"] != "renpy" or project.adapter_id != "renpy":
        raise ValueError("Byte delta helper only supports the Ren'Py adapter")
    if (
        metadata["source_language"] != project.source_language
        or metadata["target_language"] != project.target_language
    ):
        raise ValueError("Registered manifest and project languages differ")
    if source_root != project.source_root.resolve():
        raise ValueError("Source root differs from the registered workspace project")
    adapter = RenPyAdapter()
    options = dict(project.adapter_options)
    options.update(target_language=project.target_language, full_staging=False, lint_enabled=False)
    config = AdapterConfig(options=options)
    units = UnitRepository(workspace.intermediate / "units.jsonl").load()
    by_id = {unit.unit_id: unit for unit in units}
    if len(by_id) != len(units) or not units:
        raise ValueError("Extracted unit inventory is empty or has duplicate IDs")
    if set(unit_ids) - by_id.keys():
        raise ValueError("Whitelist contains unknown unit IDs")
    source_files = adapter.discover_files(source_root, config)
    source_names = [source.relative_path.casefold() for source in source_files]
    if len(source_names) != len(set(source_names)):
        raise ValueError("Windows case-insensitive source path collision")
    for source in source_files:
        ensure_within(source_root, source_root / safe_game_path(source.relative_path))
    extraction = adapter.extract(source_root, source_files, config)
    if any(issue.severity == Severity.ERROR for issue in extraction.issues):
        raise ValueError("Source extraction has errors; no delta was produced")
    if {unit.unit_id: _identity(unit) for unit in extraction.units} != {
        unit.unit_id: _identity(unit) for unit in units
    }:
        raise ValueError("Extraction inventory or source locations changed; extract again")
    revisions = RevisionStore(workspace.intermediate / "revisions.jsonl").read()
    latest = {row["unit_id"]: row for row in revisions}
    selected_ids = set(unit_ids)
    selected = [unit for unit in units if unit.unit_id in selected_ids]
    common = []
    for unit in selected:
        if unit.translation.status not in {
            TranslationStatus.TRANSLATED,
            TranslationStatus.REVIEWED,
        }:
            raise ValueError(f"Selected unit is not translated/reviewed: {unit.unit_id}")
        if unit.revision < 1 or latest.get(unit.unit_id, {}).get("after") != unit.target_text:
            raise ValueError(f"Selected translation has no matching revision: {unit.unit_id}")
        common.extend(validate_unit(unit))
    if any(issue.severity == Severity.ERROR for issue in common):
        raise ValueError("Selected translations failed common validation")

    grouped: dict[str, list[TranslationUnit]] = defaultdict(list)
    occupied: set[str] = set()
    for unit in units:
        relative = safe_game_path(str(unit.origin["path"]))
        if not relative.lower().endswith(".rpy"):
            raise ValueError("Only readable .rpy source files are supported")
        ensure_within(source_root, source_root / relative)
    for unit in selected:
        grouped[str(unit.origin["path"])].append(unit)
    for relative in grouped:
        if relative.casefold() in occupied:
            raise ValueError("Windows case-insensitive path collision")
        occupied.add(relative.casefold())
        occupied.add(str(PurePosixPath(relative).with_suffix(".rpyc")).casefold())
    extras = []
    source_existing = {
        str(path.relative_to(source_root)).casefold() for path in source_root.rglob("*")
    }
    for relative, path in sorted(extra_files.items()):
        safe_game_path(relative)
        if relative.casefold() in occupied:
            raise ValueError(f"Extra file collides with a script or compiled path: {relative}")
        occupied.add(relative.casefold())
        if relative.lower().endswith(".rpy"):
            compiled = str(PurePosixPath(relative).with_suffix(".rpyc")).casefold()
            if compiled in occupied or compiled in source_existing:
                raise ValueError("Extra runtime script has a compiled path collision")
            occupied.add(compiled)
        destination = ensure_within(source_root, source_root / relative)
        # Check all names, not just Path.exists(), because the build host may be Linux.
        siblings = destination.parent.iterdir() if destination.parent.is_dir() else ()
        if (
            relative.casefold() in source_existing
            or destination.exists()
            or any(p.name.casefold() == destination.name.casefold() for p in siblings)
        ):
            raise ValueError(f"Extra file already exists in the source game: {relative}")
        if any(parent.is_file() for parent in destination.parents if parent != source_root):
            raise ValueError(f"Extra file has an existing file as its parent: {relative}")
        if not path.is_file():
            raise ValueError(f"Extra source file does not exist: {relative}")
        extras.append(
            {
                "path": relative,
                "payload_path": "payload/extras/" + relative,
                "sha256": file_hash(path),
                "size": path.stat().st_size,
            }
        )
    runtime_guards = []
    runtime_names: set[str] = set()
    source_guard_names = {source.relative_path.casefold() for source in source_files}
    for relative in runtime_guard_paths:
        safe_relative_path(relative)
        name = relative.casefold()
        if name in runtime_names or name in occupied or name in source_guard_names:
            raise ValueError("Runtime guard path is duplicate or overlaps a patch/source path")
        runtime_names.add(name)
        path = regular_guard_file(source_root, relative)
        runtime_guards.append(
            {"path": relative, "source_sha256": file_hash(path), "source_size": path.stat().st_size}
        )

    # Staging may contain local original text, but is never copied into the payload.
    with tempfile.TemporaryDirectory(prefix="renpy-delta-", dir=workspace.staging) as temporary:
        staging = Path(temporary)
        rendered = [unit.model_copy(deep=True) for unit in units]
        for unit in rendered:
            if unit.unit_id not in selected_ids:
                unit.target_text = unit.source_text
        adapter.apply(source_root, staging, rendered, config)
        report = adapter.validate(staging, rendered, config)
        if any(issue.severity == Severity.ERROR for issue in report.issues):
            raise ValueError("Ren'Py staging validation failed; no delta was produced")
        files = []
        for relative, file_units in sorted(grouped.items()):
            source = (source_root / relative).read_bytes()
            source_fingerprint = bytes_hash(source)
            if any(unit.origin["file_fingerprint"] != source_fingerprint for unit in file_units):
                raise ValueError("Source changed while constructing the byte delta")
            text = source.decode("utf-8-sig")
            bom_size = 3 if source.startswith(b"\xef\xbb\xbf") else 0
            replacements = []
            spans = []
            for unit in file_units:
                start = int(unit.adapter_data["content_start"])
                end = int(unit.adapter_data["content_end"])
                if not 0 <= start <= end <= len(text):
                    raise ValueError("Invalid source content interval")
                if text[start:end] != unit.adapter_data["source_raw_content"]:
                    raise ValueError("Source content interval does not match extraction")
                spans.append((start, end))
                if unit.target_text == unit.source_text:
                    continue
                replacement = encode_string_content(
                    unit.target_text,
                    quote=str(unit.adapter_data["quote"]),
                    raw_prefix="r" in str(unit.adapter_data.get("string_prefix", "")).lower(),
                    escape_mode=unit.adapter_data.get("escape_mode"),
                    source_raw_content=str(unit.adapter_data["source_raw_content"]),
                ).encode("utf-8")
                replacements.append(
                    {
                        "unit_id": unit.unit_id,
                        "start": bom_size + len(text[:start].encode("utf-8")),
                        "end": bom_size + len(text[:end].encode("utf-8")),
                        "replacement_base64": base64.b64encode(replacement).decode("ascii"),
                    }
                )
            spans.sort()
            if any(
                left[1] > right[0] or left == right
                for left, right in zip(spans, spans[1:], strict=False)
            ):
                raise ValueError("Overlapping or duplicate source intervals")
            if not replacements:
                continue
            replacements.sort(key=lambda row: int(row["start"]))
            patched = apply_bytes(source, replacements)
            if patched != (staging / relative).read_bytes():
                raise ValueError("Byte delta differs from the validated Ren'Py writer result")
            files.append(
                {
                    "path": relative,
                    "source_sha256": source_fingerprint,
                    "source_size": len(source),
                    "target_sha256": file_hash(staging / relative),
                    "target_size": len(patched),
                    "replacements": replacements,
                }
            )
    if not files and not extras:
        raise ValueError("Whitelist produces no changes or extra files")
    manifest = {
        "schema": "fvn-renpy-byte-delta/v1",
        "patch_id": patch_id,
        "project": {
            "name": project.project_name,
            "source_version": options.get("source_version"),
            "source_language": project.source_language,
            "target_language": project.target_language,
        },
        "coverage": {
            "total": len(units),
            "selected": len(selected),
            "unselected": len(units) - len(selected),
            "selected_complete": len(selected),
            "project_status_counts": dict(Counter(unit.translation.status.value for unit in units)),
        },
        "selected_unit_ids": [unit.unit_id for unit in selected],
        "source_guards": [
            {
                "path": safe_game_path(source.relative_path),
                "source_sha256": source.fingerprint,
                "source_size": source.size,
            }
            for source in source_files
        ],
        "runtime_guards": sorted(runtime_guards, key=lambda row: row["path"]),
        "validation": {
            "common_error_count": 0,
            "common_warnings": [
                {"unit_id": issue.unit_id, "code": issue.code}
                for issue in common
                if issue.severity == Severity.WARNING
            ],
            "adapter_error_count": 0,
        },
        "files": files,
        "extras": extras,
    }
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".delta-build-", dir=output_root.parent) as temporary:
        build = Path(temporary) / "patch"
        build.mkdir()
        atomic_write_json(build / "patch.json", manifest)
        script = (TEMPLATES / "install.ps1").read_text(encoding="utf-8")
        script = script.replace("@@MANIFEST_SHA256@@", file_hash(build / "patch.json"))
        atomic_write_bytes(
            build / "install.ps1",
            script.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"),
        )
        for filename in ("install.cmd", "uninstall.cmd"):
            command = (TEMPLATES / filename).read_text(encoding="ascii")
            atomic_write_bytes(
                build / filename,
                command.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"),
            )
        for row in extras:
            destination = build / str(row["payload_path"])
            atomic_write_bytes(destination, extra_files[str(row["path"])].read_bytes())
            if file_hash(destination) != row["sha256"] or destination.stat().st_size != row["size"]:
                raise ValueError("Extra source changed during the build")
        notes = (
            f"# {project.project_name} 目标文字差量补丁\n\n"
            f"适用版本：{options.get('source_version') or '以 patch.json 源文件哈希为准'}。"
            f"语言：{project.source_language} → {project.target_language}。\n\n"
            f"本补丁处理明确选定的 {len(selected)} / {len(units)} 个文本单元；"
            "其余内容由玩家本地原版提供，不代表全作汉化。补丁不包含原剧情脚本。\n\n"
            "## 安装\n\n"
            "关闭游戏，将本目录所有文件解压到原游戏 EXE 同级目录，双击 install.cmd。"
            "不要先手动覆盖 game 内脚本。安装器会先核对全部源文件和附件，"
            "备份原脚本与其同名编译文件，再按 UTF-8 字节差量写入译文和新增附件。"
            "无需 Python 或管理员权限。错版、改过脚本、已有同名新增附件时会拒绝安装。\n\n"
            "请使用普通解压目录；安装器拒绝符号链接或目录联接。\n\n"
            "## 回退与中断恢复\n\n"
            "关闭游戏，在同一目录双击 uninstall.cmd。回退先核对已安装脚本和附件哈希，"
            "不会覆盖后续手工修改。原脚本恢复自 .fvn-backups/补丁ID/original；"
            "运行后生成的编译文件和已移除附件仍保存在该备份目录。"
            "在 state.json 已保存之后若安装中断，可运行 uninstall.cmd；"
            "备份准备阶段失败而尚无 state.json 时，安装器尚未替换游戏脚本或移走编译文件，"
            "自动回退没有可用状态。请保留部分备份，优先重新解压官方原版至新目录后重装。"
            "回退成功后要重装相同补丁时，先将该补丁的备份子目录归档到游戏目录外保留。"
            "电源中断或磁盘故障无法保证跨文件整体原子性，"
            "请保留该备份目录和 state.json 直到核验恢复。安装器文件、备份目录及根目录锁文件"
            "不属于游戏脚本，不会自动删除。\n"
        )
        if install_notes:
            notes += "\n## 本游戏说明\n\n" + install_notes.strip() + "\n"
        atomic_write_text(build / "README.md", notes)
        os.replace(build, output_root)
    return output_root / "patch.json"


def apply_bytes(source: bytes, replacements: list[dict[str, object]]) -> bytes:
    """Pure reference application, also checked against RenPyWriter during build."""
    output = bytearray()
    cursor = 0
    for row in replacements:
        start, end = row["start"], row["end"]
        replacement = row["replacement_base64"]
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
            or not isinstance(replacement, str)
        ):
            raise ValueError("Byte offsets must be integers and replacement must be base64 text")
        if not cursor <= start <= end <= len(source):
            raise ValueError("Overlapping or out-of-bounds byte replacement")
        output.extend(source[cursor:start])
        output.extend(base64.b64decode(replacement, validate=True))
        cursor = end
    output.extend(source[cursor:])
    return bytes(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--unit-ids-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--patch-id", required=True)
    parser.add_argument("--extra", action="append", default=[], metavar="GAME_PATH=LOCAL_FILE")
    parser.add_argument("--runtime-guard", action="append", default=[], metavar="RELATIVE_FILE")
    parser.add_argument("--install-notes", type=Path)
    arguments = parser.parse_args()
    extras: dict[str, Path] = {}
    for value in arguments.extra:
        relative, separator, local = value.partition("=")
        if not separator or not local or relative.casefold() in {key.casefold() for key in extras}:
            parser.error("--extra requires unique GAME_PATH=LOCAL_FILE entries")
        extras[relative] = Path(local)
    result = build_delta(
        Workspace(arguments.workspace),
        source_root=arguments.source,
        unit_ids=_read_ids(arguments.unit_ids_file),
        output_root=arguments.output,
        patch_id=arguments.patch_id,
        extra_files=extras,
        runtime_guard_paths=arguments.runtime_guard,
        install_notes=(
            arguments.install_notes.read_text(encoding="utf-8") if arguments.install_notes else ""
        ),
    )
    print(result)


if __name__ == "__main__":
    main()
