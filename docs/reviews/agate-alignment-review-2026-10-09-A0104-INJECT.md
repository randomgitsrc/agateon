---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A/RM-AG0104（DEBT0052+DEBT0057）——agate-inject-card.py 缺占位符不再早退（继续处理其余文件 + 末尾汇总 + 非零退出），pre-commit-gate.py 新增 2y 步校验暂存 dispatch-context 的 AGATE_CARD 占位符存在性
files_changed: [agate/scripts/agate-inject-card.py, agate/scripts/pre-commit-gate.py, agate/tests/unit/test_agate_inject_card.py, agate/tests/integration/test_pre_commit_hook.py, CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md]
---

# 协议-脚本对齐审查

**审查对象**：分支 `hotfix/batch-a-inject-card` 未提交工作区改动（`git diff`，HEAD=`47b49b50`）。
**权威源**：`agate/dispatch-protocol.md`、`agate/WORKFLOW.md`「Pre-commit 检查总览」、`agate/assets/templates/dispatch-context.md`、`agate/scripts/agate-card-inject.py`。
**只读声明**：本审查未修改任何协议/脚本/测试，未 commit/push；所有 scratch 复现均在一次性副本内「创建→操作→清理」，跑测试前后 `git status --porcelain` 一致（仅多出本报告与留痕文件）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | NEEDS_HUMAN_REVIEW |
| A2 | 脚本→文档对齐 | MISALIGNED |
| A3 | 一致性连锁 + 反向传播 | MISALIGNED |
| A4 | 测试覆盖 | MISALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（一条措辞需收紧，见 A8） |

**需修复项**：A2/A3（`WORKFLOW.md` 补 2y 行）、A4（单测无判别力）。
**需人工确认**：A1（2y 子串判定 vs 文档注释式占位符；ADR-014 判据单源）。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/dispatch-protocol.md:360-362`）：
> `<!-- AGATE_CARD_START -->` / `{由 agate-inject-card.py 注入，禁止手写}` / `<!-- AGATE_CARD_END -->`

**注入侧实现**（`agate/scripts/agate-card-inject.py:17-20`）——权威占位符判定：
> `pattern = r"(<!-- AGATE_CARD_START -->\n)(.*?)(<!-- AGATE_CARD_END -->)"` … `if not re.search(...): exit 1`

**新 2y 实现**（`agate/scripts/pre-commit-gate.py:1119-1121`）——子串判定：
> `if "AGATE_CARD_START" not in _txt or "AGATE_CARD_END" not in _txt:` → 阻断

**结论**：NEEDS_HUMAN_REVIEW。

**证据（scratch 复现，2026-10-09）**：构造一个仅**散文提及** `AGATE_CARD_START`/`AGATE_CARD_END`（非 `<!-- -->` 注释对）的 `P1-dispatch-context-analyst.md` 并暂存 →
- 新 pre-commit（2y）**放行**，commit `rc=0`（"1 file changed"）；
- 同一文件喂给 `agate-card-inject.py` → `AGATE_CARD 注入失败: … 未找到 AGATE_CARD_START/END 占位符`，`rc=1`。

即 2y 是「必要非充分」：它拦不住的漏写仍会被 inject 拒绝。与 RM-AG0085（关键词/子串判定被散文命中）**同族**。

**为什么是 NEEDS_HUMAN_REVIEW 而非 MISALIGNED**：本批把 2y 明确表述为「占位符**存在性**校验」（CHANGELOG「缺 `AGATE_CARD_START/END` 占位符 → 阻断」），按此字面语义子串判定即其设计意图；是否必须**收窄到 inject 的同一正则**（要求注释式占位符对）属设计取舍。另注意 **ADR-014（判据单一权威源）**：同一事实「占位符存在」现有两处独立判据（inject 的正则 / 2y 的子串），二者可分歧。

**建议**：2y 复用 `agate-card-inject.py` 的同一正则（或至少要求 `<!-- AGATE_CARD_START -->` 注释式），使「占位符存在」判据单源；若判定维持子串语义，请人工确认并在 2y 注释/CHANGELOG 注明「仅存在性、不保证可注入」。

> **缓解因素（不改变结论）**：即便 2y 漏放，注入链的**不再早退**（主项①）也保证失败在末尾被显式汇总，不再静默——DEBT0052 的「静默」已被主项闭合。

### A2: 脚本→文档对齐

**脚本新增行为**（`agate/scripts/pre-commit-gate.py:1110-1126`）：新增 2y 步，暂存 `P{n}-dispatch-context-*.md` 且缺占位符 → `sys.exit(1)` 阻断 commit。

**应有文档**（`agate/WORKFLOW.md:350-365`「Pre-commit 检查总览」表，自述为「**本表是「pre-commit 检查集」的唯一事实源**」）：
- 表中已登记紧邻的 **2z**（`WORKFLOW.md:363`）：`| 2z | check-debt.py | 暂存 tech-debt.md 时（与 .state.yaml 无关，循环外） | … exit 1 阻断 commit |`；
- **无 2y 行**；`git grep -n "2y" -- agate/` 仅命中 `pre-commit-gate.py:1110` 的代码注释；`WORKFLOW.md` 全文**零**处提及 `占位符` / `AGATE_CARD`（`grep` 实测空）。

**结论**：MISALIGNED。
**差异**：新增了一条阻断级 pre-commit 检查，但作为「唯一事实源」的检查总览表未同步，且同一相邻批次（2z）已建立「新内联步登记入表」的先例。
**建议**：在 `WORKFLOW.md` 检查总览表补一行 2y（触发条件=暂存 `{Pn}-dispatch-context-*.md`；循环外；行为=缺 `AGATE_CARD_START/END` 占位符 → exit 1 阻断 commit；RM-AG0104 / DEBT0057）。

### A3: 一致性连锁 + 反向传播

**A3a（已知衍生改动，已在 diff 内）**：脚本 ×2 + 单测 ×1 + 集成测 ×1 + CHANGELOG + DEBT0052/0057 + roadmap RM-AG0104 → 齐备，一致。

**A3b（主动推断的应被影响文件，逐一验证）**：

| 候选文件 | 是否需改 | 验证 |
|---|---|---|
| `agate/WORKFLOW.md`「Pre-commit 检查总览」 | **需改** | 无 2y 行（见 A2）→ **MISALIGNED** |
| `agate/dispatch-protocol.md` | 否 | 已记占位符要求（`:329`/`:360-362`/`:373`）与注入命令，规则未变 |
| `agate/assets/templates/dispatch-context.md` | 否 | 模板含 `<!-- AGATE_CARD_START -->`/`END`（`:52`/`:56`），文件名不匹配 `^P[0-9]-dispatch-context.*\.md$` ⇒ **不被 2y 误伤** |
| `agate/scripts/README.md` | 否（可选） | `:174` 描述 inject 为「注入…AGATE_CARD 占位符」，未描述逐文件 exit 语义；`:67`「按顺序调度 9 项检查」非逐项清单。非强制 |
| `agate/tests/README.md` | 否 | 无逐检查步清单 |
| CHECK 9 锚点表（`check-protocol-consistency.py`） | 否 | `:901` 显式豁免 `pre-commit-gate.py`（「调度编排脚本…不需要锚点」）；无新增 `check-*.py` |
| `agate/scripts/agate-inject-card.py` 调用方（主 Agent 流程 / 卡片 / 文档） | 否 | 见 A5——无调用方依赖「早退即中止」语义 |

**「别处是否也有『首个失败即退出』同类模式」**（任务要求）：
- 对 `agate/scripts/*.py` 做 AST 扫描（`for` 循环体内含 `sys.exit`），命中集中在 **gate 检查器**（`check-events.py` / `check-p6-evidence.py` / `check-p6-provenance.py` / `pre-commit-gate.py`），这些是**闸门**语义——首个违规即阻断正是期望行为，**不是**同类缺陷。
- 生产型脚本（`agate-dispatch.py` 渲染路径、`agate-extract-context.py --write`、`agate-inject-card.py`）中，前两者每次只处理**单个** dispatch-context，无「多文件首败即弃其余」面。
- **结论**：本批「生产端 fail-fast 静默丢其余文件」的同类模式，在 `agate/scripts/*.py` 内**未发现第二处**；**建议不另行登记**（如后续做「生产端循环健壮性」专项再扫）。

**结论**：MISALIGNED（因 `WORKFLOW.md` 未同步；反向传播其余项均验证为不需改）。

### A4: 测试覆盖

**全量实跑输出（2026-10-09，本机）**：
```
python3 -m pytest agate/tests/ --reruns 1 -n auto -q
→ 1 failed, 2903 passed, 2 skipped, 1 rerun in 95.91s
  FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
- 该失败为**环境性、与本批无关**：调用真实 `opencode` 二进制，报 `Unknown subcommand "agent" for "opencode debug"`（该 CLI 子命令已改名为 `agents`）；`test_setup_agate_dir.py` **不在本批 diff** 内，单跑复现（`1 failed in 0.27s`）。

**定向实跑**：
```
python3 -m pytest agate/tests/unit/test_agate_inject_card.py -n auto -q              → 12 passed
python3 -m pytest <RM-AG0088 ×2 + RM-AG0104 ×1 integration tests> -q                 → 3 passed
```

**结论**：MISALIGNED。

**差异（关键）**：新增单测 `test_rm_ag0104_first_missing_placeholder_does_not_skip_rest`（`test_agate_inject_card.py:310+`）**对旧实现也全绿 ⇒ 无判别力**。理由（scratch 逐条复现）：

| 断言 | 旧实现下的实际值 | 是否判别 |
|---|---|---|
| `result.returncode != 0` | 旧版首败 `exit 1` → 非零 | ✗ 两版都真 |
| `for b-good/c-good: _between_markers(txt).strip()` | `_ANALYST_DC` 块内本就是字面 `{占位}`（非空）→ 真 | ✗ 未注入也真 |
| `"注入失败" in result.output` | 旧版透传消息 `AGATE_CARD 注入失败: …` 即含「注入失败」 | ✗ 两版都真 |

scratch（旧版 `agate-inject-card.py`：`continue` 改回 `sys.exit(1)`）实测：`rc=1`，仅输出 `AGATE_CARD 注入失败: P1-dispatch-context-a-bad.md …`，b-good/c-good 未被注入（块内仍为 `{占位}`）——**上述三条断言仍全部成立**。故该用例无法在旧实现上转红，属「假绿灯」。

**对照——集成测有判别力**：`test_rm_ag0104_staged_dispatch_context_missing_placeholder_blocks` scratch（假协议树**删去 2y**）实测：暂存无占位符 dispatch-context 的 commit **`rc=0` 成功**、输出无占位符文本 ⇒ 用例断言 `rc != 0` + 含 `AGATE_CARD_START`/`占位符` **会在旧实现上转红** ⇒ 有效。（该用例 T001 无 `.state.yaml` ⇒ 账本规则不触发，2y 是唯一拦截者，实测确认。）

**覆盖缺口**：新用例只覆盖「1 坏 + 2 好」；**「全失败」（全部缺占位符 → 汇总 `N/N` + 非零退出）** 与 **「零文件回退单文件路径」** 无新用例（后者由既有 `test_icb_4`/`test_icb_7` 覆盖，前者未覆盖）。

**建议**：① 单测改为断言「b-good/c-good 块内容**等于** `agate-next-card.py P1` 输出（`_sha256_utf8` 比对）或**不含** `{占位}`」——使未注入时断言必然转红；② 断言汇总行用更强的独特串（如 `个 dispatch-context 注入失败` 或 `RM-AG0104`），避免被透传消息满足；③ 补「全失败」用例。

### A5: 下游影响 + 文档传播

**CHANGELOG**：已在 `[Unreleased]` 加条目（`CHANGELOG.md:62-68`），标注 ① 不早退 ② 2y。✓

**破坏性变更评估**：
- `agate-inject-card.py` 退出码契约**不变**（0=全成功 / 非零=有失败）；变化仅是「有失败时**其余文件已被注入**」而非「全不注入」。无调用方依赖「早退即中止」语义（`git grep` 调用方：`AGENTS.md`/`CONTEXT`/文档仅指向工具，主 Agent 流程为「跑命令→看退出码→修复重跑」，无「部分状态回滚」依赖）。
- 2y 仅对**暂存**文件生效（`_staged_name_only()` = `git diff --cached`）⇒ 对**已入库**历史 dispatch-context 无影响。实测：仓库 834 个 `P{n}-dispatch-context*.md`，833 含占位符，唯一缺失者 `agate-workspace/tasks/TAG0050-task-data-contract/P2-dispatch-context-sync-residuals.md` 已入库——**仅当未来被重新暂存**才会被 2y 拦截（符合预期）。
- `agate-dispatch.py` 渲染路径用模板 `dispatch-context.md`（含占位符）→ 产出文件必然含占位符，不受 2y 影响。

**文档传播**：`dispatch-protocol.md`（占位符规则）与模板无需改；`WORKFLOW.md` 需补 2y（见 A2/A3）。

**结论**：ALIGNED（无破坏性变更；CHANGELOG 已标注）。

### A6: 锚点表覆盖

`check-protocol-consistency.py:901` 明确将 `pre-commit-gate.py` 排除出 CHECK 9 锚点（「调度编排脚本，不承载单一 gate 判定逻辑，不需要锚点」）；本批**未新增/改名** `agate/scripts/check-*.py`（仅新增内联步）⇒ 无需更新锚点表。CHECK 9 实跑 **PASS**。

**结论**：ALIGNED。

### A7: 设计原则一致性

逐条对照相关 ADR：
- **ADR-004（安全网分层——hook 兜底）**：2y 把「占位符缺失」从「靠 inject 事后暴露」提升为 hook 层兜底，符合。
- **ADR-015（门禁只用于会导致后续错误决策的错误）**：缺占位符 → 卡片未注入 → subagent 缺卡片，属实质错误，可门禁。
- **ADR-002（gate 门槛机器可判定）**：2y 为机械判定，符合。
- **ADR-014（判据单一权威源）**：2y 的「占位符存在」判据与 inject 正则构成**两处判据**，潜在分歧——已在 A1 记为 NEEDS_HUMAN_REVIEW，未发现需新增 ADR 的架构决策。
- 未发现需要补充新 ADR 的决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|---|---|---|
| `12 passed`（单测文件） | `python3 -m pytest agate/tests/unit/test_agate_inject_card.py -n auto -q` | ✓ 12 passed |
| `3 passed`（RM-AG0088×2 + RM-AG0104 集成测） | `python3 -m pytest <3 用例> -q` | ✓ 3 passed |
| `2903 passed`（全量） | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | ✓ 2903 passed，**但同批 1 failed**（`test_bdd_43` 环境因 opencode CLI 改名，与本批无关） |
| `0 ERROR`（consistency） | `python3 agate/scripts/check-protocol-consistency.py` | ✓ rc=0，0 ERROR（424 frozen WARNING） |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✓ rc=0 |
| roadmap「全量 pytest/consistency 0 ERROR」（`roadmap.md:103`） | 同全量命令 | ⚠️ 措辞需收紧：「全量 pytest」**非全绿**（1 环境失败）。建议按批 B 先例改为「全量 pytest 2903 passed + consistency 0 ERROR」或注明 1 环境失败，避免被读成「全绿」 |
| CHANGELOG/roadmap「13 个丢失」 | 溯源 `agate-workspace/tasks/TAG0050-task-data-contract/retrospective.md:85` + `P8-dispatch-context-implementer-retrospective.md:26` | ✓ 有可追来源（历史实测，非本批可重放） |

**结论**：ALIGNED（全部数字类声称均可复核；仅 roadmap「全量 pytest/consistency 0 ERROR」措辞建议收紧）。

---

## 五项重点结论

1. **「不早退」语义正确** ✓：`continue`（`agate-inject-card.py:115`）位于 `try` 内、`finally`（`:116-118`）之前——`continue` 触发 `finally` 清理 `card_file` 后跳下一轮，**临时文件必被清理**，且跳过其后的 stdout 写（`:119`）。`failures` 计数（`len(failures)`/`len(dc_files)`）与清单（`os.path.basename`）准确；全失败时 `len==len` + 非零退出 + 汇总完整；零文件回退单文件路径（`:82-88`）**未变**（不存在的单文件仍在循环前 `exit 1`）。

2. **2y 步基本正确，但子串判定偏弱**：
   - 覆盖：`^P[0-9]-dispatch-context.*\.md$` 命中 `P1-dispatch-context-analyst.md` 与 `P1-dispatch-context-{role}-{sub}.md` ✓；
   - **不误伤**：模板/示例文件名无 `P{n}-` 前缀 ⇒ 不匹配；已入库历史文件不受影响（仅 `git diff --cached`）✓；
   - 循环外无条件运行 ✓（实测无 `.state.yaml` 的任务也能触发）；
   - **弱点**：`AGATE_CARD_START`/`END` **子串**判定会被**散文提及**满足（scratch 复现：2y 放行、inject `rc=1`）——RM-AG0085 同族 → A1 NEEDS_HUMAN_REVIEW。另：`P6.5-dispatch-context-judge.md` 因 `.` 不匹配而被 2y 跳过（与 `dispatch-protocol.md:404` 既有 2p glob 边界一致，属既有范围，非新缺陷）。

3. **未引入新问题（除上述文档/测试缺口）**：无调用方依赖旧「早退」语义；2y 仅对暂存文件生效，不影响历史入库数据；`agate-dispatch.py` 渲染路径产出必含占位符。**同类「生产端 fail-fast」在 `agate/scripts/*.py` 内未发现第二处**，无需另行登记。

4. **测试判别力**：集成测**有**判别力（scratch 删 2y → commit `rc=0` → 会转红）；**单测无判别力**（scratch 旧实现 → 三条断言仍全绿）→ **A4 MISALIGNED**，必须修（改断言为「块内容 == next-card 输出 / 不含 `{占位}`」+ 更强汇总串 + 补全失败用例）。

5. **A8 逐条可复现**：`12 passed` / `3 passed` / `2903 passed` / `0 ERROR` / `check-debt rc=0` 均实测吻合；唯「全量 pytest」非全绿（1 环境失败，与本批无关），roadmap 措辞建议收紧。

---

## 闭环建议（给主 Agent）

| 结论 | 动作 |
|---|---|
| A2/A3 MISALIGNED | 在 `agate/WORKFLOW.md` 检查总览表补 2y 行（唯一权威源 + 与 2z 对称） |
| A4 MISALIGNED | 重写单测断言使其在旧实现上转红（用 `_sha256_utf8` 比对 next-card 输出或断言不含 `{占位}`）+ 补「全失败」用例 |
| A1 NEEDS_HUMAN_REVIEW | 人工裁决：2y 是否收窄到 inject 的同一正则（判据单源，ADR-014）；确认后补 `[HUMAN_CONFIRMED: …]` |
| A8 措辞 | roadmap RM-AG0104 更新列「全量 pytest/consistency 0 ERROR」→ 注明 2903 passed / 1 环境失败 |

> 上述 NEEDS_HUMAN_REVIEW（A1）在人工确认前，按角色闭环规则**视同 MISALIGNED**，不得直接 commit。
