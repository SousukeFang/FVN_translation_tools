# Remember the Flowers Part II 汉化交接

正式 Windows 0.02 Demo 英语到简体中文翻译已完成；本次从 `work` 分支继续，先执行 `git fetch`、`git switch work`、`git pull --ff-only origin work`，基于远端提交 `2ffa497` 开始。使用 `skills/fvn-translate/SKILL.md` 和 Part II reference，正式翻译与文学审校均由 **GPT-5.6 Sol / low effort** 子代理直接处理，没有调用翻译 Provider/API。

用户随后补充：不需要翻译的人名和专有名词保留原文，不强制音译。已在首版交付提交 `125ca93` 的 `work` 分支上再次同步远端，更新核心 skill 和 Part II reference，按此规范完成 r2 专名保留修订。

## 原包与来源

- 仓库：https://github.com/SousukeFang/FVN_translation_tools
- 官方游戏页：https://jerichowo.itch.io/remember-the-flowers
- 下载列名：`RememberTheFlowers - Part II (Demo - Windows).zip`；本地下载另存 ASCII 文件名。
- 游戏目录：`RememberTheFlowersII-0.02-win`；`config.version = "0.02"`。
- 引擎：Ren’Py 8.5.3.26051504。
- Windows ZIP：474,348,906 字节。
- 原包 SHA-256：`176f847efec0f675fbc5b696d7487492d8abb8a05903fd65ecaef03d25672131`。
- 本次环境网络已允许正常下载；旧交接中的 HTTP 403 阻塞已解决。

## 翻译与覆盖

最终提取 18 个脚本、2,004 个非空单元；其中剧情 1,511 个（prologue 1,382、demo 129）、角色显示名 90 个。全部单元均经 Agent 响应严格导入；r2 中 1,751 个译文与原文不同，253 个姓名、署名、曲目、标点、插值或产品名等按规则原样保留。首版文学审校另修正 5 处语义/姓名问题、制作名单及署名连接文案修订 62 处；本轮复核 398 个实体/术语候选，修订 341 个单元，均由 GPT-5.6 Sol / low effort 子代理处理并通过完整登记批次再次导入，正式工作区合计 2,412 条 revision。

补充引擎 UI 在独立 `text-spans` 工作区登记、导出和导入：66 条唯一文案按 None/english 两个语言域登记，共 132 个单元，包含确认框、外部存档信任提示、存档日期和无障碍标签。最终运行附件由这些已校验译文确定性序列化生成，target_text 不变。

姓名、术语及人物口吻约定在本地 `work/rtf/translation-brief.md`。当前默认保留角色姓名、昵称及世界观专名（如 Lance、Cy、Viv、Cyrus Cantwell、Resoom、Axiom、Arcadia Collar）；普通职业、物种、亲属称谓及 serum/carrier/普通 augmentation 仍译中文。显示名、正文与制作名单中的角色引用一致；King/The King 作为人物/外号保留，普通国王与姓名双关按上下文处理。Lance-a-lot 保留儿童戏名；大小写不同但同指实验室技术的 biological augmentation / Biological Augmentation 均保留，命名类别 Pristine Carrier 与普通 carrier 分开。不得对中文单字全局替换。

主线采用 Lance 第一人称，保留粗口、内疚、失眠、儿童王子游戏和人物关系的揭示顺序。中文正文标题为《铭记繁花》，正式窗口产品名保留；原样专名仍是已检查完成的译文，不降低完成率。

覆盖可编辑剧情、角色名、菜单、设置、帮助和额外内容。官方作者署名、曲目/专辑名、资源名、URL、图片内 Logo 和制作名单装饰字保留原文；第三方开发工具不汉化。实际交付说明明确这些范围。

## 本轮工具修复

- 排除 ATL/layeredimage、跨行资源表达式及动态 screen 样式/动作字串误提取。
- 为 Part II 增加 `Character("...")` 和 `Character(name="...")` 的显示名定位；代码 ID 与立绘属性不变。
- 排除空白角色名和 UI 间隔字符串；原始空白源码保持，非空原文的空译文仍被拒绝。
- 对曲目/专辑名、真实创作者链接署名和 `by Username` 做精确保护，普通链接说明仍可译。
- Part II Profile 版本为 1.1.0；专属 reference 已更新。
- 合成离线测试验证误提取排除、关键字参数、署名保护及空白/CRLF 保持。

## 工作产物位置

实际 checkout：`/workspace/FVN_translation_tools`。

- 原包/原游戏：`work/rtf/downloads/`、`work/rtf/source/RememberTheFlowersII-0.02-win/`。
- 正式 FTIF：`work/rtf/translation/`；任务：`work/rtf/tasks/`；最终响应：`work/rtf/responses/`。
- 初版批次及模型响应保存在 `work/rtf/tasks-initial/`、`work/rtf/responses-initial/`；使用精确源路径、行和解码文本匹配迁移到最终登记任务，保留 provenance。
- 审校：`work/rtf/review/`；每次正式修改仍由已登记完整批次导入。
- r2 审校：`work/rtf/review/name-policy-r2/`，包含首版快照、398 个候选的任务/响应、语义判断说明、完整登记响应、provenance 和术语残留检查；旧完整人名音译与主要世界观旧译名残留为 0。
- 补充引擎 UI：`work/rtf/common-translation/`；运行附件：`work/rtf/runtime/`。
- 字体与覆盖报告：`work/rtf/fonts/`。
- 安装说明：`work/rtf/install-notes.md`。
- 最新成品：`output/rtf/zh-CN-r2/`，补丁 `Remember-the-Flowers-Part-II-Windows-0.02-zh-CN-r2-patch.zip`（776,969 字节）。首版 `output/rtf/zh-CN/` 保留作历史证据。
- 最新补丁 SHA-256：`73bc2669ccff51db9cb308b1f1f619faa0df60ea6ee94b391bf8c2e787af5edf`。
- ZIP 14 项（12 个必要游戏文件、README、manifest）；CRC、完整条目集合、源/目标哈希和与引擎测试副本逐字比对均通过。
- 下载 Page：https://chatgpt.com/space/page_997cd9312a7c8191b765e33a5c3cd4e4

上述游戏、译文和成品均已忽略，不提交 Git。只有工具、合成测试、reference 和技术文档进入仓库。

## 运行附件与版本限制

中文使用 Noto Sans CJK SC 2.004 的子集字体，带 SIL OFL 1.1 许可证，内部字体名已更名。`config.font_name_map` 将原字体已有字形与中文 fallback 合为 FontGroup，先完成构造再注册，保留原 `{font}` 标签、英文手写体和符号。原包缺失的 DotGothic 字体引用及 Linux 大小写字体路径也由附件处理。

r2 子集按修订全文与补充 UI 重新生成，796,688 字节、1,888 cmap 码位；SHA-256 为 `7adfabe6bb34849305eb78d2ebde7ed8ebddea63ac43ab5b9945747d9254dfd1`。混排与姓名显示需使用本版实测记录，不能仅沿用首版截图。

本包 `game/tl/None/common.rpym` 已有原样英文翻译；不能重复添加相同 `translate None strings`。本次 `init 200 python` 更新 None 和 english 的 `StringTranslator.translations`，兼容既有语言偏好且不覆盖原 `.rpym`。这依赖已核验的 8.5.3 实现，换版本须重新检查。

补丁只含改动脚本及必要字体/运行附件，保持 `game/...` 相对路径；不修改正式源游戏。安装时备份改动的 `.rpy` 和对应 `.rpyc`，合并 `game/` 到 EXE 所在根目录，旧编译文件移到外部备份让引擎重建。恢复时还原覆盖文件并移走新增附件；保留本地和系统存档。

## 已验证与限制

Ruff、格式检查、Pyright、75 项离线测试及 FTIF Schema 示例通过，本轮再次运行通过。正式提取无问题，完整译文的变量、标签、源指纹与 staging round-trip 校验无错误；本版 50 项弯引号 warning 已检查，属于中文/原文排版。

已下载匹配版本官方 Linux 包，将完整 Windows `game/` 复制到独立测试目录，用 Linux 8.5.3 引擎执行 lint、中文字体探针、两语言偏好 UI 映射和实际界面检查。测试存档隔离到 `work/rtf/runtime/test-saves/`。1,509 个普通对白/旁白/扩展单元逐项引擎渲染无异常或溢出，最高 159px，小于对白可用 233px。另两个标题/尾页文本在界面检查中验证。

原包 lint 自带大量未使用旧素材的 not loadable 提示和 kinetic text tags SyntaxWarnings；按原版与补丁的差异核对，不宣称原版 lint 完全无提示。Windows EXE 本机启动尚未实测，已在交付说明标明。r2 字体中文缺字/丢字均为 0，1,509 个剧情单元重新渲染仍无异常/溢出，最高 159px。最后 lint 相对 Windows 原版逐条新增/删除消息均为 0，原资源提示仍为 3,123 项。ZIP、说明、SHA256SUMS 和验证记录通过下载 Page 交付；本轮运行与截图证据位于 `work/rtf/runtime/name-policy-r2/`，首版证据保留。

## 后续工作

后续使用 r2 的专名保留规范，不回退到初版强制音译方案。若用户报告问题，先核对原包/补丁哈希和版本，在新登记批次中通过响应导入修订，保留 revision 后重新生成字体子集与补丁。若升级上游版本，重新 prepare 并核对提取范围，不能直接混用本补丁。
