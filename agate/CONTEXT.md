# agate 术语表 + 上下文

> 统一定义 agate 协议中的关键术语。定义的权威来源是各协议文件，本表是补充入口。
> 新读者（或审查 subagent）可从此处快速理解术语，再按"首次定义位置"回溯详情。

## 术语表

| 术语 | 定义 | 首次定义位置 |
|------|------|------------|
| gate | 阶段门槛检查，由脚本 exit code 判定。**通过码因 phase 而异**——见 `phases.yaml` 的 `gate_pass_exit`：多数 phase（P0-P3/P5/P6/P8）以 exit 2 为正常通过，P4/P7/P6.5 以 exit 0 为通过；exit 1 一律不通过；某 phase 的 `pass_set` 不含且 ≠1 才是真暂停 / 需人工。`agate next` 按 `pass_set` 三态消费 | WORKFLOW.md / phases.yaml / check-gate.py |
| 裁剪 | 跳过某个阶段，须在 P1 裁剪说明里写明理由 | WORKFLOW.md §可裁剪的阶段 |
| 机制交叉 | ≥2 个子系统交互、时序依赖、跨层影响的改动 | WORKFLOW.md §改动性质判断 |
| 声明性改动 | 不改变程序运行时控制流的改动（改前改后控制流相同） | WORKFLOW.md §改动性质判断 |
| 行为逻辑改动 | 改变程序运行时控制流的改动（条件分支、状态转换、数据处理） | WORKFLOW.md §改动性质判断 |
| BDD | Behavior-Driven Development，`#### BDD-NN:` 标题编号 + 一条 Given/When/Then 的验收条件 | WORKFLOW.md §需求基线 |
| NEED_CONFIRM | 需人工确认的标记（行首声明格式），subagent 拿不准方向时标注；无待确认项写 `[NO_NEED_CONFIRM]`。另有 `[SUGGEST: 推荐 X，理由 Y]`——有倾向但求确认，主 Agent 可自行采纳、不阻塞 | WORKFLOW.md §[NEED_CONFIRM] |
| SCOPE+ | 新发现的隐含需求标记，任何阶段 subagent 可标注，主 Agent 增补 P1 基线 | WORKFLOW.md §[SCOPE+] |
| SCOPE_GAP | 主 Agent 派发 prompt 漏了 P2 已声明的改动，subagent 标注 | dispatch-protocol.md |
| C8 域 | role-system.md 定义的协作域，命中时触发 P2/P4 评审 | role-system.md |
| agent 字段 | 阶段产出文件 Header 的角色标识（如 `agent: verifier`），`agent=main` 表示自审 | orchestrator-template.md |
| PAUSED | 任务暂停状态，需人工介入后才能继续。不是失败，是正确路由 | state-machine.md |
| READY | 任务完成所有 gate、准备发布的状态。实际发布由人手动触发 | state-machine.md |
| dispatch-context | 派发前主 Agent 写的核心信息源，含派发指引（目标/约束/上游关联/输入文件）+ 阶段卡片 + 客观查证信息。文件名 P{N}-dispatch-context-{role}.md，每个 subagent 一个。禁止含 PASS/FAIL 预判 | dispatch-protocol.md |
| PROD_TOUCHED | subagent 意外接触生产环境时标注的标记（二值格式：触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`），触发 PAUSED | dispatch-protocol.md |
| DESIGN_GAP | P4 实现中发现的设计偏差声明，须在 P7 被转抄 + 配对 DESIGN_GAP_REVIEWED | state-machine.md |
| 自审 | agent=main 的评审，被 check-gate.py 硬拦截（exit 1） | orchestrator-template.md |
| 裁剪说明 | P1-requirements.md 中声明跳过阶段及理由的节 | WORKFLOW.md §可裁剪的阶段 |
| 风险等级 | P1 声明的 risk_level 字段（low/medium/high），影响裁剪和评审触发 | WORKFLOW.md §裁剪风险维度 |
| ceremony | P1 frontmatter 声明的仪式深度档位（thin / standard / full），缺省 standard（fail-closed：不声明或声明要素不满足一律按 standard 处理，不做薄化）；声明 thin 须四要素 checklist（coupling_checklist 流式 + 跳过风险 + P5/P6 保留），缺一回退 standard；full 档任务 P7 不可裁 | phase-cards/P1-requirements.md §ceremony fail-closed 声明 checklist |
| P6.5 / judge | 挂载于 P6→P7 转移的**强门槛子阶段**（非独立 phase 值，`.state.yaml` phase 保持 P6 直至 P7），所有机制后新任务强制。judge 角色以 fresh context 只凭 `P6-evidence/` 证据与 git log 逐条重验全部 BDD（含已 PASS 项，零挑验），信息隔离白名单由 `check-judge-verdict.py` 机械校验；exit code（`check-judge-verdict.py` + `check-events.py` 双 0）才是门槛，judge 的 LLM 结论不单独放行 | state-machine.md / phases.yaml / role-system.md |
| gate-events.jsonl（事件账本）| 每任务 append-only 事件账本（`gate_run` / `judge_verdict` / `state_transition` / `dispatch_route`），逐行 `prev_hash` 哈希链 + ts 单调。`check-events.py` 审计（链完整性 / judge 轮次去重计数 ≤2 / dispatch_route 理由码枚举）。是 P6.5 gate 前置 | state-machine.md / check-events.py |
| 命令流日志（cmdstream）| subagent 存活/卡死可观测性机制（RM-AG0055）：从平台会话记录外部读取活动信号，统一为 `CommandRecord` IR，检测引擎判「调用冻结 / 活动冻结 / 逻辑空转」三态。**证据 + 触发核查、不自动判死**；每平台一个适配器（`agate-cmdstream-adapters.py`，claude-code/opencode/dsh/codex）| docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/ |
| agate next / agate advance | 状态推进侧 CLI（RM-AG0054）：查 `phases.yaml` 表机械推进一个 phase（跑 gate → 按 `next`/`retreat`/`gate_pass_exit` 算下一状态 → 写 `.state.yaml` + git add），不做临场判断。`agate next` = 前进，回退委托 `agate-retreat-to.py`。手工推进为 fallback | state-machine.md §主 Agent 的单步执行 |
| 派发路由 / tier | 可选机制（RM-AG0060）：`agate-workspace/dispatch-routing.yaml` 按 `(phase, role)` 查表把某角色的 subagent 派到不同 CLI+model（`tier` 能力档 bulk/standard/deep + `effort` 两正交轴，或直接 `candidates`）→ try-and-fall 逐级回落 → 全落空回落默认派发。**不配置 = 逐字节现状**；`dispatch_route` 事件留痕；gate 不认「谁生产的」 | dispatch-protocol.md §派发路由 / rules/dispatch-tiers.yaml |
| pytest | agate 测试框架。开发者在 Linux 全量 `python3 -m pytest agate/tests/`，Windows 只跑冒烟；用例数以 `bash agate/tests/scripts/count-tests.sh` 为准 | AGENTS.md §测试约定 |
| windows_smoke marker | `@pytest.mark.windows_smoke`，Windows CI 冒烟代表（每文件第 1 个用例 + 平台敏感关键词用例），Linux 全量覆盖、Windows 只验证平台敏感机制成立 | AGENTS.md §测试约定 |
| conftest | agate/tests/conftest.py，全局 fixture（agate_root / task_dir / git_repo / run_cli / py_path），根目录自动加载，test_*.py 无需 load 语句 | tests/README.md |
