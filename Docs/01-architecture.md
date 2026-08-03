# 架构与模块边界

处理链路是：`源文件 → Adapter.extract → FTIF → 公共服务/Provider → Adapter.apply(staging) → 校验 → 备份 → 原子替换`。

模块职责：

| 层 | 目录 | 责任 | 禁止事项 |
|---|---|---|---|
| TUI/CLI | `tui/`, `cli.py` | 交互、展示、启动 Worker | 写业务状态、直接请求 LLM |
| Service | `services/` | 编排用例和事务边界 | 解析具体游戏语法 |
| Repository | `storage/` | 权威文件、索引、缓存、revision | 将 SQLite 当唯一数据源 |
| Provider | `llm/` | 无状态结构化 LLM 请求 | 修改源文件、解释 Adapter 私有数据 |
| Adapter | `adapters/` | 抽取、staging 回写、格式专有校验 | 调用 LLM、覆盖正式源文件 |
| Model | `models/` | FTIF 和运行配置类型 | 游戏专有顶层字段 |

依赖方向保持从交互层指向业务层、存储与端口；Adapter 和 Provider 通过 Protocol 注入。公共模块不得出现 Ren’Py 或具体 FVN 的分支判断。

数据安全边界：`intermediate/` 是权威数据；`state.sqlite3` 可重建；Provider 响应先落到 `runs/<run_id>/responses/` 再提交译文；`adapter_data` 透传但永不进入 LLM payload。
