# agate 协议自检套件

> **这是给协议 maintainer 的测试套件**。普通用户用 agate 完成自己的任务时不需要管这里。

## 快速开始

```bash
# 安装依赖
pip install pytest pyyaml     # 测试框架 + gate 依赖（shellcheck 可选，仅 3 个 hook 薄壳）
sudo apt-get install shellcheck

# 跑全部测试
python3 -m pytest agate/tests/unit/         # 单元测试
python3 -m pytest agate/tests/regression/   # 回归测试
python3 -m pytest agate/tests/integration/  # 集成测试
python3 -m pytest agate/tests/test_sanity.py  # 框架自检

# 一次性全跑
python3 -m pytest agate/tests/

# 并行跑（推荐，16 核实测约 3.5x 提速；需 pip install pytest-xdist）
python3 -m pytest agate/tests/ -n auto
```

**并行安全性**：套件按隔离设计——用例一律 `tmp_path` + HOME/USERPROFILE 重定向 +
`AGATE_REPO_URL` 指本地临时 repo，session 级 fixture 只读，无共享可变状态，
`-n auto` 可放心用。CI 自 2026-08-25 起即 `-n auto` + `--reruns 1`（Linux 全量），
本机复现 CI 口径：`python3 -m pytest agate/tests/ --reruns 1 -n auto`。

## 覆盖度

```bash
# 自动生成（pytest --collect-only 收集计数）
bash agate/tests/scripts/count-tests.sh
```

| 脚本 | 测试文件 | 用例数 |
|------|---------|-------|
| check-pruning.py | unit/test_check_pruning.py | 29 |
| agate-risk-score.py | unit/test_agate_risk_score.py | 11 |
| check-routing.py | unit/test_check_routing.py | 13 |
| ceremony 文档条文（TAG0019）| unit/test_docs_assertions.py | 4 |
| check-gate.py | unit/test_check_gate.py | 144 |
| check-gate.py 集成锚点 | unit/test_check_gate_p1_review.py | 9 |
| check-gate.py P5 命令 diff | unit/test_check_gate_p5_diff.py | 13 |
| agate-next-card.py | unit/test_agate_next_card.py | 22 |
| agate-render-dispatch-prompt.py | unit/test_agate_render_dispatch_prompt.py | 20 |
| check-p6-evidence.py | unit/test_check_p6_evidence.py | 45 |
| check-p6-format.py | unit/test_check_p6_format.py | 16 |
| check-p6-provenance.py | unit/test_check_p6_provenance.py | 40 |
| check-p6-provenance.py | unit/test_review_role_docs.py（UI/UX 机制文档条文，TAG0006）| 14 |
| check-scope-resolved.py | unit/test_check_scope_resolved.py | 10 |
| check-frontmatter.py | unit/test_check_frontmatter.py | 14 |
| check-state-yaml.py | unit/test_check_state_yaml.py | 9 |
| check-state-transition.py | unit/test_check_state_transition.py | 30 |
| check-changelog.py | unit/test_check_changelog.py | 8 |
| check-retrospective.py | unit/test_check_retrospective.py | 15 |
| agate-feedback.py | unit/test_agate_feedback.py | 7 |
| 复盘协议文档条文 | unit/test_retrospective_protocol_docs.py | 13 |
| check-tdd-red.py | unit/test_check_tdd_red.py | 43 |
| formatters | unit/test_check_tdd_red_formatter.py | 13 |
| ci-gate-backstop.py | unit/test_ci_gate_backstop.py | 11 |
| agate-json-get.py | unit/test_agate_json_get.py | 8 |
| agate-read-p5-commands.py | unit/test_agate_read_p5_commands.py | 4 |
| agate-state-get.py | unit/test_agate_state_get.py | 6 |
| agate-retreat-state.py | unit/test_agate_retreat_state.py | 4 |
| agate-md-field-get.py | unit/test_agate_md_field_get.py | 16 |
| dispatch_plan 编排字段契约 | unit/test_dispatch_orchestration.py | 10 |
| agate-state-yaml-check.py | unit/test_agate_state_yaml_check.py | 3 |
| agate-changelog-unreleased.py | unit/test_agate_changelog_unreleased.py | 2 |
| agate-card-inject.py | unit/test_agate_card_inject.py | 2 |
| agate-vision-blocker.py | unit/test_agate_vision_blocker.py | 2 |
| agate-evidence-consistency.py | unit/test_agate_evidence_consistency.py | 2 |
| agate-image-check.py | unit/test_agate_image_check.py | 4 |
| agate-gate-missing-cmds.py | unit/test_agate_gate_missing_cmds.py | 2 |
| agate-gate-p5-count.py | unit/test_agate_gate_p5_count.py | 3 |
| agate-extract-context.py | unit/test_agate_extract_context.py | 16 |
| agate-migrate-workspace.py | unit/test_agate_migrate_workspace.py | 9 |
| agate-retreat-to.py | unit/test_agate_retreat_to.py | 5 |
| agate-archive-stale-outputs.py | unit/test_agate_archive_stale_outputs.py | 7 |
| agate-capture-env-baseline.py | unit/test_agate_capture_env_baseline.py | 15 |
| agate-debt-check.py | unit/test_agate_debt_check.py | 21 |
| agate-scripts-encoding.py（守卫）| unit/test_agate_scripts_encoding.py | 2 |
| agate-workspace-resolve.py | unit/test_agate_workspace_resolve.py | 10 |
| dispatch-context warning | unit/test_dispatch_context_warning.py | 1 |
| 测试 helper（PYTHON 探测）| unit/test_helpers_python.py | 3 |
| check-platform-assumptions.py | agate/tests/scripts/test_check_platform_assumptions.py | 16 |
| check-mvwu.py（MVWU 观测器）| unit/test_check_mvwu.py | 111 |
| MVWU 协议文档断言（TAG0036）| unit/test_mvwu_protocol_docs.py | 65 |
| 文档/CI 断言（shellcheck/ruff/matrix）| unit/test_env_adapt_docs.py | 9 |
| DSH 平台模板结构（TAG0018）| unit/test_dsh_preset.py | 8 |
| 回归 (R1-R5) | regression/ | 17 |
| commit-msg-self-gate | unit/test_commit_msg_self_gate.py | 4 |
| commit-msg-self-gate（集成）| integration/test_commit_msg_self_gate_integration.py | 6 |
| pre-commit-hook | integration/test_pre_commit_hook.py | 48 |
| dispatch-context card | integration/test_dispatch_context_card.py | 8 |
| pre-push-hook | integration/test_pre_push_hook.py | 4 |
| install-hook | unit/test_install_hook.py | 6 |
| 协议一致性 | integration/test_consistency.py | 11 |
| self-gate | integration/test_protocol_alignment_review.py | 8 |
| 框架自检 | test_sanity.py | 6 |
| **总计** | | **以 `count-tests.sh` 输出为准** |

> 注：迁移基线为 TAG0011 的 749 用例（BDD-1，`--collect-only` 口径）。`count-tests.sh` 统计全树 pytest 用例（unit/regression/integration/sanity/scripts），以 `count-tests.sh` 输出为准。

## CI

GitHub Actions workflow 在 `.github/workflows/protocol-tests.yml`：
- `pytest` job（ubuntu + windows 双 matrix）：Linux 全量 `python3 -m pytest agate/tests/`——**功能正确性全量保证**；Windows 只跑**技术路线冒烟**（`-m windows_smoke`，`@pytest.mark.windows_smoke` 标注每文件第 1 个用例 + 名称含平台敏感关键词的用例）——Windows 验证"平台敏感机制在 Windows 成立"，不重复验证功能（功能由 Linux 全量保证）
- `ruff` job：`ruff check agate/`（含 tests）——静态检查
- `platform-scan` job：平台假设静态扫描（Linux 阻断 / Windows 等价性证明）
- `shellcheck` job：3 个 hook 薄壳静态分析
- `consistency` job：协议一致性检查
- `gate-backstop` job：push 后重跑 gate + P6 git blame 单 author WARNING

## 何时更新

- 改 gate 规则 → **必须先加失败测试，再改脚本**
- 写 gate 消费方测试夹具 → **必须走真实 gate 语义**（真实执行 gate 脚本并按真实 exit code 断言），不得 stub/mock 假 exit（DEBT0024）
- 发现新 bug → **修脚本前先写回归测试**（regression/）
- 协议文档声明新规则 → **必须新增对应 test_*.py 用例**
- 章节标题数字漂移 → 跑 `count-tests.sh` 同步
- 发现平台假设（`PATH="/usr/bin:/bin"`/裸 `python3`/`[[ -L ]]` 单平台断言/`/tmp`）→ **修测试为平台无关**（探测或按平台分支），并在 Linux 上用模拟环境覆盖 Windows 分支——测试套件目标是平台无关（原则见 AGENTS.md「测试约定」）

## 已知风险

| 编号 | 风险 | 兜底 | 状态 |
|------|------|------|------|
| R2.3 | ~~DESIGN_GAP 在 P4 但 architect 忘记转抄 P7 → 静默放过~~ | P4/P7 交叉核对 | 已关闭（v0.6 hardening R2.3） |
| R2.4 | `unit/test_agate_archive_stale_outputs.py` 的 `test_arch_4`（同一任务对 P6 归档两次）偶发因归档目录名用秒级时间戳（`agate-archive-stale-outputs.py` 的时间戳）而在快速连续执行/系统负载较高时撞名，导致该用例单独失败 | 隔离单跑必过（非逻辑错误，纯计时窗口问题）；全量重跑一次可确认是否为此 flaky，而非真实回归 | 已知不修复——功能正确性不受影响（仅影响测试稳定性），根治需把时间戳粒度提到毫秒级或加序号后缀，评估后判定当前收益不足以覆盖改动风险；v0.35 起即存在，非 v0.40.0 引入，v0.40.0（T001）改造过程中多次复现并确认，见 `archived/docs-2026-08/reviews/agate-alignment-review-final-2026-08-10.md` |

## 目录

```
agate/tests/
├── README.md               ← 你在这里
├── test_sanity.py          ← 框架自检
├── conftest.py             ← 全局 fixture（agate_root / task_dir / git_repo / run_cli / py_path）
├── scripts/
│   ├── count-tests.sh      ← pytest --collect-only 计数
│   └── test_check_platform_assumptions.py  ← 平台假设扫描器行为测试
├── fixtures/               ← 静态夹具（Gold 任务）
│   ├── full-task/          ← 全阶段未裁剪 Gold
│   ├── ui-affected/        ← UI 任务 + vision YAML
│   ├── vision-blocked/     ← vision YAML blocker_count != 0
│   ├── high-risk/          ← risk_level=high
│   └── paused-task/        ← retries 超限
├── unit/                   ← 单元测试（按脚本分文件 test_*.py）
├── regression/             ← 回归测试（按 bug 分文件）
└── integration/            ← 集成测试
```
