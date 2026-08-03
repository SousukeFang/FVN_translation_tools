from pathlib import Path
from typing import Literal, cast

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select

from fvn_translator.config import set_secret
from fvn_translator.models import ProviderConfig
from fvn_translator.services import ProviderService


class ProviderScreen(ModalScreen[bool]):
    CSS = """
    ProviderScreen { align: center middle; }
    #panel { width: 70%; height: auto; background: $surface; padding: 1 2; }
    Input, Select { margin-bottom: 1; }
    """
    BINDINGS = [("escape", "dismiss(False)", "关闭")]

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.service = ProviderService(path)

    def compose(self) -> ComposeResult:
        with Vertical(id="panel"):
            yield Label("Provider 非敏感配置；API Key 将写入系统 Keyring")
            yield Input(placeholder="配置名称", id="name")
            yield Select(
                [("Mock", "mock"), ("OpenAI-compatible", "openai-compatible")],
                value="mock",
                allow_blank=False,
                id="type",
            )
            yield Input(placeholder="Base URL（Mock 留空）", id="base_url")
            yield Input(value="mock", placeholder="模型", id="model")
            yield Input(placeholder="Secret ref", id="secret_ref")
            yield Input(placeholder="API Key（可留空）", password=True, id="api_key")
            with Horizontal():
                yield Button("保存并启用", id="save", variant="primary")
                yield Button("关闭", id="close")
            yield Label("", id="status")

    @on(Button.Pressed, "#save")
    def save_pressed(self) -> None:
        name = self.query_one("#name", Input).value.strip()
        provider_type = cast(
            Literal["mock", "openai-compatible"],
            str(self.query_one("#type", Select).value),
        )
        base_url = self.query_one("#base_url", Input).value.strip() or None
        secret_ref = self.query_one("#secret_ref", Input).value.strip() or None
        try:
            api_key = self.query_one("#api_key", Input).value
            if provider_type == "openai-compatible" and (not base_url or not secret_ref):
                raise ValueError("OpenAI-compatible Provider 需要 base_url 和 secret_ref")
            if api_key and not secret_ref:
                raise ValueError("保存 API Key 前必须填写 secret_ref")
            provider = ProviderConfig.model_validate(
                {
                    "name": name,
                    "type": provider_type,
                    "base_url": base_url,
                    "model": self.query_one("#model", Input).value.strip() or "mock",
                    "secret_ref": secret_ref,
                }
            )
            self.service.upsert(provider)
            self.service.switch(name)
            if api_key:
                assert secret_ref is not None
                set_secret(secret_ref, api_key)
        except Exception as exc:
            self.query_one("#status", Label).update(f"保存失败：{exc}")
            return
        self.dismiss(True)

    @on(Button.Pressed, "#close")
    def close_pressed(self) -> None:
        self.dismiss(False)
