---
phase: P7
task_id: TAG0042
type: consistency
parent: P2-design.md
trace_id: TAG0042-P7-20261006
status: draft
created: 2026-10-06
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0
deviation_count: 0
deviation_critical_count: 0
design_gap_count: 25
design_gap_reviewed_count: 25
code_map_new_files_count: 16
code_map_reviewed_count: 16
---

# P7 一致性交叉检查 — TAG0042 项目形态命令化 + 规则脚本化

> 审查对象：`P1-requirements.md`（22 BDD）/ `P2-design.md`（§1.1 M1-M20 / §4 / §6.1b / §11）/ 
> `P4-implementation.md` + `P4-implementation-batch1..6.md` / `P6-acceptance.md` / `P6.5-judge-verdict.md`
> / `agate-workspace/agents/CODE-MAP.md` / `agate-workspace/decisions/`（不存在）。
> 协议版本 v0.78.3（`AGATE_ROOT=/home/kity/.agate/v0.78.3/agate`）；HEAD `b884ac9`（P6/P6.5 已落）。
> 只读审查：未修改任何 P1-P6 产出、代码或协议文件。

## 1. DESIGN_GAP 配对（硬要求）

P4 正文声明 **25 条** `- [DESIGN_GAP: ...]`（`P4-implementation.md` 聚合；batch1=2 / batch2=4 /
batch3=2 / batch4=6 / batch5=5 / batch6=6）。以下**逐条转抄**并各配 `[DESIGN_GAP_REVIEWED: ...]`
裁决（接受 / 交 P8 / 属已知偏离），配对率 **25/25**。

- [DESIGN_GAP: batch1 — P2 §1.1 M3 只说「UPGRADING.md 新增批 1 行为变更记载」，未指定版本节标题；实现自主采用 `### v0.79.0`（当前 badge v0.78.3 的下一 minor），P8 发版时若版本号不同需同步。]
- [DESIGN_GAP_REVIEWED: batch1-M3 接受，交 P8 — 版本节标题属发版时点信息，P8 发版时以实际 `N.N.0` 同步（P2§1.1 M3 未定标题，实现取 badge+1 minor 为最小合理默认；不影响 BDD-2 判定）。]
- [DESIGN_GAP: batch1 — P2 §1.1 M1 只点名去除 `_advance` 的预写 + `git add`，未指明其孤儿辅助函数；实现自主删除仅服务该路径的 `_write_state()` / `_git()`（避免死代码），并保留 `_advance` 的 `repo_root` 形参以兼容既有调用点。]
- [DESIGN_GAP_REVIEWED: batch1-M1 接受 — 属最小实现决策：删死代码不改变 BDD-1/BDD-2 可观测行为，保留形参避免调用点回归；P4 implementation 与 P2 设计意图（去预写 + 去 git add）一致。]
- [DESIGN_GAP: batch2 — P2 §4.1 正文一句写「迁移期 validate 对文件缺失只输出 WARNING 返回 0」，与同节 N2 伪代码（validate rc≠0 才触发 gate_p0 的 WARNING）及 P3 用例 TC-B8-01/02 矛盾；实现按 N2 伪代码与 P3 用例：validate 对缺失/非法返回非 0，gate_p0 吸收为 WARNING 且恒 return 2。]
- [DESIGN_GAP_REVIEWED: batch2-§4.1 接受 — P2 内部文本自相矛盾（正文一句 vs N2 伪代码 + P3 用例），实现选择**可二值判定**的 N2 口径；BDD-8「行为与现状一致 + WARNING + 不 exit 1」仍成立（gate_p0 恒 return 2）。建议后续设计文本修正该句（非阻断）。]
- [DESIGN_GAP: batch2 — P2 未指定 `agate-config validate` 的 schema 校验实现方式；实现自主采用脚本内 draft-07 子集递归校验（标准库 + 数据驱动，不引入 jsonschema 依赖），未复用 `check-yaml-schema.py`（其为 `check-*.py` 且带 `if __name__` 侧效应，导入成本高于本批所需）。]
- [DESIGN_GAP_REVIEWED: batch2-schema 校验方式 接受 — stdlib-only 与仓库依赖约束（AGENTS.md 依赖清单）一致；避免导入带副作用的 `check-*.py`，与 §4.1「与既有 4 schema 同构」目标不冲突，BDD-5 用例已覆盖非法枚举/未知字段。]
- [DESIGN_GAP: batch2 — P2 §1.1 M7 未指定 install-hook 自动 init 的实现路径；实现自主选择「子进程调 agate-config init」而非在安装器内联模板，以保持声明模板的唯一实现（与 BDD-6 单源精神一致）。]
- [DESIGN_GAP_REVIEWED: batch2-M7 接受 — 唯一实现路径符合 BDD-6「无第二处解析实现」精神，避免安装器与 agate-config 双份模板漂移；BDD-7 幂等用例 PASS。]
- [DESIGN_GAP: batch2 — P2 §4.1 要求 read_project_config 对缺字段填默认值，同时 §1.1 M5 schema 声明 required；validate 只经该唯一读取函数取值（TC-B6-04 禁旁路解析），故拿到的是已注入默认值的 dict，required 字段在当前声明结构下恒满足（required 判据不触发）；实现按 P2 保留默认注入（最小实现），未额外暴露「已声明键集合」以驱动 required。]
- [DESIGN_GAP_REVIEWED: batch2-defaults vs required 接受 — 属已知偏离：默认注入使 required 判据在当前结构下不触发，但 BDD-5/BDD-6 的 Then（拒绝非法字段/枚举、单源读取）均由其它路径满足；「已声明键集合」驱动 required 记为后续增强候选（交 P8 观察，非阻断）。]
- [DESIGN_GAP: batch3 — P2 §4.2 / M10 列有「修正 formatter 计数」，但未指明缺陷、落点或判据，且 P3 未写任何覆盖该点的用例（无对应 BDD）；实现前查明仓库内无一处存在可复现缺陷（改动 `_fallback_json` 计数将改变 TDD 判定路径，违反 P2 §1.2 N3「不改 TDD 判定语义」），故本批未做该项变更，留待主 Agent 裁决落点。]
- [DESIGN_GAP_REVIEWED: batch3-formatter 计数 接受 — P4 以证据（无可复现缺陷 + 改动会违反 N3）说明不做，优于盲改；无 BDD 覆盖该点，不构成 BDD 缺口。记为后续债务候选（若将来发现真实缺陷再定落点），交 P8 登记。]
- [DESIGN_GAP: batch3 — P2 §4.2 写 `agate-run <cmd-key|命令>`，但 `project-config.schema.json` 的 `verify.commands` 为字符串数组、无命名 key；实现将 CLI 实参按声明中的命令文本精确匹配解析，并以该命令在数组中的下标作为证据槽位 key（`cmd-<n>.out`）——下标在命令文本变更后稳定，使 BDD-10-03 成立；若后续需命名 key，须先扩展 schema。]
- [DESIGN_GAP_REVIEWED: batch3-CLI 解析 接受 — 以数组下标作证据槽位 key 使 BDD-10（`--baseline` 落 `.out` + 逐字节比对）可二值判定；「命名 key」若需要须先扩 schema（P2 未定义），记为后续扩展候选，不影响本批 BDD-9~12。]
- [DESIGN_GAP: batch4 — 批 4「提交类型 → 关卡集合」的具体成员与转换表属 P2 §11 预留的设计未定面；P4 落定 code-only=全链 / docs-only=[P0,P1,P2,P7,P8] / release=[P7,P8]；P7 逐条审查。]
- [DESIGN_GAP_REVIEWED: batch4-转换表 接受 — P2 §11 明确预留此未定面（「批 4 的关卡层转换表矩体…P4 implementer 应标 DESIGN_GAP」）；三集合互不相同、含 `paused_from`，BDD-14 用例 PASS，属设计授权的实现决策。]
- [DESIGN_GAP: batch4 — phases.schema.json 不在 §6.1b batch4 output 列，但 phases.yaml 新增顶层键在 additionalProperties:false 下必须同步 schema（P2 §1.1 M11 已条件预见）；P4 已扩展，交 P7 核对。]
- [DESIGN_GAP_REVIEWED: batch4-phases.schema 接受 — P2 §1.1 M11 括号「+ `rules/schema/phases.schema.json` 若需扩展」已条件预见；`additionalProperties:false` 下不同步即 schema 校验失败，故扩展为必要条件，与 §6.1b output 列的遗漏属设计登记不全（非实现偏离）。]
- [DESIGN_GAP: batch4 — WORKFLOW.md 不在 §6.1b batch4 output 列，但 S-1（YAML↔WORKFLOW 名称一致）强制同步 P8 行名称；P4 已同步，交 P7 核对。]
- [DESIGN_GAP_REVIEWED: batch4-WORKFLOW.md 接受 — S-1 一致性门禁（`check-structure-consistency.py`）强制 YAML↔WORKFLOW 名称一致，不同步即 ERROR；P4 同步属必然动作，§6.1b output 列遗漏属设计登记不全（非实现偏离）。]
- [DESIGN_GAP: batch4 — delivery 合法取值集合设计未定；gate_p8 只查留痕存在（`"delivery:"` 子串），内容任意放行；P7 裁决是否收紧取值校验。]
- [DESIGN_GAP_REVIEWED: batch4-delivery 取值 接受（暂不收紧） — BDD-15 的 Then 只要求「未声明拦截、声明后放行」，未要求枚举取值；收紧取值属**新增需求**（P1 无对应 BDD），按「不为未覆盖需求扩范围」暂不收紧，记为后续增强候选交 P8。]
- [DESIGN_GAP: batch4 — 发版逻辑消费方散布于判定脚本/数据面/卡片/角色/叙事/CI 六面；本批只提供 preset 等价物 + WARNING，未删除任何发版逻辑；「是否/何时删除、收敛顺序」交 P7 裁决（截止版本 v0.80.0 已写 UPGRADING）。]
- [DESIGN_GAP_REVIEWED: batch4-发版逻辑删除 接受（本任务不删） — BDD-21 只要求「删前先提供等价 preset」，P4 已提供 `preset: semver-changelog-tag` + 发版痕迹 WARNING + UPGRADING 写迁移与截止版本 v0.80.0；实际删除是截止版本后的独立变更，不在本任务范围（P1 §1 分批判未含删除动作），交 P8 记录。]
- [DESIGN_GAP: batch4 — P8 叙事面（state-machine.md「P8 是发布准备」节、dispatch-protocol.md P8→READY 表、role-system.md、implementer.md）仍写「发布准备」，不在 §6.1b batch4 output 列，P2 未指定是否随名称改述；本批只改 phases.yaml/WORKFLOW/卡片，P7 裁决是否统一叙事。]
- [DESIGN_GAP_REVIEWED: batch4-P8 叙事面 接受（记为待办） — BDD-15 只要求 phases.yaml 语义=交付收尾 + 卡片记载；叙事面文档不在 §6.1b output 列，P2 未指定统一。属已知偏离：四份叙事文档与 phases.yaml 名称暂不完全一致。记待办交 P8（或后续任务）统一改述，非阻断。]
- [DESIGN_GAP: batch5 — agate-ci-verify 调用接口 P2 §4.4 未固化；P4 取「无参数 + cwd 定位（仓库根 .state.yaml 优先，其次任务级 .state.yaml）」，未采用 AGATE_TASK_DIR 注入点；多个任务级 .state.yaml 时判「歧义」并显式 SKIP（本仓多任务 ⇒ 实际会 SKIP）——「如何唯一定位本仓待兜底任务」交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch5-ci-verify 定位 接受 — 显式 SKIP + 原因满足 BDD-16「『跳过』与『通过』输出可区分、无假绿」；P2 §4.4 未固化接口，实现取保守口径（歧义即 SKIP 而非误判）。「唯一定位」属接口细化（P2 未定），记为后续增强候选交 P8，非阻断。]
- [DESIGN_GAP: batch5 — agate-doctor 退出码语义 P2 仅写「退出码固定」；P4 按 P3 DESIGN_GAP-2 解释「成功 = 诊断正常完成」⇒ rc 恒 0（报告问题 ≠ 自身失败），与 TC-B17-08 一致；若设计意图为「发现异常即非 0」则须改 TC-B17-08，交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch5-doctor 退出码 接受 — P2 §4.4 只写「退出码固定」，P4 取「诊断完成即成功 ⇒ rc 恒 0」与 P3 用例 TC-B17-08 一致；BDD-17 Then「成功退出码固定」满足。若改「异常即非 0」则需同步改 P3 用例（本任务不做），记为后续候选，非阻断。]
- [DESIGN_GAP: batch5 — 退役 backstop 的独立 P3 check-tdd-red 与 P6 provenance CI 层重跑未移植到 agate-ci-verify（BDD-16 只要求「实际重跑 gate 判定」，P3 契约 6 例只覆盖 gate 重跑 + 跳过可区分；P6.5 judge/events 已由 check-gate.py P6.5 覆盖）；「是否补回 provenance / P3-TDD-red 兜底」交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch5-未移植兜底 接受（暂不补） — BDD-16 Then 只要求「实际重跑 gate 判定 + 跳过可区分」，未要求 provenance/TDD-red；P6.5 judge/events 已由 `check-gate.py` P6.5 承载。补回属扩范围（无对应 BDD），记为后续增强候选交 P8。]
- [DESIGN_GAP: batch5 — 派发清单退役同步面未列 `agate/assets/formatters/README.md`，但它属 CHECK10-scan（PROTOCOL_DIRS）且引用退役名 ⇒ 若不改将新增 CHECK10 ERROR；P4 已同步（属退役同步，非新增需求）。]
- [DESIGN_GAP_REVIEWED: batch5-formatters/README 接受 — 属退役同步（CHECK10-scan 面必须同步引用，否则新增 ERROR）；P4 已改，P5/P6 consistency `--strict-errors-only` 0 ERROR 佐证；非新增需求。]
- [DESIGN_GAP: batch5 — workflow job 名保留 `gate-backstop`（M15 只要求改调用脚本）；「是否一并改名（如 ci-verify）」P2 未指定，交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch5-job 名 接受（暂不改名） — P2 §1.1 M15 只要求「job 改调 agate-ci-verify.py」，未要求改名；改名属未覆盖需求且会波及分支保护 required check 名，暂不改，记为后续候选交 P8，非阻断。]
- [DESIGN_GAP: batch6 — 外部审计的 160 项逐条清单不在仓库（P0-brief §四）⇒ 本次按 P0-brief fallback 从协议本体重新盘点，得 123 条（M60/C33/R30），与外部 160 项（M38/C29/N70）不可逐条对齐；差异原因见 batch6 §2.3（分类语义 M/C/R vs M/C/N、颗粒度、不可绕开路径判据更宽）——条目边界由本次盘点定义，交 P7 裁决是否可接受。]
- [DESIGN_GAP_REVIEWED: batch6-160 vs 123 接受 — P0-brief §四明示 fallback「没有就得重新盘点」；P1 BDD-18 Given 已按用户 2026-10-06 批准的基线变更改为「按 fallback 重新盘点」；P6.5 judge PASS。差异原因已登记，条目边界由本次盘点定义可接受。]
- [DESIGN_GAP: batch6 — 三态归宿 M/C/R 的判定边界 P2 §4.5 未逐条定义；P4 自主判定——M=脚本在不可绕开路径（pre-commit/check-gate/check-*.py 门禁）执行，C=有命令但依赖主 Agent 记得运行，R=判断类交强制独立评审；此边界为本次实现决策，交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch6-M/C/R 边界 接受 — P2 §4.5 只给三态语义（M/C/R），未逐条定义边界；P4 的「不可绕开路径」判据与 P0-brief §一（脚本在不可绕开路径上执行）一致且可复现（`check-obligations.py` exit 0）；属设计授权的实现决策。]
- [DESIGN_GAP: batch6 — 外部审计第三态 N「无任何脚本」在三态归宿中归 R（强制评审）——BDD-18 要求「无『无归宿』项」，而 P0-brief「不为判断类义务强行脚本化，那些交给强制评审」支持 N→R；但「现状无脚本」与「归宿为强制评审」是否等价，P2 未明确，交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch6-N→R 接受 — P0-brief §三「不为判断类义务强行脚本化，那些交给强制评审」直接支持 N→R；BDD-18 Then 只要求「每项有明确三态归宿、无无归宿项」，N 归 R 满足；P6.5 judge PASS。]
- [DESIGN_GAP: batch6 — 基线 M 占比 0.4878 由本次重新盘点自定（`baseline: {m: 60, total: 123}`），与外部审计 24% 不可比；基线一旦写入，后续只增不减——基线取值的合理性交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch6-基线 0.4878 接受 — 基线口径与本次盘点同源（60/123），BDD-19「current ≥ baseline（只增不减）」可二值判定；与外部 24% 不可比属已登记的口径差异（见上条）。取值合理性由「只增不减」护栏承载，可接受。]
- [DESIGN_GAP: batch6 — check-obligations.py 的协议根解析取「AGATE_ROOT env → 脚本相对协议根 → cwd」，未用 `agate_common.resolve_agate_root`——因 v0.73.0 版本布局后稳定版（~/.agate/current）与开发 checkout 解耦，resolve_agate_root 会解析到稳定版目录而扫不到本 checkout 的登记表；该解析口径 P2 未指定，交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch6-协议根解析 接受 — 理由与本机版本布局事实一致（AGENTS.md「本机稳定版布局」：稳定版来源 `~/.agate/current/`，与 checkout 解耦）；脚本相对优先使派发自跑命中本 checkout，P6 实测 exit 0 佐证；P2 未指定，属实现决策。]
- [DESIGN_GAP: batch6 — check-obligations.py 无独立 P3 红灯测试（P3 批 6 的 tests_filter 用既有 SG.6），BDD-18/19 的专门用例未由 P3 产出；P4 已用合成树手工验证两类负向，「是否补正式回归测试」交 P7 裁决。]
- [DESIGN_GAP_REVIEWED: batch6-无独立 P3 红灯 接受（记待办） — 当前判定逻辑由 SG.6（登记面）+ `check-obligations.py` exit code + P4 手工负向验证承载，BDD-18/19 可判定；缺正式回归测试属**已知偏离**，记为待办交 P8/后续任务补（非阻断，不影响本任务 BDD 判定）。]

**配对结论**：转抄 25 / REVIEWED 25，无遗漏；无一条升级为 `[BLOCKER]` 或 `[DEVIATION-CRITICAL]`。

## 2. SCOPE+ 闭环

- `P1-requirements.md` **无**行首 `[SCOPE_RESOLVED]`；全任务 `P1-P6` 产出亦无行首 `[SCOPE+]` 增补条目
  （P4-implementation-batch1/2 的 `## [SCOPE+]` 节内容均为「无」；batch3 提到的「SCOPE+ 消解轮」
  是 `check-events.py` docstring 注释的**就地**处理，未扩大 P1 基线）。
- ⇒ 本任务 P4 期**未产生任何 SCOPE+ 增补**，故无需 `[SCOPE_RESOLVED]`，SCOPE+ **平凡闭环**。
  与派发指引「本任务 P4 期无 `[SCOPE+]`」一致；`P2§11` 亦声明「设计未发现必须扩大 P1 范围的新隐含需求」。

## 3. 跨文件一致性

### 3.1 P2 packages vs P8 发布范围（P2§packages）

- `P2§packages` = `[agate-config, agate-run, agate-config-schema, gate-layer, agate-ci-verify,
  agate-doctor, obligations-registry]`（7 个），与 `P1-requirements.md` frontmatter `packages` **逐字一致**。
- `P8-release.md` **尚未产出**（本任务 P7 为当前最末阶段），无法对 P8 bump 范围做即时逐字核对。
  ⇒ 记为**前向核对项**：P8 必须读 `P2§packages` 确定 bump 范围（P8 卡要求「从 P2 packages 验证
  version 文件路径」），7 包全部纳入 bump；P7 不能提前裁决，非阻断。

### 3.2 P1 BDD 数 vs P6 验收 PASS 数（P1§BDD / P6§acceptance）

- `P1-requirements.md` 的 `#### BDD-NN:` 标题数 = **22**（实测 `grep -c`）。
- `P6§acceptance` frontmatter `pass: 22` / `fail: 0`，正文 `- PASS BDD-*` 行 = **22**，
  `Summary: 22/22 PASS`；`P6.5-judge-verdict.md` frontmatter `criteria_total: 22` /
  `criteria_passed: 22` / `status: passed`，`- PASS BDD-*` 行 = **22**。
- ⇒ **22 = 22 = 22**，1:1 全覆盖，无遗漏/无重复；数量与结论均匹配。

### 3.3 P4 implementation 路径 vs P2 方案设计（P4§impl-path / P2§1.1 M1-M20）

逐条对照 `P2§1.1` M1-M20 与 `P4§impl-path`（`P4-implementation.md` §2 各批一览 + 各批文件）落点：

| M | P2 落点 | P4 实际归属批 | 吻合 |
|---|---|---|---|
| M1 | `agate-next.py::_advance()` | batch1-phase-semantics | ✅ |
| M2 | phase-cards P2/P8 | batch1-phase-semantics | ✅ |
| M3 | `UPGRADING.md` 批 1 节 | batch1-phase-semantics | ✅ |
| M4 | 新增 `agate-config.py` | batch2-agate-config | ✅ |
| M5 | 新增 `project-config.schema.json` | batch2-agate-config | ✅ |
| M6 | `agate_common.py::read_project_config` | batch2-agate-config | ✅ |
| M7 | `agate-setup.py` / `install-hook.py` | batch2-agate-config | ✅ |
| M8 | `check-gate.py::gate_p0` | batch2-agate-config | ✅ |
| M9 | 新增 `agate-run.py` | batch3-agate-run | ✅ |
| M10 | `pre-commit-gate.py`（暂存账本 + formatter 计数） | batch3-agate-run（formatter 计数见 DG-batch3） | ✅（部分，见 DESIGN_GAP） |
| M11 | `phases.yaml` + `phases.schema.json` | batch4-gate-layer | ✅ |
| M12 | `check-gate.py::gate_p8` | batch4-gate-layer | ✅ |
| M13 | 新增 `agate-ci-verify.py` | batch5-ci-doctor | ✅ |
| M14 | 新增 `agate-doctor.py` | batch5-ci-doctor | ✅ |
| M15 | `.github/workflows/protocol-tests.yml` | batch5-ci-doctor | ✅ |
| M16 | 新增 `rules/obligations.yaml` | batch6-obligations | ✅ |
| M17 | 新增 `check-obligations.py`（进锚点表） | batch6-obligations | ✅ |
| M18 | `check-protocol-consistency.py` 加锚点 | batch6-obligations | ✅ |
| M19 | `UPGRADING.md` 迁移兼容（BDD-8/21） | batch2（迁移）+ batch4（preset 截止版本） | ✅ |
| M20 | 全仓 R6 差分（`/tmp` + peekview 只读副本） | 各批（BDD-20/22） | ✅ |

- **批切分与 `P2§6.1b` output 列**：各批实际改动文件与 §6.1b 预期一致；batch4 额外同步
  `phases.schema.json` / `WORKFLOW.md`、batch5 额外同步 `formatters/README.md`——均为门禁强制的
  必要同步（`additionalProperties:false` / S-1 / CHECK10-scan），已在对应 `[DESIGN_GAP]` 逐条登记。
- **依赖链**：`P2§6.1b` 声明的串行链（批 2 依赖批 1…）在 git log 中按 48091f2→18b3e3d→68a796e→
  fb56964→082aba3→b19a425 顺序落地，与 `P2§6.3` 模式 5 一致。
- ⇒ `P4§impl-path` 与 `P2§1.1` 逐条吻合（M10 的部分未做已由 DESIGN_GAP 显式登记，非静默偏离）。

## 4. 未决项清零

- `P1-requirements.md`：§5 为 `[NO_NEED_CONFIRM]` 行首声明，**无残留行首 `[NEED_CONFIRM]`**；
  含 1 条 `[SUGGEST]`（非阻塞倾向项）。
- 全 `P1-P6` 产出：**无 `[BLOCKER]` / `[DEVIATION-CRITICAL]`**（实测 `grep` 零命中）。
- `P6§acceptance` / `P6.5-judge-verdict`：客观 PASS/FAIL 二值，无 `[NEED_CONFIRM]`。
- 本 P7 产出：`blocker_count: 0` / `deviation_count: 0` / `deviation_critical_count: 0`。
- ⇒ **未决项清零**，无阻断项。

## 5. CODE-MAP 核对

对照 `agate-workspace/agents/CODE-MAP.md` 与 `P4-implementation.md`「新增文件核对表」（16 行）逐条核对：

| # | 新增文件 | P4 标记 | P7 核对结论 |
|---|---|---|---|
| 1 | `agate/scripts/agate-config.py` | UPDATED（批 2） | [CODE_MAP_SYNC: CODE-MAP.md:36「项目声明族」已登记] |
| 2 | `agate/rules/schema/project-config.schema.json` | UPDATED（批 2） | [CODE_MAP_SYNC: 由 rules 模块 `schema/*.json` 泛化覆盖 + 声明族记其消费方] |
| 3 | `agate/scripts/agate-run.py` | UPDATED（批 3） | [CODE_MAP_SYNC: CODE-MAP.md:37「执行层族」已登记] |
| 4 | `agate/scripts/agate-ci-verify.py` | UPDATED（批 5） | [CODE_MAP_DRIFT: CODE-MAP.md 无此条目（批 5 提交 082aba3 未改 CODE-MAP.md）] |
| 5 | `agate/scripts/agate-doctor.py` | UPDATED（批 5） | [CODE_MAP_DRIFT: CODE-MAP.md 无此条目] |
| 6 | `agate/rules/obligations.yaml` | UPDATED（批 6） | [CODE_MAP_SYNC: CODE-MAP.md:38「义务登记族」已登记] |
| 7 | `agate/scripts/check-obligations.py` | UPDATED（批 6） | [CODE_MAP_SYNC: CODE-MAP.md:38 已登记 + 已进 CHECK 9 锚点表] |
| 8-16 | 9 个 `agate/tests/unit/test_*.py`（`test_agate_config` / `test_config_schema` / `test_agate_run` / `test_events_ledger` / `test_gate_layer` / `test_check_p8_delivery` / `test_agate_ci_verify` / `test_agate_doctor` / `test_tag0042_batch1_phase_semantics`） | EXEMPT（纯测试脚手架） | [CODE_MAP_SYNC: 测试脚手架，CODE-MAP.md 不登记测试文件，P4 已标 EXEMPT] |

- **结论**：`code_map_new_files_count: 16` / `code_map_reviewed_count: 16`（逐条核对无遗漏）。
  其中 **14 条 SYNC**、**2 条 DRIFT**（批 5 的 `agate-ci-verify.py` / `agate-doctor.py`）。
- **DRIFT 定性（WARNING 级，不阻断）**：`CODE-MAP.md` 已含批 2/3/6 新增条目，但**未见批 5 的
  `agate-ci-verify.py` / `agate-doctor.py` 条目**；批 5 的退役对象 `ci-gate-backstop.py` 亦从未登记
  （`grep` 零命中）。与 `P4-implementation.md` 核对说明 + 批 5 `[DESIGN_GAP]` 提示一致。
  ⇒ 记**待办**：后续任务（或 P8 收尾）在 `CODE-MAP.md` 补批 5「CI/诊断族」两脚本条目
  （`agate-ci-verify.py` / `agate-doctor.py`）。**不阻断**本任务 P7 推进。

## 6. 架构决策落点

- `agate-workspace/decisions/` **不存在**（实测）。`P2§10` 亦记载「本仓 `decisions/` 不存在，P2 无需
  读既有决策」，本方案的跨任务决策（**声明层/执行层分离 + 唯一读取函数**）记录于 `P2§3`（候选 A）。
- 本任务**无被证伪的既有决策**需就地标注「已过时 + 被什么取代」。
- ⇒ 跨任务决策**未落 `decisions/`**：记**待办**（由决策提出方在下一次 P2 前补写入，见 DEBT0039），
  **不阻断**（派发指引明确「缺失记为待办（不阻断）」）。

## 7. 总结论

| 维度 | 计数 | 结论 |
|---|---|---|
| BLOCKER | 0 | 无阻断项 |
| DEVIATION-CRITICAL | 0 | 无关键偏离 |
| DEVIATION | 0 | 无一般偏离 |
| DESIGN_GAP 转抄/配对 | 25 / 25 | 逐条配对，无遗漏 |
| CODE-MAP 新增/核对 | 16 / 16 | 14 SYNC + 2 DRIFT（WARNING 级） |

**待办（不阻断，交 P8 / 后续任务）**：① 补 `CODE-MAP.md` 批 5 两脚本条目；② 跨任务决策写入
`decisions/`；③ batch4 P8 叙事面四份文档统一改述；④ batch6 `check-obligations.py` 正式回归测试；
⑤ batch3 formatter 计数落点、batch4 delivery 取值收紧、batch5 job 名改名/兜底移植等后续增强候选。

**P7 一致性交叉检查通过**：无 `[BLOCKER]` / `[DEVIATION-CRITICAL]`，DESIGN_GAP 全配对，SCOPE+ 闭环。
