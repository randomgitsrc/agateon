# TAG0050 设计独立评审 R4

- **评审对象**：R3 之后修订的设计文档（重点是 §2.2 的 `at_phase`、§2.4、§2.7、§2.9），以及 brief、exp、实施评审中同步修改的部分。
- **基线**：agateon `720c97d3`、peekview `4ea7b8f`。
- **方法**：
  - 在副本 `review2/ag` 上挂两个临时 worktree：`proto`，固定在 merge-base `a68d763`；`rwt`，用作回放工作区。
  - **按新版 §2.4 的规格实际回放**：
    1. 回放范围：`rev-list --no-merges <merge-base(a68d763, 720c97d3^2)>..720c97d3^2`；
    2. 对每个提交 C：执行 `checkout -f C && clean -fdx && reset --soft C^1`；
    3. 设置 `AGATE_ROOT=<proto>/agate`，用 `proto` 中的脚本依次运行 `pre-commit-gate.py` 和 `commit-msg-self-gate.py <msg>`。
  - 唯一偏离规格的地方：协议代码里还没有实现 `AGATE_REPLAY`，所以 2h 段的 `--fix` 照常执行。这个修正步骤会在必要时把格式改对，因此 PASS 的结论偏宽一些，FAIL 的结论不受影响。
- **日期**：2026-10-06

---

## 结论：APPROVE WITH CHANGES

**B-R3-1 已闭合，A2 锚 ① 已实测成立。** 剩下 3 个 MAJOR 都只需修改规格，不影响整体结构，改完由协调方核对即可，不必再走一轮完整评审。R3 的两个 MAJOR 已闭合，7 条 MINOR 中 6 条闭合，剩下 1 条见本报告 MINOR 1。

---

## 一、关键验证：A2 锚 ①

### 1. 正向：TAG0042 PR 的 16 个非合并提交

回放协议取 merge-base `a68d763` 处的 `agate/`。

| 提交 | 主题 | 任务目录改动文件数 | pre-commit | commit-msg | 耗时 |
|---|---|---|---|---|---|
| cb52befc | P1 | 8 | 0 | 0 | 1.47s |
| a2b8fb14 | P2 | 9 | 0 | 0 | 1.59s |
| d3ba1c5d | P3 | 15 | 0 | 0 | 1.23s |
| 48091f20 … 33413cf4 | P4 共 7 个提交 | 2–11 | 0 | 0 | 0.13–1.35s |
| d3c33002 | P5 | 7 | 0 | 0 | 1.29s |
| 36c808b3 | P6 | 23 | 0 | 0 | 1.64s |
| b884ac90 | P6.5 | 10 | 0 | 0 | 0.14s |
| 9bed740b | P7 | 4 | 0 | 0 | 1.89s |
| **33e4598c** | P8（R3 中用 HEAD 协议回放时 rc=1） | 5 | **0** | 0 | 1.70s |
| 4b0e33bb | READY | 5 | 0 | 0 | 0.42s |

- 16 个提交全部为 0，单个提交 0.13–1.89 秒，合计约 15 秒。E4 的初值可以更新为这组数据。
- **push 口径**：`rev-list --no-merges a68d763..720c97d3` 的结果与上面的 16 个提交相同，合并提交被跳过，所以同样全部 PASS。

### 2. 负向控制

都是在副本上用 `--no-verify` 构造的提交，再按同样的方法回放。

| 构造 | 回放 rc | 说明 |
|---|---|---|
| P6 提交（暂存了 `.state.yaml`）中追加 `- [PROD_TOUCHED] …` | **1** | `GATE: [PROD_TOUCHED] … commit 中止` |
| P6 提交中删掉 `P6-evidence/` | **1** | `GATE P6-EVIDENCE: 目录不存在或为空` |
| P6 提交中把 BDD-05 改成 FAIL | 0 | 这是 F1-A 在 legacy 任务上的已知缺口：该证据还被 BDD-06、BDD-20 引用，所以 provenance 也拦不住。属于批 D 的范围，不是回放的缺陷 |
| **在 READY 之后追加一个只改 `P8-release.md` 的提交，内容为 `- [PROD_TOUCHED] x`** | **0** | 见 **M-R4-1** |

结论：
- 新的回放方法能**如实复现 hook 的判定**，A2 锚 ① 成立；
- R3 中的协议版本、合并提交、删除和改名、PR 范围四类问题都已解决；
- 但"回放的强度"就等于"hook 的强度"，这一点设计没有写明，见 M-R4-1。

---

## 二、R3 闭环表

| R3 项 | 判定 | 说明 |
|---|---|---|
| B-R3-1 ① 协议版本 | **CLOSED** | 优先级为 `.agate-version`、merge-base 处的 `agate/`、否则 FAIL。实测见上（33e4598c 由 rc=1 变为 rc=0）。残留问题见 M-R4-2 |
| B-R3-1 ② 合并与聚合 | **CLOSED** | `--no-merges`；squash 仓库的 push 只做账本检查 |
| B-R3-1 ③ 删除与改名 | **CLOSED** | 回放方法改为 `checkout -f` 加 `reset --soft`，R3 中已实测会出现 D 和 R100 |
| B-R3-1 ④ PR 范围 | **CLOSED** | 范围改为 `merge-base(base.sha, head.sha)..head.sha` |
| B-R3-1 ⑤ 等级基准 | **CLOSED** | 改以 merge-base 处的 LEVELS 为准 |
| M-R3-1 `enforced_at` | **CLOSED** | 新增 `test` 字段，并以 mutation 抽样做负向控制；A4-③ 已写入 |
| M-R3-2 commit-msg | **CLOSED** | 已纳入回放（A2-③），实测 16/16 rc=0 |
| R3 MINOR 1–7 | 6 条 CLOSED，1 条 PARTIAL | 2h.1d 同时前移（§2.7 已写，但 §11 中仍只写了 2h.1c）；status 规则；`--existing` 三条件；跳过 `--fix`；brief 已同步（11 项、30 个脚本、B 依赖 A1）；实施评审行号改为 278-315。**PARTIAL** 的是 status：§2.7 写的是"写了即 ERROR"，A3-④ 写的是"手写的值不被采信"，两处说法不一致，见 MINOR 1 |

---

## 三、新发现

### MAJOR

#### M-R4-1：回放的强度就是 hook 的强度；hook 只处理暂存了 `.state.yaml` 的任务，而设计没有说明这一点

- `pre-commit-gate.py` 的主循环（`:227-232`）只遍历**被暂存的 `.state.yaml`**。gate、PROD_TOUCHED 扫描、provenance、judge，全都在这个循环里。
- 实测：在 READY 之后的提交中，只修改 `P8-release.md`，追加 `- [PROD_TOUCHED] x`，然后用 `--no-verify` 提交。回放结果为 **rc=0**。真实的 hook 在同样的状态下也会放行，所以这不是回放失真，而是 **hook 本身的缺口**。
- 这对设计有两个影响：
  1. **A2 锚 ②** 的"`--no-verify` 提交一个会被 gate 拦下的改动 → FAIL"，只有在那个提交暂存了 `.state.yaml` 时才成立。§2.4 中"中途用 `--no-verify` 跳过的每一个提交都会被重新判定"的说法过强。不改 phase 的产出提交，在本地和 CI 都不经过 gate。
  2. **批 C（生产接触）**：§4 没有说明 `prod_touched` 检查和 T4 扫描是否只在这个循环里执行。如果是，"安全门"对不改 phase 的提交依旧无效。F4 已经实测过，只要不暂存 `.state.yaml`，粗体以外的普通写法也不会被拦。
- **修改建议**：
  - §2.4 写明"回放强度等于 hook 强度"。
  - §4 规定：PROD_TOUCHED 扫描和 `prod_touched` 字段检查，对**任何有暂存文件的任务目录**都执行，phase 取 HEAD 版本。可以和 §2.3 新增的"每次提交都运行"那一步放在一起。
  - 对**非 legacy** 任务，如果暂存了已提交阶段的产出、却没有改 phase，就按 HEAD 中的 phase 重跑 gate。legacy 任务保持现状。
  - A2 锚 ② 写明"该提交暂存了 `.state.yaml`"，另外为批 C 增加一条锚：不改 phase 的提交出现 PROD_TOUCHED → 中止。

#### M-R4-2：`.agate-version` 优先级 ① 没有规定从哪个提交读取，也没有约束版本单调，PR 可以借降级削弱回放

- §2.4 只写了"项目 `.agate-version` 固定的版本"，没有说明从哪里读：merge-base、C 本身，还是 HEAD。
  - **如果从 C 或 HEAD 读**：PR 可以把版本固定到一个更早的版本，例如还没有等级机制的 v0.79.0，回放随之退回旧规则。这正是 agateon 为什么选 merge-base 的理由，而 ① 没有沿用。
  - **如果从 merge-base 读**：PR 中途正常升级协议版本时，升级之后的提交是用新版 hook 做的，用旧版回放可能误报。卡片哈希这类判定，R3 已经实测会因版本不同而结果不同。
- **修改建议**：
  - 逐提交读取 **C 树中的 `.agate-version`**，与开发者本地 hook 的口径一致；
  - 同时要求它 **≥ merge-base 处的版本**（单调不降），降级即判 FAIL；
  - 版本变化的提交本身，要求带 SELF-GATE 痕迹，或者作为人工评审项。
  - §13 建议 agateon 也写 `.agate-version`。如果采纳，② 的意义就只剩下兜底，应写明"② 只在 agateon 没有固定版本时使用"，并说明它与开发者本机稳定版之间可能存在差异（merge-base 上可能有未发版的卡片改动）。

#### M-R4-3：`at_phase` 的语义对跨阶段判据、多次升级、schema 收紧都不自洽

§2.2 规定"归属于 `at_phase` 之前阶段的要求项不追溯"，`requirement_active(task, name, phase)` 只比较"要求项所属阶段"。这在以下三种情况下行不通：

1. **跨阶段判据**：很多判据属于后面的阶段，但输入来自前面的阶段。
   - D1（P6）要求 `results` 的 BDD 集合等于 P1 中 `#### BDD-N:` 的集合；
   - E 批（P7）要求 `design_gap_reviews` 等于 P4 中 `design_gaps` 的聚合；
   - `reviewed_bdds` 和 `scope_resolved` 也属于这一类。
   - 以在 P7 迁入为例：P4 的设计缺口是 legacy 散文，结构化聚合结果为空，P7 的配对判据**空集对空集，直接通过**，真实存在的缺口被静默丢弃。P4 的 T1 绊线也因为"P4 < at_phase"而不生效。这与 §3.6"静默丢失"要防的情况正好相反。
2. **多次升级**：每条 `task_upgraded` 都有自己的 `at_phase`，但 `requirement_active` 没有说明应当用哪一条。L1 在 P1 创建、L2 在 P4 升级、L3 在 P6 升级时，某个属于 P5 的 L3 要求项到底生不生效，规格里推不出来。
3. **schema 收紧**：某个 P6 字段在 L2 中被收紧。在 P7 升级到 L2 的任务，它的 P6-acceptance 按哪一级的 schema 校验？"要求项是否生效"只是一个布尔值，表达不了"同一字段在不同阶段用不同等级的 schema"。

**修改建议**：把 `at_phase` 改写成"**按阶段确定的生效等级**"：
- `level_for(task, phase)` 等于所有满足 `at_phase ≤ phase` 的创建、迁入、升级事件中，最大的那个等级；如果没有这样的事件，就是 legacy。
- 每个产出文件按其所属阶段的生效等级，选用对应的快照来校验。
- **跨阶段判据**：属于消费阶段的判据，读取生产阶段的产出时，按生产阶段的生效等级选择读取器。生产阶段如果是 legacy，就用 legacy 读取器，例如用正文正则提取 DG，并以 WARNING 提示，不能当作空集。
- 回退之后在 `at_phase` 之前重做的阶段，仍然按原等级判定，需要写明。
- A1 增加以下验收锚：
  - 在 P7 迁入、P4 有散文缺口 → P7 配对按 legacy 读取，不能为空集；
  - 两次升级的组合用例；
  - 收紧后的 schema 只作用于 `at_phase` 及之后的产出。

### MINOR

1. **status 的处理两处说法不一致**：§2.7 写"写了即 ERROR"，A3 锚 ④ 写"手写的值不被采信"。应统一为前者，并把 A3-④ 改为"写了 status → ERROR"。
2. **§11 中 pre-commit 一行**仍然只写"把 2h.1c 移到 2g 之前"，应与 §2.7 一致，改为"2h.1c 与 2h.1d 一起前移"。
3. **`AGATE_REPLAY=1` 下要跳过的"会改动文件的步骤"没有列全**。除了 2h 的 `--fix`，至少还有 `write_gate_result` 写 `.gate-result.json` 和 `.gate-history.jsonl`、2h.1b/c 的账本追加、2h.1d 和 2h 中的 `git add`。这些副作用都只发生在 worktree 里，不影响判定，但应在 §2.4 列成清单，以免实现时遗漏需要跳过的步骤。
4. **push 口径下"merge-base"指什么没有写**（用于选协议、做等级检查）。建议明确为 `merge-base(before, HEAD)`；`before` 为全零时，取 `merge-base(HEAD, origin/<默认分支>)`。
5. **E4 的初值可以更新**：16 个提交合计约 15 秒，单个提交 0.13–1.89 秒（本轮实测）。

---

## 四、文档一致性抽查

| 项 | 判定 |
|---|---|
| brief 中的"11 项差异"、"约 30 个脚本"、B 依赖 A1 | 已与设计同步 |
| 实施评审中 `check-state-transition.py:278-315` | 已改正 |
| §2.4 中的 `[自述，R3 评审实测]` 标注 | 准确 |
| §2.9 中"28 条" | 与 R3 的数据一致 |
| status 规则（§2.7 与 A3-④） | **不一致**（MINOR 1） |
| 2h.1d 前移（§2.7 与 §11） | **不一致**（MINOR 2） |
| 其余章节 | 与 R3 时相同，未发现新的不一致 |

---

## 五、仓库是否保持干净

```
/home/claude/randomgitsrc/agateon   status --porcelain: 0 行   HEAD 720c97d3
/home/claude/randomgitsrc/peekview  status --porcelain: 0 行   HEAD 4ea7b8f
scratchpad/impl/ag                  status --porcelain: 0 行
```

回放和负向控制都在副本 `review2/ag` 的临时 worktree（`proto`、`rwt`）中完成。负向提交只存在于这个副本里。两个 worktree 已用 `git worktree remove` 删除并 prune。

---

## R4 闭环确认

- **范围**：只核对本次的改动，包括 §2.2 生效等级、§2.3 规则 7、§2.4 第 2–3 点和第 6 点、§2.7、§8 第 12 项、§10 中 A1 锚 ⑧⑨、A2 锚 ②⑥、A3 锚 ④、§11、§13、exp E4，以及 brief 的同步情况。
- **方法**：只读核对。本轮没有新增实测；R4 的回放数据仍然有效。

### 结论：APPROVE WITH CHANGES

3 个 MAJOR 都已闭合，没有引入新的 BLOCKER 或 MAJOR。下面列出的 4 条残留问题都是一两句话的规格修正，在 A1 的 P1/P2 中落实即可，**不需要再评审**。

### 闭环表

| 项 | 判定 | 依据 |
|---|---|---|
| M-R4-1 hook 覆盖面 | **CLOSED**（附残留 1、2） | 新增 §2.3 规则 7，引用的 `pre-commit-gate.py:226-232` 已核对。§2.4 写明"回放强度等于 hook 强度"。A1 新增锚 ⑧，A2 锚 ② 补上了 READY 之后的 PROD_TOUCHED 用例。§8 新增第 12 项，§11 已同步 |
| M-R4-2 `.agate-version` | **CLOSED** | 改为逐提交读取 C 树中的版本，并要求不低于 merge-base 处的版本，降级判 FAIL。A2 锚 ⑥ 覆盖了"降级 FAIL"和"中途升级不误报"两种情况 |
| M-R4-3 `at_phase` | **CLOSED**（附残留 3） | `level(Pk)` 定义清楚；单阶段判据按 `level(Pk)` 取快照；跨阶段判据按被引用产出所在阶段选择读取器，legacy 产出不当空集处理；`requirement_active = snapshot(level(phase)).requires`。多次升级、schema 收紧、P7 迁入这三种情况都能推导出唯一结果。A1 锚 ⑨ 已覆盖 |
| MINOR：status | CLOSED | §2.7 与 A3 锚 ④ 统一为"写了即 ERROR" |
| MINOR：2h.1d | CLOSED | §11 已改为与 2h.1c 一起前移 |
| MINOR：回放副作用 | CLOSED | 不写 `.gate-result` / `.gate-history`；账本仍然在临时 worktree 中写入，理由成立 |
| MINOR：push 口径的 merge-base | CLOSED | 定义为 `merge-base(before, HEAD)` |
| MINOR：E4 与 §13 | CLOSED | 已更新为 R4 的实测数据，并注明"`AGATE_REPLAY` 实现后需要复测" |
| brief 同步 | CLOSED | 允许的差异已改为 12 项；A1 改为"七规则"并加入"按阶段确定生效等级" |

### 残留项（都是 MINOR，实施时落实）

1. **规则 7 中"重跑该阶段的 gate"指哪个阶段有歧义。** 现在写的是"按 HEAD 中的 phase 重跑"。如果 HEAD 是 P7，而本次暂存的是 P6-acceptance，那么跑的是 P7 的 gate，对 P6 的改动依旧不检查。另外 HEAD 为 READY/DONE 时，2g 会直接跳过，READY 之后修改产出也同样不检查。**建议**：按**被暂存产出所属的阶段**重跑对应的 gate，并且这个阶段不得晚于 HEAD 的 phase；READY/DONE 也照此执行。
2. **§8 第 12 项和测试例外清单不一致。**
   - 第 12 项承认"legacy 任务可能出现新的 ERROR"，但"现有测试允许改动"的范围只列了第 7、8、10、11 项，应补上第 12 项。
   - 规则 7 把现行正则扩展到了更多提交上，而这个正则会把否定写法 `- [PROD_TOUCHED]: 无` 当成声明拦下（F4，peekview `T039…/P4-progress.md:21`）。因此 legacy 任务的误拦面会变大。建议在第 12 项的"性质"一栏中注明这一点，并要求 R6 差分统计这一类的新增 ERROR。
3. **采用 `at_phase` 之后回退到更早阶段的情况没有写明。** 例如在 P5 迁入的任务回退到 P3 重做，按现在的定义，`level(P3) = None`，重做的 P3 仍按 legacy 判定。这在定义上是一致的，但属于有意的取舍，建议在 §2.2 用一句话写明。
4. **§11 中"pre-commit-gate.py（回放模式）"一行**只写了"跳过会改动文件的修正步骤"，应与 §2.4 保持一致，补上"不写 `.gate-result.json` 和 `.gate-history.jsonl`"。

### 仓库是否保持干净

本轮只做了读取。`/home/claude/randomgitsrc/agateon` 和 `/home/claude/randomgitsrc/peekview` 的 `git status --porcelain` 都为空，HEAD 分别是 `720c97d3` 和 `4ea7b8f`。

---

## 作者处理记录（残留 4 条 MINOR）

4 条 MINOR 均已在设计中落实，没有留到 A1 的 P1/P2：

1. **规则 7 的重跑阶段**：改为"按被暂存产出所属的阶段"，该阶段不晚于 HEAD 的 phase，READY/DONE 同样适用（§2.3 规则 7、A1 锚 ⑧、§11）。
2. **§8 第 12 项**：注明否定写法会被误拦，R6 单独统计；测试例外清单补入第 12 项。
3. **迁入后回退**：在 §2.2 写明这是"有意的取舍"，并说明可以用 `--upgrade` 补救。
4. **§11 回放模式一行**：补上"不写 `.gate-result.json` 和 `.gate-history.jsonl`"。
