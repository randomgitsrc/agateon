---
phase: P1
task_id: TAG0042
type: features
parent: P0-brief.md
trace_id: TAG0042-P1-20261005
status: draft
created: 2026-10-05
agent: analyst
# ── v2.0 机器字段 ──
risk_level: high
ceremony: standard
phases: [P1, P2, P3, P4, P5, P6, P7, P8]
packages: [agate-config, agate-run, agate-config-schema, gate-layer, agate-ci-verify, agate-doctor, obligations-registry]
domains: [backend, cli, protocol]
implicit_coupling: true
---

# P1 需求基线 — TAG0042 项目形态命令化 + 规则脚本化

> 来源：`P0-brief.md`（主 Agent 任务简报）+ 外部设计分析 `analysis-declare-and-enforce.md`
> （经 R1–R4 评审 APPROVE；**该文件不在本仓**，本需求据 P0-brief 转述，已登记见 §2 隐含需求）。
> 批 0（X1–X9 缺陷修复）已走 hotfix 通道落地（PR #401 → v0.78.1，整改至 v0.78.3），
> **不在本任务的 P0–P8 阶段内**；`P0-batch0-record.md` 是它在本任务账本里的痕迹。

## 0. P0-brief 时效性质疑

**已核对 P0-brief 时效性，无漂移。** 逐条排查严重漂移判据（P0 卡）：

1. **`task` 目标方案是否仍成立**：`agate-config` / `agate-run` / 三态归宿（脚本执行 / 命令生成 /
   强制评审）**未被其他任务实现**——实测 `grep` 全仓 `agate-config` / `agate-run` /
   `agate-ci-verify` / `agate-doctor` / `obligations` / `delivery` / `preset:` 在 `agate/` 下**零命中**
   （仅出现在本任务派发/设计文档里）。目标方案未失效。
2. **`executor_env` 平台前提是否仍成立**：实测 `agate-resolve.py` → `AGATE_ROOT=/home/kity/.agate/v0.78.3/agate`
   （全局 current）；`check-protocol-consistency.py` → **0 ERROR / 398 WARNING**，与 P0-brief 声明的
   `consistency_baseline` 逐字吻合；pytest 可跑（collect-only 2622）。平台前提（dsh）成立。
3. **`known_risks` 的「已解决前提」是否实际未解决 / 已被他任务解决**：批 0 的 X1–X9「现在就是错的」
   已全部修复并合并（HEAD `a68d763`，v0.78.1→v0.78.3 已 tag + 安装），与 P0-brief 的登记一致，
   无「虚标已解决」；其余风险项（规模、第 4 批删除发版逻辑、第 6 批清单缺口）均**仍待本任务处理**，
   未被其他任务解决。

**局部变化（非漂移，仅记录现场事实）**：批 0 落地后 HEAD 前进到 `a68d763`（P0-brief 未写死 HEAD，
故不构成漂移）；`agate-next` 的「预先写入下一阶段」行为经实测复核**成立**——
`agate-next.py::_advance()`（第 198–210 行）在 gate 通过时把 `next_phase` 写入 `.state.yaml` 并
`git add`。注意与 `P0-batch0-record.md` §5 第 2 项 / 设计 §X9 的「agate-next **本就无**『预写 READY』
行为」**不矛盾**：后者仅指**终态 READY/DONE 不预写**（`_TERMINAL_PHASES = {PAUSED, READY, DONE}`），
而批 1 治理的是**普通 Pn→Pn+1 的预写**。两者是同一机制的不同侧面。

⇒ **无严重漂移，不阻塞**；P0-brief 主体无需重写。

## 1. 需求复述

把 P0-brief §二 的范围表用结构化语言重写（**批 0 已完成，不在此列**）：

**总目标**：让「项目形态」由项目用**声明**（而非协议里写死的技术栈假设）描述，让「规则」由**脚本在
不可绕开的路径上执行**（而非靠 Agent 记忆）；并把 160 项阶段义务逐项归入三态归宿——「脚本执行 /
命令生成 / 强制评审」，用 `rules/obligations.yaml` 防止「靠记忆的规则」重新长出来。

**分批判（每批独立 gate）**：

- **批 1 — 统一 phase 语义**：把 `agate-next` 由「gate 通过即预写下一阶段到 `.state.yaml`」改为
  「不预写」；同步阶段卡片描述。目标：`phase:` 在所有路径上都只表示「**本 commit 的产出阶段**」
  （与 P2/P8 卡「不要提前写 Pn+1」的既有表述一致）。
- **批 2 — `agate-config`（声明层）**：新增 `agate-config` 全部子命令 + schema + 唯一读取函数 +
  等价守护；`agate-setup` / `install-hook` 自动 `init`；`gate_p0` 调 `validate`（迁移期只 WARNING）。
- **批 3 — `agate-run`（执行层）**：新增 `agate-run`（含 `--baseline`、环境变量注入、`.out` 证据 +
  ignore 检查）+ `cmd_run` 账本事件 + hook 一并暂存账本；修正 formatter 计数。
- **批 4 — 关卡层分级**：关卡层按提交类型分级 + 转换表（含 `paused_from`）；P8 改为**交付收尾**，
  `delivery` 必须声明。
- **批 5 — CI 与诊断**：新增 `agate-ci-verify` + `agate-doctor`；替换 `ci-gate-backstop`。
- **批 6 — 义务登记表**：`rules/obligations.yaml` + `check-obligations`；剩余 122 项义务逐项决定去向；
  §4 的通用化清理。

**每批合并前必须满足**：① 双向 R6 差分**只在 `/tmp` 副本上跑**（AGENTS.md 工作流 0a）；
② R6 差分**除 agateon 外再加一份 peekview 只读副本**（不改 peekview，只看协议改动对它的效果）；
③ 从第 6 批起，义务登记表的 M 类（脚本强制）占比**不得下降**。

**明确不做**（P0-brief §三）：不改 peekview 或其他项目的声明/CI/hook；不为「判断类义务」强行
脚本化；不做「一次交付覆盖哪些任务」的协议定义；不复活原设计 §10 已撤回的 5 条意见。

## 2. 隐含需求识别

用户（所有者）只提出两条要求（形态声明化、规则脚本化），但技术上必须一并处理的依赖：

1. **外部设计分析不在仓库（数据缺口）**：`analysis-declare-and-enforce.md` 经 `find` 全仓无命中。
   **为什么必须**：P0-brief §四及批 6 的核心是「160 项义务逐项归宿」，而该分析只有**汇总数字**，
   逐条清单（每项位置/分类/现有脚本/失败证据）在三份审计的原始表里、**不在仓库中**。
   ⇒ 批 6 起草 `rules/obligations.yaml` **依赖这张表**，须向评审索取并入库（见 §4 待确认）。
2. **迁移兼容（存量使用者不受突兀破坏）**：协议是**装到每个使用者项目里**的。第 2 批起引入
   `agate-config` 后，**文件缺失时行为必须与现状一致 + WARNING**，到**截止版本**才改 `exit 1`；
   截止版本写入 `UPGRADING.md`。**为什么必须**：否则协议一升级，所有存量项目的 gate 会静默变红。
3. **第 4 批删除发版逻辑会波及所有使用者的发版检查**：peekview 的发版检查正来自这套协议。
   ⇒ 删除前必须提供 `preset: semver-changelog-tag`（把现有发版检查**原样搬进声明**），
   文件缺失时按**发版痕迹**（CHANGELOG / 版本文件 / `v*` tag）给显眼 WARNING，并在 `UPGRADING.md`
   写明迁移方式与截止版本。**为什么必须**：协议删功能时使用者不能悄无声息地失去保护。
4. **`agate-next` 行为变更会改变编排惯例**：批 1 使 `agate-next` 不再预写下一阶段，编排流程须相应
   调整（commit 时 phase 保持当前产出阶段）。**为什么必须**：peekview T085 的 8 次 `--no-verify`
   正是「预写 vs 不预写」冲突所致——不改则冲突持续。
5. **平台无关（Windows/MSYS2）**：`agate-run` 沿用 `agate_common` 用 bash 执行命令的既有假设，
   Windows（MSYS2）下 `pipefail` 与 `checkout-index` 的行为**未测**。**为什么必须**：协议是跨平台的
   硬约束，新执行层不能只保证 POSIX。
6. **账本一致性（append-only 哈希链）**：`agate-run` 新增 `cmd_run` 事件、hook 一并暂存账本。
   **为什么必须**：`gate-events.jsonl` 是 append-only + `prev_hash` 链，任何新写入必须走既有
   `append_event` 通道，否则破坏审计链（AGENTS.md 工作流 0a 的同类教训）。
7. **义务只增不减的守护**：第 6 批起 M 类占比不得下降。**为什么必须**：这是「规则不能靠记忆」的
   可量化护栏——没有它，登记表会随时间腐化成「又一份靠记忆的清单」。
8. **同类新增面（新增脚本的登记面）**：本任务新增 `agate/scripts/` 下文件，须按登记面实测登记
   （见 §3 同类扫描）。**为什么必须**：TAG0036 M18 实证——新增 `check-*.py` 会让 SG.6 由绿转红，
   凭推理判「不处理」已被证伪。

## 3. 同类扫描（强制节）

### 3.1 新增脚本名全仓扫描（命中清单 + 逐条判定）

对 5 个将新增的脚本名扫全仓（`*.py` / `*.md` / `*.yaml` / `*.yml`，排除 `agate-workspace/tasks`）：

| 符号 | 命中 | 文件清单 | 判定 |
|---|---|---|---|
| `agate-config` | 3 | `docs/reviews/handoff-tag0042-batch0-for-expert-review.md`、`docs/design-notes/design-tag0042-batch0-defects.md`（×2） | **本次处理**（本任务新建）——命中均为规划性引用，非既有实现 |
| `agate-run` | 3 | 同上（handoff ×1、design-notes ×2） | **本次处理**——同上 |
| `agate-ci-verify` | 2 | `docs/reviews/handoff-...md:179`、`docs/design-notes/...:18` | **本次处理**——同上 |
| `agate-doctor` | 1 | `docs/reviews/handoff-...md:179` | **本次处理**——同上 |
| `check-obligations` | 0（`agate/` 下零命中） | — | **本次处理**——本任务新建 |
| `ci-gate-backstop`（被替换对象） | 多 | `.github/workflows/protocol-tests.yml:308`、`agate-workspace/debt/tech-debt.md`、多个 `archived/` | **本次处理**（批 5 替换）＋**不处理**（`archived/` 是冻结快照，不改） |
| `obligations` / `delivery` / `preset:` | 0（`agate/` 下零命中） | — | **本次处理**——均为新产物 |

**结论**：5 个新脚本名在 `agate/` 协议本体下**均无既有实现**，不存在「改了一处漏了同类」的存量面。
`ci-gate-backstop` 的替换是批 5 的显式范围，`archived/` 冻结快照不回改。

### 3.2 新增脚本「登记面」机械门禁实测（**实测，非推理**）

按 P1 卡同类扫描第 5 条与 `agate/scripts/README.md`「新增脚本登记面」节：本任务新增
`agate/scripts/` 下文件，**把 5 个文件真放进仓库**跑了一遍相关测试与 consistency，记录**实际**变红/告警的面：

**实测方法**：复制既有脚本到 5 个目标名（`check-obligations.py` 用 `check-mvwu.py` 内容占位；
`agate-config` / `agate-run` / `agate-ci-verify` / `agate-doctor` 用 `agate-summary.py` 内容占位），
跑下列命令，**跑完即删除**（已 `git status --porcelain` 确认无残留）：

| 面 | 命令 | **实测结果** |
|---|---|---|
| ① CHECK9-coverage（WARNING，仅 `check-*.py`） | `check-protocol-consistency.py` | **仅 `check-obligations.py` 触发 WARNING**（`gate 脚本 … 既未纳入 CHECK 9 锚点表，也未列入豁免集`）；4 个 `agate-*.py` **零触发**。总计 0 ERROR / 399 WARNING（基线 398 + 本项 1） |
| ② SG.6（pytest **会红**） | `pytest test_protocol_alignment_review.py -k sg_6` | **`test_sg_6_check9_anchor_table_covers_all_gate_scripts` FAILED**（`['agate/scripts/check-obligations.py']`）；与 ① 同源（共用 `uncovered_gate_scripts()`） |
| ③ CHECK10 脚本名引用漂移 | 同上 consistency | **零触发**（方向相反：它只报「协议文档引用了**不存在**的脚本」，新增脚本不触发） |
| ④ README 脚本索引表 | 人工/特定脚本断言 | 无机械门禁（除 TAG0037 的 `agate_package.py`/`agate-release.py` 有 `test_doc_sweep.py` 断言）——属**约定**，建议补索引行 |
| ⑤ tests/README 映射表 | 人工/特定脚本断言 | 无机械门禁（除 `test_check_mvwu.py`）——属**约定** |
| ⑥ 用例总数 | `count-tests.sh` | **2622**（下界语义，只增不减，新脚本不被收集为测试） |
| ⑦ CHANGELOG / CONTEXT | 任务级约定 | 按任务流程 |

**⇒ 登记面实测结论（写入需求，供 P4/P8）**：
- **`check-obligations.py`（`check-*.py`）**：必须在 ① 二选一——承载 gate 判定逻辑 → 进
  `SCRIPT_ALIGNMENT_ANCHORS` 锚点表；纯观测/调度类 → 进 `GATE_SCRIPT_EXEMPT` 并写理由。
  **落成 BDD-13**。批 6 落地时**必须实测** SG.6 转绿（不满足则 P8 不可 READY）。
- **`agate-config` / `agate-run` / `agate-ci-verify` / `agate-doctor`（`agate-*.py`）**：**不在门禁覆盖
  面内**（实测零触发），登记属**约定**——建议在 `agate/scripts/README.md` 脚本索引表补一行（用途 +
  退出码语义）。
- **新增 `rules/*.schema.json`（`agate-config-schema`）**：`rules/schema/` 下已有 4 个 schema，新 schema
  须与之一致（命名、被 `check-protocol-consistency.py` 的 schema 扫描面覆盖）——落成 BDD-5 的验收面。

### 3.3 回归拦截（同类问题未来新增时的守护）

- 新增 `check-*.py` 的登记面守护：**已由既有 `uncovered_gate_scripts()` 单源判据承载**（①②共用），
  本任务只需在批 6 落地时按它的判据转绿——无需新增拦截手段，但**须落成 BDD-13** 确保转绿。
- 义务三态登记表的「只增不减」守护：**本任务新增**——落成 BDD-14（第 6 批 M 类占比不得下降）。

### 3.4 `agate-next` / phase 语义的同类实例扫描（批 1 相关）

对「预写下一阶段」关键符号扫描（`预先写入` / `预写` / `不要提前写` / `phase = 本 commit`）：

| 命中 | 位置 | 判定 |
|---|---|---|
| `agate-next.py::_advance()`（第 198–210 行） | 脚本 | **本次处理**（批 1 改为不预写） |
| `phase-cards/P2-design.md:14`「phase 保持 P2，不要提前写 P3」 | 卡片 | **本次处理**（与批 1 行为对齐，改述为「agate-next 亦不预写」） |
| `phase-cards/P8-release.md:15–20`（phase=P8，不提前写 DONE） | 卡片 | **本次处理**（批 0 已改卡片文字；批 1 复核一致性） |
| `UPGRADING.md:1209`「阶段卡片 phase 语义（文档，无强制）」 | 升级文档 | **本次处理**（批 1 起行为有强制，改述） |
| `state-machine.md:75/152`「phase 保持 P6 直至 P7」 | 状态机 | **不处理**——P6.5 是挂载子阶段，与 Pn→Pn+1 预写无关（不同机制） |

## 4. BDD 验收条件

> 编号全局唯一；每条独立可二值判定（PASS/FAIL）。P6 验收逐条对照。
> 括号内 Batch 标注该 BDD 归属的批次（供 P2/P8 分批推进）。

### 功能组：批 1 — 统一 phase 语义

#### BDD-1: agate-next 推进时不预写下一阶段 (Batch 1)
- Given 一个 `.state.yaml` 的 `phase: Pn`，且 `.state.yaml` **未被暂存**
- When 运行 `agate-next` 且 `check-gate.py Pn` 返回通过码（∈ `gate_pass_exit`）
- Then `agate-next` **不把** `Pn+1` 写入 `.state.yaml` 的 `phase` 字段，且 **不** `git add` `.state.yaml`

#### BDD-2: 不可绕开路径上的 phase 语义与卡片表述一致 (Batch 1)
- Given 批 1 落地后
- When 对 `agate-next.py` 与 `phase-cards/` 的 phase 语义表述做一致性扫描
- Then 全仓不再存在「agate-next 预写下一阶段」的行为代码，且卡片的「phase = 本 commit 产出阶段」
  表述与 `agate-next` 实际行为一致（无相悖描述）

### 功能组：批 2 — agate-config 声明层

#### BDD-3: 项目形态由声明文件描述，协议不写死技术栈 (Batch 2)
- Given 一个使用者项目，其形态（语言/包管理器/验证命令/发版方式等）与 agateon 不同（如 GitLab + Go + Helm）
- When 该项目用 `agate-config init` 生成声明文件并填写自身形态
- Then 协议的 gate / 推进 / 证据路径**读取该声明**决定行为，**不**再对「产品是 md」这一形态做硬编码假设

#### BDD-4: agate-config 子命令提供完整读写能力 (Batch 2)
- Given 已存在声明文件
- When 运行 `agate-config` 的读/校验/查询子命令
- Then 输出项目形态的客观值（可被脚本消费），且子命令退出码语义固定（0=成功，非 0=失败）

#### BDD-5: agate-config 声明 schema 校验拒绝非法形态 (Batch 2)
- Given 一份声明文件含非法字段名或非法枚举值
- When 运行 `agate-config validate`
- Then 返回非 0 并指出非法字段/值；合法声明返回 0

#### BDD-6: 唯一读取函数保证声明单源 (Batch 2)
- Given 声明文件与 schema 就位
- When 任意消费方读取某形态字段
- Then 全部消费方经**同一读取函数**取值（无第二个独立解析实现），且等价守护测试可验证「两处取值同源」

#### BDD-7: agate-setup / install-hook 自动 init 声明 (Batch 2)
- Given 一个尚未有声明文件的项目
- When 运行 `agate-setup`（或 `install-hook`）接入协议
- Then 自动生成（init）初始声明文件，且不覆盖既有声明（幂等）

#### BDD-8: 声明文件缺失时行为与现状一致且给 WARNING（迁移期） (Batch 2)
- Given 一个存量项目**没有**声明文件（未迁移）
- When 运行 gate_p0（调 `validate`）或任意消费声明的 gate 路径
- Then 行为与引入 `agate-config` **之前一致**，并输出显眼 WARNING（**不** exit 1），且 `UPGRADING.md`
  写明「到截止版本改 exit 1」及该截止版本号

### 功能组：批 3 — agate-run 执行层

#### BDD-9: agate-run 在不可绕开路径上执行项目命令 (Batch 3)
- Given 声明文件中定义了项目的验证命令
- When 主 Agent/Agent 需要执行验证命令
- Then 经 `agate-run` 执行（而非自由 `bash`），命令的退出码被如实传播（含 `pipefail` 语义）

#### BDD-10: agate-run 产出可比对的基线证据 (Batch 3)
- Given 首次执行某命令
- When 运行 `agate-run --baseline`
- Then 落盘 `.out` 证据文件；后续执行与之逐字节比对，差异被客观报出（可二值判定）

#### BDD-11: agate-run 证据文件被 ignore 检查覆盖 (Batch 3)
- Given `agate-run` 产出的 `.out` 证据位于项目内
- When 执行 ignore 检查
- Then 证据文件被 `.gitignore` 覆盖（`git check-ignore` 命中），否则报错

#### BDD-12: agate-run 写入 cmd_run 账本事件且不破坏哈希链 (Batch 3)
- Given `gate-events.jsonl` 是 append-only + `prev_hash` 链
- When `agate-run` 执行一次命令
- Then 追加一条 `cmd_run` 事件且 `prev_hash` 链连续（`check-events.py` 通过）；hook 一并暂存账本

#### BDD-13: check-obligations 完成登记面（SG.6 转绿） (Batch 6 落地，守护面在批 2 起适用)
- Given `check-obligations.py` 作为 `check-*.py` 已放入仓库
- When 跑 `check-protocol-consistency.py`（CHECK9-coverage）与
  `pytest test_protocol_alignment_review.py -k sg_6`
- Then **两者都无该脚本的未登记告警**（承载判定逻辑 → 锚点表；观测类 → 豁免集写理由）

### 功能组：批 4 — 关卡层分级

#### BDD-14: 关卡层按提交类型分级 (Batch 4)
- Given 一次提交属于某提交类型（如纯代码 / 纯文档 / 发版）
- When 关卡层判定该提交
- Then 按**提交类型**选择对应关卡集合（转换表可查），不同类型走不同关卡，且转换表含 `paused_from`

#### BDD-15: P8 为交付收尾且 delivery 必须声明 (Batch 4)
- Given 一个任务进入 P8
- When 运行 P8 gate
- Then P8 语义为**交付收尾**（非「发版」）；`delivery` 未声明时 gate 拦截（非 0），声明后放行

### 功能组：批 5 — CI 与诊断

#### BDD-16: agate-ci-verify 替换 ci-gate-backstop 且无假绿 (Batch 5)
- Given 一次 push / PR
- When 运行 `agate-ci-verify`
- Then 它**实际重跑** gate 判定（不再是永远 SKIP 却显示绿），无适用场景时显式声明「跳过 + 原因」
  （「跳过」与「通过」在输出上可区分）

#### BDD-17: agate-doctor 诊断项目接入状态 (Batch 5)
- Given 一个已接入/未接入的项目
- When 运行 `agate-doctor`
- Then 输出客观接入状态（声明文件、hook、版本解析、账本完整性等），并对异常项给出可执行的修复指引；
  成功退出码固定

### 功能组：批 6 — 义务登记表

#### BDD-18: obligations.yaml 登记 160 项义务的三态归宿 (Batch 6)
- Given 160 项阶段义务的逐条清单已入库（前置输入，见 §2 隐含需求 1 / §4 待确认）
- When 生成 `rules/obligations.yaml` 并运行 `check-obligations`
- Then 每项义务有明确三态归宿（脚本执行 M / 命令生成 C / 强制评审 R），且无「无归宿」项

#### BDD-19: 义务登记表 M 类占比不得下降 (Batch 6)
- Given 第 6 批落地后运行 `check-obligations` 或专门度量脚本
- When 计算 M 类（脚本强制）占比
- Then 该占比 **≥ 引入登记表时的基线值**（只增不减；下降即 FAIL）

#### BDD-20: 项目形态声明化不引入只适用于单一项目的规则 (Batch 2 起，每批 R6 差分)
- Given 每批的 R6 双向差分**除 agateon 外，在 `/tmp` 上再加一份 peekview 只读副本**
- When 对副本运行该批改动后的 consistency + 相关 gate
- Then 副本的**新转红/告警面全部可解释**（属于「本批有意收紧且已在设计登记」或「协议通用化结果」），
  并**无「只适用于 agateon 一个项目」的规则**引入

### 功能组：横切 — 迁移兼容与不回退

#### BDD-21: 第 4 批删除发版逻辑前先提供等价 preset (Batch 4)
- Given 第 4 批将删除协议里的发版逻辑
- When 提供 `preset: semver-changelog-tag`（把现有发版检查原样搬进声明）
- Then 使用者**一行声明即保持现状**；文件缺失时有发版痕迹（CHANGELOG / 版本文件 / `v*` tag）时给显眼
  WARNING；`UPGRADING.md` 写明迁移方式与截止版本

#### BDD-22: 每批遵守协议语义不回退 (各批)
- Given 本任务每批改动 `agate/` 协议本体与脚本（触发 SELF-GATE）
- When 每批合并前
- Then 已完成独立评审 + 提交信息含 `self-gate-review:` 留痕；pytest 全绿 + consistency 0 ERROR；
  义务 M 类占比（第 6 批起）不下降

## 5. 待确认清单

`[NO_NEED_CONFIRM]` —— **本阶段无阻塞性待确认项**。第 6 批的前置输入缺口（160 项逐条清单不在仓库）
已由 P0-brief §四与 dispatch-context 明确登记为「**须向评审索取该表并入库**」，且**不影响批 1–5 推进**
（批 6 在批 2 之后才启动，届时若表仍未入库则批 6 前置不足而阻塞）；故不构成本阶段 NEED_CONFIRM，
作为批 6 前置输入记录于 BDD-18 的 Given 与 §2 隐含需求 1。

`[SUGGEST: 批 6 的 160 项清单可先入库为只读参考文件（如 `docs/design-notes/` 下），
再据此起草 `rules/obligations.yaml`；理由：P0-brief §四已判定「没有就得重新盘点」，入库是唯一
经济路径]`

> 写法说明：本节不含阻塞性待确认标记；上面 `[NO_NEED_CONFIRM]` 是行首声明，`[SUGGEST]` 为倾向项
> （不阻塞，主 Agent 可自行采纳）。

## 6. 能力需求声明

```yaml
capability_requirements:
  - need: no-special-capability
    why: 本任务为纯协议/脚本改造，验证手段为本仓 pytest + consistency + git 命令 + /tmp 副本差分，
         不需要视觉、浏览器、外部网络等特殊 agent 能力
    available: []
    status: available
    note: 全部验证可由系统 python3 + pyyaml + git 完成（AGENTS.md 依赖清单），当前环境已具备
```

**无 GAP**。本任务缺的是「运行环境」（`/tmp` 副本差分需要的空间与 peekview 只读副本）——
属 `verification_env` 范畴，非能力三态（判断树见 analyst.md）。声明见下。

```yaml
verification_env: "本 checkout 内 pytest 全量 + consistency + 每批双向 R6 差分（在 /tmp 副本上跑）+ 一份 peekview 只读副本（同样在 /tmp）"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 dispatch-context 记录"
```

> **门槛声明**：`status` 无 GAP；`available` / `supplementable` 均不阻塞流程。

## 7. 裁剪说明

- **phases**: `[P1, P2, P3, P4, P5, P6, P7, P8]`——**不裁剪任何阶段**。
  理由：本任务 `risk_level: high`（改协议本体+状态机+关卡层，跨 6 批、触 SELF-GATE、破坏性变更面
  含「删除发版逻辑」），且为多批架构演进，P2 设计、P3 测试、P4 实现、P5/P6 验收、P7 一致性、
  P8 交付全部必需；`ceremony: standard`（不薄化）。
- **跳过风险**：无（不跳过）。
- **judge 启用**：本任务 `.state.yaml` 已写 `judge.enabled: true`（P0 建立时写入，见 `.state.yaml`）——
  满足 RM-AG0039 机制后新任务的强制要求，P1 gate 机械校验通过。
- **`implicit_coupling: true`**：本任务改动跨脚本与协议文档（消费方散布多处，如第 4 批删除发版逻辑
  的消费方），P7 不得裁剪。

## 8. 范围声明（机器字段，已写入 frontmatter）

- **packages**: `[agate-config, agate-run, agate-config-schema, gate-layer, agate-ci-verify, agate-doctor, obligations-registry]`
- **domains**: `[backend, cli, protocol]`（backend = 脚本/gate 逻辑；cli = 新增命令；protocol = 协议文档/规则/状态机）
- **risk_level**: `high`（决定 P2 评审强度 → 最高档）
