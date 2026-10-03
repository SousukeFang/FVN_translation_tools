# Agent 翻译模式与 Part II 汉化

目标：保留 API/TUI，新增由 Agent 直接翻译的任意语言工作流，交付版本对应的翻译补丁和说明。

1. 复用 FTIF、现有 Ren’Py Adapter 和游戏 Profile；检查输入版本、提取范围与字体。
2. 增加 Agent 批次导出、严格译文导入、revision 和断点；不调用 Provider。
3. 增加 staging 补丁打包，只包含改动文件、运行所需附件和安装说明。
4. `skills/fvn-translate/SKILL.md` 保留核心流程；游戏要求放 references，确定性操作放 scripts。
5. 未收录 Ren’Py 使用通用 Adapter；其他 UTF-8 格式用 Agent 确认剧情字段的 span map 进行精确替换。
6. 整理示例和目录规则，忽略下载、游戏、临时工作区、译文和成品。
7. 离线测试、ruff、pyright、pytest 通过后提交并推送。
8. 读取完成的 skill，取得 Windows 安装包；本游戏英语译为简体中文，正式长文本由 GPT-5.6 Sol、low effort 子代理翻译。
9. 全量导入、术语与抽样审校、结构与字体验证后交付补丁；创建包含下载链接与安装说明的 Page。

仓库只追踪工具、skill、参考规则、合成 fixture 和技术文档。真实游戏文本、响应、字体下载与翻译成品保留在忽略目录。

2026-10-03 交付调整：本轮完成 1–7 的开发与离线验证，用户要求一次提交并提供交接文档；实际安装包获取、正式汉化和最终 Page 在新任务中继续，见 `Docs/HANDOFF.md`。
