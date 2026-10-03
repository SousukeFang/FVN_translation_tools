# 实现状态

更新时间：2026-10-03

## Agent 翻译模式

已完成非 API 的 Agent 批次交换、任意语言参数、精确文本区间 Adapter、补丁打包和
`skills/fvn-translate/`。CLI 支持 prepare、export、import、status、validate、package。
安装补丁只包含改变的脚本和显式附件，原游戏目录不被修改。

本轮在 Linux / Python 3.12 / uv 环境验证：Ruff、格式检查、Pyright、70 项离线测试和
FTIF Schema 示例全部通过。独立 Agent 按 skill 执行日文 Ren’Py→法语、通用
text-spans→法语与 Part II 合成 fixture 三条端到端流程，均完成批次交换、校验和打包。
前两条还核对 BOM、CRLF、非剧情内容、附件和哈希，重复导入与续传正常。

真实 Windows 安装包尚未取得，正式汉化没有开始；字体、SDK lint、启动测试及下载 Page
留待下一任务。用户本轮要求先提交开发成果，后续见 [交接文档](HANDOFF.md)。

## Gate A 状态

公共框架首版已实现并通过自动质量门禁。2026-08-03 用户明确要求进入第二阶段；此前
未单独补录的 Gate A 人工 TUI 演示仍作为历史验收记录缺口保留，不伪装成已执行。

已完成：项目骨架与 uv 锁；FTIF 模型/六类 Schema；工作区、原子存储、可重建 SQLite、锁、revision、缓存；Mock/OpenAI-compatible Provider、配置切换与 Keyring 密钥链；人物/术语提取和审校、按场景翻译与摘要、停止/续传、搜索/编辑/批量重译服务、公共校验、备份、Apply journal、自动恢复与 Rollback；DemoAdapter、Registry、契约测试；Textual Dashboard 与配置弹窗；公共规范和对接文档。

## 自动质量门禁

在 Windows、CPython 3.12.13、uv 锁定环境执行：

- `uv run ruff format --check .`：141 files already formatted；
- `uv run ruff check .`：通过；
- `uv run pyright`：0 errors, 0 warnings；
- `uv run pytest`：33 passed；
- `uv run python scripts/validate_schemas.py`：FTIF examples are valid。

已知限制/后续验收项：

- Python 3.11、3.13 与 Linux 矩阵尚待 CI 执行；本轮本地验证为 Windows/Python 3.12。
- 网络 Provider 按安全要求只做离线结构和故障测试，未使用真实 API Key 或付费调用。
- Gate A 的 20 步人工 TUI 演示尚待用户确认。

## 阶段二与 Gate B 状态

Ren’Py Adapter、Profile 接口、Remember the Flowers - Part II Profile、真实/通用 fixture、
staging Writer、专有校验、lint runner、契约/单元/集成测试和文档已经实现。真实 0.02
项目只读扫描发现 18 个目标脚本和 2,383 个单元；词法/未知 sink 为 0，staging
round-trip 校验问题为 0。

SDK lint、完整 TUI 人工演示和游戏启动仍待具备对应交互/SDK 环境后验收。详情见
[`GATE_B_ACCEPTANCE.md`](GATE_B_ACCEPTANCE.md)，因此当前不宣告最终 Gate B 已人工签收。
