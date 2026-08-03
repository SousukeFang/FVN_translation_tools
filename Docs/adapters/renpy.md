# Ren’Py Adapter 规范

状态：阶段二实现规范。当前实现面向 Ren’Py 8.x，并以 8.5.3 项目验证；7.x
常见文本语句大体兼容，但尚未纳入引擎运行验证。

## 文件发现与解码

默认按路径排序发现 `game/**/*.rpy`，排除 `.rpyc`/`.rpymc`、cache、saves、
`.git`、backups、staging 和目标语言 `tl/<language>`。Profile 可覆盖 include、exclude
和 story/ui/characters 分类。源码必须能严格按 UTF-8 解码；单独记录 SHA-256、字节数、
BOM、CRLF/LF 和抽取单元数。Writer 保持 BOM、换行与文件末尾状态。

## 词法、语句与 FTIF

专用状态机区分普通代码、行注释、单/双/三引号、转义、圆/方/花括号嵌套和多行
字符串；正则只分类已经过词法扫描的安全语句。节点保留文件、行列、字符区间、原语句
及原字符串区间。单条错误生成带位置 issue 并从安全行边界继续；疑似可见的未知 sink
只报告 `RENPY_UNKNOWN_TEXT_SINK`，不猜测抽取。

| Ren’Py | FTIF | 不可变部分 |
|---|---|---|
| `"Narration"` | `narration` | 语句边界 |
| `e happy "Hello"` | `dialogue` | speaker 与属性 |
| `"Eileen" "Hello"` | `dialogue` + 显式显示名上下文 | 显示名默认不回写 |
| `extend "more"` | `dialogue_extension` | 上一对白关联 |
| `show text "Title" with dissolve` | `screen_text` | transition/参数 |
| menu 字面选项 | `menu_choice` | 条件、jump/call 与代码块 |
| screen `text/label/tooltip` | `ui_text` | screen 结构 |
| screen `textbutton` | `ui_button` | action |
| screen `alt` | `accessibility_text` | 其他属性 |
| `_(...)`/`__(...)` | `ui_text` | 函数与其他参数 |
| Profile 函数 sink | Profile 指定类型 | 函数调用结构 |

screen 内 `label "Settings"` 与顶层 `label start:` 由缩进上下文区分。普通 Python 字符串、
资源路径、Character/image/audio 定义不会因包含引号而抽取。Say 支持任意标识符属性、
`-SWEAT` 一类负属性，以及属性与引号紧贴。

场景边界为文件、label、scene 和 Profile 结构化注释；show、with、pause 与音乐切换不
切场景。场景 ID 为 `<path>:<label>:<scene-index>`；单元 ID 为
`renpy:<path>:<label>:<visible-index>:<role>`，只计可见语句，所以插入普通代码或注释
不改变 ID。adapter_data 另存原语句及相邻指纹、源区间、引号、属性、保护签名和文件
结构指纹，永不发送给 LLM。

## 保护、回写与校验

所有 `{...}` tag、`[...]` 插值、`\\n`/`\\t`/转义引号/反斜杠、`%%`、`{{`、`[[`
形成有顺序且保留重复次数的签名。Tag 同时检查开闭与嵌套变化；校验器不自动补标签、
修改变量或猜测位置。

当前 Writer 使用“源 `.rpy` 的 staging 副本”模式：先验证抽取时文件哈希和原字符串
内容，再按字符区间逆序替换；只写 staging，且 LLM 从不生成完整脚本。原生 `tl/`
模式仍为已评估但未实现的后续能力，因为自定义 sink 与部分 Screen Language 无法保证
被原生 tl 完整覆盖。

Adapter 校验严格 UTF-8、BOM、换行、词法、保护签名、speaker/属性、重新抽取结果和
忽略允许文本区间后的结构指纹。`RenPyLintRunner` 只以 staging 为项目目录调用 SDK；
启用 lint 时 Adapter 会先复制排除 cache/saves 的完整项目到独立 staging，再替换翻译
区间；未配置 SDK 时产生 `RENPY_LINT_NOT_RUN`，不会伪装通过。也可用
`full_staging=true` 显式准备完整 staging 而不运行 lint。

## 已知限制

- 不翻译动态表达式生成的 Screen 文本，也不猜测未知自定义语句。
- 原生 `tl/<language>` 生成和增量冲突审阅 UI 尚未实现。
- 增量重映射所需原语句/邻接指纹已保存，但公共 Repository 暂未执行交互式模糊合并。
- 内部校验不能替代引擎 lint 和实际运行测试；SDK 是否可用取决于用户配置。
