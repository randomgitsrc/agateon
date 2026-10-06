## P3 progress (batch1-phase-semantics)

- read P3-dispatch-context-test-designer.md: batch1 covers BDD-1/BDD-2 only
- read test-designer role + P0-brief: TDD red tests, platform scan 0 hits, tmp_path isolation
- read P1-requirements.md: BDD-1 (agate-next 不预写), BDD-2 (phase 语义与卡片一致)
- read P2-design.md: §6.1b batch1 output = agate-next.py, phase-cards/P2-design.md, phase-cards/P8-release.md, UPGRADING.md
- read agate/tests/README.md: unit/ layout, test files map, platform-agnostic rules
- read agate-next.py: _advance() at L198-210 does state['phase']=target + _write_state + git add (预写行为确认)
- read test_agate_next_card.py + test_tag0027_b1_agate_next_cli.py: existing patterns (run_cli, _read_state_phase, _ledger_events)
- read conftest.py: fixtures agate_root/agate_scripts/task_dir/git_repo/python_exe/run_cli
- read phase-cards/P2-design.md L14 '不要提前写 P3' + P8-release.md L15-20 phase semantics present
- read UPGRADING.md:1209 '⑥ 阶段卡片 phase 语义（文档，无强制）' — batch1 目标改述
- read test_check_state_transition.py head: run_cli + git_repo + _write_state patterns

### Design for batch1 BDD-1 / BDD-2 red tests
- BDD-1: agate-next 推进不预写下一阶段 + 不 git add .state.yaml（现行为 L204-208 预写+add）
- BDD-2: 全仓无「预写下一阶段」行为代码 + 卡片表述与 phase=本commit产出阶段 一致

### 落盘完成
- 测试代码：agate/tests/unit/test_tag0042_batch1_phase_semantics.py（6 用例：BDD-1 ×2 + BDD-2 ×4）
- 用例清单：agate-workspace/tasks/TAG0042-config-and-enforcement/P3-test-cases-batch1.md（test_code_dir: agate/tests/unit/）
- 自跑：6 failed in 0.34s，全部 AssertionError（B 类真红灯，行为未改）
- 平台扫描：check-platform-assumptions.py <测试文件> → exit 0（0 命中）
- frontmatter：phase=P3 / task_id=TAG0042 / parent=P2-design.md / trace_id=TAG0042-P3-20261005 / agent=test-designer

## P3 progress (batch2-agate-config)
- read P3-dispatch-context-test-designer-batch2.md: covers BDD-3..8 + BDD-20(batch2面); output test_agate_config.py + test_config_schema.py
- read test-designer role: TDD red, BDD 1:1, platform scan 0 hits, tmp_path isolation
- read P0-brief: batch2 = agate-config 全部子命令 + schema + 唯一读取函数 + setup/install-hook 自动 init + gate_p0 validate（迁移期只 WARNING）
- read P1-requirements.md: BDD-3 (声明描述形态不写死技术栈) / BDD-4 (子命令读写+退出码) / BDD-5 (schema 校验) / BDD-6 (唯一读取函数) / BDD-7 (setup/install-hook 自动 init 幂等) / BDD-8 (文件缺失行为不变+WARNING) / BDD-20 (不引入单项目规则)
- read P2-design.md: §4.1 agate-config 子命令 init/validate/get/list/show; read_project_config() 唯一读取函数; gate_p0 恒 return 2 + WARNING; schema rules/schema/project-config.schema.json; batch2 output files
- read agate/tests/README.md: unit layout, test map, platform rules
- read conftest.py: fixtures agate_root/agate_scripts/task_dir/git_repo/python_exe/run_cli/_run_cli_impl/HOME isolation
- read test_tag0042_batch1_phase_semantics.py: batch1 red test style (importlib load, _TMP="/"+"tmp", run_cli)
- read check-gate.py gate_p0 (L631-637 现状恒 return 2); agate-setup.py + install-hook.py CLI shapes

### batch2 test design (BDD-3..8 + BDD-20)
- BDD-3: 声明文件 agate.config.yaml 生成 + 值来自声明，无硬编码技术栈（agate-config init/get）
- BDD-4: agate-config {get,list,show,validate} 退出码语义（0成功/非0失败）
- BDD-5: schema 校验拒绝非法字段/枚举，合法返回0（project-config.schema.json）
- BDD-6: read_project_config() 唯一读取函数，两处取值同源等价守护
- BDD-7: agate-setup/install-hook 自动 init，幂等不覆盖
- BDD-8: 文件缺失时 gate_p0 仍 return 2 + WARNING；UPGRADING 记截止版本
- BDD-20(批2面): read_project_config/agate-config 读取路径不硬编码单一项目名/技术栈
- 测试文件: agate/tests/unit/test_agate_config.py (BDD-3/4/7/8) + test_config_schema.py (BDD-5/6/20)

### batch2 落盘完成
- 测试代码：agate/tests/unit/test_agate_config.py（BDD-3×3 / BDD-4×3 / BDD-7×3 / BDD-8×3 = 12 用例）
- 测试代码：agate/tests/unit/test_config_schema.py（BDD-5×4 / BDD-6×4 / BDD-20×2 = 10 用例）
- 用例清单：P3-test-cases-batch2.md（test_code_dir: agate/tests/unit/，frontmatter 已填 phase/task_id/parent/trace_id）
- 自跑：22 failed in 0.46s，全部 AssertionError(38)/AttributeError(6)（B 类真红灯：agate-config.py 不存在 / read_project_config 不存在 / schema 缺失 / gate_p0 无 WARNING / setup-install-hook 不 init）
- 平台扫描：check-platform-assumptions.py 两文件 → exit 0（0 命中；曾命中 R4 注释 /tmp 字面量，已改为「临时目录副本」）
- 无仓库内已提交文件写入（全在 tmp_path/git_repo）；gate-events.jsonl 的 M 来自 12:03 P2 commit 流程，非本批
- 说明：P3 gate 找 P3-test-cases.md（无 suffix）；本批按 dispatch-context 硬约束只产出 P3-test-cases-batch2.md（同 batch1 模式），汇总成 P3-test-cases.md 由主 Agent 承担（派发卡「按包拆分并行」步 4）
- 自检完成：文件全部落盘，22 用例全红（B 类），平台扫描 0 命中，无仓库已提交文件写入

### batch2 修订轮（测试隔离缺陷修复）
- 缺陷：调用 agate-setup/install-hook 的用例经 agate_common.record_project() 写 <agate_home()>/installed-projects.json；台账落真实仓库根（未跟踪污染）
- 根因：原 test_bdd_7_setup_scope_project* 显式传 AGATE_HOME=<repo root>（agate_root.parent）→ 台账落仓库根
- 修复：新增 _isolated_agate_env(tmp_path, agate_root) → AGATE_HOME 钉到 tmp_path/isolated-agate-home；AGATE_ROOT 钉协议根
  · test_bdd_7_install_hook_auto_inits_declaration / test_bdd_7_install_hook_init_is_idempotent 每次 run_cli 均传该 env
  · 已删除显式指向仓库根的 setup 用例（改为源码级 test_bdd_7_setup_source_invokes_config_init，无 subprocess，无写副作用）
- 实证：台账现落 /tmp/pytest-*/test_bdd_7_*/isolated-agate-home/installed-projects.json；仓库根 installed-projects.json 不再出现（rm -f 清理残留，未 commit）
- 复跑：22 failed in 0.42s（全 B 类）；git status 无 installed-projects.json
- 平台扫描：my 2 files + agate/tests/unit/ → exit 0（0 命中）
## batch3-agate-run — test-designer 进度
- [x] 读 dispatch-context-test-designer-batch3.md（BDD-9..12；产出 test_agate_run.py + test_events_ledger.py；tmp_path 隔离账本）
- [x] 读 test-designer.md 角色定义（BDD 1:1 映射；平台假设扫描 0 命中；红灯 B 类）
- [x] 读 P1-requirements.md（BDD-9..12 全部 4 条已提取）
- [x] 读 P2-design.md（§4.2 执行层设计；cmd_run schema；hook 暂存账本；平台分支）
- [x] 读 P0-brief.md + AGENTS.md + tests/README 约定
- [x] 读既有实现对象：agate_common.py（append_event/GENESIS_HASH/run_test_with_formatter 的 pipefail 写法）、check-events.py、pre-commit-gate.py 行为
- [x] 读 batch2 既有测试范式（test_agate_config.py）与 P3-test-cases-batch2.md 格式
- [x] 确认 fixtures：task_dir/git_repo/run_cli/python_exe/agate_scripts/agate_root
- [x] 写测试代码 test_agate_run.py (BDD-9/10/11) + test_events_ledger.py (BDD-12)
- [x] 写 P3-test-cases-batch3.md（15 用例 1:1 映射 + test_code_dir）
- [x] 自跑确认红灯 15/15 failed（B 类）；平台假设扫描 exit 0（0 命中）
- [x] git status 确认仓库根无新增污染文件
- [x] frontmatter 字段已填（phase/task_id/parent/trace_id/agent）

## batch4-gate-layer（P3 test-designer subagent）
- 产出：P3-test-cases-batch4.md + agate/tests/unit/test_gate_layer.py + agate/tests/unit/test_check_p8_delivery.py
- 8 用例（BDD-14 ×2 / BDD-15 ×3 / BDD-21 ×3），自跑 8 failed（B 类）；平台假设扫描 0 命中
- DESIGN_GAP：TC-B14-01（转换表键名无关断言）/ TC-B15-03（P8 名称措辞）/ TC-B21-03（WARNING 消费入口与措辞）
