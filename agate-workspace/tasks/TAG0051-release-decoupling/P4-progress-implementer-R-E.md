# P4-progress-implementer-R-E

> 角色：implementer（P4 修复轮 retry 2，R-E = 文档传播残留收敛）
> 性质：**纯文档/注释口径收敛**，不改任何行为。状态 [PROD_NOT_TOUCHED]。
> canonical：**READY 前置 = 交付物 + CHANGELOG `[Unreleased]` 含 task_id + `bump_type` 意图 + 交付收尾 + CI 全绿（含 push 口径）；不含 version bump / tag。**

## 步骤记录

- [read] 读角色定义 `~/.agate/v0.81.0/agate/assets/execution-roles/implementer.md` + dispatch-context。
- [read] 读 8 个目标文件的现状行（注意：`~/.agate/v0.81.0` 是稳定版，工作区版本已部分改动，需以工作区为准）。
- [canonical 对照] 从 P8-release.md / state-machine.md / dispatch-protocol.md / WORKFLOW.md 取到统一口径逐字。

## 改动（8 文件，comment/doc 收敛，零行为变更）[PROD_NOT_TOUCHED]

1. `agate/scripts/check-gate.py:25`（模块 docstring）：`version/CHANGELOG/tag 检查`
   → `结构化 delivery（method 枚举校验） + roadmap RM 反查`。
2. `agate/assets/execution-roles/implementer.md:45/49/90-101`：
   - :45 「每个包的版本、变更、commit」→「`bump_type` 意图、CHANGELOG `[Unreleased]` 条目、交付检查结果、commit」；
   - :49 「CHANGELOG 更新 + 版本 bump」→「`bump_type` 意图声明 + CHANGELOG `[Unreleased]` 含 task_id 条目 + 交付检查（P2 `gate_commands` 逐包 exit 0）」；
   - 节标题「P8 多包发布」→「P8 多包交付收尾」；正文 bump 版本/旧版本→新版本 → canonical（bump_type 意图 + CHANGELOG + 交付检查 exit 0）；:101 保留原 READY 前置句（已是 canonical/否定式）。
3. `agate/phase-cards/P5-verification.md:147`：「确认 bump-version 后测试仍全绿」→「P8 **交付收尾后**重跑 P5 gate」。
4. `agate/phase-cards/README.md:18`：P8 行「发布：bump / CHANGELOG / 收尾清理」→「交付收尾：`bump_type` 意图 / CHANGELOG `[Unreleased]` / 收尾清理」。
5. `agate/assets/templates/task-files.md:38`：「版本 bump + CHANGELOG」→「`bump_type` 意图 + CHANGELOG `[Unreleased]` 条目」。
6. `agate/assets/templates/active-tasks-template.md:54`：「version bump + CHANGELOG」→「`bump_type` 意图 + CHANGELOG `[Unreleased]`」。
7. `agate/scripts/README.md:149`：`agate-release.py` 索引行补 `gate [--task DIR] [--sha SHA] [--repo R]`（发布门）。
8. `agate/tests/README.md`：脚本→测试映射表补 `agate-release.py gate` → `unit/test_release_gate.py + unit/test_agate_release.py`。

（未碰 `state-machine.md:284` / `dispatch-protocol.md:1335` 的 READY 小结模板——按主 Agent 裁决保留不动。）

## 语义族 grep 自查（覆盖 `agate/` + `AGENTS.md`，排除 `agate/tests/`）

命令（与指引逐字一致）：
```
grep -rnE "version bump|版本 bump|bump-version|bump 版本|version 文件|双路径|tag 已创建|git tag|v\{prev_version\}" \
  agate/ AGENTS.md --include="*.md" --include="*.py" --include="*.yaml" | grep -v "agate/tests/"
```
结果：**38 处命中**（本支改动后）。本支 8 文件内仅剩 3 处（见下 ③/① 与 ⚠️）。

### 逐条归类

**① 显式否定式（「不含 / 不执行 version bump / tag」）——可保留**
- `dispatch-protocol.md:881`、`WORKFLOW.md:327`、`implementer.md:101`、`phase-cards/P8-release.md:13`、`state-machine.md:167/168/330/406`、`AGENTS.md:188`、`check-protocol-consistency.py:481`。
- 理由：均为「**不含** version bump / tag」「P8 **不执行** version bump」等否定式陈述，语义即 canonical 本身。

**② 历史 / 迁移 / 独立发布流程说明——可保留**
- `adr.md:672/673/674/687/688/712`（ADR-016 记录 TAG0051 去 tag/version 决策与旧状）；
- `UPGRADING.md:145/304/305/589/660`（迁移节：P8 去 tag/version、CHECK 7 改版历史）；`CHANGELOG.md`（发布产物）；
- `architect.md:186`（「T005 漏 MCP 版本 bump 的根因」历史教训）；
- `git-integration.md:190`、`AGENTS.md:194/195/207/209`（**READY 之后的独立发布流程**打 tag —— 该流程本就打 tag，BDD-14 要求其时点统一，非 P8 条件面）；
- `check-protocol-consistency.py:483/537`、`agate-release.py:123`（CHECK 7 改版说明 / SHA256 校验建议「从 git tag 自行构建」）；
- `check-retrospective.py:205`、`check-changelog.py:52`（面向项目侧 release 的 `bump-version` 命令——独立发布流程仍有该动作）；
- `phase-cards/P8-release.md:111`（举例项目侧 release 命令 `make bump-version` 会 `git add -A` 的行为）。

**③ 本任务改动自身的原文引用——可保留**
- `check-gate.py:2328`（TAG0051 删除 version/tag 检查块的**变更说明注释**，逐字引用被删的四个 WARNING 块）。

### ⚠️ 语义族 grep 额外暴露、但超出本支授权改动位置/文件（**未改，报告待裁决**）

1. `agate/scripts/check-gate.py:2238`（**文件在授权 8 文件内，但表列「仅 :25」**）：
   注释「version 文件路径和 CHANGELOG 文件名因项目而异，主 Agent 从 P2-design.md packages 读取。」
   —— P8 已不看 version 文件，此句残留。建议改「逐包交付检查命令（P2 `gate_commands`）因项目而异，主 Agent 从 P2-design.md packages 读取。」（该函数无行级锚点，仅函数级 `gate_p8`，改动不伤 obligations。）
2. `agate/assets/templates/dispatch-prompt.md:277`（**不在授权 8 文件**）：节标题「## 版本 bump 判定」——正文已正确（声明 bump 类型），标题用旧词。建议改「## `bump_type` 意图判定」。
3. `agate/dispatch-protocol.md:487`（**不在授权 8 文件**）：段落索引「…/ READY 收尾检查 / 版本 bump 判定 /…」指向上条节名，随上条同改。

> 以上 3 条不属①/②/③；因授权范围硬约束（只改 8 文件 / check-gate.py 仅 :25）未自行改动，按角色纪律报告主 Agent 裁决。

## 验证（自跑，非 P5 gate）

- `pytest test_tag0051_docs_consistency.py test_tag0051_p8_gate.py test_release_gate.py test_release_workflow.py test_agate_release.py test_tag0051_obligations_sync.py` → **90 passed**。
- `pytest test_check_gate.py test_doc_sweep.py test_docs_assertions.py test_env_adapt_docs.py test_t43_check_registration_surface.py test_mvwu_protocol_docs.py` → **338 passed**。
- `check-protocol-consistency.py --strict-errors-only` → **0 ERROR**（432 WARNING 全为按设计不改的冻结文件）。
- `ruff check agate/scripts/check-gate.py` → All checks passed。
- `check-frontmatter.py FILE`（需单文件参数；本支 8 文件均无 frontmatter）→ 跳过。

状态：[PROD_NOT_TOUCHED]
