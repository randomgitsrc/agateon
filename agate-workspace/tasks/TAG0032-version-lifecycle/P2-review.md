---
phase: P2
task_id: TAG0032
type: review
parent: P2-design.md
trace_id: TAG0032-P2review-20260907
status: approved
created: 2026-09-07
agent: plan-eng-review
---

# P2-review — TAG0032 版本管理生命周期可用性批（工程经理视角，独立评审）

[PROD_NOT_TOUCHED]

**评审对象**：`P2-design.md`（candidate_count: 4 = A1/A2/B1/B2；domains=[backend, cli]；risk_level: high；
dispatch_plan: serial 两批）
**评审方式**：C8 映射 backend + high → 单角色 plan-eng-review，无组长汇总，直接产出本文件。
**结论**：**approved** — 无阻塞级架构问题。决策 A1 / B1 的取舍站得住，最高风险面（消费方归口声明）经
独立 grep 复核属实，断点一守卫落点正确，minimal_validation 复现可信。4 项非阻塞澄清项列入「架构问题
（非阻塞）」与「测试缺口」，P4 implementer 须落实，不需退回 architect 重做方案。

复核实跑证据（read/grep/bash，未改任何文件；涉安装路径用隔离 HOME `HOME=$(mktemp -d)` 测完即删）：
- `check-protocol-consistency.py --strict-errors-only` → EXIT=0 / 329 WARNING / **0 ERROR**（§4.3 checklist 5、R6 基线声明属实）
- `shellcheck -S warning install.sh` → rc=0；`shellcheck -S warning agate/scripts/*.sh` → rc=0（`P5_shellcheck_root` 基线属实）
- `agate/tests/scripts/count-tests.sh` 存在（§6 对 dispatch 指引 `agate/tests/tests/scripts/` 的校正属实）
- 隔离 HOME 复现断点一：`os.path.islink(base)=True` 且 `isdir(base)=True`；`os.makedirs(base, exist_ok=True)` 穿透软链无报错；`repo/` `realpath` 落软链目标内部 `[PROD_NOT_TOUCHED]`

---

## 8 项重点核查项逐条结论

### 核查 1 — 决策 A 选 A1（resolve 侧增量探测 `_protocol_root`）是否站得住 → **通过**

**1a · `_protocol_root` 探测顺序与两形态皆无时的 fail-closed（§2 候选 A1 代码块 L95-103、M3、I-11）**
探测链 `isdir(vdir/scripts) → vdir`（探测序 1，红线）→ `isdir(vdir/agate/scripts) → vdir/agate`（探测序 2）→
两者皆无 `→ vdir` 原样。核对 `resolve-entry.py:49-52`：返回 `vdir` 原样后 `os.path.join(root, "scripts", gate_py)`
拼 `vdir/scripts/<gate>` 不存在 → `:50` `os.path.isfile` 判否 → `:51-52` `stderr + sys.exit(1)`（fail-closed
分支实测存在，未被本方案删除或改写）。**无静默放行风险**（I-11 守住）。「根即协议」部署方由探测序 1
先命中直接零回归（BDD-7），探测顺序在 helper 单点、无散落（R2 缓解成立）。

**1b · `version` 推导顺序（R1 / M5 / I-1 红线）**
现码 `agate_common.py:190` = `return {"root": cur, "version": os.path.basename(cur), ...}`，`basename` 取自
`cur`（= `_resolve_pointer_chain` 命中的版本目录），不取自 `_protocol_root` 返回值。M4 `.agate-version` ok
分支（L182-183）`version` 恒取 `declared`（字符串常量），结构性免疫。§9 note 2 已把机制说清（"顺序倒置则
version 变 'agate'"），BDD-6 / BDD-7 双 fixture 逐条断言 `AGATE_VERSION=vX.Y.Z`。
*非阻塞措辞建议*：M5 "顺序不可倒" 的精确表述是「`version` 恒取 `os.path.basename(cur)`（从 `cur` 取，
不从 `_protocol_root(cur)` 返回值取）」——不是语句先后，是 `basename` 的入参对象。P4 按此实现即可，
不影响方案成立。

**1c · 消费方影响面归口声明（DEBT0016 dirname 散点教训，本任务最高风险面）— 独立 grep 复核【属实】**
- `resolve_version_root` / `resolve_hook_root` / `resolve_agate_root` / `resolve_rules_root`（`agate_common.py:198-239, 663-677`）
  全部经 `_resolve_version_info`（`:166`）归口。
- `check-structure-consistency.py:_resolve_root()`（L107-113）→ `resolve_agate_root(__file__)`；
  `check-yaml-schema.py:_resolve_root()`（L139-145）→ `resolve_agate_root(__file__)`。两者 `root/rules`、
  `root/scripts/check-protocol-consistency.py`（`check-structure-consistency.py:528`）均消费归口 `root`，
  A1 返回 `vdir/agate` 后自然命中。
- `agate-dispatch.py:_resolve_agate_root` + `agate-inject-card.py:_agate_root` → `resolve_agate_root`（归口，
  §1.2 列备 P8 核对，属受益方）。
- 全脚本 grep `os.path.dirname` × `"scripts"` join：**无 `os.path.dirname(vdir)+"/scripts"` 旁路**。
  `check-protocol-consistency.py:812` 硬编码 `root/"agate"/"scripts"` 属仓库根 git-tree 检查器（消费 git repo
  根，非版本解析链），不受本方案影响。
- §9 note 2 引用行号 `:528/:545`（check-structure-consistency）、`:155`（check-yaml-schema）相对实际
  （`528` ✓ / `547` / `151`+`157`）有轻微漂移，实质正确，不阻塞。

**1d · A2 被否理由（R10 + out-of-scope）是否成立 → 成立**
A2（install 侧把 `vX/agate/` 提升为版本根）确会破坏 `git worktree add --detach` 检出的索引一致性——
`_cmd_uninstall`（`agate-install.py:316-324`）依赖 `git worktree remove` / `worktree prune`，move/删子目录后
可能误判。且 A2 须在 `install-offline.py`（`copytree`）、Windows 复制模式各自复制变形逻辑 → 被迫触碰
out-of-scope「install-offline 适配」「Windows 复制模式专项」。A1 是解析侧最小增量、单点归口、离线/复制模式
解析侧经同一 `_resolve_pointer_chain` 自然受益（I-7）。**A1 更干净，选择理由自洽。**
"agateon 仓库形态重构" 作不采纳备选记录，理由（影响面远超本任务、P0-brief 明列 out-of-scope）成立。

### 核查 2 — 决策 B 选 B1（副本 copytree）是否站得住 → **通过**

**2a · B2（软链）被否理由 → 成立**
① `repo/` 或被指向版本目录被删 → 软链悬空 → `~/.agate/scripts/agate-install.py` No such file，正是 I-3
点名的「repo 删则断」、也正是断点一要消灭的症状；② Windows 退化为复制后升级期又需重跑 → 跨平台双口径
（UPGRADING 要写两套）；③ 软链目标（元仓库形态 = `vX/agate/scripts/`）计算与决策 A1 探测结果耦合。
三条抵消 B2 的「自动跟随」优点，否决理由自洽。

**2b · B1 的代价（升级期须重跑 `agate-install.py latest` 刷新副本）是否被充分锁定 → 是**
- BDD-4 判据 2：`agate/tests/` 须含「重跑 latest 后根 `scripts/` 副本随 current 刷新」单测（副本语义单测锁）。
- M7 UPGRADING「版本管理生命周期」节含「根 `~/.agate/scripts/` 维护语义条目」（§3 末尾语义块 = 单一真相源）。
- BDD-11 判据 3 + BDD-4 判据 3 交叉锁（用例断言 ↔ UPGRADING 一致）。
- §5 跨批共享件已声明「B1 语义由主 Agent 在批 1 返回后定稿传入批 2」，避免双源漂移。
三重锁 + 跨批同步纪律，代价锁定充分。

**2c · 非阻塞 — M2 copytree 源在「指定版本分支」未锁死**
`_cmd_install()` 的 `else` 分支（`agate-install.py:281-286`，`agate-install.py vX.Y.Z`）**不写 `current`
指针**（实测 L285-286 仅 `_install_version` + `print`）。M2 表述「从当前 current 版本协议 `scripts/` 复制」
在该分支下「当前 current 版本」可能不存在 → copytree 源未定义。BDD-4/5/13 均经 `latest` 分支不受影响，
故非阻塞；但 P4 须把指定版本分支的源锁死为「刚装的 `version_dir` 经 `_protocol_root(version_dir)` 探测 →
`<protocol_root>/scripts`」。建议 M2 补一句显式区分两分支的源路径。

### 核查 3 — 断点一 fail-closed 守卫（§4.1，M1）→ **通过**

**3a · 守卫落点**：M1 表述「`_cmd_install()`（L269-288，在 `_ensure_repo` 调用前）」与 §4.1「`_cmd_install()`
首行（`_ensure_repo` 之前）」一致。核对调用链：`_cmd_install`（`:269`）→ `:271` `_ensure_repo` → `:134`
`os.makedirs(agate_home, exist_ok=True)` / `:136-139` `git clone`。守卫作 `_cmd_install` 首行 → 在
makedirs / clone 之前执行，且覆盖 `main()` 两处调用（无参 `:415` / 版本号 `:427`），对应 BDD-1「无参或带版本号」。
`os.path.islink` 判真即 `sys.exit(1)`，此前无任何 `os.makedirs` / `git clone` → **拒绝后不留半成品**
（不建 `repo/` / `vX.Y.Z/`，I-11 / BDD-1 守住）。`_cmd_uninstall` 不新建 `~/.agate` 根 → 不加守卫（P1 §4
扫描 1，正确）。

**3b · 穿透行为复现**：隔离 HOME 实测 `os.makedirs(base, exist_ok=True)` 穿透软链无报错、`repo/` `realpath`
落软链目标内部 → 守卫判据（`os.path.islink(agate_home)` 须在 makedirs / clone 前判）正确。`os.path.islink`
对普通目录 / 不存在路径为 `False` → BDD-3 不误伤（R5 缓解成立）。

**3c · 三步指引 stderr 文案**：§4.1 代码块含 `mv ~/.agate ~/.agate.bak` / `mkdir -p ~/.agate` /
`install.sh --versions` + `python3 ~/.agate/scripts/agate-install.py latest`（带版本标识）三段命令片段，
满足 BDD-2 判据 1/2/3 同粒度 grep。文案与 §4.3 对照表「迁移」行、M6 `install.sh --versions` 分支同源。

### 核查 4 — gate_commands（§6）固化完备性 → **通过**

- `P5_shellcheck_root: "shellcheck -S warning install.sh"`（R9）：**必要**——`P5_shellcheck` 的
  `agate/scripts/*.sh` glob 不含仓库根 `install.sh`（M6 改动对象）；路径对；基线实测 rc=0。独立 key，
  非 `&&` 拼接。
- `P5_timeout_seconds: 600`：`P5` 含端到端多步 install（可能 `git clone` 本地 repo）归**构建类**档，
  对齐 P2 卡片三档基准表（构建类 600s）。合理。
- 无 `&&` 拼接短路反模式：`P5` / `P5_consistency` / `P5_shellcheck` / `P5_shellcheck_root` / `P5_counttests`
  各为独立 key，各自 exit code 可判。符合 P2 卡片「`--strict` 反模式」纪律。
- `P5` = `pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/` → 覆盖新增
  `agate/tests/integration/test_version_lifecycle_e2e.py`（M15）。`P3` = `pytest agate/tests/` 全量覆盖。
- `P5_consistency` 用 `--strict-errors-only`（P2 卡片日常任务默认，非 `--strict`），worktree 自己的脚本
  （AGENTS.md 双工作区纪律）。基线 EXIT=0 / 0 ERROR 实测属实。
- `P5_counttests` 路径校正为 `agate/tests/scripts/count-tests.sh`（实测存在）——校正正确。
- `P3` 不加 `timeout_seconds`（走 `AGATE_TDD_TIMEOUT`，字段规则 1）——正确。
- `ui_affected: false` → 无 `P5_e2e`，端到端折进 `P5` 的 `integration/`——符合卡片。

### 核查 5 — 测试策略（M12-M15）覆盖 14 条 BDD 无缺口 → **基本通过（1 测试缺口 + 1 命名卫生项）**

- **双 fixture 触发元仓库 gap（I-5）**：`_make_home_meta`（建 `vX/agate/scripts/`、不建 `vX/scripts/`）
  与 `_make_home_rootproto`（直建 `vX/scripts/`）是既有 `_make_home`（`test_agate_version_resolve.py` 建
  空 `vX/`；`test_hook_resolve_entry.py` 建 `vX/scripts/`）的自然扩展。meta fixture 强制协议在 `agate/`
  子目录、根无 `scripts/` → **真正触发** TAG0008 逃逸的元仓库形态（非「根即协议」模拟）。BDD-6/7/8 可闭环。
- **端到端 fixture（M15）**：本地构造元仓库形态 git repo（`_tag_meta_upstream` 为既有 `_tag_upstream`
  的可行变体）经 `AGATE_REPO_URL` 注入即默认路径；`git_repo` / `bash` / `py_path` fixture 均在 conftest
  存在。CI 无网 → 真实 GitHub clone 增强 skip + 本地补证 P6-evidence（I-6）。闭环。
- **`os.symlink` 失败 → `pytest.skip`**：既有 `test_bdd_11b`（`except (OSError, NotImplementedError)`）
  / `test_bdd_30` 双先例，平台无关处理到位。
- **测试缺口（非阻塞）**：BDD-5「新机器官方路径」+ M12「`install.sh --versions` 隔离 HOME」用例
  要求 `install.sh --versions` 能被指向本地 fixture repo。§4.2 写 `git clone <DEFAULT_REPO_URL>`、M6 写
  `<url>`，两处不一致，且均未声明读 `AGATE_REPO_URL` 覆盖。BDD-5 无 skip 条款（不同于 BDD-13 / I-6）→
  若 `install.sh --versions` 硬编码 GitHub URL，BDD-5 与 M12 该用例离线不可验。**P4 须落实**：
  `install.sh --versions` 读 `AGATE_REPO_URL`（设置时覆盖默认 URL）。方案层面只是加一行读 env，不动
  架构，故非阻塞。
- **命名卫生（非阻塞）**：M12/M13/M14 称「新增 BDD-1~5 / BDD-6/7 / BDD-8 用例」写入已含
  `test_bdd_1`..`test_bdd_8`（TAG0008 语义）的文件。TAG0032 BDD-N ≠ TAG0008 BDD-N。P4 用例函数名建议
  加区分前缀（如 `test_tag0032_bdd_N_*`），避免收集冲突与语义混淆。

### 核查 6 — 实现就绪度 → **通过**

- §7 `files_to_read` ~25 条带行号范围：覆盖 `agate-install.py`（5 段：`_agate_home` / `_ensure_repo` /
  `_install_version` / `_cmd_install` / `main` arg 解析）、`agate_common.py`（3 段：归口 + 受益方 + rules）、
  `resolve-entry.py` / `agate-resolve.py` / `agate-summary.py`（I-1 核对锚）、`install.sh`、`UPGRADING.md`
  （5 段）、`README×2` / `SETUP.md`、6 个测试文件 + conftest（2 段）。每条有 `why`，无过量，M1-M15 落点
  全部有对应导航。
- 方案清晰度：§1 M1-M15 表（文件:落点 + 改动内容 + BDD）+ §2/§3 给出 `_protocol_root` 完整代码 + 两处
  消费点 + §4.1 完整 stderr 文案 + §4.3 生命周期节结构 + §4.4 fixture 形态。implementer 无需额外步骤计划
  可自主实现。唯一须先澄清点 = 核查 2c 的 M2 指定版本分支源路径。

### 核查 7 — minimal_validation（§9）→ **通过**

- **断点一 `result: confirmed`**：独立在隔离 HOME 重跑最小复现——`islink(base)=True` 且 `isdir(base)=True`
  同时成立；`os.makedirs(base, exist_ok=True)` 对指向已存在目录的软链无报错（穿透确认）；`repo/` `realpath`
  落软链目标内部。与 §9 note 记录一致，可信。`[PROD_NOT_TOUCHED]`（测完 `rm -rf` 隔离 HOME）。
- **A1 探测顺序 `result: not_needed`「纯代码逻辑」声明**：已写清依赖的内部函数与分支——`_resolve_version_info`
  （`:166`）两段分支（`.agate-version` ok `L180-183` / current 链 `L188-190`）+ 新 helper `_protocol_root`
  判定链 + 未改的三分支（env 覆盖 `L173-175` / legacy 软链兜底 `L192-193` / `resolve_hook_root` 脚本上溯
  `L219-228`）+ 消费方 grep 复核清单。符合 P2 卡片「须写明依赖了哪些内部函数/数据转换」。

### 核查 8 — 范围锁定 + 纯增量红线 → **通过**

- §1.2「不改什么」显式覆盖 out-of-scope 四项 + 理由：`install-offline.py:204`（out-of-scope「install-offline
  适配」，转 roadmap 候选，解析侧经共用 `_resolve_pointer_chain` 自然受益）/ Windows 复制模式
  `.agate-root` marker（out-of-scope「Windows 复制模式专项」）/ `.state.yaml` schema（RM-AG0059 独立 epic）
  / agateon 仓库形态重构（影响面远超本任务，作决策 A 不采纳备选）。与 P0-brief out-of-scope 逐项对齐。
- `dispatch_plan: serial 两批`：批 1 `scripts-tests`（M1-M6 + M12-M15）/ 批 2 `docs-consistency`
  （M7-M11 + consistency 回归）。批边界对齐影响面——批 1 不碰任何 `.md` 文档、批 2 不碰脚本/测试，
  「同一文件不跨批」成立。serial 理由自洽（脚本+测试 TDD 深度耦合；文档面依赖批 1 install 行为落地，
  BDD-12 checklist 1 交叉锁）。跨批共享件（B1 语义单源）由主 Agent 定稿传入，纪律明确。

---

## 输出结构（角色四节）

### 架构问题（阻塞级）

无。决策 A1 / B1 的取舍站得住、理由自洽；最高风险面（消费方归口声明）经独立 grep 复核属实；断点一
守卫落点正确且「拒绝不留半成品」成立；minimal_validation 复现可信；范围锁定与纯增量红线核对通过。

### 架构问题（非阻塞，P4 implementer 须落实，不退回 architect）

1. **M2 copytree 源在「指定版本分支」未锁死**（核查 2c）。`_cmd_install()` 的 `else` 分支
   （`agate-install.py:281-286`）不写 `current` 指针，M2「从当前 current 版本协议 `scripts/` 复制」在该
   分支源未定义。**P4 动作**：指定版本分支的副本源锁为「刚装的 `version_dir` 经 `_protocol_root(version_dir)`
   探测得 `<protocol_root>/scripts`」；建议 M2 补一句显式区分 latest / 指定版本两分支的源路径。
   BDD-4/5/13 经 latest 分支不受影响，故非阻塞。

2. **`install.sh --versions` 须读 `AGATE_REPO_URL`**（核查 5 测试缺口）。§4.2（`<DEFAULT_REPO_URL>`）
   与 M6（`<url>`）表述不一致且均未声明 env 覆盖。**P4 动作**：`install.sh --versions` 分支
   `git clone "${AGATE_REPO_URL:-<default>}" ~/.agate/repo`，使隔离 HOME / 离线可注入本地 fixture repo。
   否则 BDD-5（无 skip 条款）与 M12「`install.sh --versions` 隔离 HOME」用例离线不可验。

3. **M5「version 推导顺序」措辞精确化**（核查 1b）。实质不变式 = 「`version` 恒取 `os.path.basename(cur)`
   ——从 `cur` 取，不从 `_protocol_root(cur)` 返回值取」，非语句先后。P4 按此实现，P7 一致性核对按此口径。

### 测试缺口

- **BDD-5 离线可验性**（同非阻塞项 2）：依赖 `install.sh --versions` 支持 `AGATE_REPO_URL` 注入。P4 落实
  env 覆盖后，M12 须含「隔离 HOME + `AGATE_REPO_URL` 指向本地 meta-repo 形态 fixture → `install.sh --versions`
  → 产出 `repo/` + `vX.Y.Z/` + 指针 + 根 `scripts/` + 源树无污染」用例（BDD-5 判据）。
- **用例函数名冲突域**（同命名卫生项）：M12/M13/M14 新增用例写入含既有 `test_bdd_N`（TAG0008 语义）的
  文件，P4 须用区分前缀（如 `test_tag0032_bdd_N_*` 或 `test_meta_repo_*` / `test_rootproto_*`），
  防 pytest 收集冲突与 BDD 编号语义混淆。
- 其余 13 条 BDD（BDD-1/2/3/4/6/7/8/9/10/11/12/13/14）经 M1-M15 + §10「实现完成标志」逐条有落点，
  双 fixture（meta / rootproto）常驻 `agate/tests/unit/` 为 DEBT0016 回归锁（BDD-9），端到端 fixture
  强制元仓库形态（I-5）、CI 无网 skip + 本地补证（I-6），无缺口。

### 锁定决策（本次评审确认的技术方向）

- **决策 A = A1（resolve 侧增量探测 `_protocol_root`）**：`agate_common.py` 新增 helper（探测序
  `vdir/scripts` 先、`vdir/agate/scripts` 后，皆无则返回 `vdir` 原样交下游 fail-closed）；`_resolve_version_info`
  两处消费点（`.agate-version` ok 分支 `root=_protocol_root(vdir)` / current 链分支 `version=basename(cur)`
  在先、`root=_protocol_root(cur)` 在后）；`resolve-entry.py` / `agate-resolve.py` / `agate-summary.py` /
  `check-structure-consistency.py` / `check-yaml-schema.py` / `agate-dispatch.py` / `agate-inject-card.py`
  均为受益方、零改动。env 覆盖 / legacy 软链兜底 / 脚本上溯兜底三分支不改。
- **决策 B = B1（副本 `shutil.copytree(src, ~/.agate/scripts, dirs_exist_ok=True)`）**：跨平台单口径；
  `repo/` / 版本目录被删不断入口；与 resolve-entry 固定入口机制正交。维护语义（升级期须重跑
  `agate-install.py latest` 刷新副本）写入 UPGRADING 生命周期节（M7），BDD-4 判据 2/3 + BDD-11 判据 3 交叉锁。
- **断点一**：`os.path.islink(agate_home)` 守卫作 `_cmd_install()` 首行（`_ensure_repo` 的 makedirs /
  clone 之前），True → 三步迁移指引 stderr + `sys.exit(1)`，不建任何目录。
- **gate_commands（§6，P2 固化，P4-P6 不得改）**：`P3` / `P5` / `P5_consistency` / `P5_shellcheck` /
  `P5_shellcheck_root`（新增，覆盖 `install.sh`）/ `P5_counttests`（路径校正 `agate/tests/scripts/count-tests.sh`）
  / `P5_timeout_seconds: 600`。
- **dispatch_plan = serial 两批**：批 1 `scripts-tests`（high，M1-M6 + M12-M15，P3-P5 闭环）→ 批 2
  `docs-consistency`（medium，M7-M11 + consistency 回归）。同一文件不跨批。

### 技术债

本次评审不新增 DEBT 条目。`install-offline.py:204` 同源穿透模式已由 P2-design §1.2 记录为 roadmap 候选
（「断点一 helper 可复用」），属既有登记，不重复。

---

## 结论

**status: approved**（agent: plan-eng-review）

阻塞级架构问题 **0**。非阻塞澄清项 **3**（M2 指定版本分支源路径 / `install.sh --versions` 读
`AGATE_REPO_URL` / M5 措辞精确化）+ 测试缺口 **2**（BDD-5 离线可验性 / 用例函数名冲突域），均可由 P4
implementer 在实现时落实，不需退回 architect 重做方案。

8 项重点核查项逐条通过：A1 探测顺序与 fail-closed 下游（§2 / M3 / `resolve-entry.py:49-52` / I-11）✓｜
`version` 不回归（`agate_common.py:190` / M4 / M5 / BDD-6/7）✓｜消费方归口声明独立 grep 复核属实
（`_resolve_version_info` 唯一核心 + `check-structure-consistency.py:107-113` / `check-yaml-schema.py:139-145`
均 `resolve_agate_root`，无 dirname 旁路）✓｜A2 被否理由（R10 worktree + out-of-scope 外溢）成立 ✓｜
B1 vs B2（悬空断链 = I-3 症状）✓ + 代价三重锁 ✓｜断点一守卫落点（`_cmd_install()` 首行 / makedirs 前 /
不留半成品）✓ + 三步文案同粒度 grep ✓｜gate_commands 七项完备、无 `&&` 短路、`P5_shellcheck_root` 必要且
基线 rc=0 ✓｜双 fixture 触发元仓库 gap（I-5）✓ + 端到端 CI 无网 fallback（I-6）✓｜files_to_read 覆盖
充分无过量 ✓｜minimal_validation 断点一 confirmed 独立复现可信 + A1 纯代码逻辑声明写清依赖 ✓｜范围锁定
覆盖 out-of-scope 四项 + dispatch_plan 批边界对齐影响面、同一文件不跨批 ✓。
