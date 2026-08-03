from pathlib import Path

from fvn_translator.config import ProvidersConfig, load_providers, write_providers
from fvn_translator.llm import LLMProvider, create_provider
from fvn_translator.models import ProviderConfig, ProviderHealth


class ProviderService:
    def __init__(self, path: Path) -> None:
        self.path = path

    def load(self) -> ProvidersConfig:
        return load_providers(self.path)

    def upsert(self, provider: ProviderConfig) -> None:
        config = self.load()
        config.providers[provider.name] = provider
        write_providers(self.path, config)

    def switch(self, name: str) -> None:
        config = self.load()
        if name not in config.providers:
            raise KeyError(name)
        config.active_provider = name
        write_providers(self.path, config)

    def active(self, *, temporary_secret: str | None = None) -> LLMProvider:
        config = self.load()
        return create_provider(
            config.providers[config.active_provider], temporary_secret=temporary_secret
        )

    async def test_active(self, *, temporary_secret: str | None = None) -> ProviderHealth:
        return await self.active(temporary_secret=temporary_secret).test_connection()
