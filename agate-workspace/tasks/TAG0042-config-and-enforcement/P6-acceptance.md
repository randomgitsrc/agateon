---
phase: P6
task_id: TAG0042
type: acceptance
parent: P5-verification.md
trace_id: TAG0042-P6-20261006
status: draft
created: 2026-10-06
agent: verifier
# ── v2.0 机器汇总 ──
pass: 22
fail: 0
ui_affected: false
p5_evidence_reuse: false
---

# P6 验收报告 — TAG0042 项目形态命令化 + 规则脚本化

> 验收对象：HEAD `d3c3300`（P5 已落）；协议版本 v0.78.3（`AGATE_ROOT=/home/kity/.agate/v0.78.3/agate`）。
> 验收依据：`P1-requirements.md` 全部 **22 条 BDD**（功能任务口径，逐条实跑/实读）。
> 验证方式：每条 BDD 先实跑/实读拿到客观输出，再写 PASS/FAIL；证据落 `P6-evidence/`。
> `p5_evidence_reuse: false`（保守，不声明复用 P5 证据；BDD-22 独立实跑全量 pytest）。

`[PROD_NOT_TOUCHED]` —— 全程仅只读代码/协议文件 + 在 pytest `tmp_path`/`git_repo` 隔离环境实跑 + 写本任务 P6 产出；未触达任何生产环境/服务/数据库。

## BDD 逐条对照

- PASS BDD-01: agate-next 推进时不预写下一阶段——`test_bdd_1_advance_does_not_prewrite_next_phase_into_state_yaml` + `test_bdd_1_advance_does_not_git_add_state_yaml` 两用例 PASSED（phase 保持 P5、暂存区不含 .state.yaml）(P6-evidence/bdd-01-02-phase-semantics.txt)
- PASS BDD-02: phase 语义与卡片/文档表述一致——`test_bdd_2_*` 4 用例 PASSED，且 5 权威文档（state-machine/dispatch-protocol/CONTEXT/loop-orchestration/orchestrator-template）各含「不预写」表述、agate-next.py 无预写行为代码 (P6-evidence/bdd-01-02-phase-semantics.txt, P6-evidence/bdd-02-phase-semantics-docs.txt)
- PASS BDD-03: 声明描述形态不写死技术栈——`test_bdd_3_*` 3 用例 PASSED（init 生成声明、get 读回 go/go-mod 声明值、读取路径无 md/agateon/pytest 硬编码）(P6-evidence/bdd-03-04-07-08-agate-config.txt)
- PASS BDD-04: agate-config 子命令读写+退出码——`test_bdd_4_*` 3 用例 PASSED（get/list/show 输出客观值 rc=0；不存在字段 rc≠0）(P6-evidence/bdd-03-04-07-08-agate-config.txt)
- PASS BDD-05: schema 校验拒绝非法形态——`test_bdd_5_*` 4 用例 PASSED（schema 存在且与既有 4 schema 同构；非法枚举/未知字段 rc≠0 并指出字段值；合法声明 rc=0）(P6-evidence/bdd-05-06-20-config-schema.txt)
- PASS BDD-06: 唯一读取函数保证单源——`test_bdd_6_*` 5 用例 PASSED（read_project_config 存在/返回声明值/非法 YAML 优雅降级/CLI 与库取值同源/无第二处解析）(P6-evidence/bdd-05-06-20-config-schema.txt)
- PASS BDD-07: setup/install-hook 自动 init 幂等——`test_bdd_7_*` 3 用例 PASSED（install-hook 自动生成声明、既有声明不被覆盖、agate-setup 引用 agate-config init）(P6-evidence/bdd-03-04-07-08-agate-config.txt)
- PASS BDD-08: 声明缺失行为不变 + WARNING——`test_bdd_8_*` 3 用例 PASSED（gate_p0 缺声明仍 return 2 且输出含声明文件名的 WARNING；UPGRADING 记载 exit 1 截止版本）(P6-evidence/bdd-03-04-07-08-agate-config.txt)
- PASS BDD-09: agate-run 执行 + 退出码传播(pipefail)——`test_bdd_9_*` 4 用例 PASSED（成功 rc=0、失败 rc=7 如实传播、POSIX pipefail 左侧失败 rc≠0、源码含平台分支 + WARNING）(P6-evidence/bdd-09-10-11-agate-run.txt)
- PASS BDD-10: agate-run 基线证据逐字节——`test_bdd_10_*` 4 用例 PASSED（--baseline 落盘 .out、一致无 diff rc=0、偏离基线 rc≠0 报 diff、证据逐字节等于命令输出）(P6-evidence/bdd-09-10-11-agate-run.txt)
- PASS BDD-11: 证据文件被 ignore 覆盖——`test_bdd_11_*` 2 用例 PASSED（.gitignore 覆盖时 git check-ignore 命中；未覆盖时 rc≠0 报错）(P6-evidence/bdd-09-10-11-agate-run.txt)
- PASS BDD-12: cmd_run 事件不破哈希链 + hook 暂存——`test_bdd_12_*` 6 用例 PASSED（追加 cmd_run 事件含命令/退出码/时间戳、check-events 链连续 exit 0、经 append_event 单写路径、hook 一并 git add 账本）(P6-evidence/bdd-12-events-ledger.txt)
- PASS BDD-13: check-obligations 登记面（SG.6 转绿）——`test_sg_6_check9_anchor_table_covers_all_gate_scripts` PASSED（1 passed, 12 deselected）(P6-evidence/bdd-13-sg6.txt)
- PASS BDD-14: 关卡层按提交类型分级（含 paused_from）——`test_bdd_14_*` 2 用例 PASSED，且 phases.yaml 实读含 gate_layer.commit_types（code-only/docs-only/release 三集合且不同）+ transitions.pause.paused_from，gate_pass_exit 语义不变 (P6-evidence/bdd-14-21-gate-layer.txt, P6-evidence/bdd-14-gate-layer-data.txt)
- PASS BDD-15: P8 交付收尾 + delivery 拦截——`test_bdd_15_*` 3 用例 PASSED（delivery 未声明 gate 拦截非 0、声明后放行 rc=2、phases.yaml P8 name=交付收尾 + 卡片记载 delivery）(P6-evidence/bdd-15-p8-delivery.txt, P6-evidence/bdd-15-p8-semantics-data.txt)
- PASS BDD-16: agate-ci-verify 替换 backstop 无假绿——`test_bdd_16_*` 6 用例 PASSED（脚本存在、gate 失败如实 FAIL 非 0、无适用场景显式 SKIP+原因、源码重跑 check-gate、workflow 改调新脚本、协议引用已同步）(P6-evidence/bdd-16-ci-verify.txt)
- PASS BDD-17: agate-doctor 诊断 + 修复指引——`test_bdd_17_*` 8 用例 PASSED（输出声明/hook/版本解析/账本完整性维度 + 修复指引，成功退出码固定 0，已接入项目报存在）(P6-evidence/bdd-17-doctor.txt)
- PASS BDD-18: obligations.yaml 每项三态归宿、无「无归宿」——check-obligations.py exit 0（CHECK-OBLIGATIONS: OK），结构实读 123 项归宿 M=60/C=33/R=30、无归宿项 0、缺 anchor/statement 0 (P6-evidence/bdd-18-19-obligations.txt)
- PASS BDD-19: M 类占比不下降——check-obligations.py 实跑 60/123=0.4878 ≥ 基线 60/123=0.4878（只增不减判定通过）(P6-evidence/bdd-18-19-obligations.txt)
- PASS BDD-20: 不引入只适用单一项目的规则——`test_bdd_20_*` 2 用例 PASSED（read_project_config 函数体无单项目 token；go/python 两形态均按声明返回），通用性实读 agate-config.py 与 read_project_config 中 agateon/peekview/pytest 各 0 命中 (P6-evidence/bdd-05-06-20-config-schema.txt, P6-evidence/bdd-20-genericity-read.txt)
- PASS BDD-21: 删发版逻辑前先提供等价 preset——`test_bdd_21_*` 3 用例 PASSED（semver-changelog-tag 可 validate rc=0、发版痕迹缺声明时 P8 gate 给显眼 WARNING、UPGRADING 记载迁移方式与截止版本 v0.80.0）(P6-evidence/bdd-14-21-gate-layer.txt, P6-evidence/bdd-21-preset-migration.txt)
- PASS BDD-22: 每批不回退（协议语义）——全量 pytest 2668 passed / 1 预存失败（test_bdd_43，非本任务 BDD）/ 2 skipped，与 P5 基线逐字一致、新增回归失败 0；consistency --strict-errors-only 0 ERROR；6 批 P4 commit 均含 self-gate-review 留痕 (P6-evidence/bdd-22-full-regression.txt, P6-evidence/bdd-22-commits-and-consistency.txt, P6-evidence/bdd-22-consistency.txt)

**Summary**: 22/22 PASS, 0 FAIL

## 观察（非 FAIL，不阻断）

- **预存失败**：`test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent` 因外部 opencode CLI 把 `debug agent` 改为 `debug agents` 而失败（实测 `Unknown subcommand "agent"`），与本次改动无关，已登记 `known-failures.md`；**不是本任务 BDD**，未计入任何 BDD 行。全量 pytest 结果（2668 passed / 1 failed / 2 skipped）与 P5 基线逐字一致 ⇒ 无新增回归。
- **BDD-18 条目数口径**：外部审计的「160 项逐条清单」不在仓库（P1 §2 隐含需求 1 / P4-implementation-batch6.md 已登记），P4 按 P0-brief fallback 从协议本体重新盘点得 **123 项**（M60/C33/R30）。BDD-18 的 Then（每项有明确三态归宿、无「无归宿」项）已满足；123 vs 160 的差异属已登记的 `[DESIGN_GAP]`（batch6），交 P7 裁决，不影响本 BDD 判定。
- **post-test 环境残留检查**：本任务验收测试全部使用 pytest `tmp_path` / `git_repo` fixture，无创建型外部资源（无数据库/服务/端口），不产生环境残留；实跑前后仓库工作区无代码改动（仅本任务元数据 + P6 产出）。
- **consistency WARNING 408 条**全部来自冻结文件（tasks/、reviews/、CHANGELOG 等按设计不改），`--strict-errors-only` 判据下 0 ERROR。

## 交叉核对

- P1-requirements.md 的 `#### BDD-NN:` 标题数 = 22；本报告 PASS+FAIL 行数 = 22（1:1 全覆盖，无遗漏/无重复）。
- 证据文件数 = 19，全部被 PASS 行引用。
