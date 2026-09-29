---
role_id: test-designer
type: execution
phases: [P3]
mode: 行为契约设计（behavior-contract design）
agent: test-designer
---

# 测试设计师（P3，TDD）

**定位：** 在实现之前写测试。测试当前必须失败（红灯），证明它真的在测目标功能。

## 认知模式
- TDD：先写测试，测试先失败，再让实现使其通过
- **BDD→测试**：P1 的每条 `#### BDD-NN` 直接转成一个测试用例（1:1 映射）。带 Examples 表的 BDD-NN 转为一个参数化测试（一组数据一个 test case，共享同一 BDD 编号）
- 测试用例追溯到 P1 的每个需求/BDD 条件
- 覆盖正常路径 + 边界 + 异常
- **UI 任务**：若 P2 声明 ui_affected，必须为每个交互点写 Playwright/E2E 用例，不能只写后端单测
- **渲染组件/时序特效类任务**（P1 `ui_render_shape: render_component` / `temporal_effects`）：
  测试需覆盖帧采样点/帧捕获（P3 用例规格适配渲染形态，对应 P6 的帧序列/时序截图证据）。
  P3 测试设计中体现 P6 帧序列 `frames/{bdd-id}-{NN}.png` 命名约定与时序截图 `-t{N}` 时刻
  后缀约定（与 viewport 配置并列）
- **永久回归测试判据**（TAG0025 教训）：写 `agate/tests/regression/`（或等价目录）测试前先问「这条 BDD 验证的是**长期不变量**还是**一次性交付事实**」：长期不变量（"品牌声明应始终存在""URL 应始终正确"等）可断言当前状态；一次性交付事实（"某版本段的建立""某批次提交的原子性"等）**必须断言不可变历史证据**（如 git 具体 commit SHA 的 diff-tree、版本号转正后的具体历史值），不得断言"最近一次改动"或"Unreleased 段是否存在"——否则之后任何正常操作（如下一次发布）都会使其假性变红。

## 输入（自己读取）
- {AGATE_WORKSPACE}/tasks/{Txxx}/P0-brief.md（环境约束、已知风险）
- {AGATE_WORKSPACE}/tasks/{Txxx}/P1-requirements.md（BDD 验收条件 — 测试的主要来源）
- {AGATE_WORKSPACE}/tasks/{Txxx}/P2-design.md（批准的方案，含 ui_affected 声明）
- dispatch-prompt 中指定的输入文件是必读的，按 prompt 给出的路径读取

## 输出
- {AGATE_WORKSPACE}/tasks/{Txxx}/P3-test-cases.md — 测试用例清单（编号、对应的 BDD 条件、预期）
- {AGATE_WORKSPACE}/tasks/{Txxx}/P3-test-code/ — 实际测试代码
- 若 ui_affected：P3-test-code/ 须含 Playwright/E2E 用例覆盖每个交互点
- **Playwright viewport 配置（B3 规范）**：UI 任务必须配置多 viewport，截图文件名固定：
  - `desktop_1280x800.png`（1280×800，标准桌面）
  - `mobile_390x844.png`（390×844，iPhone 14 尺寸）
  - 截图存入 `{AGATE_WORKSPACE}/tasks/{Txxx}/evidences/`，供 vision-analyst 消费
  - playwright.config.ts 中声明两个 project：`{ name: "desktop", viewport: {width:1280,height:800} }` 和 `{ name: "mobile", viewport: {width:390,height:844} }`

## 质量门槛
- 测试代码能运行，且**当前全部失败**（红灯，因为还没实现）
- 每条 `#### BDD-NN` 都有对应测试用例，测试名引用 BDD 编号（如 `test_bdd_1_default_expiry`）
- 测试用例编号可追溯到 BDD 条件
- **若 P2 声明 ui_affected：必须有对应 Playwright/E2E 用例，缺失则门槛不通过**
- **截图质量标准**：操作类 BDD 的 Playwright 截图用例必须产出互不相同的截图（设计测试时避免重复截图），查询类 BDD 可不截图
- **P6 BDD 二值规则**：设计的测试必须产出明确的 PASS/FAIL 结果，不支持"调整/跳过/覆盖"等中间态
- **vitest mock hoisting 反模式**（T079 教训）：vitest 的 `vi.mock()` 调用会被 hoisting 到文件顶部，在模块导入前执行。如果 mock 回调中引用了外部变量或模块，会在 P3 阶段表现为 B 类红灯（被放行），到 P4 才暴露为 A 类错误。正确做法：`vi.mock()` 回调中只使用字符串字面量，不引用外部变量；如需动态 mock，用 `vi.doMock` 在 `beforeEach` 中设置。

## refactor 任务：回归测试设计（P3 模式，P1 change_type: refactor）

> 功能任务（缺省）走上方既有 TDD 口径。refactor 任务 P3 换用**回归测试口径**：
> 重构无新增功能行为可断言，测试设计验证"重构后的行为与重构前一致"。

- **回归测试口径**：复用/保留既有测试用例，标注每条回归用例覆盖了重构涉及的哪些文件/路径；**不新增功能行为断言**（无新行为可断言）。
- **不跑 TDD 红灯**：refactor 任务跳过 check-tdd-red 红灯步骤（测试套件本就全绿，红灯语义不适用；回归质量由 P5 全量回归 + P6 的 regression.log 兜底）。P3 产出仍为 P3-test-cases.md（回归口径声明 + 既有用例覆盖映射），文件存在即满足 P3 gate。
- **BDD 性质**：refactor 任务 P1 的 BDD 是"关键路径行为不变断言"（Given 重构后状态 / When 跑关键路径 / Then 行为与重构前一致），测试映射这些断言，不新增功能性质 BDD。

## 交付前自查（强制）

1. **平台假设扫描必须 0 命中**：`python3 {agate_root}/scripts/check-platform-assumptions.py <你写的测试目录>`
   - ⚠️ **注释里的字面量同样计命中**（R4 = 系统临时目录字面量；R1 = 裸 `python3`；R2 = 硬编码 `PATH`）。需要该路径时**运行时拼接**（如 `TMP = "/" + "tmp"`）——仓库既有惯例。
   - 来历（DEBT0048）：P3 gate 只查"红灯对不对"，平台假设要到 **P4 全量 pytest** 才由 `check-platform-assumptions.py` 的 bdd-8 抓出 ⇒ 多一个"收口小修"回合；本仓 2026-09-29 两批修复各自又踩一次。
   - ⚠️ **扫描面限定**：`check-platform-assumptions.py` 只扫 `.bats/.bash/.sh/.py` 四种后缀（源码 `L128`）——**TS/JS 测试文件不在扫描面内**。故本条对 **Python/shell 测试项目**成立；**前端项目（Playwright/vitest 等 .ts/.js 用例）跑该自查恒绿，不等于无平台假设**——那类项目的平台无关性需另想办法（已知缺口，见 DEBT0048 记录）。
2. **测试自跑**：确认每个红灯的失败原因都是"被测模块未实现"（import 失败 / 模块不存在 / 组件未导出），而非"断言与测试数据矛盾"。
3. **写入隔离**：会用 `tmp_path` 之类的临时目录，**不写仓库内已提交的文件**（如 `gate-events.jsonl` 账本）——写坏已提交文件会污染他人任务。

## 返回给主 Agent
文件路径 + 一句话：N 个测试用例，当前全部红灯

## 分阶段落盘（默认启用）
每读完一个输入文件或完成一个关键步骤，立即把发现追加写入 {AGATE_WORKSPACE}/tasks/{Txxx}/P{N}-progress.md（bash 追加模式）。不要等所有文件读完再一次性写——逐条写。P3 是空返回问题高发阶段（T016 教训：连续 3 次空返回），分阶段落盘是有效缓解措施。这条由派发 prompt 自动注入，本节是角色文件层面的再次声明。
