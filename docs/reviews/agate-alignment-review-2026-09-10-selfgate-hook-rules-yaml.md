---
review_date: 2026-09-10
reviewer: protocol-alignment-review
change_summary: commit-msg-self-gate.py 的 _SELF_GATE_RE 触发面补 `agate/rules/.+\.ya?ml`，收口 PR #307 文档刷新留下的「文档已列 rules/*.yaml、advisory hook 未匹配」缺口
files_changed:
  - agate/scripts/commit-msg-self-gate.py
  - agate/tests/unit/test_commit_msg_self_gate.py
branch: fix/self-gate-hook-rules-yaml
base_main: 6e4cde9
---

# 协议-脚本对齐审查

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐（意图） | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED |
| A4 | 测试覆盖 | ALIGNED（附实跑输出） |
| A5 | 下游影响 + 文档传播 | ALIGNED-WITH-NITS |
| A6 | 锚点表覆盖（CHECK 9） | ALIGNED |
| A7 | 设计原则一致性（ADR） | ALIGNED |

**总结论：`aligned-with-nits`**

无 MISALIGNED，无 NEEDS_HUMAN_REVIEW，无阻断项。两条非阻断 NIT 见 A5。

---

## 意图分析

**为什么改**：PR #307（doc-refresh，批 F/G）把 `SELF-GATE.md`「触发条件」与
`agate/assets/review-roles/protocol-alignment-review.md`「触发条件」都补上了
`agate/rules/*.yaml`（数据面权威源：phases / dispatch / roles / dispatch-tiers.yaml），
但承载实际触发面判定的 advisory hook `commit-msg-self-gate.py` 的 `_SELF_GATE_RE`
正则没有对应 alternation——文档说该触发、hook 不 WARN。本次改动只把 hook 对齐到
**已发布的文档语义**，不引入新语义。

**强制力边界确认**：该 hook 是 WARNING-only。`commit-msg-self-gate.py` docstring
（L5-6）明写「WARNING 不拦截——遵循 hook 鲁棒性优先原则（exit 0）」；`SELF-GATE.md`
「强制力边界」（L9-11）明写「WARNING 不拦截……主 Agent 仍可忽略 WARNING 直接 commit」。
本改动不改变任何拦截/放行行为——它只是让一类此前静默的 commit 现在会收到提醒。

---

## 逐项审查

### A1: 文档→脚本对齐（意图是对齐还是 scope-creep）

**文档声明**（`SELF-GATE.md:13-21`「## 触发条件」）：
> 以下任一文件有改动并准备 commit 时：
> - `agate/scripts/*.sh` … - `agate/scripts/*.py`
> - `agate/*.md`（协议文档）
> - `agate/**/*.md`（角色文件、模板文件等子目录）
> - `agate/rules/*.yaml`（数据面权威源：phases.yaml / dispatch.yaml / roles.yaml / dispatch-tiers.yaml；CHECK 15 专扫）
> - `SELF-GATE.md`

**文档声明**（`agate/assets/review-roles/protocol-alignment-review.md:12`「触发条件」）：
> `agate/scripts/*.sh`、`agate/scripts/*.py`、`agate/*.md`、`agate/**/*.md`、`agate/rules/*.yaml`（数据面权威源）、`SELF-GATE.md` 有改动时……

**脚本实现**（`agate/scripts/commit-msg-self-gate.py:38-41`，改动后）：
> ```python
> _SELF_GATE_RE = re.compile(
>     r"^(agate/scripts/.*\.(sh|py)|agate/[^/]+\.md|agate/.+/.*\.md"
>     r"|agate/rules/.+\.ya?ml|SELF-GATE\.md|README\.md|AGENTS\.md)$"
> )
> ```

**结论**：ALIGNED
**判断**：改动只加了一条 alternation `agate/rules/.+\.ya?ml`，其覆盖的文件集正是文档
已列出的「数据面权威源」。这是把 advisory hook 对齐到 PR #307 已发布的文档语义，
**不是 scope-creep 行为变更**：hook 仍 exit 0、仍只 WARN、拦截行为零变化。stderr
WARNING 文案的文件清单串同步补 `agate/rules/*.yaml`（并把 `agate/*.md` 顺手改成更
准确的 `agate/**/*.md`——正则本来就靠 `agate/.+/.*\.md` alt 匹配子目录 md，旧文案
低估了实际覆盖面，纯文案精确化，无行为含义）。

### A2: 脚本→文档对齐

**结论**：ALIGNED
**判断**：本次是「脚本追文档」，方向天然对齐。反向核对——脚本侧此次唯一的行为面
变化（rules/*.yaml 纳入触发面）已在 `SELF-GATE.md` L20 与
`protocol-alignment-review.md` L12 有权威声明；stderr 文案变化无独立文档面。
`commit-msg-self-gate.py` 自身 docstring（L4-9）用「self-gate 触发文件」泛指、不逐条
枚举，无需同步。

### A3: 一致性连锁 + 反向传播

**A3a 连锁**：diff 已含配套测试（`test_commit_msg_self_gate.py` 加 2 个 `test_bdd_10*`）。
无其他强制连锁。

**A3b 反向传播——所有描述 commit-msg-self-gate 触发面的文件，是否现在都同意
`agate/rules/*.yaml` 是触发项**：

| 文件 | 位置 | 是否已声明 rules/*.yaml 触发 | 结论 |
|------|------|------------------------------|------|
| `SELF-GATE.md` | L20「触发条件」 | ✅ 已列（PR #307） | 一致 |
| `agate/assets/review-roles/protocol-alignment-review.md` | L12「触发条件」 | ✅ 已列（PR #307） | 一致 |
| `agate/git-integration.md` | L180-183「SELF-GATE trailer」 | ✅ 已列 `agate/rules/*.yaml`，并指向 `SELF-GATE.md` | 一致 |
| `AGENTS.md`（仓库根） | L24（自检清单第 5 条） | 不枚举——「触发文件面见 `SELF-GATE.md`」 | 一致（委托，无漂移） |
| `agate/AGENTS.md` | L34 | 只描述 3 个薄壳职责，不列触发面 | 无关，无漂移 |
| `agate/scripts/commit-msg-self-gate.sh`（薄壳） | 全文 | 只做自定位 + python 探测 + exec resolve-entry，无触发列表 | 无关，无漂移 |
| `agate/scripts/README.md` | L26 | 「self-gate 触发面检测」泛指，不枚举 | 一致（另见 A5 NIT-2） |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」 | 全文 grep | 不含 self-gate / rules/*.yaml 描述（self-gate 是 commit-msg hook，不在 pre-commit 检查总览表内） | 无关，无漂移 |
| `agate/state-machine.md` / `agate/dispatch-protocol.md` | grep | 只指向 WORKFLOW「Pre-commit 检查总览」，不各自维护副本 | 无关，无漂移 |

**结论**：ALIGNED。此前 hook 是触发面描述链里唯一的落后方；本改动收口后，所有权威与
次级描述一致同意 `agate/rules/*.yaml` 属 self-gate 触发面。

### A4: 测试覆盖

**新增测试**（`agate/tests/unit/test_commit_msg_self_gate.py:139-173`）：
- `test_bdd_10_rules_yaml_triggers_self_gate_warning`：stage `agate/rules/phases.yaml`
  → `assert result.returncode == 0` + `assert "self-gate" in result.output`（WARNING 出现）
- `test_bdd_10b_rules_yaml_review_trailer_passes`：stage `agate/rules/dispatch-tiers.yaml`
  + commit message 含 `self-gate-review: docs/reviews/x.md` → `assert result.output == ""`（静默通过）

**BDD 编号**：接续既有 `test_bdd_9_*`（L126），编号连续，命名风格与既有一致。

**边界覆盖**：正性用例覆盖 2 个不同的 data-plane yaml（phases / dispatch-tiers）+
trailer 静默分支。未新增「`agate/rules/schema/*.json` 不触发」「`.yaml.bak` / 仓库外
`rules/` 不触发」的负性边界用例——既有 `test_cmsg_3_non_agate_py_no_warning`（L51）
已覆盖泛化的非触发路径，属可接受的轻量缺口（见 A5 NIT-1，非阻断）。

**正则手工核验**（Python re，改动后正则）：

| 输入 | 结果 | 期望 |
|------|------|------|
| `agate/rules/phases.yaml` | MATCH | ✅ 触发 |
| `agate/rules/dispatch.yaml` | MATCH | ✅ |
| `agate/rules/roles.yaml` | MATCH | ✅ |
| `agate/rules/dispatch-tiers.yaml` | MATCH | ✅ |
| `agate/rules/schema/dispatch.schema.json` | nomatch | ✅ 不触发（与文档「*.yaml」措辞一致） |
| `agate/rules/review-mapping.md` | MATCH（经既有 `agate/.+/.*\.md` alt） | ✅ 不回归 |
| `agate/rulesX/phases.yaml` / `docs/rules/phases.yaml` | nomatch | ✅ 无过匹配（`^`/`$` 锚定） |
| `agate/rules/phases.yaml.bak` / `agate/rules/phasesyaml` | nomatch | ✅ 无过匹配 |
| `agate/rules/schema/foo.yaml`（假想） | MATCH（`.+` 跨 `/`） | 见 A5 NIT-1，无害 |

**pytest 实跑输出**（2026-09-10）：
```
$ timeout 200 python3 -m pytest agate/tests/unit/test_commit_msg_self_gate.py \
    agate/tests/integration/test_protocol_alignment_review.py -n auto -q
bringing up nodes...
..................                                                       [100%]
18 passed in 0.90s
EXIT=0
```

**结论**：ALIGNED。TDD 红→绿链完整，新逻辑两条 BDD 场景各有用例，实跑 18 passed / 0 failed。

### A5: 下游影响 + 文档传播

**下游 gate 行为影响**：
- 该 hook 永不阻断（exit 0），下游项目（PeekView 等）的 commit 不会因此被拦。
- 语义面：此前 stage **仅** `agate/rules/*.yaml`（无其他触发文件）的 commit 静默通过；
  改动后这类 commit 会收到 self-gate WARNING，除非 commit message 带
  `self-gate-review:` / `self-gate-skip:` trailer。**这正是 PR #307 已发布的文档意图**
  （数据面权威源改动须走 self-gate），不是意外降级。
- stage 仅 `agate/rules/schema/*.json` 的 commit 仍静默——与 `SELF-GATE.md` 触发条件
  措辞（只写 `*.yaml`）一致。

**CHANGELOG**（`CHANGELOG.md` `[Unreleased]` 当前为空）：未加条目。
- 对照先例 RM-AG0017（`commit-msg-self-gate.py` 触发面补 README/AGENTS）曾在
  CHANGELOG 记一条（L824-826）。
- 但 PR #307 的文档刷新（本改动收口的对象）**同样没有** CHANGELOG 条目——把
  「rules/*.yaml 走 SELF-GATE」当作 v0.71.0 已声明语义的文档追平，非新语义。
- 判断：本改动是 advisory hook 追平已发布文档语义，用户可见协议语义不变，
  CHANGELOG 条目为**可选**。**[NIT-2]**：若维护者希望与 RM-AG0017 先例保持记录风格
  一致，可在 `[Unreleased]` 加一行「advisory `commit-msg-self-gate` 触发面补
  `agate/rules/*.yaml`，收口 PR #307 文档刷新（WARNING-only，语义不变）」。非阻断。

**文档传播**（orchestrator-template / WORKFLOW / dispatch-protocol / 角色文件 / 模板 /
LIMITATIONS）：无需同步——见 A3b 表，所有触发面描述文件要么已列 rules/*.yaml
（SELF-GATE.md / protocol-alignment-review.md / git-integration.md），要么委托给
SELF-GATE.md（AGENTS.md），要么与触发面无关。

**[NIT-1]**（非阻断）：正则 alt `agate/rules/.+\.ya?ml` 用 `.+` 允许跨 `/`，比字面
「`agate/rules/*.yaml` 单层 glob」略宽——`agate/rules/<子目录>/x.yaml` 也会命中。
当前 `agate/rules/` 下除 `schema/`（只含 `.json`）无其他子目录，实际无影响；且对
WARNING-only hook 而言「宁可多提醒」是保守正确方向。可保留现状；若要严格贴合 glob
可用 `agate/rules/[^/]+\.ya?ml`。同时建议（可选）补一条负性测试锁定
`agate/rules/schema/*.json` 不触发，防未来正则调整回归。

**结论**：ALIGNED-WITH-NITS。两条 NIT 均非阻断。

### A6: 锚点表覆盖（CHECK 9）

**核查**（`agate/scripts/check-protocol-consistency.py:512-765` `SCRIPT_ALIGNMENT_ANCHORS`）：
逐条通读 53 个锚点条目，**没有任何一条 `script` 指向 `commit-msg-self-gate.py` 或
`commit-msg-self-gate.sh`**，也没有以 self-gate 触发面文件清单为关键词的锚点。

**反向覆盖检查**（同文件 `check_anchor_coverage`，L811-844）：只枚举
`agate/scripts/check-*.py` glob + `pre-commit-gate.{sh,py}` + `ci-gate-backstop.py`。
`commit-msg-self-gate.py` 不在该集合内，**不会**触发 `CHECK9-coverage` WARNING，
协议也不要求它进锚点表。

**CHECK 10**（`SCRIPT_REF_RE`，L855-860）含 `commit-msg-self-gate\.(?:py|sh)`，但那是
「脚本名引用漂移」检测（脚本改名/退役才相关），本次脚本名未变，不受影响。

**结论**：ALIGNED。CHECK 9 无 `commit-msg-self-gate.py` 锚点，**无需同步任何关键词**。
（机械回归见下：`check-protocol-consistency.py --strict-errors-only` = 0 ERROR，
CHECK 9 PASS。）

### A7: 设计原则一致性（ADR）

**核查**：`grep` `agate/adr.md` 全文，无 ADR 涉及 self-gate 触发文件清单 /
commit-msg hook 触发面。现有 ADR 群（ADR-001/002/004「谁能改什么、怎么保证不被绕过」、
ADR-013「派发路由 / gate 生产者无关性」）均与本改动无交集。

角色文件反向传播表（`protocol-alignment-review.md:39`）指出「改 `SELF-GATE.md` 或
`protocol-alignment-review.md` → self-gate 机制自身的递归适用」——即本改动本身须走
self-gate，而这份审查即是该递归适用的执行。无未记录的架构决策（advisory hook 触发面
是实现细节，不是架构决策）。

**结论**：ALIGNED。无 ADR 蕴含，无需新增 ADR。

---

## 机械回归实跑（2026-09-10）

| 命令 | 结果 |
|------|------|
| `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | **0 ERROR**（362 WARNING 均为既有叙事文件引用噪声，与本改动无关）；CHECK 9 PASS，CHECK 15 PASS；EXIT=0 |
| `python3 agate/scripts/check-structure-consistency.py` | S1-phases OK / S2-workflow OK / S3-cards OK / S4-scripts OK / S5-schema OK / S6-references OK / S0-numbers OK；EXIT=0 |
| `python3 -m pytest test_commit_msg_self_gate.py test_protocol_alignment_review.py -n auto -q` | **18 passed** in 0.90s；EXIT=0 |
| `ruff check agate/scripts/commit-msg-self-gate.py` | All checks passed；EXIT=0 |

---

## 闭环

| 项 | 结论 | 动作 |
|----|------|------|
| A1-A4, A6, A7 | ALIGNED | 通过 |
| A5 | ALIGNED-WITH-NITS | 2 条非阻断 NIT，可随本 PR 顺手处理或记入 backlog，不阻断 commit |

**总结论：`aligned-with-nits`** — 可 commit。commit message 带
`self-gate-review: docs/reviews/agate-alignment-review-2026-09-10-selfgate-hook-rules-yaml.md`。

**MISALIGNED**：无
**NEEDS_HUMAN_REVIEW**：无

**非阻断 NIT**：
- [NIT-1] 正则 `agate/rules/.+\.ya?ml` 的 `.+` 跨 `/`，比字面单层 glob 略宽（当前无实际
  影响；WARNING-only hook 下属保守正确）；可选补 `agate/rules/schema/*.json` 不触发的
  负性测试。
- [NIT-2] 未加 CHANGELOG 条目——与 PR #307 处理方式一致（文档语义追平），可选按
  RM-AG0017 先例在 `[Unreleased]` 记一行。
