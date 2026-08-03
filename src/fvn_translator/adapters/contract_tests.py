from pathlib import Path

from fvn_translator.core.hashing import file_hash

from .base import AdapterConfig, FVNAdapter


def run_adapter_contract_tests(adapter: FVNAdapter, fixture_project: Path, staging: Path) -> None:
    before = {path: file_hash(path) for path in fixture_project.rglob("*") if path.is_file()}
    config = AdapterConfig()
    files = adapter.discover_files(fixture_project, config)
    first = adapter.extract(fixture_project, files, config)
    second = adapter.extract(fixture_project, files, config)
    assert [
        (
            unit.unit_id,
            unit.sequence,
            unit.segment_id,
            unit.source_text,
            unit.origin,
            unit.adapter_data,
        )
        for unit in first.units
    ] == [
        (
            unit.unit_id,
            unit.sequence,
            unit.segment_id,
            unit.source_text,
            unit.origin,
            unit.adapter_data,
        )
        for unit in second.units
    ]
    assert before == {
        path: file_hash(path) for path in fixture_project.rglob("*") if path.is_file()
    }
    adapter.apply(fixture_project, staging, first.units, config)
    assert before == {
        path: file_hash(path) for path in fixture_project.rglob("*") if path.is_file()
    }
    assert not adapter.validate(staging, first.units, config).has_errors
