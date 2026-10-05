# 独立评审记录：TAG0042 批 0 §6 改动（v0.78.2 → v0.78.3）

> 本文是 v0.78.2 的协议本体 / CI 改动的 **SELF-GATE 独立评审**记录，供 `self-gate-review:` 留痕。
> 评审对象 = PR #404（合并 commit `37a04d0`）中的两个提交 `9223262..50ca02f`。

## 评审范围

```bash
git diff --stat 9223262..50ca02f   # 19 files, +501 / -40
```

触发面：`agate/` 协议本体（check-*.py / phases.yaml / 卡片 / ADR）+ `.github/workflows/release.yml`
+ `protocol-tests.yml`。

## 评审方式

- **独立 subagent**（`general`，read-only），不共享主会话上下文——只给 diff 范围与需求文档。
- 强制**实跑复核**（非仅阅读）：构造反例、跑相关测试套件、读真实任务数据；`git status --porcelain` 留空。
- 评审产出见本文件「发现」。

## 发现（2 Important + 若干 Minor）

| 项 | 级别 | 复核结论（均已由主 Agent 复测证实） | 处置 |
|---|---|---|---|
| **I-1** | Important | v0.78.2 的 M-2「结构性信号」**召回不足却被 CHANGELOG 说成全部闭合**：初版只经 `extract_evidence_refs`，该抽取器先剥反引号、只取整组裸路径括号组 ⇒ 反引号/裸引用逃逸（复测 TAG0016/TAG0020 `signal=False`）——fail-open 残留 | 改**原始 PASS 行正则** `P5-test-results/<file>.<ext>`，两路取并集；4 形态 + 2 判别力反例用例 + 改坏即红复验 |
| **I-2** | Important | §6 后 CHECK 7 已 tag 无关，但 **5 处权威文档仍写「badge == tag」**（含根 `AGENTS.md` squash 规则理由、`git-integration.md`、`adr.md`）——会误导下次发布者「先推 tag」 | 逐处改述 + squash 规则改由 G-5 支撑；另修 `scripts/README.md`、`P8-release.md` DEBT0013 时序说明 |
| **m-a** | Minor | §6 新增的 `release.yml` tag 校验步**零测试** | 补静态契约 + **实跑**用例（5 场景） |
| **m-b** | Minor | 该步 `grep\|head\|grep` 链在 `pipefail` 下无 badge 时**丢失友好错误**（复测 stdout 空、只剩 rc=1） | 改 `sed` 抽取 + 实跑用例锁定 |

### 评审未采纳 / 降级项

- **m-c**（`false` + PASS 引用 P5 可过度阻断）：方向 fail-closed，无存量任务命中，暂不改，留批 1 观察。
- **m-d/m-e/m-f**：均为**既有**行为或 §6 设计的固有取舍（tag 无关后「badge 回退到旧 tag 之下」不再拦），
  已在 CHANGELOG/设计文档如实标注，不属本次引进的缺陷。
- **`site/blog/20260828/post-01-evidence-ladder.md`**（中英双版）用 CHECK 7 作「证据阶梯」的**举例**，
  描述的是**发布时**的机制（`git describe --tags`）。属**已发布内容**，改动是内容决策而非机械纠漂，
  **本次不改**，上报用户。

## 复核证据

- 主 Agent 对 I-1：全仓 P6 普查命中 9 处**全为真引用**；反例（TAG0020 BDD-4 仅目录名、TAG0033/TAG0019 否定式）不误伤；改坏即红（禁用原始行正则 ⇒ 恰 3 形态用例变红）。
- 主 Agent 对 m-b：恢复旧 `grep` 链 ⇒ no-badge 用例变红（stdout 空）；`sed` 版 5 场景全绿。
- 全量：unit+regression+integration `2597 passed / 2 skipped`（deselect 1 个 opencode CLI 环境失败，未触碰该文件）；`ruff` clean；consistency 0 ERROR；structure S0-S6 OK；count-tests 2622。

## 结论

**评审通过（含整改）**：v0.78.2 的两提交修复了真实缺陷、未引入新 fail-open；评审另外发现并推动了
I-1/I-2 两项 Important 整改，随 **v0.78.3** 发布。
