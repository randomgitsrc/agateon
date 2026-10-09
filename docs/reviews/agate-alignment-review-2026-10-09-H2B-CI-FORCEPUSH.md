---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 修 `agate-ci-verify` push 口径在 `before` 非 HEAD 祖先时的假 FAIL（RM-AG0112）
files_changed: [agate/scripts/agate-ci-verify.py, agate/tests/unit/test_agate_ci_verify.py, agate-workspace/roadmap/roadmap.md, CHANGELOG.md]
---

# 协议-脚本对齐审查（批 B/H2 · CI force-push）

**审查对象**：`hotfix/batch-b-hygiene` 分支上**未提交**的工作区改动（`ac93f22c` 之后新增）。
**审查范围**：`git diff` 全部 4 文件 + 第二步推断的反向传播面 + 权威源（`agate/WORKFLOW.md`、`.github/workflows/protocol-tests.yml`、`agate/scripts/README.md`）。

---

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | **MISALIGNED** |

> **一句话总评**：脚本改动**语法无误、NOTE 非静默**，但**没有修复它声称要修的那个缺陷**——PR #422 的 `before`（`7c419e93`）在 CI 检出中**是一个不存在的对象**（不是"存在但非祖先"），新逻辑在该情形下**仍判 FAIL**（实测 rc=1）。回归用例复现的是一条**从未产生失败**的路径。⇒ **必须修复**。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate-workspace/roadmap/roadmap.md:111`，RM-AG0112）：
> push 口径下 `rev-list <before>..HEAD` 在 `before` **非 HEAD 祖先**（rebase / 历史改写后强推）时直接失败 ⇒ 判 FAIL……**修**：`--push` 且 `before` 非 HEAD 祖先时回退 `merge-base(before, HEAD)`（= 分支点）并**显式** NOTE（不静默）；merge-base 也解析不出才 FAIL。**验收锚=force-push / rebase 后强推不再假红**；真缺陷仍拦

**脚本实现**（`agate/scripts/agate-ci-verify.py:489-501`）：
> ```python
> _rc_anc, _, _ = _git(["merge-base", "--is-ancestor", base, head], repo)
> if _rc_anc != 0:
>     _mb = _git_out(["merge-base", base, head], repo)
>     if not _mb:
>         return _fail(f"push 的 before（{base[:8]}）不是 HEAD 的祖先，且无法解析 merge-base(before, HEAD)——无法确定回放范围")
>     print(f"NOTE: push 的 before {base[:8]} 不是 HEAD 的祖先 ... base = _mb")
>     base = _mb
> ```

**结论**：**MISALIGNED**。

**差异（决定性，附实测）**：

1. **文档对失败条件的表述是错的**。`git rev-list A..B`（即 `B ^A`）**不要求** A 是 B 的祖先——A 存在但非祖先时**照样成功**（它算集合差）。它**只有在 A 不是有效版本对象时**才失败。实测（本仓 `7c419e93` 对象存在）：
   - `git rev-list --no-merges 7c419e93..ac93f22c` → `rc=0`（成功）。
   - 在**无**该对象的仓库：`fatal: Invalid revision range 7c419e93…f94..ac93f22c`（`rc=128`）。
   ⇒ 真实失败根因是 **`before` 对象在 CI 检出中缺失**，而非"非祖先"。

2. **CI 检出于结构上不含 `before` 对象**（实证）：
   - job 113733056770 的 `PUSH_BEFORE=7c419e936046fb80b262daca6e3f1a6fbd551f94`（= rebase 前 head）。
   - 该 job 的 fetch 命令（日志 L93）：`git fetch --prune --no-recurse-submodules origin +refs/heads/*:refs/remotes/origin/* +refs/tags/*:refs/tags/*`——**只按 ref 取对象**，悬空的旧 head 不在任何 ref。
   - `git ls-remote origin | grep -c 7c419e93` = **0**；用同一 refspec 做 fresh clone → `git cat-file -t 7c419e93…` = `fatal: could not get object`（缺失）。
   - 旁证：CI 报出的就是本脚本的 `FAIL: rev-list 7c419e93..ac93f22c 失败`——该分支**仅**在 `rev-list` 返回非 0 时触发，而非 0 只可能因对象缺失。

3. **新逻辑在真实场景下仍判 FAIL**（`/tmp/opencode/ci-sim` = fresh clone + 同一 refspec，HEAD=`ac93f22c`，无 `7c419e93`）：
   ```
   $ python3 agate/scripts/agate-ci-verify.py --push --base 7c419e936046fb80b262daca6e3f1a6fbd551f94
   FAIL: push 的 before（7c419e93）不是 HEAD 的祖先，且无法解析 merge-base(before, HEAD)——无法确定回放范围
   rc=1
   ```
   ⇒ `--is-ancestor` 因对象缺失返回 128（≠0）进入回退分支，随后 `merge-base` 同样因对象缺失返回空 → 走 `_fail`。**PR #422 仍会被拦**——**声称的"修"未达成**。

4. **`--is-ancestor` 用法本身正确**（0=祖先 / 1=非祖先 / 其它=错误，均被 `!= 0` 覆盖）；回退语义（`merge-base(before, HEAD)` = 分支点）与 PR 口径（`merge-base(base, HEAD)`）**一致**；NOTE **确实非静默**（`print` 到 stdout，实测输出见 A4/A8）。**问题不在实现细节，而在它命中的分支是"从未失败"的那条。**

**建议**：`before` **无法解析**（对象缺失）时应回退到**可解析**的基准——最自然的是 `merge-base(HEAD, origin/<默认分支>)`（= 分支点，即本分支引入的提交范围，与 PR 口径同源），并打印同样显式 NOTE；仅当该值也解析不出才 FAIL。这样才覆盖 PR #422 的真实形态。

### A2: 脚本→文档对齐

**脚本改动**：push 口径新增"非祖先 → 回退 + NOTE"分支（`agate-ci-verify.py:484-501`）。

**应同步的文档**：

| 位置 | 现状 | 是否同步 |
|------|------|----------|
| `agate/scripts/README.md:108`（`agate-ci-verify.py` 行）| 只写「`--push --base <sha>`（push 口径；`before` 全零时回退 `merge-base HEAD origin/<默认分支>`）」| **未同步**——没有描述新增的"非祖先/对象缺失"回退 |
| `agate-ci-verify.py:10`（模块 docstring）| 「GitHub push（`--push --base <sha>`）：`rev-list --no-merges <before>..HEAD`」| **未同步**——只列原始口径，未提回退 |

**结论**：**MISALIGNED**（脚本行为已变，对应文档仍写旧口径）。

**建议**：`README.md:108` 补一句「`before` 非 HEAD 祖先 / 解析不出时的回退与 NOTE 口径（RM-AG0112）」；脚本 docstring L10 同步。

### A3: 一致性连锁 + 反向传播

**A3a（连锁：已知衍生改动）**：无新增脚本名、无新增 frontmatter 字段、无新增 CHECK 规则 → 无连锁面。

**A3b（反向传播：主动推断的"应被影响但不在 diff"的文件）**：

| 文件 | 是否应受影响 | 现状 |
|------|--------------|------|
| `agate/scripts/README.md`（工具清单表 L108）| **应**（角色表：`agate/scripts/check-*.py` 行为 → README）| **未改** → GAP |
| `AGENTS.md` 0b（本地彩排 L103-106）| 不受影响：push 口径用 `--base "$(git rev-parse origin/main)"`，`origin/main` 恒为 HEAD 祖先（存在），不触发新分支 | OK |
| `agate/WORKFLOW.md:370`「Pre-commit 检查总览 → CI 兜底」| 高层次描述，未要求回退细节；可选补一句 | 可接受 |
| `RM-AG0103` | 主题相邻（"PR绿⇔main绿"靠 push 口径覆盖），可加交叉引用；**非强制** | 未改（可接受） |
| `RM-AG0098` | 无关（CHECK 7/13 发布顺序）| 不涉及 |
| **`.github/workflows/protocol-tests.yml` `detect-docs-only`（L82-95）** | **同一个潜在假设**：push 事件下 `git merge-base "$BASE" "$HEAD"` 在 `before` 缺失时失败 → `MERGE_BASE` 空 → `docs_only=false`（fail-closed，**不假红**，只是丢失 fast-pass）| **未改**；属既有、非本 diff 引入的同类隐患，建议一并登记 |
| **workflow 注释 L19-22** | 称「gate-backstop 已移出 required（2026-10-05）」| **与实况不符**：`gh api .../branches/main/protection` 的 required contexts **含 `gate-backstop`**（6 个）。注释过期，且**恰好支撑本次"BLOCKED"前提** |

**结论**：**MISALIGNED**（`README.md` 反向传播缺失；另有 2 处同源/过期项待登记）。

### A4: 测试覆盖

**新增用例**：`agate/tests/unit/test_agate_ci_verify.py:356-391`（`test_rm_ag0112_push_before_not_ancestor_not_fake_fail`）。

**实跑输出**（跑前后 `git status` 一致，仅多本次的 progress 留痕文件）：

```
# 本批被改测试文件（新码）
$ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py -n auto -q
11 passed in 0.83s

# 全量（-n auto）
$ python3 -m pytest agate/tests/ -n auto -q
1 failed, 2896 passed, 2 skipped in 86.41s (0:01:26)
# 唯一 failed = test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
#   根因=本地 opencode CLI `debug agent` 子命令漂移（`Unknown subcommand "agent"`），与本次 diff 无关

# 判别力 scratch（新测试 vs 旧代码，在一次性 clone /tmp/opencode/ci-sim 中，未触碰被评审仓）
$ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py -n auto -q   # clone 内 agate-ci-verify.py 为旧（已提交）版
1 failed, 10 passed
```

**结论**：**MISALIGNED**。理由：

1. **用例有判别力**——旧代码下**转红**（`1 failed`），但**红在第二个断言**（缺 NOTE），**不是**第一个断言。旧码在该用例场景下 `rc=0`（见下条），所以第一断言 `returncode == 0` **无判别力**。
2. **用例复现的是"非缺陷"路径**：它用 `git reset --hard HEAD~1` 让 `stale`（c1）**悬空但对象仍在**（reflog 持有）。实测旧码在此场景 `rev-list stale..HEAD` **成功** → `rc=0` + `SKIP`（无 FAIL）。⇒ 它**既没复现真 FAIL，也没复现假红**，只验证了新 NOTE 行为。
3. **真缺陷（`before` 对象缺失）无覆盖**：全仓无任何用例以"不存在的对象"为 `before`（`integration/test_tag0050_ci_replay.py::test_push_all_zero_before_does_not_fail` 只覆盖全零）。
4. **新逻辑的另一分支"merge-base 也解析不出 → FAIL"**（`agate-ci-verify.py:492-495`）**无用例覆盖**（该用例场景总能解析出 merge-base）。

**建议**：加一条以**缺失对象**（如随机 40-hex SHA，或用 `git reflog expire --expire=now --all && git gc --prune=now` 真正剪除悬空提交）为 `before` 的用例，断言新码不 FAIL。

### A5: 下游影响 + 文档传播

- **CHANGELOG**：已加 [Unreleased] 修复条目（`CHANGELOG.md:37-42`）——**✓ 有**。
- **UPGRADING**：无破坏性变更，无需新增章节——✓。
- **但 CHANGELOG 的因果与结论表述不准确**：
  - L37 写「`rev-list <before>..HEAD` 在 `before` **非 HEAD 祖先**时直接失败」——**事实错误**（非祖先不导致失败，对象缺失才导致；见 A1）。
  - L39-42「**修**：……merge-base 也解析不出才 FAIL」——字面对代码成立，但**对报告的事故（PR #422）不成立**（实测仍 FAIL）。
- **文档传播**：`README.md` 未同步（同 A2/A3b）。
- **下游 gate 行为**：改动只在 `--push` 且 `base` 非祖先时生效；新建分支（全零）路径在更早处处理（`agate-ci-verify.py:478-479`）→ `base=merge-base(HEAD)` 恒为祖先 → 新分支不受影响（✓）。常规 push（`before` 为祖先）不受影响（`--is-ancestor` 返回 0 → 跳过）→ **无回归**。

**结论**：**MISALIGNED**（文档因果表述错误 + README 未传播）。

### A6: 锚点表覆盖

改动是 `agate-ci-verify.py` 内部判定逻辑，**未新增协议规则、脚本名、frontmatter 字段或 CHECK 规则**。`check-protocol-consistency.py` 的 CHECK 9 锚点表无 `agate-ci-verify` 专属锚点（仅 L956 一处"退役名保留"注释，不涉及 push 口径）。**无需更新锚点表**。

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-002（可判定性）**：修复方向（让门禁对"提交本身没问题"不误判）符合。
- **ADR-014（判据单源）**：改动仍单源（判据只在 `agate-ci-verify.py`），符合；但其"文档可以复述"要求下，`README.md` 复述**尚未跟上**（已计入 A3b，非本项 ADR 违反）。
- **ADR-015（实质/非实质）**：假红会**阻断合并**（实质），修它方向正确。
- **未发现未记录的架构决策**；唯一"设计决策"是"`before` 无法解析时该回退到什么"——这是一个**取值选择**（建议见 A1），不影响本项结论。

**结论**：ALIGNED（无 ADR 违反；ADR-014 的"复述"义务在 A3b 追踪）。

### A8: 声称-命令绑定

| # | 声称（出处）| 产出它的命令 | 结论 |
|---|-------------|--------------|------|
| 1 | 「对 force-push / rebase 判假 FAIL……**修**」/「验收锚=force-push / rebase 后强推**不再假红**」（`roadmap.md:111`、`CHANGELOG.md:37`）| 在无 `before` 对象的 CI 同构仓库跑 `agate-ci-verify.py --push --base 7c419e93…f94`（`/tmp/opencode/ci-sim`）| **不成立**：`FAIL … rc=1`（仍假红）→ 该声称**应予删除/改写** |
| 2 | 「回归用例 `test_rm_ag0112_push_before_not_ancestor_not_fake_fail`」（`roadmap.md:111`）| `grep`/`pytest agate/tests/unit/test_agate_ci_verify.py` | ✓ 用例存在；新码通过、旧码转红（判别力成立）|
| 3 | 「11 passed」（本批自述）| `python3 -m pytest agate/tests/unit/test_agate_ci_verify.py -n auto -q` | ✓ `11 passed in 0.83s` |
| 4 | 「0 ERROR」（本批自述）| `python3 agate/scripts/check-protocol-consistency.py` | ✓ `0 ERROR`（419 WARNING，冻结文件）|
| 5 | 用例 docstring「实测复现：PR #422 rebase 后强推……`rev-list <before>..HEAD` 失败 ⇒ FAIL」（`test…py:359-367`）| 复现用例场景（stale 对象**存在**）跑旧码 `rev-list` | **不成立**：`rc=0`（成功）→ 用例复现的是**非缺陷路径** |
| 6 | 「push 口径下 `rev-list` 在 `before` **非 HEAD 祖先**时直接失败」（`CHANGELOG.md:37`）| `git rev-list A..B`（A 存在但非祖先）| **不成立**：`rc=0`（只有 A 不存在才失败）|

> 按角色约定，**无法给出命令的声称应删除**。上表 #1、#5、#6 属**表述错误/未成立**的声称，须随修复一并更正。

**结论**：**MISALIGNED**。

---

## 重点结论（对应派发单 4 项）

1. **修复是否正确**：**否**。`merge-base --is-ancestor` 用法正确、回退语义（= 分支点）与 PR 口径一致、NOTE 非静默——**但命中的分支是"存在但非祖先"，而该情形下旧码 `rev-list` 本就不失败**。真实场景是 **`before` 对象在 CI 检出中缺失**，此时 `merge-base` 也解析不出 → 新码**仍 `FAIL`**（实测 rc=1）。**PR #422 形态未被修复。**
2. **是否引入新问题**：新建分支（全零）路径**不受影响**（更早分支处理，回退值恒为祖先）；常规 push 不受影响（`--is-ancestor`=0 跳过）；FAIL 信息**清晰**。唯一"吞真缺陷"风险方向相反——**是over-fail（漏放行），不是漏拦**。
3. **测试判别力**：**有**（旧码转红，实测 `1 failed/10 passed`），但**红的理由错**（红在 NOTE 断言，非 rc）；且**未覆盖真缺陷**（对象缺失）与**"merge-base 解析不出 → FAIL"分支**。用例 docstring 的"复现"声称**不成立**。
4. **A8 复现**：见上表；`11 passed` ✓、`0 ERROR` ✓，但**核心声称「不再假红」在真实场景下证伪**（命令：#1）。

---

## 闭环建议（供主 Agent 派 implementer）

1. **改脚本**：`before` **无法解析**（对象缺失）时，回退 `merge-base(HEAD, origin/<默认分支>)`（分支点，与 PR 口径同源）并显式 NOTE；仅当该值也解析不出才 FAIL。（保留现有"存在但非祖先 → `merge-base(before, HEAD)`"分支亦可。）
2. **补测试**：以**缺失对象**（随机 40-hex SHA 或真正 `gc --prune=now` 后的悬空提交）为 `before`，断言不 FAIL；补一条"完全无法确定回放范围 → FAIL"分支用例；并修正现有用例 docstring 的"复现"表述。
3. **修文档**：`agate/scripts/README.md:108` + 脚本 docstring L10 同步新回退口径；`CHANGELOG.md:37` 与 `roadmap.md:111` 更正"非祖先 → 失败"的因果表述，并把"不再假红"的验收锚改为可复核命令。
4. **登记**：workflow `detect-docs-only` 的同类假设 与 workflow 注释 L19-22 的 required 过期表述，建议一并登记（不阻断本批）。

> 修完须重跑本审查（MISALIGNED 项修复后重审）。
