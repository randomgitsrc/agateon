---
type: review
phase: P4
task_id: TAG0050
parent: P4-implementation-G2.md
trace_id: TAG0050-P4-20261008
agent: cso
status: rejected
---
# P4-review-cso — TAG0050 批 G2（B+C）安全维度独立评审

- **评审对象**：TAG0050 合批 G2（批次 B 写入工具与契约单源 + 批次 C 生产接触安全门）的**未提交**实现；
  HEAD `54a814fc`（分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0）。
- **范围**：`P4-dispatch-context-cso-G2.md` 的 5 个重点核验项（安全面）；不重做设计，只审安全边界与绕过面。
- **方法**：静态读码（引 `文件:行`）+ 在**仓外可丢弃副本**上做可复现验证（`/tmp/opencode/csoG2/`）；
  不改被评审文件、不写仓。真实仓库评审前 `git status --porcelain` = 33 行，评审后 = 34 行（+1 即本评审产出文件自身；被评审文件逐行未变，见「六、验证留痕」）。
- **环境隔离**：`[PROD_NOT_TOUCHED]` 全部验证在 `/tmp/opencode/csoG2/` 下的一次性 git 仓与裸文件副本中进行。

## 一、结论汇总

| 指标 | 值 |
|---|---|
| 最高严重级别 | **HIGH** |
| CRITICAL | 0 |
| HIGH | 1（F-1：BDD-46 的 `derive` 现算读取未实现，P6 汇总可被伪造/漏写值被信任） |
| MEDIUM | 2（F-2 系统字段拒写非契约语义；F-3 T4 扫描面可被伪造 `AGATE_CARD` 块绕过） |
| LOW | 3（F-4 单源残留/降级口径；F-5 降级副本与等级口径；F-6 非安全观察） |
| 是否阻塞发布 | **是** —— F-1：G2 验收项 BDD-46 的 Then 后半「读取返回按 `derive` 现算的值（忽略文件里的值）」**未实现**，且其验收用例无判别力；非 legacy 任务的 P6 汇总（`pass`/`fail`）仍是文件值，本任务「可信写入/防伪造」的核心目标在该点落空 |
| status | `rejected` |

## 二、STRIDE 矩阵（G2 改动面）

| 威胁 | 适用性 | 结论 |
|---|---|---|
| **S**poofing | 低 | `set agent` 的拒写被 DESIGN_GAP-1 有意解除（ADR-014：set 权限非安全边界）；与既有决策一致，不新增身份伪造面 |
| **T**ampering | **高** | **F-1**：`writer: system` 字段（P6 `pass`/`fail`）的「现算」防篡改机制未落地，`agate-md-field-get.py` 直读文件值 → `check-gate.py:1270` 与 `check-p6-provenance.py:603` 均信任该值。**F-2**：system 语义未在写入面落地 |
| **R**epudiation | 中 | 安全门命中即 `sys.exit(1)` 并有 `prod_touched_in_paused` 留痕；无「静默放行」新面（除 F-3 绕过） |
| **I**nformation disclosure | 低 | 无新日志/响应泄露面；安全门输出仅路径与标记名 |
| **D**enial of service | 低 | 无新增循环/资源放大；`_check_render_blocks`/`find_render_blocks` 为线性扫描 |
| **E**levation of privilege | 低 | 无新权限面；`agate-config set` 仅就地更新已存在声明（不创建），无路径穿越（`os.path.join(project_root, CONFIG_FILE)`） |

## 三、5 个重点核验项逐条结论

| # | 核验项 | 结论 |
|---|---|---|
| 1 | T4 单一来源 + 扫描面绕过面 | **基本通过**：运行期安全门确已改调 `agate_markers.pattern("PROD_TOUCHED")`（`pre-commit-gate.py:246-249`），`markers.yaml` 的 `lead_variant: default`（`:132`），粗体/引用块/`*`/`+`/否定写法均命中（regex 实测）。**但**扫描面存在两处可绕过边角（**F-3** 伪造 `AGATE_CARD` 块、任务目录外标记不扫）与单源残留（**F-4**） |
| 2 | 字段可信：T4 优先于字段 | **通过**：2g.0 标记扫描（`pre-commit-gate.py:750-778`）先于 2g.3 字段检查（`:781`），命中即 `exit(1)` 不看字段值；BDD-54 用例（粗体 + 字段 `false`）驱动真实 `pre-commit-gate.py` 并断言中止 |
| 3 | 系统字段拒写（BDD-46） | **不通过** —— **F-1**：`derive` 现算读取未实现（`agate-md-field-get.py` 未改动、`agate_schema.derive()` 无消费方）；**F-2**：拒写走的是「证据字段」路径而非契约 `writer: system` 语义 |
| 4 | `agate_schema.py` 单源（BDD-50） | **通过**（附观察 F-5）：三处消费方均委托单源；`agate-frontmatter-check.py` 的降级副本仅在 `agate_schema is not None` 为假时启用，语义是其所用 schema 子集，不构成绕过面 |
| 5 | legacy 兼容（§8） | **通过**（附观察）：F10/prod_touched 均以 `task_level`/`requirement_active` 门控为「非 legacy 才生效」；legacy 面唯一新增拦截是 `PROD_TOUCHED` 口径由 `dash_only` 放宽到 `default`，已登记为允许差异 **D12**（`P2-design.md` §3.3） |

## 四、发现详述

### F-1（HIGH，阻塞）— BDD-46 的 `derive` 现算读取未实现，P6 汇总可被伪造/漏写值被信任

**声明 vs 实现**：`P4-implementation-G2.md` §1 将 BDD-46 标 ✅，但落地物只含「证据字段拒写路径 + 快照 `files...derive` 数据」，**未落地读取侧的现算**。
设计 §3.3 明确：「对非 legacy 任务，`agate-md-field-get` 读取 `writer: system` 的键时按 `derive` 现算，忽略文件里的值。经 md-field-get 取值的消费方（check-gate 中 P6、P7 的计数，`check-p6-provenance.py`，`agate-feedback.py`）不需要改代码。」

**证据 1（无消费方）**：
```
$ grep -rn "agate_schema.derive\|\.derive(" agate/scripts/ --include=*.py
（无命中；derive 仅在 agate_schema.py 定义、agate-md-field-set.py:613 打印）
$ git diff --name-only HEAD -- agate/scripts/agate-md-field-get.py
（空 = 未改动）
```
`agate-md-field-get.py:_get()`（`:240-249`）对 `pass`/`fail`（∈`NO_FALLBACK_INT_FIELDS`）只做「frontmatter 有则返回文件值，无则空串」，无 derive。

**证据 2（伪造/漏写值被信任，仓外可复现）**：
```
# /tmp/opencode/csoG2/P6-acceptance.md：results 含一条 FAIL，但汇总写 pass: 999 / fail: 0
$ FILE=/tmp/opencode/csoG2/P6-acceptance.md python3 agate/scripts/agate-md-field-get.py pass   → 999
$ FILE=/tmp/opencode/csoG2/P6-acceptance.md python3 agate/scripts/agate-md-field-get.py fail   → 0
$ python3 agate/scripts/agate_schema.py --derive "count(results, verdict == FAIL)" '{"results":[{"bdd":"1","verdict":"FAIL"}]}'  → 1
# 非 legacy 任务（账本 task_created level=1）跑 check-gate P6：
$ AGATE_ROOT=<repo>/agate python3 agate/scripts/check-gate.py P6 <task>   （results 含 FAIL、汇总 fail: 0）
GATE P6: 证据目录非空，FAIL=0，NC=0，P6_TOTAL=1。…   ← 伪造的 fail:0 通过了 fail 计数判定
```
消费方 `check-gate.py:1270-1275`（`pass_fm`/`fail_fm`）与 `check-p6-provenance.py:603-612` 都经 `agate-md-field-get.py` 取该文件值。

**证据 3（验收用例无判别力）**：`test_tag0050_write_tools.py:52-64` 的夹具 `p6` 内容为 `---\nagent: test\n---\n\nbody\n`——**从未写入 `pass` 值**，故断言 `"3" not in g.output` 恒真（`pass` 缺失 → 空串），无法检出「读取侧现算」是否实现。这与对齐审查已判 BLOCKER 的 BDD-52「判据落空」同类（`docs/reviews/agate-alignment-review-2026-10-08-TAG0050-G2.md` R1），但该审查未覆盖本条。

**威胁模型边界说明**：设计 §3.1 第 6 点 / §1 声明「不防故意伪造（说谎的 agent）」。因此 F-1 的**主要**危害不是对抗性伪造，而是：① 「消除漏写」的既定机制缺位——诚实但汇总未同步的 agent 的 `pass`/`fail` 被当作权威；② 本任务 P0 的 `known_risks` 明列 F2「P7 汇总值盖住 BLOCKER」，同类「汇总值可被改/可漏写」在 P6 侧未闭合。**修复建议**：`agate-md-field-get.py` 读 `writer: system` 键时调用 `agate_schema.derive(spec['derive'], fm)`（快照 `files` 节），文件值仅在快照不可用时降级使用；并把 `test_bdd_46` 的夹具改为「文件里写 `pass: 999` + `results` 含 FAIL」以取得判别力。

### F-2（MEDIUM）— 系统字段拒写非契约 `writer: system` 语义

`_cmd_set`（`agate-md-field-set.py:391-423`）的可写面 = `_writable_keys ∪ _contract_fields(file).keys()`，其中 `_contract_fields` 含 `pass`/`fail`（`writer: system`）。`set pass` 之所以被拒，是因为 `pass` 恰在 `get_mod.NO_FALLBACK_INT_FIELDS`（证据字段表，`:401-404`）——是**偶发耦合**，非契约语义：
```
$ FILE=<P6> agate-md-field-set.py set pass 3
ERROR: pass 是证据字段，由验证脚本产出，不可手动填写   （rc=1；未提 writer:system/derive）
```
⇒ 任何**未来**新增、且不在证据字段表内的 `writer: system` 字段将可被 `set` 写入（BDD-46 的「系统字段拒写」未成为契约驱动的性质）。另：`explain pass` 在解析不到快照（未设 `AGATE_ROOT`）时把来源误报为「phases.yaml task_fields / 通用 Header」。**建议**：在 `_cmd_set` 增加 `writer == "system"` 判定（拒写并指明 `derive` 来源）。

### F-3（MEDIUM）— T4 扫描面的 `AGATE_CARD` 块排除是纯文本的，可被伪造绕过

`pre-commit-gate.py:757-766`（主循环 2g.0）与 `:597-609`（`_scan_prod_touched_and_rerun`）按行判定：任一新增行含 `<!-- AGATE_CARD_START -->` 即进入排除态、直到 `<!-- AGATE_CARD_END -->`；**不校验**该卡片是否真实、成对、或经 2p 哈希校验（2p 只校验 `*-dispatch-context-*.md`）。

**证据（仓外一次性 git 仓，真实 `pre-commit-gate.py`）**：
```
# /tmp/opencode/csoG2/scratch2：TAG0001/P5-test.md 内 **[PROD_TOUCHED]** 夹在伪造 CARD 块中；
#                          另 OUTSIDE.md（任务目录外）写 **[PROD_TOUCHED]**
$ AGATE_ROOT=<repo>/agate python3 agate/scripts/pre-commit-gate.py   → rc=0（未拦）
# 对照 /tmp/opencode/csoG2/scratch3：同一标记、不夹 CARD 块
$ ... pre-commit-gate.py   → rc=1（GATE: [PROD_TOUCHED] 检测到生产环境接触 …）
```
同证据亦显示：写在**任务目录外**（`OUTSIDE.md`）的标记不被扫描——后者是设计 §3.1 第 2 点「扫描面 = 任务目录内」的**已声明边界**，仅作记录；前者（伪造 CARD）不是声明过的边界，属实现弱点。**建议**：仅对**已 hash 校验的** dispatch-context 文件做 CARD 排除，或要求 START/END 成对（未闭合的 START 视为普通行参与扫描）。

### F-4（LOW）— 单一来源的残留与降级口径

- `pre-commit-gate.py:774-778` 仍保留字面 `re.match(r"^\s*-?\s*\[PROD_TOUCHED\]\s*$", ln)`（dash_only 口径）。经读码，该分支在非 PAUSED 下**不可达**（同形态已在 `:767` 命中 `exit(1)`），实为死代码，为 `test_marker_single_source.py` 的 mk_7b/mk_8 从源码文本抽取而保留（DESIGN_GAP-5）。
- `:246-249` 的降级字面 `re.compile(r"^\s*-?\s*\[PROD_TOUCHED\]")` 是 **dash_only 口径**，比单源 `default` **窄**：若 `agate_markers.py` 缺失（安装破损），粗体/引用块形态（BDD-54）将被**静默放行**——注释称「fail-safe（不静默放行）」，实测口径实为 fail-open 于 BDD-54 形态。**建议**：降级字面改用与 `default` 等价的 `^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?\[PROD_TOUCHED\]`。
- `agate_markers.pattern("PROD_TOUCHED")` 带 `exclude.backtick` 负向断言，行首反引号包裹的 `[PROD_TOUCHED]` 不命中（regex 实测 `False`），而设计 §3.1 第 2 点称 T4 扫描「不额外排除行内代码」。属 LOW 边界（且与旧门一致，非回归）。

### F-5（LOW / 观察）— 降级副本与等级口径

- `agate-frontmatter-check.py:167-215` 保留 `_local_iter_errors`/`_local_max_depth`/`_local_type_ok` 递归副本，仅当 `agate_schema is not None` 为假时启用。其覆盖 = 本文件 SCHEMAS 转换出的 JSON Schema 子集（`type`/`enum`/`required` + 深度），与单源语义一致 ⇒ **不构成绕过面**（与对齐复评 R4 结论一致）。守护 `test_tag0050_fitness.py` 的机械判据 + 白名单已锁定该事实。
- `check-frontmatter.py::_declaration_files()` 用 `current_level`（全局最大等级），而 `pre-commit-gate.py::_declaration_files(task_dir)` 用 `task_level`（任务等级）；当前仅 level 1 故恒等，level≥2 时会对在途任务分叉（对齐复评已记 LOW，沿用）。

### F-6（LOW / 非安全观察）

- `agate-config.py:220-222` 的 `_write_config` 用 `open(..., "w")` **非原子写**（设计 §3.4 要求原子写；`agate-md-field-set.py` 已用 `tempfile.mkstemp + os.replace`）。
- `agate-config.py:339` 用 `project_root = os.getcwd()`，设计 §3.4 要求 `agate_common.project_root()`（git toplevel 优先）。二者均非安全项，但属设计与实现的口径分歧，供主 Agent 决定是否本批修。
- BDD-52 修复命令行尾附中文注（`set prod_touched false（若未触达生产）`），整行照抄会作为 value 传入非 `true/false` 字符串 → 不可执行；与对齐复评「新问题②」一致，LOW。

## 五、已独立验证的安全面（通过项）

1. **BDD-52 强制点确在提交路径**（重点核验项 1 的 BDD-52 子项）：仓外一次性 git 仓 + 真 `pre-commit` hook（指向工作树 `pre-commit-gate.py`）+ 非 legacy 任务（账本 `task_created` level=1）缺 `prod_touched` → `git commit` rc=1，输出「缺 prod_touched 字段…修复命令…」（见「六」）。调用点在 `main()` 2g.3（`pre-commit-gate.py:781`）与 `_scan_prod_touched_and_rerun`（`:592`），非仅 `check-frontmatter.py` 直调。
2. **T4 优先于字段**：2g.0 先于 2g.3；BDD-54/55 用例驱动真实 `pre-commit-gate.py` 并断言中止与专门指引。
3. **单源成立**：运行期安全门取值自 `agate_markers.pattern("PROD_TOUCHED")`；regex 实测 `- / ** / > / * / +` 形态与 `[PROD_TOUCHED]: 无` 全部命中（fail-safe 成立）。
4. **legacy 不追溯**：`requirement_active`/`task_level` 对 legacy 返回 `None` ⇒ prod_touched 必填/中止、F10 缺 frontmatter 均不作用于 legacy（`check-frontmatter.py:100` 的 `_task_is_non_legacy` 二次门控）。
5. **无新增注入/路径穿越面**：`agate-config set/unset` 仅就地更新已存在文件（缺失不创建）、`yaml.safe_dump` 写出；`agate-md-field-set` 原子写。

## 六、验证留痕

- **仓外副本根**：`/tmp/opencode/csoG2/`（裸文件副本 `P6-acceptance.md`/`task/`、一次性 git 仓 `scratch2/`、`scratch3/`、`hook52/`）。
- **关键命令**：
  ```
  # F-1
  FILE=/tmp/opencode/csoG2/P6-acceptance.md python3 agate/scripts/agate-md-field-get.py pass  → 999
  python3 agate/scripts/agate_schema.py --derive "count(results, verdict == FAIL)" '{...FAIL...}'  → 1
  AGATE_ROOT=<repo>/agate python3 agate/scripts/check-gate.py P6 <forge task>  → "FAIL=0，P6_TOTAL=1"
  grep -rn "agate_schema.derive\|\.derive(" agate/scripts/ --include=*.py  → 无命中
  # F-3
  (cd /tmp/opencode/csoG2/scratch2 && AGATE_ROOT=<repo>/agate python3 agate/scripts/pre-commit-gate.py)  → rc=0
  (cd /tmp/opencode/csoG2/scratch3 && AGATE_ROOT=<repo>/agate python3 agate/scripts/pre-commit-gate.py)  → rc=1（对照）
  # 通过项：BDD-52 真 hook
  (cd /tmp/opencode/csoG2/hook52 && git commit …)  → rc=1「缺 prod_touched 字段…修复命令」
  ```
- **真实仓库只读核验**：评审前 `git status --porcelain | wc -l` = **33**；评审后 = **34**——增量恰为 `?? agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso-G2.md`（本评审产出文件自身），其余 33 行逐行未变（未写仓、未改被评审文件）。

## 七、返回给主 Agent

- **最高严重级别**：HIGH
- **各级问题数**：CRITICAL 0 / HIGH 1 / MEDIUM 2 / LOW 3
- **是否阻塞发布**：**是**（F-1：BDD-46 的 `derive` 现算读取未实现且验收用例无判别力）
- **status**：`rejected`
