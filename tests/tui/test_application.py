import pytest
from textual.widgets import Input

from fvn_translator.config import load_project_config
from fvn_translator.tui import TranslatorApp


@pytest.mark.asyncio
async def test_dashboard_starts() -> None:
    app = TranslatorApp()
    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#workspace")
        assert app.query_one("#units")
        assert app.query_one("#progress")


@pytest.mark.asyncio
async def test_dashboard_creates_detected_renpy_project(tmp_path) -> None:
    app = TranslatorApp()
    workspace = tmp_path / "workspace"
    source = tmp_path / "source"
    game = source / "game"
    game.mkdir(parents=True)
    (game / "options.rpy").write_text('define config.name = "Fixture"\n', encoding="utf-8")
    (game / "script.rpy").write_text('label start:\n    "Hello"\n', encoding="utf-8")
    async with app.run_test() as pilot:
        app.query_one("#workspace", Input).value = str(workspace)
        app.query_one("#source", Input).value = str(source)
        await pilot.click("#create_project")
        await pilot.pause()
        config = load_project_config(workspace / "project.toml")
        assert config.adapter_id == "renpy"
        assert app.workspace is not None
