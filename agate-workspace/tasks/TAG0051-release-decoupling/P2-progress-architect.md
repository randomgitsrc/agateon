
## P2 architect 进度（TAG0051，2026-10-11）

- [读] P2-dispatch-context-architect.md（dispatch_guide 全节）— 7 条关键决策 + 影响面强制节 + 最小验证硬要求
- [读] 角色定义 architect.md（P2 产出规格 + 批次设计 + gate_commands 声明）
- [读] P1-requirements.md（23 条 BDD，9 packages，domains [backend,security]，risk high，全阶段无裁剪）
- [读] P0-brief.md（env_constraints / known_risks / 时效性自检）
- [读] P1-review.md（approved；§五 22 项断言全部独立复现）
- [下一步] 读先例设计件三件（RM-AG0098）+ roadmap RM-AG0103 + P8 现状源文件
- [读] 先例三件：design-release-order-boundary.md（RM-AG0098 分析）/ handoff-release-order-20261003.md（前提更正 + Q1/Q2 + 「P8 是通用协议不应写本仓 GitHub 流程」）
- [读] roadmap RM-AG0103 全文（目标切法①②+配套+锚）；RM-AG0098 done；RM-AG0110/0115 done/backlog；RM-AG0116 done
- [读] .github/workflows/release.yml（tag push 唯一触发器 + Verify tag points to matching commit 步 :33-65）
- [读] P8-release.md（:12 同一 commit+tag；:122/:156 两处 git tag；:99-103 DEBT0013 已消解说明）
- [读] level-1.yaml（delivery 契约 required:[method]/none_requires_reason/non_none_requires_ref；phase_universe）
- [读] agate.config.yaml（verify.commands 四条 + release.preset: semver-changelog-tag）
- [读] check-gate.py::gate_p8（bump_type/debt_check exit1；结构化 delivery :2255-2292；version WARNING :2317-2337；CHANGELOG WARNING :2339-2356；config 迁移期 :2358-2374；tag WARNING :2376-2389；RM-AG0043 反查 :2294-2315）
- [读] state-machine.md :165 P8→READY 转移 + :177 READY 收尾（git tag 已创建）；state-transitions.md :54 P8→READY（git tag 创建）
- [读] phases.yaml P8（:167 gates 含 version/CHANGELOG/tag；:169 DEBT0013；:171 task_fields [bump_type]）
- [读] obligations.yaml OBL-P8-01..14（:717-828，anchor 分布）
- [读] AGENTS.md :185-210（发布清单 6 步 + G-5 + release PR 普通 merge）
- [读] LEVEL-1 delivery 契约 + config release.preset
- [读] check-changelog.py（exit0/1 契约，CHECK_CHANGELOG_MODE post-bump）
- [读] check-protocol-consistency.py CHECK9 anchors/coverage/GATE_SCRIPT_EXEMPT；CHECK10；CHECK13；README「新增脚本登记面」
- [读] agate-release.py 子命令（boundary/pyyaml-pin/notes/is-prerelease/build）
- [读] dispatch-protocol.md :881 P8→READY；implementer.md :101；git-integration.md :185-190
- [最小验证] 只读 gh api：check-runs（name/status/conclusion，total=11）、actions/runs?head_sha、combined status(=pending,0)、branch protection（6 required contexts, strict）、workflow list → 全部 confirmed；deploy-pages.yml 证实 push+workflow_dispatch 并存
- [写] P2-design.md 产出：影响面三部分(在候选前) + 3 候选(发布门落点主轴) + 7 条关键决策 + 7 批 dispatch_plan + 四字段 + files_to_read/env_constraints/minimal_validation + 23 BDD 映射
- [工具] agate-md-field-set 写 header+机器字段(OK)；gate_commands 经 agate-md-field-set-gate-commands.py 写(OK)
- [缺口上报] ① dispatch_plan 被 agate-md-field-set 拒写(超 DEBT0067 面)；② 卡允许的 batches[].output 因 check-frontmatter MAX_DEPTH=3 写不进(二者矛盾，建议独立 DEBT)——均如实登记未静默绕过
- [自检] check-frontmatter rc=0；gate P2 reconcile 0 mismatches(仅缺 P2-review.md=评审 subagent 产出)；候选 3==candidate_count；影响面在候选前；四字段齐
- [隔离] 真实仓库 git status --porcelain 仅 3 个未跟踪任务文件；agate/ 零改动；[PROD_NOT_TOUCHED]

## 修复轮（retry 1，2026-10-11）—— 修 B1 + NB-1..5（候选/决策不变）

- [读] P2-review.md（plan-eng-review，rejected：1 BLOCKER=B1）；P2-dispatch-context-architect-retry1.md（增量指引）
- [读] obligations.yaml baseline（m:56 / total:121；reset.to=56/121）；OBL-P8-01..14（:717-828）逐条 statement/disposition/anchor/enforced_at/test
- [读] check-obligations.py（_evaluate :320 整数交叉相乘，:236-245 _effective_baseline reset 优先）；_reachable_set 实证 check-gate.py::gate_p8 在必经路径
- [读] check-gate.py gate_p8：version 2317-2337 / CHANGELOG 2339-2356 / 迁移期 2358-2374 / tag 2376-2389；pre-commit-gate.py:1086 P8 调 check-changelog.py（WARNING-only）
- [读] check-frontmatter.py MAX_DEPTH=3；LEVELS.yaml/level-1.yaml；CHECK16 check_task_data_snapshot_freeze（:1498-1502 未登记→ERROR）；r6-differential.sh 接口（--corpus 须为含 .git 整仓，corpus/agate-workspace/tasks 被读）
- [读] M_IDS（test_tag0050_obligations_enforcement.py :61 附近含 OBL-P8-04）；fixtures/task-data/level-1/{pass,fail}/gate-events.jsonl（task_created.contract_level）
- [实测·B1 独立复现] /tmp/opencode 一次性副本跑 check-obligations.py 四路径：基线 56/121 OK(0)；①删条目 55/120 FAIL(1)；②M→C 55/121 FAIL(1)；③scope:protocol-repo 55/120 FAIL(1)；④就地重挂 56/121 OK(0)。跑前后真实仓库 git status --porcelain 一致
- [改] §1.1 M1（+删 CHANGELOG diff WARNING 块 :2339-2356，NB-2）；M6 扩为「OBL-P8-* 十四条逐条」；M7（M_IDS 保持 + 新增 BDD-21 机械断言）
- [改] 新增 §1.1.1（十四条逐条结论表 + M 计数四路径实测表；定死④重挂、不写 baseline.reset）
- [改] §1.2 NB-1（release.preset 无任何消费方 + DEBT0069）+ NB-4（WORKFLOW.md/orchestrator-template.md/assets/templates 点名 Not-Modify）
- [改] §1.3 R9（DEBT0069）+ R11（NB-5 跨项目破坏半径）+ R12（level-2 与 LEVELS 同批，CHECK16）
- [改] §1.4（NB-3 wrapper 零登记面）；§3 决策5（NB-2 定死删）+ 决策6（NB-1）+ 决策7（7→8 批）+ 新增决策8（NB-3 wrapper）
- [改] §4（8 批；obligations-sync 能力改述；新增 r6-harness 批）；frontmatter dispatch_plan（parallel_limit 8 + r6-harness）
- [改] §5 P5_r6 改调 wrapper `docs/design-notes/r6-differential-prepare.sh`（NB-3）；§6 files_to_read（+wrapper）；§7 isolation_check
- [改] §9 完成标准 7/7a/8 + BDD 表（4/5/16-17/20/21）+ 新增 §9.1（P3 level-2 fixture 来源与构造）
- [自检] check-frontmatter rc=0；agate-md-field-get dispatch_plan=合法 JSON（8 批≤8）；check-gate P2 reconcile 0 mismatches，唯一 FAIL=P2-review.md 仍 rejected（待复评）
- [自检] consistency 0 ERROR / 440 WARNING（无因本次引用新增的告警）；真实仓库 agate//docs/ 零改动
- [隔离] 真实仓库 git status --porcelain 与开跑前一致（仅 9 项任务/债务文件）；[PROD_NOT_TOUCHED]
