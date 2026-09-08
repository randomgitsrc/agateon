---
phase: P1
task_id: TAG0033
type: review
parent: P1-requirements.md
trace_id: TAG0033-P1-review-20260909-r2
status: approved
created: '2026-09-09'
review_round: 2
agent: requirements-review
---

# P1 需求基线评审 — TAG0033 Codex 命令流适配器（RM-AG0061）

> 第 1 轮判 `needs-revision`（1 阻塞 + 2 非阻塞）。analyst 定向修订后本轮为第 2 轮复评。
> 本轮范围：① 复核 3 修订点是否闭合；② 抽查第 1 轮已通过部分无回归。**不重新全量评审。**
> 结论：**approved** —— 3 修订点全部 CLOSED，抽查无回归。

---

## 第 2 轮复核段（本轮新增）

### 修订点 1〔阻塞〕—— `capability_requirements` `codex-api-key-account` 条目 —— **CLOSED**

analyst 采用**修法 (a)**：整条移除。逐判据独立复核：

- **(a) frontmatter `capability_requirements` 只剩一条** —— ✔ 复核 frontmatter line 15-20：列表现只有
  `- need: codex-cli-installed-authenticated`（`available:` 含"本机 codex-cli 0.153.4 + ChatGPT 登录已具备"、
  `status: available`——本机确有，不矛盾）。`grep -nE 'codex-api-key-account' P1-requirements.md` **无命中**——
  `codex-api-key-account` 整条已不存在。
- **(b) `verification_env` + `verification_env_budget` 两行仍在、未削弱** —— ✔ frontmatter line 21-22：
  `verification_env: "codex-cli 0.153.4 + ChatGPT 登录（本机已就绪）；API-key 账号环境本机不可得"`、
  `verification_env_budget: "止损轮次 2（独立计数，不占 retries[P5]）；仅适用于 API-key 账号 model 阵容项，
  其余真机项本机可做"`——内容与第 1 轮所见一致，未被削弱。
- **(c) §10 正文对应段已改说明、与 §7 V8 / #### BDD-26: / #### BDD-29: 指向一致、无残留矛盾** —— ✔
  §10「能力需求声明」现两条：`codex-cli-installed-authenticated` 标 **available**；第二条改为
  「API-key 账号 model 阵容（§7 V8）是**运行环境不可得项**，不是 `capability_requirements` 条目——走 frontmatter
  `verification_env` + `verification_env_budget: 止损轮次 2` 声明（按 P1 卡片『verification_env vs supplementable
  边界判断树』：换谁来做都得先有 API-key 账号 → 环境问题）。非 GAP、非阻塞；由 §7 V8 + BDD-26 / BDD-29 承载」。
  与 §7 V8 表行（"❌ 待有该环境时补（非阻塞）" + `verification_env_budget: 止损轮次 2`）、#### BDD-26:
  （"API-key 账号 model 阵容登记为『待有该环境时补』（非阻塞）"）、#### BDD-29: （"本机 ChatGPT 账号做不了的项
  … 显式标注『待有该环境时补（非阻塞）』并给出 `verification_env_budget` 轮次占位"）**三处指向一致**，无
  "一处 capability 一处 env" 的残留镜像矛盾。
- **(d) `check-frontmatter.py` exit 0** —— ✔ 复跑
  `python3 agate/scripts/check-frontmatter.py agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P1-requirements.md`
  → **EXIT=0**。

第 1 轮维度 7 的唯一阻塞理由（`status: available` + `available: []` + `note` 自陈本机不具备，声明与实际/仓内先例
矛盾）已随该条目整体移除而消解——不再有"声明与实际不一致"的条目。**修订点 1 CLOSED。**

### 修订点 2〔非阻塞〕—— §3 同类扫描补 S12 + S10 —— **CLOSED**

- **§3 表新增 S12 行** —— ✔ 复核 P1-requirements.md §3 表（line 87）：
  `| S12 | agate/tests/unit/test_agate_cmdstream_detect.py:371 | for platform_word in ("claude", "opencode", "dsh"):
  （test_bdd_24_output_platform_agnostic）| 本次不处理——负向断言（断言检测输出**不含**这些平台词），加第四键
  不打破；可选强化：元组加 "codex" 以断言 Codex 也不泄漏 |`——处置判定与第 1 轮维度 2 补全建议 1 一字对应。
- **S10 处置行补一句** —— ✔ §3 表 S10 行（line 85）末补：
  「P4 同步把 `agate/tests/fixtures/cmdstream/codex-session.jsonl` 加入
  `test_agate_cmdstream_adapters.py::test_bdd_7_fixture_sanitized` 的脱敏校验清单（否则新 fixture 无自动脱敏校验）」
  ——与第 1 轮维度 2 补全建议 2 一致。
- **独立抽验 S12 负向断言** —— ✔ `grep -n 'for platform_word' agate/tests/unit/test_agate_cmdstream_detect.py`
  → `371:    for platform_word in ("claude", "opencode", "dsh"):`。读 :362-372 上下文确认该断言体为
  `assert platform_word not in joined.lower(), f"检测输出绑定平台: {platform_word}"`——**是"断言检测输出不含平台词"的
  负向断言**（`test_bdd_24_output_platform_agnostic`，检测输出本就平台无关）。向 `ADAPTERS` 加第四键
  `"codex"` 不会让检测输出冒出 "codex" 字样，**不打破该断言**。S12 判定"本次不处理"成立。

**修订点 2 CLOSED。**

### 修订点 3〔非阻塞〕—— #### BDD-7: Given 补兜底 fixture 来源 —— **CLOSED**

- ✔ 复核 P1-requirements.md line 300：#### BDD-7: 的 Given 现为
  「Given rollout fixture 含一条 `CommandExecution`，输出携带截断标记形态（**P4 先用 §8 `[SUGGEST]` ③「比照
  `DSHAdapter._detect_truncated` 保守双信号」兜底 fixture，P5 V4 实测后按 §4.1.2 收敛——不必等 V8/V4 产出才能写
  本 BDD 测试**）」——含第 1 轮修订点 3 要求的"P4 保守双信号兜底 fixture、P5 V4 实测后按 §4.1.2 收敛"意味，
  且显式点出"不必等 V8/V4 产出"，正好消除第 1 轮担心的"P4 执行者误读为必须先有 V8 产出"。
- ✔ **判定语义未变**：When 仍为 `read_commands`；Then 仍为
  `对应 CommandRecord.truncated is True 且 output_hash is None`——与第 1 轮所见二值判据逐字一致，无收紧/放宽。

**修订点 3 CLOSED。**

---

## 抽查无回归声明（第 1 轮已通过部分）

逐项复核，确认未被本轮定向修订波及：

- **BDD 仍 30 条、编号 1..30 连续** —— ✔ `grep -c '^#### BDD-' P1-requirements.md` → **30**；
  `grep -oE '^#### BDD-[0-9]+'` 列出 #### BDD-1: … #### BDD-30: 连续无缺号、无跳号。
- **frontmatter 五机器字段未变** —— ✔ line 10-14：`risk_level: medium` / `ceremony: standard` /
  `phases: [P1, P2, P3, P4, P5, P6, P7, P8]` / `packages: [agate-scripts, agate-docs, agate-tests]` /
  `domains: [backend]`——与第 1 轮维度 8 所核一致。
- **`[NO_NEED_CONFIRM]` / `[PROD_NOT_TOUCHED]` 仍在** —— ✔ line 32-33 原位保留；§8 line 451
  `[NO_NEED_CONFIRM]` 亦在。
- **§4.1.1 `[P0_STALE: …]` 段未被波及** —— ✔ line 131-142 §4.1.1「Codex 有无数字 exit code」整段 +
  行首 `[P0_STALE: P0-brief/交接单称 Codex 无数字 exit code …仅 turn 级失败无数字 exit]`（line 138）完好；
  §4.6 时效性质疑表「轻微漂移」行（line 240）同一 `[P0_STALE]` 陈述 + "判据 1-3 均不命中、轻微漂移 → 记录后
  继续、不阻塞"结论未变。
- **§4.6 时效性质疑结论未变** —— ✔ "已核对 P0-brief 时效性。判定：基本无漂移 + 1 处轻微漂移已记录"
  （line 230）+ 6 行核对表 + "判据 1-3 均不命中"结论原样。
- **§5 范围锁定未被波及** —— ✔ "P1 分析**未发现**需超出四交付面的情形"（line 246）+ 五条逐项论证
  （IR 十字段足以表达 / 检测引擎零改 / 阈值零改 / 既有三适配器不动 / 唯一改动清单）+ 逃生阀句
  "若 P2/P3/P4 发现必须扩 IR / 改检测引擎 / 改阈值 / 动既有适配器——**立即停下报告主 Agent**"（line 258）原样。
- **§7 V8 行 + `verification_env_budget` 未削弱** —— ✔ §7 表 V8 行（line 444）"❌ **待有该环境时补
  （非阻塞）**——本机为 ChatGPT 账号。`verification_env_budget: 止损轮次 2`"，V8 脚注（line 446-447）
  "唯一『环境不可得』项 … **不阻塞** P1-P8 推进"未变。
- **同类扫描 S1-S11 判定未变** —— ✔ §3 表 S1-S11 行内容与第 1 轮维度 2 独立核验表逐条一致（仅在 S10 行
  末尾追加一句、在 S11 后新增 S12 行，S1-S9、S11 正文未动）。
- **§9 裁剪说明未变** —— ✔ `phases: [P1..P8]` 全保留 + 逐阶段保留理由 + `risk_level: medium` /
  `ceremony: standard` 论证（line 458-476）原样。

**抽查结论：无回归。** 本轮 diff 严格局限于 frontmatter 删 1 条 capability 条目、§10 改 1 段说明、§3 补 S10 半句 +
S12 整行、#### BDD-7: Given 补兜底来源——均为定向修订，未溢出到其它章节。

---

## 第 1 轮逐维度结论摘要（沿用，未重评）

> 以下为第 1 轮独立评审结论，本轮抽查确认对应产物未回归，结论沿用。

### 维度 1 — BDD 二值可判定性〔覆盖〕：**通过**

#### BDD-1: … #### BDD-30: 均为 `#### BDD-NN:` 标准格式、连续不跳号、每条单一 Given/When/Then、无中间态、
无主观词。重点抽查：#### BDD-4: 十字段逐字段给可判值（`platform=="codex"` / `command` 含 `"echo hi"` /
`ts_start==T1` / `ts_end==T2` / `exit==0` / `truncated is False` / `output_hash == sha1("hi\n")`；`tool`/`exit_signal`
为非空检查；`session_id` 由 #### BDD-10: 覆盖）；#### BDD-7: / #### BDD-17: 截断判据本身二值可执行、截断形态为延迟
输入（本轮修订点 3 已把 Given 兜底来源写清）；#### BDD-13: / #### BDD-14: 阈值 900s / 300s 与
`agate-cmdstream-detect.py`（`CALL_SUSPECT_FALLBACK=900` / `ACTIVITY_SUSPECT=300`）+ RM-AG0055 §3.4.3 逐条一致；
#### BDD-15: SPIN ≥ 5（`SPIN_THRESHOLD=5`）+ #### BDD-17: 截断行 `if r.get("truncated"): continue` 跳哈希；
#### BDD-21: "零功能改动"机械判定（`git diff` 下十字段无改动 / 阈值常量与 `detect()` 逻辑无改动 / 既有三 class
体无改动）边界清晰、可二值。

### 维度 2 — 同类扫描完整性〔覆盖〕：**核心判断通过**（本轮 2 处补全建议已落地为 S12 + S10 半句）

§3 命中表 S1-S11 逐条独立核验成立：S1（`detect.py` CLI `choices=sorted(ADAPTERS.keys())` 动态、非硬编码三键，
加第四键零改动）、S2（`adapters.py:623-627` 三键字面量，加 `"codex"` 一行）、**S4**（`test_agate_cmdstream_adapters.py:317`
`assert registered == {"claude-code","opencode","dsh"}` **精确等值确认存在**、加 `"codex"` 键必破 → #### BDD-19: 改包含式，
修订面正确）、S3/S5（`>=` 包含式 / 仅断言引用存在，不破）、S6（CHECK 12 `AUTHORITATIVE_VALUE_ANCHORS` 仅 `retry-max`，
与 `platform-notes.md` 能力矩阵无关）、S7（`platform-notes.md` / `SETUP.md` 在 `_MD14_WHOLE_FILE_EXEMPT` 整文件豁免，
由 #### BDD-20: `--strict-errors-only` 0 ERROR 兜底）、S8（既有 Hardening-roadmap 表已含 Codex 列 + max_depth=1 注记，
#### BDD-25: 要求交叉引用 + 标时效）、S9（`WORKFLOW.md` 非交付面）、S10（fixtures 目录新增 `codex-session.jsonl`）、
S11（research / design-note 只读参照）。repo 全量扩查 `len(ADAPTERS)` / `ADAPTERS.*==` / `claude-code.*opencode.*dsh`
**未发现第二处会被第四键打破的精确等值 / 计数断言**——#### BDD-19: 修订面（仅 :317 一处）完整。

### 维度 3 — P0-brief 时效性质疑〔覆盖〕：**通过**

P1 卡片判据 1-3（目标方案不成立 / 平台前提不成立 / 已解决前提实际未解决）均不命中；§4.6 判定"轻微漂移 → 记录后
继续"正确。主 Agent 已把 `[P0_STALE: ① 需修正]` 回写 `P0-brief.md` scope ①（line 35-38），内容与 P1-requirements.md
§4.1.1 / §4.6 表述一致、无残留矛盾。真机抽验：`~/.codex/sessions/2026/09/09/` 下 `CommandExecution` item 键含
`exit_code`（实测值 0）+ `status:"completed"`——§4.1.1 结论属实。

### 维度 4 — 证据强度标注纪律〔覆盖〕：**通过**

§4 标注（`[已实测]` / `[自述]` / `[推断]` / `[未实测 / 待定]`）名副其实。§4.3（`spawn_agent` schema）老实标 `[自述]`，
明确写"**未见** `background` / `timeout` / `permission` 键——但**未证实不存在**"、"落地代码按『schema 可能不全』处理"。
#### BDD-24: 把纪律转成可验证判据（"明确标注为 `[自述]`；不把『未见…字段』表述为『确认无』；指明穷尽 schema 是待执行
项"）；#### BDD-30: 把"令模型逐字输出内部 tool schema 此法不可用（模型拒绝）"登记进 §7 并要求 P5-P6 换法。

### 维度 5 — 范围锁定〔覆盖〕：**通过**

§5「未发现需超四交付面」独立核验成立：`CommandRecord` IR 十字段足以表达 Codex 语义（`exit ← item.exit_code` 数字、
`ts_start/ts_end ← started_at_ms/completed_at_ms` epoch ms、`command ← item.command` 数组、`output_hash ←
_sha1_hex(aggregated_output)`，无需扩 IR）；检测引擎三态判据平台无关（S1 已证 CLI choices 动态）；阈值平台无关；
既有三适配器不动（#### BDD-21: 锁定）；§5 保留逃生阀。

### 维度 6 — 真机验证清单四要素〔覆盖〕：**通过**

§7 表 V1-V8 每项均写全「验证什么 / 怎么验（含具体命令）/ 阶段 / 通过判据（二值）/ 本机可做？」五列。V2（`spawn_agent`
穷尽 schema）给三条换法 + 判据；V4（截断标记形态）命令 `yes | head -c 500000` 经 `codex exec` + 判据（同时是
#### BDD-7: fixture 来源）；V8（API-key 账号 model 阵容）标"❌ 待有该环境时补（非阻塞）" + `verification_env_budget:
止损轮次 2`——按 P1 卡片「verification_env vs supplementable 边界判断树」属"运行环境"问题、走 `verification_env` 声明，
**本轮修订点 1 已移除 capability 侧冗余镜像条目**，声明方式现完全正确。#### BDD-29: / #### BDD-30: 把 §7 完整性转成
可判定门槛。

### 维度 7 — capability_requirements 三态〔覆盖〕：**本轮 CLOSED**

第 1 轮阻塞理由（`codex-api-key-account` 条目 `status: available` + `available: []` 与 note/实际/仓内先例
TAG0006 `gui-e2e-framework-win` / TAG0009 `真 Windows 执行环境` 均 `status: supplementable` + `gap_note` 矛盾）
已随该条目整体移除消解。现 `capability_requirements` 仅 `codex-cli-installed-authenticated`（`status: available`，
本机确有，不矛盾）。API-key 账号 model 阵容改由 `verification_env` + `verification_env_budget` + §7 V8 +
#### BDD-26: / #### BDD-29: 承载——机制归类正确（环境问题非能力问题）。

### 维度 8 — frontmatter 机器字段〔覆盖〕：**通过**

`domains: [backend]`（无用户可见页面 / 渲染产线，无需 UX BDD / vision 条目）、
`packages: [agate-scripts, agate-docs, agate-tests]`（与 §3 / §9 改动面吻合：agate-scripts↔adapters.py；
agate-docs↔platform-notes.md + SETUP.md；agate-tests↔test_agate_cmdstream_adapters.py + fixtures/cmdstream/）、
`risk_level: medium`（新适配器完全增量 + 强回归底线，但改协议本体 + 触发 SELF-GATE，取 medium）、
`ceremony: standard`（不申请 thin，fail-closed）、`phases: [P1..P8]` 全保留（§9 逐阶段理由成立）。
`check-frontmatter.py` exit 0。

### 维度 9 — 覆盖维度标注

本次评审覆盖：BDD 质量（维度 1）/ 同类扫描（维度 2，含 S4 精确断言独立复跑 + repo 全量扩查）/ 时效性（维度 3，
含 P0-brief 回写一致性核对）/ 证据强度（维度 4）/ 范围（维度 5，含十字段映射逐字段 + 真机抽验）/ 真机清单
（维度 6，含 verification_env 边界判断树）/ 能力声明（维度 7）/ frontmatter（维度 8）。

隐含需求维度标注（角色 checklist 口径）：
- 数据维度：✔ 覆盖（§2 + #### BDD-9: 畸形行 / #### BDD-6: 未结束命令 / #### BDD-8: 非 shell 工具事件 /
  #### BDD-10: session_id 一致性；Codex rollout 为外部只读、无迁移问题）
- 前端维度：N/A（`domains: [backend]`，无用户可见页面——已核实）
- 多端维度：✔ 覆盖（#### BDD-13: ~ #### BDD-17: 经 CLI `detect --platform codex` 通路 + §2 多端行确认 CLI
  choices 动态纳新键）
- 边界维度：✔ 覆盖（#### BDD-5: 非 0 exit / #### BDD-6: pending / #### BDD-7: 截断 / #### BDD-9: 畸形 /
  #### BDD-12: 子会话 id ≠ 父 session_id）
- 兼容维度：✔ 覆盖（#### BDD-25: 新旧 Codex 内容不自相矛盾 + 标时效；#### BDD-19: 注册表断言改包含式；
  既有已知局限登记不新造）

**未覆盖 / 未逐一深挖**（显式说明）：真机 codex 命令按 dispatch-context 授权"按需抽验"（抽验了目录结构、
`CommandExecution.exit_code`、子会话 `session_meta` 父子字段、:371 负向断言体、`check-frontmatter.py` exit 0）；
未复跑 `codex exec --json` 实时流 / `codex features list` / 现场 `spawn_agent` 派发（转 P5 V3/V5 回归复核）；
未跑全量 `pytest`（#### BDD-18: 以实际 exit 0 为准，已带 xdist flake 免责）；未独立评估 §8 三条 `[SUGGEST]` 之外
的 P2 设计取舍（属 P2 职责）。

---

## 非阻塞项确认（沿用第 1 轮，合理即可）

- `[SUGGEST]` ① 注册表键名 `"codex"`：与 `CommandRecord.platform` 标识、research 文档、CLI 名一致——无技术硬伤。
- `[SUGGEST]` ② `read_commands` 只以 rollout JSONL 为源、`codex exec --json` 实时流后置 / out-of-scope：
  §4.5 对比表推理成立——`--json` 实时流事件不带 per-item 时间戳，`detect()` 需要 `ts_start`/`ts_end`。无技术硬伤。
- `[SUGGEST]` ③ 截断标记 P5 V4 实测前用比照 `DSHAdapter._detect_truncated` 的保守双信号：不阻塞 P2/P3、实测后
  收敛——合理（本轮修订点 3 已把此来源写进 #### BDD-7: Given）。

---

## 本轮结论

**status: approved。** 3 修订点（修订点 1〔阻塞〕/ 修订点 2〔非阻塞〕/ 修订点 3〔非阻塞〕）全部 **CLOSED**；
第 1 轮已通过的 8 维度对应产物抽查**无回归**；BDD 仍 30 条连续、frontmatter 五机器字段未变、
`[NO_NEED_CONFIRM]` / `[PROD_NOT_TOUCHED]` 仍在、§4.1.1 `[P0_STALE]` 段 + §4.6 + §5 未被波及。
P1 需求基线可进入 P2。

---

## 独立核验命令留痕（本轮）

```
python3 agate/scripts/check-frontmatter.py .../P1-requirements.md              → EXIT=0
grep -c '^#### BDD-' .../P1-requirements.md                                    → 30
grep -oE '^#### BDD-[0-9]+' .../P1-requirements.md                             → BDD-1..BDD-30 连续
grep -nE 'codex-api-key-account' .../P1-requirements.md                        → 无命中（整条已移除）
grep -nE 'capability_requirements|codex-cli-installed-authenticated|verification_env' .../P1-requirements.md
                                                                              → capability_requirements 仅 1 条；verification_env + verification_env_budget line 21-22 保留
grep -n 'for platform_word' agate/tests/unit/test_agate_cmdstream_detect.py   → 371: for platform_word in ("claude", "opencode", "dsh"):
sed -n '362,372p' agate/tests/unit/test_agate_cmdstream_detect.py             → assert platform_word not in joined.lower()（负向断言，test_bdd_24，加第四键不破）
sed -n '85,87p' .../P1-requirements.md                                        → S10 补 test_bdd_7_fixture_sanitized 脱敏清单半句；S12 整行已在
sed -n '299,302p' .../P1-requirements.md                                      → BDD-7 Given 含"P4 保守双信号兜底 fixture、P5 V4 收敛"；When/Then 语义未变（truncated is True + output_hash is None）
```

`[PROD_NOT_TOUCHED]`
