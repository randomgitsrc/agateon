# tech-debt 条目模板

> 用途：登记协议/项目技术债。文件落 `{AGATE_WORKSPACE}/debt/tech-debt.md`，每条 DEBT = 一个 ` ```yaml ` fenced block（机器校验）+ 可选正文（人读），标题按 id 编号（`## DEBT0001`）。
> 机器校验：`python3 {agate_root}/scripts/check-debt.py {AGATE_WORKSPACE}/debt/tech-debt.md`（schema 校验，exit 0/1）。
> 回退覆盖比对：`python3 {agate_root}/scripts/check-debt.py --retreat-coverage`（git log 的 retreat 提交 vs `source: retreat` 条目，缺失 WARNING）。

## 登记判据（三分法）

登记前回答一句话：**"不修它，当前任务的验收声明会不会变成假的？"**

1. **会** → 登记（债已经威胁到验收真实）
2. **不会，但会让未来变更更贵 / 更危险** → 登记（技术债的本质：未来变更成本）
3. **都不影响**（验收声明不受威胁，未来变更成本不变）→ **不登记**（合法出口，防止登记簿变成垃圾场）

> **硬规则：登记 DEBT 不豁免当前任务。** 记了债 ≠ 当前任务的验收声明可以打折扣——该完成的验收一个都不能少。登记只是承认"有账"，不改变本期必须交付的范围。

## 字段表（schema 校验，缺失/非法即 exit 1）

| 字段 | 必填 | 枚举 / 类型 | 说明 |
|------|------|------------|------|
| `id` | 是 | str，文件内唯一 | 登记簿唯一引用 id |
| `category` | 是 | `technical` / `management` / `protocol` | 债的类型 |
| `title` | 是 | str | 一句话描述 |
| `status` | 是 | `open` / `in_progress` / `closed` | 三态 |
| `priority` | 是 | `high` / `medium` / `low` | 优先级 |
| `evidence` | 是 | 非空 list（`path`/`note`/`ref`） | 债的出处证据（回退债必须引用 retreat 提交哈希） |
| `impact` | 是 | str | 不修的影响 |
| `recommendation` | 是 | str | 建议的处理方向 |
| `closure_criteria` | 是 | 非空 list | 关闭判据 |
| `source` | 是 | `retreat` / `review` / `retrospective` | 债的来源 |
| `created_at` | 是 | str | 登记日期 |
| `task_id` | 否 | str 或 null | 立项任务（`closed` 必填） |
| `closed_at` | `closed` 时必填 | str（如 `2026-08-20`） | 关闭日期（RM-AG0088 / DEBT0033 起取代原「evidence 须含 P5/P6」子串判据） |
| `source_ref` | 否 | str，格式 `<task_id>:<DG id>`（`task_id` 为**裸编号**，如 `TAG0050`） | **双向回指**锚（TAG0050 批 E）：当该债由某任务的**设计缺口**析出时回指其出处——① P4 缺口（`basis: followup:DEBT<n>`）由 `gate_p7` **机械校验**回指成立；② **P7 缺口**（被「接受/延后」但无 owner 者，2026-10-09 外部实施评审 m-2 用法）**仅作记录**、不受 `gate_p7` BDD-66 校验 |

## 三态语义

| status | 含义 | 准入 |
|--------|------|------|
| `open` | 已登记未立项 | 无（`task_id` 非空即视为已立项，属 `in_progress` 语义，schema 不拦截此组合） |
| `in_progress` | 已立项/进行中 | `task_id` 非空即视为 in_progress |
| `closed` | 已关闭 | **必须**含 `task_id` + `evidence` 引用该 task_id + **`closed_at`**（关闭时间）（否则 schema 拦截；RM-AG0088 / DEBT0033 起取代原 P5/P6 子串判据） |

## 示例条目

### open（未立项）

```yaml
id: DEBT0001
category: technical
title: 模块耦合
status: open
priority: high
evidence:
  - path: archived/docs-2026-08/reviews/review-20260812-1204.md
impact: 未来变更更贵
recommendation: 拆分模块
closure_criteria:
  - 拆分完成
source: review
created_at: 2026-08-12
```

### closed（须 task_id + 引用该 task_id 的 evidence + closed_at）

```yaml
id: DEBT0002
category: management
title: 验收流程遗留
status: closed
priority: medium
task_id: TAG0003
evidence:
  - path: agate-workspace/tasks/TAG0003-workspace-architecture/P6-acceptance.md
impact: 影响后续验收
recommendation: 补登记
closure_criteria:
  - 验收通过
source: review
created_at: 2026-08-12
closed_at: 2026-08-20   # closed 条目必填（RM-AG0088 / DEBT0033）
```

### 回退强制（source: retreat）

回退落地（`agate-retreat-to.py`）后**必须**建 `source: retreat` 条目，`evidence` 引用该次回退的 retreat 提交哈希（供 `check-debt.py --retreat-coverage` 比对）：

```yaml
id: DEBT0003
category: management
title: 回退未建债
status: open
priority: medium
evidence:
  - ref: 023b28b
impact: 回退原因可能复发
recommendation: 补建债条目
closure_criteria:
  - 条目补齐
source: retreat
created_at: 2026-08-12
```

> 注意：示例条目占位（如 `023b28b`）仅为示意，真实条目应填实际 retreat 提交哈希；`{agate_root}` 等占位符会在 CHECK 1 中被 sanitize。
