# 第二阶段：专用 FVN Adapter 与项目接入实施计划

## 1. 阶段目标

本阶段在公共框架 Gate A 验收通过后执行。

目标是为一部具体 FVN 建立完整的专用接入模块，使该 FVN 可以使用第一阶段完成的公共能力进行：

- 文本发现。
- 文本抽取。
- FTIF 格式转换。
- 人物和术语分析。
- LLM 翻译。
- 中间文件编辑。
- 原文件备份。
- 译文回写。
- 格式校验。
- 错误定位。
- 回退和重新回写。

本阶段不得修改公共翻译流程来迁就某一部 FVN。

专有差异必须通过 Adapter、项目配置和扩展规则实现。

---

## 2. 第二阶段的分层

第二阶段拆分为两层：

`text
第一层：引擎级 Adapter
例如 RenPyAdapter
负责理解 Ren’Py 通用语法

第二层：项目级 FVN Profile
例如 RememberTheFlowersProfile
负责当前 FVN 的自定义角色、语句、目录和校验规则
`

两层关系：

`text
具体 FVN 项目
    ↓
项目级 Profile
    ↓
引擎级 Adapter
    ↓
FTIF v1
    ↓
公共翻译框架
`

禁止为每一部 Ren’Py FVN 完整复制一套解析器。

不同 Ren’Py FVN 应复用同一个 `RenPyAdapter`，只新增各自的项目 Profile 和必要扩展。

---

## 3. 本阶段范围

### 3.1 必须完成

- Ren’Py 引擎级 Adapter。
- Ren’Py 通用文本抽取器。
- Ren’Py 通用回写器。
- Ren’Py 通用格式校验器。
- Ren’Py Lint 集成。
- 项目级 FVN Profile 接口。
- 当前目标 FVN 的 Profile。
- 当前 FVN 的自定义语句规则。
- 当前 FVN 的角色映射。
- 当前 FVN 的文件发现和排除规则。
- 当前 FVN 的场景切分规则。
- 当前 FVN 的特殊标签和占位符规则。
- 当前 FVN 的完整测试样本。
- 当前 FVN 的端到端测试。
- `Docs/adapters/renpy.md`。
- `Docs/fvn/<project-id>.md`。

### 3.2 暂不完成

- 其他游戏引擎 Adapter。
- 图片 OCR 翻译。
- 视频字幕翻译。
- 语音识别。
- 二进制封包解包。
- 自动修改游戏字体。
- 自动修复游戏 UI 宽度。
- 对未知自定义语句进行猜测式翻译。

---

## 4. 目录结构

在第一阶段目录基础上增加：

`text
src/fvn_translator/
├── adapters/
│   └── renpy/
│       ├── __init__.py
│       ├── adapter.py
│       ├── detector.py
│       ├── discovery.py
│       ├── lexer.py
│       ├── parser.py
│       ├── extractor.py
│       ├── writer.py
│       ├── validator.py
│       ├── lint.py
│       ├── models.py
│       ├── protected_tokens.py
│       └── statements/
│           ├── say.py
│           ├── menu.py
│           ├── show_text.py
│           ├── screen_language.py
│           ├── translate_function.py
│           └── custom.py
├── profiles/
│   ├── base.py
│   ├── registry.py
│   └── remember_the_flowers/
│       ├── __init__.py
│       ├── profile.py
│       ├── config.py
│       ├── character_map.py
│       ├── custom_statements.py
│       ├── scene_rules.py
│       ├── validation_rules.py
│       └── fixtures/
└── ...

Docs/
├── adapters/
│   └── renpy.md
└── fvn/
    ├── template.md
    └── remember-the-flowers.md

tests/
├── contract/
│   └── test_renpy_adapter_contract.py
├── integration/
│   └── test_remember_the_flowers_pipeline.py
└── fixtures/
    ├── renpy_generic/
    └── remember_the_flowers/
`

项目目录和类名不得在公共 `core`、`llm`、`storage`、`services` 模块中硬编码。

---

## 5. 项目级 Profile 接口

### 5.1 Profile 定位

Profile 用于描述同一引擎下不同 FVN 的项目差异。

Profile 不重新实现完整解析器。

Profile 只提供配置、映射、扩展钩子和额外校验。

### 5.2 接口草案

`python
class FVNProfile(Protocol):
    profile_id: str
    profile_version: str
    engine_adapter_id: str

    def detect(self, source_root: Path) -> ProfileDetectionResult:
        ...

    def get_file_rules(self) -> FileDiscoveryRules:
        ...

    def get_character_map(self) -> CharacterMap:
        ...

    def get_custom_text_sinks(self) -> list[CustomTextSink]:
        ...

    def get_scene_rules(self) -> SceneRules:
        ...

    def get_protected_token_rules(self) -> ProtectedTokenRules:
        ...

    def enrich_unit(
        self,
        unit: TranslationUnit,
        parse_context: ParseContext,
    ) -> TranslationUnit:
        ...

    def validate_project(
        self,
        staging_root: Path,
        units: list[TranslationUnit],
    ) -> ValidationReport:
        ...
`

### 5.3 Profile 不得执行

Profile 不得：

- 调用 LLM。
- 操作 API Key。
- 直接修改 `units.jsonl`。
- 自己管理备份。
- 自己实现断点续传。
- 直接覆盖源文件。
- 绕过 Adapter 的 staging 流程。

---

## 6. 阶段 2A：目标 FVN 调研

### 6.1 扫描项目结构

Agent 首先只读扫描目标 FVN：

- 游戏根目录。
- `game/` 目录。
- `.rpy` 文件。
- 已有 `tl/` 目录。
- `screens.rpy`。
- `options.rpy`。
- 角色定义文件。
- 自定义 Python 模块。
- 自定义语句定义。
- 字体配置。
- 语言配置。

不得在调研阶段修改任何文件。

### 6.2 输出项目清单

生成：

`text
Docs/fvn/<project-id>-inventory.md
`

至少记录：

- 项目文件数量。
- `.rpy` 文件数量。
- 每个文件大小。
- 估算可翻译文本量。
- 主要剧情文件。
- UI 文件。
- 系统文件。
- 已存在的翻译目录。
- 检测到的角色定义。
- 检测到的自定义语句。
- 检测到的自定义 Text Tag。
- 编码和换行格式。
- 可能影响回写的特殊情况。

### 6.3 建立语法样本

从目标 FVN 中为每类语法选择真实样本。

每类至少保存：

- 一个普通样本。
- 一个复杂样本。
- 一个边界样本。

样本写入测试 Fixture，不得只写在说明文档中。

### 6.4 调研验收

- 所有主要剧情目录已识别。
- 所有主要可见文本入口已识别。
- 未识别语句已形成列表。
- 没有修改源项目。

---

## 7. 阶段 2B：Ren’Py 通用 Adapter 规范

### 7.1 先完成文档

在实现代码前完成：

`text
Docs/adapters/renpy.md
`

文档必须明确：

- 支持的 Ren’Py 版本范围。
- 文件发现规则。
- 文件排除规则。
- 编码规则。
- BOM 规则。
- 换行规则。
- 注释处理。
- 字符串解析。
- Say 语句。
- Menu。
- `show text`。
- Screen Language。
- `_()` 和 `__()`。
- `extend`。
- 三引号字符串。
- 字符串插值。
- Text Tag。
- 转义字符。
- 自定义语句扩展方法。
- FTIF 映射。
- 稳定 ID。
- 回写模式。
- 格式校验。
- 已知限制。

### 7.2 未知语法策略

遇到无法识别的疑似玩家可见文本时：

1. 不自动翻译。
2. 创建 `warning` 或 `error`。
3. 保存文件和行号。
4. 保存语句摘要。
5. 提示开发者增加 Profile 规则。

不得通过扫描所有引号字符串来规避解析问题。

### 7.3 规范验收

- 文档可独立指导实现。
- 每一种语法有输入和 FTIF 输出示例。
- 每一种语法有回写示例。
- 所有未知情况有明确处理方式。

---

## 8. 阶段 2C：Ren’Py 文件发现

### 8.1 默认包含

默认扫描：

`text
game/**/*.rpy
`

### 8.2 默认排除

默认排除：

- `.rpyc`。
- `.rpymc`。
- `cache/`。
- `saves/`。
- `.git/`。
- 自动生成文件。
- 备份目录。
- staging 目录。
- 当前目标语言的 `tl/<language>/`。

### 8.3 Profile 覆盖

Profile 可以配置：

`yaml
include:
  - "game/**/*.rpy"

exclude:
  - "game/vendor/**"
  - "game/legacy/**"

categories:
  story:
    - "game/story/**"
  ui:
    - "game/screens/**"
`

### 8.4 文件记录

每个文件记录：

- 相对路径。
- 文件大小。
- SHA-256。
- 编码。
- 是否有 BOM。
- 换行类型。
- 分类。
- 抽取单元数量。

---

## 9. 阶段 2D：Ren’Py 词法扫描和解析

### 9.1 实现原则

不得使用单一正则完成解析。

至少实现能够识别以下状态的词法扫描器：

- 普通代码。
- 行注释。
- 单引号字符串。
- 双引号字符串。
- 三单引号字符串。
- 三双引号字符串。
- 转义字符。
- 括号嵌套。
- 方括号嵌套。
- 花括号内容。
- 多行语句。

### 9.2 源位置

所有解析节点必须保留：

- 文件路径。
- 起始行。
- 结束行。
- 起始列。
- 结束列。
- 原始字节区间或字符区间。
- 原始语句。

### 9.3 错误恢复

单个语句解析失败时：

- 不得终止整个项目扫描。
- 记录解析错误。
- 跳过当前安全语句边界。
- 继续后续文件。

存在解析 `fatal` 时，不允许正式 Apply。

### 9.4 测试

必须覆盖：

- 转义引号。
- 引号中的 `#`。
- 标签中的引号。
- 多行字符串。
- 连续多个字符串。
- 字符串前无空格。
- Windows CRLF。
- UTF-8 BOM。
- 文件末尾无换行。

---

## 10. 阶段 2E：通用文本抽取

### 10.1 无说话者文本

例如：

`renpy
"We had another fight."
"{i}Am I sinking?{/i}"
`

映射为：

`text
type = narration
speaker = null
`

### 10.2 角色对白

例如：

`renpy
u "Heyyy, Lance!!!"
`

映射为：

`text
type = dialogue
speaker.id = u
`

### 10.3 带属性的角色对白

例如：

`renpy
Lan2 M0305 E1T107 "UGH!"
Lan2 EARS02 M0104 E1T306P6 SWEAT"{i}Damnit...{/i}"
`

要求：

- `Lan2` 作为角色 ID。
- 中间属性保存至 `speaker.attributes`。
- 属性不得发送给 LLM 翻译。
- 属性和引号之间没有空格时也必须识别。

### 10.4 显式显示名称

例如：

`renpy
"Eileen" "Hello."
`

角色显示名称和对白拆成独立语义字段。

是否翻译角色名由项目配置决定。

### 10.5 `extend`

保留其与上一条对白的关联：

`text
type = dialogue_extension
extends_unit_id = <previous-unit-id>
`

### 10.6 `show text`

抽取玩家在画面上看到的字符串。

`with`、Transition 和显示参数不得进入译文。

### 10.7 Menu

抽取每个玩家可选文本。

条件、Jump、Call 和代码块不得翻译。

### 10.8 Screen Language

至少支持：

- `text`。
- `textbutton`。
- Screen 内的 `label`。
- `tooltip`。
- `alt`。

必须区分：

`renpy
label start:
`

和：

`renpy
screen settings():
    label "Settings"
`

### 10.9 翻译函数

抽取：

`renpy
_("Text")
__("Text")
`

不得抽取普通 Python 代码中的所有字符串。

### 10.10 玩家可见函数

支持 Profile 注册：

`yaml
custom_text_sinks:
  - function: renpy.notify
    argument: 0
    type: notification

  - function: renpy.input
    argument: 0
    type: input_prompt
`

### 10.11 普通注释

普通注释不作为翻译单元。

Profile 可配置结构化注释白名单，作为上下文：

`text
Scene
Location
Time
Chapter
Route
Translation Note
`

---

## 11. 阶段 2F：受保护内容处理

### 11.1 Text Tag

所有 `{...}` 结构默认受保护。

包括：

`text
{i}
{/i}
{b}
{/b}
{font=...}
{/font}
{size=...}
{/size}
{color=...}
{/color}
{cps=...}
{/cps}
{w}
{w=...}
{p}
{nw}
{fast}
{clear}
{#...}
`

### 11.2 插值

所有 `[...]` 插值默认受保护。

例如：

`text
[player_name]
[points]
[mood!t]
[value:.2f]
`

### 11.3 转义

必须保留：

`text
\n
\t
\"
\'
\\
%%
{{
[[
`

### 11.4 保护签名

每个单元生成：

- 标签集合。
- 标签顺序。
- 标签配对关系。
- 插值集合。
- 转义签名。

翻译后必须重新计算并比较。

### 11.5 不允许的自动修复

公共或 Adapter 校验器不得在没有确认的情况下：

- 自动补充缺失标签。
- 自动修改变量名。
- 自动猜测标签位置。

这些问题必须进入返工流程。

---

## 12. 阶段 2G：场景和上下文切分

### 12.1 场景边界候选

Ren’Py 通用 Adapter 可以识别：

- `label`。
- `scene`。
- 文件边界。
- Profile 注册的结构化注释。

### 12.2 项目 Profile 决策

Profile 必须定义：

`yaml
primary_segment: file
scene_boundaries:
  - label
  - scene
  - structured_comment
`

### 12.3 不得错误切分

以下情况不要自动建立新场景：

- 单纯 `show` 角色立绘。
- `with dissolve`。
- `pause`。
- 音乐切换。
- 临时黑屏。

除非 Profile 明确配置。

### 12.4 场景 ID

场景 ID 由稳定信息生成：

`text
<relative-file>:<label>:<scene-index>
`

不得由 LLM 生成。

---

## 13. 阶段 2H：稳定 ID 和增量重新抽取

### 13.1 `unit_id`

建议组成：

`text
<relative-file>:<label>:<statement-index>:<text-role>
`

同时保存：

- 源文本指纹。
- 原始语句指纹。
- 前后相邻语句指纹。
- 源位置。

### 13.2 重新抽取映射

源文件变化后，按照以下顺序映射旧单元：

1. 原生稳定 Translation ID。
2. 完全相同的原始语句指纹。
3. 文件、Label 和语句索引。
4. 源文本及相邻上下文指纹。
5. 无法唯一匹配时标记冲突。

### 13.3 不允许静默处理

不得把旧译文自动应用到多个候选单元。

不得在模糊匹配结果不唯一时自动选择。

### 13.4 映射状态

`text
unchanged
moved
source_changed
new
deleted
conflict
`

---

## 14. 阶段 2I：当前 FVN Profile

### 14.1 Profile 文档

建立：

`text
Docs/fvn/remember-the-flowers.md
`

必须包含：

- 项目标识。
- 引擎和版本。
- 源目录。
- 包含文件规则。
- 排除文件规则。
- 角色定义位置。
- 角色 ID 映射。
- 立绘属性形式。
- 自定义文本语句。
- 自定义函数。
- Text Tag 扩展。
- 场景切分方法。
- 术语注意事项。
- 回写模式。
- 校验命令。
- 已知限制。

### 14.2 角色映射

Profile 应从项目定义中提取角色映射。

无法自动确认的角色保留：

`json
{
  "speaker_id": "Lan2",
  "display_name": null,
  "status": "unresolved"
}
`

不得依赖 LLM 猜测角色 ID。

LLM 可以提供候选解释，但必须由用户确认。

### 14.3 已知样本

至少覆盖：

`renpy
"We had another fight."
u "Heyyy, Lance!!!"
Lan2 M0305 E1T107 "UGH!"
Lan2 EARS02 M0104 E1T306P6 SWEAT"{i}Damnit...{/i}"
centernar2 "I was{cps=3}...{/cps}{w=0.8} alone."
show text "{font=font/amyshandwriting.ttf}{size=40}Remember the Flowers{/size}"
`

### 14.4 补充样本

目标文件未覆盖的语法需要单独建立最小测试文件：

- Menu。
- Screen Language。
- `_()`。
- `__()`。
- `extend`。
- 三引号字符串。
- 插值。
- 转义引号。
- 自定义可见文本函数。

---

## 15. 阶段 2J：回写模式

### 15.1 支持两种模式

Ren’Py Adapter 设计上支持：

`text
模式 A：生成 tl/<language>/ 翻译文件
模式 B：回写源 .rpy 的 staging 副本
`

### 15.2 默认优先级

优先评估原生 `tl/` 模式。

满足以下条件时优先采用：

- 目标项目兼容 Ren’Py 原生翻译机制。
- 目标文本类型能被原生翻译文件覆盖。
- 不需要直接替换特殊自定义语句内部字符串。

### 15.3 源文件回写模式

源文件回写只允许：

- 在 staging 中生成。

- 替换已定位的字符串内容。

- 保留原始代码前缀和后缀。

- 保留缩进。

- 保留编码。

- 保留换行符。

- 保留 BOM。

不得由 LLM 输出完整 `.rpy`。

### 15.4 字符串转义

Writer 负责：

- 根据原引号样式重新转义。

- 防止 ASCII `"` 被替换为中文 `“”`。

- 处理反斜杠。

- 处理显式换行。

- 处理多行字符串。

- 检查译文是否提前结束字符串。

---

## 16. 阶段 2K：Ren’Py 专有校验

### 16.1 翻译单元校验

至少检查：

- 所有 Text Tag 是否保留。

- 标签参数是否一致。

- 标签嵌套是否合法。

- 插值是否一致。

- 受保护转义是否一致。

- 角色 ID 是否未变。

- 立绘属性是否未变。

- 原始 ASCII 引号边界是否完整。

### 16.2 文件校验

至少检查：

- 文件编码。

- BOM。

- 换行格式。

- 未闭合字符串。

- 未闭合括号。

- 异常缩进。

- Label 是否丢失。

- Jump 和 Call 目标是否改变。

- 资源标识是否被意外修改。

- 非翻译区域是否发生无关变化。

### 16.3 结构差异检查

回写前后建立规范化结构指纹。

指纹忽略允许变化的文本内容，但包含：

- 语句类型。

- 角色 ID。

- 角色属性。

- Label。

- Jump。

- Call。

- 资源名。

- 条件表达式。

结构指纹不同则至少标记为 `error`。

### 16.4 项目级校验

Profile 可以增加：

- 自定义角色属性格式检查。

- 特定标签检查。

- 固定术语检查。

- 禁止翻译的字符串检查。

- 文件数量检查。

- 关键剧情文件存在性检查。

### 16.5 问题关联

每个问题必须尽可能关联：

- `unit_id`。

- 文件。

- 起止行。

- 问题代码。

- 原文。

- 当前译文。

- 预期结构。

- 实际结构。

---

## 17. 阶段 2L：Ren’Py Lint

### 17.1 SDK 配置

项目配置允许指定：

`toml
[adapter.renpy]
sdk_path = "D:/Tools/renpy-sdk"
lint_enabled = true
`

### 17.2 执行位置

Lint 必须针对 staging 中的完整测试项目执行。

不得先覆盖正式源项目再运行 Lint。

### 17.3 结果解析

保存：

- 命令。

- Exit Code。

- 标准输出。

- 标准错误。

- 文件和行号。

- 可关联的 `unit_id`。

### 17.4 无 SDK 时

如果未配置 SDK：

- 运行内部校验。

- 标记 `RENPLY_LINT_NOT_RUN` 警告。

- 明确提示最终语法校验未完成。

不得伪装成 Lint 已通过。

---

## 18. 阶段 2M：测试

### 18.1 Fixture 分类

`text
tests/fixtures/renpy_generic/
├── valid/
├── edge_cases/
├── invalid/
└── expected_ftif/

tests/fixtures/remember_the_flowers/
├── source/
├── expected_ftif/
├── translated_units/
├── expected_output/
└── invalid_translations/
`

### 18.2 抽取黄金测试

对固定 `.rpy` 输入比较预期 FTIF。

必须比较：

- 单元数量。

- 顺序。

- 类型。

- 说话者。

- 属性。

- 原文。

- 受保护 Token。

- 源位置。

### 18.3 回写黄金测试

对固定 FTIF 译文生成 `.rpy`，与预期输出比较。

非翻译区域应进行字节级或规范化结构比较。

### 18.4 Round-trip 测试

执行：

`text
源文件
→ 抽取
→ 设置测试译文
→ 回写
→ 再次抽取
`

验证：

- 单元仍可识别。

- 角色和属性未变。

- 译文正确。

- 结构未变。

### 18.5 错误译文测试

至少构造：

- `{i}` 丢失。

- `{/i}` 丢失。

- `[player_name]` 被翻译。

- `"` 变成 `“`。

- 多余反斜杠。

- 引号未闭合。

- 属性被修改。

- Label 被修改。

- Jump 被修改。

### 18.6 全项目抽取测试

对目标 FVN 的只读副本执行完整抽取。

统计：

- 总文件。

- 总单元。

- 对白数量。

- 旁白数量。

- 菜单数量。

- UI 数量。

- 未识别候选数量。

- 解析错误数量。

### 18.7 端到端测试

使用 MockProvider 执行：

1. 项目检测。
2. 文件发现。
3. 文本抽取。
4. FTIF 生成。
5. 人物和术语生成。
6. 翻译。
7. 中间文件编辑。
8. 公共校验。
9. Ren’Py 校验。
10. 备份。
11. Staging 回写。
12. Lint。
13. 正式 Apply。
14. 回退。

测试期间不得真实调用付费 LLM。

---

## 19. 阶段实施顺序

Agent 必须按照以下顺序执行：

1. 扫描目标 FVN，生成项目清单。
2. 补充真实语法 Fixture。
3. 完成 `Docs/adapters/renpy.md`。
4. 完成 Profile 接口。
5. 完成 Ren’Py 文件发现。
6. 完成词法扫描器。
7. 完成通用解析器。
8. 完成通用文本抽取器。
9. 完成受保护 Token 解析。
10. 完成 FTIF 转换。
11. 完成场景切分。
12. 完成稳定 ID。
13. 完成目标 FVN Profile。
14. 完成 staging Writer。
15. 完成通用 Ren’Py 校验。
16. 完成项目级校验。
17. 完成 Lint 集成。
18. 完成 Adapter 契约测试。
19. 完成目标 FVN 端到端测试。
20. 更新全部文档。

不得先编写回写代码，再补抽取和数据契约。

---

## 20. 每个任务的完成要求

每个任务完成后必须：

1. 增加或更新测试。
2. 更新 `Docs/IMPLEMENTATION_STATUS.md`。
3. 运行静态检查。
4. 运行相关单元测试。
5. 运行 Adapter 契约测试。
6. 记录新增限制。
7. 不允许留下无说明的 TODO。

质量命令：

`bash
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest tests/unit
uv run pytest tests/contract
uv run pytest tests/integration
`

---

## 21. 第二阶段验收门禁 Gate B

只有以下条件全部满足，第二阶段才算完成：

- Ren’Py Adapter 不调用 LLM。

- 公共模块不存在目标 FVN 专用判断。

- 当前 FVN 差异全部位于 Profile 或配置中。

- 目标项目的主要 `.rpy` 文件可以完整扫描。

- 所有支持的玩家可见文本可以抽取。

- 未识别的疑似文本有明确报告。

- 所有 FTIF 单元具有稳定 ID。

- 角色对白、旁白和内心独白可以覆盖。

- `show text` 可以抽取。

- Menu 可以抽取。

- Screen Language 支持范围已明确。

- `{i}` 等标签能够完整保留。

- `[]` 插值能够完整保留。

- 带立绘属性的对白可以正确拆分。

- 属性和引号紧贴时可以解析。

- 回写只发生在 staging。

- 非翻译代码不会被 LLM 修改。

- 回写后能够重新解析。

- 公共校验通过。

- Ren’Py 专有校验通过。

- 已配置 SDK 时 Ren’Py Lint 通过。

- Apply 前可以备份。

- Apply 失败可以恢复。

- 回退可以恢复原始文件字节。

- 完整端到端测试通过。

- `Docs/adapters/renpy.md` 完整。

- `Docs/fvn/<project-id>.md` 完整。

- 所有测试不依赖真实付费 LLM。

---

## 22. Gate B 演示流程

Agent 必须能够完整演示：

1. 在 TUI 中选择目标 FVN 路径。
2. 自动识别 Ren’Py Adapter。
3. 自动识别目标 FVN Profile。
4. 扫描项目文件。
5. 展示包含和排除文件。
6. 抽取全部待翻译文本。
7. 展示对白、旁白、菜单和 UI 统计。
8. 展示未识别语法列表。
9. 生成人物和术语候选。
10. 使用 MockProvider 执行部分翻译。
11. 在 TUI 中修改译文。
12. 执行公共格式校验。
13. 执行 Ren’Py 专有校验。
14. 创建原文件备份。
15. 将译文写入 staging。
16. 对 staging 执行 Ren’Py Lint。
17. Apply 到测试项目副本。
18. 启动或解析测试项目。
19. 回退到翻译前版本。
20. 使用现有中间文件再次 Apply，且不重新调用 LLM。

---

## 23. 最终交付物

第二阶段最终必须交付：

`text
RenPyAdapter
RenPyExtractor
RenPyWriter
RenPyValidator
RenPyLintRunner
FVNProfile 公共接口
目标 FVN Profile
目标 FVN 项目配置
Ren’Py Adapter 契约测试
目标 FVN 端到端测试
Docs/adapters/renpy.md
Docs/fvn/<project-id>.md
Docs/fvn/<project-id>-inventory.md
完整测试 Fixture
Gate B 验收报告
`

---

## 24. Agent 执行约束

1. 第一阶段 Gate A 未通过时，不得开始本阶段。
2. 必须先完成规范和样本，再编写解析器。
3. 不得使用单一正则实现完整 Ren’Py 解析。
4. 不得抽取所有 Python 字符串。
5. 不得由 LLM 判断哪些代码需要翻译。
6. 不得由 LLM 修改完整 `.rpy`。
7. 不得直接覆盖正式源文件。
8. 不得在源文件哈希变化后静默 Apply。
9. 不得忽略未识别的疑似玩家文本。
10. 不得把具体 FVN 判断写进公共核心模块。
11. 不得为具体 FVN 复制完整 Ren’Py 解析器。
12. 项目差异必须通过 Profile、配置或扩展钩子实现。
13. 所有回写必须经过 staging、校验、备份和 Apply。
14. 所有格式错误必须关联文件和行号。
15. 所有新增规则必须具有测试样本。
16. 所有测试不得修改真实游戏目录。
17. 所有测试不得调用付费 LLM。
18. 遇到不确定语法时应停止自动处理并报告，不能猜测回写。
19. 优先保证源文件安全和格式正确，其次才是抽取覆盖率。
20. Gate B 未通过前，不得宣告当前 FVN 已正式接入。