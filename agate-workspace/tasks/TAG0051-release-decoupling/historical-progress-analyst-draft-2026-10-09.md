[输入] 读完 P0-brief.md：task=任务与发布解耦（P8 不落 tag，Release 独立流程+发布门）；goal 三段（①任务止于 READY ②Release 独立流程 ③配套）；known_risks 6 条；executor_env=opencode/has_task_tool/has_local_runtime/network=available；env_constraints.debug_env=""。
[输入] 读完 analyst.md 角色定义：七节结构、同类扫描强制、P0 时效性质疑、capability_requirements 三态、BDD 反模式自检。
[输入] 读完 roadmap.md：RM-AG0103（scheduled，关联 TAG0051）全文含现状问题/事故实证 TAG0050/目标切法①②/配套/锚；RM-AG0098（done，CHECK7 已改 tag 无关 + release.yml 已加 tag 校验步）；RM-AG0110（backlog，不可裁剪阶段集下沉契约单源，ADR-014）。
[输入] 读完 P8-release.md 卡：现状 P8=交付收尾，含 bump+CHANGELOG+git tag（推进条件含「git tag 已创建」L156）；gate 规则含暂存区 version/CHANGELOG 变更 + roadmap RM done；delivery 字段结构化（非 legacy）。
[输入] 读完 agate/scripts/README.md「新增脚本登记面」：机械门禁仅 ① CHECK9-coverage（只 glob check-*.py）+ ② SG.6（共用 uncovered_gate_scripts()）；agate-*.py 不在门禁面；实测方法=放探针脚本实跑。
[输入] 读完 release.yml：on: push: tags:['v*'] 唯一触发器，无 workflow_dispatch；含「Verify tag points to matching commit」步（TAG0042 批0）；build 调 agate-release.py。
[输入] 读完 protocol-tests.yml：jobs detect-docs-only/pytest/platform-scan/shellcheck/ruff/consistency/gate-backstop；顶部注释称 required=5（gate-backstop 移出），但 objective_info 称 gate-backstop 已升 required（6 项）——注释可能滞后。
[输入] 读完 P8-release.md 卡 + phases.yaml P8 条目（gates 含 version/CHANGELOG/tag 检查）+ check-gate.py gate_p8（L2176-2330：bump_type/debt_check/delivery 结构化/roadmap done/version/CHANGELOG/tag 存在性 WARNING）。
[输入] 读完 AGENTS.md 版本发布清单 6 步（第 4 步先 push tag；第 6 步才验合并后 CI 全绿）+ release PR 必须普通 merge。
[输入] 读完 UPGRADING.md v0.80.1/v0.80.2 节。
[输入] 读完 r6-differential.sh：before/after 协议下对 legacy 任务逐 gate 跑 check-gate.py，比较 (rc, ERROR 行集合)，差异须匹配 r6-allowlist.yaml；运行前后各核验 corpus 干净。legacy 判定=账本无 task_created/task_adopted。
[输入] 读完 .state.yaml（TAG0051 仅 task_id/phase:P0/retries:{}）；CHANGELOG [Unreleased] 当前为空；state-machine.md READY→DONE=人手动 make publish；P8 是交付收尾非发布。
[输入] 读完 agate-release.py 头部：子命令 boundary/pyyaml-pin/notes/is-prerelease/build；notes 从 CHANGELOG 提段；build 确定性产物。release.yml 内零打包逻辑。
[输入] 读完 agate-ci-verify.py 头部：逐提交回放 hook；--base 必填；回放协议根=base 处 agate/；退出码 0/1。
[输入] 读完 level-1.yaml：delivery 契约 required:[method]/none_requires_reason/non_none_requires_ref（method 取值域未定死，RM-AG0103 要求定死）；phase_universe=[P1..P8]；pruned required_fields=[phase,reason,risk]。
[扫描开始] 开始同类扫描关键符号。
[扫描] tag 已创建：命中 agate/phase-cards/P8-release.md(L122,L156)、agate/state-machine.md(L177)、agate-workspace/debt/tech-debt.md(L508，叙述)。
[扫描] git tag：agate/state-machine.md(L165,L177)、agate/phase-cards/P8-release.md(L37,50,122,156)、agate/rules/state-transitions.md(L54)、agate/assets/execution-roles/implementer.md(L90)、agate/scripts/check-gate.py(L2316-2328 tag 存在性 WARNING)、agate/git-integration.md(L188)、AGENTS.md(L169,174,182)。
[扫描] workflow_dispatch：仅 .github/workflows/deploy-pages.yml 有；release.yml 无（确认现状）。
[扫描] VERSION_TAG_PREFIX：check-gate.py(L2317,2328) + state-machine.md(L165)。
[扫描] delivery：P8-release.md(L70,71,85)、UPGRADING.md(L455,480,488,527,529)、level-1.yaml(L52-56)；测试用 delivery: local / package-release / (结构化)。
[扫描] bump_type：phases.yaml(L159,163)、P8-release.md、state-machine.md(L165,393)、check-gate.py(L2184-2186)、WORKFLOW.md(L327)、dispatch-protocol.md(L881)、obligations.yaml(OBL-P8-01)。
[关键发现] task_level：仅账本有 task_created/task_adopted 事件才算非 legacy。全仓 44 任务目录，仅 TAG0051 有 task_created（唯一非 legacy）；其余 43 个全 legacy → 结构化 delivery 路径当前只对 TAG0051+ 生效；既有任务 delivery 走子串路径（TAG0042/TAG0050 P8-release.md 的 delivery 是自由文本）。
[关键发现] check-gate.py gate_p8 现状：bump_type/debt_check/delivery 必填（非 legacy 结构化，legacy 子串）；roadmap done 硬拦；version 文件变更 WARNING；CHANGELOG 变更 WARNING；tag 存在性 WARNING（L2316-2328）。P8 卡要求 bump-version + CHANGELOG 切版本节 + git tag。
[扫描] AGENTS.md tag 时点三处：L169 第4步先 push tag；L174 第6步才验合并后 CI 全绿；L182「release PR 必须普通 merge」先合 PR 后打 tag。→ 三处自相矛盾（P0-brief/RM-AG0103 所指）。
[扫描] P8 tag 条件全清单（须移除）：state-machine.md L165/L177、phase-cards/P8-release.md L122/L156、rules/state-transitions.md L54、dispatch-protocol.md L881、check-gate.py L2316-2328（tag 存在性 WARNING）、phases.yaml L159（gates 措辞含 tag）。
[扫描] CHECK 7=badge↔CHANGELOG 已发布版本(tag 无关)；CHECK 13=CHANGELOG 最新版本↔UPGRADING §3 章节(RM-AG0052)。
[待做] 登记面实测（新增/改名 agate/scripts/ 文件）——在 /tmp 副本上放探针脚本跑 consistency + SG.6。
[登记面实测] 在 /tmp 副本（git clone 本仓 task 分支）放入探针 check-probe-surface.py + agate-probe-surface.py：consistency 对 check-*.py 出 CHECK9-coverage WARNING（exit 0，415 WARNING 无 ERROR）；SG.6 test_sg_6_check9_anchor_table_covers_all_gate_scripts **FAILED**（未登记脚本 → 红）；agate-*.py 零触发。→ 若实现新增 check-*.py 须登记（锚点表或豁免集）方使 SG.6 绿。
[扫描] 实测分支保护 required checks = 6：shellcheck×2 / pytest×2 / consistency / gate-backstop。→ protocol-tests.yml 头部注释（2026-10-05，称 gate-backstop 已移出 required、5 项）**已陈旧**，本任务须同步（同类扫描发现）。
[P0 时效] 逐条核对：task 目标方案仍成立（release.yml 仍无 workflow_dispatch；P8 仍要求 tag）；executor_env.platform=opencode 与实际一致；6 条 known_risks 均未被其他任务解决；debug_env 仍空 → 无漂移。
[BDD 起草] 开始定 BDD（分组：①任务终态 READY ②Release 独立流程 ③配套 ④兼容/机制）。
[产出] 已写 P1-requirements.md：19 条 BDD（BDD-1..19，4 功能组）；同类扫描 8 小节；P0 无漂移；[NO_NEED_CONFIRM]；phases 全阶段；capability_requirements: []。
[验证] 运行 check-frontmatter / check-pruning / check-routing / consistency 预检。
[验证] check-pruning exit 0（0 mismatches）；check-frontmatter exit 0；consistency --strict-errors-only exit 0（0 ERROR，414 WARNING 全为冻结叙事）；BDD 19 条连续；真实仓库 git status 仅 3 个未跟踪新文件（无协议/脚本/测试改动）。
[完成] P1-requirements.md 落盘完成。
