---
phase: P8
task_id: TAG0037
type: release
parent: P7-consistency.md
trace_id: TAG0037-P8-20260920
status: draft
created: '2026-09-20'
agent: implementer
bump_type: minor
debt_check: reviewed
---
# P8 发布准备 — TAG0037 安装与多版本模型统一（RM-AG0066）

[PROD_NOT_TOUCHED]

> 角色：P8 releaser（implementer P8 模式）。本文件只做发布准备与遗留收尾；**未执行** bump-version / git add / git commit / git tag / git push，未删除任何文件，未触碰真实 `~/.agate` 与开发 checkout。
> 基线：HEAD 5eac312（P7 提交）。本次工作区改动仅限：`agate/scripts/README.md`、`CHANGELOG.md`、`agate/UPGRADING.md`、`agate-workspace/agents/CODE-MAP.md`、`agate-workspace/roadmap/roadmap.md`（仅追加 2 条 backlog）、本文件、`P8-progress.md`。
> 如实披露：为核对 BDD-20 ④ 的当前状态，本次曾各执行一次只读的 `gh -R randomgitsrc/agateon release list` 与 `git ls-remote --tags origin`（无任何写操作、无删除/推送）；结果见 §4 第 1、2 项。

## 1. 版本号变更确认

- 版本变更：v0.72.0 → **v0.73.0**。
- `bump_type: minor`；理由：判定表按"公共 API 行为变化 / 破坏性变更 → major"字面应升 major，但本项目 0.x 阶段沿用既有惯例（v0.5x → v0.72 的破坏性变更均在 minor 位标注 **BREAKING**，如 v0.50.0 布局变更），且 P1/P2、UPGRADING `### v0.73.0`、CHANGELOG 均已按 v0.73.0 撰写；P1 明确"README badge 非 1.0"（BDD-50 ③）。故 bump 类型 = minor，并在 CHANGELOG / UPGRADING / PR 描述以 **BREAKING** 醒目标注（删除旧单软链布局支持；`install.sh` 无参语义变更；解析链五层收敛为三层）。
- 版本文件（P2 packages `agate-docs`）：`README.md:12` 与 `README.zh-CN.md:12` 的 version badge，当前均为 `v0.72.0`——**待主 Agent 在 gate 通过后改为 `v0.73.0`**（本 releaser 不执行 bump）。
- CHANGELOG `[Unreleased]` → `[0.73.0] - <发布日期>`：**待主 Agent 执行**（本 releaser 未改名，仅补正文）。`agate/UPGRADING.md` 的 `### v0.73.0` 节已存在，无需改名。
- 主 Agent 执行后的只读检查命令：
  - `grep -n 'badge/version' README.md README.zh-CN.md`（两行均含 `version-v0.73.0`，不得为 `1.0`）
  - `grep -n '^## \[' CHANGELOG.md | head -3`（第一条应为 `## [0.73.0] - 日期`，其后为 `[0.72.0]`）
  - `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（CHECK 7 须在 commit + 创建 tag 之后跑，见 P8 卡 DEBT0013 时序注意；且远端测试 tag 清理后本地无该 tag，`git describe --tags --abbrev=0` 才与 badge 对得上）
  - `git log v0.72.0..HEAD --oneline` 对照 CHANGELOG 无遗漏

## 2. CHANGELOG 更新确认

- `CHANGELOG.md [Unreleased]` 已含：BREAKING 头注 + `### BREAKING`（legacy 软链删除、`install.sh` 无参语义、废弃 env）+ `### 新增`（版本目录契约、三路径同构 / `--adopt` / `--check --portable`、Release 流水线、文档）+ `### 变更`。
- 本次补记（DEVIATION-3）：在 `### 变更` 末尾新增"离线路径行为收紧"一条（5 个子项：旧格式 bundle 拒绝并要求重新打包 + manifest 新增 `files` / `source_ref` + `--ref`；`vX.Y.Z/` 已存在时 `install-offline.py` 替换语义；pack 输出目录已存在拒绝覆盖；不再写 `.installed-version` / `.agate-root`、嵌入式 python 不落入版本目录、`AGATE_HOOK_COPY_MODE` 不影响离线 `current`；废弃 env `AGATE_REPO_DIR` / `AGATE_SYMLINK` 的 WARNING）。同步在 `agate/UPGRADING.md` `### v0.73.0` 新增第 10 条（与 CHANGELOG 同口径、更详细）。
- 事实核对来源（先核对再写）：`P7-consistency.md` §6 DEVIATION-3；`P4-implementation.md` 批 B2 / 批 B1a / 批 E 与新增 DESIGN_GAP 第 4 条；`P2-design.md` D-6 / D-7 / R-9 / R-10 / R-11；代码实测——`agate/scripts/install-offline.py` 模块 docstring（"不再写 `.installed-version` / `.agate-root`""嵌入式 python/ 组件不安装，仅打印一行说明""`vX.Y.Z/` 已存在则旧目录先移入备份容器"）、`agate/scripts/agate-pack-offline.py` docstring（`--ref`、manifest `source_ref`）、`install.sh:16-19` 废弃 env WARNING；`AGATE_HOOK_COPY_MODE` 在 `install-offline.py` 中已无引用（grep 无命中）。旧格式拒绝文案已由 P7 §3.5 核对（`install-offline.py:243-244`）。
- 已知不写入 CHANGELOG 的内部项：`retries` 账面（DEVIATION-4）、P3 历史文档陈旧引用（DEVIATION-2）。

## 3. P7 遗留 DEVIATION 处置表

| 编号 | 内容 | 处置 | 结果 |
|------|------|------|------|
| DEVIATION-1 | `agate/scripts/README.md`「版本管理」表三行仍写旧机制 | 已改写三行（只改这三行，未重写整表，无新增脚注）：`agate-install.py`（`agate_package` 构建只含本体的版本目录、不再是 worktree；`--adopt`；`--uninstall` 仅旧整仓形态且 `repo/` 存在才 `git worktree remove`；`--check --portable`；软链 fail-closed）；`agate-pack-offline.py`（`--outdir` / `--repo` / `--ref`、manifest `files` / `source_ref`、bundle 顶层 = `agate/` + 登记根文件 + `wheels/` + `manifest.json`、无双层嵌套、outdir 已存在拒绝覆盖）；`install-offline.py`（软链守卫 → manifest 对账 → 旧格式拒绝 → checksum → 只拷 manifest 已登记本体包到带标记临时目录 → pip → 换位（替换语义）→ 兄弟 `agate-install.py --adopt`；adopt 失败回滚目录与指针；只清扫带有效标记的过期临时目录，不再写 `.installed-version` / `.agate-root`） | 已收尾 |
| DEVIATION-2 | `P3-test-cases.md` 第 120 行引用旧测试名 `test_bdd_28_use_legacy_is_gone_and_no_symlink_target_as_root_branch`（实名已在 P4 批 F2 改为 `test_bdd_28_legacy_switch_param_is_gone_and_no_symlink_target_as_root_branch`）；第 192 行"改名 3"实为 4 | **不改**（已提交的历史阶段产出）。**已知陈旧引用，接受**：不影响测试与 gate（D=12、A=247、A−D=235 已由 P6 BDD-48 重算） | 接受，不修 |
| DEVIATION-3 | 用户可见的离线路径行为收紧未入发布文档 | 已补记 `CHANGELOG.md [Unreleased]`（`### 变更` 末条）与 `agate/UPGRADING.md` `### v0.73.0` 第 10 条，事实来源见 §2；未把 `[Unreleased]` 改名 | 已收尾 |
| DEVIATION-4 | `.state.yaml` 无 `retries.P4/P5` 记录 | 主 Agent 已补（派发指引声明），本 releaser 未触碰 `.state.yaml` | 主 Agent 已处理 |
| DEVIATION-5 | P4 新增文件核对表不完整；CODE_MAP_DRIFT 2 条 | 已更新 `agate-workspace/agents/CODE-MAP.md`：在 scripts 模块段"MVWU 观测族"后新增"安装与发布族（新增 TAG0037）"，登记 `agate_package.py`（stdlib-only 库，不 import agate_common）、`agate-release.py`（Release 构建 CLI），并记载依赖边（`agate-install.py` / `install-offline.py` / `agate-pack-offline.py` → `agate_package`；`agate_common` 单向依赖 `agate_package`，无环）。`release.yml` 与 `helpers_tag_repo.py` 按 CODE-MAP 既有惯例（不登记 `.github/workflows/` 与测试文件；现有 4 个 workflow、220 余个测试文件均未登记）**不登记**，与 P7 §5 的 `CODE_MAP_SYNC` 判定一致 | 已收尾 |

## 4. BDD-20 ④ 与 BDD-50 ②–⑥ 的 P8 复验清单（主 Agent 亲自执行，均为只读检查）

前提：用户已手动清理远端测试 tag 与其预发布 Release（见 §5）。

| # | 验收项 | 只读检查命令 | 判定 | 本次 releaser 观察（HEAD 5eac312，用户尚未清理时） |
|---|--------|-------------|------|------|
| 1 | BDD-20 ④：远端无测试预发布 Release | `gh -R randomgitsrc/agateon release list` | 输出中**不含** `v0.73.0-tagtest.1` | 不满足：列表仍含 `v0.73.0-tagtest.1  Pre-release`（2026-09-20T10:34:08Z）——待用户清理 |
| 2 | BDD-20 ④：远端无测试 tag | `git ls-remote --tags origin v0.73.0-tagtest.1` | 输出为空 | 不满足：仍有 1 条命中——待用户清理 |
| 3 | BDD-20 ④ / BDD-49 前置：本地无残留测试 tag | `git tag -l 'v0.73.0*'` | 发版前为空；主 Agent 打正式 tag 后仅含 `v0.73.0`（**不得**含 `-tagtest.*`）| 满足：输出为空；`git describe --tags --abbrev=0` = `v0.72.0` |
| 4 | BDD-50 ②：README badge 非 1.0，且与版本一致 | `grep -n 'badge/version' README.md README.zh-CN.md` | 两文件均为 `version-v0.73.0-blue`，不含 `1.0` | 当前为 `v0.72.0`（bump 待主 Agent），亦非 1.0 |
| 5 | BDD-50 ③：PR 描述如实列出 release workflow 触发与权限，及测试 tag 连带触发的现有 workflow | 人工核对 PR 描述文本 | 须含：release workflow 触发条件 `on: push tags: v*`；权限 `contents: write`（零第三方 action、无 secrets、`GH_TOKEN` 仅 Publish 步骤 env）；测试 tag `v0.73.0-tagtest.1` 推送连带触发的现有 workflow 及结论——Protocol Tests 与 Docs Check 失败（根因 1：CHECK 7 badge v0.72.0 ≠ latest tag `v0.73.0-tagtest.1`；根因 2：T-17 夹具在 git 2.55 拒绝 `fast-import` 危险路径，已由修复批 895a10c 修复、待 PR CI 于 git 2.55 确认），Site Check 成功，`deploy-pages` 未触发 | PR 尚未创建，待主 Agent 撰写；事实来源 `P6-acceptance.md`「已知遗留」第 4 条、`P6-evidence/g1/bdd-15-hostile-members-ci-vs-fixed.md`、`P7-consistency.md` §4 |
| 6 | BDD-50 ④：roadmap RM-AG0066 = done | `grep -n '^| RM-AG0066 ' agate-workspace/roadmap/roadmap.md` | 「状态」列为 `done`（P8 gate 硬校验，RM-AG0043）| 当前 `scheduled`——**主 Agent 亲自回写**；本 releaser 未改该行 |
| 7 | BDD-50 ⑤：`HANDOFF-TAG0037.md` 归档 | `ls HANDOFF-TAG0037.md agate-workspace/archived/plans/HANDOFF-TAG0037.md` | 根目录不再有，`agate-workspace/archived/plans/` 下有（用 `git mv`，不删除） | 当前仍在仓库根——待主 Agent 归档 |
| 8 | BDD-50 ⑥ / BDD-21：正式 v0.73.0 Release 含 3 个 tarball + `SHA256SUMS` | `gh -R randomgitsrc/agateon release view v0.73.0 --json assets --jq '.assets[].name'` | 至少含 `agateon-v0.73.0.tar.gz`、`agateon-v0.73.0-offline-linux-x86_64.tar.gz`、`agateon-v0.73.0-offline-windows-x86_64.tar.gz`，另有 `SHA256SUMS`（共 4 个资产，P2 C-1 口径）；并 `gh release download` 后 `sha256sum -c SHA256SUMS` 通过 | 正式 tag 尚未推送，待主 Agent 推 tag 后执行 |

## 5. 临时资源清单（releaser → 主 Agent 交接）

- **常驻进程 / 服务**：无（P4–P8 未启动任何常驻服务、调试服务器或后台进程；P4 起的 pytest / 打包 / 安装实验均为一次性命令，已退出）。
- **开发安装**：无（未向真实 `~/.agate`、系统 Python 或全局环境安装任何东西；所有安装实验使用隔离的 `AGATE_HOME` / `HOME` 落在 scratchpad 内）。
- **临时数据（本地，agent 建立）**：均在会话 scratchpad `/tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/` 下（仓库外，不影响 git 状态），约 115 项，前缀：`g1*` / `g2*`（P6 验收分组）、`p5-home-*` / `p5-release-*`（P5 验证）、`p7-01`（P7 实验）、`exp-*` / `expA-*`（实验）、`cso-*` / `cso-p4-*`（安全评审）、`eng*` / `eng-r1-*`（工程评审）、`rv-*`（review）、`c1*` / `c-ref*` / `c3a.tgz` / `c3b.tgz` / `c2.tar`（C 批冒烟）、`tdd-red-*`、`t15.log` / `t17-*`、`backup*`、`b52-*`、`manual-*`、`h_smoke_*`、`refB-*` / `refroot`、`scan*`、`*.log`（pytest / ruff / shellcheck / consistency / build 日志）等。**不做清理**（会话 scratchpad 由会话生命周期管理；不 rm -rf，若主 Agent 认为需要清理应在用户确认后自行处理）。
- **仓库内临时文件**：无新增（P4 起各批记录"仓库内无遗留 `.agate-tmp-*` / 备份 / 临时文件"；本次仅改上述 5 个既有文件并新增本文件与 `P8-progress.md`）。已忽略的 `__pycache__/` 目录（`agate/scripts/`、`agate/tests/` 等，`git status --ignored` 显示为 `!!`）来自早先阶段的解释器运行，被 `.gitignore` 忽略，不影响 git 状态；本次所有命令均设 `PYTHONDONTWRITEBYTECODE=1` / `python3 -B`。
- **远端测试资源（待用户手动清理，精确名称）**：
  - 远端测试 tag：**`v0.73.0-tagtest.1`**（指向 d6dd3cb）；
  - 其预发布 Release：**`v0.73.0-tagtest.1`**（Pre-release，含 4 个资产）。
  - 参考清理命令（**由用户亲自执行**，本 releaser 未执行、也不执行）：`gh -R randomgitsrc/agateon release delete v0.73.0-tagtest.1 --cleanup-tag`；或先 `gh -R randomgitsrc/agateon release delete v0.73.0-tagtest.1`，再 `git push origin :refs/tags/v0.73.0-tagtest.1`。详见 `P6-acceptance.md`「已知遗留」第 1 条。清理后须重跑 CHECK 7 / BDD-49。
- **`.agate/formatters/pytest.sh` 任务内覆盖文件**：路径 `agate-workspace/tasks/TAG0037-install-package-model/.agate/formatters/pytest.sh`（已被 git 跟踪，属任务目录内容）。作用：与稳定版 `agate/assets/formatters/pytest.sh` 逻辑相同，仅把 pytest 输出经临时文件而非环境变量传给 python，规避全量红灯输出 >128KB 时的 `参数列表过长`（MAX_ARG_STRLEN）。处置：**保留，随任务目录归档提交**（不删除，作为 P5 证据的可复现来源）；它只在本任务目录内生效（`resolve_formatter` 优先取 `$task_dir/.agate/formatters/`），不影响其他任务与稳定版；不需要还原任何全局状态（脚本内 `mktemp` 临时文件由 `trap ... EXIT` 自清理）。后续如要修稳定版同类缺陷，属独立议题（本次未登记 backlog、未改稳定版 formatter）。

## 6. 债务清单核对（debt_check: reviewed）

已读 `agate-workspace/debt/tech-debt.md`（DEBT0001–DEBT0048）。与本任务（安装 / 离线 / 发布 / 解析）文件面相关的条目：

- 已关闭且与本任务改动面同域（本次未引入回归、不需动作）：DEBT0002（`compute_sha256` 共享单实现，本任务保持并新增字节码忽略）、DEBT0003（离线 checksum 信任边界，README 信任边界段保留）、DEBT0034（迁移文案双写，本任务 `_migration_steps` 跨入口比对沿用）、DEBT0042（`AGATE_HOME` 基址覆盖，本任务 `agate_package.agate_home()` 承接）、DEBT0013（P8 CHECK 7 时序，已按 P8 卡时序注意排在 tag 之后重跑）。
- 未关闭条目已逐条扫描，标题范围均不落在本任务改动面（协议脚本 gate / 提示 / 评审工具类）：DEBT0008、0014、0015、0028、0029、0030、0031、0032、0033、0040、0041、0043、0044、0045、0046、0047、0048——**无一由本任务新引入，也无一被本任务关闭**。其中 DEBT0047（gate_commands 取值引号陷阱）与 DEBT0048（P3 阶段 `/tmp` 字面量平台假设）属流程类既有债务，本任务过程中未作为阻塞项出现；不阻断发布。
- 本任务新增待办均登记为 roadmap backlog，不写入债务表：RM-AG0069（`install.sh` 重跑更新 `repo/`）、RM-AG0070（`latest` 从 Release asset 取包）。P2 §13 的其他后续建议（`_sync_root_scripts` 条件同步已并入 RM-AG0069 描述；`pip` 走 `sys.executable`、`--require-hashes`、并发锁、静态迁移文案硬编码 `~/.agate`（cso L-5）、portable 文档 shell 守卫处理 `/.`（cso L-2）、AGENTS 发布清单 `gh release delete` 缺 `-R`（cso L-8））暂未单独立项，建议主 Agent 在复盘时决定是否登记。

已核对债务 id 清单：DEBT0002、DEBT0003、DEBT0013、DEBT0034、DEBT0042（相关且已关闭）；DEBT0008、0014、0015、0028–0033、0040、0041、0043–0048（未关闭、与本任务无关）。

## 7. roadmap backlog 登记确认

- 在 `agate-workspace/roadmap/roadmap.md` 条目表末尾（RM-AG0068 之后，当前最大编号 RM-AG0068，顺延不复用）追加：
  - **RM-AG0069**：`install.sh` 重跑时对已存在 `repo/` 做 `git pull --ff-only`（升级自举缺口；P2 主 Agent 裁定本任务不做），状态 `backlog`。
  - **RM-AG0070**：`agate-install.py latest` 从 Release asset 取包（RM-AG0066 拟议模型第 2 项，P1 已声明不属本任务），状态 `backlog`。
- **未改动 RM-AG0066 的状态行**（`scheduled`，由主 Agent 亲自回写 `done`，见 §4 第 6 项）。

## 8. 自检结果

- 改动 `agate/*.md`（`agate/UPGRADING.md`、`agate/scripts/README.md`）后：`python3 -B agate/scripts/check-protocol-consistency.py --strict-errors-only` → 0 ERROR（386 个既有叙事类 WARNING）。
- 文档类测试：`test_upgrading_lifecycle.py` / `test_upgrading_contract_doc.py` / `test_doc_sweep.py` / `regression/test_no_legacy_residue.py` 合跑 78 passed；附加 `test_agate_changelog_unreleased.py` / `test_check_changelog.py` / `test_code_map_template.py` / `test_agate_version_install.py` / `test_tag0034_docs.py` / `test_mvwu_protocol_docs.py` / `test_check_protocol_consistency.py` / `regression/test_tag0037_out_of_scope_untouched.py` 合跑 166 passed / 0 failed。
- 发布检查命令（P2 packages）与 P5 重跑 / CHECK 7 / `check-gate.py P8`：按 P8 卡由主 Agent 亲自执行，本 releaser 未执行。
