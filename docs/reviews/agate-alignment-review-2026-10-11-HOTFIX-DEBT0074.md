---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: "hotfix DEBT0074——发布门 `_non_success_names` 由逐条判 `conclusion != success` 改为按检查名归组、只看已完成结论（无已完成结论=missing/queued/in_progress → 非 success；已完成含非 success → 非 success），使 tag push 并发重跑的新 run 不再致假失败；同步脚本 header / 测试头 / workflow 注释三处自述，补 3 条用例"
files_changed:
  - agate/scripts/agate-release.py
  - agate/tests/unit/test_release_gate.py
  - .github/workflows/release.yml
---

# 协议-脚本对齐审查（HOTFIX-DEBT0074）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（附 2 条可选刷新，非阻断） |
| A4 | 测试覆盖 | ALIGNED |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（**经实测无既有用例转红**；无夹具需更新） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（逐条附命令；见下） |

**MISALIGNED 计数：1（A5）。** 结论：`needs-revision`。

**一句话**：核心语义改动**窄且保守**——独立对抗探针（函数级 + CLI 端到端）**未发现任何可把真实失败掩盖成通过的场景**；唯一问题在**文档传播**（CHANGELOG `[Unreleased]` 与 DEBT0074 关单未随本次改动落盘）。

---

## 对 dispatch「重点核」的逐条答复

### 1. 有没有过宽？（最重要）——**没有**，已独立构造对抗用例验证

不依赖主 Agent 的实测：我在 `/tmp/opencode` 一次性副本内，把**当前 `_non_success_names`** 与**旧实现**（`git show HEAD` 的逐条版，未改动工作树）对同一组对抗输入并排比对：

| 对抗输入（同名=同一检查名） | 新实现（空=通过） | 旧实现 | 判定 |
|---|---|---|---|
| A 仅 in-flight、零已完成 | `['pytest (ubuntu-latest)（in_progress）']` | 非空 | 新口径**仍非 0** ✓ fail-closed |
| B 同名「已完成 success + 已完成 failure」 | `['pytest (ubuntu-latest)']` | 非空 | **仍非 0** ✓ 保守 |
| C 同名「已完成 failure + 新 run in-flight」 | `['pytest (ubuntu-latest)']` | 非空 | **仍非 0** ✓ |
| D 另一 required 名 `status: missing`（完成 success + 缺失） | `['shellcheck (ubuntu-latest)（missing）']` | 非空 | **仍非 0** ✓ |
| E 空 runs | `[]` | `[]` | 交 `_cmd_gate:626 if not runs: return 1` 拦截 ✓ |
| **F 同名「已完成 success + 新 run in_progress」** | `[]`（通过） | `['pytest…']` | **唯一放宽点 = DEBT0074 目标场景** |
| **H 同名「已完成 success + queued」** | `[]`（通过） | `['pytest…']` | 同上（唯一另一放宽点） |
| G 混入非 dict | `["'garbage'"]` | 非空 | **仍非 0** ✓ |
| J 同名「success + 已完成 cancelled」 | `['pytest…']` | 非空 | **仍非 0** ✓ |

**结论**：新旧实现的**唯一行为差**就是 F / H（同名的「已完成 success + 尚未完成的新一轮」）。新口径的通过集 ⊆ 旧通过集，**只朝「容忍同 SHA 并发新 run」这一个方向放宽**，未越界。理由链：check-runs 按提交 SHA 查询，同 SHA 上的新 run 是**同一代码**的重跑；同名的历史 success 即该 SHA 曾通过该检查 ⇒ 不再被后续 in-flight 覆盖，属可辩护的语义收敛。

`required` 列表为空 + 零 check-run ⇒ 仍非 0：`_cmd_gate:626-637`（SEC-01）**未在 diff 内**（`git diff -U0` 仅两个 hunk：header 17-19 与 `_non_success_names` 453-479）；CLI 探针 `--ci-cmd [] → rc=1` 实测确认。

### 2. SEC-02 / SEC-07 是否被改变？——**未改变**

`git diff -U0` 全文只触及 header 与 `_non_success_names`。`_gh_check_runs`（可信上报 App 过滤 SEC-02，`agate-release.py:411-433`）与 `--task` 复用 `check-gate.py P8`（SEC-07，`agate-release.py:585-597`）**逐字未动**。

### 3. A2 自述一致性——**逐条相符**

- 脚本 header（17-19）、测试头（23-25）、workflow 注释（85-89）三处口径一致，且与实现逐字相符。
- 主 Agent 的两条自述核实为**属实**：①「不依赖时间戳」——实现只按 `conclusion is not None` 归组，无任何时间/序号比较；②「不因存在 success 而放行」——`elif any(x.get("conclusion") != "success" for x in done)` 对**已完成结论**取「任一非 success 即失败」。
- stderr 文案 `agate-release.py:640-642`「非 success（fail-closed，含 pending/queued/missing）」在新口径下**仍准确**：当某名**只有**未完成结论时，该项会带 `（in_progress/queued/missing）` 被列出 ⇒ 该括注描述的是「非 success 项可能的类别」，非「所有 pending 一律失败」，无陈述错误。

### 4. A4 判别力——**真能锁住新口径**（已独立验红）

- 3 条新用例中 `test_debt0074_concurrent_inflight_rerun_does_not_fail_gate` 是**红-绿判别**：旧实现下 F 场景返回非空 ⇒ 门 rc≠0 ⇒ 该用例 FAIL（我的函数级探针 F 行 DIFFER 与 CLI 探针独立复现）。
- 另两条 (`only_inflight_still_fails_closed` / `completed_failure_among_success_still_fails`) 在**新旧实现下都通过**——它们锁的是「**不得过宽**」（防新口径把 A/B/C 类真实失败放行），属**反向守护**而非红-绿，符合主 Agent 自述，判别价值成立。
- **未改动工作树、未用 `git checkout/stash`**：全程 `/tmp/opencode` 一次性副本，同次 bash 调用内创建→清理。

### 5. A5/A6/A7 与 ADR-014

- **A6 锚点表**：未新增 `agate/scripts/` 文件（diff 仅改既有 `agate-release.py`）⇒ CHECK 9 锚点表**无需更新**，确认。
- **A7 / ADR-014 判据单源**：本改动是**判定策略**收敛，不引入任何「手抄副本」数据；`release.preset` 的 schema 单源路径未动 ⇒ 判据单源仍守住。`adr.md:692`「机械发布门（可注入命令、fail-closed）」粗口径仍成立，**不需新 ADR**（新口径是 fail-closed 内的语义细化，非新增架构决策）。
- **A5**：见下，**MISALIGNED**。

---

## A1：文档→脚本对齐 — ALIGNED

变更涉及的口径（DEBT0074）无独立协议条文，仅由脚本 header / 测试头 / workflow 注释自述承载；三处均已同步，与 `_non_success_names` 实现逐字相符。**ALIGNED。**

## A2：脚本→文档对齐 — ALIGNED

（见「重点核 3」）**ALIGNED。**

## A3：一致性连锁 + 反向传播 — ALIGNED（附 2 条可选刷新）

- **A3a 连锁**：三处自述已同步；无其它协议条文描述旧「逐条」口径（`grep` 全仓确认，除本改动三处外无命中）。
- **A3b 反向传播**（应被影响而未列在 diff 的文件，逐一验证）：
  - `agate/scripts/README.md:149`、`agate/tests/README.md:97`：gate 索引行「CI success + consistency 0 ERROR + check-gate.py P8」为**粗口径**，新口径仍是「CI success」（定义细化）⇒ **不算陈述错误**。可选：补 `DEBT0074` 标注以对齐其它债务条目的惯例（非阻断）。
  - `agate/UPGRADING.md:308`、`agate/adr.md:692`：粗口径「CI success / 机械发布门 fail-closed」，**仍真**，且属**已发布版本**的历史条文，**不应回改**。
  - `docs/guides/ci-docs-only-playbook.md`：与本改动无关（只涉 docs/site 快路径识别），无需改；无独立「发布 runbook」文档（发布清单在根 `AGENTS.md`，粗口径仍真）。

## A4：测试覆盖 — ALIGNED

**实跑证据**：`python3 -m pytest agate/tests/unit/test_release_gate.py -q` → **18 passed in 2.13s**（本次审查独立实跑）。判别力另由本报告「重点核 1/4」的函数级 + CLI 对抗探针独立佐证。

## A4b：闭合后既有测试转红 + 夹具更新清单 — ALIGNED

- **经实测无既有用例转红**。重点核 `test_bdd_9_gate_fails_when_ci_not_success`（`pytest…` 仅 in_progress + `consistency` success）：其 `pytest` 名**无任何已完成结论** ⇒ 新口径仍判非 0 ⇒ 该用例仍绿（我的探针 A/C 行佐证）。18 passed 亦覆盖。
- **夹具更新清单：无**（未改 `_OK_RUNS` / `_ci_cmd` / `_rc_cmd` / `_gate` 等既有夹具，新增用例全部复用）。

## A5：下游影响 + 文档传播 — MISALIGNED

**差异**：本改动是**发布门 CI 判定口径的协议语义变更**，但：

1. `CHANGELOG.md` 的 `[Unreleased]`（第 11-12 行）**为空**，未登记 DEBT0074——违反本审查角色的反向传播判据「`CHANGELOG.md` 未更新 + 协议语义变更 = A5 下游影响不完整」。下游后果具体：发布说明由 `agate-release.py notes` **从 CHANGELOG 提取** ⇒ 若缺条目，本次修复不会出现在下一个版本的 Release notes。
2. 既有模板佐证（最近同类 hotfix）：`git show --stat cd0ffd6e`（DEBT0072 收口）= `CHANGELOG.md` + `agate-workspace/debt/tech-debt.md` + 脚本 + test + 两份评审报告 ⇒ 债务收口 hotfix 的既有做法**含** CHANGELOG 条目与 debt 关单。
3. `agate-workspace/debt/tech-debt.md:3213` 的 DEBT0074 仍为 `status: open`，**无** `closure_note`（同类 DEBT0072 收口时同步关单）。其 `closure_criteria` 之一（「有判别力用例覆盖并发进行中 run」）本改动**已满足**，另一条（「tag push 触发发布能一次跑通」）须待下次真实发版验证——故本条是否随本 PR 关单，可判 `NEEDS_HUMAN_REVIEW`；但 CHANGELOG 条目**宜**一并落盘。

**建议方向**：在本次改动内补 `CHANGELOG.md [Unreleased]` 的 `修复` 条目（含 DEBT0074 语义摘要），并按惯例更新 DEBT0074 的 `status`/`closure_note`；若 CHANGELOG 与关单**有意**延后到批次关单提交（批次标签 `hotfix-debt0073-0074-dogfood-findings`），请在 PR 描述一句话说明（留痕不阻断）。二者择一即可闭合。

## A6：锚点表覆盖 — ALIGNED

未新增 `agate/scripts/` 文件 ⇒ CHECK 9 锚点表无需更新。旁证：`test_release_gate.py:350 test_bdd_23_no_new_check_star_script_added` 仍在；`_known_release_presets()` 的 schema 单源未动。

## A7：设计原则一致性 — ALIGNED

相关 ADR：ADR-002（可判定性，发布门只认 exit code）——新口径仍以 exit code 判定；ADR-013/014（gate 生产者无关性 / 判据单源）——不新增复制品、权威源未分叉；`adr.md`「发布门」节（692/700/702）粗口径仍成立。新口径是「机械发布门 fail-closed」**内部**的判定细化，非新增架构决策 ⇒ **无需新 ADR**。

## A8：声称-命令绑定

| 声称 | 产出命令 | 结论 |
|---|---|---|
| 新旧实现仅 F/H 两例行为不同（唯一放宽点） | `/tmp/opencode` 副本内并排跑 `_non_success_names`（当前 vs `git show HEAD` 旧版），11 例对抗输入 | 仅 F/H DIFFER，其余一致 ✓ |
| SEC-01 空 check-run 仍 fail-closed | 同副本 CLI：`gate --sha HEAD --repo <tmp> --ci-cmd <dump []> --consistency-cmd <ok>` | rc=1 ✓ |
| DEBT0074 目标场景放行 | 同上，ci-cmd = `success+inflight` | rc=0 ✓ |
| 已完成 failure 不被 success 掩盖 | 同上，ci-cmd = `success+done failure` | rc=1 ✓ |
| test_release_gate.py 18 passed | `python3 -m pytest agate/tests/unit/test_release_gate.py -q` | 18 passed ✓ |
| diff 仅动 header + `_non_success_names` | `git diff -U0 -- agate/scripts/agate-release.py \| grep '^@@'` | 2 hunk ✓ |
| DEBT0072 收口模板含 CHANGELOG + debt 关单 | `git show --stat cd0ffd6e` | 含 CHANGELOG.md + tech-debt.md ✓ |
| CHANGELOG `[Unreleased]` 缺 DEBT0074 | `grep -n 'DEBT007[34]' CHANGELOG.md`（无命中）＋ `sed -n '11,13p'` | [Unreleased] 空 ✓ |

## 附：只读纪律自证

- 全程**未写仓**：无 `checkout/stash/restore/reset/add/commit`、无 push、无 tag/Release/workflow 触发、无写类 `gh`；未动 `agate-workspace/tasks/**`。
- 两处探针均在 `/tmp/opencode` 一次性副本，**同一次 bash 调用内**创建→清理（`rm -rf` 后核验不存在）。
- 工作树复核：`git status --porcelain` 仍仅 3 个被评审文件（＋本次评审产出的 2 份报告）。
