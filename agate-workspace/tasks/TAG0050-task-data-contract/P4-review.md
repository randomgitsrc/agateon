---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G2.md
trace_id: TAG0050-P4-20261008
agent: leader
status: approved
---

# P4 实现评审（专家组汇总）— TAG0050 合批 G2（B + C）

> 角色：`leader`（专家组组长；**只汇总，不发表新意见**）。
> 对象：G2（批次 B 写入工具与契约单源 + 批次 C 生产接触安全门）**未提交**改动，HEAD `54a814fc`，
> 分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 依据：`P4-dispatch-context-leader-G2.md`；输入 = 两评审角色（`review`、`cso`）的首轮 + 第 2 轮整改（fix2）复审文件。
> 汇总规则：不发表新意见，只汇总；任何未解决 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved。
> `[PROD_NOT_TOUCHED]`（组长仅读输入并汇总，未接触生产环境）。

## 0. 汇总结论

**`status: approved`** —— 首轮 `review` 与 `cso` **双双 `rejected`**；经 **fix2 整改**后，两方**复审均 `approved`**，
首轮阻断项 **B1/H1（review）与 F-1/F-2/F-3（cso）全部独立验证闭合**，**无未解决 BLOCKER**。

| 汇总指标 | 值 |
|---|---|
| 首轮 verdict | `review` = rejected（B1 BLOCKER + H1 HIGH + M1/M2 MEDIUM + L1–L6 LOW）／`cso` = rejected（F-1 HIGH **BLOCKER** + F-2/F-3 MEDIUM + F-4/F-5/F-6 LOW） |
| 复审 verdict | `review` = **approved**（B1/H1 独立验证闭合；M1/M2/L1–L6 全 ALIGNED）／`cso` = **approved**（F-1/F-2/F-3 全闭合；无新安全阻断） |
| 未解决 BLOCKER | **0** |
| 残余非阻断项 | cso 复审新观察 2 LOW（F-1 降级 fail-open、F-3 扫描派生次进程）+ F-4/F-5/F-6 仍成立（已声明/非安全）+ review 复审 1 项 xdist flake 观察 |
| 是否阻塞发布 | **否** |

> 判定：两角色首轮的阻断项**同源**（review B1 ≡ cso F-1：BDD-46 `derive` 现算读取未实现），
> 均由 fix2 落地并经**两方独立复现**（含负向控制）确认；H1 亦经「照抄修复命令 → 重新提交转绿」独立验证。

## 1. 各角色评审汇总表

| 角色 | 首轮 verdict | 首轮关键 finding | 复审 verdict | 闭合方式 |
|---|---|---|---|---|
| `review` | **rejected** | B1（**BLOCKER**）BDD-46 derive 现算未实现、验收用例空转；H1（HIGH）BDD-52 修复命令在非 P6 主产出上不可执行（连带 BDD-49 未真验证）；M1/M2（MEDIUM）；L1–L6（LOW） | **approved** | B1/H1 **独立验证闭合**；M1/M2/L1–L6 全 **ALIGNED**（实现或显式登记/声明） |
| `cso` | **rejected** | F-1（HIGH，**BLOCKER**）同 B1（伪造 P6 汇总被信任）；F-2（MEDIUM）系统字段拒写非契约语义；F-3（MEDIUM）CARD 块排除可伪造绕过；F-4/F-5/F-6（LOW） | **approved** | F-1/F-2/F-3 全 **CLOSED**；F-4/F-5/F-6 仍成立（已声明/非安全）；**无新安全阻断** |

## 2. 首轮阻断项闭合明细（经首轮 → fix2 → 复审）

| # | 来源 | 首轮问题 | 复审判定 | 闭合方式（复审所录证据） |
|---|---|---|---|---|
| **B1** | review（BLOCKER）；= cso F-1 | BDD-46「`agate-md-field-get` 读 `writer: system` 字段按 `derive` 现算」未实现（`agate_schema.derive()` 零生产消费方），验收用例对半空转 | **ALIGNED（闭合）** | `agate-md-field-get.py` 新增 `_system_field_spec()` + 现算分支：非 legacy 且快照可用时调 `agate_schema.derive(spec["derive"], fm)`，忽略文件值。两复审独立复现：伪造 `pass: 999`+FAIL → get=2/fail=1；下游 `check-gate.py P6` 报 FAIL=1 rc=1（伪造不再通过）；负向控制（禁用 derive）→ 回退伪造值 999。`test_bdd_46` 重写为「文件写 `pass: 999` + results 含 FAIL → 断言现算值」取得判别力 |
| **H1** | review（HIGH） | BDD-52 修复命令 `set prod_touched …` 在非 P6 主产出上 `非法 key` 不可执行（连带 BDD-49 未真验证） | **ALIGNED（闭合）** | `prod_touched` 纳入声明文件合法 key（快照 `files` 定义）；修复命令与中文注解**分行**输出。两复审独立复现：非 P6 主产出缺字段 → hook 报错 → **照抄执行** rc=0 写入 → 重新提交 **rc=0 转绿**；`test_bdd_49` 改为真「提交报错→照抄执行→转绿」用例 |
| **F-2** | cso（MEDIUM） | 系统字段拒写非契约 `writer: system` 语义（靠证据字段表偶发耦合） | **CLOSED** | `_cmd_set` 在可写性判定**之前**加契约驱动判定：凡快照登记 `writer == "system"` 一律拒写并指明 `derive` 来源。独立验证注入**未来**系统字段（不在证据字段表内）亦被拒；`set prod_touched true`/`set agent x` 未被误伤 |
| **F-3** | cso（MEDIUM） | T4 的 `AGATE_CARD` 块排除是纯文本判定，可伪造 CARD 起止注释对绕过 | **CLOSED** | 收紧为「真实注入块」：`_card_block_verified()` 要求文件名匹配 `-dispatch-context-*.md` **且**块内容 sha256 == 当前阶段卡片期望值（与 2p 同源）；未闭合 START fail-safe 参与扫描。独立验证：伪造块/非 dispatch-context 文件/未闭合块内标记**仍拦**（rc=1）；真实卡片仍被排除（hash 逐字节 MATCH） |

> 同源确认：review B1 与 cso F-1 为**同一缺陷**，由 fix2 一处落地闭环，两方**各自独立复现**。

## 3. 首轮 MEDIUM/LOW 处理明细（复审裁定）

| # | 来源 | 首轮问题 | 复审裁定 | 方式 |
|---|---|---|---|---|
| M1 | review | BDD-45 `agate-config` set/unset/explain 往返用例未真往返 | **ALIGNED** | 用例改真往返（init→set→get/show/explain 可见→unset 后消失、raw 无残留；无声明文件时 set 不创建） |
| M2 | review | BDD-51 `traps.T1.downgrade` 是惰性数据（T1/T2/T3 未接线） | **ALIGNED（显式登记）** | `P4-implementation-G2.md:164` 以 `[DESIGN_GAP]` 显式登记 T1/T2/T3 接线为后续批待办（符合 dispatch「接线或显式登记」二选一裁定） |
| L1 | review | `check-frontmatter._declaration_files` 用 `current_level`，与 `pre-commit-gate` 的 `task_level` 口径不一致 | **ALIGNED** | 改用 `task_level`（回退 `current_level`），两处同口径（diff 实测一致） |
| L2 | review | `_primary_output_for`/`_declaration_files` 的 `task_level` 与 `requirement_active` 的 `level_at_phase` 口径不一致 | **ALIGNED（显式声明）** | 结构面（任务级最新快照）vs 时间面（`level_at_phase`）刻意不统一，代码注释 + `P4-implementation-G2.md:159` 声明 |
| L3 | review | 安全门扫描面 = 任务目录内全部暂存文件（偏宽 fail-safe） | **ALIGNED（显式声明）** | 保留偏宽并在 `P4-implementation-G2.md:160` 声明偏差 |
| L4 | review | `pre-commit-gate.py` 保留字面 `[PROD_TOUCHED]` 正则（DESIGN_GAP-5） | **ALIGNED（已裁定）** | 声明于 `P4-implementation-G2.md:161` |
| L5 | review | 类型错误文案由 Python 名改 JSON 名，无测试守护 | **ALIGNED** | 守护用例 `test_l5_frontmatter_type_error_json_type_names` 断言「应为 integer」，实测通过 |
| L6 | review | `_local_iter_errors`/`_local_max_depth` 为不完全第二份递归遍历 | **ALIGNED（已裁定）** | 声明于 `P4-implementation-G2.md:162`（门控 + 白名单守护） |

## 4. 残余非阻断项（复审所录，**均非本批引入或非安全绕过**）

| 来源 | 级别 | 内容 | 复审倾向 |
|---|---|---|---|
| cso 复审 §四.1 | LOW（新观察） | F-1 的**降级路径静默 fail-open**——`agate_common`/`agate_schema` 不可导入（安装破损）时 `_system_field_spec` 返回 None，`_get` 回退文件值且**不告警** | 仅安装破损时出现，与既有降级哲学（F-5/L6）一致；建议后续降级时补一行 WARNING（可选） |
| cso 复审 §五 | LOW（新观察） | F-3 的 `_expected_card_hash()` **每次扫描派生一次** `agate-next-card.py` 子进程 | 有界（按暂存任务数）、失败即 `None`→不排除（fail-safe，更严），非 DoS 放大 |
| cso 复审 F-4/F-5/F-6 | LOW | F-4 单源降级字面仍为 dash_only（安装破损下 BDD-54 形态 fail-open，已声明 DESIGN_GAP-5/L4）；F-5 `_local_*` 降级副本仍保留（L6 已声明，L1 口径已统一）；F-6 `agate-config` 非原子写 / `os.getcwd()`（非安全项） | 均**仍成立**、已声明或非安全，不阻断 |
| review 复审 §5 | 非阻断观察 | 首轮全量并行跑（未加 `--reruns`）曾出现一次 `test_pre_commit_hook.py::test_it8_phase_p2_missing_design_blocked` 失败，**未能复现**（单跑过、文件内 62 passed、CI 口径 `--reruns 1` 回到恰为登记的 8 个预期红灯） | 判为 xdist 跨文件并行隔离的既有 flake（CI 以 `--reruns 1` 兜底），**非 G2 fix2 引入** |
| 两复审一致 | 非阻断 | 登记预期红灯 8 条（BDD-43/59/60/63/66/69/71/76，属 D/E/F 批） | 与 `P4-implementation-G2.md §6` 一致，非 G2 引入 |

## 5. 门槛判定

- **`status: approved`** —— 汇总规则满足：全票无未解决 BLOCKER；两角色复审均 approved；首轮 B1/H1/F-1/F-2/F-3 全闭合。
- **分歧**：无（两角色对同源缺陷 B1≡F-1 及各自整改项判定一致闭合）。
- **残余项处理建议**（转交主 Agent，组长不裁决）：cso 复审两项新 LOW 观察可选随本批补 WARNING/缓存优化，或登记 DEBT 留痕后放行。

## 6. 被汇总文件清单（只读，未编辑）

- 首轮：`P4-review-G2.md`（review，rejected）、`P4-review-cso-G2.md`（cso，rejected）
- 复审：`P4-review-rereview-G2.md`（review，approved）、`P4-review-cso-rereview-G2.md`（cso，approved）
- 整改指引：`P4-dispatch-context-implementer-G2-fix2.md`
- 历史：`P4-review.md`（原 G1 汇总，已被本汇总文件覆盖）

## 7. 环境隔离

`[PROD_NOT_TOUCHED]` —— 组长仅读取上述输入文件并写出本汇总文件，未接触生产环境，未执行任何写仓/破坏性命令。
