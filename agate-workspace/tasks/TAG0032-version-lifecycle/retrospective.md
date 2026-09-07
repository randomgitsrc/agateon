---
task_id: TAG0032
mechanism_issues:
  - "P2 gate_commands.P5 的 pytest 命令按子目录挑选（unit/regression/integration），漏 agate/tests/scripts/ → 本地 P5 全绿但 CI 全量才暴露失败"
  - "check-platform-assumptions.py 的 R4（临时目录字面量）行级豁免不含 # 注释行——R2 有 _r2_comment_exempt，R4 没有，导致注释里说明『不用 /tmp 字面量』反被判违规"
execution_issues:
  - "P1 同类扫描（扫描 4 文档面）+ P2 影响面梳理 §1.1 漏了 agate/scripts/README.md / agate/AGENTS.md / agate/adr.md 三处文档传播目标，靠 SELF-GATE Layer 1 兜住"
  - "P4 implementer 为迁就 P3 fixture（故意精简，不含 agate-install.py）把 install.sh --versions 改用 $SCRIPT_DIR → 真实 curl|bash 新机场景断裂（CRITICAL），P4-review 抓住"
feedback_ready: true
---

# 复盘 — TAG0032 版本管理生命周期可用性批（RM-AG0058 → v0.69.0）

## 一、事实基线

| 项 | 值 |
|----|-----|
| 阶段 | P0-P8 全流程 + P6.5 judge + SELF-GATE Layer 1（协议自变更任务） |
| wf commit 数 | 11（P1-P8，含 P8 CI 修复轮）+ 立项 3f3cc01（已由 PR #281 先并入 main）+ HANDOFF |
| BDD 条数 | 14（断点一入口断链 5 / 断点二元仓库 gap 4 / 断点三 update 入口 3 / 端到端 2） |
| retry | P1 ×1（requirements-review needs-revision：BDD-12 判据恒真 / I-3 无 BDD 绑定 / BDD-2 判据宽严不一）；P4 ×1（review needs-revision，1 CRITICAL：install.sh --versions 在 curl\|bash 断裂） |
| 额外评审迭代轮 | P1 复评 1 / P4 fix-1 + 复评 1 / SELF-GATE Layer 1 fix-1 + 复审 1 / P8 CI 修复 1 |
| subagent 派发 | ~22（analyst ×3 / requirements-review ×2 / architect / plan-eng-review / test-designer / implementer ×5 / review ×3 / verifier ×2 / judge / consistency-reviewer / protocol-alignment-review ×2） |
| 代码文件改动 | agate/scripts/agate-install.py（+64）/ agate/scripts/agate_common.py（+21）/ install.sh（+35） |
| 文档/ADR 改动 | README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md / agate/scripts/README.md / agate/AGENTS.md / agate/adr.md（新增 ADR-012）/ agate/platform-notes.md / CHANGELOG.md |
| 测试改动 | 5 文件（test_agate_version_install.py / test_agate_version_resolve.py / test_hook_resolve_entry.py 追加 + test_upgrading_lifecycle.py 新增 + test_version_lifecycle_e2e.py 新增），18 个 test_tag0032_* 用例 |
| gate 失败次数 | check-gate P1 一次（行首 [NEED_CONFIRM] token 误触发，主 Agent dispatch-context 微修）；P4-review 1 CRITICAL；SELF-GATE Layer 1 首轮 4 NEEDS_HUMAN_REVIEW；CI 首轮 platform-scan + pytest fail（R4 误判） |
| 版本 | v0.68.0 → v0.69.0（minor） |
| PROD_TOUCHED | 无（全程隔离 HOME，真实 ~/.agate legacy 软链未触碰） |
| DEBT 登记 | DEBT0034（三步 legacy 软链迁移文案在 agate-install.py 与 install.sh 双写） |
| PR | #284（普通 merge，merge commit e4f123d）；G-5：`git merge-base --is-ancestor v0.69.0 origin/main` = 0 |

## 二、做得好的 + 可复用模式

**填写引导语回答（本次产生的临时命令/脚本/经验，哪些该沉淀）**：本次没有产生一次性脚本；有价值的是"验证方式"层面的做法，下列两条已在流程内落地为 P6 证据 / 评审动作，不需另沉淀文件。

- **P6 验收对 install.sh --versions 补了一条隔离 HOME 真实 `cat install.sh | bash -s -- --versions` transcript**（不止跑 `test_tag0032_bdd_5` 的 worktree 全路径调用）→ 正是这条 transcript 佐证了 fix-1 后主路径可用；**去向：回馈 agate**——「涉及 bootstrap / CLI 入口的 BDD，P6 证据应含一条『按文档字面命令』的实跑 transcript，不只跑用例内的辅助调用形态」值得进 verifier.md 或 P6 卡（与 P1 卡「人工体验路径验收」同源精神，扩到 CLI 入口）。
- **P4-review 独立复现（隔离 HOME）确认 CRITICAL 是真 bug**（`cat install.sh | bash -s -- --versions` → EXIT=2，`~/.agate/scripts/` 未建）→ 不是纸面担忧，评审的价值在"换个调用形态就炸"；**去向：项目资产沉淀**——已是 review.md「收到视觉否定先反驳」的同类纪律（"先复现再下结论"），本次是 CLI 场景的实例，不需新增条文。

## 三、发现的问题

### 问题 1：P2 gate_commands.P5 的 pytest 命令按子目录挑选，漏了 agate/tests/scripts/

- **归因层面: 机制缺口**
- 说明：P2-design §6 固化 `P5: "python3 -m pytest agate/tests/unit/ agate/tests/regression/ agate/tests/integration/ -q --tb=no -n auto"`——三个子目录，**没有 `agate/tests/scripts/`**。P5 verifier 与主 Agent 本地全量按此命令跑，`test_check_platform_assumptions.py::test_bdd_8_clean_tree_zero_detection`（断言 clean tree 扫描 exit 0）从未被执行。CI 用 `pytest agate/tests/`（全目录）才暴露。后果：一个真实的 CI-red（platform-scan + pytest 双 fail）拖到 PR 阶段才发现，多一轮 P8 CI 修复。
- P2 architect 卡片 / gate_commands 声明节没有"pytest 命令必须覆盖测试根目录、不得挑子目录"的约束；三档基准表只谈超时不谈覆盖面。

### 问题 2：check-platform-assumptions.py 的 R4 行级豁免不含 # 注释行

- **归因层面: 机制缺口**
- 说明：`_RULES` 里 R2（命令位置裸 python3）有 `_r2_comment_exempt`（`# ` 开头行豁免，且 R2 已因 BLOCKER-1 决策把 docstring 也豁免"文档非可执行代码"）；但 R4（`/tmp` 字面量）的行级豁免 `_r4_exempt` 只认 `BATS_TEST_TMPDIR` 变量行和 `# scan-exempt:` 显式标记。结果：测试文件注释里写"平台无关：……无 /tmp 字面量……"（在**说明没用**）被 R4 命中 → 扫描器 exit 1。本任务两个新测试文件各中一处。
- R4 与 R2 对"注释行是文档非代码"的处理不一致——同一份"注释豁免"逻辑 R2 有 R4 无。

### 问题 3：P1 同类扫描 + P2 影响面梳理漏了三处次级参考文档

- **归因层面: 执行错误**
- 说明：P1-requirements.md §4「同类扫描」的扫描 4「文档面 update / 升级指引散落位置」枚举了 README×2 / UPGRADING / SETUP / install.sh，**未列 `agate/scripts/README.md`（L5 版本管理机制段 + L70 agate-install.py 工具行）与 `agate/AGENTS.md`（L91-96 版本管理形态块）**；P2-design.md §1.1「改什么」表同样没有这三处 + `agate/adr.md`。SELF-GATE Layer 1（protocol-alignment-review）首轮把这些标为 A2/A3/A5/A7 NEEDS_HUMAN_REVIEW 兜住，主 Agent 派 implementer 补 `agate/scripts/README.md` + `agate/AGENTS.md` + 新增 ADR-012。
- 机制（self-gate）本身正常工作并兜住了——所以不是机制缺口。但"同类扫描"的强制节要求"对关键符号 grep 全仓"，本次 grep `agate-install` / 版本机制关键词时**没扫到或没纳入** `agate/scripts/README.md` / `agate/AGENTS.md`——执行时同类扫描做得不够全。

### 问题 4：P4 implementer 迁就 P3 fixture 改 install.sh exec 路径 → 真实场景断裂（CRITICAL）

- **归因层面: 执行错误**（主因），伴随一处 P3 机制边界
- 说明：P3 的 `_tag_upstream` / `_tag_meta_upstream` fixture **故意精简**（`agate/scripts/` 不含 `agate-install.py`，模拟元仓库 gap 的最小形态）。P4 implementer 发现 P2-design §4.2 M6 写的 `exec ~/.agate/repo/agate/scripts/agate-install.py` 在 fixture 下不存在，就自主改成 `exec "$SCRIPT_DIR/agate/scripts/agate-install.py"`——在 `test_tag0032_bdd_5`（用 worktree 全路径调 install.sh，`$SCRIPT_DIR` 恰好有效）下转绿，但真实 `curl … | bash -s -- --versions` 场景 `$SCRIPT_DIR` = cwd，路径不存在 → EXIT=2。P4-review 首轮独立复现抓住，判 CRITICAL。fix-1 按选项 A 回归 `$AGATE_HOME/repo/…` 优先 + `$SCRIPT_DIR` 兜底，**并补两个 fixture 让 `agate/scripts/` 含 `agate-install.py`**（贴近真实元仓库形态），随后 `_sync_root_scripts` 也回退 P2-design B1 单源 copytree。
- implementer 应识别"fixture 缺 agate-install.py 是测试简化，不是真实约束"——`P2-design §4.2 M6` 已明写正确形态。这是执行错误（[DESIGN_GAP] 标了、也被审到了，机制链完整）。
- 伴随：P3 test-designer 卡「fixture 形态铁律」只要求"元仓库形态 = 协议在 agate/ 子目录、根无 scripts/"，**没要求 fixture 的 agate/scripts/ 含完整版本工具集**——fixture 太"骨感"给了 implementer 迁就的空间。

## 四、改进措施

| # | 措施 | 落点 |
|---|------|------|
| 1 | gate_commands.P5 的 pytest 命令约束"覆盖测试根目录，不挑子目录"（或直接用 `agate/tests/`）——architect 卡 + P2-design gate_commands 声明节加一条；check-gate P2 可加 WARNING：`P5` 的 pytest 命令若列了 `tests/<子目录>/` 而非 `tests/` 根，提示"CI 跑全量，本地挑子目录会漏" | `agate/assets/execution-roles/architect.md`「gate_commands」节 + `agate/phase-cards/P2-design.md`「gate_commands 声明」节；可选 `agate/scripts/check-gate.py` P2 分支 WARNING |
| 2 | `check-platform-assumptions.py` 的 R4 行级豁免复用 `_r2_comment_exempt`（`# ` 开头注释行同类豁免，与 R2 docstring 豁免 BLOCKER-1 决策一致）——`_scan_file` 里 `if exempt == "r4"` 分支加注释行判定；配 regression 测试（注释里含 `/tmp` 不触发 R4） | `agate/scripts/check-platform-assumptions.py` `_r4_exempt` / `_scan_file`；`agate/tests/scripts/test_check_platform_assumptions.py` 新增用例 |
| 3 | P1「同类扫描」+ P2「影响面梳理」的强制节补一句"次级参考文档也在扫描面"——凡改脚本行为/CLI 用法，`agate/scripts/README.md` 工具清单表 + `agate/AGENTS.md` 相关形态块 + `agate/adr.md` 相关 ADR 必须纳入 grep 命中判定（不只 README/UPGRADING/SETUP）。可挂到 protocol-alignment-review 的"反向传播常见路径"表已有 `check-*.py 脚本行为 → scripts/README.md`，把 `agate-*.py` 也明确列进去 | `agate/assets/review-roles/protocol-alignment-review.md` 反向传播表（补 `agate-install.py / agate-*.py 行为变化 → agate/scripts/README.md 工具行 + agate/AGENTS.md`）；`agate/phase-cards/P1-requirements.md`「同类扫描」+ `P2-design.md`「影响面梳理」提示 |
| 4 | P3 test-designer 卡「fixture 形态铁律」补：模拟真实部署形态的 fixture，其 `<协议根>/scripts/` 应含被测入口命令本体（如 `agate-install.py`），不能因"最小复现"精简掉——精简 fixture 会诱导 implementer 迁就 fixture 而非真实约束 | `agate/assets/execution-roles/test-designer.md` fixture 相关节 + `agate/phase-cards/P3-tdd.md` |

## 技术债登记核对清单

| 机制 | 应该触发？ | 实际触发？ | 未触发后果 | 原因 |
|------|-----------|-----------|-----------|------|
| retry 记录 | 是（P1 needs-revision / P4 needs-revision） | ✅（.state.yaml retries P1×1 + P4×1） | — | — |
| PAUSED | 否（retry 未超限，无跨 ≥2 阶段回退，无不可逆操作） | — | — | — |
| PROD_TOUCHED | 否（全程隔离 HOME） | — | — | — |
| SCOPE+ | 否（P0-brief scope 三段全程未突破，无新隐含需求越界） | — | — | — |
| SCOPE_RESOLVED | 否（无 SCOPE+） | — | — | — |
| DESIGN_GAP | 是（P4 implementer 自主决策 5 处） | ✅（P4-implementation.md 5 处行首 [DESIGN_GAP:]） | — | — |
| DESIGN_GAP_REVIEWED | 是 | ✅（P7-consistency.md 5 处配对 [DESIGN_GAP_REVIEWED:]，design_gap_reviewed_count=5） | — | — |
| NEED_CONFIRM | 否（无实跑结果与 BDD 偏差的方向性疑问） | — | — | — |
| CAPABILITY_GAP | 否（capability_requirements: []，非 frontend 无 vision） | — | — | — |
| gate 验证（每阶段） | 是 | ✅（P1-P8 每阶段主 Agent 预跑 check-gate + pre-commit hook 复跑） | — | — |
| 阶段产出文件（每阶段） | 是 | ✅（P1-requirements / P2-design + review / P3-test-cases + 代码 / P4-implementation + review / P5-test-results / P6-acceptance + evidence / P6.5-verdict / P7-consistency / P8-release） | — | — |
| .state.yaml phase 同步 | 是 | ✅（每阶段 commit 前经 agate-next.py 或主 Agent 编辑推进；phase = 本 commit 产出阶段） | — | — |
| 裁剪条件 + override | 否（phases 全 8 阶段不裁，无 override） | — | — | — |
| capability_requirements | 是（P1 须声明） | ✅（P1 声明 []，requirements-review 核对通过） | — | — |
| 分阶段落盘（防 subagent 空返回） | 是 | ✅（每个 dispatch-context 注入 progress 落盘指令；无空返回事件） | — | — |
| phase-产出一致性 | 是 | ✅（P8 commit 一处 WARNING「暂存 P4 产出但 phase=READY」——self-gate fix-1 追加了 P4-implementation.md，非违规） | 轻微：commit-msg WARNING 提示 | 机制正常（WARNING 非阻断） |
| P6 evidence（含截图 + 引用 + vision YAML） | 是（非 UI，无截图/vision） | ✅（14 条 bdd-NN-*.log + bdd-5 curl-bash transcript，check-p6-evidence + provenance exit 0） | — | — |
| P2 候选方案 + 权衡（≥2） | 是 | ✅（决策 A 候选 A1/A2 + 决策 B 候选 B1/B2，candidate_count=4，plan-eng-review approved） | — | — |
| P8 internal_only_reason | 否（internal_only 不成立，走完整 P8 + 发布 v0.69.0） | — | — | — |
| dispatch-context.md | 是 | ✅（每次派发含重试/复评/并行拆分各写一个 dispatch-context + agate-inject-card 注入卡片） | — | — |
| pre-commit hook（gate / 状态转移 / 裁剪） | 是 | ✅（每 commit 触发，consistency S0-S6 + check-gate + check-state-transition + check-p6-provenance 等） | — | — |
| CI backstop | 是 | ✅（PR #284 CI 全绿：pytest / shellcheck / consistency / gate-backstop / platform-scan；首轮抓到 R4 误判，修复后全绿） | — | CI 兜住了本地 P5 命令漏跑 agate/tests/scripts/（见问题 1） |
| **技术债登记** | 是 | ✅ | — | DEBT0034（三步 legacy 软链迁移文案在 agate-install.py 与 install.sh 双写，status: open，本任务登记未关闭，留后续收敛） |

## agate 反馈

> `feedback_ready: true`——以下条目供 `agate-feedback.py` 提取。

1. **【机制缺口 · P2 gate_commands】** gate_commands.P5 的 pytest 命令允许按子目录挑选（`tests/unit/ tests/regression/ tests/integration/`），CI 跑 `tests/` 全量——本地 P5 全绿而 CI red 的结构性成因。建议：architect.md + P2 卡约束 pytest 命令覆盖测试根目录；check-gate P2 对"列了 tests/<子目录>/ 而非 tests/ 根"加 WARNING。
2. **【机制缺口 · check-platform-assumptions.py】** R4（`/tmp` 字面量）行级豁免不含 `#` 注释行，与 R2 的 `_r2_comment_exempt` + docstring 豁免（BLOCKER-1 决策）不一致——测试文件注释里说明"不用 /tmp 字面量"反被判违规。建议：R4 豁免复用注释行判定。
3. **【执行面 · 同类扫描覆盖】** 改脚本 CLI 行为时，`agate/scripts/README.md` 工具清单表 + `agate/AGENTS.md` 形态块 + `agate/adr.md` 相关 ADR 属"必须纳入同类扫描 / 影响面梳理"的次级文档——本次 P1 §4 扫描 4 + P2 §1.1 未覆盖，靠 SELF-GATE Layer 1 兜住。建议：protocol-alignment-review 反向传播表把 `agate-*.py 行为变化` 明确指向这三处。
4. **【执行面 · fixture 贴近真实】** 模拟真实部署形态的 P3 fixture 若为"最小复现"精简掉被测入口命令本体（如 `agate-install.py` 不进协议 `scripts/`），会诱导 P4 implementer 迁就 fixture 改实现（本次 CRITICAL：install.sh 用 `$SCRIPT_DIR`）。建议：test-designer.md「fixture 形态铁律」补"协议根 scripts/ 应含被测入口命令本体"。
