---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "修复合并后 main CI 红：agate-ci-verify.py 的 _resolve_protocol 增 base 入参，协议根改由回放基准 base 推导（协议仓库中 merge-base(base, HEAD) 处 agate/），回退路径显式 note；测试夹具改为当前协议良构非 legacy"
files_changed:
  - agate/scripts/agate-ci-verify.py
  - agate/scripts/README.md
  - agate/tests/integration/test_tag0050_ci_replay.py
  - agate/tests/unit/test_agate_ci_verify.py
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/tasks/TAG0050-task-data-contract/retrospective.md
  - agate-workspace/tasks/TAG0050-task-data-contract/P4-progress.md
---

# 协议-脚本对齐审查（TAG0050 P8 CI-fix3：push-to-main 协议根选择真缺陷）

> 审查对象：PR #408 合并、v0.80.0 tag/Release 已发布后，**main push run 红**的真缺陷修复（未提交，分支 `fix/TAG0050-ci-replay-protocol-root`）。
> 触发面：`agate/scripts/agate-ci-verify.py`（SELF-GATE）。
> 方法：仓外全量副本（含 `.git`）独立复跑；**端到端真脚本复现 push-to-main**（HEAD == origin/main）+ 改前红/改后绿双向证据；变异测试。
> 环境隔离：`[PROD_NOT_TOUCHED]` —— 只在仓外一次性副本 `/tmp/opencode/tag0050-fix3-review` 上做变异/复跑，**未对真实仓库执行任何写仓命令，未编辑被评审文件**（跑前/跑后 `git status --porcelain` 均为原始 7 改 + 3 未跟踪）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（附 1 条 docstring 措辞小瑕，见下，不阻断） |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED（附 CHANGELOG [Unreleased] 空注记，不阻断） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**无 MISALIGNED / 无 NEEDS_HUMAN_REVIEW。** 可 commit。

## dispatch 范围 6 条逐条对照

| 范围 | 问题 | 结论 |
|------|------|------|
| 1 | 协议根推导正确性（四路径 + 回退 note + 两分支用 base + 不破坏单调/等级检查） | 全部独立验证通过 —— ALIGNED |
| 2 | 测试夹具良构性（当前协议良构、不再依赖 checkout 协议版本） | 良构、`test_bdd_23/24` 稳定 PASS —— ALIGNED |
| 3 | 新回归用例真实性（改前红 + 断言有效） | 变异测试 + 端到端双向验证 —— ALIGNED |
| 4 | 缺口登记（DEBT0059 编号/内容、check-debt 0 错、retrospective 一致） | 已登记、0 错、一致 —— ALIGNED |
| 5 | 文档反向传播（README 行同步） | 已同步 —— ALIGNED |
| 6 | SELF-GATE 清单（consistency 0 ERROR；全量 pytest 除环境漂移 1 条外 0 failed） | 通过 —— ALIGNED |

## 逐项审查

### A1: 文档→脚本对齐 —— ALIGNED

**变更意图**：`agate-ci-verify.py` 选协议根的函数 `_resolve_protocol` 输入面缺回放基准 `base`——主流程已算出 `base`（PR = merge-base；push = `before`）却未传入，函数自行用 `merge-base HEAD origin/<默认分支>`。push 到默认分支时 HEAD 就是 origin/main ⇒ merge-base = HEAD 自己 ⇒ 用刚合并的新协议回放历史提交。

**设计意图支持**（`docs/design-notes/design-tag0050-task-data-contract.md:186`）：
> GitHub push | …在 push 口径下，第 3、4 点所说的"merge-base"指 `merge-base(before, HEAD)`

即设计文档**早已明确** push 口径的"merge-base"应为 `merge-base(before, HEAD)`；修复正是实现该语义（旧实现按 `merge-base HEAD origin/main` 解读，属实现与设计语义偏离）。

**脚本实现**（`agate/scripts/agate-ci-verify.py:183-212`）：
- 签名 `_resolve_protocol(repo, agate_root_env, base)`（:183）；调用点传主流程 `base`（:538）。
- AGATE_ROOT 分支：`rev = _merge_base(proto_repo, base, "HEAD") if base else ""`（:198）——**用了 base**。
- 仓库本体分支：`rev = (_merge_base(repo, base, "HEAD") if base else "") or "HEAD"`（:206）——**用了 base**。
- 回退：AGATE_ROOT 分支 `return agate_root_env, None, _fallback_note(base)`（:204）；仓库本体分支 `rev="HEAD"` 时 `note=_fallback_note(base)`（:209-210）。`_fallback_note`（:177-180）产非空 note。
- 模块 docstring（:18-27）与函数 docstring（:184-194）同步。

**结论**：ALIGNED。
**docstring 措辞小瑕（不阻断）**：函数 docstring（:189-190）与模块 docstring（:26-27）称"**或 worktree 建立失败 → 回退当前 HEAD 的 `agate/` 并在 note 中写明回退原因**"，但代码中**只有 AGATE_ROOT 分支**在 worktree 失败时回退（:200-204）；**仓库本体分支** `_make_protocol_worktree` 失败时返回 `None`（:208-212）→ main 走 `_fail`（:539-540），并不回退。二者皆非静默（FAIL 是响亮失败），故核心要求"不得静默"成立；建议把 docstring 收窄为"worktree 失败 → AGATE_ROOT 分支回退 / 仓库本体分支 fail-closed"，或给仓库本体分支补同款回退以对齐 docstring。

### A2: 脚本→文档对齐 —— ALIGNED

`agate/scripts/README.md:108` 的 `agate-ci-verify.py` 行已同步：
> 协议版本：仓库含协议本体（agateon-like）或 `AGATE_ROOT` 提供协议 → **回放基准 `base`** 处（协议仓库中 `merge-base(base, HEAD)`）的 `agate/`（push-to-main 时 = `before`；`base` 不在协议仓库则回退当前 HEAD 协议并在 note 写明原因）

与实现（:196-211）逐字对齐：两分支均用 `base`、回退分支有 note、push-to-main = `before`。同行的 `--base` / `--push --base` / `before` 全零回退描述（:108 前半）未变，仍准确（:477-488）。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播 —— ALIGNED

**主动推断"应被影响但 diff 未列出的文件"**，逐一验证：

| 候选文件 | 是否需改 | 判据 |
|----------|----------|------|
| `agate/scripts/README.md` | 需改，已改 | 见 A2 |
| `agate/UPGRADING.md:304-305`（"协议根取…merge-base 处 `agate/`"） | **不需改** | 该措辞用的是**设计同术语**（design-note:186 "push 口径 merge-base 指 merge-base(before,HEAD)"）；修复后语义 = `merge-base(base, HEAD)`，与该表述一致。且该节属已发布 v0.80.0 的历史发布注（`UPGRADING.md:277`「历史版本节…仅作历史记录」），非本次应改写对象 |
| `agate/platform-notes.md:344`（"无参数…按 `merge-base HEAD origin/<默认分支>` 逐提交回放"） | **不需改** | 描述的是**无参本地口径的回放范围**（`main():485-488` 未变），非协议根；仍准确 |
| `agate/WORKFLOW.md:370` / `state-machine.md:154` / `tests/README.md:67` | 不需改 | 只述"逐提交回放 + `SKIP:`"，不述协议根选择 |
| `check-protocol-consistency.py`（CHECK 9 锚点） | 不需改 | 见 A6 |

**retrospective.md 一致性**：frontmatter `mechanism_issues` 9 条 ↔ 正文"机制缺口"9 条；`execution_issues` 6 条 ↔ 正文"执行错误"6 条（含本批新增各 1 条）——**计数一致**（上一轮 P8-ci-fix 曾因计数不一致判 A3 MISALIGNED，本轮已不复现）。技术债表列 `DEBT0051..DEBT0059`（9 条）与实际条目一致（见 A4 命令）。

**结论**：ALIGNED。

### A4: 测试覆盖 —— ALIGNED

**最近一次全量实跑**（仓外副本，`AGATE_ROOT=<副本>/agate python3 -m pytest agate/tests/ -n auto -q`）：
```
1 failed, 2865 passed, 3 skipped in 81.09s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
该 1 failed 为**既有环境漂移**（`opencode debug agent` 子命令已改名 `agents`，见断言 `Unknown subcommand "agent" for "opencode debug"`），与本次改动无关（不碰 setup/opencode）。与 dispatch「除既有环境漂移 1 条外 0 failed」一致。总用例 2869 = `count-tests.sh` 口径。

**新增用例与覆盖**：
- `test_push_to_main_protocol_root_uses_base_not_head`（unit）：合成仓库令 `origin/main == HEAD`（真 push-to-main），断言协议根取 **base 处旧协议**（读实际文件内容）+ note 含 `base[:8]`——**语义断言，非纯文本匹配**。
- `test_resolve_protocol_falls_back_when_base_absent`（unit）：base 为仓外 SHA → 断言回退**当前 HEAD 协议** + note 含基准。
- `_task_commit_repo` 默认改为**当前协议良构非 legacy**（账本首行 `task_created`、`write_ledger` 哈希链、去系统字段 `status`、`contract_level: 1`），`legacy=True` 保留 legacy 语义供 BDD-26b。

**改前红（变异测试，独立复跑）**：把 `_resolve_protocol` 仓库本体分支 `rev` 还原为旧逻辑 `_merge_base(repo) or "HEAD"`（保留 3 参签名）后：
```
FAILED test_push_to_main_protocol_root_uses_base_not_head
E   AssertionError: …实际取到 '# NEW protocol\n'
```
还原后 PASS——**负向控制成立**。

**结论**：ALIGNED。**次要覆盖观察（不阻断）**：四路径中"push-new-branch（before 全零）"的协议根未新增直接用例，但其归约为 `merge-base(HEAD, origin/default)`（`main():478` 未变，等价于 PR/本地路径），非本次回归面。

### A5: 下游影响 + 文档传播 —— ALIGNED

- **是否有破坏性变更**：无。修复只改变**已合并到默认分支的 push 回放**协议根选择（PR/本地/新建分支三路径结果不变：`base` 为 HEAD 祖先 ⇒ `merge-base(base, HEAD) = base`）。
- **下游项目影响**：使用者项目若 `AGATE_ROOT` 指向**外部安装**（base 为其仓外 SHA）→ 新代码回退 `AGATE_ROOT` 本身（旧代码在版本目录场景亦回退 `AGATE_ROOT`，行为等价；仅 `~/.agate/repo` 这类真 git 仓场景由"其仓 merge-base"改为"AGATE_ROOT 当前协议"——两者皆为 AGATE_ROOT 提供者，无破坏性）。
- **CHANGELOG**：`[Unreleased]` 为空。本次为 v0.80.0 发布后的 hotfix，按既有约定（上一轮 P8-ci-fix 同类修复亦未改 CHANGELOG，A5 判 ALIGNED）在下一版本发布时归并。**注记（不阻断）**：若维护者希望 hotfix 立即留痕，可在 `[Unreleased]` 补一行。
- **README/脚本 docstring**：已同步（见 A2/A1）。

**结论**：ALIGNED。

### A6: 锚点表覆盖 —— ALIGNED

`check-protocol-consistency.py` 对 `agate-ci-verify` 的唯一引用是 :951 的**退役名保留注释**（`ci-gate-backstop.py` → `agate-ci-verify.py`），非规则锚点。本次改动是**既有函数内部语义修正**（协议根推导），未引入新协议规则/字段，CHECK 9 锚点表无需更新。

**结论**：ALIGNED。

### A7: 设计原则一致性 —— ALIGNED

逐条查 `agate/adr.md` 中与"协议根/版本解析"相关的 ADR：**ADR-009**（`_protocol_root` 两形态探测序）针对的是**安装期版本目录探测**（`agate_common._resolve_version_info` / `resolve-entry.py`），与 `agate-ci-verify.py` 运行期回放协议根选择是**不同机制**，不涉及。

本次改动是**设计 §2.4 既有语义的落地修正**（design-note:186 已写明 push 口径 merge-base = `merge-base(before, HEAD)`），**未引入新的架构决策**，无需新增 ADR。

**结论**：ALIGNED。

### A8: 声称-命令绑定 —— ALIGNED

逐条 `声称 → 命令 → 结论`：

| 声称（出处） | 产出命令 | 结论 |
|--------------|----------|------|
| `26 passed`（P4-progress:688 自查） | 副本 `pytest .../test_agate_ci_replay.py .../test_agate_ci_verify.py` → 18 + 8 | ✅ 26，一致 |
| `check-protocol-consistency.py → 0 ERROR / 410 WARNING`（P4-progress:689） | 副本跑（去本次 review 产物） | ✅ 0 ERROR；410 WARNING 复现（带本次 review 产物时为 412，噪声来自 frozen 扫描面 `docs/`、`tasks/`） |
| `count-tests.sh → 2869`（P4-progress:691） | 副本 `bash agate/tests/scripts/count-tests.sh` | ✅ 2869 |
| `ruff check → All checks passed`（P4-progress:692） | 副本 `~/.venvs/agate-dev/bin/ruff check`（3 文件） | ✅ All checks passed |
| `仓外副本 OLD rc=1（7 FAIL）→ NEW rc=0`（P4-progress:677-685） | 副本真脚本 `--push --base 720c97d3`（HEAD==origin/main） | ✅ 独立复现：NEW note=`回放基准 720c97d3 的 agate/` rc=0；OLD(HEAD committed) 7 FAIL rc=1 |
| DEBT0051..0059（9 条，retrospective:222） | `grep '^id: DEBT005' tech-debt.md` | ✅ DEBT0050..0059 齐，本次新增 DEBT0059 |

**结论**：ALIGNED。

## 范围 1 独立证据（核心）：四路径协议根

`_resolve_protocol` 在 `base` 为 HEAD 祖先时返回 `base` 处协议（两分支均如此）。四路径的 `base` 由 `main()` 计算（:475-488，未变），逐一：

| 路径 | `base` 计算 | `merge-base(base, HEAD)` | 协议根 | 判定 |
|------|-------------|--------------------------|--------|------|
| PR（`--base PR_BASE`） | `merge-base(PR_BASE, HEAD)` | = base（分支点） | 分支点（旧）协议 | ✅ |
| push-to-main（`--push --base before`） | `before`（旧 main 尖） | = before（HEAD 祖先） | **before（旧）协议** | ✅ 修复点 |
| push-new-branch（before 全零） | `merge-base(HEAD, origin/default)` | = base（分支点） | 分支点协议 | ✅ |
| 本地缺省（无参） | `merge-base(HEAD, origin/default)` | = base | 分支点协议 | ✅ |

**端到端真脚本复现（push-to-main，副本 HEAD == origin/main == `ef843019`）**：
```
$ env -u AGATE_ROOT python3 agate/scripts/agate-ci-verify.py --push --base 720c97d3...
回放: 23 个非合并提交（协议：回放基准 720c97d3 的 agate/）
回放完成：23 个提交，失败 0 个，耗时 16.42s
NEW_E2E_RC=0
```
同一命令换回 HEAD 已提交的**旧脚本** → `失败 7 个` `OLD_E2E_RC=1`（与 CI run 37851356052 的 7 提交 FAIL 一致）。

**不破坏既有检查**：`_ci_ledger_checks` / `_ci_level_checks` / 单调不降版本检查（`main():498-519`）均沿用**同一** `base` 变量，本次 diff **未触碰**（改前改后同为 base），无连带破坏。

## 人工验收清单

- [x] Write 前已检查目标路径不存在同名文件（`ls` 确认 `agate-alignment-review-2026-10-09-TAG0050-P8-ci-fix3.md` 不存在；同名 `-ci-fix.md` 属上一批，未覆盖）
- [x] 审查报告含 A1-A8 八项，每项有结论
- [x] MISALIGNED 项：无
- [x] NEEDS_HUMAN_REVIEW 项：无
- [x] 审查报告落盘到 `docs/reviews/agate-alignment-review-{date}-{task_id}.md`
- [x] 只读纪律：仅在仓外副本 `/tmp/opencode/tag0050-fix3-review` 做变异/复跑；跑后原仓 `git status` 未变
