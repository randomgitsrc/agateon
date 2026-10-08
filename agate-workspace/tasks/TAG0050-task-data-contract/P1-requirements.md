---
phase: P1
task_id: TAG0050
type: problems
parent: P0-brief.md
trace_id: TAG0050-P1-20261006
status: draft
created: 2026-10-06
agent: analyst
risk_level: high
ceremony: full
phases: [P1, P2, P3, P4, P5, P6, P7, P8]
packages: [agate-scripts, agate-rules, agate-task-data, agate-cards, agate-roles, agate-tests, ci-workflows, docs-upgrading]
domains: [backend, cli, security]
---

# TAG0050 P1 需求基线 — 任务数据契约：结构化判定、可信写入与任务版本

> **设计依据**：`docs/design-notes/design-tag0050-task-data-contract.md`（r4 APPROVE WITH CHANGES）。
> **范围**：只改 agateon 本仓；peekview 只在**只读副本**上做 R6 双向差分。
> **本文件是活基线**：后续阶段新发现的隐含需求以 `[SCOPE+ from Pn]` 回写。

---

## 0. P0-brief 时效性质疑

已核对 P0-brief 时效性。**不命中严重漂移三条**（`task` 目标方案仍成立；`known_risks` 的"已解决前提"未被他任务解决；平台前提差异仅影响工具层、不影响方案）。逐条结论：

- `[P0_STALE: executor_env.platform 声明为 dsh，本会话实际运行于 opencode]` —— **轻微漂移**，已更新 P0-brief 字段 `executor_env.platform` → `opencode`；不影响任何 BDD，不阻塞。
- 设计基线：main `720c97d3`（v0.79.0，TAG0042 已合入），与 P0-brief 声明一致 → **无漂移**。
- consistency 基线：本 checkout 实测 **0 ERROR**；WARNING 现测 **410**（P0-brief 记 409），差额 1 条为本任务未跟踪的 `P1-progress.md` 等叙事文件的 `CHECK2-refs` 冻结 WARNING，**无 live WARNING、无 ERROR** → **无漂移**。
- F1–F15 在 v0.79.0 上仍成立（P0-brief 依据 `repro-tag0050.sh` 于 2026-10-06 实跑复现；本轮未复跑该脚本，按 P0 既有实测采信）→ **无漂移**。
- 结论：**已核对，仅 1 条轻微漂移（platform），已按"记录"处理，不阻塞 P1。**

---

## 1. 需求复述

把 agate 协议中"判定依据"从**可随手改写、又有歧义的文本**，改为**按冻结契约快照登记的结构化数据 + 机械核验**，并让**任务带版本**。分三块：

1. **判定只读结构化数据**：正则从"命中才算"的判据降级为"命中即拦"的绊线；agent 声明只经 set/append 工具写入；计数/创建时间/judge 是否必需/义务执行方式等系统事实由工具/gate 现算。
2. **契约按等级冻结**：`agate/rules/task-data/LEVELS.yaml` + `level-N.yaml`；快照文件字节 sha256 登记（consistency CHECK 拦截）；代码语义一经发布冻结（新行为起新名字）；每级黄金 fixture 在 CI 回归。
3. **任务版本**：账本首行 `task_created` 记录 `contract_level`，只升不降；无创建事件即 legacy，走旧逻辑；`level(Pk)` 按阶段确定生效等级；跨阶段判据按被引用产出所在阶段选读取器。
4. **可信锚点在 CI**：`agate-ci-verify` 改为按 `merge-base..HEAD` 的非合并提交**逐提交回放** pre-commit 与 commit-msg hook（`checkout -f` + `reset --soft`），协议版本取 C 树 `.agate-version`（≥ merge-base，降级判 FAIL），否则协议仓库用 merge-base 协议，再否则 FAIL。

**10 个批次**（A0/A1/A2/A3/A4/B/C/D/E/F），每批独立 PR、独立 gate、独立评审；新增/收紧要求的批登记新一级快照。修复实测缺陷 F1–F15，并承接 TAG0042 实施评审 I-1/I-2（证据部分）/I-4/I-5/I-6/I-7/I-8，吸收 RM-AG0085/0087/0097 与 RM-AG0059 第①项。

**边界（明确不做，设计 §12）**：不改 peekview 或其他项目；不迁移 legacy 格式；不做看板/`agate-rm`/`agate-idea`；不引入签名；不改 P0-brief 内嵌 yaml 与 judge 信息隔离扫描；不处理 `gate_layer` 消费方、`release.preset`、`agate-run` 基线比对（后者的基线缺陷由**独立 hotfix** 处理，仅作为批 D 前置条件，不在本任务实现）。

---

## 2. 隐含需求识别

| 维度 | 隐含需求 | 为什么必须 |
|---|---|---|
| **数据** | 账本是 append-only + `prev_hash` 链，任何写入工具不得破坏链；`--existing` 重建哈希链仅限"未被 git 跟踪且非改名目标且无创建事件"的账本 | 改写链会破坏审计可信；`--existing` 若放宽会被 `git mv` + 前置改写绕过"只追加" |
| **数据** | 黄金 fixture（`agate/tests/fixtures/task-data/level-N/{pass,fail}/`）随每级登记 | 冻结代码语义，拦"改渲染/判据导致在途任务被追溯" |
| **数据** | legacy 任务**零迁移**：格式、退出码、ERROR 集合不变 | 42 个 agateon + 95 个 peekview 存量任务无创建事件，一旦追溯即全量爆红 |
| **兼容** | 允许的差异仅限设计 §8 的 **12 项**，且第 12 项（legacy 也可能新增 ERROR，含 F4 否定写法误拦）须在 R6 差分中单独统计并逐条列出 | "退出码不变"承诺必须可证伪，否则无法判断是否回归 |
| **多端** | 消费方横跨：本地 3 个 hook、`check-gate`、~30 个脚本、卡片与角色文件、CI（GitHub PR/push + GitLab MR/push + squash 仓库差异） | 设计 §11 逐列约 30 个脚本 + 卡片；漏一处即判定分叉 |
| **多端** | CI 回放**不是**本仓唯一 CI：peekview 无 agate job，需按 UPGRADING 新增（给出 GitHub 示例 + GitLab 等价写法） | 可信锚点在 CI，但使用者项目形态各异 |
| **边界** | 并行写入不撞号（58 个 `P4-implementation-*.md`，含 `P4-implementation/` 目录聚合） | ID 格式 `<相对路径去 .md>:<前缀><n>`，每文件独立编号 |
| **边界** | 空值/极值：`need_confirm` 空列表即"无"；`phases` 与 `pruned.phase` 的并集必须等于快照 `phase_universe` 且不相交 | 空白与"未声明"必须区分 |
| **边界** | 回滚：状态回退时同步写 `retries`；等级只升不降，迁入后回退到更早阶段仍按原等级判定（有意取舍，可用 `--upgrade` 补救） | 否则回退会静默降级判定 |
| **边界** | 任务等级高于运行中协议最大等级 → fail-closed 提示升级 | 多人使用不同协议版本 |
| **兼容** | 现有测试：规则 1（新目录须有创建事件）会使"新建任务目录并提交"用例转红（设计预判 `test_pre_commit_hook.py` 约 26 个、`test_agate_migrate_workspace.py` 约 9 个，**以 A1 实测为准**），改用 conftest `init_task()` | 不许把已知回归当新缺陷追 |
| **前端** | **无 UI**（`domains` 不含 frontend）→ 无 UX 类别 BDD、无人工体验路径验收、无 vision 能力条目 | 本任务产出是协议脚本与规则，不含用户可见页面 |
| **安全** | 生产接触安全门（`prod_touched` 字段 + T4 正文扫描）必须对**任何有暂存文件的任务目录**执行，phase 取 HEAD 版本；T4 优先于字段 | F4/M-R4-1 实测：只改产出、不暂存 `.state.yaml` 的提交当前完全绕过安全门 |

---

## 3. 同类扫描结论（强制节）

### 3.1 扫描动作与命中

对问题涉及的关键符号扫全仓，记录命中数量 + 文件清单：

| 符号面 | 命令口径 | 命中 | 判定 |
|---|---|---|---|
| **新增脚本名** `agate-task-init` / `agate-state-set` / `agate_schema` | `grep -rn` 全仓 | 仅出现在 `docs/design-notes/design-tag0050-*.md`、`review-r1/r2/r4`、P0-brief、本任务 dispatch-context；**代码中 0 处** | 本次新建（见 3.3 实测） |
| **新增事件/字段/函数名** `task_created`/`task_adopted`/`task_upgraded`/`requirement_active`/`task_level`/`check_ledger_events`/`resolve_evidence_ref` | 全仓 | 同上，**仅设计/评审文档**；代码中 0 处 | 本次新建 |
| **判据面**：同时含 `re.(compile\|search\|match\|findall\|finditer\|fullmatch)` 与阶段产出文件名 `P[0-9](\.5)?-[a-z-]+\.md` 的 `agate/scripts/*.py` | 逐文件 `grep -cE`（见进度文件） | **30 个**（与 P0-brief 预判一致，上界） | 本任务改动的消费方逐一列于设计 §11（约 30 个脚本 + 卡片）；抽取类（`agate-extract-context` 除 :190-211 外）与协议文档自检不在范围 |
| **标记面**：`markers.yaml` 已登记标记 | 读 `agate/rules/markers.yaml` | **8 个**（SCOPE+/SCOPE_RESOLVED/DESIGN_GAP/DESIGN_GAP_REVIEWED/NEED_CONFIRM/NO_NEED_CONFIRM/PROD_TOUCHED/PROD_NOT_TOUCHED） | 批 E 补登记 5 个（BLOCKER/DEVIATION-CRITICAL/CODE_MAP_UPDATED/CODE_MAP_EXEMPT/SUGGEST），只作 T1 绊线 |
| **标记文本面**：`agate/**/*.md` 提及标记 | `grep -rEc`（11 标记任意出现） | **292 行 / 46 文件**（另一口径"唯一 file:line"=142 行；设计 §3.6 记 167 行/30 文件） | 口径差异已如实登记，不臆测；**逐行改写清单由各批 P1 给出**（设计 §3.6 明确） |
| **ID 正则不一致** | `grep -rn "T\[A-Z\]{2}"` | `agate-state-yaml-check.py:39` 用 `^T[A-Z]{2}\d+$`，与设计统一目标 `^[A-Z]+[0-9]+$` 不一致 | 本次处理（A1 统一；`T090` 由 rc=1 变 rc=0，属 §8 允许差异第 3 项） |
| **新建任务目录用例** | `grep -cE "def test_"` | `test_pre_commit_hook.py` 56 个 def；`test_agate_migrate_workspace.py` 9 个；引用 `tasks/T*` 的测试文件 10 个 | 规则 1 影响面须在 **A1 的 P1 给出逐条清单**（本 P1 登记为约束，不预先臆断条数） |

### 3.2 逐条判定

- **本次处理**：新增脚本与事件/字段/函数（3.1 前两行）；ID 正则统一（A1）；30 个判据面脚本按设计 §11 分批改；标记面 5 个补登记（E）；协议文档标记改写面按批给出逐行清单。
- **本次不处理（+理由）**：`agate-extract-context.py` 抽取类除 :190-211 外不动（不在范围）；`gate_layer` 消费方 / `release.preset` / `agate-run` 基线比对（设计 §9 建议各自单独登记 RM）；peekview 的 CI job / `.gitignore` / `.agate-version` 改动**不在本仓范围**（只在 UPGRADING 给指引）。

### 3.3 机械门禁实测（**实测，非推理** —— 本任务新增 `agate/scripts/` 文件）

登记面权威清单：`agate/scripts/README.md`「新增脚本登记面」节（已区分机械门禁与团队约定）。

**实测方法**：把本任务将新增的三个文件真放进仓库（探针，用完即删）：
`agate/scripts/agate-task-init.py`、`agate/scripts/agate-state-set.py`、`agate/scripts/agate_schema.py`（均为 `agate-*.py` / 库，**非 `check-*.py`**），随后运行：
`python3 agate/scripts/check-protocol-consistency.py` 与 `pytest agate/tests/integration/test_protocol_alignment_review.py agate/tests/integration/test_consistency.py agate/tests/unit/test_t43_check_registration_surface.py`。

**实测结果**（2026-10-06，本 checkout，HEAD `7fd9f75`）：

| 登记面 | 类型 | 实测结果 |
|---|---|---|
| ① CHECK 9 覆盖（`uncovered_gate_scripts()`，仅 glob `check-*.py` + `pre-commit-gate.{sh,py}`） | **门禁** | **CHECK 9 仍 PASS**，无新增告警 —— 印证 README"`agate-*.py` 不在门禁覆盖面内" |
| ② SG.6（`test_protocol_alignment_review.py`） | **门禁**（pytest） | **通过**（与 ① 共用同一判据） |
| ③ CHECK 10 协议文档脚本名引用漂移 | **非登记面（方向相反）** | **无新增**（新增脚本不会让 CHECK 10 报"引用了不存在的脚本"） |
| ④ `agate/scripts/README.md` 脚本索引表 | 约定 | 无需动作（有特定脚本的机械断言，不含本三文件） |
| ⑤ `agate/tests/README.md` 映射表 | 约定 | 建议在对应批补映射行 |
| ⑥ `count-tests.sh` | 自动（下界语义） | 基线 2671 个用例；新增脚本不使其转红 |
| ⑦ `CHANGELOG.md` | 任务级约定 | 各批按需写 |

**consistency 实测**：探针在位时 **0 ERROR / 410 WARNING**（基线 409，差额非探针引入）；**无 CHECK 9 新告警、无 CHECK 10 新增**。**pytest 三文件 36 passed**。
**清理核验**：探针删除后 `git status --porcelain` 仅剩 TAG0050 未跟踪的派发/进度文件，无探针残留。

**结论**：新增的 `agate-*.py` / 库文件**不触发任何机械门禁**（① 不覆盖、② 共用同判据、③ 方向相反），登记属团队约定；本任务**不新增 `check-*.py`**（§2.1 的冻结 CHECK、§2.9 的核验均为**修改既有脚本**），故 ① 覆盖面无需扩展。

### 3.4 回归拦截（同类问题未来还会新增）

- 快照冻结由 consistency 新 CHECK + 黄金 fixture 双重守护（BDD-15/16）；
- "只剩 1 个 schema 校验实现"由等价守护测试拦截（BDD-50）；
- 新增判据与卡片"必须"一律登记进新一级快照与 `obligations.yaml`，执行方式由 §2.9 机械核验（BDD-40..44）；
- `agate/scripts/README.md`「新增脚本登记面」的机械门禁与团队约定区分保持不变（本任务实测确认）。

---

## 4. BDD 验收条件

> 每条 BDD 均可二值判定（PASS/FAIL）。编号全局连续，`#### BDD-NN:` 标题格式。分组对应设计 §10 的 10 个批次。

### 批次 A0 — hotfix（F8；`check-gate` 不存在目录返回 1）

#### BDD-01: PAUSED 状态下的生产接触留痕真实落盘
- Given 任务进入 PAUSED 且本次提交写入 `[PROD_TOUCHED]`
- When pre-commit 处理该提交
- Then 账本中真实追加一条 `prod_touched_in_paused` 事件（可 grep 到），而非静默丢弃

#### BDD-02: check-gate 对不存在的任务目录返回 1
- Given 传入一个不存在的任务目录路径
- When 运行 `check-gate.py <phase> <不存在的目录>`
- Then 退出码为 1（不再返回 0 造成假 PASS）

### 批次 A1 — 契约等级与账本完整性

#### BDD-03: 追加降级事件被判 ERROR
- Given 一个含 `task_created`（等级 1）的账本
- When 追加一条使等级下降的事件并提交
- Then 判定为 ERROR

#### BDD-04: 第 2 条 task_created 被判 ERROR
- Given 账本已有首行 `task_created`
- When 再追加一条 `task_created` 并提交
- Then 判定为 ERROR

#### BDD-05: task_created 不在第 1 行被判 ERROR
- Given 账本第 1 行不是 `task_created`
- When 该账本被提交
- Then 判定为 ERROR

#### BDD-06: 未登记的 contract_level 被判 ERROR
- Given `task_created` 的 `contract_level` 不在 `LEVELS.yaml` 登记集合内
- When 该账本被提交
- Then 判定为 ERROR

#### BDD-07: 手写低等级的新任务被判 ERROR（本地检查）
- Given 新建任务目录，账本首行手写低于当前等级的 `contract_level`
- When 在本地提交
- Then 判定为 ERROR

#### BDD-08: 回填或删除 created 后 judge 仍强制（修复 F3a）
- Given 用 `agate-task-init` 创建的任务
- When 回填或删除 P1 的 `created`
- Then judge 强制要求仍然生效（不因日期改变而失效）

#### BDD-09: P6 改 judge.enabled:false 后 P6.5 仍阻断（修复 F3b）
- Given 非 legacy 任务在 P6 将 `.state.yaml` 的 `judge.enabled` 改为 false
- When 运行 P6.5 gate
- Then 仍然阻断（判定不读 `judge.enabled`，读契约 `requires`）

#### BDD-10: 回填 created 不改变 evidence_ref 强制级别（修复 F3c）
- Given 非 legacy 任务，某条缺证据引用的 PASS
- When 把 P1 的 `created` 回填为截止日之前
- Then 该 PASS 仍为阻断（rc=1），不降级为 WARNING（rc=2）

#### BDD-11: 新增无创建事件的目录判 ERROR，--existing 补写后转绿
- Given 暂存区新增一个任务目录，其账本第 1 行不是 `task_created`
- When 提交
- Then 判 ERROR；执行 `agate-task-init.py --existing <dir>` 补写创建事件后再次提交，转绿

#### BDD-12: git mv legacy 目录后仍为 legacy 且不报错
- Given 一个 legacy 任务目录（无创建事件）
- When 用 `git mv` 改名并提交
- Then 不报错，且该任务仍按 legacy 处理

#### BDD-13: 改写或删除已有创建事件的账本判 ERROR
- Given HEAD 中含有 `task_created` 或 `task_adopted` 的账本
- When 该账本被删除、截空或移走（不含改名）
- Then 判 ERROR

#### BDD-14: legacy 任务从 DONE 回到 P1 判 ERROR
- Given 一个 legacy 任务处于 DONE
- When 将其 phase 回到 P1 并提交
- Then 判 ERROR（提示用 `--adopt` 或新建任务）

#### BDD-15: 修改已发布快照或新增未登记快照判 consistency ERROR
- Given `agate/rules/task-data/` 下已发布的 `level-N.yaml` 或其登记项
- When 修改其字节，或新增快照文件但未登记到 `LEVELS.yaml`
- Then `check-protocol-consistency.py` 判 ERROR

#### BDD-16: 黄金 fixture 判定结果不变
- Given 每个已登记等级的一组黄金 fixture
- When CI 对全部已登记等级逐一运行
- Then 判定结果与登记一致、不发生变化

#### BDD-17: 任务等级高于运行中协议最大等级时 fail-closed
- Given 任务账本记录的等级高于当前运行协议 `LEVELS.yaml` 的最大等级
- When 对该任务运行判定
- Then fail-closed，并提示"协议版本低于任务等级，请升级"

#### BDD-18: 只暂存产出未改 phase 时 legacy 任务也做 PROD_TOUCHED 扫描
- Given 一个 legacy 任务，本次只暂存阶段产出、未暂存 `.state.yaml`
- When 提交，且产出正文出现 `[PROD_TOUCHED]`
- Then 执行 PROD_TOUCHED 扫描（安全门不再依赖"是否改了 phase"）

#### BDD-19: 非 legacy 任务按被暂存产出所属阶段重跑 gate（含 HEAD=READY）
- Given 非 legacy 任务 HEAD 在 P7，本次暂存的是 P6-acceptance
- When 提交
- Then 按 P6（被暂存产出所属阶段）重跑该阶段 gate；HEAD 为 READY/DONE 时同样执行

#### BDD-20: P7 迁入任务的 P4 散文缺口仍由旧读取器计数
- Given 一个在 P7 才迁入的任务，其 P4 中有散文 `[DESIGN_GAP]`
- When 校验 P7 的 `design_gap_reviews`
- Then 这些缺口仍由旧读取器计数（不被当作空集），未被覆盖则判 ERROR

#### BDD-21: 连续两次升级时各阶段取各自等级
- Given 任务在 P1 创建为 L1、在 P4 升级为 L2、在 P6 升级为 L3
- When 校验各阶段产出
- Then 每个阶段的产出按其所属阶段的 `level(Pk)` 选择快照（不统一取最高或最低）

#### BDD-22: 两仓副本 R6 差分符合设计 §8
- Given agateon 与 peekview 的只读副本
- When 按设计 §8 口径运行双向 R6 差分
- Then 结果符合 §8 允许的 12 项差异；跑完两个真实仓库 `git status --porcelain` 为空

### 批次 A2 — CI 回放（可信锚点，修复 F15）

#### BDD-23: PR 口径回放 TAG0042 的 16 个非合并提交全部 PASS
- Given TAG0042 PR（`a68d763..720c97d3`）的 16 个非合并提交，协议取 merge-base
- When 按 PR 口径逐提交回放 pre-commit 与 commit-msg
- Then 全部判 PASS

#### BDD-24: push 口径回放同样全部 PASS
- Given 同一批提交
- When 按 push 口径（`rev-list --no-merges <before>..HEAD`）回放
- Then 全部判 PASS（合并提交被跳过）

#### BDD-25: --no-verify 的违规提交判 FAIL 并指出提交
- Given 在分支上用 `--no-verify` 提交一个会被 gate 拦下的改动（暂存了 `.state.yaml`），最终 HEAD 为 READY
- When 回放
- Then 判 FAIL，并输出是哪个提交；push 口径同样判 FAIL

#### BDD-26: READY 之后只改产出的 PROD_TOUCHED 提交判 FAIL
- Given READY 之后一个 `--no-verify` 提交，只改 `P8-release.md` 且写入 `[PROD_TOUCHED]`
- When 回放
- Then 判 FAIL（安全门覆盖到不改 phase 的提交）

#### BDD-27: 缺 self-gate trailer 的协议本体提交判 FAIL
- Given 用 `--no-verify` 提交协议本体改动且 commit message 无 self-gate trailer
- When 回放（含 commit-msg hook）
- Then 判 FAIL

#### BDD-28: 删除已有创建事件账本判 FAIL；legacy 改名判 PASS
- Given 某提交删除了含创建事件的账本，另一提交对 legacy 目录做 `git mv`
- When 回放
- Then 前者 FAIL、后者 PASS

#### BDD-29: 手写低等级 task_created 并 --no-verify 提交判 FAIL
- Given 手写一条低等级 `task_created` 并用 `--no-verify` 提交
- When 回放
- Then 判 FAIL

#### BDD-30: 在途分支跨越协议升级不误报
- Given 分支在途中协议等级从 L1 升到 L2（merge-base 处仍为 L1）
- When 做 merge-base 等级检查
- Then 不误报（新增任务等级 ≥ merge-base 处最大等级即通过）

#### BDD-31: 使用者项目未写 .agate-version 判 FAIL 并给提示
- Given 一个未固定协议版本、且不含协议本体的使用者项目
- When 回放
- Then 判 FAIL，并提示"未固定协议版本，无法可信回放；请写 `.agate-version`"

#### BDD-32: PR 降级 .agate-version 判 FAIL
- Given 某提交把 `.agate-version` 固定到低于 merge-base 处的版本
- When 回放
- Then 判 FAIL（单调不降被违反）

#### BDD-33: PR 中途升级 .agate-version 不误报
- Given 分支在途正常升级 `.agate-version`
- When 逐提交读取 C 树版本并回放
- Then 不误报

#### BDD-34: 未改动任务目录的 PR 判 SKIP；squash 仓库 push 只做账本检查
- Given 一个没有改动任何任务目录的 PR，以及一个 squash 合并仓库的 push
- When 运行 ci-verify
- Then PR 输出 `SKIP:` 并附原因；squash 仓库 push 只做账本前缀与事件规则检查

#### BDD-35: E4 耗时在可接受范围
- Given 改造后的 `agate-ci-verify --base`
- When 在副本上回放 TAG0042 规模的 PR 与一个 hotfix 类 PR
- Then 记录被回放提交数、总耗时与单提交耗时分布；TAG0042 规模不超过现有 `protocol-tests` 最慢 job 的耗时

### 批次 A3 — state-set 与状态事实

#### BDD-36: agate-state-set phase 以 HEAD 为基准拒绝非法转换
- Given `agate-state-set.py <dir> phase <Pn>` 以 HEAD 版本为 `old_state`
- When 连续两次 state-set 后提交
- Then 非法转换被拒绝；提交时的判定结果与工具当时的判定一致

#### BDD-37: 回退时同时写入 retries
- Given 一次状态回退
- When 执行 state-set
- Then 同时写入 `retries[...]`，满足现有转移规则

#### BDD-38: 进入 READY/PAUSED 写 state_transition；agate-next 不再写
- Given 进入 READY 或 PAUSED 的转换
- When 提交
- Then 账本写入 `state_transition`（随本次提交入库）；`agate-next` 通过时只打印建议、不再追加事件

#### BDD-39: 非 legacy 任务写 status 判 ERROR，读取方现算
- Given 非 legacy 任务的 `.state.yaml` 写入了 `status`
- When 校验
- Then 判 ERROR；读取方得到的 status 值由 phase/cancelled 现算

### 批次 A4 — 义务执行方式机械核验（修复 F13）

#### BDD-40: check-obligations 对 F13 的 4 条 M 报 ERROR
- Given F13 中不在必经路径的 4 条 M（OBL-P2-12、X-10、X-17、X-19）
- When 运行 `check-obligations.py`
- Then 对这 4 条报 ERROR

#### BDD-41: M 项缺 test 或 test 节点不存在判 ERROR
- Given 一条 M 义务缺少 `test` 字段，或其 `test` 指向的 pytest 节点不存在
- When 运行 check-obligations
- Then 判 ERROR

#### BDD-42: 负向控制——删掉判据分支使 test 转红
- Given OBL-P8-02（以及本批抽样的其他 M 项）对应的判断分支
- When 以 mutation 方式删掉该分支
- Then 其 `test` 转红

#### BDD-43: 缺 review_output 的 R 判 ERROR
- Given 一条 R 义务没有指向合格评审产出（check-gate 会校验其存在且 `agent ≠ main`）
- When 运行 check-obligations
- Then 判 ERROR；找不到合格评审产出的 R 改标为 C

#### BDD-44: 改标并重设基线后转绿；之后 M 占比下降仍 FAIL
- Given 首次核验后改标 F13 的 4 条 M 与若干 R，并以 `baseline.reset` 显式重设
- When 再次运行 check-obligations
- Then 转绿；此后 M 占比下降仍判 FAIL（恢复"只增不减"）

### 批次 B — 写入工具与契约单源

#### BDD-45: md-field-set 7 操作与 agate-config set/unset/explain 往返用例
- Given `agate-md-field-set.py` 的 set/append/upsert/remove/--list/explain/render 与 `agate-config.py` 的 set/unset/explain
- When 对每种操作各写一次往返用例
- Then 全部通过

#### BDD-46: 系统字段拒写，get 返回现算值
- Given 一个 `writer: system` 的字段（如 P6 的 `pass`/`fail`）
- When 尝试写入，并经 md-field-get 读取
- Then 写入被拒并说明来源；读取返回按 `derive` 现算的值（忽略文件里的值）

#### BDD-47: 缺 frontmatter 判 ERROR（修复 F10）
- Given 一个非 legacy 任务的声明文件没有 frontmatter 块
- When 校验
- Then 判 ERROR（不回退到正文正则）

#### BDD-48: 渲染块被手改判 ERROR，CRLF 行为一致
- Given 一个 `<!-- AGATE:RENDER ... -->` 渲染块
- When 手改其内容（或在 CRLF 换行下校验）
- Then 判 ERROR 并给出 `agate-md-field-set.py render` 修复命令；两侧 CRLF 规范化为 LF 后逐字节比较，CRLF 下行为一致

#### BDD-49: 报错附带的修复命令真能执行并转绿
- Given gate 报错附带的修复命令
- When 照抄执行后重新校验
- Then 转绿

#### BDD-50: 只剩 1 个 schema 校验实现
- Given `agate/scripts/*.py`
- When 运行等价守护测试
- Then 不存在第二个递归 schema 校验实现（三处统一调用 `agate_schema.py`）

#### BDD-51: E3 误报为 0 或已落实降级方案
- Given T1 绊线在两仓语料上的命中行
- When 各随机抽 50 条人工分类
- Then "引述/讨论/否定"类为 0；若不为 0，已按设计 §3.6 落实"P7/P8 评审稿 T1 降为 WARNING 且声明同时写入字段"的降级

### 批次 C — 生产接触

#### BDD-52: 缺 prod_touched 判 ERROR
- Given 主产出的 frontmatter 缺少 `prod_touched`
- When 提交
- Then 判 ERROR 并附修复命令

#### BDD-53: prod_touched 为 true 且不在 PAUSED 时中止提交
- Given 主产出 `prod_touched: true`，当前不在 PAUSED
- When 提交
- Then 中止提交

#### BDD-54: 正文粗体 PROD_TOUCHED、字段 false 仍中止
- Given 正文写粗体 `**[PROD_TOUCHED]**`，而字段写 `prod_touched: false`
- When 提交
- Then 仍中止提交（T4 优先于字段）

#### BDD-55: [PROD_TOUCHED]: 无 否定写法继续阻断并给专门指引
- Given 正文出现否定写法 `- [PROD_TOUCHED]: 无`
- When 提交
- Then 仍中止提交（否定写法由 T4 安全门继续阻断，fail-safe），报错信息给出专门指引：「疑似否定写法：未触达生产请在主产出写 `prod_touched: false`，并删除正文中的标记」，修复 F4

> [BASELINE_CHANGE: P2 §3.1 F4 规格取代旧口径，经主 Agent 批准] 原 Then「T1 将其指向字段（不误当声明中止）」与新规格方向相反——T1 标记表已去掉 `PROD_TOUCHED`，否定写法改由 **T4 继续阻断**（靠专门指引而非改正则）。Given/When 意图不变。

### 批次 D — 验收结论与证据绑定

#### BDD-56: F1 的 A/B/C 三种篡改全部转红
- Given P6 的 A（正文把 BDD-5 改 FAIL）、B（删掉一条 BDD 及其证据）、C（把 BDD-5 改写成重复的 BDD-4）
- When 运行 P6 判据（D1/D2）
- Then 三种篡改全部转红

#### BDD-57: 证据被 ignore 判 ERROR
- Given 一条证据引用指向被 `.gitignore` 忽略的文件
- When 校验（pre-commit 中还要求已跟踪或已暂存）
- Then 判 ERROR（修复 F9）

#### BDD-58: PASS 条目日志 EXIT_CODE≠0 判 ERROR
- Given 一个 PASS 条目引用的日志带 `EXIT_CODE` 尾行且值非 0
- When 校验
- Then 判 ERROR

#### BDD-59: run: 引用的 sha256 与事件不一致判 ERROR
- Given `run:<k>` 引用的 `<task>/runs/<k>.log`
- When 其 sha256 与 `cmd_run` 事件记录不一致
- Then 判 ERROR

#### BDD-60: extract-context 计数等于现算值
- Given 非 legacy 任务
- When 运行 `agate-extract-context.py`
- Then 其计数等于按字段现算的值

### 批次 E — 成对声明

#### BDD-61: F2 转红（P7 汇总值盖不住 BLOCKER）
- Given P7 正文追加 `- [BLOCKER] …` 而 frontmatter 写 `blocker_count: 0`
- When 运行 P7 判据
- Then 转红（计数为系统字段，不被汇总值盖住）

#### BDD-62: P2-review 与 P4 分文件中的声明都被聚合
- Given 声明字段写在 P2-review 或 P4 分文件的 frontmatter
- When gate 跨文件聚合
- Then 这些声明都被聚合到

#### BDD-63: 并行写入不撞号
- Given 多个 `P4-implementation-*.md` 并行写入
- When 各自生成 ID
- Then ID 格式为 `<相对路径去 .md>:<前缀><n>`，每文件独立编号、不撞号

#### BDD-64: 集合不相等或悬空 id 判 ERROR
- Given `scope_resolved`/`design_gap_reviews`/`code_map_reviewed` 与对应聚合结果的 id 集合不相等，或出现悬空 id
- When 校验
- Then 判 ERROR

#### BDD-65: resolved 缺证据判 ERROR
- Given 一条 `resolved` 的 blocker/deviation_critical 缺 `resolution` 或 `evidence`
- When 校验
- Then 判 ERROR

#### BDD-66: followup:DEBT<n> 中 DEBT 不存在或无回指判 ERROR
- Given `basis: followup:DEBT<n>`
- When 该 DEBT 条目不存在，或其 `source_ref` 未回指 `<task_id>:<DG id>`
- Then 判 ERROR

### 批次 F — 代理判定（含 RM-AG0085、RM-AG0087、F12）

#### BDD-67: UI 维度标 na 却无理由判 ERROR
- Given P2 的 `ui_design.dimensions.<维度>` 标 `status: na` 但没有 `reason`
- When 校验
- Then 判 ERROR

#### BDD-68: reviewed_bdds 不相等判 ERROR
- Given P1-review 的 `reviewed_bdds` 与 P1 的 BDD 集合不相等
- When 校验
- Then 判 ERROR

#### BDD-69: 骨架标题级判定回归用例
- Given `check-gate.py` 的骨架判定改为标题级匹配
- When 正文仅以散文提及"## 骨架声明"而非标题行
- Then 不被误判为"标题已存在"（回归用例通过，RM-AG0085）

#### BDD-70: 阶段集合不闭合判 ERROR
- Given `set(phases) ∪ set(pruned.phase)` 不等于快照 `phase_universe`，或两者相交
- When 校验
- Then 判 ERROR（RM-AG0087）

#### BDD-71: T2 拦下 ### BDD-1:
- Given P1 正文出现 `### BDD-1:` 等非规范标题
- When 绊线 T2 扫描
- Then 命中并指向统一格式 `#### BDD-N:`

#### BDD-72: 按 F12 方式篡改 P8 delivery 转红
- Given 删除 P8 的 `delivery` 字段，在正文写"暂不声明 delivery: 方式"
- When 运行 P8 gate
- Then 转红（`delivery` 为结构化字段，不再子串判定）

### 跨批通用验收

#### BDD-73: 每批独立 PR/独立 gate/独立评审并登记快照
- Given 任一批次合并
- When 检查该批
- Then 有独立 PR、独立 gate、独立评审；新增/收紧要求的批登记了新一级契约快照

#### BDD-74: legacy 任务的 gate 退出码与 ERROR 集合不变
- Given legacy 任务（无创建事件）
- When 运行各 gate
- Then 退出码与 ERROR 集合与 v0.79.0 一致，差异仅限设计 §8 的 12 项；第 12 项新增 ERROR 在 R6 差分中单独统计并逐条列出

#### BDD-75: 每批 pytest 全绿 + consistency 0 ERROR + count-tests 一致
- Given 任一批次
- When 运行 pytest 全量、`check-protocol-consistency.py`（本 checkout）、`count-tests.sh`
- Then pytest 全绿、consistency 0 ERROR、用例计数一致（下界 749 不被击穿）

#### BDD-76: 义务基线一次性重设写入 CHANGELOG
- Given A4 首次机械核验后 M 占比下降
- When 以 `baseline.reset: {reason, from: "60/123", to: "<新值>"}` 重设
- Then 该重设写入 CHANGELOG，之后恢复"只增不减"

#### BDD-77: 新增 agate/scripts 文件不触发既有测试转红
- Given 本任务新增的 `agate-task-init.py`/`agate-state-set.py`/`agate_schema.py`
- When 运行 consistency + SG.6 + 登记面测试
- Then 无新 ERROR/告警、测试通过（实测见 §3.3）

---

## 5. 待确认清单

`[NO_NEED_CONFIRM]`

- `[SUGGEST: A2 的 CI `gate-backstop` 设为 required 需用户明确许可；建议在 A2 派发时由主 Agent 单独向用户取得许可，本 P1 不阻塞——A0/A1 可先行，许可仅影响 A2 的 workflow 落地]`（理由：不涉及破坏性变更，属流程许可；设计 §2.4/§13 已列）
- `[SUGGEST: agateon 也写 `.agate-version`（设计 §13 建议）；若采纳，回放协议优先级②（merge-base 的 `agate/`）退为兜底]`
- `[SUGGEST: 设计 §9 的三项（`gate_layer` 消费方 / `release.preset` / `agate-run` 基线比对）各自单独登记 RM，不并入本任务]`

> 以上均为倾向项，不阻塞推进；**无未决阻塞项（NEED_CONFIRM = 0）**。

---

## 6. 裁剪说明

- `phases: [P1, P2, P3, P4, P5, P6, P7, P8]`，**不裁剪任何阶段**。
- 理由：`risk_level: high`（改协议内核 + 生产接触安全门 + CI 可信锚点 + 账本完整性），且 `ceremony: full` 要求 P7 不可裁；P3 因每批"先写失败用例并确认红"（TDD）而必需。
- `ceremony: full`：`phases` 含 P7（满足 full 的硬要求）。
- `domains: [backend, cli, security]`（不含 frontend，故无 UX 类别 BDD 与人工体验路径验收）。
- `project_phase` 不声明（缺省 established）。

---

## 7. 能力需求声明

```yaml
capability_requirements:
  - need: independent-self-gate-review
    why: 本任务改 agate/ 协议本体与脚本，每批触发 SELF-GATE，须独立评审并留 self-gate-review 痕迹
    available:
      - "agate 内置评审角色（protocol-alignment-review / design-review / review）"
    status: available

  - need: multi-repo-r6-differential
    why: 存量兼容承诺（legacy 退出码与 ERROR 集合不变）须在两仓只读副本上做双向差分验证
    available:
      - "peekview 只读副本 /home/kity/oclab/peekview（HEAD 4ea7b8f7）"
      - "本 checkout 的 /tmp 副本（跑完核验真实仓库 git status 为空）"
    status: available

  - need: ci-replay-local-validation
    why: A2 的逐提交回放须能在本地副本上复现（R4 已实测 TAG0042 的 16 个提交合计约 15 秒）
    available:
      - "本 checkout + /tmp 副本（AGATE_ROOT 显式指向选定协议）"
    status: available
```

无 `GAP`。无 `[CAPABILITY_GAP]`。

---

## 8. A0 hotfix 通道判定

**判定：A0 走 hotfix 通道（不占本任务 P0–P8 阶段）。**

依据（AGENTS.md「改动通道」三条件）：

1. **单一主题**：F8 修复（`append_event` 参数错）+ `check-gate` 对不存在任务目录返回 1 —— 一个自洽的"缺陷修复"主题，无跨模块影响（不依赖快照/等级机制）。
2. **不是 agate 任务**：A0 无独立 P0-brief/`.state.yaml`/P1-P8 产物，是一次性修复。
3. **可快速验证**：明确判据（BDD-01/02：事件真实落盘 + 不存在目录 rc=1），单测即可。

**留痕要求**：A0 碰 `agate/` 协议本体 ⇒ 触发 SELF-GATE，须在提交信息写 `self-gate-review:`（WARNING 不拦截）；F8 修复在 CHANGELOG 留痕。**先例**：TAG0042 批 0（`P0-batch0-record.md`）。
**A0 与本任务的关系**：A0 是 A1/A3 的**前提**（顺序 A0 → A1 → {A2, B}；A3、A4 与 A1 并行），但 A0 本身不占用 TAG0050 的 P1–P8。

---

## 9. 批次顺序与依赖

- **顺序**：A0 → A1 → {A2, B}；A3、A4 与 A1 并行；B → C → {D, E, F}。
- **额外依赖**：D 另依赖 `agate-run` 基线 hotfix（I-2，设计 §5 前置条件）——该 hotfix 不在本任务实现（设计 §12），仅作为 D 的前置。
- **等级依赖**：A1 建立契约等级与账本；B 依赖 A1（快照单源）；C 依赖 B（`prod_touched` 字段写入）；D/E/F 依赖 B。
- **每批合并前**：先写失败用例确认红（验收锚见设计 §10）；双向 R6 差分只在副本上跑；新一级快照通过冻结 CHECK；卡片每条"必须"都有脚本判据/报错路径并登记 `obligations.yaml`，经 §2.9 核验。

---

## 10. 义务基线一次性重设声明

A4 首次机械核验后，F13 的 4 条 M 与若干 R 会改标，M 占比随之下降。**须以 `baseline.reset: {reason, from: "60/123", to: "<新值>"}` 显式重设，并写入 CHANGELOG**，否则会被误读为质量倒退；之后恢复"只增不减"（BDD-44/76）。这是**一次性**动作，不得作为常规下降的借口。

---

## 11. 环境约束与验证预算

- **debug_env**（承 P0-brief）：无独立 debug 环境；验证＝本 checkout 内 pytest 全量 + `check-protocol-consistency.py`（用**本 checkout 自己的**）+ `repro-tag0050.sh` 改坏即红复验 + agateon/peekview 只读副本上的双向 R6 差分（`/tmp` 副本，跑完核验真实仓库 `git status` 为空）。
- **生产接触**：`[PROD_NOT_TOUCHED]` 本阶段仅在 agateon 本 checkout 与只读副本上工作，未接触生产环境。
- **R6 差分必须在副本上跑**（AGENTS.md 工作流 0a）：判据脚本有写副作用（`check-judge-verdict.py` 会往 `gate-events.jsonl` 追加事件），禁止对着真实仓库跑批量实验。
- **环境验证轮次预算**：

```yaml
verification_env: "本 checkout pytest 全量 + check-protocol-consistency.py（本 checkout）+ /tmp 上的 agateon 与 peekview 只读副本（双向 R6 差分）"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 dispatch-context 记录"
```

- **E1–E4 待测项**（exp 文档，须在对应批 P2 前完成）：E1 引号问题（批 B）、E2 往返成本（批 D 之前）、E3 T1 误报抽样（批 B 启用 ERROR 之前）、E4 CI 回放耗时（批 A2）。本 P1 登记为**约束**。

---

## 12. 关联登记与承接

- **RM**：RM-AG0099（本任务）；吸收 RM-AG0085（=DEBT0029，骨架标题级判定）、RM-AG0087（=DEBT0031，`phases`↔`pruned` 一致性）、RM-AG0097（证据日志入库）、RM-AG0059 第①项（`.state.yaml` 元数据，②③ 不在范围）。相关批次合入后核对并关闭对应 DEBT。
- **承接 TAG0042 实施评审**：I-1、I-2（证据部分）、I-4、I-5、I-6、I-7、I-8；I-3、I-9、`release.preset` 不并入（建议单独登记）。
- **修复缺陷**：F1–F15（设计 §0），BDD 覆盖每条验收锚。
- **P8 回写**：RM-AG0099 回写 `done`（RM-AG0043 硬校验）。

---

`[PROD_NOT_TOUCHED]` 本 P1 仅在 agateon 本 checkout 与只读副本上做只读扫描与探针实测，未接触生产环境。
