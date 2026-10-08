---
type: review
phase: P4
task_id: TAG0050
parent: P4-implementation-G2.md
trace_id: TAG0050-P4-20261008
agent: cso
status: approved
---
# P4-review-cso（第 2 轮复评）— TAG0050 批 G2（B+C）安全维度聚焦复审

- **评审对象**：TAG0050 合批 G2 的 C8 第 2 轮整改（`P4-dispatch-context-implementer-G2-fix2.md` 落实）；
  HEAD `54a814fc`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0），改动未提交。
- **范围**：**只核**首轮 cso 的 F-1/F-2/F-3 是否闭合 + F-4/F-5/F-6 是否仍成立 + 是否引入**新安全阻断**。
  不重做设计、不重评已通过项。
- **方法**：静态读码（引 `文件:行`/diff）+ 在**仓外可丢弃副本**（`/tmp/opencode/csoG2r2/`）上做可复现验证；
  未改被评审文件、未写仓。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/csoG2r2/` 下的一次性 git 仓与裸文件副本中完成。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **LOW**（无 CRITICAL / HIGH / MEDIUM 未闭合项） |
| CRITICAL | 0 |
| HIGH | 0（首轮 F-1 已闭合） |
| MEDIUM | 0（首轮 F-2/F-3 已闭合） |
| LOW | 2（新观察：F-1 降级路径 fail-open；F-3 每次扫描派生一次子进程——均非阻断） |
| 是否阻塞发布 | **否** —— F-1/F-2/F-3 全部闭合；无新引入的安全阻断 |
| status | `approved` |

## 二、STRIDE 矩阵（第 2 轮整改面）

| 威胁 | 适用性 | 结论 |
|---|---|---|
| **S**poofing | 低 | `set agent` 可写为设计有意解除（BDD-45 / ADR-014：set 权限非安全边界），与首轮结论一致；非新增面 |
| **T**ampering | 低（原高） | **F-1 已闭合**：`writer: system` 字段读取改按快照 `derive` 现算、忽略文件值；下游消费方随之生效 |
| **R**epudiation | 低 | 安全门命中即 `sys.exit(1)` + `prod_touched_in_paused` 留痕；F-3 绕过面已收紧 |
| **I**nformation disclosure | 低 | 无新日志/响应泄露面 |
| **D**enial of service | 低 | F-3 的 `_expected_card_hash` 每次扫描派生一次 `agate-next-card.py`（有界，非放大） |
| **E**levation of privilege | 低 | 无新权限面；F-2 拒写收紧、未误伤合法写入 |

## 三、逐条复核

| # | 原问题 | 第 2 轮结论 | 证据 |
|---|---|---|---|
| **F-1**（HIGH 阻塞） | BDD-46 `derive` 现算读取未实现；P6 汇总伪造值被信任 | **ALIGNED（闭合）** | 见 §四.1 |
| **F-2**（MEDIUM） | 系统字段拒写非契约 `writer: system` 语义 | **ALIGNED（闭合）** | 见 §四.2 |
| **F-3**（MEDIUM） | T4 的 CARD 块排除是纯文本，可伪造绕过 | **ALIGNED（闭合）** | 见 §四.3 |
| **F-4**（LOW） | 单源残留 / 降级口径 | 仍成立（已声明 DESIGN_GAP-5 / L4） | 见 §四.4 |
| **F-5**（LOW） | 降级副本与等级口径 | 仍成立（L6 已声明）；L1 口径已统一 | 见 §四.5 |
| **F-6**（LOW 非安全） | 非原子写 / `os.getcwd()` | 仍成立；H1 修复命令行注解已分行 | 见 §四.6 |

## 四、发现详述

### F-1 — CLOSED

**声明 vs 实现**：`agate-md-field-get.py` 新增 `_system_field_spec()`（`agate-md-field-get.py:255-283`）与
`_get()` 内现算分支（`:288-305`）：当 `op` 存在于 frontmatter、且 `FILE` 所属任务为**非 legacy**、且快照可用时，
调 `agate_schema.derive(spec["derive"], fm)`，**忽略文件里的值**；快照不可用/legacy/字段缺失 → 回退既有语义。
契约源：`agate/rules/task-data/level-1.yaml:69-70`（`pass`/`fail` = `writer: system` + `derive`）。

**独立验证（仓外副本，命令 + 输出）**：
```
# /tmp/opencode/csoG2r2/f1/tasks/TAG9001：账本 task_created contract_level=1（非 legacy）；
#   P6-acceptance.md 写伪造 pass: 999 / fail: 0，results 含 2 条 FAIL
$ FILE=.../P6-acceptance.md AGATE_ROOT=<repo>/agate python3 agate-md-field-get.py pass  → 0   （忽略 999）
$ FILE=.../P6-acceptance.md AGATE_ROOT=<repo>/agate python3 agate-md-field-get.py fail  → 2   （忽略 0）
$ # 对照：删账本（legacy）→ 回退文件值
$ FILE=.../f1legacy/.../P6-acceptance.md ... agate-md-field-get.py pass  → 999   （声明过的边界）
$ # 字段缺失（无 pass 键）→ 空串（保持「无声明→调用方回退」语义）
$ FILE=.../f1miss/.../P6-acceptance.md ... agate-md-field-get.py pass  → （空）
```

**下游消费方随之生效（独立验证）**：
```
# check-gate.py P6（非 legacy，伪造 fail:0 + 2×FAIL）
$ AGATE_ROOT=<repo>/agate python3 agate/scripts/check-gate.py P6 /tmp/opencode/csoG2r2/p6
GATE P6: FAIL=2, TOTAL=2        → rc=1   （修复前用文件值 fail:0 会通过）
# 对照 legacy：GATE P6: …FAIL=0…P6_TOTAL=999 → rc=2（旧行为面）
# check-p6-provenance.py 审计3（P1 有 3 条 BDD，伪造 pass:999/fail:0，2×FAIL）
$ AGATE_ROOT=<repo>/agate python3 agate/scripts/check-p6-provenance.py /tmp/opencode/csoG2r2/prov
GATE PROVENANCE: P6 结果数(2) < P1 BDD 条目数(3)，挑验不通过   → rc=1
# 对照 legacy：…pass+fail=999… → rc=2（旧行为面）
```
两个消费方均经 `agate-md-field-get.py` 取值（`check-gate.py:1270-1271`、`check-p6-provenance.py:604-610`），
故现算对二者**自动生效**，无需改消费方（与设计 §3.3 一致）。

**验收用例判别力**：`test_tag0050_write_tools.py:92-121` 已重写为「文件写 `pass: 999` + results 2×PASS+1×FAIL →
断言 get=2」；本复评独立重跑该文件 **16 passed**（`test_bdd_46…` 在内）。

**新观察（LOW，非阻断）**：F-1 的**降级路径是静默 fail-open**——当 `agate_common`/`agate_schema` 不可导入
（安装破损）时 `_system_field_spec` 返回 None，`_get` 回退文件值且**不告警**：
```
$ # 副本目录放一个 raise ImportError 的 agate_schema.py
$ FILE=.../P6-acceptance.md AGATE_ROOT=<repo>/agate python3 <copy>/agate-md-field-get.py pass  → 999
$ stderr: []     （无 WARNING）
```
仅安装破损时出现，与既有降级哲学（F-5/L6）一致；建议后续可在降级时补一行 WARNING（可选）。

**新观察（LOW，设计已接受）**：`pass`/`fail` 非 `required`，**删除**这两个键即回退到旧「正文 `- PASS|FAIL BDD-N`
计数」路径（代码注释显式声明「避免把未写误判为现算 0」）。此非新伪造面（等价于 legacy 行为），且设计 §3.1 第 6 点
已排除「故意伪造（说谎的 agent）」威胁模型，不计为阻断。

### F-2 — CLOSED

**整改**：`_cmd_set`（`agate-md-field-set.py:428-437`）在可写性判定**之前**加契约驱动判定：
凡快照 `files` 节登记 `writer == "system"` 的字段一律拒写并指明 `derive` 来源。
可写面（`:456-460`）改为 `phases.yaml task_fields ∪ 通用 Header ∪ 契约字段 ∪ 声明文件安全字段`。

**独立验证（仓外副本协议根，注入未来系统字段）**：
```
# 在 /tmp/opencode/csoG2r2/root/rules/task-data/level-1.yaml 的 files.P6-acceptance.fields 加
#   future_sys: {writer: system, derive: "count(results, verdict == PASS)"}   （不在证据字段表内）
$ FILE=.../P6-acceptance.md AGATE_ROOT=/tmp/.../root agate-md-field-set.py set pass 3
ERROR: pass 是系统字段（writer: system），由契约现算，不可手动填写；来源: derive count(results, verdict == PASS)   rc=1
$ ... set future_sys 1
ERROR: future_sys 是系统字段（writer: system）…；来源: derive …   rc=1   ← 契约驱动（非偶发耦合）成立
# 未误伤合法写入：
$ ... set prod_touched true   → OK: prod_touched=true 已写入   rc=0
$ ... set agent x             → OK: agent=x 已写入            rc=0
```
⇒ F-2 的核心诉求（**未来**新增系统字段亦被拒、不靠证据字段表偶发耦合）已落地；合法写入未被误伤。

### F-3 — CLOSED

**整改**：CARD 块排除由「纯文本 START/END 区间」收紧为「真实注入块」——`_card_block_verified()`
（`pre-commit-gate.py:275-280`）要求**文件名匹配 `-dispatch-context-*.md`** 且**块内容 sha256 ==
当前阶段卡片期望值**（`_expected_card_hash()` 与 2p 同源）；主循环 2g.0 与
`_scan_prod_touched_and_rerun` 均改调 `_added_lines_excluding_real_cards()`（`:282-320`）。未闭合 START fail-safe 参与扫描。

**独立验证 1（端到端 rc=1，真实 `pre-commit-gate.py`）**：
```
# /tmp/opencode/csoG2r2/f3：TAG0001/P5-test.md（非 dispatch-context）内 **[PROD_TOUCHED]** 夹伪造 CARD 块
$ AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/pre-commit-gate.py
GATE: [PROD_TOUCHED] 检测到生产环境接触（TAG0001），commit 中止   → rc=1   （首轮此处 rc=0）
# /tmp/opencode/csoG2r2/f3b：文件名匹配 *-dispatch-context-*.md，但块内容伪造（hash 不匹配）
$ ... pre-commit-gate.py   → GATE: [PROD_TOUCHED] … commit 中止   → rc=1
```

**独立验证 2（helper 单测，5 场景，monkeypatch `_expected_card_hash`）**：
```
1 real card（dispatch-context 名 + hash 匹配）  -> marker excluded: True
2 forged content（同名，hash 不匹配）           -> marker kept: True
3 non-dispatch-context 文件名                   -> marker kept: True
4 未闭合 START                                  -> marker kept: True   （fail-safe）
5 标记不在块内                                  -> marker kept: True
```
⇒ 只有**真实注入**的卡片块被排除；伪造块/非 dispatch-context 文件/未闭合块内标记**仍拦**。首轮 F-3 绕过面闭合。

**独立验证 3（无回归）**：重跑 `test_pre_commit_hook.py`（含真实 hook 路径）**62 passed**、
`test_tag0050_fitness.py` **3 passed**（合计 65 passed）。

### F-4（LOW）— 仍成立，已声明

- 运行期安全门已单源化：`_PROD_TOUCHED_RE = agate_markers.pattern("PROD_TOUCHED")`（`pre-commit-gate.py:246-249`），
  `markers.yaml` 的 `lead_variant: default`（`:132`）。regex 实测 `- / ** / > / * / + / 否定写法` 全命中、
  行首反引号不命中（见下）。
- **仍成立**：单源库不可用时的降级字面 `re.compile(r"^\s*-?\s*\[PROD_TOUCHED\]")` 仍是 **dash_only 口径**
  （实测 `match('**[PROD_TOUCHED]**')=False`）⇒ 安装破损下粗体/引用块形态（BDD-54）会被静默放行（fail-open）。
- **仍成立**：`:822` 保留字面 `re.match(r"^\s*-?\s*\[PROD_TOUCHED\]\s*$")`（DESIGN_GAP-5 / L4 已裁定可接受）。
- 行首反引号 `[PROD_TOUCHED]` 不命中（`exclude.backtick`，与旧门一致，非回归）。

### F-5（LOW）— 仍成立，已声明；L1 口径已统一

- `agate-frontmatter-check.py:167-215` 的 `_local_*` 递归副本仍保留（门控 `agate_schema is not None`，L6 已声明）；
  与单源语义一致，不构成绕过面。
- **L1 已修**：`check-frontmatter.py::_declaration_files(task_dir)` 改按**任务等级**（回退协议当前等级），
  与 `pre-commit-gate.py::_declaration_files(task_dir)` 同口径（diff 实测两处均为 `task_level(...) or current_level(...)`）。

### F-6（LOW / 非安全）— 仍成立；H1 已修

- `agate-config.py:_write_config` 仍用非原子 `open(..., "w")`；`main` 仍用 `project_root = os.getcwd()`
  （`agate-config.py:314`）。均非安全项（首轮 F-6 定性不变）。
- **H1 已修**：`pre-commit-gate.py:_check_prod_touched_primary` 的修复命令与中文注解**分行**输出
  （命令行可整行照抄，注解不再被吃进 value）；`test_bdd_49_fix_command_executes_and_turns_green` 真「提交报错→照抄执行→转绿」用例存在且通过。

## 五、新引入安全阻断核查

| 面 | 结论 |
|---|---|
| F-2 拒写是否误伤合法写入 | **否**：`set prod_touched true` / `set agent x` 均 rc=0（§四.2） |
| F-1 降级路径是否引入新信任面 | **是，但仅安装破损下的静默 fail-open（LOW）**，与既有降级哲学一致，非阻断（§四.1） |
| F-3 收紧是否误伤真实注入卡片 | **否**：helper 场景 1（真实块）正确排除；`test_pre_commit_hook.py` 62 passed |
| F-3 派生 `agate-next-card.py` 是否可 DoS | 每次扫描一次、有界（按暂存任务数），且失败即 `None` → 不排除（fail-safe，更严）；非放大 |
| 新注入 / 路径穿越 / 越权 | 未见新增面（F-2 仅收紧、F-3 仅收紧、F-1 仅读取侧现算） |

## 六、验证留痕

- **仓外副本根**：`/tmp/opencode/csoG2r2/`（`f1/`、`f1legacy/`、`f1miss/`、`p6/`、`p6legacy/`、`prov/`、
  `provlegacy/`、`f2/`、`root/`（注入未来系统字段的协议根副本）、`f3/`、`f3b/`、`degrade/`）。
- **关键命令**（详见 §四）：
  ```
  # F-1
  FILE=<f1 P6> AGATE_ROOT=<repo>/agate python3 agate-md-field-get.py pass  → 0 ; fail → 2
  AGATE_ROOT=<repo>/agate python3 agate/scripts/check-gate.py P6 <p6>        → rc=1（FAIL=2）
  AGATE_ROOT=<repo>/agate python3 agate/scripts/check-p6-provenance.py <prov>→ rc=1（2<3）
  # F-2
  FILE=<f2 P6> AGATE_ROOT=<root> python3 agate-md-field-set.py set future_sys 1 → rc=1
  # F-3
  (cd <f3> && AGATE_ROOT=<repo>/agate python3 <repo>/agate/scripts/pre-commit-gate.py)  → rc=1
  (cd <f3b> && … pre-commit-gate.py)                                                    → rc=1
  # 无回归
  pytest -p no:cacheprovider -q test_tag0050_write_tools.py test_tag0050_prod_touched.py   → 16 passed
  pytest -p no:cacheprovider -q test_tag0050_fitness.py test_pre_commit_hook.py             → 65 passed
  ```
- **真实仓库只读核验**：评审前 `git status --porcelain` modified=**21** / untracked=**19**；
  评审后 modified=**21**（未变）/ untracked=**20**——增量恰为 `?? docs/reviews/tag0050-g2-cso-rereview-01.progress.md`
  与本产出文件；被评审文件逐行未变（未写仓、未改被评审文件）。

## 七、返回给主 Agent

- **最高严重级别**：LOW
- **各级问题数**：CRITICAL 0 / HIGH 0 / MEDIUM 0 / LOW 2（新观察）
- **是否阻塞发布**：**否**（F-1/F-2/F-3 全部闭合；无新安全阻断）
- **status**：`approved`
