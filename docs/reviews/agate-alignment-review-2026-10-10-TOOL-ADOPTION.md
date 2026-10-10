---
review_date: 2026-10-10
reviewer: protocol-alignment-review
change_summary: 命令采纳审计 + 三处孤儿工具接线（agate-run 新增任务源 / agate-advance 与 agate-md-field-set-gate-commands 文档接线；strip_paired_quotes 提为 agate_common 单源）
files_changed: [CHANGELOG.md, agate/phase-cards/P2-design.md, agate/phase-cards/P5-verification.md, agate/scripts/agate-read-p5-commands.py, agate/scripts/agate-run.py, agate/scripts/agate_common.py, agate/state-machine.md, agate/tests/unit/test_agate_run.py]
---

# 协议-脚本对齐审查

> 分支 `hotfix/wire-orphan-tools`（未提交，工作区）。审查只读；写类动作（全量 pytest / consistency / ruff / 手工实跑）一律在
> `/tmp/opencode/tooladopt-repo`（`rsync` 副本，含 `.git` 与全部未提交改动）与 `/tmp/opencode/tooladopt-scratch` 上执行。
> 原仓 `git status` 未被本次审查改动（见文末自核验）。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | ALIGNED |
| A2 | 脚本→文档对齐 | **MISALIGNED**（`agate/scripts/README.md:182` + `agate-run.py` 模块 docstring 未随新任务源同步） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED**（A3b：README/docstring 未列；verifier.md 等为可选） |
| A4 | 测试覆盖 | ALIGNED（附全量实跑：1 failed〔环境性〕/ 2912 passed / 3 skipped） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | ALIGNED（经实测无既有用例因本次变更转红；无需更新夹具） |
| A5 | 下游影响 + 文档传播 | NEEDS_HUMAN_REVIEW（无破坏性变更、CHANGELOG 已记；传播面 README 见 A2，verifier.md/`project-map` 为可选） |
| A6 | 锚点表覆盖 | ALIGNED（未改 `check-*.py`、未新增脚本） |
| A7 | 设计原则一致性 | ALIGNED（符合 ADR-014 判据单源） |
| A8 | 声称-命令绑定 | NEEDS_HUMAN_REVIEW（「完全孤儿」标签与空格形态提及相抵；「改为」措辞偏强） |

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

三处新接线逐条对脚本行为核验，均一致：

**① P5 卡执行入口**（`agate/phase-cards/P5-verification.md:38-42`）：
> **执行入口（推荐，RM-AG0102 采纳）**：`python3 {agate_root}/scripts/agate-run.py --task <TASK_DIR> "<命令>"`。
> 它按 **P2 的 `gate_commands` 白名单**执行（未声明命令**拒绝执行**）、把输出写
> `<TASK_DIR>/runs/<k>.log`（**证据入库**）并追加账本事件 `cmd_run`……退出码**如实传播**（POSIX 开 pipefail…）

对应实现（`agate/scripts/agate-run.py`）：
- 白名单拒绝：`_resolve_from_task`（:69-101）未命中 → `(None,-1)`；`main`（:313-320）→ `return 1`，stderr 列出两处来源。
- 写 `runs/<k>.log` + 账本：`_run_with_task`（:273-289）→ `_write_run_log`（:248-270）+ `_record_cmd_run`（:206-227，`append_event` 唯一写路径）。
- pipefail 如实传播：`_run_command`（:115-142）`"set -o pipefail; " + cmd` + `executable="bash"`。

**② state-machine 回退机制**（`agate/state-machine.md:679-683`）：
> `agate-advance.py [TASK_DIR] [--to <phase>] [--reason <text>]` —— **人工回退/跳转的引导入口**：不传 `--to` 打印…转移表建议；`--to` 时…（**diff≥2 会提示「须先 PAUSED」**），diff=1 等价**委托** `agate-retreat-to.py`……它**不内联回退实现**，只做解析 + 提示 + 委托

对应 `agate-advance.py`：不传 `--to` → `_print_table`（:166-168）；`diff>=2` → PAUSED 提示（:180-188）；`diff==1` → 委托 `agate-retreat-to.py`（:190-214）。逐条一致。

**③ P2 卡写入工具**（`agate/phase-cards/P2-design.md:173-177`）：
> 逐 key 用 `agate_common.is_legal_gate_key()` 校验（与 `check-gate.py::_reconcile_p2_fields` **同一函数**，非重写）

核验：`agate-md-field-set-gate-commands.py:107` 调 `agate_common.is_legal_gate_key(key, phase_ids)`；`check-gate.py:1012`（`_reconcile_p2_fields` 内）调同一 `is_legal_gate_key`（:86 从 `agate_common` import）。同一函数，属实。

**结论**：ALIGNED。
**次要观察（不判 MISALIGNED）**：P5 卡代码块（:46-48）用**裸** `agate-run.py --task …`（无 `python3 {agate_root}/scripts/` 前缀），与本仓“脚本经 `python3 <root>/scripts/x.py` 调用”惯例及本卡上文（:38）的完整路径形不一致；读者若照抄裸名可能因不在 PATH 失败。另：卡未提 `runs/**` 若被 `.gitignore` 覆盖时 `agate-run` 返回 1（脚本 :279-285 会给出取反规则提示）——实际使用可能遇到的摩擦未在卡中预告。

### A2: 脚本→文档对齐 — MISALIGNED

**差异 1（本次改动引入）**——`agate/scripts/README.md:182` 的 `agate-run.py` 索引行仍只写单一命令源：
> 执行层：在不可绕开路径上执行声明 `verify.commands` 中的验证命令（`agate-run [--baseline] [--task <TASK_DIR>] <命令>`）。…

新增任务源后，`--task` 时命令还可来自任务 `P2-design.md` 的 `gate_commands`。该行（HEAD 版）已在 batch D 补过 `--task` 日志描述，**本次未随之补新命令源**——属**本次改动引入**的脚本→文档不同步。读者据 README 不会知道任务源存在，削弱「采纳」目标。

**差异 2（部分为既有欠账）**——`agate/scripts/agate-run.py` 模块 docstring（:2-21）：
> `* BDD-9  从 `agate.config.yaml` 的 `verify.commands` 取命令…`（:5）
> `命令解析：CLI 实参须**精确匹配** `verify.commands` 中的一条…`（:15）
> `证据槽位：证据文件按命令在 `verify.commands` 中的**下标**命名…`（:16）

该 docstring 既未提 `--task`（batch D 引入，早于本 diff 即已欠账），也未提本次新增的任务源。新函数 `_resolve_from_task` 自带 docstring 记录了口径，但模块头未同步。

**建议**：① README :182 改为「声明 `verify.commands`（或 `--task` 时该任务 `P2-design.md` 的 `gate_commands`）中的验证命令」；② `agate-run.py` 模块 docstring :5/:15/:16 补一句「`--task` 时命令另可来自任务 `P2-design.md` 的 `gate_commands`；该路径证据写 `runs/<k>.log`（不落 `.out` 槽位）」。均为一两行改动。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（已知衍生改动）**——均已随实现更新：
- `CHANGELOG.md:188-200` 新增条目 ✅
- `agate/tests/unit/test_agate_run.py:472-507` 新增用例 ✅
- `agate-read-p5-commands.py:18-19` 改 import 共享函数 ✅

**A3b（主动推断的“应被影响但未列 diff”文件）**——逐一验证：

| 推断文件 | 是否应受影响 | 实况 |
|---|---|---|
| `agate/scripts/README.md`（:182 agate-run 行） | **是** | **未改 → MISALIGNED**（同 A2 差异 1） |
| `agate/scripts/agate-run.py` 模块 docstring | **是** | **未改 → 见 A2 差异 2** |
| `agate/assets/execution-roles/verifier.md:60`（P5 执行叙述） | 可选 | 未改。verifier 经 AGATE_CARD 注入可见 P5 卡（`agate-inject-card.py`），故非硬性缺口；但角色文件与卡“同一活动”表述不齐 |
| `docs/guides/project-map.md:108`（`agate-advance.py` 同族） | 可选 | 未改，非必需 |
| `agate/CONTEXT.md:33`（`agate next / agate advance`） | 可选 | 未改，非必需 |
| `agate/scripts/README.md` 脚本索引表缺 `agate-md-field-set-gate-commands.py` 行 | 可选（约定） | 该工具从未进索引表（P2 卡现指向它）——`README` §新增脚本登记面 ④ 标注为**约定**、非门禁 |
| `agate/tests/README.md` 映射表 | 否 | 无 `agate-run.py` 映射行（既有，非本次引入；⑤ 约定） |
| `agate/WORKFLOW.md:323` / `dispatch-protocol.md:878`（P5→P6 转移） | 否 | 描述“从 P2 读命令执行”，语义未变，无需改 |
| `agate-gate-missing-cmds.py` / `check-gate.py P5` / `agate-gate-p5-count.py` | 否 | 消费 P2-design，不读卡；`agate-run` 写 `runs/`+账本、不写 `P5-test-results/`，与 P5 gate 判定面无交集 |

**结论**：MISALIGNED（A3b 的 README/docstring 与 A2 同根因）。其余推断项经核验为**不需要**或**可选**。

### A4: 测试覆盖 — ALIGNED

**最近一次全量实跑**（副本 `/tmp/opencode/tooladopt-repo`，CI 口径 `--reruns 1 -n auto`）：
```
1 failed, 2912 passed, 3 skipped, 1 rerun in 76.04s
EXIT=1
```
`count-tests.sh` → **总计 2916 个用例**（2912 + 1 + 3 = 2916，自洽）。

唯一 failed = `agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`：
```
ERROR  Unknown subcommand "agent" for "opencode debug"   Did you mean this?  agents
```
= 本机 `opencode` CLI 版本不支持 `debug agent` 子命令 ⇒ **环境性失败，与本次 diff 无关**（作者侧该用例通过时为 2913 passed，与 2916 总数亦自洽）。

**定向实跑**（7 个相关文件）：
```
109 passed in 8.06s
```
含新增 `test_rm_ag0102_task_source_gate_commands`（单跑 1 passed）、`test_agate_read_p5_commands.py`（7 passed，覆盖成对/不成对/空串边界）。

**边界覆盖**：新逻辑 `_resolve_from_task` 覆盖「任务源命中→可执行 + `runs/<k>.log` + 账本 `cmd_run`」与「未声明→拒绝」；共享函数边界由既有 `test_agate_read_p5_commands.py` 的 RM-AG0092 两例（`"pytest -k 'foo'"` / 不成对 `'foo`）覆盖。
**次要建议（不判 MISALIGNED）**：`agate_common.strip_paired_quotes` 无**直接**单测（仅经两 CLI 间接覆盖）；「config 源与 task 源同名」优先级无专项用例（手工实跑已确认无歧义，见 A8 实跑）。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED

**逐条**：经实测**无既有用例因本次变更转红**。证据：全量运行唯一失败为上述**环境性** `test_bdd_43_*`（opencode CLI 版本）；本次改动为「新增函数 + 逐字节搬移函数 + 文档接线」，无既有断言语义被改。
**夹具更新清单**：**空**——无需更新任何夹具。核验：`git grep _strip_paired_quotes` 在 `agate/tests/*` **0 命中**（无测试直接 import 被搬移的私有函数）；新用例复用既有 `git_repo`/`agate_scripts`/`python_exe`/`run_cli` fixtures。

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW

- **破坏性变更**：无。新任务源仅在 `--task` 时生效；`--task` 未给时行为**逐字不变**（见 A8 实跑：错误串与旧版完全一致）。
- **对既有项目 gate 行为**：无影响（`agate-run` 非 gate 判定路径；P5 gate 仍查 `P5-test-results/`）。
- **CHANGELOG**：已在 `[Unreleased]`（:188）记录。
- **UPGRADING.md**：本仓为 hotfix（非 release），按发布清单在发版时补章节；本次不要求。
- **文档传播缺口**：`agate/scripts/README.md`（同 A2）——建议同步；`verifier.md`/`project-map.md`/`CONTEXT.md` 为**可选**（卡经注入可见）。
- 需人工确认：传播面是否止于 README，还是连 `verifier.md` 一并补（设计取舍）。

### A6: 锚点表覆盖 — ALIGNED

本次未改任何 `check-*.py`、未新增 `agate/scripts/` 脚本。CHECK 9（`uncovered_gate_scripts()` 仅 glob `check-*.py`）不触发。实跑 `check-protocol-consistency.py` → **0 ERROR**（CHECK 9 ✅ PASS，CHECK 10 ⚠️ WARN 全为冻结历史告警，新增引用的 `agate-run.py`/`agate-advance.py`/`agate-md-field-set-gate-commands.py` 均真实存在，无 ERROR）。无需更新锚点表。

### A7: 设计原则一致性 — ALIGNED

符合 **ADR-014「判据必须单源」**：`strip_paired_quotes` 从 `agate-read-p5-commands.py` 提为 `agate_common` 单源，两消费方（`agate-read-p5-commands` 与 `agate-run`）共用，消除“同一引号语义两处实现”的漂移入口（`agate_common.py:1433` docstring 明标「单源（ADR-014）」）。无未记录的新架构决策，无需补 ADR。

### A8: 声称-命令绑定 — NEEDS_HUMAN_REVIEW

逐条 `声称 → 命令 → 结论`（均在 `/tmp/opencode/tooladopt-repo` 或原仓只读执行）：

| 声称 | 命令 | 结论 |
|---|---|---|
| 「全部 **49 个 `agate-*`**」 | `ls agate/scripts/ \| grep -c '^agate-'` | ✅ = 49 |
| 「真接线 47 / 仅历史提及 1 / 完全孤儿 1」 | 逐脚本 `git grep -l -- "$name" HEAD -- 'agate/*.md' 'agate/phase-cards/*' 'agate/assets/*' 'agate/rules/*' 'agate/scripts/*' '*.sh'`（排除自身） | ⚠️ **hyphen 形态下可复现**：仅 `agate-advance` 命中 0；`agate-md-field-set-gate-commands` 命中 1（`UPGRADING.md:1093`，发布说明=历史提及）⇒ 47/1/1。**但「完全孤儿」措辞不精确**（见下） |
| 「`agate-advance` = 完全孤儿」 | `git grep -n "agate advance" HEAD -- 'agate/*.md'` | ❌ 命中 **`agate/state-machine.md:339`**（“`agate advance` 是回退侧的引导壳”）、`agate/CONTEXT.md:33`；`UPGRADING.md:1029` 亦有 ⇒ 工具在协议文档中**已有（空格形态）提及**，非“零引用” |
| 「`agate-md-field-set-gate-commands` = 仅历史提及」 | 同上 | ✅ 非任务/CHANGELOG 面仅 `UPGRADING.md:1093`（发布说明） |
| 「P5 卡执行入口**改为** `agate-run --task`」 | 读 `P5-verification.md:38-42` | ⚠️ 卡实为「**推荐**」且明言「直接 bash 执行也能跑」——「改为」措辞偏强 |
| 「引号剥离口径提为 `agate_common.strip_paired_quotes` 单源」 | `git grep -n strip_paired_quotes` | ✅ 两处消费同源 |
| 「与 `check-gate.py::_reconcile_p2_fields` 同一函数」 | `check-gate.py:1012` vs `agate-md-field-set-gate-commands.py:107` | ✅ 同一 `agate_common.is_legal_gate_key` |
| 「0 ERROR」（consistency） | `python3 agate/scripts/check-protocol-consistency.py` | ✅ 0 ERROR（432 冻结 WARNING） |
| 「ruff」 | `~/.venvs/agate-dev/bin/ruff check agate/` | ✅ All checks passed |
| 「2913 passed」（作者侧） | `pytest agate/tests/ --reruns 1 -n auto` | ⚠️ 本机 **2912 passed + 1 环境性 failed + 3 skipped = 2916**；作者侧（`debug agent` 可用）为 2913 passed + 3 skipped，与总数自洽 |
| 「未声明命令仍被拒 / 未给 `--task` 行为不变」 | 手工 scratch 实跑（见下） | ✅ |

**手工 scratch 实跑**（`/tmp/opencode/tooladopt-scratch/proj`）：
1. `--task` + 任务源声明命令 → rc=0，落 `runs/1.log`，账本含 `cmd_run`（含 `k`/`log`/`sha256`）。
2. `--task` + 未声明命令 → rc=1，报「…或该任务 P2-design.md 的 gate_commands 中声明…」。
3. **无** `--task` + config 声明 → rc=0（旧路径不变）。
4. **无** `--task` + 未声明 → rc=1，错误串**与旧版逐字一致**：`agate-run: 命令未在 agate.config.yaml 的 verify.commands 中声明（不可绕开路径拒绝执行）: echo nope`。
5. config 与 task **同名** → config 先命中，命令文本相同 ⇒ 无歧义（`index` 在 `--task` 路径被丢弃）。

**需人工确认**：「完全孤儿」是否应改为更精确措辞（如「无调用接线——仅 `state-machine.md`/`CONTEXT.md` 空格形态同族提及」），或补记审计所用搜索口径。

## 重点结论（对应派发 5 项）

1. **白名单仍不可绕开**：✅ 任务源加入后，未在**任一**来源声明的命令仍被拒（用例 + scratch 实跑双向验证）；config 与 task 同名时 config 先命中且命令文本相同，无歧义；`--task` 未给时行为**逐字不变**（错误串逐字节一致）。
2. **单源提取逐字节等价**：✅ `strip_paired_quotes` 函数体从 `agate-read-p5-commands.py` **原样**搬入 `agate_common`（`if len(value)>=2 and value[0]==value[-1] and value[0] in ("'", '"')` 逐字相同），旧脚本改为 `import … as _strip_paired_quotes`；既有 7 例（含 RM-AG0092 成对/不成对/空串边界）仍全绿。
3. **P5 卡改动自洽**：✅ 新执行入口与既有「verifier 从 P2 读并执行」「判定规则」「技术栈无关/formatter」节**无直接矛盾**；`agate-run` 在子代理上下文**可调用**（`{agate_root}` 为本卡既有占位符，账本写 `<TASK_DIR>/gate-events.jsonl`）。次要：卡未说明 `agate-run` **不应用** formatter（formatter 仍由 baseline 捕获链消费），亦未预告 `runs/**` 被 ignore 时的拦截——建议补一句。
4. **两处文档接线可达性**：✅ 均可达——`state-machine.md` 注记落在「回退机制」节读者必经处且与脚本逐条相符；P2 卡注记落在「gate_commands 声明」节。**但**：`state-machine.md:339` **早已**以空格形态提及 `agate advance` ⇒ 审计「完全孤儿」措辞与事实相抵（A8）；且 `README`/模块 docstring 未同步（A2）。
5. **A4b + A8 实跑数字**：✅ 全量 `-n auto`：**1 failed（环境性 opencode CLI）/ 2912 passed / 3 skipped / 1 rerun**（总数 2916）；`0 ERROR`；ruff `All checks passed`；审计数字 `49` 与 `47/1/1`（hyphen 口径）复现，**「完全孤儿」措辞待改**。**不称「全绿」**。

## 是否可 commit

**不可 commit（存在 MISALIGNED）**。须先处置：

1. **A2/A3b（MISALIGNED，本次引入）**：同步 `agate/scripts/README.md:182` 与 `agate/scripts/agate-run.py` 模块 docstring，写明 `--task` 的第二命令源（任务 `P2-design.md` 的 `gate_commands`）。改动 1-2 行，低风险。
2. **A8（NEEDS_HUMAN_REVIEW）**：`CHANGELOG.md:189-190` 的「完全孤儿 1」对 `agate-advance` 不精确（`state-machine.md:339`/`CONTEXT.md:33` 已有空格形态提及）——改词或补记搜索口径；`CHANGELOG.md:193`「改为」宜改「推荐为」。人工确认后按 `[HUMAN_CONFIRMED: …]` 放行。

其余项（A1/A4/A4b/A6/A7 ALIGNED；A5 的可选传播面）不阻断。修完 A2 后重审 A2/A3；A8 经人工确认或改词后即可 commit。

## 审查自核验（只读纪律）

- 写类动作全在副本：全量 pytest / consistency / ruff 跑于 `/tmp/opencode/tooladopt-repo`；手工实跑于 `/tmp/opencode/tooladopt-scratch`。
- 原仓未被本次审查改动：`git status --porcelain` 仍仅列本 diff 的 8 个文件 + 本审查的两份文档（progress / 本报告），无协议/脚本/测试被改、无 commit/push。
