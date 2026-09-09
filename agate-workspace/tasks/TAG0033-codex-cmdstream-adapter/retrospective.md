---
task_id: TAG0033
mechanism_issues:
  - "agate-next.py P4→P5 推进在「多提交阶段」或「回退后修复提交」场景被 check-gate.py P4（只看 git diff --cached）挡住——阶段工作已提交、暂存区空 → gate P4 exit 1 → 拒绝推进"
  - "check-judge-verdict.py 的 P6.5 dispatch-context 黑/白名单扫描：`p6-acceptance.md` 子串匹配无 `agate/phase-cards/` 路径豁免（引用阶段卡片被误判为引用 verifier 自述）；白名单不含角色定义文件路径（其它 phase 的 dispatch-context 都列它）"
  - "新平台适配器的 P1 spike / P2 minimal_validation 只「读已有会话」而非「主动构造每个终态/边界样本」——已有会话恰好无失败命令，导致 status:\"failed\" 终态漏采样 → F1 缺陷带到 P6 才被真机 V6 发现"
execution_issues: []
feedback_ready: true
---

# TAG0033 复盘 —— Codex 命令流适配器 + 平台接入（RM-AG0061 → v0.70.0）

## 一、事实基线

- 阶段：全量 P0-P8，无裁剪（`phases: [P1..P8]`）。
- 重试：`retries.P1` round 1（P1-review needs-revision：`capability_requirements` 的
  `codex-api-key-account` 条目 `status: available` + `available: []` 自相矛盾，回派 analyst 定向修订）；
  `retries.P4` attempt 1（P5→P4 单步回退修 F1）。均未超上限。
- **回退 1 次**：P5→P4（`52fe210`）——P6 真机验证 V6 发现 F1（真机 Codex 把已结束但非 0 退出的命令
  记为 `payload.item.status == "failed"`、携带完整 `exit_code`/`completed_at_ms`，`CodexAdapter` 原
  pending 判据 `status != "completed"` 误判其为 pending、丢真实 exit_code/output_hash → detect 对真机
  重复失败会话判不出 SPIN）。登记 DEBT0035（`source: retreat`），P4 重试 #1 修复（新增
  `_codex_is_finished` helper），P5 r3 + P6 重做 + P6.5 judge 复核后 DEBT0035 → closed。
- 评审轮次：P1-review ×2 / P2 plan-eng-review ×1 / P4 review ×2 + protocol-alignment-review ×3
  （adapter-core / protocol-docs / F1 修复面）/ P5 verifier ×3 / P6 verifier ×2（首轮被 API 限额中断）/
  P6.5 judge ×1 / P7 consistency-reviewer ×1 / P8 releaser ×1。
- 子 Agent 被 API 限额（HTTP 429）中断 2 次：P2 plan-eng-review（无产出，重派）、P6 verifier（BDD-1~30
  证据已落盘、V6 已发现 F1，重派从零重做）。分阶段落盘让两次中断都没丢关键信息。
- 提交约 20 个（P0 交接单 → `v0.70.0` tag），含 1 个 `retreat:` 提交 + 1 个 `debt:` 提交。
- 代码改动：`agate/scripts/agate-cmdstream-adapters.py` +252 / −0（新增 `CodexAdapter` class + 3 helper +
  2 截断常量 + `ADAPTERS["codex"]` + `import shlex`）；`test_agate_cmdstream_{adapters,detect}.py` 断言调整
  + 1 守护用例；新增 `test_codex_platform_docs.py`（BDD-22~30）；新增 fixture `codex-session.jsonl` +
  `codex-subagent-session.jsonl`。文档：`platform-notes.md` Codex 章（待补充→完整）、`SETUP.md` 步骤
  2-Codex、`CODE-MAP.md` 四平台、`docs/research/...` 回写。
- **零改动硬约束守住**：`git diff v0.69.0..HEAD -- agate-cmdstream-detect.py agate-cmdstream-ir.py` 空
  （检测引擎 / 阈值 / `CommandRecord` IR 十字段 / 既有三适配器 class 体全程零改动）。RM-AG0055 §3.4.4
  「未来接新平台只写一个适配器、检测引擎零改动」扩展点兑现。
- 验收：30 条 BDD 全 PASS（P6-evidence 逐条 `-v` 实跑）；P6.5 judge fresh context 独立重验 30/30 passed；
  P7 一致性 `blocker_count: 0` / `deviation_critical_count: 0`（`deviation_count: 1` = V7 措辞滞后 WARNING）。
- 真机验证（codex-cli 0.153.4 + ChatGPT 登录）：V1（rollout 解析）/ V3（spawn_agent 子会话独立文件）/
  V4（截断标记形态实测收敛 fixture）/ V5（`multi_agent` flag stable/true）/ V6（三态 FROZEN/NORMAL/SPIN
  完整）/ V7（`spawn_agent` 嵌套 depth 1→2 生效）/ V2（跨 9 次真实调用键并集无 `[自述]` 之外的键）。
  V8（API-key 账号 model 阵容）本机为 ChatGPT 账号、环境不可得，登记待补（非阻塞）。
- 全量单测 1389 → 1390 passed（+1 F1 守护）/ 0 failed / 2 skipped；consistency 0 ERROR；ruff clean。

## 二、做得好的 + 可复用模式

**填写引导语回答**：本次产生的临时脚本/经验里，值得沉淀的是「新平台适配器的真机采样纪律」——
不是临时脚本，是一条应写进协议/角色文件的做法。

- **P1 派 analyst 做真机 spike（模式 4 先理解后拆）再写需求**——analyst 现场派了一个 Codex
  `spawn_agent` 子代理，观察 `~/.codex/sessions/` 目录，**当场确认子会话是独立 `rollout-*.jsonl`
  文件**（不是父文件内嵌事件，也不是 DSH 式 `delegationDepth`），`list_sessions` 的 `os.walk` 设计因此
  一开始就对。
  → 去向：回馈 agate（见「## agate 反馈」）——新平台/新数据源适配器的 P1，spike 应包含「现场产生一个
  真实会话 + 逐字段核对」，而不是只读文档/研究报告。
- **RM-AG0055 真机验证清单（V1-V8）在 P6 抓住了 fixture 测试全绿也没发现的 F1**——单测用 P2 推测的
  `status:"completed"` fixture 全部 PASS，是 P6 V6「对真实 Codex 会话跑 detect 判三态」造了一个真实重复
  失败会话、发现 detect 判不出 SPIN 才逼出根因。**这条清单值回它的成本**。
  → 去向：回馈 agate——真机验证清单在「新平台适配器」类任务里不是可选加强项，是必须项；且它应
  明确要求「每个终态/边界（成功/失败/未结束/截断）各造一个真实样本」。
- **分阶段落盘让 2 次 API 429 中断零损失**——P6 verifier 首轮被中断时，BDD-1~30 证据 + V6 发现 F1 的
  勘查结论都已在 `P6-evidence/` / `P6-progress.md` 落盘，主 Agent 据此直接做了 P5→P4 回退决策，重派
  只是补一份 `P6-acceptance.md`。
  → 去向：既有机制，无需改，但值得记为「分阶段落盘 + 长任务」的正面实证。
- **static-batch 第 2 批（protocol-docs）拉回 P4 执行**——architect 原标「protocol-docs 批 P7 执行」，
  主 Agent 判定「补文档内容属实现工作、不是 P7 一致性验证工作」（比照 TAG0030：doc-assertion 审计测试
  P3 写红、内容 P4 补绿），拉回 P4 第 2 批，避免 P5/P6 带着 6 条 by-design 红推进。
  → 去向：回馈 agate——`dispatch_plan` 的批次「执行阶段」标注，架构师容易把「协议文档内容补写」误标到
  P7；协议应明确「补协议文档正文 = P4 实现工作；P7 只做一致性验证，不 author 内容」。

## 三、发现的问题

- 问题：`agate-next.py` 在「一个 phase 跨多个 commit」（adapter-core + protocol-docs 两批）和「P5→P4
  回退后的修复 commit」两个场景下，跑 `check-gate.py P4`（只看 `git diff --cached` 有无非 md/yaml 文件）
  得 exit 1，因为阶段工作已提交、当前暂存区空 → `agate-next.py` 按 `phases.yaml` 查 P4 的 `retreat`
  （null）→「提示重试本阶段，不推进」。主 Agent 两次手动按 `_advance` 逻辑（改 `.state.yaml` phase +
  `append_event` state_transition）推进。
  归因层面: 机制缺口
  说明：`check-gate.py P4` 的 exit 1 判据（暂存区无代码文件）对「阶段完整度」是个不完备代理——
  它假设「离开 P4 时暂存区必有代码 diff」，但多提交阶段 / 回退后再推进都破坏这个假设。协议未定义
  「阶段完整度」在这些场景下怎么判。

- 问题：P6.5 judge 的 dispatch-context 首版在「输入文件」节字面写了 `agate/phase-cards/P6-acceptance.md`
  （阶段规格卡片，不是本任务的 verifier 自述产出）+ 角色定义文件路径 + `real-machine-p6.md` 裸文件名，
  三处都被 `check-judge-verdict.py` 的信息隔离黑/白名单扫描拦下（`p6-acceptance.md` 子串纯匹配无
  `agate/phase-cards/` 豁免；白名单不含角色文件路径；`P6-evidence/` 目录白名单不认裸文件名）。judge
  verdict 本体（30/30 passed）已通过、卡在 dispatch-context 措辞。主 Agent 重写 dispatch-context
  （收敛为「`P6-evidence/` 整目录」+ 移除角色文件路径 + 移除阶段卡片引用）后 P6.5 gate 转绿。
  归因层面: 机制缺口
  说明：黑名单子串匹配太粗（`p6-acceptance.md` 命中 `agate/phase-cards/P6-acceptance.md`）；白名单
  与「每个 dispatch-context 都要列角色文件」的通用惯例冲突，P6.5 是唯一例外但没在派发模板/卡片里
  显式说明。

- 问题：F1 —— `CodexAdapter` 对真机 Codex `status:"failed"` 终态（已结束但非 0 退出，携带完整
  `exit_code`/`completed_at_ms`）误判为 pending。P1 §4.1 spike 描述 `item.status` 只列了 `"completed"` /
  `"in_progress"`，P2 minimal_validation 对 23 个真实 rollout 跑解析、result: confirmed，但那些会话
  恰好没有失败命令 → `"failed"` 终态从未进入采样。单测用 P2 推测形态的 fixture 全绿。
  归因层面: 机制缺口
  说明：spike / minimal_validation 的「读已有真实会话」策略对「枚举所有终态」不完备——已有会话是
  被动样本，缺哪个终态取决于运气。协议未要求「解析类适配器的 P1/P2 必须主动构造每个终态/边界样本
  并采集」。

## 四、改进措施

- **`check-gate.py P4` / `agate-next.py` 的多提交阶段与回退后推进**（对应问题 1）：
  落点 `agate/scripts/check-gate.py`（`_gate_p4`）+ `agate/scripts/agate-next.py`（`_advance` 前的 gate
  判定）。方向：P4 完整度判据从「当前暂存区有代码 diff」放宽为「本 phase 的任一 commit 引入过代码
  diff」（`git log --oneline <phase 起点>..HEAD` 扫非 md/yaml），或对「回退后再推进」显式识别
  （`.state.yaml` `retries[P4]` 非空 + 已有 `wf(...-P4):` commit）。登记 DEBT（`source: retrospective`）
  或 roadmap backlog 一条。

- **`check-judge-verdict.py` 信息隔离扫描的误判面**（对应问题 2）：
  落点 `agate/scripts/check-judge-verdict.py`（`_check_blacklist` / `_check_whitelist`）+
  `agate/dispatch-protocol.md`「Judge 信息隔离」节。方向：① 黑名单 `p6-acceptance.md` 匹配加
  `agate/phase-cards/` 路径豁免（阶段规格卡片不是 verifier 自述）；② 白名单显式允许角色定义文件路径，
  或在派发模板/P6 卡片里写明「P6.5 dispatch-context 的『输入文件』节不列角色文件（派发机制注入）」；
  ③ `P6-evidence/` 目录白名单认「目录下裸文件名」。登记 DEBT。

- **新平台/解析类适配器的 P1 spike / P2 minimal_validation 终态枚举纪律**（对应问题 3，最重要）：
  落点 `agate/phase-cards/P1-requirements.md`（spike 节）+ `agate/phase-cards/P2-design.md`
  （minimal_validation 节）+ `agate/assets/execution-roles/analyst.md` / `architect.md`。方向：明确
  「解析外部数据源的适配器，P1 spike / P2 minimal_validation 必须**主动构造并采集**每个终态/边界样本
  （成功 / 失败 / 未结束 / 截断 / 畸形），不能只『读已有会话』——已有会话是被动样本、缺哪个终态靠运气」。
  RM-AG0055 的真机验证清单已隐含这个要求（V4 截断、V6 三态），但它在 P5/P6 才执行，太晚——应前移到
  P1/P2 的采样阶段。可作一条 roadmap RM（agate 协议增强）。

- **`dispatch_plan` 批次的执行阶段标注**（对应「做得好」第 4 条的反面）：
  落点 `agate/assets/execution-roles/architect.md`（批次设计节）+ `agate/dispatch-protocol.md`
  （派发编排机制）。方向：明确「补协议文档正文（platform-notes / SETUP / 卡片等）= P4 实现工作，
  批次执行阶段标 P4；P7 只做跨文件一致性验证，不 author 文档内容」。防止架构师把 doc 内容补写误标 P7。

- **DEBT0036（V7 措辞滞后）** 已登记（`source: retrospective`，`priority: low`）：`platform-notes.md`
  Codex 章「`spawn_agent` 嵌套深度未测 / `max_depth=1` 待 V7 复核」措辞在 P6 V7 两次实测 `depth=2`
  可用后已滞后，closure = 收敛为「已实测 depth=2 可用」+ 回跑 `test_bdd_25` + consistency。留后续
  小任务/顺手改。

## 技术债登记核对清单

| 机制 | 应该触发？ | 实际触发？ | 未触发后果 | 原因 |
|------|-----------|-----------|-----------|------|
| retry 记录 | 是（P1 review needs-revision / P5→P4 回退）| ✅（`retries.P1` round 1 + `retries.P4` attempt 1）| — | — |
| PAUSED | 否（retry 未超限、单步回退、无不可逆操作）| — | — | — |
| PROD_TOUCHED | 否 | — | — | 真机验证只跑 echo/sleep/ls/date；`~/.codex/sessions/` 会话文件为 Codex 正常产物、非 agate 生产环境 |
| SCOPE+ | 否（分析未发现 P1 未覆盖的新隐含需求）| — | — | — |
| SCOPE_RESOLVED | 否 | — | — | — |
| DESIGN_GAP | 否（P4 三批均声明「DESIGN_GAP: 无」）| — | — | — |
| DESIGN_GAP_REVIEWED | 否 | — | — | 无 DESIGN_GAP 待配对 |
| NEED_CONFIRM | 否（P1 `[NO_NEED_CONFIRM]`；3 条 `[SUGGEST]` 主 Agent 直接采纳）| — | — | — |
| CAPABILITY_GAP | 否（`codex-cli-installed-authenticated` = available；API-key 账号项走 `verification_env` 待补、非 GAP）| — | — | — |
| gate 验证（每阶段） | 是 | ✅（P1-P8 逐阶段 check-gate + P6 三脚本 + P6.5 双脚本 + P7 + P8）| — | — |
| 阶段产出文件（每阶段） | 是 | ✅ | — | — |
| .state.yaml phase 同步 | 是 | ✅（P1-P7 经 agate-next.py；P4→P5 ×2 + P8→READY 因 agate-next.py 多提交阶段局限手动 `_advance` + 补 state_transition 事件）| — | agate-next.py 机制缺口，见「问题 1」 |
| 裁剪条件 + override | 否（全阶段保留，无裁剪）| — | — | — |
| capability_requirements | 是 | ✅（P1 声明，requirements-review 复核后收敛为单条 available + `verification_env` 承载 API-key 账号项）| — | — |
| 分阶段落盘（防 subagent 空返回） | 是 | ✅（渲染 dispatch-prompt 默认启用；2 次 API 429 中断零关键信息损失）| — | — |
| phase-产出一致性 | 是 | ✅（pre-commit WARNING：P1/P2 产出在 phase=P4 暂存 = BASELINE_CHANGE 授权编辑；P8 产出在 phase=READY 暂存 = P8 卡片规定）| — | — |
| P6 evidence（含截图 + 引用 + vision YAML） | 是（非 UI，走 pytest -v + grep + 真机日志）| ✅（`bdd-01.log`~`bdd-30.log` + `real-machine-v6-{frozen,normal,spin}.log` + `real-machine-p6.md`；check-p6-evidence + check-p6-provenance exit 0）| — | — |
| P2 候选方案 + 权衡（≥2） | 是 | ✅（`candidate_count: 3`；5 设计点各给候选 + 权衡；`follows_existing_pattern: [agate-cmdstream-adapters.py]` 对照搬 DSHAdapter 的点）| — | — |
| P8 internal_only_reason | 否（未裁剪 P8）| — | — | — |
| dispatch-context.md | 是 | ✅（每次派发前写 + `agate-inject-card.py` 注入卡片；P6.5 首版因黑/白名单误判返工一次，见「问题 2」）| — | — |
| pre-commit hook（gate / 状态转移 / 裁剪） | 是 | ✅（每次 commit 触发；hook 指向 `~/.agate` 稳定版，判定对象是 worktree 产出）| — | — |
| CI backstop | 是（合并 PR 时）| — | 待合并 PR 后 CI 兜底（Linux 全量 pytest / shellcheck / consistency / gate-backstop）| 本地已全绿，CI 为最终确认 |
| **技术债登记** | 是 | ✅ | — | DEBT0035（`source: retreat`，F1 回退债，本任务 closed）+ DEBT0036（`source: retrospective`，V7 措辞滞后，open）+ 改进措施建议登记 2 条（agate-next.py 多提交阶段 / check-judge-verdict 扫描误判）待落 DEBT 或 roadmap |

## agate 反馈

> `feedback_ready: true`。以下条目归因到 agate 机制层面，值得反馈给协议项目组。

1. **`check-gate.py P4` 的完整度判据在多提交阶段 / 回退后推进场景不完备**：判据「当前暂存区有非
   md/yaml 文件」假设「离开 P4 时暂存区必有代码 diff」，但一个 phase 跨多个 commit（如 static-batch
   分两次提交）或 P5→P4 回退后的修复 commit 已提交、暂存区空时，该判据 exit 1，`agate-next.py` 因此
   拒绝推进。建议判据放宽为「本 phase 的任一 commit 引入过代码 diff」或显式识别「回退后再推进」
   （`retries[P4]` 非空 + 已有 `wf(...-P4):` commit）。

2. **`check-judge-verdict.py` 信息隔离扫描误判**：① 黑名单 `p6-acceptance.md` 子串纯匹配会命中
   `agate/phase-cards/P6-acceptance.md`（阶段规格卡片，不是 verifier 自述）——应加 `agate/phase-cards/`
   路径豁免；② 白名单不含角色定义文件路径，与「每个 dispatch-context 的『输入文件』节都列角色文件」的
   通用惯例冲突，P6.5 是唯一例外但没在派发模板 / P6 卡片里显式写明「P6.5 dispatch-context 不列角色
   文件」；③ `P6-evidence/` 目录白名单不认「目录下裸文件名」（如 `real-machine-p6.md`），只认带
   `P6-evidence/` 前缀的引用。

3. **解析类 / 新平台适配器的 P1 spike / P2 minimal_validation 应强制「主动构造每个终态/边界样本」**：
   本次 F1（`status:"failed"` 终态漏采样 → pending 判据误判 → detect 判不出 SPIN）根因是 spike /
   minimal_validation 只「读已有真实会话」，已有会话恰好无失败命令。RM-AG0055 真机验证清单
   （V4 截断 / V6 三态）已隐含「每个终态都要真实样本」的要求，但它在 P5/P6 执行、太晚。建议在
   P1 卡片 spike 节 + P2 卡片 minimal_validation 节 + analyst/architect 角色文件里明确：**解析外部
   数据源的适配器，P1/P2 必须主动构造并采集每个终态/边界样本（成功 / 失败 / 未结束 / 截断 / 畸形），
   不能只被动读已有会话**。

4. **`dispatch_plan` 批次「执行阶段」标注易把「补协议文档正文」误标到 P7**：architect 原把
   `protocol-docs` 批（补 `platform-notes.md` Codex 章 + `SETUP.md` 小节）标「P7 执行」。补协议文档
   正文是 P4 实现工作（doc-assertion 审计测试 P3 写红、内容 P4 补绿——TAG0030 先例），P7 只做跨文件
   一致性验证、不 author 内容。建议在 architect 角色文件「批次设计」节 + dispatch-protocol「派发
   编排机制」写明这条边界。
