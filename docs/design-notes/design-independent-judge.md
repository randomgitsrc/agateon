# 独立 Judge 机制设计（agate 协议增强提案）

> 状态：**已落地（TAG0020，v0.59.0，RM-AG0032 P6.5 独立 Judge）**
> 目标：对抗 `LIMITATIONS.md` 局限 3——"自写 gate 的作者与评判者同为一人，造假成本低"。参照竞品 [oh-my-agent](https://github.com/first-fluke/oh-my-agent) 的独立 judge + append-only 事件账本模式，融入 agate 现有双层角色体系。

---

## 1. 问题定义

### 现状（局限 3 原文要点）
- P6/P7 的 gate 判定对象是"主 Agent/subagent 自己写的文件"（P6-acceptance.md、P7-consistency.md）
- 现有缓解：证据存在性检查、provenance 六道审计、BDD 计数对照——**只是提高造假成本，不是硬保证**
- 根因：verifier 在 P5/P6 的结论"测试通过、条件满足"与事实之间，缺乏**独立第三方复核**

### 要解决的三个具体造假/漂移场景
1. **叙述与事实不符**：subagent 声称"BDD-3 通过"，实际从未运行（或运行失败被忽略）
2. **标准衰减**：P1 定 12 条 BDD，P6 只验了其中 8 条，"看起来完成了"
3. **回归盲区**：修 BDD-2 时悄悄破坏 BDD-1（已 PASS 项不复验）

---

## 2. 设计总览

```
P5 技术验证 → P6 验收（verifier 自评，现状）→ 【新增】P6.5 独立 Judge 复核 → P7 一致性
                                    │
                        judge 复核是 P6→P7 的硬门槛：
                        verdict: PASS 才可推进；FAIL/NEEDS-REVISION 弹回
```

**核心原则（与 agate 哲学一致）**：
- Judge 是**机械可判定的**——verdict 落盘为机器可读文件，gate 脚本读 exit code
- Judge 是**信息隔离的**——fresh context，只看到标准（P1 BDD + P2 验收设计），看不到实现者的自述
- Judge 是**有成本上限的**——token/轮次预算，防无限复核

---

## 3. 角色设计：`judge`（新增 review-role）

### 3.1 角色文件：`assets/review-roles/judge.md`

| 字段 | 定义 |
|------|------|
| 角色名 | `judge`（验收独立裁判）|
| 层 | review-roles（评审层，非执行层）|
| 插入阶段 | P6 之后、P7 之前（编号 **P6.5**）|
| 派发条件 | **所有任务强制**（与 P6 不可裁剪对齐；高风险任务可由人工指定 double-judge）|
| 输入（只传路径）| `P1-requirements.md`（BDD 标准）、`P2-design.md` 的验收相关节、`P6-evidence/` 目录、`.state.yaml`、`gate-events.jsonl` |
| **禁止输入** | `P6-acceptance.md`（实现者的自述）、implementer/verifier 的 dispatch-context（防锚定）|
| 产出 | `P6.5-judge-verdict.md`（Header 含 `status: passed/rejected/needs-revision` + `criteria_total` + `criteria_passed` + `verdict_evidence` 字段）|
| 认知模式 | ① 逐条重验**所有** BDD（含已 PASS 项）② 只信证据文件与 git log，不信叙述 ③ 每条结论必须引用证据路径 ④ 禁止"看起来没问题"式结论 |

### 3.2 与现有角色体系的关系（挂靠现有机制）

agate 已有"专家组并行评审 + 组长汇总 + status 门槛映射"机制（role-system.md），judge 是**其特化**：

- status 映射沿用现表：`passed → approved`、`needs-revision → needs-revision`（计入 retry）、`rejected → rejected`
- 派发方式沿用 dispatch-prompt.md 模板 + 方法 B（general subagent + 角色文件注入，跨平台最稳）
- 高风险任务可派 **double-judge**（两个独立 judge 并行，verdict 不一致 → 组长汇总或交人工）

---

## 4. 防造假机制（三层）

### 层 1：信息隔离（防止"被实现者带偏"）
- judge 的 dispatch-context **绝不包含** P6-acceptance.md 及实现者的任何自述
- 只给：标准（P1 BDD）、证据目录、git log 查询权
- 实现：`dispatch-prompt.md` 新增「Judge 信息隔离」节；`check-judge-verdict.py` 校验 judge 的 dispatch-context 文件内容不含被禁输入（白名单校验）

### 层 2：证据交叉核对（防止"无中生有"）
judge 每条结论必须引用证据，gate 脚本做**机械核对**：

| 核对项 | 判定 | 脚本 |
|--------|------|------|
| BDD 总数一致 | judge 声明的 `criteria_total` == P1 BDD 条数 == P6 声明的条数 | `check-judge-verdict.py`（对照 P1-requirements.md 计数）|
| 证据存在 | 每条 BDD 引用的证据文件真实存在且非空 | 复用 `check-p6-evidence.py` 逻辑 |
| 证据唯一 | 证据 md5 去重（同一截图糊两处 → FAIL）| 复用现有 avg-hash/md5 去重 |
| 执行留痕 | 关键 BDD 对应的命令在 `gate-events.jsonl` 中有真实 exit 0 记录 | `check-events.py`（新增）|
| git 留痕 | 声称的产出 commit 在 `git log` 中存在且 author 为对应角色 | 复用 `check-p6-provenance.py` 审计 |

### 层 3：append-only 事件账本（防止"事后篡改"）
新增 `{AGATE_WORKSPACE}/tasks/{Txxx}/gate-events.jsonl`：

```jsonl
{"ts":"2026-08-20T10:00:01Z","event":"gate_run","phase":"P5","cmd":"pytest -q","exit":0,"runner":"main"}
{"ts":"2026-08-20T10:05:12Z","event":"judge_verdict","phase":"P6.5","verdict":"passed","criteria_total":12,"criteria_passed":12,"judge_agent":"judge-7f3a"}
{"ts":"2026-08-20T10:05:13Z","event":"state_transition","phase":"P6.5","from":"P6","to":"P7"}
```

- **append-only 约束**：文件只能追加，不允许改写历史行（gate 校验行序时间戳单调 + 行内哈希链：每行含 `prev_hash`）
- 谁来写：`agate_common.py` 新增 `append_event(task_dir, event)`；hook 和 gate 脚本统一走它
- 审计：`check-events.py` 验证哈希链完整 + 时间戳单调 + 无空洞（gate 判定前置条件）

---

## 5. 预算与防死循环

| 预算维度 | 上限 | 判定 |
|----------|------|------|
| judge 复核轮次 | ≤2 轮（含首轮），超限 → `verdict: rejected` + 交人工 | 写入 state-machine.md 重试表（P6.5 行）|
| judge token 预算 | 默认 100k token（可用 `judge_token_budget` 字段覆盖）| 超限 → 按已验条目部分裁决 + 标注 `partial: true` |
| 时间预算 | 默认 30 分钟 wall-clock | 超时 → 同上 |

预算耗尽时的**诚实降级**（对齐 oh-my-agent 的"stop honestly with partial status"）：
- `partial: true` 时 P6.5 gate 判定为 **needs-revision**（不静默放行），主 Agent 决定补派或人工接管
- 账本中记录 `reason: budget_exhausted`

---

## 6. 状态机与 .state.yaml 集成

```yaml
# .state.yaml 新增字段
judge:
  rounds: 2            # 已用轮次
  last_verdict: passed
  partial: false
  double_judge: true   # 高风险任务
retries:
  P6.5:
    - round: 1
      failure_mode: judge-needs-revision
      adjustment: "……"
```

- 状态机新增转移：`P6 → P6.5 → P7`；`P6.5(needs-revision) → P6`（弹回，计入 retry 上限）
- 迁移兼容：旧任务无 `judge` 字段 → gate 对**历史任务**跳过 P6.5 要求（只对新任务生效），避免存量任务全挂

---

## 7. 涉及的文件改动清单（协议本体）

| 文件 | 改动 |
|------|------|
| `assets/review-roles/judge.md` | **新增**（角色定义）|
| `agate/scripts/check-judge-verdict.py` | **新增**（verdict 门槛判定）|
| `agate/scripts/check-events.py` | **新增**（事件账本审计）|
| `agate/scripts/agate_common.py` | 新增 `append_event()` + `read_judge_verdict()` |
| `agate/scripts/check-gate.py` | 增加 `P6.5` 阶段分支 |
| `WORKFLOW.md` | P1-P8 总览表加 P6.5 行；P6 节补"judge 复核"说明 |
| `state-machine.md` | 转移表 + 重试上限表加 P6.5 |
| `dispatch-protocol.md` | 「Judge 信息隔离」节 + P6.5 派发流程 |
| `phase-cards/P6-acceptance.md` | 门槛节补"P6.5 judge 复核（强制）" |
| `assets/templates/dispatch-prompt.md` | Judge 专用追加节（信息隔离 + 预算声明）|
| `SELF-GATE.md` | 触发面已含 `agate/**/*.md` 与 `scripts/*.py`，本改动自动触发 self-gate review |
| `tests/` | 新增 `test_check_judge_verdict.py`、`test_check_events.py` + 回归用例（BDD 计数对照、哈希链、信息隔离白名单）|

---

## 8. 与竞品对标（设计取舍说明）

| 特性 | agate 本设计 | oh-my-agent | 取舍理由 |
|------|--------------|-------------|----------|
| 独立 judge | ✅ P6.5 强制 | ✅ 每轮全部重验 | 对齐 |
| 信息隔离 | ✅ 白名单校验 | ✅ fresh context | 对齐，agate 加机械校验更严 |
| 事件账本 | ✅ JSONL + 哈希链 | ✅ JSONL append-only | 对齐 + 哈希链防改写 |
| 预算 | ✅ 三档预算 | ✅ quota_cap | 对齐 |
| 判据来源 | P1 BDD（人类可读标准）| 工作流 criteria | agate 更贴合"需求基线即契约"哲学 |
| 治理成本 | 每任务多 1 次派发 | 每轮多 1 次 judge | agate 用"强制但仅 P6.5 一次"控制成本 |

**设计红线**：不引入"LLM 当 gate 主判据"——judge 的 verdict 仍需叠加机械核对（层 2/3），LLM 结论只作行为描述，exit code 才是门槛（保持 agate"gate 是硬边界"哲学）。

---

## 9. 落地节奏（建议并入 roadmap RM-AG0029）

1. **Phase 1（机制落地）**：judge.md 角色 + P6.5 gate + 信息隔离 + verdict 文件；跑通 1 个 dogfooding 任务（TAG0018）
2. **Phase 2（账本强化）**：gate-events.jsonl + 哈希链 + check-events.py；历史任务跳过兼容
3. **Phase 3（预算与 double-judge）**：token/时间预算 + 高风险 double-judge
4. **Phase 4（回填验证）**：对比启用前后 P7 BLOCKER 检出率，产出实证报告
