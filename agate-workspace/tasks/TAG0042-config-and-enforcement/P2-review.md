---
phase: P2
task_id: TAG0042
parent: P2-design.md
trace_id: TAG0042-P2-20261005
status: approved
agent: plan-eng-review
---

# P2 工程评审（plan-eng-review）— TAG0042（第 2 轮复审）

> 评审对象：`P2-design.md`（修订后，candidate_count: 3，mode: serial，6 批）
> 评审角色：plan-eng-review（C8：backend→plan-eng-review + high→plan-eng-review，去重为单评审）
> 评审轮次：**第 2 轮复审**（首轮 rejected，阻塞 B1 + 非阻塞 N1-N4 + 测试缺口 T1-T6）
> 评审方式：只读评审 + 独立实测（探针副本均在仓外 `/tmp/opencode/`，用完即删）
> 协议版本：agate v0.78.3（`AGATE_ROOT=/home/kity/.agate/v0.78.3/agate`）；HEAD `cb52bef`

---

## 0. 复审范围与独立实测摘要

本轮复审聚焦：**① 实跑核验 B1 是否真解（batch1 tests_filter）；② 核验 N1-N4 是否已修**；
③ 不放松对上轮已通过部分的核验（登记面、gate_commands、候选方案、minimal_validation）。

| # | 实测项 | 方法 | 结果 |
|---|---|---|---|
| E1 | **B1 实跑：batch1 tests_filter 三文件存在且 exit 0** | `ls` + `python3 -m pytest <三文件> -q` | ✅ 三文件均存在；**93 passed，exit 0** |
| E2 | **B1 残留：旧错名是否仍作为「当下绿灯命令」出现** | grep `test_agate_next.py` / `test_state_transition.py` | ✅ 全篇仅在「旧设计误写为…」订正注里出现，无残留断言 |
| E3 | **B1 语义：batch2-6 是否显式标注「P3 产出后生效」** | 读 §6.1b 先行声明 + 分类列 | ✅ 明确分 `[既有·当下可跑]`（batch1/6）/ `[P3 产出后生效]`（batch2-5）两类 |
| E4 | **N1：`parallel_limit` 双值消除** | grep 全文 `parallel_limit` | ✅ frontmatter / §6 / §6.3 三处**统一为 `3`**（含订正注）；无 `6` 残留 |
| E5 | **N1：serial 模式 gate 不校验 batch 数** | 读 `check-gate.py::_gate_p2_dispatch_plan`（777-812 行） | ✅ `if mode in ("static-batch","parallel")` 才校验 `len(batches) ≤ limit`；`serial` 跳过——设计论证准确 |
| E6 | **N2：gate_p0 返回值口径** | 读 §4.1 伪代码 + grep `return 2` | ✅ 有伪代码级口径：`validate` 的 rc **只决定 WARNING**，`gate_p0` **恒 `return 2`**；含负向用例交 P3 |
| E7 | **N3：解释器口径统一** | grep `python3` / `AGATE_PYTHON` / `probe_python` | ✅ §5 顶注（320-326）+ §6.1b 顶注（411-415）两处同一口径；实测本机 `probe_python()` → `/usr/bin/python3` |
| E8 | **N4：锚点 keywords 定值** | 读 §1.4（115-129）+ §4.5 | ✅ 定值 `["obligations.yaml","M 类占比","无归宿"]` + 批 6 落地实测三判据；与 `check_script_alignment` 读法一致 |
| E9 | **登记面实测复现** | 仓外 `/tmp/opencode` 副本放探针 `check-obligations.py` 跑 consistency + SG.6 | ✅ 复现设计结论：CHECK9-coverage 仅该脚本 1 条 WARNING + SG.6 `['agate/scripts/check-obligations.py']` FAILED（同源）；4 个 `agate-*.py` 零触发 |
| E10 | **consistency 基线** | `check-protocol-consistency.py --strict-errors-only` | ✅ **0 ERROR / 398 WARNING，exit 0**（与 §8 声明逐字吻合） |
| E11 | **批次内嵌键深度（B1 同步声明）** | 读 `agate-frontmatter-check.py`（`MAX_DEPTH=3`）+ 实跑 `FILE=… P2-design.md` | ✅ batches[] 仅留 `id`+`complexity`（深度 3），实跑 **exit 0**——「tests_filter/output 不写 frontmatter」的声明准确 |
| E12 | **锚点表读法（keywords 字面匹配）** | 读 `check_script_alignment`（855-868 行） | ✅ `if kw not in text: rep.warn("CHECK9-align")`——N4 的「须字面出现」要求准确 |

**只读纪律声明**：E1/E9/E10/E11 均为只读或仓外副本操作。E9 探针建于
`/tmp/opencode/tag0042-probe-*`（复制 `agate/` 后加探针脚本），跑完 `rm -rf`。
真实仓库 `git status --porcelain` 核验：**无本次评审引入的新改动**
（`gate-events.jsonl` 的 M 态 mtime = 11:19，来自 P1 commit 的 `state_transition` 事件，
早于本评审活动时刻；本评审的 `check-gate.py P2` 运行在 review status 校验处 exit，未追加事件）。

---

## 架构问题（阻塞级）

**无。** 上轮唯一阻塞 **B1 已真正解除**（见 §1），实跑证据充分。

### §1. B1 解除核验（实跑）

上轮 B1：`tests_filter` 全部指向不存在的测试文件 → 批级绿灯契约不可执行（pytest exit 4）。

**本轮实跑复核**（E1）：

```
$ ls agate/tests/unit/ | grep -iE "next|state_transition"
test_agate_next_card.py
test_check_state_transition.py
test_tag0027_b1_agate_next_cli.py
test_tag0027_b3b_structure_s1s2_next_retreat.py

$ timeout 180s python3 -m pytest \
    agate/tests/unit/test_agate_next_card.py \
    agate/tests/unit/test_tag0027_b1_agate_next_cli.py \
    agate/tests/unit/test_check_state_transition.py -q
93 passed in 11.81s
EXIT_CODE=0
```

**判定**：§6.1b 中 batch1 的 `tests_filter` 指向的**三个既有真实文件均存在**，
**当下可跑，exit 0 / 93 passed**——tracer bullet 的「管道确实通」反馈恢复。

**B1 三条修复证据齐备**：
1. batch1 改用既有真实文件名（`test_agate_next_card.py` + `test_tag0027_b1_agate_next_cli.py` +
   `test_check_state_transition.py`）——**实跑 exit 0**（E1）；
2. §6.1b 增列「先行声明」：明确 `[既有·当下可跑]`（batch1/6）vs `[P3 产出后生效]`（batch2-5）
   两类，并指明 pytest 对未知路径返回 exit 4（usage error，非测试红）——**语义混淆根因已表述清楚**（E3）；
3. 旧错名仅存于「旧设计误写为…」订正注，无残留断言（E2）。

**结论**：**B1 解除**。

---

## 架构问题（非阻塞）

### N1-N4 修订核验（全部已修）

| # | 上轮问题 | 本轮核验 | 判 |
|---|---|---|---|
| N1 | `parallel_limit` frontmatter(6) vs §6 正文(3) vs §6.3 论证(6) 三处矛盾 | frontmatter/§6/§6.3 三处**统一为 `3`**；`mode` 统一为 `serial`（并附订正注说明原委）。实测 `_gate_p2_dispatch_plan`：serial 模式**不**校验 `len(batches) ≤ parallel_limit` ⇒ 6 批不触发拦截（E4/E5） | ✅ |
| N2 | gate_p0 吸收 `validate` 退出码口径未写明 | §4.1 补伪代码级口径：`validate` 的 rc **只决定是否打印 WARNING**，`gate_p0` **恒 `return 2`**；「未来改 exit 1」明示为独立后续变更；负向用例交 P3（E6） | ✅ |
| N3 | 解释器口径两处不一致（裸 `python` vs 探测） | §5 顶注 + §6.1b 顶注**统一口径**：所有解释器名为**声明**，执行按 `AGATE_PYTHON`/`probe_python()` 替换；实测本机探测 → `/usr/bin/python3`（E7） | ✅ |
| N4 | 锚点 keywords 未定 | §1.4/§4.5 定值 `["obligations.yaml","M 类占比","无归宿"]` + 批 6 落地实测三判据（脚本内字面存在 / CHECK9-align 无新 WARNING / SG.6 转绿）；与 `check_script_alignment` 的 `kw not in text` 读法一致（E8/E12） | ✅ |

> **是否提债**：本轮无新的「后续应重构 / 存在架构债」项，**不登记 DEBT 条目**
> （符合角色定义「不强制提债」）。上轮 N1-N4 均属设计内可直接修正项，本轮已全部闭合。

### 本轮新发现的非阻塞观察（不阻断）

- **O1（信息项，供 P4/P8 留意）**：`dispatch_plan.batches[]` 未在 frontmatter 写 `tests_filter` /
  `output`，改由正文 §6.1b 承接「批级绿灯契约」——这是**有意的双源分工**（深度限制所致），
  设计已在 §6.1b 落点说明与 §9 声明的「单源」措辞**存在轻微张力**：正文称「frontmatter
  `tests_filter` 同步为单源」（P2-progress 行 20），而设计正文又定其为「frontmatter 只登记编排单元 +
  正文承接契约」。**这不是缺陷**（正文是权威源、frontmatter 仅登记单元），但 P4 执行者可能困惑
  「以谁为准」。**建议 P4 派发指令显式重申**：批级 `tests_filter`/`output` **以 P2-design.md §6.1b
  正文为准**，frontmatter 的 `batches[]` 仅作编排单元登记。**非阻塞**（设计已两处说明，仅措辞可再统一）。
- **O2（前置风险，已在设计登记）**：批 6 前置输入（160 项逐条清单）**不在仓库**，§10 已声明
  「不影响批 1-5，届时若仍缺则批 6 前置不足而阻塞」。**非阻塞**，但主 Agent 编排时须
  **在批 6 派发前确认该表已入库**，否则批 6 会空转。

---

## 测试缺口

上轮 T1-T6 情况（本轮核验）：

| # | 上轮缺口 | 本轮状态 |
|---|---|---|
| T1 | 批级绿灯命令不可执行（B1 关联） | ✅ **已闭合**——batch1 三文件实跑 exit 0（E1）；batch2-5 显式标「P3 产出后生效」（E3） |
| T2 | BDD-8「文件缺失 → 行为与现状一致」负向用例未落具体断言 | ⏳ 设计已明确交 P3（§4.1 末段「负向用例交 P3」+ §12.2），**P3 输入到位**，非设计缺口 |
| T3 | N2 的 gate_p0 吸收 validate rc 缺用例 | ⏳ 同上，§4.1 明示交 P3（「存量项目无 agate.config.yaml → gate_p0 返回 2 且 stderr 含 WARNING」） |
| T4 | `cmd_run` 事件字段 schema 未定义 | ⚠️ **仍为设计侧细化项**——§4.2 只写「经 `append_event()` 追加」，未给字段清单。**非阻塞**（P3 设计测试时可定），但建议 §4.2 补 event/命令/退出码/时间戳 字段清单，供 `check-events.py` 校验 |
| T5 | BDD-20/R6 差分判据为人工判读 | ⏳ 设计已声明为约定；建议 P8 逐条列出「新增告警 → 解释」（非设计缺口） |
| T6 | 平台分支 Windows 真机不可得 | ⏳ 已声明环境约束（§8 platform）；P3 按平台分支断言 + 模拟覆盖（非设计缺口） |

**新测试策略评估**：设计 §6.2 三判据（Tracer Bullet / Vertical Slice / Fitness Functions）齐备，
且判据一（batch1 tracer bullet）**本轮已由 E1 实证当下可跑**——测试策略在执行层面成立。

---

## 锁定决策

本轮复审后确定下来的技术方向（供 P4/P5/P8 遵循）：

1. **B1 解除（实跑证据）**：batch1 `tests_filter` 指向既有真实测试，**93 passed / exit 0**；
   batch2-5 标注「P3 产出后生效」；batch6 SG.6 文件既存（当下红、批 6 转绿）。**批级绿灯契约可执行**。
2. **候选 A 采纳确认**：声明层 + 执行层分离、唯一读取函数收敛、逐批增量落地。三候选 + 权衡 +
   选择理由齐备，**多方案探索满足 v0.6 要求**（上轮已核，本轮无变化）。
3. **编排模式锁定 `mode: serial` + `parallel_limit: 3`**：6 批强依赖链，serial 下 gate 不校验
   `len(batches) ≤ parallel_limit`（实测 `_gate_p2_dispatch_plan`），6 批不触发拦截；实际并行度恒为 1。
   **P4 派发须按 §6.1 依赖列逐批派发，每批 gate 通过后派下一批**。
4. **批级测试契约的权威源锁定**：`tests_filter` / `output` 以 **P2-design.md §6.1b 正文为准**；
   frontmatter `batches[]` 仅登记 `id`+`complexity`（深度 3，实跑 frontmatter-check exit 0）。
5. **登记面结论确认**：`check-obligations.py` 是**唯一**命中门禁面的新脚本，进
   `SCRIPT_ALIGNMENT_ANCHORS`（锚点表）+ keywords 定值 `["obligations.yaml","M 类占比","无归宿"]`
   （批 6 落地实测 CHECK9-align 无新 WARNING + SG.6 转绿）；4 个 `agate-*.py` 不在门禁 glob 面
   （登记属约定）。**本轮仓外副本实测复现**（E9），结论可信。
6. **gate_commands 锁定**：§5 独立 key（P3/P5/P5_consistency/P5_structure/P5_ruff/P5_platform）
   遵守「`--strict` 反模式」一 key 一命令，无 `&&` 短路；`P5_e2e` 不声明（`ui_affected: false`）；
   架构适应度检查（判据三）落 `P5_platform`。**P2 固化后 P4-P6 不得改**。
7. **迁移兼容底线锁定**：声明文件缺失/非法 ⇒ `gate_p0` 行为与引入前一致 + WARNING，
   **`gate_p0` 恒 `return 2`**（N2 伪代码级口径）；截止版本写 `UPGRADING.md`。不可退让。
8. **账本唯一写路径锁定**：`cmd_run` 事件与 hook 暂存**必须走既有 `append_event`**；hook 用
   `git add` 而非直接写文件——防破 `prev_hash` 链（R5）。

---

## 结论

- **阻塞问题：0 个**（上轮 B1 经实跑核验**确已解除**：batch1 tests_filter 三文件存在 + 93 passed / exit 0）
- 非阻塞问题：N1-N4 **全部已修**；本轮新增 2 条观察（O1 双源分工措辞、O2 批 6 前置输入）——均非阻塞
- 测试缺口：T1 已闭合；T2/T3/T5/T6 转 P3 输入/已声明约束；T4（`cmd_run` 字段 schema）为设计侧细化项，非阻塞
- 锁定决策：8 条
- **判定：approved**

**批准的限定说明**：本批准以「B1 已实跑解除 + N1-N4 已修 + 无新增阻塞」为准；
T4 的 `cmd_run` 字段 schema 属 P3 可在测试设计中补齐的细化项，**不构成设计阻塞**
（符合角色定义「不可判定是否选最优」边界——设计已清晰到 implementer 可自主实现）。

> ⚠️ 本评审只审不写，不直接改 `P2-design.md`。status 由 draft → **approved**。
> P2 评审重试预算：本轮为 retry #1 后的复审（P2 MAX=3），**剩余预算充足**。
