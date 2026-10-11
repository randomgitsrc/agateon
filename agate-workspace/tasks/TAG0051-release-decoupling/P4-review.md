---
phase: P4
task_id: TAG0051
agent: review
role: 专家组组长（P4 专家组合并汇总）
type: review
status: approved
created: 2026-10-11
reviewed_inputs:
  - agate-workspace/tasks/TAG0051-release-decoupling/P4-review-code.md
  - agate-workspace/tasks/TAG0051-release-decoupling/P4-review-cso.md
  - docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md
prod_touched: false
---
# P4 评审（专家组汇总） — TAG0051 任务与发布解耦

> **本文件性质**：专家组组长**汇总产出**（唯一 P4 门槛文件）。组长**不发表新意见**——
> 仅把三份已定稿评审的结论落到一个 `status`、记录分歧、逐条转录非阻塞项与阻塞项。
> **以各文件 frontmatter 实际 `status` 为准**（已逐文件实读核验）。

## 0. 结论

**`status: approved` —— 全票无 BLOCKER/CRITICAL。**

三份评审**均**在各自 frontmatter 声明 `status: approved`：

| 评审 | 角色 | 定稿 `status` | 关键发现 |
|------|------|--------------|---------|
| `P4-review-code.md`（backend） | `review` | **approved** | **0 CRITICAL**；Pass-1 六个 CRITICAL 项重跑仍全部成立（fail-closed 更强）；首轮 6 条 INFORMATIONAL 中 4 条已闭合（INFO-1/2/5 + 文档残留由 R-E 收口），INFO-3/4/6 仍开（非阻塞）；本轮新析出 N1（中）/N3（低），N2 已闭合 |
| `P4-review-cso.md`（security，retry 2） | `cso` | **approved** | **0 CRITICAL/HIGH/BLOCKER**；SEC-04（wrapper `--dst` 删除前防护）换 `git clone` 后**未放松**（10 负例全 rc=2、rm 调用数=0、哨兵完好）；残余 MEDIUM×1（SEC-03）+ LOW/INFO SEC-05/06/10/11 + 新增 INFO 2 项（SEC-12/13） |
| `agate-alignment-review-2026-10-11-TAG0051-P4.md`（SELF-GATE，retry 2） | `protocol-alignment-review` | **approved** | **0 协议语义 MISALIGNED**；A1–A8 全 **ALIGNED**；retry 1 的 4 项 MISALIGNED 全部闭合；残余登记 6 处（R1–R6，非行为性）**不阻断**，建议随 P7 收口 |

⇒ 依组长规则「**全票无 BLOCKER ⇒ approved**」：**`status: approved`**。三份评审**均无** BLOCKER/CRITICAL，**不构成打回理由**。

## 1. 三份评审结论摘要

### 1.1 `review`（backend）— approved，0 CRITICAL
- **Pass-1 六个 CRITICAL 项重跑全部成立**：① 枚举新增消费方全覆盖 + legacy 不误伤；② fail-closed 正确性（`--ci-cmd "[]"`→rc1、`--sha ""`→rc1、坏 JSON→rc1、consistency 非 0→rc1）；③ TOCTOU/竞态（残余窗口=INFO-4，净 fail-closed）；④ 删除四个 WARNING 块**无新的静默通过**（R6 双向差分：rc 不变 2→2 为独立物证）；⑤ wrapper 健壮性/注入/误删（负例全闭）；⑥ 敏感数据/凭证（无命令注入面）。
- **R-C 12 测试文件抽查**：**未发现放宽断言**——多为正向重定向 / 断言增强；无新增 skip/xfail/`assert True`。
- 首轮 6 条 INFORMATIONAL：**4 条已闭合**（INFO-1/2/5 + 文档残留 R-E 收口），**3 条仍开**（INFO-3/4/6，非阻塞）。
- 本轮新析出：**N1**（中，非 CRITICAL，wrapper `cp -a` 在本真实仓库因 `.worktrees/` 失败 rc=1）、**N3**（低，断言风格脆性）；**N2 已闭合**。

### 1.2 `cso`（security，retry 2 增量）— approved，0 CRITICAL/HIGH/BLOCKER
- 本轮范围极窄：只复核 wrapper `--dst` 防护面（SEC-04）；其余沿用 retry 1 结论。
- **SEC-04 删除前防护未放松**：10 负例（空/相对/src 内/==src/src 祖先/前缀外/根/前缀根/已存在软链/软链绕过）全部 **rc=2、rm 调用数=0**、哨兵/源/软链完好；最危险三类（src 祖先、前缀外任意绝对路径、软链绕过）换实现后**仍被拒**。
- **`git clone --local --no-hardlinks` 未引入新的可删除/可写路径**，较 `cp -a` **收窄**信任面（不拷源 hooks、无 inode 共享、src 实测只读）。
- 残余：MEDIUM×1（SEC-03，沿用、有据接受）；LOW/INFO SEC-05/06/10/11（沿用）+ SEC-12/13（新增，均 INFO）。**均不阻塞。**

### 1.3 SELF-GATE `protocol-alignment-review`（retry 2）— approved，0 MISALIGNED
- **0 项协议语义 MISALIGNED**，可 commit；A1–A8 逐项 **ALIGNED**。
- retry 1 的 4 项 MISALIGNED **全部闭合**（实读/实跑核验）；R-E/R-F 主体改动自洽（`dispatch-prompt.md:277` ↔ `dispatch-protocol.md:487` 逐字一致；wrapper 换 `git clone` 后 `rc=0 / legacy 39 / 差异 2 / 未匹配 0`）。
- 残余登记 **6 处（R1–R6）**：均为描述性文本（注释/设计记录/角色卡与模板措辞/模块索引），**不改变任何 exit code、判据、ERROR 集合或 acceptance criterion** ⇒ 判非阻断，建议随 P7 收口。

## 2. 分歧记录

**无分歧。**

三份评审的**门槛结论完全一致**（均 `approved`，均 0 BLOCKER/CRITICAL），不存在指向相反方向的结论，故**无需交人工裁决**。

> **供人工知悉的「非分歧」快照时点说明（非意见、非分歧）**：`review` 的 N1 针对**修复轮 R-A..R-E** 时点的
> wrapper 实现（`cp -a`，实测 rc=1）；其后并发落地的 **R-F** 将建 corpus 实现换为
> `git clone --local --no-hardlinks`——该时点由 `cso`（retry 2）与 SELF-GATE（retry 2）评审并经实测确认
> **rc=0 / 39/2/0**。二者**不矛盾**（同一 wrapper 的不同实现快照），**不构成分歧**，仅在此如实登记时点差异，
> 以免后续误读「N1 与 R-F 结论冲突」。

## 3. 非阻塞项清单（逐条一行，供 P5/P7 消费）

### 3.1 `review`（backend）非阻塞项
- **N1**（中）`r6-differential-prepare.sh` 的 `cp -a` 在含 `.worktrees/` 的真实仓库失败（rc=1）⇒ `P5_r6` gate 命令本机跑不起来；**注**：R-F 已换 `git clone`（cso/alignment retry 2 实测 rc=0），该项在最终树应已消解，建议 P5 前以 R-F 后实现复跑确认。（原文：`P4-review-code.md` §4）
- **INFO-3**（非阻塞，仍开）默认 `--dst` 固定共享路径 `$TMP/opencode/tag0051-r6-corpus` 并发竞争。
- **INFO-4**（非阻塞，仍开）`workflow_dispatch` 用 `--sha "$GITHUB_SHA"`（ref HEAD）而非 tag 提交；净 fail-closed。
- **INFO-6**（非阻塞，仍开）`concurrency.group` 两条触发路径取值不同（`release.yml:21`）。
- **N3**（低）断言 `assert "WARNING" not in result.output` 为全局否定，未来无关 WARNING 会误红（脆性），可留待收窄。
- **口径护栏**（非扣留项）`state-machine.md` / `dispatch-protocol.md` 中的**显式否定句**（「**不含** version bump / tag」）属 BDD-1 允许的收敛表述，**不应再删**。

### 3.2 `cso`（security）非阻塞项
- **SEC-03**（MEDIUM，沿用 retry 1、有据接受）required 集合漂移；注释级缓解，未引入需 admin 的 API。
- **SEC-05**（LOW/INFO）门步令牌最小权限（部分收敛）。
- **SEC-06**（LOW/INFO）`workflow_dispatch` 授权语义 = 与旧 tag-push 同级（非回归）。
- **SEC-10**（INFO）安全控制缺自动回归锁：`test_tag0051_r6_harness.py` 仍只覆盖 3 负例（空/相对/src 内），**未覆盖**祖先/前缀外/前缀根/已存在软链/软链绕过 5 类；建议按 §2 负例补 5 条单测。
- **SEC-11**（INFO）`R6_PREPARE_ALLOW_PREFIX` 可放宽为 `/`。
- **SEC-12**（INFO，新增）`--src` 非 git 仓库（或空仓库无 HEAD）时 `git clone` 失败发生在 `rm -rf -- "$DST_REAL"` **之后** ⇒ 仅删已过全量校验的可弃置 corpus，src/前缀外无触；可选硬化：`rm` 前先 `git -C "$SRC_REAL" rev-parse --git-dir` 探活。
- **SEC-13**（INFO，新增）wrapper 头部注释仍述「⑤ 会 `clean -fdx`」，该步已移除（改 clone）⇒ 措辞与实现不一致（结论仍成立）。

### 3.3 SELF-GATE 残余登记（非阻断，建议随 P7 收口）
- **R1** `agate/tests/unit/test_tag0051_r6_harness.py:6` 注释仍述「先 `cp -a` 建一次性整仓 corpus」（注释级，不影响断言）。
- **R2** `agate-workspace/tasks/TAG0051-release-decoupling/P2-design.md:235/283/326/337` 述 `cp -a` + `checkout -- .` + `clean -fdx`（已批准设计记录 vs 实现，留待 P7 以 DESIGN_GAP/known deviation 处置）。
- **R3** `docs/design-notes/r6-differential-prepare.sh:24` 残余「⑤ 会 `clean -fdx`」，与同文件 `:18`/`:192` 冲突（注释级、无行为影响）。
- **R4** `agate/assets/execution-roles/consistency-reviewer.md:53` / `agate/phase-cards/P7-consistency.md:33` / `agate/assets/templates/task-files.md:477`（「P8 **release bump 范围**」措辞陈旧）。
- **R5** `agate/dispatch-protocol.md:948`（「**需要 bump 哪些包**」措辞陈旧）。
- **R6** `agate/state-machine.md:284` = `agate/dispatch-protocol.md:1335`（READY 小结模板 `{version}`；**主 Agent 已明示裁决保留不动**，尊重该裁决）。

### 3.4 跨评审的后续提醒（原文照录，非新增意见）
- **P8 必须补** `CHANGELOG.md [Unreleased]` 的 **TAG0051** 条目（否则 `check-changelog.py` 会拦）。（SELF-GATE A5 / §闭环结论）
- **grep 族补全**：语义族 grep 不匹配 `release bump` / `bump 范围` / `bump 哪些包` —— R4/R5 即由此漏网；后续收敛若仍用单一字面 grep，须补该族。（SELF-GATE 残余登记）

## 4. 阻塞项清单

**无。**

三份评审均无 BLOCKER/CRITICAL/未闭合的 `needs-revision` 项；全部残余项均为**非阻塞**（措辞/注释/鲁棒性/回归锁缺口），依组长规则**不得**据此打回。

---

> **汇总依据**（组长仅转录，未改判）：
> `P4-review-code.md`（`status: approved`，0 CRITICAL）· `P4-review-cso.md`（`status: approved`，0 CRITICAL/HIGH/BLOCKER）·
> `docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md`（`status: approved`，0 协议语义 MISALIGNED）。
> 组长只读汇总，未编辑/删除任何被评审文件，未改动三份评审产出，未 commit / push。
