---
phase: P2
task_id: TAG0035
type: review
parent: P2-design.md
trace_id: TAG0035-P2-review-20260916
created: '2026-09-16'
agent: plan-eng-review
status: approved
---

# P2-review — TAG0035 gate 健壮性批（plan-eng-review）

> 独立评审 P2-design.md（TAG0035，4 子批 gate 健壮性方案）。评审依据：dispatch-context 约束 1-8、
> P1-requirements.md（14 条 BDD）、P0-brief.md、agate/assets/review-roles/plan-eng-review.md。
> 已对约束 2/3/4 独立读代码核实（非只信设计文档文字），见下方逐条记录。

## 逐条评审结论（dispatch-context 约束 1-8）

### 约束 1：候选方案 2 是否真实、非稻草人

**结论：成立，非稻草人。** 逐条核对候选方案 2 的三处"真实缺点"：

1. **"WARNING 语义无法被共享函数覆盖"**——成立。若真的把 `parse_phase_num_or_fail` 做成"内部直接
   `sys.exit`"的共享函数，`pre-commit-gate.py` 的一致性检查是 WARNING-only、不能拦截 commit 的语义，
   该共享函数确实无法覆盖，仍需为它单独写一条不调用共享函数的分支——统一抽象并未真正统一。这不是
   设计者编出来凑数的弱点，是真实的接口不匹配。
2. **`retries[P4]` 非空即放行削弱拦截力**——成立。`retries[P4]` 非空只代表"发生过重试"，不代表
   "此前确实交付过代码"（可能因其他门槛失败触发重试但代码从未提交）。若真的采用候选 2 这条判据，
   会造成"用状态标记代替真实代码历史证据"的实质性拦截力削弱，直接违反 known_risks 的"判据放宽不能
   削弱拦截力"要求。
3. **硬编码路径白名单扩展性差**——成立。逐场景加一个新分支/新正则，格式不统一（有的判路径前缀、有的
   判裸文件名、有的判目录），维护成本确实高于统一的"路径 token 提取 + 正则 search"模式。

三处缺点均可推演验证、非表面化陪衬，候选方案 2 是一个"真实可行但确有缺陷"的方案。**满足约束 1。**

### 约束 2：子批 B 根因判断（`_P_OUTPUT_RE` 上游过滤层）—— 已独立读代码核实

已直接读 `agate/scripts/pre-commit-gate.py`：
- `_P_OUTPUT_RE = re.compile(r"P[0-8]-.*\.md$")`（L81）
- `_P_NUM_RE = re.compile(r"P[0-8]")`（L82）
- `_phase_num()`（L192-195）：`m = _P_NUM_RE.search(phase_text or ""); return m.group(0) if m else None`
- 两处调用点：L291（`out_phase = _phase_num(out_file)`，`out_file` 取自 L282-285 的
  `_P_OUTPUT_RE.search(f)` 过滤结果）、L576（`out_phase = _phase_num(staged_file)`，`staged_file`
  同样取自 L557/L560 的 `_P_OUTPUT_RE.search(f)` 过滤结果）。

由于 `_P_OUTPUT_RE`（要求字符串中存在 `P[0-8]-` 子串）是 `_P_NUM_RE`（只要求存在 `P[0-8]`）的**更严格**
子集匹配，任何通过 `_P_OUTPUT_RE.search()` 的字符串必然也能被 `_P_NUM_RE.search()` 命中——`_phase_num`
的 `if not m: return None` 分支在这两个调用点确实**不可达**，设计对根因的断言（"真正问题在 `_P_OUTPUT_RE`
上游过滤层，而非 `_phase_num` 内部"）**成立**，已用代码结构验证，不是只信设计文档文字。**满足约束 2。**

### 约束 3：子批 C 红灯边界（`wf(<task_id>-P4` 标签匹配）—— 已独立验证，发现非阻塞的边界缺口

已用临时 git 仓库实测 `git log --grep="wf(TAG0035-P4" --fixed-strings` 的匹配行为：

```
commit message: "wf(TAG0035-P40): unrelated phase name collision test"
git log --grep="wf(TAG0035-P4" --fixed-strings --format=%H
→ 返回该 commit（匹配成功）
```

**实测确认：`--fixed-strings` 只是把 pattern 从正则改为字面量，不做任何锚定/边界约束，本质仍是
"whole message 里是否包含该子串"的 contains 判断。** 因此设计中 `_gate_p4_has_prior_code_commit` 用
`tag = f"wf({task_id}-P4"`（无收尾定界符，如 `)`或 `:`）作为 `--grep` 参数，理论上确实可能被一个
commit message 里恰好含 `wf(TAG0035-P40)`（或任何 `P4` 后接其他字符再遇到 `)` 之前的形态）的 commit
意外命中。

但进一步核实 `agate/rules/phases.yaml`：协议合法阶段名封闭为 `P0`-`P8` + `P6.5`（唯一小数阶段，挂靠
P6，非 P4），**不存在、也不会出现 `P40`/`P4x`/`P4.5` 这类"以 P4 为前缀但非精确等于 P4"的合法阶段名**，
commit message 的 `wf(<task_id>-P{阶段}):` 格式受仓库既有强制纪律约束（AGENTS.md/CLAUDE.md commit
message 规范），只会出现 `wf(TAG0035-P4):` 这一种精确形态。故此边界缺口**在当前协议阶段命名封闭的前提下
不可被实际触发**，不构成 BDD-10"纯文档、无代码历史、非回退场景仍应拦截"红灯边界的真实反例。

**判定：非阻塞，但设计文档未提及此边界假设（隐含依赖了"阶段名封闭"这一前提，却未显式写出）。**
建议 P4 实现时把 `--grep` pattern 收尾加一个定界符（如 `f"wf({task_id}-P4)"` 或 `f"wf({task_id}-P4:"`），
消除对"阶段名封闭"这一隐含前提的依赖，属于低成本的防御性加固，不要求本轮 P2 推倒重来。

### 约束 4：子批 D BDD-14 红灯用例是否真的还能拦住 —— 已独立验证

已读 `agate/scripts/check-judge-verdict.py` 现状（`_BLACKLIST_MD`/`_check_blacklist`/`_is_whitelisted`
现状实现，L62-189），并核对设计新正则 `re.finditer(r"[\w./\-]*" + re.escape(exact), low)` 的实际行为：

- `[\w./\-]*` 字符类不含反引号、空格、花括号、中文标点（`（`/`：`等）——裸写"参考 P6-acceptance.md"或
  反引号包裹 `` `P6-acceptance.md` `` 时，token 会在空格/反引号处截断，`token == exact`（或接近），
  不含 `phase-cards/`，`_PROTOCOL_SPEC_DIR_RE.search(token)` 不命中 → 不豁免 → 仍 `hits.append` →
  `exit 1`。**BDD-14 红灯用例确实仍能命中。**
- 已额外核实真实的 `P6.5-dispatch-context-judge.md` 现存样本（如
  `agate-workspace/tasks/TAG0034-dispatch-routing/P6.5-dispatch-context-judge.md`）：文中唯一出现
  `` `agate/phase-cards/P6-acceptance.md` `` 协议路径引用的位置落在 `<!-- AGATE_CARD_START -->` ~
  `<!-- AGATE_CARD_END -->` 注入块内，该块在 `_strip_card()` 阶段即被整体剥离，根本不会进入
  `_two_sections()` 扫描范围——这进一步佐证了 BDD-11 设计的豁免机制在真实场景下是防御性补强
  （即便不加这条豁免，现状的 AGATE_CARD 剥离已能规避这个具体样本的假阳性），但不影响 BDD-11/14
  设计本身的正确性判断。

**满足约束 4，设计对红灯边界的论证成立。**

### 约束 5：DoD 是否覆盖全部 14 条 BDD

第 9 节"实现完成的标志"用"14 条 BDD 逐条可执行验证命令全部按 P1-requirements.md 原文跑通"做统一声明，
未逐条摘抄独立成行，但已按子批分组列出 BDD 编号范围（A: BDD-1/2/3；B: BDD-4/5/6/7；C: BDD-8/9/10；
D: BDD-11/12/13/14），14 条全覆盖、无遗漏。BDD-2 的 `ci-gate-backstop.py` 验证点、BDD-6 的差集扫描
逻辑均已在 P1 原文对应 BDD 中显式要求，DoD 引用"按原文跑通"已隐含覆盖，不构成遗漏。**满足约束 5。**

### 约束 6：gate_commands 声明纪律（P5 三条 pytest `&&` 拼接）—— 已修复，复核通过

> **复核更新（第 2 轮）**：architect 已把 P2-design.md 第 4 节 `gate_commands` 的 `P5` 拆分为 3 个
> 独立 key（`P5`/`P5_regression`/`P5_integration`，各自单独一条 pytest 命令 + 各自
> `_timeout_seconds: 120`），三者之间无 `&&` 连接；正文"说明"段落也改写为解释"为何拆成独立 key"。
> 已重新读取当前 P2-design.md 全文逐段核对：除本处修复 + 非阻塞建议①（子批 C 的
> `_gate_p4_has_prior_code_commit` grep tag 由 `f"wf({task_id}-P4"` 改为
> `f"wf({task_id}-P4)"`，右括号定界，docstring 同步补充说明）外，其余章节（候选方案 1/2、
> 影响面梳理、子批 A/B/D 技术方案、files_to_read 12 条、env_constraints、minimal_validation、
> dispatch_plan、DoD）逐字未变，未发现意外改动。`grep -n "&&"` 全文复核确认 `gate_commands` 代码块
> 内不再含任何 `&&`，唯二命中均为正文中"不用 && 拼接"的说明性文字。**约束 6 阻塞项已消除，本条判定
> 由"阻塞"更新为"通过"。**

（以下为第 1 轮记录的原始分析，结论已被上方复核更新取代，保留存档）

设计第 4 节：
```yaml
P5: "python3 -m pytest agate/tests/unit/ -q -n auto --tb=no && python3 -m pytest agate/tests/regression/ -q -n auto --tb=no && python3 -m pytest agate/tests/integration/ -q -n auto --tb=no"
```
设计自辩"三条都是同类命令、非短路反模式，因为反模式本质风险是'后面的校验被跳过而未被发现'，三条
pytest 都是同一失败语义"。**该自辩不成立**，理由：

1. P2 卡片"`--strict` 反模式"节原文是**无条件表述**："若把多个校验命令用 `&&` 拼接成一条命令串塞进
   同一个 key，会有短路问题"——规则本身**没有为"同类命令"开例外口子**，约束的是"链式短路导致后段
   未执行"这一行为模式本身，与命令是否同源无关。
2. 三条 pytest 分别对应 unit / regression / integration 三个不同的验证范围，本仓库 `AGENTS.md`
   已明确将其作为独立"分片"对待（"全量 pytest 分 unit/regression/integration 片跑、每片大 timeout"），
   这与设计里"三条都是同类命令、非独立校验"的定性本身自相矛盾——若真是同类到可以合并，AGENTS.md
   就不会要求分片跑。
3. 实际后果：若 `unit/` 有一个用例失败，`regression/`/`integration/` 两个分片**根本不会执行**，
   本次 gate 只能看到"unit 失败"，无法一次性获知 regression/integration 是否也有问题——这正是
   "后半段从未被执行过，问题被掩盖"的具体体现，只是被掩盖的是"诊断完整性"而非"gate 是否拦截"
   （链式失败时最终退出码仍非零，不会造成误判"通过"）。
4. `gate_commands` 在 P2 固化后 P4-P6 不能改（P2 卡片"下游影响"节明文），此处若不修正，整个实现-
   验证-验收周期都会背着这条不合规声明走，修正成本随阶段推进上升。

**要求（MUST-FIX）**：拆成 3 个独立 key（如 `P5` / `P5_regression` / `P5_integration`），每个 key
各自声明 `_timeout_seconds`（可参照现有 P5 280s 预算按分片粒度重新拆分或沿用同一档位），不用 `&&`
连接，符合卡片"各自独立跑、独立记录 pass/fail"的要求。

### 约束 7：files_to_read 是否精简（12 条 vs "不超过约 10 个"）

12 个条目逐条有明确 `why` 且对应到具体子批改动落点/参照文件，未见"顺手列上"的冗余条目，但确实超出
dispatch-context 约束 8 给出的"约 10 个"软上限（超 2 条）。4 条测试文件条目（`test_check_gate.py` /
`test_check_state_transition.py` / `test_check_judge_verdict.py` / `test_pre_commit_hook.py`）均以
"既有测试写法/fixture 参照"为由列出，理由较通用，可考虑在正式派发各子批 P4 dispatch-context 时按
子批实际改动文件做二次裁剪（如子批 A 只需 `test_check_gate.py`，不需要另外 3 个）。

**判定：非阻塞。** 12 条对应 4 个被改脚本 + 4 个测试文件 + 2 个文档，考虑到本任务本身横跨 4 个脚本、
一次性交付，条目数量有客观依据、非任意堆砌；建议（非强制）P4 派发阶段按子批过滤成更小子集，不要求
本轮 P2-design.md 返工。

### 约束 8：dispatch_plan 声明合法性

已读 `agate/scripts/check-gate.py` 的 `_gate_p2_dispatch_plan()`（L743-774）实现确认：
`mode` 枚举校验只要求 ∈ `{single, static-batch, parallel, recon-then-split, serial}`——`serial`
合法；`batches` 字段的**结构校验（id/complexity/数量≤parallel_limit）只在 `mode ∈ {static-batch,
parallel}` 时触发**，`mode: serial` 时该校验分支被跳过，`batches` 字段即便存在也不会被结构校验，
不会导致 gate 报错。设计声明的
`dispatch_plan: {mode: serial, batches: [{id: sub-batch-A, complexity: low}, ...]}` 在当前
`check-gate.py` 实现下**合法可通过 P2 gate**，`batches` 部分是信息性声明（供人工/orchestrator
参考批次拆分），不违反字段契约。**满足约束 8。**

## 输出结构（按角色定义模板）

```
架构问题（阻塞级）：
  - （已修复，第 2 轮复核通过）原 gate_commands.P5 三条 pytest 分片用 && 拼接成一条命令，违反
    P2 卡片"--strict 反模式"禁令；architect 已拆成 P5 / P5_regression / P5_integration 三个独立
    key，各自声明 _timeout_seconds，无 && 连接，复核确认合规。

架构问题（非阻塞）：
  - （已采纳）子批 C 的 `_gate_p4_has_prior_code_commit` grep tag 已改为
    `f"wf({task_id}-P4)"`（右括号定界），消除了原 `--fixed-strings` 前缀子串误配的理论缺口。
  - （未采纳，接受）files_to_read 维持 12 条，architect 说明本轮不返工、留给 P4 派发时按子批裁剪
    ——上轮已判定此项不影响 approve/reject，维持该判定。

测试缺口：
  - 未发现新增测试缺口；建议（可选）为子批 C 的 grep 边界加一条"commit message 含相似但非精确
    P4 标签不应被误配"的防御性 regression 用例，与上述非阻塞项配套，非必须。

锁定决策：
  - 候选方案 1（分层精确 patch）确认锁定，候选方案 2 的三处缺点经推演成立、非稻草人。
  - 子批 B 三处独立判据设计方案确认锁定（根因判断已用代码核实成立）。
  - 子批 C 判据放宽机制（commit message 标签扫描 + git diff-tree 检查）确认锁定，红灯边界基本
    成立（附非阻塞加固建议）。
  - 子批 D 路径 token 化豁免机制确认锁定，红灯边界（BDD-14）验证成立。
  - dispatch_plan（mode: serial + 4 batches）确认合法，锁定为本任务编排方案。
```

## 门槛判定

**status: approved**（第 2 轮复核）。第 1 轮唯一的阻塞项（约束 6，gate_commands.P5 的 `&&` 链式
拼接）已由 architect 修复为 3 个独立 key（`P5`/`P5_regression`/`P5_integration`，各自声明
`_timeout_seconds: 120`，无 `&&` 连接），已重新逐段核对 P2-design.md 全文，确认：
1. 修复点本身合规——`gate_commands` 代码块内不再含任何 `&&`；
2. 除该修复 + 已采纳的非阻塞建议①（子批 C grep tag 右括号定界）外，其余全部章节内容与第 1 轮
   评审时逐字一致，未见意外改动；
3. 第 1 轮已判定成立的约束 1/2/3/4/5/7/8 结论均维持不变（本轮未重新展开分析，按主 Agent 指示
   直接沿用）。

至此本方案全部 8 条约束均已满足，无阻塞项遗留，**批准通过，可进入 P3**。
