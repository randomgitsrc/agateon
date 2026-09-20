---
task_id: TAG0037
type: problems
parent: P0-brief.md
trace_id: TAG0037-P1-20260919
status: draft
created: '2026-09-19'
risk_level: high
phases:
- P1
- P2
- P3
- P4
- P5
- P6
- P7
- P8
packages:
- agate-scripts
- agate-docs
- agate-tests
- ci-workflows
- install-sh
domains:
- backend
- security
phase: P1
ceremony: full
agent: analyst
---

# P1-requirements — TAG0037 安装与多版本模型统一（RM-AG0066）

[NO_NEED_CONFIRM]
[PROD_NOT_TOUCHED]

> 范围来源：`P0-brief.md`（子批 A–E + 11 条完成判据）+ 主 Agent dispatch-context 中的用户裁决。**范围严格锁定**，未发现需超出 P0-brief 的项（发现的"看似超范围"项已逐条归类并说明为何落在既有子批边界内，或明确列入「本次不处理」）。
> 本文件只定义"要解决什么 / 做完什么样算对"，**不选实现机制**（排除机制 `export-ignore` / 显式清单 / `git archive` 等留给 P2 比对）。
> 每条 BDD 的 Given 均含【隔离】前置：`HOME` / `USERPROFILE` / `AGATE_HOME` 指向 `tmp_path`，**真实 `~/.agate` 不读不写**（可选 canary：测试前后 `~/.agate` 内容哈希不变）。

## 1. 需求复述

**一句话**：为 Agateon 定义「版本目录的唯一结构契约」，让在线 / 离线 / portable 三条安装路径产出**同一结构**（`~/.agate/vX.Y.Z/agate/` 本体），引入 GitHub Release + 本体 portable tarball，同时**彻底删除** legacy 单软链 `~/.agate` 支持（破坏性变更，v0.73.0）。

分子批（与 P0-brief 一致）：

| 子批 | 内容 | 主要 BDD |
|------|------|---------|
| **A** | 版本目录结构契约（含本体精确边界清单，可机械验证）；已装旧形态仍可解析；`_protocol_root` 探测序不动 | BDD-1 ~ BDD-8 |
| **B** | 修复 P0 BUG：离线安装后解析失效（pack 用 worktree 检出整仓 → `vX.Y.Z/agate/agate/scripts` 双层嵌套）；修正同源假设的假 bundle 测试 | BDD-9 ~ BDD-12 |
| **C** | GitHub Release（tag push 自动建）+ 本体 portable tarball + offline tarball；portable 不依赖 git（但仍依赖 `python3` + `pyyaml`） | BDD-13 ~ BDD-21 |
| **D** | 在线安装只装本体（冗余 91% → 可判定阈值）；保留「装任意历史 tag」（`repo/` 保留） | BDD-22 ~ BDD-26 |
| **E** | 彻底删除 legacy 软链支持 + fail-closed 迁移提示 + 4 平台接入不受影响 | BDD-27 ~ BDD-45 |
| 收口 / 负向 | out-of-scope 文件零 diff、全量 pytest、consistency / ruff / shellcheck、发布物 | BDD-46 ~ BDD-50 |
| 评审修订追加（retry #1，编号追加在末尾防漂移） | 软链基址 + 有效 `current` 链的规则（属子批 E）；包内脚本缺 `agate/tests/` 的冒烟（属子批 A/D） | BDD-51 ~ BDD-52 |

### 1.1 用户已裁决（dispatch-context 转达，直接写入需求，不再列为待确认）

1. **CI 许可**：允许新增 `.github/workflows/` release workflow，**含触发条件（`on: push tags v*`）与 `permissions: contents: write`**；PR 描述须如实列出触发 / 权限（见 BDD-13、BDD-50）。
2. **legacy 迁移方式**：**仅文档化迁移三步 + fail-closed 提示**（检测到 `~/.agate` 为软链 → 报错并打印 `mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions` 三步）；**不做迁移工具**（BDD-27、31~36）。
3. **版本号**：沿用 0.x **minor bump**，UPGRADING 明确标注 **BREAKING**，不 bump 1.0。**⚠ 具体版本号见 §2：`v0.72.0` 已被 TAG0036 占用，本任务对应 `v0.73.0`**（BDD-50）。
4. **存量用户规模**：见 §1.2，已如实核对。

### 1.2 存量用户规模核对（独立复核结果，写入需求而非再问用户）

| 证据 | 结果 |
|------|------|
| 本机 `~/.agate` | 实测**非软链**（`test -L` 假、实体目录：`current→latest→v0.71.1` + `repo/` + `scripts/` + `v0.71.1/`）；根 `AGENTS.md:62` 记载 2026-09-18 已从 legacy 迁移 |
| 公开仓库外部足迹 | `gh api`：stars 0 / forks 0 / watchers 0；14 日 clone 数 2849（uniques 284，含 CI / 机器人 / 自有机器，**无法归因到真实软链用户**） |
| GitHub Release | `gh release list` 空（0 个）——无发行物可能被外部依赖 |
| 结论 | **已知 legacy 存量实例 = 1（本机，已迁移）**；外部规模无遥测无法证明为零，故**按"可能存在未知软链用户"设计**：fail-closed + 三步迁移文案 + UPGRADING 明确 BREAKING，且 `install.sh` 无参（官网 / README 主推的 `curl \| bash` 一键装法）对软链用户必须给出迁移提示而非静默破坏（BDD-31） |

## 2. P0-brief 时效性质疑

立项 2026-09-19，启动同日；期间 origin/main 合入 PR #352 / #353（P0 补「本体精确边界」+「彻底删除 legacy」，已并入当前 P0-brief）。主 Agent 已核对"无严重漂移"，本节为 analyst **独立复核**（`git tag`、`git ls-tree`、`gh`、逐行 grep 实测，未照抄）：

已核对 P0-brief 时效性，**无严重漂移**（P0 卡判据 1–3 逐条排查：① 目标方案（结构契约 + Release + 删 legacy）仍成立；② `executor_env`（worktree、稳定版 `~/.agate/current`=v0.71.1）仍成立；③ `known_risks` 的已解决前提无一被他任务解决——GitHub Release 仍 0 个、`agate_common.py:182/219/231/243` 的 `use_legacy` 命中行号逐一核实无误、`test_offline_bundle_roundtrip` 同源假设仍在）。下列为**轻微漂移 / 校正**，已记录，不阻塞：

[P0_STALE: 轻微——最新已发布 tag 已是 v0.72.0（TAG0036，CHANGELOG `[0.72.0]` / UPGRADING `v0.72.0` 节均已存在），P0-brief 与 dispatch-context 的体积 / 文件数据基于 v0.71.1，且 dispatch-context 写"minor bump（v0.72.0）"应更正为 **v0.73.0**；已在本文件按 v0.73.0 写入（BDD-50），P0-brief 数据字段不改（v0.72.0 仅 +check-mvwu.py 等，量级不变：tag 3390 文件 / `agate/` 370 / `agate/tests/` 220）]
[P0_STALE: 轻微——P0-brief 边界表列出 `agate/CLAUDE.md`，实测**该文件不存在**（`ls agate/`、`git ls-files agate` 均无；根 `CLAUDE.md` 是开发者指引且仅指向根 `AGENTS.md`）。边界清单以 `git ls-files` 实测为准（§3.1 T-1），P0 该项无对象，已更正]
[P0_STALE: 轻微——dispatch-context 输入清单写 `agate/tests/integration/test_offline_bundle_roundtrip.py`，实际路径为 `agate/tests/regression/test_offline_bundle_roundtrip.py`；已按实际路径纳入 BDD-11]

## 3. 隐含需求识别

> P1 最常见的失败是"只复述不质疑"。以下为读代码 / 跑复现后识别、用户与 P0-brief 均未明说但**必须**满足的依赖，每条说明"为什么必须"及落到哪条 BDD。

1. **官网 / README 主推的 `curl \| bash` 就是被删除的 legacy 无参路径**（`install.sh` 无参 = 建 `~/.agate` 软链；README / README.zh-CN / `site/index.md` / `site/zh/index.md` / `SiteFooter.vue` 均指向它）。删除软链分支后，**必须定义 `install.sh` 无参的新语义**（P0 已定：直接进版本管理布局，`--versions` 保留为等价别名），否则一键安装入口直接失效；`AGATE_REPO_DIR` / `AGATE_SYMLINK` 两个 legacy 专用环境变量随之成为死参数，须有明确处置（不得静默忽略）。→ BDD-29 / 30 / 31。
2. **离线路径除嵌套 BUG 外还与在线路径有 4 处结构性分叉**（读 `install-offline.py` 实证）：① 不建 `latest` 指针，`current` 直指 `vX.Y.Z`；② **不建根 `~/.agate/scripts/` 副本**——SETUP / README 全部命令以 `python3 ~/.agate/scripts/...` 开头，离线装完这些命令直接 No such file；③ `_DEFAULT_DEST` 硬编码 `~/.agate`、不认 `AGATE_HOME`（`agate-pack-offline.py::_DEFAULT_REPO` 同），与解析侧（认 `AGATE_HOME`，DEBT0042）基址分叉；④ **无软链守卫**——`~/.agate` 是 legacy 软链时会穿透软链把 `vX.Y.Z/` 写进源仓库（TAG0032 在线路径已修的同一类缺陷，离线路径漏了）。判据 2「三路径产出同一结构」不覆盖这些就等于没做。→ BDD-4 / 10 / 33。
3. **已存在的旧格式离线 bundle**（旧 packer 已产出的 `bundle/agate/{整仓树}`）：新 `install-offline` 遇到它必须有确定行为（旧包本来就解析失效，拒绝并提示重打包比"装成半坏状态"更安全）。→ BDD-12。
4. **"只装本体"的排除机制不能依赖被装 tag 自带的配置**：若排除靠 tag 内的属性 / 清单文件，则**历史 tag（早于该机制）装出来仍是全量**——「保留装任意历史 tag」与「只装本体」在老 tag 上互相打架。契约必须对老 tag 同样成立。→ BDD-24。
5. **本体边界还有 P0 未列的三类文件**：`LICENSE`（MIT，要求"所有副本"含版权与许可声明——Release 二次分发的 tarball 若不带它即违反自身许可）、`NOTICES.md`（`role-system.md:249` 引用的 gstack 致谢）、`CHANGELOG.md`（`agate-summary.py` **每次会话启动**都提示读它；在线整仓形态下它在 `vdir/CHANGELOG.md`，只装 `agate/` 会让该提示静默指向死路）。→ T-1 表 / BDD-2。
6. **`agate-install.py --check` 强制要求 git**（`_cmd_check` 把 git 与 python3 / pyyaml / bash 并列必备，缺 git 即 exit 1）。portable 的卖点是"不依赖 git"，`--check` 却在无 git 环境报失败——自相矛盾。须给 portable 口径，且**既有口径（`test_bdd_7/8`）不变**。→ BDD-18。
7. **`~/.agate` 当作"协议根"的遗留路径**（仅 legacy 下成立，版本布局下是死路径）——不止 `SETUP.md` 的 `$AGATE_DIR` fallback：`agate-summary.py:179` 每次启动打印"读 `~/.agate/AGENTS.md`"（版本布局下该文件不存在，应为 `{AGATE_ROOT}/AGENTS.md`）；`agate/assets/templates/handoff-template.md:37` 的 `~/.agate/orchestrator-template.md`；`agate/orchestrator-template.md:20` 的"脚本不可用则默认 `~/.agate`"。→ BDD-40。
8. **判据 10 的 grep 断言若只搜 `use_legacy|legacy 软链布局` 会漏**：同一概念还有"单软链""软链兜底""单软链布局（legacy）"等同义写法（`SETUP.md` / `adr.md` / `WORKFLOW.md` / `agate-summary.py` / `agate/AGENTS.md` / `UPGRADING.md` 均用之，见 §5 扫描 C）。断言须覆盖同义词，并对"允许出现的位置"给出**有限、显式的白名单**（fail-closed 文案、迁移文档、历史版本节）。→ BDD-37。
9. **`vX.Y.Z/` 顶层"唯一内容"需给隐藏元数据留登记口**：离线安装当前写 `.installed-version`（**全仓无任何读取方**，仅被自家测试断言）、`git worktree` 形态有 `.git` 指针文件、Release tarball 需带 LICENSE。契约不登记就无法"机械验证顶层条目集合"，登记则可验证任何未登记条目 = FAIL。→ BDD-1 / 3 / 4。
10. **时序：release workflow 必须先合入 main，v0.73.0 tag 才会触发它**（tag push 触发使用被打 tag 的 commit 上的 workflow 文件）；v0.73.0 是本 workflow 的**首次真实运行**。故"CI 实跑验证"须在合并前用测试 tag 做（BDD-20），且 P8 须把"v0.73.0 推送后 Release 自动出现"作为发布验收项（BDD-21 / 50）。
11. **GitHub 会自动为每个 tag 生成 "Source code (zip / tar.gz)"**——含全量仓库，与我们的本体 tarball **并存**。Release notes / 文档须明确"下载哪个"，否则用户仍会拿到 91% 冗余的整仓包。→ BDD-14 / 19。
12. **tarball 成员路径安全（供应链 / security 域）**：产物不得含绝对路径、`..`、软链 / 硬链 / 设备文件成员；`install-offline` 已有 manifest 路径穿越校验（CRITICAL-3），新增的任何解包入口须同等防护。→ BDD-15。

**分析师衍生项的子批归属**（评审「范围纪律」建议，供 P7 一致性核对；均未越出 P0-brief 子批边界，故不标 `[SCOPE+]`）：BDD-8（`_protocol_root` 双实现一致性）→ 子批 A（回归拦截，同类扫描 F）；BDD-10（离线补 `latest` / 根 scripts / `AGATE_HOME` 同源）→ 子批 B + 判据 2；BDD-18（`--check` portable 口径）→ 子批 C（判据 6）；BDD-21（改 AGENTS.md 发布清单）→ 子批 C（tag ↔ Release 双轨，P0 known_risks）；BDD-33（离线软链守卫）、BDD-34（summary 软链提示）、BDD-40（协议根遗留路径）→ 子批 E（删 legacy 的完整性）；BDD-51 / 52 → 子批 E / A。

## 3.1 本体精确边界清单 T-1（判据 1 的核心输入；S-1…S-6 已按评审 m-1 采纳为 **P1 基线值**——P2 只选打包 / 排除**机制**，不再改这些边界值）

**事实基线**（`git ls-tree -r -l v0.72.0` 实测，字节数取自该 tag）：`agate/` 370 文件 / 3,309,321 B（3.31MB）（`agate/tests/` 220 文件 / 1,608,842 B（1.61MB）= **48.6%**）；入包基线值 B = 除 tests 外的 `agate/` 1,700,479 B + `CHANGELOG.md` `LICENSE` `NOTICES.md` 共 164,392 B = **1,864,871 B（1.86MB）**；仓库其余：`agate-workspace/` 2571 文件、`archived/` 220、`site/` 131、`docs/` 93、`.github/` 4，根文件 `LICENSE` `NOTICES.md` `CHANGELOG.md`（162KB）`README*` `pyproject.toml` `SELF-GATE.md` `AGENTS.md` `CLAUDE.md` `install.sh` `HANDOFF-*.md` `.gitignore` `.gitattributes`。**git 跟踪文件中 `__pycache__` 命中 0**（工作副本 / 安装目录可能有，故仍须显式排除）。

| # | 路径 / 模式 | 处置 | 依据 |
|---|------------|------|------|
| 1 | `agate/` 下**除 `tests/` 外**全部跟踪文件（协议卡 / 规则 / 角色 / 模板 / `scripts/`） | **入包（必须）** | 协议运行面；`agate/` 目录名固定（design-rename-execution.md §8.1） |
| 2 | `agate/AGENTS.md` | **入包**（基线，S-2） | 协议本体入口；`agate-summary` 启动提示与 SETUP 引用；与仓库根开发者指引 `AGENTS.md` 是两个文件 |
| 3 | `agate/tests/`（220 文件 / 1.61MB） | **排除**（基线，S-1） | 使用者无需跑 Agateon 自身测试（`platform-notes.md:181` 已声明 pytest 仅开发者）；占本体 48.6%；维护者工具（`check-protocol-consistency.py` 等）本就以**仓库根**为检查对象，在包内不可用 |
| 4 | `__pycache__/`、`*.pyc` | **排除（必须）** | 构建产物 |
| 5 | 仓库根 `.github/` `site/` `docs/` `archived/` `agate-workspace/` | **排除（必须）** | 维护者产物 / 产品 Web 层 / 开发资料 / Agateon 自身任务数据（会被用户误认为自己的任务空间） |
| 6 | `HANDOFF-*.md` | **排除（必须）** | 开发交接单 |
| 7 | `README.md` `README.zh-CN.md` `pyproject.toml` `SELF-GATE.md` 根 `AGENTS.md` 根 `CLAUDE.md` `install.sh` `.gitignore` `.gitattributes` | **排除**（基线，S-5） | 仓库门面 / 开发配置 / 维护者指引；运行面无依赖（使用者文档已在 `agate/UPGRADING.md` `agate/SETUP.md`） |
| 8 | `CHANGELOG.md` | **入包**（`vX.Y.Z/` 顶层；基线，S-4） | `agate-summary.py:152-160` 探测 `<root>/../CHANGELOG.md`；每会话启动读取；整仓形态下原本就在 `vdir/` 顶层 |
| 9 | `LICENSE`、`NOTICES.md` | **入包**（`vX.Y.Z/` 顶层；基线，S-3） | MIT「所有副本须含许可声明」；`role-system.md:249` 引用 NOTICES.md |
| 10 | 隐藏元数据（如 `.git` worktree 指针、`.installed-version`） | 默认**不允许**；实现若需要须在契约文档**逐个登记** | 使"顶层条目集合"可机械验证 |

**结论性契约形态**（P2 定案的输入）：`vX.Y.Z/` 顶层条目集合 = {`agate/`} ∪ {入包的根级登记文件（S-3 / S-4：`LICENSE` `NOTICES.md` `CHANGELOG.md`）} ∪ {已登记隐藏元数据}；`_protocol_root(vX.Y.Z)` 命中既有**探测序 2**（`vdir/agate/scripts`）返回 `vdir/agate`——**新契约形态本身就是既有探测序已支持的形态，`_protocol_root` 无需改动**（BDD-6）。

## 4. BDD 验收条件

> 二值判定；无 PASS/FAIL 预判字样；`[NO_NEED_CONFIRM]`（文首）。判据映射见 §4.7。
> 【隔离】= `HOME` / `USERPROFILE` / `AGATE_HOME` 指向 `tmp_path`；本地 `file://` git 上游仓库（`AGATE_REPO_URL`）；不联网、不触真实 `~/.agate`。（BDD-42/43/45 的"CLI 自身配置"例外见各条 Given。）
>
> **全或无规则（M-1，方案 b）**：凡标题带 `[参数化]` 的 BDD（含多个 When / 夹具 / 调用形态），其**全部子场景逐一判定**，**任一子场景失败则该 BDD 整体判 FAIL**（不存在"部分通过"）；P6 验收须**逐子场景留证据**（证据文件按 `BDD-N.<子场景序号>` 命名）；P6 的 PASS/FAIL 总数仍以 BDD 编号条数计。未带该标签的 BDD 均为单一 Given-When-Then。

### 4.1 子批 A：版本目录结构契约

#### BDD-1: 结构契约成文于权威源，含根级结构与登记项
- Given `agate/UPGRADING.md`「版本管理生命周期」节（权威源，`test_upgrading_lifecycle.py` 已锁该节存在）
- When 读取该节
- Then 含且仅含**一个**契约小节，其中同时给出：(a) 版本根结构树（`vX.Y.Z/`、`latest`、`current`、根 `scripts/`、可选 `repo/`）；(b) `vX.Y.Z/` 顶层条目集合的完整列举（`agate/` + T-1 表 #8/#9 的根级登记文件 + 已登记隐藏元数据），并写明"未登记的顶层条目 = 违约"；(c) 目录名固定为 `agate/`，**不出现**"本体目录名可配置 / 由 manifest 声明"的表述（grep `可配置|可扩展|manifest 声明` 于该小节无命中）；(d) 边界清单的**单一来源文件路径**（BDD-3）

#### BDD-2: 本体边界清单逐项落到包内文件集合
- Given 【隔离】+ 当前仓库 HEAD（或等价的合成 tag 仓库，含 T-1 全部条目的代表文件）+ 产品实际使用的「生成本体包」入口（P2 定名，在线安装 / tarball / offline pack 共用同一份边界逻辑）
- When 对该 tag 生成本体包，得到包内文件相对路径集合 F_pkg
- Then ① T-1 标"必须入包"的项全部 ∈ F_pkg（至少含 `agate/scripts/agate-install.py`、`agate/scripts/agate_common.py`、`agate/WORKFLOW.md`、`agate/orchestrator-template.md`、`agate/phase-cards/`、`agate/rules/`、`agate/assets/`）；② T-1 标"必须排除"的项全部 ∉ F_pkg（金丝雀集合：任一以 `agate-workspace/`、`docs/`、`site/`、`archived/`、`.github/` 开头的路径；任一 `HANDOFF-*.md`；任一 `__pycache__/` 或 `*.pyc`）；③ 已采纳的基线值同样成立：`agate/tests/` ∉ F_pkg；`agate/AGENTS.md`、`LICENSE`、`NOTICES.md`、`CHANGELOG.md` ∈ F_pkg；`README*`、`pyproject.toml`、`SELF-GATE.md`、根 `AGENTS.md` / `CLAUDE.md`、`install.sh`、`.gitignore`、`.gitattributes` ∉ F_pkg（T-1 #2 #3 #7 #8 #9）；④ F_pkg 顶层条目集合 == BDD-1 登记的集合（无多无少）

#### BDD-3: 排除清单来源单一可维护，文档与来源不漂移，默认拒绝新增顶层内容 [参数化]
- Given 边界清单的单一来源（P2 定机制与路径：可为属性文件 / 显式清单 / 打包脚本常量——**P1 不选**）与 UPGRADING 契约小节
- When ① 在合成 tag 仓库根新增一个**未登记**的顶层目录 `zz-new/`（含文件）；② 在其 `agate/` 下新增一个普通文件 `agate/zz-new.md`；③ 比对 UPGRADING 契约小节列举的条目与该来源文件所列条目
- Then ① `zz-new/**` ∉ F_pkg（**默认不入包**，新增顶层内容须显式登记才入包）；② `agate/zz-new.md` ∈ F_pkg（本体新增文件自动入包，`tests/` `__pycache__` 除外）；③ 两处条目集合**相等**（文档由来源生成或有一致性测试锁定，不得各自维护）

#### BDD-4: 三条安装路径产出同一结构
- Given 【隔离】+ 同一合成 tag `vX.Y.Z`（含 `agate/`（含 `tests/`）+ 噪声：`agate-workspace/tasks/TAG0001-x/`、`docs/`、`site/`、`archived/`、`HANDOFF-X.md`、`CHANGELOG.md`、`LICENSE`、`NOTICES.md`）三个独立 `AGATE_HOME`：H1 / H2 / H3
- When H1 走**在线**（`agate-install.py latest`，git 上游为本地 `file://`）；H2 走**离线**（`agate-pack-offline.py` 真实 git 步骤 + `install-offline.py`；仅 `pip download` 的网络调用可 stub，git 检出 / 导出必须真实执行）；H3 走 **portable**（本体 tarball 按 UPGRADING 文档所列步骤解压并建指针，BDD-17）
- Then ① 三处 `vX.Y.Z/` 下递归文件相对路径集合**逐一相等**（且不含 `wheels/`、`manifest.json` 等安装输入物）；② 三处 `_protocol_root(vX.Y.Z)` 均为 `vX.Y.Z/agate`；③ 三处版本根均含 `latest → vX.Y.Z`、`current → latest`（Windows 文本指针等价）与根 `scripts/agate-install.py`；`repo/` 仅 H1 存在（可选项，非契约必需）；④ 三处 `agate-resolve.py` 均 exit 0 且 `AGATE_VERSION=vX.Y.Z`、`AGATE_ROOT` 结尾为 `vX.Y.Z/agate`

#### BDD-5: 已装旧形态 `vX.Y.Z/{agate, agate-workspace, docs, …}` 仍可解析 [参数化]
- Given 【隔离】+ 用**旧安装器同款方式**（`git worktree add --detach vX.Y.Z <tag>`，整仓树检出）手工构造的旧形态版本根：`vX.Y.Z/{agate,agate-workspace,docs,site,archived,HANDOFF-*.md,CHANGELOG.md,…}` + `latest` + `current`（新安装器不再产出该形态，fixture 须**显式构造**并保留在测试中）
- When 分别运行 ① `agate-resolve.py`（cwd 无 `.agate-version`）；② 在项目根写 `.agate-version`（`agate: vX.Y.Z`）后 `agate-resolve.py`；③ `resolve-entry.py pre-commit` 的 gate 路径解析（`resolve_hook_root`）；④ `agate-summary.py`
- Then 四者均 exit 0；① `AGATE_ROOT` 为 `vX.Y.Z/agate`、`AGATE_REASON=全局 current`；② `AGATE_REASON=引用 .agate-version`；③ 解析出的 `<root>/scripts/pre-commit-gate.py` 存在；④ 输出 `版本：vX.Y.Z`

#### BDD-6: `_protocol_root` 探测序语义不变，新契约形态零改动命中
- Given `agate_common._protocol_root` 既有探测序：`vdir/scripts` 优先 → `vdir/agate/scripts` → 原样返回（红线：不可颠倒，只可增量扩展）
- When 运行既有用例 `test_tag0032_bdd_6_meta_repo_resolve_returns_agate_subdir` / `test_tag0032_bdd_7_rootproto_resolve_semantics_unchanged`，并新增一条：同时含 `vdir/scripts` 与 `vdir/agate/scripts` 的目录调用 `_protocol_root`
- Then 既有两用例**源码未被修改**且通过（`git diff` 这两个用例为空）；新增用例返回 `vdir`（探测序 1 优先）；`_protocol_root` 函数体在本任务 diff 中**无删改**（若 P2 论证需增量探测序 3，须在 P2 明示且探测序 1、2 的返回语义不变——`[SUGGEST: S-16]` 推荐**不增加**）

#### BDD-7: 旧形态版本与新形态版本共存 [参数化]
- Given 【隔离】+ 版本根内已有旧形态 `v0.71.1/`（BDD-5 fixture）+ 用新安装器再装的新形态 `v0.73.0/`，`current` 指向新版
- When ① 无 `.agate-version` 解析；② 项目 `.agate-version` 写 `agate: v0.71.1` 后解析
- Then ① `AGATE_ROOT` 为 `v0.73.0/agate`；② `AGATE_ROOT` 为 `v0.71.1/agate`（旧形态被钉版正确命中）；（旧形态版本的**卸载**判定统一归 BDD-25，此处不重复，避免双重失败源）

#### BDD-8: `_protocol_root` 双实现行为一致（回归拦截，避免第二份实现漂移）
- Given `agate_common._protocol_root` 与 `agate-install.py` 内 pyyaml 缺失时的降级副本 `_protocol_root`（TAG0031 hash 双实现合并的同类隐患：两份探测逻辑）
- When 对同一组目录夹具（仅 `vdir/scripts` / 仅 `vdir/agate/scripts` / 两者皆有 / 两者皆无 / 新契约形态）分别调用两份实现
- Then 五组夹具下两份实现返回值**逐一相等**（探测序改动只改一处必被该测试拦截）

### 4.2 子批 B：离线安装解析失效（P0 BUG）修复

#### BDD-9: 用真实 pack 产物结构离线安装后解析成功
- Given 【隔离】+ 真实布局：合成 tag 仓库（整仓树，含 `agate/` 与噪声顶层目录），`agate-pack-offline.py` 的 **git 步骤真实执行**（**禁止**再用"mock `subprocess.run` 凭空造 `bundle/agate/WORKFLOW.md`"的假 bundle；唯一可 stub 的是 `pip download` 网络调用，wheel 用本地占位文件）
- When `pack_offline` → `install-offline.py <bundle> --dest-root <AGATE_HOME>`（`pip install` 可 stub）→ `AGATE_HOME=<dest> agate-resolve.py`
- Then resolve exit 0，`AGATE_ROOT == <dest>/vX.Y.Z/agate` 且 `<AGATE_ROOT>/scripts/agate-resolve.py` 存在；**不存在** `<dest>/vX.Y.Z/agate/agate/` 双层嵌套；`_protocol_root(<dest>/vX.Y.Z)` 不再"原样返回 vdir"（P0 机理：原样返回 = 解析失效）

#### BDD-10: 离线路径基址与 `AGATE_HOME` 同源，并补齐版本根级结构
- Given 【隔离】+ 仅设 `AGATE_HOME=<tmp>`（`HOME` 指向另一个空 tmp），不传 `--dest-root`
- When 执行 BDD-9 的 `install-offline.py`（以及 `agate-pack-offline.py` 缺省 `--repo`）
- Then 安装落在 `<tmp>`（不落 `HOME/.agate`）；`<tmp>` 下含 `latest`、`current → latest`（**不再直指 `vX.Y.Z`**）与根 `scripts/agate-install.py`；`python3 <tmp>/scripts/agate-install.py --check` 可运行（与在线路径一致，SETUP 中 `~/.agate/scripts/...` 命令在离线安装后可用）

#### BDD-11: 三处"同源假设"的假 bundle 测试助手被修正为反映真实布局
- Given 现有三处以"`bundle/agate/` 就是本体"为前提造数据：`test_install_offline.py::_make_bundle`、`test_agate_pack_offline.py::_fake_artifacts_side_effect`、`regression/test_offline_bundle_roundtrip.py::_fake_pack_artifacts`（后者的 pack→install→卸载链路**从不调用解析**，故同源假设长期不暴露）
- When 审查并运行修正后的测试
- Then ① 三处助手改为经**真实 pack 入口**（BDD-9 口径）或与其共享的 fixture 生成 bundle，源码中不再出现手工 `(agate / "WORKFLOW.md").write_text(...)` 冒充本体的构造；② 新增 sentinel 用例：真实 pack 产出的 `bundle/agate/` 顶层**含** `scripts/` 与 `WORKFLOW.md` 且**不含** `agate-workspace/`、`docs/`、`site/`（bundle 内 `agate/` 是本体而非整仓树）；③ `test_offline_bundle_roundtrip` 的链路末尾追加"安装后 `agate-resolve.py` exit 0"断言；④ **红灯回放**：把 P4 实现临时还原为旧 pack 行为（整仓检出）时，BDD-9 与本 sentinel **必须失败**（P3 须留红灯证据，防同源假设复发）

#### BDD-12: 旧格式 bundle 被拒绝而非装成半坏状态
- Given 【隔离】+ 旧 packer 产出的旧格式 bundle（`bundle/agate/` 为整仓树、`bundle/agate/agate/scripts/` 存在，manifest 校验和自洽）
- When `install-offline.py <旧bundle> --dest-root <tmp>`
- Then exit 1；stderr 指明"bundle 为旧格式（`agate/agate/scripts` 双层嵌套），请用新版 `agate-pack-offline.py` 重新打包"；`<tmp>` 下**不产生**任何 `vX.Y.Z/` 半装目录与 `current` 指针（基线：拒绝而非自动归一化，S-13）

### 4.3 子批 C：GitHub Release + portable

#### BDD-13: release workflow 静态契约（触发 / 权限 / 供应链）
- Given 新增的 `.github/workflows/<release>.yml`（文件名 P2 定），经 `yaml.safe_load` 解析；现有 4 个 workflow（deploy-pages / docs-check / protocol-tests / site-check）
- When 检查该 workflow 与现有 workflow 的 diff
- Then ① 触发器**仅** `on.push.tags` 匹配 `v*`（无 `branches` / `pull_request` / `pull_request_target` / `workflow_dispatch`）；② `permissions` 为 `contents: write` 且**仅此一项**（无 `id-token` / `packages` / `pages` 等）；③ 不引用 `secrets.*`（仅 `GITHUB_TOKEN`）；④ 若使用第三方 action，须固定到 40 位 commit SHA（基线：首选 runner 自带 `gh release create`，零第三方 action，S-10）；⑤ 产出资产名 = `agateon-<tag 名原样>.tar.gz` 与每个支持平台的 `agateon-<tag 名原样>-offline-<platform>.tar.gz`（`<platform>` ∈ {`linux-x86_64`, `windows-x86_64`}，基线 S-19）——正式 tag `vX.Y.Z` 即 `agateon-vX.Y.Z.tar.gz` 等；预发布测试 tag（如 `v0.73.0-tagtest.1`）名称原样进入资产名；offline 资产内 `manifest.json` 的 `version` 字段**恒为严格 `vX.Y.Z`**（预发布 tag 取去后缀版本，因 `install-offline` 的 `_VERSION_RE` 只接受严格 semver）；⑥ 现有 4 个 workflow 文件 `git diff` 为空

#### BDD-14: Release notes 取自 CHANGELOG 对应版本段；正式 tag 缺段 fail-closed，预发布 tag 有确定回落规则 [参数化]
- Given CHANGELOG 夹具含 `## [Unreleased]`（有内容）、`## [0.73.0]`、`## [0.72.0]`；notes 提取逻辑**可在无 CI 环境下被测试直接调用**（不得只存在于 workflow 内联 shell，否则无法测试；承载形态留给 P2）
- When ① 提取正式 tag `v0.73.0`；② 提取夹具中不存在的正式 tag `v0.99.0`；③ 对**真实** CHANGELOG 提取 `v0.72.0`；④ 对预发布测试 tag `v0.73.0-tagtest.1`（严格 `vX.Y.Z` + `-` 后缀）分别在夹具 A（含 `[0.73.0]` 段）与夹具 B（**仅**含 `[Unreleased]` 与 `[0.72.0]`，即 BDD-20 执行时分支 CHANGELOG 的真实状态：`[Unreleased]→[0.73.0]` 重命名在 P8 才发生）上提取
- Then ① 输出恰为 `[0.73.0]` 段正文，不含 `[0.72.0]` 段任何内容；② exit 1、stderr 指明缺段，且**不产生任何输出文件**（正式 tag 缺段不得创建空 notes 的 Release）；③ 输出非空；notes 头部含一句说明"推荐下载 `agateon-vX.Y.Z.tar.gz`（本体），GitHub 自动生成的 Source code 包为整仓"（隐含需求 11）；④ 预发布 tag：夹具 A 取去后缀版本 `[0.73.0]` 段、夹具 B **回落**取 `[Unreleased]` 段，两者均 exit 0，notes **首行**为"预发布测试（<tag 名原样>）——非正式发布"标注，且不含 `[0.72.0]` 段内容（**回落规则只对预发布 tag 生效**，正式 tag 缺段仍按 ② fail-closed）

#### BDD-15: 本体 tarball 与 tag 内容一致且成员安全
- Given 合成 tag 仓库（同 BDD-4）与可在无 CI 环境下调用的本地打包入口（CI 产物与该本地入口产物**逐成员字节一致**，由 BDD-20 ③ 判定；承载形态留给 P2）
- When 对该 tag 生成 `agateon-vX.Y.Z.tar.gz`
- Then ① 文件名精确；② 解包后条目集合 == F_pkg（BDD-2），且**顶层无包裹目录**（`tar -xzf … -C ~/.agate/vX.Y.Z/` 即得契约形态）；③ 每个成员内容与 `git show <tag>:<path>` 的 **blob 字节逐一相同**（**双轨一致**：asset 与 tag 同版本同内容；`.gitattributes` 含 `*.py text eol=lf` 等规则，故打包机制不得使用会做 eol / 文本转换的导出路径，否则与 blob 字节可能不同）；④ 所有成员为普通文件 / 目录：无绝对路径、无含 `..` 的路径、无软链 / 硬链 / 设备文件成员（`tar -tvf` 逐项判定）

#### BDD-16: offline tarball 解包后可被 install-offline 直接消费
- Given 同 BDD-15 + `pip download` 以本地占位 wheel stub
- When 生成 `agateon-vX.Y.Z-offline-linux-x86_64.tar.gz` → 解包 → `install-offline.py <解包目录> --dest-root <AGATE_HOME>`（`pip install` stub）
- Then 解包目录含 `manifest.json` + `agate/`（本体，非整仓）+ `wheels/`；manifest 中 `version` / `platform` 正确、各组件 sha256 校验通过；安装后满足 BDD-4 的结构断言与 `agate-resolve.py` exit 0

#### BDD-17: portable 安装不依赖 git，解压即用
- Given 【隔离】+ 一个 `PATH` 目录 `P`：仅含 `python3`（含 `pyyaml`）与必要 coreutils 的链接，`command -v git` 在该 `PATH` 下**失败**；本体 tarball（BDD-15 产物）
- When 按 UPGRADING「portable 安装」小节**所列命令逐条实跑**（经变量替换；**不得**另写测试专用命令，文档即验收脚本）：解压 → 建 `latest` / `current` 指针 → 根 `scripts/` 就位
- Then 全程 exit 0 且无 git 调用；`agate-resolve.py` exit 0，`AGATE_VERSION=vX.Y.Z`；`agate-summary.py` exit 0（无 CHANGELOG 探测崩溃）；`agate-install.py --check`（portable 口径，BDD-18）exit 0

#### BDD-18: `--check` 提供 portable 口径，既有口径不变 [参数化]
- Given 【隔离】+ 无 git 的 `PATH`（BDD-17 的 `P`）；以及缺 pyyaml 的 `PATH`
- When ① 无 git 环境下跑 portable 口径 `--check`；② 缺 pyyaml 环境下跑 portable 口径；③ 无 git 环境下跑**默认口径**（现行 `--check`）
- Then ① exit 0，git 缺失仅提示"仅在线安装 / 装历史 tag 需要"；② exit 非 0 且列出 pyyaml 修复指引；③ exit 1 且列出 git 缺失（**既有 `test_bdd_7` / `test_bdd_8` 源码未改且通过**）（基线：portable 口径为 opt-in 标志，默认口径不变，S-12）

#### BDD-19: 文档不宣称"零依赖"，且声明 portable 的真实依赖
- Given README / README.zh-CN / `agate/UPGRADING.md` / `agate/SETUP.md` 的 portable 相关小节与 Release notes 模板
- When grep `零依赖|zero[- ]dependenc|no dependenc|无任何依赖`（不区分大小写）
- Then 0 命中；且 portable 小节含 `python3` 与 `pyyaml` 两项依赖声明，并写明"无需 git，但 `agate-changes.py` 等依赖 agate git 仓库的工具不可用"

#### BDD-20: 测试 tag 上 CI 实跑验证（合并前）
- Given 本任务分支已含 release workflow；分支 CHANGELOG 此时仍只有 `[Unreleased]`（重命名在 P8），故该 tag 的 notes 走 BDD-14 ④ 夹具 B 的回落规则；**执行前主 Agent 取得用户当次许可**（向 origin 推 tag 属外部可见操作）；测试 tag `v0.73.0-tagtest.1`（基线 S-9：匹配 `v*` 触发；不匹配严格 `^v\d+\.\d+\.\d+$`，故 `agate-install.py latest` 的版本选择忽略它——**注意 CHECK 7 / G-5 的 `git describe --tags --abbrev=0` 不做 semver 过滤，不忽略它**）；**先后顺序（强制）**：本 BDD 的 ④ 清理完成**之后**才可跑 CHECK 7 / BDD-49，否则该 tag 在 HEAD 期间会使本地 CHECK 7 取到 `0.73.0-tagtest.1` 而与 badge 失配；**副作用声明**：tag push 会连带触发所有含 `push` 触发器的现有 workflow（`protocol-tests.yml` 为 `on: [push, pull_request]`，必触发；`docs-check.yml` / `site-check.yml`（`push` + `paths`）及 `deploy-pages.yml`（`branches: [main]`）是否触发以 `gh run list --commit <sha>` **实测为准**并记录），这些连带运行的结论与本 BDD 判定无关，但须如实写入 PR 描述（与 BDD-50 ③ 同口径）
- When 把该 tag 打在本分支 HEAD 并推送 → 等 release workflow 结束 → 取产物 → **清理**（`gh release delete <tag> --cleanup-tag --yes`，并 `git tag -d`）
- Then ① `gh run list --workflow=<release>.yml` 该次运行 `conclusion == success`；② Release 存在且标为 prerelease，notes 首行为预发布测试标注（BDD-14 ④）；资产名 = `agateon-v0.73.0-tagtest.1.tar.gz` 与 `agateon-v0.73.0-tagtest.1-offline-<platform>.tar.gz`（**tag 名原样**，BDD-13 ⑤），`gh release download` 全部成功；③ 本体 asset 解包后成员内容与本地打包入口对同一 tag 的产物**逐成员字节一致**（BDD-15 ④ 的 CI/本地一致性）；offline asset 内 `manifest.json` 的 `version` 为严格 `v0.73.0` 且各组件 sha256 校验通过（**不**在真实环境跑 `pip install`）；④ 清理后 `gh release list` 无该 tag、`git ls-remote --tags origin v0.73.0-tagtest.1` 为空、本地无该 tag、`git describe --tags --abbrev=0` 不再返回它——**正式 Release 列表零污染**；⑤ 降级口径（用户不许可推 tag 时）：以 BDD-13~16 的本地全链路 + `actionlint` 静态校验替代，并把 v0.73.0 正式 tag 触发标为 P8 的首次真实运行验收（BDD-21 / 50），由主 Agent 提 `[BASELINE_CHANGE]` 显式记录

[BASELINE_CHANGE: BDD-20 范围口径（仅注解，不改 Given/When/Then）——Then ④（清理）由用户按其自身决定**手动执行**；P6 对 BDD-20 的验收范围 = ①②③ + 一份精确的待清理清单（GitHub Release `v0.73.0-tagtest.1` 与远端 tag `refs/tags/v0.73.0-tagtest.1`）；④ 在 P8 开 PR 前以只读命令复核（`gh release list`、`git ls-remote --tags origin v0.73.0-tagtest.1`、`git tag -l 'v0.73.0*'`、`git describe --tags --abbrev=0`）。验收人不得自行删除该 tag / Release。CHECK 7 / BDD-49 须在清理完成后运行的先后顺序约束不变。依据：主 Agent 依用户裁决所作范围裁定。]

#### BDD-21: tag 与 Release 双轨不失配（防"打了 tag 忘了 Release"）
- Given AGENTS.md「版本发布清单」与 P8 阶段卡引用的版本引用文件清单
- When 检索发布清单
- Then 含 push tag 之后的 Release 校验步骤（命令含 `gh release view v<版本>` 并断言 3 个资产：本体 + 两平台 offline）以及"tag 已推而 Release 缺失"的补救步骤（用本地打包脚本重建并 `gh release create`，因 workflow 无 `workflow_dispatch`）；G-5 最终验证条目同步含 Release 存在性

### 4.4 子批 D：在线只装本体 + 保留历史 tag

#### BDD-22: 在线安装只装本体，不装维护者产物与自身任务数据
- Given 【隔离】+ 合成上游 tag 仓库（同 BDD-4，含 `agate-workspace/tasks/TAG0001-x/`、`docs/reviews/`、`site/`、`archived/`、`HANDOFF-X.md`）
- When `agate-install.py latest`
- Then `vX.Y.Z/` 文件集合 == F_pkg；下列均**不存在**：`agate-workspace`、`docs`、`site`、`archived`、`.github`、`HANDOFF-*.md`；`AGATE_ROOT` 为 `vX.Y.Z/agate`；根 `scripts/` 副本仍由 `_sync_root_scripts` 建立（`test_tag0032_bdd_4` 保持通过）

#### BDD-23: 冗余量化下降
- Given BDD-22 的安装结果；旧形态基线（本机 `~/.agate/v0.71.1` 只读实测）：整仓形态 `vX.Y.Z/` 文件字节和 35.6MB，其中本体 `agate/` 3.28MB，即**冗余 ≈ 91%**（`du -sh` 口径 43M vs 4.1M）
- When 计算 `S = vX.Y.Z/ 内全部文件字节和`（`du -sb` 等价，忽略目录项开销）与 `B = 按 T-1 入包清单对该 tag 求和的文件字节和`
- Then `S ≤ 1.25 × B`（冗余 ≤ 20%，基线 S-8）；在 tag v0.72.0 上 B = 1,864,871 B（T-1 基线值），即 `S ≤ 2,331,089 B（2.33MB）`，较旧形态 35.6MB 下降 >93%；合成仓库用例用同一判定式；**真实仓库实测**（P5 / P6：在隔离 `AGATE_HOME` 下对 v0.72.0 或 HEAD 做在线安装，`du -sb` 记录）须同样满足

#### BDD-24: 保留「装任意历史 tag」，且同样只装本体 [参数化]
- Given 【隔离】+ 版本根已有 `repo/` 与 `latest → vN`；上游含更老的 `v0.48.0`——其树内**没有任何"排除机制文件"**（早于该机制）与 `agate/` + 噪声顶层目录；更新的 `v0.49.0`；以及一个**树内无 `agate/scripts/`** 的畸形 tag `v0.1.0`
- When ① `agate-install.py v0.48.0`，项目写 `.agate-version: agate: v0.48.0`；② `agate-install.py v0.1.0`
- Then ① `v0.48.0/` 文件集合 == 对该 tag 应用 T-1 得到的 F_pkg（**不因该 tag 缺排除配置而退回全量**）；`latest` / `current` **指针不变**（既有契约：`vX.Y.Z` 只预装不改指针）；项目内 `agate-resolve.py` 得 `AGATE_VERSION=v0.48.0`；`repo/` 仍在；② exit 1，stderr 指明该 tag 无 `agate/scripts/`，**不留半装版本目录**、指针不变（fail-closed，避免装出无法解析的空目录）

#### BDD-25: 卸载兼容新旧形态，repo/ 有无均可 [参数化]
- Given 【隔离】+ 新形态版本目录 ① 版本根含 `repo/`；② 版本根**无** `repo/`（offline / portable 安装）；③ 旧形态 worktree 版本目录（BDD-5 fixture）
- When 各自 `agate-install.py --uninstall vX.Y.Z`（无项目引用）
- Then 三者均 exit 0，版本目录被移除，`latest` / `current` 曾指向它时被重指最新有效版本或清除（不悬空），`repo/` 存在时其 `git worktree list --porcelain` 无残留条目；引用保护语义不变（有 `.agate-version` 引用时仍 exit 1 拒绝）

#### BDD-26: 在线安装幂等且不污染源仓库树（既有契约保持）
- Given 【隔离】+ 同一 `AGATE_HOME` 连续两次 `agate-install.py latest` 与一次 `install.sh`（无参，BDD-29）
- When 比较两次之间的版本根与源仓库 checkout 的 `git status --porcelain`
- Then 第二次不报错、不重复建版本目录、指针幂等；源 checkout（脚本所在仓库）无新增 `repo/` / `vX.Y.Z/` / 非预期未跟踪条目；既有 `test_bdd_3`、`test_tag0032_bdd_3/4/5`、`test_tag0032_bdd_13/14`（`test_version_lifecycle_e2e.py`）保持通过

### 4.5 子批 E：彻底删除 legacy 软链支持

#### BDD-27: `agate-resolve.py` 对软链 `~/.agate` fail-closed 并打印迁移三步
- Given 【隔离】+ `AGATE_HOME`（或 `HOME/.agate`）是**软链** → 一个含 `scripts/` 与 `assets/` 的目录（原 legacy 形态，即现有 `test_bdd_30_legacy_symlink_direct_root` 的 fixture）；未设 `AGATE_ROOT`
- When `agate-resolve.py`
- Then **exit code == 1**（基线 S-15，取 1 的理由：`install.sh` / `agate-install.py` / `agate-resolve.py` 现行 fail-closed 均为 1，2 保留给用法错误；改码会破坏依赖方与既有 `test_tag0032_bdd_1` 语义）；stdout 无 `AGATE_ROOT=` 行；stderr 含三步片段 `mv ~/.agate ~/.agate.bak`、`mkdir -p ~/.agate`、`install.sh`（装版本命令）；软链目标目录内容前后不变

#### BDD-28: 解析链仅剩「env → 项目声明 → current」三层，`use_legacy` 彻底消失 [参数化]
- Given 【隔离】+ 依次构造：(a) 设 `AGATE_ROOT`；(b) 项目 `.agate-version` 声明已装版本；(c) 仅 `current` 指针；(d) 三者皆无（终态）；(e) 设 `AGATE_ROOT` **且** `AGATE_HOME` 为软链
- When 各自运行 `agate-resolve.py`
- Then (a)(e) `AGATE_REASON=AGATE_ROOT 环境变量覆盖` 且 exit 0（env 覆盖在软链下仍生效，开发 worktree 场景依赖）；(b) `引用 .agate-version`；(c) `全局 current`；(d) exit 1（终态 fail-closed，`test_resolve_terminal_failure_fail_closed` 保持）；`AGATE_REASON` 取值集合 ⊆ {上述三种}，**任何输出不含 `legacy`**；`inspect.signature(agate_common._resolve_version_info)` **无 `use_legacy` 参数**；`agate_common.py` 中**不存在把软链目标当 `AGATE_ROOT` 返回的分支**（即 `realpath(base)` 作 root 的逻辑）——软链**检测 + 迁移提示**分支允许存在且位置不限（BDD-27 / 34 需要它），实现者不得为满足字面而删掉检测

#### BDD-29: `install.sh` 无参直接进入版本管理布局，`--versions` 保留为等价别名 [参数化]
- Given 【隔离】+ `HOME` 下无 `~/.agate`；`AGATE_REPO_URL` 指本地 `file://` 上游；`PATH` 含 git 与 python3
- When ① `bash install.sh`（无参）；② 另一个隔离 HOME 下 `bash install.sh --versions`
- Then 两者均 exit 0，`~/.agate` 为**实体目录**（非软链），含 `repo/`、契约形态的 `vX.Y.Z/`、`latest → vX.Y.Z`、`current → latest`、`scripts/agate-install.py`；两个版本根的目录结构树**相等**；脚本所在 checkout 的 `git status --porcelain` 无新增（不污染源仓库）；`install.sh` 中**不再含**建软链逻辑（`ln -s` / `LINK_NAME` 不出现）

#### BDD-30: 废弃环境变量 `AGATE_REPO_DIR` / `AGATE_SYMLINK` 有明确处置
- Given 【隔离】+ BDD-29 的环境 + 设置 `AGATE_SYMLINK=<tmp>/x` 与 `AGATE_REPO_DIR=<tmp>/y`
- When `bash install.sh`（无参）
- Then exit 0；stderr 含一行 WARNING 指明这两个变量已废弃且被忽略（基线 S-14：不静默忽略，也不因此失败）；`<tmp>/x`、`<tmp>/y` **均未被创建**；`install.sh` 头注释 / 末尾用法提示不再引用这两个变量；`test_agate_version_install.py` / `test_version_lifecycle_e2e.py` 中对 `AGATE_REPO_DIR` 的引用与"pre-P4 legacy 分支快速失败"注释一并清理

#### BDD-31: `install.sh` 遇软链 `~/.agate` fail-closed（无参与 `--versions` 两个入口） [参数化]
- Given 【隔离】+ `~/.agate` 是软链 → 含 `scripts/` `assets/` 的目录（存量用户重跑官网一键命令的场景）
- When ① `bash install.sh`（无参）；② `bash install.sh --versions`
- Then 两者均 **exit 1**；stderr 含三步迁移片段（同 BDD-27）；软链目标目录**不新增** `repo/` 与任何 `vX.Y.Z/`（目录列表前后一致）；**未发生** `git clone`（`AGATE_REPO_URL` 指向的上游无访问记录 / 目标 `repo/` 不存在）

#### BDD-32: `agate-install.py` 遇软链 fail-closed（保留并沿用既有拒绝逻辑） [参数化]
- Given 【隔离】+ 软链 `~/.agate`（既有 `_legacy_symlink_home` fixture 语义）
- When `agate-install.py`（无参 / `latest` / `vX.Y.Z`）
- Then 三种调用均 exit 1，stderr 含三步片段，软链目标不被穿透污染（**保留** `test_tag0032_bdd_1_legacy_symlink_install_fail_closed` / `test_tag0032_bdd_2_legacy_symlink_rejection_migration_hint` 的断言实质，仅去掉"legacy 直通解析"相关表述；测试名可去 `legacy` 字样，如 `*_symlink_home_install_fail_closed`）

#### BDD-33: `install-offline.py` 遇软链 fail-closed（此前无守卫，会穿透软链写源仓库）
- Given 【隔离】+ `--dest-root`（或 `AGATE_HOME`）解析到软链 → 含 `scripts/` 的目录 + 一个合法新格式 bundle
- When `install-offline.py <bundle>`
- Then exit 1，stderr 含三步片段，软链目标目录列表前后一致（**无** `vX.Y.Z/`、无 `current`）；`--dest-root` 指向普通目录 / 不存在的新目录时行为不受影响（不误伤）

#### BDD-34: `agate-summary.py` 在软链基址下给出迁移提示而非静默失败
- Given 【隔离】+ 软链 `~/.agate`（存量用户 `git pull` 后每会话启动跑 `agate-summary.py` 的场景）
- When `agate-summary.py`
- Then 进程不崩溃；输出的 `AGATE_ROOT` 行明确为"无可用"；输出含一行迁移提示（含 `mv ~/.agate ~/.agate.bak`）；启动建议中的协议入口路径取自**解析出的根**（`{AGATE_ROOT}/AGENTS.md`），不再是硬编码 `~/.agate/AGENTS.md`（BDD-40）

#### BDD-35: 三步迁移文案跨入口逐片段一致（DEBT0034 守护延续）
- Given 迁移三步出现的全部入口：`install.sh`（heredoc）、`agate-install.py`（常量）、`install-offline.py`、`agate_common.py`（resolve 侧）、UPGRADING 迁移小节
- When 用 `_migration_steps` 同款正则抽取三片段（备份 / 建目录根 / 装版本）
- Then 各入口三片段**逐一相等**；`test_debt0034_migration_steps_consistent_across_entries` 与 `test_debt0034_install_sh_heredoc_is_guarded` **保留并扩展**到新增入口（这两个测试守护的是"迁移提示文案"，属保留项，不因删 legacy 而删除）

#### BDD-36: 迁移三步在隔离环境真实可走通
- Given 【隔离】+ 软链 `~/.agate` → 含旧 checkout 的 `agate/` 目录；本地 `file://` 上游
- When 依次执行文案中的三步：`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions`
- Then 三步均 exit 0；结果满足 BDD-29 的版本根结构；`agate-resolve.py` exit 0；`~/.agate.bak`（原软链）保持完好（可回滚：`rm -rf ~/.agate && mv ~/.agate.bak ~/.agate` 后回到软链态）

#### BDD-37: 全仓 grep 断言——legacy 残留复发拦截（判据 10）
- Given 一个新增的**永久回归测试**（放 `agate/tests/regression/`；自身文件排除在扫描外）；扫描范围 = `git ls-files`，排除**任意层级**的 `archived/`（含 `agate-workspace/archived/`）、`agate-workspace/tasks/`（历史任务产物不改）、`docs/reviews/`、`docs/design-notes/`（历史叙事）、`node_modules/`、`package-lock.json` 等 lock 文件；**大小写口径：不区分大小写**（`re.I`）；模式集（基线 S-18）：`use_legacy`、`legacy[ _-]?(软链|symlink|layout)`、`单软链`、`软链兜底`
- When 按上述范围与模式扫描
- Then ① `use_legacy` 全范围命中 **0**（唯一例外：`agate-workspace/debt/tech-debt.md`，已 closed 债务叙事）；② 其余模式的命中文件集合 ⊆ **白名单 W**（下列 12 项，测试内以 `(路径, 理由)` 列出，新增白名单项须显式改测试）；③ 现状（HEAD 75a8102，按本 BDD 的范围与模式**实扫**）命中 23 个文件，落地时**必须**达到：R 集合 12 个文件**清零**（改写，已在 BDD-39 / BDD-40 列为改写对象），W 集合内文件可保留命中；④ 判据 10 的原口径 `grep -rn "use_legacy\|legacy 软链布局"` 在非 W 处无残留
  - **W 白名单（12 项）**：(a) 历史 / 叙事：`CHANGELOG.md`（append-only 发布记录，含 v0.73.0 BREAKING 条目）、`agate/UPGRADING.md`（v0.73.0 迁移节 + 历史版本节，按小节标题界定）、`agate/adr.md`（ADR-009 历史条目 + "已被 v0.73.0 取代"注记）、`agate-workspace/debt/tech-debt.md`（closed 债务叙事）；(b) fail-closed 迁移文案的承载文件（**有限枚举**，其余代码文件不得含旧称）：`install.sh`、`agate/scripts/agate-install.py`、`agate/scripts/install-offline.py`（预登记，现状无命中）、`agate/scripts/agate_common.py`、`agate/scripts/agate-resolve.py`、`agate/scripts/agate-summary.py`；(c) 断言 fail-closed 的测试（场景名 / 注释可含旧称）：`agate/tests/unit/test_agate_version_install.py`、`agate/tests/unit/test_agate_version_resolve.py`
  - **R 清零集合（12 项，现状均有命中，须改写）**：`AGENTS.md`（根，`:62` 历史句改为"本机于 2026-09-18 由旧软链布局迁移"，不含旧称）、`README.md`、`README.zh-CN.md`、`agate/AGENTS.md`（`:4`、`:104` 卸载节）、`agate/SETUP.md`、`agate/WORKFLOW.md`（`:41`）、`agate/orchestrator-template.md`（`:20`）、`agate/platform-notes.md`（`:250` 末句"与单软链时代一致"，**指针软链机制的描述保留**，仅去旧称）、`agate/scripts/README.md`、`agate/tests/unit/test_dsh_preset.py`（`:222` 注释）、`docs/guides/project-map.md`（`:114`）、`docs/guides/worktree-dogfooding-guide.md`

#### BDD-38: 4 个真 legacy 测试按"改写 / 删除"精确处置，撞名测试零误伤
- Given 4 个目标测试：`test_bdd_30_legacy_symlink_direct_root`、`test_debt0042_agate_home_legacy_symlink`（测的是"软链**可**解析"→ 与新语义相反）、`test_tag0032_bdd_1_legacy_symlink_install_fail_closed`、`test_tag0032_bdd_2_legacy_symlink_rejection_migration_hint`（fail-closed 语义保留，见 BDD-32）；以及**撞名的** `bdd_30` 系列（`spawn_agent` / quoted node ids / formatter 等，与 legacy 无关）
- When 完成删除 / 改写
- Then ① 前两者被**改写为 fail-closed 断言**（对应 BDD-27）或删除，其 `legacy` 直通解析断言不复存在；② 后两者保留实质断言；③ 以名字前缀 `test_bdd_30` 匹配的全部测试：**除上述 `test_bdd_30_legacy_symlink_direct_root` 外**，其余每一个的函数体在本任务 diff 中**零改动**（对 `git diff` 逐函数核对）；④ `test_upgrading_lifecycle.py::test_tag0032_bdd_10_*` 中 `"git pull" in sec` / "legacy 布局" 的断言（**P0-brief 未列，读测试发现**）随 UPGRADING 对照表去 legacy 列而改写：版本布局侧的 `agate-install latest` + `幂等` 断言保留

#### BDD-39: 文档面 legacy 表述改写完成（UPGRADING / README / SETUP / WORKFLOW / adr / AGENTS / project-map / dogfooding 指南）
- Given `agate/UPGRADING.md`、`README.md`、`README.zh-CN.md`、`agate/SETUP.md`、`agate/WORKFLOW.md`、`agate/adr.md`、`agate/AGENTS.md`、根 `AGENTS.md`、`agate/scripts/README.md`、`agate/platform-notes.md`、`docs/guides/project-map.md`、`docs/guides/worktree-dogfooding-guide.md`
- When 逐处核对
- Then ① UPGRADING「安装 / 迁移 / 更新 / 回退对照表」不再有 legacy 列（单布局表，含"迁移"行写迁移三步）；② 解析优先级表**无第 5 行**，文字口径为「三层：env（`AGATE_ROOT` > `AGATE_HOME`）→ 项目声明 → current」；③ `:809` 区的「存量单软链用户行为不变（红线，BDD-30）」承诺**改写**为"legacy 已移除（v0.73.0 BREAKING）+ 迁移指引"，`:841` 同步；④ 新增 `### v0.73.0` 节：标注 **BREAKING**，写明影响面（仅 legacy 软链用户；已知存量 1 = 本机已迁移）、迁移三步、`install.sh` 无参语义变更、`AGATE_REPO_DIR` / `AGATE_SYMLINK` 废弃、Release / portable 新增；⑤ 历史版本节（v0.50.0 / v0.69.0 等）**原文保留**，§3 顶部加一行注记"v0.73.0 起 legacy 软链布局不再支持，下列历史节中软链布局表述仅作历史记录"（`[SUGGEST: S-18]`）；⑥ README / README.zh-CN 首推装法改为版本管理布局（`curl \| bash` 仍写，语义注明为进入版本管理布局）；⑦ 其余文件的 legacy / 单软链表述改为版本布局叙述或历史注记；⑧ `test_agate_version_resolve.py:3` 头注与 `test_resolve_terminal_failure_fail_closed` docstring 的 legacy 字样、`test_dsh_preset.py:222` 注释的「单软链」字样同步更新；⑨ BDD-37 的 R 清零集合（12 个文件）全部达成 0 命中

#### BDD-40: 「`~/.agate` 当协议根」的遗留路径全部改为解析出的根
- Given 三处遗留：`agate-summary.py` 启动建议 `读 ~/.agate/AGENTS.md`；`agate/assets/templates/handoff-template.md` 的 `~/.agate/orchestrator-template.md`；`agate/orchestrator-template.md:20` 的"脚本不可用则默认 `~/.agate`"
- When 在版本管理布局（隔离）运行 `agate-summary.py` 并检查两份模板文本
- Then 启动建议里的协议入口路径 == `<解析出的 AGATE_ROOT>/AGENTS.md` 且该文件存在；模板文本改用 `$AGATE_DIR`（或 `~/.agate/current/agate`），且 `orchestrator-template.md` 的 fallback 为 `~/.agate/current/agate`；grep `~/\.agate/(AGENTS|orchestrator-template|WORKFLOW|assets|phase-cards|rules)` 在非历史叙事文件中 0 命中

#### BDD-41: SETUP.md 的 `$AGATE_DIR` 取值去掉 legacy fallback（判据 11 前提）
- Given 【隔离】+ 版本管理布局（`~/.agate/current → latest → vX.Y.Z`）；`SETUP.md`「先取协议根路径」节
- When 提取该节的取值命令并在隔离 `HOME` 下执行
- Then 命令**不含** `|| echo "$HOME/.agate"` 式 fallback，结果 `$AGATE_DIR == $HOME/.agate/current/agate`，且 `$AGATE_DIR/orchestrator-template.md` 可读；布局对照表只剩版本管理一行；`current` 缺失时命令给出明确失败提示而非静默落到 `~/.agate`

#### BDD-42: Claude Code 接入（agate 侧命令）可二值验证（判据 11）
- Given 【隔离】+ 版本管理布局 + 临时项目目录；本 BDD **不调用 `claude` CLI**（其验证命令 `claude --agent orchestrator -p "echo test"` 是联网真实模型调用，需真实凭据，在隔离前提下不可确定，故不属 BDD，降为 P6 人工验收项 H-1，见 §6）
- When 按 SETUP「Claude Code」节命令：`mkdir -p .claude/agents` + `ln -sf "$AGATE_DIR/orchestrator-template.md" .claude/agents/orchestrator.md`（`$AGATE_DIR` 按 BDD-41 取值）
- Then 链接存在且目标可读（`test -r`）；目标文件首部 frontmatter 可被 `yaml.safe_load` 解析且含 `name: orchestrator`（SETUP 已记载的两类静默失败：frontmatter 解析失败 / 缺 `name`）；链接目标位于**隔离** `AGATE_HOME` 内；测试前后真实 `~/.agate` 内容哈希不变

#### BDD-43: OpenCode 接入命令实跑（判据 11）
- Given 版本管理布局与临时项目目录均在隔离 `tmp_path`（`AGATE_HOME` / `$AGATE_DIR` 指隔离布局）；`HOME` 保持真实**仅供 opencode 读自身配置**，命令不读不写真实 `~/.agate`（前后内容哈希不变）；`opencode` 在 PATH（**不在 PATH → 本 BDD 判 FAIL**：环境未就绪，走 verification_env 失败协议，不得记为通过或跳过）
- When 按 SETUP「OpenCode」节命令建 `.opencode/agents/orchestrator.md` 链接，再在项目目录跑 `opencode debug agent orchestrator`
- Then 命令 exit 0；输出可解析为 JSON 且 `mode == "primary"`、`tools.task == true`

[BASELINE_CHANGE: G-1 CI 例外（仅注解，不改 Given/When/Then）——BDD-43 仅在 GITHUB_ACTIONS=true 且 opencode 缺失时跳过；本地 / P5 / P6 运行缺 CLI 仍判 FAIL。原因：GitHub runner 未预装该 CLI，且改 workflow 属本任务 out-of-scope；主 Agent 裁决已采纳。]

#### BDD-44: DSH 接入命令实跑（判据 11）
- Given 【隔离】`HOME` + 版本管理布局；DSH 无需真实安装（`dsh` 不在本机 PATH：只验证 agate 侧命令）
- When 按 SETUP「步骤 2-DSH」节命令：`mkdir -p ~/.dsh/.agent-presets/agate ~/.dsh/skills/agate-protocol` + 三条 `ln -sf "$AGATE_DIR/assets/templates/dsh/…"`（既有 `test_dsh_preset.py` 已锁字面命令，保持通过）
- Then 三个链接均存在且目标 `test -r` 为真；随后 `agate-summary.py` exit 0 且无"DSH 安装产物漂移"警告

#### BDD-45: Codex 接入命令实跑（判据 11）
- Given 版本管理布局在隔离 `tmp_path`（`$AGATE_DIR` 按 BDD-41 取值）；`HOME` 保持真实**仅供 codex 读自身配置**，命令不读不写真实 `~/.agate`（前后内容哈希不变）；`codex` 在 PATH（**不在 PATH → 本 BDD 判 FAIL**：环境未就绪，走 verification_env 失败协议，不得记为通过或跳过）
- When 读取 `$AGATE_DIR/orchestrator-template.md`，并跑 SETUP「步骤 2-Codex」的验证命令 `timeout 60s codex features list`
- Then 模板可读；命令 exit 0 且输出含 `multi_agent` 行，该行状态值为 `stable` 或 `true`；（Codex 无 orchestrator 软链注册步骤，本 BDD 验证 legacy fallback 移除后协议根取值与 Codex 接入链路无回归；不执行需登录 / 联网的 `codex exec`）

[BASELINE_CHANGE: G-1 CI 例外（仅注解，不改 Given/When/Then）——BDD-45 仅在 GITHUB_ACTIONS=true 且 codex 缺失时跳过；本地 / P5 / P6 运行缺 CLI 仍判 FAIL。原因：GitHub runner 未预装该 CLI，且改 workflow 属本任务 out-of-scope；主 Agent 裁决已采纳。]

#### BDD-46: out-of-scope 文件零 diff（负向）
- Given 本任务全部提交
- When 对 hook 三件套（`agate/scripts/pre-commit-gate.{sh,py}` / `commit-msg-self-gate.{sh,py}` / `pre-push-gate.{sh,py}`）、`resolve-entry.py` 的 gate 映射与 exec 语义、SELF-GATE 机制（`SELF-GATE.md`、`commit-msg-self-gate.py` 的 `_SELF_GATE_RE`）、`.state.yaml` schema、`agate/rules/*.yaml` 权威源、`install-hook.py` 的 `AGATE_HOME` 语义执行 `git diff 75a8102..HEAD`（基线写死为 P1 启动时的 HEAD `75a8102`，即本任务分支自 main 分出后的首个基线）
- Then 上述文件 diff 为空（**例外**：`resolve-entry.py` / `agate_common.resolve_hook_root` 的注释与 docstring 中 legacy 字样可改，函数语义不变）；`install-hook.py` 层次差别（协议根 vs 版本根基址）仅在 UPGRADING 文档点明

#### BDD-47: hook 解析路径不受 legacy 删除影响
- Given 【隔离】+ 版本管理布局 + 已装 hook（`install-hook.py`，走既有测试夹具）；另 worktree dogfooding 场景（hook 软链指向稳定版脚本、`AGATE_ROOT` 未设）
- When 运行既有 `test_hook_resolve_entry.py` / `test_pre_commit_hook.py::test_agate_root_self_locate_worktree` 与 commit 触发 gate
- Then 全部保持通过；`resolve_hook_root` 的**脚本路径上溯 + `.agate-root` 复制模式恢复**兜底保持（`[SUGGEST: S-17]`：这是 hook 自定位契约、dogfooding 依赖，**不属于** legacy 软链布局支持，故不随 E 删除；仅清理其 docstring 中的"软链 readlink 上溯"legacy 措辞）

#### BDD-48: 全量 pytest 不减反增，测试计数对账
- Given CI 口径基线 **1842 passed / 2 skipped**（HEAD 75a8102）
- When `python3 -m pytest agate/tests/ --reruns 1 -n auto`（本机已装 `pytest-rerunfailures`）
- Then 失败数 0；`passed ≥ 1842`，`skipped ≤ 2`；**删除 / 改写对账**：P5 报告列出 (删除数 D, 新增数 A)，`A − D ≥ 0`（本任务预期：4 个真 legacy 测试均"改写"而非净删；新增 BDD-2/3/4/8/9/11/13~16/17/18/22~25/27/28/29~37/40/41/44/51/52 等对应用例）；`bash agate/tests/scripts/count-tests.sh` 计数已记录；`agate/tests/` 内若有含用例总数字面量的文档则同步（现状：`agate/tests/` 内文档无静态总数字面量，grep `1842` 无命中，仅需确认无新增漂移）

#### BDD-49: consistency 0 ERROR + ruff 0 error + shellcheck
- Given 本任务全部改动（含新增 workflow、新增脚本、`install.sh`）
- When ① 用 **worktree 自己的** `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`；② `~/.venvs/agate-dev/bin/ruff check agate/`（CI 锁 0.16.4）；③ `shellcheck -S warning install.sh agate/scripts/*.sh`；④ 新增脚本已登记 `agate/scripts/README.md` 脚本索引与测试映射（CHECK 对脚本引用完整性）
- Then ① 0 ERROR；② 0 error；③ 0 warning/error；④ 索引齐全

#### BDD-50: 发布物齐全，版本号为 v0.73.0，破坏性变更如实标注
- Given P8 发布清单（AGENTS.md「版本发布清单」）
- When 检查发布相关文件
- Then ① README version badge、`CHANGELOG.md`（`[Unreleased]` → `[0.73.0]`，含 **BREAKING** 标注与迁移指引指针）、`agate/UPGRADING.md`（`### v0.73.0` 节，BDD-39 ④）三处版本一致；CHECK 7（badge vs tag）与 CHECK 13（CHANGELOG 最新版本 ↔ UPGRADING 章节）通过；② **不 bump 1.0**（用户裁决）；③ PR 描述如实列出 release workflow 的触发条件（`on: push tags v*`）与权限（`permissions: contents: write`）（CI 改动许可范围），并列出 BDD-20 实测到的、被 tag push 连带触发的现有 workflow；④ 本任务 `roadmap.md` RM-AG0066 回写 `done`（P8 gate 硬校验 RM-AG0043）；⑤ HANDOFF-TAG0037.md 归档到 `agate-workspace/archived/plans/`（P8 收尾，已三次被漏）；⑥ P8 后验：v0.73.0 正式 tag 推送后 `gh release view v0.73.0` 含 3 个资产（本体 + 两平台 offline，BDD-21），首次真实运行成功

[BASELINE_CHANGE: BDD-50 P6 验收范围口径（仅注解，不改 Given/When/Then）——② 版本号 bump、`[Unreleased]`→`[0.73.0]` 重命名、tag、④ roadmap 回写、⑤ HANDOFF 归档、⑥ 正式 Release 资产、③ PR 描述均属 P8/发布时事实，P6 阶段不可能已发生。故 BDD-50 在 P6 的验收范围 = 发布前就绪度：`agate/UPGRADING.md` 存在 `### v0.73.0` 节且标注 BREAKING 与迁移三步、`CHANGELOG.md [Unreleased]` 已含本任务条目与 BREAKING 标注及 UPGRADING 指针、README badge 不为 1.0、release workflow 触发（`on: push tags v*`）/权限（`contents: write`）可如实列出（引用 release.yml 静态事实）；②–⑥ 的最终事实在 P8 复验并写入 P8-release.md。依据：主 Agent 决策，验收人 P6 g2 verifier 据此判定。]

### 4.6.1 评审修订追加（retry #1；编号追加在末尾，不改既有编号）

#### BDD-51: 软链基址但目标是完整版本根（含有效 `current` 链）时的确定行为 [参数化]
- Given 【隔离】+ `AGATE_HOME` 是**软链** → 一个**完整版本根**（含 `vX.Y.Z/agate/`、`latest → vX.Y.Z`、`current → latest`；即用户把版本根软链到别的磁盘）；未设 `AGATE_ROOT`
- When ① `agate-resolve.py`；② `agate-install.py latest`
- Then ① exit 0，`AGATE_REASON=全局 current`，`AGATE_ROOT` 为目标内 `vX.Y.Z/agate`（**放行**：被删除的只是"把软链目标直接当协议根"的分支，经 `current` 链正常解析的软链基址不是 legacy 布局；与 BDD-27 的"目标是协议本体目录、无 `current`"夹具互不矛盾）；② exit 1 并按 BDD-32 拒绝（**安装侧对任何软链基址一律拒绝**，沿用 TAG0032 既有行为，因安装器无法区分"旧布局"与"被软链的版本根"），stderr 的迁移三步文案同时说明"若 `~/.agate` 是指向完整版本根的软链，解析仍可用，仅安装类命令需先改为实体目录或对软链目标直接执行安装"

#### BDD-52: 排除 `agate/tests/` 后包内脚本冒烟：缺目录时无 Traceback
- Given 【隔离】+ 按 BDD-2 基线值生成的本体包解出的目录树（**不含** `agate/tests/`）作为 `AGATE_ROOT`
- When 在该树内运行：`check-platform-assumptions.py`（无参，默认扫描 `agate/tests/`）、`agate-risk-score.py`（无参）、`agate-summary.py`、`agate-resolve.py`
- Then 四者输出均**不含 `Traceback`**；退出码落在各自既有契约内（`check-platform-assumptions.py` 非 0 且输出含 `目标不存在` 的明确报错——实测其在缺目录时已是 `FATAL: 目标不存在`；`agate-risk-score.py` 按其既有 `git_ok: false` 降级输出；`agate-summary.py` / `agate-resolve.py` 为 0）；hook 主链路（`resolve-entry.py` → gate 脚本）不读取 `agate/tests` 与仓库根 README / pyproject（读码核实，评审 m-11 已确认）

### 4.7 完成判据 ↔ BDD 映射（P0-brief 11 条）

| 判据 | 内容 | BDD |
|------|------|-----|
| 1 | 结构契约成文 + 本体精确边界清单（可机械验证） | 1、2、3 |
| 2 | 三条路径产出同一结构 | 4（另 10、16、17 补路径细节） |
| 3 | P0 修复：离线安装后解析成功（真实 pack 产物结构） | 9（另 12） |
| 4 | `_make_bundle` 反映真实布局（防同源假设复发） | 11 |
| 5 | Release 自动创建 + assets 可下载（CI 测试 tag 实跑） | 13、14、15、16、20、21 |
| 6 | portable 不依赖 git（无 git 环境验证；不宣称零依赖） | 17、18、19 |
| 7 | 在线只装本体，冗余量化下降 | 22、23（另 24、52） |
| 8 | 已装旧形态仍可解析（独立 BDD） | 5、6、7 |
| 9 | Full pytest + consistency 0 ERROR | 48、49 |
| 10 | legacy 软链支持彻底删除；全仓 grep 无残留；解析链仅三层 | 27、28、36、37、38、39（另 51、29~35、40） |
| 11 | 4 平台接入保持正常 | 41、42、43、44、45 |

## 5. 同类扫描（强制节）

> 扫描口径：`git` 工作副本（HEAD 75a8102）；通用排除 `--exclude-dir=.git --exclude-dir=archived --exclude-dir=node_modules --exclude-dir=__pycache__`；"本任务目录"（`agate-workspace/tasks/TAG0037-*`）自身命中不计。逐条判定 **处理 / 不处理 + 理由**。

### 扫描 A — `use_legacy`

命令：`grep -rnIE 'use_legacy' . <通用排除>`。**命中 9 行 / 5 文件**（不含本任务目录；含本任务 P0-brief 引用则为 dispatch 所述 11 行 / 6 文件，差异仅是 P0-brief 自身引用）。

| 文件 | 命中 | 判定 |
|------|------|------|
| `agate/scripts/agate_common.py`（`:182` 参数、`:219` 分支、`:231` `use_legacy=True`、`:243` `use_legacy=False`） | 4 | **本次处理**——**唯一代码面**（BDD-28）；`:243` 是 `resolve_hook_root` 传 `False`，删参数后此调用同步简化 |
| `agate-workspace/debt/tech-debt.md:1466` | 1 | **不处理**——已 closed 的历史债务叙事（DEBT0042 note），BDD-37 白名单登记 |
| `agate-workspace/tasks/TAG0022/P4-progress.md`、`TAG0032/P2-progress.md`、`TAG0032/P7-consistency.md`（×2） | 4 | **不处理**——历史任务产物，只读 |

**结论**：代码面确认**只此一处**（`agate_common.py`）；其余为历史记录。回归拦截：BDD-37。

### 扫描 B — `legacy`（大小写不敏感，文件级）

命令：`grep -rliIE 'legacy' . <通用排除>`。**命中 140 文件**（不含本任务目录；写作时快照；评审自扫得 136，差 4 为本机 worktree 口径差异，不影响分类结论），分布：`agate/` 协议本体 14、`agate/tests/` 15、`docs/` 7、根文件 6（`AGENTS.md` `CHANGELOG.md` `HANDOFF-TAG0037.md` `install.sh` `README.md` `README.zh-CN.md`）、`site/package-lock.json` 1、`agate-workspace/tasks/`（历史）95、`agate-workspace/` 其他 2。

**语义分类**（关键：多数命中的 "legacy" **不是**指软链布局）：

| 类别 | 文件（举例） | 判定 |
|------|-------------|------|
| **软链布局 legacy**（本任务对象） | 协议本体：`agate_common.py`、`agate-install.py`、`agate-resolve.py`、`agate-summary.py`、`scripts/README.md`、`SETUP.md`、`UPGRADING.md`、`WORKFLOW.md`、`adr.md`、`AGENTS.md`、`orchestrator-template.md`（共 11）；测试：`test_agate_version_install.py`、`test_agate_version_resolve.py`、`test_upgrading_lifecycle.py`、`test_version_lifecycle_e2e.py`（注释）、`test_dsh_preset.py`（注释）；根：`install.sh`、`README*`、`AGENTS.md`、`CHANGELOG.md`；`docs/`：`project-map.md`、`worktree-dogfooding-guide.md` | **本次处理**（BDD-27~40）；`CHANGELOG.md` 历史条目**不改**（append-only 发布记录） |
| **其他含义的 "legacy"**（与软链无关） | `agate-migrate-workspace.py`（"legacy docs/tasks layout"）、`check-events.py`（`judge_verdict_legacy`）、`pre-commit-gate.py`（legacy 任务）、`conftest.py`（`legacy_fields`）、`test_agate_inject_card` / `md_field_set` / `check_gate*` / `check_maintainability` / `check_mvwu` / `check_pruning` / `retrospective_protocol_docs` / `migrate_workspace`（旧格式 / 旧字段 / 旧回顾） | **不处理**——同名不同义；误改会破坏其它机制。BDD-37 的模式限定 `legacy[ _-]?(软链\|symlink\|layout)`，不误伤 |
| 历史叙事 | `docs/design-notes/doc-consistency-audit-2026-09.md`、`docs/reviews/*`（4）、`agate-workspace/roadmap/roadmap.md`、`debt/tech-debt.md`、`tasks/**`（94） | **不处理**——历史 / 叙事；`roadmap.md` RM-AG0066 行在 P8 回写 done |
| 无关 | `site/package-lock.json` | **不处理** |

### 扫描 C — 同义词：`单软链|软链布局|软链兜底|legacy 软链`（本任务新增的关键扫描）

命令：`grep -rlIE '单软链|软链布局|软链兜底|legacy 软链' . <通用排除>` 且排除 `agate-workspace/tasks/`。**命中 27 文件**，其中**只含"单软链 / 软链布局 / 软链兜底"而不含 `legacy` 字样**的有：`agate/SETUP.md`（`:5/:17/:28`）、`agate/WORKFLOW.md:41`、`agate/AGENTS.md:4/:104`、`agate/platform-notes.md:250`（末句"与单软链时代一致"为旧称，**本次处理**——R 清零集合，BDD-37；同段对 latest / current **指针**软链机制的描述保留）、`agate/scripts/agate-summary.py:152`、`agate/adr.md`（多处）——**P0-brief 判据 10 的 grep（`use_legacy\|legacy 软链布局`）会全部漏掉它们**。→ 已提升为 BDD-37 的模式集；`agate/platform-notes.md:250`（latest / current **指针**是软链）与 `test_agate_summary.py` 的软链指针用例**不处理**（指针机制保留，非 legacy 布局）。

### 扫描 D — `islink|os.symlink|readlink|[ -L`（软链检测代码面）

命令：`grep -nE 'os\.path\.islink|os\.symlink|os\.readlink|is_symlink|\[ -L ' agate/scripts/*.py agate/scripts/*.sh install.sh`。命中 → 判定：

| 位置 | 判定 |
|------|------|
| `agate_common.py:219` `use_legacy and islink(base)` | **本次删除**（BDD-28） |
| `agate_common.py:139-141` `_resolve_pointer_chain` 的 `islink` + `readlink` | **保留**——指针链解析（current / latest 软链），与 legacy 无关 |
| `agate-install.py:336` `islink(agate_home)` fail-closed | **保留并沿用**（BDD-32），文案改为"软链布局已不支持" |
| `agate-install.py:107/131-132` 指针写入 / 解析 | 保留（指针机制） |
| `install.sh:20` `[ -L "$AGATE_VER_ROOT" ]` fail-closed | **保留**，扩展到无参入口（BDD-31） |
| `install.sh:64-79` 无参建软链分支 | **本次删除**（BDD-29） |
| `install-offline.py:235-237` `current` 软链创建 | 保留（改为 `current → latest`，BDD-10）；**缺软链守卫，新增**（BDD-33） |
| `install-hook.py`（hook 软链 / 复制模式）、`check-platform-assumptions.py` | **不处理**——hook 软链与平台扫描，不属版本布局 |

### 扫描 E — 四条安装路径逐个核对产出结构（+ 是否有未列入 P0-brief 的路径 / 形态）

| 路径 | 现状产出（读代码 / 复现） | 处理 |
|------|--------------------------|------|
| ① `install.sh` 无参 | `~/.agate` → `<clone>/agate` 软链；`AGATE_REPO_DIR` / `AGATE_SYMLINK` | **改为进版本布局**（BDD-29/30/31） |
| ② `install.sh --versions` | 克隆 `repo/` → `exec agate-install.py latest` | 保留为别名（BDD-29）；软链守卫保留（BDD-31） |
| ③ `agate-install.py`（无参 / `latest` / `vX.Y.Z`） | `git worktree add --detach vX.Y.Z <tag>` 整仓树；`latest`/`current→latest`；`_sync_root_scripts` | **改为只装本体**（BDD-22/24）；指针 / 根 scripts 语义保留 |
| ④ `agate-pack-offline.py` → `install-offline.py` | pack：`git worktree add <bundle>/agate <tag>`（整仓根，且带 `.git` 指针文件被一并复制进 vdir）；install：`_copy_tree(bundle → vX.Y.Z/)`（含 `wheels/`、`manifest.json`、`.installed-version`）→ **复现确认**：`git archive v0.72.0` 检出到 `bundle/agate` 后复制，`_protocol_root` 返回 vdir 原样（解析失效）；另 4 处分叉见隐含需求 2 | **BDD-9/10/11/12/33** |
| **未列入 P0-brief 的路径**（本次核对结论） | `agate-install.py` **无** `update` / `rollback` 子命令（回退 / 更新靠文档中的 `latest` + `ln -sfn`）——**已确认没有遗漏的安装路径**；`--uninstall`（BDD-25）与 `--check`（BDD-18）是既有子命令，受契约影响已纳入；`agate-summary.py` 版本显示（BDD-34/40）；`install-hook.py`（不动，BDD-46）；**新增第五条：portable tarball 手工安装**（BDD-17，本任务产物，非既有） | 已纳入 |

### 扫描 F — `_protocol_root` 调用方与同类探测（避免又造第二份）

命令：`grep -rn '_protocol_root\|vdir/scripts\|agate/scripts"' agate/scripts install.sh`；`grep -rn 'ENTRY_ROOT\|\.agate-root\|realpath\|readlink' agate/scripts`。

| 位置 | 性质 | 判定 |
|------|------|------|
| `agate_common._protocol_root`（`:166`） | **权威实现** | **不改**（BDD-6） |
| `agate_common._resolve_version_info`（`:207/:216`，两处调用） | 调用方 | 保留 |
| `agate-install.py:37-45` 降级副本 | **第二份实现**（pyyaml 缺失时 `--check` 仍需运行，`import agate_common` 会 `sys.exit(1)`，故有意重复；源码注释已声明） | **保留但加一致性拦截**（BDD-8）——TAG0031 hash 双实现先例的教训是"合并"，此处**不能**合并（`--check` 需零依赖启动）→ 退而求"行为一致性测试锁定" |
| `agate-install.py:319` `_sync_root_scripts` 调用 | 调用方 | 保留 |
| `resolve-entry.py`、`agate-resolve.py`、`agate-summary.py`、`install-offline.py` | 均**不**重复探测（分别经 `resolve_hook_root` / `resolve_version_root` / 无） | **已确认只此一处 + 一处降级副本**，无第三份 |
| `pre-commit-gate.sh` 等 3 个 hook 薄壳的 `ENTRY_ROOT` 自定位 | **入口根**自定位（`readlink -f`），非协议根探测 | **不处理**（out-of-scope hook 三件套） |
| `agate_common.resolve_hook_root` 的脚本路径上溯 + `.agate-root` 恢复 | hook 自定位契约（dogfooding 依赖） | **保留**（BDD-47，`[SUGGEST: S-17]`）——不是 legacy 布局支持 |

### 扫描 G — 版本引用 / 权威源文档面（`~/.agate` 用法逐处判定）

- `agate/UPGRADING.md`「版本管理生命周期」节（`:40-160`）：**权威源**——对照表 legacy 列（`:48-55`）、解析表第 5 行（`:113`）→ 改（BDD-39）；「路径层次」图 `:95` 与"整仓形态下协议根为 `<版本目录>/`"一句（`:103`，与真实 `_protocol_root` 语义不符：整仓形态实为 `vdir/agate`）→ **一并订正**；新增契约小节（BDD-1）与 portable 小节（BDD-17）。
- `agate/SETUP.md`：`:5/:13-28`（两布局表 + `$AGATE_DIR` fallback）→ 改（BDD-41）；四平台小节（Claude Code `:97`、OpenCode `:114`、DSH `:165`、Codex `:196`）**逐节核对**：前三者用 `$AGATE_DIR`，Codex 无软链注册步骤 → BDD-42~45；`:354` 更新口径 → 改。
- 其余 `~/.agate/scripts/...` 用法（SETUP `:47/:75/:76/:179/:272/:308/:314/:315`、README 快速上手）：**版本布局下有效**（根 `scripts/` 副本），**不改**——但离线路径此前缺根 scripts 副本致其失效（BDD-10 补齐）。
- `docs/design-notes/dsh-integration.md:103` 的 `~/.agate/orchestrator-template.md`：历史设计笔记，**不处理**。
- `README*` / `site/index.md` / `site/zh/index.md` / `SiteFooter.vue` 的 `curl \| bash`：**命令本身保持有效**（语义变为进入版本布局，BDD-29），站点 / README 说明文字随 BDD-39 修订；`site/` 博客文章（含"安装就是一个软链"的历史文章，如 `20260827/post-02-agateon-intro.md`）为**带日期历史文章，不改**——`site/` 不在 P0-brief scope。

### 扫描 H — 同源假设（测试假 bundle）全仓

命令：`grep -rln 'install-offline\|pack-offline\|pack_offline\|install_offline' agate/tests`。**3 处**同源假设（不是 dispatch 所述 1 处）：`test_install_offline.py::_make_bundle`、`test_agate_pack_offline.py::_fake_artifacts_side_effect`、`regression/test_offline_bundle_roundtrip.py::_fake_pack_artifacts`——**全部本次处理**（BDD-11）。`.installed-version` 的断言分布于其中 3 处（`test_install_offline.py:135/227`、`test_offline_bundle_roundtrip.py:146`）：该文件**无生产读取方**，契约登记方式见隐含需求 9。

### 扫描 I — 本次**不处理**的同类观察（附理由；建议进 roadmap）

| 观察 | 理由 | 去向 |
|------|------|------|
| `agate-changes.py` 依赖 agate git 仓库（`_find_git_root` 要求含 `.git` **目录**）——在 worktree 版本目录（`.git` 是文件）与 portable 安装下均 exit 1 | **既有缺陷**（整仓 worktree 形态下已不可用），非本任务引入；portable 只需**文档如实声明**（BDD-19） | 建议 backlog（一条 DEBT） |
| offline bundle 固定 `pip download --python-version 311` → wheel 绑定 CPython 3.11 ABI，其它版本内网机装不上 | 既有限制，不在 P0-brief scope；Release notes 如实写明"offline asset 面向 Python 3.11" | 建议 backlog |
| `agate-install.py latest` 改为"从 Release asset 取包"（roadmap 拟议模型第 2 项） | P0-brief 子批 C / D **未含**，用户决策 ② 保留 tag 安装路径；本任务只交付 asset，不改在线取包源 | 建议 backlog（RM 追加）；**不写 `[SCOPE+]`**——未越界，仅未做 |
| `SETUP.md` 中 Windows / 复制模式与 legacy 无关内容 | 无关 | — |

### 扫描 J — 回归拦截手段汇总（"立规则须有机械验证"）

| 规则 | 拦截手段 | BDD |
|------|---------|-----|
| legacy 残留复发 | 全仓 grep 断言测试 + 显式白名单 | 37 |
| 版本目录结构契约 | 装后目录结构比对（三路径同构 + F_pkg 逐项）+ 文档 ↔ 来源单一来源测试 | 2、3、4、22 |
| 同源假设复发（假 bundle） | 真实 pack 入口 + sentinel + 红灯回放 | 9、11 |
| `_protocol_root` 双实现漂移 | 行为一致性测试 | 8 |
| 探测序被颠倒 | 既有用例不改 + 新增优先级用例 | 6 |
| 迁移文案多入口漂移 | `_migration_steps` 跨入口比对 | 35 |
| tag 与 Release 失配 | 发布清单含 Release 校验 + P8 后验 | 21、50 |
| workflow 越权 | YAML 解析静态断言（触发 / 权限 / 第三方 action） | 13 |

## 6. 环境与能力声明

```yaml
capability_requirements: []
# 无 agent 侧能力缺口：本任务无 frontend / 视觉需求；所需外部工具均为环境项（见 verification_env），走 verification_env 而非 supplementable。

verification_env: |
  全部安装机制验证在隔离 AGATE_HOME + HOME=tmp_path 下进行，严禁读写真实 ~/.agate；
  版本源用本地 file:// git 上游（AGATE_REPO_URL）；无 git 场景用受限 PATH 目录；
  真实 pack 的 git 步骤真实执行，仅 pip download / pip install 的网络与环境副作用调用可 stub；
  BDD-20 需 gh 已登录（已实测：github.com 账号 randomgitsrc 已认证）+ 用户当次许可推测试 tag；
  BDD-43/45 需 opencode / codex 在 PATH（本机均已实测存在）：在 PATH 则必须判 PASS，不在 PATH 则该 BDD 判 FAIL（环境未就绪，走 verification_env 失败协议，无第三态）；其 HOME 保持真实仅供 CLI 读自身配置，AGATE_HOME / $AGATE_DIR 指隔离布局，真实 ~/.agate 前后内容哈希不变；
  BDD-42 不调用 claude CLI（agate 侧命令 + frontmatter 静态断言）；
  DSH CLI 本机无，BDD-44 仅验证 agate 侧链接命令。
verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；轮次追踪由主 Agent 在 dispatch-context 记录"
```

- **P6 人工验收项 H-1（非 BDD，不计入 PASS/FAIL 总数，P6 单独留证）**：真实 `claude --agent orchestrator -p "echo test"`。该命令是联网真实模型调用，使用**真实 HOME 凭据**；仅将 `AGATE_HOME` / `$AGATE_DIR` 指向隔离布局、临时项目目录内建链接，**不写真实 `~/.agate`**；期望：能选中 orchestrator 并返回、不报 `Failed to parse agent`。结果与输出记入 P6 证据。
- **judge**：`.state.yaml` 已含 `judge.enabled: true`（RM-AG0039 强制），确认满足。
- `[PROD_NOT_TOUCHED]`：本阶段只读探测（`du`、`gh` 只读 API、`git archive` 到 scratchpad 复现 P0 机理），未写入真实 `~/.agate`。

## 7. 倾向项汇总（本轮修订按评审 m-1 已把 S-1…S-6、S-8…S-19 的推荐值转写为 P1 基线值——BDD / T-1 中不再出现"推荐 / P2 定案"的浮动值，仅**实现机制**留给 P2；S-9 已按 M-2 更正。均**不阻塞**；`suggest_resolved` 因 `agate-md-field-set` 不接受该键，请主 Agent 采纳时补写）

**边界清单（用户显式委托 P1 给推荐 + 理由）**

- [SUGGEST: S-1 推荐 `agate/tests/` 排除出本体包，理由：使用者无需跑 Agateon 自身测试（platform-notes.md:181 已声明）；占本体 48.6%（1.61MB/3.31MB，v0.72.0 实测）；依赖 tests 的维护者工具（check-protocol-consistency / check-platform-assumptions）本就以仓库根为检查对象、在包内不可用；代价是包内文档对 `agate/tests/README.md` 的引用（agate/AGENTS.md:35、CONTEXT.md、platform-notes.md）成为断链——须在这几处加"仅仓库开发者可用"注记，包内文档对包外路径既有 ~122 处引用（45 文件，多数指用户项目侧路径）不构成新回归]
- [SUGGEST: S-2 推荐 `agate/AGENTS.md` 入包，理由：它是协议本体入口指引，agate-summary 每会话启动提示与 SETUP 均引用；与仓库根开发者指引 AGENTS.md 是两个文件，后者排除]
- [SUGGEST: S-3 推荐 `LICENSE` 与 `NOTICES.md` 入包并登记为 `vX.Y.Z/` 顶层文件，理由：MIT 要求所有副本含版权与许可声明，Release 二次分发的 tarball 不带即违反自身许可；role-system.md:249 引用 NOTICES.md。这会把 P0-brief 的"`vX.Y.Z/` 唯一内容 = agate/"精确化为"agate/ + 已登记根级许可/变更文件"，属 P0 委托 P1 定夺的边界待定项，非范围扩张]
- [SUGGEST: S-4 推荐 `CHANGELOG.md` 入包（`vX.Y.Z/` 顶层），理由：agate-summary.py 每会话启动提示读取 `<root>/../CHANGELOG.md`（162KB），整仓形态下原本存在；排除会使该提示静默指向死路，属可见回归]
- [SUGGEST: S-5 推荐 `README*` `pyproject.toml` `SELF-GATE.md` 根 `AGENTS.md`/`CLAUDE.md` `install.sh` `HANDOFF-*.md` `.gitignore` `.gitattributes` 排除，理由：仓库门面 / 开发配置 / 维护者指引，运行面无依赖；使用者文档已在 agate/UPGRADING.md 与 agate/SETUP.md]
- [SUGGEST: S-6 推荐边界机制满足"默认拒绝"语义（未登记的新顶层内容默认不入包），理由：否则未来新增的顶层目录会静默漏进用户环境；该语义与具体排除机制（export-ignore / 显式清单 / git archive）无关，P2 只需选出能满足它的机制并比对其对 GitHub 自动 Source code 包的副作用（export-ignore 会影响所有 archive 消费者）]

**版本 / 数值**

- [SUGGEST: S-7 推荐版本号 v0.73.0（0.x minor bump，UPGRADING 标 BREAKING），理由：v0.72.0 已被 TAG0036 发布（tag、CHANGELOG、UPGRADING 均已存在），用户裁决"沿用 minor bump、不 bump 1.0"对应 v0.73.0]
- [SUGGEST: S-8 推荐冗余阈值 S ≤ 1.25×B（冗余 ≤ 20%），理由：基线 91%（35.6MB vs 本体 3.28MB，即 10.9 倍；v0.72.0 上 B=1.86MB、上限 2.33MB）；允许 25% 余量吸收 pyc 目录项 / 少量登记元数据而不至于放过整仓形态；相对阈值随本体增长自适应，绝对阈值会随时间腐化]

**CI / 发布**

- [SUGGEST: S-9 推荐测试 tag 命名 `v0.73.0-tagtest.N`（匹配 `v*` 触发，但不匹配严格 `^v\d+\.\d+\.\d+$`，故 agate-install 的 `_VERSION_RE` 版本选择忽略它；**但 CHECK 7 / G-5 的 `git describe --tags --abbrev=0` 不做 semver 过滤、不忽略它**，故 BDD-20 必须先清理 tag 再跑 CHECK 7 / BDD-49），workflow 对非严格 semver 的 tag 自动 `--prerelease`，notes 走 BDD-14 ④ 的回落规则，资产名用 tag 名原样，验证后 `gh release delete --cleanup-tag --yes` 并核对 `gh release list` / `git ls-remote --tags` / `git describe` 零残留；tag push 会连带触发含 push 触发器的现有 workflow（须如实记入 PR 描述）；推 tag 属外部可见操作，执行前须取得用户当次许可；不许可时降级为本地全链路 + actionlint，并由主 Agent 提 BASELINE_CHANGE 显式记录，P8 后验 v0.73.0 首次真实运行]
- [SUGGEST: S-10 推荐 workflow 使用 runner 自带 `gh release create`、零第三方 action、触发器仅 `push.tags: v*`（不含 workflow_dispatch / PR 类），理由：`contents: write` 是高危权限，最小化供应链面与触发面；缺 workflow_dispatch 的代价是失败后补发靠本地脚本 + gh（已写入 BDD-21）]
- [SUGGEST: S-11 推荐 Release 附 `SHA256SUMS` 资产且打包脚本确定性（固定 mtime / 排序 / owner，同 tag 两次产物哈希相同），理由：tarball 完整性可校验、可复现；不作为本任务 BDD 二值条件，P2 可采纳或说明放弃理由]
- [SUGGEST: S-19 推荐 offline asset 覆盖 pack 现支持的两个平台（linux-x86_64、windows-x86_64），理由：agate-pack-offline 已支持两平台；`pip download --platform` 在 ubuntu runner 上可拉两平台 wheel]

**行为语义**

- [SUGGEST: S-12 推荐 `--check` 的 portable 口径为 opt-in 标志（如 `--check --portable`，P2 定名），默认口径不变，理由：`test_bdd_7/8` 锁定的既有语义（缺 git 即 exit 1）不动，仅在 portable 场景把 git 降为提示]
- [SUGGEST: S-13 推荐 install-offline 遇旧格式 bundle 拒绝并提示重新打包，不做自动归一化，理由：旧 bundle 安装后本就解析失效，拒绝比"装成半坏状态"更安全；归一化会为已损坏的历史格式永久背负兼容代码]
- [SUGGEST: S-14 推荐 install.sh 遇废弃环境变量 AGATE_REPO_DIR / AGATE_SYMLINK 时打印一行 WARNING 并忽略（不失败），理由：不静默忽略（避免"设了却没生效"）也不阻断已在 CI 里设置该变量的自动化]
- [SUGGEST: S-15 推荐 fail-closed 退出码统一为 1，理由：install.sh / agate-install.py / agate-resolve.py 现行 fail-closed 均为 1，2 保留给用法错误；改码会破坏依赖方与既有 test_tag0032_bdd_1 的语义]
- [SUGGEST: S-16 推荐不为已装的历史损坏离线安装（agate/agate/scripts 形态）增加第 3 探测序，理由：新契约形态就是既有探测序 2，`_protocol_root` 零改动最安全（红线）；本机无此形态实例（已知实例 0），受影响用户用新 bundle 重装即恢复（重装后 vdir/agate/scripts 命中探测序 2）]
- [SUGGEST: S-17 推荐保留 resolve_hook_root 的脚本路径上溯与 .agate-root 恢复兜底，理由：这是 hook 自定位契约（worktree dogfooding 依赖，out-of-scope hook 三件套），不是 legacy 软链布局支持；仅清理其 docstring 的"软链 readlink 上溯"措辞]
- [SUGGEST: S-18 推荐 UPGRADING 历史版本节原文保留，仅在 §3 顶部加一行注记；判据 10 的 grep 采用 `use_legacy`、`legacy[ _-]?(软链|symlink|layout)`、`单软链`、`软链兜底` 四模式 + 有限白名单，理由：历史节是发布事实记录，改写会失真；P0-brief 原口径（`use_legacy|legacy 软链布局`）会漏掉"单软链""软链兜底"等同义写法]

## 8. 裁剪说明

frontmatter 已含 `ceremony: full` 与 `agent: analyst`（主 Agent 授权手写）；`phases` 不裁剪（P1–P8 全走，含 P7）。

- **risk_level: high**：破坏性变更（删除 legacy 支持）+ 安装 / 解析主链路 + 新增带 `contents: write` 权限的 CI workflow + 触 SELF-GATE；**兼容性**（已装旧形态仍可解析、`_protocol_root` 探测序不动）是最大风险。
- **ceremony: full**、`phases: [P1..P8]`：不裁剪。P3（测试先行）——BDD-9/11 的红灯回放要求 P3 留旧行为红灯证据；P7（一致性）——命中 `agate/` 协议文档 + UPGRADING / README / CHANGELOG 多文件交叉核对，不可裁；P8——含 Release 首次真实触发验收。
- **domains: [backend, security]**：`backend` = 安装 / 解析 / 打包脚本与测试；`security` = tarball 完整性与成员路径安全、`contents: write` 权限最小化、fail-closed 破坏性变更、软链穿透防护。**无 frontend**：不需 UX 类别 BDD / `ui_render_shape`；无 vision 能力需求。
- **packages: [agate-scripts, agate-docs, agate-tests, ci-workflows, install-sh]**（与 dispatch 建议一致）。
- 跳过风险：无裁剪，不适用。
- **预期 SELF-GATE 触发**（供 P4 / P8 提交信息）：`agate/scripts/*.py`、`install.sh`、`agate/**/*.md`；`.github/workflows/*` 新增（CI 配置，已获用户许可）；提交信息须含 `self-gate-review:` 或 `self-gate-skip:`。

## 9. 待确认清单

[NO_NEED_CONFIRM]

- 所有取舍均已收敛为 §7 的 `[SUGGEST]`（不阻塞，主 Agent 可直接采纳），无方向性歧义、无待确认项（NEED_CONFIRM 类）、无 `[SCOPE+]`（未发现需超出 P0-brief 的项；"未做但相关"的观察已在 §5 扫描 I 列为不处理并建议进 roadmap）。
- **需主 Agent 在执行阶段单独取得用户当次许可的一项**（属操作许可而非需求方向，故不写为待确认标记）：BDD-20 向 origin 推送并清理测试 tag。

## 10. 评审处置记录（P1 retry #1，依据 P1-review.md）

| 项 | 处置 | 说明 |
|----|------|------|
| **M-1** 多场景 BDD | **已修改（方案 b）** | §4 头部新增"全或无规则"；BDD-5 / 7 / 14 / 18 / 25 / 28 / 29 / 31 / 32 共 9 条标 `[参数化]`；另因 BDD-3（三个 When）与新增的 BDD-24 ②（畸形 tag）、BDD-51 同为多子场景，一并标注（多标不少标）；P6 逐子场景留证 |
| **M-2** BDD-14 ↔ BDD-20 矛盾 / 资产名 / S-9 | **已修改** | ① BDD-14 新增 ④：预发布 tag 取去后缀段、缺段回落 `[Unreleased]`、首行"预发布测试"标注；正式 tag 缺段仍 fail-closed；② BDD-13 ⑤ / BDD-20 ② 明确"资产名 = tag 名原样"，并补 offline `manifest.version` 恒为严格 `vX.Y.Z`（否则 `install-offline._validate_manifest` 会拒收预发布 tag 的包——评审未提及的关联缺陷）；③ S-9 更正：CHECK 7 / G-5 的 `git describe` 不忽略该 tag，BDD-20 Given 写入"先清理 tag 再跑 CHECK 7 / BDD-49"，Then ④ 增"`git describe` 不再返回该 tag"；④ BDD-20 Given 增副作用声明（tag push 连带触发 `protocol-tests.yml` 等，实测记录、PR 如实列出，与 BDD-50 ③ 同口径） |
| **M-3** BDD-37 白名单 | **已修改（已实扫）** | 按 BDD-37 自身范围（`git ls-files`，任意层级 `archived/` 与 tasks / reviews / design-notes 排除，`re.I`）与四模式实跑：命中 **23 个文件** = R 清零集合 12 + W 白名单 11（+ `install-offline.py` 预登记 = W 共 12 项）；逐项落到"改写（BDD-39 / 40）"或"白名单 `(路径, 理由)`"；纠正扫描 C 中 `platform-notes.md` 判"不处理"的矛盾；BDD-39 增 ⑧⑨ 覆盖 `test_dsh_preset.py` 与 R 集合清零 |
| **M-4** BDD-42/43/45 | **已修改** | BDD-42 去掉真实模型调用，改为链接可读 + frontmatter 可解析且含 `name: orchestrator` + 指向隔离布局 + 真实 `~/.agate` 哈希不变；真实 `claude -p` 降为 P6 人工验收项 H-1（§6，不计入 BDD 总数）；BDD-43/45 二值化（tool 在 PATH 必须 PASS，不在则 FAIL），**消除 `[CAPABILITY_GAP]` 第三态**；Given 明确 `HOME` 仅供 CLI 读自身配置、`AGATE_HOME`/`$AGATE_DIR` 隔离，与【隔离】前提自洽；§6 verification_env 同步 |
| m-1 判定值悬挂 SUGGEST | **已修改** | 按评审建议把 S-1…S-6、S-8…S-19 转为 P1 基线值，BDD-2 ③ / T-1 / BDD-12 / 13 / 18 / 23 / 27 / 30 等去掉"推荐 / P2 定案"措辞；§7 保留 `[SUGGEST]` 作审计痕迹并注明已采纳；`suggest_resolved` 的 frontmatter 写入因 set 工具不接受该键、且本轮约束"不改 frontmatter 已有字段"，留给主 Agent 补写 |
| m-2 §8 与 frontmatter 矛盾 | **已修改** | §8 注释改为"已含 ceremony / agent（主 Agent 授权手写）" |
| m-3 体积数据 | **已修改** | 按 `git ls-tree -r -l v0.72.0` 校正：`agate/` 3,309,321 B、tests 1,608,842 B（48.6%）、B = 1,864,871 B、上限 2,331,089 B；标注取值 tag（T-1 / BDD-23 / S-1 / S-8） |
| m-4 BDD-46 基线 | **已修改** | 基线写死 `75a8102` |
| m-5 BDD-27 ↔ 28 措辞 | **已修改** | BDD-28 改为"不存在把软链目标当 `AGATE_ROOT` 返回的分支"，明确检测 + 迁移提示分支允许存在 |
| m-6 软链基址 + 有效 current | **已修改（追加 BDD-51）** | 规则：resolve 放行（经 `current` 链正常解析），安装侧一律拒绝（沿用 TAG0032）；配夹具；编号追加在末尾 |
| m-7 BDD-15 ③ 口径 | **已修改** | 改为"与 blob 字节逐一相同"，并写明打包机制不得用做 eol 转换的导出路径 |
| m-8 P1 纯净性 | **已修改** | BDD-14 / 15 改写为可观测需求（"逻辑可在无 CI 下被测试调用"、"CI 与本地产物逐成员字节一致"），脚本承载形态留给 P2；BDD-13 ④（第三方 action SHA 固定）作为安全约束保留 |
| m-9 BDD-7 ③ 与 BDD-25 ③ 重叠 | **已修改** | BDD-7 去掉 ③，旧形态卸载统一归 BDD-25 |
| m-10 历史 tag 缺 `agate/` | **已修改** | BDD-24 增 ②：无 `agate/scripts/` 的畸形 tag → exit 1、不留半装目录、指针不变 |
| m-11 缺 tests 目录的包内脚本容错 | **已修改（追加 BDD-52）** | 实测 `check-platform-assumptions.py` 缺目录时为明确 `FATAL: 目标不存在` 而非 Traceback，`agate-risk-score.py` 降级输出；BDD-52 锁定四脚本冒烟 |
| 评审"范围纪律"建议 | **已修改** | §3 增"衍生项子批归属"段（BDD-8/10/18/21/33/34/40/51/52 → 子批 A/B/C/E），不标 `[SCOPE+]` |
| 评审 scan B 差 4 文件 | **已记录** | §5 扫描 B 注明口径差异，不影响分类 |
