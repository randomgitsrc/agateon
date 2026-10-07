---
phase: P2
task_id: TAG0050
type: design
parent: P1-requirements.md
trace_id: TAG0050-P2-20261006
status: draft
created: 2026-10-06
agent: architect
candidate_count: 3
packages:
- agate-scripts
- agate-rules
- agate-task-data
- agate-cards
- agate-roles
- agate-tests
- ci-workflows
- docs-upgrading
domains:
- backend
- cli
- security
ui_affected: false
dispatch_plan: {mode: static-batch, parallel_limit: 10, batches: [{id: A0, complexity: low}, {id: A1, complexity: high}, {id: A2, complexity: high}, {id: A3, complexity: medium}, {id: A4, complexity: medium}, {id: B, complexity: high}, {id: C, complexity: low}, {id: D, complexity: high}, {id: E, complexity: medium}, {id: F, complexity: medium}]}
---

# TAG0050 P2 方案设计 — 任务数据契约：结构化判定、可信写入与任务版本

> **设计依据**：`docs/design-notes/design-tag0050-task-data-contract.md`（14 节 + 附录 A，r4 **APPROVE WITH CHANGES**）。
> **需求基线**：`P1-requirements.md`（77 条 BDD，10 批 A0/A1/A2/A3/A4/B/C/D/E/F）。
> **本文件的性质**：把**已 4 轮独立评审通过的设计**形式化为本任务的 P2 设计——**不改设计的技术决策**。
> 形式化过程中发现的**设计内部矛盾**或**与当前代码不符**一律登记在 §10 `design_gap`，交 P2 评审裁决，不擅自改方案。
> **范围**：只改 agateon 本仓；peekview 只在**只读副本**上做 R6 双向差分。

---

## 修订记录（P2 retry 1，2026-10-07）

> 首版被两位专家双双 rejected（`P2-review-eng.md` / `P2-review-cso.md` / `P2-review.md`），外部专家对 Q1–Q4 给出实测裁决（`docs/reviews/tag0050-p2-expert-answers.md`）。本次**不改设计路线**（契约等级 / 工具写入 / 机械核验 / CI 回放），只改**规格与措辞**：

| # | 修订项 | 闭合方式 | 落点 |
|---|---|---|---|
| 1 | **B1**（eng BLOCKER，源自 G5）：`gate_commands.P5_r6_differential` 指向不存在的脚本 | 路线①改形：A1 交付 `docs/design-notes/r6-differential.sh`（接口 `--before/--after/--corpus/--allow` + `r6-allowlist.yaml` + 副本内自核验 + 负向用例）；gate 命令改 `--corpus .`（只跑仓内语料）；peekview 部分转 **P6 证据**（D3 绑定）；§8 十二项改写为机器可读匹配规则 | §1.1 A1、§3、§6、§7、§3.3、§10 G5 |
| 2 | **BLOCKER-1**（cso）：F4 生产接触安全门规格矛盾 | 单一来源：`markers.yaml` 的 `PROD_TOUCHED.lead_variant` 改 `default`，pre-commit 用 `agate_markers.pattern()`；扫描面 = 任务目录内**全部暂存 `*.md` 新增行**（只排除 `AGATE_CARD` 块）；**T4 = 唯一安全门**，T1 标记表去掉 `PROD_TOUCHED`；否定写法继续阻断 + 专门指引；补非声明文件粗体/引用块锚；补威胁模型 | §1.1 A1/C、§1.3 R8、§3.1（新增 F4 规格节）、§8、§10 |
| 3 | **`P5_repro` 是「不会变红的 gate」**（专家新发现，与 B1 同类） | 从 `gate_commands` **删除** `P5_repro`（只打印不断言 + 篡改全在 legacy 上 ⇒ 永不变红）；`repro-tag0050.sh` 保留为**证据文档**；改由各批验收锚的「先红后绿」pytest 用例（非 legacy init 任务）承担 | §6、§7、§8、§9 |
| 4 | **G3（RM-AG0100）**：专家裁**作为缺陷不成立**（版本错位误诊） | §10 G3 改写为裁决（含「误诊」结论）；派生真实事项归 **A3**（PAUSED/READY/DONE 转换事件入库 + 2h.1d `git add` 失败可见）；BDD-01 Then 收窄为「写入工作区账本」、committed-ledger 断言归 A3（BDD-38）；A3 验收须用真实 `git commit` + 指向 checkout 协议的 hook | §1.1 A3、§3、§10 G3 |
| 5 | **新派生风险**：本机稳定版 v0.78.3 与 §2.4 回放的 merge-base 协议 v0.79.0 不一致 | **已缓解**：主 Agent 已把本机对齐 v0.79.0（`agate-install.py v0.79.0` + `--adopt`），本机与 merge-base 协议同为 v0.79.0；**保留**「agateon 写 `.agate-version`」作为 A2 前置条件（防未来发版后本机再次漂移）；并注明 hook 内跨目录调 git 须用绝对路径 | §1.3 R13、§8 |
| 6 | **非阻塞项**（两位专家已确认） | eng M2/G1/N2、cso MEDIUM-2/MEDIUM-4/LOW-1/LOW-2 及 eng N1/N3–N7 逐条落实 | 见各处 |

---

## 0. 形式化边界与基线

| 项 | 值 |
|---|---|
| 设计基线 | main `720c97d3`（v0.79.0，TAG0042 已合入）；本 checkout HEAD `adb0b11`（分支 `feat/TAG0050-task-data-contract`，仅 TAG0050 P0/P1 + chore，**协议代码与 main 无漂移**） |
| `origin/main` | 仍 `720c97d3` → 无漂移 |
| 协议版本 | 本机稳定版 agate 已对齐 **v0.79.0**（`AGATE_ROOT=/home/kity/.agate/v0.79.0/agate`、`AGATE_VERSION=v0.79.0`；`current→latest→v0.79.0`），与 main `720c97d3`（v0.79.0）一致；**对齐动作已完成**（`agate-install.py v0.79.0` + `--adopt`）。原风险（v0.78.3 ↔ v0.79.0 不一致）见 §1.3 R13 与 §8 |
| consistency 基线 | 本 checkout **0 ERROR / 410 WARNING**（WARNING 全为冻结文件，无 live WARNING） |
| 测试环境 | pytest 9.0.3；`count-tests.sh` 实测 **2671** 用例（下界语义"目标 ≥ 749"为 TAG0011 迁移基线） |
| 项目侧架构决策 | `agate-workspace/decisions/` **不存在** → 无既有跨任务决策需对齐 |
| 评审链 | r1 REJECT → r2 REJECT → r3 REJECT（仅 §2.4）→ r4 APPROVE WITH CHANGES（3 MAJOR + 4 MINOR 已落实） |

**形式化只做四件事**：① 影响域分析（改什么/不改什么/风险）；② 候选方案探索（选定设计既定路线）；③ 验证契约固化（`gate_commands`）；④ 实现导航（`files_to_read`）与批次编排（`dispatch_plan`）。技术方案以设计为准。

---

## 1. 影响面梳理（强制节，写在候选方案之前）

> 证据来源：设计 §0/§11 的消费方清单、P1 §3 同类扫描与登记面实测、本 P2 的登记面再实测与只读代码核验（§9）。

### 1.1 改什么（Modify）

逐批列出**改动落点**（到文件:小节/函数）与关联 BDD 编号：

| 批 | 改动落点（文件 : 小节 / 函数） | 关联 BDD |
|---|---|---|
| **A0** | `agate/scripts/pre-commit-gate.py` PAUSED 留痕分支（`:370` `append_event` 改 2 参调用）；`agate/scripts/check-gate.py` **`main()` 单点早检**（`if not os.path.isdir(task_dir): return 1`，置于 `handlers.get(phase)` 分派**之前**）→ **所有 phase**（含 P7/P5/P0/P6.5/未知 phase）对不存在的任务目录统一返回 1（现状随 phase 不同，见 §10 G1） | BDD-01, BDD-02 |
| **A1** | 新增 `agate/rules/task-data/LEVELS.yaml` + `level-1.yaml`（冻结快照）；新增 `agate/scripts/agate-task-init.py`；`agate_common.py` 新增 `task_level`/`requirement_active`/`check_ledger_events`/`TASK_ID_RE`/`load_contract`/`project_root`，改 `is_new_task_for_evidence_ref`；`check-events.py` 改调 `check_ledger_events`；`pre-commit-gate.py` 在 `2h.1b` 之前新增"账本与新目录"步骤（每次提交都跑）、把 PROD_TOUCHED 扫描面扩到"每个有暂存文件的任务目录"、非 legacy 按被暂存产出所属阶段重跑 gate、改 `_judge_enabled`；`check-gate.py:767` 与 `gate_p65`；`check-state-transition.py` legacy 重开判 ERROR；`agate-next.py:_p6_judge_advance`；`check-state-yaml.py` 与 `agate-state-yaml-check.py:39` 统一 ID 正则；`check-protocol-consistency.py` 新增快照冻结 CHECK + 黄金 fixture 回归；`check-p6-evidence.py`/`check-p6-provenance.py` 的 `evidence_ref` 改依契约；`agate-migrate-workspace.py` 补用例；`conftest.py` 新增 `init_task()`；新增 `agate/tests/fixtures/task-data/level-1/{pass,fail}/`；**新增 R6 差分交付物** `docs/design-notes/r6-differential.sh`（接口 `--before <rev> --after <dir> --corpus <repo>... [--allow <file>]`，见 §3.2）+ `docs/design-notes/r6-allowlist.yaml`（§3.3 的机器可读匹配规则）；**PROD_TOUCHED 扫描面扩到「每个有暂存文件的任务目录内的全部暂存 `*.md` 新增行」**（§2.3 规则 7，只排除 `AGATE_CARD` 块） | BDD-03…22 |
| **A2** | 重写 `agate/scripts/agate-ci-verify.py`（逐提交回放 + `--base` + 按事件取范围 + 协议版本选择 + merge-base 等级检查 + 账本前缀/事件最终检查）；`pre-commit-gate.py` 回放模式（`AGATE_REPLAY=1` 跳过改文件步骤、不写 `.gate-result.json`/`.gate-history.jsonl`）；`.github/workflows/protocol-tests.yml`（`fetch-depth: 0`；`gate-backstop` required 需许可） | BDD-23…35 |
| **A3** | 新增 `agate/scripts/agate-state-set.py`；`check-state-transition.py` 抽纯函数 `check_transition(old,new,task_dir)` **并让 `_scan_bdd3_keyword_phases()` 扫描排除 `<!-- AGATE_CARD_START -->…<!-- AGATE_CARD_END -->` 块**（RM-AG0101，单 owner）+ 两向回归用例；`pre-commit-gate.py` 把 `2h.1c`+`2h.1d` **一起**前移到 `2g` 之前（**使进入 PAUSED/READY/DONE 的转换事件随本次提交入库**，RM-AG0100 派生事项①）、并让 `2h.1d` 的 `git add` **失败可见**（检查返回码，失败给 WARNING，派生事项②）；`agate-next.py` 不再追加 `state_transition`、建议里给 state-set 命令；`check-state-yaml.py` 非 legacy `status` 现算 | BDD-36…39 |
| **A4** | `check-obligations.py`（`enforced_at` ast 可达 + `test` 节点存在 + `review_output` + `scope: protocol-repo` + 负向控制抽样）；`agate/rules/obligations.yaml`（改标 F13 的 4 条 M 与若干 R + `baseline.reset`） | BDD-40…44 |
| **B** | 新增 `agate/scripts/agate_schema.py`（JSON Schema 子集 + `derive`/`render`）；`check-yaml-schema.py`/`agate-frontmatter-check.py`/`agate-config.py:_validate_node` 三处合并调用；`agate-md-field-set.py` 支持 7 种操作；`agate-md-field-get.py` 系统字段现算；`agate-config.py` 补 set/unset/explain；`agate-run.py`/`agate-config.py` 改用 `project_root()`；`check-structure-consistency.py` 检查 `task_fields` ⊆ 快照字段；`agate-feedback.py` 补用例；快照 `files` 节 + 渲染块（`<!-- AGATE:RENDER ... -->`） | BDD-45…51 |
| **C** | `pre-commit-gate.py` 增 `prod_touched` 字段检查；**F4 安全门单一来源**：`markers.yaml` 的 `PROD_TOUCHED.lead_variant` 由 `dash_only` 改 `default`、`:348/355` 删字面正则改调 `agate_markers.pattern("PROD_TOUCHED")`；**T4 = 唯一 PROD_TOUCHED 安全门**（T1 标记表去掉 `PROD_TOUCHED`）；否定写法继续阻断 + 专门指引；快照 `primary_outputs` 指定各阶段主产出（**完整规格见 §3.1**） | BDD-52…55 |
| **D** | `check-gate.py` `gate_p6` 实现判据 D1–D10；**D3 在 `cmd_run` 事件缺失时 fail-closed，并区分「事件缺失」与「sha256 不匹配」两种报错**（cso MEDIUM-4）；`check-judge-verdict.py` 第 4–6 条改读 `criteria`；`agate-run.py --task` + 任务内日志 `run:<k>`（`cmd_run` 增 `k`/`log`/`sha256`）；`agate-extract-context.py:190-211` 改读字段；非 legacy 跳过 `check-p6-format.py`/`agate-evidence-consistency.py`；`gitignore-fragment.txt` 增取反规则 + **提示 Git 父目录排除限制（父目录被排除时 `!` 无法重新包含其下文件，cso LOW-2）**；快照 `results` | BDD-56…60 |
| **E** | `check-gate.py` P7 与 P4 核对表（`design_gap_reviews`/`code_map_reviewed`/`findings`）；`check-scope-resolved.py`/`check-retrospective.py` 改读聚合结果；`agate-debt-check.py` + tech-debt schema 增 `source_ref`；`markers.yaml` 补登记 5 个标记；快照 `declaration_files` | BDD-61…66 |
| **F** | `check-gate.py` P1-review `reviewed_bdds`、P2 UI 节、`:964` 骨架标题级判定（RM-AG0085）、`:1450` P8 `delivery` 结构化；`check-pruning.py` 改读 frontmatter 与 `pruned`；快照 `ui_design`/`delivery`/`pruned`/`phase_universe` | BDD-67…72 |
| **跨批** | 每批独立 PR/gate/评审 + 新增要求登记新一级快照（BDD-73）；legacy 退出码与 ERROR 集合不变、差异限设计 §8 十二项（BDD-74）；每批 pytest 全绿 + consistency 0 ERROR + count-tests 一致（BDD-75）；义务基线一次性重设写 CHANGELOG（BDD-76）；新增 `agate/scripts/` 文件不触发既有测试转红（BDD-77） | BDD-73…77 |

### 1.2 不改什么（Not Modify）

显式列出**看起来该改但决定不改**的范围（P4 implementer 的范围边界）：

| 范围 | 不改的理由 |
|---|---|
| peekview 及其他项目 | 设计 §12 明确不做；peekview 只作 R6 差分的**只读副本**检验对象，不改其文件/CI/`.gitignore`/`.agate-version`（只在 `UPGRADING.md` 给指引） |
| legacy 任务的格式与数据 | 零迁移承诺（设计 §8）：格式、退出码、ERROR 集合不变；无创建事件即走旧逻辑 |
| P0-brief 内嵌 yaml、judge 的信息隔离扫描 | 设计 §12 明确不改 |
| `gate_layer` 消费方、`release.preset`、`agate-run` 普通运行基线比对 | 范围外（设计 §9/§12）；各自建议单独登记 RM。`agate-run` 基线缺陷由**独立 hotfix** 修复，仅作批 D 前置条件，不在本任务实现 |
| `agate-extract-context.py` 的抽取逻辑（除 `:190-211`） | 设计 §11/§12：只有 `:190-211` 的计数改读字段，抽取算法不动 |
| 既有测试（除允许例外） | 只允许改设计 §8 第 7/8/10/11/12 项涉及用例 + "新建任务目录并提交"用例（改 `init_task()`）；其余全绿 |
| `active-tasks.md` 渲染 | RM-AG0059 第 ② 项不在范围（设计 §2.7） |
| 签名机制 | 设计 §12 明确不引入 |
| 协议文档正文的改写 | 属各批 P4 工作（DEBT0039），不在本 P2 设计范围内落地 |

### 1.3 风险在哪（Risk）

每条风险配一条缓解措施：

| # | 风险 | 缓解措施 |
|---|---|---|
| R1 | **双源同步**：快照（数据）与 gate 代码语义可能漂移，导致在途任务被追溯 | 代码语义一经发布冻结（改行为起新名字）+ 每级黄金 fixture 在 CI 回归（BDD-16）+ 快照字节 sha256 冻结 CHECK（BDD-15） |
| R2 | **schema 迁移**：`agate-frontmatter-check.py` 的自定义格式转 JSON Schema 子集时行为漂移 | legacy 任务用**转换前的冻结副本**；三处校验器合并为 `agate_schema.py` 单实现；等价守护测试（BDD-50） |
| R3 | **legacy 兼容**：扩大判定面可能使 legacy 任务新增 ERROR | 设计 §8 承诺"退出码与 ERROR 集合不变"，差异限 12 项；每批在两仓**只读副本**上跑 R6 双向差分，第 12 项新增 ERROR 单独统计并逐条列出（BDD-22/74） |
| R4 | **既有测试转红**：规则 1 使"新建任务目录并提交"用例转红（预估约 35 个） | conftest 新增 `init_task()`；批 A1 的 P1 给出**逐条清单**并列入 §8 例外（BDD-75） |
| R5 | **CI 回放协议版本**：回放用错协议版本会误判合规提交 | 逐提交读 C 树 `.agate-version` 且 ≥ merge-base，降级判 FAIL；agateon 未固定版本用 merge-base 的 `agate/`；否则 FAIL（BDD-31/32/33）。**与 R13 合看**：本机稳定版与 merge-base 协议不一致时，回放可能误报 |
| R6 | **义务基线一次性重设**被误读为质量倒退 | `baseline.reset` 显式重设 + 写 CHANGELOG；之后恢复"只增不减"（BDD-44/76） |
| R7 | **T1 绊线误报**：存量 626 行（agateon 393 + peekview 233）命中 | 批 B 启用 ERROR 前完成 E3 抽样（引述/讨论类误报为 0）；否则 P7/P8 评审稿 T1 降 WARNING 且声明同时写入字段（BDD-51） |
| R8 | **安全门误拦面**：F4 的否定写法 `[PROD_TOUCHED]: 无` 在新扫描面下**仍会被拦**（安全门 fail-safe，有意取舍） | 专家两仓全量语料实测：新口径 + 新扫描面**新增误拦为 0**；否定写法继续阻断，报错信息专写指引（未触达生产请写 `prod_touched: false` 并删除正文标记）；对 legacy 与现状一致，不属 §8 新差异；R6 差分第 12 项单独统计并逐条列出（BDD-54/55，§3.1） |
| R9 | **判据脚本写副作用污染真实仓库**：R6/批量实验若对真实仓库跑会改账本 | 一律在 `mktemp -d`/`cp -r` 副本上跑，跑完核验真实仓库 `git status --porcelain` 为空（AGENTS.md 工作流 0a） |
| R10 | **新增 CHECK 误伤存量**：快照冻结 CHECK 等新规则可能命中既有文档/数据面 | 按 DEBT0025 先全量扫描存量再启用常驻阻断；快照冻结 CHECK 只作用于 `agate/rules/task-data/` |
| R11 | **A0 修复范围不全**：不存在的任务目录 rc 随 phase 不同（P7=0、P5=2、其余=1） | A0 实现须逐 phase 统一为 1（含 P7/P5），见 §10 G1 |
| R12 | **并行写入撞号**：58 个 `P4-implementation-*.md` 的 ID 编号 | ID 格式 `<相对路径去 .md>:<前缀><n>`，每文件独立编号；`agate-md-field-set` 不加锁、各子任务写各自文件（BDD-63） |
| R13 | **本机稳定版与回放协议不一致**（专家新提）→ **已缓解**：原风险 = 本机 hook 为 **v0.78.3**，而设计 §2.4 规定 agateon 未固定版本时回放用 **merge-base 的 `agate/`（v0.79.0）** ⇒ A2 落地后可能误报 FAIL（同一提交、两版本、两种结果，专家实测）。**现已对齐 v0.79.0**（`agate-install.py v0.79.0` + `--adopt`；主 Agent 真实 `git commit` 探针复验：v0.79.0 hook 下 committed ledger = 2 行、工作区干净，账本 `git add` 正常落入本次提交） | **风险已缓解**（本机与 merge-base 协议同为 v0.79.0）。**仍保留**「把 P1 §5 的 SUGGEST『agateon 写 `.agate-version`』升为 A2 前置条件」——**理由改为防未来发版后本机再次漂移**（版本对齐是一次性动作，`.agate-version` 是持久约束）；写入 §8 `env_constraints`（`agateon_version_alignment`）。另注：`git` 对普通提交在 pre-commit hook **之后**重读索引，hook 内 `git add` **会**进入本次提交；hook 拿到的 `GIT_INDEX_FILE=.git/index` 为相对路径，现有 `run_git` 不设 `cwd` 故不受影响——**A3 说明中注明**：hook 内若在别目录调 git，须用绝对路径 |
| R14 | **R6 差分脚本自身可能「不会变红」**（与 B1/P5_repro 同类教训） | A1 交付的 `r6-differential.sh` 必须配**负向用例**：从 `r6-allowlist.yaml` 删掉一条真实需要的规则 → 脚本必须变红（exit 1）；且脚本**自己核验**每个 corpus 原仓库 `git status --porcelain` 为空，否则 exit 1（把 AGENTS.md 工作流 0a 变成机械判据） |

### 1.4 登记面（新增/改名 `agate/scripts/` 下文件时必填）—— 实测

本任务**新增**三个文件：`agate/scripts/agate-task-init.py`、`agate/scripts/agate-state-set.py`、`agate/scripts/agate_schema.py`（均为 `agate-*.py` / 库，**非 `check-*.py`**）；**不新增 `check-*.py`**（冻结 CHECK 与义务核验均为**修改既有脚本**）。

**实测方法**（本 P2，2026-10-06，本 checkout）：把上述三个探针文件真放进 `agate/scripts/`，实跑 `check-protocol-consistency.py` 与 `pytest test_protocol_alignment_review.py test_consistency.py test_t43_check_registration_surface.py`；跑完删除探针并核验 `git status --porcelain`。

| 登记面 | 类型 | 实测结果 |
|---|---|---|
| ① **CHECK 9 覆盖**（`uncovered_gate_scripts()`，仅 glob `check-*.py` + `pre-commit-gate.{sh,py}`） | **门禁**（WARNING） | **无新增告警**——印证 README"`agate-*.py` 不在门禁覆盖面内" |
| ② **SG.6**（`test_protocol_alignment_review.py`） | **门禁**（pytest） | **通过**（与 ① 共用同一判据 `uncovered_gate_scripts()`） |
| ③ **CHECK 10 协议文档脚本名引用漂移** | **非登记面（方向相反）** | **无新增**——它只报"协议文档引用了**不存在**的脚本"，新增脚本本身不触发；**改名/退役**脚本时才看 |
| ④ `agate/scripts/README.md` 脚本索引表 | 约定 | 无需动作（本三文件无特定机械断言） |
| ⑤ `agate/tests/README.md` 映射表 | 约定 | 建议在对应批补"脚本→测试"映射行 |
| ⑥ `count-tests.sh` | 自动（下界语义） | 新增脚本不使其转红（实测 2671，下界 749） |
| ⑦ `CHANGELOG.md` | 任务级约定 | 各批按需写（含义务基线重设说明） |

**实测结论**：探针在位时 consistency **0 ERROR / 410 WARNING**（与基线 410 相同，探针未新增任何 WARNING）；`pytest` 三文件 **36 passed**；探针删除后真实仓库 `git status --porcelain` 仅剩 TAG0050 未跟踪派发/进度文件，**无探针残留**。⇒ 新增 `agate-*.py` / 库**不触发任何机械门禁**（① 不覆盖、② 共用同判据、③ 方向相反），登记属团队约定；本任务**不新增 `check-*.py`**，① 覆盖面无需扩展。

**B1 交付物（`docs/design-notes/r6-differential.sh` + `r6-allowlist.yaml`）的登记面**：二者位于 `docs/design-notes/`，**不在 `agate/scripts/` 下**，故不属 CHECK 9 / SG.6 的扫描面（`uncovered_gate_scripts()` 只 glob `check-*.py` + `pre-commit-gate.{sh,py}`）；CHECK 10 只报「协议文档引用了不存在的脚本」，**新增**脚本文件不触发。⇒ 无机械登记面动作，按团队约定在 `docs/design-notes/README.md` 索引登记。

---

## 2. 候选方案

### 候选一（**选定**）：按设计的"契约等级冻结 + 工具写入 + 机械核验 + CI 回放"，10 批分阶段落地

- **做法**：`agate/rules/task-data/level-N.yaml` 冻结字段契约与要求项；账本首行 `task_created` 记录 `contract_level`（只升不降，无创建事件即 legacy）；agent 声明只经 set/append 工具写入、gate 用同一契约复验；计数/创建时间/judge 是否必需/义务执行方式由工具/gate 现算或机械核验；可信锚点为 `agate-ci-verify` 对变更任务的逐提交 CI 回放。顺序 A0 → A1 → {A2, B}；A3、A4 与 A1 并行；B → C → {D, E, F}。
- **优点**：逐条对应 P1 的 77 BDD；根治 F1–F15；新旧任务按契约等级分流、不靠日期；可解释的 CI 可信锚点。
- **风险/代价**：规模大（约 30 个脚本 + 卡片，设计 §11）；需一次性义务基线重设；CI 回放依赖 `.agate-version`；A2 设 required 需用户许可。
- **工作量**：高（10 批，其中 4 批 high）。

### 候选二：只做"结构化字段 + 机械核验"，去掉契约等级/任务版本与 CI 回放

- **做法**：保留 §3–§7 的结构化字段与判据，但不引入 `LEVELS.yaml`/`task_created`/`level(Pk)`（不做 A1 的等级机制、不做 A2 的 CI 回放），legacy 与新任务共用一套判定。
- **优点**：改动面显著更小；无 CI 依赖、无等级迁移、无协议版本要求。
- **缺点**：F3（`created` 日期门槛、`judge.enabled` 开关）与 F7（覆盖模式读不到版本）**无法根治**；无"按阶段确定生效等级"，schema 收紧会追溯在途任务；无 CI 锚点 → `--no-verify`/amend 改写账本仍无外部约束；P1 的 A1/A2 锚（BDD-03…35）无法满足。

### 候选三：维持正则/散文判定，只加固正则 + 增加绊线

- **做法**：不引入结构化字段与工具写入，只把行首正则从 4 套口径收敛为 1 套，并扩大绊线覆盖。
- **优点**：最小改动、最低回归风险。
- **缺点**：根因未除——F6 的 182 行口径分歧会随语料增长重现（"追着改正则永远追不完"）；F2 的自报汇总仍可被盖住、F3 的开关仍可改；与 P1 §1"判定只读结构化数据"的需求**直接冲突**。

### 权衡与选择理由（tradeoff / choice_and_reason）

| 维度 | 候选一 | 候选二 | 候选三 |
|---|---|---|---|
| 覆盖 P1 77 BDD | 全部 | 缺 A1/A2 的 33 条 | 缺 A1–F 的绝大多数 |
| 根治 F1–F15 | 是 | 部分（F3/F7/F15 未解） | 否 |
| 新旧任务分流 | 契约等级（不靠日期） | 无分流 | 无分流 |
| 可信锚点 | CI 逐提交回放 | 无 | 无 |
| 规模/代价 | 高 | 中 | 低 |
| 回归风险 | 中（有 R6 + 例外清单兜底） | 低 | 低但需求不满足 |

**选择理由**：候选一与 P1 需求基线**逐条对应**，且其技术决策已由独立评审 r1→r4 收敛至 APPROVE WITH CHANGES；候选二在"任务版本/可信锚点"两个 P1 核心目标上不成立，候选三与 P1 原则直接冲突。因此选定候选一，并**不改其技术决策**（形式化中发现的问题登记于 §10）。

---

## 3. 设计要点与 BDD 逐批对应

> P1 的 77 条 BDD 按 10 批分组（`P1-requirements.md` §4）。下表把**批 ↔ BDD ↔ 设计节 ↔ 复杂度**逐行对应，供 P3 测试设计逐批取用。

| 批 | BDD | 设计节 | 复杂度 | 一句话要点 |
|---|---|---|---|---|
| A0 | BDD-01…02 | §2.8、§2.4 | low | 修 F8（PAUSED 留痕真实落盘）；**所有 phase** 对不存在的任务目录 rc=1（`main()` 单点早检） |
| A1 | BDD-03…22 | §2.1–2.3、2.5、2.6 | high | 冻结快照与等级登记、`agate-task-init`、账本七规则、按阶段确定生效等级、judge/evidence_ref 由契约决定、创建时间系统化、ID 正则统一、**R6 差分脚本 + allowlist 交付**、**PROD_TOUCHED 扫描面扩到全部暂存 `*.md`** |
| A2 | BDD-23…35 | §2.4 | high | `agate-ci-verify` 逐提交回放 pre-commit + commit-msg、协议版本选择、merge-base 等级检查、squash/push 口径 |
| A3 | BDD-36…39 | §2.7 | medium | `agate-state-set`（phase/meta/cancel）、`check_transition` 纯函数、所有 phase 变化写事件（**含 PAUSED/READY/DONE 随本次提交入库**）、`agate-next` 不写事件、`status` 现算、**RM-AG0101 卡片块排除**、**2h.1d `git add` 失败可见** |
| A4 | BDD-40…44 | §2.9 | medium | 义务 `enforced_at`（ast 可达）+ `test`（负向控制）+ `review_output` + `scope`；基线重设 |
| B | BDD-45…51 | §3 | high | 逐文件字段契约、三校验器合并为 `agate_schema.py`、md-field-set 7 操作、`agate-config set/unset/explain`、渲染块、T1–T3 绊线、E3 |
| C | BDD-52…55 | §4 | low | `prod_touched` 必填、**T4 = 唯一安全门（`default` 口径 + 单一来源）**、否定写法阻断 + 指引（F4，规格见 §3.1） |
| D | BDD-56…60 | §5 | high | P6 `results` 与判据 D1–D10、P6.5 `criteria`、`resolve_evidence_ref` + `agate-run --task`、入库检查（RM-AG0097） |
| E | BDD-61…66 | §6 | medium | 成对声明跨文件聚合、ID 带路径前缀、`basis`（followup 只接受 DEBT 编号并双向回指）、补登记 5 标记 |
| F | BDD-67…72 | §7 | medium | UI 维度、`reviewed_bdds`、骨架标题级判定（RM-AG0085）、`pruned` 闭合（RM-AG0087）、P8 `delivery` 结构化（F12）、T2 |
| 跨批 | BDD-73…77 | §8、§10 | — | 每批独立 PR/gate/评审 + 快照登记；legacy 不变（差异限 12 项）；pytest/consistency/count-tests；基线重设写 CHANGELOG；新增 scripts 不转红 |

**批次依赖**（设计 §10、P1 §9 一致）：`A0 → A1 → {A2, B}`；A3、A4 与 A1 并行；`B → C → {D, E, F}`；**D 另依赖 `agate-run` 基线 hotfix**（I-2，不在本任务实现）。等级依赖：A1 建等级与账本；B 依赖 A1（快照单源）；C 依赖 B（`prod_touched` 字段）；D/E/F 依赖 B。**A2 另依赖 R13 的版本对齐前置**（agateon 写 `.agate-version` 或本机装 v0.79.0）。

> **BDD-01 / BDD-38 口径收窄（专家裁决，G3 处置）**：
> - **BDD-01（A0）** 的 Then 只断言「账本中真实追加一条 `prod_touched_in_paused` 事件（**写入工作区账本**，可 grep 到）」——**不再断言「随本次提交入库」**；
> - 「**committed ledger 含该事件**」的断言归 **A3**（由 **BDD-38** 一并覆盖：进入 PAUSED/READY/DONE 的转换事件随本次提交入库）；
> - **A3 的验收用例必须用真实 `git commit` + 指向 checkout 协议的 hook**（不能只手动调脚本），否则会重演「版本错位误诊」（§10 G3）。
>
> 上述是对 **P1 活基线**的措辞澄清（P1 §4 的 BDD-01/38 文本在 P1 下次触及时同步收窄；本 P2 先按此口径设计，避免留下永假判据）。

### 3.1 F4 生产接触安全门规格（BLOCKER-1 闭合，外部专家规格）

> 本规格**取代**设计 §3.6 中「T4 = 现有的 PROD_TOUCHED diff 扫描，**保持原样**」与 §4 的「T4 优先」表述（二者与 BDD-54 矛盾，且造成注册表与 T1 口径分叉）。批 C 按此实现。

1. **单一来源**：
   - `agate/rules/markers.yaml` 中 `PROD_TOUCHED` 的 `lead_variant` 由 `dash_only` **改为 `default`**（即 `lead` 口径：认粗体 / 引用块 / `*`/`+` 列表符）；
   - `agate/scripts/pre-commit-gate.py:348/355` **删除字面正则** `^\s*-?\s*\[PROD_TOUCHED\]`，改为调用 `agate_markers.pattern("PROD_TOUCHED")`；
   - 消除「注册表（`dash_only`）与 T1（`default`）口径分叉」；`markers.yaml` 的 `mk_3`（`render()` ⊂ `pattern()`）继续守护单源。
2. **扫描面**：对每个**有暂存文件的任务目录**（§2.3 规则 7），扫描**全部暂存 `*.md` 文件的新增行**（`git diff --cached -M`），**不限于声明文件**；**只排除 `AGATE_CARD` 块**（保持现状），**不额外排除**围栏 / 行内代码（安全门宁可多拦；专家实测多拦代价 = 0）。
3. **职责划分**：
   - **T4 = 唯一的 PROD_TOUCHED 安全门**（设计 §3.6 删去「保持原样」）；
   - **T1 的标记表去掉 `PROD_TOUCHED`**（避免两条路径判同一件事）。
4. **否定写法** `[PROD_TOUCHED]: 无` **继续阻断**（安全门 fail-safe），但报错信息专写指引：「**疑似否定写法：未触达生产请在主产出写 `prod_touched: false`，并删除正文中的标记。**」——用正则识别「这是否定」正是本任务要根除的做法，故靠**指引**而非改正则。BDD-55 按此改写。对 legacy 与现状一致（现状也拦），不属 §8 新差异。
5. **补锚（BDD-54 覆盖非声明文件面）**：在**非声明文件**（如 `P4-progress.md`）写粗体 / 引用块形式的**正向** `[PROD_TOUCHED]`，同时字段写 `prod_touched: false` → **中止提交**。
6. **威胁模型补充**：T4 拦的是「**诚实但沿用旧习惯**」的声明，**拦不住「说谎的 agent」**（想隐瞒者根本不写标记）。cso 描述的「字段 false + progress 写粗体」是**同一 agent 前后不一致**，不是对抗性绕过——仍值得拦且成本为 0，但**不应据此推断 T4 能防谎报**。防谎报需旁证（如 cmdstream），此边界设计 §1 已声明，§4 再写一句。

### 3.2 R6 双向差分交付物规格（B1 闭合，外部专家规格）

> 设计 §8「legacy 退出码与 ERROR 集合不变」是本任务对存量 137 个任务目录的唯一兼容承诺，须由脚本机械保证（不靠记忆）。批 A1 交付：

1. **接口**：`docs/design-notes/r6-differential.sh --before <rev> --after <dir> --corpus <repo>... [--allow <file>]`
   - `before` 缺省 = `merge-base HEAD origin/main` 的 `agate/`；`after` 缺省 = 工作树的 `agate/`；
   - 全部在 `mktemp -d` 副本内运行；**脚本自己核验**每个 corpus 原仓库 `git status --porcelain` 为空，否则 exit 1（把 AGENTS.md 工作流 0a 变成机械判据）。
2. **判定**：对每个 legacy 任务、每个相关 gate 比较 **(退出码, ERROR 行集合)**；差异必须匹配 `r6-allowlist.yaml`（§3.3 的机器可读规则）中的某一条，否则 exit 1。
3. **gate 命令**（只跑 agateon 自身语料，完全可复现）：`P5_r6_differential: "bash docs/design-notes/r6-differential.sh --corpus ."`。
4. **peekview 部分**：每批在 **P6** 用同一脚本加 `--corpus <peekview 副本>` 运行，输出作为**证据文件**由 **D3** 绑定（外部仓库，如实作为过程证据，**不放进 gate**）。
5. **负向用例**：从 `r6-allowlist.yaml` 删掉一条真实需要的规则 → 脚本必须变红（满足 eng 测试缺口 ①）。

### 3.3 R6 允许差异的机器可读匹配规则（`docs/design-notes/r6-allowlist.yaml`）

> 把设计 §8 的 12 项散文差异改写为**机器可读规则**（`r6-differential.sh` 依此判定「差异是否属于允许的 12 项」）。字段：`id` / `batch`（所属批）/ `kind`（差异类别）/ `gate`（出现在哪个 gate）/ `task_scope`（适用任务面）/ `match`（匹配式，对 ERROR 行或结构化信号）。

| id | 所属批 | kind | gate | task_scope | match（匹配式） | 依据（设计 §8 项） |
|---|---|---|---|---|---|---|
| D01 | A0 | `ledger_event_added` | `pre-commit` | legacy | event=`prod_touched_in_paused` | 1（缺陷修复） |
| D02 | F | `new_error` | `check-gate:P2` | legacy | `骨架声明` | 2（RM-AG0085） |
| D03 | A1 | `rc_change` | `check-gate` | specific:`T090` | `任务 ID`，rc 1→0 | 3（放宽） |
| D04 | A1 | `new_error` | `pre-commit` | non-legacy | `创建事件` / `账本` | 4（仅非 legacy） |
| D05 | D | `new_warning` | `check-gate:P6` | any | `ignore` / `证据` | 5（新 WARNING） |
| D06 | A1 | `ledger_bytes` | `pre-commit` | any | event=`gate_run`（+3 字段） | 6 |
| D07 | A3 | `ledger_bytes` | `pre-commit` | any | event=`state_transition` | 7（去重 + 补记） |
| D08 | A2 | `rc_change` | `ci-verify` | any | `回放` / FAIL | 8（F15 修复） |
| D09 | A4 | `rc_change` | `check-obligations` | any | `义务` / `baseline` | 9（§2.9） |
| D10 | A3 | `new_error` | `check-gate` | legacy | `READY`/`DONE` → `Pn` | 10（§2.3 规则 6） |
| D11 | A0 | `rc_change` | `check-gate` | any | `不存在的任务目录`，rc→1 | 11（缺陷修复） |
| D12 | A1+C | `new_error` | `pre-commit` | legacy | `PROD_TOUCHED` | 12（安全门；含 F4 否定写法误拦，**R6 单独统计并逐条列出**） |

> `match` 的具体语法（正则 / 子串 / 结构化字段）由 A1 实现 `r6-differential.sh` 时定稿；**判据**是「对每个 legacy 任务、每个相关 gate 比较 (退出码, ERROR 行集合)，差异必须匹配上表某一条，否则 exit 1」。上表即设计 §8 十二项的机器可读版本（一一对应，`batch` 为差异的归属批）。

---

## 4. 批次设计与 dispatch_plan

### 4.1 编排模式

本任务含 10 个独立子任务（每批独立 PR、独立 gate、独立评审，设计 §10），按 `static-batch` 编排。frontmatter 的 `dispatch_plan` 声明批次表（`id` + `complexity`）；批次间依赖由 §3 的依赖链约束（非扁平并行）。

> `parallel_limit: 10` 是**扁平批次表的声明上界**（gate 校验"批数 ≤ parallel_limit"）；实际并发由依赖链与"资源密集型批次默认串行"约束决定（全量 pytest / R6 差分属资源密集型，串行）。

### 4.2 批切分判据自检

- **判据一（Tracer Bullet）**：批 A0 是"可端到端验证的最小打通"（修 F8 + 不存在目录 rc），其验收锚（BDD-01/02）为冒烟级，先取得"管道确实通"的反馈；不替代任务级 P3 红灯基线。
- **判据二（Vertical Slice）**：批按**能力**切（"账本完整性"、"CI 可信回放"、"写入工具与契约单源"、"生产接触安全门"、"验收结论与证据绑定"、"成对声明"、"代理判定"），而非按技术层切；A0/A3/A4 属"系统事实与状态"能力族。
- **判据三（Architecture Fitness Functions）**：见 §6 的 `P5_fitness_*` 三条（快照冻结 + 黄金 fixture、schema 单实现等价守护）。**N2 落实**：这三个 fitness 测试（`task_data_freeze` / `task_data_golden` / `schema_single_source`）在 **P3 中先以失败状态存在**（TDD 红灯），其 `-k` 模式必须落成真实 pytest 节点名，否则 `pytest -k` 零匹配 **exit 5**（非零）。

### 4.3 tests_filter / output

**本任务级 P2 不声明 `tests_filter`/`output`**：每批是独立 PR，各批将在自己的 P2 中声明批级 `tests_filter`（只覆盖该批交付面）；本文件声明 `gate_commands.P5` 为全量回归，`gate_commands.P3` 为任务级红灯基线。批 `id` 均为 `[A-Za-z0-9]+`，满足 filename-safe。

---

## 5. 实现完成的标志（可判定）

1. 77 条 BDD 全部有对应实现与测试，P6 二值判定（PASS/FAIL）无中间态。
2. `agate/rules/task-data/LEVELS.yaml` + `level-N.yaml` 存在，快照冻结 CHECK 0 ERROR，黄金 fixture 对全部登记等级回归通过。
3. 三个新增脚本（`agate-task-init.py`/`agate-state-set.py`/`agate_schema.py`）可运行，`agate-md-field-set --list`/`explain`/`render` 可用。
4. 每批：pytest 全绿 + `check-protocol-consistency.py` 0 ERROR + `count-tests.sh` 计数不漂移 + **`r6-differential.sh` 对 agateon 语料判定通过（差异全部匹配 `r6-allowlist.yaml`）**。
5. legacy 任务的 gate 退出码与 ERROR 集合与 v0.79.0 一致（差异限 §3.3 十二项机器可读规则，第 12 项新增 ERROR 逐条列出）。
6. `gate_commands` 全部 key 可跑且各自独立记录 pass/fail。
7. 义务基线重设写入 CHANGELOG；每批新增"必须"均有脚本判据/报错路径并登记 `obligations.yaml`。
8. **`r6-differential.sh` 自身可证伪**：删掉 `r6-allowlist.yaml` 一条真实需要的规则 → 脚本变红（§3.2 负向用例）。

---

## 6. gate_commands

```yaml
gate_commands:
  P3: "python3 -m pytest"
  P5: "python3 -m pytest agate/tests/ -q --tb=no"
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_structure: "python3 agate/scripts/check-structure-consistency.py"
  P5_shellcheck: "shellcheck -S warning agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.sh"
  P5_ruff: "~/.venvs/agate-dev/bin/ruff check agate/"
  P5_platform: "python3 agate/scripts/check-platform-assumptions.py"
  P5_count: "bash agate/tests/scripts/count-tests.sh"
  P5_r6_differential: "bash docs/design-notes/r6-differential.sh --corpus ."
  P5_fitness_snapshot_freeze: "python3 -m pytest agate/tests/ -k task_data_freeze -q"
  P5_fitness_golden_fixture: "python3 -m pytest agate/tests/ -k task_data_golden -q"
  P5_fitness_schema_single_source: "python3 -m pytest agate/tests/ -k schema_single_source -q"
  P5_timeout_seconds: 600
  P5_consistency_timeout_seconds: 120
  P5_structure_timeout_seconds: 120
  P5_shellcheck_timeout_seconds: 60
  P5_ruff_timeout_seconds: 60
  P5_platform_timeout_seconds: 120
  P5_count_timeout_seconds: 300
  P5_r6_differential_timeout_seconds: 600
  P5_fitness_snapshot_freeze_timeout_seconds: 300
  P5_fitness_golden_fixture_timeout_seconds: 300
  P5_fitness_schema_single_source_timeout_seconds: 120
  project_module: "agate"
```

**说明**：

- **一 key 一命令**，无 `&&` 链路，`--strict` 不置于链路中间。`--strict-errors-only`（仅 ERROR 判失败）为日常默认。
- **值行不带行尾注释（RM-AG0092 陷阱）**：`agate-read-p5-commands.py` 对值只做 `strip('"')`（各自剥离首尾引号），**行尾注释会被并入命令串致其不可跑** ⇒ `P3`/`P5` 行不含注释，语义说明放本处：`P3` = 测试运行器（verbose，供 `check-tdd-red.py` 读取）；`P5` = 全量回归（分片口径见 AGENTS.md「测试约定」）。
- **架构适应度检查**（判据三，N2 映射）：`P5_fitness_snapshot_freeze` → **BDD-15**（快照字节 sha256 冻结 CHECK + 黄金 fixture 防代码语义回溯）、`P5_fitness_golden_fixture` → **BDD-16**（每级黄金 fixture 对全部登记等级回归）、`P5_fitness_schema_single_source` → **BDD-50**（`agate/scripts/*.py` 中不存在第二个递归 schema 校验实现）。三个 `-k` 模式必须在 P3 落成真实测试节点名（零匹配 `pytest -k` 会 exit 5）。
- `P5_r6_differential` 的脚本是 **A1 交付物**（`docs/design-notes/r6-differential.sh`，见 §3.2）：接口 `--before/--after/--corpus/--allow`，在 `mktemp -d` 副本内跑，脚本自己核验 corpus 原仓库 `git status --porcelain` 为空；gate 命令只跑 agateon 自身语料（`--corpus .`）。peekview 部分转 **P6 证据**（§3.2 第 4 点），不进 gate。
- **`P5_repro` 已移除**（专家新发现：`repro-tag0050.sh` 只打印、不断言，且其篡改全在 legacy 任务上，而 legacy 行为按 §8 保持不变 ⇒ 实现后仍会「显示绕过」且是正确结果，**永不变红**）。`repro-tag0050.sh` 保留为**证据文档**；F1–F15 的「改坏即红」由各批验收锚中的 pytest 用例承担（在**非 legacy 的 init 任务**上构造同样篡改，断言判 FAIL）。
- **P5 全量执行口径（N3）**：`P5` 为 2671 用例，按 AGENTS.md「测试约定」**分片 + `-n auto` 并行**执行（unit/regression/integration 片），故 `P5_timeout_seconds: 600` 为**分片后单条命令**的上限；完整 CI 口径（含 flaky 兜底 `--reruns`）见 `agate/tests/README.md`。

---

## 7. files_to_read（实现导航）

| path | why |
|---|---|
| `docs/design-notes/design-tag0050-task-data-contract.md` | 核心设计依据（§0–§14）；实现时逐节对照 |
| `agate-workspace/tasks/TAG0050-task-data-contract/P1-requirements.md` | 77 BDD 与 10 批的验收锚 |
| `agate/scripts/pre-commit-gate.py` | A0/A1/A3/B/C/D 的落点：hook 步骤 2g/2h、PROD_TOUCHED 扫描、`append_event` 调用、回放模式 |
| `agate/scripts/check-gate.py` | A0/A1/D/E/F：`gate_p1/p2/p6/p7/p8`、`main()`/`handlers`、`:964`、`:1450`、`dispatch_plan` 校验 |
| `agate/scripts/agate_common.py` | `append_event`(:524)、`is_new_task_for_evidence_ref`、`resolve_workspace`、`probe_python`；新增 `task_level`/`requirement_active`/`check_ledger_events` 等 |
| `agate/scripts/check-state-transition.py` | A1/A3：legacy 重开判定 + 抽 `check_transition` 纯函数 |
| `agate/scripts/agate-ci-verify.py` | A2：重写为逐提交回放（现状 `_locate_state`/`:126` 拼路径为缺陷源） |
| `agate/scripts/check-obligations.py` + `agate/rules/obligations.yaml` | A4：`enforced_at`/`test`/`review_output`/`scope` 与基线重设 |
| `agate/scripts/agate-md-field-set.py` / `agate-md-field-get.py` | B：7 种操作、系统字段现算、`JSON_FIELDS`（`dispatch_plan`） |
| `agate/scripts/agate-frontmatter-check.py` / `check-yaml-schema.py` / `agate-config.py` | B：三校验器合并为 `agate_schema.py`（含 `:104 _validate_node`） |
| `agate/rules/phases.yaml` / `agate/rules/markers.yaml` / `agate/rules/dispatch.yaml` | 字段契约、标记单源、日期门槛（F3）来源 |
| `agate/scripts/check-state-yaml.py` / `agate-state-yaml-check.py` | A1/A3：ID 正则统一（`:39`）、status 现算 |
| `agate/scripts/check-p6-evidence.py` / `check-p6-provenance.py` | A1/D：`evidence_ref` 依契约、`results` 读取、D3 证据解析 |
| `agate/scripts/check-judge-verdict.py` | D：第 4–6 条改读 `criteria` |
| `agate/tests/conftest.py` | A1：新增 `init_task()`；测试平台无关约定 |
| `agate/scripts/README.md`（「新增脚本登记面」节） | 登记面权威清单（CHECK9/SG.6/CHECK10 区分） |
| `docs/design-notes/repro-tag0050.sh` | **证据文档**（已从 `gate_commands` 移除）：复现 F1–F15 现状；R6 脚本的形态参照（`mktemp -d` 副本内运行） |
| `docs/design-notes/r6-differential.sh` + `docs/design-notes/r6-allowlist.yaml` | **A1 交付物**（B1 闭合，§3.2）：R6 双向差分的可执行判据 + §3.3 机器可读允许差异规则；接口 `--before/--after/--corpus/--allow` |
| `.github/workflows/protocol-tests.yml` | A2：`fetch-depth: 0`、job 结构、required 设置（需许可） |

---

## 8. env_constraints

```yaml
env_constraints:
  debug_env: "无独立 debug 环境；验证＝本 checkout 内 pytest 全量（分片 + -n auto）+ check-protocol-consistency.py（用本 checkout 自己的）+ r6-differential.sh 对 agateon 语料判定 + agateon/peekview 只读副本上的双向 R6 差分（peekview 部分在 P6 作为证据）"
  consistency_baseline: "0 ERROR / 410 WARNING（本 checkout 实测；WARNING 全为冻结文件，无 live WARNING）"
  isolation_check: "R6 差分与批量实验只在副本上跑（mktemp -d / cp -r），跑完核验真实仓库 git status --porcelain 为空；判据脚本有写副作用（check-judge-verdict.py 写账本），禁止对真实仓库跑批量实验。r6-differential.sh 自己核验每个 corpus 原仓库 git status --porcelain 为空，否则 exit 1"
  no_prod_env: "本任务不接触生产环境（不写 prod_env）"
  executor_env: "executor_env.platform = opencode（P1 §0 已更新；has_task_tool/has_local_runtime/network=full 同 P0-brief）"
  ci_required_permission: "把 agateon 的 gate-backstop 设为 required 需用户明确许可（A2 派发时取得）。⚠️ **required 是可信锚点强制力的硬前提**：未取得许可时 CI 回放**降级为 advisory（非锚点）**，设计宣称的『可信锚点』不成立——须在 A2 的 workflow 落地时明确声明该降级语义（cso MEDIUM-2）"
  replay_protocol: "A2 回放协议版本：逐提交读 C 树 .agate-version 且 ≥ merge-base，降级判 FAIL；agateon 未固定版本时用 merge-base 的 agate/；否则 FAIL"
  agateon_version_alignment: "R13（专家新提）**已缓解**：原风险 = 本机稳定版 v0.78.3 与设计 §2.4 回放用的 merge-base 协议（main 720c97d3 = v0.79.0）不一致 ⇒ A2 落地后回放可能误报 FAIL（同一提交、两版本、两种结果，专家实测）。**现本机已对齐 v0.79.0**（agate-install.py v0.79.0 + --adopt；AGATE_VERSION=v0.79.0，current→latest→v0.79.0），与 merge-base 协议一致。**仍保留前置条件**：把 P1 §5 的 SUGGEST『agateon 写 .agate-version』升为 A2 前置条件——理由为**防未来发版后本机再次漂移**（一次性版本对齐 vs 持久约束）。另注：git 对普通提交在 pre-commit hook **之后**重读索引，hook 内 git add **会**进入本次提交；hook 拿到 GIT_INDEX_FILE=.git/index（相对），现有 run_git 不设 cwd 故不受影响——A3 说明中注明：hook 内若在别目录调 git，须用绝对路径"
  git_hook_note: "探针纪律（G3 误诊教训）：探针必须记录实际解析到的协议版本（agate-resolve.py）；AGENTS.md『gate 工具 ≠ 检查对象』"
  e_tests: "E1 批 B 前、E2 批 D 前、E3 批 B 启用 ERROR 前、E4 批 A2 后复测（见 §11）"
```

> 边界提醒：`env_constraints` 是**声明性**字段，不自动执行；需要强制执行的约束已落到 `gate_commands`（§6）或各批 P4/P8 卡片 checklist。

---

## 9. minimal_validation

```yaml
minimal_validation:
  assumption: "新增 agate-*.py / 库文件不触发机械门禁（CHECK9/SG.6/CHECK10）；设计描述的关键缺陷现状（A0/F8/F12/F4/RM-AG0085/ID 正则）与当前代码一致；外部行为（CI 回放耗时）有既有实测"
  method: "① 把三个探针文件（agate-task-init.py/agate-state-set.py/agate_schema.py）真放进 agate/scripts/，跑 check-protocol-consistency.py 与 SG.6+consistency+登记面测试，随后删除并核验 git status；② 只读核验：check-gate 对不存在目录的 rc（逐 phase）、pre-commit-gate.py:370 append_event 元数、check-gate.py:1450 delivery 子串、:964 骨架子串、agate-state-yaml-check.py:39 ID 正则、pre-commit-gate.py:348/355 PROD_TOUCHED 字面正则 + markers.yaml dash_only；③ 外部行为验证引用 R4 实测（TAG0042 的 16 个非合并提交逐提交回放合计约 15s）"
  result: "confirmed"
  note: "① consistency 0 ERROR/410 WARNING（探针未新增），SG.6+consistency+登记面 36 passed，探针删除后 git status 干净。② check-gate 对不存在目录：P7→0（假 PASS，即 F15b）、P5→2、P1/P2/P3/P4/P6/P8→1 ⇒ A0 须逐 phase 统一为 1（§10 G1，`main()` 单点早检）；pre-commit-gate.py:370 以 3 参调用 agate_common.append_event(task_dir,event)（2 参）确认 F8；check-gate.py:1450 为 'delivery:' 子串判定确认 F12；:964 为 '## 骨架声明' 子串判定确认 RM-AG0085；agate-state-yaml-check.py:39 用 ^T[A-Z]{2}\\d+$ 确认 ID 正则不一致；pre-commit-gate.py:348/355 用字面 `^\\s*-?\\s*\\[PROD_TOUCHED\\]` 且 markers.yaml 登记 dash_only ⇒ 确认 F4 分叉（§3.1）。③ CI 回放的可信锚点依赖 git/CI 外部行为，其可行性由 R4 的 16 提交/约 15s 实测支撑（N5），非『无外部依赖』。④ B1 的 r6-differential.sh 为 A1 交付物，本 P2 不实现（§3.2）；其接口规格来自外部专家实测裁决。⑤ G3 的『真实 commit 账本 0 行』为版本错位误诊（**升级前本机 hook 为 v0.78.3**，无 2h.1d 的 git add；v0.79.0 才有；本机现已对齐 v0.79.0，主 Agent 真实 git commit 探针复验 committed ledger = 2 行、工作区干净），§2.7 措辞成立（§10 G3）。依赖的内部函数/数据转换：agate_common.append_event / check-gate handlers / agate_markers 单源。"
```

---

## 10. 设计偏差与风险登记（design_gap）

> 本 P2 **不改设计的技术决策**。以下为形式化过程中发现的**内部矛盾**或**与当前代码不符**，如实登记，交 P2 评审裁决。

| # | 类型 | 描述 | 建议去向 |
|---|---|---|---|
| **G1** | 与代码不符（范围细节） | 设计 §2.4 与 A0 锚 ② 写"不存在的任务目录 → rc=1"；实测现状**随 phase 不同**：P7→0（正是 F15b 的假 PASS）、P5→2、其余→1。 | **已裁决（eng 采纳）**：A0 实现须把**所有 phase** 统一为 1（含 P7/P5/P0/P6.5/未知 phase）；修复放 `check-gate.py` **`main()` 单点早检**（`if not os.path.isdir(task_dir): return 1`，置于 `handlers.get(phase)` 分派**之前**）。不改变设计意图，只补齐落点。 |
| **G2** | P1 与代码口径 | BDD-75 写"用例计数一致（下界 749 不被击穿）"，而 `count-tests.sh` 实测 **2671**、README 的 **749** 是 TAG0011 迁移下界（"目标 ≥ 749"）。 | P3/P5 以"计数与基线一致 + 下界 749 不被击穿"**双口径**解释；建议 P1 活基线澄清措辞。 |
| **G3** | 设计未覆盖（同域）→ **已裁决：误诊** | **RM-AG0100 作为缺陷不成立**（外部专家实测证伪）：主 Agent 探针的「真实 commit 账本 = 0 行」是**版本错位**——真实 commit 跑的是 `~/.agate/current` 的 **v0.78.3** hook（agateon 无 `.agate-version`），而 2h.1d 的账本 `git add` 是 **v0.79.0** 才加入的（`grep -c` v0.78.3=0 / v0.79.0=1）；探针比对的是 checkout 的 v0.79.0 源码（AGENTS.md「gate 工具 ≠ 检查对象」的又一实例）。**本机现已对齐 v0.79.0**（`agate-install.py v0.79.0` + `--adopt`），主 Agent 真实 `git commit` 探针复验：committed ledger = 2 行、工作区干净，账本 `git add` 正常落入本次提交——**印证误诊**。**§2.7 措辞成立，不改**。 | **裁决（专家）**：RM-AG0100 以「误诊」关闭（roadmap 已回写）。**派生真实事项归 A3**：① 进入 **PAUSED/READY/DONE** 的转换事件随本次提交入库（BDD-38；2g 在 2h.1c/d 前 `continue`，正是 A3 前移要解决的）；② 2h.1d 的 `git add` **失败须可见**（检查返回码，失败给 WARNING）。**cso BLOCKER-2 ⇒ 降为 MEDIUM-3，归 A3**。BDD-01 Then 收窄为「工作区账本」、committed-ledger 断言归 A3（§3）。A3 验收须用真实 `git commit` + 指向 checkout 协议的 hook。 |
| **G4** | 设计未覆盖（同族） | **RM-AG0101**：`check-state-transition.py` `_scan_bdd3_keyword_phases()`（`:182`）BDD-3"重派"关键词扫描误伤**注入的 `AGATE_CARD` 正文** → 每个注入 P1 卡的任务都误报；与 §2.7 转换检查 / §3.6 T1 排除面（卡片块）**同族**。 | **已裁决（eng 采纳，单 owner）**：**纳入 A3**（A3 重构该文件），扫描排除 `<!-- AGATE_CARD_START -->…<!-- AGATE_CARD_END -->` 块 + 两向回归用例（仅卡内出现「重派」不触发；`P*-progress.md` 中真实「重派」仍触发）。**不接受双 owner**。roadmap 已回写 `scheduled（并入 TAG0050 批 A3）`。 |
| **G5** | 验证面缺可执行脚本 → **已裁决：路线①改形** | 设计 §8 的"R6 双向差分"是过程描述，仓库内无现成可复用脚本；`gate_commands` 需一条可跑命令。 | **裁决（专家，路线①改形）**：A1 交付 `docs/design-notes/r6-differential.sh` + `r6-allowlist.yaml`（规格见 §3.2、§3.3）；gate 命令改 `P5_r6_differential: "bash docs/design-notes/r6-differential.sh --corpus ."`（只跑仓内语料，完全可复现）；peekview 部分转 **P6 证据**（D3 绑定）；配**负向用例**（删 allowlist 一条规则 → 脚本变红）。**不保留不可执行命令、也不改为纯过程性验收**（§8 兼容承诺须机械保证）。 |
| **G6** | 外部依赖/许可 | A2 把 `gate-backstop` 设为 required 需用户**明确许可**；批 D 依赖 `agate-run` 基线 hotfix（I-2，**不在本任务实现**）。 | A2 派发时取得许可；D 的前置 hotfix 先行（P1 §9 已登记）。 |
| **G7** | 工具面 | `dispatch_plan` **不在** `agate-md-field-set` 白名单（`GENERIC_HEADER_KEYS ∪ phases.yaml task_fields`），工具拒写 → 须手工写入 frontmatter；`agent` 亦被工具拒写（防伪造身份）。 | 记录即可，不阻断（P2 gate 不校验该键的来源；与 P1 处理 agent 的既有先例一致）。**N6**：`dispatch_plan` 属架构声明，手工写入可辩护，与「agent 声明只经工具写入」原则的张力如实登记。 |

### 10.1 BLOCKER 闭合对照（P2 retry 1）

| BLOCKER | 来源 | 闭合方式 | 验证锚 |
|---|---|---|---|
| **B1** | eng（源自 G5） | A1 交付 `r6-differential.sh` + `r6-allowlist.yaml`（§3.2/§3.3）；gate 命令改 `--corpus .`；peekview 转 P6 证据；负向用例 | §3.2；`P5_r6_differential` 可跑；删 allowlist 一条 → 脚本变红 |
| **BLOCKER-1** | cso（F4） | 单一来源（`markers.yaml` `default` + `agate_markers.pattern()`）；扫描面 = 全部暂存 `*.md` 新增行（只排除 `AGATE_CARD` 块）；T4 唯一安全门、T1 去 `PROD_TOUCHED`；否定写法阻断 + 指引；补非声明文件锚；威胁模型 | §3.1；BDD-52/53/54/55（BDD-54 覆盖非声明文件粗体面） |
| **BLOCKER-2** | cso（G3） | **降为 MEDIUM-3，归 A3**（G3 误诊关闭；派生事项 = PAUSED/READY/DONE 事件入库 + 2h.1d 失败可见） | §10 G3；A3 用真实 `git commit` + checkout 协议 hook |
| **`P5_repro`（同类）** | 专家新发现 | 从 `gate_commands` 删除；`repro-tag0050.sh` 转证据文档；「改坏即红」由各批非 legacy pytest 用例承担 | §6 说明；`gate_commands` 无 `P5_repro` key |

> 其余非阻塞项落实：eng **M2**（RM-AG0101→A3 单 owner）、**G1**（A0 `main()` 单点早检）、**N2**（fitness 测试 P3 先红）、**N3**（P5 分片）、**N4**（§8 `executor_env`）、**N5**（§9 引用 R4 回放实测）、**N7**（README 映射不带用例数）；cso **MEDIUM-2**（required 为硬前提 + 未许可降级 advisory）、**MEDIUM-4**（D3 fail-closed，区分「事件缺失」/「sha256 不匹配」）、**LOW-1**（「CI 保证留痕」限定「在 required 生效时」）、**LOW-2**（Git 父目录排除限制）。N1（BDD-75 计数双口径）沿用首版解释并建议 P1 澄清措辞。

---

## 11. E1–E4 批级约束（待测项）

| 实验 | 断言 | 完成时点 | 判据 |
|---|---|---|---|
| **E1** 引号 | `k=v`/`--json`/stdin 三种写法至少一种在各平台首次成功率 ≥ 4/5 | **批 B 前** | 达不到 → 回设计 §3.4 补"按模板文件追加"写法 |
| **E2** 往返成本 | 命令写入 + 当场校验的派发轮次/token 不高于"写散文→gate 失败→回退" | **批 D 前** | 第二种 gate 失败次数不多于第一种；token 高出 >20% 登记为代价 |
| **E3** T1 误报抽样 | 两仓各随机抽 50 条，"引述/讨论/否定"类为 0 | **批 B 启用 ERROR 前** | 不为 0 → 调整排除规则或把 P7/P8 评审稿 T1 降 WARNING |
| **E4** CI 回放耗时 | TAG0042 规模 PR 回放耗时 ≤ 现有 `protocol-tests` 最慢 job | **批 A2 后复测** | 初值：16 个非合并提交合计约 15s（R4 实测）；超限则只回放改动任务目录的提交或按任务并行 |

---

## 12. 环境隔离声明

本 P2 仅在 agateon 本 checkout 与只读副本上做只读扫描、探针实测（用完即删）与代码核验，**未接触生产环境**。

[PROD_NOT_TOUCHED]
