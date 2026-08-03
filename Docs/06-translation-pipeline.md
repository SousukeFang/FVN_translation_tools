# 翻译流水线

1. Adapter 发现文件、抽取玩家可见文本并保存 FTIF。
2. MetadataService 分块提取人物与术语候选，保留 evidence，用户确认后递增版本。
3. TranslationService 依据预算分批，构造 system prompt、项目要求、相关人物/术语、当前单元、少量相邻上下文和 `<Previous Summary>`。
4. Provider 返回 `{unit_id,target_text}`；完整响应先写入 run 目录，再校验并原子提交批次。
5. 场景结束后 SummaryService 用旧摘要和本场景更新摘要，下一场景只携带新摘要，不累计完整历史。
6. 用户在中间文件编辑器审校；人工或自动返工均追加 revision。
7. 公共校验和 Adapter 校验通过后，Adapter 写 staging；Apply 服务备份并替换正式文件。

缓存键至少包含源指纹、目标语言、Provider/模型、Prompt 版本、人物/术语版本、摘要版本及约束。任一语义输入改变都应失效。断点恢复只处理 `pending`/`failed` 单元；已归档并提交的响应不重复请求。
