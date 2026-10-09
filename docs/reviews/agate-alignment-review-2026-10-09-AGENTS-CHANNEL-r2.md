---
review_date: 2026-10-09
reviewer: protocol-alignment-review
round: 2
change_summary: r2 复审——核实 r1 三处发现（M1/M2/M3）是否修复 + 完整 A1-A8 复审
files_changed: [AGENTS.md, docs/guides/worktree-dogfooding-guide.md]
commit: f189d0e4
supersedes: docs/reviews/agate-alignment-review-2026-10-09-AGENTS-CHANNEL.md
---

# 协议-脚本对齐审查（r2）

## 第 1 轮 3 处发现逐条核实

| # | r1 发现 | 修法（我方声称） | 核实命令 | 结论 |
|---|---------|------------------|----------|------|
| M1 | `docs/guides/worktree-dogfooding-guide.md` 是「改动通道」节活镜像，仍列旧口径；其条件 1 仍「≤2 文件」 | ① guide「不适用」段去掉协议改动 + 新增 ⚠️ 段；② 条件 1 改「单一主题」 | `git show f189d0e4 -- docs/guides/worktree-dogfooding-guide.md`（`guide:260/266/268`） | ✅ **已修** |
| M2 | 更正条目仍挂「必须立项」标题下 ⇒ 条目与标题自相矛盾 | 把条目移出清单，改为清单后独立段落 | `git show f189d0e4 -- AGENTS.md`；`sed -n '54,64p' AGENTS.md`（`58` 行无 `- ` 前缀、前有 `>` 空行） | ✅ **已修** |
| M3 | 原 commit message「grep 0 命中」为假 | `--amend` 重写，删假声称，改列 r1 漏项与同步动作 | `git log -1 --format=%B f189d0e4` | ✅ **已修** |

**M1 逐句核实**（`docs/guides/worktree-dogfooding-guide.md`）：

- `:260` 条件 1：`**单一主题**：改动服务一个自洽目标、无跨模块影响（**2026-10-03 更正：文件数不再作为条件**，见 AGENTS.md）` —— 与 `AGENTS.md:41` 一致 ✅
- `:266` 不适用清单：`需阶段产出的改动（= agate 任务）、跨子系统探索性设计。` —— 已**移除**「`agate/` 协议本体/脚本改动」✅
- `:268` 新增独立 ⚠️ 段：「『`agate/` 协议本体/脚本改动』不在上述面内（2026-10-09 更正，与 `AGENTS.md` 同步）……」 ✅

**M2 逐句核实**（`AGENTS.md:55-61`）：清单仅剩 2 条（阶段产出 / 跨子系统探索性设计），其后的 ⚠️ 更正段为**独立段落**（`58` 行无 `- ` 列表符，前面是 `>` 空行）——条目不再挂在「必须立项」标题之下，**条目↔标题矛盾已消除** ✅

**M3 逐句核实**：`f189d0e4` commit message 中**已无**「grep 0 命中」字样；改为「同步（SELF-GATE r1 抓出的反向传播漏项）：`docs/guides/worktree-dogfooding-guide.md`……**已同步**；并修其滞后的「改动面 ≤2 文件」……更正条目**移出**「必须立项」清单标题之下」——如实、且与 diff 相符 ✅

**⇒ r1 三处 MISALIGNED 全部修复。**

---

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（含 1 条残留 NIT） |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED（含 1 条残留 NIT） |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**总评**：r1 三处发现均已真实修复；`AGENTS.md` 与 guide 两处**逐句一致**（仅 trivial 措辞差）；本次 commit message **每条声称均可复现**；**未引入新矛盾**。结论为**通过（可 commit）**。残留 1 条**非阻断 NIT**（roadmap 一处陈旧描述，见下）。

---

## 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`AGENTS.md:59`，更正后）：
> **⚠️「`agate/` 协议本体或脚本改动」不在上述面内（2026-10-09 更正）**：……**口径以条件 2 + 轴 C 为准**——协议本体/脚本改动触发的是**独立评审义务**（提交信息写 `self-gate-review:`），**不是**立项义务……只有**跨多子系统 / 需探索性设计 / 需阶段产出与看板登记**才立项。

**比对锚点**：

- 条件 2（`AGENTS.md:42`）：「……**注意：这与是否触发 SELF-GATE 无关**——若碰触发面，仍须在提交信息写 `self-gate-review:`」→ **一致**。
- 轴 C（`AGENTS.md:25`）：「碰 SELF-GATE 触发面 → 须独立评审；**留痕**由 `self-gate-review:`……仅 WARNING、**不拦截**——**与 B 无关**」→ **一致**。
- `SELF-GATE.md:7-11`（强制力边界）：只讲**评审/留痕**（hook WARNING 不拦截），**从不提「立项」**→ 更正后正文与之**一致**。

**脚本面**：立项 vs hotfix 是**人读工作流约定**，无机器判据实现（`agate/scripts/*` 无该概念）→ 无「文档↔脚本」对齐对象。

**结论**：ALIGNED。

---

### A2: 脚本→文档对齐

本次仅改 2 个 `.md`（`git show f189d0e4 --stat`：`AGENTS.md`、`docs/guides/worktree-dogfooding-guide.md`），无脚本改动 → 无「脚本→文档」待同步项。

**结论**：ALIGNED。

---

### A3: 一致性连锁 + 反向传播

#### A3a 一致性连锁

- **`SELF-GATE.md` 无需同步**：其「强制力边界」只表达评审留痕口径，从不主张「协议改动须立项」——与更正后口径本就不冲突（r1 已核，r2 复核无变化）。

#### A3b 反向传播（本仓全量扫描）

扫描命令（含 `docs/`、`agate/`、`.github/`、`README*`、`SELF-GATE.md`）：

```bash
grep -rn "不适用 hotfix\|必须立项\|≤2 文件\|≤2 个文件\|协议本体/脚本改动\|协议本体或脚本改动" \
  --include="*.md" --include="*.yaml" --include="*.yml" --include="*.json" . | grep -v "/archived/"
```

**活文档命中与判定**：

| 文件 | 内容 | 判定 |
|------|------|------|
| `AGENTS.md:45/55/59` | 45=「原为 ≤2 个文件」说明；55=标题；59=更正段 | ✅ 正确（本次所改） |
| `docs/guides/worktree-dogfooding-guide.md:266/268` | 不适用清单（已去协议改动）+ ⚠️ 更正段 | ✅ 正确（本次所改） |
| `agate-workspace/roadmap/roadmap.md:81`（RM-AG0079） | 「agateon 仓库自己有一条 hotfix 通道（`AGENTS.md:17-40`：改动面 **≤2 文件** + **不触发 SELF-GATE** + 不产生阶段产出 + 可快速验证……」 | ⚠️ **残留陈旧**（见下 NIT） |

**冻结文件命中**（按设计不改，非漏项）：`agate-workspace/reviews/self-gate-worktree-necessity-20260929.md:50`、`docs/reviews/agate-alignment-review-2026-10-09-AGENTS-CHANNEL.md`（r1 报告，本次随 amend 入库）、`docs/reviews/agate-alignment-2026-10-09-AGENTS-CHANNEL-01.progress.md`（r1 留痕，本次入库）。

**⇒ 无「活规则文档」仍写旧口径。** 唯一残留是 roadmap 一处**描述性**陈旧（NIT）。

**NIT（非阻断）——`RM-AG0079` 陈旧描述**：该行把 hotfix 通道描述为「改动面 **≤2 文件** + **不触发 SELF-GATE** + ……」。其两处均已过时：①「≤2 文件」早于 2026-10-03 被更正为「单一主题」；②「不触发 SELF-GATE」正是**本次更正的误解**（条件 2 明说「与是否触发 SELF-GATE 无关」）。**不判 MISALIGNED 的理由**（据实）：(a) 它在 `agate-workspace/`（任务数据），`check-protocol-consistency.py` 显式将其排除在扫描面外（「按设计不改」）；(b) **本仓先例**——2026-10-03 那次条件 1 更正（commit `37ed89d4`）**只改了 `AGENTS.md`，未动 roadmap**（`git show --stat 37ed89d4` 实测），即 roadmap 描述性引用**不随 `AGENTS.md` 条件变更同步**；(c) 它是 backlog 条目的**时点快照**（含创建日期），非规则权威源。**建议**：若日后触及 RM-AG0079，顺手把该括注改为「单一主题 + 与 SELF-GATE 无关」；本批不要求。

**结论**：ALIGNED（反向传播已补全到活镜像；唯一残留为 roadmap 描述性陈旧，按先例不属本批同步面）。

#### A3c 两处活文档互一致性（逐句比对）

| 维度 | `AGENTS.md:59` | `guide:268` | 一致性 |
|------|----------------|-------------|--------|
| 触发面归属 | 「不在上述面内」 | 「不在上述面内」 | ✅ |
| 义务性质 | 独立评审义务、**不是**立项义务 | 只带来独立评审义务、**不是**立项义务 | ✅ |
| 判定口径 | 条件 2 + 轴 C | （省略，指 `AGENTS.md`） | ✅ |
| 立项条件 | 跨多子系统 / 需探索性设计 / 需阶段产出**与看板登记** | 跨多子系统 / 需探索性设计 / 需阶段产出 | ✅（guide 略「与看板登记」，与其自身清单「= agate 任务」等价） |
| worktree | 按轴 B（并行/隔离需要时才开） | 按轴 B | ✅（guide 略括注） |
| 先例列表 | 含 4 条 | 省略 | ✅（镜像可省） |

**结论**：两处**语义一致**，差异仅 trivial 措辞（不影响判定）。

---

### A4: 测试覆盖

本次为 **docs-only**（2 个 `.md`），无脚本/判据改动 → **无需新增 pytest**。

**已执行**：

1. 相关文档断言 + 回归测试——**实跑通过**：

   ```
   python3 -m pytest agate/tests/unit/test_doc_sweep.py agate/tests/unit/test_tag0030_assertions.py \
     agate/tests/unit/test_docs_assertions.py agate/tests/unit/test_retrospective_protocol_docs.py \
     agate/tests/regression/test_no_legacy_residue.py -q
   → 98 passed in 0.41s   (EXIT=0)
   ```

2. **既有测试仍不覆盖本口径**：`grep -rn "协议本体或脚本改动\|协议本体/脚本改动\|不适用 hotfix\|必须立项" agate/tests/` → 0 命中。即「改动通道」判据文本无 pytest 守护——属人读约定（观察项，同 r1）。

3. **全量 pytest**：见下。

**全量实跑输出**（本机，2026-10-09）：

```
python3 -m pytest agate/tests/ -q -n auto
→ 1 failed, 2876 passed, 2 skipped in 84.26s (0:01:24)
```

**唯一失败项与环境相关、与本变更无关**：`agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`——本机 `opencode` CLI 子命令为 `debug agents`（复数）而非测试期望的 `debug agent`（单数）：

```
ERROR  Unknown subcommand "agent" for "opencode debug"
       Did you mean this?  agents
assert 1 == 0
```

与 r1 全量跑**完全相同的唯一失败项**（`1 failed, 2876 passed, 2 skipped`），系本机工具链版本漂移，**与 docs-only 改动无因果**。

**污染核验**：全量跑后 `git status --porcelain` 仅显示本审查两份产出文件，`agate-workspace/**` 账本零改动。

**结论**：ALIGNED（docs-only 无需新测试；相关测试 98 passed；全量 2876 passed，唯一失败为环境相关且与本变更无关，与 r1 一致）。

---

### A5: 下游影响 + 文档传播

- **下游 gate 行为**：无影响——开发侧工作流约定，不改变 gate 脚本行为、不改变协议对使用者项目语义，**无破坏性变更**。
- **CHANGELOG**：本次为 `AGENTS.md`+镜像的内部矛盾澄清，协议实质约定未变（协议改动触发 SELF-GATE → 独立评审留痕），**不强制** CHANGELOG 条目（判断项）。
- **文档传播**：**已补全**——活镜像 `docs/guides/worktree-dogfooding-guide.md` 已同步（r1 的 MISALIGNED 已闭环）；`SELF-GATE.md` 无需同步；唯一残留为 roadmap 描述性陈旧（A3b NIT）。

**结论**：ALIGNED（文档传播闭环；残留 NIT 同 A3b）。

---

### A6: 锚点表覆盖

本次未新增协议规则、未改 `check-*.py` → **CHECK 9 锚点表无需更新**。根 `AGENTS.md` 在 CHECK 10 扫描面内（`check-protocol-consistency.py` `SCRIPT_REF_SCAN_FILES` 含 `"AGENTS.md"`），该次运行 CHECK 10 为 WARN 且仅命中 frozen 历史文件，未因本次改动新增告警（见 A8）。

**结论**：ALIGNED。

---

### A7: 设计原则一致性

- **ADR-005（改动性质决定流程，`adr.md:134`）**：更正后口径以「改动性质」（单一主题 vs 跨子系统/探索性设计）为入口维度，放弃「文件数」代理——**一致**。
- **ADR-014（判据单源 / 文档可复述须指权威源，`adr.md:533`）**：r1 指出的镜像漂移**已收口**——`guide` 现复述并**显式指向** `AGENTS.md`（`:268`「与 `AGENTS.md` 同步」），`AGENTS.md:61` 亦反向指向 guide（「同一口径的镜像见……」）——**双向指针，符合 ADR-014**。
- 未发现需新补的架构决策。

**结论**：ALIGNED。

---

### A8: 声称-命令绑定

逐条核实 `f189d0e4` commit message 的声称：

| # | 声称 | 产出命令 | 结论 |
|---|------|---------|------|
| 1 | 「条件 2：……**这与是否触发 SELF-GATE 无关**」 | `sed -n '42p' AGENTS.md` | ✅ 真（原文一致） |
| 2 | 「『不适用 hotfix』第 3 条却把『`agate/` 协议本体或脚本改动』列为**必须立项**」 | `git show 973ed81e:AGENTS.md \| sed -n '55,58p'`（父提交旧态：该条确在「必须立项为任务」标题下） | ✅ 真 |
| 3 | 「实践先例：……（均批次标签直改、**无同名任务目录**）」 | `grep -n "^task_id:" agate-workspace/debt/tech-debt.md`（4 个 task_id 存在）；`ls -d agate-workspace/tasks/TAG00{42,43,44,50}*` | ✅ 真（精确 slug 无同名目录；措辞已由「无任务目录」改为更准确的「无同名任务目录」，回避了编号复用歧义） |
| 4 | 「`docs/guides/worktree-dogfooding-guide.md`……**已同步**」 | `git show f189d0e4 -- docs/guides/worktree-dogfooding-guide.md` | ✅ 真 |
| 5 | 「并修其滞后的『改动面 ≤2 文件』」 | `sed -n '260p' docs/guides/worktree-dogfooding-guide.md`（现为「单一主题」） | ✅ 真 |
| 6 | 「更正条目**移出**『必须立项』清单标题之下」 | `sed -n '54,64p' AGENTS.md` | ✅ 真 |
| 7 | 「校验：`check-protocol-consistency.py` **0 ERROR**」 | `python3 agate/scripts/check-protocol-consistency.py` → `EXIT=0`，输出「仅有 413 个 WARNING，无 ERROR」 | ✅ 真 |
| 8 | `self-gate-review: docs/reviews/agate-alignment-review-2026-10-09-AGENTS-CHANNEL.md` | `git ls-files docs/reviews/`（该路径存在、已入库） | ✅ 路径有效（**但见下 NIT**） |

**结论**：ALIGNED（每条声称均可复现）。

**NIT（非阻断）——`self-gate-review:` 指向 r1（MISALIGNED）报告**：`f189d0e4` 的 `self-gate-review:` 指向 `...-AGENTS-CHANNEL.md`（r1 报告），而 r1 报告的结论是 **MISALIGNED**（列 M1/M2/M3）。按 `SELF-GATE.md`「闭环规则」，MISALIGNED 须修复并**重审**——重审产物是**本 r2 报告**。建议在合并前把 `self-gate-review:` 更新为 `...-AGENTS-CHANNEL-r2.md`（或补一条指向 r2），以免留痕指向一份自身未通过的结论。此系**流程留痕**问题，不影响代码/文档正确性。

---

## 残留观察项（均非阻断）

| # | 项 | 位置 | 处置建议 |
|---|----|------|----------|
| NIT-1 | 陈旧描述「≤2 文件 + 不触发 SELF-GATE」 | `agate-workspace/roadmap/roadmap.md:81`（RM-AG0079） | 非本批同步面（先例 `37ed89d4` 未同步 roadmap）；触及该条目时顺手更正 |
| NIT-2 | `self-gate-review:` 指向 r1（MISALIGNED）报告 | `f189d0e4` commit message | 合并前改指 r2 报告 |

---

## 备注：本报告的只读边界

本次审查**未修改任何协议 / 脚本 / 测试**，仅写本报告与留痕文件；未 `commit` / `push` / `amend`。全量 pytest 已在后台完成并回填（见 A4），跑后账本零污染。
