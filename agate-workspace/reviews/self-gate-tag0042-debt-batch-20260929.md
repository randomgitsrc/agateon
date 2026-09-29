---
status: approved
agent: protocol-alignment-review
reviewed_at: 2026-09-29
---
# SELF-GATE 评审：DEBT0048 + DEBT0045 + DEBT0040 批

## 结论

**approved（可提交，但需先完成下述 3 项非阻断整改）**。

**无阻断项**。本批唯一的代码行为变更（DEBT0045）经对抗性核实**核心声称成立**：我构造的 **9 种审计失败输入全部仍为 exit 1**，唯一产生 exit 2 的路径确实只有「缺 agent 字段」这一条协作规范警告。把真失败放行的风险**不成立**。

但有三项**非阻断**问题必须如实登记（其中前两项是本仓高发的「声称有、实际无」）：

1. **DEBT0045 的 closure_criteria 第 2 条未满足，却把债标为 `closed`**——「agate-next 暂停信息含 provenance 的具体原因行」**实测未实现**：真失败（exit 1）时 agate-next 仍只打印「验收异常」，**不转达 provenance 的 stderr 原因**。我端到端复现：缺证据引用 → 输出中**不含**「不存在」「missing-e1」，落盘 `P6-exit2-resolution.md`。本次改动只补了 **exit 2 分支**的告警转达，exit 1 分支一字未动。
2. **DEBT0040 的 closure_criteria 三条中有两条未落实**（详见下文），且新哨兵的自述「真正的全量对比由 P6.5 judge 的 `git status` 复核承担」**在仓库中不存在**（judge.md 无任何 `git status`/`porcelain` 字样）。
3. **新哨兵 `test_t42_ledgers_not_dirtied_by_test_suite` 在 CI 实际配置下会静默失效**——我把一个真实污染账本的测试放进套件、以 CI 口径 `-n auto` 跑 unit 片，**哨兵仍 PASS**（它先于污染者执行）；随后单独跑才转红。即该哨兵**依赖执行顺序**，不能作为 CI 兜底。

另注：评审期间父 Agent **持续在编辑**被评审文件（P3-tdd.md、test_t42_*.py、4 处协议文档、tech-debt.md、CHANGELOG），工作树在我核实过程中发生多次实质变化。本报告以**核实当时的快照**为准，并在文中标注了各文件 md5。

---

## 逐条核实

### DEBT0045（代码行为变更）——**成立**

#### 1. 契约真实存在 ✔

`agate/scripts/README.md:32` 确实写着：

```
| `check-p6-provenance.py` (P2.1/P2.10) | ... | 0=通过, 1=审计失败, 2=WARNING |
```

脚本自身 docstring（第 5–6 行）**独立重述**同一契约：

```
exit 0 = 通过; exit 1 = 审计不通过; exit 2 = WARNING（不阻塞）
```

即**改动者没有编造契约**——两处独立来源一致，且都早于本批改动（`git diff` 未触及 README/脚本）。

#### 2. exit 2 只由「协作规范警告」产生 ✔（**最关键检查点，通过**）

`check-p6-provenance.py`（589 行）中 `sys.exit(2)` **全仓只有 1 处**（第 584 行），且其守卫变量 `warning_found` **只有 2 个赋值点**（第 542、557 行），**两处都是 agent 字段缺失警告**，stderr 文案均为「（协作规范，不阻塞）」。

其余 **19 处 `sys.exit(1)`** 覆盖全部真审计失败：审计 1a 证据引用不存在(313)、1b 证据目录空(322)、1c 证据文件未被引用(336)、审计 2 验收结论预判(397)、审计 3 非数字 field(430)/无标准 BDD(438)/挑验(441)、审计 4 vision 缺引用(472,478,493,505,511)、审计 5 EXIT_CODE 矛盾(528)、审计 6 evidence JSON 不一致(571)、审计 7 复用被阻(581)。另有 `--audit7-only` 分支(243) 与用法错误(251,257)。

**结论：不存在「某种审计失败也走 2」的路径。** 我进一步用**穷尽式实测**验证（见「反例搜索」节）：9 种真失败 → **9 个 exit 1，0 个 exit 2**。

#### 3. 消费方全查 ✔

独立 grep 确认**只有 3 个消费方**，且都只拦 `== 1`：

| 消费方 | 代码 | 判据 |
|---|---|---|
| `agate-next.py::_p6_pass` | L271-278 | 改成 `rc in (0,2)`（本批唯一语义变更） |
| `pre-commit-gate.py:400` | `_run_script_rc("check-p6-provenance.py", [task_dir]) == 1` | **只拦 1** |
| `ci-gate-backstop.py:261` | `if prov_result.returncode == 1:` | **只拦 1** |

**没有任何地方把 2 当失败。** 改动者关于「只有 agate-next 需改」的声称成立。

##### ⚠️ 但发现一处**反向**的文档-实现漂移（本批未处理）

`agate/rules/phases.yaml:109`（**机器可读的权威源**）仍写：

```yaml
- {check: "check-gate.py P6 exit 2 + check-p6-evidence.py / check-p6-provenance.py exit 0"}
```

`agate/WORKFLOW.md:324`（P6 gate 表）同样仍写 `check-p6-provenance.py exit 0`。改动者本轮同步了 4 处文档（state-machine / state-transitions / loop-orchestration / dispatch-protocol），**但这两处最权威的落点被漏掉**——而它们恰是 orchestrator 判定「P6 gate 是什么」的引用面。新加的守护测试 `_DEBT0045_DOCS` 里**也不含** WORKFLOW.md / phases.yaml（`grep -c "WORKFLOW\|phases.yaml"` = 0），所以这个漏洞**不会被任何测试发现**。这属于「修了 4 处、漏了 2 处最该修的」——非阻断，但应在本批内补齐，否则正是本批想消除的那类漂移。

#### 4. 负向对照真有效 ✔（变异测试证明）

我做了**双向变异测试**，确认正/负两条测试都真有牙齿：

| 变异 | 预期 | 实测 |
|---|---|---|
| **A**：`return rc in _P6_PROVENANCE_PASS` → `return rc == 0`（还原旧 bug） | 正向测试转红 | **`test_debt0045_warning_only_still_advances_p6_to_p7` FAILED** ✔ |
| **B**：→ `return rc in (0, 1, 2)`（过度放宽，把真失败也放行） | **负向对照转红** | **`test_debt0045_audit_failure_still_blocks` FAILED** ✔ |
| 还原 | 两条皆绿 | **2 passed** ✔ |

变异 B 尤其重要：它证明 `test_debt0045_audit_failure_still_blocks` **不是恒真的**——如果改动者写成 `rc != 1` 之类，这条测试会立刻抓住。

**并且我自己独立构造了 9 种审计失败**（不只测试里那 1 种），全部**不推进**：

| 注入的失败 | exit | 是否放行 |
|---|---|---|
| PASS 引用不存在的证据文件（审计 1a） | **1** | 否 ✔ |
| 有 PASS 但证据目录为空（审计 1b） | **1** | 否 ✔ |
| 存在未被引用的证据文件（审计 1c 充数） | **1** | 否 ✔ |
| PASS 数(1) < P1 BDD 数(2)（审计 3 挑验） | **1** | 否 ✔ |
| 声明 PASS 但日志 `EXIT_CODE: 1`（审计 5） | **1** | 否 ✔ |
| dispatch-context 含 PASS/FAIL 预判（审计 2） | **1** | 否 ✔ |
| frontmatter pass 非数字（审计 3） | **1** | 否 ✔ |
| P1 无标准 `#### BDD-NN` 格式（审计 3） | **1** | 否 ✔ |
| **审计 1a 失败 + 缺 agent 字段同时存在** | **1** | 否 ✔ |
| （对照）仅缺 agent 字段 | 2 | 是（= 预期） |
| （对照）全合规 | 0 | 是（= 预期） |
| （对照）无 P6-acceptance.md（GATE SKIP） | 0 | 是（= 既有语义，本批未改） |

**最后一行值得单列**：`缺 agent + 真失败同时存在 → exit 1`，说明脚本是**先跑审计、failure 优先 exit**，警告不会「掩盖」真失败。这是 `rc in (0,2)` 安全性的结构性保证。

#### 5. 是否有更保守的修法——**有，但改动者的选择可以接受**

DEBT0045 自己的 `recommendation` ① 写的是**两条路二选一**：

> 「『缺 agent 字段』类协作规范警告**不应改变退出码**（或统一改为 exit 1 并把提示语改为『阻塞』，二者择一，使提示与行为一致）」

改动者选了**第三条路**（既没让 provenance exit 0，也没改成 exit 1，而是让消费方认 2）。评估：

- **不是最小改动**：DEBT0045 建议的「provenance 警告不改退出码（exit 0 + stderr）」只改 1 个脚本，且**同时**满足另两个消费方（pre-commit / CI backstop）的既有 `==1` 语义，无需改文档。改动者所选方案需要**改 4+2 处文档**来消除漂移（且漏了 2 处）——改动面反而更大。
- **但也不是把风险从「卡住」换成「放行真失败」**：已由上述第 2、4 点**实测证伪**——真失败全部仍为 1。
- 改动者所选方案的**优势**：`exit 2 = WARNING` 已是 README 明文契约，消费方按契约消费比「改脚本让 2 永不出现」更符合「既定契约优先」；且保留 2 这个可观测信号（exit 0 + stderr 会丢失退出码层面的区分度）。
- **代价**：contract 里 2 的语义从此有了**两个**消费者解释（agate-next = 通过；另外两个 = 忽略），未来若有人给 2 增加新的产生路径，agate-next 会**静默放行**。我核实的**结构性缓解**是：2 的产生路径被 `warning_found` 这一个变量独占锁死，且注释明确登记了「协作规范用 WARNING、安全审计用 ERROR」的分层原则。

**判断：可接受，非阻断。** 但我建议补一条 `test` 锁死「exit 2 的产生路径 = agent 字段」这一前提（如断言 provenance 源码中 `warning_found = 1` 的赋值点数 == 2），否则将来有人给 warning_found 加第三个赋值点，`rc in (0,2)` 会无声扩大放行面。这是**本批唯一真正值得补的加固**。

### DEBT0048（文档类）——**部分成立**

#### 1. 4 条测试是否真是断言——**是，且有行为验证** ✔

无恒真/空断言：每条都 `assert` 具体子串或 exit code。`test_t42_scan_is_runnable_and_clean_on_repo` **真有牙齿**——我注入一处平台假设后它转红：

```
注入 agate/tests/unit/test_tag0027_b1_agate_next_cli.py:
  # INJECTED PROBE: literal system temp dir /tmp/agate-probe
→ 扫描器 exit 1，报 R4 ...:439
→ test_t42_scan_is_runnable_and_clean_on_repo FAILED ✔
→ 还原后扫描器 exit 0、测试 PASS ✔（md5 复原为 103eb2a4...）
```

（备份放在**仓库内** `.review-scratch/`，未用 `/tmp`，符合本机 per-call tmpfs 约束。）

#### 2. 三处落点一致性 ✔

| 落点 | 脚本名 | 判据 | 修法示例 |
|---|---|---|---|
| `P3-tdd.md:102` | `check-platform-assumptions.py` | **0 命中** | `TMP = "/" + "tmp"` |
| `dispatch-prompt.md` P3 自检 | 同名 | 必须 0 命中 | 同上 |
| `test-designer.md` 交付前自查 | 同名 | 必须 0 命中 | 同上 |

三处判据、脚本名、修法完全一致，指向的脚本**真实存在**且可跑（我实测 exit 0）。`test-designer.md` 第 3 条还把 DEBT0040 的写入隔离一并纳入，与另一条债做了正确交叉引用。✔

#### 3. ⚠️ `{agate_root}` 路径写法与「对任何使用者项目成立」的声称——**声称过头了（部分成立）**

**该条本身写对了**：`P3-tdd.md:102` 用的是 `{agate_root}/scripts/...` 占位符，且第 103 行**显式解释**了为何不用裸 `agate/scripts/`：

> 用 `{agate_root}`（协议根占位符）而非裸 `agate/scripts/`：本卡其余处写 `agate/scripts/...` 是**面向 agateon 自身**的惯例，而本条对**任何使用者项目**都成立

这**正面回应了**「以 agateon 自身为中心写通用协议」的陷阱，是本次改动里质量最高的一处。`{agate_root}` 确由 `agate-resolve.py` 解析，脚本也确实会被安装到用户项目（我验证 `~/.agate/current/agate/scripts/check-platform-assumptions.py` 存在）。

**但「对任何使用者项目成立」不成立**，有两个实测反例：

- **反例 A（扫描器只认特定扩展名）**：`check-platform-assumptions.py:128` 只扫 `.bats/.bash/.sh/.py`。我造了一个**只有 `.test.ts`** 的测试目录（内含 `/tmp` 字面量）→ **exit 0（静默通过）**；同目录塞一个 `.sh` 才 exit 1。**TS/JS 项目（尤其是 Playwright 项目——恰恰是本协议 P3 明确要求写 E2E 用例的场景）跑这条自查会恒绿，是纯噪声。**
- **反例 B（P3 卡的 `<测试目录>` 是占位符，未给解析方式）**：使用者需自行知道测试目录在哪；卡里未提示「无参数时默认扫 `agate/tests/`（即协议自身测试树）」这一误导性默认值——用户项目里若不传参，扫的是**协议自带的 tests/**，与本项目测试无关。

**判断：`{agate_root}` 的写法是正确的，但「对任何使用者项目都成立」这句声称应改为「对 Python/shell 测试项目成立」，并点明扫描器的扩展名覆盖范围。** 非阻断（文档措辞问题），但正是本批要修的那类「声称与实际能力不符」。

（另注：本次改动**未**把该扫描接入 P3 gate 机械判定——`check-gate.py::gate_p3` 仍只查 `P3-test-cases.md` 存在。所以它是**自查项而非 gate**，卡里也未声称已 gate 化，此处**无「声称有实际无」问题**。）

### DEBT0040（哨兵）——**部分成立**

#### 1. 哨兵真能抓到污染 ✔（但**依赖执行顺序**）

注入一条账本变更 → 哨兵转红：

```
注入 agate-workspace/tasks/TAG0021-structured-layer/gate-events.jsonl
→ FAILED: 跑测把已提交的事件账本改脏了（DEBT0040 复发）：
     M agate-workspace/tasks/TAG0021-structured-layer/gate-events.jsonl ✔
→ 还原后 PASS ✔
```

**但**——我按 **CI 实际口径** `-n auto` 跑 unit 片，同时放入一个真实污染账本的测试：

```
python3 -m pytest agate/tests/unit/ -n auto
→ 1 failed (opencode，环境性), 2217 passed
→ 而 agate-workspace/tasks/TAG0021-structured-layer/gate-events.jsonl 确实是 M（脏）
→ 哨兵 test_t42_ledgers_not_dirtied_by_test_suite 却 PASSED ✗
```

原因：`-n auto` 下 xdist 按文件分发给 worker，哨兵**先于**污染者执行 → 采样时账本还干净。**该哨兵在同一进程内既当「污染者」又当「检测者」时必然失效**（自指），在 CI 上只对「上一次运行遗留的污染」有效。这使其作为 CI 兜底的价值**远低于其自述**。

#### 2. CI 是否误报——否 ✔

CI 是干净 checkout，跑测本身不脏账本（我实测全量前后 20 个账本哈希零变化），故哨兵在 CI 上恒绿 → **不误报**。但结合上一点，**不误报的代价是几乎不会报**。

#### 3. 是否等价于关闭 DEBT0040——**不等价**（已修 ≠ 已守护）

- **「已修还是恰好没写」**：我做了**全量前后哈希对比**（这是直接证据，非推理）：

```
全量 pytest agate/tests/ -n auto  →  2425 passed, 2 failed(环境性), 2 skipped
跑前/跑后 20 个 gate-events.jsonl（+ .state.yaml/active-tasks.md 共 21 个已跟踪状态文件）
  md5sum 对比 →  IDENTICAL，零变化 ✔
```

  并确认写账本的测试都走 `tmp_path`（`test_agate_common.py` 的 `append_event` 用例全部 `td = tmp_path / "task"`）。**结论：已是真修（测试走 tmp_path），不是「恰好没写」。** ✔

- **但 closure_criteria 有 2/4 条未落实**（该债仍被标为 `closed`）：

| DEBT0040 closure_criteria | 状态 |
|---|---|
| ① `test-designer.md` **+ `implementer.md`** 含 tmp 隔离条文 | **一半**：`test-designer.md` ✔；`implementer.md` **零改动、零相关字样** ✗ |
| ② 存在回归用例拦截「append_event 指向仓库内账本」的测试形态 | **部分**：新哨兵是「事后 git status」而非「fixture/lint 约束」；且如上所述会静默失效 ✗ |
| ③ CI 有 `git diff --exit-code` 账本兜底步（**或等效机制**），故意污染能被 CI 捕获 | **未落实**：`.github/workflows/` 下**无任何** `git diff --exit-code` / `git status` / 账本检查 ✗ |
| ④ 全量 pytest 全绿 + consistency 0 ERROR | **部分**：consistency **0 ERROR** ✔；pytest 有 **2 个失败**，但均为**环境性**（`opencode` 不在 PATH；`/tmp` 跨设备 link），与本批无关 ✗(环境) |

  第 ③ 条由 closure_note 用「或等效机制」自我豁免了，但**新哨兵不构成等效机制**（顺序依赖）。这是**「声称有、实际无」**在本批的第二次出现。

#### 4. 哨兵只查 `agate-workspace/tasks` + 只认 `gate-events.jsonl`——**范围不足**（有实测反例）

我逐项注入，验证哨兵覆盖：

| 注入对象 | git 是否变脏 | 哨兵是否转红 |
|---|---|---|
| `agate-workspace/tasks/*/gate-events.jsonl` | 是 | **是** ✔ |
| `agate-workspace/tasks/active-tasks.md` | 是（` M`） | **否** ✗（`endswith("gate-events.jsonl")` 过滤掉） |
| `agate-workspace/tasks/*/.state.yaml` | 是（` M`） | **否** ✗ |

- `.gate-result.json` / `.gate-history.jsonl`：**确认未被 git 跟踪**且已在 `.gitignore:2,5`（closure_note 的声称**成立** ✔）。仓库内计数 0，故非风险面。
- **但** `active-tasks.md`（1 个，已提交）与 **42 个 `.state.yaml`（已提交）** 明确可被测试写脏且哨兵查不到。`.state.yaml` 尤其危险——它是**阶段状态机本体**，被测试写脏会直接改变 gate 判定。

**判断：哨兵范围应按 closure_criteria 扩到「所有已提交的状态/账本文件」，而非只认一种文件名。** 当前实现是「窄哨兵 + 无效兜底」的组合，**不足以关闭 DEBT0040 的 ②③ 两条**。

### 通用检查

#### `_log` 只打印第一行非空 stderr——**确实漏警告**（实测）

`agate-next.py:272-277` 的 `break` 只输出第一条。我构造了一个有 **4 条** agent 字段警告的任务目录：

```
exit 2, 4 条非空警告行：
  GATE PROVENANCE: P2-design.md 缺 agent 字段（协作规范，不阻塞）
  GATE PROVENANCE: P3-test-cases.md 缺 agent 字段（协作规范，不阻塞）
  GATE PROVENANCE: P4-implementation.md 缺 agent 字段（协作规范，不阻塞）
  GATE PROVENANCE: P5-verification.md 缺 agent 字段（协作规范，不阻塞）
→ agate-next 只转达第一条 → 另外 3 个缺字段文件对主 Agent 不可见
```

**更值得注意**：`_run_cmd` **合并了 stdout+stderr**（L143），而 provenance 的**审计失败原因全在 stderr**。所以理想做法不是 `break` 取首行，而是**全量转达**（或按 `GATE PROVENANCE` 前缀过滤后逐行输出）。当前实现连「有几条警告」都没告诉主 Agent。

**建议**（非阻断）：去掉 `break`，改为输出全部非空行（或至少输出计数 + 首行），并把同一逻辑用到 **exit 1** 分支——后者正是 DEBT0045 closure_criteria 第 2 条要求而未实现的。

#### 是否有「声称有、实际无」——**有，两处**

1. **DEBT0045 closure_criteria 第 2 条**（「暂停信息含 provenance 具体原因行」）：标 `closed` 但**实测未实现**。我端到端复现 exit 1 真失败，输出为：

```
AGATE NEXT:   gate: GATE P6: 证据目录非空，FAIL=0，NC=0，P6_TOTAL=1。...
AGATE NEXT: P6 真暂停（gate exit 2 ∉ pass_set 且 ≠ 1）：已落盘 P6-exit2-resolution.md...
AGATE NEXT: P6 gate exit 2 ∈ pass_set 但 check-p6-provenance 未过（验收异常）→ 暂停转主 Agent 决策
→ 输出中「不存在」=False，「missing-e1」=False，resolution 落盘 =True
```

  即债的 `impact` 原文「agate-next 只输出『验收异常』而不指出真正原因」**在 exit 1 路径上依然成立**，本批并未修复它（只修了 exit 2 路径）。

2. **新哨兵自述的 P6.5 judge 兜底**（`test_t42_p3_platform_selfcheck.py:75`）：「真正的全量对比由 P6.5 judge 的 `git status` 复核承担」——`agate/assets/review-roles/judge.md` 中**无任何** `git status`/`porcelain`/`污染`/`工作树` 字样；全仓 `judge` 相关的 `git status` 复核**不存在**。该兜底是虚构的。

（另：DEBT0045 closure_note 称「穷尽实测 **5** 种输入」，我实测覆盖 **9** 种真失败 + 3 种对照，结论一致；数字口径偏小但结论无误——不构成问题，仅记录。）

#### 新增测试文件的平台假设——**干净** ✔

```
python3 agate/scripts/check-platform-assumptions.py agate/tests  →  exit 0（全树 0 命中）
新文件 grep 'python3|PATH=|/tmp'  →  none found
```

`test_t42_*.py` 用 `git -C` 子进程 + `agate_root`/`python_exe` fixture，无 `/tmp` 字面量、无裸 `python3`、无硬编码 PATH。**本批自己的新测试没有重犯 DEBT0048 的毛病** ✔。

（一处可选加固：`test_t42_ledgers_not_dirtied_by_test_suite` 直接 `subprocess.run(["git", ...])`，依赖 `git` 在 PATH 上——仓库既有惯例如此（`test_check_mvwu.py`、`test_doc_sweep.py` 同款），**不算新引入的平台假设**。）

---

## 反例搜索

### 重点一：exit 2 的其他产生路径——**不存在**（穷尽核实）

三层证据：

1. **静态**：`sys.exit(2)` 全仓 1 处（L584），守卫 `warning_found` 仅 2 个赋值点（L542/L557），均为 agent 字段警告。
2. **动态**：9 种真失败实测**全为 exit 1**，无一为 2。
3. **组合**：「真失败 + 缺 agent 同时存在」→ exit 1（failure 优先），警告不掩盖失败。
4. **反查消费方**：3 个消费方中 2 个（pre-commit / CI backstop）本就只认 `== 1`，与改动前行为一致，未被本批放宽。

**⇒ 「把真失败放行」的阻断风险，证伪。**

### 重点二：注入平台假设后测试是否红——**是** ✔

注入 `/tmp/agate-probe` 注释 → 扫描器 exit 1（R4）→ `test_t42_scan_is_runnable_and_clean_on_repo` **FAILED** → 还原后 PASS。
**反例（哨兵盲区）**：仅 `.test.ts` 的目录含 `/tmp` → 扫描器 **exit 0**（扩展名不含 TS）。

### 重点三：账本哨兵是否真有效——**有效，但顺序依赖 + 范围过窄**

- 直接注入账本 → 转红 ✔
- CI 口径 `-n auto` 下注入污染测试 → **哨兵 PASS（漏报）** ✗
- `active-tasks.md` / `.state.yaml` 变脏 → **哨兵 PASS（漏报）** ✗

### 重点四：并发编辑

评审期间父 Agent 多次改写被评审文件（P3-tdd.md 13:18、test_t42_*.py 至少 4 次、4 处协议文档、tech-debt.md、CHANGELOG、fixture baseline）。**其中一次我的核实捕捉到真实红灯**（`test_t42_docs_state_provenance_exit_warning_is_nonblocking` 因正则 `check-p6-provenance\.py\`?\s*...` 不匹配 `loop-orchestration.md` 的 `check-p6-provenance exit 0/2`（**无 `.py`**）而 FAILED）——该问题随后被父 Agent 修掉（正则改为 `check-p6-provenance.{0,12}exit 0/2`），我确认**现已 7 passed**。这属于**已在评审窗口内自愈**的问题，登记备查。

---

## 真空通过自检

以下每个被我引用的 exit code / 数字，及其在何种前提下才算证据：

| 我引用的 | 前提 | 若前提不成立会怎样 |
|---|---|---|
| `check-p6-provenance.py` exit 2 仅 1 处 | 以**工作树快照 md5 未变**为前提；我用 `grep -n "sys.exit"` 全量枚举 589 行 | 若脚本在评审期间被改，计数失效——已用静态+动态双重交叉验证 |
| 9 种真失败均 exit 1 | 前提：**我的 fixture 真触发了对应审计**（每次均读 stderr 确认命中了预期分支，如「有 1 条 PASS 引用的证据文件不存在」） | 若 fixture 未命中，会得到 0/2 而非 1——实测输出逐条对上了审计文案，故成立 |
| 变异 B 负向对照转红 | 前提：**变异真的写进了文件**（初版因目标字符串已被变异 A 改掉而 `assert s2!=s` 失败，我当场发现并重做） | 首次尝试确实**假绿过**，已修正——记录在案 |
| 全量 pytest「2425 passed / 2 failed」 | 前提：**2 个失败与本批无关**——已读失败详情（`opencode` 不在 PATH、`/tmp` 跨设备 link），二者均在**本批改动之外**（前者依赖外部 CLI，后者是 tmpfs 挂载语义） | 若其中一个实为本批引入，结论需翻转；逐条读了 traceback，确认无关 |
| 账本哈希「零变化」 | 前提：**对比的是同一组文件**（前后各 21 个已跟踪状态文件，find 同一表达式）且**全量套件真的跑过**（2425 passed 为证） | 若套件被 skip/中断则不是有效证据——exit code 与 passed 计数确认跑完 |
| 哨兵漏报（`-n auto` 下 PASS 但账本脏） | 前提：**同一时刻**账本确为 ` M`——我在同一命令后立即 `git status --porcelain` 独立确认（输出 ` M ...gate-events.jsonl`） | 这是本报告最关键的负面结论，已用「哨兵结果」+「独立 git status」双证据交叉确认 |
| `active-tasks.md` / `.state.yaml` 漏报 | 前提：注入后 **git 确实变脏**——已附 `git status --porcelain` 原始输出为证 | 若未变脏则哨兵 PASS 是正确行为；实测两例均 ` M` |
| WORKFLOW.md / phases.yaml 漏改 | 前提：它们**仍是权威引用面**（正文 P6 gate 表 + `rules/phases.yaml`）且**未在守护清单内**（`grep -c` = 0） | 若它们已在本批被改，则我读了过期内容——已用 md5 与实时 grep 双重确认仍为 `exit 0` |
| 「judge git status 兜底不存在」 | 前提：**judge.md 是判官职责的唯一权威源** | 若兜底定义在别处（如 phase-card），我的 grep 会漏；已扩到全仓 `agate/ --include=*.md/*.py/*.yaml` 搜索，无命中 |
| `{agate_root}` 写法为正 | 前提：`{agate_root}` 是协议既有占位符惯例 | 已 grep 到 P3-tdd.md 同文件它处、P8 卡均用该占位符，成立 |

**未取证的推断（明确标注）**：DEBT0045 建议的「provenance 改 exit 0 + stderr」方案「改动面更小」——我**未实际实现该方案跑测试**，只做了静态改动面计数（1 个脚本 vs 4+2 文档）。若据此决策，应在实现后重跑本报告的全部 9 种失败注入。

---

## 遗留问题 / 建议

按优先级：

### 应在本批内处理（非阻断，但影响「债真的关了吗」）

1. **补 WORKFLOW.md:324 + phases.yaml:109 的 `exit 0` → `exit 0/2`**，并把这两个文件加入 `_DEBT0045_DOCS`。
   *为什么*：本批的全部价值主张是「消除文档-实现漂移」，却把**机器可读的 `phases.yaml`** 和**主 WORKFLOW gate 表**留在了旧表述——这是最该改的两处，且现有守护测试的结构决定了**它永远不会为此报警**。

2. **`_log` 去掉 `break`，并把原因转达复用到 exit 1 分支**。
   *为什么*：这同时修掉两个问题——① 多警告只显示第一条（实测 4 条只出 1 条）；② DEBT0045 closure_criteria 第 2 条（「暂停信息含具体原因」）**当前未实现却被标 closed**。不修则应把该债**重开或降级标注**，而不是标 `closed`。

3. **账本哨兵：扩范围 + 解决顺序依赖**。
   *为什么*：当前只认 `gate-events.jsonl`（漏 `active-tasks.md` + 42 个 `.state.yaml`，均已提交且可被写脏），且在 `-n auto` 下会静默漏报。更稳的形态是**会话级 fixture**（`autouse`，在 `pytest_sessionfinish` 比对 `git status --porcelain` 全仓快照）或**CI 后置步** `git diff --exit-code`——后者正是 DEBT0040 closure_criteria 第 ③ 条的字面要求。

### 建议（加固，可不阻塞提交）

4. **加一条测试锁死「exit 2 的产生路径唯一性」**：断言 `check-p6-provenance.py` 中 `warning_found = 1` 的赋值点数 == 2、`sys.exit(2)` 数 == 1。
   *为什么*：`rc in (0,2)` 的安全性**完全依赖**「2 只由协作规范警告产生」这一前提；该前提目前只由注释和我的本次人工核实守护。一旦有人给 `warning_found` 加第三个赋值点（比如把某个弱审计降级成警告），放行面会无声扩大，而现有测试**全部仍绿**。

5. **修正 DEBT0048 的两处声称过头**：
   - 「对任何使用者项目都成立」→ 限定为「对 Python/shell 测试项目成立」；
   - 点明扫描器**只覆盖 `.bats/.bash/.sh/.py`**，TS/JS/Go 测试文件（如 Playwright 用例）**不在扫描面内**，需自行用等效检查。
   *为什么*：本协议 P3 明确要求 UI 任务写 Playwright 用例，而**这类项目跑该自查会恒绿**——比没有自查更危险（给出虚假保障）。

6. **DEBT0040 的债记应重新对齐**：`implementer.md` 未加 tmp 隔离条文（criteria ① 只完成一半）、CI 无兜底步（criteria ③）。建议要么补齐，要么在 `closure_note` 里**显式声明哪条未做及理由**，而不是以「或等效机制」一笔带过（该「等效机制」经实测不成立）。

### 事实性更正（供父 Agent 采纳）

7. 新哨兵注释中的「真正的全量对比由 P6.5 judge 的 `git status` 复核承担」**应删除或改为「当前无此兜底（已知缺口）」**——judge.md 无此职责，属虚构的保障来源。

---

**评审人身份声明**：本报告由独立评审角色（protocol-alignment-review）产出，全部结论基于**本机实跑复现**（12 组 provenance 输入 / 2 组变异测试 / 2 组注入测试 / 1 次全量套件 + 哈希对比 / 1 次 `-n auto` 顺序复现）。所有注入均已还原，工作树中**除父 Agent 自己的改动外无评审残留**（临时目录 `.review-scratch/` 已删除）；未修改任何被评审文件、未 commit。

---

## 处置记录（主 Agent，2026-09-29）

**评审 status = approved（无阻断项，3 项非阻断整改 + 2 处「声称有实际无」+ 2 处实测缺陷）；以下逐条处置。**

> ⚠️ **评审者两次指出的并发编辑问题都成立**：评审窗口内我持续改被评审文件（P3-tdd.md、`test_t42_*.py` 至少 4 版、4 处协议文档、tech-debt.md、CHANGELOG、baseline）。评审仍以固定快照给出结论并标注了 md5。**这是本批流程的真实缺口**（与 TAG0039/TAG0041 同源：改动者与评审者共用工作区）。

| # | 评审发现 | 处置 |
|---|---|---|
| **1（最严重）** | **漏改 2 处最权威落点**：`agate/WORKFLOW.md:324` 与 `agate/rules/phases.yaml:109` 仍写 `check-p6-provenance.py exit 0`；而新守护 `_DEBT0045_DOCS` **不含这两者** ⇒ **永远不会为此报警** | **已修**：两处均补 `exit 0/2（2 = 协作规范 WARNING，不阻塞）`；守护清单**扩到 6 处**（含这两处），并注明它们是「4 处散文 + 2 处最权威落点」。`phases.yaml` 属逐字节护栏保护面，基线第 7 次刷新并写明理由 |
| **2** | **DEBT0045 closure_criteria #2 未实现却标 closed**：exit 1 真失败时仍只打「验收异常」，不转达 provenance 原因 | **已修**：新增 `_p6_relay_provenance()`，**exit 1 与 exit 2 两条分支都转达**具体原因行；并去掉初版的 `break`（原只转达第一条、不告知总数）→ 现列出全部、多行时给总数。新增 2 条测试（`..._relays_specific_reason` 断言输出含具体缺失文件名；`..._renders_all_warnings_not_just_first` 断言多条不截断）。既有断言同步更新为新措辞 |
| **3** | **DEBT0040 哨兵顺序依赖 + 范围窄**：`-n auto` 下哨兵常先于污染者执行 ⇒ **静默漏报**；且只认 `gate-events.jsonl`（注入 `active-tasks.md`/`.state.yaml` 均漏报） | **已重设计**：改为**静态检查**（扫测试源码，禁止把仓库内路径传给 `append_event`/`write_state_yaml`/`write_gate_result`）——**与执行顺序无关**。已实测：`-n auto` 下注入违规→**转红**（旧哨兵同场景 PASS）。范围据实收窄为「根因覆盖」，不再声称等价于关闭本债 |
| **4** | 新哨兵注释称「真正的全量对比由 P6.5 judge 的 `git status` 复核承担」——**该保障在仓库中不存在**（judge.md 无 `git status`/`porcelain`） | **已删**（虚构保障）；改为如实写「事后是否写脏**没有** CI 兜底——已知缺口」 |
| **5** | **DEBT0048 声称「对任何使用者项目成立」过头**：实测扫描器只认 `.bats/.bash/.sh/.py`（`L128`）⇒ 只含 `.test.ts` 的前端用例目录**恒绿**，是虚假保障 | **已据实收窄**：三处落点（P3 卡 / 派发模板 / test-designer）均加「扫描面限定」——对 **Python/shell 测试项目**成立，**TS/JS 用例不在扫描面内**；前端项目的平台无关性列为已知缺口 |
| **6** | **DEBT0040 判为 closed 但 closure_criteria #1/#3 未落实**（`implementer.md` 零改动、CI 无兜底步） | **已处置**：① 补 `implementer.md`「写类代码与测试的仓库隔离」节（是）；② 静态 lint 落地（是）；③ **CI 改动须用户许可**（`AGENTS.md` 第 5 条），本批未请求 ⇒ **债改回 `open`**，`closure_note` 据实写明 3/4 完成 + 缺口，**不以 3/4 的完成度标 closed** |
| **附** | `_log` 的 `break` 漏警告（构造 4 条只转达 1 条） | 已随第 2 项一并修（去 `break` + 报总数） |

**核验**：全量 pytest **2427 passed / 2 failed / 2 skipped**（两个 failed 均为**预存环境性**：`opencode` 不在 PATH；`git clone --bare --local` 跨设备硬链接——`/tmp` 为独立 tmpfs）；consistency 386 WARNING / 0 ERROR；ruff / shellcheck 通过；`agate-debt-check` exit 0。

**元教训**：本批我被抓到 **3 处「声称有、实际无」**（漏改的权威落点、未满足却标 closed 的债、虚构的 judge 兜底），**全部由独立评审发现，无一是自查发现的**。共同形态是「**改了显眼处、漏了权威处**」与「**把计划当已做**」——与我在 TPV0099 复盘里记录的失效模式同族，且在**我自己**身上重复出现。这再次说明：独立评审不是流程装饰，它抓的正是作者的结构性盲区。
