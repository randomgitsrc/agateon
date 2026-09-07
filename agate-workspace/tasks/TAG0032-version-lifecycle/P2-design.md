---
phase: P2
task_id: TAG0032
type: design
parent: P1-requirements.md
trace_id: TAG0032-P2-20260907
status: draft
created: 2026-09-07
agent: architect
candidate_count: 4
packages: [agate-scripts, agate-docs, agate-tests]
domains: [backend, cli]
ui_affected: false
dispatch_plan: {mode: serial, parallel_limit: 1, batches: [{id: scripts-tests, complexity: high}, {id: docs-consistency, complexity: medium}]}
---

# P2-design — TAG0032 版本管理生命周期可用性批（RM-AG0058 整合 epic）

[PROD_NOT_TOUCHED]

把 P1 的 14 条 BDD 转成可实现技术方案。核心是两处「二选一」实现方向决策（决策 A / 决策 B），
外加断点一 fail-closed + 迁移指引、`install.sh --versions`、UPGRADING 生命周期节、端到端 fixture。

> `candidate_count: 4` = 决策 A 的候选 A1/A2 + 决策 B 的候选 B1/B2。BDD-5 / 生命周期节 / 端到端
> fixture 是既定行为的落地设计（非「二选一」），写在「§4 其他覆盖点」，不计入候选数。

---

## §1 影响面梳理（写在候选方案之前）

梳理接续 P1 §4 同类扫描四类结论，本节做**候选方案级**影响域分析。证据 = 本次 grep 命中清单
+ 读过的消费方代码（见文末 `files_to_read`）。

### 1.1 改什么（Modify）

| # | 文件:落点 | 改动内容 | 关联 BDD |
|---|-----------|----------|----------|
| M1 | `agate/scripts/agate-install.py` · `_cmd_install()`（L269-288，在 `_ensure_repo` 调用前）| 新增 legacy 软链 fail-closed 守卫：`os.path.islink(agate_home)` 为真 → stderr 三步迁移指引 + `sys.exit(1)`，**不建任何目录**（守卫在 `_ensure_repo` 的 `os.makedirs`/`git clone` 之前） | BDD-1, BDD-2, I-11 |
| M2 | `agate/scripts/agate-install.py` · `_cmd_install()` 成功路径末尾（`_install_version` + `_write_pointer` 之后，L277-286）| 新增根 `~/.agate/scripts/` 建立（决策 B = 副本）：把当前 current 版本协议 `scripts/`（源路径 = 决策 A 探测结果，`vdir` 或 `vdir/agate`）`shutil.copytree(src, agate_home/'scripts', dirs_exist_ok=True)`。装 latest / 指定版本两条路径都落地 | BDD-4, BDD-5, I-3, I-4 |
| M3 | `agate/scripts/agate_common.py` · 新增模块级 helper `_protocol_root(vdir)`（紧邻 `_resolve_version_info`，L166 前）| 探测顺序：`isdir(vdir/scripts)` → `vdir`（「根即协议」，探测序 1，红线）；否则 `isdir(vdir/agate/scripts)` → `vdir/agate`（元仓库形态，探测序 2）；两者皆无 → `vdir` 原样返回 | BDD-6, BDD-7, BDD-8, I-11 |
| M4 | `agate/scripts/agate_common.py` · `_resolve_version_info()` `.agate-version` ok 分支（L180-183）| `if os.path.isdir(vdir):` 命中后 `root = _protocol_root(vdir)`；`version` 恒取 `declared`（不受影响，I-1 天然安全）| BDD-6, BDD-7, I-1 |
| M5 | `agate/scripts/agate_common.py` · `_resolve_version_info()` current 链分支（L188-190）| `cur = _resolve_pointer_chain(base, "current")`；命中后**先算** `version = os.path.basename(cur)` **再** `root = _protocol_root(cur)`——顺序不可倒，否则 `version` 变 `"agate"`（I-1 红线）| BDD-6, I-1 |
| M6 | `install.sh`（仓库根，55 行）· 新增 `--versions` 分支 | `$1 == "--versions"` → 若 `~/.agate` 是软链则打同一三步迁移指引 + exit 1；否则 `mkdir -p ~/.agate` + `git clone <url> ~/.agate/repo` + `python3 ~/.agate/repo/agate/scripts/agate-install.py latest`（后者建 `vX.Y.Z/` + 指针 + 根 `scripts/`）。原单软链路径（无参）不变 | BDD-5 |
| M7 | `agate/UPGRADING.md` · 新增 `## 版本管理生命周期` 节（插在 `## 1. 通用升级步骤` 之后）| 安装/迁移/更新/回退对照表 + hook 重装时机口径 + 根 `~/.agate/scripts/` 副本维护语义条目（决策 B 语义） | BDD-10, BDD-11, BDD-12 |
| M8 | `agate/UPGRADING.md` · v0.50.0 节 §① 表格（L543-553）| 「根含 `scripts/`」行 + 「升级 = agate-install.py」行：各加一句「详见『版本管理生命周期』节」指针，**不改历史叙事文字** | BDD-12 checklist 1/2 |
| M9 | `agate/UPGRADING.md` · v0.60.0/0.61.0/0.62.0 节（L280/L315/L377）与 v0.66-0.68 节 | 不逐条改写历史节；由 M7 生命周期节给「切版本/升级通常无需重跑 `install-hook.py`；仅 hook 薄壳 `.sh` 变更或 Windows 复制模式才重跑」统一口径 | BDD-12 checklist 3 |
| M10 | `README.md` L36-46 / `README.zh-CN.md` L36-46 · 快速上手「版本管理」块 | 补「进入版本管理布局」官方路径（`install.sh --versions`）；升级表述与生命周期节口径一致（版本布局 = `agate-install latest`） | BDD-5, BDD-12 checklist 4 |
| M11 | `agate/SETUP.md` L244-250 · 「## 升级 Agateon 之后」节 | 升级表述加指向 UPGRADING 生命周期节的指针，口径一致（legacy = `git pull`；版本布局 = `agate-install latest`） | BDD-12 checklist 4 |
| M12 | `agate/tests/unit/test_agate_version_install.py` | 新增 BDD-1~5 用例：软链 fail-closed（`os.symlink` 失败 → `pytest.skip`，同既有 `test_bdd_30`）/ 三步指引 grep / 普通目录不误伤 / 根 `scripts/` 就位 + `--help` exit 0 / 重跑 latest 后副本刷新（副本语义单测锁）/ `install.sh --versions` 隔离 HOME | BDD-1~5, BDD-9, I-3 |
| M13 | `agate/tests/unit/test_agate_version_resolve.py` | 新增双 fixture：`_make_home_meta`（`~/.agate/vX/agate/scripts/` 建、`vX/scripts/` 不建）+ `_make_home_rootproto`（`vX/scripts/` 直建）；BDD-6（meta → `AGATE_ROOT` 结尾 `/vX/agate` + `AGATE_VERSION=vX`）/ BDD-7（rootproto → `AGATE_ROOT` 结尾 `/vX` + `AGATE_VERSION=vX`） | BDD-6, BDD-7, BDD-9, I-1, I-5 |
| M14 | `agate/tests/unit/test_hook_resolve_entry.py` | 新增 meta fixture 版 BDD-8：`resolve-entry.py pre-commit` → exit 0 + gate 路径 `vX/agate/scripts/pre-commit-gate.py` 被 exec（stub gate 打 marker） | BDD-8, BDD-9 |
| M15 | `agate/tests/integration/test_version_lifecycle_e2e.py`（新增）| 端到端：隔离 HOME + 本地构造元仓库形态 git repo 经 `AGATE_REPO_URL` 注入 → `install.sh --versions` → 钉 `.agate-version` → `resolve-entry.py pre-commit` → 再 `agate-install.py latest` 验幂等；worktree `git status --porcelain` 无污染断言 | BDD-13, BDD-14, I-5, I-6 |

### 1.2 不改什么（Not Modify）

| 范围 | 决定不改 | 理由（含证据） |
|------|----------|----------------|
| `agate/scripts/resolve-entry.py:49` `os.path.join(root, "scripts", gate_py)` | 只核对不改 | 决策 A1 让 `root` 返回 `vdir/agate` 后此拼接自然命中 `vdir/agate/scripts/`（受益方）。gate 缺失分支 `:50-52` fail-closed exit 1 保留（I-11）。grep 确认无 `os.path.dirname(vdir)` 旁路 |
| `agate/scripts/agate_common.py:216-228` `resolve_hook_root` 脚本上溯兜底 | 不改 | 仅 `info["root"] is None` 时进入；决策 A1 不改该终态语义，`_protocol_root` 只在 `root` 已是有效版本目录时作用 |
| `agate/scripts/agate_common.py:173-175` `AGATE_ROOT` env 覆盖分支 | 不改 | 既有最高优先级契约（BDD-12 env override）；元仓库探测只在「无 env 覆盖」时生效 |
| `agate/scripts/agate_common.py:192-193` legacy 软链兜底分支 | 不改 | `os.path.realpath(base)` 已直接指向 `<checkout>/agate`（根含 `scripts/`），`_protocol_root` 对其返回原值，无需特判 |
| `.agate-version` 声明格式 / `_find_project_declaration`（L99）查找语义 | 不改 | I-9：格式恒为 `agate: vX.Y.Z`；适配在归口下游（`vdir` → `_protocol_root`），不碰声明解析 |
| `agate-install.py` 卸载路径 `_cmd_uninstall`（L290-328）/ 指针机制 `_write_pointer` | 不改 | 断点一只涉及 install 路径穿透；卸载不新建 `~/.agate` 根，无软链穿透语义（P1 §4 扫描 1） |
| `install-offline.py:204` `shutil.copytree(dirs_exist_ok=True)` / `agate-pack-offline.py` 打包侧 | 不改 | out-of-scope「install-offline 离线链路适配」。同源穿透模式的同类实例，转 roadmap 候选（断点一 helper 可复用）；解析侧因共用 `_resolve_pointer_chain` 自然受益（I-7） |
| Windows 复制模式 `.agate-root` marker（`install-hook.py:125` / `agate_common.py:222`）| 不改 | out-of-scope「Windows 复制模式专项」。经同一 `_resolve_pointer_chain`，A1 探测自然覆盖其解析侧（I-7，P1 §4 扫描 3） |
| `.state.yaml` schema | 不改 | out-of-scope「.state.yaml schema 扩字段」（RM-AG0059 独立 epic） |
| agateon 仓库形态（把 `agate/` 提升为仓库根）| 不改 | out-of-scope「agateon 仓库形态重构」，影响面远超本任务；作为决策 A 的「不采纳备选」记录（见 §2） |
| `agate/scripts/agate-summary.py:140` / `agate-resolve.py:31,40` 输出逻辑 | 不改代码，只核对 | 消费 `info["version"]` 显示 `AGATE_VERSION`；M4/M5 保 `version` 仍为 `vX.Y.Z` 后这两处输出自动正确（BDD-6）。新增断言用例即回归锁 |
| 编排/派发类（`agate-dispatch.py` / `agate-inject-card.py` / `agate-next-card.py` / `agate-render-dispatch-prompt.py`）| 不改 | P1 §4 扫描 2：按项目约定走 `~/.agate` 稳定版解析，不经版本链；`root=vdir/agate` 后子目录拼接仍自然命中，无破坏。列出备 P8 一致性核对 |

### 1.3 风险在哪（Risk）

| # | 风险 | 缓解 |
|---|------|------|
| R1 | **决策 A1 · `version` 推导顺序倒置**：current 链分支若先拼 `/agate` 再算 `basename`，`AGATE_VERSION` 从 `vX.Y.Z` 回归为 `agate`（I-1 红线）| M5 明确「先算 `version=os.path.basename(cur)` 再 `_protocol_root(cur)`」；BDD-6/7 双 fixture 用例逐条断言 `AGATE_VERSION=vX.Y.Z`；P7 一致性检查核对该顺序 |
| R2 | **决策 A1 · 探测顺序颠倒**：若先探 `vdir/agate/scripts` 会让某些「根即协议」且恰好含 `agate/` 子目录的部署方被改判 → 破坏纯增量红线（BDD-7）| `_protocol_root` 硬编码「`vdir/scripts` 先」；BDD-7 用例用 rootproto fixture 断言不进 `/agate` 分支；探测顺序在 helper 单点，无散落 |
| R3 | **DEBT0016 dirname 散点复发**：新增解析旁路绕过 `_resolve_version_info` 归口 | grep 复核（见 §5 minimal_validation note 2 与 files_to_read）：所有 `resolve_*` 消费方 + `check-structure-consistency.py:528/545` 均经归口，无 `os.path.dirname(vdir)+"/scripts"`；BDD-9 全量 pytest（双 fixture 常驻）为回归锁 |
| R4 | **决策 B 副本漂移**：升级后未重跑 `agate-install.py latest` → `~/.agate/scripts/` 停在旧版本工具 | 维护语义写入 UPGRADING 生命周期节（M7，BDD-11 判据 3）；BDD-4 判据 2 单测锁「重跑 latest 后副本随 current 刷新」；判据 3 交叉锁「用例断言 ↔ UPGRADING 一致」 |
| R5 | **断点一守卫误伤**：普通目录 / 全新机器被 fail-closed 拦 | `os.path.islink` 对普通目录与不存在路径均为 `False`；BDD-3 用例专测「普通目录 / 全新 → exit 0」 |
| R6 | **文档双源同步**：UPGRADING v0.50.0 表格 + README×2 + SETUP 四处「升级 / 根含 scripts/」表述漂移 | M7 生命周期节作单一真相源；M8-M11 逐处加指针不改历史叙事；BDD-12 checklist 四条二值断言 + `check-protocol-consistency.py --strict-errors-only` 附加回归项（基线 0 ERROR 已实测） |
| R7 | **端到端 fixture 形态错**：用「根即协议」模拟 repo 测不出元仓库 gap（TAG0008 教训 I-5）| M15 fixture 强制元仓库形态（协议在 `agate/` 子目录、根无 `scripts/`）+ 保留 rootproto 对照 fixture；BDD-13 CI 无网 → skip + 本地补证 P6-evidence（I-6） |
| R8 | **`install.sh --versions` 平台假设**：`git clone` / 目录操作在 Windows Git Bash 下差异 | M6 复用既有 `install.sh` 的 POSIX shell 约束（已 shellcheck 干净）；`--versions` 只加 `git clone` + 调 `agate-install.py`（后者已平台无关）；新增 shellcheck gate 覆盖 `install.sh`（见 §3 `P5_shellcheck_root`） |
| R9 | **`shellcheck` gate 不覆盖 `install.sh`**：固化命令 `shellcheck -S warning agate/scripts/*.sh` 不含仓库根 `install.sh`，M6 改动无 gate | §3 新增 per-key `P5_shellcheck_root: "shellcheck -S warning install.sh"`（基线实测 rc=0） |
| R10 | **worktree git 一致性**（针对被否的 A2）：移动/复制 `vX/agate/` 破坏 git worktree 索引 | 选 A1 规避——A1 不动 `~/.agate/vX/` 目录内容，只在解析时探测 |

---

## §2 决策 A — 元仓库 gap 修复方向（BDD-6/7/8，I-1）

### 候选 A1 — resolve 侧增量探测（`_resolve_version_info` 命中版本目录后按探测顺序定位协议根）

新增 helper `_protocol_root(vdir)`（`agate_common.py`，紧邻 `_resolve_version_info`）：

```python
def _protocol_root(vdir):
    """版本目录命中后定位协议根：根即协议（探测序 1）→ 元仓库形态（探测序 2）→ 原样。"""
    if os.path.isdir(os.path.join(vdir, "scripts")):
        return vdir                                  # 「根即协议」部署方，红线：先命中
    sub = os.path.join(vdir, "agate")
    if os.path.isdir(os.path.join(sub, "scripts")):
        return sub                                   # 元仓库形态（agateon 整仓）
    return vdir                                       # 两形态皆无 → 原样，下游维持既有 fail-closed
```

消费点两处（`_resolve_version_info` 内）：
- `.agate-version` ok 分支（L182-183）：`root = _protocol_root(vdir)`，`version = declared`（不变）。
- current 链分支（L188-190）：**先** `version = os.path.basename(cur)`，**再** `root = _protocol_root(cur)`。

env 覆盖分支、legacy 软链兜底分支、`resolve_hook_root` 脚本上溯兜底 **均不改**。

**权衡**：
- 优点：① 纯解析侧增量，单点归口（1 helper + 2 调用），回滚 = 删调用；② `~/.agate/vX/` 目录内容零变形——不碰 git worktree 一致性（对比 A2 的 R10）；③ 离线包 / Windows 复制模式解析侧经同一 `_resolve_pointer_chain` → `_resolve_version_info` 自然受益（I-7），无需在多条安装路径复制逻辑；④「根即协议」部署方由「探测序 1 先」直接零回归（BDD-7）。
- 风险：① `version` 推导顺序（R1）——缓解见 M5 + BDD-6/7；② 每次解析多 1-2 次 `os.path.isdir`——可忽略（解析非热路径）。
- 工作量：小。`agate_common.py` +~10 行；`resolve-entry.py` / `agate-resolve.py` / `agate-summary.py` 零改动（受益方）。

### 候选 A2 — install 侧一次性变形（worktree 检出后把 `vX/agate/` 提升为版本根）

`agate-install.py._install_version()`（`_worktree_add` 之后）：若 `isdir(version_dir/agate/scripts)` 且
`not isdir(version_dir/scripts)` → 把 `version_dir/agate/*` 提升到 `version_dir/`（move 或 copy）。resolve 内核不改。

**权衡**：
- 优点：① resolve 内核零改动；② 版本目录形态统一为「根即协议」，全部下游消费方无感；③ 概念直白（装完即规范形态）。
- 风险：① **git worktree 一致性**（R10）——`version_dir` 是 `git worktree add --detach` 检出，move/删 `agate/` 子目录使 worktree 与 `repo/` 索引不一致，后续 `git worktree prune/remove/list`（`agate-install.py` 卸载路径 L316-324 依赖）可能误判或报错；② **一次性变形要在每条安装路径复制**——`install-offline.py`（`copytree`）、Windows 复制模式各有独立落地逻辑，A2 被迫触及 out-of-scope（违反范围锁定）；③ 幂等复跑（`agate-install.py latest`，BDD-13 判据 5）需额外「已提升」状态检测分支；④ 形态判别（元仓库 vs 已是根即协议的上游源）复杂度不亚于 A1 的探测；⑤ move 破坏 git 索引 / copy 磁盘翻倍且仍留 `agate/` 原件需清理；⑥ 回滚困难（已提升目录难还原判断）。
- 工作量：中-大，且外溢 out-of-scope。

### 决策 A：选 **A1（resolve 侧增量探测）**

理由：A1 是**解析侧最小增量 + 单点归口**，天然覆盖离线 / 复制模式解析侧（I-7），「根即协议」零回归由探测顺序直接保证（纯增量红线不可违反）。A2 触碰 git worktree 一致性（R10），且被迫在多条安装路径复制变形逻辑（撞 out-of-scope「install-offline 适配」/「Windows 复制模式专项」），风险与工作量显著更高。

**不采纳的备选（记录理由）**：agateon 仓库形态重构（把 `agate/` 提升为仓库根）——一次性根治元仓库 gap，但影响面远超本任务（所有引用 `agate/` 路径的文档 / CI / 脚本 / 下游项目），P0-brief 明列 out-of-scope。

**纯增量红线核对（无论 A 选哪个）**：本决策选 A1 —「根即协议」部署方 `_protocol_root` 探测序 1（`vdir/scripts`）先命中，返回 `vdir` 不变；探测顺序 `vdir/scripts` 先、`vdir/agate/scripts` 后（M3）；不改 `AGATE_ROOT` env 覆盖契约、不改 `.agate-version` 格式、不改既有解析语义。

---

## §3 决策 B — 根 `~/.agate/scripts/` 建立方式（BDD-4/11，I-3）

### 候选 B1 — 副本（install 时 `copytree` 当前版本协议 `scripts/` → `~/.agate/scripts/`）

`agate-install.py._cmd_install()` 成功路径末尾：`src = <当前 current 版本协议根>/scripts`（协议根 = 决策 A1
探测结果，`vdir` 或 `vdir/agate`），`shutil.copytree(src, os.path.join(agate_home, "scripts"), dirs_exist_ok=True)`。
`agate-install.py latest` 重跑 → `dirs_exist_ok=True` 刷新副本 → 跟随 current 版本。

**权衡**：
- 优点：① 无软链依赖 → Windows 无退化问题，跨平台**语义单一**；② `~/.agate/scripts/` 是实体目录——`repo/` 或某 `vX.Y.Z/` 被手动删不影响已建副本的入口可用性（直接规避 I-3 点名的「repo 删则断」）；③ 与 resolve-entry 固定入口机制**正交无耦合**（hook 仍按 `.agate-version` 解析版本，`~/.agate/scripts/` 只承载「新机入口命令存在」）；④ 语义直白：「装完 / 升级后 `~/.agate/scripts/` = 当时 current 版本工具副本」。
- 风险：① 升级期须重跑 `agate-install.py latest` 才刷新副本（R4）——缓解：写入 UPGRADING 生命周期节（M7）+ BDD-4 判据 2 单测锁；② 副本漂移（用户手改副本文件）——非本任务范围，`agate-summary.py` 已有漂移检测思路；③ 多一份磁盘副本（`scripts/` 体量小，可忽略）。
- 工作量：小。`agate-install.py` +~6 行。

### 候选 B2 — 软链（`~/.agate/scripts` → 当前 current 版本协议 `scripts/`；Windows 退化为复制）

POSIX `os.symlink`（同 `_write_pointer` 既有二态模式）；`os.name == "nt"` → `copytree` 退化。
`agate-install.py latest` 切 current 指针时一并重指该软链。

**权衡**：
- 优点：① 跟随 current 指针自动切换，升级期无需额外 copy（POSIX）；② 零副本漂移（软链无内容）；③ 与 `latest`/`current` 指针形态一致。
- 风险：① **`repo/` 或被指向版本目录被删 → 软链悬空 → `~/.agate/scripts/agate-install.py` No such file**——回到断点一的死路，正是 I-3 点名的「repo 删则断」，且这正是本任务要消灭的症状；② Windows 退化为复制后行为等同 B1 但升级期又需重跑 → **跨平台双口径**（POSIX 自动跟随 vs Windows 需重跑），UPGRADING 要写两套；③ 软链目标（元仓库形态下是 `vX/agate/scripts/`）计算须与决策 A1 探测结果一致 → 与 A1 耦合；④ 只 `agate-install.py vX.Y.Z`（无指针）时软链无目标可指。
- 工作量：小-中（含 Windows 退化分支 + 双口径文档）。

### 决策 B：选 **B1（副本）**

理由：跨平台语义单一（不分 POSIX/Windows 两套口径）；`repo/` 或版本目录被删不断入口（直接规避 I-3「repo 删则断」，而这正是断点一要消灭的症状）；与 resolve-entry 固定入口机制正交无耦合。B2 的「自动跟随」优点被「悬空断链 + 跨平台双口径 + 与 A1 耦合」抵消。B1 的代价（升级期重跑 install 刷新）明确、可单测锁、可写入 UPGRADING。

**所选维护语义（写入 UPGRADING「版本管理生命周期」节，M7；BDD-4 判据 2/3 + BDD-11 判据 3）**：
> 根 `~/.agate/scripts/` = `agate-install.py` 从当前 current 版本协议 `scripts/` 复制的**副本**。
> - 升级（`agate-install.py latest`）会一并刷新该副本 → **升级期须重跑 `agate-install.py latest`** 使根入口指向新版本工具。
> - `repo/` 或某个 `vX.Y.Z/` 版本目录被手动删除**不影响**已建立的 `~/.agate/scripts/` 副本可用性（副本是实体，不依赖被删目录）。
> - 该副本**不参与 hook 版本解析**——hook 经 resolve-entry 固定入口按项目 `.agate-version` 解析版本，切版本无需重跑 install。

---

## §4 其他覆盖点（既定行为的落地设计，非「二选一」）

### 4.1 断点一 fail-closed + 三步迁移指引（BDD-1/2，I-11）

`agate-install.py._cmd_install()` 首行（`_ensure_repo` 之前）守卫：

```python
if os.path.islink(agate_home):
    sys.stderr.write(
        "错误: ~/.agate 是 legacy 软链布局，agate-install 会穿透软链把 repo/ 与 vX.Y.Z/ "
        "静默建进源仓库，已拒绝（fail-closed）。\n"
        "迁移到版本管理布局（三步）：\n"
        "  1. 备份软链:  mv ~/.agate ~/.agate.bak\n"
        "  2. 建目录根:  mkdir -p ~/.agate\n"
        "  3. 装版本:    install.sh --versions\n"
        "               # 迁移完成后亦可: python3 ~/.agate/scripts/agate-install.py latest\n"
    )
    sys.exit(1)
```

- 守卫在 `os.makedirs` / `git clone` 之前 → 拒绝后不留半成品（不建 `repo/`、不建 `vX.Y.Z/`）（I-11、BDD-1）。
- stderr 三段命令片段满足 BDD-2 判据 1/2/3 同粒度 grep：`mv ~/.agate ~/.agate.bak` / `mkdir -p ~/.agate` /
  `install.sh --versions` + `agate-install.py latest`（带版本标识）。
- BDD-3：`os.path.islink` 对普通目录 / 不存在路径为 `False` → 不误伤。
- `_cmd_uninstall` 不新建 `~/.agate` 根，本次不加守卫（P1 §4 扫描 1）。

### 4.2 `install.sh --versions`（BDD-5）

M6：`install.sh` 加 `--versions` 分支——`~/.agate` 是软链则打同一三步指引 + exit 1；否则
`mkdir -p ~/.agate` + `git clone <DEFAULT_REPO_URL> ~/.agate/repo` + `python3 ~/.agate/repo/agate/scripts/agate-install.py latest`。
`agate-install.py._ensure_repo` 见 `~/.agate/repo/.git` 存在 → 复用（不重 clone）→ 建 `vX.Y.Z/` + 指针 + 根 `scripts/`（决策 B1）。
全程在 `~/.agate/`（普通目录，非软链）内 → 不在任何源仓库树内新建 `repo/` / `vX.Y.Z/`（BDD-5）。

**方式选择说明**（非候选方案）：`install.sh --versions` 优于「纯文档命令序列」——新机器只按 README + `install.sh`
即可，无需先有 `~/.agate/scripts/` 就能进版本布局（断点一的另一半死路）。M10 README 快速上手同步补该官方路径。

### 4.3 UPGRADING「版本管理生命周期」节结构（BDD-10/11/12）

M7 新增 `## 版本管理生命周期` 节（插在 `## 1. 通用升级步骤` 之后，不重排既有编号）：

1. **安装 / 迁移 / 更新 / 回退对照表**（两列：legacy 软链布局 / 版本管理布局）：
   | 动作 | legacy 软链布局 | 版本管理布局 |
   |------|-----------------|--------------|
   | 安装（新机）| `curl … install.sh \| bash` | `install.sh --versions` |
   | 迁移 | — | 三步：`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions`（与 install fail-closed 文案同源）|
   | 更新 | `cd <clone> && git pull`（hook 口径见下）| `python3 ~/.agate/scripts/agate-install.py latest`（**幂等**：重复执行不报错、不重复建版本目录、指针幂等切换）|
   | 回退 | `git checkout <旧 tag>` | `python3 ~/.agate/scripts/agate-install.py v<旧版本>` + 项目 `.agate-version` 钉旧版（或 current 指针切回）|
2. **hook 重装时机条目**（BDD-11 判据 2、BDD-12 checklist 3 统一口径）：
   > resolve-entry 固定解析入口机制下，切版本 / 升级**通常无需重跑 `install-hook.py`**；仅
   > hook 薄壳（`.sh`）本身变更或 Windows 复制模式才重跑。
3. **根 `~/.agate/scripts/` 维护语义条目**（BDD-11 判据 3、BDD-4 判据 3；= 决策 B1 语义块，§3 末尾）。

**BDD-12 checklist 四条收敛落点**：
1. v0.50.0 §① 表格「根含 `scripts/`」行 → 决策 B1 建根 `scripts/` 后表述成真（隔离 HOME 装完实测存在，与 BDD-4 判据 1 同源）→「已收敛到新口径」；M8 加指针不改叙事。
2. v0.50.0 §① 表格「升级 = agate-install.py」行 → M7 声明版本布局升级 = `agate-install latest` 幂等；M8 加「详见『版本管理生命周期』节」指针 →「已标注为版本历史叙事保留」。
3. v0.60-0.62 vs v0.66-0.68 hook 重装口径分歧 → M7 给统一判定口径；M9 历史版本节保留原叙事不逐条改写 → PASS。
4. README×2 L36-46 + SETUP L244 → M10/M11 三处口径与 M7 一致或加指针 →「已收敛到新口径」。
5. 附加回归项：`check-protocol-consistency.py --strict-errors-only` EXIT 0 / 0 ERROR（基线实测 0 ERROR，本任务不引入新 ERROR）。

### 4.4 端到端隔离 HOME 测试的元仓库形态 fixture（BDD-13/14，I-5/I-6）

M15 新增 `agate/tests/integration/test_version_lifecycle_e2e.py`：

- **fixture 形态**：本地构造**元仓库形态** git repo（复用 conftest `git_repo`）——含 `agate/scripts/`
  子目录（放真实 `resolve-entry.py` + `agate_common.py` + stub `pre-commit-gate.py` 打 marker）、
  `agate/rules/` 占位；根**无** `scripts/`；两次 commit + `vX.Y.Z` tag。经 `AGATE_REPO_URL` 注入
  （新增 helper `_tag_meta_upstream(git_repo)`，对比既有 `_tag_upstream` 只建 `agate/scripts/README.md` 无 gate 脚本）。
- **对照 fixture**：「根即协议」形态（`scripts/` 直接在 tag 根）——保留作 BDD-7 单元层对照（M13 `_make_home_rootproto`）。
- **隔离**：`HOME=$(mktemp -d)`（`HOME` + `USERPROFILE` 双 env，同 conftest `_resolve_env`）；`~/.agate` 为
  普通目录（非软链）。
- **链路**：`install.sh --versions`（或 `agate-install.py latest` + `AGATE_REPO_URL`）→ 项目写
  `.agate-version` 钉版 → `resolve-entry.py pre-commit`（断言 exit 0 + marker）→ 再 `agate-install.py latest`
  验幂等（`~/.agate/vX.Y.Z/` 数量不变、指针幂等）。
- **污染断言**（BDD-14）：worktree `git status --porcelain` 无新增 `repo/` / `vX.Y.Z/` / 非预期未跟踪条目。
- **CI 无网 fallback**（I-6）：本地构造 fixture 即默认路径（不依赖 GitHub）；真实 GitHub clone 是可选增强，
  无网 → 该增强断言 skip + 本地隔离 HOME 记录补证 P6-evidence。平台无关：`os.symlink` 仅 BDD-1/BDD-14
  的 legacy 软链场景需要 → 失败 `pytest.skip`（同 `test_bdd_30`）；`install.sh` 经 conftest `bash` fixture 调用。

---

## §5 批次设计（dispatch_plan）

`dispatch_plan: {mode: serial, parallel_limit: 1, batches: [{id: scripts-tests, complexity: high}, {id: docs-consistency, complexity: medium}]}`

- **mode: serial**（串行链，high 复杂度不单发）。理由：本任务三部分中「脚本 + 测试」深度耦合
  （TDD：P3 先写元仓库/根即协议双 fixture 失败测试 → P4 改脚本转绿，跨 install/resolve/entry 一条链，
  不可拆），「文档面」依赖脚本行为先落地（BDD-12 checklist 1「根含 scripts/」需 install 行为实测存在）。
- **批 1 `scripts-tests`（complexity: high）**：M1-M6（`agate-install.py` / `agate_common.py` /
  `install.sh`）+ M12-M15（unit 双 fixture + integration e2e）。`resolve-entry.py` 只核对不改。
  P3-P5 在此批闭环。
- **批 2 `docs-consistency`（complexity: medium）**：M7-M11（`UPGRADING.md` / `README.md` /
  `README.zh-CN.md` / `SETUP.md`）+ `check-protocol-consistency.py --strict-errors-only` 回归。
  依赖批 1 的 install 行为落地（BDD-12 checklist 1/2 交叉锁）。
- **跨批共享件**：`agate/UPGRADING.md` 生命周期节的「根 scripts/ 维护语义」条目 = 决策 B1 语义单源
  （批 1 单测断言 ↔ 批 2 文档条目，BDD-4 判据 3 交叉锁）——由主 Agent 在批 1 返回后把 B1 语义定稿传入批 2。
- **同一文件不跨批**：批 1 只碰脚本 + 测试；批 2 只碰文档。无重叠。
- **资源密集**：批 1 的 P5 = 全量 pytest `-n auto` + 端到端多步 install → 资源密集，`parallel_limit: 1` 串行。

---

## §6 gate_commands（P2 固化，后续阶段不得修改）

```yaml
gate_commands:
  P3: "python3 -m pytest agate/tests/ -p no:cacheprovider"
  P5: "python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto"
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_shellcheck: "shellcheck -S warning agate/scripts/*.sh"
  P5_shellcheck_root: "shellcheck -S warning install.sh"
  P5_counttests: "bash agate/tests/scripts/count-tests.sh"
  P5_timeout_seconds: 600
```

- `P3` 走既有 `AGATE_TDD_TIMEOUT`（默认 120s），不加 `timeout_seconds`（字段规则 1）。
- `P5` 含端到端多步 install（可能 `git clone` 本地 repo）→ 归**构建类**档 → `P5_timeout_seconds: 600`
  （单条 P5 key 覆盖，per-key 规则 2）。无独立 E2E 命令（`ui_affected: false`，端到端折进 P5 pytest 的 `integration/`）。
- `P5_shellcheck_root` 新增（R9）：固化命令 `agate/scripts/*.sh` 不覆盖仓库根 `install.sh`（M6 改动对象）；
  基线实测 `shellcheck -S warning install.sh` rc=0。独立 key，不用 `&&` 拼接。
- `P5_counttests` 路径已按实际校正：`agate/tests/scripts/count-tests.sh`（派发指引写的
  `agate/tests/tests/scripts/` 不存在；`ls agate/tests/scripts/` + `find agate/tests -name 'count-tests*'` 已核对）。
- `P5_consistency` 用 worktree 自己的 `agate/scripts/check-protocol-consistency.py`（AGENTS.md 双工作区纪律）。

---

## §7 files_to_read（P4 implementer 上下文地图）

```yaml
files_to_read:
  - path: agate/scripts/agate-install.py:66-68
    why: _agate_home()——agate_home 路径来源（M1/M2 守卫与根 scripts/ 落地基准）
  - path: agate/scripts/agate-install.py:129-147
    why: _ensure_repo()——makedirs + git clone 段，M1 守卫须插在其调用前
  - path: agate/scripts/agate-install.py:177-184
    why: _install_version()——版本目录建立点；M2 根 scripts/ copytree 在成功路径末尾
  - path: agate/scripts/agate-install.py:269-288
    why: _cmd_install()——M1 守卫首行 + M2 副本落地（装 latest / 指定版本两分支）
  - path: agate/scripts/agate-install.py:402-431
    why: main() arg 解析——确认 --versions 不需在 agate-install.py 侧加（install.sh 侧处理）
  - path: agate/scripts/agate_common.py:125-196
    why: _resolve_pointer_chain + _resolve_version_info——M3 helper 位置 + M4/M5 两处调用点与 version 推导顺序
  - path: agate/scripts/agate_common.py:198-239
    why: resolve_version_root / resolve_hook_root / resolve_agate_root——受益方，核对不改；脚本上溯兜底分支边界
  - path: agate/scripts/agate_common.py:663-677
    why: resolve_rules_root——受益方（rules/ 在 vdir/agate/rules/），核对不改
  - path: agate/scripts/resolve-entry.py:35-52
    why: main() gate_path 拼接（:49）+ fail-closed 分支（:50-52）——BDD-8 受益方，核对无需改
  - path: agate/scripts/agate-resolve.py:29-42
    why: AGATE_VERSION / AGATE_ROOT 输出契约——I-1 核对锚点（BDD-6）
  - path: agate/scripts/agate-summary.py:140-155
    why: info["version"] / info["root"] 显示——I-1 核对，不改代码
  - path: install.sh:1-55
    why: M6 加 --versions 分支；保持既有单软链路径不变
  - path: agate/UPGRADING.md:16-38
    why: §1 通用升级步骤——M7 生命周期节插入位置 + git pull 口径基准
  - path: agate/UPGRADING.md:543-583
    why: v0.50.0 节 §① 布局变化表格——M8 加指针（BDD-12 checklist 1/2）
  - path: agate/UPGRADING.md:92-190
    why: v0.66-0.68 hook 口径节
  - path: agate/UPGRADING.md:255-380
    why: v0.60/0.61/0.62 节「通用升级动作 git pull + 重跑 install-hook.py」——M9 不逐条改写，核对
  - path: agate/SETUP.md:242-250
    why: 「## 升级 Agateon 之后」节——M11 口径对齐 + 指针
  - path: README.md:34-46
    why: 快速上手「版本管理」块——M10 补 install.sh --versions 官方路径
  - path: README.zh-CN.md:34-46
    why: 同 README.md（中文版同步）
  - path: agate/tests/unit/test_agate_version_install.py:21-121
    why: _run_install / _tag_upstream / 既有 BDD 用例形态——M12 新增 BDD-1~5 的基准
  - path: agate/tests/unit/test_agate_version_resolve.py:17-90
    why: _make_home / _resolve_env / _write_version_decl——M13 双 fixture（_make_home_meta / _make_home_rootproto）的基准
  - path: agate/tests/unit/test_hook_resolve_entry.py:29-118
    why: _make_home（建 vX/scripts/ 直含）/ _STUB_GATE / BDD-16 形态——M14 meta fixture BDD-8 的基准
  - path: agate/tests/unit/test_agate_version_resolve.py:181-205
    why: test_bdd_30_legacy_symlink_direct_root——os.symlink 失败 → pytest.skip 的既有平台无关模式（M12 BDD-1 复用）
  - path: agate/tests/conftest.py:264-303
    why: GitRepo 封装——M15 端到端 fixture 复用
  - path: agate/tests/conftest.py:305-429
    why: agate_scripts / python_exe / run_cli / git_repo / py_path fixture 契约
  - path: agate/tests/integration/test_pre_commit_hook.py
    why: integration 层测试结构参考——M15 test_version_lifecycle_e2e.py 骨架
```

---

## §8 env_constraints（继承 P0-brief，细化不弱化）

```yaml
env_constraints:
  debug_env: "隔离 HOME：HOME=$(mktemp -d)（测完 rm -rf）跑一切涉及安装路径的最小验证 / 端到端；绝不触碰真实 ~/.agate（本机 legacy 软链 → 主 checkout agate/）。解释器 /usr/bin/python3（pytest 9.0.3 / pyyaml 6.0.1）；ruff = ~/.venvs/agate-dev/bin/ruff（0.16.4）；shellcheck 0.9.0"
  isolation_check: "install / 端到端用例断言两条：① 隔离 HOME 下 ~/.agate 为 mktemp 目录（HOME + USERPROFILE env 双设，见 conftest _resolve_env / _run_install）；② 跑完 worktree `git status --porcelain` 无新增 repo/ 或 vX.Y.Z/（BDD-14）。P5 gate 会执行 gate_commands（§6）——isolation 断言落在测试用例内，不是本字段"
  dual_workspace: "改造对象 = worktree（/home/kity/oclab/agateon/.worktrees/agate-TAG0032）的 agate/ + 仓库根 install.sh；跑 gate / 读卡片用 ~/.agate 稳定版；check-protocol-consistency.py 必须用 worktree 自己的（agate/scripts/check-protocol-consistency.py）；主 checkout /home/kity/oclab/agateon 禁止改动，状态标记 [PROD_NOT_TOUCHED]"
  self_gate: "改 agate/scripts/*（agate-install.py / agate_common.py；resolve-entry.py 预期只核对不改）+ agate/tests/* + 文档面（README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md / install.sh）→ 触发 SELF-GATE。P8 commit message 须含 self-gate-review: 路径 或 self-gate-skip: 理由（commit-msg hook 检查）。P2 不含 self-gate 流程本身"
  platform_neutral: "新增测试：tmp_path + python_exe fixture（不写死 python3）；不假设 POSIX symlink（os.symlink 失败 → pytest.skip，同既有 test_bdd_30）；不用 /tmp 字面量；install.sh 经 conftest bash fixture 调用。决策 B 选副本（B1）→ 无 Windows 软链退化，无需写双口径"
```

> 边界提醒：`env_constraints` 是声明性字段，不被自动执行。真正被强制的是 §6 `gate_commands`
> 与 P4/P8 卡片 checklist。isolation / 双工作区 / 平台无关的强制力落在：测试用例内断言（isolation_check）、
> `P5_consistency` / `P5_shellcheck*` gate 命令、P8 SELF-GATE commit-msg 检查。

---

## §9 minimal_validation

```yaml
minimal_validation:
  - assumption: "断点一 · os.makedirs(agate_home, exist_ok=True) 穿透 legacy 软链；随后 repo/ 与 vX.Y.Z/ 落入软链目标内部（污染源仓库）"
    method: "隔离 HOME（HOME=$(mktemp -d)）+ 最小复现脚本（scratchpad/mv1.sh，约 25 行）：ln -s real_target/agate ~/.agate → python3 检查 os.path.islink/isdir → os.makedirs(~/.agate, exist_ok=True) → os.makedirs(~/.agate/repo) → git clone ~/.agate/repo_clone → 检查 realpath 与 st_ino"
    result: confirmed
    note: "实测（2026-09-07 隔离 HOME）：islink(base)=True 且 isdir(base)=True 同时成立；os.makedirs(base, exist_ok=True) 对指向已存在目录的软链无报错（穿透确认）；os.makedirs(~/.agate/repo) 的 realpath 落 <mktemp>/real_target/agate/repo，inode(base)==inode(target)；git clone repo_clone 落软链目标内部确认。→ 修复判据：os.path.islink(agate_home) 须在 _ensure_repo 的 makedirs / git clone 之前判，True → fail-closed exit 1 且不建任何目录（M1）。与 P0-brief 2026-09-07 实测（repo 实体落 src/agate/repo，无提示）一致，本次补最小复现印证。"
  - assumption: "决策 A1 · resolve 探测顺序 vdir/scripts 先、vdir/agate/scripts 后 + AGATE_VERSION 不回归（I-1）"
    method: "纯代码逻辑，无外部系统依赖"
    result: not_needed
    note: "依赖 _resolve_version_info（agate_common.py:166）两段分支 + 新 helper _protocol_root：① .agate-version ok 分支 L180-183——vdir = os.path.join(base, declared)，os.path.isdir(vdir) 命中后 root = _protocol_root(vdir)，version 恒取 declared（字符串常量，不受 root 影响，I-1 天然安全）；② current 链分支 L188-190——cur = _resolve_pointer_chain(base, 'current')，必须先 version = os.path.basename(cur) 再 root = _protocol_root(cur)，顺序倒置则 version 变 'agate'（I-1 红线，M5）。_protocol_root 判定链：isdir(vdir/scripts) → 返回 vdir（探测序 1，纯增量红线，BDD-7）；否则 isdir(vdir/agate/scripts) → 返回 vdir/agate（探测序 2，BDD-6）；两者皆无 → 返回 vdir 原样，下游 resolve-entry.py:49 拼 <vdir>/scripts/<gate> 不存在 → :50-52 fail-closed exit 1（既有兜底分支，I-11，未删除任何路由 → 无 T086 类落点漂移）。env 覆盖分支 L173-175、legacy 软链兜底分支 L192-193、resolve_hook_root 脚本上溯兜底 L219-228 均不改。消费方 grep 复核（本次实跑）：resolve_version_root / resolve_hook_root / resolve_agate_root / resolve_rules_root + check-structure-consistency.py:528,545 + check-yaml-schema.py:155 全部经 _resolve_version_info 归口，无 os.path.dirname(vdir)+'/scripts' 旁路（DEBT0016 教训）。"
```

---

## §10 实现完成的标志（供 P3 / P5 / P6）

1. **决策 A1 落地**：`agate_common.py` 含 `_protocol_root` helper；`_resolve_version_info` 两处调用；
   BDD-6（meta fixture → `AGATE_ROOT` 结尾 `/vX.Y.Z/agate` + `AGATE_VERSION=vX.Y.Z`）与
   BDD-7（rootproto fixture → `AGATE_ROOT` 结尾 `/vX.Y.Z` + `AGATE_VERSION=vX.Y.Z`）双 fixture 用例 PASS；
   BDD-8（`resolve-entry.py pre-commit` exit 0 + gate 路径在 `vX.Y.Z/agate/scripts/`）PASS。
2. **决策 B1 落地**：装 latest 后 `~/.agate/scripts/agate-install.py --help` exit 0（BDD-4 判据 1）；
   `agate/tests/` 含「重跑 latest 后根 scripts/ 副本随 current 刷新」用例（BDD-4 判据 2）；
   该用例断言语义与 UPGRADING 生命周期节一致（BDD-4 判据 3 ↔ BDD-11 判据 3）。
3. **断点一**：BDD-1（软链布局 install exit≠0 + 软链目标内无 `repo/` / `vX.Y.Z/`）、
   BDD-2（stderr 三段命令片段可 grep）、BDD-3（普通目录 / 全新 exit 0）PASS。
4. **BDD-5**：`install.sh --versions` 在隔离 HOME 产出版本管理根布局（`repo/` + `vX.Y.Z/` + 指针 + 根 `scripts/`），无源树污染。
5. **断点三文档面**：BDD-10（两布局更新指令对齐 + 幂等声明）、BDD-11（生命周期节四动作 + hook 时机 + 副本语义条目）、
   BDD-12（checklist 四条各命中「已收敛」或「历史叙事保留」，无第三态）PASS。
6. **回归底线**：`python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -n auto` 全 PASS（BDD-9）；
   `check-protocol-consistency.py --strict-errors-only` EXIT 0 / 0 ERROR；`shellcheck -S warning agate/scripts/*.sh`
   与 `shellcheck -S warning install.sh` 均 0 error；`count-tests.sh` 用例数只增不减（新增 ≥ 10 条用例）。
7. **端到端**：BDD-13（隔离 HOME 全链路逐步 exit 符合期望 + 幂等复跑不重复建目录）、
   BDD-14（worktree `git status --porcelain` 无污染）PASS（CI 无网 → 真实 GitHub clone 增强 skip + 本地补证）。
8. **范围锁定**：`install-offline.py` / Windows 复制模式 / `.state.yaml` schema / agateon 仓库形态重构 未被触碰。
