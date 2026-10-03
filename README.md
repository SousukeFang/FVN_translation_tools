# FVN Translation Tools
可扩展的 FVN 翻译框架，支持 API/TUI 和无需翻译 API 的 Agent 模式。它以 FTIF v1 保存可审校的中间数据，通过 Adapter 隔离游戏格式，并提供翻译、断点恢复、校验、备份、回写与补丁打包能力。

```powershell
uv sync --extra dev
uv run fvn-translator
```

没有 uv 时可执行 `python -m pip install -e .`，再运行 `fvn-translator`。根目录 `main.py` 是未安装命令入口时的便捷启动器。

当前包含可离线演示完整流程的 DemoAdapter/MockProvider，以及 Ren’Py 8.x Adapter 和
Remember the Flowers - Part II 0.02 Profile。阶段二自动验收与仍需 SDK/人工验证的项目见
[Gate B 报告](Docs/GATE_B_ACCEPTANCE.md)；架构与格式说明见
[Docs/00-overview.md](Docs/00-overview.md)，版本记录见 [Docs/CHANGELOG.md](Docs/CHANGELOG.md)。

Agent 翻译使用 [skills/fvn-translate/SKILL.md](skills/fvn-translate/SKILL.md)：核心流程支持任意语言互译，游戏差异放 `references/`，程序负责抽取、分批、导入、校验和打包。未收录的 Ren’Py 走通用解析，其他 UTF-8 文本格式可使用明确剧情区间的 `text-spans` Adapter。

```bash
uv run fvn-translator agent prepare --source work/game/source --workspace work/game/translation --source-language en --target-language zh-CN
uv run fvn-translator agent export --workspace work/game/translation --output work/game/tasks
# Agent 读取任务并直接生成响应后：
uv run fvn-translator agent import --workspace work/game/translation --task work/game/tasks/tasks/batch-00000.json --response work/game/responses/batch-00000.json
uv run fvn-translator agent validate --workspace work/game/translation
uv run fvn-translator agent package --workspace work/game/translation --output output/game/zh-CN
```

详细命令与模块职责见 [Agent 翻译模式](Docs/12-agent-translation.md)。真实游戏、临时工作区、译文和成果均不提交；继续 Part II 汉化见 [交接文档](Docs/HANDOFF.md)。
