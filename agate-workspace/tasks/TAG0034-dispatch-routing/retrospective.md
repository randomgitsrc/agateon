---
task_id: TAG0034
mechanism_issues:
  - "P6.5 judge 全量 pytest 跑测把 judge_verdict 事件写进 committed fixture 账本（TAG0030/32/33），测试隔离缺口"
  - "P3-test-cases.md 缺 agent frontmatter 字段导致 P6→P7 provenance exit 2，agate-md-field-set 不支持为 P3 写 agent 字段"
  - "DEBT0037：static-batch 多 commit stage 下 agate-next.py 拒绝 P4→P5 自动推进，需手工 _advance"
execution_issues:
  - "P2-design §4.1 dispatch_plan 用嵌套花括号 flow-mapping YAML，触发 check-protocol-consistency.py 占位符 sanitizer 误判，自造一致性回归"
feedback_ready: true
---

# TAG0034 复盘 —— 派发路由（配置驱动跨 CLI/model 派发 + tmux 观测，RM-AG0060 epic）

## 一、事实基线

- **交付形态**：v0.71.0（minor）。104 files changed / +14233 / −79（含全部 P1–P8 阶段产出）。
  实现面：`agate/` 36 文件 · `agate-workspace/` 62 · `docs/` 2 · 根 README×2 + CHANGELOG。
- **BDD**：P1 基线 53 条（连续 BDD-1~53）。P6 逐条验收 53/53 PASS / 0 FAIL。
  P6.5 judge fresh-context 复核 53/53 passed（partial=false）。
- **测试**：`pytest -k tag0034` P4c 收口 90 passed / 0 failed。P5 全量 gate 重跑
  1625 passed / 0 failed / 2 skipped（exit 0）。新增 12 个 unit 文件 + 1 regression + 3 fixture 目录。
- **wf() 提交**：11 个（P1 / P2 / P3 / P4a / P4b / P4c / P6 / P6.5 / P7 / P8 + 本 READY 收尾）。
  P4 按 `dispatch_plan: {mode: static-batch, batches: [P4a, P4b, P4c], serial}` 串行三子批。
- **事件账本**：`gate_run`×9 · `state_transition`×17 · `judge_verdict`×4。`check-events.py` hash 链完整、exit 0。
  新增第 8 条审计链（`dispatch_route` 理由码 ∈ {launch_fail, infra_error, no_parseable_output}）。
- **SELF-GATE alignment-review**：6 轮（P4a×3 = 首审 MISALIGNED→2 轮修复 ALIGNED；P4b×1 A1 修复；
  P4c×1；P8×1 收口）。首审 3 项 MISALIGNED（A3/A4/A6 锚点缺失 + A1 reason-code 分类偏差），全部修复。
  A5 / A7 → NEEDS_HUMAN_REVIEW → HUMAN_CONFIRMED（LIMITATIONS 局限 2 缓解链段 + ADR-013）。
- **范围事件**：DEBT0039 并入（用户批准，closure → BDD-48/49/50）；BDD-10 `[BASELINE_CHANGE]`
  （Claude Code 2.1.266 实测有 `--effort`，按 `claude --help` 能力探测映射，不硬编码版本号）；
  A5.3 + A7.4 两条 `[SCOPE+]`（P2-design 范围外，P8 落地，HUMAN_CONFIRMED）。
- **DESIGN_GAP**：4 条（G1 `_route_main` P4a 形态 / G2 `AGATE_DISPATCH_EXPECT` / G3 mid-chain native
  HAS_OUTPUT 占位 / G4 tmux feature flag 默认关），4/4 均 `[DESIGN_GAP_REVIEWED]` 配对。
- **异常恢复**：月度额度 429 触发 3 次（P3 test-designer / P4b implementer / P6.5 judge），
  按用户指示 auto 恢复，均 SendMessage 续跑保上下文，三次死前都已完成实质工作。
- **手工干预**：DEBT0037 P4→P5 手工 `_advance`（编辑 `.state.yaml` + `append_event` state_transition）×1。

## 二、做得好的 + 可复用模式

**填写引导语回答**：本次产生的临时命令主要是 gate 分步验证串（consistency / check-events /
check-dispatch-routing 三连 + audit7），这些已是 `~/.agate/scripts/` 常驻能力，无新增项目脚本需沉淀。
`check-dispatch-routing.py` 本身作为新 gate 已进 `SCRIPT_ALIGNMENT_ANCHORS`，属协议资产而非临时命令。

- **`maintainability.yaml` 先例复用**：项目级 `dispatch-routing.yaml`（全兜底 / 非协议本体 /
  不受 SELF-GATE 管辖 / `_load_config` 仿 `check-maintainability.py:_load_config`）——精确对齐既有先例
  使 P2 candidate 收敛到 2 个、评审一轮过。→ 去向：回馈 agate（「新增项目级配置文件」应固化为
  architect 的标准参照清单：maintainability.yaml → dispatch-routing.yaml 两例同构）。
- **完整性不变量前置写死**：R1 model-shopping 完整性洞在 P2 §3.7 / §3.8 就落成机械约束
  （`GATE_FAIL_TRIGGERS_FALLBACK = False` 常量 + `dispatch_route` 理由枚举无 `gate_fail` 值 +
  `check-events.py` 第 8 链机械拒绝）——三处冗余锁定，P4 实现无解释空间。→ 去向：回馈 agate
  （「高风险设计决策落成常量 + 事件枚举 + gate 链三重锁」值得写进 architect.md 作为模式）。
- **P4 static-batch 串行子批**：high→medium→low 复杂度递减排布，每批独立 commit + 独立 alignment
  delta 审查，把一个 SELF-GATE 大改切成 3 个可评审单元。→ 去向：项目资产已固化
  （architect.md「批次设计」节，DEBT0039① 已写入边界措辞）。

## 三、发现的问题

- **问题**：P6.5 judge 在 fresh context 里跑全量 `pytest` 复核，测试用例真实调用
  `agate_common.append_event`，把 `judge_verdict` 事件写进了 **已提交的** fixture 账本
  `agate-workspace/tasks/TAG003{0,2,3}/gate-events.jsonl`（非 TAG0034 目录，是历史任务的账本夹具）。
  发现后 `git checkout` 三个文件复原。
  归因层面: 机制缺口
  说明：涉及 `append_event` 的测试没有把 `AGATE_WORKSPACE` / task_dir 重定向到 tmp_path，
  真实账本被当可写夹具。协议/测试规范里没有「碰 append-only 账本的测试必须 tmp 隔离」的强制条款，
  `check-events.py` 也不校验「跑测后账本零新增」。TAG0030 RM-AG0057 建过测试副作用 gate，
  但覆盖的是 E2E 创建型清理，没覆盖 append-only 账本这类。

- **问题**：P6→P7 被 `check-p6-provenance.py` exit 2 挡住——`P3-test-cases.md` 缺 `agent`
  frontmatter 字段。releaser 用 `agate-md-field-set` 只能写 `test_code_dir`，该工具不支持给 P3
  写 `agent` 字段，最终手工补了整段标准 frontmatter header。
  归因层面: 机制缺口
  说明：`agate-md-field-set` 的字段白名单没覆盖 P3-test-cases.md 的 `agent`，而 provenance 检查
  又强依赖该字段。工具与检查器对「P3 产出必备字段」的认知不一致。

- **问题**：`agate-next.py` 在 static-batch 多 commit stage 下拒绝 P4→P5 自动推进
  （check-gate.py P4 在暂存区为空时 exit 1），必须手工编辑 `.state.yaml` + `append_event`。
  归因层面: 机制缺口
  说明：已登记 DEBT0037。static-batch 的「多 commit、每 commit 后暂存区清空」与 gate P4
  「暂存区非空才算有产出」的前提冲突，推进侧没给 static-batch 开豁免路径。

- **问题**：P2-design.md §4.1 `dispatch_plan` 示例用了嵌套花括号 flow-mapping YAML
  （`{mode: static-batch, batches: [{id: P4a, ...}], serial: true}`），触发
  `check-protocol-consistency.py._sanitize_placeholders` 的 `\{[^}]*\}` 正则误吞，
  产出 `mapping values are not allowed here` ERROR，连带 3 个既有 consistency 回归测试变红。
  改成等价 block-style YAML 后解决。
  归因层面: 执行错误
  说明：`_sanitize_placeholders` 对含冒号的 flow-mapping 敏感是**已知**行为（历史多次踩），
  写设计文档时应默认用 block YAML。不是协议缺陷，是没遵守既有约定。

## 四、改进措施

- **测试碰 append-only 账本必须 tmp 隔离**：在 `agate/assets/execution-roles/test-designer.md`
  和 `implementer.md` 补一条硬规则——「任何直接或间接调用 `agate_common.append_event` /
  写 `gate-events.jsonl` 的测试，必须把 task_dir 指向 `tmp_path`，禁止指向仓库内真实/夹具账本」；
  并在 `check-events.py` 增一个可选自检模式或在 CI 加一步「pytest 跑完后 `git diff --exit-code
  agate-workspace/tasks/*/gate-events.jsonl`」兜底。落点：test-designer.md / implementer.md /
  ci-gate-backstop 或新 CHECK。→ 建议登记 DEBT。
- **`agate-md-field-set` 字段白名单对齐 provenance 必备字段**：把 P3-test-cases.md 的 `agent`
  加入 `agate-md-field-set` 支持字段；或让 `check-p6-provenance.py` 对 P3-test-cases.md 的
  `agent` 缺失降级为 WARNING（P3 是 test-designer 唯一产出，agent 恒定）。落点：
  `agate-md-field-set.py` 字段表 / `check-p6-provenance.py:573` 附近。→ 建议登记 DEBT。
- **DEBT0037 给 static-batch 开推进豁免**：`agate-next.py` 识别 `.state.yaml` 有
  `dispatch_plan.mode == static-batch` 且当前 stage 已全部 commit 时，允许 P4→P5 推进而不要求
  暂存区非空。落点：`agate-next.py` P4 推进分支 + `check-gate.py` P4。已在 DEBT0037，本次复盘加权。
- **设计文档 YAML 一律 block-style**：在 `agate/assets/execution-roles/architect.md` 明确
  「P2-design.md 内所有 YAML 示例用 block-style，禁止含冒号的 flow-mapping」，附
  `_sanitize_placeholders` 的踩坑说明链接。落点：architect.md「设计文档写作约定」。

## agate 反馈

- **append-only 账本测试隔离缺口**：协议有 append-only 事件账本机制（RM-AG0032 / TAG0020），
  也有测试副作用 gate（RM-AG0057 / TAG0030），但两者交集没覆盖——「测试真实调用 append_event
  写进仓库内账本夹具」既不被 test-designer 规范禁止，也不被任何 gate 检出。建议：append-only
  账本的写入测试强制 tmp_path 隔离 + CI 加 `git diff --exit-code` 账本兜底步。
- **结构化字段写入工具与 provenance 检查器认知不一致**：`agate-md-field-set` 支持的字段集
  与 `check-p6-provenance.py` 要求的必备字段集不是同一份权威来源，P3-test-cases.md 的 `agent`
  字段就落在缝里。建议：两者共读同一份「阶段产出必备 frontmatter 字段」表（rules/ 下）。
- **static-batch 推进侧豁免缺失（DEBT0037）**：`dispatch_plan.mode == static-batch` 的多 commit
  阶段，推进侧 gate 与「暂存区非空」前提冲突，主 Agent 每次都要手工 `_advance`。高频、可机械化。

## 技术债登记核对清单

| 机制 | 应该触发？ | 实际触发？ | 未触发后果 | 原因 |
|------|-----------|-----------|-----------|------|
| retry 记录 | 是（429×3） | ✅ | — | rate-limit 恢复经 SendMessage 续跑，事件账本 state_transition 留痕 |
| PAUSED | 否 | — | — | 无 retry 超限 / 无跨 ≥2 阶段回退 |
| PROD_TOUCHED | 否 | — | — | 三平台真机冒烟只读不驻留，`~/.agate` 与 worktree 未污染，标 `[PROD_NOT_TOUCHED]` |
| SCOPE+ | 是（A5.3 / A7.4） | ✅ | — | P2-design 范围外两条 doc-sync，P1 §1 backtick-wrapped `[SCOPE+]` 登记，P8 落地 |
| SCOPE_RESOLVED | 是 | ✅ | — | P1 frontmatter `scope_resolved:` 增 DEBT0039 + A5.3/A7.4，`check-scope-resolved.py` exit 0 |
| DESIGN_GAP | 是（4 条） | ✅ | — | G1–G4，P4/P4b/P4c 各 `[DESIGN_GAP:]` 声明 |
| DESIGN_GAP_REVIEWED | 是（4 条） | ✅ | — | 4/4 配对 `[DESIGN_GAP_REVIEWED: 已确认]`，P7 `design_gap_reviewed_count: 4` |
| NEED_CONFIRM | 否 | — | — | P6 逐条 53/53 PASS，无 BDD 偏差歧义 |
| CAPABILITY_GAP | 否 | — | — | 三平台 CLI + tmux 环境齐备；BDD-10 是 BASELINE_CHANGE 非能力缺口 |
| gate 验证（每阶段） | 是 | ✅ | — | 每阶段主 Agent 亲跑 check-gate.py + 阶段脚本；P8 后 consistency/events/routing 三连复跑 |
| 阶段产出文件（每阶段） | 是 | ✅ | — | P1–P8 全部 P{n}-*.md 齐备，无裁剪 |
| .state.yaml phase 同步 | 是 | ✅ | — | 含 DEBT0037 手工 `_advance` P4→P5 时同步 phase + append state_transition |
| 裁剪条件 + override | 否 | — | — | `ceremony: standard`，phases P1–P8 全跑，无裁剪 |
| capability_requirements | 是 | ✅ | — | P1 analyst 声明三平台 CLI + tmux + effort 能力探测 |
| 分阶段落盘（防 subagent 空返回） | 是 | ✅ | — | 每个 dispatch-context 派发前落盘 + `agate-inject-card.py`；3 次 429 死前均有实质产出 |
| phase-产出一致性 | 是 | ✅ | — | pre-commit WARNING 未报；P8 badge-bump 前 CHECK 7 ERROR 为 DEBT0013 设计内时序 |
| P6 evidence（含截图 + 引用 + vision YAML） | 是（`ui_affected: false`，无截图） | ✅ | — | P6-evidence/ 含 pytest 日志 + 逐条 BDD 对照；judge verdict_evidence 指 P6.5-judge-evidence/ |
| P2 候选方案 + 权衡（≥2） | 是 | ✅ | — | `candidate_count: 2`，选 Candidate A（MVP 双文件）+ 权衡表 |
| P8 internal_only_reason | 否 | — | — | 未裁剪 P8，正常发布 v0.71.0 |
| dispatch-context.md | 是 | ✅ | — | 每角色 P{n}-dispatch-context-{role}.md 派发前落盘，无行首 `- PASS`/`- FAIL` |
| pre-commit hook（gate / 状态转移 / 裁剪） | 是 | ✅ | — | 每 wf() commit 触发；commit-msg `self-gate-review:` trailer 齐 |
| CI backstop | 是 | ✅ | — | push 后待确认（本复盘属 READY 收尾，PR 阶段核 CI green） |
| 技术债登记 | 是 | ✅ | 本次复盘新识别 3 条机制缺口（账本测试隔离 / 字段表不一致 / DEBT0037 加权）建议登记 DEBT，去向见「四、改进措施」；DEBT0039 已 closed（task_id: TAG0034） | 机制缺口 3 条待登记 + DEBT0039 已闭 + DEBT0013/0037 为已知设计内 |
