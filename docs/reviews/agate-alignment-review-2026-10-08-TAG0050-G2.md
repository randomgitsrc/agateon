---
review_date: 2026-10-08
reviewer: protocol-alignment-review
task_id: TAG0050
batch: G2 (B + C)
change_summary: TAG0050 批 G2——写入工具与契约单源（agate_schema.py + 7 操作 + 渲染块 + F10 缺 frontmatter ERROR）与生产接触安全门（prod_touched + T4 单一来源）
files_changed: [agate/scripts/agate_schema.py(new), agate/scripts/agate-md-field-set.py, agate/scripts/agate-config.py, agate/scripts/agate-frontmatter-check.py, agate/scripts/check-yaml-schema.py, agate/scripts/check-frontmatter.py, agate/scripts/check-gate.py, agate/scripts/pre-commit-gate.py, agate/scripts/README.md, agate/rules/markers.yaml, agate/rules/task-data/level-1.yaml, agate/rules/task-data/LEVELS.yaml, agate-workspace/agents/CODE-MAP.md]
---

# 协议-脚本对齐审查（TAG0050 批 G2）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（快照 `declaration_files` 无消费方；F10 实际作用面与快照/设计不符） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（`agate/scripts/README.md` 的 `agate-config.py` 索引行未随 set/unset/explain 更新） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（`declaration_files` 死键 + `pre-commit-gate.py:809` 硬编码；`design-md-field-set.md` §7.2 陈旧） |
| A4 | 测试覆盖 | **MISALIGNED**（BDD-52 判据落空；BDD-53/48/50 弱测试；CRLF 无覆盖） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（UPGRADING G2 节 / design note §7.2 / tests/README 映射未传播） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED（DESIGN_GAP-1 与 ADR-014 一致） |
| A8 | 声称-命令绑定 | **NEEDS_HUMAN_REVIEW**（E3 抽样数字无命令；consistency WARNING 数 410↔实测 412） |

> 6 条 `[DESIGN_GAP]` 逐条裁定结果：GAP-1 可接受；**GAP-2 可接受（附闭合建议）**；**GAP-3 必须闭合**；GAP-4 可接受（附保留意见）；GAP-5 可接受；GAP-6 可接受。详见文末「DESIGN_GAP 逐条裁定」。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明 1**（`agate/rules/task-data/level-1.yaml:74-81`，即快照的权威作用面）：
> ```yaml
> # 声明文件（批 B/C 消费；§3.6）：缺 frontmatter / 缺 prod_touched 判 ERROR 的作用面。
> declaration_files:
>   - P1-requirements.md
>   - P2-design.md
>   - P6-acceptance.md
>   - P6.5-judge-verdict.md
>   - P7-consistency.md
>   - P8-release.md
> ```

**脚本实现**（`agate/scripts/check-frontmatter.py:21-41`）：
> ```python
> _FALLBACK_DECLARATION_FILES = frozenset({
>     "P1-requirements.md", "P2-design.md", "P6-acceptance.md", "P7-consistency.md",
> })
> def _declaration_files():
>     ...
>     files = contract.get("files") if isinstance(contract, dict) else None
>     if isinstance(files, dict) and files:
>         return frozenset(files.keys()) | _FALLBACK_DECLARATION_FILES
> ```

**结论**：**MISALIGNED**。

- `_declaration_files()` 读的是快照的 **`files`**（逐文件字段契约，其定义仅含 `P6-acceptance.md`）而非 **`declaration_files`**；`grep -rn "declaration_files" agate/ --include=*.py` 无任何消费方（`agate/scripts/check-frontmatter.py:25` 只是同名函数，不读该键）⇒ 快照新键 `declaration_files` 是**死数据**。
- 实际生效面 = `{P1-requirements.md, P2-design.md, P6-acceptance.md, P7-consistency.md}`（硬编码 fallback）；与快照声明的 6 文件相比**缺 `P6.5-judge-verdict.md` / `P8-release.md`**；与设计 `docs/design-notes/design-tag0050-task-data-contract.md:558`「覆盖各阶段主产出、`*-review.md`、`P4-implementation-*.md`、`P4-implementation/**/*.md`」相比缺得更多。
- 复现：`python3 -c` 读契约键集合即可确认（`files` 键 = `{P6-acceptance.md}`）。

**建议**：`_declaration_files()` 改读 `contract.get("declaration_files")`（保留 fallback 仅作安装破损降级）；`pre-commit-gate.py:809` 的硬编码元组 `("P1-requirements.md","P2-design.md","P6-acceptance.md","P7-consistency.md")` 同步改为读快照键。

---

### A2: 脚本→文档对齐

**脚本变更**（`agate/scripts/agate-config.py` diff）：新增 `set`/`unset`/`explain` 子命令，`_usage()` 已更新。

**对应文档**（`agate/scripts/README.md:164`）：
> `| agate-config.py | 项目形态声明（agate.config.yaml）读写/校验：init（幂等，不覆盖）/ validate（schema 校验）/ get <field> / list / show；... |`

**结论**：**MISALIGNED**（低严重度）。
索引行仍只列 `init/validate/get/list/show`，未列 G2 新增的 `set`/`unset`/`explain`；G2 的 README diff 只加了 `agate_schema.py` 一行（:84），未动 :164。
**建议**：把 :164 的命令集合更新为 `init/validate/get/set/unset/explain/list/show`。

（其余脚本→文档方向：`check-frontmatter.py` / `check-gate.py` / `check-yaml-schema.py` / `agate-frontmatter-check.py` 的行为变更属内部实现，未见需要同步的协议 md 叙述段——除 A3/A5 指出的项外。）

---

### A3: 一致性连锁 + 反向传播

**A3a 连锁（diff 内应改）**：`check-frontmatter.py` 引入的 `_declaration_files()` 与快照 `declaration_files` 不同源（见 A1）。

**A3b 反向传播（应被影响但 diff 未列出的文件，逐一验证）**：

| 应被影响文件 | 理由 | 验证结果 |
|---|---|---|
| `agate/scripts/README.md:164` | `agate-config.py` 命令集变更 | **未同步**（A2） |
| `agate/tests/integration/test_pre_commit_hook.py:809` 对应面 | 新增快照 `declaration_files` 应取代硬编码 | **未同步**（`pre-commit-gate.py:809` 仍硬编码 4 文件） |
| `docs/design-notes/design-md-field-set.md` §7.2 | DESIGN_GAP-1 解除 agent 拒写，该 design note 变陈旧 | **未标注**（`:252` 仍写「`agent` 字段不可被 set 改写」） |
| `agate/UPGRADING.md` | G1 加了「未发布 — TAG0050 批 G1」节；G2 引入 F10 + prod_touched 行为变更 | **缺 G2 节**（`grep "G2.*TAG0050"` 无命中） |
| `agate/tests/README.md` | 登记面 ⑤（脚本→测试映射，约定） | 无 `agate_schema` 映射行（约定项，非门禁） |
| `agate/adr.md` | DESIGN_GAP-1 的设计原则 | ADR-014 已覆盖「引导型 CLI 权限非安全边界」⇒ 无需新增 ADR |

**结论**：**MISALIGNED**（根因同 A1：新快照键 `declaration_files` 与两处消费面不同源；其余为文档传播滞后）。
**建议**：先闭合 A1 的同源问题；文档传播项按 A5 处理。

---

### A4: 测试覆盖

**实跑输出（本审查环境）**：
```
$ python3 -m pytest agate/tests/unit/test_tag0050_write_tools.py \
    agate/tests/integration/test_tag0050_prod_touched.py \
    agate/tests/unit/test_tag0050_fitness.py -q
14 passed in 1.21s
$ python3 -m pytest agate/tests/unit/test_marker_single_source.py -q
36 passed（与上合并跑 50 passed）
```
（仅此 4 文件在本审查中实跑；全量 `pytest agate/tests/{unit,integration}` 未重跑——见 A8。）

**问题 1（致命，对应 DESIGN_GAP-3）：BDD-52 的验收测试不能为 BDD-52 转红——判据落空。**

- 测试 `test_tag0050_prod_touched.py:19-27` 的机制：
  ```python
  d = h.init_task_via_conftest(tmp_path)
  r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P1", str(d))
  assert r.returncode != 0, "BDD-52：缺 prod_touched 须 ERROR"
  ```
- **命令查证**：`grep -n "prod_touched" agate/scripts/check-gate.py` → 无匹配（rc=1）。`check-gate.py` 根本不读 `prod_touched`，故 `rc!=0` 与该 BDD 无关。
- **复现实测**（仓外副本 `/tmp/opencode/G2rev/`）：按 `conftest.init_task` 造非 legacy 任务后
  ```
  $ AGATE_ROOT=<repo>/agate python3 agate/scripts/check-gate.py P1 <task>
  GATE P1: 契约要求 judge（level-1 requires.judge: true）须在 .state.yaml 声明 judge.enabled: true ...
  RC=1
  ```
  → `rc=1` 来自 **judge 要求**，与缺 `prod_touched` 无关。
- `P4-progress.md:272` 亦自陈「BDD-46/52/53 … 已绿」——即该用例在 G2 实现**之前**就是绿的 ⇒ 它对本次交付无判别力。
- 结论：BDD-52 的 When 是「提交」，而唯一落地的 `prod_touched` 逻辑在 `pre-commit-gate.py:_check_prod_touched_primary`（只做 `true`→中止，**未做缺字段→ERROR**）。测试既未驱动该强制点，也未断言缺字段错误。**MISALIGNED**（详见 DESIGN_GAP-3 裁定）。

**问题 2：BDD-53 的验收测试是同义反复。**
`test_bdd_53_prod_touched_true_not_paused_aborts`（:30-33）只断言快照文本含 `"prod_touched"`，不驱动任何强制点。实际 `true`→中止行为**已实现且实测有效**（本审查在仓外 git 副本实测 `prod_touched: true` → `rc=1`，报「声明 prod_touched: true 且当前不在 PAUSED（P4），commit 中止」），但**无端到端用例锁定**，回归无守护。

**问题 3：BDD-48 的验收测试弱且缺 CRLF 覆盖。**
`test_bdd_48_render_block_tamper_errors`（:76-88）只断言 `rc != 0`；对被手改的渲染块，`gate_p6` 即使不命中渲染块也会因缺 PASS/FAIL 汇总而失败 ⇒ 无法判别渲染块判据是否生效；且**未断言修复命令文案**、**未覆盖 CRLF**（BDD-48 Then 明确含「CRLF 规范化为 LF 后逐字节比较；CRLF 下行为一致」），也**未加 `@pytest.mark.windows_smoke`**（设计 §3.5 明示「这项检查纳入 windows_smoke」）。全仓 `grep` 未发现任何 CRLF 断言。

**问题 4：BDD-50 的守护是子串判定，且仍存在第二处递归实现的降级副本。**
`test_schema_single_source_only_agate_schema` 只断言三个文件源码含 `"agate_schema"` 子串；而 `agate/scripts/agate-frontmatter-check.py:167-208` 保留了 `_local_iter_errors` / `_local_max_depth` / `_local_type_ok` 一套**递归校验副本**（安装破损降级路径）。字面上「只剩 1 个 schema 校验实现」不成立（副本是不完全子集，无 array/items/pattern）。可辩护为刻意的 fail-safe，但守护未覆盖该事实。

**结论**：**MISALIGNED**（问题 1 为 BDD 判据落空，必须闭合；问题 2/3/4 为弱守护，建议补强）。

---

### A5: 下游影响 + 文档传播

- **对既有项目 gate 行为的破坏性变更**：G2 使非 legacy 任务的 `prod_touched: true`（非 PAUSED）提交中止（BDD-53，已生效）。F10/缺字段 ERROR 目前未生效（GAP-2/3），一旦闭合即为破坏性面。
- **CHANGELOG**：本任务按 P8 统一写（延后），非本批缺口。
- **UPGRADING.md**：G1 已加「未发布 — TAG0050 批 G1」节，G2 未加对应节（见 A3b）。若「每批加未发布节」是既定口径，则为缺口；若统一 P8 写，则可辩护。
- **design-md-field-set.md §7.2**：原文「`agent` 字段不可被 set 改写（防伪造身份）」已被 DESIGN_GAP-1 取代，无任何标注，后续读者会读到矛盾口径。

**结论**：**NEEDS_HUMAN_REVIEW**（需人工定：UPGRADING 按批写还是 P8 写；design note §7.2 是否本批加注）。
`[HUMAN_CONFIRMED: 待主 Agent 确认]`

---

### A6: 锚点表覆盖

- `python3 agate/scripts/check-protocol-consistency.py` → **CHECK 9 PASS**、**CHECK 16 PASS**，0 ERROR。
- 新增脚本 `agate_schema.py` 属 `agate_*.py`，**不在** CHECK9-coverage 门禁面（该判据只 glob `check-*.py` / `pre-commit-gate.{sh,py}`，见 `agate/scripts/README.md:12-15`），故无需进 `SCRIPT_ALIGNMENT_ANCHORS`；G2 已在 README 工具表登记（:84）与 CODE-MAP 登记（「契约校验单源族」）。
- 未发现「新增协议规则需要新锚点而未加」的情形（G2 未新增 md 叙述型规则）。

**结论**：**ALIGNED**。

---

### A7: 设计原则一致性

- DESIGN_GAP-1（解除 `agent` 拒写）与 `agate/adr.md` ADR-014（`adr.md:416-431`，「引导型 CLI 工具的权限检查不是安全边界」）一致；亦与 `design-md-field-set.md:267` §7.4「set 权限不是安全边界」一致。故解除该限制不违反已记录架构决策。
- 未发现需要新增 ADR 的未记录架构决策。

**结论**：**ALIGNED**（附：`design-md-field-set.md` §7.2 应加注「已被 TAG0050 取代」——属文档传播，见 A5）。

---

### A8: 声称-命令绑定

| 声称（`P4-implementation-G2.md §6`） | 产出它的命令 | 结论 |
|---|---|---|
| 3 测试文件 **14 passed** | `pytest …write_tools …prod_touched …fitness -q` | ✅ 复核 = 14 passed |
| consistency **0 ERROR / 410 WARNING** | `python3 agate/scripts/check-protocol-consistency.py` | ⚠️ 实测 **0 ERROR / 412 WARNING**（+2 = 新增未跟踪任务文件，皆 frozen）；数字应更新或注明「随工作树变化」 |
| count-tests **2833**（=G1 基线） | `bash agate/tests/scripts/count-tests.sh` | ✅ 复核 = 2833 |
| platform **0 命中** | `python3 agate/scripts/check-platform-assumptions.py` | ✅ 复核 rc=0 |
| ruff **All checks passed** | `ruff check agate/scripts/` | ✅ 复核 |
| 全量 **8 failed / 2720 passed / 2 skipped** | `pytest agate/tests/{unit,integration} -n auto` | ⚠️ 本审查未重跑全量（成本）；未复核 |
| §4 E3 抽样 `~48/~2`、`~49/~1`（两仓各抽 50，seed=20261008） | —（§7 自陈「抽样脚本置于 `/tmp/opencode/`（未入库）」） | ❌ **无仓内可复现命令** ⇒ 该数字类声称按 A8 应删除，或把抽样脚本+种子入库并给出命令 |

**结论**：**NEEDS_HUMAN_REVIEW**（E3 数字无据；consistency 计数与实测不符）。
`[HUMAN_CONFIRMED: 待主 Agent 确认]`

建议：① 删除 §4 的精确数字（或改「见 E3 抽样证据文件」并入库脚本）；② §6 的 consistency 计数改为「0 ERROR，WARNING 数随工作树新增未跟踪文件浮动」。

---

## DESIGN_GAP 逐条裁定

> 依据 `P4-implementation-G2.md §5`（6 条）。任务尚在 P4、无 P7 `REVIEWED-ACCEPTED` 记录，故按角色定义不自动降级为 KNOWN_DEVIATION，逐条裁定如下。

### DESIGN_GAP-1 — 解除 `agent` 拒写 —— **可接受**

- BDD-45（P1 活基线）显式要求 `set agent writer` rc=0（`test_tag0050_write_tools.py:35`），该用例在 G2 前为红、G2 后转绿 ⇒ 属**契约驱动的行为变更**，非实现迁就。
- 与 ADR-014 一致（set 端权限「引导，非安全边界」）。
- 唯一遗留：`design-md-field-set.md` §7.2 该加注「已被 TAG0050 取代」（归 A5）。

### DESIGN_GAP-2 — F10 经 `AGATE_PRECOMMIT_GATE=1` 在 hook 路径被跳过 —— **可接受（附闭合建议）**

- **关键判据：BDD-47 的 When 是「校验」，不是「提交」**（`P1-requirements.md:376`）。`check-frontmatter.py` 的直接调用路径返回 ERROR —— 实测：
  ```
  $ python3 agate/scripts/check-frontmatter.py <non-legacy task>/P6-acceptance.md   # 无 frontmatter
  GATE FRONTMATTER: … 非 legacy 任务的声明文件缺 frontmatter 块 … → RC=1
  $ AGATE_PRECOMMIT_GATE=1 python3 …（同一文件）→ RC=0    # hook 路径被跳过
  ```
  且 `test_bdd_47` 在 G2 前为红、G2 后转绿（`P4-progress.md:272`）⇒ **BDD-47 的验收锚未落空**。
- 但**设计 §3.6 写的是「gate 侧（非 legacy 任务）：声明文件必须有 frontmatter（修复 F10）」**，而 G2 恰恰在 gate 侧（hook）把它关掉；结合 A1 的 `declaration_files` 死键，F10 在 gate 侧**零强制力**。
- 裁定：**本批可接受**（BDD-47 字面为「校验」且直接路径已生效）；但须记为**待闭合**：下一批接线时（a）删 `AGATE_PRECOMMIT_GATE` 跳过，（b）`check-frontmatter.py` 改读 `declaration_files`，（c）更新既有 `test_pre_commit_hook.py` 夹具（见下「附带裁定」）。

### DESIGN_GAP-3 — BDD-52「缺 `prod_touched` → ERROR」未接强制点 —— **必须闭合（MISALIGNED）**

- **BDD-52 的 When 是「提交」**（`P1-requirements.md:402`），强制点应在 pre-commit；但 `pre-commit-gate.py:_check_prod_touched_primary` **只实现 `true`→中止，未实现缺字段→ERROR**（源码注释 `:537-542` 自陈）。
- **验收测试不能为 BDD-52 转红**（A4 问题 1 已给可复现证据）：
  - `grep prod_touched agate/scripts/check-gate.py` 无命中；测试却在 `check-gate.py P1` 上断言 rc≠0；
  - 实测该 rc=1 来自 **judge 要求**；
  - 且用例在 G2 前即绿。
- **实证「无强制点」**（仓外 git 副本）：非 legacy 任务、`P4-implementation.md` 缺 `prod_touched`、`P4-review.md` approved → `pre-commit-gate.py` 输出 `GATE P4 (T0001): 通过`，**RC=0**。
- ⇒ 判据落空（弱测试）。按 dispatch 明示口径判 **MISALIGNED**。
- **最小修复建议**：① 在 `_check_prod_touched_primary` 补「缺字段 → ERROR + 修复命令」（`FILE=… agate-md-field-set.py set prod_touched false <值>`）；② 重写 `test_bdd_52` 走真实强制点（真实 git repo + 安装 hook 提交，如 BDD-54/55 的手法），断言「缺字段」错误文案；③ 既有 `test_pre_commit_hook.py` 夹具随契约更新（见下）。

**附带裁定**：**「改既有 `test_pre_commit_hook.py` 夹具（补 frontmatter / `prod_touched`）」是正解。**
理由：这些夹具代表**合法的非 legacy 任务提交**（如 `_write_state_yaml(..., legacy=False)` 播种 `task_created`），按**新契约**它们的主产出本就必须带 frontmatter 与 `prod_touched`。夹具编码的是**旧契约**；随新契约更新夹具属**契约驱动的夹具演进**（同 A1 批已用过的 §8 例外机制），不属于「改测试迁就实现」（后者是削弱断言以迁就有缺陷的实现）。故 DESIGN_GAP-2/3 的正确闭合路径 = 接线强制点 + 更新夹具，而非「跳过」或「另寻路径」。
（实测依据：`test_pre_commit_hook.py` 的 P6 夹具如 `:623/:647/:671/:750` 部署了**无 frontmatter** 的 `P6-acceptance.md`；`_P1_REQ`(:433) 虽有 frontmatter 块但 `risk_level/phases` 落在块外。）

### DESIGN_GAP-4 — E3 误报 >0 → T1 降级 —— **可接受（附保留意见）**

- BDD-51 的 Then 是「误报为 0；**若不为 0，已按设计 §3.6 落实降级**」（`P1-requirements.md:396`）。G2 已在 `level-1.yaml:101-104` 落 `traps.T1.downgrade`（`files: [P7-consistency.md, P8-release.md]` / `action: warning` / `requires_field_write: true`）。按 BDD-51 的允许分支，**可接受**。
- **保留意见**：`traps.T1/T2/T3` 与 `T1.downgrade` **无任何 gate 侧消费方**（`grep 'traps\[' agate/scripts/*.py` 无命中；T1 未启用 ERROR、T2/T3 未接线）⇒ 该「降级」当前是**惰性数据**，`requires_field_write` 无人执行。即在「降级」与「未启用」之间，G2 实际选的是**未启用**，不是「降级后启用」。若设计 §3.6「T1–T3 绊线」是本批交付面，则属未接线；若本批只交付数据，则应把该留待后续批的接线登记为显式待办（建议在 `P4-implementation-G2.md §5` 明确写出）。
- 另：E3 抽样数字无仓内可复现命令（A8）。

### DESIGN_GAP-5 — 保留一处字面正则 —— **可接受**

- 验证：`test_marker_single_source.py:384` 用 `re.search(r're\.match\(r"([^"]*\\\[PROD_TOUCHED\\\][^"]*)"', gate_src)` 从 `pre-commit-gate.py` **源码文本**抽取消费方正则；`mk_8`(:419) 抽取 `^\s*-?\s*\[(PROD_[A-Z_]+)\]`。源码中唯一满足者 = `pre-commit-gate.py:755` 的 `re.match(r"^\s*-?\s*\[PROD_TOUCHED\]\s*$", ln)`。⇒ 删净该字面会使 mk_7b/mk_8 转红（成立）。
- 该字面**另有真实用途**：它是「裸标记格式」检查，对 `-[PROD_TOUCHED]`（无空格）等 `default` 口径不命中而 `dash_only` 命中的边角形态可达。
- 真正的安全门（`:747`）已改调 `agate_markers.pattern("PROD_TOUCHED")`，单源成立；`mk_3`（render ⊂ pattern）随 `lead_variant: default` 仍通过（本次实跑 50 passed 含 marker_single_source）。
- 裁定**可接受**；建议后续把 mk_7b/mk_8 改为从 `agate_markers` 取值后再删该字面（消除「为测试而保留的字面副本」）。

### DESIGN_GAP-6 — 同任务内对 `level-1.yaml` 追加键并重登记 sha256 —— **可接受**

- 验证：`sha256sum agate/rules/task-data/level-1.yaml` = `e96a06b2a7c7…`，与 `LEVELS.yaml` 登记值一致；`check-protocol-consistency.py` **CHECK 16 PASS**。
- 与 §2.1 冻结规则（改快照须重登记 sha256）一致，且 `level-1.yaml:9-10` 注释本就声明「其余键为后续批次（B/C/D/E/F）的契约数据，随本快照一并冻结登记」⇒ 属预期演进。**可接受**。

---

## 遗留项与建议（供主 Agent）

| 编号 | 项 | 严重度 | 建议 |
|---|---|---|---|
| R1 | BDD-52 判据落空（DESIGN_GAP-3） | **BLOCKER** | 接线「缺字段→ERROR」+ 重写 `test_bdd_52` 驱动真实强制点（见裁定） |
| R2 | `declaration_files` 死键 / F10 作用面不符（A1/A3） | 高 | `check-frontmatter.py` 与 `pre-commit-gate.py:809` 改读快照键；同步容差 |
| R3 | BDD-48 缺 CRLF/修复命令/windows_smoke 覆盖（A4） | 中 | 补 CRLF 用例 + 断言修复命令 + 打 `windows_smoke` 标记（设计 §3.5） |
| R4 | BDD-53 弱测试、BDD-50 子串守护（A4） | 中 | 补端到端 prompt 中止用例；schema 单源守护改为「无第二递归实现」的机械判据 |
| R5 | README `agate-config.py` 行陈旧（A2） | 低 | 更新 :164 命令集合 |
| R6 | UPGRADING G2 节 / design note §7.2 / tests/README（A5） | 低 | 人工定型口径后补齐 |
| R7 | E3 数字无命令、consistency 计数 410↔412（A8） | 低 | 删除/迁移无据声称；更新计数或注明浮动 |

## 闭环判断

存在 1 项 **BLOCKER**（R1 / DESIGN_GAP-3，MISALIGNED）与若干 MISALIGNED/NEEDS_HUMAN_REVIEW ⇒ **本轮不可直接 commit（须先修复 R1 或由人工裁定并留痕）**。R1 修复后应重审 BDD-52 相关面。
