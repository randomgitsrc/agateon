---
phase: P2
task_id: TAG0050
parent: P2-design.md
trace_id: TAG0050-P2-20261006
created: '2026-10-07'
agent: cso
status: rejected
---
# TAG0050 P2 安全维度评审（cso）

- **评审对象**：`agate-workspace/tasks/TAG0050-task-data-contract/P2-design.md`（P2 形式化设计）。
- **上游依据**：`docs/design-notes/design-tag0050-task-data-contract.md`（r4 APPROVE WITH CHANGES）、`review-r4.md`、`review-tag0042-implementation.md`、`P1-requirements.md`（77 BDD）、`P0-brief.md`、项目 `AGENTS.md`。
- **基线**：本 checkout HEAD `adb0b11`（分支 `feat/TAG0050-task-data-contract`）；`origin/main` = `720c97d3`（v0.79.0）；协议稳定版 `~/.agate/v0.78.3`。
- **方法**：只读核验（`文件:行`）+ 独立最小复现（仓外 `mktemp -d`，用后即删）。未对真实仓库跑任何写副作用命令。
- **日期**：2026-10-07
- **角色口径**：本任务不是产品安全任务，评审对象是**协议安全门的正确性**——「谁能改判定依据」「可信锚点是否真的可信」「安全门会不会误判/漏判」。

---

## 0. 结论摘要

| 项 | 值 |
|---|---|
| **Status** | **rejected** |
| **最高严重级** | **BLOCKER（2）** |
| **问题数** | BLOCKER 2 / HIGH 0 / MEDIUM 4 / LOW 2 |
| **是否阻塞推进** | **是**（F4 安全门闭合机制自相矛盾；G3 账本信任链未裁决） |

两条 BLOCKER 均**不是**要推翻设计路线（契约等级 / 工具写入 / CI 回放），而是要补正**安全门的扫描面与模式规格**、并把已登记的账本信任链缺口**落进批次**。改动量小，但**不补正则实现会重现已知的 F4 漏拦**。

---

## 1. 重点核验项裁决（逐项对 dispatch 的 7 面）

### 1.1 生产接触安全门（设计 §4 / F4）—— **BLOCKER-1：闭合机制自相矛盾，双向误判未真正闭合**

**现状核验（只读，成立）**：`agate/scripts/pre-commit-gate.py:348` 的正则为 `^\s*-?\s*\[PROD_TOUCHED\]`（即 `markers.yaml` 的 `lead_variants.dash_only`）：
- 粗体 `**[PROD_TOUCHED]**`、引用块 `> [PROD_TOUCHED]`、`*`/`+` 列表写法**不命中**（F4 漏拦方向，成立）；
- `- [PROD_TOUCHED]: 无` **命中**（F4 误拦方向，成立）。
- 该扫描（2g.0）位于 `for state_file in staged_all … .state.yaml` 主循环内（`pre-commit-gate.py:226-232`）⇒ 只改产出、不暂存 `.state.yaml` 的提交**完全不扫**（M-R4-1，成立）。

**设计给出的闭合**：§2.3 规则 7（扫描面扩到「每个有暂存文件的任务目录」）+ §4（`prod_touched` 必填字段 + 「T4 优先」）+ BDD-54/55。

**裁决：不成立。** 两条独立缺陷：

1. **T4 无法交付 BDD-54 声明的行为（机制归因错误）。** 设计 §3.6 明确「**T4 = 现有的 PROD_TOUCHED diff 扫描，保持原样**」；§0 F4 已实测该正则不认粗体。而 §4 与 BDD-54 却要求「粗体 `**[PROD_TOUCHED]**` + 字段 false → 中止（**T4 优先于字段**）」。**「保持原样」的 T4 与「必须命中粗体」的 BDD-54 直接矛盾**——照 §3.6 实现，粗体不会被 T4 拦下。
2. **真正能命中粗体的是 T1，但其扫描面比 T4 更窄。** §3.6 的 T1 用 `markers.yaml` 的 `default` 口径（`lead: '^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?'`，**认粗体/引用块**），但它「扫描**声明文件**的正文」。§6 的 `declaration_files` 只含「各阶段主产出、`*-review.md`、`P4-implementation-*.md`、`P4-implementation/**/*.md`」——**不含 `P*-progress.md`**。而 F4 的真实样例恰恰是 progress 文件（peekview `T039…/P4-progress.md:21`）。⇒ 在 progress 等非声明文件中写粗体/引用块形态的**正向** `[PROD_TOUCHED]`，T4（dash_only）与 T1（仅声明文件）**都不拦**。

**残留绕过（可复现推理，非臆测）**：任务触及生产 → 主产出 `prod_touched: false`（谎报）→ 在 `P4-progress.md` 写 `**[PROD_TOUCHED] db write`。T4 不认粗体、T1 不扫 progress ⇒ 提交放行。这正是 F4 漏拦方向的**未闭合子集**。

**附带不一致**：`markers.yaml` 把 `PROD_TOUCHED` 登记为 `lead_variant: dash_only`（与安全门对齐），而 T1 又要求「只用 `default` 口径」——**注册表单源与 T1 口径分叉**，违反 §1 原则 5「一个事实只有一个源」。

**修复要求（供 architect 落实）**：
- 明确**安全门的扫描面 = 每个有暂存文件的任务目录内的全部暂存文件**（不止声明文件），**模式 = `markers.yaml` 的 `default` 口径**（或显式写明「T4 升级为 default 口径」，不再写「保持原样」）；
- 补锚：**非声明文件（如 `P*-progress.md`）中的粗体/引用块正向 PROD_TOUCHED + 字段 false → 中止**（现 BDD-54 未覆盖该面）；
- 调和 T1「default 口径」与 `PROD_TOUCHED` 的 `dash_only` 登记——二者取一为单源。

### 1.2 可信锚点（设计 §2.4）—— **成立**，附 2 条 MEDIUM

逐条回答 dispatch 的四问：

- **① 回放协议版本选择是否足以防「PR 顺手削弱判定」？** 基本成立。逐提交读 C 树 `.agate-version` + **不低于 merge-base**（降级 FAIL）+ 否则 fail-closed（设计 §2.4 优先级 ①②③、BDD-31/32/33）⇒ PR 无法把版本钉回旧规则；agateon 走 merge-base 的 `agate/`（固定），不受 PR 影响。**残留（MEDIUM 级认知边界，非缺陷）**：版本号单调 ≠ 规则单调（理论上新版可削弱某条规则），该缺口由 §2.4 边界「PR 同改协议本体/workflow → 交 SELF-GATE 人工评审」承接，属如实声明。
- **② `--no-verify` 违规提交会被回放抓到？** 成立，**且依赖 §2.3 规则 7 先落地**。R4 实测：暂存 `.state.yaml` 的 PROD_TOUCHED 提交 rc=1、commit-msg 缺 trailer FAIL、删除账本 FAIL；M-R4-1 的「READY 后只改产出」缺口由规则 7 + A2 锚 ② 补上（依赖链 A0→A1→A2 正确）。§2.4 已如实写明「回放强度 = hook 强度」。
- **③ 边界是否如实声明并交 SELF-GATE？** **是**。§1 与 §2.4 两处写明「CI 判不了新规则是否合理，只能靠 SELF-GATE 人工评审，回放 commit-msg 只保证留痕」。诚实。
- **④ `gate-backstop` 设 required 需用户许可（G6）是否登记为阻塞项？** **登记了但未定性为安全属性的硬前提**——见 §1.6 MEDIUM-2。

### 1.3 账本完整性（设计 §2.3 七规则 / G3）—— **BLOCKER-2：G3 未裁决，信任链前提未证实**

**七规则本身**（只追加 / 不可删 / 事件规则 / legacy 不可重开 / 每有暂存文件的任务目录都检查）设计合理，且 `--no-verify` 跳过本地的缺口由 §2.4 CI 回放 + CI 端 base..HEAD 账本终检兜底——**阻断型判据**（规则 1/4/6/7 与事件规则）在 CI 端独立重演，**不依赖账本是否入库**，故**不构成对强制力的绕过**。

**但 G3（RM-AG0100）直接冲击「事件随提交入库」这一 §2.7/§2.3 的信任链前提**：

- 设计 §2.7 断言「2h.1c/d 使进入 PAUSED/READY/DONE 的转换**随本次提交入库**」；P2 §1.1 A3 行亦如此。
- **RM-AG0100**（`agate-workspace/roadmap/roadmap.md:99`）实测：`pre-commit-gate.py:428-429` 的 `run_git(["add", …/gate-events.jsonl])` 在**真实 `git commit`** 中不生效 → 账本永久滞后一次提交。
- **P2 §10 G3 只登记、未裁决**（「交 P2 评审裁决：纳入 A1/A3 或明确排除」）⇒ 设计**当前没有任何批次承接**该缺口。

**独立复现（本评审，仓外 `mktemp -d`，git 2.43.0）**：最小仓库中令 pre-commit hook「追加 tracked 文件 + `git add`」，三种场景——普通提交、**新建空文件同提交**、**路径限定 `git commit -- <path>`**——committed 内容**均含** hook 追加行。⇒ **RM-AG0100 的根因假设（`git commit` 持 `index.lock` / 临时索引致 hook 的 `git add` 被吞）在我的最小复现下不成立**。该 symptom 或为探针环境特有（如路径/`GIT_INDEX_FILE`/探针测法），或根因判断有误——**须重新实测**，设计不应建立在一个未证实的根因上。

**裁决**：G3 **确实削弱**「事件随提交入库」信任链，且**未分配批次 = 设计未闭合**。后果：
- 账本审计链（`gate_run` / `state_transition` / `prod_touched_in_paused`）可能系统性缺行；
- 证据链 `cmd_run` 事件（含 `sha256`）可能不入库 → **D3 的 sha256 绑定在干净克隆下失效**（F9 未完全闭合，见 §1.7）；
- §2.7「`created`/`updated` 取账本尾行 ts 现算」依赖事件齐全，事件缺失则现算值失真。

**修复要求**：**纳入 A1**（与账本七规则同域），新增锚「**真实 `git commit` 后 committed ledger 含本 hook 追加的事件**」（= RM-AG0100 自身建议的锚），并让 2h.1d 的 `git add` **失败可见**（不再静默）；同时**重新实测根因**后再定 §2.7 措辞。

### 1.4 判定依据不可被改写（设计 §1 原则 / §2.5）—— **通过**，附 1 条残留

- **F3b（`judge.enabled`）**：现状核验 `check-gate.py:756` 读 `judge.get("enabled")`、`pre-commit-gate.py:157 _judge_enabled`、`agate-next.py:274`——设计 §2.5 改为 `requirement_active`（契约 `requires`），BDD-09 覆盖 ⇒ **消除**。
- **F3a（P1 `created` 日期门槛）**：现状核验 `check-gate.py:767` 按 `created ≥ judge_required_since`（`dispatch.yaml:17`）——§2.6 改为创建事件 `ts`，BDD-08 ⇒ **消除**。
- **F3c（evidence_ref 日期门槛）**：现状核验 `agate_common.py:1707 is_new_task_for_evidence_ref` 依 `created` 且 fail-open——§2.5 改 `requirement_active`，BDD-10 ⇒ **消除**。
- **F2（P7 汇总盖 BLOCKER）**：`blocker_count` 改系统字段现算，BDD-61 ⇒ **消除**。
- **F1（P6 自报 pass/fail）**：`results` 结构化 + D1/D2，BDD-56 ⇒ **消除**。
- **残留（可接受，已在设计边界内）**：`prod_touched`（agent 声明）仍可谎报，靠 T4 兜底——**而 T4 正是 BLOCKER-1 的缺陷点**；契约等级由账本事件推导，低等级伪造由规则 2 + BDD-07 + A2 锚 ④⑤ 拦下，`--upgrade` 只升不降，账本前缀防删行 ⇒ **无残留「agent 可改的值决定强制力」**。

### 1.5 结构化 vs 伪造边界（设计 §1 边界）—— **成立**，附 1 条 LOW

§1 边界写明「结构化只消除解析歧义与漏写，防不了故意伪造；本地账本无密钥；可信锚点在 CI 回放；CI 也判不了新规则是否合理，只能靠 SELF-GATE，CI 只保证评审留痕」。**诚实**，与 §2.4 分工清晰（§1 定原则、§2.4 定实现）。**LOW-1**：措辞「CI 能保证这次评审确实留了痕」略强——SELF-GATE trailer 仅 **WARNING 不拦截**，且未设 required 时连该痕迹都不校验；宜写明「**在 gate-backstop required 生效时**」。

### 1.6 权限 / 许可面 —— 附 1 条 MEDIUM

- **CI required（`gate-backstop`）**：P2 §10 G6 + §8 `env_constraints.ci_required_permission` 已登记「需用户明确许可；未取得则只落地 workflow、不设 required」。**问题（MEDIUM-2）**：未把它定性为**可信锚点强制力的硬前提**——若未设 required，CI 回放**仅为建议**（PR 可带 FAIL 合并），设计宣称的「可信锚点」**不成立**。建议在 §2.4/`env_constraints` 显式声明「**security property conditional on `gate-backstop` required**」，并写明未许可时的降级语义（回放为 advisory，非锚点）。
- **peekview 新增 job / `.agate-version`**：设计 §12「不改 peekview」，仅在 `UPGRADING` 给指引；P2 §1.2 一致。**越界检查：无**（本任务只改 agateon 本仓）。但**peekview 作为真实使用者，其锚点未被任何 BDD 验证**（BDD 只测 agateon）——属范围外，已如实声明。
- **agateon 写 `.agate-version`**：P1 §5 记为 SUGGEST（非阻塞）；未写则走优先级② merge-base 协议，与开发者本机稳定版可能有差（R5 已登记）。登记完整。

### 1.7 证据链（设计 §5 / RM-AG0097 / F9）—— 附 1 条 MEDIUM + 1 条 LOW

- **正向**：`resolve_evidence_ref` 唯一入口 + `run:<k>` + `cmd_run` 事件记 `sha256` + `gitignore-fragment.txt` 取反（`!.../P6-evidence/**`、`!.../runs/**`）+ D3「解析到非空、未被 ignore、pre-commit 中还须已跟踪/已暂存」。F9 的「证据存在只在作者本机成立」在**方向**上被 D3 兜住。
- **MEDIUM-4**：**D3 的 sha256 校验在 `cmd_run` 事件缺失时的行为未定义**。叠加 G3，`cmd_run` 事件可能不入库 ⇒ 干净克隆/换机下无 `sha256` 参照。若此时 D3 **跳过**（fail-open）→ 可绕过证据完整性校验；若 **FAIL**（fail-closed）→ 合法证据被误拦。设计必须**显式规定**（建议 fail-closed，并区分「事件缺失」与「sha256 不匹配」两类错误）。
- **LOW-2**：§5.4 只提示「取反规则必须写在 `*.log` 之后」，未提示 Git 的**父目录排除限制**（「若父目录被排除，`!` 无法重新包含其下文件」）——`agate-workspace/` 或 `tasks/` 被整体 ignore 的项目，取反失效。宜补一句约束。

---

## 2. STRIDE 矩阵

| STRIDE | 威胁（本任务判定面） | 设计对策 | 裁决 |
|---|---|---|---|
| **S**poofing | 伪造 `agent` 身份 / 伪造「评审已做」 | `agent` 工具拒写（G7）；`agent ≠ main` 校验；SELF-GATE trailer | 成立（`agent` 可手改，属 §1 已声明边界） |
| **T**ampering | 改写账本（amend/reset）、改快照、降级协议版本、换证据 | CI 逐提交回放；快照 sha256 冻结 CHECK；`.agate-version` 单调不降；D3 sha256 | **部分**：CI 锚成立；**账本事件入库链受 G3 冲击（BLOCKER-2）** |
| **R**epudiation | PAUSED 生产接触无留痕 / phase 转换无记录 | F8 修复（BDD-01）；2h.1c/d 前移 | **部分**：F8 修复真实；但 **PAUSED 事件在 2g 分支内、位于 2h.1d 之后，不会被 `git add`（MEDIUM-3）**，叠加 G3 更甚 |
| **I**nfo disclosure | 证据/日志泄露敏感信息入库 | 证据入库取反 + `prod_touched_detail` | 未评估（范围外；PROD_TOUCHED 描述入库的敏感性未讨论，LOW） |
| **D**oS | CI 回放耗时 / fail-closed 误拦全仓 | E4 耗时实测（~15s）；清晰升级提示 | 成立 |
| **E**levation | 用低等级绕开强制 / legacy 重开 / 手改判定依据 | 规则 2/4/6；BDD-07；A2 锚 ④⑤；§2.5/§2.6 现算 | 成立 |

---

## 3. 独立验证证据（只读核验 + 最小复现）

**A. 只读核验（本 checkout，`文件:行`）**

| 声明 | 核验结果 |
|---|---|
| F4 正则 `^\s*-?\s*\[PROD_TOUCHED\]` | `pre-commit-gate.py:348` 确认；`markers.yaml` `lead_variants.dash_only` 同构 |
| 2g.0 只在暂存 `.state.yaml` 的任务上跑 | `pre-commit-gate.py:226-232`（`for state_file in …`）确认 |
| F8：`append_event` 3 参 vs 2 参 | `pre-commit-gate.py:370` 传 3 参；`agate_common.py:524 def append_event(task_dir, event)` 2 参确认；`except Exception` 静默吞 |
| F3a：`judge_required_since` 依 `created` | `check-gate.py:756-767` + `dispatch.yaml:17` 确认 |
| F3c：evidence_ref 依 `created` 且 fail-open | `agate_common.py:1707 is_new_task_for_evidence_ref` 确认 |
| F12：`delivery` 子串判定 | `check-gate.py:1450 "delivery:" not in p8_text` 确认 |
| RM-AG0085：骨架子串判定 | `check-gate.py:964 "## 骨架声明" not in _read_text(...)` 确认 |
| F15b / G1：不存在目录 rc 随 phase | `check-gate.py:1618-1632 main()` 无存在性检查；`gate_p7`（`:1246`）对不存在目录读到空值 → `count_p7_markers`=(0,0) → 返回 0（假 PASS）确认 |
| F15a：多任务恒 SKIP | `agate-ci-verify.py:95-104`（>1 个 `.state.yaml` → `ambiguous` → `_skip`）确认；`:126` 按 `task_id` 拼路径确认 |
| F13：义务 M 自标 | `check-obligations.py:85-146` 只查 disposition/anchor/statement 非空 + M 占比不降确认 |
| `markers.yaml` T1 vs 注册表 | `lead`（认粗体/引用块）与 `PROD_TOUCHED: lead_variant: dash_only` 并存确认（BLOCKER-1 的注册表分叉） |
| G3 | `agate-workspace/roadmap/roadmap.md:99` RM-AG0100 存在，P2 §10 G3 未裁决确认 |

**B. 最小复现（仓外 `mktemp -d`，用后即删）**

- **目的**：验证 RM-AG0100 的根因假设「`git commit` 持索引锁 / 临时索引 ⇒ hook 的 `git add` 不生效」。
- **环境**：git 2.43.0；三个场景：① tracked 文件追加；② 同提交新建空文件；③ 路径限定 `git commit -- <path>`。
- **结果**：三场景 committed 内容**均含** hook 追加行；`git status --porcelain` 为空。
- **结论**：该根因假设**未被复现**。RM-AG0100 的 symptom 若属实，根因另有其因（探针路径/`GIT_INDEX_FILE`/测法），**须在真实 hook 上重新实测**——设计不应据未证实的根因作推断。
- **清理**：`trap 'rm -rf "$T"' EXIT`；真实仓库未触碰（见 §5）。

---

## 4. 修复建议（按优先级）

| # | 级别 | 建议 | 去向 |
|---|---|---|---|
| BLOCKER-1 | **BLOCKER** | 明确安全门扫描面=任务目录内**全部暂存文件**、模式=`markers.yaml` **default 口径**（或显式升级 T4，删「保持原样」）；补锚「**非声明文件**中的粗体/引用块正向 PROD_TOUCHED + 字段 false → 中止」；调和 T1「default」与 `PROD_TOUCHED: dash_only` 的注册表分叉 | §3.6/§4 + BDD-54；architect 补 P2-design |
| BLOCKER-2 | **BLOCKER** | G3 **纳入 A1**，补锚「真实 `git commit` 后 committed ledger 含本 hook 追加事件」；2h.1d `git add` 失败**可见**；**重新实测根因**后再定 §2.7 措辞 | §10 G3 裁决 + §1.1 A1 行 + §2.7 |
| MEDIUM-1 | MEDIUM | BDD-55 措辞修正：`[PROD_TOUCHED]: 无` 仍会被 T1（default）命中 → ERROR → **仍阻断**；写明这是「正文不再承载标记」的有意取舍，并确认 F4 误拦样例在 R6 差分第 12 项**单独统计** | §4/§3.6 + BDD-55 + §8 第 12 项 |
| MEDIUM-2 | MEDIUM | 显式声明「可信锚点强制力 conditional on `gate-backstop` required」及未许可时的降级语义 | §2.4/§8 `env_constraints` + G6 |
| MEDIUM-3 | MEDIUM | BDD-01 增加「**committed ledger 含** `prod_touched_in_paused`」断言；核对 2h.1d 前移后 PAUSED 追加事件的暂存顺序（现 2g 分支内、2h.1d 之后） | §2.7 + BDD-01 |
| MEDIUM-4 | MEDIUM | 规定 D3 在 `cmd_run` 事件缺失时的行为（建议 fail-closed，区分「事件缺失」/「sha256 不匹配」） | §5.1 D3 |
| LOW-1 | LOW | §1 边界「CI 能保证留痕」改为「在 required 生效时」 | §1 |
| LOW-2 | LOW | 补 Git 父目录排除限制（`!` 无法在被排除的父目录下重包含） | §5.4 |

---

## 5. 环境隔离声明

本评审仅在 agateon 本 checkout 与仓外 `mktemp -d` 副本上做只读核验与最小复现（用后即删）；未对真实仓库执行任何破坏性/写仓命令；未接触生产环境。核验后真实仓库工作树未被本评审改动。

[PROD_NOT_TOUCHED]
