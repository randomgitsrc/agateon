---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "r2 复审：hotfix 修第 1 轮 6 项 MISALIGNED + 1 BLOCKER（workflow shell 假红 / platform-notes 硬矛盾 / AGENTS.md 悬空引用 / skip 用例碰巧通过 / workflow 零覆盖 / CHANGELOG 缺失）"
files_changed:
  - .github/workflows/protocol-tests.yml
  - AGENTS.md
  - CHANGELOG.md
  - agate/platform-notes.md
  - agate/scripts/agate-ci-verify.py
  - agate/tests/unit/test_agate_ci_verify.py
---

# 协议-脚本对齐审查（r2）

**审查对象**：分支 `hotfix/ci-verify-explicit-base`（工作区未提交，`git diff` 6 文件）。
**本轮任务**：先读第 1 轮报告 `docs/reviews/agate-alignment-review-2026-10-09-HOTFIX-CI-BASE.md`，**逐条独立核实其发现是否已修**，再做完整 A1-A8 复审。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** |
| A4 | 测试覆盖 | **ALIGNED**（含 1 条非阻断 RESIDUAL） |
| A5 | 下游影响 + 文档传播 | **ALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **ALIGNED**（含 1 条措辞建议） |

> 第 1 轮的 1 个 BLOCKER 与 6 项 MISALIGNED **均已闭合**（逐条证据见下）。仅余若干**非阻断**建议（RESIDUAL），不影响 commit。

---

## 第 1 轮发现逐条核实

> 以下每条均为**独立复核**（不采信作者自述），附复核命令/实跑输出。

| # | 第 1 轮发现 | 修法（作者） | 独立复核 | 结论 |
|---|---|---|---|---|
| F1 | **[BLOCKER]** workflow `grep -A 3 'SKIP:' log1 log2`（无 `-q`）在 push 事件下 `ci-verify-push.log` 缺失 → grep exit 2 → `pipefail`+`-e` → step 假红 | 改 `logs=""` 只收集**存在**的日志 + 内层管道 `\|\| true` | 见「核实 F1」 | ✅ **已修** |
| F2 | `platform-notes.md:344` 硬矛盾（称「无参数可用 + 按 `merge-base HEAD origin/<默认分支>`」） | 改为「须显式给 `--base`……不再支持缺省推断，缺 `--base` 即 FAIL」 | `sed -n '344p'` → 已改，与新行为一致 | ✅ **已修** |
| F3 | 脚本 `:490`「（见 AGENTS.md）」为悬空引用（AGENTS.md 0 命中） | AGENTS.md「改脚本的工作流」新增 **0b** 步，给出两条口径命令 | `grep -n "0b\|agate-ci-verify" AGENTS.md` → 命中；命令可跑（见核实 F3） | ✅ **已修** |
| F4 | `test_bdd_16_ci_verify_skip_declared_with_reason` 空仓库「碰巧通过」 | 改为「有提交 + `--base HEAD`」，断言正则加 `未改动` | scratch 真脚本复现（见核实 F4）；`pytest` PASSED | ✅ **已修** |
| F5 | workflow shell 逻辑零覆盖 | 新增 `test_m1_pr_job_runs_both_invocations` | 该用例判别力实测（见核实 F5）；但**仅覆盖双口径存在性，未覆盖 SKIP-log 逻辑** | ⚠️ **部分闭合**（RESIDUAL R1） |
| F6 | `CHANGELOG.md [Unreleased]` 无条目 | 新增条目 | `sed -n '26,31p' CHANGELOG.md` → 已加，逐条比对行为（见 A5） | ✅ **已修** |
| F7 | `docs/design-notes/repro-tag0050.sh` 裸调 | 不改（判为冻结证据件） | 核实无 CI/测试引用（见核实 F7） | ✅ **可接受** |
| F8 | `agate/UPGRADING.md` 无本改动节 | 未加 | 见 A5：`[Unreleased]` 改动，UPGRADING 节按流程在**发布时**写；CHECK 13 0 ERROR | ✅ **可接受** |
| F9 | `agate/scripts/README.md:108` 未声明 `--base` 必填 | 未改 | 无矛盾（仅不完整） | ⚠️ RESIDUAL R2 |

### 核实 F1（BLOCKER）— 已修，实测复现

在一次性副本 `/tmp/opencode/r2scratch/` 用**逐字复刻**的新 step（`bash -e` + `set -o pipefail`）跑 5 个场景：

```
A push+SKIP (only ci-verify.log)  → STEP EXIT=0   summary 已写出 ✓  （改动前为 EXIT=2）
B PR both PASS                     → STEP EXIT=0   无 summary ✓
C PR one FAIL then PASS            → STEP EXIT=1 ✓（无假绿）
D push+PASS                        → STEP EXIT=0 ✓
E PR first SKIP second FAIL        → STEP EXIT=1   summary 已写出 ✓
```

修法逐点核对（`protocol-tests.yml`）：
- `logs=""`；`if [ -f /tmp/ci-verify.log ]; then logs="…"; fi`；`if [ -f /tmp/ci-verify-push.log ]; then logs="$logs …"; fi` ⇒ **只收集实际存在的文件**，`grep $logs` 不会遇到缺失文件（不会 exit 2）。
- `if [ -n "$logs" ] && grep -q 'SKIP:' $logs` —— `[ -n ]` 短路保护空 logs；`$logs` 无引号按空白拆成文件参数（路径无空格，安全）。
- 内层 `grep -A 3 'SKIP:' $logs | head -20 || true` —— `|| true` 兜底。
- `exit "$rc"` 在块之后，聚合逻辑未变。
⇒ **BLOCKER 闭合。**

### 核实 F3 — AGENTS.md 命令可跑

```
$ git merge-base HEAD origin/main   → 108fe8c3d763c82fffac69a18b23833577cdd9f9
$ git rev-parse origin/main         → 108fe8c3d763c82fffac69a18b23833577cdd9f9
```
AGENTS.md 0b 的两条命令（`--base "$(git merge-base HEAD origin/main)"` / `--push --base "$(git rev-parse origin/main)"`）在本仓可解析。脚本 `:490` 的「（见 AGENTS.md）」指针**已落地**。

### 核实 F4 — skip 用例真跑目标分支

一次性 scratch 仓库（有提交、无任务目录）实跑真脚本：
```
$ python3 agate/scripts/agate-ci-verify.py --base HEAD
SKIP: 回放范围 8155e5fe..8155e5fe 未改动任务目录（0 个提交）
rc=0
```
⇒ 该用例现真正命中「未改动任务目录」SKIP 分支（不再是空仓库的「无法解析 HEAD」），且断言正则含 `未改动`。`pytest …::test_bdd_16_ci_verify_skip_declared_with_reason` → **PASSED**。

### 核实 F5 — 新 workflow 用例的判别力

`test_m1_pr_job_runs_both_invocations` 断言 workflow 文本含 `args="--base $PR_BASE"` 与 `extra_args="--push --base $PR_BASE"`。scratch 反例（在副本文本上跑同一正则）：
```
原始            → r1(PR口径)=True  r2(push口径)=True
删 extra_args 行 → r1=True  r2=False
删 args 行       → r1=False r2=True
```
⇒ 对「两行之一被删」**有判别力**。但**不覆盖** F1 的 SKIP-log shell 逻辑（`logs=` 收集 / `|| true`）——见 RESIDUAL R1。

### 核实 F7 — repro-tag0050.sh 无 CI/测试引用

`grep -rn "repro-tag0050" --include=*.py/*.yml/*.sh .` → 仅 `docs/design-notes/repro-tag0050.sh` 自身 + `agate-workspace/tasks/TAG0050-*/`（冻结任务文档）与 `docs/design-notes/`。无任何 `tests/`、`.github/`、`gate_commands` 引用。且 `P2-design.md:333/358` 与 `P3-test-cases.md:243` 明确「`repro-tag0050.sh` 保留为**证据文档**，不再作 gate」。⇒ **不改可接受**。

---

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

**文档声明**（`agate/platform-notes.md:344`，本 diff 改后）：
> 需要等价实现：`git push` 后调用 `agate-ci-verify.py`（cwd = 项目根；**须显式给 `--base`**——PR 口径 `--base <base>`、push 口径 `--push --base <before>`；**不再支持**缺省推断，缺 `--base` 即 FAIL），它**逐提交回放**本地 hook 判定

**脚本实现**（`agate/scripts/agate-ci-verify.py:486-491`）：缺 `--base` → `_fail("--base 必填…")`（exit 1）；docstring `:11-12` 同步为「本地彩排：**必须显式**给 `--base`……**不再支持**缺省推断」。`AGENTS.md` 0b 提供本地彩排命令。

**结论**：**ALIGNED**（第 1 轮 A1 的两处矛盾——platform-notes 与 AGENTS.md 悬空引用——均已消除）。

### A2: 脚本→文档对齐 — ALIGNED

脚本新行为（缺 `--base` 即 FAIL）在文档面已同步：
- `agate/platform-notes.md:344`：已同步（见 A1）。
- `agate/scripts/README.md:108`：描述两口径，**未声明** `--base` 必填——**不矛盾**（未声称有缺省推断），仅不完整（RESIDUAL R2）。
- `agate/WORKFLOW.md:370`：「CI 用 `--base`/`--push --base` 传入回放范围」——一致。
- `agate/UPGRADING.md:353/369`：示例在 pr/push 分支显式给 base——一致。

**结论**：**ALIGNED**。

### A3: 一致性连锁 + 反向传播 — ALIGNED

**A3a 连锁**：脚本 / workflow / 测试 / platform-notes / AGENTS / CHANGELOG 六文件同主题同步。

**A3b 反向传播**（主动推断「应被影响」的文件，逐一核实）：

| 应被影响文件 | 现状 | 核实命令/证据 | 判定 |
|---|---|---|---|
| `agate/platform-notes.md:344` | 已改 | `sed -n '344p'` | ✅ |
| `AGENTS.md`（彩排命令） | 已加 0b | `grep -n 0b AGENTS.md`；命令可跑 | ✅ |
| `CHANGELOG.md [Unreleased]` | 已加条目 | `sed -n '26,31p'` | ✅ |
| `agate/scripts/README.md:108` | 未改（不完整） | 无矛盾 | ⚠️ R2（可选） |
| `agate/UPGRADING.md` | 未加节 | `[Unreleased]` 改动，发布时写；CHECK 13 0 ERROR | ✅（按流程） |
| `.github/workflows/release.yml` | 无调用 | `grep ci-verify release.yml` → 0 | ✅ N/A |
| `docs/design-notes/repro-tag0050.sh` | 裸调（未改） | 无 CI/测试引用（核实 F7） | ✅（冻结证据件） |
| `agate/tests/unit/test_check_gate.py:3619` | 非 git 仓库 SKIP | 走「非 git 仓库」分支 | ✅ 无需改 |

**结论**：**ALIGNED**。

### A4: 测试覆盖 — ALIGNED（含 RESIDUAL R1）

**实跑证据（本轮）**：
1. 变更相关两文件（`-n auto`）：
   ```
   $ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py agate/tests/integration/test_tag0050_ci_replay.py -n auto -q
   28 passed in 3.48s
   ```
2. 三条目标用例单跑：`test_bdd_16_ci_verify_skip_declared_with_reason` / `test_m1_pr_job_runs_both_invocations` / `test_m1_base_required_no_inference` → **3 passed**。
3. **全量**（`-n auto`）：
   ```
   $ python3 -m pytest agate/tests/ -n auto -q -p no:cacheprovider
   1 failed, 2876 passed, 2 skipped in 85.17s (0:01:25)
   FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
   ```
   唯一 failed 与本改动**无关**：本机 `opencode` CLI 报 `Unknown subcommand "agent" for "opencode debug"`（应为 `debug agents`）——环境/工具版本问题，diff 未触碰该文件（与第 1 轮同因）。
   跑前/跑后 `git status --porcelain` 一致。

**三条用例独立核实**：
- `test_m1_base_required_no_inference`：有提交 + 无 `--base` → FAIL（scratch 实跑 `FAIL: --base 必填…` rc=1）。✅ 真覆盖。
- `test_bdd_16_ci_verify_skip_declared_with_reason`：现真跑「未改动任务目录」SKIP（核实 F4）。✅ 真覆盖。
- `test_m1_pr_job_runs_both_invocations`：文本存在性，对「删任一口径行」有判别力（核实 F5）。⚠️ 未覆盖 F1 的 SKIP-log shell 逻辑。

**RESIDUAL R1（非阻断）**：F1 的 workflow SKIP-log 修复（`logs=` 收集 + `|| true`）**无 pytest 行为级守护**——本报告以 scratch 逐字复刻实测确认其正确（核实 F1）。这与本仓既有约定一致（`test_bdd_16_ci_verify_workflow_invokes_new_script` 等亦为文本存在性判据，workflow YAML 无法被 pytest 执行）。**建议**（可选）：若担心未来回归，可将该 step 的 shell 抽为可测脚本。

**结论**：**ALIGNED**（第 1 轮两项问题——skip 用例碰巧通过、workflow 零覆盖——已分别闭合/部分闭合；余 R1 为非阻断）。

### A5: 下游影响 + 文档传播 — ALIGNED

**CHANGELOG 条目核对**（`CHANGELOG.md:26-31`）：
> `agate-ci-verify` 缺 `--base` 时静默推断 + PR 只跑一条口径（TAG0050 P8 事故根因，评审建议先行落地）：① `--base` 改为**必填**……push 到默认分支时该值 = HEAD 自己 ⇒ 用新协议回放历史提交致误报；② `gate-backstop` 的 **PR 事件同时跑两条口径**……详见 `AGENTS.md`「改脚本的工作流」0b。

逐点核对：①「静默推断」→ 属实（原 `:486-491` 旧代码走 `_merge_base`）；「必填」→ 属实（`_fail`）；②「PR 同时跑两条口径」→ 属实（workflow `args`+`extra_args`）；「详见 AGENTS.md 0b」→ 0b 存在（核实 F3）。**无夸大**。
> ⚠️ 唯一措辞问题：「使『PR required 绿 ⇔ 合并后 main 绿』对同一组提交成立」——`gate-backstop` **当前非 required**（同文件 `:19-22` 自述），该等价性在重新纳入 required 前不严格成立。属措辞（RESIDUAL R3），**不阻断**。

**UPGRADING**：本改动在 `[Unreleased]`；UPGRADING 版本节按发布清单在**发布时**写（AGENTS.md「版本发布清单」第 3 步），`CHECK 13` 0 ERROR。**符合流程**。

**结论**：**ALIGNED**。

### A6: 锚点表覆盖 — ALIGNED

- 既有函数内部语义修正 + workflow 逻辑，未引入新协议规则/字段/BDD 编号，CHECK 9 锚点表无需更新。
- 实跑 `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**（CHECK 9 PASS）。
- CHECK 10 唯一 WARNING = `CHANGELOG.md:99` 历史叙事引用退役名 `ci-gate-backstop.py`（冻结文件），**非本改动引入**。

**结论**：**ALIGNED**。

### A7: 设计原则一致性 — ALIGNED

- **ADR-014（判据单一权威源）**：回放基准解析收敛为单点（主流程算 `base` → 传入 `_resolve_protocol`，`:541`），消除第二份推断源。**一致**。
- **ADR-015（实质/非实质；让错误不可能/可见）**：删除静默推断 = 手段①「让错误不可能」。**一致**。
- **ADR-002（可判定性）**：缺参 → FAIL 可机械判定。**一致**。

**附带观察**（同第 1 轮，非 ADR 违反）：workflow `:320-321` 与 CHANGELOG `:29-30` 的「PR required 绿 ⇔ main 绿」措辞，与同文件「gate-backstop 非 required」自述存在张力（RESIDUAL R3）。

**结论**：**ALIGNED**。

### A8: 声称-命令绑定 — ALIGNED

| 声称（来源） | 产出它的命令 | 结论 |
|---|---|---|
| 「缺 `--base` 即 FAIL，不得从 HEAD/origin 推断」（`agate-ci-verify.py:487-491`；`platform-notes.md:344`；`CHANGELOG.md:26`） | 有提交仓库 `python3 agate/scripts/agate-ci-verify.py`（无 `--base`）→ rc=1 `FAIL: --base 必填` | ✅ 成立 |
| 「本地彩排两条口径命令」（`AGENTS.md` 0b；脚本 `:490` 指向它） | `git merge-base HEAD origin/main` / `git rev-parse origin/main` 均可解析（核实 F3）；命令即 0b 文本 | ✅ 成立 |
| 「PR 事件同时跑两条口径」（`CHANGELOG.md:28`；workflow `:326-327`） | `grep -E 'args="--base \$PR_BASE"\|extra_args="--push --base \$PR_BASE"' protocol-tests.yml` → 两行均在 | ✅ 成立 |
| 「三条用例覆盖其声称场景」（测试 docstring） | `pytest …::test_m1_base_required_no_inference ::test_bdd_16_ci_verify_skip_declared_with_reason ::test_m1_pr_job_runs_both_invocations` → 3 passed | ✅ 成立 |
| 「使『PR required 绿 ⇔ 合并后 main 绿』对同一组提交成立」（`CHANGELOG.md:29-30`；workflow `:320-321`） | 无法给出命令；且 `:19-22` 自述 gate-backstop 非 required | ⚠️ 措辞过度（R3，建议软化，非阻断） |

**结论**：**ALIGNED**（第 1 轮的无据声称「（见 AGENTS.md）」已落地为可复核引用；仅余 R3 措辞建议）。

---

## 五项重点核查结论（本轮）

1. **workflow shell 正确性**：F1 BLOCKER **已修并经 scratch 逐字复刻实测**（push+SKIP → exit 0 且 summary 正常；PR FAIL → exit 1；无假绿/假红）。✅
2. **`--base` 必填后的既有调用面**：非冻结裸调仅剩 `docs/design-notes/repro-tag0050.sh`（冻结证据件，无 CI/测试引用，可接受）；`platform-notes.md` 已同步；`release.yml` 无调用。✅
3. **测试充分性**：三条用例独立核实——两条真覆盖（base 必填、未改动 SKIP），一条有判别力但仅存在性（PR 双口径）。SKIP-log shell 逻辑无行为级守护（R1，非阻断，已 scratch 验证）。✅
4. **② 是否引入新的假绿/假红**：聚合正确（任一 FAIL → 最终 FAIL）；SKIP 覆盖存在的日志；**假红已消除**。✅
5. **① 是否削弱本地可用性 + 文档同步**：`--base` 必填仍需显式传值（可用性变化），但 `AGENTS.md` 0b 已落地彩排命令、`platform-notes.md` 已同步。✅

---

## 残留项（均非阻断，供人工取舍）

| # | 残留项 | 建议 |
|---|---|---|
| R1 | workflow SKIP-log shell 逻辑（F1 修复）无 pytest 行为级守护 | 可选：抽 step shell 为可测脚本；否则维持（本报告已 scratch 实测其正确） |
| R2 | `agate/scripts/README.md:108` 未声明 `--base` 必填 | 可选：补一句 |
| R3 | CHANGELOG/workflow 注释「PR required 绿 ⇔ 合并后 main 绿」措辞过度（gate-backstop 非 required） | 可选：软化为「PR 与 push 两口径对同一组提交都回放」 |
| R4 | `docs/design-notes/repro-tag0050.sh` 裸调 | 维持不改（冻结证据件） |
| R5 | `agate/UPGRADING.md` 无本改动节 | 维持（发布时按清单写） |

## 放行建议

**A1–A8 全部 ALIGNED** ⇒ **可 commit**。第 1 轮 BLOCKER 与 6 项 MISALIGNED 均已闭合；残留 5 项为非阻断建议（R1–R5），可择机处理。

> **注**：F1 的 exit-2 修复结论为**在一次性副本上的逐字复刻实测**（未在真实仓库运行写操作）；全量 pytest 与 consistency 均为只读运行，跑前/跑后 `git status --porcelain` 一致。
