# Changelog

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
