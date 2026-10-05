---
phase: P4
task_id: TAG0042
type: review
parent: P4-implementation-batch1.md
status: approved
agent: review
review_round: 1
review_date: 2026-10-06
role: review (偏执 Staff Engineer，工程视角)
scope: batch1-phase-semantics（agate-next 去预写 + 卡片/文档反传 + 测试同步）
prod_isolation: "[PROD_NOT_TOUCHED]"
---

# P4 实现评审 — TAG0042 batch1-phase-semantics（round 1）

> 评审对象：`git diff` 未 commit 改动（HEAD `d3ba1c5`，P3 已落）。
> 评审依据：`P4-dispatch-context-review.md`、`P4-implementation-batch1.md`（含修正轮）、`P2-design.md` §1.1 M1/M2/M3、
> `P3-test-cases-batch1.md`、`P0-brief.md` known_risks、`docs/reviews/agate-alignment-review-2026-10-06-TAG0042.md`（round2 aligned）。
> 视角：**工程正确性/边界/回归/测试充分性**；语义对齐已由 protocol-alignment-review round2 判 aligned，本报告不重复、不替代其结论。

## 结论

**status: approved**。Pass 1（CRITICAL/BLOCKER）：**0 条**。Pass 2（INFORMATIONAL）：**5 条**（均非阻断，可 P5/P7/P8 或后续批次承接）。

改动面（`agate-next.py` 去预写/删孤儿函数、P2/P8 卡、UPGRADING v0.79.0、5 处权威文档反传、3 处既有断言同步）
经独立实跑核对：行为自洽、无残留调用、无回归、新用例覆盖 BDD-1/BDD-2 全部门槛。可进入 P5。

---

## Pass 1（CRITICAL）— 数据安全与正确性

**0 条。** 逐项排查（派发重点 1-4）结论如下：

### 1. `_advance()` 推进判定链自洽 — 通过

- **gate exit 三态消费**（`agate-next.py:367-402`）未被本批触及：`rc ∈ pass_set` → 普通 phase 查 `next`、P6 走 `_p6_pass` 条件式；`rc == 1` → 查 `retreat` 委托 / 提示重试；`else` → 落 exit2-resolution。结构不变、分支互斥、无遗漏。
- **P6 条件式裁决**（`_p6_pass` / `_p6_judge_advance`，`:229-297`）不变：`provenance` 通过的判据含 exit 2（DEBT0045），judge 启用时 `check-gate P6.5 exit 0` 才消费 `next`。`_advance` 的内部改动（不再写 phase/git add）不影响其调用契约（仍返回「已处理」语义）。
- **retreat 委托**（`_delegate_retreat`，`:300-325`）不变，仍以 `repo_root` 为 cwd 调 `agate-retreat-to.py`；retreat-to 自身写 phase 的路径未动。
- **孤儿函数删除无残留调用**：`grep -n "_write_state\|_git" agate/scripts/agate-next.py` → **0 命中**；全仓 `agate/**/*.py` 中 `_write_state`/`_git` 仅命中各文件**同名局部 helper**（`test_check_gate.py` 的 `_write_state_judge` 等）与注释，无对被删函数的 import/调用。`_advance` 调用点（`:279/:288/:386`）与保留形参兼容。
- `_advance` 不再做 git 操作，主 Agent 负责 `git add` 与 commit——与 `git-integration.md` 规则 2「一阶段一 commit、phase 随产出同 commit」一致。

### 2. 跳变合法性校验仍有效 — 通过

- `check-state-transition.py:251-269` 的触发面是**暂存区含 `.state.yaml`**（`git diff --cached --name-only`），**不读账本**。去预写后 phase 变更改由「下一阶段产出 commit 暂存 `.state.yaml`」触发，`pre-commit-gate.py:243-255`（2b 检测 `phase:` 变更 → 2c 调 `check-state-transition.py`）**同一机械路径不变** → 校验**未弱化**，仅触发时机后移一个 commit（与设计意图一致）。
- 实测回归：`test_check_state_transition.py` 全绿（见验证清单）。

### 3. `state_transition` 事件 `.phase=target` 而 `.state.yaml` 保持旧 phase — 不构成 CRITICAL

- **无硬消费者**：`grep` 全 `agate/scripts/*.py`，`state_transition` 事件只被**生产**（`agate-next.py:158`、`pre-commit-gate.py:415`），无脚本**解析**其字段（`check-events.py` 仅校哈希链/ts/已知类型，`check-judge-verdict.py` 不读该事件）→ 不破链、不触发审计、不改变 gate 判定。
- 残留歧义（事件语义/重复）不足以上升为 CRITICAL，记入 Pass 2 #1。

### 4. 测试充分性 — 通过

- 新增 `test_tag0042_batch1_phase_semantics.py`（6 例）覆盖 **BDD-1**（不预写 phase / 不 `git add`）与 **BDD-2**（`_advance` 无 `state["phase"]=target` / 卡片表述与行为一致 / UPGRADING 记载 / 全 `agate/scripts/*.py` 无预写实现）→ 派发重点所列 6 条新红灯测试到位。
- 既有同步**完整**：`test_tag0027_b1_agate_next_cli.py` 仅 4 处 `_read_state_phase` 断言（`:156` P5、`:317` P6、`:336` gate_p65 exit 1 停留 P6、`:371` P5）；3 处「推进后 phase」已同步为新语义，`:336` 非预写断言（保留正确）。**无遗留「推进后 phase 被写」断言**（跨 `agate/tests/` 复核，无其它文件在 agate-next 后断言 phase 前进）。

### 5. UPGRADING v0.79.0 版本号假设 — 属已登记 DESIGN_GAP，非缺陷

`P4-implementation-batch1.md`「[DESIGN_GAP]」节显式登记：P2 §1.1 M3 未指定版本节标题，实现自主采用 `### v0.79.0`，P8 发版时同步。**登记齐备**，P8 需据实版本号核对（不阻断本批）。

---

## Pass 2（INFORMATIONAL）— 代码健康 / 边界观察

### [INFORMATIONAL-1] `state_transition` 事件语义分裂 + 同转移双写
`agate-next.py:158-163` 在 gate 通过时追加 `state_transition`（from=old,to=target,phase=target），相位**未变**；而 `pre-commit-gate.py:413-420` 在**真实提交**相位变更时**也**追加一条同 from/to/phase 的事件（「双写语义」为既有设计）。差别：
- 批 1 前，agate-next 已把 phase 写盘，两条事件指向**同一次真实提交**；批 1 后，agate-next 的事件语义变为「**建议推进**」（可能对应未来某 commit，甚至在任务中止时成为**从未落地的幻影转移**）。
- 当前无消费者（Pass 1 §3 已证），**不阻断**。建议（非必须）：P7/P8 或观测器侧若要区分「已提交/仅建议」，可在事件内加 `committed: true|false` 或备注字段；或在 `CONTEXT.md` 账本事件表补一句语义说明。交由 P7/P8 判断，不在本批硬改。

### [INFORMATIONAL-2] 逐阶段卡片步「phase 保持 Pn」措辞在去预写后不再精确
批 1 后，进入 Pn 时 `.state.yaml` 的 phase 实际为 **P(n-1)**（agate-next 不再预写），须由主 Agent 在 Pn 产出 commit 时写入 Pn。`P2-design.md` / `P8-release.md` 已由本批补「agate-next 亦不预写」注；但 `P1/P3/P4/P5/P6/P7` 卡第 5 步仍写「此时 `.state.yaml` 的 phase 保持 Pn，不要提前写 P(n+1)」——「保持」隐含 phase 已为 Pn。
- **为何不判 CRITICAL**：手工规格已在两处明文档兜底——`git-integration.md:113`「更新 `.state.yaml` phase（先更新再 commit）」、`state-machine.md:523`「先更新 phase → 再 add → 再 commit」；且各卡第 6/N 步已有「phase 推进 P(n+1) 随 P(n+1) 产出 commit 一起」。流程闭合，属**措辞精确性**而非逻辑缺口。
- **与 round2 A3b 的差异**：对齐审查判「P1/P3/P4/P5/P6/P7 卡不需改」，工程侧同意其**非阻断**；此处仅补充建议——后续批次/文档整备时为这几张卡各补一句「进入本阶段后由本阶段产出 commit 将 phase 写为 Pn」，可消除主 Agent 漏写 phase 导致 pre-commit 按旧 phase 跑 gate 的静默风险（去预写把该写入从机械动作变为 Agent 手工动作，与本任务「规则不靠记忆」的立项动机存在张力）。不阻断本批。

### [INFORMATIONAL-3] `_advance` 的 `repo_root` 形参已成死参数
`agate-next.py:166` 保留 `repo_root` 但函数体不再使用（docstring `:173` 已如实注明「批 1 后不再做 git 操作」）。保留理由（避免级联改 `_p6_judge_advance`/`main` 签名）合理，ruff 不报。可在后续批次顺手移除，或保持现状；**不影响正确性**。

### [INFORMATIONAL-4] `P4-evidence/batch1-phase-semantics.log` 未含本批新增测试文件
日志 command 沿用 P2 §6.1b 声明的「既有 3 文件」filter（`test_agate_next_card` + `test_tag0027_b1_agate_next_cli` + `test_check_state_transition`，实测 93 passed / exit 0），**未包含**本批专属新用例 `test_tag0042_batch1_phase_semantics.py`。声明如实、命令实跑合规（MVWU 不阻断）；仅作过程提示：作为「本批绿灯」证据，若把新增 6 例一并纳入 filter（共 99 passed）会更完整。供 P8/后续批参考。

### [INFORMATIONAL-5] 一致性 WARNING 基线口径
实跑 `check-protocol-consistency.py --strict-errors-only` → **0 ERROR / 398 WARNING**，与 `P0-brief.md` 基线一致（对齐审查 round2 记 398；round1 因派发文件瞬时引用曾记 400，现已回落到冻结基线 398）。无新增 WARNING。信息性登记。

---

## 验证清单（本次评审独立实跑，证据先于结论）

| 验证项 | 命令 | 结果 |
|---|---|---|
| 批 1 相关 4 文件 | `pytest test_tag0042_batch1_phase_semantics test_tag0027_b1_agate_next_cli test_check_state_transition test_agate_next_card -q` | **99 passed**（12.77s） |
| UPGRADING 契约文档 | `pytest test_upgrading_contract_doc test_upgrading_lifecycle -q` | **27 passed** |
| ruff | `ruff check agate-next.py test_tag0027_b1_agate_next_cli.py test_tag0042_batch1_phase_semantics.py` | `All checks passed!` |
| 平台假设扫描（改动文件） | `check-platform-assumptions.py <3 文件>` | exit 0（0 命中） |
| 一致性 | `check-protocol-consistency.py --strict-errors-only` | exit 0 / **0 ERROR / 398 WARNING** |
| 用例数 | `bash agate/tests/scripts/count-tests.sh` | **2687**（未漂移） |
| 残留调用 | `grep "_write_state\|_git" agate-next.py` | 0 命中 |
| 残留旧行为文档 | `grep "写回 .state.yaml + git add\|更新 .state.yaml phase + git add" agate/*.md` | 0 命中（其余命中均为手工 fallback 规格，已显式限定） |

## [PROD_NOT_TOUCHED]

本评审**只读**改动集、任务数据与协议文档，并运行**只读/隔离**测试（pytest tmp_path 夹具、ruff、平台扫描、一致性、count-tests）。未修改任何被评审文件、未触碰主 checkout 状态、未访问 `~/.agate` 生产安装、未运行任何写生产环境/生产数据库/生产 API 的操作。实跑命令均无对仓库内已提交文件的写副作用（pytest 用例经 `tmp_path`/`git_repo` 夹具隔离；一致性/ruff/scan 为只读扫描）。

<!--
增量复评说明（供后续批次）：本文件为 round 1（batch1-phase-semantics）。若同一 reviewer 对后续批次增量复评，
按轮次追加（参照 TAG0034 P4-review.md 形态），保留本 round 1 全文。
-->
