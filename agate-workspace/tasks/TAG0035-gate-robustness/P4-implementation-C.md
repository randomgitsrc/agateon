---
phase: P4
task_id: TAG0035
parent: P2-design.md
trace_id: TAG0035-P4-C-20260916
agent: implementer
type: implementation
created: '2026-09-16'
status: draft
implementation_dir: agate/scripts
---
# P4-implementation-C — TAG0035 子批 C（`_gate_p4` 完整度判据过窄，DEBT0037）

## 改动清单

### `agate/scripts/check-gate.py`

1. 新增辅助函数 `_gate_p4_has_prior_code_commit(task_id)`（放在 `gate_p4` 定义之前，
   紧邻 `_STAGED_EXCLUDE_RE` 常量之后）：扫描本任务 P4 阶段历史 commit（commit message
   含 `wf(<task_id>-P4)` 标签，用 `git log --grep --fixed-strings` 定位，标签**带收尾右括号**
   做边界定界，按 P2-review.md 约束3 的实测结论加固，避免无收尾定界符时对
   `wf(TAG0035-P40)` 一类假想 commit message 的误配），逐个 commit 用
   `git diff-tree --no-commit-id --name-only -r` 取文件列表，命中任一非
   `_STAGED_EXCLUDE_RE`（非 P[0-8]-*.md / 非 .state.yaml）的文件即返回 `True`；
   `task_id` 为空或历史无匹配 commit 或均为纯文档 diff 返回 `False`。

2. `gate_p4()` 调用处（原 `has_code_file` 判定之后的 `if not has_code_file: return 1`）
   改为：`has_code_file` 为假时先取 `task_id = _load_state_yaml(task_dir).get("task_id", "")`，
   调用 `_gate_p4_has_prior_code_commit(task_id)`——为真则放行（继续走后续 RM-AG0046
   维护性反模式判据），为假才 `return 1`。`_load_state_yaml` 复用 `gate_p8`
   （约第 1374 行）已有的同一写法，无兼容性问题。

3. 红灯边界（BDD-10）：纯文档、本任务从未有过 `wf(<task_id>-P4)` 代码 commit、非回退
   场景，`_gate_p4_has_prior_code_commit` 必然返回 `False`——不需要额外排除逻辑，
   是函数设计的自然结果。

关联：BDD-8（一个 P4 阶段跨多 commit 交付，较早 commit 已含代码 diff，当前暂存区
仅 md 不应误判）、BDD-9（P5→P4 回退后修复 commit，暂存区仅 md/yaml，历史已有代码
commit 时不应误判）、BDD-10（纯文档、无代码历史、非回退场景仍应 `return 1`，放宽
不削弱拦截力）。

## 自测结果

```
timeout 60 python3 -m pytest agate/tests/unit/test_check_gate.py -q \
  -k "tag0035_bdd_8 or tag0035_bdd_9 or tag0035_bdd_10"
→ 3 passed

timeout 90 python3 -m pytest agate/tests/unit/test_check_gate.py -q
→ 210 passed（含子批 A/B 已落地的 tag0035_bdd_1~7、既有 G4 系列旧用例，
  均无回归；子批 C 目标 BDD-8/9/10 全部转绿）
```

以上为自查结果，不代表 P5 gate 已过。

## 改动范围核对（`git diff --stat`）

```
agate/scripts/check-gate.py | 34 ++++++++++++++++++++++++++++++++--
1 file changed, 32 insertions(+), 2 deletions(-)
```

改动只涉及新增 `_gate_p4_has_prior_code_commit` 函数 + `gate_p4` 调用处的
`if not has_code_file:` 分支修改，未触碰子批 A（`main()` 内回退判空分支 / 未知阶段
`sys.exit(1)`）与子批 B（`check-state-transition.py` / `pre-commit-gate.py`）已落地的改动。

## ruff 修复（子批 D 自测发现）

子批 D 自测发现 `_gate_p4_has_prior_code_commit` 循环体内 `commit_hash = commit_hash.strip()`
触发 ruff PLW2901（循环变量被同名赋值覆盖），导致
`test_bdd_34_shellcheck_three_hook_shells_and_ruff`（`test_env_adapt_docs.py`）失败。
纯机械改名修复：循环变量改为 `raw_hash`，`commit_hash = raw_hash.strip()`，不改逻辑。

```
timeout 30 ~/.venvs/agate-dev/bin/ruff check agate/scripts/check-gate.py
→ All checks passed!

timeout 90 python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_env_adapt_docs.py -q -k "tag0035 or bdd_34"
→ 19 passed, 202 deselected
```
