from fvn_translator.config.secrets import get_secret
from fvn_translator.models import ProviderConfig

from .base import LLMProvider
from .mock import MockProvider
from .openai_compatible import OpenAICompatibleProvider


def create_provider(config: ProviderConfig, *, temporary_secret: str | None = None) -> LLMProvider:
    if config.type == "mock":
        return MockProvider()
    if not config.secret_ref:
        raise ValueError("secret_ref is required for a network provider")
    secret = get_secret(config.secret_ref, temporary=temporary_secret)
    if not secret:
        raise ValueError(f"No credential available for {config.secret_ref}")
    return OpenAICompatibleProvider(config, secret)
