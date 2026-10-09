---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 按 r1 澄清重做——`agate-ci-verify` push 口径 `before` **不可解析**时回退 `merge-base(HEAD, origin/<默认>)`（RM-AG0112）
files_changed: [agate/scripts/agate-ci-verify.py, agate/tests/unit/test_agate_ci_verify.py, agate/scripts/README.md, CHANGELOG.md, agate-workspace/roadmap/roadmap.md]
---

# 协议-脚本对齐审查 r2（批 B/H2 · CI force-push）

**审查对象**：`hotfix/batch-b-hygiene` 分支上**未提交**的工作区改动（`ac93f22c` 之后，r1 后的第二版）。
**审查范围**：`git diff` 全部 5 文件（本轮新增 `agate/scripts/README.md`）+ r1 报告 + 权威源（`WORKFLOW.md`、workflow）。
**先读**：`docs/reviews/agate-alignment-review-2026-10-09-H2B-CI-FORCEPUSH.md`（r1）。

---

## 一句话总评 + 是否可 commit

**r1 的决定性发现已被正确吸收**：本轮把失败源从"非祖先"改为"**不可解析（对象缺失）**"，并在该情形回退 `merge-base(HEAD, origin/<默认分支>)`。**在 r1 的同构场景（CI clone 中 `before` 对象缺失）实测已不再 FAIL**（`rc=0` + 显式 NOTE），且**真缺陷仍被拦**（实测 `rc=1`）。同步面（README / CHANGELOG / roadmap）已跟上且与实现一致。

⇒ **结论：可 commit。** 附 **3 条非阻断跟进**（见文末）。

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED（模块 docstring L10 残留，minor） |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（2 处 r1 已标"待登记"的 out-of-diff 项仍未登记，不阻断） |
| A4 | 测试覆盖 | ALIGNED（核心路径已覆盖且判别力成立；FAIL 分支缺 pytest，minor） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（逐条命令见下） |

---

## r1 发现逐条核实

| r1 发现 | 本轮处置 | 核实结论 |
|---------|----------|----------|
| **A1 决定性**：`rev-list A..B` 不要求 A 是祖先；真因是 `before` **对象缺失/不可解析** | 代码注释 L486-488 明写该澄清；`roadmap.md:111` / `CHANGELOG.md:37-41` 因果由"非祖先"改为"**不可解析**" | **✓ 已接受并据此重做** |
| **A1 建议**：不可解析时回退 `merge-base(HEAD, origin/<默认>)` + NOTE | `agate-ci-verify.py:492-504` 实现（`rev-parse --verify {base}^{commit}` 空 → `_merge_base(repo,"HEAD")` → NOTE → `base=_mb`；解析不出 → `_fail`）| **✓ 已实现**；ci-sim 实测 `rc=0` |
| **A2**：`agate/scripts/README.md:108` 未同步 push 口径回退 | README:108 补「**`before` 不可解析**……回退 `merge-base HEAD origin/<默认分支>` 并显式 NOTE——RM-AG0112」| **✓ 已修**（模块 docstring L10 仍残留，见 A2） |
| **A4**：缺"不可解析"用例；r1 用例复现的是非缺陷路径 | 删 r1 用例，新增 2 条：`..._unresolvable_falls_back`（不可解析 + origin/main）、`..._non_ancestor_keeps_diff_semantics` | **✓ 已补**；旧码下 **2 failed/10 passed**（判别力成立）。**FAIL 分支仍无 pytest**（minor） |
| **A5/A8**：因果表述错误 + 验收锚被证伪 | `roadmap.md:111`、`CHANGELOG.md:37-41` 已更正；验收锚"rebase/强推后不再假红"现由 ci-sim 实测支持 | **✓ 已修** |
| **A3b**：workflow `detect-docs-only` 同假设 / workflow 注释 L19-22 required 过期 | 未处理（r1 已标"建议登记、不阻断"）| **未登记**（不阻断） |

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`roadmap.md:111`）：
> **修**：`before` 不可解析时回退 `merge-base(HEAD, origin/<默认分支>)`（与 PR 口径同源 = 分支点）并**显式** NOTE（不静默）；merge-base 也解析不出才 FAIL。⚠️ `rev-list A..B` **不要求** A 是 B 的祖先……失败源是**不可解析**，非「非祖先」

**脚本实现**（`agate-ci-verify.py:492-513`）：
> ```python
> if not _git_out(["rev-parse", "--verify", f"{base}^{{commit}}"], repo):   # 不可解析
>     _mb = _merge_base(repo, "HEAD")          # = merge-base(HEAD, origin/<默认分支>)
>     if not _mb:
>         return _fail("... 不可解析 ... 且无法解析 merge-base HEAD origin/... ")
>     print("NOTE: push 的 before ... 在本地**不可解析** ... 回退 merge-base(HEAD, origin/<默认分支>) = ...")
>     base = _mb
> else:                                        # 可解析非祖先：不回退，仅诊断 NOTE
>     _rc_anc, _, _ = _git(["merge-base", "--is-ancestor", base, head], repo)
>     if _rc_anc != 0:
>         print("NOTE: push 的 before ... 不是 HEAD 的祖先（历史改写）——按差集语义回放")
> ```

**结论**：ALIGNED。文档的因果、回退目标、NOTE 口径与实现**逐字一致**；`merge-base(HEAD, origin/<默认分支>)` 与 PR 口径（`merge-base(base, HEAD)`，base=默认分支 tip）**同源**。

### A2: 脚本→文档对齐

| 位置 | 现状 | 是否同步 |
|------|------|----------|
| `agate/scripts/README.md:108` | 已补「`before` 不可解析（对象缺失…）时回退 `merge-base HEAD origin/<默认分支>` 并显式 NOTE——RM-AG0112」| **✓** |
| `CHANGELOG.md:37-41` | 因果改为"不可解析"，回退目标与 NOTE 与实现一致 | **✓** |
| `agate-ci-verify.py:10`（模块 docstring）| 仍写「GitHub push（`--push --base <sha>`）：`rev-list --no-merges <before>..HEAD`」，未提回退 | **残留（minor）** |

**结论**：ALIGNED。README（工具清单，权威）已同步；docstring L10 仅描述常规口径、未提例外——非错误，但建议补一句（见跟进 2）。

### A3: 一致性连锁 + 反向传播

**A3a**：无新增脚本名 / frontmatter 字段 / CHECK 规则 → 无连锁面。

**A3b**：

| 文件 | 应否受影响 | 现状 |
|------|-----------|------|
| `agate/scripts/README.md` | 应（脚本行为 → README）| **✓ 已同步** |
| `AGENTS.md` 0b（本地彩排）| 否：push 口径用 `--base "$(git rev-parse origin/main)"`（可解析），不触发回退 | OK |
| `agate/WORKFLOW.md:370` | 高层次，未要求回退细节 | 可接受 |
| `RM-AG0103` | 主题相邻，可选交叉引用 | 未改（可接受）|
| workflow `detect-docs-only`（L82-95）同假设 | 同类隐患（`before` 缺失 → `docs_only=false`，fail-closed 不假红）| **未登记**（r1 已标，不阻断）|
| workflow 注释 L19-22（称 gate-backstop 已移出 required）| 与实况不符（protection 含 gate-backstop）| **未登记**（不阻断）|

**结论**：ALIGNED（本 diff 面已闭合；2 处 out-of-diff 项仍待登记，非本轮阻断项）。

### A4: 测试覆盖

**实跑输出**（跑前后 `git status` 一致，仅多 r2 的 progress 留痕文件）：

```
# 本批被改测试文件（新码）
$ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py -n auto -q
12 passed in 1.09s

# 相关集成（无回归）
$ python3 -m pytest agate/tests/integration/test_tag0050_ci_replay.py -n auto -q
18 passed in 3.18s

# 全量
$ python3 -m pytest agate/tests/ -n auto -q
1 failed, 2897 passed, 2 skipped in 85.61s (0:01:25)
# 唯一 failed = test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
#   = 本地 opencode CLI `debug agent` 子命令漂移（Unknown subcommand "agent"），与本次 diff 无关

# 判别力 scratch（新用例 vs 旧代码；一次性 clone /tmp/opencode/ci-sim 内脚本为已提交旧版）
$ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py -n auto -q
2 failed, 10 passed      # 两条新用例均转红 → 判别力成立
```

**判别力细节**：
- `test_rm_ag0112_push_before_unresolvable_falls_back`（`test…py:356`）：旧码 `base="f"*40` → `rev-list` 失败 → `FAIL` `rc=1` → 第一断言转红。**✓ 真复现了"对象缺失"缺陷。**
- `test_rm_ag0112_push_before_non_ancestor_keeps_diff_semantics`（`test…py:392`）：旧码 `stale` 对象存在 → `rev-list` 成功 `rc=0`、无 NOTE → 第二断言转红。**✓**

**缺口（minor，非阻断）**：「`before` 不可解析 **且** `merge-base(HEAD, origin/<默认>)` 也解析不出 → `FAIL`」分支（`agate-ci-verify.py:493-499`）**无 pytest 覆盖**（两条新用例均设了 `origin/main`）。手动验证可用：无 origin 的仓库 + `--push --base ffff…` → `FAIL: … 不可解析 … 且无法解析 merge-base HEAD origin/main——无法确定回放范围`，`rc=1`（信息清晰）。

**结论**：ALIGNED（核心缺陷路径已覆盖、判别力成立；FAIL 分支建议补测）。

### A5: 下游影响 + 文档传播

- CHANGELOG [Unreleased] 条目已更正（`CHANGELOG.md:37-41`）：因果=不可解析、回退目标、NOTE、FAIL 条件——**✓**。
- 无破坏性变更 → UPGRADING 无需新增章节 **✓**。
- README 已传播 **✓**；roadmap 已更正 **✓**。
- **下游 gate 行为（无回归）**：
  - 新建分支（全零）：更早分支处理（`agate-ci-verify.py:478-479`）→ 回退值恒为祖先 → 不受影响（集成 `test_push_all_zero_before_does_not_fail` 通过）**✓**。
  - 常规 push（`before` 可解析且祖先）：`--is-ancestor`=0 → 无 NOTE，原路径 **✓**。
  - `before` 可解析非祖先：**保留差集语义、不回退**，仅加 NOTE（原行为不变）**✓**。

**结论**：ALIGNED。

### A6: 锚点表覆盖

无新增协议规则 / 脚本名 / 字段 / CHECK 规则；CHECK 9 锚点表无 `agate-ci-verify` 专属锚点。**无需更新**。

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-002（可判定性）**：修复方向符合（对"提交本身没问题"不误判）。
- **ADR-014（判据单源）**：判据仍单源；本轮 README 复述已跟上 → 符合。
- **ADR-015（实质/非实质）**：假红阻断合并（实质），修它方向正确；回退仅影响"回放起点"，不改门禁强度。
- 未发现未记录的架构决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| # | 声称（出处）| 命令 | 结论 |
|---|-------------|------|------|
| 1 | 「`before` 不可解析时回退 `merge-base(HEAD, origin/<默认分支>)` + NOTE；merge-base 也解析不出才 FAIL」（`roadmap.md:111`/`CHANGELOG.md:37-41`）| 读 `agate-ci-verify.py:492-504` | ✓ 与实现一致 |
| 2 | 「**rebase / 强推后不再假红**」（`roadmap.md:111` 验收锚）| ci-sim（fresh clone 无 `7c419e93`）`python3 agate-ci-verify.py --push --base 7c419e93…f94` | ✓ `rc=0` + NOTE + SKIP |
| 3 | 「**真缺陷仍拦**」（`roadmap.md:111`）| defect-sim（不可解析 before + origin/main + gate 失败提交）同上命令 | ✓ `rc=1`（回放该提交 FAIL）|
| 4 | 「回归用例 `test_rm_ag0112_push_before_unresolvable_falls_back` + `..._non_ancestor_keeps_diff_semantics`」（`roadmap.md:111`）| `grep`/`pytest` | ✓ 两用例存在；旧码下均转红 |
| 5 | 「12 passed」（本批自述）| `pytest agate/tests/unit/test_agate_ci_verify.py -n auto -q` | ✓ `12 passed` |
| 6 | 「0 ERROR」（本批自述）| `python3 agate/scripts/check-protocol-consistency.py` | ✓ `0 ERROR`（419 WARNING，冻结文件）|

**结论**：ALIGNED（本轮无"无法给命令"的声称）。

---

## 重点验证（对应派发单 5 项）

1. **是否真修了 r1 缺陷**：**是**。ci-sim（与 r1 同一同构场景：fresh clone、`before` 对象缺失、HEAD=`ac93f22c`）实测：
   ```
   NOTE: push 的 before 7c419e93 在本地**不可解析**（对象缺失…RM-AG0112）⇒ 回放范围回退 merge-base(HEAD, origin/main) = e81fa081
   SKIP: 回放范围 e81fa081..ac93f22c 未改动任务目录（1 个提交）
   rc=0
   ```
   `origin/HEAD` → `origin/main` 与 **unset（回退 `origin/main`）** 两种情形均 `rc=0`。r1 的 CI 日志确认 `origin/HEAD` **未设置**（无 `set-head`）→ `_default_branch` 回退 `origin/main`（存在）→ 正确。NOTE **非静默**（stdout）。
2. **回归用例判别力**：**成立**（旧码下 **2 failed/10 passed**，见 A4）。**FAIL 分支未被 pytest 覆盖**——已指出（A4，手动 `rc=1` 已验证）。
3. **是否引入新问题**：
   - 新建分支路径**不受影响**（集成用例通过）；`before` 可解析非祖先路径**保持差集语义**（原行为）；**真缺陷仍拦**（defect-sim `rc=1`）。
   - **无"吞真缺陷"**：回退只改**回放起点**，不改门禁强度；被 push 的提交仍在回退区间内。
   - **边界观察（minor）**：① `_default_branch` 用 `.split("/")[-1]`——若 `origin/HEAD` 指向**含斜杠**的分支（如 `hotfix/x`），回退会拼成不存在的 `origin/x` → `FAIL`（`ci-sim` 实测复现）。**本 CI 不命中**（`origin/HEAD` 未设置 → `origin/main`），且该脆弱性**继承自既有全零路径**（非本轮新增）。② force-push 到**默认分支**且 `before` 不可解析时，`merge-base(HEAD, origin/main)=HEAD` → 区间空 → `SKIP`（与全零路径、PR 口径同，属既有边界）。
4. **同步面逐字一致**：README:108 / CHANGELOG:37-41 / roadmap:111 的"回退目标 + NOTE + FAIL 条件"与 `agate-ci-verify.py:492-504` **一致**（A1/A2/A5 已核）。r1 的 A2/A5/A8 已修。
5. **A8**：见上表，逐条命令复现，全部成立。

---

## 非阻断跟进（建议随本批或后续登记）

1. **补 pytest**：`before` 不可解析 **且** 无 `origin/<默认分支>` → 断言 `FAIL` + 清晰信息（覆盖 `agate-ci-verify.py:493-499`）。
2. **模块 docstring L10**：补一句 push 口径的"不可解析 → 回退 + NOTE"（与 README 一致）。
3. **登记 r1 已标两项**：workflow `detect-docs-only` 同假设（`before` 缺失 → 丢 fast-pass）；workflow 注释 L19-22 关于 gate-backstop required 的过期表述（实况：required 含 gate-backstop）。另可选加固 `_default_branch` 对含斜杠默认分支的处理。

> 结论：**可 commit**（上述 3 条均为非阻断）。
