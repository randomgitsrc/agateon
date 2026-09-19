# P0-brief — TAG0037 安装与多版本模型统一（RM-AG0066）

> 主 Agent 亲自填写（P0 产出）。RM-AG0066（`agate-workspace/roadmap/roadmap.md`，backlog→scheduled）。
> **来源**：用户 2026-09-19 提出「是否该像正常安装包一样提供 setup/install？GitHub 是否该用 Release 发布？」+ 随后的安装机制系统审计。
> **性质**：**协议级设计变更**（改发布/安装契约）——**不是**局部修补。多版本机制已经历 4 轮 task（TAG0008 版本管理 v1 / TAG0017 工具链修复 / TAG0031 DEBT 清理 / TAG0032 版本生命周期），用户反馈「问题还是不少」；审计确认根因为**四条安装路径、三套目录结构约定，从未定义「版本目录里该有什么」这一根本契约**。
> **证据**：全部实测数据见 `agate-workspace/roadmap/roadmap.md` 的「RM-AG0066 详情」节。
> **DM 前置**：无。

## task

"统一 agateon 的**安装与多版本模型**——定义「版本目录的唯一结构契约」，引入 GitHub Release 与本体安装包（portable），统一在线/离线/legacy 三条安装路径，并修复离线安装的解析失效缺陷。"

### scope

**子批 A：定义并落地「版本目录结构契约」（本任务的**核心**）**

**问题**：当前三条路径产出三种结构，互不兼容——

| 路径 | 产出结构 | 状态 |
|------|---------|------|
| `install.sh`（legacy 无参） | `~/.agate` 软链 → `<repo>/agate`（**本体**） | ✅ 正确 |
| `install.sh --versions` / `agate-install.py` | `vX.Y.Z/{agate, agate-workspace, docs, site, archived, HANDOFF-*.md, ...}` | ⚠️ 冗余 91% |
| `agate-pack-offline.py` → `install-offline.py` | `vX.Y.Z/agate/{agate, README.md, ...}`（**本体在两层下**） | ❌ **解析失效** |

**实测数据**：
- `~/.agate/v0.71.1/` = **43M**，其中本体 `agate/` = **4.1M** → 冗余 ≈39M（**91%**）；另 `repo/` = **59M**
- tag v0.71.1 含 **3290 文件**，`agate/` 占 **367（11%）**；顶层含 `agate-workspace/`、`docs/`、`site/`、`HANDOFF-TAG0035.md`
- **GitHub Release**：**0 个**（从未发布）

**契约提案（P2 定案）**：

```
~/.agate/vX.Y.Z/
└── agate/              # 本体（唯一内容；目录名可经 manifest 声明，不硬编码）
```

- **legacy 形态天然符合**（软链直指本体）→ 在线/离线**对齐到它**
- 已装用户的 `vX.Y.Z/{...}`（当前在线形态）**须保持可解析**（兼容红线）

**子批 B：修复 P0 —— 离线安装解析失效（真 BUG）**

**机理（实测确认）**：

```
pack 侧   : git worktree add <bundle>/agate <tag>   → bundle/agate/ 是【整仓根】
install 侧: _copy_tree(bundle → vX.Y.Z/)            → vX.Y.Z/agate/agate/scripts/

_protocol_root 探测: vX.Y.Z/scripts ✗、vX.Y.Z/agate/scripts ✗（真实在 .../agate/agate/scripts）
→ 返回 vX.Y.Z 原样 → 【解析链失效】
```

**测试为何没抓到（根因）**：`test_install_offline.py::_make_bundle` 构造 `bundle/agate/WORKFLOW.md`——**假设 `bundle/agate/` 就是本体**，并断言 `version_dir/agate/WORKFLOW.md` 存在，**与实现同源错误**。真实 packer 用 `worktree add` 检出整仓树，布局被测试假设掩盖。

**修法**：与子批 A 的结构契约统一——pack/install 两侧按同一约定产出/解读（`bundle/agate/` 应为**本体**而非整仓树）。**并修正 `_make_bundle` 使之反映真实布局**（否则测试继续掩盖）。

**子批 C：引入 GitHub Release + 本体安装包（用户决策 ①）**

```
GitHub Release vX.Y.Z（tag push 时自动创建）
├── Release notes ← 自动提取 CHANGELOG 该版本段
└── Assets
    ├── agateon-vX.Y.Z.tar.gz                    ← 本体（portable，解压即用，无需 git）
    └── agateon-vX.Y.Z-offline-<platform>.tar.gz ← 本体 + wheels
```

- **portable 语义**：解压到 `~/.agate/vX.Y.Z/` → 建 `current` 指针即可用（**不依赖 git**）
- **⚠ 新增 `.github/workflows/` workflow 属 CI 配置改动 → 须用户明确许可**（`AGENTS.md` 规则 5）；P1 须先确认许可范围
- Release notes 从 `CHANGELOG.md` 该版本段提取（现有人工流程已有 CHANGELOG，提取脚本成本低）

**子批 D：在线安装「只装本体」+ 保留历史 tag 能力（用户决策 ②）**

- **只装本体**：消除 91% 冗余；**不再把 agateon 自身任务数据**（`agate-workspace/tasks/TAG0001-...`）与**维护者产物**（`HANDOFF-*.md`、`docs/reviews/`、`site/`）装入用户环境（现会造成语义混淆——用户可能误认为那是自己的任务空间）
- **保留**「装任意历史 tag」：`repo/`（59M）**保留**，`git worktree add` 路径仍可用（Release asset 是便利路径而非唯一路径）
- 排除清单**来源与维护方式**须 P2 定（候选：`.gitattributes export-ignore` / 显式清单文件 / `git archive` 语义）

### 完成判据

| # | 判据 | 验证方式 |
|---|------|---------|
| 1 | **结构契约成文**（权威源：`agate/UPGRADING.md`「版本管理生命周期」节） | 文档评审 |
| 2 | 三条路径**产出同一结构** | 集成测试：三种装法各装一次，断言版本目录内容一致 |
| 3 | **P0 修复**：离线安装后 `agate-resolve.py` 解析成功 | 新增 e2e 测试（**用真实 pack 产物结构**，非假 bundle） |
| 4 | `_make_bundle` 反映真实布局 | 测试评审（防同源假设复发） |
| 5 | Release 自动创建 + assets 可下载 | CI 在测试 tag 上的实跑验证 |
| 6 | portable 安装**不依赖 git** | 隔离环境（无 git）验证 |
| 7 | 在线安装**只装本体**（冗余对比有量化下降） | 装后 `du -sh` 对比 |
| 8 | 已装旧形态**仍可解析** | 兼容性测试（用当前 `vX.Y.Z/{agate,docs,...}` 结构） |
| 9 | Full pytest + consistency 0 ERROR ✅ | 常规 gate |

### out-of-scope

- **不改** `_protocol_root` 的既有探测序语义（`vdir/scripts` 优先于 `vdir/agate/scripts`——标注「不可颠倒」红线）；仅**扩展**（新增形态须增量、不破坏既有两种）
- **不改** hook 三件套与 SELF-GATE 机制
- **不改** `.state.yaml` schema、`rules/*.yaml` 权威源
- **不做**包管理器集成（npm/pip/brew 等）——本轮只做 GitHub Release + tarball
- **不做** `install-hook.py` 的 `AGATE_HOME` 语义统一（它是**协议根**而非版本根基址，属独立议题；本轮仅在文档点明层次差别）
- **不迁移已装用户的目录结构**（仅保证**可解析**；主动迁移另议）

### known_risks

- **兼容性是最大风险**：已有用户装了当前形态（`vX.Y.Z/{agate, agate-workspace, docs, ...}`）。**结构契约若收紧，必须保证旧形态仍能解析**——`_protocol_root` 的探测序是红线，只可增量扩展。P1 须先勘察「本机之外还有多少种已装形态」（本机实测只有当前形态 + legacy 软链）。
- **CI 改动的许可边界**：新增 release workflow 需用户明确许可（`AGENTS.md` 规则 5）。**P1 必须先确认**：是"允许新增 workflow 文件"，还是"连触发条件/权限也要逐项确认"。
- **`git archive` vs `export-ignore` vs 显式清单**：三种排除机制语义不同（`export-ignore` 会影响所有 archive 消费者）。P2 须比对，**勿默认选一个**。
- **tag 与 Release 的双轨一致性**：tag 是全量源码、Release asset 是本体——两者**内容不同但必须对应同一版本**。须防"打了 tag 忘了发 Release"（用户决策 ② 保留 tag 安装路径，故 tag 缺失 Release 不致命，但**最优路径不可用**）。
- **portable 的"无需 git"不是零依赖**：仍依赖系统 `python3` + `pyyaml`（`--check` 会探测）。文档勿宣称"零依赖"。
- **打包体积的边界**：本体 4.1M 中含 `tests/`（367 文件中相当部分）——**tests 是否入包**需 P2 定（用户环境不需要跑 agateon 自身测试，但排除后 `check-protocol-consistency.py` 等在用户侧可能受限）。

### env_constraints

- 运行 agateon 只需系统 `python3` + `pyyaml`（**portable 包同样需要**）；开发需 `ruff`（CI 锁 `0.16.4`）
- **本机环境**：`~/.agate` 已是版本管理布局（`v0.71.1` + `current` 指针，2026-09-18 从 legacy 迁移）；改动安装逻辑须在**隔离 `AGATE_HOME`** 下验证，勿动真实 `~/.agate`
- 本机已装 `pytest-rerunfailures`（对齐 CI 口径 `--reruns 1`）——验证须用该口径
- **改动面**：`agate/scripts/agate-install.py` / `install-offline.py` / `agate-pack-offline.py` + `install.sh` + 可能新增 `.github/workflows/` → **全部触发 SELF-GATE**（除 workflow）

## executor_env

- **worktree**：`.worktrees/agate-TAG0037`（分支 `feat/TAG0037-install-package-model`），构建流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0037.md` 按模板全 9 节填写
- **稳定版工具**：`~/.agate/scripts/`（勿动）
- **相关证据**：`agate-workspace/roadmap/roadmap.md` 的「RM-AG0066 详情」节（含四路径对比表 / 体积数据 / P0 机理 / 5 个开放问题）
- **先例参照**：`TAG0032-version-lifecycle`（上一轮，交付版本管理生命周期）、`TAG0008-version-management`（版本管理 v1）
- **关联 DEBT**：DEBT0034（迁移文案双写，closed）、DEBT0042（基址 env 覆盖，closed，其「指向层次」概念在本任务延续）
