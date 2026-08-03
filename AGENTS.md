# 项目说明

本项目是基于 FTIF v1 的可扩展 FVN LLM 翻译工具。公共层负责 TUI、Provider、翻译编排、中间文件、断点与缓存、校验、备份、Apply 和 Rollback；各游戏格式通过 Adapter 接入，LLM 不直接修改源文件。

开始工作前先阅读：

- [项目总览](Docs/00-overview.md)
- [架构与模块边界](Docs/01-architecture.md)
- [FTIF v1 公共格式](Docs/02-ftif-v1.md)
- [Adapter 对接契约](Docs/04-adapter-contract.md)
- [翻译流水线](Docs/06-translation-pipeline.md)
- [仓库目录与追踪规则](Docs/11-repository-layout.md)
- [实现状态与 Gate A](Docs/IMPLEMENTATION_STATUS.md)

# Agents 运行规范

1. 仓库内容禁止直接删除
   - Agent 清理已有源码、文档、样本或用户文件时，只能移动到 `./trash/`。
   - 此限制不阻止程序在正常运行时清理自己创建的原子写入临时文件和工作区锁；源文件替换与恢复仍必须遵循备份、哈希校验和原子替换规范。

2. Python 与依赖
   - 代码使用 Python 3.11–3.13，默认 3.12；采用 `src/fvn_translator/` 布局。
   - `pyproject.toml` 是依赖声明的唯一来源，`uv.lock` 锁定环境；不得另行维护 `requirements.txt`。
   - 没有 uv 时使用 `python -m pip install -e .` 安装项目。

3. 密钥与敏感数据
   - API Key 只允许进入系统 Keyring、环境变量或进程内临时输入；禁止写入仓库、工作区、SQLite、日志和测试样本。
   - 用户级 `providers.toml` 只保存非敏感 Provider 配置。

4. 计划类内容
   - 所有计划类内容统一放到 plan/ 文件夹内，按任务名做分隔管理。

5. 文档类内容
   - 所有技术文档和版本记录统一放到 `Docs/`，根目录只保留工具发现、构建、许可和入口所需文件。

6. 入口与质量门禁
   - 根目录 `main.py` 是便捷统一入口，正式命令入口为 `fvn-translator`。
   - 提交实现前运行 `uv run ruff check .`、`uv run ruff format --check .`、`uv run pyright`、`uv run pytest`。
   - 测试必须离线，不得调用付费 LLM。

7. 模块边界与数据安全
   - 公共包放在 `src/fvn_translator/`；`scripts/` 仅放维护命令。
   - TUI 调用 Service，Service 通过 Repository 持久化；Adapter 不调用 LLM，LLM 不接收 `adapter_data`。
   - 权威 JSON/JSONL 必须原子写入；所有人工或自动译文修改必须留下 revision；源文件替换前必须备份并检查哈希冲突。

8. Adapter 扩展
   - 公共 Adapter 放在 `src/fvn_translator/adapters/<adapter_id>/`，游戏专属配置和样本可放在对应 FVN 目录。
   - 新 Adapter 必须遵循 `Docs/04-adapter-contract.md` 并通过公共契约测试。
   - Gate A 未确认前禁止实现正式 Ren’Py 解析、回写或特有校验；
   - 当前 FVN 目标为 Remember The Flower。
