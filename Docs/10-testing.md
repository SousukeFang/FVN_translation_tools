# 测试与质量门禁

测试分为 `unit/`、`integration/`、`contract/` 和 `tui/`。所有测试离线执行，默认使用 MockProvider，禁止真实付费请求和真实 API Key。

新 Adapter 必须运行公共契约测试，并补充确定性、稳定 ID、源文件只读、staging-only Apply、编码/BOM/换行、重新抽取和专有错误样本。公共服务需覆盖外部修改、非法响应、标签丢失、缓存命中、中断恢复、备份损坏和替换失败恢复。

质量门禁：

```powershell
uv run ruff check .
uv run ruff format --check .
uv run pyright
uv run pytest
python scripts/validate_schemas.py
```

当前环境/覆盖范围和未完成项以 [`IMPLEMENTATION_STATUS.md`](IMPLEMENTATION_STATUS.md) 为准，不得通过跳过测试或弱化校验宣告完成。
