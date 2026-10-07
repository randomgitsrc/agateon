# 任务数据契约：结构化判定、可信写入与任务版本（TAG0050）

- **对象**：agateon 协议本体，main `720c97d3`（v0.79.0，TAG0042 已合入）。
- **检验项目**：
  - **agateon**：走 PR，多任务合版，42 个任务目录；
  - **peekview**（main `4ea7b8f`）：直推 main，95 个任务目录，CI 中没有 agate 相关 job；
  - **X**（假想项目）：Go 服务，使用 GitLab，没有 CHANGELOG、UI、roadmap，也没有发版流程。
- **关联**：
  - RM-AG0099（本任务登记）；
  - 吸收 RM-AG0085、RM-AG0087、RM-AG0097，以及 RM-AG0059 的第 ① 项；
  - 承接 TAG0042 实施评审（`review-tag0042-implementation.md`）中的 I-1、I-2（证据部分）、I-4、I-5、I-6、I-7、I-8。
- **标注**：
  - `[实测]`：附命令，可复现，由 `repro-tag0050.sh` 统一复现（附录 A）；
  - `[读码]`：给出 `文件:行`，以 v0.79.0 为准；
  - `[自述]`：引自仓库内的既有记录，或独立评审报告中的实测；
  - `[推断]`：推理所得，未经实测；
  - `[待测]`：尚未核实，列入 `exp-tag0050-task-data-contract.md`。

---

## 0. 问题：判定依据是可以被随手改写、又有歧义的文本

下表各项在 v0.79.0 上**全部仍然成立**。F12–F15 是 TAG0042 新引入或没有解决的问题。

| # | 事实 | 后果 |
|---|---|---|
| F1 | P6 frontmatter 的 `pass`/`fail` 由 agent 自报，`check-gate P6` 只信这两个值（`check-gate.py:1186`）。正文与汇总不一致时只给 WARNING，BDD 对照只比条数 `[实测]`。三种篡改的结果：<br>**A**：正文把 BDD-5 改成 FAIL → check-gate 放行；provenance 恰好以"证据未被引用"拦下；<br>**B**：删掉一条 BDD 及其证据 → 两道检查都放行，只出 WARNING；<br>**C**：把 BDD-5 改写成重复的 BDD-4 → 两道检查都**静默放行** | 漏验、挑验在 P6 这一层看不见 |
| F2 | 在 P7 正文追加 `- [BLOCKER] …`，frontmatter 写 `blocker_count: 0` → `check-gate P7` rc=0 `[实测]` | 汇总值可以盖住阻断项 |
| F3 | 新机制的强制要求，取决于 agent 能改的值 `[实测]`：<br>**F3a**：judge 的 P1 门槛按 `created` 日期判断（`dispatch.yaml:17`，`check-gate.py:767` 有意 fail-open）。把 `created` 改早或删掉，强制就失效；<br>**F3b**：在 P6 时把 `judge.enabled` 改为 false，`gate_p65` 直接放行（`:1232`）。另外两个消费方同理：`pre-commit-gate.py:157`、`agate-next.py:266` `[读码]`；<br>**F3c**：证据引用的强制 `evidence_ref_required_since`（`dispatch.yaml:26`）同样依据 `created`（`agate_common.py:1707`，有意 fail-open），消费方为 `check-p6-evidence.py:187` 和 `check-p6-provenance.py:479`。把 TAG0042 的 P1 `created` 回填为截止日前，同一条缺证据引用的 PASS 从 rc=1（阻断）降为 rc=2（仅 WARNING）`[实测]`。全仓只有这两个日期门槛 `[读码]` | 改一个值，机制就失效 |
| F4 | 生产接触安全门的判据是 `^\s*-?\s*\[PROD_TOUCHED\]`（`pre-commit-gate.py:348`）`[实测]`：<br>• 粗体、引用块、`*` 列表写法**不拦**；<br>• `- [PROD_TOUCHED]: 无` 这种否定写法**反而拦**（peekview `T039…/P4-progress.md:21`） | 安全门在两个方向上都会判错 |
| F5 | 否定写法被正则当成声明 `[实测]`，例如：<br>• `- [DESIGN_GAP: 无]`（peekview `TPV0091/P7-consistency.md:32`）<br>• `` - `[NEED_CONFIRM]`：…无残留 ``（peekview `T083/P7-consistency.md:202`） | 正则判断不了散文的语义 |
| F6 | 同一标记有 4 套行首口径，两仓真实语料中有 **182 行**判定不一致（`markers.yaml:43` 注释）`[自述]`；10-02 到 10-03 之间，行首形态修订了 4 次 `[自述]` | 追着改正则，永远追不完 |
| F7 | `AGATE_ROOT` 覆盖模式下版本号是空串（`agate_common.py:354`）；任务目录里没有任何版本或契约字段（`.state.yaml` 中没有对应键，`phases.yaml` 的 `task_fields` 中也没有） `[读码]` | "这个任务按哪套规则判"，只能拿日期近似 |
| F8 | `pre-commit-gate.py:370` 以 3 个参数调用 2 参数的 `append_event`，抛出的 TypeError 被吞掉 `[实测]` | PAUSED 时的生产接触留痕从来没有写成功过 |
| F9 | P6 引用的 `.log` 在克隆中缺失 `[实测]`：peekview 173 个中缺 157 个，涉及 40 个任务；agateon 665 个中缺 9 个 | "证据存在"只在作者本机成立 |
| F10 | 没有 frontmatter 块时，schema 校验整体跳过（`agate-frontmatter-check.py:217`）`[读码]` | 可以退回旧格式，绕开校验 |
| F11 | 用"出现了某个词"代替"做了这件事" `[读码]`：<br>• P2 UI 节只看关键词（`check-gate.py:604`）；<br>• P1-review 只要求出现任意 `BDD-数字`（`:677`）；<br>• 骨架用子串判断（`:964`，RM-AG0085）；<br>• P7 交叉引用只看关键词（`:1332`）；<br>• P1 的 `phases` 与正文裁剪没有一致性校验（RM-AG0087） | 判据的下限太低 |
| F12 | P8 的 `delivery` 用子串判断（`check-gate.py:1450`）：删掉字段、在正文写一句"暂不声明 delivery: 方式" → rc=2 `[实测]` | F11 那一类问题又多了一处 |
| F13 | `obligations.yaml` 的 M（脚本强制）是作者自己标的，`check-obligations` 只检查"非空"和"占比不降" `[读码]`。M 类中有 **4 条**的 `script` 不在 hook 或 check-gate 的调用集合里（OBL-P2-12、X-10、X-17、X-19）`[实测]`。R 类要求"由脚本强制评审出现"，但 check-gate 只对 P1、P2、P4 的评审校验了 `agent ≠ main`（`check-gate.py:672/919/1007`）`[自述，R2 评审]` | 义务登记重演了"自报汇总"的问题 |
| F14 | TAG0042 批 1 之后，`agate-next` 不再写 phase，协议**也没有提供写 phase 的工具**；`agate-config` **没有 set**；仓库里有 3 处手写的结构校验：`check-yaml-schema.py`、`agate-frontmatter-check.py`（自定义 `{required, enums}` 格式）、`agate-config.py:104` `[读码]` | 声明能读不能写，又回到了靠记忆 |
| F15 | `agate-ci-verify` 存在两个问题：<br>• 多任务时恒为 SKIP（`:103`；agateon 42 个任务 → SKIP，rc=0）`[实测]`；<br>• 单任务时按 `tasks/<task_id>` 拼路径（`:126`），而真实目录名是 `{ID}-{slug}`，`check-gate` 对不存在的目录返回 0，结果是**假 PASS**：仅保留 TAG0037、phase 设为 P7 并删除 P7-consistency.md 后，ci-verify 输出 PASS，而真实目录的 `check-gate P7` 为 rc=1 `[实测]`；<br>• `.gate-result.json` 被 ignore，导致 CI 中的对照代码是死代码 `[自述，R2 评审]` | 防 `--no-verify` 的 CI 锚点并不存在 |

**根因**：判定依据是 agent 写的自由文本、自报的汇总值、可以随手改的开关、作者自标的分类；规则写在散文里，靠 agent 记住。TAG0042 的实施过程也印证了这一点：评审已经看到 F12 和"`gate_layer` 没有消费方"，但"BDD 的 Then 没写到"，于是被接受了。**评审发现了问题，却没有变成判据。**

---

## 1. 原则

1. **判定只读结构化数据。** 正则只做"命中即拦"的**绊线**，不做"命中才算"的**判据**。
2. **任务数据分三类，每类只有一个写入方：**

   | 类 | 例子 | 由谁写 | 校验 |
   |---|---|---|---|
   | **系统事实** | 契约等级、创建时间、计数与汇总、是否需要 judge、任务状态、义务的执行方式 | 工具写入，或由 gate 现算 | **不提供 setter**；文件中写了的值也不采信 |
   | **agent 声明** | 逐条验收结论、生产接触、待确认项、范围增补、交付方式、phase | 只能经 set/append 工具写入 | 写入时校验；gate 用**同一份契约**复验 |
   | **叙事** | 方案取舍、方法说明 | 自由 markdown | 交给评审 |

3. **推导值不允许声明。**
4. **不依赖记忆。** 缺什么由工具列出，gate 报错时直接给出修复命令。
5. **一个事实只有一个源。** 给人看的视图由工具渲染，gate 规范化行尾后逐字节核对。
6. **新旧任务靠契约等级分流，不靠日期。** 等级取自任务自己的创建事件，契约按等级冻结。
7. **通用。** 字段只表达协议自身的概念，必须同时对 agateon、peekview、X 成立。

**边界**：结构化能消除**解析歧义**和**漏写**，但防不了**故意伪造**。本地账本没有密钥，`commit --amend` 或 `reset --soft` 之后改写账本，本地规则发现不了。因此**可信锚点是受保护分支上的 CI 回放**（§2.4），本地规则只负责尽早发现问题。CI 回放也有边界：PR 同时修改协议本体或 workflow 时，CI 判定不了"新规则是否合理"，这部分只能依靠 SELF-GATE 的人工独立评审。CI 能保证的只是这次评审确实留了痕。**注意**：CI 能保证「这次评审留了痕」**是在 `gate-backstop` required 生效时**；未设 required 时，连 SELF-GATE trailer 痕迹也不校验。

---

## 2. 契约等级与任务版本（批 A0–A4）

### 2.1 契约按等级冻结

```
agate/rules/task-data/
├── LEVELS.yaml          # [{level: 1, file: level-1.yaml, sha256: "…"}, …]；当前等级 = 最大值
├── level-1.yaml         # 第 1 级，发布后冻结
└── level-2.yaml         # extends: 1，只写本级的增量
```

**快照内容**：快照通过 `extends` 链合并后自成一体，包括：
- 逐文件的字段契约（§3.1）；
- 本级要求 `requires: {judge, evidence_ref, prod_touched, results, …}`；
- 绊线（§3.6）；
- 声明文件模式（§6）；
- 各阶段主产出（§4）；
- 阶段全集（§7）；
- `.state.yaml` 契约（§2.7）；
- 任务 ID 模式。

**冻结规则**：

1. **快照文件冻结。** `check-protocol-consistency` 新增 CHECK：每个快照文件 LF 规范化后的字节 sha256 必须等于登记值，文件与登记一一对应。改了已发布快照或新增快照未登记，都判 ERROR。
2. **代码语义冻结。**
   - 快照中引用的名字都由代码实现，**一经发布，语义即冻结**。包括：要求项的键、`render` 种类、`derive` 算子、绊线 id、判据 id（D1–D10）。要改变行为，必须起新名字（例如 `results_table_v2`），并由新一级快照引用。
   - 每一级都保存一组**黄金 fixture**：`agate/tests/fixtures/task-data/level-N/{pass,fail}/`。CI 对所有已登记等级逐一运行，判定结果不允许变化。这样可以在代码层拦住"改了渲染或判据，导致在途任务被追溯"。
3. **何时升一级。** 新增或收紧要求时登记新一级，否则在途任务会被追溯。用 `extends` 写增量，避免重复整份快照。
4. **任务等级高于运行中协议的最大等级时**（多人使用不同协议版本），一律 fail-closed，并提示"协议版本低于任务等级，请升级"。

**不用版本号的理由**：覆盖模式下读不到版本号（F7）；版本先后和"契约有没有变"是两回事。

快照本身只是数据：gate 代码按"要求项是否生效"分支；没有创建事件的任务（legacy）一律走旧路径。

### 2.2 创建事件（批 A1）

新增 `agate-task-init.py`：

```
agate-task-init.py <TASK_ID> --slug <slug> --title "<一句话>" [--priority high|medium|low] [--depends ID,ID]
agate-task-init.py --existing <TASK_DIR>   # 目录已手工建好、账本未被 git 跟踪：前置写入创建事件并重建哈希链
agate-task-init.py --adopt <TASK_DIR>      # 存量任务主动迁入当前等级
agate-task-init.py --upgrade <TASK_DIR>    # 非 legacy 任务升到当前等级
```

**新建任务的流程**：

1. 校验 `TASK_ID` 是否匹配 `agate_common.TASK_ID_RE`，即 `^[A-Z]+[0-9]+$`。同时把 `agate-state-yaml-check.py` 中的 `^T[A-Z]{2}\d+$` 统一到这个正则——后者会拒绝 peekview 的 `T090` `[自述，R1 评审实测]`。
2. 校验 tasks 目录下**不存在任何以 `{ID}-` 开头的目录**（peekview 的 T003、T004、T005 都有重名目录 `[自述]`）。
3. 创建目录和 `.state.yaml`，在账本**第一行**写入：

   ```json
   {"event":"task_created","task_id":"…","contract_level":<当前等级>,"agate_version":"…","resolver":"…","prev_hash":"<GENESIS>","ts":"…"}
   ```

4. 写入 P0-brief 骨架，然后 `git add`。

**`--existing` 的限制**：必须同时满足以下三个条件，因此不能用它把已提交的 legacy 任务（包括刚 `git mv` 过的）改写成新任务：
- 账本在 HEAD 中不存在；
- 账本**不是**暂存区中任何改名操作的目标；
- 账本中不含 `task_created` 或 `task_adopted`。

满足条件时，前置写入创建事件并重建哈希链是安全的，因为这些行没有被任何历史提交引用。

**事件规则**（`agate_common.check_ledger_events()`，以下违反任一条均判 ERROR）：

| 事件 | 规则 |
|---|---|
| `task_created` | 只能出现在**第 1 行**，最多 1 条；`contract_level` 必须是 LEVELS 中登记过的等级 |
| `task_adopted` `{contract_level, at_phase}` | 只能用于账本已有内容、但没有 `task_created` 的任务；最多 1 条；必须是本次暂存中**新增**的行 |
| `task_upgraded` `{from_level, to_level, at_phase}` | 必须出现在创建事件之后；`to_level` 严格递增，且必须是已登记的等级 |

- **任务等级** = 最后一条 `task_upgraded.to_level`，没有升级事件时取创建事件的 `contract_level`。等级只升不降。
- `agate_version`、`resolver` 只作记录，判定不读。
- **按阶段确定生效等级**：`task_created` 的 `at_phase` 视为 P0。对任一阶段 Pk：

  > `level(Pk)` = `at_phase ≤ Pk` 的创建、迁入、升级事件中，`contract_level` / `to_level` 的最大值；
  > 如果没有这样的事件，`level(Pk) = None`，即该阶段的产出按 legacy 处理。

  由此得到三条规则：
  - **单阶段判据**：Pk 的产出，按 `level(Pk)` 对应的快照来校验，包括 schema 和 `requires`。多次升级时，各阶段各取自己对应的等级；schema 收紧只影响升级之后的阶段。
  - **跨阶段判据**（例如 P7 对 P4 设计缺口的配对、P6 对 P1 BDD 集合的对照）：被引用的那个阶段的产出，按**它自己所在阶段**的等级选择读取方式。`level = None` 的产出用旧的正文读取器，**绝不能当作空集**。例如在 P7 才迁入的任务，P4 的散文 `[DESIGN_GAP]` 仍由旧读取器计数，P7 的结构化 `design_gap_reviews` 必须覆盖它们。被引用产出是散文时，配对按"计数相等"进行；是结构化数据时，按"id 集合相等"进行。
  - `requirement_active(task, name, phase)` 等价于 `snapshot(level(phase)).requires[name]`；当 `level(phase)` 为 None 时，走旧逻辑。
  - **有意的取舍**：任务迁入后又回退到更早阶段时（例如在 P5 迁入、回退到 P3 重做），重做的 P3 仍按迁入前的等级判定（legacy 迁入时即按旧逻辑）。理由是 `level(Pk)` 只取决于事件，不随回退变化。如果希望重做的阶段也按新契约判定，需要再执行一次 `--upgrade`，并把 `at_phase` 记为回退到的阶段。

### 2.3 legacy 判定与账本完整性（批 A1）

**legacy 判定**：`agate_common.task_level(task_dir)` 在账本中没有创建事件时返回 `None`，表示 legacy，任务走旧逻辑。conftest、fixture、repro 副本、R6 副本在**未提交新目录**的情况下，行为都不变。

**pre-commit 新增的检查**放在单独一步，位于 hook 的**任何追加写入之前**，即现有的 2h.1b 之前。每次提交都运行，不依赖 `.state.yaml` 是否被暂存。

**"任务目录"的定义**：tasks 下含有 `.state.yaml` 的直接子目录。`active-tasks.md` 这类文件不算任务目录。

| # | 规则 | 结果 |
|---|---|---|
| 1 | **新目录必须有创建事件。** 用 `git diff --cached -M --name-status` 判断。暂存区中新增的任务目录（HEAD 中该路径下没有已跟踪文件），如果它的账本**不是由 HEAD 中某个路径改名而来**，则账本第 1 行必须是 `task_created` | 否则 ERROR，附修复命令：`agate-task-init.py <ID> …` 或 `--existing <dir>`。<br>改名而来的目录（`git mv`、`agate-migrate-workspace`）沿用原任务的状态；legacy 任务改名后仍是 legacy |
| 2 | **新任务的等级必须是当前等级**（只在本地检查） | 否则 ERROR |
| 3 | **账本只追加。** 对每个被暂存的 `gate-events.jsonl`，HEAD 中的字节必须是暂存字节的前缀。在 v0.79.0 的全部历史上，共 166 次变化、0 次违反 `[自述，R2 评审实测]` | 否则 ERROR |
| 4 | **账本不可删除。** HEAD 中含有 `task_created` 或 `task_adopted` 的账本，被删除、截空或移走（不含改名）时 | ERROR（防止"降回 legacy"） |
| 5 | **事件规则。** 对每个被暂存的账本运行 `check_ledger_events()` | 违反即 ERROR |
| 6 | **legacy 不可重开。** legacy 任务从 READY 或 DONE 回到 Pn。现状是 `check-state-transition` 把 old_num 当作 0，对 `DONE → P1` 返回 rc=0 `[自述，R2 评审实测]`。历史上有 1 次合法使用：TAG0008 曾从 READY 回到 P5（`35001926`）`[自述，R3 评审]` | ERROR，提示用 `--adopt`（`at_phase` 记为重开的阶段）或新建任务 |
| 7 | **每个有暂存文件的任务目录都要检查**，不论是否暂存了 `.state.yaml`。现有的 hook 只处理暂存了 `.state.yaml` 的任务（`pre-commit-gate.py:226-232`），所以在 READY 之后只改产出、写入 `[PROD_TOUCHED]` 的提交可以通过 `[自述，R4 评审实测]`。改为：<br>• 对所有任务目录做 PROD_TOUCHED 扫描（2g.0），批 C 起再加上 `prod_touched` 字段检查；<br>• 非 legacy 任务暂存了阶段产出、却没有改 phase 时，按**被暂存产出所属的阶段**重跑该阶段的 gate。该阶段必须不晚于 HEAD 的 phase；HEAD 为 READY 或 DONE 时同样执行。例如 HEAD 在 P7、改的是 P6-acceptance，就重跑 P6 的 gate | 安全门不再依赖"是否改了 phase" |

**对既有测试的影响**：

- 规则 1 会使新建 `tasks/T001` 并提交的用例转红。粗略估计 `test_pre_commit_hook.py` 约 26 个、`test_agate_migrate_workspace.py` 约 9 个 `[自述，R2 评审]`。
- 迁移工具的用例因为走改名检测，预期不受影响 `[待测]`。
- 处理方式：受影响的用例改用 conftest 新增的 `init_task()` 辅助函数建任务（写入 `task_created`，等级为 1）。批 A1 的 P1 要给出**逐条清单**，列入 §8 的例外。

### 2.4 CI 回放：可信锚点（批 A2，修复 F15）

改造 `agate-ci-verify.py`：不再"重跑当前 phase 的 gate"，改为**在 hook 当时的条件下逐提交回放本地 hook**。

**1. 回放范围（合并提交一律跳过）**

| 事件 | 范围 |
|---|---|
| GitHub PR | `rev-list --no-merges <merge-base(base.sha, head.sha)>..<head.sha>`<br>注：检出的合成 merge ref 不参与回放 |
| GitHub push | `rev-list --no-merges <before>..HEAD`；`before` 为全零时取 `merge-base HEAD origin/<默认分支>`。在 push 口径下，第 3、4 点所说的"merge-base"指 `merge-base(before, HEAD)` |
| GitLab MR / push | 对应变量：`CI_MERGE_REQUEST_DIFF_BASE_SHA`、`CI_COMMIT_BEFORE_SHA` |
| 本地 | 缺省 `merge-base HEAD origin/<默认分支>`，仅供本地使用 |

- 只回放**改动了任一任务目录**的提交；
- 没有这类提交时才输出 `SKIP:` 并附原因；
- 合并提交本身从未经过 hook（`git merge` 不触发 pre-commit），把它当作一次提交回放，会把整个 PR 聚合成一次判定，导致合规合并被判 FAIL `[自述，R3 评审实测：回放 720c97d3 → rc=1]`；
- **squash 合并的仓库**：分支上的原始提交不会进入 main，因此 push 事件只做"账本前缀与事件规则"检查（见第 4 点），逐提交回放由 PR 事件承担。UPGRADING 中写明这一点。

**2. 回放方法**

对每个提交 C，在临时 worktree 中依次执行：
1. `git checkout -f C && git clean -fdx`
2. `git reset --soft C^1`
3. 此时 HEAD 是 C 的第一父提交，暂存区与工作树都等于 C，删除和改名都会如实出现在 `git diff --cached -M` 中。旧方法 `checkout C -- .` 看不到删除，还会把 `git mv` 退化成新增 `[自述，R3 评审实测]`，因此弃用。

在该状态下依次运行：
- `pre-commit-gate.py`
- `commit-msg-self-gate.py <msgfile>`（提交信息取自 `git log -1 --format=%B C`）

因为 `--no-verify` 会同时跳过这两个 hook，所以两个都要回放。任一 rc ≠ 0 即判 FAIL，并输出提交 SHA 和原因。

回放的强度**等于 hook 本身的强度**。§2.3 规则 7 把 hook 的覆盖面扩大到"每个有暂存文件的任务目录"之后，中途用 `--no-verify` 跳过的提交，都会按它本该受到的检查重新判定。

回放模式下的运行约束：
- 设置 `AGATE_REPLAY=1`；
- 跳过所有会改动文件的修正步骤（例如 2h 段的 `check-p6-format --fix`），只做校验；
- 不写 `.gate-result.json` 和 `.gate-history.jsonl`；
- 账本追加和 `git add` 照常执行，因为后续步骤要读取它们。这些副作用只发生在临时 worktree 中，回放结束后整个 worktree 删除。

**3. 回放用哪一版协议**

回放必须与开发者提交时 hook 所用的协议一致。否则合规提交也会被判 FAIL：卡片哈希这一类判定依赖执行它的协议版本。R3 评审实测回放 P8 提交 `33e4598c`：用 HEAD 的协议 rc=1，用 base 的协议 rc=0。同时，也不能用 PR 自身的协议，否则同一个 PR 可以顺手削弱判定。

| 优先级 | 来源 | 适用情况 |
|---|---|---|
| ① | **项目 `.agate-version` 固定的版本**：现有的 asdf 式声明（`UPGRADING.md:151`），本地 hook 也按它解析，因此本地与 CI 口径一致。**逐提交读取 C 树中的 `.agate-version`**，并且要求它**不低于 merge-base 处的版本**，降级即判 FAIL，防止 PR 把版本钉回旧规则；PR 中途正常升级则不受影响。CI 从 GitHub Release 安装所需的各个版本，可以缓存 | 所有项目 |
| ② | 未固定版本、且仓库本身含协议本体（agateon）：使用 **merge-base 处的 `agate/`**，即 `git worktree add <merge-base>` 后取其中的协议 | agateon |
| ③ | 其他未固定版本的项目 | **FAIL**，提示"未固定协议版本，无法可信回放；请写 `.agate-version`" |

回放时显式设置 `AGATE_ROOT` 指向选定的协议，不依赖 `~/.agate`。

**边界**：PR 同时修改了 workflow 或协议本体时，CI 无法独立判定"新规则是否合理"，只能依靠 SELF-GATE 的人工独立评审。回放 commit-msg hook 能保证这次评审**留下了痕迹**（见 §1 的边界）。

**4. 只在 CI 中做的额外检查**

| 检查 | 内容 |
|---|---|
| 新任务等级 | 新增任务目录的 `contract_level`，必须 ≥ **merge-base** 处 `LEVELS.yaml` 的最大等级。分支在途中如果跨越了协议升级，merge-base 处仍是旧等级，因此不会误报 |
| 账本前缀与事件规则 | 对 `<base>..HEAD` 中每个变化过的账本做最终状态检查。即使不逐提交回放（squash 仓库的 push）也照常执行 |

**5. 删除的代码**

- 按 `task_id` 拼路径的逻辑；
- 与 `.gate-result.json` 的对照。

`check-gate` 对不存在的任务目录改为返回 1，这一项随批 A0 hotfix 先行。

**6. 前提与代价**

- CI 检出必须设置 `fetch-depth: 0`。
- 回放耗时：按本节规格回放 TAG0042 PR 的 16 个非合并提交，使用 merge-base 协议，同时回放 pre-commit 和 commit-msg：全部 rc=0，单个 0.13–1.89 秒，合计约 15 秒 `[自述，R4 评审实测]`。E4 用于在实现之后复测。
- 把 agateon 的 `gate-backstop` 设为 required，需要用户**明确许可**。
- peekview 需要**新增** CI job，并写 `.agate-version`；UPGRADING 给出 GitHub 示例和 GitLab 等价写法。

### 2.5 要求项由契约决定（批 A1，修复 F3）

对非 legacy 任务，`judge` 和 `evidence_ref` 是否生效由快照的 `requires` 决定，**不再读** `judge.enabled` 或 `created`。以下消费方统一改为调用 `requirement_active(task_dir, <name>, <phase>)`（`phase` 是该要求项所属的阶段，与 `at_phase` 比较，见 §2.2）：

| 要求项 | 消费方 |
|---|---|
| judge | `check-gate.py:767`、`gate_p65`（`:1219`）、`pre-commit-gate.py:157`、`agate-next.py:266` |
| evidence_ref | `agate_common.is_new_task_for_evidence_ref`（`:1707`）及其消费方 `check-p6-evidence.py:187`、`check-p6-provenance.py:479` |

level 1 设置 `requires: {judge: true, evidence_ref: true}`。legacy 任务保持现有逻辑。

### 2.6 创建时间是系统事实（批 A1）

- 非 legacy 任务：创建时间取创建事件的 `ts`；P1 的 `created` 不被任何判定读取，setter 也拒绝写入。
- legacy 任务：照旧读取 P1 的 `created`。

### 2.7 `.state.yaml` 由工具写入（批 A3；RM-AG0059 ①；修复 F14 的 phase 部分）

```yaml
phase: P4                     # agent 声明，只能经 agate-state-set 写入
cancelled: {reason: "…"}      # 可选，agent 声明
meta:
  title: "…"
  priority: high|medium|low
  depends: [TAG0042]          # 元素必须是已存在的任务 ID
```

**`status` 改为系统字段。** 它由 `phase` 和 `cancelled` 现算：PAUSED → paused，READY → ready，DONE → done，有 `cancelled` → cancelled，其余 → active。
- **非 legacy 任务**：`.state.yaml` **不写** `status`，写了即判 ERROR，以免文件中残留过时的值。`agate-state-yaml-check.py:34` 中"status 必填"只对 legacy 任务生效。
- **legacy 任务**：现有 13 种取值不受影响。

`active-tasks.md` 是主 Agent 维护的**非权威视图**，不被任何 gate 读取。改由 `.state.yaml` 渲染属于 RM-AG0059 第 ② 项，不在本任务范围内。

新增 `agate-state-set.py`：

```
agate-state-set.py <TASK_DIR> phase <Pn|PAUSED|READY|DONE>
agate-state-set.py <TASK_DIR> meta.priority low
agate-state-set.py <TASK_DIR> cancel --reason "…"
agate-state-set.py <TASK_DIR> --list
```

**写 phase 的规则**：

- **转换检查**：先把 `check-state-transition.py` 中 `main()` 的判定重构成纯函数 `check_transition(old_state, new_state, task_dir) -> [errors]`，`main()` 和 state-set 共用这一个函数。state-set 以 **HEAD 版本**作为 `old_state`，与 pre-commit 口径一致，因此连续两次 state-set 后，提交时的判定结果不会和工具当时的判定不同。
- **回退时**：同时写入 `retries[...]`，满足现有规则（`check-state-transition.py:392-400`）。
- **写入方式**：原子替换文件后执行 `git add`，不写事件。

**事件由 pre-commit 统一写入**：

- 把 `pre-commit-gate.py` 的 2h.1c（写入 `state_transition`）和 2h.1d（`git add` 账本）**一起**移到 2g 的 `continue` **之前**，使进入 PAUSED、READY、DONE 的转换也被记录，并且随本次提交入库。现状下 TAG0042 的账本里没有 P8→READY 这一条 `[自述，R2 评审实测]`。
- `agate-next` 通过时只打印建议，例如"下一步：`python3 <agate_root>/scripts/agate-state-set.py <dir> phase P5`"，**不再追加** `state_transition`，以消除重复记录（TAG0042 实施评审 I-6）。

**不写入 `.state.yaml` 的字段**：`created` 和 `updated` 分别取创建事件和账本尾行的 ts，由读取方现算。这一点依赖上面"所有转换都写事件"的改动。

**gate 侧**：`check-state-yaml.py` 对非 legacy 任务按快照复验。

### 2.8 修复 F8（批 A0）

`pre-commit-gate.py:370` 改为：

```python
append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})
```

并补一条用例，验证事件**真实落盘**。

### 2.9 义务的执行方式由机械核验（批 A4，修复 F13）

**必经路径**定义为：hook 的入口（`pre-commit-gate.py`、`commit-msg-self-gate.py`、`pre-push-gate.py`）加上 `check-gate.py`，以及从这些入口出发、按字面量脚本名做闭包得到的调用点。**CI 路径不计入**：agateon 的 workflows 不会随协议一起装到使用者项目里。

`obligations.yaml` 中的每条 M 义务新增两个字段：

```yaml
- id: OBL-P8-02
  disposition: M
  enforced_at: {file: check-gate.py, function: gate_p8}       # call 可选，仅用于"调用另一个脚本"的义务
  test: agate/tests/unit/test_check_p8_delivery.py::test_obl_p8_02_delivery_missing_blocks
```

`check-obligations.py` 的核验分为以下几类：

| 归宿 | 核验 | 性质 |
|---|---|---|
| **M** | ① `function` 存在于 `file` 中（用 `ast`）；② 该函数可从必经路径的入口到达：`gate_pN` 经 `handlers` 表（`check-gate.py:1640`），pre-commit 的各步骤属于 `main`，在文件内用 ast 建调用图；③ 如果填了 `call`，同一个 `ast.Call` 节点的参数中必须包含全部字面量（含参数，例如 `--retreat-coverage`） | 机械判据 |
| **M** | ④ `test` 指向的 pytest 节点必须存在，且测试名或 docstring 中要引用该义务的 id | 机械判据 |
| **M** | 60 条 M 中有 28 条的 `script` 就是 `check-gate.py` 或 `pre-commit-gate.py` 本身，义务由函数内部的分支实现，并没有一次"调用" `[自述，R3 评审]`。对这类义务，①–③ 只能证明"函数还在"，所以实质证明交给 ④ 和**负向控制**：删掉该义务对应的判断分支，`test` 必须转红。A4 的负向控制以 mutation 方式抽样执行，每批至少覆盖本批新增或改动的 M 项 | 机械判据（抽样） |
| **M** | 调用条件（例如"只在 P8"）是否覆盖了该义务所属的阶段 | 判断项，交给评审 |
| **R** | 新增 `review_output: <阶段产出文件名>`，该文件必须是 check-gate 会校验其存在、且校验 `agent ≠ main` 的评审产出。目前只有 P1、P2、P4 的评审满足这一条 | 机械判据 |
| **R** | 找不到合格评审产出的 R 项改标为 C。预计约 20 条，其中包括 P0 的 3 条 `[自述，R2 评审]`，以 A4 实测为准 | — |
| **CI 才执行的义务** | 归入 `scope: protocol-repo`，单独统计，不计入 M 占比 | — |

这一节就是 RM-AG0094"复犯即落成机械判据"的落点：一条义务若想算作 M，必须有一个能被删改打红的测试作为凭证。

**基线重设**：首次核验后会改标 F13 中的 4 条 M 以及若干 R，M 占比随之下降。这一次通过 `baseline.reset: {reason, from: "60/123", to: "<新值>"}` **显式重设**，并写进 CHANGELOG。之后恢复"只增不减"。

---

## 3. 写入工具与契约单源（批 B）

### 3.1 逐文件字段契约

快照的 `files` 节，以 P6 为例：

```yaml
files:
  P6-acceptance.md:
    fields:
      results:
        writer: agent
        required: true
        key: bdd
        render: results_table
        schema:
          type: array
          items:
            type: object
            required: [bdd, verdict, evidence]
            additionalProperties: false
            properties:
              bdd:           {type: string, pattern: "^[0-9]+[a-z]?$"}
              verdict:       {enum: [PASS, FAIL]}
              evidence:      {type: array, minItems: 1, items: {type: string}}
              vision:        {type: string}
              manual_review: {type: string}
      pass: {writer: system, derive: "count(results, verdict == PASS)"}
      fail: {writer: system, derive: "count(results, verdict == FAIL)"}
```

**字段属性**：

| 属性 | 含义 |
|---|---|
| `writer` | `agent` 或 `system` |
| `required` / `required_if` | 必填 / 条件必填 |
| `key` | 列表元素的主键 |
| `id_prefix` | ID 前缀 |
| `render` | 渲染种类 |
| `derive` | 系统字段的推导式，只允许 `count`、`sum`、`union`、`any` 四个算子 |

**迁移**：
- `agate-frontmatter-check.py` 的 `SCHEMAS` 是自定义的 `{required, enums, types, min_values}` 格式，**先转换成 JSON Schema 子集**，再移入快照；legacy 任务用转换前的冻结副本。
- `phases.yaml` 的 `task_fields` 保留，`check-structure-consistency` 新增检查：`task_fields` 必须是快照字段的子集。

### 3.2 校验器合并（修复 F14 的校验器部分）

- 从 `check-yaml-schema.py` 中抽出 JSON Schema 子集校验器，做成库 `agate_schema.py`。支持的关键字：`type`、`enum`、`required`、`properties`、`additionalProperties`、`items`、`minItems`，**只新增** `pattern`。
- `check-yaml-schema.py`、`agate-frontmatter-check.py`（格式转换后）、`agate-config.py:_validate_node` 三处都改为调用这个库。
- 库同时提供 `derive()` 和 `render()`。
- 等价守护：测试检查 `agate/scripts/*.py` 中不存在第二个递归 schema 校验实现。

### 3.3 读取路径

对非 legacy 任务，`agate-md-field-get` 读取 `writer: system` 的键时**按 `derive` 现算**，忽略文件里的值。经 md-field-get 取值的消费方（check-gate 中 P6、P7 的计数，`check-p6-provenance.py`，`agate-feedback.py`）不需要改代码。

### 3.4 写入工具

**任务数据**：`agate-md-field-set` 支持 7 种操作。

```
FILE=<path> agate-md-field-set.py set    <key> <value>
FILE=<path> agate-md-field-set.py append <key> k=v [k=v …]     # 或 --json '<obj>' / --from-file F / stdin
FILE=<path> agate-md-field-set.py upsert <key> <主键值> k=v …
FILE=<path> agate-md-field-set.py remove <key> <主键值>
FILE=<path> agate-md-field-set.py --list
FILE=<path> agate-md-field-set.py explain <key>
FILE=<path> agate-md-field-set.py render
```

- **兼容旧写法**：`<key> <value>` 等同于 `set`。
- **值的解析**：`k=v` 按 schema 转换类型；`--json` 和 stdin 用于规避 shell 引号问题（E1）。
- **自动编号**：ID 由工具生成，格式为 `<任务目录内相对路径去掉 .md>:<前缀><n>`（§6）。
- **系统字段拒写**：拒写时说明这个值从哪里来。
- **写入流程**：每次写入后校验整个 frontmatter，原子替换文件，再重新渲染。
- **不加锁**：并行时每个子任务写自己的文件。语料中有 58 个 `P4-implementation-*.md`（两个仓库合计，例如 TAG0042 的 `P4-implementation-batch1..6.md`），check-gate 本来就会聚合 `P4-implementation/` 目录（`check-gate.py:1311-1314`）`[读码]`。
- **证据字段**：解除一期的写入禁令。
- **不写留痕事件**：本地没有密钥，写入工具的定位是"保证写对"，不是可信边界。

**项目声明**：`agate-config` 补齐 `set`、`unset`、`explain`（修复 F14 的 set 部分）。

```
agate-config.py set <点分路径> <value> [--append]
agate-config.py unset <点分路径>
agate-config.py explain <点分路径>
```

- 写入后用 `agate_schema` 复验，然后原子写入。
- `project-config.schema.json` 的每个属性都补上 `consumed_by`，由测试核对它与源码中的实际读取点一致。
- 项目根统一用 `agate_common.project_root()` 解析：先用 `git rev-parse --show-toplevel`，失败时回退到 cwd（TAG0042 实施评审 I-9）。`agate-run.py:155`、`agate-config.py:215` 同步修改。

### 3.5 渲染块

```
<!-- AGATE:RENDER results BEGIN（agate-md-field-set 生成，勿手改） -->
| BDD | 结论 | 证据 |
|---|---|---|
| 1 | PASS | P6-evidence/bdd-01.log |
<!-- AGATE:RENDER results END -->
```

gate 的检查：
- 块必须恰好出现一次；
- 两侧都把 CRLF 规范成 LF 后，块内容与 `render(value)` 逐字节相等。先例是 `pre-commit-gate.py` 的 2p 段（TAG0009）；
- 缺失或被改动时，给出修复命令 `agate-md-field-set.py render`；
- 这项检查纳入 `windows_smoke`。

### 3.6 gate 侧与绊线

**gate 侧（非 legacy 任务）**：
- 声明文件（§6）必须有 frontmatter（修复 F10）；
- 按任务等级对应的快照校验，不回退到正文正则；
- 报错时附带由 `explain` 模板生成的修复命令。

**绊线**：定义在快照中，扫描声明文件的正文。排除以下内容：围栏代码块、`AGATE_CARD` 块、渲染块、行内代码、以反引号开头的行。

| 绊线 | 命中条件 | 指向 |
|---|---|---|
| **T1** | 正文出现**正向**标记的声明形态，只用 `markers.yaml` 的 `default` 口径。涉及的标记：`SCOPE+`、`SCOPE_RESOLVED`、`DESIGN_GAP`、`DESIGN_GAP_REVIEWED`、`NEED_CONFIRM`、`SUGGEST`、`PROD_TOUCHED`、`BLOCKER`、`DEVIATION-CRITICAL`、`CODE_MAP_UPDATED`、`CODE_MAP_EXEMPT`（其中未登记的 5 个由批 E 补登记，§6） | §4、§6 中对应的字段 |
| **T2** | P1 中的 BDD 标题匹配 `^#{1,6}\s*\**BDD-`，但不匹配 `^#### BDD-[0-9]+[a-z]?:` | 统一为 `#### BDD-N:` |
| **T3** | P6、P6.5 的正文中，在渲染块之外出现严格结论行 `- (PASS\|FAIL\|NEEDS-REVISION) BDD-N` | `results` / `criteria` |
| **T4** | 现有的 PROD_TOUCHED diff 扫描，保持原样 | §4 |

> ⚠️ **[已被取代 2026-10-07]** 本行「保持原样」表述已过时——由 `P2-design.md §3.1` 的 F4 规格取代：`markers.yaml` 的 `PROD_TOUCHED.lead_variant` 改 `default`、pre-commit 用 `agate_markers.pattern()`、扫描面 = 任务目录内全部暂存 `*.md` 新增行、**T4 为唯一 PROD_TOUCHED 安全门**（T1 标记表去掉它）、否定写法继续阻断 + 专门指引。批 C 按 P2 §3.1 实现。（原文保留，仅作决策史。）

**T1 默认判为 ERROR**：字段是必填的，如果 agent 按旧习惯把内容写进正文，这些内容会**静默丢失**。

**影响面** `[实测]`：按上述口径，存量语料中 agateon（v0.79.0）命中 393 行，涉及 31 个任务；peekview 命中 233 行，涉及 42 个任务。这些基本都是按旧习惯写的真实声明。

**误报控制**：批 B 启用 ERROR 之前，必须完成 E3 抽样，要求"引述 / 讨论"类误报为 0。如果做不到，**P7、P8 评审稿中的 T1 降为 WARNING**，并且这些文件中的声明必须同时写入字段。例如 R2 评审抽到的折行续写：TAG00xx `P7-consistency.md` 中的 `[SCOPE_RESOLVED]）以"无需存在"方式满足`。

**协议文档改写面**：`agate/**/*.md` 中提及这些标记的文本为 167 行，分布在 30 个文件（上界口径：12 个标记名的任意出现，命令见附录 A；只计正向或已登记标记时为 159–165 行）。各批 P1 给出逐行清单。

---

## 4. 生产接触（批 C）

- 快照的 `primary_outputs` 指定每个阶段的主产出：P1–P8、P6.5 各一个，P5 为 `P5-test-results/unit.md`。
- 主产出的 frontmatter 增加 `prod_touched: true|false`（agent 声明，必填）；值为 true 时，`prod_touched_detail` 必填。
- pre-commit 的处理：

  | 情况 | 结果 |
  |---|---|
  | 缺少该字段 | ERROR，附修复命令 |
  | 值为 true，且当前不在 PAUSED | 中止提交 |
  | 当前在 PAUSED | 写入 `prod_touched_in_paused` 事件（依赖 §2.8） |

- **T4 优先**：正文扫描命中、而字段写的是 false 时，中止提交。

> ⚠️ **[已被取代 2026-10-07]** 本处「T4 优先」表述已过时——由 `P2-design.md §3.1` 的 F4 规格取代（同上：单一来源 `markers.yaml default` + `agate_markers.pattern()`、扫描面 = 任务目录内全部暂存 `*.md` 新增行、**T4 为唯一 PROD_TOUCHED 安全门**、否定写法继续阻断 + 专门指引）。批 C 按 P2 §3.1 实现。（原文保留，仅作决策史。）

---

## 5. 验收结论与证据绑定（批 D，含 RM-AG0097）

**前置条件**：`agate-run` 的基线比对缺陷（TAG0042 实施评审 I-2）必须先以 hotfix 修复——普通运行只返回命令自身的退出码；基线比对只在 `--baseline` 时进行，并实际打印 diff。

### 5.1 P6

`results` 的结构见 §3.1；`pass`、`fail`、`regression_pass` 是系统字段。

非 legacy 任务的判据：

| # | 判据 | 取代 |
|---|---|---|
| D1 | `results` 的 `bdd` 集合与 P1 中 `^#### BDD-([0-9]+[a-z]?):` 的集合**相等**，且不重复（修复 F1-B、F1-C） | 审计 3 的条数比较 |
| D2 | 所有 `verdict == PASS`（修复 F1-A） | 自报的 `fail` |
| D3 | 每条证据引用都能经 `resolve_evidence_ref()` 解析到一个非空文件，且该文件未被 ignore；在 pre-commit 中还要求它已跟踪或已暂存（修复 F9） | 审计 1a |
| D4 | `P6-evidence/` 下每个非隐藏文件至少被引用一次 | 审计 1c |
| D5 | 不同文件内容相同时给 WARNING，提示"可以共享引用" | 新增 |
| D6 | PASS 条目引用的日志，如果带 `EXIT_CODE` 尾行，其值必须为 0 | 审计 5 |
| D7 | 证据 JSON 与结论一致 | 审计 6 |
| D8 | 涉及 UI 的条目：截图必须带 `vision`；如果没有视觉能力（GAP），改为必须带 `manual_review` | 审计 4 |
| D9 | 审计 7 改为从 `results` 读取 | — |
| D10 | 渲染块一致 | — |

非 legacy 任务不再运行以下检查：`check-p6-format.py`（包括 2h 段）、`agate-evidence-consistency.py`、provenance 中的正文解析。`agate-extract-context.py:190-211` 改为经 md-field-get 取值。

### 5.2 P6.5

- `criteria: [{bdd, verdict: PASS|FAIL|NEEDS-REVISION, evidence}]`；
- `status`、`partial` 由 agent 声明；
- `criteria_total`、`criteria_passed`、`verdict_evidence` 是系统字段；
- `check-judge-verdict` 第 4–6 条改为读取 `criteria`；信息隔离扫描不变。

### 5.3 证据引用与 `agate-run --task`

`resolve_evidence_ref(task_dir, ref)` 是唯一的引用解析入口，接受两种形式：

- **任务目录内的相对路径**；
- **`run:<k>`**：指向 `<task>/runs/<k>.log`。其中 `k` 由 `agate-run` 按任务自增分配，并记录在 `cmd_run` 事件里。

`agate-run` 新增 `--task <TASK_DIR>` 参数（等价于设置 `AGATE_TASK_DIR`）。指定后：

- 输出写入 `<task>/runs/<k>.log`：头部记录 cmd、cwd、`git_head`、起止时间，尾行为 `EXIT_CODE: n`；
- 这个日志**必须未被 ignore**，因为它是任务证据，需要入库。它与 `.agate-evidence/` 这个基线缓存是两回事；
- `cmd_run` 事件增加 `k`、`log`、`sha256` 三个字段；D3 校验文件的 sha256 与事件记录一致。

### 5.4 入库

- `gitignore-fragment.txt` 增加 `!agate-workspace/tasks/**/P6-evidence/**` 和 `!agate-workspace/tasks/**/runs/**`，并注明**取反规则必须写在 `*.log` 之后**。
- 真正起约束作用的是 D3；legacy 任务只给 WARNING。
- peekview 按 UPGRADING 调整。

---

## 6. 成对声明（批 E）

**声明文件**：快照的 `declaration_files` 覆盖各阶段主产出、`*-review.md`、`P4-implementation-*.md` 和 `P4-implementation/**/*.md`。声明字段可以写在任意声明文件的 frontmatter 里，由 gate 跨文件聚合。ID 的格式是 `<相对路径去掉 .md>:<前缀><n>`，每个文件独立编号。

| 声明 | 结构 | 判据 |
|---|---|---|
| 待确认 | `need_confirm: [{id: NC<n>, text, status: open\|confirmed, resolution}]`<br>`suggest: [{id: SG<n>, text}]` | P1 中存在 open 条目 → 不通过。`need_confirm` 必填，**空列表即表示"无"** |
| 范围增补 | `scope_plus: [{id: SP<n>, text}]` | P1 的 `scope_resolved` 必须覆盖全部聚合到的 id；出现悬空 id → ERROR。`check-scope-resolved.py`、`check-retrospective.py` 改为读取聚合结果 |
| 设计缺口 | P4 各文件中的 `design_gaps: [{id: DG<n>, text}]` | P7 的 `design_gap_reviews: [{gap, verdict: accepted\|rejected\|followup, checked_against: [ref…], basis, note}]`：`{gap}` 必须与 `{DG id}` 集合相等；`checked_against` 不能为空；`basis` 必填（见下） |
| CODE-MAP | P4 各文件中的 `code_map: [{file, status: updated\|exempt, reason}]` | P7 的 `code_map_reviewed` 与之集合相等 |
| 一致性发现 | P7 的 `findings: [{id: F<n>, severity: blocker\|deviation_critical\|deviation\|note, text, status: open\|resolved, resolution, evidence}]` | 存在 open 的 blocker 或 deviation_critical → 不通过；`resolved` 必须带 `resolution` 和 `evidence`；所有计数都是系统字段 |

**`basis`**：取值为 `in_bdd`、`out_of_scope` 或 `followup:DEBT<n>`。

- `followup` **只接受 DEBT 编号**。tech-debt 是协议自有、带 schema 的登记表，在 agateon、peekview、X 上都存在。roadmap 的格式因项目而异：peekview 没有 RM 编号，X 没有 roadmap，所以不能用。
- gate 会查证两件事：该 DEBT 条目确实存在；它的 `source_ref` 字段**回指** `<task_id>:<DG id>`，形成双向绑定。需要在 tech-debt schema 中新增 `source_ref` 字段，由 `agate-debt-check` 校验。
- RM 编号可以写在 `note` 里作为补充，不参与判定。

**设计意图**：TAG0042 的 F12、`gate_layer` 这类问题，都是"以 BDD 没要求为理由接受，然后就没有下文"。`basis` 要求每一次接受都留下一个可追踪的去向。

**补登记标记**：`markers.yaml` 补登记 BLOCKER、DEVIATION-CRITICAL、CODE_MAP_UPDATED、CODE_MAP_EXEMPT、SUGGEST，这 5 个标记只用作 T1 绊线。

结构化本身并不阻止 agent 把 BLOCKER 置为 resolved，所以 F2 的修复范围是"计数不会被汇总值盖住"。

---

## 7. 用关键词代替"做没做"的判定（批 F，含 RM-AG0085、RM-AG0087、F12）

| 现状 | 改为 |
|---|---|
| P2 UI 节只看关键词 | `ui_design: {shape, dimensions: {<维度>: {status: covered\|na, reason, ref}}}`。必填维度由 `shape` 决定（在快照中定义）；`na` 必须带 `reason` |
| P1-review 只要出现任意 `BDD-数字` | `reviewed_bdds` 必须**等于** P1 的 BDD 集合 |
| P7 交叉引用只看关键词 | 改为 §6 中必填的 `checked_against` |
| 骨架用子串判断（RM-AG0085） | **对所有任务**：`check-gate.py:964` 改为标题级匹配，并补回归用例；对非 legacy 任务另加结构化字段 |
| `phases` 与正文裁剪不一致（RM-AG0087） | 新增 `pruned: [{phase, reason, risk}]`。判据：`set(phases) ∪ set(pruned.phase)` 等于快照的 `phase_universe`，且两者不相交。可裁剪规则以 `check-pruning.py` 为唯一来源，它对非 legacy 任务改为读取 frontmatter |
| P8 `delivery` 用子串判断（F12） | `delivery: {method, ref, reason}`：<br>• `method` 是非空字符串，不枚举技术栈；取值为 `none` 时 `reason` 必填；<br>• `method ≠ none` 时 `ref` 至少要有 1 项；<br>• legacy 任务保留子串判断 |
| BDD 标题格式 | T2 |

**说明**：对 X 这类没有发版流程的项目，P8 仍会因为 version 和 CHANGELOG 收到 WARNING（`gate_p8` 中写死了这项检查）。根源在于 `release.preset` 没有消费方，不在本任务范围内（§9）。

**结构化的能力边界**：它把判据的下限从"提到一个词"提高到"逐项枚举、逐项给理由"，但证明不了"做到位了"，后者仍然由评审负责。

---

## 8. 存量兼容与迁移

**承诺**：legacy 任务的 **gate 退出码与 ERROR 集合不变**。允许的差异全部列在这里：

| # | 差异 | 性质 |
|---|---|---|
| 1 | `prod_touched_in_paused` 真实落盘 | 缺陷修复（§2.8） |
| 2 | 骨架改为标题级判定 | 缺陷修复（RM-AG0085） |
| 3 | 任务 ID 正则统一，`T090` 从 rc=1 变为 rc=0 | 放宽 |
| 4 | 改写或删除已有创建事件的账本 → ERROR | 只作用于非 legacy 任务的账本；前缀规则在历史上 0 次违反 |
| 5 | 新增"证据被 ignore"的 WARNING | 新 WARNING |
| 6 | `gate_run` 事件新增 3 个字段 | 账本字节变化 |
| 7 | `state_transition` 写入点改动：`agate-next` 不再写；进入 PAUSED、READY、DONE 时开始写 | 去重 + 补记 |
| 8 | `agate-ci-verify` 由恒 SKIP 或假 PASS 改为逐提交回放 | 修复 F15，CI 中可能出现新的 FAIL |
| 9 | `obligations.yaml` 改标并显式重设基线 | §2.9 |
| 10 | legacy 任务从 READY 或 DONE 回到 Pn → ERROR | §2.3 规则 6 |
| 11 | `check-gate` 对不存在的任务目录返回 1 | 缺陷修复（§2.4） |
| 12 | 没有暂存 `.state.yaml` 的任务目录也做 PROD_TOUCHED 扫描（§2.3 规则 7） | 安全门修复。legacy 任务可能出现新的 ERROR，其中也包括现行正则把否定写法 `[PROD_TOUCHED]: 无` 误拦的情况（F4）。R6 差分须单独统计这类新增 ERROR，并逐条列出 |

**R6 双向差分**：在 agateon 和 peekview 的副本上，按上述口径运行，跑完后核验两个真实仓库的 `git status --porcelain` 为空。

**现有测试**：pytest 全量必须全绿。只有以下两类允许改动用例：
- 第 7、8、10、11、12 条所涉及的用例；
- §2.3 中"新建任务目录并提交"的用例（改用 `init_task()`）。

批 A1、A2、A3 的 P1 要给出**逐条清单**，PR 中逐条说明。

**UPGRADING**：
- 新任务一律用 `agate-task-init` 创建，phase 一律用 `agate-state-set` 写入；
- 说明 `--adopt` 和 `--upgrade` 的用法；
- peekview 需要：调整 `.gitignore`（含取反规则的顺序）；**新增** agate CI job（给出 GitHub 示例和 GitLab 等价写法）；设置 `fetch-depth: 0`。

---

## 9. 与 TAG0042 已落地接口的关系

| TAG0042 接口 | 实际状态 `[读码]` | 本任务处理 |
|---|---|---|
| `agate.config.yaml` + `read_project_config` | 项目根声明，唯一的读取函数 | 不改；新增 set/unset/explain（§3.4） |
| `agate-config` 的 `_validate_node` | 第 3 处手写校验 | 合并（§3.2） |
| `agate-run` + `cmd_run` | 证据写入 `.agate-evidence`，且必须被 ignore；事件写入依赖 env；没有 gate 消费它 | 新增 `--task` 和任务内日志，供 `run:` 引用（§5.3）；基线缺陷由 hotfix 修复，作为批 D 的前置条件 |
| `agate-ci-verify` | 多任务时 SKIP；单任务时假 PASS | 改为逐提交回放 pre-commit（§2.4） |
| `obligations.yaml` + `check-obligations` | M 类由作者自标 | 改为 `enforced_at` 机械核验，并重设基线（§2.9） |
| `agate-next` 不预写 phase | phase 只能手写；事件重复记录 | 用 `agate-state-set` 写 phase；事件统一由 pre-commit 写入（§2.7） |
| P8 `delivery` | 子串判断 | 结构化字段（§7） |
| `phases.yaml` 的 `gate_layer` | 没有消费方 | **范围外**，建议单独登记 RM |
| `release.preset` | 只有一个枚举值，没有消费方 | **范围外**，建议单独登记 RM |

**TAG0038**：其度量字段登记进新一级快照的 `state` 节。

---

## 10. 分批与验收锚

- 每批独立 PR、独立 gate、独立评审。新增要求的批要登记新一级快照。
- 顺序：**A0 → A1 → {A2, B}**；A3、A4 与 A1 并行；**B → C → {D, E, F}**；D 另外依赖 I-2 hotfix。
- 每条验收锚都要先写失败用例并确认红灯。

| 批 | 内容 | 验收锚 |
|---|---|---|
| **A0**（hotfix） | F8 修复；`check-gate` 对不存在的目录返回 1 | ① PAUSED 留痕真实落盘<br>② 不存在的任务目录 → rc=1 |
| **A1** | §2.1–§2.3、§2.5、§2.6、ID 正则统一 | ① 以下操作均报 ERROR：追加降级事件；第 2 条 `task_created`；`task_created` 不在第 1 行；未登记的等级；手写低等级的新任务（本地检查）<br>② 用 init 建的任务：回填或删除 `created`，judge 和 evidence_ref 仍然强制；在 P6 改 `judge.enabled: false`，P6.5 仍然阻断（修复 F3a/b/c）<br>③ 新增没有创建事件的目录 → ERROR，用 `--existing` 补写后转绿；`git mv` legacy 目录后仍是 legacy，不报错<br>④ 改写或删除已有创建事件的账本 → ERROR<br>⑤ legacy 任务从 DONE 回到 P1 → ERROR<br>⑥ 修改已发布的快照，或新增快照不登记 → consistency ERROR；黄金 fixture 判定结果不变<br>⑦ 任务等级高于运行中协议的最大等级 → fail-closed<br>⑧ 只暂存产出、未改 phase 的提交：legacy 任务也做 PROD_TOUCHED 扫描；非 legacy 任务按被暂存产出所属的阶段重跑 gate（包括 HEAD 为 READY 的情况）<br>⑨ 生效等级按阶段确定：在 P7 迁入的任务，P4 散文中的 `[DESIGN_GAP]` 仍由旧读取器计数，若 P7 的 `design_gap_reviews` 没有覆盖 → ERROR；连续两次升级时，各阶段分别取自己对应的等级<br>⑩ 两仓副本上的 R6 符合 §8 |
| **A2** | §2.4 | ① 在副本上回放 TAG0042 PR 的 16 个非合并提交（PR 口径）以及合并后的 push（push 口径），**全部判 PASS**<br>② 在分支上用 `--no-verify` 提交一个会被 gate 拦下的改动，最终 HEAD 为 READY → 判 FAIL，并指出是哪个提交；push 口径同样判 FAIL。另外，READY 之后的一个 `--no-verify` 提交只改 `P8-release.md`、写入 `[PROD_TOUCHED]` → 判 FAIL<br>③ 用 `--no-verify` 提交协议本体改动、且没有 self-gate trailer → 判 FAIL（commit-msg 回放）<br>④ 某个提交删除了已有创建事件的账本 → FAIL；对 legacy 目录做 `git mv` → PASS<br>⑤ 手写低等级 `task_created` 并用 `--no-verify` 提交 → FAIL；在途分支跨越协议升级 → 不误报<br>⑥ 使用者项目未写 `.agate-version` → FAIL，并给出提示；PR 把 `.agate-version` 降级 → FAIL；PR 中途升级 → 不误报<br>⑦ 没有改动任务目录的 PR → SKIP，并给出原因；squash 仓库的 push 只做账本检查<br>⑧ E4 的耗时记录 |
| **A3** | §2.7 | ① `agate-state-set phase` 以 HEAD 为基准拒绝非法转换；连续两次 state-set 后提交，判定结果与工具一致<br>② 回退时同时写入 retries<br>③ 进入 READY、PAUSED 时写入 `state_transition`；`agate-next` 不再写<br>④ 非 legacy 任务的 `.state.yaml` 写了 `status` → ERROR；读取方得到的值是现算的 |
| **A4** | §2.9 | ① `check-obligations` 对 F13 的 4 条 M 报 ERROR<br>② M 项缺少 `test`，或 `test` 节点不存在 → ERROR<br>③ 负向控制：删掉 OBL-P8-02 对应的判断分支（以及本批抽样的其他 M 项），其 `test` 转红<br>④ 缺少 `review_output` 的 R 报 ERROR<br>⑤ 改标并重设基线后转绿；之后 M 占比下降仍判 FAIL |
| **B** | §3 | ① 7 种操作，以及 agate-config 的 set/unset/explain，都有往返用例<br>② 系统字段拒写；get 返回现算值<br>③ 缺少 frontmatter → ERROR<br>④ 渲染块被手改 → ERROR；CRLF 下行为一致<br>⑤ 修复命令真的能执行并转绿<br>⑥ 只剩 1 个 schema 校验实现<br>⑦ E3 误报为 0，或已落实降级方案 |
| **C** | §4 | ① 缺少 `prod_touched` → ERROR<br>② 值为 true → 中止提交<br>③ 正文写粗体 `**[PROD_TOUCHED]**`、字段写 false → 仍然中止<br>④ `[PROD_TOUCHED]: 无` 被 T1 指向字段 |
| **D** | §5 | ① F1 的 A/B/C 三种篡改全部转红<br>② 证据被 ignore → ERROR<br>③ PASS 条目的日志 `EXIT_CODE ≠ 0` → ERROR<br>④ `run:` 引用的 sha256 与事件不一致 → ERROR<br>⑤ extract-context 的计数等于现算值 |
| **E** | §6 | ① F2 转红<br>② P2-review 和 P4 分文件中的声明都被聚合<br>③ 并行写入不撞号<br>④ 集合不相等、出现悬空 id → ERROR<br>⑤ resolved 缺少证据 → ERROR<br>⑥ `followup:DEBT<n>` 中 DEBT 不存在，或没有回指 → ERROR |
| **F** | §7 | ① UI 维度标 na 却没有理由 → ERROR<br>② `reviewed_bdds` 不相等 → ERROR<br>③ RM-AG0085 的回归用例<br>④ 阶段集合不闭合 → ERROR<br>⑤ T2 能拦下 `### BDD-1:`<br>⑥ 按 F12 的方式篡改 → 转红 |

**每批都要满足**：
- pytest 全绿；consistency 0 ERROR；`count-tests.sh` 计数一致；
- 经过 SELF-GATE 独立评审，并留下 `self-gate-review:`；
- 卡片中每新增一条"必须"，都有脚本判据或报错路径，并登记进 `obligations.yaml`，再由 §2.9 核验。

---

## 11. 消费方 × 批次 × 改法

| 消费方 | 批 | 改法 |
|---|---|---|
| `agate_common.py` | A1 | 新增 `task_level`、`requirement_active`、`check_ledger_events`、`TASK_ID_RE`、`load_contract(level)`、`project_root()`；`is_new_task_for_evidence_ref` 改为调用 `requirement_active` |
| `check-events.py` | A1 | 调用 `check_ledger_events` |
| `pre-commit-gate.py` | A0 / A1 / A3 / B / C / D | A0：修复 F8<br>A1：在 2h.1b 之前新增"账本与新目录"步骤（对每次提交都执行）；对所有有暂存文件的任务目录做 PROD_TOUCHED 扫描，并对非 legacy 任务按被暂存产出所属的阶段重跑 gate（§2.3 规则 7）；修改 `_judge_enabled`<br>A3：把 2h.1c 和 2h.1d 一起移到 2g 之前<br>B：frontmatter 检查改为面向声明文件<br>C：`prod_touched`<br>D：非 legacy 任务跳过 2h 段 |
| `check-gate.py` | A0 / A1 / D / E / F | A0：不存在的目录返回 1<br>A1：`:767`、`gate_p65`<br>D：P6<br>E：P7 与 P4 核对表<br>F：P1-review、P2 UI、`:964`、`:1450` |
| `check-state-transition.py` | A1 / A3 | A1：legacy 任务重开 → ERROR<br>A3：抽出纯函数 `check_transition` |
| `agate-next.py` | A1 / A3 | A1：`_p6_judge_advance` 改为依据契约<br>A3：不再写事件；建议中给出 state-set 命令 |
| `agate-ci-verify.py` + `protocol-tests.yml` | A2 | 新增 `--base` 与按事件取范围（`--no-merges`）；`checkout -f` + `reset --soft` 逐提交回放 pre-commit 与 commit-msg hook；协议版本选择（`.agate-version`、协议仓库的 merge-base、否则 FAIL）；merge-base 等级检查；修改 workflow 需要用户许可 |
| `pre-commit-gate.py`（回放模式） | A2 | `AGATE_REPLAY=1` 时跳过会改动文件的修正步骤，只做校验；不写 `.gate-result.json` 和 `.gate-history.jsonl` |
| `check-obligations.py` + `obligations.yaml` | A4 | 核验 `enforced_at`（ast 可达性）、`test`、`review_output`；负向控制抽样；新增 `scope: protocol-repo`；重设基线 |
| `check-state-yaml.py`、`agate-state-yaml-check.py` | A1 / A3 | A1：统一 ID 正则<br>A3：meta 和 status 改为现算 |
| `check-protocol-consistency.py` | A1 | 快照冻结 CHECK；黄金 fixture |
| `check-p6-evidence.py`、`check-p6-provenance.py` | A1 / D | A1：`evidence_ref` 改为依据契约<br>D：改为读取 `results` |
| 新增 `agate-task-init.py`、`agate-state-set.py` | A1 / A3 | — |
| `check-yaml-schema.py` → `agate_schema.py`；`agate-config.py:_validate_node` | B | 合并，新增 `pattern` |
| `agate-config.py` | B | 新增 set/unset/explain；改用 `project_root()` |
| `agate-run.py` | B / D | B：改用 `project_root()`<br>D：新增 `--task`、任务内日志、事件字段 |
| `agate-frontmatter-check.py`、`check-frontmatter.py` | B | 格式转换后移入快照；legacy 任务使用冻结副本 |
| `agate-md-field-set.py`、`agate-md-field-get.py` | B 起 | 7 种操作；系统字段现算；`KNOWN_OPS` 随批扩充 |
| `check-structure-consistency.py` | B | 检查 `task_fields` 是快照字段的子集 |
| `agate-feedback.py` | B | 代码不改，补用例 |
| `check-p6-format.py`、`agate-evidence-consistency.py` | D | 非 legacy 任务不再运行 |
| `check-judge-verdict.py` | D | 第 4–6 条改为读取 `criteria` |
| `agate-extract-context.py:190-211` | D / E | 改为读取字段 |
| `check-scope-resolved.py`、`check-retrospective.py` | E | 改为读取聚合结果 |
| `agate-debt-check.py` + tech-debt schema | E | 新增 `source_ref` |
| `markers.yaml` | E | 补登记 5 个标记，只作绊线 |
| `check-pruning.py` | F | 改为读取 frontmatter 和 `pruned` |
| `agate-migrate-workspace.py` | A1 | 不改代码；补用例，确认改名检测下 legacy 任务不受影响 |
| conftest | A1 | 新增 `init_task()` |
| 卡片与角色文件（约 160 行，30 个文件） | A3–F | 按标记和 phase 写法逐行改写 |

---

## 12. 不做

- 不改 peekview 或其他项目。
- 不迁移 legacy 任务的格式。
- 不做看板渲染、`agate-rm`、`agate-idea`。
- 不引入签名。
- 不改 P0-brief 内嵌的 yaml，也不改 judge 的信息隔离扫描。
- 不处理 `gate_layer` 消费方、`release.preset`（建议各自单独登记 RM）。`agate-run` 的基线缺陷由 hotfix 处理，作为批 D 的前置条件，不在本任务内实现。

---

## 13. 代价与风险

| 项 | 判断 |
|---|---|
| agent 写结构化数据的摩擦 | 多一次命令调用，但报错能直接定位、修复命令可照抄 `[推断]`。由 E2 验证 |
| shell 引号 | E1：提供三个写入入口 |
| 旧习惯写法被 T1 拦下 | 存量 626 行（agateon 393 + peekview 233）。靠卡片改写和报错中附带的命令消化；E3 控制误报，降级方案已写进 §3.6 |
| 代码分支增多 | 快照是数据，代码按要求项分支；代码语义靠命名冻结和每级的黄金 fixture 防止回溯；R6 保护 legacy 路径 |
| CI 回放的耗时 | 与"改动任务目录的非合并提交数"成正比：TAG0042 PR 的 16 个非合并提交，单个 0.13–1.89 秒，合计约 15 秒 `[自述，R4 评审实测]`，见 E4 |
| CI 回放的协议版本 | 依赖 `.agate-version` 固定版本，没有固定的使用者项目会被 FAIL。协议仓库用 merge-base 的协议时，与开发者本机稳定版之间可能有差异，因此建议 agateon 也写 `.agate-version` |
| 规模 | 拆成 A0–A4、B、C、D、E、F 共 10 批，涉及约 30 个脚本加卡片（§11）。A0 先行；A1 是地基；A2 是可信锚点；C 是安全项 |
| 义务基线重设 | 一次性下降，必须显式说明，否则会被误读为倒退 |
| 依赖用户许可 | A2 的 CI required 设置需要用户许可；peekview 要新增 job |

---

## 14. 待核实

见 `exp-tag0050-task-data-contract.md`：

- E1：引号问题
- E2：往返成本
- E3：T1 误报抽样
- E4：CI 回放耗时

---

## 附录 A：复现

```bash
bash repro-tag0050.sh <agateon 仓库根> [<peekview 仓库根>]
```

- 脚本在 `mktemp -d` 创建的副本中运行，不写真实仓库。
- 依次输出：F1（A/B/C）、F2、F3a、F3b、F4、F8、F5、F9、F12、F13、F15（多任务）、T1 语料计数、F3c、F15b（单任务假 PASS）、协议文档中提及标记的行数（167 行 / 30 个文件）。
- 2026-10-06 在 agateon `720c97d3`（v0.79.0）和 peekview `4ea7b8f` 上运行，结论与 §0、§3.6 一致；运行后两个真实仓库的 `git status --porcelain` 均为空。
- 以下几项出自独立评审的实测，不在本脚本内：
  - **R2**（`review-r2.md`）：账本 166 次变化、0 次违反；legacy 任务 `DONE → P1` 在 `check-state-transition` 中返回 rc=0；TAG0042 账本缺少 P8→READY 转换记录。
  - **R4**（`review-r4.md`）：按 §2.4 规格回放 TAG0042 的 16 个提交，全部 PASS，合计约 15 秒；用 `--no-verify` 构造的违规提交回放结果为 rc=1；READY 之后只改产出、写入 PROD_TOUCHED 的提交，在现有 hook 下 rc=0。
  - **R3**（`review-r3.md`）：在 TAG0042 真实提交上的回放。按协议版本、合并提交、`checkout C -- .` 与 `checkout -f` + `reset --soft` 几种方式对照；单个提交的回放耗时；60 条 M 项中有 28 条以 gate 脚本本身作为 `script`。
