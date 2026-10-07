---
phase: P2
task_id: TAG0050
parent: P2-design.md
trace_id: TAG0050-P2-20261006
agent: plan-eng-review
status: approved
---
# P2 单一复评（plan-eng-review）— TAG0050（修订后复评）

> **评审对象**：`agate-workspace/tasks/TAG0050-task-data-contract/P2-design.md`（retry 1 修订版；`candidate_count: 3`、`ui_affected: false`、10 批 static-batch）
> **评审角色**：plan-eng-review（C8：`backend`→plan-eng-review + `high`→plan-eng-review 去重；本次按外部专家建议作**单一复评**，无组长汇总）
> **复评范围**：外部专家建议「只重派单一评审，确认 **B1 / BLOCKER-1 / `P5_repro`** 三项闭合即可，不必重开全量评审」（`docs/reviews/tag0050-p2-expert-answers.md`「修订后对 P2 的整体判断」）
> **评审方式**：**只读核验**（无写仓 / 破坏性命令；未编辑被评审文件；验证均为读操作，见 §6）
> **协议版本**：本机稳定版 agate **v0.79.0**（`agate-resolve.py` → `/home/kity/.agate/v0.79.0/agate`）；本 checkout HEAD `42f6df7`
> **上游依据**：`docs/reviews/tag0050-p2-expert-answers.md`、`P2-review-eng.md` / `P2-review-cso.md` / `P2-review.md`（原 3 BLOCKER）、`docs/design-notes/design-tag0050-task-data-contract.md`（r4 APPROVE WITH CHANGES）、`P1-requirements.md`（77 BDD）

---

## 0. 结论

**status: approved。**

三项闭合**全部确认**（逐项判据见 §2）：

| 项 | 来源 | 复评结论 | 关键锚点 |
|---|---|---|---|
| **B1** | eng（源自 G5） | **闭合** | `P5_r6_differential` 改为 `--corpus .`（`P2-design.md:309`）；`r6-differential.sh` + `r6-allowlist.yaml` 登记为 **A1 交付物**（`:80`、`:193`、`:359`、`:406`）；§8 十二项 → 机器可读规则（§3.3 `:245-258`）；负向用例（`:239`、`:126`、`:293`） |
| **BLOCKER-1** | cso（F4） | **闭合** | §3.1 新 F4 规格**自洽**（`:213-227`）；单一来源 `markers.yaml default` + `agate_markers.pattern()`；扫描面 = 全部暂存 `*.md` 新增行（只排除 `AGATE_CARD` 块）；T4 唯一安全门、T1 去 `PROD_TOUCHED`；否定写法阻断 + 指引；补非声明文件锚；威胁模型 |
| **`P5_repro`** | 专家新发现 | **闭合** | `gate_commands` **无** `P5_repro` key（§6 `:299-325`）；`repro-tag0050.sh` 转**证据文档**（`:333`、`:358`） |

**无 BLOCKER。** 另有 **3 项非阻塞残留**（§4）——均已由 P2-design 显式取代/标注，但建议在 P3/P4 前同步相邻文件（design note / P1），以免实现与验收输入分叉。

---

## 1. 独立只读核验摘要

| # | 核验项 | 方法（只读） | 结果 |
|---|---|---|---|
| E1 | `r6-differential.sh` / `r6-allowlist.yaml` 是否存在于仓内 | `ls docs/design-notes/r6-*.{sh,yaml}` | ❌ **不存在**——但已登记为 **A1 交付物**（设计使然；见 §2.1） |
| E2 | `gate_commands` 其余脚本文件是否真实存在 | `test -e` 逐项 | ✅ 9/9 存在（consistency / structure / platform / count-tests / 3 hook / read-p5-commands）；`ruff` 0.16.4 在 `~/.venvs/agate-dev/bin/` |
| E3 | `gate_commands` 是否有 `P5_repro` key / `&&` 链路 | 读 §6 块 | ✅ 无 `P5_repro`；一 key 一命令，无 `&&`，`--strict` 不在链路中间 |
| E4 | F4 字面正则现状 | 读 `pre-commit-gate.py:348,355` | ✅ 确认 `^\s*-?\s*\[PROD_TOUCHED\]`（两条），待批 C 改为 `agate_markers.pattern()` |
| E5 | `markers.yaml` 的 `PROD_TOUCHED` 口径 | 读 `markers.yaml:118-131` | ✅ 确认 `lead_variant: dash_only`（`:129`），与 T1 `default` 分叉——§3.1 单源修复方向正确 |
| E6 | `agate_markers.pattern()` 是否可用、`default` 是否认粗体/引用块 | 读 `agate_markers.py:157-173` + `markers.yaml:28-40` | ✅ `pattern()` 存在；`lead` = `^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?`（认粗体/引用块/列表符）；`lead_variant: default` → `m["lead"]` |
| E7 | 设计 §8 十二项 ↔ §3.3 `D01–D12` | 逐行比对 `design §8:600-613` 与 `P2 §3.3:245-258` | ✅ **一一对应**（12↔12，无缺漏） |
| E8 | 三位原评审的 BLOCKER 是否逐一回应 | 读 `P2-review-eng.md`/`-cso.md`/`P2-review.md` + `P2-design.md:410-419` | ✅ B1/BLOCKER-1/BLOCKER-2(→MEDIUM-3) 均有闭合对照表 |
| E9 | retry1 的编辑范围约束 | 读 `P2-dispatch-context-architect-retry1.md:59` | ✅ 「**只改 `P2-design.md`**（及它自报的交付物登记）」——解释相邻文件未同步 |
| E10 | design note §3.6 / §4 是否已按新规格改写 | 读 `design §3.6:471`、`§4:495` | ⚠️ **未改**：`T4 = 现有的 PROD_TOUCHED diff 扫描，保持原样` / `- **T4 优先**` 仍在——P2 §3.1 显式**取代**（见 §4-R1） |
| E11 | P1 BDD-54 / BDD-55 是否与新规格同步 | 读 `P1-requirements.md:410-418` | BDD-54 ✅ 一致（T4 优先于字段）；**BDD-55 ⚠️ 仍为旧口径**「T1 将其指向字段（不误当声明中止）」（见 §4-R2） |
| E12 | `v0.78.3` 残留 | `grep v0.78.3 P2-design.md` | ✅ 仅出现在「原风险」历史叙事中（`:48,59,125,375,391,404`），无「现行版本 = v0.78.3」的活声明 |
| E13 | G3 派生事项是否归 A3、BDD-01/38 口径收窄 | 读 `P2 §3 note:206-211`、`§1.1 A3:82`、`§10 G3:404` | ✅ 齐备 |
| E14 | 77 BDD 逐批无遗漏 | 逐批加总 `§3:190-202` | ✅ 2+20+13+4+5+7+4+5+6+6+5 = 77，连续无空洞 |

> 全部命令为只读（`ls`/`test -e`/`grep`/`sed`/`read`），**无** `git add/commit/checkout/restore/reset/stash/clean/switch -f`；未对真实仓库跑任何写副作用命令。

---

## 2. 三项闭合逐项判据（复评核心）

### 2.1 B1（eng BLOCKER，源自 G5）— `P5_r6_differential` 指向不存在的脚本 → **闭合**

**原缺陷**：`P5_r6_differential` 指向 `docs/design-notes/r6-differential.sh`，该脚本**不存在且未被任何批次登记为交付物** → 命令必红、且 P2 固化后无修复窗口。

**复评判据（dispatch 三小问逐项）**：

1. **命令引用的脚本是否在 A1 交付物清单中（不再"不存在"）** → ✅ **是**：
   - `§1.1` A1 行（`:80`）明列「**新增 R6 差分交付物** `docs/design-notes/r6-differential.sh`（接口 `--before <rev> --after <dir> --corpus <repo>... [--allow <file>]`）+ `docs/design-notes/r6-allowlist.yaml`」；
   - `§3` A1 行（`:193`）一句话要点含「**R6 差分脚本 + allowlist 交付**」；
   - `§7 files_to_read`（`:359`）单列该两文件为「**A1 交付物**（B1 闭合，§3.2）」；
   - `§10 G5`（`:406`）记为「已裁决：路线①改形」；
   - `§5`（`:289`、`:293`）把「`r6-differential.sh` 对 agateon 语料判定通过」「脚本自身可证伪」列入实现完成标志。
   - E1 实测两文件当前**确实不存在**——但这是**设计使然**（A1 是 TAG0050 的首个交付批，先于 P5；eng 原评审的「首选」裁决即如此要求，`:63`）。
2. **§8 十二项是否改写为机器可读匹配规则** → ✅ **是**：`§3.3`（`:241-258`）给出 `D01–D12` 表，字段 = `id`/`batch`/`kind`/`gate`/`task_scope`/`match` + 依据；E7 逐行比对确认与设计 §8 十二项**一一对应**。
3. **是否仍有任何 `gate_commands` key 指向 P2 定稿时不存在的文件** → ✅ **无**：E2 实测 9 个脚本文件全部存在；唯一的 `r6-differential.sh` 已登记为 A1 交付物（本条允许）。
   - 命令形态正确：`P5_r6_differential: "bash docs/design-notes/r6-differential.sh --corpus ."`（`:309`），只跑仓内语料，接口 `--corpus <repo>...` 兼容 `.`（`§3.2:233`）。
4. **负向用例** → ✅ 三处齐备：`§3.2` 第 5 点（`:239`「删掉一条真实需要的规则 → 脚本必须变红」）、`R14`（`:126`）、`§5` 第 8 点（`:293`）。

**结论**：**闭合**。脚本是 A1 的**显式交付物**（不再是"待建/无归属"），命令可跑、有负向用例、peekview 部分转 P6 证据（`:238`）。

### 2.2 BLOCKER-1（cso，F4）— 安全门闭合机制自相矛盾 → **闭合**

**原缺陷**：设计 §3.6 写「T4 = 现有扫描，**保持原样**」，而 §4/BDD-54 要求「粗体 `**[PROD_TOUCHED]**` + 字段 false → 中止」——「保持原样」的 T4（`dash_only`，不认粗体）**无法**交付 BDD-54；真正认粗体的 T1 又只扫声明文件（不含 `P*-progress.md`）；且 `markers.yaml` 登记 `dash_only` 与 T1 `default` 分叉。

**复评判据（dispatch 三小问逐项）**：

1. **`markers.yaml` 的 `PROD_TOUCHED.lead_variant` 改 `default`** → ✅ 规格明确（`§3.1` 第 1 点，`:218`）；E5 确认现状 `dash_only`（`:129`），E6 确认 `default` → `m["lead"]`（认粗体/引用块），修复方向技术可行。
2. **`pre-commit-gate.py:348/355` 删字面正则改 `agate_markers.pattern("PROD_TOUCHED")`** → ✅ 规格明确（`:219`）；E4 确认现状为两条字面正则（`:348,355`）；E6 确认 `pattern()` 存在（`:157`）。
3. **扫描面 = 任务目录内全部暂存 `*.md` 新增行（只排除 `AGATE_CARD` 块）** → ✅ 规格明确（`:221`）；与设计 §2.3 规则 7、现状 `pre-commit-gate.py:340-346`（排除 `AGATE_CARD` 块）一致。
4. **T4 = 唯一安全门、T1 标记表去 `PROD_TOUCHED`** → ✅ `§3.1` 第 3 点（`:222-224`）；`§1.1` C 行（`:85`）同步。
5. **否定写法继续阻断 + 专门指引** → ✅ `§3.1` 第 4 点（`:225`），并说明「靠**指引**而非改正则」（与本任务"根除用正则识别否定"的主旨一致）。
6. **补非声明文件锚（BDD-54）** → ✅ `§3.1` 第 5 点（`:226`）「非声明文件（如 `P4-progress.md`）写粗体/引用块正向 `[PROD_TOUCHED]` + 字段 false → 中止提交」——正对 cso 指出的「progress 文件未被 T1 覆盖」子集。
7. **威胁模型补充** → ✅ `§3.1` 第 6 点（`:227`）「T4 拦的是诚实但沿用旧习惯，拦不住说谎的 agent」。
8. **`§3.6` 的「保持原样」是否已删 / `§4` 的「T4 优先」是否已改写** → ⚠️ **未在 design note 删除**，但 `§3.1` 开头（`:215`）**显式取代**：「本规格**取代**设计 §3.6 中「…保持原样」与 §4 的「T4 优先」表述…批 C 按此实现」。**operative 规格（P2-design）自洽**——见 §4-R1 的残留说明。
9. **BDD-54/55 是否同步** → BDD-54 ✅ 与新规格一致；**BDD-55 ⚠️ 未同步**（见 §4-R2）。

**结论**：**闭合**。核心（F4 安全门新规格**自洽**、单一来源、扫描面扩大、T4 唯一、否定写法阻断+指引、补锚、威胁模型）在 `§3.1` 完整成立；E4/E5/E6 确认代码现状与规格的差异正是要修的，修复路径可行。

### 2.3 `P5_repro`（专家新发现，与 B1 同类）→ **闭合**

- `gate_commands`（§6 `:299-325`）**无** `P5_repro` key（E3）。
- `repro-tag0050.sh` 保留为**证据文档**（`:333`、`:358`）。
- 「改坏即红」改由各批验收锚的 pytest 用例承担（在**非 legacy 的 init 任务**上构造同样篡改，断言判 FAIL，`:333`）。
- `§10.1`（`:417`）列「`P5_repro`（同类）」为已闭合项。

**结论**：**闭合**。

---

## 3. 也须核对项（dispatch 4–7）

### 3.1 G3 处置（dispatch 4）→ ✅ 落实
- `§10 G3`（`:404`）已改写为**误诊裁决**：RM-AG0100 作为缺陷不成立（版本错位：真实 commit 跑 v0.78.3 hook，无 2h.1d 的 `git add`；v0.79.0 才有）；RM-AG0100 以「误诊」关闭（roadmap 已回写）。
- **派生事项归 A3**：`§1.1` A3 行（`:82`）含「2h.1c+2h.1d 一起前移到 2g 之前（使进入 PAUSED/READY/DONE 的转换事件随本次提交入库）」+「2h.1d 的 `git add` 失败可见（检查返回码，失败给 WARNING）」。
- **BDD-01 Then 收窄 + committed-ledger 断言归 A3**：`§3` note（`:206-211`）明确——BDD-01 只断言「写入工作区账本」；committed-ledger 断言由 **BDD-38**（A3）覆盖；A3 验收须用**真实 `git commit` + 指向 checkout 协议的 hook**。
- `cso BLOCKER-2` → 降 **MEDIUM-3，归 A3**（`:416`）。

### 3.2 env_constraints（dispatch 5）→ ✅ 落实
- `§0`（`:59`）协议版本行已更新为 **v0.79.0**（`AGATE_ROOT=/home/kity/.agate/v0.79.0/agate`、`AGATE_VERSION=v0.79.0`，`current→latest→v0.79.0`），对齐动作已完成。
- **R13**（`:125`）标为「**已缓解**」，但**保留**「agateon 写 `.agate-version`」作 **A2 前置条件**（理由改为防未来发版后本机再次漂移）；`§8 agateon_version_alignment`（`:375`）同步。
- E12：`v0.78.3` 仅存于历史叙事（原风险描述），无活声明。

### 3.3 两位专家确认的非阻塞项（dispatch 6）→ ✅ 基本落实
| 项 | 落点 | 结论 |
|---|---|---|
| eng **M2**（G4→A3 单 owner） | `§1.1 A3:82`（`_scan_bdd3_keyword_phases()` 排除 `AGATE_CARD` 块，RM-AG0101，单 owner）；`§10 G4:405`（「不接受双 owner」） | ✅ |
| eng **G1**（A0 逐 phase 统一 rc=1） | `§1.1 A0:79`（`main()` 单点早检，置于 `handlers.get(phase)` 分派之前）；`§10 G1:402` | ✅ |
| eng **N2**（fitness 测试 P3 先红） | `§4.2:276`（三个 fitness 测试 P3 先以失败状态存在；`-k` 零匹配 exit 5）；`§6:331` | ✅ |
| eng **N1/N3–N7** | `§10.1:419` 逐条列；N3（P5 分片）落 `§6:334`；N4（executor_env）落 `§8:372`；N5（引用 R4 回放实测）落 `§9:391` | ✅ |
| cso **MEDIUM-2**（required 硬前提 + 未许可降级 advisory） | `§8 ci_required_permission:373`（「required 是可信锚点强制力的硬前提；未取得许可时 CI 回放降级为 advisory（非锚点）」） | ✅ |
| cso **MEDIUM-4**（D3 fail-closed + 区分两类报错） | `§1.1 D:86`（「D3 在 `cmd_run` 事件缺失时 fail-closed，并区分「事件缺失」与「sha256 不匹配」」） | ✅ |
| cso **LOW-2**（Git 父目录排除限制） | `§1.1 D:86`（「提示 Git 父目录排除限制（父目录被排除时 `!` 无法重新包含其下文件）」） | ✅ |
| cso **LOW-1**（「CI 保证留痕」限定「在 required 生效时」） | `§10.1:419` 声明落实，但**实际措辞未见于任何产出**（P2-design 无该句；design note §1 未改） | ⚠️ 见 §4-R3 |

### 3.4 `gate_commands` 可执行性 + 一 key 一命令（dispatch 7）→ ✅
- E3：一 key 一命令，无 `&&`，`--strict-errors-only` 为单命令（不在链路中间）。
- E2：除 A1 交付物 `r6-differential.sh` 外，所有脚本路径实测存在；`ruff` 0.16.4 就位。
- `P5_fitness_*` 三条依赖 P3 落成真实节点名（N2 已记，`:331`）。

---

## 4. 非阻塞残留（记录 + 建议去向）

以下 3 项**均非 BLOCKER**（原始级别分别为 MEDIUM/LOW/文档同步），已由 P2-design 显式取代或标注，故不阻断；但为避免 P3/P4 的输入分叉，建议在推进前同步。

| # | 残留 | 证据 | 影响 | 建议去向 |
|---|---|---|---|---|
| **R1** | design note §3.6 `:471` 仍写「T4 = 现有的 PROD_TOUCHED diff 扫描，**保持原样**」、§4 `:495` 仍写「**T4 优先**」，与 `§3.1` 新规格矛盾 | E10；`design §3.6:471`、`§4:495` vs `P2 §3.1:215-224` | `files_to_read`（`:342`）把 design note 列为「**实现时逐节对照**」→ 批 C 的 P4 implementer 可能照旧文实现旧 T4，致 BDD-54 落空 | 在 design note §3.6/§4 就地标注「**已过时 + 被 P2 §3.1 取代**」（保留决策史，不删除），或在 `§3.1` 头部加指向 design note 的醒目取代注记；属 P2 定稿前后的小同步 |
| **R2** | P1 `BDD-55`（`:415-418`）Then 仍为旧口径「**T1 将其指向字段（不误当声明中止）**」，与新规格（T1 已去 `PROD_TOUCHED`、否定写法由 T4 **继续阻断**）**方向相反** | E11；`P1:415-418` vs `P2 §3.1:225` | P3 test-designer 读 P1 会设计"否定不阻断"的测试 → 与实现冲突 | `§3.1` 已写「BDD-55 按此改写」；建议把 `§3` note（`:206-211`）的「P1 下次触及时同步」**显式扩到 BDD-55**（现仅列 BDD-01/38），或直接改写 P1 BDD-55 |
| **R3** | cso **LOW-1**（「CI 能保证留痕」→「**在 required 生效时**」）在 `§10.1:419` 声明落实，但该措辞**未出现在任何产出**（P2-design 无此句；design note §1 未改） | E9 编辑范围 = 只改 P2-design.md；`grep 在 required 生效时` 无命中 | 认知边界措辞略强（未设 required 时连 SELF-GATE trailer 痕迹都不校验） | 在 design note §1 或 `§8 ci_required_permission`（`:373`）补一句「在 gate-backstop required 生效时」 |

> **口径说明**：R1–R3 都不改变设计路线，也不使任何 `gate_commands` 必红；它们是「operative 文档已自洽、相邻文件待同步」的一致性问题。按原评审分级，R2 为 **MEDIUM**（cso MEDIUM-1）、R3 为 **LOW**、R1 为文档同步——**均不阻塞 approved**。

---

## 5. 锁定决策（本次复评后确定）

1. **B1 / BLOCKER-1 / `P5_repro` 三项闭合成立**，P2 可推进 P3；`gate_commands` 固化生效。
2. **`P5_r6_differential` 的脚本交付归属锁定为 A1**——A1 必须先于 TAG0050 的 P5 产出该脚本；peekview 部分**不进 gate**，转 P6 证据由 D3 绑定。
3. **F4 单一来源锁定**：`markers.yaml` `PROD_TOUCHED.lead_variant = default` + `agate_markers.pattern("PROD_TOUCHED")`；T4 为**唯一** PROD_TOUCHED 安全门，T1 标记表去 `PROD_TOUCHED`；扫描面 = 任务目录内全部暂存 `*.md` 新增行（只排除 `AGATE_CARD` 块）。
4. **`P5_repro` 不得回填**；F1–F15 的「改坏即红」由各批非 legacy pytest 用例承担。
5. **R1–R3 为 approved 的非阻塞附随项**：建议随本次 P2 提交或 P3 前同步相邻文件（design note §3.6/§4 取代注记、P1 BDD-55、LOW-1 措辞）。

---

## 6. 只读纪律声明

本复评全程**未执行任何破坏性/写仓命令**（无 `git add/commit/checkout/restore/reset/stash/clean/switch -f`），**未编辑/删除被评审文件**（`P2-design.md` 及三份原评审均未改）。全部核验为读操作：`ls`/`test -e`/`grep`/`sed`/`read`，以及 `agate-resolve.py`（只读）。本复评仅新增/更新两份**自身产出**：`P2-review.md`（本文件，覆盖原 rejected 版）与 `P2-progress.md` 的 progress 追加；核验后真实仓库 `git status --porcelain` 仅含 TAG0050 未跟踪的派发/进度/评审文件，**无写副作用残留**。

[PROD_NOT_TOUCHED] 本复评仅在 agateon 本 checkout 上做只读核验，未接触生产环境。
