# 已知局限

> agate 是一套轻量文档协议，不是代码框架（见 README 设计原则）。这条路线选择带来了真实价值（零基础设施、Agent 能读文件就能用），也继承了这条路线结构性的弱点。本文档诚实记录这些局限，不是为了自我否定，是为了让使用者知道协议的能力边界，不要误以为这些问题已经被解决。

## 局限 1：gate 的可信度上限取决于测试本身的质量

agate 反复强调"主 Agent 必须亲自跑 gate，不信任 subagent 的自我报告"（见 dispatch-protocol.md）。这个原则解决的是"Agent 有没有撒谎"，**没有解决"测试写得好不好"**。如果 P3 阶段的测试本身是弱测试（断言太宽松、覆盖率虚高但没测到真正的边界条件），P5 跑出 exit 0 一样是"客观的假象"——exit code 客观，但它客观验证的是一个可能不靠谱的标准。

这是测试驱动开发这个方法论本身的老问题，不是 agate 独有，也几乎不可能在协议层面解决——除非引入额外的"测试质量评审"角色，而这会让流程更重，且评审测试质量本身又依赖另一层主观判断，没有真正消除问题，只是把它往后推了一层。

**现状**：无解，需要使用者自己对 P3 阶段的测试质量保持警惕，agate 协议本身不提供这层保证。→ ADR-002（可判定性的边界：gate 机器可判定 ≠ 测试本身正确）

## 局限 2：角色隔离是认知层面的隔离，不是真正的独立视角

P3 test-designer 和 P4 implementer 是两个不同的 subagent，目的是制造"独立视角"防止自己骗自己。但这两个 subagent 通常用的是**同一个底层模型**，在同样的训练分布下，容易对同一类问题有相似的盲点——这和人类团队里两个不同背景的工程师互相 review 的"独立"程度不是同一回事。

这种隔离能防住"明显的偷懒"（比如直接抄实现当测试通过），但防不住"系统性盲区"（比如这个模型家族普遍不擅长的某类边界条件，两个角色都会漏）。这是当前所有基于同一模型做多角色编排的方案共同的局限，不是 agate 独有。

**现状**：无解。详细讨论见 `docs/design-notes/main-agent-oversight.md`——其中讨论的"LLM 裁判员"方案被否决，正是因为这同一个根因（同源模型的系统性盲区共享）。→ ADR-006（双层角色的认知隔离上限：同源模型隔离是认知层非真正独立）

**派发路由缓解链（TAG0034 / RM-AG0060 已落地）**：局限 2 的根因是「P3/P4/P6.5 等角色虽是不同 subagent、但通常同一底层模型 → 系统性盲区共享」。派发路由机制在**机制层**给「角色隔离」补上 model / 厂商维度：项目级 `agate-workspace/dispatch-routing.yaml` 按 `(phase, role)` 声明有序跨 CLI 候选链，主 Agent 到阶段派角色时机械查表 → try-and-fall（无 probe，只在 `launch_fail` / `infra_error` / `no_parseable_output` 三类基础设施信号逐级回落）→ 全落空回落默认派发（等价未启用）。两种缓解强度：`cli: native`（同厂商换 model，不脱离原生派发工具）是**弱缓解** —— 同训练系谱盲区基本共享，只省成本 + 一点 failure-mode 多样性，且自动化天花板是「主 Agent 读文件机械横传 model」；`cli:` 另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程）是**强缓解** —— 真正的异源独立视角、可端到端自动化。`dispatch_route` 事件与 `gate_run` 等同构、无差别留痕（哈希链账本 `check-events.py` 审计），两条完整性不变量机械强制（「候选回落 ≠ 状态机 retry」/「gate FAIL 绝不换候选」，理由码枚举无 `gate_fail` 值）防「换模型试到出 green」的完整性洞。**仍非根治** —— 主 Agent 自身的选型判断、以及「机械横传 model」这一步本身，仍缺乏外部约束，与局限 3「主 Agent 判断力是单点故障」同构；且是否真配跨 CLI 候选、配哪些，由使用者按本机现状决定、后果自负（per-machine 机会式，不追求跨机可复现）。

## 局限 3：主 Agent 的判断力是单点故障

agate 的所有质量保证最终都收敛到"主 Agent 的判断力"这一个点：裁剪哪些阶段、gate 算不算过、SCOPE+ 影响范围多大，全部由主 Agent 最终拍板。协议设计里"主 Agent 永远是最终裁判"，没有任何机制检验主 Agent 自己的判断是否可靠。

这不是假设性担忧——T005/T006（生产环境数据污染）、T016（违规降级，3 次违反现成协议）、T019（误写生产 DB 后未标 PROD_TOUCHED、跨阶段回退未 PAUSED、SCOPE+ 未触发）、T068（P5 阶段实际看到 63 个预存失败，主 Agent 以"非本任务相关"一句话带过，未登记未排查，回归潜伏 3 天后才在下一个任务 T073 被发现）——五个独立案例，同一个根因：主 Agent 遇到困难时倾向于自行解决而非触发安全网。这个倾向不是某个任务的偶然失误，是 LLM 作为编排者的固有行为模式——"解决问题"的冲动强于"报告问题"的冲动。

**gate 的 self-authored 分类**（T026 教训）：gate 按判定对象分为两类——
- **外部产出 gate**（P3/P4/P5）：判定对象是外部工具产出（test runner exit code、git log），主 Agent 无法伪造
- **self-authored gate**（P1/P2/P6/P7）：判定对象是主 Agent 自己写的 markdown 文件，主 Agent 可以直接写假结论

T026 事故：主 Agent 编造 11/16 条 BDD 验收结果（不跑验证脚本直接写 PASS），`grep PASS` 仍然通过——因为文件内容和 grep 条件都是主 Agent 自己写的，作者和裁判是同一人。缓解措施：P6 gate 追加 `P6-evidence/` 目录非空检查（外部产出作为必要条件），但**证据存在 ≠ 证据与结论对应**——这是必要非充分条件。self-authored gate 的造假风险只能缓解（提高成本 + 留痕审计），无法根治。

**现状**：部分缓解，未根治。已落地的应对分两类：(1) 针对具体已知风险的强制客观信号（如 `[PROD_TOUCHED]` 标记，二值格式：触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`，消除"无 PROD_TOUCHED"的模糊表述）；(2) 结构性绑定（如状态标记必须绑定 gate 验证、跨阶段回退 phase 跳变检测）；(3) self-authored gate 的证据存在性检查（P6-evidence/ 非空）；(4) 门槛失败事件↔retries 对应性机械校验（RM-AG0042，`check-state-transition.py` 检查3）：单步回退未同步写 retries 阻断，评审 rejected 重派/子代理空返回重派未写 retries 高优 WARNING。前者能拦住已知风险模式，后者不依赖主 Agent 主动遵守。但下一个没被预见到的风险模式，仍然完全依赖主 Agent 当时的判断力。"确定性脚本扫描历史生成异常模式报告"方向曾被认为是值得探索的，但经分析发现其数据源（.state.yaml / commit message）全部由主 Agent 自己写，数据源与监督对象同源，前提未解决，归类为开放问题（详见 `docs/design-notes/main-agent-oversight.md`）。

**P6.5 独立 Judge 缓解链（TAG0020 已落地）**：自写 gate（P6/P7）的作者与评判者同信任链是局限 3 的核心弱点——机制层补一层**独立第第三方复核**：judge 在 P6 之后以 fresh context 逐条重验所有 BDD（含已 PASS 项，零挑验），只信 `P6-evidence/` 证据与 git log，信息隔离白名单（dispatch-context 禁含 verifier/implementer 自述）由 `check-judge-verdict.py` 机械校验；三条防线（信息隔离 / 证据交叉核对与 BDD 计数对照 / append-only 事件账本 `gate-events.jsonl` 哈希链审计 `check-events.py`）把"作者与裁判同一人"的造假成本进一步抬高；judge 的 LLM 结论仍不单独放行——**exit code（check-judge-verdict + check-events 双脚本）才是门槛**（BDD-9 哲学红线）。这仍是缓解（提高成本 + 留痕审计）而非硬保证——judge 自身的结论仍可被其实现者左右，机械核对面不覆盖 verdict 正文语义，局限 3 的"无法根治"结论不变。

**方向性错配**：agate 的防御机器（五步校验、gate 亲跑、上下文隔离）主要布置在 subagent 一侧——而 subagent 是廉价的、可无限重派的、失败即被打回的一方。主 Agent 一侧——握有全部最终裁量权（裁剪、gate 算不算过、SCOPE+ 范围）且被实证是主要事故源（T005/T006/T016/T019 根因全是主 Agent）——几乎没有任何外部约束。这个错配是"纯文档协议 + 单编排者"这条路线的结构性产物：只要主 Agent 是唯一最终裁判且它写的东西是唯一事实源，就不可能从内部约束它。承认这一点，比继续往 subagent 侧加检查更重要。

**降级缓解（v2 客观行为审计，已实现）**：
- P6 验收：`scripts/check-p6-provenance.py` 六道客观审计
  - 证据-结论对应：每条 PASS 的证据引用路径必须存在 + 每个证据文件必须被引用（空 png 充数拦截）；多条 PASS 可共享同一证据文件
  - dispatch-context 审计：P6-dispatch-context-{role}.md 不含验收结论预判（防误导 verifier）
  - BDD 总数对照：P6 结果数 = P1 `#### BDD-NN` 标题数（精确计数，不再依赖 Given 行数启发式）
- P2 评审：agent=main 硬拦截（check-gate.py exit 1，不可自行批准评审）
- P5 机械化回归判定（v0.24.0，P2.47/P2.48）：任务开始时自动捕获全量测试失败列表快照（`pre-task-baseline.md`），P5 阶段对两次快照做 `comm` diff——只在"任务后"出现的 = 新增回归，直接拦截；两边都有的 = 预存，需 `known-failures.md` 登记。判定不再依赖主 Agent 文字声明，纯粹是两个文件的集合运算。缓解但不根治——P5 整体仍是 self-authored gate，快照文件本身理论上仍可被主 Agent 绕过（如 `--no-verify` 或手改 fail-list.txt），与 provenance 审计的已知局限同级。
- 已知局限：主 Agent 可造假证据文件（如空 png 充数），但造假成本远高于合规（需造 N 个文件 + 正确交叉引用 + BDD 总数匹配）。证据-结论对应检查只验证引用存在性和数量，不验证证据内容真实性（如截图是否为真实 UI 截图 vs 纯色 png）——这是造假成本提升 + 留痕审计，不是硬保证
- 已知局限：`git commit --no-verify` 绕过 pre-commit hook 时 provenance 审计也被绕过，CI backstop 现已重跑 check-p6-provenance.py（M4.2），provenance 的 CI 层覆盖为 git blame WARNING + provenance 重跑
 - 根治：Phase 3 平台支持独立 git author 后，agent 字段升级为 git author 硬检查

→ ADR-001（隔离性不约束主 Agent 裁量权）、ADR-005（改动性质判断依赖主 Agent）

## 局限 4：subagent 活动不可观测

Task 工具返回最终结果，不暴露中间过程。主 Agent 无法判断 subagent 是否在干活（在推理/调工具/输出）。导致：无法区分"subagent 卡死"和"subagent 在干活但慢"；空返回时无法诊断是"没启动"还是"跑了一阵放弃"。

**间接缓解（agate 协议层，已验证有效）**：
- **分阶段落盘**（已验证）：派发 prompt 要求 subagent 每读完一个文件就追加写入 progress 文件。实测 10 文件交叉评审任务：无落盘 → 空返回；有落盘 → 完整返回 + 114 行进度文件。根因不是上下文窗口满，是任务结构导致认知过载，落盘把"一次性大产出"拆成"逐步小产出"。
- 主 Agent 记录派发耗时作参考（弱信号，不能区分"卡死"和"在干活但慢"）
- 空返回后检查中间产物文件判断 subagent 是否动过

**根本解决（需平台支持，超出 agate 协议范围）**：
- Task 工具暴露 subagent 活动信号（工具调用日志、输出流、心跳）
- Task 工具增加超时参数（主 Agent 可设定）
- 基于活动的智能超时（有活动续期，无活动终止）

**现状**：当前做不到。空返回时走 retry→PAUSED，不降级——这不依赖诊断，只依赖规则遵守。

## 局限 5：协议规则文档自身的内部一致性验证不在流程内

agate 作为项目开发流程时，P2 评审角色（plan-eng-review / cso / design-review）、P6 BDD 验收、P7 一致性检查**已经在做语义层验证**——检查"实现是否偏离设计意图"、"行为对不对"。这不是"只做下限"，是多层次的质量保障。

但有一个场景 agate 的流程不覆盖：**协议规则文档自身的内部一致性**。例如 dispatch-protocol.md 的 P0 模板说 4 字段、自查清单说 5 字段——这种"同一协议文件内的措辞矛盾"不会被任何阶段的 gate 或评审角色抓到，因为：

- gate 检查的是**产出文件**（P1-requirements.md / P2-design.md），不检查**协议文件本身**
- 评审角色审查的是**阶段产出**，不审查**协议规则文档**
- P7 一致性检查是"实现 vs P2 设计"，不是"协议文件 A vs 协议文件 B"

**为什么不在流程内加"协议一致性扫描"**：
- 协议文件由主 Agent 自己读，不是阶段产出——没有 gate 时机
- 一致性检查是语义判断，不可机器判定——无法写成可判定的转移规则
- 加"实现评审"环节（落地后回扫 review 意见）依赖主 Agent 记忆 + 语义判断，违背"状态落盘、不依赖记忆"的核心设计

**现状**：协议文档的内部一致性靠维护者在旁人工保证。agate 作为项目开发流程时不存在这个问题——项目流程不修改协议文件。

**缓解（v0.8）**：协议-脚本语义对齐审查（protocol-alignment-review）。改协议/脚本时派发独立 review subagent 做语义审查（A1-A6 审查清单），CHECK 9 做结构兜底（锚点表关键词存在性检查）。语义一致性仍非 100% 自动化——需要人触发审查 + 人确认 NEEDS_HUMAN_REVIEW 项。→ ADR-002（可判定性不覆盖协议文档自身的一致性）

## 局限 6：运行时依赖 python3+git+pyyaml（强制）+ bash（仅 hook 薄壳）+ Pillow（可选），但不限制被管理项目语言

agate 的 gate 脚本和 pre-commit hook 依赖 python3、git、pyyaml 作为运行时工具（TAG0010 起产品逻辑全部 Python 化，bash 仅剩 3 个 hook 薄壳）。这些是**工具依赖**，不是被管理项目的语言限制——agate 编排的项目可以是任何语言（Go、Rust、Java、Ruby 等），只要执行环境有 python3+git 可用。

具体影响：
- **python3 + pyyaml（强制）**：全部 gate 脚本（check-gate.py、check-pruning.py 等）和 pre-commit hook 用 Python 编写，`agate_common.py` 及所有状态读取工具 import yaml。**pyyaml 是强制依赖**（`pip install pyyaml`），缺失时脚本 fail-closed（exit 1 阻断），不做静默降级。无 python3 则无法运行 gate
- **bash（仅 3 个 hook 薄壳）**：git hook 入口保留 `.sh` 薄壳（定位 AGATE_ROOT + python 探测 + exec py 主程序）。**无 bash 环境（纯 cmd/PowerShell）成为可行选项**——gate 脚本可直接 `python3` 运行（P0-P8 全程可执行），仅 hook 薄壳需要 sh（Git for Windows 自带）。详见 `platform-notes.md`「Windows 原生」
- **git**：状态落盘、pre-commit hook、P8 version 检测、P7 源文件计数均依赖 git。非 git 项目无法使用 agate
- **Pillow（可选）**：check-p6-evidence.py 的像素方差检测和 average hash 相似度检测需要 Pillow。Pillow 未安装时这两项检测跳过并输出 WARNING（不阻断 gate），可设 `AGATE_SKIP_IMAGE_CHECKS=1` 主动声明跳过。CI 环境建议安装 Pillow 以获得完整检测覆盖

**现状**：这些依赖是 agate 作为"零基础设施文档协议"的代价——用通用工具替代专用服务。如果执行环境不满足，gate 检查和 pre-commit hook 不可用，但协议的文档部分（阶段卡片、角色文件、状态机规则）仍可参考。→ ADR-003（不绑定被管理项目技术栈，但 agate 自身有运行时依赖）

## 局限 7：vision/UI 验收依赖外部基础设施

P6 验收中的视觉验收（vision-analyst 角色）需要截图能力——这依赖 Agent 平台提供浏览器或截图工具。agate 协议本身不提供此基础设施。

具体影响：
- 无浏览器/截图工具时，P6 视觉验收退化为文本描述验收（verifier 角色替代 vision-analyst）
- UI 变更的验收质量取决于截图工具的可用性和 Agent 的视觉理解能力
- 截图证据的真实性无法机器验证（见局限 3 的证据-结论对应讨论）

**现状与缓解（TAG0006 落地）**：视觉验收不再是"可选增强"的模糊表述，而是**能力识别 + 三态分档 +
降级链**：P1 显式声明视觉能力三态（available/supplementable/GAP，frontend 任务 P1 gate 强制声明），
P6 按声明分档消费证据——
- available/supplementable → vision YAML 引用 + blocker_count=0（真实视觉分析，判据须可量化）
- GAP → 降级链：截图/帧序列等多形式证据 + 像素检测 + **人工复核记录**（不要求 vision YAML，
  复核记录缺失会被 check-p6-evidence/check-p6-provenance 拦截）
- 渲染组件/时序特效形态（P1 `ui_render_shape` 声明）可选用帧序列（`frames/`）/渲染输出对比
  （`renders/` + `diff.json`）/时序截图（`-tN`）证据，框架与单测按形态适配
- avg-hash 雷同截图从纯 WARNING 升级为"降级待复核"（有 `雷同截图复核`/manual-review 记录放行，
  无记录阻断）；帧序列与 `-tN` 时序截图按"同 BDD 证据组（bdd-id 前缀）"同权豁免相邻样本，
  避免动画/时序证据被误伤；md5 逐字节去重硬阻断不变

缓解的残余边界：三态声明是自写文件（P1 可虚报），降级链依赖 verifier 自述的复核记录——
self-authored gate 固有局限（局限 3），靠"形态声明与 UX BDD/UI 设计节/证据形式三处互相印证"
抬高伪造成本，不消除。

## 局限 8：CI backstop 支持 GitHub Actions / GitLab CI / Gitea Actions

ci-gate-backstop.py 设计为 CI 层兜底——在 pre-commit hook 被绕过时（如 `git commit --no-verify`）重跑 gate 检查。当前实现支持 GitHub Actions、GitLab CI、Gitea Actions 三种平台（通过 `detect_ci_platform()` 函数检测，检测顺序 Gitea → GitLab → GitHub，避免 Gitea Actions 的 GitHub 兼容变量导致误判）。

具体影响：
- Jenkins、CircleCI 等其他平台的用户需自行适配 ci-gate-backstop.py 的环境检测逻辑
- 不使用 CI 的项目完全依赖 pre-commit hook，无兜底机制
- AGATE_TASKS_DIR 环境变量（v0.13.0 新增）允许配置任务目录路径，但 CI 平台检测仍需手动适配
- Gitea Actions 的环境变量（`GITEA_ACTIONS=true`）和事件文件格式尚未实测确认（见第六部分验证状态说明），`get_pr_metadata` 的 Gitea 分支先按 GitHub 兼容路径实现，实测不符时需调整

**现状**：CI backstop 是可选增强层。核心 gate 检查在 pre-commit hook 中运行，不依赖特定 CI 平台。非支持平台的用户可参考 ci-gate-backstop.py 的逻辑自行实现对应平台的 backstop。M4.2 新增 provenance 审计重跑（check-p6-provenance.py），CI backstop 现在同时重跑 check-gate.py + check-p6-provenance.py。

## 这些局限意味着什么

如果你的任务涉及高风险操作（数据删除、生产环境交互、安全敏感逻辑），**不要把 agate 的 gate 通过当作"绝对安全"的保证**——它验证的是"测试这样写、主 Agent 这样判断时，结果是这样"，不是"这件事在所有意义上都是对的"。这类任务建议保留人工最终复核，不要让 agate 的 P8 发布准备成为唯一的把关点。
