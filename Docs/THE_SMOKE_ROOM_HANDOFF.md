# The Smoke Room Build 39 接入与交付记录

更新时间：2026-11-07。本轮译文与产品代码已冻结，补丁和补译工具已完成发布与回读验证。

## 官方 Windows 输入

官方页面 <https://thegoodnightfellowship.itch.io/the-smoke-room> 提供普通 PC、PC legacy、mac、Linux 和 Android 构建。本次实际下载普通 `TSR-39-pc (2).zip`，740,307,890 bytes，SHA-256 `287a78a53580463570e151161d1613cd24f31ebf5c7013e1a8ae569f45630ab6`。ZIP CRC 通过；根目录 `TSR-39-pc/`，`config.version=39`，引擎 `8.5.2.26010301`。

`work/the-smoke-room/` 保存原 ZIP、独立 pristine/source、逐文件 SHA-256 清单和脚本元数据。原版 3,993 个文件；`game/` 有 27 `.rpy`、28 `.rpyc`，无 RPA。额外 `storage.rpyc` 为 288-byte RPC2，静态解压的两份 pickle AST 列表为空，无编译独有剧情；未反序列化执行该文件。

普通 PC 与 legacy 的 27 份 `.rpy` 逐字节相同，后者实际引擎为 8.1.3。源脚本 hash 不能区分这两个包；正式补丁必须另核验 `renpy/vc_version.py` 和 `TSR.exe`，两个 runtime 文件均只读，不能随补丁替换。

## Profile 与公共工具扩展

专属 Profile 为 `the-smoke-room`，规则与命令见 [reference](../skills/fvn-translate/references/the-smoke-room.md)。公共开场、四条路线、select 脚本、角色显示名、screen、笔记变量及两套 `journal_entries` 分别覆盖；只提取登记的可见赋值与字典字段，资源/控制值保留。

公共 Ren’Py 修复了普通引号跨物理行、`@` 临时角色属性、嵌套菜单 caption/选项识别；新增普通文字赋值 sink。普通非 raw Say/Menu/extend/显式显示名使用明确的 `renpy_text_escapes_v1`，按真实引擎先折叠空白再去转义。未知转义按引擎语义处理，真正换行、引号、反斜杠、标签与插值仍受保护。旧工作区不自动改变语义，须重提取、映射并用正式任务迁移。

冻结提取 **55,416 单元、0 issues**。与匹配引擎全部 54,157 Say 和 392 菜单项目的位置/文本 hash 精确对应；菜单为 313 选项与 79 caption。原作 10 个未知转义不是技术漏译。Python 三引号保留混合物理换行与显式转义的有序拼写；实际关于文本的 4 physical CRLF + 6 literal `\n` 在语义及保护签名上均通过。pending 空目标保持本地源文，不再被公共验证器误报为丢失标签；完成空译、非空错误草稿及公共打包未完成门禁仍拒绝。

新增 `build_renpy_delta.py` 和 `local_renpy_translation.py`。前者在独立重提取、revision/白名单/字节区间与 staging 等价验证后生成目标文字差量；后者是 Python 3.11+ 标准库单文件本地交换工具。全量 `agent package` 完成门禁未放宽。

## 实际翻译范围

用户要求自己随后下载官方 Windows 原版安装补丁；交付必须是实际剧情及界面汉化，另附可导出未译原文、手填、校验、回写的脚本。界面补丁或空工具不构成替代。

已核实[官方非营利民间翻译许可](https://itch.io/post/12717617)及[声明主体与本作的关系](https://itch.io/profile/thegoodnightfellowship)。本补丁非官方、非营利，原作版权与创作所有权归原作者和权利人；不以“免费公开下载”代替授权。

全作提取范围已逐场审核，最终 **52,194 接受并完成、3,216 排除、6 暂留、0 未审核**。范围外 3,222 条真实保留 pending/空目标，由玩家本地原版提供。普通粗话、成人非露骨双关/亲昵、职业讨论、非性裸体和严重非情色情节按语境处理，不用关键词补集假定安全；确实不可处理项保留英文。审核只保存位置/分类/hash，无排除原文摘录。

所有译文由 Agent 直接提供，通过登记任务和公共 service 串行导入并保留 revision。统一专名、物种、亲属称谓、POV、时代语境和外国词谜题；不把外语揭示提前解释。最后 7 处文学 QC 修订已正式导入，所有作者确认响应冻结。最终规范单位文件 SHA-256 `c6f54ac65c716ef7e92c2894ade289fba54d44a3f0c642489acb8020187ce762`。

## 补丁与个人补译

正式基础补丁为 **51,809 处实际文本替换 + 385 条已校对原样保留项**，改变 26 个脚本；27 份脚本源守卫、2 runtime 守卫、9 个新增附件。包中没有完整原剧情脚本、原 `.rpyc`、美术/音乐或排除原文。

新增附件含 Noto Sans CJK SC/OFL、Ren’Py 中文引擎 UI 及许可、字体和导航支持。常用引擎 UI 为 293 个官方项与 48 个功能项，其完整字符串对原 54,157 Say 无碰撞。原 PNG 主导航与 Return 由独立中文 textbutton screen 覆盖，保留动作、分支、原画、滚动与 transclude；剧情图片内文字未重绘。Default/OpenDyslexic 和 sin/forbid/willfont 等显式字体均纳入验收。

玩家解压到 EXE 同级后运行 `install.cmd`，Windows PowerShell 5.1+ 在全量预检后备份、替换本地脚本，并移走同名原编译文件；无需 Python 或管理员权限。回退先核对当前与备份 hash，不覆盖玩家后续修改。真实突然终止可能保留锁/journal，不能承诺断电整体原子恢复。

补译工具包含无原文的 55,416 单元定位目录、单文件脚本、5 个 CMD 入口和官方 Python 3.13.17 x64 嵌入式运行时/许可证。运行时原 ZIP 11,441,267 bytes，SHA-256 `9e35319bffedab8b36ad44d8f377cb4f1733bcec257a0b6d04d94f01486ddb38`。定位目录只含 ID、位置、类型、引号/模式与 hash，源文在玩家导出时才从本地原版/核验备份读取，不联网翻译或上传。

`target_text:null` 不抹去之前中文，连续 apply 保留原汉化及已填个人译文；重复相同文件不写游戏。活动记录、个人包、备份和归档分别为 `.fvn-active-translation.json`、`.fvn-personal/`、`.fvn-backups/`、`.fvn-backup-history/`。个人回退后用同一 JSONL 再 apply；不要调用旧基础安装器而留下旧活动记录。只装基础版应使用新原版目录。

## 已完成的工具与运行检查

代码门禁 `uv run ruff check .`、`uv run ruff format --check .`、`uv run pyright` 和启用实际便携 PowerShell 的全仓 `uv run pytest -q` 均通过。Pyright 0 errors/0 warnings，184 个 Python 文件格式通过。测试使用合成数据，不含本作真实剧情 fixture。

独立审查发现并修复：旧卸载实际完成后异常的恢复误判、合法 history ID 与归档目录冲突，以及已知 source/target 混合状态的回退。36 个本地工具专项测试及独立真实 pwsh 复验通过；第三态、坏备份、runtime 变动仍零写拒绝。

匹配 Linux SDK 为 8.5.2，原 tar SHA-256 `cf9ed145e5b32521a4b2caddb4cd3073c64259ac51e1f7aab94a8a8ff72b55c4`。原版 lint exit0，但有 55 项已有 path:line 诊断及过时处理器/不可达提示，不能称原版零警告。

首轮 37,471 目标×两字体 74,942 次真实 Text 渲染、124 个展开日记模板及原生 UI/姓名/菜单检查通过，无缺字或高度溢出。三种导航模式×两字体动作逐一同源，12 次实际菜单路由及两次 Return 通过。最终 52,194 目标×两字体 **104,388 次** Text 渲染及真实字体 span cmap 检查全部通过，0异常、0缺字、0正文溢出；正文最大 Default138/OpenDyslexic115px，均小于原208px。全量 validate 为0错误、3个已复核的 SMART_QUOTE，lint 与原版55条诊断相比无新增。独立 staging 的26个脚本与9附件逐个size/hash完全匹配正式manifest。实际最大8项菜单也已对照原英文；OpenDyslexic在假设保留姓名框时存在原版同尺寸几何边界，未作为汉化新增缺陷。

正常主菜单实际 Start 后推进前6条已审核普通开场；第4条通过真实 FileSave/FileLoad，after_load执行一次、状态marker恢复且 what widget 目标hash精确匹配。Windows EXE/CMD/嵌入式Python未原生执行，未做完整通关。

正式原版副本玩家e2e通过：导出恰为3,222个未选ID；两轮个人增补保留全部基础与旧个人差量，重复apply全树hash/mtime/目录元数据零写；rollback后同JSONL重新apply再rollback成功，3,993原文件完整恢复，EXE/runtime未变。错runtime的apply与rollback均零写拒绝。纯元数据报告为work下`delivery/player-flow-final-r1-metadata.json`，原文导出仅在私有测试副本，没有上传或入库。

## 最终发布记录

作品文件夹已在历史 [Game Patch](https://drive.google.com/drive/folders/1Tef7XKdv-gr1qKjMjiuY_2qIvHlJ2bGJ) 下建立 [The Smoke Room](https://drive.google.com/drive/folders/1Qu1IXAdSb6SHnd1hmbxX7bvXD5oafJXt)，版本目录为 [Build 39 Windows 简体中文 r1](https://drive.google.com/drive/folders/1b4uStTsNuhZ4Sy7ddOHQ-5x_xd_eccBw)。仅交付补丁、用户要求的补译工具和玩家说明，不上传原游戏、工作区、导出的原文或内部验收记录。


正式交付文件：

- [TSR-39-Windows-zh-CN-r1-Patch.zip](https://drive.google.com/file/d/1Xg24hVD02EZCpo3qRR0lEnHFuImQoOJv/view)，15,829,356 bytes，SHA-256 `0739fd59b81bbdec6065eb7a15f5d154757f53da166263bb9ab4348588962d20`。
- [TSR-39-Windows-Manual-Translation-Tools-r1.zip](https://drive.google.com/file/d/1sUrCZXtXYqSsN8hIUKhWb0vPqdE2G1fj/view)，16,596,632 bytes，SHA-256 `9e5ecbe4f5606af7680998c7bb9252d54b54dd2737ffb56e830129d1f6fefeea`。

两文件上传后已经连接器重新下载，逐字节SHA-256与ZIP CRC均匹配。不能将未返回的Drive checksum字段声称为服务端hash核验；此处证据来自完整回下载字节。

[补丁与补译工具下载Page](https://chatgpt.com/space/page_0ec99300ec188191902b093c168b59f4)已创建，标题、完整正文、版本/范围、两下载链接与hash全部回读匹配。未提供可视预览工具，未宣称页面视觉验收。
