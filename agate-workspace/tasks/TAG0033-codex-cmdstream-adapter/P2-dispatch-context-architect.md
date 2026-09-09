---
phase: P2
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0033
role: architect
---

<dispatch_guide>
> 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 大于 客观查证信息 大于 阶段卡片（参考规范）。

### 目标

产出 `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md`：把 P1 的 30 条 BDD 落成
可实现的方案设计。核心是 **CodexAdapter 的 5 个设计点**（下方逐条），以及测试策略、文档改动落点、
批次编排。P1 已把大量机制事实通过 spike 实测确定（§4），你的工作是**在既定事实上做方案取舍与结构设计**，
不是重新调查。

### CodexAdapter 5 个设计点（每点给方案 + 定论）

P1 §9 已点明 P2 要设计：`probe` 判据 / `read_commands` 事件→IR 映射规则 / `session_id` 取法 /
截断信号形态 / 子会话判定。逐条要求：

1. **`probe(path)` 判据**——如何可靠区分「Codex rollout JSONL」与「Claude Code 转录 JSONL / 其它 `.jsonl`」。
   P1 BDD-1 给了判据方向（basename `rollout-<ts>-<uuid>.jsonl` + 首行 `type=="session_meta"` + payload 含
   codex 标记如 `cli_version`/`originator`）。设计要定：只看 basename 够不够？要不要读首行？读首行时对
   大文件的性能（只读第一行，别整文件 load）。给出最终判据 + 为什么这样够稳。
2. **`read_commands(session_path)` 事件→`CommandRecord` 映射规则**——P1 §4.1 已定源为
   `type=="event_msg"` 且 `payload.type=="item_completed"` 且 `payload.item.type=="CommandExecution"`。
   逐字段定映射：`platform`（固定 `"codex"`）/ `session_id`（见设计点 3）/ `tool`（取什么——`"exec"`？
   `item.command[0]` 的 basename？）/ `command`（`item.command` 数组如何拼成字符串——`shlex.join`？
   直接空格 join？取末元素？）/ `ts_start`←`payload.started_at_ms` / `ts_end`←`payload.completed_at_ms` /
   `exit`←`item.exit_code`（P1 §4.1.1：直接取数字，未结束/无字段才回落 None）/ `exit_signal`（留档什么
   原始形态——`f"exit_code={item.exit_code}"`？`item.status`？P1 BDD-4 只要求"非空原始形态留档"）/
   `output_hash`←`_sha1_hex(item.aggregated_output)`（`truncated` 时 None，用既有 `adapters.py` 的
   `_sha1_hex` 助手）/ `truncated`（见设计点 4）。**非 shell 工具事件**（`apply_patch`/`web__run` 经
   `custom_tool_call` 但不派生 `CommandExecution`）——BDD-8 要求不产出记录，定过滤逻辑。**畸形行**
   （BDD-9）——定 try/except 跳过粒度（逐行 parse，坏行 continue，不整体崩）。
3. **`session_id` 取法**——BDD-10（同文件所有记录 `session_id` 一致、非空、可定位）+ BDD-12（子会话
   记录的 `session_id` 指向**子会话自身**，而 `session_meta` 里 `id`=子会话自身 id、`session_id` 字段=
   父会话 id——P1 §4.2 实测）。定：取 `session_meta.id`？还是文件 basename（去 `rollout-` 前缀 + `.jsonl`
   后缀）？两者对主会话/子会话分别是什么值？哪个满足"可据其定位回该会话文件"。给结论。
4. **截断信号形态**——P1 §4.1.2 标注为 `[未实测/待定]`（本会话样本无超长输出）。P1 §8 SUGGEST ③ +
   BDD-7 Given 已定 P4 兜底策略 = **比照 `DSHAdapter._detect_truncated` 的保守双信号**（item 上显式布尔
   字段 ∪ 输出文本字面量标记），P5 V4 实测后收敛。设计要：读 `DSHAdapter._detect_truncated` 现有实现，
   定 Codex 侧的双信号具体是什么（候选布尔字段名 / 候选文本标记），定"实测后如何收敛"的接口（改一个
   常量？改一个方法？让 P4 写成易替换的形式）。`truncated=True` ⇒ `output_hash=None` 是 IR 铁律，不放宽。
5. **子会话判定 + `list_sessions` 实现**——P1 §4.2 实测已定：父子会话都是独立 `rollout-*.jsonl`、同
   `YYYY/MM/DD/` 扁平目录、`os.walk` 天然同时枚举、子会话判据 = `session_meta.thread_source=="subagent"`
   （或 `parent_thread_id` 存在）。设计要：`list_sessions(cwd)` 遍历的**根目录**是什么——`~/.codex/sessions/`
   固定？还是接受传入 `cwd` 再拼 `.codex/sessions`？（对比既有 `ClaudeCodeAdapter`/`DSHAdapter` 的
   `list_sessions` 签名语义——它们的 `cwd` 参数怎么用的）。定返回值（绝对路径 list）+ 排序（按 mtime？
   按文件名时间戳？）+ 是否过滤非 `rollout-` 前缀文件。

### 3 条 SUGGEST 已由主 Agent 采纳（写进 P2 作为既定前提）

P1 §8 的 3 条 `[SUGGEST]` 主 Agent 已确认采纳，P2 按既定前提设计、不再作为待决项：

1. **`ADAPTERS` 注册表键名 = `"codex"`**（与 `CommandRecord.platform` 标识、research 文档、CLI 名一致）。
2. **`read_commands` 只以 rollout JSONL（`~/.codex/sessions/**/*.jsonl`）为源**；`codex exec --json` 实时流
   **不实现**（P1 §4.5 实测：实时流事件不带 per-item 时间戳，`detect()` 需 `ts_start`/`ts_end`）。
   P2 可在 out-of-scope 明确写「实时流源后置/不做」。
3. **截断标记 P5 V4 实测前用比照 `DSHAdapter._detect_truncated` 的保守双信号兜底**（见设计点 4）。

### 约束（不可违反）

1. **零改动硬约束**（P0-brief 核心约束 2 / P1 §5 / BDD-21）：`agate-cmdstream-detect.py` 检测引擎、阈值
   （RM-AG0055 §3.4.3）、`agate-cmdstream-ir.py` 的 `CommandRecord` dataclass 十字段、既有三适配器
   （`ClaudeCodeAdapter`/`OpenCodeAdapter`/`DSHAdapter` 的 class 体）——**全部零功能改动**。本任务唯一
   代码改动 = `agate-cmdstream-adapters.py` 加 1 个 `CodexAdapter` class + `ADAPTERS` 字典加 1 行 +
   `test_agate_cmdstream_adapters.py:317` 的精确等值断言（`test_bdd_6_detect_consumes_registry_zero_change`）
   改为包含式（BDD-19）+ 文档两处 + fixture + 新单测。**方案若发现必须动检测引擎/IR/阈值/既有适配器
   → 立即停下报告主 Agent**（P1 §5 逃生阀），可能拆子任务。
2. **`candidate_count` ≥2**：5 个设计点里，凡有真实取舍的（尤其设计点 1 probe 判据、设计点 3 session_id
   取法、设计点 4 截断双信号）给 ≥2 候选 + 权衡 + 选择理由。凡确实是「照搬 `DSHAdapter` 既有模式」的
   （设计点 5 的 `os.walk` 枚举），可声明 `follows_existing_pattern: [agate/scripts/agate-cmdstream-adapters.py]`
   对该点写 1 候选——但 P2-design.md 整体仍须给出 ≥2 candidate_count（对有取舍的点），不能全程 1 候选。
3. **影响面梳理节**（P2 卡片强制节，写在候选方案**之前**）：三部分——改什么（逐文件/逐函数 + 关联 BDD
   编号）/ 不改什么（看起来该改但不改的 + 理由，尤其检测引擎、既有三适配器、IR dataclass）/ 风险在哪
   （每条配缓解）。要有客观证据（grep 命中、读过的消费方代码）。P1 §3 同类扫描 12 行表 + §5 范围锁定
   是你的输入，在其上做候选方案级细化，不重复劳动。
4. **`gate_commands` 固化**（P2 是声明验证契约的唯一窗口）：
   - `P3`: 测试运行器（`python3 -m pytest`——供 `check-tdd-red.py` 读取）
   - `P5`: `python3 -m pytest agate/tests/unit/ -q --tb=no`（或含 regression/integration 分片，按你判断）
   - `P5_consistency`: `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
     （⚠️ 用 worktree 自己的脚本路径，不是 `~/.agate`——检查对象是 worktree 里改的 platform-notes/SETUP）
   - `P5_shellcheck`: 本任务不改 `.sh`，可选声明 `shellcheck -S warning agate/scripts/*.sh` 作结构性回归
   - **不要用 `&&` 串联**（P2 卡片「`--strict` 反模式」）——每个校验独立 key
   - **不声明 `P3_xxx` 检测键**（P2 卡片禁令 BDD-6）
   - `ui_affected: false` → **不需要 `P5_e2e`**
   - 按需给 `{key}_timeout_seconds`（单元测试类 120s 档；consistency 类按经验）
5. **`dispatch_plan` 声明**（P2 对后续编排的机器声明）：本任务子任务面 = ①CodexAdapter class + 注册表
   ②新单测（解析单测 + 检测引擎三态确定性试验）③fixture（`codex-session.jsonl` + spawn_agent 子会话片段）
   ④`platform-notes.md` Codex 章 ⑤`SETUP.md` Codex 小节 ⑥`test_bdd_6` 断言改包含式。判断用 `static-batch`
   还是 `serial`：①②③⑥ 强耦合（TDD：先红后绿，同一批）、④⑤ 文档面可并行或独立批。给出 batches +
   complexity + parallel_limit。
6. **P2 最小验证**（派发 prompt 追加要求）：本任务 `read_commands` 解析逻辑依赖**真实 Codex rollout JSONL
   的字段结构**——不是纯代码逻辑。`minimal_validation` 字段要：对 `~/.codex/sessions/2026/09/*/rollout-*.jsonl`
   跑一段 ≤20 行 python，验证 `CommandExecution` item 确有 `command`(数组)/`exit_code`(数字)/`status` +
   `payload.started_at_ms`/`completed_at_ms`，并验证 `session_meta` 首行的 `id` / `session_id` /
   `thread_source` 字段（主会话 + 一个 `spawn_agent` 子会话各验一次）。把实际观察到的字段样例写进
   `minimal_validation`。命令加 `timeout`。
7. **`files_to_read`**（控制 P4 上下文，别列太多）：至少含 `agate/scripts/agate-cmdstream-adapters.py`
   （DSHAdapter 段为主）+ `agate/scripts/agate-cmdstream-ir.py` + `agate/tests/unit/test_agate_cmdstream_adapters.py`
   + `agate/tests/fixtures/cmdstream/dsh-session.jsonl` + P1-requirements.md。
8. **SELF-GATE 预告**：P4 改 `agate-cmdstream-adapters.py` + `agate/tests/` + P7 改 `platform-notes.md` +
   `SETUP.md` 触发 SELF-GATE——P2 设计里点明「P4/P7 commit message 须含 `self-gate-review:` / `self-gate-skip:`；
   P7 派 protocol-alignment-review（A1-A6）」，作为下游阶段的既定要求，不需要 P2 自己做。

### 上游关联

- **P1-requirements.md**（同目录，已 approved）——30 条 BDD（§6）、spike 实测结论（§4，尤其 §4.1 事件形态 /
  §4.1.1 exit_code / §4.2 子会话 / §4.5 实时流对比）、同类扫描 12 行表（§3）、范围锁定（§5）、
  真机验证清单 V1-V8（§7）、裁剪说明（§9，逐阶段保留理由）
- **P0-brief.md**（同目录）——四交付面 / out-of-scope / 核心约束 6 条 / env_constraints；scope ① 已有
  `[P0_STALE: ① 需修正]` 标注（exit_code 有数字字段）
- **RM-AG0055 设计**：`docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`——§3.4.2
  检测信号差异点（差异点 4 = 截断排除，`truncated` 参与冻结检测不参与无效重复哈希）/ §3.4.3 阈值 /
  §3.4.4 适配器契约（`CommandStreamAdapter` 三方法）与「约一个文件、检测引擎零改动」承诺
- **机制事实**：`docs/research/cross-platform-dispatch-mechanics.md`（Codex 章 + 附录 A12 spawn_agent
  schema / A17 feature flag）
- **既有实现范式**：`agate-cmdstream-adapters.py` 的 `DSHAdapter`（line 394-621）——同样无数字 exit code
  的历史处理、同样的子会话定位问题、`_detect_truncated` 实现、`list_sessions` 的 `cwd` 参数语义。
  CodexAdapter 是它的近亲，优先照它的结构。

### 输入文件（按顺序读）

1. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`（30 BDD + §4 spike + §3 同类扫描 + §5 范围 + §7 真机清单 + §9 裁剪）
2. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P0-brief.md`（四交付面 / 核心约束 / env_constraints / `[P0_STALE]`）
3. `agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-review.md`（第 2 轮 approved——维度结论 + 复核段，了解已核实过什么）
4. `agate/scripts/agate-cmdstream-adapters.py`（`CommandStreamAdapter` 契约 line 95-114 / `DSHAdapter` line 394-621 全读 / `_sha1_hex` 助手 line ~68 / `ADAPTERS` line 623-628）
5. `agate/scripts/agate-cmdstream-ir.py`（`CommandRecord` dataclass line 31-44——十字段契约，不改）
6. `agate/scripts/agate-cmdstream-detect.py`（三态判定 + 阈值常量——理解它消费 `CommandRecord` 的哪些字段，确认零改动可行）
7. `agate/tests/unit/test_agate_cmdstream_adapters.py`（既有适配器单测范式；`test_bdd_6_detect_consumes_registry_zero_change` @ :317 精确等值断言原文；`test_bdd_7_fixture_sanitized` 脱敏校验清单 @ :325-333）
8. `agate/tests/unit/test_agate_cmdstream_detect.py`（检测引擎三态确定性试验范式；`:371` 附近 `test_bdd_24_output_platform_agnostic` 负向断言）
9. `agate/tests/fixtures/cmdstream/dsh-session.jsonl` + `claude-code-session.jsonl`（fixture 结构与脱敏约定范式）
10. `agate/scripts/verify-heartbeat-cmdstream/verify_cmdstream_detection.py`（若存在——虚拟时钟三态试验范式；否则 design-note 目录下同名）
11. `agate/platform-notes.md`（Codex 章现状 line 43-45「待补充」+ line 53-70 既有 Codex 列 + line 67-70 兼容性注记 + line 74 验证记录节 + line 176+ DSH 章作新兴平台文档范式）
12. `agate/SETUP.md`（找 DSH 小节作 Codex 小节结构范式）
13. `agate/phase-cards/P2-design.md`（本阶段卡片——产出规格 / 影响面梳理节 / gate_commands 规则 / C8 评审映射）
14. `agate/assets/execution-roles/architect.md`（角色定义 + 批次设计节 + 影响面梳理规格）
15. `docs/design-notes/260903-design-subagent-liveness-and-self-dispatch/`（§3.4.2 / §3.4.3 / §3.4.4）
16. `AGENTS.md`（worktree 根——改脚本 TDD 工作流、双工作区纪律、工具纪律）

### 客观查证信息（主 Agent 已核实，2026-09-09）

- **环境**：worktree `.worktrees/agate-TAG0033`，分支 `feat/TAG0033-codex-cmdstream-adapter`，
  `.state.yaml` phase=P1（P2 产出 commit 时随 P2-design.md 一起推进到 P2）/ judge.enabled=true。
  P1 已 commit（`4d75958 wf(TAG0033-P1): ...`）。codex-cli 0.153.4 + ChatGPT 登录。
- **`CommandStreamAdapter` 契约**（`agate-cmdstream-adapters.py` line 95-114）：`probe(self, path)` /
  `list_sessions(self, cwd)` / `read_commands(self, session_path)`。三个既有适配器
  （`ClaudeCodeAdapter` line 116 / `OpenCodeAdapter` line 293 / `DSHAdapter` line 394）+ `ADAPTERS`
  注册表 line 623-628（三键 `"claude-code"`/`"opencode"`/`"dsh"`）。CLI（detect.py）`choices=sorted(ADAPTERS.keys())`
  动态取自注册表。
- **`CommandRecord` 十字段**（`agate-cmdstream-ir.py` line 31-44）：`platform` / `session_id` / `tool` /
  `command` / `ts_start:int` / `ts_end:int|None` / `exit:int|None` / `exit_signal:str=""` /
  `output_hash:str|None` / `truncated:bool=False`。**不改这个 dataclass**。
- **P1 §4 spike 已确定的事实**（不用重查，直接用）：
  - `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO8601>-<uuid>.jsonl`（UTC 日期分层）
  - 每行 `{"timestamp","ordinal","type","payload"}`；shell 命令源 = `type=="event_msg"` +
    `payload.type=="item_completed"` + `payload.item.type=="CommandExecution"`；item 含 `command`(数组) /
    `exit_code`(数字) / `status` / `aggregated_output`；`payload.started_at_ms` / `completed_at_ms`(epoch ms)
  - `custom_tool_call` name=`"exec"` 的 `input` 为 `tools.apply_patch(...)` / `tools.web__run(...)` 时
    **不派生** `CommandExecution` → 不产出 CommandRecord（BDD-8）
  - `spawn_agent` 子会话 = 独立 `rollout-*.jsonl`；子会话 `session_meta`：`id`=子自身 id、
    `session_id`=父 id、`thread_source=="subagent"`、`parent_thread_id` 存在、
    `source.subagent.thread_spawn.depth` 存在
  - `codex features list`：`multi_agent` = stable/true（0.153.4）
- **C8 评审映射**（本任务 domains=[backend] + risk_level=medium）：命中「backend + 任意 → plan-eng-review」。
  **单评审角色**（非 high、非 full、无 frontend）——plan-eng-review 直接产出 `P2-review.md`，无需组长汇总。
  主 Agent 负责在你产出 P2-design.md 后派 plan-eng-review。
- **P2 gate 规则**（`check-gate.py P2`）：`candidate_count ≥2`（design_trivial/follows_existing_pattern 附
  理由时可 1）+ P2-review.md 存在且 `status: approved`（agent≠main）+ 四字段齐全
  （`packages`/`domains`/`ui_affected`/`gate_commands`）+ 含影响面梳理节。

### 产出文件字段

先 `Write` 出 `P2-design.md`（含正文骨架 + 影响面梳理节 + 5 设计点候选方案 + gate_commands），再用
`FILE=agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-design.md python3 ~/.agate/scripts/agate-md-field-set.py --list`
查字段并逐个 `set`；写入失败照错误提示修正，不手写 frontmatter；仍失败报告主 Agent。

frontmatter 必填：`phase=P2`、`task_id=TAG0033`、`type=design`、`parent=P1-requirements.md`、
`trace_id=TAG0033-P2-20260909`、`status=draft`、`created=2026-09-09`、`agent=architect`、
`candidate_count`（int ≥2）、`packages`（承接 P1 `[agate-scripts, agate-docs, agate-tests]`）、
`domains: [backend]`、`ui_affected: false`。可选：`follows_existing_pattern`（对照搬 DSHAdapter 的设计点）/
`dispatch_plan`（单行 flow YAML）。

### 返回

返回：P2-design.md 路径 + `candidate_count` + 5 个设计点各自的定论（一句话）+ `dispatch_plan` mode +
`minimal_validation` 关键观察 + 是否有范围外发现（有则停下报告）。不要自己派 plan-eng-review（主 Agent 派）。
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P2

路径：phase-cards/P2-design.md
---
# P2 — 方案设计

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → P2 不可裁剪。design_trivial / follows_existing_pattern 可简化（1 个候选方案），不可省略。

## 如果是首次进入本阶段

1. 派发 architect subagent → 产出 P2-design.md
   1.1 写 P2-dispatch-context-architect.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 C8 映射表派评审（见下方）
3. 评审通过 → P2-review.md status: approved
4. 预跑 check-gate.py P2（脚本化检查）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/（含 .state.yaml + 产出文件，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P2，不要提前写 P3——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P2): {摘要}"（phase=P2，P2 产出含 P2-design.md + P2-review.md）
7. P2 commit 完成后进入 P3：**phase 推进 P3 随 P3 产出 commit 一起**（P3-test-cases.md 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（方案选择有误 / 候选方案不足 / 评审 rejected）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P2 MAX=3）

## 前置条件

- [ ] P1-requirements.md 含 domains / risk_level / phases 声明
- [ ] P0-brief.md env_constraints 可查阅

## 派发

- **角色**：architect（`{agate_root}/assets/execution-roles/architect.md`）
- **输入**：P1-requirements.md + P0-brief.md
- **输出**：P2-design.md
- **派发 prompt 追加**：

```
## P2 最小验证
方案设计前，先用最小验证确认关键假设（10 行 HTML 测试页 / curl 请求 / 20 行脚本）。
验证结果写入 P2-design.md 的 minimal_validation 字段。
- 方案依赖浏览器行为/安全模型/外部系统行为 → 必须做最小验证
- 纯代码逻辑 → 须在 minimal_validation 字段声明 `纯代码逻辑，无外部系统依赖`（须写明依赖了哪些内部函数/数据转换）
```

## 产出规格

P2-design.md 必须包含：
- **候选方案 ≥2** + 权衡 + 选择理由（design_trivial / follows_existing_pattern 时可只写 1 个，见下方）
- **`candidate_count: N` 必填**：本方案候选方案数（≥2，design_trivial/follows_existing_pattern 时可 1），gate 按此字段校验，不再解析标题。你写几个候选就填几个，与正文一致。
- **四字段**：`packages:` `domains:` `ui_affected:` `gate_commands:`
- **files_to_read**：实现时需要参考的文件清单（控制 P4 implementer 上下文）
- **env_constraints**：确认/细化 P0-brief 的环境约束
- **minimal_validation**：验证结果 或 声明"纯代码逻辑，无外部系统依赖"（声明时须附理由）

`candidate_count`/`packages`/`domains`/`ui_affected` 写在文件头 **frontmatter**（`---` 分隔块），
不写正文；`gate_commands:`/`files_to_read:`/`env_constraints:`/`minimal_validation:` 留正文。
**可直接复制的完整样例**：
```yaml
---
phase: P2
task_id: TAG0001           # 替换为实际任务编号
type: design
parent: P1-requirements.md
trace_id: T001-P2-20260101 # {task_id}-P2-{YYYYMMDD}
status: draft
created: 2026-01-01
agent: architect
# ── v2.0 机器字段 ──
candidate_count: 2                # int ≥1，必填
packages: [pkg-a]                 # list，必填
domains: [backend, cli]           # list，必填
ui_affected: false                # bool，必填
ui_design_section: true           # bool，可选（presence 语义：ui_affected: true 时声明已含 UI 设计节）
---
```

**UI 设计节（`ui_affected: true` 时必含，P2 gate 校验）：** `ui_affected: true` 的 P2-design.md
正文必须包含 `## UI 设计` 节，节内含**渲染形态声明**（`渲染形态:` 声明行，复用 P1 frontmatter
`ui_render_shape` 的规范形态值 + 中文注释，gate 按规范化值比对校验 P1-P2 一致；无 P1 声明时按
布局型默认）+ **维度选择**（`适用维度:` 声明行）+ **按形态适配的 checklist**（常规布局型 =
布局/交互/视觉三类；渲染组件/时序特效型 = 渲染正确性/动效时序等适用维度 checklist；不适用的维度
显式声明"维度不适用"）。缺 UI 设计节 / 缺形态声明 / 缺按形态 checklist / P1-P2 形态声明不一致 →
P2 gate exit 1。结构规格见 `assets/execution-roles/architect.md`「UI 设计节」节（由 architect
兼任产出，不新增 designer 角色）。

**骨架产出（`project_phase: bootstrap` 时必含，P2 gate 校验）：** P1-requirements.md frontmatter
声明 `project_phase: bootstrap`（0→1 新项目；缺省 `established` 不触发）的任务，P2 architect 除
P2-design.md 外，还须在 task 目录下产出 `P2-skeleton.md`（须含 `## 骨架声明` 标题）。骨架内容以
「候选目录集合 + 项目侧声明」的参数化形式表达（不写死具体语言/框架目录名），模板见
`assets/templates/skeleton-template.md`，结构规格见 `assets/execution-roles/architect.md`
「骨架设计职责」节（由 architect 兼任产出，不新增专属角色）。`project_phase` 字段缺失或非
`bootstrap` 时不检查（向后兼容，行为与改动前一致）。

候选方案简化（须附理由，无理由视为无效声明，要求 ≥2 候选方案）：
- `design_trivial: true` + 理由（为什么 trivial）→ 可只写 1 个候选方案（P2 仍不可省略）
- `follows_existing_pattern: [src/foo.py]`（列出参照文件路径）→ 可只写 1 个候选方案，参照已有模式（P2 仍不可省略）

## dispatch_plan 机器字段（可选，TAG0014）

> 本字段是 P2 对**后续阶段编排方案**的机器声明（评估 + 编排模式，见 dispatch-protocol「派发编排机制」），由 architect 在"批次设计"节（execution-roles/architect.md）产出，P2 gate 校验其合法性。

方案含多个独立子任务（多包/多模块/high 复杂度）时，P2-design.md frontmatter 应声明 `dispatch_plan:`（单行 flow YAML，与 candidate_count 同级，**不入 frontmatter-check schema**，缺省不校验）：

```yaml
# ── v2.0 派发编排字段（可选）──
dispatch_plan: {mode: static-batch, parallel_limit: 3, batches: [{id: pkg-a, complexity: medium}, {id: pkg-b, complexity: low}]}
```

字段契约（gate 校验口径）：
- `mode` ∈ {single, static-batch, parallel, recon-then-split, serial}——编排模式（单发/静态拆批/并行/先理解后拆/串行链）
- `parallel_limit` 可选，≥1 整数——并行上限（缺省 3）
- `batches` 可选——mode ∈ {static-batch, parallel} 时每批须含 `id` + `complexity` ∈ {low, medium, high}；批数 ≤ parallel_limit
- 缺字段 / 坏 YAML → P2 gate 跳过校验，行为等同现状（向后兼容，不误拦）

## 影响面梳理（强制节）

**写候选方案之前**先做影响面梳理——方案的取舍取决于它牵动多大面，先设计再补影响面等于反过来给方案找理由。P0 卡片的「同类/影响面预判」给量级、P1 卡片的「同类扫描」给清单，P2 在这两者基础上做**候选方案级**的影响域分析，三处同源、逐级细化，不重复劳动。

P2-design.md 正文必须含影响面梳理节，覆盖三部分：

1. **改什么（Modify）**：逐文件/逐模块列出改动点 + 关联 BDD 编号；改动落点必须落到"哪个文件的哪个小节/函数"，不写"相关代码"这种模糊表述
2. **不改什么（Not Modify）**：显式列出**看起来该改但决定不改**的文件/范围 + 理由。这一栏比"改什么"更容易漏，也是 P4 implementer 判断范围边界的依据（避免"顺手改进"）
3. **风险在哪（Risk）**：每条风险配一条缓解措施；跨模块引用、双源同步（权威源 + 副本）、schema 变更、并发/资源竞争是高频风险项

梳理动作要有客观证据：grep/rg 命中清单、读过的消费方代码、既有 gate 脚本的校验口径——不是凭印象列。P1 已声明 `follows_existing_pattern` 的任务同样要做（沿用既有模式不等于影响面为零）。

## gate_commands 声明

gate_commands 在 P2 固化，后续阶段按此执行：

```yaml
gate_commands:
  P3: "pytest"                  # 可选：测试运行器（verbose 输出，供 check-tdd-red.py 自动读取）
  P5: "pytest -q --tb=no"       # 紧凑输出模式
  P5_e2e: "playwright test --reporter=line tests/e2e/"  # ui_affected: true 时必填
  P5_timeout_seconds: 120       # 可选：该 key 命令的预期耗时上限（秒），见下方字段规则
  P5_e2e_timeout_seconds: 300   # 可选：per-key 声明，不同命令类型各自取档
```

### `{key}_timeout_seconds` 字段规则

`timeout_seconds` 是 `gate_commands` 块内的**可选声明性字段**，用来给每条 gate 命令声明"预期耗时上限"，供跑命令的一方（主 Agent / subagent）据此设置 shell 层超时。四点规则：

1. **排除 P3**：`gate_commands.P3` 继续走既有 `AGATE_TDD_TIMEOUT` 环境变量机制（默认 120s，由 `agate_common.py` 的 `run_test_with_formatter()` 消费、`check-tdd-red.py` 读取，exit 124 → 超时 JSON，区分 A/B 类错误）。`timeout_seconds` **只服务 P5 / P6 / 其他非 P3 key**，不覆盖 P3。两层不合并：P3 层是运行时代码真实消费的超时，`timeout_seconds` 是给人和 subagent 读的静态声明
2. **per-key 声明**：写成 `{key}_timeout_seconds`（如 `P5_timeout_seconds` / `P5_e2e_timeout_seconds`），每条 key 各自声明，**不设整体共享默认**——单元测试与 E2E 的耗时差 2.5 倍以上，共享一个值起不到分类阈值的作用。命名与既有 `{key}_formatter` / `{key}_e2e` 的 per-key 惯例一致
3. **三档默认基准表**（**建议档位，需按命令类型手动声明，不是自动推断**——没有任何代码去"猜"命令属于哪一类）：

   | 命令类型 | 建议档位 | 依据 |
   |---------|---------|------|
   | 单元测试类（pytest / vitest 等） | 120s | 与 `AGATE_TDD_TIMEOUT` 默认值对齐，同类命令的既有锚点 |
   | E2E 类（Playwright / CDP） | 300s | 覆盖页面加载 + 多步操作；比脚本内部硬超时（HARD 90s/180s）更大——外层命令级预期时长必须留够内层完整走完的余量 |
   | 构建类（编译 / 安装依赖 / 打包） | 600s | 覆盖 `npm install` / 编译等长操作。宁可档位定高，也不要让长命令被误判失败（TPV0093 教训：`make test-quick` 挂 188 分钟） |

4. **向后兼容**：缺字段 → 行为等同现状（沿用 `dispatch_plan` 的"缺字段 / 坏 YAML → gate 跳过校验"先例），不新增强制阻断，老任务无需回填

与运行时超时纪律的关系：本字段是**静态声明**（层级 1），subagent 执行命令时真正去设 shell timeout 的是**层级 4** 的「命令超时兜底」（取值 = 预期耗时 ×1.5；本字段已声明时"预期耗时"直接取该值）。四层超时机制的完整分层见 dispatch-protocol.md「命令超时兜底与既有超时机制的分层关系」。

### env_constraints 与 gate_commands 的边界（不等价）

`env_constraints` 是**声明性字段**——它只做信息确认/注入（写清楚环境约束是什么，供 P4/P8 读取参考），本身不会被自动执行，也没有任何 gate 脚本会去校验 `env_constraints` 里写的条件是否真的成立。真正被执行的机制是 `gate_commands`：P5/P6 只会去跑 `gate_commands` 里声明的命令，不会去"执行" `env_constraints` 的内容。二者不等价，不能互相替代。

**因此**：任何需要被强制执行的约束，必须落到 `gate_commands`（有命令可跑、有 exit code 可判定），或者落到 P4/P8 阶段卡片里的明确 checklist 条目（有人工自查动作可执行）。只写进 `env_constraints` 而不落 `gate_commands`/checklist 的约束，等于没有强制力——architect 设计时若发现某条环境约束必须被强制执行，不要止步于写进 `env_constraints`。

### `--strict` 反模式：不要放进 `&&` 链路中间

`gate_commands` 的每个 key 声明的是**一条完整命令**，若把多个校验命令用 `&&` 拼接成一条命令串塞进同一个 key，会有短路问题——只要前一个命令非零退出，后面的命令（包括 `--strict` 校验）根本不会跑，看似"全部声明了"，实际后半段从未被执行过，问题被掩盖。

**反例（不要这样写）**：
```yaml
gate_commands:
  P5: "pytest -q --tb=no && check-protocol-consistency.py --strict && shellcheck scripts/*.sh"
```
上面这条命令一旦 `pytest` 失败就短路退出，`--strict` 校验和 `shellcheck` 都不会执行，历史上 TAG0004 等任务已经在这类写法上吃过亏。

**正确做法**：把每个校验拆成独立的 key 分别声明，各自独立跑、独立记录 pass/fail，不共享短路关系：
```yaml
gate_commands:
  P5: "pytest -q --tb=no"
  P5_consistency: "check-protocol-consistency.py --strict-errors-only"
  P5_shellcheck: "shellcheck scripts/*.sh"
```
`--strict-errors-only`（仅 ERROR 判失败）适合日常任务默认使用；`--strict`（WARNING-only 也判失败）保留给专门做 WARNING 债务清理的任务主动选用。

### `P3_xxx` 禁止声明（P2 卡禁令，BDD-6）

`gate_commands` 的测试命令键只允许裸 `P3`（`check-tdd-red.py` 只收集精确键
`key == "P3"`）。禁止声明 `P3_xxx` 检测键：旧解析器曾用 `startswith("P3")`
静默收集辅助键，致 TDD 误执行非测试命令。白名单后缀清单（不收集为检测命令）：
`_formatter` / `_timeout_seconds`（元键，`is_gate_meta_key` 豁免）+ `_e2e`
（E2E 形态，P5_e2e 消费，P3 永不收集）+ 历史 `_js` / `_html`（已退役，
不得复用为检测键；未来多栈回归走协议修订登记收集后缀，不走静默收集）。

### CHECK / 扫描面上线流程（DEBT0025：先全量扫描存量）

`check-platform-assumptions.py` 新增 CHECK / 扫描面上线时，先全量扫描存量
测试树登记命中清单，有命中先登记再启用常驻阻断，避免存量命中阻断正常开发。

## 评审派发（C8 机械映射）

按 P1 声明的 domains + risk_level 机械映射评审：

| domain | risk_level | 必须派的评审 |
|--------|------------|------------|
| backend | 任意 | plan-eng-review（P2 方案评审） |
| frontend | 任意 | plan-design-review |
| 任意 | high | plan-eng-review（硬规则，必须派独立 subagent） |
| 任意 | full（tier=full 或声明 ceremony: full）| plan-eng-review（硬规则，必须派独立 subagent）+ cso（security 域）+ P7 不可裁 |
| P1-requirements.md 含 [NEED_CONFIRM] 且涉及业务方向 | 任意 | plan-ceo-review |

> **去重说明**：同一任务命中多行且触发同一评审角色时，去重只派发一次（如 backend + high 均命中 plan-eng-review，只派 1 个 plan-eng-review，不重复派发）。

多个评审角色 `专家组并行` → 组长汇总 → P2-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件（示例非穷举，按 C8 映射表触发）：
   - plan-eng-review → P2-review-eng.md
   - plan-design-review → P2-review-design.md
   - plan-ceo-review → P2-review-ceo.md
   - cso → P2-review-cso.md
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长输入：所有评审文件路径
5. 组长产出：P2-review.md（统一 status: approved / rejected）。**组长 subagent 产出的 P2-review.md 的 Header agent 字段必须是组长角色名（非 main）——check-gate.py P2 硬拦截 agent=main 的 approved**
6. 组长规则：
   - 不发表新意见，只汇总
   - 任何专家标 BLOCKER → status: rejected
   - 多位专家分歧 → 标「专家组分歧」交人工
   - 全票无 BLOCKER → status: approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P2-review.md。

review 不通过 → architect 修改方案 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

**UI 测试选择器**：涉及前端时，P2 design 建议声明 UI 组件的稳定测试标识清单（如 `data-testid`，而非 class 命名）。P3 test-designer 用稳定标识定位元素，P4 implementer 按清单实现--class 命名可重构，稳定标识不变。具体方案由 P2 architect 决定。

## gate 规则

```bash
check-gate.py P2 $TASK_DIR
```

- 候选方案数 ≥2（design_trivial / follows_existing_pattern 时可只写 1 个）
- P2-review.md 存在且 status: approved（agent≠main）— 不存在 → gate exit 1
- 四字段齐全（packages/domains/ui_affected/gate_commands）
- gate_commands.P3 可选（非 pytest 项目建议声明，供 check-tdd-red.py 自动读取测试运行器）
- 候选方案 ≥2 时含权衡/选择理由

## 推进条件（全部满足才写 phase: P3）

- [ ] P2-design.md 候选方案 ≥2（或 design_trivial/follows_existing_pattern 须附理由时可只写 1 个）+ 四字段齐全
- [ ] 含「影响面梳理」节（改什么 / 不改什么 / 风险在哪 三部分齐全，且写在候选方案之前）
- [ ] P2-review.md 存在且 status: approved（agent≠main）
- [ ] gate_commands.P5_e2e 已声明（ui_affected: true 时）

## 常见错误

1. **忘了最小验证**：方案依赖外部系统行为（API MIME 类型、浏览器 CSP 等）但直接假设前提成立 → 到 P6 才发现不可行。跑一个 curl / 10 行 HTML 就能 5 分钟发现
2. **gate_commands.P5 只列单元测试**：UI 任务时缺少 P5_e2e → P5 不会跑端到端验证
3. **files_to_read 列太多文件**：把所有相关文件都列上 → P4 implementer 上下文爆炸。只列确实需要参考的
4. **忘了派评审**：按 C8 映射机械执行，不靠"觉得不需要"
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P4 依赖 files_to_read 导航代码阅读范围
- P5 依赖 gate_commands 执行验证命令
- P6 依赖 ui_affected 判断是否需要 vision-helper
- gate_commands 在 P2 固化后 P4-P6 不能改——设计阶段是声明验证契约的唯一窗口

> 完成 → 读 phase-cards/P3-tdd.md
<!-- AGATE_CARD_END -->
