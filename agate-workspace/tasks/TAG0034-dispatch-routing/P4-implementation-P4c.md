---
agent: implementer
implementation_dir: agate/
---

# P4-implementation — TAG0034 派发路由 P4c 批（static-batch 第 3 批，complexity: low，依赖 P4b，可整体切除）

`[PROD_NOT_TOUCHED]`

实现落点（`implementation_dir` = `agate/`）：`agate/scripts/agate_dispatch_route.py` + `agate/dispatch-protocol.md` + `agate/tests/unit/test_tag0034_p4c.py`。

> 本批 = P4c：tmux 观测层。让 `test_tag0034_tmux.py::test_bdd_37` + `test_bdd_38` 由红转绿（不改 P3 断言）。
> 两个 helper（`build_subprocess_launch` / `tmux_cleanup_action`）为纯逻辑、CI 直跑；`_default_subprocess_run` 的 tmux 包裹接入**默认关**（`AGATE_DISPATCH_TMUX=1` 才启用），本机 WSL2 + tmux 3.4 冒烟通过、目标环境代表性未定 → 「定稿 + 待落地验证」姿态，见下方 `[DESIGN_GAP]`。
> 自查 ≠ P5 gate。本文件只声明路径 + 改动 + 摘要，不预判 gate 结论。

## 改动清单

### 新增文件

| 文件 | 模块 | 内容 |
|---|---|---|
| `agate/tests/unit/test_tag0034_p4c.py` | 测试 | P4c 新增覆盖（BDD-37/38 断言留在 `test_tag0034_tmux.py`，不改）：`build_subprocess_launch` 纯逻辑边界（裸路径返回新 list 且身份不别名 cmd / 包裹路径含 `tee <capture>` + 末尾 `sleep <N>` 退出倒计时 / `countdown_n` 可配）；`tmux_cleanup_action` 边界（空 session → `noop` / `elapsed == N + margin` 边界含入 `let_countdown` / 越界 → `force_kill`）；`_maybe_tmux_wrap` 默认关 → 裸 argv 逐字节现状、开关开但 `which tmux` 失败 → 裸 argv、开关开 + `which tmux` 成功 → `tmux new-session` 包裹 + 命名空间 session（`agate-<task>-<phase>-<ts>`）；`_default_subprocess_run` 的 P4b-I1（stderr 透传诊断面、不并入判定文本）+ P4b-I2（`except OSError` 捕获 `FileNotFoundError` → `spawn_oserror`）；P4b-I3 桥接端到端（`functools.partial` + 适配层闭包 + 真 `append_event` 哈希链账本跑 `try_and_fall` → 一次回落落 1 条合法 `dispatch_route` 事件）。12 例。 |

### 修改文件

| 文件 | 模块 | 改动点 |
|---|---|---|
| `agate/scripts/agate_dispatch_route.py` | tmux 观测层（P4c） | **新增 2 个 importable 纯逻辑 helper**（`test_tag0034_tmux.py` 契约）：<br>① `build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name, countdown_n=15) -> list[str]` —— `tmux_available=True` → `["tmux","new-session","-d","-s",<session_name>, "<cmd 串> | tee <capture_path>; echo '=== 派发结束 ==='; echo '…N 秒后关闭…'; sleep <N>"]`（末项一条 shell 串）；`tmux_available=False` → `list(cmd)` 裸跑。<br>② `tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s) -> str ∈ {"kill_now","let_countdown","force_kill","noop"}` —— falsy session → `noop`；无 client → `kill_now`（跳倒计时）；有 client 且 `elapsed_s <= countdown_n + margin_s` → `let_countdown`；否则 → `force_kill`（余量 10s，P2-design §3.10）。<br><br>**接入 `_default_subprocess_run`（P4b 留的 hook 位）**：新增 `_maybe_tmux_wrap(argv_str)`（**默认关**：`AGATE_DISPATCH_TMUX=1` 且 `shutil.which("tmux")` 成功才包裹；session 名 `agate-{AGATE_DISPATCH_TASK_ID}-{AGATE_DISPATCH_PHASE}-{int(time.time())}`，capture 路径取 `AGATE_DISPATCH_CAPTURE` 或临时目录）+ `_tmux_teardown`（先 `has-session` 判断、容忍 `kill-session` 对已消失 session 的非零退出，MV11）+ `_tmux_collect`（`tmux new-session -d` 立即返回后轮询 session 生命周期，命令跑完进入收尾倒计时后按 `tmux_cleanup_action` 决定 `kill-session` / 等待，返回 capture 文件全文）。`_default_subprocess_run` 主体：`_maybe_tmux_wrap` → `subprocess.run(launch, ...)`；tmux 路径读 capture 文件当 stdout、`exit_code=None`（退出码不经 tmux 透出，判定走结构化流，§3.7）；裸路径与改动前逐字节等价。<br><br>**P4b-I1（做）**：`_default_subprocess_run` 捕获的 `proc.stderr` 非空则 `sys.stderr.write` 透传到路由脚本诊断面——**不并入** `classify_outcome` 的判定文本（判定输入与裸跑一致 → R1 完整性不破）。<br>**P4b-I2（做）**：`except (FileNotFoundError, OSError)` → `except OSError`（`FileNotFoundError ⊂ OSError`，去冗余）。<br><br>模块头 import 增 `shutil` / `tempfile` / `time`（stdlib，isort 有序）。模块 docstring 补 2 个 helper 条目 + tmux 默认关说明。`classify_outcome` / `resolve` / `load_config` / `try_and_fall` / `build_dispatch_command` / `dispatch_once` / `presence_parse_ok` **未改签名、未改行为**（`try_and_fall` 逐字节未动）。 |
| `agate/dispatch-protocol.md` | 「### 0. 派发路由」子节 | 「弱缓解 vs 强缓解」段后新增「**tmux 观测层（可选，仅子进程形式）**」小段：`which tmux` 成功则包 `tmux new-session -d` 供人 `attach`、路由脚本读 `tee` 的 capture 文件、失败裸跑；两路径 `dispatch_route` 留痕 + gate 结果逐字节一致；session 带命名空间；wrapper 自带退出倒计时（默认 15s、可配）；清理逻辑（`list-clients` 空 → `kill-session` 跳倒计时 / 非空 → 让倒计时收尾 / 倒计时脚本挂死超「倒计时 + 余量 10s」→ 兜底 `kill-session`，先 `has-session` 判断容忍非零退出）；**明确不做**：`send-keys` 交互 / `capture-pane` 内容解析回传主 Agent / 跨轮次 session 复用；**目标环境代表性**（WSL2 + tmux 3.4，非容器 / CI / 物理机——目标部署环境须在其自己 tmux 版本复跑跨平台机制调查落地前复核项，未通过则停在「定稿 + 待落地验证」、不阻塞发布、可整体切除）；本机接入默认关亦为「待落地验证」姿态的一部分。CHECK 14 护栏：小段全中文、无禁词（`OpenCode` / `Claude Code` / `DSH` / `workflow` / `goal` / `task`），consistency `--strict-errors-only` exit 0、WARNING 计数不变（329）。 |

## 实现关键决策

- **两个 helper 纯逻辑、零 IO**：`which tmux` 判定由调用方（`_maybe_tmux_wrap`）做、结果作 `tmux_available` 传入；`tmux_cleanup_action` 只做分支判定、不执行 `kill-session`。CI 直跑、无需 mock tmux（`test_tag0034_tmux.py` 契约即如此）。
- **`build_subprocess_launch` 包裹串含退出倒计时**：P2-design §3.10 明确「wrapper 命令末尾自带收尾脚本——跑完打结束标记 + N 秒倒计时」。shell 串 = `"<cmd> | tee <capture>; echo '=== 派发结束 ==='; echo '…N 秒后关闭…'; sleep <N>"`。`| tee` 只旁路一份、不改字节 → capture 内容 == 裸跑 stdout（BDD-37「两路径 gate 结果逐字节一致」/ R1）。收尾 `echo` 打在 pane、不进 `tee` 的管道 → 不污染 capture。
- **`tmux_cleanup_action` 的 `elapsed_s` 语义**：= 子进程命令**已结束**、进入收尾倒计时后经过的秒数（不是 session 总寿命）。`_tmux_collect` 里以「capture 出现成功 / 基础设施失败签名」为「命令跑完」的锚点，之后才开始计 `elapsed`。测试用例 `(True, 5, 15, 10) → let_countdown` / `(True, 26, 15, 10) → force_kill` 与此一致。
- **接入默认关（feature flag `AGATE_DISPATCH_TMUX`，默认不设）**：切除条款 + P2-design §3.10 + P0-brief 「R10 tmux 目标环境代表性」共同要求「不通过则停在『定稿 + 待落地验证』、不阻塞」。默认关使全量 pytest / 回归护栏（BDD-39/40「不配置 = 逐字节现状」）不受影响——裸路径与改动前行为等价。本机 WSL2 + tmux 3.4 已手动冒烟（`new-session -d` 包裹 → `_tmux_collect` 读 capture → 清理干净、`has-session` 非零退出容忍、裸路径不变），结论记 P4-progress。
- **tmux 路径 `exit_code=None`**：`tmux new-session -d` 立即返回，内层命令退出码不经 tmux 透出。返 `None` → `classify_outcome` 的「非零退出兜底」分支（要求 `exit_code is not None`）被跳过，判定纯走结构化信号 + `produced_files`——与 P2-design §3.7「退出码对 Codex 不可靠、必须解析事件流」一致，不引入新判定语义。
- **R1 完整性洞守住**：tmux 包裹只影响「子进程怎么起 + 人能不能 attach」；`classify_outcome` 拿到的 stdout（经 `tee` 的 capture）与裸跑一致；`outcome.kind` 判定 / `try_and_fall` 回落逻辑**逐字节未改**。stderr 透传只到诊断面、不并入判定文本。BDD-37「两路径留痕 + gate 结果逐字节一致」成立。
- **回归硬约束**：`phases.yaml` / `check-gate.py` / `check-state-transition.py` / `state-machine.md` / `check-judge-verdict.py` / `check-p6-provenance.py` / `check-events.py`（第 1-8 条 + 哈希链）/ `check-dispatch-routing.py` / `agate-cmdstream-adapters.py` / `agate-dispatch.py` / `dispatch-tiers.yaml` —— 本批 `git diff` 零改动（只改 `agate_dispatch_route.py` + `dispatch-protocol.md` + 新增 `test_tag0034_p4c.py`）。回归护栏 25 passed。

## P4b-review 3 条 INFORMATIONAL 处理

- **P4b-I1（`_default_subprocess_run` 丢弃 stderr）—— 做**：`proc.stderr` 非空 → `sys.stderr.write` 透传到路由脚本诊断面。选「透传」而非「并入 `_INFRA_SIGNALS` 扫描文本」——后者会改变 `classify_outcome` 的判定输入、破坏「不配置 = 逐字节现状」不变量与 R1（判定输入须与裸跑一致）。测试 `test_default_subprocess_run_forwards_stderr` + `test_default_subprocess_run_stderr_not_merged_into_stdout` 锁死两侧。
- **P4b-I2（`except (FileNotFoundError, OSError)` 冗余）—— 做**：收敛为 `except OSError`（`FileNotFoundError` 是 `OSError` 子类）。测试 `test_default_subprocess_run_filenotfound_is_spawn_oserror` 断言 `FileNotFoundError` 仍归 `spawn_oserror` → `LAUNCH_FAIL`。
- **P4b-I3（`_route_main` 子进程端到端分支无 CI 覆盖）—— 部分做 + 注明残留**：新增 `test_route_bridge_end_to_end_writes_single_dispatch_route_event`——以 `_route_main` **相同的组合**（`functools.partial` 绑定 `dispatch_once` 额外 kwargs + 适配层闭包桥接到 kw-only `write_dispatch_route_event` + 真 `agate_common.append_event` 哈希链账本）跑 `try_and_fall`，mock 子进程候选链（首候选 `INFRA_ERROR` 回落、次候选 `HAS_OUTPUT`），断言一次回落落 **1 条**合法 `dispatch_route` 事件、`candidates_tried` 的 `result`/`reason` 正确、`final` == 成功候选。<br>**残留缺口（注明不做 + 理由）**：完整 `_route_main` **进程级**调用（连字符模块名需 `importlib.util` 加载 + 无 `dispatch-routing.yaml` 时恒走 `form=default` + 需 PATH 上有 fake `claude`/`codex` 可执行）——用 shell 脚本假 CLI 会引入平台敏感依赖（Windows 不跑），与 AGENTS.md「测试不得硬编码单平台假设」冲突；env-DI seam（给 `_route_main` 加注入 `run` 的钩子）改动面超出 P4c 且触及 R1 判定路径。此路径由人工真机复核 + 未来续跑迭代收敛（与 P4b `[DESIGN_GAP]` 一致）。

## [DESIGN_GAP]

[DESIGN_GAP: tmux 包裹待目标环境验证 —— 本机 WSL2 + tmux 3.4 冒烟通过（new-session -d 包裹 / capture 经 tee 落文件 / _tmux_collect 生命周期轮询 + 清理 / has-session 非零退出容忍 / 裸路径逐字节不变），但目标部署环境代表性未定（非容器 / CI runner / 纯物理机，外部评审 W2 / P0-brief R10）。按 P2-design §3.10「不通过则停在『定稿 + 待落地验证』、不阻塞 P8」：`_default_subprocess_run` 的 tmux 包裹接入用 feature flag `AGATE_DISPATCH_TMUX` 默认关，两个 helper 为纯逻辑函数（测试转绿）。目标环境须在其自己 tmux 版本复跑跨平台机制调查落地前复核项后再开启默认。P4c 不通过不影响 P4a/P4b 已 commit 的成果。]

[DESIGN_GAP_REVIEWED: 已确认（主 Agent 2026-09-10）。P2-design §3.10 + P1 §7 + 外部评审 W2 / P0-brief R10 明确 P4c「目标环境代表性存疑则停在『定稿 + 待落地验证』、不阻塞 P8」——implementer 采「两个 helper 纯逻辑（测试转绿）+ `_default_subprocess_run` tmux 包裹接入 feature flag `AGATE_DISPATCH_TMUX` 默认关」正是该条款的落地形态，非切除、非偏离。裸路径逐字节不变（BDD-37「两路径留痕逐字节一致」）+ 本机 WSL2/tmux 3.4 冒烟通过。目标环境开启默认前复跑 research §10 tmux 验证项 —— 登记为 P8 / 未来迭代事项，不阻断 P4c commit。]

## [SCOPE+] / [SCOPE_GAP] / [CLARIFY]

- 无 `[SCOPE+]`：未发现 P1/P2 未覆盖但必须做的新需求。
- 无 `[SCOPE_GAP]`：prompt 与 P2-design §3.10（tmux 观测层全节）+ §4.1 P4c 行 + §10 完成标志 9 逐条对齐。
- 无 `[CLARIFY]`。

## 新增文件核对表

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| `agate/tests/unit/test_tag0034_p4c.py` | 无 P2-skeleton.md / 无 CODE-MAP.md 机制 | `[CODE_MAP_EXEMPT: 项目未采用 CODE-MAP 机制]` |

## 自查记录（非 gate）

- `python3 -m pytest agate/tests/ -k tag0034 -q --tb=short` → **90 passed / 0 failed**（`1537 deselected`）。
  - 转绿：`test_tag0034_tmux.py::test_bdd_37`（`build_subprocess_launch`）+ `test_bdd_38`（`tmux_cleanup_action`）。
  - 新增 `test_tag0034_p4c.py` **12 passed**。
  - P3 既有断言未改且不回归（`test_tag0034_tmux.py` 断言逐字节未动；`test_tag0034_tryfall.py` / `test_tag0034_p4b.py`(18) / `test_tag0034_subprocess.py` 等仍绿）。
- `python3 -m pytest agate/tests/regression/test_tag0034_zero_change.py agate/tests/unit/test_check_events.py agate/tests/unit/test_tag0027_b2_agate_dispatch.py agate/tests/unit/test_tag0027_b2_audit2_dual_anchor.py -q` → **25 passed**（BDD-39 字节基线 + BDD-40「不配置 = 现状」+ check-events 零改动 + agate-dispatch 渲染路径零改动仍绿；回归基线哈希文件不含 `agate_dispatch_route.py` / `dispatch-protocol.md`，本批改动不触 BDD-39）。
- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → exit 0（CHECK 1~15 全 PASS，0 ERROR / 329 WARNING —— 与 P4b 后基线一致，tmux 小段未新增 WARNING、未触 CHECK 14 平台名护栏）。
- `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing` → exit 0（账本 14 行，哈希链完整，ts 单调）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate_dispatch_route.py agate/tests/unit/test_tag0034_p4c.py` → All checks passed。
- 本机 tmux 冒烟（`timeout 30`，WSL2 + tmux 3.4）：`build_subprocess_launch(tmux_available=True)` 生成的 `tmux new-session -d` launch 跑通 → `_tmux_collect` 读到 capture 文件内容 → session 清理后 `has-session` 非零退出（容忍）；裸路径 `build_subprocess_launch(tmux_available=False)` 返回原样 cmd。中文收尾 `echo` 在 pane 无报错。

## SELF-GATE 预告（供主 Agent，不 commit）

本批改 `agate/scripts/agate_dispatch_route.py` + `agate/dispatch-protocol.md` + `agate/tests/**` → 触发 SELF-GATE。commit 前主 Agent 派 `protocol-alignment-review`（A1-A7）+ C8 `review`，commit message 带 `self-gate-review:` trailer。
