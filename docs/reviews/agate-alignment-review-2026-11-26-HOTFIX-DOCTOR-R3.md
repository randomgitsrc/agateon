---
review_date: 2026-11-26
reviewer: protocol-alignment-review
round: R3（fresh context，独立第三轮；不预设 R1/R2 结论正确）
change_summary: agate-doctor 诊断对象由「存在性」改为「效力」——hook 位置问 git、版本问 gate 的解析入口（resolve_hook_root）、并修 SystemExit 打断诊断/账本假绿/修复指引死循环；R2 后再补「回退分支不判 OK」+ 声明维度区分「缺失/读不懂」+ 去掉未经验证的仓库类型推断
files_changed:
  - agate/scripts/agate-doctor.py
  - agate/tests/unit/test_agate_doctor.py
  - agate/scripts/README.md
  - agate/LIMITATIONS.md
  - docs/guides/project-map.md
  - CHANGELOG.md
  - docs/reviews/agate-alignment-review-2026-11-26-HOTFIX-DOCTOR.md（R1 报告，被审对象的一部分）
  - docs/reviews/agate-alignment-review-2026-11-26-HOTFIX-DOCTOR-R2.md（R2 报告，同上）
reviewed_rev: c8acd5ff（origin/main..HEAD 三个提交 8690c9d2 / 70f051ba / c8acd5ff）
verdict: 不通过——2 项 MISALIGNED（A2 / A8）+ 1 项 NEEDS_HUMAN_REVIEW（A7）+ 5 项 MINOR，修完须复审
---

# 协议-脚本对齐审查（第三轮）

## 0. 审查对象与口径

- **审查对象 = `origin/main..HEAD` 三个提交**：`8690c9d2`（效力和非存在性）、`70f051ba`（回退不判 OK + 补守护）、
  `c8acd5ff`（三处「报告状态 ≠ 实际状态」残留 + 数字勘误）。
- **审查期间 HEAD 变过一次**：我开工时 HEAD 是 `921583f9`（工作区干净），审查中作者把它 amend 成 `c8acd5ff`
  （三文件 blob 完全相同，见 §9 实测）。本报告以 **`c8acd5ff`** 为准；凡结论只对旧 `921583f9` 成立的地方均已标注。
- 未提交改动：审查期间作者曾把声明维度修复放在工作区（暂存区），随后提交。**现在工作区的
  `CHANGELOG.md` / `agate/assets/templates/dsh/*` / `agate/platform-notes.md` / `agate/tests/unit/test_dsh_preset.py`
  的暂存改动属于另一个任务（DSH 0.2.x 对齐），不在本次审查面内，我未触碰。**
- 环境：Python 3.12.3 / pytest 9.0.3 / git 2.43.0 / WSL2（Linux 6.18）。
- **`/tmp` 在本机是 4.9G tmpfs，且 `/tmp` 与工作区不同设备**——所有全量跑都改用**工作区内的
  `git clone --no-hardlinks`**，否则 `test_t15`（`git clone --local` 硬链接）会跨设备失败，
  凭空多出一个「既有失败」。这一点直接决定了 A8 的数字判定（见 §6）。

## 1. 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED（模块 docstring 与实现一致；但见 A2 的对外索引行） |
| A2 | 脚本→文档对齐 | **MISALIGNED**——`agate/scripts/README.md:131` 承诺「hook 维度判『git 会不会执行它』」「版本维度与 gate 同源」，而实现有两条分支不满足：hook 回退分支直接放弃判断（`:163-167`）、版本维度不校验 gate 脚本是否存在（`resolve-entry.py:49-52` 才是 gate 的 fail-closed 判据） |
| A3 | 一致性连锁 + 反向传播 | ALIGNED（`tests/README.md:68` 映射在、`scripts/README.md:131` 已改、`UPGRADING.md:756` 无需改、CHECK 9 不需登记——实测 `uncovered_gate_scripts()` = 0；`LIMITATIONS.md` / `project-map.md` 的改动逐句核实为真） |
| A4 | 测试覆盖 | ALIGNED（附实跑：**26 passed**；9 个变异全部转红且各自因对应断言）——但记 2 处 MINOR 缺口（§5） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **有 2 条既有用例一度转红**（`test_selfgate_trailer_integrity.py::test_trailer_1_*`、`test_tag0051_self_gate.py::test_bdd_22_*`），原因是 `921583f9` 的 `self-gate-review:` 指向不存在路径；作者在同一次 amend 中修掉（`c8acd5ff` 实测 28 passed）。夹具无需更新。明细见 §4b |
| A5 | 下游影响 + 文档传播 | ALIGNED（doctor 只诊断不改判定，`rc` 恒 0；CHANGELOG `[Unreleased]` 已标；无破坏性变更） |
| A6 | 锚点表覆盖 | ALIGNED（doctor 不是 `check-*.py`，`uncovered_gate_scripts()` 实测返回 `[]`；无需新增锚点） |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW**——方向符合 ADR-014（消灭第二处实现），但账本维度 `_check_chain` 是 gate 判据（`check-events.py`）的**第二份实现且更窄**（实测 ts 倒退时 doctor 绿、gate 红），正是 ADR-014① 要拦的形态 |
| A8 | 声称-命令绑定 | **MISALIGNED**——4 处数字/结论无法用其声称的命令产出：`3042`（实测 3041）、勘误里的 `3049`（实测 **3046**，且 3049+3+3≠3052）、`433 冻结 WARN 与基线同`（实测 434/435/435）、`四处 except`（实测 3 处）。逐条见 §6 |

**总判定：不通过。** 依角色闭环规则，2 项 MISALIGNED 必须修完再复审；A7 的 NEEDS_HUMAN_REVIEW 需人工确认。

## 2. 逐项审查

### A1 文档→脚本对齐

**文档声明**（`agate/scripts/agate-doctor.py:1-25`，模块 docstring）：
> 2. git hook：`pre-commit` / `commit-msg` / `pre-push` 是否**存在且生效**。查的是
>    **git 实际会执行的目录**（`agate_common.git_hooks_dir`，覆盖链接 worktree 与
>    `core.hooksPath`）里的**效力**，不是 `<repo>/.git/hooks` 里的存在性。
> 3. 版本解析：报 **gate 实际会用的那个** `AGATE_ROOT`——以 `resolve_hook_root()`（gate 入口
>    `resolve-entry.py` 走的同一个函数）为准

**脚本实现**：`:127-130` 用 `agate_common.git_hooks_dir()`；`:250` 用 `resolve_hook_root()`；
`:158-174` 在位 + 可执行 + 非断链才判 OK 且措辞收窄到「git 会不会执行它」。

**结论：ALIGNED。** R1 的 C1（版本链与 gate 入口不同源）**确已闭合**：我逐字比对
`resolve-entry.py:43` 调的就是 `resolve_hook_root(os.path.abspath(__file__))`，doctor `:250` 同函数；
且喂进去的是 hooks 目录下 `pre-commit` 解析后的真实入口（`:241-246`），不再是 doctor 自身 checkout。

一处**措辞残留**（不计缺陷）：docstring 说 hook 维度判「是否存在**且生效**」，而实现与状态行
刻意只说「git 会不会执行它」（`:169-172` 明写「不含其内容是否真能阻断」）。docstring 的「生效」
比实现强，建议改成与状态行同口径。

### A2 脚本→文档对齐（反向）

**文档声明**（`agate/scripts/README.md:131`，本次改动行）：
> **hook 维度判「git 会不会执行它」**（查 `git rev-parse --git-path hooks` 指向的目录 + POSIX 执行位 + 非断链），
> **版本维度与 gate 同源**（走 `resolve_hook_root`，解析链告警判异常）——即两处判的都是**效力**而非仅存在性

逐项核对：

| README 承诺 | 实现 | 一致？ |
|---|---|---|
| hook：查 `git rev-parse --git-path hooks` 指向的目录 | `:127-137` `agate_common` 不可用时**回退到 `project_root/.git/hooks`**，且 `:163-167` 直接判 `[!!] 无法确认效力`（不再判 OK） | **否**——回退分支既没问 git，也没给出结论。README 没有这个分支的任何描述 |
| hook：POSIX 执行位 | `:154-156`，仅 `os.name != "nt"` | 是 |
| hook：非断链 | `:149-151` | 是 |
| 版本：走 `resolve_hook_root` | `:250` | 是 |
| 版本：解析链告警判异常 | `:282-287` | 是 |
| **「即两处判的都是效力」** | 版本维度**不校验 `AGATE_ROOT` 下有没有 gate 脚本**；而 `resolve-entry.py:49-52` 正是靠这条 fail-closed（`:49` 拼路径、`:50-52` 不存在即 `exit 1`）。实测（§8 E13）版本目录存在但缺三个 gate py 时 doctor **四维全绿「已接入」**，而真 `git commit` 被拦（rc=1） | **否**——此处 doctor 判的是「root 存在」而不是「gate 跑得起来」，恰是本批要消灭的那类差 |

**结论：MISALIGNED。**
**差异**：索引行把两个维度的判据强度说得比实现强；两处缺口都能实测出与 git/gate 相反的结论。
**建议**（两处都只需一行，且我已在副本上验证无回归，见 §8「补丁实测」）：
1. hook 回退分支**改为直调 git**（`subprocess.run(["git","rev-parse","--git-path","hooks"], cwd=...)`）——
   这条查询**不需要 pyyaml**，所以「`agate_common` 不可用」根本不构成「无法确认目录」。补丁后
   E1/E2/E3 三例全部与 git 实际一致（假绿与假红同时消失）。
2. 版本维度补一条与 `resolve-entry.py:49` 同源的判据：
   `if not (Path(root)/"scripts"/"pre-commit-gate.py").is_file(): return False, "...下缺 gate 脚本（gate 会 fail-closed 阻断提交）"`。

### A3 一致性连锁 + 反向传播

**A3a（已知衍生改动）**——全部到位：

| 应传播到 | 状态 |
|---|---|
| `agate/scripts/README.md`（工具索引行） | 已改（`:131`，本次 diff 内） |
| `agate/tests/README.md`（脚本↔测试映射） | 已在（`:68` `agate-doctor.py \| unit/test_agate_doctor.py`），无需改 |
| `CHANGELOG.md` `[Unreleased]` | 已标 5 条 + 勘误节 |
| `agate/LIMITATIONS.md` | 改了两处（抬头不再用「零基础设施」+ 局限 5 重述）。**逐句核实为真**：`agate_common.py:36-39` 确实缺 pyyaml 即 `sys.exit(1)`，故「enforcement 依赖 python3+git+pyyaml+git 仓库」成立 |
| `docs/guides/project-map.md` | 删掉写死的「约 60 个」。**实测**：`ls agate/scripts/*.py \| wc -l` = 85、`*.sh` = 3 ⇒ 旧值确已失真，改法（指向现场命令）正确 |

**A3b（主动推断的「应被影响但未在 diff 中」）**——逐一验证：

| 候选 | 验证 | 结论 |
|---|---|---|
| `agate/UPGRADING.md` 批 5 节（`:752-757`） | 原文「诊断项目接入 / 环境状态；退出码固定（诊断正常完成即成功…）」 | **不需要改**——本批未改 rc 语义，也未改调用方式 |
| CHECK 9 锚点表 | `uncovered_gate_scripts(root)` 实测返回 `[]`（doctor 只被 `scripts/glob("check-*.py")` + `pre-commit-gate.*` 覆盖） | **不需要改** |
| `agate/WORKFLOW.md`「Pre-commit 检查总览」 | doctor 不是 pre-commit 检查项 | 不需要改 |
| 角色文件 / 模板文件 | doctor 未被任何角色卡点名 | 不需要改 |
| `agate/tests/README.md` 的用例计数口径 | `count-tests.sh` 是下界语义（≥749），实测 3055 | 不需要改 |

**结论：ALIGNED。**

### A4 测试覆盖

**实跑（口径 = `agate/tests/README.md` 的 CI 复现命令 `--reruns 1 -n auto`，在干净克隆上）：**

```
# 干净克隆 c8acd5ff（git clone --no-hardlinks，工作区内，避开 /tmp tmpfs）
$ python3 -m pytest agate/tests -q -n auto --reruns 1
3 failed, 3049 passed, 3 skipped, 3 rerun in 88.42s (0:01:28)
FAILED agate/tests/integration/test_install_three_paths.py::test_t15_real_tree_smoke_pack_install_resolve
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_45_codex_template_readable_and_multi_agent_enabled

# 三条失败在 origin/main（7e3e0129）同样失败——同一环境、同样三条
$ (main) python3 -m pytest agate/tests -q -n auto --reruns 1
3 failed, 3031 passed, 3 skipped, 3 rerun in 85.82s (0:01:25)

# 目标文件
$ python3 -m pytest agate/tests/unit/test_agate_doctor.py -q
26 passed in 1.07s
```

`test_t15` 的失败**不是产品缺陷**：`/tmp` 是 4.9G tmpfs，`git clone --local` 硬链接跨设备
（`fatal: 无法创建链接 …: 无效的跨设备链接`）。把同一棵树放到工作区（`/dev/sdd`）后 `t15` **通过**
——即「3 个既有环境失败」里只有 2 个是稳定缺项（`bdd_43` 缺 opencode、`bdd_45` 缺 codex），
第 3 个取决于 `TMPDIR` 布局。作者三处记录都把它当稳定既有失败（见 A8）。

**变异实验（全部在 `mktemp -d` 的 `agate/` 整棵副本上做，一次 bash 调用内完成，未改真实工作区）：**

| # | 变异 | 结果 | 被哪条断言抓住 |
|---|---|---|---|
| 对照 | 未变异 | 26 passed | — |
| **A**（R2 声称） | 回退分支改回判 OK（`if hooks_dir_fallback:` → `if False:`） | **红 1** | `stays_green…:620` `assert not _hook_ok` |
| **B**（R2 声称） | 声明维度 `SystemExit` 分流失效（`if isinstance(exc, SystemExit):` → `if False:`） | **红 1** | `:634` `"YAML 语法" not in output` |
| **C**（R2 声称） | 建议去重失效（`dict.fromkeys(guidance)` → `guidance`） | **红 1** | `:639` `count(...) == 1`（实测 4 次） |
| **D**（R2 声称） | 账本解析失败时指引改回 `check-events.py` | **红 1** | `:628` `circular not in output` |
| E | hooks 目录硬编码回 `<repo>/.git/hooks` | **红 3** | `core_hookspath` / `linked_worktree` / `does_not_infer_not_a_repo` |
| F | 去掉执行位判定（`not_executable = []`） | **红 1** | `reports_broken_when_hooks_not_executable` |
| G | 版本维度永远喂本 checkout 的 `resolve-entry.py` | **红 1** | `uses_installed_hook_entry_for_fallback_root` |
| H | 去掉断链判定（`broken_links = []`） | **红 1** | `reports_broken_symlink_hook` |
| I | 新 `parse_error` 分支失效 | **红 1** | `distinguishes_missing_from_unparseable_declaration` |
| J | 版本「无真实入口判 `[!!]`」守卫失效 | **红 1** | `version_not_ok_when_root_is_merely_self_checkout` |
| K | hook 状态行重新加回「非 git 仓库或未初始化」 | **红 1** | `hook_status_does_not_infer_not_a_repo` |
| L | hook 永远判异常（`if not missing and …` → `if False`） | **红 4** | 含反向守护 `executable_hooks_stay_ok` |
| N | 版本维度真因分流失效（`SystemExit` 分支也建议 `agate-resolve.py`） | **红 1** | `stays_green…:628` |

**R2 声称的 4 个变异 A/B/C/D 我独立重做，4/4 真转红，且各自因**对应**断言而红（不是连带崩溃）——R2 的 M-2 结论成立。**

**MINOR-4a（测试脆弱点，非当前失败）**：`test_doctor_uses_git_hooks_dir_in_linked_worktree`
（`:332-367`）的 setup 是「先装 `exit 1` 的三个 hook，再 `git_repo.commit("base")`」（`:347-348`），
而 `GitRepo.commit`（`conftest.py:434-440`）**不检查 rc** ⇒ 该提交实际 rc=1 静默失败，
仓库停在 **unborn HEAD**。`git worktree add` 在 git 2.43 对 unborn HEAD **仍成功**，故用例当前有效
（我实测 `.git` 仍是文件、hook 仍共享），但它依赖一个未成文的 git 行为；换 git 版本/a 平台就可能
`pytest.skip` 掉而不自知（`:355` 的 skip 会把「环境不支持」和「setup 失败」混为一谈）。
修法：把 `:347` 的 hook 安装挪到 `:348` 的 commit **之后**，或 commit 后 `assert (git_repo.path/".git"/"HEAD").read_text()` 非 `ref: refs/heads/master` 形态。

**MINOR-4b（缺反向守护）**：现有用例只守「`agate_common` 挂了 + hooks 齐全 ⇒ 不得判 OK」，
**没有**守「`agate_common` 挂了但 git 实际就是 `.git/hooks` ⇒ 应当能确认」。正是这个缺口的反面
让 §8 E2 的假红无人拦。补完 A2 建议 1 之后，这条应改成「直调 git 时须与 `git rev-parse --git-path hooks`
一致」的对照断言（而不是放宽成「允许判 OK」——那会退回 N-1）。

### A4b 闭合后既有测试转红 + 夹具更新清单

**有 2 条既有用例转红，均已由作者在同一次 amend 中修掉：**

| 既有用例 | 为何转红 | 处置 |
|---|---|---|
| `agate/tests/unit/test_selfgate_trailer_integrity.py::test_trailer_1_real_repo_trailers_point_to_existing_files` | `921583f9` 的 commit message 带 `self-gate-review: docs/reviews/agate-alignment-2026-11-26-HOTFIX-DOCTOR-03.progress.md`，而该文件**不在该提交里**（`git cat-file -e 921583f9:<path>` rc=128——它是**我这个评审者**的未跟踪留痕文件）。判据 `_missing_trailer_paths` 用 `git cat-file -e` 判存在 | 作者 amend 成 `c8acd5ff`，去掉该 trailer。**实测**：干净克隆 `c8acd5ff` 上该用例 + `test_bdd_22` + doctor 26 = **28 passed** |
| `agate/tests/unit/test_tag0051_self_gate.py::test_bdd_22_protocol_commits_carry_falsifiable_self_gate_review` | 同上（`_bdd_22_violations` 同判据） | 同上 |

**夹具更新清单：无。** `conftest.py` 无需改动（新增用例复用了既有 `git_repo` / `run_cli` / `python_exe` /
`agate_root` / `tmp_path`）。空清单以外的实测依据：在 `origin/main` 上这两条用例 **23 passed**（我跑的），
在 `c8acd5ff` 上同样绿 ⇒ 不是被放宽判据「修绿」的。

另外记一条**与 A4b 相邻**的事实：`921583f9` 这次转红**正是本批自己的主题**（「声称的状态 ≠ 实际状态」
落在留痕上），且 `test_selfgate_trailer_integrity.py` 的失败信息里写着「本会话已复犯 3 次」。作者已修。

### A5 下游影响 + 文档传播

- **对已有项目的 gate 行为**：无影响。doctor 是纯诊断工具，`main()` 恒 `return 0`（`:349-383`），
  不被任何 hook / gate 脚本调用（`grep -rn "agate-doctor" agate/scripts/*.py .github/workflows/` 只命中
  `agate_common.py:908` 的注释与 doctor 自身）。
- **破坏性变更**：无。可以更严格地说：唯一「行为变严」的是输出里多出 `[!!]` 行，但 rc 不变。
- **CHANGELOG**：`[Unreleased]` 下 `### 修复` 5 条 + `### 勘误` 1 条 + `### 文档` 2 条，均有
  「走 hotfix 通道，不立项」标注。
- **文档传播**：见 A3，`LIMITATIONS.md` / `project-map.md` 的改动我逐句核实为真（不是凑数改动）。

**结论：ALIGNED**（数字问题归 A8，不在此重复计）。

### A6 锚点表覆盖

```
$ python3 -c "…check-protocol-consistency.py; m.uncovered_gate_scripts(Path('.').resolve())"
uncovered: 0
```
判据 `uncovered_gate_scripts`（`check-protocol-consistency.py:906-931`）的论域是
`agate/scripts/check-*.py` + `pre-commit-gate.{sh,py}`；`agate-doctor.py` 不在其中，故**不需要**
新增 CHECK 9 锚点。doctor 的登记面是 `scripts/README.md` 索引行（A2 已覆盖）与
`tests/README.md` 映射行（A3 已核）。

**结论：ALIGNED。**

### A7 设计原则一致性

| ADR | 检查 | 结论 |
|---|---|---|
| ADR-014① 判据必须单一权威源 | hook 位置：原写死 `<repo>/.git/hooks`（第二套实现）→ `agate_common.git_hooks_dir()`（与 install/uninstall 同源）✅；版本：原脚本自定位 → `resolve_hook_root()`（与 hook 同源）✅；**账本：`_check_chain`（`:301-316`）是 `check-events.py:80-108` 判据的第二份实现，且不完整** ❌ | 方向 ALIGNED，但账本维度**违反** ADR-014① |
| ADR-014 后果「权威源必须与既有实现逐条对账」 | 前两项我逐条对账过（上面 A1/A2）；账本这项**没对账**，漂移已经发生 | 见下 |
| ADR-015 实质/非实质 | 本批修的都是「会导致后续错误决策」的错误（把哑 gate 报绿会让维护者跳过排查），不是措辞洁癖 | 一致 |

**账本维度的漂移是可复现的**（详见 §8 E7）：

| 输入 | `check-events.py`（gate 用） | `doctor` |
|---|---|---|
| 3 条 `judge_verdict`（> 预算 2），链完整 | **exit 1**（「judge 轮次预算超限」） | `[OK] 1 个账本，链完整` |
| 第 2 行 `ts` 倒退，链完整 | **exit 1**（「时间戳单调违反」） | `[OK] 1 个账本，链完整` |
| 第 2 行是 JSON 数组 | **exit 1**（「第 2 行不是 JSON 对象」） | `[!!] _diagnose_ledger: 诊断异常（'list' object has no attribute 'get'）` |

**结论：NEEDS_HUMAN_REVIEW。** 需要人裁决的是**范围**（doctor 的「账本完整性」到底该等于
gate 的全套账本判定，还是只做哈希链子集），不是「有没有问题」——漂移是实测的。
我的建议（倾向「该等于」）：直接复用 `agate_common`：`GENESIS_HASH`（`:523`）已有单源，
`check_ledger_events(task_dir)`（`:2249`）就是 gate 侧规则判定；`_check_chain` 手写的
`_genesis_hash()`（`:62`）是第二份常量。至少应把 `ts` 单调与「顶层非 dict」补上，
否则 `README:131` 的「账本完整性」名义大于实现。

### A8 声称-命令绑定（逐条）

| # | 声称（出处） | 我的实测命令 → 结果 | 判定 |
|---|---|---|---|
| 1 | 「doctor 里原有的 **3 处** `except Exception`」（`CHANGELOG.md:64`；`test_agate_doctor.py:561`） | `git show origin/main:agate/scripts/agate-doctor.py \| grep -n except` → `:43`/`:52`/`:150` 三处 `except Exception`（另有 `:104` `except ValueError`、`:85`/`:98` `except OSError` 不算） | **成立**（R2 的 M-1 纠正正确） |
| 2 | 「修后覆盖 **6 处**」（`70f051ba` message） | `grep -c "(Exception, SystemExit)"` → HEAD **6**（`:77/86/131/247/251/363`），`8690c9d2` 与 `70f051ba` 亦为 6 | **成立** |
| 3 | 「`test_agate_doctor.py` **18 passed**」（`8690c9d2` message） | 该树 `pytest … --collect-only` → **18 tests collected** | **成立** |
| 4 | 「`test_agate_doctor.py` **23 passed**」（`70f051ba` message） | 该树 collect → **23 tests collected**（20 def + 3 参数化展开） | **成立** |
| 5 | 「`test_agate_doctor.py` **26 passed**」（`c8acd5ff` message、CHANGELOG） | 干净克隆 `c8acd5ff` → **26 passed** | **成立** |
| 6 | 「全量 **3042** passed + **2 个**既有环境失败」（`8690c9d2` message） | 干净克隆 `8690c9d2`：collect 3047 → **3041 passed / 3 skipped / 3 failed** | **两处都不成立**（3041≠3042；3≠2）。作者已在 CHANGELOG 勘误「3 个失败」，但**没改 3042** → 仍留一个错数 |
| 7 | 「全量 **3046** passed + 3 个既有环境失败」（`70f051ba` message） | 干净克隆 `70f051ba`：collect **3052** → **3046 passed / 3 skipped / 3 failed** | **完全成立**（原始 message 是对的） |
| 8 | 勘误称 `70f051ba`「收集 `3052`、跑出 **3049** passed / 3 skipped / 3 failed」（`CHANGELOG.md:116-118`） | 同上：实测 **3046**。且 3049+3+3=**3055 ≠ 3052**——该声称**自身算术矛盾** | **不成立**：作者把本来对的数字「更正」成了错的。（推测在其工作区里跑、把 `t15` 之外的差异算进去了；这也是为什么必须在干净克隆上跑） |
| 9 | 「全量 **3049** passed + 3 个既有环境失败」（`c8acd5ff` message） | 干净克隆 `c8acd5ff`：collect 3055 → **3049 passed / 3 skipped / 3 failed** | **成立**（但注意与 #8 的 3055 相同数字却是不同树，易误导；建议在报告里统一附 collect 数） |
| 10 | 「consistency 0 ERROR（**433 条冻结 WARN 与基线同**）」（三个 commit message + CHANGELOG） | `check-protocol-consistency.py`：main **433** / `8690c9d2` **434** / `70f051ba` **435** / `c8acd5ff` **435** | **不成立**：0 ERROR 对，但 WARN **不是**与基线同（+1、+2）。新增的两条来自前两份报告对 `…-01.progress.md` / `…-02.progress.md` 的引用（`docs/reviews/agate-alignment-review-2026-11-26-HOTFIX-DOCTOR.md:338`、`…-R2.md:391`）。这也解释了为什么我这份留痕文件被写进 `self-gate-review:` 会立刻多一条 WARN |
| 11 | 「**四处**收窄为 `except (Exception, SystemExit)`」（`8690c9d2` message 第 40 行） | 实际原为 **3 处**（同 #1） | **不成立**：R2 的 M-1 只改了 CHANGELOG 与测试 docstring，**这条 commit message 里的「四处」没改**。它已不可改（除 amend），但**说明「改数字」的动作没覆盖到 message 全集** |
| 12 | 「这 4 个被建议的脚本 RC 全非 0（4/4）」（`CHANGELOG.md:78-79`） | **忠实复刻**（`PYTHONPATH` 放抛 `ImportError` 的 `yaml.py`）：`agate-setup.py --scope project` rc=1、`agate-resolve.py` rc=1、`check-events.py <task>` rc=1、`agate-config.py init` rc=1（Traceback 后 rc=1） | **成立**。⚠️ 我也复现了「另一种复刻方式得出假结果」：往 `sys.path` 前置 stub `agate_common` 时 `agate-setup.py` rc=**0**、`check-events.py` rc=**0**（被脚本自身的 `sys.path.insert(0, SCRIPT_DIR)` 压过）。CHANGELOG `:80-86` 已经把「复刻方式必须写对」写进去了——**这条自我限定是本批最好的实践之一**，建议保留 |
| 13 | 「已补 **5 组断言**」（`CHANGELOG.md:84`） | `stays_green_exit_when_agate_common_aborts` 内 `assert` 计 **8** 条（`:596/601/605/612/620/628/634/639`），另加 3 条新用例 | **无法复核**：「5 组」的分组口径没有定义。按 A8 规则应改为可数表述（如「8 条断言 / 4 组逻辑各 1 条 + 去重 1 条」）或删掉数字 |
| 14 | 「本批**新增 10 条用例**」（`8690c9d2` message） | 该树 def 数 18 − origin/main 的 8 = **10** | **成立** |
| 15 | 「仓库含 **85** 个 Python 脚本」（`8690c9d2` message，附 `project-map.md` 改动） | `ls agate/scripts/*.py \| wc -l` = **85**；`*.sh` = 3 | **成立** |

**结论：MISALIGNED。** 需修：#6 的 3042、#8 的 3049（**这条最要紧——勘误本身是错的**）、
#10 的「433 与基线同」（三处 message 已不可改，但 CHANGELOG 里的同类表述须改为逐提交实测值）、
#11（message 已不可改，CHANGELOG 应记「3 处」并注明 message 里另有「四处」，避免后人照抄）、
#13（去数字或给口径）。

**方法学备注**：#6/#7/#9 的差异全部来自「在哪个目录跑」。`/tmp` 是 tmpfs ⇒ `test_t15` 跨设备失败；
跑在工作区则通过。**同一个 commit 在不同 `TMPDIR` 下 passed 数差 1**。因此本类声称必须同时给出
（a）clone 位置/`TMPDIR` 与（b）collect 数，否则「3046 / 3049 / 3052」这种组合无法互校——#8 的
算术矛盾就是这个坑的直接后果。

## 3. 修复优先级

| 优先级 | 项 | 位置 | 修法 |
|---|---|---|---|
| **必修** | A8-#8 勘误里的 `3049` 改回 `3046`（并补 collect `3052` 与「干净克隆 + 工作区内」口径） | `CHANGELOG.md:116-118` | 用我在 §6 给的两条命令复跑后改写 |
| **必修** | A8-#6 `3042` → `3041`；#10「433 与基线同」→ 逐提交实测（434/435/435）；#13 去数字或给口径 | `CHANGELOG.md:64` / `:113-119` / `:84` | 同上 |
| **必修** | A2-1 hook 回退分支改直调 git（`[!!] 无法确认效力` 在 E2/E3 是假红，且「无法确认」的前提不成立） | `agate-doctor.py:134-137,163-167` | §8「补丁实测 A」，已验证三例全对、26 用例无回归 |
| **必修** | A2-2 版本维度补 gate 脚本存在性判据（E13 四维全绿但 gate 真阻断） | `agate-doctor.py:288-296` | §8「补丁实测 B」，已验证无回归 |
| 待裁决 | A7 账本维度并到 `check-events` 的判据（或明确声明只做哈希链子集并同步 README） | `agate-doctor.py:301-316` | 二选一，需人决定范围 |
| MINOR | 声明维度 `project: go`（合法 YAML、`project` 非映射）崩成「诊断异常」+「请提交 issue」 | `agate-doctor.py:95` | 改 `proj = cfg.get("project"); language = proj.get("language","") if isinstance(proj, dict) else ""`，并在非 dict 时给「project 应为映射」的状态行。（`origin/main` 同样崩，非本批引入；但本批刚宣称「分三态」，此为第四态） |
| MINOR | `项目根: {Path.cwd()}`（`:346`/`:356`）标签名不实 | 同上 | 改名「当前目录」或改用 `git rev-parse --show-toplevel` 兜底（从子目录跑时声明/账本两维会假红，实测 §8 E4/E9） |
| MINOR | A4-4a worktree 用例 setup commit 静默失败（unborn HEAD） | `test_agate_doctor.py:347-348` | 先 commit 后装 hook，或断言 HEAD 已创建 |
| MINOR | A1 docstring「存在且生效」比实现强 | `agate-doctor.py:8-10` | 与状态行同口径 |

## 4. 七点逐条回答（派发单指定）

### ① N-1 是否真的闭合

**闭合。** 构造「`agate_common` 不可用（stub `sys.exit(1)`）+ `core.hooksPath` 指向空目录 +
`.git/hooks` 三个可执行 hook」：

```
[!!] hook: 无法确认效力（agate_common 不可用，已回退查 <repo>/.git/hooks；git 实际目录可能是 core.hooksPath 指向的别处）
$ git commit --allow-empty -m "gate 该拦我"
  commit rc=0            ← gate 真哑
```

doctor 与 `git commit` 的实际后果**一致**（都不再声称已接入）。R2 的 N-1 修法有效。
⚠️ 但同一构造的**反面**（没有 `core.hooksPath`）会变成假红，见②。

### ② 「回退分支不判 OK」是否过度

**过度，而且它的前提是假的——这不是「保守 vs 假绿」的取舍，是一个可修的实现缺陷。**

实测（E2：`agate_common` 不可用 + **无** `core.hooksPath` + `.git/hooks` 齐全可执行）：

```
[!!] hook: 无法确认效力（…）        ← doctor
$ git commit … ; commit rc=1        ← hook 真的拦住了
```

一切正常却被判异常。危害不是「多一行 `[!!]`」：修复指引变成「先让 agate_common 可用
（缺 pyyaml 时 pip install pyyaml）」，而用户环境里 pyyaml 往往确实没装**但 gate 照样生效**
（hook 薄壳自带的 python 探测 + `resolve-entry` 用的是另一个解释器环境）。用户会去装一个
与问题无关的包，然后发现 `[!!]` 还在。

**关键在于 R2 的推理有个隐含前提：「`agate_common` 不可用 ⇒ 我不知道 git 的 hooks 目录」。这个前提不成立。**
`git rev-parse --git-path hooks` 只需要 `git` 可执行，**不需要 pyyaml**。我在副本上把它改成直调
（10 行，`subprocess.run`，不改任何既有分支），三例全部与 git 实际一致：

| 场景 | 现状 | 直调 git 后 | git 真的会怎样 |
|---|---|---|---|
| E1 `core.hooksPath`→空目录 | `[!!] 无法确认效力` | `[!!] 缺失 pre-commit, commit-msg, pre-push〔/…/empty〕` | commit 成功（哑）——两边一致 |
| E2 无 `core.hooksPath`，hooks 齐全 | `[!!] 无法确认效力`（**假红**） | `[OK] 已安装且可执行` | commit 被拦（生效）——两边一致 |
| E3 链接 worktree | `[!!] hooks 目录不存在（…/wt/.git/hooks）`（**假红 + 目录报错**） | `[OK] 已安装且可执行` | commit 被拦（生效）——两边一致 |

26 条用例在补丁后**全绿**（无回归）。

**所以我的判断是：这个保守是错的，不是「正确的保守」。** 判据应该是「我能不能从权威源拿到答案」，
而权威源（git）在这里始终可用。留着 `[!!] 无法确认效力` 的唯一效果，是把「doctor 的依赖没装」
伪装成「项目接入状态不确定」——仍然是「报的不是实际状态」，只是把假绿换成了假红。
**如果坚持不改**，至少要把状态行与指引改成「本次未检查 hook（doctor 依赖缺失）」，不能写成
「无法确认**效力**」（那暗示查过了），且必须在 README/CHANGELOG 里写明这一分支——现在两处都没写（A2）。

E3 的措辞已由 `c8acd5ff` 修掉后半句（「非 git 仓库或未初始化」不再出现，`:146` 现在只陈述事实），
**这一步是对的**；但「hooks 目录不存在」这句话本身在 worktree 里仍然是**假的**（目录存在，只是
`.git` 是文件、该路径不可达）。

### ③ 变异实验复核 M-2

R2 声称的 4 个变异 **A/B/C/D 我独立重做（`mktemp -d` 里复制整棵 `agate/`），4/4 真转红**，
且都因**对应**断言而红（A→`:620`、B→`:634`、C→`:639`、D→`:628`，细节见 A4 表）。
R2 的 M-2 结论成立。**另外我加了 9 个变异（E/F/G/H/I/J/K/L/N）**，也全部转红，其中
E 与 L 证明了我最担心的一点——4 条 hook 用例与反向守护 `executable_hooks_stay_ok` 都有真实判别力。

### ④ 测试是否还有假绿

**4 条 hook 用例都真的走到了被测分支**（这是 R2 修过的坑，我逐条验了）：

| 用例 | 是否到目标分支 | 证据 |
|---|---|---|
| `reports_broken_when_hooks_not_executable` | 是（`not_executable` 非空） | 变异 F（去掉执行位判定）→ 仅此条红 |
| `executable_hooks_stay_ok` | 是（判 OK 路径） | 变异 L（永远判异常）→ 此条红 |
| `uses_git_hooks_dir_under_core_hookspath` | 是（`core.hooksPath` 生效） | 变异 E（目录硬编码）→ 此条红 |
| `uses_git_hooks_dir_in_linked_worktree` | 是（`.git` 是文件） | 变异 E → 此条红 |

**但发现两类新的「测试有效性」问题**：
1. **worktree 用例的 setup commit 静默失败**（A4-4a）：`git_repo.commit("base")` 的 rc=1 被丢弃，
   仓库停在 unborn HEAD。用例靠 `git worktree add` 对 unborn HEAD 的宽容行为活着——**现在没坏，
   但不该靠这个**。
2. **缺反向守护**（A4-4b）：没有用例守「`agate_common` 不可用 + 无 `core.hooksPath`」这个
   **正常却被判异常**的组合。R2 补的是「不得判 OK」这一侧，另一侧（不得假红）没守，
   于是②的过度保守不会被任何用例拦住。

### ⑤ A8 声称-命令绑定

见 §6 的 15 条表。**成立**：「3 处」「6 处」「18/23/26 passed」「3046」「3049（c8acd5ff）」
「4 个脚本 RC 全非 0」「85 个 Python 脚本」「新增 10 条用例」。
**不成立**：「3042」（实测 3041）、勘误里的「3049」（实测 **3046**，且算术矛盾）、
「433 冻结 WARN 与基线同」（实测 434/435/435）、「四处 except」（3 处）、「5 组断言」（无法复核）。

### ⑥ A2 反向：`agate/scripts/README.md:131`

**不逐项一致**，有两处（详见 A2）：hook 回退分支未描述（且其结论与索引行承诺相反）、
版本维度未校验 gate 脚本存在性（gate 的 fail-closed 判据在 `resolve-entry.py:49-52`，doctor 没做）。
其余各项（`--git-path hooks`、执行位、非断链、`resolve_hook_root`、告警判异常）**逐项为真**。

### ⑦ 还有没有「报告的状态 ≠ 实际状态」的残留

按四个维度扫完，**声明维度的缺失/损坏之分已修且我复核通过**（六态实测：缺失 → 「缺失」+`init`；
空文件 / 顶层非映射 / YAML 语法错 → 「存在但无法解析」+「**不要**重跑 init」，建议正确）。
剩下 4 处同类残留（均实测复现）：

| # | 残留 | 实测 | 是否本批引入 |
|---|---|---|---|
| 1 | **版本维度不判 gate 能否跑**：`AGATE_ROOT` 存在但缺 gate py ⇒ 四维全绿「已接入」，真 commit 被 `resolve-entry` fail-closed 拦（rc=1） | §8 E13 | 否（origin/main 同样绿）——但本批的主题正是这个，且 `resolve-entry.py:49` 的判据就在同仓 |
| 2 | **声明维度对「合法 YAML 但 `project` 非映射」崩溃**：`[!!] _diagnose_declaration: 诊断异常（'str' object has no attribute 'get'）` + 指引「请提交 issue 或人工排查」 | §8 E6 | 否（origin/main 同样崩）——但本批宣称「声明维度分三态」，这是第四态，且 `agate-config.py validate` 已能正确报「project: 期望 object，实际 str」 |
| 3 | **账本维度比 gate 窄**：`ts` 倒退判 OK、第 2 行非 dict 直接崩 | §8 E7 | 否（origin/main 同样）——归 A7 |
| 4 | **「项目根」标签实为 cwd**：从子目录跑 ⇒ 声明报「缺失」、账本报「无账本可审计」（两者在仓库根都存在） | §8 E4/E9 | 否（origin/main 同样） |

## 5. 实测记录

环境：Python 3.12.3 / pytest 9.0.3 / git 2.43.0 / WSL2。所有仓库构造与变异都在
`mktemp -d`（或工作区内一次性 clone）里完成，「创建 → 操作 → 清理」在同一次 bash 调用内
（本 harness 的 `/tmp` 跨调用**不保留**——我先用一个 markdown 探针目录验证了这点）。
**未修改任何被审文件；未 `git add`/`commit`/`stash`/`reset`；未改 git config。**

### 5.1 N-1 闭合性与「过度保守」（E1/E2/E3）

`agate_common` 用 `runpy` + 启动器注入 `sys.exit(1)` stub（与仓库既有做法一致，
`test_agate_doctor.py:565-579`），**不是**改 `PYTHONPATH` 顺序（那会被脚本自身的
`sys.path.insert(0, SCRIPT_DIR)` 压过）。

```
E1  core.hooksPath→空目录 + .git/hooks 齐全可执行
    doctor: [!!] hook: 无法确认效力（agate_common 不可用，已回退查 …/r1/.git/hooks；…）
    git commit --allow-empty → rc=0        ← gate 真哑       ⇒ 一致 ✅
E2  无 core.hooksPath + .git/hooks 齐全可执行
    doctor: [!!] hook: 无法确认效力（…）
    git commit              → rc=1        ← hook 真生效     ⇒ 假红 ❌
E3  链接 worktree（.git 是文件，hooks 共享主仓）
    doctor: [!!] hook: hooks 目录不存在（…/wt3/.git/hooks；来源=回退 .git/hooks（…））
    git commit              → rc=1        ← hook 真生效     ⇒ 假红 ❌（且「目录不存在」是本路径不可达、不是目录不存在）
```

### 5.2 补丁实测（**只在副本上打，未改真实文件**）

**补丁 A —— hook 回退分支直调 git：**
```python
# agate-doctor.py:134-137 的 except 分支内，把写死路径改成先问 git
_pr = subprocess.run(["git", "rev-parse", "--git-path", "hooks"],
                     cwd=str(project_root), capture_output=True, text=True)
if _pr.returncode == 0 and _pr.stdout.strip():
    hooks_dir = Path((project_root / _pr.stdout.strip()).resolve())
    hooks_dir_source = "git rev-parse --git-path hooks（直调，agate_common 不可用）"
    hooks_dir_fallback = False          # 能确认 ⇒ 恢复判 OK
else:
    ...原回退逻辑...
```
| 场景 | 补丁后 | git 真实行为 | 一致 |
|---|---|---|---|
| E1 | `[!!] 缺失 pre-commit, commit-msg, pre-push〔/…/empty〕` | commit 成功（哑） | ✅ |
| E2 | `[OK] 已安装且可执行（…）` | commit 被拦 | ✅ |
| E3 | `[OK] 已安装且可执行（…）` | commit 被拦 | ✅ |

`pytest tests/unit/test_agate_doctor.py -q` → **26 passed**（无回归）。

**补丁 B —— 版本维度补 gate 脚本判据（与 `resolve-entry.py:49-52` 同源）：**
```python
if not (Path(root) / "scripts" / "pre-commit-gate.py").is_file():
    return False, f"版本解析: AGATE_ROOT 下缺 gate 脚本（gate 会 fail-closed 阻断提交）｜{detail}", \
        "重装该版本（agate-install.py latest）或修正 .agate-version 声明"
```
| 场景 | 补丁前 | 补丁后 | gate 真实行为 |
|---|---|---|---|
| E13 版本目录缺 gate py | 四维全绿「已接入」 | `[!!] 版本解析: AGATE_ROOT 下缺 gate 脚本…` | commit rc=1（被 `resolve-entry` 拦） |
| E8 第三方 hook + 无 agate 安装 | 四维全绿「已接入」 | `[!!] …下缺 gate 脚本…` | 无 gate 在跑 |

`pytest … -q` → **26 passed**（无回归）。

### 5.3 声明维度六态（HEAD 实测）

| 输入 | doctor 状态行 | 指引 |
|---|---|---|
| 无文件 | `[!!] 声明文件: 缺失（agate.config.yaml 不存在）` | `agate-config.py init` ✅ |
| 空文件 | `[!!] 存在但无法解析（…；声明文件顶层不是映射（mapping））` | 改语法 +「**不要**重跑 init，会覆盖现有内容」✅ |
| `project: [unclosed` | `[!!] 存在但无法解析（…；while parsing a flow sequence…）` | 同上 ✅ |
| `- a\n- b`（顶层非映射） | `[!!] 存在但无法解析（…；顶层不是映射）` | 同上 ✅ |
| **`project: go`（合法 YAML，project 非映射）** | `[!!] _diagnose_declaration: 诊断异常（'str' object has no attribute 'get'）` | 「请提交 issue 或人工排查」❌ |
| `project: {language: go}` | `[OK] 声明文件: 存在（…，language=go）` | — ✅ |

（`agate-config.py validate` 对第五态能正确报 `project: 期望 object，实际 str` 并 rc=1 ⇒ 判据已在，doctor 没消费。）

### 5.4 账本维度 vs gate 判据（E7）

```
3 条 judge_verdict（> MAX_JUDGE_VERDICT_EVENTS=2），链完整
    doctor:         [OK] 账本完整性: 1 个账本，链完整
    check-events:   rc=1 「judge 复核轮次 3 > 2（verdict_hash 去重后计）」

第 2 行 ts 倒退（2026-11-26T09:00 < 第 1 行 10:00），链完整
    doctor:         [OK] 账本完整性: 1 个账本，链完整
    check-events:   rc=1 「第 2 行 ts(…) < 上一行 ts(…)——时间戳单调违反」

第 2 行是 JSON 数组
    doctor:         [!!] _diagnose_ledger: 诊断异常（'list' object has no attribute 'get'）
    check-events:   rc=1 「第 2 行不是 JSON 对象」
```

### 5.5 从子目录运行（E4/E9）

```
在仓库根：  [OK] 声明文件: 存在…   [OK] 账本完整性: 1 个账本，链完整
在 sub/deep：[!!] 声明文件: 缺失（agate.config.yaml 不存在）      ← 文件在仓库根，存在
            [OK] 账本完整性: 未发现任务目录（无账本可审计）        ← 账本也在仓库根
            （hook 维度不受影响：git_hooks_dir 按 cwd 上溯正确）
```

### 5.6 版本维度从子目录的自相矛盾（E9 附带）

```
在仓库根：  版本=v9.9.9；原因=引用 .agate-version；项目 .agate-version=agate: v9.9.9
在 sub/deep：版本=v9.9.9；原因=引用 .agate-version；项目 .agate-version=（未声明，使用 current）
```
同一次运行里「原因=引用 .agate-version」与「未声明」并列——`:224-228` 只读
`project_root/.agate-version`（= cwd），而解析链是向上的（`_find_project_declaration`）。属 MINOR 文案矛盾，
与 5.5 同根因（cwd 当项目根）。

### 5.7 数字实测（A8 的产出命令）

```bash
# 全部在「工作区内的 --no-hardlinks clone」上跑，避开 /tmp tmpfs
C=$WT/.r3-clone-<sha>; git clone -q --no-hardlinks "$WT" "$C"; git -C "$C" checkout -q <sha>
cd "$C" && python3 -m pytest agate/tests -q --collect-only | tail -2          # 收集数
cd "$C" && python3 -m pytest agate/tests -q -n auto --reruns 1 | tail -2     # CI 口径
cd "$C" && python3 agate/scripts/check-protocol-consistency.py | tail -2     # WARN 数
```

| rev | collect | 结果 | consistency WARN |
|---|---|---|---|
| origin/main `7e3e0129` | 3037 | 3 failed / **3031** passed / 3 skipped | 433 |
| `8690c9d2` | 3047 | 3 failed / **3041** passed / 3 skipped | 434 |
| `70f051ba` | 3052 | 3 failed / **3046** passed / 3 skipped | 435 |
| `c8acd5ff`（HEAD） | 3055 | 3 failed / **3049** passed / 3 skipped | 435 |

三条失败在各 rev 完全一致：`test_t15_real_tree_smoke_pack_install_resolve`（/tmp tmpfs 跨设备
硬链接）、`test_bdd_43_opencode_registration_and_debug_agent`（缺 opencode）、
`test_bdd_45_codex_template_readable_and_multi_agent_enabled`（缺 codex）。

## 6. 留痕

原始逐条痕迹（读一个文件/做一个判断就追加一行，未整理）：
`docs/reviews/agate-alignment-2026-11-26-HOTFIX-DOCTOR-03.progress.md`

## 7. 只读纪律声明

本审查**未修改任何被审文件**。审查期间工作区的 `agate/scripts/agate-doctor.py` /
`agate/tests/unit/test_agate_doctor.py` / `CHANGELOG.md` 由**作者本人**编辑并提交
（`921583f9` → amend `c8acd5ff`），我全程只读 blob 与工作区副本。所有 git 仓库构造、
`core.hooksPath` 实验、变异测试都在 `mktemp -d` 或工作区内一次性 clone 上完成，
「创建 → 操作 → 清理」在同一次 bash 调用内（本 harness 的 `/tmp` 跨调用不保留，已实测确认）。
**未执行** `git checkout/restore/reset/stash/clean/add/commit`，**未改** `git config`
（`core.hooksPath` 一律用 `git -C <repo> config …` 打在一次性仓库上，或用 `GIT_CONFIG_COUNT/KEY/VALUE`
环境变量；审查结束时实测 `git config --get core.hooksPath` 在主 checkout 与 worktree 均为**未设置**）。
本审查仅新建了两个文件：留痕文件与本报告。
