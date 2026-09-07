---
review_date: 2026-09-07
reviewer: protocol-alignment-review
review_round: re-review-1 (SELF-GATE Layer 1 复审)
change_summary: TAG0032 修复 TAG0008 版本管理 v1 生命周期三断点（入口断链 fail-closed 守卫 + 根 scripts/ 副本 / 元仓库形态 _protocol_root 探测 / install.sh --versions + agate-install.py latest 统一 update 入口）；本轮复审 fix-1 文档传播修复
files_changed:
  - agate/scripts/agate-install.py
  - agate/scripts/agate_common.py
  - install.sh
  - agate/UPGRADING.md
  - agate/SETUP.md
  - README.md
  - README.zh-CN.md
  - agate/tests/unit/test_agate_version_install.py
  - agate/tests/unit/test_agate_version_resolve.py
  - agate/tests/unit/test_hook_resolve_entry.py
  - agate/tests/unit/test_upgrading_lifecycle.py (新增)
  - agate/tests/integration/test_version_lifecycle_e2e.py (新增)
fix1_files_changed:
  - agate/scripts/README.md
  - agate/AGENTS.md
  - agate/adr.md (新增 ADR-012)
  - agate/UPGRADING.md
  - agate/platform-notes.md
---

# 协议-脚本对齐审查 — TAG0032 版本管理生命周期可用性批

[PROD_NOT_TOUCHED] — 只审不改。本轮为 **SELF-GATE Layer 1 复审**（re-review-1）。

## 复审背景

首轮结论：**0 MISALIGNED / 4 NEEDS_HUMAN_REVIEW**（A2 / A3 / A5 / A7）+ A1 含 1 处 `[KNOWN_DEVIATION]`。
主 Agent 派 implementer 做 fix-1（纯文档 + ADR 传播，不碰代码/测试），改动 5 个文件：
`agate/scripts/README.md` / `agate/AGENTS.md` / `agate/adr.md`（新增 ADR-012）/ `agate/UPGRADING.md` / `agate/platform-notes.md`
（回改说明见 `P4-implementation.md` 末尾 `## SELF-GATE fix-1（文档传播）` 节）。

本轮聚焦：**A2 / A3 / A5 / A7 的缺口是否消解 + A1 KNOWN_DEVIATION 是否追平 + fix-1 有无引入回归**。
首轮已 ALIGNED 的 **A4 / A6 不重走**（沿用首轮结论）。

## 复审结论汇总

| # | 审查项 | 首轮 | 复审 | 说明 |
|---|--------|------|------|------|
| A1 | 文档→脚本对齐 | ALIGNED（含 1 处 KNOWN_DEVIATION）| **ALIGNED（KNOWN_DEVIATION 已消解）** | `UPGRADING.md` L71-73 已改为「单源 copytree」口径，与 `_sync_root_scripts` 一致；`deviation_count` 1 → 0 |
| A2 | 脚本→文档对齐 | NEEDS_HUMAN_REVIEW | **ALIGNED** | `scripts/README.md` L5/L70 + `AGENTS.md` 形态块已反映 `latest` 别名 / `--versions` / 元仓库形态 / 根 scripts/ 副本，语义与脚本实现一致，权威口径指向 UPGRADING |
| A3 | 一致性连锁 + 反向传播 | NEEDS_HUMAN_REVIEW | **ALIGNED** | A3a 首轮已 ALIGNED；A3b 首轮点名 4 处（scripts/README.md / AGENTS.md / adr.md / platform-notes.md）已全部传播到位 |
| A4 | 测试覆盖 | ALIGNED | ALIGNED（首轮，未复核）| fix-1 未碰测试；`pytest -k tag0032` 本轮实跑 `test_upgrading_lifecycle.py` 7 passed |
| A5 | 下游影响 + 文档传播 | NEEDS_HUMAN_REVIEW | **ALIGNED（(b) 传播到位；(a)(c) = P8 待办清单，已确认）** | (b) `scripts/README.md`/`AGENTS.md`/`adr.md` 传播已落地；(a) CHANGELOG 6 条 + (c) UPGRADING §3 章节为 P8 常规动作，清单已列，fix-1 未擅自写 CHANGELOG |
| A6 | 锚点表覆盖 | ALIGNED | ALIGNED（首轮，未复核）| fix-1 未新增 CHECK / BDD 格式 / frontmatter 字段 |
| A7 | 设计原则一致性 | NEEDS_HUMAN_REVIEW | **ALIGNED** | 新增 **ADR-012** 正确记录 `_protocol_root` 两形态探测序（含不可颠倒红线）+ 决策 B1 副本机制；编号 = adr.md 现有最大 ADR-011 +1；六节格式对齐 ADR-009；显式声明「扩展 ADR-009，不替代」 |

**MISALIGNED 项数：0**
**NEEDS_HUMAN_REVIEW 项数：0**（首轮 4 项全部消解）

**SELF-GATE Layer 1 复审：通过**（A5 附「P8 待办已确认」的可 commit 态——见 A5 「P8 前提条件」）。

---

## 逐项复审

### A1: 文档→脚本对齐 — ALIGNED（KNOWN_DEVIATION 已消解）

**首轮 KNOWN_DEVIATION**（`UPGRADING.md` L72-73）：描述根 `~/.agate/scripts/` 副本内容为「运行中安装器自带的 `scripts/` **叠加**当前 `current` 版本的协议 `scripts/`（后者覆盖前者，**后拷贝者胜**）」——即 P4 fix-1 前的**双 copytree**，与代码单段 `shutil.copytree` 不符。来源 TAG0032 P7-consistency.md §1 / §3.3 REVIEWED-ACCEPTED，`deviation_count=1`，P7 建议 P8 顺手修订。

**fix-1 回改**（`agate/UPGRADING.md:71-73`）：
> 版本管理布局下 `~/.agate/scripts/` 是一份**副本**（不是软链），由 `agate-install.py`（含 `latest`）在每次安装 / 升级时重建刷新，内容 = 从当前 `current` 版本协议根的 `scripts/` 目录**单源** `copytree` 出的一份副本（该目录恒含 `agate-install.py` / `agate_common.py` / `resolve-entry.py` 等全套入口命令，保证在新机可直接调用）。

**脚本实现**（`agate/scripts/agate-install.py:292-319` `_sync_root_scripts`）：
> `proto_scripts = os.path.join(_protocol_root(version_dir), "scripts")` → `shutil.copytree(proto_scripts, dst, dirs_exist_ok=True)`（**单段** copytree，源为 `_protocol_root` 探测出的版本协议 `scripts/`；无 layer-1 自拷贝、无「叠加 / 后拷贝者胜」）。

**结论**：**KNOWN_DEVIATION 已消解**。文档口径与代码单段 copytree 语义一致；「运行中安装器自带 scripts/ 叠加」「后拷贝者胜」字样已删除。其余 3 子条目（随 `agate-install.py latest` 重跑刷新 / `repo/` 或某 `vX.Y.Z/` 被删不影响 / 不参与 hook 版本解析）fix-1 **未动**，对单源 copytree 仍全部准确（`_sync_root_scripts` 无符号链接回指；`_cmd_install` latest 分支 `:336` + 指定版本分支 `:343` 各调一次；`resolve_hook_root` 不读 `~/.agate/scripts/`）。首轮对照表 4 动作、hook 重装时机 2 子条目仍 ALIGNED。P7 `deviation_count` 1 → **0**，A1 无残留偏离。

---

### A2: 脚本→文档对齐 — ALIGNED（复审转正）

首轮 NEEDS_HUMAN_REVIEW 的真模糊点：新增 `latest` 用户可见 CLI 别名 + 元仓库形态解析扩展，是否要求同步 `agate/scripts/README.md` 与 `agate/AGENTS.md` 两处次级参考文档，还是收敛到 `UPGRADING.md` 单一权威节即可。fix-1 采「两处补框架 + 指针，完整口径指向 UPGRADING」——既传播了关键新表面，又守住单一权威哲学。

**`agate/scripts/README.md:5`（版本管理机制 blockquote）** 复审：
> 新机一键进入版本管理布局用 `install.sh --versions`，更新用 `agate-install.py latest`（`latest` 是无参 install 的显式别名，幂等）。GitHub 直装得到的**元仓库整仓形态**版本目录（协议在 `agate/` 子目录）由 `_resolve_version_info` 的 `_protocol_root` 两形态探测（`vdir/scripts` 先、`vdir/agate/scripts` 后，顺序不可颠倒）适配。版本管理布局的根 `~/.agate/scripts/` 是随每次安装/升级刷新的**单源副本**（非软链）。安装 / 迁移 / 更新 / 回退的权威口径见 `agate/UPGRADING.md`「版本管理生命周期」节，本表只做框架 + 指针。

逐点核对脚本实现：
| 文档表述 | 脚本锚点 | 语义一致？ |
|---|---|---|
| `install.sh --versions` = 新机一键进入版本管理布局 | `install.sh:14-46`（`[ "${1:-}" = "--versions" ]` 分支：软链 fail-closed → python 探测 → 条件 `git clone` → `exec "$PY" "$INSTALLER" latest`）| ✅ |
| `agate-install.py latest` = 无参 install 的显式别名，幂等 | `agate-install.py:472-473` `if not args or (len(args) == 1 and args[0] == "latest"): ...`；`_usage():461-462`「无参 / latest 装 latest 指针」| ✅ |
| 元仓库整仓形态（协议在 `agate/` 子目录）由 `_protocol_root` 两形态探测（`vdir/scripts` 先、`vdir/agate/scripts` 后，顺序不可颠倒）适配 | `agate_common.py:166-179` `_protocol_root`：`if os.path.isdir(os.path.join(vdir, "scripts")): return vdir` → `sub = .../agate`; `if os.path.isdir(os.path.join(sub, "scripts")): return sub` → `return vdir`；`:199` `.agate-version` 分支 + `:208` current 链分支各包一层 | ✅ 探测序、返回值、"顺序不可颠倒" 与 docstring「探测顺序不可颠倒（纯增量红线，TAG0032 决策 A1）」一致 |
| 根 `~/.agate/scripts/` = 随每次安装/升级刷新的单源副本（非软链）| `agate-install.py:292-319` `_sync_root_scripts`（单段 `shutil.copytree`）| ✅ |
| 权威口径指向 `UPGRADING.md`「版本管理生命周期」节 | `UPGRADING.md:43-44` 该节自声明「单一权威口径……遇分歧一律以本节为准」| ✅ 符合仓库单一权威哲学 |

**`agate/scripts/README.md:70`（`agate-install.py` 工具行）**：`无参 = 装 latest 指针（最新发布版）` → `无参 / \`latest\` = 装 latest 指针（最新发布版，幂等）`。与 `_usage():462`「无参 / latest」+ `main():472` 别名判定语义一致。✅

**`agate/AGENTS.md:91-98`（版本管理形态块）** 复审：命令块首行由 `agate-install.py`（无参）改为
`install.sh --versions`（新机一键）+ `agate-install.py latest`（更新到最新发布版，幂等；无参等价于 latest）；
块后新增 blockquote：元仓库整仓形态由 `_protocol_root` 两形态探测（`vdir/scripts` 先、`vdir/agate/scripts` 后）适配 + 根 `~/.agate/scripts/` 为随安装/升级刷新的单源副本（非软链）+ 完整口径以 `UPGRADING.md`「版本管理生命周期」节为权威。表述与脚本一致，比 `scripts/README.md` 更简，未复制完整对照表。`AGENTS.md:89`「Windows 复制模式升级后需重跑 `install-hook.py`」未被 fix-1 触碰，与 `UPGRADING.md` hook 重装时机 ② 仍一致。✅

**结论**：**ALIGNED**。首轮点名的三处描述版本机制的次级参考文档（`scripts/README.md:5` / `:70` / `AGENTS.md:91-98`）现已反映 TAG0032 全部新表面，且每点与脚本实现**语义一致**（非仅关键词存在）：探测序方向、别名幂等语义、副本单源语义均逐条核对。权威口径正确指向 `UPGRADING.md`「版本管理生命周期」节，符合仓库「单一权威 + 指针」哲学。

---

### A3: 一致性连锁 + 反向传播 — ALIGNED（复审转正）

**A3a 连锁**：首轮已全 ALIGNED（`install.sh --versions` → `exec agate-install.py latest` 调用链、`_protocol_root` 消费方 `resolve_version_root` / `resolve_hook_root` 单点归口、`resolve-entry.py` 0 hunk 受益方、纯增量红线经 `git diff` + BDD 实测锁死）。fix-1 未碰代码，A3a 不复核，沿用 ALIGNED。

**A3b 反向传播** — 首轮点名「应被影响但未在 diff 中」的文件，逐一复核 fix-1 传播情况：

| 文件 | 首轮判定 | fix-1 传播 | 复审结论 |
|---|---|---|---|
| `agate/scripts/README.md:5` / `:70` | 未更新 → NEEDS_HUMAN_REVIEW | ✅ L5 blockquote 补 `--versions` / `latest` 别名 / 元仓库形态 `_protocol_root` 探测序 / 根 scripts/ 单源副本 / 指向 UPGRADING；L70 工具行补 `latest` token | **ALIGNED**（见 A2 逐点核对）|
| `agate/AGENTS.md:91-98` / `:4` / `:89` | 未更新 → NEEDS_HUMAN_REVIEW | ✅ 形态块命令 + blockquote 补齐（见 A2）；`:89` Windows 口径未动、仍与 `UPGRADING.md` ② 一致 | **ALIGNED** |
| `agate/adr.md` | 未记录元仓库形态 / `_protocol_root` 探测序 / 决策 B1 → 见 A7 | ✅ 新增 ADR-012 | **ALIGNED**（见 A7）|
| `agate/platform-notes.md:166+` | 未提 `--versions` POSIX shell 假设 + 决策 B1 副本（非软链 → Windows 无退化）；低 severity 可选补充 | ✅ 指针形态节末补一段：`install.sh --versions` 保持 POSIX shell（无 bash 扩展）+ 决策 B1 根 `~/.agate/scripts/` 用 `shutil.copytree`（非软链）恰好规避 Windows 符号链接权限问题——比软链更平台无关，无 `latest`/`current` 那样的文本退化形态 | **ALIGNED**——与 `install.sh:14-46`（POSIX `[ ]` 测试、无 `[[ ]]`/数组等 bash 扩展）+ `_sync_root_scripts` copytree 一致 |
| `agate/tests/README.md:37-100` | 表本就非穷尽、既有 3 个 `test_agate_version_*` 亦未列、计数以 `count-tests.sh` 为准 → 无回归 | 未动（一致）| **ALIGNED（不复核，沿用首轮：既有非穷尽状态，非 TAG0032 引入的回归）** |
| `CHANGELOG.md` | P8 补 → 见 A5 | 未动（fix-1 未擅自写）| 见 A5 |

**结论**：**ALIGNED**。A3a 连锁沿用首轮全 ALIGNED；A3b 首轮点名的 4 处应被 `latest` 别名 / 元仓库形态 / 决策 B1 影响的次级文档（`scripts/README.md` / `AGENTS.md` / `adr.md` / `platform-notes.md`）fix-1 已**逐一传播到位**，`tests/README.md` 为既有非穷尽状态无回归，`CHANGELOG.md` 归 A5 的 P8 待办。首轮「单一权威 vs 处处同步」的真模糊，fix-1 以「一线文档 = UPGRADING 单一权威；次级参考 = 框架 + 指针」化解。

---

### A4: 测试覆盖 — ALIGNED（首轮结论，未复核）

fix-1 未碰任何测试文件（`git diff HEAD --name-status` 无 `agate/tests/**`）。首轮 A4 ALIGNED（18 个 TAG0032 用例 1:1 覆盖 BDD-1~14，全量 1483 passed，唯一失败 `test_agate_next_card.py::test_nc_cross_checkout_paths_hash_consistent` 为预存并行 flaky，四处独立记录，非本任务引入）继续有效。

**本轮定向实跑**（`timeout 180 /usr/bin/python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py -k tag0032 -p no:cacheprovider -q`）：
```
.......                                                                  [100%]
7 passed in 0.04s
EXIT=0
```
`test_tag0032_bdd_4_root_scripts_copy_semantics_documented` 只断言「副本」「重跑 `agate-install…` 刷新」「`repo/`」三点——`UPGRADING.md` L72-73 单源改写后三点仍满足，无断言精确匹配「叠加 / 后拷贝者胜」子串 → fix-1 的 UPGRADING 口径改写**未触发文档二值断言回归**。

---

### A5: 下游影响 + 文档传播 — ALIGNED（(b) 传播到位；(a)(c) = P8 待办清单，已确认）

**下游 gate 行为影响**：首轮已核实无破坏性回归——`_protocol_root` 仅对**元仓库整仓形态**版本目录改变 `_resolve_version_info` 返回值（`root: vdir → vdir/agate`），对「根即协议」形态探测序 1 先命中返回 `vdir` 不变（BDD-7 + 全量 1483 passed 锁死）；两形态皆无 → 返回 `vdir` 原样，`resolve-entry.py` 既有 fail-closed 未删。fix-1 未碰代码，此结论不变。

**(b) 文档传播（本轮 fix-1 的可执行部分）— ALIGNED**：
`agate/scripts/README.md` / `agate/AGENTS.md` / `agate/adr.md`（ADR-012）传播已落地并逐条核实（见 A2 / A3b / A7）。`agate/platform-notes.md` 补充亦到位。`README.md` / `README.zh-CN.md` / `agate/SETUP.md` / `agate/UPGRADING.md`「版本管理生命周期」节首轮已 ALIGNED，fix-1 未回退。

**(a) CHANGELOG 6 条语义变更条目 — P8 待办清单（已确认，fix-1 未擅自写）**：
`git diff HEAD --stat -- CHANGELOG.md` 为空 → fix-1 **未擅自写 CHANGELOG**（符合 dispatch 边界，`P4-implementation.md` fix-1 §「不做」明示「未写 CHANGELOG——A5 的 6 条 + UPGRADING §3 是 P8 步骤」）。P8 bump 时须补的 6 条（沿用首轮清单）：
1. `agate-install.py` 新增 `latest` 显式别名（= 无参 install，幂等）。
2. `install.sh --versions` 新增子命令——一键从零进入版本管理布局。
3. `agate-install.py` / `install.sh --versions` 对 legacy 软链布局 `~/.agate` **fail-closed 拒绝**（行为变化：此前会穿透软链把 `repo/`·`vX.Y.Z/` 静默建进源仓库）——附三步迁移指引。
4. `agate-install.py` `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时新增 `git fetch --tags --force --prune`（fail-open）——令重跑 `latest` 能跟随上游更高 tag。
5. resolve 链新增**元仓库整仓形态**版本目录支持（`_protocol_root`：`vdir/scripts` 先探、`vdir/agate/scripts` 后探）——GitHub 直装的整仓版本目录现可正确解析到协议子目录（RM-AG0058）。
6. 版本管理布局新增根 `~/.agate/scripts/` 入口副本（决策 B1，随每次安装 / 升级刷新）。

**(c) UPGRADING §3 版本章节 — P8 待办**：`check-protocol-consistency.py` CHECK 13（CHANGELOG 最新已发布版本 ↔ `agate/UPGRADING.md` §3 章节，`:1126-1152`）要求 P8 bump 时在 UPGRADING §3 新增本版本章节。「版本管理生命周期」是无编号节，不满足 §3 章节 —— 属常规 P8 动作。本轮 CHECK 13 实跑 **PASS**（无编号节不触发）。

**P8 前提条件（供主 Agent 在 P8 commit 时兑现）**：
- [ ] `CHANGELOG.md` 新版本段按上列 6 条补语义变更条目
- [ ] `agate/UPGRADING.md` §3 新增本版本章节（满足 CHECK 13）
- [ ] P8 后重跑 `check-protocol-consistency.py --strict-errors-only` 确认 CHECK 13 仍 PASS

**结论**：**ALIGNED（(b) 传播到位；(a)(c) 为 P8 常规动作，清单已列、前提已明）**。dispatch 结论口径允许「A5 附『P8 待办已确认』的可 commit 态」——本项即该态。无下游破坏性回归；本轮 fix-1 可执行的文档传播部分已全部落地。

---

### A6: 锚点表覆盖 — ALIGNED（首轮结论，未复核）

fix-1 未新增 CHECK、未改 BDD-NN heading / `###` 功能分组格式、未新增 frontmatter 字段、未新增需关键词匹配判定的协议规则。`agate/adr.md` 新增 ADR-012 为纯叙事内容，不进 CHECK 9 锚点表。`check-protocol-consistency.py --strict-errors-only` 本轮实跑 EXIT 0 / 0 ERROR 佐证。首轮 A6 ALIGNED 继续有效。

---

### A7: 设计原则一致性 — ALIGNED（复审转正）

首轮 NEEDS_HUMAN_REVIEW：`_protocol_root` 两形态探测序 + 决策 B1 副本机制是 `agate/adr.md` 未记录的架构决策，建议补 ADR-011（或扩 ADR-009 §后果），由人工裁定时机。fix-1 选「本轮即补新 ADR」。

**ADR 编号核查**：`grep "^## ADR-" agate/adr.md` → ADR-001 … **ADR-011**（TAG0024「引导型 CLI 工具的权限是早纠错，不是安全边界」，`adr.md:352`）为现有最大。fix-1 取 **ADR-012 = ADR-011 + 1**，正确。dispatch-context 文字曾写「新增 ADR-011」，但同处括注要求「按 adr.md 现有最大 +1 核实」——现有最大已是 ADR-011，故 +1 = ADR-012；`P4-implementation.md` fix-1 §「编号说明」已记录此推理。**编号无冲突、无跳号**。

**格式核查**（六节对齐 ADR-009）：
| ADR-009 节（`adr.md:265-303`）| ADR-012 节（`adr.md:381-431`）| 对齐？ |
|---|---|---|
| `### 状态` / `### 语境` / `### 决策` / `### 理由` / `### 权衡` / `### 后果` | `### 状态` / `### 语境` / `### 决策` / `### 理由` / `### 权衡` / `### 后果` | ✅ 六节完全一致、同序 |

**内容核查**（对照脚本实现）：
- **(a) 两形态 + `_protocol_root` 探测序**：ADR-012 §决策记「探测序 1 `isdir(vdir/scripts)` → 返回 `vdir`（根即协议，零回归）；探测序 2 `isdir(vdir/agate/scripts)` → 返回 `vdir/agate`（元仓库整仓）；皆无 → 返回 `vdir` 原样，下游 `resolve-entry.py` 拼 `<root>/scripts/<gate>` 不存在时命中既有 fail-closed（exit 1），不新增静默放行」——与 `agate_common.py:166-179` `_protocol_root` 三分支**逐字一致**。
- **「探测序不可颠倒」红线**：ADR-012 §决策记「若先探 `vdir/agate/scripts`，某些『根即协议』且恰好含 `agate/` 子目录的既有部署方会被改判协议根 → 破坏 ADR-009 §理由 2 的向后兼容红线」——与 `_protocol_root` docstring「探测顺序不可颠倒（纯增量红线，TAG0032 决策 A1）」一致，且给出了**具体的破坏场景**（不只是断言）。
- **current 链分支赋值顺序**：ADR-012 记「current 链分支须**先** `version = os.path.basename(cur)` **再** `root = _protocol_root(cur)`，顺序倒置会让 `AGATE_VERSION` 从 `vX.Y.Z` 回归为 `agate`」——与 `agate_common.py:206-208`（含代码注释「顺序不可倒（I-1 红线）：version 从 cur 取，root 从 `_protocol_root(cur)` 取」）一致。
- **(b) 决策 B1 副本机制**：ADR-012 记「单源 `shutil.copytree(..., dirs_exist_ok=True)`（非软链），随每次安装/升级重建刷新；真实 agateon 每个发布 tag 的 `agate/scripts/` 恒含全套版本工具，故单源 copytree 即覆盖全部入口命令；`repo/` 或某 `vX.Y.Z/` 被删不影响已建副本（独立实体，不回链）；副本不参与 hook 版本解析」——与 `agate-install.py:292-319` `_sync_root_scripts` + `UPGRADING.md` L71-80 一致。
- **关联声明**：ADR-012 §后果末句「本 ADR **扩展** ADR-009（版本管理根 + resolve-entry 固定入口），**不替代**；ADR-009 的四层解析优先级与 legacy 兜底红线继续有效」——恰当，明确了与 ADR-009 的层级关系，未产生 ADR 冲突。§语境亦回指 `docs/reviews/agate-alignment-review-2026-09-07-TAG0032.md` A7 作为补 ADR 的动因，可溯源。

**结论**：**ALIGNED**（A7 无 MISALIGNED 态）。ADR-012 编号（现有最大 +1）、格式（六节对齐 ADR-009）、内容（`_protocol_root` 探测序含不可颠倒红线的具体理由 + 决策 B1 副本机制，均与脚本实现逐条一致）、与 ADR-009 的关联声明（扩展不替代）均恰当。首轮「未记录的架构决策」缺口消解。

---

## DESIGN_GAP 复核（角色文件原则 6）

首轮已核实 5 处 `[DESIGN_GAP:]` ↔ `P7-consistency.md` 5 处 `[DESIGN_GAP_REVIEWED:]` 全部 `REVIEWED-ACCEPTED`（`status: approved`）。本轮复核 fix-1 对 DESIGN_GAP 的处理：
- **DESIGN_GAP 1（M2 双 copytree）**：fix-1 §③（`P4-implementation.md`）已删 layer-1 自拷贝、回退单源 copytree；本轮 A1 复核 `UPGRADING.md` L71-73 文档口径亦已追平 → 该 GAP 的**文档滞后残留亦消解**。
- **DESIGN_GAP 2（`latest` 别名）/ 3（`install.sh --versions` exec 路径）/ 4（`_ensure_repo` fetch）/ 5（v0.50.0 §① 反引号微调）**：fix-1 未改代码，P7 REVIEWED-ACCEPTED 结论不变。
- `P4-implementation.md` fix-1 明确「**不新增 DESIGN_GAP**」，且旧「决策/偏差声明」中的 2 条 `[DESIGN_GAP: 双 copytree]` / `[DESIGN_GAP: install.sh --versions 自主改为 $SCRIPT_DIR]` 已由 P4 批 2 修复消解。**本轮无新增 DESIGN_GAP**。

---

## 回归确认（本轮核查项 6）

| 项 | 命令 / 方法 | 结果 |
|---|---|---|
| fix-1 只动文档/ADR | `git diff HEAD --name-status` | ✅ 仅 `agate/scripts/README.md` / `agate/AGENTS.md` / `agate/adr.md` / `agate/UPGRADING.md` / `agate/platform-notes.md` 5 个文档/ADR 文件 + 3 个工作区任务追踪文件（`P4-implementation.md` fix-1 节 / `P4-progress.md` 落盘 / `gate-events.jsonl` 编排产物）。**无 `.py` / 无 `agate/tests/**` / 无 `install.sh` / 无 `CHANGELOG.md`** |
| 一致性检查 0 ERROR | `timeout 120 /usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` | ✅ **EXIT 0，0 ERROR，329 WARNING**（均既有叙事文件脚本名引用，与首轮基线一致，未新增）。CHECK 9（协议-脚本结构对齐）**PASS**；CHECK 10（文档脚本名引用漂移）**WARN**（既有叙事，非新增；ADR-012 提及的 `_protocol_root` / `_sync_root_scripts` 是函数名非脚本文件名，不触发 CHECK 10 脚本名漂移）；CHECK 13（CHANGELOG↔UPGRADING §3）**PASS** |
| pytest tag0032 全绿 | `timeout 180 /usr/bin/python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py -k tag0032 -p no:cacheprovider -q` | ✅ **7 passed，EXIT 0** |
| 无新 DESIGN_GAP | 见上「DESIGN_GAP 复核」 | ✅ 无新增 |

**结论**：fix-1 为纯文档 + ADR 传播，未引入代码/测试回归；一致性检查与定向 pytest 均绿；无新 DESIGN_GAP。

---

## 闭环结论

| 结论 | 项 | 主 Agent 动作 |
|------|----|--------------|
| ALIGNED | A1（KNOWN_DEVIATION 已消解）、A2、A3、A4、A6、A7 | 通过，可 commit |
| ALIGNED（附 P8 前提）| A5 | 可 commit；P8 兑现「P8 前提条件」3 项（CHANGELOG 6 条 + UPGRADING §3 章节 + P8 后 CHECK 13 复跑）|

**首轮 4 项 NEEDS_HUMAN_REVIEW（A2 / A3 / A5 / A7）全部消解** —— A2/A3/A7 转 ALIGNED（fix-1 文档传播 + ADR-012 到位），A5 的 (b) 传播部分 ALIGNED、(a)(c) 明确为 P8 待办清单（已列 6 条 + 前提条件）。**A1 KNOWN_DEVIATION 消解**（`deviation_count` 1 → 0）。**无回归**（git diff 只 5 文档/ADR 文件 + 3 工作区文件、consistency 0 ERROR、pytest tag0032 7 passed、无新 DESIGN_GAP）。

**MISALIGNED：0　NEEDS_HUMAN_REVIEW：0**

→ **SELF-GATE Layer 1 复审：通过**（A5 为「P8 待办已确认」的可 commit 态）。

[PROD_NOT_TOUCHED] — 复审全程未改代码 / 文档 / git。
