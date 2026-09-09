---
phase: P1
task_id: TAG0034
type: review
parent: P1-requirements.md
trace_id: TAG0034-P1-20260909
status: approved
created: 2026-09-09
agent: requirements-review
risk_level: medium
phases:
- P1
- P2
- P3
- P4
- P5
- P6
- P7
- P8
packages:
- agate-scripts
- agate-rules
- agate-docs
- agate-tests
domains:
- backend
- cli
---

# TAG0034 P1 需求基线评审（requirements-review，独立视角）

评审对象：`agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（复核轮后 **53 条 BDD**，`risk_level: medium`，`ceremony: standard`，全 8 阶段不裁，`packages: [agate-scripts, agate-rules, agate-docs, agate-tests]`，`domains: [backend, cli]`，含 DEBT0039 并入的 §4.17 BDD-48/49/50）。
评审依据：`P0-brief.md`（task / scope / out-of-scope / known_risks 12 条 / env_constraints）、`P1-dispatch-context-requirements-review.md` 派发指引（强制指令，含「本轮是复核轮」节 6 项对照表）、角色定义 `agate/assets/review-roles/requirements-review.md`、`agate-workspace/debt/tech-debt.md` DEBT0039 条目，以及对本 worktree 现状的独立查证（见「客观查证摘要」）。

结论（复核轮 P1 retry #1 后）：**approved**。上轮 needs-revision 的 2 项必须修订项 + 4 项非阻塞建议 analyst 已修订，本轮逐项复核通过（见文末「复核轮（P1 retry #1）」节）：BDD-31 已去漂移版本串改机制锚定；新增 BDD-51（P5→P4 跨阶段回退重解析路由）+ BDD-26 边界注 + §2 同步，BDD-26↔BDD-51 措辞张力消除；BDD-35/38 措辞收紧；BDD-46 拆为 BDD-46/52/53。编号 BDD-1~53 连续无跳号；无新引入矛盾。全部 53 条 BDD 已判定通过。仅遗留 §3 第 8 行「BDD-44/47」溯源指针小瑕（非阻塞，建议改「BDD-46/47」）。

> 下方「必须修订项」「非阻塞建议」「门槛映射」为**上轮（needs-revision）记录，保留供追溯**；本轮最终结论以文末「复核轮（P1 retry #1）」节 + 本行为准。

---

## 客观查证摘要（评审对象的事实陈述已在 worktree 独立核实）

- `check-judge-verdict.py`（545 行）：全部文件访问均为 `task_dir` 相对路径 —— `P6.5-judge-verdict.md` / `P6.5-dispatch-context-judge.md` / `P6-evidence/` / `P1-requirements.md` / `gate-events.jsonl`（`LEDGER_NAME`）/ `os.listdir(task_dir)`。grep `\.claude|\.codex|sessions|transcript|rollout|expanduser|HOME` 命中 0。**不定位、不读取任何平台会话 transcript**。
- `check-p6-provenance.py`（578 行）：文件访问为 `task_dir` 相对路径 + `git -C task_dir`（`_run_git`）；读 `P6-acceptance.md` / `P1-requirements.md` / `P2-design.md` / `P6-dispatch-context-*.md` / `P6-evidence/` / `P[0-8]-*.md` / `.state.yaml`。grep 同上命中 0。**平台无关成立**。
- → §3 第 6 组结论「routed-away judge verdict 非真缺口」**独立核实成立**：judge 路由到 codex/opencode 子进程时，只要 verdict + 证据落 `TASK_DIR`（铁律 2/3 不变），两校验器纯 `TASK_DIR` 解析、平台无关照常通过。BDD-42 对该平台无关性作回归断言，合理。
- `check-events.py`：第 7 条「未知 event 类型不拦截（向后兼容；gate_run/judge_verdict/state_transition 为已知类型）」（脚本 line 14 / line 118）—— 故 `dispatch_route` 不会被判为「非法未知 event」（BDD-30 成立），但**理由码枚举校验 + 机械拒绝 `gate_fail`（BDD-27）是必须新增的扩展**，非现成能力；评审对象在 §3 第 4 行 / §4.7 已如实表述为「追加审计链」。
- `agate/assets/execution-roles/architect.md` line 209：`## 批次设计（强制节，TAG0014）` 节存在 → BDD-48 锚点有效。
- `agate/dispatch-protocol.md` line 502：`## 派发编排机制` 节存在 → BDD-49 锚点有效。
- `agate-workspace/roadmap/roadmap.md` RM-AG0060 行：含旧措辞「新增 `rules/dispatch-routing.yaml`」+「按序探测」+「`{cli,model}`」二元 → BDD-47 目标属实（§3 第 8 行标注行号 `:68` 与实际行不符，属非阻塞小瑕，内容确在）。
- `agate/scripts/agate-cmdstream-adapters.py`：`class CodexAdapter` line 666、`ADAPTERS["codex"]` line 878 —— TAG0033 前置已满足，§0 时效性质疑判据 3 结论属实。
- `agate/scripts/check-maintainability.py:_load_config`：全兜底先例在位（§0 / §3 第 5 行引用属实）。
- `git add agate-workspace/tasks/TAG0034-dispatch-routing/` 后 `git diff --cached --stat`：仅 `.state.yaml`（+2/-1，主 Agent P0→P1 跳变）、`P1-dispatch-context-analyst.md`（新）、`P1-dispatch-context-requirements-review.md`（新）、`P1-progress.md`（新）、`P1-requirements.md`（新 487 行）、`gate-events.jsonl`（+1，P0→P1 transition 事件）。**全部为 md/yaml/jsonl，无代码改动泄漏**——与「P1 暂存区只有 P1 产出、实际代码改动在 P2+」一致。
- `[PROD_NOT_TOUCHED]`：本次评审仅在 worktree 内读；写入仅 `P1-review.md` + `P1-progress.md`（本任务目录内）。主 checkout / `~/.agate` 未触碰。

---

## BDD 评审（逐条判定 + 覆盖维度标注）

> 维度记号：数据 / 前端 / 多端 / 边界 / 兼容。「—」= 该 BDD 场景与此维度无关（非遗漏）。
> 判定用「通过」（可二值判定、判据锚客观信号）/「需修订」（有阻塞问题）/「通过·可优化」（可判定但措辞可收紧，非阻塞）。

### §4.1 schema 校验

- `BDD-1`（tier+effort 两轴合法组合被接受）：**通过**。判据 = 校验器 exit 0，二值。维度：数据✓（配置结构） 前端— 多端— 边界✓（交叉组合） 兼容—
- `BDD-2`（tier 与 candidates 互斥）：**通过**。exit 1，二值。数据✓ 前端— 多端— 边界✓ 兼容—
- `BDD-3`（`(phase,role)` key，role 可选）：**通过**。exit 0，两种 key 形态识别，二值。数据✓ 前端— 多端— 边界✓ 兼容✓（role 省略回落）
- `BDD-4`（非法 cli 取值被拒）：**通过**。exit 1，枚举 `{native,claude-code,codex,opencode}`，二值。数据✓ 前端— 多端✓（cli 枚举即多端契约） 边界✓ 兼容—
- `BDD-5`（非法 effort 取值被拒）：**通过**。exit 1，枚举 `{low,medium,high}`，二值。数据✓ 前端— 多端— 边界✓ 兼容—
- `BDD-6`（`fallback` 字段不存在于 schema）：**通过**。exit 1，二值。承接 P0-brief scope「已定：无 `fallback` 字段」，非 P1 越界做设计。数据✓ 前端— 多端— 边界✓ 兼容✓（终点回落恒为默认派发）

### §4.2 档位→候选链展开 + effort 各平台映射

- `BDD-7`（tier 引用展开为有序跨 CLI 候选链）：**通过**。判据 = 展开顺序与机器级绑定声明顺序逐项一致，二值。数据✓ 前端— 多端✓ 边界— 兼容—
- `BDD-8`（effort→Codex 推理档 flag）：**通过·可优化**。判据 = 命令含 `-c model_reasoning_effort=high` 或 `spawn_agent(reasoning_effort="high")`，可 grep，二值。flag 名版本漂移属 P0-brief known_risk「落地前照 research §10 逐平台复核」已覆盖，非 P1 阻塞。数据✓ 前端— 多端✓ 边界— 兼容—
- `BDD-9`（effort→OpenCode 推理档 flag）：**通过·可优化**。判据 = 命令含 `--variant high` 或等价 `#high` 后缀，二值。同 BDD-8 备注。数据✓ 前端— 多端✓ 边界— 兼容—
- `BDD-10`（effort 在 Claude Code CLI 静默忽略、不报错）：**通过**。判据三段全客观：派发无 error / 无非零退出、构造命令不含 effort flag、`platform-notes.md` 存在注明句（可 grep），二值。数据— 前端— 多端✓ 边界✓（不支持轴的降级） 兼容✓
- `BDD-11`（`(phase,role)` 命中优先于 phase 级）：**通过**。取候选链 Y，二值。数据✓ 前端— 多端— 边界✓ 兼容—
- `BDD-12`（无 `(phase,role)` 条目回落 phase 级）：**通过**。取候选链 X，二值。数据✓ 前端— 多端— 边界✓ 兼容—
- `BDD-13`（无 phase 条目 = standard）：**通过**。解析结果 = `standard` 档（等价未配置），二值。数据✓ 前端— 多端— 边界✓ 兼容✓

### §4.4 standard 语义钉死

- `BDD-14`（standard 恒等于继承主 Agent 当前 model 的原生派发）：**通过**。判据 = 派发方式与「本机制未启用」逐字节一致，二值（可字节比对）。这是「不配置=现状」不变量的核心锚。数据— 前端— 多端✓ 边界✓ 兼容✓（钉死 standard 语义 = 局限 6 零基础设施不变量）

### §4.5 三层配置优先级 + 合并语义 + 全兜底

- `BDD-15`（三层优先级确定且可判定）：**通过**。判据 = 取值来源严格按「P2 定死的优先级序」、结果唯一确定、无运行时含糊分支；Then 括注给出建议序（项目级直接值 > 项目级档位映射 > 机器级绑定 > 协议出厂默认）但明确落点在 P2 —— 如实留白，非 P1 武断锁定。二值（结果唯一性可判）。数据✓ 前端— 多端— 边界✓ 兼容✓
- `BDD-16`（配置文件缺失→出厂默认，不报错）：**通过**。exit 0 + 无 error + 全 `standard`，判据形态复用 `_load_config`，二值。数据✓ 前端— 多端— 边界✓ 兼容✓
- `BDD-17`（配置损坏/类型坏→出厂默认，不报错不静默跳过）：**通过**。回落默认 + 一行 stderr WARNING + exit 0 + 不抛异常 + 不整段跳过，二值。数据✓（YAML 解析失败 / 键类型坏） 前端— 多端— 边界✓ 兼容✓
- `BDD-18`（机器级绑定与项目级映射冲突时取值确定）：**通过**。判据 = 按「P2 定死的合并规则」取唯一结果、不产生「两条都生效」歧义；Then 给两个候选处理（后写覆盖 / 报 schema 错）并标「P2 定」—— 如实留白。二值（歧义有无可判）。数据✓ 前端— 多端— 边界✓ 兼容✓

### §4.6 try-and-fall 逐级回落（无 probe）

- `BDD-19`（无 probe——首选候选直接派发）：**通过**。判据 = 不发任何「探测/hi」预请求、第一个动作即派真实 dispatch-context，二值。正面钉死 out-of-scope「probe-then-commit」。数据— 前端— 多端✓ 边界✓ 兼容✓
- `BDD-20`（launch_fail→回落下一候选）：**通过**。理由码 `launch_fail` + 派下一候选，二值。数据— 前端— 多端✓ 边界✓（CLI 未装 / OSError） 兼容✓（配了但未装 = 现状回落）
- `BDD-21`（infra_error→回落下一候选）：**通过**。理由码 `infra_error` + 派下一候选，二值。识别形态列举（401 循环 / 网络不可达 / 429 / 进程中途崩溃）具体可判。数据— 前端— 多端✓ 边界✓ 兼容—
- `BDD-22`（no_parseable_output→回落下一候选）：**通过**。理由码 `no_parseable_output` + 派下一候选，判据锚 D2 假完成校验（产出文件缺失/空 / 结构化输出空返回），二值。数据✓ 前端— 多端✓ 边界✓ 兼容—
- `BDD-23`（全部候选落空→默认派发）：**通过**。判据 = 回落默认派发 + `dispatch_route` 事件 `final` = `{"cli":"default"}` + `candidates_tried` 保留每个失败理由码，可计数、二值。数据✓ 前端— 多端✓ 边界✓（候选全灭） 兼容✓（恒等于未启用）

### §4.7 完整性不变量（最高危——模型购物完整性洞）

- `BDD-24`（候选回落只在三类基础设施信号时发生）：**通过**。判据 = 产出质量差/不完整时「不回落」，二值（是否回落）。与 BDD-25/26 无矛盾（三者共同表达「有 gate 能评产出即不换候选」）。数据— 前端— 多端— 边界✓ 兼容—
- `BDD-25`（收到任何 gate 能评产出即停止回落）：**通过**。判据 = 约定产出文件非空/格式合法 → 判成功、停止后续候选、交 gate，二值。数据✓ 前端— 多端— 边界✓ 兼容—
- `BDD-26`（gate 判 FAIL→同一候选 retry，绝不换候选，dispatch_route 计数不增）：**通过**。判据措辞已成可计数客观信号 —— 「`gate-events.jsonl` 中 `dispatch_route` 事件条数与 gate FAIL 前相同」，`grep -c` 可核，二值。命中派发指引对 BDD-26 的专项要求。数据✓（事件计数） 前端— 多端— 边界✓ 兼容— 。**注**：与 §2 边界维度识别的「P5→P4 回退后重解析路由」存在措辞张力，见「必须修订项 2」。
- `BDD-27`（理由码枚举仅三值，check-events.py 机械拒绝 gate_fail）：**通过**。判据 = 出现 `gate_fail`（或任何非法值）→ `check-events.py TASK_DIR` exit 1；合法三值 exit 0。exit code 二值，命中派发指引对 BDD-27 的专项要求（措辞成可机械判定的客观信号）。数据✓ 前端— 多端— 边界✓ 兼容—
- `BDD-28`（候选回落不写 state_transition、不动 retries、不触发 PAUSED）：**通过**。判据三段全可核（`retries[Pn]` 数值不变 / 无新增 `state_transition` 事件 / 未进 PAUSED / 只新增 1 条 `dispatch_route`），二值。数据✓ 前端— 多端— 边界✓ 兼容—

### §4.9 dispatch_route 事件 + check-events 校验端

- `BDD-29`（写入 gate-events.jsonl 且复用既有哈希链）：**通过**。判据 = `prev_hash == sha256(上一行原始文本)` + `ts` 单调不减 + `check-events.py` 第 3-5 条 exit 0，二值。数据✓（append-only 账本） 前端— 多端— 边界✓ 兼容✓
- `BDD-30`（check-events.py 认 dispatch_route 为已知合法事件类型）：**通过**。判据 = exit 0 + 不判「非法未知 event」+ 既有 `test_check_events.py` 用例零改动仍绿，二值。数据✓ 前端— 多端✓（写入端↔校验端同步） 边界✓ 兼容✓（既有用例零改动 = 向后兼容回归）

### §4.10 cli: native 各平台执行

- `BDD-31`（cli: native on Claude Code — Task 单次调用传 model）：**需修订**。判据机制部分（`--output-format json` 的 `modelUsage` 字段可核实 + 驱动会话侧无自由裁量）站得住，但 Then 的断言目标 `子代理实际运行 model = claude-haiku-4-5-*` **绑定了会漂移的实现版本串**。派发指引 BDD-31/32 专项明确要求：「判据应锚定『可核实实际 model』的机制而非硬编码版本串」。通配 `-*` 只容忍 patch/日期后缀，family 版本 bump（`claude-haiku-4-6` / `-5-*`）即令该 BDD 失效。**修订方向**：Then 改为「`modelUsage` 显示的实际 model 与候选 `model: haiku` 的档位/别名解析结果一致（非父会话 model）」，不钉死具体 family 版本串。维度：数据— 前端— 多端✓ 边界— 兼容✗（漂移风险即在此）
- `BDD-32`（cli: native on OpenCode — 命名 subagent 间接路）：**通过**。判据 = 存在 phase→预配命名 agent 映射 + 预注册机制、被派 agent 的 `agents.<name>.model` = 候选 model、子代理实际跑该配置 model（非父会话 model）。用占位符 `provider/M-pro`（非真实符号），锚定「实际 model = 配置 model」机制，无漂移绑定，二值。数据— 前端— 多端✓ 边界✓（间接路复杂度） 兼容—

### §4.11 跨 CLI 子进程 spawn + 结构化输出解析

- `BDD-33`（claude-code 子进程 + JSON 输出解析判成败）：**通过·可优化**。判据 = `stop_reason == "end_turn"` 判正常 + `modelUsage` 确认 model + 非 `end_turn`/空输出判失败进回落，二值。`stop_reason` 字段名 / flag 名属 research §10「落地前逐平台对官方文档复核」覆盖面，非 P1 阻塞。数据✓ 前端— 多端✓ 边界✓ 兼容—
- `BDD-34`（codex 判成败必须解析事件流、不靠退出码）：**通过**。判据 = 构造「exit 0 但实际失败」真实终态样本（账号不支持 model → `turn.failed{status:400}` 却 exit 0）、按 `turn.completed` vs `turn.failed` 判、该样本被正确判失败并进回落，二值（样本有已知预期结论）。命中 P0-brief「主动构造终态样本」（DEBT0035 教训）。数据✓ 前端— 多端✓ 边界✓ 兼容—
- `BDD-35`（codex item 级 status:"failed" 与 turn.failed 是两层）：**通过·可优化**。「P2 须明确取哪层」如实留给 P2（Then：「按 P2 明确取的那一层判定 turn 层 vs item 层」）—— 命中派发指引对 BDD-34/35 的专项要求，未在 P1 武断锁定。Then 收尾「结论稳定（不因两层混淆而误判整条 turn 成败）」措辞略软；建议补明「构造样本的已知正确 verdict = X，解析结论须等于 X」使 P6 判定粒度更清。二值性依赖构造样本的已知预期，可判。数据✓ 前端— 多端✓ 边界✓ 兼容—
- `BDD-36`（opencode 子进程 + 空返回判定）：**通过**。判据 = 构造失效 provider 空返回样本（只有头行、无 assistant 内容、exit 0）、按 `step_finish.part.reason == "stop"` 判正常、空返回判失败进回落，二值。数据✓ 前端— 多端✓ 边界✓（空返回终态） 兼容—

### §4.12 tmux 观测层（P4c，不通过不影响 P4a/P4b — §4.12 节头已标注）

- `BDD-37`（which tmux 决定包裹 or 裸跑）：**通过**。判据 = 场景 A `tmux new-session -d -s <ns-task-phase-ts> '<cmd> | tee <capture>'` + capture 被 tail；场景 B 裸跑；两场景 `dispatch_route` 留痕 + gate 结果逐字节一致，二值。数据— 前端— 多端— 边界✓（tmux 缺失降级） 兼容✓
- `BDD-38`（tmux session 退出倒计时 + 有 client 不强杀）：**通过·可优化**。判据 = `list-clients` 空 → `kill-session`；非空 → 不强杀、倒计时收尾；异常未退出超 `N + 余量` → 兜底强杀。「余量」未量化；建议给具体值或显式标「P2 定值」。行为分支二值可判。数据— 前端— 多端— 边界✓（生命周期兜底） 兼容—

### §4.13 回归证明（零改动 + 不配置 = 逐字节现状）

- `BDD-39`（gate / 状态机 / phases.yaml 结构零改动）：**通过**。判据 = `check-gate.py` / `check-state-transition.py` / `phases.yaml` / `state-machine.md` 结构化部分逐字节不变 + `agate-dispatch.py` 既有渲染产物测试（`test_tag0027_b2_*`）零改动仍绿，二值。命中 known_risk「gate 解耦是设计前提，回归必须证明」。数据✓ 前端— 多端— 边界✓ 兼容✓
- `BDD-40`（不配置 = 逐字节现状）：**通过**。判据 = 跑完整 P1→P8、每阶段派发方式/产出/`gate-events.jsonl` 与机制引入前一致、`dispatch_route` 事件条数 = 0，可计数、二值。数据✓ 前端— 多端— 边界✓ 兼容✓（机会式启用不变量）
- `BDD-41`（dispatch-protocol.md 新节显式写「gate 不认谁生产的」）：**通过**。判据 = 新节含该句 + 两条完整性不变量（候选回落≠retry / gate FAIL 绝不换候选）+ 「查表→派首选→逐级回落→再派发」步位于铁律 1 之前，可 grep，二值。数据— 前端— 多端— 边界— 兼容✓

### §4.14 routed-away judge verdict 平台无关性（P4b 核实项）

- `BDD-42`（路由到子进程的 judge，verdict 落 task dir 后 P6.5 gate 平台无关通过）：**通过**。判据 = `check-gate.py P6.5 TASK_DIR` exit 0 + 两校验器（`check-judge-verdict.py` / `check-events.py`）本任务零改动，二值。**独立核实**：两校验器纯 `TASK_DIR` 解析、不读平台 transcript（见「客观查证摘要」），该 BDD 断言的前提成立。数据✓ 前端— 多端✓ 边界✓ 兼容✓

### §4.15 与既有派发机制的交互

- `BDD-43`（五模式并行批——每个并行 subagent 各自独立解析路由）：**通过**。判据 = 每 subagent 独立解析、同 role 并行分片解析到同一路由、不同 role 各按自己 `(phase,role)`，二值。命中 P0-brief scope 交互项①。数据✓ 前端— 多端✓ 边界✓（五模式并行） 兼容—
- `BDD-44`（自主再派发的子任务不走路由表）：**通过**。判据 = 不解析 `dispatch-routing.yaml`、继承父的实际 cli/model、无 `dispatch_route` 事件，二值。命中 scope 交互项②（倾向「不走」已落为硬判据）。数据✓ 前端— 多端✓ 边界✓（RM-AG0055 自主再派发） 兼容✓
- `BDD-45`（单 Agent 模式路由为 no-op 且显式声明出范围）：**通过**。判据 = 无派发动作、路由 no-op、`dispatch-protocol.md` / design-note 显式写「单 Agent 模式下路由不适用」（可 grep），二值。命中 scope 交互项③。数据— 前端— 多端✓ 边界✓（`has_task_tool:false`） 兼容✓

### §4.16 design-note 修订 + roadmap 回写

- `BDD-46`（design-note 头部 + §2.1/§2.2 按 2026-09-09 定案重写）：**通过·可优化**。Then 含 ~6 项子断言（落点不再 `agate/rules/` / 核心循环改 try-and-fall / 含两轴 + `(phase,role)` key / `cli: native` 弱缓解标注 / 含两条完整性不变量 / 含 per-machine 机会式）—— 每项均可 grep、二值；但一条 Then 塞 6 断言，P6 逐条 PASS/FAIL 粒度会糊。建议拆为 2-3 条子 BDD（非阻塞，doc-revision BDD 常见形态）。数据— 前端— 多端— 边界— 兼容✓
- `BDD-47`（roadmap RM-AG0060 长描述旧措辞回写）：**通过**。判据 = 不再含 `rules/dispatch-routing.yaml` 与「按序探测」字样 + 与 design-note 定案一致，可 grep，二值。数据— 前端— 多端— 边界— 兼容✓

### §4.17 DEBT0039 文档边界澄清（SCOPE+ 用户批准并入）

- `BDD-48`（architect.md「批次设计」节含「补协议文档正文 = P4」的显式边界措辞）：**通过**。判据 = 该节存在显式说明句（「补协议文档正文 …… = P4 实现工作 …… P7 只做跨文件一致性验证、不 author 文档内容」）、关键串 grep 命中，二值。锚点节「批次设计」经核存在（architect.md:209）。忠实承接 DEBT0039 `closure_criteria` 第 1 条。数据— 前端— 多端✓（跨文件边界） 边界— 兼容—
- `BDD-49`（dispatch-protocol.md「派发编排机制」节显式区分 author 内容 P4 vs 一致性验证 P7）：**通过**。判据 = 该节存在区分句 + 节标题「派发编排机制」仍存在，关键串 grep 命中，二值。锚点节经核存在（dispatch-protocol.md:502）。忠实承接 `closure_criteria` 第 2 条。数据— 前端— 多端✓ 边界— 兼容—
- `BDD-50`（全量 consistency 改后仍 0 ERROR，回归）：**通过**。判据 = `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` exit 0，二值。承接 `closure_criteria` 第 3 条（DEBT0039 原文写「consistency 0 ERROR」，评审对象用 `--strict-errors-only` 变体 —— AGENTS.md 定义该变体为「只按 ERROR 判失败」，口径等价，可接受）。数据— 前端— 多端✓ 边界— 兼容✓

**BDD 结构性核查**：编号 `#### BDD-1:` … `#### BDD-50:` 连续、无跳号（主 Agent 已机械核，本轮语义复核确认）；每条单一 Given / When / Then；全篇无「⚠️ 调整」「部分通过」中间态；无同 Given/When 场景 Then 相互矛盾（BDD-24/25/26 三点成一致谱系，非矛盾；BDD-16/17 文件缺失 vs 损坏均→出厂默认，一致）。

---

## 隐含需求覆盖（逐维度结论）

- **同类/影响面维度**：**覆盖**。§3 同类扫描 9 组（第 9 组为 DEBT0039 带入的 architect.md 新增面），每组含命中数 + 文件清单 + 逐条「本次处理/不处理 + 理由」+ 回归拦截手段（4 条，均转对应 BDD）。9 组结论经抽查（第 3/4/5/6/7/8/9 组）可信；第 6 组独立 grep 核实成立。
- **数据维度**：**覆盖**。§2 数据行 + BDD-29（`prev_hash`/`ts` 哈希链）+ BDD-27（理由码枚举）+ BDD-22（D2 空产出）。`gate-events.jsonl` append-only 语义（`check-events.py` 第 4 条）明确不破坏，新事件复用既有哈希链、不改写历史行。
- **前端维度**：**明确排除且成立**。`domains: [backend, cli]` 无 frontend；§2 前端行说明无用户可见页面/渲染产出。独立核实 `check-gate.py:_gate_p1_vision_capability`（line 440）仅 `domains` 含 frontend 触发 —— 本任务不触发 vision 硬拦；无 UX 类别 BDD / `ui_render_shape` / `ui_ux_dimensions` 属正确省略，非遗漏。
- **多端维度**：**覆盖**。本任务本体即「多 CLI 端」。写入端↔校验端同步：BDD-30（`check-events.py` 认 `dispatch_route`）+ BDD-27（理由码校验端）。`platform-notes.md` 三平台章：BDD-10（Claude Code effort 注明）+ BDD-8/9（Codex/OpenCode flag）。各 `SETUP.md` 自动化 flag 小节在 §1 / §7 声明为 P4 交付。cli 枚举即 API↔客户端契约（BDD-4）。
- **边界维度**：**大体覆盖，1 处识别未落 BDD（见必须修订项 2）**。已覆盖：候选全灭（BDD-23）/ 配了但 CLI 未装未认证（BDD-20）/ 配置文件损坏（BDD-17）/ gate FAIL 后 retry（BDD-26）/ 五模式并行批（BDD-43）/ 自主再派发（BDD-44）/ 单 Agent 模式 `has_task_tool:false`（BDD-45）/ 空返回终态（BDD-36）/ 非 0 退出但失败（BDD-34）。**未落 BDD**：§2 边界行明列的「回退（P5→P4）后重解析路由」在 §4 无任何对应 BDD。
- **兼容维度**：**覆盖**。「不配置 = 逐字节现状」：BDD-40 + BDD-14（standard 语义钉死 = 继承主 Agent 当前 model 的原生派发）+ BDD-39（结构零改动）。`standard` 语义钉死防「出厂默认全 standard ≠ 现状」，命中 known_risk「机会式启用局限 6 张力」。既有测试零改动回归：BDD-30 / BDD-39。

---

## 裁剪评审（phases 全走不裁 —— 逐阶段核对「走」的理由）

`phases: [P1, P2, P3, P4, P5, P6, P7, P8]`，无跳过阶段。逐阶段「走」的理由核对：

- **P1（走）**：需求基线，不可裁。理由成立。
- **P2（走，不可裁）**：改协议本体（`agate/rules/` 档位词表 + `dispatch-protocol.md` 新节）+ 三层配置 + 完整性不变量高危 → 须方案设计 + C8 域独立评审（protocol-alignment-review）。理由成立。
- **P3（走，不可裁）**：新增 schema 静态校验器 + `dispatch_route` 理由码校验 + 回归证明 → TDD 先写红。理由成立。
- **P4（走，不可裁）**：实现，内部 P4a/P4b/P4c 串行子批。理由成立。DEBT0039 两处纯文档边界澄清明确标为 P4 author 工作（非 P7）—— 与 DEBT0039 根因（架构师把补文档正文误标 P7）自洽。
- **P5（走，不可裁）**：三平台真机验证 + 回归全绿。理由成立（P0-brief 前置真机核实 + `requires_minimal_validation`）。
- **P6（走，不可裁）**：逐条 50 BDD 验收。理由成立。
- **P7（走，不可裁）**：改协议本体 + SELF-GATE，跨 `dispatch-protocol.md` / `agate-dispatch.py` / `check-events.py` / rules 档位词表 / `SETUP.md` / `platform-notes.md` / `architect.md` / design-note 一致性核对。理由成立。`ceremony: standard`（非 full），故「full → phases 含 P7」硬校验不适用，但 P7 已在 phases 内、理由充分。
- **P8（走，不可裁）**：SELF-GATE 收尾；roadmap RM-AG0060 回写 done（P8 gate 硬校验 RM-AG0043）；DEBT0039 置 closed + `task_id: null` → `TAG0034`。理由成立。

**裁剪评审结论：全 8 阶段「走」的理由逐条成立，无可质疑的应裁未裁 / 不应走而走。**

---

## 审声明（风险分级 / 仪式 / 阶段声明 vs diff 证据，TAG0019）

核对口径（派发指引）：本阶段暂存区只有 P1 产出（md/yaml/jsonl），实际代码改动在 P2+ —— 核对「声明与 P0-brief 描述的改动面是否自洽」，非「暂存区已有代码 diff」。

- **`git diff --cached --stat` 证据**（`git add agate-workspace/tasks/TAG0034-dispatch-routing/` 后）：`.state.yaml`（+2/-1）、`P1-dispatch-context-analyst.md`（+340）、`P1-dispatch-context-requirements-review.md`（+322）、`P1-progress.md`（+18）、`P1-requirements.md`（+487）、`gate-events.jsonl`（+1）。**文件类型**：全 md/yaml/jsonl，无 `.py` / 无非文本产出。**规模**：P1 产出 6 文件 ~1169 行增。**域**：仅 `agate-workspace/tasks/TAG0034-dispatch-routing/` 任务命名空间内。→ 与「P1 暂存区只有 P1 产出」一致，无代码改动泄漏。
- **`risk_level: medium` vs 改动面**：P0-brief 定「epic 拆走 Codex 接入后按五维评级 ≈ medium」。改动面 = 改协议本体（`dispatch-protocol.md` + `agate/rules/` 档位词表）+ 扩 `agate-dispatch.py` + 可能扩 `check-events.py` + 新增校验器 + 三层配置 + `agate/tests/` + SELF-GATE。**核对结论：与 P0-brief 自洽（medium）**，但存在张力 —— known_risk 明列「模型购物完整性洞（最高危）」。评审判断：该最高危项由 BDD-24~28 + `check-events.py` 机械强制枚举校验覆盖，且 P0-brief 已在完成五维评级后仍定 medium，故不因此单点上调；**建议 P2 architect 在方案设计里对「完整性不变量」批显式声明高危评审强度**（写入 dispatch_plan 批次 complexity）。此为非阻塞观察，不构成 needs-revision 的独立理由。
- **`ceremony: standard`（显式，不薄化）vs 改动面**：改协议本体 + 完整性不变量高危不适合薄化。声明 standard 未申请 thin，无 `coupling_checklist` / `跳过风险` 流式声明需求（thin 才需）。**核对结论：自洽**。`ceremony` 非 full，故 P7 不受「full → phases 含 P7」硬校验约束，但 P7 已在 phases。
- **`phases: [P1..P8]` vs 改动面**：全走，与「改协议本体 + SELF-GATE + 三平台真机验证 + 50 BDD 验收」自洽。**核对结论：自洽**。
- **`packages: [agate-scripts, agate-rules, agate-docs, agate-tests]` vs 改动面**：`agate-scripts`（`agate-dispatch.py` / `check-events.py` 扩展 + 新 schema 校验器）✓；`agate-rules`（`agate/rules/` 档位词表新文件）✓；`agate-docs`（`dispatch-protocol.md` / `SETUP.md` / `platform-notes.md` / design-note / roadmap + **DEBT0039 并入的 `architect.md`**）—— architect.md 归 `agate-docs` 而非独立 package 项：该文件是 `agate/assets/execution-roles/` 下角色资产、非严格「docs」，但本次仅纯文本措辞增补、枚举中无「agate-assets」项，§8 已显式说明理由，**可接受**；§9 P7 一致性核对文件清单已显式含 architect.md，闭环。`agate-tests`（`agate/tests/` 新增 pytest）✓。**核对结论：自洽**。

**审声明核对结论：`risk_level` / `ceremony` / `phases` / `packages` 声明与 P0-brief 描述的改动面自洽；暂存区 diff（全 md/yaml/jsonl、仅任务命名空间内）与「P1 阶段暂存区只有 P1 产出」一致。审声明不构成 needs-revision 理由。**

---

## DEBT0039 增补专项核对

- **§1 SCOPE+ 条目登记**：**通过**。`[SCOPE+ from user-approval：DEBT0039 并入 TAG0034]` 标注来源为「用户批准 + DEBT0039 并入，主会话已确认转交条件，2026-09-09」，明确写「非顺手改漏」。边界约束写明「仅限 `architect.md`「批次设计」节 + `dispatch-protocol.md`「派发编排机制」节两处纯文档、不扩其它 DEBT、不改任何脚本 / gate 逻辑」，且 §7 另有专门「边界约束」bullet 复述。承接 DEBT0039 `closure_criteria` 三条 → 转 BDD-48/49/50。
- **§3 同类扫描第 9 行 architect.md 新增面披露**：**通过**。第 9 行显式标注「`agate/assets/execution-roles/architect.md` 是 **P0-brief 声明改动面之外、经用户批准新增的改动面**（DEBT0039 并入带入，frontmatter `packages` 归 `agate-docs`）」。这是本次并入的关键披露，已明确落盘，未漏。
- **BDD-48-50 承接 closure criteria**：**通过**。与 `tech-debt.md` DEBT0039 `closure_criteria` 逐条比对：① 「architect.md「批次设计」节含「补协议文档正文 = P4」的显式边界说明」→ BDD-48（关键串 grep）；② 「dispatch-protocol.md「派发编排机制」区分 author 内容（P4）vs 一致性验证（P7）」→ BDD-49（关键串 grep + 节标题仍存在）；③ 「consistency 0 ERROR」→ BDD-50（`check-protocol-consistency.py --strict-errors-only` exit 0）。三条判据均锚客观信号（节标题 / 关键串 grep 命中 / exit code），可二值判定。
- **§7·§9 阶段边界**：**通过**。§7 P4 行显式「DEBT0039 的两处纯文档边界澄清 …… = P4 author 工作**（不是 P7）」，与 DEBT0039 根因（补文档正文误标 P7）自洽。§7 bullet + §9 P8 均含「DEBT0039 置 `status: closed`、`task_id: null` → `task_id: TAG0034`」。§9 P7 一致性核对文件清单含 architect.md。
- **`packages` 覆盖 architect.md**：**通过（可接受）**。归 `agate-docs`，§8 说明「纯文档措辞，无需独立 package 项」。枚举中无 `agate-assets`，folding 进 `agate-docs` 为务实处理；P7 一致性核对已显式追踪 architect.md，无覆盖遗漏风险。

**DEBT0039 专项核对结论：SCOPE+ 登记 / 新增面披露 / closure criteria 承接 / 阶段边界 / packages 五项全部通过。**

---

## §3 第 6 组「routed-away judge verdict 非真缺口」独立核对

- 独立 grep `agate/scripts/check-judge-verdict.py` 与 `agate/scripts/check-p6-provenance.py`：模式 `\.claude|\.codex|\.config|sessions|CLAUDE_CONFIG|CODEX_HOME|expanduser|HOME|transcript|rollout` —— **两脚本命中 0**。
- `check-judge-verdict.py` 全部文件访问经审读为 `task_dir` 相对：`P6.5-judge-verdict.md`（line 405）/ `P6.5-dispatch-context-judge.md`（line 406）/ `P6-evidence/`（line 243）/ `P1-requirements.md`（line 445）/ `gate-events.jsonl`（`LEDGER_NAME`，line 302）/ `os.listdir(task_dir)`（line 340）。
- `check-p6-provenance.py` 全部文件访问为 `task_dir` 相对 + `git -C task_dir`（`_run_git`，line 151-156）：`P6-acceptance.md` / `P1-requirements.md` / `P2-design.md` / `P6-dispatch-context-*.md`（glob）/ `P6-evidence/` / `P[0-8]-*.md`（glob）/ `.state.yaml`。
- **核对结论：analyst 判定成立**。两校验器不定位、不读取 `~/.claude/` 或 `~/.codex/sessions/` 平台 transcript；judge 路由到 codex/opencode 子进程时，只要其 verdict 文件 + 证据落 `TASK_DIR`（铁律 2/3 保证），`check-judge-verdict.py` + `check-events.py` 平台无关照常通过。§3 第 6 组「非真缺口」结论 + BDD-42 的回归断言均可信，不因此转 needs-revision。

---

## P1 纯净性（有无掺入解决方案设计 / 实现细节）

- **通过**。本任务 BDD 天然贴近机制（schema 字段名、flag 名、事件字段），判据口径 = 「描述可验收行为/客观信号 vs 替 P2 做设计决策」。多处如实留白给 P2：BDD-15（「P2 定死的优先级序」）/ BDD-18（「P2 定死的合并规则」）/ BDD-35（「P2 明确取的那一层」）。
- §5 六条 `[SUGGEST:]`（tier 命名 bulk/standard/deep / `model: null` 合法 / MVP 合并①③ + 是否拆机器级档位文件由 P2 定 / 三层优先级 / 扩 `agate-dispatch.py` 子命令 / 新增 `check-dispatch-routing.py`）—— 逐条核实均以 `[SUGGEST:]`（非 `[NEED_CONFIRM]`）呈现，无破坏性变更 / 无业务方向决策，属「有倾向待主 Agent 采纳」的非阻塞项，非 P1 越界。
- BDD-6（无 `fallback` 字段）承接 P0-brief scope「已定」，非 P1 新做设计决策。

---

## 时效性质疑核对

- §0 已做：独立复核严重判据 1-3，结论「无严重漂移」，逐条给复核依据（方案成立 / 前提成立 / TAG0033 前置已合并 v0.70.0）。
- 轻微偏移标记规范：`[P0_STALE: Claude Code 本机实际 2.1.266，P0-brief / HANDOFF known_risks 记 2.1.263]` —— 写出具体漂移点、判为轻微（patch bump，未命中严重判据 1-3、属 known_risk 已预期的 flag 名版本漂移）、已在本文件 `verification_env` / §7 反映实际版本、P0-brief 字段回写留给主 Agent。处理方式（记录不阻塞）符合 P0 卡片漂移分流表。**核对通过**。

---

## 必须修订项（转 analyst 修改，阻塞 approved）

**1. BDD-31 判据绑定漂移的实现版本串 `claude-haiku-4-5-*`。**
- 问题：Then「子代理实际运行 model = `claude-haiku-4-5-*`」把验收判据钉在会漂移的 model family 版本串上。派发指引 BDD-31/32 专项明确：「Then 子句不应绑定会漂移的实现符号（model id 字符串 `claude-haiku-4-5-*` 之类）—— 判据应锚定「可核实实际 model」的机制而非硬编码版本串」。通配 `-*` 仅容忍 patch/日期后缀，family bump 即失效。
- 修订方向：Then 改为锚定机制 —— 例如「`--output-format json` 的 `modelUsage` 字段显示的实际 model 与候选 `model: haiku` 经档位/别名解析后的目标一致，且非父会话继承 model」。保留「驱动会话侧无自由裁量（目标 model 由决策层全量算好）」子句。

**2. §2 边界维度识别的「回退（P5→P4）后重解析路由」在 §4 无对应 BDD，且与 BDD-26 存在措辞张力。**
- 问题：§2 隐含需求「边界」行明列「回退（P5→P4）后重解析路由」为必须覆盖项，但 §4 无任何 BDD 操作化它。P0-brief scope 明确「P5→P4 回退后的 P4 retry 等，**重新解析一次 `(phase,role)` 路由**（落哪个候选看当时哪个能用），**不做「上次失败所以这次故意升档/换模型」的逻辑**」。而 BDD-26 Then 写「retry 在**同一候选**上重跑（不重新解析路由换候选）」—— 二者需显式区分：**同阶段内 gate FAIL retry = 同一候选**（BDD-26）；**P5→P4 跨阶段回退 = 机械重新解析一次路由（可能因当时可用性落到不同候选，但无「升档」逻辑）**。P1 未落这条边界，P4 实现 / P6 验收会缺锚点，且 BDD-26 的「不重新解析路由」措辞在无对照 BDD 时易被误读为「任何 retry 都不重解析」。
- 修订方向：新增一条 BDD（编号顺延 BDD-51），Given「P5→P4 回退后 P4 进入 retry」/ When「路由决策层解析该次派发」/ Then「重新机械解析一次 `(phase,role)` 路由（按当时候选可用性）、不注入「上次失败→升档/换更强 model」逻辑；重解析与 BDD-26 的同阶段内 gate-FAIL-同候选-retry 不冲突（前者跨阶段回退、后者同阶段）」。并在 BDD-26 Then 或 §2 边界行补一句注明两种 retry 的边界。

---

## 非阻塞建议（可由主 Agent 判断是否要求 analyst 处理）

- **BDD-35** Then 收尾「结论稳定」措辞略软 —— 建议补明「构造样本的已知正确 verdict = X，解析结论须等于 X」，使 P6 判定粒度更清（当前依赖构造样本已知预期，仍可判定，非阻塞）。
- **BDD-38** 「`N + 余量` 强杀」中「余量」未量化 —— 建议给具体秒数或显式标「P2 定值」。
- **BDD-46** 一条 Then 含 ~6 项子断言 —— 建议拆为 2-3 条子 BDD 提升 P6 逐项 PASS/FAIL 粒度（doc-revision BDD 常见形态，非阻塞）。
- **§3 第 8 行** 标注 `roadmap.md:68` 与 RM-AG0060 实际行号不符（内容确在该行）—— 小瑕，修订时顺手校正行号或改为「RM-AG0060 行」。

---

## 门槛映射

- 打回项非结构性缺失、非「BDD 不完整 / 掺入方案设计 / NEED_CONFIRM 未处理」类根本问题，属可定点修订的判据措辞 + 1 条边界 BDD 缺口 → **needs-revision**（计入 P1 retry 预算，MAX=3）。
- analyst 按「必须修订项 1-2」修改 P1-requirements.md（BDD-31 判据改机制锚定；新增 P5→P4 回退重解析路由 BDD 并补 BDD-26 边界注）后重派 requirements-review 复核。

---

## 复核轮（P1 retry #1）

上轮结论 needs-revision（2 阻塞 + 4 非阻塞）。analyst 已修订，现 **53 条 BDD**（§4.18 新增 BDD-51/52/53）。本轮聚焦 6 项修订 + 编号连续性 + 无新增矛盾。

### 编号连续性

`grep -nE '^#### BDD-[0-9]+:'` → `#### BDD-1:` … `#### BDD-53:` **连续、无跳号**（53 条，§4.18「4.18 P5→P4 回退路由 + design-note 定案重写（拆分补充）」承接 BDD-51/52/53）。`check-frontmatter.py` 见「产出文件字段」后复跑，此处只核 BDD 结构。

### 6 项逐项复核

| 项 | 复核结论 | 依据 |
|---|---|---|
| 阻塞 1 — BDD-31 去漂移版本串 | **修好** | BDD-31 Then（P1-requirements.md:298）现为「`--output-format json` 的 `modelUsage` 字段显示的实际 model，与候选 `model: haiku` 经档位/别名解析后的目标一致，且非父会话继承 model；驱动会话侧无自由裁量」。已无 `claude-haiku-4-5-*` 硬编码 family 版本串；判据锚「`modelUsage` 可核实实际 model」的机制 + 「与别名解析目标一致」的可比对断言，二值可判（modelUsage 值 == 解析目标 → PASS）。保留「驱动会话零判断」子句。符合派发指引 BDD-31/32 专项要求。 |
| 阻塞 2 — 新增 P5→P4 回退 BDD + BDD-26 边界注 + §2 同步 | **修好，张力消除** | ① 新增 **BDD-51**（:412-415）单条 G/W/T：Given「P5→P4 回退发生、P4 进入 retry」/ When「路由决策层解析该次派发」/ Then「重新机械解析一次 `(phase,role)` 路由（按当时候选可用性落候选，可能与回退前不同候选），**不注入**「上次失败→升档/换更强 model」逻辑」。两个断言（是否重解析 / 是否注入升档逻辑）均二值可判。② **BDD-26** 加第 4 bullet「边界区分」（:267）：「本条是同阶段内 gate-FAIL retry = 同一候选；P5→P4 跨阶段回退后的 P4 retry 走「机械重新解析一次路由」，见 BDD-51，两者不冲突」。③ **§2 边界行**（:92）改写为「gate FAIL 后同阶段 retry（同候选，BDD-26）/ P5→P4 跨阶段回退后重新机械解析一次路由（BDD-51）」+「两类 retry 的路由行为须显式区分（同阶段 = 同候选 / 跨阶段回退 = 机械重解析、无升档逻辑）」。**张力核对**：BDD-26 的「不重新解析路由」与 BDD-51 的「重新机械解析一次路由」现已各自显式限定触发条件（同阶段 gate-FAIL vs 跨阶段回退），且互相引用点名「不冲突 + 限定理由」；串行场景（回退→重解析落候选 C→P4 内 gate FAIL→同候选 C retry）不产生矛盾指令。与 P0-brief scope「P5→P4 回退后重新解析一次路由、不做升档逻辑」一致。 |
| 非阻塞 3 — BDD-35 措辞收紧 | **修好** | BDD-35 Then（:320）现含「构造样本的已知正确 verdict = 「该 turn 整体成功」，路由决策层对该样本的解析结论须等于该 verdict（不因两层混淆把整条 `turn.completed` 的 turn 误判为失败、也不因某 item `status:failed` 就换候选）」。给出构造样本的确定预期结论，二值判定粒度清晰；「按 P2 明确取的那一层判定」仍如实留给 P2，未武断锁定。 |
| 非阻塞 4 — BDD-38「余量」量化 | **可接受** | BDD-38 Then（:337）现为「超过 `N + 余量`（余量具体秒数 P2 定值，建议 ≥10s）→ 兜底强杀」。落点交 P2 + 给建议下界，行为分支（超时 → 兜底强杀）二值可判。 |
| 非阻塞 5 — BDD-46 拆条 | **修好** | BDD-46（:382-386）收窄为「配置落点（不再 `agate/rules/`、项目级在 `agate-workspace/`）+ 核心循环（不再「按序探测」、改 try-and-fall）」两断言 + 注指向 52/53。新增 **BDD-52**（:417-420，两轴 + `(phase,role)` key + 弱/强缓解标注 + 自动化不对称）与 **BDD-53**（:422-425，两条完整性不变量 + per-machine 机会式声明），均为独立 G/W/T、判据为 design-note 正文关键串 grep、各自可独立 PASS/FAIL。§9 P6（:498）已改「53 条 BDD（PASS/FAIL 总数 ≥ 53）」。 |
| 非阻塞 6 — §3 第 8 行行号 | **已校正（残留小瑕，非阻塞）** | §3 第 8 行（:112）文件清单改为「`agate-workspace/roadmap/roadmap.md` 的 RM-AG0060 行」，`:68` 已去除。「逐条处理判定」列末尾的 BDD 引用为「BDD-44/47」——roadmap 旧措辞回写实际由 **BDD-47** 承接（BDD-44 现为「自主再派发的子任务不走路由表」，与本行无关）。此为溯源指针小瑕，不影响任何 BDD 的可判定性或覆盖完整性（roadmap 回写需求已被 BDD-47 锚定）；建议主 Agent 提示 analyst 顺手把该引用改为「BDD-46/47」（design-note + roadmap 两处旧措辞）。**不构成 needs-revision 理由**。 |

### 无新增矛盾扫描

- BDD-51 与 BDD-26：张力已消除（见阻塞 2 依据）。
- BDD-52 / BDD-53 与 BDD-46：三者切分互斥、无重叠断言（BDD-46 = 落点 + 核心循环；BDD-52 = 两轴 + key + 缓解标注；BDD-53 = 完整性不变量 + per-machine），与 BDD-41（`dispatch-protocol.md` 新节的两条不变量）为不同文件（design-note vs dispatch-protocol.md），不重复、不冲突。
- BDD-51 与 out-of-scope「retry 故意换/升档模型」：BDD-51 Then 显式「**不注入**升档逻辑」，正面钉死该 out-of-scope，无越界。
- 其余 47 条（BDD-1~50 除 26/31/35/38/46）本轮无改动、无连带影响，上轮判定（全部「通过」，含 6 条「通过·可优化」）继续有效。

### §3 第 6 组结论复核（脚本未改，结论续有效）

`check-judge-verdict.py` / `check-p6-provenance.py` 本轮未被触碰；上轮独立 grep（`\.claude|\.codex|sessions|transcript|rollout|expanduser|HOME` 命中 0、全部访问为 `task_dir` 相对 + `git -C task_dir`）结论继续成立。BDD-42 平台无关性断言前提有效。

---

## 复核轮结论

**approved。**

- **全部 53 条 BDD 均已判定通过**：BDD-1~50（除本轮改动的 26/31/35/38/46）沿用上轮「通过」判定（6 条标「通过·可优化」为非阻塞措辞建议，不影响可判定性）；BDD-26 / 31 / 35 / 38 / 46 本轮复核为「修好」；BDD-51 / 52 / 53 新增，各为单条 G/W/T、判据锚客观信号（路由重解析行为 / design-note 正文关键串 grep）、二值可判。
- **本轮 6 项修订复核通过**：阻塞 1（BDD-31 去漂移版本串、改机制锚定）、阻塞 2（BDD-51 新增 + BDD-26 边界注 + §2 同步，BDD-26↔BDD-51 措辞张力消除）、非阻塞 3~6 均已处理；仅遗留 §3 第 8 行「BDD-44/47」溯源指针小瑕（建议改「BDD-46/47」），非阻塞、不影响覆盖。
- **上轮已通过项持续有效**：隐含需求 5 维度覆盖（前端明确排除成立；边界维度本轮补齐 P5→P4 回退重解析 → BDD-51，缺口关闭）；裁剪评审（phases 全 8 阶段「走」理由逐条成立）；审声明核对（`risk_level: medium` / `ceremony: standard` / `phases: [P1..P8]` / `packages` 四声明与 P0-brief 改动面自洽，`git diff --cached --stat` 证据 = 仅 md/yaml/jsonl、仅任务命名空间内）；DEBT0039 专项五项（§1 SCOPE+ 登记 / §3 第 9 行 architect.md 新增面披露 / BDD-48-50 承接 closure_criteria / §7·§9 阶段边界 / packages 覆盖）全通过；§3 第 6 组「routed-away judge verdict 非真缺口」独立核实成立；P1 纯净性（§5 六条均 `[SUGGEST:]`、无 `[NEED_CONFIRM]`、无破坏性/业务方向决策）；范围核对无越界（SCOPE+ DEBT0039 如实登记）。
- Header `status:` → `approved`（`agate-md-field-set status approved`，agent = requirements-review ≠ main）。
