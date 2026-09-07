---
phase: P8
task_id: TAG0032
type: release
parent: P7-consistency.md
trace_id: TAG0032-P8-20260907
agent: implementer
status: draft
created: '2026-09-07'
bump_type: minor
debt_check: reviewed
---

# P8-release.md — TAG0032-version-lifecycle 发布准备声明

> releaser subagent（implementer P8 模式）产出。**未执行 `bump-version` / `git commit` /
> `git tag`**——这些由主 Agent 在 P8 gate 验证通过后亲自执行。本轮已实际编辑 `CHANGELOG.md` /
> `README.md` / `README.zh-CN.md` / `agate/UPGRADING.md` §3 / `agate-workspace/roadmap/roadmap.md`
> 五个文件（P8 产出的一部分，非"留给主 Agent"）。状态标记 `[PROD_NOT_TOUCHED]`。

## 1. 前置条件核对（P7-consistency.md）

- P7-consistency.md（TAG0032-P7）结论：**approved**，`blocker_count: 0`，5 处 GAP 全部
  `REVIEWED`（DESIGN_GAP 已配对转抄 + 判定接受）。
- SELF-GATE Layer 1 协议对齐复审：全 ALIGNED（0 MISALIGNED，A1 KNOWN_DEVIATION 追平，
  ADR-012 补齐），见 `docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md`。
- 上游链路：P1 14 BDD → P6 14/14 PASS → P6.5 judge 14/14 passed → P7 approved。
  commits：P4 `1d9a322` / P5 `2f50f4c` / P6 `af5bfe6` / P6.5 `5f08bf8` / P7 `2a01095` /
  self-gate `279c236`。
- 结论：具备进入 P8 发布阶段的一致性前提，**前置条件已满足**。

## 2. P2-design.md packages 声明核对

`packages: [agate-scripts, agate-docs, agate-tests]`——**任务内部分类，非独立发布单元**。
agateon 是单一版本号仓库（无 package.json / pyproject 各自版本号），整体 bump 一次。
P2-design.md 的 packages 声明用于任务改动分域，不触发多包拆批发布（P8 卡「多包发布拆批」
仅当存在独立可发布制品时适用，本任务不适用）。

| package（分域） | 实际改动 | 备注 |
|---|---|---|
| agate-scripts | `agate/scripts/agate_common.py`（`_protocol_root`）、`agate-install.py`（`latest` 别名 / `_ensure_repo` fetch --tags / `_sync_root_scripts` / legacy 软链 fail-closed）、`install.sh`（`--versions` 子命令） | 批 1/2 + fix-1 |
| agate-docs | `agate/UPGRADING.md`「版本管理生命周期」节、`agate/scripts/README.md`、`agate/AGENTS.md`、`agate/adr.md`（ADR-012）、`agate/platform-notes.md`、`README.md` / `README.zh-CN.md` / `agate/SETUP.md` 版本管理生命周期口径 | self-gate fix-1 文档传播 |
| agate-tests | `agate/tests/` TAG0032 批（14 BDD 对应用例 + e2e 隔离 HOME 元仓库形态 fixture） | P3/P5 |

## 3. bump_type 判断依据

**bump_type: minor**

依据：
1. **加功能（4 项纯增量）**：`agate-install.py latest` 显式别名 / `install.sh --versions`
   子命令 / 元仓库整仓形态 `_protocol_root` 两形态解析 / 根 `~/.agate/scripts/` 入口副本。
2. **一处对齐既有意图的行为收敛**：legacy 软链布局 install **fail-closed 拒绝** + 三步迁移
   指引。**向后兼容红线守住**——legacy 单软链用户**不跑新工具**（`git pull` 升级路径）行为
   完全不变；纯增量红线经 BDD-7 + 全量回归锁定。
3. 无破坏公共 API / CLI 契约的 major 变更：无参 `agate-install.py` 行为不变；`_protocol_root`
   对「根即协议」形态探测序 1 先命中、返回值不变；两形态皆无 → 返回 `vdir` 原样 +
   下游 `resolve-entry.py` 既有 fail-closed 兜底未删。
4. 版本号：当前发布版 **v0.68.0**（`git describe --tags --abbrev=0` 已核）→ 目标 **v0.69.0**。

## 4. 版本号变更确认（三处 + roadmap）

| 位置 | 文件 | 变更 | 本轮状态 |
|---|---|---|---|
| README badge（EN） | `README.md` L12 | `version-v0.68.0` → `version-v0.69.0` | ✅ 已改 |
| README badge（ZH） | `README.zh-CN.md` L12 | `version-v0.68.0` → `version-v0.69.0` | ✅ 已改 |
| CHANGELOG | `CHANGELOG.md` | 顶部新增 `## [0.69.0] - 2026-09-07` 节（顶部无 `[Unreleased]` 节，直接新增，格式对齐 `## [0.68.0]`） | ✅ 已改 |
| UPGRADING §3 | `agate/UPGRADING.md` | §3「已知破坏性变更（按版本）」新增 `### v0.69.0` 章节（对齐 `### v0.68.0` 格式；CHECK 13 CHANGELOG 最新版 ↔ UPGRADING §3 章节一致） | ✅ 已改 |
| roadmap 回写 | `agate-workspace/roadmap/roadmap.md` | RM-AG0058「状态」列 `scheduled` → `done`（「更新」列已是 `2026-09-07`）（RM-AG0043 P8 gate 硬校验） | ✅ 已改 |

> **git tag `v0.69.0` 由主 Agent 在 gate 验证通过后创建**。tag 创建前，
> `check-protocol-consistency.py` CHECK 7（README badge ↔ git tag）必然报
> `badge v0.69.0 != tag v0.68.0` ERROR——属"发布完成态"校验的设计使然，非回归；
> 主 Agent 在 tag 后重跑即 0 ERROR。releaser 本轮只确认 CHECK 13 通过。

## 5. CHANGELOG `[0.69.0]` 节内容（本轮已写入 CHANGELOG.md 本体）

`### 新增（TAG0032：版本管理生命周期可用性批，RM-AG0058 + DEBT0034）`：

1. **`agate-install.py` 新增 `latest` 显式别名**（= 无参 install，幂等）。
2. **`install.sh --versions` 新增子命令**——一键从零进入版本管理布局（建 `repo/` + 首个
   `vX.Y.Z/` + `latest` / `current` 指针 + 根 `scripts/` 副本）。
3. **`agate-install.py` `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时新增
   `git fetch --tags --force --prune`**（fail-open）——令重跑 `latest` 跟随上游更高 tag。
4. **resolve 链新增「元仓库整仓形态」版本目录支持**（`_protocol_root`：`vdir/scripts` 先探 →
   `vdir`；`vdir/agate/scripts` 后探 → `vdir/agate`；探测序不可颠倒；皆无 → `vdir` 原样 +
   下游 fail-closed 兜底不变）——GitHub 直装的整仓版本目录现可正确解析到协议子目录（RM-AG0058）。
5. **版本管理布局新增根 `~/.agate/scripts/` 入口副本**（决策 B1，单源 `copytree` 非软链，
   随每次安装 / 升级刷新）。
6. 关联：RM-AG0058 / DEBT0034 / ADR-012。

`### 变更`：

7. **`agate-install.py` / `install.sh --versions` 对 legacy 软链布局 `~/.agate` fail-closed
   拒绝**（**行为变化**：此前会穿透软链把 `repo/` · `vX.Y.Z/` 静默建进源仓库）——附三步迁移
   指引（`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions`）；
   向后兼容红线：legacy 单软链用户不跑新工具行为完全不变。

## 6. debt_check

**debt_check: reviewed**

已读取 `agate-workspace/debt/tech-debt.md`。本任务相关 DEBT 条目清单：

| DEBT id | 标题（摘） | status | 说明 |
|---|---|---|---|
| DEBT0034 | TAG0032 三步 legacy 软链迁移指引文案在 `agate-install.py`（`_LEGACY_SYMLINK_MSG`）与 `install.sh`（heredoc）双写 | **open** | **本任务新登记，未在本任务关闭**。priority: low。风险：两处文案漂移（改一处忘另一处），BDD-2 只 grep Python 侧。收敛方向：`install.sh --versions` 软链拒绝分支改为直接 `exec agate-install.py`（由其打印统一文案 exit 1），或抽公共文案资源。留后续收敛，不阻断本次发布（BDD-17：未关闭债务不阻断 P8 gate）。 |

本任务未关闭任何既有 DEBT，未新增其他 DEBT。

## 7. 临时资源清单（releaser → 主 Agent 交接）

核对本任务 P0-P8 全程：

- **启动的临时服务 / 进程**：无。本任务是纯脚本 + 文档 + 测试改动，未启动 debug server /
  临时 daemon。
- **创建的临时数据**：各阶段（P3/P5/e2e）使用隔离 HOME（`HOME=$(mktemp -d)`）+ 元仓库形态
  fixture repo 做真实 `curl|bash` / `agate-install` 端到端验证，各 subagent 执行完已
  `rm -rf`；pytest `tmp_path` / `monkeypatch` fixture 自动清理。无遗留。
- **开发安装**：无（无 editable install、无全局包安装、无 pip install）。

**清单：无临时服务 / 数据 / 安装，隔离 HOME 已随各阶段清理。**

## 8. Lessons Learned

1. **流程 / 影响面**：P2 影响面梳理 §1.1 漏了 `agate/scripts/README.md` / `agate/AGENTS.md` /
   `agate/adr.md`（ADR-012）三处文档传播目标，靠 SELF-GATE Layer 1 复审兜住。教训 = 改动"解析
   内核 / 布局机制"时，文档传播目标清单要覆盖「机制说明散文 + ADR 决策记录」两类，不能只列
   直接引用点。
2. **测试 / fixture**：fix-1 因迁就 P3 fixture（`_tag_meta_upstream` 不放 `agate-install.py`
   进协议目录以模拟元仓库 gap）一度在 `install.sh --versions` 的 `exec` 路径引入 CRITICAL
   ——`$SCRIPT_DIR` 在 `curl|bash` 形态下断裂（= 当前工作目录，非脚本目录）。教训 = fixture
   须贴近真实形态；`curl|bash` / 本地下载跑 / repo 副本三种入口路径都要有对应 fixture 覆盖，
   `exec` 目标用「刚 clone 的 repo 副本优先 + `$SCRIPT_DIR` 兜底」双保险。
3. **架构 / 向后兼容**：`_protocol_root` 两形态探测「顺序不可颠倒」是纯增量红线——先探
   `vdir/agate/scripts` 会把某些「根即协议」且恰含 `agate/` 子目录的既有部署方改判协议根，
   破坏向后兼容。教训 = 给"探测序"类决策写 ADR 时，要落具体的破坏场景（不只是断言"不可颠倒"），
   ADR-012 §决策已按此记录。

## 9. 自检

- `bump_type: minor` / `debt_check: reviewed` 字段存在：✅
- 版本号三处（README badge / CHANGELOG / UPGRADING §3）+ roadmap 回写均已实际编辑：✅
- CHANGELOG `[0.69.0]` 节含 6 条语义变更 + 关联 RM-AG0058 / DEBT0034 / ADR-012：✅
- roadmap RM-AG0058「状态」列已回写 `done`（RM-AG0043 P8 gate 硬校验）：✅
- 未执行 `bump-version` / `git commit` / `git tag`（留主 Agent）：✅
- 未碰代码 / 测试 / 其它文档；未改 `agate/UPGRADING.md`「版本管理生命周期」节：✅
- `[PROD_NOT_TOUCHED]`：✅
