---
phase: P4
generated_by: agate-inject-card.py + 主 Agent
task_id: TAG0035
role: implementer
---

<dispatch_guide>
> ⚠️ 以下派发指引是本次任务的强制指令，不是参考信息。执行优先级：派发指引 > 客观查证信息 > 阶段卡片（参考规范）
> 本次是 P4 子批 D（4 批中第 4 批，也是最后一批，dispatch_plan: serial）。子批 A/B/C 已实现（尚未 commit，均改 `check-gate.py`/`check-state-transition.py`/`pre-commit-gate.py`）。**本批只改 `agate/scripts/check-judge-verdict.py` + 2 处文档同步，不碰前三批已改的文件**。

### 目标

修复 `check-judge-verdict.py` 的 judge 信息隔离黑/白名单 3 处假阳性（DEBT0038，P1 BDD-11/12/13/14，P2-design.md §3.4）：黑名单用无路径边界的子串匹配误判协议规格文档引用；白名单不含角色定义文件路径；`P6-evidence/` 目录白名单不认目录下裸文件名。核心原则：**路径 token 化 + 上下文前缀判定**——只有 basename 命中且所在完整路径 token 含特定目录前缀特征时才豁免，裸 basename（无路径前缀）永远不豁免（保证 BDD-14 红灯边界不被误伤）。

### 约束

1. **`_check_blacklist()` 改造**（约第 166-177 行，BDD-11）：
   ```python
   _PROTOCOL_SPEC_DIR_RE = re.compile(r"(?:^|/)phase-cards/")   # 新增常量，紧邻 _BLACKLIST_DC_RE

   def _check_blacklist(section_lines):
       """BDD-4①/BDD-11：两节黑名单串扫描（大小写不敏感 + 归一化）。
       basename 命中时先取紧邻其前的最长路径 token，含 phase-cards/ 路径段则视为
       协议规格文档引用，豁免；裸 basename（无此前缀）仍判命中，保留对真实
       自述场景（BDD-14）的拦截。"""
       low = "\n".join(section_lines).lower()
       hits = []
       for exact in _BLACKLIST_MD:
           for m in re.finditer(r"[\w./\-]*" + re.escape(exact), low):
               token = m.group(0)
               if _PROTOCOL_SPEC_DIR_RE.search(token):
                   continue
               hits.append(exact)
               break
       for m in _BLACKLIST_DC_RE.finditer(low):
           hits.append(m.group(0))
       for m in _BLACKLIST_DIR_RE.finditer(low):
           hits.append(m.group(0))
       return hits
   ```
   **`break` 的作用**：同一 `exact`（如 `p6-acceptance.md`）若在文本里出现多次，只要有一次是裸命中（非协议路径引用）就应判命中并跳出，不需要为同一 basename 重复累加；但如果所有出现都命中了 `phase-cards/` 豁免，则该 `exact` 完全不进 `hits`。
2. **`_is_whitelisted()` 改造**（约第 180-189 行，BDD-12/13）：
   ```python
   _ROLE_DIR_RE = re.compile(r"(?:^|/)(?:execution-roles|review-roles)/")   # 新增常量

   def _is_whitelisted(tok, evidence_basenames=frozenset()):
       if "p6-evidence/" in tok:
           return True
       if _ROLE_DIR_RE.search(tok):
           return True
       base = tok.split("/")[-1]
       return base in _WHITELIST_MD or base in evidence_basenames
   ```
3. **新增 `_p6_evidence_basenames(task_dir)`**（放在 `_is_whitelisted` 之前，BDD-13）：
   ```python
   def _p6_evidence_basenames(task_dir):
       """task_dir/P6-evidence/ 目录下真实存在的文件 basename 集合（小写），
       目录不存在返回空集。供裸文件名白名单判定使用（BDD-13：判定与是否
       显式带 P6-evidence/ 前缀无关，只看该文件是否真实存在于该目录）。"""
       evidence_dir = os.path.join(task_dir, "P6-evidence")
       if not os.path.isdir(evidence_dir):
           return frozenset()
       try:
           return frozenset(
               name.lower() for name in os.listdir(evidence_dir)
               if os.path.isfile(os.path.join(evidence_dir, name))
           )
       except OSError:
           return frozenset()
   ```
4. **`_check_whitelist_outside()` 签名 + 调用处修改**（约第 192-207 行定义、约第 501 行调用，BDD-13）：
   ```python
   def _check_whitelist_outside(section_lines, evidence_basenames=frozenset()):
       low = "\n".join(section_lines).lower()
       outside = []
       for tok in re.findall(r"[\w./\-]+\.(?:md|yaml)", low):
           stripped = tok.strip()
           if _is_whitelisted(stripped, evidence_basenames):
               continue
           outside.append(stripped)
       for tok in re.findall(r"[\w./\-]+/", low):
           stripped = tok.strip()
           if "p6-evidence/" in stripped:
               continue
           if re.match(r"^p[0-9]", stripped):
               outside.append(stripped)
       return outside
   ```
   调用处（约第 501 行）改为：`outside = _check_whitelist_outside(section_lines, _p6_evidence_basenames(task_dir))`（`task_dir` 已在 `main()` 作用域内，第 486 行 `_check_evidence(task_dir, ...)` 已有先例用法，直接复用同一变量）。
5. **文档同步（BDD-12，`packages: agate-docs` 覆盖）**：
   - `agate/dispatch-protocol.md`「Judge 信息隔离」节（约第 398 行起，白名单/黑名单清单描述处）：补一句"角色定义文件路径（`execution-roles/`、`review-roles/` 目录前缀）不受此白名单限制，任意角色文件路径均视为合法引用"。
   - `agate/phase-cards/P6-acceptance.md`（约第 24 行附近，judge 复核相关行）：补一句同上说明，或直接指向 dispatch-protocol.md 该段的锚点（复用该卡片已有"见 dispatch-protocol.md「Judge 信息隔离」节"的指针式写法，不重复枚举细节，避免双源漂移——P2-design §1.3 风险表已明确这一点）。
6. **红灯边界（BDD-14）自检**：裸文件名场景（如反引号包裹 `` `P6-acceptance.md` `` 或裸写"参考 P6-acceptance.md"）token 不含路径字符前缀，`re.finditer(r"[\w./\-]*" + basename, low)` 捕获到的 token 就是 basename 本身（或极短），不会命中 `_PROTOCOL_SPEC_DIR_RE`，仍走 `hits.append`——实现完成后务必用 BDD-14 的测试验证这一点没有被约束1的改动意外放宽。
7. **验证目标测试**：
   - `test_check_judge_verdict.py::test_tag0035_bdd_11_blacklist_exempts_phase_card_path_reference`（2 个参数化：p6-acceptance.md / p4-implementation.md）
   - `test_check_judge_verdict.py::test_tag0035_bdd_12_whitelist_role_definition_file_path`（2 个参数化：execution-roles / review-roles）
   - `test_check_judge_verdict.py::test_tag0035_bdd_13_p6_evidence_bare_filename_recognized`
   - `test_check_judge_verdict.py::test_tag0035_bdd_14_self_referential_p6_acceptance_still_blocked`（当前已 PASS，改动后须仍 PASS——红灯边界不能被误伤，这是本子批最容易踩坑的地方）
8. **回归红线**：`test_check_judge_verdict.py` 全量跑，尤其关注既有 TAG0020 的 `test_bdd_1..9` 系列（信息隔离机制的原始测试）不因本次改动产生回归。

### 上游关联

- P2-design.md §1.1"改什么"表 + §3.4（子批D详述，含完整代码 + BDD-14 红灯边界论证）
- P2-review.md 约束4（已实测确认 `[\w./\-]*` 字符类不含反引号/空格/中文标点，裸写场景不会意外匹配到 `phase-cards/` 前缀——BDD-14 红灯边界成立）
- P3-test-cases.md §4.1（BDD-11 采用白盒直连 `_check_blacklist`，不用全流程 CLI 断言 exit code——测试设计已精确锚定到函数本身，你只需让 `_check_blacklist` 的返回值符合预期，不需要额外处理 `_check_whitelist_outside` 对同一路径缺乏豁免导致整体 exit 仍为 1 的问题；P3-test-cases.md §4.1 登记说明部分提到"若确认会导致真实场景整体判定仍为 exit 1，建议一并加 `_PROTOCOL_SPEC_DIR_RE` 豁免到 `_is_whitelisted`"——这是**可选**加固，不在 P1 BDD 硬性范围内，你可以做也可以不做，若不做需在 P4-implementation-D.md 说明理由）

### 输入文件

- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P2-design.md（§1.1 改什么表 + §3.4 子批D详述，完整代码已给出）
- {AGATE_WORKSPACE}/tasks/TAG0035-gate-robustness/P3-test-cases.md（BDD-11/12/13/14 对应测试函数 + §4.1 白盒测试设计说明）
- agate/scripts/check-judge-verdict.py:55-70,160-210,480-505（`_BLACKLIST_MD`/`_check_blacklist`/`_is_whitelisted`/`_check_whitelist_outside`/main() 调用点）
- agate/dispatch-protocol.md（第 398 行起「Judge 信息隔离」节，文档同步落点）
- agate/phase-cards/P6-acceptance.md（第 24 行附近 judge 相关说明，文档同步落点）
- agate/tests/unit/test_check_judge_verdict.py（`tag0035_bdd_11/12/13/14` 测试函数 + 既有 TAG0020 `test_bdd_1..9` 系列）
</dispatch_guide>

<!-- AGATE_CARD_START -->
## 当前阶段卡片：P4

路径：phase-cards/P4-implementation.md
---
# P4 — 代码实现

> 当前状态：[首次 / 重试 #N / 裁剪跳阶]
> 裁剪跳阶 → 确认 P1 phases 不含 P4 且有合规理由（check-pruning.py 已检查）→ 跳过，读 P5 卡片

## 如果是首次进入本阶段

0. 跑 `agate-capture-env-baseline.py $TASK_DIR`（自动捕获环境基线）。
   该步骤不会阻塞流程——任何 stderr 输出（含 WARNING）均可忽略，直接继续步骤 1，
   无需查看结果、无需判断、无需因为看到 WARNING 而停下来处理。

**创建型测试清理钩子（强制要求，与 P3 卡同源）**：实现含创建资源用例时，须落地清理钩子——创建即注册、测试结束无条件删除（不因响应非 2xx 中止删除）、删除接受 200/204/404 为已清理（afterEach 清理队列模式）；只修 P3 卡不修本卡即复发，两处须同步。

1. 派发 implementer subagent → 产出代码文件
   1.1 写 P4-dispatch-context-implementer.md（派发指引：目标/约束/上游关联/输入文件 + 客观查证信息）
2. 按 P2 的 gate_commands 跑单元测试（非 gate，只是自查）
3. 按 C8 映射表派发评审（见下方）
4. 预跑 check-gate.py P4（确认暂存区有代码文件）
5. git add {AGATE_WORKSPACE}/tasks/{Txxx}/ + 代码文件（含 .state.yaml，若 .gitignore 忽略需 git add -f）
   ⚠️ 此时 .state.yaml 的 phase 保持 P4，不要提前写 P5——phase = 本 commit 的产出阶段
6. git commit -m "wf({Txxx}-P4): {摘要}"（phase=P4，P4 产出含 P4-implementation.md + 代码文件）
7. P4 commit 完成后进入 P5：**phase 推进 P5 随 P5 产出 commit 一起**（P5-test-results/ 就绪后），不是单独 phase commit

## 如果是重试

确认上一轮失败原因（来自 gate 输出 / review rejected 理由）
→ 只修复失败项，不重做已通过的部分
→ 修复后重跑全量测试（T027 教训：修复可能引入回归）
→ 读 agate/rules/state-transitions.md 确认 retry 上限（P4 MAX=3）

**若这次是从 P6（或其他更后的阶段）退回来的**：`{AGATE_WORKSPACE}/tasks/{Txxx}/` 下不会再有旧的 P6-acceptance.md（已被归档），但当初具体是哪条 BDD 失败、失败原因是什么，会摘要在 `{AGATE_WORKSPACE}/tasks/{Txxx}/.retreat-history.md` 里——**重新派发 implementer 时，dispatch-context 必须引用这份摘要**，不能让 implementer 只看到"现有代码"却不知道具体要修哪里。已有代码不会被撤销、也不需要重新实现，是在已有实现基础上定向修复。**回退落地后必须建 DEBT 条目**（`source: retreat`，`evidence` 引用 retreat 提交哈希，模板 `assets/templates/tech-debt-template.md`——TAG0001 强制，见 `agate/rules/state-transitions.md` 回退规则节）。

## 前置条件

- [ ] P2-design.md 存在且 files_to_read 字段完整（导航清单）
- [ ] P2-review.md status: approved（P2 不可裁剪）
- [ ] P3-test-cases.md 存在（测试已设计）
- [ ] check-tdd-red.py 确认红灯（测试先于实现）
- [ ] 未跳过 P4（如有裁剪理由，见上方裁剪跳阶）

## 派发

- **角色**：implementer（`{agate_root}/assets/execution-roles/implementer.md`）
- **输入**：P2-design.md（files_to_read 导航 + gate_commands）+ P3-test-cases.md + P0-brief.md（env_constraints）
- **输出**：代码文件（在 P4-implementation.md 声明的 implementation_dir 下）
- **派发 prompt 模板**：`{agate_root}/assets/templates/dispatch-prompt.md` + 以下阶段特定追加：

```
## 上下文控制
读取代码文件以 P2-design.md 的 files_to_read 清单为准，按需读取（标了行号范围的只读片段）。
不要在项目里盲目搜索或整目录全读。

## 自查≠gate
写完代码后应自跑测试确认基本功能（自查），但自查通过 ≠ P5 gate 通过。
P5 由主 Agent 派发 verifier subagent 执行 gate_commands.P5，主 Agent 验 gate（检查产出 + failed 计数 + N5 最小校验）。
不要在返回中声称"P5 已过"或"全部测试通过"——只返回路径 + 摘要。
UI/前端等需构建任务：单元测试全绿不代表可用，implementer 在 P4 完成后应构建并确认 dist 等构建产物存在，不能只跑单元测试就认为完成。

## 生产环境隔离
任何写入生产环境/生产数据库/生产 API 的操作都必须先 PAUSED 报告人工。
```

## 产出规格

- P4-implementation.md 必须声明 `implementation_dir: {实际路径}`
- 代码文件在声明的目录下
- 遵守 P2-design.md 的方案设计 + 现有项目代码规范

## 新增文件核对表

> 仅当项目已采用骨架（`P2-skeleton.md` 存在）或 CODE-MAP（`{AGATE_WORKSPACE}/agents/CODE-MAP.md`
> 存在）机制时填写；未采用则本节可省略。

implementer 为本阶段**每个新增文件**填一行：

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| {path} | `within <dir>` / `[SKELETON_DEVIATION: 理由]` | `[CODE_MAP_UPDATED]` / `[CODE_MAP_EXEMPT: 理由]` |

- **骨架归属列**：新增文件落在骨架声明的目录内 → `within <dir>`；落在骨架外 → 标
  `[SKELETON_DEVIATION: 理由]`（不阻断，供 P7 核对）
- **CODE-MAP 处理列**：新增文件已同步更新 `agents/CODE-MAP.md` → `[CODE_MAP_UPDATED]`；判断
  该文件不需要更新 CODE-MAP（如临时/测试脚手架）→ `[CODE_MAP_EXEMPT: 理由]`

`change_type: refactor` 同样适用本表（不因换用回归口径而豁免）。

## 评审派发（C8 机械映射）

**在 P4 实现完成后、gate 前**，按 P1 声明的 domains 和 risk_level 派评审。C8 映射表是机械规则，不靠判断"需不需要"：

| domain | 派哪些评审 | 产出 |
|--------|----------|------|
| backend | review | P4-review.md |
| frontend | design-review | P4-review.md |
| mcp | review（关注 MCP 接口契约）| P4-review.md |
| security | cso | P4-review.md |
| risk=high | P4 实现评审（按 domains 派 review/design-review/cso；P2 plan-eng-review 已审方案，P4 实现评审不可省）| P4-review.md |
| full（tier=full 或声明 ceremony: full）| P4 实现评审（按 domains 派 review/design-review/cso，同 risk=high 不可省；P2 plan-eng-review 已审方案）+ cso（security 域）+ P7 不可裁（full 档任务 P7 为强制阶段）| P4-review.md |

多个评审角色 `专家组并行` → 所有返回后派组长汇总 → 统一 P4-review.md（status: approved / rejected）。
详见 `agate/rules/review-mapping.md`。

**并行派发**（多个评审角色时）：
1. 同时派发所有触发的评审 subagent（每个一个 task 调用）
   > **操作方式**：在一个 assistant 消息中连续发起多个 task 工具调用（每个评审角色一个）。
   > 不要等前一个 task 返回再发下一个——那是串行，不是并行。
   > 平台会并行执行多个 task，全部返回后再进入下一步（派发组长汇总）。
2. 每个评审 subagent 各写一个 dispatch-context + 各自产出文件
3. 所有评审返回后，派发组长汇总 subagent（角色：review + 指定为「专家组组长」）
4. 组长产出：P4-review.md。**agent 字段必须非 main**（与 P2 评审同规则，check-gate.py 在 P2 分支硬拦截 agent=main 的 approved）
5. 组长规则：不发表新意见，只汇总；任何 BLOCKER → rejected；分歧 → 交人工；全票无 BLOCKER → approved

**单评审角色时**：直接派发，无需组长汇总，产出直接写 P4-review.md。

**评审 checklist（RM-AG0046）**：`agate/scripts/check-maintainability.py` 检出 violations 非空时，评审角色 approve 前必须读过任务目录 `known-violations.md` 的登记理由——"是否接受该反模式"的判断权在评审角色，登记与数量对齐不单独构成放行依据。

review 不通过 → implementer 修改代码 → 再 review → … → approved（⑩迭代循环，review 和 gate 重试共享 retry 预算）

## 按包拆分并行（条件触发，需额外约束）

> 仅当 P2 packages > 1 且包间无依赖时适用。单包任务跳过本节。
> 并行上限 / 失败批 retry / 共享文件统一后处理见 dispatch-protocol「派发编排机制」并行规则。

当 P2 声明多个 packages 且包间无数据依赖时，P4 可拆分并行，但**有额外约束**：

1. 每个 package 派一个 implementer subagent
2. **各 implementer 只改自己 package 目录下的文件**——跨包的共享文件（类型定义、接口、配置）由主 Agent 在所有并行 implementer 返回后统一处理
3. 各自返回路径 + 摘要
4. 主 Agent 汇总后统一 commit
5. 主 Agent 在所有 implementer 返回后，统一处理共享文件改动（如果有）

**冲突预防**：
- dispatch-context 约束节必须写明：`只改动 {pkg}/ 目录下的文件。共享文件（{列出}）不在本次改动范围内`
- 如果某个 implementer 必须改共享文件 → 该包不能并行，改为串行（主 Agent 先派其他包并行，再串行处理含共享改动的包）
- 无法确定是否有共享改动 → 串行（安全默认值）

**基础设施隔离（并行时强制）**：
- debug server 端口：每个 implementer 的 dispatch-context 约束节分配不同端口（如 pkg-a: 3001, pkg-b: 3002）
- 测试数据库：每个 implementer 用独立数据库路径（如 `test-{pkg}.db`），不共享同一 test.db
- 环境变量：dispatch-context 写明各 subagent 独立的环境变量值（如 `PORT=3001` vs `PORT=3002`）
- 临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录

主 Agent 在并行派发前**必须**为每个 subagent 的 dispatch-context 分配上述隔离参数。当前无 gate 脚本检查（已知缺口），但未分配导致运行时冲突（端口占用/数据库锁）时计为重试，不算环境问题。

## gate 规则（check-gate.py 会跑）

```bash
check-gate.py P4 $TASK_DIR
```

- **exit 0**：暂存区含非 md/yaml 代码文件（git diff --cached --name-only）
- **exit 1**：暂存区仅 .md/.yaml 文件（无实际代码变更）→ 不能推进
- **exit 1**（RM-AG0046 三重门槛）：检测 violations 非空时，`known-violations.md` 必须存在且登记条目数 ≥ violation 数（评审检查复用上方既有 exit 1 条件；violations 为空 / 检测未部署 / git 通道不可用时不阻断）
- WARNING（不改变 exit code）：骨架/CODE-MAP 机制已采用（P2-skeleton.md 或 agents/CODE-MAP.md 存在）但缺「新增文件核对表」标题

## 推进条件（全部满足才写 phase: P5）

- [ ] 暂存区含代码文件（非 .md/.yaml）
- [ ] 按 C8 映射表触发的评审全部完成：P4-review.md status: approved（所有任务都要求——risk=high 的 P2 plan-eng-review 审方案，P4 实现评审按 domains 另行派发，不可省）
- [ ] SCOPE+ 已处理（若本阶段产生）：P1-requirements.md 有 [SCOPE_RESOLVED]（行首声明格式）
- [ ] git commit 完成

## 常见错误

1. **不读 files_to_read，在项目里乱翻**：implementer 拿到 P2 的 files_to_read 清单后应按清单阅读，不要在项目里全文搜索或整目录全读——上下文会爆炸
2. **自行加范围外改动**：发现需要做但不在 P1 范围内的改动 → 标 [SCOPE+]（行首声明格式）而非直接做
3. **只跑单元测试不验证集成**：单元测试全绿 ≠ 功能可用。P5 会跑 gate_commands 做技术验证，但要确保实现时路径依赖的端点行为已验证
4. **先更新 .state.yaml 再 commit**：state 和产出在同一 commit 里——不要先 commit 产出再单独 commit state
5. **gate 不过 ≠ 你失败了**：红灯指向工作/设计的问题，不指向你。正确动作是诊断→退回/重试/PAUSED，不是修改产出让它变绿。

## 下游影响

- P5 验证依赖：P5 跑 gate_commands.P5 的命令（在 P2 声明），确保你的实现能通过
- P6 验收依赖：实现路径的端点行为必须可验证（确认 API 返回正确的 Content-Type、状态码等）
- 代码改动文件路径：P8 发布时确认版本文件变更需要知道你改动了哪些 package

> 完成 → 读 phase-cards/P5-verification.md

6. **修改 P1 文档**：P4 发现 BDD 矛盾时标 DESIGN_GAP，不直接改 P1-requirements.md。需变更 P1 时标 `[BASELINE_CHANGE: 理由]` 并经主 Agent 批准。
<!-- AGATE_CARD_END -->

<objective_info>
- 环境：worktree 分支 feat/TAG0035-gate-robustness；python3 3.12.3 / pytest 9.0.3
- 本次核实 `check-judge-verdict.py` 现状代码：`_BLACKLIST_MD = {"p6-acceptance.md", "p4-implementation.md", "p4-review.md"}`（约第 62-66 行）；`_check_blacklist`（166-177 行，`if exact in low` 子串判定）；`_is_whitelisted(tok)`（180-189 行，仅 `p6-evidence/` 前缀 + basename 白名单两种豁免）；`_check_whitelist_outside`（192-207 行）；main() 调用点 `black_hits = _check_blacklist(section_lines)` 约497行、`outside = _check_whitelist_outside(section_lines)` 约501行；`task_dir` 变量已在 main() 作用域可用（第486行 `_check_evidence(task_dir, ...)` 已有先例）
- 子批A/B/C 已完成的改动均在 `check-gate.py`/`check-state-transition.py`/`pre-commit-gate.py`，与本批改动的 `check-judge-verdict.py` 完全不重叠文件
</objective_info>
