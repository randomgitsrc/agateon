---
phase: P1
task_id: TAG0051
trace_id: TAG0051-P1-review-20261011
status: approved
created: '2026-10-11'
agent: requirements-review
reviewed_bdds:
- 1
- 2
- 3
- 4
- 5
- 6
- 7
- 8
- 9
- 10
- 11
- 12
- 13
- 14
- 15
- 16
- 17
- 18
- 19
- 20
- 21
- 22
- 23
---

# P1 需求基线评审 — TAG0051（任务与发布解耦）— **复审（retry 2，轻量定点）**

> **被评审对象**：`agate-workspace/tasks/TAG0051-release-decoupling/P1-requirements.md`（**525 行 / 23 条 BDD**，本轮 retry 2 修复后）。
> **角色**：requirements-review（独立 subagent，agent≠main）；**只审不写**——本文件不改被评审对象。
> **本轮口径（轻量定点复核，我自己上轮给出的重评口径）**：只核 retry 2 指引「定点核验清单」3 项——(D') 是否真闭合 / (A-残余) 是否闭合 / 有无新破坏。**不重做 §五 22 项、不重跑回归全表**（断言未变）。
> **环境隔离**：`[PROD_NOT_TOUCHED]`——评审前后真实仓库 `git status --porcelain` **一致**（`MM .state.yaml` + 10 个 `??` 未跟踪任务文件；`git status --porcelain -- agate/` 行数 = **0**，协议/脚本/测试零改动）。回滚/探针类实测均在 `/tmp/opencode` 一次性副本。
> **结论**：**approved** —— 3 项定点全部闭合且无新破坏；上轮确认的 (A)(B)(C)(E)(F) 闭合与「§五 22 项事实断言全部成立」继续有效。**无必改项，无新增可选打回项。**

---

## 一、定点核验 3 项（本轮唯一评审焦点）

### 1. (D') 是否真闭合 —— **已闭合** ✓

**① 合并为单条穷尽分支 BDD**：`BDD-24` 已不存在（`grep -n 'BDD-24'` rc=1，零命中）；新增**单条** `BDD-23`（:288-291）：

> `#### BDD-23: 发布门三种落点（穷尽互斥）下 SG.6 与 CHECK9-coverage 判定正确`
> - Given 三种互斥落点之一：① `agate/scripts/check-*.py`；② `agate/scripts/agate-*.py`；③ `release.yml` 内新增步（**不**新增 `agate/scripts/` 文件）
> - When 运行 SG.6 与 `check-protocol-consistency.py`（CHECK9-coverage）
> - Then 三支穷尽、每支恒可判 PASS/FAIL：① 已登记则 SG.6 通过（未登记 SG.6 红→FAIL）；② 零触发（SG.6 不红、无新增 WARNING/ERROR）→PASS 反之 FAIL；③ 无新增 `agate/scripts/` 文件、登记面无适用项、无**新增** WARNING/ERROR →PASS 反之 FAIL

⇒ **三支穷尽且互斥**（`check-*.py` / `agate-*.py` / 无新增脚本三种落点覆盖穷尽，互不重叠），**每支自带 PASS/FAIL 终结判据**（且有「反之 FAIL」兜底）⇒ **恒可判、无中间态、无覆盖空洞**。**相较上轮的建议 1 甚至更完整**：合并时**新增了第③支**（`release.yml` 内步），把上轮 BDD-23/24 **未覆盖的第三落点空洞**一并堵上。

**② N/A 类表述删净**（全部为 0）：

| 检索 | 计数 | 结论 |
|------|------|------|
| `grep -c 'N/A'` | **0** | ✓ 删净 |
| `grep -c '不计入 P6 的 PASS'` | **0** | ✓ |
| `grep -c '转无条件'` | **0** | ✓（隐含「P2/P6 可改 P1 BDD 文本」句已移除——消除与 P1 基线保护相抵） |
| `grep -c '命中项'` / `'取其一'` | **0** | ✓ |
| `grep -c 'BDD-24'` | **0**（rc=1） | ✓ |

§3 前言（:149-153）现表述为：「**条件式 BDD 的穷尽分支写在单条 `Then` 内**（如 BDD-23 覆盖三种互斥落点）——**始终可判、无中间态、无覆盖空洞**；**P6 逐条记 PASS/FAIL**」。**不再有任何「某条 BDD 可以不产生 verdict」的语义**。

**③ 与 P6 `_gate_p6_structured` D1/D2 相容**（**关键项，已独立复现**）：
- `check-gate.py::_gate_p6_structured`（`AGATE_ROOT=/home/kity/.agate/v0.81.0/agate`，:1446-1480）：
  - **D1**（:1462-1471）：`results` 的 `bdd` 集合须**逐条等于** `_bdd_id_set_from_p1`（P1 全集），否则 exit 1；
  - **D2**（:1473-1480）：**所有** `verdict == "PASS"` 才过。
- 新 BDD-23 是**无条件单条 BDD**，P6 必须且只能给它记 PASS 或 FAIL ⇒ `results` 恒含 **23** 条 bdd、与 P1 全集 `[1..23]` 相等、`verdict` 恒可判 ⇒ **D1/D2 天然满足**。
- ⇒ **上轮 (D') 的「N/A/不计 PASS ⇒ D1 集合不等 ⇒ gate exit 1」硬冲突已彻底消除**；新表述（含 §3 前言「P6 逐条记 PASS/FAIL」）**不含**任何可被解读为「某条 BDD 不产 verdict」的措辞。

### 2. (A-残余) 是否闭合 —— **已闭合** ✓

§4.1 `check-protocol-consistency.py` 行（:317）现为：

> **本次处理（仅措辞，非逻辑）**（**BDD-12**：该文件的**门行为**由 BDD-12 承接——运行它须 CHECK 7/13 各 0 ERROR）。CHECK 7 逻辑**已 tag 无关**（RM-AG0098 落地），**不复改逻辑**；**措辞同步属条件性**（仅当发布入口/流程名变化时触发），触发时该提示句须与新独立发布流程口径一致，其可判定性由 **BDD-12 的门判定（该脚本 0 ERROR）间接覆盖**。

**一致性核对**（判定面 vs 承接 BDD）：
- 该行**已把「门行为」与「措辞」两件事显式分开**：「门行为」= BDD-12 的判定面（`check-protocol-consistency.py` 运行时 CHECK 7/13 各 0 ERROR）——**判定面确含该文件**；「措辞」被标注为**条件性**（仅当入口/流程名变化时触发），其可判定性**由 BDD-12 的门判定间接覆盖**。
- ⇒ 不再是「承接 BDD-12，但 BDD-12 判定面不含措辞」的**混同**；声明与判定面**已对齐**。此修法即我上轮 (A-残余) 建议的「注明措辞属条件性、由 BDD-12 门判定间接覆盖」**逐字落地**。
- 另核：§4.1 **无**「本次处理」行缺 BDD 承接（每行承接 BDD 与其判定面逐行复核一致：P8 卡/`state-machine`/`state-transitions`/`phases.yaml`/`implementer`/`dispatch-protocol`→**BDD-1**；`obligations.yaml`→**BDD-21**；`check-gate.py`→**BDD-2**；`check-protocol-consistency.py`→**BDD-12**；`git-integration.md`/`AGENTS.md`→**BDD-14**；`release.yml`→**BDD-8**+发布门 **BDD-9/10/12/13**；`agate-release.py`→**条件性 BDD-9 或按「不改动」处理（无协议变更、无需 BDD 承接）**；`UPGRADING.md`→**本次不处理、显式不承接**）。

### 3. 无新破坏 —— **已闭合** ✓

**结构计数（全部实测）**：

| 判据 | 期望 | 实测 | 结论 |
|------|------|------|------|
| `^#### BDD-` 计数 | 23 | **23** | ✓ |
| 编号连续无跳号/无字母后缀 | 1..23 | 行 157/162/167/172/177/182/187/202/207/212/217/224/229/234/240/247/252/257/263/271/276/283/288 ⇒ **1..23 连续**；`^#### BDD-[0-9]*[a-z]` = **0** | ✓ |
| `- Given` / `- When` / `- Then` 各计数 | 各 23 | **23 / 23 / 23**（每条恰一组 G-W-T） | ✓ |
| `且 Given` | 0 | **0** | ✓ |

**BDD-1..22 未被删场景 / 未改软**（本轮为**定点**核验，非重做）：
- **行号锚点复核**：上轮 review 对「BDD-1 `Given`（:158）」「§3 功能组 2 附注（:194-200）」「BDD-18 `Then`（:260-261）」「§3 前言（:152-153）」的引用**行号与文本逐字吻合**（`BDD-1 Given` 仍为六文件枚举句于 :158；BDD-18 `Then` 仍为「人工授权入口（当前实现为 `workflow_dispatch`）…不引入第二套阻塞确认语义」于 :260-261）⇒ **行 1..~287 的字节布局与上轮一致**，retry 2 改动止于 BDD-23（:288+）与 §4.1 表行。
- **改动面差分**（对 `/tmp/opencode/probe-req.md`＝**首轮 20-BDD 版**做整篇 diff，作为「场景未丢」的独立证据）：全部差异可归为 (i) retry 1 的 (A)(B)(C)(E)(F)（BDD-1 判定面 3→6 文件；BDD-4/5、6/7、16/17 由内嵌**拆分**为独立编号；功能组 2 加载体/优先级附注；`packages` 增 `agate-docs`；BDD-18 去机制名绑死；§4/§5/§6/§9 编号同步重排）与 (ii) retry 2 的 (D')(A-残余)+§4.1 计数措辞。**无任何既有场景被删除/被合并掉/被改软**；场景数 20→（拆分后 24）→（合并 BDD-23/24 后）**23**，**合并同时新增了第三落点分支**（净为**加严**）。
- **反例 BDD 独立完整性**：`BDD-5` / `BDD-7` / `BDD-17` 仍各为独立完整三行（标题带「（BDD-N 反例）」）✓。
- ⇒ **retry 2 未引入新破坏**。

---

## 二、BDD 评审（逐条 + 覆盖维度；本轮沿用上轮结论，编号集合更新为 1..23）

覆盖维度口径：数据 / 前端 / 多端（卡·状态机·规则表·gate·CI·AGENTS·config 多处同步）/ 边界 / 兼容。

| BDD | 判定（可二值 PASS/FAIL） | 覆盖维度 |
|-----|------------------------|---------|
| BDD-1 | 可二值（六处语料面检索零命中，排除项显式） | 多端✓ 兼容✓ |
| BDD-2 | 可二值（stderr 无 tag 告警 + exit 2） | 多端✓ 兼容✓ |
| BDD-3 | 可二值（stderr 无 version 告警 + exit 2） | 多端✓ 兼容✓ |
| BDD-4 | 可二值（`check-changelog.py` exit 0） | 数据✓ 兼容✓ |
| BDD-5 | 可二值（`check-changelog.py` exit 1，独立反例） | 数据✓ 兼容✓ |
| BDD-6 | 可二值（有 `bump_type` → exit 2） | 多端✓ 兼容✓ |
| BDD-7 | 可二值（缺 `bump_type` → exit 1，独立反例） | 多端✓ 兼容✓ |
| BDD-8 | 可二值（解析 `on:` 含 `workflow_dispatch`） | 多端✓ 安全✓ |
| BDD-9 | 可二值（发布门 exit≠0 / 通过） | 边界✓ 安全✓ |
| BDD-10 | 可二值（PR 绿 + push 口径红 → 判失败） | 边界✓ 兼容✓ 安全✓ |
| BDD-11 | 可二值（badge≠tag 或版本节空 → 判失败；承接 RM-AG0098 不重复实现） | 数据✓ 多端✓ 兼容✓ |
| BDD-12 | 可二值（CHECK 7/13 各 0 ERROR；自带替代载体） | 多端✓ 兼容✓ |
| BDD-13 | 可二值（RM 非 done → 判失败；与 `gate_p8` RM-AG0043 兜底优先级已显式） | 数据✓ 多端✓ |
| BDD-14 | 可二值（全文检索 tag 时点一致；`AGENTS.md`+`git-integration.md` 归 `agate-docs`） | 多端✓ 兼容✓ |
| BDD-15 | 可二值（顺序「先回退重打、后补丁」可判） | 边界✓ 安全✓ |
| BDD-16 | 可二值（合法枚举 → exit 2） | 数据✓ 兼容✓ |
| BDD-17 | 可二值（枚举外非空 → exit 1，独立反例） | 数据✓ 兼容✓ |
| BDD-18 | 可二值（检索 `state-machine.md` 授权描述；去机制名绑死 + 不引入第二套确认语义） | 多端✓ 安全✓ |
| BDD-19 | 可二值（无悬空提示 + consistency 0 ERROR） | 多端✓ 兼容✓ |
| BDD-20 | 可二值（未匹配 0 条 + 真实仓库干净；载体 `r6-differential.sh` 实测存在） | 数据✓ 兼容✓ 多端✓ |
| BDD-21 | 可二值（anchor 无悬空 + 测试全绿；上轮实跑 66 passed） | 多端✓ 兼容✓ |
| BDD-22 | 可二值（commit message 含 `self-gate-review:` + 路径真实存在） | 多端✓ 兼容✓ |
| **BDD-23** | 可二值（**三落点穷尽分支单条 BDD**，每支恒可判 PASS/FAIL；无 N/A） | 多端✓ 兼容✓ |

---

## 三、隐含需求覆盖（沿用上轮结论，未因 retry 2 改变）

| 维度 | 结论 | 依据 |
|------|------|------|
| 数据 | ✓ 覆盖 | §2.1（legacy 账本/契约快照）+ BDD-4/5/14/20；「仅 TAG0051 有 `task_created`」实测成立 |
| 前端 | ✓ 不适用（已显式声明） | §2.7 + §8：无用户可见页面、无 UX BDD、`domains` 不含 frontend ⇒ 不触发 vision 能力门 |
| 多端 | ✓ 覆盖 | §2.2 九处；BDD-1（六处语料面）+ BDD-12/14/19/21 覆盖 gate/CI/AGENTS/config/obligations |
| 边界 | ✓ 覆盖 | 回退/重打/授权（BDD-15/18）+ 竞态（BDD-9/10 fail-closed） |
| 兼容 | ✓ 覆盖 | BDD-20（legacy 双向差分）+ BDD-16/17（仅新声明生效）+ §9 契约冻结（`level-2.yaml`） |
| 安全 | ✓ 覆盖 | §2.6 + BDD-9/15/18 + §9「不可逆外部动作须用户授权」；`domains: [security]` ⇒ P4 映射 `cso` |
| 多仓/多项目（协议中立性） | ✓ 覆盖（协调项） | §2.3 + §0：RM-AG0116 已补登记（roadmap，`done` + `hotfix-branch-neutral`） |

---

## 四、裁剪评审（未变）

- **无裁剪**：`phases: [P1..P8]` 全 8 项、`pruned` 空 ⇒ `phases ∪ pruned == phase_universe` 恒检成立。
- 逐条理由充分：**P3 不裁**（发布门/枚举/gate 行为变更须先有失败测试，TDD）；**P7 不裁**（六处 tag 条件跨文件核对是本任务核心风险）；P2/P4/P5/P6 核心阶段不可裁 ⇒ 无「跳过风险」需声明，正确。
- `risk_level: high` 与风险匹配（协议本体 + gate 脚本 + CI workflow + 不可逆对外发布语义，跨 5+ 子系统）。
- `ceremony` 未声明 ⇒ fail-closed `standard`（写工具白名单缺口 = DEBT0067，主 Agent 已登记并扩大面）；等价性已核：`risk_level: high` → `plan-eng-review`（P2）+ P4 域评审，`domains: security` → `cso`（P4），`phases` 含 P7 ⇒ **机制上不减少任何评审触发**。**不打回**。
- `capability_requirements: []` 判断树正确（CI success 查询在 Actions 运行时执行、本地 P6 用 fixture/mock ⇒ 验证方式非能力缺口）。

---

## 五、审声明（风险分级/裁剪声明 vs 证据，未变）

- **证据（暂存区）**：`git status --porcelain` —— `agate/` 内**无** `M`/`D`（`git status --porcelain -- agate/ | wc -l` = **0**）；`P1-requirements.md` 仍为 `??` 未跟踪（评审通过后由主 Agent 提交）。核对对象取「本任务声明的改动面」（§4.9 活面清单 15+ 文件 / 9 packages / 5+ 子系统）。
- `risk_level: high` ↔ 改动面：**匹配**。
- `phases` 全阶段 ↔ 无裁剪：**匹配**。
- `packages`（**9 项**，含 `agate-docs`）↔ §4.9 清单：**匹配**（首轮 (E) 缺口已闭合）。
- `domains: [backend, security]` ↔ 改动面：**匹配**；无 frontend ⇒ 无 UX/vision 义务。
- `ceremony` 缺省 standard ↔ 评审触发：**不减少**；`P7` 显式在 `phases` 内。
- `[NO_NEED_CONFIRM]` + 1 条 `[SUGGEST]`：合法（SUGGEST 不阻塞）；无 `[NEED_CONFIRM]`、无 `status: GAP`。
- `.state.yaml`（`phase` 由主 Agent 维护）：不在本次评审面（gate P1 只读 P1-requirements.md 与 P1-review.md）。

---

## 六、历轮闭合状态（对照痕迹）

- **首轮 20 BDD**：22 项事实性断言**全部独立复现成立**（上轮 §五表）；(A)–(F) 必改/随改。
- **retry 1（24 BDD）**：**(A)(B)(C)(E)(F) 均闭合**，回归核验通过（4 处为拆分、BDD-1/BDD-18 反被加强）；**唯一必改 (D')**（N/A 表述与 P6 D1/D2 冲突）+ (A-残余) 随改。
- **retry 2（23 BDD，本轮）**：**(D') 已闭合**（合并为单条穷尽分支 + 新增第三落点 + N/A 类表述全删净 + 与 D1/D2 相容）；**(A-残余) 已闭合**（声明与判定面对齐）；**无新破坏**（结构计数全对、BDD-1..22 未删未软、场景净加严）。
- ⇒ **无必改项残留**；上轮 (A)(B)(C)(E)(F) 与 §五 22 项断言结论**继续有效**。

---

## 七、结论

**status: approved**

- **`reviewed_bdds` 逐条相等**：`[1..23]` = 当前 P1 的 `#### BDD-NN:` **全集**（连续 1→23，无跳号、无字母后缀）✓（gate_p1 机械判据）。**与上轮 `[1..24]` 的差异如实记录**：retry 2 按我方 (D') 建议 1 把 BDD-23/24 **合并**为单条穷尽分支 BDD（并补齐第三落点）⇒ 24→23。
- **(D')**：**已闭合**——单条 BDD-23（三落点穷尽互斥、每支恒可判）；`grep -c 'N/A'` = 0、`不计入 P6 的 PASS` = 0、`转无条件` = 0、`BDD-24` = 0；与 `_gate_p6_structured` **D1/D2 相容**（无条件单条 ⇒ 恒入 `results` 且可判别说 `verdict`，无「某条 BDD 不产 verdict」语义）。
- **(A-残余)**：**已闭合**——§4.1 `check-protocol-consistency.py` 行已把「门行为（BDD-12 判定面）」与「条件性措辞（由 BDD-12 门判定间接覆盖）」显式分开，声明与判定面对齐。
- **无新破坏**：`#### BDD-` = 23 连续 1..23；Given/When/Then 各 23；`且 Given` = 0；BDD-1..22 行号锚点与上轮逐字吻合、未删场景/未改软（差分证据：场景 20→23 净加严）。
- **审声明**：`risk_level: high` / 全阶段无裁剪 / 9 packages / `[backend, security]` 与改动面匹配；`ceremony` 缺省 standard 不减少评审触发；`capability_requirements: []` 正确 ⇒ **通过**。
- **环境隔离**：`[PROD_NOT_TOUCHED]`——评审前后真实仓库 `git status --porcelain` 一致，`agate/` 零改动。
