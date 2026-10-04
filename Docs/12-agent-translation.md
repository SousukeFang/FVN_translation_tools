# Agent 直接翻译模式

本模式无需配置翻译 Provider 或 API Key。Agent 读取 JSON 任务，直接输出目标语言译文；工具仍使用 FTIF、Adapter、revision 和现有校验。原 API/TUI 模式保留，两条路径都接受项目的源语言与目标语言。

## 文件布局

```text
skills/fvn-translate/
  SKILL.md
  references/generic.md
  references/remember-the-flowers-ii.md
  scripts/workflow.py
src/fvn_translator/
  services/agent_translation_service.py
  services/patch_service.py
  adapters/text_spans/
examples/remember_the_flowers/project.example.toml
work/<game>/                    # 本地游戏、翻译工作区与响应，忽略
output/<game>/<language>/       # 补丁和说明，忽略
plan/agent-translation/         # 开发计划，追踪
```

`workflow.py` 是仓库 CLI 的薄入口；语法处理在 Adapter，状态和打包在 Service。新增游戏只需先补 reference；必要的格式能力再通过 Adapter 或 Profile 扩展。

## 工作流与命令

使用 `uv run fvn-translator agent --help` 查看命令，也可执行 `uv run python skills/fvn-translate/scripts/workflow.py agent ...`。skill 依赖完整仓库及其 Python 包，复制单个 SKILL.md 不包含运行能力。

| 命令 | 用途 |
| --- | --- |
| `prepare` | 创建工作区、自动识别 Adapter 并抽取；明确提供源语言与目标语言 |
| `export` | 导出 pending/failed 单元、相邻上下文、人物和术语；可按 ID 筛选；字符预算包含任务 JSON |
| `import` | 整批核对 ID、任务登记、源指纹、语言和保护内容，归档响应、追加 revision |
| `status` | 统计语言、单元数量和完成状态 |
| `validate` | 在 staging 回写并进行公共和格式校验 |
| `package` | 检查全量完成、源文件哈希和重新提取清单，产出 ZIP、README、manifest |

任务不包含 `adapter_data`。目标响应为 `{"translations":[{"unit_id":"...","target_text":"..."}]}`，每批必须覆盖所有 ID。原样保留的署名等返回与原文相同的译文。重复导入相同译文不增加 revision，审校修改可通过原任务再次导入。

姓名与世界观专名默认保留源文，不以全文每个词都中文作为完成标准。用户明确译名优先，普通描述和同形词按语境消歧；处理方式及例外记录在共享 brief。规则变更先按源文实体定位候选并读上下文，再通过完整登记批次重新导入；禁止对中文姓名单字全局替换或只修改交付 ZIP。详见 skill 的「专名与术语的处理规则」。

并行子代理各自写响应文件，导入串行执行。工作区锁与小型提交记录保证批次写入可恢复；JSON/JSONL 使用原子替换。已翻译单元不进入续传批次；重新导出用新的任务目录，避免覆盖正在执行的任务。

需要分阶段处理明确范围时，将单元 ID 保存为 JSON 数组，例如 `["unit-1","unit-3"]`，再运行：

```bash
uv run fvn-translator agent export --workspace work/game/translation --output work/game/selected-tasks --unit-ids-file work/game/selected-unit-ids.json
```

ID 必须是非空且不重复的字符串；未知 ID 会被拒绝，空数组表示此次不导出任何单元。
筛选仅导出指定范围内的 pending/failed 单元，相邻上下文也只包含所选 ID，已有译文仍可作为所选上下文。
任务按正常流程登记、导入和追加 revision；范围外单元保留原状态、译文和修订记录，不能将其标记为 skipped 来充当完成。
`AgentTranslationService.export_batches(..., unit_ids={...})` 提供同一能力；不传参数时沿用完整续传导出。
整体完成率和打包完整性门禁仍以全部权威单元为准，筛选不会改变项目范围。

源码转义由 Adapter 处理。Agent 使用解码后的 source_text 和 target_text；Ren’Py 的转义签名、字体标签与插值在最终 staging 校验中检查。

## 通用格式与补丁

Ren’Py 自动发现已知可见文本 sink，命中 Profile 时采用对应规则。未知引擎的可读 UTF-8 文件使用 `text-spans`：Agent 识别剧情字段，程序生成显式区间 map，Adapter 按原文和区间替换。支持 plain 与完整 JSON 字符串，不自动扫描所有引号。二进制、加密或编译资源仍需对应读取工具。

`package` 不调用会修改正式源目录的 ApplyService。它在独立 staging 校验后只收录变化文件与显式附件。`--extra` 或 `--extra-files` 添加字体/运行脚本，`--install-notes` 添加游戏说明。manifest 记录源/目标 SHA-256、语言、适用版本、覆盖率、文件清单和实际程序校验；引擎启动、字形和文学审校结论放安装说明，按实际执行情况记录。

只接受部分范围的项目仍保留全部权威单元和真实状态。范围内完成不满足通用 `package` 的全量完成条件；不能将排除项标为 skipped、填充原文译文或放宽门禁来打包。改变的源码文件会包含未改原文，若其中有本次不允许再分发的内容，需专属的纯差量 overlay，只包含接受白名单的目标文字、必要的安全 UI 匹配键、定位/哈希元数据和必要附件，由用户本地原版提供其余内容。overlay 必须另做白名单映射、排除项不变、控制流与初始化时机验证；不能夹带原剧情脚本、编译文件、原素材、注释/上下文里的排除内容或完整游戏包。具体实现与覆盖数量写入游戏 reference 和交付说明。

本轮 Echo: Route 65 接受 5,269 个安全文本单元汉化，175 单元及 4 张图像保留用户本地原文，仅交付安全 overlay；FTIF 中 175 单元继续 pending。Khemia 3,517、Interea 2,296 单元全量完成，沿用通用源码补丁与实际安装的完整 ZIP。规则与验证见 [Echo Project 共用 reference](../skills/fvn-translate/references/echo-project-renpy.md) 和 [交付记录](ECHO_PROJECT_HANDOFF.md)。

Route 65 使用忽略工作目录中的确定性附件打包器，manifest schema 为 `fvn-safe-overlay-patch/v1`；不是公共 PatchService 或 CLI 新增能力。该打包器只收原包不存在的新附件，逐选中 ID 调用公共 `validate_unit`，检查全部排除单元 pending 且无 target。在独立原版 Windows 副本实际写附件，并核对全部原始文件 SHA-256 未改变，不生成或上传完整游戏 ZIP。安装与回退只处理自身附件清单，不移走未替换的原 `.rpyc`。

上传要按连接器实际限制处理。本轮 Drive 对超过 100 MiB 的单文件返回 413，完整 ZIP 因而按 90 MiB 顺序字节分卷，并附逐卷/完整 SHA-256、大小与恢复工具。工具校验分卷大小/SHA-256 和合并 ZIP SHA-256；本地发布验收另执行 ZIP CRC 验证。先本地恢复核对，再上传各游戏子文件夹并回读名称、大小和父文件夹；未返回服务端哈希时不声称核对过。Page 明确分卷数量、全卷下载和恢复后解压方法，也可全卷齐备后用 7-Zip 打开 `.zip.001` 解压，不把文件夹链接标为单 ZIP 直链。

真实安装包、游戏脚本、FTIF、响应、下载字体与最终补丁均保存在忽略目录。测试使用合成 fixture，不调用真实翻译 API。
