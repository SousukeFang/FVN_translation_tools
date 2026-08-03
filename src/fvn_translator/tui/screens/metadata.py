import json
from pathlib import Path

from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Label, TextArea

from fvn_translator.models import Character, GlossaryEntry
from fvn_translator.storage import MetadataRepository


class MetadataScreen(ModalScreen[None]):
    CSS = """
    MetadataScreen { align: center middle; }
    #panel { width: 95%; height: 95%; background: $surface; padding: 1; }
    TextArea { height: 1fr; border: round $primary; }
    """
    BINDINGS = [("escape", "dismiss", "关闭")]

    def __init__(self, intermediate: Path) -> None:
        super().__init__()
        self.characters = MetadataRepository(intermediate / "characters.json", Character)
        self.glossary = MetadataRepository(intermediate / "glossary.json", GlossaryEntry)

    def compose(self) -> ComposeResult:
        from textual.containers import Vertical

        with Vertical(id="panel"):
            yield Label("人物（JSON 数组）")
            yield TextArea(id="characters")
            yield Label("术语（JSON 数组）")
            yield TextArea(id="glossary")
            with Horizontal():
                yield Button("验证并保存", id="save", variant="primary")
                yield Button("关闭", id="close")
            yield Label("", id="status")

    def on_mount(self) -> None:
        self.query_one("#characters", TextArea).text = json.dumps(
            [item.model_dump(mode="json", by_alias=True) for item in self.characters.load()],
            ensure_ascii=False,
            indent=2,
        )
        self.query_one("#glossary", TextArea).text = json.dumps(
            [item.model_dump(mode="json", by_alias=True) for item in self.glossary.load()],
            ensure_ascii=False,
            indent=2,
        )

    @on(Button.Pressed, "#save")
    def save_pressed(self) -> None:
        try:
            characters = [
                Character.model_validate(item)
                for item in json.loads(self.query_one("#characters", TextArea).text)
            ]
            glossary = [
                GlossaryEntry.model_validate(item)
                for item in json.loads(self.query_one("#glossary", TextArea).text)
            ]
            self.characters.save(characters)
            self.glossary.save(glossary)
        except (ValueError, TypeError, json.JSONDecodeError) as exc:
            self.query_one("#status", Label).update(f"保存失败：{exc}")
            return
        self.query_one("#status", Label).update("已原子保存")

    @on(Button.Pressed, "#close")
    def close_pressed(self) -> None:
        self.dismiss()
