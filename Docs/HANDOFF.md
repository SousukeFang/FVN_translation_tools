# FVN Agent 翻译交接

本轮已完成 skill 和工具开发。用户随后要求先做一次提交，真实《Remember the Flowers - Part II》汉化改在新任务中继续。

用户明确指定本游戏为**英语译为中文**；本次交付采用简体中文（`en → zh-CN`）。skill 自身支持任意语言互译，实际 Part II 任务使用上述语言方向。

## 仓库与入口

- 仓库：https://github.com/SousukeFang/FVN_translation_tools
- 本轮分支：`work`；开发提交推送至 `origin/work`，下次从该分支继续。
- 本轮工作目录：`/workspace/FVN_translation_tools`。新环境以实际 checkout 路径为准。
- 先读 `AGENTS.md`，翻译时加载 `skills/fvn-translate/SKILL.md`，再读 `references/remember-the-flowers-ii.md`。
- 开发说明：`Docs/12-agent-translation.md`；计划：`plan/agent-translation/implementation.md`。

## 已完成

1. Agent 非 API 翻译模式：程序提取、导出有上下文的任务，Agent 直接生成译文，程序严格导入；不需要翻译 Provider 或 API Key。
2. 任意语言参数贯通 Agent 与原 API/TUI 路线，默认值仍兼容 en→zh-CN。
3. 新 CLI：`agent prepare/export/import/status/validate/package`；skill 自带 `scripts/workflow.py` 是同一 CLI 的薄入口。
4. 新 AgentTranslationService：批次登记、源指纹/ID/语言/保护内容核对、响应归档、revision、幂等导入、续传和中断恢复。
5. 新 PatchService：独立 staging、重新提取与哈希核对、完整完成门禁、仅打包改变的文件与显式附件，输出 ZIP、README.md、manifest.json；不覆盖正式原游戏。
6. 未收录 FVN 的兜底：Ren’Py 用通用解析，其他可读 UTF-8 格式用 Agent 确认剧情字段的 text-spans map，支持 plain 和 json-string。
7. skill 核心流程、generic reference、Part II reference；游戏特殊要求从核心文件分离。
8. 目录整理和忽略规则。Part II 配置示例移至 `examples/remember_the_flowers/`；旧根目录样例保存在本地忽略的 `trash/layout-before-agent/`。

## 已验证

在 Linux / Python 3.12 / uv 环境执行：

```bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
uv run python scripts/validate_schemas.py
```

结果：Ruff 与格式通过，Pyright 0 errors，70 tests passed，FTIF examples valid。测试均离线，未调用付费 LLM。

独立子代理读取 skill 后实际跑通三条流程：

- 日文 Ren’Py 合成样例→法语：10 单元、6 批，提取到打包完整通过；BOM、CRLF、引号、换行、标签、插值、附件与清单哈希正确；重复导入 0 更新，续传导出 0 批。
- 通用 text-spans 日文→法语：3 单元，plain/JSON 两种 codec、附件映射、非剧情内容保持均通过。
- Part II 合成 fixture：9 单元，Profile、源版本和保留原文路径通过；它不是正式游戏翻译。

试用报告在本地 `work/skill-trial/`，不随仓库提交。上述检查验证工具链与脚本结构；真实引擎 lint、Windows 启动和字形仍是下一任务的工作。

## 未完成与输入状态

正式 Windows 安装包没有下载成功，也没有从 Google Drive 取得；真实文本的提取、术语 brief 和翻译尚未开始。本轮没有可交付的汉化补丁或下载 Page。

下载地址：https://jerichowo.itch.io/remember-the-flowers 。需要 Windows 版 Part II，先核对网页提供的文件名、游戏内版本与引擎版本。

本轮两次官网连接均被云环境策略拦截，curl 报 `CONNECT tunnel failed, response 403`。用户说已经修改策略，但最后一次 environment_status 仍返回 spec revision 2、restricted/package_managers，新策略尚未反映到实例。新任务先查当前策略，再尝试正常下载；用户也提过上传 Google Drive，但还未提供文件链接。

已有仓库 inventory 针对旧 0.02：18 个脚本、2,383 个单元，其中 prologue/demo 合计 1,515 个。数据只是旧扫描记录，不是本轮下载或汉化成果；新安装包须重新提取。

## 下一任务执行

1. 取得 Windows 安装包，计算 SHA-256，解包到 `work/rtf/source/`；源码和翻译工作区分开。
2. 读取 skill 和 Part II reference，检查剧情、UI、动态角色名、署名、字体和既有翻译，再 prepare。
3. 读实际剧情和人物定义，在工作区建立简短 `translation-brief.md`，明确中文姓名、称呼、术语和人物口吻。
4. 导出任务，正式长文本用 **GPT-5.6 Sol，low effort** 子代理直接翻译。用户最初指定 Terra/medium，确认当前工具没有 Terra 后明确改为 Sol/light；工具枚举对应 `model="gpt-5.6-sol"`、`reasoning_effort="low"`。覆盖全部任务并保持剧情语气与表达。
5. 子代理各写自己的响应文件，主 Agent 串行导入；审校术语、角色声音、情绪转折和复杂标签，再运行全量校验。
6. 准备中文字体与运行附件，执行字体覆盖、引擎 lint/启动检查；打包补丁与说明，交付文件下载链接。用户希望创建包含下载和使用说明的 Page，不能创建时直接交付文件。

典型命令（把 VERSION 换成本次确认的版本）：

```bash
uv sync --extra dev
uv run fvn-translator agent prepare --source work/rtf/source --workspace work/rtf/translation --name "Remember the Flowers - Part II" --source-language en --target-language zh-CN --profile remember-the-flowers-ii --source-version VERSION
uv run fvn-translator agent export --workspace work/rtf/translation --output work/rtf/tasks --max-chars 12000
uv run fvn-translator agent import --workspace work/rtf/translation --task work/rtf/tasks/tasks/batch-00000.json --response work/rtf/responses/batch-00000.json --model gpt-5.6-sol/low
uv run fvn-translator agent status --workspace work/rtf/translation
uv run fvn-translator agent validate --workspace work/rtf/translation
uv run fvn-translator agent package --workspace work/rtf/translation --output output/rtf/zh-CN --extra-files work/rtf/extras.json --install-notes work/rtf/install-notes.md
```

## 翻译、字体与安装细节

- `source_text` 已解码。响应中的 JSON `\n` 解码后是真换行，不应写成再转义一层的正文；原直引号、转义语义、标签数量/顺序和插值保持。源码保护签名会在 staging 回写检查。
- 不翻译 speaker ID、立绘属性、代码和路径。作者/赞助者署名、URL 等检查后原样返回 target_text，仍算完成的单元。
- 角色显示名目前不一定进入旧 Profile 的抽取范围，实际游戏需检查。源码只有编译/归档文件时先取得可解析脚本。
- 原游戏有 `{font=font/amyshandwriting.ttf}`，只改 gui.text_font 不能处理显式字体。建议 `config.font_name_map` 映射原字体到 `FontGroup`，原字体负责拉丁字符（例如 0–0x024f），CJK 字体作为默认。先构造全部 group，再更新映射，避免 FontGroup.add 把原字体当成已注册 alias。本轮所查 Ren’Py 源码中，样式字体和内嵌 font 标签都经过 font_name_map；在本次实际引擎验证后使用。
- 选用允许分发的字体并带许可证；按已译全文做子集时核对完整 cmap。字体下载、子集和运行脚本属于本地补丁附件。
- 包内保持 `game/...` 相对路径，只带改动脚本和必要附件。说明写明安装包/版本、原包 SHA-256、覆盖范围、备份与恢复方式。
- 安装至 EXE 所在游戏根目录。对应旧 `.rpyc` 移到备份，必要时移动 `game/cache/` 让引擎重建；保留存档。新增附件在恢复时移走，覆盖文件从备份还原。
- `package` 的 `--extra-files` 接受 JSON 字典：游戏内相对路径 → 本地文件路径；`--install-notes` 指向 Markdown 文本。不会自动生成字体或执行 GUI 测试。
- 通用 text-spans map 偏移是去 BOM 后、保留 CRLF 的 Python 字符索引；json-string 含完整引号。额外保护内容字段是 `protected_tokens`。

## Git 与成果放置

`work/` 放真实游戏、下载、FTIF、任务、响应、审校和字体；`output/` 放成品补丁和说明，均已忽略。后续只提交工具/reference 修复，游戏文本与翻译成果不提交。

本轮按用户要求停在开发交付。下一任务集中完成实际 Part II 汉化，继续使用已实现的 skill。
