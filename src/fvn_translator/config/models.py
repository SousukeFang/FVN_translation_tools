from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from fvn_translator.models import ProviderConfig


class ProjectConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    project_name: str
    source_root: Path
    adapter_id: str = "demo"
    source_language: str = "en"
    target_language: str = "zh-CN"
    adapter_options: dict[str, object] = Field(default_factory=dict)


class ProvidersConfig(BaseModel):
    active_provider: str = "mock"
    providers: dict[str, ProviderConfig] = Field(
        default_factory=lambda: {"mock": ProviderConfig(name="mock", type="mock")}
    )
