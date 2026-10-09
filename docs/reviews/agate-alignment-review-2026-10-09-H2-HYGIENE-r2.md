---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: 批 B / H2 第 2 轮——第 1 轮 5 项已改（/tmp 字面量、CHANGELOG、声称、第三处 check-gate.py、匿名化正则），另新增 CHANGELOG 两条；本轮复核发现第三处修复引入「外部工作区」回归
files_changed: [CHANGELOG.md, agate/scripts/agate-feedback.py, agate/scripts/agate-render-dispatch-prompt.py, agate/scripts/check-gate.py, agate/scripts/check-retrospective.py, agate/tests/unit/test_agate_feedback.py, agate/tests/unit/test_agate_render_dispatch_prompt.py, agate/tests/unit/test_check_retrospective.py]
---

# 协议-脚本对齐审查（第 2 轮）

> 审查对象：分支 `hotfix/batch-b-hygiene`（**未提交**，改动在工作区）。全程只读——未改任何协议/脚本/测试，
> 未 commit / push。跑测试前后 `git status --porcelain` 一致（8 个被评审文件 + 审查留痕/成果文件）。
> 第 1 轮报告：`docs/reviews/agate-alignment-review-2026-10-09-H2-HYGIENE.md`。
> 留痕：`docs/reviews/agate-alignment-2026-10-09-H2-HYGIENE-02.progress.md`。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **MISALIGNED** |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | ALIGNED |
| A7 | 设计原则一致性 | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED |

**一句话**：第 1 轮的 4 项（/tmp 字面量、CHANGELOG 缺口、声称、匿名化过度收窄）**已确实修好**，
全量 pytest 从「2 failed」回到「1 failed（既有环境项）/ 2892 passed」；但**第 5 项（第三处
`check-gate.py:1930`）的修法本身引入了一条新回归**——它在「项目外工作区」这一 SETUP.md 明文支持的
场景下算出**错误**的 debt 路径（旧代码在该场景是**对**的），且该处**无回归用例**；CHANGELOG 对该处
机制的描述也与实现不符。

---

## 第 1 轮 5 项逐条核实

| 项 | 第 1 轮问题 | 本轮核实 | 证据 |
|----|------------|----------|------|
| 1 | 新用例 `/tmp/x/y` 字面量打破 t42 平台自查 | **✅ 已修** | 源码改 `str(tmp_path / "x" / "y")`（`test_agate_feedback.py:241`）；`python3 agate/scripts/check-platform-assumptions.py agate/tests/` → **0 命中**（exit 0）；`test_check_platform_assumptions.py` + `test_t42_p3_platform_selfcheck.py` → **21 passed** |
| 2 | CHANGELOG 未加 RM-AG0082/RM-AG0084 | **✅ 已补（文字有 2 处瑕疵）** | `CHANGELOG.md:27-35` 新增两条；瑕疵见 A2 |
| 3 | 声称「63/78/95 passed」不可复现 | **✅ 已换可复现计数** | `python3 -m pytest agate/tests -q -n auto` → `1 failed, 2892 passed, 2 skipped`（1 failed = 既有 opencode 环境项）；3 个改动测试文件 → `49 passed`。commit message 本身未落盘，无法核字面，但计数可复现 |
| 4 | 第三处 `check-gate.py:1928` 同款 | **⚠️ 已改，但引入新回归 + 无用例** | 见下 A3/A4（**本轮核心发现**） |
| 5 | 匿名化过度收窄（`/data/secret` 漏脱敏） | **✅ 已修** | 见下 A1 重点结论 |

---

## 逐项审查

### A1: 文档→脚本对齐

**协议文档声明**（同第 1 轮）：`agate/SETUP.md:381-391` 与 `agate/WORKFLOW.md:85` 声明工作区经
`.agate.env` / `AGATE_TASKS_DIR` 覆盖、解析归口 `agate_common.resolve_workspace`；
`agate/assets/templates/retrospective-template.md:150` 声明「绝对路径等由 `agate-feedback.py` 脱敏」。

**脚本实现（本轮）**：

- 工作区推导：三处（`check-retrospective.py:74-104`、`agate-render-dispatch-prompt.py:51-77`、
  `check-gate.py:1930-1940`）均改走 `resolve_workspace`。方向与文档一致。
- 匿名化正则（`agate-feedback.py:47-53`）：
  ```python
  ABS_PATH_RE = re.compile(
      r"(?:"
      r"[A-Za-z]:\\[^\s'\"`]+"                                        # 1. Windows 盘符
      r"|/(?:home|Users|tmp|var|etc|opt|root|mnt|srv|usr)/[^\s'\"`]+" # 2. Unix 已知顶层
      r"|/[A-Za-z0-9._-]+/[^\s'\"`]+"                                 # 3. 首段为 ASCII 路径段、≥2 段
      r")"
  )
  ```

**独立探针（真实 `findall`）**：

| 样本 | 第 1 轮（≥3 段） | 本轮（ASCII 首段） | 判定 |
|------|------------------|--------------------|------|
| `/data/secret` / `/proj/foo` / `/app/src` | ❌ 漏 | ✅ 命中 | **过度收窄已修** |
| `机制/执行层面` | ✅ 不命中 | ✅ 不命中 | 保持 |
| `机制/执行/流程/层面` | ⚠️ 命中（残留假阳） | ✅ **不命中** | 额外改善 |
| `/home/x` `/tmp/a` `/var/log/x` `/opt/a/b` `/usr/local/x` `C:\Users\b` | ✅ | ✅ | 保持 |
| `/media/usb/x` `/run/x` `/boot/vmlinuz` `/_private/x` `/.config/x` | ✅ | ✅ | 保持 |

**残留面**（更宽侧，不牺牲隐私）：
- **过度脱敏**（与原正则同类，非本批新增）：ASCII 斜杠链 ≥2 段仍命中——`P1/P2/P3` → `/P2/P3`、
  `a/b/c` → `/b/c`、`foo/bar/baz` → `/bar/baz`、`机制/P1/P2` → `/P1/P2`。属「宁可多留不可漏」侧。
- **新的窄漏脱敏**：**首段为 CJK** 的绝对路径（`/项目/secret` → 不命中）与**单段**路径（`/data`）
  不再脱敏。极罕见，可接受，但建议在注释里显式声明该残留面（现注释只提「首段为 ASCII」，未点明
  CJK 首段会漏）。

**结论**：ALIGNED。第 1 轮 A1 重点结论 3 的过度收窄已修，且额外修掉了第 1 轮未点名的 CJK 残留假阳。

### A2: 脚本→文档对齐

**变更**：`CHANGELOG.md:27-35` 新增 RM-AG0084 / RM-AG0082 两条。**发现 2 处文字与实现/事实不符**：

1. **「两处」vs 列 3 文件**：条目标题写「**两处**设备路径推导绕过 `resolve_workspace()`」，
   正文却列 `check-retrospective.py`、`agate-render-dispatch-prompt.py`、`check-gate.py` **三个**文件
   （正文括号自注「第三处」）。读者见「两处」再看 3 个文件会困惑。建议改「三处」或「多处」。
2. **机制描述与 `check-gate.py` 实现不符**：条目写「改为**向上找项目根（含 `.agate.env` 或
   `agate-workspace/`）**后交 `resolve_workspace` 解析」。但 `check-gate.py:1934` 用的是
   `run_git(["rev-parse", "--show-toplevel"], cwd=task_dir)`（**git 顶层**），**不是** walk-up。
   该不符不只是措辞——**正是这个「git 顶层」取法**导致外部工作区回归（见 A3）。

**结论**：**MISALIGNED**（文档描述与代码不一致，须改文档或改代码；两处都指向同一根因）。

### A3: 一致性连锁 + 反向传播

**A3a**：本批文档面只动了 CHANGELOG；两处修复本身无需改协议正文（文档早已声明权威解析器）。

**A3b — 第三处修复的正确性（本轮核心）**：

`check-gate.py:1930-1940`（gate_p7 的 BDD-66 debt 定位）改为：
```python
_ws_debt = os.path.dirname(os.path.dirname(os.path.abspath(task_dir)))   # 旧推导
if resolve_workspace is not None:
    _pr = None
    if run_git is not None:
        _rc_pr, _out_pr = run_git(["rev-parse", "--show-toplevel"], cwd=task_dir)
        if _rc_pr == 0 and _out_pr.strip():
            _pr = _out_pr.strip()
    if _pr is None:
        _pr = _ws_debt                      # ← 把「工作区」当「项目根」喂给 resolve_workspace
    _ws_debt, _ = resolve_workspace(_pr)
debt_file = os.path.join(_ws_debt, "debt", "tech-debt.md")
```

**用真实代码路径实测**（`importlib` 加载 `check-gate.py`，monkeypatch 掉聚合器以抵达 debt 解析段，
`resolve_workspace`/`run_git` 用真实函数）：

```
A 默认布局      debt_file=/tmp/.../A/agate-workspace/debt/tech-debt.md       ✅ 正确
B .agate.env 覆盖 debt_file=/tmp/.../B/custom-ws/debt/tech-debt.md           ✅ 正确（修复目标达成）
C 外部工作区    debt_file=/tmp/.../C/ws/agate-workspace/debt/tech-debt.md   ❌ 错误（应 .../C/ws/debt/...）
```

- **C 场景 = SETUP.md:388 明文支持**：`AGATE_WORKSPACE=/srv/agate-ws/My Project`（项目外绝对路径）。
  task_dir 落在**项目 git 仓库之外** ⇒ `run_git --show-toplevel cwd=<外部 task_dir>` **失败**
  （实测 `fatal: 不是 git 仓库`，rc=128；且 pre-commit hook 环境 **GIT_DIR 未设**——实测 hook 打印
  `GIT_DIR=<unset>`）⇒ `_pr = _ws_debt`（= 工作区）⇒ `resolve_workspace(工作区)` 返回
  `<工作区>/agate-workspace` ⇒ **debt_file 多了一层**。
- **这是回归**：**旧代码 `dirname²(task_dir)` 在 C 场景本就正确**（= `<ws>`）；新代码把它改错了。
- **失败模式是阻断性**：gate_p7 对 `basis: followup:DEBT<n>` 找不到条目时 `return 1`
  （`check-gate.py:1952-1956`）⇒ 外部工作区项目会被**误阻断 commit**。
- **对比另两处**：`check-retrospective.py` / `agate-render-dispatch-prompt.py` 用 **walk-up**（找不到
  标记就回退 `dirname²`），在 C 场景**正确**（实测：check-retrospective 打印机制缺口、render 占位符
  指向 `<ws>`）。⇒ 三处修复**取法不一致**，其中 run_git 取法在外部工作区失效。
- **注**：该 run_git 取法是从 gate_p4 的 DEBT0016 修复**照搬**的（`check-gate.py:1238-1247`）——
  gate_p4 同样在 C 场景会错，但它 WARNING-only（fail-open）；照搬到 gate_p7 后变成阻断性
  （注释自称「本处为 `return 1` 阻断性，比另两处更重」，却仍沿用 fail-open 场景下可容忍的取法）。

**A3b — 是否还有第四处同款？→ 无**（grep 复核）：
`grep -rn "dirname(os.path.dirname\|dirname(dirname" agate/scripts/*.py` 的 task_dir 起点命中仅
`check-gate.py:1236/1245`（DEBT0016）、`check-gate.py:1930`（本处）、`check-retrospective.py:104`、
`agate-render-dispatch-prompt.py:77`；其余均 `__file__`/脚本路径起点。另查 `parent.parent`/`os.pardir`
惯用式，仅 `agate_common.py:41`、`agate-release.py:282`（均脚本路径）。**无第四处**。

**结论**：**MISALIGNED**（第三处修复引入外部工作区回归；取法与另两处不一致）。

### A4: 测试覆盖

**第 1 轮问题已修**：`test_agate_feedback.py:231-250` 的新用例现已覆盖 `/data/secret`（第 1 轮点名的
过度收窄类），并改用 `str(tmp_path / "x" / "y")`（不写 `/tmp` 字面量）。

**最近一次全量实跑（本审查独立执行，`-n auto`）**：
```
$ python3 -m pytest agate/tests -q -n auto
1 failed, 2892 passed, 2 skipped in 86.12s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
        （既有环境项：opencode CLI 无 `debug agent` 子命令，与本 diff 无关）
$ python3 -m pytest agate/tests/unit/test_agate_feedback.py agate/tests/unit/test_agate_render_dispatch_prompt.py agate/tests/unit/test_check_retrospective.py -q -n auto
49 passed
$ python3 -m pytest agate/tests/scripts/test_check_platform_assumptions.py agate/tests/unit/test_t42_p3_platform_selfcheck.py -q
21 passed
```
⇒ 第 1 轮引入的 t42 回归已消除（全量从 `2 failed` → `1 failed`）。

**MISALIGNED — 第三处修复无回归用例**：
- `git status` 显示 `test_check_gate.py` **未修改**；`grep -rn "followup:DEBT\|design_gap_reviews" agate/tests/unit/test_check_gate.py` **0 命中** ⇒ gate_p7 的 BDD-66 debt 解析段（含本次改的 `:1930-1940`）**无任何用例覆盖**。
- 后果：外部工作区回归（A3）**不会被现有测试发现**——正需要一个「`.agate.env` 指向项目外工作区」的用例来守护。建议补：
  ① `.agate.env` 覆盖（正例，与另两处对称）；② 外部工作区 / 非 git task_dir（反例，守护 `run_git` 失败路径）。

**结论**：**MISALIGNED**（第三处改动缺用例，且缺的正是能抓出回归的边界）。

### A5: 下游影响 + 文档传播

- **破坏性变更（新）**：第三处修复对**外部工作区项目**（SETUP.md:388 明文支持）产生行为变化——
  旧的正确 debt 路径被改错（A3）。这是「影响已有项目 gate 行为」的实打实下游影响。
- **CHANGELOG**：第 1 轮缺口已补（见 A2，文字有瑕疵）。
- **协议文档传播**：无需（工作区解析文档早已声明权威源；本次无新规则）。
- **第 1 轮的 t42 下游回归已消除**。

**结论**：**MISALIGNED**（外部工作区行为回归 = 下游影响，根因同 A3）。

### A6: 锚点表覆盖

- 未新增协议规则 / 脚本；被改脚本均已在 `agate/scripts/README.md` 登记；无新增 basename 需补登记面。
- `check-protocol-consistency.py` 实跑 **0 ERROR**（414 frozen WARNING，均历史冻结文件；含本次新增
  CHANGELOG 段落，未被 CHECK 13 判为问题）。

**结论**：ALIGNED。

### A7: 设计原则一致性

- **ADR-014「判据单一权威源」**：三处均归口 `resolve_workspace`，方向契合。
- **观察（与 ADR-014 精神相关）**：三处修复**取法不一**——另两处用 walk-up，`check-gate.py` 用
  `run_git --show-toplevel`。二者都能命中「标准仓库内 + `.agate.env` 覆盖」，但只有 walk-up 在
  外部工作区正确。同一「找 project_root」语义出现两种实现，正是 ADR-014 想收敛的重复判据；
  建议统一（下沉 `agate_common` 一个小工具，或 `check-gate.py` 改用 walk-up）。
- 未见需新增 ADR 的架构决策。

**结论**：ALIGNED（原则方向一致；实现统一性作为建议）。

### A8: 声称-命令绑定

| 声称（本轮） | 命令 | 结论 |
|------|------|------|
| 「已改为 `str(tmp_path / "x" / "y")`，源码无 `/tmp` 字面量」 | `grep -n '/tmp' agate/tests/unit/test_agate_feedback.py`（仅注释/docstring 内，均后跟反引号不触发 R4）；`python3 agate/scripts/check-platform-assumptions.py agate/tests/` → exit 0 | **✅ 成立** |
| 「`test_check_platform_assumptions.py` + `test_t42...` 全绿」 | `pytest ... -q` → `21 passed` | **✅ 成立** |
| 「已补 RM-AG0082 / RM-AG0084 两条到 `[Unreleased] ### 修复`」 | `sed -n '27,35p' CHANGELOG.md` | **✅ 成立**（文字瑕疵见 A2） |
| 「全量 2892 passed / 2 skipped / 1 failed 环境项」 | `python3 -m pytest agate/tests -q -n auto` | **✅ 逐字成立** |
| 「定向计数」 | `pytest test_agate_feedback.py test_agate_render_dispatch_prompt.py test_check_retrospective.py -q -n auto` → `49 passed` | **✅ 成立** |
| 「第三处已改用 `resolve_workspace`（run_git 取 project_root，失败回退旧推导）」 | 读 `check-gate.py:1930-1940` | **⚠️ 半成立**：确已改；但「失败回退旧推导」不准确——失败时把 `dirname²` 当**项目根**喂给 `resolve_workspace`，并非直接用旧推导（正是回归来源，见 A3） |
| 「判据 3 改为首段 ASCII 路径段」 | 读 `agate-feedback.py:51` + 正则探针 | **✅ 成立** |

**结论**：ALIGNED（可复现计数成立；唯一不准确处「失败回退旧推导」已在 A3 记为回归，不另立无据声称）。
commit message 未落盘，无法核其字面——本轮以可复现命令为准。

---

## 需修复 / 待裁决清单（本轮）

| # | 项 | 归属 | 严重度 | 动作 |
|---|----|------|--------|------|
| 1 | **第三处 `check-gate.py:1934` 的 `run_git` 取法在「外部工作区」场景算出错误 debt 路径（旧代码该场景正确）→ gate_p7 误阻断** | A3/A5（**MISALIGNED**） | 中（阻断性，但场景较少） | **必须修**：改用与另两处一致的 walk-up（找不到 marker 时**直接用** `dirname²`，不要再喂 `resolve_workspace`）；或至少让「run_git 失败」分支直接 `_ws_debt = dirname²` 不经 `resolve_workspace` |
| 2 | 第三处修复**无回归用例** | A4（**MISALIGNED**） | 中 | 补 2 条：`.agate.env` 覆盖（正例）+ 外部工作区/非 git task_dir（反例） |
| 3 | CHANGELOG 文字：标题「两处」却列 3 文件；机制描述「向上找项目根」与 `check-gate.py` 的 `run_git` 取法不符 | A2（**MISALIGNED**） | 低 | 改「三处」；机制描述与实现对齐（或随 #1 把实现统一为 walk-up 后描述即成立） |
| 4 | 匿名化残留面未在注释声明：CJK 首段（`/项目/secret`）、单段（`/data`）会漏脱敏 | A1（观察） | 低 | 注释补一句残留面；可选补 `/项目/x` 边界用例 |

> 无 NEEDS_HUMAN_REVIEW 项：本轮 MISALIGNED 均有明确判据与修复方向。
