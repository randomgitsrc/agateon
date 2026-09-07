---
phase: pre-commit (self-gate Layer 1 fix-1)
generated_by: 主 Agent
task_id: TAG0032
role: implementer
round: self-gate-fix-1
---

<dispatch_guide>
> ⚠️ 派发指引是强制指令。本轮是 **SELF-GATE fix-1（协议对齐审查发现的文档传播缺口修复）**——protocol-alignment-review 结论 0 MISALIGNED / 4 NEEDS_HUMAN_REVIEW（A2/A3/A5/A7），主 Agent 决定修复而非 `[HUMAN_CONFIRMED]` 挂起。

### 背景

`docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md`（先读「闭环建议」+ A2/A3/A5/A7 逐项 + DESIGN_GAP 优先核查节）：TAG0032 改了 `agate/scripts/agate-install.py` / `agate_common.py` / `install.sh` + 文档面，但**次级参考文档 + ADR 未同步**——无一处被证伪，属「不完整」非「矛盾」。修复它们。

### 修复目标（5 项，只改文档 + ADR，不碰任何代码/测试）

1. **`agate/scripts/README.md`（A2/A3b）**：
   - L70 附近 `agate-install.py` 工具行：现「无参 = 装 latest 指针（最新发布版）」→ 补 `latest` 显式别名（如「无参 / `latest` = 装 latest 指针（最新发布版，幂等）」）
   - L5 附近「版本管理机制（TAG0008 起）」blockquote：补一句——GitHub 直装的**元仓库整仓形态**版本目录（协议在 `agate/` 子目录）由 `_resolve_version_info` 的 `_protocol_root` 两形态探测（`vdir/scripts` 先、`vdir/agate/scripts` 后）适配；新机可用 `install.sh --versions` 一键进入版本管理布局；版本管理布局的根 `~/.agate/scripts/` 是随每次安装/升级刷新的单源副本（非软链）
2. **`agate/AGENTS.md`（协议使用者版，A2/A3b）**：L91-96「版本管理形态块」：示例补 `agate-install.py latest` + `install.sh --versions` + 一句元仓库整仓形态说明（与 `agate/scripts/README.md` 口径一致，但更简；权威口径仍指向 `agate/UPGRADING.md`「版本管理生命周期」节）
3. **`agate/adr.md`（A7）**：新增 **ADR-011**（编号按 adr.md 现有最大 +1 核实）记录：
   - (a) 版本目录**两形态**——「根即协议」（`git worktree add` 出的版本目录本身即协议本体，`vdir/scripts/` 存在）/ 「元仓库整仓」（GitHub 直装，协议在 `vdir/agate/` 子目录）；`_protocol_root(vdir)` 探测序 **`vdir/scripts` 先、`vdir/agate/scripts` 后**——**探测序不可颠倒**（既有「根即协议」部署方零回归的纯增量红线）；两形态皆无 → 返回 `vdir` 原样，下游 `resolve-entry.py` fail-closed 兜底不变
   - (b) **决策 B1**：根 `~/.agate/scripts/` = 单源 `shutil.copytree` 副本（**非软链**），随每次 `agate-install.py`（含 `latest`）安装/升级重建刷新；`repo/` 或某 `vX.Y.Z/` 被删不影响已建副本；该副本**不参与 hook 版本解析**（hook 经 resolve-entry 按 `.agate-version` 解析）
   - 关联：扩展 ADR-009（版本管理根 + resolve-entry 固定入口），方向契合其纯增量/向后兼容红线
   - 格式对齐 adr.md 既有 ADR 条目结构（决策/理由/后果/关联等节，按实际模板）
4. **`agate/UPGRADING.md`（A1 KNOWN_DEVIATION + P7 deviation_count=1）**：L72-73 附近「根 `~/.agate/scripts/` 维护语义」段——现描述 fix-1 **已删除**的 layer-1 双层机制（「运行中安装器自带的 `scripts/` **叠加**当前 `current` 版本的协议 `scripts/`（后者覆盖前者，**后拷贝者胜**）」）→ 改写为**单源 copytree** 口径（「`~/.agate/scripts/` = `agate-install.py` 从当前 `current` 版本协议根的 `scripts/` 目录复制的单份副本」）。**只改「内部拷贝机制」这一句陈述**——其余子条目（副本非软链 / 随 install 重跑刷新 / `repo/` 被删不影响 / 不参与 hook 解析）均对单源仍准确，**不动**
5. **`agate/platform-notes.md`（A3b，低 severity 可选——本轮一并做）**：指针形态节（约 L165）补一句——`install.sh --versions` 保持 POSIX shell（无 bash 扩展）；决策 B1 根 `scripts/` 用**拷贝**（非软链）恰好规避 Windows 符号链接权限问题，比软链更平台无关

### 不做（明确排除）

- **不碰任何代码/测试**（`agate/scripts/*.py` / `install.sh` / `agate/tests/*`）——本轮纯文档 + ADR
- **不写 CHANGELOG**——CHANGELOG 6 条语义变更 + UPGRADING §3 版本章节是 **P8 步骤**（版本 bump 时），本轮不做；A5 的 CHANGELOG 部分留 P8
- 不改 `agate/UPGRADING.md`「版本管理生命周期」节的其余内容（对照表 / hook 时机 / 其余维护语义子条目——A1 已 ALIGNED）
- 不扩范围到 out-of-scope

### 验证（改完必跑）

- `timeout 120 /usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → 0 ERROR（新增 ADR-011 + 文档改动不得引入 ERROR；注意 CHECK 9 脚本名引用、CHECK 10 文档引用漂移、CHECK 13 CHANGELOG↔UPGRADING）
- `timeout 180 /usr/bin/python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py -k tag0032 -p no:cacheprovider -q` → 全绿（UPGRADING 改动不得破坏 BDD-4/10/11/12 文档断言——`test_tag0032_bdd_4_root_scripts_copy_semantics_documented` 只断言「副本」「重跑 agate-install…刷新」「repo/」三点，单源口径仍满足；若某断言精确匹配了「叠加/后拷贝者胜」子串则是测试与 fix-1 不一致，标 `[DESIGN_GAP]` 报主 Agent，**不改测试**）
- `git diff --stat` 确认只动了 5 个文档/ADR 文件，无代码/测试

### 约束

- **最小修正**：只补缺失描述 + 改 UPGRADING 一句陈述 + 加 ADR-011，不重写章节、不"顺便润色"
- **口径单一权威**：`agate/scripts/README.md` / `agate/AGENTS.md` 的版本机制描述都指向 `agate/UPGRADING.md`「版本管理生命周期」节为权威，自身只做"框架 + 指针"，不复制完整对照表
- **平台无关 / 中立**：不写死平台假设
- 自主决策标 `[DESIGN_GAP: xxx]`（独立成行）；疑问标 `[CLARIFY: xxx]`
- 产出：`P4-implementation.md` 末尾**追加** `## SELF-GATE fix-1（文档传播）` 节（改了什么 + 验证结果），不覆盖既有内容

### 输入文件

- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md（协议对齐审查报告，权威——A2/A3/A5/A7 逐项 + 闭环建议 + DESIGN_GAP 核查）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-implementation.md（批 1/2 + fix-1——理解实际实现，尤其 `_sync_root_scripts` 单源 copytree / `_protocol_root` 探测序 / `latest` 别名 / `install.sh --versions`）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P2-design.md（§2 决策 A1 / §3 决策 B1——ADR-011 内容来源）
- {AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P7-consistency.md（§3.3 UPGRADING deviation 描述）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/scripts/README.md（改动对象——L5 机制段 + L70 agate-install.py 行）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/AGENTS.md（改动对象——L91-96 版本管理形态块）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/adr.md（改动对象——加 ADR-011，先读 ADR-009 + 现有最大 ADR 编号 + 条目格式模板）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/UPGRADING.md（改动对象——L72-73 附近「根 scripts/ 维护语义」段）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate/platform-notes.md（改动对象——约 L165 指针形态节）
- /home/kity/oclab/agateon/agate/assets/execution-roles/implementer.md（角色定义，稳定版）
- /home/kity/oclab/agateon/.worktrees/agate-TAG0032/AGENTS.md（改脚本工作流 / 文档保鲜 / 单一权威哲学）

路径说明：{AGATE_WORKSPACE} = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032/agate-workspace`；改造对象仓库本体 = `/home/kity/oclab/agateon/.worktrees/agate-TAG0032`；读角色/卡片用稳定版 `/home/kity/oclab/agateon/agate`。

### 客观查证信息

- 解释器 `/usr/bin/python3`；`check-protocol-consistency.py` 用 worktree 自己的
- 主 checkout 禁止改动；bash 外层 `timeout` 30-180s；单步串行；状态标记 `[PROD_NOT_TOUCHED]`
- 分阶段落盘：追加 `{AGATE_WORKSPACE}/tasks/TAG0032-version-lifecycle/P4-progress.md`

### 返回

只返回两行：① P4-implementation.md 路径；② 一句话摘要（≤30 字：5 项文档/ADR 修复 + consistency/pytest 结果）。
