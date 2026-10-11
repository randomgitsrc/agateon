---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: v0.82.0 版本发布 bump（README badge 0.81→0.82 / CHANGELOG 切分 / UPGRADING 新增 v0.82.0 章节）
files_changed: [README.md, README.zh-CN.md, CHANGELOG.md, agate/UPGRADING.md]
task_id: RELEASE-v0.82.0
reviewed_ref: origin/release/v0.82.0 (ccb1c20f)
---

# 协议-脚本对齐审查（v0.82.0 发布 bump）

> 评审对象：`git diff origin/main...origin/release/v0.82.0`（单提交 `ccb1c20f`）。
> ⚠️ 本地 `release/v0.82.0` 分支已被 reset 到 `origin/main`（见留痕），故以 `origin/release/v0.82.0` 为准。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | NEEDS_HUMAN_REVIEW（证据边界见下，交 CI） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（空清单，见下） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**总体**：`needs-revision`（MISALIGNED ×2：A3、A5；A4 待 CI 人工确认）。

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

新 `### v0.82.0` 章节（`agate/UPGRADING.md:319-350`）的行为声明逐条对脚本核对：

- 「任务终态 = READY / 不 bump 不 tag」→ `agate/state-machine.md` P8→READY 转移行（diff 已删 `git tag`/`bump-version`，READY 收尾检查删「git tag 已创建」）✓
- 「`delivery.method` 三值枚举 / `level-2.yaml`（`extends: 1`）/ `OBL-P8-*` 断言」→ `agate/rules/task-data/level-2.yaml`（`method_enum: [release-notes, tag-release, none]`）+ `LEVELS.yaml` 登记 sha256（实测 `741afaf7…2b34` 一致）+ `obligations.yaml::OBL-P8-04`（enforced_at = `check-gate.py::gate_p8`）+ `check-gate.py::gate_p8` 枚举校验分支（level≥2 非 legacy 才进，legacy 走子串）✓
- 「写工具可写面 = `GENERIC_HEADER_KEYS ∪ task_fields ∪ SCHEMAS[basename]['migrated_keys']`」→ `agate-md-field-set.py::_writable_keys` ∪ `_schema_legal_keys`（`SCHEMAS.migrated_keys` 单源派生）+ `JSON_FIELDS`✓
- 「`append` 同族对 `writer: system` 字段不可写」→ `agate-md-field-set.py::_key_capability == "script"`（契约 `writer: system` ∪ 证据字段表），append/upsert/remove 复用 `set` 同判据 ✓
- 「`release.preset` 消费点 + 未知值 fail-closed」→ `agate-release.py::_project_release_preset`（已知集单源于 `project-config.schema.json::release.preset.enum`；未知 → `ReleaseError` 非 0；未声明 → 默认不阻断）✓

无过度声称（除 A5 的承载口径表述，见下）。

### A2: 脚本→文档对齐 — ALIGNED

新增/变更的脚本行为（`agate-release.py gate`、`check-gate.py P8` 枚举、`agate-md-field-set.py` 守卫）在文档侧均有对应：`state-machine.md` P8 行与 READY 说明、`agate/scripts/README.md:149`（gate op 描述）、`agate/tests/README.md:97`、`UPGRADING.md`。语义一致（≤/< 、拦截/警告 口径未见漂移）。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**(a) 版本号传播面（已核实完整）**：`git grep -n '0\.81\.0'` 全仓命中，除本次已改的两份 README 外，其余为 roadmap 补登记行 / TAG0051 frozen 任务快照 / 评审报告 / `UPGRADING.md` 历史 `### v0.81.0` 节（**不应改**）。`site/`（仅博客正文历史版本 v0.64.0/v0.71.0，frozen）、`NOTICES.md`、`install.sh`、`pyproject.toml` 均无当前版本号；本仓无 `.agate-version`。⇒ 无其它文件需随 badge 改。

**(b) 反向传播缺口（缺陷）**：发布分支 `agate/UPGRADING.md` §3 **残留 `### 未发布 — TAG0051 …` 节（line 286）**，与本次新增的 `### v0.82.0 …` 节（line 319）并存：

- 标题「**未发布**」在 0.82.0 已发布后**失效**（该节内容 = 本版全部内容）。
- 内容**重复**：`delivery.method` 收紧 / P8 去 tag/version / `release.preset` 三块在「未发布」节与 `v0.82.0` 节各写一遍。
- **本仓口径要求发布时归并**：先例 `git show 9bfef64d`（v0.80.0 P8 提交）commit message「UPGRADING：4 个「未发布 — TAG0050 批 …」节归并为单 `### v0.80.0` 节」，diff 中 4 个 `-### 未发布` 行被删；`docs/reviews/agate-alignment-2026-10-09-TAG0050-P8-01.progress.md` 明确以「未发布—TAG0050 计数=0」为 P8 评审判据。本次「未发布」计数 = 1。
- 本次 UPGRADING diff **纯 `+`（无删除）**，属遗漏而非有意保留。

**差异**：发布后 UPGRADING 仍含未归并的「未发布」节。
**建议**：删除/并入 `### 未发布 — TAG0051 …` 节（保留内容已被 `### v0.82.0` 覆盖；如需保留细节，把其要点作为 v0.82.0 节下的加粗小节，参照 v0.80.0 归并写法）。

### A4: 测试覆盖 — NEEDS_HUMAN_REVIEW

> ⚠️ **证据边界**：按本次派发约束（「不要重跑全量 pytest」）**未跑全量 pytest**，故不附 passed/failed 实跑输出。此处只给**可静态判定**的部分，全量 pytest 交 CI（主 Agent 已报 `check-protocol-consistency.py` rc=0 / 0 ERROR，与本次逻辑核对一致）。

- CHECK 7（`check_version_badge`）：release 分支 badge=`0.82.0` == CHANGELOG 首个 `## \[X.Y.Z\]`=`0.82.0` ⇒ PASS（tag 缺失仅 WARNING）。
- CHECK 13（`check_upgrading_section`）：UPGRADING 含 `^### v0.82.0\b` ⇒ PASS。
- `test_consistency.py::test_con_6`（断言 `PASS CHECK 7`）：按上述逻辑成立，不转红。
- 建议人工在 CI 上确认 `pytest` 全绿后补 `[HUMAN_CONFIRMED: …]`。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED（空清单）

经静态核对：`git grep -n '0\.81\.0\|0\.82\.0' -- 'agate/tests/**'` → **0 命中**（无硬编码版本断言）；`test_repo_url_no_stale_rename.py` BDD-3 已断 `[0.64.0]` 段（非 Unreleased）；`test_agate_changelog_unreleased.py` / `test_check_changelog.py` 均用 fixtures，**不读真实 CHANGELOG**；`test_v060_p8_cached.py` 用 `_P8_UNRELEASED` 常量 fixture。⇒ **经静态核对无既有用例因本次 bump 转红，无需更新夹具**（全量 pytest 交 CI 复验）。

### A5: 下游影响 + 文档传播 — MISALIGNED

**(a) 未发布节未归并**（同 A3b）——使用者升级时读到「未发布 — TAG0051」会误以为该批尚未发布。

**(b) 承载口径表述偏精确性（minor）**：新章节称「该门由 `agate-release.py` 新增的 `gate` 子命令承载，CI 编排侧**只调用它**（不内联门逻辑）」。核对：`agate-release.py::_cmd_gate` 仅含 ①（`--task` 时）check-gate P8 ② consistency 0 ERROR ③ CI success；**「tag↔提交一致」是 `release.yml` 的独立步 `Verify tag points to matching commit`（其内联 sed+python 逻辑）**；**「roadmap RM done」仅当 `--task` 时生效**，而 `release.yml` 的 backstop **显式未传 `--task`**（见 workflow 注释 SEC-07）。⇒ 「只调用它（不内联门逻辑）」对 tag 校验并不成立。
> 注：`AGENTS.md:194` 与 `adr.md:692` 采用同一 composite「发布门」口径，故此为**表述收紧**建议，非新增错误——建议改为「发布门 = workflow 的 tag 指向校验步 + `agate-release.py gate` 共同构成」。
**建议**：措辞明确 tag 指向校验由 workflow 承担、RM 反查仅本地 `--task` 门生效。

其余下游：`bump_type: minor` 与「含面向新任务的准入行为变化」自洽（pre-1.0，minor 承载准入变化；章节已显式声明「不再标注无破坏性变更」）；CHANGELOG `[Unreleased]` 全部条目已在 `[0.82.0]` 内（切分精确，A8 已核），无面向使用者的行为变化漏写（RM-AG0074 ① 效率度量属新增、非破坏性，UPGRADING §3「已知破坏性变更」不列可辩护；DEBT0065/0066/0068 为无迁移成本内部修复）。

### A6: 锚点表覆盖 — ALIGNED

本次 bump 为 **docs-only**（README×2 / CHANGELOG / UPGRADING），**未新增/改名 `agate/scripts/` 文件**，CHECK 9 锚点表无需更新；亦无新增协议规则需入锚点表。

### A7: 设计原则一致性 — ALIGNED

尊重 ADR-014「判据单源」：`level-2.yaml` 以 LF 归一 sha256 冻结登记 `LEVELS.yaml`；`release.preset` 已知集运行时单源于 schema `enum`（不手抄）；写工具可写面第三来源单源于 `SCHEMAS.migrated_keys`。与 `agate/adr.md` 相关条目（发布门、判据单源）一致，无需补新 ADR。

### A8: 声称-命令绑定 — ALIGNED

| 声称 | 命令 | 结论 |
|------|------|------|
| `consistency` rc=0 / 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py --root .`（主 Agent 实测；本次读码核 CHECK 7/13 判据） | 一致 |
| badge `0.82.0` == tag 版本 | `git show origin/release/v0.82.0:README.md` 取 badge；`release.yml` sed 抽取 | 一致 |
| CHANGELOG `[0.82.0]` 版本节正文非空（4614 字符） | `git show origin/release/v0.82.0:CHANGELOG.md` 段比对（68 行非空） | 一致 |
| 全仓 `0.81.0` 无待改处 | `git grep -n '0\.81\.0'` | 一致 |
| 无未来版本号承诺（发布清单 3a） | `git show origin/release/v0.82.0:agate/UPGRADING.md | sed -n '319,350p' | grep -E 'vN/将/硬切/exit 1'` | 0 命中 |
| 「39 个 legacy 任务、差异 2 条、未匹配 0 条」 | `bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/…`（产出命令登记于 `TAG0051 P4-implementation.md:188`；allowlist D13） | 有命令 |
| `delivery.method ∈ {release-notes, tag-release, none}` | `cat agate/rules/task-data/level-2.yaml` | 一致 |

无据声称：0（未新增不可复核数字）。

## 需修复项汇总（供主 Agent）

1. **A3b/A5（MISALIGNED，必修）**：删除/归并 `agate/UPGRADING.md` §3 的 `### 未发布 — TAG0051 …` 节（本次 diff 仅新增 `### v0.82.0` 而未删该节）。
2. **A5（MISALIGNED，轻量）**：收紧「该门由 `agate-release.py gate` 承载 / CI 只调用它不内联」的表述——tag 指向校验实为 workflow 独立步、RM 反查仅 `--task` 本地门生效。
3. **A4（待人工）**：CI 上确认全量 pytest 绿后补 `[HUMAN_CONFIRMED: …]`。

---

# 增量复审（第 2 轮，2026-10-11）

> 对象：工作树中**未提交**的 `agate/UPGRADING.md`（主 Agent 对上轮 2 项 MISALIGNED 的处置）。
> ⚠️ 上修订的「A3b/A5 必修项」已知，本轮只验证**处置**与**是否引入新不一致**。

## 逐条验收（上轮 2 项）

**① A3（`### 未发布 — TAG0051` 未归并）— RESOLVED（无实质信息丢失）**

- 现状：`### 未发布` 标题**已删除**；章节序为 `### v0.82.0`(:286) → `### v0.81.0`(:343)，`grep '^### 未发布'` 仅剩**历史 v0.80.0 节内散文引用**（:410）与卸载说明（:824），非标题。
- 逐条比对（原文 = `git show origin/main:agate/UPGRADING.md` 的 `### 未发布 — TAG0051 …` 整节）：
  - blockquote「本批把交付边界…既有任务与存量数据不受影响」「⚠️ 破坏半径…`level-2.yaml`…当前契约等级由 1 抬升为 2…**这不是「无破坏性变更」**，而是面向新任务的准入行为变化」→ **逐字保留** ✓
  - bullet「`delivery.method` 取值域定死为有限枚举」→ 保留（仅「三值枚举」→「三值」，标题已含「定死为有限枚举」）✓
  - bullet「P8 去 tag/version（任务终态 = READY）」→ 保留（重排为「任务终态 = `READY`（P8 去 tag/version）」；末句「对外发布…机械发布门」移入下方新 bullet）✓
  - bullet「`release.preset` 成为发布门的真实消费点」→ 保留（三值①②③、`additionalProperties: false` ⚠️ 全在；略去「在输出」「（可审计）」「（错误信息含 preset 名）」等修饰，核心无丢失）✓
- **轻微弱化（非虚假，供知情）**：blockquote 尾句「——本次升级因此**不再标注「无破坏性变更」**。版本号与 CHANGELOG 条目在 P8 统一落。」被删——前句语义由标题「（**含面向新任务的准入行为变化**）」+ 保留句「**这不是「无破坏性变更」**」承载；后句「在 P8 统一落」**本就已过时**（P8 不再 bump），删除正确。另：上修订版曾有的 `**行为变化（面向新任务）**` 小标题与「并有 `OBL-P8-*` 机械断言」未再现于合并节——非虚假声称（OBL-P8-04 实存），属可选细节。

**② A5（「门」表述失真）— RESOLVED（三步描述属实）**

对照 `.github/workflows/release.yml` + `agate/scripts/agate-release.py::_cmd_gate` 核实新写三步：
- ①「tag↔提交一致自检（tag 名 == 该提交 README badge 版本，且该提交 CHANGELOG 版本节正文非空）」= workflow 步 `Verify tag points to matching commit`（BADGE==WANT + 版本节非空）✓
- ②「发布门 `agate-release.py gate`（fail-closed）校验目标提交 CI success 与 `check-protocol-consistency.py` 0 ERROR」= `_cmd_gate` ③/②（③ CI fail-closed、② consistency rc!=0 → 非 0）✓
- ③「构建资产并创建 Release」= 步 `Build assets` + `Publish` ✓
- ⚠️「roadmap 关联 RM `done` 的反查**只在本地门**（`gate --task <TASK>`）生效——CI 侧 backstop **不传 `--task`**，该项不参与」= `_cmd_gate` ①（`if args.task:` 才跑 check-gate P8）+ workflow 步 `Release gate` 命令 `gate --sha` **无 `--task`** + workflow 注释 SEC-07 ✓ **属实**。

## 本轮结论

| # | 审查项 | 结论 |
|---|--------|------|
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（上轮 MISALIGNED 已修复） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（上轮 MISALIGNED 已修复） |
| A4 | 测试覆盖 | NEEDS_HUMAN_REVIEW（未跑全量 pytest，交 CI） |
| A8 | 声称-命令绑定 | ALIGNED（新加 DEBT0070/0071 声称经 `tech-debt.md` + allowlist D13 核实属实） |

**⚠️ 新发现（工作树状态，阻断性）**：当前工作树相对 `origin/main` **仅 `agate/UPGRADING.md` 一处改动**；相对上轮已提交的发布提交 `ccb1c20f`，**README.md / README.zh-CN.md badge 被回退为 `v0.81.0`、CHANGELOG 的 `## [0.82.0] - 2026-10-11` 行被移除**（`git diff ccb1c20f -- README.md README.zh-CN.md CHANGELOG.md` 确证）。照此提交将产出「UPGRADING 宣布 v0.82.0、但 badge/CHANGELOG 仍 0.81.0」的**不完整发布**——`release.yml` 的 tag 指向校验会在打 `v0.82.0` tag 时失败。**提交前须把 README badge（×2）与 CHANGELOG `[0.82.0]` 切分补回**（本文件上轮已判 ALIGNED，内容可直接复用）。

（本轮 0 项 MISALIGNED；阻断项为工作树缺 3 个 bump 文件 ⇒ 总体仍为 `needs-revision`。）
