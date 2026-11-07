# The Smoke Room

Profile ID：`the-smoke-room`。官方来源：<https://thegoodnightfellowship.itch.io/the-smoke-room>。本作当前由 The Goodnight Fellowship 发行；可复用 [Ren’Py 提取、字体与验收方法](echo-project-renpy.md)，不能照搬其他作品的引擎版本、界面或覆盖统计。

## 已确认的 Windows 输入

- 2026-11-07 官方页面提供 Build 39。普通 Windows 包为 `TSR-39-pc (2).zip`；`TSR-39-pc-legacy (2).zip` 是另一构建，mac、Linux、APK 均非本次安装目标。
- 普通 PC ZIP 为 740,307,890 bytes，SHA-256 `287a78a53580463570e151161d1613cd24f31ebf5c7013e1a8ae569f45630ab6`，ZIP CRC 检查通过。保留官方下载包，不将文件名中的 `(2)` 当作不同的游戏版本。
- 根目录 `TSR-39-pc/`，`config.name="The Smoke Room"`、`config.version="39"`；`renpy/vc_version.py` 确认为 **Ren’Py 8.5.2.26010301**。
- 游戏目录有 27 份可读 `.rpy`、28 份 `.rpyc`，无 RPA；这里不计引擎 `renpy/common/` 的源码。独立的 `storage.rpyc` 为 288-byte RPC2，两 slot 解压后的 pickle AST 列表为空。该结论来自静态格式检查，没有反序列化执行；新版仍须重新核对。
- 原包共 3,993 个文件。真实下载、哈希清单、源副本、FTIF、任务和运行记录放 `work/the-smoke-room/`，不得加入 Git 或工具测试 fixture。

```bash
uv run fvn-translator agent prepare --source work/the-smoke-room/source/TSR-39-pc --workspace work/the-smoke-room/translation --name "The Smoke Room" --source-language en --target-language zh-CN --profile the-smoke-room --source-version "Windows standard PC Build 39 (TSR-39-pc (2).zip)"
```

## 结构与提取

`script.rpy` 定义角色、资源和入口，`commonroute.rpy` 为公共开场。路线分别位于 `williamroute*`、`nikroute*`、`cliffroute*`、`Murdochroute.rpy` / `murdochroute*`；各 `*select.rpy` 也有玩家文本，不能仅按 `route` 文件名筛选。保留原文件名大小写、label、跳转、菜单条件和路线状态。

除 Say、旁白、菜单、screen、`_()` 与 Character 显示名外，William 的笔记使用指定 `*_text` 等变量及 `journal_entries` 字典的 `text` 值。初始化及 `redefine_journal_entries` 的重建副本都须提取。Profile 仅登记实际可见的赋值目标；不要扫描所有赋值、字典字符串或引号。`jamesimage` 等资源名、调查顺序、路线状态与菜单控制变量不能译。

本次冻结 Profile 正式提取 55,416 单元、27 源脚本、0 issues。54,157 个引擎 Say 与 392 个菜单项目的全部位置及文本 hash 均与匹配引擎一致；菜单项目分为 313 个选项与 79 个 caption，caption 保持旁白类型。10 个原作未知反斜杠转义已通过专用模式还原真实引擎语义，无需修改官方源文件或将无意义片段强塞译文。新增明确可见赋值包含 `murdochchoices` 的 23 处文字（四个分支控制键不改）与 `investigorder` 的 9 处普通词。后续版本仍以新提取报告为准。

匹配 SDK 原版 lint 的 54,157 个 dialogue blocks / 475,010 words 只是原版规模，不能作为翻译完成量。位置覆盖和 0 issues 不替代引擎语义对照、白名单审核或实际渲染。

## 翻译上下文

Samuel 为主要第一人称视角，但不能把整条路线套作单一叙述者。Nik、Chang、Blithe 等视角及第三人称段落须按实际源文核对，保留叙述揭示顺序、悬疑、时代语境、口语与人物间的亲疏。中文自然流畅，但不增删信息、不淡化粗话、不把现代口头梗强加给原作。

人名、地名、世界观专名、正式曲名、作者署名和 URL 默认保留原拼写。`Samuel` / `Sam`、`Cliff` 的不同称呼分别保留，不自动合并。普通职业、物种和亲属称谓依语境译中文；附在人名上的 `Mrs.`、`Grandma` 等普通称呼在正文与显示名中须一致。译文规则先写进共享 `translation-brief.md`，所有子代理采用同一版本。

本轮已确认的易错项：Rowan/Byrnes 的祖辈称呼依实际母系证据为“外婆”；kit fox 为
“敏狐”，不能与沙狐混同。Sonoran、Huaxian、Batavian 等虚构词按源形保留，不改成
真实国家或语言。`Podpalacz` 与药签/拼写谜题中的外语词形保留，后文作者给出解释时
再随叙事解释，不能提前替读者揭示。普通宗教通称可沿中文惯用名，不把它们当作同名
虚构角色处理。

## 内容范围与差量交付

已核实[官方作者的非营利民间翻译许可](https://itch.io/post/12717617)，[官方账号](https://itch.io/profile/thegoodnightfellowship) 同时列出本作。许可允许为其游戏制作非官方、非营利翻译，要求不得对原作声称版权或创作所有权。此次按该明确许可制作独立差量补丁，不把“免费公开下载”等同开放许可。Page、README 和补丁许可声明均须标明非官方、非营利、原作版权及创作所有权归原作者，并链接许可原帖。

本次实际目标为：完整处理可提供的剧情与界面译文，确实无法处理的内容保留玩家本地原文，另附可导出未译原文、填写译文、校验并生成个人补丁的脚本。不能用仅界面补丁或空工具包代替剧情汉化成品。补丁不包含原游戏，玩家自行下载匹配原版安装。

实际检查确认本作含成人露骨性描写；本次从下载作品取得的此类内容不代译。普通成年职业讨论、非露骨恋情或双关、粗话、非性裸体不因单个词语自动剔除；逐场审查，最大限度处理可提供内容。任何涉及未成年人的性内容不翻译。审核记录只保存位置、类别、哈希及判断状态，不摘录排除原文。关键词仅用于定位，不构成安全白名单；未审核部分不能算已接受或已完成。

对已审查且接受的单位使用 `agent export --unit-ids-file`，正文和相邻上下文均受白名单约束，正式导入并保留 revision。范围外单位保持真实 pending 状态，不以原文译文、skipped 或手改状态制造全作完成。

当整份源码含不允许随补丁分发的原文时，不能打包完整 `.rpy` / `.rpyc`。使用经过验证的目标文字差量：仅包含白名单目标文字、精确位置、版本/哈希元数据和必要字体/运行附件，由玩家本地原版提供其余内容。原版脚本不进入交付物，公共 `agent package` 的全量门禁不放宽。安装前核对整份源文件哈希，错版停止；恢复须有独立备份并核对已安装文件，不能覆盖玩家后续修改。

范围、正式译文数、原文保留数、已审查与未审核部分必须分别记录。只以最终实际完成的白名单和补丁为交付依据，不能把尚未审查的范围或技术草稿当作已完成汉化。

### 目标文字字节差量

新增确定性 helper 不改变公共 `agent package` 的门禁：

```bash
uv run python skills/fvn-translate/scripts/build_renpy_delta.py --workspace work/the-smoke-room/translation --source work/the-smoke-room/source/TSR-39-pc --unit-ids-file work/the-smoke-room/accepted-unit-ids.json --output work/the-smoke-room/delta-build-r1 --patch-id TSR-39-zh-CN-r1 --runtime-guard renpy/vc_version.py --runtime-guard TSR.exe --install-notes work/the-smoke-room/install-notes.md
```

字体/运行附件按实际清单添加重复的 `--extra 游戏相对路径=本地文件`；仅接受原包不存在的新路径，检查 Windows 大小写碰撞。输出目录每次须全新。helper 重提取核对源清单、精确定位与 revision，校验全部选中目标，并与独立 staging 的写入结果逐字节比较；对外仅输出目标 replacement、字节位置与哈希，不含原文脚本、上下文或排除原文。

普通 PC 与 legacy 的 27 个 `.rpy` 完全相同，但 legacy 为 Ren’Py 8.1.3；仅脚本 hash 无法识别。两项独立 runtime guards 必须附上，安装、导出与个人补丁均在写入前验证引擎/EXE；runtime 文件只读，不替换、不回退。不能等游戏启动才由字体附件报错。

将输出目录的安装器、`patch.json`、payload 和玩家说明一起打 ZIP，内部 staging 不入包。玩家解压到 EXE 同级后执行 `install.cmd`，由 Windows 自带 PowerShell 安装，无需 Python 或管理员权限。全部源哈希/附件预检后才备份并替换本地 `.rpy`，同名 `.rpyc` 移入 `.fvn-backups/<patch-id>/`；这不是只合并 `game/` 的 AST overlay，安装说明不得混用。

`uninstall.cmd` 核对脚本/附件与备份后恢复原版，保留备份和移出的生成文件；玩家后续改过文件时拒绝静默覆盖。state 保存后的中断可回退；准备备份但还无 state 时游戏尚未改写，保留部分备份并优先在新解压原版中重装。同一补丁 ID 成功回退后重装，须先把该备份子目录移到游戏外归档。Linux 便携 PowerShell 的合成安装/回退检查不等于 Windows PowerShell 5.1 本机测试。

### 本地手工补译

`local_renpy_translation.py` 是 Python 3.11+ 标准库单文件工具，不依赖完整仓库或翻译 API。
先按最终实际完成白名单生成无原文定位目录：

```bash
python skills/fvn-translate/scripts/local_renpy_translation.py build-catalog --units work/the-smoke-room/translation/intermediate/units.jsonl --source work/the-smoke-room/source/TSR-39-pc --base-patch work/the-smoke-room/delta-build-r1 --output work/the-smoke-room/delta-build-r1/source-catalog.json
```

交付目录只含单位 ID、位置、类型、引号/模式与 hash，不含 source_text、raw、上下文或排除原文。玩家执行 export 时从自己的原版或经 hash 核验的备份读取，默认跳过最终补丁中已完成及已审查原样保留的单位；JSONL 的 `target_text:null` 表示未填，填写目标字符串后校验源指纹、ID、标签/插值和语义转义。未曾补译的空项保留原文，null 不清空已有个人译文。个人差量保留基础补丁全部译文、字体和 runtime guards，只合并玩家填写项。导出文件已存在时默认拒绝覆盖，保留玩家手工内容。

`apply --game-root 游戏目录 --translations untranslated.jsonl` 完成校验、生成和切换安装；
`rollback --game-root 游戏目录` 回退当前生效版本。连续使用同一 JSONL 可继续补译，
相同内容重复应用不写游戏。活动指针为 `.fvn-active-translation.json`，个人包在
`.fvn-personal/`，备份和已归档备份分别为 `.fvn-backups/` 与 `.fvn-backup-history/`；
这些目录一起保留。应用失败按实际文件和备份状态恢复旧版本，不能仅凭卸载进程的
返回状态断定是否已移除旧中文。回退仅接受原版/已安装的已知 hash，拒绝第三态、坏
备份与 runtime 变动。突然终止进程可能保留锁和 journal，须按记录恢复，不能声称所有
中断均自动恢复。

已用个人补译的目录回退后，仍用 apply 重新应用已保存的 JSONL。不要运行旧根目录
基础安装器而留下指向旧个人包的活动记录；若要只装基础汉化，使用新解压的原版目录。

用户要求执行脚本后可回写，最终前端须提供明确导出、校验、回写/回退操作，不以仅生成无法安装的草稿代替。源版本或保护内容失配时在游戏写入前停止；个人补译文件只在玩家本地读取/生成，不自动联网、上传或发布。最终 Windows 工具包可附官方嵌入式 Python 与许可证，免除安装依赖；仍分别记录 Linux 验证与 Windows 本机未执行的事实。

## 字体、界面与运行

`gui.rpy` 的字体由 `gui.preference` 选择，正文、姓名和界面分别使用 Libre Baskerville / Playfair Display；部分 Character 还有显式 `what_font="sin.ttf"`。须检查 Font Select、正文、历史记录、笔记、菜单和特殊角色字体。只修改 `gui.text_font` 不足以保证中文覆盖。

使用可分发的中文字体并附许可证，保留原资源与作者署名。核对全部正式目标文字、英文专名、标点、标签与符号的 cmap，匹配引擎检查实际渲染尺寸和中文换行。图像文字单独审核和登记；脚本完成率不能作为图片汉化证据。

本版主导航与返回按钮原为 PNG 英文，无法靠 FTIF 文本替换改变。新增独立 screen
覆盖将其改为中文 textbutton，复用功能 UI 字典；原 Action、main_menu/replay/pc
分支、Return、viewport/vpgrid/transclude 必须逐项同源核对。保留原图片和游戏逻辑，
两个字体偏好均需实际点击与尺寸验收。最终附件映射共 9 个新路径，含中文字体、许可、
引擎 UI 字典及三个运行脚本；剧情插图内文字未重绘。

使用官方匹配的 Linux 8.5.2 SDK 检查 Windows 包脚本，先建立原版 lint 基线，再比较补丁。原版 lint exit 0 但存在缺图、旧标签、过时图像操作及不可达语句诊断，不能将 exit 0 写成原版零警告。8.5.2 的对白 AST 主要为继承 `Say` 的 `TranslateSay`；不能仅按类名等于 `Say` 判断覆盖。

至少检查开场、已翻译的分支/长句、菜单、笔记及其重建、主菜单/设置/历史/存读档、退出与覆盖提示。Linux SDK 验证不等于 Windows EXE 本机测试，抽样或批量 Text 渲染也不等于完整通关。

## Drive 和 Page

历史交付位于 [Game Patch](https://drive.google.com/drive/folders/1Tef7XKdv-gr1qKjMjiuY_2qIvHlJ2bGJ)，按作品/版本新建 `The Smoke Room` 子文件夹，并在需要时分出版本；先查重再创建。默认只上传可安装的补丁与玩家说明，不上传原游戏、译文工作区或内部验收文件。

Page 须明确适用普通 Windows PC Build 39、官方原版链接、补丁实际覆盖范围、原文保留范围、安装/回退、SHA-256 和实际验收限制。部分范围补丁在标题和开头直接说明范围，不使用“全文汉化”或将全作单位总数当完成量。下载链接采用实际上传并回读核实的文件链接，未上传的项目不列为可下载。
