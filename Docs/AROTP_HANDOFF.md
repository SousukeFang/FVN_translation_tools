# A Role to Play 0.051 Windows 英译简中

更新时间：2026-10-04。正式 FTIF 与译文全部保存在忽略目录 `work/a-role-to-play/`；最终工作区为 `translation-r1-final`，源目录、原始备份、翻译工作区分离。

## 官方输入与结构

官方来源：<https://echoproject.itch.io/a-role-to-play>，选择 PC Version / Windows。
页面标记 0.05，实际 ZIP 为 `ARoletoPlay-0.051-win.zip`，463,697,209 bytes，
SHA-256 `b688ef3c1b53eece8d009313fce2dec33ff5dafa0b5a02f8574a766bf81962c1`。
ZIP CRC 通过；原版 1,979 文件建立 SHA-256 清单，工作源与 pristine 逐文件一致。

引擎为 Ren’Py 8.0.3.22090809 / Python 3.9。24 个 `.rpy` 与 24 个同名 `.rpyc`，
已有 `tl/None/common.rpym` / `.rpymc`；无 RPA 或缺失源的编译剧情。正文为 Week1 / Week2，
第二周 Megan / CW 分支合流；一字节空白 Week1_Garth 与 `.rpy_copy` 不计额外内容。

## Skill 与工具扩展

新增 `a-role-to-play` Profile 和 [独立 reference](../skills/fvn-translate/references/a-role-to-play.md)，
复用 Ren’Py staging/FTIF 流程。自定义 sink 精确抽取 `msg` 正文及选择 name、
`chat.addmessage_pc` 正文、Gallery 名称、Text 字面连接/格式片段；资源和控制参数保持原文。
`switch_dialogue` / Interlocutor 名称兼作头像绑定，保护源值，仅在额外显示层汉化亲属称呼。
多行调用语句边界及 Python AST 的 UTF-8 列偏移修正有合成离线测试。

授权文本按路径、顶层三引号和模块 header 分类保护；旧 FTIF 没有新分类时仍能拒绝许可改写。
该许可单元的 ID 和源指纹保持不变。自然语言百分比不再误判为 `% s`；明确的 printf 宽度/精度、
映射和显式声明仍受校验，`constraints.printf_format=true` 可指定真正无宽度的空格 flag。

Screen Language 纯括号字面值也能定位，动态表达式不猜；实际 Gallery 检查补出两条页码。
四项门禁通过：Ruff check、format（171 文件）、Pyright 0 errors / 0 warnings、123 项离线测试。
Schema 示例检查通过。没有翻译 Provider/API 调用，Agent 直接输出已登记批次。

## 翻译与覆盖

最终正式 5,779 单元均完成，公共与 staging 回写校验 0 issues。包含 1 条原样保留的模块许可，
其余为正文、UI、角色配置和所选脚本内残留测试标签，不将全部计成主线剧情句数。
另有独立 FTIF 的 96 条引擎提示、33 条图像文字，图像覆盖 22 路径 / 55 位置。
所有修改经正式任务导入并保留 revision，原始 source / pristine 不应用补丁。

Gallery 补漏后新建最终工作区，按源路径、内容字符区间、源指纹、源文件哈希、类型和
说话人逐项匹配旧 5,777 个目标，再通过 83 个新登记批次导入，并直接翻译两条新页码。
旧工作区与审校 revision 完整保留；三条 Gallery 按钮 ID 重编号映射有记录，未绕过
重新提取清单变化门禁。迁移记录为 `registered-target-migration.json`。

默认保留姓名、世界观专名、曲名、署名和 URL；普通物种/职业/亲属称谓译中文。
西语按原外语功能保留；merry/Mary、gooning、p**** 等依相邻解释保留关键词。
HONSE 马图 meme 保留原图；少量品牌、logo、难辨装饰小字不列为图像汉化位置。

独立文学抽样 1,275 条源译对、349 条场景边界、806 条实体候选。11 项建议已正式修订；
另将百分号改为“百分之十”避免 `config.old_substitutions` 的实际格式异常。
这是抽样审校，没有宣称每句经过第二遍文学复核。

## 运行与交付

匹配 Linux SDK 已建立原版 lint 基线：return 0，205 原游戏警告；Font/UI 附件的临时
stage 无新增警告。图像使用原生 Crop / Solid / Text 合成，原素材不进入补丁。
字体包括完整 Noto CJK 和 Symbols2，OFL 随包；已有 NotoEmoji 按原 emoji 标签使用。

最终 ZIP 为 `A-Role-to-Play-zh-CN-patch.zip`，14,349,723 bytes，
SHA-256 `be3a908f0220b21eea4d75be78125327110629b9e014a52f6cb8ebd4f50f2eff`。
CRC 与 17 个目标文件哈希通过。新原版副本按说明安装后，九个脚本和八个附件符合清单，
九个旧 `.rpyc` 移至外部备份；其余 1,961 个原文件在首次启动前逐文件不变。
运行后 17 个补丁文件仍符合目标哈希，清单外原文件变化仅九个重新编译的 `.rpyc`
与四个引擎 cache；QA 入口、Linux 大小写别名及测试存档不进入补丁。

最终工作区全文原生渲染 5,777 个单元，0 新增异常、0 实际字形缺失；另外 1 授权块
不需显示、1 未使用名牌缺图为原版同样错误。实际默认/DejaVu Sans/OpenDyslexic
字体和 emoji 路径验证通过；17 个 kinetic 单元检查四个时间点，55 个图片文字位置
原生测量无溢出，逐图复核完成。少量斜体逻辑宽度多 1–4 px、UI 逻辑高度候选
有物理边界及原版对照记录，代表屏幕确认无裁切；未宣称逐句交互截图。

新成品真实 Main Menu → Start 走过 100 条非空中文 Say，FileSave、FileLoad 和
`after_load` 均成功，恢复同一脚本节点与文本签名。真实 Gallery ShowMenu 入口分别
验证锁定问号、已解锁缩略图与中文页码；实际 Dad 聊天记录及音乐播放/时长显示通过。
干净 lint return 0，205 条警告与原版基线一致，0 新增。

交付 [汉化补丁 Page](https://chatgpt.com/space/page_6aa9f1abdd1481919893f5a667fa9fbf)，
补丁、说明与清单上传到 [Drive 文件夹](https://drive.google.com/drive/folders/1FgkGAlvM9eVB_U06fmZDxq5gdmBIUZVY)。
Drive 回读文件 ID、名称、字节数和父目录一致；云端未返回内容哈希，不将元数据回读
当作云端 SHA-256 校验。Page 列最终版本、补丁哈希、安装/回退和验证限制。
未在 Windows 本机测试 EXE，也未全剧情通关；保留真实游戏的既有缺陷和验收边界。

按用户后续要求，补丁 Page 已精简为补丁下载及玩家说明；不提供 skill 扩展包、
内部验收下载或截图预览。此交付偏好已写入 skill 的默认 Page 规则。
skill、Profile、解析器、校验器及合成测试的开发变更提交到工具仓库，并推送 main；
游戏本体、字体、译文、成品与运行记录仍只保存在忽略目录。
