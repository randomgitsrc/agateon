---
type: review
phase: P4
task_id: TAG0050
parent: P4-implementation-G3.md
trace_id: TAG0050-P4-20261008
agent: cso
status: approved
---
# P4-review-cso — TAG0050 批 G3（D + E + F）安全维度独立评审

- **评审对象**：TAG0050 合批 G3（批次 D 验收结论与证据 + 批次 E 成对声明 + 批次 F 代理判定）的**未提交**实现；
  HEAD `b746d07d`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0）。
- **范围**：`P4-dispatch-context-cso-G3.md` 的 6 个重点核验项（安全面）；不重做设计，只审安全边界与绕过面。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本**（`/tmp/opencode/csoG3/`：`cp -r agate` 副本、
  一次性 git 仓 `repo/`、R6 用干净副本 `r6repo/`）上做可复现验证；不改被评审文件、不写仓。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/csoG3/` 下的一次性 git 仓与裸文件副本中进行。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **MEDIUM** |
| CRITICAL | 0 |
| HIGH | 0 |
| MEDIUM | 2（F-1：D3 `run:<k>` 的 sha256 校验在事件缺 `sha256` 字段时 **fail-open**；F-2：`declaration_files` glob 扩展后两消费方**匹配语义不一致**，`P4-implementation/**/*.md` 子目录文件逃逸 frontmatter 强制） |
| LOW | 4（F-3 空 `run:` 日志免检；F-4 `blocker_count` 未登记为系统字段；F-5 跨文件聚合信任面；F-6 非 legacy SCOPE+ 结构化路径） |
| 是否阻塞发布 | **否** —— 无 CRITICAL / BLOCKER；G3 的 6 个重点核验项中「判定依据不可改写」「legacy 兼容」「系统字段不被汇总值盖住」**均通过**；F-1/F-2 为防御纵深缺口（威胁模型内不含故意伪造，且 F-2 不使被拦任务变绿），建议随批收紧 |
| status | `approved` |

## 二、STRIDE 矩阵（G3 改动面）

| 威胁 | 适用性 | 结论 |
|---|---|---|
| **S**poofing | 低 | 无新身份面；`set agent` 权限非安全边界（ADR-014，与 G2 结论一致） |
| **T**ampering | **中** | D1/D2/D7/D9 已把「结论与证据」绑定，`results` 强制生效；**F-1**：`run:<k>` 的 sha256 校验存在静默关闭分支（事件缺 `sha256` 字段即不校验）；**F-2**：声明文件 glob 的两消费方语义分叉，子目录声明文件不受 frontmatter 强制 |
| **R**epudiation | 低 | D3 事件缺失 → fail-closed；D9 复用检测现算；账本追加经 `append_event` 哈希链 |
| **I**nformation disclosure | 低 | 无新日志/响应泄露面 |
| **D**enial of service | 低 | 聚合/证据扫描为线性；`_p6_reuse_blocked` 单次 `git diff` |
| **E**levation of privilege | 低 | 无新权限面；`resolve_evidence_ref` 经 realpath 限界，无路径穿越（实测越界/软链逃逸被拒） |

## 三、6 个重点核验项逐条结论

| # | 核验项 | 结论 |
|---|---|---|
| 1 | 证据不可伪造（D） | **基本通过**：D1/D2/D3/D4/D6/D7/D9 + `results` 强制均按设计生效（见「五」）。**但** D3 `run:<k>` 的 sha256 校验有 fail-open 分支（**F-1**），且空 `run:` 日志免检（**F-3**） |
| 2 | 判定依据不可改写（E/F） | **通过**：`reviewed_bdds` 缺失/不等 → ERROR；`phases ∪ pruned == phase_universe` **恒检**；`resolved` 缺证据 → ERROR；`blocker_count` 汇总值**盖不住**门禁（gate 独立现算）；骨架**标题级**判定；P8 `delivery` **结构化**（正文子串不再算声明） |
| 3 | 系统字段现算（B 落地、G3 是否破坏） | **通过（附观察 F-4）**：`pass`/`fail` 经 `derive` 现算、文件值不被信任；G3 未破坏（`_gate_p6_structured` 全程不读 `pass`/`fail` 文件值）。**但** `blocker_count` 未登记为 `writer: system`（见 F-4） |
| 4 | 跨文件聚合的信任面（E） | **通过（附观察 F-5）**：聚合只读快照 `declaration_files` 命中的文件；无签名（威胁模型内不含伪造）；未引入**新的门禁绕过**（`resolved` 字符串信任为设计 §6 明示边界） |
| 5 | 快照单源（`declaration_files` glob） | **不通过** —— **F-2**：同一快照键被 `glob.glob(recursive=True)`（聚合）与 `fnmatch`（frontmatter 强制）以**不同语义**消费，`P4-implementation/**/*.md` 的**直接子文件**在 frontmatter 面免检；`check-frontmatter` 更因 `task_dir=dirname(file)` 使子目录文件 `_task_is_non_legacy` 恒 False |
| 6 | legacy 兼容（§8） | **通过**：独立重跑 R6 差分（干净副本 `r6repo/`）→ **legacy 39 任务 / 差异 0 / 未匹配 0 / exit 0**；定向 legacy 用例（P6 旧路径、`check-pruning` 不闭合、`check-frontmatter` 不强制）逐条不变 |

## 四、发现详述

### F-1（MEDIUM）— D3 `run:<k>` 的 sha256 校验在事件缺 `sha256` 字段时 fail-open

**声明 vs 实现**：设计 §5.3 要求 `cmd_run` 事件带 `k`/`log`/`sha256` 三字段，D3「校验文件的 sha256 与事件记录一致」；
实现（`agate_common.py:1712-1724`）仅在 `isinstance(recorded, str) and recorded` 为真时才比对：

```python
recorded = ev.get("sha256")
if isinstance(recorded, str) and recorded:
    ...比对...
return path, None          # ← 字段缺失/空/非字符串 → 静默放行
```

`cmd_run` 事件缺失已 **fail-closed**（`:1710-1711`），但「事件存在而 `sha256` 字段缺失」是**等价的更易绕过路径**——
攻击者只需追加一条 `{"event":"cmd_run","k":1}`（无需 `sha256`）即可让被篡改的 `runs/1.log` 通过 D3。

**证据（仓外副本，非 legacy，真 `check-gate.py P6`）**：
```
(a) 事件完全缺失        → rc=1  "run:1 的 cmd_run 事件缺失（无法核验 sha256，fail-closed）"
(b) 事件存在但无 sha256 → rc=2  "结构化 results 判据 D1–D10 通过"   ← 篡改后的日志被信任
    （对照：带正确 sha256 时篡改日志 → rc=1 "sha256 与 cmd_run 事件不一致"）
```
**威胁模型边界**：设计 §1 声明「不防故意伪造」；诚实路径（`agate-run --task`）恒写 `sha256`，故本条主要危害是**防御纵深的静默关闭**（同一机制一半 fail-closed、一半 fail-open），非对抗性伪造。**建议**：把「`sha256` 缺失/非字符串」与「事件缺失」同判 fail-closed（报 ERROR）。

### F-2（MEDIUM）— `declaration_files` glob 扩展后两消费方匹配语义不一致，子目录声明文件逃逸 frontmatter 强制

**声明 vs 实现**：GAP-8 将快照 `declaration_files` 扩展为 glob（含 `P4-implementation/**/*.md`，`level-1.yaml:103-115`）并声称「单源」。
但该键被**两种匹配器**消费，语义不同：

| 消费方 | 匹配方式 | `P4-implementation/**/*.md` 对**直接子文件** `P4-implementation/x.md` |
|---|---|---|
| 聚合（`check-gate._aggregate_list` / `check-scope-resolved` / `check-retrospective`） | `glob.glob(..., recursive=True)` | **命中**（`**/` 匹配零层） |
| frontmatter 强制（`check-frontmatter._is_declaration_file`、`pre-commit-gate._is_declaration_path`） | `fnmatch` | **不命中**（`fnmatch` 的 `*` 跨 `/`，但 `**/*.md` 仍要求至少一层子目录） |

叠加 `check-frontmatter.py:128` 用 `task_dir = os.path.dirname(os.path.abspath(file_path))`（**文件自身目录**，非任务根）——
子目录文件的 `_task_is_non_legacy`（`:72-73` 同用 dirname）恒为 `False`，frontmatter 强制**整段跳过**。

**证据（仓外副本，真 `check-frontmatter.py`，非 legacy 任务 TAG9022）**：
```
P4-implementation/direct.md      （无 frontmatter）→ rc=0   ← 应 ERROR，实际免检
P4-implementation/sub/nested.md  （无 frontmatter）→ rc=0   ← 应 ERROR，实际免检
P4-implementation-batch1.md      （无 frontmatter）→ rc=1   ← 顶层文件正常拦截（对照组）
# 匹配器语义对照（Python 实测）：
#   glob  'P4-implementation/**/*.md' → ['P4-implementation/direct.md', 'P4-implementation/sub/nested.md']
#   fnmatch 同 pattern               → ['P4-implementation/sub/nested.md']   （缺 direct.md）
```
**影响与边界**：这正是 dispatch 第 5 项所指的「未匹配即免检」口子。因**聚合**面（较宽）不漏声明、
且声明本就必须带 frontmatter 才被聚合，故本条**不使任何被拦任务变绿**，危害限于「非 legacy 声明文件须有 frontmatter」
（BDD-47/F10）在该 glob 子面**未被强制**。GAP-8 的测试（对齐复评 ⑤b）只覆盖顶层 `P4-implementation-*.md`，
**无子目录 glob 用例** → 闭合声明不完整。**建议**：两消费方统一为同一匹配器（如都走 `glob.glob(recursive=True)` 语义），
并修正 `check-frontmatter` 的 `task_dir` 解析（向上找含账本/`.state.yaml` 的目录，`agate-md-field-set._task_dir_for` 已有同款实现）。

### F-3（LOW）— `run:<k>` 引用缺「非空文件」判据

`resolve_evidence_ref` 对**相对路径**引用检查 `os.path.getsize(path) == 0`（`:1728-1732`），对 **`run:<k>`** 引用
（`:1698-1724`）无此检查，仅校验存在 + 事件 + sha256。设计 §5.1 D3 要求「解析到一个**非空文件**」。

**证据（仓外副本）**：
```
runs/1.log 为 0 字节 + 账本 cmd_run.sha256 为空文件的哈希 → rc=2 "D1–D10 通过"
（对照：相对路径引用指向空文件 → rc=1 "引用的证据文件为空"）
```
威胁模型内影响低（`agate-run` 产出的日志恒非空）。**建议**：`run:` 分支补 `getsize==0` 判据。

### F-4（LOW）— `blocker_count` 未登记为系统字段（与「系统字段现算」声明不符）

快照 `files` 节只登记 `P6-acceptance.md`（`pass`/`fail` 带 `derive`）；**无** `P7-consistency.md` 条目，
故 `blocker_count`/`deviation_critical_count` **不是** `writer: system`，`agate-md-field-get blocker_count` 返回**文件值**
（实测：文件写 `blocker_count: 0` → 取值为 `0`）。G3 的 `agate-extract-context.py:272-277` 对非 legacy **按系统字段读取**
`blocker_count`，与该键未登记的事实矛盾（读到的仍是作者自报值）。

**为何不阻塞**：真正的门禁 `_gate_p7_structured`（`check-gate.py:1772-1793`）**不读** `blocker_count`，而是
`count_p7_markers(P7 正文) + 结构化 open findings` **独立现算** → 汇总值**盖不住**（F2 已闭合，实测：正文 `[BLOCKER]` +
`blocker_count: 0` → rc=1）。**建议**：若 `extract-context` 要当系统字段用，应在快照登记 P7 计数（或改回现算）。

### F-5（LOW / 观察）— 跨文件聚合的信任面

`_aggregate_list`（`check-gate.py:1714-1729`）从**所有** `declaration_files` 命中文件聚合 `findings`/`design_gaps`/
`design_gap_reviews`/`code_map*`/`scope_plus` 等，包含 `*-review.md` 与 `P4-implementation-*.md`；**不限制**哪种声明只能出自哪类文件
（如 `design_gap_reviews` 可写在 P4 文件）。设计 §6 明示「结构化本身不阻止把 BLOCKER 置 resolved」，
且全仓无签名（同信任级）→ **不构成新的门禁绕过**，仅记录为边界。集合相等判据（`dg_ids == rev_gaps`）仍要求全覆盖。

### F-6（LOW / 观察）— 非 legacy 的 SCOPE+ 只认结构化声明

`check-scope-resolved.py:140-151` 对非 legacy 只比对**聚合**的 `scope_plus`/`scope_resolved` id 集合；
正文 `[SCOPE+]`（或写在非声明文件者）不触发 `scope_resolved` 强制。该面由批 B 的 T1 绊线（含 `SCOPE+` 标记）作后盾
（`e3_sampling_required_before_error` 未启用前为软约束）。记录为边界，非 G3 新增。

## 五、已独立验证的安全面（通过项）

> 全部在仓外副本 `/tmp/opencode/csoG3/` 上运行，构造非 legacy 任务（账本首行 `task_created` level=1）。

1. **D3 sha256 篡改检测**：`run:1` 带正确 sha256 → rc=2；追加篡改日志后 → rc=1「sha256 与 cmd_run 事件不一致」。✓
2. **D3「已跟踪或已暂存」真拦**（`AGATE_PRECOMMIT_GATE=1`，一次性 git 仓）：证据**已提交/已暂存** → D3 通过；
   **未跟踪且未暂存** → rc=1「在 pre-commit 中未跟踪且未暂存」。`_is_tracked_or_staged` 对 `resolve_evidence_ref`
   返回的**绝对路径**（`git ls-files --error-unmatch <abs>` / `git diff --cached -- <abs>`）实测有效。✓
   （`run_git is None` 的 fail-open 分支不可达：同因 `resolve_evidence_ref is None` 先报错返回。）
3. **D3 事件缺失 fail-closed**：无 `cmd_run` 事件 → rc=1。✓
4. **D6**：引用日志尾行 `EXIT_CODE: 1` → rc=1；无 `EXIT_CODE` 尾行按设计（§5.1 条件式）不报。✓
5. **D7**：`results` 标 PASS 而 `P6-evidence/*.json` 的 `bdd_results` 标 fail → rc=1「evidence JSON 显示 FAIL 但 results 标 PASS」。✓
6. **D9**：声明复用（`p5_evidence_reuse: true`）且 `p5_pass_commit..HEAD` 有非产出改动 → rc=1；无改动 → rc=2。✓
7. **GAP-1 `results` 强制**：非 legacy 缺 `results` → rc=1（不回退正文/汇总）。✓
8. **F `reviewed_bdds`**：缺失 → rc=1；`[]` 与 P1 `['1']` 不等 → rc=1；相等 → 通过。✓
9. **F `phases ∪ pruned` 恒检**：`phases` 缺 `P4` 且未声明 `pruned` → rc=1（缺=['P4']）；`pruned` 覆盖 P4 后该错消失。✓
10. **F P8 `delivery` 结构化**：正文子串 `delivery:` → rc=1；`method=none` 缺 `reason` → rc=1；`method≠none` 缺 `ref` → rc=1。✓
11. **E `resolved` 缺证据**：P7 finding 标 resolved 但缺 `evidence` → rc=1。✓
12. **E/F2 汇总值盖不住**：结构化 open blocker + frontmatter `blocker_count: 0` → rc=1「BLOCKER=1…不被汇总值盖住」。✓
13. **legacy 兼容（§8）**：独立重跑 `docs/design-notes/r6-differential.sh`（干净副本）→ **39 legacy / 0 差异 / 0 未匹配 / exit 0**；
    定向用例：legacy P6 走旧路径（rc=2）、legacy `check-pruning` 不做闭合、legacy `check-frontmatter` 不强制 frontmatter。✓
14. **无新增注入/穿越/DoS 面**：`resolve_evidence` realpath 限界（越界/软链逃逸 → None）；聚合/证据扫描线性。✓

## 六、验证留痕

- **仓外副本根**：`/tmp/opencode/csoG3/`（`agate/` 副本；一次性 git 仓 `repo/` 下 TAG9001/9003/9004/9011-9013/9020-9022/9030/9031/9040/9050/9060/9070；R6 干净副本 `r6repo/`）。
- **关键命令**：
  ```
  # F-1 / F-3 / D3
  AGATE_ROOT=$ROOT/agate python3 $ROOT/agate/scripts/check-gate.py P6 <task>            # 各分支 rc 见正文
  AGATE_PRECOMMIT_GATE=1 AGATE_ROOT=$ROOT/agate python3 .../check-gate.py P6 <task>     # 未跟踪证据 → rc=1
  # F-2
  AGATE_ROOT=$ROOT/agate python3 .../check-frontmatter.py <task>/P4-implementation/direct.md   → rc=0
  AGATE_ROOT=$ROOT/agate python3 .../check-frontmatter.py <task>/P4-implementation-batch1.md   → rc=1
  # F-4
  FILE=<task>/P7-consistency.md .../agate-md-field-get.py blocker_count                  → 0（文件值）
  # §8
  bash docs/design-notes/r6-differential.sh --corpus .                                  → 39 / 0 / 0 / exit 0
  ```
- **真实仓库只读核验**：评审前后被评审文件（`git diff --name-only HEAD`）逐行未变；未写仓、未改被评审文件。

## 七、返回给主 Agent

- **最高严重级别**：MEDIUM
- **各级问题数**：CRITICAL 0 / HIGH 0 / MEDIUM 2 / LOW 4
- **是否阻塞发布**：**否**（无 CRITICAL / BLOCKER；F-1/F-2 建议随批收紧）
- **status**：`approved`
