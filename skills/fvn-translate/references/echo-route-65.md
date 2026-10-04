# Echo: Route 65

Profile ID：`echo-route-65`。读取本文件后加载[共用 Echo Project 流程](echo-project-renpy.md)。官方来源：<https://echoproject.itch.io/echo-route-65>。

## 本次交付范围待确认

实际源文检查发现涉及未成年人物的露骨性内容。此类段落不得翻译、复述或随完整游戏包再分发；reference 只记录处理边界，不摘录原文。Root 已向用户说明可继续的非露骨摘要/技术处理范围，产品译文、补丁和完整包须等待本次范围确定后按实际允许范围记录，不能默认沿用另两作的完整汉化交付承诺。

## 本次确认的 Windows 输入

- 下载包：`EchoRoute65-1.01-pc.zip`，218,925,746 bytes。
- SHA-256：`50a7ad0f0e0cc62235df140abe29840950df0d2a2a80bbc93e3c29fdc0dd66eb`。
- 包根：`EchoRoute65-1.01-pc/`；Ren’Py 7.2.2。
- 游戏内旧元数据为 `Echo` / `0.0`；采用官方包名 1.01 标记补丁版本。
- 8 个可读 `.rpy` 与 8 个同名 `.rpyc`，没有 RPA、没有仅编译脚本。

## 文件、角色和分支

剧情在 `game/Saturday.rpy`、`game/Carl.rpy`、`game/Jas.rpy`、`game/TJ.rpy`；`game/script.rpy` 定义资源、角色和入口。`screens.rpy` 是旧定制 UI，`readback.rpy` 为回看实现，`options.rpy` 定义默认样式和构建信息。不可把 UI 样式、音效队列或 `show image "..."` 资源调用译成对白。

角色采用 `init:` 中 `$ ID = Character(' ', ...)`，姓名通过 `show_who_window_style` 对应 UI 图像。blank 显示名不属于漏译。逐一定义/核对 `m`＝Chase、`l`＝Leo、`t`＝TJ、`c`＝Carl、`k`＝Karen；`j` 涉及 Jasmynn/Jenna 的实际身份和语境称呼，不凭同一缩写强行统一名字。保留真实别称差异，不凭缩写猜测 `d` 或其他未知身份。`centered` 是实际故事 speaker，需要保留。

叙述采用 Chase 第一人称；朋友之间的打趣、疏离、暧昧、紧张与超自然悬念保持原文揭示顺序。正文姓名、地方专名与原名 UI 一致保留英文；普通职业、亲属/物种称呼和日常语句自然译中文。路线出现重复但有差异的场景，按每个实际任务译文审校，不全局覆盖重复文本。

2026-10-03 初次无 Profile 扫描为 5,473 单元，其中夹杂 style 伪对白；35 条 unknown 提示主要是图片/音效资源调用。此数字仅用于发现问题，不能当最终覆盖率。最终以专属 Profile 提取报告及图像补充登记为准，检查每个菜单选择和四个剧情文件。

```bash
uv run fvn-translator agent prepare --source work/echo-project/echo-route-65/source/EchoRoute65-1.01-pc --workspace work/echo-project/echo-route-65/translation --name "Echo Route 65" --source-language en --target-language zh-CN --profile echo-route-65 --source-version "Windows 1.01 (EchoRoute65-1.01-pc.zip)"
```

## 图像文字与字体

`game/images/cellf*.png` / `cellff*.png` 包含实际手机短信；已实际查看 `cellf1r.png`，消息正文直接烘焙在手机图像上。它们是剧情覆盖的一部分，须登记短信文字和调用场景，再制作可还原、经渲染检查的汉化覆盖。不能仅翻译四个 `.rpy` 后宣称剧情全部中文。

`game/ui/mm/` 主菜单和 `game/ui/bt_*` 按钮也使用图像文字，例如 `bt_config_idle.png` 显示 Config。姓名图像保留角色英文名；常用按钮应添加中文可见/无障碍说明或经过验证的汉化 UI。资源路径与 action、声音、focus_mask、hover 状态保持一致。

字体资产有 `Daubmark.ttf`、`ui/arcon.otf`、`ui/belligerent.ttf`；默认 `style.default.font` 却写作 `ui/Arcon.otf`。Windows 大小写不敏感，Linux 验证需处理路径兼容并记录。正文有 `{font=ui/belligerent.ttf}`，仅修改默认字体不足以覆盖中文；保持标签并验证所有显式字体的 CJK 替换。旧 UI 无 `gui.rpy`，不能套用新模板。

## 验收和交付

使用匹配 Ren’Py 7.2.2 的 Python 2 运行环境验证；不可用 Ren’Py 8 将旧游戏源码整体升级。在确定的允许范围内检查剧情、菜单分支、centered 文本、特殊字体、手机消息、主菜单与确认按钮。交付物写明真实范围、处理方式和任何未汉化的图像；作者署名和商标保留。安装、编译脚本处理和 Google Drive/Page 交付的技术步骤按共用流程执行，本作完整原游戏分发不在当前范围内。
