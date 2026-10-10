---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A2 收尾 r2 复核——针对 r1 的 A1/A3/A4/A5/A8 发现逐条核实（RM-AG0087 注改写为硬检 + BDD-70 假绿灯修复 + dispatch-prompt 追加只读纪律 + CHANGELOG 口径同步）
files_changed: [CHANGELOG.md, agate-workspace/roadmap/roadmap.md, agate/assets/review-roles/protocol-alignment-review.md, agate/assets/templates/dispatch-prompt.md, agate/tests/unit/test_tag0050_proxy_judgment.py]
branch: hotfix/batch-a2-tidy（未提交，改动在工作区）
r1_report: docs/reviews/agate-alignment-review-2026-10-09-A2-TIDY.md
---

# 协议-脚本对齐审查（批 A2 收尾 / A2-TIDY r2 复核）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（r1 的 MISALIGNED 已修；1 处非阻断残留，见下） |
| A2 | 脚本→文档对齐 | ALIGNED（本批未改脚本；r1 相关项并入 A1） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（r1 项已尝试，但落点无效 + 重复） |
| A4 | 测试覆盖 | ALIGNED（r1 的 NEEDS_HUMAN_REVIEW 已修：BDD-70 判别力实测成立） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（空清单，见下） |
| A5 | 下游影响 + 文档传播 | NEEDS_HUMAN_REVIEW（r1 两条 minor 未采纳，见下） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（r1 的 2 条不准/误导已修；本批数字声称全部复现） |

**是否可 commit**：**基本可以——但建议先修 A3 的落点**。r1 的主阻断（A1 机制归属 + A4 锚测试未满足）已**真正修复并经独立实测确认**（见下）。唯一实质性问题是 r1 的 A3/A5 传播项：`dispatch-prompt.md` 的追加**落在注入围栏之外**（实测**不会**进入评审 subagent 的 prompt），既**未达「惠及全部评审角色」的目的**，又与该文件既有只读纪律块**重复**。修法很轻（把该规则移入 `### Review 角色特别指令` 围栏内，或并入既有 RM-AG0081 只读块）。若人工确认「该 blockquote 仅作维护者文档、不追求注入」，则 A3 降为 NEEDS_HUMAN_REVIEW，可直接 commit。其余为 minor。

---

## r1 发现逐条核实

### r1-A1「RM-AG0087 理由写错机制 + 锚测试未满足」→ **已修（核实通过）**

| 子项 | 证据 | 结论 |
|---|---|---|
| ① RM-AG0087 注改写为硬检 | `roadmap.md:87` 现写「机械校验**已存在**且是**硬检**——`check-pruning.py` 的「非 legacy 恒检」…不一致 ⇒ ERROR/exit 1（代码注释/`scripts/README.md`/BDD-70 三处一致归属本条）」 | ✓ |
| ① 显式自我更正 | 同注：「⚠️ **本轮自我更正**：初稿曾把实现说成 `_reconcile_p1_fields` 的 WARNING 对账——**错**（该对账抓不到本条的原始缺陷「phases 漏写 P2」，实测 0 mismatches；硬检抓得到 rc=1）」 | ✓ |
| ① CHANGELOG 同步硬检口径 | `CHANGELOG.md:122-126`：「其机械校验是 `check-pruning.py` 的**硬检**「`phases ∪ pruned == phase_universe`（不一致 ⇒ ERROR/exit 1）」…」 | ✓ |
| ② BDD-70 假绿灯修复 | `test_tag0050_proxy_judgment.py:82-110`：改跑 `check-pruning.py`（原跑 `check-gate.py`）+ `phases` 删 **P8** + 断 `rc==1` + 断 `"阶段全集" in output and "P8" in output` | ✓ |
| ③ 行号 / 误导结论删除 | `roadmap.md:87` 与 `CHANGELOG.md` **不再**出现 `:240`；**不再**出现「warning-only 系设计选择」 | ✓ |

**三处归属一致性核实（任务点名）**：`RM-AG0087` 全仓命中（排除 frozen 的 tasks/reviews）——`check-pruning.py:248`（「TAG0050 批 F（RM-AG0087，设计 §7）…恒检」）、`scripts/README.md:78`（「非 legacy 任务（TAG0050 批 F，RM-AG0087）：…恒检 `set(phases) ∪ set(pruned.phase) == 快照 phase_universe`…0=通过, 1=不一致, 2=无 P1」）、`test_tag0050_proxy_judgment.py`（BDD-70）、`level-1.yaml:58`（设计 §7 契约）、`design-tag0050…:590`（设计 §7）、`roadmap.md:87`、`CHANGELOG.md`——**全部指向硬检**；**无任何一处**再把 RM-AG0087 说成 WARNING 对账。`grep -rn "warning-only\|WARNING 对账"` 仅剩 `CHANGELOG.md:115`（属 RM-AG0113 条目，描述对账层本身）与 `CHANGELOG.md:126`（描述 DEBT0031 的 substance）。✓

**非阻断残留（1 处，供人工判断）**：`roadmap.md:87` 的**标题**仍写「…（DEBT0031）」（即 RM-AG0087 ⇔ DEBT0031 同一条），而新注/`CHANGELOG.md:126` 现称「对账是本条**之外**的叠加层，**两者不同机制**」（RM=硬检 / DEBT0031=对账）。且 DEBT0031 的 evidence 是「P1 phases 漏写 P2」（`tech-debt.md:1238-1239`），实测**只有硬检抓得到**（对账 0 mismatches）——故「DEBT0031 的 substance = 对账」这一定性（承接自已合并的 DEBT0031 关单，非本批引入）本身也偏软。**不影响本批关单成立**（RM-AG0087 的硬检确在），但建议在注中一句话点明「标题的（DEBT0031）为历史交叉引用，机制以本注为准」，避免读者困惑。

### r1-A3/A5「只读纪律未传播」→ **已尝试，但落点无效（未达目的）**

**已做**：`dispatch-prompt.md:315` 追加了一段 blockquote，自标「**评审角色的只读纪律（单源）**」（写类工具 + `cp -r /tmp/opencode` + 47 文件实证）。

**实测（独立验证，`/tmp/opencode` 副本）**：用真实渲染器 `agate-render-dispatch-prompt.py P4 protocol-alignment-review <task>` 渲染评审 prompt，产物：
- 含既有 RM-AG0081 只读块（`grep -c RM-AG0081` → 2）；
- **不含**新增写类纪律（`grep -c 写类` → **0**）。

**原因**（`agate-render-dispatch-prompt.py:159-169`）：渲染只取 ① `## 阶段特定提示` **之前**的首个代码块 + ② `### Review 角色特别指令` 节 + ③ 阶段追加节。新增 blockquote 位于**文件末尾**、`## 返回格式（修改类任务）`（`:311`）之下，**不在任何被提取的围栏内** ⇒ **不进评审 prompt**。

**差异**：
1. **未达目的**：r1 A3 的诉求是「惠及**全部**评审角色」；本批的追加**不注入**，故 `requirements-review`/`judge`/`design-review` 等角色**仍收不到**该纪律（只有 `protocol-alignment-review.md` 自己那份角色文件里的副本生效）。这**重复**了 `SG.9d` 记录的失败模式（「存在 ≠ 生效」——初版只读纪律曾写成 `### 小节`、掉到围栏外而不生效）。
2. **重复**：`dispatch-prompt.md` 内现**两处**只读纪律——围栏内 `:115-129`（RM-AG0081，会被注入）+ 末尾 `:315`（新，不被注入）。「单源」的自我标注与实际（双处、且真正生效的是围栏内那处）不符。

**建议（轻量）**：把写类工具规则**移入 `### Review 角色特别指令` 的代码围栏内**（追加到既有 RM-AG0081 只读块的禁止清单/副本条目里，或紧随其后加一条 bullet）——这样既生效、又不重复，也无需各评审角色文件各自引用。若确拟只作维护者文档，则应删去「（单源）」表述，避免误导。

### r1-A4「是否该补真红灯」→ **已补（核实通过）**

**独立判别力实测**（任务点名，不采信原结论）：
- 造 `init_task` 夹具 + 把 `phases` 由 `[P1..P8]` 改为 `[P1..P7]`（删 P8）。
- **真实 `check-pruning.py`（硬检 ON）**：`rc=1`，stderr 含 `phases ∪ pruned.phase != 阶段全集：缺=['P8'], 多=[]`（含「阶段全集」+「P8」）⇒ 用例**通过**。
- **变异副本**（`cp -r agate/{scripts,rules}` 到 `/tmp/opencode/agatecopy`，把 `_phase_universe` 改为恒 `return set()` = **抽掉硬检**）：`rc=1`（仍由「裁剪 P8 需 internal_only」+「跳过风险」产生）但 stderr **无「阶段全集」** ⇒ 用例的 `assert "阶段全集" in r.output` **失败 = 转红**。

**「阶段全集 + P8」是否只有硬检产生（任务点名，对照各错误分支）**：`grep -n "errors.append" check-pruning.py` 共 14 处；含「**阶段全集**」的**只有** `:279`（闭合硬检消息 `phases ∪ pruned.phase != 阶段全集：…`）。「P8」另见于 `:318/:320`（裁剪 P8 的 `internal_only` 检查），但那条**不含**「阶段全集」⇒ **「阶段全集」∧「P8」的组合只有硬检产生** ✓（用例的 `rc==1` 断言本身**不**具判别力——变异副本仍 rc=1；真正的判别子是「阶段全集」）。

**一处措辞提醒（非阻断）**：测试 docstring 称「靠『阶段全集 + P8』这条**只有硬检才会产生**的消息锁定判据」——严格说「P8」单独并非硬检独有（`:318/:320` 也有），**只有「阶段全集」是硬检独有**；组合断言成立，故结论不受影响，但措辞可更精确。

### r1-A8「行号不准 / 误导结论」→ **已修**

- `:240` 引用：`roadmap.md:87`、`CHANGELOG.md` **均已删除** ✓
- 「级别 warning-only 系设计选择」：**已删除** ✓（改称硬检 + 明确 DEBT0031 的 substance 是**另一机制**）

---

## 逐项审查

### A1: 文档→脚本对齐 —— ALIGNED

r1 的 MISALIGNED（机制归属 + warning-only 误导）**已修**，且经独立实测确认注中每一条事实陈述均成立（硬检存在、默认在 gate 路径、exit 1；对账抓不到「漏写 P2」而硬检抓得到）。非阻断残留见「r1-A1 核实」末段（标题 `（DEBT0031）` 与「两者不同机制」的轻度张力）。

### A2: 脚本→文档对齐 —— ALIGNED

本批**未改动任何脚本**（`check-pruning.py` 等原样）。脚本→文档方向即 A1 所述，已一致。

### A3: 一致性连锁 + 反向传播 —— MISALIGNED

见「r1-A3/A5 核实」：`dispatch-prompt.md:315` 的追加**不在注入围栏内**（实测渲染产物无该文），未达「惠及全部评审角色」，且与 `:115-129` 重复。**建议移入围栏内**（或明确降级为文档备注并删「单源」）。

### A4: 测试覆盖 —— ALIGNED

r1 的 NEEDS_HUMAN_REVIEW（锚「先加失败测试确认红 + 新测试覆盖」未被真正满足）**已修**：`test_bdd_70_phase_set_not_closed_errors` 现**直接跑 `check-pruning.py`** + 断言闭合硬检专属消息；判别力经独立变异实测成立（见上）。targeted 实跑：`1 passed`。
- ⚠️ 定性提醒（非阻断）：该用例现为**回归测试**（硬检由 TAG0050 批 F 早于本批落地），非字面意义的「先红」——但用于**关闭**一条已由前序任务交付的 RM 时，回归锁定即恰当证据。

### A4b: 闭合后既有测试转红 + 夹具更新清单 —— ALIGNED

**空清单（显式写出）**：本批 5 文件（`CHANGELOG.md` / `roadmap.md` / `protocol-alignment-review.md` / `dispatch-prompt.md` / `test_tag0050_proxy_judgment.py`）中**仅一个测试文件被改动**（BDD-70）。**全量 pytest 实跑**：

```
1 failed, 2909 passed, 2 skipped, 1 rerun in 133.97s (0:02:13)
```

- **无其它既有用例因本批转红**；**无需更新夹具**（BDD-70 仍用 `init_task`，未改夹具）。
- 唯一 failed = `test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，**环境性**（本机 opencode 子命令为 `debug agents`，测试调 `debug agent`），该文件**未被本批改动**——**与 r1 同一环境性失败**。⚠️ 该 1 条 failed **不可称「全绿」**。
- 相关守护未受影响：`test_protocol_alignment_review.py::test_sg_9a/b/c/d`、`test_sg_2/sg_2b` 均绿（`dispatch-prompt.md` 末尾追加未进入 `SG.9a/SG.9d` 的正则切区）。

### A5: 下游影响 + 文档传播 —— NEEDS_HUMAN_REVIEW

- **CHANGELOG 已标注** ✓。⚠️ r1 指出的「条目落在 `### 修复` 节、内容为登记/治理，更贴合 `### 文档 / 登记`」——**未采纳**（条目仍在 `### 修复` 节末）。次要，供人工决定。
- **文档传播**：见 A3——已传播到 `dispatch-prompt.md`，但落点无效。
- **新规范节仍无机械守护**：r1 建议的「为「写类工具」节补一条守卫测试（对标 `SG.9b`）」**未采纳**——`test_protocol_alignment_review.py` 未新增相关用例。次要。
- **新节与顶部只读块主题重复**：`protocol-alignment-review.md:14-18`（RM-AG0081 只读纪律块）与 `:111-121`（新增写类纪律节）**同主题同标题词**，r1 建议合并/改名/交叉引用——**未采纳**。次要。
- 破坏性变更：无。

### A6: 锚点表覆盖 —— ALIGNED

本批未新增协议规则、未改脚本行为 ⇒ 无需更新 CHECK 9 锚点。`check-protocol-consistency.py` 实跑 **0 ERROR**；**改动文件未产生任何新 WARNING**（`--show-frozen-warnings` 中无源自 5 个改动文件的条目）。

### A7: 设计原则一致性 —— ALIGNED

登记/治理 + 文档/测试新增，无架构决策，无需新 ADR；与 ADR-014（判据单源）无冲突。

### A8: 声称-命令绑定 —— ALIGNED

| 声称（本批） | 命令 | 结论 |
|---|---|---|
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py`（+ `--strict-errors-only`） | **复现**：`仅有 432 个 WARNING，无 ERROR`；`--strict-errors-only` rc=0 ✓ |
| `2909 passed`（**非全绿**） | `python3 -m pytest agate/tests/ --reruns 1 -n auto -q` | **复现**：`1 failed, 2909 passed, 2 skipped, 1 rerun`。1 failed = 环境性 opencode 用例 ✓ |
| `roadmap 0 异常` | `python3 -c "…统计 split('\|') 列数≠9 的 \|RM- 行…"`（`_ROADMAP_EXPECTED_COLS=9`） | **复现**：`RM rows= 111 malformed= 0` ✓ |
| `ruff All passed` | `~/.venvs/agate-dev/bin/ruff check agate/`（ruff **0.16.4** = CI 口径） | **复现**：`All checks passed!` rc=0 ✓ |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | **复现**：rc=0 ✓ |
| 「BDD-70 已改为直接跑 check-pruning.py」 | `python3 -m pytest agate/tests/unit/test_tag0050_proxy_judgment.py::test_bdd_70_phase_set_not_closed_errors -q` | **复现**：`1 passed` ✓ |
| 「判别力已 scratch 实测：抽掉硬检 ⇒ 转红」 | 变异副本（`_phase_universe` 恒空）跑同一夹具 | **复现**：变异后无「阶段全集」⇒ 断言失败（转红）✓ |
| r1 的 `:240` 行号 / 「warning-only」 | `grep -n "warning-only\|:240" roadmap.md CHANGELOG.md` | **已删除**（本批）✓ |

**结论**：本批数字/结论类声称**全部可复现**；r1 的两条不准/误导已修。⚠️ `2909 passed` 伴随 **1 条环境性 failed**，本批与 r1 均未称「全绿」，一致。

---

## 重点结论（任务点名 5 项）

1. **4 项改正是否真修**：① **真修**（roadmap 注 + CHANGELOG + BDD-70 三处一致为硬检，`:240`/warning-only 已删）；② **已改但落点无效**（dispatch-prompt 追加不在注入围栏内，实测不生效 + 重复——见 A3）；③ **真修**（行号/误导结论删除）；④ **真补**（BDD-70 判别力独立实测成立）。
2. **BDD-70 判别力**：**独立复现成立**——真实硬检 rc=1 且含「阶段全集」；变异副本（抽掉硬检）rc=1 但**无「阶段全集」** ⇒ 用例转红。**「阶段全集 + P8」组合只有硬检产生**（「阶段全集」全仓仅 `check-pruning.py:279` 一处；「P8」虽另见 `:318/:320`，但那两条不含「阶段全集」）。⚠️ 措辞提醒：真正独有者是「阶段全集」，非「P8」。
3. **RM-AG0087 三处归属一致**：**一致**（code `:248` / README `:78` / BDD-70 均硬检；roadmap 注一致）；**全仓 grep 无别处**再把 RM-AG0087 说成 WARNING 对账。
4. **dispatch-prompt 追加位置/口径**：**不恰当**——追加在文件末尾 `## 返回格式（修改类任务）` 之下的 blockquote，**不在** `### Review 角色特别指令` 注入围栏内（实测渲染评审 prompt 不含该文）；与既有 `:115-129` 只读块**重复**；「（单源）」自标与实际不符。建议移入围栏内（惠及全部评审角色）或降级为文档备注。
5. **A4b + A8**：全量 pytest **`1 failed（环境性）、2909 passed、2 skipped`**（**非全绿**）；5 条声称 + BDD-70 单跑 + 判别力变异**全部复现**。

---

## 审查过程说明（只读纪律）

- 本审查**只读代码、只写本报告与留痕文件**，未改任何协议/脚本/测试，未 commit/push。
- **所有写类/实验操作均在 `/tmp/opencode` 副本上跑**：`bdd70probe`（BDD-70 夹具）、`agatecopy`（`cp -r agate/{scripts,rules}` 后变异 `_phase_universe` 抽掉硬检）、渲染器输出写入 `bdd70probe` 任务目录（非真实任务）。未对真实任务运行 `agate-inject-card.py` 等写工具。
- 跑测试/脚本前后 `git status --porcelain` 一致——收尾仅 5 个被审文件 + r1/r2 两份报告与两份留痕。
