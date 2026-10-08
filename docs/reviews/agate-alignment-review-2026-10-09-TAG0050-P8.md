---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: TAG0050 P8 发布文档改动——版本 bump 至 v0.80.0、CHANGELOG/UPGRADING 归并、TAG0042 config 硬切「截止版本」承诺更正、roadmap 回写与新增 RM-AG0102
files_changed: [README.md, CHANGELOG.md, agate/UPGRADING.md, agate-workspace/roadmap/roadmap.md, agate-workspace/tasks/TAG0050-task-data-contract/.state.yaml, agate-workspace/tasks/TAG0050-task-data-contract/P8-release.md]
batch: P8
task_id: TAG0050
---

# 协议-脚本对齐审查（TAG0050 P8 发布文档）

> 审查对象 = **TAG0050 P8 的发布文档改动**（触发面 `README.md`、`agate/UPGRADING.md`）。
> 聚焦审查，不重开全量。变更集为**暂存区**（`git diff --cached`）；本角色**只读**，未编辑被评审文件。
> 验证命令在活 checkout 上只读运行；未做写仓操作。状态标记：`[PROD_NOT_TOUCHED]`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（1 条轻微残留：`check-gate.py:735` 运行时 WARNING 文案，见 A1 注） |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | NEEDS_HUMAN_REVIEW（反向传播命中 2 个未随动的测试 + 1 处残留文案） |
| A4 | 测试覆盖 | NEEDS_HUMAN_REVIEW（全量 pytest 已附；BDD-8/BDD-21 两断言改后语义空洞） |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED（逐条见 A8） |

**dispatch 5 范围裁定**：

| 范围 | 裁定 |
|---|---|
| 1. 版本号 / CHANGELOG 归并 | **ALIGNED** |
| 2. UPGRADING 归并结构 | **ALIGNED** |
| 3. 截止承诺更正（关键） | **ALIGNED**（消除了前向版本号承诺；无**新**未兑现承诺；与「迁移期行为不变」一致）——附 2 条残留（A3/A4 的 NEEDS_HUMAN_REVIEW） |
| 4. roadmap | **ALIGNED**（附 1 条 minor：`scheduled` 无关联任务） |
| 5. SELF-GATE 清单 | **ALIGNED**（0 ERROR / 除环境漂移 1 条外 0 failed） |

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/UPGRADING.md:479-484`，v0.79.0 节 批 2）：
> 「**迁移期行为与引入前一致**：没有 `agate.config.yaml` 的存量项目，`gate_p0` 仍返回通过码（**exit 2**），只输出显眼 WARNING……**硬切未排期**：声明文件缺失 / 非法改为 `exit 1`……**本协议不预告实施版本号**」

**脚本实现**（`agate/scripts/check-gate.py:720-740`）：
> `validate_rc` 只决定是否打印 WARNING；「无论 validate 返回 0 还是非 0，恒 `return 2`」（L721）→ L740 `return 2`。

**结论**：ALIGNED。行为面「迁移期不变（exit 2 + WARNING）」与文档声明**逐字一致**。

**⚠️ 残留（轻微，非阻断）**：运行时 WARNING 文案（`check-gate.py:735`）仍写
`"WARNING: agate.config.yaml 缺失或非法（迁移期不阻断；截止版本起将 exit 1）\n"`。
该文案**不含版本号**（不违反「不预告实施版本号」的字面要求），但「**截止版本起**」仍隐含一个确定的截止点，与 UPGRADING 新表述「**未排期**」有轻微语义张力。属反向传播未随动项（见 A3），建议在实现硬切或下次触碰该脚本时把文案改为「未排期（见 RM-AG0102）」措辞。

### A2: 脚本→文档对齐

本次**未改任何脚本逻辑**（diff 无 `agate/scripts/*`）。文档侧（UPGRADING/CHANGELOG）为归并 + 更正，与既有脚本行为一致。
**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**已知连锁（diff 内）**：README badge ↔ CHANGELOG 版本节 ↔ UPGRADING `### v0.80.0` 三者同步，CHECK 7 / CHECK 13 实测 PASS（见 A6）。

**反向传播（主动推断「应被影响但未列在 diff」的文件）**：

| 应被影响的文件 | 理由 | 实测 | 结论 |
|---|---|---|---|
| `agate/tests/unit/test_agate_config.py`（`test_bdd_8_upgrading_documents_cutoff_version`, L404-418） | 断言 `re.search(r"v?0\.\d+\.\d+\|截止版本", upgrading)`——「须写明该**截止版本号**」。改后 config 硬切不再有截止版本 | **未改**；仍通过（`v0.80.0` 等版本号在全文随处命中） | **NEEDS_HUMAN_REVIEW**（断言语义空洞） |
| `agate/tests/unit/test_gate_layer.py`（`test_bdd_21_upgrading_documents_preset_migration_and_cutoff`, L165-180） | 断言 `re.search(r"截止版本", text)`——「preset 迁移**须写明截止版本**」。改后 preset 硬切「未排期」 | **未改**；仍通过（命中的是 v0.80.0 节**引用旧承诺**的「截止版本 v0.80.0」及无关 judge 截止） | **NEEDS_HUMAN_REVIEW**（断言被无关命中满足，假绿） |
| `agate/scripts/check-gate.py:735` | 运行时 WARNING 文案「截止版本起将 exit 1」 | **未改** | 轻微残留（见 A1） |
| `CHANGELOG.md` `[0.79.0]` 节（L78-80） | 仍含旧承诺「迁移截止版本 v0.80.0……请在此之前用 `agate-config init`」 | **按设计不动**（历史节）；由 `[0.80.0]` `### 变更` 显式更正 | 可辩护（见「范围 3 裁定」） |

**结论**：NEEDS_HUMAN_REVIEW。
**差异描述**：本次把「config/preset 硬切截止版本」从协议中**移除**，但两条锁定该承诺的测试（TAG0042 BDD-8 / BDD-21）未随之调整——它们现在**靠无关文本命中而通过**，不再验证其声明的性质（"UPGRADING 写明截止版本号"）。
**建议修复方向**：二选一——① 把两测试改为断言**新语义**（存在「未排期」/`RM-AG0102`，且不再要求「截止版本号」）；或 ② 由主 Agent 明确裁决「TAG0042 历史 BDD 不回溯修改、其断言保留」。无论哪条，都需留痕。

### A4: 测试覆盖

**最近一次全量 pytest 实跑**（本 checkout，HEAD `4e7ea04c` + P8 暂存改动，`-n auto`）：

```
$ python3 -m pytest agate/tests/ -q --tb=no -n auto
1 failed, 2863 passed, 2 skipped in 75.88s
PYTEST_EXIT=1
```

**唯一 failed 为既有环境漂移，与本次改动无关**（实测复现）：
```
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
E   ERROR  Unknown subcommand "agent" for "opencode debug"
E     Did you mean this?  agents
```
→ 本机 OpenCode CLI 的子命令为 `debug agents`（复数），测试调 `debug agent`（单数）。本次 diff 不触及 `agate-setup` 路径，**非本次引入**。

**结论**：NEEDS_HUMAN_REVIEW。全量实跑输出已附（2863 passed / 1 env-failed），但**本次改动相关的两条 BDD-8/BDD-21 测试已语义空洞**（详见 A3），属「改动未被测试真实覆盖」的缺口。

### A5: 下游影响 + 文档传播

- **无破坏性变更**：UPGRADING v0.80.0 节标注「无破坏性变更」；CHANGELOG `[0.80.0]` 归并原 `[Unreleased]`（含 `baseline.reset` 一次性重设语义，保留「此后只增不减」）。
- **文档传播**：`CHANGELOG.md` 已标 ✓、`agate/UPGRADING.md` 已同步 ✓、`README.md` badge 已 bump ✓。
- **legacy 兼容承诺**：P8-release §4 记录 R6 双向差分在干净副本上 `差异 0 条`（脚本 `docs/design-notes/r6-differential.sh`），与「legacy 退出码/ERROR 集合不变」一致。
- **既有状态（非本次引入）**：`README.zh-CN.md:12` badge 仍 `v0.78.0`；CHECK 7 只读 `README.md`，不构成一致性缺口。

**结论**：ALIGNED。

### A6: 锚点表覆盖

`python3 agate/scripts/check-protocol-consistency.py`（本 checkout 自己的脚本）实测：
```
✅ PASS CHECK 7  version badge 与 CHANGELOG 已发布版本
✅ PASS CHECK 9  协议-脚本结构对齐
✅ PASS CHECK 13 CHANGELOG↔UPGRADING 章节对应
仅 412 个 WARNING（全冻结面），无 ERROR。  EXIT=0
```
CHECK 7 输出：`v0.80.0 尚无对应 git tag（发布进行中——先合 PR、推 tag 由 release workflow 校验 tag 指向）；本次 PASS`——与 P8 卡「先合 PR、后打 tag」时序一致。
本次为文档归并/更正，**未新增需进 CHECK 9 锚点表的协议规则关键词**。
**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-005（改动性质决定流程）**：本次为**声明性改动**（文档/版本号），但位于 `agate/` 协议本体（机制交叉面）→ 走 agate + SELF-GATE（本审查即其体现），与决策一致。
- **ADR-002（可判定性）**：「不预告实施版本号」是**沟通/流程约定**，非 gate 门槛，未引入不可判定判据。
- 未发现需要补记的新架构决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|---|---|---|
| README badge = `v0.80.0` | `grep -n 'badge/version' README.md` | 命中 `version-v0.80.0` ✓ |
| CHANGELOG 顶部 `[Unreleased]` 空 + `[0.80.0] - 2026-10-09` | `grep -nE '^## \[' CHANGELOG.md` | L11 `[Unreleased]`、L13 `[0.80.0]` ✓ |
| UPGRADING 有 `^### v0.80.0` 且无残留「未发布 — TAG0050」 | `grep -n '^### v0.80.0'`=L279；`grep -c '未发布 — TAG0050'`=**0** | ✓ |
| 4 批 CHANGELOG 条目 ↔ UPGRADING 4 加粗小节对齐 | `sed -n '279,460p' UPGRADING.md \| grep -E '^\*\*批'`=G1/G2/hotfix/DEF | ✓ |
| `TAG0050` 关键词存在 | `grep -c 'TAG0050' CHANGELOG.md`=5 | ✓ |
| roadmap `RM-AG0099`/`RM-AG0101` 状态恰为 `done` | 按 `_check_roadmap_done` 同款解析（`\|` 分列、列数=9、第 5 数据列） | `done`/`done` ✓ |
| roadmap 全 RM 行无字面 `\|`（列数=9） | 同上解析，统计列数≠9 的行 | 命中 0 行 ✓（RM-AG0098 由 11→9 一并修正） |
| 新增 `RM-AG0102` 状态 `scheduled` | 同上解析 | `scheduled`，关联任务 `—` ✓ |
| 全量 pytest「除既有环境漂移 1 条外 0 failed」 | `python3 -m pytest agate/tests/ -q --tb=no -n auto` | `1 failed, 2863 passed, 2 skipped`；failed = `test_bdd_43…`（OpenCode CLI 环境漂移）✓ |
| consistency 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | `仅有 412 个 WARNING，无 ERROR`，EXIT=0 ✓ |
| 用例数 2866（P8-release §4） | `bash agate/tests/scripts/count-tests.sh` | `总计：2866 个测试用例` ✓ |
| R6「legacy 任务 39 个，差异 0 条」（P8-release §4） | 干净副本上 `r6-differential.sh`（本审查未复跑；记录于 P8-release §4，活树自核验拦截已说明） | 未独立复跑，采信 P8-release 留痕 |

无「无法给出命令的声称」。

---

## 范围 3 专项独立裁定（截止承诺更正）

**处置回顾**：`agate/UPGRADING.md` **两处**（v0.79.0 节 批 2 L479-484、批 4 L500-505）把原「**截止版本：v0.80.0** 起改 `exit 1`」改为「**硬切未排期**（`RM-AG0102` 追踪），落地时在**其实际所在版本的 UPGRADING 节**公告——**不预告实施版本号**」；`CHANGELOG.md` `[0.79.0]` 历史节**不动**，更正写入 `[0.80.0]` 的 `### 变更` 节（L50-57）。

**裁定**：

1. **是否消除「给未排期能力预告未来版本号」？→ 是（就前向/操作性面而言）。**
   原承诺的两个操作性落点（UPGRADING 批 2 / 批 4，即升级者实际阅读的迁移指引）已改为「未排期」，且 `[0.80.0]` `### 变更` 显式声明「**协议不再预告实施版本号**」。grep 全仓 `agate/**`：不再有任何**面向未来**的「config/preset 硬切将在 vX.Y.Z 落地」版本号承诺（`check-gate.py:735` 文案无版本号，见 A1）。

2. **是否留下新的未兑现承诺？→ 未引入新的版本号承诺；但存在 1 处「旧承诺残留」需知晓。**
   - 更正文本本身只做**负向承诺**（不再预告）+ 条件性流程承诺（落地时在实际版本节公告）+ 承接项（`RM-AG0102`，roadmap 已登记）——均为可满足项，**非新的未兑现承诺**。
   - **残留**：`CHANGELOG.md` `[0.79.0]` 节（L78-80）仍写「**迁移截止版本 v0.80.0**……请在此之前用 `agate-config init`」。v0.80.0 已发布且不含该硬切 ⇒ 该句**现已过期**。它**不是本次新增**，且被 `[0.80.0]` 节显式更正、按 Keep a Changelog 惯例历史节不可改 ⇒ **可辩护**，但阅读 `[0.79.0]` 节的升级者仍会看到过期祈使句。建议（非阻断）：主 Agent 裁决是否在 `[0.79.0]` 节加一行「（**已更正**：见 `[0.80.0]` `### 变更`）」指针，或维持现状并留痕。

3. **是否与「迁移期行为不变」的既有事实一致？→ 是。**
   `check-gate.py:720-740` 实测 `gate_p0` 恒 `return 2`（+ 缺失声明时 WARNING），与文档「迁移期行为不变（无声明 → `gate_p0` 仍 `exit 2` + 显眼 WARNING）」逐字一致（A1）。

**范围 3 裁定**：**ALIGNED**——问题在前向面已消除、无新承诺；残留（旧历史节过期句 + 两测试语义空洞）已按 A3/A4 记为 NEEDS_HUMAN_REVIEW 交主 Agent 裁决。

---

## 范围 4 专项（roadmap）minor

`RM-AG0102` 状态 `scheduled`，但「关联任务」列 = `—`。roadmap 图例（L102-110）定义 `scheduled` = 「**已拆任务** → 建任务目录 + active-tasks.md 写入任务行」。实测全表：`scheduled` 行共 6 条，**唯 RM-AG0102 无关联任务**（其余 5 条均指向 TAG0038/0040）。按图例字面，无关联任务的欠账更接近 `backlog`。
**不影响本任务 gate**（关联任务列 = `—`，不触发 RM-AG0043）。dispatch 明确要求 `scheduled` ⇒ 记为 **minor 观察**，非 MISALIGNED。

---

## 闭环建议

- **可 commit 项**：A1/A2/A5/A6/A7/A8（ALIGNED）。
- **commit 前须裁决**：
  - A3 / A4（NEEDS_HUMAN_REVIEW）：`test_bdd_8_*` / `test_bdd_21_*` 两断言是否随「不预告版本号」一并改述（或裁决 TAG0042 历史 BDD 不回溯）。未附 `[HUMAN_CONFIRMED]` 前视同 MISALIGNED。
  - 范围 3 残留（`CHANGELOG [0.79.0]` 过期句、`check-gate.py:735` 文案）：建议裁决并留痕（可接受现状）。
  - 范围 4 minor（`RM-AG0102` = `scheduled` 无关联任务）：建议裁决（可维持）。
- 本审查未触碰生产环境：`[PROD_NOT_TOUCHED]`。
