---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "落实 TAG0050 实施评审对 RM-AG0103 的两项可先 hotfix 落地建议：① agate-ci-verify 的 --base 由缺省推断改为必填（缺则 FAIL）；② PR job 同时跑 --base 与 --push --base 两条回放口径"
files_changed:
  - .github/workflows/protocol-tests.yml
  - agate/scripts/agate-ci-verify.py
  - agate/tests/unit/test_agate_ci_verify.py
---

# 协议-脚本对齐审查

**审查对象**：分支 `hotfix/ci-verify-explicit-base`（工作区未提交，`git diff` 3 文件；另有本报告与本报告留痕文件为审查产物）。

**变更意图**：闭合 TAG0050 P8 发布事故根因「PR 绿 ≠ 可发布」（RM-AG0103，`agate-workspace/roadmap/roadmap.md:102`）。落地其中两项「可先 hotfix 落地」建议：
- ① `agate-ci-verify` 的 `--base` **必填**——删除缺省时静默推断 `merge-base HEAD origin/<默认分支>` 的路径（push 到默认分支时该值 = HEAD 自己 ⇒ 用新协议回放历史提交致误报 FAIL）；
- ② PR job **同时跑两条口径**（`--base` 与 `--push --base`）——脚本里这是两条独立的范围/协议根解析路径。

> 触发面：`agate/scripts/*.py`、`.github/workflows/*.yml`（SELF-GATE）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **MISALIGNED** |

> **头号问题（必须先修）**：② 新增的 workflow 补充回放块在 **push 事件 + 回放 SKIP** 时会以 **exit 2 中断整个 step**（`grep -A 3` 双文件之一缺失 + `set -o pipefail` + GitHub 默认 `bash -e`），本应是 `SKIP`（rc=0）的绿色路径变成**假红**。已在一次性副本上实测复现（见 A4 / 重点结论 1）。
>
> **次号问题**：① 引入「缺 `--base` 即 FAIL」后，`agate/platform-notes.md:344` 仍向用户声称「调用 `agate-ci-verify.py`（无参数…按 `merge-base HEAD origin/<默认分支>` 回放）」——与脚本新行为直接矛盾（A1/A2/A3）；且脚本失败信息里的「见 AGENTS.md」指向一份**不存在该命令**的文档（A8）。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**意图来源**（`agate-workspace/roadmap/roadmap.md:102`，RM-AG0103）：
> **配套**：`agate-ci-verify --base` **必填**（禁从 `HEAD`/`origin` 推断）+ **PR job 跑双口径**（PR/push）

**脚本实现**（`agate/scripts/agate-ci-verify.py:486-491`）：
```python
    else:
        return _fail(
            "--base 必填（TAG0050 评审 M-1 配套）：**不得**从 HEAD/origin 推断——push 到默认分支时 "
            "merge-base = HEAD 自己 ⇒ 会用新协议回放历史提交致误报 FAIL。"
            "本地彩排请显式给 --base \"$(git merge-base HEAD origin/<默认分支>)\"（见 AGENTS.md）。"
        )
```
**结论**：脚本对 ① 的实现与 RM-AG0103 语义一致（缺 `--base` 即 `_fail`，不再走 `_merge_base`）。docstring `:11-12` 也同步为「本地彩排：**必须显式**给 `--base`……**不再支持**缺省推断」。

**但存在两处文档侧矛盾**（故本项 MISALIGNED）：

1. **`agate/platform-notes.md:344`**：
   > 需要等价实现：`git push` 后调用 `agate-ci-verify.py`（**无参数**，cwd = 项目根；它按 `merge-base HEAD origin/<默认分支>` **逐提交回放**本地 hook 判定）

   该行同时声称「无参数调用可用」与「按 `merge-base HEAD origin/<默认分支>` 回放」——两条都被 ① 删除。文档与脚本语义**直接冲突**。

2. **脚本失败信息 `:490` 的 `（见 AGENTS.md）`**：`grep -n "ci-verify\|彩排\|agate-ci" AGENTS.md` **0 命中**（AGENTS.md 唯一的 `merge-base` 在 G-5 发布清单 `:166`，与彩排无关）。脚本指向一份不含该内容的文档。

**建议**：修 `platform-notes.md:344`（改为「须显式传 `--base <merge-base>`；无参数即 FAIL」）；在 `AGENTS.md` 增补本地彩排命令，或删除脚本信息里的 `（见 AGENTS.md）`。

---

### A2: 脚本→文档对齐 — MISALIGNED

**脚本新行为**（`agate/scripts/agate-ci-verify.py:486-491`）：缺 `--base` → `FAIL`（exit 1），删除 `merge-base HEAD origin/<默认分支>` 缺省推断。

**协议文档现状**：
- `agate/scripts/README.md:108`：描述 `--base`/`--push --base` 两个口径，但**未声明 `--base` 必填**（既不矛盾也不完整）——建议补一句。
- `agate/WORKFLOW.md:370`：「CI 用 `--base`/`--push --base` 传入回放范围」——与实现一致，无需改。
- `agate/platform-notes.md:344`：**仍描述被删除的缺省推断**（见 A1）⇒ **MISALIGNED**。
- `agate/UPGRADING.md:353/369`（GitHub / GitLab CI 等价写法示例）：两条示例的 `if/elif` 只在 pr/push 分支赋值 `args`，其余事件 `args` 为空——配合 ① 后，非 pr/push 事件将 FAIL（示例未提示）。示例本身对 pr/push 是显式 `--base`，不矛盾，但**未反映新必填契约**。

**结论**：**MISALIGNED**（`platform-notes.md:344` 为硬矛盾）。
**建议**：修 `platform-notes.md:344`；`scripts/README.md:108` 与 `UPGRADING.md` 示例补「`--base` 必填 / 非 pr-push 事件亦须给 base」。

---

### A3: 一致性连锁 + 反向传播 — MISALIGNED

#### A3a 连锁（已知衍生改动）— ALIGNED
三处同主题文件同步改动：脚本（`agate-ci-verify.py:486-491`）、workflow（`protocol-tests.yml:317-351`）、测试（`test_agate_ci_verify.py:308-326`）。② 的 workflow 改动与 ① 的脚本改动是同一自洽主题。

#### A3b 反向传播（主动推断「应被影响但未列在 diff」的文件）

| 应被影响文件 | 是否被影响 | 核实命令/证据 | 判定 |
|---|---|---|---|
| `agate/platform-notes.md:344` | **否** | `grep -n "merge-base HEAD origin" agate/platform-notes.md` → 命中 `:344` 仍称无参可用 | **遗漏（硬矛盾）** |
| `AGENTS.md`（彩排命令） | **否** | `grep -n "ci-verify\|彩排" AGENTS.md` → 0 命中 | **遗漏**（脚本 `:490` 已引用它） |
| `CHANGELOG.md` `[Unreleased]` | **否** | `sed -n '12,31p' CHANGELOG.md` → 无本改动条目 | **遗漏** |
| `agate/UPGRADING.md` | **否** | `:279` v0.80.1 节讲的是 PR#409 协议根修复，非 `--base` 必填；无新节 | **遗漏** |
| `agate/scripts/README.md:108` | 部分 | 未声明 `--base` 必填 | 建议补 |
| `.github/workflows/release.yml` | N/A | `grep ci-verify release.yml` → 0 命中 | 无需改 |
| `docs/design-notes/repro-tag0050.sh:113-114,157-161` | **会受影响** | 裸调 `python3 agate/scripts/agate-ci-verify.py`（无 `--base`）→ 现会 FAIL | 见下 |
| `agate/tests/unit/test_check_gate.py:3619` | 否（碰巧） | 在非 git 仓库 tmp_path 调用，走「非 git 仓库」SKIP | 无需改 |

**`docs/design-notes/repro-tag0050.sh`**：F15/F15b 复现行 `:113-114` / `:157-161` 裸调脚本。该文件是 TAG0050 设计期的**冻结复现件**（记录的是 A2 改造前的缺陷基线），现行为变化会使其输出由 `SKIP/PASS` 变为 `FAIL`。**属历史冻结件，是否回改交人工**（不阻断本 hotfix）。

**结论**：**MISALIGNED**（`platform-notes.md` 硬矛盾 + `AGENTS.md`/`CHANGELOG`/`UPGRADING` 三处遗漏）。

---

### A4: 测试覆盖 — MISALIGNED

**实跑证据（本次审查）**：

1. 变更相关的两个测试文件（`-n auto`）：
   ```
   $ python3 -m pytest agate/tests/unit/test_agate_ci_verify.py agate/tests/integration/test_tag0050_ci_replay.py -n auto -q
   27 passed in 3.24s
   ```
2. **全量 pytest**（`-n auto`）：
   ```
   $ python3 -m pytest agate/tests/ -n auto -q -p no:cacheprovider
   1 failed, 2875 passed, 2 skipped in 85.71s (0:01:25)
   FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
   ```
   唯一 failed 经单独复跑确认**与本改动无关**：本机 `opencode` CLI 报 `Unknown subcommand "agent" for "opencode debug"`（应为 `debug agents`）——环境/工具版本问题，diff 未触碰 `test_setup_agate_dir.py`。
   跑前/跑后 `git status --porcelain` 一致（仅 3 个被评审文件 + 本报告产物）。

**新增用例**（`test_agate_ci_verify.py:308-326` `test_m1_base_required_no_inference`）：构造**有提交**仓库（`git_repo.commit("init")` 保证 HEAD 可解析），无 `--base` 运行 → 断言 `returncode != 0` 且输出含 `--base`。**真覆盖「有提交 + 无 `--base` → FAIL」**，判别力成立（改动前该路径会走 `_merge_base` 推断）。✓

**问题**：

1. **`test_bdd_16_ci_verify_skip_declared_with_reason`（`:135-154`）只是「碰巧通过」**：其 docstring 声称「Given 一个非 agate 项目（无 `.state.yaml` / 无任务）」，但 `git_repo` fixture（`conftest.py:411-440`）的 `GitRepo.__init__` 只 `git init` + config，**不建任何提交** ⇒ 脚本 `:472-473` `head = _git_out(["rev-parse","HEAD"])` 为空 → 走 `_skip("无法解析 HEAD")`。断言（含 `SKIP` + `原因`）仍成立，但它验的是**空仓库**分支，**未验其声称的「有提交但无任务」的 `SKIP` 分支**。改动前后该用例都经此路径通过 ⇒ 对本改动的回归守护力为零。

2. **workflow 的 shell 逻辑无任何测试守护**：② 新增的 `args/extra_args/rc/rc2/exit` 聚合与双文件 `grep` 全在 `run` step 内，`pytest` 不执行 workflow。**重点结论 1 的 exit-2 假红缺陷正是此盲区**——无测试能抓。

3. `test_check_gate.py:3619` 的 `test_tag0035_bdd_2_ci_verify_exit_code_comparison_unaffected` 同样在**非 git 仓库** `tmp_path` 运行、无 `--base`，走 `:465-466` 的「非 git 仓库」SKIP——其 docstring 声称验「`.gate-result.json` 比对逻辑」，实际从未进入该分支（**既有弱点，非本 diff 引入**）。

**结论**：**MISALIGNED**。
**建议**：① 修 workflow 缺陷（见重点结论 1）；② 把 `test_bdd_16_...skip...` 改为**真建一个含提交的非 agate 仓库**（使走「有提交但无任务」SKIP）；③ 为 workflow 的 push+SKIP 路径补一条可执行判据（如把 shell 逻辑抽成可测脚本，或在 CI 里加自检步骤）。

---

### A5: 下游影响 + 文档传播 — MISALIGNED

**下游影响**：
- ① 是**行为契约变更**：任何**裸调**（无 `--base`）的既有集成方现在会 FAIL。对使用者项目：`agate/UPGRADING.md:353/369` 的两份等价 CI 示例在 pr/push 事件显式传 base，不受影响；但非 pr/push 事件（如 schedule）会由「静默推断」变 FAIL。
- ② 的 workflow 补充块在 **push+SKIP** 时使 step **exit 2**（新假红，gate-backstop job 无 `continue-on-error`）——见重点结论 1。

**文档传播（CHANGELOG？）**：
- `CHANGELOG.md` `[Unreleased]`（`:12-31`）**无本改动条目**。
- `agate/UPGRADING.md` **无本改动的版本节**（`:279` v0.80.1 节仅记 PR#409 协议根修复）。
- `agate/platform-notes.md:344` 未同步（见 A1/A2）。

**结论**：**MISALIGNED**。
**建议**：`CHANGELOG.md [Unreleased]` 补「`agate-ci-verify --base` 必填 + PR 双口径」条目（含 task/RM 关联）；评估是否需在 `UPGRADING.md` 增加「使用者影响」段（裸调者行为变更）；修 `platform-notes.md:344`。

---

### A6: 锚点表覆盖 — ALIGNED

- 本改动是**既有函数内部语义修正**（`--base` 必填 + workflow 双口径），未引入新协议规则/字段/BDD 编号，CHECK 9 锚点表无需更新。
- 实跑 `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**，CHECK 9 PASS。
- CHECK 10 唯一 WARNING 来自 `CHANGELOG.md:99`（历史叙事引用退役名 `ci-gate-backstop.py`，冻结文件），**非本改动引入**（`--show-frozen-warnings` 确认）。

**结论**：**ALIGNED**。

---

### A7: 设计原则一致性 — ALIGNED

逐条查 `agate/adr.md`：

- **ADR-014（判据单一权威源，`:533`）**：本次把「回放基准」的解析**收敛为单点**——主流程算好 `base` 后传入 `_resolve_protocol`（`:541`），脚本不再自行从 `HEAD/origin` 推断第二份基准。**方向一致**（消除「同一输入两处解析」的分叉源）。
- **ADR-015（实质/非实质；让错误不可能/可见/要求人做对，`:589`）**：删除静默推断属**手段①「让错误不可能」**（错误路径结构上不存在）；`--base` 必填后本地彩排须显式给值属**手段③**，但仅限开发者本地、代价低，可接受。设计意图与 ADR-015 一致。
- **ADR-002（可判定性）**：`--base` 必填是可机械判定的（缺参 → FAIL）。

**附带观察（非 ADR 违反，交人工留意）**：workflow 注释 `:320-321` 声称「两条都跑后『PR required 绿 ⇔ 合并后 main 绿』对同一组提交成立」——但同一文件 `:19-22` 明确 `gate-backstop` **已移出 required**。该注释的等价性声称在 gate-backstop 重新纳入 required 前并不成立。属措辞，不阻断。

**结论**：**ALIGNED**。

---

### A8: 声称-命令绑定 — MISALIGNED

| 声称（来源） | 产出它的命令 | 结论 |
|---|---|---|
| 「缺 `--base` 即 FAIL，不得从 HEAD/origin 推断」（`agate-ci-verify.py:487-491`；`CHANGELOG` 未记） | 有提交仓库中 `python3 agate/scripts/agate-ci-verify.py`（无 `--base`）→ exit 1 + `FAIL: --base 必填` | ✅ 成立（由 `test_m1_base_required_no_inference` 锁定） |
| 「本地彩排请显式给 `--base`……**（见 AGENTS.md）**」（`agate-ci-verify.py:490`） | `grep -n "ci-verify\|彩排\|agate-ci" AGENTS.md` → **0 命中** | ❌ **无据**（AGENTS.md 无该命令）→ 应删除该指针或补 AGENTS.md |
| 「PR 两条口径都跑后『PR required 绿 ⇔ 合并后 main 绿』」（`protocol-tests.yml:320-321`） | 无法给出命令；且 `:19-22` 自述 gate-backstop 非 required | ⚠️ 不可复核（措辞过度） |
| 「新增用例覆盖『有提交 + 无 `--base` → FAIL』」（`test_agate_ci_verify.py:308-326` docstring） | `pytest ...::test_m1_base_required_no_inference` → passed | ✅ 成立 |

**结论**：**MISALIGNED**（第 2 条 `（见 AGENTS.md）` 为无据声称，须删除或补文档）。
**建议**：按角色规则「无法给出命令的声称应删除」——删 `agate-ci-verify.py:490` 的 `（见 AGENTS.md）`，或先在 AGENTS.md 落地该彩排命令。

---

## 五项重点核查结论

### 1. workflow shell 正确性（风险面 #1）— **发现新缺陷**

- `|| rc=$?` / `if [ "$rc2" -ne 0 ]` / `exit "$rc"` 在 `-e` 下**写法正确**：`||` 列表保护左值不被 `-e` 中断，`$?` 取值正确（=`rc` 捕获管道退出码）；`extra_args=""` 已初始化，`[ -n "$extra_args" ]` 安全。✅
- `grep -q 'SKIP:' f1 f2` 双文件**合法**：`-q` 使 grep 在「一文件命中、另一文件缺失」时仍返回 0（实测），故 `if` 会正确进入。✅
- **但内层 `grep -A 3 'SKIP:' f1 f2 2>/dev/null | head`（无 `-q`）不安全**：push 事件下 `extra_args` 为空 ⇒ `/tmp/ci-verify-push.log` **从不创建**；此时若 `ci-verify.log` 含 `SKIP:`，内层 grep 因**文件缺失返回 exit 2** → `set -o pipefail`（`:312`）使管道退出码 = 2 → GitHub 默认 `bash -e` 下**整个 step 以 exit 2 中断**，永远走不到 `exit "$rc"`。
- **实测复现**（一次性副本，`bash -e` + `set -o pipefail`，模拟 push 口径 rc=0 + SKIP）：
  ```
  STEP EXIT=2 (expect 0 if no bug)
  ```
  对照组：单文件（改动前的 `/tmp/ci-verify.log`）无此问题；双文件且都命中/都存在也无此问题。
- **后果**：**push 事件 + 回放 SKIP**（很常见：改动不含任务目录的 push，如 docs/脚本/协议改动）→ `gate-backstop` step **假红**（exit 2）。job 无 `continue-on-error` ⇒ job 红。
- **建议修法**：给内层 grep 加 `-q` 不适用（要输出上下文）；改为对**存在的**文件分别 grep，或 `grep -h -A3 'SKIP:' /tmp/ci-verify.log 2>/dev/null; grep -h -A3 'SKIP:' /tmp/ci-verify-push.log 2>/dev/null`，或先 `touch` 两个日志文件，或在块内 `|| true` 兜底。

### 2. `--base` 必填后的既有调用面（风险面 #2）
逐一 grep 核实（见 A3b 表）：
- **硬矛盾**：`agate/platform-notes.md:344`（称无参可用 + 按默认分支推断）。
- **会失败**：`docs/design-notes/repro-tag0050.sh:113-114,157-161`（裸调，冻结设计复现件）。
- **无据引用**：`agate-ci-verify.py:490` 的 `（见 AGENTS.md）`——AGENTS.md 无对应内容。
- **安全**：`.github/workflows/release.yml` 无调用；`UPGRADING.md:353/369` 示例在 pr/push 显式传 base。
- **碰巧安全**：`test_bdd_16_...skip...`（空仓库）、`test_check_gate.py:3619`（非 git 仓库）均因更早的 SKIP 分支返回。

### 3. 测试充分性（风险面 #3）
- `test_m1_base_required_no_inference` **真覆盖**目标分支（有提交 + 无 `--base` → FAIL）。✅
- `test_bdd_16_ci_verify_skip_declared_with_reason` **碰巧通过**：走「无法解析 HEAD」分支（`git_repo` 无提交），非其 docstring 声称的「有提交的非 agate 项目」。断言仍成立但守护力为零。⚠️
- workflow shell 逻辑**零测试覆盖**，exit-2 缺陷无判据守护。❌

### 4. ② 是否引入新的假绿（风险面 #4）
- **聚合正确，无新假绿**：`rc` 初值 0；第一条 FAIL→`rc`≠0；第二条 FAIL→`rc=rc2`（非零）；任一 FAIL 最终 `exit "$rc"`≠0。一条 FAIL 一条 PASS → 最终 FAIL。✅
- **SKIP 判定覆盖两个日志**：`grep -q 'SKIP:' /tmp/ci-verify.log /tmp/ci-verify-push.log` 覆盖两者（当 push 日志存在时）。✅（注意：即使一条 PASS 一条 SKIP，也照发 `::warning`——偏保守，可接受。）
- **但引入了新的假红**（push+SKIP → exit 2，见重点结论 1），非假绿。❗

### 5. ① 是否削弱本地可用性 + 文档同步（风险面 #5）
- **是**：删除了缺省推断，本地彩排必须显式 `--base "$(git merge-base HEAD origin/<默认分支>)"`（脚本 `:11-12`）。
- **文档未同步**：`AGENTS.md` **无**该彩排命令（`grep` 0 命中），而脚本 `:490` 已引用它；`agate/platform-notes.md:344` 未改且与脚本矛盾。⇒ 用户/开发者按文档操作会直接撞 FAIL 且无处查命令。❌

---

## 结论与放行建议

| 结论 | 项 |
|---|---|
| ALIGNED | A6、A7 |
| MISALIGNED | A1、A2、A3、A4、A5、A8 |

**不可 commit（存在 MISALIGNED）**。修复方向（按优先级）：

1. **[BLOCKER]** 修 workflow 内层 `grep -A 3` 双文件缺陷——push+SKIP 会 exit 2 假红（重点结论 1）。
2. **[必修]** 修 `agate/platform-notes.md:344`（删除「无参数可用 / 按默认分支推断」表述）。
3. **[必修]** 处理 `agate-ci-verify.py:490` 的 `（见 AGENTS.md）`：删除指针，或先在 `AGENTS.md` 落地显式彩排命令。
4. **[必修]** `CHANGELOG.md [Unreleased]` 补本改动条目；评估 `agate/UPGRADING.md` 是否加「使用者影响」段。
5. **[建议]** `agate/scripts/README.md:108` 补「`--base` 必填」；把 `test_bdd_16_...skip...` 改为真建含提交的非 agate 仓库；为 workflow shell 逻辑补可执行判据。
6. **[交人工]** `docs/design-notes/repro-tag0050.sh`（冻结复现件）是否回改。

> **注**：本报告的 exit-2 结论为**在一次性副本上的实验复现**（未在真实仓库运行写操作）；全量 pytest 与 consistency 均为只读运行，跑前/跑后 `git status --porcelain` 一致。
