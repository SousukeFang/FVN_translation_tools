# Adapter 开发模板

1. 在 `src/fvn_translator/adapters/<id>/` 创建类并实现 `FVNAdapter` Protocol。
2. 写明源格式版本、文件发现、编码/BOM/换行、可见文本、分段/场景、受保护内容、稳定 ID、回写定位和已知限制。
3. `extract` 只读源文件，私有定位数据放 `adapter_data`；不要增加游戏专有顶层 FTIF 字段。
4. `apply` 只写 staging，缺失译文使用原文，不重排或格式化无关内容。
5. `validate` 返回稳定 Issue，并覆盖边界、占位符、标签、关键字和语法检查。
6. 在显式 Registry 注册，准备 fixture 和故障样本，运行公共契约测试。
7. 增加完整 Extract → Mock translate → Validate → Backup → Apply → Rollback 集成测试。

验收清单：相同输入结果确定；每个单元可回源；文件哈希被记录；源文件不被抽取/Apply 直接修改；编码与换行保留；未翻译区域无无关差异；回写结果可重新解析；错误精确定位。
