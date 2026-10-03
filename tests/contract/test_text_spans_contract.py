import json
from pathlib import Path

import pytest

from fvn_translator.adapters import AdapterConfig, default_registry
from fvn_translator.adapters.text_spans import TextSpanAdapter
from fvn_translator.core.errors import ApplyConflictError
from fvn_translator.core.hashing import file_hash


def _project(tmp_path: Path) -> tuple[Path, Path, AdapterConfig]:
    source = tmp_path / "source"
    source.mkdir()
    first = 'Hello "Fox" {i}[name]{/i}.'
    second = "The door is open."
    text = (
        '{\r\n  "image": "untranslated-resource.png",\r\n'
        f'  "dialogue": {json.dumps(first)},\r\n'
        f'  "narration": {json.dumps(second)}\r\n}}\r\n'
    )
    (source / "story.json").write_bytes(b"\xef\xbb\xbf" + text.encode("utf-8"))
    spans = []
    for value in (first, second):
        raw = json.dumps(value)
        start = text.index(raw)
        spans.append(
            {"start": start, "end": start + len(raw), "source_text": value, "codec": "json-string"}
        )
    mapping_path = tmp_path / "spans.json"
    mapping_path.write_text(
        json.dumps({"files": [{"path": "story.json", "spans": spans}]}), encoding="utf-8"
    )
    return source, mapping_path, AdapterConfig(options={"map_path": str(mapping_path)})


def test_explicit_span_adapter_contract(tmp_path: Path) -> None:
    source, _, config = _project(tmp_path)
    adapter = TextSpanAdapter()
    before = file_hash(source / "story.json")
    files = adapter.discover_files(source, config)
    first = adapter.extract(source, files, config)
    second = adapter.extract(source, files, config)
    assert [unit.unit_id for unit in first.units] == [unit.unit_id for unit in second.units]
    assert [unit.adapter_data for unit in first.units] == [
        unit.adapter_data for unit in second.units
    ]
    assert [unit.origin for unit in first.units] == [unit.origin for unit in second.units]
    assert len(first.units) == 2
    assert file_hash(source / "story.json") == before
    staging = tmp_path / "staging"
    result = adapter.apply(source, staging, first.units, config)
    assert result.written_files == ["story.json"]
    assert file_hash(staging / "story.json") == before
    assert file_hash(source / "story.json") == before
    assert not adapter.validate(staging, first.units, config).has_errors
    assert default_registry().create("text-spans").adapter_id == "text-spans"
    assert not adapter.detect(source).supported


def test_translated_json_roundtrip_preserves_structure_and_bom(tmp_path: Path) -> None:
    source, mapping_path, config = _project(tmp_path)
    adapter = TextSpanAdapter()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    result.units[0].target_text = '你好，"狐狸"，{i}[name]{/i}。'
    result.units[1].target_text = "门开着。"
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert not adapter.validate(staging, result.units, config).has_errors
    data = (staging / "story.json").read_bytes()
    assert data.startswith(b"\xef\xbb\xbf")
    text = data.decode("utf-8-sig")
    assert "\r\n" in text
    assert json.loads(text)["image"] == "untranslated-resource.png"
    assert json.loads(text)["dialogue"] == result.units[0].target_text
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    for span, unit in zip(mapping["files"][0]["spans"], result.units, strict=True):
        raw = json.dumps(unit.target_text, ensure_ascii=False)
        span.update(
            start=text.index(raw), end=text.index(raw) + len(raw), source_text=unit.target_text
        )
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")
    reextracted = adapter.extract(staging, adapter.discover_files(staging, config), config)
    assert [unit.unit_id for unit in reextracted.units] == [unit.unit_id for unit in result.units]
    assert [unit.source_text for unit in reextracted.units] == [
        unit.target_text for unit in result.units
    ]


@pytest.mark.parametrize("problem", ["overlap", "out-of-range", "source-mismatch", "not-a-string"])
def test_invalid_mapping_is_rejected(tmp_path: Path, problem: str) -> None:
    source, mapping_path, config = _project(tmp_path)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    spans = mapping["files"][0]["spans"]
    if problem == "overlap":
        spans.append(dict(spans[0]))
    elif problem == "out-of-range":
        spans[0]["end"] = 10000
    elif problem == "source-mismatch":
        spans[0]["source_text"] = "Something else."
    else:
        spans[0].update(start=0, end=1)
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")
    adapter = TextSpanAdapter()
    with pytest.raises(ValueError):
        adapter.extract(source, adapter.discover_files(source, config), config)


def test_apply_rejects_source_changes_and_token_loss(tmp_path: Path) -> None:
    source, _, config = _project(tmp_path)
    adapter = TextSpanAdapter()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    result.units[0].target_text = "你好。"
    with pytest.raises(ValueError, match="Protected token changed"):
        adapter.apply(source, tmp_path / "staging", result.units, config)
    result.units[0].target_text = result.units[0].source_text
    (source / "story.json").write_bytes((source / "story.json").read_bytes() + b" ")
    with pytest.raises(ApplyConflictError, match="Source changed after extraction"):
        adapter.apply(source, tmp_path / "staging", result.units, config)


def test_source_slice_and_staging_structure_are_checked(tmp_path: Path) -> None:
    source, _, config = _project(tmp_path)
    adapter = TextSpanAdapter()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    unit = result.units[0]
    original = unit.adapter_data["source_raw_content"]
    unit.adapter_data["source_raw_content"] = '"tampered"'
    with pytest.raises(ApplyConflictError, match="Source slice changed"):
        adapter.apply(source, tmp_path / "staging", result.units, config)
    unit.adapter_data["source_raw_content"] = original
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    path = staging / "story.json"
    path.write_bytes(
        path.read_bytes().replace(b"untranslated-resource.png", b"untranslated-resource.jpg")
    )
    report = adapter.validate(staging, result.units, config)
    assert report.has_errors
    assert "outside mapped story spans changed" in report.issues[0].message


def test_map_path_escape_and_source_staging_alias_are_rejected(tmp_path: Path) -> None:
    source, mapping_path, config = _project(tmp_path)
    adapter = TextSpanAdapter()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    with pytest.raises(ValueError, match="separate"):
        adapter.apply(source, source, result.units, config)
    mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
    mapping["files"][0]["path"] = "../outside.json"
    mapping_path.write_text(json.dumps(mapping), encoding="utf-8")
    with pytest.raises(ValueError, match="relative"):
        adapter.discover_files(source, config)


def test_plain_spans_keep_newlines_and_unmapped_bytes(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    original = "asset=image.png\r\nHello\r\nWorld\r\nEnd marker\r\n"
    (source / "story.txt").write_bytes(original.encode("utf-8"))
    text = "Hello\r\nWorld"
    start = original.index(text)
    map_path = tmp_path / "map.json"
    map_path.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "path": "story.txt",
                        "spans": [{"start": start, "end": start + len(text), "source_text": text}],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    config = AdapterConfig(options={"map_path": str(map_path)})
    adapter = TextSpanAdapter()
    result = adapter.extract(source, adapter.discover_files(source, config), config)
    result.units[0].target_text = "你好\n世界"
    staging = tmp_path / "staging"
    adapter.apply(source, staging, result.units, config)
    assert (
        staging / "story.txt"
    ).read_bytes() == "asset=image.png\r\n你好\r\n世界\r\nEnd marker\r\n".encode()
    assert not adapter.validate(staging, result.units, config).has_errors
