# Echo: Route 65

Profile ID：`echo-route-65`。读取本文件后加载[共用 Echo Project 流程](echo-project-renpy.md)。官方来源：<https://echoproject.itch.io/echo-route-65>。

## 本次已接受的交付范围

实际源文检查发现涉及未成年人物的露骨性内容。用户已明确接受：175 个排除文本单元及 4 张排除短信图像在用户自己的原版中保留英文，其余安全范围汉化。此类排除内容不翻译、复述或随补丁/完整游戏包再分发；reference 只记录数量、位置与类别，不摘录原文。本作交付仅为安全文字与必需附件的纯差量 overlay，不提供或上传完整 Route 65 游戏包。

本轮 5,444 单元中已正式导入并审校接受的安全部分 5,269 单元，即接受文本范围 5,269 / 5,269 完成；175 单元保持 pending，没有标成 SKIPPED 或计为译文完成。使用 `agent export --unit-ids-file` 导出正式安全批次，范围外正文和相邻上下文不进入新批次，原始 FTIF 状态及修订规则保留。最终 overlay 文件、哈希和下载状态以 [交接记录](../../../Docs/ECHO_PROJECT_HANDOFF.md) 为准，不以接受范围完成宣称全作汉化。

## 本次确认的 Windows 输入

- 下载包：`EchoRoute65-1.01-pc.zip`，218,925,746 bytes。
- SHA-256：`50a7ad0f0e0cc62235df140abe29840950df0d2a2a80bbc93e3c29fdc0dd66eb`。
- 包根：`EchoRoute65-1.01-pc/`；Ren’Py 7.2.2。
- 游戏内旧元数据为 `Echo` / `0.0`；采用官方包名 1.01 标记补丁版本。
- 8 个可读 `.rpy` 与 8 个同名 `.rpyc`，没有 RPA、没有仅编译脚本。

## 文件、角色和分支

剧情在 `game/Saturday.rpy`、`game/Carl.rpy`、`game/Jas.rpy`、`game/TJ.rpy`；`game/script.rpy` 定义资源、角色和入口。`screens.rpy` 是旧定制 UI，`readback.rpy` 为回看实现，`options.rpy` 定义默认样式和构建信息。不可把 UI 样式、音效队列或 `show image "..."` 资源调用译成对白。

角色采用 `init:` 中 `$ ID = Character(' ', ...)`，姓名通过 `show_who_window_style` 对应 UI 图像。blank 显示名不属于漏译。逐一定义/核对 `m`＝Chase、`l`＝Leo、`t`＝TJ、`c`＝Carl、`k`＝Karen、`j`＝Jasmynn；Jasmynn 与实际别称 Jas 分别保留，不能由样式名推断为 Jenna。其他未知身份须结合实际上下文，不凭缩写猜测。`centered` 是实际故事 speaker，需要保留。

叙述采用 Chase 第一人称；朋友之间的打趣、疏离、暧昧、紧张与超自然悬念保持原文揭示顺序。正文姓名、地方专名与原名 UI 一致保留英文；普通职业、亲属/物种称呼和日常语句自然译中文。路线出现重复但有差异的场景，按每个实际任务译文审校，不全局覆盖重复文本。

2026-10-03 初次无 Profile 扫描为 5,473 单元，其中夹杂 style 伪对白；35 条 unknown 提示主要是图片/音效资源调用。此数字仅用于发现问题，不能当最终覆盖率。最终以专属 Profile 提取报告及图像补充登记为准，检查每个菜单选择和四个剧情文件。

```bash
uv run fvn-translator agent prepare --source work/echo-project/echo-route-65/source/EchoRoute65-1.01-pc --workspace work/echo-project/echo-route-65/translation --name "Echo Route 65" --source-language en --target-language zh-CN --profile echo-route-65 --source-version "Windows 1.01 (EchoRoute65-1.01-pc.zip)"
```

## 图像文字与字体

`game/images/cellf*.png` / `cellff*.png` 包含实际手机短信；已实际查看 `cellf1r.png`，消息正文直接烘焙在手机图像上。它们是剧情覆盖的一部分，须登记短信文字和调用场景，再制作可还原、经渲染检查的汉化覆盖。不能仅翻译四个 `.rpy` 后宣称剧情全部中文。

`game/ui/mm/` 主菜单和 `game/ui/bt_*` 按钮也使用图像文字，例如 `bt_config_idle.png` 显示 Config。姓名图像保留角色英文名；常用按钮应添加中文可见/无障碍说明或经过验证的汉化 UI。资源路径与 action、声音、focus_mask、hover 状态保持一致。

本轮安全覆盖验证为 102 张图像、276 个原生 Text 框；4 张排除短信图像按已接受范围保留原文，不随补丁复制。12 处 `show image "文件名"` 属于直接图像表达式，仅注册同名 `renpy.image` 不会覆盖；通过精确匹配原 Show.imspec 的窄范围替换，保持 tag、transform、hide 语义，匹配 7.2.2 验证全部资源对应/变更计数；只单独实际执行原 `Carl.rpy:9` 改写节点并恢复 next_node，未通关执行全部 12 节点。不得包装 Image 工厂或全局替换未知表达式。原头像/姓名裁片须避开相邻英文标签；字幕须遮住完整原文字区域，中文论坛说明按可读布局重建。

四份剧情中重复的一行含误用 `\,`、`\W`、`\G`。本轮只在独立 source 副本修正这四行后重新抽取，5,444 个 unit ID 不变；位置与原/准备文件哈希登记 `source-normalization.json`，原 ZIP 保持不变。不能放宽真实受保护转义校验或为了过校验在中文前插入拉丁字母。

字体资产有 `Daubmark.ttf`、`ui/arcon.otf`、`ui/belligerent.ttf`；默认 `style.default.font` 却写作 `ui/Arcon.otf`。Windows 大小写不敏感，Linux 验证需处理路径兼容并记录。正文有 `{font=ui/belligerent.ttf}`，仅修改默认字体不足以覆盖中文；保持标签并验证所有显式字体的 CJK 替换。旧 UI 无 `gui.rpy`，不能套用新模板。

## 验收和交付

使用匹配 Ren’Py 7.2.2 的 Python 2 运行环境验证；不可用 Ren’Py 8 将旧游戏源码整体升级。在接受的安全范围内检查剧情、菜单分支、centered 文本、特殊字体、手机消息、主菜单与确认按钮，排除项保持用户本地原行为。安装包仅附白名单目标文字、必要的安全 UI 匹配键、窄范围定位/运行脚本、字体、许可证及说明；不得附任何原剧情脚本、旧 `.rpyc`、原图像或完整游戏资产。源路径、单元 ID、位置和哈希属于定位/校验元数据，不附排除原文。

overlay 应在版本核对后只应用白名单中的文本；验证 5,269 单元逐一映射、175 单元未改变、4 张图像未覆盖，标签、插值、菜单动作和原控制流保持。单独核对 ZIP 清单与展开后的所有附件，不能只因“改动很小”认定补丁无受限原文。通用 `agent package` 需要全量完成且会包含完整改变脚本，不适用于本作部分范围；不得放宽该门禁。

本轮使用忽略工作目录中的确定性附件打包器，manifest 为 `fvn-safe-overlay-patch/v1`，不是公共全量 PatchService/CLI 的 overlay 功能。只列原包不存在的新附件；对白目标逐 ID 调用公共 `validate_unit` 校验选中集，并检查全部 175 排除单元仍为 pending 且无 target。安装验收在独立 `patched/` Windows 副本写入附件，逐文件核对所有原始文件 SHA-256 保持不变。此补丁不替换原脚本，安装/回退按 overlay 自己的新增文件清单处理，不能照搬源码补丁移走原 `.rpyc` 的步骤。

安装须合并补丁 `game/` 到官方原版 EXE 所在根目录，保留原版脚本/素材与 `.rpyc`。推荐从新游戏开始：旧存档已经保存的历史/回滚字符串不会追溯变为中文；界面固定中文默认语言，其他游戏版本或改过剧情脚本的安装不适用。卸载先退出游戏，再移走清单中的新增附件及其生成的同名 `.rpyc`；原 `.rpy`、`.rpyc`、素材和存档保留。只移走新增 `.rpy` 而留下其编译附件可能继续载入补丁。

实际 overlay 为新增 `game/zz_fvn_route65_safe_zhCN.rpy` 和 `game/fvn_zhCN/route65-safe-units.json`：5,193 个 Say（含 62 个 centered 文本）、38 个菜单目标、38 个 UI 单元（35 个原生 StringTranslator 调用、3 个原样审阅），合计接受范围 5,269。Say/Menu 仅附安全中文目标及原 AST 文本哈希；38 个 UI 单元包含必要的安全 `source_text`/`target_text`，35 个 UI 匹配键供原生 StringTranslator 使用。175 个排除节点只有定位/哈希，无 source/target；不包含排除原文或全量原脚本。先核对 Ren’Py 7.2.2 及原包脚本 SHA-256，预检全部节点后才一次修改内存；错版或映射失配直接报错，原文件与 4 张排除图像不改。该机制须通过独立匹配引擎验收后才能声称最终 overlay 可用。

选中 5,269 单元公共 `validate_unit` 检查为 0 errors、5 SMART_QUOTE warnings；这些警告是审校后接受的引号表达变化，不涉及保护占位符。manifest 保留该 5 警告事实，不写成“无警告”。

独立静态复核逐 ID 对照全部 5,269 目标与正式 FTIF，175 排除记录只有定位/hash；源文件、AST/Menu 位置哈希和 12 新附件路径均匹配。SDK Python 2.7 mock 的成功路径与 4 个失配场景通过，失配时 AST/UI 零写入；该 mock 验证不替代真实引擎运行。证明和技术说明保存在忽略目录 `safe-overlay/`。

本轮最终 overlay ZIP 的 CRC 及 12 个新增附件目标哈希通过，并逐项与独立 QA 冻结清单一致。在独立 Windows 原版副本实际安装后全部 1,540 原始文件 SHA-256 不变、EXE byte-identical，未生成完整游戏 ZIP。精确 7.2.2.491 实际 5,269 目标一致，175 原 what hash/who 不变；8 原 RPY 及共 265 原 RPY/RPYC/图像字节不变，4 排除图存在且无覆盖。clean lint exit 0，141 原警告位置/类别与 baseline 一致、0 新增。

5,231 个安全 Say/Menu 的独立 Text 渲染无异常/高度溢出；99 条原斜体旁白有 1–4px 字形边缘超出 640px 逻辑宽度，但在 30px 右内边距内完整可见。原生最长旁白/台词 widget 为 643×156 / 635×156，窗为 750×198，正文可用高度 167px；截图确认完整显示，不声称逻辑宽度零外伸。名牌移至框上方，原零边距 Frame 烘焙横线改为原生半透明背景，footer 提亮并预留位置；原 who/window/what ID、side_image、角色名牌和菜单动作/声音保持。

原生 Start 开场 FileSave/FileLoad 及 after_load 回读成功，前后台词 hash、全部 5,231 AST 目标和 175 排除节点一致；原 centered `_` 在安全短信背景上实际执行，透明样式保持。5 个原菜单译文仅用 QA NullAction 展示，未完整执行分支。102 图像/276 Text 无异常或区域溢出，66 共用提示映射正确；5,647 字形输入检查缺字 0。最终报告/截图在 `runtime/reports/route65-safe-final-acceptance.md` / `.json` 与 `runtime/safe-only/echo-route-65/`，不以这些检查声称 Windows 本机测试或完整通关。

最终产品为 `EchoRoute65-1.01-Windows-zh-CN-safe-patch.zip`，14,630,214 bytes，SHA-256 `1edcdc173b24aa17c71bc931123ba412c9cf9985ee056b2447e522e38ed0a3be`：[安全范围补丁 ZIP](https://drive.google.com/file/d/16-Q7jrzrd7Otatt9_GoIt3JGGMlWFaZV/view?usp=drivesdk)。原名牌烘焙图固定 `yoffset=-195` 曾遮挡中文首行，本轮只修 Route UI 中的专属 say screen，共用字体附件不改、仍为 12 新附件；修订后已重打包/安装核对，并更新同一 Drive ID，回读名称、大小及“汉化补丁”父目录。工具未返回服务端 checksum。附件锁定值、完整验收状态与 Page 见交接记录；不另提供完整 Route 65 游戏下载。

交付物及 Page 写明“安全范围汉化补丁，175 文本单元与 4 图像保留英文；需要官方 Windows 1.01 原版”，列出真实运行项目与未执行项目。没有 Windows EXE 本机测试或完整通关时如实说明。仅上传安全 overlay；安装后的本地完整副本可用于检查，不能压成完整原游戏包上传。最终哈希、检查及链接见交接记录。
