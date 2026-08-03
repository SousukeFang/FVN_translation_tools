from __future__ import annotations

import shutil
from collections import defaultdict
from pathlib import Path

from fvn_translator.core.atomic_io import atomic_write_bytes
from fvn_translator.core.errors import ApplyConflictError
from fvn_translator.core.hashing import file_hash
from fvn_translator.models import TranslationUnit

from .lexer import RenPyLexer
from .protected_tokens import compare_signatures, protection_signature


class RenPyWriter:
    def write(
        self,
        source_root: Path,
        staging_root: Path,
        units: list[TranslationUnit],
        *,
        prepare_full_project: bool = False,
    ) -> list[str]:
        if prepare_full_project:
            prepare_staging_project(source_root, staging_root)
        grouped: dict[str, list[TranslationUnit]] = defaultdict(list)
        for unit in units:
            grouped[str(unit.origin["path"])].append(unit)
        written: list[str] = []
        for relative in sorted(grouped):
            path = source_root / relative
            file_units = grouped[relative]
            expected_hashes = {str(unit.origin["file_fingerprint"]) for unit in file_units}
            if len(expected_hashes) != 1 or file_hash(path) not in expected_hashes:
                raise ApplyConflictError(f"Source changed after extraction: {relative}")
            data = path.read_bytes()
            bom = data.startswith(b"\xef\xbb\xbf")
            text = data.decode("utf-8-sig")
            if RenPyLexer().scan(text, relative).issues:
                raise ValueError(f"Source contains Ren'Py lexical errors: {relative}")
            replacements: list[tuple[int, int, str]] = []
            for unit in file_units:
                start = int(unit.adapter_data["content_start"])
                end = int(unit.adapter_data["content_end"])
                expected = str(unit.adapter_data["source_raw_content"])
                if text[start:end] != expected:
                    raise ApplyConflictError(
                        "String location changed after extraction: "
                        f"{relative}:{unit.origin['line']}"
                    )
                target = unit.target_text or unit.source_text
                quote = str(unit.adapter_data["quote"])
                prefix = str(unit.adapter_data.get("string_prefix", ""))
                rendered = (
                    expected
                    if target == unit.source_text
                    else encode_string_content(
                        target, quote=quote, raw_prefix="r" in prefix.lower()
                    )
                )
                signature = protection_signature(target, rendered)
                expected_signature = dict(unit.adapter_data["protection_signature"])
                problems = compare_signatures(expected_signature, signature)
                if problems:
                    raise ValueError(
                        f"Protected content changed for {unit.unit_id}: {problems[0].message}"
                    )
                replacements.append((start, end, rendered))
            for start, end, rendered in sorted(replacements, reverse=True):
                text = text[:start] + rendered + text[end:]
            payload = text.encode("utf-8")
            if bom:
                payload = b"\xef\xbb\xbf" + payload
            atomic_write_bytes(staging_root / relative, payload)
            written.append(relative)
        return written


def encode_string_content(value: str, *, quote: str, raw_prefix: bool = False) -> str:
    if raw_prefix:
        if quote in value:
            raise ValueError("A raw Ren'Py string cannot safely contain its original quote")
        return value
    quote_character = quote[0]
    output: list[str] = []
    braces = 0
    brackets = 0
    index = 0
    while index < len(value):
        char = value[index]
        if value.startswith("{{", index) or value.startswith("[[", index):
            output.append(value[index : index + 2])
            index += 2
            continue
        if char == "{":
            braces += 1
        elif char == "}" and braces:
            braces -= 1
        elif char == "[":
            brackets += 1
        elif char == "]" and brackets:
            brackets -= 1
        if char == "\\":
            output.append("\\\\")
        elif char == quote_character and not braces and not brackets:
            output.append(f"\\{quote_character}")
        elif len(quote) == 1 and char == "\n":
            output.append("\\n")
        elif len(quote) == 1 and char == "\r":
            if index + 1 < len(value) and value[index + 1] == "\n":
                index += 1
            output.append("\\n")
        elif len(quote) == 1 and char == "\t":
            output.append("\\t")
        else:
            output.append(char)
        index += 1
    return "".join(output)


def prepare_staging_project(source_root: Path, staging_root: Path) -> None:
    source = source_root.resolve()
    staging = staging_root.resolve()
    if staging == source or staging.is_relative_to(source) or source.is_relative_to(staging):
        raise ValueError("staging_root and source_root must be separate, non-nested directories")

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {name for name in names if name in {"cache", "saves", ".git", "backups"}}
        return ignored

    shutil.copytree(source, staging, dirs_exist_ok=True, copy_function=shutil.copy2, ignore=ignore)


def prepare_script_staging(
    source_root: Path, staging_root: Path, relative_paths: list[str]
) -> None:
    for relative in sorted(set(relative_paths)):
        atomic_write_bytes(staging_root / relative, (source_root / relative).read_bytes())
