# LLM Provider 规范

公共 Provider 只有 `test_connection()` 与 `complete(request)` 两个能力。人物抽取、翻译、摘要和返工属于 Service，不得变成供应商方法。

首期实现 `MockProvider` 和 `OpenAICompatibleProvider`。后者请求 `/chat/completions` 并要求 JSON object；响应必须严格校验预期 unit ID，不接受缺失、重复、未知 ID 或非字符串译文。

用户级 `providers.toml` 可定义多个非敏感配置并选择 `active_provider`。TUI Provider 配置弹窗可新增配置、切换活动项，并把临时输入的 API Key 直接写入系统 Keyring。API Key 查找顺序为系统 Keyring、环境变量、进程临时输入。环境变量名由 secret ref 转换为 `FVN_TRANSLATOR_<REF>`。密钥、Authorization Header 不得写入项目、数据库、日志、请求归档或测试。

自动重试仅覆盖连接错误、超时、HTTP 408/429/5xx，采用有上限的指数退避；400/401/403 和结构错误不自动重试。所有调用无会话状态，长期上下文来自版本化的 FTIF 元数据和摘要。
