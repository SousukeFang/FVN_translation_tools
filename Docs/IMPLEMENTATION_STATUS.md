# 实现状态

更新时间：2026-10-04

## Echo Project 本轮交付与安全范围收尾

Khemia 3,517 和 Interea 2,296 脚本文本单元正式完成；完整中文字体、共用 66 提示、
Khemia 21 制作名单说明、实际安装的 Windows ZIP 已验证并按连接器上限分卷上传，
下载 Page 已回读确认。实际检查使用匹配 Linux SDK，没有 Windows 本机测试或完整通关。

Route 65 5,269 单元已在正式 FTIF 中导入并留 revision，接受文本范围 5,269 / 5,269
完成，全部提取 5,444 单元中 175 仍 pending。用户已接受 175 单元及 4 图像在其本地
原版保留英文；仅交付安全文字纯差量 overlay，不上传完整 Route 65 游戏。安全图像/
UI 覆盖通过匹配引擎检查；overlay ZIP 的 12 新附件已实际安装核验，1,540 原文件
SHA-256 全部不变。精确 7.2.2 init/lint return 0，5,231 AST + 38 UI 目标匹配；补丁
已修正 Route 名牌/对话布局并重打包/安装核对、更新同一 Drive ID，回读名称/大小/父目录。
原生最长台词/旁白/centered、Start 开场 FileSave/FileLoad/after_load 通过；5,231
Text 无异常/高度溢出，99 个 italic 边缘外伸 1–4px 位于 30px 右内边距内完整可见。
102 图像/276 Text 无异常/区域溢出，12 Show 对应核对、实际隔离执行 Carl:9；
5 菜单仅 QA NullAction 展示。clean lint 的 141 原警告与 baseline 一致、0 新增；
5,647 字形输入缺字 0。Page 最终运行段已更新，完整回读 38 blocks，三个补丁 ID、
新 SHA-256/大小、存读档及 175/4 范围一致，旧 hash 无残留。
本次接受的交付与验收已完成；全部 work 提交已快进合并并推送 main。
远程两支在 7ef0d70 核对一致、work 独有提交数为 0 后，已删除本地及远程 work；
后续收尾记录直接提交 main。真实游戏、字体、成品与中间工作区均未被 Git 追踪。

Agent 增加显式单位白名单导出，正文和上下文均限于选定范围；不改范围外状态。
text-spans 支持字面占位模式，真实变量仍可显式保护。最终重跑 Ruff check 通过、
Ruff format 的 166 个文件无需改动、Pyright 0 errors / 0 warnings，102 项离线测试
通过（1.07s）；详见 [交付与续做记录](ECHO_PROJECT_HANDOFF.md)。

纯差量 overlay 不包含原剧情脚本、编译文件、原素材或排除原文；不放宽通用 package
全量门禁。Drive 完整包按本轮连接器 100 MiB 上限使用 90 MiB 顺序分卷，本地恢复
SHA-256/ZIP CRC 已核对，上传回读名称/大小/父文件夹；工具未返回服务端哈希。
Route 65 安全选中集的公共单元校验为 0 errors、5 个已审校接受的 SMART_QUOTE
warnings，manifest 如实记录；该结果不替代最终实际渲染和存读档验收。

## Echo Project 接入

三个官方 Windows 包已下载并核对，新增 `echo-route-65`、`khemia`、`interea`
Profile 与共用/专属 skill reference。它们分别使用 Ren’Py 7.2.2、8.3.4、7.4.4；
同组作品共用文本流程，但分别验证引擎、字体与 UI。角色定义、可见输入和显式
说话人显示名已纳入抽取，样式及实现模块伪对白被排除。

正式提取为 Route 65 5,444、Khemia 3,517、Interea 2,296 个非空单元；Interea
计入经匹配引擎恢复并核验的旧编译场景。数量仅为提取范围，不代表已完成翻译。
本轮 Linux / Python 3.12 / uv 的四项质量门禁、83 项离线测试及 Schema 示例通过。
Route 65 的内容处理范围与交付限制见专属 reference；正式翻译与成品另行记录。

## Agent 翻译模式

已完成非 API 的 Agent 批次交换、任意语言参数、精确文本区间 Adapter、补丁打包和
`skills/fvn-translate/`。CLI 支持 prepare、export、import、status、validate、package。
安装补丁只包含改变的脚本和显式附件，原游戏目录不被修改。

本轮在 Linux / Python 3.12 / uv 环境验证：Ruff、格式检查、Pyright、70 项离线测试和
FTIF Schema 示例全部通过。独立 Agent 按 skill 执行日文 Ren’Py→法语、通用
text-spans→法语与 Part II 合成 fixture 三条端到端流程，均完成批次交换、校验和打包。
前两条还核对 BOM、CRLF、非剧情内容、附件和哈希，重复导入与续传正常。

正式 Windows 0.02 Demo en→zh-CN 汉化已完成：2,004 个非空单元全部导入，
其中剧情 1,511 个、角色显示名 90 个；另补充 66 条引擎 UI 文案。ATL、跨行资源、
动态 screen 误提取与空白 spacer 已修复，Part II Profile 1.1.0 保留曲目和署名。
本轮全质量门禁及 75 项离线测试通过。正文 staging 校验无错误；匹配 Linux 8.5.3
引擎运行 Windows 游戏脚本，中文字体/常用提示映射和 1,509 个普通剧情单元渲染通过。
已创建下载 Page；Windows EXE 本机启动未实测。成品和验证记录见 [交接文档](HANDOFF.md)。

根据用户补充偏好，翻译 skill 增加专名默认保留、语境消歧、译名例外及跨正文/UI/显示名一致性规范。
Part II r2 复核 398 个候选、修订 341 个单元；人物姓名与世界观专名保留英文，普通词继续译中文。
修改经登记批次导入并留存 revision，全文仍为 2,004 个已完成单元；最新版补丁信息见交接文档。

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
