---
agent: implementer
implementation_dir: agate/
---

# P4-implementation — TAG0034 派发路由 P4b 批（static-batch 第 2 批，complexity: medium，依赖 P4a）

`[PROD_NOT_TOUCHED]`

实现落点（`implementation_dir` = `agate/`）：`agate/scripts/agate_dispatch_route.py` + `agate/scripts/agate-dispatch.py` + `agate/SETUP.md` + `agate/platform-notes.md` + `agate/dispatch-protocol.md` + `agate/tests/unit/test_tag0034_p4b.py`。

> 本批 = P4b：M5 端到端子进程 spawn（`dispatch_once` + `_route_main` 端到端分支 + I3 签名桥接）+ I1（`try_and_fall` 白名单化）+ I2（presence-parse 落 `produced_files` 侧）+ BDD-42（`routed_away_verdict_location`）+ M9（SETUP scaffold 小节）+ M10（platform-notes 结构化输出字段小节）+ 评审打回续跑协议文档。
> tmux 观测层（P4c，`build_subprocess_launch` / `tmux_cleanup_action`）不做——`test_tag0034_tmux.py::test_bdd_37/38` 按批次边界保持红。
> 自查 ≠ P5 gate。本文件只声明路径 + 改动 + 摘要，不预判 gate 结论。

## 改动清单

### 新增文件

| 文件 | 模块 | 内容 |
|---|---|---|
| `agate/tests/unit/test_tag0034_p4b.py` | 测试 | P4b 新增覆盖（不改 P3 既有断言）：`dispatch_once` 端到端 6 例（native 占位不 spawn / codex turn.completed+产出文件 → HAS_OUTPUT / opencode ProviderAuthError → INFRA_ERROR / 空返回 → NO_PARSEABLE_OUTPUT / spawn OSError → LAUNCH_FAIL / wait 超时 → INFRA_ERROR）；`presence_parse_ok` 变体（缺失 / 空 / frontmatter 未闭合 / 缺锚点 / OK / 无 frontmatter）；I2（空产出文件 → NO_PARSEABLE_OUTPUT；`classify_outcome` 的 NO_PARSEABLE_OUTPUT 分支无结构完整度判断，垃圾但非空产出 → HAS_OUTPUT）；I1（非契约 kind / None kind → `DispatchContractError`）；I5（回落 kind 携非法 reason → `DispatchContractError`）；I1 不误伤（三类基础设施 kind 仍正常回落）；I3（位置回调 ↔ kw-only 写入器适配层桥接落 1 条合法 `dispatch_route` 事件）；BDD-42（`routed_away_verdict_location` 恒 TASK_DIR）。15 例。 |

### 修改文件

| 文件 | 模块 | 改动点 |
|---|---|---|
| `agate/scripts/agate_dispatch_route.py` | M5 / I1 / I2 / BDD-42 / I5 / **A1 对齐** | **SELF-GATE alignment review A1（misaligned，低严重度）修复——`classify_outcome` 基础设施信号按 cli 细分对齐 P2-design §3.7 判定表 / platform-notes.md M10**：① `_INFRA_SIGNALS` 移出裸顶层 `{"type":"error"}` → 新常量 `_BARE_TOP_ERROR_SIGNALS`，**仅 `cli == "codex"`** 视为 INFRA_ERROR（MV3 `status:400`）；② 新常量 `_INFRA_SIGNALS_CLAUDE_ONLY`（`stop_reason:"error"` / `is_error:true`）+ helper `_claude_api_error(text)`（`api_error_status` 后跟非 null 数字）——`cli ∉ {codex,opencode}` 时命中 → INFRA_ERROR（夹具 `api_error.json`，此前误落 NO_PARSEABLE_OUTPUT）；③ 新增分支 2b——`cli == "opencode"` 且顶层 `{"type":"error"}` 无 ProviderAuth（MV6b UnknownError，夹具 `unknown_error.jsonl`）→ NO_PARSEABLE_OUTPUT，早于「非零退出」通用兜底返回（此前误落 INFRA_ERROR）。R1 守住：所有分支仍产出合法三值 `reason`（`infra_error` / `no_parseable_output`），无 `gate_fail`；两处路由行为仍是「回落下一候选」（只是账本 `reason` 标签更准）；`NO_PARSEABLE_OUTPUT` 分支仍不含任何结构完整度判断（I2 边界）。<br><br>其余新增（下同，不变）：`DispatchContractError`（`RuntimeError` 子类）、常量 `_FALLBACK_KINDS`（`{LAUNCH_FAIL,INFRA_ERROR,NO_PARSEABLE_OUTPUT}`）/ `_SUBPROCESS_CLIS`；`presence_parse_ok(path, *, required_anchors=None)`（I2 / N7：文件非空 + frontmatter 闭合且含 `key: value` + 必需锚点存在，**不含**内容完整度 / 质量判断）；`_default_subprocess_run(argv, *, timeout_s=None)`（裸 `subprocess.run` + 宽超时兜底 `AGATE_DISPATCH_TIMEOUT_S` 默认 1800s；`FileNotFoundError`/`OSError` → `killed_reason="spawn_oserror"`；`TimeoutExpired` → `"wait_timeout"`；P4c hook 位注释）；`dispatch_once(candidate, dispatch_context_path, *, effort_supported=False, expected_output=None, required_anchors=None, run=None, timeout_s=None, task_dir=None)`（cli ∉ `_SUBPROCESS_CLIS` → `Outcome("HAS_OUTPUT", None)` 占位不 spawn；否则 `build_dispatch_command` → `run` → presence-parse 填 `produced_files`（I2 落此处）→ `classify_outcome`）；`routed_away_verdict_location(cli)` 恒 `"TASK_DIR"`（BDD-42）。`try_and_fall` 改：I1 显式白名单——`kind == "HAS_OUTPUT"` 停；`kind not in _FALLBACK_KINDS`（含 `None`）→ `raise DispatchContractError`；I5——回落前 `reason not in _VALID_REASONS` → `raise DispatchContractError`。`classify_outcome` / `resolve` / `load_config` / `write_dispatch_route_event` 等 P4a 函数**未改签名、未改行为**。 |
| `agate/scripts/agate-dispatch.py` | M5 / I3 | `_route_main` 的 `form == "chain"` 分支拆三路：首候选 `cli == "native"` → 仍只输出路由计划 JSON（`form: "native"`，与 P4a 一致，native 由驱动会话代发）；否则（子进程形态首候选）→ 端到端 `try_and_fall`：`functools.partial(adr.dispatch_once, effort_supported=…, expected_output=…, task_dir=…)` 绑定额外 kwargs（保持 `try_and_fall` 对 `dispatch_once(cand, ctx)` 的 2 位置参数调用契约）+ I3 适配层闭包 `_write_event(phase_, tried_, final_)` 桥接到 kw-only `adr.write_dispatch_route_event(task_dir, phase_, tried=…, final=…, task_id=…)`（两处签名各自不动）；`DispatchContractError` → stderr + exit 1；输出 JSON 增 `final` / `tried` 字段（P4a 契约「只增不改」）。`effort_supported` 读 `AGATE_EFFORT_SUPPORTED == "1"`，`expected_output` 读 `AGATE_DISPATCH_EXPECT`。既有渲染路径（`_render_dispatch_context` / `_next_card_content` / `_SOURCE_MARKER` / `generated_by`）+ `form == "default"` 分支逐字节未触碰。 |
| `agate/SETUP.md` | M9 | 「步骤 2-Codex」之后新增小节「### 步骤 2-dispatch-routing：机器级档位绑定 scaffold（可选，TAG0034 / RM-AG0060）」：比照「步骤 2-Codex」per-platform onboarding 形态——机会式启用说明（不配置 = 逐字节现状）；`agate-workspace/dispatch-routing.yaml`（非协议本体 / 不触发 SELF-GATE / 全兜底）；`tier_bindings:`（机器级②）按本机现状填 + 探测命令（`command -v` / `claude --help \| grep -- --effort` 能力探测 / `models_cache.json` / `opencode models`）；`routes:`（项目级③）只引用档位名 → 跨机可移植；各 CLI 自动化环境绕过 flag（`--dangerously-skip-permissions` / `--dangerously-bypass-approvals-and-sandbox --skip-git-repo-check` / `--auto`）；`check-dispatch-routing.py` 校验；OpenCode `cli: native` 命名 subagent 间接路（约定名 `agate-route-<tier>`，无则该候选 `launch_fail` 自动回落）。 |
| `agate/platform-notes.md` | M10（结构化输出字段小节）| Codex 章之后新增顶层小节「## 跨 CLI 子进程结构化输出判成败字段（派发路由 / TAG0034）」：三平台判定表（HAS_OUTPUT / INFRA_ERROR / NO_PARSEABLE_OUTPUT 各列）——Claude Code `stop_reason == "end_turn"` + `result` 非空 + `modelUsage` 核实 model / `api_error_status` / `stop_reason == "error"`；Codex `turn.completed` vs `turn.failed` + 顶层 `type:error`（**退出码不可靠、turn 层为准**）+ item 级 `status:"failed"`（携 `exit_code`）**永不触发换候选**；OpenCode `step_finish.part.reason == "stop"` + `text` part / `ProviderAuthError` → infra_error / 纯空返回 → no_parseable_output / `UnknownError`。素材 = §5 MV1~MV7 + `agate/tests/fixtures/tag0034_*/`。含 routed-away judge verdict 落 `TASK_DIR` + 两校验器零改动说明。（P4a 已落 effort 能力探测行，本批未再动 Claude Code 章 effort 行。） |
| `agate/dispatch-protocol.md` | 评审打回续跑（design-note §2.4a / §3.9）| 「### 0. 派发路由」子节内、「retry / 回退时的路由」之后新增「**评审打回后的续跑（子进程 / native 两种形式都适用）**」段：同 target 优先平台官方续接、失败或换 target 则全新派发；续接产出仍走假完成校验（D2）；**续接失败无客观信号是已知缺口** → 按「续接优先、重起兜底」处理、不假装解决；**不需要实现续接的自动化**（人在评审循环里）、决策层留 hook 位。平台续接原语（`claude -p --resume` / `codex exec resume` / `opencode run -s` / `followup_task` 等）放 `> 实现注记：` 块（CHECK 14 护栏 1 合规——协议语义叙述面不裸露平台名）。 |

## 实现关键决策

- **M5 `dispatch_once` 签名**：前两个参数位置化（`candidate`, `dispatch_context_path`），其余 kw + 默认值——保持 `try_and_fall` 对回调 `dispatch_once(cand, ctx)` 的 2 位置参数调用契约（P3 `test_tag0034_tryfall.py` 注入的 mock 亦是此形态），`_route_main` 端到端用 `functools.partial` 绑定 `effort_supported` / `expected_output` / `task_dir`。
- **native / default / 未知 cli → HAS_OUTPUT 占位**：路由脚本不 spawn（native 由驱动会话代发，`_route_main` 首候选 native 时输出路由计划 JSON 即止，与 P4a `[DESIGN_GAP_REVIEWED]` 一致）。链中段出现 native 候选时 `dispatch_once` 同样返回 HAS_OUTPUT 占位（= 交回驱动会话），见 `[DESIGN_GAP]`。
- **I1 白名单化（R1 加固，必做）**：`try_and_fall` 显式判 `kind == "HAS_OUTPUT"` 停 / `kind in _FALLBACK_KINDS` 才回落 / 其它（含 `None` / 未来误加枚举）→ `raise DispatchContractError`。今日行为等价（`classify_outcome` 枚举闭合），但契约违例不再被静默当回落信号换候选。
- **I2 presence-parse 落 `produced_files` 侧（R1 CRITICAL 边界，必做）**：presence 级「frontmatter 可解析 + 必需锚点标题存在」判据在 `dispatch_once` 填 `produced_files` 处（`presence_parse_ok`）；`classify_outcome` 的 `NO_PARSEABLE_OUTPUT` 分支**未引入任何结构完整度 / 内容完整度判断**——只判「约定产出文件缺失或空 / 结构化输出空返回」。`test_classify_outcome_no_parseable_branch_has_no_structure_check` 锁死该边界（垃圾但非空产出 → HAS_OUTPUT）。
- **I3 签名桥接**：选「适配层闭包」而非「统一两处签名」——`write_dispatch_route_event(task_dir, phase, *, tried, final, task_id)` kw-only 契约（P3 `test_bdd_29` 依赖）与 `try_and_fall` 的 `write_event(phase, tried, final)` 位置回调契约（P3 `test_bdd_23/28` 依赖）都不动，`_route_main` 内一个 3 行闭包桥接。改动面最小、零回归风险。
- **`_default_subprocess_run` 宽超时兜底（N6）**：本批「先直接裸跑」——`subprocess.run(timeout=AGATE_DISPATCH_TIMEOUT_S 默认 1800s)`，`TimeoutExpired` → `killed_reason="wait_timeout"` → `classify_outcome` 归 `INFRA_ERROR`（宁宽勿紧）。tmux 包裹（`build_subprocess_launch`）+ RM-AG0055 命令流阈值卡死检测的接入点在 `_default_subprocess_run` 内以注释标出，归 P4c。**未自造紧超时、未改 `agate-cmdstream-*.py`**。
- **BDD-42 `routed_away_verdict_location(cli)` 恒 `"TASK_DIR"`**：judge 路由到 codex/opencode 子进程时 verdict + 证据仍落 `TASK_DIR`（铁律 2/3 不变）；`check-judge-verdict.py` / `check-p6-provenance.py` 纯 `TASK_DIR` 文件解析、不读平台 transcript 路径——本任务**零改动**这两个脚本（`test_bdd_42` 断言两脚本源码不含 `.codex/sessions` / `.claude/projects`）。
- **回归硬约束**：`agate/rules/phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py`（第 1-8 条 + 哈希链）/ `agate-cmdstream-adapters.py` / `agate-dispatch.py` 既有渲染路径 —— `git diff` 逐文件核，均零改动。`check-events.py` 第 8 条（P4a 落）本批未再动。

## I4 / I5 / I6 处理

- **I5（做）**：`try_and_fall` 写事件前用 `_VALID_REASONS` 自校每个回落候选的 `reason`，非三值 → `DispatchContractError`。`_VALID_REASONS` 常量不再是「模块内未引用」。
- **I4（不做，INFORMATIONAL，理由）**：`check-dispatch-routing.py` 对畸形混合条目（phase 级 spec 同时带 role 子键）/ 孤立 `effort:` 宽松——P4a-review 定性「低影响，非 P2 schema 契约内合法形态，不产生错误路由」。本批不碰 `check-dispatch-routing.py`（P4b 输出路径硬约束未含该文件；改它属 P4a schema 层范畴，跨批改同文件违反 §4.1 批次边界「同一文件不跨批改两轮」）。留待主 Agent 择机 / 后续任务。
- **I6（不做，INFORMATIONAL，理由）**：`agate_dispatch_route.py` import 时 `sys.path.insert(0, _HERE)` 副作用——P4a-review 定性「与仓库既有脚本模式一致，通常无害」。收窄它属跨模块风格改动、与 P4b 目标（M5 端到端 + 文档）无关，且 `agate-dispatch.py` 的 `_route_main` 依赖该 import 路径可用。本批不动，维持与既有脚本一致。

## [DESIGN_GAP]

[DESIGN_GAP: P2-design §3.7 / M5 未指定 `_route_main` 端到端 try-and-fall 时「约定产出文件路径」如何解析（HAS_OUTPUT 判据要求产出文件非空且骨架可解析，但 `(phase, role)` → 产出文件名无统一约定）。实现中自主决定：`dispatch_once` 的 `expected_output` 由 `_route_main` 从环境变量 `AGATE_DISPATCH_EXPECT` 取，未设则为 `None`；`expected_output is None` 时 `produced_files` 恒空 → 子进程即便结构化输出成功也判 `NO_PARSEABLE_OUTPUT` 回落（保守：宁可回落也不把「无法核实产出」当成功）。CI 不真跑 `_route_main` 端到端（无 dispatch-routing.yaml → form=default），此路径由人工真机复核 + 未来 P4c/续跑迭代收敛。]

[DESIGN_GAP: 候选链中段（非首位）出现 `cli: native` 候选时，端到端 `try_and_fall` 里 `dispatch_once` 返回 `HAS_OUTPUT` 占位（= 交回驱动会话代发），等价于「该候选即成功、停止回落」。P2-design 只明确了「首候选 native → `_route_main` 输出路由计划 JSON 即止」，未定义混合链的中段 native。实现按「native = 交驱动会话 = 有产出」处理，与 native 弱缓解形式的自动化天花板（主 Agent 机械横传 model）一致；未来若需「native 候选也参与真回落」需驱动会话侧回填 outcome。]

[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）。两条均为 P2-design 未定义的实现留白、决策方向与 P2 意图一致：① `expected_output` 走 `AGATE_DISPATCH_EXPECT` 环境变量、未设则保守回落（宁可回落也不把「无法核实产出」当成功）—— 符合 R1「收到 gate 能评产出才算成功」的保守侧；CI 不覆盖端到端路径（无配置 = form=default），真机迭代收敛。② 中段 native 候选 → HAS_OUTPUT 占位（交驱动会话代发）—— 与 P2-design §3.4 / dispatch-protocol.md 新节「cli: native 自动化天花板 = 主 Agent 机械横传 model」一致。均非偏离 P2，无需回 P2。P4b review + protocol-alignment-review 复核。]

## [SCOPE+] / [SCOPE_GAP] / [CLARIFY]

- 无 `[SCOPE+]`：未发现 P1/P2 未覆盖但必须做的新需求。
- 无 `[SCOPE_GAP]`：prompt 与 P2-design §1.1（M5/M9/M10）+ §4.1 P4b 行逐条对齐。
- 无 `[CLARIFY]`。

## 新增文件核对表

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/tests/unit/test_tag0034_p4b.py` | 无 P2-skeleton.md / 无 CODE-MAP.md 机制 | `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]` |

## 自查记录（非 gate）

- `python3 -m pytest agate/tests/ -k tag0034 -q --tb=short` → **76 passed / 2 failed**（`1537 deselected`）。
  - 转绿：`test_tag0034_subprocess.py::test_bdd_42`（`routed_away_verdict_location`）；`test_tag0034_docs.py::test_bdd_50`（consistency 0 ERROR，本批文档修订就位后）。
  - 新增 `test_tag0034_p4b.py` **18 passed**（15 初版 + 3 条 A1 alignment 断言：Claude Code `api_error.json` → INFRA_ERROR / OpenCode `unknown_error.jsonl` → NO_PARSEABLE_OUTPUT / Codex 裸 `type:error` 仍 INFRA_ERROR）。
  - 仍红（P4c 批次边界，符合预期）：`test_tag0034_tmux.py::test_bdd_37`（`build_subprocess_launch` 未实现）/ `test_bdd_38`（`tmux_cleanup_action` 未实现）。
  - P3 既有断言未改且不回归：`test_tag0034_tryfall.py`(10) / `test_tag0034_subprocess.py`(BDD-33~36) 等仍绿。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0（CHECK 1~15 全 PASS，0 ERROR / 329 WARNING）。
- `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（账本 14 行，哈希链完整，ts 单调）。
- `python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml` → exit 0（未改该校验器 / scaffold）。
- 回归硬约束：`python3 -m pytest agate/tests/regression/test_tag0034_zero_change.py agate/tests/unit/test_check_events.py agate/tests/unit/test_tag0027_b2_agate_dispatch.py agate/tests/unit/test_tag0027_b2_audit2_dual_anchor.py -q` → 25 passed（BDD-39 字节基线 + BDD-40 无配置 = 现状 + `check-events` 零改动 + `agate-dispatch` 渲染路径零改动仍绿）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py agate/scripts/agate-dispatch.py agate/tests/unit/test_tag0034_p4b.py` → All checks passed。
- 真机 flag 复核：本批未新起真 CLI（P4a MV9 已复核 `--resume` / `-s` / `--json` / `--output-format json` / `--dangerously-*` / `--auto` 全部仍有效、语义未变，Claude Code 2.1.266 / codex 0.153.4 / opencode 1.18.11）。`_default_subprocess_run` 的裸 spawn 路径仅在配置了子进程候选链时触发，CI 不覆盖。

## SELF-GATE 预告（供主 Agent，不 commit）

本批改 `agate/scripts/agate_dispatch_route.py` / `agate/scripts/agate-dispatch.py` / `agate/SETUP.md` / `agate/platform-notes.md` / `agate/dispatch-protocol.md` / `agate/tests/**` → 触发 SELF-GATE。commit 前主 Agent 派 `protocol-alignment-review`（A1-A7）+ C8 `review`，commit message 带 `self-gate-review:` trailer。
