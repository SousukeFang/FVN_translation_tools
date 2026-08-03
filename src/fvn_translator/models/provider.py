from typing import Any, Literal

from pydantic import Field, HttpUrl

from .common import StrictModel


class ProviderConfig(StrictModel):
    name: str = Field(pattern=r"^[A-Za-z0-9_-]+$")
    type: Literal["mock", "openai-compatible"]
    base_url: HttpUrl | None = None
    model: str = "mock"
    secret_ref: str | None = None
    timeout_seconds: float = Field(default=120, gt=0)
    max_retries: int = Field(default=4, ge=0, le=10)
    temperature: float = Field(default=0.2, ge=0, le=2)
    max_concurrency: int = Field(default=1, ge=1)


class LLMRequest(StrictModel):
    request_id: str
    run_id: str
    batch_id: str
    task: str
    system_prompt: str
    payload: dict[str, Any]
    prompt_version: str


class LLMResponse(StrictModel):
    request_id: str
    model: str
    content: dict[str, Any]
    usage: dict[str, int] = Field(default_factory=dict)
    raw_text: str | None = None


class ProviderHealth(StrictModel):
    healthy: bool
    message: str = ""
