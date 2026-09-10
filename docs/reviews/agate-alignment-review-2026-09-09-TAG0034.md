---
review_date: 2026-09-09
reviewer: protocol-alignment-review
change_summary: TAG0034 P4a+P4b 批——P4a：派发路由 schema 层 + 引擎骨架 + 协议正文。P4b：M5 端到端子进程 spawn（dispatch_once / _default_subprocess_run / presence_parse_ok / _route_main 端到端 try-and-fall）+ I1 白名单化（DispatchContractError）+ I2 presence-parse 落 produced_files 侧 + I5 reason 自校 + BDD-42（routed_away_verdict_location）+ M9（SETUP scaffold 小节）+ M10（platform-notes 跨 CLI 结构化输出判成败字段小节）+ dispatch-protocol.md 评审打回续跑段。
files_changed:
  - agate/rules/dispatch-tiers.yaml (P4a 新)
  - agate/scripts/check-dispatch-routing.py (P4a 新)
  - agate/scripts/agate_dispatch_route.py (P4a 新；P4b 加 dispatch_once/presence_parse_ok/_default_subprocess_run/routed_away_verdict_location/DispatchContractError/_FALLBACK_KINDS/_SUBPROCESS_CLIS + try_and_fall I1/I5；P4b A1 fix：classify_outcome 基础设施信号按 cli 细分（_BARE_TOP_ERROR_SIGNALS 仅 codex / _INFRA_SIGNALS_CLAUDE_ONLY + _claude_api_error 仅 claude-code / 分支 2b opencode 裸 error → NO_PARSEABLE_OUTPUT）；P4c 加 tmux 观测层 build_subprocess_launch/tmux_cleanup_action 纯逻辑 helper + _maybe_tmux_wrap/_tmux_teardown/_tmux_collect + _default_subprocess_run tmux 分支（feature flag AGATE_DISPATCH_TMUX 默认关）+ P4b-review I1 stderr 透传 / I2 except OSError 收敛)
  - agate/tests/unit/test_tag0034_p4c.py (P4c 新，12 例 —— build_subprocess_launch/tmux_cleanup_action 边界 + _maybe_tmux_wrap 默认关 + P4b-I1/I2/I3)
  - agate/scripts/agate-dispatch.py (P4a route 子命令骨架；P4b _route_main form==chain 端到端 try-and-fall + I3 适配层闭包)
  - agate/scripts/check-events.py (P4a 第 8 条审计链 + DISPATCH_ROUTE_REASONS；P4b 零改动)
  - agate/scripts/check-protocol-consistency.py (P4a 复审轮：SCRIPT_ALIGNMENT_ANCHORS 补 check-dispatch-routing.py 锚点条目)
  - agate/dispatch-protocol.md (P4a「### 0. 派发路由」新子节 + DEBT0039 措辞②；P4b 评审打回续跑段 + `> 实现注记：` 平台续接原语块；P4c「tmux 观测层（可选，仅子进程形式）」小段)
  - agate/assets/execution-roles/architect.md (P4a DEBT0039 措辞①)
  - agate/platform-notes.md (P4a effort 能力探测行；P4b「## 跨 CLI 子进程结构化输出判成败字段」小节 + routed-away judge verdict 落 TASK_DIR 说明)
  - agate/SETUP.md (P4b M9「### 步骤 2-dispatch-routing：机器级档位绑定 scaffold」小节)
  - agate/tests/unit/test_tag0034_p4b.py (P4b 新，18 例 / 56 asserts —— 首轮 15 + A1 fix 补 3：api_error→infra_error / unknown_error→no_parseable_output / codex 裸 type:error→infra_error 不回归)
  - agate-workspace/dispatch-routing.yaml (P4a 新，非协议本体)
  - docs/design-notes/design-dispatch-routing.md (P4a M12，走 docs commit；P8 §5/§7 老串定点清理 —— rules/dispatch-routing.yaml → agate-workspace/dispatch-routing.yaml、「按序探测」→ try-and-fall、§7 事项 4 作废标注，P7 [DEVIATION] 收尾)
  - agate-workspace/roadmap/roadmap.md (P4a M12，走 docs commit；P8 RM-AG0060 状态列 scheduled → done + 更新日期 2026-09-10，P8 gate RM-AG0043 硬校验)
  - agate/LIMITATIONS.md (P8：局限 2「现状：无解」段后追加「派发路由缓解链（TAG0034 / RM-AG0060 已落地）」段 —— cli:native 弱缓解 / 跨 CLI 强缓解 / dispatch_route 留痕 + 两条完整性不变量 + 诚实边界句「仍非根治……与局限 3 同构……per-machine 机会式」，形态对齐局限 3「P6.5 独立 Judge 缓解链」)
  - agate/adr.md (P8：ADR-012 后追加 ADR-013「派发路由 / gate 生产者无关性（gate 不认谁生产的）」—— 逐字采用本报告附录草案，状态/语境/决策「未来不得为跨 CLI 派发定制 gate」/理由（关联 ADR-002 / ADR-006）/后果)
  - CHANGELOG.md (P8：顶部插入 ## [0.71.0] - 2026-09-10 段 —— minor bump，TAG0034 派发路由内容清单)
  - agate/UPGRADING.md (P8：§3 追加 ### v0.71.0 章节 —— 无破坏性变更 / 零迁移动作，CHECK 13 CHANGELOG↔UPGRADING 章节对应所必需)
  - README.md / README.zh-CN.md (P8：version badge v0.70.0 → v0.71.0)
  - agate-workspace/debt/tech-debt.md (P8：DEBT0039 status open → closed + task_id null → TAG0034 + closed_at + 2 条 closure evidence（P6-acceptance BDD-48/49/50 + P7-consistency 0 ERROR）)
  - agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md (P8：frontmatter 新增 scope_resolved: 两项 —— DEBT0039 并入 + A5.3/A7.4 doc-sync，check-scope-resolved.py 读取)
review_scope: TAG0034 P4a + P4b + P4c + P8 批 agate/** 改动（SELF-GATE 语义 gate，agent≠main）；P4a 三轮（首审 misaligned → 复审 aligned）、P4b 增量两轮（首轮 A1 misaligned → A1 fix 复审 aligned）、P4c 增量一轮（aligned）、P8 收尾一轮（aligned，本文件「# P8 批复审」节）
prod_isolation: "[PROD_NOT_TOUCHED]"
conclusion: aligned
review_rounds: 6
pytest_full_run: "P8 轮（2026-09-10）：5 failed / 1620 passed / 2 skipped（155.17s）—— 5 failed **全部同一根因 = CHECK 7 pre-tag**（README badge v0.71.0 已 bump / `git tag v0.71.0` 未创建 → `check-protocol-consistency.py --strict-errors-only` 唯一 ERROR = CHECK 7 → 5 个断言「consistency exit 0 / 0 ERROR / CHECK 7 PASS」的测试红：test_bdd_50 / test_con_1 / test_con_6 / test_env_adapt_docs::test_bdd_25 / test_tag0027_b1::test_bdd_5）。1620+5=1625 = P4c 基线；主 Agent `git tag v0.71.0` 后 CHECK 7 归零 → 5 项全绿 → 1625 passed / 0 failed / 2 skipped。DEBT0013 时序、TAG0033 P8 同款，非 P8 引入回归。CHECK 7 之外无别的 ERROR、上述 5 项之外无别的 fail。"
p4c_pytest_full_run: "P4c 轮（2026-09-10）：1625 passed / 0 failed / 2 skipped（164.01s，exit 0）—— tag0034 全绿；check-protocol-consistency --strict-errors-only exit 0（CHECK 1~15 PASS，329 WARNING / 0 ERROR）。"
round1_conclusion: "P4a 首审：misaligned（A3/A4/A6 同一根因 = CHECK 9 锚点表缺 check-dispatch-routing.py；A5.3/A7.4 NEEDS_HUMAN_REVIEW）"
round2_conclusion: "P4a 复审：aligned（A3/A4/A6 修复已落地复核确认；A5.3/A7.4 用户 2026-09-09 已 HUMAN_CONFIRMED，两条 doc-sync 落 P8 收尾，不阻断 P4a commit）"
round3_conclusion: "P4b 增量首轮：misaligned（A1 —— platform-notes.md M10 判定表两处 reason-code 归类与 classify_outcome 实际行为不一致：OpenCode UnknownError / Claude Code stop_reason==\"error\"·api_error_status；低严重度，路由行为一致、仅账本 reason 标签差，须修脚本或修文档二选一。A2/A3/A4/A5/A6/A7 delta 全 ALIGNED）"
round4_conclusion: "P4b 增量复审（A1 fix）：aligned（implementer 按 option (a) 改 classify_outcome —— 基础设施信号按 cli 细分：通用集去裸 '\"type\":\"error\"'；_BARE_TOP_ERROR_SIGNALS 仅 codex；_INFRA_SIGNALS_CLAUDE_ONLY + _claude_api_error 仅 claude-code；分支 2b opencode 裸 error 无具名 → NO_PARSEABLE_OUTPUT。补 3 条断言消除 dead fixture。逐格核实 M10 表 vs 代码一致；R1 三值 reason / I2 边界 / P4a 函数 + 第 8 条 + 哈希链未破；全量 pytest 1611 passed / 2 failed（P4c by-design）零回归。P4a+P4b 合并 = aligned）"
round5_conclusion: "P4c 增量：aligned（tmux 观测层 —— build_subprocess_launch / tmux_cleanup_action 纯逻辑 helper + _maybe_tmux_wrap 接入 feature flag AGATE_DISPATCH_TMUX 默认关。A1 tmux 小段 vs helper 逐条一致 + 与 design-note §3 一致；A5 CHECK 14 PASS（tmux 子命令不在护栏 1 禁词清单）+ 6 冻结脚本 + classify_outcome/resolve/try_and_fall 零改动；A4 全量 pytest 1625 passed / 0 failed / 2 skipped，tag0034 全绿。feature flag 默认关对应 [DESIGN_GAP_REVIEWED: 已确认]，原则 6 记 A2/A7 ALIGNED + [KNOWN_DEVIATION]。无 MISALIGNED / NEEDS_HUMAN_REVIEW。P4a+P4b+P4c 三批合并 = aligned；A5.3/A7.4 + tmux 目标环境复跑为 P8 交付项、不阻断 P4 commit）"
round6_conclusion: "P8 收尾：aligned（A5.3 LIMITATIONS.md 局限 2「派发路由缓解链」段 + A7.4 adr.md ADR-013「gate 生产者无关性」逐字采用本报告附录草案 + design-note §5/§7 老串清理 + CHANGELOG [0.71.0] + UPGRADING §3 v0.71.0 + README badge v0.71.0 + roadmap RM-AG0060 done + tech-debt DEBT0039 closed + P1 scope_resolved 两项。A1/A2：ADR-013 决策措辞 vs agate_dispatch_route.py GATE_FAIL_TRIGGERS_FALLBACK=False + check-events.py DISPATCH_ROUTE_REASONS 无 gate_fail + dispatch-protocol.md「### 0. 派发路由」子节 逐条语义一致、ADR 不比它们宽/窄；LIMITATIONS 局限 2 新段弱/强缓解 + 两条完整性不变量与新节一致。A4：全量 pytest 5 failed / 1620 passed / 2 skipped —— 5 failed 全部同一根因 = CHECK 7 pre-tag（badge bumped / tag pending），CHECK 7 之外无别的 ERROR、这 5 项之外无别的 fail，主 Agent git tag v0.71.0 后归零（1625 passed / 0），DEBT0013 时序 / TAG0033 P8 同款，不判 misaligned。回归：git diff HEAD -- phases.yaml/check-gate.py/check-state-transition.py/state-machine.md/dispatch-protocol.md/agate_dispatch_route.py/check-events.py/tests 无输出。P8 delta 全 ALIGNED。P4a+P4b+P4c+P8 四批合并 = aligned)"
---

# 协议-脚本对齐审查 — TAG0034 P4a 批

> 审查对象：`git diff HEAD`（HEAD = `c218026` P3 commit）范围内的 `agate/**` 改动
> 对齐基准：`agate-workspace/tasks/TAG0034-dispatch-routing/P2-design.md` §3（方案权威）+ `P1-requirements.md` BDD-1~30
> DESIGN_GAP：`P4-implementation.md` 一条 `[DESIGN_GAP]`（P4a `_route_main` 只做 resolve + 输出路由计划 JSON，端到端 try-and-fall 交 P4b），已被主 Agent 标 `[DESIGN_GAP_REVIEWED: 已确认]`（任务在 P4，尚无 P7 记录）

`[PROD_NOT_TOUCHED]` —— 仅 worktree 内读取 + 写 `/tmp` 留痕 + 本审查报告；未触碰主 checkout 与 `~/.agate`。

> **复审轮（round 2，2026-09-09）说明**：首审轮结论 **misaligned**（A3/A4/A6 同一根因 —— `check-protocol-consistency.py` 的 `SCRIPT_ALIGNMENT_ANCHORS` 缺 `check-dispatch-routing.py` 锚点条目；A5.3 / A7.4 `NEEDS_HUMAN_REVIEW`）。复审轮两件事已处理：
> 1. **MISALIGNED 根因已修**：implementer 给 `SCRIPT_ALIGNMENT_ANCHORS` 追加 `check-dispatch-routing.py` 条目（`keywords: ["VALID_CLI", "VALID_EFFORT", "fallback"]`，三符号复核确在脚本中；无 `callers`）。本轮复核：`check-protocol-consistency.py --strict-errors-only` exit 0、`CHECK 9 PASS`、无 `CHECK9-coverage` WARNING（WARNING 总数 336→329）；全量 pytest 重跑 `3 failed / 1592 passed / 2 skipped`，`test_sg_6` 转绿，仅剩 3 条 P4b/P4c 批次边界 by-design red。→ **A3 / A4 / A6 改判 ALIGNED**。
> 2. **A5.3 / A7.4 用户已裁决（2026-09-09）**：两条 doc-sync（`LIMITATIONS.md` 局限 2 缓解链 + 新增 ADR-013「gate 生产者无关性」）**都补，落 P8 收尾批**，已登记 `P1-requirements.md` §1 `[SCOPE+ from user-approval：P4a alignment review A5.3/A7.4]`。两处 `[HUMAN_CONFIRMED]` 已填（见 A5 / A7）。→ **A5 / A7 本任务范围内已闭合（P8 落地）**。
> 3. **总结论：aligned**。A5.3 / A7.4 的两条 P8 交付项不阻断 P4a commit（草案见文末附录）。

---

## 审查结论汇总

| # | 审查项 | 首审轮 | 复审轮（终结论） |
|---|--------|------|------|
| A1 | 文档→脚本对齐 | ALIGNED | **ALIGNED**（附 `[KNOWN_DEVIATION]`：P4a 分批实现，见 A1 末） |
| A2 | 脚本→文档对齐 | ALIGNED | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | MISALIGNED | **ALIGNED**（A3b 修复已落地：`SCRIPT_ALIGNMENT_ANCHORS` 补 `check-dispatch-routing.py` 条目，commit 见 P4a） |
| A4 | 测试覆盖 | MISALIGNED | **ALIGNED**（复审轮全量实跑 3 failed / 1592 passed / 2 skipped，3 red 全为 P4b/P4c 批次边界 by-design；`test_sg_6` 已转绿） |
| A5 | 下游影响 + 文档传播 | NEEDS_HUMAN_REVIEW | **NEEDS_HUMAN_REVIEW → 已 HUMAN_CONFIRMED**（A5.3：`LIMITATIONS.md` 局限 2 缓解链，用户 2026-09-09 裁决「补，落 P8」；本任务范围内已闭合） |
| A6 | 锚点表覆盖 | MISALIGNED | **ALIGNED**（`check-dispatch-routing.py` 已加入 `SCRIPT_ALIGNMENT_ANCHORS`；`CHECK 9 PASS`、无 `CHECK9-coverage` WARNING） |
| A7 | 设计原则一致性 | NEEDS_HUMAN_REVIEW | **NEEDS_HUMAN_REVIEW → 已 HUMAN_CONFIRMED**（A7.4：补 ADR-013「gate 生产者无关性」，用户 2026-09-09 裁决「补，落 P8」；本任务范围内已闭合） |

> **首审轮**：A3 / A4 / A6 三项 MISALIGNED **同一根因、同一修复** —— `agate/scripts/check-protocol-consistency.py` 的 `SCRIPT_ALIGNMENT_ANCHORS` 缺 `check-dispatch-routing.py` 条目。
> **复审轮**：修复已落地并复核确认（`SCRIPT_ALIGNMENT_ANCHORS` 第 759-762 行新增条目 `desc`「dispatch-routing schema 静态校验（TAG0034 / RM-AG0060：cli/effort 枚举 + tier/candidates 互斥 + fallback 非法）」/ `script: agate/scripts/check-dispatch-routing.py` / `keywords: ["VALID_CLI", "VALID_EFFORT", "fallback"]`）→ `test_sg_6` 转绿、`CHECK9-coverage` WARNING 消除、`check-protocol-consistency.py --strict-errors-only` exit 0（WARNING 336→329 / 0 ERROR）。A3 / A4 / A6 改判 **ALIGNED**。
> A5.3 / A7.4 用户 2026-09-09 裁决「两条 doc-sync 都补、落 P8 收尾批」，两处 `[HUMAN_CONFIRMED]` 已填 —— A5 / A7 本任务范围内闭合（P8 落地），不阻断 P4a commit。

**总结论：aligned**（复审轮）｜ 首审轮为 misaligned

---

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

逐条核对 `dispatch-protocol.md` 新子节「### 0. 派发路由（查表 → 派首选 → 逐级回落 → 再派发）」（diff `agate/dispatch-protocol.md` +506~+566 行区）声明的规则与脚本语义。

**A1.1 优先级序**

文档（`dispatch-protocol.md:511-513`，新节 step 1）：
> 按优先级序（项目级直接值 `candidates:` > 项目级档位映射 `tier:` > 机器级绑定 `tier_bindings:` 展开 > 出厂默认 → standard）解析出「默认派发」或「有序跨 CLI 候选链」。(phase,role) 命中优先于 phase 级。

脚本（`agate_dispatch_route.py:111-160` `resolve()`）：`entry` 有 `candidates` → 优先级 1（L123-124）；`elif` 有 `tier` → 优先级 2（L125-127）；`else` → `factory_defaults.get(f"{phase}.{role}") or fd.get(phase) or "standard"` 优先级 4（L128-134）；`raw_chain is None`（来自 tier 引用）→ `tier_bindings.get(tier)` 展开优先级 3（L140-144）。`_lookup_route_entry`（L86-104）先查点分 `f"{phase}.{role}"`、再查 `routes[phase][role]` 嵌套、再查 `routes[phase]` phase 级 → (phase,role) 命中优先于 phase 级。

**语义级一致**：分支序、命中优先、tier 作为「展开字典」而非「与 routes 竞争的表」（P2-design §3.3 BDD-15 定死点）逐条对应。**ALIGNED**。

**A1.2 `standard` 短路（不变量锚）**

文档（新节 step 2 + `dispatch-tiers.yaml:24-27`）：
> `standard` / 无配置 → 直接默认派发（同平台、同 model），不写 `dispatch_route` 事件。
> `standard` 恒等于「继承主 Agent 当前 model 的原生派发」——…… `standard` 不经 tier_bindings 展开……

脚本（`resolve():137-138`）：`if tier == "standard": return _default_result(current_model)` —— `_default_result`（L107-108）= `{"form": "default", "chain": None, "model": current_model, "effort": None}`。短路发生在 `tier_bindings` 展开之前（L140 之前）。与 P2-design §3.2「决策层遇 `standard` 直接返回 `{form: default}`」逐字一致。「不写 `dispatch_route` 事件」：`try_and_fall`（L394-416）仅在 `r.form == 'chain'` 路径被调用；P2-design §3.7 伪码 `if r.form == 'default': return DEFAULT_DISPATCH`（不写事件）。**ALIGNED**。

**A1.3 三类回落理由码 + 「gate 不触发换候选」不变量**

文档（新节「两条完整性不变量」，`dispatch-protocol.md` +558~+566）：
> 候选回落只在 `launch_fail` / `infra_error` / `no_parseable_output` 三类基础设施信号时发生……
> `dispatch_route` 理由码枚举里**没有 `gate_fail` 值**，`check-events.py` 第 8 条机械拒绝任何 `gate_fail` / 非三值理由码。

脚本三处闭合：
1. `agate_dispatch_route.py:45` `_VALID_REASONS = ("launch_fail", "infra_error", "no_parseable_output")`；`classify_outcome()`（L268-300）`kind` 取值仅 `LAUNCH_FAIL / INFRA_ERROR / NO_PARSEABLE_OUTPUT / HAS_OUTPUT`，无 `GATE_FAIL`；`GATE_FAIL_TRIGGERS_FALLBACK = False`（L43）。
2. `try_and_fall()`（L402-413）：`kind == "HAS_OUTPUT"` → 写事件 return（停回落）；否则记 `reason = outcome.reason` continue。产出质量差归 `HAS_OUTPUT`（`classify_outcome` L296-297：`if files: return Outcome("HAS_OUTPUT", None)`，presence 级），不回落 —— 对应 P2-design §3.7 N7 / BDD-24。
3. `check-events.py:43-45` `DISPATCH_ROUTE_REASONS = {"launch_fail", "infra_error", "no_parseable_output"}`；`:119-134` 对 `ev.get("event") == "dispatch_route"` 的行，逐 `candidates_tried[i]`，`reason = cand.get("reason")`，`if reason is not None and reason not in DISPATCH_ROUTE_REASONS: sys.exit(1)`。

**语义级一致**（≤/< 无涉；「机械拒绝」= `sys.exit(1)` 硬拦截，非 WARNING）。与 P2-design §3.8 M6 定义、BDD-27 逐条对应。`reason` 缺省（成功候选无 `reason` 键）时放行 —— 与「若存在」措辞一致。**ALIGNED**。

**A1.4 「gate 判定只认产出文件 + exit code，不认谁生产的」**

文档（`dispatch-protocol.md` +554~+556）：
> `check-gate.py` / `check-judge-verdict.py` / `check-p6-provenance.py` 对跨 CLI 派发的产出零特殊处理……

核对：`git diff HEAD --name-only` 不含 `check-gate.py` / `check-judge-verdict.py` / `check-p6-provenance.py` —— 三校验器 P4a 零改动，无跨 CLI 特判分支被引入。P1 §3 第 6 组已独立核实「两校验器纯 TASK_DIR 文件解析、平台无关」。**ALIGNED**。

**A1.5 schema 校验口径**

文档基准 = P2-design §3.6 + P1 BDD-1~6：

| 规则 | 文档 | 脚本（`check-dispatch-routing.py`） | 判定 |
|---|---|---|---|
| `cli` 枚举 `{native, claude-code, codex, opencode}` | BDD-4 / §3.6 | `VALID_CLI`（L32）+ `_check_candidate:93` `if cand.get("cli") not in VALID_CLI: _err` | ALIGNED |
| `effort` 枚举 `{low, medium, high}` | BDD-5 / §3.6 | `VALID_EFFORT`（L33）+ `_check_effort:84-86` | ALIGNED |
| `tier` 与 `candidates` 互斥 | BDD-2 / §3.6 | `_check_route_spec:116-117` `if has_tier and has_candidates: _err` | ALIGNED |
| `fallback` 任意层非法 | BDD-6 / §3.6 | `_scan_fallback:70-81` 递归全树扫描 → `_err` | ALIGNED |
| `model: null` 放行 | §3.6 / SUGGEST #2 | `_check_candidate:95-98` `if model is not None and not isinstance(model, str): _err`（null 通过） | ALIGNED |
| `machine_routes:` 文档化保留字（放行、无语义） | §3.3 / §3.6 | `KNOWN_TOP`（L34）含 `machine_routes`；`main()` 无对其分支（L219 注释「放行、不作任何语义校验」） | ALIGNED |
| `(phase,role)` key 形态（`Pn` / `Pn.role` 点分 / `Pn: {role: {...}}` 嵌套） | BDD-3 / §3.6 | `_check_routes:142-152` 三形态分派（`_ROUTE_SPEC_KEYS` marker 判定 phase 级 vs 嵌套 role map） | ALIGNED |
| 坏 YAML / 文件不存在 / 顶层非 mapping → exit 0 | §3.6 | `main():185-205` 三分支均 `sys.exit(0)` | ALIGNED |
| `tier` 交叉核 `dispatch-tiers.yaml` `tiers:` key 集，未知 → exit 1；该文件不可读 → 降级「非空字符串放行」+ WARNING | §3.6 | `_load_tier_names()`（L49-67）；`_check_route_spec:118-131`（`tier_names is None` → 仅校验非空 + WARNING；`tier not in tier_names` → `_err`） | ALIGNED |
| `tier_bindings.standard` → WARNING（不 exit 1） | §3.6 / §3.3 | `_check_tier_bindings:160-164` `if tkey == "standard": _warn(...)` | ALIGNED |

`resolve()` 侧对 schema 的呼应（`_is_route_spec` 的 `_ROUTE_SPEC_MARKERS = ("tier", "candidates", "effort")` L76）与校验器 `_ROUTE_SPEC_KEYS = ("tier", "candidates", "effort", "fallback")` L35 一致（校验器多 `fallback` 是为了让含 `fallback` 的 phase 级条目仍进入 `_check_route_spec` 报错，非语义分歧）。**ALIGNED**。

**A1.6 `dispatch-tiers.yaml` `standard` 短路分支逐字核对**

文档（`dispatch-tiers.yaml:24-27` `standard.intent`）：
> 恒等于「继承主 Agent 当前 model 的原生派发」……standard 不经 tier_bindings 展开、不起子进程、不改 model；决策层遇 standard 直接返回默认派发。

脚本（`resolve():137` + `_default_result:107-108`）：`form='default'` / `chain=None` / `model=current_model` / `effort=None`。`current_model` 来源 = `agate-dispatch.py:_route_main` `os.environ.get("AGATE_CURRENT_MODEL", "")`（M4b diff）。与 P2-design §3.3 返回契约「`form == 'default'` → `chain = None`、`model = <主 Agent 当前 model>`、`effort = None`」逐字一致。**ALIGNED**。

**`[KNOWN_DEVIATION`（原则 6 / DESIGN_GAP_REVIEWED，非普通 MISALIGNED）**：`dispatch-protocol.md` 新节 step 3 描述完整 try-and-fall（「第一个动作即把真实 dispatch-context 派给首选候选」逐候选派发 → 收产出即停）；P4a `agate-dispatch.py:_route_main`（M4b diff L164-233）**只做 `resolve` + stdout 输出已解析的路由计划 JSON**（`form=default` → `{cli:"default", model, form, dispatch_context}`；`form=chain` → 首候选 + 完整 `chain` + `form: native|subprocess` + `dispatch_context`），**不在 P4a 内跑端到端 `dispatch_once` / 子进程 spawn**。差异点完全对应 `P4-implementation.md` 的 `[DESIGN_GAP: P2-design §3.5 把 _route_main 具体形态留给「P4a 落地时定」……P4a 只做 resolve + 输出路由计划 JSON，端到端 try-and-fall 交 P4b/M5]`，已被主 Agent `[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-09）……与 P2-design §4.1「P4a 建 route 骨架 + JSON 输出契约 → P4b 加 subprocess 分支」逐条一致……非偏离 P2 设计]`。`try_and_fall` / `classify_outcome` / `build_dispatch_command` helper 在 `agate_dispatch_route.py` 已完整实现且单测全绿（见 A4），只是尚未被 `_route_main` 端到端串联。按原则 6，本项结论记 **ALIGNED**，追加：`[KNOWN_DEVIATION: 来源 TAG0034 P4-implementation.md DESIGN_GAP_REVIEWED（主 Agent 2026-09-09），理由摘要——P4a 交付 route 骨架 + target JSON 契约，端到端 try-and-fall（dispatch_once + subprocess spawn）随 P4b/M5，与 P2-design §4.1 批次意图一致；尚无 P7 记录（任务在 P4），P7 阶段须由 consistency-reviewer 复核确认]`

---

### A2: 脚本→文档对齐 — ALIGNED

核对 P4a 新增/改动的脚本行为是否都有协议文档对应描述，有无「脚本做了但文档没写」的裸露行为。

| 脚本行为 | 文档对应 | 判定 |
|---|---|---|
| `agate-dispatch.py route PHASE ROLE [TASK_DIR]` 新子命令 | `dispatch-protocol.md` 新节 step 1「查表：resolve(Pn, R)」+ P2-design §3.5「`agate dispatch route <Pn> <R>` 新增子命令」+ design-note §2.2/§3.5（M12 diff） | ALIGNED |
| `route` 子命令 stdout 输出 target 描述 JSON（`{"cli","model","effort","form","dispatch_context"[,"chain"]}`） | P2-design §3.1 step 2.6 + §3.5「stdout = 单行 JSON」；`_route_main` docstring 逐字。P4a 固化契约、P4b/P4c 只增不改（`[DESIGN_GAP_REVIEWED]`） | ALIGNED |
| `dispatch_route` 事件 JSON 结构（`event / phase / candidates_tried / final`，复用 `append_event` 哈希链） | `dispatch-protocol.md` 新节 step 5「写 1 条 dispatch_route 事件（带 candidates_tried 理由码 + final），复用哈希链账本」+ P2-design §3.8 事件样例 | ALIGNED |
| `check-events.py` 第 8 条：`dispatch_route` 理由码枚举校验 | `check-events.py` docstring 审计链清单第 8 条（diff +14~+17）+ 第 7 条注释补 `dispatch_route` 为已知类型（diff +14）+ `dispatch-protocol.md` 新节「`check-events.py` 第 8 条机械拒绝」+ P2-design §3.8 | ALIGNED |
| `agate_dispatch_route.py` importable helper（`resolve / load_config / load_factory_defaults / classify_outcome / build_dispatch_command / resolve_native_target / try_and_fall / write_dispatch_route_event / should_consult_routing_table / route_is_noop`） | P2-design §3.3/§3.4/§3.7/§3.8/§3.9 + `P4-implementation.md` 改动清单 M4 逐条列出；模块 docstring 自带函数级 P2 章节引用 | ALIGNED |
| `dispatch-tiers.yaml` 三档 + `defaults: {}` | `dispatch-protocol.md` 新节头部「协议本体档位词表 `agate/rules/dispatch-tiers.yaml`（`bulk` / `standard` / `deep` 语义画像 + 出厂默认）」+ P2-design §3.2 | ALIGNED |

**minor（不判 MISALIGNED）**：`agate/scripts/README.md` 无 `agate-dispatch.py` 条目（grep 确认既有状态即无），故新 `route` 子命令未登记该表 —— 属既有覆盖缺口的延续，非 P4a 引入的新漂移；`agate-dispatch.py` 主体本就不在该表。建议（非阻断）：P4b 补 `agate-cmdstream-adapters.py` / SETUP 时，可顺带在 `scripts/README.md` 工具清单补 `agate-dispatch.py`（含 `route` 子命令）一行。

**结论：ALIGNED**。无裸露行为；所有脚本新增能力均有协议正文或方案文档对应。

---

### A3: 一致性连锁 + 反向传播 — ALIGNED（首审轮 MISALIGNED，修复已落地）

**A3a（连锁：已知衍生改动）— ALIGNED**

`dispatch_route` 是新 event 类型。核对「提到已知 event 类型」的位置：

- `check-events.py:14`（docstring 第 7 条）：`gate_run/judge_verdict/state_transition/dispatch_route 为已知类型` —— **已同步补 `dispatch_route`**（diff 确认）。
- `agate_common.py:328` `append_event()`：通用签名（`event` 为任意 dict），**无 event 类型枚举**，`dispatch_route` 复用零改动。ALIGNED。
- `state-machine.md` / `WORKFLOW.md`：grep `gate_run|state_transition|judge_verdict` 仅命中 `judge_verdict` 轮次预算描述（`state-machine.md:78/151/157/417/447`、`dispatch-protocol.md:417/419`），**无「已知 event 类型」集中枚举清单**需要补 `dispatch_route`。ALIGNED。
- `dispatch_route` 回落**不写 `state_transition`、不动 `retries`、不进 PAUSED**（`write_dispatch_route_event` docstring L422-427 + BDD-28）→ 与状态机 retry 语义解耦，`state-machine.md` retry / 回退规则无需改。ALIGNED。

**A3b（反向传播：应被 P4a 改动影响但未在 diff 中的文件）**

| 应被影响文件 | 影响到了没 | 判定 |
|---|---|---|
| `agate/scripts/check-protocol-consistency.py`（`SCRIPT_ALIGNMENT_ANCHORS`）—— 角色反向传播路径表明文：「新增/修改某个 `agate/scripts/check-*.py` … CHECK 9 锚点表」 | **首审轮：否**（新 `check-*.py` gate 脚本未加入 `SCRIPT_ALIGNMENT_ANCHORS`）。**复审轮：已修**（`SCRIPT_ALIGNMENT_ANCHORS` 第 759-762 行新增 `check-dispatch-routing.py` 锚点条目，`keywords: ["VALID_CLI", "VALID_EFFORT", "fallback"]` 三符号复核确在脚本中）。 | 首审 MISALIGNED → **复审 ALIGNED** |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」 | 不需改 —— `check-dispatch-routing.py` 未挂 pre-commit / CI（`grep 'check-dispatch\|dispatch-routing' pre-commit-gate.py pre-commit-gate.sh ci-gate-backstop.py check-gate.py WORKFLOW.md` 零命中），与 P2-design §3.6「不进 `gate_commands`、SELF-GATE 链手动跑 + 可选 pre-commit」一致。 | ALIGNED |
| `agate/scripts/README.md` | 见 A2 minor（既有覆盖缺口延续，非新漂移） | ALIGNED（观察项） |
| `agate/tests/README.md`（per-script 测试计数表） | tag0034 测试模块（`test_tag0034_*.py`）为 P3 commit `c218026` 产出，非 P4a diff；该表更新属 P3 遗留 / P7 一致性范围，非 P4a 责任 | 不计入 P4a |
| 角色文件（`dispatch-protocol.md` 改派发模板 → 角色文件）| `dispatch-protocol.md` 新增的是「派发编排机制」子节（机械路由步骤），非派发 prompt 模板 / gate 表；`architect.md` 的 DEBT0039 措辞①已在 diff 内（M8）。无其它角色文件需同步。 | ALIGNED |

**首审轮 MISALIGNED 详情**：`check-protocol-consistency.py` 的 `check_anchor_coverage()`（L805-838）反向兜底遍历 `agate/scripts/check-*.py`，`check-dispatch-routing.py` 命中 glob 但既不在 `SCRIPT_ALIGNMENT_ANCHORS` 也不在 `GATE_SCRIPT_EXEMPT`（L799-802）→ 运行时 `CHECK9-coverage` WARNING（首审轮实跑确认）。`--strict-errors-only` 下为 WARNING 不阻断（exit 0），但 `agate/tests/integration/test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts`（断言每个 `check-*.py` basename 出现在 `check-protocol-consistency.py` 文本中）**首审轮全量 pytest 实跑 FAIL**。

**复审轮：修复已落地并复核确认**。implementer 给 `SCRIPT_ALIGNMENT_ANCHORS` 追加一条（`check-protocol-consistency.py` 第 759-762 行）：
```python
{
    "desc": "dispatch-routing schema 静态校验（TAG0034 / RM-AG0060：cli/effort 枚举 + tier/candidates 互斥 + fallback 非法）",
    "script": "agate/scripts/check-dispatch-routing.py",
    "keywords": ["VALID_CLI", "VALID_EFFORT", "fallback"],
},
```
- `keywords` 三符号复核：`grep -c 'VALID_CLI\|VALID_EFFORT' check-dispatch-routing.py` = 6、`fallback` 多处命中 —— 三个都确在脚本中，CHECK 9 正向锚点对齐通过。
- 无 `callers` 字段 —— `check-dispatch-routing.py` 非常驻 pre-commit gate（与 P2-design §3.6「不进 `gate_commands`、SELF-GATE 链手动跑 + 可选 pre-commit」一致），不设 `callers` 即不触发 `CHECK9-callers` WARNING。**判定正确**。
- 复审轮实跑：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0、`✅ PASS CHECK 9 协议-脚本结构对齐`、**无 `CHECK9-coverage` WARNING**（WARNING 总数 336→329 / 0 ERROR）；全量 pytest 重跑 `test_sg_6` **转绿**（passed 1591→1592，failed 4→3）。

**结论：首审轮 MISALIGNED → 复审轮 ALIGNED**（A3b 反向传播缺口已闭合，commit 随 P4a）。

---

### A4: 测试覆盖 — ALIGNED（首审轮 MISALIGNED，锚点修复后全量实跑干净）

**复审轮全量 pytest 实跑（锚点修复后，本次审查执行）**：

```
$ python3 -m pytest agate/tests/ -q --tb=no
（worktree 根 /home/kity/oclab/agateon/.worktrees/agate-TAG0034，2026-09-09）
=========================== short test summary info ============================
FAILED agate/tests/unit/test_tag0034_subprocess.py::test_bdd_42_routed_away_judge_verdict_platform_independent
       - AttributeError: module 'agate_dispatch_route' has no attribute 'routed_away...'
FAILED agate/tests/unit/test_tag0034_tmux.py::test_bdd_37_which_tmux_decides_wrap_or_bare
       - AttributeError: module 'agate_dispatch_route' has no attribute 'build_subpr...'
FAILED agate/tests/unit/test_tag0034_tmux.py::test_bdd_38_countdown_and_no_force_kill_with_client
       - AttributeError: module 'agate_dispatch_route' has no attribute 'tmux_cleanu...'
3 failed, 1592 passed, 2 skipped in 175.29s (exited with code 0)
```

**計數：passed 1592 / failed 3 / skipped 2**（首审轮 = passed 1591 / failed 4；`test_sg_6` 修复后转绿 → passed +1 / failed −1）。

**failed 分类（复审轮，全部 by-design）**：

| 失败用例 | 归属 | 是否 by-design red |
|---|---|---|
| `test_bdd_42_routed_away_judge_verdict_platform_independent` | P4b（`routed_away_verdict_location` 未实现） | ✅ 是 —— P2-design §4.1 批次边界明文「routed-away judge 核实归 P4b」；`objective_info` 预告 3 红 |
| `test_bdd_37_which_tmux_decides_wrap_or_bare` | P4c（`build_subprocess_launch` / tmux wrapper 未实现） | ✅ 是 —— P2-design §3.10 / §4.1「tmux 观测层归 P4c」 |
| `test_bdd_38_countdown_and_no_force_kill_with_client` | P4c（`tmux_cleanup_action` 未实现） | ✅ 是 —— 同上 |

**首审轮的第 4 红已消除**：`test_sg_6_check9_anchor_table_covers_all_gate_scripts`（首审轮 FAIL「check-dispatch-routing.py 不在 CHECK 9 锚点表中」，属 P4a 引入的未预期回归，非 by-design）—— 锚点条目补上后本轮**转绿**（同 A3b / A6 修复）。

**新逻辑边界覆盖评估（P4a 目标 BDD）**：

- schema（BDD-1~6）：`test_tag0034_schema.py` 6 用例 —— 合法两轴组合 / tier×candidates 互斥 / (phase,role) key 形态 / 非法 cli / 非法 effort / fallback 非法，全绿。
- `resolve` 每分支（BDD-7~18 + T1/N2）：`test_tag0034_resolve.py` 10 用例 —— (phase,role) 命中 / phase 回落 / 出厂默认 / standard 短路 / tier 展开 / tier_bindings 缺 tier / effort 合并 / 返回契约键集，全绿。
- try-and-fall 三类回落 + 全兜底（BDD-19~25 + T2/N6/N7）：`test_tag0034_tryfall.py` 10 用例 —— 无 probe / launch_fail / infra_error / no_parseable_output / HAS_OUTPUT 即停 / 产出质量差不回落 / 全落空 `final={"cli":"default"}` / 挂死→INFRA_ERROR，全绿。
- `dispatch_route` 事件 + `check-events.py` 第 8 条（BDD-27/29/30 + T3）：`test_tag0034_events.py` 4 用例 —— 三合法理由码各 exit 0 / 混入 `gate_fail` exit 1 / 哈希链复用 / `test_check_events.py` 零改动仍绿（23 passed），全绿。
- `cli: native` 各平台（BDD-8/9/10/31/32）：`test_tag0034_native.py` 7 用例 —— effort 映射 Codex `-c model_reasoning_effort=` / OpenCode `--variant` / Claude Code 能力探测分流 / `model: null` 不传 flag / platform-notes doc-assertion，全绿。
- 交互（BDD-43/44/45/51）：`test_tag0034_interaction.py` 6 用例，全绿。
- 协议正文 doc-assertion（BDD-41/48/49）：`test_tag0034_docs.py` 8 用例，全绿。
- 回归零改动（BDD-39/40）：`regression/test_tag0034_zero_change.py` 2 用例 —— 字节基线 + 无配置 = 现状，全绿。

**判定**：新逻辑本身覆盖充分（边界含 T1/T2/T3 + N2/N6/N7 参数化）。首审轮全量实跑不干净（含 `test_sg_6` 这条 P4a 引入、未在批次设计中豁免的回归 —— T026/G2.5 教训正例：implementer 自查用 `-k tag0034` 分片，`test_sg_6` 在 `test_protocol_alignment_review.py`、不匹配 `tag0034` 命名域 → 被放过）。**复审轮锚点条目补上后，`test_sg_6` 转绿，全量实跑仅剩 3 条 P4b/P4c 批次边界 by-design red**（按 P2-design §4.1 批次意图 + `objective_info` 预告属可接受的分批交付红 —— P4a 只交付 schema 层 + 引擎层 + 协议正文，`routed_away_*` / `build_subprocess_*` / `tmux_cleanup_*` 明文归 P4b/P4c）。

**结论：首审轮 MISALIGNED → 复审轮 ALIGNED**（全量实跑干净，仅剩 by-design red，新逻辑边界覆盖充分）。

---

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW → 已 HUMAN_CONFIRMED（本任务范围内已闭合，P8 落地）

**A5.1 破坏性变更 / 向后兼容 — ALIGNED**

`dispatch_route` 事件对既有 `check-events.py` 账本审计向后兼容：既有任务 `gate-events.jsonl` 无 `dispatch_route` 行 → `check-events.py:120` `if ev.get("event") == "dispatch_route":` 分支不进入，第 8 条不误伤第 1-7 条。P2-design §5 MV8 已实测（构造含 `dispatch_route` 的 2 行合法链 → `check-events.py` exit 0）。本任务 `gate-events.jsonl` 实跑 `check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0（`P4-implementation.md` 自查）。ALIGNED。

`agate-dispatch.py` 既有渲染路径（无 `route` 参数）逐字节不变：`main():args and args[0] == "route"` 分支在参数分派最前（M4b diff），`_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER` / `generated_by` 未触碰。BDD-39 回归断言 + `test_tag0027_b2_*`（5 消费方）零改动仍绿（A4 全量实跑确认）。ALIGNED。

**A5.2 CHANGELOG — 待 P8（非 MISALIGNED）**

P4a 是协议语义变更（新增 `agate dispatch route` 子命令 + `dispatch_route` 事件 + `dispatch-tiers.yaml` 词表 + `dispatch-protocol.md` 新节）。核对本仓惯例：`check-changelog.py` **仅 P8 触发**（`pre-commit-gate.py:480` `if phase == "P8" and _run_script_rc("check-changelog.py", ...)`；`WORKFLOW.md:344` 表 1.6「P8 phase 且 gate 通过后……P2.54：仅 P8 检查，P1-P7 不触发」；`P8-release.md` step 3「更新 CHANGELOG [Unreleased] → 版本号」）。`CHANGELOG.md` 当前顶部 `[0.70.0] - 2026-09-09`（TAG0033），TAG0034 尚无 `[Unreleased]` 段。→ **CHANGELOG 待 P8 统一补**，符合仓库既有 SELF-GATE 任务惯例（TAG0033 亦同批发布），**不判 MISALIGNED**。

**A5.3 文档传播 — NEEDS_HUMAN_REVIEW**

- `orchestrator-template.md` / `WORKFLOW.md` / `role-system.md` / 模板文件：派发路由是「铁律 1 启动 subagent 之前插入的一步机械路由」，`dispatch-protocol.md`「派发编排机制」节是其权威来源（新节明文「此步在铁律 1 启动 subagent 之前插入」）。这些文件对「派发编排机制」节是**引用关系**（`WORKFLOW.md` / 各阶段卡片「按包拆分并行」节引用本节），不各自维护副本 → 无需同步展开。ALIGNED。
- **`LIMITATIONS.md` 局限 2（同源模型系统性盲区，line 13-19「现状：无解」→ ADR-006）**：TAG0034 的设计意图（`design-dispatch-routing.md` 动机 + `dispatch-context` 意图 + `roadmap` RM-AG0060）明确为「部分缓解局限 2」。局限 3 曾因 TAG0020 P6.5 Judge 落地而在 `LIMITATIONS.md:35` 加了「**P6.5 独立 Judge 缓解链**」整段。**是否应对称地在局限 2 补一句指向路由机制（cli:native 弱缓解 / 跨 CLI 强缓解），以及补在哪个批次（P4a 只落弱缓解 + 引擎骨架，跨 CLI 强缓解在 P4b）** —— P2-design §4.4 SELF-GATE 文件清单 / §10 BDD 列表 **均未将 `LIMITATIONS.md` 纳入 P4a（乃至本任务）范围**；P1 §9「下游影响」亦未列。此为文档传播的设计取舍（是否/何时/措辞），非机器可判定的对齐硬缺口 → **NEEDS_HUMAN_REVIEW**。

`[HUMAN_CONFIRMED: 2026-09-09 确认：补。在 agate/LIMITATIONS.md 局限 2 补一段「部分缓解链」，指向本任务路由机制（cli:native 弱缓解 / 跨 CLI 子进程强缓解 / dispatch_route 留痕 + 两条完整性不变量），与 TAG0020 给局限 3 补「P6.5 独立 Judge 缓解链」对称。落 P8 收尾批（措辞基于 P4a-P4c 最终形态）。措辞务必保留诚实边界句：「仍非根治 —— 主 Agent 自身选型 / 横传 model 无外部约束，与局限 3 同构」。已登记为 P1-requirements.md §1 [SCOPE+ from user-approval：P4a alignment review A5.3/A7.4]，P8 dispatch-context 显式列。]`

**结论：NEEDS_HUMAN_REVIEW → 已 HUMAN_CONFIRMED**（用户 2026-09-09 裁决「补，落 P8 收尾批」）。A5.1 / A5.2 ALIGNED；A5.3 的 `LIMITATIONS.md` 局限 2 缓解链为 **P8 收尾交付项**，草案见文末附录，**不阻断 P4a commit**。**本任务范围内已闭合**（P8 落地）。

---

### A6: 锚点表覆盖 — ALIGNED（首审轮 MISALIGNED，修复已落地）

**A6.1 CHECK 9 锚点表是否需要加 `check-dispatch-routing.py` — 是；首审轮缺、复审轮已补**

`check-protocol-consistency.py:805-838` `check_anchor_coverage()` 反向兜底：遍历 `agate/scripts/check-*.py`，每个须在 `SCRIPT_ALIGNMENT_ANCHORS`（`covered = {anchor["script"] for anchor in SCRIPT_ALIGNMENT_ANCHORS}`）或 `GATE_SCRIPT_EXEMPT`（仅 `check-protocol-consistency.py` 自身 + `pre-commit-gate.py`）中。`check-dispatch-routing.py` 命中 `check-*.py` glob。

- **首审轮**：不在 `SCRIPT_ALIGNMENT_ANCHORS` → 运行时 `CHECK9-coverage` WARNING + `test_sg_6_check9_anchor_table_covers_all_gate_scripts` FAIL。角色反向传播路径表「新增/修改某个 `agate/scripts/check-*.py` … CHECK 9 锚点表」明文要求 → MISALIGNED。
- **复审轮**：`SCRIPT_ALIGNMENT_ANCHORS` 第 759-762 行已新增 `check-dispatch-routing.py` 锚点条目（见 A3b 复审段引用），`keywords: ["VALID_CLI", "VALID_EFFORT", "fallback"]` 三符号复核确在脚本中。复审轮实跑：`check-protocol-consistency.py` → `✅ PASS CHECK 9 协议-脚本结构对齐`、**无 `CHECK9-coverage` WARNING**；`test_sg_6` 转绿。→ **ALIGNED**。

无 `callers` 字段的判定正确 —— `check-dispatch-routing.py` 非常驻 pre-commit gate（P2-design §3.6：不进 `gate_commands`、SELF-GATE 链手动跑 + 可选 pre-commit），不设 `callers` 即不触发 `CHECK9-callers` WARNING（复审轮实跑确认无此 WARNING）。

**A6.2 新增协议规则（`dispatch_route` 理由码枚举 / routing schema）是否需要进锚点表 — 部分（`check-events.py` 已被覆盖）**

- `dispatch_route` 理由码枚举校验落在 `check-events.py` 第 8 条。`check-events.py` **已有锚点**（L737-742：`desc`「事件账本审计（append-only 哈希链）」，`keywords` `["prev_hash", "GENESIS"]`，`callers` 三处）—— 该锚点仍成立（`prev_hash` / `GENESIS` 关键词仍在），第 8 条是**同一脚本内的追加审计链**，锚点粒度层面已覆盖。可选（非强制）：为「gate 生产者无关性 / dispatch_route 理由码机械拒绝」加一条专项锚点（`script: check-events.py`，`keywords: ["DISPATCH_ROUTE_REASONS", "dispatch_route"]`），提升语义可追溯性 —— 但按角色注（CHECK 9 部分锚点只验「脚本存在且被正确挂载」、schema 内容语义一致由 A1 逐条人工核对），此项已由 A1.3 逐条核实，**不构成 MISALIGNED**。
- routing schema（`check-dispatch-routing.py`）：见 A6.1，首审轮缺锚点 → 复审轮已补。

**结论：首审轮 MISALIGNED → 复审轮 ALIGNED**（`check-dispatch-routing.py` 已纳入 `SCRIPT_ALIGNMENT_ANCHORS`；`check-events.py` 侧锚点粒度本就已覆盖第 8 条追加审计链）。

---

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW → 已 HUMAN_CONFIRMED（本任务范围内已闭合，P8 落地）

逐条核对相关 ADR（`agate/adr.md`）：

**A7.1 ADR-006（双层角色——执行角色 + 评审角色；同源模型认知隔离上限）**

ADR-006 语境：「同源模型的系统性盲区共享」使角色隔离退化为「认知层非真正独立」（`LIMITATIONS.md:19` 亦引 ADR-006）。TAG0034 给「角色隔离」补 model / 厂商维度：`cli: native`（同厂商换 model）= 弱缓解（`dispatch-protocol.md` 新节明文「同训练系谱盲区基本共享」），跨 CLI 起子进程 = 强缓解（「真正的异源独立视角」）。**方向与 ADR-006「独立评审提供外部视角，能发现执行者因认知盲区遗漏的问题」一致**，是对 ADR-006 已记局限的**部分缓解**，不与 ADR-006 决策（评审角色 `agent≠main` / `check-gate.py` 硬拦截 `agent=main`）冲突 —— P4a 未触碰 `check-gate.py` 的 `agent=main` 分支。**一致（ALIGNED 方向）**。

**A7.2 ADR-002（可判定性——gate 门槛机器可判定）**

`dispatch-protocol.md` 新节「gate 判定只认产出文件 + exit code，不认谁生产的」+ 「未来不得为跨 CLI 派发定制 gate」—— 与 ADR-002「gate 门槛机器可判定、不依赖主观声明」**方向一致**（跨 CLI 产出与本地产出走同一 exit-code 判定面）。回落理由码枚举机械拒绝（`check-events.py` `sys.exit(1)`）而非 LLM 判断，符合 ADR-002。**一致**。

**A7.3 ADR-005（改动性质决定流程——声明性 / 行为逻辑 / 机制交叉）**

三层配置落点：`agate/rules/dispatch-tiers.yaml`（档位词表 = 协议本体，改它触发 SELF-GATE）vs `agate-workspace/dispatch-routing.yaml`（项目级 `tier_bindings:` + `routes:` = 非协议本体、不触发 SELF-GATE，对齐 `maintainability.yaml` 先例）。这条「协议定义机制、内容归用户」的分层与 ADR-005 + RM-AG0046「模式层 / 检测器层分离」同构。**一致**。

**A7.4 未记录的架构决策：「派发路由 / gate 生产者无关性」**

`dispatch-protocol.md` 新节确立一条明确的架构决策：**「gate 解耦 —— gate 只认产出文件 + exit code，不认谁生产的；这条解耦是（跨 CLI/model 派发）设计成立的前提；未来不得为跨 CLI 派发定制 gate」**。这是一条**红线级、约束未来实现**的架构决策（等同 ADR 语气：「不得……」），但 `agate/adr.md` 当前无对应 ADR 条目（最新为 ADR-012）。`dispatch-context` A7 明确提出「是否该补一条新 ADR 记录『派发路由 / gate 生产者无关性』这个架构决策」。按角色 A7 规则（发现未记录的架构决策 → **建议**补新 ADR，结论只 ALIGNED / NEEDS_HUMAN_REVIEW），此为设计指导性判断（补 ADR 的时机 —— P4a / 任务收尾 P8 / 还是 RM-AG0060 epic 后续 TAG；ADR 编号与措辞），**非机器可判定** → **NEEDS_HUMAN_REVIEW**。

`[HUMAN_CONFIRMED: 2026-09-09 确认：补。agate/adr.md 补 ADR-013「派发路由 / gate 生产者无关性」，记录红线级决策「gate 只认产出文件 + exit code、不认谁生产的；这条解耦是跨 CLI/model 派发设计成立的前提；未来不得为跨 CLI 派发定制 gate」，关联 ADR-002（可判定性）/ ADR-006（同源盲区）/ RM-AG0060。理由：dispatch-protocol.md 散文承载不够稳。落 P8 收尾批。已登记为 P1-requirements.md §1 [SCOPE+]，P8 dispatch-context 显式列。]`

**结论：NEEDS_HUMAN_REVIEW → 已 HUMAN_CONFIRMED**（用户 2026-09-09 裁决「补 ADR-013，落 P8 收尾批」）。A7.1-A7.3 与既有 ADR（ADR-006 / ADR-002 / ADR-005）方向一致；A7.4 的 ADR-013「派发路由 / gate 生产者无关性」为 **P8 收尾交付项**，草案见文末附录，**不阻断 P4a commit**。**本任务范围内已闭合**（P8 落地）。

---

## 总结论

**aligned**（复审轮）｜ 首审轮 misaligned

### 闭环规则表（复审轮终态）

| 结论态 | 项 | 状态 / 主 Agent 动作 |
|---|---|---|
| ALIGNED | A1（附 `[KNOWN_DEVIATION]`）/ A2 / **A3 / A4 / A6**（首审轮 MISALIGNED → 修复已落地） | 通过，可 commit。A3/A4/A6 修复 = `check-protocol-consistency.py` 的 `SCRIPT_ALIGNMENT_ANCHORS` 补 `check-dispatch-routing.py` 条目（复核确认：`CHECK 9 PASS` / 无 `CHECK9-coverage` WARNING / `test_sg_6` 转绿 / 全量 pytest `3 failed`(全 by-design) `1592 passed`）。A1 的 `[KNOWN_DEVIATION]`（P4a 分批实现、端到端 try-and-fall 交 P4b）来源 `P4-implementation.md` DESIGN_GAP_REVIEWED（尚无 P7 记录，任务在 P4）—— **P7 阶段须由 consistency-reviewer 独立复核确认**。 |
| NEEDS_HUMAN_REVIEW → **已 HUMAN_CONFIRMED** | A5（A5.3）/ A7（A7.4） | 用户 2026-09-09 裁决：两条 doc-sync 都补、落 **P8 收尾批**，已登记 `P1-requirements.md` §1 `[SCOPE+ from user-approval：P4a alignment review A5.3/A7.4]`。两处 `[HUMAN_CONFIRMED]` 已填。**本任务范围内已闭合（P8 落地）**，不阻断 P4a commit。P8 交付草案见文末附录。 |

**可 P4a commit**（commit message 带 `self-gate-review: docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`）。P4a 全量 pytest 仅剩 3 条 P4b/P4c 批次边界 by-design red（`test_bdd_42` / `test_bdd_37` / `test_bdd_38`，P2-design §4.1 批次意图明文豁免、`objective_info` 预告）。

---

## 附：全量 pytest 实跑输出（A4 强制项）

### 复审轮（锚点修复后，终态）

```
$ python3 -m pytest agate/tests/ -q --tb=no
（worktree 根 /home/kity/oclab/agateon/.worktrees/agate-TAG0034，2026-09-09）

=========================== short test summary info ============================
FAILED agate/tests/unit/test_tag0034_subprocess.py::test_bdd_42_routed_away_judge_verdict_platform_independent
       - AttributeError: module 'agate_dispatch_route' has no attribute 'routed_away...'
FAILED agate/tests/unit/test_tag0034_tmux.py::test_bdd_37_which_tmux_decides_wrap_or_bare
       - AttributeError: module 'agate_dispatch_route' has no attribute 'build_subpr...'
FAILED agate/tests/unit/test_tag0034_tmux.py::test_bdd_38_countdown_and_no_force_kill_with_client
       - AttributeError: module 'agate_dispatch_route' has no attribute 'tmux_cleanu...'
3 failed, 1592 passed, 2 skipped in 175.29s
[exited with code 0]
```

計數：**passed 1592 / failed 3 / skipped 2**。failed 3 条**全部**为 P4b/P4c 批次边界 by-design（见 A4）。

### 首审轮（锚点修复前，供对照）

```
4 failed, 1591 passed, 2 skipped in 172.91s [exited with code 0]
FAILED ... test_sg_6_check9_anchor_table_covers_all_gate_scripts  ← P4a 引入的未预期回归（复审轮已修，转绿）
FAILED ... test_bdd_42 (P4b) / test_bdd_37 (P4c) / test_bdd_38 (P4c)  ← by-design
```

### 补充实跑（复审轮执行）

- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0；`✅ PASS CHECK 9 协议-脚本结构对齐`；**329 WARNING / 0 ERROR**（首审轮 336 WARNING —— `CHECK9-coverage: check-dispatch-routing.py 未纳入 CHECK 9 锚点表` 已消除）
- `grep -n "check-dispatch-routing" agate/scripts/check-protocol-consistency.py` → `761:  "script": "agate/scripts/check-dispatch-routing.py"`（锚点条目已落，第 759-762 行）
- `grep -c "VALID_CLI\|VALID_EFFORT" agate/scripts/check-dispatch-routing.py` → 6；`fallback` 多处命中 —— 锚点 `keywords` 三符号确在脚本中
- `git diff HEAD --name-only` → 与 `dispatch-context` 上游关联 P4a 改动清单一致 + 本轮新增 `agate/scripts/check-protocol-consistency.py`（锚点条目）；`check-gate.py` / `check-judge-verdict.py` / `check-p6-provenance.py` / `phases.yaml` / `pre-commit-gate.{py,sh}` / `ci-gate-backstop.py` 均**不在** diff 内（回归硬约束成立）

---

## 附录：A5.3 / A7.4 的 P8 交付草案

> 供 P8 implementer 起点用。措辞基于 P4a–P4c 最终形态时须再校准（尤其跨 CLI 子进程强缓解在 P4b 落地后的实际能力边界）。

### A5.3 —— `agate/LIMITATIONS.md` 局限 2 「部分缓解链」段（草案）

在 `LIMITATIONS.md` 局限 2 现有「**现状**：无解……→ ADR-006」之后追加一段（形态对齐局限 3 的「P6.5 独立 Judge 缓解链」）：

> **派发路由缓解链（TAG0034 / RM-AG0060 落地）**：局限 2 的根因是「P3/P4/P6.5 等角色虽是不同 subagent、但通常同一底层模型 → 系统性盲区共享」。派发路由机制在**机制层**给「角色隔离」补上 model / 厂商维度：项目级 `agate-workspace/dispatch-routing.yaml` 按 `(phase, role)` 声明有序跨 CLI 候选链，主 Agent 到阶段派角色时机械查表 → try-and-fall（无 probe，只在 `launch_fail` / `infra_error` / `no_parseable_output` 三类基础设施信号逐级回落）→ 全落空回落默认派发（等价未启用）。两种缓解强度：`cli: native`（同厂商换 model，不脱离原生派发工具）是**弱缓解** —— 同训练系谱盲区基本共享，只省成本 + 一点 failure-mode 多样性，且自动化天花板是「主 Agent 读文件机械横传 model」；`cli:` 另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程）是**强缓解** —— 真正的异源独立视角、可端到端自动化。`dispatch_route` 事件与 `gate_run` 等同构、无差别留痕（哈希链账本 `check-events.py` 审计），两条完整性不变量机械强制（「候选回落 ≠ 状态机 retry」/「gate FAIL 绝不换候选」，理由码枚举无 `gate_fail` 值）防「换模型试到出 green」的完整性洞。**仍非根治** —— 主 Agent 自身的选型判断、以及「机械横传 model」这一步本身，仍缺乏外部约束，与局限 3「主 Agent 判断力是单点故障」同构；且是否真配跨 CLI 候选、配哪些，由使用者按本机现状决定、后果自负（per-machine 机会式，不追求跨机可复现）。

### A7.4 —— `agate/adr.md` 新增 ADR-013（草案）

```markdown
## ADR-013: 派发路由 / gate 生产者无关性（gate 不认谁生产的）

### 状态

已接受（2026-09-09，TAG0034 / RM-AG0060）

### 语境

TAG0034 引入配置驱动的跨 CLI / model 派发（派发路由）：同一阶段的产出可能由
主 Agent 当前平台的原生派发工具生产，也可能由另一个 CLI（claude-code / codex /
opencode）的子进程、或同厂商换 model 的 native 调用生产。这套机制能成立的前提，
是 gate 判定不因「谁生产了这份产出」而改变。

### 决策

**gate 只认产出文件 + exit code，不认谁生产的。** `check-gate.py` /
`check-judge-verdict.py` / `check-p6-provenance.py` 及一切 gate 脚本对跨 CLI / 跨
model 派发的产出**零特殊处理** —— 产出文件落 TASK_DIR（铁律 2/3 不变）、
gate_commands 的 exit code 客观可判，谁跑出来的都一样评。**未来不得为跨 CLI 派发
定制 gate**（不得新增「若产自 codex 则……」式分支）。

派发路由自身的留痕（`dispatch_route` 事件）与 gate 判定解耦：回落理由码枚举只有
`launch_fail` / `infra_error` / `no_parseable_output` 三值，无 `gate_fail`；
`check-events.py` 第 8 条机械拒绝任何非三值理由码。gate FAIL → 同一候选正常阶段
retry，绝不触发换候选。

### 理由

- **与 ADR-002（可判定性）一致**：gate 门槛机器可判定、不依赖主观声明 —— 跨 CLI
  产出与本地产出走同一 exit-code 判定面，是同一原则的直接延伸。
- **与 ADR-006（同源盲区）互补**：ADR-006 记录「同源模型隔离是认知层非真正独立」
  这一上限；派发路由给角色隔离补 model / 厂商维度是其部分缓解（见 LIMITATIONS.md
  局限 2），而「gate 生产者无关」正是这一缓解能安全落地的结构前提。
- **防完整性洞**：若 gate 因生产者而异，「换个模型 / CLI 试到 gate 放行」就成了
  绕过质量门槛的出口。生产者无关 + 回落理由码无 `gate_fail` 两条一起，把这个洞
  机械封死。
- **散文承载不够稳**：该红线目前只写在 `dispatch-protocol.md`「派发编排机制」新节
  的散文里，容易在后续编辑中被稀释；沉淀为 ADR 使其显式、可被 CHECK / 评审引用。

### 后果

- 跨 CLI 派发的产出若质量差 / 不完整，走的是「同候选正常阶段 retry」，不是「换
  候选」——retry 预算、`state_transition`、PAUSED 语义全部不变。
- 新增 gate 脚本时，若其判定逻辑试图区分产出来源，应视为违反本 ADR。
- 关联：RM-AG0060（派发路由 epic）、ADR-002、ADR-006、LIMITATIONS.md 局限 2。
```

---
---

# P4b 批复审（2026-09-10）

> **范围**：TAG0034 P4b 批（static-batch 第 2 批，`complexity: medium`，依赖 P4a）的 `agate/**` 改动增量。P4a 部分的 A1-A7 结论见上文（三轮，终态 aligned）；本节只增量审 **P4b delta**，含 A1 fix 复审轮（round 4）。
> **P4b 增量两轮**：**首轮（2026-09-10）** = A1 MISALIGNED（低严重度，`platform-notes.md` M10 判定表 2 处 reason-code 归类 ≠ `classify_outcome`），A2-A7 delta 全 ALIGNED；**复审轮（round 4，A1 fix，2026-09-10）** = implementer 按 option (a) 改 `classify_outcome`（基础设施信号按 cli 细分对齐 §3.7 / M10）+ 补 3 条断言，逐格核实通过 → **A1 改判 ALIGNED，P4b delta = aligned，P4a+P4b 合并 = aligned**。
> **审查对象**：`git diff HEAD`（HEAD = `d1c2aca` P4a commit）—— `agate/scripts/agate_dispatch_route.py`（首轮 +164/-7；A1 fix 后 +217/-7）、`agate/scripts/agate-dispatch.py`（`_route_main` `form==chain` 端到端分支 + I3 桥接）、`agate/SETUP.md`（M9 新小节）、`agate/platform-notes.md`（M10 新小节）、`agate/dispatch-protocol.md`（评审打回续跑段）、`agate/tests/unit/test_tag0034_p4b.py`（新，首轮 15 例 → A1 fix 后 18 例）。
> **对齐基准**：`P2-design.md` §3.4 / §3.7（判定表）/ §3.9 / §4.1（P4b 批次行）+ `design-dispatch-routing.md` §2.4a（评审打回续跑）+ `P1` BDD-33~36 / BDD-42。
> **DESIGN_GAP**：`P4-implementation-P4b.md` 两条 `[DESIGN_GAP]`，均 `[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）]`：① `_route_main` 端到端时「约定产出文件路径」经 `AGATE_DISPATCH_EXPECT` 环境变量解析、未设则保守回落（宁可回落也不把「无法核实产出」当成功）；② 候选链中段 `cli: native` → `dispatch_once` 返回 `HAS_OUTPUT` 占位（交驱动会话代发）。经核：两条方向与 P2-design 意图一致，且**均不涉及**下方 A1 finding（A1 是 `classify_outcome` 信号表精度 vs `platform-notes.md` M10，与这两条 DESIGN_GAP 无关，原则 6 不适用于 A1）。

`[PROD_NOT_TOUCHED]` —— 仅 worktree 内读取 + 写本报告；未触碰主 checkout 与 `~/.agate`。

## P4b delta 审查结论汇总

| # | 审查项 | P4b delta 首轮 | P4b delta 复审（终结论） |
|---|--------|------|------|
| A1 | 文档→脚本对齐 | MISALIGNED（低严重度） | **ALIGNED**（复审：按 option (a) 修 `classify_outcome` —— 基础设施信号按 cli 细分对齐 §3.7 / M10，`unknown_error.jsonl` → NO_PARSEABLE_OUTPUT、`api_error.json` → INFRA_ERROR，Codex 裸 `type:error` 不回归；补 3 条断言消除 dead fixture；R1 三值 `reason` 未破。逐格核实见 A1 复审段） |
| A2 | 脚本→文档对齐 | ALIGNED | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | ALIGNED | **ALIGNED**（A3a 无新 event 类型 / 枚举；A3b：SETUP 新小节无索引需同步、platform-notes 不在 `check-platform-assumptions.py` 扫描面、tests/README 非硬校验） |
| A4 | 测试覆盖 | ALIGNED | **ALIGNED**（复审轮全量实跑见 A4 复审段 + 文末「附」——仅剩 `test_bdd_37` / `test_bdd_38`（P4c 批次边界 by-design）红；`test_bdd_42` + `test_bdd_50` 转绿；A1 fix 3 断言 passed） |
| A5 | 下游影响 + 文档传播 | ALIGNED | **ALIGNED**（评审打回续跑段平台续接原语在 `> 实现注记：` 块内 → CHECK 14 实跑 PASS；6 个冻结脚本零改动确认；CHANGELOG 待 P8） |
| A6 | 锚点表覆盖 | ALIGNED | **ALIGNED**（P4b 未新增 `check-*.py`，CHECK 9 锚点表无需再动） |
| A7 | 设计原则一致性 | ALIGNED | **ALIGNED**（P4b 未确立新架构决策；A7.4 的 ADR-013 已在 P4a 复审轮 HUMAN_CONFIRMED、落 P8） |

**P4b delta 结论：aligned**（首轮 1 项 A1 MISALIGNED 低严重度，implementer 按 option (a) 修 `classify_outcome` 细分、补断言，复核确认）｜ **P4a+P4b 合并总结论：aligned**

> A5.3 / A7.4 的两条 doc-sync（`LIMITATIONS.md` 局限 2 缓解链 + ADR-013「gate 生产者无关性」）仍为 **P8 交付项**（P4a 复审轮已 HUMAN_CONFIRMED，草案见上文附录），**不阻断 P4b commit**。

---

## P4b 逐项审查

### A1（P4b delta）：文档→脚本对齐 — ALIGNED（首轮 MISALIGNED 低严重度，修复已落地）

**M9 SETUP scaffold 措辞（`agate/SETUP.md` +218~+255）— ALIGNED**

新小节「### 步骤 2-dispatch-routing」逐条核对：机会式启用（不配置 = 逐字节现状）、`dispatch-routing.yaml` 非协议本体 / 全兜底、`tier_bindings:` 按本机现状填 + 探测命令（`command -v` / `claude --help \| grep -- --effort` 能力探测不硬编码版本号 / `models_cache.json` / `opencode models`）、`routes:` 只引用档位名跨机可移植、逐级回落条件、「gate 只认产出文件 + exit code、不认谁生产的」、绕过 flag（`--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check` / `--auto`）、`check-dispatch-routing.py` 校验、OpenCode `cli: native` 命名 subagent 间接路（`agate-route-<tier>`，无则该候选 `launch_fail` 自动回落）。与 `agate_dispatch_route.resolve` / `build_dispatch_command` / `resolve_native_target` 语义逐条一致，与 P2-design §3.4 / §3.6 一致。**ALIGNED**。

**`dispatch-protocol.md` 评审打回续跑段（+558~+571）vs design-note §2.4a — ALIGNED**

新增「**评审打回后的续跑（子进程 / native 两种形式都适用）**」段逐条比对 `design-dispatch-routing.md` §2.4a：
- 「优先走平台官方续接、不重起」= §2.4a 首句 ✓
- 「同 target（cli + model / native 目标 subagent 未变）→ 续接 / 续接失败 / 换 target → 全新派发」= §2.4a「同 target 重做 → 续接」+「fallback 到不同 target → 退化为全新派发」✓
- 「续接产出仍走假完成校验（D2），且本就在人的评审循环里」= §2.4a「续接后的产出仍走假完成校验（D2）+ 本来就在评审循环里」✓
- 「**续接失败无客观信号是已知缺口** —— 按『续接优先、重起兜底』处理，**不假装解决**」= §2.4a「已知缺口：续接失败没有像探测失败那样的客观信号（外部评审 W1）……本设计不假装解决了这条，如实登记为缺口」✓（语义级一致：不掩盖、不假装机械可判定）
- 「**不需要实现续接的自动化**（人在评审循环里）；决策层留 hook 位给未来，不落自动续接逻辑」= §2.4a 精神（续接是「这次 retry 怎么执行」的优化，不改 `retries[Pn]`）+ P2-design §3.9 hook 位 ✓

代码侧：`_route_main` / `try_and_fall` / `dispatch_once` **未实现任何自动续接逻辑**（`grep -n "resume\|followup\|--resume" agate/scripts/agate_dispatch_route.py agate/scripts/agate-dispatch.py` 零命中）—— 与「不落自动续接逻辑、只留 hook 位」一致。**ALIGNED**。

**M10 `platform-notes.md` 跨 CLI 结构化输出判成败字段表 vs `classify_outcome` / `dispatch_once` — MISALIGNED（低严重度）**

新小节「## 跨 CLI 子进程结构化输出判成败字段（派发路由 / TAG0034）」的三平台判定表，逐行对照 `agate_dispatch_route.classify_outcome`（P4a 代码，P4b 未改）+ `dispatch_once`（P4b 新）实际行为：

| 判据 | M10 表声明 | `classify_outcome` 实际（实跑核实） | 判定 |
|---|---|---|---|
| Codex `turn.completed` 且无 `turn.failed`/顶层 `type:error` + 产出文件 | HAS_OUTPUT | `_SUCCESS_SIGNALS` 含 `turn.completed`；`files` 非空 → HAS_OUTPUT | ✓ |
| Codex `turn.failed` / 顶层 `{"type":"error","status":...}` | INFRA_ERROR | `_INFRA_SIGNALS` 含 `turn.failed` / `'"type":"error"'` → INFRA_ERROR（`turn_failed_exit0.jsonl` 即便 exit 0 亦判 INFRA_ERROR，`test_bdd_34` 锁定） | ✓ |
| Codex item 级 `status:"failed"`（携 `exit_code`）+ 整轮 `turn.completed` | HAS_OUTPUT（永不换候选） | `item_failed_turn_completed.jsonl` → HAS_OUTPUT（`test_bdd_35` 锁定，`reason is None`） | ✓ |
| OpenCode `step_finish` + `part.reason == "stop"` + text part + 产出文件 | HAS_OUTPUT | `_SUCCESS_SIGNALS` 含 `step_finish` / `'"reason":"stop"'`；+ `files` → HAS_OUTPUT | ✓ |
| OpenCode `{"type":"error","error":{"name":"ProviderAuthError",...}}` | INFRA_ERROR（`infra_error`） | `_INFRA_SIGNALS` 含 `ProviderAuthError` + `'"type":"error"'` → INFRA_ERROR（`test_bdd_36` 锁定） | ✓ |
| **OpenCode `{"type":"error","error":{"name":"UnknownError",...}}`** | **NO_PARSEABLE_OUTPUT（`no_parseable_output`）** | `_INFRA_SIGNALS` 含**裸子串 `'"type":"error"'`** → `unknown_error.jsonl` → **INFRA_ERROR / `infra_error`**（实跑 exit 0 与 exit 1 均如此）。夹具 `tag0034_opencode/unknown_error.jsonl` **存在但无任何断言** | **✗ 不一致** |
| **OpenCode 纯空返回（无 step_finish / 无 text / 无 error 事件）** | **NO_PARSEABLE_OUTPUT** | 退出码 0 → NO_PARSEABLE_OUTPUT（`test_bdd_36` 用 `exit_code=0` 锁定）；**退出码非 0 → INFRA_ERROR**（`classify_outcome` 第 2 分支：`exit_code != 0 and not files and not _SUCCESS_SIGNALS`） | ⚠ 部分（退出码 0 一致；非 0 不一致，但真机「无 error 事件」空返回退出码待核） |
| **Claude Code `stop_reason == "error"` / `api_error_status` 非 null（如 401）** | **INFRA_ERROR** | `api_error.json`（`stop_reason:"error"`, `is_error:true`, `api_error_status:401`, `type:"result"`）→ `_INFRA_SIGNALS` **无对应信号**（非 `"type":"error"`、无 auth 串）；退出码 0 → **NO_PARSEABLE_OUTPUT**（实跑核实）。夹具 `tag0034_claude_code/api_error.json` **存在但无断言** | **✗ 不一致（退出码 0 时）** |
| Claude Code `stop_reason == "end_turn"` + `result` 非空 + 产出文件 | HAS_OUTPUT | `_SUCCESS_SIGNALS` 含 `'"stop_reason":"end_turn"'`；+ `files` → HAS_OUTPUT（`test_bdd_33` 锁定；`presence_parse_ok` 填 `produced_files`） | ✓ |
| Claude Code `stop_reason == "end_turn"` 但 `result` 空 + 产出文件缺失或空 | NO_PARSEABLE_OUTPUT | `empty_result.json` + `files` 空 → NO_PARSEABLE_OUTPUT（`test_bdd_33` 锁定） | ✓ |

**MISALIGNED 详情（两处，同性质）**：

1. **OpenCode `UnknownError`**：P2-design §3.7 判定表（对齐基准）**显式区分** —— `ProviderAuthError` → `infra_error`，`{"type":"error","name":"UnknownError"}` → `no_parseable_output`（§3.7 表 OpenCode NO_PARSEABLE 列 + §3.7 末「纯空返回（无 error 事件也无 text）→ no_parseable_output」）。P4b `platform-notes.md` M10 **忠实转写了 §3.7 的这一区分**。但 P4a `classify_outcome` 的 `_INFRA_SIGNALS` 含**裸子串 `'"type":"error"'`**，把任何结构化 `{"type":"error",...}` 事件（含 `UnknownError`）都吞进 INFRA_ERROR —— 即代码比 §3.7 / M10 **更粗**。
2. **Claude Code `stop_reason == "error"` / `api_error_status`**：M10 把「`api_error_status` 非 null / `stop_reason == "error"`」列入 INFRA_ERROR。`classify_outcome` 无对应信号（`_INFRA_SIGNALS` 是 `"not logged in"` / `"Invalid API key"` / `"AuthenticationError"` / `"turn.failed"` / `'"type":"error"'` 等子串，均不匹配 `api_error.json` 的 `"type":"result"` + `"api_error_status":401` + `"stop_reason":"error"`）；退出码 0 时 → 无产出文件 → NO_PARSEABLE_OUTPUT。

**影响边界（务必与「必须拦截」的普通 MISALIGNED 区分）**：两处的**路由行为完全一致** —— 均回落到下一候选（`INFRA_ERROR` 与 `NO_PARSEABLE_OUTPUT` 都在 `_FALLBACK_KINDS` 白名单内）、`reason` 均为合法三值枚举、均非 `gate_fail`、两条完整性不变量（「候选回落 ≠ 状态机 retry」/「gate FAIL 绝不换候选」）**不受影响**。差异只在：① `dispatch_route` 事件账本记录的 `candidates_tried[].reason` 标签（`infra_error` vs `no_parseable_output`）；② 运维读账本 + 读 M10 表复盘「某候选为什么回落」时的理解会被误导。`platform-notes.md` ∈ `agate/**`（SELF-GATE 触发文件），M10 表是可测断言，两条相关夹具（`unknown_error.jsonl` / `api_error.json`）**存在但闲置**（仅列在 `test_tag0034_subprocess.py` 文件头注释，无断言）。

**建议（修复方向，主 Agent 择一）**：
- **(a) 修脚本（faithful，§3.7 是对齐基准且显式细分）**：收紧 `classify_outcome` —— OpenCode 仅具名 infra 错误（`ProviderAuthError` / `AuthenticationError`）→ INFRA_ERROR，裸 `UnknownError` / 无具名结构化 error → NO_PARSEABLE_OUTPUT；Claude Code `is_error: true` / `stop_reason == "error"` / `api_error_status` 非 null → INFRA_ERROR。并用现存闲置夹具 `unknown_error.jsonl` / `api_error.json` 补断言（消除 dead fixture）。
- **(b) 修文档（若认定粗分类可接受）**：改 `platform-notes.md` M10 表与代码一致（任意结构化 `{"type":"error"}` 事件 → `infra_error`；Claude Code `is_error:true` 且退出码非 0 → `infra_error`，否则 `no_parseable_output`），并在 `P2-design.md` §3.7 标注 UnknownError / api_error_status 的细分留待 P4c/后续迭代（或补一条 `[DESIGN_GAP]`）。
- 修完重跑 `test_tag0034_subprocess.py` + `test_tag0034_p4b.py` + 全量 pytest + `check-protocol-consistency.py --strict-errors-only`，重审本节 A1。

**首轮结论：MISALIGNED（低严重度）**。

---

#### A1 复审（round 4，2026-09-10）：修复已落地并逐格核实 — ALIGNED

**修复方式**：implementer 按 **option (a) 修脚本**（`agate/scripts/agate_dispatch_route.py` 的 `classify_outcome`，`git diff` +217/-7）—— 基础设施失败信号**按 cli 细分**对齐 P2-design §3.7 判定表 / `platform-notes.md` M10：

- 从通用 `_INFRA_SIGNALS` **移除裸子串 `'"type":"error"'` / `'"type": "error"'`**（保留 `turn.failed` / `ProviderAuthError` / `AuthenticationError` / `not logged in` / `Invalid API key` / `ECONNREFUSED` / `ENOTFOUND`）。
- 新常量 `_BARE_TOP_ERROR_SIGNALS = ('"type":"error"', '"type": "error"')` —— **仅 `cli == "codex"`** 命中时 → INFRA_ERROR（Codex MV3 顶层 `{"type":"error","status":400}`）。
- 新常量 `_INFRA_SIGNALS_CLAUDE_ONLY = ('"stop_reason":"error"', …, '"is_error":true', …)` + `_claude_api_error(text)`（`api_error_status:` 后跟非 null 数字）—— **仅 `cli ∉ {codex, opencode}`** 命中时 → INFRA_ERROR（Claude Code §3.7 INFRA 行；夹具 `api_error.json`）。
- 新分支 **2b**：`cli == "opencode"` 且顶层 `{"type":"error"}` 而**通用集未命中**（即无 `ProviderAuthError` 等具名）→ NO_PARSEABLE_OUTPUT，**排在「非零退出兜底」（2c）之前** —— 故 `unknown_error.jsonl` 即便 exit 1 亦判 NO_PARSEABLE_OUTPUT（MV6b `UnknownError`）。
- `classify_outcome` 之外的 P4a 函数（`resolve` / `load_config` / `write_dispatch_route_event` / `try_and_fall` I1/I5）+ `check-events.py` 第 8 条 + 哈希链 **未动**。

**逐格核实（本轮独立实跑 `python3 -c "...classify_outcome..."` + `pytest`）**：

| 判据 | M10 表声明 | `classify_outcome` 复审实跑 | 判定 |
|---|---|---|---|
| **OpenCode `{"type":"error"...UnknownError...}`**（`unknown_error.jsonl`） | NO_PARSEABLE_OUTPUT / `no_parseable_output` | exit 0 与 exit 1 **均 → NO_PARSEABLE_OUTPUT / `no_parseable_output`**（分支 2b，早于 2c 兜底） | **✓ 一致** |
| OpenCode `ProviderAuthError`（`provider_auth_error.jsonl`） | INFRA_ERROR / `infra_error` | → INFRA_ERROR / `infra_error`（`_INFRA_SIGNALS` 具名命中，**不回归**） | ✓ |
| OpenCode 纯空返回（`empty_return.jsonl`） | NO_PARSEABLE_OUTPUT | exit 0 → NO_PARSEABLE_OUTPUT（`test_bdd_36` 锁定）；exit 非 0 → INFRA_ERROR（2c 兜底，真机「无 error 事件」空返回退出码待核，非 §3.7 钉死项） | ✓（exit 0）/ ⚠ 观察（exit 非 0，同首轮，非阻断） |
| **Claude Code `stop_reason=="error"` + `api_error_status:401` + `is_error:true`**（`api_error.json`） | INFRA_ERROR | exit 0 与 exit 1 **均 → INFRA_ERROR / `infra_error`**（`_INFRA_SIGNALS_CLAUDE_ONLY` + `_claude_api_error`） | **✓ 一致** |
| Claude Code `stop_reason=="end_turn"` 但 `result` 空（`empty_result.json`） | NO_PARSEABLE_OUTPUT | → NO_PARSEABLE_OUTPUT（`test_bdd_33` 锁定，**不回归** —— `is_error` 缺省 / 无 `api_error_status`） | ✓ |
| Claude Code `end_turn` + 产出文件（`ok_end_turn.json`） | HAS_OUTPUT | → HAS_OUTPUT（不回归） | ✓ |
| **Codex 裸顶层 `{"type":"error","status":400}`**（无 `turn.failed`） | INFRA_ERROR | → INFRA_ERROR / `infra_error`（`_BARE_TOP_ERROR_SIGNALS` for `cli=="codex"`，**不依赖退出码**） | **✓ 一致（守不回归）** |
| Codex `turn.failed`（`turn_failed_exit0.jsonl`，exit 0） | INFRA_ERROR | → INFRA_ERROR（`_INFRA_SIGNALS` `turn.failed`，`test_bdd_34` 锁定，不回归） | ✓ |
| Codex `item.status:"failed"` + 整轮 `turn.completed`（`item_failed_turn_completed.jsonl`） | HAS_OUTPUT（turn 层为准） | → HAS_OUTPUT / `reason is None`（`test_bdd_35` 锁定，不回归） | ✓ |
| Codex `turn.completed` + 产出文件（`turn_completed_ok.jsonl`） | HAS_OUTPUT | → HAS_OUTPUT（不回归） | ✓ |

**R1 三值 `reason` 未破**：所有分支产出的 `reason` ∈ `{launch_fail, infra_error, no_parseable_output}` ∪ `{None（HAS_OUTPUT）}`，**无 `gate_fail`**（`grep gate_fail agate/scripts/agate_dispatch_route.py` 仅出现在 docstring/注释否定表述）。`_FALLBACK_KINDS` 白名单 + `try_and_fall` I1/I5 守卫未改。**I2 边界未破**：分支 2b 是**信号子串匹配**（`'"type":"error"'`），非对产出文件的结构完整度解析 —— 未把结构判断塞进 NO_PARSEABLE_OUTPUT 分支；`test_classify_outcome_no_parseable_branch_has_no_structure_check` 仍绿。

**断言到位（dead fixture 消除）**：`test_tag0034_p4b.py` 补 3 例（18 例，56 asserts）：`test_classify_claude_code_api_error_is_infra_error`（`api_error.json` exit 0 → `infra_error`）/ `test_classify_opencode_unknown_error_is_no_parseable_output`（`unknown_error.jsonl` **exit 1** → `no_parseable_output`）/ `test_classify_codex_bare_top_error_still_infra_error`（Codex 裸 `type:error` exit 0 → `infra_error`）—— 三例本轮实跑 passed；`unknown_error.jsonl` / `api_error.json` 不再是闲置夹具。

**`platform-notes.md` M10 表逐格 vs `classify_outcome`**：现**逐格一致**（上表 10 行全 ✓，仅 OpenCode 纯空返回 exit 非 0 一格为「观察项」—— 非 §3.7 钉死区分、`test_bdd_36` 用 exit 0 锁定、真机退出码待核，与首轮同判、不阻断）。

**结论：ALIGNED**（首轮 MISALIGNED 低严重度 → 复审轮修脚本细分对齐 + 补断言，逐格核实通过；R1 三值 `reason` / I2 边界 / P4a 函数 + 第 8 条 + 哈希链均未破）。

---

### A2（P4b delta）：脚本→文档对齐 — ALIGNED

| P4b 新增/改动脚本行为 | 文档对应 | 判定 |
|---|---|---|
| `dispatch_once(candidate, ctx, *, effort_supported, expected_output, required_anchors, run, timeout_s, task_dir)` 端到端单候选派发 | `agate_dispatch_route.py` docstring 逐行 + `dispatch-protocol.md` 新节 step 3「try-and-fall（无 probe，第一个动作即把真实 dispatch-context 派给首选候选）」+ `platform-notes.md` M10 判定表（判据来源）+ P2-design §3.1 step 2.3 / §3.7 | ALIGNED（判据精度问题见 A1；A2 只核「行为是否被写出来」= 是） |
| `_route_main` `form == "chain"` 且首候选子进程形态 → 端到端 `try_and_fall`；首候选 native → 仍只输出路由计划 JSON | `_route_main` docstring（「首候选为 native 时仍只输出路由计划 JSON…与 P4a DESIGN_GAP 一致」）+ `dispatch-protocol.md` 新节 step 2-3 + `P4-implementation-P4b.md` `[DESIGN_GAP_REVIEWED]` | ALIGNED |
| stdout JSON 增 `final` / `tried` 字段（子进程分支） | P4a 契约「只增不改」—— 既有键 `cli`/`model`/`effort`/`form`/`dispatch_context`/`chain` 未变，`final`/`tried` 为新增可选键；`_route_main` docstring 描述。stdout JSON 是 CLI 内部契约（非协议语义），P2-design §3.1 step 2.6 示例形态；`dispatch_route` 事件的 `candidates_tried`/`final`（协议语义面）由 `dispatch-protocol.md` 新节 step 5 + P2-design §3.8 承载 | ALIGNED（观察项：stdout JSON 新键未逐字写进协议文档，但属实现细节，事件面已覆盖） |
| `routed_away_verdict_location(cli)` 恒 `"TASK_DIR"` | docstring + `platform-notes.md` M10「routed-away judge 的 verdict 落点」段（verdict + 证据仍写 `TASK_DIR`，铁律 2/3 不变，两校验器零改动平台无关通过）+ P2-design §10 BDD-42 | ALIGNED |
| `DispatchContractError` / `presence_parse_ok` / `_default_subprocess_run` / `_FALLBACK_KINDS` / `_SUBPROCESS_CLIS` | 均 `agate_dispatch_route.py` docstring + 模块级注释（含 P4a-review I1/I2/I5 溯源）；`presence_parse_ok` 的 presence 级语义在 `platform-notes.md` M10「判据只到 presence 级」句 + P2-design §3.7 N7 | ALIGNED（内部契约守卫，非协议语义面，不要求写进协议文档） |

无「脚本做了但文档完全没写」的裸露行为。**ALIGNED**。

---

### A3（P4b delta）：一致性连锁 + 反向传播 — ALIGNED

**A3a（连锁）**：P4b 未新增 event 类型（`dispatch_route` 是 P4a 已有；P4b 只是让 `_route_main` 子进程分支端到端**写**它，经 I3 适配层闭包桥接到 `write_dispatch_route_event`）。`check-events.py` 第 1-8 条 + 哈希链 **零改动**（`git diff HEAD --name-only` 不含 `check-events.py`；`check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0 / 14 行 / 哈希链完整）。无「已知 event 类型」枚举清单需再动。**ALIGNED**。

**A3b（反向传播：应被 P4b 影响但未在 diff 中的文件）**：

| 应被影响文件 | 影响到了没 | 判定 |
|---|---|---|
| `agate/WORKFLOW.md` / onboarding 索引 —— M9 SETUP 新增「### 步骤 2-dispatch-routing」小节 | 不需改 —— `SETUP.md` 无 TOC / 索引，「### 步骤 2-*」小节（DSH / Codex / dispatch-routing）是内联并列，无任何 `WORKFLOW.md` / `AGENTS.md` 索引枚举它们（`grep "步骤 2-" WORKFLOW.md AGENTS.md` 零命中）；先例「### 步骤 2-Codex」（TAG0033）亦未加 `WORKFLOW.md` 引用 | ALIGNED |
| `check-platform-assumptions.py` 扫描面 —— M10 `platform-notes.md` 新小节含 `claude` / `codex` / `opencode` / `--dangerously-*` 等 | 不需改 —— `check-platform-assumptions.py` 仅扫 `*.bats` / `*.bash` / `*.sh` / `*.py`（docstring L15），**不扫 `.md`**；且 `platform-notes.md` 是 CHECK 14 `_MD14_WHOLE_FILE_EXEMPT`（平台适配权威源），平台名在此处 by-design 合法 | ALIGNED |
| CHECK 9 锚点表 —— M10 `platform-notes.md` 新小节 | 不需改 —— CHECK 9 锚点是 gate 脚本对齐锚点，`platform-notes.md` 非 gate 脚本；无锚点要求新小节 | ALIGNED |
| `agate/tests/README.md` per-script 测试计数表 —— 新增 `test_tag0034_p4b.py` | 观察项（非硬校验）—— `test_tag0030_assertions.py::BDD-19` 只校 tests/README「何时更新」节措辞；`count-tests.sh` 只守特定被引用路径的用例数；tests/README.md 现表**无任何 `test_tag0034_*` 行**（P3 的 6 个模块亦缺），P4a 复审轮已按同口径列为观察项、未判 MISALIGNED。P4b 沿用 | ALIGNED（观察项，与 P4a 一致） |
| `dispatch-protocol.md` 续跑段 → 角色文件 / 模板 | 不需改 —— 续跑段是「派发路由」子节内「这次 retry 怎么执行」的机制细节，不改任何角色 prompt / 派发模板；design-note §2.4a 已同源 | ALIGNED |
| 6 个冻结脚本 + `agate-cmdstream-*.py` + `agate-dispatch.py` 渲染路径 | `git diff HEAD --name-only` 确认**均不在 diff 内**（仅 `agate_dispatch_route.py` / `agate-dispatch.py` 的 `_route_main` / `SETUP.md` / `platform-notes.md` / `dispatch-protocol.md` / `test_tag0034_p4b.py` + 任务 `gate-events.jsonl` 的 P4a commit 留痕 2 行）；`_default_subprocess_run` 内 tmux 包裹 + RM-AG0055 命令流阈值卡死检测的接入点仅以注释标出、未真接（归 P4c），`agate-cmdstream-adapters.py` 零改动 | ALIGNED |

**ALIGNED**。

---

### A4（P4b delta）：测试覆盖 — ALIGNED

**P4b delta 复审轮全量 pytest 实跑（A1 fix 后，本次审查执行，2026-09-10）**：

```
$ python3 -m pytest agate/tests/ -q --tb=no
（worktree 根 /home/kity/oclab/agateon/.worktrees/agate-TAG0034）

=========================== short test summary info ============================
FAILED agate/tests/unit/test_tag0034_tmux.py::test_bdd_37_which_tmux_decides_wrap_or_bare
       - AttributeError: module 'agate_dispatch_route' has no attribute 'build_subpr...'
FAILED agate/tests/unit/test_tag0034_tmux.py::test_bdd_38_countdown_and_no_force_kill_with_client
       - AttributeError: module 'agate_dispatch_route' has no attribute 'tmux_cleanu...'
2 failed, 1611 passed, 2 skipped in 161.50s (exited with code 0)
```

**計數：passed 1611 / failed 2 / skipped 2**（P4b delta 首轮 = passed 1608 / failed 2；A1 fix 补 `test_tag0034_p4b.py` 3 例（15 → 18）→ passed +3。P4a 复审轮 = passed 1592 / failed 3）。

**failed 2 条全部为 P4c 批次边界 by-design**（同首轮，A1 fix 未引入任何新失败）：`test_bdd_37`（`build_subprocess_launch` 未实现）+ `test_bdd_38`（`tmux_cleanup_action` 未实现）—— P2-design §3.10 / §4.1「tmux 观测层归 P4c、可整体切除」；`P4-implementation-P4b.md` 明文「tmux 观测层（P4c）不做——`test_bdd_37/38` 按批次边界保持红」。

---

**P4b delta 首轮全量 pytest（A1 fix 前，供对照）**：`2 failed / 1608 passed / 2 skipped`（164.85s）—— 同样 2 red 为 `test_bdd_37/38`（P4c）。**A1 fix 未引入任何新失败、未破坏任何既有绿**（passed 净增 3 = 新增 3 条 A1 断言）。

**P4b 新逻辑边界覆盖评估**（`test_tag0034_p4b.py` 18 例 / 56 asserts，含 A1 fix 补的 3 例）：
- `dispatch_once` 端到端 6 例：native 占位不 spawn / codex `turn.completed`+产出文件 → HAS_OUTPUT / opencode `ProviderAuthError` → INFRA_ERROR / 空返回（exit 0）→ NO_PARSEABLE_OUTPUT / spawn OSError → LAUNCH_FAIL / `wait` 超时 → INFRA_ERROR（N6）—— 全绿。
- `presence_parse_ok` 变体：缺失 / 空 / frontmatter 未闭合 / 缺锚点 / OK / 无 frontmatter —— 全绿。
- I2：空产出文件 → NO_PARSEABLE_OUTPUT；`classify_outcome` 的 NO_PARSEABLE_OUTPUT 分支无结构完整度判断（垃圾但非空产出 → HAS_OUTPUT）—— `test_classify_outcome_no_parseable_branch_has_no_structure_check` 锁死 R1 CRITICAL 边界。
- I1：非契约 kind / `None` kind → `DispatchContractError`；I1 不误伤（三类基础设施 kind 仍正常回落，`reasons` 序列断言）。
- I5：回落 kind 携非法 `reason`（`gate_fail`）→ `DispatchContractError`。
- I3：位置回调 ↔ kw-only 写入器适配层桥接落 1 条合法 `dispatch_route` 事件（`candidates_tried` 失败候选 `reason == "infra_error"`）。
- BDD-42：`routed_away_verdict_location` 恒 `"TASK_DIR"`。
- **A1 fix 补 3 例（消除 dead fixture）**：`test_classify_claude_code_api_error_is_infra_error`（`api_error.json` exit 0 → `infra_error`）/ `test_classify_opencode_unknown_error_is_no_parseable_output`（`unknown_error.jsonl` **exit 1** → `no_parseable_output`）/ `test_classify_codex_bare_top_error_still_infra_error`（Codex 裸 `type:error` exit 0 → `infra_error`）—— 全绿。
- P3 既有断言未改：`test_tag0034_tryfall.py`(10) / `test_tag0034_subprocess.py`(BDD-33~36) 等仍绿。

**结论：ALIGNED**（P4b 新逻辑覆盖充分含 A1 fix 断言；复审轮全量实跑 `1611 passed / 2 failed / 2 skipped` —— 2 red 全为 P4c 批次边界 by-design，A1 fix 零回归）。

---

### A5（P4b delta）：下游影响 + 文档传播 — ALIGNED

**A5.1 CHECK 14 护栏 1（协议语义叙述面不裸露平台名）— ALIGNED（实跑核实）**

`dispatch-protocol.md` 评审打回续跑段的平台续接原语（`claude -p --resume <id>` / `codex exec resume <id>` / `opencode run -s <id>` / Codex `followup_task` / OpenCode 命名 subagent 续接 / Claude Code 续接原语待核实）**全部放在 `> 实现注记：` blockquote 块内**。核 `check-protocol-consistency.py` CHECK 14 逻辑（L1195 `_NOTE_MARKER_RE = re.compile(r"^>\s*实现注记：")`，L1248「节内任一行带 `> 实现注记：` → 整节豁免」）：`### 0. 派发路由` 节内含 `> 实现注记：` 标记行 → 整节豁免。段落正文（bullet 列表）本身亦无裸平台名（用「平台官方续接」「平台续接原语」「目标 subagent」）。**实跑确认：`check-protocol-consistency.py --strict-errors-only` → `✅ PASS CHECK 14 md 叙述段落平台名扫描` + `✅ PASS CHECK 15` + exit 0（329 WARNING / 0 ERROR）**。护栏 1 合规成立。**ALIGNED**。

**A5.2 CHANGELOG — 待 P8（非 MISALIGNED）**

P4b 同为协议语义变更（`agate dispatch route` 端到端 + M9/M10 协议文档小节 + 评审打回续跑段）。`check-changelog.py` 仅 P8 触发（P4a 轮已核实：`pre-commit-gate.py:480` `phase == "P8"` / `WORKFLOW.md:344` 表 1.6「仅 P8 检查，P1-P7 不触发」）。CHANGELOG 待 P8 统一补，**不判 MISALIGNED**。

**A5.3 冻结脚本 / 向后兼容 — ALIGNED**

`git diff HEAD --name-only` 确认 `agate/rules/phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py` / `agate-cmdstream-adapters.py` / `agate-dispatch.py` 既有渲染路径（`_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER` / `generated_by` / `form == "default"` 分支）**均零改动**。`try_and_fall` / `write_dispatch_route_event` / `classify_outcome` / `resolve` / `load_config` 的 P4a 签名与行为未变（P4b 只在 `try_and_fall` 加白名单守卫 I1/I5 —— 今日行为等价，`classify_outcome` 枚举闭合下不改判定，仅把「不可能的 kind」从静默变大声失败）。`dispatch_route` 事件对既有账本审计向后兼容（既有任务无该事件 → `check-events.py` 第 8 条分支不进入）。**ALIGNED**。

---

### A6（P4b delta）：锚点表覆盖 — ALIGNED

P4b **未新增任何 `check-*.py`**（`routed_away_verdict_location` / `dispatch_once` / `presence_parse_ok` 等均在 helper 模块 `agate_dispatch_route.py` 内，非独立 gate 脚本）。CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` 无需再动（P4a 复审轮补的 `check-dispatch-routing.py` 条目仍成立、`test_sg_6` 保持绿）。`dispatch_route` 理由码枚举锚点粒度由 `check-events.py` 既有锚点覆盖（P4a 已核）。**ALIGNED**。

---

### A7（P4b delta）：设计原则一致性 — ALIGNED

P4b **未确立新架构决策**：M5 端到端 spawn 是 P2-design §3.1/§3.7 既定机制的落地；I1 白名单化 / I2 presence-parse 落位 / I3 签名桥接均为 P4a-review 已提出的加固项（INFORMATIONAL → 本批做实），不引入新原则。评审打回续跑「续接优先、重起兜底、不假装解决续接失败无客观信号」与 design-note §2.4a + 局限 3「主 Agent 判断力单点故障、不假装机械可判定」的诚实叙述一致。A7.4 的 ADR-013「派发路由 / gate 生产者无关性」已在 **P4a 复审轮 HUMAN_CONFIRMED、落 P8 收尾批**（草案见上文附录），P4b 无新增。`dispatch_once` 对 native / default / 未知 cli 返回 HAS_OUTPUT 占位（不 spawn）、中段 native 候选同占位 —— 对应 `[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）]`，与「`cli: native` 弱缓解、自动化天花板 = 主 Agent 机械横传 model」（`dispatch-protocol.md` 新节 + ADR-013 草案）一致。**ALIGNED**。

---

## P4b 闭环规则（复审轮终态）

| 结论态 | 项 | 状态 |
|---|---|---|
| ALIGNED | A1（P4b delta，首轮 MISALIGNED 低严重度 → 修复已落地） | 通过。修复 = implementer 按 **option (a)** 改 `classify_outcome`（基础设施信号按 cli 细分对齐 §3.7 / M10 —— 通用集去裸 `'"type":"error"'`；`_BARE_TOP_ERROR_SIGNALS` 仅 codex；`_INFRA_SIGNALS_CLAUDE_ONLY` + `_claude_api_error` 仅 claude-code；分支 2b opencode 裸 error 无具名 → NO_PARSEABLE_OUTPUT 早于 2c 兜底）+ 补 3 条断言消除 dead fixture。复核确认：`unknown_error.jsonl` → NO_PARSEABLE_OUTPUT、`api_error.json` → INFRA_ERROR、Codex 裸 `type:error` 不回归；M10 表逐格 vs 代码一致；R1 三值 `reason` / I2 边界 / P4a 函数 + 第 8 条 + 哈希链均未破；全量 pytest `1611 passed / 2 failed`（2 red = P4c by-design，零回归）；`check-protocol-consistency.py --strict-errors-only` exit 0（CHECK 1~15 PASS）。 |
| ALIGNED | A2 / A3 / A4 / A5 / A6 / A7（P4b delta） | 通过。P4b 全量 pytest 仅剩 `test_bdd_37` / `test_bdd_38`（P4c 批次边界 by-design）。 |
| （P8 交付项，非 P4b 阻断） | A5.3 / A7.4（P4a 复审轮遗留） | 两条 doc-sync（`LIMITATIONS.md` 局限 2 缓解链 + ADR-013）已 HUMAN_CONFIRMED、落 P8 收尾批，草案见上文附录。**不阻断 P4b commit**。 |

**P4b delta 总结论：aligned**（首轮 1 项 A1 MISALIGNED 低严重度，implementer 按 option (a) 修脚本细分 + 补断言，复核逐格通过）。

**P4a + P4b 合并总结论：aligned** —— P4a 三轮终态 aligned（A5.3/A7.4 已 HUMAN_CONFIRMED、落 P8）；P4b delta 四轮（首轮 misaligned → A1 fix 复审 aligned）。P4b 其余 A2-A7 delta 全 ALIGNED，全量 pytest 仅剩 `test_bdd_37/38`（P4c 批次边界 by-design）red。**可 P4b commit**（commit message 带 `self-gate-review: docs/reviews/agate-alignment-review-2026-09-09-TAG0034.md`）。A5.3 / A7.4 的两条 doc-sync 为 P8 交付项、不阻断 P4b commit。

---

## 附：P4b 轮补充实跑（本次审查执行，2026-09-10）

### A1 fix 复审轮（终态）

- `python3 -m pytest agate/tests/ -q --tb=no` → **2 failed / 1611 passed / 2 skipped**（161.50s，exit 0）；2 red = `test_bdd_37` / `test_bdd_38`（P4c 批次边界 by-design）；A1 fix 零回归（passed 1608 → 1611，净增 3 = 新增 3 条 A1 断言）。
- `python3 -m pytest agate/tests/unit/test_tag0034_p4b.py agate/tests/unit/test_tag0034_subprocess.py agate/tests/unit/test_tag0034_tryfall.py agate/tests/regression/test_tag0034_zero_change.py agate/tests/unit/test_check_events.py -q` → **49 passed**（含 A1 fix 3 断言 + R1/I2 边界 + 回归护栏）。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0；**CHECK 1~15 全 PASS**；329 WARNING / 0 ERROR。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py` → All checks passed。
- `python3 -c "...classify_outcome..."` 逐夹具实跑（A1 逐格核实依据）：`unknown_error.jsonl` (opencode) → **NO_PARSEABLE_OUTPUT/no_parseable_output**（exit 0 与 1 均）；`provider_auth_error.jsonl` (opencode) → INFRA_ERROR/infra_error（不回归）；`api_error.json` (claude-code) → **INFRA_ERROR/infra_error**（exit 0 与 1 均）；`empty_result.json` (claude-code) → NO_PARSEABLE_OUTPUT（不回归）；Codex 裸 `{"type":"error","status":400}`（无 turn.failed）→ **INFRA_ERROR**（不回归）；`turn_failed_exit0.jsonl` → INFRA_ERROR（不回归）；`item_failed_turn_completed.jsonl` + 产出文件 → HAS_OUTPUT（不回归）。
- `git diff HEAD -- agate/scripts/agate_dispatch_route.py` → +217/-7（首轮 +164/-7；A1 fix +53：`_BARE_TOP_ERROR_SIGNALS` / `_INFRA_SIGNALS_CLAUDE_ONLY` / `_claude_api_error` + step 2 按 cli 细分 + 2b 分支）。`classify_outcome` 之外的 P4a 函数 + `try_and_fall` I1/I5 未再改。

### A1 fix 前（首轮，供对照）

- `python3 -m pytest agate/tests/ -q --tb=no` → **2 failed / 1608 passed / 2 skipped**（164.85s，exit 0）；2 red = `test_bdd_37` / `test_bdd_38`（P4c）。
- `check-protocol-consistency.py --strict-errors-only` → exit 0；CHECK 1~15 PASS（含 `✅ PASS CHECK 14` / `✅ PASS CHECK 15`）；329 WARNING / 0 ERROR。
- `check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（14 行，哈希链完整，ts 单调，judge 轮次×0）。
- `git diff HEAD --name-only`（HEAD = `d1c2aca` P4a commit）→ `agate/SETUP.md` / `agate/dispatch-protocol.md` / `agate/platform-notes.md` / `agate/scripts/agate-dispatch.py` / `agate/scripts/agate_dispatch_route.py` / `agate/tests/unit/test_tag0034_p4b.py`（未跟踪）/ 任务 `gate-events.jsonl`（P4a commit 留痕 +2 行）—— 6 个冻结脚本 + `agate-cmdstream-*.py` + `check-events.py` + `check-dispatch-routing.py` + `dispatch-tiers.yaml` **均不在 diff 内**（回归硬约束成立）。
- `grep -n "resume\|followup\|--resume" agate/scripts/agate_dispatch_route.py agate/scripts/agate-dispatch.py` → 零命中（续接自动化未落地，与「只留 hook 位」一致）。

---
---

# P4c 批复审（2026-09-10）

> **范围**：TAG0034 P4c 批（static-batch 第 3 批，`complexity: low`，依赖 P4b，**可整体切除**）的 `agate/**` 改动增量。P4a / P4b 的 A1-A7 结论见上文；本节只增量审 **P4c delta**。
> **审查对象**：`git diff HEAD`（HEAD = `99a4c19` P4b commit）—— `agate/scripts/agate_dispatch_route.py`（+201/-4：新增 tmux 观测层纯逻辑 helper `build_subprocess_launch` / `tmux_cleanup_action` + IO helper `_maybe_tmux_wrap` / `_tmux_teardown` / `_tmux_collect` + `_default_subprocess_run` 的 tmux 包裹分支 + P4b-review I1 stderr 透传 / I2 `except OSError` 收敛）、`agate/dispatch-protocol.md`（+16：「### 0. 派发路由」子节新增「**tmux 观测层（可选，仅子进程形式）**」小段）、`agate/tests/unit/test_tag0034_p4c.py`（新，12 例）。
> **对齐基准**：`P2-design.md` §3.10（tmux 观测层全节）+ §4.1 P4c 行 + §10 完成标志 9 + `design-dispatch-routing.md` §3（机制二：tmux 观测）+ `P1` BDD-37 / BDD-38。
> **DESIGN_GAP**：`P4-implementation-P4c.md` 一条 `[DESIGN_GAP]`，`[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）]`：tmux 包裹待目标环境验证 —— 两个 helper 为纯逻辑（测试转绿），`_default_subprocess_run` 的 tmux 包裹接入用 feature flag `AGATE_DISPATCH_TMUX` **默认关**；目标环境代表性未定（非容器 / CI runner / 纯物理机，外部评审 W2 / P0-brief R10）→ 停在「定稿 + 待落地验证」、不阻塞 P8。本机 WSL2 + tmux 3.4 冒烟通过。经核：这正是 P2-design §3.10 切除条款 + P0-brief R10 + 外部评审 W2 明确的落地形态，**非切除、非偏离**。

`[PROD_NOT_TOUCHED]` —— 仅 worktree 内读取 + 写本报告；未触碰主 checkout 与 `~/.agate`。

## P4c delta 审查结论汇总

| # | 审查项 | P4c delta 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** —— `dispatch-protocol.md` tmux 小段与 `build_subprocess_launch` / `tmux_cleanup_action` / `_maybe_tmux_wrap` / `_tmux_teardown` 逐条一致；与 `design-dispatch-routing.md` §3 一致 |
| A2 | 脚本→文档对齐 | **ALIGNED** —— 所有 P4c 脚本行为在 tmux 小段有对应；feature flag `AGATE_DISPATCH_TMUX` 语义（「本机接入默认关，环境开关启用，待落地验证姿态」）在协议正文有描述，非裸露行为（literal env var 名未入 SETUP.md 属观察项，对应已确认 DESIGN_GAP，附 `[KNOWN_DEVIATION]`） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** —— A3a 无新 event 类型；A3b：tmux 小段权威源唯一（`dispatch-protocol.md`）、design-note §3 已同源；`test_tag0034_p4c.py` → tests/README 观察项（同 P4a/P4b） |
| A4 | 测试覆盖 | **ALIGNED** —— 全量 pytest **1625 passed / 0 failed / 2 skipped**；`test_bdd_37` + `test_bdd_38` 转绿、tag0034 **0 红**；`test_tag0034_p4c.py` 12 例覆盖 helper 边界 + `_maybe_tmux_wrap` 默认关 + P4b-I1/I2/I3 |
| A5 | 下游影响 + 文档传播 | **ALIGNED** —— CHECK 14 实跑 PASS（tmux 子命令不在护栏 1 禁词清单）；6 冻结脚本 + `check-events.py`（第 1-8 条 + 哈希链）+ `agate-cmdstream-*.py` + `agate-dispatch.py` 渲染路径 + `classify_outcome` / `resolve` / `try_and_fall` **零改动确认**；stderr 透传只到诊断面、不并入判定文本（R1 不破，`test` 锁定）；CHANGELOG 待 P8 |
| A6 | 锚点表覆盖 | **ALIGNED** —— P4c 未新增 `check-*.py`，CHECK 9 锚点表无需再动 |
| A7 | 设计原则一致性 | **ALIGNED** —— P4c 未确立新架构决策；tmux 观测层沿用 P2-design §3.10 + RM-AG0046 模式层 / 检测器层分离；feature flag 默认关对应已确认 DESIGN_GAP，附 `[KNOWN_DEVIATION]` |

**P4c delta 结论：aligned**（无 MISALIGNED、无 NEEDS_HUMAN_REVIEW）

**P4a + P4b + P4c 三批合并总结论：aligned**

> A5.3 / A7.4 的两条 doc-sync（`LIMITATIONS.md` 局限 2 缓解链 + ADR-013「gate 生产者无关性」）仍为 **P8 交付项**（P4a 复审轮已 HUMAN_CONFIRMED，草案见上文附录），**不阻断 P4c commit**。

---

## P4c 逐项审查

### A1（P4c delta）：文档→脚本对齐 — ALIGNED

`dispatch-protocol.md` 新增「**tmux 观测层（可选，仅子进程形式）**」小段（+546~+562）逐条核对：

| 文档声明 | 脚本实现 | 判定 |
|---|---|---|
| `which tmux` 成功则包 `tmux new-session -d -s <命名空间> '<命令> \| tee <capture>; <收尾>'`；失败则裸跑 | `_maybe_tmux_wrap`：`if os.environ.get("AGATE_DISPATCH_TMUX") != "1" or not shutil.which("tmux"): return list(argv_str), None, None`；否则 `build_subprocess_launch(...)`。`build_subprocess_launch`：`tmux_available=False → list(cmd)`；`True → ["tmux","new-session","-d","-s",<session_name>, "<inner> \| tee <capture_path>; echo '=== 派发结束 ==='; …; sleep <N>"]` | ALIGNED |
| 经 `tee` 的 `<capture>` 内容与裸跑 stdout 逐字节一致 → 两路径 `dispatch_route` 留痕 + gate 结果完全一致 | `_default_subprocess_run` tmux 路径 `return _tmux_collect(tmux_session, tmux_capture, ...), None, None` —— `_tmux_collect` 返回 capture 文件全文（`| tee` 只旁路一份不改字节）；`classify_outcome` 拿到的 `stdout` 与裸跑一致。`test_tag0034_p4c.py::test_build_subprocess_launch_wrap_has_countdown_and_tee` 断言 `shell.startswith("claude -p \| tee cap/d.log")` | ALIGNED |
| session 名带命名空间 `agate-<任务>-<阶段>-<短时间戳>`（防碰撞） | `_maybe_tmux_wrap`：`session_name = f"agate-{task_id}-{phase}-{int(time.time())}"`（`task_id` / `phase` 取 `AGATE_DISPATCH_TASK_ID` / `AGATE_DISPATCH_PHASE`）。`test_maybe_tmux_wrap_on_wraps_with_namespaced_session` 断言 `sess.startswith("agate-TAG0034-P4-")` | ALIGNED |
| wrapper 末尾自带退出倒计时（默认 15s、可配），倒计时完自退 → session 自然结束 | `build_subprocess_launch`：`countdown_n=15` 默认；wrapper 串末 `sleep {countdown_n}`。`test_build_subprocess_launch_countdown_configurable` 断言 `countdown_n=30 → "sleep 30"` | ALIGNED |
| 清理：`list-clients` 空 → 直接 `kill-session` 跳倒计时；非空 → 不强杀让倒计时收尾；倒计时脚本挂死超「倒计时 + 余量 10s」→ 兜底 `kill-session` | `tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s)`：`not session_name → "noop"`；`not has_clients → "kill_now"`；`has_clients and elapsed_s <= countdown_n + margin_s → "let_countdown"`；else `→ "force_kill"`。`_tmux_collect` 以「capture 出现成功 / 基础设施失败签名」为「命令跑完」锚点后计 `elapsed`，`action in ("kill_now","force_kill") → _tmux_teardown`。`test_tmux_cleanup_action_boundary_inclusive`：`(True, elapsed==N+margin) → let_countdown` / `(True, 越界) → force_kill`。P2-design §3.10「余量 = 10s，N 默认 15s」逐值对应 | ALIGNED |
| 先 `has-session` 判断、容忍对已消失 session 的非零退出 | `_tmux_teardown`：`alive = subprocess.run(["tmux","has-session","-t",...]).returncode == 0`；`if alive: subprocess.run(["tmux","kill-session",...])`；`except OSError: pass`（MV11 实测容忍） | ALIGNED |
| 明确不做：`send-keys` 交互 / `capture-pane` 内容解析回传主 Agent / 跨轮次 session 复用 | `grep -n "send-keys\|capture-pane\|pipe-pane" agate/scripts/agate_dispatch_route.py` → 零命中；`_tmux_collect` 每次派发独立 session（无跨轮复用）。与 `design-dispatch-routing.md` §3「明确不做」逐条一致 | ALIGNED |
| 目标环境代表性：WSL2 + tmux 3.4（非容器 / CI / 物理机）——目标环境须在其自己 tmux 版本复跑落地前复核项；未通过则停在「定稿 + 待落地验证」、不阻塞发布（可整体切除）；本机接入默认关亦为「待落地验证」姿态的一部分 | `_maybe_tmux_wrap` docstring +「`AGATE_DISPATCH_TMUX=1` 且 `which tmux` 成功才启用；目标环境代表性未定（R10 / 外部评审 W2）→ 默认关、待落地验证」。与 `design-dispatch-routing.md` §3「实机核实……环境代表性说明（外部评审 W2 round2）」+ P2-design §3.10 R10 一致 | ALIGNED |

**tmux 路径 `exit_code=None`**：`_default_subprocess_run` tmux 分支 `return _tmux_collect(...), None, None` —— 退出码不经 `tmux new-session -d` 透出，返 `None` 使 `classify_outcome` 的「非零退出兜底」分支（`exit_code is not None`）被跳过，判定纯走结构化信号 + `produced_files`。与 P2-design §3.7「退出码对 Codex 不可靠、必须解析事件流」一致，**不引入新判定语义**。**ALIGNED**。

**结论：ALIGNED**。

---

### A2（P4c delta）：脚本→文档对齐 — ALIGNED

| P4c 脚本行为 | 文档对应 | 判定 |
|---|---|---|
| `build_subprocess_launch` / `tmux_cleanup_action`（纯逻辑 helper） | `agate_dispatch_route.py` docstring 暴露清单逐条 + `dispatch-protocol.md` tmux 小段（包裹形态 + 清理判定）+ P2-design §3.10 | ALIGNED |
| `_maybe_tmux_wrap` / `_tmux_teardown` / `_tmux_collect`（IO helper） | 模块 docstring「tmux 包裹在 `_default_subprocess_run` 内接入（`_maybe_tmux_wrap`），**默认关**」+ `dispatch-protocol.md` tmux 小段。IO helper 为实现细节，不要求逐个写进协议正文 | ALIGNED |
| feature flag `AGATE_DISPATCH_TMUX`（默认关）| `dispatch-protocol.md` tmux 小段末句「本机接入默认关（环境开关启用），亦为『待落地验证』姿态的一部分」——**协议正文明确了「默认关 + 需环境开关 + 待落地验证」这一语义状态**，非「脚本做了文档没写」的裸露行为。literal env var 名 `AGATE_DISPATCH_TMUX` 未写进 `SETUP.md`（`AGATE_DISPATCH_TASK_ID` / `_PHASE` / `_CAPTURE` / `_TIMEOUT_S` 同）—— 属观察项 | ALIGNED（附 `[KNOWN_DEVIATION]`） |
| P4b-review I1（stderr 透传）| `_default_subprocess_run` 内注释「P4b-I1：透传子进程 stderr 供人排查（诊断面）——**不并入** classify_outcome 的判定文本」+ `P4-implementation-P4c.md` I1 处理段。诊断面行为、非协议语义 | ALIGNED |
| P4b-review I2（`except OSError`）/ P4b-review I3（桥接端到端测试）| `P4-implementation-P4c.md` I2/I3 处理段 + `test_tag0034_p4c.py::test_route_bridge_end_to_end_writes_single_dispatch_route_event` | ALIGNED |

`[KNOWN_DEVIATION: 来源 TAG0034 P4-implementation-P4c.md DESIGN_GAP_REVIEWED（主 Agent 2026-09-10），理由摘要——tmux 观测层接入 feature flag `AGATE_DISPATCH_TMUX` **默认关**、待目标环境（非 WSL2）复跑 research §10 tmux 验证项后再开启；此为 P2-design §3.10 切除条款 + P0-brief R10 + 外部评审 W2 的落地形态。协议正文已表述「默认关 + 待落地验证」语义状态；literal env var 名与 SETUP onboarding 步骤留待观测层开启默认时补（P8 / 未来迭代）。非普通 MISALIGNED。]`

**结论：ALIGNED**（无裸露行为；feature flag 语义状态在协议正文有描述）。

---

### A3（P4c delta）：一致性连锁 + 反向传播 — ALIGNED

**A3a（连锁）**：P4c 未新增 event 类型（`dispatch_route` 是 P4a 已有；P4c tmux 包裹只影响「子进程怎么起 + 人能不能 attach」，`_default_subprocess_run` 返回契约 `(stdout, exit_code, killed_reason)` 不变，`try_and_fall` / `write_dispatch_route_event` 逐字节未动）。`check-events.py` 第 1-8 条 + 哈希链 **零改动**（不在 diff；`check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` exit 0）。**ALIGNED**。

**A3b（反向传播）**：

| 应被影响文件 | 影响到了没 | 判定 |
|---|---|---|
| tmux 小段 → 别处权威源 | `dispatch-protocol.md` 的 tmux 小段是唯一协议权威；`design-dispatch-routing.md` §3（机制二：tmux 观测）已同源（`which tmux` / 命名空间 / 退出倒计时 / 清理逻辑 / 明确不做 / 目标环境代表性逐条一致）。无别处需同步 | ALIGNED |
| `agate/SETUP.md` / onboarding 索引 | tmux 观测层默认关、「待落地验证」姿态 —— 开启默认前不需要 onboarding 步骤（见 A2 `[KNOWN_DEVIATION]`）。`SETUP.md` 无「步骤 2-*」索引需同步 | ALIGNED（观察项） |
| `check-platform-assumptions.py` 扫描面 | 仅扫 `*.bats`/`*.bash`/`*.sh`/`*.py`；`agate_dispatch_route.py` 的 tmux helper 是 Python `subprocess.run(["tmux",...])` 调用 —— `check-platform-assumptions.py` 的 Unix 假设检出针对 shell 脚本习语（裸 `grep`/`sed` 等），`subprocess.run` 传 list 不触发；`check-protocol-consistency.py --strict-errors-only` exit 0 确认无新 ERROR/WARNING（329 不变） | ALIGNED |
| `agate/tests/README.md` per-script 计数表 | 新增 `test_tag0034_p4c.py` —— 观察项（非硬校验，同 P4a/P4b：`test_tag0030_assertions.py::BDD-19` 只校 tests/README「何时更新」节措辞；无 `test_tag0034_*` 行，历轮未判 MISALIGNED） | ALIGNED（观察项，与 P4a/P4b 一致） |
| CHECK 9 锚点表 | P4c 未新增 `check-*.py` | ALIGNED |

**ALIGNED**。

---

### A4（P4c delta）：测试覆盖 — ALIGNED

**P4c 轮全量 pytest 实跑（本次审查执行，2026-09-10）**：

```
$ python3 -m pytest agate/tests/ -q --tb=no
（worktree 根 /home/kity/oclab/agateon/.worktrees/agate-TAG0034）

1625 passed, 2 skipped in 164.01s (exited with code 0)
```

**計數：passed 1625 / failed 0 / skipped 2**（P4b A1 fix 复审轮 = passed 1611 / failed 2；P4c 新增 `test_tag0034_p4c.py` 12 例 + `test_bdd_37` 转绿 + `test_bdd_38` 转绿 → passed +14 / failed −2）。**tag0034 全绿 0 红**（首轮 P4a 起一路带的 `test_bdd_37/38` P4c 批次边界 red 至此清零）。

**P4c 新逻辑边界覆盖评估**（`test_tag0034_p4c.py` 12 例）：
- `build_subprocess_launch` 纯逻辑边界 3 例：裸路径返回新 list 且不别名 `cmd`（`out is not cmd` + `"tmux" not in " ".join(out)`）/ 包裹路径含 `tee <capture>` + 末尾 `sleep <N>` 退出倒计时 / `countdown_n` 可配（30 → `"sleep 30"`）。
- `tmux_cleanup_action` 边界 2 例：空 session → `noop` / `elapsed == N + margin` 边界含入 `let_countdown` / 越界 → `force_kill`。
- `_maybe_tmux_wrap` 3 例：默认关（无 `AGATE_DISPATCH_TMUX`）→ 裸 argv 逐字节现状 / 开关开但 `which tmux` 失败 → 裸 argv / 开关开 + `which tmux` 成功 → `tmux new-session` 包裹 + 命名空间 session（`agate-<task>-<phase>-<ts>`）。
- `_default_subprocess_run` P4b-I1 2 例：stderr 透传诊断面（`capsys.readouterr().err` 含 `ProviderAuthError`）/ stderr **不并入** stdout（`stdout == "clean stdout"`）。
- P4b-I2 1 例：`FileNotFoundError` → `spawn_oserror`（`("", None, "spawn_oserror")`）→ 下游 `LAUNCH_FAIL`。
- P4b-I3 1 例：`_route_main` 相同组合（`functools.partial` + 适配层闭包 + 真 `agate_common.append_event` 哈希链）跑 `try_and_fall`，mock 子进程候选链（首候选 `INFRA_ERROR` 回落、次候选 `HAS_OUTPUT`）→ 一次回落落 **1 条**合法 `dispatch_route` 事件，`tried[0].result=="failed"` / `reason=="infra_error"`，`tried[1].result=="success"`，`final == {"cli":"opencode","model":"prov/y"}`，`routed[0].phase == "P4"`。
- `test_tag0034_tmux.py::test_bdd_37` + `test_bdd_38`（P3 契约断言，逐字节未改）→ 转绿。
- P3 既有断言未改：`test_tag0034_tryfall.py` / `test_tag0034_p4b.py`(18) / `test_tag0034_subprocess.py` 等仍绿。

**结论：ALIGNED**（全量实跑 0 failed，tag0034 全绿；P4c 新逻辑 helper 边界 + I1/I2/I3 覆盖充分）。

---

### A5（P4c delta）：下游影响 + 文档传播 — ALIGNED

**A5.1 CHECK 14 护栏 1 — ALIGNED（实跑核实）**

`dispatch-protocol.md` tmux 小段含 `tmux new-session` / `list-clients` / `kill-session` / `has-session` / `send-keys` / `capture-pane` 等 tmux 子命令名。核 `check-protocol-consistency.py` CHECK 14 平台词表 `PLATFORM_TOKEN_RE = re.compile(r"(?<![\w-])(?:OpenCode|Claude Code|DSH|workflow|ralph|goal|task)(?![\w-])")` —— **`tmux` 及其子命令不在护栏 1 禁词清单**（护栏 1 针对「以平台工具命名的 workflow / ralph / goal / task 概念」，`tmux` 与 `git` / `pytest` 同为通用工具，P2-design §3.10 亦按通用观测工具处理）。小段全中文叙述、无禁词。**实跑确认：`check-protocol-consistency.py --strict-errors-only` → `✅ PASS CHECK 14 md 叙述段落平台名扫描` + `✅ PASS CHECK 15` + exit 0（329 WARNING / 0 ERROR，与 P4b 后基线一致，tmux 小段未新增 WARNING）**。护栏 1 合规成立，**不需要 `> 实现注记：` 块**。**ALIGNED**。

**A5.2 冻结脚本 / R1 完整性 — ALIGNED**

`git diff HEAD --stat` 确认 P4c 只改 `agate/dispatch-protocol.md`（+16）+ `agate/scripts/agate_dispatch_route.py`（+201/-4）+ `agate-workspace/tasks/.../P4-progress.md`（任务追踪）。`git diff HEAD -- agate/scripts/agate_dispatch_route.py` 核：`classify_outcome` / `resolve` / `try_and_fall` / `load_config` / `build_dispatch_command` / `dispatch_once` / `presence_parse_ok` **函数体逐字节未动**（+/- 行只含新增 tmux helper + `_default_subprocess_run` 内 tmux 分支 + stderr 透传 + `except OSError` 收敛）。`agate/rules/phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py` / `check-dispatch-routing.py` / `dispatch-tiers.yaml` / `agate-cmdstream-adapters.py` / `agate-dispatch.py` **均不在 diff 内**。

R1 完整性洞守住：tmux 包裹只影响「子进程怎么起 + 人能不能 attach」；`classify_outcome` 拿到的 stdout（经 `tee` 的 capture）与裸跑一致；stderr 透传只到诊断面、**不并入** `_INFRA_SIGNALS` 扫描文本（`test_default_subprocess_run_stderr_not_merged_into_stdout` 锁死）。feature flag 默认关 → 裸路径与 P4b 逐字节等价（返回契约 `(stdout, exit_code, killed_reason)` 不变；stderr 透传为 P4b-review I1 INFORMATIONAL 落地，不影响 classify_outcome 输入）。回归护栏 25 passed（`P4-progress` 自查 + A4 全量实跑确认）。**ALIGNED**。

**A5.3 CHANGELOG — 待 P8（非 MISALIGNED）**

P4c 同为协议语义变更（tmux 观测层小段 + helper）。`check-changelog.py` 仅 P8 触发（P4a 轮已核实）。CHANGELOG 待 P8 统一补，**不判 MISALIGNED**。

---

### A6（P4c delta）：锚点表覆盖 — ALIGNED

P4c **未新增任何 `check-*.py`**（`build_subprocess_launch` / `tmux_cleanup_action` / `_maybe_tmux_wrap` 等均在 helper 模块 `agate_dispatch_route.py` 内，非独立 gate 脚本）。CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` 无需再动（P4a 复审轮补的 `check-dispatch-routing.py` 条目仍成立、`test_sg_6` 保持绿）。**ALIGNED**。

---

### A7（P4c delta）：设计原则一致性 — ALIGNED

P4c **未确立新架构决策**：tmux 观测层是 P2-design §3.10 既定机制的落地，架构沿用 RM-AG0046「模式层 / 检测器层分离」（协议定义「包裹 / 清理 / 留痕」语义，`tmux` 具体命令归实现）。两路径 gate 判定 / 留痕逐字节一致（BDD-37）与「gate 生产者无关性」（ADR-013 草案，P4a 复审轮 HUMAN_CONFIRMED、落 P8）一致 —— 走不走 tmux 不影响协议判断的任何环节。

tmux 包裹 feature flag `AGATE_DISPATCH_TMUX` **默认关**、目标环境代表性未定 → 对应 `[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）]`。按原则 6，此为 P2-design §3.10「不通过则停在『定稿 + 待落地验证』、不阻塞 P8」切除条款 + P0-brief R10 + 外部评审 W2 的**落地形态**（非切除、非偏离），记 **ALIGNED**，追加 `[KNOWN_DEVIATION: 来源 TAG0034 P4-implementation-P4c.md DESIGN_GAP_REVIEWED（主 Agent 2026-09-10），理由摘要——tmux 观测层「两 helper 纯逻辑（测试转绿）+ 接入 feature flag 默认关」是 §3.10 切除条款的落地姿态；目标环境（非 WSL2）复跑 research §10 tmux 验证项后再开启默认，登记 P8 / 未来迭代；裸路径逐字节不变（BDD-37）+ 本机 WSL2/tmux 3.4 冒烟通过。尚无 P7 记录（任务在 P4），P7 阶段须由 consistency-reviewer 复核确认]`。

**结论：ALIGNED**。

---

## P4c 闭环规则

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| ALIGNED | A1 / A2（附 `[KNOWN_DEVIATION]`）/ A3 / A4 / A5 / A6 / A7（附 `[KNOWN_DEVIATION]`） | 通过，可 P4c commit。P4c 全量 pytest **1625 passed / 0 failed / 2 skipped**，tag0034 全绿。 |
| （P8 交付项，非 P4c 阻断） | A5.3 / A7.4（P4a 复审轮遗留）+ P4c 的 tmux 观测层目标环境复跑 | `LIMITATIONS.md` 局限 2 缓解链 + ADR-013（HUMAN_CONFIRMED 已落）+ tmux 观测层在目标环境复跑 research §10 验证项后开启默认 —— 均 P8 / 未来迭代事项，**不阻断 P4c commit**。 |

**P4c delta 总结论：aligned**（A1-A7 全 ALIGNED，其中 A2 / A7 附 `[KNOWN_DEVIATION]` 对应已确认 DESIGN_GAP；无 MISALIGNED、无 NEEDS_HUMAN_REVIEW）。

**P4a + P4b + P4c 三批合并总结论：aligned** —— P4a 三轮终态 aligned（A5.3/A7.4 HUMAN_CONFIRMED、落 P8）；P4b 两轮终态 aligned（A1 fix `classify_outcome` 按 cli 细分）；P4c 一轮 aligned（tmux 观测层，feature flag 默认关对应已确认 DESIGN_GAP）。全量 pytest **1625 passed / 0 failed / 2 skipped**（tag0034 全绿）；`check-protocol-consistency.py --strict-errors-only` exit 0（CHECK 1~15 PASS，329 WARNING / 0 ERROR）；6 冻结脚本 + `check-events.py` + `agate-cmdstream-*.py` + `agate-dispatch.py` 渲染路径零改动。**P4 三批可全部 commit**（各带 `self-gate-review:` trailer）。A5.3 / A7.4 + tmux 目标环境复跑为 P8 交付项，不阻断 P4 commit。

---

## 附：P4c 轮补充实跑（本次审查执行，2026-09-10）

- `python3 -m pytest agate/tests/ -q --tb=no` → **1625 passed / 0 failed / 2 skipped**（164.01s，exit 0）；tag0034 全绿（`test_bdd_37` + `test_bdd_38` 转绿）。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0；**CHECK 1~15 全 PASS**（含 `✅ PASS CHECK 14 md 叙述段落平台名扫描` / `✅ PASS CHECK 15`）；329 WARNING / 0 ERROR（与 P4b 后基线一致，tmux 小段未新增 WARNING）。
- `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（14 行，哈希链完整，ts 单调）。
- `python3 -m pytest agate/tests/unit/test_tag0034_p4c.py agate/tests/unit/test_tag0034_p4b.py agate/tests/unit/test_tag0034_subprocess.py agate/tests/unit/test_tag0034_tryfall.py agate/tests/regression/test_tag0034_zero_change.py agate/tests/unit/test_check_events.py -q` → **49 passed**（P4c 12 + P4b 18 + subprocess/tryfall/zero_change/check_events 回归护栏）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py` → All checks passed。
- `git diff HEAD --stat`（HEAD = `99a4c19` P4b commit）→ `agate/dispatch-protocol.md`（+16）+ `agate/scripts/agate_dispatch_route.py`（+201/-4）+ `agate-workspace/tasks/TAG0034-dispatch-routing/P4-progress.md`（任务追踪）—— 6 冻结脚本 + `check-events.py` + `check-dispatch-routing.py` + `dispatch-tiers.yaml` + `agate-cmdstream-*.py` + `agate-dispatch.py` **均不在 diff 内**。
- `git diff HEAD -- agate/scripts/agate_dispatch_route.py` +/- 行核 → `classify_outcome` / `resolve` / `try_and_fall` / `load_config` / `build_dispatch_command` / `dispatch_once` / `presence_parse_ok` 函数体逐字节未动（仅新增 tmux helper + `_default_subprocess_run` tmux 分支 + stderr 透传 + `except OSError` 收敛）。
- `grep -n "send-keys\|capture-pane\|pipe-pane" agate/scripts/agate_dispatch_route.py` → 零命中（「明确不做」项未落地代码，与协议一致）。

---
---

# P8 批复审（2026-09-10）

> **范围**：TAG0034 P8 收尾批的 `agate/**` + 发布面 doc 改动增量。P4a / P4b / P4c 的 A1-A7 结论见上文；本节只增量审 **P8 delta**。
> **审查对象**：`git diff HEAD`（HEAD = `8ad7834` P7 commit）—— `agate/LIMITATIONS.md`（局限 2「派发路由缓解链」段，A5.3）、`agate/adr.md`（ADR-013「派发路由 / gate 生产者无关性」，A7.4）、`docs/design-notes/design-dispatch-routing.md`（§5/§7 老串定点清理，P7 `[DEVIATION]` 收尾）、`CHANGELOG.md`（`## [0.71.0]` 段）、`agate/UPGRADING.md`（§3 `### v0.71.0`）、`README.md` + `README.zh-CN.md`（badge v0.71.0）、`agate-workspace/roadmap/roadmap.md`（RM-AG0060 `done`）、`agate-workspace/debt/tech-debt.md`（DEBT0039 `closed`）、`agate-workspace/tasks/TAG0034-dispatch-routing/P1-requirements.md`（frontmatter `scope_resolved:` 两项）。
> **对齐基准**：本报告附录（A5.3 / A7.4 的 P8 交付草案，逐字采用）+ `P8-release.md`（`bump_type: minor` / `debt_check: reviewed`）+ `dispatch-protocol.md`「### 0. 派发路由」子节 + `agate_dispatch_route.py` / `check-events.py`（ADR-013 沉淀的脚本行为）。
> **A5.3 / A7.4 HUMAN_CONFIRMED**：用户 2026-09-09 裁决「两条 doc-sync 都补、落 P8 收尾批」（见上文 A5 / A7 的 `[HUMAN_CONFIRMED]`），本节复核其落地忠实度。

`[PROD_NOT_TOUCHED]` —— 仅 worktree 内读取 + 写本报告；未触碰主 checkout 与 `~/.agate`。

## P8 delta 审查结论汇总

| # | 审查项 | P8 delta 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** —— ADR-013 决策措辞与 `agate_dispatch_route.py` `GATE_FAIL_TRIGGERS_FALLBACK=False` + `check-events.py` `DISPATCH_ROUTE_REASONS`（无 `gate_fail`）+ `dispatch-protocol.md`「### 0. 派发路由」子节逐条语义一致，ADR 不比它们宽 / 窄；`LIMITATIONS.md` 局限 2 新段的弱 / 强缓解 + 两条完整性不变量与新节一致 |
| A2 | 脚本→文档对齐 | **ALIGNED** —— CHANGELOG [0.71.0] / UPGRADING §3 / roadmap done / tech-debt DEBT0039 closed / P1 `scope_resolved` 均对应实际脚本行为与 P4a-c 已落地内容，无「文档写了脚本没有」的反向裸露；`scope_resolved` 是合法 frontmatter 字段（`agate-frontmatter-check.py:37` 白名单 + `check-scope-resolved.py` 读取） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** —— A3a 无新 event 类型；A3b：ADR-013 → `adr.md` 无 TOC / 索引需同步；CHANGELOG `## [0.71.0]` → UPGRADING §3 `### v0.71.0` 已补且 **CHECK 13 PASS**；design-note §5/§7 清理后与 §2.1/§2.2 一致（无新矛盾） |
| A4 | 测试覆盖 | **ALIGNED**（`[KNOWN_DEVIATION]`：pre-tag 时序）—— 全量 pytest **5 failed / 1620 passed / 2 skipped**，**5 failed 全部同一根因 = CHECK 7 pre-tag**（README badge v0.71.0 已 bump / `git tag v0.71.0` 未创建）；`check-protocol-consistency.py --strict-errors-only` 唯一 ERROR = CHECK 7，CHECK 1-6 / 8-15 全 PASS；`1620 + 5 = 1625` = P4c 基线，主 Agent `git tag v0.71.0` 后 5 项归绿 → 1625 passed / 0 failed；DEBT0013 时序、TAG0033 P8 同款，**不判 misaligned** |
| A5 | 下游影响 + 文档传播 | **ALIGNED** —— CHANGELOG [0.71.0] 覆盖全部对外可见变更（子命令 / helper / 词表 / 项目级配置 / 校验器 / 事件 / 第 8 条 / 新节 / tmux / effort / ADR-013 / LIMITATIONS / DEBT0039 / SETUP / platform-notes）；roadmap RM-AG0060 `done` 触发 RM-AG0043（P8 gate `_check_roadmap_done` 满足）无其他连锁；P4a-c 轮「CHANGELOG 待 P8」至此闭合 |
| A6 | 锚点表覆盖 | **ALIGNED** —— P8 未新增 `check-*.py`，CHECK 9 锚点表无需再动 |
| A7 | 设计原则一致性 | **ALIGNED** —— ADR-013 与既有 ADR（ADR-002 可判定性 / ADR-006 同源盲区 / ADR-010 证据复用）无冲突、方向一致（ADR-013 显式引「与 ADR-002 一致」+「与 ADR-006 互补」）；A7.4 的补 ADR 建议至此落地闭合 |

**P8 delta 结论：aligned**（无 MISALIGNED、无 NEEDS_HUMAN_REVIEW；CHECK 7 / 5 项 test 红 = 已知 pre-tag 时序，主 Agent `git tag v0.71.0` 后归零）

**P4a + P4b + P4c + P8 四批合并总结论：aligned**

---

## P8 逐项审查

### A1（P8 delta）：文档→脚本对齐 — ALIGNED

**ADR-013「决策」措辞 vs 脚本 + 协议正文 —— 逐条对齐，ADR 不更宽 / 不更窄**

| ADR-013「决策」句 | 脚本 / 协议正文 | 判定 |
|---|---|---|
| 「gate 只认产出文件 + exit code，不认谁生产的」；`check-gate.py` / `check-judge-verdict.py` / `check-p6-provenance.py` 及一切 gate 脚本对跨 CLI / 跨 model 派发的产出**零特殊处理** | 三校验器 P4a-P8 全程零改动（`git diff HEAD` 不含）；P1 §3 第 6 组独立核实「纯 TASK_DIR 文件解析、平台无关」；`dispatch-protocol.md`「### 0. 派发路由」子节「`check-gate.py` / `check-judge-verdict.py` / `check-p6-provenance.py` 对跨 CLI 派发的产出零特殊处理」逐字 | ALIGNED |
| 「**未来不得为跨 CLI 派发定制 gate**（不得新增「若产自 codex 则……」式分支）」 | `dispatch-protocol.md` 子节「未来不得为跨 CLI 派发定制 gate」逐字；ADR-013「后果」段「新增 gate 脚本时，若其判定逻辑试图区分产出来源，应视为违反本 ADR」—— 与子节同强度，无扩张 | ALIGNED |
| 「回落理由码枚举只有 `launch_fail` / `infra_error` / `no_parseable_output` 三值，无 `gate_fail`」 | `agate_dispatch_route.py:_VALID_REASONS = ("launch_fail", "infra_error", "no_parseable_output")` + `GATE_FAIL_TRIGGERS_FALLBACK = False`；`check-events.py:DISPATCH_ROUTE_REASONS = {"launch_fail","infra_error","no_parseable_output"}`；两处**无 `gate_fail`**（`grep gate_fail` 仅注释否定表述）| ALIGNED |
| 「`check-events.py` 第 8 条机械拒绝任何非三值理由码」 | `check-events.py` 第 8 条 `if reason is not None and reason not in DISPATCH_ROUTE_REASONS: sys.exit(1)` | ALIGNED |
| 「gate FAIL → 同一候选正常阶段 retry，绝不触发换候选」 | `agate_dispatch_route.py:try_and_fall` I1 白名单（`kind == "HAS_OUTPUT"` → 停回落 return；非 `_FALLBACK_KINDS` → `DispatchContractError`）；`dispatch-protocol.md` 子节「gate FAIL 绝不换候选……那是正常阶段 retry（在同一候选上重跑）」逐字 | ALIGNED |

ADR-013「语境」「理由」「后果」三节均为对上述决策的说明性铺陈（关联 ADR-002 / ADR-006 / RM-AG0060），**未引入任何新约束或放宽**。ADR 是 `dispatch-protocol.md` 子节散文 + 脚本行为的**沉淀**，粒度层面精确一致。**ALIGNED**。

**`LIMITATIONS.md` 局限 2 新段 vs `dispatch-protocol.md`「### 0. 派发路由」子节 —— 一致**

| 局限 2 新段表述 | dispatch-protocol.md 子节对应 | 判定 |
|---|---|---|
| 「`cli: native`（同厂商换 model，不脱离原生派发工具）是**弱缓解** —— 同训练系谱盲区基本共享，只省成本 + 一点 failure-mode 多样性，且自动化天花板是「主 Agent 读文件机械横传 model」」 | 子节「`cli: native`（同厂商换 model，不脱离原生派发工具）是**弱缓解**——同训练系谱盲区基本共享，只省成本 + 一点 failure-mode 多样性；且原理上做不到「不依赖主 Agent」，自动化天花板是**主 Agent 读文件机械横传 model**」 | ALIGNED（逐字级一致） |
| 「`cli:` 另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程）是**强缓解** —— 真正的异源独立视角、可端到端自动化」 | 子节「`cli:` 另一个 CLI（`claude-code` / `codex` / `opencode`，起子进程）是**强缓解**——真正的异源独立视角，可端到端自动化」 | ALIGNED |
| 「两条完整性不变量机械强制（「候选回落 ≠ 状态机 retry」/「gate FAIL 绝不换候选」，理由码枚举无 `gate_fail` 值）防「换模型试到出 green」的完整性洞」 | 子节「**两条完整性不变量（机械强制，防「换模型试到出 green」的完整性洞）**：1. 候选回落 ≠ 状态机 retry……2. gate FAIL 绝不换候选……`dispatch_route` 理由码枚举里**没有 `gate_fail` 值**」 | ALIGNED |
| 「**仍非根治** —— 主 Agent 自身的选型判断、以及「机械横传 model」这一步本身，仍缺乏外部约束，与局限 3「主 Agent 判断力是单点故障」同构」 | 与局限 3 现状段一致的诚实叙述口径；design-note §2.2 / §2.4a「本设计不假装解决」同调 | ALIGNED（诚实边界句保留，未夸大缓解效力） |
| 「per-machine 机会式、不追求跨机可复现」 | 子节 + design-note §2.1 「routing 是 per-machine 机会式、不追求跨机可复现」 | ALIGNED |

形态对齐局限 3 的「P6.5 独立 Judge 缓解链」段（追加在局限 2「现状：无解……→ ADR-006」之后、局限 3 之前）。**ALIGNED**。

**design-note §5/§7 老串清理 vs §2.1/§2.2 —— 一致、无新矛盾**

- §5「新增**项目级** `agate-workspace/dispatch-routing.yaml`……档位词表在协议本体 `agate/rules/dispatch-tiers.yaml`」+「查表 → 派首选 → 逐级回落 → 写 `dispatch_route` 事件（try-and-fall，无 probe，**与 §2.2 一致**）」—— 与 §2.1 三层落点表 + §2.2 标题「查表 → 派首选 → 逐级回落 → 再派发（try-and-fall，无 probe）」逐条对应。
- §7 事项 1：`rules/dispatch-routing.yaml` → `agate-workspace/dispatch-routing.yaml`；事项 4「探测缓存 / native 探测方式」标注「**2026-09-09 定案已作废**：核心循环改 try-and-fall、无 probe」（`~~删除线~~`）—— 与 §2.2「try-and-fall，不是 probe-then-commit」一致。
- `grep 'rules/dispatch-routing\.yaml' design-dispatch-routing.md` → **零命中**（老串已清）。P7 `[DEVIATION]`（docs-only 残留旧路径串 + 「探测」叙事，非 CRITICAL）至此收尾。

**结论：ALIGNED**。

---

### A2（P8 delta）：脚本→文档对齐 — ALIGNED

| P8 文档新增内容 | 对应脚本行为 / 已落地内容 | 判定 |
|---|---|---|
| CHANGELOG [0.71.0]「`agate dispatch route` 子命令 + `agate_dispatch_route.py` helper（`resolve` / `load_config` / `classify_outcome` / `build_dispatch_command` / `try_and_fall` 等）……既有渲染路径逐字节不变」 | `agate-dispatch.py` `_route_main` + `agate_dispatch_route.py` 全部函数（P4a-c 已落地并单测覆盖）；BDD-39 字节基线绿 | ALIGNED |
| CHANGELOG [0.71.0]「`dispatch_route` 事件……`check-events.py` 第 8 条……混入 `gate_fail` 或任何非三值 → `sys.exit(1)`」 | `check-events.py` 第 8 条实际逻辑（P4a 落地）| ALIGNED |
| CHANGELOG [0.71.0]「tmux 观测层……feature flag `AGATE_DISPATCH_TMUX` 默认关；……目标环境按 research §10 复跑后方可开启默认」 | `_maybe_tmux_wrap` 默认关（P4c）+ P4c `[DESIGN_GAP_REVIEWED]` | ALIGNED |
| UPGRADING §3 v0.71.0「无破坏性变更，零迁移动作……不改 `.state.yaml` schema / 既有任务文件格式 / 3 个 hook 薄壳」 | P8 diff 无 `.sh` 改动、无 schema 改动、无 hook 改动；`bump_type: minor`（`P8-release.md`）| ALIGNED |
| roadmap RM-AG0060 `scheduled` → `done` + 更新日期 `2026-09-10` | RM-AG0043（P8 gate `check-gate.py._check_roadmap_done`）硬要求；「关联任务」列已是 `TAG0034` | ALIGNED |
| tech-debt DEBT0039 `open` → `closed` + `task_id: null` → `TAG0034` + `closed_at: 2026-09-10` + 2 条 closure evidence | `check-debt.py` schema 校验；closure_criteria 三条 = BDD-48（architect.md 边界）/ BDD-49（dispatch-protocol.md 边界）/ BDD-50（consistency 0 ERROR）—— P4a 落地、P6 逐条 PASS | ALIGNED |
| P1-requirements.md frontmatter `scope_resolved:` 两项（DEBT0039 并入 / A5.3·A7.4 doc-sync）| `check-scope-resolved.py:_scope_resolved_frontmatter` 读取；`scope_resolved` 在 `agate-frontmatter-check.py:37` 白名单 + P1-requirements.md schema `migrated_keys` 内（`P8-release.md` §3 核 `check-frontmatter.py` exit 0）| ALIGNED |

无「文档写了脚本没有」的反向裸露。**ALIGNED**。

---

### A3（P8 delta）：一致性连锁 + 反向传播 — ALIGNED

**A3a（连锁）**：P8 未新增 event 类型 / 枚举 / gate 脚本。`check-events.py` 零改动（`git diff HEAD` 不含）。**ALIGNED**。

**A3b（反向传播）**：

| 应被影响文件 | 影响到了没 | 判定 |
|---|---|---|
| `agate/adr.md` 目录 / 索引 —— 新增 ADR-013 | 不需改 —— `adr.md` **无 TOC / ADR 索引清单**（`grep '目录\|Table of Contents\|ADR-001.*ADR-012'` 零命中）；ADR-013 `## ADR-013:` heading 直接追加在 ADR-012 之后 | ALIGNED |
| `agate/UPGRADING.md` §3 —— CHANGELOG 新增 `## [0.71.0]` 段 | 已补 `### v0.71.0` 章节；`check-protocol-consistency.py` **CHECK 13（CHANGELOG↔UPGRADING 章节对应）PASS**（本次实跑核实：`✅ PASS CHECK 13`）；内容比照 TAG0033 P8 v0.70.0 章节形态（无破坏性变更 / 零迁移 / `git pull` 即完成）| ALIGNED |
| `agate-summary.py` / 版本相关脚本读 CHANGELOG 顶部版本 | 不在 P8 diff；badge / CHANGELOG / UPGRADING 三处版本号已同步为 v0.71.0（`P8-release.md` §3 逐文件核）；`git tag v0.71.0` 由主 Agent 在 P8 commit 后创建（`P8-release.md` 明文）—— CHECK 7 pre-tag 红为此设计使然（见 A4）| ALIGNED（版本三处同步；tag 待主 Agent） |
| design-note §5/§7 改后与 §2.1/§2.2 | 见 A1「design-note §5/§7 老串清理」—— 逐条对应、无新矛盾 | ALIGNED |
| roadmap RM-AG0060 `done` → RM-AG0043 之外的连锁 | `_check_roadmap_done`（P8 gate）是唯一硬校验；RM-AG0060 长描述 P4a M12 已回写（`agate-workspace/dispatch-routing.yaml` + `dispatch-tiers.yaml` + try-and-fall + 两轴，无残留旧串，`P8-release.md` §3 核）；无其他连锁 | ALIGNED |

**ALIGNED**。

---

### A4（P8 delta）：测试覆盖 — ALIGNED（`[KNOWN_DEVIATION]`：pre-tag 时序）

**P8 轮全量 pytest 实跑（本次审查执行，2026-09-10）**：

```
$ python3 -m pytest agate/tests/ -q
...
FAILED agate/tests/integration/test_consistency.py::test_con_1_check_1_yaml_parseable
       - AssertionError: assert 'ERROR (' not in <consistency output>
FAILED agate/tests/integration/test_consistency.py::test_con_6_check_7_version_badge_sync
       - AssertionError: assert 'PASS  CHECK 7' in <consistency output>
FAILED agate/tests/unit/test_env_adapt_docs.py::test_bdd_25_consistency_zero_error
       - AssertionError: <consistency output has ERROR (1)>
FAILED agate/tests/unit/test_tag0027_b1_phases_transfer_fields.py::test_bdd_5_consistency_worktree_still_green_regression
       - AssertionError: 协议一致性回归被破坏
FAILED agate/tests/unit/test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes
       - assert 1 == 0
5 failed, 1620 passed, 2 skipped in 155.17s
```

**計數：passed 1620 / failed 5 / skipped 2**。`1620 + 5 = 1625` = **P4c 基线**（1625 passed / 0 failed / 2 skipped）—— 即 P8 把恰好 5 个「断言 consistency 绿」的测试从 pass 翻成 fail。

**5 failed 全部同一根因 = CHECK 7 pre-tag**（逐条核实）：

| 失败测试 | 断言 | 失败原因 |
|---|---|---|
| `test_con_1_check_1_yaml_parseable` | `"ERROR (" not in <consistency 全量输出>` | CHECK 7 注入 `ERROR (1):` 块（CHECK 1 本身 `✅ PASS`）|
| `test_con_6_check_7_version_badge_sync` | `"PASS  CHECK 7" in <输出>` | CHECK 7 = **FAIL**（badge v0.71.0 已 bump / `git tag v0.71.0` 未创建）|
| `test_env_adapt_docs.py::test_bdd_25_consistency_zero_error` | consistency 0 ERROR | CHECK 7 的 1 ERROR |
| `test_tag0027_b1::test_bdd_5_consistency_worktree_still_green_regression` | consistency 保持绿 | CHECK 7 的 1 ERROR |
| `test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes` | `check-protocol-consistency.py --strict-errors-only` exit 0（`assert 1 == 0`）| CHECK 7 → exit 1 |

**`check-protocol-consistency.py --strict-errors-only` ERROR 隔离（本次实跑）**：

```
❌ FAIL  CHECK 7  version badge 与 git tag
  ERROR (1):
    ❌ README version badge v0.71.0 != 最新 tag v0.70.0 [README.md]
```

**唯一 ERROR = CHECK 7**。CHECK 1 / 3 / 4 / 6 / 8 / 9 / 11 / 12 / **13** / 14 / 15 全部 `✅ PASS`（CHECK 2 / 5 / 10 无 FAIL）。**CHECK 7 之外无别的 ERROR、上述 5 项之外无别的 fail**。

**判定**：CHECK 7（`README badge v0.71.0` ≠ `最新 tag v0.70.0`）是 P8 收尾的**已知 pre-tag 时序** —— badge 在 P8 已 bump、`git tag v0.71.0` 由主 Agent 在 P8 commit 后创建（`P8-release.md` 明文）。CHECK 7 校验的是「发布完成态」（DEBT0013 时序），主 Agent `git tag v0.71.0` 后复跑 → CHECK 7 `PASS` → 5 项 test 全绿 → **1625 passed / 0 failed / 2 skipped**、consistency `--strict-errors-only` exit 0。**与 TAG0033 P8 同款处理**，**不因这一条判 misaligned**。

`[KNOWN_DEVIATION: 来源 DEBT0013 已知时序 + TAG0033 P8 先例。P8 badge bump 与 `git tag` 创建之间的中间态使 CHECK 7 报 1 ERROR，连带 5 个断言「consistency 绿」的测试红。非 P8 引入的回归、非新问题（CHECK 7 之外 0 ERROR、这 5 项之外 0 fail）；主 Agent 在 P8 commit 后 `git tag v0.71.0`，复跑即归零（1625 passed / 0 ERROR）。]`

**结论：ALIGNED**（pre-tag 时序，非回归）。

---

### A5（P8 delta）：下游影响 + 文档传播 — ALIGNED

**A5.1 CHANGELOG [0.71.0] 覆盖度 —— 完整**

逐项核对 CHANGELOG [0.71.0] 段 vs 本任务全部对外可见变更：`agate dispatch route` 子命令 ✓ / `agate_dispatch_route.py` helper ✓ / `dispatch-tiers.yaml` 档位词表 ✓ / 项目级 `dispatch-routing.yaml` + `check-dispatch-routing.py` ✓ / `dispatch_route` 事件 + `check-events.py` 第 8 条（含「无 `gate_fail`」）✓ / `dispatch-protocol.md`「### 0. 派发路由」新子节（含「gate 不认谁生产的」+ 两条完整性不变量 + 弱/强缓解 + 单 Agent no-op + 评审打回续跑）✓ / tmux 观测层（feature flag 默认关）✓ / effort 能力探测（BDD-10 `[BASELINE_CHANGE]`）✓ / ADR-013 ✓ / `LIMITATIONS.md` 局限 2 缓解链 ✓ / DEBT0039 闭合 + `architect.md` / `SETUP.md` / `platform-notes.md` 小节 ✓。**无遗漏**。

**A5.2 CHANGELOG 闭合 —— P4a-c 轮「CHANGELOG 待 P8」至此完成**

P4a / P4b / P4c 三轮 A5.2 均判「CHANGELOG 待 P8 统一补，不判 MISALIGNED」。P8 `## [0.71.0] - 2026-09-10` 段落地 —— 该延期项闭合。`check-changelog.py`（P8 gate 触发）对 `[Unreleased]` / task_id 的要求由 P8 gate 阶段核（本节不重复）。

**A5.3 roadmap `done` 连锁**

RM-AG0060 `scheduled` → `done` 触发 `check-gate.py` P8 分支的 `_check_roadmap_done`（RM-AG0043）—— 该 gate 要求「若 roadmap 有关联 RM 条目须已回写 done」，P8 满足。无 RM-AG0043 之外的连锁（roadmap 表其他行未动，`P8-release.md` §3 核长描述无残留旧串）。

**结论：ALIGNED**。

---

### A6（P8 delta）：锚点表覆盖 — ALIGNED

P8 **未新增任何 `check-*.py`**。CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` 无需再动（P4a 复审轮补的 `check-dispatch-routing.py` 条目仍成立、`test_sg_6` 保持绿 —— `test_sg_6` **不在** P8 的 5 项 pre-tag 红名单内）。**ALIGNED**。

---

### A7（P8 delta）：设计原则一致性 — ALIGNED

**ADR-013 vs 既有 ADR —— 无冲突、方向一致**

- **ADR-002（可判定性——gate 门槛机器可判定）**：ADR-013「理由」段显式「与 ADR-002 一致 —— gate 门槛机器可判定、不依赖主观声明，跨 CLI 产出与本地产出走同一 exit-code 判定面，是同一原则的直接延伸」。回落理由码机械拒绝（`sys.exit(1)`）而非 LLM 判断，符合 ADR-002。**一致**。
- **ADR-006（双层角色——同源盲区）**：ADR-013「理由」段「与 ADR-006 互补 —— ADR-006 记录『同源模型隔离是认知层非真正独立』这一上限；派发路由给角色隔离补 model / 厂商维度是其部分缓解（见 LIMITATIONS.md 局限 2），而『gate 生产者无关』正是这一缓解能安全落地的结构前提」。**一致（互补，非冲突）**。
- **ADR-010（受控例外——满足客观可判定条件时允许复用既有验证证据）**：ADR-010 是「客观可判定条件下复用证据」，ADR-013 是「gate 不因生产者而异」—— 两者均以「客观机器可判定」为核心，无冲突。ADR-013 不放宽任何 gate 重跑要求。**一致**。
- **ADR-005（改动性质决定流程）**：ADR-013 记录的是架构决策（红线级），P8 把它从 `dispatch-protocol.md` 散文沉淀为 ADR —— 正是 ADR-005「机制交叉类改动」的正确归档动作。**一致**。

A7.4（P4a 复审轮提出「建议补新 ADR 记录『派发路由 / gate 生产者无关性』」，用户 2026-09-09 `[HUMAN_CONFIRMED]` 落 P8）—— P8 逐字采用本报告附录草案落地，**该建议闭合**。

**结论：ALIGNED**。

---

## P8 闭环规则

| 结论态 | 项 | 主 Agent 动作 |
|---|---|---|
| ALIGNED | A1 / A2 / A3 / A4（附 `[KNOWN_DEVIATION]`：pre-tag）/ A5 / A6 / A7（P8 delta） | 通过，可 P8 commit。**commit 后主 Agent `git tag v0.71.0`** → CHECK 7 归零 → 5 项 pre-tag 红全绿（1625 passed / 0 failed / 2 skipped、consistency `--strict-errors-only` exit 0），复跑确认。 |
| （已闭合，非阻断） | A5.3 / A7.4（P4a 复审轮 HUMAN_CONFIRMED 的两条 doc-sync）| P8 已落地：`LIMITATIONS.md` 局限 2「派发路由缓解链」段 + `adr.md` ADR-013。逐字采用本报告附录草案、诚实边界句保留、关联 ADR-002 / 006 / RM-AG0060。**本任务全部 SELF-GATE 对齐项闭合**。 |
| （P8 / 未来迭代，非阻断） | tmux 观测层目标环境复跑 | `AGATE_DISPATCH_TMUX` 默认关；目标部署环境按 `docs/research/cross-platform-dispatch-mechanics.md` §10 在其自己 tmux 版本复跑后开启默认（`P4-implementation-P4c.md` `[DESIGN_GAP_REVIEWED]` + UPGRADING §3 v0.71.0 第 3 点已登记）。 |

**P8 delta 总结论：aligned**（A1-A7 全 ALIGNED；A4 附 `[KNOWN_DEVIATION]` = CHECK 7 pre-tag 时序，主 Agent `git tag v0.71.0` 后归零，非回归 / 非新问题）。

**P4a + P4b + P4c + P8 四批合并总结论：aligned** —— P4a 三轮终态 aligned（A5.3/A7.4 HUMAN_CONFIRMED）；P4b 两轮终态 aligned（A1 fix `classify_outcome` 按 cli 细分）；P4c 一轮 aligned（tmux 观测层，feature flag 默认关对应已确认 DESIGN_GAP）；P8 一轮 aligned（A5.3/A7.4 doc-sync 落地 + CHANGELOG / UPGRADING / roadmap / tech-debt / P1 收尾）。全量 pytest `5 failed / 1620 passed / 2 skipped` —— 5 failed **全部** = CHECK 7 pre-tag（DEBT0013 时序，`git tag v0.71.0` 后归零至 1625/0/2）；回归护栏（`phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` / `dispatch-protocol.md` / `agate_dispatch_route.py` / `check-events.py` / `agate/tests/` 的 `git diff HEAD` 无输出）成立。**P4 三批 + P8 收尾批可全部 commit**（各带 `self-gate-review:` trailer）。

---

## 附：P8 轮补充实跑（本次审查执行，2026-09-10）

- `python3 -m pytest agate/tests/ -q` → **5 failed / 1620 passed / 2 skipped**（155.17s）；5 failed = `test_con_1_check_1_yaml_parseable` / `test_con_6_check_7_version_badge_sync` / `test_env_adapt_docs.py::test_bdd_25_consistency_zero_error` / `test_tag0027_b1_phases_transfer_fields.py::test_bdd_5_consistency_worktree_still_green_regression` / `test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes` —— **全部断言「consistency 绿 / CHECK 7 PASS」，全部因 CHECK 7 pre-tag 红**。`1620 + 5 = 1625` = P4c 基线。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only 2>&1 | grep -E "ERROR \(|❌"` →
  ```
  ❌ FAIL  CHECK 7  version badge 与 git tag
  ERROR (1):
    ❌ README version badge v0.71.0 != 最新 tag v0.70.0 [README.md]
  ```
  **唯一 ERROR = CHECK 7**。CHECK 1 / 3 / 4 / 6 / 8 / 9 / 11 / 12 / 13 / 14 / 15 全 `✅ PASS`。
- `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（27 行，哈希链完整，ts 单调，judge 轮次×1）。
- **回归护栏（关键）**：`git diff HEAD -- agate/rules/phases.yaml agate/scripts/check-gate.py agate/scripts/check-state-transition.py agate/state-machine.md agate/dispatch-protocol.md agate/scripts/agate_dispatch_route.py agate/scripts/check-events.py agate/tests/` → **无输出**（P8 未碰 P4 代码 / 已定稿协议子节 / 测试 / 状态机 / gate 脚本）。
- `git diff HEAD --name-only`（HEAD = `8ad7834` P7 commit）→ `CHANGELOG.md` / `README.md` / `README.zh-CN.md` / `agate/LIMITATIONS.md` / `agate/UPGRADING.md` / `agate/adr.md` / `docs/design-notes/design-dispatch-routing.md` / `agate-workspace/{roadmap/roadmap.md, debt/tech-debt.md, tasks/TAG0034-dispatch-routing/{P1-requirements.md, .state.yaml, gate-events.jsonl}}` —— 全为 doc / 发布面 / 任务元数据。
- `grep -n "scope_resolved" agate/scripts/agate-frontmatter-check.py` → `37: "suggest_resolved", "scope_resolved", "change_type",`（合法 frontmatter 字段）；`check-scope-resolved.py:44 _scope_resolved_frontmatter` 读取 P1 frontmatter `scope_resolved` list。
- `grep -c "^## ADR-013" agate/adr.md` → 1；`grep -c "派发路由缓解链" agate/LIMITATIONS.md` → 1；`grep -c "^## \[0.71.0\]" CHANGELOG.md` → 1；`grep -c "### v0.71.0" agate/UPGRADING.md` → 1；`grep -c "version-v0.71.0" README.md README.zh-CN.md` → 各 1。
- `grep -n 'rules/dispatch-routing\.yaml' docs/design-notes/design-dispatch-routing.md` → 零命中（P7 `[DEVIATION]` 老串已清）。
