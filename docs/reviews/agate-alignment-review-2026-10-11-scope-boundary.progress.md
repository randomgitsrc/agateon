# 留痕 scope-boundary 2026-10-11（r2 复核轮，原始痕迹，不整理）

- [角色文件] /home/kity/.agate/v0.82.0/agate/assets/review-roles/protocol-alignment-review.md — A1-A8(+A4b) 清单、只读纪律（RM-AG0081）、BDD-8 写前防误覆盖。
- [git status] 首见 7 文件（r1 快照）→ 评审中演进到 10 文件：+ `agate/SETUP.md`、`agate/tests/unit/test_setup_agate_dir.py`、`docs/design-notes/platform-extension-research.md`（主 Agent 边改边修）。HEAD == origin/main == 5de0ac8a（本批全为未提交工作区改动）。
- [reviewed_diff_sha1] `git diff | sha1sum` = e513daa1d32ba9139e364cfb3d27221764ec5b53（r2 快照）。
- [r1 报告] docs/reviews/agate-alignment-review-2026-10-11-scope-boundary.md 已存在（r1：7 文件版，MISALIGNED=2 → needs-revision）。同 task_id 同日 ⇒ BDD-8 判为复核轮，可覆盖。

--- r1 闭合核验（本轮独立实测）---

- [M1 闭合] `git diff docs/design-notes/platform-extension-research.md`：L1 标题改「第四运行时扩展素材」、L3 增「未排期（无当前需求驱动…）」、3 处「对 RM-AG0034 的含义」→「对该扩展的含义」。live grep RM-AG0034（排除 .git/.worktrees/docs/reviews/tasks）= 0 命中 ⇒ 闭合。
- [M2 闭合] roadmap `git diff`：RM-AG0036 行删除 + RM-AG0022 行去「与 RM-AG0036 双语锚点依赖本条目」。live grep RM-AG0036 = 0。行数 `grep -c '^| RM-AG'`：109→108；状态分布 backlog 12→11（其余 88 done / 5 scheduled / 4 cancelled 不变）⇒ 仅删 1 backlog。
- [N1 闭合] roadmap 范围节「做什么」第 3 条后新增：「> 通则（边界判定…）见 AGENTS.md「变更分诊」节；本节只列本项目当前的具体取舍。」
- [N2 闭合] AGENTS.md 处置规则 hotfix 句改为指针：「…走哪条通道以「改动通道」节的 hotfix 三条件为准（本节不重述条件，避免两份口径漂移）」。
- [N3 闭合] AGENTS.md:40 改为「DEBT0073 定下口径后，其构造性边界残差被登记成 DEBT0075，差点又走一轮实现 + 评审 —— 零用户价值」（去掉「两轮评审 + PR」的原归属）。

--- r2 新面 ---

- [悬空引用全扫] RM-AG0033/0034/0036/0047 live（排除 .git/.worktrees/docs/reviews/agate-workspace/tasks）= 全 0；DEBT0075 live = 1（AGENTS.md:40 有意先例）。
- [冻结面] `agate-workspace/tasks/TAG0041-platform-hygiene/P0-brief.md:120,144` 仍引 RM-AG0034（冻结任务记录，允许）；`.worktrees/blog-post11/` 旧副本（另一分支，非本工作区）。
- [计数] roadmap 无总计/汇总行 ⇒ 删行不需同步；4 条被删 RM「关联任务」列均 `—` ⇒ 不触 check-gate `_check_roadmap_done`。
- [A1 新 MISALIGNED] AGENTS.md「同一议题最多 1 轮独立评审」vs protocol-alignment-review.md L120-126「MISALIGNED → 必须修复 → 修完重审」+「未确认的 NEEDS_HUMAN_REVIEW 等同 MISALIGNED」。本批 r1→r2 即第 2 轮，自证冲突。
- [A4 全量实跑] `pytest agate/tests/ -q -n auto -p no:cacheprovider` → **3007 passed, 2 skipped in 144.91s**；`test_tag0051_self_gate.py` → 15 passed；`test_setup_agate_dir.py` → 7 passed（opencode 在 PATH：/home/kity/.opencode/bin/opencode）。
- [A4b] test_setup_agate_dir 有意放宽：`assert "opencode debug agent orchestrator" in sec` → `assert has_v1 or has_v2`；v2 分支退化为 `debug agents` + 文件级 name:/mode: 校验，去掉 v2 的 tools.task 断言（模板不声明 tools）。无其他意外转红。
- [A5] gate 行为无影响；CHANGELOG [Unreleased] 仅 DEBT0073/0074，未含 SETUP.md v2 修复 ⇒ N2。
- [A8] `git log --all` 解析：行首 skip=160、行首 review=365、同时含两者=**0** ⇒ 「真实提交从未出现」成立；`check-debt.py` rc=0、`grep -c '^## DEBT'`=74、open=0；roadmap 行数 108。
- [consistency] `check-protocol-consistency.py` rc=0（433 冻结 WARNING，未增）。
- [污染核验] 评后 `git status --porcelain` 与评前一致（仅 10 tracked + 2 本报告文件）⇒ 只读未脏化。
- [BDD-8] 目标报告文件已存在且 task_id 一致、同日 ⇒ 判复核轮，可覆盖，已写 r2。

[r2 结论] r1 的 M1/M2/N1/N2/N3 全部闭合；新增 M1（轮次上限 vs 角色闭环冲突）+ N1/N2/N3 ⇒ needs-revision。

## r2 复核（5 项处置 + 并发两文件）实测
- M1：`docs/design-notes/platform-extension-research.md` grep RM-AG0033/34/36/47 = **0** ✓；替换为中性表述（"第四运行时扩展素材"/"对该扩展的含义"/"本扩展"）+ 明确"未排期（无当前需求驱动…）" ✓ 无过度声称
- M2：roadmap RM-AG0036 行已删；RM-AG0022 行改为"RM-AG0031 写时校验依赖本条目"（去掉 0036）✓；live 残留仅冻结面（tasks/ + reviews/ + 我的报告）
- N1：roadmap「范围」节新增指路行 → 通则见 AGENTS「变更分诊」们；本节只列本项目具体取舍 ⇒ 单权威 ✓
- N2：AGENTS 处置规则改为指路（以「改动通道」三条件为准，不再重述）✓
- N3：先例句去数字 → "DEBT0073 定下口径后，其构造性边界残差被登记成 DEBT0075，差点又走一轮实现 + 评审 —— 零用户价值" ✓ 无未验证数字
- live 残留（RM 四者，排除 .git/.worktrees/tasks/reviews/CHANGELOG）= 空 ✓；roadmap `^| RM-` = **108** ✓
- 我自跑 consistency：0 ERROR（433 frozen WARNING 属设计） ✓
- 我的 pytest 实跑：`test_setup_agate_dir.py` = **7 passed**；单 `test_bdd_43` = 1 passed；早前 `test_tag0051_self_gate.py` = 15 passed

## 并发两文件（SETUP / test）核
- `opencode --version` = **v2.0.23**；`opencode debug --help` 子命令 = **agents/config/paths**（无 `agent <name>`）
  ⇒ SETUP"v2 起 debug agent <name> 已移除"**属实** ✓
- `agate/orchestrator-template.md` frontmatter = name: orchestrator / mode: primary / **无 `tools:` 块**
  ⇒ SETUP"tools.task 不是模板声明的字段"**属实** ✓；测试 v2 分支只断 `name:`/`mode:` 文件事实 ✓
- 探针：项目级 `.opencode/agents/orchestrator.md` 存在时 `opencode debug agents` **不列出**它 ⇒ SETUP"不保证列出项目级自定义 agent"**属实** ✓
- SETUP OpenCode 节 [0] bash 块仍是注册块（mkdir/ln）⇒ `_bash_blocks(sec)[0]` 断言不受新 v2 块影响 ✓
- 三问自洽：① 真实使用面（v2 用户按文档验证必失败）✓ ② 改变判定（本机曾恒红→绿）✓ ③ 本仓可解 ✓

## 非阻塞提示（按批内三问 §2「只改呈现⇒不管」判为可不改）
- `agate/SETUP.md:168`（Claude 节）仍以"OpenCode `opencode debug agent <name>`"作类比——该命令 v2 已移除，类比略陈旧（纯呈现）
- `agate-workspace/debt/tech-debt.md:642`（open 债的展开注）仍记"(4) 全量 pytest（本机 1 项环境失败——opencode CLI debug agent 漂移）"——本批已修，该记录变陈旧（记录级）
- CHANGELOG [Unreleased] 未为本批 SETUP v2 修复加行（可选；非协议语义）

## r2 结论
- 5 项处置**全部闭合**（M1/M2/N1/N2/N3）；并发两处（SETUP/test）**如实且可执行**、无过度声称。
- 最终 verdict = **approved**（残余 3 项为呈现层观察，按批内三问 §2「呈现⇒不管」不构成 MISALIGNED）。
