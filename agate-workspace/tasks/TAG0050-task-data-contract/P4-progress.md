
## P4 A1 implementer 进度

- [x] 读 dispatch-context（15 项交付物清单 + 完成判据）
- [x] 读 implementer.md 角色定义
- [x] 读 design-tag0050-task-data-contract.md（§0-§14）
- [x] 读 P2-design.md（§1/§3/§3.1-3.3/§6/§7/§10）
- [x] 读 test_tag0050_a0_a1_ledger.py（BDD-03..22）+ helpers_tag0050.py
- [x] 读 P1-requirements.md（BDD-03..22）+ P3-test-cases.md + P0-brief.md
- [ ] 读 P2 files_to_read 列出的代码文件

### A1 实现进度（续）

- 读代码文件（P2 files_to_read）：agate_common / check-events / pre-commit-gate / check-gate / check-state-transition / agate-next / check-state-yaml / agate-state-yaml-check / check-protocol-consistency / check-p6-evidence / conftest
- 新增快照：LEVELS.yaml + level-1.yaml + 黄金 fixture（pass/fail）
- 新增 agate-task-init.py（新建/--existing/--adopt/--upgrade）
- agate_common 新增契约函数；is_new_task_for_evidence_ref 改依契约
- check-events 调 check_ledger_events
- pre-commit-gate 新增「账本与新目录」步骤 + 全局面 PROD_TOUCHED + _judge_enabled 依契约
- check-gate gate_p1/gate_p65 依契约；check-state-transition legacy 重开 ERROR
- agate-state-yaml-check ID 正则统一
- check-protocol-consistency 新增 CHECK 16 快照冻结
- conftest 新增 init_task()
- R6 差分脚本 + allowlist（负向用例实测变红）
- 既有测试按设计 §8 例外更新（pre-commit hook / dispatch-context warning / state-yaml ID 正则）
- 自查：BDD-03..22 全绿（24 passed）；pre-commit 61 passed；migrate 9 passed；consistency 0 ERROR；ruff clean
- [PROD_NOT_TOUCHED]

### A1-fix（SELF-GATE 整改 F1–F7）进度

- F1：agate-next.py `_p6_judge_advance` 改调 requirement_active（None 回退 judge.enabled）
- F2：pre-commit 规则 7 后半 `_rerun_gates_for_staged_outputs` 实现；IT_PHASE_SPAN.1/2/4 按设计 §8 例外改回 legacy
- F3：`_level_registration_errors` 只校验已登记；「=当前等级」移至 pre-commit 新建目录分支（规则 2）
- F4：WORKFLOW.md 新增 1.1 行 + 更新多任务适配段
- F5：SELF-GATE.md 两处 CHECK 1-15 → 1-16
- F6：P4-implementation.md §2/§3/§6 声称与数字按实跑修正
- F7：BDD-19 重写（经 pre-commit hook）+ 新增 F1/F3 用例（target 文件 26 passed）
- A1-4：PROD_TOUCHED 扫描面「全部暂存文件」有意偏离已登记
- A5：state-machine.md 同步 legacy 重开 ERROR
- A4-R6：r6-differential.sh 纳入 READY/DONE（实测 legacy 39 个，差异 0，exit 0）
- 自查：target 26 passed / pre-commit 61 passed / 全量 40 failed 2713 passed 2 skipped / consistency 0 ERROR 410 WARNING / ruff clean / shellcheck clean
- [PROD_NOT_TOUCHED]

## [C8-A1-fix] 2026-10-07 起手
- 已读 implementer.md + dispatch-context（A1-cso-fix）+ P0-brief + P4-review-cso.md
- 目标：G1(规则4 rename 洞,BLOCKER) / G2(R6 pre-commit 面) / G3(git rm .state.yaml 绕过全局面扫描)
- 环境隔离：本机工作目录即开发 checkout，未接触生产 → [PROD_NOT_TOUCHED]
- 读完 cso 评审 + 设计 §2.3 规则 4/§8 第 12 项 + r6-differential.sh/allowlist + 测试与 helpers
- 判定：G1 用「源任务目录在暂存后索引中是否已不存在」判目录级改名（稳健，不依赖 rename 检测）；G3 改全局面扫描跳过条件（删除态不跳过）；G2 选 (b) 显式声明只承诺 check-gate 面

## [C8-A1-fix] 完成
- G1：pre-commit-gate.py 规则 4 处理 R（改名）——仅整目录改名豁免（`_is_task_dir_rename`/`_dir_moved_away`，基于索引判据）；新增 BDD-23/24/25。
- G3：`_scan_prod_touched_and_rerun` 跳过条件收紧为「暂存且工作区存在」；新增 BDD-26。
- G2：选 (b) 显式声明 A1 的 R6 只承诺 check-gate 面；§8 补记 + r6-allowlist 可达性声明；`_rule_matches` 补 task_scope；F-5 运行后自核验。
- 复验：新负向用例整改前实测变红（BDD-23/24/26 + BDD-25 去豁免变红），整改后 30 passed。
- 自查：consistency 0 ERROR/410 WARNING；R6 正/负向（0 差异 / 脏 corpus rc=1 / 缺 D12 rc=1）；ruff 通过；platform-assumptions rc=0。
- [PROD_NOT_TOUCHED] 全程仅本 checkout + /tmp/opencode 副本 + pytest tmp_path。
