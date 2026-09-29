# P0-brief — TAG0039 校验器健壮性批（真空通过根治 + 三处已复现缺陷）

> 主 Agent 亲自填写（P0 产出）。关联 RM：**RM-AG0077** + **RM-AG0080**（立项写作时实测发现，同族故并入本任务）。
> **来源**：peekview TPV0099 复盘 + 在 agateon HEAD 上**逐条独立复现**（2026-09-29）。
> **性质**：**gate 脚本判据修复**——不改状态机、不改流程语义，只让「跳过」与「通过」可区分，并修三个已被实测锁定的缺陷。
> **合并依据**：4 项同属「**校验器把不可判定/未判定 当成判定通过**」这一根因，且**全部落在 `agate/scripts/check-*.py` 同一目录**、改法都已被证据锁定、无需探索性设计 → 强合并单 task（先例：`TAG0029` gate 命令解析器修复批、`TAG0031` DEBT 存量修复批）。

```yaml
task: "根治校验器真空通过（13 个 check-*.py 的「跳过」与「通过」在退出码上不可区分），并修三个已实测复现的判据缺陷（scope-resolved 正则+未挂载 / provenance 奇数 --- 吞尾 / 内置 vitest formatter 环境变量超限）"
known_risks:
  - "🔴 改判据可能让既有任务历史产出由绿转红：必须对 agate-workspace/tasks 下全部任务跑改后脚本做前后对账，不能只看单测"
  - "同类/影响面预判：13 个脚本含真空通过（AST 枚举，非单点），须逐个处理；exit code 被 check-gate/pre-commit/agate-next/ci-backstop 消费"
  - "scope-resolved 放宽正则会改变 P7 结果，须先全量扫描存量（AGENTS.md 工作流第 0 条）"
  - "formatter 改动影响所有平台，须保持平台无关（Windows 无 mktemp 语义差异）"
  - "P0-brief 四字段格式（RM-AG0080）：extractor 读行首 YAML 键而先例用 markdown 标题 → 注入长期为空；同族第二面=_grep 对 known_risks 不回带列表"
env_constraints:
  debug_env: "无独立 debug 环境；验证=本 checkout 内 pytest + 对存量任务全量回归对账 + ≥1.5MB formatter 实测"
  platform: "dsh"
  network: "full"
  consistency_baseline: "386 WARNING / 0 ERROR"
executor_env:
  platform: "dsh"
  has_task_tool: true
  has_local_runtime: true
  network: "full"
```

## task

「根治校验器的**真空通过**（"跳过"与"通过"在退出码上不可区分），并修三个已实测复现的判据缺陷（`check-scope-resolved.py` 正则+未挂载、`check-p6-provenance.py` 奇数 `---` 吞尾、内置 vitest formatter 环境变量超限）。」

## 为何必须做（不是洁癖：已被误读一次、已在 CI 上误判）

TPV0099 实证：主 Agent 把 `check-scope-resolved.py` 的 `exit 0` 引为「SCOPE+ 已闭环」的证据，**被 P7 reviewer 用四状态矩阵推翻**——该 exit 0 是**真空通过**（脚本根本没进入判定分支）。同一族缺陷还会让 CI 误判 P3 FAIL。

## 实测证据（全部在 HEAD `84f10be` 复现）

### 证据 A：真空通过是**系统性**的（AST 精确实测）

`agate/scripts/` 23 个 `check-*.py` 中 **13 个**含「空条件 → `exit/return 0`」跳过分支（AST 判据：`if not X` / `len(X) == 0` 且该分支**首动作**即退出 0），其中 **11 个在该分支不输出任何原因**：

`check-changelog` / `check-debt` / `check-frontmatter` / `check-gate` / `check-maintainability` / `check-mvwu` / `check-p6-provenance` / `check-pruning` / `check-routing` / `check-scope-resolved` / `check-state-transition`

抽验两例确认命中为真：`check-state-transition.py:240-241`（空条件 → `sys.exit(0)`，静默）、`check-debt.py:76-77`（输出空 → `return 0`，静默）。

> **口径说明（避免本任务重犯自己批评的错）**：登记初稿曾用宽松 `grep` 得「20 个 / 8 个不输出」，**是高估**；AST 精确后为 **13 / 11**。P1 同类扫描**必须用可复现的判据**（AST 或等价），不得用宽松文本匹配。

### 证据 B：`check-scope-resolved.py` 两处叠加缺陷

```python
SCOPE_PLUS_RE = re.compile(r"^\s*-?\s*\[SCOPE\+\]", re.MULTILINE)   # 只匹配行首
...
scope_found = _scan_scope_plus(task_dir)
if not scope_found:
    sys.exit(0)          # ← 真空早退：从未进入 [SCOPE_RESOLVED] 判定
```

- 实测：`**[SCOPE+]** x` → 正则 **False**；`> [SCOPE+] x` → **False**；仅 `[SCOPE+] x` / `- [SCOPE+] x` → True。TPV0099 的 `P2-design.md:120` 正是粗体形态。
- **`check-gate.py` 根本不调用它**（`grep -c check-scope-resolved` = **0**）；真实调用方 `pre-commit-gate.py:439` 还带 `if gate_exit != 1` 前置 → **P7 gate 通过 ≠ SCOPE+ 被校验过**。

### 证据 C：`check-p6-provenance.py` 奇数 `---` 吞尾（判定位置依赖）

`check-p6-provenance.py:369-382` 剥离 frontmatter 用「遇 `---` 向后找下一个 `---`」逐对配对；**奇数个 `---` 时最后一个会吞掉其后至 EOF**。

- 独立复现：14 行构造输入 → 输出 **3 行**，违规行**与**尾部标记一并消失。
- 后果：同一违规放**被吞区间** → `exit 0`（漏检）；放**存活区间** → `exit 1`（检出）→ **同一违规因位置不同判定相反**。

### 证据 D：内置 vitest formatter 用环境变量传输出，超 `MAX_ARG_STRLEN`

`agate/assets/formatters/vitest.sh:6-8`：`OUTPUT="$(cat)"; export EXIT_CODE OUTPUT` → 整份测试输出经**环境变量**传给 `python3`。

- 独立复现：1,509,095 字节（本仓前端全量输出量级）→ **`OSError: [Errno 7] Argument list too long`**（`MAX_ARG_STRLEN = 131072`，超 11.5×）→ formatter exit 126。
- 误判链：formatter 失败 → 回退 `raw_output` → 命中 `check-tdd-red.py:110-121` 的 A 类分支（`raw_output` 含 `matching`）→ **误判假红灯**。
- **CI 同源中招**：`ci-gate-backstop.py:183` 对 `tdd_exit == 1` 判 **FAIL** → **本仓任何前端任务的 P3 在 CI 上都会被误判 FAIL**（另有 4 个声明 `P3_formatter: vitest.sh` 的存量任务）。
- 既有先例：TPV0099 已用**任务级 formatter**（`$task_dir/.agate/formatters/vitest.sh`，agate 官方扩展点）规避，**改法逐字可复用**。

### 证据 E：同族第 6 例在 gate 自身（本次由修补 roadmap 时实测暴露）

`check-gate.py::_check_roadmap_done`（RM-AG0043）对列数 ≠ 9 的行**整行 `continue` 跳过**（BDD-20 设计如此），而「无匹配行 → 返回 None → 不误拦」（BDD-6）→ 含**字面竖线**的 RM 行对 P8 done 反查**隐形**。

- **已有真实受害者**：`RM-AG0056`（11 列）/ `RM-AG0059`（12 列）长期隐形；实测其状态/关联任务列**全部错位**（`RM-AG0056` 的 status 列读到正则片段、关联任务列读到 `"done"`）。
- 数据面已由 **PR #369 修复**（`\|` → `&#124;`，全表 9 列）；**本任务修机制面**：列数异常行须**告警**而非静默跳过。
- 注：`46ba956` 曾试图用 `\|` 转义，但 `line.split("|")` **不认反斜杠转义** → 该「修复」无效。**这是本族缺陷最讽刺的实例：修它的人以为修好了。**

## scope

### 子批 A：真空通过根治（13 个脚本）

对 **13 个**含「空条件 → 静默 exit/return 0」的脚本，逐个在**跳过分支输出显式原因**（如 `GATE SCOPE: no line-start [SCOPE+] found; resolved-check skipped`），使「**未检出/未判定**」与「**已判定通过**」在输出上**可区分**。

- **不改**各脚本的判定语义与 exit code 约定（gate 消费方不受影响）
- 判据：**对每个脚本，构造"输入不存在"与"输入存在且合规"两种前置，两者输出必须不同**

### 子批 B：`check-scope-resolved.py`（证据 B）

- `SCOPE_PLUS_RE` 放宽以覆盖**粗体/引用**等常见包裹形态（或改为「行内出现 `[SCOPE+]` 即可」，P2 定）
- 早退分支输出显式提示
- **明确它与 gate 的关系**：纳入 `check-gate.py P7` 分支，**或**在协议中写明当前调用关系与前置条件（消除「P7 gate 通过即已校验」的误读）

### 子批 C：`check-p6-provenance.py` frontmatter 剥离（证据 C）

改为**只剥离文件顶部第一对 `---`**（起点判定 + 找不到闭合对时**不删除并告警**），或剥离后校验行数守恒。判据：同一违规放**任意位置**判定一致。

### 子批 D：内置 vitest formatter（证据 D）

`OUTPUT` 环境变量 → **临时文件**传输出（`TMP=$(mktemp); cat > "$TMP"; python3 - "$TMP"`），**判定语义逐字不变**。判据：**≥1.5MB 输入实测 exit 0 且 JSON 可解析**。

### 子批 E：`_check_roadmap_done` 列数异常告警（证据 E）

列数 ≠ `_ROADMAP_EXPECTED_COLS` 的行**输出 WARNING**（指明行号与列数），而非静默 `continue`；`无匹配行` 的不误拦语义**保持不变**（BDD-6 不回归）。

### 子批 F：P0-brief 四字段格式与消费方对齐（RM-AG0080）

**实测发现**：`agate-extract-context.py:104-110` 按**行首 YAML 键**读取 P0-brief 四字段（`^task:` / `^known_risks:` / `^env_constraints:`），而**实际先例用 markdown 标题**书写（`TAG0037`：`## task` / `### known_risks`）→

```
$ python3 agate/scripts/agate-extract-context.py P1 agate-workspace/tasks/TAG0037-install-package-model
### P0-brief 关键字段
            ← 零字段（P0→P1 上下文注入长期为空）
```

**同类第二面**：`_grep` 对 `known_risks:` 只回带**键行本身**（不回带其后列表），故即便格式正确该字段仍为空 → 应改用 `_grep_after`（`env_constraints` 已正确使用）。

**已实证可修**：本次 TAG0038-0041 的 P0-brief 按**卡内 YAML 块**书写，实测注入能取到 `task` 与 `env_constraints`。

**要求**：① 让 extractor 与**实际书写形态**一致（或让 P0 卡/模板写明唯一形态并统一先例）② `known_risks` 改用 `_grep_after` 回带列表 ③ 判据 = 对任一任务跑 extract-context 能取到**非空**三字段。

## 验收基线（倾向，P1 细化）

1. Given 13 个真空通过脚本 When 逐个构造「未检出」前置 Then **stderr 有显式跳过原因**，且与「已判定通过」的输出**可区分**
2. Given 粗体 `**[SCOPE+]**` / 引用 `> [SCOPE+]` 形态 When 跑 `check-scope-resolved.py` Then **能检出**（不再真空早退），且「未检出」与「已闭环」输出可区分
3. Given 文件含**奇数个** `---` When 跑 `check-p6-provenance.py` Then 尾部区间**仍参与审计 2**（同一违规放任意位置判定一致）
4. Given ≥1.5MB 测试输出 When 经内置 vitest formatter Then **exit 0 且 JSON 可解析**；且 `check-tdd-red.py` 不再因该缺陷误判 A 类
5. Given roadmap 含列数 ≠ 9 的行 When 跑 `check-gate.py P8` Then **有 WARNING 指明该行**（不再静默跳过），且合法的「无匹配行」仍不误拦
6. Given 全量 pytest When 跑 Then 全绿（改动不得破坏既有判据语义——**这是本类改动最大风险，见 known_risks**）
7. Given 任一任务的 P0-brief When 跑 `agate-extract-context.py P1` Then 取到**非空**的 `task` / `known_risks`（含列表）/ `env_constraints` 三字段

## known_risks

- **同类/影响面预判——同类实例**：**13 个脚本**含真空通过（已 AST 枚举，清单见证据 A）。**本任务须逐个处理，不能只修被报告的 `check-scope-resolved.py` 一处**——「只修被报告的那一处」是 agate 反复复发的反模式。P1 同类扫描须复核该清单（口径须可复现，不得用宽松文本匹配，见证据 A 口径说明）。
- **同类/影响面预判——上下游消费方**：`check-*.py` 的 exit code 被 `check-gate.py` / `pre-commit-gate.py` / `agate-next.py` / `ci-gate-backstop.py` 消费；子批 A 虽不改 exit code，但**新增 stderr 输出可能被既有测试断言**（`agate/tests/` 有大量对 stderr 的断言）。须先全量跑基线，改后逐条对账。
- **🔴 最大风险：改判据可能反过来破坏既有语义**。`check-p6-provenance.py` 的 frontmatter 剥离被**审计 2**（验收结论预判扫描）依赖；改法若让更多行参与扫描，**既有任务的历史产出可能由绿转红**（TPV0099 实测该文件被吞区间无违规，但不能假设所有任务都如此）。**必须对既有任务做全量回归**（对 `agate-workspace/tasks/` 下全部任务目录跑改后脚本，前后对账），不允许只看单测。
- **`check-scope-resolved.py` 放宽正则会改变 P7 结果**：放宽后能检出粗体形态 → 本仓既有任务中若有「含 `[SCOPE+]` 但无 `[SCOPE_RESOLVED]`」的，会在 P7 gate **由绿转红**。须**先全量扫描存量**（`AGENTS.md` 工作流第 0 条：新增 CHECK/规则上线前先全量扫描存量确认不误伤），把命中清单作为 P1 输入。
- **`formatter` 改动影响所有平台**：内置 formatter 是共享资产，改传输方式须保持**跨平台**（Windows 无 `mktemp` 语义差异——须用 `tempfile` 或平台安全的写法，参照仓库既有平台无关约定）。
- **CI 改动的许可边界**：若涉及 `.github/workflows/`（如 backstop 口径），需用户明确许可（`AGENTS.md` 规则 5）。**本任务倾向不改 CI**（修 formatter 后 backstop 自然不再误判），P1 须确认该判断。

## env_constraints

- 运行 agateon 只需系统 `python3` + `pyyaml`；开发另需 `ruff`（CI 锁 `0.16.4`）
- **本机环境**：`~/.agate` 为**版本管理布局**（`current` 指针）。**稳定版来源 = `~/.agate/current/`，不是本 checkout**——hook 判定恒用稳定版（已实证：`agate-resolve.py` → `AGATE_ROOT=~/.agate/vX.Y.Z/agate`；解析链 `AGATE_ROOT env > AGATE_HOME > .agate-version > current`，**无 cwd 相对回退**），故**改本 checkout 的 `agate/` 不影响 gate 判定**（该耦合已在 v0.73.0 版本布局解除）。`~/.agate/scripts/` 与 hook 同源——**本任务改的正是 gate 脚本**，故该纪律尤其关键：**跑 gate 判定用 `~/.agate`（稳定版，与 hook 同源、判定本次 commit），改代码/跑测试在本 checkout**
- **`check-protocol-consistency.py` 必须用本 checkout 自己的**（检查对象是本次改动的协议文件）
- **平台无关是硬约束**：测试不得裸 `python3`、不得用 `/tmp`（用 `tmp_path`）、不得假设 POSIX symlink；DSH 下 `/tmp` 只读、pytest 需 `--basetemp`
- 一致性基线：**386 WARNING / 0 ERROR**
- 新增 `check-*.py` 须同步登记面（**RM-AG0077 之外**：`TAG0036` 复盘的 DEBT0046 已登记「新增 check 脚本无登记面清单」，本任务**不重复处理**，仅在新增脚本时遵守该清单）
- **改动面全部触发 SELF-GATE**（`agate/scripts/*.py` / `agate/assets/formatters/`）→ 须独立评审 + `self-gate-review:` 引用

## executor_env

- **工作目录**：**worktree 非必需**——v0.73.0 版本布局后稳定版（`~/.agate/current`）与任何 checkout 已解耦，hook 恒用稳定版判定（已实证：`agate-resolve.py` → `AGATE_ROOT=~/.agate/vX.Y.Z/agate`），故本任务可**直接在开发 checkout 的分支上做**。**何时仍建议 worktree**：① 与其他任务**并行**（工作目录互不干扰）② 需要与 main 的 hotfix/合并操作**隔离**。若用 worktree：`git worktree add .worktrees/agate-TAG0039 -b fix/TAG0039-checker-robustness`，流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0039.md`- **稳定版工具**：`~/.agate/scripts/`（勿动）
- **证据来源**：`agate-workspace/roadmap/roadmap.md` 的 RM-AG0077 条目（含全部复现数据与行号）
- **先例参照**：`TAG0029`（gate 命令解析器修复批——同类「同源多脚本强合并单 task」先例）、`TAG0031`（DEBT 存量修复批——低风险脚本修复批先例）、`TAG0035`（gate 健壮性批——含 fail-open→fail-closed 修复先例）
- **关联外部证据**：peekview 项目登记簿 DEBT0014（formatter）/ DEBT0015（scope-resolved）/ DEBT0016（provenance）——三条均为 `category: protocol`、`task_id` 指向 TPV0099；本任务即其在 agateon 侧的落地

## 裁剪倾向

- **P2 完整走**（多决策点：正则放宽形态 / frontmatter 剥离改法 / formatter 跨平台写法 / 列数告警形态）
- **P3 保留**（每条判据均可单测：构造未检出/已检出/奇数 `---`/大输出，**负向对照可写**）
- **P6 不可裁**（须端到端实跑证据：≥1.5MB formatter 实测 + 存量任务全量回归前后对账）
- **P7 完整走**（跨 13+ 脚本 + 可能与 gate 挂载关系变更，多文件改动）
- **P8**：协议脚本改动 → 需 bump（**非破坏性**：不改 exit code 语义、不改状态机；若子批 B 改为纳入 gate P7 导致存量转红，须在 CHANGELOG 明确标注）

## 不做的事（边界）

- **不做**协议比例阀 / 度量 / 债务可见性（**TAG0038** 范围）
- **不做**派发成本治理（**TAG0040** 范围）
- **不做** RM-AG0079（轻量改动通道）
- **已并入**：RM-AG0080（P0-brief 四字段格式与消费方对齐，子批 F）——**不再另立任务**
- **不改** `check-*.py` 的判定语义与 exit code 约定（本任务只让「跳过」可见 + 修三个已锁定缺陷）
- **不重做** DEBT0045/0046（P6→P7 卡顿与新增 check 登记面）——已由 **TAG0036 复盘的 RM-AG0068** 承接，本任务**不重复**
- **不改** `.github/workflows/`（除非 P1 证明确有必要且取得用户许可）
