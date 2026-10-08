---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G1.md
trace_id: TAG0050-P4-20261008
agent: leader
status: approved
---

# P4 实现评审（专家组汇总）— TAG0050 合批 G1（A2 + A3 + A4）

> 角色：`leader`（专家组组长；**只汇总，不发表新意见**）。
> 对象：G1 未提交改动，HEAD `b0a16c3a`，分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 依据：`P4-dispatch-context-leader-G1.md`；输入 = 两评审角色（`review`、`cso`）的首轮 + fix3 复审文件。
> 汇总规则：不发表新意见，只汇总；任何未解决 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved。
> `[PROD_NOT_TOUCHED]`（组长仅读输入并汇总，未接触生产环境）。

## 0. 汇总结论

**`status: approved`** —— 首轮 `review` 与 `cso` 双双 `rejected`；经 **fix3 整改**后，两方**复审均 `approved`**，
**K1–K6 全票闭合**，**无未解决 BLOCKER**。

| 汇总指标 | 值 |
|---|---|
| 首轮 verdict | `review` = rejected（2 CRITICAL）／`cso` = rejected（1 BLOCKER） |
| 复审 verdict | `review` = **approved**（K1–K6 全 ALIGNED）／`cso` = **approved**（K1–K6 全 ALIGNED） |
| 未解决 BLOCKER | **0** |
| 残余非阻断项 | 2 MEDIUM + 1 LOW（复审新观察）+ 首轮 MINOR/LOW（未列入本轮 K1–K6 整改范围） |
| 是否阻塞发布 | **否** |

> 判定：两角色首轮的阻断项同源（review C1/C2 ≡ cso F-2/F-1），均由 fix3 的 K1–K4 整改闭环，并经两方**独立复现**（负向控制）确认。

## 1. 各角色评审汇总表

| 角色 | 首轮 verdict | 首轮关键 finding | 复审 verdict | 闭合方式（K 项） |
|---|---|---|---|---|
| `review` | **rejected** | C1（CRITICAL）A4 凭证自指、C2（CRITICAL）A2 等级检查缺失；M1/M2/M3（MINOR） | **approved** | C1 → **K3**（同 K2）；C2 → **K4** |
| `cso` | **rejected** | F-1（HIGH，**BLOCKER**）合并提交静默删/改账本；F-2（HIGH）M 义务核验空转；F-3/F-4/F-5（MEDIUM）；F-6/F-7（LOW） | **approved** | F-1 → **K1**；F-2 → **K2**；F-5 → **K5**；F-3 → **K6** |

## 2. K1–K6 闭合明细（经首轮 → fix3 → 复审）

| # | 来源 | 整改项 | 复审判定 | 闭合方式（复审所录证据） |
|---|---|---|---|---|
| **K1** | cso F-1（HIGH，BLOCKER） | 合并提交（evil merge）可静默删/改账本，A2 回放漏检 | **ALIGNED** | 账本最终状态检查与逐提交回放**解耦**：`rev-list <base>..<head>`（含合并提交）、`diff --name-status --no-renames`（取改名被摘除的源路径）、在「无任务改动 → SKIP」**之前无条件执行**；补负向用例。两复审**独立复现** evil merge 删账本 → `FAIL 账本` rc=1，并以「回退 `--no-merges` 即退化为 SKIP/rc=0」作因果证明 |
| **K2** | cso F-2（HIGH） | M 义务机械核验空转，负向控制打错对象（F13 未根治） | **ALIGNED** | `obligations.yaml` 抽样 6 条 M（覆盖 P1/P2/P8）`test` 改指**真实行为凭证** `test_tag0050_obligation_behavior.py::test_obl_*`，`enforced_at.function` 精确到 `gate_p8` 等；BDD-42 改为对**执行分支**真变异。两复审独立复现：删 `check-gate.py` 交付分支 → 行为凭证转红（基线绿/变异红）。设计 §2.9 明确允许**抽样** |
| **K3** | review C1（CRITICAL） | A4 凭证自指（`test` 只断言 YAML 文本） | **ALIGNED** | 与 K2 同根因；6 条 `test` 改指真实行为凭证，其余 54 条保留登记辅助断言 |
| **K4** | review C2（CRITICAL） | 设计 §2.4 第 4 点「新任务等级」CI 检查缺失；`test_bdd_30` 形同虚设 | **ALIGNED** | `_ci_level_checks`（新增任务目录 `contract_level` ≥ merge-base 处 `LEVELS.yaml` 最大等级）落地；`test_bdd_30`（跨升级不误报）/`test_bdd_30b`（低于则 FAIL）转绿 |
| **K5** | cso F-5（MEDIUM） | 协议版本分支①（逐提交 `.agate-version` 选协议根）未实现 | **ALIGNED** | docstring 显式降级「未实现」+ 补齐 F-5 影响 2 已知绕过面说明；`P4-implementation-G1.md` 登记 `[DESIGN_GAP]` |
| **K6** | cso F-3（MEDIUM） | CI 可信锚点实为 advisory，缺降级声明 | **ALIGNED** | `P4-implementation-G1.md` 专节写明「`gate-backstop` 未设 required ⇒ 回放为 advisory，回放失败不阻塞合并」 |

> SELF-GATE 对齐：`…-G1-rereview2.md` 的 H1–H3 已判 ALIGNED（`P4-review.md` 首轮 §1 第 5 项确认）。

## 3. 残余非阻断项（复审所录，**均非本批引入或非安全绕过**）

| 来源 | 级别 | 内容 | 复审倾向 |
|---|---|---|---|
| review 复审 §8 | MEDIUM | `_ci_ledger_checks` 账本路径过滤过宽（仅 `endswith(gate-events.jsonl)`，未限定 `agate-workspace/tasks/` 前缀）→ 把 `agate/tests/fixtures/**/gate-events.jsonl` 黄金夹具当真实账本误报 FAIL；**已核非本轮 fix3 引入** | 建议随本批加 `tasks` 前缀限定 + 回归用例，或登记 DEBT 留痕后放行 |
| cso 复审 N-1 | MEDIUM | K1 解耦后的账本检查对**整目录任务改名**误判 FAIL——pre-commit 规则 4 对该场景有 BDD-25 显式豁免（rc=0），CI 新检查无该豁免且 `--no-renames` 拆成 D+A ⇒ 同一提交「本地 PASS / CI FAIL」。**误报/过度拦截，非安全绕过**；`gate-backstop` 转 required 后才会升级影响 | 建议复刻 pre-commit 的目录改名豁免（`-M` 取源/目标并按 `_dir_moved_away` 判），或改用 `--name-status -M` |
| cso 复审 N-2 | LOW | `_ci_level_checks` 用 `--no-renames` 会把改名目录当「新增」，对老任务改名可能等级误报（实际被 N-1 吸收） | 与 N-1 同源，一并修正 |
| review 首轮 M1/M2/M3 | MINOR | M1 squash 仓库 push「只做账本检查」口径未实现；M2 `scripts/README.md` 声称「只回放改动任务目录的提交」与实现（遍历全部非合并提交）不符；M3 `obligations.yaml` `OBL-X-10` statement 口径陈旧 | 首轮即判**非阻断**，**未列入** K1–K6 整改范围 |
| cso 首轮 F-6/F-7 | LOW | F-6 phase「唯一写入口」为约定而非机械强制（设计有意取舍）；F-7 `check-obligations.py` docstring 候选顺序与代码不一致（纯文档瑕疵） | 非阻塞观察，**未列入** K1–K6 整改范围 |
| review 首轮 §4 观察 | 非阻塞 | 分支①未实现（→ 已由 K5 降级登记）；回放遍历全部非合并提交（SELF-GATE A2 备注）；`agate-retreat-state.py` 仍直接写 phase（疑为范围外）；A7 ADR 仍待人工确认 | 供主 Agent 裁定/留痕 |

## 4. 门槛判定

- **`status: approved`** —— 汇总规则满足：全票无未解决 BLOCKER；两角色复审均 approved；K1–K6 全闭合。
- **分歧**：无（两角色在 K1–K6 判定上一致 ALIGNED）。
- **残余项处理建议**（转交主 Agent，组长不裁决）：review 复审 §8 与 cso 复审 N-1/N-2 建议随本批补最小修正 + 回归用例，或登记 DEBT 留痕后放行。

## 5. 被汇总文件清单（只读，未编辑）

- 首轮：`P4-review.md`（原 review 首轮，已被本汇总文件覆盖）、`P4-review-cso-G1.md`
- 复审：`P4-review-rereview-G1.md`（review，approved）、`P4-review-cso-rereview-G1.md`（cso，approved）
- 整改指引：`P4-dispatch-context-implementer-G1-fix3.md`

## 6. 环境隔离

`[PROD_NOT_TOUCHED]` —— 组长仅读取上述输入文件并写出本汇总文件，未接触生产环境，未执行任何写仓/破坏性命令。
