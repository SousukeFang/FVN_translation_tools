# Echo Project 三部 Windows FVN 汉化

任务来源：用户要求先扩充 translation skill/reference 并提交仓库，再将 Echo: Route 65、Khemia、Interea 从英语翻译为简体中文，完成字体适配、补丁、实际安装的 Windows ZIP、Google Drive 整理和下载 Page。本次最终范围：Khemia/Interea 提供全量汉化补丁与完整 Windows ZIP；Route 65 提供安全范围纯差量补丁，175 文本单元和 4 张图像保留用户本地原文，不上传完整 Route 65 游戏。

## 目录与输入

工具和可复用规则进入 `src/`、`skills/fvn-translate/`、合成测试及 `Docs/`；计划在本目录。原 ZIP、解包游戏、FTIF、译文、运行记录、字体在忽略的 `work/echo-project/`；补丁与完整包在忽略的 `output/`。不提交实际游戏内容或工作成果。

三个官方 Windows 包下载与 ZIP 完整性检查已完成；版本分别为 Route 65 1.01 / Ren’Py 7.2.2、Khemia 0.4 / Ren’Py 8.3.4、Interea 0.4 / Ren’Py 7.4.4。都带可读源码；Interea 的仅编译 `a2s2.rpyc` 已恢复并通过匹配引擎 AST 比对，确认是当前流程未调用的旧 a1s2 变体，保留控制流并覆盖文字。

Route 65 实际检查发现涉及未成年人物的露骨性内容；此类内容不翻译/复述/再分发。用户已确定上述保留原文的范围；overlay 仅携带安全译文、必要的安全 UI 匹配键、定位元数据和必需附件，不携带原脚本/编译文件/素材或排除原文。技术 reference 和排除清单不摘录受限段落。

## 阶段一：技能接入与仓库提交

- [x] 读取 origin/work 中既有 Agent 翻译 skill、AGENTS 与公共工作规范。
- [x] 实际比较三个包的引擎、剧情、角色定义、UI、字体与资源结构。
- [x] 新增共用 Echo Project reference 与三份专属 reference，并接入 skill 分发。
- [x] 注册三个专属 Profile，识别旧式/跨行角色与可见输入，排除实现模块和 style 误抽取；增加显式显示名及空姓名关联的回写测试。署名/曲目按共享 brief 审核保留。
- [x] 调查 Interea 仅编译文件，恢复与 AST 比对确认覆盖边界；登记 Route 65 手机短信图像补充覆盖要求。
- [x] Ruff、格式、Pyright、83 项离线测试和 FTIF Schema 示例通过；暂存区只含工具/规则/合成测试/文档，阶段一提交到 work。

## 阶段二：正式翻译、字形与验证

- [x] 三部独立 prepare，正式清单与共享 brief 登记。
- [x] Agent 并行直接翻译和主代理串行导入：Khemia 3,517 / Interea 2,296 全部完成；Route 65 安全部分 5,269 完成，175 明确保留 pending。
- [x] 文学与结构分别审校，修订通过注册任务留 revision；图像、UI、共用提示独立登记。
- [x] 完整 CJK + 符号字体适配，已登记目标记录无缺字。
- [x] Khemia/Interea staging、匹配 lint、Text 渲染、实际开场与 UI 检查；Route 65 新 overlay 实际范围、Text/图像/原生 UI、开场存读档验收完成。未执行 Windows 本机启动或完整通关。

## 阶段三：打包与交付

- [x] Khemia/Interea 版本对应补丁、manifest 和安装/恢复说明。
- [x] 两作在独立原版副本实际安装，目标哈希和 ZIP CRC 通过，Windows EXE 字节保持原版。
- [x] Drive 系列/语言/版本文件夹整理；完整 ZIP 超过连接器 100 MiB 上限，改为校验过的 90 MiB 分卷与恢复工具；所有上传回读文件名、大小、位置。
- [x] 创建并回读真实下载 Page，提供 Khemia/Interea 下载与分卷恢复说明。
- [x] 更新 reference 和交接记录，四项门禁与 102 项测试通过；只提交工具、规则、合成测试和文档。
- [x] 用户确定 Route 65：5,269 安全单元汉化，175 单元与 4 图像保留本地原文，不上传完整游戏。
- [x] 确定性打包 Route 65 纯差量 overlay：12 新附件、ZIP CRC 与目标哈希通过，独立 Windows 副本实际安装后 1,540 原文件 SHA-256 不变，不生成完整游戏 ZIP。
- [x] Route 65 选中单元公共校验 0 errors / 5 已审校 SMART_QUOTE warnings；精确 7.2.2 初始化/lint return 0，5,231 AST + 38 UI 目标匹配。
- [x] 修复真实截图发现的 Route 固定名牌偏移遮挡首行，只改专属 say screen；重打包/安装校验 12 新附件、1,540 原文件不变，并更新同一 Drive 文件的 ZIP 哈希/大小。
- [x] 完成 Route 65 新 overlay 实际渲染/存读档与排除集合验收；5231 Text 无异常/高度溢出、99 italic 外伸在 padding 内完整显示，102/276 图像检查通过，clean lint baseline 141/0 新增，5647 字形输入无缺字。只隔离执行 Carl:9 Show 和 QA NullAction 展示 5 菜单，未冒称完整分支通关。
- [x] 上传 Route 65 安全补丁并回读名称/大小/父目录，登记最终 SHA-256/大小/下载链接；未取得服务端 checksum。
- [x] 更新并回读 Page 的三作下载/范围/字体及 Route 65 独立安装/卸载说明，最终 38 canonical blocks 的三个补丁 ID、新 hash/大小、标题和保留范围核对通过。
- [x] 按最终实际渲染/存读档结果更新 Page 运行验收段并回读，旧 hash 无残留。
- [x] 更新最终验收记录，分别披露接受范围完成率、全量 FTIF 状态、Linux 检查与未执行的 Windows/完整通关项目；全部 12 ZIP 附件 SHA 与独立 QA 冻结清单一致，真实工作/成品未被 Git 追踪。
- [ ] 任务全部完成后合并并推送 main，验证 work 全部同步，再删除本地/远程 work。
