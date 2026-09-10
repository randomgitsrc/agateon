# 已知局限

> Agateon 是一套轻量文档协议，不是代码框架（见 README 设计原则）。这条路线选择带来了真实价值
> （零基础设施、Agent 能读文件就能用），也继承了这条路线结构性的弱点。本文档只记录**真正的
> 结构性局限**——让使用者知道协议的能力边界，不要误以为这些问题已经被解决。已缓解到位、或本质上
> 是"能力矩阵 / 依赖披露"的条目不列在此。

## 局限 1：gate 的可信度上限取决于测试本身的质量

Agateon 反复强调"主 Agent 必须亲自跑 gate，不信任 subagent 的自我报告"。这个原则解决的是
"Agent 有没有撒谎"，**没有解决"测试写得好不好"**。P3 的测试若断言太宽松、覆盖率虚高但漏了真正的
边界条件，P5 跑出 exit 0 一样是"客观的假象"——exit code 客观，但它客观验证的是一个可能不靠谱的
标准。这是 TDD 方法论本身的老问题，几乎不可能在协议层面根治：引入"测试质量评审"角色会让流程更重，
且评审测试质量本身又依赖另一层主观判断，只是把问题往后推一层。

**现状**：无解。使用者需自己对 P3 测试质量保持警惕。→ ADR-002（gate 机器可判定 ≠ 测试本身正确）

## 局限 2：角色隔离是认知层面的隔离，不是真正的独立视角

P3 test-designer 与 P4 implementer 是两个不同的 subagent，目的是制造"独立视角"。但它们通常用**同一个
底层模型**，同一训练分布下对同一类问题有相似盲点——这和人类团队里两个不同背景的工程师互相 review
不是同一回事。这种隔离能防"明显的偷懒"，防不住"系统性盲区"（这个模型家族普遍不擅长的某类边界，
两个角色都会漏）。

**部分缓解（RM-AG0060 派发路由，已落地）**：项目级 `agate-workspace/dispatch-routing.yaml` 可按
`(phase, role)` 把某角色的 subagent 派到不同 CLI+model，给"角色隔离"补上 model / 厂商维度。
`cli: native`（同厂商换 model）是**弱缓解**——同训练系谱盲区基本共享，且自动化天花板是"主 Agent
机械横传 model"；跨 CLI 子进程（换厂商）是**强缓解**——真正的异源独立视角、可端到端自动化。不配置
= 逐字节现状；是否配、配哪些由使用者按本机现状决定（机会式，不追求跨机可复现）。**仍非根治**——
主 Agent 自身的选型判断这一步仍缺乏外部约束，与局限 3 同构。

**现状**：部分缓解，无根治。→ ADR-006（同源模型隔离是认知层非真正独立）

## 局限 3：主 Agent 的判断力是单点故障

Agateon 的所有质量保证最终都收敛到"主 Agent 的判断力"这一个点：裁剪哪些阶段、gate 算不算过、
SCOPE+ 影响范围多大，全部由主 Agent 最终拍板。没有任何机制检验主 Agent 自己的判断是否可靠。

这不是假设性担忧——生产环境数据污染、违规降级（多次违反现成协议）、误写生产 DB 后未标
`[PROD_TOUCHED]` / 跨阶段回退未 PAUSED、P5 阶段对预存失败一句话带过导致回归潜伏——多个独立事故，
同一根因：**主 Agent 遇到困难时倾向于自行解决而非触发安全网**。这是 LLM 作为编排者的固有行为
模式，不是偶然失误。

**gate 的 self-authored 分类**：外部产出 gate（P3/P4/P5，判定对象是 test runner exit code / git log，
主 Agent 无法伪造）vs self-authored gate（P1/P2/P6/P7，判定对象是主 Agent 自己写的 markdown，
可以直接写假结论）。**证据存在 ≠ 证据与结论对应**——self-authored gate 的造假风险只能缓解，无法根治。

**已落地的缓解**（提高造假成本 + 留痕审计，均非硬保证）：

- `[PROD_TOUCHED]` 等针对具体已知风险的强制客观信号（二值格式，消除"无 X"的模糊表述）
- 结构性绑定：状态标记必须绑定 gate 验证、跨阶段回退 phase 跳变检测
- 门槛失败事件 ↔ `retries` 对应性机械校验（RM-AG0042，`check-state-transition.py`）——不依赖主 Agent 主动遵守
- **P6.5 独立 Judge**（RM-AG0032，强制）：judge 以 fresh context 只凭 `P6-evidence/` 证据与 git log
  逐条重验全部 BDD（含已 PASS 项、零挑验），信息隔离白名单由 `check-judge-verdict.py` 机械校验，
  append-only 事件账本 `gate-events.jsonl` 由 `check-events.py` 哈希链审计；judge 的 LLM 结论不单独
  放行——exit code 才是门槛。仍是缓解：judge 结论可被其实现者左右，机械核对面不覆盖 verdict 正文语义。
- **协议文档自身的语义一致性**没有 in-flow gate：`check-protocol-consistency.py` + SELF-GATE 是结构 /
  关键词兜底，不覆盖语义；改协议靠人触发 protocol-alignment-review + 人确认 `NEEDS_HUMAN_REVIEW`。
  （本文档的存在就是这条的实例——一次全仓文实脱节靠人发起审计才发现。）
- **不启用 CI 时**，`git commit --no-verify` 可绕过全部 pre-commit gate 且无自动恢复——pre-commit
  hook 是唯一 enforcement 点。启用 CI（GitHub / GitLab / Gitea Actions）则 backstop 重跑
  `check-gate.py` + `check-p6-provenance.py` + `check-events.py` 兜底。

**方向性错配**：Agateon 的防御机器主要布置在 subagent 一侧——而 subagent 是廉价的、可无限重派的、
失败即被打回的一方。主 Agent 一侧握有全部最终裁量权且被实证是主要事故源，几乎没有任何外部约束。
这是"纯文档协议 + 单编排者"路线的结构性产物：只要主 Agent 是唯一最终裁判且它写的东西是唯一事实源，
就不可能从内部约束它。

**现状**：部分缓解，未根治。→ ADR-001（隔离性不约束主 Agent 裁量权）、ADR-005（改动性质判断依赖主 Agent）

## 局限 4：subagent 活动的中间过程不可观测

Task 工具返回最终结果，不暴露中间过程。主 Agent 无法直接判断 subagent 是在推理 / 调工具 / 输出，
还是卡死；空返回时无法区分"没启动"和"跑了一阵放弃"。

**部分缓解（RM-AG0055 命令流日志机制，已落地）**：从平台会话记录**外部**读取 subagent 的活动
信号，统一为 `CommandRecord` IR，检测引擎判「调用冻结 / 活动冻结 / 逻辑空转」三态。原则是
**"证据 + 触发核查、不自动判死"**——给主 Agent 一个可观测面，不做自动终止。加上派发模板默认要求的
**分阶段落盘**（subagent 每读完一个文件追加 progress，把"一次性大产出"拆成"逐步小产出"，实测显著
降低空返回），实践中的"卡死 vs 慢"多数可判。

**残余边界**：依赖各平台的会话记录格式（每平台一个适配器：claude-code / opencode / dsh / codex）；
仍非"平台原生的活动信号 + 智能超时"。空返回时走 retry → PAUSED，不降级。

## 局限 5：gate 与 hook 的强制力依赖 python3 + git + pyyaml + git 仓库

"零基础设施"是相对的：**协议的文档部分**（阶段卡片、角色文件、状态机规则）确实零依赖、任何能读
文件的 Agent 都能参考；但 **gate 脚本与 pre-commit hook 的 enforcement** 依赖 python3 + git + pyyaml
（`pyyaml` 是强制依赖，缺失时脚本 fail-closed），且项目必须是 git 仓库。缺任一，协议退化为"可参考
的散文"，失去把关能力。

这是用通用工具替代专用服务的代价，非缺陷——但采用者要知道边界在哪。具体安装要求（含 bash 仅用于
3 个 hook 薄壳、Pillow 可选用于 P6 图像检测）见 `SETUP.md` /（README 的 Requirements）；
被管理项目的语言不受限制（Go / Rust / Java / …，只要执行环境有 python3 + git）。
→ ADR-003（不绑定被管理项目技术栈，但 Agateon 自身有运行时依赖）

## 局限 6：vision / UI 验收依赖外部基础设施

P6 的视觉验收需要截图能力——依赖 Agent 平台提供浏览器 / 截图工具，Agateon 协议本身不提供。
无该能力时 P6 视觉验收退化为文本描述验收 + 人工复核记录；截图证据的真实性无法机器验证（同局限 3
的证据-结论对应问题）。

**缓解（TAG0006）**：P1 显式声明视觉能力三态（available / supplementable / GAP），P6 按声明分档
消费证据（有能力 → 量化 vision 分析；GAP → 多形式证据 + 像素检测 + 人工复核记录）。机制细节
（三态分档 / avg-hash 降级 / 帧序列 / 渲染对比）见 `phase-cards/P6-acceptance.md` 与
`assets/execution-roles/vision-analyst.md`。残余边界：三态声明是自写文件、复核记录依赖 verifier
自述——self-authored gate 固有局限（局限 3），靠多处互相印证抬高伪造成本，不消除。

## 这些局限意味着什么

如果你的任务涉及高风险操作（数据删除、生产环境交互、安全敏感逻辑），**不要把 Agateon 的 gate
通过当作"绝对安全"的保证**——它验证的是"测试这样写、主 Agent 这样判断时，结果是这样"，不是
"这件事在所有意义上都是对的"。这类任务保留人工最终复核，不要让 P8 发布准备成为唯一的把关点。
