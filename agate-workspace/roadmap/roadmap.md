# agate 项目 roadmap 看板

> 规划层（想做什么/做了没），执行层见 `tasks/active-tasks.md`。roadmap 条目拆出的任务行记录 `roadmap: <条目id>` 关联。

---

## 条目列表

| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |
|----|------|------|------|----------|------|------|
| RM-AG0004 | P6 视觉验收能力边界：无多模态模型时强制双证据 + 雷同截图降级待复核 | done | TQC0001 复盘 Q7（2026-08-13）| TAG0006 | 2026-08-13 | 2026-08-18 |
| RM-AG0005 | 冒烟验证脚本内置 finally-kill + 进程清理主 Agent 复核 | cancelled | TQC0001 复盘 Q8（2026-08-13）| — | 2026-08-13 | 2026-08-13 |
| RM-AG0006 | GUI 自动化框架评估（WinAppDriver/AutoIt）补真实 GUI 交互路径 | done | TQC0001 复盘 Q9（2026-08-13）| TAG0006 | 2026-08-13 | 2026-08-18 |
| RM-AG0007 | UI/UX 质量机制缺失：P1/P2 缺 UX 需求与设计评审、P6 缺视觉质量验收 | done | qtcalc 对比分析 §6（2026-08-13）| TAG0006 | 2026-08-13 | 2026-08-18 |
| RM-AG0008 | 0→1 项目目录结构脚手架：agate 立项时应按最佳实践设计合理目录结构，避免东放一点西放一点 | done | 用户需求（2026-08-13）| TAG0007 | 2026-08-13 | 2026-08-20 |
| RM-AG0009 | code-map + 架构演进纪律：新增文件/代码要从架构设计与设计模式层面考虑，避免胶水式层层堆叠 | done | 用户需求（2026-08-13）| TAG0007 | 2026-08-13 | 2026-08-20 |
| RM-AG0013 | 阶段卡缺"同类扫描/影响面梳理"机制层要求：P0-P8 卡无举一反三提示，仅 task P0-brief 局部 | done | 阶段提示词核查（2026-08-13）| TAG0012 | 2026-08-13 | 2026-08-18 |
| RM-AG0014 | 跨平台/外部环境验证的机制边界：supplementable vs verification_env 误用 + verification_env 缺失败处理流程 | done | TAG0005/0009 复盘核实（2026-08-14）| TAG0012 | 2026-08-13 | 2026-08-18 |
| RM-AG0019 | P0-brief 时效性验证缺失：立项后搁置再启动时，P0-brief 前提（技术路线/依赖/风险）可能已与最新状态漂移（TAG0008 .sh→py 实证），无检测/更新环节 | done | 用户提问（2026-08-15）| TAG0012 | 2026-08-15 | 2026-08-18 |
| RM-AG0020 | 复盘机制统一：模板缺正文结构（只有核对清单）、内容无价值标准、标的矛盾（异常触发 vs 所有任务）、路径矛盾（应放 tasks/{Txxx}/ 作 task 产物 vs 实际 docs/reviews/ vs check-retrospective 提示 docs/releases/，三处不一致）；分层归因 + 执行错误/机制缺口二分 + 措施可落地缺失 | done | TAG0013/0014 复盘讨论（2026-08-16）| TAG0015 | 2026-08-16 | 2026-08-19 |
| RM-AG0021 | agate 跨项目反馈机制：复盘中的 agate 机制/执行问题回馈到 agate 项目组（结构化 agate 反馈节 + 匿名化 + 开关，只回传 agate 归因内容不涉项目敏感信息）| done | TAG0014 复盘讨论（2026-08-16）| TAG0015 | 2026-08-16 | 2026-08-19 |
| RM-AG0022 | 协议规则结构化层（层 1）：把 agent 消费的协议规则从自由文本抽成结构化定义（phases.yaml/dispatch.yaml/roles.yaml + JSON Schema + S-1~S-6 双向一致性 gate），解决"agent 读 8000+ 行 md 理解规则"的摩擦 + gate 脚本从 grep markdown 迁移读 YAML（DEBT0010 实证）；M0-M3 渐进迁移（纯增量→双跑对账→切换权威源→卡片渲染化）；RM-AG0031 写时校验与 RM-AG0036 双语锚点依赖本条目；设计文档已就绪（docs/design-notes/design-structured-layer.md）| done | TAG0014 复盘讨论（2026-08-16）+ 设计文档（2026-08-21）| TAG0021 | 2026-08-16 | 2026-08-22 |
| RM-AG0023 | subagent 运行时管控（TPV0093 跨项目反馈回流）：命令超时兜底（timeout_seconds 字段 + dispatch-prompt 标准节 + 资源密集默认串行 + progress 心跳扩展）+ 环境准备职责边界（谁启动 debug/多 subagent 冲突）+ timeout 合理阈值与执行留痕 | done | TPV0093 复盘（2026-08-16）+ 用户补充（2026-08-17）| TAG0012 | 2026-08-17 | 2026-08-18 |
| RM-AG0025 | 协议文档职责边界与去重：WORKFLOW/dispatch-protocol/state-machine/platform-notes 等交叉重复（平台适配三份/阶段门槛两份/派发 prompt 双源/Pre-commit 清单两份），无内容归属约定——渐进叠加导致，需职责唯一化 + 去重 | done | WORKFLOW.md 审查（2026-08-17）| TAG0016 | 2026-08-17 | 2026-08-19 |
| RM-AG0026 | 测试重跑审计与跨阶段证据引用：P5 首跑/P5 重试/P6 refactor regression/P8 重跑 P5 最坏 4-5 遍全量（823 用例单次 106-115s）；P6 regression.log 独立证据是 gate 硬校验（regression_pass），复用需协议支持"跨阶段证据引用 + 无改动校验"——机制改进非纯优化 | done | 外部 agent 分析（2026-08-17）| TAG0016 | 2026-08-17 | 2026-08-19 |
| RM-AG0027 | 协议工具链修复批（TAG0016 复盘发现，DEBT0010/0011/0012/0014）：gate_commands 键解析脚本未排除 _timeout_seconds 后缀（4 脚本，P2/P3/P5 误判）+ SELF-GATE 审查文件纯日期命名跨任务同日覆盖历史记录 + check-protocol-consistency --strict 与 && 链路短路 + Windows Store python3 占位符命中 hook 探测循环（DEBT0014，跨项目反馈汇入）| done | TAG0016 复盘（2026-08-19）+ 用户跨项目反馈（2026-08-19）| TAG0017 | 2026-08-19 | 2026-08-20 |
| RM-AG0028 | env_constraints 声明性字段无执行/gate 绑定：deploy 类动作（UI 任务 windeployqt 构建 dist）只注入 subagent 上下文、不触发任何 gate 检查（agate-extract-context.py L107-109 只注入，check-gate.py grep deploy 零命中；TQC0001 实证 dist 从未主动产出直到用户提醒）| done | TQC0001 跨项目反馈（2026-08-19）| TAG0017 | 2026-08-19 | 2026-08-20 |
| RM-AG0030 | agate 原生支持 DSH 平台（deepseek-harness）：DSH 无 .claude/agents 等价物，身份注册用 agent-preset——提供 assets/templates/dsh/ preset+skill 模板（身份薄、协议厚，persona 指向 orchestrator-template.md）+ SETUP.md「步骤 2-DSH」符号链接接入 + platform-notes.md DSH 条目 + preset 必填配置回归测试；实机验证 preset 挂载与会话人格（2026-08-21，修复 tool-fs-search 缺 sampleOverCapGlobResults）| done | DSH 集成研究（2026-08-20）| TAG0018 | 2026-08-21 | 2026-08-21 |
| RM-AG0031 | 风险分路由（ceremony routing）：agate 成本高/速度慢，根因之一是复杂度判定依赖 agent 自报（self-authorization 陷阱，TAG0018 实证：analyst 声明 low 后 P5 仍抓真实违规；4 场 LLM 评审净收益≈0 而机械 gate 全胜）——改为客观信号脚本算分（agate-risk-score.py：文件类型/敏感路径/改动规模对齐 pruning 源码数≤5/域映射/影响面，analyst 只解释不决定）+ fail-closed 默认（thin 档=申请+checklist，不声明=standard）+ requirements-review 增"审声明"职责 + thin 档跳过 LLM 评审（M3 以实证数据验收）；配套 subagent 返回前自检 gate + 写时 schema 校验（联动 RM-AG0022）| done | 用户反馈（2026-08-21 成本/速度讨论，含设计提案）| TAG0019 | 2026-08-21 | 2026-08-22 |
| RM-AG0032 | 独立 Judge 机制（P6.5 验收独立裁判）：TAG0018 实证 4 场 LLM 评审≈0 净收益而机械 gate 全胜——评审失手根因是"评审者与作者同信任链/同上下文"，修复=新增 review 角色 judge（fresh context 只给标准 P1 BDD+P2 验收设计、信息隔离白名单禁传实现者自述）+ 三层防造假（①信息隔离 ②证据交叉核对：BDD 计数对照/md5 去重/git 留痕 ③append-only 事件账本 gate-events.jsonl 行间哈希链防改写）+ 三档预算（轮次≤2/token 100k/时间 30min，超限诚实降级 partial 不静默放行）+ 挂靠现有机制（status 门槛映射/专家组评审/dispatch-prompt 模板，零新架构）；设计文档：docs/design-notes/design-independent-judge.md（含完整文件改动清单：review-roles/judge.md 角色、check-judge-verdict.py、check-events.py、state-machine P6.5 转移行、phase-cards/P6 补节）；v0.59.0 已发布、PR #184 已合并，历史记录缺口补记 done（TAG0023 复盘发现，RM-AG0043 修复项②）| done | 竞品研究（oh-my-agent 独立 judge）+ TAG0018 实证（2026-08-21）| TAG0020 | 2026-08-21 | 2026-08-24 |
| RM-AG0033 | DSH 深度集成（TAG0018 MVP 后的第二层）：TAG0018 已交付 preset+skill 接入（身份层），本条目做运行时增强——@agate/dsh-plugin cordis 插件（①gate runner 服务：check-gate 结果面板 + 阶段状态机可视化 ②PostToolUse session hooks 实时 gate，早于 git commit 拦截）+ workflow 批量并行派发食谱产品化（P3/P4 多批并行一行脚本，TAG0017 的 5 批并行模式）+ goal 跨轮续跑增强（长任务崩溃恢复运行时化）；定位：平台原生 hooks 正在把 gate 变成平台内置能力，agate 价值从"发明 gate"转向"定义 gate 语义 + 编排 gate 组合"；参考 docs/design-notes/dsh-integration.md §4 扩展点清单（packages/extensions/cordis-*-runner、packages/hooks/）与 §8.5 能力超集表 | backlog | TAG0018 完成后的自然延续（2026-08-21）| — | 2026-08-21 | 2026-08-21 |
| RM-AG0034 | 平台扩展（第四平台起）：竞品 gap——oh-my-agent 已覆盖 10+ 运行时（Claude Code/Codex/Cursor 等）而 agate 目前 3 个（OpenCode/Claude Code/DSH）；按 TAG0018 已立模板扩展 Codex/Cursor/Gemini CLI 等——每平台交付物 = assets/templates/ 身份模板（agent-preset 或 agent md）+ SETUP.md「步骤 N」章节 + platform-notes.md 条目 + 回归测试（test_dsh_preset.py 先例）；平台能力差异表驱动（task 工具形态/hooks 机制/sandbox 语义）；CLI 型平台优先评估 session hooks 替代 git hooks 的场景；各平台接入须符合"不发明新结构"原则（文档化符号链接 + 唯一 install-hook.py）；**调研已完成**（docs/design-notes/platform-extension-research.md，2026-08-25）：Codex/Cursor/Gemini CLI 三平台能力对照 + 优先级建议（Codex>Cursor>Gemini），Aider 因默认 `--no-verify` 跳过 commit gate 判为不兼容，建议文档标注；接入前需实机复核 Codex subagent max_depth 旧记录与沙箱默认值 | backlog | 竞品分析（2026-08-21，v1/v2）| — | 2026-08-21 | 2026-08-25 |
| RM-AG0035 | 品牌改名执行（Agateon，2026-08-23 决策已定）：agate 名称与 4+ 活跃项目撞车（GitHub in:name 1223）——**用户拍板改名 Agateon**（"agent gates on"闸门开启/验证激活；2026-08-23 四源核验：npm/PyPI 空闲、**agateon.com 已注册（2026-08-25）**、.dev/.io 未注册[.io 因 TLD 存续风险未采用]、GitHub 0 真实撞名；保留 agate 前缀迁移成本最低；候选对比与淘汰记录于 docs/design-notes/rename-recommendation.md[gatewise 因域名被占淘汰/agaton 造词感/turngate 有 4 撞名]）。**执行设计评审通过**：docs/design-notes/design-rename-execution.md（2026-08-25 三轮独立评审收敛，三层解耦——品牌名 agateon/主仓 agateon/目录 agate 永久保留 + 分层迁移 + 基础设施层 AGATE_*/~/.agate/agate-*.py 兼容策略 + brand-check（一致性 gate 不校验品牌）；门户暂定独立仓 agateon-portal，否决 monorepo）。**剩余工作（转执行型）**：①商标正式申请（**调研已完成**：docs/design-notes/agateon-trademark-research.md，2026-08-25；建议美→中→欧 9+42 类、约 ¥1 万内，申请前人工复核 EAGATON/AGATON/AGON 商品项目）②仓库改名（agate→agateon，原 URL 301 + install.sh/README×2/agate-install.py/agate-changes.py 硬编码 URL 同批更新）③`agate-*.py` 脚本前缀 + `~/.agate`/`AGATE_*` 环境变量兼容别名策略 ④品牌 prose 迁移（in-scope 文件 + backtick token 判定规则）+ brand-check ⑤v1.0 迁移窗口 ⑥GitHub org 占名防抢注（**已占 2026-08-25**：github.com/agateon 空 org 仅占名，迁 org 随门户立项再议）；验收锚=仓库/文档/脚本品牌统一 agateon + AGATE_* 兼容别名生效、旧 URL 301 跳转正常。**部分完成
（TAG0025，2026-08-26）**：②已完成——GitHub 主仓已改名为 `randomgitsrc/agateon`
改名执行 + 7 处硬编码 URL 同批更新（install.sh/README×2/agate-install.py/agate-changes.py）+
本机 remote 迁移，4 条验收锚（301/ls-remote/残留扫描/GitHub 搜索）实测通过；品牌声明（README
首屏 "Agateon (formerly agate)"）已随批同步上线。①③④⑤⑥**仍未完成**（①商标申请人工复核未做/
③CLI 别名/④prose 统一+brand-check/⑤后续窗口重评估/⑥org 迁移待门户立项），状态维持 `backlog`
不标 `done`（TAG0025 未关联进「关联任务」列，避免触发 RM-AG0043 单任务闭环校验——本条目需
后续任务补齐剩余 5 项才应整条标 done）。| backlog | 用户决策（2026-08-23 拍板 Agateon）| — | 2026-08-21 | 2026-08-26 |
| RM-AG0036 | 国际化（英文协议文档先行）：全球采用第一道门槛——README 已双语但协议正文（WORKFLOW/dispatch-protocol/state-machine/phase-cards/角色文件，约 8000 行 md）全中文；策略：先核心后全量（orchestrator-template/WORKFLOW/phase-cards 先行，Fallback 文档殿后）+ 双语一致性 gate 防漂移（联动 RM-AG0022 结构化层——YAML 声明可作双语锚点，S-1~S-6 检查扩展）+ 里程碑=首个英文-only 接入项目；涉及体量大（8000+ 行），适合独立 task，P1 需按文件分组 BDD 并做影响面梳理（用户明确不愿一轮轮来回改）| backlog | 竞品分析（2026-08-21）| — | 2026-08-21 | 2026-08-21 |
| RM-AG0037 | ruff 检查合并强制（防第四次复发）：TAG0019(23 处)+TAG0020(12 处) 带 ruff 违规合并进 main，靠事后 PR #183 补修（35 处全清）；TAG0021 靠内部 P5 自抓 70 处回修——CI 已有 ruff job（protocol-tests.yml:106）但对 PR 合并非硬性。修复：①ruff job 设为 PR required check（分支保护）②可选：pre-merge 前强制 ruff 0 error gate；验收锚=新任务合并时 ruff 零违规无需事后补修 | done | TAG0019-21 全面分析（2026-08-22，合并后 main 实测 35 处错误）| TAG0022 | 2026-08-22 | 2026-08-22 |
| RM-AG0038 | 结构化层 M2 迁移闭环（RM-AG0022 剩余工作）：check-gate.py（主 Agent 每阶段总闸）实测仍 22 处 markdown/grep 解析、0 处 YAML；53 脚本大量 grep 残留——"权威源"目前是并行双源（YAML+md），未真正切换，双份维护漂移风险仍在（S-1~S-6 只防漂移不消灭 grep）。修复：check-gate.py 等核心脚本迁移到 rules/*.yaml（对齐已迁移的 gate_commands 族经 agate-md-field-get 模式）+ 迁移后 S-1~S-6 收紧为"YAML 权威、md 禁止承载可判定规则"；验收锚=check-gate.py 零 md 解析 + 全量测试绿 | done | TAG0019-21 全面分析（2026-08-22，实测）| TAG0022 | 2026-08-22 | 2026-08-22 |
| RM-AG0039 | judge 启用强制化（TAG0020 设计意图未完全实现）：P6 卡宣称"P6.5 judge 复核强制所有任务"，但 judge.enabled 由 P1 主 Agent 自写（state-machine.md:443），未启用则全链跳过（TAG0019/20 无 judge 块）——"与 P6 同不可裁"是软强制，残留半 self-authorization。修复：新任务机械强制——P1 gate 校验新任务必须 judge.enabled: true（缺失阻断或高优先 WARNING 升级），历史任务（机制前）维持跳过；验收锚=新任务 P1 不写 judge 即被拦 | done | TAG0019-21 全面分析（2026-08-22）| TAG0022 | 2026-08-22 | 2026-08-22 |
| RM-AG0040 | TAG0019 M3 实证收尾（RM-AG0031 只完成一半）：ceremony: thin 档从未实战——全仓无任何任务跑过 thin，成本下降目标（评审轮数 vs 真实发现数对比，TAG0018 基线）无实证数据；thin 档"跳过评审"是协议/提示词级行为，check-routing 只校验声明格式不校验执行。修复：下一个 low 风险任务真跑 thin 档并产出对比实证；收益不达预期则回滚 standard；验收锚=实证报告（thin 任务评审轮数/发现数 vs standard 基线）| done | TAG0019-21 全面分析（2026-08-22，全仓无 ceremony: thin 实战）| TAG0022 | 2026-08-22 | 2026-08-22 |
| RM-AG0041 | 环境假象测试根治（test_bdd_7/25）：测试依赖 basetemp 位置（git 仓库内/共享污染），TAG0020/21 各复现 2 次，仅登记 known-failures 未根治——反复出现有掩盖真实回归风险。修复：两测试改为探测 git 上下文/强制仓库外 basetemp（或按平台分支断言），使任意环境全绿；验收锚=任意 basetemp 位置下全量 pytest 0 失败 | done | TAG0019-21 全面分析（2026-08-22，known-failures.md + 多次复现）| TAG0022 | 2026-08-22 | 2026-08-22 |
| RM-AG0042 | 门槛失败事件强制记录 retries（重试上限防绕过）：复盘审计实证——TAG0019/20/21/22 四任务 .state.yaml retries 全为 {}，而 requirements-review 3 轮、plan-eng-review 1 轮 rejected、P5→P4 回退 3 次（TAG0019/21/22）、子代理空返回重派均真实发生且未记录。现状：check-state-transition.py 有重试上限机制（retries_over → PAUSED，L146-154）但**无任何检查强制'门槛失败事件必须记录进 retries'**——记录自选，不记录则 MAX_RETRY→PAUSED 被静默绕过，重试上限机制空转。修复：①gate 校验 retries 与门槛失败事件（评审 rejected/P5→P4 回退/子代理空返回）对应性——失败事件存在而 retries 为空 → 阻断或高优 WARNING ②P1/P2 卡明确评审被拒须写 retries；验收锚=新任务评审 rejected 后 retries 必有对应条目（对应性校验拦截空记录）| done | 复盘独立评审（2026-08-23，agate-workspace/reviews/retrospective-tag0019-21.md 问题 10/措施 9，四任务 .state.yaml 逐一核实）| TAG0023 | 2026-08-23 | 2026-08-25 |
| RM-AG0045 | 声明写时校验（formatter/schema 级，RM-0031 配套 + RM-0022 联动）：P1/P2 声明（ceremony/coupling_checklist/跳过风险/phases 等）写文件时即由 schema 校验，消灭 commit 时格式折返——TAG0019 实证：coupling_checklist 流式/半角冒号/源码数 6>5 均在 commit 才暴露，每轮折返一次 subagent 往返。修复=①声明 schema 校验接入写路径（生成器/编辑器/formatter 层）②错误信息给具体行+修复提示；验收锚=声明格式错误写入时即报、commit 折返归零 | done | TAG0019-21 复盘+风险分路由设计（2026-08-23，RM-0031 配套项）| TAG0023 | 2026-08-23 | 2026-08-25 |
| RM-AG0044 | 环境敏感测试集中治理（第三例 test_bdd_14）：2026-08-23 实证——docs-only PR #188 同 commit 双 CI run 一过一挂（push 事件过 / pull_request 事件 pytest ubuntu 挂：test_bdd_14_retreat_entry_present_no_warning，GATE DEBT WARNING 断言失败），重跑即过；本地 3/3 过。与 RM-0041（test_bdd_7/25 basetemp）同类不同根因（check-debt --retreat-coverage 的 git 环境敏感性：short SHA/runner 差异）。修复：①排查 check-debt.py --retreat-coverage 的 git 环境敏感点（short SHA 比较确定性）②建立环境敏感测试判定标准+集中清单+CI flaky 自动重跑机制；验收锚=test_bdd_14 连续 5 次 CI 稳定 + 环境敏感测试有集中治理清单 | done | 复盘后 CI 实证（2026-08-23，PR #188 双 run 对比 + 重跑）| TAG0023 | 2026-08-23 | 2026-08-25 |
| RM-AG0043 | P8 roadmap 回写 done 校验（记录闭环防复发）：复盘审计实证——RM-AG0032（独立 Judge）v0.59.0 已发布、PR #184 已合并，但 roadmap 至今无 done 行（现为 backlog/scheduled 残留），P8 gate（check-gate.py）**无任何 roadmap 回写 done 校验**。修复：①P8 gate 增加 roadmap 校验——关联 RM 条目状态必须为 done（按 task_id 反查）②补记 RM-AG0032 → done（历史数据修正）；验收锚=新任务 P8 后 roadmap RM 自动 done，无漏记 | done | 复盘独立评审（2026-08-23，agate-workspace/reviews/retrospective-tag0019-21.md 事实基线记录缺口 + roadmap 实测）| TAG0023 | 2026-08-23 | 2026-08-25 |
| RM-AG0046 | 维护性反模式 gate（P4/P6 代码质量复杂度机械校验）：设计文档已就绪（docs/design-notes/design-maintainability-gate.md，2026-08-25，源自 Cursor thermo-nuclear review 的 gate 化分析）——协议层定义反模式语义（God File 跨越 / Conditional Tangling / DRY 违反 / Fuzzy Boundary / Thin Abstraction / Sequential Coupling）+ 判定标准（diff 驱动、跨越≠超过、判定权在 gate），检测器由各项目按 gate_commands 自行实现（不绑定技术栈）；客观信号算分 + LLM 只解释不决定（联动 RM-AG0031 风险分路由模式）；反模式语义可进 rules/*.yaml（联动 RM-AG0022 结构化层）；验收锚=新增/修改代码出现可判定反模式时 P4/P6 gate 阻断或高优 WARNING | done | 用户提供 Cursor skill 分析（2026-08-25）；落地计划 v3：docs/design-notes/rm-ag0046-maintainability-gate-plan.md（2026-08-30 独立评审定稿，P4 挂载三重门槛）| TAG0026 | 2026-08-25 | 2026-08-30 |
| RM-AG0047 | Agateon 门户（agateon.com，后续）：设计文档已就绪（docs/design-notes/design-agateon-portal.md，2026-08-25）——"Agateon 之于 agate 如同 GitHub 之于 git"：数据面（协议/本地 gate，离线自治）与控制面（门户，只读镜像）分离；分层交付 Layer 0-4（协议→agate-status 本地聚合→上报协议→git-native 门户→组织/用户/注册）；git-native 上报（agate-report 提取最小快照+账本哈希链头 push，零后端）；门户只读 + 告警 + 指引，不提供干预按钮（fail-closed）；核心词=可验证性（gate 验证 agent→事件账本验证任务→门户验证组织）；首个用例=agate dogfooding 自己；验收锚=后续首个可交付层（Layer 1 agate-status --all）| backlog | 用户产品愿景（2026-08-23 发散讨论 + 2026-08-25 设计）| — | 2026-08-25 | 2026-08-25 |
| RM-AG0048 | agate-md-field-set 结构化字段写入工具（补 get 工具缺失的 set 面）：设计文档已就绪（docs/design-notes/design-md-field-set.md，2026-08-25，自审 2 轮通过，独立评审待环境恢复；**仅为参考输入，不作为 task 交付物**，执行中发现设计弊端按实际情况调整）——给 subagent 提供"写入即校验"的 CLI（key 从 schema 白名单限定、value 写入时校验、格式由工具生成），消灭手写 frontmatter 摩擦（P1-gate-diagnosis 实证）；核心设计=同源铁律（与 gate 共用 phases.yaml task_fields + 校验值域 + resolve-entry 版本链）+ 自描述（--list/--help/错误给合法值，判据"零协议知识 subagent 照提示填对"）+ 权限引导（角色/阶段/文件三维，明确非安全边界，防造假靠 gate 链）；两阶段落地（**一期**=完整写字段工具：标量+简单 list+gate_commands 正文块+证据字段拒绝端+跨文件提示，2026-08-25 拍板 Q1/Q2/D1；**二期**=证据字段自动写入/账本留痕/跨文件预检，需单独设计）；验收锚=design note §10 十一条 | done | 用户架构建议（2026-08-25 set/get 结构化填写讨论）| TAG0024 | 2026-08-25 | 2026-08-25 |
| RM-AG0049 | P4-review.md 产出声明对齐（协议文档自洽 NIT）：phases.yaml 的 P4 阶段 outputs 未列出 P4-review.md，但 check-gate.py gate_p4 实际要求其存在（P1/P2 的 review 文件在 outputs 有声明，P4 缺失造成"产出声明与 gate 要求"不对称）；修复=phases.yaml P4 outputs 补 `{file: P4-review.md, required: true, status_field: status}`，并核对 check-structure-consistency 是否需同步 | done | 2026-08-25 文件名约定审查（独立评审发现）| TAG0024 | 2026-08-25 | 2026-08-25 |
| RM-AG0050 | P6.5 定位表述统一（协议文档自洽 NIT）：phases.yaml 将 P6.5 列为独立阶段条目，state-machine.md 明确其为"挂载于 P6→P7 转移的强门槛子阶段，不是独立 phase 值"——两处对 P6.5 定位叙述不一致，易误导读者；修复=统一为"强门槛子阶段"口径（state-machine 为准），核对 check-gate/check-judge-verdict 消费端不受影响 | done | 2026-08-25 文件名约定审查（独立评审发现）| TAG0024 | 2026-08-25 | 2026-08-25 |
| RM-AG0051 | CHECK 7 版本漂移防线失效：protocol-tests.yml consistency job 浅克隆无 tag，`git describe --tags` 恒失败走 WARNING——版本漂移在 CI 零机械防线（v0.51.0 教训场景不再 FAIL，防线静默退化）+ 本地"未推送 tag 算最新 tag"假绿 | done | 一致性机制盘点（2026-08-25）| — | 2026-08-25 | 2026-08-25 |
| RM-AG0052 | CHANGELOG 破坏性变更 ↔ UPGRADING 章节对应性无自动检查：CHANGELOG 标"破坏性变更见 UPGRADING vN ②"但无 gate 校验章节存在性——v0.62.0 漏写 UPGRADING 章节实测溜过（发布清单第 3 步纯人工兜底）| done | 一致性机制盘点（2026-08-25）| — | 2026-08-25 | 2026-08-25 |
| RM-AG0053 | 双归零方法论引入失败处理闭环（PeekView 提案）：known-failures 补「复现证据 / 举一反三」列 + 归零检查单（方案 B：参考工具非强制 gate），统一 known-failures / DEBT / 复盘关闭标准；初评核验——复现证据=真缺口（直击 self-authored 防伪，LIMITATIONS 局限 3）、举一反三=缺追溯侧（预防侧 P0 已有同类/影响面预判）、管理归零=复盘归因分层已有（非空白）、「责任明确」改写为「归属明确」（反追责哲学）；方案 C（强制 gate）待 B 实践数据；提案全文见 `docs/design-notes/return-to-zero-proposal.md` | backlog | PeekView 双归零提案（2026-08-28，https://peek.gsis.top/agate-return-to-zero-proposal/raw；本地副本 docs/design-notes/return-to-zero-proposal.md）| — | 2026-08-28 | 2026-08-28 |
| RM-AG0054 | 编排语义统一落地（推进侧状态机 CLI）：推进决策从 orchestrator 临场判断改为查表推进——`agate next`/`agate advance` 推进侧 CLI（复用 check-state-transition.py + check-gate.py exit 三态 + phases.yaml 扩展 next/retreat 字段纳入 S-1/S-2 + agate-retreat-to.py 对接）；CLI 为 /loop 档位 C 可观测层（档位 C 推进强制走 agate next）；编排心智统一文档化（dispatch 五模式锚点 + 实现注记标记）；设计文档 v3b 三轮独立评审闭环（2026-09-02）：`docs/design-notes/design-orchestration-semantics.md` | done | 编排语义讨论 + 设计笔记三轮评审（2026-09-01/09-02）| TAG0027 | 2026-09-02 | 2026-09-03 |

| RM-AG0055 | subagent 存活可观测性与受控自主再派发：命令流日志机制（从平台会话记录外部获取活动信号——Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd，model 思考/输出/执行 tool 三类事件）机械检测两类卡死（调用冻结 = 未结束 call 超期 vs expected×2 复用 RM-AG0023 timeout_seconds + 兜底；活动冻结 = 无未结束 call 且无任何活动超期）+ 逻辑空转（同命令同结果签名重复）+ 截断排除；解析架构按适配器模式（统一 CommandRecord IR + 每平台一个适配器 + 检测引擎平台无关，新增平台只写适配器）；心跳文件生命周期定义；受控自主再派发（执行角色子派发权限下放，judge 类例外）；检测定位'证据+触发核查、不自动判死'；设计文档 v5（4 轮独立评审 + 三平台数据源实机验证闭环 2026-09-03）：`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/` | done | 用户实测观察（长尾 subagent 卡死 vs 正常无法区分，2026-09-01）+ 设计评审与实机验证闭环（2026-09-02/03）| TAG0028 | 2026-09-03 | 2026-09-03 |
| RM-AG0056 | 平台假设扫描器区分代码面与 fixture 数据面 + 阶段自查常驻（TAG0028 复盘机制缺口）：R2 规则（`(^|[\s=(\'\"])python3([\s]|$)`）静态扫描无法区分"测试代码里的命令调用"（应禁止裸 python3）与"fixture 模拟平台日志的数据面内容"（command 字段模拟真实日志本应含 `python3 -m pytest`）——cmdstream fixture 17 处裸 python3 被命中破坏 TAG0011 bdd-8「tests 树 0 命中」，P5 全量 pytest 红灯回 P4 fix3 才闭环；且扫描器不在 P3/P4 gate_commands 常驻面，回归到 P5 全量才暴露 | done | TAG0028 复盘（2026-09-03，retrospective.md §三 机制缺口 2）| TAG0029 | 2026-09-03 | 2026-09-04 |

| RM-AG0057 | 验收盲区机制补强批（TPV0095 跨项目复盘，peekview v0.22.0 交付后暴露 4 类问题查证）：①**测试副作用/环境还原 gate**——BDD 只有正向路径，创建型 E2E（建团队/条目）跑完不清理累积污染共享环境，P6 验收全 PASS 时环境尚干净、残留验收后才暴露（agate 卡 P3 只有测试前失败基线 capture-env-baseline，无测试后残留检查/清理钩子要求；peekview DEBT0008 实证）；②**P1 人工体验路径验收节**——排除 seed/数据改动时 BDD 全用 fixture 验收，"用户按文档 seed 后页面应有内容"成隐性无人验路径（peekview DEBT0009 实证：make debug-seed 后 Teams tab 空）；③**plan-design-review 形态驱动化 + 布局方案 ≥2 候选必审**——现状查证：形态适配机制（ui_render_shape：layout/render_component/temporal_effects 开放集合 → 维度选择 ui_ux_dimensions → 按形态 checklist → 可量化判据禁主观词）已在 P1 analyst/P2 architect/gate（_gate_p1_ui_shape）全链落地，但**评审角色文件 plan-design-review.md 未接到此形态体系**——它是固定 7 维评分（布局一致性/颜色/字体/组件各打分）+ 一行条件启用（渲染时序维度仅声明型启用），无"按受评任务声明的形态加载对应维度组"机制，评审者只读角色文件会拿布局维度评 Canvas 渲染任务或漏评；P2 候选≥2 现为架构级（candidate_count）不下沉 UI 布局层，"行 vs 卡"布局决策无候选权衡必审（TPV0095 实测 N 卡片堆叠过全部 44 BDD）。修复 = plan-design-review.md 改形态驱动评分（先读受评 ui_render_shape 再加载对应维度组评分细则）+ 每个启用维度要求布局方案 ≥2 候选 + 权衡（架构级 candidate_count 下沉 UI 布局层）+ 渲染组件型任务的评审 checklist 对接 architect 渲染正确性 checklist；④**视觉契约断言收录**——"dropdown ≥ trigger"类可量化协调性无 BDD 表达机制（vision-analyst 现为被动截图翻译，P6 无 DOM 度量断言要求），建议收录为可表达子集（E2E DOM 度量断言：宽度/高度/对齐/重叠/溢出可量化断言）+ P2 视觉 checklist/P6 指南提及，作为视觉质量的可表达子集 | done | TPV0095 复盘（2026-09-03，peekview team-visibility 交付后暴露层；RM-AG0021 跨项目反馈机制汇入）| TAG0030 | 2026-09-03 | 2026-09-04 |

| RM-AG0058 | 版本管理生命周期可用性 epic（2026-09-07 扩写整合：TAG0008 解析内核完整，生命周期外壳断裂）：① 入口断链——软链布局下按官方指引跑 agate-install 穿透软链，把 repo/ 与 vX.Y.Z worktree 静默建进源仓库 agate/ 内（2026-09-07 隔离 HOME 实测确认）；先删软链再装则 ~/.agate/scripts 不存在（install 不建根 scripts，工具在 repo/agate/scripts）→ README 入口命令 No such file——两条进入路径均死路；② 元仓库 gap——装出的版本目录 = agateon 整仓（协议在 agate/ 子目录），resolve 返回 vdir 而 gate 在 vdir/agate/scripts → 钉版本 commit 阻断（TAG0008 测试用根即协议模拟 repo，从未覆盖元仓库形态）；③ 无 update 入口——legacy 升级无指引、版本布局升级依赖断链入口。修复方向：install 软链检测 fail-closed + 迁移指引 + 装后建根 scripts；resolve 命中版本目录探测 vdir/agate 或 install 提升 agate/ 为版本根（P2 决策）；统一 update 指引。验收锚 = 隔离 HOME 全新安装 → 项目钉 .agate-version → hook gate 实跑可用（真实元仓库形态端到端） | done | 2026-09-03 实机验证（官方指引部署 v0.66.0+v0.67.0 失败复盘）+ 2026-09-07 生命周期分析 | TAG0032 | 2026-09-03 | 2026-09-07 |
| RM-AG0059 | 任务管理命令化（task management 全生命周期结构化/自动化/命令化——2026-09-03 立项侧纯手工实证：同天手工立项 TAG0029/30/31 踩 3 次表格 | 坑）：现状断层——执行侧已 CLI 化（agate next/advance/dispatch/retreat，TAG0027/28 交付）但**管理侧零工具**（想法→roadmap→立项全手工）；.state.yaml 声称权威源但看板 8 列中 5 列（任务名称/优先级/依赖/创建/更新日期）不在其内，'可从 .state.yaml 重建 active-tasks'是假承诺（重建丢信息）→ 表格必须手编，越积越大（roadmap 56 条 46 条 done 历史）+ 格式摩擦不断（DEBT0019/BB-20：gate 按 | 分列列数精确 9，RM 描述长文本塞格内天然冲突）。方向：① .state.yaml schema 扩元数据字段（title/priority/depends/created/updated/status 值域含 cancelled）成真权威源；② agate-idea（想法→提案）→ agate-rm（提案→RM 条目，YAML 存避免 | 坑）→ agate-init（RM→task 立项：编号+P0-brief 骨架+.state.yaml 初始化+看板渲染+worktree 搭建）→ agate-board（从 .state.yaml 渲染 active-tasks/roadmap 表，消灭手编）；③ 历史/活跃分离（done 46 条移 archived，gate 按 task_id 查不受影响）；验收锚=立项 TAG00xx 全命令化（从 backlog 选 RM 一条命令生成 P0-brief+.state.yaml+看板登记+worktree），看板可再生（删 active-tasks 一条命令重建信息不丢） | backlog | 任务管理现状诊断（2026-09-03，roadmap/active-tasks 单文件增长+格式摩擦+立项手工复盘）| — | 2026-09-03 | 2026-09-03 |
| RM-AG0060 | 派发路由（配置驱动的跨 CLI/model 派发 + tmux 观测）epic——设计三件套：`docs/design-notes/design-dispatch-routing.md`（终版设计）、`docs/research/cross-platform-dispatch-mechanics.md`（三平台 CLI 调用/model 指定/子代理派发/返回识别/续接 客观机制调查，含 A1-A19 实测记录 + §10 落地前复核清单 + §11 未尽项状态）、`docs/reviews/review-dispatch-routing-external-20260908.md` 与 `-round2-` 两轮外部独立评审（FAIL→PASS，核心是"证据强度传递失真"已修）。动机=给角色隔离补模型维度、部分缓解 `LIMITATIONS.md` 局限 2（同源模型系统性盲区，现状 ADR-006 无解），顺带成本/档位/专业度匹配；不解决局限 3。两机制：① 新增项目级 `agate-workspace/dispatch-routing.yaml`（`routes:` + `tier_bindings:`，非协议本体、不受 SELF-GATE）+ 协议本体档位词表 `agate/rules/dispatch-tiers.yaml`（bulk/standard/deep 语义画像 + 出厂默认，改它走 SELF-GATE），按 `(phase,role)` 查表（tier + effort 两正交轴，或 candidates 直接值二选一）→ try-and-fall（无 probe：第一个动作即把真实 dispatch-context 派给首选候选→只在 launch_fail/infra_error/no_parseable_output 三类基础设施信号时逐级回落，收到任何 gate 能评产出即停）→ 全落空回落默认派发（终点恒为同平台同 model、不可配、等价未启用），cli 可为 native（同平台换 model：Claude Code Task 传 model、Codex spawn_agent 传 model+reasoning_effort、OpenCode 走命名 subagent 配置 agents.name.model——三平台"按次生效"均端到端实测）或另一个 CLI（起子进程，各有 -m + 权限绕过 flag，三平台均实测跑通 + Codex 沙箱对照）；新增 dispatch_route 事件与 gate_run 等同构、无差别留痕（呼应局限 3 "fallback 链太顺滑成回避出口"）；决策机械化落 CLI（优先扩 agate-dispatch.py，承接 RM-AG0054 查表推进方向，命令为新增非既有），子进程形式可端到端自动化。② CLI 子进程形式的 tmux 观测层（wrapper 自带退出倒计时改善 attach 端体验；WSL2+tmux3.4 全链路含真人 attach 实测，目标环境需复跑）。存活/卡死检测直接复用 RM-AG0055 命令流机制（Claude Code/OpenCode 适配器现成，缺一个 CodexAdapter 约一个文件）+ 子进程形式另有 wait(pid)/kill-0 更强信号；不自造超时（固定紧超时误杀长任务=违规处理）。架构沿用 RM-AG0046 模式层/检测器层分离。epic（Codex 接入已拆到 RM-AG0061 单独立）。剩下三块：a 配置路由核心 + native(Claude Code/OpenCode) / b 跨 CLI 子进程(spawn + --json 解析 + D2) / c tmux 观测层(可后置/可选、不通过可整体移除不影响 a/b)。**Codex 拆走后 a/b/c 重新评级掉到 medium 附近，可一个 task 内分 P4a/P4b/P4c 串行子批交付**（参照 RM-AG0058/0057 epic + 一个 task），也可再拆多个 TAG——P2 立项定。软点：b 的 `cli: codex` 子进程部分依赖 RM-AG0061（存活检测靠 CodexAdapter），可先发 claude-code/opencode 子进程；c 的 tmux 目标环境验证若任务环境与目标不同则停在"定稿 + 待落地验证"不阻塞 P8。建议排期 RM-AG0061 与 a 并行 → b → c。立项前待办见 design-note §7：确切 schema（tier + effort 两轴 / (phase,role) key）、dispatch_route 事件 + check-events 衔接、决策 CLI 落点、与五模式·自主再派发·单 Agent 模式(has_task_tool:false)的交互、OpenCode 旧 bug② + Codex spawn_agent 完整 schema 补直接实测、Codex API-key 账号 model 阵容自查、tmux 目标环境复跑。与 RM-AG0059（任务管理命令化，backlog）有 CLI 家族(agate-dispatch/推进侧 CLI)重叠，排期注意 | scheduled | 用户需求（2026-09-08 会话：跨 CLI+model 派发 + tmux 观测）+ 跨 CLI 派发路由 v1→v5 与 角色-模型映射 v1→v2 两讨论线合并 + 两轮外部独立评审（FAIL→PASS）| TAG0034 | 2026-09-08 | 2026-09-08 |
| RM-AG0061 | Codex 命令流适配器 + 平台接入（RM-AG0055 §3.4.4 预留的"未来接 Codex/Cursor 只写一个适配器、检测引擎零改动"扩展点的落地 + RM-AG0060 派发路由 epic 的 b 块前置）。设计沿用 RM-AG0055 §3.4.4 适配器契约（`probe`/`list_sessions`/`read_commands` → `CommandRecord` IR），无需独立 design-note；机制事实见 `docs/research/cross-platform-dispatch-mechanics.md`（§1.2/§2/§3/§4.2/§5/§6/§7/§8/§9 + 附录 A4-A8/A12/A17-A19 的 Codex 实测记录）。交付：① `CodexAdapter` 加入 `agate/scripts/agate-cmdstream-adapters.py` 注册表——把 Codex 会话记录（`~/.codex/sessions/` 下 rollout JSONL + `spawn_agent` 子会话）解析为 `CommandRecord` IR；已知坑（2026-09-08 调查）——Codex 无数字 exit code（同 Claude Code/DSH 靠 `is_error`/文本前缀）、`spawn_agent` 子会话疑似 delegationDepth 式独立文件、`codex exec --json` 事件流（thread.started/item.completed/turn.started/turn.completed/turn.failed）可作实时源；检测引擎/阈值/其它适配器零改动。② `agate/platform-notes.md` Codex 章从"待补充"补完整——能力矩阵：非交互 `codex exec`、`-m/--model` 与 `-c model_reasoning_effort` 推理档、权限绕过 `--dangerously-bypass-approvals-and-sandbox` 与中间档 `-s`/`--approve-for-me`（`--full-auto`/`-a` 已弃）、`spawn_agent` 原生子派发按次可传 model+reasoning_effort、`--json` 结构化输出、`resume`；退出码不可靠须解析 `--json`；model 阵容随账号类型变（ChatGPT 账号 `codex exec -m` 只默认 model、`spawn_agent` 的 model 枚举 4 个；API-key 账号未核实）；`multi_agent` feature flag 撑 `spawn_agent`、命名有变更史。③ `agate/SETUP.md` Codex 小节：`npm i -g @openai/codex` + `codex login` + 自动化环境 flag。④ Codex fixture 单测（真实 session 片段解析）+ 真机验证清单（比照 RM-AG0055 三平台数据源验证严格度：`spawn_agent` 完整 schema 直接实测、API-key 账号 model 阵容、`spawn_agent` 嵌套深度、`~/.codex/sessions/` 格式确认）。触发 SELF-GATE（动 `agate/` 下脚本 + platform-notes + SETUP）。验收锚 = Codex 上派一个真实子代理 + `agate-cmdstream-detect.py` 能对 Codex 会话正确判"活着/卡住/空转"三态 | done | RM-AG0055 §3.4.4 预留扩展点 + RM-AG0060 b 块前置 + 2026-09-08 会话对 Codex CLI 的机制调查（已装 codex-cli 0.153.4、ChatGPT 登录、`codex exec`/`spawn_agent`/`--json` 端到端跑通）| TAG0033 | 2026-09-08 | 2026-09-09 |
## 状态标识

| 状态 | 说明 | 何时进入 |
|------|------|----------|
| `backlog` | 待规划 | 新需求/讨论进入 roadmap 时（含来源与日期）|
| `scheduled` | 已拆任务 | 拆任务 → 工作区 tasks/ 建任务目录 + active-tasks.md「待开始」写入任务行（任务行 `roadmap: <条目id>` 关联）|
| `in_progress` | 实施中 | 对应任务进入 P1 起（可选标记，不做强制）|
| `done` | 已完成 | 任务 P8 gate + READY 完成 → 回写 |
| `cancelled` | 取消 | 需求变更/不再需要 → 回写 |

## 条目 id 规则

- 格式：`RM-{项目代号}{编号}`（本仓代号 `AG`，与任务编号 `TAGxxxx` 对齐）。
- 项目局部命名空间内递增，不复用已取消条目的编号。

## 循环规范

1. **需求/讨论 → backlog**：追加 `backlog` 条目，来源列记录需求出处（讨论/评审/复盘），创建列记日期。
2. **条目 → 任务**：拆任务时建任务目录 + active-tasks.md「待开始」区写入任务行（`roadmap: <条目id>`），条目状态改 `scheduled`。
3. **任务完成 → 回写**：P8 gate + READY → 条目改 `done`（或 `cancelled`），更新列记日期。

## 维护规则

1. 只有主 Agent 维护本文件，subagent 不直接写。
2. 条目状态变更与任务看板推进同步（拆任务 → scheduled，完成 → done）。
3. 状态只允许五选一（backlog/scheduled/in_progress/done/cancelled），不写中间态。

---

## RM-AG0001 详情

**check-gate P1 标记反引号包裹识别盲区**

- **问题**：check-gate.py P1 NEED_CONFIRM 检查用行首正则 `^\s*-?\s*\[SUGGEST:` / `^\s*-?\s*\[NO_NEED_CONFIRM\]` 计数。当标记被反引号包住（`` `[SUGGEST: ...]` `` / `` `[NO_NEED_CONFIRM]` ``）时，行首不匹配 → 计数 0；typo 兜底（`grep '\[SUGGEST'` && ! `grep '\[SUGGEST:'`）也不触发（冒号子串仍存在）→ 落入「未检测到 NEED_CONFIRM 声明」WARNING，**不阻断**。
- **影响**：主 Agent 若用反引号包裹标记（markdown 代码样式），P1 gate 静默降级为 WARNING，NEED_CONFIRM 声明形同虚设。中低风险（只影响该标记的强制力，非数据/安全）。
- **建议修复方向**：typo 兜底扩展为「子串存在 + 行首正则不匹配」也报错（类似现有 L121-124 逻辑，改为"有子串但计数为 0"），使反引号包裹被明确拦截而非静默 WARNING。契约格式已在 analyst.md:138-152 / P1-card:78 / task-files.md:186 讲清，无需改文档。
- **验证口径**：新增回归测试——反引号包住 `[SUGGEST: ...]` / `[NO_NEED_CONFIRM]` 时 gate exit 1（而非 WARNING）；合规写法仍通过。
- **攒批说明**：单独立项不值得（一个 gate 正则盲区）。等 gate/协议层问题攒到 2-4 个再拆任务走裁剪 agate（P1-P6，跳过 P7，P2 不可裁剪）。

---

## RM-AG0005 取消说明

**状态**：cancelled（2026-08-13）

**取消理由**：核实后确认**非缺陷**——机制已存在且实测有效：
- `state-machine.md:148` 收尾清单明确要求"调试服务/进程已停止"
- `dispatch-protocol.md:606-607` 要求 P8 产出列出临时服务/进程供主 Agent 清理
- TQC0001 READY 收尾**逐项实查发现并强杀了残留进程**（复盘自述"流程有效"）

冒烟验证的 finally-kill 是**项目侧实现细节**（每个项目冒烟方式不同，agate 不该规定具体实现），不属于 agate 协议 backlog。复盘结论本身是正面案例（收尾兜底生效），非缺陷。若后续要补强，可在 `state-machine.md:148` 加注"冒烟验证启动的进程须由验证者自行 finally-kill，不依赖收尾兜底"——属文档补强，不立项。

---

## RM-AG0007 详情

**UI/UX 质量机制缺失：agate 保证工程质量但不保证 UX 质量**

- **背景**：qtcalc 对比分析（review-qtcalc-basic-vs-qtcalc-comparison.md）——走 agate 的 qtcalc（B）在架构/测试/治理全面领先，但**表达式次显示、键盘输入、UI 样式三项 UX 反而不如没走 agate 的 qtcalc-basic（A）**。B 的 P2 明确"为可测试性让渡视觉打磨"。
- **根因（协议机制）**：
  - `ui_affected` 只触发 **E2E 交互功能测试**（state-machine.md:89-94），不要求视觉/交互质量
  - P2 的 plan-design-review 审的是**架构**（分层/可测性），不是**视觉稿/交互设计**
  - P3 TDD 鼓励 offscreen + objectName 契约 → 抑制视觉打磨
  - P6 视觉验收看"渲染成功"（截图/blocker），无多模态时退化为像素/OCR（RM-AG0004），无"美观/易用"维度
  - **全部 gate 是 exit code，无"用户主观体验"验收标准**
- **影响**：走 agate 的 UI 项目"功能正确但 UX 平庸"；agate 不阻止做 UX，也不要求、不度量、不评审 UX。
- **建议修复方向**：
  1. P1/P2 增加 UX 需求基线（把键盘输入/表达式显示/样式等写成 BDD 可测项 + 视觉验收项）
  2. P2 的 domains 含 frontend 时，plan-design-review 增加视觉/交互维度评审（不只架构）
  3. P6 对 UI 任务强制双证据（截图 + 行为日志）+ 视觉质量 checklist（对齐/间距/反馈/可用性）
  4. 与 RM-AG0004（无多模态视觉能力）关联，落地时一并考虑
- **归属**：独立任务（跨 P1/P2/P6 的协议增强），不并入 TAG0004（TAG0004 是脚本环境适配，本条目是质量机制）

---

## RM-AG0008 详情

**0→1 项目目录结构脚手架：agate 立项时应按最佳实践设计合理目录结构**

- **背景**（用户需求 2026-08-13）：项目从 0→1 开始时，项目文件夹可能还没建立。agate 应该能够按**最佳实践**设计出**合理的目录结构**，不要"东放一点西放一点"。合理的目录文件该建立的就可以建立。
- **现状**：agate 的 P0-brief 只写任务描述/风险/环境，**没有"项目骨架设计"环节**；P1 analyst 分析需求，P2 architect 设计**本次任务**的方案，但都不要求"设计整个项目的目录布局"。
- **问题**：0→1 项目若缺骨架设计，会出现——CMakeLists/源码/测试/文档/构建产物散落、阶段文件与工程文件不同步（qtcalc-basic 复盘问题 C：CMake 引用了尚未存在的文件）、后续每阶段往项目里"加东西"却无整体布局。
- **建议修复方向**：
  1. P1（或 P0）增加"项目骨架"产出：analyst/architect 按技术栈最佳实践输出目录树（如 C++/CMake：src/include/tests/docs/build/deploy；Web：src/components/hooks/pages/api 等）
  2. P2 的 files_to_read + P4 的上下文注入包含项目骨架，实现时遵循既定布局
  3. 骨架作为"第一个可验收产物"（P1 或独立前置阶段），后续阶段产出必须落在骨架布局内
  4. 提供模板（agate/assets/templates/ 下按技术栈的 skeleton-template）
- **归属**：独立任务（协议增加"项目骨架"阶段或产出），与架构演进（RM-AG0009）关联
- **落地（TAG0007，2026-08-20，v0.56.0）**：`P1-requirements.md` 新增可选字段
  `project_phase: bootstrap`（缺省 `established`，向后兼容）；`project_phase: bootstrap` 时
  P2 architect 除 `P2-design.md` 外须产出 `P2-skeleton.md`（含 `## 骨架声明` 标题），模板
  `assets/templates/skeleton-template.md` 用"候选目录集合（源码/测试/文档/构建/部署五类
  抽象标签）+ 项目侧技术栈声明填空区"参数化表达（不硬编码具体语言/框架目录名，ADR-003
  合规，黑名单回归测试覆盖）；`check-gate.py` `gate_p2` 新增判定分支（bootstrap 缺骨架
  exit 1，字段缺失/`established` 行为逐字节不变）。11 条 BDD 中 BDD-1~5 覆盖本条目，P6
  验收全 PASS。**未验证项（诚实说明）**：本次落地未实际跑通一个真实 0→1 新项目走完整
  P1→P4（TAG0007 自身是 established 项目，`project_phase` 字段未在自身声明），触发判据
  "谁来判定 0→1"仍是 P1 analyst 人工判断（与既有 `risk_level`/`domains` 判定方式一致，非
  本条目独有新风险，但机器化判定仍是未来可探索方向）。

---

## RM-AG0009 详情

**code-map + 架构演进纪律：新增代码要从架构设计与设计模式层面考虑**

- **背景**（用户需求 2026-08-13）：项目已正常开展时，要有 **code-map** 思路——能找到有效文件位置；当新增文件和代码时，要从**架构设计、设计模式**层面考虑，**不要用胶水一层一层砌砖块**，砌得老高、摇摇欲坠。
- **现状**：agate 每阶段（P2/P4）只对**本次任务**做设计/实现，**无全局架构视角**；P7 一致性只查本次任务范围。新增代码若不在架构约束内，会逐步偏离最初设计（架构漂移）。
- **问题**：
  - 缺"当前架构全貌"的维护物（code-map：模块/层/依赖方向/关键文件索引）——subagent 每次独立上下文启动，不知道项目里有什么
  - 缺"新增代码必须符合架构"的约束（新增文件放哪层、依赖方向、是否引入新抽象 vs 胶水堆叠）
  - 架构随版本演进的变更记录（重构成一等任务 TAG0002 已支持"重构类"任务，但缺"日常增量也要守架构"的防漂移机制）
- **建议修复方向**：
  1. **code-map 维护物**：项目工作区维护 `CODE-MAP.md`（或并入 `agents/project.md`）——模块/层/依赖方向/关键文件/约定；每次 P4 新增文件时更新；P7 一致性核对 code-map 与实际结构是否漂移
  2. **P2 架构演进检查**：新增/修改文件时，P2 必须回答"新文件属于哪层、依赖方向是否合规、是否复用既有抽象 vs 新砌胶水层"
  3. **gate 或 WARNING**：检测"新增文件数量/新增依赖方向"与 code-map 声明的偏离（如新的 include/import 方向违反分层）
  4. **设计模式约束**：P2 候选方案评审增加"设计模式合理性"维度（是否引入合适抽象，避免 if-else 胶水堆叠）
- **归属**：独立任务（协议增加 code-map 维护 + 架构演进纪律），与 RM-AG0008（骨架）、TAG0002（重构一等任务）关联
- **落地（TAG0007，2026-08-20，v0.56.0）**：`{AGATE_WORKSPACE}/agents/CODE-MAP.md` 作为
  项目架构全貌维护物（复用既有 `agents/` 子目录，未新增 WORKFLOW.md 第 10 个固定子目录），
  五字段（模块/层/依赖方向/关键文件/约定），模板 `assets/templates/code-map-template.md`；
  `P4-implementation.md` 新增「新增文件核对表」小节（implementer 逐个新文件填骨架归属列 +
  CODE-MAP 处理列 `[CODE_MAP_UPDATED]`/`[CODE_MAP_EXEMPT: 理由]`）；`consistency-reviewer.md`
  新增 CODE-MAP 核对职责（人工判断，不做跨语言静态依赖分析，ADR-003 合规）；`check-gate.py`
  新增两处判定：`gate_p4`（机制已采用但缺核对表 → WARNING 不阻断）+ `gate_p7`（
  `code_map_new_files_count`/`code_map_reviewed_count` 两层 pairing 硬校验，与既有
  DESIGN_GAP 判定结构对齐）。11 条 BDD 中 BDD-6~11 覆盖本条目，P6 验收全 PASS。agate 自身
  已 dogfooding 产出 `agate-workspace/agents/CODE-MAP.md` 实例。**未完全解决/已知遗留（诚实
  说明）**：① 依赖方向偏离检测走人工判断 + gate 强制"必须留痕"（`[CODE_MAP_DRIFT:]`/
  `[CODE_MAP_SYNC:]`），未做自动化静态依赖分析（P2 设计阶段已论证违反 ADR-003，非阻塞遗留，
  是既定方向）；② P2 设计模式合理性评审维度**未落地**（建议修复方向第 4 条未实现，留待
  未来任务）；③ 多 worktree/多任务并发更新同一份 `CODE-MAP.md` 的合并冲突机制**未设计**
  （P2 已声明为已知限制，比照 `CHANGELOG.md [Unreleased]` 现有处理方式，未新增锁机制）；
  ④ P7 一致性检查发现 `gate_p4`「## 新增文件核对表」子串判定在自指/dogfooding 场景存在
  假阴性（TAG0007 自身未对新增文件打标准 CODE-MAP 标记），登记 DEBT0017（open，留待后续
  任务修复为整行匹配 + 补齐自我应用）；⑤ CODE-MAP.md 路径解析用本地简化推导而非
  `agate_common.resolve_workspace` 权威函数，登记 DEBT0016（open，标准场景下已论证代数
  等价，非阻塞）。

---

## RM-AG0010 详情

**P2 gate 与 C8 映射表契约矛盾（TPV0090 复盘 M1）**

- **问题**：三层契约不一致——
  - `check-gate.py` P2 L323：**无条件**硬性要求 `P2-review.md` 存在且 status=approved（"P2 评审不可裁剪，必须派发独立 subagent 产出"）
  - `role-system.md` C8 表（L52-56）：backend 域 = "review（P4 后）"，**P2 无触发评审角色**（只有 frontend→plan-design-review、high→plan-eng-review、NEED_CONFIRM→plan-ceo-review 触发）
  - `phase-cards/P2-design.md` L91-96 C8 表：同样 backend 域无 P2 评审
- **后果**：backend 域（low/medium 风险）任务 P2 时，按 C8 表不派评审 → 无 P2-review.md → check-gate exit 1 拦截 → 主 Agent 被迫"自造评审派发"补文件（TPV0090 实测踩坑）
- **影响**：每个 backend 域 P2 都会踩（TPV0091 是 backend+frontend，frontend 触发评审没暴露）
- **建议修复方向（二选一，需设计）**：
  1. C8 表补一句"backend 域 P2 也派 review"（消除契约差，但增加评审开销）
  2. check-gate 对无 C8 触发角色的任务豁免 P2-review 硬性要求（但要保证 P2 评审不裁的原则不破——需定义"无角色时评审退化为 self-review 还是必须派通用 review"）
- **归属**：独立任务（机制契约一致性，涉及 check-gate.py + role-system.md + P2 卡片三层同步）。与 Q2（卡片 phase 契约，TAG0004 内）同类但独立

---

## RM-AG0011 详情

**check-gate P5 gate_commands 计数语义模糊（TPV0090 复盘 M2）**

- **问题**：`check-gate.py` L424，`P5*` 前缀命令都计入 P5 命令数，WARNING "P2 声明了 N 个 gate_commands.P5 命令，请确认已全部执行"。当 P2 声明 `P5/P5_cli_remote/P5_serial` 时计数 3，但实际是"1 主 + 2 辅助"——WARNING 语义模糊，易误解。
- **影响**：轻微（WARNING 不阻断，全执行就通过），但理解成本高，可能误导主 Agent。
- **建议修复方向**：脚本区分"主命令"与"辅助命令"（如 `P5_*` 后缀为辅助），WARNING 文案区分"N 个 P5 命令"与"M 个辅助命令"。
- **归属**：可随 RM-AG0010 或攒批小任务。

---

## RM-AG0012 详情

**自定义角色机制两瑕疵（角色体系验证实测，2026-08-13）**

- **背景**：评估"自定义角色机制是否好用"时实测发现——机制本身可用（模板完整、render 脚本支持 execution-roles/ 与 review-roles/、方法 B 稳妥），但有两个瑕疵：
- **瑕疵 1（模板）**：`agate/assets/templates/dispatch-prompt.md` L10-13 无条件注入"Review 角色特别指令"（产出文件 Header `status:` draft → approved/rejected/needs-revision）。该指令对**评审角色**是必需的，但对**执行角色**（implementer/analyst/test-designer 等）也被注入——执行角色不产评审文件，status 字段语义混乱。实测：render db-specialist（执行角色）后产物含"Review 角色特别指令"。修复方向：按角色类型条件注入（type: review 才注入 status 指令）。
- **瑕疵 2（脚本）**：`agate-render-dispatch-prompt.py` L126-128 角色文件不存在时报错到 stderr，但 **exit 0**（实测 `nonexist-role` → 报错但 exit 0）。主 Agent 可能忽略 stderr 继续走 → 派发失败无声。修复方向：角色文件不存在时 exit 非零（如 exit 2），与"渲染成功"区分。
- **归属**：攒批小任务（模板条件注入 + 脚本 exit code，单点低风险）。

---

## RM-AG0013 详情

**阶段卡缺"同类扫描/影响面梳理"机制层要求（阶段提示词核查，2026-08-13）**

- **背景**：核查 P0-P8 阶段提示词（phase-cards/*.md）时发现——所有阶段卡均无"同类扫描/全仓 grep/影响面梳理/联动"要求。agate 历史多次栽在"修一处漏同类"（M4/M5 的 `[:：]` 只修 check-p6-format.py:84 一处、Q2 只修 P5 卡、TPV0090 backend 域反复踩 P2 契约）。
- **现状**："同类扫描强制要求"只存在于 TAG0005/0006/0007 三个 task 的 P0-brief 里（局部、一次性），**机制层（阶段卡）缺失**——未来其他任务不会有此要求。
- **建议修复方向**：
  1. **P0 卡片**：加"同类/影响面预判"——写 P0-brief 时识别"这个改动会牵动哪些同类/联动处"
  2. **P1 卡片**：加"同类扫描"到产出规格或常见错误——analyst 建立 BDD 时 grep 全仓同类，纳入需求
  3. **P2 卡片**：加"影响面梳理"——architect 画改动影响面（如 ui_affected 64 处消费点），确保联动点同步
- **范围界定（2026-08-13 用户确认）**：**不属于 TAG0005/0006/0007**——那三个 task 只做各自 roadmap 条目的修复（带 P0-brief 已有的局部同类扫描质量保障）；本条目是**协议本体阶段卡增强**，独立 backlog，另行立项（改 phase-cards/*.md 触发 SELF-GATE）。
- **归属**：独立任务（阶段卡协议增强），或并入未来"协议机制增强"类任务。

---

## RM-AG0014 详情

**跨平台/外部环境验证的机制边界（TAG0005/0009 复盘核实，2026-08-14）**

- **背景**：TAG0009 在 Windows CI 排障拉了 11.7 小时（78→29→全绿），复盘归因于"supplementable 是声明非协议"。核实后修正——**主因是机制误用，不是机制缺失**：
- **核实 1：机制误用**——协议已有 `verification_env`（dispatch-protocol.md L884-886）专用于"环境依赖"场景（debug server、测试数据库、临时端口），触发条件含"P0-brief known_risks 含环境依赖"。TAG0009 的 P0-brief **声明了"无法实测 Windows 靠 CI matrix 兜底"**（满足 verification_env 触发条件），但 P1 实际把"真 Windows CI"标成了 `supplementable`（capability_requirements 三态，用于**能力缺失**如缺 vision/skill）——**用错了机制**。跨平台验证是"环境依赖"，不是"能力缺失"。
- **核实 2：真协议空白**——`verification_env` 只定义"如何声明环境"，**没有定义"环境验证失败后怎么办"**：无 CI 轮次预算、无止损轮次、无"一次 CI 验证多个假设"的批处理要求、无 READY 后外部问题归属（原任务补丁 vs 新任务）。11.7 小时拉锯的根源在此。
- **建议修复方向**：
  1. **明确 supplementable vs verification_env 边界**：P1 卡片 + analyst 角色加注——"能力缺失"用 supplementable，"环境依赖/需外部环境验证"用 verification_env；跨平台验证属后者
  2. **补 verification_env 的失败处理协议**：本地无法验证的项，P1 声明时同时列"可验证清单 vs 不可验证清单"；设定每轮 CI 验证多假设的批处理要求；设止损轮次（如 3 轮未收敛必须升级汇报）；定义 READY 后暴露外部问题的归属（补丁 vs 新任务）
  3. **CI 轮次预算进 P1**：risk_level 或专门字段记录"预计外部验证轮次"，让主 Agent 和用户对总时长有预期
  4. **环境准备职责边界（TPV0093 回流，RM-AG0023，2026-08-17 补充）**：verification_env 定义"如何声明环境"，还要补"**谁负责准备环境**"——P5/P6 需运行环境（debug server/测试数据库）时：①主 Agent（P0-brief debug_env 声明，负责启动/维护/关停）还是 subagent（自启无防护 → 卡死）？②多个 subagent（前端+后端）各启各的 debug → 冲突/资源竞争？**建议：环境启动/维护/关停归主 Agent（或 P0-brief 明确单一方），subagent 只消费不启动**；多 subagent 需共享环境时主 Agent 统一启动 + dispatch-context 注入环境访问方式。落点：dispatch-protocol verification_env 节 + P5/P6 卡片
  5. **subagent 能力探测与传递（2026-08-17 用户讨论补充，通用机制扩展）**：supplementable 传递规则（dispatch-protocol L1184）只解决"任务级声明 + 派发注入"，但**主 Agent 能力 ≠ subagent 能力**（主可能无 vision、sub 有，反之亦然），且**平台不暴露 subagent 能力**（Task 工具不返回）。补"**subagent 级能力自查 + 失败回退**"：①派发时 prompt 要求 subagent **先自查能力**（"你有 vision 能力吗？没有就报告，不要静默假设"）；②subagent 能力不可用 → **报告主 Agent**（非静默失败）→ 主 Agent 降级（双证据/像素/人工）或换路径（主 Agent 亲自 / 换 subagent 类型）；③**不写死具体工具**（vision-engine 只是本机例子，项目可能有其他视觉能力）——能力探测按三态（available/supplementable/GAP），GAP 才降级。落点：dispatch-protocol supplementable 规则扩展 + dispatch-context 能力自查要求 + capability_requirements 三态细化
- **归属**：独立任务（协议机制增强：dispatch-protocol + P1 卡片 + analyst 角色），与 RM-AG0013（阶段卡同类扫描）同属"协议机制增强"簇。

---

## RM-AG0015 详情

**文档脚本名引用漂移无 gate 兜底（TAG0010/0011 复盘 + 实测验证，2026-08-15）**

- **问题**：`check-protocol-consistency.py` 的 CHECK 2 引用存在性检查用 `REF_RE = (?<![\w/])((?:docs|assets|scripts)/[A-Za-z0-9_./\-]+\.(?:md|sh|ya?ml|py))`（L238）——**只匹配带 `docs/` `assets/` `scripts/` 前缀的相对路径引用**。协议文档（phase-cards/rules/assets）里大量使用**裸脚本名**（`check-gate.py`、`check-tdd-red.py`，无前缀），实测 `'check-tdd-red.py 确认'` → 正则匹配 `[]` → **完全不被捕获**。脚本被删/改名后文档漂移，consistency 0 ERROR 照过。v0.46.0 的 phase-cards 26 处过时 .sh 引用就是实锤（已修但无 gate 防复发）。
- **问题 2（同批）**：`PROTOCOL_FILES`（L52-64）只含 11 个文件 + `agate/assets/` 目录，**不含 `agate/phase-cards/`、`agate/rules/`** → 这些必读卡引用不存在文件时按"非协议文件"宽松降级 WARNING 而非 ERROR。
- **问题 3（同批，2026-08-15 补充，经数据核查修正）**：`NARRATIVE_DIRS`（L74）按**目录**粗分，未按**文件性质**分——导致两类误配：① 历史目录（`archived/` 62.7% 引用漂移、已完成 task 42.7% 漂移）若严格 = 误报海啸；② 活文档（`roadmap.md`/`active-tasks.md`/`debt/`/进行中 task）若宽松 = 漂移漏网（实测：审查报告引用已归档 `archived/docs-2026-08/plans/agate-test-plan-2026-07-01.md` 的原路径触发 ERROR，改归档路径才通过；进行中 task 引用已删脚本不会被抓）。**按文件性质分类**：严格（活文档，引用必须真实）= roadmap.md / active-tasks.md / debt/ / 进行中 task（phase 非 READY/DONE）；宽松（历史/参考，漂移是常态）= archived/ / reviews/ / plans/ / 已完成 task（phase = READY/DONE）。
- **建议修复方向**：
  1. **新增 CHECK 10**：扫描协议文件中的脚本名引用（裸名 + 相对路径），对照 `agate/scripts/` 实际文件，漂移报 ERROR。豁免：UPGRADING 迁移对照表（旧→新命令对照写旧名是有意保留）、assets/formatters/（仍为 sh）、3 个 hook 薄壳（pre-commit-gate.sh 等）、count-tests.sh
  2. **phase-cards/rules 入 PROTOCOL_DIRS**：把 `agate/phase-cards/`、`agate/rules/` 加入协议目录，享受严格引用检查
  3. **NARRATIVE_DIRS 按文件性质重组**：`agate-workspace/debt/` 移出宽松（evidence 应指向真实路径，债的证据不能是死的）；`archived/ reviews/ plans/` 保持宽松（历史/参考，漂移是常态，实测 62.7% 漂移严格=误报海啸）；`roadmap.md`/`active-tasks.md` 保持严格（活看板，引用应真实）。基线已确认（2026-08-15 0 ERROR）
  4. **进行中 task 动态分类**（并入 CHECK 10 实现，2026-08-15 用户确认）：CHECK 2 扫描 `tasks/` 时读 `{task}/.state.yaml` 的 phase——phase ∈ {READY, DONE} 宽松，否则严格。进行中 task 引用已删脚本/归档路径 = 前提漂移 → ERROR 暴露（复用 agate-state-get.py 读取，TAG0013 的 .sh 引用实测会被抓）
- **验证口径**：新增一致性测试——协议文件引用已删脚本名 → ERROR；引用现存脚本 → 通过；UPGRADING/formatters/薄壳豁免路径不误报
- **归属**：独立任务（协议机制增强），与 RM-AG0013/0014 同簇。

---

## RM-AG0016 详情

**subagent 派发编排机制（全阶段，TAG0010/0011 复盘 + 用户扩展，2026-08-15）**

- **背景**：TAG0010 批次 0 卡死（agate_common 整库 + ci-gate-backstop + 3 bats 一次派发，用户中止）；TAG0011 拆 19 批后零卡死。复盘 §3.1 称"P2 批次设计有效"，但**协议本身没有任何批次粒度机制**——"表 E 批次设计"是任务内部临时产物，非协议要求。工作量高的形态不限于 P4——P1/P2 单发 architect/analyst 扛整任务、P3-P6 分散的"按包并行"（P3/P4/P5/P6 卡片各写各的）、多包 P8 releaser 单发，都可能过载。
- **根因**：「任务粒度指引」只存在于 `dispatch-protocol.md` L639-663（产出 ≤3 文件 / 输入 ≤3 个），**无任何其他文件引用它**（P2-design.md / architect.md / 派发模板均无）。且只覆盖"数量上限"，**无工作量评估方法、无编排模式定义、无并行规则**（上限/失败处理/共享文件）。P2 architect 设计批次时看不到粒度约束，主 Agent 派发时靠记忆——渐进披露下不一定读到 dispatch-protocol。
- **现状核查**（全阶段）：
  - P3/P4/P5/P6 有"按包拆分并行"（各卡片独立定义，非统一机制）
  - P7 明确不拆分（一致性需跨文件对照）
  - **P1/P2 无任何拆分/编排机制**——P2 恰是最需要"先理解后拆"的阶段（architect 要先读 P1 全貌才能规划后续批次）
  - 并行规则分散且缺：无并行上限（平台并发 + 主 Agent 上下文）、无并行失败处理（失败批单独 retry vs 全批重跑）、无共享文件统一约束（仅 P4 有）
- **建议修复方向**（统一机制，全阶段适用）：
  1. **工作量评估**：复杂度 = 产出规模/输入规模/改动性质/耦合度/认知负荷 五维评级 → low/medium/high
  2. **五模式编排**：
     - 模式 1 单发（low）：一个 subagent 直接做
     - 模式 2 静态拆批（medium）：批次表（P2 预设计 或 本阶段派发前设计），按批执行
     - 模式 3 并行（无依赖且 ≤medium）：多 subagent 并行 + 共享文件后处理
     - 模式 4 先理解后拆（high/结构不明）：侦察 subagent 读全貌产出拆分方案 → 按方案派执行（并行/串行）→ 合并（轻量拼装由主 Agent/单 subagent；重量整合派整合 subagent）
     - 模式 5 串行链（有依赖）：分批串行
  3. **并行规则统一**：并行上限默认 3（可配置）；失败批单独计 `retries[Pn]` 不重跑成功批；各批只改自己范围、共享文件由主 Agent 统一后处理（P4 约束推广到全阶段）
  3.5 **运行时管控（TPV0093 回流，RM-AG0023）**：①**timeout_seconds 字段**——gate_commands/dispatch_plan 声明命令时同时声明预期时长（如 `P5_e2e.timeout: 600`），派发时硬编码到 subagent 命令；**阈值须合理**（pytest 全量 ~70s/CDP E2E 需更大，不能低到长命令误判失败）+ **执行留痕**（timeout 判定基于真实执行，不拍脑袋）；②**dispatch-prompt 超时兜底节**——"每个 bash 命令必须设 timeout（≤预期时长×1.5）；超时→停止+写 progress 返回；遇非预期失败→记录后返回主 Agent，禁止自行深入诊断"；③**资源密集型默认串行**——backend 全量 pytest（xdist）+ frontend 全量 vitest 属高资源命令，默认串行，需并行时评估 CPU/IO 竞争；④**progress 心跳扩展**——每个 bash 命令**前**写 progress（`[HH:MM] 开始执行: ...`），主 Agent 可判断 subagent 是否卡在命令中（TPV0093 实证：卡死时命令执行中不写 progress，心跳失效）
  4. **落地位置**（单一权威源）：dispatch-protocol.md 新增「派发编排机制」节（升级扩充现有任务粒度指引）；P2-design.md 新增 `dispatch_plan:` 机器字段；各阶段卡片加"编排模式"引用（指向权威节，不重复定义）；dispatch-prompt.md 内联"产出>3 或输入>5 必须分批或说明"兜底
- **验证口径**：`dispatch_plan:` 字段可被 gate 校验（复杂度/模式/并行上限一致性）；派发模板约束主 Agent 每轮可见；模式 4 流程有测试覆盖（侦察→执行→合并 三阶段）
- **参考实施计划（2026-08-15）**：`agate-workspace/plans/agate-dispatch-orchestration-20260815.md`（已通过 plan-eng-review 三轮评审，approved，2026-08-15）——含字段契约（frontmatter 单行 flow YAML + op `dispatch_plan` 子进程读取 + JSON 输出 + 不入 frontmatter-check schema）、6 个 Task（TDD 驱动）、验收标准。实施本条目时作为**参考输入**，不是替代。
- **⚠️ 阶段完整性声明**：**有实施计划 ≠ 裁剪 agate 阶段**。本条目作为任务执行时，仍须走完整 agate 流程（P0 立项 → P1 需求基线 + BDD → P2 设计 → … → P8 发布），P1/P2 须对照本 roadmap 详情 + 参考计划重新产出当前任务自己的需求基线与设计（可引用计划内容，不可跳过阶段）。计划文档只提供"做什么、怎么落地"的既有分析，不豁免本任务的质量 gate。同理适用于其他含参考计划/设计文档的条目。
- **归属**：独立任务（协议机制增强：dispatch-protocol + P2-design.md + 各阶段卡片 + 派发模板 + 角色文件），与 RM-AG0013/0014/0015 同簇，工作量最大，建议单独立项。

---

## RM-AG0017 详情

**self-gate 触发面缺仓库根级文档（TAG0010/0011 复盘，2026-08-15）**

- **问题**：`commit-msg-self-gate.py` 的 `_SELF_GATE_RE`（L38-40）覆盖 `agate/scripts/*.sh|*.py`、`agate/*.md`、`agate/*/*.md`、`SELF-GATE.md`——**不含仓库根级文档**：README.md / AGENTS.md / CHANGELOG.md。
- **影响**：改仓库根级协议文档（README 门面、AGENTS 开发指引）不触发 self-gate WARNING，绕过语义审查。本次文档体系更新（README/AGENTS 重写）即未走独立评审。
- **注意**：复盘原文称"SELF-GATE.md 不在触发面"是**错误**（实测正则包含它）——本条目只补 README/AGENTS，CHANGELOG 变动频繁且非协议语义，豁免。
- **建议修复方向**：`_SELF_GATE_RE` 扩展匹配 `README.md`、`AGENTS.md`（CHANGELOG.md 豁免，理由：频繁变动 + 非协议语义）。SELF-GATE.md 已覆盖，不加。
- **验证口径**：新增测试——staged 含 README.md/AGENTS.md → self-gate WARNING 触发；CHANGELOG.md → 不触发
- **归属**：独立任务（脚本 + 测试），低优先级，可与 RM-AG0015/0016 攒批。

---

## RM-AG0018 详情

**复盘/评审发现未接 tech-debt 登记触发点（独立观察 + DEBT0001 破冰，2026-08-15）**

- **背景**：TAG0001 技术债闭环（v0.43.0）建成后，`agate-workspace/debt/tech-debt.md` **零登记**（目录都不存在）。复盘/评审发现的缺陷只写进复盘文档或 roadmap backlog，从不走 DEBT 路径。独立观察者指出：复盘自己发现"文档脚本名引用漂移无 gate 兜底"（CHECK 10 缺口）并建议修复，但没登记进刚建好的技术债系统——机制建好了，发现渠道没接上。
- **根因**：tech-debt 只有 **retreat 回退**一个自动触发渠道（`check-debt.py --retreat-coverage` 强制登记 source: retreat）。**review / retrospective 来源无登记钩子**——发现者直接把缺口写进复盘/roadmap 就完事，tech-debt 无感知。这不是"习惯问题"，是**机制缺触发点**（review/retrospective 无法机器检测，设计上就没强制，但可在模板层加要求）。
- **本次处置（已落地，2026-08-15）**：
  1. **DEBT0001 登记**：`agate-workspace/debt/tech-debt.md` 首条真账（CHECK 10 缺口，source: retrospective，task_id: RM-AG0015 关联），`check-debt.py` 校验通过——tech-debt 从零破冰，验证系统真实可用
  2. **postmortem-template.md 加"技术债登记"核对行 + 机制说明**：复盘/评审发现缺陷或缺口（影响验收真实性或让未来变更更贵）→ 必须登记 DEBT 或 roadmap backlog，二选一注明去向；未登记 = 机制缺口（引用 DEBT0001 教训）
- **建议修复方向**：
  1. **模板层触发**（已做）：postmortem-template 核对清单加"技术债登记"行——复盘时强制核对"本次发现是否登记了"
  2. **可选增强**：`check-retrospective.py`（P2.12）输出加一行提醒"复盘发现的新缺口请登记 DEBT/roadmap"（纯提醒不拦截，与 P2.12 精神一致）——是否做可评估
  3. **克制原则**：不做"发现必须登记 DEBT"的硬 gate——tech-debt-template 三分法明确"不影响验收也不影响未来成本的不登记"是合法出口，硬登记会让登记簿变垃圾场
- **归属**：本条目主体（模板层 + 提醒）已随本次处置落地，**剩余可选增强**（check-retrospective 提醒）低优先级，可与 RM-AG0017 攒批。

---

## RM-AG0019 详情

**P0-brief 时效性验证缺失（用户提问，2026-08-15）**

- **问题**：P0-brief 是**立项时点的快照**（task/known_risks/executor_env/env_constraints 反映当时状态），状态机把它当恒真前提——P0 完成即锁死，之后任何阶段不再回头校验。任务立项后搁置再启动时（如 TAG0008：8-13 立项写 .sh 路线，8-15 启动时 TAG0010 已全量 Python 化），P0-brief 前提可能已与最新项目状态漂移。若直接按错误 P0 推进实施，产出是**放大版且错误的 task**。
- **现状核查**（无此机制）：
  - P0 卡片「环境自检」（P0-orchestrator.md L29-34）：只查 debug 环境/测试框架/浏览器**运行时可用**，不查 P0-brief 内容是否过时
  - P0 推进条件（L42-44）：四字段齐全 + 环境自检 + 看板行——全是"是否做了"，无"前提是否仍成立"
  - P1 输入校验（P1-requirements.md L30/35）：P0-brief 完成 + 作为输入——**P1 在过时基础上工作**
  - state-machine L77：`P0 --[P0-brief 完成，四字段自查通过]--> P1`——无时效维度
  - 现有 `env_state` 环境一致性验证（state-machine L300-306）只覆盖**运行时资源**（URL/端口），不覆盖**立项前提**（技术路线/依赖/风险）
- **问题分层**：
  1. **检测缺失**：无环节检测"P0-brief 前提 vs 当前状态"是否漂移
  2. **更新缺失**：检测到漂移后，无流程定义"如何更新 P0-brief 并重新进入决策"（轻更新 vs 重新立项/可行性分析）
- **建议修复方向**：
  1. **P0 → P1 前提校验**：启动（含搁置后启动）时，主 Agent 对照当前项目状态核对 P0-brief 四字段前提（技术路线/依赖/风险/环境）是否仍成立；有漂移 → 更新 P0-brief（标注更新日期 + 变更点）
  2. **重启动判断**：漂移严重（技术路线全变/前置任务完成改变依赖）→ 需重新立项分析/可行性分析，而非直接 P1
  3. **P1 analyst 职责扩展**：需求质疑前先校验 P0-brief 前提，发现过时标记 `[P0_STALE]` 交主 Agent
  4. **落点**：P0 卡片加"前提时效性自检" + state-machine P0→P1 转移条件加"前提验证" + P1 卡片加"P0-brief 前提校验"
- **验证口径**：搁置后启动的任务，P0-brief 前提漂移被检测 → 更新或重立项；P1 在验证过的 P0-brief 基础上工作
- **归属**：**并入 TAG0012**（2026-08-15 决策）——改动域与 TAG0012 高度重叠（P0/P1 卡片 + analyst + dispatch-protocol/state-machine），且与 RM-AG0014 同类（声明有时效处理无）；分开做会两轮改同文件。实施时 P1 须按"哪些卡/哪些节"组织 BDD，与 RM-AG0013/0014 一并规划。

---

## RM-AG0020 详情

**复盘机制统一（TAG0013/0014 复盘讨论，2026-08-16）**

- **问题**：复盘机制在协议层面残缺且不自洽：
  1. **模板缺正文结构**：`docs/reviews/` 下的 `postmortem-template.md`（→ 已于 TAG0015 迁移至 agate/assets/templates/retrospective-template.md）只有"机制触发核对清单"（retry/SCOPE+/gate 等是否触发），**无复盘正文结构**（做得好的/发现的问题/改进措施）——正文靠执行者临场拼（TAG0013 复盘 84 行是拼出来的，非模板定义）
  2. **内容无价值标准**：不定义"什么值得写"——易沦为流水账（复述 P1-P8 过程）/自我表扬（只写做得好的）；有价值的内容是"机制缺口 + 可复用模式 + 归因到可行动层面的问题"
  3. **标的矛盾**：`check-retrospective.py`（P2.12）只在**异常模式**（retry 超限/SCOPE+/override）时提醒复盘；但正常任务（TAG0013 无 retry）也写了复盘（因发现机制缺口）——无统一标的定义
  4. **路径矛盾（三处不一致）**：复盘是**该 task 的产物**（绑定具体 task，内容全是该 task 的事，与任务内 P{n}-review.md 同类）→ 应放 `{AGATE_WORKSPACE}/tasks/{Txxx}/`（如 `{Txxx}/retrospective.md`，与 P1-review.md 等并列）；但实际先例（TAG0013/0014）写在 `docs/reviews/retrospective-*.md`（老布局习惯），check-retrospective 又提示 `docs/releases/v{version}-retrospective.md`——三个位置互不一致。**区分**：工作区顶层 `{AGATE_WORKSPACE}/reviews/` 放**跨任务评审**（alignment-review / plan-review 等独立评审报告，非绑定具体 task）；task 内复盘与 P{n}-review.md 同类，归 `tasks/{Txxx}/`。postmortem-template.md 在 docs/reviews/ 合理（模板描述流程规范，非流程产出）（→ 已于 TAG0015 迁移至 agate/assets/templates/retrospective-template.md）
  5. **归因纪律缺失**：不区分"执行错误（agent 没遵守规则 → 修纪律）" vs "机制缺口（协议没定义 → 修协议）"——归因错层，措施落空（如把协议缺陷误判为执行粗心）
  6. **产出流向缺失**：复盘发现机制缺口 → 应流向 roadmap（RM 条目）或 DEBT 登记，但无强制/约定（check-retrospective 提醒行已加，TAG0018）
- **建议修复方向**：
  1. **复盘正文结构模板**：事实基线（客观数据）/ 做得好的 + 可复用模式（问"该固化进协议吗"）/ 发现的问题（分层归因：管理/技术/agate 机制/agent 执行，标注"执行错误 vs 机制缺口"）/ 改进措施（落到文件/字段/gate）/ 核对清单（沿用 postmortem-template）
  2. **标的定义**：①异常模式（retry 超限/SCOPE+/override）→ 强制 ②发现机制缺口（任何任务）→ 强制 ③高价值任务（大型/跨模块/首次新做法/用户要求）→ 建议。正常完成且无机制发现 → 可不复盘
  3. **路径统一到 task 产物**：复盘产出放 `{AGATE_WORKSPACE}/tasks/{Txxx}/retrospective.md`（复盘是绑定该 task 的产物，与任务内 P{n}-review.md 同类——2026-08-16 用户判断）；check-retrospective 输出同步；工作区顶层 `reviews/` 保留给跨任务评审（alignment-review/plan-review）；postmortem-template.md 保留在 docs/reviews/（模板描述流程规范，非流程产出）（→ 已于 TAG0015 迁移至 agate/assets/templates/retrospective-template.md）。已存在的 docs/reviews/retrospective-*.md 存量复盘迁移到 `tasks/{Txxx}/` 或标记旧布局
  4. **归因纪律 + 产出流向**：每条问题标"执行错误/机制缺口"；机制缺口 → 立 RM/DEBT；执行偏差 → 更新角色文件/派发模板/阶段卡
  4.5 **项目资产沉淀（2026-08-17 用户补充）**：复盘"做得好的/可复用模式"节要**区分两类可复用资产并明确流向**——①agate 机制可复用 → 回馈 agate（RM-AG0021）；②**项目可复用资产**（临时命令/脚本如 make/run-e2e、经验教训如 xdist flaky/timeout 陷阱）→ **提炼到项目基础设施（Makefile/scripts/）+ 项目记忆（agents.md/project.md）**。复盘模板强制问："本次产生的临时命令/脚本/经验，哪些该沉淀为项目固定资产？沉淀到哪？"——解决"agent 很难自主发现可提炼资产"的盲区（TPV0093 复盘：run-e2e-tests.sh 无 timeout 是临时脚本，应提炼为项目基础设施并加防护；flaky 应记 agents.md）
  5. **事实依据三层（2026-08-16 补充，核心）**：复盘的机理分析（为什么这么做）不能只靠 git log（结果级）——因果链在主 Agent/subagent 的 session 里，session 会 compact 导致事实源丢失。按可靠性分层：
     - **L1 仓库落盘（永久）**：git log / 产出文件 / orchestrator-log / progress.md
     - **L2 会话 checkpoint（任务期间持续落盘，新增）**：防 compact 的核心保障——orchestrator-log 从"只记决策"扩展为"决策 + 依据"（每次派发记"给了哪些输入/为什么"、每次 gate 判定记"基于什么"）；每个阶段 gate 通过时落盘 `P{n}-checkpoint.md`（本阶段异常/关键判断/subagent 表现）；P8 完成时先落盘 `task-session-summary.md`（任务级过程摘要）
     - **L3 平台 session 导出（补充，可能已 compact）**：OpenCode / Claude Code 会话历史可导出，作补充事实源，不作为依赖。**OpenCode 提取指南已实现**：`docs/reviews/opencode-session-extraction-guide.md`（TPV0093 验证——opencode.db SQLite 表结构/主会话与 subagent 识别/part 工具调用提取/`$.state.time` 卡死定位/证据包隔离大库）
  6. **复盘时机前置（2026-08-16 定稿）**：**过程摘要（L2）在任务完成时立即落盘（趁 session 完整）**，正式复盘在 PR merge main 后基于摘要写——防止 session compact 后事实源丢失。时机链条：`P8 完成 → 落盘 task-session-summary.md → PR merge main → 基于摘要写正式复盘 → 登记 RM/DEBT`
  7. **平台导出工具书（2026-08-16 补充，可做）**：产出平台 session 导出指南（各平台 session 存储位置/导出方法/如何定位某次 subagent 派发过程）。找对方法即可用，不作协议硬依赖
- **验证口径**：复盘文档含"做得好的/发现的问题/改进措施"三节 + 每条问题标归因层面 + 措施写落点；check-retrospective 提示路径与实际一致；复盘文档"事实依据"节列出 L1/L2/L3 来源；长任务复盘能在 session compact 后仍写出完整因果链（L2 落盘生效）
- **归属**：独立任务（协议机制增强：postmortem-template + check-retrospective.py + orchestrator-log 扩展 + checkpoint 落盘 + 复盘文档规范 + session-export-guide），与 RM-AG0018（tech-debt 登记触发点）同簇。

---

## RM-AG0021 详情

**agate 跨项目反馈机制（TAG0014 复盘讨论，2026-08-16）**

- **问题**：其他项目用 agate 实施时的复盘，其中**归因到 agate 机制层/agent 执行层**的问题（如"CHECK 10 漏检裸名"、"主 Agent 未遵守粒度指引"）对 agate 项目组有直接价值（修复惠及所有项目），但**没有机制回馈**。协议无遥测/反馈（rg 确认零命中）。
- **内容边界**（只回传 agate 相关，不涉项目敏感信息）：复盘文档的"发现的问题"已标归因层面——**归因含 agate（机制缺口/执行偏差）的条目才回馈**；归因到管理/技术层（项目自身，如"我们 DB 迁移写错了"）的不回馈。敏感/隐私保护 = 只回传 agate 归因条目，不传整个复盘。
- **建议修复方向**：
  1. **结构化 agate 反馈节**（层 0 产出结构化）：复盘文档加 frontmatter 机器字段（`mechanism_issues`/`execution_issues`/`feedback_ready`）+ `## agate 反馈` 结构化节（每条 = 一个候选立项：问题/归因/建议/涉及版本）——项目写这节时天然知道内容边界
  2. **提取脚本 `agate-feedback.py`**：解析复盘文档的"agate 反馈"节 → 匿名化（去项目名/路径）→ 生成结构化 JSON → 提示提交（手动/半自动，如 gh issue / PR）
  3. **开关**：`.agate.env` 或配置文件 `AGATE_FEEDBACK=on/off`，**默认 off（opt-in，隐私优先）**；关闭时完全不提取不提交
  4. **回传通道**：提交到 agate 仓库（issue/PR）或结构化目录；agate 项目组收到后可直接立 RM/DEBT
- **分阶段**：① 复盘模板加结构化反馈节（内容边界机制先建立）② `agate-feedback.py` 提取+匿名化（手动触发）③ 全自动遥测（价值验证后可选，需 opt-in 明确）
- **⚠️ 触发方式（2026-08-17 修正）**：TPV0093 回流实证——回流是**用户主动要求外部项目写复盘**才触发，**非项目自发回馈**。RM-AG0021 的"回馈通道"（项目复盘→提取→提交）依赖外部项目**愿意做**，而外部项目通常不会主动为 agate 写复盘（无动机）。**设计修正**：反馈机制的触发源主要是**用户/agate 项目组推动**（要求外部项目复盘时提醒其登记 agate 反馈节），而非"项目自动回馈"假设。`agate-feedback.py` 的价值在"把复盘里散落的 agate 归因条目结构化提取"，降低回馈成本，但不解决"外部项目没动机复盘"的根因——后者靠用户推动 + 反馈节模板引导。
- **验证口径**：复盘文档含可解析的"agate 反馈"节；`agate-feedback.py` 正确提取且不含项目敏感信息；AGATE_FEEDBACK=off 时不产生任何输出
- **归属**：独立任务（协议机制增强：复盘模板 + 提取脚本 + 开关），与 RM-AG0020（复盘机制，反馈的内容来源）关联，依赖 AG0020 的复盘结构化产出。

---

## RM-AG0022 详情

**协议规则结构化层（层 1，TAG0014 复盘讨论，2026-08-16）**

- **问题**：agate 协议本体是自由文本（WORKFLOW/dispatch-protocol 等 8000+ 行 markdown），但**真正消费它的是 agent**——agent 每轮要"读全文 → 理解 → 提取规则"，上下文开销大、易歧义、理解漂移（同一规则不同段落表述不同）。用户痛点："受够了人类本身不太看的文档也用自由协议，导致 agent 摩擦过多"。gate 机器可判定性只做到了"gate 输出"，没做到"协议定义"。
- **现状基础**（层 0 已有）：task 产出结构化已有（frontmatter schema + 20 个机器字段 op + dispatch_plan），证明"机器读结构化、人读自然语言"的分层可行。层 1 是把**协议规则本身**（非 task 产出）也结构化。
- **建议方向**（需先设计 schema 方案再立项，**本条目仅为方向记录**）：
  1. **规则抽离**：`phases.yaml`（P0-P8 阶段契约：gate 命令/产出文件/转移条件）、`dispatch.yaml`（派发模板结构/粒度上限/并行规则）、`roles.yaml`（角色→阶段→输入/产出映射）、`markers.yaml`（标记名/触发条件/gate 行为枚举）
  2. **并存**：结构化定义 + 自然语言解释并存——机器读 yaml（规则快照，确定性），人读 markdown（叙事/理由/教训）；一致性由 gate 校验（扩展 check-protocol-consistency.py：yaml vs md 同步）
  3. **定义生成（层 2，可选进阶）**：从 yaml 自动渲染文档/派发 prompt——根治"双源手动同步"（TAG0014 N6 修复的痛点）
- **价值**：agent 读 yaml 快照而非全文 → 上下文开销从"读全文"降到"读 schema"；规则变更只改 yaml + 自动同步文档 → 消除双源漂移
- **⚠️ 规模与风险**：改变 agate 根本形态（纯文档 → 文档 + 结构化定义），工作量大、需专门设计（yaml schema 方案、agent 消费方式、与现有 md 的关系）。**不在近期任务内做**；先由 RM-AG0021（复盘/反馈结构化，层 0 增量）落地验证"结构化产出"收益，再推进层 1。
- **归属**：独立大方向（协议架构演进），需专门设计规划后立项，不拆入现有任务。

---

## RM-AG0023 详情

**subagent 运行时管控（TPV0093 跨项目反馈回流，2026-08-16/17）**

- **来源**：**用户主动要求 PeekView 项目组写 TPV0093 复盘**（非其自主识别）——复盘发现 3 次 subagent 卡死等 agate 机制缺口 → **经 RM-AG0021 跨项目反馈机制回流**（第一个回流案例）。**说明**：回流依赖外部项目愿意/被要求写复盘，非自动机制——RM-AG0021 的"主动回馈"设计仍需在反馈机制中明确（当前是用户推动，未形成项目自发的回馈通道）。复盘全文存外部（PeekView 侧），agate 侧记录结论与流向。
- **问题**：TPV0093 执行中 3 次 subagent 卡死（`cat vitest.config.*` 一个 <1s 命令挂 3.1 小时、`make test-quick` 挂 188 分钟），根因：
  - **P-1 subagent bash 命令无超时兜底**：命令挂起 = subagent 挂起 = 主 Agent 无感知（progress 心跳在命令执行中不写）
  - **P-2 subagent 遇 flaky 偏离约束**：遇偶发失败倾向自由诊断而非按约束"报告"（dispatch-context 写了约束但面对 flaky 自然偏离）
  - **P-3 并行未评估资源竞争**：pytest 16 workers + vitest 同时跑 → 双倍卡死风险
  - **P-4 P5 测试与实现同源**：P3 测试没覆盖列表+is_starred 路径，P5 跑"自证"测试 → bug 漏到 P6
- **建议修复方向**（TPV0093 §6.1 A-1~A-4 + 用户补充）：
  1. **A-1 timeout_seconds 字段**：gate_commands 声明命令时同时声明预期时长（如 `P5_e2e.timeout: 600`），verifier 派发时从 P2 读取并硬编码到 subagent 命令 → **并入 RM-AG0016**（dispatch_plan 字段扩展）
  2. **A-2 dispatch-prompt 超时兜底标准节**：模板级加入"每个 bash 命令必须设 timeout 参数（≤ 预期时长×1.5）；命令超时 → 立即停止写 progress 返回；遇非预期失败 → 记录后返回主 Agent 判定，禁止自行深入诊断" → **并入 RM-AG0016**（派发模板）
  3. **A-3 资源密集型默认串行**：P5 卡片明确"backend 全量 pytest（xdist）+ frontend 全量 vitest 属高资源消耗命令，默认串行；需并行时评估 CPU/IO 竞争" → **并入 RM-AG0016**（并行规则）
  4. **A-4 progress 心跳扩展**：分阶段落盘补"每个 bash 命令**前**写一条 progress（`[HH:MM] 开始执行: make test-quick`）"——主 Agent 可据 progress 时间戳判断 subagent 是否卡在命令中（当前只在命令后写，卡住时无信号）→ 独立小改进
  5. **环境准备职责边界（用户补充）**：谁负责启动/维护/关停 debug 环境——P5/P6 需运行环境时，主 Agent（P0-brief debug_env 声明）还是 subagent（自启无防护 → 卡死）？多 subagent（前端+后端）各启各的 → 冲突/资源竞争。**并入 RM-AG0014**（verification_env 定义"如何声明"，补"谁负责准备"）
  6. **timeout 合理阈值 + 执行留痕（用户补充）**：timeout 必须给合理时间——阈值不能低到长命令误判失败（pytest 全量 ~70s、CDP E2E 需更大）；执行命令要留痕（timeout 判定基于真实执行，不拍脑袋）。**并入 A-1/A-2**（timeout_seconds 设计核心约束）
  7. **项目资产沉淀**（复盘时提炼临时命令到项目基础设施 + 经验记 agents.md）→ **已并入 RM-AG0020**（复盘模板"可复用模式"节扩展）
  8. **xdist 试点（2026-08-17 外部 agent 分析补充）**：P5 单发场景（无并行派发同时跑）试点 `-n auto`，观察真实 CI（4 核）加速比；**不与模式 3 并行派发叠加**（本条目 A-3 已记"资源密集默认串行"）——测试套件隔离性实测过关（823 一致），加速收益需真实 CI 验证。实施时与 A-3 一并评估
- **验证口径**：dispatch-prompt 含超时兜底节；gate_commands 支持 timeout_seconds；P5 资源密集默认串行；progress 命令前写心跳；verification_env 定义环境准备职责
- **归属**：跨条目反馈回流，已并入（2026-08-17）——A-1/A-2/A-3 + timeout 阈值 + A-4 progress 心跳 → **TAG0012**（协议机制批，因 TAG0014 已完成 v0.49.0 未含新增内容，运行时管控并入 TAG0012 的 dispatch-protocol/派发模板/P5 卡改动）；环境职责 → **TAG0012**（RM-0014 verification_env）；项目资产沉淀 → **TAG0015**（RM-0020 复盘模板）。**本条目作为反馈源头记录 + 分发标记，内容已并入上述 task 的 P0-brief**

---

## 已归档 RM 条目（done，折叠）

<details>
<summary>已完成的 RM（点击展开）——历史归档，详情见各条目</summary>

| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |
|----|------|------|------|----------|------|------|
| RM-AG0001 | check-gate P1 标记反引号包裹识别盲区 | done | TPV0091 复盘 §11.1 B1（2026-08-13）| TAG0004 | 2026-08-13 | 2026-08-15 |
| RM-AG0002 | check-tdd-red 无 formatter 时 A/B 类盲区（编译失败误判红灯）| done | TQC0001 复盘 Q3 残留（2026-08-13）| TAG0004 | 2026-08-13 | 2026-08-15 |
| RM-AG0003 | subagent 短命会话制度化重试（空返回自动重试一次 + <1min 告警）| done | TQC0001 复盘 Q4（2026-08-13）| TAG0005 | 2026-08-13 | 2026-08-15 |
| RM-AG0010 | P2 gate 与 C8 映射表契约矛盾：backend 域 P2 无评审角色但 check-gate 硬拦 P2-review.md | done | TPV0090 复盘 M1（2026-08-13）| TAG0005 | 2026-08-13 | 2026-08-15 |
| RM-AG0011 | check-gate P5 gate_commands 计数语义模糊（P5* 前缀全算，WARNING 误解主/辅命令）| done | TPV0090 复盘 M2（2026-08-13）| TAG0005 | 2026-08-13 | 2026-08-15 |
| RM-AG0012 | 自定义角色机制两瑕疵：dispatch-prompt 无条件注入评审指令到执行角色 + render 脚本角色不存在时 exit 0 | done | 角色体系验证（2026-08-13）| TAG0005 | 2026-08-13 | 2026-08-15 |
| RM-AG0016 | subagent 派发编排机制（全阶段）：工作量评估 + 五模式编排（单发/静态拆批/并行/先理解后拆/串行链）+ 并行规则统一；P1/P2 补空白、P3-P6 统一现有分散"按包并行" | done | TAG0010/0011 复盘（2026-08-15）+ 用户需求扩展（全阶段）| TAG0014 | 2026-08-15 | 2026-08-17 |
| RM-AG0015 | 文档脚本名引用漂移无 gate 兜底：CHECK 2 只捕获 `scripts/` 前缀引用，裸脚本名（phase-cards/rules 全是）完全漏检 + phase-cards/rules 不在 PROTOCOL_FILES（引用检查降级 WARNING）| done | TAG0010/0011 复盘（2026-08-15）+ 实测验证 | TAG0013 | 2026-08-15 | 2026-08-17 |
| RM-AG0017 | self-gate 触发面缺仓库根级文档：README.md/AGENTS.md 不在触发面（改协议语义绕过 self-gate 评审）| done | TAG0010/0011 复盘（2026-08-15）| TAG0013 | 2026-08-15 | 2026-08-17 |
| RM-AG0018 | 复盘/评审发现未接 tech-debt 登记触发点：tech-debt.md 零登记（DEBT0001 前），复盘发现缺口只写进复盘/roadmap 不走 DEBT 路径 | done | 独立观察 + DEBT0001 破冰（2026-08-15）| TAG0013 | 2026-08-15 | 2026-08-17 |

</details>

---

## RM-AG0025 详情

**协议文档职责边界与去重（WORKFLOW.md 审查，2026-08-17）**

- **问题**：agate 协议文档是**渐进叠加**出来的（每版本/任务往顺手文件追加），无"职责边界审计"——导致多文档交叉重复 + 内容归属混乱：
  1. **平台适配三份**：WORKFLOW.md L461-467 + dispatch-protocol.md L1207-1228 + platform-notes.md——同一内容三处维护，改一处漏两处（漂移源）
  2. **阶段门槛两份**：WORKFLOW.md 阶段总览表（L284-293，含详细 grep 命令）+ dispatch-protocol.md 可判定门槛规范（L903-978）——TAG0013 的 CHECK 10 教训就是这种双源没同步
  3. **派发 prompt 双源**：dispatch-protocol.md L429-628（模板 + 阶段特定提示）+ assets/templates/dispatch-prompt.md——N6 修复过的双源问题仍在
  4. **Pre-commit 检查清单两份**：WORKFLOW.md L303-334 + state-machine.md L215-218
  5. **重试上限两份**：state-machine.md L367-382 + dispatch-protocol.md L996-1033
  6. **职责定位混乱**：WORKFLOW 标题说"主流程，详细见其他文件"，实际塞了 gate 命令/Pre-commit 清单/平台适配等实现细节；dispatch-protocol 塞了派发编排机制（TAG0014 新增，该在别处）
- **根因**：无"每份文档唯一职责"的定义 + 无"新内容写哪个文件"的归属约定。这是 LIMITATIONS 局限 5（协议文档自身一致性）的具体表现——consistency 只查引用存在性，不查"同一规则多处维护"的重复。
- **建议修复方向**：
  1. **定义每份文档唯一职责**：WORKFLOW=主流程概要（阶段总览只留概要，gate 细节指向 dispatch-protocol）；dispatch-protocol=派发；state-machine=状态机；platform-notes=平台唯一权威；role-system=角色；git-integration=git
  2. **消除交叉重复**：平台适配收敛到 platform-notes（其他处指向）；阶段门槛收敛到 dispatch-protocol（WORKFLOW 只留概要）；派发 prompt 收敛到模板（dispatch-protocol 指向）；Pre-commit 清单收敛到一处（WORKFLOW 或 scripts/README）
  3. **内容归属约定**：加"新内容写哪个文件"规则（如派发编排机制→归 dispatch-protocol 还是独立文档，需定）
  4. **防复发**：check-protocol-consistency 或审计补充"同一关键词多处出现"检测（或协议结构化 AG0022 时一并解决）
- **与 RM-AG0022 关系**：AG0022 是"结构化"（大方向，规则抽成 yaml）；AG0025 是"职责边界+去重"（眼前卫生）。**AG0025 可先行**（轻，改文档结构），AG0022 后行（重）。但 AG0025 的"内容归属"定义可为 AG0022 的结构化打基础——两者相关。
- **⚠️ 系统排查方法（2026-08-17 用户强调：不只修已知 6 处，要举一反三）**：本条目发现的 6 处是"打地鼠"式抽查，不能只修它们。P1 阶段必须做**系统性全量排查**：
  1. **关键词交叉扫描**：对每条协议规则（平台适配/阶段门槛/重试上限/标记声明/裁剪规则/派发模板/Pre-commit 清单/降级规则/空返回恢复/证据要求等），grep 全仓确认**出现次数**，>1 处即潜在双源——逐条判定"哪个是权威，其余改指向"
  2. **职责声明表**：产出"每份文档的唯一职责"对照表（WORKFLOW/dispatch-protocol/state-machine/role-system/platform-notes/git-integration/loop-orchestration/SETUP/LIMITATIONS/adr 各一句话职责），作为去重依据
  3. **内容归属审计**：对每份文档的每个节，问"这内容该在这吗？权威在哪？"——迁移到正确位置或改指向
  4. **生成性扫描**：检查是否还有"渐进叠加"产生的同类问题（新内容塞错文件），如派发编排机制（TAG0014 新增）塞在 dispatch-protocol 是否合适
  5. **防复发机制**：除了"内容归属约定"，评估 check-protocol-consistency 能否加"同一关键词多处出现检测"（至少 WARNING 级）
- **验证口径**：每份文档职责单一可描述；交叉重复消除（同一规则只有一处权威）；consistency 0 ERROR
- **归属**：独立任务（协议文档重构），或并入 AG0022 前期。改动面大（动 WORKFLOW/dispatch-protocol/state-machine/platform-notes 等），触发 self-gate，需专门规划。
- **落地（TAG0016，2026-08-19，v0.54.0）**：P1 系统性全仓关键词交叉扫描核实已知 6 处中 4 处成立（平台适配 ×3/阶段门槛 ×2/派发 prompt 双源/重试上限表文档级，其中重试上限实际权威文件对与本条目原始猜测不同——是 `state-machine.md` vs `rules/state-transitions.md`，非 `dispatch-protocol.md`）、1 处不成立（Pre-commit 清单已是正确"权威源+指针"模式）、新发现 1 类未预判重复（8 张阶段卡片内联 `MAX=` 数值散落）。收敛为单一权威源+指针：`platform-notes.md`/`state-machine.md`/`assets/templates/dispatch-prompt.md`；新增 CHECK 12 防复发跨文件一致性检测（结构化白名单锚点扫描，非文本相似度，与既有"只做结构一致性"设计哲学一致）。7 份协议文档新增职责边界声明行。19 条 BDD 全 PASS，P7 一致性检查 BLOCKER=0。

---

## RM-AG0026 详情

**测试重跑审计与跨阶段证据引用（外部 agent 分析，2026-08-17）**

- **问题**：同一任务的**全量测试套件可能被重复跑 4-5 遍**：
  1. **P5 首跑**：进入 P5 全量跑一遍（gate_commands.P5）
  2. **P5 重试**：每次修复后要求全量重跑（T027 教训：修复可能引入回归，不能只检查修复项）
  3. **P6 refactor 口径**：强制独立 `regression.log`（`regression_pass: true` + 证据存在是 gate 硬校验，P6-acceptance.md L108；check-p6-provenance.py 审计 5 核 EXIT_CODE）
  4. **P8**：明确"重跑 P5 gate"（P8-release.md L82/118）
  - 实测：823 用例单次全量 106-115s，4-5 遍 = 500+ 秒花在"重复确认同一件事"
- **核实结论**：
  - P5 重试全量 ✅ 必须（T027 教训真实，保留）
  - **P6/P8 的证据复用是优化点**——但 agent 称"零新增机制"是**低估**：P6 regression.log 是 refactor 任务的 **gate 硬校验**（regression_pass + 证据存在 + provenance 审计），且"P6 验收时的代码状态 ≠ P5 验证时"（P6 可能回 P4 修过 bug）。**复用需协议支持"跨阶段证据引用 + 中间无改动校验"**（如 git log 对比证明 P5 通过后无代码改动），这是**机制改进**（provenance 审计要支持引用前序证据），不是纯优化
  - P8 重跑 P5 本质是"确认 bump 没破坏"，可**放宽为 bump 后跑一次**而非完整重跑（有优化空间）
- **建议修复方向**：
  1. **审计全量重跑点**：逐任务统计 P5/P6/P8 实际跑了几遍全量，量化浪费
  2. **跨阶段证据引用协议**（核心，机制改进）：定义"何时可引用前序阶段证据"——P5 全绿 + P6 验收前无代码改动（git log 校验）→ P6 regression 可引用 P5 产物；provenance 审计支持"引用前序证据 + 无改动声明"
  3. **P8 放宽**：bump 后跑一次 P5（非完整重跑），或"bump 无逻辑改动时引用 P5 最后通过"
- **xdist 试点**（同批，TPV0093 已记 xdist flaky）：P5 单发场景（无并行派发同时跑）试点 `-n auto`，观察真实 CI（4 核）加速比；**不与模式 3 并行派发叠加**（RM-AG0023 A-3 已记录"资源密集默认串行"）。并入本条目或 RM-AG0023 实施时一并评估
- **批次数据化备注**（不立条目）："1 轮可完成"是定性规则，等 RM-AG0016 的 dispatch_plan 字段攒够批次数据后再量化安全上限
- **验证口径**：逐任务统计全量重跑次数；协议支持 P6 引用 P5 证据（gate + provenance 校验通过）；P8 放宽后仍保证发布质量
- **归属**：独立任务（协议机制改进：P6/P8 卡片 + check-p6-provenance.py + 可能新脚本），与 RM-AG0023（运行时管控）相关但独立
- **落地（TAG0016，2026-08-19，v0.54.0）**：`check-p6-provenance.py` 新增审计 7（`audit7_p5_evidence_reuse`，三态判定 `reuse_allowed`/`reuse_blocked`/`no_reuse_claim_possible`，`git diff` 命令失败时 fail-closed 为 `reuse_blocked`，P4-review CRITICAL-1 修复）+ `--audit7-only` CLI 模式供 P8 消费判定结果；`.state.yaml` 新增可选字段 `p5_pass_commit`；`P5-verification.md`/`P6-acceptance.md`/`P8-release.md`/`verifier.md`/`dispatch-prompt.md` 五处协议文档同步落地"P5 全绿+验收/发布前无代码改动→可引用 P5 证据、不必重跑全量"规则；`dispatch-protocol.md` 新增「全量重跑点审计」小节；`.github/workflows/protocol-tests.yml` 新增 `continue-on-error: true` 的 xdist 观测步骤（不影响门禁）；新增 ADR-010 记录"受控例外——满足客观可判定条件时允许复用既有验证证据"这一新架构原则。P8 现状确认为"跑一次"（非原描述的额外重跑），本次精简为条件化（无改动→复用证据）。

---

## RM-AG0027 详情

**协议工具链修复批（TAG0016 复盘发现，DEBT0010/0011/0012，2026-08-19）**

- **来源**：TAG0016 复盘（v0.54.0）登记 3 个真实、未修复、影响后续任务的协议工具链系统缺陷；另有 DEBT0009（决策备忘非债）已单独关闭、DEBT0013（P8 时序文档注）已随 PR #166 顺手修复。

- **问题 1（DEBT0010，medium）**：`gate_commands` 键解析脚本系统性未排除 `_timeout_seconds` 后缀（4 处同类）：
  - `agate-read-gate-commands.py` L31、`agate-gate-missing-cmds.py` L20、`agate-gate-p5-count.py` L23、`agate-read-p5-commands.py` L29——均只排除 `_formatter` 后缀，未排除 `_timeout_seconds`
  - 影响：任何任务按 P2 卡片「`{key}_timeout_seconds` 字段规则」正常声明后，P2 报假"命令不存在" WARNING、P3 的 `check-tdd-red.py` 会把真红灯误判为假红灯（A 类，`bash -c "120"` → 127）、P5 报假"1 主 + 1 辅助"计数——操作者误判任务自身有问题而返工，或对真实 WARNING 掉以轻心
  - 修复：4 脚本判据统一补 `key.endswith("_timeout_seconds")`（与 `_formatter` 并列），可抽 `agate_common.py` 共享判据函数防第五处遗漏 + 回归用例覆盖三阶段场景

- **问题 2（DEBT0011，medium）**：SELF-GATE 审查文件纯日期命名触发跨任务覆盖：
  - `SELF-GATE.md` 派发模板规定 `agate-alignment-review-{date}.md`（只含日期）——TAG0015/TAG0016 同日各自触发审查时生成同名文件，TAG0016 覆盖 TAG0015 已提交历史（`git diff` 实证），git 无法区分"合法覆盖草稿"与"意外破坏历史"
  - 修复：命名模板补任务标识（`agate-alignment-review-{date}-{task_id}.md`）+ protocol-alignment-review 角色文件提示 subagent 覆盖写前先确认目标不是别的任务记录

- **问题 3（DEBT0012，medium）**：`check-protocol-consistency.py --strict`（WARNING-only 也 exit 2）与 `gate_commands.P5` 的 `&&` 串联组合，在存量 WARNING 未清零（当前 314 条，全为历史叙事文件死链）时**永远短路**链路末步（P5 实跑 count-tests 未执行到）；历史验证方法盲区（`command | tail` 掩盖真实 exit code）使该缺陷长期存在未被发现
  - 修复（二选一或都做）：(a) P2 卡片 gate_commands 声明示例不再推荐 `--strict` 放 `&&` 链路中间，改为三条独立命令分别判；(b) `check-protocol-consistency.py` 加 `--strict-errors-only` 模式（仅 ERROR 时非 0，WARNING 通过打印提示），保留 `--strict` 供人工主动选用

- **问题 4（DEBT0014，medium，2026-08-19 跨项目反馈汇入）**：Windows Store `python3` 占位符命中 hook 探测循环导致 Windows 用户 commit 阻断
  - `agate/scripts/pre-commit-gate.sh` 第 11-13 行（及 commit-msg-self-gate.sh / pre-push-gate.sh 同结构薄壳）探测循环 `for c in python3 python` 中 `command -v python3` 能命中 WindowsApps 目录下的 Store 占位符 `python3.exe`（它是个真实存在的 exe stub），但 exec 时 Store 占位符非交互模式直接 exit 49（无输出，不打开 Store）→ hook 走 fail-closed 分支阻断 commit
  - Windows 用户每次都踩的坑：AGENTS.md/CLAUDE.md 已知提示"python3 是 Store 占位符必须用 python"，但**协议层未做任何防护**——当前 workaround 是手动复制 `python.exe` 为 `python3.exe` 或改用 `python` 命令，脆弱且不可重现（任何新项目/新用户都会重新踩）
  - 修复：(a) 3 薄壳探测循环增强——探测后做可执行性小测试（exit 49 / stderr 含 "Microsoft Store" 字符串 → skip 该候选，转下一候选 python）或加 `AGATE_PYTHON` 环境变量优先（项目侧设 `AGATE_PYTHON=/path/to/python.exe` 时直接接受，跳过探测循环）；(b) `agate/platform-notes.md`「已知限制」表新增一条 + 「Windows 原生」章节加 Store 占位符说明 + `AGATE_PYTHON` 机制文档；(c) `agate/AGENTS.md`「升级 agate」段同步一句
  - P1 派发时需实测薄壳代码并定 Store 占位符识别阈值（exit 49 / stderr 内容 / Python313 路径是否在 WindowsApps 之前）

- **验证口径**：
  - DEBT0010：声明 `P3_timeout_seconds`/`P5_timeout_seconds` 时，check-tdd-red.py 仍正确判定真红灯 + check-gate.py P2/P5 不再误报（回归用例）
  - DEBT0011：SELF-GATE.md 模板含任务标识占位符 + 覆盖写前确认检查项
  - DEBT0012：gate_commands.P5 声明示例/脚本退出码模式更新 + 回归测试覆盖两种模式的 exit code 差异
  - DEBT0014：Windows 环境（Git for Windows 实测，含 Store 占位符）下 commit 钩子能正确解析到真实 python；`AGATE_PYTHON` 环境变量机制文档化；platform-notes 已知限制表新增一条
  - 全量 pytest + consistency 0 ERROR + shellcheck 0 issue

- **归属**：独立任务（协议工具链修复批，TAG0017）。三债均改脚本 + 协议文档 + 回归测试，不宜顺手改；DEBT0013 已在 PR #166 修复，DEBT0009 已关闭。改造域 = gate 脚本 + SELF-GATE.md + P2 卡片，触发 SELF-GATE。DEBT0014（2026-08-19 跨项目反馈汇入）扩展改造域 = 3 薄壳 sh + platform-notes.md + AGENTS.md，同样触发 SELF-GATE。
- **落地（TAG0017，2026-08-20，v0.55.0）**：`agate_common.py` 新增共享判据函数 `is_gate_meta_key`（`_formatter`/`_timeout_seconds` 统一排除），4 处解析脚本改用，DEBT0010 closed；`SELF-GATE.md` 命名模板补 `{task_id}`（DEBT0011 closed）；`check-protocol-consistency.py` 新增 `--strict-errors-only` 互斥模式 + 协议卡片示例同步改用（DEBT0012 closed）；3 薄壳新增 `AGATE_PYTHON` 显式覆盖 + 候选可执行性小测试（DEBT0014，Linux 模拟回归通过，Windows 真实环境待本次 PR 的 CI matrix 确认，**未提前宣称已实测**，DEBT0014 保持 open）。12 条 BDD 全 PASS，P4 review 迭代 1 轮（CRITICAL：协议卡片新示例未同步用新 flag）+ self-gate 迭代 1 轮（`agate/scripts/README.md` 遗漏）。

---

## RM-AG0028 详情

**env_constraints 声明性字段无执行/gate 绑定（TQC0001 跨项目反馈，2026-08-19）**

- **问题**：`env_constraints` 是 P0-brief/P2-design 的**声明性字段**——协议所有引用都是"确认/细化 + 注入 subagent 上下文"（`agate-extract-context.py` L107-109 只做注入；P0/P1/P2/P4 卡片当输入/约束读；dispatch-prompt 注入约束节），**没有任何 gate/脚本消费 `env_constraints.deploy` 之类的字段做执行性校验**。
- **实证**：TQC0001（Qt 简单计算器跨项目复盘）——P2 设计声明了 `env_constraints.deploy`（windeployqt 构建 dist），但全流程 P0-P8 **从未主动执行**，直到用户双击 exe 报缺 DLL 后才补做。根因不是 agent 粗心，是**协议层面"声明了但没有执行点"**——`env_constraints` 语义是"环境约束的声明"，不含"必须执行哪些部署命令"的 gate 绑定。
- **影响**：任何依赖 `env_constraints` 声明 deploy/pack/build 产物的任务，都可能出现"设计说要做但流程不强制"的静默缺口；UI 任务 dist 产物、打包产物、部署产物均无 gate 检查。
- **建议修复方向**（P1/P2 设计时选定）：
  1. 明确 env_constraints 字段语义边界：声明性（信息注入）vs 执行性（gate 强制）——P2 卡片/architect 角色说明"执行性约束必须落到 `gate_commands` 或 P4/P8 明确 checklist，不能只靠 env_constraints 声明"
  2. UI 任务 P4 后应构建 dist：P4 卡片「自查≠gate」节补"UI 任务 P4 后构建 dist（windeployqt 等）"；或 P8 gate 加 dist 产物存在性检查
  3. 可选：`check-gate.py` 或新脚本校验 `gate_commands` 中声明了 deploy/构建命令时，P4/P8 产出物存在
- **验证口径**：TQC0001 类 UI 任务在 P4 后自动产出 dist（不靠用户提醒）；env_constraints 语义边界文档化；UI 任务 P8 有 dist 产物检查
- **归属**：并入 TAG0017（协议工具链修复批，与 DEBT0010/11/12/14 同域——都是"协议有声明/设计但 gate 无强制"的系统性缺口）。P1 时与 DEBT0010（gate_commands 解析）一并做"env_constraints vs gate_commands 执行绑定"的整体设计。
- **落地（TAG0017，2026-08-20，v0.55.0）**：`phase-cards/P2-design.md`「gate_commands 声明」节 + `architect.md` 新增 `env_constraints` 声明性 vs `gate_commands` 执行性边界说明；`phase-cards/P4-implementation.md`「自查≠gate」节新增"UI/需构建任务 P4 后应构建并确认 dist 类产物存在"提醒。**验证口径第 3 条（TQC0001 类 UI 任务在 P4 后自动产出 dist，不靠用户提醒）本次未验证**——TAG0017 自身不涉及 UI/dist 场景，该指标需下一个实际 UI 任务走完 P4 后才能实证，DEBT0015 保持 open，不提前标记 closed。

---

## RM-AG0051 详情

**CHECK 7 版本漂移防线失效（CI consistency job 浅克隆无 tag；2026-08-25 一致性机制盘点）**

- **问题**：`protocol-tests.yml` 的 consistency job 用 `actions/checkout@v4` 默认配置（浅克隆，不取 tags），`check-protocol-consistency.py` CHECK 7（README version badge vs `git describe --tags --abbrev=0`）在 CI 恒走 WARNING 分支（"无法获取最新 git tag"）——**版本漂移在 CI 零机械防线**，v0.51.0 教训场景（本地 tag 未推送 → CI CHECK 7 FAIL）现在不会 FAIL，防线静默退化。pytest job 已带 `fetch-depth: 0 + fetch-tags: true`（protocol-tests.yml L85-88），consistency job 遗漏。本地侧 CHECK 7 有"未推送 tag 算最新 tag"假绿（本地绿 CI 红风险）。
- **修复方向**：
  1. consistency job checkout 对齐 pytest job：`fetch-depth: 0` + `fetch-tags: true`（一行配置，CI 恢复真实判定；1250 commits 小仓库无性能负担）
  2. 可选：`check_version_badge` 检测最新 tag 未推送——`git branch -r --contains <tag>` 为空且存在远端引用 → WARNING"tag vX 未推送，CI 判定会不一致"（无远端引用时跳过判定，避免本地未 fetch 误报），消除本地假绿体验
- **验证口径**：CI consistency job 中 CHECK 7 真实判定（badge 与 tag 不符 → exit 1 阻断，而非 WARNING 跳过）；本地存在未推送 tag 时 consistency 输出 WARNING（若做修复方向 2）
- **归属**：独立任务（CI workflow 配置 + `check-protocol-consistency.py` + 回归测试）；`check-protocol-consistency.py` 改动触发 SELF-GATE
- **落地（2026-08-25，hotfix 修复，非任务立项）**：修复方向 1 完成——`protocol-tests.yml` consistency job checkout 加 `fetch-depth: 0 + fetch-tags: true`（对齐 pytest job），CI 日志实证 `git fetch --no-tags --depth=1` → `fetch-depth: 0` 后 **CHECK 7 从 WARN 变 PASS**（PR #202，普通 merge 至 main 5fe2950）；修复方向 2（本地未推送 tag WARNING 预警）可选未做，保持 backlog 挂起（低价值，不新增脚本逻辑）。**未引入新 gate**——仅恢复既有 CHECK 7 的判定能力。

---

## RM-AG0052 详情

**CHANGELOG 破坏性变更 ↔ UPGRADING 章节对应性无自动检查（2026-08-25 一致性机制盘点）**

- **问题**：CHANGELOG 每版本标注"破坏性变更见 UPGRADING vN ②"或"本版本无破坏性变更"，但**没有任何 gate 校验 CHANGELOG 版本条目与 `agate/UPGRADING.md` 章节的对应性**——v0.62.0 发布时漏写 UPGRADING 章节实测溜过（AGENTS.md 发布清单第 3 步纯人工 + P8 卡兜底，无自动检查）。UPGRADING.md 虽在 consistency 的 PROTOCOL_FILES 里，但只受 CHECK 2/3（路径引用、行号）类检查，章节存在性无校验。
- **修复方向**：CHECK 12 锚点表模式扩展或新增 CHECK——CHANGELOG 每个版本条目（含"无破坏性变更"声明）↔ UPGRADING.md 对应 `### vN.N.N` 章节存在性对照；缺章节 → ERROR/WARNING。
- **验证口径**：模拟缺 UPGRADING 章节的版本 → consistency 报 ERROR/WARNING；全量 0 ERROR。
- **归属**：独立任务（`check-protocol-consistency.py` + 测试，触发 SELF-GATE）。
- **落地（2026-08-25，hotfix 修复，非任务立项）**：新增 **CHECK 13**（`check_upgrading_section`）——
  CHANGELOG 最新已发布版本（第一个 `## [X.Y.Z]` 条目，[Unreleased] 自然跳过）↔ `agate/UPGRADING.md`
  `### vX.Y.Z` 章节存在性对照，缺章节 → **ERROR 阻断**（v0.62.0/v0.63.0 连续两次漏写后立案，
  v0.63.0 章节已在 PR #208 补上）。范围限定"只查最新版本"：历史版本在 §3 本就不全（0.53-0.56 无章节），
  全量核对会在存量数据误报；发布时点拦截只需盯最新版本。6 用例 TDD（含 [Unreleased] 跳过 / 缺文件静默 /
  无已发布版本 WARNING 边界）；真实仓库 CHECK 13 PASS + 全量 0 ERROR + pytest 1293 collected 全绿。
