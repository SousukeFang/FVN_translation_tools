# 工作区与状态存储

每个翻译项目使用独立工作区：

```text
project.toml
intermediate/{manifest.json,units.jsonl,characters.json,glossary.json,scene_summaries.jsonl,issues.jsonl,revisions.jsonl}
state/state.sqlite3
runs/<run_id>/{requests,responses}
backups/<backup_id>/{backup.json,files/}
staging/
logs/
exports/
```

`intermediate/` 中的公共文件是权威数据。SQLite 仅保存索引、缓存、断点与 `units.jsonl` 哈希；文件哈希不一致时先由 Pydantic 验证 JSONL，再重建索引。可运行 `python scripts/rebuild_state.py <workspace>` 手动重建。

JSON/JSONL 使用同目录临时文件、flush、fsync 和 `os.replace()` 原子替换。项目锁阻止两个写进程同时打开工作区。WAL 只用于本机磁盘；工作区位于网络共享时应改用非 WAL 模式。

`project.toml` 只能保存源项目路径、Adapter ID、语言和非敏感选项，不能保存凭证。
