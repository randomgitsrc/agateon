---
phase: P7
task_id: TAG0032
type: consistency
parent: P2-design.md
trace_id: TAG0032-P7-20260907
status: approved
created: 2026-09-07
agent: consistency-reviewer
# ── v2.0 机器计数 ──
blocker_count: 0
deviation_count: 1
deviation_critical_count: 0
design_gap_count: 5
design_gap_reviewed_count: 5
code_map_new_files_count: 2
code_map_reviewed_count: 2
---

# P7-consistency — TAG0032 版本管理生命周期可用性批 跨文件一致性审查

[PROD_NOT_TOUCHED]
[NO_NEED_CONFIRM]

> 审查对象：P1-P6.5 全部产出 + 实现侧第一手锚点核验（只审不改，无 worktree git 写操作）。
> 审查时 .state.yaml phase=P7；worktree HEAD `5f08bf8`（P6.5 commit）。
> 输入：dispatch-context 清单全读（P7 输入数量豁免）——P0-brief / P1-requirements / P2-design /
> P2-review / P4-implementation（批1 + 批2 + fix-1）/ P4-review（复评轮 approved）/
> P5-test-results/unit.md / P6-acceptance / P6.5-judge-verdict / known-failures.md / CODE-MAP.md /
> consistency-reviewer.md（角色定义）。
> 实现侧核验：`git diff 3f3cc01..HEAD -- agate/ install.sh README.md README.zh-CN.md` 逐 hunk 读；
> `agate/scripts/agate_common.py` `_protocol_root` / `_resolve_version_info` 两处调用点；
> `agate/scripts/agate-install.py` `_sync_root_scripts` / `_ensure_repo` / `main()` `latest` 别名 /
> `_LEGACY_SYMLINK_MSG`；`install.sh --versions` 分支；`agate_common.py:50` `run_git` 返回契约；
> `agate/UPGRADING.md` 生命周期节 diff；`test_upgrading_lifecycle.py` 断言逐条。

结论：**status: approved**。blocker_count=0，deviation_critical_count=0。5 处 DESIGN_GAP 逐条转抄 +
配 REVIEWED（design_gap_reviewed_count == design_gap_count == 5）。SCOPE+ 全流程无产生 → N/A。
跨文件一致性 4 项各有结论 + 具体锚点。CODE-MAP 2 个新增文件均测试文件 → `[CODE_MAP_SYNC:]`。
发现 **1 处非关键偏差**（deviation_count=1）：`agate/UPGRADING.md`「版本管理生命周期 › 根
`~/.agate/scripts/` 维护语义」段的实现机制描述滞后于 P4 fix-1（详见 §3.3 与 DESIGN_GAP 1 REVIEWED）——
用户可见承诺（副本非软链 / 重跑刷新 / repo 被删不影响）不受影响，非阻塞，建议 P8 顺手修订。

---

## 1. DESIGN_GAP 配对（P4-implementation.md 行首 [DESIGN_GAP:] → 本文件逐条转抄 + [DESIGN_GAP_REVIEWED:]）

`grep -nE '^\[DESIGN_GAP' agate-workspace/tasks/TAG0032-version-lifecycle/P4-implementation.md` →
5 处：L55 / L56 / L57 / L58（批 1「决策/偏差声明」四条）+ L118（批 2「决策/偏差声明」一条）。
`design_gap_count: 5`。gate_p7 走 frontmatter 结构化计数判定（`design_gap_reviewed_count: 5` ==
`design_gap_count: 5`）；下述逐条转抄 + REVIEWED 为人类痕迹与实质锚点。

裁决方法：不盲信主 Agent 建议措辞——独立读 P4-review 复评轮逐条核查、P4-implementation.md fix-1 节
（§①/②/③/④）、`git diff 3f3cc01..HEAD` 实际代码，逐条判定裁决理由是否成立。

### DESIGN_GAP 1（M2 双 copytree）

原文逐字转抄（P4-implementation.md:55，批 1「决策/偏差声明」）：

[DESIGN_GAP: P3 fixture `_tag_upstream`/`_tag_meta_upstream` 的 `agate/scripts/` 均不含 `agate-install.py`，但 BDD-3/4/4b/5/13 都断言 `~/.agate/scripts/agate-install.py` 存在且 `--help` exit 0；单按 dispatch 字面「src = _protocol_root(vdir)/scripts」单次 copytree 无法转绿。M2 自主采用「自拷贝运行中安装器 scripts/ 目录 + 叠加版本协议 scripts/」双 copytree。]

[DESIGN_GAP_REVIEWED: 已确认——本条已在 P4 fix-1 §③ 消解并回退 P2-design §3 决策 B1 单源 copytree，独立核对成立。核对锚点：① `git diff 3f3cc01..HEAD -- agate/scripts/agate-install.py` 的 `_sync_root_scripts` 函数体为**单段** `shutil.copytree(proto_scripts, dst, dirs_exist_ok=True)`，`proto_scripts = os.path.join(_protocol_root(version_dir), "scripts")`——layer-1（自拷贝运行中安装器 scripts/）在 HEAD diff 中不再出现，与 P2-design §3 候选 B1「单源 `shutil.copytree(src, …, dirs_exist_ok=True)`」（P2-design.md §3 L140-141 / L164-167）一致；② fix-1 §② 配套把 `_tag_upstream`（`test_agate_version_install.py`）与 `_tag_meta_upstream`（`test_version_lifecycle_e2e.py`）纯增量补 `agate-install.py` + `agate_common.py`——贴近 P1-requirements §3.4「版本工具随协议仓在 repo/agate/scripts/」的真实元仓库形态，属补 fixture 缺口非放宽判据（P4-review 复评核查项 2 PASS：无 assert 改动 / 无删用例）；③ 遗留副作用见 §3.3——批 2 P4-implementation.md 的 UPGRADING.md「维护语义」段仍按 fix-1 前的双 copytree 撰写「运行中安装器自带 scripts/ 叠加 current 版本协议 scripts/（后拷贝者胜）」，代码回退单源后该机制描述滞后（deviation_count=1，非关键）。跨文件引用：P2-design §3 candidate B1 / P4-implementation fix-1 §③ / P1 §3.4 BDD-4 判据 2。]

### DESIGN_GAP 2（`latest` 别名）

原文逐字转抄（P4-implementation.md:56，批 1「决策/偏差声明」）：

[DESIGN_GAP: `agate-install.py main()` 原不认 `latest` 参数（落 `_VERSION_RE` 失配 → exit 2），但 P1 §3.4 步骤 5 / e2e BDD-13 步骤 5 / install.sh --versions / BDD-2 迁移指引均用 `agate-install.py latest`；M 表未列该别名。自主在 main() 增 `latest` 作无参 install 别名。]

[DESIGN_GAP_REVIEWED: 已确认——P1 隐含要求、P2 M 表遗漏的合理补全，独立核对成立。核对锚点：① P1-requirements.md BDD-2 判据 3 明列「命令片段匹配 `agate-install.py` 且带版本标识（`latest` / `v<X.Y.Z>` / `--versions` 三者其一）」，BDD-13 When「再次 `agate-install.py latest`（验幂等）」、Then 判据 5「再次 `agate-install.py latest`（幂等复跑）→ exit 0」——`latest` 字面是 P1 BDD 显式要求；② P2-design §1.1 M1-M15 表 + §4.2 未把 `latest` 别名列为独立 M 项（遗漏），非设计否决；③ `git diff` 确认 `main()` 改为 `if not args or (len(args) == 1 and args[0] == "latest")` → `_cmd_install(agate_home)`，`_usage()` 文案同步——纯别名映射到既有无参 install 路径，无新语义、幂等由既有 `_install_version`/`_write_pointer` 保证（P6 BDD-13 判据 5 PASS）；④ P4-review 复评核查项 6 判「保留待 P7 配对」，本轮确认合理。跨文件引用：P1 §3.4 BDD-2/BDD-13 / P2-design §1.1 M 表 / P4-implementation main() 别名。]

### DESIGN_GAP 3（`install.sh --versions` exec 路径）

原文逐字转抄（P4-implementation.md:57，批 1「决策/偏差声明」）：

[DESIGN_GAP: dispatch M6 写 `python3 ~/.agate/repo/agate/scripts/agate-install.py latest`，但 e2e `_tag_meta_upstream` 故意不放 `agate-install.py` 进协议目录（模拟元仓库 gap）。install.sh --versions 自主改为 `exec "$SCRIPT_DIR/agate/scripts/agate-install.py"`（install.sh 同侧脚本），`~/.agate/repo` 仅作 `git worktree add` 版本源。]

[DESIGN_GAP_REVIEWED: 已确认——本条批 1 形态（`$SCRIPT_DIR` 旁路）经 P4-review **首轮 CRITICAL**（`curl … | bash -s -- --versions` 场景 `$SCRIPT_DIR` = 工作目录无 `agate/scripts/` → EXIT=2，新机官方路径断裂），已在 P4 fix-1 §① 按 P4-review 首轮**选项 A** 消解并回归 P2-design §4.2 M6 意图。核对锚点：① `git diff 3f3cc01..HEAD -- install.sh` `--versions` 分支 exec 行为 `INSTALLER="$AGATE_HOME/repo/agate/scripts/agate-install.py"` / `[ -f "$INSTALLER" ] || INSTALLER="$SCRIPT_DIR/agate/scripts/agate-install.py"` / `exec "$PY" "$INSTALLER" latest`——刚 `git clone` 的 `$AGATE_HOME/repo/…` **优先**、`$SCRIPT_DIR` 仅 `[ -f ]` 兜底，与 P2-design §4.2 M6「用刚 clone 的 `~/.agate/repo` 内安装器」意图对齐；② fix-1 §② 两 fixture 补 `agate-install.py` 后主路径可被测（P4-review 复评核查项 1 PASS：独立复现 `cat install.sh | bash -s -- --versions` 隔离 HOME EXIT=0、实走主路径、兜底未触发）；③ P6-acceptance BDD-5 额外实测 transcript + P6.5-judge BDD-5 独立重验均 PASS；④ P4-review 复评 `status: approved` / 0 CRITICAL（trace_id TAG0032-P4review-re1-20260907）。跨文件引用：P2-design §4.2 M6 / P4-implementation fix-1 §① / P1 §3.4 BDD-5 + BDD-13。]

### DESIGN_GAP 4（`_ensure_repo` git fetch）

原文逐字转抄（P4-implementation.md:58，批 1「决策/偏差声明」）：

[DESIGN_GAP: BDD-4 判据 2 要求「重跑 latest 后副本随 current 刷新」在新增更高 tag 后成立，但既有 `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时从不 fetch，永远看不到上游新 tag。自主在 `_ensure_repo` 已有 repo 分支加 `git fetch --tags --force --prune origin`（fail-open）。属 TAG0032 update 路径范围。]

[DESIGN_GAP_REVIEWED: 已确认——落在 P0-brief scope「Phase 3（update 统一入口）」范围内，fail-open 属实，独立核对成立。核对锚点：① `git diff 3f3cc01..HEAD -- agate/scripts/agate-install.py` `_ensure_repo` 已有 `repo/.git` 分支新增 `run_git(["fetch", "--tags", "--force", "--prune", "origin"], cwd=repo)`，返回值被忽略；② `agate_common.py:50` `run_git` 定义——`try: subprocess.run(...) return proc.returncode, proc.stdout / except OSError: return 1, ""`，**不抛异常**，返回码被忽略 → 离线/fetch 失败不致命（fail-open 名副其实）；③ `--tags --prune`（无 `--prune-tags`）只 prune 远程跟踪引用，不删本地 tag——dispatch-context「`--force --prune` 不误删本地 tag」核实成立；④ P0-brief scope「Phase 3」+ P1 断点三「版本布局升级 = `agate-install latest` 幂等」——为使「重跑 latest 跟随更高 tag」（BDD-4 判据 2）成立所必需，非范围外扩张；⑤ P5 全量 pytest 1484 passed（run2）/ P6 BDD-9 全绿——无回归。跨文件引用：P0-brief scope Phase 3 / P1 §3.3 断点三 BDD-4 判据 2 / P4-implementation fix-1 保留不动。]

### DESIGN_GAP 5（v0.50.0 §① 表格反引号微调）

原文逐字转抄（P4-implementation.md:118，批 2「决策/偏差声明」）：

[DESIGN_GAP: P3 用例 test_tag0032_bdd_12[v050_root_scripts_row_pointer] 断言精确子串 `scripts/（版本管理工具）`，但 v0.50.0 §① 表格原文是 `` `scripts/`（版本管理工具） ``（`scripts/` 与全角括号间夹一个收尾反引号），子串不成立。M8 自主把收尾反引号右移为 `` `scripts/（版本管理工具）` ``——纯 markdown 代码格式微调，渲染后措辞与语义不变，符合 BDD-12「加指针不改叙事」。]

[DESIGN_GAP_REVIEWED: 已确认——格式微调非叙事改动，BDD-12「加指针不改叙事」判据不违反，独立核对成立。核对锚点：① `git diff 3f3cc01..HEAD -- agate/UPGRADING.md` v0.50.0 §① 表格「迁移后」列唯一变化为把 `` `scripts/` ``（收尾反引号在 `scripts/` 后）右移为 `` `scripts/（版本管理工具）` ``（整段入代码 span），行内其余文字、表格结构、升级/卸载行均未动；② 渲染后仅代码 span 边界差异，中文措辞「版本管理工具」与语义（根含 scripts/）不变——符合 P1 §3.4 扫描 4 + BDD-12 checklist 1「加指针不改叙事」；③ 同表新增 blockquote 指针「本表为版本历史叙事，不再单独维护」指向「版本管理生命周期」节，历史叙事文字保留（P2-design §4.3 checklist 1/2「历史叙事保留」判据）；④ P4-review 复评核查项 6「批 2 v0.50.0 反引号微调（首轮 D 组判 INFORMATIONAL / 可接受）不受本轮影响」；⑤ P6 BDD-12 参数化 `v050_root_scripts_row_pointer` PASS + `check-protocol-consistency.py --strict-errors-only` EXIT 0 / 0 ERROR。跨文件引用：P1 §3.4 扫描 4 BDD-12 checklist 1 / P2-design §4.3 checklist / P4-implementation 批 2 M8。]

**DESIGN_GAP 配对小结**：5 转抄 / 5 REVIEWED，`design_gap_reviewed_count == design_gap_count == 5`。
其中 GAP 1 / GAP 3 已由 fix-1 消解（分别回退 P2-design §3 B1 / §4.2 M6），GAP 2 / GAP 4 判为 P1 隐含
要求或 scope 范围内的合理补全，GAP 5 为不违反判据的格式微调。GAP 1 的文档侧遗留副作用记为
deviation_count=1（§3.3），非阻塞。

---

## 2. SCOPE+ 闭环

**无 SCOPE+，N/A。** `grep -nE 'SCOPE\+|SCOPE_RESOLVED|\[SCOPE'` 扫 P1-requirements.md /
P2-design.md / P4-implementation.md → 零命中。P1 §8「待确认清单」为 `[NO_NEED_CONFIRM]`（所有「二选一」
方向已由 P0-brief 明确划归 P2-design 决策，无需人拍板）；P2-design / P2-review 无 SCOPE+ 增补；
P4-implementation 批 1/批 2/fix-1 三处「决策/偏差声明」均为 `[DESIGN_GAP:]`，无 `[SCOPE+]` / `[BASELINE_CHANGE:]`
（P4-review 复评核查项 6 亦确认「fix-1 节无新增 `[SCOPE+]` / `[BASELINE_CHANGE:]`」）。→ 无 SCOPE+ 待闭环。

---

## 3. 跨文件一致性（逐项结论 + 具体锚点）

### 3.1 P2 packages ↔ 实际改动面 ↔ P8 bump 范围

**结论：一致。** P1/P2 frontmatter `packages: [agate-scripts, agate-docs, agate-tests]`。
`git diff --name-status 3f3cc01..HEAD` 实际改动面逐项归类：

| 改动文件 | 归属 package |
|---|---|
| `agate/scripts/agate-install.py`（M1/M2/M6 附/fix-1）、`agate/scripts/agate_common.py`（M3/M4/M5）、仓库根 `install.sh`（M6/fix-1 §①）| agate-scripts |
| `agate/UPGRADING.md`（M7/M8/M9）、`agate/SETUP.md`（M11）、`README.md` / `README.zh-CN.md`（M10）| agate-docs |
| `agate/tests/unit/test_agate_version_install.py`、`test_agate_version_resolve.py`、`test_hook_resolve_entry.py`、`agate/tests/unit/test_upgrading_lifecycle.py`（新）、`agate/tests/integration/test_version_lifecycle_e2e.py`（新）| agate-tests |

`agate/scripts/resolve-entry.py` 与 P2-design §1.2「不改什么」一致——只核对不改（决策 A1 受益方，
`resolve-entry.py:49` `os.path.join(root, "scripts", gate_py)` 在 `root=vdir/agate` 后自然命中）；
`git diff` 确认 `resolve-entry.py` 无 hunk。agateon 为单一版本号（AGENTS.md「版本发布清单」：README badge /
CHANGELOG / UPGRADING 章节 / tag 一处 bump，非多包独立发布）→ P8 bump agate 版本即覆盖上述三 package 的
改动面，无「声明包 ≠ 实际改动包」漂移。P1 §6「预期 SELF-GATE 触发文件清单」与实际改动面逐项对齐
（脚本 + 文档面 + 测试）。

### 3.2 P1 14 条 BDD ↔ P6 14 条 PASS ↔ P6.5 judge 14/14

**结论：数量匹配且逐编号对应，无内容错位。**
- P1-requirements.md §3：§3.1 BDD-1~5（断点一）+ §3.2 BDD-6~9（断点二）+ §3.3 BDD-10~12（断点三）+
  §3.4 BDD-13~14（端到端）= **14 条**，全局连续编号无跳号无重复。
- P6-acceptance.md：frontmatter `pass: 14 / fail: 0`；正文「逐条 BDD 验收结果」按 §3.1/§3.2/§3.3/§3.4
  分组列 BDD-1 至 BDD-14 各一行 PASS，每行附**具名测试函数**（`test_tag0032_bdd_1_*` …
  `test_tag0032_bdd_14_*`）+ `EXIT_CODE 0` + P6-evidence/ 证据文件名。BDD-9 无独立用例（P3 §4），
  由全量回归套件（`1484 passed, 2 skipped`）承接——P6 与 P6.5 均显式注明，非遗漏。
- P6.5-judge-verdict.md：frontmatter `criteria_total: 14 / criteria_passed: 14 / status: passed /
  partial: false`；正文「逐条结论（14 条，零挑验）」按 BDD-1 至 BDD-14 逐编号复核，每条对照 P1 §3
  Given/When/Then 原文 + P6-evidence 内容 + 测试断言交叉核对（P4 commit `1d9a322`）。
- 逐编号语义抽查（防「数量对但内容错位」）：BDD-6 → `test_tag0032_bdd_6_meta_repo_resolve_returns_agate_subdir`
  断言 `AGATE_ROOT={vdir}/agate` + `AGATE_VERSION=v0.50.0`（对应 P1 BDD-6 Then）；BDD-7 →
  `test_tag0032_bdd_7_rootproto_resolve_semantics_unchanged` 断言 `_protocol_root(vdir)==vdir` +
  `AGATE_ROOT={vdir}`（非 /agate）+ `AGATE_VERSION=v0.50.0`（对应 P1 BDD-7 Then，纯增量红线）；
  BDD-14 → `test_tag0032_bdd_14_e2e_no_source_pollution` 断言 `git status --porcelain` 无 `/repo/` /
  `/vX.Y.Z/` offender（对应 P1 BDD-14 Then）。编号↔判据对应正确。

### 3.3 P4 实现路径 ↔ P2 方案设计（决策 A1 / 决策 B1 / M1-M15 落点 / resolve-entry「只核对不改」）

**结论：基本一致；1 处非关键偏差（文档机制描述滞后于 fix-1）。**

- **决策 A1（`_protocol_root` 探测序 + `_resolve_version_info` 两处调用）** ↔ P2-design §2 候选 A1：
  一致。`git diff -- agate/scripts/agate_common.py`——新增模块级 `_protocol_root(vdir)` 紧邻
  `_resolve_version_info` 之前，探测链 `isdir(vdir/scripts) → return vdir`（探测序 1，纯增量红线）→
  `isdir(vdir/agate/scripts) → return sub`（探测序 2）→ `return vdir`（原样），与 P2-design §2 候选
  A1 代码块（P2-design.md §2 L95-103）逐行等价；两处消费点 `.agate-version` ok 分支
  `root = _protocol_root(vdir)` + `version = declared`（M4）、current 链分支**先** `version =
  os.path.basename(cur)` **再** `root = _protocol_root(cur)`（M5，diff 注释即写「顺序不可倒（I-1 红线）：
  version 从 cur 取，root 从 _protocol_root(cur) 取——两条独立」）。env 覆盖分支 / legacy 软链兜底分支
  （`if use_legacy and os.path.islink(base)`）/ `.agate-version` 格式解析在 diff 中无 hunk → 与
  P2-design §1.2「不改什么」一致。P6 BDD-6/BDD-7 + P6.5 独立重验 `AGATE_VERSION` 恒为 `vX.Y.Z`（I-1
  版本号不回归）双 fixture 全绿。
- **决策 B1（单源 copytree，fix-1 后）** ↔ P2-design §3 候选 B1：**代码一致，文档描述滞后（deviation_count=1，非关键）**。
  代码侧：`git diff -- agate/scripts/agate-install.py` `_sync_root_scripts` 为单段
  `shutil.copytree(proto_scripts, dst, dirs_exist_ok=True)`，`proto_scripts = _protocol_root(version_dir)/scripts`
  ——与 P2-design §3 候选 B1「单源 `shutil.copytree(src, os.path.join(agate_home, "scripts"),
  dirs_exist_ok=True)`」（P2-design.md §3 L140-141）一致；`_cmd_install` latest 分支
  `_sync_root_scripts(agate_home, os.path.join(agate_home, tag))` / 指定版本分支
  `…, os.path.join(agate_home, version))` 两分支源路径显式区分（对应 P2-review 核查 2c 非阻塞项）。
  P4-review 复评核查项 3 PASS（layer-1 已删，回归 B1 单源）。
  **偏差**：P4-implementation.md 批 2 §「M7『根 `~/.agate/scripts/` 维护语义条目』与批 1 实现对齐」
  及 `git diff -- agate/UPGRADING.md` 生命周期节「根 `~/.agate/scripts/` 维护语义（决策 B1：副本）」段
  仍按 fix-1 **前**的双 copytree 撰写：「内容 = 运行中安装器自带的 `scripts/` … 叠加当前 `current`
  版本的协议 `scripts/`（后者覆盖前者，后拷贝者胜）」——fix-1 §③ 删 layer-1、回退单源后，该「叠加 /
  后拷贝者胜 / 运行中安装器自带 scripts/」机制描述已不成立。影响评估：`test_upgrading_lifecycle.py::
  test_tag0032_bdd_4_root_scripts_copy_semantics_documented` 只断言「副本」「重跑 agate-install …
  latest 刷新」「repo/ …被删…影响」三点（均对单源 copytree 仍为真），故 BDD-4 判据 3 / BDD-11 判据 3
  PASS 不受影响；用户可见承诺（副本非软链 / 随 install 重跑刷新 / repo 或版本目录被删不影响副本
  可用性）全部仍准确；真实 agateon 每个 tag 的 `agate/scripts/` 恒含全套工具（P1 §3.4）→ 单源
  copytree 的净内容与双层叠加等价，无功能差异。仅「内部拷贝机制」一句陈述滞后。因 P1 I-4 / BDD-12
  的主旨是消除 doc/reality mismatch、且该节被声明为「单一权威口径」，记为 `deviation_count: 1`
  （非 critical）：**建议 P8 顺手把该句改写为单源 copytree 口径**（P8 本就编辑 UPGRADING.md 新增发布
  章节 + CHANGELOG，是自然修订点），不构成 P7 回退理由。
- **M1-M15 落点** ↔ P2-design §1.1「改什么」表：一致。M1 软链 fail-closed 守卫（`_cmd_install` 首行
  `if os.path.islink(agate_home): sys.stderr.write(_LEGACY_SYMLINK_MSG); sys.exit(1)`，在
  `_ensure_repo` 的 `os.makedirs`/`git clone` 之前）；M2 `_sync_root_scripts`；M3-M5 见上；M6
  `install.sh --versions` 分支（`[ -L "$HOME/.agate" ]` → heredoc 三步指引 + exit 1；否则
  `python3` 探测 + `mkdir -p` + 条件 `git clone "${AGATE_REPO_URL:-…}"` + exec 安装器 latest）；
  M7-M11 文档面（UPGRADING 生命周期节 + v0.50.0 blockquote 指针 + README×2 + SETUP.md）；M12-M15
  测试。`git diff --stat` 12 文件全部落在 M 表范围内，无表外文件。
- **resolve-entry.py「只核对不改」** ↔ P2-design §1.2「不改什么」：一致。`git diff` 无
  `resolve-entry.py` hunk；P4-implementation 批 1 明述「`agate/scripts/resolve-entry.py` 只核对
  未改（决策 A1 受益方）」；P6 BDD-8 `test_tag0032_bdd_8_meta_repo_hook_gate_path_resolves` 验证
  `resolve-entry.py pre-commit` 在 `root=vdir/agate` 后解析出 `<root>/scripts/pre-commit-gate.py`
  存在并 exec（stub marker `GATE-META-050` 命中），未改代码即受益。

### 3.4 纯增量红线（根即协议部署方继续可用 + 探测序 + 不改 env 覆盖/legacy 软链兜底/`.agate-version` 格式）

**结论：锁死成立。** P2-design §2 决策 A「纯增量红线核对」+ P1 I-11 + 断点二「行为纯增量」。
- 探测序 `vdir/scripts` **先**、`vdir/agate/scripts` **后**：`_protocol_root` 硬编码，`git diff` 确认
  第一分支 `if os.path.isdir(os.path.join(vdir, "scripts")): return vdir`——「根即协议」部署方探测序 1
  先命中直接返回 `vdir`，不进 `/agate` 分支。P6 BDD-7 + P6.5 独立重验断言
  `_protocol_root(vdir)==vdir`、`AGATE_ROOT={vdir}`（非 /agate）PASS。
- 两形态皆无 → `return vdir` 原样 → 下游 `resolve-entry.py:49-52` 拼 `vdir/scripts/<gate>` 不存在 →
  `:51-52` fail-closed `sys.exit(1)`（既有兜底未删）——I-11「不新增静默放行」守住（P2-review 核查 1a
  确认，P7 复核 `git diff` 无 `resolve-entry.py` 改动）。
- env 覆盖契约（`AGATE_ROOT` env 优先）/ legacy 软链兜底分支（`if use_legacy and os.path.islink(base):
  return {"root": os.path.realpath(base), …}`）/ `.agate-version` 格式（`agate: vX.Y.Z`，
  `_find_project_declaration`）：`git diff -- agate/scripts/agate_common.py` 均无对应 hunk，三者未改。
- DEBT0016 dirname 散点回归锁：P2-design §5 note 2 + P2-review 核查 1c 已 grep 复核所有 `resolve_*`
  消费方经 `_resolve_version_info` 归口、无 `os.path.dirname(vdir)+"/scripts"` 旁路；P6 BDD-9 全量
  `1484 passed`（双 fixture `_make_home_meta` / `_make_home_rootproto` 常驻并存）为回归锁，本轮无新增
  解析旁路（`git diff` 仅 `_protocol_root` 单点 + 两调用点）。

---

## 4. 未决项清零

**结论：清零。** `grep -nE '^\[?(NEED_CONFIRM|BLOCKER|DEVIATION-CRITICAL)' P1-requirements.md` →
零命中（P1 §8 为 `[NO_NEED_CONFIRM]`，§1 顶部为 `[PROD_NOT_TOUCHED]`）。P6-acceptance.md 为客观二值
验收（14 PASS / 0 FAIL），无 NEED_CONFIRM。P4-review 复评 `status: approved` / 0 CRITICAL。
P5-test-results/unit.md：`failed = 1`（预存并行 flaky `test_agate_next_card.py::
test_nc_cross_checkout_paths_hash_consistent`，`-n auto` worker 间干扰，与 TAG0032 diff 无关——
TAG0032 改动完全不触碰 `agate-next-card.py` 及其测试；已登记 `known-failures.md`，run2 全绿、隔离
单跑 PASS），新增失败 0；P6 BDD-9 本轮全量运行未复现该 flaky（`1484 passed`）。非阻塞、非本任务
引入。

---

## 5. CODE-MAP 核对

**结论：`[CODE_MAP_SYNC:]`（2/2）。** `git diff --name-status 3f3cc01..HEAD` 新增文件（`A`）共 2：

[CODE_MAP_SYNC: agate/tests/unit/test_upgrading_lifecycle.py —— 新增测试文件（P3 test-designer 建，BDD-10/11/12 + BDD-4 判据 3）。CODE-MAP.md 描述对象为 agate 协议本体架构（phase-cards / execution-roles / review-roles / scripts / templates / rules 五模块），测试文件不在其记录范畴（CODE-MAP.md 头「后续任务新增/挪动协议文件时…P7 核对」——测试脚手架 CODE-MAP 豁免，dispatch-context 明示）。无 CODE-MAP 记录需更新，依赖方向无偏离。]

[CODE_MAP_SYNC: agate/tests/integration/test_version_lifecycle_e2e.py —— 新增端到端测试文件（P3 建，BDD-13/14，`_tag_meta_upstream` 元仓库形态 fixture）。同上，测试文件不进 CODE-MAP.md 五模块记录，CODE-MAP 豁免。P4 fix-1 §② 对其 `_tag_meta_upstream` 补 `agate-install.py` 为 fixture 增量，非新增文件。无 CODE-MAP drift。]

P4（含 fix-1）**未新增任何非测试文件**——`agate/scripts/agate-install.py` /
`agate/scripts/agate_common.py` 均为 `M`（修改既有），无新 script / 新 role / 新 template / 新 rules
YAML → CODE-MAP.md「scripts」模块记述无需更新。`code_map_new_files_count: 2` /
`code_map_reviewed_count: 2`（== ）。测试文件 SYNC，无 DRIFT WARNING。

---

## 6. 门槛自检

- P7-consistency.md 存在，Header `status: approved`（Review 角色映射：无 BLOCKER / 无 CRITICAL → approved）✔
- P4-implementation.md 5 处行首 `[DESIGN_GAP:]` 逐条转抄 + 配行首 `[DESIGN_GAP_REVIEWED:]`，
  `design_gap_reviewed_count (5) == design_gap_count (5)` ✔
- 每条 `[DESIGN_GAP_REVIEWED:]` 均含跨文件引用关键词（`P1 …BDD` / `P2-design §…` / `P4-implementation …`）
  ——gate WARNING 规避 ✔
- `blocker_count: 0` / `deviation_critical_count: 0` → 不触发 rejected；`deviation_count: 1`（非 critical，
  §3.3 UPGRADING.md 维护语义机制描述滞后 fix-1，建议 P8 修订）明确指出 ✔
- SCOPE+ 闭环：全流程无 SCOPE+ → N/A（§2）✔
- 跨文件一致性 4 项（§3.1 packages / §3.2 BDD↔验收 / §3.3 实现路径↔设计 / §3.4 纯增量红线）各有
  结论 + 具体锚点（文件节名 / BDD 编号 / M 编号 / commit SHA `1d9a322`·`5f08bf8` / `git diff` hunk）✔
- CODE-MAP 核对：2 个新增测试文件 `[CODE_MAP_SYNC:]`，无 DRIFT ✔
- 结论引用具体锚点，无裸「一致」/「BLOCKER=0」✔

---

## 结论

**status: approved**（agent: consistency-reviewer）

blocker_count=0，deviation_critical_count=0。5 处 DESIGN_GAP 全部转抄 + REVIEWED（独立核对裁决理由
成立：GAP 1/3 已由 fix-1 分别回退 P2-design §3 B1 / §4.2 M6；GAP 2/4 为 P1 隐含要求 / scope Phase 3
范围内的合理补全；GAP 5 为不违反 BDD-12 判据的格式微调）。SCOPE+ 全流程未产生 → N/A。跨文件一致性
4 项均以具体锚点闭环：P2 `packages` ↔ 实际改动面 ↔ P8 单一版本号 bump 一致；P1 14 条 BDD ↔ P6 14
PASS ↔ P6.5 judge 14/14 数量匹配且逐编号语义对应；决策 A1（`_protocol_root` + `_resolve_version_info`
两处调用 + version 从 cur 取）与决策 B1（fix-1 后单源 copytree）与 P2-design §2/§3 候选一致；纯增量
红线（探测序 vdir/scripts 先、env 覆盖 / legacy 软链兜底 / `.agate-version` 格式不改）经 `git diff` +
P6 BDD-7 锁死。CODE-MAP 2 个新增均测试文件 → SYNC 豁免。

**1 处非关键偏差（deviation_count=1，不阻断 P8）**：`agate/UPGRADING.md`「版本管理生命周期 › 根
`~/.agate/scripts/` 维护语义（决策 B1：副本）」段仍按 fix-1 前的双 copytree 撰写「运行中安装器自带
`scripts/` 叠加 current 版本协议 `scripts/`（后拷贝者胜）」，与 fix-1 §③ 回退的单源 copytree 代码
不符。BDD-4/BDD-11 判据仅断言「副本 / 重跑刷新 / repo 被删不影响」三点（对单源仍为真），用户可见
承诺不受影响；建议 P8（本就修订 UPGRADING.md 发布章节）顺手把该句改写为单源 copytree 口径。
