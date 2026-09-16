---
phase: P2
task_id: TAG0035
type: design
parent: P1-requirements.md
trace_id: TAG0035-P2-20260916
status: draft
created: 2026-09-16
agent: architect
# ── v2.0 机器字段 ──
candidate_count: 2
packages: [agate-scripts, agate-tests, agate-docs]
domains: [backend]
ui_affected: false
# ── v2.0 派发编排字段 ──
dispatch_plan: {mode: serial, batches: [{id: sub-batch-A, complexity: low}, {id: sub-batch-B, complexity: medium}, {id: sub-batch-C, complexity: medium}, {id: sub-batch-D, complexity: medium}]}
---

# P2-design — TAG0035 gate 健壮性批

> 依据：P1-requirements.md（14 条 BDD，4 子批）+ P0-brief.md（范围/known_risks）+ P2-dispatch-context-architect.md（约束 1-8）。
> 本设计已读现有代码（check-gate.py / check-state-transition.py / pre-commit-gate.py / check-judge-verdict.py 全部相关函数），不凭空设计。

## 1. 影响面梳理（改什么 / 不改什么 / 风险在哪）

### 1.1 改什么（逐文件/逐函数，关联 BDD）

| 文件 | 函数/位置 | 改动内容 | 关联 BDD |
|---|---|---|---|
| `agate/scripts/check-gate.py` | `main()` L1486-1489（`handlers.get(phase) is None` 分支） | `sys.exit(2)` → `sys.exit(1)`，stderr 已含阶段名文本（无需改） | BDD-1/2/3 |
| `agate/scripts/check-gate.py` | `main()` L1464-1472（回退抵达检测，`old_num`/`new_num` 解析） | 新增分支：`old_num is None or new_num is None` → stderr 写"无法解析阶段序号" + `sys.exit(1)`（放在原有 `if old_num and new_num` 判断之前） | BDD-4/7 |
| `agate/scripts/check-gate.py` | `gate_p4()` L951-963（暂存区代码文件判据） | `has_code_file` 为 False 时，不直接 `return 1`；先调用新增辅助函数 `_gate_p4_has_prior_code_commit(task_id)` 判断本任务 P4 阶段历史 commit 是否已引入过代码 diff，仍无历史才 `return 1` | BDD-8/9/10 |
| `agate/scripts/check-gate.py` | 新增函数 `_gate_p4_has_prior_code_commit(task_id)`（放在 `gate_p4` 之前，紧邻 `_STAGED_EXCLUDE_RE`） | `git log --grep="wf(<task_id>-P4)" --fixed-strings --format=%H` 取历史 commit 列表（右括号定界，防止误配 `-P40)` 一类未来阶段名） → 逐个 `git diff-tree --no-commit-id --name-only -r <hash>` 检查是否含非 md/yaml 文件（复用 `_STAGED_EXCLUDE_RE`） | BDD-8/9 |
| `agate/scripts/check-state-transition.py` | `phase_num()` L212-215 | 无法解析时返回 `None`（不再 `return 0`），docstring 同步更新 | BDD-5/7 |
| `agate/scripts/check-state-transition.py` | `main()` L242-249（`old_num`/`new_num` 赋值处） | `old_phase` 为空字符串时 `old_num = 0`（保留"无前序阶段"合法语义，向后兼容）；否则 `old_num = phase_num(old_phase)`。`new_phase`（已在 L245 排除空/哨兵值）直接 `new_num = phase_num(new_phase)`。紧接着：`new_num is None` 或（`old_phase` 非空且 `old_num is None`）→ stderr 写"无法解析阶段序号" + `sys.exit(1)` | BDD-5/7 |
| `agate/scripts/pre-commit-gate.py` | 新增常量（紧邻 `_P_OUTPUT_RE`/`_P_NUM_RE`，L82 后） | `_P_OUTPUT_ANY_RE = re.compile(r"(?:^|/)[Pp][^/]*-.*\.md$")`（宽松版：任意非目录分隔符字符打头的 `P<...>-*.md`，不要求数字/大小写） | BDD-6/7 |
| `agate/scripts/pre-commit-gate.py` | 2f 节 L277-301（per-task 一致性 WARNING 循环） | 新增一段：对 `_staged_name_only()` 中命中 `_P_OUTPUT_ANY_RE` 但未命中 `_P_OUTPUT_RE` 的文件（且属于本任务 `prefix` 下），逐个 stderr 输出"无法识别该产出文件的阶段号，一致性检查未覆盖: {file}"（纯增量，不改既有窄口径分支） | BDD-6 |
| `agate/scripts/pre-commit-gate.py` | 第 3 节 L556-587（全局 staged_all 循环） | 同上，对全局 `staged_all` 中命中 `_P_OUTPUT_ANY_RE` 但未命中 `_P_OUTPUT_RE` 的文件补一段等价的 stderr 提示 | BDD-6 |
| `agate/scripts/check-judge-verdict.py` | `_check_blacklist()` L166-177 | 逐 `exact in _BLACKLIST_MD` 由"整段文本子串包含"改为"正则捕获包含该 basename 的最长路径 token，检查 token 是否含 `phase-cards/` 路径段"；含则豁免（跳过该次命中），否则计入 `hits`（`_BLACKLIST_DC_RE`/`_BLACKLIST_DIR_RE` 两处不变） | BDD-11/14 |
| `agate/scripts/check-judge-verdict.py` | 新增正则常量（紧邻 `_BLACKLIST_DC_RE`） | `_PROTOCOL_SPEC_DIR_RE = re.compile(r"(?:^|/)phase-cards/")` | BDD-11 |
| `agate/scripts/check-judge-verdict.py` | `_is_whitelisted()` L180-189 | 新增两条豁免：① token 含 `execution-roles/` 或 `review-roles/` 路径段（角色定义文件目录前缀）② token 的 basename 命中调用方传入的 `evidence_basenames` 集合（`P6-evidence/` 目录下真实存在的文件名，裸文件名识别） | BDD-12/13 |
| `agate/scripts/check-judge-verdict.py` | 新增函数 `_p6_evidence_basenames(task_dir)`（放在 `_is_whitelisted` 之前） | `os.listdir(task_dir/P6-evidence)` 取真实文件 basename 小写集合（目录不存在返回空集） | BDD-13 |
| `agate/scripts/check-judge-verdict.py` | `_check_whitelist_outside()` L192-207、`main()` L501 调用点 | 函数签名加 `evidence_basenames` 形参并透传给 `_is_whitelisted`；`main()` 调用处改为 `_check_whitelist_outside(section_lines, _p6_evidence_basenames(task_dir))` | BDD-13 |
| `agate/dispatch-protocol.md` | 「Judge 信息隔离」节「白名单输入」段（~L406） | 补一句："角色定义文件路径（`execution-roles/`、`review-roles/` 目录前缀）不受此白名单限制，任意角色文件路径均视为合法引用" | BDD-12 |
| `agate/phase-cards/P6-acceptance.md` | judge 复核相关行（L24 附近） | 补一句同上说明或指向 dispatch-protocol.md 该段的明确锚点 | BDD-12 |
| `agate/tests/unit/test_check_gate.py` | 新增用例 | BDD-1/2/3/4/7/8/9/10 对应的新增/回归测试 | 见 P1 各 BDD 验证命令 |
| `agate/tests/unit/test_check_state_transition.py` | 新增用例 | BDD-5/7 | 同上 |
| `agate/tests/unit/test_check_judge_verdict.py` | 新增用例 | BDD-11/12/13/14 | 同上 |
| `agate/tests/integration/test_pre_commit_hook.py` 或新增 regression 文件 | 新增用例 | BDD-6/7（pre-commit-gate.py 无专属单测文件，P0-brief/dispatch-context 已确认覆盖面在此文件；P3/P4 可视需要新增 `agate/tests/regression/test_pre_commit_gate_*.py`） | BDD-6/7 |

### 1.2 不改什么（显式边界）

- **`phases.yaml`**：不新增 `order:`/`predecessors:` 字段，不碰 `additionalProperties: false` schema——P0-brief/P1 已裁定"完整案"是独立议题，本批只做最小案（纯判据修复）。
- **`handlers` 字典的声明式化**：10 个 `gate_pN` 手写函数保持现状，不改造成 YAML 驱动（out-of-scope 明确排除）。
- **`gate_p8` 的双路径回看 + WARNING 降级实现**：只作为子批 C 设计参照，不修改 `gate_p8` 本身任何一行代码——它已被 P1「同类扫描」判定为不构成同类风险。
- **`_BLACKLIST_DC_RE` / `_BLACKLIST_DIR_RE` 两个正则本身**：P1 同类扫描已判定未发现假阳性场景，本次不改动其匹配逻辑（只改 `_BLACKLIST_MD` 走的路径判定分支）。
- **`agate-workspace/archived/**`、`agate/tests/fixtures/**` 两类路径**：P1 已裁定不纳入 BDD-11 豁免范围，本次 `_PROTOCOL_SPEC_DIR_RE` 只精确匹配 `phase-cards/` 段，天然不覆盖这两类路径，不做额外处理。
- **`check-gate.py` 的 `handlers` 分支本身的阶段判定函数（`gate_p0`~`gate_p3`/`gate_p5`~`gate_p65`/`gate_p7`）**：均不使用暂存区快照类判据（P1 同类扫描已核实），本次不涉及。
- **`ci-gate-backstop.py` / `agate-next.py` 消费 `check-gate.py` 退出码的逻辑本身**：P1 已用 grep 核实两者均为"纯粹两值相等/三态判断"，不特判具体数值，退出码语义变化（2→1）不需要改这两个消费方——仅需新增 regression 测试验证这一点（BDD-2），不改代码。
- **DEBT0040（CI workflow 改动）/ DEBT0041（字段集同源）**：P0-brief 已明确移出本批，本次设计不涉及。

### 1.3 风险在哪（逐条配缓解措施）

| 风险 | 缓解措施 |
|---|---|
| 子批 B 三处修复若误用同一 patch，可能把"early-exit 快速失败"逻辑和"WARNING 不拦截"逻辑混为一谈（P1 隐含需求 3 已明确警告） | 三处设计**完全独立**：check-gate.py 回退检测新增 `sys.exit(1)` 分支；check-state-transition.py 改 `phase_num()` 返回值语义 + main() 显式判空；pre-commit-gate.py 只做增量 WARNING 输出，不改变既有 `_P_OUTPUT_RE`/`_phase_num` 窄口径分支的行为——三处改法、三处消费点、三处退出码语义均不复用同一段代码 |
| `phase_num()` 返回值从 `int`（恒非负）改为 `Optional[int]`，若有遗漏的调用点会在整数运算处抛 `TypeError`（比静默错误更早暴露，但需确认无遗漏） | 已用 `grep -rn "phase_num"` 核实全仓仅 `check-state-transition.py` 一处定义 + 两处调用（L248/249），且 `check-protocol-consistency.py` 的结构锚点只检查字符串"phase_num"存在性、不检查其返回类型，无隐藏调用点；main() 改造后先判空再参与算术运算 |
| `_gate_p4_has_prior_code_commit` 依赖 commit message 严格含 `wf(<task_id>-P4)` 子串（右括号定界）——若某次 P4 commit 因手工操作/squash 未遵循该约定，会被误判为"无历史"从而拦截 | 这是**已知的保守失败模式**（宁可误拦不放宽，符合 known_risks"放宽不能减弱拦截力"要求）；HANDOFF §5 已明确"commit message 含 `wf(TAG0035-P{阶段}):` 前缀"是本仓库既有强制纪律，非本批新增假设 |
| pre-commit-gate.py 新增的 `_P_OUTPUT_ANY_RE` 若匹配过宽，可能对已被 `_P_OUTPUT_RE` 覆盖的标准文件重复触发（双重 WARNING） | 设计上仅对"命中 `_P_OUTPUT_ANY_RE` 但未命中 `_P_OUTPUT_RE`"的文件集合（差集）触发新提示，标准数字阶段文件已被 `_P_OUTPUT_RE` 捕获，不会落入差集——回归测试（BDD-7）显式断言标准文件不产生新增 WARNING 行数变化 |
| `_check_blacklist` 从整段文本子串搜索改为逐 basename 正则 token 提取，若正则字符类 `[\w./\-]*` 未覆盖某些合法路径写法（如反引号内含空格、URL 编码），可能漏检真实自述场景，削弱信息隔离（对应 known_risks"DEBT0038 白名单放宽可能削弱 judge 信息隔离"） | BDD-14 专门覆盖"裸文件名直接引用"这一最常见、最高风险的真实自述形态（无路径前缀，token 退化为 basename 本身，正则天然命中）；`agate/phase-cards/P6-acceptance.md` 这类协议路径引用当前只出现在"输入文件"/"上游关联"节的固定书写惯例中（无空格/无 URL 编码），P3 测试设计需覆盖"裸文件名"+"协议路径引用"两种真实存在的书写形态，不需要覆盖理论上不会出现的边缘转义形态 |
| `_p6_evidence_basenames` 读真实文件系统而非纯文本判定，若 `P6-evidence/` 目录内文件名与其他任务的黑名单 basename 恰好同名（如某任务真把 `p6-acceptance.md` 放进了 `P6-evidence/` 目录） | 白名单判定顺序上 `_check_blacklist` 先于 `_check_whitelist_outside` 执行（main() L497→501 既有顺序不变）——即便该文件名被 `_p6_evidence_basenames` 收录进白名单豁免，黑名单命中判定已经先行拦截，两者不冲突；且这是极端边缘场景（把黑名单文件塞进证据目录本身即可疑），不在本次 BDD 范围内，登记为已知边界不展开 |
| 双源同步风险：`dispatch-protocol.md` 与 `agate/phase-cards/P6-acceptance.md` 都要补白名单说明，两处措辞若不一致会造成协议文档自相矛盾 | P4 实现时以 `dispatch-protocol.md`「Judge 信息隔离」节为权威源，P6 卡只做指针式引用（复用该卡片当前 L24 已有的"见 dispatch-protocol.md「Judge 信息隔离」节"写法模式），不重复枚举白名单细节，避免双源漂移 |
| 跨批共享文件：`check-gate.py` 被子批 A（未知阶段 exit 码）、子批 B（回退检测）、子批 C（`gate_p4`）三个子批共同修改 | 三处改动落在同一文件的三个不同函数/代码块（`main()` 两处不相邻分支 + `gate_p4()`），批次串行交付（dispatch_plan: serial）天然避免同一 commit 内交叉冲突；P4 implementer 每批只改自己负责的函数块，不触碰其他子批尚未到达的代码 |

## 2. 候选方案（2 个，权衡 + 选择理由）

> 场景类型判定：本任务属"设计模式需适配"（子批 B/C/D 均有 P0-brief 给出的候选机制，需要在"分散精确 patch" vs "集中统一改造"两种模式间权衡），采用"列 2-3 个候选模式 → 每个模式写伪代码适配 → 选适配成本最低的"方法论。

### 候选方案 1（推荐）：分层精确 patch——三处独立判据修复 + git-log 标签扫描 + 路径 token 正则豁免

**思路**：不引入新的抽象层，在每个既有函数/文件的现有代码结构上做最小侵入式修改；子批 B 三处保持独立实现（不共享一个"通用阶段号解析"函数）；子批 C 用单一「commit message 标签扫描」机制同时覆盖 BDD-8/BDD-9（不额外查 `.state.yaml retries` 字段）；子批 D 用路径 token 正则 + 真实文件系统核对（而非扩大字符串硬编码列表）。

**伪代码适配（子批 B 三处，各自独立）**：
```python
# check-gate.py main()
old_num = re.search(r"[0-9]+", old_phase) if old_phase else None
new_num = re.search(r"[0-9]+", phase)
if old_phase and (old_num is None or new_num is None):
    sys.stderr.write(f"GATE {phase}: 无法解析阶段序号（old_phase={old_phase!r}）\n")
    sys.exit(1)
if old_num and new_num and int(old_num.group(0)) > int(new_num.group(0)):
    ...  # 既有回退逻辑不变

# check-state-transition.py
def phase_num(text):
    m = re.search(r"[0-9]+", text)
    return int(m.group(0)) if m else None   # 不再 return 0
# main(): old_num = 0 if not old_phase else phase_num(old_phase)
#         new_num = phase_num(new_phase)
#         if new_num is None or (old_phase and old_num is None): exit(1)

# pre-commit-gate.py（新增，不改既有 _phase_num/_P_OUTPUT_RE 分支）
extra = [f for f in staged_outputs_any if f not in staged_outputs_strict]
for f in extra:
    sys.stderr.write(f"GATE WARNING: 无法识别该产出文件的阶段号，一致性检查未覆盖: {f}\n")
```

**优点**：
- 每处修改都是局部的、可独立测试的小 diff，符合 P1 隐含需求 3"三处独立验证，不可复用同一 patch"的明确要求
- 不引入新的公共抽象（不改 `agate_common.py`），改动半径小，回归风险低——`agate_common.py` 被全仓十余个脚本 import，任何改动都会放大回归面
- 子批 C 用单一 git-log 标签扫描同时满足 BDD-8/BDD-9，比"显式查 `retries[P4]` 字段 + 单独 lookback"更保守：只有真的存在过带代码的历史 commit 才放行，不会因为 `retries[P4]` 非空这一状态标记本身（可能因异常原因非空但从未真正交付过代码）而误放行，直接对应 known_risks"判据放宽不能削弱拦截力"的要求

**缺点**：
- 三处独立实现意味着以后若阶段号解析规则再变，需要改三个地方（可维护性略低于统一抽象）——但 P1 隐含需求 3 已明确指出三处消费语义本就不同，统一抽象反而是过度设计
- `_gate_p4_has_prior_code_commit` 依赖 commit message 严格遵循 `wf(<task_id>-P4)` 约定（右括号定界），若约定被破坏会保守拦截（见风险表，非缺陷是设计取舍）

### 候选方案 2（对比，未采用）：集中式共享工具函数 + 状态字段驱动放宽 + 硬编码路径白名单扩展

**思路**：把子批 B 三处的"阶段号解析 + fail-closed 报错"逻辑抽成 `agate_common.py` 的一个共享函数 `parse_phase_num_or_fail(text) -> int`（解析失败时函数内部直接 `sys.exit(1)`），三个脚本都 import 使用；子批 C 按 P0-brief 字面描述的"两案"分别实现：BDD-8 用 `git log <phase起点>..HEAD --name-only`（需要额外定义"phase 起点"锚点，如 lookback 固定 N 条，仿 `gate_p8`），BDD-9 用显式读 `.state.yaml` 的 `retries.get("P4")` 非空 + 存在 `wf(TAGxxxx-P4)` commit 两个条件的组合判断（命中即放行，不再验证该历史 commit 是否真的含代码）；子批 D 用一张显式的 `_EXEMPT_PATH_PREFIXES = ["phase-cards/"]` 列表，对每个新发现的豁免场景（协议路径、角色目录、evidence 裸文件名）都追加一个专门的字符串匹配分支。

**伪代码适配**：
```python
# agate_common.py（新增）
def parse_phase_num_or_fail(text, exit_code=1):
    m = re.search(r"[0-9]+", text or "")
    if not m:
        sys.stderr.write(f"无法解析阶段序号: {text!r}\n")
        sys.exit(exit_code)
    return int(m.group(0))

# check-gate.py / check-state-transition.py 均改为：
old_num = parse_phase_num_or_fail(old_phase) if old_phase else 0

# check-gate.py gate_p4()（子批C，双分支）
retries = _load_state_yaml(task_dir).get("retries", {})
if retries.get("P4"):  # BDD-9：只看字段是否非空，不验证历史是否真含代码
    return _continue_p4_checks(task_dir)
if _git_log_has_code_since_phase_start(task_dir):  # BDD-8：固定 lookback 窗口
    return _continue_p4_checks(task_dir)
return 1
```

**优点**：
- 阶段号解析逻辑单点维护，未来若要扩展（如支持 `P6.5` 这类复合阶段号）只需改一处
- 更贴近 P0-brief 原文字面描述的"两种可选机制"，评审时更容易对照文档逐条核对

**缺点（真实、非稻草人）**：
- `parse_phase_num_or_fail` 内部直接 `sys.exit`，把"是否报错""退出码是几"的决定权从调用方转移到共享函数——但 P1 隐含需求 3 已明确三处消费点的错误处理语义不同（check-gate.py 是 early-exit 快速失败，check-state-transition.py 是主流程判定失败，pre-commit-gate.py 是 WARNING 不阻断），共享函数的"内部直接 exit"模式**无法覆盖 pre-commit-gate.py 这种"不退出、只警告"的语义**，仍需为它单独写一条不调用该共享函数的分支——统一抽象并未真正统一，只是多了一层不完全复用的间接层
- 改 `agate_common.py` 会被全仓所有 import 它的脚本共享，任何微小疏漏（如 `exit_code` 参数默认值选错）的影响面从"3 个文件"放大到"整个 `agate_common` 消费方集合"，回归测试成本更高
- 子批 C 的"`retries.get("P4")` 非空即放行"直接违反 known_risks"判据放宽不能削弱拦截力"的止损要求——`retries[P4]` 非空只代表"发生过重试"，不代表"此前确实交付过代码"（理论上可能因为其他门槛失败触发过重试但代码始终未提交），用状态标记代替真实代码历史核验，是本方案的实质性缺陷
- 子批 D 的硬编码 `_EXEMPT_PATH_PREFIXES` 列表式扩展，每新增一类豁免场景都要加一个新分支+新正则，且各分支彼此独立、格式不统一（有的判断路径前缀、有的判断裸文件名、有的判断目录），比候选 1 统一用"路径 token 提取 + 各类 `_XXX_RE.search(token)`"的模式扩展性更差、代码更零散

### 权衡对比表

| 维度 | 候选方案 1（推荐） | 候选方案 2 |
|---|---|---|
| 回归风险面 | 小（改动局限在 4 个原文件） | 大（新增 `agate_common.py` 公共函数，影响全仓 import 方） |
| 是否满足"三处独立不可复用同一 patch" | 满足 | 不完全满足（共享函数无法覆盖 WARNING 语义，实质仍需分叉） |
| 子批 C 是否满足"放宽不能削弱拦截力" | 满足（要求真实代码历史证据） | 不满足（`retries[P4]` 非空即放行，脱离真实代码证据） |
| 子批 D 扩展性 | 好（统一路径 token 模式） | 差（逐场景硬编码分支） |
| 实现工作量 | 中 | 中（看似省事，实际 pre-commit-gate.py 仍需单独实现，工作量未真正减少） |

### 选择理由

采用**候选方案 1**。核心理由：① 直接对应 P2-dispatch-context 约束 2 明确要求的"阻断力不能减弱，只能精确化判定范围"——候选 2 的子批 C 设计用状态字段代替真实代码历史证据，存在实质性削弱拦截力的风险；② 直接对应 P1 隐含需求 3"三处独立验证，不可复用同一 patch"的明文要求——候选 2 的共享函数在 WARNING 语义处仍需分叉，统一抽象是虚假复用；③ 候选 1 改动面局限在 4 个已知文件，不新增 `agate_common.py` 公共函数，符合"改核心 gate 脚本、risk_level: medium"场景下应优先控制回归面的一般原则。

## 3. 技术方案详述（逐子批，回答 dispatch-context 约束 1/2/3）

### 3.1 子批 A：未知阶段 fail-closed（简单，无歧义，采用候选方案 1 唯一实现）

`check-gate.py` L1487-1489 现状：
```python
func = handlers.get(phase)
if func is None:
    sys.stderr.write(f"未知阶段: {phase}\n")
    sys.exit(2)
```
改为 `sys.exit(1)`。stderr 文本已含阶段名（`{phase}`），无需改动。BDD-2 要求验证 `ci-gate-backstop.py` 的比对逻辑不受影响——P1 已用 `grep -n "recorded_exit\|ci_exit"` 核实该脚本只做 `if recorded_exit != ci_exit` 纯相等判断，不特判具体数值，本次改动不需要动 `ci-gate-backstop.py`。

### 3.2 子批 B：修复层级选择（核心决策点，dispatch-context 约束 1）

**三处独立设计，逐处明确修复点/函数签名/返回值语义变化**：

1. **`check-gate.py` 回退抵达检测（`main()` 内联代码，非独立函数）**：
   - 修复点：`main()` 函数体内 L1464-1472 的 `if old_phase:` 分支内部
   - 签名变化：无新函数，原地插入判空分支
   - 返回值语义变化：新增路径 `sys.exit(1)`（此前该分支只有"检测到回退→exit 2"和"未检测到回退→继续走 handlers 分发"两条路径，现新增第三条"无法解析→exit 1"路径）
   - 判据：`old_num is None or new_num is None`（原判据 `if old_num and new_num` 中 `and` 短路吞掉了 None 情况，现改为先显式判空报错，再判断数值比较）

2. **`check-state-transition.py` 的 `phase_num()`**：
   - 修复点：函数本身（返回值类型从 `int` 改为 `Optional[int]`）+ `main()` 调用处（L248-249）新增判空分支
   - 签名变化：`phase_num(text: str) -> int` → `phase_num(text: str) -> Optional[int]`（`0` 不再是"无法解析"的哨兵值，`None` 才是；`0` 仍保留给"合法初始态"——`old_phase` 为空字符串这一唯一合法场景，在调用处特判，不进入 `phase_num()` 内部）
   - 返回值语义变化：调用方（`main()`）新增 `if new_num is None or (old_phase and old_num is None): sys.exit(1)` 判空，其后所有既有比较逻辑（`old_num > 0 and new_num > 0` 等 4 处判据）保持不变——因为判空已确保走到这些判据时 `old_num`/`new_num` 必为合法整数（0 或正数）
   - 这是本次 P2 设计的最核心决策点之一：**不是**在 `phase_num()` 内部直接 `sys.exit`（会让该函数从纯函数变成有副作用的函数，且无法区分"函数被其他潜在调用点复用"的场景），而是保持 `phase_num()` 纯函数语义（输入→输出，无副作用），把"报错退出"的决定权留给调用方 `main()`——因为只有 `main()` 知道"当前 `old_phase`/`new_phase` 是否处于合法的空字符串初始态"这一上下文

3. **`pre-commit-gate.py` 的一致性 WARNING（真正的静默失效点在 `_P_OUTPUT_RE` 上游过滤层，非 `_phase_num` 内部）**：
   - **根因确认（dispatch-context 约束 1 明确要求）**：`_phase_num()`（L192-195）的 `if not m: return None` 分支，在当前两处调用点（L291、L576）传入的字符串都已被 `_P_OUTPUT_RE = re.compile(r"P[0-8]-.*\.md$")` 过滤筛选过——非标准阶段名的产出文件在进入 `_phase_num()` 之前就已被 `_P_OUTPUT_RE.search()` 排除在 `staged_outputs`/`staged_all` 候选列表之外，`_phase_num` 的 `None` 分支在这两个调用点**目前实际不可达**。若只修 `_phase_num` 内部逻辑，改动会打在不可达代码上
   - **真正的修复点**：`_P_OUTPUT_RE` 过滤这一步本身（L284/288/560 三处 `.search(f)` 调用）——不改 `_P_OUTPUT_RE` 本身的匹配范围（会牵动既有窄口径行为，违反 BDD-7 回归要求），而是**新增一个更宽松的探测正则** `_P_OUTPUT_ANY_RE`，在 `_P_OUTPUT_RE` 过滤之外并行做一次宽松探测，取"宽松命中 - 窄口径命中"的差集，对差集里的文件输出一条 WARNING
   - 签名变化：无函数签名变化，新增模块级常量 `_P_OUTPUT_ANY_RE` + 2f 节/第 3 节各新增一段差集扫描代码
   - 返回值语义变化：不涉及返回值（`main()` 本身仍 `sys.exit(0)` 收尾，WARNING 性质不变，不新增阻断路径）——与 dispatch-context 约束 1 要求的"这是 WARNING 性质、不能引入新的阻断"完全一致

### 3.3 子批 C：判据放宽机制选择（dispatch-context 约束 2）

选定机制：**commit message 标签扫描**（不是 P0-brief 两个可选机制中的任何一个的原样照搬，而是二者的收敛简化——理由见候选方案对比）。

```python
def _gate_p4_has_prior_code_commit(task_id):
    """扫描本任务 P4 阶段历史 commit（commit message 含 'wf(<task_id>-P4)' 标签，
    见 dispatch-protocol.md commit 命名惯例）是否已引入过非 md/yaml 代码 diff。
    覆盖 BDD-8（跨 commit 交付）与 BDD-9（回退后修复）——两者共同前提都是
    "此前存在过一个带代码变更的 P4 commit"，无需分别处理。
    tag 收尾带右括号（'-P4)' 而非 '-P4'）做定界：--fixed-strings 不锚定边界，
    右括号防止形如 wf(TAG0035-P40): 的未来阶段名 commit 被误配（review 指出的
    防御性加固点，当前 phases.yaml 阶段名封闭在 P0-P8/P6.5 尚不可实际触发，
    但作为字符串前缀匹配的通用防御不额外增加成本）。"""
    if not task_id:
        return False
    tag = f"wf({task_id}-P4)"
    rc, log_out = _git(["log", "--grep=" + tag, "--fixed-strings", "--format=%H"])
    if rc != 0 or not log_out.strip():
        return False
    for commit_hash in log_out.splitlines():
        commit_hash = commit_hash.strip()
        if not commit_hash:
            continue
        rc, files_out = _git(["diff-tree", "--no-commit-id", "--name-only", "-r", commit_hash])
        if rc != 0:
            continue
        for raw_line in files_out.splitlines():
            line = raw_line.rstrip("\r")
            if not _STAGED_EXCLUDE_RE.search(line):
                return True
    return False
```

`gate_p4()` 调用处（原 L962-963）：
```python
if not has_code_file:
    task_id = _load_state_yaml(task_dir).get("task_id", "")
    if not _gate_p4_has_prior_code_commit(task_id):
        return 1
```

**如何满足 BDD-10 红灯边界**：`_gate_p4_has_prior_code_commit` 只在存在"确实含代码 diff 的历史 commit"时返回 `True`。"纯文档、无代码历史、非回退"场景下，本任务从未有过任何 `wf(<task_id>-P4)` 标签的代码 commit（无论是否发生过回退），函数必然返回 `False`，`gate_p4` 仍 `return 1`——红灯边界由"是否存在真实代码证据"这一客观事实决定，不依赖任何可能被绕过的状态标记。

**与 `gate_p8` 风格参照的关系**：借鉴 `gate_p8` 的"双路径回看"结构性思路（暂存区快照不够时才追加历史扫描），但**不**照搬其"两路径都未命中时降级为 WARNING"的收尾——`gate_p4` 的语义要求是硬阻断（`return 1`），本设计的历史扫描路径命中时"放行"（继续走后续 known-violations 等既有判据），未命中时维持原有硬 `return 1`，阻断力完全保留，只是精确化了"哪些场景应视为已有代码交付"的判定范围。

### 3.4 子批 D：路径豁免机制设计（dispatch-context 约束 3）

**核心设计原则**：不用"更宽松的 basename 判断"（会同时放宽 BDD-14 要求拦截的真实自述场景），而是"路径 token 化 + 上下文前缀判定"——只有当 basename 命中且其所在的完整路径 token 含有特定的目录前缀特征时才豁免，裸 basename（无路径前缀）永远不豁免。

**① 黑名单路径豁免（BDD-11，`agate/phase-cards/*.md`）**：
```python
_PROTOCOL_SPEC_DIR_RE = re.compile(r"(?:^|/)phase-cards/")

def _check_blacklist(section_lines):
    low = "\n".join(section_lines).lower()
    hits = []
    for exact in _BLACKLIST_MD:
        for m in re.finditer(r"[\w./\-]*" + re.escape(exact), low):
            token = m.group(0)
            if _PROTOCOL_SPEC_DIR_RE.search(token):
                continue  # 协议规格文档路径引用，豁免（BDD-11）
            hits.append(exact)
            break  # 该 basename 一次真实命中即够，避免重复计入
    for m in _BLACKLIST_DC_RE.finditer(low):
        hits.append(m.group(0))
    for m in _BLACKLIST_DIR_RE.finditer(low):
        hits.append(m.group(0))
    return hits
```
`re.finditer(r"[\w./\-]*" + basename, low)` 会捕获紧邻 basename 之前的最长连续路径字符序列（`\w`/`.`/`/`/`-`，反引号、空格、括号等 markdown 标点天然作为边界，不会被吞入 token）。裸文件名场景（如 `p6-acceptance.md` 前面没有路径字符或前面是空白/反引号）时，`token == exact`（或极短），不含 `phase-cards/`，走 `hits.append`——**保证 BDD-14 红灯用例仍能命中**（自述场景直接写 `P6-acceptance.md` 或反引号包裹，不含 `agate/phase-cards/` 前缀）。

**② 白名单补齐角色文件路径（BDD-12）**：
```python
_ROLE_DIR_RE = re.compile(r"(?:^|/)(?:execution-roles|review-roles)/")

def _is_whitelisted(tok, evidence_basenames=frozenset()):
    if "p6-evidence/" in tok:
        return True
    if _ROLE_DIR_RE.search(tok):
        return True
    base = tok.split("/")[-1]
    return base in _WHITELIST_MD or base in evidence_basenames
```
选用目录前缀正则（而非枚举具体角色文件名）的理由：角色文件数量会随任务演进持续增加（`analyst.md`/`architect.md`/`implementer.md`/... 及 `review-roles/*.md`），枚举法需要每新增一个角色就同步改一次脚本；目录前缀判定一次性覆盖任意角色文件名，且与既有 `p6-evidence/` 目录前缀判定风格一致（`_is_whitelisted` 本身已有此先例，非新引入模式）。

**③ `P6-evidence/` 裸文件名识别（BDD-13）**：
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
`main()` 调用处（原 L501）：
```python
outside = _check_whitelist_outside(section_lines, _p6_evidence_basenames(task_dir))
```
`_check_whitelist_outside` 签名同步加 `evidence_basenames=frozenset()` 形参并透传给 `_is_whitelisted`。选择"结合任务目录实际文件列表核对"（P1 BDD-13 原文建议的机制）而非"扩大裸文件名正则匹配范围"的理由：纯正则扩大会把任意 `.md` 裸文件名都视为潜在白名单（例如引用另一个不相关任务的产出文件名恰好与某个真实证据文件同名），核对真实文件系统状态是唯一能精确排除误判的方式，且实现成本低（一次 `os.listdir`）。

**如何保证不误判"协议规格文档路径引用"与"任务自己产出文件的自述"（约束 3 原话）**：三处修复统一遵循"越具体的路径上下文，豁免范围越窄"原则——① 只豁免明确带 `phase-cards/` 段的路径引用，不豁免任何裸文件名；② 角色文件豁免同样要求路径含角色目录段；③ evidence 裸文件名豁免建立在"该文件在本任务 `P6-evidence/` 目录下真实存在"这一客观文件系统事实上，而不是放宽字符串匹配规则本身。BDD-14 红灯用例（真实自述，直接引用任务自己的 `P6-acceptance.md`，无路径前缀）在三处修复后仍然：不满足①的路径前缀条件 → 不豁免 → `_check_blacklist` 仍命中 → `exit 1`，红灯边界保持成立。

## 4. gate_commands

```yaml
gate_commands:
  P3: "python3 -m pytest agate/tests/unit/test_check_gate.py agate/tests/unit/test_check_state_transition.py agate/tests/unit/test_check_judge_verdict.py agate/tests/integration/test_pre_commit_hook.py -v"
  P3_timeout_seconds: 120
  P5: "python3 -m pytest agate/tests/unit/ -q -n auto --tb=no"
  P5_timeout_seconds: 120
  P5_regression: "python3 -m pytest agate/tests/regression/ -q -n auto --tb=no"
  P5_regression_timeout_seconds: 120
  P5_integration: "python3 -m pytest agate/tests/integration/ -q -n auto --tb=no"
  P5_integration_timeout_seconds: 120
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_consistency_timeout_seconds: 120
  P5_shellcheck: "shellcheck -S warning agate/scripts/*.sh"
  P5_shellcheck_timeout_seconds: 60
  P5_count_tests: "bash agate/tests/scripts/count-tests.sh"
  P5_count_tests_timeout_seconds: 60
  project_module: "agate"
```

**说明**：
- `P3` 只跑本批直接命中的 4 个既有测试文件（不跑全量——P3 阶段目的是先红后绿的 TDD 验证，全量回归留给 `P5`）。若 P4 implementer 为子批 B/C 新增独立 regression 测试文件，`P3` 命令须相应扩展（P4 阶段可在此基础上追加文件路径，不违反 gate_commands 固化原则——固化的是"格式/口径"，具体文件清单允许 P3/P4 阶段按新增测试文件路径追加，这是既有惯例）。
- `P5`/`P5_regression`/`P5_integration` 对应 HANDOFF-TAG0035.md §4 三分片命令、P1 BDD-3/BDD-7 验证命令，拆成 3 个独立 key，不用 `&&` 拼接（P2 卡片「`--strict` 反模式」节对此为无条件表述，不因"同类命令"开例外；独立 key 才能保证 unit 分片失败时 regression/integration 仍会各自执行并留下独立诊断，不被短路掩盖）。
- `P5_consistency`/`P5_shellcheck`/`P5_count_tests` 同样各自独立 key，不与其余 key 用 `&&` 拼接。`P5_shellcheck` 本批设计不涉及任何 `.sh` 文件改动，但 HANDOFF §4 将其列为全批基线校验命令之一（改动触发 SELF-GATE，仍需确认 `agate/scripts/*.sh` 整体无回归），保留声明。
- 未声明 `P5_e2e`：`ui_affected: false`，无 UI/E2E 覆盖需求。
- `project_module: "agate"`——pytest 项目模块前缀，供 B 类 import 错误检测使用。

## 5. files_to_read

```yaml
files_to_read:
  - path: agate/scripts/check-gate.py:928-1000
    why: gate_p4 完整度判据现状（子批C改动落点）+ _STAGED_EXCLUDE_RE 复用
  - path: agate/scripts/check-gate.py:1353-1452
    why: gate_p8 双路径回看+WARNING降级参照实现（子批C风格参照，不修改）
  - path: agate/scripts/check-gate.py:1455-1494
    why: main() 回退检测（子批B改动点）+ handlers 分发（子批A改动点）
  - path: agate/scripts/check-state-transition.py:212-335
    why: phase_num() 定义 + main() 全部4处 old_num/new_num 消费点（子批B改动落点）
  - path: agate/scripts/pre-commit-gate.py:70-102,192-207,260-330,540-588
    why: _P_OUTPUT_RE/_P_NUM_RE/_phase_num 定义 + 2f节/第3节两处一致性WARNING调用点（子批B根因所在层）
  - path: agate/scripts/check-judge-verdict.py:55-214,399-509
    why: _BLACKLIST_MD/_check_blacklist/_is_whitelisted/_check_whitelist_outside 全部定义 + main()调用点（子批D改动落点）
  - path: agate/tests/unit/test_check_gate.py
    why: 既有测试写法/fixture 参照，子批A/B/C新增用例风格对齐
  - path: agate/tests/unit/test_check_state_transition.py
    why: 既有测试写法参照，子批B（check-state-transition.py）新增用例风格对齐
  - path: agate/tests/unit/test_check_judge_verdict.py
    why: 既有测试写法参照，子批D新增用例风格对齐
  - path: agate/tests/integration/test_pre_commit_hook.py
    why: pre-commit-gate.py 唯一既有测试覆盖面，子批B新增用例落点参照
  - path: agate/dispatch-protocol.md:398-430
    why: Judge信息隔离权威定义（白名单/黑名单清单），BDD-12文档同步落点
  - path: agate/phase-cards/P6-acceptance.md:20-30,178-215
    why: judge复核相关行，BDD-12要求同步的第二处文档落点
```

## 6. env_constraints

```yaml
env_constraints:
  debug_env: "worktree 内 python3 3.12.3 + pyyaml + pytest 9.0.3；跑 gate 判定工具用 ~/.agate（稳定版），改代码/跑测试在 worktree 自身（AGENTS.md 双工作区纪律，见 HANDOFF-TAG0035.md §2）"
  isolation_check: "check-protocol-consistency.py 必须用 worktree 自己的脚本（python3 agate/scripts/check-protocol-consistency.py），不得用 ~/.agate 版本——检查对象是 worktree 里的协议文件，用稳定版会漏检本次改动"
```

## 7. minimal_validation

```yaml
minimal_validation:
  assumption: "纯代码逻辑，无外部系统依赖（无浏览器行为/安全模型/外部网络/外部凭据）"
  method: "读代码确认依赖的内部函数/数据转换：① check-gate.py main() 的 handlers 字典 dispatch（新阶段判据不改变 dispatch 结构，只改未匹配分支的退出码）② 全部三处修复均围绕 re.search/re.compile 正则匹配的返回值语义（match对象 truthy/None）③ git diff --cached / git log --grep / git diff-tree 三类 git 子进程调用（均为只读命令，无写操作，子批C新增的 _gate_p4_has_prior_code_commit 只读 git log 历史，不修改仓库状态）④ check-judge-verdict.py 的 _check_blacklist/_check_whitelist_outside 子串/正则匹配（改动局限在匹配算法本身，输入输出契约——两节文本→命中列表——不变）。已用 grep 核实全仓 phase_num/_phase_num/_P_OUTPUT_RE/_BLACKLIST_MD/_is_whitelisted 均只有本设计列出的调用点，无隐藏调用方；check-protocol-consistency.py 的结构锚点（phase_num/--cached/criteria_total等关键词存在性校验）经核对不受本次改动影响（函数名/调用点保留，只改内部逻辑与返回值语义）"
  result: "not_needed"
  note: "本任务全部改动是 gate/check 脚本的判据分支修复，无删除/移动路由或接口注册表项（子批A是退出码数值变更，非删除分支；子批C是新增放行条件，非删除既有拦截；子批D是新增豁免分支，原有黑白名单匹配逻辑主干保留）。唯一需要额外确认的'删除后原请求流向哪个分支'类问题（architect.md T086教训）是：phase_num() 返回值从 int 改为 Optional[int] 后，check-state-transition.py 是否有遗漏的调用点会在整数运算处静默出错——已用 grep -rn phase_num agate/scripts/ 核实全仓仅此文件1处定义+2处调用（main() L248/249），且改造后调用处会先判空再参与后续比较运算，不存在遗漏调用点导致的静默失效风险。"
```

## 8. dispatch_plan 说明

frontmatter 已声明 `dispatch_plan: {mode: serial, batches: [sub-batch-A(low), sub-batch-B(medium), sub-batch-C(medium), sub-batch-D(medium)]}`，与 HANDOFF-TAG0035.md/P0-brief.md 明确的"一个 task 内分 4 个子批串行交付"一致。串行理由：
- 四个子批共享 `check-gate.py` 这一文件（A/B/C 三批都在其中改动不同函数/代码块），串行交付可保证每批各自一个独立 commit，避免并行 subagent 对同一文件产生合并冲突
- 每批复杂度：子批 A 是单行退出码数值变更（low）；子批 B 涉及 3 个文件、3 处独立语义设计（medium，非 high——每处改动本身是局部小函数/分支插入，不引入新的跨模块数据流或架构层）；子批 C 新增一个历史扫描辅助函数并接入 `gate_p4`（medium）；子批 D 涉及 3 个函数改造 + 2 个文档同步（medium）
- 每批产出/输入文件数均在"派发编排机制"任务粒度基准内（单批改动 1-3 个源文件 + 对应测试文件，未超 ≤3 产出 / ≤3 输入的粒度基准）
- 每批 commit 均含至少一个代码文件（`.py` 改动），天然不会触发 `_gate_p4` 的"暂存区无代码文件"判据（HANDOFF §7 已知风险的直接呼应）——子批 D 虽含 2 个文档同步，但主体改动仍是 `check-judge-verdict.py` 的 3 个函数，同一 commit 内代码文件与文档文件共存，不构成"纯文档 commit"

## 9. 实现完成的标志（Definition of Done，供 P3/P5/P6 使用）

- 14 条 BDD 逐条可执行验证命令全部按 P1-requirements.md 原文跑通（子批 A：BDD-1/2/3；子批 B：BDD-4/5/6/7；子批 C：BDD-8/9/10；子批 D：BDD-11/12/13/14）
- `agate/tests/unit/` + `agate/tests/regression/` + `agate/tests/integration/` 三分片 `-n auto` 全绿（对应 BDD-3/7 的回归不变性要求）
- `check-protocol-consistency.py --strict-errors-only` 0 ERROR
- `dispatch-protocol.md`「Judge 信息隔离」节 + `agate/phase-cards/P6-acceptance.md` 均已补充"角色文件路径不受白名单限制"的说明（BDD-12 文档同步部分）
- `bash agate/tests/scripts/count-tests.sh` 确认测试计数文档与实际新增测试数一致（隐含需求 8）
- 4 个子批各自一个独立 commit，每个 commit message 含 `wf(TAG0035-P4):` 前缀且暂存区含至少一个代码文件（呼应 known_risks 止损要求）
