---
phase: P4
task_id: TAG0050
type: review
parent: P4-implementation-G3.md
trace_id: TAG0050-P4-20261008
agent: leader
status: approved
---
# P4 实现评审（专家组汇总）— TAG0050 合批 G3（D + E + F）

> 角色：`leader`（专家组组长；**只汇总，不发表新意见**）。
> 对象：G3（批次 D 验收结论与证据 + 批次 E 成对声明 + 批次 F 代理判定）**未提交**改动，HEAD `b746d07d`，
> 分支 `feat/TAG0050-task-data-contract`，协议 v0.79.0。
> 依据：`P4-dispatch-context-leader-G3.md`；输入 = 两评审角色（`review`、`cso`）的首轮 + 第 2 轮整改（fix2）复审文件。
> 汇总规则：不发表新意见，只汇总；任何未解决 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved。
> `[PROD_NOT_TOUCHED]`（组长仅读输入并汇总，未接触生产环境）。

## 0. 汇总结论

**`status: approved`** —— 首轮 `review` **`rejected`**（**BLOCKER-1** + MINOR-2/3/4）、`cso` **`approved`**
（F-1/F-2 MEDIUM + F-3..F-6 LOW，非阻断）；经 **fix2 整改**后，两方**复审均 `approved`**：
首轮阻断项 **BLOCKER-1** 独立验证闭合，**MINOR-2/3/4** 闭合且新用例具改前红判别力，
cso **F-1/F-2 闭合**、**F-3 已修 / F-4 已登记 / F-5/F-6 已声明**，**无未解决 BLOCKER、无新阻断**。

| 汇总指标 | 值 |
|---|---|
| 首轮 verdict | `review` = rejected（BLOCKER-1 BLOCKER + MINOR-2/3/4）／`cso` = approved（F-1/F-2 MEDIUM + F-3–F-6 LOW，最高 MEDIUM，非阻断） |
| 复审 verdict | `review` = **approved**（BLOCKER-1 独立复现闭合；MINOR-2/3/4 全 ALIGNED 且改前红）／`cso` = **approved**（F-1/F-2 闭合；F-3 已修、F-4 已登记、F-5/F-6 已声明；无新阻断） |
| 未解决 BLOCKER | **0** |
| 残余非阻断项 | cso 复审新增 2 LOW（F-2′ 子目录 shadow 绕过、F-2″ basename 口径差）+ F-5/F-6 声明边界仍成立；review 复审 2 项非阻断观察（D7 形态判据较严、consistency WARNING 412 vs 410） |
| 是否阻塞发布 | **否** |

> 判定：首轮唯一阻断项 **BLOCKER-1**（非 legacy 任务 P6.5 `criteria` 读取链路断裂 → P6→P7 死锁）
> 由 fix2 落地并经 **review 独立复现**（正向 exit 0 / 负向 exit 1 / 判别力反证转红）确认；
> cso 首轮两项 MEDIUM 为防御纵深缺口（最高 MEDIUM，首轮即判非阻断），fix2 后经 **cso 独立验证**闭合。

## 1. 各角色评审汇总表

| 角色 | 首轮 verdict | 首轮关键 finding | 复审 verdict | 闭合方式 |
|---|---|---|---|---|
| `review` | **rejected** | BLOCKER-1（**BLOCKER**）P6.5 `criteria` 读取链路断裂（`read_judge_verdict` 不透传 → 非 legacy 恒 exit 1）；MINOR-2（D8 弱化）、MINOR-3（D7 弱化）、MINOR-4（`gate_p7` 取值域未校验） | **approved** | BLOCKER-1 **独立复现闭合**；MINOR-2/3/4 全 **ALIGNED**（新用例具改前红判别力） |
| `cso` | **approved** | F-1（MEDIUM）`run:<k>` sha256 在 `cmd_run` 事件缺 `sha256` 时 fail-open；F-2（MEDIUM）`declaration_files` glob 两消费方语义分叉（子目录文件逃逸 frontmatter 强制）；F-3–F-6（LOW） | **approved** | F-1/F-2 全 **CLOSED**；F-3 已修、F-4 已登记、F-5/F-6 已声明；**无新安全阻断** |

## 2. 首轮阻断项闭合明细（经首轮 → fix2 → 复审）

| # | 来源 | 首轮问题 | 复审判定 | 闭合方式（复审所录证据） |
|---|---|---|---|---|
| **BLOCKER-1** | review（BLOCKER） | `agate_common.read_judge_verdict()` 返回值不含 `criteria` ⇒ `check-judge-verdict.py` 的 `verdict.get("criteria")` 恒 `None` ⇒ 非 legacy 任务 P6.5 恒 exit 1（且更早因系统字段缺失先报错）⇒ **P6→P7 转移死锁**；该路径无任何测试守护，前序 SELF-GATE A1「ALIGNED」因此不成立 | **ALIGNED（闭合）** | `read_judge_verdict()` 透传 `criteria`（`agate_common.py:601-608`）；`check-judge-verdict.py` 把 `criteria_total`/`criteria_passed`/`verdict_evidence` 强校验**移到 `_non_legacy` 判定与现算之后**（legacy 保留旧口径）。review 独立复现（仓外副本手工构造任务）：声明 `criteria` 且 `status: passed` → **exit 0**；缺 `criteria` → **exit 1**；**判别力反证**（删除 `criteria` 透传 → 转红）。文档承诺（`UPGRADING.md`/`CHANGELOG.md` 对 P6.5 `criteria` 现算）与修复后实现**一致** |

> 无其他首轮 BLOCKER；首轮 `cso` 最高为 MEDIUM（非阻断），其 F-1/F-2 闭合见 §3。

## 3. 首轮 MEDIUM/LOW 处理明细（复审裁定）

| # | 来源 | 首轮问题 | 复审裁定 | 方式 |
|---|---|---|---|---|
| MINOR-2 | review | D8 截图「须带 vision，无视觉能力才退 manual_review」退化为「二选一即可」，且以 `"screenshots/" in refs` 子串识别 UI 条目 | **ALIGNED** | 读 `read_vision_tri_state`：能力=GAP → 须 `manual_review`，否则须 `vision`；截图判定改结构化（目录段精确比较）。改前红用例 2 条（GAP 分支 + 结构化判定） |
| MINOR-3 | review | D7 仅单向启发式（evidence FAIL vs results PASS），未覆盖反向/字段形态/多 JSON 合并 | **ALIGNED** | 补全四类判据（正向 + 反向 + 形态 + 多 JSON 合并冲突），**面不窄于被取代的 `agate-evidence-consistency.py`**；改前红用例 2 条（形态非列表 / 非映射元素） |
| MINOR-4 | review | `gate_p7` 的 `design_gap_reviews.verdict` / `basis` 取值域未校验 | **ALIGNED** | 加枚举校验（`verdict ∈ {accepted,rejected,followup}`；`basis ∈ {in_bdd,out_of_scope} ∪ followup:DEBT<n>`），越界 → ERROR；仅非 legacy 分支，legacy 不变；改前红用例 2 条 |
| F-1 | cso（MEDIUM） | `run:<k>` 的 sha256 校验在事件缺 `sha256` 字段时**静默放行**（fail-open） | **CLOSED** | 收紧为 fail-closed：`k`/`log`/`sha256` 任一缺失/空/非字符串 → 报「事件不完整」，与「sha256 不匹配」**文案可区分**。cso 独立验证：`check-gate.py P6` 各分支 rc=1/1/2，测试 passed；未误伤合法路径（`cmd_run` 唯一生产者 `agate-run.py --task` 恒写三字段） |
| F-2 | cso（MEDIUM） | `declaration_files` glob 被 `glob`（聚合）与 `fnmatch`（frontmatter 强制）以不同语义消费，`P4-implementation/**/*.md` 直接子文件逃逸 frontmatter 强制；`check-frontmatter` 的 `task_dir=dirname(file)` 使子目录文件恒 legacy | **CLOSED** | 统一匹配语义到单源 `agate_common.match_declaration_file` / `declaration_file_paths`；`check-frontmatter`/`pre-commit-gate` 均走单源并经 `task_dir_for_file` 向上定位任务根。关键不变式：**命中面 ⊇ 枚举面**，无「未匹配即免检」逃逸。cso 独立验证：子目录缺 frontmatter → rc=1；6/6 消费方单源、无残留 `declaration_globs` |
| F-3 | cso（LOW） | `run:<k>` 引用缺「非空文件」判据 | **ALIGNED（已修）** | 补 `getsize==0` 判据（`agate_common.py:1742-1748`）；空日志 + 正确 sha → 报「日志为空文件」；测试 passed |
| F-4 | cso（LOW） | `blocker_count` 未登记为系统字段（与「系统字段现算」声明不符） | **ALIGNED（已登记）** | 快照登记 P7 计数为 `writer: system` + `derive`（`level-1.yaml:104-106`）；`agate-md-field-get blocker_count` 返回现算值；测试 passed |
| F-5 | cso（LOW） | 跨文件聚合信任面（不限制哪类声明出自哪类文件；无签名） | **ALIGNED（已声明）** | 显式声明边界（`P4-implementation-G3.md §9.7`，与设计 §6 同口径）；非新门禁绕过 |
| F-6 | cso（LOW） | 非 legacy `SCOPE+` 只认结构化声明 | **ALIGNED（已声明）** | 显式声明边界（§9.7；由批 B T1 绊线作后盾）；非 G3 新增 |

## 4. 残余非阻断项（复审所录，**均非本批引入阻断或威胁模型内绕过**）

| 来源 | 级别 | 内容 | 复审倾向 |
|---|---|---|---|
| cso 复审 §四.1 | LOW（新观察） | **F-2′** `agate_common.task_dir_for_file` 返回首个含 `.state.yaml`/账本的祖先——在 `P4-implementation/` 内**故意放置** `.state.yaml` 可 shadow 任务根 → frontmatter 免检 | **净改进**（整改前所有子目录声明文件均免检）、需故意伪造异常产物（设计 §1 明示「不防故意伪造」，威胁模型外）；建议 `task_dir_for_file` 只认 tasks 根直接子目录或含合法 `task_id`+账本 |
| cso 复审 §四.2 | LOW（新观察） | **F-2″** `match_declaration_file` 对不含 `/` 的通配加 basename 兜底，命中面比枚举面宽 | 方向为 **fail-closed（更严）**，不产生逃逸（命中面 ⊇ 枚举面）；仅口径差，如需严格同判据可去掉 basename 兜底 |
| cso 复审 §三 | LOW | F-5/F-6 声明边界仍成立 | 已显式声明（§9.7），与实现一致，不阻断 |
| review 复审 §新引入问题核查 | 非阻断观察 | **D7 形态判据较严**：证据目录内含顶层 `results`/`bdd_results` 键但值非列表的合法 JSON 会硬失败 | 「面不窄于被取代者」的**有意加宽**（旧脚本静默跳过正是被修的弱点），已记入 `UPGRADING`；留作观察 |
| review 复审 §附 | 非阻断观察 | consistency WARNING 数 412（实现者记 410），差 2 条来自本次**未跟踪**的评审/派发文件 | 非 ERROR，非缺陷 |
| review 复审 §新引入问题核查 | 非阻断 | 目标 5 文件副本跑测 **107 passed**（3 条 `cross_batch` 失败系副本未含仓库根 `docs/`/`CHANGELOG.md` 的环境假象） | 环境假象，非缺陷 |
| 两复审一致 | 非阻断 | `check-protocol-consistency.py` **exit 0 / 0 ERROR**；`count-tests.sh` **2866**（与 P3 登记 +16 一致）；快照 `level-1.yaml` LF 归一 sha256 登记一致 | 一致通过 |

## 5. 门槛判定

- **`status: approved`** —— 汇总规则满足：全票无未解决 BLOCKER；两角色复审均 approved；首轮 BLOCKER-1 与 MINOR-2/3/4、cso F-1/F-2/F-3/F-4 全闭合（F-5/F-6 已声明）。
- **分歧**：无（两角色对各自整改项判定一致闭合；cso 首轮即 approved，无与 review 相左的阻断判定）。
- **残余项处理建议**（转交主 Agent，组长不裁决）：cso 复审 2 项新 LOW 观察（F-2′/F-2″）可选随批收紧或登记 DEBT 留痕后放行；review 复审 D7 形态观察已记入 `UPGRADING`，无需动作。

## 6. 被汇总文件清单（只读，未编辑）

- 首轮：`P4-review-G3.md`（review，rejected）、`P4-review-cso-G3.md`（cso，approved）
- 复审：`P4-review-rereview-G3.md`（review，approved）、`P4-review-cso-rereview-G3.md`（cso，approved）
- 整改指引：`P4-dispatch-context-implementer-G3-fix2.md`
- 历史：`P4-review.md`（原 G2 汇总，已被本汇总文件覆盖）

## 7. 环境隔离

`[PROD_NOT_TOUCHED]` —— 组长仅读取上述输入文件并写出本汇总文件，未接触生产环境，未执行任何写仓/破坏性命令。
