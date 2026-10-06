---
phase: P1
task_id: TAG0050
type: review
parent: P1-requirements.md
trace_id: TAG0050-P1-20261006
created: '2026-10-06'
agent: requirements-review
status: approved
---
# TAG0050 P1 需求基线评审（requirements-review，独立视角）

- **评审对象**：`agate-workspace/tasks/TAG0050-task-data-contract/P1-requirements.md`（77 条 BDD，10 批 A0–A4/B/C/D/E/F）。
- **基线**：本 checkout HEAD `7fd9f75`（分支 `feat/TAG0050-task-data-contract`）；稳定版协议 `~/.agate/v0.78.3/agate`。
- **方法**：只读核对 + 在真实仓库上跑只读命令（未做任何写仓/破坏性操作，未跑有写副作用的判据脚本）。
  - 复算 §3.1 同类扫描各项计数（30 个判据面脚本、8 个标记、test defs 等）；
  - 复跑 §3.3 声称的三文件 pytest（36 passed）与本 checkout consistency（0 ERROR / 410 WARNING）；
  - 逐条 BDD 核对可二值判定性、编号连续性、跨条一致性；
  - 对照设计 §10/§11/§2.4/§2.9、review-r4、review-tag0042-implementation、P0-brief、roadmap 核对承接关系。
- **结论**：**approved**（实质锚点见下；无 BLOCKER，4 条 MINOR 非阻塞）。

---

## 一、重点核验项（dispatch-context 列出的 9 项）

| # | 核验项 | 判定 | 证据 |
|---|---|---|---|
| 1 | BDD 可二值判定 | **通过** | 77 条 Then 均可 PASS/FAIL；正文 BDD 段（127–537 行）主观词扫描（应该/尽量/可能/大约/合理/足够/良好/稳定/流畅/美观/自然/响应灵敏…）**0 命中** |
| 2 | 编号连续 | **通过** | `#### BDD-NN:` 共 77 条；去前导零后 1–77 连续、无跳号、无重复；标题均匹配 `^#### BDD-[0-9]+[a-z]?:`（无 `### BDD-1:` 等非规范标题，除 BDD-71 故意引用该反例） |
| 3 | §3.3 机械门禁实测 | **通过** | 三个探针文件当前不在仓（已清理）；`git status --porcelain` 无探针残留（仅 TAG0050 派发/进度/产出未跟踪 + P0-brief.md 的 platform 修改）；复跑三文件 pytest = **36 passed**；consistency = **0 ERROR / 410 WARNING**；README「新增脚本登记面」实测结论与 §3.3 一致（`agate-*.py` 不在 CHECK9 覆盖面） |
| 4 | P0-brief 时效性质疑 | **通过** | §0 给出 `[P0_STALE: executor_env.platform dsh→opencode]` 并定级"轻微"、记录已更新字段；现 P0-brief.md:49 `platform: "opencode"` 与记载一致；另记 consistency 409→410 的 +1 来源（非 live WARNING） |
| 5 | 批次顺序与依赖 | **通过** | §9「A0→A1→{A2,B}；A3/A4 与 A1 并行；B→C→{D,E,F}；D 另依赖 agate-run 基线 hotfix」与设计 §10、P0-brief §二 前提列**逐项一致** |
| 6 | A0 hotfix 通道判定 | **通过** | §8 按 AGENTS.md「改动通道」三条件（单一主题 / 非 agate 任务 / 可快速验证）逐条论证，并声明 SELF-GATE 留痕 + CHANGELOG；与设计 §2.4「随批 A0 hotfix 先行」一致 |
| 7 | 义务基线重设 | **通过** | §10 显式声明 `baseline.reset: {reason, from: "60/123", to: "<新值>"}` + CHANGELOG 留痕；BDD-44/76 落为可判定锚；与设计 §2.9 一致 |
| 8 | 承接关系完整 | **通过**（附 1 条 MINOR） | RM-AG0099 / 吸收 RM-AG0085·0087·0097 + RM-AG0059① / TAG0042 I-1·2·4·5·6·7·8 / F1–F15 均已覆盖（详见 §五）；F5/F6/F7 无专属 BDD，由结构化机制+T1 承载（见 MINOR-2） |
| 9 | 无未决 NEED_CONFIRM | **通过** | §5 `[NO_NEED_CONFIRM]` + 3 条 SUGGEST；A2 CI required 许可定为 SUGGEST 并延后至 A2 派发取得——判断为**可延后**（见 MINOR-4） |

---

## 二、BDD 评审（逐条编号 + 覆盖维度）

> 维度码：**数**=数据 / **接**=接口·多端 / **边**=边界（空值/极值/并发/编码）/ **兼**=兼容 / **安**=安全 / 前端维度本任务 `domains` 不含 frontend → 全条 **N/A**（§2 与 §6 已声明）。

### 批次 A0
- **BDD-01** PAUSED 留痕真实落盘：通过｜数✓ 安✓
- **BDD-02** check-gate 不存在目录 rc=1：通过｜边✓ 接✓

### 批次 A1
- **BDD-03** 追加降级事件 ERROR：通过｜数✓ 边✓
- **BDD-04** 第 2 条 task_created ERROR：通过｜数✓ 边✓
- **BDD-05** task_created 不在第 1 行 ERROR：通过｜数✓ 边✓
- **BDD-06** 未登记 contract_level ERROR：通过｜数✓ 兼✓
- **BDD-07** 手写低等级 ERROR：通过｜数✓ 兼✓
- **BDD-08** 回填/删除 created 后 judge 仍强制（F3a）：通过｜数✓ 安✓ 兼✓
- **BDD-09** P6 改 judge.enabled:false 后 P6.5 仍阻断（F3b）：通过｜数✓ 安✓
- **BDD-10** 回填 created 不改变 evidence_ref 级别（F3c）：通过｜数✓ 安✓ 兼✓
- **BDD-11** 无创建事件 ERROR / --existing 转绿：通过｜数✓ 边✓ 兼✓
- **BDD-12** git mv legacy 仍 legacy：通过｜兼✓ 边✓
- **BDD-13** 改写/删除账本 ERROR：通过｜数✓ 安✓
- **BDD-14** legacy DONE→P1 ERROR：通过｜兼✓ 边✓
- **BDD-15** 快照冻结/未登记 ERROR：通过｜数✓ 兼✓
- **BDD-16** 黄金 fixture 判定不变：通过｜兼✓ 数✓
- **BDD-17** 等级>协议 max fail-closed：通过｜边✓ 兼✓
- **BDD-18** legacy 只暂存产出仍 PROD_TOUCHED 扫描：通过｜安✓ 兼✓ 边✓
- **BDD-19** 非 legacy 按被暂存产出阶段重跑 gate：通过｜接✓ 边✓ 兼✓
- **BDD-20** P7 迁入 P4 散文缺口旧读取器计数：通过｜兼✓ 接✓ 边✓
- **BDD-21** 连续两次升级各阶段取各自等级：通过｜数✓ 兼✓ 边✓
- **BDD-22** 两仓 R6 差分符合 §8：通过｜兼✓ 接✓ 数✓

### 批次 A2
- **BDD-23** PR 回放 16 提交全 PASS：通过｜接✓ 兼✓
- **BDD-24** push 口径全 PASS：通过｜接✓ 兼✓
- **BDD-25** --no-verify 违规 FAIL 并指出提交：通过｜安✓ 接✓
- **BDD-26** READY 后只改产出 PROD_TOUCHED FAIL：通过｜安✓ 边✓
- **BDD-27** 缺 self-gate trailer FAIL：通过｜安✓ 接✓
- **BDD-28** 删账本 FAIL / legacy 改名 PASS：通过｜数✓ 安✓ 兼✓（单场景双输入，可判定）
- **BDD-29** 手写低等级 --no-verify FAIL：通过｜数✓ 安✓
- **BDD-30** 在途跨升级不误报：通过｜兼✓ 边✓
- **BDD-31** 未写 .agate-version FAIL：通过｜兼✓ 接✓ 边✓
- **BDD-32** 降级 .agate-version FAIL：通过｜兼✓ 安✓
- **BDD-33** 中途升级不误报：通过｜兼✓ 边✓
- **BDD-34** 未改任务 PR SKIP / squash push 只做账本检查：通过｜接✓ 边✓（双输出，可判定）
- **BDD-35** E4 耗时在可接受范围：通过｜边✓ 接✓（"不超过最慢 job"为可测比较锚）

### 批次 A3
- **BDD-36** state-set 以 HEAD 拒绝非法转换：通过｜数✓ 接✓ 边✓
- **BDD-37** 回退写 retries：通过｜数✓ 边✓
- **BDD-38** READY/PAUSED 写 state_transition / agate-next 不写：通过｜数✓ 接✓（含两个可判定子断言）
- **BDD-39** 非 legacy 写 status ERROR、读取现算：通过｜数✓ 兼✓

### 批次 A4
- **BDD-40** check-obligations 对 4 条 M ERROR：通过｜接✓ 数✓
- **BDD-41** M 缺 test 或节点不存在 ERROR：通过｜接✓ 数✓
- **BDD-42** 负向控制删分支 test 转红：通过｜接✓ 边✓
- **BDD-43** 缺 review_output 的 R ERROR：通过｜接✓ 数✓
- **BDD-44** 改标重设基线转绿 / M 占比下降仍 FAIL：通过｜数✓ 兼✓

### 批次 B
- **BDD-45** 7 操作 + config set/unset/explain 往返：通过｜接✓ 数✓
- **BDD-46** 系统字段拒写、get 现算：通过｜数✓ 接✓ 安✓
- **BDD-47** 缺 frontmatter ERROR（F10）：通过｜数✓ 兼✓
- **BDD-48** 渲染块手改 ERROR、CRLF 一致：通过｜数✓ 边✓ 兼✓
- **BDD-49** 修复命令可执行转绿：通过｜接✓ 数✓
- **BDD-50** 只剩 1 个 schema 校验实现：通过｜数✓ 兼✓
- **BDD-51** E3 误报 0 或已落实降级：通过｜数✓ 边✓

### 批次 C
- **BDD-52** 缺 prod_touched ERROR：通过｜安✓ 数✓
- **BDD-53** prod_touched true 非 PAUSED 中止：通过｜安✓
- **BDD-54** 粗体 PROD_TOUCHED、字段 false 仍中止（F4）：通过｜安✓ 边✓
- **BDD-55** `[PROD_TOUCHED]: 无` 被 T1 指向字段（F4）：通过｜安✓ 边✓

### 批次 D
- **BDD-56** F1 A/B/C 三种篡改全转红：通过｜数✓ 接✓
- **BDD-57** 证据被 ignore ERROR（F9）：通过｜数✓ 兼✓ 安✓
- **BDD-58** PASS 日志 EXIT_CODE≠0 ERROR：通过｜数✓
- **BDD-59** run: sha256 与事件不一致 ERROR：通过｜数✓ 安✓
- **BDD-60** extract-context 计数等于现算：通过｜数✓ 接✓

### 批次 E
- **BDD-61** F2 P7 汇总值盖不住 BLOCKER：通过｜数✓ 接✓
- **BDD-62** P2-review 与 P4 分文件声明被聚合：通过｜接✓ 数✓
- **BDD-63** 并行写入不撞号：通过｜边✓ 数✓
- **BDD-64** 集合不相等或悬空 id ERROR：通过｜数✓ 边✓
- **BDD-65** resolved 缺证据 ERROR：通过｜数✓
- **BDD-66** followup:DEBT 不存在/无回指 ERROR：通过｜数✓ 接✓

### 批次 F
- **BDD-67** UI 维度 na 无理由 ERROR：通过｜数✓
- **BDD-68** reviewed_bdds 不相等 ERROR：通过｜数✓ 接✓
- **BDD-69** 骨架标题级判定回归（RM-AG0085）：通过｜兼✓ 数✓
- **BDD-70** 阶段集合不闭合 ERROR（RM-AG0087）：通过｜数✓ 边✓ 兼✓
- **BDD-71** T2 拦下 `### BDD-1:`：通过｜数✓ 兼✓
- **BDD-72** F12 篡改 P8 delivery 转红：通过｜数✓ 接✓

### 跨批通用
- **BDD-73** 每批独立 PR/gate/评审 + 登记快照：通过｜接✓ 数✓
- **BDD-74** legacy 退出码/ERROR 集合不变（差异限 §8 十二项）：通过｜兼✓ 接✓
- **BDD-75** 每批 pytest 绿 + consistency 0 ERROR + count-tests 一致：通过｜接✓ 兼✓
- **BDD-76** 基线重设写 CHANGELOG：通过｜数✓ 兼✓
- **BDD-77** 新增 scripts 不触发既有测试转红：通过｜兼✓ 接✓

**跨条一致性**：同场景未发现 Then 矛盾。重点核对：
- BDD-74「退出码与 ERROR 集合不变」与 §8 第 12 项「legacy 可能出现新 ERROR」不矛盾——BDD-74 已显式把差异限定为 §8 十二项。
- BDD-18（legacy 安全门扫描）↔ BDD-52/53/54（C 批 prod_touched）：前者是扫描触发面扩展、后者是字段判据，层次不同，无冲突。
- BDD-53（true 且非 PAUSED → 中止）↔ BDD-01（PAUSED 下留痕落盘）：互补，优先级（T4 优先于字段，BDD-54）已声明。

---

## 三、隐含需求覆盖

对照角色清单六维（引用 P1 §2 表格行）：

- **数据维度**：覆盖——账本 append-only + `prev_hash` 链（BDD-03/13/28）、快照/黄金 fixture（BDD-15/16）、legacy 零迁移（BDD-74）、need_confirm 空列表即"无"（§2 第 3 行；无专属 BDD，由 §6 结构化字段 + BDD-64 集合判据承载）。✓
- **前端维度**：**N/A**——`domains: [backend, cli, security]` 不含 frontend；§2 明写"无 UI、无 UX 类别 BDD、无人工体验路径验收、无 vision 能力条目"。✓（符合 P1 卡片对非 frontend 任务的要求）
- **多端维度**：覆盖——消费方横跨 3 hook / check-gate / ~30 脚本 / 卡片与角色 / CI（BDD-19/22/60/62/73/74）、CI 非本仓唯一（peekview 无 agate job，BDD-31/34 + UPGRADING 指引）。✓
- **边界维度**：覆盖——并行不撞号（BDD-63）、空值/集合闭合（BDD-64/70）、回滚同步 retries（BDD-37）、等级>max fail-closed（BDD-17）、CRLF 编码（BDD-48）、空任务目录 SKIP（BDD-34）。✓
- **兼容维度**：覆盖——legacy 退出码/ERROR 集合不变 + §8 十二项差异 + R6 差分（BDD-22/74）、旧版本/旧数据/降级策略（BDD-12/30/33/69）。✓
- **安全维度**：覆盖——生产接触安全门（BDD-18/52/53/54/55）、--no-verify 回放（BDD-25/26/27/29）、账本不可改写（BDD-13/28）。✓

---

## 四、裁剪评审

- `phases: [P1, P2, P3, P4, P5, P6, P7, P8]`——**不裁剪任何阶段**。理由充分：`risk_level: high`（协议内核 + 安全门 + CI 可信锚点 + 账本完整性）；`ceremony: full` 要求 P7 不可裁；P3 因每批"先写失败用例并确认红"（TDD）必需。**无跳过阶段需逐项核理由**。
- `risk_level: high`：与暂存区实际改动面（协议脚本 + rules + 卡片 + CI + UPGRADING，设计 §11 列约 30 个脚本 + 卡片）匹配。✓
- `ceremony: full` → `phases` 含 **P7**：✓（逐信号核对，见 §六审声明）。
- `capability_requirements` 三态：3 条均 `available`，无 GAP；按判断树核对——`independent-self-gate-review`（能力，内置角色）、`multi-repo-r6-differential`（能力/环境，peekview 只读副本存在 `/home/kity/oclab/peekview`）、`ci-replay-local-validation`（能力）。**未把环境问题错标为 supplementable**；`verification_env` 在 §11 单独声明 + 轮次预算占位（止损 2 轮）——符合判断树。✓
- `domains: [backend, cli, security]`：与 dispatch 声明及任务实际域一致（非 frontend）。✓
- `packages`：8 个标签均可回溯至设计 §11 消费方（agate-scripts / agate-rules / agate-task-data / agate-cards / agate-roles / agate-tests / ci-workflows / docs-upgrading）。✓

---

## 五、承接关系核对（§12）

- **RM**：RM-AG0099（本任务，roadmap 已登记 `scheduled`）；吸收 RM-AG0085（=DEBT0029，骨架标题级，BDD-69）、RM-AG0087（=DEBT0031，phases↔pruned，BDD-70）、RM-AG0097（证据入库，BDD-57）、RM-AG0059①（`.state.yaml` 元数据，BDD-36/38/39）。②③ 明确不在范围。**逐项在 roadmap.md 定位到对应行，覆盖完整。** ✓
- **TAG0042 实施评审**：I-1（CI 回放，A2/BDD-23..34）、I-2 证据部分（run: 日志，D/BDD-57..59）、I-4（delivery 结构化，F/BDD-72）、I-5（义务机械核验，A4/BDD-40..44）、I-6（state-set，A3/BDD-36..38）、I-7（校验器合并 + config set，B/BDD-45/50）、I-8（F8，A0/BDD-01）。I-3/I-9/release.preset 明确不并入并建议单独登记。**与 review-tag0042-implementation §「对 TAG0050 的影响」表逐行一致。** ✓
- **F1–F15**：F1→BDD-56、F2→BDD-61、F3a/b/c→BDD-08/09/10、F4→BDD-54/55、F8→BDD-01、F9→BDD-57、F10→BDD-47、F11→BDD-67/68/69/70、F12→BDD-72、F13→BDD-40..44、F14→BDD-45/46/50、F15→BDD-23..34。**F5/F6/F7 无专属 BDD**（见 MINOR-2）。
- **P8 回写**：RM-AG0099 → `done`（RM-AG0043 硬校验）已声明。✓

---

## 六、审声明（风险分级/裁剪声明 vs 暂存区实际证据）

- **暂存区实际改动证据**：`git status --porcelain` 显示本任务仅 P0-brief.md 被修改（platform 字段）+ P1 派发/进度/产出未跟踪；协议本体 `agate/` 尚无改动（本 P1 为需求基线，尚未实现）。声明面与"改协议内核 + 安全门 + CI + 账本"的范围相符，`risk_level: high` / `ceremony: full` / 8 packages / 3 domains 均与设计 §10/§11 匹配——**声明与实际一致**。
- **`ceremony: full` → `phases` 含 P7（逐信号核对）**：`phases` 列表含 `P7`，通过。✓
- **声明与 diff 不一致情形**：未发现。

---

## 七、MINOR（非阻塞，建议在对应批的 P1/P2 酌情落实，不影响本次 approved）

1. **同类扫描文件数 1 处 off-by-one**：§3.1「标记文本面」记 **292 行 / 46 文件**；本轮以 13 标记全量口径复算为 **292 行 / 47 文件**（行数精确一致）。差 1 个文件属口径边界（P1 已显式声明"口径差异已如实登记，不臆测"），建议 A1/B 批给出逐行清单时顺带核准文件数。
2. **F5/F6/F7 无专属 BDD**：§12 声称"F1–F15 修复，BDD 覆盖每条验收锚"——就设计 §10 的验收锚而言成立；但 F5（否定写法语义）、F6（4 套行首口径 182 行分歧）、F7（覆盖模式版本号为空）三者**无独立 BDD 编号**，其修复由"结构化字段 + T1 绊线 + 任务版本（契约等级）"整体承载。建议在 §12 补一句显式映射（F5→T1/结构化、F6→T1 单一 default 口径、F7→契约等级），使"F1–F15 全覆盖"可逐条追溯。
3. **复合 BDD 的单一 Given-When-Then**：BDD-28/34/38 在一条 BDD 内含两组输入或两个子断言（如 BDD-38 的"提交写事件"与"agate-next 不写"）。均仍可二值判定，**不构成打回**；如后续批 P1 重编号成本低，可拆为独立编号以贴合角色"多场景拆分"偏好。
4. **A2 的 CI required 许可定为 SUGGEST**：设计 §2.4 明确"设为 required 需用户**明确许可**"。P1 定为 `[SUGGEST]` 并延后至 A2 派发时取得，判为**可延后**——理由：A0/A1 可先行，许可仅影响 A2 的 workflow 落地，且属流程许可而非破坏性变更/业务方向；P1 卡 `[SUGGEST]` 语义允许主 Agent 自行推进。若主 Agent 倾向于 P1 即锁定用户许可，可升为 `[NEED_CONFIRM]`，但**不构成本 P1 的打回项**。

---

## 八、仓库是否保持干净（只读纪律自证）

- 本轮**未执行**任何破坏性或写仓命令（无 `git checkout/restore/reset/stash/clean/add/commit/switch -f`），未编辑/删除被评审文件。
- 未运行有写副作用的判据脚本（`check-judge-verdict.py` 等会追加账本事件；`check-gate.py` 经核对不写 `.gate-result.json`）。
- 运行结束后 `git status --porcelain` 仅含 TAG0050 既有未跟踪/修改项，与评审前一致。

`[PROD_NOT_TOUCHED]` 本评审仅在 agateon 本 checkout 做只读核对，未接触生产环境。
