from pathlib import Path

from fvn_translator.adapters.base import AdapterConfig, ExtractionResult, FVNAdapter
from fvn_translator.models import Issue
from fvn_translator.storage import JSONLStore, UnitRepository


class ExtractionService:
    def __init__(self, adapter: FVNAdapter, repository: UnitRepository) -> None:
        self.adapter = adapter
        self.repository = repository
        self.last_result: ExtractionResult | None = None

    def extract(self, source_root: Path, config: AdapterConfig | None = None) -> int:
        adapter_config = config or AdapterConfig()
        files = self.adapter.discover_files(source_root, adapter_config)
        result = self.adapter.extract(source_root, files, adapter_config)
        self.repository.save(result.units)
        JSONLStore(self.repository.path.parent / "issues.jsonl", Issue).write(result.issues)
        self.last_result = result
        return len(result.units)
