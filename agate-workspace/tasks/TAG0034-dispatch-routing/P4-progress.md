
## P4a implementer — session_014jKy7LxVHNa1uwrMxuZ1Mz

### 输入读取完成 (2026-09-09)
- implementer.md 角色 / P4-dispatch-context-implementer-P4a.md / AGENTS.md / P0-brief.md
- P2-design.md §0-§11 (方案权威) / P3-progress.md (接口契约) — 读毕
- 测试契约文件读毕: conftest.py + test_tag0034_{schema,resolve,tryfall,events,native,interaction,docs}.py + regression/test_tag0034_zero_change.py
- 参考物读毕: check-maintainability.py:_load_config (88-148) / check-events.py 全文 / agate_common.py append_event (328-371) + resolve_workspace (570-599) / agate-dispatch.py main() (164-244)
- 回归基线确认: test_tag0034_zero_change.py → BDD-39 green (byte baseline), BDD-40 red (module missing, 预期)

### 实现顺序 (N3): M1 dispatch-tiers.yaml → M3 check-dispatch-routing.py → M2 dispatch-routing.yaml → M4 agate_dispatch_route.py → M4b agate-dispatch.py route → M6 check-events.py 第8条 → M7 dispatch-protocol.md → M8 architect.md → M12 design-note+roadmap

### P4a 完成 (2026-09-09)
- 新增: agate/rules/dispatch-tiers.yaml (M1) / agate/scripts/check-dispatch-routing.py (M3) / agate-workspace/dispatch-routing.yaml (M2) / agate/scripts/agate_dispatch_route.py (M4)
- 改: agate/scripts/agate-dispatch.py (M4b route 分支 + _route_main) / agate/scripts/check-events.py (M6 第8条) / agate/dispatch-protocol.md (M7 派发路由子节 + DEBT0039措辞②) / agate/assets/execution-roles/architect.md (M8 DEBT0039措辞①) / agate/platform-notes.md (M10 effort子片) / docs/design-notes/design-dispatch-routing.md (M12) / agate-workspace/roadmap/roadmap.md (M12)
- 自查:
  * pytest -k tag0034 → 57 passed / 3 failed (仅 subprocess::test_bdd_42 + tmux::test_bdd_37/38 = P4b/P4c，仍红符合预期)
  * P4a 目标文件 schema/resolve/tryfall/events/native/interaction/docs 全绿；zero_change 全绿 (BDD-39 字节基线 + BDD-40)
  * check-dispatch-routing.py scaffold exit 0；check-protocol-consistency --strict-errors-only exit 0 (0 ERROR)；check-events task dir exit 0
  * ruff check (4 脚本) All checks passed
  * 回归旁证 pytest -k "events or dispatch or consistency or protocol or tag0030 or provenance or judge_verdict or structure" → 340 passed / 1 failed (仅 P4b test_bdd_42)
- [DESIGN_GAP] ×1 (P4a _route_main chain-case 输出形态，P2 §3.5 留白)；无 [SCOPE+]/[CLARIFY]
- M10 归属说明: 实现顺序 M 清单未列 M10，但门槛要求 native.py 转绿 (含 platform-notes doc-assertion)，落地 effort 注明子片；M10 结构化输出字段小节仍归 P4b
- [PROD_NOT_TOUCHED]: 仅 worktree 内写，未碰主 checkout / ~/.agate

## P4a review (review 子 Agent — session_014jKy7LxVHNa1uwrMxuZ1Mz) — 2026-09-09

- 输入读毕：review.md 角色 / P4-dispatch-context-review.md / AGENTS.md / P0-brief.md / P2-design §3.3/§3.6/§3.7/§3.8 + N6/N7 / P2-review 8 条锁定决策 + T1/T2/T3 / P4-implementation.md + P4-progress.md
- 代码逐行核：agate_dispatch_route.py（451 行全文）/ check-dispatch-routing.py（235 行全文）/ check-events.py diff（第 8 条）/ agate-dispatch.py diff（route 分支）/ dispatch-tiers.yaml / dispatch-routing.yaml
- R1 三处闭合核实：
  * ① classify_outcome kind 枚举 = {LAUNCH_FAIL, INFRA_ERROR, NO_PARSEABLE_OUTPUT, HAS_OUTPUT}，无 GATE_FAIL；reason ∈ 三值 / None。HAS_OUTPUT = presence 级（produced_files 非空即返回），NO_PARSEABLE_OUTPUT 未掺结构完整度 → 不触发 CRITICAL。
  * ② try_and_fall 回落 = 非 HAS_OUTPUT（因枚举闭合 = 恰好三类基础设施信号）。附 I1：黑名单逻辑 vs 设计白名单，P4b 加固。
  * ③ check-events.py 第 8 条：dispatch_route candidates_tried[].reason ∉ 三值 → exit 1；第 1-7 条 + 哈希链算法未改。
  * R1 结论：无 CRITICAL。P4a 无 dispatch_once/子进程/循环运行，R1 结构性闭合、P4b 复验。
- 回归 diff 核：phases.yaml / check-gate.py / check-state-transition.py / state-machine.md / check-judge-verdict.py / check-p6-provenance.py / agate-cmdstream-adapters.py = git diff --stat 空（零字节改动）。agate-dispatch.py 只加 route 分支 + _route_main。check-events.py 只加第 8 条。
- resolve 算法：优先级序 / (phase,role)>phase / standard 短路不经 tier_bindings / tier 缺绑定回落 default / effort 合并 dict(cand) 不 mutate 调用方 / T1 返回契约键集恒 {form,chain,model,effort} —— 全部符合 §3.3。
- load_config：逐档对照 check-maintainability.py:_load_config（88-148），四档兜底形态一致。load_factory_defaults 全兜底。
- build_dispatch_command：Codex -c model_reasoning_effort= / OpenCode --variant / Claude Code 按 effort_supported（调用方传入）；无版本号硬编码（grep 确认）；model None → 不传 --model。
- write_dispatch_route_event：复用 agate_common.append_event，不写 state_transition / 不动 retries / 不触发 PAUSED。
- 枚举一致性：reason 三值（_VALID_REASONS == DISPATCH_ROUTE_REASONS）/ cli 四值 / effort 三值 / tier 白名单 —— 三处定义一致。
- 抽查测试真对应：test_bdd_19 / test_bdd_25 / test_bdd_28 断言逐行对照实现 = 真实语义校验、非绕过。
- 命令复跑：pytest -k tag0034 = 57 passed / 3 failed（3 红 = test_bdd_42 P4b + test_bdd_37/38 P4c，批次边界一致）；P4a 目标 6 文件 39 passed；zero_change 2 passed；test_check_events + tag0027_b2 ×2 = 23 passed 零改动仍绿；ruff 4 脚本 clean；check-events task dir exit 0；check-dispatch-routing scaffold exit 0；check-maintainability agate-workspace/tasks/TAG0034-dispatch-routing exit 0（violations 空，无需 known-violations.md）。
- INFORMATIONAL ×6（I1~I6），均不阻断 P4a：I1 try_and_fall 白名单化 / I2 N7 presence-parse 落 P4b produced_files 侧且禁塞 NO_PARSEABLE_OUTPUT / I3 write_event 回调↔writer 签名缝 / I4 校验器对畸形混合条目宽松 / I5 _VALID_REASONS 未引用 / I6 import 时 sys.path 副作用。
- 产出：P4-review.md（Header status: approved / agent: review / implementation_dir: agate/，经 agate-md-field-set.py 写入，无缺失字段）。
- [PROD_NOT_TOUCHED]：仅 worktree 内读；写仅 P4-review.md + P4-progress.md。

### P4a alignment 修复 (protocol-alignment-review misaligned)
- 根因: 新 gate 脚本 check-dispatch-routing.py 未登记 check-protocol-consistency.py 的 SCRIPT_ALIGNMENT_ANCHORS → CHECK9-coverage WARNING + test_protocol_alignment_review.py::test_sg_6 FAIL
- 修复: SCRIPT_ALIGNMENT_ANCHORS 追加一条 (script=check-dispatch-routing.py, keywords=[VALID_CLI,VALID_EFFORT,fallback], 无 callers)
- 自查: check-protocol-consistency --strict-errors-only exit 0 (CHECK 9 PASS, WARNING 330→329) / pytest test_protocol_alignment_review.py = 8 passed (test_sg_6 绿) / pytest -k tag0034 = 57 passed 3 failed (未回归) / ruff check-protocol-consistency.py clean

## P4b 批 review (review 子 Agent) — 2026-09-10

- 输入读毕：coordinator P4b dispatch message / P4-implementation-P4b.md + 2 条 [DESIGN_GAP_REVIEWED] / test_tag0034_p4b.py（15 例全文）/ git diff agate_dispatch_route.py + agate-dispatch.py 逐行 / classify_outcome 当前源码逐行。
- R1 + 回归复核（P4b 首要项）：
  * ① I1 白名单落地：try_and_fall 现显式 kind=="HAS_OUTPUT" 停 / kind in _FALLBACK_KINDS 才回落 / 其它（含 None / 未来误加枚举）→ raise DispatchContractError。I5 叠加：reason not in _VALID_REASONS → raise。与 check-events 第 8 条形成双层强制。测试 test_try_and_fall_raises_on_non_contract_kind / _none_kind / _i5_bad_reason / _whitelist_still_falls_back 真对应、复跑绿。→ 真闭合 P4a-I1 稳健性缺口。
  * ② I2 边界：presence_parse_ok 新函数（文件非空 + frontmatter 闭合 + 必需锚点，无内容完整度判断）只在 dispatch_once 填 produced_files 处调用。classify_outcome 逐字节未改（git diff --stat 空），NO_PARSEABLE_OUTPUT 分支无结构判断。test_classify_outcome_no_parseable_branch_has_no_structure_check 锁死「垃圾但非空产出 → HAS_OUTPUT」。→ R1 CRITICAL 边界未破。
  * ③ 回归 diff：phases.yaml / check-gate.py / check-state-transition.py / state-machine.md / check-judge-verdict.py / check-p6-provenance.py / check-events.py（第 1-8 条+哈希链）/ check-dispatch-routing.py / agate-cmdstream-adapters.py / dispatch-tiers.yaml = git diff --stat 空（零字节）。agate-dispatch.py 两 hunk 均在 _route_main 内；既有渲染路径 + form=="default" 分支未触碰。BDD-42 依赖的两校验器零改动、断言成立。回归 25 passed。
  * ④ _default_subprocess_run：subprocess.run(timeout= 默认 1800s 可配 + ValueError 兜底)；FileNotFoundError/OSError → spawn_oserror → LAUNCH_FAIL；TimeoutExpired → wait_timeout → INFRA_ERROR（N6）。未自造紧超时、未改 cmdstream。
  * ⑤ 两条 [DESIGN_GAP]：#1 expected_output 走 env、未设保守回落（理由码 no_parseable_output，回落终点恒 default，非「试到过 gate 就停」）；#2 中段 native → HAS_OUTPUT 占位（交驱动会话、与 gate verdict 无关）。均不引入模型购物口子。[DESIGN_GAP_REVIEWED] 已确认，评审同意。
  * ⑥ 抽查 test_dispatch_once_codex_turn_completed... / test_dispatch_once_i2_empty_produced_file... / test_i3_write_event_adapter... —— 断言与实现路径逐行吻合，非绕过；test 内 _write_event 闭包与 _route_main 生产闭包同构。
- 门槛复跑：pytest -k tag0034 = 73 passed / 2 failed（test_bdd_37/38 P4c tmux，批次边界一致）；check-protocol-consistency --strict-errors-only exit 0；check-maintainability agate-workspace/tasks/TAG0034-dispatch-routing exit 0（violations 空）；check-events task dir exit 0（14 行）；check-dispatch-routing scaffold exit 0；回归 25 passed；ruff 3 文件 clean。
- INFORMATIONAL（不阻断）：P4b-I1（_default_subprocess_run 丢弃 stderr → 部分 infra 错误诊断丢失，classify_outcome 非零退出兜底）/ P4b-I2（except (FileNotFoundError, OSError) 冗余）/ P4b-I3（_route_main 子进程端到端分支无 CI 覆盖，仅 try_and_fall 单元层覆盖桥接）；P4a 遗留 I4/I6 implementer 以批次边界理由暂缓、理由成立、评审同意。→ 转 P4c / 主 Agent 择机。
- 产出：P4-review.md 追加「## P4b 批评审」+「## 合并结论（P4a + P4b）」节；Header status 保持 approved（P4a+P4b 合并、CRITICAL 0），agent = review（非 main）。
- [PROD_NOT_TOUCHED]：仅 worktree 内读；写仅 P4-review.md + P4-progress.md。

## P4b 批 implementer — alignment A1 修复轮 (session_014jKy7LxVHNa1uwrMxuZ1Mz) — 2026-09-10

- 上一轮额度中断前 P4b 产出已落盘（M5 dispatch_once + _route_main 端到端 + I3 桥接 / I1 白名单化 / I2 presence_parse_ok / I5 reason 自校 / BDD-42 routed_away_verdict_location / M9 SETUP scaffold 小节 / M10 platform-notes 结构化输出字段小节 / dispatch-protocol.md 评审打回续跑段 / test_tag0034_p4b.py 15 例）。C8 review approved。
- 本轮：protocol-alignment-review misaligned（A1，低严重度）—— classify_outcome 2 处 reason-code 归类与 P2-design §3.7 判定表 / platform-notes.md M10 不一致。按 option a 修 classify_outcome 对齐 §3.7（不改 M10 / §3.7）：
  * ① Claude Code API error（fixture api_error.json：stop_reason:"error" + api_error_status:401 + is_error:true）→ 此前无信号误落 NO_PARSEABLE_OUTPUT。新增 _INFRA_SIGNALS_CLAUDE_ONLY（stop_reason:"error" / is_error:true）+ _claude_api_error(text)（api_error_status 后跟非 null 数字），cli ∉ {codex,opencode} 命中 → INFRA_ERROR。
  * ② OpenCode UnknownError（fixture unknown_error.jsonl：{"type":"error","error":{"name":"UnknownError"}}）→ 此前裸子串 '"type":"error"' 误落 INFRA_ERROR。裸顶层 error 子串移出 _INFRA_SIGNALS → 新常量 _BARE_TOP_ERROR_SIGNALS，仅 cli=="codex" 视 INFRA_ERROR（MV3 status:400）；新增分支 2b：cli=="opencode" 且裸顶层 error 无 ProviderAuth → NO_PARSEABLE_OUTPUT，早于「非零退出」通用兜底返回。
  * R1 守住：所有分支仍产出合法三值 reason（infra_error / no_parseable_output），无 gate_fail；两处路由行为仍是「回落下一候选」（账本 reason 标签更准）；NO_PARSEABLE_OUTPUT 分支仍不含结构完整度判断（I2 边界）。
- test_tag0034_p4b.py 补 3 条断言（不改 P3 断言）：Claude Code api_error.json → INFRA_ERROR / OpenCode unknown_error.jsonl → NO_PARSEABLE_OUTPUT / Codex 裸 type:error 仍 INFRA_ERROR。共 18 例。
- 自查：pytest -k tag0034 = 76 passed / 2 failed（test_bdd_37/38 P4c tmux，批次边界一致；test_bdd_33~36 不回归）；check-protocol-consistency --strict-errors-only exit 0（CHECK 1~15 全 PASS，0 ERROR）；check-events task dir exit 0（14 行）；回归护栏 test_tag0034_zero_change + test_check_events + test_tag0027_b2 ×2 = 25 passed；ruff（agate_dispatch_route.py + agate-dispatch.py + test_tag0034_p4b.py）clean。全量 pytest 见下（后台跑）。
- 产出记录：P4-implementation-P4b.md（frontmatter agent: implementer + implementation_dir: agate/，implementation_dir 经 agate-md-field-set.py 复核）；改动清单增「A1 对齐」条目 + 自查记录更新 76 passed / 18 例。
- [DESIGN_GAP] ×2（P4b 文件内，行首单行）：#1 _route_main 端到端「约定产出文件路径」走 env AGATE_DISPATCH_EXPECT、未设保守回落；#2 中段 native 候选 → HAS_OUTPUT 占位交驱动会话。无 [SCOPE+]/[SCOPE_GAP]/[CLARIFY]。
- I4/I6 未做（INFORMATIONAL，理由记 P4b 文件）：I4 改 check-dispatch-routing.py 属 P4a schema 层、跨批改同文件违反 §4.1 批次边界；I6 sys.path 收窄与 P4b 目标无关且 _route_main import 依赖该路径。I5 已做（try_and_fall 用 _VALID_REASONS 自校）。
- [PROD_NOT_TOUCHED]：全程仅 worktree 内写，未碰主 checkout / ~/.agate。

## P4c 批 implementer — tmux 观测层 (session_014jKy7LxVHNa1uwrMxuZ1Mz) — 2026-09-10

- 输入读毕：implementer.md 角色 / P4-dispatch-context-implementer-P4c.md（强制指令）/ AGENTS.md / P0-brief.md / test_tag0034_tmux.py 契约（BDD-37/38 全文）/ P2-design.md §3.10 + §3.9 + §4.1 P4c 行 / P4-review.md P4b 节 3 条 INFORMATIONAL / P4-implementation-P4b.md（hook 位 + 决策）/ P4-progress.md 尾部 / dispatch-protocol.md「### 0. 派发路由」子节 / design-dispatch-routing.md §2.6+§3 / check-protocol-consistency.py CHECK 14 平台名护栏 / regression baseline json（不含 agate_dispatch_route.py / dispatch-protocol.md）。
- 实现（implementation_dir = agate/）：
  * agate/scripts/agate_dispatch_route.py：新增纯逻辑 helper build_subprocess_launch（tmux_available=True → tmux new-session -d -s <ns> '<cmd> | tee <cap>; echo 结束标记; echo 倒计时; sleep N'；False → list(cmd) 裸跑）+ tmux_cleanup_action（falsy session→noop / 无 client→kill_now / 有 client 且 elapsed<=N+margin→let_countdown / 否则→force_kill）。接入 _default_subprocess_run：_maybe_tmux_wrap（默认关 AGATE_DISPATCH_TMUX=1 + shutil.which("tmux") 才包裹，session=agate-{TASK_ID}-{PHASE}-{int(time.time())}）+ _tmux_teardown（has-session 判断 + 容忍 kill-session 非零退出）+ _tmux_collect（new-session -d 立即返回后轮询生命周期，命令跑完按 tmux_cleanup_action 决定 kill / 等待，返回 capture 全文）。P4b-I1 stderr 透传 sys.stderr（不并入判定文本）。P4b-I2 except (FileNotFoundError, OSError) → except OSError。import 增 shutil/tempfile/time。classify_outcome/resolve/load_config/try_and_fall/dispatch_once/presence_parse_ok 未改签名未改行为。
  * agate/dispatch-protocol.md「### 0. 派发路由」子节：新增「tmux 观测层（可选，仅子进程形式）」小段——包裹判定 / 命名空间 session / 退出倒计时（默认 15s）/ 清理逻辑（list-clients 空→kill 跳倒计时 / 非空→让倒计时收尾 / 挂死超 N+余量10s→兜底 kill，先 has-session）/ 明确不做（send-keys / capture-pane 回传 / 跨轮复用）/ 目标环境代表性 W2（WSL2+tmux3.4，非容器/CI/物理机，须复跑落地前复核项，未通过停在「定稿+待落地验证」不阻塞、可整体切除）/ 本机默认关。全中文、无 CHECK 14 禁词。
  * agate/tests/unit/test_tag0034_p4c.py：12 例（build_subprocess_launch 边界 / tmux_cleanup_action noop+精确边界 / _maybe_tmux_wrap 默认关=现状 3 态 / _default_subprocess_run P4b-I1 stderr 透传+不并入 / P4b-I2 FileNotFoundError→spawn_oserror / P4b-I3 桥接端到端 真 append_event 账本 1 条 dispatch_route 事件）。
- P4b-review 3 条 INFORMATIONAL：I1（stderr）做——透传诊断面不并入判定；I2（冗余 except）做——收敛 except OSError；I3（_route_main 无 CI 覆盖）部分做——加桥接端到端单测（partial + 适配层闭包 + 真哈希链账本），完整 _route_main 进程级调用注明不做（连字符模块 + form=default 门控 + 假 CLI 平台敏感，与 AGENTS.md 平台无关硬约束冲突）+ 理由。
- 切除条款处理：不整体切除。两个 helper 纯逻辑（BDD-37/38 转绿），_default_subprocess_run 接入 feature flag AGATE_DISPATCH_TMUX 默认关。标 [DESIGN_GAP: tmux 包裹待目标环境验证]（本机 WSL2+tmux3.4 冒烟通过，目标环境代表性未定 R10/W2，按 P2-design §3.10「停在定稿+待落地验证不阻塞 P8」）。
- 自查（非 gate）：
  * pytest -k tag0034 = 90 passed / 0 failed（test_bdd_37/38 转绿；新增 test_tag0034_p4c.py 12 passed；P3 断言未改不回归）。
  * 回归护栏 test_tag0034_zero_change + test_check_events + test_tag0027_b2 ×2 = 25 passed（BDD-39 字节基线 + BDD-40 不配置=现状仍绿）。
  * check-protocol-consistency.py --strict-errors-only exit 0（CHECK 1~15 全 PASS，0 ERROR / 329 WARNING —— 与 P4b 后基线一致，tmux 小段未新增 WARNING、未触 CHECK 14）。
  * check-events.py agate-workspace/tasks/TAG0034-dispatch-routing exit 0（账本 14 行，哈希链完整，ts 单调）。
  * ruff check agate/scripts/agate_dispatch_route.py agate/tests/unit/test_tag0034_p4c.py → All checks passed。
  * 本机 tmux 冒烟（timeout 30，WSL2 + tmux 3.4）：包裹 launch 跑通 → _tmux_collect 读到 capture → session 清理干净、has-session 非零退出容忍；裸路径返回原样 cmd；中文收尾 echo 在 pane 无报错。
- 产出记录：P4-implementation-P4c.md（frontmatter agent: implementer + implementation_dir: agate/ 经 agate-md-field-set.py 写入/复核）；[DESIGN_GAP] ×1（grep -c '^\[DESIGN_GAP:' = 1）；无 [SCOPE+]/[SCOPE_GAP]/[CLARIFY]。
- SELF-GATE 预告：改 agate/scripts/agate_dispatch_route.py + agate/dispatch-protocol.md + agate/tests/** → 触发。commit 前主 Agent 派 protocol-alignment-review (A1-A7) + C8 review，commit message 带 self-gate-review: trailer。
- [PROD_NOT_TOUCHED]：全程仅 worktree 内写，未碰主 checkout / ~/.agate（agate-md-field-set.py 用 ~/.agate 稳定版只读调用、只写 worktree 内产出文件）。

## P4c 批 review (review 子 Agent) — 2026-09-10

- 输入读毕：coordinator P4c dispatch message / P4-implementation-P4c.md + [DESIGN_GAP_REVIEWED] / git diff agate_dispatch_route.py + dispatch-protocol.md 逐行 / test_tag0034_p4c.py 全文 12 例。
- 重点复核：
  * ① R1 不受 tmux 影响：classify_outcome / try_and_fall / resolve / dispatch_once / build_dispatch_command / presence_parse_ok 逐 hunk 核零改动（diff 仅命中 module docstring + import 三行 + 新增 tmux 节 + _default_subprocess_run 体）。tmux 路径 classify_outcome 拿到的 stdout = tee capture 全文 = 裸跑 stdout（tee 不改字节、收尾 echo/sleep 在 ; 后不进 tee 管道）。stderr 透传只写诊断面不进判定文本（test_default_subprocess_run_stderr_not_merged_into_stdout 锁死）。
  * ② feature flag 默认关 ≡ P4b：_maybe_tmux_wrap `!= "1" or not which(tmux)` 短路 → flag 未设时 which(tmux) 都不调、返回裸 argv + (None,None)。launch=list([str(a) for a in argv]) → subprocess.run(launch) == P4b。TimeoutExpired/正常返回分支 `if tmux_capture:` 均 None → 走 P4b 原路。except OSError vs except (FileNotFoundError, OSError) 捕获集合相同。唯一新增副作用 = flag 关时若 _default_subprocess_run 被调且 stderr 非空 → 多一行 sys.stderr.write（P4b-I1 要求的修复、不改返回/判定/路由/gate）。「不配置=现状」不受影响（无配置 → form=default → _default_subprocess_run 根本不被调）。
  * ③ tmux 分支健康：new-session -d 立即返回、外层 subprocess.run 有 timeout；_tmux_collect 有 hard_cap_s=timeout_s（默认1800s）硬上限 → 无死循环无泄漏；_tmux_teardown 先 has-session 判断 + 容忍 kill-session 非零退出 + except OSError pass。附 P4c-I2：内层 has-session/list-clients/kill-session 三处 subprocess.run 无 timeout=（loop 由 hard_cap_s 兜底不致无界，仅 flag-ON 路径）。
  * ④ [DESIGN_GAP tmux 待目标环境验证]：feature flag 默认关是 P2-design §3.10「定稿+待落地验证、不阻塞、可切除」条款的正确落地形态——机制完整实现+单测覆盖、IO 集成 gated。默认路径无副作用。[DESIGN_GAP_REVIEWED] 已确认，评审同意，非切除非偏离。
  * ⑤ P4b-I1 已做（透传诊断面、双侧 test 锁死）；P4b-I2 已做（except OSError 收敛、捕获集合不变）；P4b-I3 部分闭合（test_route_bridge_end_to_end 以 _route_main 相同组合 partial+闭包+真 append_event 哈希链跑 try_and_fall）+ 残留理由复核站得住（平台敏感假 CLI 与 AGENTS.md「测试不得硬编码单平台假设」冲突 / env-DI seam 触 R1 判定路径；桥接测试已覆盖真实风险；人工真机复核为文档化兜底）。
  * ⑥ 抽查 test_build_subprocess_launch_wrap_has_countdown_and_tee / test_tmux_cleanup_action_boundary_inclusive / test_default_subprocess_run_stderr_not_merged_into_stdout / test_route_bridge_end_to_end —— 断言与实现逐段吻合、真实语义校验、非绕过。
  * 回归 diff：phases.yaml / check-gate / check-state-transition / 状态机 / check-judge-verdict / check-p6-provenance / check-events（1-8条+哈希链）/ check-dispatch-routing / agate-cmdstream-adapters / agate-dispatch（含渲染路径）/ dispatch-tiers.yaml = git diff --stat 空。本批仅改 agate_dispatch_route.py + dispatch-protocol.md + 新增 test_tag0034_p4c.py。
- 门槛复跑：pytest -k tag0034 = 90 passed / 0 failed（test_bdd_37/38 转绿）；check-protocol-consistency --strict-errors-only exit 0（329 WARNING / 0 ERROR，与 P4b 基线一致）；check-maintainability agate-workspace/tasks/TAG0034-dispatch-routing exit 0（violations 空）；check-events task dir exit 0（14 行）；回归 25 passed；ruff 2 文件 clean。
- INFORMATIONAL（不阻断，均限 flag-ON 待落地验证路径）：P4c-I1（tmux 路径 exit_code=None → 窄口径「非零退出+无结构化信号+无产出文件」时 reason 码 INFRA_ERROR↔NO_PARSEABLE_OUTPUT 分叉；两者都回落、gate 结果一致、仅审计串不同）/ P4c-I2（tmux IO helper 内层 subprocess.run 缺 timeout=）/ P4b-I3 残留（完整进程级集成测试转未来任务）/ P4a I4/I6（主 Agent 择机）。
- 产出：P4-review.md 追加「## P4c 批评审」+ 更新「## 合并结论（P4a + P4b + P4c）」；Header status = approved（三批合并、CRITICAL 0、无需切除），agent = review（非 main）。
- [PROD_NOT_TOUCHED]：仅 worktree 内读；写仅 P4-review.md + P4-progress.md。
