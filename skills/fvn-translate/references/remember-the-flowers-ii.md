# Remember the Flowers Part II

Profile ID：`remember-the-flowers-ii`。已核对的旧版本为 Windows 0.02、Ren’Py 8.5.3；本次安装包须重新检查版本和提取清单。

## 提取范围

```bash
uv run fvn-translator agent prepare --source work/rtf/source --workspace work/rtf/translation --name "Remember the Flowers - Part II" --source-language en --target-language zh-CN --profile remember-the-flowers-ii --source-version VERSION
```

优先阅读 `game/story/prologue.rpy`、`game/story/demo.rpy`、`game/characters/names.rpy`。UI 位于 screens、extras、credits、music display/room、options。Profile 排除既有 `tl/`、第三方 ActionEditor、资源定义、立绘、effects 和 vendor libs。

旧 0.02 提取结果为 18 个脚本、2,383 个单元，剧情文件合计 1,515 单元。它是核对线索，不是新版本必须达到的数字。特别检查动态角色显示名、音乐曲目/作者、赞助名单与制作人员署名，确认它们是否进入本次范围。

## 翻译与口吻

从人物定义读取 speaker 身份，不凭缩写猜测未知角色。`Lan2` 是 speaker，后续的 `M0305 E1T107` 等为立绘属性，不翻译。根据实际剧情建立简短人物/术语 brief，所有子代理共享。

保留悬念、失忆相关信息的揭示顺序、人物亲疏、轻松玩笑与沉重情绪之间的变化。对白自然，旁白保留原叙述视角；不提前解释未知称呼。对原文不明确的关系保持同样程度的含糊。

游戏标题可在故事/主菜单中译为目标语言，正式产品名、署名、歌曲作者、赞助者用户名和 URL 保留原文；中文标题/姓名方案以本次 brief 为准。`{i}`、`{cps}`、`{w}`、`{font}`、`{size}`、插值、直引号和显式换行由程序保护。

## 字体与运行检查

原项目包含 `{font=font/amyshandwriting.ttf}` 等显式字体标签。仅设置 `gui.text_font` 不足以显示中文。保留标签本身，使用实际 Ren’Py 版本支持的字体替换/FontGroup 设置，为原字体增加目标语言 fallback；若使用同路径替代字体，记录替代的字体文件并确保可恢复。

字体附件使用允许分发的字体，附许可证。可按已译全文字符做字体子集，检查所有中文、标点、原文残留和角色名都在 cmap 中；不得仅包含开场字符。字体与运行脚本属于成品附件，放 `work/`，不提交字体下载或译文到仓库。

抽查普通对白、姓名、含 handwriting tag 的标题、菜单和 extras。在可运行环境执行 lint/启动；Windows 安装包在 Linux 上无法直接启动时明确记录限制，仍进行脚本 round-trip 和字体覆盖检查。

## 补丁与安装说明

本游戏采用源脚本覆盖补丁：只打包改动的 `game/...rpy` 与必需字体/运行附件，不带游戏 EXE、立绘、音乐和完整原包。

说明须包含：

1. 适用的 Windows 版本、原安装包校验值、剧情和 UI 覆盖范围。
2. 关闭游戏，备份补丁清单中的同路径文件；将补丁的 `game/` 合并到 EXE 所在目录。
3. 对补丁涉及的脚本，将同名旧 `.rpyc` 移到备份目录，首次启动由引擎重编译。需要清缓存时仅移动 `game/cache/`，不要移动存档。
4. 新增文件在恢复时移走，原文件从备份还原；保留 `game/saves/` 和系统存档。
5. 实际验证结果、仍未验证的引擎/平台项目，以及上游更新后不应混用旧补丁的版本限制。

在工作目录保存游戏专属 `install-notes.md`，通过 `agent package --install-notes` 纳入说明。
