---
phase: P1
task_id: TAG0032
type: problems
parent: P0-brief.md
trace_id: TAG0032-P1-20260907
status: draft
created: 2026-09-07
agent: analyst
risk_level: high
ceremony: standard
phases: [P1, P2, P3, P4, P5, P6, P7, P8]
packages: [agate-scripts, agate-docs, agate-tests]
domains: [backend, cli]
implicit_coupling: true
capability_requirements: []
---

# P1-requirements — TAG0032 版本管理生命周期可用性批（RM-AG0058 整合 epic）

[NO_NEED_CONFIRM]
[PROD_NOT_TOUCHED]

## 1. 需求复述

修复 TAG0008 v1 版本管理「全新机器 → 版本布局 → 项目钉版 → 更新」全链路的三个断点，使之真实
可用。TAG0008 的解析内核（四层解析、指针链、asdf 模式 `.agate-version`）完整，断裂的是生命周期
外壳。范围严格锁定 P0-brief `scope` 的三段：

- **断点一 · 入口断链**：
  - legacy 软链布局下按官方指引（README / UPGRADING）跑 `agate-install.py` →
    `_ensure_repo()` 的 `os.makedirs(agate_home, exist_ok=True)`（`agate-install.py:134`）
    穿透软链（软链目标已存在 → 不报错），随后 `git clone <url> ~/.agate/repo` 落入软链目标
    内部，把 `repo/` 主克隆与 `vX.Y.Z/` worktree **静默建进源仓库 `agate/` 目录**
    （2026-09-07 隔离 HOME 实测：repo 实体落 `src/agate/repo`，无任何提示）。
  - 先删软链再装（正确姿势）→ `~/.agate/scripts/` 不存在（`agate-install.py` 全程不建根
    `scripts/`，版本工具只在 `repo/agate/scripts/`）→ README「快速上手」列出的
    `python3 ~/.agate/scripts/agate-install.py` 直接 No such file。
  - **两条进入版本布局的路径均死路。**
  - 修复行为（P1 只定验收行为，实现方案 P2-design）：install 检测 `agate_home` 为软链时
    **fail-closed 拒绝**（exit 非 0）并输出可操作迁移指引（备份软链 → 建目录根 → 装版本）；
    install 完成后建立根 `~/.agate/scripts/`（副本 vs 软链到 `repo/agate/scripts/` 的维护
    语义差异留 P2-design 决策，P1 只声明「装完 README 入口命令须存在且可执行」）；`install.sh`
    补 `--versions` 模式或等价文档指引，让新机器有官方路径从零进版本布局。

- **断点二 · 元仓库 gap（RM-AG0058 本体）**：GitHub 装出的 `vX.Y.Z` = agateon 整仓（协议在
  `agate/` 子目录）。resolve 命中版本目录后返回 `vdir`（仓库根），hook 消费方
  （`resolve-entry.py:49` = `os.path.join(root, "scripts", gate_py)`）找
  `vdir/scripts/pre-commit-gate.py` 不存在（实际在 `vdir/agate/scripts/`）→ 项目钉
  `.agate-version` 后 commit 被 fail-closed 阻断（2026-09-03 实机验证复现）。根因：TAG0008
  测试用「根即协议」模拟 repo（`_make_home` 直接建 `vX.Y.Z/scripts/`），从未覆盖元仓库形态。
  - 修复行为（方向二选一，P2-design 决策）：resolve 命中版本目录后按探测顺序
    `vdir/scripts` 先、`vdir/agate/scripts` 后，命中后者则返回 `vdir/agate`；**或** install
    在 worktree 检出后把 `agate/` 内容提升为版本根。**行为纯增量**：「根即协议」部署方
    （版本目录直接含 `scripts/`）必须继续可用，解析语义不破坏。

- **断点三 · update 统一入口**：legacy 升级 = 手动 `git pull`（无文档指引），版本布局升级 =
  `agate-install latest`（入口又是断链），hook 是否随版本重装散落在 `UPGRADING.md` 各版本节。
  - 修复行为：文档面对齐两种布局的生命周期指令（legacy = `git pull`、版本布局 =
    `agate-install latest` 幂等）；`agate/UPGRADING.md` 增补「版本管理生命周期」节
    （安装 / 迁移 / 更新 / 回退一张图）；hook 重装时机写明（薄壳固定 + resolve-entry 机制下
    通常无需随版本重装）。

## 2. 隐含需求识别

| # | 隐含需求 | 为什么必须 |
|---|---------|-----------|
| I-1 | **resolve 返回值语义变更须保「version 号不回归」** | `_resolve_version_info` 返回 dict 的 `version` 字段与 `root` 独立。指针链分支现在 `version = os.path.basename(cur)`；若把 `root` 改为 `vdir/agate` 而不修正 `version` 推导，`agate-summary` / `agate-resolve` 的 `AGATE_VERSION` 会从 `vX.Y.Z` 变成 `agate`。P1 须锁「`AGATE_VERSION` 输出仍为 `vX.Y.Z`」。 |
| I-2 | **legacy 软链拒绝是行为变更，须给迁移指引** | 现网 legacy 软链用户（含本机 `~/.agate` → 主 checkout `agate/`）按现有文档升级会撞新拒绝。拒绝信息不含可操作迁移路径 = 自断现网用户升级路。P1 须锁「拒绝 + 三步指引文案」。 |
| I-3 | **根 `scripts/` 建立方式（副本 vs 软链）的维护语义差异须落 UPGRADING** | 副本随 install 刷新（升级需重跑 install）、软链跟随 repo 更新（repo 删则断）。P1 只声明验收行为（装完入口命令可执行），取舍属 P2-design，但 P1 须要求「所选语义有单测锁定 + 写入 UPGRADING」。**对应 BDD**：BDD-4 判据 2/3（单测锁定 + 与 UPGRADING 一致）+ BDD-11 判据 3（写入生命周期节）。 |
| I-4 | **文档面 update 指引现状互相矛盾，须收敛而非只新增一节** | `UPGRADING.md` v0.50.0 节 §① 布局变化表格（约 L549-L553，行号随编辑漂移，以 `### v0.50.0` §① 表格为准）已声称「`~/.agate/` 版本管理根目录 … + `scripts/`（版本管理工具）」——文档已承诺根 `scripts/` 存在但 install 从未实现（doc/reality mismatch）。仅新增「生命周期」节而不修订既有互斥表述 → 读者仍会踩坑。**对应 BDD**：BDD-12 checklist 4 条逐条二值断言。 |
| I-5 | **端到端必须用真实元仓库形态，不能用「根即协议」模拟 repo** | TAG0008 教训：`_tag_upstream` 用元仓库形态源但只断言 worktree/指针；`_make_home` 用「根即协议」fixture 跑 resolve/gate。install 与 resolve/gate 从未串成一条链，gap 因此逃逸。新增端到端 BDD 须真实 clone 形态（或本地构造的元仓库形态 git repo 经 `AGATE_REPO_URL` 注入）。 |
| I-6 | **CI 无网时端到端 BDD 的降级路径** | 真实 GitHub clone 依赖网络。CI 无网 → 该 BDD 标 skip + 本地隔离 HOME 验收记录补证进 P6-evidence（这是环境降级，不是能力缺失，见 §5 verification_env）。 |
| I-7 | **离线包 / Windows 复制模式解析侧自然受益，打包侧不动** | `install-offline.py` / 复制模式经同一 `_resolve_pointer_chain` → resolve 核心的增量探测自然覆盖其解析侧；`agate-pack-offline.py` 打包形态属 out-of-scope，本任务不改。P1 须声明「不波及离线包接口；若波及则最小兼容」。 |
| I-8 | **SELF-GATE 触发** | 改 `agate/scripts/*`（agate-install.py / agate_common.py / resolve-entry.py）+ 文档面（README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md / install.sh）→ 触发 SELF-GATE；commit message 须含 `self-gate-review:` 或 `self-gate-skip:`。P1 不含 self-gate 流程本身，但预期触发文件清单见 §6 以利 P8。 |
| I-9 | 数据面 | 无数据库、无迁移数据。`.agate-version` 声明格式不变（仍 `agate: vX.Y.Z`）。既有钉版项目在修复后应「从阻断转为可用」，无需改声明。 |
| I-10 | 多端 | 无 MCP / API 面。CLI 面 = `agate-install.py` / `agate-resolve.py` / `resolve-entry.py` / `install.sh`，均在范围内。 |
| I-11 | 边界/回滚 | install 拒绝后不得留半成品（不建 `repo/`、不建 `vX.Y.Z/`）；resolve 探测两形态均不存在时维持现有 fail-closed（`root=None` → 调用方 exit 非 0），不新增静默放行。 |
| I-12 | 兼容 | Linux 全量 pytest 全绿是回归底线；新增用例平台无关（`tmp_path`、探测 `python3\|python`、不假设 POSIX symlink 语义、不用 `/tmp` 字面量）。 |

## 3. BDD 验收条件

> 全局连续编号 `#### BDD-NN:`，每条一条 Given/When/Then，可二值判定（PASS/FAIL）。
> 三断点各成分组 + 端到端分组。所有安装路径验收在隔离 HOME（`HOME=$(mktemp -d)` 级别）执行，
> 绝不触碰真实 `~/.agate`。

### 3.1 断点一：入口断链修复（install 软链 fail-closed + 根 scripts + 新机入口）

#### BDD-1: legacy 软链布局下 install 被 fail-closed 拒绝
- Given 隔离 HOME 下 `~/.agate` 是指向某目录的软链（legacy 布局），软链目标是一个 git 工作树
- When 运行 `python3 <worktree>/agate/scripts/agate-install.py`（无参）或带版本号
- Then 命令 exit 非 0；软链目标内部不出现新建的 `repo/` 目录，也不出现任何 `vX.Y.Z/` 目录（穿透污染被阻断）

#### BDD-2: 拒绝信息含可操作三步迁移指引
- Given BDD-1 触发的拒绝
- When 读该命令的 stderr 输出
- Then 输出同时包含以下三段可 grep 的命令片段级迁移指引，三者缺一即 FAIL（每项判据同粒度，均为命令片段匹配，不留「什么算定位到」的裁量）：
  1. **备份软链**：命令片段匹配 `mv ~/.agate ~/.agate.bak`（或 `mv ~/.agate ` + `.bak` / `.old` 等备份后缀目标）
  2. **建目录根**：命令片段匹配 `mkdir -p ~/.agate`（或 `mkdir ` + `~/.agate`，语义为把 `~/.agate` 重建为普通目录而非软链）
  3. **装版本**：命令片段匹配 `agate-install.py` 且带版本标识（`latest` / `v<X.Y.Z>` / `--versions` 三者其一），形如 `python3 ~/.agate/scripts/agate-install.py latest` 或 `install.sh --versions`

#### BDD-3: 非软链（普通目录 / 全新）布局 install 不被新拒绝逻辑误伤
- Given 隔离 HOME 下 `~/.agate` 不存在，或为普通（非软链）目录
- When 运行 `agate-install.py v<X.Y.Z>`（`AGATE_REPO_URL` 指向本地构造的版本源 repo）
- Then 命令 exit 0，版本目录 `~/.agate/v<X.Y.Z>/` 建立成功

#### BDD-4: install 完成后根 `~/.agate/scripts/` 就位且入口命令可执行
- Given 隔离 HOME 下全新执行 `agate-install.py`（装 latest，`AGATE_REPO_URL` 注入本地版本源）成功
- When 检查 `~/.agate/scripts/agate-install.py` 并以 `python3 ~/.agate/scripts/agate-install.py --help` 调用；再在 `agate/tests/` 内检索针对根 `scripts/` 建立方式维护语义的用例
- Then 三项判据全 PASS，缺一即 FAIL：
  1. `~/.agate/scripts/agate-install.py` 路径存在且 `--help` 调用 exit 0（README「快速上手」列出的 `~/.agate/scripts/*` 入口命令不再 No such file）
  2. `agate/tests/` 内存在至少一条用例，断言 P2-design 所选建立方式（副本 vs 软链）在「升级 / 重跑 install latest」后根 `~/.agate/scripts/` 的入口仍解析到当前版本的版本管理工具（副本方式 → 断言副本随 install 刷新；软链方式 → 断言软链跟随新版本目录），即 I-3 的「所选维护语义有单测锁定」
  3. 该用例断言的维护语义与 UPGRADING「版本管理生命周期」节所写一致（与 BDD-11 交叉锁）

#### BDD-5: 新机器有从零进入版本布局的官方路径
- Given 一台无 `~/.agate` 的机器，只按 README + `install.sh` 的文档操作
- When 按文档走完「进入版本布局」步骤（`install.sh --versions` 模式或文档明确指定的等价命令序列）
- Then 得到版本管理根布局（`repo/` + `vX.Y.Z/` + `current`/`latest` 指针 + 根 `scripts/`），且执行过程不在任何源仓库树内新建 `repo/` 或 `vX.Y.Z/`

### 3.2 断点二：元仓库 gap 修复（RM-AG0058 本体）

#### BDD-6: resolve 对元仓库形态版本目录返回协议子目录
- Given 隔离 HOME 下装有元仓库形态版本目录 `~/.agate/v<X.Y.Z>/`（协议在其 `agate/` 子目录：`agate/scripts/` 存在、`v<X.Y.Z>/scripts/` 不存在），某项目根 `.agate-version` 内容 `agate: v<X.Y.Z>`
- When 在该项目目录内运行 `python3 ~/.agate/scripts/agate-resolve.py`
- Then 输出 `AGATE_ROOT` 指向 `~/.agate/v<X.Y.Z>/agate`，且 `AGATE_VERSION` 仍为 `v<X.Y.Z>`（版本号不回归）

#### BDD-7: 「根即协议」部署方解析语义不变（纯增量红线）
- Given 隔离 HOME 下装有「根即协议」形态版本目录 `~/.agate/v<X.Y.Z>/`（`v<X.Y.Z>/scripts/` 直接存在）
- When 运行 `agate-resolve.py`（项目钉该版本）
- Then 输出 `AGATE_ROOT` 仍为 `~/.agate/v<X.Y.Z>`（探测顺序 `vdir/scripts` 先命中，不进入 `vdir/agate` 分支），且 `AGATE_VERSION` 仍为 `v<X.Y.Z>`（与 BDD-6 对称，版本号不回归）

#### BDD-8: 钉版后 hook gate 路径存在，commit 不再被阻断
- Given 元仓库形态版本已装 + 项目 `.agate-version` 钉该版本 + hook 经 `resolve-entry.py` 解析
- When 运行 `python3 ~/.agate/scripts/resolve-entry.py pre-commit`（在钉版项目目录内）
- Then 解析出的 gate 路径 `<解析根>/scripts/pre-commit-gate.py` 存在并被 exec；不因「gate 脚本不存在」exit 1

#### BDD-9: 两形态下现有全量 pytest 均全绿（无旁路漏改）
- Given 修复后代码
- When 在 worktree 内跑 `python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -n auto`（含新增的元仓库形态用例与「根即协议」形态用例）
- Then 全部用例 PASS（无直接拼 `vdir/scripts` 的解析旁路被漏改；DEBT0016 dirname 散点教训回归锁）

### 3.3 断点三：update 统一入口（文档面）

#### BDD-10: 两种布局的更新指令在文档面对齐且各自幂等
- Given `agate/UPGRADING.md` 的「版本管理生命周期」节
- When 查找 legacy 布局与版本布局各自的「更新」指令
- Then legacy 明确为 `git pull`（含「是否需要重跑 install-hook.py」的判定口径），版本布局明确为 `agate-install latest` 并声明幂等（重复执行不报错、不重复建版本目录）

#### BDD-11: UPGRADING 新增「版本管理生命周期」节覆盖安装/迁移/更新/回退
- Given `agate/UPGRADING.md`
- When 检索该节
- Then 以下均满足，缺一即 FAIL：
  1. 该节存在且四个动作均有对应命令或步骤：安装、迁移（legacy → 版本布局）、更新、回退
  2. 写明 hook 重装时机（薄壳固定 + resolve-entry 机制下通常无需随版本重装）
  3. 该节含一条「根 `~/.agate/scripts/` 建立方式的维护语义」条目：随 P2-design 选定副本或软链后填实，明确升级期是否需重跑 `agate-install`、以及 repo 被删 / 版本目录切换对该入口的影响（即 I-3 的「所选维护语义写入 UPGRADING 生命周期节」，与 BDD-4 判据 2/3 交叉锁）

#### BDD-12: 文档面 update / 升级指引的具体矛盾表述逐条收敛
- Given §4 扫描 4 已列出的 4 条具体矛盾表述（doc/reality mismatch 或版本节口径分歧），以及 README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md 中所有「更新 / 升级 agate 本体」及「`~/.agate` 根含 `scripts/`」的表述
- When 逐条走下列 checklist，并附加跑 `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
- Then 下列 checklist 每条命中「已收敛到新口径」或「已标注为版本历史叙事保留」二者之一（无第三态），任一条两者皆不满足即 FAIL：
  1. **`UPGRADING.md` v0.50.0 节 §① 布局变化表格「`~/.agate/` = 版本管理根目录：… + `scripts/`（版本管理工具）」行**（行号随编辑漂移，以 `### v0.50.0` 节 §① 表格为准，约 L549-L553 之「迁移后」列布局行）—— doc/reality mismatch（I-4）。**二值断言**：install 落地建根 `~/.agate/scripts/` 后，隔离 HOME 装完实测该目录存在（与 BDD-4 判据 1 同源）→「已收敛到新口径」；若表格仍承诺根含 `scripts/` 而 install 后该目录不存在 → FAIL。
  2. **同表「升级 = `python3 ~/.agate/scripts/agate-install.py`」行**（约 L552）—— 升级入口表述。**二值断言**：新增「版本管理生命周期」节声明版本布局升级 = `agate-install latest`（幂等，BDD-10），且该 v0.50.0 表格行要么原地更新为一致口径、要么该版本节内新增一行指针指向生命周期节 →「已收敛到新口径」或「已标注为版本历史叙事保留（v0.50.0 发布记录，加指针不改叙事）」；若表格行与生命周期节口径冲突且无指针 → FAIL。
  3. **`UPGRADING.md` v0.60.0 / v0.61.0 / v0.62.0 节「通用升级动作：`git pull` + 重跑 `install-hook.py`」** 与 **v0.66.0 / v0.67.x / v0.68.0 节「无需重跑 `install-hook.py`（软链布局 `git pull` 即生效）」** 的 hook 重装口径分歧。**二值断言**：新增「版本管理生命周期」节统一写明「resolve-entry 固定解析入口机制下，软链布局切版本 / 升级通常无需重跑 `install-hook.py`；仅 hook 薄壳（`.sh`）本身变更或 Windows 复制模式才重跑」，且 v0.60-0.62 三个历史版本节保留原叙事、不逐条改写（属「已标注为版本历史叙事保留」：那是各自版本发布时的动作记录）→ PASS；若生命周期节未给统一判定口径，或历史版本节被逐条改写（违反「不改版本历史叙事」约束）→ FAIL。
  4. **README.md:40-42 / README.zh-CN.md:40-42「升级 agate」表述 + `agate/SETUP.md` 升级节（约 L244）**。**二值断言**：三处升级表述与生命周期节口径一致（legacy = `git pull`；版本布局 = `agate-install latest`）→「已收敛到新口径」；若任一处仍单独描述与新口径冲突的旧步骤且无指向生命周期节的指针 → FAIL。
- **附加回归项**（非主判据，仅防新增 ERROR）：`check-protocol-consistency.py --strict-errors-only` 仍 EXIT=0 且 0 ERROR（基线即 0 ERROR，本项只保证本任务不引入新 ERROR，不作为「矛盾是否收敛」的判据）。

### 3.4 端到端（真实元仓库形态 + 隔离 HOME）

#### BDD-13: 「全新机器 → 版本布局 → 钉版 → 更新」全链路可用
- Given 隔离 HOME（`HOME=$(mktemp -d)`）+ 真实 GitHub 元仓库形态（CI 无网时用本地构造的元仓库形态 git repo，含 `agate/` 子目录 + `vX.Y.Z` tag，经 `AGATE_REPO_URL` 注入）
- When 依次执行：进入版本布局（官方路径）→ `agate-install.py`（装版本）→ 项目写 `.agate-version` 钉版 → `resolve-entry.py pre-commit` → 再次 `agate-install.py latest`（验幂等）
- Then 逐步 exit 均符合下列期望，且最终 gate 脚本路径存在且可执行，缺一即 FAIL：
  1. 进入版本布局（官方路径）→ exit 0
  2. `agate-install.py`（装版本）→ exit 0
  3. 项目写 `.agate-version` 钉版 → exit 0（文件写入）
  4. `resolve-entry.py pre-commit` → exit 0（gate 路径存在并被 exec，不因「gate 脚本不存在」exit 1）
  5. 再次 `agate-install.py latest`（幂等复跑）→ exit 0，且不重复建版本目录（`~/.agate/vX.Y.Z/` 数量不变、指针幂等切换）、不在任何源仓库树内新建 `repo/` / `vX.Y.Z/`
  - CI 无网环境该用例标 skip + 本地隔离 HOME 验收记录补证进 P6-evidence

#### BDD-14: 端到端全链路不污染源仓库（TAG0008 教训回归锁）
- Given 同 BDD-13 的隔离 HOME 全链路执行完毕
- When 检查 worktree 源仓库树（`git status --porcelain` + 目录扫描）
- Then 源仓库内无新增 `repo/` 主克隆、无 `vX.Y.Z/` worktree、`git status --porcelain` 无非预期未跟踪条目

## 4. 同类扫描（强制节）

扫描以 worktree（`/home/kity/oclab/agateon/.worktrees/agate-TAG0032`，含其 `agate/` 子目录）为准。

### 扫描 1 — `makedirs` / `exist_ok` 在安装路径相关脚本（软链穿透风险面）

命中 9 处（`grep -rn "makedirs\|exist_ok" agate/scripts/*.py`，排除 test）：

| 文件:行 | 判定 | 理由 |
|---------|------|------|
| `agate/scripts/agate-install.py:134`（`_ensure_repo`：`os.makedirs(agate_home, exist_ok=True)`） | **本次处理** | 软链穿透源本体。`agate_home = ~/.agate`，软链存在时 `exist_ok=True` 不报错 → 后续 `git clone` 落入软链目标。断点一修复点，BDD-1/2 锁定。 |
| `agate/scripts/install-offline.py:204`（`_copy_tree` → `shutil.copytree(..., dirs_exist_ok=True)`，`_DEFAULT_DEST = ~/.agate`） | **本次不处理** | 同类穿透风险（`version_dir = dest/version`，dest 默认 `~/.agate`，软链时 leaf 落软链目标）。属 out-of-scope「install-offline 离线链路适配」。→ 进 roadmap 候选：`agate-install.py` 软链检测落地后，以同一 helper 复用到 `install-offline.py`（若断点一改动波及其接口则最小兼容，见 I-7）。 |
| `agate/scripts/install-hook.py:109`（`os.makedirs(hook_dir, exist_ok=True)`，`hook_dir = <repo>/.git/hooks`） | 不处理（非同类） | 目标是项目 `.git/hooks/`，不是 `~/.agate` 根，不涉及软链穿透污染源仓库。 |
| `agate/scripts/agate-archive-stale-outputs.py:42` / `agate-capture-env-baseline.py:90` / `agate-migrate-workspace.py:123` / `agate-pack-offline.py:74,91,94` | 不处理（非同类） | 均在项目工作区 / 打包临时目录内建子目录，不触及 `~/.agate` 根、无软链穿透语义。 |

**结论**：软链穿透污染源仓库的风险，安装路径上只有 `agate-install.py:134` 一处需本次修；`install-offline.py:204` 是同源模式的同类实例但在 out-of-scope 边界内，转 roadmap 候选并声明「断点一 helper 可复用」。

### 扫描 2 — resolve 语义消费方（返回值改为 `vdir/agate` 的影响面）

归口：`_resolve_version_info`（`agate_common.py:166`）是唯一版本解析核心，对外三个入口
`resolve_version_root` / `resolve_hook_root` / `resolve_agate_root`（+ `resolve_rules_root` 二次封装）。

消费 `root` 后拼子目录的点（`grep -rn '"scripts"\|"rules"\|"assets"\|"phase-cards"'` 交叉 resolve 调用方）：

| 消费点 | 拼接 | 判定 |
|--------|------|------|
| `resolve-entry.py:49` | `os.path.join(root, "scripts", gate_py)` | **本次处理（受益方）** — 断点二命中点。resolve 返回 `vdir/agate` 后自然命中 `vdir/agate/scripts/`。BDD-8。 |
| `agate_common.py:677`（`resolve_rules_root`） | `os.path.join(root, "rules")` | **本次处理（受益方）** — 元仓库 `rules/` 在 `vdir/agate/rules/`，返回 `vdir/agate` 后命中。 |
| `agate_common.py:221`（`resolve_hook_root` 脚本上溯兜底分支） | `os.path.join(agate_root, "scripts")` | 本次核对：仅 `info["root"] is None` 时进入（既有兜底），不受返回值语义影响；保持不动。 |
| `agate-summary.py:150` | 仅显示 `info["root"]` / `info["version"]` | **本次处理（关联）** — 须保 `AGATE_VERSION` 仍为 `vX.Y.Z`（I-1），BDD-6。 |
| `agate-resolve.py:40` | 输出 `AGATE_ROOT` / `AGATE_VERSION` | **本次处理（关联）** — 同 I-1，BDD-6。 |
| `agate-dispatch.py:78,199` / `agate-inject-card.py:53` / `agate-render-dispatch-prompt.py:118,128` / `agate-next-card.py:166` | `os.path.join(agate_root, "scripts"/"assets"/"phase-cards"/"rules", ...)` | 本次不处理（编排/派发类，按项目约定走 `~/.agate` 稳定版解析，不经版本链；返回 `vdir/agate` 后子目录拼接仍自然命中，无破坏）。列出备 P8 一致性核对。 |
| `check-gate.py:715,808`（经 `resolve_rules_root`） | `rules/` | 受益方，随 `resolve_rules_root` 一并覆盖。 |
| `check-structure-consistency.py:113` / `check-yaml-schema.py:145`（`resolve_agate_root` + 校验 `root/rules` 存在） | `os.path.join(root, "rules")` | 本次核对：返回 `vdir/agate` 后 `rules/` 校验命中；FATAL「缺 rules/ 目录」不再误触。 |

**无直接拼 `vdir/scripts` 的解析旁路**（DEBT0016 dirname 推导散点教训）：确认所有 gate 路径拼接
都先经 `_resolve_version_info` 归口，无脚本内 `os.path.dirname(vdir) + "/scripts"` 之类的旁路推导。

**回归拦截**：新增「元仓库形态 resolve 用例」+「根即协议形态 resolve 用例」双 fixture 常驻
`agate/tests/unit/`（BDD-6/7/9），锁定探测顺序与两形态并存。

### 扫描 3 — 版本布局解析链探测点（`.agate-version` / `.agate-root` / `AGATE_ROOT`）

| 符号 | 命中 | 判定 |
|------|------|------|
| `.agate-version` 读取 | `agate_common.py:99`（`_find_project_declaration`，唯一归口）+ `agate-install.py:249,251`（卸载引用扫描，只读不解析） | 归口单点；元仓库适配在归口下游（`vdir` → `vdir/agate` 探测），不改 `.agate-version` 格式/查找语义。 |
| `.agate-root` marker | producer：`install-hook.py:125`（hook_dir）、`install-offline.py:232`（dest）；consumer：`agate_common.py:222`（`resolve_hook_root` 兜底）、pre-commit 复制模式恢复 | 复制模式 / Windows 恢复路径。属 out-of-scope「Windows 复制模式专项」；但经同一 `_resolve_pointer_chain`，resolve 核心增量探测自然覆盖其解析侧，**本次不额外改**，P2 影响面梳理复核。 |
| `.installed-version` | 仅 `install-offline.py:226` 写、`:11` 验证 | 离线包内部校验，不参与在线 resolve；out-of-scope，不动。 |
| `AGATE_ROOT` env 覆盖 | 各 `resolve_*` 首条分支（env 优先返回原值） | 既有最高优先级契约，不动；元仓库探测只在「无 env 覆盖」时生效。 |

**结论**：元仓库形态适配集中在 `_resolve_version_info` 命中版本目录后的一段增量探测，不波及
离线包解析格式、不改 Windows 复制模式语义、不改 env 覆盖契约。离线 / 复制模式解析侧因共用
`_resolve_pointer_chain` 而自然受益（I-7）。

### 扫描 4 — 文档面 update / 升级指引散落位置

| 表述 | 命中位置 | 收敛判定 |
|------|---------|---------|
| `git pull` 作为升级动作 | `agate/UPGRADING.md` §1 通用步骤（L16/24）+ 各版本节约 40 处「`git pull` 即完成」+ `agate/SETUP.md:244` 升级节 + `install.sh:20` | **本次处理**：§1 通用步骤 + 新增「版本管理生命周期」节明确 legacy=`git pull`；各历史版本节的「`git pull` 即完成」是版本历史叙事，不逐条改（BDD-12 只要求无与新口径**冲突**的表述）。 |
| `agate-install.py` 作为升级入口 | README.md:40-42 / README.zh-CN.md:40-42 / `UPGRADING.md` v0.50.0 节 §① 表格「升级 = agate-install.py」行（约 L552，行号随编辑漂移，以 `### v0.50.0` §① 表格为准）/ `SETUP.md:26,54` | **本次处理**：README 快速上手补「进入版本布局」官方路径（断点一）；`UPGRADING.md` 新节声明版本布局升级 = `agate-install latest` 幂等。BDD-12 checklist 2 锁。 |
| `~/.agate/` 根含 `scripts/` 的承诺 | `UPGRADING.md` v0.50.0 节 §① 布局变化表格「迁移后」列布局行（约 L551，行号随编辑漂移，以 `### v0.50.0` §① 表格为准；review 锚点写作 L546 为同一表格的近似行号） | **本次处理（doc/reality mismatch，I-4）**：install 落地建根 `scripts/` 后该表述成真；BDD-4 判据 1 + BDD-12 checklist 1 双锁。 |
| 「重装 hook」时机 | `UPGRADING.md` v0.60.0（约 L377-379）/ v0.61.0（约 L315）/ v0.62.0（约 L280）节「通用升级动作」要求 `git pull` + 重跑 `install-hook.py`；v0.66.0（约 L171-172）/ v0.67.x（约 L117-118、L138-139、L155-156）/ v0.68.0（约 L95-96）节声明「无需重跑 `install-hook.py`（软链布局 `git pull` 即生效）」；`SETUP.md:138,206,248` | **本次处理**：新节统一写明「薄壳固定 + resolve-entry 机制下切版本通常无需重装 hook；仅 hook 薄壳（`.sh`）本身变更或 Windows 复制模式才重跑」。历史版本节保留原叙事不逐条改。BDD-12 checklist 3 锁。 |

**回归拦截**：`check-protocol-consistency.py --strict-errors-only` 纳入 P5/P8（既有）；文档面
一致性由 BDD-12 交叉核对锁定。文档口径未来漂移属人工维护面，新节作为「单一真相源」收敛点。

## 5. 环境与能力声明

### verification_env（端到端 BDD 的运行环境）

```yaml
verification_env: "隔离 HOME（HOME=$(mktemp -d)）+ 真实 GitHub 元仓库形态 clone（agateon 整仓，协议在 agate/ 子目录）；CI 无网 fallback = 本地构造的元仓库形态 git repo（agate/ 子目录 + vX.Y.Z tag）经 AGATE_REPO_URL 注入"
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 P5/P6 dispatch-context 记录当前第几轮 + 历次已排除假设"
```

判别：端到端缺的是「运行环境」（需网络 clone 真实仓库），不是 agent 能力 → 走 `verification_env`，
非 `supplementable`。环境可由主 Agent 用标准操作准备（隔离 HOME + clone / 本地 fixture repo）。
CI 无网 → 该 BDD skip + 本地验收记录补证 P6-evidence（I-6）。

### capability_requirements

`[]` — 本任务无特殊 agent 能力需求：非 frontend（无 vision 需求）、无浏览器 / 外部系统行为依赖；
所需的 bash / python3 / git / 文件系统操作在 worktree 开发环境已具备。

## 6. 裁剪说明

| 阶段 | 走 | 理由 |
|------|----|------|
| P1 | ✅ | 需求基线（本文件）。 |
| P2 | ✅ | 两个断点各有「二选一」实现方向需 design 决策（resolve 探测 vs install 提升；根 scripts 副本 vs 软链）；`risk_level: high` → 需 plan-design-review。 |
| P3 | ✅ | 改脚本走 TDD（AGENTS.md「改脚本的工作流」）：先写失败测试确认红 → 改脚本转绿。不可裁。 |
| P4 | ✅ | 实现 `agate-install.py` / `agate_common.py` / `resolve-entry.py` + 文档面。 |
| P5 | ✅ | 全量 pytest（unit/regression/integration）+ consistency + shellcheck 回归底线。不可裁。 |
| P6 | ✅ | 14 条 BDD 逐条验收，含隔离 HOME 端到端。不可裁。 |
| P7 | ✅ | `implicit_coupling: true`（resolve 返回值语义变更牵动多消费方 + 文档面多文件交叉）→ 一致性检查不可裁。 |
| P8 | ✅ | 触发 SELF-GATE（脚本 + 文档面），发布面变更（`agate/CHANGELOG.md` + `UPGRADING.md` 新节 + 版本号），`internal_only` 不成立。 |

**不裁剪任何阶段。**

### 预期 SELF-GATE 触发文件清单（供 P8）

- 脚本：`agate/scripts/agate-install.py`、`agate/scripts/agate_common.py`、`agate/scripts/resolve-entry.py`（可能 `agate/scripts/agate-resolve.py` 随 `version` 推导修正）
- 文档面：`README.md`、`README.zh-CN.md`、`agate/UPGRADING.md`、`agate/SETUP.md`、`install.sh`
- 测试：`agate/tests/unit/`（新增元仓库形态 install/resolve/端到端用例）
- commit message 须含 `self-gate-review:` 或 `self-gate-skip:`；协议文档变更须 `check-protocol-consistency.py --strict-errors-only` 0 ERROR

## 7. P0-brief 时效性质疑

**已核对 P0-brief 时效性，无漂移。** 立项（RM-AG0058 关联 TAG0032）与任务启动同为 2026-09-07，
无跨会话间隔。逐条对照 P0 卡片严重漂移判据（严重 3 条）：

1. **`task` 目标方案是否仍成立** — 三个断点在当前 worktree 代码中仍可复现：`agate-install.py:134`
   `os.makedirs(agate_home, exist_ok=True)` 无软链检测、全程不建根 `scripts/`；`resolve-entry.py:49`
   `os.path.join(root, "scripts", gate_py)` 对元仓库形态取不到；`UPGRADING.md` 无 update 统一入口节。
   → 目标方案成立，未漂移。
2. **`executor_env` 平台前提是否仍成立** — Linux + worktree（`.worktrees/agate-TAG0032`，分支
   `feat/TAG0032-version-lifecycle`）+ `/usr/bin/python3`（pytest 9.0.3 / pyyaml 6.0.1）齐备，
   基线 consistency 0 ERROR 已验（交接单 §9）。→ 未漂移。
3. **`known_risks` 的「已解决前提」是否实际未解决 / 已被他任务解决** — P0-brief 4 条 known_risks
   全部是前瞻性风险声明（resolve 语义变更须先 grep 消费方 / install 拒绝须给迁移指引 / 根 scripts
   二选一 / 端到端须真实元仓库），无「某前提已解决」类断言。→ 无此类漂移。

无轻微漂移需记录（路径 / 依赖版本 / `env_constraints` 具体值均与 P0-brief 一致）。

## 8. 待确认清单

[NO_NEED_CONFIRM] — 所有实现方向的「二选一」（resolve 探测 vs install 提升 `agate/` 为版本根；
根 `scripts/` 副本 vs 软链）已由 P0-brief 明确划归 P2-design 决策，P1 只定验收行为，无需人拍板
方向。范围严格落在 P0-brief `scope` 三段内，未触碰 `out-of-scope`（pack-offline 适配 / Windows
复制模式专项 / `.state.yaml` schema 扩字段 / agateon 仓库形态重构），无阻塞性待确认项。
