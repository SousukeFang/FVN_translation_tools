# 仓库目录与 Git 追踪规则

根目录只保留会被 Git、uv、Python 构建工具、代码托管平台或 Agent 自动发现的文件。

| 文件 | 是否追踪 | 必须位于根目录的原因 |
|---|---:|---|
| `.gitattributes` | 是 | Git 属性从仓库层级生效 |
| `.gitignore` | 是 | 定义全仓库忽略规则 |
| `.python-version` | 是 | uv/pyenv 自动选择 Python 3.12 |
| `AGENTS.md` | 是 | Agent 自动发现的仓库级指令 |
| `LICENSE` | 是 | 代码托管平台和打包工具识别许可证 |
| `main.py` | 是 | 未安装命令入口时的便捷启动器 |
| `pyproject.toml` | 是 | Python 构建、依赖和工具配置入口 |
| `README.md` | 是 | 仓库首页，也是包元数据的 readme |
| `uv.lock` | 是 | uv 在项目根发现的可复现依赖锁 |

以下内容不放根目录：

- 版本记录放在 `Docs/CHANGELOG.md`；
- 技术规范和对接文档放在 `Docs/`；
- 维护命令放在 `scripts/`；
- 实现代码放在 `src/fvn_translator/`；
- 测试、示例和计划分别放在 `tests/`、`examples/`、`plan/`；
- 清理或废弃内容移动到不追踪的 `trash/`。

依赖声明只维护 `pyproject.toml`，环境解析结果维护在 `uv.lock`。根目录 `requirements.txt` 被忽略，避免产生两套可能漂移的依赖来源。
