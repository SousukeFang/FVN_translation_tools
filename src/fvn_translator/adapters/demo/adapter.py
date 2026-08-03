import re
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from fvn_translator.core.atomic_io import atomic_write_bytes
from fvn_translator.core.hashing import bytes_hash, file_hash
from fvn_translator.models import Issue, Severity, TranslationUnit, UnitType

from ..base import (
    AdapterConfig,
    ApplyResult,
    DetectionResult,
    ExtractionResult,
    SourceFile,
    ValidationReport,
)

LINE = re.compile(r"^\[(?P<speaker>[^\]]+)\](?P<space>\s*)(?P<text>.*)$")
TOKEN = re.compile(r"\{/?[A-Za-z][^}]*\}|\[[A-Za-z_][^\]]*\]")


def _decode(data: bytes) -> tuple[str, str, bool]:
    bom = data.startswith(b"\xef\xbb\xbf")
    return data.decode("utf-8-sig"), "utf-8", bom


class DemoAdapter:
    adapter_id = "demo"
    adapter_version = "1.0.0"
    supported_ftif_versions: tuple[str, ...] = ("v1",)

    def detect(self, source_root: Path) -> DetectionResult:
        found = any(source_root.rglob("*.demo")) if source_root.is_dir() else False
        return DetectionResult(supported=found, confidence=1.0 if found else 0.0, reason="*.demo")

    def discover_files(self, source_root: Path, config: AdapterConfig) -> list[SourceFile]:
        files = []
        for path in sorted(source_root.rglob("*.demo")):
            data = path.read_bytes()
            text, encoding, bom = _decode(data)
            newline = "\r\n" if "\r\n" in text else "\n"
            files.append(
                SourceFile(
                    relative_path=path.relative_to(source_root).as_posix(),
                    fingerprint=file_hash(path),
                    encoding=encoding,
                    newline=newline,
                    has_bom=bom,
                )
            )
        return files

    def extract(
        self, source_root: Path, files: list[SourceFile], config: AdapterConfig
    ) -> ExtractionResult:
        units: list[TranslationUnit] = []
        sequence = 0
        for source_file in files:
            path = source_root / source_file.relative_path
            text, _, _ = _decode(path.read_bytes())
            for line_number, line in enumerate(text.splitlines(), 1):
                match = LINE.match(line)
                if not match:
                    continue
                source = match.group("text")
                speaker = match.group("speaker")
                identity = f"demo:{source_file.relative_path}:{line_number}:{source}"
                unit_id = str(uuid5(NAMESPACE_URL, identity))
                units.append(
                    TranslationUnit(
                        unit_id=unit_id,
                        sequence=sequence,
                        segment_id=source_file.relative_path,
                        scene_id=source_file.relative_path,
                        type=UnitType.NARRATION if speaker == "NARRATION" else UnitType.DIALOGUE,
                        speaker=None if speaker == "NARRATION" else speaker,
                        source_text=source,
                        source_fingerprint=bytes_hash(source.encode("utf-8")),
                        protected_tokens=TOKEN.findall(source),
                        origin={
                            "path": source_file.relative_path,
                            "line": line_number,
                            "file_fingerprint": source_file.fingerprint,
                        },
                        adapter_data={"speaker": speaker, "space": match.group("space")},
                    )
                )
                sequence += 1
        return ExtractionResult(units=units, files=files)

    def apply(
        self,
        source_root: Path,
        staging_root: Path,
        units: list[TranslationUnit],
        config: AdapterConfig,
    ) -> ApplyResult:
        grouped: dict[str, list[TranslationUnit]] = {}
        for unit in units:
            grouped.setdefault(str(unit.origin["path"]), []).append(unit)
        written = []
        for relative, file_units in grouped.items():
            source = source_root / relative
            data = source.read_bytes()
            text, _, bom = _decode(data)
            newline = "\r\n" if "\r\n" in text else "\n"
            trailing = text.endswith(("\n", "\r"))
            lines = text.splitlines()
            for unit in file_units:
                index = int(unit.origin["line"]) - 1
                match = LINE.match(lines[index])
                if not match:
                    raise ValueError(f"Demo source structure changed at {relative}:{index + 1}")
                target = unit.target_text or unit.source_text
                lines[index] = f"[{match.group('speaker')}]{match.group('space')}{target}"
            rendered = newline.join(lines) + (newline if trailing else "")
            target_path = staging_root / relative
            payload = rendered.encode("utf-8")
            if bom:
                payload = b"\xef\xbb\xbf" + payload
            atomic_write_bytes(target_path, payload)
            written.append(relative)
        return ApplyResult(written_files=written)

    def validate(
        self, staging_root: Path, units: list[TranslationUnit], config: AdapterConfig
    ) -> ValidationReport:
        issues: list[Issue] = []
        for relative in sorted({str(unit.origin["path"]) for unit in units}):
            path = staging_root / relative
            if not path.exists():
                issues.append(
                    Issue(
                        issue_id=f"demo-missing-{relative}",
                        code="DEMO_FILE_MISSING",
                        severity=Severity.ERROR,
                        message="Staging file is missing",
                        path=relative,
                    )
                )
                continue
            for number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
                if line and not LINE.match(line):
                    issues.append(
                        Issue(
                            issue_id=f"demo-line-{relative}-{number}",
                            code="DEMO_LINE_INVALID",
                            severity=Severity.ERROR,
                            message="Expected [SPEAKER] text",
                            path=relative,
                            line=number,
                        )
                    )
        return ValidationReport(issues=issues)
