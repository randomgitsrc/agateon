# 变更日志

所有对 Agateon 协议的重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

> **已有 Agateon 项目升级前，先读 `agate/UPGRADING.md`**——旧任务数据（active-tasks.md/.state.yaml/任务编号）如何处理，以及各版本的破坏性变更。

---

## [0.70.0] - 2026-09-09

### 新增（TAG0033：Codex 命令流适配器 + 平台接入，RM-AG0061 + DEBT0035）

- **`agate-cmdstream-adapters.py` 新增 `CodexAdapter`**（`ADAPTERS` 注册表键 `"codex"`）——
  RM-AG0055 命令流机制新增 Codex 平台适配器，subagent 存活/卡死检测（调用冻结 / 活动冻结 /
  逻辑空转）覆盖 Codex：把 `~/.codex/sessions/**/rollout-*.jsonl`（含 `spawn_agent` 子会话的
  独立 rollout 文件）解析为统一 `CommandRecord` IR；实现 `probe` / `list_sessions` /
  `read_commands` 三方法。**检测引擎 / 阈值（RM-AG0055 §3.4.3）/ `CommandRecord` IR / 既有三
  平台适配器（Claude Code / OpenCode / DSH）零改动**——兑现 RM-AG0055 §3.4.4「未来接新平台
  只写一个适配器、检测引擎零改动」扩展点（`agate-cmdstream-adapters.py` +252 insertions / 0
  deletions）。
- **`agate/platform-notes.md` Codex 章**从「待补充」占位补为完整能力矩阵：非交互 `codex exec` /
  `-m`/`--model` 与 `-c model_reasoning_effort` 推理档 / 权限绕过 `--dangerously-bypass-approvals-and-sandbox`
  与中间档 `-s <read-only|workspace-write|danger-full-access>` / `spawn_agent` 原生子派发 /
  `--json` 结构化输出 / `resume`；退出码不可靠须解析 `--json`；model 阵容随账号类型变
  （ChatGPT 账号默认 model、`spawn_agent` model 枚举）；`multi_agent` feature flag。附实机
  验证记录（codex-cli **0.153.4** + ChatGPT 登录，2026-09）。
- **`agate/SETUP.md` 新增「步骤 2-Codex」接入小节**：`npm i -g @openai/codex` + `codex login`
  （ChatGPT vs API key 影响可用 model）+ 自动化环境绕过 flag + `codex features list` /
  `codex exec --json` 冒烟验证。
- 关联：RM-AG0061（RM-AG0055 §3.4.4 预留扩展点落地 + RM-AG0060 派发路由 epic 的 b 块前置）、
  DEBT0035（本版本关闭，见「修复」）。

### 修复

- **`CodexAdapter` pending 判据收紧（F1 / DEBT0035，P5→P4 回退修复）**：pending 判据从
  `item.status != "completed"` 收紧为「无终态信号才算 pending」——新增模块级 helper
  `_codex_is_finished(payload, item)`：已结束 = `status ∈ {"completed","failed"}` ∪
  `payload.completed_at_ms` 非 None ∪ `item.exit_code` 是 int 非 bool（三者任一）。修复真机
  Codex 把「已结束但非 0 退出」的命令记为 `status:"failed"`（携带完整 `exit_code` /
  `completed_at_ms`）时被旧口径误判为 pending、丢弃真实 `exit_code` / `output_hash`，导致
  `agate-cmdstream-detect.py` 对真机重复失败会话判不出 SPIN 的缺陷。

## [0.69.0] - 2026-09-07

### 新增（TAG0032：版本管理生命周期可用性批，RM-AG0058 + DEBT0034）

- **`agate-install.py` 新增 `latest` 显式别名**：`agate-install.py latest` 等价于无参 `install`
  （装 `latest` 指针指向的最新发布版），幂等，重跑安全——补齐官方指引里"装最新版"的显式命令形态。
- **`install.sh --versions` 新增子命令**：一键从零进入版本管理布局——建 `~/.agate/repo/` +
  首个 `vX.Y.Z/` 版本目录 + `latest` / `current` 指针 + 根 `~/.agate/scripts/` 入口副本，
  免去手工搭建版本目录结构。
- **`agate-install.py` `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时新增
  `git fetch --tags --force --prune`**（fail-open，网络失败不阻断）——令重跑 `latest`
  能跟随上游更高 tag，不再停留在首次 clone 的旧版本。
- **resolve 链新增「元仓库整仓形态」版本目录支持**：`agate_common._protocol_root` 对版本目录
  按两形态探测（`vdir/scripts` 先探 → 返回 `vdir`「根即协议」；`vdir/agate/scripts` 后探 →
  返回 `vdir/agate`「元仓库整仓」；皆无 → 返回 `vdir` 原样，下游 `resolve-entry.py` 既有
  fail-closed 兜底不变）。探测顺序不可颠倒（「根即协议」既有部署方零回归的纯增量红线）。
  GitHub 直装的 agateon 整仓版本目录（协议在 `agate/` 子目录）现可正确解析到协议子目录（RM-AG0058）。
- **版本管理布局新增根 `~/.agate/scripts/` 入口副本**（决策 B1）：从当前 `current` 版本协议根的
  `scripts/` 单源 `shutil.copytree`（非软链），随每次安装 / 升级重建刷新；`repo/` 或某
  `vX.Y.Z/` 被删不影响已建副本；副本不参与 hook 版本解析。修复"先删软链再装则
  `~/.agate/scripts` 不存在 → README 入口命令 No such file"的死路。
- 关联：RM-AG0058（版本管理生命周期可用性 epic，本批交付）、DEBT0034（三步 legacy 软链迁移
  文案在 `agate-install.py` 与 `install.sh` 双写，本任务登记 `status: open`，留后续收敛）。
- 架构决策：新增 ADR-012（版本目录两形态探测序 + 决策 B1 根 `scripts/` 单源副本机制，
  扩展 ADR-009 不替代）。

### 变更

- **`agate-install.py` / `install.sh --versions` 对 legacy 软链布局 `~/.agate` fail-closed 拒绝**
  （**行为变化**）：此前会穿透软链把 `repo/` · `vX.Y.Z/` 静默建进源仓库 `agate/` 内；现检测到
  `~/.agate` 为软链即拒绝并打印三步迁移指引（`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate`
  → `install.sh --versions`）后 `exit 1`。**向后兼容红线**：legacy 单软链用户**不跑新工具**
  （`git pull` 升级路径）行为完全不变；纯增量红线经 BDD-7 + 全量回归锁定。

## [0.68.0] - 2026-09-04

### 新增（TAG0030：验收盲区机制批，RM-AG0057 四类 + DEBT0024/25/26）

- **测试副作用/环境还原 gate（RM-AG0057-①）**：P3/P4 卡新增创建型测试清理钩子要求（创建即注册、
  无条件删除、接受 200/204/404——afterEach 清理队列模式）；P6 卡验收流程新增 post-test 环境残留
  检查步骤（快照比对或清理钩子验证二选一）；dispatch-context 模板约束节补环境清理/环境还原条目位。
- **P1 人工体验路径验收节（RM-AG0057-②）**：P1 卡 + analyst 角色新增「人工体验路径验收」要求
  （凡用户可见页面且内容受 seed 影响，强制补「Given seed 数据 → 页面有内容」BDD）。
- **plan-design-review 形态驱动化（RM-AG0057-③）**：评审角色先读受评任务 `ui_render_shape` 再加载
  维度组评分细则（布局型三组 / 渲染组件型渲染正确性 + 动效时序），每启用维度要求布局方案 ≥2 候选 +
  权衡；0-10 评分与 status 门槛映射原文保留，无形态声明回落布局型默认；role-system.md 行 47 七维
  描述同步形态驱动口径。
- **视觉契约断言收录（RM-AG0057-④）**：architect 视觉 checklist 头部单源定义视觉契约可表达子集
  （宽度/高度/对齐/重叠/溢出五类 DOM 度量，不收主观视觉）；verifier 证据形式指南补 DOM 度量量化
  证据句（`getBoundingClientRect` 示例）。
- **断言审计单测**：新增 `test_tag0030_assertions.py`（BDD-1~21 锚词 grep 断言审计，任一条文被删
  即转红）。
- **TAG0027 复盘三连（DEBT0024/25/26）**：tests/README「何时更新」补真实 gate 语义要求；AGENTS.md
  「改脚本的工作流」补「新增 CHECK 上线前先全量扫描存量」第 0 步；dispatch-context 模板补「改动
  体量 >5 文件按体量评估拆小」默认指导。

### 变更

- **plan-design-review.md 维度体系改形态驱动分派**：评分维度节首加形态分派头（先读 `ui_render_shape`
  再加载维度组），既有七维评分行与 0-10/status 门槛契约保留（CHECK11 三锚词「视觉设计/交互设计/
  渲染正确性与时序」只增不删）。

## [0.67.2] - 2026-09-04

### 修复（TAG0031：DEBT 存量修复批，历史遗留 7 条技术债）

- **版本管理域（DEBT0002/0003/0004）**：
  - `compute_sha256` 目录/文件哈希工具收敛到 `agate_common.py` 单点定义，
    `agate-pack-offline.py`/`install-offline.py` 改为共享 import，消除双实现漂移风险；
    `install-offline.py` 新增 `_ensure_agate_common` 引导函数解决 pyyaml 组件"先安装后校验"的
    离线 bootstrap 时序缺口（先内联 checksum 校验通过才 pip install，保持"先校验后使用"顺序）。
  - `UPGRADING.md`/`scripts/README.md` 离线包章节补充信任边界说明："checksum 防损坏、不防整包
    替换，bundle 提供者需可信"。
  - `agate-install.py` 的 `_find_references` 改为返回 `(refs, hit_limit)` 二元组，卸载时若命中
    限流边界（深度>4 / mtime 超窗 / 跳过目录含 .agate-version）向 stderr 输出 WARNING 提示可能
    漏扫旧引用。
- **测试隔离验证（DEBT0007）**：确认 `test_check_pruning.py` 的 `_staged_source_count` 隔离
  修复（TAG0024 已落地）在暂存区含 6+ 无关文件场景下 4 个既有回归用例稳定 exit 0，debt 登记闭合。
- **check-gate.py 健壮性（DEBT0016/0017/0018）**：
  - gate_p4 的 CODE-MAP.md 路径推导改为调用 `agate_common.resolve_workspace` 权威函数，替代
    本地 `dirname(dirname(...))` 算术，覆盖非标准两级嵌套场景。
  - 「## 新增文件核对表」存在性判定由子串包含改为整行/标题级正则，消除自指/dogfooding 场景下
    说明性文字被误判为"已满足"的假阴性。
  - `agate_common` import 降级 stub（4 个关键读取器）改为 fail-closed：安装破损（agate_common
    不可导入）时显式报错并 `return 1`，替代原静默 0/空 false-PASS 降级。
- 新增登记 2 条同类扫描发现的 open DEBT（DEBT0028/DEBT0029），不在本次处理范围。
- 全量 pytest 1445 passed + consistency 0 ERROR；P6.5 judge 独立复核 15/15 criteria passed；
  P7 一致性 BLOCKER=0。

## [0.67.1] - 2026-09-04

### 修复（TAG0029：gate 命令解析器与 TDD 红灯判定缺口修复，RM-AG0056）

- **语义变更——`P3_js` / `P3_html` 退役**：`gate_commands` 检测键收紧为精确键（DEBT0023），历史多栈后缀形态不再被收集执行；多栈并行需经协议修订登记收集后缀。真实任务 P2 从未声明 `P3_xxx` 检测键（无存量用法），存量测试已同步 S1。
- **值清洗 fail-closed**（DEBT0027）：行内注释剥离 + 引号闭合校验，堵住 `bash -c` 报 unterminated quote（exit 2）被误判红灯可推进的假绿灯。
- **judge 补 exit 2 显式分支**：判定分支内部扩展，返回约定 0/1/2/3 不变。
- **R2 fixture 豁免**（RM-AG0056）：fixture 目录不计入数据面误伤。

---

## [0.67.0] - 2026-09-03

### 新增（TAG0028：subagent 存活可观测性与受控自主再派发，RM-AG0055）

- **命令流检测三脚本**：`agate-cmdstream-ir.py`（CommandRecord 统一 IR：十字段字段契约 +
  JSON 往返）/ `agate-cmdstream-adapters.py`（CommandStreamAdapter 基类契约 + 三平台适配器
  ——Claude Code JSONL / OpenCode SQLite / DSH JSONL.zstd（spawn node 解压隔离）+ 显式注册表
  ADAPTERS + 子 agent 会话定位）/ `agate-cmdstream-detect.py`（检测引擎：调用冻结
  expected×2 + 兜底 300/900s、活动冻结 60/300s、无效重复窗口 10 内 ≥5、REPEAT_UNIQUE_MIN=3
  信息级、截断排除、轮询误报标注；阈值可配置 maintainability.yaml 节，缺失/损坏全兜底；
  CLI 子命令 list-sessions / read-commands / detect）。
- **存活/卡死判定职责改由命令流日志承担**：dispatch-protocol.md「Subagent 安全 → 硬超时保护 →
  存活检查」节改写——命令流日志（平台会话记录外部活动信号）承担存活/卡死判定，progress.md
  保留"语义进展"职责不变，两套信号分工明确。
- **心跳文件生命周期**：`.heartbeat` / `.heartbeat.child-{n}` 命名规范 + 审计豁免显式登记
  （check-p6-provenance.py `_find_files` 隐藏文件过滤天然跳过，注释级登记确认）+ 清理时机
  （任务结束由产生方清理，异常遗留由派发前置检查清空，复用 agate-archive-stale-outputs 模式）。
- **受控自主再派发**：role-system.md「子派发权限边界」节——执行角色（analyst/architect/
  implementer/verifier）可被授予子派发权限，两条硬边界（子任务不写 .state.yaml / 写权限是父
  权限严格子集）；judge 类角色例外（不开放 Agent/subagent_fork，信息隔离冲突）；dispatch-context
  模板补「不启用子派发能力」显式声明位。
- **maintainability.yaml 新增 cmdstream_detection 节**：检测阈值（300/900/60/300/10/5 +
  repeat_unique_min=3 + expected ×2/30s），缺失/损坏兜底协议默认值，不报错。
- 新增 pytest 用例（tag0028 批，P5 实测 1434 passed + 0 failed + 2 skipped，count-tests 不漂移）。

### 变更

- **dispatch-protocol.md 存活检查节改写**（见上「新增」第 2 条，属协议文档职责重定义——
  存活判定信号源切换，既有 progress.md 语义不变，不破坏既有 gate 返回约定）。

---

## [0.66.0] - 2026-09-03

### 新增（TAG0027：编排语义统一落地，RM-AG0054）

- **推进侧状态机 CLI：`agate next` / `agate advance`**：推进决策从 orchestrator 临场判断改为
  查表推进——消费 `phases.yaml` 新声明的 `next` / `retreat` / `gate_pass_exit`（逐 phase「检查
  通过」出口码）+ `check-gate.py` exit 三态（exit ∈ gate_pass_exit → 直推 next / P6 条件式推进
  前置 gate_p65；exit 1 → 按 retreat 表值委托 `agate-retreat-to.py` 逐阶回退；真暂停 → 落盘
  `{phase}-exit2-resolution.md` 转主 Agent）；推进只 git add 不自行 commit；档位 C 自动推进改走
  `agate next`（可观测层，事件留痕 gate-events.jsonl）。
- **`agate dispatch` 渲染时注入单命令（方案 A）**：派发 = 单命令自动渲染 dispatch-context
  （Lazy Injection——渲染时拼装阶段卡片 + 块外 `CARD-SOURCE` 来源标记），主 Agent 不再直接调用
  `agate-inject-card.py`；`agate-inject-card.py` / `agate-card-inject.py` 手工兜底路径保留兼容。
- **`phases.yaml` 转移表结构化字段**：主线 P0-P8 条目新增 `next` / `retreat` / `gate_pass_exit`
  键（值域枚举 + null，schema 同步声明），P6.5 条目新增 `gate_subphase`（hosted_on/forward_to/
  needs_revision_to，非独立转移边口径保持）。
- **护栏 1 机械化（CHECK 14/15）**：`check-protocol-consistency.py` 新增 md 叙述段落平台名扫描
  （段落级「实现注记」豁免 + 结构豁免：platform-notes/SETUP/已知适用环境表/dsh 平台食谱目录）与
  数据面平台名词边界扫描（豁免词典从 schema + rules 机械生成，不手抄文件名单）。
- **审计 2 双锚点剥离**：`check-p6-provenance.py` 审计 2 卡片块剥离 = CARD-SOURCE 行起物理块优先
  + START..END 兜底（渲染产物与手工注入两路并存覆盖）；`check-judge-verdict.py` `_strip_card`
  同步 + P6.5 复核谓词 Fix C（只校验经真暂停分支落盘的 resolution 文件，健康任务不误拦）。
- 新增 48 个 pytest 用例（tag0027 批 9 新测试文件，P5 实测 1381 passed + 2 skipped）。

### 变更

- **S-1/S-2 加列比对**：`check-structure-consistency.py` S-1 扩展比对 YAML `next`/`retreat` ↔
  WORKFLOW.md 阶段总览表第 4/5 列（P6.5 行走 gate_subphase 形态特判）。
- **编排心智统一文档化**：协议文档平台名三分类清理（语义段清理 / 「实现注记」标记 /
  结构豁免）；loop-orchestration.md 档位 C 推进点改走 `agate next`；dispatch-protocol.md /
  模板 / 角色文件平台适配说明挂实现注记。
- **check-gate.py 头注释补 exit 2 语义说明**（exit 2 = 多数 phase 正常通过码，「exit 2 = 需主
  Agent 自判」是信号语义；返回逻辑与约定未改）。

---

## [0.65.0] - 2026-08-30

### 新增（TAG0026：维护性反模式 gate，RM-AG0046）

- **`check-maintainability.py` 维护性反模式检测器（RM-AG0046）**：新增 diff 驱动的两类反模式
  检测——god-file 跨越（before < 阈值 ≤ after，默认 1000 行）与 fuzzy-boundary（裸 `except:` /
  `# type: ignore` / `: any` 等，按扩展名路由正则）；阈值与正则集经 `agate-workspace/maintainability.yaml`
  可配置（默认值仅供参考），配置缺失/损坏全部兜底为默认值，不报错。
- **`check-gate.py` gate_p4 新增三重门槛（RM-AG0046）**：检测 violations 非空时，要求
  known-violations.md 登记（新模板 `agate/assets/templates/known-violations-template.md`）+
  登记条目数 ≥ violation 数 + P4 评审 approve 三者齐全才放行——登记本身不构成放行依据，
  "是否接受该反模式"的判断权在评审角色；violations 为空 / 检测未部署 / git 通道不可用三场景
  行为与旧版完全一致（零回归面）。
- **P4/P6 卡片机制条目**：P4 卡新增评审 checklist（approve 前必须读过登记理由）与 gate 规则
  exit 1 条目；P6 卡「自查≠gate」节新增非阻断复跑提醒（挂载在 P4，P6 暂存区通常无代码 diff）。
- **一致性配套**：check-protocol-consistency.py 锚点登记 + agate-summary.py `_DRIFT_SCRIPTS`
  同步；新增 27 个单测（count-tests 1308 → 1335，只增不减）。
- **DEBT0023 登记**：gate_commands 的 P3* 前缀键被静默收集为 TDD 测试命令执行（协议缺口，
  low，本任务以"禁用 P3_xxx 键"约定规避，收口留待后续任务）。

### 变更

- **入口文档品牌文案统一**：README×2 / AGENTS×2 / SETUP / UPGRADING（当前节）品牌词 agate → Agateon（TAG0025 Phase 0 收尾；backtick token 与历史版本节按设计保留）
- **DSH preset 显示名**：「agate 编排者」→「Agateon 编排者」（preset.yml / agent.cordis.yml / SKILL.md / SETUP 同步；新会话生效）
- **本地测试并行化文档补齐**：CI 自 2026-08-25 已用 `-n auto`（3.5x 提速），本机口径补齐至 tests/README + worktree 指南 + AGENTS.md（`pip install pytest-xdist` 后 `-n auto`）
- **agate-summary.py 新增 DSH 安装产物链接校验**：检测 ~/.dsh 三个软链（preset/cordis/SKILL）漂移并给出修复命令（防"软链指向过时副本"静默漂移；上线首日即检出 2 处存量漂移）
- **TAG0025 复盘改进措施落地**：test-designer 角色补「永久回归测试判据」（长期不变量 vs 一次性交付事实）、P1 卡基线保护节补「隐含扩展同样要授权」触发点（落点 1/2）
- **DEBT0022 关闭**：retrospective-tag0019-21.md 补提交入库（agate-workspace/reviews/）+ roadmap 2 处引用补实际路径；DEBT0021/0022 关闭证据补齐（check-debt 0 错误）
- **删除未经用户授权的 v1.0/v2.0 版本锚点**：roadmap/设计文档/协议正文中的「v1.0 窗口/之后」「v2.0 起」等表述统一改为中性「后续/当前」——v1.0 系规划期引入的假想里程碑，v2.0 系内部「结构化工作区」时代名的误用；内部层标记（`v2.0 机器字段`）与 semver 策略说明保留
- **HANDOFF-TAG0024/0025** 归档至 archived/

---

## [0.64.0] - 2026-08-26

### 变更（TAG0025：Agateon 品牌改名执行 Phase 0-1，RM-AG0035 剩余工作②）

- **品牌声明上线**：README.md / README.zh-CN.md 首屏新增 "Agateon (formerly agate)" 品牌声明，
  标志本项目正在从 `agate` 更名为 `Agateon`。
- **GitHub 主仓改名 + 硬编码仓库 URL 同批更新**：主仓已改名为 `randomgitsrc/agateon`
  （用户当次会话放行确认后由主 Agent 亲自执行，4 条验收锚——301 跳转/`git ls-remote`/全仓残留
  扫描/GitHub 搜索首位命中——实测通过）；`install.sh`、`agate/scripts/agate-install.py`、
  `agate/scripts/agate-changes.py`、README.md/README.zh-CN.md 的 badge 与安装入口，共 7 处
  硬编码仓库路径已同批更新为 `randomgitsrc/agateon`；本机 remote 迁移（主 checkout 一次
  `git remote set-url`，worktree 通过共享 `.git/config` 自动跟随，实测验证）。
- 三层解耦原则：仅改外部品牌层（仓库名/品牌声明），内部命名空间（`agate/` 目录、
  `agate-workspace/`、`~/.agate`、`AGATE_*`、`agate-*.py` 文件名、`agate_common`）不变。

### 其他（v0.63.0 之后、TAG0025 之外的维护性变更——同一发布区间内，一并记录）

- **CHECK 13：CHANGELOG↔UPGRADING 章节对应性检查（RM-AG0052）**：`check-protocol-consistency.py`
  新增校验，确保 CHANGELOG 最新已发布版本在 `agate/UPGRADING.md` §3 有对应章节，防止发布清单
  第 3 步遗漏（v0.62.0/v0.63.0 曾连续两次漏写）。
- **CI：consistency job 全量 fetch tags，恢复 CHECK 7 版本漂移判定**：修复 CI 环境下浅克隆导致
  CHECK 7（README badge 与最新 git tag 一致性）长期失效的问题。
- **CI：docs-only PR 无法合并的根治修复**：required job 内嵌 fast-pass 替代 job 级 `if` 跳过，
  修复纯文档 PR 因 required check 未触发而无法合并的问题。
- **文档维护**：补写 `agate/UPGRADING.md` v0.62.0/v0.63.0 章节（发布清单遗漏补救）；重构
  `AGENTS.md`（精简为"不读就不知道"原则，修复 5 处过时点）；恢复 AGENTS.md Gate 脚本分层节
  标题与依赖节；roadmap 登记 RM-AG0051/RM-AG0052 并回写 RM-AG0051 done（CHECK 7 hotfix）。
- **归档与收尾**：TAG0024 合并后复盘归档 + DEBT0022 登记（复盘归档断链）；归档 TAG0023 交接单
  并清理其 worktree/分支；关闭 Agateon 改名调研的最后开放问题（GitHub org `agateon` 已占名，
  2026-08-25）；`design-rename-execution.md` 状态行更新为三轮独立评审通过。

## [0.63.0] - 2026-08-25

### 新增（TAG0024：工具链批立项，RM-AG0048 一期 + DEBT0019/20 + RM-AG0049/50）

- **`agate-md-field-set` 结构化字段写入工具（RM-AG0048 一期）**：新增
  `agate/scripts/agate-md-field-set.py`（标量字段/简单 list 字段/`gate_commands` 正文块写入
  + 证据字段拒绝端 + 跨文件提示）与配套 `agate-md-field-set-gate-commands.py`
  子命令，key 从 `phases.yaml` task_fields 白名单限定、value 写入时按值域校验、格式由工具
  统一生成——消灭 subagent 手写 frontmatter 的格式摩擦（P1-gate-diagnosis 实证）；核心设计
  遵循"同源铁律"（与 gate 共用 `phases.yaml` 权威源 + resolve-entry 版本链）与"自描述"
  （`--list`/`--help`/错误提示给合法值），"零协议知识 subagent 照提示填对"为验收判据。
  二期（证据字段自动写入/账本留痕/跨文件预检）另行设计。
- **`check-gate.py` roadmap-done 校验健壮性修复（DEBT0019/DEBT0020）**：
  `_check_roadmap_done()` 表格解析由"实际列数 ≥8"改为**精确匹配 9 列**（含首尾空列），
  单元格内含字面 `|` 字符时整行跳过而非错位取值（DEBT0019，消灭潜在漏判/误判）；
  `gate_p8()` 调用点的 roadmap.md 路径定位由"相对 CWD 硬编码拼接"改为
  `git rev-parse --show-toplevel` 仓库根锚定，非仓库根 CWD 调用不再静默失配，
  非 git 仓库环境下输出区分性 stderr 提示（DEBT0020）；均配套回归用例
  （`test_check_gate.py` BDD-20~24）。
- **`phases.yaml` 文档自洽修复（RM-AG0049/RM-AG0050）**：P4 阶段 `outputs` 补齐
  `P4-review.md` 声明（`required: true`），消除"产出声明与 gate 实际要求不对称"
  （RM-AG0049）；统一 P6.5 定位表述为"挂载于 P6→P7 转移的强门槛子阶段，不是独立 phase
  值"（以 `state-machine.md` 口径为准），消除 phases.yaml 与 state-machine.md 两处叙述
  不一致（RM-AG0050）。
- **`check-pruning.py` 测试隔离修复（BDD-30，SCOPE+ 发现）**：`_staged_source_count`
  改为以 `task_dir` 自身所属仓库定位，消除跨仓库/多 worktree 场景下的测试隔离缺口。
- **ADR-011**：新增架构决策记录，落定本批次工具链设计的关键决策依据——引导型 CLI 工具的
  权限是早纠错，不是安全边界。
- 新增回归用例覆盖 BDD-1~30（含 RM-AG0048 一期 BDD-1~19、DEBT0019 BDD-20~21、
  DEBT0020 BDD-22~24、RM-AG0049 BDD-25~26、RM-AG0050 BDD-27~28、跨 issue 约束 BDD-29、
  BDD-30 SCOPE+）；全量 pytest 1285 passed / 2 skipped / 0 failed；ruff 0 违规；
  consistency 0 ERROR；P6.5 judge 独立评审 `status: passed`；P7 一致性核对 BLOCKER=0。

## [0.62.0] - 2026-08-25

### 新增（TAG0023：机制校验补强批，RM-AG0042~RM-AG0045）

- **门槛失败事件↔retries 对应性校验（RM-AG0042）**：`check-state-transition.py` 新增
  `check_retries_correspondence()`，覆盖三类事件源——评审 rejected（扫描评审角色
  retry/rev dispatch-context 文件，C8 角色 token 精确枚举）、P5→P4 等单步回退（复用
  `get_old_phase()` 的 git-show-HEAD 范式，`old_num>new_num` 且暂存 `retries` 长度未增长
  → exit 1 阻断）、子代理空返回重派（关键词扫描）；BDD-2 阻断，BDD-1/BDD-3 高优 WARNING
  不阻断——四任务复盘"retries 全为 `{}`"的机制缺口首次被机械校验兜底。
- **P8 roadmap done 反查（RM-AG0043）**：`check-gate.py` `gate_p8()` 新增
  `_check_roadmap_done()`，按 `task_id` 精确匹配 roadmap.md「关联任务」列，任一关联 RM
  条目状态非 `done` → exit 1 阻断，避免任务收尾时遗漏 roadmap 回写。
- **环境敏感测试根因修复 + 集中清单 + CI 重跑（RM-AG0044）**：`check-debt.py.
  _retreat_coverage()` 的 short hash 比对由固定 `full[:7]` 切片改为动态
  `git rev-parse --short`，消除 CI（git 2.55.0）与本地（git 2.43.0）auto-abbrev 长度差异
  导致的 flaky（已用 PR #188 真实 CI 失败日志 forensic 确认根因）；新增
  `agate/tests/ENV-SENSITIVE-TESTS.md` 集中登记环境敏感测试（含根因分类字段）；
  `protocol-tests.yml` pytest job 新增 `pytest-rerunfailures --reruns 1` 兜底。
- **声明写时自检 + 错误提示增强（RM-AG0045）**：`dispatch-prompt.md`「返回前自检」节新增
  子项——产出含 P1/P2 时先跑 `check-frontmatter.py`（+ `ceremony: thin` 时加跑
  `check-routing.py`），非 0 退出需自行修正后再返回，把 TAG0019 三类历史格式错误的发现
  时点从 commit-time 提前到写时；`agate-frontmatter-check.py` 的错误消息逐条追加具体
  修复提示文本。
- RM-AG0032 历史数据补记：roadmap.md 追加一行 `done` 状态记录。

## [0.61.0] - 2026-08-22

### 新增（TAG0022：质量门禁与迁移收尾批，RM-AG0037~RM-AG0041）

- **ruff 合并强制（RM-AG0037）**：CI `ruff` job 锁版本 `ruff==0.16.4`（与本地开发环境
  `~/.venvs/agate-dev/bin/ruff` 对齐）+ job name 固化 `ruff`（可被 GitHub 分支保护按 check 名引用）；
  UPGRADING/AGENTS.md 写入「将 ruff 设为 PR required check（维护者在仓库设置勾选）」配置步骤——
  TAG0019/20 曾带 23/12 处违规合并的复发防线（required 勾选为维护者配置，非实现侧动作）。
- **check-gate 权威源切换闭环（RM-AG0038，M2 二期）**：check-gate.py 协议规则类 md/grep 解析清零——
  A 组 frontmatter 字段改走 `agate-md-field-get` 新 op（status/agent/project_phase/code_map_*/created）、
  B/C/D 组标记与产出格式判定迁 `agate_common` 共享读取器单点（判定口径不变、well-formed 等价、旧格式
  正文回退保留）；S-3 双向收紧（S-3a YAML→卡片、S-3b 卡片→YAML 的 gate 命令一致性，md 禁止承载
  可判定规则）——「YAML 权威、md 禁止承载可判定规则」落地（破坏性变更见 UPGRADING v0.61.0 ②）。
- **judge 启用强制化（RM-AG0039）**：check-gate P1 新增 judge 校验——机制后新任务（P1 `created` ≥
  `judge_required_since: "2026-08-22"`）缺 `.state.yaml` 的 `judge.enabled: true` → exit 1 阻断；
  历史任务（created < 截止或未声明）跳过（向后兼容，与 gate_p65 历史语义一致）；state-machine /
  P1 卡模板语义同步（破坏性变更见 UPGRADING v0.61.0 ③）。
- **ceremony: thin 实证收尾（RM-AG0040）**：M3 实证执行计划 + 触发条件落盘（P2 §4.4：评审轮数 /
  真实发现数 / TAG0018 基线 / 不达标回滚 standard / 触发条件 = 下一 low 薄任务），薄任务实战后产出
  对比报告。
- **环境假象测试根治（RM-AG0041）**：test_bdd_7 改 `GIT_CEILING_DIRECTORIES` 注入确定化非 git
  上下文；test_bdd_25 改位置感知 + `check-protocol-consistency.py` `iter_md_files` 新增 opt-in
  排除钩子 `AGATE_CONSISTENCY_SKIP_DIRS`（默认关闭、行为不变）——任意 basetemp 位置全量 0 失败
  （TAG0020/21 反复复现的 2 条 known-failures 根治）。
- 新增 13 测试用例（count-tests 1202 → 1215）；全量 pytest 1213 passed / 2 skipped / 0 failed
  （P5/P6 双位置验证）；consistency 0 ERROR；structure S0-S6 0 漂移；ruff×2 0 违规。

### 破坏性变更

见 `agate/UPGRADING.md` v0.61.0 节：① ruff job 锁版本 + required check 配置步骤（纯 CI 配置 +
文档，无升级动作）② check-gate 规则读取切 YAML 唯一权威源（判定口径不变、旧格式任务靠正文回退，
对账兜底行为见 UPGRADING）③ 机制后新任务 P1 强制 `judge.enabled: true`（历史任务跳过）。

## [0.60.0] - 2026-08-22

### 新增（TAG0021：协议结构化层 rules/ + S-1~S-6 双向一致性，RM-AG0022）

- **结构化规则权威源 `agate/rules/`（M0，纯增量）**：`phases.yaml` / `dispatch.yaml` / `roles.yaml`
  承载可判定规则（阶段定义 / 派发三铁律 / 五模式编排 / gate_commands 语法 / 角色映射 / C8 机械映射），
  markdown 保留为人类叙事层；配套 `rules/schema/*.schema.json`（draft-07 子集）+ 手写校验器
  `check-yaml-schema.py`（不引入 jsonschema 依赖）。
- **双向一致性 gate `check-structure-consistency.py`（S-1~S-6 + S0）**：phases↔WORKFLOW 总览表双向
  对账（S-1/S-2）、YAML→卡片（S-3）、YAML→脚本登记（S-4）、schema 校验（S-5）、引用完整性（S-6）、
  S 编号自校验（S0）；ERROR 即 exit 1。
- **三脚本双跑对账模式（M1）**：`agate-read-gate-commands` / `check-pruning` / `check-gate`（P2 分支）
  grep↔YAML 结构化双读，差异输出 stderr `RECONCILE WARNING` + 汇总计数，退出码语义不变（告警不阻断）；对账工具函数入 `agate_common`（reconcile_field / read_rules_yaml / is_legal_gate_key 等）。
- **切换权威源 + 阻断提升（M2）**：gate_commands 块解析 / 四字段计数迁至 `agate_common` 共享助手单点，
  删除消费脚本内联正则；协议规则读 rules/*.yaml；S-1/S-2 漂移进 **pre-commit 独立 step + CI
  consistency job 追加步骤**（exit 1 阻断）——判定语义与 v0.59 逐字节等价（破坏性变更见
  UPGRADING v0.60.0）。
- **卡片渲染化 + 稳定版隔离（M3）**：`agate-next-card.py` 内嵌渲染器 render_card()，卡片门槛 / 产出 /
  派发 / gate 规则 / retry 上限节由 phases.yaml 渲染（正式卡片字节稳定、sha256 契约保持）；S-3 升级为
  全卡逐字段对账；渲染经 AGATE_ROOT 解析隔离（worktree 未发布 YAML 不污染稳定版注入）。
- 新增 34 测试用例（count-tests 1168 → 1202，≥ 749 基线）；全量 pytest 1198 passed（2 环境假象已登记）。

### 破坏性变更

见 `agate/UPGRADING.md` v0.60.0 节：① 三脚本从 grep 解析 md 切为读 YAML 权威源 + 对账兜底（判定语义
不变，旧正文格式任务靠对账可跑，会持续出 RECONCILE 差异告警）② 一致性 gate 提升为 pre-commit + CI 阻断
③ rules/ 数据层纯增量，既有 rules/*.md 保留不动。

## [0.59.0] - 2026-08-22

### 新增（TAG0020：P6.5 独立 Judge 机制，RM-AG0032）

- **新评审角色 judge**（`assets/review-roles/judge.md`，所有任务强制）：P6 验收后、P7 之前以 fresh
  context 逐条重验**所有** BDD（含已 PASS 项，零挑验），只信 `P6-evidence/` 证据与 git log，不读
  verifier/implementer 自述——补 self-authored gate（P6/P7）的作者与裁判同信任链弱点（LIMITATIONS.md
  局限 3 缓解链）。
- **三层防造假**：① 信息隔离白名单（judge 的 dispatch-context 仅允许白名单输入，`check-judge-
  verdict.py` 机械校验黑名单路径引用集）② 证据交叉核对（BDD 计数对照「criteria_total == P1 标题数
  + 编号集零挑验」/ 证据存在非空 / md5 去重 / 引用对称）③ append-only 事件账本
  `gate-events.jsonl`（`agate_common.append_event` 单点写入，行间哈希链 + 时间戳单调，
  `check-events.py` 审计）。
- **新脚本**：`check-judge-verdict.py`（verdict 门槛判定九步链，通过后自记 `judge_verdict` 事件含
  `verdict_hash` 内容寻址——同一 verdict 被多处 gate 执行重跑不增轮次）、`check-events.py`（账本
  审计：哈希链完整 / ts 单调 / judge 复核轮次 ≤2 按 verdict_hash 去重）。
- **P6.5 状态机挂载**：P6 → P6.5（judge 复核）→ P7；`.state.yaml` phase 保持 P6 直至 P7（P6.5 非独立
  phase 值，valid_phases/重试表零扩展）；`check-gate.py` 新增 `P6.5` 分支（judge 未启用 → 早退跳过，
  历史兼容）；pre-commit-gate 2i.1 + ci-gate-backstop judge/events 兜底。
- **三档预算与诚实降级**：轮次 ≤2 / token 100k（`judge_token_budget` 可覆盖）/ 时间 30min；预算耗尽
  → `partial: true` + `status: needs-revision`（账本 `reason: budget_exhausted` 交叉校验），不静默
  放行。哲学红线保持：judge verdict 是行为描述输入，**机械核对（双脚本 exit 0）才是门槛**。
- 文档：state-machine / WORKFLOW / dispatch-protocol（Judge 信息隔离节）/ P6 卡片（P6.5 门槛）/
  dispatch-prompt（Judge 派发追加节）/ role-system（judge 登记）/ LIMITATIONS（局限 3 缓解链）/
  AGENTS / CODE-MAP；CHECK 9 锚点 + `_DRIFT_SCRIPTS` 登记。

## [0.58.0] - 2026-08-21

### 新增（TAG0019：风险分路由 ceremony routing，RM-AG0031）

- **ceremony 声明字段**（P1 frontmatter 可选，thin / standard / full，缺省 standard fail-closed）：
  声明 thin 须四要素 checklist（coupling_checklist 流式 + 跳过风险 + P5/P6 保留），缺一回退 standard；
  `ceremony: full` 任务 phases 必须含 P7（P7 不可裁，声明层 + 评审层双重保证）。
- **check-routing.py gate**（pre-commit 链 2j.1）：ceremony 路由校验——声明与算分 tier 单向 fail-closed
  （声明 thin 而算分 standard/full → 拦截）+ thin 四要素 checklist + 非法值 / P1 缺失边界（exit 0/1/2）；
  不声明 ceremony 的存量任务 exit 0 不拦截（向后兼容）；importlib 复用 check-pruning 同源函数（BDD-10）。
- **agate-risk-score.py 客观信号算分**：文件类型 / 敏感路径（词干匹配 + 左锚防误标）/ 改动规模 /
  影响面（反向引用，跳过任务产出文档）四信号 → risk_score / tier（thin|standard|full）+ 逐信号证据行 +
  域映射；提供可 import 的 `score_task(task_dir)` 与 CLI 薄壳；git 通道异常输出 `git_ok: false` 不静默降级。
- **requirements-review 审声明职责**：评审核对「风险分级/裁剪声明（risk_level/ceremony/phases）vs
  暂存区 diff 证据」，不一致 → needs-revision / rejected。
- **M3 验收锚度量协议**：评审轮数 vs 真实发现数双指标 + TAG0018 基线（4 场 LLM 评审 ≈0 净收益）+
  不达标回滚规则（机制文档，M3 主体不在本任务实行）。
- 修复：check-protocol-consistency CHECK 9 锚点表补 check-routing（反向覆盖）；测试注释 `/tmp` 字面
  清理（platform-assumptions 变更文件集 0 命中）。

## [0.57.0] - 2026-08-21

### 新增（TAG0018：agate 原生支持 DSH 平台，RM-AG0030）

- **DSH（deepseek-harness）成为 agate 官方支持的第三个平台**（继 OpenCode、Claude Code 之后）：
  新增 `assets/templates/dsh/` 模板目录（`agent.cordis.yml` orchestrator agent-preset +
  `preset.yml` 会话选择器元数据 + `SKILL.md` agate-protocol skill）、`SETUP.md`「步骤 2-DSH」
  接入章节、`platform-notes.md` DSH 平台条目、`tests/unit/test_dsh_preset.py` 平台无关回归测试
  （8 用例）。
- **orchestrator agent-preset（agent.cordis.yml）**：薄身份 persona（行为规范指向
  `{agate_root}/orchestrator-template.md`，不复制模板全文）+ 最小工具面 + `tool-fs-search` 必填
  配置 `config.sampleOverCapGlobResults: false`（DSH schemastery 必填无默认值，缺失 → preset
  挂载失败 → fail-closed 拒绝创建会话，2026-08-21 实机缺陷回归）。
- **SETUP.md「步骤 2-DSH」**：符号链接接入命令（`mkdir -p` + 三条 `ln -sf` 指向
  `~/.agate/assets/templates/dsh/`），与 Claude Code/OpenCode/Windows 平台小节同构；「身份薄、
  协议厚」说明 + 升级跟随行为（符号链接免操作 / 复制模式重跑）+ 使用与验证指引（会话选择器选
  「agate 编排者」）。
- **platform-notes.md「## DSH（deepseek-harness）」条目**：六项能力差异对照表（orchestrator 身份
  注册 / 派发 subagent / 批量并行 / 独立复核 / 跨轮续跑 / 实时 gate）+「已知注意」节（sandbox
  只读、DSH 无 `.claude/agents/*.md` 等价物），接入步骤单一真相源指向 SETUP.md「步骤 2-DSH」。
- **test_dsh_preset.py（8 用例，平台无关）**：守护 agent.cordis.yml 行结构（id/name）、
  tool-fs-search 必填配置、preset.yml 元数据、SKILL frontmatter、SETUP.md 章节与命令在位；只
  校验仓库内文件，无 DSH 实例的 CI 环境可跑。

### 关键机制

- DSH 平台接入 = SETUP.md 文档化符号链接 + 唯一 `install-hook.py`，不发明新结构（无 per-platform
  installer）；「身份薄、协议厚」保证模板随 `~/.agate` 升级自动更新。
- 回归测试平台无关原则：不依赖真实 DSH 实例、不写 /tmp、不假设符号链接语义——无 DSH 的 CI 环境
  可跑。

### 说明

- **本版本无破坏性变更**：交付物全部为新增文件（`assets/templates/dsh/` 三文件、
  `test_dsh_preset.py`）与文档追加章节（SETUP.md / platform-notes.md），未改动任何既有协议机制
  运行时行为；已有项目升级仅需 `git pull` + 重跑 `install-hook.py`。
- **技术债**：本次无技术债关闭（`debt_check: none`）——既有 open 债务
  （DEBT0002/3/4/7/8/14/15/16/17）与本任务无交集。
- DSH 平台接入步骤见 `SETUP.md`「步骤 2-DSH」（单一真相源）；`platform-notes.md` DSH 条目只做
  能力差异说明。

---

## [0.56.0] - 2026-08-20

### 新增（TAG0007：agate 项目结构管理机制，RM-AG0008 + RM-AG0009）

- **RM-AG0008：0→1 项目骨架脚手架（BDD-1~5）**：新增 `P1-requirements.md` 可选 frontmatter 字段
  `project_phase: bootstrap`（缺省 = `established`，向后兼容，不触发骨架流程）。触发后 P2
  architect 除 `P2-design.md` 外额外产出任务目录内 companion 文件 `P2-skeleton.md`（含
  `## 骨架声明` 标题），使用新增模板 `agate/assets/templates/skeleton-template.md`——五类候选
  目录（源码/测试/文档/构建/部署）以抽象类别标签 + 项目侧技术栈声明填空区表达，不硬编码
  `src/components`/`src/include` 等具体技术栈目录名（跨语言/框架通用）。`check-gate.py` 的
  `gate_p2` 新增判定：`project_phase: bootstrap` 时要求 `P2-skeleton.md` 存在且含
  `## 骨架声明` 标题，否则 exit 1；字段缺失/非 bootstrap 时行为与改动前逐字节一致。
- **RM-AG0009：CODE-MAP 架构演进纪律（BDD-6~11）**：复用既有工作区 `agents/` 子目录，新增
  `{AGATE_WORKSPACE}/agents/CODE-MAP.md`（配套模板 `agate/assets/templates/code-map-template.md`）
  维护"当前架构全貌"（模块/层/依赖方向/关键文件/约定），文件是否存在即"该项目是否已采用
  CODE-MAP 机制"的判据。`P4-implementation.md` 新增「新增文件核对表」小节：implementer 为每个
  新增文件填一行——骨架归属列（`within <dir>` / `[SKELETON_DEVIATION: 理由]`）+ CODE-MAP
  处理列（`[CODE_MAP_UPDATED]` / `[CODE_MAP_EXEMPT: 理由]`），`change_type: refactor` 场景同样
  适用不豁免。`P7-consistency.md` frontmatter 新增两个可选字段
  `code_map_new_files_count`/`code_map_reviewed_count`（语义分别对应既有
  `design_gap_count`/`design_gap_reviewed_count`），「检查清单」新增第 5 条 CODE-MAP 核对——对照
  `agents/CODE-MAP.md` 与 P4 新增文件核对表，发现依赖方向偏离标 `[CODE_MAP_DRIFT:]`（WARNING
  级，不阻断），核对通过标 `[CODE_MAP_SYNC:]`，与既有 `DESIGN_GAP`/`DESIGN_GAP_REVIEWED`
  双轨判定模式平行运作，不新造一套判定机制。`consistency-reviewer.md`「检查清单」节新增
  CODE-MAP 核对职责段落。`check-gate.py` 的 `gate_p4` 新增 WARNING 分支：骨架/CODE-MAP 机制
  已采用但 `P4-implementation.md` 缺「新增文件核对表」标题时提醒（非阻断）。
- **关联 BDD 覆盖**：P1-requirements.md 11 条 BDD 全覆盖（RM-AG0008 骨架 BDD-1~5 +
  RM-AG0009 CODE-MAP BDD-6~11），新增 12 个回归测试用例验证向后兼容性与新判定分支。

### 已知遗留（本轮新登记，留待后续任务处理）

- DEBT0016（低优先级）：`gate_p4` 的 CODE-MAP.md 路径推导用本地路径算术，未调用
  `agate_common.resolve_workspace` 权威解析函数，标准两级嵌套场景下结果代数等价，但非标准布局
  存在潜在分歧风险。
- DEBT0017（低优先级）：`gate_p4`「## 新增文件核对表」子串判定在自指/dogfooding 场景下存在
  假阴性（说明性文字可误判为已满足），且 TAG0007 自身 P4 产出未对新增文件逐条打标准
  CODE-MAP 标记，构成机制的自我应用缺口。

## [0.55.0] - 2026-08-20

### 新增（TAG0017：协议工具链修复批，RM-AG0027 + RM-AG0028，来源 TAG0016 复盘 + TQC0001 跨项目反馈）

- **DEBT0010 修复：`gate_commands` 键解析统一排除 `_timeout_seconds` 后缀（BDD-1~4）**：
  `agate/scripts/agate_common.py` 新增共享判据函数 `is_gate_meta_key(key)`
  （`key.endswith(("_formatter", "_timeout_seconds"))`），`agate-read-gate-commands.py` /
  `agate-gate-missing-cmds.py` / `agate-gate-p5-count.py` / `agate-read-p5-commands.py` 四处解析
  脚本改用该函数，消除此前只排除 `_formatter`、把 `{key}_timeout_seconds` 声明字段误判为待执行
  命令/待核实项的系统性缺陷（TAG0016 P2/P3/P5 三阶段均实测复现）；新增结构性审计测试防第五处
  遗漏，`check-tdd-red.py` 补 `P3_timeout_seconds` 真红灯场景用例防止判定被放宽。
- **RM-AG0028/DEBT0015 修复：`env_constraints` 声明性 vs 执行性边界文档化（BDD-5~6）**：
  `agate/phase-cards/P2-design.md`「gate_commands 声明」节新增边界说明——`env_constraints` 是
  声明性字段（信息注入），执行性约束必须落到 `gate_commands` 或 P4/P8 明确 checklist；
  `agate/assets/execution-roles/architect.md` 同步；`agate/phase-cards/P4-implementation.md`
  「自查≠gate」节新增"UI/需构建任务 P4 后应构建并确认 dist 类产物存在"提醒（TQC0001 跨项目反馈
  实证：声明了 `env_constraints.deploy` 但全流程从未主动执行，用户双击 exe 报缺 DLL 才补做）。
- **DEBT0011 修复：SELF-GATE 审查文件命名补任务标识防跨任务覆盖（BDD-7~8）**：
  `SELF-GATE.md` 成果文件/留痕文件命名模板从纯日期（`agate-alignment-review-{date}.md`）改为
  含任务标识（`agate-alignment-review-{date}-{task_id}.md`），消除同日多任务生成同名文件互相
  静默覆盖已提交历史审查记录的风险（TAG0016 实测复现并手工恢复过一次）；
  `agate/assets/review-roles/protocol-alignment-review.md` 新增"Write 前检查"段落，要求写入前
  先确认目标路径是否已存在、是否为同一任务复核轮（可覆盖）还是他任务遗留（不可覆盖）。
- **DEBT0012 修复：`check-protocol-consistency.py` 新增 `--strict-errors-only` 模式（BDD-9）**：
  解决 `--strict`（WARNING-only 也 exit 2）与 `&&` 串联的 `gate_commands.P5` 组合在长期存量
  WARNING 债务下永久短路中断的问题——新增互斥模式 `--strict-errors-only`，仅 ERROR 非零
  （exit 1），WARNING-only 场景打印提示后 exit 0；既有 `--strict` 语义不变，仍可供专门清理
  WARNING 债务的任务主动选用。`phase-cards/P2-design.md` 增补 `--strict` 不放 `&&` 链路中间的
  指引 + 反例，本任务自身 `gate_commands.P5` 声明也改用 `--strict-errors-only` 以身作则。
- **DEBT0014 修复：Windows Store python3 占位符探测增强（BDD-10~12）**：
  `pre-commit-gate.sh` / `commit-msg-self-gate.sh` / `pre-push-gate.sh` 三处探测循环（结构一致，
  逐字同步改动）新增：① `AGATE_PYTHON` 环境变量显式指定时直接使用，跳过探测循环；② 探测循环
  内每个候选先做可执行性小测试，非零则跳过继续下一候选——默认路径即可绕过 Windows Store 占位符
  exe stub（命中后 exit 49 导致 hook fail-closed 阻断 commit）导致的 commit 阻断，不要求用户先
  知道环境变量才能规避问题。`agate/platform-notes.md`「已知限制」表 + Windows 原生章节、
  `AGENTS.md`「Gate 脚本分层」节同步补充说明（严格遵守 verification_env 约束，不含"已在 Windows
  实测通过"断言，本环境为 Linux，Windows 行为靠 CI matrix 冒烟 + 模拟 stub 回归验证）。

### 关键机制

- `is_gate_meta_key(key)`（`agate_common.py`）：4 处 `gate_commands` 键解析脚本共享判据，
  避免"改一处忘改一处"的重复失误来源再次出现（DEBT0010 根因）。
- `check-protocol-consistency.py --strict-errors-only`：ERROR-only 判定新模式，与既有 `--strict`
  （WARNING-only 也非 0）并列不冲突，互斥组参数校验。
- SELF-GATE 命名模板新增 `{task_id}` 占位符：`agate-alignment-review-{date}-{task_id}.md` /
  `agate-alignment-{date}-{task_id}-{NN}.progress.md`。
- `AGATE_PYTHON` 环境变量：3 个 hook 薄壳探测循环的显式覆盖机制，跳过探测直接使用指定解释器。

### 技术债关闭（TAG0017 修复，均登记于 `agate-workspace/debt/tech-debt.md`）

- DEBT0010（medium）：4 处 `gate_commands` 键解析脚本未排除 `_timeout_seconds` 后缀——已修复，
  closure_criteria 全部满足（四脚本统一改用 `is_gate_meta_key`；新增回归用例覆盖
  `P3_timeout_seconds`/`P5_timeout_seconds` 声明场景；全量 pytest 回归通过）。
- DEBT0011（medium）：SELF-GATE 审查文件纯日期命名跨任务覆盖——已修复，命名模板补
  `{task_id}` + `protocol-alignment-review.md` 新增写前防覆盖检查段落。
- DEBT0012（medium）：`check-protocol-consistency.py --strict` 与 `&&` 链路永久短路——已修复，
  新增 `--strict-errors-only` 模式 + 文档指引不再推荐 `--strict` 放 `&&` 链路中间。
- DEBT0014（medium，跨项目反馈汇入）：Windows Store python3 占位符命中探测循环阻断 commit——
  已修复，3 处 hook 薄壳同步增强 + `AGATE_PYTHON` 机制文档化。
- DEBT0015（medium，RM-AG0028/TQC0001 跨项目反馈）：`env_constraints` 声明性字段无执行/gate
  绑定——已修复，字段语义边界文档化（P2 卡片 + architect 角色）+ P4 卡片新增 dist 产物确认提醒。

## [0.54.0] - 2026-08-19

### 新增（TAG0016：agate 协议卫生与测试效率，RM-AG0025 + RM-AG0026）

- **协议文档职责边界与去重（RM-AG0025，BDD-1~10、19）**：全仓关键词交叉扫描核实 P0-brief 六处
  已知重复中四处成立（平台适配 ×3、阶段门槛表 ×2、派发 prompt 模板双源、重试上限表文档级
  ×2——实际权威文件对为 `state-machine.md` vs `rules/state-transitions.md`，非最初猜测的
  `dispatch-protocol.md`）、一处不成立（Pre-commit 清单已是正确"权威源+指针"模式）、并新发现
  一类未被预判的重复（8 张阶段卡片内联 `MAX=` 数值散落）。收敛为单一权威源 + 指针引用：
  `platform-notes.md`（平台适配）、`state-machine.md`（重试上限）、
  `assets/templates/dispatch-prompt.md`（派发 prompt 完整模板，`dispatch-protocol.md` 收窄为
  极简结构骨架）；7 份协议文档新增「职责边界」声明行（BDD-1/19）。
- **CHECK 12 防复发跨文件一致性检测（RM-AG0025，BDD-9~10）**：`check-protocol-consistency.py`
  新增结构化白名单锚点扫描（`AUTHORITATIVE_VALUE_ANCHORS` + `check_authoritative_values()`，
  沿用既有 CHECK 4/9/11 骨架），覆盖重试上限表（权威源 vs 指针文件 vs 8 张卡片内联值）跨文件
  一致性；扫描范围裁剪到目标小节（`extract_section()`），避免误吞同形态无关表格行（P4-review
  CRITICAL-2 修复）。
- **P5→P6/P8 跨阶段证据引用机制（RM-AG0026，BDD-11~18）**：`check-p6-provenance.py` 新增审计 7
  （`audit7_p5_evidence_reuse()`，三态判定 `reuse_allowed`/`reuse_blocked`/
  `no_reuse_claim_possible`，`git diff` 命令失败时 fail-closed 为 `reuse_blocked`，P4-review
  CRITICAL-1 修复）+ `--audit7-only TASK_DIR` CLI 模式（stdout 输出 `AUDIT7_RESULT:` 供主 Agent
  在 P8 场景消费判定结果）；`.state.yaml` 新增可选字段 `p5_pass_commit`（缺失时静默回退强制
  重跑，不影响存量任务）；`P5-verification.md`/`P6-acceptance.md`/`P8-release.md`/
  `verifier.md`/`dispatch-prompt.md` 五处协议文档同步落地"P5 全绿 + 验收/发布前无代码改动 →
  可引用 P5 证据、不必重跑全量"的操作规则；`dispatch-protocol.md` 新增「全量重跑点审计」小节
  （P5 首跑/P5 失败重跑/P6 refactor regression/P8 bump 后重跑，逐点标注必然/条件性质）。
- **xdist CI 观测试点（RM-AG0026，BDD-15~16）**：`.github/workflows/protocol-tests.yml` pytest
  job 新增 `continue-on-error: true` 的 `pytest -n auto` 耗时观测步骤，不影响门禁结果，仅在真实
  CI（4 核）留痕耗时数字供后续评估；「并行规则」第 4 条资源密集型判据（含 xdist）保持不变。
- **ADR-010：受控例外——满足客观可判定条件时允许复用既有验证证据**：记录"P5→P6/P8 间无代码
  改动时可复用证据、不重新执行验证"这一新架构原则（判定标准必须机器可判定 + 失败方向保守 +
  显式声明何时不可复用），在 ADR-004"完整重跑是安全网"哲学基础上开的受控例外口子。

### 技术债登记（TAG0016 dogfooding 过程中发现，均已登记 `agate-workspace/debt/tech-debt.md`）

- DEBT0009（low）：BDD-12 provenance 存储候选 C（commit message 派生）本次未采纳，记录权衡供
  未来 commit message 格式若被 gate 强校验后重新评估。
- DEBT0010（medium，扩充为系统性条目）：至少 4 个 `gate_commands` 键解析脚本
  （`agate-read-gate-commands.py`/`agate-gate-missing-cmds.py`/`agate-gate-p5-count.py`/
  `agate-read-p5-commands.py`）均未排除 `_timeout_seconds` 后缀键，把超时声明字段误判为待执行
  命令/待核实项。
- DEBT0011（medium）：`SELF-GATE.md` 的 `protocol-alignment-review` 成果文件/留痕文件按纯日期
  命名（不含任务标识），跨任务同日复用会静默覆盖已提交的历史审查记录（本次实测复现并手工规避）。
- DEBT0012（medium）：`check-protocol-consistency.py --strict` 在"仅 WARNING 无 ERROR"时返回
  exit 2，与 `&&` 串联的 `gate_commands.P5` 组合会因本仓库长期存量 WARNING 债务而永久短路
  中断（历史 P5/P8 commit 从未声称"0 WARNING"，只声称"0 ERROR"，印证长期实际验收标准）。

## [0.53.0] - 2026-08-19

### 新增（TAG0015：agate 复盘与反馈机制统一，RM-AG0020 + RM-AG0021）

- **复盘模板迁入协议本体（RM-AG0020，BDD-1~8）**：`docs/reviews/postmortem-template.md`
  git mv 为 `agate/assets/templates/retrospective-template.md`，补齐正文四节结构（事实基线 /
  做得好的 + 可复用模式 / 发现的问题 / 改进措施，BDD-1）、内容价值标准小节（机制缺口 / 可复用
  模式 / 归因到可行动层面的问题，BDD-2）、「发现的问题」节强制"归因层面：机制缺口 / 执行错误"
  二值字段（BDD-3）、技术债登记核对行强制说明（标记"是"必须填 DEBT/roadmap 编号，BDD-4）、
  「做得好的」节两类去向标注 + 强制追问句（BDD-5）、frontmatter 三机器字段
  `mechanism_issues`/`execution_issues`/`feedback_ready`（BDD-6）、「## agate 反馈」结构化节
  （BDD-7）；挂钩点落在 `agate/phase-cards/P8-release.md`「READY 收尾检查」节，模板不再游离
  于协议本体外（BDD-8）；`agate-workspace/roadmap/roadmap.md` 三处旧路径引用同步脚注更正
- **`check-retrospective.py` 路径与触发标的扩展（RM-AG0020，BDD-9~11）**：stderr 提示文案改为
  指向 `tasks/{Txxx}/retrospective.md`，不再提及 `docs/releases/`（BDD-9）；新增
  `_scan_debt_roadmap_signal` 检测分支，任务关联 DEBT/roadmap 条目时输出独立于异常模式的第二段
  "建议复盘"提醒（消息文案可区分，BDD-10），`exit code` 恒为 0 的既有契约未变；
  `agate/tests/unit/test_check_retrospective.py` 新增测试函数覆盖路径文案与两类信号（BDD-11）
- **`orchestrator-log` 语义扩展为"决策 + 依据"（RM-AG0020，BDD-12~14）**：`agate/state-machine.md`
  第 481 行规则文本追加"和触发决策的简要依据"分句（三项既有排除原样保留）；新增「L2 会话
  checkpoint（两件套）——`P{n}-checkpoint.md` + `task-session-summary.md`」小节，回答落盘
  时机/文件路径/与 orchestrator-log 关系/防 compact 策略四问（BDD-13）；核实
  `loop-orchestration.md`/`agate/assets/templates/task-files.md` 既有引用不与新语义矛盾，
  `task-files.md`「辅助文件」表新增两行说明两个 L2 文件（BDD-14）
- **`agate/AGENTS.md` 复盘位置措辞同步（RM-AG0020，BDD-15）**：区分"历史存量复盘仍在
  `docs/reviews/`（迁移前旧布局）"与"新复盘归 `tasks/{Txxx}/retrospective.md`"，消除过期声明
  对新复盘同样成立的推论
- **存量 5 份复盘文档标注（RM-AG0020，BDD-16）**：`docs/reviews/retrospective-tag0008-*.md` /
  `retrospective-tag0010-0011-*.md`（含同名 review）/ `retrospective-tag0013-*.md` /
  `retrospective-tag0014-*.md` 首行统一插入历史标注，指向新路径约定，文件原地保留不物理迁移
- **`agate-feedback.py` 新增（RM-AG0021，BDD-17~20）**：新脚本 `agate/scripts/agate-feedback.py`
  从复盘文档提取 `mechanism_issues`/`execution_issues`/「## agate 反馈」节结构化数据（BDD-17，
  ADR-007 合规复用 `agate-md-field-get.py` 单一双读工具）；输出脱敏（项目名 → `<PROJECT>`，
  绝对路径按项目根截断/替换 `<PATH>`，BDD-18）；`AGATE_FEEDBACK` 开关默认 `off`，未启用时不
  产生任何提取输出，exit code 明确提示功能未启用（BDD-19）；产出物为待人工提交的 JSON +
  Markdown 片段，脚本本身不调用 `git push`/`gh` 等网络提交命令，且不存在任何自动触发钩子
  （BDD-20）
- **`agate-md-field-get.py` 字段注册（ADR-007 合规）**：`NO_FALLBACK_BOOL_FIELDS` 新增
  `feedback_ready`，`NO_FALLBACK_LIST_FIELDS` 新增 `mechanism_issues`/`execution_issues`，
  三字段均为 `retrospective.md` 专用，纯新增不影响既有 4 个字段行为

### 测试

- 新增/扩展 `agate/tests/unit/test_check_retrospective.py`（BDD-9/10/11）+ 全新
  `agate/tests/unit/test_agate_feedback.py`（BDD-17~20）+ 全新
  `agate/tests/unit/test_retrospective_protocol_docs.py`（纯文档类 BDD-1/2/3/4/5/6/7/8/12/13/
  14/15/16），三文件合计 35 passed
- 全量 `pytest agate/tests/ -q --tb=no` → 932 passed + 2 skipped，无回归（基线 909 passed，
  净增 23）；`check-protocol-consistency.py --strict` → 0 ERROR
- **本版本无破坏性变更**：`check-gate.py` 零改动；`check-retrospective.py` `exit code` 契约
  不变；`agate-md-field-get.py` 新字段纯新增不影响既有消费字段；均为面向新场景的加性变更

---

## [0.52.0] - 2026-08-18

### 新增（TAG0012：agate 协议机制增强批）

- **verification_env 失败处理协议（RM-AG0014 主体，`dispatch-protocol.md`）**：新增可重试/不可重试判据表（含"机制误用型问题应立即改正声明方式"）、批处理要求（单轮 ≥2 待验假设须一次性列出批量验完）、止损轮次=2（与阶段 `retries[Pn]` 独立计数，不新增 `.state.yaml` 字段，超限转 PAUSED）、READY 后问题归属三判据（本任务遗留/环境本身问题/证据不足默认按前者）
- **环境准备职责边界（RM-AG0014 补充，`dispatch-protocol.md` + `P5-verification.md` + `P6-acceptance.md` + `verifier.md`）**：环境启动/维护/关停默认归主 Agent，subagent 默认只消费不自启；多个并行 subagent 共享环境由主 Agent 统一注入访问方式；`P5-verification.md`/`P6-acceptance.md`/`verifier.md` 改为引用式落地，不重复展开
- **`{key}_timeout_seconds` 字段（RM-AG0016，`P2-design.md` 卡 + `architect.md` + `task-files.md`）**：per-key 声明式超时基准字段（三档建议默认：单元测试 120s / E2E 300s / 构建类 600s，手动声明非自动推断），明确排除 P3（P3 继续走既有 `AGATE_TDD_TIMEOUT` env var 机制），缺字段行为等同现状（向后兼容，`check-gate.py` 不新增校验）
- **命令超时兜底 + 资源密集型默认串行（RM-AG0016，`dispatch-protocol.md` + `dispatch-prompt.md` 双源同步）**：subagent 执行任意 bash 命令前须设 shell 层超时（预期耗时 ×1.5，有 `_timeout_seconds` 声明则直接取值），超时/非预期失败固定三动作（停止执行/写 progress 记卡点/返回主 Agent，不自行换命令）；「派发编排机制」并行规则新增第 4 条"资源密集型默认串行"（全量 xdist 测试/CDP-Playwright E2E/构建打包默认不并行）
- **P0-brief 漂移判据（RM-AG0019，`P0-orchestrator.md` + `P1-requirements.md` 卡 + `state-machine.md`）**：严重漂移 3 条判据（任务目标方案不成立/`executor_env` 平台前提不成立/`known_risks` 已解决前提失效或已被他任务解决）+ 轻微漂移 2 条判据（局部细节变化/`env_constraints` 值刷新），命中严重 → 回 P0 重新立项；命中轻微 → 更新字段 + 标 `[P0_STALE: 漂移点]` 后继续
- **同类扫描/影响面梳理（RM-AG0013，`P0-orchestrator.md` + `P1-requirements.md` 卡 + `P2-design.md` 卡 + `analyst.md` + `architect.md`）**：P0"同类/影响面预判"节、P1"同类扫描（强制节）"、P2"影响面梳理（强制节）"三级递进；`analyst.md` 隐含需求清单新增"同类/影响面"维度 + "缺的是能力还是环境？"判断树；`architect.md` 批次设计前置检查项引用 P2 强制节

### 测试

- 新增 `agate/tests/unit/test_protocol_mechanism_anchors.py`：28 条 parametrize 用例，逐条 grep 断言审计上述新增机制的关键词锚点已落盘（覆盖 BDD-1~22 + BDD-15b，共 23 条 BDD）
- 全量 `pytest agate/tests/ -q --tb=no` → 909 passed + 2 skipped，无回归；`count-tests.sh` → 911（≥749 单调不减）；`check-protocol-consistency.py --strict` → 0 ERROR（与改动前基线逐行 diff 比对，WARNING 集合完全一致，未新增）；`shellcheck -S warning agate/scripts/*.sh` → 0 issue
- **本版本无破坏性变更**：`timeout_seconds` 为纯声明性可选字段（`check-gate.py` 未新增校验，无运行时消费方）；新增文档强制节/checklist 项为人工评审流程要求，不对应任何 gate 脚本 exit code 变化；`.state.yaml` schema 无新增字段；`agate/scripts/` 目录零改动（仅新增 1 个测试文件于 `agate/tests/`）

---

## [0.51.0] - 2026-08-18

### 新增（TAG0006：agate UI/UX 验收质量机制）

- **P1 vision 能力三态硬声明（check-gate.py gate_p1）**：`domains` 含 `frontend` 的任务 P1 必须在 `capability_requirements` 声明视觉能力条目（`need`/`name` 含 visual/vision）且 `status ∈ {available, supplementable, GAP}`；缺失/非法 → exit 1。既有任务无 frontend domains 不触发（向后兼容）。
- **P1 渲染形态/维度声明（可选字段）**：frontmatter 新增可选 `ui_render_shape`（规范值 layout / render_component / temporal_effects）+ `ui_ux_dimensions`（presence 语义，缺失 = 布局型默认，不破坏性）；跨阶段一致（I14）由 P2 gate + P7 CHECK 11 校验。
- **P2 UI 设计节检查（check-gate.py gate_p2）**：`ui_affected: true` 的 P2-design.md 必须含「UI 设计」节（渲染形态声明 + 按形态 checklist：常规布局型布局/交互/视觉；渲染组件型渲染正确性/动效时序）+ P1-P2 形态一致性规范化值比对；缺节/缺声明/不一致 → exit 1。由 architect 兼任产出，**不新增 designer 角色**。
- **P6 三态分档双证据 + 证据形式按形态（check-p6-evidence / check-p6-provenance）**：P1 vision=GAP → 降级为像素检测 + 人工复核记录；available/无声明（默认 available）保留既有 R1b vision YAML + blocker_count 强制。渲染组件型形态可用帧序列 / 渲染输出对比 / 时序截图，纯文本证据拦截。
- **输入态/交互形态变化类人工复核（BDD-13）**：该类 BDD 结论必须附人工复核记录。
- **P7 一致性 CHECK 11（check_uiux_doc_anchors）**：断言各协议文档含 UI/UX 机制条文锚点，防文档-脚本-单测三件套漂移。
- **plan-design-review 维度五维→七维**：新增视觉设计/交互设计细节/渲染正确性与时序 0-10 可判定评分项 + 七维边界注。
- **dispatch-prompt 新增「能力自查（强制）」节 + A3 视觉 supplementable 注入**：subagent 无法调用视觉能力时须报告 [CAPABILITY_GAP] 走降级，不静默假设。

### 变更（行为变化，需读者注意）

- **avg-hash 雷同截图判定升级（check-p6-evidence.py avg-hash）**：视觉高度相似截图从非阻断 WARNING（exit 2）升级为「降级待复核」——含人工复核记录 → 放行；无记录 → exit 1 阻断。md5 硬阻断语义不变。帧序列/时序截图按同 BDD 组（bdd-id 前缀）豁免相邻样本。**本行为变化对所有任务的 P6 截图证据路径生效，见 `agate/UPGRADING.md` v0.51.0 章节。**

### 测试
- P3 53 新增用例（test_check_gate / test_check_p6_evidence / test_check_p6_provenance / test_review_role_docs）；全量 pytest 881 passed + 2 skipped 无回归；consistency 0 ERROR；count-tests 883（≥749 单调不减）。

---

## [0.50.0] - 2026-08-16

### 新增（TAG0008：agate 版本管理机制 v1）

- **`agate-install.py`（新，版本安装/卸载/环境探测）**：无参 = 装 latest 指针（最新发布版）；`agate-install v0.48.0` = 装指定版本（repo 单克隆 + `git worktree add` tag）；`--uninstall vX` = 删版本目录 + worktree remove + 清理/重指指针（含项目引用保护扫描，被引用版本拒绝卸载）；`--check` = 环境探测（python3/pyyaml/git/bash，exit code 可判 + 分平台修复指引）。重复安装幂等（版本目录已存在即跳过）。`~/.agate` 从单软链升级为版本管理根目录（`repo/` + `vX.Y.Z/` + `latest`/`current` 纯指针）
- **`agate-resolve.py`（新，版本解析 CLI）**：cwd 向上找 `.agate-version`（asdf 模式，支持 `agate: vX.Y.Z` 精确版本）→ 映射版本目录 → 输出 AGATE_ROOT/AGATE_VERSION/AGATE_REASON；优先级 env 最高 → 项目声明 → current → legacy 软链兜底；解析失败回退 current 绝不静默禁用 gate
- **`resolve-entry.py`（新，hook 固定解析入口）**：install-hook 安装固定入口而非具体版本脚本；运行时读项目 `.agate-version` → exec 对应版本 gate py。项目 A 锁旧版、项目 B 用新版互不干扰；切版本不用重装 hook
- **`agate-pack-offline.py`（新，外网离线打包器）**：`agate-pack-offline.py vX.Y.Z [--platform linux-x86_64|windows-x86_64] [--include-python] [--include-pillow]` → 平台标签 bundle（tag 代码 + 目标平台 wheels（`pip download --platform`）+ 可选嵌入式 Python + manifest.json 含 sha256 checksum）；失败路径（tag 不存在/网络失败/wheel 缺失）非 0 退出不产坏包
- **`install-offline.py`（新，内网一键安装器）**：读 manifest.json 核对平台（不匹配警告拒绝安装 fail-closed）+ 校验 checksum（不匹配拒绝）→ `pip install --no-index --find-links wheels/` → 建 `~/.agate/vX.Y.Z/` + hook/orchestrator 指向（Linux 软链 / Windows 复制模式）+ 验证闭环；`--skip-python`/`--skip-pillow` 覆盖勾选
- **`agate-summary.py` 语义迁移**：从"仓库自身 tag"改为"项目解析到的版本 + 原因"（`.agate-version` 声明或全局 current）
- **3 个内联解析脚本统一归口 `agate_common.resolve_agate_root`**：agate-inject-card / agate-next-card / agate-render-dispatch-prompt 不再各自内联解析，避免解析入口分叉
- **`agate_common.py` 集成项目版本解析**：`resolve_agate_root` 扩展四层语义（env 最高 → 项目声明 → current → legacy 软链兜底），作为全部 gate 脚本统一解析入口

### 变更（文档层联动）

- **`agate/SETUP.md` 新增「环境准备（agent 执行）」节**：探测命令 exit code 可判 → 分平台修复 → 验证闭环
- **`agate/UPGRADING.md` 新增本版本章节**：破坏性变更逐条列（~/.agate 目录化 / .agate-version 语法 / hook 解析入口迁移 / agate-install 新工具）
- **`agate/scripts/README.md` 脚本清单补 4 新脚本 + resolve-entry** + 解析入口说明；`check-protocol-consistency.py` CHECK 10 白名单补 install-offline / resolve-entry（命名联动，判定逻辑未改）
- **README / README.zh-CN / AGENTS / WORKFLOW / platform-notes / adr / project.md 模板 / install.sh**：版本目录与解析叙述联动
- **install.sh 兼容保留**：单软链场景仍可用，作为 agate-install 的底层/替代入口

### 测试

- 6 个新测试文件（resolve 3 + install 1 + offline 2）+ test_install_hook / integration hook 测试修正，31 条 BDD 全 PASS；全量 pytest 823 passed + 新增 29 passed；consistency 0 ERROR；ruff 通过
- **本版本破坏性变更（存量 `~/.agate` 单软链用户升级路径）**：见 `agate/UPGRADING.md` v0.50.0 章节——不跑新工具时 legacy 软链直接解析为 AGATE_ROOT（BDD-30 向后兼容红线），存量用户无感

## [0.49.0] - 2026-08-16

### 新增（RM-AG0016：派发编排机制）

- **`dispatch-protocol.md`「任务粒度指引」节升级为「派发编排机制」权威节**：新增工作量评估五维评级表（产出规模/输入规模/改动性质/耦合度/认知负荷）、五模式编排（单发/静态拆批/并行/先理解后拆/串行链）、模式 4 三步流程（侦察→执行→合并，含 BDD 全局编号 + 包归属去重合并语义）、并行规则三要素（上限默认 3 / retry 与 retries[Pn] 对齐整组计 1 次 / 共享文件统一后处理 + P6 例外）、P1-P8 全阶段适用表；既有有效规则（输入/产出上限、拆分判据、T016/T026 教训、P7 例外、状态机不变）原位保留
- **P2-design.md 新增可选 `dispatch_plan:` 机器字段**：frontmatter 单行 flow YAML（mode/batches/parallel_limit），由 `agate-md-field-get.py` 新增 `dispatch_plan` op 输出 JSON（`json.dumps` ensure_ascii=False），check-gate.py P2 分支校验（mode 枚举 / parallel_limit≥1 / batch id+complexity / 批数≤上限），缺字段/坏 YAML 跳过不误拦（向后兼容）
- **`architect.md` 新增"批次设计"强制节**：high 复杂度必须拆批；批次粒度受工作量评估约束
- **`dispatch-prompt.md` + 协议内联节新增任务粒度兜底**：产出 >3 或输入 >5 须分批派发或说明理由

### 变更（阶段卡片统一引用权威节）

- **P3/P4/P5/P6 卡片「按包拆分并行」节改为引用权威节并行规则**，阶段特定约束原样保留（P3 拆分判据 / P4 共享文件后处理 + 基础设施隔离 + 串行默认值 / P5 端口/数据库/临时输出/E2E 隔离 / P6 证据并行 + 汇总 verifier）
- **P7 卡片表述更新**：输入数量豁免为"模式 1 单发 + 输入数量豁免特例"（保留跨文件一致性理由）
- **P1 卡片新增复杂需求编排（模式 4）**：侦察 subagent + 合并语义（BDD 全局编号、包归属去重）
- **P8 卡片新增多包发布拆批**：多 releaser 并行各写 P8-release-{pkg}.md → 合并 subagent 整合唯一 P8-release.md

### 测试

- 10 条新增用例（test_dispatch_orchestration.py 8 条 + test_agate_md_field_get.py +2），11 条 BDD 全 PASS；全量 pytest 全绿；consistency 0 ERROR；ruff 通过
- 本版本**无破坏性变更**：dispatch_plan 为可选字段，缺字段任务行为等同现状

## [0.48.0] - 2026-08-16

### 新增（RM-AG0015：CHECK 10 文档脚本名引用漂移 gate）

- **`check-protocol-consistency.py` 新增 CHECK 10「协议文档脚本名引用漂移」**：扫描协议文档面（`PROTOCOL_FILES` + `PROTOCOL_DIRS` + 根级 README/AGENTS + `agate/UPGRADING.md` + `agate/scripts/README.md` + `CHANGELOG.md`）中的脚本名引用（裸名 + `scripts/` 前缀 + `agate/scripts/` 全路径），对照 `agate/scripts/` 实际文件，漂移报 ERROR——脚本删/改名后文档漂移不再无人拦截（DEBT0001 关闭）
- **豁免 5 类**：UPGRADING.md 整文件（历史迁移对照）/ formatters 名（`agate/assets/formatters/`）/ 3 个 hook 薄壳（`pre-commit-gate.sh` / `commit-msg-self-gate.sh` / `pre-push-gate.sh`）/ `count-tests.sh`（同名不同目录）/ scripts/README.md 退役名
- **`agate/phase-cards/` 与 `agate/rules/` 纳入 `PROTOCOL_DIRS`**：必读卡的引用检查升级为严格（CHECK 2/3 对它们按协议文件检查，实测无新 ERROR）
- **main() CHECK 状态匹配修复**：`startswith(key)` → `split("-")[0] == key`（修复 CHECK 1/CHECK 10 前缀碰撞导致的状态行误标）

### 变更（RM-AG0017：self-gate 触发面）

- **`commit-msg-self-gate.py` 触发面补 `README.md` / `AGENTS.md`**（根级精确名锚定；`CHANGELOG.md` 天然豁免，频繁变动不触发噪音），stderr 提示文案同步

### 变更（RM-AG0018 剩余：复盘登记提醒）

- **`check-retrospective.py` warnings 块追加「新缺口请登记 DEBT/roadmap」提醒行**（纯提醒不拦截；无异常模式时输出为空，RT.1 不回归）

### 测试

- 19 条新增用例（count-tests 770 = 基线 751 + 19），11 条 BDD 全 PASS；全量 pytest 768 passed / 2 skipped / 0 failed；consistency 0 ERROR；ruff 通过
- 本版本**无破坏性变更**：CHECK 10 为增量检查（当前 0 漂移），self-gate 触发面扩展与复盘提醒均为内部行为，用户可见协议语义不变

## [0.47.0] - 2026-08-15

### 破坏性变更（TAG0011 测试框架迁移：Bats → pytest）

- **`agate/tests/` 下 60 个 `.bats` 文件（749 @test）迁移为 `test_*.py` pytest 用例并退役删档**：46 unit + 6 regression + 6 integration + sanity + scripts 扫描器，`.bats` 文件 0 残留；`count-tests.sh` 改写为 pytest 收集计数
- **`agate/tests/helpers/` 三文件（load.bash / fixtures.bash / git-helper.bash）退役**：职责并入 `agate/tests/conftest.py` fixture 体系（含合并流 `.output` 复刻 bats `$output` 语义）
- **`check-windows-smoke.sh` / `.bats` 退役**：Windows 冒烟由 `@pytest.mark.windows_smoke` marker（78 用例）承接
- **测试依赖变更**：Bats + shellcheck → pytest + pyyaml（仅 3 个 hook 薄壳仍需 sh/shellcheck）
- **CI 变更**：`protocol-tests.yml` 的 bats job → pytest job（job 名变更影响分支保护 checks）；ruff 覆盖扩展至 `agate/`

### 新增

- **`agate/tests/conftest.py`**：pytest fixture 体系（run_cli/CommandResult 合并流、task_dir、git_repo、add_* 纯函数、python_exe、agate_root 解析）
- **`windows_smoke` marker**：78 个代表用例（每文件第 1 个 + 平台关键词）供 Windows CI 冒烟
- **`pyproject.toml` pytest 配置**：`[tool.pytest.ini_options]`（testpaths + markers 注册）

### 变更

- 12 条 BDD 全 PASS（pytest 750 collected / 748 passed / 2 skipped + consistency 0 ERROR + ruff 0 error）
- UPGRADING.md v0.47.0 迁移章节（破坏性变更逐条 + 迁移命令）

---

## [0.46.0] - 2026-08-15

### 破坏性变更（TAG0010 agate 产品逻辑 Python 化：30 个脚本跨语言迁移）

- **`agate/scripts/` 全部 30 个 `.sh` 的 bash 逻辑迁移为 Python（`.py`）**：24 个同名换后缀（check-changelog/check-frontmatter/check-state-yaml/check-p6-format/check-scope-resolved/agate-archive-stale-outputs/agate-extract-context/agate-next-card/agate-render-dispatch-prompt/agate-summary/agate-changes/agate-migrate-workspace/check-platform-assumptions/check-state-transition/check-retrospective/check-pruning/check-debt/check-tdd-red/check-gate/check-p6-evidence/check-p6-provenance/agate-capture-env-baseline/agate-retreat-to/agate-inject-card）+ `install-hook.sh` → `install-hook.py`；直接调用脚本的用户调用命令从 `bash xxx.sh` 改为 `python3 xxx.py`
- **3 个 git hook 入口保留 `.sh` 薄壳**（pre-commit-gate / commit-msg-self-gate / pre-push-gate）：只做「AGATE_ROOT 自定位 + python 探测 + exec py 主程序」，失败 **fail-closed 阻断 commit**（无 sh 兜底逻辑）
- **`gate-result.sh` + `agate-workspace-resolve.sh` 删档并入 `agate_common.py`**：函数库合并为单一公共模块，执行模式输出 `AGATE_WORKSPACE=`/`AGATE_TASKS_DIR=` 两行（契约不变）
- **pyyaml 从「可选」变「强制依赖」**：缺失时 fail-closed exit 1；Pillow 仍为可选
- **shellcheck → ruff**：shellcheck 扫描面收敛到 3 个 hook 薄壳；Python 脚本改用仓库根 `pyproject.toml` 规则集，CI 新增独立 ruff job
- **无 bash 环境（纯 cmd/PowerShell）成为可行选项**：gate 脚本全部 Python 化可直接运行（仅 git hook 入口薄壳仍需 sh）
- 已部署项目升级指引见 `agate/UPGRADING.md` v0.46.0 章节

### 新增

- **`agate_common.py` 公共库**：承载原 gate-result.sh + agate-workspace-resolve.sh 全部函数库；MAX_RETRY_MAP 单一数据源
- **`install-hook.py`**：软链安装（Windows 复制模式 + 写 `.agate-root` 标记）+ chmod + 备份既有 hook + `.gitignore` 检测
- **`pyproject.toml` ruff 规则集**：`target-version = "py38"` + select/ignore 组合使全部 py 0 违规
- **hook 链 Python 化**：pre-commit-gate.py / commit-msg-self-gate.py / pre-push-gate.py 承载完整调度逻辑
- **`check-platform-assumptions.py`** 扩展覆盖 `.py` 扩展名 + docstring 块豁免

### 变更（实现细节，行为等价）

- `ci-gate-backstop.py` `resolve_tasks_dir` 改调 `agate_common.resolve_workspace`
- bats 机械调用面 sh→py 全量同步；5 个测试文件断言级调整（38→40 用例）
- check-gate.py 拆 P0-P8 分支子任务实现

---

## [0.45.0] - 2026-08-14

### 修复（TAG0005 agate 机制修复批：4 个已核实机制/契约缺陷）

- **RM-AG0010 C8 表补 backend 域 P2 评审**：role-system.md / rules/review-mapping.md / phase-cards/P2-design.md 三处 C8 映射表 backend 行新增 `plan-eng-review（P2 方案评审）`（保留既有 `review（P4 后）`），附去重说明（同任务命中同一评审角色只派发一次）——消除「P2 gate 强制要 P2-review.md 但 C8 无触发角色 → 主 Agent 被迫自造评审」契约矛盾；check-gate.sh P2 分支未改（无条件要求保留）
- **RM-AG0011 P5 gate_commands 主/辅命令计数语义**：`agate-gate-p5-count.py` 输出改单行双值 `{main} {aux}`（main 精确匹配 `P5:`、aux 为 `P5_*` 且排除 `_formatter`，与 read-p5-commands.py 执行枚举对齐）；check-gate.sh P5 WARNING 文案改为「X 个主命令 + Y 个辅助命令（共 Z 条 gate_commands.P5 命令）」；仅 P5 无辅助命令时不 WARNING（行为不变）
- **RM-AG0012① Review 角色特别指令按角色类型条件注入**：`assets/templates/dispatch-prompt.md` 将「Review 角色特别指令」从主代码块拆为「## 阶段特定提示」下独立子块；`agate-render-dispatch-prompt.sh` 按 `ROLE_DIR=review-roles` 追加该节（组装顺序 main_block → review_appendix → 阶段 appendix）——执行角色派发 prompt 不再含 status draft→approved 评审语义，评审角色含完整语义
- **RM-AG0012② render 角色文件不存在 exit 2 回归锁定**：行为 v0.23.0 已修复（exit 2 + stderr 报错），本任务新增 RP.17 bats 测试锁定
- **RM-AG0003 空返回自动重试（增量增强）**：dispatch-protocol.md 空返回恢复策略「第 1 次空返回」新增步骤 a——相同 prompt 原样自动重试一次（不占用 retries[Pn] 槽位），会话时长 <1min 输出「会话时长异常短」告警；自动重试仍空返回才进入既有 retries[Pn] 流程；「相同 prompt 直接重试」禁令的唯一豁免（仅限首次/单次/原样重发）；retry 上限/PAUSED 规则未改
- **同类扫描守卫 / check-debt.sh 依赖加载失败 exit 2**：`check-debt.sh --retreat-coverage` 依赖 agate-workspace-resolve.sh 加载失败（source 失败或文件缺失）从「stderr 报错但 exit 0」改为 **exit 2**（需主 Agent 自判，与 check-gate.sh 约定一致）；「无 retreat 提交」有意跳过分支保持 exit 0；`rg '>&2;\s*exit 0' agate/scripts/*.sh` 仅剩 3 处「跳过」语义（agate-capture-env-baseline.sh）

### 新增（TAG0009 测试套件平台无关化）

- **平台假设静态扫描器 gate**：`agate/scripts/check-platform-assumptions.sh`（bash + POSIX ERE，自身平台无关）扫描 `agate/tests/` 全树的 Unix 假设（R1 硬编码 PATH / R2 命令位置裸 python3 / R3 `[[ -L ]]` symlink / R4 /tmp 逻辑路径 / R5 Unix-only 工具），CI `platform-scan` job（Linux 阻断 + Windows 等价证明）阻断新假设
- **PYTHON 探测 + harness shim helper**：`agate/tests/helpers/fixtures.bash` 新增 `detect_python` / `PYTHON` 导出（优先 python3 回退 python）+ `create_python_shim_bin`（临时 bin 的 python3 包装器内嵌真解释器绝对路径，测试运行产品脚本时前置 PATH，覆盖 41 例 script-side 裸 python3 失败）+ `SHELLCHECK` 导出（shellcheck|shellcheck.exe 探测）
- **bats job Windows matrix（技术路线冒烟）**：`protocol-tests.yml` bats job 增 `windows-latest`，但 Windows 分支**不跑全量**（747 用例 ~11.5 分钟，随测试增长线性上升、阻塞 CI）——改为跑 `agate/tests/scripts/check-windows-smoke.sh`（对每个 .bats 文件选第 1 个用例 + 名称含平台敏感关键词的用例，约 60 文件代表子集，`xargs -P 4` 并行约 2 分钟）。功能正确性由 Linux 全量保证，Windows 只验证每条平台敏感机制（py_path / shim / cp1252 / CRLF / symlink / 盘符路径等）的代表用例跑通——技术路线成立则共享同机制（helper/shim/setup）的同类用例在 Windows 应同样通过

### 变更

- **agate-extract-context.sh bc→awk**：P5 failed 求和 `paste -sd+ | bc` → `awk '{s+=$1} END{print s+0}'`（POSIX 工具 Windows Git Bash 自带，同时消除原 `|| echo 0 | tail -1` 管道优先级隐患）
- **24 个测试文件平台无关化**：测试侧裸 python3 → `$PYTHON`、`env -i PATH="/usr/bin:/bin"` → `env -u PATH`、`[[ -L ]]` symlink 断言按平台分支（Linux readlink / Windows 复制模式 WARNING）、`/tmp` 逻辑路径 → `$BATS_TEST_TMPDIR`、输出匹配 CRLF 归一化（`tr -d '\r'`）、cp1252 编码模拟用例；新增 helpers-python.bats + check-platform-assumptions.bats（14 例）+ CI 扫描器行为测试 step
- **check-protocol-consistency.py**：CHECK 9 锚点表补 `check-platform-assumptions.sh`（反向覆盖要求）

### 测试

- 全量 740 bats（基线 714 + TAG0005 12 + TAG0009 7 + WSMOKE 7）+ consistency 0 ERROR + shellcheck 0 error + 平台假设扫描器零命中

### 文档

- 三处 C8 表去重说明 / dispatch-prompt.md 模板结构调整 / dispatch-protocol.md 空返回策略与内联模板评审语义备注 / scripts/README.md check-debt 描述同步 / tests/README.md 计数表同步

## [0.44.0] - 2026-08-13

### 修复（TAG0004 脚本健壮性 + 环境适配：Windows 原生兼容 + Linux 基线回归）

- **S1 pre-commit-gate.sh 空格路径 fail-open 修复**：`STAGED_STATE_FILES` / `PROCESSED_DIRS` 由空格拼接字符串 → bash 数组（L50/57/339/343/350），消除目录/文件名含空格时静默绕过 gate 的 fail-open 风险；新增空格路径 commit 场景 fixture 回归
- **S3 13 个 py 文本 open() 补 encoding="utf-8"**：全部文本读写加 `encoding="utf-8"`（Image.open 与二进制模式除外），修复中文路径/内容在非 UTF-8 locale 下解析失败；新增 grep 断言审计测试作永久回归拦截
- **S2 check-p6-evidence.sh 中文证据文件名支持**：证据引用正则字符类加宽（`\([^()]*[^()[:space:]]\.[a-zA-Z0-9]+[^)]*\)`），中文/含空格文件名正确匹配，维持"必须有扩展名"结构（无扩展名仍拒绝）
- **M4/M5 全角冒号 POSIX locale**：check-gate.sh L356/357 与 check-p6-format.sh L69 的 `[:：]` bracket 改 alternation（`(:|：)`），修复 `LC_ALL=C` 下全角冒号不匹配（与 v0.40.3 L84 修法统一）
- **M6 frontmatter 提取 CRLF 容错**：frontmatter 提取入口（agate-md-field-get.py / agate-frontmatter-check.py / check-gate.sh 8 处 sed / check-frontmatter.sh 链路）统一剥离行尾 `\r`，Windows checkout 的 CRLF md 也能正确提取；不动 .gitattributes，历史 CRLF review 文件不受影响
- **M9 路径正则元字符**：pre-commit-gate.sh 的 `^${TASK_REL}` grep -E 拼接改 grep -F 字面前缀 + `awk index($0,p)==1` 行首锚定（L102/104/133/228/290 共 5 处），目录名含 `[`/`]`/`*` 时不再误判
- **Q1 agate-next-card.sh 路径归一化**：`${CARD_FILE#$AGATE_ROOT/}` 前缀剥离改"先试直接剥离、失败则归一化后剥离"（rel_card + 盘符小写），修复 Windows 盘符/混合斜杠下卡片 hash 校验失败（TQC0001 实测）；Linux 相对路径输出逐字节不变
- **Q2 7 张 phase-cards 补注规则 2 语义**：P1/P2/P3/P4/P6/P7/P8 卡片"更新 .state.yaml phase"步骤对齐 git-integration.md 规则 2——commit 时 phase = 本 commit 产出阶段，下一阶段推进随下一阶段产出同 commit（与已对齐的 P5 卡一致，纯文档，gate 判定逻辑零改动）
- **Q5 SETUP.md Windows 章节 + .gitignore 预设**：SETUP.md 扩展独立 Windows 章节（AGATE_ROOT Unix 风格路径 / PATH 注入风险 / PYTHONUTF8=1 / core.autocrlf 与 CRLF）；.gitignore 模板预设 `!version.txt` + `dist/`
- **RM-AG0001 check-gate.sh P1 反引号盲区**：行首标记正则（`[SUGGEST:` / `[NEED_CONFIRM]` / `[NO_NEED_CONFIRM]`）加可选反引号容错（L69/71/89/109/121/125/129），`` `[SUGGEST: ...]` `` 正确计 WARNING、`` `[NEED_CONFIRM]` `` 正确阻塞
- **RM-AG0002 + TPV0090-M4 check-tdd-red A/B 判定增强**：无 formatter 时不再纯 exit-code-only——exit 1 且输出含 compile/error 关键词判 A 类，普通失败仍判正确红灯；formatter 路径 B 类检测纳入 NameError（pytest.sh 增 name_errors 数组），非 NameError（TypeError 等）仍判 A 类；globals().get() 规避模式保持向后兼容
- **其他-a .agate.env CR 剥离**：agate-workspace-resolve.sh 读取 `.agate.env` 值前 `tr -d '\r'`，Windows 编辑的 CRLF env 文件不再导致路径含 `\r`
- **其他-b 复制模式 AGATE_ROOT 解析回退**：install-hook.sh 复制模式写 `.agate-root` 标记文件，pre-commit-gate.sh readlink 解析失败时读标记兜底，Windows 复制模式 hook 不再静默放行
- **其他-c render-dispatch-prompt sed 转义**：agate-render-dispatch-prompt.sh 替换串转义 `&`/`|`（awk gsub + 反斜杠预处理），AGATE_ROOT 含 `&`/`|` 时替换不再错误

### 新增
- **CI windows-latest matrix**：`.github/workflows/protocol-tests.yml` 新增 `windows-latest` 平台矩阵（bats / shellcheck / consistency / gate-backstop），Windows 原生兼容的唯一兜底验证（本环境为 Linux，不宣称"已实测 Windows"）
- **S3 grep 断言审计测试**：扫描 `agate/scripts/*.py` 文本 `open(`/`read_text(` 必须带 `encoding=`（Image.open 与二进制模式除外），防后续改动漏加 encoding

### 文档
- **SETUP.md Windows 章节**（见上 Q5）
- **Q2 七张阶段卡片规则 2 语义补注**（见上 Q2）

### 变更
- **S1 数组化**：pre-commit-gate.sh 内部结构改动，行为语义不变（见上 S1）

---

## [0.43.0] - 2026-08-12

### 新增（TAG0001 技术债登记闭环，Phase 1-3）
- **DEBT 条目模板 `assets/templates/tech-debt-template.md`**：标准技术债登记格式——用法/判据三分法（技术/管理/协议）+「都不影响→不登记」出口 + 三态（open/in_progress/closed）+ 字段表 + 可解析示例条目；落点 `{AGATE_WORKSPACE}/debt/tech-debt.md`（单文件多条目，每条 fenced yaml 机器块 + 可选正文）
- **`agate-debt-check.py` + `check-debt.sh`**：技术债 schema 校验器（fail-closed 薄壳 + 独立 .py）——必填字段 / 枚举（category/status/priority/source）/ 类型 / closed 准入（须 task_id + evidence 引用 P5/P6 证据）/ 同文件 id 唯一性；无任何 yaml 块 → no-op（向后兼容）
- **`check-debt.sh --retreat-coverage` 回退覆盖比对**：`git log --all --grep='^retreat:'` 提取回退提交，与 `source: retreat` DEBT 条目 evidence 引用比对，未登记 → WARNING（恒 exit 0，只读提醒不挂 gate）
- **P8 `debt_check` 必填字段**：P8-release.md 产出规格新增（`none` = 本次无关注项 / `reviewed` = 已核对并附条目清单）；check-gate.sh P8 分支缺失即 exit 1 硬拦截、内容任意放行不阻断发布；`debt_check: none` 可跨发布 grep 计数（防无脑打勾可观测）

### 变更（TAG0001 debt/ 归类修正 + 回退强制）
- **工作区子目录集 8→9**：新增 `debt/` 技术债登记目录（WORKFLOW.md 目录图 + orchestrator-template/SETUP/state-machine 三处 mkdir 同步同一 9 集字面量）；tech-debt 不再归入 `agents/`（该目录只放 agent 输入知识 project.md/memory）
- **回退落地后必须建 DEBT 条目**：`rules/state-transitions.md` 回退规则 + P6/P4 卡片 + `agate-retreat-to.sh` 回退完成提醒 四处同步「`source: retreat` 条目，evidence 引用回退提交哈希」强制
- **review 可发现性**：`plan-eng-review.md` 追加「提债须用标准 DEBT 条目格式」

### 文档
- **UPGRADING.md v0.43.0 节**：子目录 8→9（可选启用）/ tech-debt 路径 / P8 debt_check / 回退强制四项升级指引
- **TAG0003 BDD-1 口径修订注**（P1/P6 各一行）：8 子目录 → 9 子目录口径更新

---

## [0.42.0] - 2026-08-12

### 新增（TAG0002 重构一等任务机制，Phase A）
- **`change_type: refactor` 任务类型声明**（P1 frontmatter 可选机器字段，枚举 `{refactor}`，缺省 = 功能任务）：重构任务可在 P1 声明类型，gate/CI 按类型分流——`agate-md-field-get.py` 新增 `change_type`/`regression_pass` 读取 op；`agate-frontmatter-check.py` P1 schema 增枚举校验
- **P6 重构验收口径（回归口径，非功能 BDD 口径）**：change_type=refactor 的任务，P6 验收改为三段式——行为不变声明 + 全量回归全绿（frontmatter `regression_pass: true` + `P6-evidence/regression.log` 尾行 `EXIT_CODE: 0` 双证）+ 关键路径行为不变 BDD 逐条 PASS/FAIL；`check-gate.sh` P6 分支按 change_type 分流硬校验（缺回归双证 → gate 不通过）
- **P3 重构回归测试口径**：refactor 任务 P3 走回归测试设计（既有用例覆盖映射，不新增功能行为断言），跳过 TDD 红灯步骤（红灯语义不适用）；`ci-gate-backstop.py` P3 分支对 change_type=refactor 任务跳过 check-tdd-red 兜底（避免全量即绿被误判 FAIL）

### 变更（TAG0002 重构一等任务机制，Phase A）
- **重构验收口径对 no_behavior_change 独立**：refactor 判定只看 change_type，不读 no_behavior_change——即使重构任务声明 no_behavior_change，回归双证仍强制（换口径 ≠ 裁 P6，P6 仍不可裁剪）；WORKFLOW.md/state-machine.md/dispatch-protocol.md 同步"P6 不可裁剪"表述
- **可发现性**：P1/P6/P3 卡片 + verifier/test-designer 角色 + P5/P6/P3 派发指引补充 refactor 口径说明；明文禁止"为凑验收数量新增功能性质 BDD"

### 文档（TAG0002 重构一等任务机制，Phase A）
- P6-acceptance.md / P1-requirements.md / P3-tdd.md 卡片 refactor 分支说明；verifier.md / test-designer.md 角色口径

---

## [0.41.0] - 2026-08-12

### 破坏性变更（TAG0003 工作区架构）
- **编排状态迁移到工作区（agate-workspace/）**：agate 的全部编排状态（任务/看板/归档/评审/决策/计划/日志/roadmap/agent 知识）从项目 `docs/tasks/`、`docs/agents/`、`docs/archived/` 迁移到**工作区**（默认项目根 `agate-workspace/`，可用 `.agate.env` 的 `AGATE_WORKSPACE=` 配置位置）。orchestrator 从工作区读取 `agents/project.md` 与 `tasks/active-tasks.md`，不再读 `docs/` 下旧路径——**影响所有已部署项目**。⚠️ 存量项目升级前必读 `agate/UPGRADING.md` §3「v0.41.0」迁移节（迁移工具步骤见下）
- **新增迁移工具 `agate-migrate-workspace.sh`**：目录级 `git mv` 强制迁移 `docs/tasks/` → `{workspace}/tasks/`、`docs/archived/` → `{workspace}/archived/`，保留 git 历史；空源 no-op、重复运行幂等、外部工作区 fallback 普通 mv（WARNING 标注历史不可在新路径追溯）。在项目根运行 `bash {agate_root}/scripts/agate-migrate-workspace.sh`
- **未迁移时的行为**：orchestrator 启动检测到旧布局（项目 `docs/` 下存在旧版 `tasks/active-tasks.md` 而工作区 tasks 无 active-tasks）→ 输出迁移指引并停止自动推进，不静默使用旧路径

### 新增（TAG0003 工作区架构）
- **`agate-workspace-resolve.sh`**：工作区路径单点解析器——解析优先级 `.agate.env`（`AGATE_WORKSPACE=`）> 环境变量 `AGATE_TASKS_DIR`（向后兼容既有 CI 设置）> 默认 `agate-workspace/`；输出 `AGATE_WORKSPACE` + `AGATE_TASKS_DIR`，bash（source 复用）与 python（ci-gate-backstop subprocess）共用，结构性保证本地 hook 与 CI 解析同路径。支持相对/绝对/含空格/项目外路径
- **roadmap 项目级任务管理循环**：新增 `assets/templates/roadmap-template.md` 单文件模板（对齐 active-tasks-template 模式），条目结构 `| id | 标题 | 状态 | 来源 | 关联任务 | 创建 | 更新 |`，状态标识 backlog/scheduled/in_progress/done/cancelled；循环规范（新需求→backlog、拆任务→scheduled、任务完成→回写 done）写入 WORKFLOW.md 正式规则
- **内容边界判据正式规则**（WORKFLOW.md）：文件是否由 agate 编排流程生成/消费 → 归工作区；描述产品/项目本身 → 留项目 docs/。二值判定、对偶自洽（验收记录→工作区 / 项目 README→项目 docs/）
- **`agate/UPGRADING.md`**：存量项目迁移指引（迁移工具步骤 + 旧布局说明 + 外部工作区限制）

### 变更（TAG0003 工作区架构）
- **orchestrator-template.md**：project.md 路径 `{project_root}/docs/agents/project.md` → `{AGATE_WORKSPACE}/agents/project.md`；active-tasks 路径 → `{AGATE_WORKSPACE}/tasks/active-tasks.md`；接入 mkdir 建 8 子目录（roadmap/tasks/agents/archived/reviews/decisions/plans/logs）；启动时旧布局检测 + 迁移指引
- **6 个既有脚本路径换血 + 2 处隐藏硬编码去硬编码**：
  - `pre-commit-gate.sh`：tasks_base 改调工作区解析器（AGATE_TASKS_DIR 默认值 + 根级 .state.yaml 的 TASK_DIR 推导跟随解析结果）
  - `ci-gate-backstop.py`：tasks_base 改调解析器，本地 hook 与 CI 同路径
  - `check-state-transition.sh`：任务级 .state.yaml 检测从 `grep 'docs/tasks/[^/]+/'` 改为 `dirname != REPO_ROOT` 语义（隐藏硬编码，改法已验证）
  - `check-pruning.sh`：P7 源码文件数过滤排除模式跟随工作区路径（隐藏硬编码）
  - `check-protocol-consistency.py`：`PATH_IGNORE_SUBSTRINGS` 白名单 `docs/tasks/` → 工作区运行时目录
  - `install-hook.sh`：gitignore 提示文字路径跟随工作区
  - 另 `agate-render-dispatch-prompt.sh` 路径同步
- **16 文档 + 8 测试文件全量路径换血**：dispatch-protocol.md（28 处）/ state-machine.md / git-integration.md / role-system.md / WORKFLOW.md / SETUP.md / phase-cards / assets/templates / assets/execution-roles / loop-orchestration.md / rules/state-transitions.md 等；测试 fixture 中 `docs/tasks` 硬编码路径改为工作区路径（既有用例 603 条换血不改数）
- **新增测试**：`unit/agate-workspace-resolve.bats`（解析优先级/空格/外部路径）+ `unit/agate-migrate-workspace.bats`（迁移/幂等/空源/归档）；用例基线 625

### 修复（本版本范围 [v0.40.2..HEAD] 内既有修复，随本版本一并发布）
- **check-p6-format.sh --fix POSIX locale 下全角冒号总结行静默失效**（8cc7cd3）
- **orchestrator permission 全 allow + consistency 排除平台目录**（40c5713）
- **.gitignore 移除 .state.yaml 忽略规则**（f773e30/8aa94fb）——迁移工具目录级 git mv 依赖文件物理移动而非跟踪状态
- **README 升级段链 UPGRADING.md + 新增 UPGRADING.md 升级指引**（892f266/cf2ddce）

### 文档（非协议变更，随版本发布）
- 项目侧：知识索引试点 / 主动架构演进机制设计 / 生命周期演进框架讨论稿 / agate 商业分析 / 质量评估 / roadmap P2.67-P2.71 讨论记录 / 独立评审（本项目开发资料，与协议本体变更分离）

---

## [0.40.2] - 2026-08-11

### 修复
- **P4 gate 补 P4-review 门禁**：与 P2 gate 对称——`P4-review.md` 必须存在 + `status: approved` + `agent≠main`。此前 P4 gate 只查暂存区代码文件，未强制 P4-review（P4-implementation.md 声称"agent 必须非 main 与 P2 同规则"但脚本未实现）。堵住"主 Agent 跳过 P4 独立评审或自批实现"漏洞
- **修 C8 表 risk=high 逃生口**：C8 映射表（review-mapping.md + P4 card 内联表 + 推进条件）原将 risk=high 的 P4 实现评审省略（"plan-eng-review 在 P2 已派"）——但 P2 plan-eng-review 审方案设计，P4 review 审实现代码（SQL 注入/竞态/TOCTOU），高风险实现恰恰最需要 P4 评审。三处同步修正，P4 对所有任务要求实现评审

---

## [0.40.1] - 2026-08-11

### 修复（T091 复盘）
- **phase 字段语义澄清**：`git-integration.md` 规则 2 明确 `.state.yaml` 的 `phase` = 本 commit 提交的产出阶段，不得提前写下一阶段；P5 phase card 修正推进指令（phase=P5 提交产出，P6 推进随 P6 产出同 commit）。消除 P5 合法产出（fail-list.txt）在 P5→P6 硬拦边界被误伤的问题
- **subagent 外部中断恢复清单**：`dispatch-protocol.md` 补"外部中断（额度/超时/崩溃）恢复"——先查已落盘完整度（≥80% 补充复用 / <80% 重派），复用仍须亲自跑 gate。明确优先于返回校验 step 4
- **roadmap 记入并行环境隔离规范**（P2.66，P4 设计讨论项）

---

## [0.40.0] - 2026-08-10

### 变更（orchestrator 接入方式，破坏性）
- **`orchestrator-template.md` 改为对所有项目内容完全一致**：不再要求逐项目拷贝后手改 `agate_root`/`project_root`/项目特定约束——`agate_root`/`project_root` 改为会话开始时运行时解析（环境变量 `$AGATE_ROOT` 兜底默认 `~/.agate`；`project_root` 向上找最近 `.git` 目录），项目特定信息迁移到新的可选文件 `{project_root}/docs/agents/project.md`（模板见 `assets/templates/project.md`）。frontmatter 补充 Claude Code 必需的 `name: orchestrator` 字段（此前缺失会导致 Claude Code 静默跳过整个文件、agent 完全不可用）
- **标准接入方式改为符号链接**（不是拷贝）：`.claude/agents/orchestrator.md` / `.opencode/agents/orchestrator.md` 文件级链接直接指向 `orchestrator-template.md`，agate 升级模板后自动生效，不需要手动同步。完整步骤（含 Windows 无符号链接权限的复制模式退化、要不要设默认 agent）新增 `agate/SETUP.md`
- **⚠️ 迁移路径（已部署项目升级到本版本需要手动做）**：删除旧的拷贝文件 `docs/agents/orchestrator.md`（如果存在），按 `agate/SETUP.md` 重新建立符号链接；原来内联在 orchestrator.md 里的项目特定约束，迁移到新建的 `docs/agents/project.md`

### 新增（T001 v0.40.0 结构化数据改造）
- **`agate-frontmatter-check.py` + `check-frontmatter.sh`**：新增 frontmatter schema 校验器，覆盖 `P1-requirements.md`/`P2-design.md`/`P6-acceptance.md`/`P7-consistency.md` 四类产出文件——按文件名匹配 schema，做必填字段/枚举/类型/嵌套深度（>3 报错）校验；`yaml.safe_load` 解析异常（含 `YAMLError`/`RecursionError`/`UnicodeDecodeError`）统一捕获并 fail-closed（不再静默放行坏格式）；无 frontmatter 块视为旧格式豁免（向后兼容）。挂载到 `pre-commit-gate.sh`（新增步骤 "2g.2"），P1/P2/P6/P7 产出提交前强制过检
- **P6/P7 结果结构化**：P6-acceptance.md frontmatter 新增 `pass`/`fail`/`ui_affected` 汇总字段，P7-consistency.md frontmatter 新增 `blocker_count`/`deviation_count`/`deviation_critical_count`/`design_gap_count`/`design_gap_reviewed_count` 计数字段；`check-gate.sh` P6/P7 分支优先读取 frontmatter 汇总判定，两字段皆非空才走新格式（AND 语义），否则回退既有正文 grep（向后兼容）；新增 FIND-6 交叉校验 WARNING（frontmatter 汇总与正文逐条行数不一致时提示复核，不阻断）
- **`check-p6-format.sh` `--check`/`--fix` 双模式重写**：`--check` 独立实现严格行格式校验（`^\s*-\s+(PASS|FAIL)\s+BDD-[0-9]+`），不再依赖"和 --fix 输出 diff"判定
- **P1 标记状态结构化**：P1-requirements.md frontmatter 新增可选字段 `need_confirm_resolved`/`suggest_resolved`/`scope_resolved`（换行连接的列表），`check-gate.sh`/`check-scope-resolved.sh` 改为逐条精确匹配已解决/已采纳的 `[NEED_CONFIRM]`/`[SUGGEST:]`/`[SCOPE+]` 描述文本（而非数量相减，消除"N vs N 但内容对不上"的假一致歧义）
- **角色卡/模板可复制 frontmatter 样例**：`task-files.md`（P1/P2/P6/P7 四节）、`analyst.md`、`architect.md`、`verifier.md`、4 个 `phase-cards/{P1,P2,P6,P7}-*.md` 补充可直接复制的完整 frontmatter YAML 代码块，替换原先"正文写字段"的过时示例
- **ADR-007**：`agate/adr.md` 新增"机器字段并入 frontmatter——单工具双读，不拆分独立事实文件"决策记录

### 变更（T001 v0.40.0 结构化数据改造）
- **机器字段迁移：正文内嵌 YAML/正则提取 → frontmatter + pyyaml + schema 校验**：`agate-md-field-get.py` 双读改造——`_read_frontmatter`/`_get` 实现"frontmatter 优先，字段不存在时正则回退"的判别契约；`_format_value` 统一 bool 字段输出 `true`/`false`、list 字段空格或换行连接（视字段语义）；新增 17 个 op（`candidate_count`/`packages`/`domains`/`coupling_checklist`/`follows_existing_pattern`/`override`/`internal_only_reason`/`internal_only`/`design_trivial`/`pass`/`fail`/`blocker_count`/`deviation_count`/`deviation_critical_count`/`design_gap_count`/`design_gap_reviewed_count`/`need_confirm_resolved`/`suggest_resolved`/`scope_resolved`），既有 3 个 op（`risk_level`/`ui_affected`/`phases`）正文回退逻辑字节级不变
- **任务编号规则硬切为 `T[A-Z]{2}\d+`**：`agate-state-yaml-check.py` 的 `task_id` 正则从 `^T\d+$` 硬切为 `^T[A-Z]{2}\d+$`（如 `TAG0001`），不兼容旧格式 `T001`；`check-changelog.sh` 去短前缀提取逻辑，直接用完整 `task_id` 做带单词边界的匹配（同时移除无边界保护的固定字符串 fallback，避免 `TAG0001` 被 `TAG00012` 误匹配）；`active-tasks-template.md`/`state-machine.md`/`dispatch-protocol.md`/`role-system.md` 示例同步为新格式
- **`check-protocol-consistency.py` CHECK 9 锚点表**：`SCRIPT_ALIGNMENT_ANCHORS` 新增 `check-frontmatter.sh` 条目，锚点总数 37→38

### 修复（T001 v0.40.0 结构化数据改造）
- **`check-p6-format.sh` `--fix` 分支破坏 frontmatter**：`--fix` 归一化 sed 此前作用于整个文件，会把 P6-acceptance.md frontmatter 中合法的 `pass:`/`fail:` 字段误改写为 `**Summary**: PASS: ...`，导致 frontmatter 变成非法 YAML。修复为先切分 frontmatter/正文，sed 只作用于正文部分，frontmatter 原样保留
- **`agate-frontmatter-check.py` 异常处理不完整**：深嵌套字段（如 2000 层嵌套 `risk_level`）触发 `RecursionError` 未被原有 `except yaml.YAMLError` 捕获，进程崩溃导致 `check-frontmatter.sh` 误判"无错误"放行坏格式；补齐 `Exception` 兜底 + `check-frontmatter.sh` 侧改为 fail-closed（脚本非零退出时不再静默放行）

### 已知偏离（T001，均经 P7 独立核实，7/7 REVIEWED-ACCEPTED，非 BLOCKER）
- `check-gate.sh`/`check-pruning.sh` 部分字段读取点未迁移到双读工具（现有 grep 对顶格 frontmatter 天然兼容，schema 校验器已承担格式拦截责任，无实际解析可靠性缺口）
- `check-gate.sh` P6 分支旧格式回退正则较 P2 设计文字表述更宽松（为兼容既有历史正文写法）
- `check-scope-resolved.sh` 对 `scope_resolved` 字段"存在但空列表"与"字段不存在"两种情况未做区分（概率低的边界场景，功能后果等价）

---

## [0.35.0] - 2026-08-09

### 修复（T090 复盘）
- **PROD_TOUCHED 标记检测收紧**：pre-commit-gate.sh 宽松分支从 `grep -q` 改为行尾锚定，正文"句中提及"标记词不再误报为不合规声明；行首独立声明仍拦截。IT_PT_BINARY.4/.5 预期反转，新增 IT_PT_MENTION.1
- **P6 证据白名单补 `evidences/`**：与 verifier.md 对齐，消除协议内文档与脚本对"合法输出路径"定义的分叉
- **gate_commands 补 `P3_e2e`**：UI 任务新增测试在 E2E 层时 TDD 红灯确认不再假绿（P5 有 P5_e2e，P3 缺对应字段）
- **DESIGN_GAP 格式强制**：implementer 卡加产出后自检 `grep -c`；check-gate P7 加启发式 WARNING（有关键词但计数 0 时提醒人工确认），防"0 vs 0 假一致"
- **agate-summary 检测本地脚本副本漂移**：对比 scripts/ 同名副本与权威版本 checksum，不一致 WARNING
- **check-changelog post-bump 模式**：`CHECK_CHANGELOG_MODE=post-bump` 时检查新版本段落非空而非 [Unreleased]，消除 bump-version 结构误报

---

## [0.34.0] - 2026-08-07

### 内部重构
- **内联 python 抽离为独立 `.py` 工具**：把 14 个 `.sh` 脚本里 46 处 `python3 -c '...'` 内联段（含 `chr()` 引号规避病征、重复的单行 JSON 提取）抽离为 14 个独立可测试的 `agate/scripts/agate-*.py` 工具，行为完全等价。消除 bash+python 混合架构债，检查逻辑可独立测试复用。非 BREAKING
  - **注意（一次性）**：`P5_DATA` 中间格式由裸数组改为 `{"commands":[...]}`（内部表示），导致既有 env-baseline 缓存键（`agate-capture-env-baseline.sh` 的 `CACHE_KEY`）失效一次——每个任务会重跑一次 P5 测试命令并写新 baseline，之后正常。行为等价，仅首次缓存重建。

### 改进
- **Windows 原生支持（Git for Windows bash，不用 WSL）**：新增 `.gitattributes` 强制 LF（防 `core.autocrlf` CRLF 污染 .sh/.py）；`install-hook.sh` 在 `ln -sf` 无符号链接权限退化为复制时打印升级提醒；`platform-notes.md` 新增「Windows 原生」章节（前置条件 + 安装步骤 + 已知限制）。对 Linux/macOS 零行为变化。非 BREAKING

---

## [0.33.0] - 2026-08-07

### 改进
- **pre-commit-gate.sh AGATE_ROOT 自定位**：从硬编码 `$HOME/.agate` 改为 `readlink -f` 自定位（与其他脚本一致），支持 git worktree 隔离--hook 软链到 worktree 时自动指向 worktree 本体，不再误指主 checkout。`install-hook.sh` 不变（安装脚本应默认全局）。非 BREAKING
- **一致性检查跳过 `.worktrees/`**：worktree 隔离工作区不应被协议一致性扫描（含隔离实验内容，会污染主仓一致性报告）
- **测试卫生**：pre-commit-hook.bats / dispatch-context-card.bats 的 hook 安装从 `cp` 改 `ln -sf`，与真实 install-hook.sh（软链）一致

> **worktree 手动装 hook 说明**：git linked worktree 共享主仓库的 `.git/hooks/`（`git rev-parse --git-path hooks` 指向主仓），`install-hook.sh` 在 worktree 内运行会把 hook 装到主仓库 hooks。worktree 场景请手动把 hook 软链到主仓库 hooks：`ln -sf <worktree>/agate/scripts/pre-commit-gate.sh <mainrepo>/.git/hooks/pre-commit`。

---

## [0.32.0] - 2026-08-07

### 内部重构
- **pre-push hook 从写死复制改为软链统一**：新建 `pre-push-gate.sh` 独立脚本，`install-hook.sh` 以 `ln -sf` 安装（与 pre-commit/commit-msg 一致）。bug 修复自动分发，消除写死复制导致的升级滞后（T086 grep -c bug 教训）。补 pre-push 备份 guard + 源文件存在性检查。一致性锚点 `AGATE_ALIGNMENT_REVIEW_THRESHOLD` 同步指向新脚本。非 BREAKING

---

## [0.31.0] - 2026-08-07

### BREAKING
- **P2-design.md 必填 `candidate_count:` 字段**：check-gate.sh P2 候选方案判定从"正则数标题"改为强制显式 `candidate_count:` 字段（替代 `^#{2,4}\s*(候选方案|方案\s*[A-Za-z0-9一二三四五]|Alternative|Option)` 脆弱匹配，`### 方案：` 全角冒号不再被误拦）。gate 只检查字段存在性（自声明 nudge），不做语义真实性校验。design_trivial/follows_existing_pattern 时 MIN=1 保留。architect.md 输出规格 + task-files.md P2-design 模板同步补该字段。G2.26/G2.27 测试验证

### 改进
- **A1 角色卡补 gate 解析字段 YAML 模板**：analyst.md 补 `risk_level`/`phases`/`跳过风险` + 可选字段（`design_trivial`/`follows_existing_pattern`/`implicit_coupling`/`coupling_checklist`/`internal_only`/`internal_only_reason`/`override`）的机器可解析模板，消除"语义对但格式错"返工（T086 复盘 A1）
- **B1 architect.md minimal_validation 补删除/移动验证**：涉及删除/移动路由、接口、注册表项时，即使判定"纯代码逻辑"也必须验证"删除后请求流向哪个兜底分支"，不因标签豁免（T086 复盘 B1，唯一造成生产代码 bug 的根因）
- **C1 verifier.md 截图补 settle-wait**：`waitForSelector(visible)` 不保证 `opacity===1`，截图前用 `getComputedStyle().opacity === '1'` 或 `waitForTimeout(200)` 确认 CSS 过渡完成（T086 复盘 C1）

---

## [0.30.3] - 2026-08-06

### BREAKING
- **P6 删除 NEED_CONFIRM 检测**：P6 是客观验收（PASS/FAIL 二值），"无法验证"标 FAIL 回 P4，不标 NEED_CONFIRM 等人确认。check-gate.sh P6 删除 NC 检测。verifier.md "无法验证标 FAIL"。state-machine.md/loop-orchestration.md 同步删除 P6 NEED_CONFIRM 引用。G6.10/G6.11 测试验证新行为
- **P2 architect NEED_CONFIRM → SUGGEST**：architect.md "DEVIATION + NEED_CONFIRM（不硬阻塞）"改为"DEVIATION + SUGGEST"。语义一致：不阻塞的倾向项用 SUGGEST
- **P4 review 不用 BLOCKER**：architect.md P4 review 的 BLOCKER 改为 DEVIATION（与同文件 DEVIATION 体系一致）。BLOCKER 专属于 P7
- **标记声明规范表加适用范围列**：dispatch-protocol.md 标记表增加"适用环节"列，明确每个标记在哪些环节使用

---

## [0.30.2] - 2026-08-06

### BREAKING
- **[NEED_CONFIRM倾向:] 重命名为 [SUGGEST:]**：v0.30.1 引入的 `[NEED_CONFIRM倾向:]` 与 `[NEED_CONFIRM]` 共享前缀导致视觉混淆和 typo 风险。v0.30.2 起重命名为 `[SUGGEST: 推荐 X，理由 Y]`——完全不共享前缀，视觉/grep/正则完全可区分。旧标记 `[NEED_CONFIRM倾向:]` 报格式不符并提示重命名。check-gate.sh 加 typo 兜底检测（旧标记残留 + `[SUGGEST` 漏冒号）。G_SUGGEST.1-4 测试

---

## [0.30.1] - 2026-08-06

### 变更
- **NEED_CONFIRM 三值分级（T080 retro）**：P1 NEED_CONFIRM 从二值升级到三值。`[NEED_CONFIRM倾向: 推荐 X，理由 Y]`（有倾向，WARNING 不阻塞，主 Agent 自行采纳）vs `[NEED_CONFIRM]`（真无方向，阻塞）。check-gate.sh P1 检测逻辑区分两者。analyst 角色说明何时用倾向项。G_NC_TENDENCY.1/.2 测试
- **gate 格式契约透明化（T080 retro）**：verifier 角色文件追加精确正则模板（PASS/FAIL 行、vision YAML 结构、引用括号）。consistency-reviewer 角色追加 P7 DESIGN_GAP 行首格式。dispatch-context 模板追加约束节避免行首 PASS/FAIL 提示
- **P1 基线保护（T080 retro）**：P1-requirements.md 加基线保护说明（`[BASELINE_CHANGE: 理由]` + 主 Agent 显式批准）。P4-implementation.md 常见错误节提醒不直接改 P1
- **P8 bump + CHANGELOG 同一 commit（T080 retro）**：P8-release.md L12 明确 bump-version + CHANGELOG 更新 → 同一 commit + tag
- **P2 选择器契约提示（T080 retro）**：P2-design.md 加 UI 测试选择器契约提示（稳定测试标识清单，如 data-testid）
- **P1 review 跨条 BDD 一致性维度（T080 retro）**：requirements-review 角色加"BDD 跨条一致性"维度（Then 矛盾 + 保护优先级 + 环境约束）
- **P2 review UI 组件完整性维度（T080 retro）**：plan-design-review 角色加"组件完整性"评分维度（每个 UI 组件有完整 input/output）
- **known-failures.md 语义边界（T080 retro）**：known-failures 模板 + P5-verification.md 明确"只登预存失败，不登当前任务失败"
- **反向传播同步**：dispatch-protocol.md / state-machine.md / state-transitions.md / WORKFLOW.md / analyst.md / CONTEXT.md / task-files.md 同步 NEED_CONFIRM 三值语义。CHECK 9 锚点 desc/keywords 更新

---

## [0.30.0] - 2026-08-04

### 变更
- **evidence 类型检查**：check-p6-evidence.sh 在 `ui_affected: true` 时检查 evidence 目录不能全是 .md/.txt（防源码分析充数）。不绑定特定工具（vision-engine/playwright-cdc 等），只验证"有没有运行时数据文件"。E.15/E.16/E.17 测试
- **office-hours 角色清理 + 六问内化**：删除从未触发的 office-hours 角色文件 + 清理 9 处引用。Startup Mode 六问内化到 P0 卡片作为 P0-brief 质量自检清单（非门槛，零派发开销）
- **P6 总结行格式显式化**：check-p6-format.sh check+fix 模式都检测总结行（`- PASS：34` / `- FAIL：0`）并自动修正为 `**Summary**` 格式。防止 gate 误判总结行为 BDD 条目。F11/F12 测试
- **check-tdd-red.sh 内部 timeout**：gate-result.sh run_test_with_formatter 加 120s timeout（AGATE_TDD_TIMEOUT 可覆盖）。exit 124 → judge_result 视为红灯可推进（return 0）。macOS 兼容（command -v timeout 检测）。TDD.TIMEOUT 测试
- **P0 卡片 hardening 审计提示**：P0-orchestrator.md 加"hardening/refactor 类任务建议含代码审计"提示（非门槛）

---

## [0.29.0] - 2026-08-03

### 变更
- **审计 6 短路修复**：check-p6-provenance.sh agent 字段检查的 `exit 2` 会终止整个脚本，导致审计 6（evidence JSON 一致性，P2.57）被静默跳过。改为 `WARNING_FOUND` 变量记 WARNING 后继续执行审计 6，末尾统一判断 exit code。新增 PV.28 测试（agent 缺失 + evidence 矛盾 → exit 1）。删除伪"v2 向后兼容"注释
- **phase 更新时机统一（P2.64）**：7 个阶段卡片统一为"先更新 .state.yaml → git add（含 state + 产出）→ git commit"（模式 B）。删除 check-state-transition.sh 检查 3（pre-phase-change commit gate，强制模式 A 两步 commit）——与模式 B 冲突，产出存在性由 check-gate.sh 检查。更新 ST.17/ST.18 测试语义反转
- **P3 gate 分离（P2.64）**：check-gate.sh P3 从 `exec check-tdd-red.sh` 改为文件存在性检查（秒级），解决 hook 超时导致 --no-verify 绕过（T085 复盘 8/10 次 --no-verify）。ci-gate-backstop.py P3 时额外跑 check-tdd-red.sh 兜底，插入在 .gate-result.json 存在性判断之前（--no-verify 场景仍执行）。AGATE_TDD_RED_SCRIPT 环境变量支持 mock 测试。5 个新测试覆盖真红灯/绿灯/假红灯/无运行器/--no-verify 场景
- **install-hook.sh .gitignore 检测（P2.64）**：安装时检测 .gitignore 中 .state.yaml 忽略并提醒用 git add -f
- **P2 候选方案正则放宽（P2.64）**：`^###?` → `^#{2,4}` 支持 ####（h4）标题。G2.4 测试改用 #####（h5 边界），新增 G2.25 测试验证 h4 识别
- **gate_commands 命令可执行性检查（P2.61）**：check-gate.sh P2 分支解析 gate_commands 每个命令的第一个 token，用 `command -v` 验证存在性，WARNING 不阻断。消除 T075 中 `python` 不存在导致 P3 gate exit 127 的损耗
- **P3 自检注入 + 经典红灯提示（P2.62）**：dispatch-prompt.md 新增 P3 派发追加块（强制自检步骤，机械注入每次 P3 派发）+ agate-render-dispatch-prompt.sh 新增 P3 case 分支 + check-tdd-red.sh 经典红灯分支输出断言矛盾提示（WARNING）。帮助 P3 阶段发现"断言与测试数据矛盾"而非到 P5 才暴露
- **修复轮 dispatch-context 增量模式（P2.63）**：dispatch-prompt.md 新增修复轮派发追加块（主 Agent 模板：引用上轮文件 + 只写增量），减少多轮修复的 dispatch-context 维护负担
- **check-pruning YAML 列表格式支持（P2.52）**：check-pruning.sh 的 phases 解析从只认内联格式 `phases: [P1,P2]` 扩展为同时支持 YAML 列表格式（每阶段一行）。消除 T084 中 3 次 gate 拦截
- **SCOPE+ 排除 progress 文件（P2.53）**：check-scope-resolved.sh 和 check-retrospective.sh 的 [SCOPE+] 检测排除 progress 文件，防止 `[SCOPE+] 检查: 无` 等文本被误匹配
- **CHANGELOG 检查限制到 P8（P2.54）**：pre-commit-gate.sh 的 CHANGELOG 检查从每次 commit 触发改为仅 P8 phase 触发。消除 P1-P7 阶段 4 次无意义 WARNING
- **并行派发操作级指导（P2.55）**：P2/P4 卡片追加操作级指令——"在一个消息中连续发起多个 task 工具调用，不要等前一个返回再发下一个"
- **review status 字段指导（P2.56）**：dispatch-prompt 模板追加明确指令——评审完成后必须将 Header status 从 draft 改为 approved/rejected/needs-revision
- **P6 evidence-consistency 检查（P2.57）**：check-p6-provenance.sh 新增审计 6——检查 evidence JSON 中的 bdd_results 与 P6-acceptance.md 的 PASS/FAIL 声明一致性。防止 P6 commit 声称全 PASS 但 evidence 实际有 FAIL 的时序倒置
- **测试输出标准化（P2.51）**：check-tdd-red.sh 和 agate-capture-env-baseline.sh 重写为 formatter + 标准 JSON 格式，不再硬编码 pytest 输出解析。新增 6 个内置 formatter 模板（pytest/vitest/go-test/generic-tap/generic-junit-xml/generic-exit-only）。gate_commands 扩展 P3_formatter/P5_formatter/project_module 可选键。支持多技术栈声明（P3 + P3_js）。不提供 formatter 时退化为 exit-code-only。TEST_RUNNER 环境变量保留但退化为 exit-code-only（不再有 A/B 类检测）。废弃 TEST_RUNNER_FLAGS/TEST_FAIL_PATTERN/TEST_ERROR_PATTERN/TEST_IMPORT_PATTERN 环境变量
- **P6 截图格式放宽**：check-p6-evidence.sh 从 PNG-only 改为接受任意图片格式（file 命令 + magic bytes fallback）
- **P7 DESIGN_GAP 正则修复（T083）**：check-gate.sh 正则加 `>?` 匹配 markdown blockquote 格式
- **P0-brief 四字段**：移除 `pruning_tendency` 字段（五字段→四字段：task/known_risks/executor_env/env_constraints）。理由：P0 阶段无足够信息判断裁剪倾向，与 P1 risk_level 重复，给 P1 analyst 施压。office-hours 触发条件简化为"大任务"（去掉 pruning_tendency 条件）
- **阶段卡片措辞加固（P2.50）**：所有阶段卡片"推进条件"改为显式 AND checklist。消灭"可选"/"若有触发"/"若方案依赖"/"nudge"等模糊措辞。check-gate.sh P2 review 文件不存在时 exit 1（bug fix：原来文件不存在时跳过检查）。design_trivial/follows_existing_pattern 须附理由。minimal_validation 强制声明。P4"P5 由主 Agent 亲自执行"→"派发 verifier subagent 执行"。P5 签名校验"轻量验证"→"必须"。P8"手动确认"→"必须亲自执行"
- **gate_commands.P3（P2.49）**：gate_commands 新增可选 P3 键（architect 在 P2 声明测试运行器命令）。check-tdd-red.sh 回退链扩展：`$TEST_RUNNER → gate_commands.P3 → which pytest → exit 3`。P3 键用 verbose 输出（区分 A/B 类错误），P5 键用紧凑输出，两者分离。非 pytest 项目不再需要每次手动设 TEST_RUNNER 环境变量

---

## [0.20.0] - 2026-07-24

### 破坏性变更
- **BDD 格式标准化，不做过渡期兼容**：P1-requirements.md 的 BDD 验收条件从"格式不固定"变为标准
  `#### BDD-NN: {描述}` 标题 + 一条 Given/When/Then。`### {功能分组名}` 必选，保证 heading 层级
  `##` → `###` → `####` 不跳级。相关检查（provenance 审计 3、P1-review.md BDD 锚点）均直接
  `exit 1` 硬阻，不设 legacy 格式的 WARNING 退化路径（当前无在途任务使用旧格式，已完成任务不需要
  追溯符合新标准）

### 修复
- `check-p6-provenance.sh` BDD 总数对照改为按 `#### BDD-NN` 标题精确计数（原按 Given 行数启发式
  计数，一条 BDD 挂多个 Given 时虚增，导致挑验误判）
- `pre-commit-gate.sh` PROD_TOUCHED 步骤2 扫描前剥离 AGATE_CARD 注入块，不再误拦卡片说明文本中的
  `[PROD_TOUCHED]` 字面量（复用 `check-p6-provenance.sh` 已验证的剥离模式）
- `check-gate.sh` P5 gate_commands 计数改为解析 `gate_commands:` YAML 块内的 P5 相关键，不再统计
  P2-design.md 全文所有缩进 bullet 行（原会把候选方案、权衡列表等无关 bullet 一并计入，"27 个命令"
  的误报即由此产生）
- `check-gate.sh` P1-review.md BDD 编号锚点正则从 `BDD-|B[0-9]` 收紧为 `BDD-[0-9]`（原正则会误匹配
  "B2B"/"B2C" 这类词）

### 变更
- 17 处协议文档（模板、角色定义、phase-cards、state-machine.md、dispatch-protocol.md、
  WORKFLOW.md、LIMITATIONS.md、CONTEXT.md、rules/state-transitions.md 等）BDD 编号示例统一为
  `BDD-NN` 格式
- `check-protocol-consistency.py` CHECK 9 锚点表追加 BDD 编号格式检查
- 测试 fixture（5 个 P1 + 5 个 P6）与 8 个测试文件中约 112 处 `AC\d+`/`B0\d` 编号批量替换为
  `BDD-\d` 格式；`tests/helpers/fixtures.bash` 新增 `add_p1_bdd` helper，`add_given_line`/
  `add_p1_given` 标记废弃（无调用者，保留代码避免破坏下游 fork）

## [0.19.0] - 2026-07-23

### 新增
- `agate-archive-stale-outputs.sh`：回退时归档被跨过阶段的 self-authored 产出（P1/P2/P6/P7），
  归档到 `docs/tasks/Txxx/.archived/{时间戳}-{阶段}/`（留痕，非删除），并在
  `docs/tasks/Txxx/.retreat-history.md`（不被归档）追加摘要，P6 时摘录具体 FAIL 详情，
  防止重新派发时忘记当初失败原因
- `agate-retreat-to.sh`：自动化多步单向回退，主 Agent 只需调用一次即可完成多步
  "归档 + phase 更新 + commit"序列，每一步仍是独立、真实、受 `pre-commit-gate.sh`/
  `check-state-transition.sh` 完整校验的 commit，不改变 diff≥2 强制 PAUSED 的安全网

### 修复
- **`check-gate.sh` 新增回退抵达检测**（实施过程中发现的架构性问题，超出原 plan 范围）：
  原本每个阶段分支检查的是"这个阶段是否已完成"（文件存在/approved/FAIL=0 等），这个假设
  只对"正常推进抵达"成立——对"回退抵达"（如从 P6 退到 P4，归档后刚落地）不成立，因为退回
  来的那一刻工作本来就还没重做。此前这会导致 `agate-retreat-to.sh` 的退回序列中途被硬拦截
  （P1/P2/P4/P6/P7 等有完成度硬校验的阶段皆受影响，不止 P4）。现支持可选第 3 个参数
  `OLD_PHASE`，`pre-commit-gate.sh` 会自动计算并传入；省略时行为与之前完全一致（向后兼容，
  不影响任何现有调用方）。检测到回退抵达时跳过完成度校验、返回 exit 2（视为"待重做"，不是
  "已通过"），重新推进离开该阶段时会再次正常校验
- `check-state-transition.sh` 新增检查：单步回退时若被跨过阶段（P1/P2/P6/P7）的自撰产出
  仍在原位（未归档），拦截 commit 并提示先跑归档脚本——此前回退没有任何机制防止旧产出被
  静默复用，gate 可能基于修复前的验收结果误判通过
- `pre-commit-gate.sh` E3 检查区分证据文件与项目源码：P6 阶段暂存 `P6-evidence/` 之外的
  文件（即项目源码）现在会被硬拦截（此前 P6 与 P4/P5 一样被无脑放行）——P6 是
  self-authored gate 的验收阶段，验收失败应退回重新派发实现，而非在 P6 原地改代码

### 变更
- `phase-cards/P6-acceptance.md` 补充"验收失败不能直接改代码"的显式指引
- `phase-cards/P4-implementation.md` 补充"重新派发时须引用 `.retreat-history.md`"的要求
- `dispatch-protocol.md` 红灯处理优先级补充归档前置要求 + `agate-retreat-to.sh` 用法
- `agate/rules/state-transitions.md` 回退规则补充自撰产出归档要求

### 修复
- check-p6-provenance.sh 支持逗号分隔的多文件证据引用（原会把逗号和空格当路径一部分导致误判缺失）
- check-p6-provenance.sh 审计 1c/5 用 grep -F 替代 grep -E（防止文件名含正则元字符时误判）
- agate-inject-card.sh 幂等注入误报修复：判定逻辑从"替换前后文本是否相同"改为"正则是否匹配"，
  消除同一 phase 卡片内容未变时重复注入被误判为"占位符缺失"的问题
- agate-inject-card.sh 替换逻辑改用 lambda（防止卡片内容含 `\1` 等 backreference 被误解析）
- pre-commit-gate.sh phase 跨度 WARNING 误报修复：阶段号低于当前 phase 的新增文件（历史产出晚提交）
  不再被误判为"过期跨阶段产出"；阶段号高于当前 phase 的新增文件（提前产出）仍正确报 WARNING，
  修复带方向判断以避免破坏既有测试 IT.7
- check-p6-evidence.sh 证据引用检测从扩展名白名单改为结构判定（含路径分隔符或"文件名.扩展名"结构即视为
  有效引用，不再枚举扩展名；不锚定行末，与 check-p6-provenance.sh 的逗号多文件解析兼容；边界误判交给
  provenance 的文件存在性硬验证兜底）
- check-p6-evidence.sh 内联 Python 改用 os.environ 传递路径（防止文件名含单引号时的命令注入风险）

### 变更
- phase-cards/P6-acceptance.md 更正 md5 完全重复截图的处理指引，与 verifier.md 及脚本实际行为
  （hook 硬阻断，无例外）保持一致

### 新增
- phase-cards/P3-tdd.md、P5-verification.md、verifier.md 补充 TEST_RUNNER 环境变量的可发现性提示
  （能力已存在，仅补充文档醒目度）

---

## [0.17.0] - 2026-07-23

### 新增
- 标记二值声明：PROD_TOUCHED / NEED_CONFIRM 采用正向/负向二选一格式
- `[PROD_NOT_TOUCHED]` / `[NO_NEED_CONFIRM]` 负向声明格式
- 缺失声明 WARNING（NEED_CONFIRM 两个都没写时提醒；PROD_TOUCHED 缺失静默通过）
- 标记声明规范节（dispatch-protocol.md）

### 变更
- **BREAKING**：`[PROD_TOUCHED]` / `[NEED_CONFIRM]` 标记必须行首声明，句中引用会被 gate 拦截
- **BREAKING**：`无 [PROD_TOUCHED]` 等否定语境写法不再被接受，须用 `[PROD_NOT_TOUCHED]`
- pre-commit-gate.sh PROD_TOUCHED 检测只扫 git diff 新增行（`^+`），不再匹配删除行/上下文行
- SCOPE+ / DESIGN_GAP / SCOPE_RESOLVED grep 加行首锚点
- NEED_CONFIRM grep 加行首锚点

### 修复
- pre-commit-gate.sh 扫描 git diff 删除行/上下文行导致 PROD_TOUCHED 误判

---

## [0.16.0] - 2026-07-22

### 修复
- T060 复盘 bugfix：`agate-inject-card.sh` 找不到占位符时 exit 1（非静默成功）
- T060 复盘 bugfix：`check-scope-resolved.sh` 跳过 dispatch-context 文件（约束指令中的 `[SCOPE+]` 字面引用不再误报）
- T060 复盘 bugfix：`check-changelog.sh` 从完整 task_id 目录名提取 `T\d+` 短前缀搜索 CHANGELOG

### 新增
- **M3.1 像素方差检测**：`check-p6-evidence.sh` 检测低方差/疑似占位图（WARNING 不阻断，需 Pillow）
- **M3.2 average hash 相似度检测**：`check-p6-evidence.sh` 检测视觉高度相似截图（WARNING 不阻断，纯 Pillow 实现）
- **M4.1 多平台 CI 支持**：`ci-gate-backstop.py` 自动检测 Gitea Actions / GitLab CI / GitHub Actions（Gitea 未实测）
- **M4.2 provenance 审计 CI 兜底**：`ci-gate-backstop.py` 重跑 `check-p6-provenance.sh`
- **M5.1 pre-push hook**：`install-hook.sh` 安装 pre-push hook，`agate/*.md` 大改动自动提示 alignment-review
- **M1.3a 日志格式约定**：`dispatch-prompt.md` 定义 `EXIT_CODE: <n>` 标准日志尾行
- **M1.3b 日志一致性检测**：`check-p6-provenance.sh` 审计 5——`EXIT_CODE` 与 PASS/FAIL 声明一致性检测
- **P5 全量测试 WARNING**：`check-gate.sh` P5 多命令时提醒主 Agent 确认是否全量执行
- `AGATE_SKIP_IMAGE_CHECKS=1` 主动跳过图像检测开关

### 变更
- **BREAKING**：`check-p6-evidence.sh` md5 完全重复截图从 exit 2 (WARNING) 升级为 exit 1（阻断）
- `commit-msg-self-gate.sh` 触发正则通配 `*.py`（原仅匹配 `check-protocol-consistency.py`）
- `check-protocol-consistency.py` CHECK 9 扫描范围追加 `ci-gate-backstop.py`
- `check-changelog.sh` 搜索方式从全路径精确匹配改为 `T\d+` 短前缀 + 全路径 fallback

### 已评估
- **M1.1 时间戳弱信号**：已评估，判定不值得实现（CI 场景 mtime 被 checkout 重置 + 威胁模型对伪造行为无区分力）。完全依赖独立 git author 根治方向

---

## [0.15.0] - 2026-07-21

### 重大变更
- **dispatch-context 单一信息源重构**：文件名 `P{N}-dispatch-context.md` → `P{N}-dispatch-context-{role}.md`（每个 subagent 一个），格式改为 Markdown+XML（`<dispatch_guide>` + `<objective_info>`），新增 4 子节（目标/约束/上游关联/输入文件），所有 P1-P8 统一强制，hook/provenance 校验改为 glob 匹配
- **dispatch-prompt 精简**：移除任务特定内容（目标/关注点/约束/输入文件），保留执行框架 + 执行顺序 + 权威性声明

### 新增
- **`agate-inject-card.sh`**：自动注入 AGATE_CARD 到 dispatch-context 文件（替代手写），支持 glob 匹配多文件
- **`known-failures-template.md`**：已知债务登记模板（预存失败可见、可追踪）
- **BDD 反模式自检清单**：analyst.md 新增 5 项 BDD 质量自检

### 变更
- **G1 (provenance)**：PASS 行截图路径改用精确正则提取（兼容嵌套括号描述）
- **G2 (evidence ≤1KB)**：PNG header 校验（非 PNG 仍拦截，合法小 PNG WARNING）
- **G3 (evidence md5)**：md5 去重降级为 WARNING（行为差异类 BDD 截图可视觉相同）
- **G5 (P8 gate)**：version/CHANGELOG 双路径检查（暂存区 + 最近 5 commit），CHANGELOG 降级为 WARNING
- **G6 (SCOPE+)**：扫描排除 AGATE_CARD 嵌入块（防卡片模板文本误报）
- **G8 (P8 提交控制)**：releaser subagent 只产出不提交，bump-version + commit + tag 由主 Agent 统一执行
- **P5 全量测试 WARNING**：建议 P5 运行全量测试，预存失败登记到 known-failures.md
- **P6 PASS 行格式标准化**：`- PASS {BDD}: {描述} ({证据路径})`，描述文本不影响解析
- **verifier P6 gate 格式预检**：返回前预检格式/证据/provenance，最多 2 轮修复
- **orchestrator-log 强制写入点**：5 种事件必须追加（派发/gate 失败/诊断/subagent 失败/流程决策）

## [0.14.0] - 2026-07-20

### 新增
- **ADR 架构决策记录**：`adr.md` 含 6 条核心决策（隔离性/可判定性/最小约定/安全网分层/改动性质分类/双层角色），A7 审查锚点
- **术语表 + 上下文**：`CONTEXT.md` 含 20 个术语的 Ubiquitous Language，跨文件术语统一入口
- **A7 锚定到 ADR**：protocol-alignment-review.md A7 从"提炼设计原则"改为"引用 ADR"

### 变更
- **AGENTS.md 文件清单**：增加 adr.md 和 CONTEXT.md
- **WORKFLOW.md 改动性质判断**：引用 ADR-005
- **hardening-roadmap.md Phase 2C**：ADR + 术语表条目

---

## [0.13.1] - 2026-07-20

### 新增
- **改动性质分层判断**：WORKFLOW.md §适用边界从举例式定义改为分层判断（声明性/行为逻辑/机制交叉 × 单点/跨模块 + 高风险覆盖规则），替代旧"微任务"模糊定义
- **P8 gate tag WARNING**：check-gate.sh P8 检查 CHANGELOG diff 中版本号对应 tag 是否存在，不存在 → WARNING（exit 2，不阻断），`VERSION_TAG_PREFIX` 环境变量覆盖
- **P3 前置状态覆盖提示**：P3-tdd.md 常见错误第 5 条 + WORKFLOW.md §P3 测试设计指导（含 UI/后端/嵌入式跨领域举例）
- **orchestrator-log 最低纪律**：从"想写就写"改为"gate 失败/subagent 失败/流程决策/用户叫停应追加至少一行"
- **A7 设计原则一致性**：protocol-alignment-review.md + SELF-GATE.md 审查清单增加 A7

### 变更
- **风险矩阵前加入口判断**："先用上方改动性质判断确定流程类型，再用本矩阵确定裁剪程度"
- **P2.14 改动性质声明**："直接做"commit message 须声明改动性质（声明性/行为逻辑/机制交叉）+ 为什么安全
- **orchestrator-template.md 关键不变量**：增加"机制交叉改动必须走 agate"
- **PROD_TOUCHED 检测范围收窄**：pre-commit-gate.sh 只扫任务目录下的暂存 diff，不扫协议/模板/项目文档

---

## [0.13.0] - 2026-07-13

### 新增
- **P1 NEED_CONFIRM 检查**：check-gate.sh P1 分支加 NEED_CONFIRM 检查（与 P6 二行式对称），P1-requirements.md 含 `[NEED_CONFIRM]` 时 exit 1
- **P4/P5 不可裁剪检查**：check-pruning.sh 补检查 4/5（P4 实现底线 + P5 验证底线），与 P2/P6 不可裁检查对称
- **P3 裁剪条件收紧**：risk≠high可裁 → risk=low才可裁（medium/high 必须走 TDD 红灯），可裁比例从 ~80-90% 降到 ~33%
- **P4 gate 排除收窄**：从排除所有 .md/.yaml → 仅排除 agate 流程产物（`P[0-8]-*.md` + `.state.yaml`），配置类 .yaml 交付不再被误拦
- **P8 version 检测降级 WARNING**：不匹配时从 exit 1 降为 WARNING + `AGATE_VERSION_FILES` 环境变量覆盖
- **TEST_RUNNER_FLAGS + 可配汇总正则**：check-tdd-red.sh 支持 `TEST_RUNNER_FLAGS`（多 flag 展开）、`TEST_FAIL_PATTERN`/`TEST_ERROR_PATTERN`（适配 go test/cargo test/jest 等非 pytest 输出格式）
- **AGATE_TASKS_DIR 环境变量**：ci-gate-backstop.py 支持 `AGATE_TASKS_DIR` 配置任务目录路径 + 补 `import os`
- **review-mapping.md C8 机制警告**：顶部加 C8 是 mapping 机制而非结果的警告，项目方应基于本表扩展自己的 mapping
- **LIMITATIONS.md 局限 6/7/8**：运行时依赖（bash+git+python3+pyyaml）不限制被管理项目语言、vision/UI 验收依赖外部基础设施、CI backstop 仅 GHA

### 变更
- **P1 卡片评审措辞修正**：从"P1 评审与 P2 对称"改为"P1 评审通用必有，P2/P4 评审是 C8 域触发——二者不对称"
- **WORKFLOW.md 删"纯文档"范畴**：P3 裁剪条件从"纯文档/配置类"改为"配置类任务"，文档任务不是独立范畴，配置类仍是软件工作
- **state-machine.md 裁剪条件同步**：P3 从"high 风险不可裁剪"改为"仅 low 风险可裁剪"；补 P4/P5 不可裁剪
- **P3-tdd.md 裁剪条件同步**：从"risk≠high"改为"risk=low"
- **AGENTS.md 依赖节**：列出所有 8 个内联 python3 的 sh 脚本
- **check-protocol-consistency.py**：PATH_IGNORE_SUBSTRINGS 加 `docs/decisions/`（项目侧决策记录示例路径）

---

## [0.12.0] - 2026-07-12

### 新增
- **P1 强制需求评审**：P1 阶段须产出 `P1-review.md`（`status: approved` + `agent≠main` + BDD 锚点），gate 检查从 frontmatter 提取 status（非全文 grep，防正文误匹配）
- **P1 评审角色**：`assets/review-roles/requirements-review.md`，P1 阶段由独立 subagent 执行需求基线评审
- **do→review 迭代循环**：P2/P4/P6/P7 阶段卡片增加 do→review 迭代注释，retry 预算耗尽走 PAUSED
- **P5/P7/P8 subagent 派发**：P5 verifier / P7 consistency-reviewer / P8 releaser 均由 subagent 执行，主 Agent 只做 P0-brief + P8 READY 收尾
- **P7 一致性检查角色**：`assets/execution-roles/consistency-reviewer.md`，P7 阶段由 consistency-reviewer subagent 执行跨文件交叉检查
- **dispatch-context 扩展**：任务上下文节（目标/关注点/已知约束/与上阶段关联）+ P2 结构化字段 grep
- **gate 诊断落盘**：gate 失败时写入独立 `P{N}-gate-diagnosis.md`，不追加到 dispatch-context
- **N2 诊断格式禁令**：`gate-diagnosis.md` 和 dispatch-context 回退节禁止 `- PASS/FAIL` 行首（防误触审计2）
- **check-p6-format.sh**：`--fix`/`--check` 模式，仅修行首大小写+空白（无歧义自动修复），printf '%s' 防路径转义
- **PAUSED 语义翻转**：PAUSED = 正确路由（非失败），state-machine 13 处标注 + 8/8 阶段卡片 + WORKFLOW 声明
- **回退机制修正**：诊断→跳转→PAUSED→人工批准→修→重跑（替代"一次退一阶"）
- **CI 证据原则**：P6 验收声明"CI 证据原则"（L0），CI backstop 兜底外部产出 gate
- **subagent 假完成校验**：D2 最小校验 grep test runner 真实输出签名 + dispatch-prompt 返回前自检
- **P2 gate regex 放宽**：支持 Alternative/Option/多词方案名 + 数字编号（方案1/2/3）
- **verification_env 条件化**：仅 `ui_affected` 或 `e2e` 需要时声明，纯后端无需
- **CHECK 9 锚点表扩展**：6 条新增锚点（P1 review agent≠main / consistency-reviewer / dispatch-context / PAUSED / check-p6-format / gate-diagnosis）

### 变更
- `check-gate.sh` P1 分支：frontmatter 提取 status（替代全文 grep）
- `check-gate.sh` P7 分支：N3 WARNING（有 DESIGN_GAP_REVIEWED 但缺跨文件引用关键词 → WARNING，不改变 exit code）
- `check-gate.sh` P2 分支：regex 扩展支持数字编号方案名
- `dispatch-protocol.md`：P1 评审 + 迭代循环 + P5/P7/P8 派发 + 任务上下文 + 诊断落盘 + N2 + D2 + CI 证据 + verification_env
- `state-machine.md`：P1 转移 + P5/P7/P8 subagent 注释 + PAUSED 标注 + 回退修正 + 诊断落盘
- `WORKFLOW.md`：P1/P5/P7/P8 角色更新 + PAUSED 声明
- `orchestrator-template.md`：P1 不变量 + READY 交接 + 任务上下文 + verification_env
- `dispatch-prompt.md`：结构化任务节 + 返回前自检
- `verifier.md`：P5 subagent 派发说明
- `AGENTS.md`：角色清单新增 consistency-reviewer + requirements-review

## [0.10.0] - 2026-07-05

### 新增
- **逐阶段 commit 强制**：`check-state-transition.sh` 检查 3（commit gate）。推进 phase 到 Pn+1 前，Pn 产出必须已 commit——产出+推进同 commit 或产出从未 commit 均拦截。仅任务级 `.state.yaml`（`docs/tasks/Txxx/`）生效，根 `.state.yaml` 跳过。回退/PAUSED 恢复不受影响
- **拦截后处理策略**：`orchestrator-template.md` 补 8 种拦截类型对应处理方案 + 同一阶段累计 3 次拦截 → PAUSED
- **`git-integration.md` 标记强制执行**：每阶段 commit 规则由 `check-state-transition.sh` 强制执行

### 变更
- `check-state-transition.sh`: `get_old_phase` 支持任务级 `.state.yaml` 路径（`HEAD:docs/tasks/Txxx/.state.yaml`），不再只读根路径

## [0.11.0] - 2026-07-08

### 新增
- **main 分支保护**：GitHub required status checks（bats / shellcheck / consistency / gate-backstop），红 CI 阻断 PR 合入
- **CI gate-backstop job**：`protocol-tests.yml` 新增 `gate-backstop` job，CI 兜底重跑 gate + ci-gate-backstop.py
- **shellcheck -S warning**：CI shellcheck 过滤 info 级误报，只报 warning 及以上
- **bats fetch-depth: 0**：CI bats job 拉完整历史+tag，修复 CHECK 7 在浅克隆下失败

### 变更
- **CI workflow 合并**：`gate-backstop` job 并入 `protocol-tests.yml`，删除冗余的 `protocol-consistency.yml`。单一 workflow 为真相源，4 个 job：bats / shellcheck / consistency / gate-backstop
- **P2 不可裁剪**：删除 design_trivial / follows_existing_pattern / legacy_p2_pruned 例外口。design_trivial / follows_existing_pattern 语义改为"可简化 P2（1 个候选方案），不可省略 P2"
- **P6 不可裁剪**：删除 no_behavior_change 例外口。no_behavior_change 语义改为"可简化 P6（快速验收），不可省略 P6"
- **P7 裁剪加强**：声明"无隐式耦合"时须有 coupling_checklist 列出检查过的耦合点
- **T-G2.5 root_cause 更正**：从"bats not in CI"更正为"CI detective not preventive (no branch protection)"

---

## [0.9.1] - 2026-07-05

### 热修复
- **dispatch-context 强制化范围收窄**：v0.9.0 barrier 从"派发阶段任何 commit"改为"派发阶段产出 commit"。仅当该阶段的产出文件（P1-requirements.md / P2-design.md 等）被暂存时才要求 dispatch-context.md，避免拦截中间 commit / legacy 根 .state.yaml 任务 / 裁剪跳阶场景

---

## [0.9.0] - 2026-07-05

### 新增
- **Phase Card 渐进披露**：`agate/phase-cards/P{N}-*.md`（9 张）+ `agate/rules/state-transitions.md` + `review-mapping.md`（2 个）。主 Agent 按当前阶段只读一张卡片（~100 行），不再全量加载 8 个协议文件（~2900 行）。`orchestrator-template.md` mapping 表为默认入口，8 文件降级为 reference。旧 CHECK 5（协议文件计数校验）随之删除
- **agate-next-card.sh CLI**：输出当前阶段卡片全文（PHASE P0-P8）。9 个 sha256 byte-stability 硬证明测试。跨 checkout/CI 路径 hash 稳定（相对路径）
- **dispatch-context.md 防漂移**：新模板（`agate/assets/templates/dispatch-context.md`）+ hook 2p hash 校验。嵌入卡片 sha256 与 CLI 输出一致（防过期/防篡改）。**P1/P2/P3/P4/P6 派发阶段强制要求** dispatch-context.md 存在，缺则 exit 1
- **P0 gate 显式分支**：check-gate.sh 加 `P0` 分支，停止把标准阶段谎报为"未知"写入审计轨迹
- **pre-commit-gate.sh 2j/2k 容错**：仅 exit 1 拦截，exit 2 静默放过（与 2i 对齐）
- **self-gate-review:/skip: 加 ^ 行锚**：修复 commit body 任意位置提一句即绕过的假阴性
- **orchestrator-log.md 机制**：主 Agent 长操作前写 NEXT 锚点防无响应

### 变更
- 同 [Unreleased] 节（措辞修正 / LIMITATIONS 方向性错配 / self-gate 强制触发 / self-gate 递归终止 / CHECK 9 反向覆盖 / README gate 分类学 / CON.9 测试改写 / SELF-GATE 强制力边界）

### 破坏性变更
- 同 [Unreleased] 节（删 8 文件必读框架 + 删 CHECK 5 + state-machine.md:506 中断恢复语义更新 + 反向传播同步 + scripts/README.md 改检查数）

---

## [0.8.0] - 2026-07-02

### 新增
- **self-gate 反向传播机制**：SELF-GATE.md 派发模板加意图分析 + 反向传播两步。protocol-alignment-review 角色 A3 拆为 A3a（一致性连锁）+ A3b（反向传播），A5 加文档传播。加"反向传播常见路径"推理起点表。变更触发模式审查从"改了什么对不对"升级为"改了什么 + 应影响什么 + 影响到了没"
- **subagent 产出路径约束**：派发模板"## 输出"节加路径硬约束（不得将产出文件写入 /tmp 或其他路径）。新增"非阶段产出的路径规范"节覆盖 self-gate 审查/设计评审等场景。SELF-GATE.md 两个派发模板同步
- **pre-commit-gate.sh 多任务适配**：hook 扫描所有暂存的 `.state.yaml`（根 + `docs/tasks/{Txxx}/`），多任务架构下不再静默放行。新增 phase-产出一致性 WARNING（暂存了 P{n} 产出但 phase 不匹配时提醒，不拦截）

### 变更
- **check-state-transition.sh 行为变更**：
  - 回退跳变（差 ≥2 阶段）从 WARNING 恢复为 exit 1（强制 PAUSED）。之前因 `.gate-history.jsonl` 未实现降级，现确认 HEAD/staged diff 机制已隐式覆盖 PAUSED 验证，无需等待精确历史记录
  - 重试上限改为按阶段差异化：P3/P5/P6/P7/P8 = 2（上限定严，少轮次），P1/P2/P4 = 3。之前所有阶段统一为 3
- **check-retrospective.sh 同步**：复盘提醒的重试阈值改为按阶段差异化，与 check-state-transition.sh 保持同步
- **state-machine.md L407-411 回退跳变规则**：去绝对值，明确为回退方向（current - next >= 2）。前向跨阶跳不由本检查拦截，由 P5 gate 的阶段产出文件检查兜底
- **check-pruning.sh 行为变更**：
  - P8 裁剪新增 `internal_only_reason:` 字段检查（之前只查 `internal_only: true`，现在还需理由字段）
  - P6 裁剪新增"跳过风险:"评估要求（检查 7 条件补 P6）
- **check-gate.sh P2 行为变更**：
  - 新增 P2-review.md `status: approved` 检查（评审文件存在时）
  - 新增 P2-design.md 四字段计数（packages/domains/ui_affected/gate_commands ≥4）
  - 新增 P2-design.md 权衡/选择理由 form check
- **门槛表对齐**：P4 门槛从 `git log` / `P4-implementation/ 下文件非空` 改为 `git diff --cached` 暂存区检查（对齐脚本实际行为）
- **P3 裁剪措辞**：state-machine.md 从"需 risk_level=low"改为"high 风险不可裁"（对齐脚本实际行为——medium 放行）
- **P8 裁剪文档**：明确字段名 `internal_only_reason: <理由>`（之前只写"理由"未指定字段名）
- **md5 去重已实现**：check-p6-evidence.sh 新增截图 md5 重复检测（hook 强制），文档从"建议"改回"hook 强制"
- **BDD 总数对照**：从"="改为"≥"（允许 SCOPE+ 增补）
- **客观审计计数**：从"三道"统一为"四道"（R1b vision YAML 审计已落地）
- **P3 UI 用例**：从"gate 不通过"改为"主 Agent 确认"（P3 gate 不检查 UI 用例存在性）
- **pre-commit 表格**：补 P1.2 PROD_TOUCHED 行 + 调顺序对齐脚本实际执行顺序

### 影响
- 下游项目（如 PeekView）：重试超限会更早触发 PAUSED（少 1 轮），跨阶段回退会被强制 PAUSED（之前只警告）

---

## [0.5.0] - 2026-06-30

### 新增
- **hardening-roadmap Phase 1+2 完整实施**：9 项 pre-commit 检查脚本 + 1 CI backstop
  - P1.1 `check-gate.sh`：各阶段脚本化 gate（在 v0.4.0 已实现）
  - P1.6 `check-changelog.sh`：本次 `[0.5.0]` 条目含 task_id 检查（自动 run）
  - P1.7 `check-p6-evidence.sh`：P6/P7 阶段证据目录非空 + BDD 行数 ≥ 1
  - P2.1/P2.10 `check-p6-provenance.sh`：P6 客观行为审计（三道审计 + agent 字段协作规范）
  - P2.3-P2.5 `check-state-transition.sh`：状态转移合法性 + 重试上限
  - P2.7-P2.9 `check-pruning.sh`：裁剪条件 + override 校验
  - P2.11 `check-scope-resolved.sh`：`[SCOPE+]` 必须 `[SCOPE_RESOLVED]`
  - P2.12 `check-retrospective.sh`：异常模式提醒（不阻塞）
  - P2.15 `check-state-yaml.sh`：`.state.yaml` 格式校验
- **P6 客观行为审计三道硬拦截**（P2.1/P2.10 v2 降级方案）：
  - 审计 1：证据-结论对应（每条 PASS 引用证据路径 + PASS 数 ≤ 证据数 + 每个证据文件被 PASS 行引用）
  - 审计 2：`P{N}-dispatch-context.md` 禁止预判 PASS/FAIL
  - 审计 3：BDD 总数对照（P6 PASS 数 ≥ P1 BDD 数）
- **agent 字段协作规范**：阶段产出文件 Header 含 `agent: <角色>`（v2 协作层），缺字段 WARNING 不阻塞，`risk_level=high` + `agent=main` WARNING 建议派发独立 subagent
- **CI backstop（P1.3）**：`.github/workflows/protocol-consistency.yml` 增加 `gate-backstop` job，重跑 `check-gate.sh` + `ci-gate-backstop.py`（git blame P6 单 author WARNING 兜底）
- **目录结构重构**：协议本体移至 `agate/` 子目录，仓库根放项目资料（README/CHANGELOG/docs/等），`~/.agate` 软链接指向协议本体
- **`install.sh`**：一键 install（clone + 软链接），支持 `AGATE_REPO_DIR` 和 `AGATE_SYMLINK` 环境变量
- **`install-hook.sh`** 接受 AGATE_ROOT 参数：可在项目仓库内运行，明确指定 agate 路径
- **`pre-commit-gate.sh`** 路径分离：`AGATE_ROOT` 解析协议脚本（默认 `~/.agate` 软链接），`REPO_ROOT` 解析项目运行时文件
- **`agate/AGENTS.md`**：新建协议本体入口指引（角色清单 + 升级/卸载）
- **`check-protocol-consistency.py`**：`PROTOCOL_FILES/DIRS` 加 `agate/` 前缀；内部引用检查兼容子目录；FILE_COUNT_ANCHORS 锚点修复（指向真实声明位置）
- **`python3 -c "import ast"` 所有 Python 脚本语法验证通过**

### 变更
- **协议文档同步**：WORKFLOW.md / dispatch-protocol.md / state-machine.md 新增「Pre-commit 检查总览/全景」表；orchestrator-template.md 加 hardening-roadmap 关键机制段；verifier.md 加「Hardening 关键约束」段（PASS 引用证据 + dispatch-context 禁预判 + 诚实边界）
- **15 个角色文件 Header 加 `agent:` 字段**：6 个 execution-roles + 9 个 review-roles（与 role_id 对应）
- **RISK/gating 一致性**：P2 评审 risk=high 时必须派发独立 subagent，hook 对 agent=main 输出 WARNING
- **gate exit 语义统一**：`exit 0` 通过、`exit 1` 拦截、`exit 2` WARNING 不阻塞；跨脚本对齐
- **`scripts/check-p6-provenance.sh`** v2 实施：精确匹配（括号上下文）+ 只搜 PASS 行 + FAIL 词边界 + evidences/ 旧前缀兼容 + 隐藏文件排除
- **README.md**：安装命令改为 `git clone + ln -s`；新增「为什么装到 `~/oclab/agate`」段 + 常见误区 + 升级/卸载
- **.gitignore**：加 `*.swp/*.swo/*.bak/*~/.DS_Store`

### 移除/破坏性变更
- 无（向后兼容：v2 前存量任务 agent 字段缺失降级 WARNING 不阻塞）

### 修复
- agent 字段向后兼容陷阱：v2 引入前所有文件无 agent，缺失从 `exit 1` 降为 `exit 2` 不阻塞
- `get_agent()` 在 `set -euo pipefail` 下 grep 无匹配时 pipefail 传播 crash，加 `{ grep || true }` 修复
- `ci-gate-backstop.py` 中 P6 git blame 在新文件总是 WARNING 的噪音接受（M3 评审）
- 安装 hook 路径死锁：pre-commit hook 装在 agate 仓库自己时 `REPO_ROOT/scripts/` 不存在导致 gate 加载失败；用 `AGATE_ROOT` 软链接解析修复
- `__pycache__` 入库：`scripts/__pycache__/*.pyc` 被 commit；`.gitignore` 加 `__pycache__/` + `*.pyc` 防御
- 评测 README.md 末尾残留 `# test`
- `check-protocol-consistency.py` CHECK 5 FILE_COUNT_ANCHORS 第二个锚点位置错误（指向引用而非源声明）

### Known Limitations 更新
- `LIMITATIONS.md` 局限 3：v2 客观行为审计已落地（"等等" 内容已大段补全）
- 局限新增：空 png 充数仅验证引用存在性和数量，不验证内容真实性
- 局限新增：CI backstop 当前不重跑 `check-p6-provenance.sh`（只重跑 check-gate.sh），`--no-verify` 绕过 hook 时 provenance 也被绕过

---

## [0.4.0] - 2026-06-29

### 新增
- P3 gate 红灯 A/B 分类：B 类（import 未实现）exit 0 通过，A 类（测试代码 bug）exit 1。`PROJECT_MODULE` 环境变量提高精度，未设置退化为启发式
- P5 修复流程：修复 subagent 返回后主 Agent 必须重跑 P5 gate 全量测试，不是只检查修复项。修复重派 prompt 必须附修复历史
- P8 gate CHANGELOG 覆盖率检查：`git log v{prev_version}..HEAD --oneline` 对照 CHANGELOG 条目。`CHANGELOG_FILE` 环境变量支持非 CHANGELOG.md 项目
- P6 BDD 结果格式约定：必须用行首 `- PASS`/`- FAIL`，不用表格/emoji，保证 gate grep 可靠匹配
- P6 证据目录（`P6-evidence/`）：非空检查作为 self-authored gate 的造假成本提升措施
- gate 分类体系：外部产出 gate（P3/P4/P5）vs 自写文件 gate（P1/P2/P6/P7），⚠️ 标记造假风险较高的 gate
- `check-gate.sh`：P3/P4/P6/P7/P8 脚本化 gate 检查（exit 0/1/2）
- `check-protocol-consistency.py`：6 类结构一致性检查 + CI workflow
- 任务粒度指引：拆分判据从"输出异构性"改为"产出文件数 > 3"（T026 实验证实 dispatch prompt 模板可处理异构产出）
- `LIMITATIONS.md` 局限 3：self-authored gate 分类 + T026 事故记录
- CHANGELOG.md 变更日志 + README version badge 与 git tag 一致性检查（CHECK 7）

### 变更
- P6 gate exit code 从 0 改为 2：脚本化检查（FAIL=0/NC=0/证据非空）通过，但 BDD 总数对照需主 Agent 手动核实
- `check-tdd-red.sh`：新增 `PROJECT_MODULE` 环境变量，多语言 import 错误检测，TEST_RUNNER 输出契约文档化，pytest 作为参考实现
- `check-gate.sh` P8：新增 `CHANGELOG_FILE` 环境变量，扩展 version 文件匹配（go.mod/pom.xml 等），文档化单 commit 假设
- P6-evidence/ 子目录：`screenshots/` 和 `traces/` 标注为 UI 任务专属，`test-output.log` 通用
- gate 分类举例：从 pytest/vue-tsc 改为通用术语（test runner/type checker）

### 修复
- `check-tdd-red.sh`：`IndententationError` → `IndentationError` 拼写修复；SyntaxError 正则去重

---

## [0.3.0] - 2026-06-28

### 新增
- `check-gate.sh`：P3/P4/P6/P7 脚本化 gate 检查（exit 0/1 可判定，exit 2 需主 Agent 自判）
- `check-tdd-red.sh`：`TEST_RUNNER` 环境变量 + 回退链（$TEST_RUNNER → which pytest → exit 3）
- P8 gate：bump_type 字段检查、version 文件变更检查、CHANGELOG 变更检查
- T022 债务清还：P6 BDD 覆盖完整性、P8 bump 后重跑 P5、bump 判定指引、DEVIATION-CRITICAL 分类、写跑分离澄清、verifier 证据优先级（DOM > 交互 > vision）、compact 环境恢复（env_state in .state.yaml）

### 变更
- 状态机步骤 5：gate 命令分档——可 shell 化的（P3/P4/P7）写 shell 命令，不可的（P1/P2/P5/P6/P8）保留自然语言
- P5/P8 gate：bump 后必须重跑 P5 gate + bump_type 字段
- P7 gate：DEVIATION-CRITICAL 标记格式
- P8 gate：`git diff HEAD~1` 验证 version/CHANGELOG

---

## [0.2.0] - 2026-06-27

### 新增
- 分阶段落盘改为默认启用：每次派发 prompt 自带落盘指令，不再作为空返回后的补救措施
- P0-brief executor_env 补全、P0/P1 职责边界三层指引
- `LIMITATIONS.md` 局限 5：协议文档自身内部一致性验证不在流程内
- `WORKFLOW.md`：主 Agent 合法职责清单与降级硬边界

### 变更
- T020 评审修复：P6 单步函数旧表述修正（PASS/FAIL 二值），删除重复的写跑分离段落
- assets/ 与 orchestrator 同步 T016-T020 协议修复（6 个执行角色 + 4 个模板 + 所有协议文件）

### 修复
- T019 复盘修复：6 项（复盘机制核对清单模板、LIMITATIONS T019/T016 数据点等）
- T020 复盘修复：6 项（2 bug fix + 3 能力补充 + 1 已知限制）
- subagent 空返回根因验证：证实 `steps` 上限无效，分阶段落盘有效（5 组对照实验）

---

## [0.1.0] - 2026-06-26

### 新增
- 核心协议：状态机（P0-P8 阶段）、派发协议、工作流指南
- 角色体系：6 个执行角色（analyst/architect/test-designer/implementer/verifier/vision-analyst）+ 3 个评审角色
- orchestrator 模板：启动读取列表、平台专有配置区块
- git 集成、loop 编排、平台适配说明
- `LIMITATIONS.md`：5 个已知局限
- T016 复盘：5 项协议修复（输入导航、降级禁止、空返回恢复等）
- 专家评审：10 个 BLOCKER 修复 + 8 个建议

### 变更
- 通用化清理：移除 PeekView 特有内容（6 处）
- 标准安装位置：`~/.agate/`
- 上下文工程优化：orchestrator 启动时读取全部 7 个顶层文件

### 修复
- 模糊触发条件：git-integration 边界 + 评审角色判定标准
- 启动读取缝隙：orchestrator-template 改为强制启动读取，补中断恢复缝隙
