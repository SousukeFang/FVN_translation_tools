# Changelog

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
