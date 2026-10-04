# Changelog

## 2026-10-04 A Role to Play Windows 汉化与 skill 扩展

- 接入官方 Windows 0.051 / Ren’Py 8.0.3，新增专属 Profile 与 reference；精确抽取手机消息、选项、画廊及文本格式片段，修正多行语句定位、纯括号 UI 和自然百分比的占位符边界，保护模块许可与资源绑定。
- 完成 5,779 登记单元、96 引擎提示与 33 图片文字；最终补丁的安装哈希、全文原生渲染、开场存读档、聊天/画廊/音乐界面通过匹配 Linux SDK 验证，原版 205 lint 警告无新增。未在 Windows 本机测试或完整通关；详细范围与交付记录见 `Docs/AROTP_HANDOFF.md`。
- 按用户要求，补丁 Page 只保留下载与玩家说明；skill 与工具开发内容提交并推送 main，不提供扩展包或内部验收下载。此默认交付规则已写入核心 skill。
- 提交前 Ruff、格式检查、Pyright 和 123 项离线测试通过；真实游戏、字体、译文、补丁及运行记录保持 Git 忽略。

## 2026-10-04 Echo Project 本轮交付

- 完成 Khemia 3,517、Interea 2,296 脚本文本单元及中文字体；另补充共用 66 提示和 Khemia 21 制作名单说明，实际安装补丁并验证 Windows 完整 ZIP。
- Khemia/Interea 匹配 SDK 的正文渲染、开场、界面和中文姓名检查通过；图像文字按独立补充范围检查。Google Drive 超过 100 MiB 的完整 ZIP 使用校验过的字节分卷，下载与安装 Page 已发布。
- Route 65 正式保存 5,269 安全译文；用户已接受 175 单元及 4 图像在本地原版保留英文。仅交付安全范围纯差量 overlay，不翻译/复述/再分发排除内容，不上传完整 Route 65 游戏，不宣称全作汉化。
- 补充安全 overlay 与源码补丁的打包边界、连接器 100 MiB 实测限制和 90 MiB 分卷恢复规则；明确接受范围完成率、全量 FTIF pending、Linux SDK/Windows 本机测试及服务端哈希的验收界限。Route 65 最终 14,630,214-byte 补丁已独立安装/上传，12 附件与 QA 冻结清单一致、1,540 原文件不变。
- Route 65 实际 5,269 目标和 175 保留节点核对、5,231 Text 渲染、长句/centered、原生开场存读档、102 图像/276 Text、clean lint 与字形验收完成；99 条 italic 的 1–4px 边缘外伸在 30px padding 内完整可见。仅隔离执行一个 Show 改写和展示菜单标签，未完成 Windows 本机测试/全路线通关。Page 最终回读 38 blocks，核对三补丁、新 hash/大小、存读档和 175/4 范围。
- 更新专属/common reference 的实际行高、图像表达式覆盖、字体符号、源规范化及分卷处理；续做与下载记录见 `Docs/ECHO_PROJECT_HANDOFF.md`。
- 全部 work 提交已快进合并并推送 main；两支在 7ef0d70 核对一致且 work 独有提交数为 0 后，已删除本地及远程 work。收尾记录直接在 main 同步，真实游戏与交付产物不进入仓库。

## 2026-10-04 Agent 选定范围导出

- Agent 导出增加可选 `unit_ids` 白名单与 CLI `--unit-ids-file`，正文及相邻上下文都限于选定范围；未知 ID 拒绝导出，范围外状态与 revision 不变。
- 选定批次沿用正式任务登记、指纹核对及 revision 导入；部分范围完成仍保留整体待处理单元，不通过标记 SKIPPED 冒充全量完成。
- 四项门禁通过，102 项离线测试覆盖稀疏范围、恢复导入、默认兼容、非法选择与非选定单元完整保留。

## 2026-10-04 字面图像文本保护

- 为明确不做插值的 `text-spans` 文本增加 `placeholder_mode="explicit"`：只校验声明的受保护项，避免将图像内 `[Click thumbnail to enlarge]` 一类文字误认成变量。
- 默认继续自动识别标签与插值；离线测试验证字面说明可翻译、声明变量不可丢失，以及 staging 回写保持准确。
- Ruff、格式、Pyright 与 85 项离线测试通过；实际游戏、译文及运行附件仍放忽略目录。

## 2026-10-03 Echo Project 三部 FVN 技能接入

- 实际下载并比较 Echo: Route 65 Windows 1.01、Khemia Windows 0.4、Interea Windows 0.4；引擎分别为 Ren’Py 7.2.2、8.3.4、7.4.4，复用文本处理流程并保留版本差异。
- 新增共用 Echo Project reference 和三份专属 reference，登记原包 SHA-256、剧情/角色/UI、字体路径、Route 65 手机短信图像和 Interea 仅编译脚本的覆盖检查要求。
- 扩充 skill 参考分发与分阶段计划，继续使用忽略的 `work/` 与 `output/` 保存实际游戏、翻译及成品。
- 注册共用实现的三个游戏 Profile，识别旧式及跨行 Character 定义、命名输入和通知，排除实现模块与样式伪对白；增加显式说话人名称的抽取和回写关联校验。
- 本项为翻译前的接入记录；正式译文、运行检查、上传与 Page 发布按实际完成后另行记录。

## 2026-10-03 专名保留规范与 Part II 修订

- 核心翻译 skill 加入专名默认保留、用户规则优先、语境消歧及有依据的译名例外；自然中文不要求姓名和世界观名称一律中文化。
- 更新 Part II reference；区分 King 姓名与普通国王、命名类型与通用描述，要求正文/显示名/制作名单一致。
- 使用 GPT-5.6 Sol / low effort 审校 398 个相关候选，正式修订 341 个单元并追加 revision；重新生成字体、验证混排布局和 r2 补丁。
- 游戏、译文、字体和交付物继续保存在忽略目录，规范与交接记录进入 Git。

## 2026-10-03 Agent 翻译模式

- 新增 Agent 非 API 批次导出/导入、断点、响应归档、revision 与可恢复提交；任务不包含 Adapter 私有数据。
- 新增 `agent prepare/export/import/status/validate/package` CLI、skill 核心流程、通用和 Part II reference。
- 新增 `text-spans` Adapter，按明确剧情区间替换 UTF-8 plain/JSON 文本。
- 新增仅包含变化文件的补丁 ZIP、安装说明和哈希/验证 manifest；正式源文件不变。
- 源语言与目标语言接入原 API 服务、流水线和 TUI，保留旧默认值。
- 整理示例、skill、工作文件与交付物目录，并忽略真实游戏和翻译成果。
- 本次仅完成开发与离线验证；真实 Part II 下载、汉化和字体验证移交下一任务。

## 0.2.0 - 2026-08-03

- 实现 Ren’Py 8.x Adapter 的发现、词法/语句解析、FTIF 抽取、staging 回写、结构校验、
  SDK lint 集成和增量 remap。
- 新增通用 FVN Profile 接口与 Remember the Flowers - Part II 0.02 Profile。
- 新增真实语法 fixture、契约/单元/离线端到端测试、项目 inventory 和 Gate B 自动验收报告。

## 0.1.0 - 2026-08-02

- 建立 FTIF v1 公共模型、工作区与可重建状态存储。
- 增加 Provider、翻译编排、缓存、修订、校验、备份、Apply 与 Rollback。
- 增加 Adapter SDK、DemoAdapter、Textual TUI 和公共文档。

## 2026-10-03 Part II 正式汉化

- 从 origin/work 最新代码继续，完成 Windows 0.02 Demo 英语到简体中文翻译及审校；游戏和译文保留在忽略目录。
- 修复 Ren’Py ATL/跨行资源/动态 screen 误提取，补齐 Character 显示名，排除空白可见节点，精确保护曲目与真实署名。
- 最终提取 2,004 个非空单元；另补充 66 条常用引擎提示和日期/无障碍文案。提供中文字体、版本对应补丁、安装恢复说明和下载 Page。
- Ruff、格式、Pyright、75 项离线测试与 Schema 示例通过；matching Linux 8.5.3 引擎检查 Windows 脚本，Windows EXE 本机启动仍待验证。
