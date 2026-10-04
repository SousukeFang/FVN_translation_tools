# A Role to Play

Profile ID：`a-role-to-play`。读取本文件后加载[共用 Echo Project 流程](echo-project-renpy.md)。官方来源：<https://echoproject.itch.io/a-role-to-play>。

## 本次确认的 Windows 输入

- 2026-10-04 官方页面标注 Windows `0.05`，实际下载文件为 `ARoletoPlay-0.051-win.zip`，463,697,209 bytes。
- SHA-256：`b688ef3c1b53eece8d009313fce2dec33ff5dafa0b5a02f8574a766bf81962c1`。
- 包根：`ARoletoPlay-0.051-win/`；`config.name="A Role to Play"`、`config.version="0.051"`。安装版本应同时说明页面版本与实际包版本，不把两者混为一谈。
- 实包为 **Ren’Py 8.0.3.22090809 / Python 3.9**：`renpy/vc_version.py` 为 `22090809`，`lib/py3-windows-x86_64/` 含 `libpython3.9.dll`。`renpy/__init__.py` 同时保留 Python 2 的 7.5.3 分支，不能只看第一处版本元组误判引擎。
- 24 个 `.rpy` 和 24 个同名 `.rpyc`，另有已配对 `game/tl/None/common.rpym` / `.rpymc`；没有 RPA 或仅编译脚本。`Week1_Garth.rpy` 是 1-byte 空文件，`script.rpy_copy` 是不被引擎加载的副本，不应当作额外章节。

## 剧情范围与专属抽取

剧情位于 `game/Week1.rpy` 和 `Week2.rpy`。`start` / `week1postgame` 进入第一周，接着跳转 `week2`；第二周含 `week2_megan`、`week2_cw` 两个分支并在 `week2_diner` 合流。按原 label、jump 与变量保留分支，不增删或合并重复场景。

Profile 排除未接入主线的开发演示 `testing_room.rpy`、`zTesting_ground.rpy`，以及 `ActionEditor.rpy`、camera / image_viewer / keymap / spline / warper 等第三方编辑器实现。后续版本必须重新核对可达性，不能把本次排除作为所有版本的永久规则。保留玩家使用的 `screens.rpy`、`gui.rpy`、`script.rpy`、`xPhone.rpy`、`zArchive.rpy`、`zmessenger.rpy`、`zGallery.rpy`、`zMusic_player.rpy` 和 `zRoll20.rpy`。

最终正式提取 13 个 `.rpy`，其中 11 个有脚本单元，共 **5,779 个脚本单元，0 errors / 0 warnings**。第一周 1,749、第二周 3,859；其余包括 UI、角色配置、Gallery、手机状态，以及 1 个保持原文的模块许可致谢单元。初次 generic 扫描 5,327 单元；专属 Profile 增加 617 个明确可见字段，移除 167 个编辑器/演示场景或样式、声音、资源参数，随后实际 Gallery 验收补入 2 条括号页码 UI，未丢失 generic 的 Week1 / Week2 剧情单元。统计是本次输入的范围证据，未来版本以新的抽取报告为准。

`game/gui.rpy` 的顶层三引号 `Kinetic Text Tags Ren'Py Module` 许可致谢并非玩家可见旁白。本次为兼容已登记任务，保留其单元 ID 和源指纹，Profile 标记 `text_class=module_license`、`player_visible=false` 并保护整段原文，译文必须原样返回；打包校验也会从源定位信息识别缺少新标记的旧工作区，拒绝改写许可。不能为排除这一单元而重新提取并打乱既有清单。

专属 sink 精确定位以下字段，不扫描所有引号：

- `msg` 第 0 参数 / `what=` 为手机消息正文，本次所选脚本 541 条。`who`、`status`、`pic`、`audio`、资源 ID 和状态控制值不翻译。
- `msg(..., choices={index: {'name': "可见选项", 'jump': "label"}})` 仅提取 `choices[index]['name']` 字面值；`jump`、字典键、元数据及动态表达式保留。支持跨行字典；本包只在已排除的演示文件有这种选项，不能计入正式主线覆盖。
- `chat.addmessage_pc` 第 2 参数为正文，前两个图标/说话人表达式保留。本包活跃调用只在已排除的演示文件，`zRoll20.rpy` 中相关例子均为注释。
- `GalleryItem` 第 0 参数 / `name=` 为展示名称；本包实际 `Sketch 1` 已提取，图片列表、thumb、locked 与 type 保留。
- `Text` 第 0 参数中的直接字面值、字符串连接片段与 `%` 左侧格式串为可见 UI，包括 13 条手机状态文本。不提取格式参数、嵌套函数参数、style/font/color。保留 `%s` 等插值及纯格式模板，不能把这些格式串当作未翻译剧情。

Screen Language `text ("literal")` 的纯括号字面值也须抽取，包括 Gallery 的动态/零页码两条。嵌套括号和既有 `_()` 支持不应重复抽取；`text (currentTrack[0])`、纯 `[title]`、条件数字/星号、连接/索引/format 表达式不能借此猜出剧情。本轮最终新建 `translation-r1-final`：原 5,777 单元按精确源区间、源指纹、文件哈希、类型和说话人逐项匹配，重新导出已登记任务导入审校译文，再补两条新译文；旧 FTIF 与 revision 全部保留，迁移映射留档，不绕过清单变化门禁。

`nm = DynamicCharacter("?", ...)` 的第 0 参数是 Python 表达式，不能译成中文显示名；本作 roster 单独保留 `nm`，避免以后遇到其 Say 语句被角色过滤漏掉。角色定义中的 `{image=gui/names/speaker_*.png}` 是图片名牌标签，完整保留，不能用脚本文字完成率推定名牌已经汉化。

```bash
uv run fvn-translator agent prepare --source work/a-role-to-play/source/ARoletoPlay-0.051-win --workspace work/a-role-to-play/translation --name "A Role to Play" --source-language en --target-language zh-CN --profile a-role-to-play --source-version "Windows 0.051 (official page 0.05; ARoletoPlay-0.051-win.zip)"
```

## 姓名、手机资源与文本语气

叙述采用 Danny 第一人称，现实朋友的口语、手机消息的随意拼写与桌游人物的角色扮演语气分别处理。人物姓名、角色扮演名、用户名和世界观专名默认保留英文；普通亲属、物种、职业、动作和描述按语境翻译。重复摔角场景及不同分支仍是独立单元，保持人物、语气和术语一致，不按重复句子跳过未登记位置。

`switch_dialogue(name=...)` 和 `Interlocutor(..., name=...)` 的名称既显示在界面上，又用来拼接 `images/phone/icon/<name>.png`。本次 22 个 `switch_dialogue` 名称全部原样检查；Profile 标记保护并在回写/打包校验中阻止改值。`Dad`、`Unknown User` 等普通显示名若汉化，应在明确的显示层映射，不修改用于头像、存档或聊天选择的源值。不要为这些绑定名称全局字符串替换。

## 图像、字体与运行验收

定制主菜单、设置页、phone 应用、手机状态、图片名牌及部分图片资源有烘焙文字。正文也用 `{image=gui/names/...}` 显示人物名；检查实际调用图像，对需要汉化的普通称呼和操作项通过单独 FTIF 注册，再制作字体/坐标验证的显示附件。作者、logo、姓名和正式曲名通常保留。图像覆盖数量和最终脚本 5,779 单元分开计数。

`gui.rpy` 默认采用 `PatuaOne-Regular.ttf`；screen 还有显式 `Belgrano-Regular.ttf` / `DejaVuSans.ttf`，桌游人物正文有 `MarkoOne-Regular.ttf` / `CarterOne-Regular.ttf`，phone 使用 `style_font`。已有 NotoEmoji-Bold 的 emoji 标签完整保留。设置的 Font Select 菜单和 `gui.rpy` 的动态字体标签可改变实际字体；添加 CJK 字体后须核对这些路径、regular/bold/italic 组合、普通/斜体旁白、手机气泡与历史记录，不只更改 gui 默认 font。

引擎共用提示不在正常抽取范围。原包已有 `translate None strings` 的 `common.rpym`，补充提示前要确认既有项目、默认语言和初始化时机，避免重复注册。使用匹配 8.0.3 的 Linux SDK 验证 Windows 包脚本，先建立原版 lint 基线；不能用这种检查声称实测 Windows EXE。

本轮 96 条引擎提示单独经过 FTIF 登记。附件在 `init 995 python` 更新已确认的 8.0.3 `StringTranslator.translations`，避免重复注册既有 None 语言条目；原 `common.rpym` 保持不变。实际 DejaVu accessibility transform 会覆盖显式 emoji 字体，需保留原 NotoEmoji、Symbols2 和 CJK face；OpenDyslexic 的原生 FontGroup 则可保持 Latin 字体并由 CJK 回退，不能仅因看到内置字体名称就强制替换。两种选择都须实渲染中文、emoji 和符号。

普通正文中的百分号在 `config.old_substitutions` 下也可能变成 printf 解析。例如本包 `10% slope` 的中文采用“百分之十”，保留数值含义并避免真正的运行异常；公共占位符没有报错不能证明引擎能够显示。

至少验收开场短信、常规/桌游对白、两条第二周分支的长句、手机归档与 Gallery、音乐播放器、主菜单/设置/历史/存读档、Font Select 切换、退出及覆盖确认。保留特殊标签、插值、原控制流；字形核对包含正文、保留姓名、UI、补充提示、图片覆盖、emoji 和快进箭头。实际运行、布局、安装 ZIP CRC/目标哈希、上传回读与 Page 下载应分别记录，未执行完整通关或 Windows 本机测试则如实说明。

## 打包与 Page 交付

目前 Profile 使用通用 staging 源码补丁流程。全部接受单元经正式任务导入并验证后，`agent package` 只收入变化的 `.rpy` 和显式附件；无需分发原游戏。安装时把 `game/` 合并到匹配原版 EXE 同级 `game/`，备份被替换的原脚本，将补丁涉及的同名旧 `.rpyc` 移到备份，并按实际需要处理 cache；保留游戏及系统存档。回退恢复原文件、移走新增附件及其编译产物。若未来接受范围有限且整份源文件有不能再分发的内容，改用本作引擎验证后的纯差量 overlay，不能放宽通用完整性门禁。

交付 Page 须包含真实补丁下载链接、官方 Windows 原版链接、适用版本与包 SHA-256、脚本/补充覆盖范围、安装/回退说明和实际验收限制。用户本次只要求汉化补丁，不额外分发完整游戏。下载、源游戏、FTIF、任务、响应、字体与成品放忽略目录；可追踪开发内容只包含 Profile、确定性语法处理、离线合成测试与 skill/reference。
