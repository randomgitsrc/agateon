# Phase Cards — 渐进披露协议入口

> 不再一次读完 8 个协议文件。当前在哪个阶段，只读哪张卡片。

## 卡片索引

| 阶段 | 卡片 | 内容 |
|------|------|------|
| P0 | [P0-orchestrator.md](P0-orchestrator.md) | 任务启动：P0-brief / 环境自检 / 任务粒度 |
| P1 | [P1-requirements.md](P1-requirements.md) | 需求基线：BDD / domains / 裁剪声明 |
| P2 | [P2-design.md](P2-design.md) | 方案设计：候选方案 / gate_commands / 评审派发 |
| P3 | [P3-tdd.md](P3-tdd.md) | TDD 红灯：测试设计 / check-tdd-red |
| P4 | [P4-implementation.md](P4-implementation.md) | 代码实现：files_to_read 导航 / 评审派发 |
| P5 | [P5-verification.md](P5-verification.md) | 技术验证：gate_commands 执行 / E2E |
| P6 | [P6-acceptance.md](P6-acceptance.md) | 验收：BDD 对照 / vision-helper 绑定 |
| P6.5 | （无独立卡片，见 P6 卡「judge 复核」节）| 独立 Judge 复核：fresh context 逐条重验全部 BDD；`.state.yaml` phase 保持 P6 直至 P7 |
| P7 | [P7-consistency.md](P7-consistency.md) | 一致性：DESIGN_GAP / SCOPE+ 闭环 |
| P8 | [P8-release.md](P8-release.md) | 发布：bump / CHANGELOG / 收尾清理 |

## 跨阶段规则（按需查阅）

| 文件 | 查阅时机 |
|------|---------|
| [../rules/state-transitions.md](../rules/state-transitions.md) | 推进到下一阶段 / 重试 / PAUSED 恢复 |
| [../rules/review-mapping.md](../rules/review-mapping.md) | P2 / P4 派发评审时 |

## 旧协议文件（Reference）

卡片查不到的信息，回退到完整协议文件：

| 文件 | 作用 |
|------|------|
| `WORKFLOW.md` | 阶段总览 + 完整流程 |
| `dispatch-protocol.md` | 派发模板（完整版）/ 裁剪规则 / 特殊事件 |
| `state-machine.md` | 状态机（完整版）/ 单步函数 / .state.yaml 规范 |
| `role-system.md` | 双层角色体系（完整版） |
| `loop-orchestration.md` | /loop 自动编排 |
| `git-integration.md` | Git commit 规范 / push 策略 |
| `platform-notes.md` | 各平台适配说明（平台能力权威源） |
| `LIMITATIONS.md` | 已知局限 |
| `SETUP.md` | 首次接入（平台注册 + 装 hook）|
| `CONTEXT.md` | 术语表 / 统一语言 |
| `adr.md` | 架构决策记录（A7 审查锚点）|
| `UPGRADING.md` | 存量项目升级 / 破坏性变更 |

## 使用方式

Agent 从 orchestrator-template.md 的 mapping 表查当前阶段 → 读对应卡片。
卡片末尾指向下一张卡片。
