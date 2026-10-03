# Agent 直接翻译模式

本模式无需配置翻译 Provider 或 API Key。Agent 读取 JSON 任务，直接输出目标语言译文；工具仍使用 FTIF、Adapter、revision 和现有校验。原 API/TUI 模式保留，两条路径都接受项目的源语言与目标语言。

## 文件布局

```text
skills/fvn-translate/
  SKILL.md
  references/generic.md
  references/remember-the-flowers-ii.md
  scripts/workflow.py
src/fvn_translator/
  services/agent_translation_service.py
  services/patch_service.py
  adapters/text_spans/
examples/remember_the_flowers/project.example.toml
work/<game>/                    # 本地游戏、翻译工作区与响应，忽略
output/<game>/<language>/       # 补丁和说明，忽略
plan/agent-translation/         # 开发计划，追踪
```

`workflow.py` 是仓库 CLI 的薄入口；语法处理在 Adapter，状态和打包在 Service。新增游戏只需先补 reference；必要的格式能力再通过 Adapter 或 Profile 扩展。

## 工作流与命令

使用 `uv run fvn-translator agent --help` 查看命令，也可执行 `uv run python skills/fvn-translate/scripts/workflow.py agent ...`。skill 依赖完整仓库及其 Python 包，复制单个 SKILL.md 不包含运行能力。

| 命令 | 用途 |
| --- | --- |
| `prepare` | 创建工作区、自动识别 Adapter 并抽取；明确提供源语言与目标语言 |
| `export` | 导出 pending/failed 单元、相邻上下文、人物和术语；字符预算包含任务 JSON |
| `import` | 整批核对 ID、任务登记、源指纹、语言和保护内容，归档响应、追加 revision |
| `status` | 统计语言、单元数量和完成状态 |
| `validate` | 在 staging 回写并进行公共和格式校验 |
| `package` | 检查全量完成、源文件哈希和重新提取清单，产出 ZIP、README、manifest |

任务不包含 `adapter_data`。目标响应为 `{"translations":[{"unit_id":"...","target_text":"..."}]}`，每批必须覆盖所有 ID。原样保留的署名等返回与原文相同的译文。重复导入相同译文不增加 revision，审校修改可通过原任务再次导入。

姓名与世界观专名默认保留源文，不以全文每个词都中文作为完成标准。用户明确译名优先，普通描述和同形词按语境消歧；处理方式及例外记录在共享 brief。规则变更先按源文实体定位候选并读上下文，再通过完整登记批次重新导入；禁止对中文姓名单字全局替换或只修改交付 ZIP。详见 skill 的「专名与术语的处理规则」。

并行子代理各自写响应文件，导入串行执行。工作区锁与小型提交记录保证批次写入可恢复；JSON/JSONL 使用原子替换。已翻译单元不进入续传批次；重新导出用新的任务目录，避免覆盖正在执行的任务。

源码转义由 Adapter 处理。Agent 使用解码后的 source_text 和 target_text；Ren’Py 的转义签名、字体标签与插值在最终 staging 校验中检查。

## 通用格式与补丁

Ren’Py 自动发现已知可见文本 sink，命中 Profile 时采用对应规则。未知引擎的可读 UTF-8 文件使用 `text-spans`：Agent 识别剧情字段，程序生成显式区间 map，Adapter 按原文和区间替换。支持 plain 与完整 JSON 字符串，不自动扫描所有引号。二进制、加密或编译资源仍需对应读取工具。

`package` 不调用会修改正式源目录的 ApplyService。它在独立 staging 校验后只收录变化文件与显式附件。`--extra` 或 `--extra-files` 添加字体/运行脚本，`--install-notes` 添加游戏说明。manifest 记录源/目标 SHA-256、语言、适用版本、覆盖率、文件清单和实际程序校验；引擎启动、字形和文学审校结论放安装说明，按实际执行情况记录。

真实安装包、游戏脚本、FTIF、响应、下载字体与最终补丁均保存在忽略目录。测试使用合成 fixture，不调用真实翻译 API。
