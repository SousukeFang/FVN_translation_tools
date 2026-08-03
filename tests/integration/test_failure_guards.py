import asyncio

import pytest

from fvn_translator.adapters import AdapterConfig
from fvn_translator.adapters.demo import DemoAdapter
from fvn_translator.core.errors import ResponseFormatError
from fvn_translator.core.hashing import bytes_hash
from fvn_translator.llm.base import LLMProvider
from fvn_translator.models import (
    LLMRequest,
    LLMResponse,
    ProviderHealth,
    TranslationUnit,
    UnitType,
)
from fvn_translator.services import ApplyService, BackupService, RollbackService, TranslationService
from fvn_translator.storage import CacheStore, RevisionStore, StateDatabase, UnitRepository


class InvalidProvider(LLMProvider):
    async def test_connection(self) -> ProviderHealth:
        return ProviderHealth(healthy=False)

    async def complete(self, request: LLMRequest) -> LLMResponse:
        return LLMResponse(
            request_id=request.request_id,
            model="invalid",
            content={"translations": []},
        )


def test_invalid_response_marks_units_failed(tmp_path) -> None:
    database = StateDatabase(tmp_path / "state.sqlite3")
    repository = UnitRepository(tmp_path / "units.jsonl", database)
    unit = TranslationUnit(
        unit_id="u",
        sequence=0,
        segment_id="a",
        type=UnitType.NARRATION,
        source_text="Hello",
        source_fingerprint=bytes_hash(b"Hello"),
    )
    repository.save([unit])
    service = TranslationService(
        InvalidProvider(),
        repository,
        RevisionStore(tmp_path / "revisions.jsonl"),
        CacheStore(database),
        tmp_path / "runs",
    )
    with pytest.raises(ResponseFormatError):
        asyncio.run(service.translate())
    assert repository.load()[0].translation.status == "failed"
    database.close()


def test_common_validation_blocks_apply(tmp_path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    path = source / "chapter.demo"
    path.write_text("[Fox] Hello {i}friend{/i}.\n", encoding="utf-8")
    adapter = DemoAdapter()
    config = AdapterConfig()
    units = adapter.extract(source, adapter.discover_files(source, config), config).units
    units[0].target_text = "你好，朋友。"
    units[0].translation.status = "translated"
    database = StateDatabase(tmp_path / "state.sqlite3")
    repository = UnitRepository(tmp_path / "units.jsonl", database)
    repository.save(units)
    service = ApplyService(
        repository,
        BackupService(tmp_path / "backups"),
        RollbackService(tmp_path / "backups"),
    )
    with pytest.raises(ValueError, match="Common validation failed"):
        service.apply(adapter, source, tmp_path / "staging")
    assert path.read_text(encoding="utf-8") == "[Fox] Hello {i}friend{/i}.\n"
    database.close()
