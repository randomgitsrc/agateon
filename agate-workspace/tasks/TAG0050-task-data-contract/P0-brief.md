# P0-brief — TAG0050 任务数据契约：结构化判定、可信写入与任务版本

> 主 Agent 亲自填写（P0 产出）。
>
> **设计依据**：`docs/design-notes/design-tag0050-task-data-contract.md`，以独立评审 APPROVE 为准。
>
> **配套文档**（均放在 `docs/design-notes/`）：
> - 实验需求：`exp-tag0050-task-data-contract.md`
> - 复现脚本：`repro-tag0050.sh`
> - 前置评审：`review-tag0042-implementation.md`（TAG0042 v0.79.0 实施评审）
>
> **关联 RM**：
> - **RM-AG0099**：本任务登记；
> - 吸收 **RM-AG0085**、**RM-AG0087**、**RM-AG0097**；
> - 吸收 **RM-AG0059 第①项**（`.state.yaml` 元数据），②③ 不在范围内。
>
> **承接 TAG0042 实施评审**：I-1、I-2（证据部分）、I-4、I-5、I-6、I-7、I-8。
>
> **独立评审**：`review-r1.md`（REJECT）→ `review-r2.md`（REJECT）→ `review-r3.md`（REJECT，仅 §2.4）→ `review-r4.md`（**APPROVE WITH CHANGES**；闭环确认中的 3 个 MAJOR 与残留 4 条 MINOR 均已落实到设计）。
>
> **性质**：协议内核演进。判定依据从"正文正则 + 自报汇总 + 可改开关 + 作者自标的分类"改为"按冻结契约快照登记的结构化字段与机械核验"。任务以账本创建事件记录契约等级。正则只保留为"命中即拦"的绊线。
>
> **范围**：只改 agateon 本仓。peekview 只在**只读副本**上检验。

```yaml
task: "任务数据按冻结的契约快照（rules/task-data/level-N.yaml）结构化：agent 声明只经 set/append 工具写入（任务数据 agate-md-field-set、项目声明 agate-config set、phase 与元数据 agate-state-set），gate 用同一契约复验；计数、创建时间、judge 是否必需、义务执行方式等系统事实由工具/gate 现算或机械核验；任务以账本首行 task_created 记录契约等级（只升不降），取代日期门槛与 judge 开关；可信锚点为 agate-ci-verify 对变更任务的 CI 校验；正文正则只作命中即拦的绊线"
known_risks:
  - "🔴 已实测的判定缺陷（v0.79.0 上仍成立，repro-tag0050.sh 在副本上复现）：P6 漏验/挑验静默放行（F1-B/C）；P7 汇总值盖住 BLOCKER（F2）；回填/删除 P1 created、或在 P6 改 judge.enabled 即跳过 judge（F3a/F3b）；回填 created 使证据引用强制从阻断降为 WARNING（F3c）；PROD_TOUCHED 安全门漏拦粗体写法、误拦 `[PROD_TOUCHED]: 无`（F4）；PAUSED 留痕调用写错、从未写入（F8）；peekview P6 引用的 173 个日志在克隆中缺 157 个（F9）"
  - "🔴 TAG0042 新引入或未解决的缺陷（实测）：P8 delivery 用子串判定（F12）；obligations.yaml 的 M 由作者自标，4 条不在 hook/check-gate 必经路径（F13）；phase 只能手改、agate-config 无 set、仓库里有 3 套 schema 校验器（F14）；agate-ci-verify 在多任务仓库恒为 SKIP，rc=0；单任务时因按 task_id 拼路径而给出假 PASS（F15）"
  - "🔴 规模：10 批（A0 hotfix / A1 契约等级与账本完整性 / A2 CI 回放 / A3 state-set / A4 义务核验 / B 写入工具与契约单源 / C 生产接触 / D 验收结论与证据 / E 成对声明 / F 代理判定）；顺序 A0→A1→{A2,B}，A3、A4 与 A1 并行，B→C→{D,E,F}，D 另依赖 agate-run 基线 hotfix；每批独立 PR、独立 gate、独立评审；新增要求的批须登记新一级快照"
  - "🔴 可信锚点在 CI：本地规则挡不住 amend/reset 后改写账本；agate-ci-verify 改为对 base..HEAD 的非合并提交逐提交回放 pre-commit 与 commit-msg hook（checkout -f + reset --soft，协议版本取 .agate-version 固定版本或协议仓库的 merge-base），须以 fetch-depth: 0 运行；使用者项目须写 .agate-version（逐提交读取，不得降级）；把 gate-backstop 设为 required 需用户明确许可；peekview 的 CI 中无 agate job，需按 UPGRADING 新增；回放耗时：TAG0042 的 16 个提交合计约 15 秒（R4 实测）"
  - "🔴 义务基线一次性重设：§2.9 机械核验后 M 数下降，须以 baseline.reset 显式重设并写入 CHANGELOG，否则会被误读为质量倒退"
  - "同类/影响面预判（判据面）：agate/scripts 下 30 个 .py 同时含 re 调用与阶段产出文件名（上界；命令：对每个 .py 判 grep -cE 're\\.(compile|search|match|findall|finditer|fullmatch)\\(' 与 grep -cE 'P[0-9](\\.5)?-[a-z-]+\\.md' 均 >0）；本任务改动的消费方逐一列于设计 §11（约 30 个脚本 + 卡片）；抽取类（agate-extract-context 除 :190-211 外）与协议文档自检不在范围"
  - "同类/影响面预判（标记面）：markers.yaml 已登记 8 个标记，本任务再登记 5 个（含 SUGGEST），只作绊线；agate/**/*.md 中提及标记的文本 167 行 / 30 个文件（上界，grep -rc），由各批 P1 给出逐行改写清单"
  - "同类/影响面预判（习惯面）：按设计 §3.6 的 T1 口径，存量语料中会被引导改写为字段的行：agateon 393 行（31 个任务）、peekview 233 行（42 个任务）；批 B 启用 ERROR 前须完成 E3 误报抽样"
  - "同类/影响面预判（存量）：agateon 42 个任务目录（含已完成的 TAG0042）、peekview 95 个，均无创建事件 ⇒ 全部按 legacy 处理，gate 退出码与 ERROR 集合不变（允许的 12 项差异列于设计 §8）；每批在两仓副本上跑 R6（AGENTS.md 工作流 0a）"
  - "同类/影响面预判（未来实例）：新增判据与卡片里新增的「必须」一律登记进新一级快照与 obligations.yaml；执行方式由 §2.9 机械核验，改动快照不升级由一致性 CHECK 拦截——不靠记忆"
  - "与 TAG0042 的关系：其接口已在 v0.79.0 落地，本设计 §9 以实际代码为准。gate_layer 无消费方、release.preset 无消费方、agate-run 基线比对恒失败这三项不在本任务范围，建议单独登记（TAG0042 实施评审 I-2/I-3/I-7）"
  - "编号：TAG0043–TAG0049 已被直改批次用作批次名，故本任务取 TAG0050"
  - "本地无密钥：结构化只消除解析歧义与漏写，不防故意伪造（设计 §1 边界）"
  - "🔴 代码语义回溯：快照只冻结数据；render/derive/判据 id 一经发布即冻结语义（改行为须起新名字），每级保存黄金 fixture，在 CI 中对全部等级回归"
  - "既有测试：§2.3 新目录规则使『新建任务目录并提交』的 hook/迁移用例转红（约 35 个，以 A1 实测为准），改用 conftest init_task()，逐条列入设计 §8 例外"
  - "待测：E1 各平台 append 对象值的引号、E2 往返成本、E3 T1 误报抽样、E4 CI 回放耗时，须在对应批的 P2 前完成"
  - "本任务改 agate/ 协议本体与脚本 ⇒ 每批均触发 SELF-GATE，须独立评审并留 self-gate-review 痕迹"
env_constraints:
  debug_env: "无独立 debug 环境；验证＝本 checkout 内 pytest 全量 + check-protocol-consistency.py（用本 checkout 自己的）+ repro-tag0050.sh 改坏即红复验 + agateon/peekview 只读副本上的双向 R6 差分（/tmp 副本，跑完核验真实仓库 git status 为空）"
  consistency_baseline: "0 ERROR / 409 WARNING（main 720c97d3 v0.79.0，2026-10-06 实测；落盘本任务设计文档后 408→409，+1 为 review-r2.md 对 docs/roadmap/improvement-backlog.md 的历史叙事引用，属冻结 WARNING，无 live WARNING）"
executor_env:
  platform: "opencode"
  has_task_tool: true
  has_local_runtime: true
  network: "full"
```

---

## 一、为什么立这个项

1. **判定依据可以被改写，而且有歧义。** gate 现在读取的依据有以下几类：
   - 自报的汇总值：P6 的 `pass`/`fail`、P7 的 `blocker_count`；
   - agent 填的日期：P1 的 `created`；
   - 可以随时改的开关：`judge.enabled`；
   - 作者自标的分类：`obligations.yaml` 的 M；
   - 正文里的散文标记和子串，例如 P8 的 `delivery:`。

   前四类改一个值就能绕开；最后一类的行首正则 10-02 到 10-03 两天修订了 4 次，仍有 182 行口径分歧（设计 §0）。
2. **规则不能靠记忆。** 字段该写什么、用什么格式，应由工具列出、由工具写入、由 gate 复验，报错时直接给出修复命令。TAG0042 批 1 之后，phase 只能由 agent 手改 `.state.yaml`，项目声明也没有 set 命令，记忆依赖反而变多了（F14）。
3. **任务需要有版本。** "这个任务按哪套规则判"现在只能拿 agent 填的日期来近似（F3a），协议根在覆盖模式下也读不到版本号（F7）。
4. **评审发现要变成判据。** TAG0042 的 P4-review 已经点出了 F12 和 "gate_layer 无消费方"，但因为"BDD 的 Then 没写到"，P7 接受、P6/P6.5 通过。设计 §6 的 `basis` 字段要求每一次"接受"都留下可追踪的去向。

## 二、任务范围（分批，每批独立 gate）

| 批 | 内容 | 设计节 | 前提 |
|---|---|---|---|
| **A0** | hotfix：F8 修复；`check-gate` 对不存在的任务目录返回 1 | §2.8、§2.4 | 无 |
| **A1** | 冻结快照与等级登记（含 CHECK、黄金 fixture）、`agate-task-init`（新建 / `--existing` / `--adopt` / `--upgrade`）、创建与升级事件规则、无创建事件即 legacy、账本完整性七规则（新目录含改名检测、只追加、不可删、事件规则、legacy 不可重开、每个有暂存文件的任务目录都检查）、按阶段确定生效等级、judge 与 evidence_ref 由契约决定、创建时间转为系统事实、统一任务 ID 正则 | §2.1–2.3、2.5、2.6 | A0 |
| **A2** | `agate-ci-verify` 逐提交回放 pre-commit 与 commit-msg hook（F15；跳过合并提交、回放模式只校验不修正、协议版本固定）+ CI 端 merge-base 等级检查 + workflow 改动（需许可） | §2.4 | A1 |
| **A3** | `agate-state-set`（phase / meta / cancel）+ `check_transition` 纯函数 + 所有 phase 变化都写事件 + `agate-next` 不写事件 + status 现算 | §2.7 | A0 |
| **A4** | 义务 `enforced_at`（ast 可达）+ `test`（含负向控制抽样）+ `review_output` 机械核验 + `scope: protocol-repo` + 基线重设（F13） | §2.9 | A0 |
| **B** | 逐文件字段契约（含 frontmatter-check 格式转换）；三套校验器合并为 `agate_schema.py`；md-field-get 对系统字段现算；md-field-set 支持 7 种操作；`agate-config set/unset/explain`；项目根统一解析；渲染块；非 legacy 任务强制 frontmatter、不回退正则；报错附修复命令；T1–T3 绊线 | §3 | A1 |
| **C** | `prod_touched` 必填；T4 优先 | §4 | B |
| **D** | P6 `results` / P6.5 `criteria`；判据 D1–D10；`resolve_evidence_ref` 与 `agate-run --task` 产出任务内日志（`run:<k>`）；入库检查与 gitignore 片段（RM-AG0097）；extract-context 改读字段 | §5 | B + agate-run 基线 hotfix |
| **E** | 声明跨文件聚合；ID 带路径前缀；待确认 / 范围增补 / 设计缺口（含 `basis`，followup 只接受 DEBT 编号并双向回指）/ CODE-MAP / P7 发现；补登记 5 个绊线标记 | §6 | B |
| **F** | UI 维度、`reviewed_bdds`、骨架标题级判定（RM-AG0085，对全部任务生效）、`pruned` 闭合（RM-AG0087）、P8 `delivery` 结构化（F12）、T2 | §7 | B |

**每批合并前须满足：**
- 先写失败用例并确认为红，验收锚见设计 §10；
- 双向 R6 差分只在副本上跑（agateon 与 peekview 各一份），按设计 §8 的口径比较；
- 新一级快照通过冻结 CHECK；
- 卡片里每新增一条"必须"，都有对应的脚本判据或报错路径，并登记进 `obligations.yaml`，其执行方式经 §2.9 核验。

## 三、明确不做

- 不改 peekview 或其他项目；
- 不迁移 legacy 任务的格式；
- 不做看板渲染、`agate-rm`、`agate-idea`；
- 不引入签名；
- 不改 P0-brief 内嵌 yaml 的格式和 judge 的信息隔离扫描；
- 不处理 `gate_layer` 消费方、`release.preset` 和 `agate-run` 基线比对问题（建议各自单独登记）。

## 四、与既有登记的关系

- **TAG0042**（v0.79.0，READY）：
  - 本任务修正它的 F12–F15，并在它已落地的接口上扩展：`agate-config`、`agate-run`、`agate-ci-verify`、`obligations.yaml`、`agate-next`（设计 §9）；
  - TAG0042 本身属于 legacy 任务。
- **TAG0038**：它在 `.state.yaml` 和账本中新增的度量字段，登记进新一级快照的 `state` 节。
- **DEBT**：
  - RM-AG0085 对应 DEBT0029，RM-AG0087 对应 DEBT0031，对应批次合入后核对并关闭；
  - F8 走 hotfix，在 CHANGELOG 中留痕。
- **新登记建议**（由维护者决定）：
  - `gate_layer` 消费方，或删除该数据面；
  - `release.preset` 增加 `none` 并接入消费方；
  - `agate-run` 普通运行不做基线比对；
  - RM-AG0094 提前（"评审发现 → 判据"）。
- **roadmap**：RM-AG0099 由本任务登记；P8 时回写 `done`，这是硬校验（RM-AG0043）。

## 五、P0 收尾自检

- [x] 任务目录 + `.state.yaml`（`phase: P0`）+ 空账本
- [x] 四字段齐全；`known_risks` 含同类/影响面预判，结论见上
- [x] 时效性：基线为 main `720c97d3`（v0.79.0），与设计同日。启动时若 main 已前进，按 P0 卡片的漂移判据核对，重点核对 §9 所列 TAG0042 接口是否被改动
- [x] 环境自检（pytest / consistency / repro 脚本可运行）
- [x] `active-tasks.md` 写入新任务行，roadmap 登记 RM-AG0099

> **2026-10-06 启动核对（主 Agent）**：
> - 时效性：main 仍为 `720c97d3`（v0.79.0），与设计基线一致 → 无漂移。
> - 设计包已落盘：`docs/design-notes/` 下 design/exp/repro/review-tag0042-implementation + `review-r1..r4.md`；`docs/design-notes/README.md` 已加索引。
> - 环境：`pytest 9.0.3`；`check-protocol-consistency.py`（本 checkout）0 ERROR / 409 WARNING；`repro-tag0050.sh` 语法通过。
> - ⚠️ 待决：P0-brief 原 `executor_env.platform` 写 `dsh`，本会话运行于 `opencode`——推进 P1 前确认派发平台（不影响 P0 门槛）。
