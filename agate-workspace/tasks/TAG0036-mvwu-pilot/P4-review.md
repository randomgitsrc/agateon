---
phase: P4
task_id: TAG0036
parent: P4-implementation.md
trace_id: TAG0036-P4-20260919
created: '2026-09-19'
agent: review
status: approved
---
# P4 实现评审（review，偏执 Staff Engineer）— TAG0036 MVWU 阶段 1 观测器

[PROD_NOT_TOUCHED] 只读评审：未改任何代码/文档，未 git add/commit，未触碰 `~/.agate`；所有实测用 `mktemp -d` 临时目录/临时 git 仓库，已全部删除；`git status` 除既有改动与 `P4-review.md` / `P4-review-progress.md` 外无新增。这是重派轮（上轮因限流中断），下列全部结论为本轮**独立实测**所得。

**结论：approved（0 个 BLOCKER；Pass 1 CRITICAL 无；Pass 2 有 1 条 MAJOR 建议修复 + 若干 INFORMATIONAL）。**

## 关于上一轮遗留问题：`--observe` 耗时列遇超长数字吞行 —— 独立复现并定级

**判定：真实缺陷，确认；定级 MAJOR（应修，建议本任务内顺手收口），不是 BLOCKER。**

- **最小复现**（Python 3.12.3）：任务目录含 3 批 b1/b2/b3，b2 的证据含 `duration_seconds: 99…9`（5000 个 9；或 4301 个 9；或 `9`×400 + `.5`）：
  ```
  $ check-mvwu.py --observe <task_dir>
  check-mvwu: internal error: ValueError: Exceeds the limit (4300 digits) for integer string conversion ...
  | b1 | pytest a | 12.5s | yes | UNKNOWN | UNKNOWN | PASS |
  | - | - | - | no | UNKNOWN | UNKNOWN | UNKNOWN |
  ```
  期望 3 行（每批一行），实得 2 行：b2、b3 丢失，且被 `main()` 兜底的"无批"占位行（第 1 列 `-`）顶替。默认（非 observe）模式**不受影响**（3 行 PASS 正常）。
  - 变体：`.` 形态 `"9"*400 + ".5"` → `float()` 得 `inf` → `int(inf)` 抛 `OverflowError`，同样吞行。
  - 边界：恰 4300 位数字**不**触发（正常输出超长单元），4301 位起触发；无小数点分支的触发点取决于 `sys.int_info.str_digits_check_threshold`（3.11+；3.8-3.10 无此限制，仅小数分支会溢出）。
- **根因**：`agate/scripts/check-mvwu.py:136-144` `_fmt_duration`：`DURATION_RE = [0-9]+(\.[0-9]+)?` 对位数无上限（行 61），随后 `int(raw)`（行 140）/ `float(raw)` + `int(val)`（行 141-143）对超大值抛 `ValueError`/`OverflowError`。该调用位于 `_run` 的观察表输出循环内（行 447-452），**没有 per-row try/except**（对照 verdict 判定在行 432-436 有 per-batch 兜底，`--observe` 的 `_forms_and_boundaries` 在行 442-446 也有）。异常一路冒到 `main()` 的兜底（行 468-471），该兜底打印单行占位后返回，已印出的行保留、其余批全部丢失。
- **为何不是 BLOCKER**：① 脚本是不阻断的观测器，exit 0 / verdict 不受影响（默认契约行完好，verdict 只经契约行表达）；② 触发需要证据里出现 300+ 位的耗时数字，而 `duration_seconds` 由主 Agent 机械转录真实运行耗时，正常运行不可能出现；③ 失败方向是"少输出行 + stderr 有诊断"，非 fail-open（不会把 UNKNOWN 变 PASS）。
- **为何仍应修（MAJOR）**：违反口径 A/D 的"每批恰一行"不变量与 BDD-45（"不可解析 → `-`"）；观察表是日后的试点数据来源，静默缺行会让统计失真且行数与批数不对齐，脚本自身承诺"任何异常仅影响该批"在此处被破坏。
- **修法（只说怎么改）**：任选其一或叠加——(a) `DURATION_RE` 限长，如 `[0-9]{1,15}(?:\.[0-9]{1,15})?`（不可解析即落 `-`，与既有 BDD-45 语义一致，改动最小）；(b) `_fmt_duration` 内 `try: ... except (ValueError, OverflowError): return "-"`；(c) 在输出循环里对每行 `render_observe_row(...)` 计算包 per-row try/except，失败时输出该批 `UNKNOWN` 行（同时消除同类未来隐患）。推荐 (a)+(c)。补一条单测：耗时 5000 位数字的批仍输出恰 N 行、该批耗时列 `-`。

## Pass 1 —— CRITICAL（数据安全 / 正确性 / 只读性）

**无 CRITICAL。** 逐项核查与实测如下（全部在 `mktemp -d` 内实跑）：

1. **只读 / 从不执行**（约束 1）：
   - 静态：`check-mvwu.py` 无 `subprocess` / `os.system` / `shell=` / `exec` / `Popen`；唯一外部进程调用是 `agate_common.run_git`（`agate_common.py:50`，列表参数 `["git", *args]`，无 shell）；仅有的两个 `open()`（行 82、182）均为 `"rb"` 只读。`shlex.split` 仅用于词法切分，命令永不执行（`_first_word_ok` 只做 `shutil.which` / `os.path.isfile` + `os.access(X_OK)` 静态探测）。
   - 实测哨兵：证据 `command: touch <tmp>/sentinel_cmd` 且 `tests_filter: "touch <tmp>/sentinel_tf"`，默认与 `--observe` 两模式各跑 → 哨兵文件均**未生成**（`ls | grep sentinel` 空）；临时目录内无任何新文件（仅本人预先构造的输入）；该批 verdict PASS（首词 `touch` 可解析，符合口径 F"只判首词"）。
2. **特殊字符 / 输入注入**（约束 1）：14 个构造批（`a b` / `a|b\`c` / `../../outside` / `/etc/passwd` / `é\nnl` / 数字 id `12345` / 缺 id / 非 dict 批 / 符号链接证据 / BOM+CRLF 证据 / 非 UTF-8 证据 / 超长）→ 默认与 `--observe` 各**恰 14 行**，无 traceback，rc=0：
   - 不合规 id 均按 UTF-8 字节输出 `\xNN`（`é\nnl` → `\xc3\xa9\x0anl`），非字符串 → `?`，契约行可按空白分词；`tests_filter` 含换行/`|`/反引号/`\` 按 GFM 转义为 `line1\nline2 \| \`x\` \\`，恰 7 列。
   - 路径穿越：`../../outside`、`/etc/passwd` 因 id 不匹配 `ID_RE` 根本不拼路径（`_read_evidence` 行 173-174），`evidence=no`；含 `outside_ok.log` 的**符号链接逃逸**（`P4-evidence/sym.log -> 任务目录外`）→ `_under(realpath)` 判 CORRUPT，`UNKNOWN reason=evidence`，未读取外部文件；`P4-evidence` 整目录为指向外部的符号链接同样 fail-closed（UNKNOWN，见 INFO-5）。
   - BOM+CRLF 证据（行 183 `utf-8-sig`、行 161 剥 `\r`）正确解析为 PASS；BOM+CRLF 的 `P2-design.md`（行 86）正确解析；非 UTF-8 证据 → `UNKNOWN reason=evidence`；超长 id（>255 字节文件名）→ `isfile` 返回 False → `evidence`，无异常。
   - `task_dir`：不存在 / 是文件 → stderr + rc=2；以 `-` 开头：`-- -x` 正常处理（git 仅经 `cwd=` 传递，不进 argv，无伪参数注入面），裸 `-x` 被 argparse 拒（rc=2）；含空格 OK；无 P2 / P2 非 UTF-8 / frontmatter 语法坏 / `batches` 空列表 / `batches` 非列表 → 一行 `UNKNOWN batch=- reason=tests_filter`；无 `.git` → verdict 正常、git_head 类全部 `UNKNOWN reason=git_head`（fail-closed）、observe 有 `baseline: not a git repository`。
3. **git 调用面**（约束 1）：所有 git 调用均只读（`rev-parse` / `cat-file -e` / `symbolic-ref -q` / `merge-base` / `rev-list --count` / `log --no-merges --no-renames --name-only -z`）。证据 `git_head` 先过 `SHA_RE.fullmatch`（仅 hex，40/64 位）才拼进 `cat-file -e <sha>^{commit}`；注入形态 `--output=/tmp/x…`、短 sha、全零 sha、大写 sha 实测：注入/短/全零 → `git_head`，大写 → PASS（口径 G 大小写不敏感，符合）。`git` 不在 PATH（`env PATH=/nonexistent`）→ `run_git` 吞 `OSError`、降级为 "not a git repository"，无崩溃。
   - `-z` 解析实测（临时 git 仓库，feature 分支含 `src/a b.py`、`src/é.py`、含**换行**文件名 `src/nl\nx.py`、tasks 目录内文件、合并提交）：批 `output` 命中三种奇异文件名 → `per-batch exact`；提交同时含 tasks 目录笔记 → 前缀排除后仍 `exact`；两批共享同一提交 → `merged / UNKNOWN`；合并提交内的 side 提交文件仍被计入（`--no-merges` 仅去合并提交本身）；缺 `output` / 无匹配提交 → `UNKNOWN`。单趟 `git log` 一次读取，无 N×M git 调用；批间比较为集合运算，B²（批数）量级，可忽略。
4. **异常兜底**（约束 1）：无裸 `except:`；全部为 `except Exception` / 具体异常，`KeyboardInterrupt` / `SystemExit` 不被吞。`judge_batch` 外有 per-batch try（行 432-436）：构造 `exit_code: 99…9`（5000 位）触发 `int()` `ValueError` → 仅该批 `UNKNOWN reason=evidence` + stderr 诊断，其余 26 批不受影响；`expected_red` 5000 层嵌套括号（`RecursionError`）与 YAML 锚点别名 → 被 `_parse_list` 的 `except Exception` 兜住，落 `expected_red`。**唯一漏网点是 `--observe` 输出循环**，见上文 MAJOR。
5. **verdict 正确性**（约束 1，本轮实测 27 个证据用例，均在 git 临时仓库内，全部与口径 A-H 一致）：`exit 0`→PASS；`exit 1` 无 expected_red→FAIL；`exit 1` + failed 全命中 expected_red（含 `b::t[x,y]` 带逗号方括号 id）→EXPECTED_RED；failed 含预期外用例→FAIL；`exit 0` + `failed_tests` 非空（自相矛盾）→`UNKNOWN reason=exit_code`（先于 git_head，符合口径 B 顺序）；`exit 1` + expected_red 非空但无 failed→`UNKNOWN reason=expected_red`；`expected_red` 非 flow 序列 / 含非字符串元素 / 嵌套炸弹→`UNKNOWN reason=expected_red`；`expected_red: []` + failed 非空→FAIL；`exit_code: 0x0` / `abc`→`exit_code`；无 command / 空 command / 引号未闭合 / 不存在的二进制 / 不存在的相对脚本 / 含 NUL 的命令→`command`（六项优先级 tests_filter→evidence→command→exit_code→git_head→expected_red 与设计一致，如 command 与 git_head 同时缺时取 `command`）；`FOO=1 BAR=2 python3 -c 1` 跳过前导赋值 PASS；仅注释/空证据→`evidence`；重复 id 批所有出现均 `evidence`。UNKNOWN 无任何路径被当作 PASS（`judge_batch` 只有行 276 一处返回 PASS，且前置 5 项均已通过）。
6. **平台 / 语法**（约束 1）：`ast.parse(..., feature_version=(3,8))` 通过；无 `match` / `removeprefix` / `X | Y` 注解；`grep '/tmp'` 无命中；文件读写显式 utf-8（`rb` + 手动 decode）；`sys.stdout.reconfigure` 缺失时（以无该方法的包装对象实测）不崩（行 456-459 `hasattr` + `suppress`）；`--help` 含三条字面局限（"检查 3 仅检查首词" / "不比对 command 与 tests_filter" / "UNKNOWN 不等价于 PASS"）；`BrokenPipeError`（`| head -1`）安静退出、rc=0。
7. **M18**（约束 2）：`git diff HEAD -- agate/scripts/check-protocol-consistency.py` 恰**+1 行**（`GATE_SCRIPT_EXEMPT` 集合内新增 `"agate/scripts/check-mvwu.py",  # 观测脚本，不挂 gate`），其余零改动；`check-protocol-consistency.py` 全量运行 0 ERROR。
8. **范围**（约束 4）：`git diff HEAD --stat` 15 个文件 / 173 增 2 删，无 `check-gate.py` 等内核脚本被改，无 `.sh` 新增/修改；`git diff HEAD -- agate/tests/unit/test_mvwu_protocol_docs.py agate/tests/unit/test_check_mvwu.py` 仅 `test_mvwu_protocol_docs.py` 一行注释措辞修订（`无 /tmp 字面量` → `不依赖固定临时目录路径字面量`），无断言被放宽；`test_check_mvwu.py` 无 diff；`pytest test_check_mvwu.py` 109 passed（实测）。新增未跟踪文件仅 `agate/scripts/check-mvwu.py`（+ 任务目录产出）。

## Pass 2 —— INFORMATIONAL

- **[MAJOR·建议修复] `check-mvwu.py:136-144`（`_fmt_duration`）+ `:447-452`**：见上文"关于上一轮遗留问题"。
- **[INFO-1] `check-mvwu.py:158-168`（`_parse_evidence`）重复键后者覆盖，冲突值无提示**：实测证据含 `exit_code: 1` 后接 `exit_code: 0` → `PASS`（后者胜）。因证据由机械转录写入，正常不出现；但"两条矛盾的退出码"取 PASS 方向属 fail-open 味道，与 "UNKNOWN≠PASS / 无法核对不放行" 哲学略不一致。docstring 已声明该语义且无 BDD 反向要求，故仅建议：重复键且值不同 → 该批 `UNKNOWN reason=evidence`（或至少 stderr 告警）。可选，不阻断。
- **[INFO-2] `check-mvwu.py:423-430`（重复 id 判定）大小写不敏感文件系统**：批 id `A` 与 `a` 在 Windows/macOS 默认文件系统上共用同一 `.log` 文件，但 `counts` 按区分大小写计，二者不被判重复，`a` 的证据可被 `A` 读到。实测（Linux）`A`→evidence（无文件）、`a`→PASS，行为正常；此为跨平台窄缝隙，观测器不阻断，仅记录。
- **[INFO-3] `check-mvwu.py:263-265`**：`exit_code` 为 5000 位整数时经兜底得 `reason=evidence` 而非 `exit_code`（值"非整数"口径的边缘；实际仅 stderr 多一条 `internal error`）。同一类"大整数"隐患，修 MAJOR 时可一并给 `int()` 加保护（如 `INT_RE` 限长）。
- **[INFO-4] `check-mvwu.py:461-463`**：`task_dir` 为文件时提示"目标目录不存在"措辞略不精确（应为"不是目录"）；不影响 rc=2 契约。
- **[INFO-5] `check-mvwu.py:178-180`**：`P4-evidence` 整个目录是指向仓库内/外的符号链接时一律 fail-closed（UNKNOWN reason=evidence）。安全上正确；若日后有人把证据目录做成合法链接会全部 UNKNOWN——属设计取舍，已 fail-closed，无需改。
- **[INFO-6] `agate/phase-cards/P4-implementation.md`（新增小节，"观测"条）**：写 `python3 agate/scripts/check-mvwu.py <task_dir>`。其他既有卡片的脚本调用同为此写法，且脚本调用面不在 `tests_filter` 平台中立要求之内（该要求针对 `tests_filter` 示例，已核对 P2 卡/architect/task-files 三处均写 `python -m pytest …` 形态、无裸 `python3`），故不构成缺陷，仅备忘。
- **[INFO-7] `--observe` 大仓库**：`_default_branch_base` 与 `_collect_range` 各为常数次 git 调用，区间提交数线性；未做万级提交压测（未构造），按算法分析无 N×M。

## 文档改动抽查（次要，约束 3）

- **插入位置 / 既有结构不破坏**：`P2-design.md` 卡新增小节位于既有 `dispatch_plan` 机器字段说明之后、"影响面梳理"之前；`P4-implementation.md` 卡新增"批级证据"小节位于"产出规格"之后、"新增文件核对表"之前；`architect.md` 新增小节位于"批次设计"检查清单之后、"返回给主 Agent"之前；`adr.md` 仅在开头新增"复审触发条件"节（**未删任何既有 ADR**，diff 纯新增）；`CONTEXT.md` 仅追加 5 行术语（既有 29 条术语无 `-` 行，diff 纯新增）；`role-system.md` 新增审查锚点节位于"子派发权限边界"之前；`P7-consistency.md` 检查清单追加第 6 条；`task-files.md` / `scripts/README.md` / `tests/README.md` 各为新增行。所有 diff 除 CHANGELOG 的占位句替换与测试文件一行注释外均无删除行。
- **无"机制已生效"式断言**：`role-system.md` 新节明写"其实际效果尚未做任何验证，不作有效性宣称"；`adr.md` "不设自动失效或阻断流程的机制"；P4 卡"记录不阻断 / UNKNOWN 不等价于 PASS"；`architect.md` "不新增 gate 校验"。
- **`tests_filter` 示例平台中立**：`P2-design.md` 卡示例 `python -m pytest ...`，并明确"不裸 python3 / 以 AGATE_PYTHON 探测为准"；`architect.md` 与 `task-files.md` 同。
- **DEBT0043**：`check-debt.py agate-workspace/debt/tech-debt.md` rc=0（schema 合法，字段齐备含 evidence/closure_criteria/source/created_at/task_id）；其 evidence 中 `check-gate.py::_gate_p2_dispatch_plan` 行号 `def 767` / `769-770`、`772-774`、`775-776`、调用点 `919` 与源码逐行核对吻合；**`check-gate.py` 零改动**（`git diff HEAD --stat` 无该文件），未修 `_gate_p2_dispatch_plan`，符合零内核。
- **一致性 / 测试**：`check-protocol-consistency.py` 0 ERROR（367 WARNING 为既有存量）；`test_check_mvwu.py` 109 passed。

## 建议登记的技术债

无需登记新 DEBT：MAJOR 缺陷可在本任务内 1-2 行收口，建议主 Agent 回派 implementer 修复（`_fmt_duration` 限长/捕获 + 输出循环 per-row 兜底 + 补 1 条单测），修后重跑 `test_check_mvwu.py`。若主 Agent 决定不修，则应登记为 DEBT（`category: technical`，`priority: low`，evidence: `agate/scripts/check-mvwu.py:136-144, 447-452`，复现：`duration_seconds` 写 4301 位数字后跑 `--observe`）。

## 待主 Agent / 人工决策项

- **MAJOR 是否本任务内修**：选项 A（推荐）回派 implementer 修 `_fmt_duration` + 输出循环兜底并补单测，成本极低、消除"每批恰一行"唯一已知违约点；选项 B 不修、登记 DEBT，approved 状态不变。评审结论 **不因此改判 rejected**（非 BLOCKER）。
- INFO-1（重复键冲突 → UNKNOWN）为可选加固，属语义变更，须先与 P1 口径对齐后再定，不建议在本任务扩范围。
