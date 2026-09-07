---
phase: pre-commit (self-gate Layer 1)
generated_by: 主 Agent
task_id: TAG0032
role: protocol-alignment-review
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。本轮是 **SELF-GATE Layer 1（协议-脚本语义对齐审查，变更触发模式）**——TAG0032 改了 `agate/scripts/*.py` + `agate/*.md` + `install.sh`，P8 发布前须过本审查。

## 你的角色定义
读取并遵循：`/home/kity/oclab/agateon/agate/assets/review-roles/protocol-alignment-review.md`（A1-A7 审查清单 + 反向传播常见路径表）

## 第一步：意图分析

本次变更意图（1-2 句「为什么改」）：修复 TAG0008 版本管理 v1 的「全新机器 → 版本布局 → 项目钉版 → 更新」生命周期三个断点——① 入口断链（legacy 软链下 `agate-install` 穿透软链污染源仓库 / 装完根 `~/.agate/scripts/` 不存在）② 元仓库 gap（GitHub 装出的版本目录 = agateon 整仓，协议在 `agate/` 子目录，resolve 返回仓库根导致 gate 路径取不到）③ 无 update 统一入口。

## 第二步：反向传播——列出应被影响的文件

基于意图主动推断「这次改动应该传播到哪些文件」，不只列 git diff 里的。参考角色文件「反向传播的常见路径」表。重点核查：

- `agate/scripts/README.md`：diff **未改**——但 L70 `agate-install.py` 描述「无参 = 装 latest 指针」，TAG0032 新增 `latest` 显式别名（DESIGN_GAP 2）；L5 版本管理机制段描述是否需补 `install.sh --versions` bootstrap 路径 + 根 `~/.agate/scripts/` 副本 + 元仓库形态 `_protocol_root` 探测？
- `agate/tests/README.md`：新增 5 个测试文件（`test_upgrading_lifecycle.py` + `test_version_lifecycle_e2e.py` + 3 个 `test_agate_version_*` / `test_hook_resolve_entry` 追加用例）——测试清单/计数描述是否需同步？
- `agate/adr.md`：`_protocol_root` 探测序（`vdir/scripts` 先、`vdir/agate/scripts` 后）+ 决策 B1 副本机制——是否触及已记录 ADR？是否有未记录的架构决策需补 ADR？
- `agate/platform-notes.md`：install.sh --versions 的 POSIX shell 假设 / 决策 B1 副本（非软链，无 Windows 退化）——是否需补平台说明？
- `agate/AGENTS.md`（协议使用者版）：版本管理机制描述是否需同步？
- `CHANGELOG.md`：**P8 会更新**（AGENTS.md 发布清单）——A5 核查是否已标注语义变更；本审查在 P8 之前，可标「CHANGELOG 待 P8 补，本审查已确认需标注的条目」
- `README.md` / `README.zh-CN.md` / `agate/SETUP.md` / `agate/UPGRADING.md`：diff **已改**——核查 A1/A2 语义一致

## 第三步：实际审查范围

读以下文件全文（或相关节）：
- **diff 直接改的**（`git diff 3f3cc01..HEAD -- agate/ install.sh README.md README.zh-CN.md`）：`agate/scripts/agate-install.py`、`agate/scripts/agate_common.py`、`agate/UPGRADING.md`、`agate/SETUP.md`、`README.md`、`README.zh-CN.md`、`install.sh`、5 个测试文件
- **第二步反向传播候选**：`agate/scripts/README.md`、`agate/tests/README.md`、`agate/adr.md`、`agate/platform-notes.md`、`agate/AGENTS.md`
- **权威规则源**：`agate/state-machine.md`、`agate/dispatch-protocol.md`、`agate/WORKFLOW.md`（本次不太可能触及，快速扫）

## 审查清单（A1-A7，逐项 ALIGNED / MISALIGNED / NEEDS_HUMAN_REVIEW）

- **A1 文档→脚本**：UPGRADING「版本管理生命周期」节写的行为（安装/迁移/更新/回退对照表 + hook 重装口径 + 根 `scripts/` 维护语义条目）↔ `agate-install.py` / `install.sh` 实际实现是否语义一致？**特别核查**：P7-consistency.md 已记录一处非阻塞偏差——UPGRADING「根 scripts/ 维护语义」段仍描述 fix-1 已删的 layer-1「运行中安装器 scripts/ 叠加 current 协议 scripts/（后拷贝者胜）」双层机制，但代码 fix-1 已回退单源 copytree。核实该偏差，判 MISALIGNED（P8 须修）或 NEEDS_HUMAN_REVIEW
- **A2 脚本→文档**：`agate_common.py` 新增 `_protocol_root` + `_resolve_version_info` 两处调用 / `agate-install.py` 新增 `_sync_root_scripts` + `latest` 别名 + `_ensure_repo` git fetch / `install.sh` 新增 `--versions` 分支——对应文档（尤其 `agate/scripts/README.md` L5/L70）是否同步？
- **A3a 一致性连锁** + **A3b 反向传播**：列出「应被这次改动影响但未在 diff 中的文件」，逐一验证。重点 `agate/scripts/README.md` / `agate/tests/README.md` / `agate/adr.md`
- **A4 测试覆盖**：新逻辑（`_protocol_root` 两形态 + install 软链守卫 + 根 scripts + install.sh --versions + 端到端）是否有对应 pytest 且覆盖边界？**必须附最近一次全量 pytest 实跑输出**（含 passed/failed 计数）——可自跑 `timeout 600 /usr/bin/python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto` 或引用 P5-test-results/unit.md 的 P5 实跑记录（1484 passed / 2 skipped / 1 预存 flaky）+ 自己复跑一次确认
- **A5 下游影响 + 文档传播**：`_protocol_root` 改变 `_resolve_version_info` 返回值语义（元仓库形态返回 `vdir/agate`）——下游消费方（`resolve-entry.py` gate 路径拼接 / `resolve_rules_root` / `check-gate.py` / `agate-summary.py` / `agate-resolve.py`）行为是否受影响？纯增量红线（根即协议部署方零回归）是否真的守住？CHANGELOG 语义变更条目（P8 待补）核查
- **A6 锚点表覆盖**：CHECK 9 锚点表是否需更新？新增协议规则（若有）是否需加锚点？
- **A7 设计原则一致性**：对照 `agate/adr.md` 相关 ADR（尤其版本管理 / 解析链 / 平台无关相关）。`_protocol_root` 探测序 + 决策 B1 副本是否符合已记录 ADR？有无未记录架构决策需补 ADR？（A7 只有 ALIGNED / NEEDS_HUMAN_REVIEW）

## DESIGN_GAP 优先核查（角色文件原则 6）

发现文档-脚本不一致时，先查 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md` + `P7-consistency.md` 是否已有对应 `[DESIGN_GAP:]` / `[DESIGN_GAP_REVIEWED:]`。P7-consistency.md（`agent: consistency-reviewer`，approved，5 GAP 全配对 REVIEWED）已独立核实 5 处 DESIGN_GAP + 1 处非阻塞偏差（UPGRADING layer-1 描述滞后）。已 REVIEWED-ACCEPTED 的不判 MISALIGNED，注明「已知偏离，来源：TAG0032 P7 REVIEWED-ACCEPTED」；P7 未覆盖或裁决理由站不住的仍按 MISALIGNED 处理。

## 分阶段落盘（留痕文件，防空返回）

留痕文件：`/home/kity/oclab/agateon/.worktrees/agate-TAG0032/docs/reviews/agate-alignment-2026-09-07-TAG0032-01.progress.md`
开始前先删除（如已存在）：`rm -f <留痕文件路径>`
每读完一个文件 / 完成一个对比判断，立即 bash `echo "- ..." >>` 追加原始痕迹（不整理、不格式化）。

## 产出（成果文件，最终交付物）

`/home/kity/oclab/agateon/.worktrees/agate-TAG0032/docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md`
审查完所有文件后一次性写出（覆盖写）。含 frontmatter（`review_date` / `reviewer` / `change_summary` / `files_changed`）+ A1-A7 结论汇总表 + 逐项审查详情（每项引用文档原文行号 + 脚本代码行号）。
⚠️ 路径是硬约束：用 Write 工具写入此路径，不得写 /tmp / 工作区根 / 其他路径。

## 客观查证信息

- 解释器 `/usr/bin/python3`；只审不改，不碰 git
- 改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；`check-protocol-consistency.py` 用 worktree 自己的
- bash 外层 `timeout`（全量 pytest 600s，其他 30-90s）；单步串行；状态标记 `[PROD_NOT_TOUCHED]`

## 闭环规则

| 结论 | 处理 |
|------|------|
| 全 ALIGNED / A7 NEEDS_HUMAN_REVIEW（附 [HUMAN_CONFIRMED]）| 通过，可 commit |
| 任一 MISALIGNED | 必须修复——主 Agent 派 implementer 修脚本或修文档，修完重审 |
| NEEDS_HUMAN_REVIEW | 附 `[HUMAN_CONFIRMED: 日期 确认：理由]` 后可 commit |

## 返回给主 Agent

`File: <成果文件路径>` + A1-A7 结论汇总（一行）+ MISALIGNED 项数 + 一句话摘要。不返回文件全文。
</dispatch_guide>
