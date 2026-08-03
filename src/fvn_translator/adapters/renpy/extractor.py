from __future__ import annotations

from pathlib import Path

from fvn_translator.adapters.base import ExtractionResult, SourceFile
from fvn_translator.core.hashing import bytes_hash
from fvn_translator.models import TranslationUnit
from fvn_translator.profiles.base import FVNProfile, ParseContext, SceneRules

from .parser import RenPyParser
from .protected_tokens import protection_signature, unique_protected_tokens


class RenPyExtractor:
    def __init__(
        self,
        profile: FVNProfile | None = None,
        *,
        allowed_speakers: set[str] | None = None,
    ) -> None:
        self.profile = profile
        self.allowed_speakers = allowed_speakers

    def extract(self, source_root: Path, files: list[SourceFile]) -> ExtractionResult:
        units: list[TranslationUnit] = []
        issues = []
        updated_files: list[SourceFile] = []
        sinks = self.profile.get_custom_text_sinks() if self.profile else []
        scene_rules = self.profile.get_scene_rules() if self.profile else SceneRules()
        allowed_speakers = self.allowed_speakers
        if allowed_speakers is None and self.profile:
            allowed_speakers = set(self.profile.get_character_map(source_root))
        parser = RenPyParser(
            custom_sinks=sinks,
            scene_rules=scene_rules,
            allowed_speakers=allowed_speakers,
        )
        sequence = 0
        for source_file in files:
            path = source_root / source_file.relative_path
            text = path.read_bytes().decode("utf-8-sig")
            parsed = parser.parse(text, source_file.relative_path)
            issues.extend(parsed.issues)
            file_units: list[TranslationUnit] = []
            local_ids: list[str] = []
            for node in parsed.nodes:
                unit_id = (
                    f"renpy:{source_file.relative_path}:{node.label}:"
                    f"{node.statement_index}:{node.text_role}"
                )
                signature = protection_signature(node.token.value, node.token.raw_content)
                adapter_data: dict[str, object] = {
                    "node_kind": node.kind,
                    "label": node.label,
                    "statement_index": node.statement_index,
                    "text_role": node.text_role,
                    "statement_start": node.statement_start,
                    "statement_end": node.statement_end,
                    "content_start": node.token.content_start,
                    "content_end": node.token.content_end,
                    "quote": node.token.quote,
                    "string_prefix": node.token.prefix,
                    "source_literal": node.token.raw,
                    "source_raw_content": node.token.raw_content,
                    "source_statement_fingerprint": bytes_hash(
                        text[node.statement_start : node.statement_end].encode("utf-8")
                    ),
                    "speaker_attributes": list(node.speaker_attributes),
                    "explicit_display_name": node.explicit_display_name,
                    "protection_signature": signature,
                    "file_structure_fingerprint": parsed.structure_fingerprint,
                    "file_encoding": source_file.encoding,
                    "file_newline": source_file.newline,
                    "file_has_bom": source_file.has_bom,
                    **node.context,
                }
                unit = TranslationUnit(
                    unit_id=unit_id,
                    sequence=sequence,
                    segment_id=source_file.relative_path,
                    scene_id=node.scene_id,
                    type=node.unit_type,
                    speaker=node.speaker,
                    source_text=node.token.value,
                    source_fingerprint=bytes_hash(node.token.value.encode("utf-8")),
                    protected_tokens=unique_protected_tokens(signature),
                    context={
                        "semantic_role": node.kind,
                        "speaker_display_name": node.explicit_display_name,
                    },
                    origin={
                        "path": source_file.relative_path,
                        "line": node.start_line,
                        "end_line": node.end_line,
                        "column": node.token.start_column,
                        "end_column": node.token.end_column,
                        "file_fingerprint": source_file.fingerprint,
                    },
                    constraints={"preserve_protected_tokens": True},
                    adapter_data=adapter_data,
                )
                if node.extends_index is not None and node.extends_index < len(local_ids):
                    unit.adapter_data["extends_unit_id"] = local_ids[node.extends_index]
                if self.profile:
                    unit = self.profile.enrich_unit(
                        unit,
                        ParseContext(
                            relative_path=source_file.relative_path,
                            label=node.label,
                            scene_id=node.scene_id,
                        ),
                    )
                file_units.append(unit)
                local_ids.append(unit.unit_id)
                sequence += 1
            units.extend(file_units)
            updated_files.append(
                source_file.model_copy(update={"extracted_unit_count": len(file_units)})
            )
        return ExtractionResult(units=units, files=updated_files, issues=issues)
