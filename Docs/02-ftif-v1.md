# FTIF v1 公共格式规范

FTIF（FVN Translation Intermediate Format）是 UTF-8 JSON/JSONL 格式。所有文档包含固定 `schema` 标识；未知顶层字段默认拒绝。新增可选字段可留在 v1，删除字段、改变语义或必填规则必须升级主版本。

## 文件

- `manifest.json`：项目、语言、Adapter 与 Prompt/Schema 版本。
- `units.jsonl`：一行一个 `ftif-unit/v1`，是翻译的核心权威文件。
- `characters.json`、`glossary.json`：可人工确认、带 evidence 和 version 的元数据。
- `scene_summaries.jsonl`：`previous_summary`、当前摘要及来源单元。
- `issues.jsonl`：稳定问题 ID、严重级别和源位置。
- `revisions.jsonl`：译文修改前后值、来源和时间。

## TranslationUnit

必填定位字段为 `unit_id`、`sequence`、`segment_id`、`type`、`source_text`、`source_fingerprint`。`origin` 保存源路径、行和抽取时文件哈希；`adapter_data` 保存格式私有的回写信息。公共代码只能透传 `adapter_data`。

标准 `type`：`dialogue`、`dialogue_extension`、`narration`、`screen_text`、`menu_choice`、`ui_text`、`ui_button`、`character_name`、`notification`、`input_prompt`、`accessibility_text`、`other_visible_text`。游戏语义放入 `context.semantic_role`。

状态分离：

- `translation.status`：`pending|in_progress|translated|reviewed|skipped|failed`；
- `validation.status`：`unchecked|passed|warning|failed`；
- `apply.status`：`not_applied|applied|apply_failed`。

译文来源为 `llm|human|translation_memory|cache|imported`。每次修改增加 `revision`，并同步追加 revisions 记录。机器可读定义见 [`schemas/`](schemas/)。
