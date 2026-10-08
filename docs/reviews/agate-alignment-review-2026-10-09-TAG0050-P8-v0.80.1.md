---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: "v0.80.1 补丁发布的文档改动：README.md badge v0.80.0→v0.80.1、CHANGELOG 新增 [0.80.1] 修复节、UPGRADING 新增 v0.80.1 节——记述 PR #409 的 agate-ci-verify 回放协议根修复"
files_changed:
  - README.md
  - CHANGELOG.md
  - agate/UPGRADING.md
---

# 协议-脚本对齐审查（TAG0050 P8：v0.80.1 补丁发布的文档改动）

> 审查对象：v0.80.1 补丁发布的**文档改动**（未提交，分支 `release/v0.80.1`）。
> 触发面（SELF-GATE）：`README.md`、`agate/UPGRADING.md`。
> 背景：v0.80.0（PR #408）的 `agate-ci-verify` 有缺陷（push 到默认分支时选错回放协议根），修复经 PR #409（merge `5d43bfba`，fix commit `1c5f43d8`）落地，main 已全绿。本次为该修复出 v0.80.1 补丁。
> 方法：逐条对照 PR #409 实际改动；版本面用 `check-protocol-consistency.py`（CHECK 7/13）机械核验；全量 pytest 在**仓外副本**实跑。
> 环境隔离：`[PROD_NOT_TOUCHED]` —— 仅在仓外一次性副本 `/tmp/opencode/tag0050-v0801-review` 跑全量 pytest；未对真实仓库执行任何写仓命令，未编辑被评审文件（跑前/跑后原仓 `git status --porcelain` 均为「3 改 + 未跟踪」，被评审 3 文件完好）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | ALIGNED |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（附 1 条既有观察，见下，不阻断） |
| A4 | 测试覆盖 | ALIGNED |
| A5 | 下游影响 + 文档传播 | ALIGNED |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**无 MISALIGNED / 无 NEEDS_HUMAN_REVIEW。** 可 commit。

## dispatch 范围 5 条逐条对照

| 范围 | 问题 | 结论 |
|------|------|------|
| 1 | 版本面自洽（badge / CHANGELOG [0.80.1] / UPGRADING v0.80.1 / [Unreleased] 空 / [0.80.0] 未动 / CHECK 7 & 13） | 全部独立验证通过 —— ALIGNED |
| 2 | 内容与 PR #409 实际改动一致、无过度承诺、无遗漏使用者影响 | 逐点核对一致 —— ALIGNED |
| 3 | 无破坏性变更声明正确 | 属实 —— ALIGNED |
| 4 | 无新未兑现承诺（不预告实施版本号） | 无任何版本预测 —— ALIGNED |
| 5 | SELF-GATE 清单（consistency 0 ERROR；全量 pytest 除既有漂移 1 条外 0 failed） | 通过 —— ALIGNED |

## 逐项审查

### A1: 文档→脚本对齐 —— ALIGNED

**文档声明**（`CHANGELOG.md:17-23`）：
> `_resolve_protocol` 用 `merge-base HEAD origin/<默认分支>` 选协议根 —— push 到 main 时 merge-base = HEAD 自己 ⇒ 用刚合并的新协议回放历史提交 ⇒ 旧 dispatch-context 里注入的卡片 hash … 与新版卡片不符 ⇒ `gate-backstop` 误报多个提交 FAIL（PR 时因 merge-base 恰好指向旧协议而掩盖）。
> **修**：协议根改由**回放基准**推导（`merge-base(<base>, HEAD)` 处的 `agate/`；解析失败显式 note 回退）；`_task_commit_repo` 测试夹具改为**当前协议下良构**…；新增 push-to-main 场景回归用例。

**脚本/测试实现**（PR #409 = fix `1c5f43d8`）：
- `agate/scripts/agate-ci-verify.py:183` 签名 `_resolve_protocol(repo, agate_root_env, base)`；`:538` 调用点传入主流程 `base`。
- `:198` `rev = _merge_base(proto_repo, base, "HEAD") if base else ""`（AGATE_ROOT 分支用 base）；`:206` `rev = (_merge_base(repo, base, "HEAD") if base else "") or "HEAD"`（仓库本体分支用 base）。
- 回退显式 note：`:204` / `:209-210` 调 `_fallback_note(base)`（`:177-180` 产非空 note）。
- 夹具良构：`agate/tests/integration/test_tag0050_ci_replay.py:25-52` 默认写账本首行 `task_created`、`.state.yaml` 去 `status`；`legacy=True` 保留 legacy 语义。
- 新回归用例：`agate/tests/unit/test_agate_ci_verify.py` `test_push_to_main_protocol_root_uses_base_not_head`（合成仓库令 `origin/main == HEAD`，断言取 base 处**旧**协议）+ `test_resolve_protocol_falls_back_when_base_absent`。

**结论**：ALIGNED。文档对缺陷根因、修法、夹具、用例的描述与 PR #409 实际改动逐点一致。

### A2: 脚本→文档对齐 —— ALIGNED

本次 patch **未改脚本**（仅 README/CHANGELOG/UPGRADING 三文档）。文档描述的是已在 PR #409 落地的脚本行为：`_resolve_protocol` 由 `base` 推导协议根（`agate-ci-verify.py:183/198/206`）、`agate/scripts/README.md:108` 的脚本行已在 PR #409 同步（本次不需再改）。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播 —— ALIGNED

**主动推断「应被影响但 diff 未列出的文件」**，逐一验证：

| 候选文件 | 是否需改 | 判据 |
|----------|----------|------|
| `README.zh-CN.md:12` badge（仍 `v0.78.0`） | **不需本次改** | 既有漂移（自 v0.78.0 起未随版本 bump）；**非本次引入**——v0.80.0 发布 commit `9bfef64d` 同样只 bump `README.md`；`check-protocol-consistency.py` CHECK 7 只读 `README.md`（`:493-494`）。既有记录：`docs/reviews/agate-alignment-review-2026-10-09-TAG0050-P8.md:104`「CHECK 7 只读 README.md，不构成一致性缺口」。**沿用同一约定，不算本次缺口** |
| `agate/scripts/README.md` | 不需改 | PR #409 已同步（`:108` 行已改），本次无脚本改动 |
| `agate/UPGRADING.md` 历史 v0.80.0 节 | 不需改 | 已发布历史节，非本次应改写对象 |
| `CHANGELOG.md` `[Unreleased]` | 不需改 | 保留且置空（`:11`），符合 Keep a Changelog 约定 |

**观察（既有、不阻断）**：`README.zh-CN.md` badge 长期落后 3 个版本（v0.78.0）。若维护者希望中文镜像同步，可另开 hotfix；**与本次 v0.80.1 补丁无关**，且不触发任何机械 CHECK。

**结论**：ALIGNED。

### A4: 测试覆盖 —— ALIGNED

**最近一次全量实跑**（仓外副本 `/tmp/opencode/tag0050-v0801-review`，`AGATE_ROOT=<副本>/agate python3 -m pytest agate/tests/ -n auto -q`）：
```
1 failed, 2865 passed, 3 skipped in 76.52s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
该 1 failed 为**既有环境漂移**：本机 `opencode debug` 子命令已由 `agent` 改名 `agents`（断言 `Unknown subcommand "agent" for "opencode debug"`），与本 patch（README/CHANGELOG/UPGRADING 文档）**无关**。与 dispatch「除既有环境漂移 1 条外 0 failed」一致。

本次 patch 无代码改动，回归面由 PR #409 的用例（见 A1）承担，PR #409 的 SELF-GATE 审查（`agate-alignment-review-2026-10-09-TAG0050-P8-ci-fix3.md`）已含改前红/改后绿双向证据。

**结论**：ALIGNED。

### A5: 下游影响 + 文档传播 —— ALIGNED

- **破坏性变更**：无。修复只改 `_resolve_protocol` 的协议根选择（push-to-main 场景），未触碰账本最终状态检查 / 等级检查 / 单调不降检查（`agate-ci-verify.py:498-519` 未变）、未改 `.state.yaml` / 账本格式。UPGRADING 的「无破坏性变更」声明属实。
- **CHANGELOG 是否标注**：已标注（`[0.80.1] - 2026-10-09` + `### 修复`）。
- **文档传播**：`README.md` badge 同步（`:12`）、`UPGRADING.md` 新增使用者影响段（`:290-292`「若你的项目用 agate-ci-verify 作 CI 兜底且在 merge 后向默认分支 push，v0.80.0 会把历史提交误判为 FAIL。升级到 v0.80.1 即修复；无需改动你的项目」）——准确、无遗漏。
- **使用者影响表述核对**：仅影响「`--push --base <before>` 于默认分支 push」路径；PR/本地/新建分支三路径结果不变（`base` 为 HEAD 祖先 ⇒ `merge-base(base, HEAD) = base`）。文档表述与实现一致。

**结论**：ALIGNED。

### A6: 锚点表覆盖 —— ALIGNED

本次 patch 仅文档，未引入新协议规则/字段/脚本名。`check-protocol-consistency.py` CHECK 9（协议-脚本结构对齐）不受影响；CHECK 10（脚本名引用漂移）保持既有 1 条冻结 WARNING。

**结论**：ALIGNED。

### A7: 设计原则一致性 —— ALIGNED

本次为**已落地修复的发布记录**，未引入新的架构决策，无需新增 ADR。修复本身是设计 §2.4 既有语义（push 口径 merge-base = `merge-base(before, HEAD)`）的落地修正——见 `docs/reviews/agate-alignment-review-2026-10-09-TAG0050-P8-ci-fix3.md`（A7 ALIGNED）。

**结论**：ALIGNED。

### A8: 声称-命令绑定 —— ALIGNED

逐条 `声称 → 命令 → 结论`：

| 声称（出处） | 产出命令 | 结论 |
|--------------|----------|------|
| badge `v0.80.1` == CHANGELOG 最新已发布版本（`README.md:12`、`CHANGELOG.md:13`） | `python3 agate/scripts/check-protocol-consistency.py` → CHECK 7 PASS | ✅ 一致 |
| CHANGELOG `[0.80.1]` 节 ↔ UPGRADING `### v0.80.1` 节对应 | 同上 → CHECK 13 PASS | ✅ 一致 |
| `[Unreleased]` 保留且置空（`CHANGELOG.md:11`） | `git diff -U0 CHANGELOG.md`（仅 `+13,12` 一处新增） | ✅ 未动 |
| `[0.80.0]` 历史节未被改动 | `git diff -U0 CHANGELOG.md`（无 `[0.80.0]` 行入 diff） | ✅ 未动 |
| 「回放协议根改由 base 推导 / 夹具良构 / 新回归用例」 | `git show 1c5f43d8 -- agate/scripts/agate-ci-verify.py agate/tests/...` | ✅ 逐点复现 |
| 「误报多个提交 FAIL」（`CHANGELOG.md:20`） | 量值来源：PR #409 提交信息「误报 7 个提交 FAIL」+ `ci-fix3` 审查「CI run 37851356052 的 7 提交 FAIL」；本文档用「多个」不写死数字 | ✅ 保守、可复核 |
| 「除既有环境漂移 1 条外 0 failed」 | 仓外副本 `pytest agate/tests/ -n auto -q` → `1 failed, 2865 passed, 3 skipped` | ✅ 一致 |

无「无法给出命令」的声称。

**结论**：ALIGNED。

## 关键证据（范围 1 版本面）

```
$ python3 agate/scripts/check-protocol-consistency.py
  ✅ PASS  CHECK 7  version badge 与 CHANGELOG 已发布版本
  ✅ PASS  CHECK 13 CHANGELOG↔UPGRADING 章节对应
  仅有 412 个 WARNING，无 ERROR。
EXIT=0
```
（412 WARNING 全部来自 `tasks/`、`reviews/`、`CHANGELOG` 等**按设计不改**的冻结历史文件，属既有噪声。）

```
$ git diff --stat
 CHANGELOG.md       | 12 ++++++++++++
 README.md          |  2 +-
 agate/UPGRADING.md | 15 +++++++++++++++
 3 files changed, 28 insertions(+), 1 deletion(-)
```

## 人工验收清单

- [x] Write 前已检查目标路径不存在同名文件（`ls` 确认 `agate-alignment-review-2026-10-09-TAG0050-P8-v0.80.1.md` 不存在）
- [x] 审查报告含 A1-A8 八项，每项有结论
- [x] MISALIGNED 项：无
- [x] NEEDS_HUMAN_REVIEW 项：无
- [x] 审查报告落盘到 `docs/reviews/agate-alignment-review-{date}-{task_id}.md`
- [x] 只读纪律：仅在仓外副本 `/tmp/opencode/tag0050-v0801-review` 跑全量 pytest；跑后原仓 `git status` 未变（3 改 + 未跟踪，被评审文件完好）
