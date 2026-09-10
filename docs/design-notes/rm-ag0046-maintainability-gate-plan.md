# RM-AG0046 落地计划 v2：维护性反模式 gate（G0 优先，diff 驱动）

> **状态：已落地（TAG0026，v0.65.0，RM-AG0046）**——本文为落地前的计划记录，保留作决策追溯。
> v1 → v2 修订说明见文末「评审记录 v1→v2」。
> v2 → v3 修订：独立评审（peek.gsis.top/uucahi）发现 2 BLOCKER + 1 WARNING + 2 NIT，本版逐条修复，记录见文末「评审记录 v2→v3」。

---

## 0. v3 核心修正摘要（先说清楚改了什么，再看正文）

- **挂载阶段从 P6 改为 P4**：v2 把检测器挂在 P6，但代码在 P4 阶段就已经 staged/commit（`gate_p4` 校验 `git diff --cached` 含代码文件，见 check-gate.py:893-900），P6 提交时暂存区只剩验收文档——按 v2 的写法，检测器在 P6 是**死代码，永远零命中**。这是纯粹的事实错误，不是设计取舍，v3 直接改正。
- **删除"登记内容进 provenance 审计范围"的虚构声称**：核实 `check-p6-provenance.py` 现有七道审计，无一道涉及 known-violations/known-failures 登记内容。v2 这句话没有依据，v3 删除，不新增第八道审计（范围裁剪，见第6节）。
- **重新设计 known-violations 的放行条件**：known-failures 登记的是"预存失败、非本任务造成"，known-violations 登记的是"本任务自己引入的反模式"——这是两种性质相反的登记，"数量对齐即放行"这套算法可以照抄，但"登记即可放行"这个结论不能照抄。v3 改为"登记 + 数量对齐 + P4 评审角色 approve"三重門檻，不是单靠登记数量。

---

## 1. 范围裁剪：这次做什么，不做什么

设计文档统计过 G0/G1/G2/G3 占比（20% / 20% / 25% / 35%）。全量落地不现实——G2（条件纠缠、薄抽象、顺序耦合）需要 AST 级分析，工作量大、误报风险高，不适合第一版。

**本次只做 G0 两条**（最高确定性、最低误报率、和 `agate-risk-score.py` 模式完全同构）：

| 反模式 | 判据 | 为什么选它 |
|---|---|---|
| **God File 跨越** | diff 前后 `wc -l`，`before < N and after >= N` 触发 | 设计文档给出精确判据（决策2：跨越≠超过），零歧义，纯算术 |
| **Fuzzy Boundary（模糊边界）** | diff **新增行**匹配语言相关"类型逃逸"模式（Python `# type: ignore`/裸 `except:`；TS `any`/`as any`） | 同样 diff 驱动、正则可判；直接对应 agate 自身 Python 代码库真实需求 |

**明确不做**：
- G1（DRY 重复检测）：需先建 canonical 清单，人工维护成本高，留到 G0 验证有效后再评估。
- G2（条件纠缠/薄抽象/顺序耦合）：设计文档自己写"半自动"，检测器实现成本和误报率都不确定。
- G3：不进 gate，维持 LLM 心法。
- RM-AG0022 结构化层联动（语义进 `rules/*.yaml`）：属于另一个 roadmap 条目，本次只用现有 markdown + Python 脚本形态。

这个裁剪写进 P1 的 SCOPE 声明，防止范围蔓延。

---

## 2. 落点：新脚本 + 两处 phase card 挂载 + check-gate.py 挂钩

### 2.1 新脚本 `agate/scripts/check-maintainability.py`

复用 `agate-risk-score.py` 的既有模式：

```python
"""check-maintainability.py — 维护性反模式 diff 驱动检测（RM-AG0046 G0）

god-file       diff 前后 wc -l，before < N and after >= N → violation
fuzzy-boundary diff 新增行匹配类型逃逸模式（语言由扩展名路由） → violation

模块形态：check_maintainability(task_dir) -> dict，可 import（供 check-gate.py 复用）。
CLI 为薄壳，exit code 是唯一判定依据——不依赖 verifier 的文字描述（BDD-9 红线对齐）。
"""
```

- `god_file_check(staged_files, repo_root) -> list[dict]`：`git show HEAD:path` 算 before 行数（新增文件 before=0），工作区当前文件算 after 行数，判定"跨越"（不是"超过"，对齐决策2）。
- `fuzzy_boundary_check(staged_files) -> list[dict]`：只扫 diff **新增**行（`git diff --cached -U0`，前缀 `+` 且非 `+++` 的行），按扩展名路由正则集。**新增行判定用现有 diff 机制天然处理"移动代码"边界**——若一段含裸 `except:` 的代码被移动，diff 会同时显示为删除行（旧位置）+ 新增行（新位置），这在纯文本 diff 层面确实会被判定为"新增"违规。这是已知的假阳性来源，本版**不引入跨行匹配的移动检测**（复杂度和 God File 判据的"零歧义"原则冲突），而是通过 known-violations 的客观登记机制处理（见2.3），不是假装能自动识别"移动 vs 真新增"。
- 阈值与正则集可配置：读取 `agate-workspace/maintainability.yaml`（**不用 `.agate/`**——该前缀是用户级版本管理根目录 `~/.agate` 的专属命名空间，ADR-009 已界定；项目级协议配置统一放 `agate-workspace/` 下，与 `agate-workspace/roadmap/`、`agate-workspace/tasks/` 同级），缺失时用协议默认值（God File N=1000，来自 Cursor skill 原始阈值，**无实证依据，仅供参考**，文档需明确写清楚）。
- 返回结构对齐 `agate-risk-score.py` 的 `score_task()` 形状：`{"violations": [...], "god_file_count": N, "fuzzy_boundary_count": M, "git_ok": bool}`，供 `check-gate.py` 直接 import 调用，不走 subprocess 解析文本输出。

### 2.2 P4 gate 挂钩（不是 P6——修正 v2 的挂载阶段错误）

**为什么必须是 P4，不是 P6**：`gate_p4`（check-gate.py:870-900）在 pre-commit 时校验暂存区含代码文件，这正是代码改动被 staged 的时刻。P5 是验证阶段（跑测试），P6 提交的是验收文档——`git diff --cached` 到 P6 时已经不含代码 diff。检测器的数据源（`git diff --cached`）必须和它被调用的阶段对齐，否则是永远不会命中的死代码。

参考 `check-gate.py` 现有 P5 known-failures 判定的函数形态（读客观快照 diff 算数字 → 与登记数量比对 → 返回值判定），`check-maintainability.py` 挂载到 **P4** 走类似结构，但放行条件比 known-failures 更严格（见下方"三重门槛"）：

```
check-gate.py 的 P4 判定函数（gate_p4）新增一步：

1. 调 check_maintainability(task_dir) 拿到 violations 列表（客观算出，git diff --cached 此时确实
   包含本次 commit 的代码改动，数据源与挂载阶段对齐）
2. violations 为空 → 直接通过，跳过后续
3. violations 非空 → 三重门槛（不是"登记即放行"）：
   a. agate-workspace/tasks/{Txxx}/known-violations.md 是否存在
      - 不存在 → exit 1（"检测到 N 个维护性反模式 violation，需登记 known-violations.md"）
   b. 登记条目数是否 >= violations 数量（复用 P5 known-failures 的数量对齐算法）
      - 登记条目数 < violations 数量 → exit 1（"登记条目数(X) < violation 数(N)，登记不完整"）
   c. P4-review.md status 是否为 approved 且 agent != main（复用 P4 现有评审闭环，
      见 P4-implementation.md「评审」节；gate_p4 本身已有这个检查，本次只是要求
      评审角色在 approve 前必须读过 known-violations.md 的登记理由——这是流程要求，
      写进 P4 phase card 的评审 checklist，不是新增一个独立的 approve 字段）
      - 三项都满足 → 放行（returns值以 P2 architect 阅读 check-gate.py 全文后确定为准）
```

**为什么需要 c（P4 评审 approve），不是只有 a+b（对齐 v1→v2 修复的错误方向）**：v2 曾经犯过"登记数量对齐就放行"的错误，这次独立评审（B3）指出一个更深的问题——known-failures 宽容的是"预存的、非本任务造成的问题"，known-violations 宽容的是"本任务自己引入的新反模式"，这是两种性质相反的登记。如果只要求"数量对齐"就放行，等于"只要肯写理由，引入任意数量反模式都没有代价"，这比没有这个gate还糟，因为它给"引入反模式"发了一张打折券。**加上c（P4评审角色必须读过登记理由才能approve）**，把"是否接受这个反模式"的判断权交还给现有的、独立于implementer的评审角色（P4-review.md的评审本来就要求`agent != main`，即不能是主Agent自己批准），而不是让"数量对齐"这个纯算术条件单独构成放行依据。这不是新发明一层机制，是把已有的P4评审闭环和已有的known-failures数量对齐算法组合起来，各自发挥各自能做的部分。

**不新增第八道provenance审计**（对齐第0节修正2）：本次不改动`check-p6-provenance.py`，known-violations的登记内容不进入现有七道审计范围。如果未来需要对登记内容做机械化审计（比如核实登记理由不是空话），属于独立的后续评估，本计划不预先承诺。

### 2.3 P6 phase card（改为单纯的自查提醒，不是强制阻断点——对调v2的P4/P6角色）

`agate/phase-cards/P6-acceptance.md`「自查≠gate」节新增一条：verifier 在验收自查阶段可再跑一次 `check-maintainability.py`，确认 P4 之后（P5/P6 阶段）是否有新的代码改动引入反模式。这只是自查清单项，真正的强制阻断点在 P4（2.2 节）；P6 阶段 `git diff --cached` 通常已不含代码 diff，故不把 P6 作为判定挂载点。

---

## 3. 和现有机制的具体挂钩（不新增判定权归属的哲学）

| 复用点 | 具体做法 |
|---|---|
| `agate-risk-score.py` 的信号-证据模式 | 返回结构（dict）同形状，供 `check-gate.py` 直接 import |
| `_load_script` importlib 加载模式 | 复用同一 helper，不重复实现加载逻辑 |
| P5 known-failures 的"客观快照 diff + 登记数量硬校验"模式 | known-violations 机制完整照抄这套逻辑，**不是抄表面格式，是抄判定算法**（这是 v1→v2 最核心的修正） |
| `gate_commands` 声明式插拔 | `check-maintainability.py` 是协议自带**参考实现**，P2 architect 可在 `gate_commands` 换成项目自有等价工具（如已有 ruff 规则覆盖 fuzzy-boundary 的场景），只要语义等价并同样输出可判定 violation 数量 |
| BDD-9 哲学红线 | P4 判定完全落在 exit code，不依赖 verifier 文字描述 |

---

## 4. BDD 验收标准

1. **God File 跨越检测**：900行文件（N=1000）diff 后变 1150 行 → `check_maintainability()` 返回含该文件的 violation，exit 1。
2. **God File 不误伤存量**：已有1200行文件，diff 只改5行（不跨越阈值）→ 无 violation，exit 0。
3. **Fuzzy boundary 检测（Python）**：diff 新增一行裸 `except:` → violation 含文件名+行号。
4. **Fuzzy boundary 不误伤存量**：文件已有的裸 `except:`（非本次diff新增）不触发。
5. **阈值可配置**：`agate-workspace/maintainability.yaml` 声明 `god_file_threshold: 500` 时，480→520行触发；默认值(1000)下不触发。
6. **配置缺失兜底**：无配置文件时用默认值N=1000，不报错不静默跳过。
7. **P4 gate 三重门槛（核心BDD，对应B1+B3修复）**：violations非空且 `known-violations.md` 不存在 → `check-gate.py` 的 `gate_p4` 返回1（阻断，不管verifier/implementer输出什么文字）。
8. **登记数量硬校验**：violations=3，`known-violations.md` 只登记2条 → 仍返回1（"登记不完整"），不是"有文件就过"。
9. **登记数量对齐但评审未approve仍阻断（核心BDD，对应B3修复）**：violations=3，登记3条，但`P4-review.md`不存在或status非approved → 仍返回1，不能靠"数量对齐"单独放行。
10. **三重门槛全部满足才放行**：violations=3，登记3条，`P4-review.md` status=approved 且 agent≠main → 放行，登记内容**不**进provenance审计（对齐第0节修正2，本次不新增第八道审计）。
11. **平台无关性**：Windows路径分隔符不影响检测结果（复用 `_norm_rel` 归一化模式）。
12. **移动代码假阳性的诚实处理**：构造"代码从A位置移到B位置，内容含裸except:"的diff → 判定为violation（已知假阳性，非bug），验证known-violations三重门槛能正常处理这种"合理但需登记+需评审确认"的场景。
13. **数据源与挂载阶段对齐验证（新增，直接针对B1教训）**：构造一个任务，P4阶段commit代码后，P6阶段只commit验收文档 → 验证`check_maintainability()`在P4阶段被调用时能读到代码diff（而非等到P6才调用、读到空diff）。这条BDD的存在本身就是为了防止"检测器挂载阶段与数据源时机错位"这类问题再次发生而不被测试覆盖。

配套要求：新脚本需要 `agate/tests/` 下对应 pytest 用例覆盖以上13条（对齐现有96个测试文件的覆盖惯例），不是只写BDD文档不写测试。

### 4.1 known-violations.md 登记模板（对应N2修复，v2遗漏）

`count_kf_entries`（agate_common.py:1015-1017）数的是表格行首 `| N |` 格式，known-violations若要复用同一计数函数，必须沿用同样的表格结构。P1/P2阶段前需在`agate/assets/templates/`新增`known-violations-template.md`，格式对齐`known-failures-template.md`但语义反转：

```markdown
---
task_id: {Txxx}
generated_by: {agent}
---
# 维护性反模式登记

> **语义边界**：本文件登记**本次任务diff引入的**维护性反模式（god-file跨越/fuzzy-boundary新增行），
> 与known-failures.md（登记预存失败）语义相反——这里登记的是"本任务自己造成的"问题。
> 登记 + 数量对齐 + P4评审approve 三者齐全才放行，登记本身不构成放行依据。

## 本次引入的反模式

| # | 文件 | 反模式类型 | 理由 | P4评审确认 |
|---|------|-----------|------|-----------|
| 1 | | god-file跨越 / fuzzy-boundary | | 是/否 |
```

「P4评审确认」列不参与`count_kf_entries`的机械计数（该函数只数行数），是给评审角色人工填写的可读性字段，机械判据仍然是"表格行数≥violations数量"+"P4-review.md status:approved"两个独立信号的组合，不依赖这一列的内容。

---

## 5. 已知风险与诚实边界（写进设计文档，不等外部发现）

- **Fuzzy boundary 正则集覆盖不完整**：仅覆盖 Python/TypeScript 最常见逃逸模式，其它语言（Go `interface{}`、Java `@SuppressWarnings`）不在本版范围，需在文档明确写"协议参考实现覆盖Python/TS，其它语言项目需在 `gate_commands` 自行补充等价检测"。
- **G0本身仍是self-authored gate的一个环节**：判定逻辑是机械算法（不依赖LLM主观判断"这是不是反模式"），但verifier仍是运行脚本、读exit code的那个agent——如果verifier想在CLI层面造假（比如声称跑过了实际没跑），这条局限和局限3同源，本次任务**不解决**"判定过程是否被诚实执行"，只解决"判定标准是否客观"。这个区分必须在设计文档和CHANGELOG写清楚，避免造成"self-authored gate问题已被解决"的错觉。
- **阈值N=1000无实证依据**：抄自Cursor skill经验值，需写明"默认值仅供参考，项目可自行调整"。
- **移动代码导致的假阳性**：见2.1/BDD-12，明确记录为已知行为而非缺陷，靠known-violations登记机制吸收，不试图做跨行移动检测。

---

## 6. 不做的事（防范围蔓延）

- 不做RM-AG0022结构化层联动（反模式语义进`rules/*.yaml`）——留给未来独立评估。
- 不做门户/可视化面板——纯CLI脚本+exit code，符合"零基础设施"路线。
- 不扩展到G1/G2——见第1节。
- 不做跨行移动代码识别——见第5节，用登记机制吸收而非算法消除。

---

## 评审记录（v1 → v2）

**自我评审发现的问题**：

1. **（已修复，架构级）** v1的BDD-7写成"verifier不能输出PASS"，这是对agent行为的期望，不是机械判定——违反协议自己的BDD-9红线（"exit code才是门槛"）。v2改为：判定完全落在`check-gate.py`导入的函数返回值，不依赖verifier的任何文字声明。

2. **（已修复，架构级）** v1设计的"known-violations登记即放行"，没有约束登记数量必须和violation数量对齐，等于给一个本来是G0（纯机械无主观空间）的检测重新开了self-authored的后门——只要愿意写理由就能绕过。v2改为完整复刻`check-gate.py`现有P5 known-failures的"客观快照diff算数字 + 登记条目数≥该数字才放行"判定算法。

3. **（已修复）** v1未提配套pytest测试要求。v2补充明确要求。

4. **（已修复）** v1的`.agate/maintainability.yaml`路径与用户级`~/.agate`命名空间（ADR-009已界定）冲突。v2改为`agate-workspace/maintainability.yaml`。

5. **（已处理，诚实承认而非算法消除）** v1未讨论"移动代码导致假阳性"边界。v2明确说明是diff文本层面已知局限，不引入跨行移动检测算法，改用known-violations登记吸收。

## 评审记录（v2 → v3，独立评审 peek.gsis.top/uucahi）

独立评审发现 2 BLOCKER + 1 WARNING + 2 NIT，均已核实属实并逐条修复：

1. **B1（BLOCKER，已修复）**：v2把检测器挂在P6，但代码在P4阶段就已staged/commit（`gate_p4`校验`git diff --cached`含代码文件，check-gate.py:893-900），P6提交的是验收文档，`git diff --cached`到P6时不含代码diff——按v2写法检测器是**永远零命中的死代码**。这是我在两轮自我评审里都没有发现的纯事实错误：我在设计"判定权归属"这类架构哲学问题时想得比较细，却没有去核实一个更基础的事实——代码到底在哪个阶段被提交。v3改为挂载P4，并新增BDD-13专门验证"数据源与挂载阶段对齐"，防止这类问题以后不被测试覆盖到。

2. **B2（BLOCKER，已修复）**：v2声称"登记内容进provenance审计范围"，核实`check-p6-provenance.py`现有七道审计后，确认无一道涉及known-violations登记内容——这句话是我在没有核实的情况下，凭"听起来应该有兜底"的直觉加上的修饰性描述，恰好违反了我自己在v2第5节反复强调的"不要给人已经有保障的错觉"这条原则。v3删除该声称，明确本次不新增第八道provenance审计。

3. **B3（WARNING，已修复，判断为最深的一处）**：v2的"完整复刻P5 known-failures"这个类比本身是错的——known-failures宽容的是"预存的、非本任务造成的问题"，known-violations宽容的是"本任务自己引入的新反模式"，两者登记后被容忍的道德性质相反。如果只复刻"数量对齐"这一层算法而不正视这层语义差异，等于把"引入反模式"变成一个只要肯登记就没有代价的选项，这比没有这个gate还糟。v3改为"登记+数量对齐+P4评审角色approve"三重门槛，把"要不要接受这个反模式"的判断权交还给独立于implementer的现有评审角色，不让"数量对齐"这一个纯算术条件单独构成放行依据。

4. **N1（NIT，已修复）**：本计划文件本身需登记进`docs/design-notes/README.md`的索引（该README已登记`design-maintainability-gate.md`但未登记本落地计划文件）。已登记（2026-08-30），纯执行遗漏，不是设计问题。

5. **N2（NIT，已修复）**：v2未定义known-violations.md的登记模板格式，而`count_kf_entries`函数依赖固定的表格行格式（`| N |`）才能正确计数。v3第4.1节补充模板定义，格式对齐`known-failures-template.md`但语义边界说明反转，且模板本身写明"P4评审确认"列不参与机械计数，避免给人"填了这一列就自动放行"的错觉。

**三轮评审（自我×2 + 独立×1）之后，仍然明确存在、判断为"合理边界不是缺陷"的点**：
- G0本身仍无法保证"判定过程被诚实执行"（implementer/verifier是否真的跑了脚本、是否用`git commit --no-verify`绕过pre-commit hook），这和局限3同源，本任务范围内不解决。
- Fuzzy boundary正则集只覆盖Python/TS，其它语言需项目自行在gate_commands补充。
- 阈值N=1000无实证依据，仅供参考。