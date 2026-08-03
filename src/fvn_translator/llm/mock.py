from fvn_translator.models import LLMRequest, LLMResponse, ProviderHealth


class MockProvider:
    """Deterministic, offline provider used for tests and demonstrations."""

    model = "mock-v1"

    async def test_connection(self) -> ProviderHealth:
        return ProviderHealth(healthy=True, message="offline mock ready")

    async def complete(self, request: LLMRequest) -> LLMResponse:
        if request.task in {"translation", "repair"}:
            translations = [
                {"unit_id": item["unit_id"], "target_text": f"译文：{item['source_text']}"}
                for item in request.payload.get("units", [])
            ]
            content: dict[str, object] = {"translations": translations}
        elif request.task == "summary":
            sources = [item["source_text"] for item in request.payload.get("units", [])]
            content = {"summary": "；".join(sources)[-500:]}
        elif request.task == "metadata":
            speakers = sorted(
                {
                    item.get("speaker")
                    for item in request.payload.get("units", [])
                    if item.get("speaker")
                }
            )
            content = {
                "characters": [
                    {
                        "character_id": value.lower(),
                        "names": [value],
                        "description": "待人工确认",
                        "evidence_unit_ids": [],
                    }
                    for value in speakers
                ],
                "glossary": [],
            }
        else:
            content = {}
        return LLMResponse(request_id=request.request_id, model=self.model, content=content)
