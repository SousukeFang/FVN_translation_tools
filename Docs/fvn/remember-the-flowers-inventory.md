# Remember the Flowers - Part II 0.02 只读项目清单

调研日期：2026-08-03。源目录只读使用，未作为任何测试输出目录。

- Ren’Py 8.5.3.26051504；项目版本 0.02。
- `game/` 有 3,870 个文件；严格扩展名统计为 50 个 `.rpy`，共 1,357,864 bytes。
- 50 个脚本均为 UTF-8/CRLF，其中 13 个带 UTF-8 BOM。
- 主要剧情为 `game/story/prologue.rpy`（135,938 bytes，约 2,744 行）和
  `game/story/demo.rpy`（12,840 bytes，约 333 行）。
- 角色定义位于 `game/characters/names.rpy`；UI 主要位于 screens、credits、extras、
  music display/room 和 options。
- 已有 `game/tl/None/common.rpym`，第三方 ActionEditor 另带 chinese/japanese tl；
  都不作为待翻译源文。

风险点包括紧贴引号的角色属性、混用 BOM、全部 CRLF、大量资源/Python 字符串、
`{i}`/`{cps}`/`{w}`/`{font}`/`{size}`、插值和显式 `\n`。因此不能扫描所有引号，
也不能按行重写；必须使用语法 sink 和已定位的字符串区间。

## Profile 实际发现结果

Profile 排除第三方、既有译文、Python 文档字符串和纯资源/特效代码后发现 18 个脚本，
共抽取 2,383 个单元：旁白 1,115、对白 841、UI text 351、UI button 62、
show text 14。Menu、
extend 等目标文件未使用的语法由 generic fixture 覆盖。词法错误和未识别可见 sink 均为 0。

| 文件 | bytes | 分类 | 单元 | SHA-256 前缀 |
|---|---:|---|---:|---|
| `game/characters/names.rpy` | 11,500 | characters | 0 | `626a8…` |
| `game/credits1.rpy` | 1,627 | ui | 0 | `73d7a…` |
| `game/credits2.rpy` | 1,880 | ui | 0 | `81d74…` |
| `game/credits3.rpy` | 52,041 | ui | 420 | `0a230…` |
| `game/credits_end.rpy` | 448 | ui | 2 | `5a9f1…` |
| `game/credits_endint2.rpy` | 1,660 | ui | 0 | `57d8c…` |
| `game/creditsnew.rpy` | 10,207 | ui | 0 | `8d166…` |
| `game/extras.rpy` | 27,359 | ui | 91 | `bfb7a…` |
| `game/extratext.rpy` | 3,979 | ui | 10 | `e2af8…` |
| `game/gui.rpy` | 17,433 | other | 0 | `e98a3…` |
| `game/music_display.rpy` | 6,236 | ui | 72 | `6b4c2…` |
| `game/music_room/01_music_room_backend.rpy` | 31,033 | ui | 0 | `7f5ae…` |
| `game/music_room/music_room.rpy` | 38,107 | ui | 45 | `2b18e…` |
| `game/options.rpy` | 7,141 | ui | 1 | `5d3af…` |
| `game/screens.rpy` | 56,400 | ui | 227 | `d954b…` |
| `game/script.rpy` | 119 | other | 0 | `4c8d0…` |
| `game/story/demo.rpy` | 12,840 | story | 129 | `19ac6…` |
| `game/story/prologue.rpy` | 135,938 | story | 1,386 | `8e0db…` |

对这 2,383 个单元执行了未翻译及确定性离线测试译文 staging 回写和重新抽取：写入
18 个发现脚本均被复制到 staging，其中 10 个含翻译单元的脚本发生定位替换；内部
编码/BOM/换行/保护 token/结构校验问题为 0。测试 staging 位于仓库
忽略的 `trash/rtf-stage-gate-b-20260803/`；真实游戏目录没有作为输出目标。
