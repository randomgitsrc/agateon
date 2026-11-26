---
review_date: 2026-11-26
reviewer: protocol-alignment-review
change_summary: agate-doctor 诊断对象由「存在性」改为「效力」——hook 维度改问 git 实际执行的目录并判执行位，版本维度改走与 gate 同源的解析入口
files_changed:
  - agate/scripts/agate-doctor.py
  - agate/tests/unit/test_agate_doctor.py
  - agate/LIMITATIONS.md
  - docs/guides/project-map.md
  - CHANGELOG.md
branch: fix/doctor-hook-veracity
head_at_review: 7e3e0129df34cffa77ca44a870e61be9086d7b25
verdict: ALIGNED_WITH_FOLLOWUPS
blocking_count: 0
---

# 协议-脚本对齐审查 — HOTFIX-DOCTOR-01

## 0. 意图（比 diff 更重要）

`agate-doctor` 这个诊断工具此前报的是**「我以为的状态」而不是「gate 实际的状态」**：hook 维度只看
`<repo>/.git/hooks` 里有没有同名文件，版本维度只回显 env 或「脚本自己住在哪个 checkout」。
于是它在两类真实场景里给出**与事实相反**的结论——（a）hook 全在位但都不可执行时，
git 静默跳过、`git commit` 照常成功，doctor 却报 `[OK] … 全部维度正常`（gate 全哑而诊断判绿）；
（b）链接 worktree 里 `.git` 是文件、hook 明明生效，doctor 报「非 git 仓库」。
本批把这四个维度的判据一律换成**问权威源**：位置问 git（`git rev-parse --git-path hooks`）、
版本问解析链（与 hook 入口同一个函数）、效力判执行位。

**这是一次「让诊断工具说的话与 gate 实际行为同源」的修正，不是新增能力**——所以走 hotfix 通道、
不立项，是恰当的（单一主题、可快速验证）。

## 1. 审查对象快照说明（重要，影响本报告如何被读）

审查期间作者**持续在同一 worktree 上追加修复**（本评审的部分发现被即时采纳）。因此存在两个快照：

| 快照 | 标识 | 状态 |
|---|---|---|
| **S0 暂存版** | `git ls-files -s` → `agate-doctor.py` blob `efd2735a`、测试 `e82c2abb` | 我已逐行审过（§A1–A8 的「S0」标注） |
| **S1 工作区版** | 加上未暂存修改（`git status` 显示 `MM`），末态 `agate-doctor.py` md5 `48064dc2`、测试 md5 `345df392` | 17 passed；本报告结论以 S1 为准 |

**发现 C1（下述）在 S0 中成立、在 S1 中已被修复**。为避免读者把已修项当未修项，A1/A4 分别标注了
两个快照的结论。**提交前请确认 `git add -A` 把未暂存修复一并纳入**——当前 `git status` 为 `MM`，
若只提交暂存区，落地的仍是含 C1 的 S0。

> 附加事实：16:44 前后该文件曾出现 `IndentationError`（`agate-doctor.py:112`），属编辑中瞬时态，
> 45 秒后消失（15 passed）。**不是提交态缺陷**，仅记录以免读者用中间态复核。

## 2. 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED**（S1）／S0 有 1 处 MISALIGNED（C1，已修） |
| A2 | 脚本→文档对齐 | **MISALIGNED**（仅剩 1 处：`CHANGELOG.md` 的「逐字一致」遗留已删，但见 M-1） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（反向传播 6 个面逐一实测，无漏改） |
| A4 | 测试覆盖 | **ALIGNED**（17 passed；回退实验独立复现 7 条转红；M-2/M-3/M-4 已在审查期间被作者补齐） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**——经实测**无既有用例转红**，空夹具清单（显式） || A5 | 下游影响 + 文档传播 | **ALIGNED**（无破坏性；真实下游 PeekView 实跑对比，判定未变） |
| A6 | 锚点表覆盖 | **ALIGNED**（实测无需动 `SCRIPT_ALIGNMENT_ANCHORS` / `GATE_SCRIPT_EXEMPT`） |
| A7 | 设计原则一致性 | **ALIGNED**（ADR-004 / ADR-011 / ADR-014） |
| A8 | 声称-命令绑定 | **MISALIGNED**（3 条声称已自查并自行收敛；1 条「逐字一致」曾被删，见 A8 表） |

**总判定：ALIGNED_WITH_FOLLOWUPS — 0 BLOCKER，1 MINOR（M-1 文档索引行）+ 1 NEEDS_HUMAN_REVIEW（N-1 死代码）。
其余发现问题（C1、M-2、M-3、M-4）已在审查期间被作者修复并各自补齐用例。**

## 3. 逐项审查

### A1: 文档→脚本对齐

**文档声明**（`agate/scripts/agate-doctor.py:11-12`，S1 现状）：
> 3. 版本解析：报 **gate 实际会用的那个** `AGATE_ROOT`——以 `resolve_hook_root()`（gate 入口
>    `resolve-entry.py` 走的同一个函数）为准，并附上 `resolve_version_root()` 的解析链结论

**脚本实现**（S1，`agate-doctor.py:164-184`）：
> `chain = agate_common.resolve_version_root(project_root)` / `hook_entry = Path(git_hooks_dir(...))/"pre-commit"` →
> `hook_entry.resolve()` → `resolve_hook_root(hook_entry)` / `root = chain_root or hook_root`

**结论：ALIGNED（S1）**。三处同源均已核实：
- hook 位置：`agate_common.git_hooks_dir()`（`agate_common.py:92-118`）= `git rev-parse --git-path hooks`
  + `clean_location_env=True` 中和 `GIT_DIR`，与 `install-hook.py` / `agate-setup.py` **同一个函数** ⇒ 安装侧与诊断侧不可能再分叉（ADR-014 要求的单源）。
- 版本：`resolve_hook_root` 正是 `resolve-entry.py:26` 调的函数 ⇒ doctor 与 hook **同一入口**。
- 执行位：POSIX 判 `os.access(X_OK)`，Windows 显式不分叉（`os.name != "nt"` 守卫），与 git 实际判据一致。

**S0 的 MISALIGNED（C1，已在 S1 修复）**：S0 只用 `resolve_version_root()`，而 gate 实际走
`resolve_hook_root()`——后者**多一层「脚本路径上溯 + `.agate-root` 标记」兜底，恒返回非空 root**。
实测（`AGATE_HOME` 指向空目录、不设 `AGATE_ROOT`）：

```
resolve_version_root -> {'root': None, ...}          # 解析链无结果
resolve_hook_root    -> ('<checkout>/agate', [])     # hook 照样跑得动
```

⇒ S0 的 doctor 会在「gate 跑得动」的环境里报 `[!!] 无可用 AGATE_ROOT`，**正好是本次要消灭的那类
镜像缺陷**（把「链没结果」当成「gate 没 root」）。S1 改为 `resolve_hook_root` 并新增对应用例，正确。
`resolve_hook_root` 恒非空还使 S0 的 `if not root:`（原 `:162`）成为死代码——S1 已移除该分支。

### A2: 脚本→文档对齐

**结论：MISALIGNED（1 处 MINOR，措辞面，不阻断）**

| 文档 | 行 | 现写 | 实际 | 判定 |
|---|---|---|---|---|
| `agate/scripts/README.md` | 131 | 诊断项目接入状态（声明文件 / git hook / **版本解析** / 账本完整性） | hook 维度语义已由「是否装了」变为「git 会不会执行它（在位+可执行+非断链）」；版本维度已由「回显」变为「与 gate 同源的解析结果 + warnings」 | **可辩护不构成漂移**——该行是**维度枚举**（四个维度名未变），不描述判据强度。维度名仍是「git hook」「版本解析」，故未失真。若要求更严，可把「版本解析」改为「版本解析（与 gate 同源）」——**建议但非必需** |
| `agate/UPGRADING.md` | 752-756 | 「新增 `agate-doctor` 命令：诊断项目接入 / 环境状态；退出码固定」 | 仍然准确（rc 恒 0 未变，维度集合未变） | **无需同步**——该节是 v0.79.0 的**历史发布记录**（`### v0.79.0 — TAG0042 批 1`），按本仓「历史节只作记录」的既有口径不回改 |
| `agate/scripts/agate-doctor.py` 模块 docstring | 11-12 | 已改为 `resolve_hook_root` 为准 | 与 S1 实现一致 | **ALIGNED**（作者已同步） |

**M-1（MINOR，建议）**：`agate/scripts/README.md:131` 的「版本解析」+ 该行副标题「+ 对异常项给出可执行
修复指引」未反映**新增的 `[!!]` 语义**——版本维度现在会因「声明未安装」而判异常。该行不描述判定强度，
故不判 BLOCKER；但 doctor 的**可观测行为**确实变了（见 §4 判据判断）。建议在该行括注
「版本解析（与 gate 同源，解析链告警判 `[!!]`）」，使索引行的承诺与实际输出对齐。

### A3: 一致性连锁 + 反向传播

**结论：ALIGNED**。按意图主动推断的「应被影响」文件，逐一实测：

| # | 应被影响面 | 是否在 diff | 实测结果 |
|---|---|---|---|
| 1 | `agate/scripts/README.md`（脚本索引，A3 常见路径） | ❌ 未改 | 见 A2/M-1：维度枚举未变，**不构成失真**；建议括注 |
| 2 | `agate/tests/README.md:68`（脚本→测试映射） | ❌ 未改 | 映射行 `agate-doctor.py → unit/test_agate_doctor.py` 仍准确（文件未改名/未增删） ⇒ **无需改** |
| 3 | `docs/guides/project-map.md`（时变数字） | ✅ 已改 | 见 A8：原「约 60」实测当时=61、今=85 ⇒ 改动成立 |
| 4 | `agate/LIMITATIONS.md` 抬头 | ✅ 已改 | 见 A5：与两 README 不矛盾，反而三方收敛 |
| 5 | `agate/UPGRADING.md:752-756` | ❌ 未改 | 历史节，**正确不回改**（见 A2 表） |
| 6 | 断言旧行为的字符串（「全部维度正常」/「已安装（pre-commit」） | — | 全仓 grep：仅 `agate-doctor.py` 自身、新测试、CHANGELOG。**无其它文件断言旧行为** |
| 7 | `check-protocol-consistency.py` 锚点表 / 豁免表 | ❌ 未改 | 见 A6：实测不需要 |
| 8 | CI workflow / `agate/*.md` 协议文档 / SETUP / platform-notes | ❌ 未改 | 全仓 grep `agate-doctor`：CI 0 命中、协议文档 0 命中 ⇒ **doctor 不在任何 gate 路径上**，传播面天然很小 |

**值得记录的正面证据**：本批修的两条缺陷早在 `TAG0042 P4-review.md:474-483` 就以
`[INFORMATIONAL-3] 只查 <root>/.git/hooks，漏 worktree / core.hooksPath` 与
`[INFORMATIONAL-5] 只回显字符串，未解析版本链` 被记录，当时判「非阻断」。本次是**历史遗留的闭合**，
不是新引入的问题——这与 hotfix 定位一致。

### A4: 测试覆盖

**最近一次实跑输出**（`timeout 600 python3 -m pytest agate/tests/unit/test_agate_doctor.py -q`，S1 末态）：
```
.................                                                        [100%]
17 passed in 0.86s
```
（快照演进：S0 `13 passed` → S1 首轮 `15 passed` → S1 末态 `17 passed`。增量全部来自作者
按本评审 A4/A1 发现即时补的用例：C1 修复 1 条、C1 残余 1 条、断链 1 条、内容不阻断 1 条。）

**回退实验——独立复核用户说法（成立，且随快照变强）：**

在**一次性副本**上（`cp -a` 到 `mktemp -d`，同一次 bash 调用内创建+操作+清理），把
`agate-doctor.py` 换回 `HEAD` 版、测试保留新版：

```
7 failed, 10 passed
FAILED test_doctor_reports_broken_when_hooks_not_executable
FAILED test_doctor_uses_git_hooks_dir_under_core_hookspath
FAILED test_doctor_uses_git_hooks_dir_in_linked_worktree
FAILED test_doctor_version_reports_what_gate_actually_resolves
FAILED test_doctor_uses_installed_hook_entry_for_fallback_root
FAILED test_doctor_reports_broken_symlink_hook
FAILED test_doctor_does_not_claim_hook_content_blocks
```

反向守护单独跑（同一回退态下）：
```
1 passed, 14 deselected      # test_doctor_executable_hooks_stay_ok
```
⇒ **「回退 doctor.py 时多條转红、反向守护仍绿」属实**。用户说 4 条转红，在 **S0** 快照下正是 4 条
（`not_executable` / `core.hooksPath` / `linked_worktree` / `version_resolves`）；S1 增至 7 条。
**结论一致，数字随快照增长，非矛盾。**

**未覆盖的失效模式（我独立构造并实测，逐条给结论）：**

| # | 失效模式 | 实测行为 | 是否有用例 | 判定 |
|---|---|---|---|---|
| 1 | hook 是软链但目标不存在（断链） | `[!!] hook: 断链 pre-commit, commit-msg, pre-push〔<dir>〕` ——**代码已正确报** | ✅ **已补** `test_doctor_reports_broken_symlink_hook` | **已闭合**（审查中补齐） |
| 2 | hook 存在、可执行、但内容为空文件（0 字节） | `[OK] hook: 已安装且可执行`；措辞显式声明「判的是 git 会不会执行它，不含其内容是否真能阻断」 | ✅ **已补** `test_doctor_does_not_claim_hook_content_blocks` | **已闭合（按「诚实呈现」而非「判据收严」）**——doctor 不再过度声称；`[OK]` 仍保留（合理：git 确实会执行它） |
| 3 | hook 可执行但不**是** agate 薄壳（任意 `#!/bin/sh; exit 0`） | 同 #2 —— 实测 marker 证明 git 确实执行了它，但 gate 无效；S1 措辞已诚实收窄 | ✅ 被 #2 的用例间接覆盖（同一「不声称能拦」契约） | **已闭合（呈现层）**。若要收严到判据层（校验内容含 `resolve-entry`）属新增判据，按仓内「新增判据须先答能拦下几个真缺陷」口径，**建议不在此 hotfix 内做** |
| 4 | `agate_common` 不可用时的 fallback 分支 | **实测为死代码**：`agate_common.py:35-39` 在 `import yaml` 失败时执行 `sys.exit(1)`，抛 `SystemExit`，**`except Exception` 抓不到**。实测（`PYTHONPATH` 注入坏 `yaml.py`）：OLD 与 NEW 均 `rc=1`，只打印 3 行标题后中止 | ❌ 无 | **NEEDS_HUMAN_REVIEW（N-1）**：先于本批存在的缺陷，但本批**新增了两段基于它的 fallback 文案**（`_diagnose_hooks` 的「回退 .git/hooks（agate_common 不可用：…）」、`_diagnose_version` 的「解析链不可用（…）」），两处**永不显示**。且该场景 rc=1 违反 BDD-17「rc 恒 0」 |
| 5 | Windows 分支 | `os.name != "nt"` 守卫使执行位判定在 Windows 跳过；相关用例 `pytest.skip` | ✅ **已补** 文件第 1 个用例加 `@pytest.mark.windows_smoke`（实测 `-m windows_smoke` → `1 passed, 16 deselected`） | **已闭合** |

### A4b: 闭合后既有测试转红 + 夹具更新清单

**结论：ALIGNED——空清单（显式写出）**

经实测**无既有用例转红**，**无夹具需要更新**。依据：
1. `pytest agate/tests/unit/test_agate_doctor.py -q` ⇒ 15 passed，其中原有 8 条 BDD-17 用例（含
   `test_bdd_17_doctor_reports_hook_status`）全绿——它们断言的是「输出含 hook/版本等关键字」，
   未锁定旧措辞（旧措辞「已安装（pre-commit…）」改为「已安装且可执行（…）」不影响这些断言）。
2. 全仓 grep 引用 `agate-doctor` / `_diagnose_hooks` / `_diagnose_version` 的**测试文件仅 1 个**
   （`agate/tests/unit/test_agate_doctor.py`），无第二处测试消费 doctor 输出。
3. `count-tests.sh`：HEAD `3037` → 工作区 `3043`（`+6`），与「新增 5 条(S0) + 1 条(C1) + 1 条(C1 残余)」
   一致，**无既有用例被删除或改名**。
4. 夹具：本批未改 `agate/tests/conftest.py`；新用例复用既有 `git_repo` / `agate_scripts` /
   `python_exe` / `run_cli` / `agate_root` fixtures（`agate-doctor` 无新 fixture 需求）。

### A5: 下游影响 + 文档传播

**结论：ALIGNED（无破坏性变更）**

- **CHANGELOG 已标注**：`[Unreleased]` 下 `### 修复` 两条 + `### 文档` 两条，均标「走 hotfix 通道，不立项」。
- **真实下游实测（PeekView，`/home/kity/oclab/peekview`，装着 agate hook、有 10 个账本）**：

  | | OLD doctor（HEAD） | NEW doctor（S1） |
  |---|---|---|
  | 声明文件 | `[!!] 缺失` | `[!!] 缺失`（未变） |
  | hook | `[OK] 已安装（pre-commit, commit-msg, pre-push）` | `[OK] 已安装且可执行（…）——注意：判的是「git 会不会执行它」…` |
  | 版本 | `[OK] AGATE_ROOT=<doctor 所在的 checkout>` | `[OK] AGATE_ROOT=/home/kity/.agate/v0.83.3/agate；版本=v0.83.3` |
  | 账本 | `[OK] 10 个账本，链完整` | `[OK] 10 个账本，链完整`（未变） |

  ⇒ **判定结果（OK/!!）一个都没变**，变的只是「报的值更真」。**非破坏性**。
- **`LIMITATIONS.md` 抬头 vs 本分支两 README（独立核实，与用户说法不符）**：
  用户提示「README.md / README.zh-CN.md 在本分支上仍是旧措辞」。**实测不成立**——
  `git show HEAD:README.md | sed -n 28p` 已是「**Zero infrastructure (on the *user* side).** … the
  **install / version-management / CI-backstop** side is *not* zero-infrastructure — see
  `agate/LIMITATIONS.md`」，`README.zh-CN.md:28` 同构（「零基础设施（使用侧）…并非零基础设施」）。
  ⇒ 两 README 早已把「零」限定到使用侧，与 LIMITATIONS 新抬头**方向一致**，**不构成同批自相矛盾**。
  唯一可挑的精度问题（LIMITATIONS 说「没有旁挂服务」，README 说「zero infrastructure (on the user side)」+
  显式否定安装/CI 侧）三者互不冲突。**判定：无矛盾。**
- **其它项目**：`agate-doctor` 不在任何 CI（`.github/` 0 命中）、不在协议文档（`agate/*.md` 0 命中）、
  不在 `SETUP.md` / `platform-notes.md` / `WORKFLOW.md` ⇒ 无 gate 行为变化，无下游破坏性。

### A6: 锚点表覆盖

**结论：ALIGNED——本批不需要动 `SCRIPT_ALIGNMENT_ANCHORS` 或 `GATE_SCRIPT_EXEMPT`**

实测判据（`check-protocol-consistency.py:918-931`）：
```python
gate_scripts = [ ... for p in scripts_dir.glob("check-*.py") if p.is_file()]
for extra in ("pre-commit-gate.sh", "pre-commit-gate.py"): ...
```
⇒ 覆盖面 = `check-*.py` + 两个 `pre-commit-gate.*`。本批**只改 `agate-doctor.py`**（`agate-*.py` 工具类），
且**未新增/改名任何 `check-*.py`**，故不在覆盖面内。实跑确认：
```
CHECK 9  协议-脚本结构对齐   ✅ PASS
CHECK 10 协议文档脚本名引用漂移 ⚠️ WARN（433 条全为冻结历史文件）
```
⇒ **ALIGNED**。另注：`agate/scripts/README.md` 属 CHECK 10 扫描面，本批未在该文件写入新脚本名，
无新增 ERROR。

### A7: 设计原则一致性

**结论：ALIGNED**

| ADR | 关系 | 判定 |
|---|---|---|
| **ADR-014 判据单一权威源** | 本批核心即「消灭第二处实现」：hook 位置原写死 `<repo>/.git/hooks`（第二套实现）→ 改用 `agate_common.git_hooks_dir()`（与 install/uninstall 同源）；版本原用脚本自定位（第二套）→ 改用 `resolve_hook_root()`（与 hook 同源）。**方向与 ADR 完全一致** | ALIGNED |
| **ADR-004 安全网分层** | doctor 不参与任何 gate 判定，只做「安全网（hook）是否真的生效」的可观测性。修的是观测层的保真度，不改变 gate 层责任划分 | ALIGNED |
| **ADR-011 引导型 CLI 权限非安全边界** | doctor 是只读诊断工具，无权限检查，不涉该边界 | ALIGNED |
| **ADR-002 可判定性** | 新判据（`os.access(X_OK)`、`rev-parse --git-path hooks`）均为外部工具可机读的客观值，非主观判断 | ALIGNED |

**未发现需要新 ADR 的架构决策**——本批是对既有 ADR-014 的直接落实，无新取舍。

### A8: 声称-命令绑定

逐条列本批 CHANGELOG / 代码注释中的**数字或结论类声称** → 产出它的命令 → 结论。

| # | 声称（位置） | 命令 | 结论 |
|---|---|---|---|
| 1 | 「三个 hook 权限 0644 时 git **忽略它们并让 commit 照常成功**（只打印两行 advice 提示，不阻断）」（`CHANGELOG:17`） | `mktemp -d` + `git init` + `chmod 644 .git/hooks/pre-commit` + `git commit` | **可复现**：`RC=0`，输出「提示：因为没有将钩子 … 设置为可执行，钩子被忽略」2 行 ⇒ 声称成立。⚠️ 作者已自行把原「**静默**忽略」改为「忽略…只打印两行 advice 提示」——该收紧**正确**（git 确实打印提示） |
| 2 | 「修后 doctor 与 `agate-resolve.py` 的输出**逐字一致**」（S0 `CHANGELOG` 曾有此句） | 同一 fake home + 同一 `.agate-version` 下并跑两脚本 | **不成立**：resolve 输出 `AGATE_ROOT=…` / `AGATE_VERSION=…` / `AGATE_REASON=…` 三行独立字段；doctor 输出单行 `AGATE_ROOT=…；版本=…；原因=…；项目 .agate-version=…`。**字段值一致，格式/字段名/追加字段均不同，非逐字**。✅ **作者已删除该声称**（当前 `CHANGELOG` 无「逐字一致」字样）——处理正确 |
| 3 | 「`docs/guides/project-map.md` 原写『约 60 个』，与实际已不符」（`CHANGELOG:42`） | `git log -S"约 60 个 Python 脚本"` → `c96880b9`(2026-08-30)；`git ls-tree -r c96880b9 -- agate/scripts | grep '\.py$' | wc -l` → **61**；`git ls-files agate/scripts | grep '\.py$' | wc -l` → **85** | **成立**：引入时 61（「约 60」准确），今 85（偏离 40%）⇒「与实际已不符」为真。现改为 `ls agate/scripts/*.py | wc -l` 现场命令，符合 `doc-freshness-guide.md`「时变数字不写死」 |
| 4 | 「项目声明 `agate: v0.80.0`（未安装）时 doctor 报 `<开发 checkout>/agate`，而 `agate-resolve.py` 报 `~/.agate/v0.83.3/agate`」（`CHANGELOG:29-31`） | 临时仓库 + `printf 'agate: v0.80.0\n' > .agate-version`，分别跑 OLD doctor 与 `agate-resolve.py`；`ls ~/.agate` 确认无 `v0.80.0` | **可逐字复现**：OLD → `AGATE_ROOT=/tmp/…/old/agate`；resolve → `AGATE_ROOT=/home/kity/.agate/v0.83.3/agate`；NEW doctor → 同 resolve 值 + 「声明的版本 v0.80.0 未安装，回退全局 current」。**声称完全准确** |
| 5 | 「链接 worktree 里 `.git` 是**文件**，doctor 误报『未检测到 .git/hooks（非 git 仓库或未初始化）』」 | `git worktree add` 后 `.git` 为文件（用例内 `assert (wt/".git").is_file()` 已证）；OLD doctor 走 `project_root/".git"/"hooks"` → `is_dir()` False ⇒ 走「未检测到 .git/hooks」分支 | **成立**（代码路径可静态确证，且新用例 `test_doctor_uses_git_hooks_dir_in_linked_worktree` 实跑通过） |
| 6 | 「`core.hooksPath` 覆盖时同理误报缺失」 | 新用例 `test_doctor_uses_git_hooks_dir_under_core_hookspath` 在 OLD 实现下实跑红（见 A4 回退实验） | **成立** |
| 7 | 「同一失效模式本仓已踩过两次（复制模式装出 0644），都只修了产生端」 | `CHANGELOG:1161-1162`（v0.83.3 节）记录「复制模式 hook 不可执行 → gate 静默失效」，且 `install-hook.py:124` 注释「复制**不携带权限位**…必须显式补执行位」 | **有据**（既有 CHANGELOG 与代码注释双证） |
| 8 | 测试用例 docstring 的「修前实况」断言（如 `[OK] hook: 已安装（pre-commit, commit-msg, pre-push）`） | 回退实验：OLD doctor 在 0644 场景下确实输出该行 | **成立** |

**A8 结论：8 条声称全部可给出命令；其中 2 条（#2 逐字一致、#1 静默）曾被作者自行收窄/删除，
处理方向正确。当前 CHANGELOG 无不可复核声称。**

## 4. 两个需要独立判断的问题（不顺着提问者的说法）

### 判断 1：版本维度因「解析链有 warning」判 `[!!]`，是设计取舍还是缺陷？

**结论：NEEDS_HUMAN_REVIEW——倾向「取舍成立，但语义标签错位」，建议改呈现而非改判定。**

反对者会说：「声明未安装但已回退 current」是**可用状态**，判 `[!!]` 会让正常项目显示不健康。
这个反对意见有实据：我实测 PeekView（无 `.agate-version`）与一个声明 v0.80.0 的项目，
前者 `[OK]`、后者 `[!!]`，而**两者 gate 都正常工作**（都解析到 v0.83.3 并成功执行）。
即 `[!!]` 在此处**不代表 gate 失效**。

但判 `[!!]` 仍有正当理由，且更符合本批意图：
1. **doctor 的语义是「与你的预期是否一致」，不只是「能不能跑」**。声明 v0.80.0 却跑 v0.83.3
   是**用户明确表达的意图没有被满足**——这正是最该被摊到台面上的事实（原实现把它完全吞掉）。
2. `warnings` 的产出方（`agate_common._resolve_version_info:366-368`）只在**两种真实异常**下生成：
   声明未安装、声明格式非法。两者都是**用户可行动的错误**（改声明或装版本），不是噪声。
3. 若判 `[OK]` 而把 warning 塞进状态行，doctor 的 `main()` 会打印「全部维度正常（已接入）」
   ——在一个声明未被满足的项目上说「正常」，**又把本批刚消灭的「报绿」缺陷请回来**。

**但存在一个真实缺陷（措辞层）**：`[!!]` 与相邻维度共用同一标记，而相邻维度的 `[!!]` 含义是
「gate 不生效」。两种严重度用同一符号，读者无法区分「gate 坏了」与「你的声明没被满足」。
**建议（非阻断）**：无需改判定，改**文案**——把该行改为
`[!!] 版本解析（声明未满足，gate 仍可用：回退 current）…`，或在 `main()` 的汇总行区分
「N 个维度异常」与「M 个声明未满足」。这样既保住「不假绿」，又不误导读成 gate 故障。

> 附带：这属于「呈现类」问题。按仓内 `AGENTS.md`「呈现类问题不作为 MISALIGNED、不因它开启新一轮」
> 的口径，**不应因此阻断本次提交**——故我把它列为建议，不列 BLOCKER。

### 判断 2：`_diagnose_version` 用 `Path(root).resolve()` 是否重新引入「报的不是实际用的」？

**结论：ALIGNED——不构成缺陷，但有一处真实的不一致面（且不是 `.resolve()` 引入的）。**

`resolve()` 本身是正确的，因为 **gate 侧也 `resolve`**：`agate-resolve.py:41` 写的是
`sys.stdout.write(f"AGATE_ROOT={Path(root).resolve()!s}\n")`。实测验证两个易错场景：

| 场景 | doctor 报 | `agate-resolve.py` 报 | 一致？ |
|---|---|---|---|
| `AGATE_HOME` 是软链（`linkhome → real`） | `/tmp/…/real/v5.0.0` | `/tmp/…/real/v5.0.0` | ✅ 一致 |
| `AGATE_ROOT` 为**相对路径**（`real/v5.0.0`） | `/tmp/…/real/v5.0.0` | （resolve 的 env 分支原样返回，**下游各自 resolve**） | ✅ doctor 显示了绝对真值，更不易误读 |

⇒ `.resolve()` 让 doctor 与 resolve **对齐**，不是分叉。

**但真正的「报的不是实际用的」面在别处（新发现，非同源问题）**：
`resolve_hook_root` 的兜底「脚本路径上溯」是**基于喂进去的 `hook_entry` 路径**计算的。
S1 已正确地改为「取 `git_hooks_dir()` 下的 `pre-commit` 并 `resolve()` 穿过软链」——这是对的。
**但若 hook 未安装**，`hook_entry.exists()` 为 False，S1 退回**本 checkout 的**
`_AGATE_ROOT/scripts/resolve-entry.py`。此时若解析链也无结果，doctor 报的是
**doctor 自己所在的 checkout**（我实测得到 `<worktree>/agate`，而真实 hook 入口
`~/.agate/scripts/resolve-entry.py` 上溯得到 `/home/kity/.agate`）。
⇒ 这仍是「把『我住哪』当『gate 用哪个』」的**残余**，只是收窄到「无 hook + 链无结果」的组合。
**缓解事实**：此组合下 hook 本来就没装，gate 根本不运行，该值不会被任何实际判定消费。
**建议（MINOR，可选）**：当 `hook_entry` 回退到本 checkout 时，状态行注明「hook 未安装，
此值为本工具所在 checkout，非 gate 实际入口」。

## 5. 必修项清单

| ID | 级别 | 文件:行 | 问题 | 修法 |
|---|---|---|---|---|
| — | **BLOCKER** | — | **无** | — |
| **M-1** | MINOR | `agate/scripts/README.md:131` | 索引行「版本解析」未反映新增的 `[!!]` 语义（版本维度现会因声明未满足而判异常）；该行亦未提 hook 维度改判「可执行性」 | 改为「版本解析（与 gate 同源，解析链告警判 `[!!]`）」。**注意**：按仓内「呈现类问题不作为 MISALIGNED」口径，此项**不应阻断提交**；若判定为「维度枚举未变、不构成失真」而选择不改，亦可接受——只需在 PR 描述里说明 |
| **N-1** | NEEDS_HUMAN_REVIEW | `agate/scripts/agate-doctor.py:91-95`、`:174-177`；根因 `agate_common.py:35-39` | `agate_common` 不可用分支为**死代码**：`sys.exit(1)` 抛 `SystemExit`，`except Exception` 抓不到。实测该场景 rc=1（违反 BDD-17「rc 恒 0」）；本批新增的两段 fallback 文案永不显示 | 二选一：① 删掉两处 fallback 文案，承认 fail-closed（最小改动）；② 改 `except (Exception, SystemExit)`，让 doctor 在缺 pyyaml 时仍完成诊断并 rc=0（更符合 BDD-17 既定语义）。**此项先于本批存在**，可另开 hotfix |

**已在审查期间被作者修复并补齐用例的项**（保留记录，便于复核「曾经存在而后闭合」）：

| 原 ID | 问题 | 闭合证据 |
|---|---|---|
| C1 | S0 的版本维度只用 `resolve_version_root`，与 gate 实际入口 `resolve_hook_root` 不同源 ⇒ 在「gate 跑得动」时报 `[!!] 无可用 AGATE_ROOT`（镜像缺陷） | `agate-doctor.py:164-184` 改为 `resolve_hook_root`；`test_doctor_version_matches_hook_resolution_when_chain_unavailable` 守护 |
| C1 残余 | 兜底时喂本 checkout 的 `resolve-entry.py` ⇒ 上溯得到 doctor 自身 checkout | 改为取 `git_hooks_dir()/pre-commit` 并 `resolve()` 穿软链；`test_doctor_uses_installed_hook_entry_for_fallback_root` 守护 |
| M-2 | 断链软链分支代码正确但无用例 | `test_doctor_reports_broken_symlink_hook` |
| M-3 | 空文件 / 非 agate 钩子仍报 `[OK]` 且曾称「已安装且生效」 | 措辞改为「已安装且可执行…不含其内容是否真能阻断」+ `test_doctor_does_not_claim_hook_content_blocks` |
| M-4 | 该测试文件无 `windows_smoke` 标记 ⇒ Windows CI 完全不跑 | 第 1 个用例已加标记（`-m windows_smoke` → `1 passed, 16 deselected`） |

## 6. 留痕

原始逐条痕迹：`docs/reviews/agate-alignment-2026-11-26-HOTFIX-DOCTOR-01.progress.md`

## 7. 只读纪律声明

本审查**未修改任何被审文件**：`git status --porcelain` 中被审的 5 个文件状态与审查开始时一致
（`M ` ×3 + `MM` ×2，`MM` 系**作者本人**在审查期间追加，非本评审所为）；
所有可能产生写副作用的实验（回退实验、变异测试、git 仓库构造）均在 `mktemp -d` 的一次性副本上
完成，且「创建 → 操作 → 清理」在同一次 bash 调用内执行。本评审仅新建了留痕文件与本报告两个文件。
