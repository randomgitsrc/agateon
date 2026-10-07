# TAG0050 P2 评审问题单 — 外部专家答复

- **对象**：`tag0050-p2-expert-questions.md`（Q1–Q4），以及配套的 `P2-design.md`、`P2-review-eng.md`、`P2-review-cso.md`、`P2-review.md`
- **基线**：agateon `720c97d3`（v0.79.0）与 `a68d763`（v0.78.3）；git 2.43.0
- **方法**：实测全部在 `scratchpad` 副本上完成，真实仓库 `git status --porcelain` 为空
- **日期**：2026-10-07

---

## 结论速览

| # | 答复 | 一句话理由 |
|---|---|---|
| **Q2** | **症状可以复现，但根因是版本错位，不是 git 的问题** | 真实 commit 跑的是 `~/.agate` 中的 v0.78.3 hook，这个版本**没有** 2h.1d 的 `git add`；"手动跑"用的是 checkout 里的 v0.79.0 脚本。换成 v0.79.0 hook 后，真实 commit 中的账本是 2 行 |
| **Q1** | **G3 作为缺陷不成立，RM-AG0100 应以"误诊"关闭**。真正剩下的两件事归 **A3** | 判据是**单一 owner = 让该 Then 成立的那次改动所在的批**，而不是主题所属的领域 |
| **Q3** | **路线 ①（A1 交付脚本），但要改形**：gate 只覆盖仓内语料；peekview 部分转为 P6 证据 | §8"legacy 退出码与 ERROR 集合不变"是本任务最重要的兼容承诺，不应靠记忆来保证 |
| **Q4** | 单一来源：`markers.yaml` 中 `PROD_TOUCHED` 改为 `default` 口径，pre-commit 调用 `agate_markers.pattern()`；扫描面为任务目录内全部暂存的 md 新增行；否定写法**继续阻断**，但给出指引 | 在两个仓库的全量语料上，新口径和新扫描面**新增误拦为 0** |
| 附 | **`P5_repro` 也是"不会变红的 gate"**，与 B1 同类 | 复现脚本只打印、不断言；legacy 行为不变，所以实现之后它仍会"显示绕过" |

---

## Q2：G3 的症状与根因

### 实测

| 场景 | committed | worktree | status |
|---|---|---|---|
| 真实 `git commit`，hook 为 **v0.79.0**（`720c97d3`） | **2** | 2 | 干净 |
| 真实 `git commit`，hook 为 **v0.78.3**（`a68d763`） | **0** | 2 | `M` |
| 手动运行 checkout 中的 **v0.79.0** `pre-commit-gate.py` | index=2 | 2 | `A` |

第二行和第三行与主 Agent 探针的数字**逐项一致**（0/2/`M`，2/`A`）。

两个版本中 2h.1d 语句的出现次数：

```
grep -c 'run_git(["add", os.path.join(task_dir, "gate-events.jsonl")' pre-commit-gate.py
  v0.78.3 → 0
  v0.79.0 → 1
```

2h.1d 是 TAG0042 批 3（BDD-12）在 **v0.79.0** 才加进来的。问题单 §0 的基线写着"协议稳定版 agate v0.78.3"，也就是说，真实 commit 时执行的 hook 根本没有这一步。

### 根因

- **不是** `index.lock`，也**不是**临时索引。
- git 对普通提交（as-is commit）会在 pre-commit hook 运行**之后**重新读取索引，所以 hook 里执行的 `git add` 会进入本次提交。cso 的最小复现结论正确。
- 实测中 hook 拿到的环境变量是 `GIT_INDEX_FILE=.git/index`（相对路径）。现有代码的 `run_git` 不设置 `cwd`，所以不受影响。但这是一个潜在的坑，建议在 A3 的说明中注明：hook 里如需在其他目录调用 git，必须改用绝对路径。

**真正的原因是：探针比较的是两个不同版本的协议。** 这正是 AGENTS.md"gate 工具 ≠ 检查对象"那一节要防的情形。

### 对设计的含义

1. **§2.7 的措辞成立，不需要改。** 在 v0.79.0+ 中，"2h.1c/d 使事件随本次提交入库"对**推进类 phase**成立（实测为 2 行）。仍未覆盖的是**进入 PAUSED / READY / DONE 的转换**：2g 在 2h.1c/d 之前就 `continue` 了，这本来就是设计 §2.7 要通过前移来解决的（A3）。cso 的 MEDIUM-3 也指的是这一点。
2. **这起误诊恰好说明 A1 的必要性。** 设计 §2.3 让 `gate_run` 事件附带 `agate_version` 和 `resolver`。如果当时账本里有这两个字段，"commit 时跑的是哪一版 hook"一眼就能看出来。建议把本案写进 A1 的动机说明。
3. **新的风险（比 G3 更值得关注）：开发者本机稳定版与回放协议不一致。**
   - 现状：开发者的 hook 是 v0.78.3，而设计 §2.4 规定 agateon 在没有固定版本时，回放使用 **merge-base 处的 `agate/`**，也就是 v0.79.0。
   - 后果：TAG0050 的提交是在 v0.78.3 下通过 hook 的，A2 落地后用 v0.79.0 回放，可能误报 FAIL。上表就是"同一提交、两个版本、两种结果"的实例。
   - 建议：
     - 把 P1 §5 中的 SUGGEST"agateon 写 `.agate-version`"**升级为 A2 的前置条件**；
     - 或者在开发 TAG0050 之前，先执行 `agate-install.py v0.79.0` 让本机与 main 对齐；
     - 两种做法任选其一，都要写进 P2 的 `env_constraints`。

### 复现命令（副本）

```bash
# 在 agateon 副本中，分别把 hook 指向两个版本的协议
cat > .git/hooks/pre-commit <<EOF
#!/bin/bash
export AGATE_ROOT=<协议根>/agate      # 分别取 a68d763 与 720c97d3 的 worktree
exec python3 <协议根>/agate/scripts/pre-commit-gate.py "\$@"
EOF
# 然后原样运行问题单 §3 的探针
```

---

## Q1：G3 归属

**裁决：G3 作为"缺陷"不成立，RM-AG0100 应以"误诊（版本错位）"关闭。** 关闭时附上 Q2 的复现结果和教训：探针必须记录实际解析到的协议版本（`agate-resolve.py`）。

剩下两件真实的事，都归 **A3**：

| 事项 | 归属 | 依据 |
|---|---|---|
| 进入 PAUSED / READY / DONE 的转换事件随本次提交入库（BDD-38），含 `prod_touched_in_paused`（cso MEDIUM-3） | **A3** | 让这个 Then 成立的改动，是 A3 把 2h.1c/d 前移到 2g 之前 |
| 2h.1d 的 `git add` 失败时可见（检查返回码，失败则 WARNING） | **A3** | 改的是同一行代码 |

**判据：单一 owner = 让该 Then 成立的那次改动所在的批。** 主题领域（"账本信任链属于 A1"）适合用来组织评审视角，不适合用来分配归属。如果改动落在 A3、验收锚却挂在 A1，A1 的 BDD 在 A3 合入之前不可能为真，就会形成一个"跨批依赖却无法独立验收"的锚。

**对 cso 关切的回应**：账本信任链的**强制力**并不依赖"事件是否入库"。A1 的账本七条规则和 A2 的 CI 回放，都是在暂存或提交的内容上独立判定的（cso 自己在 §1.3 也确认了这一点）。所以 G3 不构成对 A1 的阻塞。

**相应调整**：
- BDD-01（A0）的 Then 只断言"事件写入工作区账本"；
- "committed ledger 含该事件"的断言放到 A3（BDD-38 一并覆盖）；
- A3 的验收用例必须用**真实的 `git commit` 加上指向 checkout 协议的 hook**，不能只手动调用脚本，否则会重演 Q2 的误诊。

**cso BLOCKER-2 的结论**：前提已经消失，可以降为 MEDIUM（即 MEDIUM-3，归 A3）。

---

## Q3：`P5_r6_differential`

**选路线 ①（A1 交付脚本），但不能照原样"脚本 + 一个 `.` 参数"，要改成下面的形态。**

### 为什么不选 ②

§8"legacy 的 gate 退出码与 ERROR 集合不变，允许的差异是这 12 项"，是本任务对存量 137 个任务目录的唯一兼容承诺。如果改成"各批过程性 checklist"，就等于让这条承诺依赖记忆来保证，与 TAG0050 的立项主旨直接矛盾。同时，它也是每一批都要重复做的检查，正适合用一个脚本做唯一来源。

### 为什么不能照原样

原 gate 命令是 `bash r6-differential.sh .`，有两个问题：
- 只有一个参数，无法覆盖 peekview（P5 环境不保证有 peekview 副本，gate 命令又是固定字符串）；
- "差异是否属于允许的 12 项"目前写在散文里，脚本无从判断。

### 建议规格（A1 交付物，带 BDD 锚和负向用例）

1. **接口**：

   ```
   r6-differential.sh --before <rev> --after <dir> --corpus <repo>... [--allow <file>]
   ```

   - `before` 缺省为 `merge-base HEAD origin/main` 的 `agate/`；
   - `after` 缺省为工作树中的 `agate/`；
   - 所有运行都在 `mktemp -d` 副本里进行，跑完后**脚本自己**核验每个 corpus 原仓库的 `git status --porcelain` 为空，否则 exit 1。这样就把 AGENTS.md 工作流 0a 变成了一条机械判据。
2. **判定**：对每个 legacy 任务、每个相关 gate，比较 (退出码, ERROR 行集合)。差异必须匹配 `r6-allowlist.yaml` 中的某一条，否则 exit 1。设计 §8 的 12 项要改写成机器可读的匹配规则（类别 + 匹配式 + 所属批）。
3. **gate 命令**：只跑 agateon 自身的语料，结果完全可复现：

   ```
   P5_r6_differential: "bash docs/design-notes/r6-differential.sh --corpus ."
   ```

4. **peekview 部分**：每批在 P6 中用同一个脚本、加 `--corpus <peekview 副本>` 运行，输出作为证据文件，由 D3 绑定。这部分是"外部仓库"，如实作为过程证据，不放进 gate。
5. **负向用例**：在 allowlist 中删掉一条真实需要的规则，脚本必须变红（满足 eng 测试缺口 ①）。

---

## Q4：F4 安全门的规格

### 实测：口径与扫描面扩大后的影响

扫描范围：两个仓库全部任务目录下的全部 `*.md`，包括 progress、dispatch-context、`AGATE_CARD` 块内的内容。

| 口径 | agateon 命中 | peekview 命中 | 新增误拦 |
|---|---|---|---|
| 现行 `^\s*-?\s*\[PROD_TOUCHED\]` | 0 | 2 | — |
| `markers.yaml` 的 default 口径 | 0 | 2（与现行相同） | **0** |

两处命中都是 peekview T039 的否定写法 `- [PROD_TOUCHED]: 无`（`P4-progress.md:21` 和 `P4-implementation/implementation.md`），新旧口径都会命中。存量语料中**从来没有出现过**真实的正向 PROD_TOUCHED 声明。

### 规格

1. **单一来源**：
   - `markers.yaml` 中 `PROD_TOUCHED` 的 `lead_variant` 由 `dash_only` 改为 `default`；
   - `pre-commit-gate.py:348/355` 删除字面正则，改为 `agate_markers.pattern("PROD_TOUCHED")`；
   - 这样就消除了 cso 指出的"注册表与 T1 口径分叉"；`mk_3`（render ⊂ pattern）会继续守护这一点。
2. **扫描面**：对每个有暂存文件的任务目录（§2.3 规则 7），扫描**全部暂存的 `*.md` 文件**的新增行（`git diff --cached -M`），**不限于声明文件**。只排除 `AGATE_CARD` 块（保持现状），不额外排除围栏或行内代码。对安全门来说，宁可多拦；而实测表明多拦的代价为 0。
3. **职责划分**：
   - **T4 = 唯一的 PROD_TOUCHED 安全门**，按上述规格实现，§3.6 删去"保持原样"；
   - **T1 的标记表中去掉 PROD_TOUCHED**，避免两条路径判定同一件事。
4. **否定写法**：`[PROD_TOUCHED]: 无` **继续阻断**（安全门 fail-safe）。报错信息要专门说明："疑似否定写法：未触达生产请在主产出写 `prod_touched: false`，并删除正文中的标记。"
   - 用正则去识别"这是否定"，正是本任务要根除的做法，所以"误拦"这个问题靠**指引**解决，而不是靠改正则；
   - 对 legacy 任务，这与现状一致（现状也会拦），不属于 §8 的新差异；
   - BDD-55 按这个意思改写（cso MEDIUM-1）。
5. **补锚**：在**非声明文件**（`P4-progress.md`）中写粗体或引用块形式的正向 `[PROD_TOUCHED]`，同时字段写 `false` → 中止提交。这满足 cso BLOCKER-1 的要求。

### 威胁模型补充（供定级参考）

T4 能拦住的是"**诚实但沿用旧习惯**"的声明，拦不住"**说谎的 agent**"：一个想隐瞒的 agent 根本不会写这个标记。所以 cso 描述的"残留绕过"（字段写 false，同时在 progress 里写粗体标记）本质上是**同一个 agent 前后不一致**，不是对抗性绕过。它仍然值得拦，而且成本为 0，但不应据此推断"T4 能防谎报"。防谎报需要旁证（例如 cmdstream），这已在设计 §1 的边界中声明，建议在 §4 再写一句。

---

## 附：`P5_repro` 同样是"不会变红的 gate"（新发现，与 B1 同类）

- `repro-tag0050.sh` 是**演示脚本**：它打印各个缺陷的现状，不做断言。退出码取决于最后一条命令，与"缺陷是否已修复"无关。
- 更根本的问题是：它构造的篡改全部作用在 **legacy 任务**（TAG0001、TAG0037、TAG0042）上。而按设计 §8，legacy 的行为**保持不变**，所以 TAG0050 实现完成后，它**仍然会显示 F1、F2、F3a 等绕过**，而这恰恰是正确的结果。
- 这个脚本是我写的，设计中"`P5_repro` 复现 F1–F15（改坏即红）"的说法不成立，我负责更正。

**建议**：从 `gate_commands` 中删除 `P5_repro`，改为两项：
- 各批验收锚中"先红后绿"的 pytest 用例：在**非 legacy 的 init 任务**上构造同样的篡改，断言判为 FAIL。这些用例已经分布在设计 §10 各批的锚里；
- `repro-tag0050.sh` 保留为证据文档，不再作为 gate。

---

## 对其余项的简要意见（非阻塞）

| 项 | 意见 |
|---|---|
| eng M2（RM-AG0101，归 A3 单 owner） | 同意。 |
| eng G1（`main()` 单点早检） | 同意。 |
| eng N2（`-k` 零匹配时 exit 5） | 同意，并建议三个 fitness 测试在 P3 中先以失败状态存在。 |
| cso MEDIUM-2（required 是锚点成立的前提） | 同意，写进 §2.4 和 `env_constraints`；未获许可时，回放降级为 advisory。 |
| cso MEDIUM-4（D3 在事件缺失时的行为） | 同意 fail-closed，并区分"事件缺失"和"sha256 不匹配"两种报错。G3 消解后，"事件缺失"只会出现在 `--no-verify` 或 A3 之前的历史中。 |
| cso LOW-1 / LOW-2 | 同意。 |

## 修订后对 P2 的整体判断

去掉 G3 之后，阻塞项只剩两类问题，两类都只需改规格，不改设计路线：
- **gate 不可执行，或不会变红**：B1，以及上面新发现的 `P5_repro`；
- **F4 的规格矛盾**（BLOCKER-1）。

按上面的方式收口后，建议在 P2 修订时重派**单一评审**，确认 B1、BLOCKER-1 和 `P5_repro` 三项已闭合即可，不必重开全量评审。
