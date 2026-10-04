# Echo Project Windows 简体中文交付与续做

状态日期：2026-10-04。三份官方 Windows ZIP 已实际下载并通过 CRC，原包哈希和架构见各 skill reference。Khemia、Interea 已交付；Route 65 的安全译文已正式保存，交付范围待用户选择。原游戏、译文、SDK、字体、补丁及中间过程只在忽略的 `work/`、`output/`，不进入 Git。

## 已交付下载

[下载与安装 Page](https://chatgpt.com/space/page_9ce9f3c49b888191971a4b5b3fd563db) 已创建并回读核对内容与链接。

Drive 位置：个人文件夹 / Game / Game Patch / [Echo Project 简体中文 Windows](https://drive.google.com/drive/folders/1gzunGEjvFWqGoGSFN_c_UzoS7WA7UIED)，含“汉化补丁”和“已汉化 Windows 游戏”子文件夹。

| 成品 | 下载 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| Khemia Windows 0.4 补丁 | [ZIP](https://drive.google.com/file/d/1XDICjdRhetAmPGwgPpVImQZh-rXwxDXH/view) | 14,306,520 | `4b6cb68cb1644a04c77f564e8450e852fabf44625c4283ad93f2f870a6142820` |
| Khemia 已汉化完整 ZIP | [5 分卷与恢复工具](https://drive.google.com/drive/folders/11JAw0_EczynifjA7yTgFK5mYvkS86x25) | 387,952,711 | `02f64456b8671b377bcf90867f6ec8e400e743675af6d59ba7252e424560b940` |
| Interea Windows 0.4 补丁 | [ZIP](https://drive.google.com/file/d/1sDMaZO827C2KpVSTnADUEA9Nx0jQ-jw5/view) | 14,234,436 | `a509ae2529d251bff21d245464531b5b116e3aafe3a7df980fdbf0272f35a054` |
| Interea 已汉化完整 ZIP | [4 分卷与恢复工具](https://drive.google.com/drive/folders/1Xq2fqcKL2t1kCMNOx3ek3A7ZYptaHiZi) | 333,327,925 | `19fb9b2cef181140f4a971adedc80bf4f876443f36a265f44c312ade5a46472d` |

连接器上传 387,952,711-byte 单文件时返回 413 / 100 MiB 上限，未声称上传成功。完整 ZIP 改为 90 MiB 字节分卷，合并 SHA-256 与已安装补丁的 ZIP 一致；上传后回读确认全部文件名、大小与父文件夹。每作附恢复工具 ZIP、分卷校验清单。服务端校验和未由工具返回，不声称已读取服务端 SHA/MD5。

## 覆盖与运行验收

| 作品 | 脚本 FTIF | 补充范围 | 精确引擎与实际检查 |
| --- | --- | --- | --- |
| Khemia | 3,517 / 3,517 translated | 21 制作名单说明；66 常用引擎提示 | 8.3.4.24120703：3,350 Say Text 渲染无错误/溢出；真实开场 110 段对白，菜单和两页制作名单截图 |
| Interea | 2,296 / 2,296 translated | 66 常用提示；含恢复旧 a2s2 | 7.4.4：2,161 Say 含旧场景 415；无错误/溢出，开场 80 段对白，真实中文命名/插值及旧字面长说话人检查 |
| Route 65 | 5,269 / 5,444 translated；175 pending | 102 安全图像 / 276 Text；36 旧 UI 标签；4 图像待范围 | 7.2.2：安全图像无溢出，12 Show 表达式对应并执行原节点；未声称完成汉化剧情运行 |

全部翻译由 Agent 直接处理，没有 Provider/API 翻译。正文、名字、曲目保留、标签/插值/转义经审校和正式任务导入留 revision；共享专名规则保留 Parents/Siblings/Monitor，Lux 的描述性城市称谓例外在 brief 登记。语义审校与结构校验分别进行。

字体采用完整 OFL Noto Sans CJK SC 和 Noto Sans Symbols2；后者只处理 skip_triangle 的 U+25B8。Khemia/Interea 与共用/制作名单共 5,900 目标记录无缺字；随后全部已登记目标记录 11,330 也通过（不代表 Route 65 待定范围完成）。支持常见中文自定义姓名。

所有运行在 Linux 的匹配官方 SDK，使用实际 Windows 游戏脚本和素材；没有 Windows EXE 本机测试或完整通关。Windows EXE 在实际装好补丁的副本中逐字节保持原版。Khemia lint 增加 7 条百分号接中文标点的已审查旧格式误报，实际渲染正常；Interea 与原版基线相比无新增产品提示。QA 脚本、日志、缓存和用户存档未进入成品。

## 本地证据位置

工作根 `work/echo-project/`：各作品的 `source/`、`pristine/`、`translation/`、`responses/`；共用 `common/translation/`；精确 SDK 与运行证据在 `runtime/`。源规范化记录分别在 Khemia 和 Route 65 `source-normalization.json`，Interea 恢复证据在 `recovery-verification/`。

现代两作 staging 已验证，最终补丁在 `output/echo-project/<slug>/patch-r1/`，实际安装目录在 `work/echo-project/<slug>/patched/`。`output/echo-project/<slug>/installation-verification.json` 记录 ZIP CRC、全部目标哈希；`drive-parts/parts-manifest.json` 记录分卷。完整上传回读记录在 `output/echo-project/drive-delivery-receipts.json`。

`runtime/reports/acceptance-summary.json`、`font-khemia-interea-final.json`、`font-all-safe-finals.json` 是运行/字体证据；真实开场、命名、菜单和制作名单截图在 `runtime/patched/`。这些文件不提交。

## Route 65 待办与分支条件

已询问用户：采用简短非露骨概述替代相关内容并注明改编范围，或只保留技术 reference 和安全部分、不交付完整游戏。尚未收到选择，不能把时间经过当作同意；不得原样翻译或分发涉及未成年人物的性内容。

安全译文已经用正式白名单导出/导入，175 单元仍 pending，没有 SKIPPED。冻结清单和目标映射：

- `echo-route-65/dedup/safe-unit-ids.json`：5,269 IDs，SHA-256 `8bef702d7695a2d2fafb4c2aa2f15b5737718e0590fefb6b7795ed1dcb53ce98`。
- `safe-targets-by-unit.json`：SHA-256 `6ec798674f80d8f8d0cf0557746dbbaa1355a2ee95b821f28376fb8bf715f730`。
- `safe-selected-tasks/`、`safe-selected-responses/`、`safe-selected-import-report.json` 保留正式进度；`inspection/content-flags.json` 只登记位置/类别。
- 图像附件 `runtime/zz_fvn_route65_raster_zhCN.rpy` SHA-256 `d560d2b713ca674b59c4ab5b929d988afa3a777f7d3337227b70736e172532ec`，目前只覆盖允许范围。

若用户选择改编版本，所有改动仍须通过注册任务导入并留 revision；需要再次检查完整文本、图片、注释/旧编译文件与包内资产，确保成品不保留受限原文，再做最终回写/真实运行/打包/上传并更新现有 Page。不能仅给中文覆盖而把受限原版内容放进完整 ZIP。若用户选择技术与安全范围，则明确不交付本作完整游戏，保存既有成果即可。

用户要求任务完成后合并 `work` 到 `main`，确认全部同步后删除本地/远程 `work`。目前仍有上述范围待定，因此只提交并同步 `work`，未合并/删除。最终范围完成后 fetch 最新两支，核对清洁状态与祖先关系，合并推送 `main` 并回读验证，再删除 `work`；不得提前删除未同步成果。
