---
phase: P6
task_id: TAG0051
type: acceptance
parent: P5-verification.md
trace_id: TAG0051-P6-20261011
status: draft
created: 2026-10-11
agent: verifier
pass: 23
fail: 0
ui_affected: false
prod_touched: false
results:
- bdd: '1'
  verdict: PASS
  evidence:
  - bdd-01.log
- bdd: '2'
  verdict: PASS
  evidence:
  - bdd-02.log
- bdd: '3'
  verdict: PASS
  evidence:
  - bdd-03.log
- bdd: '4'
  verdict: PASS
  evidence:
  - bdd-04.log
- bdd: '5'
  verdict: PASS
  evidence:
  - bdd-05.log
- bdd: '6'
  verdict: PASS
  evidence:
  - bdd-06.log
- bdd: '7'
  verdict: PASS
  evidence:
  - bdd-07.log
- bdd: '8'
  verdict: PASS
  evidence:
  - bdd-08.log
- bdd: '9'
  verdict: PASS
  evidence:
  - bdd-09.log
- bdd: '10'
  verdict: PASS
  evidence:
  - bdd-10.log
- bdd: '11'
  verdict: PASS
  evidence:
  - bdd-11.log
- bdd: '12'
  verdict: PASS
  evidence:
  - bdd-12.log
- bdd: '13'
  verdict: PASS
  evidence:
  - bdd-13.log
- bdd: '14'
  verdict: PASS
  evidence:
  - bdd-14.log
- bdd: '15'
  verdict: PASS
  evidence:
  - bdd-15.log
- bdd: '16'
  verdict: PASS
  evidence:
  - bdd-16.log
- bdd: '17'
  verdict: PASS
  evidence:
  - bdd-17.log
- bdd: '18'
  verdict: PASS
  evidence:
  - bdd-18.log
- bdd: '19'
  verdict: PASS
  evidence:
  - bdd-19.log
- bdd: '20'
  verdict: PASS
  evidence:
  - bdd-20.log
  - post-test-residue.log
- bdd: '21'
  verdict: PASS
  evidence:
  - bdd-21.log
- bdd: '22'
  verdict: PASS
  evidence:
  - bdd-22.log
- bdd: '23'
  verdict: PASS
  evidence:
  - bdd-23.log
---

# P6 验收报告 — TAG0051 任务与发布解耦

> **性质**：本文件是 TAG0051 的 **P6 验收产出**。逐条验收 `P1-requirements.md` 的 **23 条 BDD**（1:1，不挑验）。
> **只读验证**：全程**未改**任何代码/测试/协议文件；**未** commit / push；**未**触发 `workflow_dispatch` / 打 tag / 建 Release。
> **状态标记**：`[PROD_NOT_TOUCHED]`（无生产环境触达）。
> **环境**：分支 `task/TAG0051-release-decoupling`，HEAD `c5bda4df`（P5 已提交）。
> **证据**：`P6-evidence/` 下每条 BDD 一个 `.log`（含**实际跑的完整命令 + 输出**，非 1 行充数）；另有 `post-test-residue.log`。
> **自查 ≠ gate**：本报告记录**验收时的事实**；判定权在主 Agent 跑的 gate 脚本（`check-gate.py P6` + `check-p6-evidence.py` + `check-p6-provenance.py`）。

**关键环境口径（影响 BDD-2/3/6/7/16/17/19）**：直接以绝对路径运行**本工作树** `agate/scripts/check-gate.py` 时，
其 `agate_common.resolve_rules_root()` 会按版本解析链（无 `AGATE_ROOT` env → `~/.agate/current`）解析到**已安装稳定版
`~/.agate/v0.81.0`**——该版**无 `level-2.yaml`**，会使 `delivery.method` 枚举校验 no-op。故对"读契约快照"的 BDD
（本轮实测 BDD-16/17）**导出 `AGATE_ROOT=<工作树>/agate`**，使被测对象 = **本工作树的 check-gate.py + 本工作树的
`agate/rules/task-data/*`**（这正是本任务的改动对象）。该口径与 P3 测试一致（conftest 以隔离 HOME 使版本链失败 →
回退脚本路径上溯 → 指向工作树）。BDD-17 证据里附了"不设 AGATE_ROOT 时 rc=2"的对照，证明枚举校验**确由本工作树
`level-2.yaml` 驱动，非真空**。

## 逐条 BDD 验收结果

- PASS BDD-1: P8/READY 语料面（state-machine.md / P8-release.md / state-transitions.md / phases.yaml / dispatch-protocol.md / implementer.md 六处）对「tag 作为 P8 条件/动作」字面（git tag / tag 已创建 / tag 检查 / 先 tag）零命中 (bdd-01.log)
- PASS BDD-2: check-gate.py P8 对「无对应版本 tag」不再告警/拦截（level-1 非 legacy 夹具、本地无 tag ⇒ stderr 无 tag 告警、exit 2） (bdd-02.log)
- PASS BDD-3: check-gate.py P8 不再要求 version 文件变更（未改 version 文件 ⇒ stderr 无 version 变更告警、exit 2） (bdd-03.log)
- PASS BDD-4: READY 前置保留「CHANGELOG [Unreleased] 含本任务条目」（含 task_id ⇒ check-changelog.py exit 0） (bdd-04.log)
- PASS BDD-5: 「CHANGELOG [Unreleased] 缺本任务条目」判失败（check-changelog.py exit 1，BDD-4 反例） (bdd-05.log)
- PASS BDD-6: P8 产出声明 bump_type 意图（含 bump_type ⇒ check-gate.py P8 exit 2） (bdd-06.log)
- PASS BDD-7: P8 产出缺 bump_type 字段时判失败（check-gate.py P8 exit 1，BDD-6 反例） (bdd-07.log)
- PASS BDD-8: 发布编排工作流 release.yml 的 on: 含 workflow_dispatch 人工授权入口（且 push: tags 触发器保留并存） (bdd-08.log)
- PASS BDD-9: 发布门机械校验「目标提交 CI 结论为 success」（非 success 含 pending ⇒ 门非 0；全 success + consistency 0 ⇒ 门 exit 0） (bdd-09.log)
- PASS BDD-10: 发布门不把「PR 口径绿」当作「合并后绿」的等价替代（push-to-main 口径 CI failure ⇒ 门非 0，TAG0050 事故回归锁） (bdd-10.log)
- PASS BDD-11: 发布门校验「tag↔提交一致」（badge / CHANGELOG 版本节；注入反例 ⇒ exit 1，正例 ⇒ exit 0） (bdd-11.log)
- PASS BDD-12: 发布门校验 CHECK 7 与 CHECK 13 均 0 ERROR（consistency 非 0 ⇒ 门非 0；真跑 CHECK 7/13 均 PASS、rc=0） (bdd-12.log)
- PASS BDD-13: 发布门校验 roadmap 关联 RM 条目已 done（关联 RM 非 done ⇒ 门非 0，提示须先回写 done） (bdd-13.log)
- PASS BDD-14: tag 时点在发布文档中全文统一（AGENTS.md 清单 + 「release PR 普通 merge」条 + git-integration.md 一致为「先合 release PR → main CI 绿 → 后打 tag → Release」，无「先 push tag」矛盾副本） (bdd-14.log)
- PASS BDD-15: 发布失败处置显式规定「先评估回退 tag/Release 重打，仅当已被外部消费才出补丁」 (bdd-15.log)
- PASS BDD-16: delivery.method 取值域定死为有限枚举（level-2 夹具 + 合法枚举值 release-notes ⇒ exit 2） (bdd-16.log)
- PASS BDD-17: delivery.method 取枚举外非空值时判失败（level-2 夹具 + definitely-not-in-enum ⇒ exit 1，BDD-16 反例） (bdd-17.log)
- PASS BDD-18: state-machine.md 显式发布授权转移（独立流程 + 人工授权入口 workflow_dispatch），且不引入与既有 PAUSED/NEED_CONFIRM 并行的第二套阻塞确认语义 (bdd-18.log)
- PASS BDD-19: release.preset 声明层消费点与去 tag/version 后 P8 语义一致（无悬空 preset 提示 + check-protocol-consistency.py 0 ERROR） (bdd-19.log)
- PASS BDD-20: legacy 任务行为不变（R6 双向差分：legacy 39 个 / 差异 2 条 / 未匹配 0 条，均 [ALLOWED]；rc 2→2；跑前跑后真实仓库 git status 一致） (bdd-20.log, post-test-residue.log)
- PASS BDD-21: 改 P8 语义时 obligations / anchor / 测试三者同步（M 类占比 56/121 不降；OBL-P8-04 仍为 M 且含 method_enum、落 gate_p8；enforcement/behavior 测试 68 passed） (bdd-21.log)
- PASS BDD-22: 改动 agate/ 协议本体/脚本的提交含独立评审留痕（origin/main..HEAD 内每个协议提交均带可兑现 self-gate-review:；test_tag0051_self_gate.py 绿） (bdd-22.log)
- PASS BDD-23: 发布门三种落点穷尽下 SG.6 与 CHECK9-coverage 判定正确（本任务落支② agate-*.py；SG.6 14 passed、CHECK9-coverage 无 ERROR、无新增 check-*.py ⇒ 零触发） (bdd-23.log)

**Summary**: 23/23 PASS, 0 FAIL — ui_affected: false，prod_touched: false。

## post-test 环境残留检查（强制步骤，结论）

- 已落盘 `Post-test residue` 证据：`post-test-residue.log`。
- 结论：**无残留** —— ① 无已跟踪文件改动 / 无暂存改动；② 账本 `gate-events.jsonl` 未被手写；③ 无长驻进程；
  ④ 新增项仅 `P6-evidence/*` 与 `P6-progress-verifier.md`（+ 主 Agent 的 dispatch 文件），全在任务目录内、非代码/测试/协议文件。
- 一次性临时目录（`/tmp/opencode/tag0051-p6*`，含 R6 corpus 与夹具）由工具自管/本 subagent 夹具，均在仓库外、不被提交。

## 参考（非本 subagent 重跑项，按上游口径）

- P5 全量回归 `1 failed, 2958 passed, 2 skipped`，唯一红 = **预存失败** `test_bdd_43`（本机 opencode CLI 环境漂移，
  非本仓缺陷，见 `known-failures.md`）——本任务 23 条 BDD 的判据**均不含**「全量 pytest 全绿」，故不触发预存失败豁免口径；
  所涉定向测试（obligations/self-gate/SG.6/delivery-contract）本轮**已实跑并全绿**。

<!-- AGATE:RENDER results BEGIN（agate-md-field-set 生成，勿手改） -->
| BDD | 结论 | 证据 |
|---|---|---|
| 1 | PASS | bdd-01.log |
| 2 | PASS | bdd-02.log |
| 3 | PASS | bdd-03.log |
| 4 | PASS | bdd-04.log |
| 5 | PASS | bdd-05.log |
| 6 | PASS | bdd-06.log |
| 7 | PASS | bdd-07.log |
| 8 | PASS | bdd-08.log |
| 9 | PASS | bdd-09.log |
| 10 | PASS | bdd-10.log |
| 11 | PASS | bdd-11.log |
| 12 | PASS | bdd-12.log |
| 13 | PASS | bdd-13.log |
| 14 | PASS | bdd-14.log |
| 15 | PASS | bdd-15.log |
| 16 | PASS | bdd-16.log |
| 17 | PASS | bdd-17.log |
| 18 | PASS | bdd-18.log |
| 19 | PASS | bdd-19.log |
| 20 | PASS | bdd-20.log, post-test-residue.log |
| 21 | PASS | bdd-21.log |
| 22 | PASS | bdd-22.log |
| 23 | PASS | bdd-23.log |
<!-- AGATE:RENDER results END -->
