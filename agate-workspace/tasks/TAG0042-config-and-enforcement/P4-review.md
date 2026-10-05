---
phase: P4
task_id: TAG0042
type: review
parent: P4-implementation-batch3.md
batch1_parent: P4-implementation-batch1.md
batch2_parent: P4-implementation-batch2.md
status: approved
agent: review
review_round: 5
review_date: 2026-10-06
role: review (偏执 Staff Engineer，工程视角)
scope: batch1（approved）+ batch2（C1 闭合，approved）+ batch3-agate-run（round 4 rejected→round 5 C1 闭合，approved）
prod_isolation: "[PROD_NOT_TOUCHED]"
---

# P4 实现评审 — TAG0042 batch1-phase-semantics（round 1）

> 评审对象：`git diff` 未 commit 改动（HEAD `d3ba1c5`，P3 已落）。
> 评审依据：`P4-dispatch-context-review.md`、`P4-implementation-batch1.md`（含修正轮）、`P2-design.md` §1.1 M1/M2/M3、
> `P3-test-cases-batch1.md`、`P0-brief.md` known_risks、`docs/reviews/agate-alignment-review-2026-10-06-TAG0042.md`（round2 aligned）。
> 视角：**工程正确性/边界/回归/测试充分性**；语义对齐已由 protocol-alignment-review round2 判 aligned，本报告不重复、不替代其结论。

## 结论

**status: approved**。Pass 1（CRITICAL/BLOCKER）：**0 条**。Pass 2（INFORMATIONAL）：**5 条**（均非阻断，可 P5/P7/P8 或后续批次承接）。

改动面（`agate-next.py` 去预写/删孤儿函数、P2/P8 卡、UPGRADING v0.79.0、5 处权威文档反传、3 处既有断言同步）
经独立实跑核对：行为自洽、无残留调用、无回归、新用例覆盖 BDD-1/BDD-2 全部门槛。可进入 P5。

---

## Pass 1（CRITICAL）— 数据安全与正确性

**0 条。** 逐项排查（派发重点 1-4）结论如下：

### 1. `_advance()` 推进判定链自洽 — 通过

- **gate exit 三态消费**（`agate-next.py:367-402`）未被本批触及：`rc ∈ pass_set` → 普通 phase 查 `next`、P6 走 `_p6_pass` 条件式；`rc == 1` → 查 `retreat` 委托 / 提示重试；`else` → 落 exit2-resolution。结构不变、分支互斥、无遗漏。
- **P6 条件式裁决**（`_p6_pass` / `_p6_judge_advance`，`:229-297`）不变：`provenance` 通过的判据含 exit 2（DEBT0045），judge 启用时 `check-gate P6.5 exit 0` 才消费 `next`。`_advance` 的内部改动（不再写 phase/git add）不影响其调用契约（仍返回「已处理」语义）。
- **retreat 委托**（`_delegate_retreat`，`:300-325`）不变，仍以 `repo_root` 为 cwd 调 `agate-retreat-to.py`；retreat-to 自身写 phase 的路径未动。
- **孤儿函数删除无残留调用**：`grep -n "_write_state\|_git" agate/scripts/agate-next.py` → **0 命中**；全仓 `agate/**/*.py` 中 `_write_state`/`_git` 仅命中各文件**同名局部 helper**（`test_check_gate.py` 的 `_write_state_judge` 等）与注释，无对被删函数的 import/调用。`_advance` 调用点（`:279/:288/:386`）与保留形参兼容。
- `_advance` 不再做 git 操作，主 Agent 负责 `git add` 与 commit——与 `git-integration.md` 规则 2「一阶段一 commit、phase 随产出同 commit」一致。

### 2. 跳变合法性校验仍有效 — 通过

- `check-state-transition.py:251-269` 的触发面是**暂存区含 `.state.yaml`**（`git diff --cached --name-only`），**不读账本**。去预写后 phase 变更改由「下一阶段产出 commit 暂存 `.state.yaml`」触发，`pre-commit-gate.py:243-255`（2b 检测 `phase:` 变更 → 2c 调 `check-state-transition.py`）**同一机械路径不变** → 校验**未弱化**，仅触发时机后移一个 commit（与设计意图一致）。
- 实测回归：`test_check_state_transition.py` 全绿（见验证清单）。

### 3. `state_transition` 事件 `.phase=target` 而 `.state.yaml` 保持旧 phase — 不构成 CRITICAL

- **无硬消费者**：`grep` 全 `agate/scripts/*.py`，`state_transition` 事件只被**生产**（`agate-next.py:158`、`pre-commit-gate.py:415`），无脚本**解析**其字段（`check-events.py` 仅校哈希链/ts/已知类型，`check-judge-verdict.py` 不读该事件）→ 不破链、不触发审计、不改变 gate 判定。
- 残留歧义（事件语义/重复）不足以上升为 CRITICAL，记入 Pass 2 #1。

### 4. 测试充分性 — 通过

- 新增 `test_tag0042_batch1_phase_semantics.py`（6 例）覆盖 **BDD-1**（不预写 phase / 不 `git add`）与 **BDD-2**（`_advance` 无 `state["phase"]=target` / 卡片表述与行为一致 / UPGRADING 记载 / 全 `agate/scripts/*.py` 无预写实现）→ 派发重点所列 6 条新红灯测试到位。
- 既有同步**完整**：`test_tag0027_b1_agate_next_cli.py` 仅 4 处 `_read_state_phase` 断言（`:156` P5、`:317` P6、`:336` gate_p65 exit 1 停留 P6、`:371` P5）；3 处「推进后 phase」已同步为新语义，`:336` 非预写断言（保留正确）。**无遗留「推进后 phase 被写」断言**（跨 `agate/tests/` 复核，无其它文件在 agate-next 后断言 phase 前进）。

### 5. UPGRADING v0.79.0 版本号假设 — 属已登记 DESIGN_GAP，非缺陷

`P4-implementation-batch1.md`「[DESIGN_GAP]」节显式登记：P2 §1.1 M3 未指定版本节标题，实现自主采用 `### v0.79.0`，P8 发版时同步。**登记齐备**，P8 需据实版本号核对（不阻断本批）。

---

## Pass 2（INFORMATIONAL）— 代码健康 / 边界观察

### [INFORMATIONAL-1] `state_transition` 事件语义分裂 + 同转移双写
`agate-next.py:158-163` 在 gate 通过时追加 `state_transition`（from=old,to=target,phase=target），相位**未变**；而 `pre-commit-gate.py:413-420` 在**真实提交**相位变更时**也**追加一条同 from/to/phase 的事件（「双写语义」为既有设计）。差别：
- 批 1 前，agate-next 已把 phase 写盘，两条事件指向**同一次真实提交**；批 1 后，agate-next 的事件语义变为「**建议推进**」（可能对应未来某 commit，甚至在任务中止时成为**从未落地的幻影转移**）。
- 当前无消费者（Pass 1 §3 已证），**不阻断**。建议（非必须）：P7/P8 或观测器侧若要区分「已提交/仅建议」，可在事件内加 `committed: true|false` 或备注字段；或在 `CONTEXT.md` 账本事件表补一句语义说明。交由 P7/P8 判断，不在本批硬改。

### [INFORMATIONAL-2] 逐阶段卡片步「phase 保持 Pn」措辞在去预写后不再精确
批 1 后，进入 Pn 时 `.state.yaml` 的 phase 实际为 **P(n-1)**（agate-next 不再预写），须由主 Agent 在 Pn 产出 commit 时写入 Pn。`P2-design.md` / `P8-release.md` 已由本批补「agate-next 亦不预写」注；但 `P1/P3/P4/P5/P6/P7` 卡第 5 步仍写「此时 `.state.yaml` 的 phase 保持 Pn，不要提前写 P(n+1)」——「保持」隐含 phase 已为 Pn。
- **为何不判 CRITICAL**：手工规格已在两处明文档兜底——`git-integration.md:113`「更新 `.state.yaml` phase（先更新再 commit）」、`state-machine.md:523`「先更新 phase → 再 add → 再 commit」；且各卡第 6/N 步已有「phase 推进 P(n+1) 随 P(n+1) 产出 commit 一起」。流程闭合，属**措辞精确性**而非逻辑缺口。
- **与 round2 A3b 的差异**：对齐审查判「P1/P3/P4/P5/P6/P7 卡不需改」，工程侧同意其**非阻断**；此处仅补充建议——后续批次/文档整备时为这几张卡各补一句「进入本阶段后由本阶段产出 commit 将 phase 写为 Pn」，可消除主 Agent 漏写 phase 导致 pre-commit 按旧 phase 跑 gate 的静默风险（去预写把该写入从机械动作变为 Agent 手工动作，与本任务「规则不靠记忆」的立项动机存在张力）。不阻断本批。

### [INFORMATIONAL-3] `_advance` 的 `repo_root` 形参已成死参数
`agate-next.py:166` 保留 `repo_root` 但函数体不再使用（docstring `:173` 已如实注明「批 1 后不再做 git 操作」）。保留理由（避免级联改 `_p6_judge_advance`/`main` 签名）合理，ruff 不报。可在后续批次顺手移除，或保持现状；**不影响正确性**。

### [INFORMATIONAL-4] `P4-evidence/batch1-phase-semantics.log` 未含本批新增测试文件
日志 command 沿用 P2 §6.1b 声明的「既有 3 文件」filter（`test_agate_next_card` + `test_tag0027_b1_agate_next_cli` + `test_check_state_transition`，实测 93 passed / exit 0），**未包含**本批专属新用例 `test_tag0042_batch1_phase_semantics.py`。声明如实、命令实跑合规（MVWU 不阻断）；仅作过程提示：作为「本批绿灯」证据，若把新增 6 例一并纳入 filter（共 99 passed）会更完整。供 P8/后续批参考。

### [INFORMATIONAL-5] 一致性 WARNING 基线口径
实跑 `check-protocol-consistency.py --strict-errors-only` → **0 ERROR / 398 WARNING**，与 `P0-brief.md` 基线一致（对齐审查 round2 记 398；round1 因派发文件瞬时引用曾记 400，现已回落到冻结基线 398）。无新增 WARNING。信息性登记。

---

## 验证清单（本次评审独立实跑，证据先于结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 批 1 相关 4 文件 | `pytest test_tag0042_batch1_phase_semantics test_tag0027_b1_agate_next_cli test_check_state_transition test_agate_next_card -q` | **99 passed**（12.77s） |
| UPGRADING 契约文档 | `pytest test_upgrading_contract_doc test_upgrading_lifecycle -q` | **27 passed** |
| ruff | `ruff check agate-next.py test_tag0027_b1_agate_next_cli.py test_tag0042_batch1_phase_semantics.py` | `All checks passed!` |
| 平台假设扫描（改动文件） | `check-platform-assumptions.py <3 文件>` | exit 0（0 命中） |
| 一致性 | `check-protocol-consistency.py --strict-errors-only` | exit 0 / **0 ERROR / 398 WARNING** |
| 用例数 | `bash agate/tests/scripts/count-tests.sh` | **2687**（未漂移） |
| 残留调用 | `grep "_write_state\|_git" agate-next.py` | 0 命中 |
| 残留旧行为文档 | `grep "写回 .state.yaml + git add\|更新 .state.yaml phase + git add" agate/*.md` | 0 命中（其余命中均为手工 fallback 规格，已显式限定） |

## [PROD_NOT_TOUCHED]

本评审**只读**改动集、任务数据与协议文档，并运行**只读/隔离**测试（pytest tmp_path 夹具、ruff、平台扫描、一致性、count-tests）。未修改任何被评审文件、未触碰主 checkout 状态、未访问 `~/.agate` 生产安装、未运行任何写生产环境/生产数据库/生产 API 的操作。实跑命令均无对仓库内已提交文件的写副作用（pytest 用例经 `tmp_path`/`git_repo` 夹具隔离；一致性/ruff/scan 为只读扫描）。

<!--
增量复评说明（供后续批次）：本文件按轮次追加（参照 TAG0034 P4-review.md 形态），保留前轮全文。
round 1 = batch1-phase-semantics（approved）；round 2 = batch2-agate-config（rejected）。
-->

---

# P4 实现评审 — round 2（增量）：batch2-agate-config（声明层）

> 评审对象：`git status --short` + `git diff` 未 commit 改动（HEAD `48091f2`，batch1 已落）。
> 评审依据：`P4-dispatch-context-review-batch2.md`、`P4-implementation-batch2.md`（含 4 条 DESIGN_GAP）、
> `P2-design.md` §1.1 M4-M8 / §4.1、`P3-test-cases-batch2.md`、`docs/reviews/agate-alignment-review-2026-10-06-TAG0042.md`（round 3 aligned）。
> 视角：**工程正确性/边界/回归/测试充分性**；语义对齐已由 protocol-alignment-review round 3 判 aligned，本报告不重复、不替代。

## 结论

**status: rejected**。Pass 1（CRITICAL/BLOCKER）：**1 条**（C1，可复现）。Pass 2（INFORMATIONAL）：**6 条**（非阻断）。

> frontmatter 的 `status` 为**聚合门禁态**：round 1（batch1）结论不变（approved），但 batch2 存在 1 条 CRITICAL，
> 按 review 角色门槛映射「有 CRITICAL → rejected」。须修复 C1（1 行改动 + 1 条测试）后复审 batch2，P4 gate 方可放行。

---

## Pass 1（CRITICAL）— 数据安全与正确性

### [CRITICAL] `agate/scripts/agate_common.py:871`（`read_project_config`）— 非法 YAML 未按契约优雅返回，抛未捕获异常

**问题**：`read_project_config` 的 docstring（`:855-859`）与 `P4-implementation-batch2.md`（§3）均声称
「文件存在但 YAML 非法 / 顶层非映射 → 返回默认 dict + `present=False` + `parse_error`」。但实现只捕获
`except (OSError, ValueError)`（`:871`），而 PyYAML 的语法/扫描/组合错误（`yaml.parser.ParserError` /
`yaml.scanner.ScannerError` / `yaml.composer.ComposerError`）都继承自 **`yaml.YAMLError` → `Exception`**，
**既不是 `ValueError` 也不是 `OSError`**（本机实测 `issubclass(ParserError, ValueError) == False`）。

**复现（本次评审实测）**：

```text
$ printf 'not: [a mapping\n' > <proj>/agate.config.yaml
$ python3 agate/scripts/agate-config.py validate          # cwd=<proj>
  Traceback (most recent call last):
    ...
    File ".../agate_common.py", line 870, in read_project_config
      loaded = yaml.safe_load(f)
  yaml.parser.ParserError: while parsing a flow sequence ...
  rc=1
```

进程内调用同样抛出（`read_project_config(d)` → `RAISED: yaml.parser.ParserError`），**不返回** `present=False`/`parse_error`。

**影响**：
- `agate-config validate` 对非法声明打印**完整 traceback**（而非契约的逐条报错），违反「退出码语义 + 客观报错」的交付面；`UPGRADING.md` / BDD-8 明确把「声明文件**非法**」纳入迁移契约，故该路径是**约定内输入**，非边缘情况。
- 本批 `gate_p0` 经**子进程**调 validate，rc≠0 仍被吸收为 WARNING（恒 return 2 不变量未被破坏）——故**迁移期用户可见行为尚可**；但 `read_project_config` 是 P2 §4.1 指定的**唯一读取函数**，batch3+（`agate-run` / `agate-doctor`）将**进程内**消费它，届时非法声明会让消费方**直接崩溃**，而不是拿到默认值 + `parse_error`。这正与该函数「让所有消费方免于各自处理解析错误」的设计目的相悖。
- 测试未覆盖该路径（`test_agate_config.py` / `test_config_schema.py` 只测「文件缺失」，无非法 YAML 用例）→ 缺陷未被红灯拦住。

**建议 Fix（最小、单一）**：
1. `:871` 的 `except (OSError, ValueError)` 增补 `yaml.YAMLError`（`yaml` 在 `agate_common` 顶部已 import，import 失败会 `sys.exit(1)`，无需额外守卫）；与**同文件**既有惯例一致（`read_rules_yaml:1212` 直接 `except Exception`）。
2. 补 1 条红灯/绿灯测试（如 `test_bdd_6_read_project_config_malformed_yaml_is_graceful`）：写非法 YAML → 断言 `read_project_config` **不抛**、`present is False`、`parse_error` 非空；并可加 `agate-config validate` 对该输入 rc≠0 且**无 traceback**（stderr 不含 `Traceback`）。

---

## Pass 2（INFORMATIONAL）— 代码健康 / 边界观察

### [INFORMATIONAL-1] `gate_p0` 经**调用方 cwd** 定位声明，未用 `task_dir`/项目根（WARNING 可假阳性/假阴性）
`check-gate.py::gate_p0`（`:631-652`）以 `subprocess.run([sys.executable, config_script, "validate"])` 调 validate，**未传 `cwd`** → 继承 check-gate 进程的 cwd；而 `agate-config.py` 用 `os.getcwd()` 作 project_root。实测：从**有合法声明**的目录跑 `check-gate.py P0 <task>` → **无 WARNING**；从无声明目录跑 → 有 WARNING。即 WARNING 取决于调用方 cwd，而非被检查任务的所属项目根。
- pre-commit hook 路径 cwd=仓库根（正确）；但 `gate_p0` 的 `task_dir` 形参被闲置，任何从其它目录调用（子目录 / 不同项目）都会给出**错误 WARNING**。
- **建议**：由 `task_dir` 确定项目根（如 `agate_common.resolve_workspace(task_dir)` 或 `git -C task_dir rev-parse --show-toplevel`），并显式 `cwd=<repo_root>` 调 validate。

### [INFORMATIONAL-2] BDD-8 测试依赖「仓库根当前无 `agate.config.yaml`」，环境决定红绿
`test_bdd_8_gate_p0_missing_declaration_keeps_passing_exit` / `..._emits_warning` 通过 `run_cli`（`cwd=None`）继承 pytest 进程 cwd = 仓库根，其 WARNING 断言**隐含要求 agateon 仓库根没有 `agate.config.yaml`**。而本批新增的 `install-hook` 自动 init 会在项目根生成该文件——一旦 agateon 自身被接入（或在仓库根手动 `init`），这两条测试即变红。这与 conftest `_run_cli_impl` docstring 明确反对的「本机环境决定红绿」同类。**建议**：给这两条用例传显式隔离 `cwd`（tmp 项目根），与 INFORMATIONAL-1 的确定性定位一并解决。

### [INFORMATIONAL-3] `agate-config.py` shebang `#!/usr/bin/env python` 偏离主流惯例（测试驱动的工作绕过）
仓内 78 个脚本用 `#!/usr/bin/env python3`，仅 `agate-config.py`（及 1 个既有文件）用 `python`——原因是为规避 `test_bdd_3_protocol_does_not_hardcode_md_product_shape` 对**源码任意位置** `python3` 字面量的扫描（连 shebang 一并命中）。本机 `command -v python` **不存在** ⇒ `./agate-config.py` 直接执行会失败（虽常规路径经 `sys.executable` 调用，无功能影响）。**建议**：收窄该测试扫描（跳过 shebang/注释行）并恢复 `python3`，避免测试倒逼脚本偏离惯例。

### [INFORMATIONAL-4] DESIGN_GAP ④（默认注入使 schema `required` 不可达）— 独立复现，确认非阻断
实测：仅 `schema_version: 1`（缺 required 的 `project`）→ validate **rc=0**；空映射文件（0 字节 → `safe_load` 返回 `None`）→ 走 `present=False` → rc=1。即顶层 `required`（`schema_version`/`project`）在「先注入默认值再校验」的 effective-config 模型下**永不触发**。与 round 3 判定一致（DESIGN_GAP 交 P7）。**建议 P7 明确裁决**：或从 schema 移除 `required`（与 effective 语义对齐），或让 validate 针对「用户实际声明的键集合」判 required（需 `read_project_config` 额外暴露声明键集）。

### [INFORMATIONAL-5] `read_project_config` 把元数据（`present`/`parse_error`）混入数据 dict
消费方须自行用 `_public_config` 剥除内部键；后续消费方（batch3+）若忘记剥除，会把 `present` 误当声明字段。**建议**：返回 `(config, present)` 或专用结果对象，或至少在 P2/文档固化「消费方必须剥除内部键」的约定。非阻断。

### [INFORMATIONAL-6] `_load_schema()` 无缺失/损坏守卫
`agate-config.py:98-101` 直接 `open` + `json.load` schema；schema 缺失或非法 JSON → 未捕获异常。schema 是随协议发布的固定产物，风险低；与「唯一读取函数」的优雅风格不一致。**建议**：捕获并给出明确报错（非阻断）。

---

## 验证清单（本次评审独立实跑）

| 验证项 | 命令 | 结果 |
|---|---|---|
| batch2 红→绿 | `pytest test_agate_config test_config_schema test_agate_scripts_encoding -q` | **24 passed** |
| 关联回归（5 文件） | `pytest test_check_gate test_install_hook test_agate_common test_agate_config test_config_schema -q` | **277 passed** |
| ruff | `ruff check agate/` | `All checks passed!` |
| 一致性 | `check-protocol-consistency.py --strict-errors-only` | exit 0 / **0 ERROR / 401 WARNING**（冻结面） |
| 用例数 | `count-tests.sh` | **2687**（未漂移） |
| 平台扫描（改动文件） | `check-platform-assumptions.py <6 脚本 + 1 测试>` | 仅 5 条 R2 **存量行**（`agate_common:332`/`install-hook:257`/`agate-setup:157,848,945`）；`git diff` 新增行含 `python3` **0 命中** |
| C1 复现（非法 YAML） | `printf 'not: [a mapping\n' > agate.config.yaml && agate-config.py validate` | **Traceback + `yaml.parser.ParserError`**（契约应为 present=False + parse_error） |
| gate_p0 cwd 依赖 | 从有/无合法声明的目录各跑一次 `check-gate.py P0 <task>` | WARNING 出现与否**随 cwd 翻转**（INFORMATIONAL-1 实证） |
| DESIGN_GAP ④ | `validate`（仅 schema_version / 空文件） | 仅 schema_version → rc=0；空文件 → rc=1（确认 required 不可达） |

## [PROD_NOT_TOUCHED]

本评审**只读**改动集、任务数据与协议文档，并运行**只读/隔离**测试与 CLI 探针。C1 复现与 DESIGN_GAP ④ 探针全部在 `/tmp/opencode/cfgprobe/` 下以自建 `agate.config.yaml` 运行，**未在仓库内写入/修改任何文件**；pytest 经 `tmp_path`/`git_repo` 夹具隔离；未触碰主 checkout 状态、未访问 `~/.agate` 生产安装、未运行任何写生产环境/生产数据库/生产 API 的操作。

---

# P4 实现评审 — round 3（复审）：batch2-agate-config C1 闭合

> 复审对象：round 2 判定的唯一 CRITICAL = **C1**（`read_project_config` 漏捕 `yaml.YAMLError`）。
> 修复面：`agate/scripts/agate_common.py::read_project_config()`（`:871`）+ 新增测试
> `agate/tests/unit/test_config_schema.py::test_bdd_6_read_project_config_malformed_yaml_is_graceful`。
> 依据：`P4-dispatch-context-review-batch2-rereview.md`；只复核 C1 闭合与回归，不重开其它面。

## 结论

**status: approved**。**C1 已闭合**，无剩余 CRITICAL/BLOCKER。round 2 的 6 条 INFORMATIONAL **仍为非阻断**（按派发指引不在本轮修，留 P7/P8 或后续批次）。

## C1 闭合核验（独立实跑）

1. **代码**：`agate_common.py:871` 已改为 `except (OSError, ValueError, yaml.YAMLError) as exc`，并附注释说明 `yaml.YAMLError`（`ParserError`/`ScannerError`/`ComposerError`）不继承 `ValueError`/`OSError`。`yaml` 在 `agate_common` 顶部 import（失败即 `sys.exit(1)`），无需额外守卫——修复正确、无副作用。
2. **进程内**（本次评审自建非法 YAML 复跑）：`read_project_config(<dir with 'not: [a mapping\n'>)` → **不再抛异常**，返回 `present=False` 且 `parse_error` 非空（与 docstring 契约一致）。
3. **CLI**：`agate-config.py validate` 对非法 YAML → **rc=1，输出干净报错、`Traceback` 计数 = 0**（修复前为完整 traceback）。
4. **新增测试**：`test_bdd_6_read_project_config_malformed_yaml_is_graceful` **1 passed**（断言不抛 + `present is False` + `parse_error` 非空）——C1 契约已由红灯测试锁定。
5. **无新回归**：`test_agate_common.py` + `test_agate_config.py` + `test_config_schema.py` + `test_agate_scripts_encoding.py` → **52 passed**；`test_check_gate.py` + `test_install_hook.py` + `test_agate_common.py` → **255 passed**；`ruff check` 两改动文件 → `All checks passed!`。
6. **用例数**：`count-tests.sh` → **2688**（较上轮 2687 +1 = C1 回归测试，符合预期）。

## 验证清单

| 验证项 | 命令 | 结果 |
|---|---|---|
| C1 回归测试 | `pytest test_config_schema.py::test_bdd_6_read_project_config_malformed_yaml_is_graceful -q` | **1 passed** |
| 进程内不抛 | 自建非法 YAML 调 `read_project_config` | `present=False` + `parse_error` 非空，**无异常** |
| CLI 无 traceback | `agate-config.py validate`（非法 YAML） | rc=1，`Traceback` 计数 **0** |
| 关联回归（4 文件） | `pytest test_agate_common test_agate_config test_config_schema test_agate_scripts_encoding -q` | **52 passed** |
| 关联回归（3 文件） | `pytest test_check_gate test_install_hook test_agate_common -q` | **255 passed** |
| ruff | `ruff check agate_common.py test_config_schema.py` | `All checks passed!` |
| 用例数 | `count-tests.sh` | **2688**（+1） |

## [PROD_NOT_TOUCHED]

本轮复核**只读**改动集并运行**只读/隔离**测试与 CLI 探针。非法 YAML 探针在 `/tmp/opencode/c1probe/` 下自建 `agate.config.yaml` 运行（探针文件已清理），**未在仓库内写入/修改任何文件**；pytest 经 `tmp_path` 夹具隔离；未触碰主 checkout 状态、未访问 `~/.agate` 生产安装、未运行任何写生产环境/生产数据库/生产 API 的操作。

---

# P4 实现评审 — round 4（增量）：batch3-agate-run（执行层）

> 评审对象：`git status --short` + `git diff` 未 commit 改动（HEAD `18b3e3d`，batch2 已落）。
> 评审依据：`P4-dispatch-context-review-batch3.md`、`P4-implementation-batch3.md`（含修正轮 + 2 条 DESIGN_GAP）、
> `P2-design.md` §1.1 M9/M10 / §4.2、`P3-test-cases-batch3.md`、`docs/reviews/agate-alignment-review-2026-10-06-TAG0042.md`（round 5 aligned）。
> 视角：**工程正确性/边界/平台/回归/测试充分性**；语义对齐已由 protocol-alignment-review round 5 判 aligned，本报告不重复、不替代。

## 结论

**status: rejected**。Pass 1（CRITICAL/BLOCKER）：**1 条**（C1，跨平台正确性，静态可判定）。Pass 2（INFORMATIONAL）：**5 条**（非阻断）。

> frontmatter `status` 为聚合门禁态：batch1/batch2 结论不变（approved），batch3 存在 1 条 CRITICAL → 按角色门槛映射 rejected。
> 须修复 C1（1 行 + 1 条平台面测试）后复审 batch3。

---

## Pass 1（CRITICAL）— 数据安全与正确性

### [CRITICAL] `agate/scripts/agate-run.py:121`（`_write_evidence`）— `.out` 证据以**文本模式默认换行**落盘，与**逐字节比对**不一致（Windows 恒报 baseline mismatch）

**问题**：`_write_evidence` 用 `open(path, "w", encoding="utf-8")` 写证据（默认 `newline=None` → **写时把 `\n` 翻译成 `os.linesep`**），而比对侧 `_read_bytes(evidence_path) != output.encode("utf-8")`（`:180`/`:182`）是**字节精确**。二者在 POSIX 上重合（`os.linesep="\n"`），在 Windows（`os.linesep="\r\n"`，CI = `actions/setup-python` 原生 Python）**必然不一致**：命令输出经 `text=True` 读取已被归一化为 `\n`，写入时又被翻译为 `\r\n`，再读回是 `\r\n`，与 `output.encode("utf-8")`（`\n`）不等。

**后果**：Windows 上 `agate-run --baseline` **首次落盘后，任何后续执行（含输出完全一致）都判 `baseline mismatch` 并返回 1**——BDD-10「逐字节比对二值判定」在 Windows 上失效（恒红）。这是**假阴性（false failure）**：不违反「不静默报绿」（ADR-015），但使该功能在受支持平台上不可用，且报错内容（diff 存在）是**误导**。

**为何是 CRITICAL（而非观察）**：
1. **违反本批契约**：P2 §4.2 / BDD-10 明确要求「**逐字节**比对」；写盘必须产出与比对同一字节序列。
2. **违反仓库既有硬约定**：仓库对「字节精确 I/O」一律用 `newline=""`/`newline="\n"`（`agate_package.py:813/845/848` 快照、`agate-release.py:143`），`agate-run` 是唯一偏离点；AGENTS.md「平台无关是硬约束」。
3. **测试盲区**：`test_bdd_10_*` 均非 `windows_smoke`，Windows CI（`protocol-tests.yml:155` 只跑 `-m windows_smoke`）**不执行**，故红灯拦不住。

**建议 Fix（最小、单一）**：
- 写证据改为**字节精确**：`with open(path, "wb") as fh: fh.write(output.encode("utf-8"))`；或保留文本写但显式 `newline=""`（与 `agate_package` 同款）。二者择一即可让写/读字节一致。
- 补 1 条测试锁定「落盘字节 == `output.encode("utf-8")`」（读 `"rb"` 断言），并（可选）加 `windows_smoke` 面用 `newline` 敏感输入（含多行）验证后续比对 rc=0。注：纯 Linux 运行无法复现换行翻译，故建议同时以源码面守卫（断言 `_write_evidence` 用 `"wb"` 或 `newline=""`）防回归。

---

## Pass 2（INFORMATIONAL）— 代码健康 / 边界观察

### [INFORMATIONAL-1] `agate-run` 以 `os.getcwd()` 作 project_root（cwd 依赖，同 batch2 I1）
`main` 取 `project_root = os.getcwd()`（`:148`）读取声明、定位证据。约定「从项目根运行」，但与 `gate_p0`（batch2 I1）同属 cwd 依赖；从子目录/他处调用会读错声明与证据槽位。**建议**：由显式项目根（或 `AGATE_PROJECT_ROOT` env）解析，与 gate_p0 一并统一。非阻断。

### [INFORMATIONAL-2] DESIGN_GAP ②（命令文本匹配 + 下标槽位）确认语义自洽，但有重排脆弱性
实现按命令文本精确匹配、以**声明下标**为证据槽位（`cmd-<n>.out`），使「原地改命令文本 → 仍与旧基线比对」成立（BDD-10-03）。但若**重排/插入/删除** `verify.commands`，其后命令的下标漂移 → 与既有基线**错配**（假 mismatch）。P2 与 schema 的接口张力（schema 无命名 key）已登记为 DESIGN_GAP 交 P7。**同意交 P7**；建议 P7 明确「按声明下标」是否可接受，或扩展 schema 引入命名 key。

### [INFORMATIONAL-3] DESIGN_GAP ①（P2 M10「修正 formatter 计数」）确认无可执行落点 → 交 P7
复核：`agate_common._fallback_json`（无 formatter 时 total/passed/failed 恒 0）为**既有设计**，A/B 出口码依赖它；`is_gate_meta_key` 后缀排除已有 GPC 测试锁定；`agate-capture-env-baseline` 一致性检查不在本批 output 面。**无可复现缺陷**，改动反而违反 P2 §1.2 N3。实现「未做」正确。**同意交 P7**（建议 P2 删/细化该条）。

### [INFORMATIONAL-4] `test_bdd_12_hook_stages_ledger` 为源码面弱断言（未端到端验证暂存）
该用例仅以正则断言 `pre-commit-gate.py` 源码含「账本 + add」逻辑（`:242-253`），不验证真实 commit 上下文下账本确被暂存。hook 端到端暂存由既有 `test_pre_commit_hook.py`（61 passed）间接覆盖，但无**针对本批新增 2h.1d 暂存逻辑**的端到端用例。**建议**（非阻断）：后续批次或 P7 补一条在 `git_repo` 中真实 commit、断言 `git diff --cached --name-only` 含 `gate-events.jsonl` 的用例。

### [INFORMATIONAL-5] `_is_ignored` 的 `os.path.relpath` 跨盘符/异常边界
`os.path.relpath(path, project_root)` 在 Windows 上若证据路径与项目根**不同盘符**会抛 `ValueError`（未捕获）→ agate-run 崩溃而非「无法判定 → WARNING」。属极边缘（证据目录通常同盘）。**建议**：包一层 `try/except ValueError → None`。非阻断。

---

## 验证清单（本次评审独立实跑）

| 验证项 | 命令 | 结果 |
|---|---|---|
| batch3 红→绿 | `pytest test_agate_run test_events_ledger test_check_events -q` | **29 passed** |
| hook 集成回归 | `pytest agate/tests/integration/test_pre_commit_hook.py -q` | **61 passed** |
| ruff | `ruff check agate-run.py pre-commit-gate.py` | `All checks passed!` |
| 一致性 | `check-protocol-consistency.py --strict-errors-only` | exit 0 / **0 ERROR / 402 WARNING**（冻结面） |
| 平台扫描（本批改动） | `check-platform-assumptions.py agate-run.py pre-commit-gate.py` | exit 0（0 命中） |
| C1 静态判定 | 读 `agate-run.py:121`（文本写）vs `:180/:182`（字节比）+ `agate_package.py:813/845/848`（`newline=""` 约定）+ `protocol-tests.yml:155`（Windows 只跑 smoke） | 写/比字节不一致，Windows 恒 mismatch（C1 成立） |
| DESIGN_GAP ① 复核 | 读 `_fallback_json` / `is_gate_meta_key` / capture-env-baseline | 无可复现缺陷（同意交 P7） |

## [PROD_NOT_TOUCHED]

本评审**只读**改动集、任务数据与协议文档，并运行**只读/隔离**测试与静态核对（pytest 经 `tmp_path`/`git_repo` 夹具隔离；ruff / 平台扫描 / 一致性为只读）。**未在仓库内写入/修改任何文件**、未触碰主 checkout 状态、未访问 `~/.agate` 生产安装、未运行任何写生产环境/生产数据库/生产 API 的操作。C1 为**静态判定**（读源码 + 仓库既有字节精确约定 + CI 配置），未在 Windows 上实跑。

---

# P4 实现评审 — round 5（复审）：batch3-agate-run C1 闭合

> 复审对象：round 4 判定的唯一 CRITICAL = **C1**（`_write_evidence` 文本模式默认换行 vs 逐字节比对不一致，Windows 恒 mismatch）。
> 修复面：`agate/scripts/agate-run.py::_write_evidence`（`:117`）+ 新增测试
> `agate/tests/unit/test_agate_run.py::test_bdd_10_baseline_evidence_is_byte_exact`（端到端字节相等 + 源码面守卫，标 `windows_smoke`）。
> 依据：`P4-dispatch-context-review-batch3-rereview.md`；只复核 C1 闭合与回归。

## 结论

**status: approved**。**C1 已闭合**，无剩余 CRITICAL/BLOCKER。round 4 的 5 条 INFORMATIONAL **仍为非阻断**（按派发指引不在本轮修）。

## C1 闭合核验（独立实跑）

1. **代码**：`_write_evidence`（`:128-129`）已改为 `with open(path, "wb") as handle: handle.write(output.encode("utf-8"))`——**字节精确写**，与比对侧 `_read_bytes(...) != output.encode("utf-8")`（`:180`/`:182`）字节一致；docstring 记录了「文本模式 `newline=None` 会把 `\n` 翻译为 `os.linesep`」的根因。POSIX/Windows 行为现一致。
2. **新增测试**：`test_bdd_10_baseline_evidence_is_byte_exact` **1 passed**——① 端到端：多行命令输出，断言证据 `read_bytes()` == 命令输出 UTF-8 字节；② 源码面守卫：断言 `_write_evidence` 的 `with open(...)` 调用行含 `"wb"` 或 `newline=""`（只查调用行、不搜 docstring，避免被注释误导）。
3. **守卫有效性**（本次评审独立模拟，未改仓库）：对当前源码 `call_lines=['with open(path, "wb") as handle:']` → 守卫 **True**；对模拟的 buggy 行 `with open(path, "w", encoding="utf-8")` → 守卫 **False**（能抓住回归）。
4. **无新回归**：batch3 两文件（`test_agate_run.py` + `test_events_ledger.py`）→ **16 passed**；`test_pre_commit_hook.py` → **61 passed**；`ruff check` 两改动文件 → `All checks passed!`。
5. **用例数**：`count-tests.sh` → **2689**（较上轮 2688 +1 = C1 回归测试，符合预期）。

## 验证清单

| 验证项 | 命令 | 结果 |
|---|---|---|
| C1 回归测试 | `pytest test_agate_run.py::test_bdd_10_baseline_evidence_is_byte_exact -q` | **1 passed** |
| batch3 两文件 | `pytest test_agate_run.py test_events_ledger.py -q` | **16 passed** |
| hook 集成回归 | `pytest agate/tests/integration/test_pre_commit_hook.py -q` | **61 passed** |
| ruff | `ruff check agate-run.py test_agate_run.py` | `All checks passed!` |
| 守卫有效性 | 对当前/模拟 buggy 写盘行跑守卫正则 | 当前 True / buggy False（有效） |
| 用例数 | `count-tests.sh` | **2689**（+1） |

## [PROD_NOT_TOUCHED]

本轮复核**只读**改动集并运行**只读/隔离**测试与静态核对。守卫有效性以内存字符串模拟验证（未改仓库源码）；pytest 经 `tmp_path`/`git_repo` 夹具隔离；ruff 为只读。**未在仓库内写入/修改任何文件**、未触碰主 checkout 状态、未访问 `~/.agate` 生产安装、未运行任何写生产环境/生产数据库/生产 API 的操作。
