"""Target-only delta tests use synthetic scripts; no downloaded game text is a fixture."""

import base64
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from fvn_translator.adapters.renpy import RenPyAdapter
from fvn_translator.config import ProjectConfig
from fvn_translator.core.atomic_io import atomic_write_json
from fvn_translator.core.hashing import file_hash
from fvn_translator.models import TranslationStatus
from fvn_translator.services import ExtractionService, ProjectService
from fvn_translator.services.agent_translation_service import AgentTranslationService
from fvn_translator.storage import UnitRepository

HELPER = Path(__file__).resolve().parents[2] / "skills/fvn-translate/scripts/build_renpy_delta.py"
SPEC = importlib.util.spec_from_file_location("build_renpy_delta", HELPER)
assert SPEC and SPEC.loader
delta = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(delta)


@pytest.fixture
def delta_project(tmp_path):
    source = tmp_path / "source"
    (source / "game").mkdir(parents=True)
    script = (
        "# Unicode offset: π 校验 😊\r\nlabel start:\r\n"
        '    "Hello [name], {i}friend{/i}."\r\n'
        '    "UNSELECTED_ORIGINAL_SENTINEL."\r\n'
        '    "A quote: \\"yes\\" and slash \\\\."\r\n'
        '    "First line\\nSecond line."\r\n'
    )
    (source / "game/script.rpy").write_bytes(b"\xef\xbb\xbf" + script.encode("utf-8"))
    (source / "game/other.rpy").write_text(
        'label other:\n    "Another source."\n', encoding="utf-8"
    )
    (source / "game/script.rpyc").write_bytes(b"synthetic compiled original")
    (source / "game/logic.rpy").write_text("init python:\n    synthetic_flag = True\n")
    (source / "renpy").mkdir()
    (source / "renpy/vc_version.py").write_text("version = '8.5.2-synthetic'\n")
    (source / "Synthetic.exe").write_bytes(b"MZ synthetic Windows executable")
    workspace = ProjectService().create(
        tmp_path / "workspace",
        ProjectConfig(
            project_name="Synthetic byte delta",
            source_root=source,
            adapter_id="renpy",
            target_language="zh-CN",
            adapter_options={"source_version": "test-1"},
        ),
        adapter_version=RenPyAdapter.adapter_version,
    )
    repository = UnitRepository(workspace.intermediate / "units.jsonl")
    ExtractionService(RenPyAdapter(), repository).extract(source)
    units = repository.load()
    assert len(units) == 5
    targets = {
        "Hello [name], {i}friend{/i}.": "你好，[name]，{i}朋友{/i}。",
        'A quote: "yes" and slash \\.': '引号："好"，斜线\\。',
        "First line\nSecond line.": "第一行\n第二行。",
        "Another source.": "另一句译文。",
    }
    selected = [unit.unit_id for unit in units if unit.source_text in targets]
    assert len(selected) == 4
    service = AgentTranslationService(workspace)
    for index, task in enumerate(
        service.export_batches(tmp_path / "tasks", unit_ids=set(selected))
    ):
        response = tmp_path / f"response-{index}.json"
        atomic_write_json(
            response,
            {
                "translations": [
                    {"unit_id": unit["unit_id"], "target_text": targets[unit["source_text"]]}
                    for unit in json.loads(task.read_text(encoding="utf-8"))["units"]
                ]
            },
        )
        service.import_batch(task, response, model="offline-test-fixture")
    return source, workspace, repository, selected


def build_fixture(delta_project, tmp_path, **kwargs):
    source, workspace, _, selected = delta_project
    return delta.build_delta(
        workspace,
        source_root=source,
        unit_ids=selected,
        output_root=tmp_path / "built-patch",
        patch_id="synthetic-1",
        **kwargs,
    )


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def test_delta_is_target_only_preserves_bom_crlf_offsets_and_pending_state(delta_project, tmp_path):
    source, workspace, repository, _ = delta_project
    before_source = snapshot(source)
    before_units = repository.path.read_bytes()
    before_revisions = (workspace.intermediate / "revisions.jsonl").read_bytes()
    manifest_path = build_fixture(delta_project, tmp_path)
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest = json.loads(manifest_text)
    assert "UNSELECTED_ORIGINAL_SENTINEL" not in manifest_text
    assert "Hello" not in manifest_text
    assert "source_text" not in manifest_text and "context" not in manifest_text
    assert manifest["coverage"]["total"] == 5
    assert manifest["coverage"]["selected"] == 4
    assert manifest["coverage"]["unselected"] == 1
    assert manifest["coverage"]["project_status_counts"] == {"translated": 4, "pending": 1}
    assert {row["path"] for row in manifest["source_guards"]} == {
        "game/script.rpy",
        "game/other.rpy",
        "game/logic.rpy",
    }
    for row in manifest["files"]:
        original = before_source[row["path"]]
        patched = delta.apply_bytes(original, row["replacements"])
        if row["path"] == "game/script.rpy":
            assert patched.startswith(b"\xef\xbb\xbf")
            assert patched.count(b"\r\n") == original.count(b"\r\n")
            assert b"UNSELECTED_ORIGINAL_SENTINEL" in patched
            assert "你好" in patched.decode("utf-8-sig")
            assert "第一行\\n第二行" in patched.decode("utf-8-sig")
        for replacement in row["replacements"]:
            assert base64.b64decode(replacement["replacement_base64"]).decode("utf-8")
    assert snapshot(source) == before_source
    assert repository.path.read_bytes() == before_units
    assert (workspace.intermediate / "revisions.jsonl").read_bytes() == before_revisions
    excluded = next(unit for unit in repository.load() if "UNSELECTED_" in unit.source_text)
    assert excluded.translation.status == TranslationStatus.PENDING
    assert excluded.target_text == "" and excluded.revision == 0
    assert file_hash(manifest_path) in (manifest_path.parent / "install.ps1").read_text()


@pytest.mark.parametrize(
    "kind", ["pending", "skipped", "revision", "location", "source", "missing"]
)
def test_delta_rejects_unregistered_changed_or_unfinished_input(delta_project, tmp_path, kind):
    source, workspace, repository, selected = delta_project
    units = repository.load()
    unit = next(unit for unit in units if unit.unit_id == selected[0])
    if kind in {"pending", "skipped"}:
        unit.translation.status = TranslationStatus(kind)
    elif kind == "revision":
        unit.revision = 0
    elif kind == "location":
        unit.adapter_data["content_start"] += 1
    elif kind == "source":
        (source / "game/other.rpy").write_text('label other:\n    "Changed."\n')
    elif kind == "missing":
        units.pop()
    repository.save(units)
    with pytest.raises(ValueError):
        build_fixture(delta_project, tmp_path)
    assert not (tmp_path / "built-patch").exists()
    assert not workspace.lock_path.exists()


@pytest.mark.parametrize(
    "relative",
    [
        "../escape",
        "game/../escape",
        "game/C:foo",
        "game/CON.txt",
        "game/name.",
        "game\\font",
        "game/SCRIPT.RPY",
        "game/script.rpyc",
    ],
)
def test_delta_rejects_unsafe_extra_paths_and_windows_collisions(delta_project, tmp_path, relative):
    font = tmp_path / "font"
    font.write_bytes(b"synthetic font")
    with pytest.raises(ValueError):
        build_fixture(delta_project, tmp_path, extra_files={relative: font})
    assert not (tmp_path / "built-patch").exists()


def test_delta_rejects_duplicate_ids_and_byte_spans(delta_project, tmp_path):
    source, workspace, _, selected = delta_project
    with pytest.raises(ValueError, match="unique"):
        delta.build_delta(
            workspace,
            source_root=source,
            unit_ids=selected * 2,
            output_root=tmp_path / "bad",
            patch_id="test",
        )
    with pytest.raises(ValueError, match="Overlapping"):
        delta.apply_bytes(
            b"1234",
            [
                {"start": 0, "end": 3, "replacement_base64": "eA=="},
                {"start": 2, "end": 4, "replacement_base64": "eA=="},
            ],
        )


def _pwsh():
    value = os.environ.get("FVN_TEST_PWSH") or shutil.which("pwsh")
    if not value:
        pytest.skip("Set FVN_TEST_PWSH to test the installer with a local PowerShell runtime")
    return value


def run_installer(patch, game, action="Install"):
    return subprocess.run(
        [
            _pwsh(),
            "-NoProfile",
            "-File",
            str(patch / "install.ps1"),
            "-Action",
            action,
            "-GameRoot",
            str(game),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_powershell_real_install_generated_compile_and_uninstall(delta_project, tmp_path):
    source, _, _, _ = delta_project
    runtime = tmp_path / "runtime.rpy"
    runtime.write_text("init python:\n    synthetic_delta_flag = True\n")
    font = tmp_path / "font.bin"
    font.write_bytes(b"synthetic font fixture")
    patch = build_fixture(
        delta_project,
        tmp_path,
        extra_files={"game/fvn/runtime.rpy": runtime, "game/fvn/font.bin": font},
    ).parent
    game = tmp_path / "installed"
    shutil.copytree(source, game)
    original = snapshot(game)
    result = run_installer(patch, game)
    assert result.returncode == 0, result.stdout + result.stderr
    manifest = json.loads((patch / "patch.json").read_text(encoding="utf-8"))
    for row in manifest["files"]:
        assert file_hash(game / row["path"]) == row["target_sha256"]
    assert not (game / "game/script.rpyc").exists()
    assert (game / "game/fvn/runtime.rpy").read_bytes() == runtime.read_bytes()
    (game / "game/script.rpyc").write_bytes(b"new compiled result")
    (game / "game/fvn/runtime.rpyc").write_bytes(b"new runtime compiled result")
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode == 0, result.stdout + result.stderr
    for relative, payload in original.items():
        assert (game / relative).read_bytes() == payload
    assert not (game / "game/fvn/runtime.rpy").exists()
    assert not (game / "game/fvn/runtime.rpyc").exists()
    assert not (game / "game/fvn/font.bin").exists()
    state = json.loads((game / ".fvn-backups/synthetic-1/state.json").read_text(encoding="utf-8"))
    assert state["phase"] == "uninstalled"
    assert run_installer(patch, game, "Uninstall").returncode == 0


@pytest.mark.parametrize(
    "failure", ["source", "no_text_source", "extra_exists", "payload", "manifest"]
)
def test_powershell_preflight_failures_do_not_change_any_game_file(
    delta_project, tmp_path, failure
):
    font = tmp_path / "font.bin"
    font.write_bytes(b"synthetic font fixture")
    patch = build_fixture(delta_project, tmp_path, extra_files={"game/new.bin": font}).parent
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    if failure == "source":
        (game / "game/script.rpy").write_bytes(b"user changed original")
    elif failure == "no_text_source":
        (game / "game/logic.rpy").write_text("init python:\n    synthetic_flag = False\n")
    elif failure == "extra_exists":
        (game / "game/new.bin").write_bytes(b"keep this existing file")
    elif failure == "payload":
        (patch / "payload/extras/game/new.bin").write_bytes(b"corrupt payload")
    else:
        (patch / "patch.json").write_bytes(b"{}")
    before = snapshot(game)
    result = run_installer(patch, game)
    assert result.returncode != 0
    after = snapshot(game)
    after.pop(".fvn-patch.lock", None)
    assert after == before
    assert not (game / ".fvn-backups").exists()


def test_powershell_uninstall_refuses_changed_script_before_any_restore(delta_project, tmp_path):
    patch = build_fixture(delta_project, tmp_path).parent
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    result = run_installer(patch, game)
    assert result.returncode == 0, result.stdout + result.stderr
    (game / "game/script.rpy").write_bytes(b"later user modification")
    before = snapshot(game)
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode != 0
    assert snapshot(game) == before


@pytest.mark.parametrize("interruption", ["exception", "exit"])
def test_powershell_partial_install_can_restore_all_originals(
    delta_project, tmp_path, interruption
):
    patch = build_fixture(delta_project, tmp_path).parent
    script = patch / "install.ps1"
    text = script.read_text(encoding="ascii")
    injected = "throw 'synthetic write interruption'" if interruption == "exception" else "exit 73"
    # Only this disposable synthetic test's installer is fault-injected.
    text = text.replace(
        "Write-Atomic $path $file.bytes", "Write-Atomic $path $file.bytes\n" + injected
    )
    script.write_text(text, encoding="ascii")
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    original = snapshot(game)
    result = run_installer(patch, game)
    assert result.returncode != 0
    if interruption == "exit":
        state = json.loads((game / ".fvn-backups/synthetic-1/state.json").read_text())
        assert state["phase"] == "prepared"
        result = run_installer(patch, game, "Uninstall")
        assert result.returncode == 0, result.stdout + result.stderr
    for relative, payload in original.items():
        assert (game / relative).read_bytes() == payload
    state = json.loads((game / ".fvn-backups/synthetic-1/state.json").read_text())
    assert state["phase"] == "uninstalled"


def test_powershell_backup_corruption_is_rejected_before_restore(delta_project, tmp_path):
    patch = build_fixture(delta_project, tmp_path).parent
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    result = run_installer(patch, game)
    assert result.returncode == 0, result.stdout + result.stderr
    (game / ".fvn-backups/synthetic-1/original/game/script.rpy").write_bytes(b"corrupt backup")
    before = snapshot(game)
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode != 0
    assert snapshot(game) == before


def test_powershell_linked_game_directory_is_rejected(delta_project, tmp_path):
    patch = build_fixture(delta_project, tmp_path).parent
    game = tmp_path / "linked-game"
    game.mkdir()
    (game / "game").symlink_to(delta_project[0] / "game", target_is_directory=True)
    before = snapshot(delta_project[0])
    result = run_installer(patch, game)
    assert result.returncode != 0
    assert snapshot(delta_project[0]) == before


def test_powershell_tampered_state_inventory_cannot_move_another_file(delta_project, tmp_path):
    patch = build_fixture(delta_project, tmp_path).parent
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    result = run_installer(patch, game)
    assert result.returncode == 0, result.stdout + result.stderr
    state_path = game / ".fvn-backups/synthetic-1/state.json"
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["compiled"][0]["path"] = "game/script.rpy"
    atomic_write_json(state_path, state)
    before = snapshot(game)
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode != 0
    assert snapshot(game) == before


def test_powershell_backup_preparation_failure_leaves_game_unchanged(delta_project, tmp_path):
    patch = build_fixture(delta_project, tmp_path).parent
    script = patch / "install.ps1"
    text = script.read_text(encoding="ascii")
    text = text.replace(
        "[System.IO.File]::Copy($path, $backup, $false)",
        "if ($file.path -eq 'game/script.rpy') { throw 'synthetic backup failure' }; "
        "[System.IO.File]::Copy($path, $backup, $false)",
    )
    script.write_text(text, encoding="ascii")
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    original = snapshot(game)
    result = run_installer(patch, game)
    assert result.returncode != 0
    assert "before this installer replaced any game script" in result.stderr
    for relative, payload in original.items():
        assert (game / relative).read_bytes() == payload
    assert not (game / ".fvn-backups/synthetic-1/state.json").exists()
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode != 0
    assert "No backup state found" in result.stderr


def test_extras_only_preserved_whitelist_retains_source_guards(delta_project, tmp_path):
    source, workspace, _, _ = delta_project
    service = AgentTranslationService(workspace)
    for index, task_path in enumerate((tmp_path / "tasks/tasks").glob("*.json")):
        task = json.loads(task_path.read_text(encoding="utf-8"))
        response = tmp_path / f"preserve-{index}.json"
        atomic_write_json(
            response,
            {
                "translations": [
                    {"unit_id": row["unit_id"], "target_text": row["source_text"]}
                    for row in task["units"]
                ]
            },
        )
        service.import_batch(task_path, response, model="offline-revision-test")
    extra = tmp_path / "extra.bin"
    extra.write_bytes(b"synthetic added payload")
    patch = build_fixture(delta_project, tmp_path, extra_files={"game/extra.bin": extra}).parent
    manifest = json.loads((patch / "patch.json").read_text(encoding="utf-8"))
    assert manifest["files"] == []
    assert len(manifest["source_guards"]) == 3
    game = tmp_path / "installed"
    shutil.copytree(source, game)
    before = snapshot(game)
    result = run_installer(patch, game)
    assert result.returncode == 0, result.stdout + result.stderr
    for relative, payload in before.items():
        assert (game / relative).read_bytes() == payload
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode == 0, result.stdout + result.stderr
    assert not (game / "game/extra.bin").exists()


@pytest.mark.parametrize("relative", ["renpy/vc_version.py", "Synthetic.exe"])
def test_powershell_runtime_guard_rejects_wrong_engine_or_platform_before_any_write(
    delta_project, tmp_path, relative
):
    patch = build_fixture(
        delta_project, tmp_path, runtime_guard_paths=["renpy/vc_version.py", "Synthetic.exe"]
    ).parent
    manifest = json.loads((patch / "patch.json").read_text(encoding="utf-8"))
    assert {row["path"] for row in manifest["runtime_guards"]} == {
        "renpy/vc_version.py",
        "Synthetic.exe",
    }
    assert not {row["path"] for row in manifest["runtime_guards"]}.intersection(
        row["path"] for row in manifest["source_guards"]
    )
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    (game / relative).write_bytes(b"different engine or platform")
    before = snapshot(game)
    result = run_installer(patch, game)
    assert result.returncode != 0
    assert "Runtime version/platform mismatch" in result.stderr
    assert snapshot(game) == before


def test_runtime_guards_are_read_only_and_are_not_restored_on_uninstall(delta_project, tmp_path):
    patch = build_fixture(
        delta_project, tmp_path, runtime_guard_paths=["renpy/vc_version.py", "Synthetic.exe"]
    ).parent
    game = tmp_path / "installed"
    shutil.copytree(delta_project[0], game)
    result = run_installer(patch, game)
    assert result.returncode == 0, result.stdout + result.stderr
    runtime = game / "renpy/vc_version.py"
    runtime.write_bytes(b"later user engine change")
    result = run_installer(patch, game, "Uninstall")
    assert result.returncode == 0, result.stdout + result.stderr
    assert runtime.read_bytes() == b"later user engine change"
    assert not (game / ".fvn-backups/synthetic-1/original/renpy/vc_version.py").exists()


@pytest.mark.parametrize(
    "relative", ["../escape", "C:/engine", "renpy\\engine.py", "game/script.rpy", "renpy"]
)
def test_runtime_guards_require_safe_distinct_ordinary_files(delta_project, tmp_path, relative):
    with pytest.raises((ValueError, OSError)):
        build_fixture(delta_project, tmp_path, runtime_guard_paths=[relative])
    assert not (tmp_path / "built-patch").exists()


def test_runtime_guard_cannot_follow_a_symbolic_link(delta_project, tmp_path):
    source = delta_project[0]
    outside = tmp_path / "outside-engine.py"
    outside.write_bytes(b"outside guard input")
    (source / "engine-link.py").symlink_to(outside)
    with pytest.raises(ValueError, match="linked"):
        build_fixture(delta_project, tmp_path, runtime_guard_paths=["engine-link.py"])
