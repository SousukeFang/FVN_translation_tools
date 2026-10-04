---
name: fvn-translate
description: Translate a furry visual novel directly with an Agent into any requested language, preserve its voice, and deliver a version-specific translation patch with installation instructions. No translation API is required.
---

# FVN Agent 翻译

未特别指定时，只向用户交付可安装的翻译补丁和说明文件；此默认规则适用于文件、下载链接和 Page 等所有交付方式。必要字体、运行脚本、许可证和校验清单随补丁打包。完整游戏、skill/工具扩展包、源码、译文工作区及内部验收文件仅在用户明确要求时作为额外交付项。

Agent 处理语义、人物口吻、术语与审校；程序处理定位、分批、导入、校验、回写和打包。使用本 skill 所在的完整仓库，执行 `uv sync --extra dev`；没有 uv 时执行 `python -m pip install -e .`。

## 1. 识别输入与参考规则

确认游戏版本、平台、原文语言和用户目标语言，以及本次接受的翻译、保留和交付范围。语言不局限于英语和中文。下载、解包、真实游戏文本和译文放仓库忽略的 `work/<game>/`，交付文件放忽略的 `output/<game>/<language>/`。

按目标游戏读取匹配 reference：

- 《Remember the Flowers - Part II》：[专属 reference](references/remember-the-flowers-ii.md)。
- 《Echo: Route 65》：[专属 reference](references/echo-route-65.md)。
- 《Khemia》：[专属 reference](references/khemia.md)。
- 《Interea》：[专属 reference](references/interea.md)。
- 《A Role to Play》：[专属 reference](references/a-role-to-play.md)。
- 其他 FVN：[通用 reference](references/generic.md)。

Echo Project 的专属 reference 共用 [引擎、字体、图像文字与交付流程](references/echo-project-renpy.md)，但分别采用真实包对应的 Profile 和 Ren’Py 版本。只有命中的 reference 及其共用规则需要加载；新游戏的处理要点写入新的 reference，核心流程继续使用本文件。

检查真实输入的引擎、剧情位置、角色定义、UI、字体与既有译文。参考中的旧版本统计只作线索，本次提取报告才是覆盖范围依据。

## 2. 提取与建立翻译上下文

在仓库根目录运行（也可将 `uv run fvn-translator` 换成 `uv run python skills/fvn-translate/scripts/workflow.py`）：

```bash
uv run fvn-translator agent prepare --source work/game/source --workspace work/game/translation --source-language en --target-language zh-CN
```

按 reference 添加 `--profile`、`--source-version`，或通用流程的 `--span-map`。查看 `intermediate/extraction_report.json`，解决提取错误和遗漏的剧情字段后再翻译。源目录与工作区分开；续传直接使用已有工作区。

阅读连贯的开场/关键场景及人物定义，整理术语、角色称呼和口吻。将采用的规则存到工作区的 `translation-brief.md`，供所有翻译子代理共享。已有 FTIF `characters.json`、`glossary.json` 可随批次提供；内容少时直接使用简短 brief，无须专门让模型生成所有元数据。

范围包含明确排除项时，分别保存接受的单元白名单和排除位置/类别，不在排除记录摘录受限内容。用 `agent export --unit-ids-file` 导出正式选定范围，正文和相邻上下文均受该白名单约束。范围外单元保留真实状态；接受范围内完成与全项目完成分开报告。用户要求排除内容留在自己的原版中，不授权将该原文复制到补丁或完整游戏分发。

### 专名与术语的处理规则

自然的目标语言表达不要求每个词都译成目标语言。先识别人物、地名、组织、品牌、装置、命名事件和称号指向的实体，再决定表达方式；这是命名实体消歧与受控术语的一致性问题。

- 用户明确要求优先；其次采用用户提供或确认的译名。已有官方译名可作为依据记录在 brief；Agent 自行拟定的旧译名不等于用户认可，不能压过新要求。
- 未指定译法的人名及世界观专名默认保留原文，不强制音译、意译或创造解释性名称。只有本任务有明确依据的例外才本地化；不自动增加双语括注或译者注。
- 普通职业、亲属称呼、物种、通用动作和描述仍按语境翻译。大小写只是线索；同形词作为姓名、命名概念或普通名词时可有不同处理，不能仅凭首字母大写或全局字符串替换决定。
- 在 brief 为候选项记录源名及实际别称、实体/普通词语境、处理方式（保留/翻译/按语境）、采用形式和例外依据。保留姓名拼写、缩写及别名差异，不合并相似姓名；称谓、英文所有格和复数等在句子层面自然处理，实体身份保持一致。
- 正文、说话人显示名、UI、制作名单中的角色引用必须一致。称号和姓名双关须结合上下文审校，保留原名的同时传达原文含义，不另加未请求的解释。

用户调整规则时，先更新共享 brief，再对受影响单元连同上下文修订，既检查旧音译/意译残留，也检查普通词误保留。修改经已登记任务导入并追加 revision；重新验证字体、混排布局和补丁，不能只替换已打包文件。

## 3. 分批直接翻译

```bash
uv run fvn-translator agent export --workspace work/game/translation --output work/game/tasks --max-chars 12000
```

读取导出的任务及 brief，用当前 Agent 或子代理直接译出：

```json
{"translations":[{"unit_id":"任务中的 ID","target_text":"目标语言译文"}]}
```

每个任务只写自己的响应文件。长文本按用户指定的模型与 effort 分配子代理；未指定时选择兼顾质量与成本的可用模型。任务正文和相邻上下文应一起阅读，避免逐句无上下文翻译；并行任务共享 brief，由主 Agent 串行导入。

忠实保留叙述视角、节奏、幽默、双关、情绪、粗口和亲密表达。用目标语言自然地表达原文；不增删剧情、不解释笑话、不统一掉人物个性。姓名和世界观术语遵循上述处理规则及本次 brief；保留专名不降低完成率，也不属于漏译。作者/赞助者署名、URL、资源路径通常原样保留；需要原样保留的可见文本也返回相同的 `target_text`，表示已经检查。

完整覆盖任务 ID。标签、插值及受保护内容按任务保留数量与顺序。`source_text` 已解码：JSON 中的 `\n` 解码后是真换行，`\t` 是 tab；不要再多转义一层。原直引号和显式换行应保持，不将源码的转义表示机械复制成正文。

```bash
uv run fvn-translator agent import --workspace work/game/translation --task work/game/tasks/tasks/batch-00000.json --response work/game/responses/batch-00000.json --model MODEL
uv run fvn-translator agent status --workspace work/game/translation
```

导入由程序核对批次、语言、源指纹、ID 和保护内容，追加 revision。失败时修正该响应再导入。续传时向新的任务目录导出，已完成单元不会重复翻译。审校修改仍通过已登记任务的响应导入，保留修改记录。

## 4. 审校与验证

检查整体完成率、术语与称呼一致性，抽读开场、角色对话、情绪转折、双关、菜单和尾声。对照 brief 检查保留专名的拼写、上下文例外及跨正文/显示名/UI 的一致性；不将原样 target_text 误判为未完成。对含标签/插值的单元与程序报告的问题逐项处理；不以无报错替代文学审校。

```bash
uv run fvn-translator agent validate --workspace work/game/translation
```

程序只写 staging，检查编码、BOM、换行、结构和回写内容。按 reference 检查目标语言字形和 UI；存在运行环境时执行引擎 lint 和启动验证。记录实际执行的检查与无法执行的项目。

## 5. 打包与交付

按对应 reference 准备字体、运行时脚本等必需附件和游戏专属安装说明。通用流程直接用译文替换已定位的剧情内容，补丁只收录改变的文件。

改变的脚本仍包含本次不允许分发的原文时，不能将整份脚本收入上述通用补丁。采用专属 reference 中经版本与范围验证的纯差量 overlay，只包含允许的目标文字、必要的安全 UI 匹配键、定位元数据及必需附件，由用户的本地原版提供未翻译内容；不绕过全量 `agent package` 门禁或将排除单元标为已完成。Echo: Route 65 的本次安排见其专属 reference 和共用交付规则。

```bash
uv run fvn-translator agent package --workspace work/game/translation --output output/game/zh-CN --install-notes work/game/install-notes.md
```

附件用 `--extra 游戏内相对路径=本地文件` 或 `--extra-files 附件映射.json`。程序输出 ZIP、`README.md` 和 `manifest.json`；默认对外交付只有补丁 ZIP 和说明文件，manifest 随补丁保存，不额外提供独立下载项。说明包含适用版本、安装路径、备份/恢复、覆盖范围与验证情况。内部验收照常执行并记录在工作区。

确认 ZIP 清单、安装说明和可下载文件后交付。用户要求 Page 时，默认只发布汉化补丁下载与面向玩家的说明：适用版本、安装/回退、覆盖范围、校验值、已知限制和许可。skill 源码、工具扩展包、内部验收文件保存在仓库或工作区，不加入补丁 Page。若上传需分卷，记录单卷/完整 ZIP 的大小、SHA-256、顺序和恢复方法，实测恢复一致后再交付；按连接器实际返回记录上传验证，不推定服务端哈希已核对。真实游戏、临时文件、翻译响应和成品不提交到 Git；工具或 reference 开发变更按用户要求提交并推送，通过仓库门禁后核对远端提交。
