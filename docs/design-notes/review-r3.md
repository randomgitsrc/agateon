# TAG0050 设计独立评审 R3

- **评审对象**：修订后的 `design-tag0050-task-data-contract.md`、`P0-brief.md`、`exp-tag0050-task-data-contract.md`（新增 E4）、`repro-tag0050.sh`（新增 F3c、F15b、协议文档行数），以及 `review-tag0042-implementation.md`。
- **基线**：agateon `720c97d3`（v0.79.0），peekview `4ea7b8f`。
- **方法**：
  - 读码；
  - 运行新版 repro；
  - 在 `scratchpad/review2/` 下的副本里，**按设计 §2.4 的方法，在 TAG0042 的真实提交上实际回放 pre-commit**。为此用了 3 个临时 worktree（`wt-m`、`old`、`mv`），结束时已全部移除。
- **日期**：2026-10-06

---

## 结论：REJECT（只需重审 §2.4；其余部分修订后可放行）

R2 的 1 个 BLOCKER 和 8 个 MAJOR 中，**7 个 MAJOR 已在设计层面闭合**，主要包括：
- 账本完整性六条规则；
- judge 和 evidence_ref 由契约决定；
- 代码语义冻结加黄金 fixture；
- `check_transition` 纯函数，所有 phase 变化都写事件；
- `followup` 只接受 DEBT 编号，并要求双向回指；
- 批 A 拆成 A0–A4。

repro 新增的 F3c、F15b 和 167 行统计都能复现。

**B-N1 只是换了一个形态，没有闭合。** 新的"逐提交回放 pre-commit"方案，我在 TAG0042 的真实历史上实测了，有四个问题：
1. 对**合规**的提交给出 FAIL；
2. agateon 每次合并 PR 后的 push 都会 FAIL；
3. 看不到删除和改名，第 4 条规则在 CI 中失效，`git mv` 反而被误判；
4. GitHub PR 事件下的回放范围取错。

可信锚点仍然不可用，所以判 REJECT。好在需要修改的只有 §2.4 和 A2 的验收锚，修法也都已有实测支持（见下文），预计一轮就能收敛。

---

## 一、R2 闭环表

| R2 项 | 判定 | 证据 |
|---|---|---|
| **B-N1** CI 锚点 | **OPEN（换了形态）** | 见下面的 **B-R3-1** |
| **M-N1** B1 残余与 legacy 后门 | **PARTIAL** | §2.3 的规则 3–6 已经补齐：事件规则对每个暂存账本都执行，并在任何追加之前执行；有创世事件的账本不可删除；legacy 不可从 READY/DONE 重开；等级必须已登记。CI 也校验新任务的等级。**但是**：<br>• 规则 4 在 CI 中依赖回放能看到"删除"，而按 §2.4 的方法看不到（B-R3-1 ③）；<br>• CI 的等级检查用 `pull_request.base.sha`，与设计"跨越升级不误报"的说法相矛盾（B-R3-1 ⑤） |
| **M-N2** 必经路径 | **PARTIAL** | 已闭合的部分：CI 路径不计入；`scope: protocol-repo`；F13 改为 4 条；R 项按 `review_output` 判定。新机制 `enforced_at` 对一半以上的 M 项起不到作用，见 **M-R3-1** |
| **M-N3** 改名、迁移、测试 | **CLOSED**（本地） | 本地用 `-M` 检测改名：对 agateon 全部 2636 个任务文件做目录级 `git mv`，实测全部识别为 `R`（精确改名不受 renameLimit 限制）。其余几项也已处理：任务目录只认含 `.state.yaml` 的目录；检查放在 2h.1b 之前；新增 `init_task()`；受影响用例列入 §8 例外。**CI 侧仍会误伤**，见 B-R3-1 ③ |
| **M-N4** 第二个日期门槛 | **CLOSED** | F3c 已复现：回填 created 后，rc 从 1 变为 2。§2.5 和 A1-② 都已覆盖。经 grep 确认，全仓的日期门槛只有 `dispatch.yaml` 中的这两个 |
| **M-N5** 代码语义回溯 | **CLOSED** | §2.1 第 2 条规定：名字一经发布语义即冻结，每级保存黄金 fixture；fail-closed；用 `extends` 写增量 |
| **M-N6** §2.7 与现状不一致 | **CLOSED**（附 MINOR） | 改动包括：抽出纯函数、以 HEAD 为基准、回退时写 retries、2h.1c 移到 2g 之前、status 改为现算。还有两处细节，见 MINOR 1、MINOR 2 |
| **M-N7** followup 不通用 | **CLOSED** | §6 规定只接受 `DEBT<n>`，并要求 `source_ref` 回指 |
| **M-N8** 批 A 过大 | **CLOSED** | 已拆成 A0–A4，依赖关系见 §10 |
| R2 MINOR 1–8 | **CLOSED** | SUGGEST 已登记；`run:<k>` 已定义，I-2 hotfix 已列为批 D 的前置条件；fail-closed；166 次；格式转换；关于 X 的说明；只在新增要求时升级；`{ID}-` 前缀检查。P4 引用改为 58 个文件，并引用 `check-gate.py:1311-1314` |

---

## 二、新发现

### BLOCKER

#### B-R3-1：§2.4"逐提交回放 pre-commit"的规格会误判合规提交、漏掉删除和改名，在 GitHub 上回放范围也取错

以下实验都在 `review2/ag` 的 worktree 中进行。回放方式为：检出提交 C，执行 `reset --soft C^1`，然后运行 `pre-commit-gate.py`。

**① 协议版本没有规定清楚，合规提交被判 FAIL `[实测]`**

- §2.4 第 3 步写的是"`AGATE_ROOT` 指向运行 ci-verify 的协议根"，也就是 PR 的 HEAD。
- 我回放了 TAG0042 的 P8 提交 `33e4598c`。这个提交是合规的，当时已经通过了 hook。

  | 回放所用的协议 | rc | 结果 |
  |---|---|---|
  | HEAD（`720c97d3`） | **1** | `P8-dispatch-context-implementer-delivery.md 卡片内容与 CLI 输出不一致（hash mismatch）`（2p 段） |
  | 提交自身的树（`33e4598c`） | **1** | 同上 |
  | **base（`a68d763`，即开发者当时 `~/.agate` 稳定版的协议）** | **0** | 通过 |

- 原因是 hook 的判定依赖**执行它的那一版协议**，比如卡片内容的哈希。开发者提交时用的是安装在 `~/.agate` 的稳定版，所以回放必须用同一版协议，否则合规提交也会被判 FAIL。
- 反过来，如果用 PR 自己的协议来回放，同一个 PR 就能顺手削弱 gate 脚本。
- 对 peekview 和 X 来说，仓库里没有 `.agate-version`，也没有 `agate/` 目录，CI 安装哪个版本的协议完全没有定义。

**② merge 和 squash 会把整个 PR 聚合成一次提交来判，合规合并被判 FAIL `[实测]`**

- agateon 用 merge commit 合并 PR。合并后 push 到 main 时，按设计的取法：base 是 `before` 即旧 main，`rev-list --first-parent before..HEAD` 只包含那个合并提交。
- 回放 `720c97d3`（合并 TAG0042 的提交，以第一父 `a68d763` 为 HEAD）：暂存区包含 170 个文件的聚合 diff，结果 rc=1，报错是 `GATE STATE: 转为 READY 前须先以 phase=P8 提交发布产出（当前前序 phase=P0）`。
- 也就是说，**每一次合规的合并都会 FAIL**，与 A2-③"合规的 PR 判 PASS"相矛盾。
- squash merge 也是同样的结果，而且分支上的原始提交在 main 的历史中已经不存在了。
- 另外，`git merge` 本来就不会触发 pre-commit，所以回放合并提交，判的是一个从来没有经过 hook 的对象。

**③ `git checkout C -- .` 加 `add -A` 看不到删除，改名会退化成"新增" `[实测]`**

- 最小仓库 `review2/rp` 上的实测：
  - C 删除了账本：按设计的方法，暂存区 diff 为空，删除不可见；改用 `checkout -f C` 加 `reset --soft C^` 后，能得到 `D t/T1/gate-events.jsonl`；
  - C 用 `git mv` 改了目录名：按设计的方法得到 `A t/T1-renamed/.state.yaml`，旧路径仍然留在工作树里；改用替代方法后得到 `R100`。
- 后果有两个：
  - **规则 4（账本不可删除）在 CI 中失效**，而 M-N1 正是靠 CI 来兜底的；
  - **规则 1 会把 legacy 任务的改名、`agate-migrate-workspace` 的迁移判为"新目录缺创建事件"，CI 判 FAIL**，等于把 M-N3 在本地修好的问题又带回到 CI。

**④ GitHub PR 事件的回放范围取错 `[读码]`**

- `pull_request` 事件检出的是合成的 merge ref（`refs/pull/N/merge`），它的第一父就是 base 分支的最新提交。
- 按 `--first-parent base..HEAD` 取范围，只会得到这一个合成的合并提交，结果和 ② 一样是聚合判定。

**⑤ CI 的等级检查用错了 base `[读码]`**

- `pull_request.base.sha` 是 base 分支在**事件发生时的最新提交**，不是分叉点。
- 分支在途中，main 如果登记了新等级，分支上由当时的稳定版 hook 以旧等级创建的任务，会被"≥ base 最大等级"误判为 FAIL。这与 §2.4 第 4 条"base 仍是旧等级，所以不会误报"的说法相矛盾。

**修改建议**（§2.4 重写以下几处，A2 的验收锚同步更新）：

- **回放方法**：对每个提交 C，在每次回放前先 `git checkout -f C && git clean -fdx`，再 `git reset --soft C^1`。这样 HEAD 是父提交，暂存区和工作树都等于 C。cwd 设为该 worktree。
- **回放范围**：
  - PR 事件取 `rev-list --no-merges <merge-base(base.sha, head.sha)>..<head.sha>`；
  - push 事件取 `rev-list --no-merges <before>..HEAD`；
  - 合并提交一律跳过；
  - squash 合并的仓库，push 时只校验"账本前缀与事件规则"，不做逐提交回放，逐提交回放由 PR 事件承担。在 UPGRADING 中说明这一点。
- **协议版本**：回放使用 **merge-base 处已合入的协议**。对 agateon 来说，就是 `git worktree add <merge-base>` 之后其中的 `agate/`。对使用者项目来说，就是 `agate.config.yaml` 或 `.agate-version` 中**固定的版本**，所以需要新增一个"协议版本必须固定"的声明项。这样既能与开发者 hook 的口径一致，又能避免同一个 PR 削弱判定。
  - 在 §1 的边界中加上一句：PR 同时修改 workflow 或协议本体时，只能依靠人工评审（SELF-GATE）。
- **等级检查**：以 `merge-base` 中 `LEVELS.yaml` 的最大等级为准。
- **验收锚**：
  - 在副本上回放 TAG0042 PR 的全部 16 个非合并提交，以及合并后的 push 场景，**都必须判 PASS**；
  - 删除账本、`git mv` legacy 目录这两种情况，回放结果要分别是 FAIL 和 PASS。

**E4 的初步数据**：单个提交回放耗时 0.33–1.26 秒（`4b0e33bb`、`33e4598c`、`720c97d3`），TAG0042 规模的 PR 预计不超过 30 秒。可以把这些数据写进 E4 作为初值。

### MAJOR

#### M-R3-1：`enforced_at` 对一半以上的 M 项起不到作用

- M 项共 60 条，其中 **28 条**的 `script` 就是 `check-gate.py`（25 条）或 `pre-commit-gate.py`（3 条）本身。
- 这些义务是由 gate 函数内部的分支代码实现的（例如 `gate_p8` 中的 `if "delivery:" not in p8_text`），并不存在一次"调用"。对它们来说：
  - `call` 字面量无从填写；
  - 机械判据只剩下"函数存在、且可以到达"。只要 `gate_p8` 还在，义务被删掉了也照样通过。
- 另有 3 条 `script` 是复合写法（例如 `A + B`、带参数的写法），需要规定匹配规则：同一个 `ast.Call` 节点的参数中包含全部字面量。
- 可达性分析本身是可行的：check-gate 的 `handlers` 表在 `:1640`；pre-commit 的全部步骤都在 `main` 中（`:212` 起）；用 ast 做文件内的调用图就够了。问题在于判据太弱，而不是做不到。

**修改建议**：
- M 项增加必填字段 `test: <pytest 节点 id>`。该测试必须在测试名或 docstring 中引用这条义务的 id。
- `check-obligations` 用机械方式核验两点：测试存在；测试的断言目标就是 `enforced_at.function` 所在的脚本。
- 在 A4 的验收锚中加入负向控制：删掉义务对应的那个判断分支后，对应的测试必须转红。这正是 RM-AG0094"复犯 → 机械判据"的落点。
- `call` 改为可选字段，只用于"调用另一个脚本"这一类义务。

#### M-R3-2：回放范围只覆盖 pre-commit，SELF-GATE 依赖的 commit-msg hook 同样会被 `--no-verify` 跳过，CI 却不回放

- `--no-verify` 会同时跳过 pre-commit 和 commit-msg 两个 hook。
- agateon 的 SELF-GATE（要求在提交信息里留下 `self-gate-review:` 或 `self-gate-skip:`）由 `commit-msg-self-gate.py` 强制。TAG0042 的提交里就有 `self-gate-skip:`。
- §2.4 只回放 pre-commit，于是"改协议本体却没有经过独立评审"这件事在 CI 中仍然发现不了。而本任务每一批都要触发 SELF-GATE。
- **修改建议**：回放时同时运行 `commit-msg-self-gate.py <msgfile>`，提交信息取自 `git log -1 --format=%B C`。在 A2 中加一条验收锚：`--no-verify` 提交了协议改动、但没有留 trailer，CI 判 FAIL。

### MINOR

1. **2h.1c 前移时，2h.1d 也要一起前移。** 2h.1d 负责 `git add` 账本，现在位于 2g 之后。如果只移 2h.1c，READY/DONE/PAUSED 提交写入的事件不会被暂存，要等到下一个提交才会入库，这段时间里 `updated` 现算出来的值与 HEAD 不一致。
2. **status 改为现算后的消费方。**
   - `agate-state-yaml-check.py:34` 把 `status` 列为必填字段。需要写明对非 legacy 任务的处理："不写；写了即判 ERROR"，或者"可以写但不采信"。建议选前者，以免文件里留下过时的值。
   - `agate-summary.py` 没有读取 status。`active-tasks.md` 是主 Agent 手工维护的看板，其中的状态、阶段、优先级、依赖等列与 `.state.yaml` 重复，没有任何 gate 读取它（只有 `check-ledger-pollution` 守护文件不被污染）。它属于 RM-AG0059 第 ② 项（范围外）。建议在 §2.7 注明"active-tasks 是非权威视图"。
3. **`--existing` 重建哈希链的安全边界。** 对确实没有被跟踪的账本，重建哈希链是安全的：没有历史引用这些行，前缀规则也不涉及它们。但"HEAD 中没有该文件"这个条件，会放过一种情况：先 `git mv` 一个 legacy 目录，再对新路径运行 `--existing`。新路径在 HEAD 中不存在，结果会把一条已提交的 legacy 账本前置改写成新任务，绕过"只追加"的规则。建议把条件改为："HEAD 中不存在，**且**暂存区里它不是任何改名的目标，**且**账本中不含 `task_created` 或 `task_adopted`。"
4. **规则 6（legacy 不可重开）在历史上有 1 次合法使用**：TAG0008 曾从 READY 回到 P5（`35001926`，按全部提交扫描所得）。报错时提示用 `--adopt`，但没有说明在途任务（例如处于 P5）被 adopt 后，前序阶段的产物需要满足哪一级要求。建议写明：adopt 只作用于当前阶段及之后的阶段。
5. **回放时会执行 2h 的 `check-p6-format --fix`**，修复后的内容再交给 gate。这会让用 `--no-verify` 跳过的格式错误在回放中被"自动修好"后通过。建议在回放模式下跳过 `--fix`，改为只做校验。
6. **P0-brief 与设计不一致的几处**：
   - brief 写"允许的 9 项差异"，设计 §8 现在是 11 项；
   - brief 写"约 28 个脚本"，设计 §13 写"约 30 个"；
   - brief 中 B 的前提写的是"A"，设计 §10 是"A1 → {A2, B}"。
7. **`review-tag0042-implementation.md:139`** 引用的 `check-state-transition.py:271-296`，与实际 READY/DONE 规则所在的 `:278-315` 有偏差。其余更正（I-1 单任务假 PASS、I-2"不是互相覆盖"、I-5 改为 4 条、I-6 进入 READY 等状态时不写事件）都准确。

---

## 三、TAG0042 实施评审（更正后）核实

| 项 | 判定 |
|---|---|
| I-1 | 已更正，准确。F15b 可复现：ci-verify 输出 PASS；对真实目录运行 `check-gate P7`，rc=1；对 `tasks/TAG0037` 运行，rc=0 |
| I-2 | 已更正，准确（基线只写一次；目录可配置） |
| I-5 | 已更正为 4 条，并说明了 X-19 只在非 required 的 job 中运行，准确 |
| I-6 | 已补上"进入 PAUSED / READY / DONE 时不写事件"，准确 |
| 总评 | 公允。只剩 MINOR 7 提到的一处行号偏差 |

---

## 四、事实核实表

| 项 | 判定 | 证据 |
|---|---|---|
| repro 原有各段 | CONFIRMED | 与 R2 时的输出逐行一致 |
| F3c | CONFIRMED | created 为原值时 `check-p6-evidence` rc=1；回填为 2026-10-01 后 rc=2，提示"**历史任务**，按 evidence_ref_required_since" |
| F15b | CONFIRMED | 见上 |
| 协议文档 167 行、30 个文件 | CONFIRMED | 附录 A 中的命令可复现 |
| "全仓只有两个日期门槛" | CONFIRMED | 在 rules/ 和 scripts/ 中 grep `_since`、`cutoff`、`截止`，其他命中都是"截止版本"类的迁移提示或无关函数 |
| 账本 166 次变化、0 次违反 | CONFIRMED | R2 已实测 |
| `check-gate.py:1311-1314` 中 P4 目录的聚合 | 未逐行复核 | 不影响结论 |
| §2.4 第 4 条"base 仍是旧等级" | **不成立** | B-R3-1 ⑤ |
| §2.4 第 3 步的回放方法 | **不成立** | B-R3-1 ①–③（已实测） |
| `git mv` 的改名检测（本地） | CONFIRMED | 2636 个文件全部识别为 R |
| `enforced_at` 的可达性 | 可行，但判据太弱 | M-R3-1 |
| 文档质量 | 好 | 终态文档，干净；证据标注准确，R2 的结论都标为 `[自述，R2 评审]`。§2.4 中关于回放可行性的说法没有标注：它其实是 `[推断]`，并且已被本轮实测推翻 |

---

## 五、仓库是否保持干净

```
/home/claude/randomgitsrc/agateon   status --porcelain: 0 行   HEAD 720c97d3
/home/claude/randomgitsrc/peekview  status --porcelain: 0 行   HEAD 4ea7b8f
scratchpad/impl/ag                  status --porcelain: 0 行
```

回放实验使用的 worktree 都挂在副本 `review2/ag` 上，包括 `wt-m`、`old`、`mv`，已用 `git worktree remove` 全部移除并 prune。最小仓库是 `review2/rp` 和 `rp-wt`。repro 脚本在它自己的 mktemp 目录中运行。
