---
task_id: TAG0036
phase: 复盘
type: retrospective
status: done
created: 2026-09-19
trace_id: TAG0036-retro-20260919
mechanism_issues:
  - "judge dispatch-context 的『两节』扫描面无终止符，objective_info 内斜杠连写的阶段序列被误报为任务路径（DEBT0044）"
  - "check-p6-provenance 对『不阻塞』警告返回 exit 2，agate-next 仅认 exit 0 推进；暂停时落盘未填充的 resolution 模板（DEBT0045）"
  - "新增 agate/scripts/check-*.py 的登记面无权威清单；P1 同类扫描凭推理判『不处理』，SG.6 / CHECK 9 直到 P2 评审实测才暴露（DEBT0046）"
  - "gate_commands 写法陷阱无文档：读取器剥离首尾引号、未加引号的通配被 shell 先展开致删除类变更漏检（DEBT0047）"
  - "P3 阶段无机械检查测试文件平台假设，/tmp 字面量到 P4 全量 pytest 才暴露（DEBT0048）"
execution_issues:
  - "主 Agent 在 agate-next 暂停后未核对结果就 `git add` 整个任务目录，把 P7 产出连同未填充的 resolution 模板提交进 phase 仍为 P6 的提交"
  - "主 Agent 写的 P6-gate-diagnosis.md 缺 agent 字段（协议要求该文件带 agent），直接触发上一条的暂停"
feedback_ready: false
---

# TAG0036 复盘 — MVWU 阶段 1 试点（RM-AG0063 阶段 1）

## 一、事实基线

| 项 | 值 |
|----|-----|
| 任务编号 | TAG0036（RM-AG0063 阶段 1；阶段 2 另立 RM-AG0067） |
| 阶段轨迹 | P0 → P1 → P2 → P3 → P4 → P5 → P6 → P6.5 → P7 → P8 → READY（全阶段不裁剪） |
| 重试记录 | `retries`：P1 一次（评审 needs-revision）、P2 两次（B1/B2，再 B3）；P3/P5/P6/P6.5/P7/P8 无 gate 重试；P4 无 gate 重试但有一次评审后修复与一次测试注释小修（均已记录于 P4 产出） |
| 交付形态 | 6 批 static-batch，**单个合并 commit**（`4ee499f`）；协议层提交粒度决策仍待用户裁决 |
| 版本 | v0.71.1 → **v0.72.0**（`bump_type: minor`）；PR #346，普通 merge 非 squash |
| 需求基线 | 71 条 BDD（P1 首稿 58 条，评审后拆分/补充为 71 条） |
| 验证 | 全量 pytest **1666 → 1842 passed / 2 skipped**（新增 111 + 65 个用例）；P5 10/10 命令 exit 0；P6 71/71；P6.5 judge passed 71/71（一轮）；P7 BLOCKER 0 / DEVIATION 4（均已收尾） |
| 零内核改动 | `check-gate.py` / `phases.yaml` / `rules/schema` / hook 三件套 / `agate_common.py` / 审计链 diff 均为空（P6 阶段重新实测） |
| 提交 | 分支上 15 个提交（`wf(TAG0036-P0..P8)`）+ 基线；任务目录 63 个文件 |
| 中断事件 | P4 收口的两个评审 subagent 因 API 额度限流（HTTP 429）中断、无产出，限流窗口后重派 |

## 二、做得好的 + 可复用模式

- **评审必须"实测抽样"，而非只读文档**（去向：**回馈 agate**，关联 DEBT0046/0047）。本任务三处真缺陷都是评审者实跑才发现的：P2 评审在副本放空脚本复现 `test_sg_6` 变红（B1）、实跑读取器复现末尾引号被吞（B2）、临时仓库实测通配对删除类变更漏检（B3——恰是评审者自己上一轮建议引入的，它如实承认）。若只读文档，三处都会带到 P5 才爆。
- **P6 直接实证 + 对照组**（去向：**回馈 agate**，可入 verifier.md）。BDD-19 不只信 pytest 绿：构造含 `touch <哨兵>` 的证据，运行 `check-mvwu.py` 后哨兵不存在，**并手动执行同一命令证明哨兵手法本身有效**。"证明否定结论"必须带对照组，否则"没发生"可能只是手法无效。
- **按文件拆分的 P3 并行**（去向：**回馈 agate**，P3 卡「按包拆分并行」可补一例）。script 半边与 docs 半边各写不同测试文件，主映射由一方负责、另一方写配套映射，主 Agent 用 `test_bdd_NN` 命名做机械覆盖核对（71 条无遗漏）。
- **分阶段落盘救回被限流中断的评审**（去向：**回馈 agate**，佐证 dispatch-protocol「分阶段落盘」）。两个评审中断后，progress 文件里已有的实测记录（如"observe 耗时超长吞行"）被重派的评审接手并独立复现定级，没有从零开始。
- **`gate_commands` 读回自证**（去向：项目资产沉淀，位置：`agate/phase-cards/P2-design.md` 建议节，见 DEBT0047）：用 `agate-read-p5-commands.py` 读回后逐条 `shlex.split`，再在临时 git 仓库里对通配类命令做"删除/修改/新增"三向实证。
- **发布前先打本地 tag 再重跑 P5**（去向：已在 P8 卡片 DEBT0013 提示中，本次照做有效）：tag 前 CHECK 7 必红是设计使然，tag 后 0 ERROR。
- **强制追问"临时命令/脚本沉淀到哪"的回答**：本次的一次性脚本（P8 套用发布文本、DEBT 批量登记、`mv_row`）均落在会话临时目录，不入库；可复用的只有上面几条做法，已并入本节的去向标注，无需新增项目资产。

## 三、发现的问题

- 问题：judge dispatch-context 的 `objective_info` 里写了 `P0/P1/P2/P3/P4/P5/P6` 阶段序列，`check-judge-verdict.py` 报"两节含白名单外任务路径"exit 1。
  归因层面: 机制缺口
  说明：`_two_sections` 只在遇到下一个 `#` 标题行时结束当前节，`</dispatch_guide>`、`<objective_info>` 不是标题，故文件末尾的 objective_info 全被并入扫描面；协议只说"两节"。内容本身无害（未泄漏任何被隔离信息）。已登记 **DEBT0044**。

- 问题：P6→P7 时 `agate-next` 因 `check-p6-provenance` 非 0 而暂停，真实原因是 P6-gate-diagnosis.md 缺 `agate` 字段——而脚本提示写的是"协作规范，不阻塞"。
  归因层面: 机制缺口
  说明：警告置位后 `sys.exit(2)`，`agate-next` 只认 exit 0；暂停还会落盘占位 resolution 模板。提示语与行为矛盾，且原因不回显。已登记 **DEBT0045**。

- 问题：新增 `check-mvwu.py` 使既有 `test_sg_6` 由绿转红，P1 同类扫描却判 CHECK 9 锚点表"本次不处理"。
  归因层面: 机制缺口
  说明：协议没有"新增脚本要同步哪些登记面"的权威清单，P1/P2 卡要求的同类扫描也未规定必须实测；P2 评审靠实测拦下，靠的是评审者素质而非机制。已登记 **DEBT0046**，本任务以 P1 `[BASELINE_CHANGE]` + M18 处置。

- 问题：`gate_commands` 两个 key 的写法被读取器/shell 悄悄削弱（末尾引号被吞；通配被 shell 先展开致删除类变更漏检）。
  归因层面: 机制缺口
  说明：P2 卡未记录读取器语义；`gate_commands` 在 P2 固化、P4-P6 不可改，写错无第二次机会。已登记 **DEBT0047**。

- 问题：P3 提交的测试文件注释含 `/tmp` 字面量，P4 全量 pytest 才被 `check-platform-assumptions` R4 检出。
  归因层面: 机制缺口
  说明：P3 gate 只查映射文件与红灯，无平台假设扫描；派发 prompt 的口头要求无机械兜底。已登记 **DEBT0048**，本次以只改注释措辞的小修收口。

- 问题：主 Agent 在 `agate-next` 已提示"暂停转主 Agent 决策"的情况下，仍 `git add <任务目录>` 并提交，把 P7 产出连同未填充的 `P6-exit2-resolution.md` 提交进 phase=P6 的提交（`9e9e369`）。
  归因层面: 执行错误
  说明：P7 卡与 state-machine 均要求先确认推进结果、phase 与产出同 commit；本次未看 `agate-next` 的返回就提交。已用后续提交（`1daa651`）如实补救，未改写历史。

- 问题：主 Agent 写的 `P6-gate-diagnosis.md` 缺 `agent` 字段，直接触发上一条的暂停。
  归因层面: 执行错误
  说明：dispatch-protocol「gate 诊断落盘」的模板即含头部字段；本次手写文件时省略了 `agent`。

## 四、改进措施

| 措施 | 落点 | 去向 |
|------|------|------|
| `_two_sections` 遇到 `</dispatch_guide>` / `<objective_info>` 终止；judge 协议注明 objective_info 在扫描面内 | `agate/scripts/check-judge-verdict.py`、`agate/dispatch-protocol.md`「Judge 信息隔离」、`agate/assets/review-roles/judge.md` | DEBT0044（open） |
| provenance 警告不改退出码或提示语与 exit 1 一致；agate-next 暂停回显具体原因、不落盘占位模板 | `agate/scripts/check-p6-provenance.py`、`agate/scripts/agate-next.py` | DEBT0045（open） |
| 新增脚本登记面清单（含 SG.6 / CHECK 9 / CHECK 10）并要求同类扫描"实测" | `agate/assets/execution-roles/architect.md`、`agate/phase-cards/P2-design.md`、`agate/phase-cards/P1-requirements.md` 同类扫描节 | DEBT0046（open） |
| gate_commands 写法约束（末 token 不以引号结尾；通配转义；读回自证） | `agate/phase-cards/P2-design.md` gate_commands 声明节、`agate/scripts/agate-read-p5-commands.py` | DEBT0047（open） |
| P3 自查加 `check-platform-assumptions.py` | `agate/phase-cards/P3-tdd.md`、`agate/assets/execution-roles/test-designer.md` | DEBT0048（open） |
| 主 Agent 纪律：`agate-next` 非零/暂停时禁止批量 `git add` 任务目录，先核对输出；手写诊断文件对照模板头部 | 执行纪律，不修协议 | 本复盘记录（执行错误） |

**为何不走 hotfix 通道**：以上前五项都要改 `agate/scripts/*` 或 `agate/**/*.md`，命中 SELF-GATE 触发面，不满足 AGENTS.md hotfix 条件 2（且多于 2 个文件、需独立评审），必须走 worktree + PR，故登记 DEBT 而非顺手修。

## 五、技术债登记核对清单

| 机制 | 应该触发？ | 实际触发？ | 未触发后果 | 原因 |
|------|-----------|-----------|-----------|------|
| retry 记录 | 是 | ✅ | — | P1 一次、P2 两次均写入 `.state.yaml retries` |
| PAUSED | 否 | — | — | 未超限、未跨 ≥2 阶段回退 |
| PROD_TOUCHED | 否 | — | — | 全程本地 worktree 与临时目录 |
| SCOPE+ | 否 | — | — | 无新隐含需求；M18 走 `[BASELINE_CHANGE]`（P2 评审发现的既有测试约束） |
| SCOPE_RESOLVED | 否 | — | — | 同上 |
| DESIGN_GAP | 否 | — | — | P4 无 DESIGN_GAP 声明 |
| DESIGN_GAP_REVIEWED | 否 | — | — | 同上（P7 `design_gap_count: 0`） |
| NEED_CONFIRM | 否 | — | — | P1/P2 均 `[NO_NEED_CONFIRM]`；仅提交粒度/阶段 2 RM/CHANGELOG 三项由用户在 P8 后裁决 |
| CAPABILITY_GAP | 否 | — | — | 无 UI/视觉需求 |
| gate 验证（每阶段） | 是 | ✅ | — | 每阶段预跑并提交；P6→P7 暂停一次（见问题 2/6/7） |
| 阶段产出文件（每阶段） | 是 | ✅ | — | 63 个任务文件 |
| .state.yaml phase 同步 | 是 | ✅ | 曾错位一次 | `9e9e369` 在 phase=P6 时带入 P7 产出，后由 `1daa651` 补救（执行错误） |
| 裁剪条件 + override | 否 | — | — | 全阶段不裁剪 |
| capability_requirements | 是 | ✅ | — | `capability_requirements: []` |
| 分阶段落盘（防 subagent 空返回） | 是 | ✅ | — | 429 限流中断后 progress 文件被接手 |
| phase-产出一致性 | 是 | ✅ | 曾告警 | 见 phase 同步行 |
| P6 evidence（含截图 + 引用 + vision YAML） | 是 | ✅ | — | 31 个证据文件，无 UI 故无截图/vision |
| P2 候选方案 + 权衡（≥2） | 是 | ✅ | — | 3 个候选，选方案 A |
| P8 internal_only_reason | 否 | — | — | P8 未裁剪 |
| dispatch-context.md | 是 | ✅ | — | 每次派发（含重试）均先写后派；judge 文件曾被措辞误报，已改写并留 `P6-gate-diagnosis.md`（DEBT0044） |
| pre-commit hook（gate / 状态转移 / 裁剪） | 是 | ✅ | — | 各提交均过 hook；P0→P1 单独提交被 P1 gate 拦下（设计如此，随产出一并提交） |
| CI backstop | 是 | ✅ | — | PR #346 CI 全绿（含 gate-backstop） |
| **技术债登记** | 是 | ✅ | — | DEBT0043（P0/P1 发现的同类 fail-open，只登记未修）、DEBT0044-0048（本复盘登记）；阶段 2 承接项 RM-AG0067 |

## agate 反馈

> `feedback_ready: false`。五条机制缺口均已落为 DEBT0044-0048（含证据行号与关闭判据），暂不重复提取；如需汇总反馈，以 frontmatter 的 `mechanism_issues` 为准。
