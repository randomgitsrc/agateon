---
review_date: 2026-09-09
task_id: TAG0033
round: 2 (protocol-docs batch)
reviewer: protocol-alignment-review (agent≠main)
status: approved
change_summary: TAG0033 P4 protocol-docs 批（文档面，第 2 批）——`platform-notes.md` Codex 章「待补充」→ 完整章（能力矩阵 / model 阵容 / spawn_agent schema [自述] / 命令流适配 / 验证记录表）+ Hermes/OpenClaw 拆节 + 既有「Codex 兼容性」注记加时效指针；`SETUP.md` 新增「步骤 2-Codex」小节；`CODE-MAP.md` line 33「三平台」→「四平台 / Codex rollout JSONL」；`docs/research/cross-platform-dispatch-mechanics.md` L169/L286「缺 CodexAdapter」逐处回写「已补（TAG0033, 2026-09）」；`codex-session.jsonl` 1 行（P5 V4 verifier fixture 收敛，非本批产出）。
files_changed: [agate/platform-notes.md, agate/SETUP.md, agate-workspace/agents/CODE-MAP.md, docs/research/cross-platform-dispatch-mechanics.md, agate/tests/fixtures/cmdstream/codex-session.jsonl, agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-implementation.md, agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P4-progress.md]
---

# 协议-脚本对齐审查 — TAG0033 Codex 平台文档批（P4 SELF-GATE，第 2 轮）

> 触发：`agate/*.md`（`platform-notes.md` / `SETUP.md`）改动（SELF-GATE）。本轮为**独立上下文**第 2 轮，
> 审 `protocol-docs` 批（`adapter-core` 批代码已 commit 在 `835c9b9`，本轮为其后未提交的文档改动）。
> 第 1 轮（`agate-alignment-review-2026-09-09-TAG0033.md`）SELF-GATE 对齐轴 PASS + 2 项
> NEEDS_HUMAN_REVIEW（NHR-1 = `platform-notes.md`/`SETUP.md` Codex 章待补；NHR-2 = research doc
> L169/L286 过时）——本轮核心是**确认 NHR-1 / NHR-2 已闭合** + 对新文档做 A1-A7 + 事实准确性核查。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐（NHR-1 闭合核查）| **ALIGNED（NHR-1 CLOSED）** |
| A3 | 一致性连锁 + 反向传播（NHR-2 闭合核查）| **ALIGNED（A3a ALIGNED；A3b ALIGNED，NHR-2 CLOSED）** |
| A4 | 测试覆盖 | **ALIGNED**（全量 1389 passed / 0 failed / 2 skipped）|
| A5 | 下游影响 + 文档传播 | **ALIGNED**（纯文档，无 gate 行为影响；CHANGELOG + 版本 bump 由 P8 处理——提示）|
| A6 | 锚点表覆盖 | **ALIGNED**（不新增 CHECK；`platform-notes.md`/`SETUP.md` 在 CHECK 14/15 整文件豁免）|
| A7 | 设计原则一致性 | **ALIGNED** |

**总结论：SELF-GATE 协议-脚本语义对齐轴 PASS（全 7 项 ALIGNED，无 MISALIGNED，无新增 NEEDS_HUMAN_REVIEW）。**
**第 1 轮 NHR-1 / NHR-2 均 CLOSED。** 附 1 项 P8 排期提示（CHANGELOG + 版本 bump），非本批阻塞。

---

## 逐项审查

### A1：文档→脚本对齐 — ALIGNED

新 `## Codex` 章每一处技术陈述对照 `CodexAdapter` 代码（`agate/scripts/agate-cmdstream-adapters.py:622-853`）
+ research doc `[实测]` 项 + `P5-test-results/real-machine.md` V1/V3/V4/V5 + `P1-requirements.md §4`：

| # | 文档陈述（platform-notes.md 行）| 对照源 | 判定 |
|---|---|---|---|
| 1 | rollout JSONL 落 `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO8601 秒精度>-<uuid>.jsonl`（按 UTC 日期分层）（L47）| P1 §4.1 [已实测] + P5 V1（「目录布局 `~/.codex/sessions/YYYY/MM/DD/`」）；代码 `list_sessions` `root = ...expanduser("~/.codex/sessions")` + `os.walk` 收 `rollout-*.jsonl`（L668-684）；`probe` `base.startswith("rollout-")` ∧ `.jsonl` 非 `.jsonl.zstd`（L641-651）| ALIGNED |
| 2 | per-command `CommandExecution` item **带数字 `exit_code` 字段**，`CommandRecord.exit` 直取（L87）| P1 §4.1.1 `[P0_STALE: ① 需修正]`（rollout item 有 `exit_code` 数字字段）+ P5 V1（`item.exit_code == 0` int）；代码 `_build_record` L836-838 `exit_code = raw_exit if isinstance(raw_exit, int) and not isinstance(raw_exit, bool) else None` | ALIGNED |
| 3 | 「退出码不可靠」只针对 **turn 级失败**（`turn.failed{status:400}` / `item.type=="error"`），对 per-command shell 执行不成立（能力矩阵「退出码可靠性」行 L61 + 命令流适配小节 L87）| P1 §4.1.1（「『无数字 exit code』结论只对 turn 级失败成立」）+ research §6.2 L195；P0-brief `[P0_STALE]` 已同步修正 | ALIGNED — **适用边界分清**：能力矩阵行明确「此结论只针对 turn 级失败；per-command shell 执行的退出码见下『命令流适配』小节（rollout item 带数字 `exit_code`）」，命令流适配小节反向再声明一次「上方『退出码不可靠』只针对 turn 级失败…对 per-command shell 执行不成立」 |
| 4 | 截断标记出现在 `formatted_output`——`Warning: truncated output (original token count: N)` + `…N tokens truncated…`（U+2026 省略号）；`CodexAdapter` 据 `_CODEX_TRUNC_TEXT_MARKERS` 的 `"tokens truncated"` 子串命中 → `truncated=True` + `output_hash=None`（L88）| P5 V4 [实测]（`formatted_output` 含 `"…252152 tokens truncated…"`，`_detect_truncated` → True，record `truncated is True` ∧ `output_hash is None`）；代码 `_CODEX_TRUNC_TEXT_MARKERS = ("[output truncated]", "output truncated", "tokens truncated", "[truncated]")`（L626-631）——**逐字确认含 `"tokens truncated"`**；`_detect_truncated` 对 `aggregated_output`+`formatted_output` 小写子串匹配（L764-787）；`_build_record` L845 `output_hash = None if truncated else _sha1_hex(...)` | ALIGNED |
| 5 | `multi_agent` = stable / effective true（实测 `codex features list`, 0.153.4）；`collaboration_modes` / `multi_agent_mode` 已 `removed`；`multi_agent_v2` stable 但 false（L74）| P5 V5 [实测]（`multi_agent  stable  true`；`collaboration_modes  removed`；`multi_agent_mode  removed  false`；`multi_agent_v2  stable  false`）+ P1 §4.4 + research 附录 A17 | ALIGNED |
| 6 | ChatGPT 账号 `codex exec -m` 默认 `gpt-5.6-terra`；`-m gpt-5` / `-m gpt-5-codex` 被 API 400 拒（引用 `"The 'gpt-5' model is not supported when using Codex with a ChatGPT account."`）（L68）| research §2.2 [实测]（逐字一致）+ P1 §4 | ALIGNED |
| 7 | `spawn_agent` 子会话是独立 `rollout-*.jsonl`（非父文件内嵌），与父同目录；`session_meta` 含 `parent_thread_id` / `thread_source=="subagent"` / `source.subagent.thread_spawn.depth`；`os.walk` 天然同时枚举父子（L75）| P1 §4.2 [已实测] + P5 V3（子文件 `thread_source=="subagent"` + `parent_thread_id`，`list_sessions` 枚举到子文件）；代码类 docstring L652-657 + `list_sessions` `os.walk`（L668-684）；`read_commands` `session_id = os.path.basename(session_path)`（不取 `payload.session_id`——对子会话是父 id，L686）| ALIGNED |
| 8 | `spawn_agent(task_name, message, model?, reasoning_effort?, fork_turns?)` schema 标 `[自述]`；「未见 `background`/`timeout`/`permission` 字段」只表述为「`[自述]` 未提及」，不升级为「一定不存在」；穷尽 schema 直接实测 = V2 待执行项（L78-82）| P1 §4.3 [自述]（「模型受训拒绝逐字输出内部 tool schema」，`[自述]` 是当前证据上限，穷尽登记为 V2）+ P0-brief 核心约束「证据强度诚实」（外部评审 B1 教训）| ALIGNED |
| 9 | `--full-auto` / `-a` 已从 `codex exec` 移除；旧「`-a never -s workspace-write` 折中」写法过期（能力矩阵「权限/沙箱（中间档）」行 L58）| research §4.2 L104「已弃：`--full-auto` / `-a` 已从 `codex exec` 移除」| ALIGNED |
| 10 | 能力矩阵其余 flag（`codex exec` 别名 `codex e`；`-m`/`--model`；`-c model_reasoning_effort=<low\|medium\|high>`；`-s <read-only\|workspace-write\|danger-full-access>` + `--approve-for-me`；`--skip-git-repo-check`；`--json` JSONL 事件流；`-o`/`--output-last-message`；`--output-schema`；`resume` / `fork` / `review` 子命令）| research §1.2 L40-42 + §3 L84 + §4.2 L102-104；子命令 `resume`/`fork`/`review` research L41 | ALIGNED |

**说明（非缺陷）**：代码 `_detect_truncated` 仍保留 `_CODEX_TRUNC_BOOL_KEYS`（`truncated`/`output_truncated`/`is_truncated`）
布尔信号分支，而文档 L88 如实记「item 上**无**布尔截断字段」——两者不冲突：文档描述 P5 V4 实机观察，代码保留
P2 设计点 4 的「保守双信号」兜底（`_detect_truncated` docstring 明示比照 `DSHAdapter`）。P5 V4 结论已明确
「`_CODEX_TRUNC_*` 常量无需收敛、无需回 P4」——belt-and-suspenders，非过时代码。

**A1 判定：ALIGNED。** 新 `## Codex` 章 10 组技术陈述逐条与 `CodexAdapter` 代码 + research `[实测]` + P5 V1/V3/V4/V5
+ P1 §4 一致。「退出码不可靠」vs「per-command 数字 exit_code」的适用边界（turn 级失败 vs per-command shell 执行）
在能力矩阵行 + 命令流适配小节**双向明确分清**。

---

### A2：脚本→文档对齐（NHR-1 闭合核查）— ALIGNED（NHR-1 CLOSED）

第 1 轮 NHR-1 = 「`platform-notes.md` 的 `## Codex / Hermes / OpenClaw 等` 章仍为『待补充』占位，`SETUP.md`
无 Codex 接入小节（`test_codex_platform_docs.py::test_bdd_22~27` 6 条预期红）」。本轮核查：

| 文档 | 本轮现状 | 判定 |
|---|---|---|
| `agate/platform-notes.md` `## Codex` 章 | 「待补充」占位 → 完整 `## Codex` 章（章首时效注记 + 平台形态 + 能力矩阵 14 行 + model 阵容小节 + `spawn_agent` 派发时效小节 + `spawn_agent` schema `[自述]` 小节 + 命令流适配小节 + 验证记录表）；Hermes/OpenClaw 拆为独立 `## Hermes / OpenClaw 等` 节续保「待补充」（不在 `_codex_section` 截取范围）| **CLOSED** |
| `agate/SETUP.md` Codex 小节 | 新增 `### 步骤 2-Codex：codex-cli（Codex）接入`（安装 `npm i -g @openai/codex` / `codex login`（ChatGPT vs API key 影响 model）/ 自动化绕过 flag `--dangerously-bypass-approvals-and-sandbox` + `--skip-git-repo-check` + `--json` / 验证接入 `codex features list` grep `multi_agent` + `codex exec --json` 冒烟）——排在 `### 步骤 2-DSH` 后，与 DSH 小节同构 | **CLOSED** |

**pytest 实跑核查（本审查自跑，2026-09-09）**：
`timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q` →
```
........                                                                 [100%]
8 passed in 0.03s
```
**8 passed / 0 failed**（第 1 轮为 6 failed / 2 passed；BDD-22~27 6 条由红转绿，BDD-29/30 守护保持绿）。

**A2 判定：ALIGNED（NHR-1 CLOSED）。** `CodexAdapter` 落地所需的协议文档同步（`platform-notes.md` Codex 章
BDD-22~26 + `SETUP.md` Codex 小节 BDD-27）已全部完成，doc-assertion 审计 8 passed / 0 failed。

---

### A3：一致性连锁 + 反向传播（NHR-2 闭合核查）— ALIGNED（NHR-2 CLOSED）

#### A3a 连锁 + 既有内容一致性（BDD-25）— ALIGNED

- **`CODE-MAP.md` line 33 同步**：`三平台命令流适配器：Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd`
  → `四平台命令流适配器：… DSH JSONL.zstd / Codex rollout JSONL（\`~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl\`，
  CodexAdapter 于 TAG0033 补齐）`。与 `ADAPTERS` 注册表现含 4 键（`claude-code`/`opencode`/`dsh`/`codex`，
  `agate-cmdstream-adapters.py:851`）一致。
- **新 `## Codex` 章与既有 line ~53-70 Codex 列 + 「Codex 兼容性」注记（`max_depth=1`）无未标时效对立**（BDD-25）：
  - 既有「Hardening-roadmap 跨平台适配」表的 Codex 列（pre-commit hook / provenance / CI backstop 等机制维度）
    未动、仍一致（P1 §3 S8 已核，本轮复核无回归）。
  - 既有「Codex 兼容性」注记（`Codex subagent max_depth=1` / 「单层任务工具无法再派发」，platform-notes.md
    L130-133）**几行事实内容未删**；其下**新增 1 行时效指针**（L135）：「↑ 上述 `max_depth=1` /「无法再派发」
    记于 subagent workflows 默认启用之前；时效更新见上方 `## Codex` 章…（`multi_agent` flag 实测 stable/true、
    `spawn_agent` 单层已实测可用、嵌套深度未测待复核）」。
  - 新 `## Codex` 章「子代理派发（`spawn_agent`）与既有「Codex 兼容性」注记的时效」小节（L72-76）反向交叉引用：
    明示 `multi_agent` stable/true、单层已实测（P5 V3）、嵌套深度未测（归 P6 V7）、`max_depth=1` 结论待 V7 复核，
    并显式声明「**不存在**『一处说无法再派发、另一处说已支持多层』的未标时效对立陈述」。
  - `test_bdd_25` 断言（`max_depth=1` 仍在全文 ∧ `## Codex` 节含 `max_depth` + `multi_agent` + 时效词）→ 绿。

**A3a 判定：ALIGNED。** 连锁项（CODE-MAP.md）已同步；新旧 Codex 内容双向交叉引用 + 标时效，无裸对立陈述。

#### A3b 反向传播（NHR-2 闭合 + 主动推断应被影响文档）— ALIGNED（NHR-2 CLOSED）

第 1 轮 NHR-2 = 「`docs/research/cross-platform-dispatch-mechanics.md` L169『⚠ 缺 `CodexAdapter`』/ L286
『唯一缺口 = Codex 适配器』在 `CodexAdapter` 落地后过时」。本轮逐一验证：

| # | 候选文件 | 应否受影响 | 本轮现状 | 结论 |
|---|---|---|---|---|
| 1 | `docs/research/cross-platform-dispatch-mechanics.md` **L169**（§6.0.1 映射表 Codex 行）| 是 | `⚠ **缺 \`CodexAdapter\`**` → `✅ **\`CodexAdapter\` 已补**（TAG0033，2026-09；本文调查快照期 2026-09-08 为「⚠ 缺」）…`spawn_agent` 子会话为 DSH 的 `delegationDepth` 式独立文件（P5 V3 实测确认）` | **CLOSED**（逐处回写，保留调查快照期标注）|
| 2 | `docs/research/cross-platform-dispatch-mechanics.md` **L286**（§11 未尽项 #2）| 是 | `唯一缺口 = Codex 适配器` → `~~唯一缺口 = Codex 适配器~~ → **\`CodexAdapter\` 已补**（TAG0033，2026-09；按 RM-AG0055 §3.4.4"约一个文件"落地，检测引擎/阈值零改动）` | **CLOSED**（划除 + 回写）|
| 3 | research doc L131（§5.3 Codex 深度继承）| 否 | `Codex \`[文档]\` \`[本轮未测]\`…未测嵌套深度——落地前实测 \`spawn_agent\` 内再 \`spawn_agent\`` | 无需改——嵌套深度**确实仍未测**（归 P6 V7），非过时表述；platform-notes.md 新章口径一致（「嵌套深度未测」）|
| 4 | research doc L275（§10 复核清单 #6）| 否 | 「本轮『证据强度低于实测』的两项…② Codex `spawn_agent` 参数 schema 是否穷尽…落地写调用代码时按『schema 可能不全』处理」| 无需改——穷尽 schema **确实仍是 V2 待执行项**（P5 real-machine.md「V2 → 延后 P6」），非过时；代码 `read_commands` 未假设 schema 已穷尽 |
| 5 | `agate/scripts/README.md` | 否 | `grep -n "cmdstream\|agate-cmdstream\|adapters.py\|detect.py\|codex\|适配器"` → **零命中**（该 README 从不维护 cmdstream 适配器/脚本清单）| 无需回写 |
| 6 | `agate/tests/README.md` | 否 | 同上，grep 零命中 | 无需回写 |
| 7 | `agate/LIMITATIONS.md` | 否 | `grep -n "[Cc]odex\|exit_code\|数字 exit\|命令流\|cmdstream\|adapter\|三平台"` → **零命中**（无「Codex 无数字 exit code」旧表述、无 cmdstream 适配器清单；P0-brief `[P0_STALE]` 指向 P0-brief/交接单本身，已在 P0-brief 内就地修正，不指向 LIMITATIONS.md）| 无需回写 |
| 8 | `agate/WORKFLOW.md` | 否 | L156 `\| Codex \| ✅ \| ✅ \| 完整 P0-P8 \|`（「已知适用环境」表行，环境适用性声明，本就 ✅，CHECK 14 表行豁免）；无 cmdstream / 命令流适配提及 | 无需改（P1 §3 S9 已核，本轮复核一致）|
| 9 | `agate/adr.md` | 否 | 无 ADR 与新增第四适配器冲突（见 A7）；「命令流适配器模式」ADR 缺口属 RM-AG0055/TAG0028 血缘，非 TAG0033 引入 | 无需改 |
| 10 | `CHANGELOG.md` / 版本文件 | 是 | 本批未含 | **P8 处理**（提示，见 A5；非本批阻塞）|
| 11 | `agate-cmdstream-detect.py` | 否 | `choices=sorted(ADAPTERS.keys())` 动态纳入 `codex` 键（第 1 轮 A3a 已核，`git diff` 空）| 无需改（连锁自动生效）|

**A3b 判定：ALIGNED（NHR-2 CLOSED）。** research doc L169 + L286 两处过时表述已逐处回写（保留「调查快照期
2026-09-08 为『⚠ 缺』」的时效标注，未做过度声明式全文改写——符合该文「时效性研究叙事」定位）。其余候选
（L131/L275 = 未测项非过时、两个 README / LIMITATIONS.md / WORKFLOW.md = 无对应旧文、adr.md / detect.py = 无需改）
均验证无需回写。CHANGELOG + 版本 bump 归 P8。

**A3 综合判定：ALIGNED。** A3a 连锁（CODE-MAP.md）+ 新旧内容交叉引用一致；A3b NHR-2 CLOSED，无遗漏的反向传播项。

---

### A4：测试覆盖 — ALIGNED

#### 全量 pytest 实跑输出（本审查自跑，2026-09-09）

命令：`timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=line`

```
........................................................................ [ 46%]
........................................................................ [ 51%]
........................................................................ [ 56%]
........................................................................ [ 62%]
........................................................................ [ 67%]
........................................................................ [ 72%]
........................................................................ [ 77%]
........................................................................ [ 82%]
........................................................................ [ 87%]
........................................................................ [ 93%]
........................................................................ [ 98%]
.......................                                                  [100%]
1389 passed, 2 skipped in 114.30s (0:01:54)
[exited with code 0]
```

**passed / failed / skipped 计数：1389 passed / 0 failed / 2 skipped**（与 dispatch-context「客观查证信息」
预期基线逐字一致；第 1 轮的 6 条 `test_codex_platform_docs.py::test_bdd_22~27` 预期红本轮全部转绿）。

#### doc-audit 断言体抽查（`agate/tests/unit/test_codex_platform_docs.py`，非空断言核查）

| BDD | 断言体（抽读）| 非空判定 |
|---|---|---|
| BDD-22（L41-63）| `assert "待补充" not in section` + `for anchor in ("codex exec","--model","model_reasoning_effort","--dangerously-bypass-approvals-and-sandbox","danger-full-access","--approve-for-me","--full-auto","spawn_agent","--json","resume","退出码"): assert anchor in section` —— 11 个具体锚点 grep | **实断言**（逐锚点校验措辞落地）|
| BDD-24（L82-92）| `assert "[自述]" in section` ∧ `assert "确认无" not in section` ∧ `assert ("待执行" in section or "真机验证" in section or "待实测" in section)` —— 证据强度三态守护（正向标注 + 负向禁词 + 待执行登记）| **实断言**（防止把 `[自述]` 升级为「确认无」）|
| BDD-27（L128-143）| `assert re.search(r"Codex", text)` + `for anchor in ("npm i -g @openai/codex","codex login","--dangerously-bypass-approvals-and-sandbox","--skip-git-repo-check"): assert anchor in text` + `assert "API key" in text or "API-key" in text` —— SETUP.md 4 个 CLI 锚点 + 账号类型说明 | **实断言**（校验安装/登录/绕过 flag 全覆盖）|

三条抽查均为具体子串 / 正则匹配断言，非 `assert True` 空断言；断言失败信息（如「Codex 章仍为『待补充』占位」
「不得把『未见字段』表述为『确认无字段』」）指向具体文档缺陷。

**A4 判定：ALIGNED。** 全量 1389 passed / 0 failed / 2 skipped（本审查自跑）；doc-audit 断言体为实校验、
覆盖新 Codex 章 + SETUP 小节的关键锚点与证据强度纪律。

---

### A5：下游影响 + 文档传播 — ALIGNED

- **gate 行为影响**：本批为**纯 `.md` 文档补齐**（`platform-notes.md` +67/-3、`SETUP.md` +43/-0、
  `CODE-MAP.md` +1/-1、research doc +2/-2）。**不改** `agate/scripts/*.py` / `agate/tests/` / `phases.yaml` /
  任何 gate 脚本 → 既有项目的 gate 行为**零影响**，无破坏性变更。
- **`codex-session.jsonl` 1 行改动**：dispatch-context 明确为 **P5 verifier 的 V4 fixture 收敛**（截断样例
  从 P2 推测形态收敛为 P5 V4 实测形态），属未提交的 P5 产出、非本批产物。本轮核对该行与 P5 real-machine.md
  §V4「顺手 fixture 数据收敛」描述一致（去布尔字段、`formatted_output` 用真机标记文本），BDD-7/9/17 复跑绿
  （已含在上方 1389 passed）。
- **`check-protocol-consistency.py`**（本审查自跑）：
  `timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` →
  `仅有 329 个 WARNING，无 ERROR`，`EXIT: 0`。329 WARNING 全为既有叙事文件的旧引用（与本改动无关）；
  新 Codex 章 / SETUP 小节 / research 回写未引入死链、行号漂移、平台名污染 ERROR。
- **CHANGELOG.md / 版本 bump**：本批未含。→ **提示 P8 需覆盖**「agate 协议本体 CHANGELOG：新增第四命令流
  适配器 Codex（`CodexAdapter`）+ 新增 Codex 平台接入文档（`platform-notes.md` Codex 章 + `SETUP.md`
  步骤 2-Codex）」+ 版本 bump（P2 §11 + 本任务 P8 阶段职责）。
- **`WORKFLOW.md`「Pre-commit 检查总览」**：不需动——本任务未新增 CHECK / gate 脚本触发行为。

**A5 判定：ALIGNED**（附 P8 提示：CHANGELOG + 版本 bump）。纯文档、无 gate 行为影响、无破坏性变更。

---

### A6：锚点表覆盖 — ALIGNED

- 本任务**不新增协议规则 / CHECK**（P0-brief 核心约束 + DEBT0025；P1 §5 范围锁定不扩 IR schema / 不改
  检测引擎 / 不改阈值）。
- `agate/platform-notes.md` / `agate/SETUP.md` 在 `check-protocol-consistency.py` 的 CHECK 14/15
  `_MD14_WHOLE_FILE_EXEMPT` **整文件豁免**名单（平台适配权威源；P1 §3 S7 已核）——补 Codex 散文 / 能力矩阵
  不触发平台名污染 ERROR。
- CHECK 9 `SCRIPT_ALIGNMENT_ANCHORS`（文档规则 → gate 脚本关键词白名单）遍历对象为 `check-*.py` +
  `pre-commit-gate.{sh,py}` + `ci-gate-backstop.py`——新 Codex 章不引入任何 CHECK / 协议数值规则 /
  锚点关键词。CHECK 12（权威数值跨文件一致性：重试上限表等）与 Codex 平台文档无关。
- 本审查自跑 `check-protocol-consistency.py --strict-errors-only` → EXIT 0 / 0 ERROR 佐证。

**A6 判定：ALIGNED。** 不新增 CHECK / 协议规则，CHECK 9 / CHECK 12 锚点表均无需更新。

---

### A7：设计原则一致性 — ALIGNED

对照 `agate/adr.md`：

| ADR | 相关性 | 对齐判定 |
|---|---|---|
| ADR-003 最小约定——不绑定技术栈 | 相关：新 `## Codex` 章把 Codex rollout JSONL 格式、`~/.codex/sessions` 布局、`exit_code` 数字字段、截断标记形态、`spawn_agent` schema 等平台特定细节**收敛在平台适配权威源文档**（`platform-notes.md` line 3 职责声明：「平台适配权威源——各 Agent 平台能力矩阵」），未向协议骨架 / gate 脚本泄漏 Codex 概念 | ALIGNED |
| ADR-005 改动性质决定流程——机制交叉 | 相关：改 `agate/*.md`（含平台适配权威源）触发 SELF-GATE（commit-msg hook + 本 A1-A7 审查，`agent != main`）。本轮即该流程第 2 轮 | ALIGNED——SELF-GATE 流程照走 |
| ADR-006 双层角色——独立评审 | 间接：本审查独立上下文（`agent≠main`）执行 | ALIGNED |
| ADR-001/002/004/007~012 | 无相关性——本批不涉隔离性产出、可判定 gate 门槛、frontmatter schema、版本管理、证据复用、引导型 CLI | N/A |

**「新兴平台需持续复核 + 注明验证版本」范式一致性**（比照 DSH 章 / OpenCode 章）：
- 新 `## Codex` 章**章首时效注记**（L45）：「已实机验证（**2026-09**，codex-cli **0.153.4**，**ChatGPT 登录**
  账号，本机 Linux/WSL2）——新兴平台，机制随版本变化快，落地前须在目标版本上 `codex features list` +
  `codex exec --help` 复核（比照本文件 DSH 章 / OpenCode 章「新兴平台需持续复核」惯例）」——与 DSH 章
  「已实机验证（2026-08-21，DSH v0.1.0-rc.8）——新兴平台，机制可能随版本变化」范式逐条对应。
- 章末**验证记录（Codex）表**（L90-102）：逐项标结论 + 阶段（V1/V3/V4/V5 = P5，V6/V7/V2 = P6，
  API-key model 阵容 = 待环境）；表末「验证环境：codex-cli 0.153.4、ChatGPT 登录账号、本机 Linux（WSL2），
  验证日期 2026-09」——符合「注明验证版本」范式（DSH 章有等价「最近复核（2026-09-01, DSH v0.1.2-alpha.3）」）。
- model 阵容小节把「API-key 账号 model 阵容」显式登记「本会话未核实…**待有该环境时补（非阻塞）**」——
  证据强度诚实（P0-brief 核心约束）。
- `SETUP.md` 「步骤 2-Codex」小节结构与「步骤 2-DSH」同构（编号步骤 + 版本敏感提示 + 「新兴平台，机制随
  版本变化」）。

**观察（非阻塞，非本轮新增）**：「统一 IR + 每平台一个适配器 + 检测引擎平台无关」架构决策仍仅存于设计笔记
§3.4.4，未沉淀为 `adr.md` 条目——与第 1 轮 A7 及 TAG0024/TAG0032 A7 同类观察一致，属 RM-AG0055/TAG0028 血缘，
非 TAG0033 引入、非本轮阻塞。

**A7 判定：ALIGNED。** 新 Codex 章符合 `platform-notes.md` 「平台适配权威源」职责边界（line 3）+ DSH/OpenCode 章
确立的「新兴平台需持续复核 + 注明验证版本」范式；SETUP.md Codex 小节与 DSH 小节同构。无 ADR 冲突。

---

## 事实准确性核查（顶 C8 review 对文档的一遍）

新 `## Codex` 章关键事实断言逐条对照权威来源，标 ✔ / ✘：

| # | 文档断言 | 权威来源 | 核查 |
|---|---|---|---|
| 1 | `codex exec` 别名 `codex e`；flag 全集 `-m` / `-c model_reasoning_effort=<low\|medium\|high>` / `-s <read-only\|workspace-write\|danger-full-access>` / `--approve-for-me` / `--json` / `resume`（子命令，另 `fork`/`review`）/ `--skip-git-repo-check` | research §1.2 L40-42、§3 L84、§4.2 L102-104 | **✔**（逐项命中；别名 `codex e` = research L40；`resume`/`fork`/`review` = research L41）|
| 2 | `--full-auto` / `-a` 已从 `codex exec` 移除；旧「`-a never -s workspace-write` 折中」写法过期 | research §4.2 L104「已弃」 | **✔**（逐字一致）|
| 3 | ChatGPT 账号 `codex exec -m` 默认 `gpt-5.6-terra`（实测可用）；`-m gpt-5` / `-m gpt-5-codex` 被 API 400 拒（`"The 'gpt-5' model is not supported when using Codex with a ChatGPT account."`）；白名单见 `~/.codex/models_cache.json` | research §2.2 [实测]（L64-65）、§2.3 | **✔**（引号内报错信息逐字一致；research L65「gpt-5 家族推测需 API key 账号」）|
| 4 | `spawn_agent` 的 `model` 枚举 4 个（`gpt-5.6-terra` / `gpt-5.6-luna` / `gpt-5.5` / `gpt-5.4-mini`，`[自述]`，比 `codex exec -m` 可用集更宽）；`reasoning_effort` 枚举 `low\|medium\|high\|xhigh\|max\|ultra` | research §5.2 L126 [自述]、附录 A12 | **✔**（4 枚举 + 6 档逐项一致；标注 `[自述]`）|
| 5 | `multi_agent` = stable / effective true（`codex features list`, 0.153.4，无需 `--enable`）；`collaboration_modes` / `multi_agent_mode` = removed；`multi_agent_v2` = stable / false（但子会话 `session_meta` 见 `multi_agent_version: "v2"`）| P5 V5 [实测]（`codex features list` 原始输出）、P1 §4.4、research 附录 A17 | **✔**（与 P5 V5 `codex features list` 四行输出逐字对应）|
| 6 | rollout JSONL 目录结构 `~/.codex/sessions/YYYY/MM/DD/rollout-<ISO8601 秒精度>-<uuid>.jsonl`（UTC 日期分层）；`CommandExecution` item 带 `command`（数组）/ `exit_code`（数字）/ `status` / `aggregated_output` / `formatted_output`；`payload.started_at_ms` / `completed_at_ms`（epoch ms int）| P1 §4.1 [已实测] + P5 V1 PASS（「目录布局」「`item` 键 `{aggregated_output, command, cwd, duration, exit_code, formatted_output, id, parsed_cmd, process_id, source, status, stderr, stdout, type}`」「`started_at_ms` / `completed_at_ms` = epoch ms int」）| **✔** |
| 7 | 截断标记实测形态（P5 V4）：item 上**无**布尔截断字段；标记在 `formatted_output`——`Warning: truncated output (original token count: N)` + `…N tokens truncated…`（U+2026 省略号字符）；`_CODEX_TRUNC_TEXT_MARKERS` 的 `"tokens truncated"` 子串命中 → `truncated=True` + `output_hash=None` | P5 V4 [实测]（「item 键…无 `truncated`/`output_truncated`/`is_truncated` 任何布尔字段」「`formatted_output`…`Warning: truncated output (original token count: 262152)`…`…252152 tokens truncated…`（U+2026）」「`_detect_truncated(<真机 item>)` → `True`」）+ 代码 `_CODEX_TRUNC_TEXT_MARKERS` 逐字含 `"tokens truncated"` | **✔** |
| 8 | `spawn_agent` schema 标 `[自述]`（非逐字 tool JSON schema dump——模型受训拒绝逐字输出）；「未见 `background` / `timeout` / `permission` 字段」只表述为「`[自述]` 未提及」，不升级为「一定不存在」；「穷尽 `spawn_agent` 参数 schema 直接实测」= 真机验证清单 V2 待执行项（P5-P6，换法：读二进制 strings / 内省 / 跨调用归纳键并集）| P1 §4.3 [自述]（「模型受训拒绝」「`[自述]` 是当前证据上限」「穷尽 schema 登记为真机验证清单 §7 项 V2」）+ P0-brief 核心约束「证据强度诚实」（外部评审 B1 教训）+ P5 real-machine.md「V2 → 延后 P6」 | **✔** |

**事实核查结果：8 / 8 全 ✔，无 ✘。**

---

## NHR-1 / NHR-2 闭合判定

| 第 1 轮 NHR | 内容 | 本轮闭合动作 | 判定 |
|---|---|---|---|
| **NHR-1** | `platform-notes.md` 的 `## Codex / Hermes / OpenClaw 等` 章为「待补充」占位 + `SETUP.md` 无 Codex 接入小节（`test_codex_platform_docs.py::test_bdd_22~27` 6 条预期红）| `platform-notes.md` 补完整 `## Codex` 章（能力矩阵 + model 阵容 + `spawn_agent` schema `[自述]` + 命令流适配 + 验证记录表）+ Hermes/OpenClaw 拆节；`SETUP.md` 新增「步骤 2-Codex」小节；`test_bdd_22~27` 6 条转绿（本审查自跑 8 passed / 0 failed）| **CLOSED** |
| **NHR-2** | `docs/research/cross-platform-dispatch-mechanics.md` L169「⚠ 缺 `CodexAdapter`」/ L286「唯一缺口 = Codex 适配器」在 `CodexAdapter` 落地后过时 | L169 → 「✅ `CodexAdapter` 已补（TAG0033，2026-09；本文调查快照期 2026-09-08 为『⚠ 缺』）」+ P5 V3 实测锚；L286 → 划除原句 + 「`CodexAdapter` 已补（TAG0033，2026-09；检测引擎/阈值零改动）」。逐处回写、保留调查快照期时效标注（符合「时效性研究叙事」定位）| **CLOSED** |

**两项第 1 轮 NEEDS_HUMAN_REVIEW 本轮均 CLOSED，无需再挂人工确认。**

---

## A3b 反向传播清单（逐一验证汇总）

| # | 候选文件 | 应否受影响 | 现状 | 结论 |
|---|---|---|---|---|
| 1 | research doc L169（§6.0.1 映射表）| 是 | 已回写「`CodexAdapter` 已补」+ 快照期标注 | **CLOSED** |
| 2 | research doc L286（§11 #2）| 是 | 划除 + 回写「已补」| **CLOSED** |
| 3 | research doc L131（§5.3 深度继承）| 否 | 嵌套深度确实仍未测（P6 V7）| 无需改 |
| 4 | research doc L275（§10 复核清单 #6）| 否 | schema 穷尽确实仍是 V2 待执行 | 无需改 |
| 5 | `agate/scripts/README.md` | 否 | grep 零命中（无 cmdstream 适配器/脚本清单）| 无需改 |
| 6 | `agate/tests/README.md` | 否 | grep 零命中 | 无需改 |
| 7 | `agate/LIMITATIONS.md` | 否 | grep 零命中（无「Codex 无数字 exit code」旧文、无适配器清单）| 无需改 |
| 8 | `agate/WORKFLOW.md` | 否 | L156 环境适用性表行本就 ✅，与 cmdstream 无关 | 无需改 |
| 9 | `agate/adr.md` | 否 | 无 ADR 冲突（A7）；适配器模式 ADR 缺口属 RM-AG0055 血缘 | 无需改 |
| 10 | `CHANGELOG.md` / 版本文件 | 是 | 本批未含 | **P8 处理**（提示，非本批阻塞）|
| 11 | `agate-cmdstream-detect.py` | 否 | `choices=sorted(ADAPTERS.keys())` 动态纳入 codex 键 | 无需改 |
| 12 | `agate-workspace/agents/CODE-MAP.md` L33 | 是 | 「三平台」→「四平台 / Codex rollout JSONL（CodexAdapter 于 TAG0033 补齐）」| **已同步** |

---

## A4 pytest 实跑输出（完整）

**命令 1**：`timeout 120s python3 -m pytest agate/tests/unit/test_codex_platform_docs.py -q`
```
........                                                                 [100%]
8 passed in 0.03s
```
→ **8 passed / 0 failed**（NHR-1 闭合佐证；第 1 轮 6 failed / 2 passed → 本轮全绿）

**命令 2**：`timeout 300s python3 -m pytest agate/tests/unit/ -q --tb=line`
```
1389 passed, 2 skipped in 114.30s (0:01:54)
[exited with code 0]
```
→ **1389 passed / 0 failed / 2 skipped**（与 dispatch-context 预期基线逐字一致；第 1 轮 6 条 doc-audit 预期红本轮全转绿）

**命令 3**：`timeout 120s python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`
```
仅有 329 个 WARNING，无 ERROR。
EXIT: 0
```
→ **EXIT 0 / 0 ERROR / 329 WARNING**（WARNING 全为既有叙事文件旧引用，与本改动无关）

---

## 附：非阻塞提示（不计入 NEEDS_HUMAN_REVIEW）

- **P8 提示**（A5 / A3b #10）：agate 协议本体 `CHANGELOG.md` + 版本 bump 需在 P8 覆盖「新增第四命令流适配器
  Codex（`CodexAdapter`）+ 新增 Codex 平台接入文档（`platform-notes.md` Codex 章 + `SETUP.md` 步骤 2-Codex）」。
  第 1 轮 A5 已提示（针对 `CodexAdapter` 代码），本轮补充文档面同批覆盖。
- **A7 观察**（非本轮新增）：「命令流适配器模式」架构决策仅在设计笔记 §3.4.4、未沉淀为 `adr.md` 条目
  （同第 1 轮 A7 / TAG0024 / TAG0032 A7），属 RM-AG0055/TAG0028 血缘，可酌情转该 RM 后续，非本任务必办。
- **fixture 归属**（A5）：`agate/tests/fixtures/cmdstream/codex-session.jsonl` 1 行改动 = P5 V4 verifier 已做的
  fixture 收敛（未提交的 P5 产出），非 protocol-docs 批产物；本轮核对与 P5 real-machine.md §V4 描述一致。

---

## 总结论

**SELF-GATE 协议-脚本语义对齐轴：PASS（全 7 项 ALIGNED，无 MISALIGNED，无新增 NEEDS_HUMAN_REVIEW）。**

- **A1 / A2 / A3 / A4 / A5 / A6 / A7 全部 ALIGNED**：
  - A1 — 新 `## Codex` 章 10 组技术陈述逐条符合 `CodexAdapter` 代码 + research `[实测]` + P5 V1/V3/V4/V5 + P1 §4；
    「退出码不可靠」vs「per-command 数字 exit_code」适用边界双向分清；`_CODEX_TRUNC_TEXT_MARKERS` 逐字含 `"tokens truncated"`。
  - A2 — **NHR-1 CLOSED**：`platform-notes.md` Codex 章 + `SETUP.md` Codex 小节已补，`test_codex_platform_docs.py`
    8 passed / 0 failed（本审查自跑）。
  - A3 — **NHR-2 CLOSED**：research doc L169/L286 逐处回写；A3a 连锁（CODE-MAP.md）已同步；A3b 其余候选
    （两个 README / LIMITATIONS.md / WORKFLOW.md / adr.md / detect.py / research L131·L275）均验证无需回写。
  - A4 — 全量 1389 passed / 0 failed / 2 skipped（本审查自跑）；doc-audit 断言体为实校验。
  - A5 — 纯文档、无 gate 行为影响、无破坏性变更（附 P8 提示：CHANGELOG + 版本 bump）。
  - A6 — 不新增 CHECK / 协议规则；`platform-notes.md` / `SETUP.md` CHECK 14/15 整文件豁免；
    `check-protocol-consistency.py --strict-errors-only` EXIT 0 / 0 ERROR。
  - A7 — 符合「平台适配权威源」职责边界 + DSH/OpenCode 章「新兴平台需持续复核 + 注明验证版本」范式；无 ADR 冲突。

- **事实准确性核查：8 / 8 全 ✔，无 ✘。**

- **第 1 轮 NHR-1 / NHR-2 均 CLOSED**——无需再挂 `[HUMAN_CONFIRMED]`。

**闭环动作**：本 SELF-GATE 第 2 轮审查即闭环，protocol-docs 批可随 P4b（连同 P5 产出）commit
（commit message 须含 `self-gate-review:` 指向本报告
`agate-workspace/reviews/agate-alignment-review-2026-09-09-TAG0033-r2.md`）。文档本身无需任何修订。
P8 需覆盖 CHANGELOG + 版本 bump（Codex 适配器 + Codex 平台文档同批）。
