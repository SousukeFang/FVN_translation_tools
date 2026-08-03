# Gate B 验收报告

更新时间：2026-08-03

## 自动验收结果

- RenPyAdapter、Extractor、Writer、Validator、LintRunner 和 Profile 接口已实现；Adapter
  不依赖 Provider，公共 core/service 未写入具体 FVN 分支。
- Remember the Flowers - Part II 0.02 Profile 已从真实只读目录识别并发现 18 个目标脚本。
- 全项目抽取 2,383 个单元，词法错误 0、未识别可见 sink 0；带普通/负立绘属性和紧贴
  引号的对白均已覆盖。
- generic/真实样本覆盖 Say、旁白、显式显示名、extend、show text、Menu、Screen
  Language、`_`/`__`、三引号、tag、插值和自定义函数 sink。
- Writer 只写 staging，检查源哈希和原字符串区间，保留 UTF-8/BOM/CRLF；真实项目的
  未翻译及离线测试译文 round-trip 复制 18 个支持脚本并定位修改其中 10 个，重新抽取
  与结构校验问题为 0；测试前后真实目录 50 个 `.rpy` 的 SHA-256 全部一致。
- 单元 ID、原语句/相邻指纹与明确的 incremental remap 状态已实现；多候选返回 conflict，
  不静默选择。
- 离线集成测试覆盖 MockProvider、revision、校验、备份、Apply 和 Rollback；回退恢复
  fixture 原始字节。

## 尚需环境/人工验收

- 未配置独立 Ren’Py SDK，因此本轮没有宣称 SDK lint 通过；启用时缺 SDK 会明确返回
  `RENPY_LINT_NOT_RUN`。
- 真实游戏目录按用户要求禁止修改，因此正式 Apply、启动游戏和真实目录 Rollback 未
  执行；仅对 staging 和测试项目副本验证。
- TUI 已加入源目录项目创建、Adapter 自动识别和抽取统计，但完整 20 步人工交互演示
  仍需在可交互终端执行。
- 原生 `tl/<language>` Writer 与增量冲突审阅 UI 是已记录限制，当前安全模式为 staging
  源副本回写。

因此阶段二代码和自动 Gate B 项已完成；依赖 SDK/GUI/实际启动的人工项保持“待验收”，
在这些项目完成前不宣告正式游戏接入已通过最终 Gate B。
