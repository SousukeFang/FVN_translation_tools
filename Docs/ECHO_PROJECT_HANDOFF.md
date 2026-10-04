# Echo Project Windows 简体中文交付与续做

状态日期：2026-10-04。本次接受的交付范围已完成：三作简体中文补丁与 Khemia/Interea 实际安装的完整 Windows ZIP 已上传；Route 65 仅提供安全范围 overlay，175 文本单元与 4 张图像按用户接受范围保留本地原文，不提供完整游戏。三份官方 Windows ZIP 均已实际下载并通过 CRC，原包哈希和架构见各 skill reference。最终补丁、原文件完整性、匹配引擎实际运行、字体、图像与 Page 回读已有证据。没有 Windows 本机启动或完整通关。原游戏、译文、SDK、字体、补丁及中间过程只在忽略的 `work/`、`output/`，不进入 Git。

## 已交付下载

[下载与安装 Page](https://chatgpt.com/space/page_9ce9f3c49b888191971a4b5b3fd563db) 已更新三作补丁、两作完整分卷、Route 65 175 文本/4 图像保留范围、独立安装/卸载步骤和共用字体，以及最终实际运行验收。完整回读 38 个 canonical blocks，断言核对三个补丁 ID、Route 65 新 `1edcdc...` SHA-256、存读档结果及保留范围；旧补丁 SHA-256 与“等待用户选择”表述均无残留。

Drive 位置：个人文件夹 / Game / Game Patch / [Echo Project 简体中文 Windows](https://drive.google.com/drive/folders/1gzunGEjvFWqGoGSFN_c_UzoS7WA7UIED)，含“汉化补丁”和“已汉化 Windows 游戏”子文件夹。

| 成品 | 下载 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| Khemia Windows 0.4 补丁 | [ZIP](https://drive.google.com/file/d/1XDICjdRhetAmPGwgPpVImQZh-rXwxDXH/view) | 14,306,520 | `4b6cb68cb1644a04c77f564e8450e852fabf44625c4283ad93f2f870a6142820` |
| Khemia 已汉化完整 ZIP | [5 分卷与恢复工具](https://drive.google.com/drive/folders/11JAw0_EczynifjA7yTgFK5mYvkS86x25) | 387,952,711 | `02f64456b8671b377bcf90867f6ec8e400e743675af6d59ba7252e424560b940` |
| Interea Windows 0.4 补丁 | [ZIP](https://drive.google.com/file/d/1sDMaZO827C2KpVSTnADUEA9Nx0jQ-jw5/view) | 14,234,436 | `a509ae2529d251bff21d245464531b5b116e3aafe3a7df980fdbf0272f35a054` |
| Interea 已汉化完整 ZIP | [4 分卷与恢复工具](https://drive.google.com/drive/folders/1Xq2fqcKL2t1kCMNOx3ek3A7ZYptaHiZi) | 333,327,925 | `19fb9b2cef181140f4a971adedc80bf4f876443f36a265f44c312ade5a46472d` |
| Echo: Route 65 Windows 1.01 安全范围补丁 | [ZIP](https://drive.google.com/file/d/16-Q7jrzrd7Otatt9_GoIt3JGGMlWFaZV/view?usp=drivesdk) | 14,630,214 | `1edcdc173b24aa17c71bc931123ba412c9cf9985ee056b2447e522e38ed0a3be` |

连接器上传 387,952,711-byte 单文件时返回 413 / 100 MiB 上限，未声称该单文件上传成功。这是本轮连接器限制，不是 Google Drive 通用文件上限。完整 ZIP 改为 90 MiB（94,371,840-byte）顺序字节分卷，合并 SHA-256 与已安装补丁的 ZIP 一致，ZIP CRC 验证通过；上传后回读确认全部文件名、大小与父文件夹。每作附恢复工具 ZIP、分卷校验清单。服务端校验和未由工具返回，不声称已读取服务端 SHA/MD5。

完整游戏下载方法：将对应子文件夹中的全部分卷和恢复工具下载到同一目录，用附带 Windows 恢复工具先校验每卷大小/SHA-256，再按顺序合并并核对完整 ZIP SHA-256；本地发布验收另执行 ZIP CRC 检查并通过，恢复工具自身不做 CRC 检查。完整 ZIP 校验成功后再解压并运行原版 EXE；全卷齐备时也可用 7-Zip 打开 `.zip.001` 解压。Khemia 必须下载 5 卷，Interea 必须下载 4 卷，只下载首卷无法恢复完整游戏。补丁 ZIP 是独立下载项，需要匹配版本的官方原版；完整包已实际安装补丁，无需再次覆盖。

## 覆盖与运行验收

| 作品 | 脚本 FTIF | 补充范围 | 精确引擎与实际检查 |
| --- | --- | --- | --- |
| Khemia | 3,517 / 3,517 translated | 21 制作名单说明；66 常用引擎提示 | 8.3.4.24120703：3,350 Say Text 渲染无错误/溢出；真实开场 110 段对白，菜单和两页制作名单截图 |
| Interea | 2,296 / 2,296 translated | 66 常用提示；含恢复旧 a2s2 | 7.4.4：2,161 Say 含旧场景 415；无错误/溢出，开场 80 段对白，真实中文命名/插值及旧字面长说话人检查 |
| Route 65 | 接受范围 5,269 / 5,269 完成；全部提取 5,269 / 5,444 translated，175 pending | 102 安全图像 / 276 Text；36 旧 UI 标签；66 共用提示；4 排除图像保留原文 | 7.2.2.491：5,269 实际目标一致，175 原 who/hash 不变；5,231 Say/Menu Text 无异常/高度溢出；原生长句/centered、Start 开场及 FileSave/FileLoad/after_load 通过 |

全部翻译由 Agent 直接处理，没有 Provider/API 翻译。正文、名字、曲目保留、标签/插值/转义经审校和正式任务导入留 revision；共享专名规则保留 Parents/Siblings/Monitor，Lux 的描述性城市称谓例外在 brief 登记。语义审校与结构校验分别进行。

字体采用完整 OFL Noto Sans CJK SC 和 Noto Sans Symbols2；后者只处理 skip_triangle 的 U+25B8。Khemia/Interea 与共用/制作名单共 5,900 目标记录无缺字；随后全部已登记目标记录 11,330 也通过。该字形检查不代表 Route 65 全作汉化或最终 overlay 运行验收。支持常见中文自定义姓名。

所有运行在 Linux 的匹配官方 SDK，使用实际 Windows 游戏脚本和素材；没有 Windows EXE 本机测试或完整通关。Windows EXE 在实际装好补丁的副本中逐字节保持原版。Khemia lint 增加 7 条百分号接中文标点的已审查旧格式误报，实际渲染正常；Interea 与原版基线相比无新增产品提示。QA 脚本、日志、缓存和用户存档未进入成品。

Route 65 的 99 条原斜体旁白有 1–4px 字形边缘超出 640px 逻辑换行宽度，位于正文窗 30px 右内边距内；最终实际长旁白/台词 widget 为 643×156 / 635×156，窗为 750×198、正文可用高度 167px，截图完整可见。保留该测量，未声称逻辑宽度零外伸。原名牌固定 -195 偏移与零边距 Frame 的烘焙白横线曾遮挡文字，最终 Route 独立 say screen 将名牌置于框上方、采用原生半透明正文背景并预留 footer；common 字体附件未改。

Route 的 102 图像/276 Text 无异常或区域溢出，12 literal Show 资源对应/变更计数核对；只单独实际执行原 `Carl.rpy:9` 改写节点并恢复 next_node，未声称 12 节点全部通关执行。原 centered `_` 在安全短信背景上实际运行，透明样式保持；5 个真实菜单译文使用 QA NullAction 展示，未完整执行分支。原生 Start 开场实际 FileSave/FileLoad 后触发 after_load，前后台词 hash 一致，5,231 AST 目标及 175 原节点仍一致。最终 clean lint exit 0，141 个原警告的位置/类别与 pristine baseline 一致、0 新增。Route 的 5,647 交付文本输入字形检查缺字 0，共用 66 提示映射全部匹配。

最终工具门禁重跑通过：Ruff check、Ruff format（166 files already formatted）、Pyright 0 errors / 0 warnings、pytest 102 passed（1.07s）。这些仓库检查不替代单作的引擎运行和成品验收。

## 本地证据位置

工作根 `work/echo-project/`：各作品的 `source/`、`pristine/`、`translation/`、`responses/`；共用 `common/translation/`；精确 SDK 与运行证据在 `runtime/`。源规范化记录分别在 Khemia 和 Route 65 `source-normalization.json`，Interea 恢复证据在 `recovery-verification/`。

现代两作 staging 已验证，最终补丁在 `output/echo-project/<slug>/patch-r1/`，实际安装目录在 `work/echo-project/<slug>/patched/`。`output/echo-project/<slug>/installation-verification.json` 记录 ZIP CRC、全部目标哈希；`drive-parts/parts-manifest.json` 记录分卷。完整上传回读记录在 `output/echo-project/drive-delivery-receipts.json`。

`runtime/reports/acceptance-summary.json`、`font-khemia-interea-final.json`、`font-all-safe-finals.json` 是运行/字体证据；真实开场、命名、菜单和制作名单截图在 `runtime/patched/`。这些文件不提交。

Route 最终证据为 `runtime/reports/route65-safe-final-acceptance.md` / `.json`、`route65-final-attachment-freeze.json`、`font-route65-safe-final.json` 和 `route65-safe-final-lint-comparison.json`；实际长句、centered、菜单、存读档及图像截图在 `runtime/safe-only/echo-route-65/`。最终 ZIP 的全部 12 附件逐项 SHA-256 与独立 QA 冻结清单一致、CRC 通过。Git 追踪清单已确认不含 work/output/trash/archive、实际字体或编译产物。

## Route 65 已接受范围与差量交付

用户已明确保留 175 个排除文本单元及 4 张排除短信图像的本地原文，其余安全范围汉化；不做摘要替换。不得翻译、复述或再分发这些排除内容，也不上传完整 Route 65 游戏。交付仅包含安全目标、必要的安全 UI 匹配键和必需附件的 overlay，安装依赖用户自行获取的官方 Windows 1.01 原版。

安全译文已经用正式白名单导出/导入，接受文本范围 5,269 / 5,269 完成；全部 FTIF 中 175 单元仍 pending，没有 SKIPPED。冻结清单和目标映射：

- `echo-route-65/dedup/safe-unit-ids.json`：5,269 IDs，SHA-256 `8bef702d7695a2d2fafb4c2aa2f15b5737718e0590fefb6b7795ed1dcb53ce98`。
- `safe-targets-by-unit.json`：SHA-256 `6ec798674f80d8f8d0cf0557746dbbaa1355a2ee95b821f28376fb8bf715f730`。
- `safe-selected-tasks/`、`safe-selected-responses/`、`safe-selected-import-report.json` 保留正式进度；`inspection/content-flags.json` 只登记位置/类别。
- 安全图像附件 `runtime/zz_fvn_route65_raster_zhCN.rpy` SHA-256 `d560d2b713ca674b59c4ab5b929d988afa3a777f7d3337227b70736e172532ec`，仅覆盖安全范围；该值对应单个图像附件，完整补丁 ZIP 哈希另列于下文及下载表。

overlay 打包原则：不收入原剧情 `.rpy`、`.rpyc`、原图像、完整游戏素材、排除原文或任务上下文，只收入接受白名单的目标文字、必要的安全 UI 匹配键、定位/版本哈希元数据、必要运行脚本、字体、许可证和安装说明。原路径/单元 ID/位置/hash 可用于核对本地原版，排除清单只记位置/类别。通用 `agent package` 的完整性门禁不放宽，不将整份改变脚本当作安全差量附件。

本轮确定性附件打包器位于忽略目录，manifest schema 为 `fvn-safe-overlay-patch/v1`，只列原包不存在的新附件；公共全量 PatchService/CLI 未增加 overlay 功能。逐 ID 调用公共 `validate_unit` 检查安全选中集，验证全部 175 排除单元 pending 且无 target。在独立 `patched/` Windows 副本写附件并逐文件核对所有原始 SHA-256 不变，不生成/上传完整 Route 65 ZIP。安装和回退只处理新增附件清单，不移动未替换的原 `.rpyc`。

机制已落实为 `game/zz_fvn_route65_safe_zhCN.rpy` + `game/fvn_zhCN/route65-safe-units.json`：5,193 Say（含 62 centered 文本）、38 菜单目标、38 UI（35 原生 StringTranslator 调用 + 3 原样审阅）合计 5,269。Say/Menu 只附安全中文目标及原 AST 文本哈希；38 UI 有必要的安全 `source_text`/`target_text`，35 UI 匹配键供原生 StringTranslator 使用。175 排除节点只有定位/哈希，无 source/target，不附排除原文或全量原脚本。核对精确引擎/原包脚本 SHA-256，预检全部节点后一次改内存；失配报错，不改原文件、不覆盖 4 张排除图像。最终精确 7.2.2.491 实际运行的 5,269 目标一致，175 原 what hash/who 不变；8 原 RPY 及共 265 原 RPY/RPYC/图像字节不变，4 排除图存在且未注册覆盖。

公共单元校验已检查 5,269 选中单元：0 errors、5 SMART_QUOTE warnings。警告均为审校接受的引号表达变化，不涉及保护占位符；最终 manifest 记录 5 警告，不写成无警告。

独立静态 review 逐 ID 确认 5,269 目标等于正式 FTIF，175 记录仅定位/hash，源/AST/Menu 位置哈希及 12 新路径符合清单。SDK Python 2.7 mock 的成功路径与 4 个失配场景通过，失败路径无 AST/UI 写入；这是受控模拟检查，不能作为真实游戏启动结论。证据在 `work/echo-project/echo-route-65/safe-overlay/coverage-proof.json` 与 `technical-notes.txt`。

最终本地补丁：`output/echo-project/echo-route-65/patch-r1/EchoRoute65-1.01-Windows-zh-CN-safe-patch.zip`，14,630,214 bytes，SHA-256 `1edcdc173b24aa17c71bc931123ba412c9cf9985ee056b2447e522e38ed0a3be`。名牌/对话布局修订后已重新打包；ZIP CRC、12 个新增附件目标哈希验证通过，独立 Windows 原版副本实际安装后全部 1,540 原始文件 SHA-256 不变，Windows EXE byte-identical，未生成完整 Route 65 游戏 ZIP。数据附件 SHA-256 `0191a2caa8c91c48e2b10e8bbd12475f35741522a88c406b2eddaa95dd91892f`、overlay 脚本 SHA-256 `432d5a622239f7eb8654eecfef67b38a42357b4d58c25b885ed16507491f2e10` 保持锁定；修订 UI 附件 SHA-256 `250100f4d60fa1f318e64128f9553128dfba64e80f4043321f7298efb133edd1`。安装证据在 `output/echo-project/echo-route-65/installation-verification.json`。Drive 原文件 ID 已更新并回读名称、14,630,214-byte 大小及“汉化补丁”父目录，链接见上表，回执在 `output/echo-project/drive-delivery-receipts.json`。工具未返回服务端 checksum，不声称核对服务端 SHA。旧补丁与旧安装/上传记录已移入 `trash/echo-project/route65-before-say-layout-fix/`。

Route 65 安装：在匹配的官方 Windows 1.01 原版退出状态下，将补丁 `game/` 合并到 EXE 同级的 `game/`，保留全部原 `.rpy`/`.rpyc`、素材和存档。建议开始新游戏；旧存档历史/回滚中已经保存的字串不会追溯汉化。补丁固定中文默认语言，其他版本或已改剧情脚本会因哈希失配中止初始化。回退只移走 manifest 的新增文件，并移走新增 `.rpy` 运行后生成的同名 `.rpyc`；不要移走原版编译脚本。

最终验证已逐项核对 5,269 目标、175 排除单元和 4 张图像范围不变，完成实际渲染、原生存读档、附件冻结比对、Drive 更新回读与 Page 运行段回读。Windows EXE 本机测试和完整通关未执行，不能用 Linux SDK 检查替代该结论。

## 分支收尾

2026-10-04 已按用户要求将全部 `work` 提交快进合并并推送到 `main`。合并时远程两支均为 `7ef0d7002f1d14b5501e08a4815c4dffe33771c9`，`main..work` 独有提交数为 0；核对一致后，以该预期提交校验删除远程 `work`，再删除本地 `work`。远程回读仅有 `main`，本地也仅保留 `main`。本段收尾事实另在 `main` 提交同步；真实游戏与成品继续留在忽略目录，175 个范围外 pending 保持原状态。
