# 评审报告：agate 文档体系更新（2026-08-15）

日期：2026-08-15
评审对象：`feat/TAG0010-python-migration` 分支上 ef2dfa3..f8a6e7d 的 6 个文档 commit（文档体系更新设计 → README 门面 → 中文镜像 → AGENTS 入口 → SETUP/UPGRADING/CONTEXT 核对 → role/loop/adr 引用修复）
评审角色：独立评审员（只评审，不修改文件）
评审依据：`docs/superpowers/specs/2026-08-15-docs-suite-update-design.md`（设计文档）+ 设计文档声明的事实源（WORKFLOW / platform-notes / LIMITATIONS / 脚本与测试实物）

## 1. 评审方法

逐文件核对以下事实（不依赖文档自述，直接对照仓库实物）：

- 脚本层：`agate/scripts/` 下 `check-gate.py` / `install-hook.py` / 3 个 hook `.sh` 薄壳是否存在；`install-hook.py` 是否 `ln -sf` 软链安装
- 测试层：`agate/tests/` 下 `.bats` 残留数、`test_*.py` 数、`helpers/` 是否退役、`conftest.py` 与 `count-tests.sh` 是否存在
- 版本层：`git tag` 最新版本、`CHANGELOG.md` 版本章节
- 迁移数字：用 `git ls-tree` 对 v0.46.0 tag 与 bats 退役提交（6e69c00）前一刻实测 `.bats` 数与 `@test` 数
- 导航层：README / AGENTS 引用的每个文档、目录、角色文件逐一确认存在
- 一致性层：中英 README 逐章节对拍；文档间交叉引用对拍；`check-gate.sh` / `install-hook.sh` / `.bats` 残留扫描（范围文件内）
- 裁剪表述：README 风险裁剪段与 `WORKFLOW.md` 风险矩阵逐条对照

## 2. 逐维度结论

### 维度 1：信息准确性

**结论：有问题（2 处，1 中 1 轻）**，核心状态事实全部核实无误，风险裁剪概述一处与协议冲突。

核对通过项：

- v0.47.0 状态准确：`check-gate.py`、`install-hook.py`、`agate-summary.py` 等 `.py` 产物全部存在；`commit-msg-self-gate.sh` / `pre-commit-gate.sh` / `pre-push-gate.sh` 3 个薄壳存在且为仅存的 `.sh`；`install-hook.py` 实测 `_ln_sf`（`ln -sf` 等价，Windows 无权限退化为复制）。
- 测试状态准确：`agate/tests/` 下 `.bats` 实测 **0 残留**；`test_*.py` 实测 60 个（46 unit + 6 regression + 6 integration + sanity + scripts 扫描器，与 UPGRADING 口径一致）；`helpers/` 已退役；`conftest.py` / `tests/scripts/count-tests.sh` 存在。
- 迁移数字准确："60 个 `.bats` / 749 `@test`" 经 git 实测验证：bats 退役提交 6e69c00 前一刻为 60 个文件 / 749 个 `@test`（v0.46.0 tag 有 61 个是因为 `check-windows-smoke.bats` 在退役批次 17 已先删，数字自洽）。
- 无过时引用（评审范围文件内）：README / README.zh-CN / AGENTS 扫描无 `check-gate.sh` / `install-hook.sh` / `.bats`（唯一 `.sh` 是 curl 安装脚本 `install.sh`，指向真实存在的安装器）；UPGRADING 的 `.sh` 引用全部落在迁移对照表、退役脚本说明、hook 薄壳说明内，符合"对照表除外"豁免。
- 版本号统一 v0.47.0：`git tag` / README badge / CHANGELOG `[0.47.0]` 三方一致。

问题（详见第 3 节）：

- **[中] 问题 1**：README.md:92（及中文镜像 :92）风险裁剪表述与 `WORKFLOW.md` 冲突。
- **[轻] 问题 3**：SETUP.md:101 交叉引用失效。

范围外观察（详见第 3 节）：`agate/phase-cards/P1-P8` 仍存在可操作的 `check-gate.sh` / `check-pruning.sh` / `agate-capture-env-baseline.sh` 过时引用——不在本次评审文件清单内，但直接违背"无过时引用"目标且为编排者每阶段必读文档，已如实列出。

### 维度 2：专业性与实践符合度

**结论：通过。**

- 英文 Native-level、无翻译腔：tagline（"verifies AI agents the way a build system verifies a compiler"）、"Gates are hard boundaries"、"Self-authored gates are mitigated, never cured…" 等表述准确且有力度；Quick start / How it works / 四件事概述与协议实际行为一致。
- 中文专业、术语准确：exit code、gate、subagent、orchestrator、状态落盘、自写文件 gate、外部产出 gate、provenance、risk_level 等与协议词汇体系一致，无生造词。
- README 门面结构符合设计文档要求：tagline → What/Why → Quick start → How it works → Platforms → Documentation → Principles → Limitations → Contributing（另加 License），接入细节全部归 SETUP，门面不承载实施细节。
- 语言切换惯例两端一致：`[English](README.md) | [中文](README.zh-CN.md)`。
- 中英镜像对等：两文件均 108 行，10 个章节一一对应，版本 badge、GitHub 链接、语言切换、文档导航表、信任分级表、局限引用、测试命令逐条对应。
- 信任分级表（外部产出 gate P3/P4/P5 vs 自写文件 gate P1/P2/P6/P7）与 `LIMITATIONS.md` 局限 3 的分类一致；"See Limitation 3" 指向局限 3 内容正确。

### 维度 3：一致性

**结论：通过（1 处轻量交叉引用问题）。**

- 中英镜像对等：版本号、链接、章节数全部一致（见维度 2）。
- 文档互引一致：README 文档表 10 行、AGENTS 入口导航表 15 行引用的目标文件全部存在；角色文件清单与 `assets/execution-roles/`（7 个）、`assets/review-roles/`（10 个）逐文件对应；`phase-cards/P0-P8`、`rules/`（review-mapping / state-transitions）存在；`assets/templates/project.md` 等模板存在。
- README → SETUP/WORKFLOW/AGENTS/LIMITATIONS/UPGRADING/CONTEXT/adr/tests-README 互引无断链。
- 3 个 hook 薄壳、`install-hook.py`、`python3 -m pytest agate/tests/` 在各文件表述一致，无 `bash ~/.agate/scripts/*.sh` 旧调用残留。
- **[轻] 问题 3**：SETUP.md:101"见 `agate/AGENTS.md`"指向错误——该内容实际记录在 `.gitattributes` 注释，`agate/AGENTS.md` 无相关讨论。

## 3. 问题清单

| # | 严重度 | 文件:位置 | 问题描述 | 建议修复 |
|---|--------|-----------|----------|----------|
| 1 | 中 | README.md:92（`README.zh-CN.md:92` 镜像同病） | 风险裁剪段与 `WORKFLOW.md` 冲突：(a) "low-risk tasks may skip P7 (and **optionally P3 TDD**)" —— WORKFLOW 明言"P3 TDD 测试先行**默认保留**，有明确理由才跳过"（WORKFLOW.md §可裁剪的阶段），且低风险小改动裁剪流（P1+P3+P4+P5）**保留 P3**；"optionally" 表述错误。(b) "later phases are pruned **automatically**" —— 裁剪须在 P1 写明理由、最终拍板权在主 Agent，非自动。(c) 裁剪实为"复杂度 × 风险"矩阵，非仅 risk_level；低风险小改动同时跳过 P2/P6/P8，只提 P7 不完整 | 对齐 WORKFLOW 矩阵改写，如："Pruning is decided in P1 (risk × complexity): small single-point changes run a pruned flow with test-first kept, medium changes run the standard flow, and high-risk tasks keep acceptance/consistency mandatory and warrant a final human review"（中文镜像同步） |
| 2 | 中（范围外） | agate/phase-cards/P1-requirements.md:16,84 / P2-design.md:12,117,133 / P3-tdd.md:53 / P4-implementation.md:4,8,87,119,122 / P5-verification.md:82 / P7-consistency.md:13,79 / P8-release.md:57 | 编排者每阶段必读的卡片仍写 `check-gate.sh`（P4 卡片另有 `check-pruning.sh`、`agate-capture-env-baseline.sh`）。脚本已不存在，卡片命令与实际产物脱节；这些文件不在本次评审清单内，但直接违背"无过时引用"目标 | 建议后续批次统一改 `check-gate.py` / `check-pruning.py` / `agate-capture-env-baseline.py`，并纳入 `check-protocol-consistency.py` 的引用扫描（若已覆盖则修复后自然清零） |
| 3 | 轻 | agate/SETUP.md:101 | "历史 review 文件保持 CRLF，见 `agate/AGENTS.md`"——`agate/AGENTS.md` 无任何 CRLF 讨论；该说明实际在 `.gitattributes` 文件头注释里。交叉引用失效 | 改为"见仓库根 `.gitattributes` 文件头注释"（或删除该引用） |
| 4 | 轻 | README.md:32（`README.zh-CN.md:32` 镜像） | "workspace is created automatically on first run — no manual setup" 与 SETUP.md 步骤 5 让用户手工 `mkdir -p {AGATE_WORKSPACE}/…` 存在轻微张力。orchestrator-template.md 接入段确认编排者首跑会自建（可辩护），但"no manual setup"仍略强 | 可改为"the workspace directory structure is created on first run；see `agate/SETUP.md` for the one-time setup"，与 SETUP 步骤 5 的自查语义对齐 |
| 5 | 轻 | agate/UPGRADING.md:106 | "仅存 `test_*.py` pytest 用例"表述略宽——`agate/tests/` 下还含 `conftest.py`、`fixtures/`、`agate/tests/scripts/count-tests.sh` 等非 `test_*.py` 文件 | 改为"不再有 `.bats`，测试用例均为 `test_*.py` pytest 用例" |

## 4. 总体结论

**需修订（修订面很小）。**

第一级（README / README.zh-CN / AGENTS）与第二、三级整体质量高：v0.47.0 状态事实全部核实准确、无过时引用、中英镜像对等、导航零断链、英文/中文均专业无翻译腔，设计文档声明的结构目标全部达成。阻塞项仅一处协议事实冲突（问题 1：README 风险裁剪段把"默认保留的 P3 TDD"写成 low-risk 可选），建议修订后即可通过。问题 2（phase-cards 过时引用）在评审清单之外，但属同类"无过时引用"目标缺口且是编排者实操文档，建议单独安排一次小批次修复。

## 5. 附：核对明细（关键事实核实记录）

| 事实 | 核实方式 | 结果 |
|------|----------|------|
| `check-gate.py` 等脚本存在 | `ls agate/scripts/` | ✅ 46 个 `.py` + 3 个 hook `.sh` 薄壳 |
| `install-hook.py` 用 `ln -sf` | 读 `install-hook.py` `_ln_sf()` | ✅ os.symlink 等价，Windows 退化复制 |
| `.bats` 0 残留 | `find agate/tests -name "*.bats" | wc -l` | ✅ 0 |
| `test_*.py` 60 个 | `find agate/tests -name "test_*.py" | wc -l` | ✅ 60（46+6+6+1+1） |
| 迁移数字 60/749 | `git ls-tree` 实测 6e69c00^ | ✅ 60 个 `.bats` / 749 `@test` |
| `helpers/` 退役 | `ls agate/tests/helpers` | ✅ 目录不存在 |
| 版本 v0.47.0 | `git tag` / `git describe` | ✅ v0.47.0 |
| README badge 仓库 | `git remote -v` | ✅ randomgitsrc/agate |
| 安装脚本 `install.sh` | 仓库根存在 + `git show origin/main:install.sh` | ✅ 存在且已在 main |
| 引用目标文件 | 逐文件 stat README/AGENTS 全部链接 | ✅ 全部存在 |
| 角色文件清单 | 对照 `assets/execution-roles`、`assets/review-roles` | ✅ 17 个文件逐一对应 |
| README 中英对等 | 逐章节对拍（均 108 行） | ✅ 章节、版本、链接一一对应 |
| 范围文件无过时引用 | `grep -rin "check-gate\.sh\|install-hook\.sh\|\.bats"` | ✅ 仅 UPGRADING 迁移对照表/退役说明 |
