---
phase: P4
task_id: TAG0034
type: review
parent: P4-implementation.md
trace_id: TAG0034-P4-20260909
status: approved
created: 2026-09-09
agent: review
implementation_dir: agate/
---

# TAG0034 P4a 实现评审（review — 偏执 Staff Engineer 视角）

评审对象：TAG0034 派发路由 **P4a 批**实现代码
- 新增：`agate/rules/dispatch-tiers.yaml`、`agate/scripts/check-dispatch-routing.py`、`agate/scripts/agate_dispatch_route.py`、`agate-workspace/dispatch-routing.yaml`
- 修改：`agate/scripts/agate-dispatch.py`（`route` 分支）、`agate/scripts/check-events.py`（第 8 条）、`agate/dispatch-protocol.md`、`agate/assets/execution-roles/architect.md`、`agate/platform-notes.md`、`docs/design-notes/design-dispatch-routing.md`、`agate-workspace/roadmap/roadmap.md`

评审依据：`P4-dispatch-context-review.md`（强制指令）、`P2-design.md` §3.3/§3.6/§3.7/§3.8 + N6/N7、`P2-review.md` 8 条锁定决策 + T1/T2/T3、`P0-brief.md` known_risks（模型购物完整性洞 R1 最高危）、`AGENTS.md`、`agate/assets/review-roles/review.md`。

结论：**approved**。CRITICAL = 0；BLOCKER = 0。INFORMATIONAL（Pass 2）6 条，均属 P4b 落地边界提醒 / 防御性加固建议，不构成返工、不阻断 P4a 推进。

`[PROD_NOT_TOUCHED]` — 本次评审仅在 worktree `.worktrees/agate-TAG0034` 内读；写入仅 `P4-review.md` + `P4-progress.md`（任务目录内）。主 checkout / `~/.agate` 未触碰。

---

## Pass 1（CRITICAL）— 数据安全与正确性

### R1 模型购物完整性洞（首要审查项）— 三处闭合，全部通过

**① `classify_outcome` / `Outcome.kind` 枚举无 `GATE_FAIL`** — PASS
- 锚点：`agate/scripts/agate_dispatch_route.py:268-300`。`classify_outcome` 全部返回路径只产出
  `Outcome("LAUNCH_FAIL","launch_fail")` / `Outcome("INFRA_ERROR","infra_error")` /
  `Outcome("HAS_OUTPUT",None)` / `Outcome("NO_PARSEABLE_OUTPUT","no_parseable_output")`。
  无 `GATE_FAIL` 取值；`.reason` 只可能是 `launch_fail` / `infra_error` / `no_parseable_output` / `None`。
- `agate/scripts/agate_dispatch_route.py:43` `GATE_FAIL_TRIGGERS_FALLBACK = False` 常量在位。
- `HAS_OUTPUT` 判据（`:296-297`）= `files = [f for f in (produced_files or []) if f]` 非空即返回，
  **presence 级**，无 frontmatter 解析、无锚点标题校验、无内容完整度 / BDD 覆盖度判断。
- `NO_PARSEABLE_OUTPUT` 分支（`:300`）仅在「无 killed_reason + 无基础设施签名 + 非（非零退出且无产出）+ `not files`」时到达，
  **未掺入任何结构完整度校验**（N7 定死点满足；未把结构完整度塞进 `NO_PARSEABLE_OUTPUT` → 不触发 dispatch_context 的 CRITICAL 条件）。

**② `try_and_fall` 回落只在三类基础设施信号** — PASS（附 I1 加固建议）
- 锚点：`agate/scripts/agate_dispatch_route.py:394-416`。循环体：`kind == "HAS_OUTPUT"` → 记 success、写事件、`return`（停止回落）；
  否则记 failed（`reason = getattr(outcome, "reason", None)`）、`continue`。
- 因 ①（`classify_outcome` 枚举闭合），「非 HAS_OUTPUT」= 恰好三类基础设施信号，回落边界成立。
- 产出质量差 / 内容不完整 → `HAS_OUTPUT`（`return`，交 gate、不回落）：`test_bdd_24` / `test_bdd_25` / `test_bdd_26` 断言与实现真对应，已复跑绿。

**③ `check-events.py` 第 8 条拒 `gate_fail`** — PASS
- 锚点：`agate/scripts/check-events.py:119-134`（`git diff` 复核）。对 `ev.get("event") == "dispatch_route"` 的行，
  遍历 `candidates_tried[]`，`reason is not None and reason not in DISPATCH_ROUTE_REASONS` → `sys.exit(1)`。
- `DISPATCH_ROUTE_REASONS = {"launch_fail","infra_error","no_parseable_output"}`（`:44`）——无 `gate_fail`、无第四值。
- 该块**追加**在逐行循环内（block 6 之后、循环结束前），`idx` 在作用域内；第 1-7 条 + 哈希链算法
  （`sha256(上一行原始文本)` / GENESIS / ts 单调 / judge 计数）逐行核对**未改动**。docstring 第 7 条注释补 `dispatch_route`、追加第 8 条说明。
- `test_bdd_27` / `test_t3`（三值 exit 0 + `gate_fail` exit 1）复跑绿；`check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0（12 行哈希链完整）。

**R1 结论：三处口子全部闭合，无 CRITICAL。** 另注：P4a `_route_main` 只做 resolve + 输出路由计划 JSON
（`agate-dispatch.py` diff `_route_main:164-238`），P4a 无 `dispatch_once`、无子进程派发、无回落循环运行
→ R1 在 P4a 天然不可触发，闭合为结构性 / 潜伏正确，P4b 落地 try-and-fall 循环时须复验（见 I1/I2）。
`[DESIGN_GAP_REVIEWED: 已确认]` 与 P2-design §4.1 批次意图一致，无 P2 偏离。

### 枚举一致性（Pass 1）— 通过

- `reason` 三值：`agate_dispatch_route._VALID_REASONS`（`:45`）== `check-events.DISPATCH_ROUTE_REASONS`（`:44`）
  == `check-dispatch-routing` 无独立 reason 校验（非其职责）。三处一致，无一处多 `gate_fail` / 缺值。
- `cli` 四值：`check-dispatch-routing.VALID_CLI = {native, claude-code, codex, opencode}`（`:32`）；
  `build_dispatch_command`（`agate_dispatch_route.py:320-358`）分支恰好覆盖 `codex` / `opencode` / `claude-code`+`native`
  三组、无遗漏 `native`、无多余枚举。
- `effort` 三值：`check-dispatch-routing.VALID_EFFORT = {low, medium, high}`（`:33`）；`agate_dispatch_route`
  运行时不重复 effort 枚举校验（schema 校验器职责），无 `xhigh` 混入。
- tier 白名单：`dispatch-tiers.yaml` `tiers: {bulk, standard, deep}` == `check-dispatch-routing._load_tier_names()`
  交叉核来源 == `agate_dispatch_route.load_factory_defaults` 内建兜底 `{bulk, standard, deep}`。一致。

### resolve 算法正确性（§3.3 / P2-review 决策 2）— 通过

- 优先级序（`agate_dispatch_route.py:111-160`）：`candidates`（优先级 1）→ `tier`（优先级 2）→
  `factory_defaults.get("Pn.role") or .get("Pn") or "standard"`（优先级 4）；machine_routes（优先级 3）MVP 不实现，与 §3.3 一致。
- `(phase,role)` 命中优先于 `phase`：`_lookup_route_entry`（`:86-104`）先查点分 `Pn.role`、再查嵌套 `routes[Pn][role]`、
  末查 `routes[Pn]` phase 级 spec。`test_bdd_11` / `test_bdd_12` 断言与实现真对应，复跑绿。
- `standard` 短路（`:137-138`）：`if tier == "standard": return _default_result(current_model)` —— 不经 `tier_bindings` 展开、
  `chain=None` / `model=current_model` / `effort=None`。「不配置 = 逐字节现状」不变量锚成立（`test_bdd_13/14/40`）。
- tier 引用但 `tier_bindings` 缺该 tier（`:140-144`）：回落 `_default_result`（`form='default'`，机会式），与 §3.3 step 3 一致。
- effort 合并（`:150-156`）：`merged = dict(cand); merged["effort"] = merged.get("effort") or effort_override` ——
  候选自带优先、否则 route 层。**`dict(cand)` 浅拷贝后再改，不 mutate 调用方 `tier_bindings` / `routes`**；
  `_default_result` 返回新 dict 字面量；`chain = []` 新列表；`raw_chain` 仅迭代不改。同输入多次 `resolve` 恒等（`test_t1`）。
- T1（N2）返回契约：每条返回路径键集恒为 `{form, chain, model, effort}`、`form ∈ {default, chain}`、
  `form=='default'` → `chain is None`。逐条 return 路径核对满足（`test_t1` 复跑绿）。

### 全兜底加载器 `load_config`（BDD-16/17）— 通过

- 逐字对照 `agate/scripts/check-maintainability.py:_load_config`（88-148 行）：
  文件 / 目录不存在 → `({}, {})`（`agate_dispatch_route.py:183-185`）；`import yaml` 失败 → `({}, {})` + stderr（`:176-181`）；
  解析失败 → `({}, {})` + stderr WARNING（`:187-194`）；非 dict → `({}, {})`（`:196-197`，与参照一致，静默）；
  某键类型坏（`routes:` 写成 list）→ 该键默认 `{}` + stderr WARNING、不抛异常、不静默跳过整段（`:199-214`）。
  形态与参照 `_load_config` 逐档一致。
- `load_factory_defaults`（`:218-245`）：`agate/rules/dispatch-tiers.yaml` 缺失 / 损坏 / 非 dict → 内建
  `({"bulk","standard","deep"}, {})`，全兜底。

### build_dispatch_command effort 映射（BDD-8/9/10/31/32）— 通过

- 锚点 `agate_dispatch_route.py:306-358`。Codex → `-c model_reasoning_effort=<e>`（`:327-328`）；
  OpenCode → `--variant <e>`（`:336-337`）；Claude Code / native → `if effort and effort_supported: cmd += ["--effort", str(effort)]`（`:348-349`），
  `effort_supported` **为调用方传入的参数**、函数内部无能力探测、无版本号硬编码（`grep -nE "2\.1\.|0\.15|1\.18" ` 两新脚本 = 无命中）。
- `model is None → 不传 --model`：每分支 `if model is not None`（`:325 / :335 / :346`）。
- `test_bdd_10` supported / absent 两分支断言与实现真对应，复跑绿。
- `platform-notes.md` diff：新增「推理档（effort）」行，版本号以 `[实测]` 观测记录出现 + 明文「不硬编码版本号」+ 能力探测措辞
  —— 属文档如实登记，非代码硬编码，`test_bdd_10_platform_notes_records_effort_probe` 三关键词命中。

### write_dispatch_route_event（BDD-28/29）— 通过

- 锚点 `agate_dispatch_route.py:422-437`。`from agate_common import append_event` → 复用既有哈希链
  （`prev_hash = sha256(上一行原始文本)` / `ts` 既有逻辑填），**不自造哈希链**。
- 事件体 `{"event":"dispatch_route","phase","candidates_tried","final"[, "task_id"]}` 与 `gate_run` / `judge_verdict` / `state_transition` 同构。
- **不写 `state_transition`、不动 `retries`、不触发 PAUSED**（函数体只 `append_event` 一次）。`test_bdd_29` 复跑绿。

---

## 回归硬约束 diff 核（BDD-39/40）— 通过

`git diff HEAD` 逐文件核：
- **零改动确认**：`agate/rules/phases.yaml` / `agate/scripts/check-gate.py` / `agate/scripts/check-state-transition.py` /
  `agate/state-machine.md` / `agate/scripts/check-judge-verdict.py` / `agate/scripts/check-p6-provenance.py` /
  `agate/scripts/agate-cmdstream-adapters.py` —— `git diff --stat` 空输出，逐字节未改。
- `agate-dispatch.py`：diff 只有两处 —— `main()` 顶部新增 `if args and args[0] == "route": _route_main(args[1:]); return`
  三行（在 `len(args) < 2` 与 `_PHASES` 校验之前）+ 新增 `_route_main` 函数。
  `_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER`（CARD-SOURCE）/ `generated_by` 逐行未触碰。
  `re` / `os` / `sys` 模块级已 import、`_resolve_agate_root` 已定义，`_route_main` 引用无 NameError 风险。
- `check-events.py`：diff 只有第 8 条追加块 + docstring 两处补注（见 R1 ③）。
- 零改动仍绿：`test_check_events.py` + `test_tag0027_b2_agate_dispatch.py` + `test_tag0027_b2_audit2_dual_anchor.py` = 23 passed（复跑）。
- `test_tag0034_zero_change.py`（BDD-39 字节基线 + BDD-40 无配置 = 现状）= 2 passed（复跑）。
- `pytest -k tag0034` = 57 passed / 3 failed；3 红 = `test_bdd_42`（P4b routed_away_verdict）+ `test_bdd_37/38`（P4c tmux），
  与批次边界一一对应，符合预期。

---

## 循环导入 / 副作用核 — 通过（附 I6）

- `agate-dispatch.py` 在 `_route_main` 内 lazy `import agate_dispatch_route`；后者不反向 import `agate-dispatch`
  （只 `os` / `sys` + lazy `yaml` + lazy `from agate_common import append_event`）。无循环导入。
- `agate_dispatch_route.py:38-40` import 时 `sys.path.insert(0, _HERE)` —— 与仓库既有脚本模式一致，副作用轻微（见 I6）。

---

## Pass 2（INFORMATIONAL）— 代码健康（不阻断，供 P4b / 主 Agent）

### I1 — `try_and_fall` 用黑名单逻辑而非设计的白名单
- 定位：`agate/scripts/agate_dispatch_route.py:404-413`。实现是「`if kind == "HAS_OUTPUT"` → 成功；else → 回落」；
  P2-design §3.7 伪代码是显式白名单「`if kind == LAUNCH_FAIL / INFRA_ERROR / NO_PARSEABLE_OUTPUT` → `continue`」。
- 影响：今日安全（`classify_outcome` 枚举闭合，「非 HAS_OUTPUT」恒等于三类基础设施信号）。但 P4b 的
  `dispatch_once` 若返回不符合契约的 outcome（如未来误加 `kind`），当前结构会**静默当作回落信号**换候选。
- Fix 方向（P4b）：`try_and_fall` 回落分支显式判 `kind in {"LAUNCH_FAIL","INFRA_ERROR","NO_PARSEABLE_OUTPUT"}`，
  其它「非 HAS_OUTPUT」kind → `raise`（契约违例大声失败），而非落入 `continue`。

### I2 — N7 的 presence 级「frontmatter 可解析 + 必需锚点标题存在」在 P4a 未落地
- 定位：`agate/scripts/agate_dispatch_route.py:296`。`classify_outcome` 对 `produced_files` 仅做 truthy 判空，
  未做 frontmatter / 锚点标题解析（该判据 P2-design §3.7 N7 定义在 `HAS_OUTPUT` 侧）。
- 影响：P4a 无害（`produced_files` 由调用方喂、子进程解析归 P4b/M5）；但方向必须钉死。
- Fix 方向（P4b review 关注项）：presence-parse 落在 `produced_files` 填充处（P4b spawn 侧），
  **禁止**在 `NO_PARSEABLE_OUTPUT` 分支引入结构完整度判断（否则即 R1 CRITICAL）。

### I3 — `write_event` 回调 与 `write_dispatch_route_event` 签名缝
- 定位：`try_and_fall` 内注入回调按 `write_event(phase, tried, final)` 位置参数调用（`:408 / :415`）；
  独立写入器 `write_dispatch_route_event(task_dir, phase, *, tried, final, task_id=None)` 为 kw-only（`:422`）。
- 影响：P4a 两者未接线（DESIGN_GAP，`_route_main` 不跑端到端）。P4b 集成 `_route_main` 时须写适配层桥接位置↔kw 参数。
- Fix 方向（P4b）：在 `_route_main` 端到端分支里显式适配，或统一两处签名。

### I4 — `check-dispatch-routing.py` 对畸形混合条目 / 孤立 effort 宽松
- 定位：`agate/scripts/check-dispatch-routing.py:146-152`。`{P4: {tier: bulk, review: {...}}}` 这类「phase 级 spec
  同时带 role 子键」→ 命中 `_ROUTE_SPEC_KEYS` 走 phase 级校验、`review` 子键被静默忽略；
  仅含 `effort:`（无 tier/candidates）的 route 层条目校验器不拒、`resolve` 静默丢弃（`:117-135`，与 §3.3 伪代码一致）。
- 影响：低。均非 P2 schema 契约内的合法形态；不产生错误路由，只是少一层防呆。
- Fix 方向（可选）：混合条目 / 孤立 `effort:` 出 WARNING。

### I5 — `_VALID_REASONS` 常量在模块内未被引用
- 定位：`agate/scripts/agate_dispatch_route.py:45`。定义了 `_VALID_REASONS`，但校验实际发生在
  `check-events.py:DISPATCH_ROUTE_REASONS`；模块内 `try_and_fall` 未用它自校。
- 影响：无（两处值一致，无漂移）。属轻微冗余 / 意图不清。
- Fix 方向（可选）：要么 `try_and_fall` 写事件前用它自校 `reason`，要么删除 / 改注释为「对外契约常量」。

### I6 — 模块 import 时 `sys.path` 变更副作用
- 定位：`agate/scripts/agate_dispatch_route.py:38-40`（import 时 `sys.path.insert(0, _HERE)`）。
- 影响：与仓库既有脚本一致，通常无害；但 helper 被其它进程 import 时会改其 `sys.path`。
- Fix 方向（可选）：把 path 注入收进 `if __name__ == "__main__"` 或函数内（本模块无 `__main__`，可移到首次需要处）。

---

## 门槛项核对

- RM-AG0046 checklist：`python3 agate/scripts/check-maintainability.py agate-workspace/tasks/TAG0034-dispatch-routing`
  → exit 0，`god_file_count: 0` / `fuzzy_boundary_count: 0`（violations 为空）。无需 `known-violations.md`（该文件当前不存在，符合预期）。
- 抽查测试真对应（非实现骗断言）：`test_bdd_19`（首个动作即真实 ctx、无 probe）、`test_bdd_25`（HAS_OUTPUT 即停、不试后续候选）、
  `test_bdd_28`（回落 2 次后第 3 候选成功，只 1 条 dispatch_route 事件、`reason` 序列正确）—— 三条断言逐行对照实现，均为真实语义校验、非表面绕过。
- ruff（`~/.venvs/agate-dev/bin/ruff check` 四脚本）→ All checks passed。
- `check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` → exit 0。
- 技术债：本评审未提「后续应重构 / 架构债」类结论，无需 DEBT 条目。

---

## 修复回派建议

I1~I6 均为 INFORMATIONAL，不构成 P4a 返工。建议：
- I1 / I2 / I3 → 写入 P4b 的 implementer dispatch-context「约束」节（P4b 落 try-and-fall 循环 + subprocess 时必须处理），并作为 P4b review 的重点核查项。
- I4 / I5 / I6 → 可选清理，主 Agent 择机（不阻断本任务）。

status 结论（P4a 单批）：**approved**（agent = review，非 main）。

---

## P4b 批评审（review — 偏执 Staff Engineer 视角，2026-09-10）

评审对象：TAG0034 派发路由 **P4b 批**（依赖 P4a，已 commit `d1c2aca`）
- 修改：`agate/scripts/agate_dispatch_route.py`（M5 `dispatch_once` / `presence_parse_ok` / `_default_subprocess_run` / `routed_away_verdict_location` / `DispatchContractError` / 常量 `_FALLBACK_KINDS` `_SUBPROCESS_CLIS` + `try_and_fall` I1 白名单 + I5 reason 自校）、`agate/scripts/agate-dispatch.py`（`_route_main` `form=="chain"` 拆三路 + I3 适配层闭包）、`agate/SETUP.md`（M9）、`agate/platform-notes.md`（M10 结构化输出字段小节）、`agate/dispatch-protocol.md`（评审打回续跑段）
- 新增：`agate/tests/unit/test_tag0034_p4b.py`（15 例）

评审依据：coordinator P4b dispatch message（强制指令）、`P4-implementation-P4b.md` + 2 条 `[DESIGN_GAP_REVIEWED]`、`P2-design.md` §3.1/§3.4/§3.7 + N6/N7、`P0-brief.md` known_risks R1、`P4-review.md` P4a 节 I1~I6。

结论（P4b 单批）：**approved**。CRITICAL = 0；BLOCKER = 0。P4a 提出的 I1/I2/I3/I5 四项均已按方向落地并复核闭合；INFORMATIONAL 3 条新增（P4b-I1~I3）+ 2 条 P4a 遗留（I4/I6，implementer 以批次边界理由暂缓，理由成立），均不阻断。

`[PROD_NOT_TOUCHED]` — 仅 worktree 内读；写入仅 `P4-review.md` + `P4-progress.md`。

## Pass 1（CRITICAL）— R1 + 回归（P4b 首要项）

### 1. I1 白名单落地 — 真闭合 R1 稳健性缺口，PASS
- 锚点：`agate/scripts/agate_dispatch_route.py` `try_and_fall`（diff `+551~+575` 区）。
  `kind = getattr(outcome, "kind", None)` → `kind == "HAS_OUTPUT"` → 停、写事件、`return`；
  `kind not in _FALLBACK_KINDS`（`frozenset({"LAUNCH_FAIL","INFRA_ERROR","NO_PARSEABLE_OUTPUT"})`，**含 `None` / 未来误加枚举**）→ `raise DispatchContractError`；
  仅当 `kind` 在三类白名单内才继续到回落记录。
- 即回落分支现是**显式白名单** `kind in {LAUNCH_FAIL, INFRA_ERROR, NO_PARSEABLE_OUTPUT}` 才 `continue`；
  其它「非 HAS_OUTPUT」→ 大声失败而非静默换候选。P4a-review I1 的方向逐字落地。
- I5 叠加：`reason not in _VALID_REASONS`（`("launch_fail","infra_error","no_parseable_output")`，无 `gate_fail`）→ 写事件前 `raise DispatchContractError`。
  与 `check-events.py` 第 8 条（持久审计层）形成双层强制。
- 测试真对应：`test_try_and_fall_raises_on_non_contract_kind`（`Outcome("SURPRISE_KIND","weird")` → raise）/
  `test_try_and_fall_raises_on_none_kind`（无 `.kind` 对象 → raise）/ `test_try_and_fall_i5_raises_on_bad_reason_for_fallback_kind`（`Outcome("INFRA_ERROR","gate_fail")` → raise）/
  `test_try_and_fall_whitelist_still_falls_back_on_three_infra_kinds`（三类仍正常回落、不误伤）。复跑绿。

### 2. I2 边界守住 — R1 CRITICAL 未破，PASS
- `presence_parse_ok(path, *, required_anchors=None)`（新函数，`+414~+438`）：文件存在且非空 +
  frontmatter（若有 `---\n` 前缀）须闭合且至少一行 `key: value` + `required_anchors` 全部出现。
  **不含**内容完整度 / BDD 覆盖度 / 质量判断。
- 该判据**只**在 `dispatch_once`（`+467~+474`）填 `produced_files` 处调用：
  `if expected_output and presence_parse_ok(...): produced_files = [expected_output]` → 再交 `classify_outcome`。
- **`classify_outcome` 逐字节未改**（`git diff --stat` 空 + 逐行核 `:299-333`）：`NO_PARSEABLE_OUTPUT` 分支仍是
  「无 killed_reason + 无基础设施签名 + 非（非零退出且无产出）+ `not files`」→ `return`，**未引入任何结构 / 内容完整度判断**。
- R1 CRITICAL 边界锁死：`test_classify_outcome_no_parseable_branch_has_no_structure_check` —— `produced_files=["junk-but-nonempty.md"]` + 垃圾非结构化 stdout → `HAS_OUTPUT`（交 gate、不回落）。
  「垃圾但非空产出 → HAS_OUTPUT」成立，未把结构完整度塞进 `NO_PARSEABLE_OUTPUT` → **不触发 CRITICAL**。
- `test_dispatch_once_i2_empty_produced_file_is_no_parseable_output`：空产出文件 → `presence_parse_ok` False → `produced_files` 空 → `NO_PARSEABLE_OUTPUT`，结构判断落在填充侧、不在 `classify_outcome`。复跑绿。

### 3. 回归 diff 逐文件核 — 零改动，PASS
- `git diff --stat HEAD` 对 `agate/rules/phases.yaml` / `check-gate.py` / `check-state-transition.py` /
  `agate/state-machine.md` / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py`（第 1-8 条 + 哈希链）/
  `check-dispatch-routing.py` / `agate-cmdstream-adapters.py` / `agate/rules/dispatch-tiers.yaml` —— **空输出，逐字节未改**。
- `agate-dispatch.py`：`git diff` 两个 hunk 均在 `_route_main`（`@@ -167` / `@@ -213`）内；`_render_dispatch_context` /
  `_next_card_content` / `_SOURCE_MARKER` / `generated_by` / `main()` 分派 + `form == "default"` 分支逐字节未触碰。
  `form == "chain"` 原 `else` 拆为 `elif 首候选 native`（输出路由计划 JSON，行为同 P4a）/ `else 子进程端到端`。
- `check-events.py` 第 8 条（P4a 落）本批未再动。
- BDD-42 依赖：`test_bdd_42` 断言 `check-judge-verdict.py` / `check-p6-provenance.py` 源码不含 `.codex/sessions` / `.claude/projects`
  —— 两脚本零改动，断言成立；`routed_away_verdict_location(cli)` 恒 `"TASK_DIR"`（`+485~+496`），judge 子进程 verdict + 证据仍落 TASK_DIR、两校验器纯 TASK_DIR 文件解析。
- 回归复跑：`test_tag0034_zero_change.py` + `test_check_events.py` + `test_tag0027_b2_*` = 25 passed。

### 4. `_default_subprocess_run` 子进程健康 — PASS（附 P4b-I1）
- `+441~+463`：`subprocess.run([str(a) for a in argv], capture_output=True, text=True, encoding="utf-8",
  errors="replace", timeout=timeout_s)`；`timeout_s` 缺省 `float(os.environ.get("AGATE_DISPATCH_TIMEOUT_S","1800"))`
  带 `ValueError` 兜底 —— **宽超时兜底 1800s、可配、未自造紧超时**。
- `except (FileNotFoundError, OSError) → ("", None, "spawn_oserror")` → `classify_outcome` 归 `LAUNCH_FAIL`（`_LAUNCH_KILLED` 含 `spawn_oserror`）。
- `except subprocess.TimeoutExpired → (exc.stdout or "", None, "wait_timeout")` → `classify_outcome` 归 `INFRA_ERROR`（N6：非 `_LAUNCH_KILLED` 的非空 killed_reason）。
- **未改 `agate-cmdstream-adapters.py`**（零 diff）；tmux 包裹 + RM-AG0055 命令流阈值卡死检测的接入点以注释标出、归 P4c。
- 测试：`test_dispatch_once_spawn_oserror_launch_fail` / `test_dispatch_once_wait_timeout_infra_error` 复跑绿。

### 5. 两条 `[DESIGN_GAP]` — 未在端到端路径引入模型购物口子，PASS
- **GAP #1（`expected_output` 走 `AGATE_DISPATCH_EXPECT` env、未设则保守回落）**：`expected_output is None` → `produced_files` 恒空 →
  即便结构化输出成功也判 `NO_PARSEABLE_OUTPUT` 回落。核：这是「无法核实产出 → 保守回落」，理由码 `no_parseable_output`（合法三值之一）；
  回落链耗尽终点恒为 `{"cli":"default"}`（当前 model 原生派发），**不是「试到某候选过 gate 就停在那」**。R1 的「换模型试到出 green」需要「产出被 gate 评过但不喜欢 → 换候选」——此路径一旦任一候选产出可核实的非空文件即 `HAS_OUTPUT` 停止回落，无该口子。方向属 R1 保守侧。
- **GAP #2（中段 native 候选 → `HAS_OUTPUT` 占位）**：`dispatch_once` 对 `cli not in _SUBPROCESS_CLIS`（含 native）返回 `Outcome("HAS_OUTPUT", None)` →
  `try_and_fall` 视为该候选成功、停止回落、交回驱动会话代发。核：native 派发由驱动会话执行、非路由脚本可判失败之物；
  且该「成功」**与 gate verdict 无关**（不是「gate 过了才算」），不构成购物。与 `dispatch-protocol.md` 新节「cli: native 自动化天花板 = 主 Agent 机械横传 model」一致。
- 两条均 `[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）]`，与 P2-design §3.4 意图一致，无 P2 偏离。本评审复核同意。

### 6. 抽查测试真对应（非实现骗断言）— PASS
- `test_dispatch_once_codex_turn_completed_with_produced_file_has_output`：真写含 `## 改动清单` 锚点的 fixture 文件 + 注入 `turn_completed_ok.jsonl` mock stdout →
  逐步走 `presence_parse_ok`（frontmatter 闭合 + 锚点命中 → True）→ `produced_files` 非空 → `classify_outcome` step 3 → `HAS_OUTPUT`。断言与实现路径逐行吻合。
- `test_dispatch_once_i2_empty_produced_file_is_no_parseable_output`：空文件 → `presence_parse_ok` 于 `not text.strip()` 返 False → `produced_files=[]` → `classify_outcome` step 4 → `NO_PARSEABLE_OUTPUT`。真实语义校验。
- `test_i3_write_event_adapter_bridges_positional_to_kwonly`：测试内 `_write_event(phase_, tried_, final_)` 位置闭包桥接到 kw-only `write_dispatch_route_event`，
  **结构与 `_route_main` 生产代码内的 `_write_event` 闭包同构**；断言「一次回落落 1 条合法 `dispatch_route` 事件、`final` / `reason` 正确」。非绕过。

## Pass 2（INFORMATIONAL）— P4b 新增（不阻断）

### P4b-I1 — `_default_subprocess_run` 丢弃 stderr
- 定位：`agate/scripts/agate_dispatch_route.py:_default_subprocess_run`。`capture_output=True` 捕获 stderr 但只回传 `proc.stdout`。
- 影响：只往 stderr 打印的基础设施错误（部分 auth / 网络失败）不会命中 `_INFRA_SIGNALS`（仅扫 stdout）。
  由 `classify_outcome` 的「非零退出 + 无产出 + 无成功签名 → INFRA_ERROR」兜底，但丢失诊断信息。
- Fix 方向（P4c / 后续）：把捕获的 stderr 并入 `_INFRA_SIGNALS` 扫描文本，或至少透传到路由脚本 stderr 供人排查。

### P4b-I2 — `except (FileNotFoundError, OSError)` 冗余
- 定位：同函数。`FileNotFoundError` 是 `OSError` 子类，二者并列冗余。纯风格，可留可简化。

### P4b-I3 — `_route_main` 子进程端到端路径无 CI 覆盖
- 定位：`agate/scripts/agate-dispatch.py:_route_main` 的 `else`（子进程端到端）分支。CI 无 `dispatch-routing.yaml` → 恒走 `form=default`，
  该分支（`functools.partial` 绑 kwargs + I3 适配层闭包 + `try_and_fall` + `DispatchContractError` → exit 1）不被执行。
  当前仅 `test_i3_*` 在 `try_and_fall` 单元层覆盖桥接逻辑，未经 `_route_main`。
- 影响：与 `[DESIGN_GAP_REVIEWED]`「CI 不真跑端到端、人工真机复核」一致，非阻断；但适配层接线（partial + 闭包 + exit 码）零自动化回归。
- Fix 方向（P4c / P5）：加一条集成用例——构造含子进程候选链的临时 `dispatch-routing.yaml` + 注入 mock `run`（DI seam）+ 设 `AGATE_DISPATCH_EXPECT`，冒烟 `_route_main` 子进程分支的 JSON 输出与 `dispatch_route` 事件。

### P4a 遗留 I4 / I6 — implementer 以批次边界理由暂缓，理由成立
- I4（`check-dispatch-routing.py` 对畸形混合条目 / 孤立 `effort:` 宽松）：改它属 P4a schema 层、跨批改同文件违反 §4.1 批次边界。低影响、非合法形态、不产生错误路由。留主 Agent 择机 / 后续任务。
- I6（`agate_dispatch_route.py` import 时 `sys.path.insert`）：收窄属跨模块风格改动、与 P4b 目标无关，且 `_route_main` 依赖该 import 路径。维持与既有脚本一致。
- 本评审同意两项暂缓，不计入 P4b 返工。

## 门槛复跑（P4b）

- `python3 -m pytest agate/tests/ -k tag0034 -q` → **73 passed / 2 failed**；2 红 = `test_bdd_37` / `test_bdd_38`（P4c tmux `build_subprocess_launch` / `tmux_cleanup_action` 未实现），符合批次边界。
- `check-protocol-consistency.py --strict-errors-only` → exit 0。
- `check-maintainability.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0，`god_file_count: 0` / `fuzzy_boundary_count: 0`（violations 空，无需 `known-violations.md`）。
- `check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（14 行哈希链完整）。
- `check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` → exit 0（未改校验器 / scaffold）。
- 回归：`test_tag0034_zero_change.py` + `test_check_events.py` + `test_tag0027_b2_*` = 25 passed。
- `ruff check`（`agate_dispatch_route.py` + `agate-dispatch.py` + `test_tag0034_p4b.py`）→ All checks passed。
- 技术债：本评审未提「后续应重构 / 架构债」类结论，无需 DEBT 条目。

## 修复回派建议（P4b）

P4b-I1 / P4b-I3 → 写入 P4c 的 implementer dispatch-context「约束」节（P4c 落 tmux 包裹层时一并处理 stderr 透传 + 加 `_route_main` 子进程分支集成用例）。
P4b-I2 / I4 / I6 → 可选清理，主 Agent 择机，不阻断本任务。

---

## 合并结论（P4a + P4b）

- P4a：approved（CRITICAL 0）。P4b：approved（CRITICAL 0，且已闭合 P4a 的 I1/I2/I3/I5）。
- R1 模型购物完整性洞三处闭合在 P4b 端到端路径下仍成立并经 I1 白名单 + I5 双层强制加固；
  回归硬约束全部冻结文件逐字节零改动；两条 `[DESIGN_GAP_REVIEWED]` 未引入购物口子。
- **合并 status：approved**（`agent` = review，非 main）。
- 未决 INFORMATIONAL：P4b-I1/I2/I3 + P4a 遗留 I4/I6，全部非阻断、转 P4c / 主 Agent 择机。
