# TUI 交互规范

Textual TUI 由根入口 `main.py` 或 `fvn-translator` 启动。当前 Dashboard 支持打开/创建 Demo 工作区、抽取、人物/术语提取与 JSON 审校、多 Provider 配置/切换、按场景翻译与摘要、停止、单元搜索/跳转、译文编辑与选中重译、进度与原/译文日志、问题跳转、校验、Apply 和本次备份回退。

网络请求和长任务必须在 Textual Worker 中运行，界面事件循环不得被阻塞。TUI 只调用 Service，不直接写中间文件、SQLite 或源文件。危险操作需显示目标路径、备份信息和确认语义；错误应显示稳定错误码而不是吞掉异常。

Dashboard 与元数据、Provider 弹窗共享同一 Service 边界。后续进行纯界面拆分时也必须保持项目、元数据、翻译、编辑、校验、备份与 Provider 设置共享单一工作区上下文。
