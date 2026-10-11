---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: "hotfix DEBT0074（commit 7d3cdeb7）——发布门 `_non_success_names` 由逐条判 `conclusion != success` 改为按检查名归组、只看已完成结论（无已完成结论=missing/queued/in_progress → 非 success；已完成含非 success → 非 success），使 tag push 并发重跑的新 run 不再致假失败；同步脚本 header / 测试头 / workflow 注释三处自述，补 3 条用例；retry 1 补 CHANGELOG `[Unreleased]` 条目 + DEBT0074 关单"
files_changed:
  - agate/scripts/agate-release.py
  - agate/tests/unit/test_release_gate.py
  - .github/workflows/release.yml
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
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
| A5 | 下游影响 + 文档传播 | ALIGNED（retry 0 = MISALIGNED → retry 1 已闭合，见「增量复审」节） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（逐条附命令；见下） |

> **评审轮次**：retry 0（未提交 diff）→ `needs-revision`（1 项 A5：缺 CHANGELOG 条目与 DEBT0074 关单件）；**retry 1（commit `7d3cdeb7`，已并入 `main` 之 Merge `47901872`）A5 已闭合 → 本报告终态 `approved`。**

**MISALIGNED 计数：0（retry 1，终态）。** 结论：`approved`。

**一句话**：核心语义改动**窄且保守**——独立对抗探针（函数级 + CLI 端到端）**未发现任何可把真实失败掩盖成通过的场景**（新旧实现唯一行为差 = 同名「已完成 success + 未完成新 run」⇒ **通过集 ⊆ 旧通过集**）；retry 0 唯一问题（CHANGELOG 条目 + DEBT0074 关单未落盘）在 retry 1 已**如实、完整**补齐，**关单裁决 = 可接受**（依据见「增量复审」节）。

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

**结论**：新旧实现的**唯一行为差**就是 F / H（同名的「已完成 success + 尚未完成的新一轮」）⇒ 新口径**通过集 ⊆ 旧通过集**，**只朝「容忍同 SHA 并发新 run」这一个方向放宽**，未越界。理由链：check-runs 按提交 SHA 查询，同 SHA 上的新 run 是**同一代码**的重跑；同名的历史 success 即该 SHA 曾通过该检查 ⇒ 不再被后续 in-flight 覆盖，属可辩护的语义收敛。

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
- **A7 / ADR-014 判据单源**：本改动是**判定策略**收敛，不引入任何「手抄副本」数据；`release.preset` 的 schema 单源路径未动 ⇒ **ADR-014 判据单源仍守住**。`adr.md:692`「机械发布门（可注入命令、fail-closed）」粗口径仍成立，**不需新 ADR**（新口径是 fail-closed 内的语义细化，非新增架构决策）。
- **A5**：retry 0 判 MISALIGNED（见下节历史），retry 1 已闭合。

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

## A5：下游影响 + 文档传播 — ALIGNED（retry 0 = MISALIGNED，retry 1 已闭合）

**retry 0 的发现（历史，已被 retry 1 处置）**：本改动是**发布门 CI 判定口径的协议语义变更**，但当时：
1. `CHANGELOG.md` 的 `[Unreleased]` **为空**，未登记 DEBT0074——违反本审查角色的反向传播判据「`CHANGELOG.md` 未更新 + 协议语义变更 = A5 下游影响不完整」；下游后果：发布说明由 `agate-release.py notes` **从 CHANGELOG 提取** ⇒ 缺条目则该修复不进下一版 Release notes。
2. 既有模板佐证：`git show --stat cd0ffd6e`（DEBT0072 收口）= `CHANGELOG.md` + `tech-debt.md` + 脚本 + test + 两份评审报告 ⇒ 债务收口 hotfix 的既有做法**含** CHANGELOG 条目与 debt 关单。
3. `tech-debt.md` 的 DEBT0074 仍为 `status: open`、无 `closure_note`（其 `closure_criteria` 第二条已满足，第一条「tag push 一次跑通」待复验）。

**retry 1 处置与核验**：见「增量复审（retry 1）」节——CHANGELOG 条目与关单四件套**均已落地且如实**（无过度声称），A5 **闭合 → ALIGNED**。

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
| CHANGELOG `[Unreleased]` 缺 DEBT0074（retry 0 时） | `grep -n 'DEBT007[34]' CHANGELOG.md`（无命中）＋ `sed -n '11,13p'` | 当时为空 ✓（retry 1 已补） |

---

## 增量复审（retry 1，commit `7d3cdeb7`）——A5 处置 + 关单裁决

审查对象 = `git show 7d3cdeb7`（4 文件实现/文档 + `CHANGELOG.md`(12 行) + `tech-debt.md`(24 行) + 本报告两份）。
核心实现已在 retry 0 核实（**未重核**，结论复用）：**未发现任何可掩盖真实失败的场景**；SEC-01/02/07 与 ADR-014 未动。

### A5-a：CHANGELOG `[Unreleased]` 条目 —— **落地且如实**（无过度声称）

- `CHANGELOG.md:13-23` 新增 `### 修复` 条目，机制 / run 号（38141030366 假失败、38141340966 绕过）/ 修法 / 「SEC-01/02/07 未改动」限定齐备。
- **A8 过度声称核**（逐句）：
  - 「v0.82.0 首发实证：Release run `38141030366` 失败并报 6 项 required 非 success……绕过方式 `workflow_dispatch` 二次触发 `38141340966` 成功」= 转述 `tech-debt.md` DEBT0074 原始 evidence（登记提交 `f3dad13e`），非新声称，无夸大。
  - 「修复……已完成结论全 success ⇒ 通过（**并发重跑不再假失败**）」= 对新实现**逻辑**的描述（`agate-release.py:472-479`），措辞为「不再假失败」而**非**「已线上验证」⇒ **未见把机制层写成线上验证的过度声称**。
  - 「**不依赖时间戳**」「SEC-01/02/07 均未改动」= retry 0 已逐条实测为真（实现只按 `conclusion is not None` 归组；`git diff -U0` 仅 2 hunk）。
- 机制旁证：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **rc=0（0 ERROR）**，CHECK 7（badge↔CHANGELOG）/CHECK 13（CHANGELOG↔UPGRADING）均 **PASS**；`python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **rc=0**。释义：`[Unreleased]` 条目未破坏一致性。

### A5-b：DEBT0074 关单四件套 —— **齐且如实**

`agate-workspace/debt/tech-debt.md`（`7d3cdeb7` diff）：

| 件 | 内容 | 核 |
|---|---|---|
| `status` | `open → closed` | ✓ |
| `closed_at` | `2026-10-11`（`agate-debt-check.py:158-173` 对 closed 条目的**机械**要求） | ✓ |
| `task_id` | `hotfix-debt0074-gate-concurrent-runs` | ✓ |
| evidence 引用 task_id | 新增 evidence#1（`agate/scripts/agate-release.py`）note 内含该 task_id；机械判据为「evidence **序列化文本**含 task_id」（`agate-debt-check.py:162-165`）⇒ 满足（注：新增 evidence#2 用「同批次」指代、未含字面量，属**宽松表述**但不违规） | ✓ |
| `closure_note` | 见下 | ✓ |

- 台账数字复核：`grep -c '^## DEBT'` = 74；`grep -c '^status: open'` = 1，唯一 open = DEBT0073 ⇒ 声称「**74 条 / open 1（仅剩 DEBT0073）**」**属实**（`awk` 提取 open id 仅 DEBT0073）。
- `closure_note` 的「`protocol-tests.yml` 的『不改为 push 只限 main』既定口径未动（避免 PR #222 自引用陷阱）」**属实**：`.github/workflows/protocol-tests.yml:34-37` 原文记载「改了 `on:` 触发器的 PR，GitHub 不再运行该 workflow 自身（自引用，PR #222 实证零 run）」。

### 关单裁决（主 Agent 请裁项）——**可接受 → `approved`**

**事实**：`closure_criteria` 第二条（判别力用例）**已满足**（3 条用例 + 先红后绿，retry 0 已验）；第一条（tag push 一次跑通 **或** 明示只支持 `workflow_dispatch`）**仅达机制层**——真机 tag-push 复验因 v0.82.0 tag 已发布/Release 已存在而**客观不可重放**（重跑必在 `Publish` 步失败；且对已发布 tag 做不可逆操作须用户授权，按 `AGENTS.md` 应改出补丁版本）；`closure_note` **如实登记**该遗留。

**裁决依据（为何可接受，非掩盖）**：

1. **遗留被如实披露**：`closure_note` 明写「本批以单测覆盖该场景为准」+ 复验时点，属**如实登记**，非掩盖——与「把机制层写成线上验证」正相反。
2. **第一条的实质意图已由机制层满足**：该缺陷观测到的**唯一**成因 = 门逐条判把 in-flight `None` 当失败；新口径移除该成因（retry 0 探针证明「通过集 ⊆ 旧集，仅放宽同 SHA 同名『已完成 success + 未完成新 run』」）。故「tag push 触发发布」在**分支 CI 已完成**（RUNBOOK 要求 `main CI 绿 → 打 tag`）前提下**不再必然失败**。
3. **残留风险有界、且自动复验**：门为 **fail-closed**——若修复仍不足，下次 tag-push 会**响亮失败**（新 run 号落 CI），无「静默放行」路径；且该复验**由下次发版自动触发**，不依赖有人记得去跑。
4. **不可逆约束是客观的**，非规避：删/重推已发布 tag 属禁用的不可逆外部动作。

**非阻断建议**（不改判）：为免「只在已关债务里留痕」被遗忘，可在下次发版清单或一条 RM 加一句「v0.83.0 发版时确认 tag-push 门通过即视本遗留复验完成」（对齐 `AGENTS.md` RM-AG0108/DEBT0051 的「给 owner」精神）；本项不阻断本次 `approved`。

### 本轮 A8（声称-命令绑定）

| 声称 | 产出命令 | 结论 |
|---|---|---|
| CHANGELOG 条目已落且不破坏一致性 | `check-protocol-consistency.py --strict-errors-only` | rc=0，CHECK 7/13 PASS ✓ |
| 关单 schema 合法 | `check-debt.py agate-workspace/debt/tech-debt.md` | rc=0 ✓ |
| 74 条 / open 1（仅 DEBT0073） | `grep -c '^## DEBT'`(=74)、`grep -c '^status: open'`(=1)、`awk` open id | 属实 ✓ |
| PR #222「不改为 push 只限 main」口径属实 | `.github/workflows/protocol-tests.yml:34-37` 原文 | 属实 ✓ |
| 提交仅含 4 实现/文档文件 + 报告 | `git show --stat 7d3cdeb7` | 7 文件 ✓ |

---

## 附录：本报告修订说明（记录与事实对齐）

本文件首版（retry 0，未提交工作树）判 `needs-revision`（1 项 A5）。retry 1 增量复审判定 `approved` 的更新曾落于**未提交工作树**，随后在同步分支时被 `git reset --hard` 冲掉（主 Agent 操作失误）；本文件据此**重写**为自洽终态：结论 = `approved`，保留 retry 0 发现作为历史，「增量复审（retry 1）」节完整承载 A5 闭合核验与关单裁决。

## 附：只读纪律自证

- 全程**未写仓**：无 `checkout/stash/restore/reset/add/commit`、无 push、无 tag/Release/workflow 触发、无写类 `gh`；未动 `agate-workspace/tasks/**`。
- 两处探针均在 `/tmp/opencode` 一次性副本，**同一次 bash 调用内**创建→清理（`rm -rf` 后核验不存在）。
- retry 0 后 `git status --porcelain` 仅 3 个被评审文件（＋评审产出 2 份）；retry 1 时改动已提交为 `7d3cdeb7`，本轮仅**只读** `git show` / `check-*.py` / `grep` 复核，未产生除本报告与 `.progress.md` 外的任何改动（工作树内另有他人对 `agate/tests/unit/test_release_gate.py` 的 ruff 修复，**未触碰**）。
