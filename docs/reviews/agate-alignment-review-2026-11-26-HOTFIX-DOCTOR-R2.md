---
review_date: 2026-11-26
reviewer: protocol-alignment-review
review_round: 2
change_summary: agate-doctor 诊断对象由「存在性」改为「效力」——hook 维度问 git 实际执行的目录并判执行位/断链，版本维度改与 gate 同源（resolve_hook_root），并把 6 处 except 放宽到 (Exception, SystemExit) 以免缺 pyyaml 时诊断中断
files_changed:
  - agate/scripts/agate-doctor.py
  - agate/tests/unit/test_agate_doctor.py
  - agate/scripts/README.md
  - agate/LIMITATIONS.md
  - docs/guides/project-map.md
  - CHANGELOG.md
branch: fix/doctor-hook-veracity
head_at_review: 8690c9d296e270236dda01ffd8541cdf3c2542e5
base: origin/main (7e3e0129)
verdict: ALIGNED_WITH_FOLLOWUPS
blocking_count: 0
minor_count: 3
needs_human_review_count: 1
---

# 协议-脚本对齐审查（第二轮）— HOTFIX-DOCTOR-R2

> 独立评审，fresh context。**未预设第一轮结论正确**；第一轮报告（`agate-alignment-review-2026-11-26-HOTFIX-DOCTOR.md`）
> 只作为「作者据以修改的输入」阅读，其结论一律重新实测。

## 0. 意图（1-2 句）

`agate-doctor` 此前报的是**「我以为的状态」而不是「gate 实际的状态」**：hook 维度只看
`<repo>/.git/hooks` 里有没有同名文件（不看 git 真正会执行的目录，也不看执行位），版本维度只回显
env 或「doctor 自己住在哪个 checkout」（不跑解析链）。于是它在两类真实场景给出与事实相反的结论——
hook 全在位但不可执行时 git 静默跳过、`git commit` 照常成功，doctor 却报「全部维度正常」；
链接 worktree / `core.hooksPath` 下 hook 明明生效却报「未接入」。本批把判据换成**问权威源**
（位置问 `git rev-parse --git-path hooks`、版本问 `resolve_hook_root()`、效力判执行位），
并顺带修掉「缺 pyyaml 时 `SystemExit` 打断整个诊断」的旧缺陷。

**这是「让诊断工具说的话与 gate 实际行为同源」的修正，不是新增能力**——hotfix 通道、不立项恰当。

## 1. 审查对象快照说明（必读）

审查期间作者**在同一 worktree 上持续追加修复**（部分由本评审的即时发现驱动），已发生 4 次漂移：

| 时刻 | `agate-doctor.py` md5 | 状态 |
|---|---|---|
| 审查开始 | `ce09529c`（staged） / `eef1380a`（worktree） | 暂存区落后工作区（`MM`） |
| 中途 | `92553a8d` → `b8a5b5b8` → `d1867c59` | 编辑中间态（曾出现 `_tasks_dir` 返回元组而 `_diagnose_ledger` 未同步，实跑报 `'tuple' object has no attribute 'is_dir'`） |
| **终态（本报告结论基准）** | **`2f210e52`** | 作者已 `git add -A` 并 commit `8690c9d2`；`git status` 除本评审两个留痕文件外为空 |

**本报告 A1–A8 结论一律以终态 `2f210e52`（= commit `8690c9d2`）为准**；中途态发现若已闭合，
在对应项下标「已闭合」并保留记录，便于复核「曾经存在而后闭合」。
（第一轮的教训：报告写「以 S1 为准」但未固定 blob，读者无法复现。本轮固定为 commit SHA。）

## 2. 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED** |
| A4 | 测试覆盖 | **ALIGNED_WITH_MINOR**（M-2） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**——空清单（显式） |
| A5 | 下游影响 + 文档传播 | **ALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **MISALIGNED**（M-1：「四处」实为 3 处，2 个落点） |

**总判定：ALIGNED_WITH_FOLLOWUPS — 0 BLOCKER，3 MINOR（M-1「四处」数字、M-2 两处新逻辑无用例守护、
M-3 `_exc_note` 与 BDD-17 的 rc 语义无守护），1 NEEDS_HUMAN_REVIEW（N-1 回退路径不校验 `core.hooksPath`）。**

**对第一轮结论的独立判断**：第一轮判 A2 MISALIGNED（M-1 索引行）与 A8 MISALIGNED（3 条声称自查收敛），
本轮复核**方向正确但有一处漏判**——第一轮 A8 第 1 条声称（0644 hook 行为）已实测成立，但它**没有核对
「四处」这个数字**，该数字从第一轮起就是错的（详见 A8）。第一轮把 N-1 判 NEEDS_HUMAN_REVIEW 也偏保守：
该场景 rc=1 **确实违反** BDD-17 已写死的契约，属可判定的 MISALIGNED 而非「取舍模糊」。

## 3. 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

**模块 docstring 声明**（`agate/scripts/agate-doctor.py:11-14`）：
> 3. 版本解析：报 **gate 实际会用的那个** `AGATE_ROOT`——以 `resolve_hook_root()`（gate 入口
>    `resolve-entry.py` 走的同一个函数）为准，并附上 `resolve_version_root()` 的解析链结论

**脚本实现**（`:202-247`）：`chain = agate_common.resolve_version_root(...)`；`hook_entry` 取
`git_hooks_dir()/pre-commit` 并 `Path.resolve()` 穿软链 → `hook_root, hook_warnings =
agate_common.resolve_hook_root(str(hook_entry))`；`root = chain_root or hook_root`。

三处同源逐一实测：

| 声明 | 实现 | 实测判据 |
|---|---|---|
| 位置问 git | `agate_common.git_hooks_dir()`（`agate_common.py:92-118`）= `git rev-parse --git-path hooks` + `clean_location_env=True` 中和 `GIT_DIR` | 与 `install-hook.py` / `agate-setup.py` **同一函数** ⇒ 安装侧与诊断侧不可能分叉（ADR-014） |
| 版本问 gate 入口 | `resolve_hook_root`（`agate_common.py:389-410`） | 正是 `resolve-entry.py:26` 调的函数 ⇒ doctor 与 hook 同一入口 |
| 执行位 | `os.access(X_OK)`，`os.name != "nt"` 守卫 | 与 git 实际判据一致（Windows 无该语义） |

**结论：ALIGNED**。`resolve_hook_root` 恒非空（脚本路径上溯兜底），故第一轮 S0 的 `if not root:`
死代码分支已正确移除——实测 `:244` 的 `if not Path(root).is_dir()` 是**另一条**判据（root 存在但目录不在），非死代码。

### A2: 脚本→文档对齐 — ALIGNED

`agate/scripts/README.md:131` 新索引行逐项核对（本轮用户特别要求 A2 反向）：

| # | 索引行声称 | 实现位置 | 实测 |
|---|---|---|---|
| ① | 查 `git rev-parse --git-path hooks` 指向的目录 | `:117-118` | ✅ 一致 |
| ② | + POSIX 执行位 | `:139-142`（`os.name != "nt"` 守卫 + `os.access(X_OK)`） | ✅ 一致 |
| ③ | + 非断链 | `:135-137`（`is_symlink() and not exists()`） | ✅ 一致 |
| ④ | 版本维度走 `resolve_hook_root` | `:219` | ✅ 一致 |
| ⑤ | 解析链告警判异常 | `:244`（`if warnings: return False, ...`） | ✅ 一致 |
| ⑥ | 「即两处判的都是**效力**而非仅存在性（缺失/断链仍会报…）」 | `:128-132`（目录不存在）、`:153-159`（缺失/断链/不可执行） | ✅ 一致 |

**⑥ 是本轮修掉的一处过度声称**：中途态曾写「两处都只报**效力**，不报「文件在不在」」——
与实现直接矛盾（`:132`/`:155`/`:157` 明确报「目录不存在 / 缺失 / 断链」）。终态改为
「效力**而非仅**存在性（缺失/断链仍会报）」后**严格一致**。**无夸大**。

其它面：
- `agate/tests/README.md:68` 映射行 `agate-doctor.py → unit/test_agate_doctor.py` 仍准确（未改名/增删）⇒ 无需改。
- `agate/UPGRADING.md:752-756`（v0.79.0 历史节）「退出码固定」仍准确（rc 语义未变）⇒ **历史节correctly 不回改**。
- 模块 docstring 与实现一致（见 A1）。

**结论：ALIGNED**。

### A3: 一致性连锁 + 反向传播 — ALIGNED

主动推断「应被影响但未在 diff 中的文件」，逐一实测：

| # | 面 | 在 diff | 实测 |
|---|---|---|---|
| 1 | `agate/scripts/README.md` | ✅ | 本轮已改（A2）；严格一致 |
| 2 | `agate/tests/README.md:68` | ❌ | 映射行仍准确 ⇒ 无需改 |
| 3 | `docs/guides/project-map.md` | ✅ | 删写死脚本数；实测引入时（`c96880b9`）61 个、今 **85** 个 ⇒ 原「约 60」已偏离 40% |
| 4 | `agate/LIMITATIONS.md` | ✅ | 抬头改「状态在仓库里 / 无旁挂服务」；与两 README（`README.md:28` / `README.zh-CN.md:28` 早已限定「使用侧」）**三方一致**，无矛盾 |
| 5 | `agate/UPGRADING.md:752-756` | ❌ | 历史发布记录，正确不回改 |
| 6 | 断言旧行为的字符串（「已安装（pre-commit」「全部维度正常」） | — | 全仓 grep：仅 doctor 自身、新测试、CHANGELOG、`docs/reviews/`（评审记录）⇒ 无其它文件断言旧行为 |
| 7 | `check-protocol-consistency.py` 锚点/豁免表 | ❌ | 见 A6，实测不需要 |
| 8 | CI / `agate/*.md` 协议文档 / SETUP / platform-notes | ❌ | 全仓 grep `agate-doctor`：CI 0 命中；协议文档仅 `UPGRADING.md`（历史节）⇒ doctor 不在任何 gate 路径上 |

**结论：ALIGNED**。反向传播面 8 个逐一实测，无漏改。

### A4: 测试覆盖 — ALIGNED_WITH_MINOR

**最近一次实跑输出**（终态 `2f210e52`）：
```
$ timeout 300 python3 -m pytest agate/tests/unit/test_agate_doctor.py -q
..................                                                       [100%]
18 passed in 0.85s
```
```
$ timeout 120 ~/.venvs/agate-dev/bin/ruff check agate/scripts/agate-doctor.py agate/tests/unit/test_agate_doctor.py
All checks passed!
```
```
$ timeout 300 python3 agate/scripts/check-protocol-consistency.py
  仅有 433 个 WARNING，无 ERROR。
```
用例数（`count-tests.sh`，HEAD `8690c9d2^`=3037 → 今 **3047**，`+10`）：与「HEAD 8 个 test 函数 → 今 18 个」
= **新增 10 条**一致。⚠️ 用户任务描述写「新增 11 条」——实测为 **10 条**（见 A8 #2）。

#### 4.1 独立变异实验（**全部在 `mktemp -d` 副本内**，staged/committed blob 为基准，`cp -a agate` 整树）

| # | 变异 | 结果 | 判定 |
|---|---|---|---|
| M1 | 声明维度 `(Exception, SystemExit)` 退回 `except Exception` | **1 failed**：`test_doctor_stays_green_exit_when_agate_common_aborts` | ✅ 守得住 |
| M2 | `_exc_note` 退回裸 `str(exc)` | **1 failed**：同上 | ✅ 守得住 |
| M3 | 清空 `not_executable`（不判执行位） | **1 failed**：`..._reports_broken_when_hooks_not_executable` | ✅ 守得住 |
| M4 | hook 目录退回写死 `.git/hooks` | **2 failed**：`..._under_core_hookspath`、`..._in_linked_worktree` | ✅ 守得住 |
| M5 | 版本维度退回「env 或脚本自定位」 | **2 failed**：`..._version_reports_what_gate_actually_resolves`、`..._uses_installed_hook_entry_for_fallback_root` | ✅ 守得住 |
| M6 | **反向**：hook 恒判异常（`if False:`） | **4 failed**，含 `test_doctor_executable_hooks_stay_ok` | ✅ 反向守护有效 |
| M7 | 清空 `broken_links` | **1 failed**：`..._reports_broken_symlink_hook` | ✅ 守得住 |
| M8 | 账本：`tasks_dir is None` 退回判 `OK` | **1 failed**：`test_doctor_stays_green_exit_when_agate_common_aborts` | ✅ 守得住（本轮新增断言） |
| M9 | `hooks_dir_fallback` 恒 `False` | **18 passed**（无守护） | ⚠️ **M-2**（行为但无用例） |
| M10 | `dict.fromkeys(guidance)` 退回不去重 | **18 passed**（无守护） | ⚠️ 可接受（呈现层，无判定变化） |
| M11 | 声明维度退回「查 YAML 语法」误指路 | **18 passed**（无守护） | ⚠️ **M-2** 同族 |

**复现命令**（任取一条，全部同构）：
```bash
T=$(mktemp -d); cp -a <worktree>/agate "$T/agate"
python3 - "$T/agate/scripts/agate-doctor.py" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1]); t = p.read_text(encoding="utf-8")
t = t.replace('        not_executable = [n for n in present if not os.access(hooks_dir / n, os.X_OK)]',
              '        not_executable = []', 1)
p.write_text(t, encoding="utf-8")
PY
( cd "$T" && python3 -m pytest agate/tests/unit/test_agate_doctor.py -q )   # → 1 failed
rm -rf "$T"
```

**结论**：**8/11 个变异被抓**，其中关键 5 个修复面（执行位 / 目录来源 / 版本同源 / 断链 / SystemExit）
各有独立用例守护，**反向守护也真的会红**（M6）。**失守的 3 个**：M9（`hooks_dir_fallback`）、M11（指引按真因分流）、
M10（去重）——三者都是**本轮新加的逻辑**，无用例 ⇒ **M-2**。

#### 4.2 测试是否假绿（用户第 4 点的独立核实）

`test_doctor_stays_green_exit_when_agate_common_aborts` 用 launcher + `sys.path.insert(0, stub_dir)` 注入假
`agate_common`。**我独立验证了注入确实生效**（三重证明）：

```bash
# 证明 1：stub 路径首位 → import 立刻 SystemExit（说明赢过真模块）
$ python3 -c "import sys; sys.path.insert(0,'$T/stub'); import agate_common"
PROOF-OK: stub won, SystemExit code = 1

# 证明 2（对照）：真 scripts 目录首位 → 正常 import 真模块
$ python3 -c "import sys; sys.path.insert(0,'agate/scripts'); import agate_common; print(agate_common.__file__)"
CONTROL: real module imported -> .../agate/scripts/agate_common.py

# 证明 3：同一 launcher 只删 stub 那行 → 输出完全不同（差异确由 stub 造成）
launcher WITHOUT stub → [!!] 声明文件: 读取失败（No module named 'agate_common'）
launcher WITH    stub → [!!] 声明文件: 无法读取（agate_common 在 import 阶段中止…）
```

⇒ **注入真生效，非假绿**。作者注释里说的坑（「真模块同目录、优先级更高」）是**对 `PYTHONPATH` 方式**的描述：
`agate-doctor.py` 无 `sys.path` 操作，但 launcher 用 `runpy.run_path` 时 `sys.path[0]` 是**launcher 所在目录**
而非 `agate/scripts`，故 `sys.path.insert(0, stub)` 能赢。**该用例的构造是正确的**，且我另用**更忠实的模拟**
交叉验证了同一结论（见 4.3）。

#### 4.3 更忠实的「缺 pyyaml」模拟（比 stub 更强）

stub（`sys.exit(1)` 无条件触发）只能证明「捕获 `SystemExit`」这一半。我用**真 `agate_common` + 坏 `yaml.py`**
复刻真实失效路径：
```bash
printf 'raise ImportError("No module named yaml")\n' > $T/badyaml/yaml.py
PYTHONPATH=$T/badyaml python3 agate/scripts/agate-doctor.py
```
实测结果（终态）：**rc=0、四个维度齐全**，每行原因可读：
```
[!!] 声明文件: 无法读取（agate_common 在 import 阶段中止（code=1；通常是依赖未安装，最常见是 pyyaml））
[!!] hook: 缺失 pre-commit, commit-msg, pre-push〔…/.git/hooks〕
[!!] 版本解析: 解析链不可用（…）；项目 .agate-version=（未声明）
[!!] 账本完整性: 无法定位任务目录（…），审计未执行
修复建议（异常项的可执行动作）：
  - 先让 agate_common 可用（缺 pyyaml 时 pip install pyyaml）后重跑
```
⇒ **BDD-17「诊断完成即 rc=0」已恢复**，且四维度不再被截断；指引也**不再**建议跑
`agate-setup.py` / `check-events.py` / `agate-config.py` / `agate-resolve.py`。这四个脚本在同环境下
我**逐个实跑**，RC 全为 `1`（死循环建议确实是真问题，作者修得对）。

**未覆盖的失效模式（我独立构造并实测）：**

| # | 失效模式 | 实测行为 | 用例 | 判定 |
|---|---|---|---|---|
| 1 | hook 断链 | `[!!] hook: 断链 commit-msg〔…〕` | ✅ | 已闭合 |
| 2 | hook 空文件 / 非 agate 薄壳 | `[OK]` + 显式声明「不含其内容是否真能阻断」 | ✅ | 已闭合（诚实呈现） |
| 3 | `SystemExit.code` = `None` / `'boom'` / `3` | rc=0，文案 `code=None` / `code=boom` / `code=3`，**不崩** | ❌ | 无用例，但无缺陷（见下） |
| 4 | **`core.hooksPath` 覆盖 + `agate_common` 挂掉** | `[OK] 已安装且可执行` **假绿** | ❌ | **N-1** |
| 5 | Windows 分支 | `os.name != "nt"` 守卫；用例 `pytest.skip` | ✅ | 已闭合 |

**#3 细节**（用户第 2 点）：`SystemExit.code` 为 `None`/字符串/非整数时 `f"code={exc.code}"` 均正常输出，
**不会崩、不会二次抛异常**。`_exc_note` 对 `SystemExit` 走 `isinstance` 分支，非 `SystemExit` 走 `str(exc)`，
**正确**。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED（空清单，显式）

**经实测无既有用例转红，无夹具需要更新。** 依据：

1. `pytest agate/tests/unit/test_agate_doctor.py -q -k bdd_17` ⇒ **8 passed, 10 deselected**——
   原有 8 条 BDD-17 用例全绿（它们断言「输出含 hook/版本等关键字」，未锁死旧措辞）。
2. 全仓 grep 引用 `agate-doctor` 的**测试文件仅 1 个**（`test_agate_doctor.py`），无第二处消费 doctor 输出。
3. `count-tests.sh`：**3037 → 3047（+10）**，与「8 → 18 个 test 函数」一致，**无既有用例被删除或改名**。
4. 夹具：本批**未改 `agate/tests/conftest.py`**（`git diff --cached --name-only | grep conftest` 为空）；
   新用例复用既有 `git_repo` / `agate_scripts` / `python_exe` / `run_cli` / `agate_root` fixtures。

### A5: 下游影响 + 文档传播 — ALIGNED

- **CHANGELOG 已标注**：`[Unreleased]` 下 `### 修复` 三条（hook 效力 / 版本同源 / SystemExit）+ `### 文档` 两条。
- **真实下游实测（本 worktree 自身，已接入 agate）**：终态 doctor 输出
  ```
  [OK] 声明文件: 存在（agate.config.yaml，language=python）
  [OK] hook: 已安装且可执行（…）——注意：判的是「git 会不会执行它」，不含「其内容是否真能阻断」
  [OK] 版本解析: AGATE_ROOT=/home/kity/.agate/v0.83.3/agate；版本=v0.83.3；原因=全局 current
  [OK] 账本完整性: 23 个账本，链完整
  ```
  版本值由「doctor 所在 checkout」改为「`~/.agate/v0.83.3/agate`」，与 `agate-resolve.py` 实测输出**字段值一致**。
- **`LIMITATIONS.md` 抬头**：删「零基础设施」概括，改为「状态在仓库里 / 无旁挂服务要运维」，并显式声明
  「『没有旁挂服务』与『零依赖』不是一回事」。与 `README.md:28` / `README.zh-CN.md:28`（早已限定「使用侧」）
  方向一致，**无同批自相矛盾**。
  - **补充实测（支持该措辞方向）**：缺 python3 时 `pre-commit-gate.sh` 实测输出
    `GATE ERROR: 无法启动 resolve-entry（python3/python 均不可用或脚本缺失）` 并 **commit 中止（RC=1）**；
    缺 pyyaml 时真实 `git commit` 实测 **RC=1** + `resolve-entry: agate_common 不可用（缺 pyyaml？），gate 阻断`。
    ⇒ 「依赖 python3 + git + pyyaml，缺任一 gate 失效」**逐项可复现**，非不可复核声称。
- 无破坏性变更：`agate-doctor` 不在任何 CI、不在协议 gate 路径（A3 #8）。

### A6: 锚点表覆盖 — ALIGNED

实测判据（`check-protocol-consistency.py`）：
```python
gate_scripts = [ ... for p in scripts_dir.glob("check-*.py") if p.is_file()]
for extra in ("pre-commit-gate.sh", "pre-commit-gate.py"): ...
```
⇒ 覆盖面 = `check-*.py` + 两个 `pre-commit-gate.*`。本批只改 `agate-doctor.py`（`agate-*.py` 工具类），
**未新增/改名任何 `check-*.py`** ⇒ 不在覆盖面内，无需动 `SCRIPT_ALIGNMENT_ANCHORS` / `GATE_SCRIPT_EXEMPT`。
实跑确认 `CHECK 9 协议-脚本结构对齐 ✅ PASS`、`CHECK 10 ⚠️ WARN（433 条全为冻结历史文件）`。
另：`agate/scripts/README.md` 属 CHECK 10 扫描面，本批未写入新脚本名，无新增 ERROR。

### A7: 设计原则一致性 — ALIGNED

| ADR | 关系 | 判定 |
|---|---|---|
| **ADR-014 判据单一权威源** | 本批核心即消灭第二处实现：hook 位置原写死 `<repo>/.git/hooks` → 改用 `git_hooks_dir()`（与 install/uninstall 同源）；版本原用脚本自定位 → 改用 `resolve_hook_root()`（与 hook 同源） | ALIGNED |
| **ADR-004 安全网分层** | doctor 不参与 gate 判定，只做「安全网是否真生效」的可观测性；本批修的是观测层保真度，不改 gate 层责任划分 | ALIGNED |
| **ADR-009 版本管理 + fail-closed** | 实测 gate 在缺 pyyaml / 缺 python3 时**均 fail-closed**（真实 commit RC=1），本批未削弱该性质——doctor 自身 rc=0 是 BDD-17 的既定契约（诊断工具报告问题 ≠ 自身失败），与 gate fail-closed **不冲突**（两者职责不同） | ALIGNED |
| **ADR-011 引导型 CLI 权限非安全边界** | doctor 只读诊断，无权限检查 | ALIGNED |
| **ADR-002 可判定性** | 新判据（`rev-parse --git-path hooks`、`os.access(X_OK)`、`is_symlink()`）均为外部工具可机读的客观值 | ALIGNED |

**未发现需要新 ADR 的架构决策**——本批是对 ADR-014 的直接落实，无新取舍。

### A8: 声称-命令绑定 — MISALIGNED（M-1）

逐条列本批 CHANGELOG / 代码注释 / docstring 的**数字或结论类声称** → 产出它的命令 → 结论。

| # | 声称（位置） | 命令 | 结论 |
|---|---|---|---|
| 1 | 「三个 hook 权限 0644 时 git 忽略它们并让 commit 照常成功（只打印两行 advice 提示，不阻断）」（`CHANGELOG.md:17-18`） | `mktemp -d` + `git init` + `chmod 644 .git/hooks/pre-commit` + `git commit` | **成立**：实测 `RC=0`，输出恰 **2 行**「提示：因为没有将钩子 … 设置为可执行，钩子被忽略」+ 1 行 commit 结果；`git commit` 成功（`1 file changed`） |
| 2 | 「用户任务描述称新增 11 条用例」 | `git show HEAD^:…/test_agate_doctor.py \| grep -c '^def test_'` → **8**；今 → **18**；`count-tests.sh` HEAD **3037** → 今 **3047** | **不成立，实为 10 条**。已核对：任务描述的口径偏差，非 CHANGELOG 声称（CHANGELOG 未写用例数）⇒ **不构成 A8 缺陷，但记录以免被后人当数字引用** |
| 3 | 「doctor 里**四处** `except Exception` 一处都接不住」（`CHANGELOG.md:39`、`CHANGELOG.md:41`「四处收窄为」，测试 docstring `test_agate_doctor.py:561`） | `git show HEAD^:agate/scripts/agate-doctor.py \| grep -c 'except Exception'` → **3**；逐行：`:43`、`:52`、`:150` | **不成立，实为 3 处**（HEAD 版）。终态确有 **6 处** `(Exception, SystemExit)`（`:70/:79/:107/:193/:196/:285`），但「原先是四处」这个**历史数字错了**。⇒ **M-1：三个落点需改正** |
| 4 | 「`docs/guides/project-map.md` 原写『约 60 个』，与实际已不符」（`CHANGELOG.md:47`） | `git ls-tree -r c96880b9 -- agate/scripts \| grep -c '\.py$'` → **61**；`ls agate/scripts/*.py \| wc -l` → **85** | **成立**：引入时 61（「约 60」当时准确），今 85（偏离 40%）⇒「与实际已不符」为真；改为现场命令符合 `doc-freshness-guide.md` |
| 5 | 「项目声明 `agate: v0.80.0`（未安装）时 doctor 报 `<开发 checkout>/agate`，而 `agate-resolve.py` 报 `~/.agate/v0.83.3/agate`」（`CHANGELOG.md:29-31`） | 临时仓库 + `printf 'agate: v0.80.0\n' > .agate-version`；`ls -d ~/.agate/v0.80.0` → 不存在；分别跑 HEAD doctor / `agate-resolve.py` / 终态 doctor | **可逐字复现**：HEAD doctor → `AGATE_ROOT=/tmp`（脚本自定位）；`agate-resolve.py` → `AGATE_ROOT=/home/kity/.agate/v0.83.3/agate`；终态 doctor → 同 resolve 值 + 「声明的版本 v0.80.0 未安装，回退全局 current」。**声称完全准确** |
| 6 | 「修后该场景 **rc=0、四维度齐全、原因可读**」（`CHANGELOG.md:43`） | 坏 `yaml.py` + `PYTHONPATH` 跑终态 doctor（见 A4 §4.3） | **成立**：实测 rc=0、四行维度齐全、原因文案可读（「在 import 阶段中止…通常是依赖未安装」）；且**指引不再指向同样挂掉的 4 个脚本**（实测全 RC=1） |
| 7 | 「链接 worktree 里 `.git` 是文件」（`CHANGELOG.md:20-21`） | 新用例 `..._in_linked_worktree` 内 `assert (wt/".git").is_file()` + 实跑通过 | **成立** |
| 8 | 「`core.hooksPath` 覆盖时同理误报缺失」（`CHANGELOG.md:22`） | 新用例 `..._under_core_hookspath`；M4 变异下转红 | **成立** |
| 9 | 「并在状态行标出『查的是哪个目录』」（`CHANGELOG.md:24`） | 终态实测：`[!!]` 分支含 `〔<dir>〕`（`:159,:169`）；**`[OK]` 分支与 `missing` 分支不含目录**（`:148-151`、`:169` 的 OK 路径） | **部分不成立**：`[OK]` 分支不标目录。但该分支报 OK 时目录无诊断价值（无异常需定位）⇒ **可辩护，建议不改**（呈现层） |
| 10 | `_exc_note` 新措辞「agate_common 在 import 阶段中止……通常是依赖未安装，最常见是 pyyaml」 | `grep -n 'sys.exit' agate_common.py` → **1 处**（`:39`，在 `except ImportError` 分支）；`grep 'raise SystemExit'` → 0 | **成立且措辞已刻意去依赖该事实**（`:46-49` 自述「刻意不写『唯一一处 sys.exit』」）⇒ **本轮已按 (b) 方案修好**，不再随 `agate_common` 变化而变假 |
| 11 | README 索引行「查 `git rev-parse --git-path hooks` 指向的目录 + POSIX 执行位 + 非断链」 | 见 A2 逐项表（①–⑥ 全核对） | **逐项成立** |

**A8 结论：11 条声称中 9 条可给出命令且成立，2 条有问题**：
- **#3（M-1，须改）**：「四处」实为 **3 处**，出现在 `CHANGELOG.md:39`、`CHANGELOG.md:41`、`test_agate_doctor.py:561`。
- **#9（可辩护，不改）**：`[OK]` 分支不标目录——无异常需定位，不建议加。

## 4. 两个需要独立判断的问题（不顺着提问者/第一轮的说法）

### 判断 1：`_exc_note` 的「唯一 sys.exit」措辞该 (a) 加断言 / (b) 改写 / (c) 保持？

**结论：选 (b)，且作者已完成。** 理由：
- (a) 加断言锁「`agate_common` 只有一处 `sys.exit`」会**制造假警报**：往模块级新增一处 `sys.exit`（如「不支持 Python 版本」检查）是**合理演进**，却会让 doctor 的用例转红，而 doctor 的行为其实完全正确。
- (c) 保持现状（措辞依赖该事实）会在 `agate_common` 演进后**变成假话**，且是**读者可见的输出文案**——比代码注释更严重（违反 A8 精神）。
- (b) 正解：把「为什么中止」降级为**概率陈述**（「通常是依赖未安装，最常见是 pyyaml」）+ 给出**可行动的下一步**。这既保住可读性，又不把会漂移的事实固化成文案。
- **实测支持**：终态文案为 `agate_common 在 import 阶段中止（code=1；通常是依赖未安装，最常见是 pyyaml）`；`code` 为 `None`/字符串/非整数时均正常输出（见 A4 #3）。

### 判断 2：`core.hooksPath` 覆盖 + `agate_common` 挂掉时判 `[OK]` —— 是缺陷还是可接受？

**结论：NEEDS_HUMAN_REVIEW（N-1）——真缺陷，但优先级低，且属「本批修法的副作用而非本批引入的旧缺陷」。**

**精确复现（与用户的分歧在此，双方构造不同，各自都对）**：

| 构造 | `agate_common` | `.git/hooks` 内容 | `core.hooksPath` | doctor 判 | 是否正确 |
|---|---|---|---|---|---|
| **A**（我的） | 挂掉 | **3 个可执行** | → 空目录 | **`[OK]` 已安装且可执行** | ❌ **假绿** |
| B（用户的） | 挂掉 | **空** | → 空目录 | `[!!]` 缺失〔`…/.git/hooks`〕 | ✅ 正确（碰巧对） |
| C | 活的 | 3 个可执行 | → 空目录 | `[!!]` 缺失〔`…/empty-hooks`〕 | ✅ 正确 |
| D | 挂掉 | 3 个可执行 | 无 | `[OK]` 已安装且可执行 | ✅ 正确 |

**机理**：`agate_common` 挂掉 → `:122` 回退 `project_root/.git/hooks`（**不经 `git rev-parse`**）→
该目录里 3 个 hook 在位且可执行 → `:144` 判 OK。而 git 实际看的是 `core.hooksPath` 指向的**空目录**
⇒ **gate 真哑**（实测 `git commit` **RC=0** 成功提交）。A 与 D 的差别仅在 `core.hooksPath` 是否设置。

**定性**：
- 这是**本批修法的副作用**：HEAD 版在 A/C/D 三种构造下**都**用 `.git/hooks`（不认 `core.hooksPath`），
  所以 A 在 HEAD 下也是 `[OK]`——**假绿先于本批存在**，本批只是把它**收窄到「`agate_common` 挂掉」这一格**
  （`agate_common` 活着时 A 已正确报缺失）。**不是本批引入的新缺陷**。
- 触发条件是**两个前提同时成立**（缺 pyyaml **且** 设了 `core.hooksPath`），真实使用面窄。
- 但它的危害性质正是本批要消灭的那一类（gate 全哑而诊断判绿），且 `:120-121` 的注释
  「并**在状态行里标明这是回退值**」只做到了**回退路径分支**（`:132`），`[OK]` 分支未标。

**建议（MINOR，非阻断）**：回退分支下不判 OK，改判 `[!!]`/`[--]`「**无法确认效力**（`agate_common`
不可用，回退 `.git/hooks`，未校验 `core.hooksPath`）」。即把「我查不到权威位置」如实说成查不到，
而不是拿一个可能错的目录下「全部正常」的结论。**若判为「触发面窄、可接受」，须在 PR 描述里显式认账**
——按仓内口径，呈现/边界类问题不作为 MISALIGNED、不因此开启新一轮。

## 5. 必修项清单

| ID | 级别 | 文件:行 | 问题 | 修法 |
|---|---|---|---|---|
| — | **BLOCKER** | — | **无** | — |
| **M-1** | MINOR（A8） | `CHANGELOG.md:39`、`CHANGELOG.md:41`、`agate/tests/unit/test_agate_doctor.py:561` | 「doctor 里**四处** `except Exception`」实为 **3 处**（HEAD 版 `:43`/`:52`/`:150`，`grep -c` = 3） | 三处「四处」改为「三处」。**注意**：若想表达「修后覆盖 6 处」应另写一句（现状 6 处的数字是对的），不要把两个数字混谈 |
| **M-2** | MINOR（A4） | `agate-doctor.py:166-173`（`hooks_dir_fallback` 分流）、`:87-92`（声明维度真因分流）、`:220-224`（版本维度真因分流）、`:330`（`dict.fromkeys` 去重） | 本轮新增的三段「按真因分流指引」+ 去重**无任何用例守护**：变异 M9/M11/M10 全部 **18 passed**。其中 M9 变异**行为确实倒退**（`agate_common` 挂掉时又建议跑同样跑不起来的 `agate-setup.py`） | 在 `test_doctor_stays_green_exit_when_agate_common_aborts` 里加 2 条断言即可：① `assert "agate-setup.py" not in result.output`（不得建议同环境跑不起来的脚本）；② `assert result.output.count("先让 agate_common 可用") == 1`（去重生效）。两行覆盖 M9+M10+M11 |
| **M-3** | MINOR（A4，可选） | `agate-doctor.py:50-51` | `SystemExit` 的 `code` 为 `None` / 字符串 / 非整数时无守护用例（实测**行为正确**，不崩） | 可加一条参数化用例固化该行为；若不改亦可接受（无缺陷，纯加固） |
| **N-1** | NEEDS_HUMAN_REVIEW | `agate-doctor.py:119-127`（回退分支）、`:144-151`（OK 分支不标目录） | `agate_common` 挂掉 + `core.hooksPath` 覆盖 + `.git/hooks` 有可执行 hook 时判 `[OK] 已安装且可执行`，而 git 真看空目录（实测 `git commit` RC=0 成功）⇒ **gate 真哑而诊断判绿**。假绿先于本批存在，本批把它收窄到该组合 | 回退分支不判 OK，改判「无法确认效力（未校验 `core.hooksPath`）」。或人工认账「触发面窄」并在 PR 描述记录 |

**本轮已闭合项**（保留记录，便于复核「曾经存在而后闭合」）：

| 原 ID | 问题 | 闭合证据 |
|---|---|---|
| R2-a | 账本维度假绿：`_tasks_dir` 失败返回 `None` → `_diagnose_ledger` 判 `[OK]「未发现任务目录」` | `_tasks_dir` 改返回 `(dir, 原因)`（`:76`）；`:277-283` 判 `[!!]「审计未执行」`；加断言（`test_agate_doctor.py:602-607`）；**M8 变异实测转红** |
| R2-b | `README.md:131` 过度声称「两处都只报效力，不报『文件在不在』」 | 改为「效力**而非仅**存在性（缺失/断链仍会报）」⇒ 与 `:132/:155/:157` 严格一致（A2 ⑥） |
| R2-c | 声明维度 `SystemExit` 分支误指路（让人查 `agate.config.yaml` 的 YAML 语法） | `:88-92` 按 `isinstance(exc, SystemExit)` 分流为「先让 agate_common 可用」 |
| R2-d | `hooks_dir_fallback` 只用于「目录不存在」分支，`missing` 分支未用（**M9 发现，作者称等价死代码**） | `:166-173` 已接入 `missing or broken_links` 分支；实测 `agate_common` 挂掉时建议只剩「先让 agate_common 可用」一条 |
| R2-e | 四维度建议里 4 个脚本（`agate-config`/`agate-setup`/`check-events`/`agate-resolve`）同样 `import agate_common` ⇒ 死循环建议 | 四个脚本在忠实缺 pyyaml 下实测 **RC 全 = 1**；终态 doctor 不再建议它们 |
| R2-f | 编辑中间态：`_tasks_dir` 返回元组而 `_diagnose_ledger` 未同步（实跑 `'tuple' object has no attribute 'is_dir'`） | 终态已一致；仅记录，非提交态缺陷 |

## 6. 留痕

原始逐条痕迹：`docs/reviews/agate-alignment-2026-11-26-HOTFIX-DOCTOR-02.progress.md`

## 7. 只读纪律声明

本审查**未修改任何被审文件**。审查开始 `git status` 为 `M `×4 + `MM`×2（作者在审查期间追加修改），
结束时被审文件已由**作者本人** `git add -A` 并 commit `8690c9d2`——提交与我无关，我只读了 blob/工作区。

所有可能产生写副作用的实验（7 + 4 个变异、git 仓库构造、缺 pyyaml 模拟、真实 `git commit` 探针）
**一律在 `mktemp -d` 一次性副本内完成**，且「创建 → 操作 → 清理」在**同一次 bash 调用内**执行
（`trap 'rm -rf "$T"' EXIT`）。**未在 worktree 内执行** `git checkout` / `git stash` / `git restore` /
`git reset` / `git clean` / `git add` / `git commit` / `git push`。

本评审仅新建两个文件：本报告 + 留痕文件。
