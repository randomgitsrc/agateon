---
status: needs-revision
agent: protocol-alignment-review
reviewed_at: 2026-09-29
---
# SELF-GATE 评审：TAG0041 平台适配层卫生

## 结论

**不可按现状提交**（needs-revision）——阻断项 3 条：① `check-gate.py P8` 新增检查**按 CWD 而非 `task_dir` 定位仓库**，同时产出**假阳性**与**假阴性**各一组（已实测复现），且这与同函数内既有 DEBT0020 的明确教训直接冲突；② RM-AG0076 的核心断言「启用 agent-team 会使 preset 工具映射**整体失效**」**与上游原文相反**（上游 README 第 108 行「已知限制」明文写 preset 作用域挂载的子代理控件**不被**顶层组合包替换），据此得出的「无机制可写」结论**不成立**；③ 平台文档新增「`/tmp` 不可写」与 `~/.dsh/env.md` 及本机实测**相反**，而这条正是该节「为什么必须在项目树内落产物」的**唯一理由**。

A/D/E 三条基本成立（含 D 的护栏退化判断，见下），B 部分成立（数字属实，但有两处溯源不足与一处措辞超出证据）。

**评审期间本批文件仍在被并发编辑**（`check-gate.py` 17:48、`platform-notes.md` 17:54、`test_t41_platform_hygiene.py` 18:01；评审开始时的 diff 与结束时不同，期间还新增了 `.gitignore` 与 `dispatch-prompt.md` 两处改动）。本报告对以下版本负责：

| 文件 | sha256(前 16) | bytes | mtime |
|---|---|---|---|
| `agate/scripts/check-gate.py` | `b79e8bb526bc2c1c` | 78730 | 2026-09-29 17:48:30 |
| `agate/tests/unit/test_t41_platform_hygiene.py` | `c489ad6d44a24b67` | 6387 | 2026-09-29 18:01:03 |
| `agate/tests/fixtures/tag0034_regression_baseline.json` | `785a8ed952ff2a4b` | 2335 | 2026-09-29 17:48:45 |
| `agate/platform-notes.md` | `071db526b4238523` | 39880 | 2026-09-29 17:54:57 |

（基线 sha 与 `check-gate.py` 当前值 **MATCH**，BDD-39 当场为绿——但见 D 节。）

---

## 逐条核实

### A. 临时产物约定（RM-AG0075）— **部分成立**

#### A-1 ✅ 成立：两条 WARNING 的基本组合行为正确

自建 git 仓库跑真实 CLI（`python3 agate/scripts/check-gate.py P8 task`，`cwd=` 仓库根），四种组合逐项实测：

| 目录 | `.gitignore` | 收集模式文件名 | (a) 未忽略告警 | (b) 收集模式告警 |
|---|---|---|---|---|
| 存在 | 有 | 无 | 不出现 ✓ | 不出现 ✓ |
| 存在 | 有 | 有 | 不出现 ✓ | **出现 ✓** |
| 存在 | 无 | 无 | **出现 ✓** | 不出现 ✓ |
| 不存在 | — | — | 不出现 ✓ | 不出现 ✓ |

- **不阻断属实**：所有分支均落到 `gate_p8` 末尾 `return 2`（"脚本化检查通过，主 Agent 自判"语义）。我核对了 `gate_p8` 全部 `return 1` 点（第 11/15/37 行三处，均为 `bump_type` / `debt_check` / roadmap-done），新增代码**不在任何 return 路径上**——WARNING-only 的声称成立。
- **`git check-ignore -q` 退出码语义正确**：exit 0 = 被忽略，exit 1 = 未被忽略（且 `-q` 无输出）。代码用 `if rc_ig != 0` 判"未被忽略"，方向正确。
- **`AGATE_TMP_DIR` 覆盖真的生效**：`AGATE_TMP_DIR=scratch-pad` 时正确改扫自定义目录并出告警。
- **2000 文件上界**：初版代码（我评审开始时读到的版本）**会漏报**——`_scanned > 2000` 后 break 且**静默**，把所有文件都命名为 `aaa*.mjs`、仅最后一个命中时无提示。当前版本已修好：改为 `scanned >= SCAN_CAP` + `truncated` 标志，并在 `hits` 为空但截断时**额外输出"仅扫描了前 2000 个（未发现收集模式文件名，但不能断定全部）"**。我实测 2600 个干净文件 → 该提示出现 ✓；2501 文件 + 命中项 → 告警带"（仅扫了前 2000 个文件，未扫全）" ✓。**这条属于"声称有检查但实际没检查"的一个已修实例**，方向上正确。

#### A-2 ❌ 不成立（阻断项 ①）：检查按 CWD 定位仓库 → 假阳性 + 假阴性并存

`_git(["rev-parse", "--show-toplevel"])` 与 `_git(["check-ignore", "-q", tmp_rel])` **均未传 `cwd`**，`run_git` 默认 `cwd=None` ⇒ 走**进程 CWD**；而 `os.path.isdir` 用的是 `repo_root`（CWD 的 toplevel）。三者中前两者依赖 CWD、第三者与 `task_dir` 脱钩，于是：

**假阳性**（目录确实被忽略却报"未被忽略"）——`check-ignore` 的路径参数是**相对 CWD** 解析，而忽略规则匹配的是"从仓库根到该路径"的**相对仓库根的路径**。CWD 在子目录时两者不一致：

```
仓库根/.gitignore:  .agate-tmp/      （无前导斜杠，子目录同名目录本应也匹配）
仓库根/.agate-tmp/ 存在且已被忽略
$ cd sub && git check-ignore -q .agate-tmp   →  exit 1   ← 被当成"未忽略"
```

端到端复现（真实 gate CLI，`task_dir` 用绝对路径传入）：

```
### RUN FROM REPO ROOT ###     → 0 条告警（正确）
### RUN FROM SUBDIR ###        → GATE P8 WARNING: .agate-tmp/ 存在但**未被 .gitignore 忽略**…
```

**假阴性**（目录确实未被忽略却静默放行）——反向构造：根 `.agate-tmp/` 未被忽略（内含 `creds.env`），子目录的 `.agate-tmp/` 被忽略、CWD 在子目录：

```
### from ROOT (正确：应告警) ###   → 1
### from sub/ (真实未忽略) ###    → 0   ← 静默漏报
```

**跨仓库假阴性**（最严重形态）：CWD 在仓库 B、`task_dir` 在仓库 A ⇒ 检查的是 **B 的** `.agate-tmp`，对 A 的真实未忽略目录**完全无感**：

```
### gate run from repo B, task_dir in repo A ###  → 0（A 中确有未被忽略的 .agate-tmp/creds.env）
### from repo A ###                               → 1
```

**为什么这是本批的实质缺陷而不是吹毛求疵**：① 该检查的**声明目的**是防"release 的 `git add -A` 把明文凭证提交"，而 `git add -A` 作用于**它自己所在仓库**——用 CWD 判定恰好是最坏选择；② **同一函数、相邻代码已有明确教训**——`check-gate.py:1414` 注释白纸黑字写着「DEBT0020：roadmap_path 按**仓库根锚定**（而非 CWD 相对拼接），非仓库根 CWD 下仍能正确定位（BDD-22）」，新代码在**同一个 `gate_p8` 里、上方 80 行处**违反了这条已确立的自家规则；③ 现有 5 个测试**全部在 `cwd=repo` 下跑**，结构性无法发现该缺陷（我用 `cd sub` 一条命令就复现了）。

**修法**（两处，都很小）：`_git([...], cwd=repo_root)`（或复用 `agate_common.run_git` 的 `clean_location_env` 语义），且 `check-ignore` 传**仓库根锚定的绝对路径** `os.path.join(repo_root_out, tmp_rel)`——我实测绝对路径形式在任意 CWD 下都返回正确值。

#### A-3 ✅ 成立：不误报既有项目（本仓与存量项目实测）

- **agateon 自己**：评审开始时**无** `.agate-tmp/` 目录，`.gitignore` 也不含该行 ⇒ 检查**不触发**（无噪声）。⚠️ 但评审末尾并发改动给 `.gitignore` 加上了 `.agate-tmp/`（并自陈理由"协议定义者自己不遵守，会让该约定看起来像无消费方的声明"）——该补充是合理的，且**它使 A-2 的假阳性更值得修**（一旦有人真用该目录，CWD 一变就误报）。
- **存量项目扫描**：`~/oclab/{agateon,deepseek-harness,md2docx,peekview,skills-lab,skills-lab-private}` 六个 git 仓库**全部无** `.agate-tmp/` ⇒ 新增检查对存量**零噪声**。「仅对采用约定的项目生效」的声称**成立**（在 CWD=仓库根的前提下）。
- 需要指出：peekview 的 `.gitignore` **现在已有** `.agate-tmp/`（且是 2026-09-29 加的，注释"禁止入库"），所以"该目录存在却未被忽略"的历史风险**在该项目已被项目侧自愈**；本仓 likewise。

#### A-4 ✅ 成立：P4「基础设施隔离」确实是两层

读了 `agate/phase-cards/P4-implementation.md:155-161` 原文：

> **基础设施隔离（并行时强制）**：… 「临时文件：各 subagent 写入 `P4-implementation/{pkg}/` 独立目录」

与 `.agate-tmp/` 的区分**不是我为了自圆其说编的**——P4 卡管的是**批内产出隔离**（落点在任务产出目录 `tasks/{Txxx}/P4-implementation/{pkg}/`，**要入库、要可审计**），新节管的是**scratch 落点**（`.agate-tmp/`，**不入库**）。platform-notes 第 190-198 行的两层表**准确**，且额外补了"P4 的 per-pkg 隔离理由在 scratch 下同样适用（否则两个并行 subagent 在同一 scratch 互相覆盖）"——这是有价值的澄清而非重复。**成立。**

#### A-5 ✅ 成立（有一处小瑕疵）：忽略片段模板可用

`assets/templates/gitignore-fragment.txt` 第 19 行就是可直接粘贴的 `.agate-tmp/`，我实测 `echo '.agate-tmp/' > .gitignore` 后 `git check-ignore -q .agate-tmp` → exit 0 ✓（目录存在时）。

⚠️ **瑕疵**：模板第 15 行给的自查命令 `git check-ignore -q .agate-tmp && echo ok` 在**目录尚不存在时必然失败**（我实测：目录不存在 + 规则正确 → `check-ignore` exit 1，用户会误以为"没配上"）。而"粘贴忽略片段"的场景恰好在目录存在**之前**。建议自查命令改为 `git check-ignore -q .agate-tmp/`（带尾斜杠，**目录不存在时也返回 0**——我实测确认这是 git 的路径不存在语义）或 `git check-ignore -v --no-index .agate-tmp`。

#### A-6 ❌ **落点部分找错**（用户问题 5）：主风险站点在协议之外，且 `git add -A` 在本仓不存在

**同类站点全量搜索**（`agate/` 全域 `git add -A` / `--all` / `git add .`）：

- `agate/scripts/`、`agate/phase-cards/`、`agate/assets/` 下**没有任何** `git add -A` / `git add --all` / `git add .`（命中的 5 处全是**叙述该风险的文字**：`check-gate.py` 注释与告警串、`gitignore-fragment.txt`、`platform-notes.md`、测试注释）。P8 卡唯一的 `git add` 是**精确路径**：`git add {AGATE_WORKSPACE}/tasks/{Txxx}/`（第 14 行）。
- 真实的全量暂存在**项目侧**：`~/oclab/peekview/Makefile:265` 的 `git add -A`（`bump-version` 的 Step 4），另有 `:318`、`:389`。本项目侧 `-A` 就是 RM-AG0075 声称的"stage 158 条"发生处。
- **RM-AG0077 第 ⑤ 项早已把归属拆对了**（原文：「`make bump-version` 是**项目自有** target（agateon 无 Makefile、无该模板），其 `git add -A` 属项目侧；**agateon 侧**应做的是 P8 卡补"提交前暂存面审查"要求 + 交付 `.gitignore` 模板预置」）。**本批交付了模板（后半），但没交付"P8 卡补提交前暂存面审查（前半）"**——我在 `agate/phase-cards/P8-release.md` 与全部 `assets/execution-roles/` 下检索「暂存面」**命中 0**（P8 卡只有既有第 77-78 行的"暂存区有 version/CHANGELOG 变更"，那是版本存在性检查、不是"暂存面有无意外文件"的审查）。而 P8 READY 收尾检查单里也**没有** `.agate-tmp/` 条目（`sed -n '/## READY 收尾检查/,$p' | grep -c agate-tmp` = **0**）——四项约定里的 ④「清理时点由 P8 卡检查单承载」**只在 P8 卡第 13 行有一句指针**，收尾**检查单本体未加项**。

**判断**：把检查放进 `check-gate.py P8` **不算完全找错落点**（P8 是发布前最后一道机械门，且新增的是 WARNING-only，成本低），但**落点不完整**——真正会发生 `git add -A` 的是项目侧命令，协议侧能做的是 ① P8 卡"提交前暂存面审查"（RM-AG0077 ⑤ 已承诺却未交付）② 收尾检查单加 `.agate-tmp/` 清理项（约定 ④ 自陈的承载处却未落）。建议补齐这两处，否则约定 ④ 与 RM-AG0077 ⑤ 都是**声称有、实际无**。

#### A-7 ⚠️ 文档内部有一处措辞不一致

- `roadmap.md`（RM-AG0075 落地段）写：「四项约定**均可机械校验**」。
- `platform-notes.md` 写：「**②③ 由 `check-gate.py P8` 机械校验，① 是它们共同依据的常量，④ 由 P8 卡收尾检查单承载**」。

**两者矛盾**：roadmap 的"四项均可机械校验"与 platform-notes 的"①是常量、④靠检查单（非脚本判据）"直接冲突。platform-notes 的表述**更准确**（① 是事实约定、不是校验项；④ 自陈"非脚本判据"），roadmap 那句是**夸大**。而 ④ 的承载处（P8 收尾检查单）**实际也没加**（见 A-6）⇒ ④ 目前**既非机械校验、也无检查单条目**。

---

### B. 长驻服务生命周期（RM-AG0075）— **部分成立**

#### B-1 ✅ 成立：`env.md` 引用准确，且**保留了限定**

`~/.dsh/env.md` 第 48 行原文（逐字）：

> **DSH 的 bash 工具命令/后台 job 结束时回收其派生的整个进程树**（**DSH 专属行为**；其他 agent 环境是否有同样回收**未经验证，勿假设通用**）（2026-09-03 实测：`python3 -m http.server` 在 job 内 HTTP 200，job 结束进程/端口同时消失）：`&`/`nohup`/`setsid` detach 均不保活，与普通 shell 不同。长驻服务必须挂在**长驻后台 job + `sleep` 托底**（如 `( make debug-start; sleep 3600 )` 挂后台 job），job 结束即清理。影响：任何跨命令常驻进程（debug server、MCP server、mock 服务）都需此方式，且 **job kill 即等价进程清理**。

对照 `platform-notes.md:203`：「**事实（DSH 实测，权威源 `~/.dsh/env.md`「已知环境限制或坑」）**：… **其他平台是否有同样回收未经验证，勿假设通用**」。

- 「回收整个进程树」「`&`/`nohup`/`setsid` 均不保活」「job kill = 进程清理」**逐字一致** ✓
- **限定被完整保留**（"未经验证，勿假设通用"写进了文档）✓ ——**没有把推断当实测**。
- ⚠️ 一处**轻微过度外推**：`env.md` 标题就写明这是「**DSH 专属行为**」，而新节标题却是「**受限 harness 通用约束**」并把适用范围扩到「**所有**默认限制写权限的 agent 平台（DSH `workspace-write`、Codex `-s workspace-write` 等）」——进程回收这条**只有 DSH 有实测**，Codex 侧**无任何证据**。文档正文保留了限定（好），但**节的标题与开篇适用范围句**比证据宽。建议标题收窄为"受限 harness 通用约束（进程回收部分 DSH 实测）"或在节首把两条事实的证据等级分开标注。

#### B-2 ✅ 数字属实：「7200 → 43200 s 仍被跨越 4 次」

`grep` 逐条核对 `orchestrator-log.md`，**次数与时长完全属实**：

| 次 | 行 | 时长递进 | 原话要点 |
|---|---|---|---|
| 1 | 20 | → **7200s**（`bash-745`） | 评审期间掉线，`:8888` 无监听 |
| 2 | 50 | → **14400s**（`bash-1115`） | rev2 期间再掉线；rev2 subagent 自行 `make debug-start` 恢复 |
| 3 | 161 | → **28800s**（`bash-1880`） | 「前两次分别 7200s / 14400s 均不够」 |
| 4 | 403/408 | → **43200s**（`bash-2858`） | 「**这是本任务第 4 次同因掉线**，托底时长逐次加长（7200→14400→28800→43200s）」 |

第 408 行的自陈与 `platform-notes.md:207` 的「逐次加长 **7200 → 14400 → 28800 → 43200 s（12 h）**，仍被跨越 **4 次**」**逐字吻合**。日志还有**第 5 次**（第 526 行，收尾阶段；这是"服务跟随调用"机制而非"托底到期"），文档写「4 次」指的是**托底被跨越**的次数，**口径正确**（roadmap 里写「4-5 次掉线」则把两种都算上了——两处口径不同但各自内部自洽）。

#### B-3 ❌ **溯源错误 + 措辞超出证据**（阻断项 ②的次要项）

**(a) 「pidfile 有值而端口无监听」确有据，但文档标错了出处。** `platform-notes.md:209` 写「出处：**某项目 `AGENTS.md`** 记录的实测『`/tmp/<svc>.pid` 有值但 `ss -ltn` 无监听』」。实际原文在 `~/oclab/peekview/AGENTS.md:126`：

> 查证：`/tmp/peekview-debug.pid` 有值但 `ss -ltn` 无 8888 监听。

**出处正确** ✓。但同句后半「另有任务记录『per-call tmpfs 下 pidfile 根本不可见 ⇒ `debug-stop` 看不到进程』」把两件**不同的事**并列，容易读成同一条证据——后者在 `orchestrator-log.md:526` 的原文是「**`make debug-stop` 报"服务已停止"但端口仍在监听**；真正持有者是挂托底的 keepalive job；且 `/tmp` 在本沙箱为 per-call tmpfs，pidfile 不可见」。即：**"pidfile 有值"与"pidfile 不可见"是相反的现象**（前者 = 陈旧 pidfile 未被清理；后者 = 跨调用看不到文件）。作为"不要信 pidfile"的论据**两者都支持结论**，但文档把相反现象并置而未说明区别，属于**证据表述含混**（非造假）。

**(b) 「每次白跑一整轮」是**过度概括**——证据只有 1 次、且不是"白跑"而是"自行恢复"。** `platform-notes.md:207` 与 `P5-verification.md:128` 都写「每次都表现为 subagent 拿到 `ConnectTimeout` / `FATAL: 调试服务未运行`，**白跑一整轮**」。核实：

- `FATAL: 调试服务未运行` 在 `orchestrator-log.md` 中**出现 0 次**（`grep -c` = 0）；该串的真实出处是 `~/oclab/peekview/AGENTS.md:126`（"下一条调用必然连不上：seed 报 `ConnectTimeout`、`make debug-test` 报 `✗ FATAL: 调试服务未运行`"）——即 **AGENTS.md 的一般性陈述**，不是本任务 4 次掉线的实测记录。
- `ConnectTimeout` 在日志中**仅 1 次**（第 162 行），且是复盘里的**预期描述**（"掉线时 subagent **会**拿到 ConnectTimeout"——将来时，非实测）。
- 「白跑」在日志中出现 2 次，**都与掉线无关**（第 383、434 行讲 E2E 环境陷阱与派发自测教训）。
- 4 次掉线的**实际后果**：第 2 次明确写「rev2 subagent **自行检测到停机并用 `make debug-start` + `make debug-seed` 恢复**」（**没白跑**）；第 4 次明确写「**对本阶段无影响**（P5 已完成、6 条命令均在掉线前跑完）」（**没白跑**）；第 1、3 次是评审期/执行期被发现并重启（未记录白跑）。
- 第 162 行确实有「浪费一整轮」的说法，但那是主 Agent 对**风险的预期**，不是已发生的记录。

⇒ 「**每次**都表现为 … **白跑一整轮**」在"每次"与"白跑"两个词上都**超出证据**。这是本批最接近"声称 > 事实"的一处（其余数字均属实）。建议改为"掉线本身无数据损失（subagent 可自行恢复），但会造成诊断与重启成本；预期失效形态是 `ConnectTimeout`"。

#### B-4 ⚠️ 四步做法**部分可执行**——第 3 步缺"启动命令从哪来"的答案

四步中：

1. **单一责任方** ✅ 可执行——已有机制（P5 卡「环境准备职责边界」+ `dispatch-protocol.md`「verification_env 失败处理协议」），且**确实被 P5 卡引用**（P5 卡第 128 行新增指针）⇒ 验收锚"被判据引用"**成立**。
2. **每次使用前探活** ✅ 可执行——给了具体判据（`curl -sf <health>` / `ss -ltn`）而非抽象原则，并给了**负面判据**（不是 pidfile 存在）。这是四步里质量最高的一步。
3. **掉线即重启** ⚠️ **正确但信息不全**——文档写"探活失败 → 重启 → 复验"，**但没有回答"重启用什么命令、从哪知道"**。核实证据：第 2 次掉线的恢复靠 `make debug-start` + `make debug-seed`（`orchestrator-log.md:50`），而这两个 target **是 peekview 项目自有的**（`peekview/Makefile`）；`agateon` 本身**无 Makefile**。协议文档既未指明"启动/种子命令应声明在何处"（P0-brief 的 `debug_env` 字段是**已有**载体，但新节只写了"subagent 不自行启动"，**没说这两条命令要写进 `debug_env`**），也未在四步里给出"从 dispatch-context / P0-brief `debug_env` 取启动命令"的指向。⇒ 这一步目前**依赖读者自行知道启动命令**，属"正确但不可操作"的缺口。**建议**：第 3 步补一句"启动/种子命令由 `debug_env` 声明（P0-brief），掉线恢复照此执行"。
4. **收尾即清理** ✅ 可执行——`job kill = 进程清理`有 `env.md` 明文与日志第 526 行实证（终止 `bash-2858` 后 `ss -ltn` 无 8888）✓。

#### B-5 ⚠️ `env.md` 与新增文档在 `/tmp` 上**互相矛盾**（阻断项 ③）

- `~/.dsh/env.md:66`（文件写权限表）：`| /tmp | ✅ 可写 | 调试数据/日志/PID（如 peekview-debug 全套） | — |`
- `~/.dsh/env.md` 同表下方说明：「可写范围按**当前工作区**配置（workspace-write 含当前 repo + `~/.local/share` + `~/Downloads`），**不同工作区不同**」
- 新增 `platform-notes.md:173`：「工作区外**含 `/tmp` 不可写**」
- 新增 `dispatch-prompt.md`：「⚠️ **不要用 `/tmp`**：受限 harness（DSH `workspace-write` 等）下 `/tmp` **只读**，写它会失败」

**实测**：`touch /tmp/probe-$$` **成功**（本会话）。且 `peekview` 的 debug 全套**正在用** `/tmp/peekview-debug/`（`AGENTS.md:46,62,115`），`orchestrator-log.md:526` 只说 `/tmp` 是 **per-call tmpfs**（跨调用看不见），**从未说只读**。

**为什么这条要紧**：新增节的**整个理由**是「沙箱把写权限限制在会话工作区内（**工作区外含 `/tmp` 不可写**）⇒ agent 只能在项目树内落临时产物」。如果 `/tmp` 实际可写（本机实测如此），则"必须在项目树内"这一**唯一论据**不成立——正确表述应是「`/tmp` 在 DSH 下是 **per-call tmpfs**（跨调用不可见，且不同工作区策略可能不同），故**中间产物应落在项目树内的 `.agate-tmp/` 以保证跨调用可见**」。**结论（用 `.agate-tmp/`）仍然成立且更好**，但**论据用错了**，而这条错误论据同时被写进了 `platform-notes.md`（跨平台权威源）、`dispatch-prompt.md`（注入每个 subagent 的派发模板）与 `SKILL.md`（第 2 条"`/tmp` 只读"是**既有**条目，本批的 5 引用了它）。

注：`SKILL.md:66` 的「`/tmp` 只读」是**本批之前就存在**的（`git show HEAD:...` 确认），不是本批引入；但本批**新写**的 platform-notes 与 dispatch-prompt 把它**升格为跨平台结论**并作为核心论据，**扩大了既有错误的传播面**。建议本批至少把 platform-notes/dispatch-prompt 的措辞改为"per-call tmpfs / 跨调用不可见"，并顺带订正 `SKILL.md` 第 2 条。

---

### C. agent-team 定位（RM-AG0076）— **部分成立；核心断言与上游相反**

#### C-1 ✅ 引用准确、id 集合逐字一致

`packages/experimental/agent-team-profile/cordis.patch.yml` 实测四条 disable：

```yaml
- id: tool-subagent-control
  disabled: true
- id: tool-subagent-list-agents
  disabled: true
- id: tool-subagent
  disabled: true
- id: tool-subagent-fork
  disabled: true
```

`agate/assets/templates/dsh/agent.cordis.yml` 派发组授权四行（第 161/164/167/174 行）：`tool-subagent-control` / `tool-subagent-list-agents` / `tool-subagent` / `tool-subagent-fork`。

**`diff` 实测两个集合完全相同（IDENTICAL）**——roadmap 所称「`diff` 实测一致」**属实** ✓。README 引用也逐字对得上：

> 「普通 subagent 委派及名称重叠的全局 child control 会被禁用；Workflow 仍可创建 fresh 子代理。本包随 dsh 安装提供，**默认关闭**，可在插件页开启或添加到已初始化的 profile。」

✅ **「独立 bundle / 随安装提供 / 默认关闭」成立**（README 概述 + 已知限制「仅显式启用——本包随安装提供但默认关闭；随附 CLI、Web、SDK、ACP 与 Python profile 都不会启用它」）。

✅ **本机 profile 未启用**：`~/.dsh/profiles/web/package.json` 实测 `dsh.profile.bundles` = `["@deepseek-ai/dsh-base", "@deepseek-ai/dsh-web-app"]`，**未含** agent-team ✓。`cordis.patch.yml` 中亦无 agent-team 相关行 ✓。（顺带：本机**只有 `web` 一个 profile**，`~/.dsh/profiles/` 下无其他 profile。）

#### C-2 ❌ **「整体失效」与上游原文相反**（阻断项 ②）

**上游 README 第 108 行「已知限制」原文**（中文）：

> **预设内的子代理控件**——Web 预设仍可在**预设作用域**挂载 continuable Subagent 控件；**顶层组合包不会替换这些注册**。

英文（`README.md:108`）：

> **Preset-scoped child controls** — Web presets can still mount continuable Subagent controls in their own scope; **this top-level bundle does not replace those registrations**.

**这正是 agateon 的情形**：`agent.cordis.yml` 的派发组四行**不是** profile 顶层行，而是经由 `dsh_preset_block()` 包成 `@deepseek-ai/dsh-agent-preset` 的 `config.plugins`（`agate_common.py:927-990`，生成 `- id: preset-agate / name: '@deepseek-ai/dsh-agent-preset' / config.plugins: [...]`）⇒ 它们挂在**preset 作用域**，**正是**上游点名"不被顶层组合包替换"的那类注册。

机制侧可佐证（我读了实现，非仅读 README）：

- `agent-preset-registry/src/mount.ts:254-268` `mountPreset()` 为每个 preset 声明建**独立的 `PresetTree`**（`new PresetTree(ctx)`），`ctx` 来自 `createScope(owner, key)` 新建的**preset 作用域**（`index.ts:106-113`）。patch 的 `disabled` 按 **Loader row id** 作用于**它自己所在的那棵树**；preset 树里的行 id 带命名空间前缀——`mount.spec.ts:43` 实测 `expect([...mount.tree.entries()][0]!.id).toBe('parent:child')`，即 preset 子行 id 是 **`<parentEntryId>:<childId>`**，**不是**裸 `tool-subagent`。
- `packages/bundle/base/cordis.patch.yml` 的四行确实位于**顶层 `- insert:`**（第 15 行起、缩进 4），id 是**裸的**；而**shipped 的 Web preset 自己也在 preset 作用域挂同名四行**（`packages/bundle/web-app/presets/standard.patch.yml:86-98`，cordis/ptc 同样是 12 处 `tool-subagent`）——上游自己就是"顶层有 + preset 内又有"的双份结构，这正解释了为何要专门写这条限制。

⇒ **「启用后本 preset 的工具映射整体失效」是错的**。准确结论应是：**顶层那四行会被禁用，但 agate preset 自己作用域内的同名四行仍然挂载并生效**——即 agateon 的 `subagent` / `subagent_fork` / child control **不会**因启用 agent-team 而消失；实际风险是**两套委派面并存**（team 工具 + preset 的 subagent 工具），恰恰是 roadmap **原本**声称、后被"更正"掉的"同时可见"形态。

**这直接推翻了两条下游结论**：

1. **「替换式而非叠加式」的适用性**：该说法对**顶层 dsh-base 行**成立（README 概述"普通 subagent 委派…会被禁用"），对**preset 作用域行不成立**。文档把它当成对 agateon 情形的完整刻画，**缺了 preset 作用域这一层** ⇒ 断言**部分不成立**（是"叠加"与"替换"各占一半，取决于行挂在哪一层）。
2. **「无机制可写」不成立**（用户问题 3）：既然启用后是**两套工具面并存**，就**存在需要收敛的叠加态**，也就**存在可写的介入点**。可操作的介入点至少有二：
   - **profile 层守卫**：`agate-setup.py` 已遍历 `dsh_patch_files()`（`~/.dsh/profiles/*/cordis.patch.yml`）并在其中维护托管块 ⇒ 完全可以在 `--list` / 安装时读同一 profile 的 `package.json` 的 `dsh.profile.bundles`，命中 agent-team 时**输出显式告警**（含"preset 侧 subagent 行不受其 disable 影响、但两套委派面并存"的准确说明）。我核实 `agate-setup.py` 当前**完全未读** `bundles`（`grep -c bundles` = 0）——**这是一个明确可写、代价极低的机制**，而非"无机制可写"。
   - **预置判据已有**：`SKILL.md` 第 7 条新增的"核查是否已启用：看 `dsh.profile.bundles`"已经给了自查命令，把它从**散文**升级为**`agate-setup.py --list` 的实际输出**只差几行。
   - ⚠️ 至于**能否在 preset 声明侧直接抑制**：preset 的 `disabled` 只作用于自己的树，**管不到顶层/team 行**（这正是上游那条限制的另一面）；`config.plugins` 也**只能**声明自己挂什么。所以"让 agateon preset 显式禁用 team 工具"**确实不可行**——这一点你的判断方向对，但**结论表述错**（不是"无机制可写"，而是"不能在 preset 侧写；可在 profile/setup 侧写"）。

#### C-3 ❌ `test_t41_agent_team_disables_exactly_the_preset_grants` 断言的是**代理指标**，不是被争议的结论

该测试只做一件事：`granted ⊆ disabled`（两个 id 集合包含关系）。我验证：

- 两个集合**本来就完全相同**（见 C-1），所以 `missing` 恒为空 ⇒ **断言恒真类**（在当前上游不变的前提下）。它的**唯一价值**是"上游若改了这四条 id 就变红提醒重核"——这是**合法的漂移哨兵**，但**它不能、也没有**验证"启用后 preset 工具映射失效"这个**实际被写进文档的结论**。
- 更关键：**即使该断言恒真，被争议的结论仍然是错的**——因为"顶层禁用这四行"**不等于**"preset 作用域的那四行失效"（C-2）。**测试通过给了文档一个虚假的安心信号**：测试绿 ≠ 文档断言成立，二者之间**没有蕴含关系**。
- **CI 上会 skip 吗？** 实测**不会**——本机存在 DSH checkout，测试**实际执行并 passed**。但 CI（`.github/workflows/` 中无 `DSH_REPO`、无 deepseek-harness）下 `upstream is None` → `pytest.skip`，此时**仅剩 `granted` 非空**这一条断言（弱哨兵）。**结论：有价值但价值被高估**——它对"id 集合漂移"是有效哨兵；对"文档结论是否正确"**零覆盖**。建议：要么把该测试降级/改名为"id 集合漂移哨兵"，要么补一条**真正**断言作用域语义的测试（例如断言 `agent.cordis.yml` 的行是 `config.plugins` 子行、其 id 在 preset 树中带命名空间前缀），否则它会被后续读者误当作文档结论的证据。

#### C-4 ⚠️ 上游 README 的「已知限制」在本批文档中被**遗漏引用**

文档引用了 README 的**概述段**（默认关闭 / 禁用普通 subagent 委派），但**未引用同文件第 108 行的「已知限制」**——而那条限制**恰好**是本情形（preset 作用域行）的**直接反例**。这不是"引用不准"，而是**选择性引用**：支持结论的那段引了，限定结论的那段没引。**这是 C-2 缺陷的成因**，也提示一个流程性教训：引用上游结论时应同时检索**同文件的「已知限制 / Known limitations」节**。

---

### D. 逐字节回归护栏（第三次刷新）— **护栏语义确需重定义（我的独立判断）**

**先说事实**（可复现）：

- 基线文件历史上被刷新 **3 次**（commit-message 轨迹与 sha 轨迹逐条对上）：

| commit | `check-gate.py` 基线 sha | 说明 |
|---|---|---|
| `c218026` (TAG0034-P3) | `bd4855fbdb` | 建立 |
| `e1f947c` / `bef79e6` | `bd4855fbdb` | 未变（文档轮） |
| `6d765a1` (TAG0035) | `e6a4cf4a1b` | **刷新 1** |
| `71063be` (TAG0039) | `9a50256ed4` | **刷新 2** |
| 本批（TAG0041，未提交） | `5dd2f247` → 现 `b79e8bb5` | **刷新 3** |

- 同基线文件里其余受保护项**几乎都冻住了**：`agate/rules/phases.yaml` **0 次**变化、`state-machine.md` 1 次、`check-state-transition.py` 1 次（TAG0035）；**只有 `check-gate.py` 反复刷新**。
- 本批刷新**已按先例在 `_note` 中留痕**（写明"直改未走 P0-P8"+"可观测性改动，未改任何判据/exit code"），程序上**合规**。
- 我实测本批 `check-gate.py` 的改动**确实只增 WARNING**（新增代码不在任何 `return 1` 路径上，见 A-1）⇒ **本次刷新是诚实的**。

**我的独立判断：护栏并未"名存实亡"，但它守护的东西已经**不是**它自称守护的东西——语义应重定义。**

理由：

1. **"名存实亡"的严格判据是"刷新不再需要论证"**，而本批**仍做了论证**（`_note` 里逐条说明改动性质、且经 SELF-GATE 评审）。所以它**还在工作**——它事实上变成了"**每次改 `check-gate.py` 都必须显式声明并说明理由**"的**强制留痕装置**。
2. **但它的名义语义（"逐字节不变 = BDD-39 不违反"）已经被证伪 3 次**：一个 3 次被合法推翻的不变量，**不再是"不变"**，而是"**变更需申报**"。继续叫"零字节改动护栏"，会让读者（含未来的 agent）**误以为 `check-gate.py` 是冻结的**，从而在需要正当修改时产生**不必要的犹豫**，或反过来在刷新时**不再认真审视**（"反正又要刷"）——**第 3 次刷新正是后一种风险的信号**。
3. **字节不变不是有价值的守护目标**：本批的正确性主张是"**未改任何判据 / exit code**"（`_note` 自己这么写）。字节不变**既过严**（注释、措辞、新 WARNING 都会触发）**又过松**（一次成功的刷新后，**真正的判据回归**可以混在同一次字节变化里蒙混过关——**没有任何机制检查"判据是否变了"**）。**这是当前护栏的结构性缺陷**：它用"字节"度量"行为"，两者不等价。

**明确建议（需单独决策，我给出我认为最优的形态）**：

**方案 A（推荐）：把 BDD-39 拆成"行为不变"+"变更申报"两层。**

- **第一层（真正的护栏，自动化）**：新增**行为快照**测试——对 `check-gate.py` 的**每个阶段**（P0/P1/P2/P3/P4/P5/P6/P6.5/P7/P8）用一组**固定夹具**跑真实 CLI，断言 **exit code 精确相等**（本仓已有此手法：`test_tag0035_bdd_3_known_phase_not_routed_to_unknown_path` 就是 `parametrize` 全阶段断言"不被路由到未知阶段"）；再加一组**判据级**断言（如 P8 roadmap-done 拦截、P4 纯文档拦截、P7 CODE-MAP pairing——这些**已经存在**于 `test_check_gate.py`）。这一层**不因加注释/加 WARNING 而红**，但**判据一变就红**。这才是 BDD-39 声称要守的东西。
- **第二层（留痕，人工可审）**：保留 sha256 基线，但**改名与改语义**为「**`check-gate.py` 变更申报表**」——刷新时**必须**在 `_note` 写明"改了什么 / 为什么 / 是否触及判据"，**并且**提交信息含 `self-gate-review:`（已有机制）。即把"字节不变"从**断言**降级为**申报触发器**。
- 好处：正当改动（本批这种）**一次刷新即可**且不产生"护栏失效"的错觉；不正当改动（偷改判据）会被**第一层**抓住——而这是当前护栏**完全抓不到**的。

**方案 B（次优，最小改动）**：保留字节基线不动，但**把 BDD-39 的失败信息与文档改成自陈语义**：「本护栏守护的是**变更需申报 + 需经 SELF-GATE**，不是字节冻结；刷新是**预期动作**，未刷新才是缺陷」。成本最低，但没有补上"判据回归"的检测。

**方案 C（不推荐）**：只保护 `phases.yaml` + `check-state-transition.py`（本批 `_note` 已自陈这两者"未改任何判据"）而把 `check-gate.py` 移出基线。**不推荐**——`check-gate.py` 是判定主体，移出等于放弃唯一的行为锚点。

**⚠️ 无论选哪个方案，都不应在同一 commit 里既改 `check-gate.py` 又刷新基线而无独立证据**——本批做了评审（OK），但三段式刷新已经形成惯例化倾向，建议在方案落地前，**刷新时必须在 `_note` 里附"判据未变"的可核证据**（如"新增代码不在任何 `return 1` 路径上"+ 指向行为快照测试全绿），而不只是"可观测性改动"这类**无法核验的形容词**。

---

### E. 一致性与自洽 — **基本成立，有 2 处小问题**

#### E-1 ⚠️ 新测试的断言**是真的断言**（非空/非恒真），但**有一个是代理指标**

`test_t41_platform_hygiene.py` 7 个用例逐条核实：

| 用例 | 断言内容 | 评价 |
|---|---|---|
| `..._gitignore_fragment_exists_and_names_canonical_dir` | 文件存在 + 含 `.agate-tmp/` | ✅ 真断言（能红） |
| `..._p8_warning_points_to_existing_template` | 从 `check-gate.py` 抽取 `assets/templates/*` 引用，要求至少一个 gitignore 相关且**文件存在** | ⚠️ **代理指标**（见下） |
| `..._platform_notes_has_restricted_harness_section` | 6 个关键词 `in text` | ✅ 真断言（但纯字符串，易被措辞改动误伤） |
| `..._cards_and_dsh_skill_cross_reference` | P8 卡含 `.agate-tmp`、P5 卡含"探活"**或**"受限 harness"、SKILL 含 3 词 | ⚠️ **偏松**（`or` 分支降低了强度；纯字符串匹配） |
| `..._dsh_skill_forbids_agent_team` | SKILL 含"不要启用"+"agent-team"+"dsh.profile.bundles" | ✅ 真断言 |
| `..._agent_team_disables_exactly_the_preset_grants` | `granted ⊆ disabled` | ❌ **代理指标 + 恒真**（详 C-3） |

**代理指标问题（`..._p8_warning_points_to_existing_template`）——已用变异实验证实**：该测试用**正则扫源码字符串**来证明"告警指向的模板存在"，但它**不检查**告警是否真的会被**输出**。我做了变异实验（在 `agate/` 的**副本**上操作，未动被评审文件）：

- **变异体**：删掉整个 `sys.stderr.write(...)` 告警块（第 1504-1509 行），代之以 `pass` + 一行注释 `# ref: assets/templates/gitignore-fragment.txt`。
- **结果**：变异体已**完全失去该行为**（`grep -c "未被 .gitignore 忽略" <mutant>` = **0**），但该测试**依然判定通过**——因为它只要求 `assets/templates/([A-Za-z0-9._-]+)` 在源码里**出现过**（注释里的出现同样命中），且 `(mutant/assets/templates/gitignore-fragment.txt).is_file()` 为真。

⇒ **该测试无法区分"告警会输出"与"告警被删除、只剩字符串"**，属**冗余的弱代理**。而**真正的行为断言已由 `test_check_gate.py::test_t41_scratch_dir_not_ignored_warns` 覆盖**（跑真实 CLI 并断言 stderr 含告警文本），说明该代理**不必要**。建议删掉，或改为"运行真 CLI 后断言 stderr 提到的路径确实存在"。

**关于 `skip` 的价值（用户问题）**：CI 上 skip 的是 `test_t41_agent_team_disables_exactly_the_preset_grants` 的**交叉核对段**，此时它**仍执行** `assert granted`（preset 模板授权非空）——所以**不是完全不跑**，但**只剩弱哨兵**。价值判断见 C-3：**有效但被高估**。

#### E-2 ⚠️ `_read()` 与函数内 `import pytest` —— 一处小反模式

- `_read(p)` = `p.read_text(encoding="utf-8")`：**封装了 6 处重复调用**，属**合理**（不是反模式）。它缺 `errors="replace"`，与仓库既有 `agate_common._read` 口径略异，但测试读的是本仓 UTF-8 文件，**不构成风险**。
- **函数内 `import os` / `import pytest`**（第 77、88 行）：`os` **已在文件顶部导入？——核实：本文件顶部只有 `import re`**（第 10 行），所以 `import os` 在函数内是**唯一**导入，能工作但**违反 PEP 8**（导入应在模块顶部）。`pytest` 在函数内导入是**为了在 skip 分支才引入**——这个**有理由**（虽然 pytest 在测试文件里必然可用，提前导入零成本）。**判定：轻微反模式**（`os` 应在顶部；`pytest` 可接受但建议统一到顶部）。`ruff check` 通过（项目的 ruff 选择集不含 PLC0415/import-outside-top-level），所以**不会被 CI 拦**——属**风格问题、非缺陷**。
- 另注：该文件用 `open(upstream, encoding='utf-8').read()`（第 91 行）**未用 `with`**——**资源泄漏**（CPython 下会靠 refcount 及时关闭，故实际无害），但同文件其他地方用 `_read()`（用 `with`），**风格不一致**。建议统一。

#### E-3 ❌ **存在"声称有检查但实际没检查"的残留**（用户问题）

我按你的要求再查一遍，找到**两处**（一处在**被承诺但未交付**的层面，一处在**已交付但未验证**的层面）：

1. **约定 ④「清理时点 = P8/READY」+ RM-AG0077 ⑤「P8 卡补提交前暂存面审查」——两处都声称由 P8 卡承载，实际 P8 卡没收尾检查单条目**：
   - `platform-notes.md` 明写「④ 由 P8 卡收尾检查单承载」，但 `## READY 收尾检查` 节中 `grep -c agate-tmp` = **0**（该节只有"调试服务/进程已停止""临时数据已删除""测试占用的端口已释放"三条**笼统**项）。P8 卡**唯一**的 `.agate-tmp` 出现是第 13 行的**流程指针**，不是检查项。
   - 「提交前暂存面审查」在 `agate/phase-cards/` 与 `agate/assets/execution-roles/` 中**命中 0**——RM-AG0077 ⑤ 的**前半句完全未落地**（后半句"交付 `.gitignore` 模板预置"落地了）。
   - ⇒ 二者都是**声称有、实际无**。
2. **新增的 2000 文件截断分支**（当前版本新增的 `elif truncated:` 输出）**无测试覆盖**：`grep -n "仅扫描了前\|未扫全\|2000\|SCAN_CAP" agate/tests/unit/test_check_gate.py` → **0 命中**。5 个新测试**全部**是小目录场景。我手工构造 2600 文件验证了该分支**确实会输出**（行为正确），但**没有回归保护**——将来若有人改动这段，**测试不会红**。这属于"有检查但未被检查"（同一族问题的**新增实例**）。
3. **一处"声称的两条 WARNING 均可机械校验"，但 ① 与 ④ 实际无校验**（详见 A-7，roadmap 措辞夸大）。

（另：`test_t41_platform_hygiene.py` 的 6 个关键词/交叉引用断言**确实在跑**，非空断言——此项**通过**。）

---

## 反例搜索

### 反例 1：P8 检查的**假阳性**（实锤，可复现）

```
mkdir -p $T/sub && cd $T && git init -q . && printf '.agate-tmp/\n' > .gitignore
mkdir -p .agate-tmp && printf 'x\n' > .agate-tmp/probe.mjs && git add -A && git commit -qm init
cd $T/sub && python3 <agate>/scripts/check-gate.py P8 $T/task
# → GATE P8 WARNING: .agate-tmp/ 存在但**未被 .gitignore 忽略**     ← 假阳性
```

根因：`check-ignore` 的**相对路径参数按 CWD 解析**，与仓库根锚定的忽略规则不匹配。**代价**：使用者会在"目录明明已忽略"的情况下被反复告知"未被忽略"，并按 remedy 去改一个**本来就正确**的 `.gitignore`——**噪声会导致真实告警被忽略**（狼来了）。

### 反例 2：P8 检查的**假阴性**（实锤，可复现）

**(a) 子目录 CWD 掩盖根目录真实问题**（同上构造，根目录未忽略 + CWD 在已忽略的子目录）→ **0 条告警**。

**(b) 跨仓库错位（最严重）**：CWD 在仓库 B、`task_dir` 指向仓库 A ⇒ 检查 B 的 toplevel，对 A 的未忽略 `.agate-tmp/`（内含 `creds.env`）**完全静默**。而该检查的**唯一目的**就是防这类凭证入库 ⇒ **在最需要它的场景下失效**。

### 反例 3：误报既有项目？—— **否**（实测 6 个仓库全部无 `.agate-tmp/`，零噪声）

### 反例 4：落点是否选错？—— **落点不完整**（A-6）

真实 `git add -A` 在**项目侧** `peekview/Makefile:265`（`bump-version`）；agateon 侧**无任何** `git add -A`，P8 卡用的是精确路径 `git add {workspace}/tasks/{Txxx}/`。⇒ 把检查放在 `check-gate.py P8` **不是错的**（发布前最后一道机械门 + WARNING-only），但 RM-AG0077 ⑤ 自己拆出的"**agateon 侧应做 P8 卡提交前暂存面审查**"**未交付**，且约定 ④ 的承载处（P8 收尾检查单）**也没加**。

### 反例 5：上游事实与文档不一致 —— **C-2 实锤**（预设作用域）

上游 README **第 108 行「已知限制」**明文："预设内的子代理控件——Web 预设仍可在**预设作用域**挂载 continuable Subagent 控件；**顶层组合包不会替换这些注册**。" 而 agateon 的 preset 四行**正是** `config.plugins` 内的**预设作用域**行 ⇒ 文档"整体失效"结论**与上游相反**。机制侧佐证：preset 行 id 带命名空间（`parent:child`）、每 preset 建独立 `PresetTree`。

### 反例 6：`/tmp` 可写性 —— **文档与 env.md 及实测相反**（B-5）

`env.md` 表格（2026-09-03 实测）标 `/tmp` **✅ 可写**；本会话 `touch /tmp/...` **成功**；peekview debug 全套**正在用** `/tmp/peekview-debug/`。文档新增的"只读/不可写"是**论据错误**（结论仍可用，但理由需换成 per-call tmpfs）。

### 反例 7：`AGATE_TMP_DIR=''` 空值 —— **扫描整个仓库**（实锤）

`os.environ.get("AGATE_TMP_DIR", ".agate-tmp")` 对**已设置但为空**的变量返回 `""`（不是走默认）⇒ `os.path.isdir(repo_root + "")` = True（仓库根恒为目录）⇒ **对整个仓库做 `os.walk`** 并把根目录下的 `test_toplevel.py` 报成"`.agate-tmp` 内有文件匹配测试收集模式"，告警文本显示为 **`/ 内有 1 个…`**（目录名渲染为空）。**后果**：① 输出误导（`/`）；② 大仓库下每次 P8 都全树扫描 2000 个文件。我实测复现。**修法**：`os.environ.get("AGATE_TMP_DIR") or ".agate-tmp"`，并校验 `tmp_rel` 非绝对路径、不含 `..`。

### 反例 8：`AGATE_TMP_DIR` 绝对路径 —— 无害（实测 `isdir` 走绝对路径，行为合理）

### 反例 9：文档叙述的**事故形态未被检查覆盖**

`platform-notes.md` 用**整行**论述"探针文件名命中收集面"的实例是「并行评审写入的 `.agate-tmp/*.spec.ts`」，而 `roadmap.md` 与 `P0-brief.md` 记载的**真实事故**是 `frontend-v3/.agate-tsprobe/*.spec.ts`（**嵌套在子目录**）。我实测：把 `frontend-v3/.agate-tsprobe/foo.spec.ts` 放在仓库里（该目录已忽略）→ **0 条告警**（检查只看**项目根**的 `.agate-tmp/`，不看嵌套 probe 目录）。⇒ **检查覆盖不到被引为理由的那次真实事故**。这不必然是缺陷（新约定只规范了 canonical 目录），但**文档把"根因事故"与"检查能力"写得像是同一件事**，属**声称与事实的落差**。

---

## 真空通过自检

**每个 exit code / 数字在何种前提下才算证据**：

| 证据 | 成立前提 |
|---|---|
| `git check-ignore -q` **exit 0 / exit 1** | 仅在**指定路径相对于 CWD 的解析**与**忽略规则相对仓库根的匹配**一致时，才等价于"该目录被忽略"。**CWD=仓库根**时成立；CWD 在子目录或跨仓库时**不成立**——这是 A-2 两组反例的机理。我据此才敢断言"假阳性/假阴性"。 |
| `gate P8` **return 2** | 仅证明"脚本化检查通过、需主 Agent 自判"，**不证明**任何 WARNING 被输出。断言"WARNING 出现"必须**同时** grep stderr 文本（我的 A-1 表格就是这样做的）；单看 exit code **会真空通过**。 |
| 5 个 `test_t41_*` **passed**（`cwd=repo`） | 仅证明 **CWD=仓库根**这一种姿态下行为正确。我 `cd sub` 后立刻复现假阳性 ⇒ **绿 ≠ 无缺陷**。 |
| `test_t41_platform_hygiene.py` **7 passed** | 其中 1 个是**恒真**（`granted ⊆ disabled`），故"7 passed"的**有效信息量 < 7**；6 个是字符串/文件存在性断言，**不验证**被写进文档的行为结论。 |
| BDD-39 **passed** + sha **MATCH** | 仅证明"基线已被同步刷新到当前字节"。**它不证明**判据未变——本批判据未变是**我另行核对 `return 1` 路径**得出的，**不是**基线给的。 |
| `check-protocol-consistency.py` **0 ERROR / 386 WARNING** | WARNING 未逐条归因，**不能**据此认为"无协议问题"；仅证明无 ERROR 级不一致。 |
| `count-tests.sh` = **2420** | 是 `collect-only` 口径；证明"收集数"，**不证明**每个用例都在 CI 上**实际执行**（skip 的用例同样计入收集数——`test_t41_agent_team_...` 在 CI 上正属此类）。 |
| `peekview` `.agate-tmp/` **76MB / 10 token / 158 条** | 单点实测记录（`P8-release.md:221`、`retrospective.md:88`），**未复现**（目录已清理，`ls` 不存在）⇒ 属**有据但不可复核**的引用。注意 `P8-release.md` 记 **158**（另有 `git status` = 156）、`retrospective.md` 记 **162 条路径其中 158 条在该目录**，本批文档统一写 **158**——**口径正确**（取"该目录下的条数"）。 |
| **7200→43200s / 4 次** | 前提是"日志记录 = 实际发生"。逐行核对**次数与时长吻合** ⇒ 成立。但「每次都白跑一整轮」**不成立**（B-3b：第 2 次自行恢复、第 4 次明确"无影响"）——**同一日志既能支持前者、也能证伪后者**，这正是"引用了数字却过度概括"的典型。 |
| `/tmp` 可写 | 前提是**当前沙箱配置**。`env.md` 自陈"不同工作区不同"⇒ 我的 `touch` 成功**只证明本工作区**，不足以证明"所有 DSH 配置下可写"；但**足以证伪**文档"（跨平台）`/tmp` 只读/不可写"的**全称断言**。 |
| **6 个存量仓库无 `.agate-tmp/`** | 前提是 `~/oclab/*` 代表"既有项目"。样本有限，但结论方向（"仅对采用约定的项目生效"）有结构性支撑：检查**以目录存在为前置条件**。 |

**真空通过风险总评**：本批新增检查的两条 WARNING **均为 WARNING-only**（不阻断）。这意味着**它们自身永远不会让 gate 变红**——一条永不阻断的检查，其**唯一**证据形态就是"stderr 里出现了正确文本"。因此 A-2/A-7/反例 7 的假阳性与假阴性**不会被任何 exit code 暴露**，只能靠**读输出**发现。这正是本仓反复出现的"**exit 0 承载两种互斥语义**"（RM-AG0077 ①）在**本批新增代码上的再现**：建议在 WARNING 文本里加入**判定依据**（如"仓库根=`<path>`，检查路径=`<path>`"），使读者能一眼发现 CWD 错位。

---

## 遗留问题 / 建议

### 阻断项（提交前必须解决）

1. **[A-2] 修 CWD 定位**：`rev-parse --show-toplevel` 与 `check-ignore` 均传 `cwd=repo_root`（仓库根锚定），`check-ignore` 用**绝对路径**；并补 2 个测试（`cwd=subdir` 的假阳性回归 + `task_dir` 与 CWD 分属不同仓库时的正确锚定）。**这同时是对既有 DEBT0020 教训的一致性修复**。
2. **[C-2] 订正 RM-AG0076 的核心断言**：把"启用后 preset 工具映射**整体失效**"改为反映上游「已知限制」的准确表述——**顶层四行被禁用，但 preset 作用域的同名四行仍生效 ⇒ 风险是"两套委派面并存"而非"工具面消失"**；相应订正 `platform-notes.md` DSH 章、`SKILL.md` 第 7 条、`roadmap.md` 的落地段，并**补引上游第 108 行**。
3. **[B-5] 订正 `/tmp` 论据**：`platform-notes.md` / `dispatch-prompt.md`（及顺带 `SKILL.md:66`）把"`/tmp` 不可写/只读"改为"DSH 下 `/tmp` 为 **per-call tmpfs**（跨调用不可见；且写权限按工作区配置而异）"——**结论（用 `.agate-tmp/`）保持不变**，只换论据。

### 强烈建议（同一批内可低成本完成）

4. **[C-2/C-3] 交付"可写的介入点"**：在 `agate-setup.py --list`（或安装路径）中读取同一 profile 的 `package.json` 的 `dsh.profile.bundles`，命中 agent-team 时输出**显式告警 + 准确说明**（顶层禁用 / preset 行不受影响 / 两套委派面并存）。把 `SKILL.md` 的自查命令从散文升级为脚本输出 ⇒ 撤销"无机制可写"的结论。
5. **[A-6] 补齐承诺但未交付的两处**：① P8 卡加"**提交前暂存面审查**"（RM-AG0077 ⑤ 的前半句）；② P8 `## READY 收尾检查` 加 `.agate-tmp/` 清理项（约定 ④ 自陈的承载处）。
6. **[A-7] 统一措辞**：`roadmap.md` 的"四项均可机械校验"改为与 `platform-notes.md` 一致的"②③ 机械校验 / ① 常量 / ④ 检查单"。
7. **[B-3b] 收紧过度概括**：删掉「每次都表现为 … 白跑一整轮」，改为"掉线本身无数据损失（第 2 次 subagent 自行恢复、第 4 次对本阶段无影响），但带来诊断/重启成本与'用前未探活即失败'的风险"。
8. **[B-4] 补第 3 步的可操作性**：注明启动/种子命令由 P0-brief 的 `debug_env` 声明，掉线恢复照此执行。
9. **[反例 7] 修 `AGATE_TMP_DIR` 空值**：`os.environ.get("AGATE_TMP_DIR") or ".agate-tmp"`；并拒绝绝对路径/`..`。
10. **[A-5] 修模板自查命令**：`git check-ignore -q .agate-tmp/ && echo ok`（带尾斜杠），或改用 `--no-index` 形式，避免"目录尚不存在时误判未配置"。
11. **[E-3] 给 2000 截断分支补测试**；**[E-1] 删/改代理指标测试**（`..._p8_warning_points_to_existing_template`：改为跑真 CLI 后检查 stderr 路径存在）；**[E-2] `import os` 提到模块顶部、`open()` 改 `with`**。
12. **[C-4 流程] 引用上游结论时同检「已知限制 / Known limitations」节**——本次缺陷的根因是只引概述段未引限制段。

### 需要单独决策（D 节）

13. **重定义 BDD-39**：推荐**方案 A**（"行为不变"自动断言 + "变更申报"留痕两层）；退而求其次**方案 B**（仅改自陈语义）。**核心判断**：字节不变**既过严又过松**——它拦不住真正的判据回归（本批的正确性是我**另行**核对 `return 1` 路径得出的，护栏没参与），却因 3 次合法刷新而**削弱了自身信号价值**。**在方案落地前**，每次刷新应在 `_note` 附**可核证据**（"新增代码不在任何 `return 1` 路径上" + 行为快照测试全绿），而非"可观测性改动"这类不可核验的形容词。

### 流程性观察

14. **评审期间文件被并发编辑**（评审窗口内 `check-gate.py`、`platform-notes.md`、`test_t41_platform_hygiene.py` 均变动，且新增了 `.gitignore`、`dispatch-prompt.md` 两处改动）。这让"评审对象"边界不稳定——**SELF-GATE 应在改动冻结后进行**，否则评审结论与提交内容可能错位（本报告已固定受审版本 sha，但若继续改动，需**增量复审**）。另：**`2000 文件上界静默漏报`这个问题在我评审过程中被修掉了**（初版 `_scanned > 2000` + 静默 → 现版 `truncated` + 显式提示），说明并发修复确实在发生——但这也意味着**任何单一时点的评审都可能打在移动靶上**。

---

*评审者：protocol-alignment-review（独立 SELF-GATE 语义审查）。本轮**未修改任何被评审文件**：未 commit、未改源码/测试/文档；所有实验均在 `mktemp -d` 临时仓库中进行并已清理。*

---

## 处置记录（主 Agent，2026-09-29）

**评审 status = needs-revision（3 条阻断 + 6 条重要发现）；以下逐条处置。评审原文保留不改，便于追溯。**

> ⚠️ **评审者提示的并发编辑问题成立**：评审窗口内我仍在改（新增 `.gitignore`、`dispatch-prompt.md`，并二次修改 `check-gate.py`/`platform-notes.md`）。评审报告的结论已固定在它受审的那一版；**下列处置基于其发现，但改动后的版本未再经它复审**——这是本批流程的真实缺口，记录在案。

| # | 评审发现 | 处置 |
|---|---|---|
| **1（最严重）** | `check-gate.py P8` 新检查**按 CWD 而非 `task_dir` 定位仓库** → 假阳性（`cd` 到子目录时已忽略被误报）+ **跨仓库漏检**（CWD 在 B、task_dir 在 A 时对 A 的真实凭证风险无感）；且**违反同一函数内 DEBT0020「仓库根锚定」** | **已修**：`_git()` 增加 `cwd` 参数（`run_git` 本就支持）；仓库定位改 `cwd=task_dir`；`check-ignore` 判据改传**绝对路径**。四组端到端复测：正常/子目录/跨仓库/空值 全部符合预期 |
| **2** | `agent-team` 断言与上游 README 第 108 行「**顶层组合包不会替换这些注册**」**直接冲突**，且属选择性引用（只引支持结论的概述段） | **已更正**：文档改为「**两套委派面并存**」而非「preset 失效」，并**显式承载上游原文**；两次写错（先「同时可见」、后「整体失效」）**均已留痕**备查；新增测试断言文档必须引用该原文（防再犯） |
| **3** | `/tmp` 论据错误（文档称「只读」，实测可写） | **已更正**（我先改了一版但论据仍不扎实）：现写作「**per-call tmpfs**（可写但跨调用不可见）」，补**DSH 源码机制出处**（`roots.ts::writableRoots()` 把 `/tmp` 列入可写白名单；`profiles.ts` 为 workspace-write 加 `--tmpfs /tmp`）+ 本机跨调用实测（写入后下一次调用文件消失、`/tmp` 为空）；三处（platform-notes / SKILL / dispatch-prompt）同步 |
| **4** | `AGATE_TMP_DIR=''` → `isdir(root+"")` 恒真 → **扫描整个仓库** | **已修**：`os.environ.get(...) or ".agate-tmp"`；复测输出为 `.agate-tmp/`（正常路径） |
| **5a** | 约定 ④ 声称「P8 卡收尾检查单承载」但该节 `.agate-tmp` 命中 **0** | **已修**：纳入 `## READY 收尾检查` 的「测试环境已清理」项（含自查命令与两项约束） |
| **5b** | RM-AG0077⑤ 承诺的「P8 卡补**提交前暂存面审查**」在全部 phase-cards/roles **0 命中** | **已修**：P8 卡新增「提交前暂存面审查」节（`git diff --cached --name-only` 过目 + 背景数字） |
| **5c** | roadmap 写「四项均可机械校验」与 platform-notes「①常量/④检查单」**自相矛盾** | **已修**：roadmap 改为精确分工表述 |
| **6a** | `..._p8_warning_points_to_existing_template` 是**源文本扫描**（评审变异实验：删掉整个告警块、只在注释留路径，测试仍绿） | **已改为行为级**：真实触发告警并断言 `stderr` 中的模板路径真实存在；**并用同一变异复验**（改后该变异转红） |
| **6b** | `..._agent_team_disables_exactly_the_preset_grants` 是**恒真 + 代理指标**（`granted ⊆ disabled` 本来就相同） | **已拆为三条**：① 仓内前提（生成块的 `plugins:` 作用域内含四个委派控件——测**生成产物**而非模板）② 上游交叉核对（skip 语义保留，但定位为**结构哨兵**）③ 文档须引用上游原文 |
| **D** | 字节护栏语义须重定义（**过严**：注释/WARNING 也触发；**过松**：判据回归可混在同次刷新蒙混） | **已按「绊线」更正语义**（文件头写明真实语义 + 有效边界 + 改进方向）；本次为**第 5 次刷新**，`_note` 已如实记理由。**未重写机制**（评审推荐的两层结构需设计，属独立议题） |
| **E（弱代理）** | 2 个测试是弱代理 | `p8_warning` 已升级为行为级；`disables_exactly` 已拆分。**2000 截断分支仍无测试覆盖**（已记入遗留） |

**核验**：`check-protocol-consistency.py` 386 WARNING / 0 ERROR；`ruff` / `shellcheck` 通过；全量 pytest **2418 passed / 2 failed / 2 skipped**——两个 failed 均为**预存环境问题**：`opencode` 不在 PATH、`test_install_three_paths` 的 `git clone --bare --local` 跨设备硬链接失败（`/tmp` 为独立 tmpfs；已 stash 本批改动在 HEAD 复现同样失败）。

**元教训（值得留存）**：本次评审的**最有价值发现（CWD 锚定）与我的新代码同处一个函数**，且**上方 80 行就是 DEBT0020 的同款规则**——我复制了「定位仓库」这个动作却漏了它的取向。**已有规则就在旁边，不等于会被遵守**；这类「局部一致、整体不一致」只有**独立评审**或**跨场景测试**能发现（现有 5 个测试全在 `cwd=repo` 下跑，结构性发现不了）。
