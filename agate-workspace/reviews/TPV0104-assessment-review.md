# TPV0104 核实报告 · 独立审查结论

> **审查对象**：`reviews/TPV0104-Agateon-current-state-assessment.md`（371 行）
> **审查者**：独立审查者（非报告作者，fresh context）
> **审查时间**：2026-11-27（+0800）
> **审查基线**：Agateon `main` @ `2e7e4a0f`（`v0.83.4-8`）；Peekview `main` @ `c1430589`
> **原始痕迹**：`reviews/TPV0104-assessment-review.progress.md`
> **本次审查未修改 Agateon/Peekview 任何代码、协议、配置**（仅新建本文件与 progress 文件；
> 实验全部在 `mktemp -d` 临时仓内完成并已清理；已核 `git status --porcelain` 无残留）

---

## 总判定：**需修正**

报告的**主干事实可靠且可复现**——第 12 条（我四配置矩阵逐格复现）、第 13 条（7/7 写法
逐格复现）、第 15 条已解决、第 11 条「义务挂错环节」的根因、以及「近期三类改动与此 5 条
无关」的判断，经我独立实测**全部成立**。这部分质量高于一般核实报告。

但报告有 **1 处方向性错误 + 3 处事实错误 + 1 处失实引用 + 1 条重大漏报**，
且方向性错误恰好落在它自己列为「关键取舍」的第 14 条上，**不能按现状采信**。

| 级别 | 数量 | 内容 |
|---|---|---|
| 方向性错误 | 1 | §2.4 第 14 条：机制与适用范围双错，且范围判断**恰好相反** |
| 事实错误 | 3 | §2.1「适用所有任务」高估；§3.3 算术（7 应为 8）+ 行数（9 应为 7）；§2.1 OBL-P2 计数（10 应为 17） |
| 失实引用 | 1 | §5.1「P1 后回答两个问题」在声称的 `retrospective.md` 中**查无此句** |
| 重大漏报 | 1 | OBL-P8-05 登记为 M（机械执行）实为 WARNING 效力——与报告 §4 自己称赞的「存在性→效力」方法论同型，却未在自己脚下应用 |
| 建议缺陷 | 2 | §6-P1① 的覆盖面被高估；§6-P1①「可选加固」会直接打红 `check-obligations.py` |

---

## 12 问逐条回答

### 问 1：是否用了最终更正版而非初稿？

**是。** 交接单 `git log` 显示 `82844019`（9 条初稿）/ `96e8d72c`（追加 §11–15）。
报告头注明写「`96e8d72c` 追加的 5 条，非 `82844019` 初稿的 9 条」，且 §2.1–2.5 与
交接单 §11–15 **逐条对应**（编号、现象、机制、建议均一致）。

**关键核查点：有没有把初稿错误结论重新包装成需求？没有，反而是报告纠正了它。**
- 初稿/`retrospective.md:79` 仍写第 14 条是「**规则要求 judge 用豁免集，白名单又不给，
  自相矛盾**」——这是被最终版明确更正掉的夸大表述。
- 最终版 §14 末尾有注：「白名单排除它是设计，不是缺陷。真正的矛盾在「P6 卡推荐格式 ↔
  legacy 解析」」。
- 报告 §2.4 照最终版写，并明写「**不要**为了让 Judge 能读该文件而改白名单——那会破坏
  信息隔离」，`judge.md:95` 原文核对一致（`[文档]`）。

⇒ 这一项**报告做对了**，且是它比原始复盘更准确的地方。（问 1 判 **通过**。）

### 问 2：是否核实了 Agateon 当前代码（不是只读 CHANGELOG）？

**是。** 我抽查了它引用的 8 处行号，7 处精确、2 处差 1 行（`check-scope-resolved.py`
报 137-151 实为 138-150；`agate-run.py` 报 278-286 实为 279-287），无捏造。

我自行通读了：`check-changelog.py`(86 行全文)、`check-changelog-quality.py`(310 行全文)、
`agate-run.py`(`_is_ignored`/`_write_run_log`/`_run_with_task`/`main`)、
`check-scope-resolved.py`(`_aggregate_declaration_ids`/`main`)、
`check-judge-verdict.py`(`_WHITELIST_MD`/`_two_sections`/`_check_whitelist_outside`/
`_check_evidence`/`main`)、`agate_common.py`(`extract_conclusion_refs`/`_REF_TOKEN_RE`/
`resolve_evidence`/`gate_commands` 解析)、`obligations.yaml`、`phases.yaml`、
三个 review-role、四张 phase-card、`pre-commit-gate.py`/`check-gate.py`/`check-obligations.py`。

⇒ 问 2 判 **通过**。（但读得够不等于读得对——见问 4。）

### 问 3：报告称「CHANGELOG 守卫 / doctor / DSH 三类改动均不解决这 5 条」成立吗？

**成立**，且我给出了比报告更强的证据。

| 近期改动 | 我核实的依据 | 结论 |
|---|---|---|
| CHANGELOG 质量守卫（RM-AG0117）与第 13 条 | `grep -n 'task_id\|TAG\|TPV' check-changelog-quality.py` → **0 命中**；它扫的是「过程痕迹」词表（A1/A2/A4/A5/A6/A7），判据与 `task_id` 存在性**不共享任何词表或函数**；两脚本互不调用（前者只在注释里提后者） | **无关，成立** |
| doctor 不覆盖 agate-run | `grep -c 'agate-run' agate-doctor.py` = **0**；`grep -c 'runs'` = **0** | **无关，成立** |
| DSH 0.2.x 兼容（v0.83.4） | 平台 preset 路径适配，非协议机制 | **无关，成立** |

**报告没给、但我补上的决定性证据**：
`git log -- agate/scripts/check-changelog.py` 最后一次改动是 `71063be5`（TAG0039）。
本次 `v0.83.3 → v0.83.4` 的三个 changelog-quality 提交（`43fbcf3b` / `edb63b58` /
`d11d7675`）**完全没有触碰** `check-changelog.py`。
⇒ 「不解决第 13 条」在**提交层面**即可证，不必靠语义辨析。

（补充一条报告未提的关联：`check-changelog-quality.py` 的**阻断级**主闸是 pre-commit `2z2`
（循环外、`exit 1`），而 `check-changelog.py` 在 pre-commit 里只是 WARNING（见问 12-A）。
两者在同一 hook 里**一强一弱**，这正是报告 §4 表格「无关」背后的真实结构。）

⇒ 问 3 判 **通过**，且报告的判断经得起更严格的检验。

### 问 4：是否把有意设计误判为缺陷？第 14 条「白名单排除 `known-failures.md` 是设计」对吗？

**「白名单排除是设计」这半句对；但报告用来支撑它的整条结论不成立。**

**（a）「是设计」——对。** `judge.md:95` 原文：「（白名单**不含** `known-failures.md`，
且**禁读** `P6-acceptance.md`）⇒ 你**不**机械读豁免集」。`_WHITELIST_MD`（
`check-judge-verdict.py:81`）确不含它。设计意图是信息隔离：judge 不看豁免集，
由主 Agent 转述 baseline。⇒ 报告 §2.4「Intentional（白名单）」**正确**，
且它明确拒绝「把该文件加入白名单」这个错误修法，**这个取舍是对的**。

**（b）但报告的核心断言「legacy 任务照抄 P6 卡推荐格式 → exit 1」经实测为假。**

我构造真实 legacy 任务（`gate-events.jsonl` 仅 `gate_run`、无 `task_created`
⇒ `task_level()=None` ⇒ legacy，脚本自报走 legacy 路径），写入 P6 卡 `:47` 的
**逐字推荐格式**：

```
- PASS BDD-01: pytest 全绿（引入失败 0；预存失败 N 条见 known-failures.md）(P6-evidence/a.log)
⇒ 实测 exit = 0，输出「校验通过（status=passed, criteria 1/1）」
```

根因（读实现得出）：该括号组内容是 `引入失败 0；预存失败 N 条见 known-failures.md`，
`extract_conclusion_refs` 要求「整组非空且**全部**是路径」（`_REF_TOKEN_RE =
^[\w.\-/]+\.[A-Za-z][A-Za-z0-9]{0,7}$`），含空格与全角分号 ⇒ **整组被丢弃**，
只取到 `(P6-evidence/a.log)`。⇒ **推荐格式根本不会失败。**

真正 `exit 1` 的是另一种写法（`known-failures.md` 作为**纯路径括号组**）：
`- PASS BDD-01: 全绿 (known-failures.md)` ⇒
`结论行引用的证据不存在或不可解析: known-failures.md`。但**这不是 P6 卡的推荐格式**。
（更深一层：`resolve_evidence` 恒以 `<task>/P6-evidence/` 为基准拼接，
`known-failures.md` 位于任务根 ⇒ 任何任务根文件都解析不到——与 legacy 无关。）

**（c）真正咬人的是另一条检查，且它对 legacy/非 legacy 一视同仁。**

`_check_whitelist_outside` 扫 `P6.5-dispatch-context-judge.md` 的「输入文件/上游关联」两节：

| 场景 | 实测 |
|---|---|
| legacy：两节写 `- known-failures.md` | **exit 1**「白名单外任务路径引用: known-failures.md」 |
| 非 legacy：同一文件同一行（我直接调 `_check_whitelist_outside`） | **同样命中** `['known-failures.md']` |
| 改为「任务目录下的预存失败登记文件」（不写文件名） | exit 0 通过 |

这正是 `retrospective.md` 问题 2 描述的现象（「主 Agent 在 judge 派发单里一引用就被 gate
拦」「只能靠改写表述绕过」）——是 **dispatch-context 白名单**，**不是 legacy 解析**。
我核 TPV0104 的实况吻合：`P6.5-dispatch-context-judge.md:29` 写「**文件名由你自行在任务
目录内确认**」、`:82` 写「文件名由你在任务目录内自行定位」——**正是改写绕过后的文本**。

⇒ **报告 §2.4 的「适用范围：仅 legacy / TPV0104 是非 legacy ⇒ 本任务未踩到」恰好相反**：
TPV0104 是非 legacy，而它**踩到了**（这正是复盘的原始观察）。

### 问 5：是否把执行错误误判为协议缺陷？（阶段通过码 + `| tail`）

**报告判断正确。**

- `phases.yaml` 实测 `gate_pass_exit`：P0/P1/P2/P3/**P4=0**/P5/P6/**P6.5=0**/**P7=0**/P8
  ⇒ 与报告「P0-P3/P5/P6/P8→2；P4/P7/P6.5→0」完全一致。
- `retrospective.md:166` 原话确有「一个用 `| tail` 读到 0」⇒「吞退出码」**不是报告臆造**。
- `agate-run.py:7` docstring 确有「POSIX 开 `pipefail`，避免 `cmd | tail` 吞掉左侧失败」。
- 单一事实源确为 `phases.yaml` 的 `gate_pass_exit`。

⇒ 「执行错误，不因此统一退出码、不新增 gate」**成立**。

**但报告漏了复盘的原始诉求（属"过度驳回"）**：`retrospective.md:116` 改进措施 #4 要的是
「在 `phase-cards/` 或 `WORKFLOW.md` 加一张**阶段→通过码速查表**」——这是**加一行文档**，
既不是新增 gate 也不是统一退出码。实测 `grep -n "gate_pass_exit\|通过码" agate/WORKFLOW.md`
= **零命中**，`phase-cards/` 亦无。报告把它整体归入「执行错误 ⇒ 无需处理」，未说明
为何连这张表也不加。**报告 §3.2「不转化为待修项」的取向对，但对这条的具体处置过宽。**

### 问 6：报告自己有没有变相提出「gate 逐条核对 Then 子句」？

**没有。这个判断我支持报告。**它提的是「在 `plan-eng-review.md` 增一条检查项」，
与「P2 gate 用脚本逐条比对 Then 子句」是**不同性质的东西**：

| | 报告提的方案 | 已被证伪的方案 |
|---|---|---|
| 载体 | 自然语言评审提示（review-role 的一句话） | 机械脚本判据 |
| 判定者 | 评审 agent 的语义判断 | gate 的字符串/结构比对 |
| 19/19 误报是否适用 | **不适用**（不会逐条机械枚举） | 适用 |

19/19 实验否证的是「机械逐条核对会把 19 条带 `①②③` 的 BDD 全判红」，
它**不否证**「让评审 agent 多问一句『P2 是否削弱了某条 Then 子句』」。
⇒ 报告 §3.1 / §6-P1① 的自我约束是**诚实且成立**的。

（我先复核了它的证伪数据：54 条 BDD 中带 `①②③` 的 = **19** 条，id 为
`BDD-02,05,16,17,18,19,22,24,28,29,31,33,35,38,40,45,50,53,54`；
`P6-acceptance.md` 的 54 条 PASS 行里含 `①②③` 的仅 **1** 条（BDD-38）⇒
「没有一条逐条枚举」基本成立（1 条例外，量级不影响 19/19 结论）。

**但这条建议有两个真问题**（见问 9）：覆盖面被高估 + 「必然提出」不可验收。

### 问 7：是否把 legacy 与非 legacy 混为一谈？

**报告在第 15 条上标对了，在第 14 条上标反了。**

- **第 15 条**：正确。`check-scope-resolved.py:138-150` 明写
  `is_non_legacy` 为真则走结构化聚合、为假才回 P1 正文；
  报告写「非 legacy 已解决；legacy 保留旧路径」——与实现一致 ✅
- **第 14 条**：错且反。见问 4(c)：真机制（dispatch-context 白名单）**不分 legacy**；
  报告写的「仅 legacy、本任务未踩到」与实际相反。

### 问 8：是否为每个结论提供足够证据？（抽查 3 条自行复现）

抽查第 12 / 13 / 11 条，**全部复现成功**。

**抽查 A — 第 12 条（`agate-run.py` 四配置矩阵）**：真实 `mktemp -d` git 仓，
每个配置**独立新仓**：

| # | `.gitignore` | `check-ignore -q` | `agate-run --task` exit | 账本行数 |
|---|---|---|---|---|
| A | 空（≈ Agateon 本仓无 `*.log`） | rc=1 | **0** | 1 |
| B | `*.log` + `!.../P6-evidence/logs/*`（≈ Peekview） | rc=0 | **1** | **0** |
| C | `*.log` + `!.../runs/**` | rc=1 | **0** | 1 |
| D | `agate-workspace/**/runs/` | rc=0 | **1** | **0** |

与报告矩阵**逐格一致**。`return 1` 确在 `_record_cmd_run` 之前
（`agate-run.py:279-287`），账本 0 行实测 ⇒「三样同时丢」成立。

> ⚠️ **方法论提醒（对后来者）**：我首轮在**同一仓**里连续切四个配置，D 组得 `exit 0`
> 假绿——因为 `runs/1.log` 已被前一配置 `git add` 成 tracked，而 `git check-ignore`
> 对 tracked 文件返回 1。**必须每次新建仓**。报告的四配置矩阵应也是这么做的
> （其 D 组结果与我"干净重做"后一致），但报告未写明这一前提。

**抽查 B — 第 13 条（7 种写法矩阵）**：`mktemp -d` + 真 `CHANGELOG.md`，逐格一致（7/7）：

| 写法 | 实测 exit | 报告 |
|---|---|---|
| `修复（TPV0104）` | 1 | 1 ✅ |
| `TPV0104（全角）` | 1 | 1 ✅ |
| `TPV0104，逗号` | 1 | 1 ✅ |
| `TPV0104: 冒号` | 0 | 0 ✅ |
| `TPV0104 空格` | 0 | 0 ✅ |
| `TPV0104)` | 1 | 1 ✅ |
| `TPV01040` | 1（正确，防误命中） | 1 ✅ |

并且我**验证了报告 §6-P2③ 的修复方案可行**：把右边界补 `）`、`，`、`：`、`)` 后，
前 6 种全部命中、`TPV01040` 仍不命中 ⇒ 验收条件可达成 ✅

**抽查 C — 第 11 条（`OBL-P1-14` 落点）**：

| 断言 | 我的实测 | 结论 |
|---|---|---|
| 规则在 `P1-requirements.md:248` | 逐字命中「隐含扩展同样要授权…放宽/收紧某条 BDD 的判定边界」 | ✅ |
| `OBL-P1-14`：`phase: P1`、`disposition: R`、`review_output: P1-review.md` | `obligations.yaml:196-203` 逐字一致 | ✅ |
| P2 无对应义务 | `OBL-P2-01..17` 共 **17** 条，区间内 `BDD` 关键字命中 **0** | ✅（计数错，见问 9） |
| 评审角色未覆盖 | `grep -c 'BDD\|基线'`：`plan-eng-review.md`=**0**、`design-review.md`=**0** | ✅ |
| `gate_p2` 不读 BDD 正文 | 只把 `candidate_count` 下限 2→1（`check-gate.py:1063`） | ✅ |

⇒ 问 8 判 **通过**：报告的证据是**真跑出来的**，不是纸面推断。

### 问 9：是否提出了不必要的新阶段/新角色/新 Gate？P1/P2/P3 是否符合「最小修复」？

**方向上符合「最小修复」，但有 2 处实质缺陷。**

做对的：§6 四条建议**均未新增阶段、未新增 Agent 角色、未新增 gate**；
第 14 条明确拒绝改白名单；第 12 条给了「降为 WARNING」与「先记账再返回」两个最小选项。
这符合仓库 `AGENTS.md`「新增判据 = 给所有使用者加成本」的取向。

**缺陷 1：§2.1「适用范围：所有任务」不成立，导致 §6-P1① 的覆盖面被高估。**
`rules/review-mapping.md` 规定 `plan-eng-review` **仅在**以下情形派发：
`backend`（任意 risk）／`任意 domain + risk=high`／`full 档`。
`OBL-P2-13` 原文亦为「plan-eng-review（**backend 或 risk=high 强制**）」。
`plan-design-review`（frontend 域）的 `BDD|基线` 命中也是 **0**。

⇒ 对「**纯 frontend + risk 非 high + 非 full**」的任务，`plan-eng-review` **根本不会被派**，
报告新增的那条检查项**永远不生效**——缺口仍在，报告却宣称已覆盖。
（TPV0104 恰有 `domains: [frontend, backend]` ⇒ 本任务会被覆盖，但这是**个例**，
推不出「所有任务」。）应改为「backend / risk=high / full 档任务」，并说明
frontend-only 任务的缺口是否需要另案处理。

**缺陷 2：§6-P1① 的「可选加固」（`OBL-P2-xx` 增一条义务）会直接打红 `check-obligations.py`。**
我在副本上实加了 1 条 `disposition: R` 的义务：

```
M 类占比: 56/122 = 0.4590（基线 56/121 = 0.4628）
CHECK-OBLIGATIONS: FAIL M 类占比低于基线：current=56/122 < baseline=56/121
```

而 `check-obligations.py` 由 `agate/tests/unit/test_tag0050_obligations.py:287` 在
**全量 pytest** 里以真 `AGATE_ROOT` 端到端跑 ⇒ 加 R 义务必须**同时**改
`baseline.reset`（该字段支持一次性显式重设，但需写 CHANGELOG 留痕）。
报告把这条写成「可选加固」而无任何提示，照做会被 CI 打红并误以为是判据误报。

**缺陷 3（较轻）：§6-P1① 的验收条件不可判定。** 它写「看 P2 评审是否**必然**提出该点」——
自然语言评审提示**无法保证"必然"**。应改为可判定形态，如「构造反例时，
`P2-review.md` 是否含针对该反例的显式结论」。

### 问 10：§3.3 的 Gate 分类（2 真保护 / 7 格式摩擦）准确吗？

**「2 次真保护」正确；「7 次格式摩擦」错，应为 8；「合计 10(9 行)」行数也错，明细表是 7 行。**

按 `retrospective.md:38-46` 明细表逐行重算：

| # | 明细 | 次数 | 类别 |
|---|---|---|---|
| 1–3 | `prod_touched` 字段缺失（P1/P2/P3） | 3 | 格式 |
| 4 | progress 缺 frontmatter | 1 | 格式 |
| 5 | `P4-review.md` 缺失（评审不可裁剪） | 1 | **真保护** |
| 6 | P6 混入源码改动 | 1 | **真保护** |
| 7 | `source: task` 非法 | 1 | 格式 |
| 8 | `P8-release.md` 缺 `prod_touched` | 1 | 格式 |
| 9–10 | `.state.yaml` 非法 `status` 键 | 2 | 格式 |

- 真保护 = **2** ✅（报告正确）
- 格式 = 3+1+1+1+2 = **8**（报告写 7 ❌）
- 合计 = 2+8 = **10** ✅
- 明细表行数 = **7**（报告写「9 行」❌）

⇒ 结论取向（「不要用 gate 次数衡量保障质量」）**正确且重要**，但**两个数字都要改**。
附带：报告自己内部也不自洽——它写「2 + 7」却写合计 10。

### 问 11：§5 对自主性的评价是否过度？

**取向克制、恰当，甚至偏保守；但它用的那句引文查无出处，且低估了可数的干预。**

- 报告 §5.1 表格引「任务自述『P1 后回答两个问题，之后基本不需协调』」，来源标
  `retrospective.md`（`[自述]`，未独立核实）。
- 我实测 `grep -n "P1 后\|两个问题\|基本不需" retrospective.md` ⇒ **零命中**。
  ⇒ **该引文在其声称的来源里不存在**（引用失实）。
- 反向证据（报告未用，但就在同一任务目录里）：`orchestrator-log.md`（422 行）中
  「用户」出现 **18** 次，其中明确的用户介入至少 **6** 处：
  - `:12`/`:18`/`:19` 「开工」指令与范围决策（「范围**不再扩**」）
  - `:51`/`:54` 「**用户定夺**」两项 P0 未覆盖空白
  - `:10` 用户指出 V-04「已修复」的初判是错的
  - `:16` 用户指出 `firstFileId` / `file` 的概念错误（致 BDD 44→45）
  - `:161` 用户要求「按 agateon 执行完任务」
- ⇒ 报告「用户注意力成本未量化、不能说它证明了成本效率」的**立场正确**，
  但它**明明有 6 处可数的介入记录却只引了一句查不到的自述**——应改为引用上述实测计数，
  这会让同一结论**更有力**而非更弱。

### 问 12：有没有报告漏掉的重要问题？

**有 1 条重大漏报，且与报告自己的方法论主张同型。**

#### (A) `OBL-P8-05` 登记为 M（机械执行），实机只有 WARNING 效力

- `obligations.yaml:753-761`：`OBL-P8-05`「CHANGELOG `[Unreleased]` 含 task_id」，
  **`disposition: M`**（= 脚本执行），`enforced_at: {file: check-changelog.py, function: main}`，
  且登记了 pytest 凭证。
- 但**唯一生产调用点** `pre-commit-gate.py:1087`：
  ```python
  if phase == "P8" and _run_script_rc("check-changelog.py", [task_id], suppress_stderr=True) != 0:
      sys.stderr.write(f"GATE CHANGELOG: 警告 — [Unreleased] 未记录 {task_id}\n")
  ```
  **分支内无 `sys.exit()`** ⇒ 退出码被丢弃，仅打印告警。
- 对照同文件 `2n`（`check-p6-evidence.py`）与 `2z2`（`check-changelog-quality.py`）
  都有 `sys.exit(1)` ⇒ 不是风格差异，是本条**确实不阻断**。
- `check-gate.py:2330` 自 TAG0051（`9771e76a`，2026-10-11）起**不再**承载 CHANGELOG 检查，
  注释称「载体改为 `check-changelog.py`，已在 P8 必经路径 `pre-commit-gate.py` 内被调用，
  **判据强度不降**」——但该「必经路径」实为 WARNING ⇒ **该注释的强度声明不成立**。
- `check-obligations.py` 为何没抓到？它核的是 ①`enforced_at.function` 存在
  ②可从必经路径**到达**——`check-changelog.py:main` 确实被调用到，**核"可达"不核"其
  结果是否改变判定"**；`test_obligation_enforced` 也只断言 YAML 块里有 `enforced_at` 字符串
  （`test_tag0050_obligations_enforcement.py:93-99`）。
- ⇒ **`CHANGELOG [Unreleased] 含 task_id` 这条 READY 前置在实机上不阻断任何东西**，
  而登记表声称 M。
- **与报告的关系**：报告 §4 称赞 doctor「从『文件在不在』转向『能否真的工作』」，
  并说第 12 条是「同类症状」——**它自己脚下就有一条同型缺口，却没应用同一把尺子**。
- **对报告结论的影响**：第 13 条「不阻断交付」的方向正确，但**机理说错了**。
  真实原因是「**登记为 M 却只实现为 WARNING**」，不是「设计上只做 WARNING」。
  且**修好正则也不会恢复阻挡**——§6-P2③ 会让读者以为修完就生效。

#### (B) 次要：`WORKFLOW.md` 缺「阶段→通过码速查表」（见问 5 末）
#### (C) 次要：第 13 条的 `TPV01040` 判据说明正确，但未指出「修右边界后需同步加回归测试」
（现有 `test_check_changelog.py` 未覆盖全角边界，修完无守护）

---

## 必须修正项清单

| # | 报告位置 | 错在哪 | 应改成什么 |
|---|---|---|---|
| **M1** | §2.4（第 14 条）全节 | 断言「legacy 照抄 P6 卡推荐格式 → exit 1」**实测为假**（我构造真 legacy 任务跑出 exit 0）；且把机制错定为「legacy 解析」。真机制在 `check-judge-verdict.py` 的 `_check_whitelist_outside`（扫 `P6.5-dispatch-context-judge.md` 两节） | 改为：**这是 dispatch-context 信息隔离白名单，不是 legacy 解析冲突**；P6 卡推荐格式不会失败（括号组含空格/全角分号 ⇒ 整组被 `extract_conclusion_refs` 丢弃）；真正失败的是「dispatch-context 两节写出 `known-failures.md` 文件名」⇒ 只能改写为「任务目录下的预存失败登记文件」绕过（TPV0104 实况即此） |
| **M2** | §2.4「适用范围」行 + §0 结论表第 14 行 | 「**仅 legacy**」「TPV0104 是非 legacy ⇒ **本任务未踩到**」**方向恰好相反** | 改为：**适用范围 = 所有任务（不分 legacy）**；TPV0104（非 legacy）**踩到了**（`retrospective.md` 问题 2 即此现象）。「仅 legacy」应删 |
| **M3** | §6-P3（④） | 修法目标错：让「legacy 解析跳过非证据性文件名」修不到真问题 | 改为：真问题是 dispatch-context 白名单与「主 Agent 需向 judge 说明豁免来源」的张力。两条候选：① 主 Agent 一律用转述语（现做法，**已是事实标准**，可只做文档化）；② 若确要给 judge 一个可引用的锚点，应新增一个**白名单内的**转述载体（如 `P6.5-baseline-digest.md`），而非放开 `known-failures.md`。**先统计 legacy 存量不该是前置**——该问题与 legacy 无关 |
| **M4** | §2.1「适用范围」行 + §6-P1① | 「**所有任务**」高估：`plan-eng-review` 仅在 backend / risk=high / full 档派发（`review-mapping.md`、`OBL-P2-13`）；`plan-design-review` 的 `BDD\|基线` 命中亦为 0 ⇒ frontend-only 任务**永不生效** | 改为：「backend / risk=high / full 档任务已覆盖；**纯 frontend 且 risk 非 high 的任务仍无覆盖**」并在 §7 证据缺口登记该残余面 |
| **M5** | §2.1「P2 无对应义务」行 | 写「`OBL-P2-01`…`OBL-P2-10` 十条」，实际 `OBL-P2-01..17` 共 **17** 条 | 改为「`OBL-P2-01`…`OBL-P2-17` 共 17 条，无一涉及 BDD 语义核对」 |
| **M6** | §3.3 表格 | 「仅补格式/元数据 **7**」应为 **8**；「合计 **10(9 行)**」行数应为 **7 行**（报告自身也不自洽：2+7≠10） | 表格改为「真保护 2 / 格式 8 / 合计 10（明细表 7 行）」 |
| **M7** | §5.1 表格「用户参与」行 | 引文「P1 后回答两个问题，之后基本不需协调」在 `retrospective.md` 中**查无此句**（grep 零命中） | 换为可核实的实测：`orchestrator-log.md` 中「用户」出现 18 次，明确介入 ≥6 处（`:10` `:12` `:16` `:18` `:19` `:51` `:161`），据此说明「成本可数但未量化（无计时），且介入次数明显多于『两个问题』」 |
| **M8** | §2.3「影响」行 + §6-P2③ + §4 表格 | 第 13 条「不阻断」的**机理缺失**：真实原因是 `OBL-P8-05` 登记为 **M** 但 `pre-commit-gate.py:1087` 只 WARNING（无 `sys.exit`），`check-gate.py` 自 TAG0051 起已卸载该检查 | 补一句：「该义务在 `obligations.yaml` 登记为 M（脚本执行），但唯一调用点只告警不退出 ⇒ 实机无强制力；**修右边界不会恢复阻挡**，若要恢复需另议（改 `sys.exit(1)` 会改变 READY 前置语义）」 |
| **M9** | §6-P1①「可选加固」 | 未提示：新增 `disposition: R` 义务会**直接打红** `check-obligations.py`（我实测 `56/122 < 56/121` ⇒ FAIL），而它由全量 pytest 端到端跑 | 补一句：「增义务须**同批**更新 `obligations.yaml` 的 `baseline.reset`（一次性显式重设，写 CHANGELOG 留痕），否则 `check-obligations.py` 判 FAIL、全量 pytest 转红」 |
| **M10** | §6-P1①「验收条件」 | 「看 P2 评审是否**必然**提出该点」不可判定——自然语言提示无法保证「必然」 | 改为可判定形态：「构造反例时 `P2-review.md` 是否含针对该反例的显式结论（有/无）」 |
| **M11** | §6「无需处理」中「阶段通过码不同」条 | 整体归为「执行错误，不处理」，**驳回了复盘的最小诉求**（`retrospective.md:116` 改进措施 #4：加一张阶段→通过码速查表）；实测 `WORKFLOW.md`/`phase-cards/` 均无此表 | 改为：「统一退出码**不做**（会牵动 `agate-next.py` 三态语义）；但**加一张速查表**是零风险文档改动，建议采纳」 |

> **M1/M2/M3 应视为一个整体**（第 14 条的机制+范围+修法全链条），
> 单独改任一条都会留下矛盾。

---

## 报告做得好的地方（简短）

1. **证据是真跑出来的，不是纸面推断**：第 12 条四配置矩阵、第 13 条七写法矩阵，
   我逐格复现**全部命中**；第 11 条的 `obligations.yaml` / `gate_p2` / 两个 review-role
   三处落点核实也逐条成立。这在核实类报告里是少数。
2. **用最终版而非初稿，且主动纠正了初稿/复盘的夸大表述**：把「Judge 白名单自相矛盾」
   改成「白名单是设计，不要改它」——这是**逆着上游材料的错误结论走**，需要判断力。
3. **拒绝重提已证伪方案，且给了证伪数据**：§3.1 明确不重提「gate 逐条核对」，
   并说明 19/19 误报的机理。§6-P1① 提的「评审检查项」与之性质不同，**这个区分是对的**。
4. **「近期改动 ≠ 旧问题已解决」的对应关系建立得干净**：逐类给出「解决什么 / 与本 5 条
   的关系」，并给了 `[实测]` 依据。我用 `git log` 追加了更强证据，结论一致。
5. **边界声明诚实**：§7「未核实 / 证据缺口」、§1.3「未读收费标准原文 / 未做跨平台」
   都主动列出，没有把推断包装成实测。

---

## 给下游的处置建议

- **可**直接采用：§2.2（第 12 条）、§2.3（第 13 条，含七写法矩阵与修复验收条件）、
  §2.5（第 15 条已解决）、§3.1（不重提 gate 逐条核对）、§4（近期改动无关性）。
  这些我独立复现全部成立。
- **须先按 M1–M3 重写**：§2.4（第 14 条）与 §6-P3。**当前版本若照做会修错地方**。
- **须按 M4–M11 修订后再用**：§2.1 适用范围、§3.3 数字、§5.1 引文、§6 各条建议。
- **须补入**：M8 的 `OBL-P8-05` 缺口——建议单独立项，优先级不低于第 13 条，
  因为它是「登记为 M 却无强制力」的**判据失真**，属报告 §4 自己推崇的方法论问题。

---

*审查完。原始痕迹见 `TPV0104-assessment-review.progress.md`。*
