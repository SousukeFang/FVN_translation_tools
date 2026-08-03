# 校验规范

公共校验检查 FTIF Schema、译文状态、受保护标签/插值/printf 占位符的多重集合、空译文和可疑弯引号。格式 Adapter 增加语法、编码、结构和引擎专有检查。

Issue 包含稳定 `issue_id`、`code`、`severity`、消息、`unit_id`、路径、行和 details。严重级别是 `info|warning|error`；存在未解决 error 时不得 Apply。校验结果写入 `issues.jsonl`，并更新每个单元的 `validation.status` 与 `issue_ids`。

受保护内容比较必须考虑重复次数和参数，不允许只用集合或简单 substring。Adapter 应进一步验证标签嵌套、字符串边界、关键字、控制流和可解析性。
