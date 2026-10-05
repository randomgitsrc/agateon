# 第 0 批记录（本任务范围之外执行，此处登记痕迹）

> **性质**：**不是**本任务的阶段产物（P0–P8 之外）。批 0 走 **hotfix 通道**——
> 不立项、不建任务目录、直接分支 + PR。**本文件是它在本任务账本里的唯一痕迹**，
> 按 `P0-brief.md` §五 的「待补」项补记。
> **执行日期**：2026-10-04

---

## 1. 为什么批 0 不在本任务的阶段流程里

`P0-brief.md` §二 的范围表把批 0 列为本任务第 0 批（前提列写「无」），
但同一份 brief §四 又写明「第 0 批的 X 项**本就走 hotfix 通道**」、「它走 hotfix 通道、
**在任务阶段之外**」。

⇒ 两处口径并存：**「第 0 批」是内容编号（属本次改造），「hotfix 通道」是执行方式（不归任务管）**。
这是刻意的——批 0 是**修 gate 本身**，而批 1–6 全要**由 gate 来判**；
先修判据、再往上盖，故它必须先于任务主体落地。

**⇒ 读本任务阶段产物时，不要把批 0 当成 P0–P8 的某一步。**

## 2. 产物与落地

| 项 | 值 |
|---|---|
| PR | **#401**（`fix/tag0042-batch0-impl` → main） |
| 合并方式 | 普通 merge（`--no-ff`，符合「release PR 禁止 squash」） |
| 合并提交 | `69d708a`（合并后以 `git log --oneline --grep="#401" main` 取准确值） |
| 版本 | **v0.78.1**（patch；协议语义 / `.state.yaml` schema / 任务数据格式均未变） |
| tag | `v0.78.1`（打在 release 提交上，已随 PR 进 main；G-5 三条判据实测通过） |
| Release | `gh release view v0.78.1`（资产：本体 + 两平台 offline + SHA256SUMS） |
| 已安装 | `~/.agate/v0.78.1`，`agate-resolve.py` 实测解析到该版本 |

**设计文档**：`docs/design-notes/design-tag0042-batch0-defects.md`
（§5 = 验收锚 V1–V11；**§8 = 实现记录**，含设计未预见项的逐条登记，**接手前必读 §8**）

## 3. 九项缺陷的处置

X1、X2、X3、X4、X5、X6、X7、X8、X9 **全部已修并合并**。
逐项缺陷描述、目标行为、实测证据与风险见设计文档 §2 与 §8，本文件不重复。

**四项会改变使用者项目的行为**（已写入 `agate/UPGRADING.md` 的 v0.78.1 章节）：
X1（收尾阶段开始扫 PROD_TOUCHED）、X9（转 READY 须先提交 P8）、
X4（复用声明改用结构化字段 `p5_evidence_reuse`）、X8（软链 hook 也备份）。

## 4. 验收锚（V1–V11）结论

逐条判据见设计 §5；结论：

| 锚 | 结论 |
|---|---|
| V1 X1 所有阶段都扫（任务目录内） | ✅ 行为判据 + 负向控制 |
| V2 X2 从暂存区读 | ✅ 端到端（改前跑 `GATE P4`、改后 `GATE P3`） |
| V3 X3 不再静默假绿（5 个 SKIP 面 + CI 注解） | ✅ 逐面行为判据；**并已把 `gate-backstop` 移出 required checks** |
| V4 X4 三类断言 | ✅ 字段 true/false/缺失三分支 + 3 例误报固化为反例 |
| V5 X5 pipefail 生效 | ✅（含 P3 条件登记：存量 P3 键含管道 = 0） |
| V6 X6 两键分别处理 | ✅ |
| V7 X7 不再返回通过码（两个 site） | ✅（**该用例的 P4 参数曾是空转，已由独立评审查出并修正**，见设计 §8.7） |
| V8 X8 软链也备份（含悬空） | ✅ 悬空软链改前**静默丢失**，改后留备份 |
| V9 X9 卡片 + 机械检查 | ✅ 并据实登记：存量 35 个可判定任务中 **26 个用的是新规则禁止的写法**（设计 §8.4b） |
| V10 存量扫描 | ✅ 四项无未解释转红 |
| V11 全量回归 | ✅ pytest 全绿（排除项为已知环境失败，已在 main 复现）+ consistency 0 ERROR + ruff |

## 5. ⚠️ 提交后续批次前必读：设计未预见的四项

（均已在设计 §8 逐条登记，此处只列指针，避免两处副本漂移）

| # | 内容 | 位置 |
|---|---|---|
| 1 | X7 与两处**既有守护断言**冲突（改测试而非回退代码，附时间线证据） | §8.3 |
| 2 | X7 之后 **P4 不再存在任何合法 exit 2 路径** ⇒ `agate-next` 真暂停分支经真实 gate 不可达 | §8.4 / **DEBT0050** |
| 3 | **X9 的存量面比设计所述更广**（26/35 旧写法；抽样确认 P8 未被裁剪却跳过，且未声明 `internal_only`） | §8.4b |
| 4 | **X4 实现偏离设计**：兜底词表收窄为「粗体独立声明」（设计原打算保留更宽的词表） | §8.6 |

## 6. 本任务尚未解决、且**不在批 0** 的项

- **发布顺序问题（已于 v0.78.2 / v0.78.3 根治，本节的「尚未解决」表述已作废）**：
  `docs/design-notes/design-release-order-boundary.md` 记载「先 PR 后 tag」走不通
  （CHECK 7 需要 tag 已存在）——批 0 当时仍按**方案 C（先推 tag）**执行。
  **根治已落地（外部评审第五方案，登记 RM-AG0098）**：
  （1）CHECK 7 改为**不依赖 tag**（badge ↔ CHANGELOG 最新已发布版本，与 CHECK 13 同源；
  版本无 tag ⇒「发布进行中」PASS+提示）；
  （2）`.github/workflows/release.yml` 新增「Verify tag points to matching commit」步，
  拦「tag 打到无关提交」——**该步已在 v0.78.3 的 Release run 中实际运行并通过**（实测）。
  ⇒ 方案 C 的已知弱点（tag 打错位置无机械判据可察）已消除；发布流程改为**先合 PR、后打 tag**。
  **逐项细节见下文 §8 / §9 与 `CHANGELOG.md` [0.78.3]。**
- 批 1–6 的全部内容（见 `P0-brief.md` §二 范围表）。

## 7. 当前状态

- 本任务 `.state.yaml` 仍为 **phase: P0**；
- **P0 收尾自检已全部勾选**（见 `P0-brief.md` §五）；
- **P0-brief 时效性自检（P0 卡片刻录）**：对照卡片「漂移判据」逐条排查——
  ① `task` 目标方案（agate-config / agate-run / 三态归宿）未变；② `executor_env`（dsh + pytest）
  仍成立；③ `known_risks` 无「虚标已解决」也无被其他任务解决 ⇒ **三条严重漂移均未命中**，
  判定 **无严重漂移**，brief 主体无需重写（`consistency_baseline` 的 398 WARNING 实测仍准）。
- **批 1（统一 phase 语义）具备启动条件**：无前提、且判定它的 gate 现已是 **v0.78.3**
  （含批 0 的 X2/X7/X9 修复 + 外部评审整改 + §6 根治）；
- 何时启动由人决定，本文件不代为推进。

## 8. 外部评审整改（批 0 已发版后的复核，2026-10-05 → v0.78.2）

批 0（v0.78.1）经**外部独立评审**（`review-tag0042-batch0-impl.md`，送审文档见
`docs/reviews/handoff-tag0042-batch0-for-expert-review.md`）复核，确认 **2 MAJOR + 5 MINOR**，
本批逐条修复并固化为回归用例（走 hotfix 通道，不立项）：

| 项 | 级别 | 一句话 |
|---|---|---|
| M-1 | MAJOR | X9 只拦 READY 不拦 DONE ⇒ 可从 DONE 绕过 |
| M-2 | MAJOR | X4 漏判是 **fail-open**（非"朝安全方向失败"）⇒ 补结构性信号 |
| §6 | 悬置 | CHECK 7/13 时序耦合 ⇒ **根治**（CHECK 7 改 tag 无关 + release.yml 补 tag 指向校验），登记 **RM-AG0098** |
| m-1/m-2/m-3/m-5/m-2b | MINOR | 空转测试 / 字段登记 / 三处文案 / 死代码 / 错误提示文案 |

**逐项细节见 `CHANGELOG.md` [0.78.2] 与 `agate/UPGRADING.md` v0.78.2 章节。**

## 9. §6 改动的独立评审整改（v0.78.2 发版后的复核，2026-10-05 → v0.78.3）

v0.78.2 的协议本体 / CI 改动（触发 SELF-GATE）经**独立评审**（`subagent` general，read-only，
对照 `9223262..50ca02f` 全量 diff 并实跑测试）复核，发现 **2 个 Important**（均已由主 Agent
复测证实）+ 若干 Minor：

| 项 | 级别 | 问题（复核结论） | 修法 |
|---|---|---|---|
| **I-1** | Important | M-2 结构信号**召回不足**却被 CHANGELOG 说成全部闭合：初版只经 `extract_evidence_refs`，而该抽取器先剥反引号、只取整组裸路径括号组 ⇒ 反引号/裸引用逃逸（复测 TAG0016/TAG0020 `signal=False`） | 改**原始 PASS 行正则** `P5-test-results/<file>.<ext>`，两路取并集；4 形态 + 2 判别力反例用例 + 改坏即红 |
| **I-2** | Important | §6 后 CHECK 7 已 tag 无关，但 5 处权威文档仍写「badge == tag」（含根 `AGENTS.md` squash 规则理由），会误导下次发布者「先推 tag」 | 逐处改述 + squash 规则改由 G-5 支撑；另修 `scripts/README.md`、`P8-release.md` DEBT0013 时序说明 |
| **m-a** | Minor | §6 新增的 `release.yml` tag 校验步**零测试** | 补静态契约 + **实跑**用例（5 场景） |
| **m-b** | Minor | 该步 `grep\|head\|grep` 链在 `pipefail` 下无 badge 时**丢失友好错误**（复测 stdout 空、只剩 rc=1） | 改 `sed` 抽取 + 实跑用例锁定 |

**教训**：静态契约通过 ≠ 行为正确——I-1/m-b 都是「静态看着对、实跑才暴露」⇒ m-a 用例做成真跑内联脚本。

**逐项细节见 `CHANGELOG.md` [0.78.3] 与 `agate/UPGRADING.md` v0.78.3 章节。**

