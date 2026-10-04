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

- [ ] 每部游戏独立 prepare；根据真实提取报告确认清单和共享 brief。
- [ ] Agent 并行直接翻译，主代理串行导入，完整覆盖任务 ID，修订保留 revision。
- [ ] 审校视角、人物、专名、菜单/分支、含插值/标签和情绪转折。
- [ ] 完成图像补充文本和常用引擎提示，适配允许分发的中文字体并检查 cmap。
- [ ] staging round-trip、匹配版本 lint、开场/分支/UI/特殊字体运行检查，记录 Windows EXE 实测情况。

## 阶段三：打包与交付

- [ ] 每部游戏导出版本对应补丁、SHA-256 manifest 与安装/回退说明。
- [ ] 在独立原版副本实际应用最终补丁，核对所有目标哈希，再压缩 Windows 完整包。
- [ ] Google Drive 下建立合适系列/语言/版本子文件夹，上传补丁和完整包并验证链接。
- [ ] 创建含真实下载地址、校验值、版本/覆盖与使用方法的 Page。
- [ ] 将最终复用经验与实际验证结论更新 reference/文档，提交后续工具和规则修订；成品不进入 Git。
