import json

import httpx

from fvn_translator.core.errors import ProviderError, ResponseFormatError
from fvn_translator.models import LLMRequest, LLMResponse, ProviderConfig, ProviderHealth

from .retry import with_retry


class OpenAICompatibleProvider:
    def __init__(self, config: ProviderConfig, api_key: str) -> None:
        if not config.base_url:
            raise ValueError("base_url is required")
        self.config = config
        self.api_key = api_key

    async def test_connection(self) -> ProviderHealth:
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.get(
                    f"{str(self.config.base_url).rstrip('/')}/models", headers=self._headers()
                )
                response.raise_for_status()
            return ProviderHealth(healthy=True, message="connection succeeded")
        except httpx.HTTPError as exc:
            return ProviderHealth(healthy=False, message=str(exc))

    async def complete(self, request: LLMRequest) -> LLMResponse:
        async def send() -> httpx.Response:
            async with httpx.AsyncClient(timeout=self.config.timeout_seconds) as client:
                response = await client.post(
                    f"{str(self.config.base_url).rstrip('/')}/chat/completions",
                    headers=self._headers(),
                    json={
                        "model": self.config.model,
                        "temperature": self.config.temperature,
                        "response_format": {"type": "json_object"},
                        "messages": [
                            {"role": "system", "content": request.system_prompt},
                            {
                                "role": "user",
                                "content": json.dumps(request.payload, ensure_ascii=False),
                            },
                        ],
                    },
                )
                response.raise_for_status()
                return response

        try:
            response = await with_retry(send, self.config.max_retries)
            body = response.json()
            raw = body["choices"][0]["message"]["content"]
            content = json.loads(raw)
            usage = {key: int(value) for key, value in body.get("usage", {}).items()}
        except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ResponseFormatError(
                "Provider returned invalid structured JSON", detail=str(exc)
            ) from exc
        except httpx.HTTPError as exc:
            raise ProviderError("Provider request failed", detail=str(exc)) from exc
        return LLMResponse(
            request_id=request.request_id,
            model=self.config.model,
            content=content,
            usage=usage,
            raw_text=raw,
        )

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
