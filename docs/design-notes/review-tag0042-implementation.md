# TAG0042 实施评审（v0.79.0，main `720c97d3`）

- **对象**：TAG0042「项目形态命令化 + 规则脚本化」6 批落地。基线为 `a68d763` 到 `720c97d3` 的 17 个提交，协议本体涉及 54 个文件、+4793 / −784 行。
- **方法**：
  - 读码；
  - 在**副本**上实跑：`scratchpad/impl/ag` 为 main 的本地克隆；`scratchpad/runx` 为最小 git 仓库；
  - 对照 P1 BDD、P4-review、P7 裁决、CHANGELOG 的对外说法逐项核对。
  - 真实仓库 `git status --porcelain` 结束时为空。
- **标注**：`[实测]` 附命令或输出要点；`[读码]` 附 `文件:行`。

---

## 结论

**有条件接受。**（本报告经独立评审 R2 核实：I-1、I-2、I-4、I-5、I-6 属实，评价公允；R2 指出的低估与口径偏差已改正。） 批 1、批 2、批 6 的骨架可用；批 3、批 4、批 5 各有一处核心承诺**在真实使用者上不成立**。这些问题不需要回滚，但应当**在下一版前修正对外说法**，并按下文登记修复去向。

本任务最值得注意的不是单个缺陷，而是一个**过程性发现**：

- P4-review 已经点名了"`gate_layer` 无运行时消费者"和"delivery 只查子串"；
- P7 以"BDD 的 Then 未要求"为理由接受；
- P6 与 P6.5 judge 判 22/22 通过。

也就是说，**评审发现了问题，但发现没有转成判据**。BDD 写得比 P0-brief 窄（例如 BDD-14 只要求"转换表可查"，没有要求"由脚本按类型选择"），验收于是只验证数据在不在、不验证行为对不对。这正是 TAG0050 要解决的问题，也说明 RM-AG0094（"复犯 → 机械判据"）需要提前做。

---

## 发现

### I-1【高】批 5 `agate-ci-verify` 在 agateon 和 peekview 上恒为 SKIP，防 `--no-verify` 实际未生效

- **代码**：`agate-ci-verify.py:_locate_state` 的逻辑是：仓库根没有 `.state.yaml` 时，tasks 下要**恰好只有 1 个**任务才会重跑，多于 1 个就返回 `ambiguous`，然后输出 SKIP 并 exit 0 `[读码]`。
- **实测**：在 main 副本根目录运行：

  ```
  SKIP: 发现多个任务级 .state.yaml，无法唯一确定本次兜底对象
  rc=0
  ```

  agateon 有 42 个任务目录；peekview 有 95 个，按同一逻辑必然 SKIP `[实测]`。
- **对外说法与实际不符**：
  - CHANGELOG 写的是"实际重跑 gate 判定，替代退役 ci-gate-backstop"；
  - `obligations.yaml` 把 OBL-X-10 登记为 **M**（脚本强制）。
  - 实际效果和退役前的"永远 SKIP"相同，区别只是打印了原因。CI job 也不在 required 列表里（`protocol-tests.yml:20` 注释）。
- **单任务模式同样有问题，结果是假 PASS**：代码按 `tasks/<task_id>` 拼接路径（`agate-ci-verify.py:126`），而真实目录名是 `{ID}-{slug}`；`check-gate` 对不存在的目录返回 0。实测：副本中只保留 TAG0037，phase 设为 P7，删掉 P7-consistency.md，ci-verify 输出 `PASS`，而对真实目录运行 `check-gate P7` 得到 rc=1 `[实测，repro F15b]`。测试 fixture 恰好把目录命名为 `tasks/T001`，所以测试发现不了这个问题。另外，`.gate-result.json` 被 ignore，导致 CI 里的对照代码成了死代码（独立评审 R2 指出）。
- **为何验收通过**：BDD-16 的测试用的是单任务 fixture。P7 认为"显式 SKIP 满足 BDD-16"，接受了这一点，把"唯一定位"记为"后续增强候选"。
- **建议**：
  - 改为按 `merge-base..HEAD` 的 diff 找出**本次变更涉及的任务目录**，逐个重跑；
  - 没有变更任务时才 SKIP；
  - OBL-X-10 在修好之前改登记为 C。
  - **去向**：并入 TAG0050 批 A 的 CI 锚点（见 TAG0050 设计 §2.4）。

### I-2【高】批 3 `agate-run`：基线建立后，每次运行都会因输出里的不确定内容失败；证据被强制忽略，与 RM-AG0097 方向相反

在最小仓库中实测，命令为 `echo ok; date +%N` `[实测]`：

| 步骤 | 结果 |
|---|---|
| 证据未被忽略时 `--baseline` | rc=1，"证据文件未被 .gitignore 覆盖" |
| 加上 ignore 后，第 1 次 `--baseline` | rc=0 |
| 第 2 次 `--baseline`（命令本身 exit 0） | **rc=1**，baseline mismatch |
| **不带** `--baseline` 的普通运行 | **rc=1**，baseline mismatch |

- **基线问题**：普通运行时，只要存在基线文件就做逐字节比对（`agate-run.py` 的 main 末段 `elif os.path.isfile(evidence_path) …`）。pytest、go test 的输出都带耗时，所以一旦建过基线，`agate-run` 对这类命令**永远返回 1**。报错写着"diff 已客观报出"，实际并没有输出 diff。
- **证据去向**：证据写到项目根的 `.agate-evidence/cmd-<下标>.out`（目录可通过 `paths.evidence` 配置），所有任务共享同一槽位。基线只在文件不存在时写入，因此之后所有任务都与**第一份基线**比较，而不是互相覆盖。证据**必须被忽略**。这与 RM-AG0097"证据要入库，才能在他人克隆上复核"的方向正好相反。
- **账本记录**：`cmd_run` 只有设置了 `AGATE_TASK_DIR` 才会写入，否则静默跳过。事件里没有输出哈希、`git_head`，也没有证据路径。
- **"不可绕开"未落实**：没有任何 gate 消费 `cmd_run`（全仓 grep，只有 `check-events` 的已知类型表 `[读码]`）。卡片、角色文件里也没有要求使用 `agate-run`（grep 结果为 0）。BDD-9 的"在不可绕开路径上执行"目前不成立，它只是一个可选工具。
- **建议**：
  - **hotfix**：普通运行只返回命令自身的退出码，基线比对只在 `--baseline` 时进行，比对对象改为 formatter 归一化后的结果；mismatch 时实际打印 diff。
  - 证据绑定（任务目录内日志、头部信息、`EXIT_CODE` 尾行、入库）并入 TAG0050 批 D 的 `run:` 引用（见 TAG0050 设计 §5.3）。

### I-3【高】批 4「关卡层按提交类型分级」只有数据，没有执行代码

- `phases.yaml` 新增的 `gate_layer`（`commit_types`、`transitions`、`paused_from`）在 `agate/scripts/*.py` 中**没有任何读取方**（grep 结果为 0 `[读码]`）。P4-review 的 INFORMATIONAL-2 已经指出这一点。
- `commit_types.release: [P7, P8]` 这类数据既没有语义说明，也没有消费方，属于**声明了却不生效**的数据面内容，读者会误以为它已经生效。
- P6 对 BDD-14 的通过依据是"phases.yaml 实读含 gate_layer"。
- **建议**：
  - 在有消费方之前，从 `phases.yaml` 中删除 `gate_layer`，或者至少把"本节无消费方、仅为设计草案"写进注释第一行；
  - CHANGELOG 的说法"按提交类型选择关卡集合"应当更正；
  - **单独登记 RM**，不并入 TAG0050。

### I-4【中】批 4 `delivery` 判定用的是子串匹配

- **代码**：`check-gate.py` gate_p8 的判定是 `if "delivery:" not in p8_text` `[读码]`。
- **实测**：在副本上删掉 TAG0042 自己 `P8-release.md` 里的 `delivery:` 字段行，在正文加一句"本任务暂不声明 delivery: 方式，待定"，P8 gate 返回 **rc=2（通过）**。
- 这和 RM-AG0085 是同一类问题，而且是本任务**新引入**的。P4-review 和 P7 都看到了，最后以"取值集合未定"为由放行。
- **建议**：`delivery` 改为 P8 frontmatter 的结构化字段，按 schema 校验。**去向**：并入 TAG0050 批 F（§7）。

### I-5【中】批 6 义务登记表的 M 类是作者自己标的，`check-obligations` 不校验标注是否属实

- `check-obligations` 只检查 disposition 非空、M 占比不下降 `[读码]`，这和 P6 frontmatter 自报 `pass` 是同一种结构。
- 抽查 60 条 M 类，其中 **4 条**的 `script` 不在 hook 或 check-gate 的调用集合中 `[实测，repro F13]`：OBL-P2-12、X-10、X-17、X-19。X-19（`check-platform-assumptions`）只在 CI 的 platform-scan job 中运行，而该 job 不是 required，协议也不会随使用者项目带上 CI，所以同样不算必经路径。前三条的情况如下：
  - **OBL-P2-12** `check-tdd-red.py`：check-gate P3 原文写的是"TDD 红灯由主 Agent 手动跑 check-tdd-red.py"（`check-gate.py:979`）；
  - **OBL-X-17** `check-debt.py --retreat-coverage`：RM-AG0088 实测"未挂任何 gate/CI"；
  - **OBL-X-10** `agate-ci-verify.py`：见 I-1。
- R 类（强制评审）同样存在问题：check-gate 只对 P1、P2、P4 的评审校验 `agent ≠ main`（`check-gate.py:672/919/1007`）。30 条 R 中，约 20 条找不到由脚本强制出现的评审产出（独立评审 R2 统计），其中包括 P0 的 3 条——P0 根本没有评审环节，OBL-P0-01 自己的 evidence 也写着"当前无脚本强制力"。
- **影响**：60/123 这个基线本身偏高。修正后的 M 占比会下降，按现有规则会被判 FAIL，反过来**惩罚如实修正**。
- **建议**：
  - `check-obligations` 增加机械核验：M 项的 `script` 必须出现在 pre-commit 或 check-gate 实际调用的脚本集合中（可从源码抽取），否则判 ERROR；R 项必须指向一个由 gate 校验其存在的评审产出；
  - 第一次核验后**重设基线**，并在 CHANGELOG 中说明。
  - **去向**：并入 TAG0050 批 A（它属于"自报汇总改为机械核验"）。

### I-6【中】批 1 之后，phase 改由手工编辑 `.state.yaml` 写入

- `agate-next` 不再写 phase（`_write_state` 已删除），phase 改为"由下一阶段产出提交时写入"。但协议**没有提供写 phase 的工具**，agent 只能手工编辑 YAML `[读码]`。
- 同时，`agate-next` 在 phase 没有变化时就追加了 `state_transition` 事件，之后 pre-commit 在 phase 真正变化时会**再追加一条**，账本里同一次推进会出现两条 `[读码]`。
- **另一面（独立评审 R2 指出）**：pre-commit 在 PAUSED / READY / DONE 时会在 2g 步 `continue`，进入这三个状态的转换**不写**事件。TAG0042 账本里有 P0→P8 的重复记录，却**缺少 P8→READY**。
- **建议**：
  - 提供 `agate-state-set phase <Pn>`：以 HEAD 为基准校验转换是否合法，校验通过后执行 `git add`；
  - `agate-next` 只打印建议，并在建议中给出这条命令，不再写事件；
  - 把 pre-commit 写 `state_transition` 的步骤移到 2g 之前，这样所有 phase 变化都会被记录。
- **去向**：并入 TAG0050 批 A 的 `agate-state-set`（§2.7）。

### I-7【中】`agate-config` 没有 set 子命令，并新增了第 3 套 schema 校验器

- 子命令只有 init / validate / get / list / show。外部分析中列出的 `set / unset / explain / schema` 没有实现。BDD-4 只要求了"读/校验/查询"，所以 P6 判定通过。用户的要求"该结构化的地方应该有 set/get 工具"在声明层只落实了一半。
- `agate-config.py:_validate_node` 是又一份手写的 draft-07 子集校验器，与 `check-yaml-schema.py`、`agate-frontmatter-check.py` 并存。
- `release.preset` 的枚举只有 `semver-changelog-tag`，而且**没有任何消费方**：P8 仍按写死的 version/CHANGELOG/tag 逻辑检查。`PROJECT_CONFIG_DEFAULTS` 还把它设成了默认值。没有发版流程的项目（例如 X）无法声明"无"。
- **建议**：
  - 补上 `set / unset / explain`，写入时按 schema 校验；
  - 三套校验器合并为 `agate_schema.py`；
  - `release.preset` 增加 `none`；在有消费方之前，从 `DEFAULTS` 中移除。
  - **去向**：set/explain 与校验器合并并入 TAG0050 批 B；`release.preset` 单独登记。

### I-8【低】F8 仍未修复

- `pre-commit-gate.py:370` 仍以 3 个参数调用 2 参数的 `append_event`，PAUSED 状态下的 PROD_TOUCHED 留痕始终写不进账本 `[实测]`。
- **去向**：TAG0050 §2.8（可以单独走 hotfix 先行合入）。

### I-9【低】`gate_p0` / `agate-config` / `agate-run` 以 `os.getcwd()` 作为项目根

- 从任务目录或子目录调用时，读不到声明文件，于是给出"缺失"的 WARNING，或报"命令未声明" `[读码]`。
- v0.80.0 的截止版本会把声明缺失改为 exit 1，届时这个问题会变成误拦。
- **建议**：统一改为 `git rev-parse --show-toplevel`，失败时再回退到 cwd。

---

## 做得好的部分

- 批 0 和批 1 的状态转换规则（P7→READY 必须先以 P8 提交，并同时覆盖 P7→DONE）由机械判据强制，确实生效（`check-state-transition.py:278-315`）。
- `read_project_config` 是唯一读取入口，等价守护测试已经到位。
- P8 的发版逻辑没有直接删除，而是采用"等价 preset + WARNING + 截止版本"的迁移方式，保护了存量项目。
- R6 差分覆盖了 peekview 副本（BDD-20）。
- P4-review 的 CRITICAL（Windows 换行导致恒定 mismatch）被发现并修复，修复附带 `windows_smoke` 用例。

---

## 对 TAG0050 的影响（已据此修订设计）

| 发现 | TAG0050 处理 |
|---|---|
| I-1 | §2.4 的 `agate-ci-verify` 改为逐提交回放 pre-commit；A0 hotfix：`check-gate` 对不存在的目录返回 1 |
| I-2 | §5.3 的 `agate-run --task` 产出任务内日志，供 `run:<k>` 引用；基线问题单独走 hotfix，作为批 D 的前置条件 |
| I-4 | §7 增加 P8 `delivery` 结构化字段 |
| I-5 | §2.9 用 `enforced_at` / `review_output` 做机械核验，CI 路径不计入，重设基线 |
| I-6 | §2.7 新增 `agate-state-set` 和 `check_transition` 纯函数；pre-commit 记录所有 phase 变化；`agate-next` 不再写事件 |
| I-7 | §3.2 合并三套校验器；§3.4 为 `agate-config` 增加 set/unset/explain |
| I-8 | §2.8（不变） |
| I-3、I-9、`release.preset` | 不并入 TAG0050，建议登记 RM |

---

## 复现

```bash
# I-1
cd <main 副本> && python3 agate/scripts/agate-ci-verify.py; echo rc=$?

# I-2：在最小仓库中写 agate.config.yaml，verify.commands 含 "echo ok; date +%N"，
#      再依次运行 --baseline（未加 ignore）/ 加 ignore / --baseline ×2 / 普通运行

# I-4：在副本中删除 P8-release.md 的 delivery 行，正文加一句含 "delivery:" 的话，
#      然后运行 check-gate.py P8 <task>

# I-5：python3 -c 抽取 obligations.yaml 中 M 项的 script，
#      与 pre-commit-gate.py、check-gate.py 中引用的 .py 集合求差
```
