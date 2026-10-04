# Echo Project 三部 Windows FVN 汉化

任务来源：用户要求先扩充 translation skill/reference 并提交仓库，再将 Echo: Route 65、Khemia、Interea 从英语翻译为简体中文，完成字体适配、补丁、实际安装的完整 Windows ZIP、Google Drive 整理和下载 Page。

## 目录与输入

工具和可复用规则进入 `src/`、`skills/fvn-translate/`、合成测试及 `Docs/`；计划在本目录。原 ZIP、解包游戏、FTIF、译文、运行记录、字体在忽略的 `work/echo-project/`；补丁与完整包在忽略的 `output/`。不提交实际游戏内容或工作成果。

三个官方 Windows 包下载与 ZIP 完整性检查已完成；版本分别为 Route 65 1.01 / Ren’Py 7.2.2、Khemia 0.4 / Ren’Py 8.3.4、Interea 0.4 / Ren’Py 7.4.4。都带可读源码；Interea 的仅编译 `a2s2.rpyc` 已恢复并通过匹配引擎 AST 比对，确认是当前流程未调用的旧 a1s2 变体，保留控制流并覆盖文字。

Route 65 实际检查发现涉及未成年人物的露骨性内容；此类内容不翻译/复述/随完整原包分发。Root 已向用户说明可继续范围，本作产品交付待范围确定；另两作继续独立处理。技术 reference 不摘录受限段落。

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
- [x] Khemia/Interea staging、匹配 lint、Text 渲染、实际开场与 UI 检查；Route 65 安全图像/UI 验证，完整剧情仍待范围。未执行 Windows 本机启动或完整通关。

## 阶段三：打包与交付

- [x] Khemia/Interea 版本对应补丁、manifest 和安装/恢复说明。
- [x] 两作在独立原版副本实际安装，目标哈希和 ZIP CRC 通过，Windows EXE 字节保持原版。
- [x] Drive 系列/语言/版本文件夹整理；完整 ZIP 超过连接器 100 MiB 上限，改为校验过的 90 MiB 分卷与恢复工具；所有上传回读文件名、大小、位置。
- [x] 创建并回读真实下载 Page，明确两作下载和 Route 65 待定范围。
- [x] 更新 reference 和交接记录，四项门禁与 102 项测试通过；只提交工具、规则、合成测试和文档。
- [ ] 用户确定 Route 65 的允许交付范围后，完成该范围的最终交付并更新现有 Page。
- [ ] 任务全部完成后合并并推送 main，验证 work 全部同步，再删除本地/远程 work。
