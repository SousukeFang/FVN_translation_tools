"""Replace only the UTF-8 story spans explicitly identified in a map by an Agent."""

import json
from collections import defaultdict
from pathlib import Path
from typing import Literal

from pydantic import Field

from fvn_translator.core.atomic_io import atomic_write_bytes
from fvn_translator.core.errors import ApplyConflictError
from fvn_translator.core.hashing import bytes_hash, file_hash, stable_hash
from fvn_translator.core.paths import ensure_within
from fvn_translator.models import Issue, Severity, TranslationUnit, UnitType
from fvn_translator.models.common import StrictModel
from fvn_translator.validators.placeholders import extract_placeholders

from ..base import (
    AdapterConfig,
    ApplyResult,
    DetectionResult,
    ExtractionResult,
    SourceFile,
    ValidationReport,
)


class Span(StrictModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    source_text: str
    codec: Literal["plain", "json-string"] = "plain"
    type: UnitType = UnitType.NARRATION
    speaker: str | None = None
    scene_id: str | None = None
    protected_tokens: list[str] = Field(default_factory=list)


class MappedFile(StrictModel):
    path: str
    spans: list[Span] = Field(min_length=1)


class SpanMap(StrictModel):
    files: list[MappedFile] = Field(min_length=1)


def _load_map(config: AdapterConfig) -> SpanMap:
    map_path = config.options.get("map_path")
    if not map_path:
        raise ValueError("text-spans requires AdapterConfig.options.map_path")
    mapping = SpanMap.model_validate_json(Path(str(map_path)).read_text(encoding="utf-8-sig"))
    paths = [item.path for item in mapping.files]
    if len(paths) != len(set(paths)):
        raise ValueError("Span map contains duplicate file paths")
    return mapping


def _path(root: Path, relative: str) -> Path:
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"Span map path must be relative: {relative}")
    return ensure_within(root, root / relative)


def _read(path: Path) -> tuple[str, bool]:
    data = path.read_bytes()
    return data.decode("utf-8-sig"), data.startswith(b"\xef\xbb\xbf")


def _decode(raw: str, codec: str) -> str:
    value = json.loads(raw) if codec == "json-string" else raw
    if not isinstance(value, str):
        raise ValueError("A json-string span must include one complete JSON string literal")
    return value


def _render(unit: TranslationUnit) -> str:
    target = unit.target_text or unit.source_text
    if target == unit.source_text:
        return str(unit.adapter_data["source_raw_content"])
    if unit.adapter_data["codec"] == "json-string":
        return json.dumps(target, ensure_ascii=False)
    newline = str(unit.adapter_data["file_newline"])
    return target.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline)


def _structure(text: str, ranges: list[tuple[int, int]]) -> str:
    chunks = []
    previous = 0
    for start, end in ranges:
        chunks.append(text[previous:start])
        previous = end
    chunks.append(text[previous:])
    return stable_hash(chunks)


def _group(units: list[TranslationUnit]) -> dict[str, list[TranslationUnit]]:
    grouped: dict[str, list[TranslationUnit]] = defaultdict(list)
    for unit in units:
        grouped[str(unit.origin["path"])].append(unit)
    for file_units in grouped.values():
        file_units.sort(key=lambda unit: int(unit.adapter_data["content_start"]))
    return grouped


class TextSpanAdapter:
    adapter_id = "text-spans"
    adapter_version = "1.0.0"
    supported_ftif_versions: tuple[str, ...] = ("v1",)

    def detect(self, source_root: Path) -> DetectionResult:
        return DetectionResult(
            supported=False,
            confidence=0,
            reason="Explicit Agent-created span map required; text is not auto-discovered",
        )

    def discover_files(self, source_root: Path, config: AdapterConfig) -> list[SourceFile]:
        files = []
        for mapped in sorted(_load_map(config).files, key=lambda item: item.path):
            path = _path(source_root, mapped.path)
            text, bom = _read(path)
            files.append(
                SourceFile(
                    relative_path=mapped.path,
                    fingerprint=file_hash(path),
                    has_bom=bom,
                    newline="\r\n" if "\r\n" in text else "\n",
                    size=path.stat().st_size,
                    category="story",
                )
            )
        return files

    def extract(
        self, source_root: Path, files: list[SourceFile], config: AdapterConfig
    ) -> ExtractionResult:
        mapping = {item.path: item for item in _load_map(config).files}
        units: list[TranslationUnit] = []
        updated_files = []
        for source_file in sorted(files, key=lambda item: item.relative_path):
            relative = source_file.relative_path
            path = _path(source_root, relative)
            if file_hash(path) != source_file.fingerprint:
                raise ApplyConflictError(f"Source changed after discovery: {relative}")
            text, _ = _read(path)
            spans = sorted(mapping[relative].spans, key=lambda item: item.start)
            previous = 0
            for span in spans:
                if span.start < previous or span.end <= span.start or span.end > len(text):
                    raise ValueError(f"Invalid or overlapping span in {relative}: {span.start}")
                if _decode(text[span.start : span.end], span.codec) != span.source_text:
                    raise ValueError(
                        f"Span source_text differs from source in {relative}: {span.start}"
                    )
                previous = span.end
            fingerprint = _structure(text, [(span.start, span.end) for span in spans])
            for span_index, span in enumerate(spans):
                units.append(
                    TranslationUnit(
                        unit_id=f"text-spans:{relative}:{span_index}:{span.codec}",
                        sequence=len(units),
                        segment_id=relative,
                        scene_id=span.scene_id or relative,
                        type=span.type,
                        speaker=span.speaker,
                        source_text=span.source_text,
                        source_fingerprint=bytes_hash(span.source_text.encode("utf-8")),
                        protected_tokens=list(
                            dict.fromkeys(
                                [*extract_placeholders(span.source_text), *span.protected_tokens]
                            )
                        ),
                        origin={
                            "path": relative,
                            "line": text.count("\n", 0, span.start) + 1,
                            "file_fingerprint": source_file.fingerprint,
                        },
                        context={"semantic_role": "agent_identified_story_text"},
                        adapter_data={
                            "content_start": span.start,
                            "content_end": span.end,
                            "source_raw_content": text[span.start : span.end],
                            "codec": span.codec,
                            "file_structure_fingerprint": fingerprint,
                            "file_has_bom": source_file.has_bom,
                            "file_newline": source_file.newline,
                        },
                    )
                )
            updated_files.append(
                source_file.model_copy(update={"extracted_unit_count": len(spans)})
            )
        return ExtractionResult(units=units, files=updated_files)

    def apply(
        self,
        source_root: Path,
        staging_root: Path,
        units: list[TranslationUnit],
        config: AdapterConfig,
    ) -> ApplyResult:
        source, staging = source_root.resolve(), staging_root.resolve()
        if source == staging or staging.is_relative_to(source) or source.is_relative_to(staging):
            raise ValueError("Source and staging must be separate, non-nested directories")
        written = []
        for relative, file_units in sorted(_group(units).items()):
            path = _path(source, relative)
            expected = {str(unit.origin["file_fingerprint"]) for unit in file_units}
            if expected != {file_hash(path)}:
                raise ApplyConflictError(f"Source changed after extraction: {relative}")
            text, bom = _read(path)
            previous = 0
            for unit in file_units:
                start, end = (
                    int(unit.adapter_data["content_start"]),
                    int(unit.adapter_data["content_end"]),
                )
                if start < previous or end <= start or end > len(text):
                    raise ValueError(f"Invalid or overlapping span for {unit.unit_id}")
                if text[start:end] != unit.adapter_data["source_raw_content"]:
                    raise ApplyConflictError(f"Source slice changed for {unit.unit_id}")
                for token in unit.protected_tokens:
                    if unit.source_text.count(token) != (
                        unit.target_text or unit.source_text
                    ).count(token):
                        raise ValueError(f"Protected token changed for {unit.unit_id}: {token}")
                previous = end
            for unit in reversed(file_units):
                start, end = (
                    int(unit.adapter_data["content_start"]),
                    int(unit.adapter_data["content_end"]),
                )
                text = text[:start] + _render(unit) + text[end:]
            atomic_write_bytes(
                _path(staging, relative), (b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8")
            )
            written.append(relative)
        return ApplyResult(written_files=written)

    def validate(
        self, staging_root: Path, units: list[TranslationUnit], config: AdapterConfig
    ) -> ValidationReport:
        issues = []
        for relative, file_units in sorted(_group(units).items()):
            try:
                text, bom = _read(_path(staging_root, relative))
                if bom != file_units[0].adapter_data["file_has_bom"]:
                    raise ValueError("UTF-8 BOM changed")
                offset = 0
                ranges = []
                for unit in file_units:
                    start = int(unit.adapter_data["content_start"]) + offset
                    rendered = _render(unit)
                    end = start + len(rendered)
                    actual = _decode(text[start:end], str(unit.adapter_data["codec"]))
                    desired = _decode(rendered, str(unit.adapter_data["codec"]))
                    if actual != desired:
                        raise ValueError(f"Re-extracted text differs from target: {unit.unit_id}")
                    ranges.append((start, end))
                    offset += len(rendered) - (
                        int(unit.adapter_data["content_end"])
                        - int(unit.adapter_data["content_start"])
                    )
                if (
                    _structure(text, ranges)
                    != file_units[0].adapter_data["file_structure_fingerprint"]
                ):
                    raise ValueError("Content outside mapped story spans changed")
            except (OSError, ValueError) as exc:
                issues.append(
                    Issue(
                        issue_id=f"text-spans:{relative}:invalid",
                        code="TEXT_SPANS_INVALID",
                        severity=Severity.ERROR,
                        message=str(exc),
                        path=relative,
                    )
                )
        return ValidationReport(issues=issues)
