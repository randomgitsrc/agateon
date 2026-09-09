[NO_NEED_CONFIRM]
[PROD_NOT_TOUCHED]

# P5 技术验证结果 — TAG0034 派发路由

独立 verifier subagent（模式一）重新执行，未照抄 P4 自报数字。逐 key 独立执行（未用 `&&` 拼接）。
基线提交 `92edcfc`（HEAD，P4a `d1c2aca` / P4b `99a4c19` / P4c `92edcfc` 三批代码均已落地）。
工作目录：worktree `.worktrees/agate-TAG0034`（分支 `feat/TAG0034-dispatch-routing`）。
检查对象类脚本（consistency / events / dispatch-routing）均用 worktree 自己的 `agate/scripts/`。

## 汇总表（4 条 gate_command 逐条独立实跑）

| key | 命令 | exit code | 判定 |
|-----|------|-----------|------|
| P5 | `python3 -m pytest agate/tests/ -q --tb=no`（外层 `timeout 600`） | **0** | 通过（1625 passed / 0 failed / 2 skipped） |
| P5_consistency | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（外层 `timeout 180`） | **0** | 通过（0 ERROR / 329 WARNING） |
| P5_events | `python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing`（外层 `timeout 90`） | **0** | 通过（15 行，哈希链完整，ts 单调） |
| P5_routing_schema | `python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml`（外层 `timeout 90`） | **0** | 通过（schema 校验通过） |

结论：4/4 gate_command exit 0；全量 pytest failed=0。无预存失败，无本次引入失败，无 flaky。
与派发指引「基线预期 1625 passed / 0 failed / 2 skipped」逐字一致。

passed=1625 failed=0 skipped=2 (gate P5_pytest, exit 0)

未运行全量测试：否（已运行全量 `agate/tests/` 套件，含非本任务测试）。
预存失败：无（不需要创建 known-failures.md）。

---

## 1. P5 — 全量 pytest

- 命令：`python3 -m pytest agate/tests/ -q --tb=no`（外层 `timeout 600`）
- 全量口径（非仅本任务用例，含 unit + regression + integration + 非 TAG0034 测试）
- exit code：**0**
- 关键输出（原始尾行，已去 ANSI）：

```
1625 passed, 2 skipped in 164.22s (0:02:44)
```

计数：
passed=1625 failed=0 skipped=2

- `grep -acE '^FAILED ' pytest.raw.log` 命中数：0
- fail-list.txt：空文件（无失败，仍已创建）
- 原始输出落盘：`P5-test-results/pytest.raw.log`（末行 `EXIT_CODE: 0`）
- BDD-39/40 回归护栏（`test_tag0034_zero_change.py`）、TAG0034 新增测试族（schema/resolve/tryfall/events/native/subprocess/tmux/interaction/docs/p4b/p4c）均在全量套件内计入 passed。

## 2. P5_consistency — 协议一致性（worktree 自己的脚本）

- 命令：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（外层 `timeout 180`）
- exit code：**0**
- 结果尾行（原样）：`仅有 329 个 WARNING，无 ERROR。`
- 329 WARNING 均为存量叙事文件（docs/reviews、docs/design-notes、CHANGELOG 等）死链引用；`--strict-errors-only` 只按 ERROR 判失败 → 不阻断。与派发指引基线（~329 WARNING / 0 ERROR）一致。
- 落盘：`P5-test-results/consistency.log`（末行 `EXIT_CODE: 0`）

## 3. P5_events — dispatch_route 事件账本审计

- 命令：`python3 agate/scripts/check-events.py agate-workspace/tasks/TAG0034-dispatch-routing`（外层 `timeout 90`）
- exit code：**0**
- 输出（原样）：`GATE EVENTS: 账本审计通过（15 行，哈希链完整，ts 单调，judge 轮次×0）`
- 15 行含主 Agent 手动 `_advance` 的 P4→P5 state_transition；`dispatch_route` 理由码枚举校验路径未被判非法。
- 落盘：`P5-test-results/events.log`（末行 `EXIT_CODE: 0`）

## 4. P5_routing_schema — routing schema 静态校验器

- 命令：`python3 agate/scripts/check-dispatch-routing.py agate-workspace/dispatch-routing.yaml`（外层 `timeout 90`）
- exit code：**0**
- 输出（原样）：`check-dispatch-routing: schema 校验通过: agate-workspace/dispatch-routing.yaml`
- 本任务提交的 `dispatch-routing.yaml` scaffold 通过 presence 级冒烟校验。
- 落盘：`P5-test-results/routing-schema.log`（末行 `EXIT_CODE: 0`）

---

## 环境隔离声明

- [PROD_NOT_TOUCHED]：全程仅在 worktree `.worktrees/agate-TAG0034` 内读 + 运行脚本；临时输出写 `/tmp`；产出写 `P5-test-results/`。未触碰主 checkout `/home/kity/oclab/agateon` 与 `~/.agate` 稳定版。
- [NO_NEED_CONFIRM]：P5 验证不涉及数据删除 / 迁移等不可逆操作。
- 只跑不改：未改任何代码 / 测试 / 配置 / 协议文档。

## 签名校验（N5 缓解）

产出本 unit.md 后自跑：
`grep -cE '^(PASSED|FAILED|passed|failed|ok|not ok)' agate-workspace/tasks/TAG0034-dispatch-routing/P5-test-results/unit.md`

签名匹配计数：2（> 0 视为有效产出）

匹配行来源：本文件「## 1」节的 `passed=1625 failed=0 skipped=2` 汇总行等以 `passed`/`failed` 开头的行。

EXIT_CODE: 0
