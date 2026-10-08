---
phase: P4
task_id: TAG0050
parent: P4-implementation-G1.md
trace_id: TAG0050-P4-20261008
type: review
agent: cso
status: rejected
---
# P4-review-cso — TAG0050 批 G1（A2+A3+A4）安全维度独立评审

- **评审对象**：TAG0050 合批 G1（A2 CI 逐提交回放 + A3 state-set/状态事实 + A4 义务机械核验）
  的**未提交**实现；HEAD `b0a16c3a`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0）。
- **范围**：`P4-dispatch-context-cso-G1.md` 的 6 个重点核验项；不重做设计，只审安全边界。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本**上做可复现验证（`/tmp/opencode/cso-g1/`）；
  不改被评审文件、不写仓。既有 G1 验收面复跑 85 passed。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/cso-g1/` 下的协议副本与一次性 git 仓
  中进行；真实仓库 `git status --porcelain` 评审前后逐行一致（47 行，见「验证留痕」）。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **HIGH**（其中 1 项构成 A2 安全目标的 BLOCKER） |
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 3 |
| LOW | 2 |
| 是否阻塞发布 | **是** —— F-1：合并提交（evil merge）可静默删除/改写账本，A2 可信锚点漏检（设计 §2.4 第 4 点要求的账本最终状态检查被耦合进回放路径且按 `--no-merges` 过滤） |
| status | `rejected` |

## 二、6 个重点核验项逐条结论

| # | 核验项 | 结论 |
|---|---|---|
| 1 | 判定依据不可改写（judge/evidence_ref 只经契约） | **通过**（A1 的 `requirement_active` 消费方在 G1 未被改回；G1 未引入新改写路径）——但该保证**以账本在场为前提**，随 F-1/F-4 失效 |
| 2 | 可信锚点 `agate-ci-verify` 逐提交回放 | **不通过** —— ① 版本分支①未实现（F-5）；② `--no-verify` 违规提交**能**被抓 ✓；③ 合并提交跳过留绕过口子（**F-1**）；且锚点实为 advisory（F-3） |
| 3 | 账本完整性（A1 已落地 + G1 是否破坏） | **部分通过** —— `gate_run`/`state_transition` 随本次提交入库（F2 回归已修，真实 commit 复核 ✓）；`git mv` 账本仍判 ERROR（F-1a/F-1b 复现 rc=1 ✓）；但 F-1R 复合残留仍在且 **A2 同样漏检**（F-4） |
| 4 | phase 写入可信（HEAD 为 old_state + retries 回退） | **通过**（静态 + 用例复核）；附带 LOW 观察 F-6 |
| 5 | 义务机械核验的证伪力（「M 由作者自标」是否被根除） | **不通过** —— M 凭证空转、负向控制打错对象，F13 未根治（**F-2**） |
| 6 | 兼容承诺 §8（legacy 退出码/ERROR 集不变） | **通过**（A2/A3/A4 改动落在 §8 第 7/8/9 项内；legacy 路径未见新 ERROR） |

## 三、通过项（可复现证据）

### 核验项 1：判定依据仍只经契约

`requirement_active` 的全部消费点在 G1 后未被改回「可改的值」：

- `agate/scripts/check-gate.py:764`（`gate_p1`）、`:1250`（`gate_p65`）：契约优先，legacy 回退；
- `agate/scripts/pre-commit-gate.py:173`（`_judge_enabled`）：契约优先；
- `agate/scripts/agate-next.py:267-271`（`_p6_judge_advance`）：A3 删除了 `append_event` 导入与
  `_state_transition_event`，但**保留了** `requirement_active` 分支（未回退到 `judge.enabled`）；
- `agate/scripts/agate_common.py:1714`（`is_new_task_for_evidence_ref`）。

`git status` 的 G1 改动集不含 `agate_common.py` 的契约函数、也不含上述消费方的回退式改动。
**结论：通过。**（但注意：`task_level(task_dir) is None → legacy` 这一前提使全部消费方随账本摘除而回退——见 F-1/F-4。）

### 核验项 3（正向部分）：`gate_run`/`state_transition` 随本次提交入库

- 实现：`pre-commit-gate.py:687-708`（2h.1c 写 `state_transition` + 2h.1d `git add`，**前移到 2g `continue` 之前**）；
  `:765-774`（2h.1e 在 `gate_run` 之后再 `git add` 一次，覆盖 2h.1d 之后追加的 `gate_run`）。
- 用例：`agate/tests/integration/test_tag0050_state_set.py:83-104`
  （`test_gate_run_and_state_transition_committed_with_real_commit`，**真实 `git commit` + 指向 checkout 协议的 hook**，
  读**已提交**账本断言 `gate_run` 与 `state_transition` 同时在库）。
- 实跑：G1 验收面 `85 passed`（含该用例），跑前/跑后 `git status --porcelain` 一致。

### 核验项 3（正向部分）：`git mv` 账本仍判 ERROR

仓外副本（`/tmp/opencode/cso-g1/repo`，`AGATE_ROOT=<副本>/agate`），种子任务含 `task_created` 账本：

| 场景 | 命令 | rc | 判定 |
|---|---|---|---|
| F-1a 同目录改名 `.bak` | `git mv …/gate-events.jsonl …/gate-events.bak` | **1** | 拦截 ✓ |
| F-1b 移入别任务目录 | `git mv TAG0001/gate-events.jsonl TAG0002/gate-events.jsonl` | **1** | 拦截 ✓ |

命中同一 ERROR：
```
GATE: 含创建/迁入事件的账本被删除/移走（agate-workspace/tasks/TAG0001/gate-events.jsonl）
      ——不得删除/截空/移走（防止降回 legacy）；迁移请用 agate-task-init.py
```

### 核验项 4：phase 写入以 HEAD 为 old_state

- `agate/scripts/agate-state-set.py:121-136`（`_head_phase` 取 `git show HEAD:<rel>`）、`:203-225`
  （`_cmd_phase` 以 HEAD phase 为 `old_phase`，用**拟写入**的 `prospective`（回退时已补 `retries`）调
  `check_transition`），与 `check-state-transition.py:295-403` 同源纯函数。
- 回退写 `retries`：`agate-state-set.py:191-200`（`_retreat_retries` 追加 `attempt`），
  `check-state-transition.py:379-388`（提交期校验 `new_retries_len > old_retries_len`）。
- 用例 `test_tag0050_state_set.py::test_bdd_37_retreat_writes_retries` 通过。

### 核验项 6：兼容承诺 §8

G1 的三批改动面与设计 §8 允许项一一对应：A2 → 第 8 项（`agate-ci-verify` 改为回放，CI 中可能出现新 FAIL）；
A3 → 第 7 项（`state_transition` 写入点改动：`agate-next` 不再写、进入 PAUSED/READY/DONE 开始写）
+ A3 status 规则（非 legacy 写 `status` → ERROR，仅作用于非 legacy）；A4 → 第 9 项（义务改标 + 基线重设）。
`agate-state-yaml-check.py:41-58` 对 **legacy** 分支保持「status 必填」原逻辑；`check-obligations.py`
不在 hook/check-gate 必经路径上，不影响 legacy 提交。既有测试改动均在 §8 例外面内（与 SELF-GATE
评审 A5 核对一致）。**结论：通过。**

## 四、发现（按严重性降序）

### F-1 HIGH（A2 安全目标的 BLOCKER）：合并提交（evil merge）可静默删账本，回放与账本最终检查均漏检

- **位置**：`agate/scripts/agate-ci-verify.py:349`（`rev-list --no-merges` → `commits` 不含合并提交）、
  `:371-373`（无「改动任务目录」的非合并提交 → 直接 `_skip`）、`:399`（`_ci_ledger_checks(repo, commits)`）、
  `:278-300`（`_ci_ledger_checks` 只遍历 `commits`，即**非合并**提交）。
- **设计口径**：`docs/design-notes/design-tag0050-task-data-contract.md:230-235`（§2.4 第 4 点）明确要求
  「对 `<base>..HEAD` 中**每个变化过的账本**做最终状态检查……**即使不逐提交回放（squash 仓库的 push）也照常执行**」。
  实现把该检查**耦合进回放路径**，且 `commits` 已按 `--no-merges` 过滤 ⇒ 合并提交引入的账本变化
  **既不回放、也不做最终状态检查**。
- **可复现证据**（`/tmp/opencode/cso-g1/repo5`，`AGATE_ROOT=<副本>/agate`）：

  ```
  $ git log --oneline --graph -4
  *   5e5e5a8 evil merge deletes ledger
  |\
  | * 93aba54 feature non-task
  |/
  * 80acc47 pin + status
  $ AGATE_ROOT=… python3 …/agate-ci-verify.py --base 80acc47
  ==================================================================
  SKIP: 回放范围 80acc470..5e5e5a8a 未改动任务目录（1 个提交）
    ⇒ 本次**未实际回放** gate（不是「跑了且通过」）
  ==================================================================
  CI_RC=0
  $ git cat-file -e HEAD:agate-workspace/tasks/TAG0001/gate-events.jsonl ; echo $?
  fatal: 路径 … 不在 'HEAD' 中   → ABSENT
  ```

  即：一次 `git merge`（把删除账本作为冲突解）即可让含 `task_created` 的账本从已提交历史中消失，
  该任务在所有消费方眼中降回 legacy，而 **CI 可信锚点输出 SKIP/通过**。本地 `git merge` 不触发
  pre-commit（`pre-commit-gate.py` 规则 4 无从运行）。agateon 的 release PR 按 AGENTS.md 须用
  `--no-ff` 合并 ⇒ **合并提交正是本仓常态集成路径**，此口子非边缘场景。
- **性质**：这是实现与设计 §2.4 第 4 点的**明确偏差**（不是设计有意跳过合并回放——设计只对「回放」跳过合并，
  对「账本最终状态检查」要求无条件执行）。
- **建议修复（最小）**：`_ci_ledger_checks` 改为遍历 `base..HEAD` 的**全部**提交（含合并），
  且**无条件**执行（不因 `task_commits` 为空而 `_skip`）。补一条负向用例：evil merge 删账本 → rc≠0。
- **严重性判定**：HIGH（BLOCKER 级）——一次合并提交即静默摘除账本、且这正是 A2 要建立的「可信锚点」的
  核心不变量（账本不可删 / 防降回 legacy）。

### F-2 HIGH：M 义务的机械核验是空转——负向控制打错对象，F13 未根治

- **位置**：`agate/rules/obligations.yaml` 的 60 条 M 义务**全部**把 `test` 指向
  `agate/tests/unit/test_tag0050_obligations_enforcement.py::test_obligation_enforced[<id>]`
  （`grep -oE "test:\s*\S+::" agate/rules/obligations.yaml | sort -u` 只有一个文件）；
  该节点（`test_tag0050_obligations_enforcement.py:85-92`）**只读 YAML 文本**断言该义务块含
  `enforced_at` 字样，**不 import、不执行任何 gate/hook 代码**。
- **设计口径**：设计 §2.9（`:337`、`:343`）要求「删掉**该义务对应的判断分支**，`test` 必须转红」；
  「一条义务若想算作 M，必须有一个能被删改打红的测试作为凭证」。
- **事实**：
  - 60/60 的 `test` 凭证是同一个空转参数化节点——删掉**任何**义务的真实执行分支，它都**不会**转红；
  - `enforced_at` 的落点极粗：`grep -cE "enforced_at:.*function:\s*main\b"` = **57/60** 指向某脚本的
    `main`（如 `OBL-P8-02` 指向 `check-gate.py::main`，而非 `gate_p8`），可达性检查近乎「该脚本 main 存在」；
  - SELF-GATE 复评 `…-G1-rereview2.md` 的 H1 把 BDD-42 改为「删 `check-obligations.py` 的
    `_check_enforced_at` 调用 → 用例转红」——**打的是检查器，不是义务的执行分支**，故其「ALIGNED」结论
    并未触及设计要求的负向控制。
- **可复现证据**（副本 `/tmp/opencode/cso-g1/agate`，把 `check-gate.py` 的 `gate_p8` 交付校验分支
  `if "delivery:" not in p8_text:` 改为 `if False:`）：

  ```
  $ AGATE_ROOT=/tmp/opencode/cso-g1/agate python3 …/check-obligations.py ; echo rc=$?
  M 类占比: 56/119 = 0.4706（基线 56/119 = 0.4706）
  CHECK-OBLIGATIONS: OK（无「无归宿」项 + 无 ERROR + M 类占比不低于基线）
  rc=0                       # ← 删掉 OBL-P8-02 的真实执行分支后，工具仍绿
  $ pytest '…/test_tag0050_obligations_enforcement.py::test_obligation_enforced[OBL-P8-02]'
  1 passed                   # ← 该「凭证」仍绿（它只读 YAML）
  ```
- **结论**：**「M 由作者自标」并未被根除**——机制只是把「作者自标 M」换成了「作者自标 M + 指向一个
  必然存在的函数名 + 指向一个只读 YAML 的空转节点」。F13 的实质（义务真有可被删改打红的执行落点）未达成。
- **建议**：`test` 凭证须指向**真正校验该义务行为**的用例（设计示例 `test_obl_p8_02_delivery_missing_blocks`
  在仓内不存在）；并落地设计要求的负向控制抽样——删义务执行分支 → 对应用例转红。
- **严重性判定**：HIGH（信任/不可否认面：gate 声称「机械核验」而实为自证）。

### F-3 MEDIUM：可信锚点实为 advisory，且缺设计要求的降级声明

- **事实**：`.github/workflows/protocol-tests.yml:19-22` 明记「**gate-backstop 已移出 required**」
  （2026-10-05 更正）。故本仓 CI 的 `gate-backstop` **不是 required check** ⇒ 回放失败**不阻塞合并**。
- **设计口径**：`P2-design.md §8` `env_constraints.ci_required_permission` 要求：
  「未取得许可时 CI 回放**降级为 advisory（非锚点）**，设计宣称的『可信锚点』不成立——**须在 A2 的 workflow
  落地时明确声明该降级语义**」。
- **现状**：`agate/UPGRADING.md:279-348` 的 G1 节只说「可信锚点移到 CI」「本仓 CI：gate-backstop job 已加
  `fetch-depth: 0`…」，**未声明 advisory 降级**；workflow 的 G1 diff 也未声明。
- **影响**：在 required 落地前，「可信锚点」对 agateon 自身并不成立（advisory 等于没有强制力），
  文档/实现口径与设计前提不符。
- **建议**：在 UPGRADING G1 节与 workflow 注释中显式声明「未设 required ⇒ 回放为 advisory，非可信锚点」，
  或取得用户许可把 `gate-backstop` 设为 required。

### F-4 MEDIUM：F-1R 复合改名残留仍在，且 **A2 同样漏检**（新增证据）

- **事实**：A1 复评（`P4-review-cso-rereview.md` §三）登记的 F-1R 残留（清空源任务目录索引 + 把账本
  `git mv` 进既有任务目录 → `pre-commit-gate.py` rc=0，`task_level` 由 1 变 None）在 G1 **未闭合**。
- **新增证据（A2 也漏检）**：`_ci_ledger_checks` 用 `git diff --name-only parent c` 枚举变化账本，
  而 git **默认开启改名检测** ⇒ 改名只输出**目标路径**、**不输出被删除的源路径**：

  ```
  $ git diff --name-only  <parent> <head>          # 默认 -M
  agate-workspace/tasks/TAG0002/gate-events.jsonl          # 源 TAG0001/… 不出现
  $ git diff --name-only --no-renames <parent> <head>
  agate-workspace/tasks/TAG0001/gate-events.jsonl          # 源路径（被摘除）
  agate-workspace/tasks/TAG0002/gate-events.jsonl
  ```

  实跑 `/tmp/opencode/cso-g1/repo4`：复合改名提交经 `--base` 回放判 **PASS**，无 `FAIL 账本` 行
  （`CI_RC` 只因另一无关提交为 1）。故复评所称「不被 A2 的 CI 回放捕获」成立，且**账本最终状态检查亦盲**
  （同 F-1 的过滤/路径枚举问题）。
- **建议**：`_ci_ledger_checks` 改用 `--no-renames` 或 `--name-status -M` 同时取源/目标路径；
  或在豁免判据加「目标任务目录在 HEAD 中不存在」的必要条件（复评 §三 已给改法）。补负向用例。

### F-5 MEDIUM：回放协议版本分支①未实现 → 使用者项目锚点不可信；删除 `.agate-version` 不判 FAIL

- **位置**：`agate/scripts/agate-ci-verify.py:18-23`（docstring 自认分支①未实现）、`:160-181`
  （`_resolve_protocol` **只**认 `AGATE_ROOT` 或其仓库 merge-base / 仓库本体，**不按 `.agate-version` 选协议**）、
  `:355-368`（`.agate-version` 仅做单调不降检查）。
- **影响 1（使用者项目）**：带 `.agate-version` 但无协议本体、CI 未设 `AGATE_ROOT` 的项目，
  `_resolve_protocol` 返回 `(None,None,None)` → `:383` `_fail("未固定协议版本……请写 .agate-version")`
  （**误导**：用户已写）；即使设了 `AGATE_ROOT`，回放用的是 `AGATE_ROOT` 指向的协议，而**非**钉住的版本
  ⇒ 项目钉 `v0.50.0`、CI 装 `v0.79.0` 时会用错协议判定（设计 §2.4 优先级①的本意失效）。
- **影响 2（钉版本可被移除）**：`_version_in_commit` 对**缺失** `.agate-version` 的提交返回 `None` →
  `:360-363` `continue`，不判 FAIL。实跑 `/tmp/opencode/cso-g1/repo6`：PR 删除 `.agate-version` 并改任务 →
  回放 `PASS`（`CI_RC=0`）。设计只写「不低于 merge-base」，未写「删除」，但删除后项目不再钉版本、
  回放协议退化为环境/merge-base，属单调不降检查的**绕过面**。
- **建议**：把「提交缺失 `.agate-version` 且非仓库本体」也判 FAIL；或实现分支①（按逐提交版本定位/安装）。

### F-6 LOW（信息）：phase「唯一写入口」是约定而非机械强制

- 设计 §2.7 称 phase 只能经 `agate-state-set` 写入；但提交期只校验**转移合法性**
  （`check-state-transition.py` 以 HEAD 为 old、当前为 new），**不校验「写入路径」**。
  直接手改 `.state.yaml` 的 phase 到任一合法后继（如 P5→P6）并提交，与经 state-set 写入等效通过。
  这是设计的有意取舍（state-set 是**推荐**路径，强制力来自提交期转移检查），此处仅记录边界，
  非 G1 引入，非阻塞。

### F-7 LOW：`check-obligations.py` docstring 与代码的候选顺序不一致

- `agate/scripts/check-obligations.py:62-67` 注释列候选顺序为「AGATE_ROOT → 脚本根 → cwd」，
  随后一句却写「**脚本相对优先**，保证开发 checkout 与安装版本布局都能定位到本脚本同源的登记表」——
  与代码（`:68-82` env 优先）矛盾。纯文档瑕疵，不影响判定。建议改注释与代码一致。

## 五、STRIDE 矩阵（针对 G1 改动面）

| 威胁 | 面 | 评估 | 关联 |
|---|---|---|---|
| **S**poofing | 任务身份 / 等级 | 等级仍由账本首行 `task_created` 记录；G1 未改判定源 ✓ | — |
| **T**ampering | 账本内容 | 只追加（A1 规则 3）✓；`git mv` 单次改名被拦 ✓；**合并提交可静默删账本** ✗ | **F-1** |
| **T**ampering | 判定依据（judge/evidence_ref） | 消费方均依契约 ✓；但依赖账本在场 ⇒ 随 F-1/F-4 回退旧逻辑 ✗ | F-1/F-4 |
| **R**epudiation | 义务「机械核验」留痕 | `enforced_at`/`test` 字段齐备但**空转**，负向控制打错对象 ⇒ 声称的机械核验不成立 ✗ | **F-2** |
| **R**epudiation | CI 可信锚点 | 回放能抓 `--no-verify` ✓；但合并提交漏检（F-1）、锚点实为 advisory（F-3）、版本分支①未实现（F-5） | F-1/F-3/F-5 |
| **I**nfo disclosure | 账本 / 产出 | 未见敏感数据暴露面（本批无日志/响应面） | — |
| **D**oS | 安全门误拦 | A3 status 规则对 legacy 无回归（实测 85 passed）；未见新增误拦面 | — |
| **E**levation | 阶段 / gate 推进 | state-set 以 HEAD 为 old、retries 回退校验 ✓；合并提交可绕过转移/账本检查 ✗ | F-1 |

## 六、与既有 SELF-GATE 评审的关系

- `docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G1.md`（首评）已点出 A4-3「BDD-42 负向控制
  非真变异」与 A1-2「`gate_run` 未随提交入库」；后者在 G1-fix 中已修（本评审复核通过，见 §三）。
- `…-G1-rereview2.md` 判 H1（A4-3）「ALIGNED」——但其变异对象是**检查器**（`check-obligations.py` 的
  `_check_enforced_at` 调用），**不是义务的执行分支**；本评审以 F-2 的实测证明设计要求的负向控制
  **仍未达成**（删 `gate_p8` 交付分支 → 工具与凭证均不转红）。
- 首评 A4-4「分支①/全零/squash/§8-12 无测试」：本评审进一步给出 F-5 的可复现绕过（删 `.agate-version`）
  与 F-1 的合并提交漏检——均不在首评/复评覆盖面内。
- 复评 §三 已登记 F-1R（MEDIUM，非阻塞）并声明「不被 A2 捕获」；本评审以 F-4 补齐**可复现证据**
  （`--name-only` 隐藏源路径），并指出其与 F-1 同源。

## 七、验证留痕与环境隔离

- 仓外副本：`/tmp/opencode/cso-g1/agate`（协议工作树副本，供 `AGATE_ROOT` 指向）、
  `/tmp/opencode/cso-g1/{repo,repo2,repo3,repo4,repo5,repo6}`（一次性 git 仓，`mkrepo.sh` 构造）。
- 真实仓库只跑了一次 G1 验收面 pytest（`-p no:cacheprovider` + `PYTHONDONTWRITEBYTECODE=1` +
  `--basetemp=/tmp/opencode/cso-g1/pt*`）→ **85 passed**；跑前/跑后 `git status --porcelain` 逐行一致（47 行）。
- F-2 的真变异只在副本 `/tmp/opencode/cso-g1/agate/scripts/check-gate.py` 上做，跑后逐字节恢复（`RESTORED`）。
- 未编辑任何被评审文件；未执行任何破坏性/写仓命令。
- `[PROD_NOT_TOUCHED]` 未接触生产环境。

## 八、返回给主 Agent

- **File**: `agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso-G1.md`
- **Status**: `rejected`
- **最高严重级别**：HIGH（F-1 为 A2 安全目标的 BLOCKER）
- **各级计数**：CRITICAL 0 / HIGH 2 / MEDIUM 3 / LOW 2
- **是否阻塞发布**：**是**。F-1（合并提交静默删账本，回放+最终检查双漏检）须修并补负向用例后重审；
  F-2（M 凭证空转）须落成真负向控制或经 P7 显式接受；F-3/F-4/F-5 建议随修复一并处理或经主 Agent 明确豁免。
