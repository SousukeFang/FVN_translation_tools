# Remember the Flowers - Part II Profile

- Profile ID：`remember-the-flowers-ii`
- Profile 版本：`1.0.0`
- 引擎：Ren’Py 8.5.3（实测项目版本 0.02）
- 识别依据：`game/options.rpy` 的项目名和 `game/story/prologue.rpy`

Profile 扫描剧情、UI、credits、extras、music room、options 和角色定义；排除现有
`tl/`、ActionEditor 第三方目录、资源定义、sprite 定义、effects 和 vendor libs。
角色映射只读取 `game/characters/names.rpy` 的 `Character(...)` 定义，不用 LLM
猜测 `u` 等未知身份。`Lan2` 是 speaker ID，后续 `M0305 E1T107` 等标识符作为不可
翻译的立绘属性保存。

主要分段是文件；场景边界为 label、scene 和 `Scene/Location/Time/Chapter/Route/
Translation Note` 结构化注释。Profile 注册 `renpy.notify` 与 `renpy.input` 可见文本
sink，保护所有 Ren’Py tag、插值和转义。当前使用 staging 源副本回写；SDK lint 由
`sdk_path` 与 `lint_enabled` 配置启用。

当前规则针对 0.02 文件布局。上游版本变化后必须重新发现和核对未识别 sink；模糊
匹配不得把一个旧译文自动应用到多个候选。
