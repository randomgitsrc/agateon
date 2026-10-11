---
review_date: 2026-10-11
reviewer: protocol-alignment-review
change_summary: "批次 hotfix-debt-0065-0066：① check-mvwu._default_branch_base 改为复用单源 agate_common.default_branch（DEBT0065）；② gate_p0 声明校验改按 task_dir 推项目根再传 cwd=（DEBT0066）。两条 low 债务关单。"
files_changed:
  - agate/scripts/check-mvwu.py
  - agate/scripts/check-gate.py
  - agate/tests/unit/test_check_mvwu.py
  - agate/tests/unit/test_agate_config.py
  - agate-workspace/debt/tech-debt.md
  - CHANGELOG.md
---

# 协议-脚本对齐审查（DEBT0065 / DEBT0066 hotfix 批次）

**被评审状态**：分支 `hotfix/debt-0065-0066`，**未提交**（6 文件在工作区，`git diff` 可复核）。
**只读纪律**：本审查全程只读原仓（`git status --porcelain` 复核仅 6 个改动 + 本报告/留痕文件）；
所有实跑（pytest / 突变 / 差分 / ruff / 写类工具）均在副本 `/tmp/opencode/debt6566/corpus`（tar 副本，
排除 `site/`）上进行，跑完未触碰原仓。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（附 2 处 minor 文案漂移，见下） |
| A2 | 脚本→文档对齐 | ALIGNED（协议文档无需改；`scripts/README.md` 条目仍准确） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（A3b：带斜杠默认分支名的**窄回归**未被命名、无守护） |
| A4 | 测试覆盖 | ALIGNED（2 条新用例可用、突变转红；但 DEBT0065 守护仅源码面，见 A4 详情） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（**无既有用例转红**，见实测） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED**（minor：`CHANGELOG.md` 出现连续两个 `### 修复`） |
| A6 | 锚点表覆盖 | ALIGNED（CHECK 9 实跑 PASS，无需改表） |
| A7 | 设计原则一致性 | ALIGNED（与 ADR-014「判据单源」一致） |
| A8 | 声称-命令绑定 | ALIGNED（逐条见下；无无据声称） |

**总体**：**不可 commit**，直至处置 A3b 与 A5 两项（均低成本；机器门禁本身全绿）。

---

## 逐项审查

### A1: 文档→脚本对齐

**协议面**：本批无新增/变更协议规则条文（改的是脚本实现与债务记录）。两条债务的
`recommendation` 就是本次落地的口径，逐条对齐：

- DEBT0065 recommendation（`agate-workspace/debt/tech-debt.md`）：
  > 评估是否可统一为「`default_branch()` 给分支名 → 调用方自组 ref」
- 实现（`agate/scripts/check-mvwu.py:296-332`）：
  > `from agate_common import default_branch as _db` → `cands += [f"refs/remotes/origin/{_name}", f"refs/heads/{_name}"]`

**结论**：ALIGNED。两处 minor 文案漂移（非语义）：

1. `check-mvwu.py:330` 的失败原因串仍是 `"baseline: no default branch (origin/HEAD, main, master)"`——
   新实现实际候选是 `refs/remotes/origin/<name>` / `refs/heads/<name>` / `refs/heads/main` /
   `refs/heads/master`，`origin/HEAD` 只经单源间接使用。建议改为
   《`origin/<name>, <name>, main, master`》。
2. `check-mvwu.py:296-311` 的 docstring 描述了「远端优先 → 本地回退」，但**未提**末尾
   `main`/`master` 兜底是与 `_name` 无关的**无条件**追加项。措辞已足够读者自明，仅建议补一句。

### A2: 脚本→文档对齐

扫描协议文档有无需要同步的「默认分支解析」或「gate_p0 声明校验」描述：

- 命令：`grep -rn "默认分支" agate/*.md agate/**/*.md` → 命中集中在 `UPGRADING.md`（讲 v0.80.0
  `agate-ci-verify` 的 `origin/<默认分支>`，**与本批无关**）。`check-mvwu` 的默认分支候选顺序在
  任何协议文档中**均无**描述 ⇒ 无文档需改。
- `agate/scripts/README.md:93`（check-mvwu 条目）与 `agate/tests/README.md:96`（覆盖度映射）
  描述的是「观测器 / 不阻断 / 7 列」——本批未改这些语义 ⇒ 无需更新。

**结论**：ALIGNED。

### A3: 一致性连锁 + 反向传播

**A3a（已知连锁）**：
- 三处默认分支消费方现均为单源：`agate-changes.py:25-27,125`、`agate-ci-verify.py:76-79,116-122`、
  `check-mvwu.py:308`。复核命令：
  `grep -rn "refs/heads/main\|refs/heads/master\|origin/HEAD" agate/scripts/*.py` →
  仅剩 `agate_common.py:1291-1309`（权威源）与 `check-mvwu.py:300,301,330`（**注释/提示串**，
  无解析逻辑）⇒ DEBT0065 的「全仓无第三份副本」成立。
- `--observe` 的数据语义**确实变了**（新：`refs/remotes/origin/<name>` 优先；旧：`origin/HEAD`
  之后**直接**用本地 `refs/heads/main|master`，**完全忽略** remote-tracking refs）。已在
  `check-mvwu.py:300-303` docstring 与 CHANGELOG 显式命名（"远端优先"），属**有意收敛**。
  差分实测（见「重点 1」表）确认受影响面仅「有 `origin/<name>` 但无 `origin/HEAD`」一种。

**A3b（主动推断：应被影响但未在 diff 中的文件）**：

| 推断的受影响面 | 实测影响 | 处置 |
|---|---|---|
| `agate_common.default_branch` 的**截断缺陷**（`:1304 out.split("/")[-1]`）被 check-mvwu 新依赖放大 | **命中**：默认分支名含 `/`（如 `feature/foo`）时 `default_branch` 返回 `foo` ⇒ check-mvwu 由「旧：正确 base」退化为「新：`None` + `no default branch`」 | **未命名、无守护 ⇒ MISALIGNED** |
| `agate-changes.py` / `agate-ci-verify.py` 口径一致性 | 一致（同调单源；`agate-ci-verify` 直接用 `origin/<name>`，与 check-mvwu 新口径同向） | 无需改 |
| worktree 场景（`.git` 是文件） | 实测 `--show-toplevel` = **worktree 根**；声明从 worktree 根读（删 worktree 内声明即出 WARNING，主 checkout 声明不兜底）——对受版本控制的 `agate.config.yaml` 无影响；若某项目将其 gitignore 且只存在于主 checkout，则新旧**同为** WARNING（旧：cwd=worktree；新：toplevel=worktree）⇒ **无回归** | 无需改 |
| `SELF-GATE.md` 触发面 / 提交信息 | 本批含 `agate/scripts/*.py` ⇒ 触发 SELF-GATE（本审查即其义务）；commit 信息须含 `self-gate-review:` 指向本报告 | 留痕提示 |

**结论**：**MISALIGNED**（A3b 第一行）。差异与建议：

- **差异**：`check-mvwu._default_branch_base` 对「默认分支名含 `/`」的仓库出现行为回归
  （旧 `('386108cd…', None)` → 新 `(None, 'baseline: no default branch …')`），该差异**既未在
  docstring/CHANGELOG 命名，也无守护用例** ⇒ 不满足 DEBT0065 `closure_criteria` 的
  「差异被显式命名 + 有等价守护用例」。
- **根因**：单源自身的 `split("/")[-1]` 取错（`refs/remotes/origin/HEAD` 前缀恒为 `origin/`，
  故正确写法是 `split("/", 1)[-1]`）。该缺陷**同样**影响 `agate-ci-verify.py`（`origin/foo` 解析失败）
  与 `agate-changes.py`——属**既有缺陷**，本批只是把它引入 check-mvwu（此前 check-mvwu 是好的）。
- **建议（二选一，均低成本）**：
  ① **推荐**：一行修权威源 `agate_common.py:1304` → `out.split("/", 1)[-1]`，并加一条用例
  （放 `test_agate_ci_verify.py` 或公共处）锁 `feature/foo` 场景——顺带修好另两个消费方；
  ② 若本批不想动单源：在 `check-mvwu.py` docstring 显式命名该已知偏离 + **登记新 DEBT**（给 owner），
  并在 teardown 说明「DEBT0065 关单以 ① 或 ② 为前提」。

### A4: 测试覆盖

**新增用例（2 条）**：
- `agate/tests/unit/test_check_mvwu.py:1107 test_debt0065_default_branch_is_single_source`
  ——**源码面**断言 `"symbolic-ref" not in src` 且 `"default_branch" in src`。
- `agate/tests/unit/test_agate_config.py:439 test_debt0066_gate_p0_uses_task_project_root_not_cwd`
  ——行为面：项目 A（无声明）+ 调用方 cwd=B（有声明）⇒ 须出 WARNING。

**突变测试（判别力，独立跑）**：在副本上按 `git show HEAD:` 还原两处修复后**只跑这 2 条**：

```
FAILED test_check_mvwu.py::test_debt0065_default_branch_is_single_source
FAILED test_agate_config.py::test_debt0066_gate_p0_uses_task_project_root_not_cwd
2 failed in 0.17s
```

⇒ 两条用例**各自**对本次修复有判别力（抽掉修复即转红）。

**覆盖强度评注（非阻断）**：DEBT0065 的守护是**源码字符串**断言——它能防「退回自建解析」，
但**不能**防候选顺序/裁剪语义回归（本次 A3b 的 S5 回归、以及 S1 的"远端优先"变更，**均无用例覆盖**）。
若采纳 A3b 建议 ①，顺带补一条行为用例即可把这一类补上。

**最近一次全量实跑**（副本，CI 口径 `--reruns 1 -n auto`，命令与输出见 A4b/A8）：
`1 failed, 2916 passed, 3 skipped, 1 rerun in 106.54s`。

**结论**：ALIGNED。

### A4b: 闭合后既有测试转红 + 夹具更新清单（RM-AG0107 / DEBT0054）

**既有用例转红清单：无**（经实测）。证据 = 全量实跑：

```
$ cd /tmp/opencode/debt6566/corpus && python3 -m pytest agate/tests/ --reruns 1 -n auto -q
1 failed, 2916 passed, 3 skipped, 1 rerun in 106.54s   (EXIT=1)
```

唯一 failed = `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`，
**环境性**：本机 `opencode debug agent` 子命令已更名为 `agents`（`ERROR Unknown subcommand "agent"
for "opencode debug"`）；与本次 6 文件改动无关（改的都是 check-mvwu/check-gate，未碰
`agate-setup.py` / `install-hook.py` / opencode 注册路径）。**故本批不得声称「全绿」**。

**夹具更新清单：无**。两处既有 BDD-8 用例（`test_agate_config.py:368/397`）自带项目根
（`_project = td.parent.parent`，见其注释），在本批新逻辑下：`task_dir` 非 git 仓库 ⇒ 走**兜底 ②**
（最近含 `agate-workspace` 的祖先 = 同一 `tmp_path`）⇒ 与旧 cwd 行为**等价**，无需改夹具（实跑通过）。

**结论**：ALIGNED（空清单，已显式写出）。

### A5: 下游影响 + 文档传播

- **对已有项目 gate 行为**：`gate_p0` 退出码**恒 2 不变**（XP 场景实测 rc：旧 2 / 新 2；
  hook 路径 rc 亦 2）。声明缺失/非法仍只 WARNING、不阻断 ⇒ **无破坏性变更**。
- **文档传播**：协议文件无需改（见 A2）；CHANGELOG 已登记两条修复。
- **发现（minor）**：`CHANGELOG.md` `[Unreleased]` 下出现**连续两个 `### 修复`**（第 13 行与第 24 行）：

```
11:## [Unreleased]
13:### 修复        ← 本批插入的标题
24:### 修复        ← 原有标题（v0.81.0 发版期那条）
```

正确形态应为**合并为一个 `### 修复`**（新加两条 bullet 追加到既有节内）。仓库既有各版本节的
重复标题均为**不同类型**（修复/文档、变更/新增…），非同型重复 ⇒ 此为本批引入的格式缺陷。
机器门禁（CHECK 7 / CHECK 13）不检此项（实跑未报）。

**结论**：**MISALIGNED**（minor：删掉第 24 行的第二个 `### 修复` 标题即可）。

### A6: 锚点表覆盖

无新增协议规则、无新增/改名 `agate/scripts/` 文件 ⇒ CHECK 9 锚点表无需更新。实跑：

```
$ python3 agate/scripts/check-protocol-consistency.py --strict-errors-only   → rc=0
  ✅ PASS  CHECK 9  协议-脚本结构对齐
  仅有 432 个 WARNING，无 ERROR。
```

并**核验本批未新增 WARNING**：把 `CHANGELOG.md` 还原为 `HEAD` 版重跑，WARNING 总数同为 **432**
（CHECK 10 那 1 条 scriptref 为**既有**，与本批无关）。

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-014（判据单一权威源）**：本批正是把「默认分支」判据从三份收敛为一份（`agate_common.default_branch`），
  方向与 ADR-014 决策 ① 完全一致。
- **RM-AG0116（协议不假设项目分支）**：收敛后，check-mvwu 不再自带 `main|master` 假设表作为**主路径**
  （`main`/`master` 仅作兜底），与 `agate-changes.py` / `agate-ci-verify.py` 同向。
- 未发现需要新 ADR 的架构决策。

**结论**：ALIGNED。

### A8: 声称-命令绑定

本批**新增/变更的声称**逐条给命令：

| # | 声称（出处） | 命令 | 结论 |
|---|---|---|---|
| 1 | 「`_default_branch_base` 原自建 `symbolic-ref origin/HEAD` 候选表」（CHANGELOG:15 / debt:2697） | `git show HEAD:agate/scripts/check-mvwu.py \| grep -n symbolic-ref` | 成立（旧脚本含该行） |
| 2 | 「改为复用 `agate_common.default_branch()` 取分支名，再转候选 ref（远端优先→本地回退→main/master 兜底）」（CHANGELOG:16-18） | 读 `check-mvwu.py:305-318` + 差分驱动（重点 1） | 成立 |
| 3 | 「纯本地仓库仍可用」（CHANGELOG:18 / debt:2704） | 差分 S2「只有本地 main」→ OLD/NEW `SAME` | 成立 |
| 4 | 「守护用例锁源码面」（CHANGELOG:18） | 读 `test_check_mvwu.py:1107-1119` + 突变转红 | 成立 |
| 5 | 「全仓无第三份副本」（debt closure_criteria:2712） | `grep -rn "refs/heads/main\|refs/heads/master\|origin/HEAD" agate/scripts/*.py` | 成立（仅剩注释/提示串） |
| 6 | 「原 `agate-config.py validate` 按**进程 cwd** 找 `agate.config.yaml`」（CHANGELOG:20 / debt:2686） | 读 `agate-config.py:340 project_root = os.getcwd()` → `_cmd_validate`(:140) | 成立 |
| 7 | 「从项目外调用会校验**错的项目**（hook 里 cwd=仓库恰好掩盖）」（CHANGELOG:21） | XP 场景：cwd=B(有声明) 调 A 的任务 → OLD WARNING=0（漏报）/ NEW WARNING=1 | 成立 |
| 8 | 「按 `task_dir` 推项目根（git toplevel → 含 `agate-workspace` 的祖先 → cwd 兜底）再传 `cwd=`」（CHANGELOG:22） | 读 `check-gate.py:728-756`；① 路径=worktree 实测；② 路径=XP 实测；③ 路径=`task_dir` 不存在/无祖先 实测（逐字节同旧行为） | 成立 |
| 9 | 「回归用例覆盖跨项目场景（任务在 A、调用方 cwd 在 B ⇒ 按 A 判定）」（CHANGELOG:23 / debt:2749） | `test_agate_config.py:439` + 突变转红 | 成立 |

另复核**本报告自身**的声称：全量 pytest 计数、突变结果、差分表、ruff/consistency/count-tests
计数 —— 命令与输出见对应小节，均可复核。**无「无法给出命令」的声称**（故无需删除任何声称）。

---

## 重点 5 项结论

### 1. DEBT0065 是否真「收敛」且无回归 —— 四（+1）情形逐条实测

驱动脚本：`/tmp/opencode/debt6566/diff/drive.py`（对同一批临时 git 仓库分别调**旧**实现
（`git show HEAD:agate/scripts/check-mvwu.py`）与**新**实现）：

| 场景 | OLD | NEW | 差异 |
|---|---|---|---|
| S1 有 `origin/main`、无 `origin/HEAD`，且 `origin/main` 较新（本地 `main` 落后） | `('386108cd…', None)` | `('803d17b8…', None)` | **DIFFERENT**（远端优先 ⇒ base 由「本地 main 尖端」改为「`origin/main` 尖端」） |
| S2 只有本地 `main`（无任何 origin ref） | `('386108cd…', None)` | `('386108cd…', None)` | SAME |
| S3 既无 `main` 也无 `master`（默认分支叫 `trunk`） | `(None, 'baseline: no default branch (origin/HEAD, main, master)')` | 同左 | SAME（含**原因串逐字相同**） |
| S4 `origin/HEAD` → `origin/develop` | `('386108cd…', None)` | `('386108cd…', None)` | SAME |
| **S5** `origin/HEAD` → `origin/feature/foo`（**分支名含 `/`**） | `('386108cd…', None)` | `(None, 'baseline: no default branch …')` | **DIFFERENT = 回归** |

S5 根因佐证：`git symbolic-ref --short refs/remotes/origin/HEAD` → `origin/feature/foo`；
`agate_common.default_branch(该仓库)` → `'foo'`（截断），`refs/remotes/origin/feature/foo`
**可解析**（`git rev-parse --verify` 成功）⇒ 是「名字被截断」而非「ref 不存在」。

- **收敛性**：成立（全仓只剩一处解析逻辑，见 A3a grep）。
- **按 `--observe` 数据语义**：S1 是**有意**变更（CHANGELOG/docstring 命名为「远端优先」）；
  S5 是**未命名回归** ⇒ 见 A3b。
- **`from agate_common import ...` 放函数内（延迟导入）**：无功能隐患——`agate_common` 已在
  `check-mvwu.py:54` **模块级**导入，本处再导入不会引入新失败模式；`except Exception` 把潜在
  编程错误也吞掉（降级为「无单源名 → 走 main/master 兜底」），**不破坏**观测器（只读、不阻断）。
  仅**风格不一致**：两个兄弟消费方（`agate-changes.py:25-27`、`agate-ci-verify.py:76-79`）用
  **模块级 `try/except ImportError`**；建议同构（非阻断）。
- **去重与候选顺序**：`cands = [c for c in cands if not (c in seen or seen.add(c))]`
  语义正确（首现保留、重复丢弃；`name=="main"` 时 `refs/heads/main` 不会被追加两次），且
  「远端 → 本地同名 → main → master」顺序与 A3a 表一致——经 S2/S3/S4 端到端复核。

### 2. DEBT0066 的正确性与安全性

- **`cwd=` 传值失败/路径不存在**：`subprocess.run` 对不存在目录抛 `FileNotFoundError`
  （`OSError` 子类），被既有 `except OSError: validate_rc = 0`（`check-gate.py:759`）**吞掉** ⇒
  最坏是「不打印 WARNING」，**不会崩 gate**。且 `_proj_root` 两个来源（`realpath(show-toplevel)`、
  逐级祖先存在性检查）实际上**恒为已存在目录**，该分支不可达。
- **hook 路径逐字节不变**：实测（副本，`cwd=repo`、任务在 repo 内、`agate.config.yaml` 存在）：
  `diff -u old.out new.out` → **无差异**；rc 同为 2。另测「`task_dir` 不存在」→ 亦逐字节一致。
- **worktree 场景**：实测 `--show-toplevel` 返回 **worktree 根**（`.git` 为 file）；
  声明从 **worktree 根**读——删 worktree 内声明（主 checkout 仍在）→ **出 WARNING**（证明读的是
  worktree 根，而非主 checkout）。对受版本控制的 `agate.config.yaml` 无影响；与旧行为对比**无回归**。
- **`run_git is None`（公共库缺失）降级**：跳过 ①，落到 ②（含 `agate-workspace` 的最近祖先）；
  ② 也拿不到 ⇒ `None`（保持旧 cwd 语义）。**不崩**。⚠️ 风格：`check-gate.py:269 _git()` 已是
  「优先 `run_git`、缺库本地 `subprocess` 兜底」的封装，新代码直接调 `run_git` + `is not None`
  判断（该写法在文件内亦有先例，如 `:1420`），二者等价但**不统一**，建议改用 `_git`（非阻断）。

### 3. 测试判别力（独立突变）

见 A4。两条新用例**各自**在「抽掉对应修复」后转红（`2 failed`）⇒ 判别力成立。
补充评注：DEBT0065 用例为**源码面**断言，对「候选顺序/语义」零覆盖（S1 变更与 S5 回归均不漏检）——
若要给 A3b 的修法配守护，需补一条**行为**用例。

### 4. 债务关单是否成立（判据逐条核）

**DEBT0065**（criteria：收敛到单实现／或差异显式命名 + 等价守护；全仓无第三副本）
- 收敛 ✅；无第三副本 ✅（grep 见 A3a）。
- 「差异显式命名」：**部分**——S1（远端优先）已命名；**S5（带斜杠名）未命名**。
- 「等价守护」：❌——现有守护为**源码面**，非行为等价。
⇒ **关单暂不成立**，直到 A3b 的 ①/② 落地（① 一行 + 一条行为用例最简单）。

**DEBT0066**（criteria：以任务所属项目根为基准 + 跨项目回归用例）
- 行为 ✅（XP：旧 0 WARNING → 新 1 WARNING，rc 恒 2）；用例 ✅ 且突变转红。
⇒ **关单成立**。

**`check-debt.py`**：`python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **rc=0**（副本实跑）。
（`YAML 代码块可解析` / `文件引用存在` 亦由 check-protocol-consistency CHECK1/CHECK2 覆盖，未新增 ERROR/WARNING。）

### 5. A4b + A8 实跑数字

- 全量：`1 failed, 2916 passed, 3 skipped, 1 rerun in 106.54s`（`-n auto --reruns 1`，副本）。
  **1 条为环境性 failed**（`test_setup_agate_dir.py::test_bdd_43`：opencode `debug agent`
  子命令已改名 `agents`）——**不得称「全绿」**。
- `ruff 0.16.4 check`（4 个改动 py）→ `All checks passed!`（rc=0）。
- `check-protocol-consistency.py --strict-errors-only` → rc=0（432 WARNING，**既有**；还原 CHANGELOG 后同为 432）。
- `check-debt.py` → rc=0；`count-tests.sh` → **2920**（副本，含本批 +2）。

---

## 是否可 commit

**否——先处置 2 项（均低成本）**；处置后可 commit（附 SELF-GATE 留痕）。

必须处置：

1. **A3b / DEBT0065 关单（MISALIGNED）**——带斜杠默认分支名的窄回归。二选一：
   - ① 一行修权威源 `agate_common.py:1304`：`out.split("/")[-1]` → `out.split("/", 1)[-1]`，
     并补一条 `feature/foo` 行为用例（顺带修好 `agate-ci-verify` / `agate-changes`）；**推荐**；
   - ② 在 `check-mvwu.py` docstring 显式命名该已知偏离 + **登记新 DEBT（给 owner）**，
     并在 DEBT0065 的 `closure_note` 记明关单前提。
2. **A5（MISALIGNED，minor）**——删掉 `CHANGELOG.md:24` 第二个 `### 修复` 标题（合并为一节）。

建议（非阻断）：`check-mvwu.py:330` 失败原因串与 docstring 措辞同步（A1 minor）；
`check-mvwu.py` 的延迟导入与 `check-gate.py` 的 `run_git`/`_git` 用法与仓内既有范式统一（A3a minor）。

**commit 附加义务**：本批含 `agate/scripts/*.py` ⇒ 触发 SELF-GATE；提交信息须含
`self-gate-review: docs/reviews/agate-alignment-review-2026-10-11-DEBT-6566.md`（commit-msg hook 检查，
WARNING 不拦截但属留痕义务）。若按 ① 改动权威源，须**重审**本报告相关项。
