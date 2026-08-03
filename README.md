# FVN Translation Tools
可扩展的 FVN LLM 翻译公共框架。它以 FTIF v1 保存可审校的中间数据，通过 Adapter 隔离游戏格式，并提供翻译、断点恢复、校验、备份、回写与回退能力。

```powershell
uv sync --extra dev
uv run fvn-translator
```

没有 uv 时可执行 `python -m pip install -e .`，再运行 `fvn-translator`。根目录 `main.py` 是未安装命令入口时的便捷启动器。

当前包含可离线演示完整流程的 DemoAdapter/MockProvider，以及 Ren’Py 8.x Adapter 和
Remember the Flowers - Part II 0.02 Profile。阶段二自动验收与仍需 SDK/人工验证的项目见
[Gate B 报告](Docs/GATE_B_ACCEPTANCE.md)；架构与格式说明见
[Docs/00-overview.md](Docs/00-overview.md)，版本记录见 [Docs/CHANGELOG.md](Docs/CHANGELOG.md)。
