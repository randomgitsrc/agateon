---
task_id: TAG0050
mechanism_issues:
  - "「给未排期能力预告未来版本号」无 owner 约束（UPGRADING 可写截止版本却不要求登记 RM/DEBT）"
  - "agate-inject-card.py 遇首个缺占位符文件即 exit 1，其后文件全部静默不注入"
  - "check-state-transition.py 的 BDD-3 自由文本关键词扫描可被散文误命中（RM-AG0101 只排除 AGATE_CARD 块）"
  - "SELF-GATE 反复出现同一失败模式：implementer 以「保持既有测试全绿」为由不实现设计要求，无机械对照"
  - "P6 的「pytest 全绿」类 BDD 遇预存失败无机械豁免口径（P5 有 known-failures，P6 无对应）"
  - "维护性 god_file_threshold 遇「设计强制改动」无机械豁免，只能走 known-violations.md 登记"
  - "dispatch-context 卡片占位符无机械校验（漏写占位符无 gate 拦截）"
  - "check-platform-assumptions.py 未覆盖「subprocess text=True 却无 encoding=」类平台假设（扫描 0 命中）"
  - "agate-ci-verify.py::_resolve_protocol 选协议根的输入面未含回放基准 base——push-to-main 时 merge-base = HEAD 自己，用新协议回放历史提交致误报 FAIL"
execution_issues:
  - "主 Agent 两次在 dispatch-context 散文里写入会触发扫描的字面量，自造误报"
  - "G3 整改子任务返回中间状态（全量测试仍在后台跑）而主 Agent 未即时核对"
  - "主 Agent 一度以「会话边界」为由准备停止推进（协议无「会话边界」概念）"
  - "写 TAG0050 批 A4 测试时未按平台无关硬约束为 subprocess.run(text=True) 指定 encoding，Windows CI 抓出"
  - "G1/K1 的账本最终检查未收窄为真实任务账本路径（误判测试夹具），PR CI 的 gate-backstop 抓出"
  - "A2 的 _resolve_protocol 未覆盖 push-to-main 场景（PR run 因 merge-base 恰好=旧 main 未暴露），合并后 main 的 CI 抓出"
feedback_ready: true
---

# TAG0050 复盘 — 任务数据契约：结构化判定、可信写入与任务版本

> 内容价值标准（模板「填写前必读」）：只写 ①机制缺口 ②可复用模式 ③可归因到可行动层面的问题；
> **不复述 P0–P8 过程**，不自我表扬。
> 环境隔离：`[PROD_NOT_TOUCHED]`——本任务全程只在 agateon 本 checkout 与只读/一次性副本上工作，
> 未接触生产环境。

## 一、事实基线

> 客观数据，不含主观判断。

- **规模**：10 批（A0/A1/A2/A3/A4/B/C/D/E/F）+ 1 个批外前置 hotfix（`agate-run` 基线比对，I-2）。
- **提交序列**：`7fd9f75` P0 → `8b9ed06` P1 → `3f9af93` P2（+`8077de6` 同步）→ `75b8add` P3 →
  `1d5aab2` A0 → `b0a16c3a` A1 → `54a814fc` G1 → `f21b314e` G2 → `b746d07d` hotfix-I2 →
  `3b0bd755` G3 → `3d207ff7` P5 → `a87f2bd5` 修正 → `2852711e` P6 → `d59ea950` P6 重验 →
  `36d490cb` P6.5 → `4e7ea04c` P7 → P8（未提交）。
- **`.state.yaml` retries**：P1×1（quality）、P2×1（quality）——均为 phase 级记录。
  P4 各批（G1/G2/G3）均经 1–3 轮整改，属**批次级**（非 phase gate 失败，不进 `retries`）。
- **评审轮次**：P1 requirements-review 1 轮；P2 经 eng+cso reject → 外部专家 → architect retry →
  单次复评通过；G1/G2/G3 各 **SELF-GATE（首轮+复评）+ C8（首轮 reject + fix + 复审 + 组长）**；
  P6.5 judge **2 轮**（轮次上限 2）。
- **关键数字**：P6 验收 77/77 PASS；P6.5 judge 77/77 passed；P7 DESIGN_GAP 15/15 配对；
  全量 pytest 2863 passed / 1 预存失败 / 2 skipped；R6 差分 legacy 39 任务 0 差异 0 未匹配；
  count-tests 2866。
- **本机环境事件**：v0.78.3 → v0.79.0 升级（RM-AG0100「hook 账本 `git add` 不生效」误诊的根因
  ——实为探针比较了两个版本的协议）。
- **已知偏离留痕**：known-violations 1 条（`pre-commit-gate.py` god-file 跨越 998→1144）；
  CODE-MAP DRIFT 3 处（WARNING 级）；版本语义冲突 1 处（v0.79.0 预告 v0.80.0 硬切而本任务不含）。

## 二、做得好的 + 可复用模式

> 填写引导语（强制追问）：本次产生的临时命令/脚本/经验，哪些该沉淀为项目固定资产？沉淀到哪？
> —— 答：**R6 双向差分脚本 `docs/design-notes/r6-differential.sh` + `r6-allowlist.yaml`**（把
> AGENTS.md 工作流 0a 的「差分只在副本上跑」变成可执行判据，且自带跑前/跑后「原仓库干净」自核验）
> 应沉淀为项目固定资产；**E3 抽样脚本 `e3_sample.py`（含种子）** 随批入库供复现。

- **「闭合后既有测试转红 + 夹具更新清单」**（G3 review 产出）：把「按设计接线会红哪些既有用例、
  夹具如何随契约更新」一次性列清（GAP-1 1 条 / GAP-2 1 条 / GAP-4 5 条…），使整改一轮修完，
  消除「改一处发现一处红」的往返。**去向：回馈 agate**（建议进 `review-roles/protocol-alignment-review.md`
  的输出要求）。
- **用 `agate-state-set` 做 phase 推进（dogfooding A3）** + `p5_pass_commit` 写入——新工具在真实编排中
  即用即验（A3 交付的 `agate-state-set.py` 即被本任务后续 phase 推进使用）。**去向：回馈 agate**
  （`state-machine.md` / 卡片的推进示例改用 `agate-state-set`）。
- **R6 差分脚本自带「原仓库干净」自核验（跑前/跑后）**——把 AGENTS.md 工作流 0a 的纪律变成机械判据，
  多次阻止了对真实仓库的污染。**去向：回馈 agate**（已有，作为模式确认）。
- **评审的「独立在仓外副本上复跑」纪律**——G1/G2/G3/P6.5 均在仓外副本复跑（如 judge 的
  `/tmp/opencode/tag0050-judge-r2`），多次阻止了对真实仓库的污染与「改坏即红」证据污染。**去向：回馈 agate**
  （角色卡已含，作为模式确认）。

## 三、发现的问题

> 每条强制标注 `归因层面: 机制缺口 / 执行错误`（二选一）。

### 机制缺口

- 问题：**「给未排期能力预告未来版本号」无 owner 约束**——`agate/UPGRADING.md` 允许写「截止版本：vN」
  却**不要求同时登记 RM/DEBT**；TAG0042 公告 v0.80.0 硬切后无人兑现，TAG0050 撞上该版本号才暴露。
  归因层面: 机制缺口
  说明：公告发出即无 owner，到期无人兑现；机制层缺「预告版本号须绑定登记」的约束。
  （欠账本身已由 RM-AG0102 承接；本条登记的是**机制规则**缺口。）

- 问题：**`agate-inject-card.py` 遇首个缺占位符文件即 `exit 1`，其后文件全部静默不注入**——本次实测
  `P4-dispatch-context-implementer-G1-test-fix.md` 缺占位符 ⇒ 排序其后 13 个 context 均未注入，
  直到人工发现。
  归因层面: 机制缺口
  说明：无「继续处理其余文件 + 末尾汇总失败清单」行为，单点失败扩散为静默批量失败。

- 问题：**BDD-3 自由文本关键词扫描可被散文误命中**（`check-state-transition.py` 的 `("空返回","重派")`）
  ——本次主 Agent 的 dispatch-context 散文写「重派」即触发误报（RM-AG0101 同族；**本次再犯**）。
  归因层面: 机制缺口
  说明：RM-AG0101 只解决「排除 `AGATE_CARD` 块」，未收窄扫描面本身——散文命中仍会误报。

- 问题：**SELF-GATE 反复出现同一失败模式**：G2/G3 的 implementer 以「保持既有测试全绿」为由
  **不实现设计要求**（回退判定 / 只声明时校验 / D5-D7-D9 未实现），两批各需一轮整改；
  `implementer.md` 未显式禁止此理由，且**无「设计要求 ↔ 实现」机械对照**。
  归因层面: 机制缺口
  说明：协议未把「不得以保持测试绿为由回退设计」写进角色卡，也无机械判据，只能靠 SELF-GATE 逐条抓。

- 问题：**P6 的「pytest 全绿」类 BDD 遇预存失败无机械豁免口径**：P5 卡有 known-failures 机制，P6 无对应；
  judge 据此判 needs-revision（76/77），须人工裁定 + 一轮重验。
  归因层面: 机制缺口
  说明：P5 有预存失败机制、P6 无等价物，判定口径不对齐。

- 问题：**维护性阈值 vs 设计强制改动**：`pre-commit-gate.py` 因 §3.1 强制的 T4 改动 998→1144 行
  越 `god_file_threshold` ⇒ 只能走 `known-violations.md` 登记；无「设计强制改动」的机械豁免。
  归因层面: 机制缺口
  说明：设计强制的越阈改动缺少机械豁免/标注语义，每次须人工登记 + 评审确认。

- 问题：**dispatch-context 卡片占位符无机械校验**：本次一个 context 漏写占位符，无 gate 拦截
  （靠 inject 早退暴露，见上第 2 条）。
  归因层面: 机制缺口
  说明：漏写占位符与 inject 早退两缺陷叠加，使漏写长期不可见。

- 问题：**`check-platform-assumptions.py` 未覆盖「`subprocess` 用 `text=True` 却无 `encoding=`」类平台假设**
  ——R1–R5 只扫 PATH/裸 `python3`/单平台 symlink/临时目录/裸外部工具；本缺陷扫描 0 命中。
  归因层面: 机制缺口
  说明：跨平台解码假设无静态判据，只能靠 Windows CI 运行时暴露（本任务实证：本机 Linux UTF-8
  与扫描器双双静默，缺陷延迟到 PR #408 的 `pytest(windows-latest)` 才抓出）。

- 问题：**`agate-ci-verify.py::_resolve_protocol` 选协议根的输入面未含回放基准 `base`**——主流程
  已算出 `base`（PR = merge-base；push = `before`）却未传入；`_resolve_protocol` 自行用
  `merge-base HEAD origin/<默认分支>`。push 到 main 时 HEAD 就是 origin/main ⇒ merge-base =
  **HEAD 自己** ⇒ 用刚合并的新协议回放历史提交（卡片 hash 按旧协议注入 ⇒ hash mismatch）。
  归因层面: 机制缺口
  说明：选协议根的函数**输入面缺一个既有参数**（`base`）——函数无法区分「PR 分支尖」与
  「已合并的 main」，同一段代码在两个事件口径下语义不同，属输入面设计缺口。

### 执行错误

- 问题：写 TAG0050 批 A4 测试时，`subprocess.run(..., text=True)` **未按平台无关硬约束指定 `encoding=`**
  （`test_tag0050_obligations.py` 的 `:54` 与 `:279`）⇒ Windows cp1252 解码子进程非 ASCII 输出失败
  ⇒ `stdout=None` ⇒ TypeError。
  归因层面: 执行错误
  说明：AGENTS.md「测试约定」已列平台无关硬约束，本次是写测试时未落实（**由本任务自身的
  Windows CI 全量/冒烟抓出**，是平台无关机制的**有效实证**；修法为补 `encoding="utf-8", errors="replace"`）。

- 问题：主 Agent 两次在 dispatch-context 散文里写入会触发扫描的字面量（`AGATE_CARD` 起止注释对；
  「重派」关键词）⇒ 自造误报。
  归因层面: 执行错误
  说明：`check-state-transition.py` / 卡片块机制已定义扫描面，本次是编排时未规避已知字面量。

- 问题：G3 整改子任务返回**中间状态**（全量测试仍在后台跑）而主 Agent 未即时核对，后经主 Agent
  自查补齐。
  归因层面: 执行错误
  说明：分阶段落盘/子代理返回核对为既有约定，本次未即时核对中间状态。

- 问题：主 Agent 一度以「会话边界」为由准备停止推进（经用户纠正）——协议无「会话边界」概念，
  `loop-orchestration.md` 的默认就是 P0→P8 一路推进。
  归因层面: 执行错误
  说明：协议默认是连续推进，本次属对协议默认的偏离。

- 问题：**TAG0050 自身交付的 CI 兜底（A2 的 `agate-ci-verify.py`）在 PR CI 上抓出 K1 修复的真缺陷**
  ——`_ci_ledger_checks` 用 `path.endswith("gate-events.jsonl")` 识别账本，把 A1 新增的**黄金夹具**
  `agate/tests/fixtures/task-data/level-1/fail/gate-events.jsonl`（**故意非法**，供 fail 用例断言判 FAIL）
  误判为真实任务账本并判 FAIL，致 `gate-backstop` job 假红（PR #408）。本地未暴露：pre-commit 只扫
  **暂存的任务目录**，从不扫 `agate/tests/fixtures/**`；只有 CI 兜底（`base..HEAD` 全量枚举变化账本）才会撞上。
  归因层面: 执行错误
  说明：K1 实现时未区分「任务账本」与「任意以 `gate-events.jsonl` 结尾的路径」；已修（新增
  `_is_task_ledger_path`，与 `_TASKS_PREFIX` 同口径 + 回归用例）。**该缺陷由 TAG0050 自己交付的 CI 兜底
  抓出，是 A2 机制有效的实证**（本地 hook 抓不到、CI 兜底抓到）。

- 问题：**A2 的 `_resolve_protocol` 未覆盖 push-to-main 场景**——PR run 时 merge-base 恰好=旧 main，
  协议选择「碰巧正确」，掩盖了输入面缺口；合并后 main 的 push run 才暴露（`gh run 37851356052`：
  gate-backstop 7 提交 FAIL + `test_bdd_23/24` FAIL）。
  归因层面: 执行错误
  说明：A2 实现只按 PR 口径验证协议选择，未构造「分支尖 == origin/main」的用例（A2 的 13 个 BDD
  无 push-to-main 协议根用例）；已修并补直接回归用例（负向控制：旧逻辑转红）。

## 四、改进措施

> 措施落到具体文件/字段/gate。

- `agate/UPGRADING.md` / 发布流程约定（+ `AGENTS.md` 版本发布清单）：**不得预告未排期能力的实施版本号**；
  若确需预告，**必须同时登记 RM/DEBT（owner）**（与 RM-AG0102 处置一致）。
- `agate/scripts/agate-inject-card.py`：遇缺占位符时**继续处理其余文件**，末尾汇总失败清单并**非零退出**
  （消除静默早退）。
- `agate/scripts/check-state-transition.py`：BDD-3 关键词扫描**收窄为结构化信号**（或至少排除代码块/行内代码），
  使散文不触发。
- `agate/assets/execution-roles/implementer.md`：明确「**不得以『保持既有测试全绿』为由不实现设计要求**；
  契约驱动的夹具演进优先」。
- `agate/assets/review-roles/protocol-alignment-review.md`：输出要求加「**闭合后既有测试转红 + 夹具更新清单**」。
- `agate/phase-cards/P6-acceptance.md`（+ `check-judge-verdict.py`）：为「pytest 全绿」类 BDD 补
  **预存失败豁免口径**（与 P5 卡 known-failures 一致，须 judge 可机械复核）。
- `agate/scripts/check-maintainability.py`：评估「设计强制改动越阈」的机械豁免/标注语义，或明确
  known-violations 登记即该场景既定出口。
- `agate/scripts/agate-inject-card.py` 或 gate：dispatch-context **卡片占位符存在性**的机械校验。
- `agate/scripts/check-platform-assumptions.py`：新增「`subprocess` 用 `text=True`（或 `universal_newlines=True`）
  却未显式指定 `encoding=`」的规则并接入 CI 阻断（跨平台解码假设静态化）。
- `agate/scripts/agate-ci-verify.py::_resolve_protocol`：**选协议根的输入面必须含回放基准 `base`**；
  协议仓库中取 `merge-base(base, HEAD)` 处的 `agate/`，push-to-main 时即 `before`；解析失败回退
  当前 HEAD 协议并**在 note 写明回退原因**（不得静默）。测试夹具须对**当前**协议良构（非 legacy、
  账本首行 `task_created`），不依赖 checkout 协议版本。

## 技术债登记核对清单

| 机制 | 应该触发？ | 实际触发？ | 未触发后果 | 原因 |
|------|-----------|-----------|-----------|------|
| retry 记录 | 是 | ✅ | — | P1×1 / P2×1（quality）已记 `.state.yaml`；P4 批次级整改为批次内、非 phase retry |
| PAUSED | 否 | — | — | 未超 retry 上限、无跨 ≥2 阶段回退 |
| PROD_TOUCHED | 否 | — | — | 全程本 checkout + 只读/一次性副本，`[PROD_NOT_TOUCHED]` |
| SCOPE+ | 否 | — | — | P1 无行首 `[SCOPE+]`（空闭环） |
| SCOPE_RESOLVED | 否 | — | — | 无 SCOPE+ ⇒ 无需 resolved |
| DESIGN_GAP | 是 | ✅ | — | P4 四处 15 条，已全量转抄 |
| DESIGN_GAP_REVIEWED | 是 | ✅ | — | 15/15 配对（P7 gate 转抄核对通过） |
| NEED_CONFIRM | 否 | — | — | P1/P6 无残留未决项 |
| CAPABILITY_GAP | 否 | — | — | 能力满足（本 checkout pytest + consistency + 副本差分） |
| gate 验证（每阶段） | 是 | ✅ | — | 各阶段主 Agent 亲跑 gate |
| 阶段产出文件（每阶段） | 是 | ✅ | — | 各阶段 `P{n}-*.md` 齐备 |
| .state.yaml phase 同步 | 是 | ✅ | — | 推进随各 commit 同步 |
| 裁剪条件 + override | 否 | — | — | 未裁剪（全阶段执行） |
| capability_requirements | 是 | ✅ | — | P0 `executor_env` 声明（opencode/has_task_tool/network） |
| 分阶段落盘（防 subagent 空返回） | 是 | ✅ | — | `P*-progress.md` 逐条落盘 |
| phase-产出一致性 | 是 | ✅ | — | pre-commit 面判定与 phase 一致 |
| P6 evidence（含截图 + 引用 + vision YAML） | 否 | — | — | 非 UI（`ui_affected: false`） |
| P2 候选方案 + 权衡（≥2） | 是 | ✅ | — | P2 含候选方案与权衡 |
| P8 internal_only_reason | 否 | — | — | 未裁剪 P8 |
| dispatch-context.md | 是 | ✅ | — | 各批派发前落盘 |
| pre-commit hook（gate / 状态转移 / 裁剪） | 是 | ✅ | — | 各 commit 经 hook |
| CI backstop | 是 | ✅ | — | 逐提交回放（A2 交付） |
| **技术债登记** | 是 | ✅ | 本次机制缺口逐条登记：**DEBT0051 / DEBT0052 / DEBT0053 / DEBT0054 / DEBT0055 / DEBT0056 / DEBT0057 / DEBT0058 / DEBT0059**（9 条，`source: retrospective`） | 复盘发现机制缺口，逐条登记 |

## agate 反馈

> 归因到 agate 机制/执行层面、值得反馈给 agate 项目组的条目（不涉项目敏感信息）。

1. **发布流程**：`UPGRADING` 不得预告未排期能力的实施版本号；确需预告须同时登记 RM/DEBT（owner），
   否则公告变成必然过期的承诺（本任务实证：v0.79.0 预告 v0.80.0 硬切、无 owner、到期未兑现）。
2. **`agate-inject-card.py`**：缺占位符时不得 `exit 1` 早退——应继续处理其余文件、末尾汇总失败清单并
   非零退出（本任务实测：单点缺占位符导致其后 13 个上下文静默不注入）。
3. **`check-state-transition.py` BDD-3**：自由文本关键词扫描应收窄为结构化信号（或排除代码块/行内代码），
   避免散文命中误报（RM-AG0101 只排除了卡片块，散文命中仍误报）。
4. **`implementer.md`**：明确「不得以『保持既有测试全绿』为由不实现设计要求」；并在评审角色输出要求中
   加「闭合后既有测试转红 + 夹具更新清单」（SELF-GATE 反复出现该失败模式的根治）。
5. **P6 卡**：为「pytest 全绿」类 BDD 补与 P5 known-failures 一致的预存失败豁免口径，且 judge 可机械复核。
6. **维护性判据**：为「设计强制改动越阈」提供机械豁免/标注语义，或明确 known-violations 为既定出口。
7. **dispatch-context 卡片占位符**：加机械存在性校验（与 `agate-inject-card.py` 早退缺陷一并修）。
8. **`check-platform-assumptions.py`**：新增「`subprocess` 用 `text=True` 却无 `encoding=`」规则——
   跨平台解码假设应有静态判据（本任务实证：本机 Linux UTF-8 + 扫描器双双静默，仅 Windows CI 抓出）。
9. **`agate-ci-verify.py`**：选协议根的函数必须把**回放基准 `base`** 作为输入（不能用
   `merge-base HEAD origin/<默认分支>`）——push 到受保护分支时 HEAD 就是 origin/main，
   merge-base = HEAD 自己 ⇒ 会用合并后的新协议回放历史提交致误报 FAIL（本任务实证：PR run
   碰巧正确、合并后 main CI 必红）。回退分支须在 note 写明原因（不得静默）。
