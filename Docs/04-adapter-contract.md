# Adapter 对接契约

Adapter 实现 `detect`、`discover_files`、`extract`、`apply` 和 `validate`，并声明 `adapter_id`、`adapter_version`、`supported_ftif_versions`。接口类型位于 `fvn_translator.adapters.base`。

职责边界：

- `extract` 只读源文件，按确定顺序输出 FTIF；每个单元保存稳定 ID、源文件位置/哈希、受保护内容和足够的回写数据。
- `apply` 只读取译文并写 `staging_root`，不得修改 `source_root`。
- `validate` 可独立检查 staging，返回带路径、行和 unit ID 的 Issue。
- Adapter 不调用 LLM、不管理凭证、不访问公共 SQLite 表、不实现 TUI。

必须满足的契约：相同输入的顺序和 ID 稳定；抽取不修改源文件；未翻译内容不发生无关变化；保留编码、BOM 和换行；Apply 后格式可重新抽取；专有校验可定位错误。

注册采用显式 `AdapterRegistry.register()`，不动态执行工作区里的 Python。新增适配器复制[开发模板](adapters/template.md)，准备独立 fixture，并调用：

```python
run_adapter_contract_tests(MyAdapter(), fixture_project, staging_root)
```

完成后还应增加格式故障样本、Apply/rollback 集成测试，并更新实现状态。Ren’Py 的已
实现语法、回写安全边界和已知限制见[专有规范](adapters/renpy.md)。
