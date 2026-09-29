---
status: needs-revision
agent: protocol-alignment-review
reviewed_at: 2026-09-29
---

# SELF-GATE 评审：RM-AG0077 校验器健壮性批

> 评审方式：HEAD 版本与工作树逐字节/逐行为对照实验（`/tmp/tag0039-verify/`，未改动被评审文件）。
> 所有数字均为本机独立复现，未采信改动者数据。

## 结论

**可提交性：核心工程正确、可复现，但本批自设的验收锚未达成，且两处"语义等价/完成"声称与事实不符 → 判定 `needs-revision`（不阻断提交，但须先修正声称或补齐缺口并同步 roadmap 措辞）。**

阻断项（均为"声称 > 事实"，非代码错误）：

1. **子批 A 未达自设验收锚**：roadmap 声称"③ 子批 A 完成——10 处 CLI 级静默跳过加 `GATE SKIP:`"，而 RM-AG0077 验收锚写的是"23 个 `check-*.py` 的跳过分支**均**输出显式跳过原因"。本批只动了 6 个文件；同属"CLI 级、对象缺席即静默通过"的 **`check-p6-provenance.py`（无 P6 时 exit 0 零输出，且处于 `agate-next.py` 的 P6→P7 推进路径）、`check-pruning.py`（缺 P1 时 exit 2 零输出）、`check-frontmatter.py`（文件不存在时 exit 0 零输出，且**就在 roadmap 自列的 11 个静默脚本里**）** 三处未动。
2. **"逐行扫描与 `.*(?:X).*` 逐字等价"不成立**：`pytest.sh` 的 `name_errors` 在"同一行含 ≥2 个 `NameError: name ...`"时取**首个**匹配，旧正则在贪婪 `.*` 下取**末个**。影响低（非空性/分类不变），但该断言在代码注释与 README 中被写成了绝对等价。
3. **子批 B"放弃"的论证不足**：改动者只测了最宽的"行内出现即命中"变体（我复现为 **28** 个任务，非 27），未测**窄变体**（行首 + 可选 `**`/`>` 包裹）。窄变体 delta = **1**，且该唯一新增命中（`TAG0021`）是**真实 SCOPE+ 声明**，不是误报。DEBT0015 报的正是这个形态 ⇒ "净价值为负"的结论对最宽变体成立，但不能覆盖窄变体。

非阻断观察（见第 1、6 节）：新 formatter 在 **TMPDIR 不可写**时由"成功"变为 exit 1（HEAD 可跑通）；provenance 新逻辑对"有前导说明再跟 frontmatter"的文件**不再剥离** frontmatter。

## 逐条核实

### 声称 1：子批 D（formatter / E2BIG）——**成立（含一处新引入的可用性回退）**

| 核实点 | 独立证据 | 判定 |
|---|---|---|
| ① 真的是 6 个同一形态 | `grep` + 读取全文：5 个（`generic-junit-xml` / `generic-tap` / `go-test` / `pytest` / `vitest`）为 `OUTPUT="$(cat)"; export OUTPUT`；`generic-exit-only.sh` 同样 `export OUTPUT`（虽不读） | 成立 |
| ② 契约不变有依据 | `resolve_formatter()`（`agate_common.py:629`）优先 `$task_dir/.agate/formatters/`；**野外确有该形态文件**：`agate-workspace/tasks/TAG0037-install-package-model/.agate/formatters/pytest.sh`（且它自己也用 `mktemp`）。CLI 仍为 `bash <fmt> <exit_code>` + 输出走 stdin | 成立 |
| ③ 大输入不崩 | 16 MiB 输入 → 6/6 `exit 0`、输出合法 JSON 单行 | 成立 |
| ④ 小输入逐字节一致 | 6 formatter × 6 样本（pytest/go/vitest/tap/junit/plain）共 **36/36 `SAME`**（stdout 与 rc 全部逐字节相同） | 成立 |

E2BIG 机制自证：HEAD `generic-exit-only.sh` 在 **120 KB → exit 0**、**128 KB → exit 126**（`参数列表过长`），阈值恰为 `MAX_ARG_STRLEN = 131072 = 128 KiB`。故 roadmap 的"1.5 MB 触发"为真且**低估了触发面——任何 >128 KB 的输出即可触发**。

> **新发现（HEAD 可跑通、新代码失败）**：`TMPDIR` 不可写时 `mktemp` 失败 → `set -e` 中止 → formatter `exit 1`。实测：`TMPDIR=<只读目录>` 下 `HEAD pytest.sh → exit 0 / 552 B JSON`，`新 pytest.sh → exit 1 / 0 B`。这会经 `run_test_with_formatter` 回退 `_fallback_json(raw_output=全量)`，即**重新回到 A 类误判路径**（正是本批要消灭的故障）。本机 `AGENTS.md` 已登记"受限 harness 下 `/tmp` 只读"这类约束，故非纯理论。建议：mktemp 失败时回退到"不建临时文件"或把输出经 stdin 直连 python（`python3 -c ... <&0`），或在 README 明示 formatter 需可写 TMPDIR。

### 声称 2：连带发现 1（二次方正则）——**部分成立（退化属实且更严重；"等价"有反例）**

① **二次方属实，且比声称更严重**。关键前提是"**关键词缺席**才最慢"（命中即提前返回）：

| 单行尺寸 | 8 KB | 16 KB | 32 KB | 64 KB | 128 KB | 256 KB |
|---|---|---|---|---|---|---|
| `findall` 关键词缺席 | 0.117 s | 0.475 s | 1.915 s | 7.687 s | 30.53 s | 121.41 s |
| 每翻倍倍率 | — | 4.05× | 4.03× | 4.01× | 3.97× | 3.98× |

32 KB ≈ 1.92 s（与声称 2.1 s 一致）；按 ×49.4 外推 1.8 MB ≈ **5999 s ≈ 1.67 h**（与声称 1.8 h 一致）。更值得注意的是：**HEAD 在 E2BIG 阈值之下同样会挂死**——`HEAD pytest.sh` 喂 100 KB 单行无关键词耗时 **39.1 s**（40 KB → 6.3 s），即"输出未超 128 KB 也不能幸免"。

② **"逐行扫描与 MULTILINE 下 `.*(?:X).*` 整行匹配逐字等价"——找到反例**。

- 4 处语法/import 模式（`ImportError|ModuleNotFoundError`、`SyntaxError|IndentationError`、`syntax error|parse error`、`SyntaxError|ParseError|Unexpected token`）：20 万例差分 fuzz（含两行同命中、行首/行尾、跨行 `Import\nError`、CRLF、无尾换行）+ 定向用例 → **0 差异**。因旧模式等价于"整行 + `strip()`"，新模式为"逐行 + `strip()`"，两者确实等价。
- **`pytest.sh` 的 `name_errors` 不等价**：旧式 `.*NameError: name '([^']+)' is not defined.*` 的**贪婪 `.*` 吞到本行最后一个**匹配；新式 `re.search` 取**第一个**。最小反例：

  ```text
  x NameError: name 'myapp.a' is not defined y NameError: name 'x' is not defined
  ```

  | | `symbol` | `module` |
  |---|---|---|
  | 旧 | `x`（末个） | `''` |
  | 新 | `myapp.a`（首个） | `myapp` |

  影响评估：`check-tdd-red.py` 只消费 `len(name_errors)` 与 `module.startswith(project_module)`（`check-tdd-red.py:143-149`）；单 `NameError` 行是现实形态，两分支都落 B 类 `exit 0`，故**当前不改变任何退出码**。但把它写成"逐字等价"不准确，且 `README.md`（本次新增节）与 `pytest.sh` 注释都用了"语义等价/逐字等价"。**真正等价的最小改法是 `re.finditer` 三次**：`for m in re.finditer(r"NameError: name '([^']+)' is not defined", raw)`（旧式不含 `.*` 时 `findall` 即逐次匹配），或保留旧式语义用 `re.findall(r"NameError: name '([^']+)' is not defined", raw)` 后仍按同样方式 append。

③ **修复后线性属实**：新 `pytest.sh` 喂单行输入 200 KB → 0.028 s、400 KB → 0.036 s、800 KB → 0.051 s、**1.8 MB → 0.092 s**；多行 800 KB → 0.057 s。线性、且 16 MiB 输入 `exit 0`。

### 声称 3：连带发现 2（formatter 无超时）——**成立**

① HEAD 版本确认无 timeout：`git show HEAD:agate/scripts/agate_common.py` 的 `run_test_with_formatter` 中 formatter 的 `subprocess.run` **无 `timeout=` 参数**。成立。

② **超时语义与"formatter 失败"同源，未引入新分支/新 exit code**：`except subprocess.TimeoutExpired` 与既有 `except OSError` / `if fmt_proc.returncode != 0` 三条路径**都** `return _fallback_json(exit_code, output)`；差别仅多写一行 stderr。空/非法/≤0 的 `AGATE_FORMATTER_TIMEOUT` → 回落 120；合法正整数直达（含极大值，无上界钳制，可接受）。成立。

③ **超时确实能解开"永久卡死"**：构造 formatter 内 python 子进程（孙进程）`sleep 3600` 且继承 stdout 管道，设 `AGATE_FORMATTER_TIMEOUT=3` → `run_test_with_formatter` **3.01 s 返回**并给出降级 JSON（而非挂到 3600 s）。这是本修复的实际价值，已实证。

④ 默认 120 s 是否误杀正常慢 formatter：**否**。formatter 是纯文本后处理，实测 1.8 MB ≈ 0.092 s（含 bash 启动），比 120 s 宽裕三个数量级；且 `AGATE_FORMATTER_TIMEOUT` 可覆盖。唯一需注意：`AGATE_TDD_TIMEOUT` 默认同为 120 s，极端情况下单次 gate 最坏等待 120+120 s（非缺陷，属预期）。

### 声称 4：子批 A（静默跳过 ≈ 真空通过）——**部分成立（站点修复属实、BDD-10 例外属实、但覆盖不完整）**

① **逐个站点"修复前确实静默"**：全部经 `git diff` 的 `-U0` 上下文确认——新增的 `sys.stderr.write("GATE SKIP: ...")` 均**紧插在既有 `sys.exit(0)` 之前**，即原分支只有 `sys.exit(0)`。共 **10 处 / 6 文件**（changelog 1、debt 1、p6-format 2、routing 1、scope-resolved 1、state-transition 4），与"10 处"一致。

② **exit code 未变**：`git diff -U0 -- agate/scripts/ | grep -E "^[+-].*sys\.exit"` **零命中**（无任何 exit 行被增删）。新测试 `test_check_skip_announcements.py`（11 用例）自跑 **11 passed**，其中含"真通过时**不得**出现 `GATE SKIP:`"的负向对照。成立。

③ **`check-debt.py` 例外名副其实**——改动者是"发现并尊重契约"，**不是**"测试红了改测试"：
- `agate/tests/unit/test_agate_debt_check.py:296 test_bdd_10_no_file_or_no_yaml_block_is_noop` **明文**断言：无文件 / 空文件 / 旧格式纯正文 → `returncode == 0` **且 `result.output == ""`**（其文件头还注明"debt-check 5 处 `[ -z "$output" ]`：bdd_5 / bdd_10 / bdd_11"）。
- `git log` 显示该测试**未被本批触碰**（`git status --short` 该文件为空）；`check-debt.py` 的例外分支**只加了注释、无行为改动**。
- 判定：**例外成立**，且改动者给出的是"尊重既有契约 + 显式登记已知局限"，处理得当。

④ **有漏掉的同类站点（本批最关键的反例）**。以"CLI 级、校验对象缺席即静默通过"这一**改动者自己采用的口径**扫全部 `check-*.py`：

| 脚本 | 站点 | 缺席时的实测行为 | 是否本批覆盖 |
|---|---|---|---|
| `check-p6-provenance.py` | 无 `P6-acceptance.md` 的任务目录 | `exit 0`、**stderr 0 字节** | ❌ 未动 |
| `check-pruning.py` | 无 `P1-requirements.md` | `exit 2`、**stderr 0 字节** | ❌ 未动 |
| `check-frontmatter.py` | 目标文件不存在 | `exit 0`、**stderr 0 字节** | ❌ 未动（**在 roadmap 自列的 11 个静默脚本名单内**） |
| `check-maintainability.py` | git 通道不可用 | 有 `WARNING: ... 本轮跳过` | 本批前已有（无害） |
| `check-mvwu.py` | 目标目录不存在 | `return 2`（非静默） | 不适用 |
| `check-gate.py` | 无 CLI 级静默 `exit(0)` | 无参数 → usage + `exit 1` | 不适用 |

其中 `check-p6-provenance.py` 的缺席路径**真实可达**：`agate-next.py:63` 定义 `CHECK_PROVENANCE`，`:372` 用其判定 P6→P7 推进失败——"目录没有 P6 文件"与"P6 审计通过"在 `exit 0` 上不可区分。`check-frontmatter.py` 由 `pre-commit-gate.py:356` 按阶段调起。改动者自己在测试文件头承认"先前登记的 13 个 / 11 处"为脚本级高估、精确口径只覆盖 6 个脚本——**诚实的自我修正值得肯定，但 roadmap 的落地记录写成"子批 A 完成"与 RM-AG0077 的验收锚"跳过分支均输出显式跳过原因"直接冲突**。这正是本仓反复复发的"只修被报告的那一处"反模式的部分复发：修了 10 处（远好于 1 处），但宣称的口径是"全类"。

### 声称 5：子批 B（放宽 SCOPE+ 正则）——**部分成立（放弃最宽变体正确；但论证未覆盖窄变体，且"3/3 全误报"欠采样）**

① **27 这个数字**：我复现为 **28**（任务级 `tasks/*/*.md`、剥离 AGATE_CARD、跳过 dispatch-context/prompt/progress）：现行 `^\s*-?\s*\[SCOPE\+\]` 命中 **8** 个任务，"行内出现 `[SCOPE+]` 即命中"命中 **36** 个 → delta **28**。换用全部任务文件 glob 仍为 28。数字量级属实（±1 取决于扫描面），非实质错误。

② **"抽样 3/3 全是误报"欠采样——存在被放弃的"真声明"**。我把 delta 的 28 个任务逐条分类（否定/散文提及/测试断言 vs 声明节标题）：

- 绝大多数确为误报（`**无** [SCOPE+]`、`[SCOPE+]（非行首）不触发`、grep 说明、测试日志等），改动者的判断在**主体上是正确的**。
- **但存在真实声明形态**：`TAG0021-structured-layer/P2-design.md:379` 是
  ```markdown
  **[SCOPE+] 发现（供主 Agent 关注，不擅自扩大范围）**：
  - SCOPE+1：`agate/rules/{phases,dispatch,roles}.yaml` ...
  ```
  其后**逐条列举 SCOPE+1/2/3**；`TAG0021/P4-implementation.md` 亦有 `### [SCOPE+] 声明（实现期新发现…）`。`TAG0012`/`TAG0014`/`TAG0023` 为 `## [SCOPE+] 声明` 标题，`TAG0025/P2-design.md:80` 为 `### [SCOPE+] 发现：...` —— 这些是被现行行首正则漏掉的**标题/粗体包裹声明**。

③ **前提"行首非 `[` 形态"并不完全成立——应当区分"窄放宽"与"宽放宽"**：

| 变体 | 命中任务 | delta |
|---|---|---|
| 现行 `^\s*-?\s*\[SCOPE+\]` | 8 | — |
| 行首 + 可选 `**`/`__`/`>` 包裹 | 9 | **1**（`TAG0021`） |
| 行首 + Markdown 标题含标记 | 15 | 9 |
| 行内出现即命中（改动者所测） | 36 | 28 |

即：DEBT0015 报的 `**[SCOPE+]**` / `> [SCOPE+]` **恰是"窄变体"能覆盖的形态**，而改动者**只测了最宽的"行内任意位置"变体**并据此放弃整个子批。窄变体的唯一新增命中（`TAG0021`）是**真声明**而非误报 ⇒ "放宽必然产生大量误报、净价值为负"这一结论对宽变体成立、对**窄变体不成立**。

④ 用真实脚本逻辑跑窄放宽的后果（说明为何结论仍需谨慎）：`TAG0021` 的 P1 虽在 `:231` 有 `[SCOPE_RESOLVED: ...]`，但该标记被**反引号包裹**（`` `[SCOPE_RESOLVED: ...` ``），`SCOPE_RESOLVED_RE` 的 `^\s*-?\s*` 同样匹配不上，且 P1 frontmatter 无 `scope_resolved` ⇒ 窄放宽会使 `TAG0021` 由"静默通过"变为 `exit 1`。这**既可能是一次真检出**（其闭环标记本身不可机读），**也可能是一次假 FAIL**（该 SCOPE+ 已在 P4-review/P7 散文中处置）。两种解读都指向同一结论：**正确的修法很可能不是"放宽 `SCOPE_PLUS_RE` 单点"，而是同时收紧 `SCOPE_RESOLVED_RE` + 规定机读标记形态（或让 gate 校验 `scope_resolved` frontmatter 字段）**，否则单侧放宽会把"标记书写不机读"的存量任务集体判红。

**判定**：放弃**宽**放宽是正确决定（避免 28 个任务的噪声，且其中确含大量误报）；但"3/3 全误报"的抽样不足以支撑"子批 B 整体不可做"的结论，且 RM-AG0077 的验收锚"`SCOPE_PLUS_RE` 覆盖粗体/引用形态**或**早退有提示"——改动者靠子批 A 的"早退有提示"满足了后半句，前半句仍是**已知未闭合缺口**（应显式记为遗留而非"净价值为负"一笔带过）。

### 声称 6：子批 C（provenance 奇数 `---` 吞尾）——**成立**

① **原缺陷属实（构造实证）**：`---`(frontmatter 开) / … / `---`(闭) / 正文 / `---`(第三条，正文分隔线) / `- PASS BDD-99 ...`：

| 脚本 | 结果 |
|---|---|
| HEAD | `exit 0`（**漏检**尾部预判） |
| 新 | `GATE PROVENANCE: ... 含 1 处验收结论预判` → `exit 1`（正确检出） |

② **11 / 0 属实**：自有复现脚本对 `agate-workspace/tasks/*/*dispatch-context*.md`（**706 个**，与声称一致）套用两版剥离逻辑 → 卡片剥离后**奇数 `---` 文件 = 11 个**；`^\s*- (PASS|FAIL)` 命中文件数 **旧 1 / 新 1**，**判定发生变化的文件 = 0**。声称的三个数字全部复现。

③ **新逻辑边界合理**：无前导 `---` → 不剥离；`---` 在正文中间（`filtered[0] != "---"`）→ 不剥离；正常 frontmatter → 剥离；仅一个 `---` 或无闭合对 → **不剥离 + stderr 告警**（"宁可多审，不可吞正文"）；空文件 → 空。方向正确。

> **须登记的语义变化（非缺陷）**：1) 实测有 **115/706** 文件在两版下**剥离后的内容不同**——真实 dispatch-context 普遍在正文用 `---` 作分隔线（`689/706` 在顶部 frontmatter 对之外还含 `---`），旧逻辑会从正文第一条 `---` **吞到 EOF**；新逻辑恢复扫描，这正是修复目的（现存文件无预判命中，故"新增命中 0"与"扫描面显著变大"同时成立、并不矛盾）。2) 新逻辑对"**前导说明 + 其后才是 frontmatter**"的文件（实测 92 个文件首行是 `> **所有 P1-P8 阶段统一强制本文件存在**...` 而非 `---`）**不再剥离 frontmatter**，frontmatter 行进入审计区间。因 frontmatter 不含 `- PASS/FAIL` 行，实测无新增命中，但这是行为变化，建议在代码注释中写明"仅识别**首行** frontmatter"。

④ **是否削弱审计**：**否**。对以 `---` 开头的文件新逻辑扫描面 ≥ 旧逻辑（吞尾被消除）；对前导说明文件也只会**多扫**不会少扫。方向是单向增强。

### 声称 7：逐字节回归基线刷新——**先例属实；护栏仍有效，但只是"需留痕的绊线"而非"永不变更"**

① **`6d765a1` 先例核实为真**：`git show --stat 6d765a1` 显示**同一 commit** 同时改 `agate/scripts/check-gate.py`（+29/-…）与 `agate/tests/fixtures/tag0034_regression_baseline.json`（10 行），且 commit message 带 `self-gate-review: agate-workspace/tasks/TAG0035-gate-robustness/P4-protocol-alignment-review.md` trailer。先例引用准确。

② **是否掩盖了本该发现的问题**：本批的刷新**没有**掩盖问题。我独立核对了基线的两个受控文件：
- `check-state-transition.py`：4 处改动全为 `sys.stderr.write(...)` 新增，**无 exit code / 判据改动**；
- `check-gate.py`：改动仅在 `_check_roadmap_done` 的"列数异常"分支内**新增告警**，`continue` 与 `return None` 语义不变（与 `test_check_skip_announcements.py` 的"告警但不阻断"断言一致）。
且基线 `_note` **已同步记录**："2026-09-29（RM-AG0077 校验器健壮性批，直改未走 P0-P8；经 SELF-GATE protocol-alignment-review）：…两者均为**可观测性**改动（未改任何判据/exit code/转移规则），基线随同 commit 刷新（沿用 TAG0035 先例）"。故"零改动护栏"在本批中**起到了绊线作用并留下了带理由的刷新记录**。

③ **明确判断——护栏还有没有意义**：**有，但其语义必须正确定义为"任何字节变化都须显式解释并留痕的绊线"，而不是"这些文件永不改变"。**
- 测试文件自己的注释写的是"**长期不变量**"（`test_tag0034_zero_change.py:4-5`），但基线在其生命周期内已被刷新**至少两次**（`state-machine.md` 2026-09-10、`check-gate.py` TAG0035）。把"长期不变量"读成"永不变更"是**错的**——`phases.yaml`/`state-machine.md` 这类机制本体注定会演进；护栏真正守护的是"**变化必须可见、必须经审查**"。
- 它**不会**因"谁都能刷新"而彻底失效，原因是刷新有成本（必须改基线文件本身、必然出现在 diff 里、需写理由），而"静默改 gate 而不动基线"会**立即转红**。这就是绊线的价值。
- **但它的强制力确实只靠自觉**：`self-gate-review:` 仅是 commit-msg hook 的 WARNING（不拦截），且**没有任何机制校验"未改判据/exit code"这一声明**——本批的声明为真，是我**人工比对代码**才确认的。建议（择一即可显著加固）：
  1. 让基线刷新**必须携带** review 产物路径（把 `self-gate-review:` 从 WARNING 升为"改了基线文件时必填"，或 CI 里对基线 diff 要求同 commit 含 review 文件）；
  2. 或增加**行为级**护栏替代部分字节护栏（例如断言 gate 脚本在固定输入集合上的 exit code 矩阵不变），这样纯可观测性改动无需刷新基线，字节护栏只留 `phases.yaml` 等真正的长期不变量。

### 补充核实：README「两个必看的实现陷阱」小节（父 agent 追加范围）——**成立，两处措辞需收紧**

| 核实点 | 独立证据 | 判定 |
|---|---|---|
| ① 描述与代码一致 | `mktemp`+`trap`+`python3 - "$TMP"` 与 5 个 formatter 实际写法一致；`generic-exit-only.sh` 的例外（`cat > /dev/null`）README 在紧随的括号里**已显式carve out**；`AGATE_FORMATTER_TIMEOUT` 默认 120 s 与 `FORMATTER_TIMEOUT_DEFAULT = 120` 一致；"超时会降级为原始输出"与 `return _fallback_json(...)` 一致；文档未承诺任何代码没做的事 | 成立 |
| ② "正确写法"片段可跑 | 逐字复制到临时目录实跑：`echo hello` → 打印 `12`、rc 0；**2 MB 输入 → rc 0**（不触发 E2BIG）。片段中字面 `...` 是合法 Python `Ellipsis` 表达式语句，误复制也不报错 | 成立 |
| ③ 未把"兜底"说成"许可" | 原文"超时会降级为原始输出，**但那是兜底、不是许可**"——定性正确，无误导 | 成立 |

数字复核：`MAX_ARG_STRLEN` = 131072 B ✓（实测 120 KB 通过 / 128 KB E2BIG）；"1.5 MB 超限 11 倍" = 11.44×（十进制）✓；"32 KB 单行 2.1 s、翻倍 ×4、1.8 MB 外推 1.8 h" ✓（对应**关键词缺席**路径，我实测 32 KB = 1.92 s、256 KB = 121.4 s → 1.8 MB ≈ 1.67 h）。

需收紧的两处措辞（与声称 2 同源）：
1. README 写"改成**逐行扫描**即线性且**语义等价**（`.` 本就不跨 `\n`）"——对 4 个语法/import 模式成立，对 `pytest.sh` 的 `name_errors` **不成立**（首/末匹配差异，见声称 2②）。建议改为"逐行扫描即线性；**但注意贪婪 `.*X.*` 取的是本行末次匹配，逐行 `search` 取首次——需多次 `finditer` 才逐字等价**"。
2. "内置 formatter 现在都是这个写法"——严格说 5 个是，`generic-exit-only.sh` 不是（下一句括号已说明，属可接受的行文紧凑，若追求精确可改为"需要读输出的内置 formatter 现在都是这个写法"）。

另建议补一句**坑 ③**：`mktemp` 依赖可写 `TMPDIR`——受限沙箱（`/tmp` 只读）下 `mktemp` 失败会让 formatter `exit 1`，退回本节的 A 类误判路径（见声称 1 的 TMPDIR 实证）。

## 反例搜索

| # | 反例 | 证据 | 影响 |
|---|---|---|---|
| 1 | **"逐行扫描语义等价"不成立于 `name_errors`** | 单行含两个 `NameError: name ...` 时：旧 `symbol='x'`、新 `symbol='myapp.a'`（首个 vs 末个） | 低（当前不改任何 exit code，仅 `module` 前缀判定可能不同 → 影响"是否识别为项目内符号"的**提示文案**，两者同为 B 类 `exit 0`）。但使"逐字等价"声称不成立 |
| 2 | **窄放宽 SCOPE+ 的"唯一新增命中"是真声明，不是误报** | `TAG0021/P2-design.md:379` `**[SCOPE+] 发现…**` 后逐条列 SCOPE+1/2/3；`P4-implementation.md` `### [SCOPE+] 声明` | 使"放宽必然大量误报 ⇒ 净价值为负"的**全称**结论不成立；放弃**宽**变体仍是对的，但窄变体（delta=1）从未被评估 |
| 3 | **`TAG0021` 的 `[SCOPE_RESOLVED]` 标记自身不可机读** | P1 `:231` 为 `` `[SCOPE_RESOLVED: ...]` ``（反引号包裹），不匹配 `^\s*-?\s*\[SCOPE_RESOLVED` | 说明"行首标记"这一族判据两侧都脆；单侧放宽会把这类任务判红 → 正确修法需双侧协同 |
| 4 | **子批 A 覆盖不完整** | `check-p6-provenance.py`（无 P6 → exit 0 / stderr 0 B；在 `agate-next.py` P6→P7 路径上）、`check-pruning.py`（缺 P1 → exit 2 / stderr 0 B）、`check-frontmatter.py`（缺文件 → exit 0 / stderr 0 B，且在 roadmap 自列 11 名单内） | 与 RM-AG0077 验收锚"跳过分支**均**输出显式原因"冲突；`check-p6-provenance` 是可达的真实真空通过 |
| 5 | **新 formatter 引入 TMPDIR 可写依赖** | `TMPDIR=<只读>`：HEAD `exit 0`/552 B JSON → 新 `exit 1`/0 B | `mktemp` 失败 → `set -e` 中止 → 回退 `raw_output` → **正是本批要消灭的 A 类误判路径**在受限沙箱下复活 |
| 6 | **护栏刷新会掩盖问题吗** | 本批为**否**：`_note` 已记录、两文件改动经我独立核对确认"无判据/exit code 变化" | 护栏未被滥用；但"未改判据"这一声明**无机制校验**，全靠人工，属结构性弱点 |

## 真空通过自检

本节说明报告中每个 exit code / 数字在**何种前提下**才构成证据，以及是否存在"输入不存在与输入合规输出相同"的混淆。

| 引用 | 前提（才成立） | 是否可能"真空通过" |
|---|---|---|
| HEAD formatter `exit 126` @128 KB | stdin 真的提供了 ≥131072 B 且**经 env 传递**；已核对 stderr 为 `参数列表过长` 而非其他错误 | 否（stderr 有具体 E2BIG 文本 + 阈值两侧对照 120 KB/128 KB） |
| 新 formatter 16 MiB → `exit 0` | 输出须为合法 JSON 且字段有内容；已核 stdout 非空（114–131 B）与 `rc=0` | 否（同时断言了 stdout 形态） |
| `36/36 SAME` 小输入逐字节一致 | 两侧**都**须真正产出输出；已同时比对 stdout 与 rc（否则"都失败"也会 SAME） | 否（rc 亦比对；样本含 6 类真实输出） |
| 二次方 4× 倍率 | 须固定"关键词缺席"这一最慢路径，且测量为同一正则同一解释器 | 否（尺寸阶梯单调、倍率稳定 3.97–4.05） |
| 新逻辑线性 (1.8 MB→0.092 s) | 须确认 python 真的读到了全部输入（而非提前退出） | 否（同一文件在旧逻辑下会跑数十分钟，说明输入确实完整到达） |
| 10 处 `GATE SKIP` | 须确认是**新增**且插在既有 `sys.exit(0)` 之前；已用 `-U0` diff 上下文核对 | 否（`git diff` 明确显示为 `+` 行，且 `exit` 行零增删） |
| BDD-10 例外成立 | 须确认测试**未被本批改动**且断言"无输出"；已核 `git status` 该文件为空 + 读取断言原文 | 否（"无输出"是**显式断言**，不是"没看到输出"） |
| `check-*` 漏站点（provenance/pruning/frontmatter） | 我引用的 `exit 0/2` 是**对象缺席**场景，非"对象存在且合规" | **这正是"真空通过"本身**：`check-p6-provenance.py /tmp/nope-dir → exit 0/0 B` 与"P6 审计通过"在退出码与输出上**完全相同**——即本次评审发现的就是这种不可区分性，非评审方法的疏漏 |
| provenance 706 / 11 / 0 | 706 须等于 `tasks/*/*dispatch-context*.md` 口径（已验证该 glob 恰为 706；`**/*` 为 738，差别在 glob 深度） | 否（三数字均由同一脚本、同一剥离函数复现） |
| `check-p6-provenance` 构造用例 HEAD `exit 0` / 新 `exit 1` | 须确证 HEAD 漏检**不是因为**输入未送达 | 否（同一输入同一路径，仅剥离逻辑不同；新版本检出 1 处） |
| 窄放宽 delta=1 / 宽放宽 delta=28 | 须剥离 AGATE_CARD 并跳过 dispatch-context/prompt/progress，与脚本同口径 | 否（分类时逐条回读了命中行原文） |
| README 片段可跑 | 须真在临时目录执行，非目视检查 | 否（实跑 rc=0，含 2 MB 输入） |

## 遗留问题 / 建议

1. **【阻断项 1】补齐或改口子批 A**：`check-p6-provenance.py`（无 P6 时）、`check-pruning.py`（缺 P1 时）、`check-frontmatter.py`（缺文件时）三处至少应加 `GATE SKIP:`；若判定 `check-frontmatter.py` 的"非目标文件 → exit 0"是**有意契约**，则须把它从 roadmap 自列的"11 个静默脚本"名单中**移出并注明**。同步修正 roadmap "子批 A 完成" 的措辞为"覆盖 6/至少 9 个脚本，余下 N 处登记为遗留"。
2. **【阻断项 2】修正"逐字等价"表述**（`README.md` 新增节 + `pytest.sh` 注释）：`name_errors` 首/末匹配不同。最小修法是把该段改回 `re.finditer` 循环（逐次匹配即天然等价），或把注释降级为"对 4 类语法/import 模式逐字等价；`name_errors` 改为首个匹配（旧为末个）"。
3. **【阻断项 3】子批 B 的结论须收窄**：把"放宽会命中 27 个存量任务、抽样 3/3 全误报 ⇒ 净价值为负"改为"**行内任意位置**放宽 delta=28、主体为误报 ⇒ 放弃该变体；**行首 + 粗体/引用包裹**变体 delta=1、但会与 `SCOPE_RESOLVED_RE` 的非机读标记叠加导致存量判红 ⇒ 暂不单独放宽，登记为遗留并建议**双侧协同修法**"。删除"3/3"这类小样本的总体化表述。
4. **【建议】处理 TMPDIR 依赖**：formatter 的 `mktemp` 在只读 `/tmp` 沙箱下会 `exit 1` 并退回 A 类误判路径。修法可选：`mktemp` 失败时降级为"不建临时文件、经 stdin 直连 python"，或改用 `python3 -c '...' <&0` 形态彻底去掉临时文件（同时也就无需 `trap`）。至少应在 `README.md` 的陷阱节补一句前置条件。
5. **【建议】加固基线护栏的强制力**（详见声称 7③）：把"改了基线文件必须在同 commit 带 review 产物"做成可校验判据（CI 或 commit-msg 由 WARNING 升为条件阻断），或引入行为级 exit-code 矩阵测试，让纯可观测性改动不必刷新字节基线。
6. **【建议】provenance 注释补一句**："仅识别**首行** frontmatter"——实测 92 个存量 dispatch-context 以 `> **...**` 说明行开头，其 frontmatter 在新逻辑下不再被剥离（当前无新增命中，但语义已变）。
7. **【建议】`_formatter_timeout` 加一个上界钳制或告警**：当前接受任意大整数（如 `999999999999999999999`），会重新引入"事实上的无超时"。可加 `min(val, 3600)` 或对超大值写 WARNING。

## 附：本报告使用的复现命令（可独立重跑）

```bash
# E2BIG 阈值两侧对照（HEAD 版本）
git show HEAD:agate/assets/formatters/generic-exit-only.sh > /tmp/head-g.sh
python3 -c "import sys;sys.stdout.write('x'*131072)" | bash /tmp/head-g.sh 1; echo "exit=$?"   # 126
python3 -c "import sys;sys.stdout.write('x'*122880)" | bash /tmp/head-g.sh 1; echo "exit=$?"   # 0

# 二次方尺寸阶梯（关键词缺席 = 最慢路径）
python3 - <<'EOF'
import re, time
pat = re.compile(r".*(?:ImportError|ModuleNotFoundError).*")
for n in (8000,16000,32000,64000,128000,256000):
    s = "a"*n; t0=time.perf_counter(); pat.findall(s)
    print(n, round(time.perf_counter()-t0,4))
EOF

# 小输入逐字节回归（HEAD vs 工作树，6 formatter）
for f in generic-exit-only generic-junit-xml generic-tap go-test pytest vitest; do
  a=$(printf 'ok 1\nnot ok 2\n' | bash <(git show HEAD:agate/assets/formatters/$f.sh) 1)
  b=$(printf 'ok 1\nnot ok 2\n' | bash agate/assets/formatters/$f.sh 1)
  [ "$a" = "$b" ] && echo "$f SAME" || echo "$f DIFF"
done
```
