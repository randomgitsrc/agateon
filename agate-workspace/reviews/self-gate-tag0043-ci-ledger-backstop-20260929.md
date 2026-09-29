---
status: approved_after_changes
agent: protocol-alignment-review
reviewed_at: 2026-09-29
---
# SELF-GATE 评审：DEBT0040 ③ CI 账本污染兜底

## 范围

直改通道交付（分支 + PR，未走 P0-P8）。改动 8 个跟踪文件 + 2 个新文件，落地
DEBT0040 `closure_criteria` 第 ③ 条（**CI 有账本兜底步**）——该条因「CI 改动须用户许可」
长期空置，本次经用户**明确许可**后落地（`~/.dsh/AGENTS.md` 第 5 条）。

触发面：`.github/workflows/*.yml` + `agate/scripts/*.py` + `agate/**/*.md` + 仓库根 `AGENTS.md` ⇒ 须 SELF-GATE。

## 结论

**评审首轮 REQUEST CHANGES（1 实质 MAJOR + 1 过度声称 MAJOR + 3 MINOR + 1 NIT），全部已处置；
处置后复验全绿。** 评审同时确认 6 项声称成立（架构约束、`status` vs `diff`、测试非真空、
性能数字、登记面机制、计数 68 与 fixtures=5）。

## ⚠️ 评审事故（必须披露，已核验无残留）

**评审者用 `git checkout -- .` 丢弃了未提交改动集。** 其首次 scratch 验证在 `/tmp/...` 下落空
（本机 `/tmp` 为**逐调用 tmpfs**，跨 bash 调用不保留），遂在仓库内执行了 `git checkout -- .`，
并额外产生一个游离提交 `204e5f4`（message `ign`）。

**主 Agent 独立核验结果**：
- `git reflog` 显示 `204e5f4 commit: ign` → `2698b56 reset: moving to HEAD~1`，**HEAD 已回到
  2698b56，游离提交不在任何分支上**（`git log` 干净）
- 评审者称已从首轮 diff 恢复，`git diff --stat` = 57 insertions / 2 deletions 与事故前一致
- **但恢复不完整**：主 Agent 在事故后于 `implementer.md` / `test_t42_p3_platform_selfcheck.py` /
  `CHANGELOG.md` 所做的 **3 处改动被一并丢弃**（因它们发生在其首轮 diff 捕获之后）——
  已**全部重做**并在本轮重新验证（见「遗留与诚实说明」）

**流程教训（建议入 roadmap）**：本仓的评审者若要用临时目录做 scratch 验证，**必须把
「建目录 → 操作 → 清理」放在同一次 bash 调用内**（`/tmp` 跨调用不保留）；且**禁止**在共享
工作树上执行 `git checkout -- .` / `git reset --hard` 这类破坏性命令——评审应为只读角色，
scratch 一律在仓外或 `git worktree` 内进行。本次已按此结论重做受影响改动。

## 逐条核实（评审给结论，本表为摘要）

| # | 声称 | 判定 | 依据 |
|---|------|------|------|
| 1 | 兜底**必须**在 `pytest` job 内（独立 job 看到干净 checkout，结构上不可能观测副作用） | **TRUE** | `gate-backstop` 有自己的 `actions/checkout@v4`；job 间是独立 VM；新步骤确在 `pytest` job 内且在全量测试步骤之后 |
| 2 | 用 `status` 而非 `diff`（`diff --exit-code` 漏新建未跟踪账本） | **TRUE** | scratch 仓实测：新建未跟踪账本时 `diff` rc=**0**、`status` 能捕获 |
| 3 | 10 条测试非真空 | **TRUE** | 删 workflow 步 → 1/2/3 红；掏空检测 → 6/7/8 红；无"为错误理由通过"的用例 |
| 4 | 68 个状态文件、恰两处落点 | **PARTIAL** | 68 与 fixtures=5 正确，但 `agate-workspace/`=**63 而非 62**（初版错，已改） |
| 5 | 全量测试后兜底仍 exit 0（不误报） | **FALSE（初版）** | 真实树 exit 1，命中 `M agate-workspace/debt/tech-debt.md`——**兜底让自己红**；见 MAJOR-1 |
| 6 | 性能 ~6ms / ~31ms、不增 job | **TRUE** | 复测 `git status` 6.0-7.5ms、端到端 30ms、3.6k 跟踪/21k 工作区文件 |
| 7 | 文档准确 | **PARTIAL** | "仍 exit 0" 与 62 两处失实（均已改）；残余不确定性披露被评审判定为**准确且恰当** |
| 8 | 登记面机制生效 | **TRUE** | 0 条 `CHECK9-coverage`；`callers` A/B（有→0 警告，无→1 警告） |

## 处置记录

| 编号 | 级别 | 问题 | 处置 |
|------|------|------|------|
| MAJOR-1 | **MAJOR** | **兜底让自己红 / pathspec 过宽**：初版用**目录** pathspec，把该子树下**任何**文档编辑（含本债闭合记录 `tech-debt.md`）判成污染 ⇒ 引入它的 PR 自己红，且**只在「本来就没有任何东西需要检查」的树上才绿**（**零覆盖**） | 改为 git magic glob **精确到三族状态文件名**（6 条 glob，覆盖两处落点）。加 **2 条回归判据**：`t43lb_11`（正常文档编辑须 exit 0）、`t43lb_12`（禁止退回目录级写法）。**负向控制实测**：退回目录写法时**仅这 2 条**转红。真实树复测 → **exit 0** |
| MAJOR-2 | **MAJOR** | **过度声称**：「跑完全量测试后立即跑兜底仍 exit 0」在真实树上为**假** | 承认该测量系在**未含本债闭合编辑的树**上取得、对最终改动集**不成立**，已作废；修正 pathspec 后**重测**（2450 passed 后实测 exit 0），并在 CHANGELOG/closure_note **明写"先前记录作废重测"**，不静默改数 |
| MINOR-3 | MINOR | `agate-workspace/` 状态文件数 **62 → 63**（3 处：脚本 docstring / DEBT closure / CHANGELOG） | 三处全部改正（62 = 仅 `tasks/` 子目录；63 = 含 `archived/`） |
| MINOR-4 | MINOR | `status.showUntrackedFiles=no` 之类 git 配置会让新账本静默不可见 | 加 `-uall`（hardening）：显式逐文件列出，不依赖 `status` 收集器默认值 |
| MINOR-5 | MINOR | **固有边界未披露**：脚本只在 `pytest` job 内跑，**无 push/合并后**对应检查——状态文件被提交后合并即不再复查 | 在脚本 docstring 与 closure_note 的「诚实边界」节**明确写出**（连同「被 `.gitignore` 覆盖的运行时产物有意排除」的理由） |
| NIT-6 | NIT | `callers` 是**子串**匹配，注释提及即可满足，文档不应暗示它是强制力 | 文档改为明写：`callers` 是**弱**判据，**真正强制力在 workflow 步骤的机械判据上**（`t43lb_1/2` 断言步骤确在 `pytest` job 内且在测试之后） |
| — | 未复现 | 评审称 DEBT0040 块内有**重复 YAML 键**（`closed_at` 两处 + 潜在第二个 `status`） | **核验后未复现**：该块 `status:` 1 处、`closed_at:` 1 处，`2026-09-10` 是 `created_at`（非 `closed_at`）。评审大概看的是其自己恢复过程中的中间态。**据实记录为「未复现」，不据此改动** |

## 复验结果（处置后）

| 项 | 结果 |
|----|------|
| 相关测试 | **37 passed**（`test_t43_ledger_pollution_backstop` 12 + `test_t43_check_registration_surface` 12 + `test_t42_p3_platform_selfcheck` 5 + `test_protocol_alignment_review` 8） |
| 全量 pytest | **2450 passed / 2 failed / 2 skipped**（2 failed 为既有环境缺陷；另 1 条 `test_bdd_13_6` 在 workflow 改动**提交前**必然失败——它断言既有 workflow 无未提交改动，提交后即绿，评审已确认其历史条款清白） |
| consistency | **0 ERROR / 386 WARNING**（与基线一致） |
| ruff | 全绿 |
| 兜底自检（真实树，含本改动集） | **exit 0** |
| 负向控制 | 目录级 pathspec → 恰 2 条新回归判据转红；掏空检测 → 6/7/8 红；删 workflow 步 → 1/2/3 红 |

## 遗留与诚实说明

- **评审事故导致 3 处改动丢失并已重做**：`implementer.md`、`test_t42_p3_platform_selfcheck.py`
  头注、`CHANGELOG.md` 的「同类扫描修掉两处已失效陈述」行。重做后已重新验证（见上表）。
  该事故与「评审者需只读、scratch 须在仓外」的流程缺口已如实登记，**本次未单方面改动评审流程**。
- **criterion 第 ③ 条的残余不确定性**：本机只能证「干净树不误报」与「合成仓上污染必被捕获」，
  **真在 CI 上推一次污染提交反证**未做（不会为验证故意让 CI 变红）。已如实写入 closure_note，
  未以「已完整验证」表述。
- **criterion 第 ④ 条「全量 pytest 全绿」**：本改动集提交后 CI 应为绿（`test_bdd_13_6` 的红
  纯由未提交状态造成）。**本地仍有 2 个既有环境失败**（`opencode` 不在 PATH / 跨设备链接），
  与本批无关，未伪称本地全绿。
- **未做**：`RM-AG0071/0072/0073`（效率类，需先出设计）。
