# 项目说明

本项目是基于 FTIF v1 的可扩展 FVN 翻译工具，支持 API/TUI 和 Agent 直接翻译两种模式。公共层负责编排、中间文件、断点、校验、备份、Apply/Rollback 与补丁打包；各游戏格式通过 Adapter 接入，LLM 不直接修改源文件。

开始工作前先阅读：

- [项目总览](Docs/00-overview.md)
- [架构与模块边界](Docs/01-architecture.md)
- [FTIF v1 公共格式](Docs/02-ftif-v1.md)
- [Adapter 对接契约](Docs/04-adapter-contract.md)
- [翻译流水线](Docs/06-translation-pipeline.md)
- [仓库目录与追踪规则](Docs/11-repository-layout.md)
- [实现状态与 Gate A](Docs/IMPLEMENTATION_STATUS.md)
- [Agent 翻译模式](Docs/12-agent-translation.md)

Agent 直接翻译游戏时加载 [FVN 翻译 skill](skills/fvn-translate/SKILL.md)，只读取匹配的 reference。Part II 汉化见 [交接文档](Docs/HANDOFF.md)，A Role to Play 本轮记录见 [交接文档](Docs/AROTP_HANDOFF.md)。

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
   - 公共包放在 `src/fvn_translator/`；根 `scripts/` 仅放维护命令，skill 自带 `scripts/` 只做确定性操作或公共命令入口。
   - TUI 调用 Service，Service 通过 Repository 持久化；Adapter 不调用 LLM，LLM 不接收 `adapter_data`。
   - 权威 JSON/JSONL 必须原子写入；所有人工或自动译文修改必须留下 revision；源文件替换前必须备份并检查哈希冲突。

8. Adapter 扩展
   - 公共 Adapter 放在 `src/fvn_translator/adapters/<adapter_id>/`，游戏专属配置和样本可放在对应 FVN 目录。
   - 新 Adapter 必须遵循 `Docs/04-adapter-contract.md` 并通过公共契约测试。
   - 当前已进入 Ren’Py 与 Agent 翻译阶段；历史 Gate A/B 的人工演示缺口记录在实现状态中。
   - 当前 FVN 目标为 A Role to Play；匹配 Profile 和独立 reference 已接入。

9. Agent 翻译与交付
   - `skills/fvn-translate/SKILL.md` 保留核心流程；每个游戏的翻译与打包要求放独立 reference。
   - Agent 只输出任务对应译文，程序导入 FTIF、追加 revision、校验和打包；不通过 Provider/API 翻译。
   - 下载、原游戏、译文、运行记录放忽略的 `work/`；补丁和说明放忽略的 `output/`。这些产物不提交到仓库。
   - 未收录的 Ren’Py 使用通用 Adapter；其他可读 UTF-8 格式使用明确剧情 span map，不扫描所有引号猜剧情。
