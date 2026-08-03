from typing import Protocol

from fvn_translator.models import LLMRequest, LLMResponse, ProviderHealth


class LLMProvider(Protocol):
    async def test_connection(self) -> ProviderHealth: ...
    async def complete(self, request: LLMRequest) -> LLMResponse: ...
