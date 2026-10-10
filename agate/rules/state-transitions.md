# 状态转移与恢复规则

> 权威源：`agate/state-machine.md`。本文提取跨阶段共用的转移/重试/恢复规则，供各阶段卡片按需查阅。

## 状态集合

```
P0 → P1 → P2 → P3 → P4 → P5 → P6 → P7 → P8 → READY → DONE
任意阶段 → PAUSED（人工介入后恢复）
```

## 转移条件（逐阶段）

### P0 → P1
- P0-brief.md 完成，四字段自查通过（task / known_risks / executor_env / env_constraints）

### P1 → P2
- P1-requirements.md 有效 + 含至少一条 BDD 验收条件 + 无未决行首 NEED_CONFIRM（倾向项 `[SUGGEST:]` WARNING 不阻塞；无待确认项写 `[NO_NEED_CONFIRM]`）+ 无 status: GAP（supplementable 不阻）
- frontend 任务（domains 含 frontend）：P1 必须声明 vision 视觉能力条目（need 含 visual/vision，
  status ∈ available/supplementable/GAP，缺失 P1 gate exit 1）+ 渲染形态/维度声明合法性通过
  （声明 ui_render_shape 但维度空 / 维度不在分类框架且未在 BDD 标题声明 → exit 1）

### P2 → P3
- P2-review.md 有效 + status: approved + P2-design.md 声明 packages/domains/ui_affected/gate_commands + 候选方案 ≥2 + 含权衡/选择理由/取舍/考量/trade-off
- UI 任务（ui_affected: true）：P2-design.md 必须含 UI 设计节（## UI 设计 + 渲染形态声明 +
  维度选择 + 按形态 checklist，P2 gate 拦截缺失；形态声明须与 P1 ui_render_shape 一致，
  规范化值比对）

### P3 → P4
- check-tdd-red.py exit 0 + assertion_failures>0 + collection_errors==0
- UI 任务：P3 含 Playwright/E2E 用例

### P4 → P5
- 暂存区含非 md/yaml 文件（git diff --cached）

### P5 → P6
- gate_commands.P5 全部 exit 0 + failed==0 + 无 PROD_TOUCHED（二值格式：触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`）
- UI 任务：gate_commands.P5 E2E 命令 exit 0

### P6 → P7
- check-gate.py P6 exit 2（FAIL=0 / NC=0 / 证据非空）
- check-p6-provenance.py exit 0/2（由审计 3 自动对照 BDD 总数；**exit 2 = 协作规范 WARNING［缺 agent 字段］，不阻塞**；exit 1 硬阻，无过渡期兜底）
- UI 任务 P6 双证据按 P1 vision 能力三态分档：available/supplementable（无声明默认 available）→
  vision YAML 引用 + blocker_count=0；GAP → 截图/帧序列 + 人工复核记录引用（不要求 vision YAML）；
  证据形式按渲染形态选择（常规布局型=截图/行为日志；渲染组件/时序特效型=帧序列/渲染输出对比/
  时序截图，check-p6-evidence.py 校验形态匹配）

### P7 → P8
- 声明行 [BLOCKER]: N 条 被排除后 =0 / [DEVIATION-CRITICAL] 同理
- DESIGN_GAP 全部配对 REVIEWED

### P8 → READY
- 各 package 发布检查 exit 0 + version bump 确认 + CHANGELOG 非空
- READY 收尾检查：测试环境清理 / 开发环境还原 / git tag 创建

## 重试上限

详见 `state-machine.md`《重试上限》——权威唯一来源，本文件不重复维护。

重试记录按阶段独立存储于 `.state.yaml` 的 `retries` 字段。

## 回退规则

| 回退范围 | 允许？ | 处理 |
|----------|--------|------|
| Pn → Pn-1（单步回退）| ✅ 允许 | retry+1，定向回补不清零目标阶段已有的 retry |
| |n-m| ≥ 2（跨多阶段）| ❌ 强制 PAUSED |

**单步回退必须同步写 retries（RM-AG0042）**：单步回退（Pn→Pn-1）必须同步在 `retries[目标阶段]` 追加一条记录，不能只改 `phase` 字段；`check-state-transition.py` 对"暂存版本 `retries[目标阶段]` 长度未超过 HEAD 版本长度"的情形做机械校验并拦截（阻断，exit 1）——不要求该阶段此前必须已有过 retries 记录，首次单步回退（此前从未记录过）同样会被拦截——只手动改 `phase` 而绕过 `agate-retreat-state.py`/`agate-retreat-to.py` 的标准写入路径会被 gate 挡下。

**回退时的自撰产出归档（self-authored gate 专属）**：P1/P2/P6/P7 的产出文件（判定对象是主 Agent/verifier 自己写的 markdown）在被跨过时必须先归档，不能留在原位——否则重新走到该阶段时，旧文件的内容可能被误当作仍然有效，`check-gate.py` 不会区分"修复前写的"还是"修复后写的"。P4/P5 属于外部产出 gate（判定对象是测试运行器 exit code），没有跨重试持久化的自撰文件，不需要归档。

```bash
python3 agate/scripts/agate-archive-stale-outputs.py {被跨过的阶段} {TASK_DIR}
```

`check-state-transition.py` 会在检测到单步回退时，检查被跨过阶段的产出文件是否仍在原位——若未归档，直接拦截 commit，提示先跑上面这条命令。归档不是删除：文件被移到 `{TASK_DIR}/.archived/{时间戳}-{阶段}/`，历史证据留痕保留；同时会在 `{TASK_DIR}/.retreat-history.md`（不被归档，始终留在当前任务目录）追加一份摘要，P6 的话还会摘录具体 FAIL 详情，避免重新派发时忘记"当初是哪里失败的"。

**多步回退的自动化**：若诊断已经明确指向 2 阶之外（如 P6→P4），不需要手动分两次执行"归档→改 phase→commit"，可以直接：

```bash
python3 agate/scripts/agate-retreat-to.py {TASK_DIR} {目标阶段} "{诊断原因}"
```

这个脚本会依次产生多个独立的、diff=1 的真实 commit（每一步都归档 + 过 gate 校验），不会绕过或放宽 `check-state-transition.py` 对大跳回退的 PAUSED 限制——它只是自动化了合法的单步回退序列，不是让大跳直接放行。调用前需确保暂存区没有与本次回退无关的文件（脚本会检查并拒绝）。

**回退落地后必须建 DEBT 条目（TAG0001 强制）**：任何正式回退（`retreat:` 提交，含多步回退）完成后，必须建立 `source: retreat` 的 DEBT 条目，`evidence` 引用该 retreat 提交的哈希——模板见 `assets/templates/tech-debt-template.md`，条目登记于 `{AGATE_WORKSPACE}/debt/tech-debt.md`。回退是协议定义的事实事件，登记不依赖任何人的判断（BDD-12）；事后 `check-debt.py --retreat-coverage` 会把未登记的 retreat 提交比对出来并报 WARNING（只读提醒，不阻断 commit/发布）。

## 前向跨阶规则（TAG0050 评审 M-1）

前向跨阶（`Pn → Pn+k`，k ≥ 2）**对非 legacy 任务（账本含 `task_created`/`task_adopted`）由 `check-state-transition.py::check_transition` 机械校验**（**M-1 读法修订（RM-AG0113）**：`declared` 的读取与 `check-pruning.py::_p1_field` **同代码路径**——`agate_common.fm_field_value` 优先、**frontmatter 缺失时**回退 `body_field_value` 的正文结构化解析；M-1 禁止的是「用 `^phases:\s*\[` 正则匹配正文」这一**写法**，非「读正文」本身，且回退只会让判据**更严**）——hook 与 CI 回放共用该函数，不是只由目标阶段产出兜底（TAG0050 实测：`gate_p5` 兜底返回 2、`_gate_p7_structured` 曾对缺产出放行）：

- 被跨过的阶段须**已从 P1 `phases` 移除并在 `pruned` 中声明**（`declared` 读法与
  `check-pruning.py::_p1_field` **同代码路径**：frontmatter 结构化值优先，**缺失时**回退
  `agate_common.body_field_value` 的正文结构化解析——**M-1 读法修订见上**；`pruned` 恒为
  frontmatter 结构化字段）；
- **不可跳过的阶段**（P1 需求基线 / P2 方案设计 / P4 实现 / P5 技术验证 / P6 验收）**一律不得跨过**
  ——该集为**数据面单源**：`agate/rules/phases.yaml` 顶层键 `non_prunable_phases`
  （`check-pruning.py` 与 `check-state-transition.py` 经 `agate_common.non_prunable_phases()` 共读，RM-AG0110）；
- 合法前向跳只有裁剪后的跳变，如 `P2→P4`（裁 P3）、`P6→P8`（裁 P7）。
- **legacy 任务维持不检查**（历史任务行为不变，详见 `state-machine.md`《阶段跳过转移规则》）。

## PAUSED 恢复

- 人工确认/决策后恢复到 PAUSED 前的阶段
- PAUSED 原因 = retry 耗尽 → recovery_bonus=1，允许额外 1 次重试（可选，写入 .state.yaml）
- SCOPE+（行首声明格式）暂不处理，恢复后一并纳入 P1 基线增补

## 中断恢复步骤

1. 重读 orchestrator-template.md 的 mapping 表 → 查当前阶段卡片
2. 读 {AGATE_WORKSPACE}/tasks/active-tasks.md → 确认进行中任务
3. 读 .state.yaml → 确认 phase + retries
4. 读 {AGATE_WORKSPACE}/tasks/{Txxx}/ → 确认产出文件是否存在（不存在 → 无效标记，回退到 Pn-1）
5. 按卡片指引执行当前阶段

## 状态标记绑定（T019 教训）

.state.yaml 标记 Pn，但 Pn 产出文件不存在 → 无效标记。回退到 Pn-1 重新执行 gate。标记不能在验证之前。

## PROD_TOUCHED

任意阶段出现行首 PROD_TOUCHED 标记（二值格式：触发写 `[PROD_TOUCHED] {描述}`，未触发写 `[PROD_NOT_TOUCHED]`）→ 立即 PAUSED，报告人工。
