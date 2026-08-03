from collections import Counter
from pathlib import Path

from platformdirs import user_config_path
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ProgressBar,
    RichLog,
    Select,
    TextArea,
)

from fvn_translator.adapters import AdapterConfig, FVNAdapter, default_registry
from fvn_translator.config import (
    ProjectConfig,
    load_project_config,
    load_providers,
)
from fvn_translator.llm import create_provider
from fvn_translator.models import Character, GlossaryEntry, Issue, TranslationUnit
from fvn_translator.services import (
    ApplyService,
    BackupService,
    EditingService,
    ExtractionService,
    MetadataService,
    ProjectService,
    RollbackService,
    SummaryService,
    TranslationPipelineService,
    TranslationService,
    ValidationService,
)
from fvn_translator.storage import (
    CacheStore,
    JSONLStore,
    MetadataRepository,
    RevisionStore,
    StateDatabase,
    UnitRepository,
    Workspace,
)
from fvn_translator.tui.screens import MetadataScreen, ProviderScreen


class TranslatorApp(App[None]):
    TITLE = "FVN Translator"
    CSS = """
    #toolbar { height: auto; }
    #workspace { width: 1fr; }
    #units { height: 1fr; }
    #editor { height: 8; }
    #log { height: 8; }
    ProgressBar { margin: 0 1; }
    """
    BINDINGS = [("q", "quit", "退出"), ("ctrl+s", "save_edit", "保存译文")]

    def __init__(self) -> None:
        super().__init__()
        self.provider_path = user_config_path("fvn-translator") / "providers.toml"
        self.providers = load_providers(self.provider_path)
        self.workspace: Workspace | None = None
        self.database: StateDatabase | None = None
        self.repository: UnitRepository | None = None
        self.selected_unit_id: str | None = None
        self.last_backup_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll():
            yield Label("工作区")
            yield Input(placeholder="translation-workspace 路径", id="workspace")
            yield Input(placeholder="FVN 源目录（包含 game/）", id="source")
            yield Select(
                [(name, name) for name in self.providers.providers],
                value=self.providers.active_provider,
                allow_blank=False,
                id="provider",
            )
            yield Button("配置 Provider", id="provider_settings")
            with Horizontal(id="toolbar"):
                yield Button("打开", id="open", variant="primary")
                yield Button("创建 FVN 项目", id="create_project")
                yield Button("创建 Demo", id="demo")
                yield Button("抽取", id="extract")
                yield Button("人物/术语", id="metadata")
                yield Button("编辑人物/术语", id="metadata_edit")
                yield Button("翻译", id="translate")
                yield Button("停止", id="stop")
                yield Button("校验", id="validate")
                yield Button("Apply", id="apply", variant="warning")
                yield Button("回退", id="rollback", variant="error")
            with Horizontal():
                yield Input(placeholder="搜索原文、译文或说话者", id="search")
                yield Button("搜索", id="search_button")
                yield Button("全部", id="search_reset")
                yield Button("重译选中", id="retranslate")
                yield Button("下个问题", id="next_issue")
            yield DataTable(id="units", cursor_type="row")
            yield TextArea(id="editor")
            yield ProgressBar(id="progress", show_eta=False)
            yield RichLog(id="log", markup=True)
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#units", DataTable)
        table.add_columns("序号", "说话者", "原文", "译文", "状态")

    @on(Select.Changed, "#provider")
    def provider_changed(self, event: Select.Changed) -> None:
        name = str(event.value)
        if name in self.providers.providers:
            self.providers.active_provider = name
            self.log_message(f"Provider 已切换为 {name}")

    def log_message(self, message: str) -> None:
        self.query_one("#log", RichLog).write(message)

    def _open(self, root: Path) -> None:
        if self.workspace:
            self.workspace.release()
        if self.database:
            self.database.close()
        self.workspace = Workspace(root)
        self.workspace.acquire()
        self.database = StateDatabase(self.workspace.state / "state.sqlite3")
        self.repository = UnitRepository(self.workspace.intermediate / "units.jsonl", self.database)
        self.refresh_units()
        self.log_message(f"已打开 {root}")

    def refresh_units(self, unit_ids: set[str] | None = None) -> None:
        if not self.repository:
            return
        table = self.query_one("#units", DataTable)
        table.clear()
        for unit in self.repository.load():
            if unit_ids is not None and unit.unit_id not in unit_ids:
                continue
            table.add_row(
                str(unit.sequence),
                unit.speaker or "",
                unit.source_text,
                unit.target_text,
                unit.translation.status.value,
                key=unit.unit_id,
            )

    def _config(self) -> tuple[ProjectConfig, FVNAdapter]:
        if not self.workspace:
            raise RuntimeError("请先打开工作区")
        config = load_project_config(self.workspace.root / "project.toml")
        return config, default_registry().create(config.adapter_id)

    @on(Button.Pressed, "#open")
    def open_pressed(self) -> None:
        root = Path(self.query_one("#workspace", Input).value).expanduser()
        self._open(root)

    @on(Button.Pressed, "#demo")
    def demo_pressed(self) -> None:
        root = (
            Path(self.query_one("#workspace", Input).value or "demo_workspace")
            .expanduser()
            .resolve()
        )
        source = root.parent / f"{root.name}_source"
        source.mkdir(parents=True, exist_ok=True)
        sample = source / "chapter.demo"
        if not sample.exists():
            sample.write_text(
                "[NARRATION] The room is quiet.\n[Lance] I need to leave.\n", encoding="utf-8"
            )
        adapter = default_registry().create("demo")
        ProjectService().create(
            root,
            ProjectConfig(project_name="Demo", source_root=source),
            adapter_version=adapter.adapter_version,
        )
        self.query_one("#workspace", Input).value = str(root)
        self._open(root)

    @on(Button.Pressed, "#create_project")
    def create_project_pressed(self) -> None:
        workspace_root = Path(self.query_one("#workspace", Input).value).expanduser().resolve()
        source_root = Path(self.query_one("#source", Input).value).expanduser().resolve()
        registry = default_registry()
        detections = []
        for adapter_id in registry.ids():
            adapter = registry.create(adapter_id)
            detection = adapter.detect(source_root)
            if detection.supported:
                detections.append((detection.confidence, adapter_id, adapter))
        if not detections:
            raise RuntimeError("未找到支持该目录的 Adapter")
        _, adapter_id, adapter = max(detections, key=lambda item: item[0])
        ProjectService().create(
            workspace_root,
            ProjectConfig(
                project_name=source_root.name,
                source_root=source_root,
                adapter_id=adapter_id,
            ),
            adapter_version=adapter.adapter_version,
        )
        self._open(workspace_root)
        self.log_message(f"已识别 Adapter：{adapter_id}")

    @on(Button.Pressed, "#extract")
    def extract_pressed(self) -> None:
        if not self.repository:
            return
        config, adapter = self._config()
        service = ExtractionService(adapter, self.repository)
        options = {**config.adapter_options, "target_language": config.target_language}
        count = service.extract(config.source_root, AdapterConfig(options=options))
        self.refresh_units()
        result = service.last_result
        issue_count = len(result.issues) if result else 0
        file_count = len(result.files) if result else 0
        self.log_message(f"抽取完成：{file_count} 个文件，{count} 个单元，{issue_count} 个解析提示")
        if result:
            stats = Counter(unit.type.value for unit in result.units)
            self.log_message(f"类型统计：{dict(sorted(stats.items()))}")
            for source_file in result.files:
                self.log_message(
                    f"包含 [{source_file.category}] {source_file.relative_path}："
                    f"{source_file.extracted_unit_count} 个单元"
                )
            all_rpy = sum(
                path.suffix.lower() == ".rpy"
                for path in (config.source_root / "game").rglob("*")
                if path.is_file()
            )
            self.log_message(f"排除脚本：{max(0, all_rpy - file_count)} 个")
        profile_id = getattr(adapter, "selected_profile_id", None)
        if profile_id:
            self.log_message(f"已识别 Profile：{profile_id}")

    @on(Button.Pressed, "#translate")
    def translate_pressed(self) -> None:
        self.translate_worker()

    @work(exclusive=True, group="translation")
    async def translate_worker(self) -> None:
        if not self.repository or not self.workspace or not self.database:
            return
        provider_name = str(self.query_one("#provider", Select).value)
        provider = create_provider(self.providers.providers[provider_name])
        service = TranslationService(
            provider,
            self.repository,
            RevisionStore(self.workspace.intermediate / "revisions.jsonl"),
            CacheStore(self.database),
            self.workspace.runs,
        )
        self.translation_service = service
        total = len(self.repository.load())
        progress = self.query_one("#progress", ProgressBar)
        progress.update(total=total, progress=0)

        def update(unit: TranslationUnit, done: int, all_units: int) -> None:
            progress.update(total=all_units, progress=done)
            self.log_message(f"[b]{unit.source_text}[/b] → {unit.target_text}")

        pipeline = TranslationPipelineService(
            service,
            SummaryService(provider),
            self.repository,
            self.workspace.intermediate / "scene_summaries.jsonl",
        )
        await pipeline.run(progress=update)
        self.refresh_units()

    @on(Button.Pressed, "#metadata")
    def metadata_pressed(self) -> None:
        self.metadata_worker()

    @on(Button.Pressed, "#metadata_edit")
    def metadata_edit_pressed(self) -> None:
        if self.workspace:
            self.push_screen(MetadataScreen(self.workspace.intermediate))

    @on(Button.Pressed, "#provider_settings")
    def provider_settings_pressed(self) -> None:
        self.push_screen(ProviderScreen(self.provider_path), self.provider_settings_closed)

    def provider_settings_closed(self, changed: bool | None) -> None:
        if not changed:
            return
        self.providers = load_providers(self.provider_path)
        select = self.query_one("#provider", Select)
        select.set_options([(name, name) for name in self.providers.providers])
        select.value = self.providers.active_provider

    @work(exclusive=True, group="metadata")
    async def metadata_worker(self) -> None:
        if not self.repository or not self.workspace:
            return
        provider_name = str(self.query_one("#provider", Select).value)
        provider = create_provider(self.providers.providers[provider_name])
        service = MetadataService(
            provider,
            MetadataRepository(self.workspace.intermediate / "characters.json", Character),
            MetadataRepository(self.workspace.intermediate / "glossary.json", GlossaryEntry),
        )
        characters, glossary = await service.extract(self.repository.load())
        self.log_message(f"人物 {len(characters)}，术语 {len(glossary)}；请检查中间文件")

    @on(Button.Pressed, "#stop")
    def stop_pressed(self) -> None:
        if hasattr(self, "translation_service"):
            self.translation_service.stop()

    @on(DataTable.RowSelected, "#units")
    def row_selected(self, event: DataTable.RowSelected) -> None:
        self.selected_unit_id = str(event.row_key.value)
        if self.repository:
            unit = next(
                item for item in self.repository.load() if item.unit_id == self.selected_unit_id
            )
            self.query_one("#editor", TextArea).text = unit.target_text

    def action_save_edit(self) -> None:
        if self.repository and self.workspace and self.selected_unit_id:
            EditingService(
                self.repository, RevisionStore(self.workspace.intermediate / "revisions.jsonl")
            ).edit(self.selected_unit_id, self.query_one("#editor", TextArea).text)
            self.refresh_units()

    @on(Button.Pressed, "#search_button")
    def search_pressed(self) -> None:
        if self.repository and self.workspace:
            service = EditingService(
                self.repository, RevisionStore(self.workspace.intermediate / "revisions.jsonl")
            )
            self.refresh_units(set(service.search(self.query_one("#search", Input).value)))

    @on(Button.Pressed, "#search_reset")
    def search_reset_pressed(self) -> None:
        self.refresh_units()

    @on(Button.Pressed, "#retranslate")
    def retranslate_pressed(self) -> None:
        if self.repository and self.workspace and self.selected_unit_id:
            EditingService(
                self.repository, RevisionStore(self.workspace.intermediate / "revisions.jsonl")
            ).mark_for_retranslation([self.selected_unit_id])
            self.translate_worker()

    @on(Button.Pressed, "#next_issue")
    def next_issue_pressed(self) -> None:
        if not self.workspace or not self.repository:
            return
        issues = JSONLStore(self.workspace.intermediate / "issues.jsonl", Issue).read()
        issue = next((item for item in issues if not item.resolved and item.unit_id), None)
        if issue and issue.unit_id:
            self.selected_unit_id = issue.unit_id
            unit = next(item for item in self.repository.load() if item.unit_id == issue.unit_id)
            self.query_one("#editor", TextArea).text = unit.target_text
            self.log_message(f"{issue.code}: {issue.message}")

    @on(Button.Pressed, "#validate")
    def validate_pressed(self) -> None:
        if self.repository and self.workspace:
            issues = ValidationService(
                self.repository, self.workspace.intermediate / "issues.jsonl"
            ).validate()
            self.refresh_units()
            self.log_message(f"校验完成：{len(issues)} 个问题")

    @on(Button.Pressed, "#apply")
    def apply_pressed(self) -> None:
        if not self.repository or not self.workspace:
            return
        config, adapter = self._config()
        backup = BackupService(self.workspace.backups)
        rollback = RollbackService(self.workspace.backups)
        self.last_backup_id = ApplyService(self.repository, backup, rollback).apply(
            adapter,
            config.source_root,
            self.workspace.staging,
            AdapterConfig(options=config.adapter_options),
        )
        self.log_message(f"Apply 完成；备份 {self.last_backup_id}")

    @on(Button.Pressed, "#rollback")
    def rollback_pressed(self) -> None:
        if self.workspace and self.last_backup_id:
            config, _ = self._config()
            RollbackService(self.workspace.backups).rollback(
                self.last_backup_id, config.source_root
            )
            self.log_message(f"已回退 {self.last_backup_id}")

    def on_unmount(self) -> None:
        if self.database:
            self.database.close()
        if self.workspace:
            self.workspace.release()
