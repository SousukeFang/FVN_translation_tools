# 备份、续传与回退

Apply 前按涉及的相对路径创建 `backups/<backup_id>/files/`，`backup.json` 保存每个备份文件的 SHA-256。若源文件哈希与抽取时不一致，抛出冲突并停止，禁止静默覆盖。

Adapter 先写 staging 并校验；之后逐文件通过同目录临时文件和 `os.replace()` 替换。`state/apply_journal.json` 在每个文件替换后原子更新 `pending/replaced` 状态。中途失败时自动从刚创建的备份恢复并把 journal 标记为 `failed_and_restored`。手工 Rollback 在恢复前验证备份哈希，损坏时拒绝继续。

翻译续传以 `units.jsonl` 状态为准。Provider 响应先持久化再更新单元，因此进程在响应后退出时可恢复响应；SQLite 丢失时可从权威文件重建。回退只恢复游戏源文件，不清空 FTIF、revision 或缓存，因而可以修改现有译文后不调用 LLM 再次 Apply。
