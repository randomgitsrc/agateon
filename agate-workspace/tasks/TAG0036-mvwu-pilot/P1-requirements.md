---
phase: P1
task_id: TAG0036
type: problems
parent: P0-brief.md
trace_id: TAG0036-P1-20260919
status: draft
agent: analyst
created: '2026-09-19'
risk_level: medium
phases:
- P1
- P2
- P3
- P4
- P5
- P6
- P7
- P8
packages:
- agate-scripts
- agate-docs
- agate-tests
domains:
- backend
---
# P1 需求基线 — TAG0036 MVWU 阶段 1 试点（RM-AG0063）

[NO_NEED_CONFIRM]

> 权威范围来源：`P0-brief.md`（含「P0 自检记录」）。设计依据：`docs/design-notes/design-mvwu-protocol.md` v2.1。
> 本文件是活基线；后续阶段发现的新隐含需求以 `[SCOPE+ from Pn]` 回写。
> `judge.enabled: true` 已在 `.state.yaml`（RM-AG0039 机制强制），本基线确认，无需另行声明。
> 本版为 retry #1 就地修订（依据 `P1-review.md` F-1…F-9）；BDD 因拆分/合并已**全量重排编号**（共 71 条），处置见文末「修订记录（retry #1）」。

## 0. P0-brief 时效性质疑（analyst 独立复核，非照抄）

立项 2026-09-16 → 启动 2026-09-19，期间 PR #341/#342/#343 合并。逐条对照 P0 卡「漂移判据」：

- 判据 1（`task` 目标方案不再成立）：**不命中**。`check-gate.py::_gate_p2_dispatch_plan` 仍只校验 mode/parallel_limit/batches/id/complexity、不拒未知键（已读源码 `check-gate.py:767-800` 确认）；`agate-md-field-get.py` 的 `JSON_FIELDS = {"dispatch_plan"}`（frontmatter-only、无正文回退）仍成立。`agate/` 内 `tests_filter` / `P4-evidence` / `MVWU` / `check-mvwu` 命中仍为 0。
- 判据 2（`executor_env` 平台前提）：**不命中**。python 3.12.3 / pytest 9.0.3 / 版本管理布局 `~/.agate` 未变；`count-tests.sh` 实测 1668 用例（= CI 口径 1666 passed + 2 skipped）。
- 判据 3（`known_risks` 前提被解决/重叠）：**不命中**。TAG0035 已合并（PR #324/#326，2026-09-16/17），但其文件面与本任务不重叠（见下第 4 条）。

结论：**无严重漂移**，共 4 条轻微漂移，均不阻塞：

[P0_STALE: `_gate_p2_dispatch_plan` 现位于 `check-gate.py:767`（P0-brief 原写 `:743`），调用点 `check-gate.py:919`——行号漂移，语义不变；P0 自检记录已载明，本基线以 :767 为准]

[P0_STALE: worktree 内 `agate-workspace/decisions/` 目录**不存在**（P0-brief 写"空置"）——git 不跟踪空目录，属实况表述差异；同样印证"机制未启用"，⑤-e 结论不变；P0 自检记录已载明]

[P0_STALE: P0-brief ⑤-e 证据 2 称 "`adr.md:278` 的解析优先级已因 `AGATE_HOME` 失实、静默漂移"——该行已被 commit `28293d8`（DEBT0042 独立评审修正，2026-09-19 06:25）同步，现文已含 `AGATE_HOME`。缺口本身（`adr.md` 无"前提被证伪 → 复审"的触发条件）仍成立，且该漂移恰是被 DEBT0042 评审"顺手"发现而非被机制发现，反而佐证需要触发条件。影响：⑤-e 的第 2 条证据措辞过期（第 1 条 `decisions/` 无人写仍成立）。P1 已据此收窄：BDD 不依赖"adr.md:278 仍失实"]

上一条的处置：P0-brief 该处本阶段未改（analyst 不改 P0）；**主 Agent 已补记进 P0-brief「P0 自检记录」**（P0-brief 含 "P0_STALE 补记" 条目 (d)）。

[P0_STALE: P0-brief 头部称"TAG0035 先启动、本任务与之可并行"——TAG0035 已合并并归档（active-tasks 已完成表、`agate-workspace/tasks/TAG0035-gate-robustness/` 已 P8/READY）。无重叠风险（TAG0035 未改 `_gate_p2_dispatch_plan` 语义，仅致行号 743→767）。连带影响：P0-brief scope ① 的"同类 fail-open（`_gate_p2_dispatch_plan` 解析失败/缺字段 `return None` 静默放行）——若 TAG0035 未覆盖，另立 DEBT"，其条件已触发：`grep -n "_gate_p2_dispatch_plan\|dispatch_plan" agate-workspace/debt/tech-debt.md` 无 fail-open 登记条目、TAG0035 P1 亦未覆盖 → 本基线把"登记该 DEBT（只登记不修）"落为 BDD-5]

上一条的处置：P0-brief 头部表述本阶段未改（analyst 不改 P0）；**主 Agent 已补记进 P0-brief「P0 自检记录」**（同条目 (c)）。

另记一处**非漂移的同类扫描发现**（见 §4.4）：协议已有 `project_phase: bootstrap` → `P2-skeleton.md`「骨架声明」机制（目录布局声明），与 ⑤-d「Walking Skeleton」**同词不同义**，P0-brief ⑤-d 表中"❌ 无对应"对**概念**成立、对**术语**有撞名风险，⑤-d 成文须消歧（BDD-62）。

## 1. 需求复述

在 agate 协议层落地 MVWU 阶段 1（**只观测、不阻断、零协议内核改动**），并并入 ⑤ 组 7 个方法学概念的成文：

| 编号 | 交付物 | 一句话 |
|------|--------|--------|
| ① | `batches[].tests_filter` | `P2-design.md` frontmatter `dispatch_plan.batches[]` 的**可选**键，缺省时既有 P2 gate 行为不变 |
| ② | `P4-evidence/{batch}.log` | 批级证据落点新约定（新目录，含最小内容格式，`{batch}` = 批 `id`） |
| ③ | `agate/scripts/check-mvwu.py` | 新建独立脚本：六项检查 + 四态 verdict（PASS/FAIL/EXPECTED_RED/UNKNOWN）+ `--observe` 模式（补齐耗时 / commit 形态 / boundary 三列）；**不挂 gate、不改 `.state.yaml`、不阻断** |
| ④ | 字段落地路径 | `phase-cards/P2-design.md` + `assets/execution-roles/architect.md` 写明 `tests_filter` 写法与选择方法（否则无人写该字段） |
| ⑤-a | 术语补录 | `agate/CONTEXT.md` 补 5 个术语（MVWU / tests_filter / P4-evidence / 四态 verdict / boundary(I1)），沿用三列，不动既有行 |
| ⑤-b | Deep Modules 审查锚点 | `role-system.md` 补一节（判据 = 角色文件是否规定执行顺序而浅化接口） |
| ⑤-c | 批切分三判据 | Tracer Bullet / Vertical Slice / Architecture Fitness Functions 落 `architect.md` + `P2-design.md` 卡片 |
| ⑤-d | Walking Skeleton | 仅成文"拒绝部署/CI（ADR-003 技术栈中立）+ 吸收'骨架先跑通'并入 ⑤-c 判据一"，无独立交付物 |
| ⑤-e | 决策复审机制 | `adr.md` 补复审触发条件（过时不删）+ 项目侧 `{AGATE_WORKSPACE}/decisions/` 落点与 P2 读取 |

**完成判据边界**：交付"工具 + 采集能力 + 字段落地路径 + ⑤ 成文"，**不含**"Q1/Q3 已答"（需自然样本）；Q2=13%（任务级 2/16）为引用结论，无需试点。**⑤-b/⑤-d 只要求成文到位，不宣称机制已生效。**

## 2. 隐含需求识别

逐维度过（数据 / 前端 / 多端 / 边界 / 兼容 / 同类），每条说明"为什么必须"：

1. **写入方文档（②）**：`P4-evidence/{batch}.log` 由 P4 阶段主 Agent 在批 commit 前写入。若只在 `check-mvwu.py` 侧定义格式而无写入方说明，重演"字段无人写 → 样本永不到来"（与 ④ 同构）。故**必须**在 P4 阶段卡（`phase-cards/P4-implementation.md`）写明落点/格式/不阻断语义。P0-brief ② 只写"新目录约定"、未指定落文档处，此为**隐含需求**。
2. **EXPECTED_RED 需要"失败清单"才可判定**：设计文档 §5.1.1 定义 EXPECTED_RED = "非零退出，但**全部命中** `expected_red`"。P0-brief ② 最小内容只有 `command/exit_code/git_head/timestamp/expected_red`（+ `duration_seconds`），**无失败测试名**——仅凭 `exit_code≠0` 与 `expected_red` 无法判定"全部命中"。→ 已采纳 SUGGEST-1（§5）。且判定依赖**列表编码与元素相等口径**（见 §3 口径 C；pytest 参数化 id 含逗号与方括号，必须引号包裹、精确相等）。
3. **`{batch}` filename-safe**：`{batch}` 直接拼进 `P4-evidence/{batch}.log`，`id` 是自由字符串，含 `../` 或路径分隔符即路径穿越 → 必须约束为 `[A-Za-z0-9._-]+`，且 check 侧对不安全 id **fail-closed 为 UNKNOWN**（设计文档 UNKNOWN 触发集含"路径不安全"）。不安全 id 与含 `|`、换行的 `tests_filter` 在输出中的**打印形态**须有确定规则（§3 口径 D），否则契约行/观察表行不可机读、不可粘贴。
4. **YAML 引号**：`dispatch_plan` 约定为 frontmatter "单行 flow YAML"；`tests_filter` 值含空格/`:`/`,` 时，flow 风格不加引号会解析错位甚至整块解析失败。⑤/④ 的写法说明必须要求**双引号包裹**，并有一条 BDD 走"写 → `agate-md-field-get.py` 读"的真实链路。
5. **verdict 与 boundary 解耦（**对设计文档 §5.1.1 的有意偏离**，见 §5 SUGGEST-2）**：P0-brief 六项检查"且仅此六项"**不含** boundary，`--observe` 表的 verdict 列来源写作"六项检查结果"。但设计文档有两处与此不一致，如实列出、不称"读法不同"：
   - **(a) §5.1.1「MVWU verdict 四态定义」表**（该节自称"本节为权威定义，§7.2 的 check 实现据此"）在 `UNKNOWN` 触发条件里**明文列有"边界不可归属"**，与"boundary 不参与 verdict"**字面相反**；
   - **(b) §7.3 试点观察表示例 C 行**（合并 commit、boundary "不可归属"）的 verdict 写为 **UNKNOWN**。
   本基线选择解耦，理由：若 boundary 参与 verdict，则 87%（14/16）合并 commit 任务的 verdict 几乎全 UNKNOWN，**Q1（`tests_filter` 是否稳定可执行）被 Q2（边界可比对性）污染**，二者无法分别度量；且默认模式与 `--observe` 会对同一批给出不同 verdict。**此为对设计文档 §5.1.1 的有意偏离，限定为「阶段 1 观测口径」**：verdict 是否纳入 boundary，**由阶段 2 与提交粒度决策（P0-brief 决策 A/B，用户裁决项）一并复议**；BDD-42 只固化阶段 1 口径，**不预裁**阶段 2 门槛。
6. **`output` 键的写入方（`--observe` boundary/commit 形态的来源）**：P0-brief ③ 表 boundary 列来源 = "声明 `output`（如有）"，commit 形态来源 = "batch 产出文件的 git log"。**`output` 是设计文档 §4.2 已预算的 MVWU 可选字段，但 P0-brief scope ① 只交付 `tests_filter`，未规定任何文档告诉 architect 何时/如何写 `output`**——不写则自然样本的 commit 形态/boundary 恒为 UNKNOWN，Q2/Q3 采集退化。→ 已采纳 SUGGEST-3（§5）。
7. **`check-mvwu.py` 不得执行 `tests_filter`**：check 的"command 可执行"是静态可解析性判断，否则检查本身会产生副作用、依赖环境、不可平台无关单测（设计文档 UNKNOWN 触发集里的"超时"指**写证据的那次运行**，非 check）。
8. **CHECK 10 排序约束**：`check-protocol-consistency.py` CHECK 10 对协议文档面（含 `CONTEXT.md`、`scripts/README.md`、phase-cards、roles）里出现的 `check-*.py` 字样对照 `agate/scripts/` 实际文件，**不存在即 ERROR**。→ `check-mvwu.py` 必须与首个引用它的文档**同一 commit 或更早**落库（P2/P4 排批时须体现）。
9. **不回填 / 不造样本 / 不改历史任务产物**：P0-brief 已排除；写成负向 BDD 以便机械判定（BDD-68）。
10. **多端**：无 MCP/API/前端面；仅 CLI 脚本 + 协议文档。**兼容**：`tests_filter` 可选键，老任务无需回填；`check-mvwu.py` 对**所有现存任务目录**（均无 `tests_filter`/`P4-evidence`）须给出诚实的 UNKNOWN 行而非崩溃（BDD-39/56）。**数据/前端**：无迁移、无 UI。
11. **计数文档同步**：新增测试文件使 `count-tests.sh` 总数漂移，须同步 `agate/tests/README.md`（BDD-69）。
12. **观测范围（git 查找范围）必须有界**（review F-3）：commit 形态/boundary 若取全仓历史，真实仓库中几乎所有 `output` 文件都有多个历史 commit，"分散于多个 commit"恒成立，`--observe` 采集失去意义。故观测限定于任务分支相对默认分支的提交区间（§3 口径 E），且基线不可确定时诚实 UNKNOWN。已知局限：任务合并回默认分支后，对其再跑 `--observe` 因区间为空 commit 形态/boundary 恒 UNKNOWN——阶段 1 观测发生在**任务分支上**，回顾性采集不在范围。
13. **多故障并存与自相矛盾证据的确定性**（review F-6）：单批可同时命中多个故障；无固定判定顺序则同一输入可得不同 reason。故 reason 优先级须显式（§3 口径 B）并有 BDD 固化（BDD-34）；`id` 重复/非字符串、`exit_code: 0` 而 `failed_tests` 非空、`git_head` 格式，均须各有确定处置（§3 口径 B/G，BDD-24/32/33 等）。
14. **已知观测局限须显式声明而非隐含**（review F-9）：检查 2 只静态判断"命令首词可解析"，**不比对 `command` 与 P2 声明的 `tests_filter` 是否一致**（"且仅此六项"，不新增检查）；复合命令只判首词。以负向 BDD 固化，避免下游误以为已核对（BDD-16/17/18）。

## 3. BDD 验收条件

> 约定：编号全局唯一、顺序（`#### BDD-NN:`，1…71 连续）；每条一个 Given/When/Then；Then 均可二值判定。"内核基线"= `git merge-base HEAD main`。

### 口径定义（`check-mvwu.py` 的外部可观测契约；BDD 引用之，P2 据此设计）

**A. 契约行**：默认模式**每批一行** `MVWU_RESULT: <VERDICT> batch=<id>`，未 PASS 的行在末尾追加 ` reason=<token>`；`<VERDICT>` ∈ {`PASS`,`FAIL`,`EXPECTED_RED`,`UNKNOWN`}；`reason` 词表 = {`tests_filter`,`command`,`evidence`,`exit_code`,`git_head`,`expected_red`}（前 5 个对应检查 1-5，`expected_red` 对应检查 6 内部"无法判定是否全部命中/列表不可解析"）。无可判定批时输出一行 `MVWU_RESULT: UNKNOWN batch=- reason=tests_filter`。

**B. 多故障并存的 reason 判定顺序**（取**首个**命中者）：`tests_filter` → `evidence` → `command` → `exit_code` → `git_head` → `expected_red`。各 reason 的覆盖面：
- `tests_filter`：该批缺 `tests_filter` 键，或值为空串/非字符串。
- `evidence`：`P4-evidence/<id>.log` 不存在；**批 id 不安全**（不匹配 `[A-Za-z0-9._-]+`，含非字符串/空）；**批 id 重复**（同一 `id` 出现在多个批，证据无法唯一归属——该 id 的**所有**批均判此 reason）；证据文件损坏（存在但为空、含非 UTF-8 字节、或无任何可解析的 `key: value` 行）。
- `command`：证据缺 `command` 键，或其首词不可解析（口径 F）。
- `exit_code`：证据缺 `exit_code` 键或其值非整数；或**自相矛盾**（`exit_code: 0` 而 `failed_tests` 非空——证据自洽性无法保证，fail-closed）。
- `git_head`：证据缺 `git_head` 键，或其值不满足口径 G，或任务目录不在 git 仓库内。
- `expected_red`：见口径 C。

**C. `expected_red` / `failed_tests` 的列表编码与元素相等口径**：证据日志内二者的值均为**单行 YAML flow 序列，元素为双引号包裹的 pytest node id 字符串**（例 `["tests/a/test_x.py::test_x[a,b-1]", "tests/a/test_y.py::test_y"]`；元素内的 `"` 与 `\` 按 YAML 双引号规则转义；空列表写 `[]`；键缺省视同 `[]`）。理由：参数化 id 含逗号/方括号，不加引号的 flow 序列会错位。**元素相等 = node id 精确字符串相等**（逐字节，不做前缀、函数名、大小写归一）。"不可解析" = 值不是合法 flow 序列，或含非字符串元素。verdict 判定（检查 1-5 通过后）：
- 二者中任一不可解析（无论 `exit_code`）→ `UNKNOWN reason=expected_red`；
- `exit_code: 0` → `PASS`；
- `exit_code≠0`：`expected_red` 为空 → `FAIL`；`expected_red` 非空但 `failed_tests` 为空 → `UNKNOWN reason=expected_red`；`failed_tests` 非空且每个元素都在 `expected_red` 中 → `EXPECTED_RED`；否则 → `FAIL`。

**D. 输出转义规则**（保证每批**恰一行**、契约行可按空白分词、观察表行可直接粘贴进 markdown 表）：
- **批 id**（契约行 `batch=` 与观察表第 1 列）：合规 id 原样输出；id 中**每个不属于 `[A-Za-z0-9._-]` 的字节**（按 UTF-8 字节）替换为 `\xNN`（小写十六进制；`\` 本身为 `\x5c`）；非字符串/空 id 输出单字符 `?`。理由：id 是标识符，可逆编码且不含空白/管道，契约行分词不受影响。
- **`tests_filter`**（观察表第 2 列，自由文本）：按 GFM 表格转义——`\`→`\\`、`|`→`\|`、`` ` ``→`` \` ``、换行→字面 `\n`、回车→字面 `\r`、其他 C0 控制字符→`\xNN`；空格等其余字符原样；缺键/空串/非字符串输出 `-`。理由：保持可读，且管道在 markdown 表内的标准写法即 `\|`。
- 观察表行按 GFM 规则切分（`\` 转义下一字符）后**恰 7 列**。

**E. 观测范围（commit 形态/boundary 的 git 查找范围）**：仅取提交区间 `git merge-base HEAD <默认分支>..HEAD`。`<默认分支>` = `origin/HEAD` 所指分支；无 `origin/HEAD` 则依次取本地 `main`、`master`。**基线无法确定**（三者皆无 / merge-base 无结果）或**区间为空**时，该批 commit 形态与 boundary 均为 `UNKNOWN`，stderr 输出含 `baseline` 字样的诊断（原因），stdout 与 verdict 不受影响。区间外的历史提交对 commit 形态/boundary **不可见**。

**F. 检查 2 的"首词"语义**：按 shell 词法切分 `command`；**跳过**前导 `NAME=value` 形态的环境变量赋值词；其后第一个词为"首词"，须在 PATH 上可解析（或为存在且可执行的路径）。首词为 shell 内建 `cd`/`export`/`set`/`source`/`.` 时视为可解析，**其后的命令不再检查**（含 `&&`/`||`/`;`/`|` 复合命令一律只判首词）。切分失败（如引号不闭合）或无首词 → `reason=command`。**已知观测局限**：不比对 `command` 与 `tests_filter` 是否一致。

**G. `git_head` 合法格式**：全长对象名——40 位（或 sha256 仓库的 64 位）十六进制，大小写不敏感——且解析为仓库中**存在的 commit**。短 sha、分支/标签名、`HEAD` 等一律不合法（无法复现地钉住确切提交）。

**H. 观察表字段**：`--observe` 每批一行 7 列 markdown 表格行：`| <MVWU> | <tests_filter> | <耗时> | <evidence> | <commit 形态> | <boundary> | <verdict> |`（无表头、无其他 stdout；诊断走 stderr）；无可判定批时输出一行，第 1 列为 `-`。

### ① `batches[].tests_filter`

#### BDD-1: tests_filter 写入 frontmatter 后可被结构化读取
- Given `P2-design.md` frontmatter 含单行 flow 风格 `dispatch_plan: {mode: static-batch, batches: [{id: auth-token-parser, complexity: medium, tests_filter: "python -m pytest tests/auth/test_token.py -q"}]}`（值含空格，双引号包裹）
- When 执行 `FILE=<该文件> python3 agate/scripts/agate-md-field-get.py dispatch_plan`
- Then 输出为合法 JSON，且 `batches[0].tests_filter` 字符串与写入值逐字节相同

#### BDD-2: 含 tests_filter 的合法 dispatch_plan 不被 P2 gate 拒绝
- Given 一份其余内容合规、`dispatch_plan` 合法且每批含 `tests_filter` 的 `P2-design.md`
- When 调用 `check-gate.py` 的 P2 dispatch_plan 校验（`_gate_p2_dispatch_plan`，或整体 `check-gate.py P2`）
- Then 该校验返回"通过"（`None`/不产生 dispatch_plan 相关 ERROR），且与"同文件删去全部 `tests_filter` 键"的结果相同

#### BDD-3: 缺省 tests_filter 时既有 P2 gate 行为不变（回归）
- Given 本任务全部改动完成，既有测试 `agate/tests/unit/test_dispatch_orchestration.py`、`agate/tests/unit/test_check_gate.py`、`agate/tests/unit/test_agate_md_field_get.py` 的用例**未被删除或放宽断言**
- When 运行这三个文件
- Then 全部通过（0 failed），且 `git diff <内核基线> -- agate/scripts/check-gate.py` 为空

#### BDD-4: 批内含 tests_filter 与不含的批可混用
- Given `dispatch_plan.batches` 含两批：批 A 有 `tests_filter`、批 B 无该键
- When 运行 `check-gate.py` P2 dispatch_plan 校验，且运行 `check-mvwu.py <task_dir>`
- Then 校验通过；`check-mvwu.py` 对批 B 输出 `MVWU_RESULT: UNKNOWN batch=<B> reason=tests_filter`，对批 A 的输出不受批 B 影响（可选键逐批独立）

#### BDD-5: `_gate_p2_dispatch_plan` 的同类 fail-open 已登记为 DEBT（只登记不修）
- Given `agate-workspace/debt/tech-debt.md` 在本任务前无 `_gate_p2_dispatch_plan` 解析失败/缺字段静默放行的条目
- When 本任务完成后检查该文件，并运行 `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md`
- Then 文件新增至少一条同时含 `_gate_p2_dispatch_plan` 与"静默放行"（或 `return None`）字样的 DEBT 条目、`check-debt.py` exit 0，且 `git diff <内核基线> -- agate/scripts/check-gate.py` 为空

### ④ 字段落地路径（P2 卡片 + architect 角色）

#### BDD-6: P2 卡片写明 tests_filter 的写法与约束
- Given 本任务完成
- When 读取 `agate/phase-cards/P2-design.md` 的「dispatch_plan 机器字段」节
- Then 该节同时包含以下要点（**每个要点至少含其字面标记**，标记用反引号/引号括出）：`tests_filter` 为 `batches[]` 的**可选**键（字面：`tests_filter`、`可选`）；写在 frontmatter 且值须**双引号包裹**（字面：`双引号`）；只覆盖**该批交付面**、**禁止全量套件**（字面：`禁止全量`）；`expected_red` 声明位置为 `P4-evidence/{batch}.log`（字面：`expected_red`、`P4-evidence/{batch}.log`）；`{batch}` 即批 `id`，须匹配 `[A-Za-z0-9._-]+`（字面：`[A-Za-z0-9._-]+`）；缺省时 gate 行为不变（字面：`缺省`）；示例使用 `python -m pytest` 形态（字面：`python -m pytest`）

#### BDD-7: architect 角色文件写明如何为每批选择 tests_filter
- Given 本任务完成
- When 读取 `agate/assets/execution-roles/architect.md` 的「批次设计」节
- Then 该节包含（字面标记）：如何为一批选取 `tests_filter`（只含该批交付面测试、不含后续批测试、不得全量；字面：`禁止全量`）；与 P3 的分工（`gate_commands.P3` = 任务级红灯基线，`tests_filter` = 批级交付面绿灯确认，互不替代；字面：`gate_commands.P3`、`红灯基线`、`绿灯确认`）；该批确有设计上应红的测试时须留待写入 `expected_red`（字面：`expected_red`）；且该节既有「硬规则」四条**逐字未变**（diff 无对其的删除/修改行）

#### BDD-8: 协议文档中的 tests_filter 示例值不含裸 python3
- Given 本任务完成
- When 在 `agate/` 下（排除 `agate/tests/`）执行 `grep -rInE 'tests_filter: *"[^"]*\bpython3\b'`（即限定为位于 `tests_filter` 示例值**内部**的 `python3`；同行别处出现的 `python3 agate/scripts/check-mvwu.py` 等脚本调用不计）
- Then 命中 0 行；且 P2 卡片与 architect.md 均含字样"`AGATE_PYTHON`"或"DEBT0014"或"不裸 python3"之一，说明平台中立约束（Windows 无 `make` 应写 `python -m pytest`）

#### BDD-9: output 可选键的写入说明（SUGGEST-3 已采纳）
- Given 本任务完成
- When 读取 P2 卡片「dispatch_plan 机器字段」节与 architect.md「批次设计」节
- Then 二者均说明（字面标记）：`output`（该批预期改动的文件路径列表）为**可选**键（字面：`output`、`可选`），**仅供** `check-mvwu.py --observe` 的 boundary/commit 形态比对读取（字面：`--observe`），**不**新增任何 gate 校验（字面：`不新增 gate 校验`）；且 `agate/scripts/agate-frontmatter-check.py` 与 `agate/scripts/check-structure-consistency.py` 两个脚本相对内核基线的 `git diff` **均为空**（`output` 嵌套在 `dispatch_plan` 内，无需触碰 `check-structure-consistency.py` 中的 `_TASK_FRONTMATTER_FIELDS` 顶层白名单）

### ② `P4-evidence/{batch}.log` 证据落点

#### BDD-10: P4 阶段卡写明证据落点与最小内容格式
- Given 本任务完成
- When 读取 `agate/phase-cards/P4-implementation.md`
- Then 含一节说明（字面标记）：路径 `P4-evidence/{batch}.log`（位于任务目录）；文件为逐行 `key: value` 且含键 `command`、`exit_code`、`git_head`（须为全长 commit 对象名，口径 G）、`timestamp`、`expected_red`（默认 `[]`）、`duration_seconds`，及可选 `failed_tests`（默认 `[]`；SUGGEST-1 已采纳）；`expected_red`/`failed_tests` 的值为**单行 flow 序列、元素为双引号包裹的 pytest node id**（字面：`node id`、`双引号`，口径 C）；由主 Agent 在该批 commit 前运行 `tests_filter` 后写入；**记录不阻断**（字面：`不阻断`；非零退出仍可 commit）；`{batch}` 须 filename-safe（字面：`filename-safe`）；该目录不进 judge 白名单

#### BDD-11: task-files 模板登记新落点并补 tests_filter 示例
- Given 本任务完成
- When 读取 `agate/assets/templates/task-files.md`
- Then 阶段产出表含 P4 行登记 `P4-evidence/{batch}.log`，且 `dispatch_plan` 示例注释含 `tests_filter` 为可选键的说明

#### BDD-12: 证据落点不改任何 gate/hook/审计/judge 登记面
- Given 本任务完成
- When 对以下文件做 `git diff <内核基线> -- <paths>`：`agate/scripts/pre-commit-gate.py`、`agate/scripts/agate-archive-stale-outputs.py`、`agate/scripts/check-p6-provenance.py`、`agate/scripts/check-judge-verdict.py`、`agate/assets/review-roles/judge.md`
- Then 全部为空；且 `dispatch-protocol.md`「白名单输入」「黑名单禁注入」两段无 diff；且 `grep -rn "P4-evidence" agate/rules/` 命中 0

### ③ `check-mvwu.py`（六项检查、四态 verdict、不阻断）

#### BDD-13: 基本调用与只读输出契约
- Given 一个含合法 `P2-design.md`（两批 A、B，均含 `tests_filter`）与两份合法证据的临时任务目录（`tmp_path` 内 git 仓库）
- When 执行 `<PY> agate/scripts/check-mvwu.py <task_dir>`（`<PY>` 为测试探测到的解释器）
- Then stdout 恰有两行契约行（口径 A），顺序与 `batches` 声明顺序一致，`batch=` 依次为 A、B；每行 VERDICT 属四态之一

#### BDD-14: 检查 1（tests_filter 存在）——缺失判 UNKNOWN
- Given 某批无 `tests_filter` 键（或值为空串/非字符串）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: UNKNOWN batch=<id> reason=tests_filter`

#### BDD-15: 检查 2（command 可执行）——首词不可解析或缺失判 UNKNOWN
- Given 某批证据 `command:` 的首词在 PATH 上不可解析（如 `no-such-runner-xyz tests/`），或证据缺 `command` 键，其余各项合法
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `UNKNOWN ... reason=command`

#### BDD-16: 检查 2 首词语义——前导环境变量赋值被跳过
- Given 两批，证据其余各项合法：批 A 的 `command:` 为 `FOO=1 <可解析解释器> -m pytest tests/a`；批 B 的 `command:` 为 `FOO=1 no-such-runner-xyz tests/b`
- When 运行 `check-mvwu.py <task_dir>`
- Then 批 A 不因 `FOO=1` 判 `reason=command`（按其余检查得 `PASS`）；批 B 判 `UNKNOWN ... reason=command`（首词取 `FOO=1` 之后的 `no-such-runner-xyz`）

#### BDD-17: 检查 2 首词语义——复合命令只判首词（已知观测局限）
- Given 某批证据其余各项合法，`command:` 为 `cd sub && no-such-runner-xyz tests/`
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批**不**判 `reason=command`（首词 `cd` 为内建、视为可解析，其后命令不检查），verdict 按其余检查得出；`check-mvwu.py --help` 或模块 docstring 含"仅检查首词"（或等义中英文）的已知局限声明

#### BDD-18: 不比对 command 与 tests_filter（已知观测局限）
- Given 某批 P2 声明 `tests_filter: "python -m pytest tests/a -q"`，而证据 `command:` 为另一条合法且首词可解析的命令（如 `<可解析解释器> -m pytest tests/other -q`），其余各项合法且 `exit_code: 0`
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: PASS`（二者不一致不改变 verdict）；`--help` 或模块 docstring 含"不比对 command 与 tests_filter"（或等义表述）的已知局限声明

#### BDD-19: check-mvwu.py 绝不执行 command / tests_filter
- Given 某批证据 `command:` 为一条可解析、且**若被执行会创建哨兵文件**的命令（哨兵路径位于 `tmp_path`）
- When 运行 `check-mvwu.py <task_dir>` 与 `check-mvwu.py --observe <task_dir>`
- Then 哨兵文件不存在（脚本从不 spawn `command`/`tests_filter`）

#### BDD-20: 检查 3（evidence 存在）——缺失判 UNKNOWN
- Given 某批有 `tests_filter` 但 `P4-evidence/<id>.log` 不存在
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `UNKNOWN ... reason=evidence`

#### BDD-21: 不安全的批 id 判 UNKNOWN 且不读取 P4-evidence/ 之外的文件
- Given 某批 `id` 含不合规字符（如 `../escape`、含空格、含 `/` 或 `\`），且 `P4-evidence/` 之外的位置存在一个内容合法的同名候选证据文件
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `UNKNOWN ... reason=evidence`，且输出中不含该外部候选文件的任何字段值（未被读取）

#### BDD-22: 不安全批 id 的打印形态可机读（口径 D）
- Given 五个批，均含 `tests_filter`：`id` 分别为 `a b`（含空格）、`x|y`（含管道）、`../e`、`ok-1.2_3`（合规且证据合法）、空串 `""`
- When 运行 `check-mvwu.py <task_dir>`
- Then stdout 恰五行、按声明顺序；按空白切分每行恰得 `MVWU_RESULT:`、VERDICT、`batch=…`（及可选 `reason=…`）各一词；前三行依次为 `... batch=a\x20b reason=evidence`、`... batch=x\x7cy reason=evidence`、`... batch=..\x2fe reason=evidence`，第四行 `batch=ok-1.2_3` 原样（`PASS`）；第五行（空串 id）为 `UNKNOWN batch=? reason=evidence`（非字符串 id 同样打印 `batch=?`）

#### BDD-23: 检查 4（exit_code 可解析）——缺失或非整数判 UNKNOWN
- Given 某批证据缺 `exit_code` 键，或其值不是整数（如 `exit_code: ok`）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `UNKNOWN ... reason=exit_code`

#### BDD-24: 检查 5（git HEAD 可关联）——格式非法或无法关联判 UNKNOWN，即使测试全绿
- Given 某批证据 `exit_code: 0`，但 `git_head` 属下列之一：仓库中不存在的 40 位十六进制 sha、短 sha（如前 7 位）、分支名/`HEAD`、缺该键，或任务目录不在 git 仓库内（合法格式见口径 G：全长十六进制且为存在的 commit）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `UNKNOWN ... reason=git_head`（不是 PASS）

#### BDD-25: verdict = PASS
- Given 某批检查 1-5 全部通过且证据 `exit_code: 0`
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: PASS batch=<id>`（无 reason）

#### BDD-26: verdict = FAIL（无预期红灯却非零退出）
- Given 某批检查 1-5 通过、证据 `exit_code: 1` 且 `expected_red: []`
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: FAIL batch=<id>`

#### BDD-27: verdict = FAIL（存在预期外红灯）
- Given 某批检查 1-5 通过、`exit_code: 1`、`expected_red: ["t/a.py::t_a"]`、`failed_tests: ["t/a.py::t_a", "t/a.py::t_b"]`（`t_b` 不在预期清单）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: FAIL batch=<id>`

#### BDD-28: verdict = EXPECTED_RED
- Given 某批检查 1-5 通过、`exit_code: 1`、`expected_red: ["t/a.py::t_a", "t/a.py::t_b"]`、`failed_tests: ["t/a.py::t_a"]`（非空且为 `expected_red` 子集）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: EXPECTED_RED batch=<id>`

#### BDD-29: 非零退出且预期红灯无法核对时判 UNKNOWN，不得猜 EXPECTED_RED
- Given 某批检查 1-5 通过、`exit_code: 1`、`expected_red` 非空，但证据缺 `failed_tests`（或为空 `[]`）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: UNKNOWN batch=<id> reason=expected_red`

#### BDD-30: 含逗号与方括号的参数化 node id 在引号包裹的列表中被正确解析
- Given 某批检查 1-5 通过、`exit_code: 1`、`expected_red: ["tests/a/test_x.py::test_x[a,b-1]", "tests/a/test_y.py::test_y"]`、`failed_tests: ["tests/a/test_x.py::test_x[a,b-1]"]`
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: EXPECTED_RED batch=<id>`（列表按 2 个元素与 1 个元素解析，未被参数化 id 内的逗号切碎）

#### BDD-31: 元素相等为 node id 精确字符串相等（近似 id 不算命中）
- Given 某批检查 1-5 通过、`exit_code: 1`、`expected_red: ["tests/a/test_x.py::test_x[a,b-1]"]`、`failed_tests: ["tests/a/test_x.py::test_x[a,b-2]"]`（仅参数化后缀不同）
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: FAIL batch=<id>`（不按前缀/函数名归并为命中）

#### BDD-32: expected_red / failed_tests 不可解析判 UNKNOWN
- Given 某批检查 1-5 通过，且 `expected_red` 或 `failed_tests` 的值不是合法 flow 序列（如 `expected_red: t_a`、`expected_red: [t_a, `）或含非字符串元素（如 `expected_red: [1, 2]`），`exit_code` 取 0 或 1 均可
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `MVWU_RESULT: UNKNOWN batch=<id> reason=expected_red`

#### BDD-33: exit_code 与 failed_tests 自相矛盾判 UNKNOWN
- Given 某批证据 `exit_code: 0` 但 `failed_tests: ["t/a.py::t_a"]`（非空），其余检查 1-5 合法
- When 运行 `check-mvwu.py <task_dir>`
- Then 该批契约行为 `UNKNOWN ... reason=exit_code`（不是 PASS）

#### BDD-34: 多故障并存时 reason 按固定顺序取首个
- Given 六个批：批 P 无 `tests_filter` 且无证据；批 Q 有 `tests_filter`、证据的 `command` 首词不可解析且 `exit_code` 非整数；批 R 有 `tests_filter`、证据的 `exit_code` 非整数且 `git_head` 非法；批 S 有 `tests_filter`、证据的 `git_head` 非法且 `expected_red` 不可解析；批 T、U 共用同一 `id`、均有 `tests_filter` 与各自合法的证据
- When 运行 `check-mvwu.py <task_dir>`
- Then 六行 reason 依次为 `tests_filter`、`command`、`exit_code`、`git_head`、`evidence`、`evidence`（判定顺序 tests_filter → evidence → command → exit_code → git_head → expected_red，取首个命中；重复 id 的所有批均判 `evidence`）

#### BDD-35: UNKNOWN 不等价于 PASS，不得作为放行依据
- Given 覆盖 BDD-14/15/20/21/23/24/29 的全部 UNKNOWN 场景各一批
- When 运行 `check-mvwu.py <task_dir>`，逐行取契约行
- Then 所有这些行的 VERDICT 为 `UNKNOWN` 且行内不含独立词 `PASS`；脚本模块 docstring/`--help` 输出含"UNKNOWN 不等价于 PASS，不得作为放行依据"（或等义中文/英文表述）

#### BDD-36: exit code 约定——任一 verdict 均 exit 0
- Given 四态 verdict 各至少一个场景（含 FAIL、UNKNOWN、EXPECTED_RED）
- When 分别运行 `check-mvwu.py <task_dir>`
- Then 四态场景 **exit code 均为 0**（verdict 只经 stdout 契约行表达，理由：本脚本是观测器、不在任何 gate/hook 链上，且 0 是"永不令 commit/gate 失败"的最强保证；与 `check-retrospective.py` "0=总是通过"同一先例）；任何情形均无 Python traceback

#### BDD-37: exit code 约定——仅用法/目标错误非零（exit 2）
- Given 无参数调用，或目标目录不存在
- When 运行 `check-mvwu.py`（无参数）与 `check-mvwu.py <不存在的目录>`（含 `--observe` 变体）
- Then 二者均 **exit 2**，stderr 含用法/目标不存在说明，stdout 无契约行；无 Python traceback（与 `check-platform-assumptions.py`"2=目标不存在"同一先例）

#### BDD-38: 不阻断、不写状态（只读）
- Given 一个真实布局的任务目录（含 `.state.yaml`、`gate-events.jsonl`）位于 `tmp_path` 的 git 仓库内
- When 运行 `check-mvwu.py <task_dir>` 与 `--observe`（任一 verdict）
- Then 运行前后 `.state.yaml`、`gate-events.jsonl` 字节不变，`git status --porcelain` 与 git index 不变，任务目录内无新增/修改文件

#### BDD-39: 无可判定批的输入给出诚实 UNKNOWN 行且不崩溃
- Given 四种输入之一：`P2-design.md` 缺失；frontmatter 为坏 YAML；`P2-design.md` 无 `dispatch_plan`；`dispatch_plan` 为 `mode: single` 且无 `batches`
- When 运行 `check-mvwu.py <task_dir>`
- Then exit 0、无 traceback，stdout 恰一行 `MVWU_RESULT: UNKNOWN batch=- reason=tests_filter`

#### BDD-40: 损坏的证据文件判 UNKNOWN 且不崩溃
- Given 某批证据文件存在但为空文件、或含非 UTF-8 字节、或无任何可解析的 `key: value` 行
- When 运行 `check-mvwu.py <task_dir>`
- Then exit 0、无 traceback，该批契约行为 `UNKNOWN ... reason=evidence`；其他批不受影响

#### BDD-41: 多批独立判定，互不污染
- Given 三批：A 证据 `exit_code: 0`、B 证据 `exit_code: 1` 且 `expected_red: []`、C 无证据
- When 运行 `check-mvwu.py <task_dir>`
- Then 依声明顺序输出 A=`PASS`、B=`FAIL`、C=`UNKNOWN reason=evidence`；B 的 FAIL 不改变 A 的 PASS

#### BDD-42: boundary/commit 形态不影响 verdict（SUGGEST-2 已采纳；阶段 1 观测口径，对设计文档 §5.1.1 的有意偏离，阶段 2 复议）
- Given 某批检查 1-5 通过且 `exit_code: 0`，该批的产出与其他批共享同一 commit（合并形态）
- When 分别运行 `check-mvwu.py <task_dir>` 与 `check-mvwu.py --observe <task_dir>`
- Then 两种模式下该批 verdict 均为 `PASS`，且 `--observe` 行 boundary 列为 `UNKNOWN`（verdict 只由检查 1-6 决定，boundary 不参与）

### ③ `--observe` 模式

#### BDD-43: --observe 输出的列结构（7 列 markdown 表格行，每批一行）
- Given 含两批的合法任务目录
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then exit 0；stdout 恰两行，每行形如 `| <MVWU> | <tests_filter> | <耗时> | <evidence> | <commit 形态> | <boundary> | <verdict> |`，按 GFM 表格规则（`\` 转义下一字符）切分**恰 7 列**，列序固定为 MVWU / tests_filter / 耗时 / evidence / commit 形态 / boundary / verdict；无表头行、无其他 stdout 输出（诊断走 stderr）；第 1 列为批 `id`，第 2 列为 `tests_filter`（无该键为 `-`）

#### BDD-44: tests_filter 含管道/换行/反引号时观察表行仍为 7 列且可直接粘贴
- Given 某批 `tests_filter` 为 `"python -m pytest tests/a -q | tail -n 5"`；另一批为含反引号与反斜杠的值（如 ``python -m pytest -k `x` C:\t``）；第三批的 `tests_filter` 含换行（YAML 双引号内 `\n` 转义）
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then stdout 恰三行（一批一行，换行未产生额外行）；第 2 列依次为 `python -m pytest tests/a -q \| tail -n 5`、``python -m pytest -k \`x\` C:\\t``、含字面 `\n` 的单行文本（口径 D）；每行按 GFM 规则切分**恰 7 列**

#### BDD-45: 耗时列来自 duration_seconds
- Given 某批证据含 `duration_seconds: 8`；另一批证据缺该键或值不可解析为非负数
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then 前者耗时列为 `8s`，后者为 `-`；耗时列的取值不影响 verdict 列

#### BDD-46: evidence 列反映日志文件存在性
- Given 批 A 的 `P4-evidence/A.log` 存在，批 B 的不存在
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then A 行 evidence 列为 `yes`，B 行为 `no`

#### BDD-47: commit 形态 = per-batch（逐批）
- Given `tmp_path` git 仓库：默认分支 `main` 上有初始提交，任务分支自 `main` 分出；批 A 声明 `output: [src/a.py]`、批 B 声明 `output: [src/b.py]`，`src/a.py` 与 `src/b.py` 在任务分支上分别于**两个独立 commit** 中被改动（且 `src/a.py` 在 `main` 的更早历史提交中也被改动过——区间外提交不可见，口径 E）
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then A、B 行 commit 形态列均为 `per-batch`

#### BDD-48: commit 形态 = merged（合并）
- Given 同 BDD-47 的分支布局，但 `src/a.py` 与 `src/b.py` 在任务分支的**同一个 commit** 中被改动
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then A、B 行 commit 形态列均为 `merged`

#### BDD-49: commit 形态无法归属时为 UNKNOWN
- Given 同 BDD-47 的分支布局，且某批属下列之一：未声明 `output`；其 `output` 文件在提交区间（`merge-base..HEAD`）内从未被改动；其 `output` 文件在区间内分散于多个 commit
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then 该批 commit 形态列为 `UNKNOWN`

#### BDD-50: git 基线无法确定时 commit 形态与 boundary 为 UNKNOWN，并给出原因
- Given `tmp_path` git 仓库中既无 `origin/HEAD`、也无本地 `main`/`master` 分支（如仅有分支 `trunk`），或 `HEAD` 即默认分支尖端使提交区间为空；某批已声明 `output` 且其文件已提交
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then exit 0；该批 commit 形态列与 boundary 列均为 `UNKNOWN`；stderr 含 `baseline` 字样的诊断；该批 verdict 列不受影响

#### BDD-51: boundary = exact
- Given 某批为逐批 commit（区间同口径 E），声明 `output: [src/a.py]`，该 commit 的 `git diff --name-only` 在排除 `{AGATE_WORKSPACE}/tasks/` 前缀（此处为默认工作区 `agate-workspace/tasks/`）后恰为 `{src/a.py}`
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then 该批 boundary 列为 `exact`

#### BDD-52: boundary 的工作区排除前缀随工作区配置而变
- Given 项目根 `.agate.env` 含 `AGATE_WORKSPACE=my-ws`；某批为逐批 commit，声明 `output: [src/a.py]`，该 commit 改动 `src/a.py` 与 `my-ws/tasks/T1/P4-evidence/A.log`；另一批的 commit 改动 `src/b.py`（声明 `output: [src/b.py]`）与 `agate-workspace/tasks/T1/note.md`（此处**非**当前工作区）
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then 前一批 boundary 列为 `exact`（`my-ws/tasks/` 前缀被排除）；后一批 boundary 列为 `mismatch`（`agate-workspace/tasks/` 不再被排除，计为未声明改动）

#### BDD-53: boundary = mismatch
- Given 某批为逐批 commit，声明 `output: [src/a.py]`，但该 commit 还改了未声明的 `config/x.yaml`（或声明了却没改的文件）
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then 该批 boundary 列为 `mismatch`

#### BDD-54: boundary = UNKNOWN（合并 commit / 无 output）——I1 诚实标注
- Given 某批为合并 commit 形态（即使已声明 `output`），或未声明 `output`
- When 运行 `check-mvwu.py --observe <task_dir>`
- Then 该批 boundary 列为 `UNKNOWN`

#### BDD-55: --observe 的 verdict 列与默认模式一致，且同样只读、同 exit 约定
- Given 任一含 BDD-25..29 各态场景的任务目录
- When 分别运行 `check-mvwu.py <task_dir>` 与 `check-mvwu.py --observe <task_dir>`
- Then 同一批的 verdict 值逐一相同；`--observe` 亦 exit 0（用法/目标错误 exit 2）、不写任何文件、不改 `.state.yaml`

#### BDD-56: 判据 6——--observe 在仓库内真实任务目录上跑通
- Given 仓库内任一已有任务目录（不要求多批；如 `agate-workspace/tasks/TAG0034-dispatch-routing/`、`TAG0035-gate-robustness/`，取其一）
- When 在 worktree 根运行 `python3 agate/scripts/check-mvwu.py --observe agate-workspace/tasks/<该任务>`
- Then exit 0；stdout 至少一行、行数 = 该任务 `dispatch_plan.batches` 数（无则 1 行，MVWU 列 `-`）；**每行**满足 BDD-43 的 7 列结构；运行前后 `git status --porcelain` 无变化；该输出行被摘录进 P6 证据（`P6-evidence/`）

### 单测与平台无关

#### BDD-57: check-mvwu.py 自身单测覆盖六项检查、四态与 --observe 各列，且合规
- Given 本任务完成
- When 检查 `agate/tests/` 下新增的 check-mvwu 测试文件（如 `unit/test_check_mvwu.py`）
- Then 该文件含：检查 1-5 各 ≥1 条失败用例、verdict 四态各 ≥1 条用例、`--observe` 七列各有 ≥1 条断言用例（含 BDD-47..54 的 commit 形态、git 基线不可确定与 boundary 各态）、exit-code 约定用例（BDD-36/37）、reason 判定顺序用例（BDD-34）、列表编码含参数化 id 用例（BDD-30/31/32）、输出转义用例（BDD-22/44）；所有文件写入均经 pytest `tmp_path`（无硬编码 `/tmp`，无对仓库内 `agate-workspace/` 的写入——运行前后 `git status --porcelain agate-workspace` 不变）；不裸 `python3`（用 `sys.executable`/既有 PYTHON 探测 helper）；文件内首个测试用例带 `@pytest.mark.windows_smoke`

#### BDD-58: 自身单测在 Windows 冒烟口径下可选中并通过
- Given 本任务完成
- When 运行 `python3 -m pytest agate/tests/unit/test_check_mvwu.py -m windows_smoke`
- Then 选中 ≥1 条且全部通过

### ⑤-a 术语补录

#### BDD-59: CONTEXT.md 补录 5 个术语，沿用三列格式且不动既有行
- Given `agate/CONTEXT.md` 现有术语表（`^| ` 行共 29，含表头；即 28 条术语行——P0-brief 所称"29 条"含表头，无实质影响）
- When 对比 `git diff <内核基线> -- agate/CONTEXT.md`
- Then diff **只含新增行**（无删除/修改行）、新增**恰 5 个**表格数据行，其"术语"列依次覆盖 `MVWU`、`tests_filter`、`P4-evidence`、四态 verdict（含 `PASS`/`FAIL`/`EXPECTED_RED`/`UNKNOWN` 四词）、`boundary`（含 `I1`）；每行均为 `| 术语 | 定义 | 首次定义位置 |` 三列、"首次定义位置"列非空且指向仓库中存在的文件路径（相对仓库根或相对 `agate/`，与既有行的写法一致）；`MVWU` 定义含"最小可验证工作单元"，四态 verdict 定义含"UNKNOWN 不等价于 PASS"

### ⑤-b Deep Modules 审查锚点（只要求成文）

#### BDD-60: role-system.md 新增审查锚点节
- Given 本任务完成
- When 读取 `agate/role-system.md`
- Then 存在一个新增的 `##`/`###` 节，标题含"审查锚点"，正文含以下要点（字面标记）：审查对象=角色文件/阶段卡片；核心问题=是否把"实现细节"写进"接口"（字面：`浅化`）；判据=是否规定"第 1 步做 A、第 2 步做 B"式执行顺序（字面：`执行顺序`、`资源地图`——协议哲学是"资源地图 + 判据"、不给步骤脚本）；说明其与批切分判据（⑤-c）**正交、不可互相替代**（字面：`正交`）；新增节不含"已生效"/"已验证生效"字样；`agate/assets/execution-roles/` 下除 `architect.md` 外的文件 `git diff <内核基线>` 为空（不重写既有角色行为约定）

### ⑤-c 批切分三判据（Tracer Bullet / Vertical Slice / Fitness Functions；只要求成文）

#### BDD-61: 判据一（Tracer Bullet）落 architect.md 与 P2 卡片
- Given 本任务完成
- When 读取 `architect.md`「批次设计」与 P2 卡片「dispatch_plan 机器字段」二处
- Then 二者均含（字面标记）：`Tracer Bullet`；触发条件（任务含 ≥2 个批且存在可端到端验证的关键路径）；首个批应为端到端最小打通、其 `tests_filter` 覆盖该路径的**冒烟级**验证（字面：`冒烟`）而非该批完整单元测试；目的（投入全部实现前取得"管道确实通"反馈）；**与 P3 红灯批的边界**（字面：`P3 红灯批`；tracer bullet 不替代 P3 完整红灯批，只是首个批的切法，后续批仍按常规 MVWU）

#### BDD-62: ⑤-d Walking Skeleton 拒绝/吸收记录（同处成文，无独立交付物，且与 P2-skeleton 消歧）
- Given 本任务完成
- When 读取 `architect.md` 判据一所在处（P2 卡片同处可选）
- Then 含字样 `Walking Skeleton`，并说明：**吸收**"骨架先跑通"并入判据一（字面：`吸收`）；**拒绝**自动化部署/CI 配置部分，依据 `adr.md` ADR-003（字面：`拒绝`、`ADR-003`；技术栈中立、不硬编码语言/框架/部署方式）；明示其与既有 `P2-skeleton.md`「骨架声明」（字面：`P2-skeleton.md`；bootstrap 项目的目录布局声明）**不是同一机制**；本任务**不新增**任何新字段/新 gate/新模板文件（`agate/assets/templates/` 无新增文件）；新增文字不含"已生效"字样

#### BDD-63: 判据二（Vertical Slice）落 architect.md 与 P2 卡片
- Given 本任务完成
- When 读取上述二处
- Then 二者均含（字面标记）：`Vertical Slice`；批/包**优先按业务能力切**（字面：`业务能力`；一个批 = 一条端到端可交付能力）而非技术层；若必须按技术层切**须在 `P2-design.md` 写明理由**（字面：`写明理由`；非禁止、非 gate 拦截）；判据式表述"批 `id` 应能回答'这个批交付了什么能力'而非'动了哪层代码'"；与判据一的关系（端到端批天然是垂直切片，同一决策的两个面）；`check-gate.py` 无新增对批 `id`/理由的校验（同 BDD-3 的空 diff）

#### BDD-64: 判据三（Architecture Fitness Functions）落 architect.md 与 P2 卡片
- Given 本任务完成
- When 读取 architect.md 与 P2 卡片「gate_commands 声明」节附近
- Then 二者均含（字面标记）：`Fitness Functions`、`适应度`；`gate_commands` 除功能测试外**应为本任务涉及的架构约束**配置适应度检查，示例维度含依赖方向/分层边界/循环依赖/公共 API 稳定性之至少三项；**agate 不规定具体工具**（字面：`由项目自选`；命令仍经 `gate_commands` 注入）；只要求"该维度存在"；项目判定无架构约束时写明"本任务无架构适应度检查"即可（字面：`本任务无架构适应度检查`；不强制）；`agate/` 内不出现对 ArchUnit/dependency-cruiser/import-linter 的**强制**要求（若作示例须带"示例/由项目自选"字样）

### ⑤-e 决策复审机制

#### BDD-65: adr.md 头部补复审触发条件（过时不删）
- Given `agate/adr.md` 现有 ADR-001..N 正文
- When 读取本任务后的 `agate/adr.md`
- Then 文件头部（"本文件记录…"引言之后、首个 `## ADR-` 之前）新增复审触发条件（字面标记）：某 ADR 的前提被后续变更证伪时须**就地标注「已过时 + 被什么取代」**（字面：`已过时`）、**不删除**（字面：`不删除`；保留决策史）；复审时机含"每次新增 ADR 时顺带复核相关旧 ADR"与"P7 一致性检查阶段"（字面：`复审`、`P7`）；既有 ADR 正文相对基线 **diff 无删除行**；不含自动过期/强制复审 gate 的表述

#### BDD-66: 项目侧决策落点与 P2 读取成文
- Given 本任务完成
- When 读取 `agate/phase-cards/P2-design.md` 与 `agate/phase-cards/P7-consistency.md`
- Then P2 卡片含（字面标记）：项目内**跨任务的架构决策落 `{AGATE_WORKSPACE}/decisions/`**（字面：`decisions/`）、P2 开始前**读取既有决策**、发现前提被证伪时就地标注「已过时 + 被什么取代」且不删（字面：`已过时`）；P2 卡片与 P7 卡片**至少一处**写明写入决策的时机；不含"必须拦截"式 gate 表述；`check-gate.py` 无读取 `decisions/` 的新代码（同 BDD-3 空 diff）；具体文件名/模板不作规定

### 负向与收口

#### BDD-67: 零协议内核改动（负向，可机械判定）
- Given 本任务全部提交完成
- When 对以下路径执行 `git diff <内核基线> -- <paths>`：`agate/scripts/check-gate.py`、`agate/rules/phases.yaml`、`agate/rules/schema/`、`agate/scripts/pre-commit-gate.py`、`agate/scripts/pre-commit-gate.sh`、`agate/scripts/commit-msg-self-gate.py`、`agate/scripts/commit-msg-self-gate.sh`、`agate/scripts/pre-push-gate.py`、`agate/scripts/pre-push-gate.sh`、`agate/scripts/check-state-yaml.py`、`agate/scripts/agate-state-yaml-check.py`、`agate/scripts/check-state-transition.py`、`agate/scripts/check-events.py`、`agate/scripts/agate_common.py`、`agate/scripts/check-p6-provenance.py`、`agate/scripts/check-judge-verdict.py`
- Then 输出全部为空（`.state.yaml` schema / gate 分支 / 状态机 / hook 三件套 / gate-events 审计链均未被触碰）

#### BDD-68: check-mvwu.py 不挂 gate，且未触碰历史任务产物
- Given 本任务完成
- When ① `grep -rn "check-mvwu" agate/rules agate/scripts/check-gate.py agate/scripts/pre-commit-gate.py agate/scripts/ci-gate-backstop.py agate/scripts/agate-summary.py .github/`；② `git diff <内核基线> --stat -- 'agate-workspace/tasks/TAG00[0-2]*' 'agate-workspace/tasks/TAG003[0-5]*'`
- Then ① 命中 0 行（不在 gate/hook/CI/防护清单中登记）；② 输出为空（不回填、不改任何其他任务目录）

#### BDD-69: 新脚本的登记面同步与计数文档一致
- Given 本任务完成
- When 读取 `agate/scripts/README.md`、`agate/tests/README.md`，并运行 `bash agate/tests/scripts/count-tests.sh`
- Then `scripts/README.md` 脚本表含 `check-mvwu.py` 一行，说明"观测、不阻断、exit 0=任一 verdict、2=用法/目标错误"并含 `--observe`；`tests/README.md` 表含 check-mvwu 测试文件一行且其用例数 = `pytest --collect-only` 对该文件的实际数；`count-tests.sh` 总数 ≥ 1668 + 该文件用例数；`CHANGELOG.md` `[Unreleased]` 含 `TAG0036`

#### BDD-70: SELF-GATE 收口——全量测试 / consistency / ruff 全绿且基线只增不减
- Given 本任务全部提交完成（命中 SELF-GATE 触发面：`agate/scripts/*.py` 与 `agate/**/*.md`）
- When 依次运行：`python3 -m pytest agate/tests/ --reruns 1 -n auto`；`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`；`~/.venvs/agate-dev/bin/ruff check agate/`
- Then pytest 0 failed、passed ≥ 1666 + 新增用例数、skipped 仍为 2；consistency **0 ERROR**（含 CHECK 10：所有文档中的 `check-mvwu.py` 引用可解析）；ruff 0 error；本任务未新增/修改任何 `.sh` 文件，故 shellcheck 不适用（`git diff <内核基线> --name-only | grep '\.sh$'` 为空）

#### BDD-71: SELF-GATE 语义审查留痕
- Given 本任务 P4 完成
- When 检查任务目录
- Then 存在 `P4-protocol-alignment-review.md`（`agent` ≠ `main`，含结论），且 P4 提交信息含 `self-gate-review:` 路径

## 4. 同类扫描（强制节）

### 4.1 扫描命令与命中（均在 worktree 根执行，排除 `.git`）

> 命中数为 P1 首次撰写时实测；requirements-review 复核时因含 TAG0036 P1 自身派发/需求文件而略增（`tests_filter` 13 文件 / 157 行，`P4-evidence` 12 文件，`check-mvwu` 10 文件），增量均为本任务 P1 自引用，`agate/` 内命中数不变。

| 符号 | 命令 | 命中（文件 / 行） | 分布 |
|------|------|------------------|------|
| `tests_filter` | `grep -rIl tests_filter . --exclude-dir=.git`；`grep -rIn ... \| wc -l` | 11 文件 / 106 行 | 协议本体 `agate/` **0**；设计/评审 `docs/`（`design-mvwu-protocol.md`、`design-orchestration-evolution-analysis.md`、`design-notes/README.md`、`reviews/review-260916-0828.md`）；任务/路线图（`roadmap.md`、`active-tasks.md`、TAG0035 P0/P1、TAG0036 P0/P1）；`HANDOFF-TAG0036.md` |
| `P4-evidence` | `grep -rIl "P4-evidence" ...` / `find agate-workspace -type d -name P4-evidence` | 9 文件 / 53 行；目录数 **0** | 同上，协议本体 **0** |
| `check-mvwu` | `grep -rIl "check-mvwu" ...` | 8 文件 | 均为设计/路线图/P0/HANDOFF；`agate/scripts/` **无**该文件 |
| `MVWU` | `grep -rIl MVWU agate` | **0** | 协议本体尚无任何 MVWU 概念 |
| `dispatch_plan` | `grep -rIc dispatch_plan agate \| grep -v ':0$'` | **13 文件** | 见 4.2 |
| `decisions` | `grep -rIn decisions agate`（排除 tests） | 10 行 | 全为"目录创建/工作区布局"（`WORKFLOW.md:95`、`state-machine.md:42-43`、`SETUP.md:316`、`orchestrator-template.md:22,105`、`UPGRADING.md:872`）+ `review-mapping.md:5`/`check-protocol-consistency.py:94` 的项目侧 `docs/decisions/` 示例；**无任何阶段卡/角色规定写入方** |
| `骨架`/`skeleton` | `grep -rIn "骨架\|skeleton" agate`（排除 tests、"流程骨架"） | 见 4.4 | `P2-skeleton.md` 机制 |
| ⑤ 概念词 | `grep -rIln "Tracer Bullet\|Vertical Slice\|垂直切\|Fitness\|适应度\|Walking Skeleton\|Deep Module\|深模块\|Evolutionary"` agate | **0** | 概念名词协议内均无；仅 `Ubiquitous` 在 `agate/AGENTS.md` 有 1 处 |

### 4.2 `dispatch_plan` 全部 13 个消费方逐个判定

| 文件（agate/ 下） | 现状 | 新增可选键 `tests_filter` 是否需同步 | 处理 |
|------|------|------|------|
| `scripts/check-gate.py`（11 处） | `_gate_p2_dispatch_plan` 不拒未知键 | 否（零内核硬约束）。同类 fail-open 只登记 | **不处理**代码；DEBT 登记见 BDD-5 |
| `scripts/agate-md-field-get.py`（3 处） | `JSON_FIELDS`，frontmatter-only 原样 dump | 否（嵌套键自然透传） | **不处理**；BDD-1 验证透传 |
| `scripts/check-structure-consistency.py`（1 处） | `_TASK_FRONTMATTER_FIELDS` 仅**顶层**键白名单，含 `dispatch_plan`（该符号**仅**存在于此文件，`agate-frontmatter-check.py` 无此符号） | 否（`tests_filter`/`output` 嵌套在 `dispatch_plan` 内，不产生新顶层键） | **不处理**；BDD-9 断言两脚本无 diff |
| `phase-cards/P2-design.md`（4 处） | 「dispatch_plan 机器字段」节，示例无 tests_filter | **是** | **处理**（BDD-6/9/61/63/64/66） |
| `assets/execution-roles/architect.md`（3 处） | 「批次设计」节 | **是** | **处理**（BDD-7/9/61/63/64） |
| `assets/templates/task-files.md`（3 处） | 第 250 行 dispatch_plan 示例注释 + 阶段产出表（无 P4-evidence 行） | **是**（字段登记 + 新证据落点登记） | **处理**（BDD-11） |
| `dispatch-protocol.md`（4 处） | 模式 3 "汇总统一 commit"（:618）+ judge 白名单/黑名单（:404-410） | 提交粒度决策属用户裁决；judge 黑名单与 `check-judge-verdict.py` 同源，改动会触及 P6.5 语义面 | **不处理**（P0 out-of-scope：不改 P6.5/白名单；白名单为默认拒绝，P4-evidence 不在其内即受限）；BDD-12 断言无 diff |
| `scripts/README.md`（1 处） | agate-md-field-get 行列举 op | 该行不需列 tests_filter；但需登记**新脚本** | **处理**（新脚本行，BDD-69） |
| `tests/README.md`（1 处） | dispatch_plan 契约测试表（10 用例） | 既有 10 用例不变；需为新测试文件新增一行 | **处理**（BDD-69） |
| `UPGRADING.md`（1 处） | 历史迁移说明（CHECK 10 整文件豁免） | 发布时才写版本章节；非本任务 | **不处理**（P8 发布清单范畴） |
| `tests/unit/test_dispatch_orchestration.py`（19 处） | 既有契约测试 | 不得破坏 | **不改**，BDD-3 回归 |
| `tests/unit/test_agate_md_field_get.py`（9 处） | 既有 | 同上 | **不改**，BDD-3 回归 |
| `tests/unit/test_agate_md_field_set.py`（2 处） | 既有（`field-set` 不支持嵌套写入，无关） | 同上 | **不改** |

### 4.3 新脚本落地面（参照：独立 check 脚本 `check-platform-assumptions.py` 与 `check-p6-provenance.py` 在协议中的出现位置）

`check-retrospective.py` 因被 `pre-commit-gate.py` 链调用不适合作参照（会带入 hook 登记面）；改取**未挂 hook 的独立 check** `check-platform-assumptions.py` 作参照，其出现位置：`agate/scripts/README.md`（脚本表 :45）、`agate/tests/README.md`（测试映射表 :87）、`agate/UPGRADING.md`（发布章节）、`.github/workflows/protocol-tests.yml`（CI 步骤）、`check-protocol-consistency.py`（CHECK 引用）。据此对 `check-mvwu.py` 的登记面逐项判定：

| 登记面 | 判定 | 理由 |
|--------|------|------|
| `agate/scripts/README.md` 脚本表 | **处理**（BDD-69） | 脚本-文档登记；且 README 在 CHECK 10 扫描面内 |
| `agate/tests/README.md` 映射表 + 计数 | **处理**（BDD-69） | 计数漂移须同步 |
| `agate/CONTEXT.md`（⑤-a 引用 `check-mvwu.py` 时） | **处理**（BDD-59/70） | CONTEXT 在 CHECK 10 扫描面内，脚本须先于/同 commit 落库（隐含需求 8） |
| `CHANGELOG.md` `[Unreleased]` | **处理**（BDD-69） | P8 `check-changelog.py` 要求含 task_id |
| `agate/UPGRADING.md` | **本次不处理** | 版本章节随发布（AGENTS.md 发布清单第 3 步），非本任务交付 |
| `agate/scripts/agate-summary.py` `_GUARD_SCRIPTS` / `_DRIFT_SCRIPTS` | **本次不处理** | 二者列的是 hook 链/漂移防护脚本；本脚本不挂 gate（BDD-68 断言 0 命中） |
| `check-protocol-consistency.py` CHECK 9 锚点表 | **本次不处理** | 该表是"文档声明规则 ↔ 脚本关键词"锚点，对独立观测脚本无强制新增；CHECK 10 会自动覆盖引用漂移 |
| `.github/workflows/protocol-tests.yml` | **本次不处理** | 新单测经 `pytest agate/tests/` 自动纳入；无需独立 CI step（不引入 CI 机制，且 BDD-68 断言 `.github/` 0 命中） |
| `agate/WORKFLOW.md` 表（如 2.12 行式） | **本次不处理** | 该表登记 hook 触发的检查；本脚本不触发 |
| `agate/phase-cards/P4-implementation.md` | **处理**（BDD-10） | 证据写入方说明 + 可选提及 `check-mvwu.py` 为事后观测工具 |

### 4.4 ⑤ 组目标文件同义节 / 撞名扫描

| 目标文件 | 同义节扫描结论 | 处理 |
|----------|----------------|------|
| `agate/CONTEXT.md` | 5 术语（MVWU/tests_filter/P4-evidence/四态 verdict/boundary）grep 计数 **0**，无同义行 | 追加（BDD-59）；`^| ` 行 29（含表头），P0-brief "29 条"含表头，不影响 |
| `agate/role-system.md` | 无"审查锚点"/"深模块"节；无执行顺序审查视角 | 新增节（BDD-60） |
| `agate/adr.md` | 头部无复审触发条件；"过时"仅出现在他处；`adr.md:278` 已被 `28293d8` 同步 | 头部补触发条件（BDD-65）；**不再以"278 行失实"为证据** |
| `architect.md` / `P2-design.md` | 无 Tracer Bullet/Vertical Slice/适应度同义节（4.1 概念词 grep = 0）；`gate_commands` 现只承载功能测试命令 | 补三判据（BDD-61/63/64） |
| `P2-design.md` / `P7-consistency.md`（决策落点） | `decisions` 在卡片/角色内 **0 命中**（4.1）；`state-machine.md`/`SETUP.md`/`orchestrator-template.md`/`WORKFLOW.md` 仅有"创建 `decisions/` 目录"，**无写入方** | 卡片侧补落点（BDD-66）；**上述三个创建方文件本批不改**——"创建目录"语句仍准确，缺的是写入方而非创建方 |
| **撞名**：`skeleton-template.md` / `P2-skeleton.md` / `project_phase: bootstrap`（`P2-design.md:84-89`、`architect.md:121-128`、`P4-implementation.md:71-80`、`check-gate.py` bootstrap 校验） | **既有"骨架声明"= 0→1 项目的目录布局声明（五类候选目录），与 Walking Skeleton"骨架先跑通"同词不同义**；P0-brief ⑤-d"无对应"对概念成立 | ⑤-d 成文须明示区别（BDD-62）；**不改**既有 bootstrap 骨架机制 |

### 4.5 同类扫描结论

- `tests_filter` / `P4-evidence` / `MVWU` / `check-mvwu`：协议本体 `agate/` **命中 0**，命中仅在设计文档、评审、路线图、任务产物，均属**本任务上游输入**，无存量同类实例需迁移；**已确认无需修任何存量**。
- `dispatch_plan`：13 消费方逐个判定见 4.2（处理 5 / 不处理 8，含 3 个既有单测作回归锚）。
- **同类 fail-open 只此一处**：`check-gate.py::_gate_p2_dispatch_plan`（`except ValueError: return None` 与 `not isinstance(plan, dict): return None`、缺 `dispatch_plan` 时 `return None`）；本任务**只登记 DEBT、不修**（BDD-5）。其余 gate 函数的 fail-open 属 TAG0035 已处理范围。
- **同类未来实例的回归拦截**：`tests_filter` 写法约束（引号/不裸 python3/scoping）、⑤ 判据关键词、`decisions/` 落点均以 **grep 断言型审计测试**兜底（BDD-6/7/8/60-66 可直接转成断言测试，且各含字面标记便于写无争议的 grep 断言；具体形态由 P3 定，不在 P1 规定工具）；`check-mvwu.py` 行为由自身单测兜底（BDD-57）。

## 5. 待确认清单

[NO_NEED_CONFIRM]

以下三项 SUGGEST **已采纳**（主 Agent 与 requirements-review 在 `P1-review.md`「SUGGEST-1/2/3 逐条独立结论」中均同意；推荐方案明确、不涉破坏性/业务方向，不阻塞）；保留为审计痕迹：

- **SUGGEST-1（已采纳）**：在 `P4-evidence/{batch}.log` 最小内容中追加**可选**键 `failed_tests`（默认 `[]`），理由——EXPECTED_RED 要"全部命中 expected_red"，无失败清单则不可判定；无此键时只能退化为"非零退出且 expected_red 非空即 EXPECTED_RED"，会把预期外红灯误判为预期红（fail-open 方向，违反 UNKNOWN≠PASS 哲学）。这是对 P0-brief ② 最小内容格式的**细化**（P0 自身已因同类理由追加 `duration_seconds`），非范围扩张；BDD-10/27/28/29/30/31/32/33 依赖。列表编码与元素相等口径见 §3 口径 C。
- **SUGGEST-2（已采纳）**：verdict 与 boundary/commit 形态**解耦**——verdict 仅由检查 1-6 决定，boundary 只是 `--observe` 的独立观测列；理由见隐含需求 5（避免 Q2 污染 Q1、避免两模式 verdict 不一致）。**这是对设计文档 §5.1.1 权威表（`UNKNOWN` 触发条件含"边界不可归属"）与 §7.3 示例 C 行（合并 commit ⇒ verdict UNKNOWN）两处的有意偏离**，限定为**阶段 1 观测口径**；verdict 是否纳入 boundary，由阶段 2 与提交粒度决策（P0-brief 决策 A/B，用户裁决）一并复议。BDD-42/55 依赖（BDD-42 正文不变）。
- **SUGGEST-3（已采纳）**：把 `output`（可选，仅供 `--observe` 读取，不加 gate 校验）随 ① 的字段落地文字一并说明；理由见隐含需求 6。设计文档 §4.2 已预算该字段，P0-brief ③ 的 boundary 列来源已依赖它；仅增补写法说明，不新增校验、不改内核。BDD-9 依赖。

## 6. 能力需求声明

```yaml
capability_requirements: []
```

无浏览器/外部网络/视觉等特殊能力需求：全部验证经 `python3` + `pytest` + `git` + `grep`；无 frontend 域，故无 UX 类别 BDD / `ui_render_shape`。`requires_minimal_validation` 不适用（不依赖浏览器行为/安全模型/外部系统行为）。

## 7. 范围声明与裁剪说明

- `packages: [agate-scripts, agate-docs, agate-tests]`；`domains: [backend]`（Python CLI 脚本 + 协议文档，无 frontend/mcp/security 面）。
- `risk_level: medium`：新增独立脚本 + 多份协议卡片/角色/术语文档改动、命中 SELF-GATE 触发面；但**零内核改动**、可选键、不阻断，故非 high；亦非 low（协议文档语义改动需 protocol-alignment-review）。
- `phases: [P1, P2, P3, P4, P5, P6, P7, P8]`：**不裁剪**。P3 保留——`check-mvwu.py` 是新代码，须 TDD；⑤ 文档类改动的测试策略由 P3 定（通常 grep 断言审计测试，见 §4.5）。P6.5 judge 已由 `.state.yaml` `judge.enabled: true` 强制。
- `ceremony`：不声明（缺省 standard，fail-closed；本任务不做薄化）。

## 8. 不在范围（引用 P0-brief out-of-scope，本阶段不扩）

- 阶段 2（批级 gate）、阶段 3（`E_pipeline`）、DAG/Task Graph；**不改协议内核**（BDD-67）；不改 P6.5/judge 白名单/provenance/目录登记（BDD-12）。
- **不主动造样本、不回填历史任务**（BDD-68）；Q1/Q3 不作为任何完成条件；Q2=13% 仅引用。**不把 TAG0036 自身是否作为试点样本**写成 BDD（可选，不强制）。
- **提交粒度决策（P0-brief 决策 A/B）属用户裁决项，非本任务交付**，本基线**不替用户选**；SUGGEST-2 的"verdict 是否纳入 boundary"亦留待阶段 2 与该决策一并复议。
- **回顾性采集**（对已合并回默认分支的历史任务重建 commit 形态/boundary）不在范围：阶段 1 观测发生在任务分支上（口径 E，隐含需求 12）。
- ⑤ 组：不重构既有术语表、不加术语一致性机械校验；不改既有角色行为约定；不规定架构适应度工具；不强制垂直切分（判据非硬规则）；不做决策自动过期/强制复审 gate；不引入部署/CI 机制；不创建/预填 `{AGATE_WORKSPACE}/decisions/` 的任何决策文件；⑤-b/⑤-d **只成文、不宣称机制已生效**（P5/P6 不做超出"成文"的断言）。
- 不修 `_gate_p2_dispatch_plan` 的 fail-open（只登记，BDD-5）；不改 `agate/UPGRADING.md`（发布时写）。
- 交付顺序提示（给 P2）：`check-mvwu.py` 须先于/同批于任何引用它的文档落库（CHECK 10，隐含需求 8）。

## 修订记录（retry #1）

依据 `P1-review.md`（needs-revision）。编号均为**重排后的新编号**（BDD 58 → 71，映射：旧 16-18→19-21、旧 19-25→23-29、旧 26→35、旧 27→36/37、旧 28→38、旧 29/30→39/40、旧 31-33→41-43、旧 34-35→45-46、旧 36-38→47-49、旧 39-41→51/53/54、旧 42-58→55-71；新增 16/17/18/22/30-34/44/50/52）。未改动评审判"通过"的 BDD 语义；未超出 P0-brief out-of-scope。

| 项 | 级别 | 处置 | 涉及 BDD |
|----|------|------|----------|
| F-1 | MUST | **已改**：§2-5 与 SUGGEST-2 如实援引设计文档 §5.1.1 权威表（`UNKNOWN` 含"边界不可归属"）与 §7.3 示例 C 行两处，明示为**对设计文档的有意偏离**（不再称"读法不同"）；限定"阶段 1 观测口径"；声明 verdict 是否纳入 boundary 由阶段 2 与提交粒度决策（P0-brief 决策 A/B，用户裁决）一并复议；BDD-42 正文不变（仅标题标注口径）；SUGGEST-1/2/3 转"已采纳" | 42, 55（依赖）；§2-5、§5、§8 |
| F-2 | MUST | **已改**：新增口径 D（输出转义）：`tests_filter` 列按 GFM 转义（`\|`、`\\`、`` \` ``、`\n`/`\r`、其余控制字符 `\xNN`，理由：管道在 markdown 表内的标准写法即 `\|`）；批 id 以 `\xNN` 逐字节可逆编码、非字符串/空为 `?`（理由：id 是标识符，契约行须可按空白分词）；BDD-43 列切分改按 GFM 规则；新增独立 BDD 覆盖含 `\|`/反引号/换行的 tests_filter 与不安全 id 的打印形态 | 22（新）, 43, 44（新） |
| F-3 | MUST | **已改**：新增口径 E：观测范围 = `git merge-base HEAD <默认分支>..HEAD`（默认分支 = `origin/HEAD`，缺则本地 `main`/`master`）；基线不可确定或区间为空 → commit 形态/boundary = UNKNOWN，stderr 含 `baseline` 原因；区间外历史提交不可见；写入 BDD-47/48/49 的 Given，新增 BDD-50 覆盖基线不可确定；已知局限（合并后回顾性采集）写入隐含需求 12 与 §8。BDD-51 注明 `{AGATE_WORKSPACE}/tasks/` 前缀排除口径：实测 `agate_common.resolve_workspace` 表明 workspace **可配置**（`.agate.env` → `AGATE_TASKS_DIR` → 默认 `agate-workspace`），故按当前 workspace 的 tasks 前缀排除，新增 BDD-52 覆盖自定义 workspace | 47, 48, 49, 50（新）, 51, 52（新） |
| F-4 | MUST | **已改**：新增口径 C：`expected_red`/`failed_tests` = 单行 YAML flow 序列、元素为双引号包裹的 pytest node id；元素相等 = node id 精确字符串相等；不可解析 → `UNKNOWN reason=expected_red`；BDD-27/28 示例改用引号包裹 node id；新增含参数化 id 的正例、近似 id 反例与不可解析 BDD；BDD-10 同步写入编码要求 | 10, 27, 28, 29, 30（新）, 31（新）, 32（新） |
| F-5 | MUST | **已改**：旧 BDD-27 拆为 36（四态 exit 0）与 37（用法/目标错误 exit 2）；旧 BDD-29 拆为 39（无可判定批的输入，含合并进来的旧 BDD-30 等价类，去冗余）与 40（证据损坏）；全量重排编号 1…71 连续，并同步 §2/§4/§5/§7/§8 及 BDD 内全部交叉引用 | 36, 37, 39, 40 |
| F-6 | SHOULD | **已改**：口径 B 显式给出 reason 顺序 tests_filter → evidence → command → exit_code → git_head → expected_red 并列各 reason 覆盖面，新增 BDD-34 固化；口径 G 定义 `git_head` 合法格式（全长 40/64 位十六进制且为存在的 commit；短 sha/ref 名不合法），BDD-24 扩展；`id` 重复 → 该 id 全部批 `reason=evidence`（BDD-34）；`id` 非字符串/空 → 打印 `?`、按判定顺序得 reason（BDD-22）；`exit_code: 0` 而 `failed_tests` 非空 → `UNKNOWN reason=exit_code`（新增 BDD-33） | 22, 24, 33（新）, 34（新） |
| F-7 | SHOULD | **已改**：BDD-9 去掉标题中的"采纳时生效"条件（SUGGEST-3 已采纳）；措辞改为 `agate-frontmatter-check.py` 与 `check-structure-consistency.py` 两脚本 git diff 均为空，并注明 `_TASK_FRONTMATTER_FIELDS` 仅存在于后者 | 9；§4.2 |
| F-8 | SHOULD | **已改**：文档类 BDD 每个必含要点至少固定一个字面标记（BDD-6/7/9/10/60-66 均以"字面：…"列出），便于 P3 写 grep 断言；BDD-8 的 grep 限定为位于 `tests_filter: "…"` 示例值内部的 `python3`，同行别处的 `python3 agate/scripts/check-mvwu.py` 不计 | 6, 7, 8, 9, 10, 60-66 |
| F-9 | SHOULD | **已改**：口径 F 定义检查 2 的"首词"语义（跳过前导 `NAME=value`；复合命令只判首词；`cd`/`export`/`set`/`source`/`.` 视为可解析；切分失败 → `reason=command`）；明示"不比对 command 与 tests_filter，属已知观测局限"；新增 3 条 BDD 固化（环境变量前缀、复合命令、不比对） | 15, 16（新）, 17（新）, 18（新） |
| 其余 | — | **P0_STALE 第 3、4 条**：夹带的"请主 Agent 补记"指令已移出标记外，正文注明主 Agent 已补记进 P0-brief（条目 (c)/(d)）；§0 "另记"处 BDD 引用同步为 BDD-62 | §0 |
