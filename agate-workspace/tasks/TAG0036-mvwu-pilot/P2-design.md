---
phase: P2
task_id: TAG0036
type: design
parent: P1-requirements.md
trace_id: TAG0036-P2-20260919
status: draft
created: '2026-09-19'
agent: architect
candidate_count: 3
packages:
- agate-scripts
- agate-docs
- agate-tests
domains:
- backend
ui_affected: false
dispatch_plan: {mode: static-batch, parallel_limit: 6, batches: [{id: mvwu-verdict-observer, complexity: medium}, {id: architect-batch-guidance, complexity: medium}, {id: batch-evidence-landing, complexity: low}, {id: review-anchors-and-decision-recheck, complexity: low}, {id: mvwu-glossary-and-debt-log, complexity: low}, {id: mvwu-script-registry, complexity: low}]}
---
# P2 方案设计 — TAG0036 MVWU 阶段 1 试点（RM-AG0063）

> 输入：`P1-requirements.md`（71 BDD + 口径 A-H，approved）、`P1-review.md`、`P0-brief.md`、`docs/design-notes/design-mvwu-protocol.md` v2.1。
> **P1 口径 A-H 是既定契约**：本方案只设计落地方式，**未改任何口径**；无 `[NEED_CONFIRM]`（无口径不可实现）。
> 环境隔离：本阶段只读仓库 + `/tmp` 会话草稿目录做最小验证；不改 `agate/` 任何文件；`~/.agate` 只读。`[PROD_NOT_TOUCHED]`
> 偏离派发指引 1 处（有证据）：`gate_commands` 的解释器用 `python3 -m pytest` 而非 `python -m pytest`——本机 `command -v python` rc=1（仅有 `/usr/bin/python3`），写 `python` 会重演 T075（P3 gate exit 127）；上一任务 TAG0035 同用 `python3 -m pytest`。平台中立约束（不裸 python3）只约束**测试代码**与**协议文档里的 `tests_filter` 示例**，不约束本机 gate_commands。

## 0. 影响面梳理（强制节，先于候选方案）

证据来源：本阶段 grep/读码——`check-gate.py:767-800`（`_gate_p2_dispatch_plan` 只校验 mode/parallel_limit/batches/id/complexity，不拒未知键）；`agate-md-field-get.py:160-200`（`JSON_FIELDS`、`_read_frontmatter`）；`agate_common.py:50-64 / 578-607 / 737-754`（`run_git` / `resolve_workspace` / `split_frontmatter`）；`check-protocol-consistency.py:768-846 / 847-1000 / 1161-1240`（CHECK 9 反向覆盖 / CHECK 10 / CHECK 14）；`check-platform-assumptions.py`（独立 check 参照）；`test_agate_scripts_encoding.py`、`test_tag0027_b3a_platform_name_docs.py`（存量文档断言）；`agate-debt-check.py` 与 `tech-debt.md` 末条（DEBT0042）。

### 0.1 改什么（Modify）——落到"文件 / 小节 / BDD"

| # | 文件（`agate/` 下除注明外） | 小节 / 落点 | 关联 BDD | 批 |
|---|------|------|------|----|
| M1 | `scripts/check-mvwu.py`（**新建**） | 全文，结构见 §2.2 | 4,13-42,43-56,57(被测对象),35,36,37,38,39,40 | B1 |
| M2 | `phase-cards/P2-design.md` | 「dispatch_plan 机器字段」节末（`字段契约` 列表之后、`## 影响面梳理` 之前）新增 `### batches[] 可选键：tests_filter / output 与批切分判据（TAG0036）` | 6,8,9,61,62,63 | B2 |
| M3 | 同上 | 「gate_commands 声明」节：紧接 `### env_constraints 与 gate_commands 的边界` 之后、`### \`--strict\` 反模式` 之前新增 `### 架构适应度检查（Fitness Functions，TAG0036）` | 64 | B2 |
| M4 | 同上 | 「前置条件」之后新增 `## 项目侧架构决策（decisions/，TAG0036）` + 前置条件清单追加 1 条 checklist | 66 | B2 |
| M5 | `assets/execution-roles/architect.md` | 「批次设计（强制节，TAG0014）」节**末尾**（`长命令已声明` 检查项之后、`## 返回给主 Agent` 之前）新增 `### 批切分判据与 tests_filter 写法（TAG0036）`；四条「硬规则」逐字不动 | 7,8,9,61,62,63,64 | B2 |
| M6 | `phase-cards/P4-implementation.md` | `## 产出规格` 之后、`## 新增文件核对表` 之前新增 `## 批级证据 P4-evidence（MVWU 阶段 1，不阻断，TAG0036）` | 10 | B3 |
| M7 | `assets/templates/task-files.md` | ① 阶段产出表 P4 行组（`{implementation_dir}/` 行之后）加 `P4-evidence/{batch}.log` 行；② P2 frontmatter 样例中 `# dispatch_plan:` 注释行之后加 `tests_filter`/`output` 可选键说明注释 | 11 | B3 |
| M8 | `role-system.md` | 在 `### 专家组并行评审 + 组长汇总` 之后、`## 子派发权限边界` 之前新增 `## 审查锚点：角色文件是否浅化接口（Deep Modules，TAG0036）` | 60 | B4 |
| M9 | `adr.md` | 文件头 `>` 引言块之后、首个 `---` 分隔线之前新增 `## 复审触发条件（过时不删）` | 65 | B4 |
| M10 | `phase-cards/P7-consistency.md` | `## 执行方式` 检查清单末尾追加第 6 项「架构决策落点与过时标注核对」（**核对**，不 author 正文，见 DEBT0039） | 66 | B4 |
| M11 | `CONTEXT.md` | 术语表末尾（`conftest` 行之后）**只追加**恰 5 行三列 | 59 | B5 |
| M12 | `agate-workspace/debt/tech-debt.md`（仓库根下，非 `agate/`） | 文末追加 1 条 DEBT（末条现为 DEBT0042 → 取 DEBT0043，落笔时以文件为准；schema 以 `agate-debt-check.py` 为准，抄 DEBT0041/0042 样式） | 5 | B5 |
| M13 | `scripts/README.md` | 脚本表 `check-debt.py` 行之后追加 `check-mvwu.py` 一行 | 69 | B6 |
| M14 | `tests/README.md` | 测试映射表 `check-platform-assumptions.py` 行之后追加新测试文件行（用例数 = `pytest --collect-only` 实数） | 69 | B6 |
| M15 | `CHANGELOG.md`（仓库根） | `## [Unreleased]`：替换占位句「（暂无——…）」为 `### 新增（TAG0036：…）` 小节，含 `TAG0036` | 69 | B6 |
| M16 | `tests/unit/test_check_mvwu.py` 与文档断言测试（**P3 新建**，非 P4） | 见 §7（gate_commands.P3） | 57,58 及全部文档/行为 BDD | P3 |
| M17 | `P4-protocol-alignment-review.md`（任务目录，**审查产物，非批**） | P4 收口由 protocol-alignment-review 角色产出，`agent≠main`，commit message 含 `self-gate-review:` | 71 | P4 收口 |
| M18 | `scripts/check-protocol-consistency.py` | `GATE_SCRIPT_EXEMPT` 集合（约 805-808 行）内**新增一行** `"agate/scripts/check-mvwu.py",  # 观测脚本，不挂 gate`；**不动** `SCRIPT_ALIGNMENT_ANCHORS` 锚点表与该文件其他任何内容。来源：P2 评审 B1 + 主 Agent 裁决 + P1 `[BASELINE_CHANGE]`（BDD-70 下方、§4.3 表该行）。该文件**不在**零内核清单，`P5_kernel_diff(_wt)` 清单亦**不含**它（已核对） | 70 | B1 |

### 0.2 不改什么（Not Modify）——看起来该改但决定不改

| 文件 / 范围 | 理由（含证据） |
|------|------|
| `scripts/check-gate.py`（含 `_gate_p2_dispatch_plan` 的三处 `return None` fail-open） | 零内核硬约束（BDD-3/5/67）；fail-open **只登记 DEBT（M12）不修**；`tests_filter` 为未知键，已读源码确认不被拒 |
| `scripts/agate_common.py` | 在零内核清单内（BDD-67）；`check-mvwu.py` 只 `import` 其 `run_git` / `split_frontmatter` / `resolve_workspace` |
| `scripts/agate-md-field-get.py`、`agate-frontmatter-check.py`、`check-structure-consistency.py` | 嵌套键 `tests_filter`/`output` 自然透传（已用最小验证 V3 实测）；`_TASK_FRONTMATTER_FIELDS` 仅顶层白名单（BDD-9 断言三者无 diff） |
| `rules/`（`phases.yaml`、`schema/`）、hook 三件套、`check-state-*`、`check-events.py`、`check-p6-provenance.py`、`check-judge-verdict.py`、`agate-archive-stale-outputs.py`、`pre-commit-gate.py`、`assets/review-roles/judge.md`、`dispatch-protocol.md` | BDD-12/67：`P4-evidence/` 不进 judge 白名单/目录登记/审计面；`grep -rn P4-evidence agate/rules/` 须 0 命中 |
| `assets/execution-roles/` 除 `architect.md` 外全部文件 | BDD-60：不重写既有角色行为约定 |
| `scripts/check-protocol-consistency.py` 中**除 M18 那一行外的全部内容**——尤其 CHECK 9 的 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表、CHECK 10 / CHECK 14 逻辑、`GATE_SCRIPT_EXEMPT` 既有 2 条 | 该文件**已移出 Not Modify 整体**（改动见 M18，仅 `GATE_SCRIPT_EXEMPT` 加 1 行，P2 评审 B1 + 主 Agent 裁决 + P1 `[BASELINE_CHANGE]`）；锚点表不动——`check-mvwu.py` 是观测脚本、不挂 gate，不该有 gate 锚点，豁免集合语义（"工具类脚本、无 gate 逻辑"）正合；不动其余内容以缩小 SELF-GATE 影响面 |
| `UPGRADING.md`、`scripts/agate-summary.py`、`.github/workflows/protocol-tests.yml`、`WORKFLOW.md`、`README.md`（version badge） | P1 §4.3：发布章节/漂移防护/CI 清单/hook 登记表均与不挂 gate 的观测脚本无关（BDD-68 断言 0 命中） |
| `state-machine.md` / `SETUP.md` / `orchestrator-template.md`（创建 `decisions/` 目录的语句） | P1 §4.4：缺的是"写入方"而非"创建方"，创建语句仍准确 |
| 既有 bootstrap 骨架机制（`P2-skeleton.md`、`skeleton-template.md`、`check-gate.py` bootstrap 校验） | 与 Walking Skeleton 同词不同义，⑤-d 只做消歧成文，不动机制（BDD-62） |
| 设计文档 `docs/design-notes/design-mvwu-protocol.md` | §5.1.1 的"边界不可归属→UNKNOWN"与 P1 有意偏离已在 P1 §2-5 声明，阶段 2 复议；本任务不回改设计文档 |
| 历史任务目录（`TAG00[0-2]*`、`TAG003[0-5]*`）、`P4-evidence/` 样本、`decisions/` 内容 | BDD-68 / P0 out-of-scope：不回填、不造样本、不预填决策文件 |

### 0.3 风险在哪（Risk）——每条配缓解

| # | 风险 | 缓解 |
|---|------|------|
| R1 | **CHECK 10 顺序**：任一协议文档（CONTEXT/scripts README/phase-cards/CHANGELOG）出现 `check-mvwu.py` 而脚本不存在 → ERROR（已在 scratch 副本实测：`❌ 引用了不存在的脚本: check-mvwu.py [agate/CONTEXT.md:38]`） | 批序：B1 先于/同 commit 于其余批（§6 波次）；无论用户裁决逐批还是合并 commit 均成立；P4 每批落盘后本地跑 `P5_consistency` |
| R2 | **CHECK 9 反向覆盖 / `test_sg_6` 对新增脚本的反应**（**已缓解**）：`glob("check-*.py")` 命中未入锚点表且未入 `GATE_SCRIPT_EXEMPT` 的新脚本 → `CHECK9-coverage` WARNING +1，且既有测试 `test_sg_6_check9_anchor_table_covers_all_gate_scripts` 由绿转红（P2 评审 B1 实测复现） | **M18**：`GATE_SCRIPT_EXEMPT` 加 `check-mvwu.py` 一行（主 Agent 已裁决，P1 已落 `[BASELINE_CHANGE]`）。本轮实测（§9 V6b）：副本放空 `check-mvwu.py` + M18 → `test_sg_6` 绿（`test_protocol_alignment_review.py` 8 passed）、`check-protocol-consistency.py --strict-errors-only` 的 WARNING 计数与基线同为 30（`CHECK9-coverage` **0 新增**）、rc=0。P5 验收口径：`CHECK9-coverage` 0 新增 + `test_sg_6` 绿 |
| R3 | **CHECK 14 平台词**：`agate/*.md` 顶层叙述面（含 `role-system.md`、`adr.md`）出现裸词 `task` / `goal` / `workflow` / `DSH` / `OpenCode` / `Claude Code` / `ralph`（大小写敏感、词边界）即 ERROR，代码围栏内豁免（`check-protocol-consistency.py:1161-1240`）。M8/M9 新文字最易踩 | B4 implementer 硬约束：M8/M9 正文用"任务/目标/流程"，**禁裸词**；`tasks/`、`task_id` 因词边界不命中；落盘后立刻跑 `P5_consistency`。phase-cards/`assets/` 不在 CHECK 14 扫描面（`CONTEXT.md` 整文件豁免） |
| R4 | **平台假设扫描（R2/R4 规则）**：新测试文件（`agate/tests/**/*.py`）不得出现命令位置裸 `python3` 或 `/tmp` 字面量，也须满足 `test_agate_scripts_encoding` 的"每个 `open(`/`.read_text(` 带 `encoding=`" | 给 P3 的硬约束（§7）：解释器用 `python_exe` fixture / `sys.executable`；`tmp_path`；含 `python3` 字样的断言用 fragment 拼接（照 `test_check_platform_assumptions.py` 写法）；`@pytest.mark.windows_smoke` 加在文件首个用例 |
| R5 | **git 基线依赖型负向断言不能进 CI 单测**：BDD-3/5/9/12/67/68② 用 `git diff <merge-base HEAD main>`；CI 浅克隆/无本地 `main` 时 merge-base 不可得 → 单测在 CI 红 | 这些断言落 `gate_commands.P5_*`（本机 worktree 有 `main`，已验证四条 `git diff --exit-code` 现为 rc=0）；P3 单测只做**纯文件读取**型断言（BDD-6/7/8/10/11/59-66 字面标记、BDD-68① `grep`、BDD-12 `grep P4-evidence agate/rules/`） |
| R6 | **ADR-001（主 Agent 不写产出）张力**：P1 BDD-10 规定"由主 Agent 在该批 commit 前运行 `tests_filter` 后写入"`P4-evidence` | M6 卡片措辞限定为"**机械转录**命令运行结果（重定向/脚本落盘，非撰写内容）"，不写成主 Agent 撰写产出；protocol-alignment-review（A7）预期检查此点，B3 implementer 须自备措辞论证 |
| R7 | **双源/多源漂移**：`tests_filter` 写法在 M2、M5、M6、M7 四处出现 | 权威源 = M2（字段契约）；M5 写"如何选"并**引用** M2 不复述契约；M6 只写证据文件格式；M7 只写一行登记与注释；P3 文档断言测试对各处固定字面标记（BDD-6/7/9/10/11） |
| R8 | **本机无 `python`**：`shutil.which("python")` 为 None，故本机上证据 `command: python -m pytest …` 会被检查 2 判 `UNKNOWN reason=command`——与"文档示例写 `python -m pytest`"（BDD-6/8 要求）方向相反 | 不改口径；M2/M5 文字须注明"解释器名以本项目 `AGATE_PYTHON`/`probe_python` 探测为准，示例仅示意"；这本身是 Q1 的真实观测信号（如实记录，不掩盖） |
| R9 | **证据路径穿越 / 符号链接逃逸**：`{batch}` 正则只防 `../`，`P4-evidence/x.log` 可为指向目录外的符号链接（BDD-21 只覆盖名字型逃逸） | §2.2 `_read_evidence` 在 `isfile` 后加 `realpath` 包含性检查（必须落在 `realpath(P4-evidence)` 内），否则按 `reason=evidence` 处理（不读取） |
| R10 | **意外异常 → traceback**：BDD-36/37 要求任何情形无 traceback | 逐批 `try/except Exception` 兜底：该批判 `UNKNOWN reason=evidence`，stderr 输出一行 `internal error` 诊断（无堆栈）；顶层仍 exit 0；**不吞** `SystemExit`/`KeyboardInterrupt` |
| R11 | **`agate_common` import 副作用**：缺 pyyaml 时 `sys.exit(1)`，落在 exit 0/2 契约之外 | 与全部 agate 脚本同前置（P0 依赖清单已含 pyyaml）；`--help` 写明；不为此特殊化 |
| R12 | **测试环境泄漏 `AGATE_TASKS_DIR`**：`resolve_workspace` 在无 `.agate.env` 时读该环境变量，会让 BDD-51（默认前缀）在开发机环境变量下漂移 | 给 P3：fixture 显式清除 `AGATE_TASKS_DIR`；git 用例 `git init -q` 后**显式** `git branch -M main`（不依赖本机 `init.defaultBranch`；conftest `GitRepo` 未指定分支名） |
| R13 | **P2 卡片被 `agate-inject-card.py` 注入 dispatch-context**：M2-M4 扩写卡片会增大后续任务的注入体量 | 新增节保持"资源地图+判据"风格、字面标记为主（这正是 ⑤-b 审查锚点自身要求）；不写步骤脚本 |
| R14 | **既有测试 / 检查对新增 `agate/scripts/check-*.py` 的反应**（B1 的根因，评审曾只实测 `test_sg_6` 与 CHECK9 两处）：任何对 `agate/scripts/check-*.py` 做"全量 glob 全覆盖"式断言的既有用例，会被新脚本触发 | ① 已全仓 grep（`grep -rnE "check-\*\.py\|glob\(.check-" agate/tests agate/scripts .github`）：**仅 2 处**消费该 glob——`agate/tests/integration/test_protocol_alignment_review.py:80`（`test_sg_6`）与 `check-protocol-consistency.py:823`（CHECK 9 反向覆盖）；`test_gate_key_suffix_audit.py:30` 只 glob `agate-*.py`，`test_check_gate.py:2072` 只 glob `*.sh`，`test_agate_scripts_encoding.py:16` 只扫 `tests/**/*.py`，均不受影响；② 抽样实测（§9 V6b）：副本放空 `check-mvwu.py`+M18 后全量 `agate/tests/` 与「无 check-mvwu」基线得**同一批**失败（均为副本缺 `agate-workspace/tasks` 等造成的 7 个伪影，非 glob 引起），无新增红灯；③ P3 把 `test_sg_6` 列为"**P4 前应已绿**的守护用例"（它现在即为绿，非新增测试）；P5 全量 pytest 中它必须保持绿 |

## 1. 候选方案

**场景类型**：常规功能 + 原型/验证（涉及 git 与文件解析行为，已做最小验证，见 §9）。设计主轴 = `check-mvwu.py` 的结构与外部依赖面；其余（⑤ 组落点、登记面）由 P1 逐条锁定，无多方案空间，落点见 §3-§5。

### 候选方案 A：单文件自包含 + `import agate_common`（选定）

- `check-mvwu.py` 一个文件，全部判定为无状态纯函数，`main()` 只做 argparse 与输出。
- P2 frontmatter：`agate_common.split_frontmatter(text)`（与 `agate-md-field-get._read_frontmatter` **同规则**：文件头 `---` 块、无块/坏 YAML → None，无正文回退）后取 `dispatch_plan` dict——**不重造 frontmatter 解析**，与 `JSON_FIELDS` 机制字节等价（V3 实测二者输出的 JSON 相同）。
- git：只用 `agate_common.run_git`（utf-8/`errors=replace`/git 缺失时按失败处理）。
- 优点：新增文件数最少（scripts/README 一行、CHECK 10 一个名字）；无进程 spawn；单测可 CLI 黑盒（`sys.executable`）+ 必要时 `importlib` 直测纯函数；不碰内核。缺点：单文件约 450 行，需靠函数分区保持可读。工作量：中。

### 候选方案 B：单文件 + 子进程调 `agate-md-field-get.py dispatch_plan`

- 读 plan 时 `subprocess.run([sys.executable, field_get], env={FILE: ...})` 取 JSON。
- 优点：与 gate 读取路径**字面同一**，天然同源。缺点：每次运行多一个进程；`FILE` 环境变量管道；找 `agate-md-field-get.py` 需要额外脚本定位（与 `AGATE_ROOT`/稳定版解析纠缠，TAG0016 教训）；"缺失/坏 YAML"要从 rc+空输出反推；单测更难隔离。同源收益在 A 已由 `split_frontmatter` 等价规则取得（并用 P3 一条**同源对拍**用例锁死）。**淘汰**。

### 候选方案 C：拆库——`check-mvwu.py`（薄入口）+ `agate_mvwu.py`（判定库）

- 优点：判定函数可被直接 import 单测（不需 importlib 加载连字符文件）。缺点：多一个脚本目录文件 = 多一处登记面（README 一行、CHECK 10 白名单形状需匹配 `agate_[a-z0-9-]+`、`agate-*` 命名会被 `test_gate_key_suffix_audit` 之类按 `agate-*.py` glob 的审计波及）；本任务只有一个消费方（YAGNI）；库文件在阶段 2 才可能被 gate 复用，届时再抽。**淘汰**。

### 权衡与选择理由

| 维度 | A 单文件 | B 子进程 field-get | C 拆库 |
|------|---------|--------------------|--------|
| 新增登记面 | 1 个脚本 | 1 个脚本 | 2 个脚本 |
| 与 gate 读取路径同源 | 规则等价 + P3 对拍 | 字面同一 | 规则等价 |
| 进程/环境依赖 | 仅 git 子进程 | git + field-get 子进程 + `FILE` env | 仅 git |
| 单测隔离难度 | 低 | 高 | 低 |
| 平台风险 | 低 | 中（脚本定位、env 传递） | 低 |
| 阶段 2 复用 | 届时再抽 | 差 | 好（但属预设计未来需求） |

**选择理由（选择 A）**：只解决 P1 列出的问题（YAGNI）；同源诉求用"规则等价 + 一条对拍用例"低成本满足；`agate_common` 只读使用，零内核改动；登记面最小，CHECK 10/CHECK 9 只多一个名字。B 的"字面同源"收益不抵其环境耦合成本；C 的复用收益属未来需求。

## 2. 选定方案 A 的详细设计

### 2.1 数据流（输入 → 处理 → 输出，每步的异常路径）

```
argv ──argparse──► (task_dir, observe)          用法错误/目标不存在 ──► stderr + exit 2（无 stdout 契约行）
task_dir/P2-design.md ─read(utf-8,CRLF→LF)─► split_frontmatter ─► dispatch_plan.batches
   缺文件 / 无 frontmatter / 坏 YAML / 无 dispatch_plan / batches 非列表或为空 ──► 1 行 MVWU_RESULT: UNKNOWN batch=- reason=tests_filter（观察表：首列 `-`）
每批 ──► judge_batch()  顺序：tests_filter → evidence → command → exit_code → git_head → expected_red（口径 B，取首个命中）
      └► 任何意外异常 ──► 该批 UNKNOWN reason=evidence + stderr 一行 internal error（无 traceback）
--observe ──► + 耗时 / evidence / commit 形态 / boundary 三列（git 单趟读取，口径 E）
stdout：默认=每批一行契约行（口径 A）；--observe=每批一行 7 列表格行（口径 H）；诊断只走 stderr；exit 0
```

### 2.2 模块结构（单文件，按函数分区；Python 3.8+，禁 `match` / `str.removeprefix` / `X | Y` 注解）

| 分区 / 函数 | 职责 | 落实的口径 / BDD |
|------|------|------|
| 常量 | `ID_RE=[A-Za-z0-9._-]+`（用 `fullmatch`，不用 `$`）、`SHA_RE`（40/64 位十六进制）、`ENV_ASSIGN_RE`、`_BUILTINS={cd,export,set,source,.}`、`REASON_ORDER` | 口径 A/B/F/G |
| `_load_batches(task_dir)` | 读 P2 → `split_frontmatter` → 返回 `list` 或 `None`（"无可判定批"） | BDD-39,1 |
| `_encode_id(x)` / `_escape_cell(s)` | 口径 D：id 按 UTF-8 字节把非 `[A-Za-z0-9._-]` 编码为 `\xNN`（`\` → `\x5c`），非字符串/空 → `?`；表格单元按 GFM 转义（`\`→`\\`、`|`→`\|`、`` ` ``→`` \` ``、`\n`/`\r` 字面化、其余 C0 → `\xNN`），缺/空/非字符串 → `-` | BDD-22,43,44 |
| `_read_evidence(task_dir, bid)` | 仅当 id 合规且不重复：拼 `P4-evidence/<id>.log` → `isfile` + `realpath` 包含性（R9）→ 以 bytes 读、严格 utf-8 解码（去 BOM）；空/仅空白/无任何 `key: value` 行 → 视为损坏。**返回三态** `MISSING` / `CORRUPT` / `dict`；逐行正则 `^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$`（`\r` 剥除，`#` 注释与空行跳过，重复键**后者覆盖**），值保持原文本 | 口径 B(evidence)，BDD-20,21,40 |
| `_first_word_ok(command, base)` | `shlex.split(command, posix=(os.name != "nt"))`；跳过前导 `NAME=value`；首词为内建集 → 直接可解析（其后不再检查）；否则 `shutil.which`，或含路径分隔符时 `isfile`+`os.access(X_OK)`（相对路径相对 git 顶层）；切分失败/无首词 → False。**永不执行任何命令** | 口径 F，BDD-15,16,17,19 |
| `_parse_list(raw)` | 值须以 `[` 开头 `]` 结尾，`yaml.safe_load` 后必须是元素全为 `str` 的 `list`；否则返回 `None`（不可解析）；键缺省由调用方取 `[]`。**空值/`~`/裸标量/`[t_a, `/`[1, 2]`/含 tag 均 → None**（V2 已跑）。元素相等 = Python `str ==`（逐字节） | 口径 C，BDD-30,31,32 |
| `_git_toplevel(task_dir)` / `_commit_exists(sha)` | `rev-parse --show-toplevel`；`SHA_RE.fullmatch` 后 `cat-file -e <sha>^{commit}`（短 sha/ref 名先被正则拒） | 口径 G，BDD-24 |
| `judge_batch(...)` | 六步流水线返回 `(verdict, reason)`；**SUGGEST-A 归口**：重复 id → 并入 `evidence` 步；"`exit_code: 0` 而 `failed_tests` 非空" → 并入 `exit_code` 步（仅当 `failed_tests` 可解析时；不可解析则落 `expected_red` 步，与口径 C 一致）。**不新增第七项检查/函数编号**；来源均为设计文档 §5.1.1 UNKNOWN 触发集（"证据缺失或损坏/路径不安全"）与 fail-closed 哲学 | 口径 A/B/C，BDD-14,15,20,21,23-29,32-34,41 |
| `_resolve_baseline(cwd)` | 依次：`symbolic-ref -q refs/remotes/origin/HEAD` → 否则 `rev-parse --verify -q refs/heads/main` → `master`；`git merge-base HEAD <ref>`；`rev-list --count <base>..HEAD == 0` 视为区间空。失败返回 `(None, "baseline: <原因>")` | 口径 E，BDD-50 |
| `_collect_range(cwd, base)` | **单趟**：`git -c core.quotepath=false log --no-merges --no-renames --name-only -z --format=%x01%H <base>..HEAD`，按 `\x01` 切、按 `\x00` 拆得 `[(sha, {files})]`（V1 已验证格式）——commit 形态与 boundary **共用这一次读取**，不再逐批逐文件 `git log -- path`（免 pathspec 注入与 N 次子进程） | 口径 E，BDD-47-54 |
| `_commit_form_boundary(...)` | `output` 须为非空 `str` 列表（归一：`\`→`/`、去 `./`）；批的触达集 = 区间内 files∩output≠∅ 的 commit；0 个或 >1 个 → `UNKNOWN`；恰 1 个 c：若另一批的触达集也含 c → `merged`，否则 `per-batch`。boundary 仅 `per-batch` 计算：`files(c) − 前缀{AGATE_TASKS_DIR 相对顶层}` 与 `set(output)` 相等 → `exact`，否则 `mismatch`；其余（`merged`/`UNKNOWN`/无 output）→ `UNKNOWN`。**verdict 不读这两列**（BDD-42，阶段 1 口径） | 口径 E/H，BDD-42,47-54 |
| `_tasks_prefix(toplevel)` | `agate_common.resolve_workspace(toplevel)` → `tasks_dir` 相对顶层的 posix 前缀（在顶层外则不排除）；`.agate.env` 的 `AGATE_WORKSPACE` 生效（BDD-52） | BDD-51,52 |
| `_fmt_duration(raw)` | 仅接受 `^\d+(\.\d+)?$`：整数值 → `8s`；非整数 → 保留 1 位小数（`8.5s`，**吸收 SUGGEST-C 的格式缺口**）；缺/不可解析 → `-` | BDD-45 |
| `render_contract` / `render_observe_row` | 契约行 `MVWU_RESULT: <V> batch=<enc-id>[ reason=<tok>]`；观察表行 `\| id \| tests_filter \| 耗时 \| evidence \| commit 形态 \| boundary \| verdict \|`（evidence 列 = 日志文件是否**存在**，与损坏与否无关，BDD-46） | 口径 A/D/H，BDD-13,43 |
| `main(argv)` | `argparse`（缺参 → exit 2；`--help` 的 description 直接复用模块 docstring）；目标目录不存在 → stderr + exit 2；`sys.stdout.reconfigure(encoding="utf-8")`（可用时）；**只读**——除 stdout/stderr 外不写任何文件、不改 `.state.yaml` | BDD-36,37,38,55 |

docstring/`--help` 必须逐字含三条已知局限声明（吸收 SUGGEST-C 的"固定字面锚点"）：`仅检查首词`、`不比对 command 与 tests_filter`、`UNKNOWN 不等价于 PASS，不得作为放行依据`（BDD-17/18/35）；并写明 exit code 约定（0=任一 verdict / 2=用法或目标错误）与"观测器、不挂 gate"（BDD-36/68）。

### 2.3 git 调用面清单（全部经 `run_git`，只读）

| 用途 | 命令 | 失败降级 |
|------|------|------|
| 顶层 | `rev-parse --show-toplevel`（cwd=task_dir） | 非零 → 全部批 `git_head` 检查失败；observe 基线 `UNKNOWN` + `baseline: not a git repository` |
| 默认分支 | `symbolic-ref -q refs/remotes/origin/HEAD`；`rev-parse --verify -q refs/heads/main` / `master` | 三者皆无 → `baseline: no default branch (origin/HEAD, main, master)` |
| 基线 | `merge-base HEAD <ref>`；`rev-list --count <base>..HEAD` | 无结果 → `baseline: no merge-base`；区间空 → `baseline: empty range` |
| commit 存在 | `cat-file -e <sha>^{commit}` | 非零 → `reason=git_head` |
| 区间读取 | 见 `_collect_range` | 非零/解析空 → 该批 commit 形态与 boundary `UNKNOWN`，verdict 不受影响 |

平台无关：无 `/tmp` 字面量；所有文本读写显式 `encoding="utf-8"`；解释器相关调用无（脚本不 spawn Python）；路径用 `os.path`/`pathlib`；输出中的路径一律 posix 化。

### 2.4 被否决/收窄的实现细节

- **不做** `git log -- <每批每文件>`（N×M 次子进程 + pathspec 特殊字符风险）→ 单趟读取。
- **不用** `yaml.safe_load` 解析整个证据文件（值含 `:`/`#` 的命令会被误解析）→ 逐行 `key: value`，只对 `expected_red`/`failed_tests` 的**值**用 YAML flow 解析。
- **接受的宽松点（如实记录）**：未加引号的 flow 序列（如 `[t_a, t_b]`）能解析为字符串列表，不视为"不可解析"——口径 C 规定的是写入方契约（元素双引号包裹），"不可解析"的定义是"不是合法 flow 序列或含非字符串元素"；含逗号的未引号参数化 id 会被切碎并自然落 `FAIL`/`UNKNOWN`（保守方向）。

## 3. ⑤ 组落点（插入位置 + 字面标记）

> 字面标记 = P3 文档断言测试可 grep 的最小锚点（P1 已列，此处不加不减）。每节内容保持"资源地图 + 判据"风格（不写第 N 步式脚本——这正是 ⑤-b 审查锚点自己的判据）。

| 子项 | 文件 / 插入位置 | 必含字面标记（BDD） |
|------|------|------|
| ①④ `tests_filter` 写法（M2） | P2 卡「dispatch_plan 机器字段」节末 | `tests_filter` `可选` `双引号` `禁止全量` `expected_red` `P4-evidence/{batch}.log` `[A-Za-z0-9._-]+` `缺省` `python -m pytest`（BDD-6）；`AGATE_PYTHON` 或 `DEBT0014` 或 `不裸 python3`（BDD-8，且 `tests_filter: "…python3…"` 形态在 `agate/`（不含 tests）0 命中） |
| SUGGEST-3 `output`（M2+M5） | 同上 + architect.md | `output` `可选` `--observe` `不新增 gate 校验`（BDD-9） |
| ⑤-c 判据一/二（M2+M5） | M2 同节 + M5 新节 | `Tracer Bullet`、触发条件(≥2 批 + 关键路径)、`冒烟`、`P3 红灯批`（BDD-61）；`Vertical Slice` `业务能力` `写明理由`（BDD-63）；批 `id` 判据式表述 |
| ⑤-d Walking Skeleton（M2+M5，判据一同处） | 同上 | `Walking Skeleton` `吸收` `拒绝` `ADR-003` `P2-skeleton.md`，且声明"不是同一机制"；不新增字段/gate/模板文件；不含"已生效"（BDD-62） |
| ⑤-c 判据三（M3+M5） | M3 独立子节 + M5 引用 | `Fitness Functions` `适应度` `由项目自选` `本任务无架构适应度检查`；示例维度 ≥3（依赖方向/分层边界/循环依赖/公共 API 稳定性）；工具名若出现须带"示例/由项目自选"（BDD-64） |
| M5 `tests_filter` 选取法 | architect.md 新节 | `禁止全量` `gate_commands.P3` `红灯基线` `绿灯确认` `expected_red`（BDD-7）；四条硬规则逐字不变 |
| ⑤-e P2 侧（M4） | P2 卡「前置条件」之后 | `decisions/` `已过时`、"P2 开始前读取既有决策"、写入时机（P2 定稿含新的跨任务架构决策时落 `{AGATE_WORKSPACE}/decisions/`）；不含"必须拦截"；不规定文件名/模板（BDD-66） |
| ⑤-e P7 侧（M10） | P7 卡「执行方式」第 6 项 | 核对 `decisions/` 落点与过时标注（写入时机之一）；**核对不 author**（DEBT0039） |
| ⑤-e adr（M9） | adr.md 头部 | `已过时` `不删除` `复审` `P7`；"每次新增 ADR 时顺带复核相关旧 ADR"；无自动过期/强制 gate；既有 ADR 正文零删除行；**R3：禁裸 `task`/`goal`/`workflow`** |
| ⑤-b（M8） | role-system.md 新节 | `审查锚点` `浅化` `执行顺序` `资源地图` `正交`；无"已生效/已验证生效"；**R3：禁裸词** |
| ⑤-a（M11） | CONTEXT.md 末尾 5 行 | 术语列依次 `MVWU` / `tests_filter` / `P4-evidence` / 四态 verdict（含 `PASS`/`FAIL`/`EXPECTED_RED`/`UNKNOWN`）/ `boundary`（含 `I1`）；`MVWU` 定义含"最小可验证工作单元"；四态 verdict 含"UNKNOWN 不等价于 PASS"；"首次定义位置"每行**一个**存在的路径：`docs/design-notes/design-mvwu-protocol.md`（MVWU、boundary）、`phase-cards/P2-design.md`（tests_filter）、`phase-cards/P4-implementation.md`（P4-evidence）、`scripts/check-mvwu.py`（四态 verdict） |
| ②（M6） | P4 卡新节 | 路径 `P4-evidence/{batch}.log`；键 `command` `exit_code` `git_head`(全长) `timestamp` `expected_red`(默认 `[]`) `duration_seconds` + 可选 `failed_tests`；`node id` `双引号`；主 Agent commit 前运行后**机械转录**；`不阻断`；`filename-safe`；不进 judge 白名单；可提 `check-mvwu.py --observe` 为事后观测（BDD-10） |
| ②（M7） | task-files.md | P4 行含 `P4-evidence/{batch}.log`；样例注释含 `tests_filter` 可选说明（BDD-11） |

## 4. BDD → 落点总览（71 条全覆盖）

| BDD | 落点 |
|-----|------|
| 1,2,3,4(gate 侧) | 无新代码：既有 `agate-md-field-get.py`/`_gate_p2_dispatch_plan` 已支持；P3 加读写链路用例；BDD-3 靠既有三测试文件 + `P5_kernel_diff`；BDD-4 的 `check-mvwu` 侧在 M1 |
| 5 | M12 + `P5_debt` + `P5_kernel_diff` |
| 6,7,8,9 | M2 + M5（+ 无 diff 断言 `P5_kernel_diff`） |
| 10,11,12 | M6、M7；BDD-12 = `P5_kernel_diff` + P3 `grep P4-evidence agate/rules/` |
| 13-42 | M1 `judge_batch` 各步 / `render_contract` / `main` |
| 43-56 | M1 `_collect_range`、`_commit_form_boundary`、`_tasks_prefix`、`_fmt_duration`、`render_observe_row`；BDD-56 在 P6 真实任务目录上跑（`agate-workspace/tasks/TAG0035-gate-robustness/` 或 `TAG0034-*`，摘录进 `P6-evidence/`） |
| 57,58 | P3 测试文件（含 `windows_smoke`）；`P5_windows_smoke` |
| 59 | M11 | 
| 60 | M8 + `P5_roles_diff` |
| 61-64 | M2/M3/M5 |
| 65,66 | M9、M4、M10 |
| 67,68 | `P5_kernel_diff` / `P5_kernel_diff_wt` / `P5_history_untouched`；68① 为 P3 纯文件断言 |
| 69 | M13-M15（B6） |
| 70 | `P5` / `P5_consistency` / `P5_ruff` / `P5_count`；**落点 M18**（`GATE_SCRIPT_EXEMPT` 加一行，使 `test_sg_6` 为绿、`CHECK9-coverage` 0 新增，见 R2/R14） |
| 71 | M17（P4 收口） |

## 5. 新脚本登记面（P1 §4.3 逐项落实）

| 登记面 | 改动点 | BDD | 批 |
|--------|--------|-----|----|
| `agate/scripts/README.md` | 脚本表新增 `check-mvwu.py` 行：观测、不阻断、不挂 gate；`--observe`；exit 0=任一 verdict / 2=用法或目标错误 | 69 | B6 |
| `agate/tests/README.md` | 映射表新增新测试文件行，用例数 = `pytest --collect-only <file>` 实数；总计以 `count-tests.sh` 为准（基线 1668，只增不减） | 69,70 | B6 |
| `CHANGELOG.md [Unreleased]` | `TAG0036` 小节：新增 `tests_filter`/`output` 可选键、`P4-evidence`、`check-mvwu.py`、⑤ 组成文、DEBT 登记；（不写"新增 WARNING"类表述：M18 已使 `CHECK9-coverage` 0 新增）；`check-protocol-consistency.py` 的 `GATE_SCRIPT_EXEMPT` 增列可在同小节一句话提及 | 69 | B6 |
| `agate/CONTEXT.md` | M11（含 `check-mvwu.py` 引用 → CHECK 10 顺序约束） | 59,70 | B5 |
| `P4-implementation.md` / `task-files.md` | M6/M7 | 10,11 | B3 |
| `check-protocol-consistency.py` `GATE_SCRIPT_EXEMPT` | 新增 `check-mvwu.py` 一行（M18；与 CHECK 9 反向覆盖 / `test_sg_6` 相关的登记面，P1 §4.3 经 `[BASELINE_CHANGE]` 纠正） | 70 | B1 |
| **不改**：`UPGRADING.md`、`agate-summary.py`、CI 清单、`WORKFLOW.md`、CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS` 锚点表 | 见 §0.2 | 68 | — |

## 6. 批次设计（本任务自身的 P4 批次；`dispatch_plan` 见 frontmatter）

**五维工作量评估**（详见「派发编排机制」）：无批产出 >3 文件、输入 >3 文件；无 high 维度 → 无强制拆分之外的额外拆分；拆批是为了"同一文件不跨批两轮"与"每批可独立验收"。**注意**：单测由 **P3 test-designer 先写红**（P3 = 测试文件，见 §7），P4 各批只交付实现/文档，故"脚本+单测"在 P4 里只剩 B1 的脚本。

| 批 id（能力名，Vertical Slice） | complexity | 交付面（≤3 文件） | 说明 |
|------|------|------|------|
| `mvwu-verdict-observer` | medium | M1 `check-mvwu.py`（单文件约 450 行）+ M18 `check-protocol-consistency.py`（`GATE_SCRIPT_EXEMPT` 加 1 行）= 2 文件（≤3） | 交付"批级验证观测能力"（六项检查 + 四态 verdict + `--observe`，含其被 CHECK 9 / `test_sg_6` 正确豁免）。M18 仅 1 行改动，**complexity 维持 medium**（不降 low：M1 是 450 行口径落地，主复杂度在 M1）。**不再拆为"默认模式 / observe 两批"**：两者同改一个文件，违反"同一文件不跨批两轮"；medium 因 1 文件 + 口径全由 P1 锁定 + P3 已有红灯测试 |
| `architect-batch-guidance` | medium | M2-M5：`phase-cards/P2-design.md`、`assets/execution-roles/architect.md`（2 文件） | 交付"architect 批次设计引导能力"：`tests_filter`/`output` 写法 + 批切分判据一/二/三（Tracer Bullet / Vertical Slice / Fitness Functions）+ P2 开始前读取 `decisions/`。**批 id 由 `tests-filter-authoring-guidance` 更名为 `architect-batch-guidance`**（评审 N2：原名只覆盖 `tests_filter`，与交付内容名实不符；按 P1 判据二 id 须回答"交付什么能力"）；P2 卡的全部改动（含 ⑤-e 的 P2 侧 M4）**归此批**以守"同一文件一批" |
| `batch-evidence-landing` | low | M6 `P4-implementation.md`、M7 `task-files.md`（2 文件） | 交付"主 Agent 知道往哪写、写什么证据"的落点能力 |
| `review-anchors-and-decision-recheck` | low | M8 `role-system.md`、M9 `adr.md`、M10 `P7-consistency.md`（3 文件） | 交付"审查视角 + 决策复审"能力；**R3 硬约束：M8/M9 禁裸词** |
| `mvwu-glossary-and-debt-log` | low | M11 `CONTEXT.md`、M12 `tech-debt.md`（2 文件） | 术语与 DEBT 登记（横切登记面，按技术面切——理由：登记面天然横切各能力，且须在 B1-B4 落定后才知术语终稿） |
| `mvwu-script-registry` | low | M13 `scripts/README.md`、M14 `tests/README.md`、M15 `CHANGELOG.md`（3 文件） | 脚本/测试计数/变更日志登记（同上理由；`tests/README` 用例数须等 P3 测试文件与 B1 定稿） |

**波次**（`dispatch_plan.mode = static-batch`；`parallel_limit: 6` 仅为满足 gate 的"批数 ≤ parallel_limit"约束，**实际并发 ≤3**）。下游 orchestrator 若按 `parallel_limit: 6` 读取会放宽并发，故 **P4 各批 dispatch-context 强制写明"波次并发上限 ≤3"**（评审 N1 处置，不改 `parallel_limit: 6`；备选"把 B5/B6 并入 B1/B2 使批数 ≤3"不采纳：会破坏"≤3 文件/批"与"同一文件不跨批"）：

1. **波 1**：`mvwu-verdict-observer`（先于所有引用 `check-mvwu.py` 的文档，满足 CHECK 10——R1）。
2. **波 2**（互不依赖、无共享文件，可并行 ≤3）：`architect-batch-guidance` / `batch-evidence-landing` / `review-anchors-and-decision-recheck`。
3. **波 3**（依赖前面终稿）：`mvwu-glossary-and-debt-log` / `mvwu-script-registry`。
4. **P4 收口（非批）**：`protocol-alignment-review`（产出 `P4-protocol-alignment-review.md`，BDD-71），随后主 Agent 跑 P5。

- **跨批共享件**：⑤-e 横跨 B2（P2 卡）与 B4（adr/P7 卡）——为守"同一文件不跨批"接受这一横切；两处措辞一致性（"已过时 + 被什么取代""不删除"）由 P3 文档断言 + P7 一致性检查兜底。
- **提交形态**：本设计对"逐批 commit"与"合并 commit"两种形态**均成立**（波 1 先行天然满足 CHECK 10；合并 commit 则同 commit 满足），不依赖用户裁决 A/B，P2 不替用户选。
- **dogfooding 判断（是否在本任务自身批里写 `tests_filter`/`output`）**：**不写**。理由：① 交付其写法说明的文档（B2）在 P2 时尚不存在，P2 自己先用等于"自己验证自己"，正是 P0 论证要避免的偏差；② 本任务 P3 是**任务级**红灯基线（脚本单测 + 文档断言），按批拆 `tests_filter` 会反过来约束 P3 的测试布局；③ 写了就得在本任务目录写 `P4-evidence/*.log`——一个未在任何目录登记面登记的新目录，副作用（archive/审计面）不在本任务验证范围；④ P1 §8 明确"是否把自身作样本"为可选、不强制，Q1/Q3 样本应来自后续自然任务。`[SUGGEST: 推荐本任务自身批不写 tests_filter/output，理由：避免自证偏差 + 不引入未登记的证据目录副作用；若主 Agent/用户仍要 dogfooding，最小做法仅对 mvwu-verdict-observer 一批加 tests_filter 且注意本机无 python 会得 reason=command（见 R8）]`

## 7. gate_commands

```yaml
gate_commands:
  P3: "python3 -m pytest agate/tests/unit/test_check_mvwu.py agate/tests/unit/test_mvwu_protocol_docs.py -v"
  P3_timeout_seconds: 120
  P5: "python3 -m pytest agate/tests/ --reruns 1 -n auto"
  P5_timeout_seconds: 600
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_consistency_timeout_seconds: 120
  P5_ruff: "~/.venvs/agate-dev/bin/ruff check agate/"
  P5_ruff_timeout_seconds: 60
  P5_count: "bash agate/tests/scripts/count-tests.sh"
  P5_count_timeout_seconds: 300
  P5_windows_smoke: "python3 -m pytest agate/tests/unit/test_check_mvwu.py -m windows_smoke"
  P5_windows_smoke_timeout_seconds: 120
  P5_debt: "python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md"
  P5_debt_timeout_seconds: 60
  P5_kernel_diff: "git diff --exit-code main...HEAD -- agate/scripts/check-gate.py agate/rules/phases.yaml agate/rules/schema agate/scripts/pre-commit-gate.py agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.py agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.py agate/scripts/pre-push-gate.sh agate/scripts/check-state-yaml.py agate/scripts/agate-state-yaml-check.py agate/scripts/check-state-transition.py agate/scripts/check-events.py agate/scripts/agate_common.py agate/scripts/check-p6-provenance.py agate/scripts/check-judge-verdict.py agate/scripts/agate-archive-stale-outputs.py agate/assets/review-roles/judge.md agate/scripts/agate-frontmatter-check.py agate/scripts/check-structure-consistency.py agate/scripts/agate-md-field-get.py agate/dispatch-protocol.md"
  P5_kernel_diff_timeout_seconds: 60
  P5_kernel_diff_wt: "git diff --exit-code HEAD -- agate/scripts/check-gate.py agate/rules/phases.yaml agate/rules/schema agate/scripts/pre-commit-gate.py agate/scripts/pre-commit-gate.sh agate/scripts/commit-msg-self-gate.py agate/scripts/commit-msg-self-gate.sh agate/scripts/pre-push-gate.py agate/scripts/pre-push-gate.sh agate/scripts/check-state-yaml.py agate/scripts/agate-state-yaml-check.py agate/scripts/check-state-transition.py agate/scripts/check-events.py agate/scripts/agate_common.py agate/scripts/check-p6-provenance.py agate/scripts/check-judge-verdict.py agate/scripts/agate-archive-stale-outputs.py agate/assets/review-roles/judge.md agate/scripts/agate-frontmatter-check.py agate/scripts/check-structure-consistency.py agate/scripts/agate-md-field-get.py agate/dispatch-protocol.md"
  P5_kernel_diff_wt_timeout_seconds: 60
  P5_roles_diff: "git diff --exit-code main...HEAD -- ':(exclude)agate/assets/execution-roles/architect.md' agate/assets/execution-roles"
  P5_roles_diff_timeout_seconds: 60
  P5_history_untouched: "git diff --exit-code main...HEAD -- agate-workspace/tasks/TAG00\[0-2\]\* agate-workspace/tasks/TAG003\[0-5\]\*"
  P5_history_untouched_timeout_seconds: 60
```

说明：
- 每个校验独立 key、无 `&&` 串、无 `P3_xxx` 检测键（`_timeout_seconds` 为元键，`is_gate_meta_key` 豁免）。`P3` 指向的两个测试文件名是**给 P3 的命名建议**：`test_check_mvwu.py`（BDD-57 点名）与 `test_mvwu_protocol_docs.py`（文档字面标记断言，含 BDD-6-11/59-66/68① 的纯文件断言）；P3 若拆/并文件，可按 TAG0035 先例扩展 P3 文件清单（固化的是口径，不是文件清单）。
- `P5` 全量口径与 `agate/tests/README.md` 对齐（`--reruns 1 -n auto`）；600s 取"构建类"档上限，全量套件耗时以 P5 首次实测为准。
- `P5_ruff` 的 `~`：`agate-gate-missing-cmds.py` 对**首词含 `/`** 的命令直接跳过（评审实测），故 `P5_ruff` **不产生 WARNING**；`~` 在 bash 下展开，与 P1 BDD-70 命令逐字一致，可接受。`python3`/`bash`/`git` 均在 PATH。（此条更正首版对 `~` 触发 WARNING 的不准确描述，评审 N4。）
- **引号约束（评审 B2）**：`agate-read-p5-commands.py:33` 对每个值做 `.strip().strip('"').strip("'")`，因此**值的首尾 token 不得带引号**，否则读回后引号不闭合。`P5_roles_diff` 改为把带引号的 `':(exclude)…'` 挪到中间、末 token 用无引号的 `agate/assets/execution-roles`；`P5_history_untouched` **不能用无引号裸通配**（retry #2 / 评审 B3 纠正：第 1 轮曾去引号、称"有无匹配两路等价"，该结论只对修改/新增成立，对**删除**不成立——bash 在执行前展开通配，只匹配到仍存在于工作树的目录，被删的历史目录不进 pathspec，`git diff` 反而 rc=0 误判"历史未动"），改为**反斜杠转义通配元字符**（`TAG00\[0-2\]\*`），使 bash 不展开、`shlex.split` 还原为字面 `TAG00[0-2]*`，由 git 自己按 glob 解释（与 BDD-68② 带引号 pathspec 语义一致）；转义式末 token 不以引号结尾，不触发读取器的 strip。**语义已实测**（§9 V8：删除 / 修改 / 新增历史目录均 rc=1，改 TAG0036/0037 rc=0；`P5_roles_diff` exclude 生效见 §9 V7）。P3 应加用例：`agate-read-p5-commands.py` 对本任务 P2-design.md 读回的每条 cmd 均能 `shlex.split` 不抛 `ValueError`（防复发）；另加 B3 守护（见 §13）：`P5_history_untouched` 读回命令在临时仓库执行，删除历史目录须 rc=1。
- `P5_kernel_diff` 用三点 `main...HEAD`（= 相对 merge-base，抗 main 前进）覆盖**已提交**改动，`_wt` 覆盖**未提交**改动；BDD-3/5/9/12/67 的"内核基线空 diff"断言集中于这两个 key（R5）。BDD-12 中 `dispatch-protocol.md` 整文件无 diff（P1 判"不处理"，故整文件比两段更严）。
- **架构适应度维度（判据三自评）**：本任务**无架构适应度检查**——理由：改动是新增一个无状态观测脚本 + 文档；依赖方向只有 `check-mvwu.py → agate_common`（只读 import，由 `P5_kernel_diff` 断言 `agate_common.py` 零改动间接守住公共库边界），无分层/循环依赖风险，公共 API（`MVWU_RESULT:` 契约行格式）由 P3 用例守护。
- P5 验收口径：`P5_consistency` exit 0（0 ERROR）；`CHECK9-coverage` **0 新增**（M18 已豁免，R2）；`test_sg_6_check9_anchor_table_covers_all_gate_scripts` 在全量 `P5` 中为**绿**（R14 直接验收）；`P5` skipped 仍为 2。`P5_kernel_diff` / `P5_kernel_diff_wt` 文件清单**不含** `check-protocol-consistency.py`（M18 改动它是合法的，已核对）。

## 8. 待主 Agent 处置的标记

首版关于"接受 CHECK9-coverage +1 WARNING、不改 `check-protocol-consistency.py`"的建议**作废**：P2 评审 B1 实测该前提不成立（同一原因还使 `test_sg_6` 由绿转红），**已由主 Agent 裁决为在 `GATE_SCRIPT_EXEMPT` 加 `check-mvwu.py` 一行**，并在 P1 落 `[BASELINE_CHANGE]`；本设计据此新增 M18（并入批 `mvwu-verdict-observer`），R2 改为已缓解、R14 补"既有测试对新增脚本的反应"风险。本节除 §6 的 dogfooding 建议外无其他待处置标记。

（dogfooding 建议见 §6（严格格式标记），维持不变。无 `[SCOPE+]`：M18 已被 P1 `[BASELINE_CHANGE]`（BDD-70 及 §4.3）覆盖，P1 基线无需再增 BDD；无 `[NEED_CONFIRM]`。）

## 9. minimal_validation

依赖 git / 文件解析 / 外部系统行为，**已做最小验证**（脚本均在会话草稿目录，不入库）：

```yaml
minimal_validation:
  - assumption: "merge-base..HEAD 区间语义 + 单趟 `git log --no-merges --no-renames --name-only -z --format=%x01%H` 可同时给出 commit 集与每 commit 文件集"
    method: "本仓库实跑：symbolic-ref origin/HEAD → refs/remotes/origin/main；merge-base HEAD origin/main = efb113b；rev-list --count = 4；单趟输出按 \\x01 切、\\x00 拆得 4 个 commit 及各自文件；与 `git log --format=%H <base>..HEAD -- <P1-requirements.md>` 交叉核对，均为 84d90f7"
    result: confirmed
    note: "格式 `\\x01<sha>\\x00\\n<f1>\\x00<f2>\\x00`：首个文件前有一个换行需剥；--no-renames 使 diff 与 declared output 逐路径可比"
  - assumption: "无 origin/HEAD、无 main/master 时可稳定检出并降级"
    method: "tmp 仓库仅分支 trunk：symbolic-ref rc=1、rev-parse --verify main/master rc=1；cat-file -e <40位sha>^{commit} rc=0，全零 sha rc=128；非仓库目录 rev-parse --show-toplevel rc=128"
    result: confirmed
    note: "短 sha 会被 cat-file 接受（rc=0），因此必须先用 SHA_RE.fullmatch 拒短 sha（口径 G）再调 cat-file"
  - assumption: "expected_red/failed_tests 的 flow 序列口径可用 yaml.safe_load + 类型检查实现"
    method: "20 行脚本矩阵：含 `[a,b-1]` 参数化 id 的双引号列表 → 2 元素；`[]` → 空；`t_a`/`~`/空串 → 非 flow；`[t_a, ` → yaml 错误；`[1, 2]` → 非字符串元素；`\"a\\\"b\"` 转义 → 正确还原；`[t_a, t_b]`（未加引号）→ 解析成功（宽松点，已在 §2.4 记录）；`!!python` 标签 → YAMLError"
    result: confirmed
    note: "全部与口径 C 一致；唯一宽松点为未加引号的合法 flow 序列"
  - assumption: "含 `|`、双引号、反斜杠、换行转义、`[a,b-1]` 形 id 的 tests_filter 经 agate-md-field-get.py dispatch_plan 透传；agate_common.split_frontmatter 与其等价"
    method: "样例 frontmatter 写入 `dispatch_plan` 单行 flow YAML；FILE=… agate-md-field-get.py dispatch_plan → JSON；同文件用 split_frontmatter 取 dict 再 json.dumps 对拍"
    result: confirmed
    note: "两条路径输出逐字节相同；`tests_filter` 值（含 `\\\"x\\\"`、`C:\\\\t`、`\\n`）经 json.load 还原一致；`id: \"x[a,b-1]\"` 透传"
  - assumption: "shlex 首词语义（口径 F）：跳过前导 NAME=value；复合命令只取首词；引号不闭合可判失败"
    method: "shlex.split(posix=True) 矩阵：`FOO=1 python -m pytest …`、`FOO=1 no-such-runner-xyz …`、`cd sub && no-such-runner-xyz`、`pytest \"unclosed`（ValueError）、空/空白（无首词）、`A=1 B=2 python -V`"
    result: confirmed
    note: "本机 `shutil.which('python')` 为 None（仅 python3）：证据里写 `python -m pytest` 在本机会判 reason=command（R8，如实观测，不掩盖）；Windows 上 shlex posix=True 会吞反斜杠，故设计用 `posix=(os.name != 'nt')`"
  - assumption: "新增 check-*.py 对 CHECK 9/10 的实际影响（P1 §4.3 只推理未实测）"
    method: "scratch 目录复制 agate/ 后：① CONTEXT.md 加一行引用 check-mvwu.py 而无脚本 → 报 ❌；② 放入空 check-mvwu.py → CHECK 10 ERROR 消失，出现 `CHECK9-coverage` WARNING；`agate/` 原树未动"
    result: confirmed
    note: "证实 R1（ERROR 顺序约束）与 R2 原判（未豁免时 +1 WARNING，P1 遗漏）；scratch 副本因缺根级文件另有 13 个与本任务无关的 ERROR，不作 strict-errors-only 结论依据，故此项只取 WARNING 出现与否。M18 修订后的复核见下一条 V6b"
  - assumption: "V6b（retry #1，B1 复核）：M18（GATE_SCRIPT_EXEMPT 加 check-mvwu.py）使 test_sg_6 为绿且 CHECK9-coverage 0 新增；且全仓无其他对 check-*.py 全量 glob 的既有测试/检查会被新脚本触发"
    method: "① `grep -rnE \"check-\\*\\.py|glob\\(.check-|glob\\(\\\"check-\" agate/tests agate/scripts .github` + 扩展 grep `(glob|rglob|iterdir|listdir)\\(` 于 agate/tests，人工筛选命中 scripts 目录者：仅 test_protocol_alignment_review.py:80（test_sg_6）与 check-protocol-consistency.py:823（CHECK 9）消费 check-*.py glob；test_gate_key_suffix_audit(agate-*.py)、test_check_gate:2072(*.sh)、test_agate_scripts_encoding(tests/**/*.py) 不受影响。② scratchpad 副本（rsync 除 .git/agate-workspace/tasks/archived/site 外，git init）放空 agate/scripts/check-mvwu.py 并按 M18 在 GATE_SCRIPT_EXEMPT 加一行：`pytest agate/tests/integration/test_protocol_alignment_review.py` → 8 passed（含 test_sg_6）；`check-protocol-consistency.py --strict-errors-only` 无 CHECK9-coverage 新增，WARNING 总数 30（与删除 check-mvwu 及 M18 后的基线同为 30），rc=0。③ 同副本全量 `pytest agate/tests/ --reruns 1 -n auto`：有 M18+空脚本 与 无 check-mvwu 基线 得**同一批 7 个失败**（均因副本缺 agate-workspace/tasks/TAG00xx 等历史目录/根文件，FileNotFoundError 类伪影，与 glob 无关），1659 passed / 2 skipped 一致，即新脚本未引入任何新红灯。副本用后已删除，未入库"
    result: confirmed
    note: "test_sg_6 之所以转绿：其断言是 basename 出现在 check-protocol-consistency.py 文本中，M18 的那一行（含 check-mvwu.py 字样）满足之；P3 把它列为 P4 前应已绿的守护用例（R14）"
  - assumption: "V7（retry #1，B2 修复）：P5_roles_diff / P5_history_untouched 改写后经 agate-read-p5-commands.py 读回仍语义等价，且全部 gate_commands 值 shlex.split 无 ValueError"
    method: "`P2_DESIGN=<本文件> python3 ~/.agate/scripts/agate-read-p5-commands.py`（无 --help，环境变量取路径）读回 10 条 cmd（P5、_consistency、_ruff、_count、_windows_smoke、_debt、_kernel_diff、_kernel_diff_wt、_roles_diff、_history_untouched；`_timeout_seconds` 元键按 is_gate_meta_key 被跳过）；逐条 `shlex.split` 全部通过，末 token 分别为 `agate/assets/execution-roles` 与 `agate-workspace/tasks/TAG003[0-5]*`（无引号残留）。语义：scratchpad 临时仓库（main/feat，含 architect.md/other.md 与 TAG0010/0035/0036/0037 目录）经 `bash -c` 执行读回的两条 cmd：改 architect.md → roles 0（被 exclude）；改 other.md → roles 1；改 TAG0010、TAG0035 → hist 1；改 TAG0036、TAG0037 → hist 0。本 worktree 上四条 git diff（含 _kernel_diff/_kernel_diff_wt）均 rc=0。临时仓库已删除"
    result: confirmed
    note: "首版值以引号结尾被读取器 strip 成不闭合引号（评审实跑复现）；修订后引号仅存于中间 token（`':(exclude)…'`，shlex 正确去引号），不受首尾 strip 影响；`P5_history_untouched` 的\"去引号 + bash 展开\"写法已被 retry #2 的 V8 证伪（对删除漏检），以 V8 为准"
  - assumption: "V8（retry #2，B3 修复）：P5_history_untouched 改为反斜杠转义通配后，读回 + shlex.split 得两个字面 pathspec，且对删除 / 修改 / 新增历史任务目录均 rc=1、改 TAG0036/0037 rc=0"
    method: "值改为 `git diff --exit-code main...HEAD -- agate-workspace/tasks/TAG00\\[0-2\\]\\* agate-workspace/tasks/TAG003\\[0-5\\]\\*`。`P2_DESIGN=<本文件> python3 ~/.agate/scripts/agate-read-p5-commands.py` 读回全部 10 条 cmd，逐条 `shlex.split` 通过，`_history_untouched` 得 7 token、末两个为字面 `agate-workspace/tasks/TAG00[0-2]*` 与 `agate-workspace/tasks/TAG003[0-5]*`（读取器不改反斜杠）。scratchpad 临时 git 仓库（main 含 TAG0010-x/0011-x/0031-x/0032-x/0036-x/0037-x，feat 分支各变更后提交），经 `bash -c` 执行读回的命令：同时删除 TAG0010-x 与 TAG0031-x → rc=1；仅删 TAG0011-x → rc=1；改 TAG0032-x → rc=1；给 TAG0010-x 新增文件 → rc=1；新建 TAG0033-y 目录 → rc=1；改 TAG0036-x → rc=0；改 TAG0037-x → rc=0。对照：旧写法（无引号裸通配）在\"删 TAG0010-x + TAG0031-x\"下 rc=0（漏检，复现评审 B3）。临时仓库已删除，未入库"
    result: confirmed
    note: "转义式让 bash 不展开、git 自解释 glob，删除类变更可见；第 1 轮\"去引号、有无匹配两路等价\"对删除不成立，已被本条纠正"
  - assumption: "agate-md-field-set.py 对 P2 frontmatter 的写入能力（影响本文件产出方式）"
    method: "scratch 文件实测 --list / phase / packages / created / ui_affected / candidate_count / parent"
    result: confirmed
    note: "`agent` 与 `dispatch_plan` 不在其白名单（报错拒写）→ 这两行由 Edit 单行写入 frontmatter，已报告主 Agent；list 值用空格分隔"
```

## 10. files_to_read（P4 implementer 用；每批只读本批所需）

```yaml
files_to_read:
  # ── 通用 ──
  - path: agate-workspace/tasks/TAG0036-mvwu-pilot/P1-requirements.md
    why: "口径 A-H（约 104-132 行）+ 对应批的 BDD；口径是契约，不得改"
  # ── B1 mvwu-verdict-observer ──
  - path: agate/scripts/agate_common.py:50-64
    why: "run_git 封装（utf-8/errors=replace/git 缺失按失败）——只 import 不改"
  - path: agate/scripts/agate_common.py:578-607
    why: "resolve_workspace(project_root)：.agate.env → AGATE_TASKS_DIR → 默认；用于 boundary 前缀排除"
  - path: agate/scripts/agate_common.py:737-754
    why: "split_frontmatter：与 agate-md-field-get 同规则的 frontmatter 拆分"
  - path: agate/scripts/agate-md-field-get.py:160-200
    why: "JSON_FIELDS 与 _read_frontmatter 规则（同源对拍依据）"
  - path: agate/scripts/check-platform-assumptions.py:100-150
    why: "独立 check 脚本的 main()/退出码/参数布局参照"
  - path: agate/scripts/check-protocol-consistency.py:804-809
    why: "M18 插入点：GATE_SCRIPT_EXEMPT 集合，仅在其内新增一行 check-mvwu.py（注释「观测脚本，不挂 gate」）；文件其他部分一律不动，不改 SCRIPT_ALIGNMENT_ANCHORS"
  - path: agate/tests/integration/test_protocol_alignment_review.py:71-88
    why: "test_sg_6（glob check-*.py 全覆盖断言）——M18 后应为绿，B1 落盘后必须跑一遍确认；只读不改"
  - path: agate/tests/unit/test_check_mvwu.py
    why: "P3 产出的红灯测试，P4 转绿目标（届时存在）"
  # ── B2 architect-batch-guidance ──
  # P2-design.md 卡片行号已按实测修正（评审 N3）；以标题定位为准，行号仅为参考
  - path: agate/phase-cards/P2-design.md:96-112
    why: "「## dispatch_plan 机器字段（可选，TAG0014）」节（96 起，字段契约列表约 108-111 行；M2 插入点：字段契约列表之后、`## 影响面梳理` 113 行之前）"
  - path: agate/phase-cards/P2-design.md:125-195
    why: "「## gate_commands 声明」节（125-195）：`### env_constraints 与 gate_commands 的边界` 起于 156，`### \`--strict\` 反模式` 起于 162（M3 插入点：156-161 之后、162 之前）；M4 插入点为 `## 前置条件`（23 起）之后"
  - path: agate/assets/execution-roles/architect.md:209-232
    why: "批次设计节（M5 插入点：节末；四条硬规则 217-222 行须逐字不变）"
  - path: agate/adr.md:69-96
    why: "ADR-003 技术栈中立原文（⑤-d 拒绝依据）"
  # ── B3 batch-evidence-landing ──
  - path: agate/phase-cards/P4-implementation.md:63-69
    why: "产出规格与新增文件核对表边界（M6 插入点）"
  - path: agate/assets/templates/task-files.md:31-34
    why: "阶段产出表 P4 行（M7①）"
  - path: agate/assets/templates/task-files.md:246-252
    why: "P2 frontmatter 样例 dispatch_plan 注释（M7②）"
  # ── B4 review-anchors-and-decision-recheck ──
  - path: agate/role-system.md:177-206
    why: "M8 插入点（组长汇总小节之后、子派发权限边界之前）"
  - path: agate/adr.md:1-8
    why: "M9 插入点（引言块之后、首个分隔线之前）"
  - path: agate/phase-cards/P7-consistency.md:27-36
    why: "M10 检查清单（追加第 6 项）"
  - path: agate/scripts/check-protocol-consistency.py:1161-1240
    why: "CHECK 14 平台词表与扫描面（M8/M9 禁裸词依据，R3）"
  # ── B5 mvwu-glossary-and-debt-log ──
  - path: agate/CONTEXT.md
    why: "术语表三列格式，只追加末尾 5 行；首次定义位置写法参照既有行"
  - path: agate-workspace/debt/tech-debt.md:1428-1490
    why: "DEBT0041/0042 条目样式（M12 抄写式）"
  - path: agate/scripts/agate-debt-check.py
    why: "DEBT schema 校验口径（category/status/source 枚举）"
  # ── B6 mvwu-script-registry ──
  - path: agate/scripts/README.md:36-46
    why: "脚本表末行（check-debt.py 之后追加）"
  - path: agate/tests/README.md:37-100
    why: "映射表格式；用例数以 pytest --collect-only 实数为准"
  - path: CHANGELOG.md:10-16
    why: "[Unreleased] 占位句与条目风格"
```

## 11. env_constraints

```yaml
env_constraints:
  debug_env: "继承 P0-brief：仅用本 worktree 与 tmp_path/会话草稿目录；`~/.agate` 稳定版只读；编排类工具用 `~/.agate/scripts/`；consistency 用 worktree 自己的 `agate/scripts/check-protocol-consistency.py`"
  prod_touch_marker: "[PROD_NOT_TOUCHED]"
  interpreter: "本机仅有 python3（`command -v python` rc=1）；gate_commands 用 python3；测试代码与 tests_filter 文档示例遵守平台中立（fixture/sys.executable/python -m pytest 示意）——声明性，落实见 P3 硬约束与 P5_windows_smoke"
  isolation_check: "check-mvwu 单测全部经 tmp_path 建 git 仓库；运行前后 `git status --porcelain agate-workspace` 不变（BDD-57）；--observe 在真实任务目录跑前后 `git status --porcelain` 不变（BDD-56/38）；由 P3 用例 + P6 证据执行，并非靠本字段强制"
  python_compat: "check-mvwu.py 须 Python 3.8+ 语法（禁 match / str.removeprefix / X|Y 注解），显式 utf-8"
  enforcement_note: "env_constraints 是声明性字段；被强制执行的部分已落 gate_commands（P5_*）或阶段 checklist（R3/R4/R5 的硬约束写入对应批 dispatch-context 与 P3 派发）"
```

## 12. 实现完成的标志（供 P3/P5/P6）

1. `check-mvwu.py` 对 P1 全部行为 BDD（13-58）由 `test_check_mvwu.py` 覆盖并全绿；`--help`/docstring 含三条字面已知局限；`--observe` 在仓库内真实任务目录跑通且只读（BDD-56，P6 证据）。
2. 文档类 BDD（6-11、59-66、68①）由字面标记断言测试全绿；`agate/` 内 `tests_filter: "…python3…"` 0 命中；M8/M9 无 CHECK 14 命中。
3. `P5_*` 全部 exit 0：内核/角色/历史空 diff、consistency 0 ERROR 且 `CHECK9-coverage` 0 新增（M18 已豁免）、`test_sg_6` 为绿、ruff 0 error、全量 pytest ≥1666+新增且 skipped=2、`count-tests.sh` ≥1668+新增用例数、DEBT 校验通过。
4. `P4-protocol-alignment-review.md`（agent≠main）存在，P4 提交信息含 `self-gate-review:`。
5. 未新增 `.sh`（shellcheck 不适用）、未在 gate/hook/CI 登记 `check-mvwu`、`agate/assets/templates/` 无新增文件。

## 13. 给 P3 的提示（吸收 P1-review SUGGEST-B/C，非 P2 强制）

- SUGGEST-B：BDD-22 补 `id: 5` / `id: null` 等价类用例（打印 `batch=?`）。
- SUGGEST-C：字面锚点固定为 `仅检查首词` / `不比对 command 与 tests_filter` / `UNKNOWN 不等价于 PASS，不得作为放行依据`；耗时非整数固定为 `8.5s`（保留 1 位小数）。
- **B1 守护（评审测试缺口）**：把 `test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts` 列为"**P4 前应已绿**的守护用例"（现即为绿，非新增测试）；P5 全量 pytest 中它必须保持绿。BDD-68① 的 `grep -rn check-mvwu agate/rules ... .github/` 路径列表不含 `check-protocol-consistency.py`（M18 落在 `agate/scripts/`），不受 M18 影响。
- **B2 守护**：新增用例断言 `agate-read-p5-commands.py`（env `P2_DESIGN`）对本任务 P2-design.md 读回的每条 cmd 均 `shlex.split` 不抛 `ValueError`、且末 token 不带引号残留（防复发）。
- **B3 守护（retry #2）**：新增用例把 `P5_history_untouched` 读回后的命令在 `tmp_path` 临时 git 仓库（`git init -q` + `git branch -M main`；含 `TAG0010-x`/`TAG0011-x`/`TAG0031-x`/`TAG0032-x`/`TAG0036-x`；不裸 `python3`）执行：**删除**（非仅修改）历史目录（含同时删两个）须 rc=1、修改 / 新增历史目录须 rc=1、改 `TAG0036`/`TAG0037` 须 rc=0；并断言读回 `shlex.split` 的 pathspec 为字面 `TAG00[0-2]*` / `TAG003[0-5]*`（不是已展开的目录名）。
- 建议一条**同源对拍**用例：同一 P2 样例经 `agate-md-field-get.py dispatch_plan` 与 `split_frontmatter` 得同一 JSON（方案 A 同源性的唯一保险）。
- 建议覆盖设计层新增的兜底点：符号链接逃逸（R9）、逐批异常兜底不出 traceback（R10）、重复证据键后者覆盖、`CRLF` 证据文件。

## 14. 修订记录（retry #1）

依据 `P2-review.md`（plan-eng-review，rejected：B1、B2 阻塞，N1-N6 非阻塞）就地修订；评审判"通过"的部分（候选选择、口径 A-H、零内核、批切分与依赖顺序、dogfooding 不写 `tests_filter`）未动。`[PROD_NOT_TOUCHED]`：本轮验证仅用 worktree 与 scratchpad 副本（已删除），未改 `agate/` 任何文件、未 git add/commit。

| 项 | 处置 | 涉及章节 |
|----|------|---------|
| **B1** 新脚本致 `test_sg_6` 变红 | **已改**：新增 M18（`check-protocol-consistency.py::GATE_SCRIPT_EXEMPT` 加 `check-mvwu.py` 一行，不动锚点表与其余内容；主 Agent 已裁决、P1 已落 `[BASELINE_CHANGE]`），并入批 `mvwu-verdict-observer`（2 文件，仍 ≤3，complexity 维持 medium）。同步：§0.1 M18 行（并将 M17/M18 按序排列）、§0.2 该文件由"整体不改"改为"除 M18 一行外不改"、R2 改"已缓解"（`CHECK9-coverage` 0 新增、`test_sg_6` 绿）、新增 R14（既有测试对新增脚本的反应）、§4 BDD-70 行、§5 登记面（CHANGELOG 措辞去掉"预期 +1 WARNING"、新增 `GATE_SCRIPT_EXEMPT` 行）、§6 B1 批行、§7 P5 验收口径、§8（原 SUGGEST 作废并改写为说明主 Agent 裁决）、§10（B1 files_to_read 增 M18 插入点与 `test_sg_6`）、§12 第 3 条、§13（`test_sg_6` 列为"P4 前应已绿"守护用例）。`P5_kernel_diff(_wt)` 清单已核对**不含** `check-protocol-consistency.py`。全仓 glob 抽样实测见 §9 V6b（结论：仅 `test_sg_6` 与 CHECK 9 两处消费 `check-*.py` glob，M18 后无新红灯） | §0.1/§0.2/§0.3 R2·R14/§4/§5/§6/§7/§8/§9 V6b/§10/§12/§13 |
| **B2** 两个 P5 key 末尾引号被读取器吃掉 | **已改**：`P5_roles_diff` 把 `':(exclude)…'` 挪到中间、末 token 为无引号 `agate/assets/execution-roles`；`P5_history_untouched` 去掉 pathspec 引号（**retry #2 更正**：第 1 轮\"bash 展开通配、有无匹配两路等价 / pathspec 语义保持\"对**删除**类变更不成立，已被 B3 纠正，见下方 retry #2）。已用 `agate-read-p5-commands.py` 读回全部 10 条 cmd 并逐条 `shlex.split` 无 `ValueError`，且在临时仓库实测两条命令的 exclude / 历史通配语义保持；自证写入 §9 V7；§7 说明增"引号约束"；§13 建议 P3 加读回防复发用例 | §7/§9 V7/§13 |
| **N1** `parallel_limit: 6` 与"并发 ≤3"矛盾 | **已改（文字）**：§6 波次说明追加"P4 各批 dispatch-context 强制写明波次并发上限 ≤3"；`parallel_limit: 6` 不动；备选"合并批使批数 ≤3"说明不采纳理由 | §6 |
| **N2** 批 id 名实不符 | **已改**：`tests-filter-authoring-guidance` → `architect-batch-guidance`，同步 frontmatter `dispatch_plan`、§6 批表/波次、§10 files_to_read 分组注释；用 `agate-md-field-get.py dispatch_plan` 读回核对合法（见返回前自检） | frontmatter/§6/§10 |
| **N3** `files_to_read` 卡片行号漂移 | **已改**：按实测改为 `P2-design.md` 卡片 `dispatch_plan 机器字段` 96-112、`gate_commands 声明` 125-195（`env_constraints` 边界 156、`--strict` 反模式 162）、`前置条件` 23 起；注明以标题定位为准 | §10 |
| **N4** §7 关于 `~` 令 gate 出 WARNING 不准确 | **已改**：更正为"`agate-gate-missing-cmds.py` 对首词含 `/` 的命令跳过，`P5_ruff` 不产生 WARNING" | §7 |
| N5（R8：本机无 `python`） | 未改：评审要求"如实记录、不改口径"，R8 已如实记录；P6 观测报告标注本机 python3-only 造成的 UNKNOWN 不计入 Q1 不稳定，留给 P6 | §0.3 R8（无变化） |
| N6（方案 B 偏陪衬） | 未改：评审判定"不算稻草人、选 A 理由成立"，无需处置 | §1（无变化） |

`candidate_count: 3` 不变；`packages`/`domains`/`ui_affected` 不变；`status` 保持 draft。

## 14.1 修订记录（retry #2）

依据 `P2-review.md`（第 2 轮复审 rejected，仅剩 B3；B1/B2/N1-N4 已确认闭合）**最小就地修订**，其余章节与 frontmatter 一字未动（`status` 保持 draft）。`[PROD_NOT_TOUCHED]`：仅用 scratchpad 临时 git 仓库（已删除），未改 `agate/` 任何文件、未 git add/commit。

| 项 | 处置 | 涉及章节 |
|----|------|---------|
| **B3** `P5_history_untouched` 去引号后 bash 先展开通配，漏检"删除历史任务目录" | **已改**：值改为反斜杠转义通配、末 token 不以引号结尾——`git diff --exit-code main...HEAD -- agate-workspace/tasks/TAG00\[0-2\]\* agate-workspace/tasks/TAG003\[0-5\]\*`；读回 `shlex.split` 得字面 pathspec，由 git 自解释 glob。第 1 轮"去引号、有无匹配两路等价"的表述对删除不成立，已在 §7 与 §14 B2 行如实更正。自证（V8）：读回全部 10 条 cmd 逐条 `shlex.split` 通过；临时仓库执行读回命令，删除（含同删两个）/ 修改 / 新增历史目录均 rc=1，改 TAG0036/0037 rc=0；旧写法删除类 rc=0（复现 B3）。§13 增 B3 守护用例（删除须 rc=1） | §gate_commands（§7）/§9 V7 note + V8/§13/§14 B2 行/本节 |

`candidate_count: 3`、`packages`、`domains`、`ui_affected`、`dispatch_plan` 均不变。
