---
review_date: 2026-10-09
reviewer: protocol-alignment-review
review_round: r2
change_summary: >-
  RM-AG0105（DEBT0053 + DEBT0058）r2 复核——r1 的 6 项发现处置核实 + 新增传播面
  （README/P3-tdd/dispatch-prompt）+ 补修 agate_dispatch_route.py/check-protocol-consistency.py 的
  5 处 R6 缺陷 + DEBT0063 登记。
files_changed:
  - CHANGELOG.md
  - agate-workspace/debt/tech-debt.md
  - agate-workspace/roadmap/roadmap.md
  - agate/assets/templates/dispatch-prompt.md
  - agate/phase-cards/P3-tdd.md
  - agate/scripts/README.md
  - agate/scripts/agate_dispatch_route.py
  - agate/scripts/check-platform-assumptions.py
  - agate/scripts/check-protocol-consistency.py
  - agate/scripts/check-state-transition.py
  - agate/tests/scripts/test_check_platform_assumptions.py
  - agate/tests/unit/test_check_state_transition.py
  - agate/tests/unit/test_release_workflow.py
---

# 协议-脚本对齐审查 r2（RM-AG0105 / DEBT0053 + DEBT0058）

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **ALIGNED**（r1 悬空引用已修；残留 1 处 nit） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（有意义的目标均已传播；残留仅内部测试注释） |
| A4 | 测试覆盖 | **MISALIGNED**（⚠️ **新增测试代码触发 ruff SIM105 ⇒ CI ruff job 转红**；负例判别力已修 ✓） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**（同 r1；另 DEBT0063 已登记） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（边界已成文、scripts 缺陷已修；CHANGELOG 有 1 处 minor 未提 scripts） |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **MISALIGNED**（「83 passed」**仍不可复现**；其余 4 条 ✓） |

**总判定：MISALIGNED（A4 / A8）——尚不可 commit。** 阻断项：**ruff SIM105**（CI ruff job 转红）+「83 passed」数字。

---

## 一、r1 六项发现逐条核实

### ① 悬空引用（README 无「判据边界」节）→ ✅ 已修

`agate/scripts/README.md:104-118` 新增节 **`### check-platform-assumptions.py 的 R6 判据边界（RM-AG0105 / DEBT0058）`**，含 5 条局限表 + 「启发式，非完备证明」结论。扫描器 docstring `check-platform-assumptions.py:55` 的「见 README 判据边界」**现指向真实存在的节** ✓。
**残留 nit（非阻断）**：docstring 同句仍写「**同文件**多调用/字符串内括号属已知近似」，而 README 表写「**同一行**两个调用」。实测真实局限是**同一行**多调用（跨行/同文件多调用处理正确）⇒ docstring 措辞不准，建议与 README 对齐。

### ② 反向传播（R1-R5 未提 R6）→ ✅ 已修（有意义目标）

- `agate/scripts/README.md:91` → **R1-R6** ✓
- `agate/phase-cards/P3-tdd.md:104` → **R1~R6**（+ R6 语义）✓
- `agate/assets/templates/dispatch-prompt.md:146` → **R1~R6**（+ R6 语义）✓
- `test-designer.md` 本就不枚举规则号（无 stale）✓
**残留（非阻断）**：`test_cross_milestone.py:22` 注释、`test_check_platform_assumptions.py:14/121` 内部注释、`tests/README.md:101`「回归 (R1-R5)」——均非面向 writer 的规则清单，影响轻微。`check-platform-assumptions.py:134`「逐行跑 R1-R5 正则」**准确**（R6 非行级），无需改。

### ③ BDD-3 测试负例无判别力 → ✅ 已修（实测有判别力）

`test_check_state_transition.py:1205` 负例改为含「重派」的散文串。**用旧实现（未收窄逻辑）scratch 复现**：

| 输入 | 旧实现 | 新实现 | 判别力 |
|---|---|---|---|
| `**dispatch-context 先写后派，绝不补写**。拆并行/**重派**时每个子任务各写一个。` | **True（命中）** | **False** | **有判别力** ✓ |
| `- RM-AG0003：dispatch-protocol.md L105-135 空返回恢复全手动` | True | False | 有判别力 ✓ |
| `- 注：本批 subagent 3 次空返回…` | True | True | 正例（预期同）|

⇒ 负例现能**真正证明**收窄生效（旧实现下该断言会转红）✓。

### ④ R6 边界 → ✅ 已入 README（5 条逐条与代码一致）

逐条对照实现 `_r6_text_without_encoding_hits`（`check-platform-assumptions.py:49-78`）实测：

| README 局限（:112-116）| 实测 | 一致 |
|---|---|---|
| 同一行两个调用 ⇒ 可能漏报 | 合并块 → 漏报 | ✓ |
| `encoding=` 在字符串/注释 ⇒ 假阴性 | 视作满足 → 假阴 | ✓ |
| 单次调用跨 >40 行 ⇒ 可能误报 | 窗内 text/窗外 enc → 误报 | ✓ |
| 属性行（`subprocess.PIPE`）⇒ 可能误报 | `hits=[1,3]`，属性行被误报 | ✓ |
| 仅注释提及 `subprocess.` ⇒ 可能误报 | 注释行被当起点 → 误报 | ✓ |

### ⑤ R6 扫 `agate/scripts` 的 5 处真缺陷 → ✅ 已修

`agate_dispatch_route.py:569/574/605/621`（4 处）+ `check-protocol-consistency.py:529`（1 处）补 `encoding="utf-8"`。
**实测 R6 扫 `agate/scripts` = 0 命中；扫 `agate/tests` + `agate/scripts` = 0 命中** ✓。

### ⑥ flaky 用例 → ✅ 已登记 DEBT0063

`agate-workspace/debt/tech-debt.md` 新增 DEBT0063（`test_m1_forward_jump_p2_to_p5_blocked` 跨文件 flaky），`check-debt.py` rc=0 ✓。⚠️ **小瑕疵（非阻断）**：DEBT0063 标题写 `test_m1_forward_jump_p2_to_p5_blocked`，而 r1 实测转红的是 `test_m1_forward_jump_p0_to_p7_blocked`（`test_pre_commit_hook.py:979`）；二者同为该文件的前向跨阶用例，建议核实标题指向的用例名是否准确。

---

## 二、r2 新增发现

### ★ 阻断项：ruff SIM105（本批引入，CI ruff job 转红）

```
$ ~/.venvs/agate-dev/bin/ruff check agate/          # ruff 0.16.4，与 CI 锁定一致
SIM105 Use `contextlib.suppress(SystemExit)` instead of `try`-`except`-`pass`
    --> agate/tests/unit/test_check_state_transition.py:1191:5
Found 1 error.
```

- 位置 = **本批新增**的 `test_rm_ag0105_bdd3_scan_narrowed_to_event_lines` 内 `try: spec.loader.exec_module(mod) except SystemExit: pass`。
- **对照**：`git show HEAD:agate/tests/unit/test_check_state_transition.py` → ruff **All checks passed!** ⇒ **本批引入的回归**。
- **CI 口径**：`.github/workflows/protocol-tests.yml:254` 跑 `pip install ruff==0.16.4 && ruff check agate/` ⇒ 该 job 转红。
- **是否阻断合并**：workflow 头注释（:17）明确「platform-scan/**ruff 非 required**」⇒ 不阻塞合并；但 `AGENTS.md` 发布清单第 5 条要求「**CI ruff job 绿**」，且相对 HEAD 是**净回归** ⇒ 应修（改用 `contextlib.suppress(SystemExit)` 或 `with`）。

### 其它（非阻断）

- **CHANGELOG 未提 scripts 的 5 处修复**（`CHANGELOG.md:85` 仍只写「抓到 **3 处**真缺陷（`test_release_workflow.py`）」）——本批实际修了 3（tests）+ 5（scripts）= 8 处；建议补一句「并修复 `agate/scripts` 同类 5 处」。
- **`agate_dispatch_route.py:684`** 有一处**纯格式化**改动（`_default_subprocess_run` 的调用由两行并一行；该调用**原本已含** `encoding="utf-8"`，非 R6 命中点）。语义等价、ruff 通过，属无害，但非必要，可还原以缩小 diff。
- **批量替换无其它破坏**：7 个改动 py 文件 `ast.parse` 全通过、**无重复 kwarg**（ast 全树扫描 Call.keywords 去重）、`py_compile` 通过；`agate_dispatch_route.py` 仅 4 处 encoding 增补 + 1 处格式化，`check-protocol-consistency.py` 仅 1 处 encoding 增补（逐 hunk 核对）。

---

## 三、A8 声称-命令绑定（逐条复现）

| 声称（本轮）| 命令 | 实测 | 结论 |
|---|---|---|---|
| **1 failed(环境) / 2906 passed** | `python3 -m pytest agate/tests/ -q -n auto -p no:cacheprovider` | **1 failed, 2906 passed, 2 skipped**（唯一 failed = `test_bdd_43_opencode_registration_and_debug_agent`，环境：本机 opencode v2.0.23 只有 `agents` 子命令；该用例文件头声明 GitHub Actions 除外 ⇒ CI 不受影响；r1 的 flaky 用例本轮未复现）| ✅ **准确** |
| **0 ERROR** | `python3 agate/scripts/check-protocol-consistency.py` | `仅有 424 个 WARNING，无 ERROR`，rc=0 | ✅ 复现 |
| **扫描 0 命中** | `python3 agate/scripts/check-platform-assumptions.py`（默认 tests/）+ R6 扫 tests+scripts | rc=0；R6 命中 **0** | ✅ 复现 |
| **check-debt rc=0** | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | rc=0（含新 DEBT0063）| ✅ 复现 |
| **83 passed** | `python3 -m pytest agate/tests/scripts/test_check_platform_assumptions.py agate/tests/unit/test_check_state_transition.py -q` | **78 passed**（18 + 60）；三改动测试文件 = **96 passed**；试 `agate/tests/scripts/`(18) 等组合亦非 83 | ❌ **仍不可复现**（须改正或给出产出 83 的确切命令）|

**上一轮 r1 指出的 2 处数字**：① 「2906 passed」→ 本轮已**准确**（明确 1 failed 为环境）；② 「83 passed」→ **仍未改正/未复现**。

---

## 四、A4b：既有测试转红 + 夹具更新清单（本轮无变化）

同 r1：本批使 **2 条既有用例**转红且均已处置——`test_bdd_1`（子串断言→调用形态断言）、`test_bdd_8`（R6 命中 `test_release_workflow.py` → 补 `encoding=`）；其余既有用例（BDD-3 五条 + `cross_milestone::test_bdd_16`）实测不红。
**新增**：`agate/scripts` 的 5 处 R6 修复属**生产脚本**（非既有测试用例），不改变既有用例的红/绿；`check-protocol-consistency.py` 自身即一致性脚本，改后仍 0 ERROR ✓。
**空清单项**：除上述外，经实测无其它既有用例转红。

---

## 五、是否可 commit

**否——尚不可 commit。** 先修：

1. **【阻断】ruff SIM105**：`agate/tests/unit/test_check_state_transition.py:1191` 的 `try/except SystemExit: pass` → 改 `contextlib.suppress(SystemExit)`（或等价）。修后 `~/.venvs/agate-dev/bin/ruff check agate/` 须 `All checks passed!`。
2. **【阻断】「83 passed」**：改为可复现数字（实测两回归文件 = **78 passed**）或给出产出 83 的确切命令。

**建议（非阻断，可顺手）**：
3. `CHANGELOG.md:85` 补提 `agate/scripts` 同类 5 处修复（现只写 3 处）。
4. 扫描器 docstring `:55`「同文件多调用」→「同一行多调用」（与 README 一致）。
5. DEBT0063 标题核对用例名（`p2_to_p5` vs `p0_to_p7`）。
6. `agate_dispatch_route.py:684` 纯格式化改动可还原以缩小 diff。

**NEEDS_HUMAN_REVIEW**：无。

---

## 附：本轮执行的验证命令（证据）

```bash
python3 /tmp/opencode/a0105/ast_check.py                 # 7 文件 ast + 无重复 kwarg
python3 -m py_compile agate/scripts/agate_dispatch_route.py agate/scripts/check-protocol-consistency.py
~/.venvs/agate-dev/bin/ruff check agate/                 # -> SIM105, Found 1 error
~/.venvs/agate-dev/bin/ruff check /tmp/.../HEAD版test_check_state_transition.py   # -> All checks passed!
python3 -c "…_r6_text_without_encoding_hits over agate/tests + agate/scripts"     # -> 0
python3 /tmp/opencode/a0105/bdd3_old_vs_new.py           # 负例 old=True new=False（有判别力）
python3 agate/scripts/check-platform-assumptions.py       # rc=0
python3 agate/scripts/check-protocol-consistency.py       # 0 ERROR, rc=0
python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md   # rc=0
python3 -m pytest agate/tests/ -q -n auto -p no:cacheprovider           # 1 failed, 2906 passed, 2 skipped
python3 -m pytest <三个改动测试文件> -q                                   # 96 passed
```

*留痕文件：`docs/reviews/agate-alignment-2026-10-09-A0105-SCAN-02.progress.md`*
