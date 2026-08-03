# 项目总览

FVN Translator 把游戏格式处理与 LLM 翻译解耦：Adapter 抽取玩家可见文本并生成 FTIF v1，公共服务完成人物/术语整理、翻译、审校、校验和恢复，Adapter 再把译文写入 staging。源文件只由受控 Apply 服务在备份后替换。

当前公共框架提供：

- Pydantic FTIF 模型及六类 JSON Schema；
- 原子 JSON/JSONL、可重建 SQLite 索引、工作区锁、revision 和翻译缓存；
- Mock 与 OpenAI-compatible Provider、严格结构化响应、重试与安全凭证链路；
- 翻译、编辑、公共校验、备份、Apply、Rollback 服务；
- Textual TUI、DemoAdapter、契约测试和离线端到端测试。
- Ren’Py 8.x 语法 Adapter、Profile 扩展层及 Remember the Flowers - Part II 0.02 Profile。

阅读顺序：先看[架构](01-architecture.md)和[FTIF v1](02-ftif-v1.md)，开发格式适配器看[Adapter 契约](04-adapter-contract.md)与[模板](adapters/template.md)，Ren’Py 见[专有规范](adapters/renpy.md)，运行与故障恢复看[翻译流水线](06-translation-pipeline.md)和[备份/续传/回退](07-backup-resume-rollback.md)。

```powershell
uv sync --extra dev
uv run fvn-translator
```

没有 uv 时可用 `python -m pip install -e .` 安装，再执行 `fvn-translator`。仓库根文件的保留理由见[仓库目录与追踪规则](11-repository-layout.md)。
