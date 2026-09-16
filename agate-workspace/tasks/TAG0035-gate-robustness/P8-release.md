---
phase: P8
task_id: TAG0035
parent: P7-consistency.md
trace_id: TAG0035-P8-20260916
agent: implementer
type: release
created: '2026-09-16'
status: draft
bump_type: patch
debt_check: reviewed
---

# P8-release — TAG0035 gate 健壮性批

`[PROD_NOT_TOUCHED]`

> 本文件由 releaser subagent（implementer P8 模式）产出。**不执行 git commit/tag，不直接编辑
> README.md/CHANGELOG.md/agate-workspace/roadmap/roadmap.md/agate-workspace/debt/tech-debt.md/
> agate/UPGRADING.md**——以下各节只给出「主 Agent gate 验证通过后可直接采用」的文本/清单，
> 实际文件编辑由主 Agent 亲自执行。

## 1. bump_type 判定

`bump_type: patch`（v0.71.0 → v0.71.1）

**核实过程**：逐条读了 `P1-requirements.md` 的 14 条 BDD 标题（BDD-1～BDD-14），归类如下：

| 子批 | BDD | 性质 |
|---|---|---|
| A | BDD-1/2/3 | 未知阶段 fail-open → fail-closed（判据修复） |
| B | BDD-4/5/6/7 | 三处数字序号假设致非数字阶段名静默失效 → 显式报错/WARNING（判据修复） |
| C | BDD-8/9/10 | `_gate_p4` 完整度判据过窄 → 放宽为"历史 commit 曾含代码即放行"（判据修复，DEBT0037） |
| D | BDD-11/12/13/14 | judge 黑白名单 3 处假阳性 → 修正（判据修复，DEBT0038） |

14 条无一条属于"新增功能/新增对外可见能力"——全部是"原本会静默通过/静默失效/误判"的判据，改为
"正确报错/正确放行/正确拦截"。且 P2-design.md §1.2「不改什么」已逐条核实：
- `handlers` 字典分发结构不变、`phases.yaml` schema 不变、`ci-gate-backstop.py`/`agate-next.py`
  消费退出码的逻辑本身不变（只是被消费的退出码数值从错误值变为正确值）；
- 三处子批 B 修复均为"对不合规输入（非数字阶段名）新增报错"，不改变合规调用方（标准数字阶段名/
  已知阶段/真实自述场景）的既有行为——P6-acceptance.md BDD-3/BDD-7 已用全量三分片测试
  （1634 passed, 0 failed）实证标准路径零回归；
- 判据放宽（子批 C）只扩大"允许推进"的场景范围，且 BDD-10 红灯边界证明"纯文档、无代码历史"场景
  仍 `return 1`，拦截力未削弱；
- 黑白名单修复（子批 D）只消除 3 处假阳性，BDD-14 证明真实自述场景仍正确拦截。

**结论**：符合"修 bug / 不改 API 行为 → patch"的判据口径，判定为 **patch**（v0.71.0 → v0.71.1）。
未发现需要改判为 minor/major 的依据。

## 2. debt_check

`debt_check: reviewed`

### DEBT0037（check-gate.py P4 完整度判据）

closure_criteria 逐条核对：

| # | closure_criteria | 结果 | 证据 |
|---|---|---|---|
| 1 | check-gate.py P4 对「阶段工作已 commit、暂存区空」场景不再 exit 1（多提交阶段 + 回退后推进两个回归用例） | **满足** | `P4-implementation-C.md`（新增 `_gate_p4_has_prior_code_commit`）+ `P6-acceptance.md` BDD-8（多提交场景 PASS）/ BDD-9（回退后修复场景 PASS） |
| 2 | agate-next.py 在该场景正常推进 P4→P5，无需手动 `_advance` | **满足（设计推导 + 退出码契约验证，非直接 agate-next.py CLI 集成测试）** | `P2-design.md` §1.2 已用 grep 核实 `agate-next.py` 消费 `check-gate.py` 退出码的逻辑本身是纯粹的"exit 0 即推进"判断、不特判具体数值、未被本批修改；`gate_p4` 在 BDD-8/9 场景下退出码已从错误的 1 改为正确的 0（实测证据同上）。**注**：全仓搜索确认 `agate/tests/unit/test_tag0027_b1_agate_next_cli.py` 无 TAG0035 相关新增用例——本条满足性基于"退出码契约不变 + gate_p4 退出码已被证明修正"的逻辑链条，未见到一次真实 `agate-next.py P4→P5` 端到端 CLI 调用的新增回归测试。建议 P8 gate/READY 收尾阶段如有余力可补一次手工验证，非阻断项 |
| 3 | P4 之外的 phase 完整度判据已同类核查，结论落盘 | **满足** | `P2-design.md` §1.2「不改什么」已明确记录：`gate_p0~gate_p3/gate_p5~gate_p65/gate_p7` 均不使用暂存区快照类判据（P1 同类扫描已核实），结论已落盘在设计文档 |
| 4 | 全量 pytest 全绿 + consistency 0 ERROR | **满足** | `P6-acceptance.md`：1634 passed, 2 skipped, 0 failed；`P4-implementation-D.md`：`check-protocol-consistency.py --strict-errors-only` exit 0，0 ERROR |

### DEBT0038（check-judge-verdict.py 黑/白名单假阳性）

closure_criteria 逐条核对：

| # | closure_criteria | 结果 | 证据 |
|---|---|---|---|
| 1 | check-judge-verdict.py 对「dispatch-context 引用 agate/phase-cards/P6-acceptance.md」不再假阳性（回归用例） | **满足** | `P6-acceptance.md` BDD-11（两个参数化子场景：p6-acceptance.md / p4-implementation.md，均 PASS） |
| 2 | 角色定义文件路径 + P6-evidence/ 目录裸文件名两类引用不再被白名单拦截，或派发模板/P6 卡片显式写明 P6.5 例外惯例 | **满足** | BDD-12（角色文件路径，两个参数化子场景 PASS）+ BDD-13（P6-evidence 裸文件名 PASS） |
| 3 | dispatch-protocol.md「Judge 信息隔离」节说明 P6.5 dispatch-context 的输入文件惯例 | **满足** | 已核实 `agate/dispatch-protocol.md:404` 白名单输入段落已补"角色定义文件路径（`execution-roles/`、`review-roles/` 目录前缀）不受此白名单限制，任意角色文件路径均视为合法引用"；`agate/phase-cards/P6-acceptance.md`（P6.5 流程条目行）已补"含角色定义文件路径豁免，见 dispatch-protocol.md「Judge 信息隔离」节" |
| 4 | 全量 pytest 全绿 + consistency 0 ERROR | **满足** | 同上（DEBT0037 表格第 4 条同一份证据） |

### 结论

**两条 DEBT 的 closure_criteria 已满足，建议状态改为 closed。** DEBT0037 的第 2 条为"设计推导 + 退出码
契约验证"而非直接端到端 CLI 集成测试，建议主 Agent 在 closed 备注中如实注明这一点（与本任务其余
closure 证据的一贯做法一致——本仓库历史 DEBT closure 备注多次采用类似"非直接实测，基于代码路径核实"
的诚实表述，如 DEBT0014/DEBT0015 的先例），不构成阻断关闭的理由。

## 3. CHANGELOG.md 新版本条目文本（可直接复制进 `## [Unreleased]` 位置）

```markdown
## [0.71.1] - 2026-09-16

### 修复（TAG0035：gate 健壮性批，RM-AG0062）

- **`check-gate.py` 未知阶段 fail-closed**：`handlers.get(phase) is None` 分支退出码从
  `sys.exit(2)`（与 P8 等已知阶段"通过"码相同）改为 `sys.exit(1)`——新增阶段若忘记注册 gate
  函数不再被 `ci-gate-backstop.py` 误判为"一致通过"，而是响亮失败。
- **三处非数字阶段名静默失效修复**（`check-gate.py` 回退抵达检测 / `check-state-transition.py`
  `phase_num()` / `pre-commit-gate.py` 一致性 WARNING）：非数字阶段名（如自定义阶段名）此前会
  被 `re.search(r"[0-9]+", ...)` 无匹配静默短路或映射为 `0`，现改为显式报错（`sys.exit(1)`）
  或输出 WARNING 提示；标准 P0-P8 数字阶段名行为不变。
- **`_gate_p4` 完整度判据放宽（DEBT0037）**：判据从"当前暂存区含非 md/yaml 代码文件"放宽为
  "本 phase 任一历史 commit（`wf(<task_id>-P4)` 标签）曾引入过代码 diff"——修复"一个 P4 阶段
  跨多个 commit 交付"与"P5→P4 回退后修复 commit"两个场景被误判 `exit 1`、`agate-next.py` 拒绝
  推进、需主 Agent 手动 `_advance` 的问题；纯文档且无代码历史的场景仍正确拦截。
- **`check-judge-verdict.py` 信息隔离黑/白名单 3 处假阳性修复（DEBT0038）**：黑名单
  `p6-acceptance.md` 等 basename 子串命中协议阶段卡片路径引用（如
  `agate/phase-cards/P6-acceptance.md`）时新增路径豁免；白名单补齐角色定义文件路径
  （`execution-roles/`、`review-roles/` 目录前缀）；`P6-evidence/` 目录下真实存在的裸文件名
  引用不再被误报"白名单外"。真实自述场景（无路径前缀直接引用任务自己的 `P6-acceptance.md`）
  仍正确拦截。

来源：TAG0035（RM-AG0062，DEBT0037/DEBT0038 归并修复批）。
```

## 4. README.md / README.zh-CN.md 版本徽章更新

两文件改法完全一致：

| 文件 | 行号 | 旧值 | 新值 |
|---|---|---|---|
| `README.md` | 第 12 行 | `[![version](https://img.shields.io/badge/version-v0.71.0-blue)](https://github.com/randomgitsrc/agateon)` | `[![version](https://img.shields.io/badge/version-v0.71.1-blue)](https://github.com/randomgitsrc/agateon)` |
| `README.zh-CN.md` | 第 12 行 | `[![version](https://img.shields.io/badge/version-v0.71.0-blue)](https://github.com/randomgitsrc/agateon)` | `[![version](https://img.shields.io/badge/version-v0.71.1-blue)](https://github.com/randomgitsrc/agateon)` |

仅 badge 中的版本号字符串 `v0.71.0` → `v0.71.1` 一处改动，其余徽章（license 等，第 13 行）不动。

## 5. roadmap.md（RM-AG0062）状态回写确认

已读 `agate-workspace/roadmap/roadmap.md` 第 70 行：`RM-AG0062` 当前「状态」列为 `scheduled`，
「关联任务」列已是 `TAG0035`。**确认**：本任务 P8 gate（RM-AG0043 硬校验）要求主 Agent 在本任务
完成后将该行「状态」列回写为 `done`。不需要 releaser 自己编辑该文件，由主 Agent 执行。

（补充：第 72 行 `RM-AG0064` 已于 2026-09-16 标记 `cancelled` 并注明"已并入 RM-AG0062"，本次不
涉及该行改动，仅供交叉核对。）

## 6. UPGRADING.md 新版本条目文本草稿（参照 §3 现有条目风格，尤其 v0.67.2 TAG0031 写法）

```markdown
### v0.71.1 — gate 健壮性批（TAG0035：DEBT0037/0038 修复 + RM-AG0062）

> **本版本无破坏性变更，零迁移动作**——未改 `.state.yaml` schema / 既有任务文件格式 /
> 3 个 hook 薄壳（本任务改动清单无 `.sh` 改动），无需重跑 `install-hook.py`（软链布局
> `git pull` 即生效；Windows 复制模式重跑 SETUP.md 步骤 2 的 `cp`）。

1. **未知阶段 fail-closed——对合规调用零影响**：`check-gate.py` 收到"未注册 gate 函数"的
   阶段名时退出码从 `2`（误与已知阶段"通过"码相同）改为 `1`（fail-closed）。标准 P0-P8 十个
   已知阶段的判定路径完全不变，只影响此前会被静默误判为"通过"的未知/拼写错误阶段名场景。
2. **三处非数字阶段名判据修复——对合规调用零影响**：`check-gate.py` 回退检测 /
   `check-state-transition.py` `phase_num()` / `pre-commit-gate.py` 一致性 WARNING 三处，此前
   遇到非数字阶段名会静默短路或映射为 `0`，现改为显式报错或 WARNING 提示。标准数字阶段名
   （P0-P8）的解析与判定结果逐字节不变（回归测试 BDD-7 已验证）。
3. **`_gate_p4` 完整度判据放宽（DEBT0037）——只放宽真实存在代码交付证据的场景**：判据从
   "当前暂存区快照"放宽为"本 phase 历史 commit 曾真实引入过代码 diff"，修复多提交 P4 阶段 /
   P5→P4 回退后修复 commit 被误拦截、需主 Agent 手动 `_advance` 的问题。纯文档且无代码历史的
   场景仍按原判据拦截（`return 1`），拦截力未削弱。
4. **judge 信息隔离黑/白名单 3 处假阳性修复（DEBT0038）——只消除误判，不放宽真实自述场景**：
   `check-judge-verdict.py` 修正协议阶段卡片路径引用误判入黑名单、角色定义文件路径误判为
   白名单外、`P6-evidence/` 目录裸文件名误报三处问题；`dispatch-protocol.md`/
   `agate/phase-cards/P6-acceptance.md` 同步补充说明。真实自述违规场景（无路径前缀直接引用
   任务自己的产出文件）仍正确拦截（回归红灯用例锁定）。
5. **升级动作**：`git pull` 即完成；无迁移动作。
```

## 7. 临时资源清单

无临时资源。本任务全程无启动临时服务/进程、无创建临时数据库/数据目录、无开发安装
（editable install / 全局包安装）。全部改动为 `agate/scripts/*.py` 判据修复 + 对应 pytest 用例 +
两处协议文档同步，验证手段是本地 pytest + git 只读命令（`git log --grep` / `git diff-tree`），
不产生任何需要 READY 收尾清理的残留。

## 8. P5 验证复用确认 + per-package 发布检查命令说明

- **P5 复用**：主 Agent 已跑 `check-p6-provenance.py --audit7-only` 确认
  `AUDIT7_RESULT: reuse_allowed`（P5 通过点到当前无非任务工作区文件改动），复用现有
  `P5-test-results/`，本次不重新执行全量测试命令。
- **per-package 发布检查命令**：`P2-design.md` frontmatter 声明 `packages: [agate-scripts,
  agate-tests, agate-docs]`。三者均属同一 Agateon 协议仓库（本仓库无独立打包/发布的多包结构，
  不是 npm workspaces / monorepo 多包场景），**没有各自独立的 per-package build/test 命令**——
  统一走 `P2-design.md` §4 `gate_commands` 声明的仓库级命令（`pytest agate/tests/unit|regression|
  integration/` 三分片 + `check-protocol-consistency.py --strict-errors-only` + `shellcheck` +
  `count-tests.sh`），已在 P5/P6 阶段跑过（详见上一条"P5 复用"）。不虚构不存在的
  per-package 命令去跑，如实说明"协议本体单包，三个 packages 标签只是产出分类，非独立发布单元"。

## Lessons Learned

1. **【流程】判据"放宽"类修复必须同时提供红灯边界回归测试**：DEBT0037 的 `_gate_p4` 放宽如果
   只验证"应放行的场景放行"（BDD-8/9），不验证"不该放行的场景仍拦截"（BDD-10），放宽本身就
   可能演变成新的健壮性漏洞。本任务 P2 设计阶段就把 BDD-10 列为"红灯边界"强制项，是值得沿用
   的模式——判据放宽类任务的 P1/P2 设计必须显式包含"这次放宽不能失守的边界"BDD。
2. **【架构】三处"看似同根"的静默失效点（子批 B 的三个文件）不应共用一个抽象**：P2-design.md
   候选方案对比显式论证了"统一 `parse_phase_num_or_fail` 共享函数"反而因三处消费语义不同
   （early-exit / 主流程判定 / WARNING 不阻断）而无法真正统一，选择三处独立实现。这是"防止
   虚假复用"的一个好案例，值得在后续遇到类似"表面同构、语义不同"的多处修复时参考。
3. **【测试】closure_criteria 中"下游消费方行为验证"条目容易被"改动源头即视为已验证"带过**：
   核对 DEBT0037 时发现 closure_criteria 第 2 条（`agate-next.py` 正常推进）没有对应的直接
   端到端集成测试，只能靠"退出码契约不变 + 源头判据已修正"的逻辑链条推导满足。建议未来涉及
   "上游 gate 脚本判据修复 + 下游消费脚本按退出码推进"这类跨脚本因果链的 DEBT，P3 阶段应显式
   为下游消费方也设计至少一条端到端回归用例，而不是只测上游。

## 产出文件字段核对（供 gate 检查）

- `bump_type: patch`
- `debt_check: reviewed`
- 版本号变更确认：由主 Agent 依第 4 节完成 README/README.zh-CN badge 修改（version 文件面即
  README badge，本仓库无独立 `VERSION`/`package.json` version 字段）
- CHANGELOG `[Unreleased]` → `[0.71.1]`：由主 Agent 依第 3 节文本采用
- 临时资源清单：无（见第 7 节）
