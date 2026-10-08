---
phase: P8
task_id: TAG0050
type: release
parent: P7-consistency.md
trace_id: TAG0050-P8-20261009
status: draft
created: '2026-10-09'
agent: implementer
bump_type: minor
debt_check: reviewed
delivery: PR 普通 merge（--no-ff，禁止 squash）+ tag v0.80.0 + GitHub Release（release.yml 自动构建；先合 PR、后打 tag）
---

# P8-release.md — TAG0050 任务数据契约：结构化判定、可信写入与任务版本 发布准备声明

> releaser subagent（implementer P8 模式）产出。**未执行 `bump-version` / `git commit` /
> `git tag`**——这些由主 Agent 在 P8 gate 验证通过后亲自执行。
> **本轮只读 + 只写本文件**：未改 `README.md` badge / `CHANGELOG.md` / `agate/UPGRADING.md` /
> `agate-workspace/roadmap/roadmap.md` / `.state.yaml`（归并方案见 §3/§4/§6，均由主 Agent 执行）。
> 状态标记：`[PROD_NOT_TOUCHED]`（本任务全程只在 agateon 本 checkout 与只读副本上工作，未接触生产环境）。

## 0. 上游与基线

- **HEAD**：`4e7ea04c`（P7 已提交）；分支 `feat/TAG0050-task-data-contract`；`merge-base HEAD origin/main` = `720c97d3`（v0.79.0）。
- **上游结论**：P6 `77/77 PASS`；P6.5 judge `77/77`（轮次 2/2）；P7 `blocker 0 / DESIGN_GAP 15-15 / CODE-MAP 16-16`。
- **性质**：协议内核演进（10 批 A0/A1/A2/A3/A4/B/C/D/E/F），**对 legacy 任务退出码与 ERROR 集合不变**（R6 差分 0 差异，见 §5）。
- **P2 packages 实测 = 8 项**：`agate-scripts` / `agate-rules` / `agate-task-data` / `agate-cards` /
  `agate-roles` / `agate-tests` / `ci-workflows` / `docs-upgrading`（`P2-design.md` frontmatter，
  与 `P1-requirements.md` 逐字一致）。
  ⚠️ **派发指引记「6 个」，实测为 8 项**（与 `P7-consistency.md` §3.1 的同一处口径差异一致）——
  **以实测 8 项为准**（本文件按 8 项逐包核对；P7 已记录该差异，非新问题）。

## 1. 版本号变更确认

**bump_type: minor（v0.79.0 → v0.80.0）**

依据（对照 `agate/UPGRADING.md` 既有版本语义与发布惯例）：

1. **向后兼容的功能新增**：新增工具 `agate-task-init` / `agate-state-set` / `agate_schema.py`、
   冻结契约快照 `rules/task-data/level-1.yaml`（+ `LEVELS.yaml`）、CI 逐提交回放、
   `agate-md-field-set` 7 操作、`agate-config set/unset/explain`、P6 `results`（D1–D10）/ P6.5
   `criteria` / P7 成对声明 / P8 `delivery` 结构化 / `reviewed_bdds` 等结构化判据——均为**纯增量能力**。
2. **无破坏性变更**：`UPGRADING.md` 各批节均标注「**无破坏性变更**」；`.state.yaml` schema、
   `gate-events.jsonl` 事件结构、既有任务数据格式均未变；新判据**只对非 legacy 任务**生效，
   存量（legacy）任务不受影响、无需迁移（P0-brief「明确不做」/设计 §8 承诺）。
3. 当前发布版 **v0.79.0**（README badge `version-v0.79.0` + CHANGELOG 顶部 `## [0.79.0] - 2026-10-06`
   已核）→ 目标 **v0.80.0**（minor 位 +1）。
4. 本仓为**单一版本号仓库**（agateon 整体一次 bump）：`P2§packages` 的 8 个包是**任务改动分域**，
   **不各自独立版本号**（同 TAG0042 惯例）。

| 位置 | 文件 | 变更 | 本轮状态 |
|---|---|---|---|
| version badge（EN） | `README.md` L12 | `version-v0.79.0` → `version-v0.80.0` | **待主 Agent 改** |
| CHANGELOG | `CHANGELOG.md` | `## [Unreleased]` 下新增 `## [0.80.0] - <发布日期>` 段 | **待主 Agent 改**（方案见 §3） |
| UPGRADING | `agate/UPGRADING.md` | 4 个「未发布 — TAG0050 批 …」节归并为 `### v0.80.0` 节 | **待主 Agent 改**（方案见 §4） |

- **版本文件路径**：本仓无独立 version 文件；**版本权威面 = `README.md` 的 version badge**（CHECK 7
  口径）＋ `CHANGELOG.md` 最新已发布版本节（CHECK 7 与 CHECK 13 同源）。
- **只读确认命令**（主 Agent bump 后自查）：
  - `grep -n 'badge/version' README.md` → 须为 `version-v0.80.0`
  - `grep -nE '^## \[' CHANGELOG.md | head -2` → 第一条 `## [Unreleased]`（空），第二条 `## [0.80.0] - <日期>`
  - `grep -n '^### v0.80.0' agate/UPGRADING.md` → 命中（CHECK 13 所必需）
- ⚠️ **README.zh-CN.md badge 仍为 `v0.78.0`**（v0.78.1–v0.79.0 亦未同步，属既有状态）——`CHECK 7`
  只读 `README.md`，**不构成一致性缺口**，非本次引入的回归，**本轮不动**（与 TAG0042 P8 同款处置）。

> ⚠️ **须主 Agent 裁决的版本语义冲突（见 §8 已知偏离 D-4）**：`CHANGELOG.md`（v0.79.0 节，TAG0042）
> 预告「**迁移截止版本 v0.80.0**：`agate.config.yaml` 缺失/非法自 v0.80.0 起 `exit 1` 硬拦截」，
> 但该硬切**本任务未实现**（`agate/scripts/` 无 `0.80.0` 引用，`gate_p0` 仍为「迁移期 WARNING」）。
> 若本次按 v0.80.0 发布，该预告将不兑现——**发布前须由主 Agent 决定**：① 接受 deadline 顺延并
> 同步改述该预告；或 ② 本次改用其他版本号。本文件按惯例仍建议 **minor → v0.80.0**。

## 2. CHANGELOG 归并方案（`[Unreleased]` → `[0.80.0]`）

**方案（保留空 `[Unreleased]` + 在其下插入版本节，不改名 `[Unreleased]`）**：

1. 保留顶部 `## [Unreleased]`（置空），其下插入 `## [0.80.0] - <发布日期>`（比照 v0.78.x/v0.79.0 的插入位置）。
2. 把当前 `[Unreleased]` 的全部条目迁入 `## [0.80.0]` 节。当前 `[Unreleased]` 内容（已核）：
   - **### 新增**：TAG0050 批 D/E/F（P6 `results` D1–D10 / P6.5 `criteria` / `resolve_evidence_ref` /
     P7 成对声明 / `reviewed_bdds` / P2 `ui_design` / 骨架标题级判定 / P8 `delivery` 结构化 /
     `check-pruning` 恒检 / T2 绊线 / 快照 `declaration_files` glob 面统一 等）。
   - **义务基线一次性重设**（见下）。
3. **本版本条目须含 task_id `TAG0050`**（`check-changelog.py` 关键词口径）。
4. ⚠️ 归并时**建议补齐批 G1（A2 CI 回放 + A3 `agate-state-set`）、批 G2（B 写入工具与契约单源 +
   C 生产接触）、批 D 前置 hotfix（`agate-run` 基线比对）的 CHANGELOG 条目**——当前 `[Unreleased]`
   的 `### 新增` 只显式覆盖「批 D/E/F」，而 `UPGRADING.md` 已有 4 个批次节（G1/G2/hotfix/D-E-F）；
   为免「CHANGELOG ↔ UPGRADING 覆盖不对齐」，主 Agent 归并时**逐批补条目**（措辞可复用
   `UPGRADING.md` 对应节，见 §4 表）。

### 2.1 义务基线一次性重设声明（P1 §10 / BDD-76）

- **已在 `[Unreleased]` 落地**（已核，`CHANGELOG.md` L30–32）：
  `baseline.reset: {from: "60/123", to: "56/119"}`（`rules/obligations.yaml`），此后恢复「只增不减」。
- **归并动作**：该条目随 `[Unreleased]` 一并迁入 `## [0.80.0]` 节，**内容不变**；措辞须保留
  「**一次性**重设、非质量倒退」语义（否则会被误读为质量倒退，P1 §10）。
- 自查：`grep -c 'baseline.reset' CHANGELOG.md` ≥ 1；`grep -c 'TAG0050' CHANGELOG.md` ≥ 1。

## 3. UPGRADING 归并方案（4 个「未发布」节 → `### v0.80.0`）

当前 `agate/UPGRADING.md` §3 已有 **4 个 TAG0050「未发布」节**（均标注「无破坏性变更」）：

| # | 现有标题（行号） | 覆盖批次 |
|---|---|---|
| 1 | `### 未发布 — TAG0050 批 G1：CI 逐提交回放（A2）+ state-set（A3）`（L279） | A2、A3 |
| 2 | `### 未发布 — TAG0050 批 G2：写入工具与契约单源（B）+ 生产接触（C）`（L360） | B、C |
| 3 | `### 未发布 — TAG0050 批 D 前置 hotfix：agate-run 基线比对`（L393） | hotfix(I-2) |
| 4 | `### 未发布 — TAG0050 批 D/E/F：结构化判定与成对声明`（L403） | D、E、F |

**归并方案（推荐：单版本节 + 批小节）**：

1. 把 4 个 `### 未发布 — TAG0050 批 …` 标题**归并为一个** `### v0.80.0 — TAG0050 任务数据契约：
   结构化判定、可信写入与任务版本（**无破坏性变更**）`；原 4 个批标题降级为节内**加粗小节**
   （`**批 G1（A2+A3）…**` / `**批 G2（B+C）…**` / **批 D 前置 hotfix…** / `**批 D/E/F…**`），
   正文内容不动（与 TAG0042 `### v0.79.0` 的单节多小节惯例一致）。
2. 备选（最小改动）：仅把 4 处 `未发布` 字样改为 `v0.80.0`（得 4 个 `### v0.80.0 — TAG0050 批 X`
   标题）。**两方案均满足 CHECK 13**（只要求存在 `^### v0.80.0\b` 标题）；推荐方案 1（结构更清晰）。
3. **不得**把 `[Unreleased]` 直接改名（见 §2）；**不改历史版本节**（`### v0.79.0` 及更早）。
4. 自查：`grep -n '^### v0.80.0' agate/UPGRADING.md` → 命中；`grep -c '未发布 — TAG0050' agate/UPGRADING.md` → **0**。

## 4. 逐包发布检查命令 + 实跑 exit code

> 单版本号仓库：8 个包为**改动分域**，发布检查命令按「该包所在验证面」逐包列出。
> 命令均取自 `P2-design.md §6 gate_commands`，**本轮 releaser 在 HEAD `4e7ea04c` 实跑**
> （`check-protocol-consistency.py` 用**本 checkout 自己的**；其余为协议无关脚本）。

| # | 包（package） | 发布检查命令 | 实跑 exit | 摘要 |
|---|---|---|---|---|
| 1 | `agate-scripts` | `~/.venvs/agate-dev/bin/ruff check agate/` | **0** | All checks passed |
| 1 | `agate-scripts` | `python3 agate/scripts/check-platform-assumptions.py` | **0** | 0 命中 |
| 1 | `agate-scripts` | `python3 agate/scripts/check-structure-consistency.py` | **0** | S0–S6 OK |
| 2 | `agate-rules` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0** | 0 ERROR / 410 WARNING（全冻结面） |
| 2 | `agate-rules` | `python3 -m pytest agate/tests/ -k task_data_freeze -q` | **0** | 1 passed（快照冻结 CHECK + 黄金 fixture） |
| 3 | `agate-task-data` | `python3 -m pytest agate/tests/ -k task_data_golden -q` | **0** | 1 passed（每级黄金 fixture 回归） |
| 3 | `agate-task-data` | `python3 -m pytest agate/tests/ -k task_data_freeze -q` | **0** | 1 passed |
| 4 | `agate-cards` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0** | 卡片 CHECK 覆盖（0 ERROR） |
| 5 | `agate-roles` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0** | 角色卡 CHECK 覆盖（0 ERROR） |
| 6 | `agate-tests` | `bash agate/tests/scripts/count-tests.sh` | **0** | 2866 用例（≥ 749 下界） |
| 6 | `agate-tests` | `python3 -m pytest agate/tests/ -k schema_single_source -q` | **0** | 1 passed（schema 单实现守护） |
| 7 | `ci-workflows` | `shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh` | **0** | 0 error |
| 7 | `ci-workflows` | `python3 agate/scripts/check-structure-consistency.py` | **0** | S0–S6 OK |
| 8 | `docs-upgrading` | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0** | 含 CHECK 13（`v0.80.0` 节就位后） |
| — | **跨包（R6 兼容承诺）** | `bash docs/design-notes/r6-differential.sh --corpus .` | **1 / 0** | 见下 |

**R6 差分（§8 兼容承诺的可执行判据）——两跑如实记录**：

- `--corpus .`（活 checkout）→ **exit 1**，原因 = 脚本的**原仓库干净自核验拦截**
  （P8 阶段工作树必然含未提交任务产物：`.state.yaml` / `gate-events.jsonl` / `P8-dispatch-context-implementer.md`），
  **非差异违规**（P5 阶段同款现象，见 `P5-test-results/unit.md`）。
- 在**干净 clone 副本**上（`git clone --no-hardlinks . <tmp>`，`--before 720c97d3 --after 本 checkout/agate`）
  → **exit 0**：`legacy 任务 39 个，差异 0 条，未匹配 0 条`。跑完核验**真实仓库 `git status` 未新增脏项**。
- ⇒ **§8「legacy 退出码与 ERROR 集合不变」成立**；主 Agent 提交 P8 产出后可直接用 `--corpus .` 复跑确认（预期 0）。

**小结：8 个包的发布检查命令全部 exit 0**（R6 在干净副本上 exit 0；活树 exit 1 仅为自核验拦截，非内容违规）。

## 5. roadmap 回写核对（只核对，不修改）

反查 `agate-workspace/roadmap/roadmap.md`「关联任务」列（第 5 数据列 = `TAG0050`）的行：

| RM 条目 | 状态（实测） | 关联任务列 | 结论 / 主 Agent 动作 |
|---|---|---|---|
| **RM-AG0099**（本任务登记） | `scheduled` | `TAG0050` | **须回写 `done`**（RM-AG0043 硬校验；否则 `gate_p8` 阻断） |
| **RM-AG0101**（BDD-3 扫描排除卡片块，并入 A3） | `scheduled（并入 TAG0050 批 A3…）` | `TAG0050` | **须回写 `done`**——A3 **已交付**该修复（`check-state-transition.py` 现剔除 `AGATE_CARD` 块 + 两向回归用例，见 `P4-implementation-G1.md` §「RM-AG0101」）。关联任务列含 `TAG0050` ⇒ **同样触发 RM-AG0043 硬校验**，不回写则 `gate_p8` 阻断 |
| **RM-AG0100**（hook 账本 `git add` 误诊） | `done（误诊关闭）` | `—` | **正确**：已关闭（误诊），关联任务列为 `—` ⇒ 不触发本任务 gate。无需动作 |

> **机械核对（本轮只读实跑）**：按 `_check_roadmap_done` 同款解析（`|` 分列、列数=9、`关联任务==TAG0050`），
> 命中 **RM-AG0099（scheduled）与 RM-AG0101（scheduled）两行非 done**。⚠️ 另实测 **RM-AG0098 行 11 列**
> （单元格含字面 `|`，已知长期隐形，见 `check-gate.py` DEBT0019 注释），其关联任务列为 `—`，**不影响本任务**。
> ⇒ **主 Agent 须把 RM-AG0099 与 RM-AG0101 一并回写 `done`**（二者关联任务列均含 `TAG0050`）。

## 6. debt_check（reviewed）

**debt_check: reviewed**。已读 `agate-workspace/debt/tech-debt.md`（共 50 条，11 条 open）。与本任务改动面相关条目：

| DEBT id | 标题（摘） | status | 本轮核对 |
|---|---|---|---|
| DEBT0025 | 新增 CHECK 上线前未先全量扫描存量命中（CHECK 14/15 首跑 3 ERROR） | `closed` | 本任务遵循 AGENTS.md 工作流第 0 步；新增 CHECK（快照冻结/黄金 fixture）已全量扫描，无新 ERROR |
| DEBT0040 | append-only 账本写入测试无 tmp 隔离强制（写进仓库账本污染） | `closed` | 本任务测试用 `tmp_path`/`init_task()`，未污染仓库账本（`check-ledger-pollution.py` 兜底） |
| **DEBT0029** | `check-gate.py` gate_p2 骨架声明校验用**标题字符串子串判定**（阻断性） | **`open`** | P0-brief 声明「吸收 RM-AG0085、对应批次合入后核对并关闭」；roadmap **RM-AG0085 仍 `backlog`**、DEBT0029 **仍 `open`** ⇒ **主 Agent 须核对是否已被批 F「骨架标题级判定」闭合**，是则关闭（RM-AG0085/DEBT0029 关联任务列为 `—`，不触发本任务 gate） |
| **DEBT0031** | P1 frontmatter `phases` 与正文裁剪声明无机械一致性校验 | **`open`** | P0-brief 声明「吸收 RM-AG0087…核对并关闭」；roadmap **RM-AG0087 仍 `backlog`**、DEBT0031 **仍 `open`** ⇒ 同上，须核对批 F「`pruned` 闭合」是否已闭合 |
| DEBT0044 | `check-judge-verdict.py::_two_sections` 无终止符 + 白名单正则误报 | `open` | 与批 D（读结构化 `criteria`）同域；**本任务未闭合**，留 `open`（不阻断） |
| DEBT0047 | `gate_commands` 取值引号陷阱 + 未引号通配 pathspec 漏检 | `open` | 本任务 `gate_commands` 写入遵循约束（值行无行尾注释）；**未闭合**，留 `open` |

- **本次未新增债务条目**（P7 记录的 CODE-MAP DRIFT 等为 WARNING 级观察项，见 §7，未登记为新债务）。
- ⚠️ **主 Agent 关注项**：**DEBT0029 / DEBT0031 与 RM-AG0085 / RM-AG0087 的关闭**——P0-brief 已声明由本任务吸收，
  但实测四者状态均未变（DEBT `open` / RM `backlog`）。**这是「声明吸收」与「实际闭合」的缺口**，须在 P8 前核对决定。
- 已核对 id 清单（相关）：DEBT0025、DEBT0029、DEBT0031、DEBT0040、DEBT0044、DEBT0047。

## 7. 已知偏离留痕

1. **known-violations（维护性反模式）1 条**（`known-violations.md`，P4 评审已确认）：
   - `agate/scripts/pre-commit-gate.py` **god-file 跨越**：before=998 / after=1144 / threshold=1000。
     理由 = G2 的 T4 安全门（P2 §3.1）+ F10 接线（§3.6）为设计强制改动；后续可把
     PROD_TOUCHED 扫描/F10 检查抽到独立模块以回落阈值以下。**登记数 1 = 检测数 1，P4 评审 `是`。**
2. **DESIGN_GAP 配对**（`P7-consistency.md` §1）：**15/15 全配对**（P4 四处：`P4-implementation.md`=2、
   `-G1.md`=5、`-G2.md`=7、`-G3.md`=1），`design_gap_count=15 / design_gap_reviewed_count=15`。
   gate 转抄核对 `P4 散文(2) ≤ 15` 成立（分批文件不在 gate 计数面，属已知口径）。
3. **CODE-MAP DRIFT（WARNING 级，不阻断）**（`P7-consistency.md` §5）：
   - `[CODE_MAP_DRIFT: agate/scripts/agate-task-init.py 未登记进 CODE-MAP.md scripts 模块]`
   - `[CODE_MAP_DRIFT: agate/rules/task-data/{LEVELS,level-1}.yaml 未登记进 CODE-MAP.md rules 模块]`
   - `[CODE_MAP_DRIFT: P4-implementation.md 新增文件核对表将既有 obligations.yaml / check-obligations.py 误列为「新增文件」]`
   - 处置：**主 Agent 在 P8 前决定是否把前 2 处补登记进 `agate-workspace/agents/CODE-MAP.md`**（WARNING，不阻断）。
4. **⚠️ 版本语义冲突（须主 Agent 裁决）**：`CHANGELOG.md`（v0.79.0 节）预告「迁移截止版本 v0.80.0
   ⇒ `agate.config.yaml` 缺失/非法自 v0.80.0 起 `exit 1` 硬拦截」，但**本任务未实现该硬切**
   （`agate/scripts/` 无 `0.80.0` 引用；`gate_p0` 仍为「迁移期 WARNING」）。按 v0.80.0 发布则该预告不兑现——
   见 §1 末「须主 Agent 裁决」。
5. **派发口径差异**：派发指引记 `P2§packages` 为 **6 个**，实测 **8 项**（与 `P1§packages` 一致）。
   本文件按 8 项核对；与 `P7-consistency.md` §3.1 同源记录，**非本任务新问题**。
6. **R6 活树自核验拦截**：`r6-differential.sh --corpus .` 在 P8 脏工作树上 exit 1（干净自核验），
   干净副本上 exit 0（见 §4）。属脚本**设计行为**，非差异违规。
7. **README.zh-CN.md badge 滞后**（`v0.78.0`）：既有状态，CHECK 7 不读该文件，非本次引入，**本轮不动**。

## 8. 临时资源清单（releaser → 主 Agent 交接）

- **启动的临时服务 / 进程**：无。无 debug server / 无临时 daemon / 无占用端口。
- **临时数据库**：无。
- **临时数据 / 目录**（均在仓库外 `/tmp`，不影响 git 状态）：
  - `/tmp/oclab_r6_corpus`：R6 干净 clone 副本（跑完 **已 `rm -rf` 删除**）。
  - `/tmp/rc_*.log`、`/tmp/oclab_cons.log`：本轮只读检查命令的输出日志（仓库外，无需入库）。
  - 仓库内**无**临时目录 / 账本污染残留（跑完核验真实仓库 `git status --porcelain` 仅含本任务已知的
    P8 未提交产物：`.state.yaml` / `gate-events.jsonl` / `P8-dispatch-context-implementer.md`）。
- **开发安装**：无。用系统 `python3`，未新装 editable install / 全局包 / `pip install`。
- **canonical 临时产物目录** `<项目根>/.agate-tmp/`：本任务**未创建**（自查 `ls -A .agate-tmp` 为空/不存在）。
- **结论**：本任务临时资源清单 = **无仓库内残留**；主 Agent 无需清理（`/tmp` 项已自清或由会话生命周期管理）。
- **状态标记**：`[PROD_NOT_TOUCHED]`。

## 9. Lessons Learned

> 类别 / 教训 / 来源任务 / 日期 —— 供主 Agent 汇入 `docs/notes/lessons.md`。

- **流程 | 多包任务的 packages 是「改动分域」而非独立版本号；且派发指引的包数须以 P2 实测为准**：
  本任务派发指引记 6 个包，`P2-design.md`/`P1-requirements.md` 实测为 8 项——单版本号仓库只 bump
  agateon 一个版本号（v0.80.0）。P8 须以**实测 packages 逐包**核对，并显式写明「不各自 bump」，
  避免下游误判「漏 bump」。来源 TAG0050 / 2026-10-09。
- **流程 | roadmap 回写的反查对象是「关联任务列含本 task_id 的**全部** RM 行」**：本任务除登记的
  RM-AG0099 外，**并入批次的 RM-AG0101 关联任务列也含 `TAG0050`** ⇒ 同样触发 RM-AG0043 硬校验。
  只回写「主登记条目」会漏掉并入条目、导致 `gate_p8` 阻断。P8 须用与 `_check_roadmap_done`
  同款解析（`|` 分列、列数=9、第 5 数据列）**枚举全部命中行**，而非只看一条。来源 TAG0050 / 2026-10-09。
- **测试 | R6 差分脚本在 P8 脏工作树上必然被「原仓库干净」自核验拦截，须改在干净副本上取真信号**：
  `r6-differential.sh` 运行前/后各核验 `git status --porcelain` 为空——P8 阶段工作树含未提交任务产物，
  故 `--corpus .` 恒 exit 1（拦截，非差异违规）。取真信号的做法 = `git clone` 干净副本后
  `--corpus <clone> --after 本 checkout/agate`（P5 已用同法）。来源 TAG0050 / 2026-10-09。

## 10. 主 Agent 待办（P8 gate 通过后亲自执行，releaser 不做）

1. **裁决版本语义冲突**（§1 末 / §7-4）：确认 v0.80.0 是否接受 deadline 顺延（同步改述 TAG0042 预告），或改用其他版本号。
2. **回写 roadmap**（§5）：`RM-AG0099` 与 `RM-AG0101` **一并**改为 `done`（二者关联任务列均含 `TAG0050`）。
3. **核对债务闭合**（§6）：确认 `DEBT0029`/`DEBT0031` 与 `RM-AG0085`/`RM-AG0087` 是否已由批 F 闭合，是则关闭。
4. **（可选）补 CODE-MAP 登记**（§7-3）：`agate-task-init.py` + `rules/task-data/{LEVELS,level-1}.yaml`（WARNING 级）。
5. **bump 与归并**：改 `README.md` badge → `v0.80.0`；`CHANGELOG.md` `[Unreleased]` → `## [0.80.0]`（§2，含义务基线重设声明、逐批补条目）；`agate/UPGRADING.md` 4 个「未发布」节归并 `### v0.80.0`（§3）。
6. **跑 `check-gate.py P8 $TASK_DIR`**（bump_type + debt_check + delivery + 暂存区 version/CHANGELOG 变更 + roadmap done 反查）。
7. **P5 验证**（P8 卡条件化表述）：`python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`；
   `reuse_allowed` → 复用 `P5-test-results/`；否则完整重跑 `gate_commands.P5`。
8. **R6 复跑**：提交 P8 产出（工作树干净）后 `bash docs/design-notes/r6-differential.sh --corpus .` 预期 exit 0。
9. **commit + tag**：同一 commit（phase=P8）+ `git tag v0.80.0`；`git log v0.79.0..HEAD --oneline` 对照 CHANGELOG 无遗漏。
   本任务触及 `agate/` 协议本体与 `UPGRADING.md` 等 SELF-GATE 触发面 ⇒ commit message 须带 `self-gate-review:` 留痕。
10. **README 收尾**：`[PROD_NOT_TOUCHED]` 确认；临时资源清单（§8）无仓库内残留。

## 11. 交付收尾（delivery）

**delivery: PR 普通 merge（`--no-ff`，禁止 squash）+ tag v0.80.0 + GitHub Release**
（`.github/workflows/release.yml` 自动构建；**先合 PR、后打 tag**）。

1. **合 PR**：分支 → PR，用**普通 merge（`--no-ff`）**，**禁止 squash**（squash 会生成 SHA 不同的提交，
   tag 与 main 分叉、`git describe --abbrev=0` 回退旧版；v0.31.0 事故）。
2. **打 tag**：PR 合并到 main 后 `git tag v0.80.0 && git push origin v0.80.0`（`git push` 不带 tag 默认不推 tag）
   → `git ls-remote --tags origin v0.80.0` 验证远端到达。
3. **出 Release**：tag 推送触发 `release.yml`；`gh release view v0.80.0` 须存在，资产含本体 tarball +
   两平台 offline 包 + `SHA256SUMS`。
4. **G-5 最终验证**：`git fetch origin && git describe --tags --abbrev=0 origin/main` == `v0.80.0`
   （**`--abbrev=0` 不可省**）；`git merge-base --is-ancestor v0.80.0 origin/main` 返回 0；合并后 push 的 CI 全绿。

> 顺序要点：**先合 PR、后打 tag**——`CHECK 7`（badge ↔ CHANGELOG 最新已发布版本）已 tag 无关；
> tag 指向校验由 `release.yml`「Verify tag points to matching commit」步承担。

---

> 注：本文件不含 PASS/FAIL 预判——所有结果均为 releaser 本轮自检的**客观运行输出**，gate 判定由主 Agent 亲自执行。
