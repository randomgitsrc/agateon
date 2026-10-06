# TAG0050 设计独立评审 R1

- **评审对象**：`design-tag0050-task-data-contract.md`、`P0-brief.md`、`exp-tag0050-task-data-contract.md`、`repro-tag0050.sh`
- **基线**：agateon main `a68d763`（v0.78.3），peekview main `4ea7b8f`
- **方法**：在原仓库上只做只读的 grep/读码，以及运行 repro 脚本（该脚本自己在 mktemp 副本里跑）。所有会写数据的实验都在 `/tmp/claude-0/.../scratchpad/review/` 下的副本里进行（agateon 副本已 `fetch --unshallow`，原仓库是 1 个提交的浅克隆）。
- **评审日期**：2026-10-06

---

## 结论：REJECT（修订后重审）

方向是对的：判定只读结构化数据、推导值不让 agent 声明、用契约等级取代日期门槛，这些原则都成立。§0 中的问题陈述基本属实，大部分已复现。

但批 A 是整个设计的地基，它有两处会让其核心承诺失效的缺口：

- **B1**：可以靠追加一条账本事件把任务降级；
- **B2**：legacy 清单缺失时，行为没有定义，会波及测试、fixture、repro 和 R6 副本。

此外，"F3 对新任务已封住"与"legacy 逐字节不变"两项承诺，经实测都不成立。

两个 BLOCKER 都能靠改规格修掉，不需要推倒重来。修完 BLOCKER 和 MAJOR 后可以重审。

---

## 发现清单

### BLOCKER

#### B1：任务等级取"最后一条" `task_created`/`task_adopted`，而账本防线只保证"只追加"。追加一条降级事件就能整体绕开新契约，F3 换了个形式依然存在

- **设计原文**：§2.6 规定"账本中有 `task_created` 或 `task_adopted` → 取**最后一条**的 `contract_level`"；§2.4 只要求"HEAD 是暂存内容的前缀"；§2.7 称"这样 F3 对新任务即被封住"。
- **实测**（副本，TAG0037 账本）：

  ```
  append_event(T, {'event':'task_adopted','contract_level':0,'resolver':'forged',...})
  → 账本 27 行变 28 行
  check-events.py T → "GATE EVENTS: 账本审计通过（28 行，哈希链完整…）" rc=0
  ```

  纯追加完全满足 §2.4 的前缀规则，§9 中 ci-verify 用的也是同一条规则，同样放行。追加之后 `requirement_active` 对所有门槛都返回 False，judge 强制、证据引用强制、各批字段全部失效。
- **性质**：这不是 §1 边界里说的"整链重算"那种伪造，而是协议自己允许的写法（工具 `--adopt` 写的就是这种事件）。§2.4 想要建立的可信锚点，因为"取最后一条"而失去意义。
- **修改建议**：
  1. 等级只取**首条** `task_created`。`task_adopted` 只在账本中**没有** `task_created` 时允许出现，并且等级必须单调不减。之后的 `task_adopted` 只能用于"升级"。
  2. `check-events` 新增校验：`task_created` 必须是首行，且只能有一条；`task_adopted` 不能先于 `task_created`，也不能降级。违反时判 ERROR。
  3. 把 §2.7 的"F3 已封住"改为"在规则 1、2 成立且 ci-verify 对远端基线做前缀校验的前提下封住"，并把"追加降级事件 → ERROR"加入批 A 验收锚。

#### B2：legacy 清单"缺失"时没有定义行为。现有测试、fixture、repro 脚本和 R6 副本都会触发 `TaskNotInitialized`

- **设计原文**：§2.6 规定任务既没有创世事件、也不在清单中时，抛出 `TaskNotInitialized`。设计只写了 pre-commit 如何把它转成 ERROR，没写 check-gate、check-p6-provenance、agate-next 等单独运行时怎么办。§2.5 的清单只在"pre-commit 首次遇到"时才生成。
- **影响面**（实测）：
  - 测试中直接调用 check-gate、pre-commit-gate、provenance、agate-next 或 judge-verdict 的有 **62** 个文件。它们用 `conftest.create_task_dir(tmp_path, created="2026-10-03")` 生成的任务，既没有账本，也没有清单；
  - `agate/tests/fixtures` 下有 5 个带 `.state.yaml` 的任务，账本数为 0；
  - `repro-tag0050.sh` 把存量任务复制进 `git init` 出来的空仓库，那里同样没有清单；
  - §8 / E3 的 R6 差分要在副本上跑。副本如果没带上清单、或没有触发过一次提交，所有存量任务都会报错，这与验收锚 A-⑥ "legacy 判定零变化"直接矛盾；
  - 新安装的项目在首次提交之前，`agate-next` 也会对所有任务报错。
- **修改建议**：明确定义"清单文件不存在、且从未生成过"时的语义。建议：**没有创世事件的任务一律按 legacy 处理**，即退化为旧行为，逐字节不变。`TaskNotInitialized` 只在清单存在（或采用 M3 的替代方案）时才抛出。同时规定独立运行的 check 脚本遇到 `TaskNotInitialized` 时的退出码与提示，并把"无清单仓库上的 fixture 与 repro 零变化"写进批 A 验收锚。

### MAJOR

#### M1：F3 的真正绕过点是 `judge.enabled` 可以随时关掉，设计没有处理

- **实测**（副本，TAG0037）：

  ```
  删 P6.5-judge-verdict.md → check-gate P6.5: "缺 … P6→P7 阻断"
  再把 .state.yaml judge.enabled 改为 false → "GATE P6.5: judge 机制未启用（历史任务），跳过" rc=0
  check-state-yaml.py rc=0
  ```

  P1 的日期门槛只在 P1 跑一次。到了 P6 把 judge 关掉，`gate_p65`（`check-gate.py:1213`）、pre-commit 的 `_judge_enabled`（2i.1）以及 `agate-next._p6_judge_advance`（`:306`）都会直接放行。设计的验收锚 A-① 只测了 P1，测不到这个问题。
- **修改建议**：对非 legacy 任务，所有 judge 消费方一律改为调用 `requirement_active(task, "judge_required")`，忽略 `.state.yaml` 中的 `judge.enabled`。§2.8 的 `state` 契约要把 `judge` 列为系统字段，`agate-state-set` 对它拒写。在 A-① 中补充"P6 关掉 judge → P6.5 仍阻断"。

#### M2：§2.4 宣称"git 历史不能被本地重算覆盖，因此账本是可信锚点"，与 git 的实际行为不符

- **实测**（副本，最小仓库）：先提交 L1–L3，`git reset --soft HEAD~1` 后改写第 3 行再暂存，HEAD 前缀检查结果为 **True（放行）**。`commit --amend`、交互式 rebase 也有同样效果。
- **钩子覆盖面**：`git rebase` / 自动合并不运行 pre-commit；`install-hook.py` 只安装 pre-commit、commit-msg、pre-push 三个钩子。GitHub 端的 PR 合并在服务器上完成，不经过任何本地钩子。
- **历史验证**：在 agateon 全量历史中，账本的 133 次跨提交变化**全部满足前缀关系**（0 次违反），说明这条规则与现有行为兼容（结论为 CONFIRMED）。问题只在于它被宣称的强度。
- **修改建议**：§2.4 改为"本地规则只是提醒；可信锚点是**远端受保护分支**。ci-verify 对 PR 做 `merge-base..head` 的前缀检查"。同时写明 CI 必须 `fetch-depth: 0`：peekview 的 `ci.yml` 三处都是 `fetch-depth: 1`，本次评审拿到的两个仓库也都是浅克隆。

#### M3：§2.5 的清单"在 hook 里惰性生成 + 不可变规则"，在多分支和浅克隆下不成立；用 ID 作键也有歧义

- **多分支竞态**：hook 来自 `~/.agate` 稳定版。安装后，第一次提交发生在哪个分支，清单就生成在哪个分支上。两个分支各自生成时，合并会产生 add/add 冲突。冲突解决后执行 `git commit`，pre-commit **会**运行，此时 HEAD 是第一父提交，若取并集就违反"子集"规则而报 ERROR；只取一侧，则可能漏掉另一侧的任务。
- **浅克隆**：规则 3 和生成条件都依赖"历史中是否出现过该文件"。在浅克隆中无法判定，可能被误判为"从未生成"而重新生成，等于把新任务也洗白进清单。
- **键的歧义**：示例以任务 ID 为键。但 peekview 中 `T003`、`T004`、`T005` 各有两个目录，另有 11 个目录没有 `.state.yaml`，因而没有 task_id。
- **修改建议（同时是简化）**：取消清单文件。判据改为"**暂存区中新增**（HEAD 里没有）、且没有 `task_created` 的任务目录 → ERROR；HEAD 中已有、且没有创世事件的任务 → legacy"。ci-verify 对 `merge-base` 用同一判据。这样可以删掉 §2.5 的全部三条不可变规则和 E3，也就不存在生成竞态。如果坚持保留清单，就应在批 A 的 PR 中**显式提交**清单（agateon），其他项目由 UPGRADING 中的一条命令生成，并且以**目录名**为键。

#### M4：等级只能控制"新门槛何时引入"，控制不了"已有字段的 schema 变更"。摘要检查的覆盖面也不完整

- **schema 变更会回溯**：§3.5 规定按 `since_level ≤ task_level` 挑选字段做校验，但字段的 schema 只有**当前一份**，没有按等级保存的历史版本。例如批 E 之后给 `results.items` 增加一个 required 属性，所有已是 L_D 的在途任务会立刻失败。这与 §2.6 "之后协议升级只影响新任务"矛盾；摘要检查也只能强制"升级等级"，挡不住这种回溯效应。
- **摘要漏项**：摘要只覆盖 `files`、`requirements`、`state` 三节。§3.6 新增的 `tripwires` 节，§4 / §7 写进 `phases.yaml` 的 `primary`、`prunable` 都会改变新任务的判定，却不在摘要范围内，所以"改了契约而没登记新的一级，会被机械拦下"说得过头了。
- **实现问题**：`yaml.safe_load` 会把未加引号的日期解析成 `datetime.date`，导致 `json.dumps` 抛出 TypeError（已实测）。`1` 与 `1.0` 的序列化结果也不同。
- **修改建议**：
  1. 明确规则：已登记字段的 schema 只允许**向后兼容**的修改（放宽）；收紧必须以"新字段或新的 `since_level` 条件"的形式引入，并在 check-protocol-consistency 中用"新 schema 必须接受旧 schema 接受的全部取值"的抽样检查兜底；
  2. 摘要覆盖 `tripwires`，以及 `phases.yaml` 中被契约引用的键；
  3. 规范化时用 `json.dumps(..., default=str)`，或者禁止 YAML 中出现隐式类型。

#### M5：T1 绊线在真实语料上误报面很大，而设计只论证了"漏判无害"，没有论证误报

- **实测**：按 §3.6 的口径统计（全部行首口径的并集，加上 4 个新登记的标记；只扫主产出；排除围栏代码块和 AGATE_CARD 块）：

  | 仓库 | 扫描的主产出文件 | 命中行 | 涉及任务 |
  |---|---|---|---|
  | agateon | 308 | 469 | 37 / 42 |
  | peekview | 477 | 341 | 47 / 95 |

  其中以反引号开头、明显属于"引述"的行，agateon 有 80 行，peekview 有 28 行，例如 `` `- [NEED_CONFIRM] z 的边界条件需确认` 验证流 C… ``、`` `[NO_NEED_CONFIRM]` 理由充分 ``。原因是 `ledger_count` 口径接受行首反引号，并集会把它一起带进来。
- **后果**：T1 命中即 ERROR。按现在的写作习惯，几乎每个新任务都会被拦（P7-consistency 是评审文本，常常需要引述标记）。另外，卡片和协议文档里仍有大量"写 `[X]`"的指令：用 `grep -F` 统计，`[SCOPE+` 28 行、`[NEED_CONFIRM` 40 行、`[PROD_TOUCHED` 12 行、`[DESIGN_GAP` 21 行、`[BLOCKER` 14 行，设计没有列出改写清单。
- **修改建议**：
  - T1 只用 `default` 口径，排除行首反引号和行内代码；
  - 在 P7 / P8 这类评审文本中，T1 降级为 WARNING；
  - 批 B 先在两个仓库副本上量化 T1 的误报率并写入设计，判据为"真实语料中引述类误报为 0"；
  - 列出需要改写的卡片和文档行。

#### M6：渲染块"逐字节相等"在 Windows 上必然失败

- **事实**：`.gitattributes` 有意不对 `*.md` 强制 LF（文件注释："不含 *.md——历史 review 文档为 CRLF"）。Windows 默认 `autocrlf=true`，检出后 md 文件是 CRLF。
- **先例**：pre-commit 2p 段的 dispatch-context hash 比较就曾因 CRLF 一直不匹配，代码里专门做了归一化（`pre-commit-gate.py` 注释"Windows checkout 的 dispatch-context 是 CRLF … 否则恒 mismatch（TAG0009）"）。
- **修改建议**：§3.4 / D10 改为"规范化行尾后逐字节比较"，并纳入 windows_smoke。

#### M7：消费方清单不完整；§9 的 TAG0042 接口无法从仓库核实

设计和 brief 列出的消费方，漏掉了以下几项（均已读码确认）：

- **`agate-extract-context.py:190-211`**：为 P7 / P8 的派发上下文统计正文中的 `- PASS` / `- FAIL`、`[DESIGN_GAP:`、`[BLOCKER]`、`[DEVIATION`。非 legacy 任务改用字段之后，这里会给下游派发提供错误的数据（比如 BLOCKER 数恒为 0）。
- **`agate-md-field-get.py`**：`KNOWN_OPS` 和 `NO_FALLBACK_INT_FIELDS`（`pass`、`fail`、`blocker_count`、`design_gap_count` 等）。读取这些字段的有 `check-gate.py:1168/1169/1234/1235/1257/1258/1328/1329` 和 `check-p6-provenance.py:604/608`。系统字段改成"现算"之后，这条读取路径要么改为调用 `derive`，要么被全部替换，设计没有说明选哪种。
- **`check-pruning.py`**：读取散文里的 `跳过风险:`、`override:`、`internal_only:`、`coupling_checklist:`。§7 的 `pruned` 要取代它们，但没有说 check-pruning 怎么改。
- **`check-scope-resolved.py` 与 `check-retrospective.py`**：扫描任务目录下**所有**顶层 `*.md`（只排除 dispatch / progress 类文件）。§6 / §3.6 只覆盖"主产出"，见 M8。
- **judge 开关的三个消费方**：`agate-next._p6_judge_advance`、`gate_p65` 和 pre-commit 的 `_judge_enabled`，见 M1。
- **`agate-feedback.py`、`ci-gate-backstop.py`**：都走 md-field-get 通道读取字段。

**§9 的 TAG0042 接口**：`agate-config set --task` 委托给 md-field-set、"`agate-config schema` 输出 JSON Schema"、`cmd_run` 事件，在仓库内都找不到出处。全仓 grep `set --task` 和 `agate-config schema` 结果都是 0；TAG0042 的 P0-brief 只写了"agate-config（全部子命令）+ schema"；来源 `analysis-declare-and-enforce.md` 不在仓库里。

**修改建议**：在设计中加入一张"消费方 × 批次 × 改法"表，P0-brief 的标记面也要同步补全。§9 中各接口的出处标注为 `[自述/外部，未入库]`，并登记为 TAG0042 第 2、3 批 P2 的核对项。

#### M8：§6 的声明落点和 ID 方案，与现有的多文件、并行约定冲突，还会丢失现有覆盖

- **覆盖丢失**：`scope_plus` 只在"P2–P7 各主产出"里声明。但真实语料中有 6 个文件在非主产出里写 `[SCOPE+]`，现在由 check-scope-resolved 兜住：`TAG0001/P4-implementation-core.md`、`TAG0003/P4-implementation-docs.md`、`TAG0009/P2-review.md`，以及 peekview 的 `T052`、`T084`、`T085` 三个 `P2-review.md`。按新设计，评审员发现的范围增补将无处可写，T1 也不扫这些文件，结果就是**静默丢失**。
- **并行约定**：P4 并行的现行约定是每个子任务写自己的文件（卡片 `P4-implementation.md:159` 规定写入 `P4-implementation/{pkg}/`）。语料中有 52 个 `P4-implementation-*.md` 和 19 个 `P4-implementation/` 目录，`check-gate.py:1293-1300` 也会把目录内容一并聚合。设计改成"并行批经锁写入同一个 `P4-implementation.md`"，与现行约定相反。
- **ID 冲突**：如果并行批在不同的 worktree 或 checkout 中工作，文件锁不起作用，"最大编号 + 1"会生成重复的 `DG<n>`，合并时 frontmatter 也会冲突。
- **修改建议**：
  - 声明字段允许出现在任何**登记过的**产出文件里（包括 P2-review 和 `P4-implementation-<batch>.md`），由 gate 跨文件聚合；
  - ID 带上文件或批次前缀，例如 `P4.core-DG1`；
  - 删除 §3.3 的写入锁和 E4（同时也是简化）。

#### M9：§7 中"卡片明确不可裁剪的 P1、P2、P5"与代码、卡片不符

- **事实**：`check-pruning.py:162-186` 无条件禁止裁剪 P2、P4、P5、P6，P3 仅在 low 风险时可以裁剪。卡片 `P6-acceptance.md:4` 写的是"P6 不可裁剪"，P1 卡写的是"P1 不可裁剪"。
- **后果**：按设计只在 P1、P2、P5 上标记 `prunable: false`，就会形成第二个权威源，与 check-pruning 不一致。
- **修改建议**：`prunable` 改为三态（`false` / `conditional` / `true`），取值以 check-pruning 为准；check-pruning 改为读取 phases.yaml（只保留一个源），并补一条一致性检查。

#### M10："legacy 判定逐字节不变"不成立

设计自己的几项改动就会改变 legacy 任务的输出或数据：

- §2.3 的 `gate_run` 新增 3 个字段，对所有任务都写，legacy 账本的字节随之变化；
- §2.4 的前缀规则同样适用于 legacy 账本（新增了 ERROR 路径）；
- §2.5 第一次提交时会往暂存区写入清单；
- §5.4 对 legacy 任务给出新的 WARNING；
- §2.9 新写入 `prod_touched_in_paused` 事件。

§8 只把 §2.9 和 RM-AG0085 列为例外。

**修改建议**：把承诺改为"legacy 任务的 **gate 退出码与 ERROR 集合**不变"，并枚举允许出现的新增 WARNING 和账本字段；R6 差分的比较口径也写明这一点。

### MINOR

1. **D5（证据 sha256 互不相同）**：真实语料中，agateon 有 2 个、peekview 有 8 个 P6-evidence 目录存在内容相同的文件。例如 `TAG0020 bdd-5-unit.log` 与 `bdd-6-unit.log` 相同；`T053` 中有 6 个文件同为一个哈希。D5 的报错应提示"同一份证据可以被多条结论共同引用"，避免诱导 verifier 人为制造差异。
2. **D3 与 `agate-next` 的时序**：`agate-next` 在提交前独立运行 check-gate，此时证据可能还没暂存，D3 会报"未入库"。需要写明"先 `git add` 证据"，或者让 D3 在非 pre-commit 场景下只检查"未被忽略"。
3. **§6 `findings.status`**：agent 可以直接把 blocker 改成 `resolved`，效果等同于原来写 `blocker_count: 0`。"修复 F2"的说法偏强。建议 `resolved` 时要求填写 `resolution`，并引用证据。
4. **§2.8 "枚举值域新增 cancelled"**：现在并没有任何 status 枚举在起作用（`agate-state-yaml-check.py` 只检查字段是否存在）。语料中实际出现了 13 种取值（completed 38、done 31、active 25、complete 7、in_progress 6、gate_passed 4……）。应改为"新契约引入枚举"。
5. **任务 ID 正则不一致**：`agate-task-init` 用 `^[A-Z]+[0-9]+$`，而现有的 `agate-state-yaml-check.py` 用 `^T[A-Z]{2}\d+$`。实测 peekview 的 `T090` 会被后者拒绝（rc=1）。§2.2 "T/TPV 都适用"需要统一这两个正则。
6. **校验器重复**：`check-yaml-schema.py` 已经是手写的 draft-07 子集校验器，并且有意没有实现 `minimum`（"防子集实现膨胀"）。§3.2 新写 `agate_schema.py` 前，应先说明复用或合并的方案。
7. **陈旧锁检测（若保留锁）**：Windows 上 `os.kill(pid, 0)` 发送的是 `CTRL_C_EVENT`，不是探测。E4 应写明 pid 存活的判定方式。
8. **gitignore 片段**：negation 规则必须放在 `*.log` 之后才会生效；peekview `.gitignore:94` 已经有 `!…/P6-evidence/logs/*`。UPGRADING 应说明放置顺序。
9. **T2 在 peekview 上的影响**：在 16 个任务中，T2 会命中 138 行 `### BDD-NN:`（目前都是 legacy，但这代表现有写作习惯），P1 卡片需要明确标题格式。agateon 中还有 `#### BDD-15b:` 这种编号，`bdd: integer` 表达不了。
10. **契约分批生效**：每一批都会登记一个新等级，于是在 A 之后、F 之前创建的任务，只能得到部分契约，而 `--adopt` 只面向 legacy 任务。建议允许非 legacy 任务通过 `--adopt` 单调升级（与 B1 的规则一致）。

---

## 过度设计：可以删减的部分

| 项 | 建议 | 理由 |
|---|---|---|
| §2.5 legacy 清单及三条不可变规则、E3 | 删除，改用"暂存区新增目录必须有创世事件"（见 M3） | 消除生成竞态和浅克隆问题，价值不变 |
| §3.3 写入锁、E4 | 删除，改为按批次分文件后聚合（见 M8） | 与现行并行约定一致，没有跨平台的锁问题 |
| §2.8 meta 与 `agate-state-set` | 移出本任务，交回 RM-AG0059 | 与"判定可信"的主题无关，只会扩大批 A |
| §8 "等级无活跃任务"统计 | 删除，或推迟到出现第二个等级之后 | 收益很低 |
| `introduced_in` 字段 | 可以删除 | 设计自己说明判定不读它 |
| 每批都升一级 | 只在出现不兼容变化时升级 | 等级越多，分支和测试矩阵越大 |

---

## 事实核实表

repro 已于 2026-10-06 在 a68d763 / 4ea7b8f 上运行，输出见下表"证据"一列。

| 项 | 判定 | 证据 |
|---|---|---|
| F1-A | CONFIRMED | check-gate P6 rc=2（P6 的通过码）；provenance rc=1，提示"1 个证据文件未被 PASS 行引用" |
| F1-B | CONFIRMED | check-gate rc=2；provenance rc=0，只有 WARNING（frontmatter 20 vs 正文 19） |
| F1-C | CONFIRMED | 两道检查都 rc=0、无提示，属静默放行。`check-gate.py:1168-1173` 只读取 frontmatter 的 `pass`/`fail` |
| F2 | CONFIRMED | check-gate P7 rc=0 |
| F3 | CONFIRMED，但不完整 | 原值 rc=1；回填为 2026-08-01 rc=2；删除 rc=2。`dispatch.yaml:17,26`、`check-gate.py:749` 引用无误。另有 `judge.enabled` 可在 P6 关闭的更大绕过（M1） |
| F4 | CONFIRMED | 正则判定 T/F/F/F/T 与设计一致。`pre-commit-gate.py:348` 无误。peekview `T039…/P4-progress.md:21` 原文为 `- [PROD_TOUCHED]: 无` |
| F5 | CONFIRMED（附说明） | 三处引用逐行核对无误。其中 TAG0033 的例子在 `P8-progress.md`，check-scope-resolved 会跳过 progress 文件，所以它只被注册表正则计入，**没有被任何 gate 当作声明消费** |
| F6 | CORRECTED（轻微） | 182 行出自 `markers.yaml:43` 的注释（自述）。git 中相关修订的日期是 10-02（#387、#388）和 10-03（两次）；"10-01"只出现在 markers.yaml 的注释里，git 显示 #387 合入于 10-02 |
| F7 | CONFIRMED | `agate_common.py:353` 处 `"version": ""`；`.state.yaml` 中没有任何 contract 或 version 键（0 处） |
| F8 | CONFIRMED | `pre-commit-gate.py:370` 传了 3 个参数，`agate_common.py:523` 只接受 2 个，报 TypeError。两个仓库中 `prod_touched_in_paused` 都是 0 次 |
| F9 | CONFIRMED（附说明） | `.gitignore:87` 的 `*.log` 规则生效；入库日志数：agateon P6-evidence 621 个，peekview 12 个，均已核实。repro 用的路径 `T090/P6-evidence/bdd-01.log` 是**虚构的**（T090 没有 P6-evidence 目录），但结论成立：peekview P6 中引用的 641 个 `.log`，在克隆里缺失 601 个，涉及 40 个任务 |
| F10 | CONFIRMED | `agate-frontmatter-check.py:217-218` |
| F11 | 部分 CORRECTED | `:604-606`、`:659`、`:1314` 无误。骨架判定的实际代码在 **`:946`**（`:940-941` 是注释；RM-AG0085 中的行号已过时） |
| brief：30 个 .py 同时含 re 调用和产出文件名 | CONFIRMED | 按 brief 给出的命令复算，结果为 30 |
| brief：8 个标记，消费点 | CONFIRMED / 不完整 | 标记数为 8；消费点漏掉 agate-extract-context、agate-md-field-get、ci-gate-backstop（M7） |
| brief：agateon 42 个任务（21 个有账本），peekview 95 个（7 个有账本），均无 task_created | CONFIRMED | 实测 42/21、95/7，task_created 均为 0 |
| brief：consistency 基线 0 ERROR / 398 WARNING | CONFIRMED | 在副本上运行，结果为"仅有 398 个 WARNING，无 ERROR" |
| brief：TAG0043–0049 已被使用且没有任务目录 | CONFIRMED | 每个编号在 CHANGELOG 等处有 1–4 个文件引用，均无对应目录 |
| §2.3：check-events 对未知字段放行 | CONFIRMED | `check-events.py:14`，且只校验 ts 和 prev_hash |
| §2.4：与现有提交行为兼容 | CONFIRMED | 全量历史中 133 次账本变化，0 次违反前缀规则。但所谓"可信锚点"不成立（M2） |
| §3.3：一期拒写证据字段（BDD-9） | CONFIRMED | `design-md-field-set.md` §5.10；`agate-md-field-set.py:293` |
| §9：TAG0042 的 `set --task` 和 JSON Schema 接口 | 无法核实 | 仓库内没有出处（M7） |
| exp E3：peekview 95 个目录、7 个账本 | CONFIRMED（数量） | 但存在重复 ID 和缺少 `.state.yaml` 的目录（M3） |

---

## 仓库是否保持干净

评审结束时执行：

```
$ git -C /home/claude/randomgitsrc/agateon status --porcelain | wc -l
0
$ git -C /home/claude/randomgitsrc/peekview status --porcelain | wc -l
0
```

HEAD 仍分别是 a68d763 和 4ea7b8f。

所有写数据的实验都在下面的副本中完成：`/tmp/claude-0/-home-claude/3b55fe33-500c-5e2a-92de-c6ed624bcd96/scratchpad/review/{agateon,peekview,w,h}`。repro 脚本运行在它自己的 mktemp 副本里；`check-state-yaml.py` 对 peekview 任务做的是只读调用。
