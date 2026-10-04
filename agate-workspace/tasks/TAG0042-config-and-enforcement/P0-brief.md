# P0-brief — TAG0042 项目形态命令化 + 规则脚本化（160 项义务的归宿）

> 主 Agent 亲自填写（P0 产出）。
> **来源**：外部设计分析 `analysis-declare-and-enforce.md`（经 R1–R4 四轮独立评审，最终 APPROVE）。
> **性质**：**协议架构演进**——引入声明层（`agate-config`）与执行层（`agate-run`），
> 并把 160 项阶段义务逐项归入「脚本执行 / 命令生成 / 强制评审」三态之一。
> **范围声明**：**本任务只改 agateon 本仓**。peekview 等其他项目的声明与 CI 接入**不在本任务范围**
> （原设计 §7 第 4 批的前提"两仓声明都已合入"对本任务不适用——agateon 侧做到位即可）。

```yaml
task: "项目形态由命令声明（agate-config，不写死技术栈），规则由脚本在不可绕开的路径上执行（agate-run / 关卡层分级 / agate-ci-verify），并把 160 项阶段义务逐项归入三态归宿（脚本执行 / 命令生成 / 强制评审），用 rules/obligations.yaml 防止「靠记忆的规则」再长出来"
known_risks:
  - "🔴 规模远超常规任务：原设计分 7 批（0-6），新增 4 个命令 + 1 张登记表 + 1 个声明文件 + 新证据格式；须分批判推进，每批独立 gate"
  - "🔴 第 4 批（P8 改为交付收尾）会删除协议里的发版逻辑，消费方散布多处：check-structure-consistency.py:64-65、check-protocol-consistency.py:568、analyst.md、复盘模板、phases.yaml 的 task_fields、frontmatter schema —— 未全量 grep 前不得动手"
  - "🔴 phase 语义统一（第 1 批）会改变 agate-next 行为：现行为「预先写入下一阶段」，目标为「不预写」，须同步改卡片描述；peekview T085 的 8 次 --no-verify 正是该冲突所致"
  - "同类/影响面预判（现状实测）：160 项阶段义务中仅 38 项（24%）由脚本在不可绕开路径执行，70 项（44%）无任何脚本；P8 与 READY/DONE 收尾的 25 项中真正生效的脚本强制为 0"
  - "同类/影响面预判（记忆失效实测）：agateon 38 个 READY/DONE 任务中仅 16 个曾以 phase:P8 提交（另 22 个的 P8 gate 从未运行）；task-session-summary.md 现存 0 份；约 102 个经过 P3 的任务中仅 1 个有 pre-task-baseline.md"
  - "第 0 批的 9 项（X1-X9）是「现在就是错的」：X1 READY/DONE 跳过 PROD_TOUCHED 扫描（安全门失效）、X3 ci-gate-backstop 永远 SKIP 却显示绿（假绿）、X5 执行命令未开 pipefail（吞退出码，TAG0016 已发生）—— 已逐条实测确认"
  - "迁移兼容：第 2 批起须遵守「文件缺失时行为与现状一致 + WARNING，到截止版本改 exit 1」，截止版本写入 UPGRADING；存量任务无 base_rev 的迁移方案见原设计 §2.3"
  - "平台无关硬约束：agate-run 沿用 agate_common 用 bash 执行命令的既有假设，Windows（MSYS2）下 pipefail 与 checkout-index 的表现未测"
  - "本任务改 agate/ 协议本体与脚本 ⇒ 每批均触发 SELF-GATE，须独立评审 + self-gate-review 留痕"
env_constraints:
  debug_env: "无独立 debug 环境；验证＝本 checkout 内 pytest 全量 + 对 agate-workspace/tasks 存量任务全量回归对账 + 每批的 R6 双向差分（**必须在 /tmp 副本上跑**，AGENTS.md 工作流 0a）"
  platform: "dsh"
  network: "full"
  consistency_baseline: "0 ERROR / 398 WARNING（其中 386 条来自冻结文件，已聚合为 1 行显示）"
```

---

## 一、为什么立这个项（问题陈述）

**两条所有者要求**（外部设计分析的出发点）：

1. **项目形态必须由项目声明**，协议不写死任何技术栈——现行协议里 P8（版本/CHANGELOG/tag）、
   P3/P5（pytest 一族）、hook/git 层都有硬编码假设，对「产品就是 md 的 agateon」和
   「用 GitLab + Go + Helm 的项目」都不成立。
2. **规则不能靠 Agent 的记忆**——设计分析给出了**可查证**的失效证据（见 `known_risks` 的实测行）。

**现状量化**（设计分析 §1，我抽查核对了关键数字）：

| 段 | 义务数 | 由脚本强制（M） | 需记得调用（C） | 无任何脚本（N） |
|---|---|---|---|---|
| P0–P2 | 48 | 6 | 3 | 22 |
| P3–P5 | 40 | 9 | 6 | 21 |
| P6–P8、收尾、横切 | 72 | 23 | 20 | 27 |
| **合计** | **160** | **38（24%）** | **29** | **70（44%）** |

且**那 38 项也挂在四个会被遗忘的前提上**：已装 hook / 已暂存 `.state.yaml` / 未用 `--no-verify` /
phase 不是 READY·DONE·PAUSED。

---

## 二、任务范围（分批，每批独立 gate）

| 批 | 内容 | 前提 |
|---|---|---|
| **0** | §5 的 X1、X3–X9（X9 只改卡片）；X2 的「phase 从暂存区读取」部分 | **无**——改动小、都是已实测的缺陷 |
| **1** | 统一 phase 语义：改 `agate-next` + 同步卡片描述 | 无 |
| **2** | `agate-config`（全部子命令）+ schema + 唯一读取函数 + 等价守护；`agate-setup`/`install-hook` 自动 `init`；gate_p0 调 `validate`（迁移期只 WARNING） | 文件缺失时行为不变 + WARNING；截止版本写 UPGRADING |
| **3** | `agate-run`（含 `--baseline`、环境变量注入、`.out` 证据 + ignore 检查）+ `cmd_run` 事件 + hook 一并暂存账本；修正 formatter 计数 | 第 2 批完成 |
| **4** | 关卡层按提交类型分级 + 转换表（含 `paused_from`）；P8 改为交付收尾，`delivery` 必须声明 | 第 3 批完成 **且** 消费方全量 grep 完成 |
| **5** | `agate-ci-verify` + `agate-doctor`；替换 `ci-gate-backstop` | 第 4 批完成 |
| **6** | `rules/obligations.yaml` + `check-obligations`；剩余 122 项义务逐项决定去向；§4 的通用化清理 | 第 2 批完成 |

**每批合并前必须满足**（原设计 §7）：
- **双向 R6 差分只在副本上跑**（`AGENTS.md` 工作流 0a，本任务立项当天刚加入）；
- 不出现「只适用于某一个项目」的规则；
- 从第 6 批起，义务登记表的 M 类占比**不得下降**。

---

## 三、明确不做（边界）

- **不改 peekview**（或其他项目）的声明、CI、hook——本任务只管 agateon 本仓；
- **不为「判断类义务」强行脚本化**——那些交给**由脚本强制必须出现**的独立评审；
- **不做「一次交付覆盖哪些任务」的协议定义**——交付单元与任务不一一对应属具体交付形态；
- **原设计 §10 已撤回的 5 条意见不再复活**（不声明就不检查 / READY 时检查交付事实 /
  `git_head` 绑定证据 / `paths.code` 沿用现行默认 / 协议层检查 tag）。

---

## 四、与既有登记的关系

- **RM-AG0079**「协议缺『轻量改动通道』」——本任务**不解决**它，但第 0 批的 X 项本就走 hotfix 通道，
  可作其实证素材；
- **DEBT 侧**：X1/X3/X5 已在设计分析中定性为「现在就是错的」，第 0 批修完后应核对是否有关联债务条目需关闭；
- **本任务的 P0-brief 即立项登记**；roadmap 回写 `done` 属 P8 硬校验（RM-AG0043），届时按流程补。

---

## 五、P0 收尾自检

- [x] 任务目录 + `.state.yaml`（phase: P0）+ 空账本
- [x] P0-brief 四字段齐全（`task:` / `known_risks:` / `env_constraints:` 行首键 + 正文）
- [x] 来源可追溯：外部设计分析经 R1–R4 评审 APPROVE；关键数字已抽查复核
- [x] 范围边界明示（只做 agateon）
- [ ] **待确认**：是否先单独走第 0 批（X1/X3/X5 是真漏洞），再启动第 1–6 批
