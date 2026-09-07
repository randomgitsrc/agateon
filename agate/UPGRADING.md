# Agateon 升级指引

> 面向**已有 Agateon 项目**（已用旧版 Agateon 跑过任务）升级到新版本。
> 新接入项目不用看这里，直接读 `SETUP.md`。
> 升级前先读：`CHANGELOG.md`（本版本的变更）+ 本文件（旧数据怎么处理）。

---

## 核心原则：不动则无感

Agateon 的校验器（`agate-state-yaml-check.py` 等）**只在 .state.yaml 被 git add 暂存时才触发**（pre-commit 机制），不是扫描所有任务目录。所以：

- **旧任务数据（已完成/归档）如果不动它，升级后零检测触发、零问题**
- 只有"**要继续推进的进行中任务**"和"**新任务**"需要符合新版本规范

**升级最小动作**：`git pull` 拉新版 Agateon + 重跑 `install-hook.py`（见下文），其余按需。

---

## 1. 通用升级步骤

```bash
# 1. 升级 Agateon 本体（~/.agate 软链指向的仓库）
cd <你克隆 Agateon 的目录> && git pull

# 2. 重装 hook（推荐，pre-commit/commit-msg 软链自动跟随；pre-push 也是软链 v0.32+ 自动跟随）
python3 ~/.agate/scripts/install-hook.py

# 3. 验证版本
python3 ~/.agate/scripts/agate-summary.py   # 应显示新版本号
```

**符号链接 vs 复制模式**：
- **符号链接**（Linux/macOS 标准）：协议本体升级后自动生效，无需额外操作
- **复制模式**（Windows 无符号链接权限）：协议本体的**修改不会自动同步**到项目副本，需重跑 `cp` 命令（见 SETUP.md 步骤 2 的 Windows 段）
- **orchestrator 注册**：软链方式自动跟随；复制方式需重跑 SETUP.md 步骤 2 的 `cp`

---

## 版本管理生命周期

> 本节是版本管理布局（`~/.agate/` = 版本管理根目录：`repo/` + `vX.Y.Z/` + `latest`/`current` 指针 + 根 `scripts/`）下
> **安装 / 迁移 / 更新 / 回退** 四个动作，以及 hook 重装时机、根 `~/.agate/scripts/` 维护语义的**单一权威口径**。
> UPGRADING 其余版本历史节、`README` 快速上手、`SETUP.md` 升级节遇到分歧一律以本节为准。

### 安装 / 迁移 / 更新 / 回退对照表

| 动作 | legacy 软链布局 | 版本管理布局 |
|------|-----------------|--------------|
| 安装（新机）| `curl -sSL .../install.sh \| bash`（`~/.agate` → clone 出来的 `agate/` 子目录）| `install.sh --versions`（一键进入版本管理布局：建 `repo/` + 首个 `vX.Y.Z/` + `latest`/`current` 指针 + 根 `scripts/` 副本；`~/.agate` 已是软链则 fail-closed，提示下方迁移三步）|
| 迁移（软链 → 版本管理）| — | 三步（与 `agate-install.py` fail-closed 文案同源）：`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions` |
| 更新 | `cd <你克隆 Agateon 的目录> && git pull`（是否需重跑 `install-hook.py` 见下方「hook 重装时机」；`git pull` 无新提交时是 no-op，**幂等**）| `python3 ~/.agate/scripts/agate-install.py latest`（**幂等**：重复执行不报错、不重复建版本目录、`latest`/`current` 指针幂等切换）|
| 回退 | `git checkout <旧 tag>` | `python3 ~/.agate/scripts/agate-install.py v<旧版本>`，再在项目根 `.agate-version` 钉 `agate: v<旧版本>`（或把 `current` 指针切回旧版本目录）|

两种布局的「更新」指令在文档面对齐、各自**幂等**：legacy 侧 = `git pull`（+ 按需重跑 hook），版本管理侧 = `agate-install.py latest`。

### hook 重装时机（统一口径）

`install-hook.py` 安装的是**固定解析入口** `resolve-entry.py`（一段薄壳 `.sh` + 一个不随版本变的 Python 入口），
运行时按项目 `.agate-version` 解析版本再 exec 对应版本的 gate。因此：

- **切版本 / 升级通常无需重跑 `install-hook.py`** —— resolve-entry 固定入口机制下，改 `.agate-version`
  或跑 `agate-install.py latest` 都不改动 `.git/hooks/` 里的入口。
- **仅两种情况才重跑**：① hook 薄壳（`.sh`）本身有变更；② Windows 复制模式（hook 是复制品、不自动跟随，
  须重跑 `python3 ~/.agate/scripts/install-hook.py`）。

此口径统一收敛 v0.60-0.62 与 v0.66-0.68 历史节中「升级须重跑 `install-hook.py`」的旧表述——历史节叙事保留，实际以本节为准。

### 根 `~/.agate/scripts/` 维护语义（决策 B1：副本）

版本管理布局下 `~/.agate/scripts/` 是一份**副本**（不是软链），由 `agate-install.py`（含 `latest`）在每次
安装 / 升级时重建刷新，内容 = 运行中安装器自带的 `scripts/`（保证 `agate-install.py` / `agate_common.py` /
`resolve-entry.py` 等入口命令在新机可直接调用）叠加当前 `current` 版本的协议 `scripts/`（后者覆盖前者，后拷贝者胜）。

- **随 `agate-install.py` 重跑刷新**：升级期须重跑 `python3 ~/.agate/scripts/agate-install.py latest`，
  根入口副本才刷新到新版本工具；不重跑则根 `scripts/` 停留在上次安装的版本。
- **`repo/` 或某个 `vX.Y.Z/` 版本目录被删，不影响**已建立的 `~/.agate/scripts/` 副本可用性——
  副本是独立拷贝，不回链 `repo/` 或版本目录。
- **该副本不参与 hook 版本解析**：hook 经 resolve-entry 固定入口按项目 `.agate-version` 解析版本，
  切版本无需重跑 `agate-install.py`（也无需重跑 `install-hook.py`）。

---

## 2. 旧数据兼容策略

### 2.1 active-tasks.md（看板）

| 旧任务状态 | 处理 |
|-----------|------|
| 已完成/归档 | **不动**，保留旧编号（历史记录） |
| 进行中 | **改编号**为新格式（见 2.2），列结构本身不变 |

**列结构（进行中/待开始/已完成 + 各列头）在 v0.40.x 未变**——只有任务编号格式变了。

### 2.2 任务编号（⚠️ v0.40.0 破坏性变更）

- **旧格式**：`T001` / `T002`（`^T\d+$`）
- **新格式**：`TAG0001`（`^T[A-Z]{2}\d+$`，项目代号 2 个大写字母 + 数字）
- **硬切不兼容**：`T001` 在新校验器下会被拦（`agate-state-yaml-check.py`）

**迁移动作（仅进行中任务）**：
```bash
# 修改进行中任务的 .state.yaml 的 task_id
# T001 → TAG0001（选你项目的 2 字母代号 + 数字）
# 路径按你项目的实际任务目录（位于工作区 {AGATE_WORKSPACE}/tasks/ 下）
# Linux：sed -i 's/^task_id: T001$/task_id: TAG0001/' {AGATE_WORKSPACE}/tasks/T001-*/.state.yaml
# macOS（BSD sed 的 -i 需空后缀）：sed -i '' 's/^task_id: T001$/task_id: TAG0001/' {AGATE_WORKSPACE}/tasks/T001-*/.state.yaml
```

**已完成的旧任务**：编号保留 `T001`，不进新格式（历史记录，不被扫描）。

### 2.2.1 项目代号（`AG`/`PV`）语义

- **来源**：项目接入 Agateon 时**自行约定** 2 个大写字母代号（对齐 Jira `[A-Z][A-Z]+` 风格），Agateon **不自动生成**。例如 `AG`=agate 改造、`PV`=peekview。
- **一致性**：**同一项目应用同一代号**（`active-tasks-template.md` 第 4 条规则："项目局部命名空间内按项目代号 + 动态编号递增"）。不同项目可用不同代号（`TAG0001`/`TPV0001` 各不同，正常）；**同一项目混用代号会破坏编号的"项目标识"意义**，看板/追溯会混乱。
- **校验边界**：`agate-state-yaml-check.py` **只校验格式**（`^T[A-Z]{2}\d+$`），**不校验代号一致性**——`TAG0001`/`TPV0001`/`TXX0001` 格式都合法。代号一致性靠**项目约定 + 看板规则**维持，无强制拦截。若你的项目需要强制，可自行加检查（当前 Agateon 未内置）。
- **升级时**：为进行中的旧任务选代号时，**用你项目的既有代号**（若有约定），或新定一个并在 active-tasks-template 里记录，保持全项目一致。

### 2.3 旧任务目录

- 任务目录位于工作区 `{AGATE_WORKSPACE}/tasks/` 下
- 旧目录 `docs/tasks/T001-xxx/` 保留不动 = 无检测触发（迁移工具会将其迁入工作区 `tasks/`，见 v0.41.0 变更节）
- 新任务用新目录 `{AGATE_WORKSPACE}/tasks/TAG0001-xxx/`

### 2.4 项目侧文件（project.md 等）

- `{AGATE_WORKSPACE}/agents/project.md`（项目特定信息，位于工作区）**不在 Agateon 协议内，不会自动升级**——若其内容引用了旧编号格式（`T001`）或旧看板结构，需手动同步
- 其他项目自有文件同理：升级后检查一次即可，Agateon 不负责这些

---

## 3. 已知破坏性变更（按版本）

> 升级到新版本前，检查你的项目是否触及以下变更点。

### v0.68.0 — 验收盲区机制批（TAG0030：RM-AG0057 四类 + DEBT0024/25/26）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 /
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局
> `git pull` 即生效；Windows 复制模式重跑 SETUP.md 步骤 2 的 `cp`）。

1. **测试副作用/环境还原 gate（RM-AG0057-①）——对已有任务零影响**：P3/P4 卡新增创建型测试清理
   钩子要求（创建即注册、无条件删除、接受 200/204/404——afterEach 清理队列模式）；P6 卡验收流程
   新增 post-test 环境残留检查步骤（快照比对或清理钩子验证二选一）；dispatch-context 模板约束节
   补环境清理/环境还原条目位。均为条文新增，约束下游新任务的测试写法，不改变既有测试/验收语义。
2. **P1 人工体验路径验收节（RM-AG0057-②）——对存量任务零影响**：P1 卡 + analyst 角色新增「人工
   体验路径验收」要求（凡用户可见页面且内容受 seed 影响，强制补「Given seed 数据 → 页面有内容」
   BDD）。约束的是下游 frontend 任务的 P1 产出，不改变既有 fixture 验收机制。
3. **plan-design-review 形态驱动化（RM-AG0057-③）——对已有评审产出零影响**：评审角色先读受评任务
   `ui_render_shape` 再加载维度组评分细则；0-10 评分与 status 门槛映射原文保留，无形态声明回落
   布局型默认。
4. **视觉契约断言收录 + TAG0027 复盘三连（RM-AG0057-④ + DEBT0024/25/26）——均为条文新增**：视觉
   契约可表达子集（五类 DOM 度量）收录 architect 视觉 checklist；verifier 证据形式指南补 DOM 度量
   量化证据句；tests/README 写明 gate 消费方夹具走真实 gate 语义；AGENTS.md 新增「新增 CHECK 上线前
   先全量扫描存量」第 0 步；dispatch-context 模板补「改动体量 >5 文件按体量评估拆小」默认指导。
5. **升级动作**：`git pull` 即完成；无迁移动作。

### v0.67.2 — DEBT 存量修复批（TAG0031：DEBT0002/3/4/7/16/17/18）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 /
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局
> `git pull` 即生效；Windows 复制模式重跑 SETUP.md 步骤 2 的 `cp`）。

1. **离线包 hash 工具共享——对合规调用零影响**：`compute_sha256` 从 `agate-pack-offline.py`/
   `install-offline.py` 各自实现收敛到 `agate_common.py` 单点定义，两侧改 import 共享，函数
   签名/行为不变，仅定义位置迁移。
2. **离线安装引导逻辑增强——对合规调用零影响**：`install-offline.py` 新增 `_ensure_agate_common`
   引导函数处理 pyyaml 组件的离线 bootstrap 时序（先 checksum 校验、通过才 pip install），
   `verify_checksums` 的对外行为（checksum 不匹配即拒绝安装）不变。
3. **卸载引用扫描新增 WARNING 提示——纯增量，不改变卸载判定结果**：命中限流边界（深度>4 /
   mtime 超窗）时 stderr 多输出一行 WARNING，`_find_references` 是否允许卸载的判定逻辑本身
   不变。
4. **check-gate.py 三处健壮性修复——对合规产出零影响**：gate_p4 CODE-MAP 路径解析改用权威函数
   （标准场景结果不变）；「新增文件核对表」判定改整行匹配（真实标题存在时判定不变，只消除
   自指散文误判）；`agate_common` import 降级 stub 改 fail-closed（仅在 agate_common 不可导入
   的安装破损场景才触发新行为，正常安装不可达）。
5. **升级动作**：`git pull` 即完成；无迁移动作。

### v0.67.1 — gate 命令解析器与 TDD 红灯判定缺口修复（TAG0029：RM-AG0056 + DEBT0023/0027）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 /
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局
> `git pull` 即生效；Windows 复制模式重跑 SETUP.md 步骤 2 的 `cp`）。

1. **gate 解析语义收紧——对合规任务零影响**：`P3_js` / `P3_html` 历史多栈形态退役
   （`gate_commands` 检测键收紧为精确键，DEBT0023）；真实任务 P2 从未声明 `P3_xxx` 检测键，
   存量测试已同步；未来多栈回归走协议修订登记收集后缀。值清洗 fail-closed 只影响"命令值同行
   带注释"写法（此前本就 `bash -c` 报 exit 2 失败），合规写法（独立行注释）行为不变。
2. **judge exit 2 改判——对真实红灯零影响**：此前 exit 2（命令串本身语法错误，`bash -c`
   未起运行器）落末尾误判红灯可推进（DEBT0027 假绿灯）；现改判 exit 1（A 类）。真实测试红灯
   （运行器正常退出）判定路径不变。
3. **R2 fixture 豁免——对代码面零影响**：豁免绑定目录声明（`agate/tests/fixtures/`
   路径前缀），仅 R2 数据面跳过；目录外裸 `python3` 调用仍命中 exit 1。
4. **升级动作**：`git pull` 即完成；无迁移动作。

### v0.67.0 — subagent 存活可观测性与受控自主再派发（TAG0028：RM-AG0055）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 /
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局
> `git pull` 即生效；Windows 复制模式重跑 SETUP.md 步骤 2 的 `cp`）。

1. **新增命令流检测机制——对已有任务零影响**：三个新脚本（`agate-cmdstream-ir.py` /
   `agate-cmdstream-adapters.py` / `agate-cmdstream-detect.py`）为纯新增消费方；检测输出定位
   "证据 + 触发核查"（不自动判死），不改变既有存活机制（progress.md 语义进展职责不变）；
   `maintainability.yaml` 新增 `cmdstream_detection:` 节为可选配置，缺失/损坏兜底默认值，
   无强制、无升级动作。
2. **受控自主再派发——对已有 subagent 零影响**：子派发权限为"可被授予"而非默认开放，
   未授权 subagent 行为不变；judge 类角色不适用；dispatch-context 模板新增「不启用子派发
   能力」声明位为可选字段。
3. **升级动作**：`git pull` 即完成；无迁移动作。

### v0.66.0 — 编排语义统一落地（TAG0027：RM-AG0054）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 /
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局 `git pull`
> 即生效；Windows 复制模式重跑 SETUP.md 步骤 2 的 `cp`）。

1. **新增推进侧 CLI 与转移表字段——对已有任务零影响**：`agate next` / `agate advance` /
   `agate dispatch` 为新增消费方，不改变既有手动推进/手工 dispatch-context 路径；存量任务
   dispatch-context（物理占位符注入）由审计 2 文件版逻辑继续覆盖；`phases.yaml` 新键
   （next/retreat/gate_pass_exit/gate_subphase）只被新 CLI/新检查消费，既有 check-gate /
   check-state-transition 返回语义不变（check-gate exit 2 = 多数 phase 正常通过码的口径以
   `phases.yaml gate_pass_exit` 声明为准）。
2. **编排心智标记约定（护栏 1）**：协议文档叙述段若提平台名（OpenCode / Claude Code / DSH /
   workflow / ralph / goal / task 词边界），须挂 `> 实现注记：` 标记或落入豁免结构
   （platform-notes.md / SETUP.md 整文件 + WORKFLOW.md「已知适用环境」表 +
   assets/templates/dsh/ 平台食谱目录）——新增/改写协议 md 文档时注意（CHECK 14/15 CI 硬校验）。
   此条只约束协议维护者，不约束协议使用者。

> 实现注记：上段平台名清单（OpenCode / Claude Code / DSH / workflow / ralph / goal / task）是
> 护栏 1 检查触发的词表说明（元信息，描述 CHECK 14/15 扫什么），非协议语义定义；本升级章节为
> 历史变更记录叙事。
3. **升级动作**：`git pull` 即完成；无迁移动作。

### v0.65.0 — 维护性反模式 gate（TAG0026：RM-AG0046）

> **本版本无破坏性变更，零迁移动作**。

**① 新增检测器与 P4 三重门槛——对已有任务的兼容性说明（TAG0026 要点）**：新增
`agate/scripts/check-maintainability.py`（god-file 跨越 + fuzzy-boundary 检测，diff 驱动）与
`check-gate.py` gate_p4 三重门槛（violations 非空时要求 known-violations.md 登记 + 数量对齐 +
P4 评审 approve 三者齐全才放行）。对已有任务**零影响**：既有任务无 `known-violations.md`
时，三重门槛仅在 violations 非空时触发；violations 为空 / 检测未部署 / git 通道不可用三场景
gate_p4 行为与旧版完全一致。新模板 `agate/assets/templates/known-violations-template.md`
仅 violations 非空的任务需要使用。

**② 可选配置**：`agate-workspace/maintainability.yaml` 为可选配置（god-file 阈值 + 正则集，
文件内注释注明"默认值仅供参考可配置"）——不创建则使用内置默认值，无强制、无升级动作。

**③ 升级动作**：`git pull` 即完成（软链布局自动生效）；复制模式（Windows）需重跑
SETUP.md 步骤 2 的 `cp`。本版本未改 3 个 hook 薄壳，无需重跑 `install-hook.py`。

**④ gate 行为收紧说明（合法数据无影响）**：gate_p4 新增的阻断仅针对"本次 diff 引入反模式
且未登记"场景——历史合规任务（无 staged 代码 violation）不受影响。

### v0.64.0 — Agateon 品牌改名 Phase 0-1（TAG0025：RM-AG0035 剩余工作②）+ 维护性变更批

> **本版本无破坏性变更，零迁移动作**。GitHub 主仓改名不影响已有 clone/CI（301 跳转兜底，
> 且本机 remote 已主动迁移不依赖跳转）；本地目录名/`~/.agate`/`AGATE_*`/`agate-*.py`/
> `agate_common` 等内部命名空间均未改动。

**① GitHub 主仓改名**：主仓已改名为 `randomgitsrc/agateon`。已 clone 的项目**无需任何
动作**——旧 URL 301 自动跳转（`git fetch`/`git pull`/`git clone` 均可继续用旧 URL，性能上会多
一次重定向）；若想直接指向新仓，可选执行 `git remote set-url origin
https://github.com/randomgitsrc/agateon.git`。新用户的一键安装脚本（`install.sh`）与
`agate-install.py` 默认仓库地址已同步指向新仓，无需额外配置。

**② CHECK 13：CHANGELOG↔UPGRADING 章节对应性检查（RM-AG0052）**：`check-protocol-consistency.py`
新增校验项，仅影响 dogfooding 本仓库协议自身开发流程（消费方项目一般不运行此脚本），不影响
下游项目。

**③ CI 修复（consistency job fetch tags / docs-only PR 合并）**：仅影响本仓库自身 CI 流水线，
不影响下游消费方项目。

**通用升级动作**：`git pull` 即完成（软链布局）；无需重跑 `install-hook.py`（无 hook 变更）。

### v0.63.0 — 工具链批（TAG0024：agate-md-field-set / roadmap-done 健壮性）

> **本版本无破坏性变更，零迁移动作**。新增 CLI 工具随 `git pull` 自动可用，无需任何重装步骤
> （本版本未改 3 个 hook 薄壳与任何字段格式）。

**① 新增工具（无安装步骤）**：`agate-md-field-set.py` / `agate-md-field-set-gate-commands.py`
（"写入即校验"的结构化字段写入，RM-AG0048 一期）——脚本即产品，软链布局 `git pull` 后自动可用；
复制模式（Windows）需重跑 SETUP.md 步骤 2 的 `cp`。

**② gate 行为收紧（合法数据无影响）**：
- `check-gate.py` `_check_roadmap_done()` 列数判据改为精确匹配 9 列（原 ≥8，DEBT0019）：
  合法 roadmap.md（9 列）判定结果不变；单元格含字面 `|` 等非法列数行从"错位取值"改为"整行跳过 + WARNING"。
- `gate_p8()` 的 roadmap 路径改以 `git rev-parse --show-toplevel` 仓库根锚定（DEBT0020）：
  非仓库根 CWD 调用不再静默失配（原静默跳过 → 现正常执行校验）。**升级动作**：无；但历史习惯
  在非仓库根 CWD 跑 gate 且 roadmap 未回写 done 的项目，此后会被真实校验拦到（本就是应拦行为）。

**③ 其余（无升级动作）**：RM-AG0049/50 协议文档自洽（纯文档口径统一）、check-pruning.py 测试隔离
修复（测试侧）、ADR-011 引导型 CLI 权限原则（决策记录）。

**通用升级动作**：`git pull` 即完成（软链布局）；通用步骤的 `install-hook.py` 重跑对本版本无必要
（无 hook 变更），跑了也无害。

### v0.62.0 — 机制校验补强批（TAG0023：RM-AG0042 retries 对应性 / RM-AG0043 roadmap 回写反查）

> **本版本含 gate 行为收紧**（无字段/格式变更，仅新增校验点）。升级前逐条对照，
> 未触及项零动作（"不动则无感"原则不变）。

**① 门槛失败事件 ↔ retries 对应性校验（RM-AG0042，影响：进行中任务）**

- `check-state-transition.py` 新增 `check_retries_correspondence()`，覆盖三类事件源：
  - **评审 rejected**（扫描评审角色 retry/rev dispatch-context 文件，C8 已知评审角色 token 精确枚举）
    → 检测到事件而 `.state.yaml` `retries[Pn]` 为空/缺失 → 高优 WARNING（不阻断，信号源置信度较低）；
  - **P5→P4 等单步回退**（`get_old_phase()` 的 git-show-HEAD 范式，`old_num > new_num` 且暂存版本
    `retries` 长度未增长）→ **exit 1 阻断**（结构化数值比较，误报率低）；
  - **子代理空返回重派**（"空返回"/"重派"关键词扫描）→ 高优 WARNING（不阻断）。
- 升级动作：进行中任务若曾发生门槛失败事件但 `retries` 为空，需补写对应条目再推进（P1/P2 卡已要求
  评审被拒即写 retries）；新任务无动作。

**② P8 roadmap 回写 done 反查（RM-AG0043，影响：P8 发布流程）**

- `check-gate.py` `gate_p8()` 新增 `_check_roadmap_done()`：按 `task_id` 精确匹配
  `{AGATE_WORKSPACE}/roadmap/roadmap.md`「关联任务」列，任一关联 RM 条目状态非 `done` → **exit 1 阻断**。
- 升级动作：P8 前确认关联 roadmap 条目已回写 `done`（任务无 roadmap 关联则不触发）；无迁移动作。

**③ 其余（无升级动作）**：RM-AG0044 环境敏感测试治理（测试侧，CI pytest 加 `--reruns 1` 兜底）、
RM-AG0045 声明写时自检（dispatch-prompt 返回前自检 + frontmatter 错误消息增强，非 gate 拦截变化）。

**通用升级动作**：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`。

### v0.61.0 — 质量门禁收尾（TAG0022：RM-AG0037 ruff 合并强制 / RM-AG0038 权威源切换 / RM-AG0039 judge 强制化）

> **本版本含破坏性变更**（RM-AG0038 权威源切换 / RM-AG0039 judge 强制化，详细条目见下方
> ②③；RM-AG0037 为门禁配置步骤，无脚本行为变化）。升级前先逐条对照，判断你的项目是否触及；
> 未触及项零动作（"不动则无感"原则不变）。

**① CI ruff job 可被 PR required check 引用（RM-AG0037，维护者配置步骤）**

- **背景**：ruff 此前只是 CI 普通 job，对 PR 合并非硬性——TAG0019/20 曾分别带 23/12 处 ruff
  违规合并进 main（合并后实测共 35 处，靠事后 PR #183 补修）。v0.61.0 起 CI ruff job 的
  `pip install ruff` 改为锁版本 `ruff==0.16.4`（与本地开发环境 `~/.venvs/agate-dev/bin/ruff`
  对齐，BDD-2 对齐语义实体化），job name 保持稳定 `ruff`（可被 GitHub 分支保护按 check 名引用）。
- **配置步骤（维护者/仓库管理员在 GitHub 仓库设置执行——required check 勾选是配置，非实现侧动作）**：
  1. GitHub 仓库 → **Settings → Branches → 分支保护规则**（Branch protection rules）→ 选择受保护分支（如 `main`）；
  2. 在 "Require status checks to pass before merging" 中**勾选 ruff** check（对应 CI `ruff:` job）；
  3. 保存后，PR 合并前必须通过该 ruff check——`ruff check agate/`（`ruff==0.16.4`，项目根
     `pyproject.toml` 规则集）exit 0（零违规）方可合并。
- **升级动作**：无（纯 CI 配置 + 文档；已部署项目无迁移动作）。项目合并链路在 required check 勾选
  生效后由 CI 自动强制。

**② RM-AG0038 权威源切换（check-gate 规则读取闭环）**

- **影响面**：`check-gate.py`（P1/P2/P6/P7/P6.5 分支的协议规则类 md/grep 解析点清零）+ `agate_common.py`
  （新增共享读取器：count_markers / extract_bdd_titles / parse_ui_design_section / count_p6_pass_fail /
  count_p7_markers / count_design_gap / count_code_map_lines / parse_fail_list_block / count_kf_entries /
  extract_embedded_yaml_blocks 等）+ `agate-md-field-get.py`（新 op：status / agent / project_phase /
  code_map_new_files_count / code_map_reviewed_count / created）+ `check-structure-consistency.py`
  （S-3 双向收紧：S-3a YAML→卡片、S-3b 卡片→YAML 的 gate 命令一致性）+ `agate/rules/phases.yaml`
  （各阶段 gates[].check 增补实际命令串）。`.state.yaml` 读取与 git/CHANGELOG 输出解析（E/F 组）不在迁移面。
- **行为变化**：协议可判定规则声明**只从 `rules/*.yaml` 读取**，协议 md / phase-cards 中新增可判定规则
  （如 gate 命令行）不再被脚本消费——S-3 双向检查拦截 md 侧新增规则未入 YAML（ERROR）。任务产出文件
  （P1/P2/P6/P7 格式判定）读取走共享读取器，**判定口径与旧版逐字节等价**（well-formed 输入；畸形/带引号
  frontmatter 边界按 fail-closed/更正确方向处理，不产生假 PASS）。
- **升级动作**：`git pull` + 重跑 `install-hook.py` 即可；**无存量任务迁移动作**——旧格式任务产出
  （无新字段）靠共享读取器正文回退，语义不变（「不动则无感」原则保持）。
- **对账兜底行为**：迁移保留双轨（frontmatter 优先 + 正文回退），旧正文格式任务可照常跑 gate；
  本版本为判定口径等价迁移，无 v0.60.0 M1 型对账叠加。

**③ RM-AG0039 judge 强制化（机制后新任务 P1 机械校验）**

- **判据**：`agate/rules/dispatch.yaml` 新增 `judge_required_since: "2026-08-22"`（机制发布日，ISO）；
  `check-gate.py` gate_p1 读 `.state.yaml` judge 块 + P1 frontmatter `created`（`agate-md-field-get` created op，
  ISO 字典序比较）+ rules 截止日期。
- **判定语义**：机制后新任务（`created` ≥ `2026-08-22`）缺 judge 块或 `judge.enabled` 非 true →
  **P1 gate exit 1 阻断**（fail-closed，stderr 提示「机制后新任务须在 .state.yaml 写 judge.enabled: true」）；
  含 `judge.enabled: true` → 原语义放行；`judge.enabled` falsy 与缺失同走 created 判据（falsy + created ≥
  截止 → exit 1；falsy + pre-cutoff → 跳过）；judge 非 dict（如 `judge: true`）按缺失处理；历史任务
  （created < 截止 / created 缺失或非 ISO）无 judge 块 → **跳过不被拦**（fail-open，兼容存量）。
- **升级动作**：进行中任务（created < 2026-08-22）零动作；**新任务 P1 初始化必须写 `judge.enabled: true`**
  （P1 卡产出规格已加 checklist，state-machine L442-443 模板语义已同步）；机制后存量任务若 P1 缺 judge 块
  且 created ≥ 截止，需补写 judge 块再推进。
- **不动面**：P6.5 消费链（pre-commit-gate 2i.1 / ci-gate-backstop / gate_p65 早退语义）逐字节不变。

**通用升级动作**：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS
符号链接模式自动跟随；Windows 复制模式必须重跑——②③ 补齐后若含 hook/脚本行为变更，以补齐条目为准）。

### v0.60.0 — 协议结构化层（TAG0021/RM-AG0022，M0-M2：破坏性变更）

> **本版本含破坏性变更**（M2 切权威源 + 一致性 gate 提升阻断）。升级前先逐条对照，
> 判断你的项目是否触及；未触及项零动作（"不动则无感"原则不变）。

**① 三脚本从"grep 解析任务 md"切换为"读 YAML 权威源为主 + 对账兜底"（影响：所有进行中任务 + 运行 gate 的 CI/批处理）**

| 脚本 | 升级前（v0.59.x） | 升级后（v0.60.0） |
|------|-------------------|-------------------|
| `agate-read-gate-commands.py` | 内联正则解析 P2-design.md 的 `gate_commands:` 块 | 块解析迁至 `agate_common.parse_gate_commands_block`（公共库单点）；gate_commands 合法 key 判定读 `rules/dispatch.yaml`（`gate_commands_syntax`）+ `rules/phases.yaml`（阶段集） |
| `check-pruning.py` | risk_level/phases 经 agate-md-field-get 双读 | 同前（frontmatter 结构化优先本就成立）；协议规则读 rules/*.yaml，正文 grep 降级为对账兜底 |
| `check-gate.py`（P2 分支） | 内联四字段正则 + 内联 gate_commands 块正则 | 四字段计数/块解析迁至 `agate_common` 共享助手（`count_p2_declared_fields`/`parse_gate_commands_block`）；gate 判定读 rules/*.yaml |

- **迁移后判定语义不变**：退出码 0/1/2 语义、P2 四字段门槛、P3 命令输出 JSON 结构均与
  v0.59.x 一致；差异只在解析实现位置（消费脚本 → 公共库）与协议规则来源（md 内嵌 → rules/*.yaml）。
- **对账兜底**：M1 双跑对账（`RECONCILE WARNING`/`RECONCILE SUMMARY`，stderr，`AGATE_RECONCILE`
  可关）保留——旧格式 md 正文字段（frontmatter 之外）仍被读取用于对账比对，旧任务继续可跑。
- 升级动作：**进行中任务**的 P2-design.md / P1-requirements.md 若用旧正文格式声明四字段 /
  risk_level / phases / gate_commands，建议迁移到 frontmatter（机器字段）；不迁移也可跑
  （对账兜底不阻断），但会持续输出 RECONCILE 差异告警。

**② 一致性 gate 提升阻断（影响：commit 流程 + CI）**

- `check-structure-consistency.py`（S-1~S-6 双向一致性，ERROR 即 exit 1）从"仅 P5 gate + 手动"
  提升为 **pre-commit 独立 step + CI consistency job 追加步骤**（P2-design §3.3 触发点时间线 M2 起）。
- **漂移即阻断**：若 `rules/{phases,dispatch,roles}.yaml` 与协议 md（WORKFLOW 阶段总览表 /
  phase-cards / scripts 登记）出现不一致（如改 WORKFLOW 表忘改 phases.yaml），pre-commit 与 CI
  均会 exit 1 阻断。
- 升级动作：无（协议自带 rules/*.yaml 与 md 已一致；若你的项目对 `AGATE_ROOT` 做了自定义覆盖，
  确保覆盖的协议根含 `rules/` 目录，否则 pre-commit 结构检查 FATAL 阻断——见 ① 注释）。

**③ 新增协议规则数据层 `rules/*.yaml` + schema（纯增量）**

- 新增 `agate/rules/{phases,dispatch,roles}.yaml` + `agate/rules/schema/*.json` +
  `check-yaml-schema.py` / `check-structure-consistency.py`——全部纯新增文件，不改变既有
  协议文件语义；既有 `agate/rules/*.md`（review-mapping.md / state-transitions.md）保留不动
  （S-2 对账面仅 WORKFLOW 总览表）。
- 升级动作：无。

**通用升级动作**：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS
符号链接模式自动跟随，不放心可重跑确认；Windows 复制模式必须重跑——新 pre-commit 含结构一致性
step，复制模式不重跑则旧 hook 不生效）。

### v0.59.0 — 独立 Judge 机制（无破坏性变更）

**本版本无破坏性变更，无需迁移动作。**

- 新增 P6.5 独立 Judge 复核（P6 验收后、P7 之前，所有任务强制）：新角色 `assets/review-roles/judge.md`
  以 fresh context 逐条重验所有 BDD（含已 PASS 项），只信 `P6-evidence/` 证据与 git log。
- 新增检查脚本 `check-judge-verdict.py` + `check-events.py`；`check-gate.py` 增加 `P6.5` 分支——
  **只对启用了 judge 机制的任务生效**（`.state.yaml` 含 `judge.enabled: true`）；历史任务/存量任务
  无该字段 → P6.5 全链自动跳过（含 gate、pre-commit 注入、CI backstop 三处守卫一致）。
- 新增 append-only 事件账本 `{AGATE_WORKSPACE}/tasks/{Txxx}/gate-events.jsonl`（`append_event`
  单点写入，随任务目录落库）——仅新增文件，不改变既有 `.state.yaml` / 产出文件语义。

### v0.58.0 — TAG0019 风险分路由（无破坏性变更）

**本版本无破坏性变更，无需迁移动作。**

- 新增 `ceremony:` 声明字段（P1 frontmatter 可选，thin / standard / full）：缺省 standard（fail-closed——不声明或声明要素不满足一律按 standard 处理，不做薄化）；声明 thin 须四要素 checklist（coupling_checklist 流式 + 跳过风险 + P5/P6 保留）；`ceremony: full` 任务 phases 必须含 P7（P7 不可裁）。
- 新增 `check-routing.py` gate 挂载（pre-commit 2.7.1）：ceremony 路由校验——声明与算分 tier 一致性（单向 fail-closed）+ thin 四要素 checklist，不声明回退 standard。
- 新增 `agate-risk-score.py` 新工具：客观信号算分（文件类型 / 敏感路径 / 改动规模 / 影响面），输出 risk_score / tier（thin/standard/full）+ 逐信号证据行；提供可 import 的 `score_task(task_dir)` 与 CLI 薄壳。
- 已有项目升级：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS 符号链接模式自动跟随，不放心可重跑确认；Windows 复制模式必须重跑）。

### v0.57.0 — DSH 平台支持（无破坏性变更）

> 实现注记：本段为版本升级记录（平台支持变更史：该版本新增对 DSH/deepseek-harness 平台的原生
> 支持，RM-AG0030）——记录已发生事实，平台名是记录对象本身，属历史叙事元信息（升级说明元信息
> 判定；UPGRADING.md 全文均为面向存量项目的版本升级说明，见文件头）；不删改历史事实。

**本版本无破坏性变更，无需迁移动作。**

- agate 新增对 DSH（deepseek-harness）平台的原生支持（RM-AG0030）：`assets/templates/dsh/`
  三文件（agent.cordis.yml / preset.yml / SKILL.md）+ `SETUP.md`「步骤 2-DSH」+ `platform-notes.md`
  DSH 条目 + `tests/unit/test_dsh_preset.py` 回归测试——全部为新增文件/新增章节，未改动任何既有
  协议机制运行时行为。
- **DSH 平台接入（新接入用户）见 `SETUP.md`「步骤 2-DSH」**：符号链接注册 orchestrator
  agent-preset 与 agate-protocol skill 后，在 DSH 会话选择器选「agate 编排者」即可按 P0-P8
  全流程使用。
- 已有项目升级：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS 符号
  链接模式自动跟随，不放心可重跑确认；Windows 复制模式必须重跑）。

### v0.52.0 — 协议机制增强批（无破坏性变更）

**本版本无破坏性变更，无需迁移动作。**

- 新增 `{key}_timeout_seconds` **可选**声明性字段（`gate_commands` 块内，如 `P5_timeout_seconds`）——缺字段时行为等同现状（`check-gate.py` 未新增校验，无运行时消费方），既有任务不受影响。
- `dispatch-protocol.md` verification_env 节新增「失败处理协议」+「环境准备职责边界」子节（权威定义，P5/P6 卡片与 verifier.md 引用不重复展开）；「派发编排机制」并行规则新增第 4 条"资源密集型默认串行"；「派发 prompt 模板」新增"命令超时兜底"运行时纪律段落（与 `dispatch-prompt.md` 同步）——均为新增文档规则/运行时纪律，不改变任何既有 gate 脚本 exit code 语义。
- P0/P1/P2 三张阶段卡新增"同类扫描/影响面梳理"强制节 + P0-brief 时效性自检项（`[P0_STALE:]` 标记）——新增的是人工评审流程要求（requirements-review 打回判据），不对应脚本硬拦截，老任务不受影响。
- 已有项目升级：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS 符号链接模式自动跟随，不放心可重跑确认；Windows 复制模式必须重跑）。

### v0.51.0 — agate UI/UX 验收质量机制（影响：frontend/UI 任务 + P6 截图证据路径）

> 版本号已由 P8 确认（v0.51.0）。TAG0006 为 agate 补充 UI/UX 验收质量机制：P1 vision 能力三态硬声明、P2 UI 设计节检查、P6 双证据三态分档 + 射线形态适配、avg-hash 雷同判定升级。**本版本破坏性变更 / 行为变化逐条列出**（供升级前三问"我的项目是否触及"）。

**① `avg-hash` 雷同截图判定从 WARNING 升级为「降级待复核」（影响：所有任务的 P6 截图证据路径）**：

| 升级前 | 升级后 |
|--------|--------|
| P6 验收中两条不同操作类 BDD 截图视觉高度相似（avg-hash 相同）→ 仅非阻断 WARNING（exit 2） | avg-hash 重复 → 判定为「降级待复核」——P6-acceptance.md 含人工复核记录（`雷同截图复核` / `manual-review: <file>` 引用且文件存在）→ 放行；无记录 → exit 1 阻断 |

- **md5 逐字节重复硬阻断语义不变**（原本就是 exit 1）。
- **行为差异类 BDD 视觉相同的场景**（如两个查询命中同一空状态）：优先改用非截图证据（断言日志/response.json），或用带时间戳/高亮差异的截图，确保逐字节不同；若必须用截图且视觉相近 → 走人工复核记录放行。
- **帧序列 `frames/` 与时序截图 `-tN` 系列**：同 BDD 组（bdd-id 前缀）内的相邻帧/相邻时刻**豁免**雷同判定（动画/时序正常特性），跨 BDD 组雷同仍按上表处理。
- 升级动作：既有任务如有 P6 截图证据即将面对该判定——按需补复核记录或改用非截图证据。

**② 新检查为"零动作则无感"门槛（不触发既有任务）**：P1 vision 三态、P1 渲染形态/维度声明、P2 UI 设计节检查——只在任务**新声明 `domains: frontend` / `ui_affected: true` / 形态字段**时才触发；既有任务（无这些声明）走默认（布局型 + available 语义），不新增硬校验、不红基线。**若未来某 frontend 任务 P1 漏声明 vision 条目 → 下次过 P1 gate 会 exit 1（这正是机制目标：强制声明）**。

**③ 渲染形态适配为可选（向后兼容）**：`ui_render_shape` / `ui_ux_dimensions` 为 P1 frontmatter **可选字段**（presence 语义），缺失 = 布局型默认。开启了渲染组件/时序特效形态的任务，P6 证据形式须按形态匹配（帧序列/渲染输出对比/时序截图），纯文本证据拦截。

---

### v0.47.0 — 测试框架 bats → pytest 迁移（影响：跑 agate 测试的开发者 / CI 维护者）

> 实现注记：本段为版本升级记录（测试框架/CI matrix 变更史）——workflow、CI 平台 job 名
> （ubuntu/windows-latest 等）是记录对象本身，属历史叙事元信息（升级说明元信息判定），非协议
> 语义定义；不删改历史事实。

> 版本号已由 P8 确认（v0.47.0）。agate 测试套件从 Bats 全面迁移到 pytest（TAG0011）：`agate/tests/` 下 60 个 `.bats` 文件 / 749 @test 迁移为 `test_*.py` pytest 用例，`agate/tests/helpers/` 三文件（load.bash / fixtures.bash / git-helper.bash）退役，由 `agate/tests/conftest.py` fixture 体系承接。

**① 测试命令变化（跑 agate 测试的开发者必须改命令）**：

| 迁移前（bats） | 迁移后（pytest） |
|----------------|------------------|
| `bats agate/tests/sanity.bats agate/tests/unit/ agate/tests/regression/ agate/tests/integration/` | `python3 -m pytest agate/tests/` |
| `bats agate/tests/unit/check-pruning.bats` | `python3 -m pytest agate/tests/unit/test_check_pruning.py` |
| `bats -c` 收集计数 | `python3 -m pytest --collect-only -q`（`count-tests.sh` 已改写为 pytest 收集计数） |

- 依赖从「Bats + shellcheck + python3-yaml」改为「**pytest + pyyaml**」；shellcheck 仍用于 3 个 hook 薄壳静态检查（CI `shellcheck` job 保留）
- **Windows 冒烟机制变化**：`check-windows-smoke.sh` 退役，Windows CI 冒烟由 `@pytest.mark.windows_smoke` marker 承接（`python3 -m pytest agate/tests/ -m windows_smoke`）——平台敏感用例的打标清单即代表集，语义与退役脚本的「每文件第 1 个用例 + 平台关键词用例」一致
- **目录变化**：`agate/tests/helpers/` 三文件退役；`agate/tests/` 下 60 个 `.bats` 已全部删除（0 残留），不再有 `.bats`，测试用例均为 `test_*.py` pytest 用例（`conftest.py` fixture、`agate/tests/scripts/count-tests.sh` 等支持文件保留）

**② CI matrix（项目维护者）**：`.github/workflows/protocol-tests.yml` 的 `bats` job 改为 `pytest` job（ubuntu/windows 双 matrix 保留：Linux 全量 + Windows `-m windows_smoke` 冒烟）。若你 fork/自建 CI 参考了 agate 的 workflow，注意此点——分支保护 required checks 需更新为实际 job 名（`pytest` / `pytest (ubuntu-latest)` / `pytest (windows-latest)` 等，含平台后缀）。

**③ ruff 覆盖范围（项目维护者）**：`ruff check agate/scripts/` 扩展为 `ruff check agate/`（含 tests，BDD-3）——测试代码也纳入 ruff 静态检查。

### v0.46.0 — 产品逻辑 Python 化（影响：所有已部署项目 + 直接调用脚本的用户）

> 版本号已由 P8 确认（v0.46.0）。这是 agate 自建以来最大的一次脚本层破坏性变更：`agate/scripts/` 下全部 30 个 `.sh` 脚本的 bash 逻辑迁移为 Python（`.py`），仅 3 个 git hook 入口保留 `.sh` 薄壳。

**① 脚本改名/删档清单（直接调用脚本的用户必须改命令）**：

| 迁移前（.sh） | 迁移后（.py） | 说明 |
|---------------|--------------|------|
| `check-changelog.sh` | `check-changelog.py` | 同名换后缀 |
| `check-frontmatter.sh` | `check-frontmatter.py` | 同名换后缀 |
| `check-state-yaml.sh` | `check-state-yaml.py` | 同名换后缀 |
| `check-p6-format.sh` | `check-p6-format.py` | 同名换后缀 |
| `check-scope-resolved.sh` | `check-scope-resolved.py` | 同名换后缀 |
| `agate-archive-stale-outputs.sh` | `agate-archive-stale-outputs.py` | 同名换后缀 |
| `agate-extract-context.sh` | `agate-extract-context.py` | 同名换后缀 |
| `agate-next-card.sh` | `agate-next-card.py` | 同名换后缀 |
| `agate-render-dispatch-prompt.sh` | `agate-render-dispatch-prompt.py` | 同名换后缀 |
| `agate-summary.sh` | `agate-summary.py` | 同名换后缀 |
| `agate-changes.sh` | `agate-changes.py` | 同名换后缀 |
| `agate-migrate-workspace.sh` | `agate-migrate-workspace.py` | 同名换后缀 |
| `check-platform-assumptions.sh` | `check-platform-assumptions.py` | 同名换后缀 |
| `check-state-transition.sh` | `check-state-transition.py` | 同名换后缀 |
| `check-retrospective.sh` | `check-retrospective.py` | 同名换后缀 |
| `check-pruning.sh` | `check-pruning.py` | 同名换后缀 |
| `check-debt.sh` | `check-debt.py` | 同名换后缀 |
| `check-tdd-red.sh` | `check-tdd-red.py` | 同名换后缀 |
| `check-gate.sh` | `check-gate.py` | 同名换后缀 |
| `check-p6-evidence.sh` | `check-p6-evidence.py` | 同名换后缀 |
| `check-p6-provenance.sh` | `check-p6-provenance.py` | 同名换后缀 |
| `agate-capture-env-baseline.sh` | `agate-capture-env-baseline.py` | 同名换后缀 |
| `agate-retreat-to.sh` | `agate-retreat-to.py` | 同名换后缀 |
| `agate-inject-card.sh` | `agate-inject-card.py` | 同名换后缀 |
| `install-hook.sh` | `install-hook.py` | 同名换后缀 |
| `pre-commit-gate.sh` | **保留 `.sh` 薄壳** + 新增 `pre-commit-gate.py` | hook 入口薄壳化：只做定位 AGATE_ROOT + python 探测 + exec py 主程序 |
| `commit-msg-self-gate.sh` | **保留 `.sh` 薄壳** + 新增 `commit-msg-self-gate.py` | 同上 |
| `pre-push-gate.sh` | **保留 `.sh` 薄壳** + 新增 `pre-push-gate.py` | 同上 |
| `gate-result.sh` | **删档** → 并入 `agate_common.py` | 函数库合并为公共模块 |
| `agate-workspace-resolve.sh` | **删档** → 并入 `agate_common.py` | 工作区解析合并为公共模块 |

- **调用命令变化**：`bash ~/.agate/scripts/xxx.sh` → `python3 ~/.agate/scripts/xxx.py`（hook 薄壳仍由 git 经 sh 执行，无需手动调）
- **新增 `agate_common.py`**：承载原 gate-result.sh + agate-workspace-resolve.sh 的函数库（`write_gate_result` / `read_state_phase` / `resolve_workspace` / `probe_python` / `run_git` / `MAX_RETRY_MAP` 等），执行模式输出 `AGATE_WORKSPACE=` / `AGATE_TASKS_DIR=` 两行（workspace-resolve 契约不变）
- 3 个 hook 薄壳是**仅存的 `.sh`**；`agate/tests/scripts/count-tests.sh` 已改写为 pytest 收集计数、`check-windows-smoke.sh` 已退役（TAG0011，Windows 冒烟由 pytest marker 承接）

**② install-hook 迁移命令**：

```bash
# 旧：bash ~/.agate/scripts/install-hook.sh
python3 ~/.agate/scripts/install-hook.py
```

- **符号链接模式（Linux/macOS 标准）**：hook 为 `ln -sf` 软链 → 升级 agate 后**自动跟随新代码，无需重装**。不放心可重跑一次上面的命令确认。
- **复制模式（Windows 无符号链接权限）**：hook 是复制品，不自动跟随 → **必须重跑** `python3 ~/.agate/scripts/install-hook.py`（会以复制模式重装 + 写 `.agate-root` 标记）。
- 手动复制的 hook（早期版本 `cp` 方式）：同样重跑上面的命令。

**③ shellcheck → ruff（开发者）**：

- `shellcheck` 扫描面收敛到 3 个 hook 薄壳（`shellcheck -S warning agate/scripts/*.sh` 只覆盖它们）
- Python 脚本改用 **ruff** 静态检查：`ruff check agate/scripts/`（规则集在仓库根 `pyproject.toml`，TAG0010 交付）——CI `ruff` job 独立运行
- `bash agate/tests/scripts/count-tests.sh` 仍可用——已改写为 pytest 收集计数（TAG0011）

**④ python3 + pyyaml 强制依赖（影响：所有已部署项目）**：

- 全部 gate 逻辑现为 Python，**pyyaml 从「可选」变为「强制」**（agate_common.py 及所有状态读取工具 import yaml，缺失时 fail-closed exit 1）
- 安装：`pip install pyyaml`（Python 3.8+）
- **hook 薄壳 fail-closed 语义**：薄壳探测不到 python3/python 或对应 `.py` 缺失时，输出 `GATE ERROR` 并 **exit 1 阻断 commit**（不静默放行、无 sh 兜底逻辑）——Windows 无 python 环境的机器 commit 会被阻断，需先装 python3 + pyyaml
- Pillow 仍为可选（仅 check-p6-evidence.py 的像素方差/ahash）

**⑤ 无 bash 环境（纯 cmd/PowerShell）成为可行选项**：gate 脚本已全部 Python 化，`python3` 可直接运行（P0-P8 全程可执行）；唯一受限是 git hook 入口薄壳仍需 sh（Git for Windows）。详见 `platform-notes.md`「Windows 原生」。

### v0.50.0 — agate 版本管理机制（~/.agate 目录化 + .agate-version + hook 解析入口迁移，影响：所有已部署项目）

> 版本号已由 P8 确认（v0.50.0）。TAG0008 交付 agate 版本管理机制 v1：`~/.agate` 从**单一软链**升级为**版本管理根目录**（`repo/` + `vX.Y.Z/` 版本目录 + `latest`/`current` 纯指针），新增 `agate-install` / `agate-resolve` / `agate-pack-offline` / `install-offline` 4 个工具，hook 从"指向具体版本脚本"改为"经固定解析入口 resolve-entry 按项目 `.agate-version` 解析版本"。

**① `~/.agate` 布局变化（安装层，影响：管理 agate 本体的人）**：

| 迁移前（≤ v0.49.0） | 迁移后（v0.50.0+） |
|---------------------|---------------------|
| `~/.agate` = 软链 → 仓库的 `agate/` 子目录 | `~/.agate/` = 版本管理根目录：`repo/`（唯一主仓库）+ `vX.Y.Z/`（worktree 检出 tag）+ `latest`/`current` 纯指针 + `scripts/（版本管理工具）` |
| 升级 = `git pull` + hook 自动跟随 | 升级 = `python3 ~/.agate/scripts/agate-install.py`（装最新版，指针切到新版本目录） |
| 卸载 = `rm ~/.agate` + 删仓库 | 卸载 = `python3 ~/.agate/scripts/agate-install.py --uninstall vX.Y.Z`（含引用保护：仍有项目锁定该版本时拒绝卸载） |

> **本表为版本历史叙事，不再单独维护**：上表「根含 `scripts/`」一行的副本维护语义（决策 B1：随 `agate-install.py latest`
> 重跑刷新、`repo/` 被删不影响可用性）、「升级 = `agate-install.py`」一行的幂等 `agate-install latest` 更新口径，
> 均以本文件「版本管理生命周期」节为准。

- **存量单软链用户不跑新工具时行为不变（红线，BDD-30）**：`~/.agate` 仍是软链 → 旧 checkout 的 `agate/` 子目录，无版本目录/无指针时，resolve 直接把软链目标解析为 AGATE_ROOT，hook 照常按既有语义运行——**无迁移动作即可继续用**，gate 不静默禁用。
- **`install.sh` 兼容保留**：单软链场景仍可用，不破坏存量升级路径。

**② `.agate-version` 项目级版本锁定（新机制，可选）**：

- 项目根放 `.agate-version`，内容 `agate: v0.43.0`（v1 只支持精确版本，asdf 模式 cwd 向上找）。
- 声明版本后该项目 commit 用**该版本**的 gate 逻辑判定；改声明即生效，**不用重装 hook**。
- 声明版本未安装 / 格式非法（含空文件）→ stderr 警告 + 回退 current（**绝不静默禁用 gate**）。
- 不声明 = 用全局 `current`（默认 → latest = 最新发布版），与旧行为等价。

**③ hook 解析入口迁移（机制内部，用户无需重装 hook）**：

- `install-hook.py` 现在安装**固定解析入口** `resolve-entry.py`（不随版本变）到 `.git/hooks/`，运行时读项目 `.agate-version` → exec 对应版本 gate py。
- **符号链接模式（Linux/macOS 标准）**：升级后 hook 自动跟随新解析入口，无需重装。
- **复制模式（Windows 无符号链接权限）**：hook 是复制品，不自动跟随 → **必须重跑** `python3 ~/.agate/scripts/install-hook.py`（复制模式 + `.agate-root` 标记保留）。
- AGATE_ROOT env 显式覆盖仍是最高优先级（既有契约未破坏）。

**④ 新工具（可选使用）**：

- `agate-install.py`：安装/卸载/环境探测（`--check` 输出 python3/pyyaml/git/bash 探测结果，exit code 可判 + 分平台修复指引）。
- `agate-resolve.py`：解析项目实际使用的版本（输出 AGATE_ROOT/AGATE_VERSION/AGATE_REASON）。
- `agate-pack-offline.py` + `install-offline.py`：外网打包 → 内网离线安装闭环（平台核对 + checksum 校验 + 版本目录 + hook 指向）。**信任边界（TAG0031 DEBT0003）**：checksum 校验只防损坏（传输/存储过程中的位翻转、截断等意外错误），**不防**恶意构造的整包替换——攻击者若能替换整个 bundle（同时重算并写入匹配的 manifest sha256），checksum 校验会照常通过。因此 bundle 提供者需可信（内网分发渠道本身要可控），checksum 通过不代表来源可信，只代表"文件内容与 manifest 一致"。

**⑤ agate-summary 语义变化（显示层，提示文案变更）**：`agate-summary.py` 不再显示仓库自身 tag，改为显示**当前项目解析到的版本 + 原因**（`.agate-version` 或全局 current）——排障时直接可见"项目用哪个版本、为什么"。

**迁移动作小结**：
- 存量单软链用户：无强制迁移（legacy 兜底，BDD-30）。
- 想用版本隔离：跑 `python3 ~/.agate/scripts/agate-install.py` 装最新版 → 项目加 `.agate-version` → 重跑 `install-hook.py`（Windows 复制模式必须重跑）。
- 已验证：31 条 BDD 全 PASS（含 BDD-30 存量软链不受破坏红线）。

### v0.49.0 — 派发编排机制（无破坏性变更）

> 实现注记：本段为版本升级记录（派发编排机制变更史）——`task-files.md` 为协议文件名（既有
> 文档引用），出现的 task 词是文件/机制引用而非平台工具指代，属历史叙事元信息（升级说明元信息
> 判定），非协议语义定义。

**本版本无破坏性变更，无需迁移动作。**

- 新增 `dispatch_plan:` **可选**机器字段（P2-design.md frontmatter 单行 flow YAML，mode/batches/parallel_limit）——缺字段 / 坏 YAML 时 P2 gate 跳过校验，既有任务行为与改造前完全一致（向后兼容）。
- `dispatch-protocol.md`「任务粒度指引」节升级为「派发编排机制」权威节（五维工作量评估 + 五模式编排 + 模式 4 流程 + 并行规则 + 全阶段适用表）；既有引用点（L118/L132/L211 + task-files.md）措辞同步更新，锚点位置不变，一致性 CHECK 3 零漂移。
- 已有项目升级：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS 符号链接模式自动跟随，不放心可重跑确认；Windows 复制模式必须重跑）。

### v0.48.0 — 脚本一致性 gate（无破坏性变更）

**本版本无破坏性变更，无需迁移动作。**

- 新增 CHECK 10「协议文档脚本名引用漂移」一致性检查（增量，当前 0 漂移），self-gate 触发面补 README/AGENTS（内部行为），check-retrospective 追加登记提醒行（纯提醒）——用户可见协议语义不变。
- 已有项目升级：`git pull` + 重跑 `python3 ~/.agate/scripts/install-hook.py`（Linux/macOS 符号链接模式自动跟随，不放心可重跑确认；Windows 复制模式必须重跑）。

### v0.45.0 — backend 域 P2 评审触发 + 平台假设扫描器（影响：所有已部署项目）

**① backend 域任务 P2 现强制派发方案评审（plan-eng-review）**（RM-AG0010）：
- C8 映射表 backend 行新增 `plan-eng-review（P2 方案评审）`（保留 `review（P4 后）`）。**所有 backend 域任务（含 low/medium）P2 阶段现在必须派发一个 plan-eng-review 评审 subagent 产 P2-review.md**，否则 check-gate.py P2 会 exit 1 拦截。
- 这是「P2 gate 无条件要求 P2-review.md」契约矛盾的对齐——之前 backend low/medium 任务按 C8 不派评审被 gate 拦截、主 Agent 被迫自造评审（TPV0090），现在契约一致了。
- 同任务命中多个触发行且同一评审角色时去重只派一次（backend+high 均命中 plan-eng-review → 只派 1 个）。

**② 新增平台假设静态扫描器（测试基建，影响：测试套件维护者）**：
- 新增 `agate/scripts/check-platform-assumptions.py` 扫描 `agate/tests/` 全树 Unix 假设（硬编码 PATH / 裸 python3 / `[[ -L ]]` / /tmp / bc 等），CI `platform-scan` job 阻断。
- **测试平台无关原则是硬要求**：写新测试不得硬编码单平台假设（AGENTS.md「测试约定」）；被扫描器检出的假设会导致 CI 失败。

**③ bats job 增 windows-latest matrix（CI 维护者，TAG0011 后为 pytest job）**：bats job 改 matrix 后 job 名带平台后缀（如 `bats (windows-latest)`，TAG0011 起 pytest job 同名规则 `pytest (windows-latest)`），分支保护 required checks 需更新。

**④ P5 gate_commands 计数语义**：check-gate.py P5 WARNING 文案改「X 个主命令 + Y 个辅助命令」——不影响判定逻辑，仅文案区分主/辅。

### v0.44.0 — 脚本健壮性 + Windows 环境适配（影响：所有已部署项目）

> 实现注记：本段为版本升级记录（Windows 环境适配/CI matrix 变更史）——Windows、CI 平台 job 名
> （windows-latest 等）是记录对象本身，属历史叙事元信息（升级说明元信息判定），非协议语义定义；
> 不删改历史事实。

**① Windows 用户**：agate 现在支持 Git for Windows/MSYS2 下运行 gate 脚本（Windows 原生兼容）。
- 依赖：Git for Windows（自带 bash/coreutils），python3 + pyyaml，Git Bash 作为执行 shell。
- 见 `SETUP.md`「Windows 原生」章节（AGATE_ROOT 用 Unix 风格路径 `/c/...`、`PYTHONUTF8=1`、`core.autocrlf` 与 CRLF）。
- 若你的 hook 是复制模式安装（无符号链接权限），升级后**重跑 install-hook.py** 更新 hook。

**② 非 Windows 用户**：本版本为修复型，Linux 行为不变（676→714 bats 全绿回归，bats 时代基线）。无需迁移动作。

**③ CI matrix（项目维护者）**：`.github/workflows/protocol-tests.yml` 新增 `windows-latest` 平台矩阵（bats/shellcheck/consistency/gate-backstop；TAG0011 起 bats job 改 pytest job）。分支保护 required checks 需更新为实际 job 名（含平台后缀，如 `shellcheck (ubuntu-latest)`）——若你 fork/自建 CI 参考了 agate 的 workflow，注意此点。

**④ 路径含空格/特殊字符的项目**：`pre-commit-gate.sh` 内部数组化（S1 修复）——路径含空格/`[`/`]`/`*` 时 gate 不再静默绕过。行为更严格但更正确。

**⑤ 中文证据文件名（P6 任务）**：check-p6-evidence.py 证据引用正则加宽，中文文件名正确匹配。之前因中文证据名被误拦的项目现在可正常通过。

**⑥ 阶段卡片 phase 语义（文档，无强制）**：P1/P2/P3/P4/P6/P7/P8 卡片补注"commit 时 phase = 本 commit 产出阶段"。仅文档说明，gate 判定逻辑零改动，遵循既有习惯即可。

### v0.43.0 — 技术债登记闭环 + 工作区子目录 8→9（影响：进行中任务 + 已部署项目）

**① 工作区子目录集 8→9（新增 `debt/`，可选启用）**：
- 工作区目录集从 8 个扩为 9 个（roadmap/tasks/agents/archived/reviews/decisions/plans/logs/**debt**），`debt/` 为技术债登记目录。
- 存量项目**无需迁移动作**：技术债登记是新增可选机制，不建 `debt/` 时行为不变（校验器/回退比对/P8 留痕在无 tech-debt.md 时 no-op）。要启用技术债登记，运行 `mkdir -p {AGATE_WORKSPACE}/debt`。
- 归类修正：tech-debt 不再归入 `agents/`（该目录只放 agent 输入知识 project.md/memory）；`{AGATE_WORKSPACE}/agents/` 若已有 tech-debt.md，可手动移到 `{AGATE_WORKSPACE}/debt/tech-debt.md`。

**② tech-debt.md 路径**：技术债登记文件位于 `{AGATE_WORKSPACE}/debt/tech-debt.md`（模板 `assets/templates/tech-debt-template.md`），不再指向 agents/。

**③ P8-release.md 新增 `debt_check` 必填字段**：发布准备阶段确认债务清单并留痕（`none` = 本次无关注项 / `reviewed` = 已核对）。check-gate.py P8 分支对缺失该字段的 P8-release.md 硬拦截（exit 1）；字段存在则内容任意放行（不阻断发布）。

**④ 回退落地后必须建 DEBT 条目**：任何正式回退（`retreat:` 提交）完成后必须建立 `source: retreat` 的 DEBT 条目（`evidence` 引用 retreat 提交哈希）。`check-debt.py --retreat-coverage` 会把未登记的 retreat 提交比对出来并报 WARNING（只读提醒，不挂 gate）。

### v0.41.0 — 工作区架构（docs/tasks → agate-workspace/）（影响：所有已部署项目 + 进行中任务）

**背景**：agate 的全部编排状态（任务/看板/归档/评审/决策/计划/日志/roadmap/agent 知识）从项目 `docs/tasks/`、`docs/agents/`、`docs/archived/` 迁移到**工作区**（默认项目根 `agate-workspace/`，可用 `.agate.env` 配置位置）。orchestrator 从工作区读取 project.md 与 active-tasks，不再读 `docs/` 下旧路径。

**① 迁移工具（推荐）**：在项目根运行

```bash
python3 {agate_root}/scripts/agate-migrate-workspace.py
```

**迁移前先处理暂存区**：迁移工具会自动 commit 目录 rename（保留 git 历史），commit 用 pathspec 限定只提交迁移目录，不会带上迁移前已暂存的无关改动——但为避免状态混乱，建议先 `git commit` 或 `git unstage`（`git reset`）掉无关的已暂存改动，让暂存区只含迁移内容。

工具自动完成：
- `docs/tasks/`（含 active-tasks.md + 全部任务目录 + 被 gitignore 的 `.state.yaml`）→ 工作区 `tasks/`（git mv 目录级，保留 git 历史）
- `docs/archived/` → 工作区 `archived/`
- 空源 no-op（项目从无 docs/tasks 时正常退出）
- 幂等：重复运行无新增动作

迁移后验证：`ls {AGATE_WORKSPACE}/tasks/` 应包含 active-tasks.md 与任务目录；`python3 {agate_root}/scripts/agate-summary.py` 正常。

**② 手工迁移（不用工具时）**：`git mv docs/tasks {AGATE_WORKSPACE}/tasks`、`git mv docs/archived {AGATE_WORKSPACE}/archived`；`.state.yaml` 若被 gitignore 需 `git add -f` 后随目录移动。

**③ 项目侧文件位置变化**：
- `docs/agents/project.md` → `{AGATE_WORKSPACE}/agents/project.md`（模板 `assets/templates/project.md`）
- `docs/tasks/active-tasks.md` → `{AGATE_WORKSPACE}/tasks/active-tasks.md`（非本仓：使用者项目旧路径）
- 项目 README 等产品文档**留在**项目 `docs/` 不动（内容边界判据：编排状态进工作区，产品文档留项目 docs/，见 WORKFLOW.md「内容边界判据」）

**④ 未迁移时的行为**：orchestrator 启动检测到旧布局（`docs/tasks/active-tasks.md` 存在而工作区 tasks 无 active-tasks，非本仓：使用者项目旧路径）→ 输出迁移指引并停止自动推进，不静默使用旧路径。

**⑤ 外部工作区**：`.agate.env` 指向项目外路径时，git mv 无法跨仓库（fallback 普通 `mv` + WARNING「git 历史无法在新路径追溯」）。

### v0.40.0 — 任务编号硬切 + orchestrator 符号链接接入（影响：进行中任务 + 已部署项目）

**① 任务编号硬切**：
- `task_id` 从 `T\d+` 硬切为 `T[A-Z]{2}\d+`（如 `TAG0001`），**不兼容旧格式**
- 影响：进行中任务的 `.state.yaml` 必须改编号；已完成任务不受影响
- 迁移见上文 2.2

**② orchestrator 从拷贝改为符号链接接入**（对已部署项目影响最大）：
- 旧方式：把 `orchestrator-template.md` 拷贝到项目并手改字段
- 新方式：**删除旧拷贝文件 `docs/agents/orchestrator.md`（若存在）**，按 `SETUP.md` 重新建立符号链接（`.claude/agents/orchestrator.md` / `.opencode/agents/orchestrator.md` 直接指向 `~/.agate/orchestrator-template.md`）
- 原来内联在 orchestrator.md 里的项目特定约束，迁移到新建的 `docs/agents/project.md`（模板见 `assets/templates/project.md`）
- 影响：不迁移则 orchestrator 仍是旧拷贝，不跟随新版本

### v0.31.0 — P2 必填 candidate_count 字段（影响：P2 设计阶段）
- `P2-design.md` 必须显式声明 `candidate_count: N`（替代正则数标题）
- 影响：新任务的 P2 产出需含该字段；旧任务若重新走到 P2 需补

### v0.17.0 — 标记格式收紧（影响：产出文件标记写法）
- `[PROD_TOUCHED]`/`[NEED_CONFIRM]` 必须行首声明，句中引用会被拦截
- `无 [PROD_TOUCHED]` 等否定写法不再接受，须用 `[PROD_NOT_TOUCHED]`
- 影响：写 dispatch-context/产出文件时标记要行首

### v0.29.x 及更早
- 如需了解，查 `CHANGELOG.md` 对应版本

---

## 4. 升级后验证

```bash
# 1. 版本
python3 ~/.agate/scripts/agate-summary.py

# 2. 协议一致性（0 ERROR）
python3 ~/.agate/scripts/check-protocol-consistency.py

# 3. 进行中任务的 .state.yaml 能通过校验
cd <项目目录>
git add {AGATE_WORKSPACE}/tasks/{进行中任务}/.state.yaml
# 触发 pre-commit → 应无"task_id 格式错误"
git reset   # 取消暂存
```

---

## 5. 常见问题

**Q: 旧任务目录会导致升级后报错吗？**
A: 不会——只要不暂存它的 `.state.yaml`。consistency 不查 .state.yaml 格式，pre-commit 只在暂存时校验。旧任务目录会由迁移工具迁入工作区，未迁移时 orchestrator 会输出迁移指引。

**Q: 必须把旧任务编号都改成 TAG0001 吗？**
A: 只有"继续进行中的"必须改。已完成/归档的保留旧编号即可。

**Q: 复制模式（Windows）升级后 orchestrator 提示词是旧的？**
A: 是——复制模式不自动同步，需重跑 SETUP.md 步骤 2 的 `cp`。软链模式无此问题。
