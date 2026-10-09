---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 A / RM-AG0109——把 R6 双向差分脚本登记为「项目固定资产」并新增 AGENTS.md 工作流 0a 指针；roadmap 回写 done；CHANGELOG 补条目
files_changed: [AGENTS.md, CHANGELOG.md, agate-workspace/roadmap/roadmap.md]
commit: 448a154a
---

# 协议-脚本对齐审查（A0109-ASSET-01）

> 审查对象：`hotfix/batch-a-asset` 的 commit `448a154a`（`git show 448a154a`）。
> 只读审查——未改任何协议/脚本/测试，未 commit/push。留痕见同目录 `.progress.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED**（与 A1 同源） |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（含 1 条不阻断观察） |
| A4 | 测试覆盖 | ALIGNED（docs-only，无新测试；全量实跑见下） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（无既有用例因本批转红；无夹具需更新） |
| A5 | 下游影响 + 文档传播 | NEEDS_HUMAN_REVIEW（见下，实为 A1 的下游） |
| A6 | 锚点表覆盖 | ALIGNED（无需改锚点表；附「指针无机械守护」观察） |
| A7 | 设计原则一致性 | ALIGNED（附 ADR-014 关联观察） |
| A8 | 声称-命令绑定 | **MISALIGNED**（1 条声称被证伪） |

**总判定：不可 commit。** 阻塞项 = A1/A2/A8：AGENTS.md:107 给出的调用形式与脚本**实际接口不一致**，照抄即失败（exit 2）。须先修正指针，再重审。

---

## 逐项审查

### A1: 文档→脚本对齐 —— MISALIGNED

**文档声明**（`AGENTS.md:103-108`，本批新增）：

> **项目固定资产（RM-AG0109）**：本条的「在副本上差分 + 跑前跑后核验原仓干净」已有**可执行实现**——
> `docs/design-notes/r6-differential.sh` + `docs/design-notes/r6-allowlist.yaml`（TAG0050 复盘沉淀，
> 自带**跑前/跑后「原仓库干净」自核验**）。做「改前/改后行为差分」时**直接用它们**，不要每次手写：
> ```bash
> bash docs/design-notes/r6-differential.sh <副本仓库路径> [允许差异清单]
> ```

**脚本实现**（`docs/design-notes/r6-differential.sh:37-47`）：

```bash
while [ $# -gt 0 ]; do
  case "$1" in
    --before) BEFORE="${2:-}"; shift 2 ;;
    --after)  AFTER="${2:-}";  shift 2 ;;
    --allow)  ALLOW="${2:-}";  shift 2 ;;
    --corpus) CORPORA+=("${2:-}"); shift 2 ;;
    -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *) echo "r6-differential: 未知参数: $1" >&2; exit 2 ;;
  esac
done
```

**差异**：AGENTS.md 给的是**位置参数**形式（`<副本仓库路径> [允许差异清单]`），但脚本**只接受 `--before/--after/--corpus/--allow` 选项**，任何位置参数都落到 `*)` 分支 → `exit 2`。二者**接口不一致**。

**实测复现**（只读、fail-fast、无写副作用；事后 `git status --porcelain` 仅多出本审查的留痕文件）：

```
$ bash docs/design-notes/r6-differential.sh /tmp/some-corpus
r6-differential: 未知参数: /tmp/some-corpus
exit=2
```

即：用户**照 AGENTS.md 抄**得到的不是「可执行判据」，而是参数错误。这与本指针的目的（把纪律变成「可直接调用的固定资产」）**自相矛盾**。

**交叉证据**（脚本接口的正确形式多处一致，进一步坐实 AGENTS.md 是唯一错源）：

- 脚本自述接口（`r6-differential.sh:9-14`）：`bash r6-differential.sh [--before <rev>] [--after <dir>] [--corpus <repo>]... [--allow <file>]`。
- 索引（`docs/design-notes/README.md:36`）：「接口 `--before/--after/--corpus/--allow`」。
- TAG0050 真实用法（`agate-workspace/tasks/TAG0050-task-data-contract/P4-review-cso.md:82,85,87`）：`--corpus .` / `--corpus <clone>` / `--allow <file>`。

**语义判断**：脚本 `--corpus` 缺省为 `.`，而脚本**自带**「corpus 必须干净」自核验（`r6-differential.sh:68-82` 运行前 + `:386-395` 运行后）⇒ 在开发 checkout（通常有未提交改动）上直接跑 `--corpus .` 会 `exit 1`。故指针**意图**（传副本路径）正确，只是**写法**错误。

**建议**（修复方向，最小改动）：

```bash
bash docs/design-notes/r6-differential.sh --corpus <副本仓库路径> [--allow <允许差异清单>]
```

（`--allow` 缺省即 `docs/design-notes/r6-allowlist.yaml`，与 AGENTS.md 指出的路径一致，可省；`--before`/`--after` 一般用缺省。指针**无需**写 `AGATE_ROOT`——脚本在 `:263` 自行 `env["AGATE_ROOT"] = root`，且取副本路径由 `--corpus` 承担，不依赖外部 env。）

### A2: 脚本→文档对齐 —— MISALIGNED（与 A1 同源）

从脚本侧看：脚本的权威接口（`:9-14` 头注 + `--help`）与 `docs/design-notes/README.md:36` 一致，**唯独**本批新增的 AGENTS.md 指针背离。脚本本身无改动，无需回改脚本；**改文档即可**。与 A1 是同一缺陷的两面。

### A3: 一致性连锁 + 反向传播

**A3a（连锁：已知衍生改动）**

| 应联动文件 | 是否已动 | 判定 |
|---|---|---|
| `AGENTS.md`（0a 指针） | ✅ 新增 | 但**用法写错**（A1） |
| `CHANGELOG.md` | ✅ 新增条目（`[Unreleased]` → 「文档 / 登记」，`CHANGELOG.md:88-92`） | ALIGNED |
| `agate-workspace/roadmap/roadmap.md` RM-AG0109 | ✅ 状态 `backlog`→`done`，关联任务 `hotfix-batchA-0109` | ALIGNED |
| `docs/design-notes/README.md` | 无需动——`:36` 已登记且接口正确 | ALIGNED |

**A3b（反向传播：主动推断应被影响但未列 diff 的文件）**

- `docs/guides/worktree-dogfooding-guide.md`：AGENTS.md 有「同一口径的镜像见 …『改动通道』节」——但该节讲 **worktree vs hotfix**，**不含** 0a 的「差分在副本上跑」纪律（`grep 差分/r6 docs/guides/*.md` 零命中）⇒ **无需传播**。
- `agate/phase-cards/*.md`（RM-AG0109 文本点名「阶段卡片」）：逐卡核查——各卡只写「推进条件（全部满足才写 phase: Pn）」（`P1:207 / P2:316 / P3:96 / P4:175 / P5:88 / P6:226 / P7:103 / P8:152`），是**推进条件**表述，**无**「手写 `.state.yaml` 编辑 phase」的示例/指令（见 A8-④）。⇒ 严格说**无字面待改项**；但**本批 commit 的 ② 记录只引 `state-machine.md`，未提阶段卡片**（roadmap 原文点名了它）——属**记录不完整**，不阻断。
- `agate/scripts/README.md` / CHECK 9 锚点表：`r6-differential.sh` **不在 `agate/scripts/` 下**，不属脚本登记面/锚点目标 ⇒ 无需动（详见 A6）。

**结论**：ALIGNED（含上述「阶段卡片记录不完整」的不阻断观察）。

### A4: 测试覆盖

本批为 **docs-only**（AGENTS.md / CHANGELOG.md / roadmap.md），无代码/脚本/测试改动，故无新增用例（合理）。

**全量实跑**（本机，2026-10-09）：

```
$ python3 -m pytest agate/tests/ -q -n auto
1 failed, 2906 passed, 2 skipped in 97.32s (0:01:37)
```

唯一失败：`agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`。**与本次改动无关**——该用例在 `:298-308` **实跑真实 `opencode` 二进制**（`opencode debug agent orchestrator`），而本机 opencode 版本的子命令是 **`debug agents`**（复数）：

```
$ opencode debug --help | grep -i agent
  agents    List all agents
```

⇒ 环境/工具链漂移（opencode CLI 版本差异），非本批引入（本批不触碰该用例读取的 `agate/SETUP.md`，也不触碰任何其依赖）。**结论：ALIGNED**（无回归由本批引入）。

> **观察**：**无任何测试守护 AGENTS.md 指针**——`agate/tests/integration/test_tag0050_a0_a1_ledger.py:373-378` 只断言 `r6-differential.sh` / `r6-allowlist.yaml` **文件存在**，不校验接口；CHECK 10 的脚本名正则也**不匹配** `r6-differential.sh`（见 A6）。这正是本 A1 缺陷能**静默过关**的原因。

### A4b: 闭合后既有测试转红 + 夹具更新清单

**经实测无既有用例因本批转红。** 需更新的夹具：**无**。

（上述 `test_bdd_43` 单条失败为**环境性**、**先于本批存在**，不属「因本批闭合而转红」；本批未改任何测试读取的数据/文件，因果上不可能影响它。）

### A5: 下游影响 + 文档传播 —— NEEDS_HUMAN_REVIEW

- **gate 行为**：无变化（docs-only，不触 `agate/scripts/*`）。非破坏性变更。
- **CHANGELOG**：已更新（`CHANGELOG.md:88-92`，`[Unreleased]` 段内），措辞与本批一致。
- **文档传播**：本批的**实际下游影响**即 A1——**用户/维护者按 AGENTS.md 指针操作会失败**（exit 2），而该纪律的**目的**是「可直接调用」。此下游缺口由 A1 的修复关闭；因涉及「AGENTS.md 是否应内联复述接口」的取舍，本项标 **NEEDS_HUMAN_REVIEW**（裁决点见 A7）。

**配对**：`[HUMAN_CONFIRMED: 待主 Agent 修复 A1 指针后，人工确认 AGENTS.md 复述形式]`——未确认前等同 MISALIGNED（本报告已整体判「不可 commit」）。

### A6: 锚点表覆盖 —— ALIGNED

- CHECK 9（协议-脚本结构对齐）锚点面向 `agate/scripts/` 内的脚本；`r6-differential.sh` **不在该目录**，非锚点目标 ⇒ **无需更新锚点表**。
- CHECK 10（协议文档脚本名引用漂移）**扫描** `AGENTS.md`（`check-protocol-consistency.py:970-972`），但其正则 `SCRIPT_REF_RE`（`:961`）只匹配 `check-*`/`agate-*`/`agate_*`/hook 名/`count-tests.sh`/`ci-gate-backstop.py`，**不匹配** `r6-differential.sh`。实测新增行**零命中**：

  ```
  matches in AGENTS line: []   # 对 "`docs/design-notes/r6-differential.sh` + `r6-allowlist.yaml`"
  ```

  ⇒ 本批**不新增** CHECK10 ERROR/WARNING（与 `0 ERROR` 实测一致）。

**观察（不阻断）**：`r6-differential.sh` 落在 `agate/scripts/` 之外 ⇒ 既不在 CHECK 9 锚点、也不在 CHECK 10 脚本名白名单 ⇒ **其接口的正确性无任何机械守护**。这是「固定资产」**位置选择**（`docs/design-notes/` vs `agate/scripts/`）的连带后果，见下「重点 2」。

### A7: 设计原则一致性 —— ALIGNED（附观察）

相关 ADR 逐条：

- **ADR-014（判据单一权威源——判据必须单源，文档可以复述）**：AGENTS.md 指针属**复述**。ADR-014 要求「复述须与单源一致」（`:551`「引文须与真值一致」）——本批复述与单源（脚本接口）**不一致**，是 A1 缺陷在 ADR 层面的映射。**修正 A1 即恢复 ADR-014 一致**，不构成独立的架构决策问题。
- **ADR-004（安全网分层）**：无违反（docs-only，无新放行路径）。
- 无「未记录的架构决策」需要补 ADR（本批只是登记既有脚本 + 指针）。

**结论：ALIGNED**（ADR-014 关联点已在 A1 中作为修复项）。

### A8: 声称-命令绑定 —— MISALIGNED

本批（commit message / roadmap / CHANGELOG / 报告）的结论类声称逐条：

| # | 声称（出处） | 复现命令 | 结论 |
|---|---|---|---|
| ① | 「`check-protocol-consistency.py` 0 ERROR」（commit msg） | `python3 agate/scripts/check-protocol-consistency.py` | ✅ **成立**：exit 0，**0 ERROR**，427 frozen WARNING |
| ② | 「roadmap 列数 0 异常」（commit msg） | 按 `check-gate.py:2144+` `_check_roadmap_done` 逻辑扫 `roadmap.md`（`len(split("|")) != 9` 且匹配 `^\|\s*RM-`） | ✅ **成立**：anomalies = 0 |
| ③ | 「RM-AG0109 回写 done」（commit msg / roadmap） | `git show 448a154a -- agate-workspace/roadmap/roadmap.md` | ✅ **成立**：状态列 `backlog`→`done` |
| ④ | 「① 新增**可执行实现指针**」（commit msg，隐含「指针与脚本用法一致」） | `bash docs/design-notes/r6-differential.sh /tmp/some-corpus` | ❌ **被证伪**：`未知参数`，exit 2（详见 A1） |
| ⑤ | 「自带跑前/跑后『原仓库干净』自核验」（AGENTS.md:105） | 读 `r6-differential.sh:68-82`（前）+ `:386-395`（后） | ✅ **成立** |
| ⑥ | 「② 早已满足（`state-machine.md` 推进步骤 7 即写 `agate-state-set.py`）」（commit msg / roadmap） | 读 `agate/state-machine.md:410-419`（步骤 7）+ `:338`（唯一写入口） | ✅ **成立**（就 `state-machine.md` 而言；阶段卡片半边未在记录中体现，见 A3b，不阻断） |

**处置**：④ 是被证伪的声称，**不可保留**——须随 A1 一并修正（改指针写法），否则等于把「有据」的外观留在记录里。

---

## 五项重点结论

1. **指针正确性（A1，阻塞）**：AGENTS.md:107 的调用形式与脚本实际用法**不一致**——AGENTS.md 用**位置参数**，脚本只认 `--corpus`/`--allow`（`r6-differential.sh:37-47` 的 `*)` 分支 `exit 2`）。实测照抄即失败。脚本**不需要**在指针里额外写 `AGATE_ROOT`（脚本 `:263` 自行设置）；`--allow` 缺省路径（`$SCRIPT_DIR/r6-allowlist.yaml`）与 AGENTS.md 指出的路径**一致**，故 `[允许差异清单]` 作可选项没错，错的是**参数传递形式**。**修法**：`--corpus <副本仓库路径> [--allow <清单>]`。

2. **位置是否恰当（不阻断建议）**：`docs/design-notes/` 的目录语义是**决策记录索引**（`docs/design-notes/README.md:1`「决策记录索引」；同目录为 `design-*.md` 等设计笔记）。把**可复用工具**（固定资产）放此，与目录语义**不完全吻合**；且它**不在** `agate/scripts/`，导致 CHECK 9 锚点 / CHECK 10 脚本名白名单**都不覆盖**它（A6）。**建议（不阻断）**：若后续仍要长期维护，考虑移入脚本目录体系（如 `agate/scripts/` 或仓库级 `tools/`）以获得机械守护；**但**本批 `docs/design-notes/README.md:36` 已按现状登记该资产，**迁移属另一次改动**，不作为本批阻塞项。

3. **② 判定是否成立（成立）**：`state-machine.md` **确实**已用 `agate-state-set.py` 作推进示例——**推进步骤 7** 在 `:410-419`（`:412` / `:414` 明写「用 `agate-state-set.py` 写回 .state.yaml」），且 `:338` 声明「**phase 的唯一写入口是 `agate-state-set.py`**」、`:335` 让 `agate next` 打印建议命令。**未发现**阶段卡片里仍写「手写 `.state.yaml` 编辑 phase」的**活指引**：各卡只有「推进条件（全部满足才写 phase: Pn）」的条件表述，**无字面手写示例**。⇒ **② 判定成立**；唯一欠缺是**记录未提阶段卡片**（roadmap 原文点名），属记录不完整、不阻断。

4. **A8（声称-命令绑定）**：①②③⑤⑥ 均**成立**（命令见 A8 表）；**④ 被证伪**（指针 ≠ 脚本用法）——这是本批**唯一**的实质缺陷来源，与 A1 同源。

5. **A4b（既有用例转红）**：**无**既有用例因本批转红；**无**夹具需更新。全量实跑 `1 failed, 2906 passed, 2 skipped`，唯一失败 `test_bdd_43`（真实 opencode 二进制 `debug agent` vs 本机 `debug agents`）为**环境性、先于本批存在**，与本 docs-only 改动**无因果**。

---

## 是否可 commit

**不可 commit。**

- **阻塞项**：A1 / A2 / A8——AGENTS.md:107 指针写法与脚本接口不一致，照抄 `exit 2`（实测）。
- **修复方向**（单一主题、可快速验证，属 hotfix 面）：
  ```diff
  -    bash docs/design-notes/r6-differential.sh <副本仓库路径> [允许差异清单]
  +    bash docs/design-notes/r6-differential.sh --corpus <副本仓库路径> [--allow <允许差异清单>]
  ```
  修后按 A8-④ 复跑该命令应进入脚本主体（不再 `未知参数`），并重跑本审查（或至少重跑 `check-protocol-consistency.py` 确认仍 0 ERROR）。
- **非阻塞建议**：A3b（② 记录补提阶段卡片）、A5/A7（AGENTS.md 是否内联复述接口，或改为指向脚本 `--help`——涉及 ADR-014「复述须与单源一致」的取舍）、A6（固定资产位置与机械守护缺失）。
- A5 的 `NEEDS_HUMAN_REVIEW` 未配 `[HUMAN_CONFIRMED: …]`，按闭环规则亦**不允许 commit**——但即便确认，A1 仍须先修。

---

## 审查者声明

- 只读审查：未改任何协议/脚本/测试，未 commit/push；scratch 仅为 `bash … <位置参数>` 的 fail-fast 复现（无写副作用），事后 `git status --porcelain` 仅含本审查的留痕文件。
- 留痕文件：`docs/reviews/agate-alignment-2026-10-09-A0109-ASSET-01.progress.md`。
