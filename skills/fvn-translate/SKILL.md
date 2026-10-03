---
name: fvn-translate
description: Translate a furry visual novel directly with an Agent into any requested language, preserve its voice, and deliver a version-specific translation patch with installation instructions. No translation API is required.
---

# FVN Agent 翻译

完成目标是可安装的翻译补丁和说明文件。Agent 处理语义、人物口吻、术语与审校；程序处理定位、分批、导入、校验、回写和打包。使用本 skill 所在的完整仓库，执行 `uv sync --extra dev`；没有 uv 时执行 `python -m pip install -e .`。

## 1. 识别输入与参考规则

确认游戏版本、平台、原文语言和用户目标语言。语言不局限于英语和中文。下载、解包、真实游戏文本和译文放仓库忽略的 `work/<game>/`，交付文件放忽略的 `output/<game>/<language>/`。

《Remember the Flowers - Part II》读取 [专属 reference](references/remember-the-flowers-ii.md)。其他 FVN 读取 [通用 reference](references/generic.md)。只有命中的 reference 需要加载；新游戏的处理要点写入新的 reference，核心流程继续使用本文件。

检查真实输入的引擎、剧情位置、角色定义、UI、字体与既有译文。参考中的旧版本统计只作线索，本次提取报告才是覆盖范围依据。

## 2. 提取与建立翻译上下文

在仓库根目录运行（也可将 `uv run fvn-translator` 换成 `uv run python skills/fvn-translate/scripts/workflow.py`）：

```bash
uv run fvn-translator agent prepare --source work/game/source --workspace work/game/translation --source-language en --target-language zh-CN
```

按 reference 添加 `--profile`、`--source-version`，或通用流程的 `--span-map`。查看 `intermediate/extraction_report.json`，解决提取错误和遗漏的剧情字段后再翻译。源目录与工作区分开；续传直接使用已有工作区。

阅读连贯的开场/关键场景及人物定义，整理术语、角色称呼和口吻。将采用的规则存到工作区的 `translation-brief.md`，供所有翻译子代理共享。已有 FTIF `characters.json`、`glossary.json` 可随批次提供；内容少时直接使用简短 brief，无须专门让模型生成所有元数据。

## 3. 分批直接翻译

```bash
uv run fvn-translator agent export --workspace work/game/translation --output work/game/tasks --max-chars 12000
```

读取导出的任务及 brief，用当前 Agent 或子代理直接译出：

```json
{"translations":[{"unit_id":"任务中的 ID","target_text":"目标语言译文"}]}
```

每个任务只写自己的响应文件。长文本按用户指定的模型与 effort 分配子代理；未指定时选择兼顾质量与成本的可用模型。任务正文和相邻上下文应一起阅读，避免逐句无上下文翻译；并行任务共享 brief，由主 Agent 串行导入。

忠实保留叙述视角、节奏、幽默、双关、情绪、粗口和亲密表达。用目标语言自然地表达原文；不增删剧情、不解释笑话、不统一掉人物个性。姓名和世界观术语遵循 brief。作者/赞助者署名、URL、资源路径通常原样保留；需要原样保留的可见文本也返回相同的 `target_text`，表示已经检查。

完整覆盖任务 ID。标签、插值及受保护内容按任务保留数量与顺序。`source_text` 已解码：JSON 中的 `\n` 解码后是真换行，`\t` 是 tab；不要再多转义一层。原直引号和显式换行应保持，不将源码的转义表示机械复制成正文。

```bash
uv run fvn-translator agent import --workspace work/game/translation --task work/game/tasks/tasks/batch-00000.json --response work/game/responses/batch-00000.json --model MODEL
uv run fvn-translator agent status --workspace work/game/translation
```

导入由程序核对批次、语言、源指纹、ID 和保护内容，追加 revision。失败时修正该响应再导入。续传时向新的任务目录导出，已完成单元不会重复翻译。审校修改仍通过已登记任务的响应导入，保留修改记录。

## 4. 审校与验证

检查整体完成率、术语与称呼一致性，抽读开场、角色对话、情绪转折、双关、菜单和尾声。对含标签/插值的单元与程序报告的问题逐项处理；不以无报错替代文学审校。

```bash
uv run fvn-translator agent validate --workspace work/game/translation
```

程序只写 staging，检查编码、BOM、换行、结构和回写内容。按 reference 检查目标语言字形和 UI；存在运行环境时执行引擎 lint 和启动验证。记录实际执行的检查与无法执行的项目。

## 5. 打包与交付

按对应 reference 准备字体、运行时脚本等必需附件和游戏专属安装说明。通用流程直接用译文替换已定位的剧情内容，补丁只收录改变的文件。

```bash
uv run fvn-translator agent package --workspace work/game/translation --output output/game/zh-CN --install-notes work/game/install-notes.md
```

附件用 `--extra 游戏内相对路径=本地文件` 或 `--extra-files 附件映射.json`。输出 ZIP、`README.md` 和 `manifest.json`，说明适用版本、安装路径、备份/恢复、覆盖范围与验证情况。

确认 ZIP 清单、安装说明和可下载文件后交付。用户要求 Page 时创建包含文件下载链接和使用说明的 Page。真实游戏、临时文件、翻译响应和成品不提交到 Git；工具或 reference 开发变更按用户要求提交。
