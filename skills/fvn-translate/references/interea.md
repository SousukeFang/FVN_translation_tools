# Interea

Profile ID：`interea`。读取本文件后加载[共用 Echo Project 流程](echo-project-renpy.md)。官方来源：<https://echoproject.itch.io/interea>。

## 本次确认的 Windows 输入

- 下载包：`Interea-0.4-win.zip`，320,790,639 bytes。
- SHA-256：`2e62cf5a016e4ba91bf5b1346ceaac75c00c33b1c473959a21604a5664d213fc`。
- 包根：`Interea-0.4-win/`；Ren’Py 7.4.4，`config.name="Interea"`、`config.version="0.4"`。
- 8 个可读 `.rpy`、9 个 `.rpyc`；没有 RPA。`game/a2s2.rpyc` 无同名源码，必须独立核对。

## 剧情清单与编译文件

可读剧情是 `game/a1s1.rpy`–`a1s4.rpy`。`script.rpy` 定义资源/角色和入口；`screens.rpy` / `gui.rpy` 是 UI。a1s4 末尾明确出现 To be continued 并 return；单凭该结尾不能忽略额外 `.rpyc`。

本轮已在工作目录恢复 `a2s2.rpyc`，使用 Ren’Py 7.4.4 重新编译并对照 normalized AST：807 节点、415 个 Say，签名无差异。它是未被当前流程调用的旧 a1s2 变体；396 条正文与当前 a1s2 完全相同，其余约 19 条有差异，另有说话人误用的原版异常。实际启动链为 `start → a1s1 → a1s2 → a1s3 → a1s4 → return`。补丁可覆盖恢复后的旧脚本文字，保留其 label、跳转和原异常行为；不得新增跳转将它变成主线，不能用本轮结论跳过未来版本重新分析。恢复工具、原编译文件哈希和 AST 比对记录保存在工作目录。

`a1s1.rpy` 有 `$ mc = renpy.input("He summons this being with a simple name.")`，该提示必须用已注册 sink 抽取，玩家输入和 `[mc]` 插值完整保留。角色 `m = Character('[mc]', ...)` 是动态姓名，不能把 `[mc]` 翻译为固定人名，不能覆写玩家命名。

其他角色包括 `a`＝Amicus、`c`＝Cassius、`al`＝Alexios、`v`＝Virginia、`n`＝Neferu、`br`＝Brunis、`b`＝Bjarni、`ma`＝Magis；`com`＝Computer 显示名译为“计算机”，`mon`＝Monitor 作为命名世界观实体保留，未知 `unk='?????'` 保留。`m` 为玩家主角，和 Khemia 的 `m`＝Scipio 完全不同，禁止跨游戏按 speaker ID 套人物。

主角第一人称和 Amicus 的亲密互动保持自然；政治礼节、城市差异和不安情绪按场景转换，不擅自解释设定。名字和世界观专名默认保留英文；玩家输入、代词、直接称呼和普通职务词按上下文处理。

2026-10-03 初次无 Profile 扫描为 1,904 单元，无 unknown 提示；四个可读剧情文件计 1,746 单元，但漏出 renpy.input/Character 的专属 sink，且包含 style 伪对白，尚未扫描 `a2s2.rpyc`。此数字不能当最终覆盖范围。

```bash
uv run fvn-translator agent prepare --source work/echo-project/interea/source/Interea-0.4-win --workspace work/echo-project/interea/translation --name "Interea" --source-language en --target-language zh-CN --profile interea --source-version "Windows 0.4 (Interea-0.4-win.zip)"
```

## 字体、UI 与交付

`gui.rpy` 的文本、姓名与界面默认字体均为引擎提供的 `DejaVuSans.ttf`，游戏目录没有额外 TTF/OTF。添加可分发的中文字体，覆盖 gui 与 screen 中显式 DejaVuSans，保留 UI 箭头等字形。检查命名输入、`[mc]` 混排、存档页码、历史和确认框。

使用匹配 Ren’Py 7.4.4 的 Python 2 运行环境；复用 8.x 运行脚本前必须核对 API。实际检查所有四个当前章节，以及恢复后的旧脚本范围。补丁说明明确 `a2s2.rpyc` 的处理结论与哈希、其不属于当前启动流程的事实；保留原控制流，不将它标成新增主线章节。Windows 0.4 补丁和实际安装后完整 ZIP 按共用流程上传与发布 Page。

本轮最终 2,296 脚本文本单元完成，2,161 个 AST Say（含恢复的 415 个）实际 Text 渲染无错误/溢出；开场推进 80 段对白，中文姓名“青岚”实际输入、返回及插值正确。旧 `a2s2:102` 的长字面说话人也单独运行核对，中文完整显示，保留原异常和控制流。正式交付与待办见 [交接记录](../../../Docs/ECHO_PROJECT_HANDOFF.md)。
