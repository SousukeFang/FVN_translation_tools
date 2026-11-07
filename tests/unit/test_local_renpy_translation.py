"""Standalone manual translation exchange, using only synthetic original text."""

import base64
import copy
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills/fvn-translate/scripts/local_renpy_translation.py"
SPEC = importlib.util.spec_from_file_location("local_renpy_translation", SCRIPT)
assert SPEC and SPEC.loader
local = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(local)
TEMPLATES = SCRIPT.with_name("renpy_delta_templates")


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


@pytest.fixture
def manual_project(tmp_path):
    source, base = tmp_path / "source", tmp_path / "base"
    (source / "game").mkdir(parents=True)
    base.mkdir()
    literals = [
        ("u-hello", "say", r"Hello  [name], {i}friend{/i}.\nNext  line."),
        ("u-unknown", "say", r"Odd\Q escape."),
        ("u-quote", "say", r"QUOTE: \"yes\" and path \\."),
        ("u-null", "say", "NO_FILL_ORIGINAL_SENTINEL."),
        ("u-note", "assignment", r"First  part\nNext\tcolumn."),
    ]
    text = "# Unicode offset: π 校验 😊\r\nlabel start:\r\n"
    for _unit_id, kind, raw in literals:
        text += ("    note = " if kind == "assignment" else "    ") + '"' + raw + '"\r\n'
    sources = {
        "game/script.rpy": b"\xef\xbb\xbf" + text.encode("utf-8"),
        "game/screens.rpy": b'screen main():\n    textbutton "Start" action Return()\n',
        "game/logic.rpy": b"init python:\n    synthetic_flag = True\n",
    }
    for relative, data in sources.items():
        (source / relative).write_bytes(data)
    (source / "game/script.rpyc").write_bytes(b"synthetic original compiled script")
    (source / "game/screens.rpyc").write_bytes(b"synthetic original compiled screen")
    (source / "renpy").mkdir()
    (source / "renpy/vc_version.py").write_text("version = '8.5.2-synthetic'\n")
    (source / "Synthetic.exe").write_bytes(b"MZ synthetic Windows executable")
    guards = [
        {"path": relative, "source_sha256": local.digest(data), "source_size": len(data)}
        for relative, data in sorted(sources.items())
    ]
    units = []
    for sequence, (unit_id, kind, raw) in enumerate(
        literals + [("u-start", "screen_textbutton", "Start")]
    ):
        relative = "game/screens.rpy" if unit_id == "u-start" else "game/script.rpy"
        data = sources[relative]
        decoded_file = data.decode("utf-8-sig")
        start = decoded_file.index(raw)
        units.append(
            {
                "unit_id": unit_id,
                "sequence": sequence,
                "source_fingerprint": local.digest(raw.encode()),
                "type": "ui_button" if unit_id == "u-start" else "dialogue",
                "speaker": None,
                "origin": {
                    "path": relative,
                    "line": decoded_file.count("\n", 0, start) + 1,
                    "file_fingerprint": local.digest(data),
                },
                "context": {},
                "adapter_data": {
                    "content_start": start,
                    "content_end": start + len(raw),
                    "source_raw_content": raw,
                    "quote": '"',
                    "string_prefix": "",
                    "node_kind": kind,
                },
            }
        )
    ftif = tmp_path / "units.jsonl"
    ftif.write_text("\n".join(json.dumps(unit) for unit in units), encoding="utf-8")
    screens = sources["game/screens.rpy"]
    position = screens.index(b"Start")
    replacement = {
        "unit_id": "u-start",
        "start": position,
        "end": position + 5,
        "replacement_base64": base64.b64encode("开始".encode()).decode(),
    }
    target = local.apply_replacements(screens, [replacement])
    runtime = b"init python:\n    synthetic_manual_font_flag = True\n"
    extras = [
        {
            "path": "game/fvn/font.bin",
            "payload_path": "payload/extras/game/fvn/font.bin",
            "size": 12,
            "sha256": local.digest(b"fixture font"),
        },
        {
            "path": "game/fvn/runtime.rpy",
            "payload_path": "payload/extras/game/fvn/runtime.rpy",
            "size": len(runtime),
            "sha256": local.digest(runtime),
        },
    ]
    manifest = {
        "schema": local.PATCH_SCHEMA,
        "patch_id": "synthetic-ui-r1",
        "project": {
            "name": "Synthetic manual tooling",
            "source_version": "test-1",
            "source_language": "en",
            "target_language": "zh-CN",
        },
        "source_guards": guards,
        "selected_unit_ids": ["u-start"],
        "coverage": {"total": 6, "selected": 1},
        "files": [
            {
                "path": "game/screens.rpy",
                "source_sha256": local.digest(screens),
                "source_size": len(screens),
                "target_sha256": local.digest(target),
                "target_size": len(target),
                "replacements": [replacement],
            }
        ],
        "extras": extras,
    }
    local.atomic_write(base / "patch.json", local.json_bytes(manifest))
    script = (
        (TEMPLATES / "install.ps1")
        .read_text()
        .replace("@@MANIFEST_SHA256@@", local.digest((base / "patch.json").read_bytes()))
    )
    (base / "install.ps1").write_text(script, encoding="ascii")
    for name in ("install.cmd", "uninstall.cmd"):
        shutil.copyfile(TEMPLATES / name, base / name)
    local.atomic_write(base / extras[0]["payload_path"], b"fixture font")
    local.atomic_write(base / extras[1]["payload_path"], runtime)
    shutil.copyfile(SCRIPT, base / SCRIPT.name)
    catalog_path = base / "source-catalog.json"
    catalog = local.build_catalog(ftif, source, base, catalog_path)
    return source, base, catalog, manifest, catalog_path, ftif


def export_rows(project, tmp_path):
    source, _, catalog, base, _, _ = project
    output = tmp_path / "untranslated.jsonl"
    report = local.export_untranslated(source, catalog, base, output)
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    return output, rows, report


def fill_rows(path, rows):
    targets = {
        "u-hello": "你好 [name]，{i}朋友{/i}。\n下一行。",
        "u-unknown": "奇怪的转义。",
        "u-quote": "引号：“好”，路径 \\。",
        "u-note": "第一  段\n下一\t列。",
    }
    for row in rows:
        row["target_text"] = targets.get(row["unit_id"])
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8"
    )


def run_cli(script, *arguments):
    return subprocess.run(
        [sys.executable, "-I", str(script), *map(str, arguments)],
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )


def pwsh():
    value = os.environ.get("FVN_TEST_PWSH") or shutil.which("pwsh")
    if not value:
        pytest.skip("Set FVN_TEST_PWSH for real local installer execution")
    return value


def install(base, game, action="Install"):
    return subprocess.run(
        [
            pwsh(),
            "-NoProfile",
            "-File",
            str(base / "install.ps1"),
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


def test_catalog_has_only_metadata_export_uses_correct_literal_codecs(manual_project, tmp_path):
    source, base, catalog, manifest, catalog_path, _ = manual_project
    metadata = catalog_path.read_text(encoding="utf-8")
    assert "source_text" not in metadata and "source_raw_content" not in metadata
    for sentinel in ("Hello", "NO_FILL_ORIGINAL_SENTINEL", "Start", "First  part"):
        assert sentinel not in metadata
    assert len(catalog["units"]) == 6
    assert local.load_context(catalog_path, base) == (catalog, manifest)
    _, rows, report = export_rows(manual_project, tmp_path)
    assert report["exported"] == 5 and report["decode_warnings"] == 1
    by_id = {row["unit_id"]: row for row in rows}
    assert "u-start" not in by_id
    assert by_id["u-hello"]["source_text"] == "Hello [name], {i}friend{/i}.\nNext line."
    assert by_id["u-note"]["source_text"] == "First  part\nNext\tcolumn."
    assert by_id["u-unknown"]["source_text"] == "OddQ escape."
    assert by_id["u-unknown"]["warnings"]
    assert all(row["target_text"] is None for row in rows)
    result = run_cli(base / SCRIPT.name, "status", "--game-root", source)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["coverage"]["untranslated"] == 5


def test_partial_import_is_target_only_and_does_not_modify_game(manual_project, tmp_path):
    source, base, catalog, manifest, _, _ = manual_project
    path, rows, _ = export_rows(manual_project, tmp_path)
    fill_rows(path, rows)
    originals = local.read_originals(source, catalog, manifest)
    translated, report = local.read_translations(path, catalog, originals)
    assert report["filled"] == 4 and report["null"] == 1
    assert "\\" not in translated["u-unknown"]
    before = snapshot(source)
    output = tmp_path / "personal"
    result = local.import_personal(source, catalog, manifest, base, path, output, "personal-r1")
    assert snapshot(source) == before
    assert result["coverage"] == {
        "total": 6,
        "base_completed": 1,
        "base_changed": 1,
        "base_reviewed_unchanged": 0,
        "user_filled": 4,
        "user_changed": 4,
        "user_reviewed_unchanged": 0,
        "untranslated": 1,
    }
    personal = local.read_json(output / "patch.json")
    assert personal["extras"] == manifest["extras"]
    for file in personal["files"]:
        target = local.apply_replacements(before[file["path"]], file["replacements"])
        assert local.digest(target) == file["target_sha256"]
        if file["path"] == "game/script.rpy":
            assert target.startswith(b"\xef\xbb\xbf")
            assert target.count(b"\r\n") == before[file["path"]].count(b"\r\n")
    for data in snapshot(output).values():
        assert b"NO_FILL_ORIGINAL_SENTINEL" not in data
        assert b"Hello" not in data
    assert (
        local.load_context(output / "source-catalog.json", output)[1]["patch_id"] == "personal-r1"
    )
    assert not (output / path.name).exists()


@pytest.mark.parametrize(
    "failure",
    ["id", "duplicate", "source", "fingerprint", "tag", "interpolation", "newline", "type"],
)
def test_manual_input_validation_rejects_damage(manual_project, tmp_path, failure):
    source, _, catalog, manifest, _, _ = manual_project
    path, rows, _ = export_rows(manual_project, tmp_path)
    fill_rows(path, rows)
    hello = next(row for row in rows if row["unit_id"] == "u-hello")
    if failure == "id":
        hello["unit_id"] = "unknown-id"
    elif failure == "duplicate":
        rows.append(rows[0])
    elif failure == "source":
        hello["source_text"] += "edited"
    elif failure == "fingerprint":
        hello["source_fingerprint"] = "sha256:" + "0" * 64
    elif failure == "tag":
        hello["target_text"] = hello["target_text"].replace("{i}", "")
    elif failure == "interpolation":
        hello["target_text"] = hello["target_text"].replace("[name]", "")
    elif failure == "newline":
        hello["target_text"] = hello["target_text"].replace("\n", "")
    elif failure == "type":
        hello["target_text"] = 42
    path.write_text("\n".join(json.dumps(row) for row in rows))
    with pytest.raises(ValueError):
        local.read_translations(path, catalog, local.read_originals(source, catalog, manifest))


def test_original_guards_include_unmodified_no_text_script(manual_project, tmp_path):
    source, _, catalog, manifest, _, _ = manual_project
    (source / "game/logic.rpy").write_text("init python:\n    synthetic_flag = False\n")
    with pytest.raises(ValueError, match="Wrong version"):
        local.export_untranslated(source, catalog, manifest, tmp_path / "export.jsonl")
    assert not (tmp_path / "export.jsonl").exists()


def test_quote_and_semantic_escape_encoding_round_trips():
    for codec, source, target in [
        ("renpy", r"Quote: \"yes\" and slash \\.", "引号：“好”和斜线\\。"),
        ("python", r"Line  one\nLine\ttwo", "第一  行\n第二\t行"),
        ("renpy", r"Odd\Q text", "普通译文"),
    ]:
        original, _ = local.decode_content(source, codec, '"', "")
        unit = {"codec": codec, "quote": '"', "prefix": "", "locked": False}
        encoded = local.validate_target(original, target, unit)
        assert local.decode_content(encoded, codec, '"', "")[0] == target
    with pytest.raises(ValueError, match="Printf"):
        local.validate_target(
            "%(name)s %02d%%", "%(name)s %02f%%", {"codec": "python", "quote": '"', "prefix": ""}
        )


def test_real_installed_base_export_personal_install_and_next_round(manual_project, tmp_path):
    source, base, catalog, manifest, _, _ = manual_project
    game = tmp_path / "game-copy"
    shutil.copytree(source, game)
    original = snapshot(game)
    result = install(base, game)
    assert result.returncode == 0, result.stdout + result.stderr
    path = tmp_path / "installed-export.jsonl"
    local.export_untranslated(game, catalog, manifest, path)
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    fill_rows(path, rows)
    personal = tmp_path / "personal"
    result = run_cli(base / SCRIPT.name, "validate", "--game-root", game, "--translations", path)
    assert result.returncode == 0, result.stderr
    result = run_cli(
        base / SCRIPT.name,
        "import",
        "--game-root",
        game,
        "--translations",
        path,
        "--output",
        personal,
        "--patch-id",
        "personal-r1",
    )
    assert result.returncode == 0, result.stderr
    result = install(personal, game)
    assert result.returncode != 0  # Existing UI must be restored first.
    result = install(base, game, "Uninstall")
    assert result.returncode == 0, result.stdout + result.stderr
    result = install(personal, game)
    assert result.returncode == 0, result.stdout + result.stderr
    next_export = tmp_path / "next-export.jsonl"
    result = run_cli(personal / SCRIPT.name, "export", "--game-root", game, "--output", next_export)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["exported"] == 1
    assert len(next_export.read_text().splitlines()) == 1
    (game / "game/script.rpyc").write_bytes(b"synthetic regenerated compiled")
    (game / "game/fvn/runtime.rpyc").write_bytes(b"synthetic regenerated font runtime")
    result = install(personal, game, "Uninstall")
    assert result.returncode == 0, result.stdout + result.stderr
    for relative, data in original.items():
        assert (game / relative).read_bytes() == data
    assert not (game / "game/fvn/font.bin").exists()
    assert not (game / "game/fvn/runtime.rpyc").exists()


def test_modified_installed_target_cannot_use_old_backup(manual_project, tmp_path):
    source, base, catalog, manifest, _, _ = manual_project
    game = tmp_path / "game-copy"
    shutil.copytree(source, game)
    result = install(base, game)
    assert result.returncode == 0, result.stdout + result.stderr
    (game / "game/screens.rpy").write_bytes(b"later manual script change")
    with pytest.raises(ValueError, match="Wrong version"):
        local.read_originals(game, catalog, manifest)


def test_zero_text_font_base_skips_reviewed_originals_and_builds_personal_patch(
    manual_project, tmp_path
):
    source, base, _, manifest, catalog_path, ftif = manual_project
    old_hash = local.digest((base / "patch.json").read_bytes())
    font_base = copy.deepcopy(manifest)
    font_base["files"] = []
    local.atomic_write(base / "patch.json", local.json_bytes(font_base))
    new_hash = local.digest((base / "patch.json").read_bytes())
    installer = (base / "install.ps1").read_text().replace(old_hash, new_hash)
    (base / "install.ps1").write_text(installer, encoding="ascii")
    catalog = local.build_catalog(ftif, source, base, catalog_path)
    export = tmp_path / "font-only-export.jsonl"
    local.export_untranslated(source, catalog, font_base, export)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    assert "u-start" not in {row["unit_id"] for row in rows}
    fill_rows(export, rows)
    output = tmp_path / "personal-from-font-base"
    report = local.import_personal(
        source, catalog, font_base, base, export, output, "personal-font-r1"
    )
    assert report["coverage"]["base_completed"] == 1
    assert report["coverage"]["base_changed"] == 0
    assert report["coverage"]["base_reviewed_unchanged"] == 1
    personal = local.read_json(output / "patch.json")
    assert personal["extras"] == font_base["extras"]
    assert {file["path"] for file in personal["files"]} == {"game/script.rpy"}
    result = install(output, source)
    assert result.returncode == 0, result.stdout + result.stderr
    result = install(output, source, "Uninstall")
    assert result.returncode == 0, result.stdout + result.stderr


def test_damaged_base_payload_is_rejected_before_personal_output(manual_project, tmp_path):
    source, base, catalog, manifest, _, _ = manual_project
    export, rows, _ = export_rows(manual_project, tmp_path)
    fill_rows(export, rows)
    (base / "payload/extras/game/fvn/font.bin").write_bytes(b"bad font")
    output = tmp_path / "refused-personal"
    with pytest.raises(ValueError, match="payload failed"):
        local.import_personal(source, catalog, manifest, base, export, output, "personal-r1")
    assert not output.exists()


def test_installed_backup_corruption_is_rejected_before_export(manual_project, tmp_path):
    source, base, catalog, manifest, _, _ = manual_project
    game = tmp_path / "game-copy"
    shutil.copytree(source, game)
    result = install(base, game)
    assert result.returncode == 0, result.stdout + result.stderr
    (game / ".fvn-backups/synthetic-ui-r1/original/game/screens.rpy").write_bytes(b"damaged backup")
    output = tmp_path / "refused-export.jsonl"
    with pytest.raises(ValueError, match="backup failed"):
        local.export_untranslated(game, catalog, manifest, output)
    assert not output.exists()


def test_bare_unicode_escape_and_physical_cr_follow_native_renpy_semantics():
    assert local.decode_content(r"before\uZ", "renpy", '"', "")[0] == "beforeZ"
    assert local.decode_content("a\rb", "renpy", '"', "")[0] == "a\rb"
    unit = {"codec": "renpy", "quote": '"', "prefix": ""}
    encoded = local.validate_target("a\rb", "甲\r乙", unit)
    assert local.decode_content(encoded, "renpy", '"', "")[0] == "甲\r乙"


def guarded_manual_base(project):
    source, base, _, manifest, catalog_path, ftif = project
    previous = local.digest((base / "patch.json").read_bytes())
    guarded = copy.deepcopy(manifest)
    guarded["runtime_guards"] = [
        {
            "path": relative,
            "source_size": (source / relative).stat().st_size,
            "source_sha256": local.digest((source / relative).read_bytes()),
        }
        for relative in ("renpy/vc_version.py", "Synthetic.exe")
    ]
    local.atomic_write(base / "patch.json", local.json_bytes(guarded))
    current = local.digest((base / "patch.json").read_bytes())
    (base / "install.ps1").write_text(
        (base / "install.ps1").read_text().replace(previous, current), encoding="ascii"
    )
    catalog = local.build_catalog(ftif, source, base, catalog_path)
    return source, base, catalog, guarded


@pytest.mark.parametrize("relative", ["renpy/vc_version.py", "Synthetic.exe"])
def test_local_export_refuses_matching_scripts_with_wrong_runtime(
    manual_project, tmp_path, relative
):
    source, _, catalog, manifest = guarded_manual_base(manual_project)
    (source / relative).write_bytes(b"different runtime version or platform")
    output = tmp_path / "refused-export.jsonl"
    with pytest.raises(ValueError, match="Runtime version/platform"):
        local.export_untranslated(source, catalog, manifest, output)
    assert not output.exists()


def test_personal_patch_and_catalog_keep_and_validate_runtime_guards(manual_project, tmp_path):
    source, base, catalog, manifest = guarded_manual_base(manual_project)
    export = tmp_path / "guarded-export.jsonl"
    local.export_untranslated(source, catalog, manifest, export)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    fill_rows(export, rows)
    output = tmp_path / "guarded-personal"
    local.import_personal(source, catalog, manifest, base, export, output, "guarded-personal-r1")
    assert local.read_json(output / "patch.json")["runtime_guards"] == manifest["runtime_guards"]
    assert (
        local.read_json(output / "source-catalog.json")["runtime_guards"]
        == manifest["runtime_guards"]
    )
    game = tmp_path / "game-copy"
    shutil.copytree(source, game)
    (game / "Synthetic.exe").write_bytes(b"another platform")
    before = snapshot(game)
    result = install(output, game)
    assert result.returncode != 0
    assert "Runtime version/platform mismatch" in result.stderr
    assert snapshot(game) == before
    (source / "Synthetic.exe").write_bytes(b"modified during editing")
    result = run_cli(
        base / SCRIPT.name, "validate", "--game-root", source, "--translations", export
    )
    assert result.returncode != 0 and "Runtime version/platform mismatch" in result.stderr
    with pytest.raises(ValueError, match="Runtime version/platform"):
        local.import_personal(
            source, catalog, manifest, base, export, tmp_path / "refused-personal", "next-r2"
        )
    assert not (tmp_path / "refused-personal").exists()


@pytest.mark.parametrize("install_initial", [False, True])
def test_apply_two_rounds_from_release_script_keeps_targets_then_rollback(
    manual_project, tmp_path, install_initial
):
    source, base, catalog, manifest, catalog_path, _ = manual_project
    game = tmp_path / "play"
    shutil.copytree(source, game)
    originals = snapshot(game)
    if install_initial:
        result = install(base, game)
        assert result.returncode == 0, result.stdout + result.stderr
    export = tmp_path / "manual.jsonl"
    local.export_untranslated(game, catalog, manifest, export)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    fill_rows(export, rows)
    first = copy.deepcopy(rows)
    for row in first:
        if row["unit_id"] != "u-hello":
            row["target_text"] = None
    export.write_text("\n".join(json.dumps(row) for row in first))
    command = ["apply", "--game-root", game, "--translations", export, "--powershell", pwsh()]
    result = run_cli(base / SCRIPT.name, *command)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["coverage"]["user_filled"] == 1
    first_content = (game / "game/script.rpy").read_bytes()
    assert "你好".encode() in first_content
    second = copy.deepcopy(rows)
    for row in second:
        if row["unit_id"] != "u-unknown":
            row["target_text"] = None  # Same export; null never erases earlier fill.
    export.write_text("\n".join(json.dumps(row) for row in second))
    result = run_cli(base / SCRIPT.name, *command)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["coverage"]["user_filled"] == 2
    second_content = (game / "game/script.rpy").read_bytes()
    assert "你好".encode() in second_content and "奇怪的转义".encode() in second_content
    before_repeat = snapshot(game)
    result = run_cli(base / SCRIPT.name, *command)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["already_current"] is True
    assert snapshot(game) == before_repeat
    remaining = tmp_path / "remaining.jsonl"
    result = run_cli(base / SCRIPT.name, "export", "--game-root", game, "--output", remaining)
    assert result.returncode == 0, result.stderr
    assert {json.loads(line)["unit_id"] for line in remaining.read_text().splitlines()} == {
        "u-quote",
        "u-null",
        "u-note",
    }
    current, patch, directory = local.active_context(game, catalog_path, base)
    assert current["base_origin_unit_ids"] == ["u-start"]
    assert set(current["manual_completed_unit_ids"]) == {"u-hello", "u-unknown"}
    assert patch["extras"] == manifest["extras"]
    for name in ("install.cmd", "uninstall.cmd"):
        assert '-GameRoot "%~dp0..\\.."' in (directory / name).read_text()
        assert b"\r\r\n" not in (directory / name).read_bytes()
    for extra in patch["extras"]:
        assert local.digest((directory / extra["payload_path"]).read_bytes()) == extra["sha256"]
    advanced = tmp_path / "advanced-package"
    local.import_personal(game, current, patch, directory, export, advanced, "advanced-export")
    assert '-GameRoot "%~dp0."' in (advanced / "uninstall.cmd").read_text()
    result = run_cli(base / SCRIPT.name, "rollback", "--game-root", game, "--powershell", pwsh())
    assert result.returncode == 0, result.stderr
    for relative, data in originals.items():
        assert (game / relative).read_bytes() == data
    assert not (game / "game/fvn/font.bin").exists()
    assert local.read_json(game / local.ACTIVE_FILE)["phase"] == "uninstalled"
    # Retained personal targets can be reapplied after a rollback.
    result = run_cli(base / SCRIPT.name, *command)
    assert result.returncode == 0, result.stderr
    assert (game / "game/script.rpy").read_bytes() == second_content


@pytest.mark.parametrize("failure", ["source", "tag", "runtime", "game-script"])
def test_apply_validation_failure_has_zero_game_writes(manual_project, tmp_path, failure):
    source, base, catalog, manifest = guarded_manual_base(manual_project)
    game = tmp_path / "play"
    shutil.copytree(source, game)
    result = install(base, game)
    assert result.returncode == 0, result.stdout + result.stderr
    export = tmp_path / "input.jsonl"
    local.export_untranslated(game, catalog, manifest, export)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    fill_rows(export, rows)
    if failure == "source":
        rows[0]["source_text"] += "edited"
    elif failure == "tag":
        rows[0]["target_text"] = rows[0]["target_text"].replace("{i}", "")
    elif failure == "runtime":
        (game / "Synthetic.exe").write_bytes(b"different platform")
    else:
        (game / "game/logic.rpy").write_bytes(b"changed script")
    export.write_text("\n".join(json.dumps(row) for row in rows))
    before = snapshot(game)
    result = run_cli(
        base / SCRIPT.name,
        "apply",
        "--game-root",
        game,
        "--translations",
        export,
        "--powershell",
        pwsh(),
    )
    assert result.returncode != 0
    assert snapshot(game) == before


@pytest.mark.parametrize("failure_stage", ["new-installed", "old-uninstalled", "old-partial"])
def test_apply_real_installer_failure_restores_preceding_personal_patch(
    manual_project, tmp_path, monkeypatch, failure_stage
):
    source, base, catalog, manifest, catalog_path, _ = manual_project
    game = tmp_path / "play"
    shutil.copytree(source, game)
    export = tmp_path / "input.jsonl"
    local.export_untranslated(game, catalog, manifest, export)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    fill_rows(export, rows)
    rows = [row for row in rows if row["unit_id"] == "u-hello"]
    export.write_text(json.dumps(rows[0]))
    local.apply_personal(
        game, catalog, manifest, base, export, patch_id="first-personal", powershell=pwsh()
    )
    before = {p: b for p, b in snapshot(game).items() if p.startswith("game/")}
    pointer = (game / local.ACTIVE_FILE).read_bytes()
    current, patch, directory = local.active_context(game, catalog_path, base)
    rows[0]["target_text"] = "第二稿 [name]，{i}朋友{/i}。\n下一行。"
    export.write_text(json.dumps(rows[0]))
    real_installer = local.run_installer

    injected = False

    def fail_after_real_install(base_root, game_root, action, executable):
        nonlocal injected
        if (
            failure_stage == "old-partial"
            and not injected
            and base_root.name == "first-personal"
            and action == "Uninstall"
        ):
            injected = True
            backup = game_root / ".fvn-backups/first-personal/original/game/script.rpy"
            (game_root / "game/script.rpy").write_bytes(backup.read_bytes())
            raise RuntimeError("synthetic interrupted partial uninstall")
        real_installer(base_root, game_root, action, executable)
        if (
            failure_stage == "new-installed"
            and base_root.name == "failed-personal"
            and action == "Install"
        ):
            raise RuntimeError("synthetic post-install failure")
        if (
            failure_stage == "old-uninstalled"
            and base_root.name == "first-personal"
            and action == "Uninstall"
        ):
            raise RuntimeError("synthetic post-uninstall failure")

    monkeypatch.setattr(local, "run_installer", fail_after_real_install)
    with pytest.raises(RuntimeError, match="failed-previous-state-restored"):
        local.apply_personal(
            game, current, patch, directory, export, patch_id="failed-personal", powershell=pwsh()
        )
    assert {p: b for p, b in snapshot(game).items() if p.startswith("game/")} == before
    assert (game / local.ACTIVE_FILE).read_bytes() == pointer
    journal = local.read_json(game / ".fvn-personal/failed-personal/operation.json")
    assert journal["phase"] == "failed-previous-state-restored"
    assert (game / journal["previous_backup_archive"]).is_dir()
    assert local.installation_phase(game, current, patch) == "installed"


def test_history_patch_id_does_not_collide_with_archive_namespace(manual_project, tmp_path):
    source, base, catalog, manifest, catalog_path, _ = manual_project
    export, rows, _ = export_rows(manual_project, tmp_path)
    fill_rows(export, rows)
    local.apply_personal(
        source, catalog, manifest, base, export, patch_id="history", powershell=pwsh()
    )
    current, patch, directory = local.active_context(source, catalog_path, base)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    rows[0]["target_text"] = "再译 [name]，{i}朋友{/i}。\n下一行。"
    export.write_text("\n".join(json.dumps(row) for row in rows))
    archive_store = source / ".fvn-backup-history"
    archive_store.write_bytes(b"synthetic archive path collision")
    before = snapshot(source)
    with pytest.raises(ValueError, match="archive location"):
        local.apply_personal(
            source, current, patch, directory, export, patch_id="history-next", powershell=pwsh()
        )
    assert snapshot(source) == before
    archive_store.unlink()
    local.apply_personal(
        source, current, patch, directory, export, patch_id="history-next", powershell=pwsh()
    )
    archives = list((source / ".fvn-backup-history").glob("history-*"))
    assert len(archives) == 1 and (archives[0] / "state.json").is_file()
    current, patch, directory = local.active_context(source, catalog_path, base)
    assert patch["patch_id"] == "history-next"
    assert local.installation_phase(source, current, patch) == "installed"


@pytest.mark.parametrize("damage", [None, "script", "extra", "backup", "runtime"])
def test_rollback_accepts_only_known_hash_partial_restore_and_keeps_runtime_gate(
    manual_project, tmp_path, damage
):
    source, base, catalog, manifest = guarded_manual_base(manual_project)
    original = snapshot(source)
    export = tmp_path / "input.jsonl"
    local.export_untranslated(source, catalog, manifest, export)
    rows = [json.loads(line) for line in export.read_text().splitlines()]
    fill_rows(export, rows)
    local.apply_personal(
        source, catalog, manifest, base, export, patch_id="partial-personal", powershell=pwsh()
    )
    current, patch, directory = local.active_context(source, base / "source-catalog.json", base)
    backup = source / ".fvn-backups/partial-personal/original/game/script.rpy"
    (source / "game/script.rpy").write_bytes(backup.read_bytes())
    # A previous restore may have already removed one known extra.
    (source / "game/fvn/font.bin").unlink()
    if damage == "script":
        (source / "game/screens.rpy").write_bytes(b"unknown third-state script")
    elif damage == "extra":
        (source / "game/fvn/runtime.rpy").write_bytes(b"unknown extra change")
    elif damage == "backup":
        backup.write_bytes(b"damaged backup")
    elif damage == "runtime":
        (source / "Synthetic.exe").write_bytes(b"different platform")
    before = snapshot(source)
    if damage is not None:
        with pytest.raises((ValueError, RuntimeError)):
            local.rollback_current(source, current, patch, directory, powershell=pwsh())
        assert snapshot(source) == before
    else:
        result = local.rollback_current(source, current, patch, directory, powershell=pwsh())
        assert result["restored"] is True
        for relative, data in original.items():
            assert (source / relative).read_bytes() == data
        assert not (source / "game/fvn/runtime.rpy").exists()
