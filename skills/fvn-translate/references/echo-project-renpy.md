# Echo Project：共用 Ren’Py 流程

本 reference 供 [Echo: Route 65](echo-route-65.md)、[Khemia](khemia.md)、[Interea](interea.md)、[A Role to Play](a-role-to-play.md) 的专属 reference 共用。先读取目标游戏 reference，再读取本文件；不要把同一制作组视为同一引擎版本或同一 UI。

## 已核对的架构

2026-10-03 核对的前三个官方 Windows 包与 2026-10-04 下载的 A Role to Play 均有可读 UTF-8 `.rpy`，无需先解包 RPA；它们同时带 `.rpyc`，原包完整性检查通过。Ren’Py 对白、旁白、菜单、screen 和 `_()` 的基础处理可复用，角色定义、故事入口、图像文字及字体必须分别处理。

| 游戏 | Windows 包 | 实包引擎 | 剧情布局 | UI |
| --- | --- | --- | --- | --- |
| Echo: Route 65 | `EchoRoute65-1.01-pc.zip` | 7.2.2 | `Saturday.rpy`、`Carl.rpy`、`Jas.rpy`、`TJ.rpy` | 旧版定制 screen，姓名和按钮大量使用图片 |
| Khemia | `Khemia-0.4-win.zip` | 8.3.4.24120703 | `a1s1`–`a1s3`、`a2s1`、`a2s2` | `gui.rpy`、gallery、music room |
| Interea | `Interea-0.4-win.zip` | 7.4.4 | `a1s1`–`a1s4`；另有仅编译的旧 `a2s2`，本轮恢复核对 | `gui.rpy` 与 screen |
| A Role to Play | `ARoletoPlay-0.051-win.zip` | 8.0.3.22090809 / Python 3.9 | `Week1.rpy`、`Week2.rpy`，第二周含 Megan/CW 分支 | 定制 UI、phone archive/messenger、Gallery、音乐播放器 |

引擎版本来自包内 `renpy/__init__.py` 或 `renpy/vc_version.py`。后续下载可能改变构建，必须重新核对 SHA-256、引擎版本和 `.rpy`/`.rpyc` 差集。Route 65 的 `config.name="Echo"`、`config.version="0.0"` 是旧内部元数据，不能代替下载包版本 1.01。

## 工作目录与确定性处理

使用 `work/echo-project/<slug>/` 保存原 ZIP、`pristine/`、独立 `source/`、`translation/`、任务、响应、字体和检查记录。`pristine/` 是未改原版，源目录与翻译工作区分开；Windows 成品在独立 `patched/` 副本上安装。真实游戏、文字、字体和交付 ZIP 不提交到 Git。

专属 Profile ID 分别为 `echo-route-65`、`khemia`、`interea`、`a-role-to-play`。共用抽取 sink 包含 Character 第一个参数/`name=`、`renpy.input`、`renpy.notify`；角色 roster 同时保留 Ren’Py 的 `centered` 等实际可用 speaker。A Role to Play 另有经明确字段定位的手机/聊天、Gallery 与 Text 状态 sink，细则见专属 reference。空显示名、资源路径、style 值、第三方实现代码、ATL 与跨行图像表达式不能成为译文任务。

先检查提取报告并按文件/type/speaker 汇总。通用无 Profile 抽取在这些实包里会把顶层 `style ...` 的 `font`、`background`、`variant`、`layout`、色值等误当对白；零错误不代表覆盖正确。专属 Profile 的角色过滤也不能遗漏 `$` 赋值、动态 speaker 或显式名字对白。对比无 Profile 清单和实际角色定义，逐项解释差异。

只有 `.rpyc` 的文件必须单独检查：在工作目录用匹配引擎可读取的反编译工具恢复、记录工具版本，核对 label 和 jump/call 的可达性。无法恢复时明确范围，不能把未扫描的编译脚本计为已完成。不要用 Ren’Py 8 SDK 直接重编译 Python 2 的 7.x 游戏。

```bash
uv run fvn-translator agent prepare --source work/echo-project/SLUG/source/GAME_ROOT --workspace work/echo-project/SLUG/translation --name "GAME" --source-language en --target-language zh-CN --profile PROFILE --source-version "WINDOWS_PACKAGE_VERSION"
uv run fvn-translator agent export --workspace work/echo-project/SLUG/translation --output work/echo-project/SLUG/tasks --max-chars 12000
```

任务按核心 skill 直接由 Agent 翻译。共享 `translation-brief.md` 记录叙事视角、角色身份、实体/普通词消歧与称呼；姓名和世界观专名默认保留原拼写。三部作品的共享人物与术语采用相同规则，未指定的译名不自行音译。作者、曲目、URL、资源路径保留；通用提示、物种、职务和普通描述按语境翻译。各代理只写自己的响应，主代理串行导入，修改保留 revision。

## 图像文字与补充提示

剧情中显示的手机短信、菜单按钮和制作名单可能已经烘焙进图像。脚本提取无法证明这些文字已覆盖。实际查看被调用的图像；需要汉化的剧情图像可用单独登记的补充 FTIF 文本制作经字体/坐标验证的运行时覆盖，或明确定位的图片附件。不要翻译图片文件名、批量替换所有图片，也不要仅据 OCR 直接交付。文字须读上下文、经任务导入保留 revision，检查所有调用状态及背景遮挡。

引擎的退出、存档覆盖/删除、读取和跳过确认来自 `renpy/common/`，不在游戏脚本范围。只登记实际玩家常用提示，复用 Agent 导入流程，补充游戏内运行脚本。先检查既有 `tl/` 中 `.rpy` 与 `.rpym` 及 `config.default_language`，避免重复 `translate None strings`。Part II 的 8.5.3 内部字典写法未经本次 7.2.2/7.4.4/8.3.4 源码与启动验证不能照搬。

## 简体中文字体与运行

使用可分发的 CJK 字体并附许可证；附件放工作目录。可按最终全部目标文字生成字体子集，cmap 核对须包含正文、姓名混排、UI、补充提示、图像覆盖、标点和原文保留字符。字体 path 大小写也需核对。

设置 `gui.text_font` 只覆盖采用 gui 的样式。旧版 Route 65 使用 `style.default.font`；Khemia screen 内有显式 `font "RobotoSlab-Medium.ttf"`；Route 65 正文含 `{font=ui/belligerent.ttf}`。保持受保护标签原样，通过对应引擎支持的 `config.font_replacement_map`/字体设置处理指定路径与 bold/italic 组合。优先补充运行脚本，避免无记录改源码字体参数。逐个版本验证 API 和初始化时机。

本轮采用完整 Noto Sans CJK SC Regular 2.004（16,437,364 bytes，SHA-256 `2c76254f6fc379fddfce0a7e84fb5385bb135d3e399294f6eeb6680d0365b74b`），不按剧情裁剪，以覆盖 Interea 的常见中文自定义姓名。CJK 字体不含原版快进三角 `U+25B8`；另附 Noto Sans Symbols2 及 OFL，只替换 `style.skip_triangle`。按实际所用字体检查完整目标字符，而非只检查正文汉字。

真实 Ren’Py 行高不能用字号估算。7.2.2 中本轮字体 22px 的行高约 35px、15px 约 25px；原生 Text 渲染检查曾发现仅靠估算漏出的溢出。按 ascent、descent、line_spacing 及实际引擎渲染尺寸布局，检查宽度、高度和各覆盖层重叠。Route 65 原固定文本框需自动扩展并与底部快捷菜单错开；名牌烘焙图原固定 `yoffset=-195` 会遮挡中文首行，须在 Route 专属 say screen 中按实际文本框布局定位并截图检查，不能只用单个 Text 的宽高验收。Khemia 制作名单用三列中文原生界面避免多行署名碰撞。

验证 staging round-trip、保护内容、未翻译结构和字体覆盖；使用匹配版本的 Linux SDK 可验证 Windows 包的游戏脚本，但不能据此声称已实测 Windows EXE。记录实际 lint、开场、各分支、菜单、长句和特殊字体渲染结果。原版 lint 问题须先建立基线，不能将原有警告全部归因于补丁。

## 补丁与完整 Windows 包

`agent package` 只打包改变的 `game/...rpy` 与显式字体/运行附件，按游戏 reference 加入安装说明。说明包含官方包名与 SHA-256、覆盖范围、补丁文件清单、备份和实际验证。补丁合并到 EXE 所在目录；补丁涉及的同名旧 `.rpyc` 移到备份，必要时移走 `game/cache/`，保留 `game/saves/` 和系统存档。回退恢复原文件并移走新增附件。

上述源码补丁会包含改变文件中的全部其余原文。若接受范围只包含安全部分，且原脚本或资产有不允许再分发的内容，改用经该引擎核验的纯差量 overlay：只附白名单目标文字、必要的安全 UI 匹配键、稳定定位/版本哈希元数据、必要运行脚本、字体及许可证，由用户的本地官方原版提供未改文字和素材。ZIP 不得夹带原剧情 `.rpy`/`.rpyc`、原图像、注释中的排除原文、任务上下文或完整游戏资产。排除记录只保存 ID、位置与类别。

overlay 的正文/菜单/可见 sink 必须逐项对应接受白名单，原标签、插值、说话人、跳转、菜单动作和排除项行为保持；核对目标数、排除数、图片覆盖集合及附件清单，使用匹配引擎验证初始化顺序和实际显示。此方式需专属实现和验收，不代表通用 `agent package` 支持未完成项目：整体 FTIF 仍如实保留 pending，完成率分别说明“接受范围”和“全部提取”。本轮 Route 65 是 5,269 / 5,269 安全文本完成、175 单元与 4 图像保留英文；仅交付安全 overlay，不上传完整游戏。

Route 65 的本轮附件打包器仅位于忽略工作目录，manifest schema 为 `fvn-safe-overlay-patch/v1`；公共全量 PatchService 与 CLI 未增加 overlay 打包命令。该包只列原包不存在的新附件，逐选中 ID 使用公共 `validate_unit`，检查排除单元 pending 且无 target，并在独立安装副本验证全部原始文件 SHA-256 不变。仅新增附件的 overlay 按自身清单安装/回退，不移动未替换的原 `.rpyc`，不照搬源码补丁的清理步骤。

用户要求且本作允许范围包含完整汉化包时，在独立原版副本实际应用最终 ZIP，核对清单中的所有目标 SHA-256，处理对应旧编译脚本后再压成 Windows ZIP。Route 65 的本次范围限制见其专属 reference。可交付的补丁与完整包提供清晰下载项；完整包按制作组/系列/语言/版本整理到 Google Drive 子文件夹，不能直接散放根目录。Page 使用真实上传链接，记录大小、校验值、安装与恢复步骤；未完成上传或运行检查不得写成已完成。

本轮 Google Drive 连接器实测对超过 100 MiB 的单文件返回 413。完整 ZIP 使用 90 MiB 字节分卷，验证按序合并 SHA-256 与原 ZIP 一致；各游戏独立子文件夹上传所有分卷、校验清单及 Windows 恢复工具。Page 必须说明分卷数量和恢复方法，不能将分卷文件夹说成单个 ZIP 直链。上传回读可核对文件名、字节数和父文件夹；工具未返回服务端校验和时，不声称核对了服务端 SHA/MD5。

此上限是本轮连接器实测约束，不等于 Google Drive 通用文件上限。100 MiB＝104,857,600 bytes，90 MiB＝94,371,840 bytes；按原完整 ZIP 的字节顺序切分，所有卷放同一个游戏版本子文件夹，名称带顺序且不覆盖不同版本。恢复工具先验证分卷数量、大小与 SHA-256，再按序流式合并到新 ZIP 并核对完整 SHA-256；本地发布验收另检查合并 ZIP 的 CRC，不声称恢复工具自身执行 CRC 检查。Page 说明先将全部分卷下载到同一目录，可用附带恢复工具合并后解压，或在全卷齐备时用 7-Zip 打开 `.zip.001` 解压；只下载首卷无法恢复完整游戏。保留上传回执以及本地合并验证，失败或未上传项不写成已交付。

最终验收分开记录 FTIF 完成状态、staging/overlay 结构校验、目标字形、原生 Text 渲染、实际开场/菜单、安装包哈希与 ZIP CRC、上传回读和 Page 链接。Linux 匹配 SDK 的脚本/渲染检查不能替代 Windows EXE 本机启动，也不能推定已完整通关；字体无缺字和抽取全量完成不能证明每张图像均已汉化。保留署名、专名、排除项和原版警告的事实按各作说明披露。
