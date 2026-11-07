#!/usr/bin/env python3
"""Local manual translation exchange for a version-bound Ren'Py byte patch.

Python 3.11+ standard library only. No network access or translation service.
Only the explicit apply/rollback commands modify game files through the bound
PowerShell installer. Original text is read from the player's own files.
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import annotations

import argparse
import ast
import base64
import copy
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import uuid
import warnings
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath

CATALOG_SCHEMA = "fvn-local-renpy-catalog/v1"
ROW_SCHEMA = "fvn-local-translation/v1"
PATCH_SCHEMA = "fvn-renpy-byte-delta/v1"
RENPY_KINDS = {"say", "say_explicit", "explicit_display_name", "extend", "menu"}
PYTHON_KINDS = {"function", "assignment", "screen_text", "screen_textbutton", "screen_label"}
RESERVED = re.compile(r"^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)", re.I)
HASH = re.compile(r"^sha256:[0-9a-f]{64}$")
ACTIVE_FILE = ".fvn-active-translation.json"
ACTIVE_SCHEMA = "fvn-local-active/v1"
PRINTF = re.compile(
    r"%(?P<mapping>\([^)]+\))?(?P<flags>[#0 +\-]*)"
    r"(?P<width>\d+|\*)?(?P<precision>\.(?:\d+|\*))?[diouxXeEfFgGcrs%]"
)


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def read_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".local-translation-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def relative_path(value: str, *, game: bool = False) -> str:
    if (
        not isinstance(value, str)
        or not value
        or (game and not value.startswith("game/"))
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).drive
        or any(character in value for character in '\\<>:"|?*')
        or any(ord(character) < 32 for character in value)
        or any(
            part in {"", ".", ".."} or part.endswith((".", " ")) or RESERVED.match(part)
            for part in value.split("/")
        )
    ):
        raise ValueError("Unsafe relative path in metadata")
    return value


def inside(root: Path, relative: str, *, game: bool = False) -> Path:
    relative_path(relative, game=game)
    root = root.resolve()
    path = root / relative
    for parent in [path, *path.parents]:
        if parent == root:
            break
        try:
            info = parent.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ValueError(f"Linked paths are not supported: {relative}")
    resolved = path.resolve()
    if root not in resolved.parents:
        raise ValueError("Path escapes its metadata root")
    return resolved


def patch_identifier(value: str) -> str:
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}", value)
        or value.endswith(".")
        or RESERVED.match(value)
    ):
        raise ValueError("patch-id requires 1-80 ASCII letters, digits, dots, _ or -")
    return value


def decode_content(raw: str, codec: str, quote: str, prefix: str) -> tuple[str, list[str]]:
    """Decode literal content without executing game code.

    Ren'Py 8.5.2 Lexer.string normalizes whitespace *before* expanding its
    small escape language. Python expressions use Python literal semantics.
    """
    if quote not in {'"', "'", '"""', "'''"}:
        raise ValueError("Unsupported quote delimiter")
    if codec == "python":
        if prefix.lower() not in {"", "u", "r", "ur", "ru"}:
            raise ValueError("Only plain Unicode Python string literals are supported")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", SyntaxWarning)
            warnings.simplefilter("ignore", DeprecationWarning)
            value = ast.literal_eval(prefix + quote + raw + quote)
        if not isinstance(value, str):
            raise ValueError("Visible literal did not decode to text")
        return value, []
    if codec != "renpy" or len(quote) != 1 or prefix.lower() not in {"", "r"}:
        raise ValueError("Unsupported Ren'Py literal codec")
    raw = raw.replace("\r\n", "\n")
    if prefix.lower() == "r":
        return raw, []
    raw = re.sub(r"[ \n]+", " ", raw)
    notices = []

    def dequote(match):
        character = match.group(1)
        if character == "{":
            return "{{"
        if character == "[":
            return "[["
        if character == "%":
            return "%%"
        if character == "n":
            return "\n"
        if match.group(2):
            return chr(int(match.group(2), 16))
        if character == "u":
            notices.append("UNKNOWN_RENPY_ESCAPE:" + repr("\\u"))
            # SDK Lexer.string's bare-u branch returns None, which re.sub
            # treats as an empty replacement rather than the literal 'u'.
            return ""
        if character not in {'"', "'", "`", "\\"}:
            notices.append("UNKNOWN_RENPY_ESCAPE:" + repr("\\" + character))
        return character

    value = re.sub(r"\\(u([0-9a-fA-F]{1,4})|.)", dequote, raw)
    return value, notices


def encode_content(value: str, codec: str, quote: str, prefix: str) -> str:
    if "r" in prefix.lower():
        rendered = value
        if codec == "renpy" and not re.fullmatch(
            r"(?:[^\\" + re.escape(quote) + r"]|\\.)*", rendered, re.S
        ):
            raise ValueError("Raw Ren'Py target contains an unescaped delimiter or final backslash")
    else:
        output = []
        for character in value:
            if character == "\\":
                output.append("\\\\")
            elif character == quote[0]:
                output.append("\\" + character)
            elif character == "\n":
                output.append("\\n")
            elif codec == "renpy" and character in {" ", "\t", "\r"}:
                # \t is not a tab in Ren'Py's Say lexer; explicit Unicode also
                # keeps intentional spaces from being collapsed a second time.
                output.append(f"\\u{ord(character):04x}")
            elif character == "\r":
                output.append("\\r")
            elif character == "\t":
                output.append("\\t")
            elif ord(character) < 32:
                output.append(f"\\u{ord(character):04x}")
            else:
                output.append(character)
        rendered = "".join(output)
    decoded, _ = decode_content(rendered, codec, quote, prefix)
    if decoded != value:
        raise ValueError("Target cannot round-trip through this literal's original codec")
    return rendered


def balanced_tokens(text: str, opening: str, closing: str) -> tuple[list[str], int, int]:
    result = []
    index = escaped = unmatched = 0
    while index < len(text):
        if text.startswith(opening * 2, index):
            escaped += 1
            index += 2
            continue
        if text[index] != opening:
            index += 1
            continue
        end, depth = index + 1, 1
        while end < len(text) and depth:
            if text[end] == opening:
                depth += 1
            elif text[end] == closing:
                depth -= 1
            end += 1
        if depth:
            unmatched += 1
            index += 1
        else:
            result.append(text[index:end])
            index = end
    return result, escaped, unmatched


def printf_tokens(text: str) -> list[str]:
    return [
        match.group()
        for match in PRINTF.finditer(text)
        if not (
            " " in (match.group("flags") or "")
            and not any(match.group(key) for key in ("mapping", "width", "precision"))
        )
    ]


def validate_target(source: str, target: str, unit: dict) -> str:
    if unit.get("locked") and source != target:
        raise ValueError("This title, resource binding or license literal must remain unchanged")
    if not target.strip() and source.strip():
        raise ValueError("Target text must not be empty; use null to leave it untranslated")
    for opening, closing in (("{", "}"), ("[", "]")):
        if balanced_tokens(source, opening, closing) != balanced_tokens(target, opening, closing):
            raise ValueError("Text tags, interpolations or literal delimiter escapes changed")
    if printf_tokens(source) != printf_tokens(target):
        raise ValueError("Printf placeholders changed")
    for character, name in (
        ("\n", "newline"),
        ("\r", "carriage return"),
        ("\t", "tab"),
        ("\\", "backslash"),
    ):
        if source.count(character) != target.count(character):
            raise ValueError(f"Semantic {name} count changed")
    return encode_content(target, unit["codec"], unit["quote"], unit["prefix"])


def build_catalog(units_path: Path, source_root: Path, base_root: Path, output: Path) -> dict:
    """Author-time operation. Export only positions/hashes, never original text."""
    base = read_json(base_root / "patch.json")
    if base.get("schema") != PATCH_SCHEMA:
        raise ValueError("Expected a version-bound Ren'Py byte delta base patch")
    verify_runtime_guards(source_root, base.get("runtime_guards", []))
    guards = {row["path"]: row for row in base["source_guards"]}
    if len(guards) != len(base["source_guards"]):
        raise ValueError("Duplicate source guards")
    sources = {}
    for relative, guard in guards.items():
        data = inside(source_root, relative, game=True).read_bytes()
        if digest(data) != guard["source_sha256"] or len(data) != guard["source_size"]:
            raise ValueError(f"Source guard failed: {relative}")
        sources[relative] = data
    grouped = defaultdict(list)
    ids = set()
    for line in units_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        unit = json.loads(line)
        if unit["unit_id"] in ids:
            raise ValueError("Duplicate FTIF unit ID")
        ids.add(unit["unit_id"])
        relative = unit["origin"]["path"]
        if (
            relative not in guards
            or unit["origin"]["file_fingerprint"] != guards[relative]["source_sha256"]
        ):
            raise ValueError("FTIF origin differs from the guarded source")
        grouped[relative].append(unit)
    result = []
    for relative, units in grouped.items():
        data = sources[relative]
        text = data.decode("utf-8-sig")
        positions = sorted(
            {
                int(unit["adapter_data"][key])
                for unit in units
                for key in ("content_start", "content_end")
            }
        )
        byte_positions = {}
        previous, offset = 0, 3 if data.startswith(b"\xef\xbb\xbf") else 0
        for position in positions:
            if not 0 <= position <= len(text):
                raise ValueError("FTIF character interval is out of bounds")
            offset += len(text[previous:position].encode("utf-8"))
            byte_positions[position] = offset
            previous = position
        for unit in units:
            adapter = unit["adapter_data"]
            start, end = int(adapter["content_start"]), int(adapter["content_end"])
            raw = text[start:end]
            if start > end or raw != adapter["source_raw_content"]:
                raise ValueError("FTIF raw literal interval changed")
            kind = adapter["node_kind"]
            codec = "renpy" if kind in RENPY_KINDS else "python" if kind in PYTHON_KINDS else None
            if codec is None:
                raise ValueError(f"Unsupported literal node kind: {kind}")
            decoded, notices = decode_content(
                raw, codec, adapter["quote"], adapter.get("string_prefix", "")
            )
            result.append(
                {
                    "unit_id": unit["unit_id"],
                    "sequence": unit["sequence"],
                    "path": relative,
                    "type": unit["type"],
                    "speaker": unit.get("speaker"),
                    "line": unit["origin"]["line"],
                    "start": byte_positions[start],
                    "end": byte_positions[end],
                    "raw_sha256": digest(raw.encode("utf-8")),
                    "source_fingerprint": digest(decoded.encode("utf-8")),
                    "ftif_source_fingerprint": unit["source_fingerprint"],
                    "quote": adapter["quote"],
                    "prefix": adapter.get("string_prefix", ""),
                    "node_kind": kind,
                    "codec": codec,
                    "locked": bool(unit.get("context", {}).get("preserve_original"))
                    or unit.get("context", {}).get("player_visible") is False,
                    "decode_warning_count": len(notices),
                }
            )
    if not result:
        raise ValueError("No catalog units")
    changed = {row["unit_id"] for file in base["files"] for row in file["replacements"]}
    provided = set(base.get("selected_unit_ids", [])) | changed
    if provided - ids:
        raise ValueError("Base patch contains a unit absent from the catalog")
    catalog = {
        "schema": CATALOG_SCHEMA,
        "engine_codec": "RenPy 8.5.2 / Python literals",
        "project": base["project"],
        "base_patch_sha256": digest((base_root / "patch.json").read_bytes()),
        "base_patch_id": base["patch_id"],
        "base_origin_unit_ids": sorted(provided),
        "manual_completed_unit_ids": [],
        "source_guards": base["source_guards"],
        "runtime_guards": base.get("runtime_guards", []),
        "units": sorted(result, key=lambda unit: unit["sequence"]),
    }
    atomic_write(output, json_bytes(catalog))
    return catalog


def load_context(catalog_path: Path, base_root: Path) -> tuple[dict, dict]:
    catalog, base = read_json(catalog_path), read_json(base_root / "patch.json")
    if catalog.get("schema") != CATALOG_SCHEMA or base.get("schema") != PATCH_SCHEMA:
        raise ValueError("Unsupported catalog or base patch schema")
    if (
        digest((base_root / "patch.json").read_bytes()) != catalog["base_patch_sha256"]
        or base["patch_id"] != catalog["base_patch_id"]
    ):
        raise ValueError("Catalog does not match this base installer")
    if catalog["source_guards"] != base["source_guards"]:
        raise ValueError("Catalog source guards differ from the base patch")
    if catalog.get("runtime_guards", []) != base.get("runtime_guards", []):
        raise ValueError("Catalog runtime guards differ from the base patch")
    ids = {unit["unit_id"] for unit in catalog["units"]}
    if len(ids) != len(catalog["units"]):
        raise ValueError("Duplicate catalog unit ID")
    for field in ("base_origin_unit_ids", "manual_completed_unit_ids"):
        values = catalog[field]
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            raise ValueError("Invalid completed unit inventory")
        if len(values) != len(set(values)) or set(values) - ids:
            raise ValueError("Unknown or duplicate completed unit ID")
    guards = {guard["path"]: guard for guard in catalog["source_guards"]}
    for unit in catalog["units"]:
        if (
            unit["path"] not in guards
            or type(unit["start"]) is not int
            or type(unit["end"]) is not int
            or not 0 <= unit["start"] <= unit["end"] <= guards[unit["path"]]["source_size"]
        ):
            raise ValueError("Invalid catalog interval")
        if not HASH.fullmatch(unit["raw_sha256"]) or not HASH.fullmatch(unit["source_fingerprint"]):
            raise ValueError("Invalid catalog fingerprint")
    patch_identifier(base["patch_id"])
    return catalog, base


def verify_runtime_guards(game_root: Path, guards: list[dict]) -> None:
    """Read-only engine/platform checks, also applied when source scripts match."""
    names = set()
    for guard in guards:
        relative = relative_path(guard["path"])
        if relative.casefold() in names:
            raise ValueError("Duplicate runtime guard path")
        names.add(relative.casefold())
        path = inside(game_root, relative)
        if not path.is_file() or not stat.S_ISREG(path.stat().st_mode):
            raise ValueError(f"Runtime version/platform file is missing: {relative}")
        data = path.read_bytes()
        if len(data) != guard["source_size"] or digest(data) != guard["source_sha256"]:
            raise ValueError(f"Runtime version/platform mismatch: {relative}")


def read_originals(game_root: Path, catalog: dict, base: dict) -> dict[str, bytes]:
    """Verify every guard; recover guarded originals only behind matching targets."""
    game_root = game_root.resolve()
    if not (game_root / "game").is_dir():
        raise ValueError("Game root must contain the original game/ directory")
    verify_runtime_guards(game_root, catalog.get("runtime_guards", []))
    changed = {row["path"]: row for row in base["files"]}
    state = None
    result = {}
    for guard in catalog["source_guards"]:
        relative = guard["path"]
        path = inside(game_root, relative, game=True)
        data = path.read_bytes()
        if digest(data) != guard["source_sha256"]:
            file = changed.get(relative)
            if (
                file is None
                or digest(data) != file["target_sha256"]
                or file["source_sha256"] != guard["source_sha256"]
            ):
                raise ValueError(f"Wrong version or modified game script: {relative}")
            if state is None:
                state_path = inside(game_root, ".fvn-backups/" + base["patch_id"] + "/state.json")
                state = read_json(state_path)
                if (
                    state.get("manifest_sha256") != catalog["base_patch_sha256"]
                    or state.get("patch_id") != base["patch_id"]
                    or state.get("phase") not in {"installed", "prepared"}
                    or os.path.normcase(os.path.abspath(state.get("game_root", "")))
                    != os.path.normcase(str(game_root))
                ):
                    raise ValueError(
                        "Installed patch backup state does not match this game and catalog"
                    )
            data = inside(
                game_root, ".fvn-backups/" + base["patch_id"] + "/original/" + relative
            ).read_bytes()
        if digest(data) != guard["source_sha256"] or len(data) != guard["source_size"]:
            raise ValueError(f"Original source or verified backup failed its guard: {relative}")
        result[relative] = data
    return result


def local_text(unit: dict, originals: dict[str, bytes]) -> tuple[str, list[str]]:
    raw_bytes = originals[unit["path"]][unit["start"] : unit["end"]]
    if digest(raw_bytes) != unit["raw_sha256"]:
        raise ValueError(f"Literal location fingerprint changed: {unit['unit_id']}")
    value, notices = decode_content(
        raw_bytes.decode("utf-8"), unit["codec"], unit["quote"], unit["prefix"]
    )
    if digest(value.encode("utf-8")) != unit["source_fingerprint"]:
        raise ValueError(f"Decoded original fingerprint changed: {unit['unit_id']}")
    return value, notices


def replacements_by_id(base: dict) -> dict[str, tuple[str, dict]]:
    result = {}
    for file in base["files"]:
        for row in file["replacements"]:
            if row["unit_id"] in result:
                raise ValueError("Duplicate base replacement unit ID")
            result[row["unit_id"]] = (file["path"], copy.deepcopy(row))
    return result


def export_untranslated(
    game_root: Path,
    catalog: dict,
    base: dict,
    output: Path,
    *,
    force: bool = False,
    paths: list[str] | None = None,
) -> dict:
    if output.suffix.lower() != ".jsonl":
        raise ValueError("Export output must have a .jsonl extension")
    if game_root.resolve() / "game" in output.resolve().parents:
        raise ValueError("Export outside the game's game/ assets directory")
    if output.exists() and not force:
        raise ValueError("Output already exists; choose a new file or explicitly use --force")
    originals = read_originals(game_root, catalog, base)
    if paths and set(paths) - originals.keys():
        raise ValueError("Unknown source path filter")
    completed = (
        set(replacements_by_id(base))
        | set(catalog["base_origin_unit_ids"])
        | set(catalog["manual_completed_unit_ids"])
    )
    rows = []
    warning_count = 0
    for unit in catalog["units"]:
        if unit["unit_id"] in completed or (paths and unit["path"] not in paths):
            continue
        text, notices = local_text(unit, originals)
        warning_count += len(notices)
        rows.append(
            json.dumps(
                {
                    "schema": ROW_SCHEMA,
                    "unit_id": unit["unit_id"],
                    "source_fingerprint": unit["source_fingerprint"],
                    "path": unit["path"],
                    "line": unit["line"],
                    "type": unit["type"],
                    "speaker": unit["speaker"],
                    "source_text": text,
                    "target_text": None,
                    "locked": unit["locked"],
                    "warnings": notices,
                },
                ensure_ascii=False,
            )
        )
    atomic_write(output, ("\n".join(rows) + ("\n" if rows else "")).encode("utf-8"))
    return {"exported": len(rows), "decode_warnings": warning_count, "output": str(output)}


def read_translations(
    path: Path, catalog: dict, originals: dict[str, bytes]
) -> tuple[dict[str, str], dict]:
    units = {unit["unit_id"]: unit for unit in catalog["units"]}
    seen, translated = set(), {}
    null_count = warning_count = 0
    for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or row.get("schema") != ROW_SCHEMA:
            raise ValueError(f"Invalid translation row schema on line {number}")
        unit_id = row.get("unit_id")
        if not isinstance(unit_id, str) or unit_id not in units or unit_id in seen:
            raise ValueError(f"Unknown or duplicate unit ID on line {number}")
        seen.add(unit_id)
        unit = units[unit_id]
        original, notices = local_text(unit, originals)
        if (
            row.get("source_fingerprint") != unit["source_fingerprint"]
            or row.get("source_text") != original
        ):
            raise ValueError(f"Original text or its fingerprint was edited on line {number}")
        if "target_text" not in row:
            raise ValueError(f"target_text is missing on line {number}")
        target = row["target_text"]
        if target is None:
            null_count += 1
            continue
        if not isinstance(target, str):
            raise ValueError(f"target_text must be text or null on line {number}")
        try:
            validate_target(original, target, unit)
        except (ValueError, SyntaxError) as error:
            raise ValueError(f"Invalid target on line {number}, {unit_id}: {error}") from error
        translated[unit_id] = target
        warning_count += len(notices)
    return translated, {
        "rows": len(seen),
        "filled": len(translated),
        "null": null_count,
        "decode_warnings": warning_count,
    }


def apply_replacements(source: bytes, replacements: list[dict]) -> bytes:
    output, cursor = bytearray(), 0
    for row in replacements:
        start, end = row["start"], row["end"]
        if (
            type(start) is not int
            or type(end) is not int
            or not cursor <= start <= end <= len(source)
        ):
            raise ValueError("Overlapping or invalid replacement byte interval")
        output.extend(source[cursor:start])
        output.extend(base64.b64decode(row["replacement_base64"], validate=True))
        cursor = end
    output.extend(source[cursor:])
    return bytes(output)


def coverage(catalog: dict, replacements: dict, manual: set[str]) -> dict:
    provided = set(catalog["base_origin_unit_ids"]) - manual
    provided_changed = provided.intersection(replacements)
    manual_changed = manual.intersection(replacements)
    return {
        "total": len(catalog["units"]),
        "base_completed": len(provided),
        "base_changed": len(provided_changed),
        "base_reviewed_unchanged": len(provided - provided_changed),
        "user_filled": len(manual),
        "user_changed": len(manual_changed),
        "user_reviewed_unchanged": len(manual - manual_changed),
        "untranslated": len(catalog["units"]) - len(provided | manual),
    }


def import_personal(
    game_root: Path,
    catalog: dict,
    base: dict,
    base_root: Path,
    translations_path: Path,
    output: Path,
    patch_id: str,
    *,
    managed: bool = False,
    allow_empty: bool = False,
) -> dict:
    patch_identifier(patch_id)
    if patch_id == base["patch_id"]:
        raise ValueError("Use a new patch-id so earlier backups remain distinct")
    output, game_root, base_root = output.resolve(), game_root.resolve(), base_root.resolve()
    if output.exists():
        raise ValueError("Personal patch output already exists; choose a fresh directory")
    if managed:
        if output != inside(game_root, ".fvn-personal/" + patch_id):
            raise ValueError("Managed output must be a new personal directory within the game root")
        store = inside(game_root, ".fvn-personal")
        if store.exists() and any(
            child.name.casefold() == patch_id.casefold() for child in store.iterdir()
        ):
            raise ValueError("Personal patch path already exists (case-insensitive check)")
    elif any(
        output == root or root in output.parents or output in root.parents
        for root in (game_root, base_root)
    ):
        raise ValueError("Output must be separate from the game and base installer directories")
    originals = read_originals(game_root, catalog, base)
    translated, validation = read_translations(translations_path, catalog, originals)
    if not translated and not allow_empty:
        raise ValueError(
            "No target_text entries have been filled; null entries remain untranslated"
        )
    unit_map = {unit["unit_id"]: unit for unit in catalog["units"]}
    replacements = replacements_by_id(base)
    for unit_id, target in translated.items():
        unit = unit_map[unit_id]
        original, _ = local_text(unit, originals)
        if target == original:
            replacements.pop(unit_id, None)
            continue
        encoded = validate_target(original, target, unit).encode("utf-8")
        replacements[unit_id] = (
            unit["path"],
            {
                "unit_id": unit_id,
                "start": unit["start"],
                "end": unit["end"],
                "replacement_base64": base64.b64encode(encoded).decode("ascii"),
            },
        )
    grouped = defaultdict(list)
    for unit_id, (relative, row) in replacements.items():
        unit = unit_map.get(unit_id)
        if (
            unit is None
            or relative != unit["path"]
            or row["start"] != unit["start"]
            or row["end"] != unit["end"]
        ):
            raise ValueError("Base replacement differs from catalog byte locations")
        grouped[relative].append(row)
    guards = {row["path"]: row for row in catalog["source_guards"]}
    files = []
    for relative, rows in sorted(grouped.items()):
        rows.sort(key=lambda row: row["start"])
        target_bytes = apply_replacements(originals[relative], rows)
        files.append(
            {
                "path": relative,
                "source_sha256": guards[relative]["source_sha256"],
                "source_size": len(originals[relative]),
                "target_sha256": digest(target_bytes),
                "target_size": len(target_bytes),
                "replacements": rows,
            }
        )
    manual = set(catalog["manual_completed_unit_ids"]) | set(translated)
    summary = coverage(catalog, replacements, manual)
    personal = copy.deepcopy(base)
    personal.update(
        patch_id=patch_id,
        files=files,
        coverage=summary,
        selected_unit_ids=sorted(set(catalog["base_origin_unit_ids"]) | manual),
        validation={
            "local_manual_rows": validation,
            "target_only": True,
            "source_guards_verified": len(guards),
        },
    )
    # Copy only explicit extras after checking their payload hashes. Never copy
    # game files, exports, temporary staging or the user's input JSONL.
    payloads = []
    for extra in base["extras"]:
        relative_path(extra["path"], game=True)
        path = inside(base_root, extra["payload_path"])
        data = path.read_bytes()
        if digest(data) != extra["sha256"] or len(data) != extra["size"]:
            raise ValueError(f"Base extra payload failed verification: {extra['path']}")
        payloads.append((extra["payload_path"], data))
    installer = (base_root / "install.ps1").read_text(encoding="ascii")
    pattern = r"\$ExpectedManifestHash = 'sha256:[0-9a-f]{64}'"
    if re.findall(pattern, installer) != [
        "$ExpectedManifestHash = '" + catalog["base_patch_sha256"] + "'"
    ]:
        raise ValueError("Base installer does not bind the expected manifest")
    manifest_bytes = json_bytes(personal)
    installer = re.sub(
        pattern, "$ExpectedManifestHash = '" + digest(manifest_bytes) + "'", installer
    )
    updated_catalog = copy.deepcopy(catalog)
    updated_catalog.update(
        base_patch_id=patch_id,
        base_patch_sha256=digest(manifest_bytes),
        manual_completed_unit_ids=sorted(manual),
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".personal-patch-", dir=output.parent) as temporary:
        directory = Path(temporary) / "patch"
        directory.mkdir()
        atomic_write(directory / "patch.json", manifest_bytes)
        atomic_write(
            directory / "install.ps1",
            installer.replace("\r\n", "\n").replace("\n", "\r\n").encode("ascii"),
        )
        for name in ("install.cmd", "uninstall.cmd"):
            # Advanced import packages are copied beside the EXE. Managed apply
            # packages stay two directories below it; make their recovery CMDs
            # usable in place without changing the frozen installer template.
            command = (base_root / name).read_text(encoding="ascii")
            command = command.replace('-GameRoot "%~dp0..\\.."', '-GameRoot "%~dp0."')
            if managed:
                command = command.replace('-GameRoot "%~dp0."', '-GameRoot "%~dp0..\\.."')
            atomic_write(directory / name, command.replace("\n", "\r\n").encode("ascii"))
        for relative, data in payloads:
            atomic_write(inside(directory, relative), data)
        atomic_write(directory / "source-catalog.json", json_bytes(updated_catalog))
        shutil.copyfile(Path(__file__), directory / "local_renpy_translation.py")
        workflow = (
            "本目录由 apply 自动管理，固定保留在游戏根目录的 `.fvn-personal/补丁ID`。"
            "不要把本目录复制覆盖发行补丁。这里的 install.cmd/uninstall.cmd "
            "已定位到上两级游戏目录，"
            "可在原位置用于恢复操作。日常使用发行包的 apply/rollback 入口即可。\n\n"
            if managed
            else "1. 退出游戏。若已安装基础汉化补丁或较早个人补丁，"
            "先使用那个版本的 uninstall.cmd 回退。\n"
            "2. 保留旧备份，将本目录全部内容解压/复制到官方原版 EXE 同级目录，"
            "再运行 install.cmd。\n"
            "3. 回退使用本版本 uninstall.cmd；原脚本和编译文件备份在 .fvn-backups/补丁ID。\n\n"
        )
        notes = (
            "# 本地手工译文个人补丁\n\n"
            "本目录由你的本地文件和自行填写的 target_text 生成，未调用翻译服务，未修改游戏。\n\n"
            f"基础补丁已完成 {summary['base_completed']} 单元，"
            f"其中改变文字 {summary['base_changed']}、"
            f"审查后保留原文 {summary['base_reviewed_unchanged']}；"
            f"用户已填写 {summary['user_filled']}，"
            f"其中改变文字 {summary['user_changed']}、"
            f"保留原文 {summary['user_reviewed_unchanged']}；"
            f"尚未填写 {summary['untranslated']} / {summary['total']}。"
            "这些数字不代表全作已汉化。\n\n"
            + workflow
            + "本补丁只包含目标文字差量、哈希元数据和必要附件，未附原剧情脚本或导出的原文 JSONL。"
            "保留自己的译文 JSONL 供继续编辑。下一次可用本目录的工具/catalog 继续导出和导入，"
            "并为新个人补丁选择新的 patch-id。也可使用 apply 自动校验、切换和安装；"
            "rollback 会回到官方原版，并保留个人译文包及备份。\n\n"
            "Windows PowerShell 5.1 安装器；该本地编辑工具需 Python 3.11+。"
            "先用 validate 检查格式、源指纹、标签、插值和语义换行；游戏内实际显示仍需自行检查。\n"
            "\n日常补译可继续使用发行包中的导出/回写入口；工具会自动识别游戏根目录中的"
            "活动个人包，不必手动卸载再安装。直接使用 Python 时：\n\n"
            "- `local_renpy_translation.py export --game-root 游戏目录 --output 未译.jsonl`\n"
            "- `local_renpy_translation.py apply --game-root 游戏目录 --translations 未译.jsonl`\n"
            "- `local_renpy_translation.py rollback --game-root 游戏目录`\n\n"
            "apply 会先校验全部输入，保留既有汉化和已补译内容；null 不会抹掉以前的译文。"
            "个人包保留在 `.fvn-personal/补丁ID`，当前备份保留在 `.fvn-backups`，"
            "归档备份保留在 `.fvn-backup-history`。"
            "回退仅恢复官方文件，不删除这些本地记录。\n"
            "若操作中断或报告恢复失败，保留 operation.json、包和备份，"
            "按报告中的个人包运行 uninstall.cmd 恢复；不要自行覆盖或删除备份。"
            "残留 `.fvn-local-operation.lock` 需确认此前进程已结束后再移到游戏目录外归档。\n"
        )
        atomic_write(directory / "README.md", notes.encode("utf-8"))
        os.replace(directory, output)
    return {"output": str(output), "coverage": summary, "validation": validation}


def context_anchor(catalog: dict) -> str:
    """Bind managed successors to the same release, locations and original IDs."""
    return digest(
        json_bytes(
            {
                key: catalog.get(key, [])
                for key in (
                    "project",
                    "source_guards",
                    "runtime_guards",
                    "units",
                    "base_origin_unit_ids",
                )
            }
        )
    )


def active_context(game_root: Path, catalog_path: Path, base_root: Path) -> tuple[dict, dict, Path]:
    catalog, base = load_context(catalog_path, base_root)
    pointer = inside(game_root, ACTIVE_FILE)
    if not pointer.exists():
        return catalog, base, base_root.resolve()
    active = read_json(pointer)
    if active.get("schema") != ACTIVE_SCHEMA or active.get("phase") not in {
        "installed",
        "uninstalled",
    }:
        raise ValueError("Invalid active translation pointer; preserve it for recovery")
    patch_id = patch_identifier(active["patch_id"])
    if active["patch_path"] != ".fvn-personal/" + patch_id:
        raise ValueError("Active translation pointer has an unsafe package location")
    directory = inside(game_root, active["patch_path"])
    if (
        digest(inside(directory, "patch.json").read_bytes()) != active["manifest_sha256"]
        or digest(inside(directory, "source-catalog.json").read_bytes()) != active["catalog_sha256"]
    ):
        raise ValueError("Active personal package metadata changed")
    current, patch = load_context(directory / "source-catalog.json", directory)
    if (
        patch["patch_id"] != patch_id
        or active["anchor_sha256"] != context_anchor(catalog)
        or context_anchor(current) != active["anchor_sha256"]
    ):
        raise ValueError("Active personal package belongs to a different release or catalog")
    return current, patch, directory


def installation_phase(
    game_root: Path, catalog: dict, base: dict, *, recovery: bool = False
) -> str:
    """Check scripts/extras before changing the current installation or any pointer."""
    read_originals(game_root, catalog, base)
    state_path = inside(game_root, ".fvn-backups/" + base["patch_id"] + "/state.json")
    phase = "absent"
    if state_path.exists():
        state = read_json(state_path)
        if (
            state.get("patch_id") != base["patch_id"]
            or state.get("manifest_sha256") != catalog["base_patch_sha256"]
            or os.path.normcase(os.path.abspath(state.get("game_root", "")))
            != os.path.normcase(str(game_root.resolve()))
        ):
            raise ValueError("Current backup state differs from this game and package")
        phase = state.get("phase")
        if phase not in {"installed", "uninstalled", "prepared"}:
            raise ValueError("Invalid current installation state")
        if phase == "prepared" and not recovery:
            raise ValueError("An earlier installation is incomplete; run rollback first")
    if recovery and phase in {"prepared", "installed"}:
        # A stopped restore may have already restored some scripts or removed
        # extras. Only the two manifest hashes are accepted, never a third state.
        for file in base["files"]:
            actual = digest(inside(game_root, file["path"], game=True).read_bytes())
            if actual not in {file["source_sha256"], file["target_sha256"]}:
                raise ValueError("Game script changed outside the known source/installed states")
        for extra in base["extras"]:
            path = inside(game_root, extra["path"], game=True)
            if path.exists() and (
                not path.is_file() or digest(path.read_bytes()) != extra["sha256"]
            ):
                raise ValueError("An installed extra was changed; refusing to overwrite it")
        return phase  # Bound installer still verifies every backup and compiled entry.
    for file in base["files"]:
        expected = file["target_sha256"] if phase == "installed" else file["source_sha256"]
        if digest(inside(game_root, file["path"], game=True).read_bytes()) != expected:
            raise ValueError("Game scripts do not match their current installation state")
    for extra in base["extras"]:
        path = inside(game_root, extra["path"], game=True)
        if phase == "installed":
            if not path.is_file() or digest(path.read_bytes()) != extra["sha256"]:
                raise ValueError(
                    "An installed extra was removed or changed; refusing to overwrite it"
                )
        elif path.exists():
            raise ValueError("An extra destination already exists outside this installation")
    return phase


def powershell_program(explicit: str | None = None) -> str:
    executable = explicit or shutil.which("powershell.exe" if os.name == "nt" else "pwsh")
    if not executable:
        raise ValueError("Windows PowerShell was not found; no game files were modified")
    return executable


def run_installer(base_root: Path, game_root: Path, action: str, executable: str) -> None:
    # The frozen installer only gates runtime inputs for Install. This wrapper
    # deliberately retains its stricter runtime gate for every explicit write.
    manifest = read_json(inside(base_root, "patch.json"))
    verify_runtime_guards(game_root, manifest.get("runtime_guards", []))
    process = subprocess.run(
        [
            executable,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(inside(base_root, "install.ps1")),
            "-Action",
            action,
            "-GameRoot",
            str(game_root),
        ],
        capture_output=True,
        text=True,
        errors="replace",
        check=False,
    )
    if process.returncode:
        raise RuntimeError(
            f"{action} failed ({process.returncode}): " + process.stdout + process.stderr
        )


@contextmanager
def operation_lock(game_root: Path):
    path = inside(game_root, ".fvn-local-operation.lock")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as error:
        raise ValueError(
            "Another local operation may be active; preserve its journal and lock"
        ) from error
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        path.unlink()


def archive_restored_backup(game_root: Path, catalog: dict, base: dict) -> str | None:
    path = inside(game_root, ".fvn-backups/" + base["patch_id"])
    if not path.exists():
        return None
    if installation_phase(game_root, catalog, base) != "uninstalled":
        raise ValueError("Only a verified restored backup may be archived")
    # Keep archives outside the patch-ID namespace: a valid ID such as history
    # must never cause a directory to be moved into one of its own descendants.
    relative = ".fvn-backup-history/" + base["patch_id"] + "-" + uuid.uuid4().hex
    destination = inside(game_root, relative)
    if destination.exists():
        raise ValueError("Backup archive destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(path, destination)
    return relative


def write_active(game_root: Path, catalog: dict, base_root: Path, phase: str) -> None:
    patch_id = patch_identifier(catalog["base_patch_id"])
    if base_root.resolve() != inside(game_root, ".fvn-personal/" + patch_id):
        raise ValueError("Only managed personal packages can become active")
    atomic_write(
        inside(game_root, ACTIVE_FILE),
        json_bytes(
            {
                "schema": ACTIVE_SCHEMA,
                "phase": phase,
                "patch_id": patch_id,
                "patch_path": ".fvn-personal/" + patch_id,
                "manifest_sha256": catalog["base_patch_sha256"],
                "catalog_sha256": digest((base_root / "source-catalog.json").read_bytes()),
                "anchor_sha256": context_anchor(catalog),
            }
        ),
    )


def apply_personal(
    game_root: Path,
    catalog: dict,
    base: dict,
    base_root: Path,
    translations: Path,
    *,
    patch_id: str | None = None,
    powershell: str | None = None,
) -> dict:
    """Explicit local write: validate, build, switch, and recover on installer failure."""
    game_root = game_root.resolve()
    originals = read_originals(game_root, catalog, base)
    filled, validation = read_translations(translations, catalog, originals)
    phase = installation_phase(game_root, catalog, base)
    executable = powershell_program(powershell)
    archive_store = inside(game_root, ".fvn-backup-history")
    if phase == "installed" and archive_store.exists() and not archive_store.is_dir():
        raise ValueError("Backup archive location is not a directory; no installation was changed")
    unit_map = {unit["unit_id"]: unit for unit in catalog["units"]}
    existing = replacements_by_id(base)
    completed = set(catalog["base_origin_unit_ids"]) | set(catalog["manual_completed_unit_ids"])
    unchanged = True
    for unit_id, target in filled.items():
        unit = unit_map[unit_id]
        if unit_id in existing:
            raw = base64.b64decode(
                existing[unit_id][1]["replacement_base64"], validate=True
            ).decode("utf-8")
            previous = decode_content(raw, unit["codec"], unit["quote"], unit["prefix"])[0]
        else:
            previous = local_text(unit, originals)[0]
        unchanged &= target == previous and unit_id in completed
    if unchanged and phase == "installed":
        return {
            "applied": False,
            "already_current": True,
            "patch_id": base["patch_id"],
            "validation": validation,
            "coverage": coverage(catalog, existing, set(catalog["manual_completed_unit_ids"])),
        }
    patch_id = patch_identifier(patch_id or "personal-" + uuid.uuid4().hex)
    output = inside(game_root, ".fvn-personal/" + patch_id)
    if inside(game_root, ".fvn-backups/" + patch_id).exists():
        raise ValueError("This patch-id has retained backups; use a fresh patch-id")
    with operation_lock(game_root):
        # Recheck while holding the local operation lock. Import validates payloads
        # and every input row before it creates the managed package directory.
        if installation_phase(game_root, catalog, base) != phase:
            raise ValueError("Current installation changed during validation")
        result = import_personal(
            game_root,
            catalog,
            base,
            base_root,
            translations,
            output,
            patch_id,
            managed=True,
            allow_empty=True,
        )
        new_catalog, new_base = load_context(output / "source-catalog.json", output)
        journal_path = output / "operation.json"
        journal = {
            "schema": "fvn-local-operation/v1",
            "phase": "built",
            "previous_patch_id": base["patch_id"],
            "previous_installed": phase == "installed",
            "new_patch_id": patch_id,
            "game_root": str(game_root),
            "previous_package": str(base_root.resolve()),
            "previous_manifest_sha256": catalog["base_patch_sha256"],
            "new_package": str(output),
            "new_manifest_sha256": new_catalog["base_patch_sha256"],
        }
        atomic_write(journal_path, json_bytes(journal))
        try:
            if phase == "installed":
                journal["phase"] = "removing-previous"
                atomic_write(journal_path, json_bytes(journal))
                run_installer(base_root, game_root, "Uninstall", executable)
                journal["previous_backup_archive"] = archive_restored_backup(
                    game_root, catalog, base
                )
            journal["phase"] = "installing"
            atomic_write(journal_path, json_bytes(journal))
            run_installer(output, game_root, "Install", executable)
            if installation_phase(game_root, new_catalog, new_base) != "installed":
                raise RuntimeError("New installer did not finish in the installed state")
            write_active(game_root, new_catalog, output, "installed")
        except (OSError, ValueError, RuntimeError) as error:
            journal["phase"] = "recovering"
            journal["error"] = str(error)
            atomic_write(journal_path, json_bytes(journal))
            try:
                new_state = inside(game_root, ".fvn-backups/" + patch_id + "/state.json")
                if new_state.exists() and read_json(new_state).get("phase") in {
                    "prepared",
                    "installed",
                }:
                    try:
                        run_installer(output, game_root, "Uninstall", executable)
                    except (OSError, ValueError, RuntimeError):
                        if installation_phase(game_root, new_catalog, new_base) != "uninstalled":
                            raise
                if phase == "installed":
                    archive = recover_previous_installation(
                        game_root, catalog, base, base_root, executable
                    )
                    if archive is not None:
                        journal["previous_backup_archive"] = archive
                elif installation_phase(game_root, new_catalog, new_base) not in {
                    "absent",
                    "uninstalled",
                }:
                    raise RuntimeError("Official original state did not recover")
                journal["phase"] = "failed-previous-state-restored"
            except (OSError, ValueError, RuntimeError) as recovery_error:
                journal["phase"] = "failed-recovery-required"
                journal["recovery_error"] = str(recovery_error)
            atomic_write(journal_path, json_bytes(journal))
            raise RuntimeError(
                f"Apply failed; {journal['phase']}. Preserve {journal_path}. {error}"
            ) from error
        journal["phase"] = "installed"
        atomic_write(journal_path, json_bytes(journal))
        return {**result, "applied": True, "patch_id": patch_id, "journal": str(journal_path)}


def recover_previous_installation(
    game_root: Path, catalog: dict, base: dict, base_root: Path, executable: str
) -> str | None:
    """Use observed hashes/state, including a successful action that raised later."""
    try:
        if installation_phase(game_root, catalog, base) == "installed":
            return None
    except ValueError:
        pass  # Strict installed checks reject an interrupted source/target mixture.
    actual = installation_phase(game_root, catalog, base, recovery=True)
    if actual in {"installed", "prepared"}:
        try:
            run_installer(base_root, game_root, "Uninstall", executable)
        except (OSError, ValueError, RuntimeError):
            if installation_phase(game_root, catalog, base) != "uninstalled":
                raise
    archive = archive_restored_backup(game_root, catalog, base)
    try:
        run_installer(base_root, game_root, "Install", executable)
    except (OSError, ValueError, RuntimeError):
        if installation_phase(game_root, catalog, base) != "installed":
            raise
    if installation_phase(game_root, catalog, base) != "installed":
        raise RuntimeError("Previous installation did not recover")
    return archive


def rollback_current(
    game_root: Path, catalog: dict, base: dict, base_root: Path, *, powershell: str | None = None
) -> dict:
    game_root = game_root.resolve()
    phase = installation_phase(game_root, catalog, base, recovery=True)
    if phase not in {"installed", "prepared"}:
        return {"restored": False, "already_original": True, "patch_id": base["patch_id"]}
    executable = powershell_program(powershell)
    with operation_lock(game_root):
        installation_phase(game_root, catalog, base, recovery=True)
        run_installer(base_root, game_root, "Uninstall", executable)
        if installation_phase(game_root, catalog, base) != "uninstalled":
            raise RuntimeError("Rollback did not finish in the uninstalled state")
        if inside(game_root, ACTIVE_FILE).exists():
            write_active(game_root, catalog, base_root, "uninstalled")
    return {"restored": True, "patch_id": base["patch_id"], "personal_targets_retained": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    author = commands.add_parser("build-catalog", help="Author-time metadata-only catalog")
    author.add_argument("--units", type=Path, required=True)
    author.add_argument("--source", type=Path, required=True)
    author.add_argument("--base-patch", type=Path, required=True)
    author.add_argument("--output", type=Path, required=True)
    for action in ("export", "import", "validate", "status", "apply", "rollback"):
        command = commands.add_parser(action)
        command.add_argument("--game-root", type=Path, required=True)
        command.add_argument("--catalog", type=Path)
        command.add_argument("--base-patch", type=Path, default=Path(__file__).resolve().parent)
        if action in {"import", "validate", "status", "apply"}:
            command.add_argument("--translations", type=Path, required=action != "status")
        if action in {"export", "import"}:
            command.add_argument("--output", type=Path, required=True)
        if action == "export":
            command.add_argument("--force", action="store_true")
            command.add_argument(
                "--path", action="append", help="Optional exact game/... path filter"
            )
        if action in {"import", "apply"}:
            command.add_argument("--patch-id", required=action == "import")
        if action in {"apply", "rollback"}:
            command.add_argument("--powershell", help="Explicit PowerShell executable (optional)")
    arguments = parser.parse_args()
    try:
        if arguments.command == "build-catalog":
            catalog = build_catalog(
                arguments.units, arguments.source, arguments.base_patch, arguments.output
            )
            result = {"catalog_units": len(catalog["units"]), "output": str(arguments.output)}
        else:
            catalog_path = arguments.catalog or arguments.base_patch / "source-catalog.json"
            catalog, base, base_root = active_context(
                arguments.game_root, catalog_path, arguments.base_patch
            )
            if arguments.command == "export":
                result = export_untranslated(
                    arguments.game_root,
                    catalog,
                    base,
                    arguments.output,
                    force=arguments.force,
                    paths=arguments.path,
                )
            elif arguments.command == "import":
                result = import_personal(
                    arguments.game_root,
                    catalog,
                    base,
                    base_root,
                    arguments.translations,
                    arguments.output,
                    arguments.patch_id,
                )
            elif arguments.command == "apply":
                result = apply_personal(
                    arguments.game_root,
                    catalog,
                    base,
                    base_root,
                    arguments.translations,
                    patch_id=arguments.patch_id,
                    powershell=arguments.powershell,
                )
            elif arguments.command == "rollback":
                result = rollback_current(
                    arguments.game_root, catalog, base, base_root, powershell=arguments.powershell
                )
            else:
                originals = read_originals(arguments.game_root, catalog, base)
                result = {
                    "coverage": coverage(
                        catalog, replacements_by_id(base), set(catalog["manual_completed_unit_ids"])
                    ),
                    "source_guards_verified": len(originals),
                }
                if arguments.translations:
                    _, result["validation"] = read_translations(
                        arguments.translations, catalog, originals
                    )
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    except (ValueError, KeyError, OSError, SyntaxError, UnicodeError, RuntimeError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
