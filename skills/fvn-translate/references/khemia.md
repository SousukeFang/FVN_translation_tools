# Khemia

Profile ID：`khemia`。读取本文件后加载[共用 Echo Project 流程](echo-project-renpy.md)。官方来源：<https://echoproject.itch.io/khemia>。

## 本次确认的 Windows 输入

- 下载包：`Khemia-0.4-win.zip`，377,114,888 bytes。
- SHA-256：`692053184cf8375185d527b8ddf5150c71a2e7003e1d52e999eec7e933de9fea`。
- 包根：`Khemia-0.4-win/`；`config.name="Khemia"`、`config.version="0.4"`。
- 包内 `renpy/vc_version.py` 为 **Ren’Py 8.3.4.24120703**；不要因 Interea 或旧版本使用 7.x 而沿用 Python 2 SDK。
- 13 个可读 `.rpy`、13 个同名 `.rpyc`，没有 RPA 或仅编译脚本。

## 抽取和角色

剧情是 `game/a1s1.rpy`、`a1s2.rpy`、`a1s3.rpy`、`a2s1.rpy`、`a2s2.rpy`。`script.rpy` 定义角色与资源；UI 在 `screens.rpy`、`gui.rpy`、`gallery.rpy`、`music_room/music_room.rpy`。`music_room/01_music_room_backend.rpy` 与 `textbox_transitions.rpy` 的实现、样式和资源不应被当作剧情。

角色定义在 `script.rpy` 使用 `define ID = Character(...)`，主要为 `m`＝Scipio、`a`＝Amicus、`n`＝Neferu、`vi`＝Virginia、`ve`＝Veteris、`br`＝Brunis，以及 Ahm、Meera、Aya、Ramoses、Cassius 等。`com`＝Computer 显示名译为“计算机”，命名简称 Com 保留；`mon`＝Monitor 是为 Parents 传话的命名世界观实体，保留 Monitor，不能按普通显示器翻译。人物姓名保留英文。`narrator`、`centertext` 的 `None` 名称保留；显式姓名对白 Mother/Gaius/Flavius 需结合上下文，不合并到缩写角色。

叙述采用 Scipio 第一人称，注意焦虑、创伤、身体感受、政治礼节与亲密关系的不同语域。与 Interea 共用角色/世界观术语时保持身份与拼写一致，但不能把两作叙述者口吻统一。Adastra、Khemia 等世界观专名默认保留；普通帝国、父母、职务、物种和仪式描述按语境翻译。

2026-10-03 初次无 Profile 扫描为 3,557 单元、无 unknown 提示，仍含 screen 外 style/font/color 伪对白；五个剧情文件计 3,349 单元。数字只作预扫描线索，正式覆盖以本次专属 Profile 报告、角色显示名和补充提示登记为准。

```bash
uv run fvn-translator agent prepare --source work/echo-project/khemia/source/Khemia-0.4-win --workspace work/echo-project/khemia/translation --name "Khemia" --source-language en --target-language zh-CN --profile khemia --source-version "Windows 0.4 (Khemia-0.4-win.zip)"
```

原版有三处无效可见反斜杠转义：`a2s1.rpy:687` 的 `\I`、`a2s2.rpy:275` 和 `:772` 的 `\S`。本轮仅在 `source/Khemia-0.4-win/` 副本去掉错误反斜杠后抽取，原版 `pristine/` 和 ZIP 保持不变。每处前后文件 SHA-256、位置、修改及理由记录在 `work/echo-project/khemia/source-normalization.json`；不是对白重写或全局反斜杠替换。安装说明须区分官方原包哈希、规范化抽取源哈希和最终补丁哈希，不能让使用者误以为官方包已被修改。

## UI、图像和字体

音乐室曲名 `name=_(...)` 保留正式曲名和作者，`description=_("Main menu theme")` 等普通介绍及操作说明翻译。不能将所有音乐室 `_()` 字符串全体保留或全体翻译。Gallery 页面/按钮和解释文本列入覆盖。

`images/assets/credits01.jpg`、`credits02.jpg` 已实际查看：作者/工作室/URL 和产品 logo 保留；本轮另用补充 FTIF 登记 21 条职责、致谢及版权说明，以 `creditsbase.jpg` 原背景和原标志裁片构建原生 Composite/Text，中文三列制作名单通过真实引擎截图检查。该 21 条独立计数，不能混入脚本覆盖率。

`gui.rpy` 使用 `RobotoSlab-Medium.ttf` / `RobotoSlab-ExtraBold.ttf`；screen 多处还直接使用 Medium，音乐室使用 `gui.name_text_font`。需要同时覆盖 gui 与显式样式，并验证 regular/bold/italic 路径替换，保留箭头等 UI 字形。实际字体与许可证放工作目录及补丁附件，不提交真实字体到 Git。

## 验收和交付

以 Ren’Py 8.3.4 验证脚本、所有五段剧情、名称、centertext、Gallery、音乐室、历史/存读档/设置及常用确认提示。长段内心独白注意文本框容量和断行。默认按共用流程提供 Windows 0.4 专用补丁和说明文件，并在说明记录运行平台限制；完整游戏包仅在用户明确要求且范围允许时提供。

以下为历史验收与交付记录，不代表后续默认交付范围。

本轮最终 3,517 脚本文本单元完成，3,350 个 AST Say 的实际 Text 渲染无错误/溢出；开场实际推进 110 段对白。lint 与原版基线对比仅增加 7 条百分号接中文标点的旧格式提示，实际显示正常，记录为审查后的误报；不声称 lint 无提示或已完整通关。正式交付与待办见 [交接记录](../../../Docs/ECHO_PROJECT_HANDOFF.md)。

Windows 0.4 补丁及实际安装的完整 ZIP 已上传 Google Drive 并回读文件名、大小和父文件夹。完整 ZIP 为 5 个顺序字节分卷，需将全卷与附带恢复工具下载到同一目录，按逐卷/完整 SHA-256 校验合并后再解压；本地发布验收另检查合并 ZIP CRC 并通过。该分卷源于本轮连接器单文件 100 MiB 上限；全卷齐备也可用 7-Zip 打开 `.zip.001` 解压，只下载首卷无法恢复完整游戏。最终大小、SHA-256、下载 Page 与文件夹链接在交接记录；未实测 Windows EXE 本机启动，未取得工具未返回的服务端哈希。
