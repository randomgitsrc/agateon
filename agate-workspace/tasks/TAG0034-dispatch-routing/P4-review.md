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

status 结论：**approved**（agent = review，非 main）。
