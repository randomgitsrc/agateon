---
status: needs-revision
agent: protocol-alignment-review
reviewed_at: 2026-09-29
---
# SELF-GATE 评审：worktree 必需性主张

被评审改动（未提交）：`AGENTS.md`、`docs/guides/worktree-dogfooding-guide.md`、
`agate-workspace/tasks/TAG003{8,9}/P0-brief.md`、`agate-workspace/tasks/TAG004{0,1}/P0-brief.md`。

## 结论

**核心事实主张成立**——"改本 checkout 的 `agate/` 不影响 gate 判定"在当前本机环境（无 `AGATE_ROOT` env、
无 `.agate-version`、`~/.agate` 为版本管理布局且 `current` 链有效）下经独立复现为真，
"worktree 不再是正确性要求"以及"独立评审由 commit message 机制提供、与 worktree 无关"两条均成立。
**但不应按现状提交**：同一份被改的 guide 内部自相矛盾（新 banner 说"非必需"，同文件第 239 行仍写"**必须**走 worktree"），
4 份 P0-brief 引入了 Markdown 换行丢失的机械损坏，且有两条会改变判定归属的残留耦合路径未在正文中交代。

## 逐条核实

候选耦合路径穷举（问题：能否把 gate 判定指向开发 checkout？）：

| # | 候选路径 | 能否指向 checkout | 证据 |
|---|---------|------------------|------|
| 1 | **cwd 相对回退**（问题核心） | **否** | `resolve_hook_root`（`agate_common.py:386-408`）次序为 `AGATE_ROOT env` → `_resolve_version_info` → 脚本路径上溯兜底；前两层均不读 cwd。决定性实测：把 **dev checkout 的**脚本路径喂进去 `resolve_hook_root('/home/kity/oclab/agateon/agate/scripts/resolve-entry.py')` → 返回 `/home/kity/.agate/v0.76.0/agate`（**非** checkout），gate_path 存在。cwd 只被 `_find_project_declaration` 用于向上找 `.agate-version`，不参与"工具根"解析 |
| 2 | **`AGATE_ROOT` env** | **能（残留路径）** | 实测 `AGATE_ROOT=/home/kity/oclab/agateon/agate python3 ~/.agate/scripts/agate-resolve.py` → `AGATE_ROOT=/home/kity/oclab/agateon/agate`、`AGATE_REASON=AGATE_ROOT 环境变量覆盖`、exit 0。且 `pre-commit-gate.sh:8` 自身也用 `${AGATE_ROOT:-…}` 作 `ENTRY_ROOT`——**同一变量在 shell 与 python 两层都优先**。当前本机 `AGATE_ROOT` 未设置，故现状安全；但这是环境依赖，非结构保证 |
| 3 | **`AGATE_HOME`** | 否（间接可致 #6） | `agate_home()`（`agate_package.py:587-592`）只换"版本根在哪"，不改层序。实测 `AGATE_HOME=/tmp/nonexistent` 不指向 checkout，而是使版本链失败 |
| 4 | **项目 `.agate-version`** | 否 | 正则 `^\s*agate\s*:\s*(v[0-9]+\.[0-9]+\.[0-9]+)$` 只接受 `vX.Y.Z` 版本名，**无法表达仓库相对路径**；解析结果 = `<base>/<version>/agate`，base 恒为 `~/.agate` 或 `AGATE_HOME`。实测本仓及 4 级祖先均无 `.agate-version`（`/home/kity/oclab/agateon`、`/home/kity/oclab`、`/home/kity`、`/home` 全 absent）→ 实测 `AGATE_REASON=全局 current` |
| 5 | **`core.hooksPath`** | 否（对 gate 根无影响） | `git config --get core.hooksPath` exit 1（未设置）。即便被设为相对路径，它只改**哪个 hook 文件被执行**；hook 是薄壳，最终 gate py 仍由 `resolve-entry` 的 `resolve_hook_root` 决定（第 1 行）。`install-hook.py:176-190` 的 cwd 相关告警针对装/卸位置，不针对 gate 根 |
| 6 | **hook 自定位兜底（脚本路径上溯）** | **能（残留路径，条件性）** | `resolve_hook_root` 的末段兜底：版本链**全部失败**时返回脚本自身所在 `agate/`。实测 `AGATE_HOME=/tmp/nonexistent` + dev 脚本路径 → 返回 `/home/kity/oclab/agateon/agate`，即 checkout。触发条件：`current`/`latest` 链不可解析（版本布局被破坏 / 未安装 / 纯复制模式）。这是主张的**精确边界** |
| 7 | **稳定版实际文件** | 否 | `~/.agate/scripts/agate_common.py`、`~/.agate/v0.76.0/agate/scripts/agate_common.py` 与 dev checkout 三者内容相同但 **inode 互异**（2751704 / 1328923 / 422270），非硬链——改 checkout 不穿透稳定版 |
| 8 | **hook 安装来源** | 否 | `agate-install.py:159` `repo = os.path.join(agate_home, "repo")`——版本目录从 `~/.agate/repo` 构建，**不**从开发 checkout 构建 |

次要主张核实（独立评审 = commit message 机制、与 worktree 无关）：**成立**。
`agate/scripts/commit-msg-self-gate.py` 全文只做两件事：`git diff --cached --name-only` 匹配 `_SELF_GATE_RE`
（:38-41，触发面 `agate/scripts/*.{sh,py}` / `agate/*.md` / `agate/**/*.md` / `agate/rules/*.ya?ml` / `SELF-GATE.md` / `README.md` / `AGENTS.md`），
再要求 commit message 文件含 `self-gate-review:` 或 `self-gate-skip:`（:42-43）。全文无 `worktree` 字样，不依赖工作目录形态。
`grep -rn 'worktree' agate/scripts/*.py` 命中 8 个文件，逐条判读后**无一条强制 worktree**：唯一含 `必须` 的命中是
`agate_common.py:134` 的注释（描述 `git worktree list --porcelain` 的宿主判定，非门禁），其余均为路径/文档字符串。
另注：该 hook 只 WARN 不拦截（:6、:77-83），`SELF-GATE.md`「强制力边界」节自认"真正强制力依赖主 Agent 自觉"——所以"独立评审由该机制提供"应读作"**留痕提示**机制"，不宜表述为强保证。

## 反例搜索

**找到反例（4 类）**：

1. **同一文件内部自相矛盾（最严重）**。被改的 `docs/guides/worktree-dogfooding-guide.md` 新增 banner 称
   "worktree 不是正确性要求"（:13-31），但**同一文件未被更新的后文**仍写：
   - `:239` **默认：agate 自身改造任务（P0-P8）必须走 worktree**
   - `:246` hotfix 条件 2 "**不触发 SELF-GATE**（不碰 `agate/` 下任何文件…）"
   - `:252` "**不适用**：任何 `agate/` 协议本体/脚本改动（SELF-GATE）"
   - `:198` "`check-protocol-consistency.py` 必须用 **worktree 自己的**"
   
   `AGENTS.md` 的对应段已改为"不立项/分支+PR/轴 B"，而 guide 的同一节没改 → 两份文档现在对同一问题给出相反指令。
   这正是 `AGENTS.md:27` 自陈要修的"混同"问题，在 guide 里**原样残留**。

2. **机械损坏：换行丢失（新增缺陷，非既有）**。4 份 P0-brief 的新 bullet 与下一 bullet 被粘成一行：
   `git diff` 显示删掉了两个独立 bullet，新增行以 `` …\`HANDOFF-TAG00NN.md\`- **稳定版工具**：… `` 结尾。
   实测 `grep -o 'md\`- \*\*稳定版工具\*\*'` 在 TAG0039/0040/0041 各命中，TAG0038 为 `填写- **稳定版工具**`（粘连形态稍异）；
   同时 `流程见 \`docs/guides/worktree-dogfooding-guide.md\`` 在**同一行内重复出现 2 次**（4 份文件皆然）。
   后果：后续 bullet 失去列表项身份，"稳定版工具：`~/.agate/scripts/`（勿动）"这条纪律在渲染后并入上一条。

3. **残留耦合路径未交代**：#2（`AGATE_ROOT` env）与 #6（版本链失败→脚本路径上溯）都能把判定指向 checkout，
   但新表述以"**无 cwd 相对回退**"作为"改 checkout 不影响判定"的充分理由，未标注这两个前提。
   `agate/orchestrator-template.md:20` 恰恰教人"优先用环境变量 `$AGATE_ROOT`（若已设置）"——
   开发者按此在开发会话里 `export AGATE_ROOT=<checkout>/agate` 时，**gate 就会用 checkout 的脚本判自己**，
   即主张声称已"结构性解除"的场景可被合法途径重现。**当前本机**未设置该变量，故现状为真。

4. **未同步的兄弟文档（会造成读者误判）**：
   - `docs/guides/project-map.md:27` "正常改动走 worktree（hotfix 例外…）"、`:72` "自我改造（dogfooding）走 worktree 隔离双工作区"
   - `agate/assets/templates/handoff-template.md:15` "工作区布局（**双工作区纪律，违反必出事故**）"、`:28`/`:65` "必须用 worktree 自己的"
   - `AGENTS.md:17` 节标题仍为 "改动通道：worktree **优先**，hotfix 例外"（正文已改为"隔离选择"，标题与"hotfix 例外"措辞均滞后）
   - `docs/design-notes/` 4 处（`design-structured-layer.md:170` 等）仍以"双工作区纪律"为设计前提；属历史设计记录，严重度低，但 `project-map` 与 `handoff-template` 是活跃操作文档。

**未找到反例的项**：无任何 `cwd` 相对回退；无任何 `agate/scripts/*.py` 强制要求 worktree；
`.agate-version` 无法表达 checkout 相对路径；hook 目标确为 `~/.agate/scripts/*.sh`（`readlink -f .git/hooks/pre-commit` → `/home/kity/.agate/scripts/pre-commit-gate.sh`）。

## 真空通过自检

逐条说明所引证据的成立前提，以及如何排除"输入不存在与输入合规输出相同"：

| 证据 | 前提 | 是否真空 | 排除方式 |
|------|------|---------|---------|
| `agate-resolve.py` → `AGATE_ROOT=~/.agate/v0.76.0/agate`、`REASON=全局 current`、exit 0 | 必须**确实没有** `.agate-version` 且 `current` 可解析 | **否** | 已单独验证 4 级祖先目录全无 `.agate-version`，并 `readlink -f ~/.agate/current` → `/home/kity/.agate/v0.76.0`。两个分支的判别输入都被显式检查，非"文件缺失导致的巧合通过" |
| `git config --get core.hooksPath` **exit 1** | exit 1 = key 不存在 | **是（负面结果）** | 不单独作为"hook 位置正确"的证据；仅用作"无 hooksPath 覆盖"的辅证，主证是 `readlink -f .git/hooks/pre-commit` 与 `git rev-parse --git-path hooks`，二者指向真实存在的 `~/.agate/scripts/` 目标 |
| `AGATE_ROOT=<checkout>` → resolve 返回 checkout、exit 0 | 该变量**已设置**时 | **否** | 显式设置了变量并观察到输出随之改变（`REASON=AGATE_ROOT 环境变量覆盖`）——输入变化→输出变化，证明该层确为活路径，非恒真 |
| `AGATE_HOME=/tmp/nonexistent` + dev 脚本 → 返回 checkout | 必须确实进入"版本链失败"分支 | **否** | 输出由稳定版切到 checkout，与默认运行结果**不同**，证明分支真实触发；同时说明该兜底仅在此条件下生效 |
| `grep -rn 'worktree' agate/scripts/*.py` 命中后判"无强制" | 命中需逐条判读 | **否** | 未把"无匹配"当证据（确有匹配）；逐条区分注释/文档串与门禁代码，并定位唯一 `必须` 命中为 `agate_common.py:134` 注释 |
| 4 份 brief 换行丢失 | 需排除"原本就粘在一起" | **否** | 依据 `git diff` 中同批 `-`/`+` 行对照（两个 bullet 被删、一个粘连行被加），证明由本次改动引入 |
| `diff -q` 三方脚本"IDENTICAL" | 需内容确有可比性 | **否** | 同时用 `stat -c %i` 验证 inode 互异，避免"同一文件被比较两次"式假阳性 |

## 遗留问题 / 建议

1. **（阻断）修 guide 内部矛盾**：`worktree-dogfooding-guide.md:237-254`（对照行 239/246/252）整节需按 `AGENTS.md` 新三轴口径重写——
   删除"（P0-P8）**必须**走 worktree"、把 hotfix 条件 2 从"不触发 SELF-GATE"改为"不是 agate 任务"、
   把"不适用：任何 `agate/` 改动（SELF-GATE）"改为"须立项 + `self-gate-review:` 留痕，**worktree 按轴 B 判断**"。
   否则读者同时读到"必须"与"非必需"，无法据以行动（这比原主张的错误更难排查）。
2. **（阻断）修 4 份 P0-brief 的换行丢失与重复短语**：在 `` …HANDOFF-TAG00NN.md` `` 与 `- **稳定版工具**` 之间补回换行，
   并删除重复的"流程见 `docs/guides/worktree-dogfooding-guide.md`"（各 1 处）。
3. **（建议）把"无 cwd 相对回退"升级为带前提的表述**：改为"**当 `AGATE_ROOT` 未设置且版本链可解析时**无 cwd 相对回退"，
   并补一句：设了 `AGATE_ROOT=<checkout>/agate`（`orchestrator-template.md:20` 教人优先用它）或版本链失效时，
   判定会回落到 checkout/脚本路径上溯——后者可由 `agate-resolve.py` 的 `REASON` 一眼识别，建议把它写成提交前的自检命令。
   理由：主张的强度来自"结构性"，而这两条路径是环境性的，不加前提会把"当前本机为真"误述为"永远为真"。
4. **（建议）同步兄弟文档**：`project-map.md:27,72`、`handoff-template.md:15,28,65`、`AGENTS.md:17` 标题
   （"worktree 优先，hotfix 例外" → 与新三轴口径对齐）。`handoff-template.md` 尤其重要——它被"决定开 worktree 时"复制使用，
   现在会同时教读者"双工作区纪律，违反必出事故"与"worktree 非必需"。
5. **（提示）不要把 `self-gate-review:` 机制表述为"独立评审已由机制保证"**：该 hook 只 WARN 不拦截
   （`SELF-GATE.md`「强制力边界」自陈强制力依赖主 Agent 自觉）。建议措辞为"独立评审的**留痕检查**由 commit message 机制承担"，
   否则把"提示"读成"保证"。worktree 与评审无关这一判断本身正确，不受此影响。

---

## 处置记录（主 Agent，2026-09-29）

**评审 status = needs-revision；以下为逐条处置。评审原文保留不改，便于追溯。**

| # | 评审项 | 处置 |
|---|--------|------|
| 1 | （阻断）guide 内部矛盾 | **已修**：`worktree-dogfooding-guide.md` 改动通道节按三轴口径重写（删"必须走 worktree"、hotfix 条件 2 改"不是 agate 任务"、"不适用"改为须立项 + `self-gate-review:` 留痕 + worktree 按轴 B 判断） |
| 2 | （阻断）4 份 P0-brief 换行丢失 + 重复短语 | **已修**：补回换行、删除各 1 处重复的"流程见 …guide.md" |
| 3 | （建议）主张需加前提 | **已采纳**：`AGENTS.md` 与 guide 均补「前提 = `AGATE_ROOT` 未设置 且 版本链可解析」，列出两条**确实能**指向 checkout 的路径（`AGATE_ROOT` env / 版本链失败→脚本路径上溯），并给自检命令 `agate-resolve.py` 看 `AGATE_ROOT=` |
| 4 | （建议）同步兄弟文档 | **已修**：`handoff-template.md`（标题改"工作区布局"，补"仅选择开 worktree 时使用"；纠正"主 checkout 是稳定版来源"这一**事实错误**；软链表述改为版本管理根目录）、`project-map.md:27,72`。`AGENTS.md:17` 标题保留"worktree 优先，hotfix 例外"——正文首段已用三轴表更正，标题属于既有稳定锚点（多处引用），改名会引入新的引用漂移 |
| 5 | （提示）不要把 `self-gate-review:` 表述为"机制保证" | **已采纳**：三处改为"须独立评审；**留痕**由 `self-gate-review:` 检查（仅 WARNING 不拦截，强制力靠自觉）" |

**核验**：`check-protocol-consistency.py` 386 WARNING / 0 ERROR（与基线一致）；相关 pytest 218 passed。

**元教训**：本次我自己在被评审的改动里犯了正在记录的错——只改了 guide 的 banner、留着正文说"必须"（第 1 条）；以及用脚本插入文本时丢了换行、重复了短语（第 2 条）。**独立评审把这两处抓出来了**，且第 3 条把"当前本机为真"与"永远为真"区分开——这正是本仓反复出现的"时点快照当普遍事实"同族。
