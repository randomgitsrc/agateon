---
phase: P1
task_id: TAG0036
parent: P1-requirements.md
trace_id: TAG0036-P1-20260919
created: '2026-09-19'
agent: requirements-review
status: approved
---
# P1 需求基线评审（复审第 2 轮）— TAG0036 MVWU 阶段 1 试点

[PROD_NOT_TOUCHED] 只读评审；未修改 `P1-requirements.md`，未 git add/commit，未触碰 `~/.agate`；`agate/` 下无改动（`git status --porcelain agate` 为空，`agate/scripts/check-mvwu.py` 尚不存在，符合 P1 阶段）。

**结论：approved**。第 1 轮 F-1..F-9 经**独立实测**逐条闭合（非仅看「修订记录」自述）；71 条 BDD 编号连续、交叉引用语义指向正确；未新增第七项检查、未越出 P0-brief 范围；范围纪律（零内核改动 / 不挂 gate / 不替用户裁决提交粒度 / ⑤ 组只成文）仍成立。遗留 3 条 SUGGEST 级观察，均非阻塞，留给 P2/P3 吸收，不打回。

## 实测核实记录（独立抽样）

| 项 | 实测 | 判定 |
|----|------|------|
| `#### BDD-` 计数与连续性 | 71 条；编号 1..71 按出现顺序逐一对齐无跳号；全文最大引用 `BDD-71` 无越界 | 通过 |
| F-1 设计文档援引 | 打开 `docs/design-notes/design-mvwu-protocol.md`：§5.1.1「MVWU verdict 四态定义（本节为权威定义，§7.2 的 check 实现据此）」表第 343 行 `UNKNOWN` 触发条件确含"边界不可归属"；§7.3 示例表 C 行（合并 / 不可归属）verdict 确为 **UNKNOWN**；§7.2「六项检查（且仅此六项）」确无 boundary 项；P0-brief `--observe` 表 verdict 列确写"六项检查结果" | 援引准确（见 F-1 行） |
| F-3 git 范围实际推演（本仓库） | `git symbolic-ref refs/remotes/origin/HEAD` → `refs/remotes/origin/main`（口径 E 首选项可解析）；`git merge-base HEAD main` → `efb113b`；`merge-base..HEAD` 区间 = 2 个提交（d46adbc、c93a02d，非空）；对 `agate/scripts/check-gate.py`：**全历史 `git log -- <file>` = 18 个 commit**（若沿用 P0-brief 原式，"分散于多个 commit"恒成立，commit 形态恒 UNKNOWN），**区间内 = 0**（口径 E 下判"区间内从未被改动 → UNKNOWN"，且 BDD-47 特意构造"区间外更早提交不可见"作判别用例）。任务分支上的 P4 批 commit 落入区间，per-batch / merged 可正常区分 | 范围明确、可执行、消除了恒 UNKNOWN |
| F-3 附注 workspace 可配置 | `agate_common.resolve_workspace`（`agate_common.py:578`）确实按 `.agate.env AGATE_WORKSPACE=` → `AGATE_TASKS_DIR` → 默认 `agate-workspace` 解析，BDD-51/52 的"随配置排除"前提属实 | 通过 |
| F-6 引用的 DEBT/平台词 | `DEBT0014` 在 `agate-workspace/debt/tech-debt.md:530` 存在；`AGATE_PYTHON` 在 `agate/platform-notes.md` 存在；`AGENTS.md:91` 确有"每文件第 1 个用例 `windows_smoke`"约定，BDD-57 据此 | 通过 |
| 审声明 diff 证据 | `git diff --cached --stat`：仅 `.state.yaml` +`gate-events.jsonl`（2 文件，任务目录内）；P1 阶段尚无代码/协议文档改动，声明是对 P0-brief 范围的前瞻，见下「审声明」 | 匹配 |

## 第 1 轮 F-1..F-9 逐条闭合核对表

| 项 | 级别 | 修订处置（analyst 自述） | 独立核对结果 | 闭合 |
|----|------|----------------------|--------------|------|
| F-1 | MUST | §2-5 / SUGGEST-2 如实援引 §5.1.1 权威表与 §7.3 C 行，明示"有意偏离"，限定阶段 1 观测口径，阶段 2 与提交粒度决策一并复议 | 实测设计文档：§5.1.1 权威表 `UNKNOWN` 含"边界不可归属"（:343）✓、§7.3 C 行 verdict=UNKNOWN ✓，两处援引与原文一致；不再称"读法不同"；§2-5 明文"对设计文档 §5.1.1 的有意偏离""限定为阶段 1 观测口径""由阶段 2 与提交粒度决策（P0-brief 决策 A/B，用户裁决）一并复议""BDD-42 只固化阶段 1 口径，不预裁阶段 2 门槛"；§5、§8 同步；BDD-42 标题标注口径、正文不变（PASS + boundary UNKNOWN 两模式一致）。无需升级 NEED_CONFIRM | **闭合**（BDD-42、BDD-55） |
| F-2 | MUST | 新增口径 D 输出转义 + BDD-22/44 | 口径 D 给出确定规则：id 逐 UTF-8 字节 `\xNN`、非字符串/空 → `?`；`tests_filter` 按 GFM：`\`→`\\`、`\|`、`` \` ``、换行→字面 `\n`、CR→`\r`、其余 C0→`\xNN`；"按 GFM 规则（`\` 转义下一字符）切分恰 7 列"。逐字核对 BDD-44 期望值与规则一致（`\|`、`` \` ``、`C:\\t`、字面 `\n`），且换行与"真反斜杠 n"（`\\n`）可区分；BDD-22 五种 id（含空格 / `\|` 型管道 / `../e` / 合规 / 空串）的期望 `a\x20b`、`x\x7cy`、`..\x2fe`、`ok-1.2_3`、`?` 与规则逐一吻合；含 `\|` 时七列契约成立（BDD-43/44）。二值可判 | **闭合**（BDD-22、BDD-43、BDD-44） |
| F-3 | MUST | 口径 E：`merge-base HEAD <默认分支>..HEAD`；基线不可确定/区间空 → UNKNOWN + stderr `baseline`；写入 BDD-47/48/49/50 Given | 范围写入 BDD-47/48/49/50/51 的 Given 并含判别用例（BDD-47 区间外历史提交不可见）；本评审用本仓库实际推演（见上表）：origin/HEAD→origin/main、merge-base=efb113b、区间 2 commit；check-gate.py 全历史 18 commit 对区间 0 commit，证明取全历史时的恒 UNKNOWN/恒分散问题在新口径下不再出现；已知局限（合并回主线后回顾性采集恒 UNKNOWN）在隐含需求 12 与 §8 诚实声明，BDD-56 仅要求 7 列结构而不要求非 UNKNOWN，不自相矛盾；BDD-50 覆盖基线不可确定与区间为空两种降级 | **闭合**（BDD-47..52） |
| F-4 | MUST | 口径 C：单行 flow 序列 + 双引号 node id + 精确字符串相等；不可解析 → `UNKNOWN reason=expected_red`；BDD-30/31/32 | 列表编码、元素相等口径（逐字节 node id 相等）、`[]`/缺省等价、不可解析定义、四分支 verdict 判定均给出；BDD-30（含 `[a,b-1]` 参数化 id → EXPECTED_RED）、BDD-31（`[a,b-2]` 近似 id → FAIL）、BDD-32（非序列/截断/非字符串元素 → UNKNOWN reason=expected_red，exit_code 0/1 均可）逐条可二值判定；BDD-27/28 示例已改引号 node id；BDD-10 同步要求写入方遵守编码 | **闭合**（BDD-10、BDD-27..32） |
| F-5 | MUST | 旧 BDD-27 拆 36/37；旧 BDD-29 拆 39/40；合并冗余；全量重排 | BDD-36（四态均 exit 0）与 BDD-37（无参数/目录不存在 → exit 2，含 `--observe` 变体）各一组 GWT；BDD-39（四种无可判定批输入，**输出完全相同**：一行 `UNKNOWN batch=- reason=tests_filter`）与 BDD-40（证据损坏三种，输出相同）各一组 GWT。"多输入同一 Then"的等价类写法与首轮已判通过的 BDD-14 同构，非"多场景不同期望"；拆分后编号连续（见上）。旧 BDD-30 已并入 BDD-39 | **闭合** |
| F-6 | SHOULD | 口径 B 固定 reason 顺序并列覆盖面；BDD-34；口径 G `git_head` 格式；重复 id / 非字符串 id / 自相矛盾证据各有处置 | 口径 B 顺序 tests_filter → evidence → command → exit_code → git_head → expected_red 显式；BDD-34 六批（P/Q/R/S/T/U）逐批推演：P 缺 tests_filter→`tests_filter`；Q 双故障→`command`；R→`exit_code`；S→`git_head`（早于 expected_red）；T/U 重复 id→均 `evidence`——与口径 B 一致；口径 G（全长 40/64 位十六进制 + 存在的 commit）→ BDD-24 扩展；自相矛盾证据 → BDD-33（`reason=exit_code`），与口径 C"任一不可解析→expected_red"不冲突（不可解析时无法判断矛盾，落 expected_red，顺序确定）；空 id → `?`（BDD-22）。处置合理 | **闭合**（BDD-22/24/33/34）；见 SUGGEST-B |
| F-7 | SHOULD | BDD-9 去条件标题；两脚本 git diff 均为空 | BDD-9 标题无条件；措辞修正，并注明 `_TASK_FRONTMATTER_FIELDS` 仅存在于 `check-structure-consistency.py`（与 §4.2 表一致） | **闭合**（BDD-9） |
| F-8 | SHOULD | 文档类 BDD 各要点补字面标记；BDD-8 限定在示例值内部 | BDD-6/7/9/10/60-66 均以"字面：…"列出锚点，P3 可直接写 grep 断言；BDD-8 的 grep 收窄为 `tests_filter: *"[^"]*\bpython3\b`，同行别处的 `python3 agate/scripts/check-mvwu.py` 不计，且"AGATE_PYTHON/DEBT0014/不裸 python3"三选一锚点实测存在 | **闭合** |
| F-9 | SHOULD | 口径 F 定义首词语义；明示不比对 command 与 tests_filter；BDD-16/17/18 | 口径 F：跳过前导 `NAME=value`；`cd/export/set/source/.` 视为可解析且其后不检查；切分失败→`reason=command`；BDD-16（环境变量前缀，A 通过 / B 判 command）、BDD-17（`cd sub && no-such-runner-xyz` 不判 command，已知局限）、BDD-18（command 与 tests_filter 不一致仍 PASS）均二值可判；且**未新增第七项检查**，仅把"已知观测局限"以负向 BDD 固化 | **闭合**（BDD-16/17/18） |

## 新引入问题排查

1. **交叉引用（71 条重排后语义抽查）**：§0 → BDD-5（DEBT 登记）、BDD-62（Skeleton 消歧）✓；§2 各条 → BDD-39/56（兼容）、BDD-68（不回填）、BDD-69（计数）、BDD-34/24/32/33（多故障）、BDD-16/17/18（局限）✓；§4.2 → BDD-1/3/5/6/7/9/11/12/61/63/64/66/69 ✓；§4.3 → BDD-10/59/68/69/70 ✓；§4.5/§5 → BDD-10/27..33、BDD-42/55、BDD-9、BDD-57、BDD-60..66 ✓；BDD-35 引用的 UNKNOWN 场景集 `BDD-14/15/20/21/23/24/29` 均为 UNKNOWN 场景 ✓；BDD-55 引用 `BDD-25..29`（PASS/FAIL/FAIL/EXPECTED_RED/UNKNOWN 各态）✓；BDD-56 → BDD-43 ✓；BDD-57 → BDD-36/37、34、30/31/32、22/44、47..54 ✓；BDD-63/66 → "同 BDD-3 的空 diff" ✓；修订记录旧→新映射与现行编号一致。未发现指向错误。
2. **是否新增"第七项检查"**：口径 A 的 reason 词表仍是六个 token，`expected_red` 属检查 6 内部；新增的"批 id 不安全/重复""自相矛盾证据"分别落在既有 reason `evidence`、`exit_code` 之下（设计文档 §5.1.1 UNKNOWN 触发集本就含"证据缺失或损坏/路径不安全"）；"reason 优先级"仅是同一输入的确定性规则而非新检查。P0-brief"六项且仅此六项"仍成立。**判定：未越界**（见 SUGGEST-A，提示 P2 归口到检查 3/4，勿另立检查函数名/编号）。
3. **范围越界**：新增 BDD（16/17/18/22/30-34/44/50/52）均为 F-1..F-9 的直接落点；BDD-52（自定义 workspace 前缀排除）由实测 `resolve_workspace` 支撑，属 boundary 比对的必要口径，非新交付物。**无越界**。
4. **P1 纯净性 / 二值性**：新增口径 A-H 与 BDD 均是外部可观测契约（stdout 契约行、exit code、观察表列、诊断关键字 `baseline`、文件 diff），无函数名/数据结构/算法；无"⚠ 调整""部分通过"式中间态；BDD-34/22 虽含多批，但为同一次运行的单一 Then（逐行断言），不属"多场景多期望"。
5. **范围纪律**：零内核改动（BDD-3/5/12/67 空 diff 断言，含 `check-gate.py`、`phases.yaml`、`schema/`、hook 三件套、状态机、审计链）；不挂 gate（BDD-68①）；提交粒度决策留给用户（§8、SUGGEST-2 复议声明）；⑤-b/⑤-d 只成文、不含"已生效"（BDD-60/62）。**成立**。

## BDD 评审（新编号）

覆盖维度记号：数据 / 前端 / 多端 / 边界 / 兼容；✓=覆盖，—=本任务不涉及（无 frontend/mcp/security 域）。

- BDD-1: 通过；数据✓ 前端— 多端— 边界✓（含空格值需双引号）兼容✓
- BDD-2: 通过；兼容✓
- BDD-3: 通过（回归 + 内核零 diff）；兼容✓
- BDD-4: 通过（可选键逐批独立）；边界✓ 兼容✓
- BDD-5: 通过（DEBT 只登记不修）；兼容✓
- BDD-6: 通过（字面锚点齐备）；数据✓
- BDD-7: 通过（含既有"硬规则"四条逐字不变）；兼容✓
- BDD-8: 通过（grep 已收窄）；兼容✓（Windows 无 make）
- BDD-9: 通过；兼容✓
- BDD-10: 通过（含编码要求）；数据✓ 边界✓
- BDD-11: 通过；兼容✓
- BDD-12: 通过（登记面零改动）；兼容✓
- BDD-13: 通过；数据✓
- BDD-14: 通过；边界✓（缺失/空串/非字符串）
- BDD-15: 通过；边界✓
- BDD-16: 通过；边界✓
- BDD-17: 通过（已知局限）；边界✓
- BDD-18: 通过（已知局限）；边界✓
- BDD-19: 通过（哨兵文件法，可机械判定）；边界✓
- BDD-20: 通过；边界✓
- BDD-21: 通过（路径穿越）；边界✓
- BDD-22: 通过（打印形态）；边界✓ 数据✓
- BDD-23: 通过；数据✓
- BDD-24: 通过（口径 G）；数据✓ 边界✓
- BDD-25: 通过；数据✓
- BDD-26: 通过；数据✓
- BDD-27: 通过；数据✓
- BDD-28: 通过；数据✓
- BDD-29: 通过（UNKNOWN 不猜 EXPECTED_RED）；边界✓
- BDD-30: 通过（参数化 id）；数据✓ 边界✓
- BDD-31: 通过（精确相等反例）；边界✓
- BDD-32: 通过；数据✓ 边界✓
- BDD-33: 通过（自相矛盾证据）；边界✓
- BDD-34: 通过（优先级）；边界✓
- BDD-35: 通过（UNKNOWN≠PASS，见 SUGGEST-C）；数据✓
- BDD-36: 通过；边界✓
- BDD-37: 通过；边界✓
- BDD-38: 通过（只读）；边界✓
- BDD-39: 通过；边界✓ 兼容✓
- BDD-40: 通过；边界✓（空/非 UTF-8/无 kv）
- BDD-41: 通过；数据✓
- BDD-42: 通过（阶段 1 口径，有意偏离已如实声明）；数据✓
- BDD-43: 通过；数据✓ 多端—
- BDD-44: 通过（含 `|`/反引号/换行）；边界✓ 数据✓
- BDD-45: 通过（见 SUGGEST-C）；数据✓
- BDD-46: 通过；数据✓
- BDD-47: 通过（含区间外历史判别）；边界✓ 兼容✓
- BDD-48: 通过；边界✓
- BDD-49: 通过；边界✓
- BDD-50: 通过（基线不可确定/区间空）；边界✓ 兼容✓
- BDD-51: 通过；边界✓
- BDD-52: 通过（workspace 可配置）；兼容✓
- BDD-53: 通过；边界✓
- BDD-54: 通过（I1 诚实标注）；边界✓
- BDD-55: 通过；数据✓
- BDD-56: 通过（判据 6，真实任务跑通；兼容存量任务目录）；兼容✓ 边界✓
- BDD-57: 通过（单测覆盖面 + tmp_path + windows_smoke）；兼容✓
- BDD-58: 通过；兼容✓
- BDD-59: 通过（只增 5 行三列，不动既有行）；兼容✓
- BDD-60: 通过（字面锚点 + 不含"已生效"）；兼容✓
- BDD-61: 通过；兼容✓
- BDD-62: 通过（与 P2-skeleton 消歧）；兼容✓
- BDD-63: 通过；兼容✓
- BDD-64: 通过；兼容✓
- BDD-65: 通过（过时不删）；兼容✓
- BDD-66: 通过；兼容✓
- BDD-67: 通过（零内核，16 路径空 diff）；兼容✓
- BDD-68: 通过（不挂 gate、不回填）；兼容✓
- BDD-69: 通过（登记面/计数/CHANGELOG）；兼容✓
- BDD-70: 通过（SELF-GATE 收口）；兼容✓
- BDD-71: 通过（语义审查留痕）；兼容✓

## 隐含需求覆盖

- 数据维度：**覆盖**——证据日志格式与列表编码（口径 C、BDD-10/30/31/32）、`tests_filter` YAML 引号透传（BDD-1）、`git_head` 格式（口径 G、BDD-24）、观察表转义（口径 D、BDD-22/44）；对应隐含需求 2/3/4/12/13。无迁移需求（可选键，老任务无需回填）。
- 前端维度：**不涉及**（domains=backend，无 UI；无 frontend 故无 UX 类别 BDD / `ui_render_shape` / vision 能力声明，§6 已声明）。
- 多端维度：**不涉及**（无 API/MCP/前端契约；仅 CLI 与协议文档，隐含需求 10）。
- 边界维度：**覆盖**——空值/缺失（BDD-14/20/23/39/40）、路径穿越与不安全 id（BDD-21/22）、重复 id（BDD-34）、多故障并存（BDD-34）、自相矛盾证据（BDD-33）、git 观测范围（口径 E、BDD-47..50）、复合命令首词（BDD-16/17）、非 UTF-8/空证据（BDD-40）；并发/时区：脚本只读、timestamp 不参与判定，不涉及。
- 兼容维度：**覆盖**——`tests_filter` 可选键 + 缺省行为不变（BDD-2/3/4）、存量任务目录诚实 UNKNOWN 不崩溃（BDD-39/56）、既有 bootstrap 骨架机制撞名消歧（BDD-62）、既有 ADR/角色文本不删不改（BDD-7/65/60）、workspace 可配置（BDD-52）、Windows 冒烟（BDD-57/58）。
- 同类扫描：**已做实并落盘**（§4.1 命中数量+文件清单；§4.2 dispatch_plan 13 个消费方逐个"处理/不处理+理由"；§4.3 新脚本登记面；§4.4 ⑤ 组同义节/撞名；§4.5 结论含回归拦截手段）；首轮实测复核数字一致。
- P0-brief 时效性：§0 已逐条对照判据 1-3，无严重漂移，记录 4 条轻微 `[P0_STALE]` 并已由主 Agent 补记进 P0-brief；已核对，通过。

## 裁剪评审

- `phases: [P1..P8]` **不裁剪**：无跳过阶段；§7 给出 P3 保留（新脚本须 TDD）、P6.5 judge 由 `.state.yaml` 强制的理由；充分。
- `risk_level: medium`：新增独立脚本 + 多份协议文档、命中 SELF-GATE 触发面，但零内核改动、可选键、不阻断——medium 匹配；非 low（协议语义改动需 protocol-alignment-review），非 high（不触内核）。
- `capability_requirements: []`：无浏览器/网络/视觉需求，全部验证经 python3/pytest/git/grep，合理。

## 审声明（风险分级/裁剪声明 vs diff 证据）

- `risk_level: medium` / `ceremony`（未声明 → 缺省 standard，fail-closed，不薄化）/ `phases` 全阶段：与暂存区证据 `git diff --cached --stat`（仅任务目录内 `.state.yaml`、`gate-events.jsonl` 2 文件、+2/-1）及 P0-brief 范围（新建 `agate/scripts/check-mvwu.py` + `agate/**/*.md` 多文件 + 测试）相互一致；`agate/scripts/*.py` 与 `agate/**/*.md` 命中 SELF-GATE 触发面，BDD-70/71 已固化收口：**匹配**。
- `ceremony: full` → phases 含 P7：本任务未声明 full（缺省 standard），且 phases 仍含 P7：**通过**（不适用 full 专项校验，但含 P7 亦满足）。
- `domains: [backend]` 与实际（Python CLI + 协议文档）一致；`packages` 三项与改动面一致。
- `judge.enabled: true` 已在 `.state.yaml`（P1 基线确认），无需另声明。

## P1 纯净性

无解决方案设计混入：口径 A-H 为外部契约（输出行、exit code、转义结果、诊断关键字、git 区间定义），不规定函数拆分/数据结构/解析库；BDD-19"不 spawn command/tests_filter"、BDD-38"只读"为行为约束。P2 仍可自由选择实现。

## 非阻塞观察（SUGGEST，不打回，留给 P2/P3 吸收）

- **SUGGEST-A**：BDD-33（自相矛盾证据→`reason=exit_code`）与重复 id（→`reason=evidence`）是对检查 3/4 的语义扩展，P2 设计时应归口到检查 3/4 内部，勿另立"第七项检查"，并在 P2 设计中显式说明其口径来源为设计文档 §5.1.1 UNKNOWN 触发集。
- **SUGGEST-B**：BDD-22 的"非字符串 id 同样打印 `batch=?`"只在 Then 括注、Given 仅覆盖空串；P3 写测试时建议补一个 `id: 5` / `id: null` 的等价类用例。
- **SUGGEST-C**：BDD-17/18/35 的已知局限声明带"或等义表述"，P3 落测试时建议固定一个字面锚点（如"仅检查首词""不比对 command 与 tests_filter""UNKNOWN 不等价于 PASS"）；BDD-45 耗时列对非整数（如 `8.5`）的格式未定，P3/P2 落一个确定格式即可。

## 结论与回派

**approved**。第 1 轮 MUST 项 F-1..F-5 全部闭合、SHOULD 项 F-6..F-9 处置合理；无实质缺陷，无需第 3 轮。可推进 P1 gate（`check-gate.py P1` 预跑）与 commit。P1 retry 预算：本轮为复审 #1，通过，未再消耗。
