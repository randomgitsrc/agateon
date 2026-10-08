# TAG0050 设计独立评审 R2

- **评审对象**：`design-tag0050-task-data-contract.md`（修订版）、`P0-brief.md`、`exp-tag0050-task-data-contract.md`、`repro-tag0050.sh`、`review-tag0042-implementation.md`
- **基线**：agateon main `720c97d3`（v0.79.0），peekview main `4ea7b8f`
- **方法**：读码，以 v0.79.0 为准；运行 repro 脚本（脚本在自己的 mktemp 副本中运行）。所有写数据的实验都在 `scratchpad/review2/` 下进行，包括 `ag`（main 副本的克隆）、`runx`、`ci1`、`st`（最小仓库）。
- **日期**：2026-10-06

---

## 结论：REJECT（修订后重审；剩余问题都能靠改规格解决）

与 R1 相比，设计有明显进步：
- 取消清单，改为"无创建事件即 legacy"；
- 等级只升不降；
- 快照自成一体，并用 sha256 冻结；
- judge 改由契约决定；
- 声明跨文件聚合；
- 渲染块比对前做行尾归一。

R1 的 2 个 BLOCKER 和 10 个 MAJOR 中，有 8 项已经闭合。

但批 A 被设计称为可信锚点的 **CI 校验（§2.4）**，按现在的规格在两个参照项目上都起不到作用：
- peekview（直推 main）上恒为空集；
- agateon 典型 PR 的终态是 READY，不会重跑任何 gate；
- 设计说"保留现有逻辑"，而现有逻辑按 `task_id` 拼路径，实测会给出**假 PASS**；
- 验收锚 ⑧ 只要求"不是 SKIP"，这个假 PASS 恰好能满足它。

此外还有 7 个 MAJOR，集中在以下几处：
- B1 的残余降级路径；
- §2.3 遇到改名或迁移时的行为；
- §2.7 与现有 pre-commit 的不一致；
- §2.9 的"必经路径"无法从仓库提取；
- 漏掉的第二个日期门槛；
- 代码语义的回溯；
- 批 A 的规模。

---

## 一、R1 闭环表

| R1 项 | 判定 | 证据 |
|---|---|---|
| **B1** 追加降级事件 | **PARTIAL** | §2.2 规定：等级取创建事件，并允许 `task_upgraded` 单调递增；`task_adopted` 只能用于没有 `task_created` 的任务；追加降级 → ERROR，已写入 A-①。以下残余问题见 **M-N1**：<br>① 新事件规则只写在 `check-events.py` 中，但 pre-commit 只在 judge 启用、且已有 verdict 时才调用它（`pre-commit-gate.py:441-444`）。pre-commit 的主循环只处理暂存了 `.state.yaml` 的任务（`:227-232`），设计没有规定"每个被暂存的账本都要跑事件规则"；<br>② 删掉或截空账本 → `task_level()` 返回 None → 任务降为 legacy，设计没有把这种情况写成 ERROR 并纳入验收；<br>③ CI 不校验新任务的等级（§2.3 第 2 条只在本地检查），手写一个低等级的 `task_created` 再配合 `--no-verify` 就能过 CI；<br>④ 没有要求 `contract_level` 必须是 LEVELS 中登记过的等级 |
| **B2** 清单缺失 | **CLOSED** | §2.3 规定没有创建事件即为 legacy，conftest、fixture、repro 副本、R6 副本的行为都不变。新规则带来的副作用见 M-N3（既有 hook 测试） |
| **M1** P6 关掉 judge | **CLOSED** | §2.5 列出 4 个消费方，经 grep 核对完整（`check-gate.py:755/1230`、`pre-commit-gate.py:157`、`agate-next.py:273`）；`judge` 键对 agent 拒写；A-② 覆盖"P6 关掉 judge"。另有一个**同类**的日期门槛被漏掉，见 M-N4 |
| **M2** "账本是可信锚点"说过头 | **CLOSED**（措辞） | §1 的边界和 §2.4 都已改为"CI 才是锚点"，并写明 `fetch-depth: 0`。锚点本身能否生效，见 **B-N1** |
| **M3** 清单竞态、浅克隆、键的歧义 | **CLOSED** | 清单整体删除，改为"新增目录必须有创建事件"。改名和迁移场景下的新问题见 M-N3 |
| **M4** schema 收紧会回溯；摘要覆盖面 | **CLOSED** | 每份快照自成一体，包含 files、tripwires、primary_outputs、phase_universe、state 等各节；sha256 对 LF 归一后的原始字节计算，不再走 YAML 解析，也就绕开了日期类型和 `1`/`1.0` 的问题。schema 收紧只要复制出新一级快照即可。**但**代码定义的语义（render、derive、D 系列判据）仍然会回溯，见 M-N5 |
| **M5** T1 误报 | **CLOSED**（以 E3 为前提） | 只用 `default` 口径，排除行内代码和以反引号开头的行；启用前须通过 E3。复算 393/31 和 233/42 与设计一致。抽样中仍能看到折行续写造成的误报：TAG00xx `P7-consistency.md` 中有一行 `[SCOPE_RESOLVED]）以"无需存在"方式满足；…`。E3 的"误报为 0"大概率要靠降级方案收场，建议把 P7 降级为 WARNING 的退路写进 §3.6 正文 |
| **M6** CRLF | **CLOSED** | §3.5 规定两侧都归一后再比较，并纳入 windows_smoke |
| **M7** 消费方清单不全 | **PARTIAL** | §11 已补上 extract-context、md-field-get、check-pruning、scope-resolved、retrospective、feedback。仍漏掉以下几项：<br>① `is_new_task_for_evidence_ref` 的两个消费方（`check-p6-evidence.py:187`、`check-p6-provenance.py:479`），见 M-N4；<br>② `check-state-transition.py` 要重构成可复用的函数，见 M-N6；<br>③ `agate-migrate-workspace.py`，见 M-N3 |
| **M8** 声明落点与并行 | **CLOSED** | §6 规定在任意声明文件中声明、跨文件聚合，ID 带路径前缀，锁已删除。**小问题**：§3.4 引用的 `P4-implementation.md:159` 原文是"临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录"，讲的是临时文件，不能作为"各写各的产出文件"的出处 |
| **M9** prunable 双源 | **CLOSED** | §7 规定 `check-pruning` 是唯一来源，`phase_universe` 写进快照 |
| **M10** legacy 逐字节不变 | **PARTIAL** | 承诺已改为"退出码与 ERROR 集合不变"，并列出 9 项差异。但 §2.3 第 1 条会让既有的 hook 集成测试转红，例如 `test_pre_commit_hook.py:140-155` 新建 `tasks/T001` 后期望提交成功。这一点与 §8 的"既有用例不改"相冲突，也不在例外清单里，见 M-N3 |
| R1 MINOR 1–10 | 9 项 CLOSED | D5 已改为 WARNING；D3 要求已暂存；`resolved` 必须带 resolution 和 evidence；status 改为"新契约引入"；ID 正则已统一；校验器合并；锁已删除；gitignore 顺序已写明；BDD-15b 已兼容；`--upgrade` 已增加 |
| R1 过度设计"每批都升一级" | **OPEN**（MINOR） | §10 仍规定"新增要求的批要登记新一级快照"，B–F 每批都会新增，结果是 6 级、6 份几乎相同的全量副本 |

---

## 二、新发现

### BLOCKER

#### B-N1：§2.4 的 CI 锚点按现规格在两个参照项目上都不生效，验收锚 ⑧ 还会认可一个假 PASS

设计 §1 说"可信锚点是受保护分支上的 CI 校验"，B1 的残余防线也依赖它。但现在的规格有以下四处问题：

1. **base 的选取方式**：缺省取 `merge-base HEAD origin/<默认分支>`。在 push 到默认分支的场景下（peekview 直推 main，agateon 合并后在 main 上的 push run），HEAD 就是 `origin/main`，所以 merge-base 等于 HEAD，变更集为空，结果恒为 SKIP。
   - 实测：在 `ag` 副本上令 `origin/main = HEAD`，`git diff --name-only $(git merge-base HEAD origin/main)..HEAD` 输出 0 行。
   - peekview 的 `ci.yml` 中 agate 相关条目为 **0 处**（`grep -c agate` 的结果为 0）。也就是说，它不只是 `fetch-depth` 不对，而是根本没有这个 job，而 UPGRADING 只提了 fetch-depth。
   - X 使用 GitLab，MR pipeline 中未必有 `origin/<默认分支>`。
2. **READY/DONE 终态没有可重跑的对象**：
   - 现有逻辑对 `_NON_ADVANCING_PHASES` 直接 SKIP（`agate-ci-verify.py:27,118`）；
   - agateon 的 PR 通常在 PR 内就推进到 READY。例如 TAG0042 的合入提交 `720c97d3`，此时 `.state.yaml` 中是 `phase: READY`；
   - 结果是第 1 项检查对这类 PR 等于没做，中间任何一次 `--no-verify` 提交都发现不了。
3. **"保留现有逻辑"会保留一个假 PASS 的缺陷**：
   - 现有代码用 `task_dir = tasks_dir / task_id` 拼路径（`agate-ci-verify.py:126`），而真实的任务目录名是 `{ID}-{slug}`；
   - `check-gate` 对不存在的目录返回 0。
   - 实测（`review2/ci1`，单任务 TAG0037，phase 设为 P7，**删掉 P7-consistency.md**）：
     - `agate-ci-verify` 输出 `PASS: phase=P7 CI 重跑 exit=0`，rc=0；
     - 对正确路径 `tasks/TAG0037-install-package-model` 运行 `check-gate P7`，rc=1；
     - 对 `tasks/TAG0037` 运行，rc=0。
   - 测试 fixture 恰好把目录命名为 `tasks/T001`（`test_agate_ci_verify.py:68`），所以测试发现不了。
   - 另外，`.gate-result.json` 已被 ignore（`.gitignore:2`），在 CI 中永远不存在，"与 `.gate-result.json` 对照"这段代码在 CI 里是死代码。
4. **验收锚 ⑧** 只要求"输出 PASS 或 FAIL，不能是 SKIP"，上面第 3 点的假 PASS 正好能满足它。

**修改建议**：
- `--base` 在 CI 中必须显式传入，并在 §2.4 中写出各种事件的取值：
  - PR：`github.event.pull_request.base.sha`；
  - push：`github.event.before`，值为全零时回退到默认分支（`protocol-tests.yml:79-90` 已有同样的处理）；
  - GitLab：`CI_MERGE_REQUEST_DIFF_BASE_SHA` / `CI_COMMIT_BEFORE_SHA`。
  - 缺省值只供本地使用。
- 任务目录取自 diff 中的**实际路径**，并且只认含 `.state.yaml` 的目录（`tasks/active-tasks.md` 这类文件要排除）。删掉"按 task_id 拼路径"和"与 `.gate-result.json` 对照"这两段。`check-gate` 遇到不存在的任务目录时应返回 1。
- 对 READY/DONE/PAUSED 的任务，有两种做法：
  - 逐提交回放：对 `base..HEAD` 中每个改动了该任务 `.state.yaml` 的提交，在该提交的树上运行它当时的 phase 对应的 gate；
  - 至少在 HEAD 树上把 `phases` 中各阶段的 gate 全部跑一遍。
  - 两种做法选一种，写进 §2.4。
- 验收锚 ⑧ 改为：在一个分支上用 `--no-verify` 提交一个会被 gate 拦下的改动，最终 HEAD 为 READY，`agate-ci-verify` 必须 FAIL。push 到默认分支的场景也要给出一条同样的用例。
- UPGRADING 写明 peekview 需要**新增** job，而不只是改 fetch-depth。

### MAJOR

#### M-N1：B1 的残余降级与 legacy 后门

1. **事件规则在本地没有接线**。pre-commit 的主循环只处理暂存了 `.state.yaml` 的任务（`pre-commit-gate.py:227-232`），`check-events` 只在 judge 路径上调用（`:441-444`）。因此，一个只暂存了账本的提交（例如追加第 2 条 `task_created`，或者一条非法的 `task_upgraded`）在本地不会被拦下。
   - **建议**：在 §2.4 的"对每个被暂存的账本"这一步里，同时运行 §2.2 的事件规则。
2. **删除或截空账本 → 降为 legacy**。规格没有写明"暂存的是删除"时前缀规则怎么判。
   - **建议**：对 HEAD 中含 `task_created` 的账本，删除、截空或移走都判 ERROR，CI 中同样判 FAIL，并加入 A-①。
3. **CI 不校验新任务的等级**：手写 `task_created`、`contract_level: 1`，再用 `--no-verify` 提交，CI 会放行。
   - **建议**：CI 校验 `contract_level ≥ base 版本中 LEVELS.yaml 的最大等级`。跨越协议升级的分支，它的 base 仍然是旧等级，所以不会误报。另外要求 `contract_level` 必须是 LEVELS 中登记过的等级。
4. **重开 legacy 任务**：
   - 实测（`review2/st`）：`check-state-transition` 对 `DONE → P1` 和 `DONE → P7` 都返回 rc=0，因为 old_num 被当作 0（`check-state-transition.py:330`）。
   - 也就是说，把一个已完成的 legacy 目录拿来重做新工作，可以一直使用旧规则。
   - **建议**：非 legacy 化之后，legacy 任务从 READY/DONE 回到 Pn 判 ERROR，提示使用 `--adopt` 或新建任务。

#### M-N2：§2.9 的"必经路径集合"无法从仓库可靠提取；F13 的计数与 §2.9 自己的口径互相矛盾

1. **"required job"不在仓库里**。`protocol-tests.yml:19-22` 写明 required 集合"以 `gh api …/branches/main/protection` 为准"，是 GitHub 分支保护的设置，不在 yml 文件中。
2. **CI 路径对协议义务没有意义**。agateon 的 workflows 不会随协议安装到使用者项目中，peekview 的 CI 里 agate 引用为 0 处。对一份"协议级"的义务登记来说，只有 hook 和 check-gate 才是使用者项目中的必经路径。
3. **F13 的数字不自洽**：
   - repro 实测有 4 条：OBL-P2-12、X-10、X-17、X-19；
   - 设计以"`check-platform-assumptions` 在 CI 上运行"为由排除了 X-19，但它所在的 `platform-scan` job 是**非 required** 的（`protocol-tests.yml:17`）；
   - 按 §2.9 自己的定义，应该是 4 条，A-⑨ 写的"3 条"是错的。
4. **源码提取只能得到"出现过"，得不到"必经"**：
   - 对字面量脚本名做闭包可以算出 33 个脚本（本评审复算）；
   - 但其中很多调用带有条件：`check-changelog` 只在 P8 时运行（`pre-commit-gate.py:529`）；`check-structure-consistency` 只在文件存在时运行（`:461`）；2i/2j 只在 `gate_exit != 1` 时运行；`check-events` 只在 judge 路径上运行（`:441`）；
   - 而且只比较脚本名、忽略参数，例如 OBL-X-17 的 `--retreat-coverage`。
5. **R 项的影响面被低估**：check-gate 只对 P1、P2、P4 的评审校验 `agent ≠ main`（`check-gate.py:672/919/1007`）。R 项共 30 条，其中 P3、P5、P6、P6.5、P7、P8、X 的约 17 条也找不到合格的 `review_output`，不只是 P0 的 3 条。

**修改建议**：
- 必经路径定义为"hook 根（pre-commit、commit-msg、pre-push）+ check-gate，对字面量脚本名做闭包，并记录调用条件"；
- M 项的 `script` 必须与调用点的脚本名和参数一致，调用条件必须覆盖该义务所在的阶段；
- CI 路径一律不算，或者另设一个 `scope: protocol-repo` 类别，单独统计；
- F13 和 A-⑨ 改为 4 条；R 项的改标范围按实际计算后写入 §2.9。

#### M-N3：§2.3"新目录必须有创建事件"在改名、迁移、拆分、测试场景下的行为

1. **改名**：`git mv` 一个 legacy 任务目录，例如改 slug，新路径在 HEAD 中没有文件，于是判为"新目录"。这时无法修复：
   - `--existing` 写不到第 1 行，因为账本已有内容；
   - `--adopt` 写的是 `task_adopted`，不满足"必须有 `task_created`"。
2. **迁移**：`agate-migrate-workspace.py` 用目录级 `git mv` 迁移整个 tasks 目录（文件头注释第 4 步）。它以 `core.hooksPath=/dev/null` 提交，本地不受影响，但 CI 的第 3 项检查会把全部 legacy 任务判为 FAIL。修改 `.agate.env` 中的 `AGATE_TASKS_DIR` 也会有同样的结果。
3. **拆分、重建与未提交的账本**：pre-commit 在提交失败前就已经追加了 `gate_run`（2h.1b 在 2i 的拦截之前执行），`agate-run` 设置了 `AGATE_TASK_DIR` 时也会写入事件。这样一来，新目录的账本第 1 行可能已经不是 `task_created`，`--existing` 就无法补救。
4. **既有测试**：`test_pre_commit_hook.py` 共 56 个用例。按启发式统计，其中约 26 个会新建 `tasks/T001` 并期望提交成功，例如 `:140-155`。`test_agate_migrate_workspace.py` 中约有 9 个同类用例。这与 §8 的"既有用例不改"相冲突。
5. **"任务目录"的判定**：tasks 下还有 `active-tasks.md` 这类文件；peekview 有 11 个目录没有 `.state.yaml`（R1 已实测）。

**修改建议**：
- 判定"新目录"时使用 `git diff --cached -M --name-status` 做改名检测：如果账本是从 HEAD 中某个路径改名而来，就按原任务的状态处理；
- 只把含 `.state.yaml` 的目录视为任务；
- 规定第 1 条规则在 hook 的任何追加之前执行；
- `--existing` 只接受"账本未跟踪"的目录，可以前置写入 `task_created` 并重建哈希链；
- 迁移工具保留账本；
- 受影响的测试逐条列入 §8 的例外，或者让 conftest 生成的任务自带 `task_created`。

#### M-N4：漏掉了第二个日期门槛 `evidence_ref_required_since`，批 A 还会让新任务的证据引用强制失效

- `rules/dispatch.yaml:26` 中有 `evidence_ref_required_since: "2026-10-03"`。它由 `agate_common.is_new_task_for_evidence_ref` 读取 P1 的 `created`（`agate_common.py:1707-1721`，代码中明说是有意 fail-open），消费方是 `check-p6-evidence.py:187` 和 `check-p6-provenance.py:479`。它与 F3a 是同一类问题：把 `created` 改早或删掉，证据引用强制就失效。
- 设计 §2.6 规定，对非 legacy 任务，P1 的 `created` "不再被任何判定读取，setter 拒写"。但 §11 的批 A 没有改这个函数。结果是：从批 A 到批 D 之间创建的任务，如果没有 `created`，就会走 fail-open，**证据引用的强制在这段时间内关闭**。
- **修改建议**：
  - 批 A 把它改为 `requirement_active(task, "evidence_ref")`，level-1 快照中设 `requires.evidence_ref: true`；
  - F3 一节补上这一项；
  - A-② 增加"回填或删除 `created` 后，证据引用仍然强制"；
  - 全仓 grep `_since` 和 `read_p1_created`，确认没有第三个类似的门槛。

#### M-N5：快照只冻结了数据，代码定义的语义仍会回溯；"按要求项分支"覆盖不到这种情况

- 对纯 schema 的收紧，"复制成新一级快照"是自洽的：校验器是通用代码，旧快照不会用到新增的关键字。
- 但是快照里引用的 `render: results_table`、`derive: count(...)`、D1–D10、T1 的排除规则、`resolve_evidence_ref` 的解析规则，都是代码。修改任何一个渲染格式（例如给结果表加一列），所有非 legacy 在途任务的 D10 都会转红；修复 `additionalProperties` 的实现缺陷，也会对所有等级生效。sha256 只冻结快照的字节，冻结不了这些代码。
- **修改建议**：
  - 规定要求项的键和 `render`、`derive` 的种类名，一经发布语义即冻结；要改行为，必须新建一个名字（例如 `results_table_v2`），由新一级快照引用；
  - 为每一级保存一组**黄金任务 fixture**（一组应当通过、一组应当失败），CI 对所有等级跑一遍，结果不允许变化；
  - 把这一条写进 §2.1 的"规则"，以及 §13 的"代码分支增多"一行。

#### M-N6：§2.7 与 pre-commit、check-state-transition 的现状不一致

1. **没有可复用的"同一判定函数"**。`check-state-transition.py` 的 `main()` 自己读暂存区和 HEAD，并直接调用 `sys.exit`（`:250-422`）。它比较的是 **HEAD 与暂存区**，不是"当前 phase → 目标 phase"。如果在提交前连续执行 `state-set P8`、`state-set READY`，工具逐步检查会通过，pre-commit 却会拒绝 HEAD=P7 → READY（`:278-291`）。回退时要求同步增加 `retries[...]`（`:392-400`），state-set 也没法预先判断。
   - **建议**：重构出纯函数 `check_transition(old_state, new_state, task_dir)`，state-set 以 **HEAD 版本**为 old_state；并在 §11 中增加 `check-state-transition.py` 一行。
2. **"由 pre-commit 统一写入"并不成立**。pre-commit 对 PAUSED/READY/DONE 在 2g 步就 `continue`（`pre-commit-gate.py:360-372`），根本走不到 2h.1c。
   - 实测：TAG0042 账本中，P0→P8 每一步各有 **2 条** `state_transition`，I-6 属实；但**没有 P8→READY 这一条**，`.state.yaml` 却已经是 READY。
   - 因此 §2.7 中"`updated` 取账本尾行的 ts"在收尾提交后会是过时的值，进入 PAUSED 也没有任何记录。
   - **建议**：把 2h.1c 移到 2g 之前，使所有 phase 变化都写入事件。
3. **`status` 与 `phase` 重复**：`status: active|paused|ready|done|cancelled` 中，前 4 个值都能由 `phase` 推出，违反了原则 5"一个事实只有一个来源"。
   - **建议**：`status` 改为系统字段（由 phase 现算），只有 `cancelled` 作为 agent 声明，并经 `state-set` 写入。

#### M-N7：§6 中 `basis: followup:<编号>` 的查证不通用，可靠性也不够

- 设计要求"引用的编号必须真实存在于 roadmap 或 debt 中，由 gate 查证"，但三个项目的情况各不相同：
  - **peekview**：roadmap 在 `docs/roadmap/improvement-backlog.md`，以 `#` 序号（以及 `10b`、`15b` 这种）标识事项，**没有任何 RM 编号**；
  - **X**：没有 roadmap；
  - **agateon**：roadmap 的表格解析器遇到列数异常的行会整行跳过（RM-AG0077 ⑥ 已实测，RM-AG0056、RM-AG0059 已处于"隐形"状态）。
- 这与用户"阶段必须对所有项目通用"的原则冲突。另外，只查"编号存在"，并不能证明这个后续事项真的承接了这个设计缺口。
- **修改建议**：
  - `followup` 只接受 `DEBT<n>`。tech-debt.md 是协议自有、带 schema 的登记表，`check-debt` 和 `check-retrospective` 已经能解析 `task_id:`（`check-retrospective.py:53`）；
  - 同时要求该 DEBT 条目的来源字段回指 `<task>:<DG id>`，形成双向绑定；
  - RM 作为可选的补充引用，不参与判定。

#### M-N8：批 A 过大，应当拆分

- 批 A 现在包括：
  - 快照与冻结 CHECK；
  - task-init 的 4 种模式；
  - 事件规则；
  - legacy 判定；
  - 新目录规则；
  - 账本前缀检查；
  - ci-verify 改造（还需要用户许可调整 CI）；
  - judge 的 4 个消费方；
  - created 的处理；
  - state-set 与 agate-next 的改动；
  - ID 正则统一；
  - F8 修复；
  - 义务核验与基线重设。
- 合计约 13 个脚本、10 条验收锚。其中 §2.4、§2.7、§2.9 与"契约等级"之间**没有依赖关系**，而且各自都有上面提到的 MAJOR 或 BLOCKER。
- **建议拆分为**：
  - **A0（hotfix）**：F8 修复，以及 ci-verify 按 task_id 拼路径的假 PASS；
  - **A1**：等级、创建事件、legacy、新目录规则、judge 与 evidence_ref、created；
  - **A2**：CI 锚点（§2.4，依赖 A1 的事件规则）；
  - **A3**：state-set 与 agate-next（§2.7）；
  - **A4**：义务核验与基线重设（§2.9）。
- 其中 A3、A4 与 A1 可以并行。

### MINOR

1. **T1 列表中的 `SUGGEST` 没有登记**：`markers.yaml` 中没有 SUGGEST（8 个标记里不包括它），§6 新登记的 4 个标记里也没有。但 §3.6 说 T1"只用 markers.yaml 的 default 口径"，二者不一致。应当一起登记，或者从 T1 中删掉。
2. **§5.3 的 `run:<point>/<n>` 中 `<point>` 没有定义**。另外，`.agate-evidence` 基线 mismatch 时 `agate-run` 恒返回 1，此时 `EXIT_CODE` 尾行写什么也没有说明。应把 I-2 的 hotfix 列为批 D 的**前置条件**，而不是"范围外"。
3. **任务等级高于运行中协议的最大等级时，行为没有定义**。hook 来自 `~/.agate` 的稳定版；多人使用不同版本时，会出现快照不存在的情况。应 fail-closed，并提示升级协议。
4. **§2.4 历史验证的数字需要更新**：v0.79.0 上，全部提交对第一父提交共有 **166** 次账本变化，0 次违反（本评审复算）。设计里仍是 R1 在 a68d763 上的 133 次。
5. **F14 说有"3 套手写 JSON Schema 校验器"**：`agate-frontmatter-check` 的 `SCHEMAS` 其实是自定义的 `{required, enums}` 格式，不是 JSON Schema（`agate-frontmatter-check.py:41-99`）。合并时需要先转换格式，这项工作量应写进 §3.2。
6. **§7 的 delivery**：结构本身对 X 是通用的（`method` 为自由字符串，取 `none` 时必须给 reason）。但 X 的 P8 仍会收到 version 和 CHANGELOG 的 WARNING（`check-gate.py` gate_p8 中硬编码），根源是 `release.preset` 没有消费方（这一项已列为范围外）。建议在 §7 注明这一点，并与单独登记的 RM 建立关联。
7. **"每批都升一级"**：见闭环表最后一行。建议只在出现不兼容变化时才登记新等级。
8. **§2.2 的"校验任务目录不存在"**：应当是"不存在任何以 `{ID}-` 开头的目录"。peekview 中 T003、T004、T005 都有重名目录。

---

## 三、TAG0042 实施评审核实表

| 项 | 判定 | 证据与说明 |
|---|---|---|
| 基线数据 | 属实 | `a68d763..720c97d3` 共 17 个提交（16 个非合并提交）；`agate/` 下 54 个文件，+4793 / −784 |
| **I-1** ci-verify 恒为 SKIP | **属实，且被低估** | repro F15 输出 `SKIP … rc=0 任务目录数=42`。但实施评审没有发现：**单任务模式同样有缺陷**，按 `tasks/<task_id>` 拼出的路径不存在，`check-gate` 返回 0，结果是假 PASS（实测见 B-N1 第 3 点）；`.gate-result.json` 被 ignore，CI 中的对照逻辑永远不会执行。"required 不包含 gate-backstop"属实（`protocol-tests.yml:19-20`） |
| **I-2** agate-run 基线 | **属实，有一处小误差** | 最小仓库实测与表格一致：未 ignore 时 rc=1 → 首次 baseline rc=0 → 第 2 次 baseline rc=1 → 普通运行 rc=1，提示"diff 已客观报出"，但实际没有输出 diff。小误差是"所有任务共享同一槽位并**互相覆盖**"这句：基线只在文件不存在时写入（`agate-run.py:185-186`），所以不是互相覆盖，而是之后所有任务都与第一份基线比较；证据目录也可以通过 `paths.evidence` 配置。I-9 也一并复现：在子目录中运行时报"命令未声明" |
| **I-4** delivery 子串判定 | 属实 | repro F12：删掉字段、在正文中提及后，P8 rc=2；`check-gate.py:1450` |
| **I-5** M 类自标 | **属实，但计数口径有误** | `check-obligations` 只检查 disposition 和占比，属实。脚本法得到 **4 条**，比 I-5 多出 OBL-X-19，而 I-5 没有说明排除理由。OBL-X-19 运行在非 required 的 platform-scan 中，不应排除。R 项问题也不只 P0，见 M-N2 第 5 点。"60/123"属实 |
| **I-6** phase 手改与事件重复 | **属实，但建议不完整** | `_write_state` 已删除；TAG0042 账本中 P0–P8 每次推进都有 2 条 `state_transition`（已实测导出）。不完整之处在于：pre-commit 不写入 READY/DONE/PAUSED 的转换，删掉 agate-next 的那条事件后，转换记录需要另行补齐（M-N6 第 2 点） |
| I-3 / I-7 / I-8 / I-9（顺带核对） | 属实 | `gate_layer` 在 scripts 中读取方为 0；agate-config 的子命令只有 init/validate/get/list/show（`agate-config.py:216-227`）；F8 在 repro 中出现 TypeError；`agate-run.py:155` 和 `agate-config.py:215` 都用 `os.getcwd()` |
| 评价是否公允 | 基本公允 | "有条件接受"与证据相称；"做得好的部分"属实，例如 `check-state-transition.py` 中的 READY/DONE 前序规则。没有发现夸大，主要偏差是**低估**了 I-1 |

---

## 四、事实核实表

repro 于 2026-10-06 在 `720c97d3` 和 `4ea7b8f` 上运行。

| 项 | 判定 | 证据 |
|---|---|---|
| F1-A / B / C | CONFIRMED | A：check-gate rc=2，provenance rc=1；B：rc=2，provenance rc=0，只有 WARNING（20 vs 19）；C：rc=2 / rc=0，没有提示 |
| F2 | CONFIRMED | check-gate P7 rc=0 |
| F3a / F3b | CONFIRMED | 原值 rc=1 → 回填后 rc=2 → 删除后 rc=2；P6.5 没有裁决时 rc=1，关掉 judge 后 rc=0，提示"judge 机制未启用（历史任务），跳过"。**F3 不完整**，漏了 evidence_ref 门槛（M-N4） |
| F4 | CONFIRMED | 判定结果为 T/F/F/F/T；peekview `T039…/P4-progress.md:21` 原文为 `- [PROD_TOUCHED]: 无` |
| F5 | CONFIRMED | `TPV0091/P7-consistency.md:32`、`T083/P7-consistency.md:202` 与原文一致 |
| F7 / F8 | CONFIRMED | `agate_common.py:354`；TypeError（需要 2 个参数，实际传了 3 个） |
| F9 | CONFIRMED | agateon 引用 665 个、缺 9 个（涉及 8 个任务）；peekview 引用 173 个、缺 157 个（涉及 40 个任务），命中 `.gitignore:87 *.log` |
| F12 | CONFIRMED | rc=2 |
| F13 | **CORRECTED** | 脚本法得 4 条。"去掉 CI 上运行的那条后为 3 条"不成立，platform-scan 是非 required job（M-N2） |
| F14 | CONFIRMED（附说明） | agate-config 没有 set；第 3 套校验器在 `agate-config.py:104`。frontmatter-check 的格式不是 JSON Schema（MINOR 5） |
| F15 | CONFIRMED | SKIP，rc=0，42 个任务目录 |
| 设计中所有 `文件:行` 引用 | 23 处 CONFIRMED，1 处不准 | 正确的有：`check-gate.py` 的 1186/767/1232/1219/604/677/964/1332/1450/979；`pre-commit-gate.py` 的 157/348/370；`agate-next.py:266`；`agate_common.py:354`；`agate-frontmatter-check.py:217`；`agate-config.py` 的 104/215；`agate-run.py:155`；`agate-ci-verify.py:103`；`dispatch.yaml:17`；`markers.yaml:43`；`agate-extract-context.py:190-211`。**不准的**是 `P4-implementation.md:159`，原文讲的是临时文件（见 M8 一行） |
| §3.6 T1 影响面 393/31、233/42 | CONFIRMED | repro T1 段 |
| §2.4 账本变化 133 次、0 次违反 | 已过时 | 在 v0.79.0 上为 166 次、0 次违反 |
| brief：consistency 0 ERROR / 408 WARNING | CONFIRMED | 在 `review2/ag` 上运行，输出"仅有 408 个 WARNING，无 ERROR" |
| brief：30 个 .py 同时含 re 调用和产出文件名 | CONFIRMED | 用 brief 给出的命令复算为 30 |
| brief：8 个标记 | CONFIRMED | `agate_markers.names()` 返回 8 个 |
| brief / §3.6："167 行，分布在 30 个文件" | 近似 | 口径没有给出。按 T1 的 11 个正向标记复算为 165 行、30 个文件；按"已登记 + 新登记的 4 个"复算为 159 行、30 个文件。量级一致，建议在文中写明所用命令 |
| brief：agateon 42 个任务、peekview 95 个任务 | CONFIRMED | `ls -d tasks/*/` 的结果分别为 42 和 95 |
| 第二个日期门槛 | 新发现 | `dispatch.yaml:26`，`agate_common.py:1707` |
| 文档质量 | 基本是干净的终态文档 | 证据标注总体准确。需要修改的有两处：F13 中"去掉 CI 那条后为 3 条"本身是推断，而且是错的，却和 `[实测]` 写在一起；F7 后半句"任务目录无版本信息"标为 `[实测]`，但 repro 中没有对应的条目 |

---

## 五、仓库是否保持干净

```
$ git -C /home/claude/randomgitsrc/agateon status --porcelain | wc -l
0      # HEAD 720c97d3
$ git -C /home/claude/randomgitsrc/peekview status --porcelain | wc -l
0      # HEAD 4ea7b8f
$ git -C …/scratchpad/impl/ag status --porcelain | wc -l
0
```

写数据的实验全部在 `/tmp/claude-0/-home-claude/3b55fe33-500c-5e2a-92de-c6ed624bcd96/scratchpad/review2/{ag,runx,ci1,st}` 中完成。repro 脚本在它自己的 mktemp 副本中运行；对 peekview 只做了读取和 `git check-ignore`。
