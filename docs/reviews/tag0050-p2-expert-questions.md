# TAG0050 P2 评审问题单 — 供外部专家评估

> **用途**：TAG0050 的 P2（方案设计）经两位独立专家评审**双双 rejected**，含 **3 个 BLOCKER** 与 **1 处专家分歧**。本问题单把事实、证据、双方主张与待决问题列清楚，供外部专家独立判断。
> **生成**：2026-10-07，主 Agent（orchestrator）。
> **基线**：agateon 分支 `feat/TAG0050-task-data-contract`，HEAD `adb0b11`；`origin/main` = `720c97d3`（v0.79.0）；协议稳定版 agate v0.78.3。
> **配套文件**（同批发布）：`P2-design.md`（被评审对象）、`P2-review-eng.md`、`P2-review-cso.md`、`P2-review.md`（组长汇总）。

---

## 0. 一句话背景

**TAG0050 =「任务数据契约：结构化判定、可信写入与任务版本」** —— 把 agate 协议的判定依据从「正文正则 + 自报汇总 + 可改开关 + 作者自标的分类」改为「按**冻结契约快照**登记的结构化字段 + **机械核验**」。共 **10 批**（A0–A4/B/C/D/E/F），每批独立 PR/gate/评审。

P2 的定位：把一份**已 4 轮独立评审通过**的设计（`docs/design-notes/design-tag0050-task-data-contract.md`，r4 **APPROVE WITH CHANGES**）**形式化**为 `P2-design.md`（**不改技术决策**）。
评审：`plan-eng-review`（工程维度）与 `cso`（安全维度）各自独立评审 → **双双 rejected**；组长汇总 `P2-review.md` = **rejected**。

---

## 1. 事实基线（可复现）

- 任务产物：`agate-workspace/tasks/TAG0050-task-data-contract/`
  - `P0-brief.md`（立项）
  - `P1-requirements.md`（**77 条 BDD**，10 批；已由 requirements-review 判 approved）
  - `P2-design.md`（candidate_count: 3，ui_affected: false，10 批 static-batch，7 条 design_gap）
  - `P2-review-eng.md`（**rejected**：1 BLOCKER `B1` + 2 MAJOR `M1/M2`）
  - `P2-review-cso.md`（**rejected**：2 BLOCKER + 4 MEDIUM + 2 LOW）
  - `P2-review.md`（组长汇总：**rejected**）
- 设计依据：`docs/design-notes/design-tag0050-task-data-contract.md`（14 节 + 附录；§2 契约等级、§3 写入工具与契约单源、§4 生产接触、§5 证据绑定、§8 存量兼容、§10 分批与验收锚）。

---

## 2. 待评估问题

### Q1（专家分歧）G3 归属批：A1 还是 A3？

**事实**：`RM-AG0100` —— `agate/scripts/pre-commit-gate.py:428-429`（2h.1d）对 `gate-events.jsonl` 执行 `run_git(["add", …])`，但在**真实 `git commit`** 中该 add **不落入提交**（见 Q2 复现）。设计 §2.7（批 **A3**）要把 2h.1c（写 `state_transition`）与 2h.1d（`git add` 账本）**一起前移**到 2g 的 `continue` 之前，使事件「随本次提交入库」。

**双方主张**：

| 专家 | 裁决 | 理由 |
|---|---|---|
| plan-eng-review | **纳入 A3** | A3 本就编辑 `2h.1c`/`2h.1d` 这两行，是唯一自然落点；BDD-38「随本次提交入库」的锚也在此 |
| cso | **纳入 A1** | 账本信任链是 A1「账本完整性」域（与 §2.3 账本七规则同域）；A1 补锚 + 让 2h.1d 的 `git add` **失败可见** |

**待决**：G3 归 A1 / A3 / 排除单独登记？判据应是什么（编辑落点 vs 主题归属 vs 单一 owner 原则）？

---

### Q2 G3 根因是否成立？（主 Agent 探针 vs cso 反例）

**主 Agent 探针（真实仓库，跑两次结果一致）**：建探针任务目录（`.state.yaml` phase P0 + 空 `gate-events.jsonl`）→ `git add` → **真实 `git commit`**：

- **committed ledger = 0 行、worktree = 2 行**（hook 追加的 `gate_run` + `state_transition` 未入库）；`git status` 显示 `M`。
- **手动跑 `pre-commit-gate.py`**（不经 commit）：index 被正确更新（`git show :ledger` = 2 行、status `A`）。
- hook **无错误输出**（`run_git` 用 `capture_output=True` 吞 stderr，rc 未检查）。

**cso 的反例**：其**仓外 `mktemp -d` 副本**上做最小复现，称"三场景 committed 内容均含 hook 追加行" ⇒ 主张**根因假设未被复现**，须在**真实 hook 上重新实测根因**后再定 §2.7 措辞。

**待决**：
1. 症状在**真实仓库**是否成立（主 Agent 探针能否被外部复现）？
2. 根因是什么？（`git commit` 期间是否持有 `index.lock`？是否使用临时索引 `GIT_INDEX_FILE`？副本与真实仓库的差异在哪？）
3. 设计 §2.7 措辞应以什么为准？

---

### Q3 B1：`gate_commands.P5_r6_differential` 指向不存在的脚本

**事实**：`P2-design.md` 的 `gate_commands` 声明 `P5_r6_differential: "bash docs/design-notes/r6-differential.sh ."`，但该文件**不存在**（仓库仅有 `repro-tag0050.sh`；`r6-differential` 只出现在文档里），且**未被任何批次登记为交付物**。`gate_commands` 在 P2 固化后 **P4–P6 不可改** ⇒ 该 key 在 P5 必红、且无合法修复窗口。

**eng-review 裁决**：BLOCKER；二选一须在 P2 定稿 ——
- **（首选）批 A1 落地 `docs/design-notes/r6-differential.sh`** 并登记为交付物 + BDD 锚；
- **（次选）移除该命令**，R6 双向差分（设计 §8）转各批**过程性验收 checklist**。

**待决**：选哪条？R6 双向差分是否值得固化为可执行 gate，还是保持过程性验收？

---

### Q4 BLOCKER-1：生产接触安全门（F4）闭合机制自相矛盾

**事实**：`agate/scripts/pre-commit-gate.py:348` 的判据正则 `^\s*-?\s*\[PROD_TOUCHED\]`（= `agate/rules/markers.yaml` 的 `PROD_TOUCHED.lead_variant: dash_only`）：

- **漏拦**：粗体 `**[PROD_TOUCHED]**`、引用块 `> [PROD_TOUCHED]`、`*`/`+` 列表写法均**不命中**；
- **误拦**：`- [PROD_TOUCHED]: 无`（否定写法）**命中**（真实样例见 peekview `T039…/P4-progress.md:21`）。

设计 §3.6 写「**T4** = 现有 PROD_TOUCHED diff 扫描，**保持原样**」；而 §4 / BDD-54 要求「正文写粗体 `**[PROD_TOUCHED]**`、字段写 false → 仍然中止（**T4 优先**）」。

**矛盾**：「保持原样」的 T4 命不中粗体；真正认粗体的是 **T1**（用 `markers.yaml` **default** 口径），但 T1 只扫**声明文件**（`declaration_files` 不含 `P*-progress.md`），而 F4 的真实样例**恰在 progress 文件** ⇒ 残留绕过子集未闭合。另 `markers.yaml` 把 `PROD_TOUCHED` 登记为 `dash_only`，与 T1 的 `default` 口径**分叉**（违反单源原则）。

**cso 要求**：明确安全门扫描面 = 任务目录内**全部暂存文件**；模式 = `markers.yaml` **default** 口径（或显式升级 T4 并删「保持原样」）；补锚「**非声明文件**中的粗体/引用块正向 PROD_TOUCHED + 字段 false → 中止」；调和 T1 default 与 PROD_TOUCHED dash_only 的注册表分叉。

**待决**：安全门的扫描面与模式应如何规格化？

---

## 3. 复现命令

**Q2（G3 探针，真实仓库）**：

```bash
cd <agateon 仓库根>            # 干净工作区
P=agate-workspace/tasks/TZZ999-probe
mkdir -p "$P"
printf 'task_id: TZZ999\nphase: P0\nstatus: active\njudge:\n  enabled: true\nretries: {}\n' > "$P/.state.yaml"
: > "$P/gate-events.jsonl"
git add "$P"
git commit -m "PROBE"
git show HEAD:"$P/gate-events.jsonl" | wc -l   # 主 Agent 实测 0
wc -l < "$P/gate-events.jsonl"                 # 主 Agent 实测 2
# 清理：
git reset --soft HEAD~1 && git rm -r --cached -f "$P" && rm -rf "$P"
```

**Q4（F4 现状）**：

```bash
sed -n '348p' agate/scripts/pre-commit-gate.py     # 现行 PROD_TOUCHED 正则
grep -n -A3 "PROD_TOUCHED" agate/rules/markers.yaml # lead_variant 登记
```

---

## 4. 请专家回答（清单）

| # | 问题 | 需要给出 |
|---|---|---|
| Q1 | G3 归属批（A1 / A3 / 排除）？ | 选择 + 判据 |
| Q2 | G3 症状与根因？ | 能否复现 + 根因判断 + §2.7 措辞建议 |
| Q3 | B1 收口（A1 落地脚本 / 移除命令）？ | 选择 + 理由 |
| Q4 | F4 安全门扫描面与模式规格？ | 规格 + 与 markers.yaml 单源的关系 |

> 另：`P2-review-eng.md` 的 `M1`（G3 纳入）/`M2`（G4 = RM-AG0101：`check-state-transition.py` 的 BDD-3「重派」关键词扫描误伤注入的 `AGATE_CARD` 正文）与 `P2-review-cso.md` 的 4 MEDIUM / 2 LOW 也欢迎一并评估（非阻塞）。
