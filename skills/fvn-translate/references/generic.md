# 未收录 FVN 的通用流程

先识别引擎和剧情字段，再选择确定性回写方式。不要把资源路径、代码、事件 ID 和所有带引号字符串当作剧情。

## 可读 Ren’Py

游戏根目录包含 `game/` 和 `.rpy` 时，`agent prepare` 自动使用通用 Ren’Py Adapter。提取对白、旁白、选项、screen 可见文本和已知可见文本调用，保持非文本语法。

检查提取报告、未知可见 sink、动态角色名与 UI。没有专属 Profile 的游戏不套用其他游戏规则。自定义调用确实显示剧情时，补充通用 Adapter 支持或使用下面的显式定位流程。

只有 `.rpa`/`.rpyc` 时，先在工作目录取得可验证的脚本：用引擎/格式对应工具解包或反编译，再核对脚本能被重新解析。保留原安装包，记录工具与版本。加密或无法还原的格式需要相应读取工具，不能把二进制直接当文本替换。

## 其他可读文本格式

阅读引擎脚本或 JSON schema，识别玩家可见的剧情、选项和需要翻译的 UI。用短脚本按该格式枚举实际剧情字段，生成 `span-map.json`。枚举、偏移和替换交给程序，Agent 决定哪些字段应翻译。

`text-spans` Adapter 接受 UTF-8 文件中的明确字符区间。偏移基于保留 CRLF、去掉 UTF-8 BOM 后的完整字符串；用 `Path.read_bytes().decode('utf-8-sig')` 读取，不能使用会折叠换行的文本读取方式。

```json
{"files":[{"path":"story/chapter.json","spans":[
  {"start":12,"end":25,"source_text":"Visible text","codec":"json-string","type":"dialogue","speaker":"Alice"}
]}]}
```

`json-string` 的范围包含完整 JSON 引号，`source_text` 为 `json.loads` 后的值；`plain` 的范围是正文，原始 slice 与 `source_text` 相同。区间必须来自实际文件，不能照抄示例偏移。JSON 剧情字符串使用 JSON parser/token scanner 定位，以避免重复原文匹配到错误字段。

```bash
uv run fvn-translator agent prepare --source work/game/source --workspace work/game/translation --source-language ja --target-language fr --adapter text-spans --span-map work/game/span-map.json
```

Adapter 检查范围、重叠、原文、源哈希，按逆序区间替换并验证未修改区间。额外需要原样保留的内容用 span 的 `protected_tokens` 字符串数组声明；map 不接受 `constraints` 字段。

纯图像文字或其他已确认不做变量插值的字面文本，可在该 span 设置
`"placeholder_mode":"explicit"`，只保护明确列出的 `protected_tokens`。例如图像中的
`[Click thumbnail to enlarge]` 是可翻译说明，不能误当变量；真实 `[username]` 等变量
仍须在列表中声明。默认 `auto` 继续推断标签/插值。运行附件显示这类文字时也须
关闭插值或正确转义，不能把文字误当引擎表达式。

## 明确范围的分阶段导出

需要只处理一组已确认单元时，将 ID 保存为非空、唯一字符串组成的 JSON 数组，再给
`agent export` 添加 `--unit-ids-file work/game/selected-unit-ids.json`。未知 ID 被拒绝；
空数组表示此次不导出。任务和相邻上下文均只使用所选 ID，译文照常经过登记任务导入并追加 revision。
其余单元保留原来的待翻译等状态，不以 skipped 或人工改状态代替完成；总体覆盖率和补丁完整性仍检查全部权威单元。
默认不加此参数，继续导出全部 pending/failed 单元。

## 通用补丁要求

- 覆盖已识别剧情，检查分支与选项；指出当前格式未自动识别的范围。
- 检查目标语言字体、编码和文本框容量。需要字体时使用允许分发的字体并附许可证。
- 补丁包含直接替换的改动文件和必要附件，保留相对安装路径；不重复打包整个游戏。
- 说明记录适用安装包/版本、备份、覆盖安装、恢复方式和实际验证。
