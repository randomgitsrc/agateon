# tech-debt 登记簿

> 协议/项目技术债登记。每条 DEBT = 一个 ` ```yaml ` fenced block（机器校验）+ 可选正文。
> 机器校验：`python3 {agate_root}/scripts/check-debt.py {AGATE_WORKSPACE}/debt/tech-debt.md`
> 登记判据（三分法）：① 不修它验收声明变假 → 登记；② 不修但未来变更更贵/更危险 → 登记；③ 都不影响 → 不登记（合法出口）。

## DEBT0001

```yaml
id: DEBT0001
category: technical
title: 文档脚本名引用漂移无 gate 兜底（裸脚本名不被 CHECK 2 捕获）
status: closed
priority: high
evidence:
  - ref: agate-workspace/roadmap/roadmap.md
    note: RM-AG0015（backlog，2026-08-15 立案）
  - ref: docs/reviews/retrospective-tag0010-0011-docs-20260815.md
    note: TAG0010/0011 复盘 §3.1——phase-cards 26 处过时 .sh 引用无 gate 兜住
  - ref: agate/scripts/check-protocol-consistency.py
    note: CHECK 2 REF_RE（L238）只匹配 docs/assets/scripts 前缀引用，裸脚本名（phase-cards/rules 全是）完全漏检（实测验证）
  - ref: agate-workspace/tasks/TAG0013-script-consistency/P6-evidence/bdd-1.log
    note: CHECK 10 落地后 0 ERROR（closure_criteria 1 满足）
  - ref: agate-workspace/tasks/TAG0013-script-consistency/P6-evidence/bdd-2.log
    note: 假协议树 check-nonexistent-script.py → ERROR + exit 1（closure_criteria 2 满足）
  - ref: agate-workspace/tasks/TAG0013-script-consistency/P6-evidence/bdd-4.log
    note: PROTOCOL_DIRS 含 phase-cards/rules，CHECK 2/3 0 ERROR（closure_criteria 3 满足）
impact: 脚本删/改名后协议文档漂移，consistency 0 ERROR 照过（v0.46.0 的 26 处过时引用是实锤）；修复后无 gate 防复发，未来破坏性变更再次漂移无拦截
recommendation: 新增 CHECK 10——扫描协议文件脚本名引用（裸名+相对路径）对照 agate/scripts/ 实际文件，漂移报 ERROR；豁免 UPGRADING 对照表/formatters/3 hook 薄壳/count-tests.sh；phase-cards/rules 入 PROTOCOL_DIRS
closure_criteria:
  - check-protocol-consistency.py 新增 CHECK 10 且通过率 0 ERROR
  - 协议文档引用已删脚本名 → 报 ERROR（测试锁定）
  - phase-cards/rules 入 PROTOCOL_DIRS（引用检查升级为严格）
source: retrospective
created_at: 2026-08-15
task_id: TAG0013-script-consistency
closed_at: 2026-08-16
```

## DEBT0002

```yaml
id: DEBT0002
category: technical
title: 离线包 compute_sha256 双实现漂移（pack/install 两侧各自实现，未共享 agate_common）
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0008-version-management/P7-consistency.md
    note: DESIGN_GAP 1.3 双实现漂移——resolve-chain 批交付的 agate_common.py（438 行）未含 sha256/目录 hash 工具，offline 批受"只新建 2 脚本、不改 agate_common"约束，两侧各自实现相同约定的 compute_sha256
  - ref: agate-workspace/tasks/TAG0008-version-management/P4-review-eng.md
    note: INFORMATIONAL 8 显式跟踪（"compute_sha256 双实现漂移"）
  - ref: agate/scripts/agate_common.py
    note: "closure：本次 TAG0031-P4 commit 新增 compute_sha256(path)，agate-pack-offline.py/
      install-offline.py 均改为 import agate_common 共享同一实现，全仓 grep `def compute_sha256`
      仅剩 1 处定义"
  - ref: agate/tests/unit/test_agate_common.py / test_agate_pack_offline.py / test_install_offline.py
    note: "closure：BDD-1（test_bdd_1_compute_sha256_* / test_bdd_1_pack_offline_* /
      test_bdd_1_verify_checksums_*）全绿"
  - ref: agate/tests/regression/test_offline_bundle_roundtrip.py
    note: "closure：BDD-2（test_bdd_2_pack_install_uninstall_roundtrip_no_behavior_change）全绿，
      hash 合并后 pack→install→卸载全流程无行为变化，属本任务 gate_commands.P5_offline_bundle 覆盖范围"
impact: 目录 hash 约定（排序逐文件 hash 拼接再整体 hash）靠文档同步，两侧若未来改约定不一致 → 打包/安装校验失配，内网错装/误拒
recommendation: 在 agate_common.py 补一个目录 hash 工具（compute_sha256），pack/install 两侧改 import 共享
closure_criteria:
  - agate_common.py 新增 compute_sha256 且两侧 import
  - 两侧不再各自实现 hash 逻辑（grep 无重复定义）
  - BDD-22/23/26 回归通过
source: review
created_at: 2026-08-16
task_id: TAG0008-version-management
closed_at: 2026-09-04
```

## DEBT0003

```yaml
id: DEBT0003
category: technical
title: 离线 manifest 未签名（checksum 防损坏不防整包替换）
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0008-version-management/P4-review-cso.md
    note: MEDIUM-2——manifest 无签名，攻击者可整包替换并重算 checksum，完整性校验被绕过
  - ref: agate-workspace/tasks/TAG0008-version-management/P4-review.md
    note: 遗留建议项 1——建议发布前在 UPGRADING/README 离线包章节明示信任边界（bundle 提供者可信 + checksum 防损坏；防整包替换需引入签名）
  - ref: agate/UPGRADING.md / agate/scripts/README.md
    note: "closure：本次 TAG0031-P4 commit 在两文件离线包章节补充'checksum 防损坏、不防整包替换'
      信任边界说明（bundle 提供者需可信），不引入签名实现（P0-brief out-of-scope 明确排除签名体系）"
  - ref: agate/tests/unit
    note: "closure：BDD-3（test_bdd_3_upgrading_doc_states_checksum_trust_boundary /
      test_bdd_3_scripts_readme_states_checksum_trust_boundary）全绿，属本任务 gate_commands.P5
      全量 pytest 覆盖范围"
impact: 内网安装的信任边界依赖"bundle 提供者可信"的隐含假设；恶意中间人整包替换时 checksum 校验不拦截
recommendation: 文档明示信任边界（bundle 提供者可信）；如需防整包替换引入签名（如 minisign/GPG）校验 manifest
closure_criteria:
  - UPGRADING/scripts README 离线包章节写明"checksum 防损坏不防整包替换"信任边界
  - （可选）manifest 引入签名校验
source: review
created_at: 2026-08-16
task_id: TAG0008-version-management
closed_at: 2026-09-04
```

## DEBT0004

```yaml
id: DEBT0004
category: technical
title: 卸载引用保护扫描限流（mtime 365 天/深度 ≤4/跳隐藏目录）漏扫旧引用且无提示
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0008-version-management/P4-review-cso.md
    note: MEDIUM-3——_find_references 限流（深度 ≤4 + 跳隐藏/.agate/.git + mtime 窗口 365 天）使边界外引用漏扫，被引用的旧/深/隐藏项目在版本删除后 .agate-version 静默回退 current
  - ref: agate-workspace/tasks/TAG0008-version-management/P4-review.md
    note: 遗留建议项 2——建议限流边界命中时向 stderr 输出 WARNING 提示可能漏扫
  - ref: agate/scripts/agate-install.py
    note: "closure：本次 TAG0031-P4 commit 将 `_find_references` 改为返回二元组
      （引用列表 + 是否命中限流边界的布尔标记），调用方在命中限流边界时向 stderr 输出 WARNING"
  - ref: agate/tests/unit/test_agate_install_uninstall.py
    note: "closure：BDD-4/5（test_bdd_4_find_references_and_uninstall_warn_when_scan_limit_hit /
      test_bdd_5_find_references_no_warning_within_scan_bounds）全绿，属本任务
      gate_commands.P5 全量 pytest 覆盖范围"
impact: 引用即保护（设计稿 §8.3）保证被限流弱化——边界外项目锁定版本被误删后静默回退，无提示
recommendation: 限流边界命中（深度>4 / mtime 超窗 / 跳过目录含 .agate-version）时 stderr WARNING 提示可能漏扫
closure_criteria:
  - _find_references 限流边界命中时输出 stderr WARNING
  - BDD-6 回归通过
source: review
created_at: 2026-08-16
task_id: TAG0008-version-management
closed_at: 2026-09-04
```

## DEBT0005

```yaml
id: DEBT0005
category: technical
title: P6 双证据三态解析逻辑三处重复（check-gate / check-p6-evidence / check-p6-provenance）
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0006-ui-ux-quality/P2-design.md
    note: §2.1 _gate_p1_vision_capability / §2.8 check-p6-evidence 与 check-p6-provenance 各自读取 P1 视觉条目三态
  - ref: agate-workspace/tasks/TAG0006-ui-ux-quality/P6-evidence/bdd3-p1-vision-tri-state.log
    note: "closure：TAG0006 落地 read_vision_tri_state 公共 helper，BDD-3（P1 视觉条目三态读取）
      在 P6 阶段验证通过，三处脚本共用同一函数"
impact: 三处解析口径若漂移（如 GAP 判据扩展）会各自不一致，P6/P1 gate 判定分叉
recommendation: 抽取公共 helper（agate_common.py 新增 read_vision_tri_state(p1_file)），三处复用
closure_criteria:
  - 公共 helper 就位且三处脚本调用同一函数
  - 全量 pytest 825+ 全绿 + consistency 0 ERROR
source: review
created_at: 2026-08-17
task_id: TAG0006-ui-ux-quality
closed_at: 2026-08-18
```

## DEBT0006

```yaml
id: DEBT0006
category: technical
title: check-p6-evidence.py ahash 文件名↔哈希 zip 对齐脆性（非图片/损坏图静默跳过致错位）
status: closed
priority: high
evidence:
  - ref: agate-workspace/tasks/TAG0006-ui-ux-quality/P4-review-backend.md
    note: CRITICAL-1——agate-image-check ahash 对非图片文件 contextlib.suppress 吞错不打印行，check-p6-evidence 用 sorted(glob) 与输出 zip 对齐，行数不匹配 → 哈希错位（误拦/漏放）
  - ref: agate-workspace/tasks/TAG0006-ui-ux-quality/P6-evidence/bdd14-ahash-degradation.log
    note: "closure：TAG0006 修复 ahash 收敛单一拥有方，BDD-14（avg-hash 雷同分组含非图片文件
      场景）在 P6 阶段验证通过，zip 对齐脆性消除"
impact: avg-hash 雷同分组（BDD-14）与同 BDD 时序豁免（BDD-17）判定失真，静默破坏充数/雷同防伪
recommendation: ahash 计算收敛到单一拥有方（内联到 check-p6-evidence 或 agate-image-check 改输出 文件名\t哈希 成对行），消除 zip 对齐脆性；补含非图片文件的中等复现单测
closure_criteria:
  - check-p6-evidence 与图片哈希文件一一对应，无 zip 错位
  - 含 >1KB 非图片文件的 screenshots 场景，重复对仍正确分组
source: review
created_at: 2026-08-17
task_id: TAG0006-ui-ux-quality
closed_at: 2026-08-18
```

## DEBT0007

```yaml
id: DEBT0007
category: technical
title: test_check_pruning.py 部分用例依赖真实 git 暂存区而非隔离 fixture，大体量协议自身任务会误报
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0015-retrospective-feedback/retrospective.md
    note: TAG0015 P4/P5/P6/P8 阶段多次独立验证全量 pytest 时反复出现
      test_p2_6e_prune_p7_coupling_checklist_exit_0 / test_p2_52_yaml_list_phases_exit_0 /
      test_p2_52b_yaml_list_phases_p3_pruned_low_exit_0 三个用例间歇性失败；根因排查（手工构造
      隔离目录复现）确认 agate/scripts/check-pruning.py:56 `_staged_source_count` 用
      `git diff --cached --name-only` 读取**当前仓库真实暂存区**（通过 `git rev-parse
      --show-toplevel` 定位），不是隔离在测试自己的 tmp_path fixture 内——协议自身改造类任务
      （如 TAG0015 本身）在 P4-P8 阶段暂存区常有 20+ 个协议/文档文件（远超判据"源码文件数≤5"），
      导致这三个用例的"应 exit 0"断言被仓库真实暂存区体量污染而失败，commit 后暂存区清空即恢复
  - ref: agate-workspace/tasks/TAG0015-retrospective-feedback/orchestrator-log.md
    note: 2026-08-19 P4/P5 阶段记录了完整的根因排查过程（isolated run / 组合子集 run / git
      stash A-B 对比 / 无并发进程下干净单跑），确认非本任务代码缺陷、非资源竞争假阳性，而是该
      测试固有的隔离缺口
  - ref: agate/scripts/check-pruning.py
    note: "closure：`_staged_source_count` 隔离修复已由 TAG0024 commit `e2357fc` 落地
      （改为定位任务自身仓库/工作树而非无条件读取外层仓库真实暂存区）"
  - ref: agate/tests/unit/test_check_pruning.py
    note: "closure：BDD-6 四个既有用例（test_p2_6e_prune_p7_coupling_checklist_exit_0 /
      test_p2_52_yaml_list_phases_exit_0 / test_p2_52b_yaml_list_phases_p3_pruned_low_exit_0 /
      test_p2_6f_staged_source_count_uses_task_repo_not_outer_cwd_repo_exit_0）TAG0031 本任务
      P3/P4/P5 阶段（gate_commands.P5 全量 pytest）复跑确认全绿，暂存区含 6+ 无关文件时仍稳定 exit 0"
impact: 任何协议自身改造任务（agate 改自己）在 P4-P8 阶段跑全量回归时，都可能被这三个用例的
  误报打断验证节奏，需要每次重新排查"是不是这个已知坑"——排查成本随任务改动文件数增长；更危险的
  是若排查者不知道这个坑，可能误判为真实回归而阻塞流程，或反过来对真实回归掉以轻心（"反正是那三个
  老熟人误报"）
recommendation: 让 `_staged_source_count` 的测试用例改为在隔离的临时 git 仓库内运行（`git init`
  临时目录 + 在其中构造暂存区），不依赖运行 pytest 时外层仓库的真实暂存区状态；或至少在这三个
  用例里显式 monkeypatch `run_git`/`_staged_source_count` 的返回值，不依赖环境
closure_criteria:
  - 三个用例改为不依赖外层仓库真实 git 暂存区状态（隔离或 monkeypatch 任一方式）
  - 在暂存区含 20+ 文件的环境下重跑，三个用例仍稳定 exit 0
  - 全量 pytest 回归通过
source: retrospective
created_at: 2026-08-19
task_id: TAG0031
closed_at: 2026-09-04
```

## DEBT0008

```yaml
id: DEBT0008
category: technical
title: agate-feedback.py 匿名化正则 ABS_PATH_RE 误伤中文散文里的斜杠分隔词（非路径场景过度脱敏）
status: open
priority: low
evidence:
  - ref: agate-workspace/tasks/TAG0015-retrospective-feedback/retrospective.md
    note: 撰写本复盘后端到端跑
      `AGATE_FEEDBACK=on python3 agate/scripts/agate-feedback.py
      agate-workspace/tasks/TAG0015-retrospective-feedback/retrospective.md`（TAG0015
      自身产出、真实 dogfooding，非单测构造场景）验证机制闭环时发现：
      `agate/scripts/agate-feedback.py` 的 `ABS_PATH_RE = re.compile(r'(?:[A-Za-z]:\\|/)
      [^\s\'"`]+')` 会把中文散文里"机制/执行层面""P1/P2 卡片"这类用 `/` 做分隔符的正常文本
      误判为绝对路径并替换成 `<PATH>`（复现：`ABS_PATH_RE.findall('机制/执行层面')` →
      `['/执行层面']`），产出的脱敏 JSON/Markdown 里出现"归因到 <PROJECT> 机制<PATH> ...
      提取"这类语义被破坏的乱码式替换
impact: 不影响 BDD-18 验收的核心诉求（不泄露项目名/绝对路径，方向正确，偏保守不算安全问题），
  但会让 agate-feedback.py 产出的待提交内容出现明显语义破损的乱码片段，人工复核时体验差、
  可能被误认为脚本 bug 而不敢提交，间接削弱 AG0021 反馈机制的可用性
recommendation: ABS_PATH_RE 增加边界约束，要求路径 token 匹配后紧跟或结尾为常见路径结构特征
  （如至少含一个 `.`/字母数字扩展名，或前一个字符是空白/行首/标点而非中日韩文字），排除
  "中文字/中文字"这类纯分隔符用法；或改用更严格的路径检测（如要求匹配到已知项目内文件后缀/
  目录关键词）
closure_criteria:
  - ABS_PATH_RE（或替代实现）对 "机制/执行层面"、"P1/P2" 等中文散文分隔符用法不再误判
  - 对真实绝对路径（/home/xxx/... 、C:\Users\...）判断能力不退化（既有 test_agate_feedback.py
    BDD-18 用例仍全绿）
  - 新增覆盖本条 evidence 场景的回归用例
source: retrospective
created_at: 2026-08-19
task_id: null
```

## DEBT0009

```yaml
id: DEBT0009
category: protocol
title: BDD-12 P5 provenance 存储位置候选 C（commit message 派生）技术上更优雅但依赖无 gate 强校验的自然语言约定，本次未采纳
status: closed
priority: low
evidence:
  - path: agate-workspace/tasks/TAG0016-protocol-hygiene/P2-design.md
    note: "§3.3/§3.4 候选方案权衡——候选 C 从既有 commit message（`wf({task_id}-P5):` 前缀）现查现用派生
      P5 pass commit，零 schema 改动、直接复用已有约定；但该前缀当前没有任何 gate 脚本强制校验格式，
      属于自然语言约定，健壮性弱于候选 A。本任务最终选择候选 A（`.state.yaml` 新增可选字段
      `p5_pass_commit`），信任模型更干净（写入者为主 Agent 本人，非依赖 subagent 自报或文本格式约定）"
impact: 若未来 commit message 格式（wf() 前缀约定）仍未被 gate 强制校验，候选 C 的健壮性风险持续存在，
  不会自然消解；若届时想重新评估切换到候选 C 以省去 `.state.yaml` schema 改动，需要重新翻找本次
  P2-design.md §3.3 已做过的权衡分析，增加决策成本
recommendation: 若未来 commit message 格式（wf() 前缀约定）被新增 gate 脚本强制校验，重新评估是否将
  BDD-12 provenance 存储从候选 A（.state.yaml 字段）切换为候选 C（commit message 派生），届时候选 C
  零 schema 改动的优势才能安全兑现；若无此前提变化，维持候选 A 现状
closure_criteria:
  - commit message 的 wf() 前缀格式已被新增 gate 脚本强制校验，且完成候选 A→C 切换评估（切或不切均可，需记录理由）
  - 或明确评估后决定长期维持候选 A，本条债务关闭并记录理由
source: review
created_at: 2026-08-19
task_id: TAG0016
closed_at: 2026-08-19
close_reason: "三分法评估（2026-08-19 主 Agent 复核）：本条是 P2 设计决策记录（候选方案权衡），非缺陷——不存在'不修验收声明变假'或'未来变更更贵'的任意一者。登记本条目时误将其视为'值得追踪的权衡备忘'，违反 tech-debt 三分法（都不影响 → 不登记的合法出口）。决策本身已记录在 P2-design.md §3.3 且长期有效；若未来 wf() 前缀被 gate 强制校验，届时按 recommendation 重新评估即可，无需以债务形式持续占位。按 closure_criteria 第二条关闭。"
```

## DEBT0010

```yaml
id: DEBT0010
category: technical
title: 至少 4 个 gate_commands 键解析脚本只排除 _formatter 后缀、未排除 _timeout_seconds 后缀，把超时声明字段误判为待执行命令/待核实字段（同类扫描后发现是系统性模式，不止 P3 一处）
status: closed
priority: medium
evidence:
  - ref: agate/scripts/agate-read-gate-commands.py
    note: "L31 `elif key.startswith(\"P3\") and not key.endswith(\"_formatter\"):` 只排除
      `_formatter` 后缀键，未排除 `_timeout_seconds` 后缀键——P2-design.md §6 声明
      `gate_commands.P3_timeout_seconds: 120`（P2 卡片「{key}_timeout_seconds 字段规则」正式
      支持的可选字段）时，该整数值 120 被当成一条待执行 shell 命令解析"
  - path: agate-workspace/tasks/TAG0016-protocol-hygiene/P3-test-cases.md
    note: "§3「已知问题」——TAG0016 自身 P3 阶段实测复现：`python3 agate/scripts/check-tdd-red.py
      {task_dir}` 对真实真红灯（24 个 AssertionError/AttributeError，0 个 A 类）误报
      exit 1（A 类，`bash -c \"120\"` 返回 127）；用 `TEST_RUNNER` 环境变量覆盖绕过后确认
      exit 0（真实 B 类红灯）"
  - ref: agate/scripts/agate-gate-missing-cmds.py
    note: "L20 `if k.endswith(\"_formatter\") or k == \"project_module\":` 同样未排除
      `_timeout_seconds`——TAG0016 P2 阶段实测复现：check-gate.py P2 对
      `gate_commands.P3_timeout_seconds: 120` / `P5_timeout_seconds: 180` 均报
      'GATE P2 WARNING: gate_commands.{key} 命令 {token} 不存在于当前环境'（把整数值当成
      待核实是否可执行的命令 token）"
  - ref: agate/scripts/agate-gate-p5-count.py
    note: "L23 `aux = [k for k in re.findall(r\"^  (P5_\\w+):\", block, re.MULTILINE) if not
      k.endswith(\"_formatter\")]` 同样未排除 `_timeout_seconds`——TAG0016 P5 阶段实测复现：
      check-gate.py P5 把声明的 `P5_timeout_seconds` 计为 1 条'辅助命令'，报
      'GATE P5 WARNING: P2 声明了 1 个主命令 + 1 个辅助命令...请确认已全部执行（非子集）'，
      而实际只有 1 条真实 P5 命令（`P5_timeout_seconds` 不是命令）"
  - ref: agate/scripts/agate-read-p5-commands.py
    note: "L29 `if key.endswith(\"_formatter\"):` 同样未排除 `_timeout_seconds`——TAG0016 系统性
      grep `_formatter` 排除模式命中的第 4 处，未逐一实测复现（该脚本是否会把
      `_timeout_seconds` 键实际当命令执行、还是仅列举，需要修复时一并核实），先登记同一根因，
      避免遗漏"
  - ref: agate/scripts/agate_common.py
    note: "closure（TAG0017）：新增共享判据函数 is_gate_meta_key(key)（endswith((_formatter,
      _timeout_seconds))），4 处消费方均已切换（closure_criteria 1 满足）"
  - path: agate-workspace/tasks/TAG0017-toolchain-fixes/P6-evidence/bdd-1-2-3-4.log
    note: "closure（TAG0017）：BDD-1~4 实跑证据，test_gmc_3/test_p5c_5/test_pyx_7/test_gpc_4/
      test_bdd_2_timeout_seconds_declared_real_a_class_failure_stays_a_class/
      test_bdd_4_formatter_excluding_scripts_also_exclude_timeout_seconds 全部通过，覆盖
      P2/P3/P5 三阶段场景 + 同类遗漏审计（closure_criteria 2 满足）"
  - path: agate-workspace/tasks/TAG0017-toolchain-fixes/P5-test-results/unit.md
    note: "closure（TAG0017）：全量 pytest 1011 passed, 2 skipped, 0 failed（closure_criteria 3
      满足）"
impact: 任何任务在 P2-design.md 按 P2 卡片「{key}_timeout_seconds 字段规则」正常声明
  `{key}_timeout_seconds` 字段（协议鼓励的正常用法，非误用）后，P2/P3/P5 阶段的 gate 校验/红灯
  判定/命令完整性核对都可能被这同一类"未排除 _timeout_seconds 后缀"的解析缺陷误导——P3 会被
  `check-tdd-red.py` 误报真红灯为假红灯（A 类），P2/P5 会收到虚假的"命令不存在"/"还有命令未执行"
  WARNING，操作者若不知道这是已知的工具解析缺陷，容易误判任务自身有问题而返工，或反过来对真实
  问题的 WARNING 掉以轻心（"反正 timeout_seconds 那个坑我知道，不用管"）
recommendation: 四个脚本的判据统一补充排除 `key.endswith("_timeout_seconds")`（与已有的
  `_formatter` 排除并列，四处修法结构相似，可考虑抽成 agate_common.py 的一个共享判据函数，
  避免未来又出现第五处遗漏——这正是本任务 RM-AG0025 想要的"权威源+复用"模式在脚本代码层面的
  应用）
closure_criteria:
  - agate-read-gate-commands.py / agate-gate-missing-cmds.py / agate-gate-p5-count.py /
    agate-read-p5-commands.py 四处均不再把 `_timeout_seconds` 后缀键当作命令/待执行项解析
  - 新增回归用例覆盖"声明 P3_timeout_seconds/P5_timeout_seconds 时，check-tdd-red.py 仍正确
    判定真红灯 + check-gate.py P2/P5 不再误报命令不存在/命令数不符"场景
  - 全量 pytest 回归通过
source: review
created_at: 2026-08-19
task_id: TAG0016
closed_at: 2026-08-20
```

## DEBT0011

```yaml
id: DEBT0011
category: technical
title: SELF-GATE.md protocol-alignment-review 成果文件/留痕文件按纯日期命名，跨任务同日复用会静默覆盖已提交的历史审查记录
status: closed
priority: medium
evidence:
  - ref: SELF-GATE.md
    note: "「变更触发模式」派发模板声明成果文件路径为
      `docs/reviews/agate-alignment-review-{date}.md`、留痕文件为
      `docs/reviews/agate-alignment-{date}-{NN}.progress.md`——命名只含日期，不含任务标识"
  - path: docs/reviews/agate-alignment-review-2026-08-19.md
    note: "TAG0016 自身实测复现：2026-08-19 当天 TAG0015（commit 208a1ec，已合并入 main）与
      TAG0016 各自触发了一次 protocol-alignment-review，两次派发都按 SELF-GATE.md 模板生成同名
      文件 `agate-alignment-review-2026-08-19.md`（及同名留痕文件
      `agate-alignment-2026-08-19-01.progress.md`）。TAG0016 的 subagent 用 Write 覆盖写入该
      文件时，TAG0015 已提交的历史审查记录被静默覆盖（`git diff` 显示 TAG0015 全部审查内容被
      TAG0016 内容整体替换）——若主 Agent 未在 commit 前跑 `git status`/`git diff` 逐一核对新增
      文件是否真的是新增（而非覆盖了已跟踪文件），这类覆盖会在 commit 时静默发生且不产生任何
      WARNING（git 无法区分'合法覆盖旧草稿'与'意外破坏历史记录'）。TAG0016 已手工恢复
      TAG0015 原文件内容（`git checkout --`）并将自己的审查另存为
      `agate-alignment-review-2026-08-19-tag0016.md` 规避，但这是本次会话的人工补救，不是机制修复"
  - ref: SELF-GATE.md
    note: "closure（TAG0017）：命名模板 4 处出现点（文件类型表 + 两种审查模式派发模板）均已补
      `{task_id}`，留痕 `agate-alignment-{date}-{task_id}-{NN}.progress.md`、成果
      `agate-alignment-review-{date}-{task_id}.md`（closure_criteria 1 满足）"
  - ref: agate/assets/review-roles/protocol-alignment-review.md
    note: "closure（TAG0017）：新增 Write 前存在性检查段落，区分同一任务复核轮（可覆盖）/别的
      任务遗留（不可覆盖）两分支（closure_criteria 2 满足）"
  - path: agate-workspace/tasks/TAG0017-toolchain-fixes/P6-evidence/bdd-7-8.log
    note: "closure（TAG0017）：BDD-7/8 实跑证据，test_bdd_7_naming_template_produces_distinct_
      filenames_for_different_task_ids 等 6 条 + test_bdd_8_* 2 条全部通过；全量 pytest 1011
      passed（closure_criteria 3 满足）"
impact: 只要两次 self-gate 审查落在同一日历日（对活跃度较高的 agate 自身改造仓库并不罕见——同一天
  推进两个任务、或同一任务当天多轮 P4/P8 均可能触发多次），后触发的一次会静默覆盖前一次已提交的
  审查历史（若前一次尚未 commit 则是工作区覆盖，损失更隐蔽），且没有任何 gate/hook 检测这种覆盖；
  这类历史记录一旦被覆盖再 commit，除非人工翻 git log 逐次核对，否则不会被发现
recommendation: SELF-GATE.md 的成果文件/留痕文件命名模板补充任务标识（如
  `agate-alignment-review-{date}-{task_id}.md`，无关联任务时用序号 `-{NN}` 后缀，与留痕文件已有
  的多批次序号约定对齐）；同时可选加固：`protocol-alignment-review` 角色文件的分阶段落盘指引里
  提示 subagent 用 Write 前先检查目标路径是否已存在且内容非空，若已存在应先读一遍确认是不是同一
  任务的复核轮（可覆盖）还是别的任务遗留（不可覆盖，需改用带任务标识的新文件名）
closure_criteria:
  - SELF-GATE.md 派发模板的成果文件/留痕文件路径模板补充任务标识占位符
  - 新增或更新一条回归检查（哪怕只是文档层面的检查清单项），要求 subagent 覆盖写前先确认目标
    文件不是别的任务的记录
  - 全量 pytest 回归通过（若涉及脚本改动）
source: review
created_at: 2026-08-19
task_id: TAG0016
closed_at: 2026-08-20
```

## DEBT0012

```yaml
id: DEBT0012
category: technical
title: check-protocol-consistency.py --strict 在"仅有 WARNING 无 ERROR"时返回 exit 2，与 && 串联的
  gate_commands.P5 链路组合会因长期存量 WARNING 债务而永远短路中断
status: closed
priority: medium
evidence:
  - ref: agate/scripts/check-protocol-consistency.py
    note: "main() 末尾（约 L1129-1133）：`if rep.errors: return 1` / `if rep.warnings and
      args.strict: return 2` / `return 0`——--strict 模式下'仅有 WARNING、无 ERROR'与'有
      ERROR'是两种不同的非 0 返回码，但对 `&&` 串联的调用方而言都同样会短路后续命令"
  - path: agate-workspace/tasks/TAG0016-protocol-hygiene/P5-test-results/unit.md
    note: "TAG0016 P5 阶段实测复现：gate_commands.P5（P2-design.md §6 声明）为
      `pytest ... && check-protocol-consistency.py --strict && count-tests.sh` 三命令 &&
      串联；实跑链路整体 exit=2，第 3 步 count-tests.sh 因链路在第 2 步短路而**未在链路内
      执行到**。逐步单独复核确认：pytest 0 failed、consistency 0 ERROR（308 个 WARNING，
      全部为历史遗留的叙事文件死链引用，与本任务无关）、count-tests.sh 独立跑通过——三步
      本身均无问题，问题在于链路层面的 && 短路语义与 --strict 的'WARNING-only 也非 0'设计
      叠加后产生的组合缺陷"
  - ref: git log（历史 P5/P8 commit message）
    note: "e40adac/687e622/eb48440/916d537 等历史任务的 P5/P8 commit message 均只声称
      'consistency 0 ERROR'，从未声称'0 WARNING'——说明本仓库长期以来的实际验收标准是
      0 ERROR 而非 0 WARNING/strict-exit-0；结合当前 308+ 条存量 WARNING 从未被清理，
      推断这一 && 链路组合缺陷可能自 --strict 与该链路命令首次一起使用起就一直存在，只是
      此前的验证流程习惯性用 `command | tail -N; echo $?` 之类的管道模式核对，管道会让 `$?`
      变成 `tail` 的退出码而非目标命令的真实退出码，掩盖了这个问题（TAG0016 本次也曾踩过
      同一个验证方法陷阱，后改用 `timeout ... bash -c '...'; echo $?` 不经管道直接核对才发现）"
  - ref: agate/scripts/check-protocol-consistency.py
    note: "closure（TAG0017）：新增 --strict-errors-only 互斥模式（仅 ERROR 非零，WARNING-only
      exit 0），保留既有 --strict 语义不变；agate/phase-cards/P2-design.md「gate_commands 声明」
      节新增示例改用 --strict-errors-only 为默认推荐，--strict 保留给专门 WARNING 清理任务
      （closure_criteria 1、2 均满足，两方案都做）"
  - path: agate-workspace/tasks/TAG0017-toolchain-fixes/P6-evidence/bdd-9-code.log
    note: "closure（TAG0017）：BDD-9 代码半 3 场景矩阵实跑通过（0E0W/0E+NW/NE 三态）"
  - path: agate-workspace/tasks/TAG0017-toolchain-fixes/P6-evidence/bdd-9-chain-behavior.log
    note: "closure（TAG0017）：额外实测构造真实 `&& echo NEXT_STEP_REACHED` 链路，验证
      --strict-errors-only 场景下链路后续步骤确实被执行到，非仅引用单测断言；全量 pytest 1011
      passed（closure_criteria 3 满足）"
impact: 任何后续任务若原样沿用当前 gate_commands.P5 的 && 串联写法（这是 P2-design.md 已固化的
  声明，大概率会被后续任务复制作为范式），只要仓库内存量 WARNING 未清零，P5 阶段的链路级 exit
  code 永远是 2、且链路最后一步命令永远不会真正被链路执行到——若验证者使用管道+tail 模式核对
  exit code（如本任务前几个阶段一度采用的方式），会得到虚假的"exit 0"印象而看不出问题；若验证
  者直接核对链路真实 exit code，则会看到非 0 但需要额外做"逐步拆解复核"才能确认这不是真失败，
  增加了每次 P5 验证的认知负担和排查成本
recommendation: 二选一（或都做）——(a) gate_commands.P5 declaration 层面：不要用 `&&` 串联含
  `--strict` 的 consistency 检查，改为三条独立命令（如 P0-brief.md env_constraints.test_cmd
  已经是用中文分号分隔的三条独立命令，语义上更准确）分别执行并分别判定，不整体链式短路；
  (b) 脚本层面：`check-protocol-consistency.py` 增加一个更细粒度的模式（如
  `--strict-errors-only`），仅在存在 ERROR 时非 0，WARNING-only 时仍返回 0（把"WARNING 需要
  关注"这件事通过打印内容告知人类，而不是通过阻断式退出码），保留现有 `--strict`
  （WARNING-only 也非 0）作为可选的更严格模式供人工主动选用，不作为 && 链路的默认组成部分
closure_criteria:
  - gate_commands.P5 相关文档/模板（P2 卡片 gate_commands 声明示例、或 HANDOFF 类文档）不再
    推荐把 --strict 塞进 && 链路中间位置
  - 或 check-protocol-consistency.py 新增区分 ERROR-only 与 WARNING-only 的退出码模式，
    且有对应回归测试覆盖两种模式的 exit code 差异
  - 全量 pytest 回归通过
source: review
created_at: 2026-08-19
task_id: TAG0016
closed_at: 2026-08-20
```

## DEBT0013

```yaml
id: DEBT0013
category: technical
title: P8-release.md 未说明 CHECK 7（README badge vs 最新 git tag）与"重跑 P5 gate"之间的时序依赖，bump 版本文件后、tag 创建前重跑必然触发该 ERROR
status: closed
priority: low
evidence:
  - ref: agate/scripts/check-protocol-consistency.py
    note: "CHECK 7（check_version_badge，约 L418-441）用 `git describe --tags --abbrev=0` 取
      最新 tag，与 README.md 的 version badge 做严格字符串相等比较，不相等即 rep.error——设计上
      只有在 tag 已创建、且与 badge 一致时才会通过"
  - path: agate-workspace/tasks/TAG0016-protocol-hygiene/retrospective.md
    note: "TAG0016 P8 阶段实测复现：bump README.md/README.zh-CN.md/CHANGELOG.md 后（tag 尚未
      创建）重跑 gate_commands.P5，consistency 报 1 个 ERROR（'README version badge v0.54.0 !=
      最新 tag v0.53.0'），导致该次 pytest 链路 3 个测试失败；commit + 创建 tag v0.54.0 后
      重跑同一条 gate_commands.P5，0 ERROR，pytest 全绿——确认是时序问题非真实回归"
  - ref: agate/phase-cards/P8-release.md
    note: "closure：PR #166（2026-08-19，merge commit 7bc45fd）已在「主 Agent 必须亲自执行」节
      '重跑 P5 gate'一条后补'⚠️ 时序注意（DEBT0013）'——明确该重跑应安排在 commit + 创建 git tag
      之后进行，而非 bump 版本文件后立即重跑（closure_criteria 1 满足）。本债为纯文档补强，closure
      由作者在 docs 提交中落地，无对应 P5/P6 阶段 gate 验证（文档注类债务的特例）"
impact: 任何任务在 P8 阶段按 P8-release.md 字面顺序（先 bump 文件、随即重跑 P5 gate）执行，都会
  在"bump 已完成但 tag 未创建"这个必经的中间状态撞上 CHECK 7 的设计性 ERROR；若执行者不知道
  这是时序问题，容易误判为真实回归而重新排查协议文档/脚本改动，浪费排查时间
recommendation: 在 `agate/phase-cards/P8-release.md`「主 Agent 必须亲自执行」节"重跑 P5 gate"
  一条后附注："若 gate_commands.P5 的链路包含 check-protocol-consistency.py 的 CHECK 7
  （badge vs tag 一致性），该重跑应安排在 commit + 创建 git tag 之后进行，而非 bump 文件后
  立即重跑——bump 后、tag 前的中间状态下 CHECK 7 必然报错，这是设计使然不是回归"
closure_criteria:
  - P8-release.md「主 Agent 必须亲自执行」节补充上述时序说明
  - （可选）新增一条对该时序依赖的说明性测试或文档一致性检查项
source: retrospective
created_at: 2026-08-19
task_id: TAG0016
closed_at: 2026-08-20
close_reason: "closure_criteria 1 已满足：PR #166（merge 7bc45fd）已在 P8-release.md 补 CHECK 7 时序注意（DEBT0013），tag 创建前重跑的必然 ERROR 有明确提示。closure 为纯文档补强（docs 提交落地），非代码修复，无对应 P5/P6 阶段 gate 验证，但修复目标（消除时序误判）已达成。"
```

## DEBT0014

```yaml
id: DEBT0014
category: protocol
title: Windows Store python3 占位符命中 hook 探测循环导致 Windows 用户 commit 阻断（AGENTS.md/CLAUDE.md 已知但 protocol 层未防护）
status: open
priority: medium
evidence:
  - ref: agate/scripts/pre-commit-gate.sh
    note: "第 11-13 行探测循环 `PY=\"\"` / `for c in python3 python; do command -v \"$c\" >/dev/null 2>&1 && { PY=\"$c\"; break; }; done`——`command -v python3` 在 Windows 上能命中 WindowsApps 目录下的 Store 占位符 python3.exe（它是真实存在的 exe stub），exec 时非交互模式返回 exit 49 → hook 走 fail-closed 分支阻断 commit。薄壳是协议本体（3 个：pre-commit-gate.sh / commit-msg-self-gate.sh / pre-push-gate.sh 同结构），改需 SELF-GATE"
  - ref: agate/platform-notes.md
    note: "「已知限制」表 L141-147 仅列 3 条（`ln -sf` 退化为复制 / pytest 需安装 / 3 hook 需 sh），未列 Store 占位符；Windows 原生章节也未提及"
  - ref: AGENTS.md / agate/AGENTS.md / CLAUDE.md
    note: "提到 Windows 复制模式（hook 软链退化），未提及 Store 占位符；这是项目侧已知但协议层从未防护的兼容性缺口——任何新 Windows 用户都会重新踩"
  - ref: agate/scripts/pre-commit-gate.sh / commit-msg-self-gate.sh / pre-push-gate.sh
    note: "进行中（TAG0017）：3 薄壳探测循环已增强（AGATE_PYTHON 显式覆盖 + 逐候选可执行性小测试，
      通用 exit code 判据，3 文件逐字一致）；platform-notes.md/AGENTS.md 已补 Store 占位符说明 +
      AGATE_PYTHON 机制文档；agate/tests/integration/test_pre_commit_hook.py 新增模拟 stub 集成
      测试覆盖（closure_criteria 1/2/3/4 在 Linux 模拟环境下已满足）。**closure_criteria 5
      （Windows CI matrix 回归确认）本会话未执行**——本环境为 Linux，无法真实触发 Windows Store
      占位符，需等待本次 PR 的 GitHub Actions Windows CI matrix（pytest -m windows_smoke）跑通后
      再关闭本条，不在此提前标记 closed（遵守 P0-brief 约束 3：不宣称已实测 Windows）"
impact: Windows 用户跑 agate 时 commit 钩子默认阻断，需要手动复制 python.exe 为 python3.exe 或改 PATH 让真实 Python 优先，脆弱且不可重现；任何新项目/新用户都会重新踩这一坑，跨项目反馈回流案例（2026-08-19 用户反馈）
recommendation: 三改一并做——(a) 3 薄壳探测循环增强：探测后做可执行性小测试（exit 49 / stderr 含 Microsoft Store 字符串 → skip 该候选，转下一候选 python）或加 AGATE_PYTHON 环境变量优先（项目侧设 AGATE_PYTHON=/path/to/python.exe 时直接接受，跳过探测循环）；(b) agate/platform-notes.md「已知限制」表新增一条 + 「Windows 原生」章节加 Store 占位符说明 + AGATE_PYTHON 机制文档；(c) agate/AGENTS.md「升级 agate」段同步一句。P1 派发时需实测薄壳代码并定 Store 占位符识别阈值（exit 49 / stderr 内容 / Python313 路径是否在 WindowsApps 之前）
closure_criteria:
  - 3 薄壳探测循环增强并实测：Windows 含 Store 占位符的环境，hook 能正确解析到真实 python（或 AGATE_PYTHON 指定路径）
  - AGATE_PYTHON 环境变量机制文档化（platform-notes.md「Windows 原生」章节 + AGENTS.md「升级 agate」段）
  - platform-notes 已知限制表新增一条
  - 全量 pytest + consistency 0 ERROR + shellcheck 0 issue（薄壳改动后）
  - 新增回归用例覆盖 Store 占位符场景（模拟或 Windows CI matrix）
source: retrospective
created_at: 2026-08-19
task_id: TAG0017
```

## DEBT0015

```yaml
id: DEBT0015
category: protocol
title: env_constraints 声明性字段无执行/gate 绑定（deploy 类动作只注入不强制，TQC0001 实证 dist 从未主动产出）
status: open
priority: medium
evidence:
  - ref: agate/scripts/agate-extract-context.py
    note: "L107-109 只把 env_constraints 从 P0-brief 注入 subagent 上下文（`env = _grep_after(...)` 后 `output += ...`），不执行任何环境约束对应的动作"
  - ref: agate/scripts/check-gate.py
    note: "grep env_constraints.deploy / deploy / debug_env / test_cmd / workspace_path 零命中——gate 不检查 env_constraints 字段值（只确认字段存在）"
  - ref: agate/phase-cards/P2-design.md / P4-implementation.md / agate/assets/execution-roles/architect.md
    note: "env_constraints 全部是'确认/细化 + 注入'语义（P2 卡 L50、P4 卡 L41、architect L135），无'必须执行其中某命令'的 gate 绑定"
  - ref: TQC0001 跨项目复盘（Qt 计算器）
    note: "P2 声明 env_constraints.deploy（windeployqt 构建 dist），但全流程 P0-P8 从未主动执行，用户双击 exe 报缺 DLL 后才补做——声明了但没有执行点"
  - ref: agate/phase-cards/P2-design.md「gate_commands 声明」节 / agate/assets/execution-roles/architect.md
    note: "进行中（TAG0017）：新增 env_constraints 声明性 vs gate_commands 执行性边界说明段落
      （closure_criteria 1 满足）"
  - ref: agate/phase-cards/P4-implementation.md「自查≠gate」节
    note: "进行中（TAG0017）：新增'UI/需构建任务 P4 后应构建并确认 dist 类产物存在'提醒条目
      （closure_criteria 2 满足）。**closure_criteria 3（TQC0001 类 UI 任务在 P4 后自动产出
      dist，不靠用户提醒）本会话未验证**——这是一条面向未来的行为性指标，需要下一个实际的 UI 任务
      走完 P4 阶段后才能实证确认提醒条目是否真的改变了 implementer 行为，本任务自身不涉及 UI/dist
      构建场景，无法自我验证，不在此提前标记 closed"
impact: 任何依赖 env_constraints 声明 deploy/pack/build 产物的任务，可能出现'设计说要做但流程不强制'的静默缺口；UI 任务 dist 产物、打包产物、部署产物均无 gate 检查；TQC0001（真实跨项目）已实证
recommendation: 三改一并做——(1) 明确 env_constraints 字段语义边界（声明性 vs 执行性）：P2 卡片/architect 角色说明'执行性约束必须落到 gate_commands 或 P4/P8 明确 checklist'；(2) UI 任务 P4 后应构建 dist：P4 卡片「自查≠gate」节补'UI 任务 P4 后构建 dist（windeployqt 等）'或 P8 gate 加 dist 产物存在性检查；(3) 可选：check-gate.py 或新脚本校验 gate_commands 声明了 deploy/构建命令时 P4/P8 产出物存在
closure_criteria:
  - env_constraints 语义边界文档化（P2 卡片 / architect 角色 / task-files 至少一处权威源）
  - UI 任务 P4 后 dist 构建有明确落点（P4 卡片或 P8 gate）
  - TQC0001 类 UI 任务在 P4 后自动产出 dist（不靠用户提醒）
  - 全量 pytest + consistency 0 ERROR + shellcheck 0 issue
source: retrospective
created_at: 2026-08-19
task_id: TAG0017
```

## DEBT0016

```yaml
id: DEBT0016
category: technical
title: check-gate.py gate_p4 的 CODE-MAP.md 路径用本地"task_dir 向上两级"推导，未调用 agate_common.resolve_workspace 权威解析函数
status: closed
priority: low
evidence:
  - ref: agate/scripts/check-gate.py
    note: "L702-710：`code_map_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(task_dir))), \"agents\", \"CODE-MAP.md\")` —— 本地路径算术，未 import/调用 agate_common.resolve_workspace"
  - ref: agate/scripts/agate_common.py
    note: "L464-493：resolve_workspace(project_root) 权威解析函数，优先级 .agate.env(AGATE_WORKSPACE=) → env AGATE_TASKS_DIR → 默认 {project_root}/agate-workspace；_resolve_abs 内部用 Path(...).resolve()（解析符号链接归一化），check-gate.py 本地推导用 os.path.abspath（不解析符号链接）"
  - ref: agate/scripts/pre-commit-gate.py
    note: "L251-252：task_dir = os.path.join(tasks_dir, task_id) if state_dir == repo_root else state_dir —— 确认 task_dir 在当前所有调用路径下恒等于 {workspace}/tasks/{task_id} 两级嵌套，与 resolve_workspace 两分支的构造方式（tasks_dir=workspace/tasks 或 workspace=dirname(tasks_dir)）代数等价，故本地推导在标准场景下产出与 resolve_workspace 相同结果"
  - ref: agate/scripts/check-gate.py
    note: "closure：本次 TAG0031-P4 commit 将 gate_p4 的 CODE-MAP.md 路径推导改为调用
      agate_common.resolve_workspace，不再本地重新推导路径层级"
  - ref: agate/tests/unit/test_check_gate.py
    note: "closure：BDD-8/9（test_tag0031_bdd_8_gate_p4_code_map_uses_resolve_workspace /
      test_tag0031_bdd_9_gate_p4_non_standard_nesting_resolves_via_agate_env）全绿，覆盖正常流与
      非标准嵌套场景，属本任务 gate_commands.P5 全量 pytest 覆盖范围（本条 task_id: TAG0007 为
      原始登记任务，本次 closure 修复由 TAG0031-P4 完成）"
impact: 仅影响 gate_p4 一处 WARNING 分支（骨架/CODE-MAP 机制已采用但 P4-implementation.md 缺「新增文件核对表」标题时的提醒）——不阻断任何 commit、不影响 exit code 判定；已论证在标准 task_dir 两级嵌套约定下与权威解析函数结果代数等价，唯一已知潜在分歧点是路径含符号链接时 os.path.abspath 与 Path.resolve() 的符号链接解析行为差异（本项目 worktree 场景 ~/.agate 软链接命中的是 AGATE_ROOT 而非 AGATE_WORKSPACE，未直接命中此路径，但不能排除其他项目布局下的分歧）；未来若 resolve_workspace 的路径构造约定变化（如 task_dir 不再保证两级嵌套），本地推导会静默产出错误路径而无测试覆盖预警
recommendation: 后续改动 check-gate.py 时，将 gate_p4 的 CODE-MAP.md 路径推导改为 import agate_common 并调用 resolve_workspace(找到 task_dir 对应的 project_root)，与项目其余脚本（agate-migrate-workspace.py / pre-commit-gate.py / check-debt.py / ci-gate-backstop.py）保持同一权威解析源，消除重复路径算术；同时补一个覆盖"task_dir 非标准两级嵌套"边界场景的回归测试
closure_criteria:
  - gate_p4 的 CODE-MAP.md 路径解析改为调用 agate_common.resolve_workspace（或等价的单点权威封装），不再本地重新推导路径层级
  - 新增回归测试覆盖 task_dir 与 workspace 非标准两级嵌套关系的场景，验证路径解析仍正确
  - 全量 pytest + consistency 0 ERROR
source: review
created_at: 2026-08-20
task_id: TAG0007
closed_at: 2026-09-04
```

## DEBT0017

```yaml
id: DEBT0017
category: technical
title: check-gate.py gate_p4「## 新增文件核对表」子串判定在自指/dogfooding 场景下存在假阴性，TAG0007 自身 P4 产出未对新增文件打标准 CODE-MAP 标记
status: closed
priority: low
evidence:
  - ref: agate/scripts/check-gate.py
    note: "L713：`if \"## 新增文件核对表\" not in _read_text(p4_impl_check):` 用子串包含判定
      P4-implementation.md 是否已补「新增文件核对表」小节，未限定必须整行/标题形式匹配（如
      `^## 新增文件核对表\\s*$`）——只要该字符串以任意上下文（含说明性散文）出现在文件任意
      位置即判定为满足，L715 触发的 WARNING（骨架/CODE-MAP 机制已采用但缺该标题）因此被
      静默跳过"
  - ref: agate-workspace/tasks/TAG0007-project-structure/P7-consistency.md
    note: "第2节「CODE-MAP 核对」完整独立论证（2.1 复核问题属实：TAG0007 自己的
      P4-implementation.md 第71行命中的『## 新增文件核对表』字符串只是描述『给协议卡片模板
      新增了一个标题叫这个的小节』的说明性文字，非 TAG0007 自己为自己新增文件
      （skeleton-template.md/code-map-template.md/agate-workspace/agents/CODE-MAP.md/3个
      测试文件）真正填写的核对表；标记级正则 grep `[CODE_MAP_UPDATED]`/`[CODE_MAP_EXEMPT]`
      在该文件中 0 命中。2.2 独立判定为 [CODE_MAP_DRIFT:]——真实偏离但不构成 P7 级
      [BLOCKER]，因 gate_p4 WARNING 本就非阻断、且不影响 P6 11/11 PASS 判定；P7 结论：
      不打回本轮 P7，建议后续补核对表附录或登记技术债，两种路径均可）"
  - ref: agate/scripts/check-gate.py
    note: "closure：本次 TAG0031-P4 commit 将「新增文件核对表」判定改为整行/标题级正则
      （check-gate.py:1038 实际实现 `re.search(r\"^##\\s+新增文件核对表\", text, re.MULTILINE)`——
      刻意不加 `\\s*$` 结尾锚点，允许标题行尾附加说明文字，见 BDD-11 回归守卫），替代原子串包含
      `in` 判定（此前 recommendation 段落给出的 `\\s*$` 写法是设计阶段草案，实现时按 BDD-11
      放宽为不要求行尾无内容，protocol-alignment-review 2026-09-04 已核实两者语义差异并确认代码/
      测试为准）"
  - ref: agate/tests/unit/test_check_gate.py
    note: "closure：BDD-10/11（test_tag0031_bdd_10_gate_p4_self_referential_prose_not_matched /
      test_tag0031_bdd_11_gate_p4_real_heading_trailing_text_satisfied）全绿"
impact: 任一后续任务在"自指/dogfooding"场景（任务自身产出文档里用说明性文字描述"新增了一个标题叫
  『## 新增文件核对表』的小节"这类元描述，而非真正逐文件填写的核对表）下，gate_p4 的子串判定会被
  这类说明性文字误判为"已满足"，本该触发的 WARNING（提醒补充新增文件核对表）被静默跳过；同时
  TAG0007 自身作为骨架+CODE-MAP 机制的首个落地任务，其 P4-implementation.md 对本次新增文件的
  CODE-MAP 处置只用叙事方式交代、未使用标准 [CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT] 标记逐条落标，
  构成机制的自我应用缺口——不影响任何 BDD PASS 判定或 gate exit code，但与该任务要求未来所有
  任务遵守的标准格式不一致
recommendation: 二事并记，均为低成本后续处理——① check-gate.py 的 gate_p4 判定改用整行/标题级
  正则匹配（如 `re.search(r"^## 新增文件核对表\s*$", text, re.MULTILINE)`）替代当前子串包含
  `in` 判定，消除自指场景下说明性文字被误判为"已满足"的假阴性；② 后续任一涉及 CODE-MAP 机制
  自指场景的任务（或专门处理本债的任务）为 TAG0007 的 P4-implementation.md 补一份真正的「新增
  文件核对表」附录（逐个列出 skeleton-template.md/code-map-template.md/
  agate-workspace/agents/CODE-MAP.md/3 个测试文件，标注 [CODE_MAP_UPDATED] 或
  [CODE_MAP_EXEMPT：理由]），或确认无需补齐的替代方案并记录理由
closure_criteria:
  - gate_p4 改用整行匹配（或等价的健壮判定方式，如标题级正则）替代当前子串包含判定
  - TAG0007（或后续任一涉及 CODE-MAP 机制自指场景的任务）补齐自己新增文件的标准 CODE-MAP
    标记，或明确评估后确认无需补齐并记录替代方案理由
  - 全量 pytest + consistency 0 ERROR
source: review
created_at: 2026-08-20
task_id: TAG0007
closed_at: 2026-09-04
```

## DEBT0018

```yaml
id: DEBT0018
category: technical
title: check-gate.py 的 agate_common import 降级 stub 返回 0/空——安装破损（agate_common 不可导入）边缘消费脚本呈 false-PASS 方向（gate 漏报而非误报）
status: closed
priority: low
evidence:
  - ref: agate-workspace/tasks/TAG0022-confirmed-problems/P4-review.md
    note: "INFORMATIONAL #2（Pass 2 I2，L93-96）：check-gate.py except ImportError 降级 stub 中
      count_p7_markers → (0,0)、count_p6_pass_fail → (0,0)、count_code_map_lines → 0——若
      agate_common 缺失/损坏（安装破损），gate_p7 的 BLOCKER/DEVIATION 计数与 CODE_MAP 转抄核对
      会假通过；count_markers → 0 侧是 fail-closed（[NEED_CONFIRM] 字面 + nc_blocking==0 → exit 1）。
      评审 Fix 建议：降级 stub 改显式失败（如 P7 分支检测 read_rules_yaml is None or count_p7_markers
      is None 时输出「安装破损」错误并 return 1），或登记本债（低优先）"
  - ref: agate/scripts/check-gate.py
    note: "L73-160 except ImportError 降级 stub 块：count_p7_markers → (0,0)（L141-142）、
      count_p6_pass_fail → (0,0)（L138-139）、count_code_map_lines → 0（L147-148）、
      count_markers → 0（L114-115）；消费点（gate_p7 L1075-1076 / gate_p6 L1015-1016 /
      gate_p4 L1168-1170）直接使用返回值，无安装破损检测——数据缺失即按 0/空降级（false-PASS 方向）；
      方向不一致是既有降级先例 parse_gate_commands_block → (False, [])（L104-105）的延续，代码注释
      （L110-112）已声明"
  - ref: agate/scripts/agate_common.py
    note: "共享读取器单点（count_p7_markers L951 等 M2-0038 节）——import 成功路径由 agate_common
      提供；降级 stub 仅在 agate_common 整体不可导入（安装破损）时生效，正常安装不可达"
  - ref: agate/scripts/check-gate.py
    note: "closure：TAG0031 本次 P4 commit 将 4 个消费点（gate_p7 BLOCKER/DEVIATION 计数、gate_p6
      pass/fail 计数、gate_p4 CODE-MAP 转抄核对）改为 fail-closed——检测到降级哨兵值时输出「安装
      破损：agate_common 不可导入」错误并 return 1，不再静默 0/空假通过"
  - ref: agate/tests/unit/test_check_gate.py
    note: "closure：TAG0031 BDD-12（4 个子用例，覆盖 4 个消费点各自 fail-closed 行为）+ BDD-13
      （回归守卫，正常安装路径判定不变）全绿，属 gate_commands.P5 全量 pytest 覆盖范围"
impact: 仅在 agate_common 缺失/损坏（安装破损边缘）触发，正常安装不可达；方向为 gate 漏报而非误报——
  破损安装下 gate_p7 BLOCKER/DEVIATION 计数与 P4 CODE_MAP 转抄核对静默假通过（0 ERROR 观感），且
  与 count_markers 侧 fail-closed 方向不一致，排查「安装破损」问题时判断成本高
recommendation: 降级 stub 改为显式失败（fail-closed）：消费分支检测关键读取器（read_rules_yaml /
  count_p7_markers / count_p6_pass_fail / count_code_map_lines）为降级哨兵时输出「安装破损：
  agate_common 不可导入」错误并 return 1；或将降级统一为显式异常/哨兵值而非 0/空
closure_criteria:
  - check-gate.py 在 agate_common 不可导入时，对依赖共享读取器的 gate 分支（gate_p7/gate_p6/gate_p4
    CODE_MAP）输出显式「安装破损」错误并 return 1（fail-closed），不再静默 0/空假通过
  - 新增回归测试覆盖 agate_common 缺失（模拟 import 失败）时上述分支的 fail-closed 行为
  - 全量 pytest + consistency 0 ERROR
source: review
created_at: 2026-08-22
task_id: TAG0031
closed_at: 2026-09-04
```

## DEBT0019

```yaml
id: DEBT0019
category: technical
title: check-gate.py._check_roadmap_done() 用固定索引 split("|") 解析 roadmap.md 表格，无列数完整性校验
status: closed
priority: low
evidence:
  - ref: agate/scripts/check-gate.py
    note: "_check_roadmap_done()（约 L1181-1206）：逐行 split(\"|\") 按固定索引取「关联任务」/
      「状态」列，未校验实际分列数是否等于表格应有列数（9，含首尾空列）"
  - ref: agate-workspace/tasks/TAG0023-mechanism-checks/P4-review.md
    note: "原文：\"已用 awk -F'|' 核实当前 roadmap.md 全文无嵌入 | 的标题行...但标题是自由技术
      文本，一旦未来某条描述里写进字面 |...列会整体错位\""
  - ref: agate-workspace/tasks/TAG0024-toolchain-md-field-set/P6-evidence/check-gate-debt-fixes/bdd-20.log
    note: "closure：TAG0024 落地 _ROADMAP_EXPECTED_COLS=9 精确列数校验，BDD-20（含字面 | 的行不
      误判）+ BDD-21（既有合法表格判定结果不变，回归）均 P6/P6.5 独立复核 PASS"
impact: 未来若 roadmap.md 某行描述文本包含字面 `|` 字符，该行状态判定可能错位（漏判或误判）
recommendation: 加一条"实际列数应为 9（含首尾空列）否则跳过/WARNING"的防护，不必用完整 markdown
  表格解析器
closure_criteria:
  - 新增防护逻辑（列数校验，非法列数跳过/WARNING）
  - 对应回归用例（构造含 | 字符的行验证不误判）
  - 全量测试通过
source: review
created_at: 2026-08-25
task_id: TAG0023
scheduled_task: TAG0024
status: closed
closed_at: 2026-08-25
```

## DEBT0020

```yaml
id: DEBT0020
category: technical
title: check-gate.py._check_roadmap_done() 调用点用相对 CWD 的硬编码路径拼接 roadmap.md，与同批次其他新增函数的 repo-root 定位风格不一致
status: closed
priority: low
evidence:
  - ref: agate/scripts/check-gate.py
    note: "约 L1224 调用点：roadmap_path 用相对 CWD 硬编码拼接，未走同批次其他新增函数的
      repo-root 定位方式"
  - ref: agate-workspace/tasks/TAG0023-mechanism-checks/P4-review.md
    note: "原文：\"若脚本被非仓库根 CWD 调用，_read_text(roadmap_path) 静默返回''...'路径解析
      失败'和'确实无关联RM'被静默合并成同一结果\""
  - ref: agate-workspace/tasks/TAG0024-toolchain-md-field-set/P6-evidence/check-gate-debt-fixes/bdd-22.log
    note: "closure：TAG0024 落地 git rev-parse --show-toplevel 仓库根锚定，BDD-22（非仓库根 CWD
      正确定位）+ BDD-23（非 git 环境区分性提示）+ BDD-24（仓库根既有场景判定不变，回归）均
      P6/P6.5 独立复核 PASS"
impact: 环境差异下（非仓库根 CWD 调用）新增的 P8 roadmap-done 检查可能被静默绕过而无任何提示
recommendation: 对齐同批次其他函数用 `git rev-parse --show-toplevel` 拼 repo-root 路径，或至少
  在 roadmap.md 确实不存在时输出区分性 stderr 提示
closure_criteria:
  - 路径定位方式对齐（改用 repo-root 拼接）或加区分性提示
  - 回归用例覆盖非仓库根 CWD 调用场景
  - 全量测试通过
source: review
created_at: 2026-08-25
task_id: TAG0023
scheduled_task: TAG0024
status: closed
closed_at: 2026-08-25
```

## DEBT0021

```yaml
id: DEBT0021
category: management
title: RM-AG0032 在 roadmap.md 现存 3 行（backlog/scheduled/done），P2 设计"新增一行"策略与 P4 判定算法"任一非done即阻断"存在潜在交互副作用
status: closed
priority: low
evidence:
  - ref: agate-workspace/tasks/TAG0023-mechanism-checks/P6-acceptance.md
    note: "关闭验收锚：修复（roadmap RM-AG0032 原地合并为单行 done）在 TAG0023 任务范围内落地并验收"
  - ref: agate-workspace/roadmap/roadmap.md
    note: "RM-AG0032 三行记录（backlog/scheduled/done），「关联任务」列分别为空/TAG0020/TAG0020"
  - ref: agate-workspace/tasks/TAG0023-mechanism-checks/P4-review.md
    note: "原文：\"若未来任何人对 task_id=TAG0020 重跑 check-gate.py P8，会被这条已过时的
      scheduled 行永久阻断，即便 done 事实已经记录在后面那行\""
impact: 实际触发概率低（TAG0020 是已发布历史任务，通常不会重跑 P8 gate），但属未被察觉的设计-实现
  交互副作用
recommendation: 改为原地更新已有行状态列（而非追加新行），或调整算法为"同 RM_id+task_id 分组，组内
  任一行为done即视为已完成"
closure_criteria:
  - 主 Agent/后续任务决策采纳其中一种方案并落地
  - 回归用例覆盖
closed_at: 2026-08-25
closure_note: "按 recommendation 选项①落地——roadmap.md 原地合并为单行 done（删除 backlog/scheduled 两行，保留并清理 done 行文案），采纳方案后无需算法调整；与 DEBT0021 判定算法无交互副作用"
source: review
created_at: 2026-08-25
task_id: TAG0023
```

## DEBT0022

```yaml
id: DEBT0022
category: management
title: 复盘归档断链——roadmap 4 条目引用 retrospective-tag0019-21.md 为证据源，该文件从未入库
status: closed
priority: low
task_id: TAG0024
evidence:
  - ref: agate-workspace/tasks/TAG0024-toolchain-md-field-set/P6-acceptance.md
    note: "发现点：TAG0024 合并审计经 check-debt 检出断链；2026-08-26 hotfix 关闭（原文补提交入库 +
      roadmap 引用补实际路径），详见 closure_note"
  - ref: agate-workspace/roadmap/roadmap.md
    note: "RM-AG0042/43/44/45 的证据列均引用 'retrospective-tag0019-21.md（问题 10/措施 9 等）'，但
      git log --all --diff-filter=A -- '*retrospective-tag0019*' 为空——文件从未提交入库"
  - ref: agate-workspace/tasks/TAG0023-mechanism-checks/P1-requirements.md
    note: "TAG0023 的 P1/P2 卡同样引用该文件为事实基线"
impact: 证据断链——4 条 roadmap 条目（含已 done 的 RM-AG0042/43/44/45）的事实依据不可追溯；
  复盘引用外部文件而无入库校验时，同类断链会再次发生
recommendation: ①若原文仍在某 session/归档中则补提交；若已丢失，在 4 条 roadmap 证据列标注
  "原文未入库，以 roadmap 记载结论为准" ②是否要机制化（P8/复盘流程校验引用文件入库存在性）
  由用户评估——倾向不加新 gate（用户偏好），优先纪律：复盘引用的文件必须随复盘同批入库
closure_criteria:
  - retrospective-tag0019-21.md 补提交入库，或 roadmap 4 条证据列完成"原文未入库"标注
closed_at: 2026-08-26
closure_note: "按选项①落地——原文在 dsh-workspace/agate-research/archived/ 找到（写了但从未入库），
  补提交至 agate-workspace/reviews/retrospective-tag0019-21.md；roadmap.md 2 处裸文件名引用
  同步补实际路径。机制化校验（②）按 recommendation 不加新 gate，纪律落点：复盘引用文件随复盘同批入库"
source: review
created_at: 2026-08-25
```

## DEBT0023

```yaml
id: DEBT0023
category: protocol
title: gate_commands 的 P3* 前缀键被静默收集为 TDD 测试命令执行（无任何 gate 拦截）
status: closed
priority: low
evidence:
  - ref: agate/scripts/agate-read-gate-commands.py:60
    note: "key.startswith('P3') and not is_gate_meta_key(key) 收集所有 P3* 非元键为测试命令"
  - ref: agate/scripts/agate_common.py:79-87
    note: "is_gate_meta_key 只精确匹配 _formatter/_timeout_seconds 后缀，P3_xxx 不被豁免"
  - ref: agate/scripts/agate_common.py:679-693
    note: "is_legal_gate_key 对 P3_xxx 形态返回 True（P3 为合法阶段 + 合法后缀），仅对账 WARNING 不拦截"
  - ref: agate-workspace/tasks/TAG0026-maintainability-gate/P2-review.md
    note: "TAG0026 P2 评审实测：P2-design 靠'禁用 P3_xxx 键'约定规避，协议层无机械防护"
  - ref: agate-workspace/tasks/TAG0029-gate-parser-fix/P6-evidence/p6-bdd-4.log
    note: "closure（TAG0029，task_id=TAG0029）：P6 BDD-4（P3_xxx 不收集）实跑 PASS"
  - ref: agate-workspace/tasks/TAG0029-gate-parser-fix/P6-evidence/p6-bdd-5.log
    note: "closure（TAG0029）：P6 BDD-5（裸 P3 收集 + 元键豁免）实跑 PASS"
  - ref: agate-workspace/tasks/TAG0029-gate-parser-fix/P6-evidence/p6-bdd-6.log
    note: "closure（TAG0029）：P6 BDD-6（P2 卡禁令子节）实跑 PASS；judge 9/9 passed 见 P6.5-judge-verdict.md"
impact: 未来任务在 gate_commands 声明 P3_xxx 辅助检测键时，该命令会被 check-tdd-red 在 P3 阶段当作
  测试命令执行（可能误报红灯或产生副作用），且无任何 gate/对账机制拦截（对账 WARNING 亦不触发）
recommendation: 后续协议任务评估：agate-read-gate-commands.py 收集侧收紧（如 P3 仅精确键 + 白名单
  后缀）或 is_gate_meta_key 扩展协议级辅助键约定；并补 read-gate-commands 单测锁定收集行为
closure_criteria:
  - read-gate-commands 对 P3* 键的收集行为有单测锁定，协议文档（P2 卡 gate_commands 节）写明
    P3_xxx 键禁止声明及其原因
source: review
created_at: 2026-08-30
task_id: TAG0026
closed_at: 2026-09-04
closure_note: "TAG0029 关闭：① BDD-4/BDD-5 单测锁定（test_tag0029_gate_parser_fix_b.py，P6 BDD-4/5 PASS）；② agate/phase-cards/P2-design.md L182-189 禁令子节（含白名单 + 原因），P6 BDD-6 PASS；P5 全量 1444 绿 + judge 9/9 passed"
```


## DEBT0024

```yaml
id: DEBT0024
category: protocol
title: P3 TDD 测试夹具构造"假 gate exit"（mock/前置产物），未用真实 check-gate 实测——错误前提红灯不暴露语义冲突
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0027-orchestration-semantics/retrospective.md
    note: "P3 TDD 测试契约复制了设计的错误 exit 2 前提，红灯未暴露语义冲突（测试用 mock 造 exit 0/1/2 场景，与真实 check-gate 语义脱节）；若夹具走真实 gate（补 P5 baseline + fail-list），CRITICAL 会在 P3 测试设计期而非 P4 review 期暴露"
  - ref: agate-workspace/tasks/TAG0027-orchestration-semantics/P4-review.md
    note: "P4 review 实证发现 check-gate exit 2 双义语义错误前提 → P1/P2/P3/P4 四层返工（本任务最大返工事件）"
  - ref: agate-workspace/tasks/TAG0030-acceptance-blindspot/P6-acceptance.md
    note: "closure（TAG0030，task_id=TAG0030）：P6 验收 BDD-19 PASS——tests/README「何时更新」节已写明『gate 消费方测试夹具须走真实 gate 语义』，见 P6-evidence/bdd-19-anchor.txt；P6.5 judge 21/21 复核通过"
impact: 测试 gate 消费方时用 mock 假 exit 码，会让测试契约复制设计的错误前提、红灯无法暴露语义冲突——语义类错误延迟到 review 期才暴露，返工成本放大（本任务实证四层返工）
recommendation: 测试 gate 消费方时夹具尽量走真实 gate 语义（构造真实前置产物让 check-gate 产 exit，而非 stub）；B1 夹具修复后的 3 例（补 P5 baseline + fail-list）是正确方向，协议测试设计文档应强调此要求
closure_criteria:
  - 协议测试设计约定写明"gate 消费方测试夹具须走真实 gate 语义"，P3 测试设计评审把此项列为必查
source: review
created_at: 2026-09-03
task_id: TAG0027
closed_at: 2026-09-04
```

## DEBT0025

```yaml
id: DEBT0025
category: protocol
title: 新增 CHECK 上线前未先全量扫描存量命中——CHECK 14/15 首跑 3 ERROR（dispatch.yaml law-1 / loop-orchestration OpenCode 前提行 / dispatch-protocol 字段语境）
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0027-orchestration-semantics/retrospective.md
    note: "清理/新检查上线前先全量扫描：新增 CHECK 前须确认存量零命中（CHECK 14/15 首跑 3 ERROR 是 B3a 批边界漏网）；新检查上线先跑一次全量扫描作为前置 gate"
  - ref: agate/scripts/check-protocol-consistency.py
    note: "CHECK 14/15（护栏 1 机械化）随 TAG0027 上线，首跑 3 ERROR 均由存量平台名未挂实现注记触发"
  - ref: agate-workspace/tasks/TAG0030-acceptance-blindspot/P6-acceptance.md
    note: "closure（TAG0030，task_id=TAG0030）：P6 验收 BDD-20 PASS——AGENTS.md「改脚本的工作流」已补『新增 CHECK 上线前先全量扫描存量』第 0 步，见 P6-evidence/bdd-20-anchor.txt；P6.5 judge 21/21 复核通过"
impact: 新 CHECK 上线时若存量有命中，CI 立即红灯、任务被迫补存量清理——清理批边界按文件归属划分但命中面是内容面（同文件可能含多个清理点且跨批），需在 CHECK 上线前一次性摸清存量
recommendation: 新检查上线流程补前置步骤：先跑一次全量扫描确认存量零命中（或登记已知命中清单 + 分批清理计划），再合并启用该 CHECK
closure_criteria:
  - 协议开发约定写明"新增 CHECK 上线前先全量扫描存量"，或 CI 配置支持 CHECK 先警告后强制的渐进上线
source: review
created_at: 2026-09-03
task_id: TAG0027
closed_at: 2026-09-04
```

## DEBT0026

```yaml
id: DEBT0026
category: protocol
title: 单 agent 大任务上下文耗尽（>5 文件/大文档清理类）——B3a 派单 agent 处理 7 文件文档清理卡在开工后，改拆 7 个小 agent 后稳定
status: closed
priority: medium
evidence:
  - ref: agate-workspace/tasks/TAG0027-orchestration-semantics/retrospective.md
    note: "B3a 派单个 agent 处理 7 文件文档清理（上下文重），卡在开工后；implementer.md 有分阶段落盘要求但单 agent 大任务仍易耗尽；改按文件拆 7 个小 agent 并行后解决"
  - ref: agate-workspace/tasks/TAG0027-orchestration-semantics/P4-dispatch-context-implementer-B3a.md
    note: "B3a 派发上下文（7 文件清理批），上下文耗尽中断重派 2 次"
  - ref: agate-workspace/tasks/TAG0030-acceptance-blindspot/P6-acceptance.md
    note: "closure（TAG0030，task_id=TAG0030）：P6 验收 BDD-21 PASS——dispatch-context.md 模板已补『改动体量 >5 文件按体量评估拆小』默认指导，见 P6-evidence/bdd-21-anchor.txt；P6.5 judge 21/21 复核通过"
impact: 多文件/大文档类任务单 agent 派发易上下文耗尽，浪费多轮（本任务 B3a 两次 + B3b 初始轮共 3 次中断重派），且 dispatch-context 已含分阶段落盘要求仍不够
recommendation: 大任务（多文件/大文档）派发前先评估单 agent 上下文体量，超限按文件数/体量拆小粒度派发（本任务拆 7 个后稳定）；与 §4 自主再派发设计（subagent 内部拆批）互为补充——外部拆小是现状兜底，内部自主拆是根治方向
closure_criteria:
  - dispatch-protocol 派发模板补">5 文件/大文档类任务按体量评估拆小"的默认指导；或 §4 自主再派发落地后由 subagent 内部拆批覆盖
source: review
created_at: 2026-09-03
task_id: TAG0027
closed_at: 2026-09-04
```

## DEBT0027

```yaml
id: DEBT0027
category: protocol
title: gate 命令解析器不处理行内注释/引号闭合 + check-tdd-red 假绿灯路径（测试运行器故障被吞成红灯证据）
status: closed
priority: high
evidence:
  - ref: agate-workspace/tasks/TAG0028-subagent-liveness-self-dispatch/retrospective.md
    note: "机制缺口 1：agate-read-gate-commands.py 值清洗 `val = raw.strip().strip(chr(34)).strip(chr(39))` 不剥离值内 `# 注释` 与残留引号——值不以 `\"` 结尾时 strip(chr(34)) 只剥开头引号，残留结尾引号 + 注释尾巴；消费方 bash -c 执行 unterminated quote 语法错误（exit 2），check-tdd-red judge 分支可能把该输出误判为红灯可推进（假绿灯）"
  - ref: agate-workspace/tasks/TAG0028-subagent-liveness-self-dispatch/P2-dispatch-context-architect-fix2.md
    note: "P2 fix2 触发记录：主 Agent 跑 P3 env baseline 发现 gate_commands.P3/P5 命令带注释尾巴，经最小 shell 验证确认 bash 语法错误；fix2 只改注释形态（行内→独立行）规避本任务，未修解析器根因"
  - ref: agate-workspace/tasks/TAG0029-gate-parser-fix/P6-evidence/p6-bdd-1.log
    note: "closure（TAG0029，task_id=TAG0029）：P6 BDD-1（行内注释→纯命令，bash-c exit 非 2）实跑 PASS"
  - ref: agate-workspace/tasks/TAG0029-gate-parser-fix/P6-evidence/p6-bdd-2.log
    note: "closure（TAG0029）：P6 BDD-2（未闭合引号 fail-closed）实跑 PASS"
  - ref: agate-workspace/tasks/TAG0029-gate-parser-fix/P6-evidence/p6-bdd-3.log
    note: "closure（TAG0029）：P6 BDD-3（exit2 中英辅证判 exit1）实跑 PASS；judge 9/9 passed 见 P6.5-judge-verdict.md"
impact: 协议文档写 gate_commands 时若在命令值同行带注释，命令解析串带残渣（残留引号 + 注释），P3 check-tdd-red / P5 执行失败；check-tdd-red 的 judge 分支把"测试运行器语法错误"误读为"测试红灯可推进"——测试根本没跑却被当红灯证据放行，验收真实性受威胁
recommendation: ① agate-read-gate-commands.py 值清洗剥离行内注释（首个未转义 ` #`）并校验引号闭合，输出纯命令或报解析错误（exit 非 0 + stderr），不再产出带残渣命令串；② check-tdd-red.py run_test_with_formatter 执行失败（exit 127 / 语法错误 exit 2 / 命令不可解析）不得计入红灯证据，judge 分支仅在测试运行器正常退出时才判定红灯可推进（关联 RM-AG0002 A/B 类盲区语义，扩展覆盖语法错误类）
closure_criteria:
  - agate-read-gate-commands.py 对"命令值同行带注释"输入产出纯命令（注释剥离 + 引号闭合校验），或报解析错误 exit 非 0
  - check-tdd-red.py 对测试运行器语法错误/不可解析输出判 exit 1（A 类），不再误判红灯可推进
  - 单测覆盖：带行内注释 gate_commands 解析出纯命令；bash -c 执行不报 unterminated quote
source: retrospective
created_at: 2026-09-03
task_id: TAG0028
closed_at: 2026-09-04
closure_note: "TAG0029 关闭：① 纯命令/解析错误exit非0（BDD-1/2，P6 PASS）；② exit2+中英辅证+零统计判exit1（BDD-3，P6 PASS）；③ 行内注释单测+bash-c无unterminated实测（P6 BDD-1证据）；P5全量1444绿+judge 9/9 passed"
```

## DEBT0028

```yaml
id: DEBT0028
category: technical
title: "dirname(dirname(...)) 本地 task_dir 路径推导同款模式的另外 2 处非本体实例（DEBT0016 同类扫描，本次范围锁定只处理 check-gate.py 一处）"
status: open
priority: low
evidence:
  - path: agate-workspace/tasks/TAG0031-debt-cleanup/P1-requirements.md
    note: "「同类扫描」节第 3 小节——全仓 grep `dirname(dirname\\|dirname(os.path.dirname` 命中 14
      行，按推导起点分两类：类别 A（以 task_dir 为推导起点，风险成立，因 task_dir 依赖 workspace
      相对目录层级约定）共 4 行/3 个实例，除 DEBT0016 本体（check-gate.py:983/986）外，另 2 处同款
      模式为 check-retrospective.py:74（`_scan_debt_roadmap_signal` 用
      os.path.dirname(os.path.dirname(os.path.abspath(task_dir...))) 推导 workspace 根，定位
      debt/tech-debt.md/roadmap/roadmap.md）与 agate-render-dispatch-prompt.py:191
      （`workspace_render = os.path.dirname(os.path.dirname(task_dir))` 用于渲染
      {AGATE_WORKSPACE} 占位符）；判定：本次不处理（P0-brief scope 锁定 gate_p4 CODE-MAP 路径一处，
      其余属越界），按同类扫描规则转入 BDD-14 登记为新 DEBT，不留白"
impact: 若未来 workspace 布局非标准嵌套（如经 .agate.env 的 AGATE_WORKSPACE= 覆盖工作区位置），
  check-retrospective.py 的 debt/roadmap 信号扫描定位、agate-render-dispatch-prompt.py 的
  {AGATE_WORKSPACE} 占位符渲染均可能静默产出错误路径而无提示，与 DEBT0016 本体描述的风险同源，
  只是尚未发生在已修复的 gate_p4 一处
recommendation: 后续任务处理时，将两处推导改为 import agate_common 并调用
  resolve_workspace(找到 task_dir 对应的 project_root)，与 DEBT0016 本体的修复方式对齐，消除
  重复路径算术；同时补覆盖 task_dir 非标准两级嵌套场景的回归测试
closure_criteria:
  - check-retrospective.py:74 与 agate-render-dispatch-prompt.py:191 均改为调用
    agate_common.resolve_workspace（或等价单点权威封装），不再本地重新推导路径层级
  - 新增回归测试覆盖 task_dir 与 workspace 非标准两级嵌套关系的场景
  - 全量 pytest + consistency 0 ERROR
source: review
created_at: 2026-09-04
task_id: TAG0031
```

## DEBT0029

```yaml
id: DEBT0029
category: technical
title: "check-gate.py:881 gate_p2 bootstrap 骨架声明校验的标题字符串子串判定（DEBT0017 同款模式，风险高于本体——此处触发 return 1 阻断性）"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0031-debt-cleanup/P1-requirements.md
    note: "「同类扫描」节第 4 小节——grep `not in _read_text(` agate/scripts/check-gate.py，除
      DEBT0017 本体（check-gate.py:990，「## 新增文件核对表」，WARNING 非阻断）外，另命中 1 处
      同款子串判定且风险更高：check-gate.py:881（gate_p2，project_phase: bootstrap 分支的
      「## 骨架声明」标题存在性校验），`\"## 骨架声明\" not in _read_text(skeleton_file)`——与
      DEBT0017 本体同一子串判定缺陷，但此处触发的是 return 1（阻断性），gate_p2 的 bootstrap
      骨架声明检查比 DEBT0017 描述的场景更容易因假阴性/假阳性判定错误产生真实阻断误判；判定：
      本次不处理（P0-brief scope 锁定「新增文件核对表」一处），按同类扫描规则转入 BDD-14 登记为
      新 DEBT，正文加粗提示避免被误认为已随 DEBT0017 一并修复"
impact: "**本条风险高于 DEBT0017 本体**——若骨架声明文件中出现说明性散文提及『## 骨架声明』字样
  （而非真正的标题行），子串判定会误判为已满足，本该触发的骨架缺失检测被静默跳过；反向场景（标题
  确实存在但缺失其他必要内容）同样可能因子串宽松匹配产生误判；由于此处判定结果直接决定 gate_p2
  是否 return 1（阻断 commit），误判方向若为假阳性（应阻断而未阻断）会让不完整的骨架声明蒙混过
  P2 阶段，若为假阴性（应通过而被阻断）则会误伤合法产出"
recommendation: 后续任务处理时，将 check-gate.py:881 的判定改用整行/标题级正则匹配（如
  `re.search(r\"^## 骨架声明\\s*$\", text, re.MULTILINE)`）替代当前子串包含 `in` 判定，修复方式
  与 DEBT0017 本体（check-gate.py:990）对齐
closure_criteria:
  - check-gate.py:881 的 gate_p2 骨架声明判定改用整行匹配（或等价健壮判定方式，如标题级正则）
    替代当前子串包含判定
  - 新增回归测试覆盖"说明性散文提及标题字样但非真正标题行"场景不被误判为已满足
  - 全量 pytest + consistency 0 ERROR
source: review
created_at: 2026-09-04
task_id: TAG0031
```

## DEBT0030

```yaml
id: DEBT0030
category: technical
title: "P6.5 judge dispatch-context 白名单/P8 多路并行版本协调两处协议文档完善（TAG0031 复盘发现）"
status: open
priority: low
evidence:
  - path: agate-workspace/tasks/TAG0031-debt-cleanup/retrospective.md
    note: "「发现的问题」节两条机制缺口：① P6.5 judge dispatch-context 白名单（仅
      p1-requirements.md/p2-design.md/.state.yaml/gate-events.jsonl/p6.5-judge-verdict.md
      五个固定文件名，不含 gate-diagnosis.md）只定义在 check-judge-verdict.py 源码常量里，
      未在 P6-acceptance.md 卡片或 dispatch-protocol.md「Judge 信息隔离」节显式列出完整清单，
      也未提示「示例代码块里的字面 PASS/FAIL 文本同样受全文预判扫描约束」这一反直觉细节——本次
      任务撰写 P6.5-dispatch-context-judge.md 两次踩坑（白名单外文件引用 + 预判扫描误伤示例）；
      ② P8 卡片未覆盖多个并行任务共享 CHANGELOG.md/README 版本徽章/git tag 序列时应如何协调
      版本号——三路并行（TAG0029/30/31）场景下产生了错误的初始假设（延后到合并后统一处理），
      与兄弟任务 TAG0029 已独立完成标准 P8 流程并合并 main 的实际情况不符，导致 P8 阶段中途
      改变策略（补做 git merge origin/main + 重新规划版本号 v0.67.2）"
impact: 后续任务撰写 P6.5 dispatch-context 时可能重复踩同样的白名单/预判扫描坑，产生额外的
  格式修正轮次（本次消耗 2 轮纯格式修正，判定内容未变但增加了派发/验证开销）；后续多路并行批次
  的 P8 阶段可能重复本次"临场推测版本协调策略、与实际不符再补救"的低效路径
recommendation: ① `agate/phase-cards/P6-acceptance.md`（或专门的 P6.5 小节）补充完整白名单
  清单 + "gate-diagnosis.md 不在白名单内，示例文本也受预判扫描约束"的显式提示；
  `agate/dispatch-protocol.md`「dispatch-context 规范」节补一条"含示例代码块时同样要避免行首
  PASS/FAIL 字面文本，可用占位符替代"的具体注意事项；② `agate/phase-cards/P8-release.md` 补
  "多路并行发布协调"节，建议 bump-version 前先同步主分支最新状态确认版本号资源未被占用
closure_criteria:
  - P6-acceptance.md 或 dispatch-protocol.md 补齐 P6.5 白名单完整清单 + 示例文本预判扫描提示
  - P8-release.md 补充多路并行版本协调检查项
  - 全量 pytest + consistency 0 ERROR
source: retrospective
created_at: 2026-09-04
task_id: TAG0031
```

## DEBT0031

```yaml
id: DEBT0031
category: technical
title: "P1 frontmatter phases 列表与正文裁剪声明一致性无机械校验（TAG0030 复盘发现）"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0030-acceptance-blindspot/retrospective.md
    note: "frontmatter 机制缺口：P1 phases 漏写 P2 靠 requirements-review 打回才暴露，check-frontmatter/check-gate P1 均未拦截——frontmatter phases 列表与正文裁剪声明的一致性依赖人工核对"
impact: "P1 阶段裁剪声明错误只能靠 review 打回暴露，额外消耗 review 轮次；严重时裁剪声明与实际产出不符直达下游阶段"
recommendation: "check-gate P1 阶段校验 frontmatter phases 列表与 P1-requirements.md 正文声明的阶段裁剪一致性；先加失败测试确认红再修"
closure_criteria:
  - check-gate P1 对 frontmatter phases 与正文裁剪声明做机械一致性校验（新测试覆盖）
  - 全量 pytest + consistency 0 ERROR
source: retrospective
created_at: 2026-09-04
task_id: TAG0030
```

## DEBT0032

```yaml
id: DEBT0032
category: technical
title: "agate-next P6→P7 A1 裁决把 provenance WARNING 误判假暂停并落盘模板残留（TAG0030 复盘发现）"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0030-acceptance-blindspot/retrospective.md
    note: "agate-next P6→P7 A1 裁决把 provenance WARNING（exit 2，根因 P3 缺 agent 字段）误判为验收异常，触发假暂停并落盘 P6-exit2-resolution.md 模板残留（未跟踪，非真实事件产物）；本次任务已连带清理，但机制未修复"
impact: "P6→P7 推进被误判阻断产生无效停顿与模板残留文件；残留未跟踪文件在 worktree 清理时连带删除，但假暂停本身浪费推进轮次"
recommendation: "agate-next A1 裁决区分 provenance WARNING（exit 2）与真实验收失败：provenance 类 exit 2 应转为明确提示而非假暂停；落盘模板残留时输出提示路径供人工确认删除"
closure_criteria:
  - agate-next P6→P7 对 provenance WARNING 不再假暂停（新测试覆盖 exit 2 分类）
  - 全量 pytest + consistency 0 ERROR
source: retrospective
created_at: 2026-09-04
task_id: TAG0030
```

## DEBT0033

```yaml
id: DEBT0033
category: technical
title: "check-debt 关闭 schema 校验器无任何 gate/CI 挂载 + closed 证据判定为 P[56] 子串启发式（TAG0030 复盘发现）"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0030-acceptance-blindspot/retrospective.md
    note: "DEBT 关闭 schema 校验器 check-debt 无任何 gate/CI 挂载，closed 证据判定为 P[56] 子串启发式：P8 纯 status 翻转关闭后 main 上 check-debt exit 1——关闭动作无机械防护"
impact: "DEBT 关闭动作可绕过证据校验直接翻转 status，关闭质量依赖人工自觉；main 上 check-debt 失败暴露时已晚"
recommendation: "check-debt 挂载 gate/CI（P8 关闭时强制校验证据存在）；closed 证据判定从子串启发式改为显式字段校验"
closure_criteria:
  - check-debt 挂载 gate/CI 且 closed 证据显式字段校验（新测试覆盖）
  - 全量 pytest + consistency 0 ERROR
source: retrospective
created_at: 2026-09-04
task_id: TAG0030
```

## DEBT0034

```yaml
id: DEBT0034
category: technical
title: "TAG0032 三步 legacy 软链迁移指引文案在 agate-install.py(_LEGACY_SYMLINK_MSG) 与 install.sh(heredoc) 双写"
status: open
priority: low
evidence:
  - path: agate/scripts/agate-install.py
    note: "_LEGACY_SYMLINK_MSG 模块常量（Python 侧 fail-closed 拒绝文案）"
  - path: install.sh
    note: "--versions 分支的 heredoc（shell 侧同一三步迁移指引），措辞需人工与 Python 侧保持同步"
impact: "两处文案漂移风险：改一处忘另一处 → 用户在两条入口看到不一致的迁移指引；BDD-2 只 grep Python 侧，install.sh 侧漂移不被测"
recommendation: "收敛到单一来源：install.sh --versions 的软链拒绝分支改为直接 exec agate-install.py（由其打印统一文案并 exit 1），或抽一份公共文案资源"
closure_criteria:
  - 三步迁移文案单一真相源（一处定义，另一处引用或委托）
  - 全量 pytest + consistency 0 ERROR
source: review
created_at: 2026-09-07
task_id: TAG0032
```

## DEBT0035

```yaml
id: DEBT0035
category: technical
title: "CodexAdapter pending 判据 status!='completed' 误判真机 Codex status=='failed' 终态为 pending（P5→P4 回退，TAG0033）"
status: closed
priority: high
evidence:
  - ref: "52fe210"
    note: "retreat: P5 -> P4 提交（P6 真机 V6 发现 F1）"
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/.archived/p6-pre-retreat-20260909/real-machine-p6.md
    note: "P6 verifier 首轮真机 V6：spin 会话 7 条 status=failed/exit_code=2 命令被 CodexAdapter 映射为 pending（exit=None/output_hash=None），detect 判不出 SPIN"
  - path: agate/scripts/agate-cmdstream-adapters.py
    note: "line ~739 pending = item.get('status') != 'completed'——未识别真机终态 'failed'"
  - ref: "5f704a0"
    note: "closure: TAG0033 P5 r3 F1 修复后重新技术验证通过（gate_commands.P5 全绿 + 真机 V1/V6③ 证 F1 已修）"
  - ref: "49d3353"
    note: "closure: TAG0033 P6 重做验收 30/30 PASS（F1 修复后；真机 V6 三态 FROZEN/NORMAL/SPIN 齐）"
  - ref: "f484895"
    note: "closure: TAG0033 P6.5 judge 独立复核通过（criteria 30/30 passed，partial: false）"
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P7-consistency.md
    note: "P7 §6-B 确认 5 条 closure_criteria 本任务 5/5 全满足（P5/P6 重新通过条补齐）"
impact: "不修则 CodexAdapter 对真机 Codex 已结束但非0退出的命令丢失 exit_code + output_hash：detect 对真机重复失败会话判不出 SPIN（BDD-15 真机侧不成立）；真机失败命令 CommandRecord.exit 恒 None；BDD-6 pending 判据真机假阳性。TAG0033 的 P6 验收声明会因此变假。"
recommendation: "pending 判据改为「无终态信号」口径：status in ('completed','failed') 或存在 completed_at_ms/exit_code → 走已完成路径提取 exit_code；仅 status in ('in_progress', 其它未知) 且缺 completed_at_ms/exit_code 时才算 pending。fixture codex-session.jsonl 补真机 status=='failed' 形态；P3 测试加覆盖（BDD-5/BDD-15 或新守护）。platform-notes.md Codex 章补真机 status 取值集（completed/failed/in_progress）。P1 §4.1 spike 描述补 'failed' 终态。"
closure_criteria:
  - "CodexAdapter 对 status=='failed' 且带 exit_code 的 item 映射为 exit=<非0 int> / ts_end=<完成时刻> / output_hash=<真实哈希>，非 pending"
  - "P3 测试覆盖 status=='failed' 形态；fixture 含真机 failed 样本"
  - "detect 对真机重复失败会话（复跑 P6 V6 ③）判 SPIN"
  - "全量 pytest 全绿 + consistency 0 ERROR + P5/P6 重新通过"
  - "platform-notes.md Codex 章含真机 status 取值集；P1 §4.1 补 'failed' 终态"
source: retreat
created_at: 2026-09-09
task_id: TAG0033
closed_at: 2026-09-09
```

## DEBT0036

```yaml
id: DEBT0036
category: technical
title: "platform-notes.md Codex 章「spawn_agent 嵌套深度未测 / max_depth=1 待 V7 复核」措辞滞后——P6 V7 已两次实测 depth=2 可用"
status: open
priority: low
evidence:
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P6-evidence/real-machine-p6.md
    note: "P6 V7 重做 attempt 2 实测 source.subagent.thread_spawn.depth == 2 的孙会话（agent_path == /root/p6redo2_child/p6redo2_grand）；.archived 首轮 V7 亦得 depth 1→2——两次独立证实"
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P7-consistency.md
    note: "P7 §5 / §6-A：deviation_count: 1（WARNING 级）——platform-notes.md 子代理派发小节 + 行 136 时效指针仍写「未测 / 待 V7 复核」，与实测事实滞后"
impact: "权威源（platform-notes.md，平台适配权威源）携带指向已实测事实的「未测」指针，误导读者；不影响 CodexAdapter 契约或 BDD-25（现「待复核」时效指针本身合规，test_bdd_25 现绿）"
recommendation: "把「未测」收敛为「已实测 depth=2 可用（P6 V7，2026-09，两次独立证实）」，保留 max_depth=1 事实行 + 交叉引用结构；回跑 test_bdd_25 + check-protocol-consistency.py --strict-errors-only 确认 BDD-25 不破、0 ERROR"
closure_criteria:
  - "platform-notes.md 子代理派发小节 + 行 136 时效指针措辞收敛为「已实测 depth=2 可用」"
  - "test_codex_platform_docs.py::test_bdd_25 绿"
  - "check-protocol-consistency.py --strict-errors-only 0 ERROR"
source: retrospective
created_at: 2026-09-09
task_id: null
```

## DEBT0037

```yaml
id: DEBT0037
category: protocol
title: "check-gate.py P4 完整度判据（暂存区有非 md/yaml 文件）在多提交阶段 / 回退后推进场景不完备——agate-next.py 因此拒绝推进，主 Agent 需手动 _advance"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md
    note: "TAG0033 复盘「问题 1」+「agate 反馈」条 1：P4 跨两批 commit（adapter-core / protocol-docs）与 P5→P4 回退后修复 commit 两个场景，check-gate.py P4 看 git diff --cached 无代码文件 → exit 1 → agate-next.py 查 P4 retreat=null → 「提示重试本阶段，不推进」"
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md
    note: "技术债登记核对清单「.state.yaml phase 同步」行：P4→P5 ×2 + P8→READY 因该局限手动 _advance + 补 state_transition 事件"
  - ref: agate/scripts/check-gate.py
    note: "_gate_p4：完整度代理判据 = 暂存区有非 md/yaml 文件；假设「离开 P4 时暂存区必有代码 diff」，多提交阶段 / 回退后再推进破坏该假设"
  - ref: agate/scripts/agate-next.py
    note: "_advance 前的 gate 判定消费 check-gate.py P4 exit 码；exit 1 + retreat=null → 不推进"
  - path: agate-workspace/tasks/TAG0034-dispatch-routing/retrospective.md
    note: "TAG0034 复盘再次命中：dispatch_plan static-batch（P4a/P4b/P4c 三批 commit），P4→P5 手动 _advance 一次；复盘「四、改进措施」+「agate 反馈」条 3 对本 DEBT 加权——static-batch 是可静态识别的信号（.state.yaml dispatch_plan.mode == static-batch），推进侧可据此开豁免路径"
impact: "多提交阶段任务 / 有回退的任务，主 Agent 必须手动改 .state.yaml phase + append_event state_transition 绕过——绕过路径未走 gate 校验，且违反「不用手动替代脚本」的编排纪律；后续同形态任务复发（TAG0033 + TAG0034 连续两个 static-batch 任务均命中）"
recommendation: "P4 完整度判据从「当前暂存区有代码 diff」放宽为「本 phase 的任一 commit 引入过代码 diff」（git log --oneline <phase 起点>..HEAD 扫非 md/yaml），或显式识别「回退后再推进」（.state.yaml retries[P4] 非空 + 已存在 wf(...-P4): commit）。落点 check-gate.py _gate_p4 + agate-next.py。同类扫描：其它 phase 的 check-gate 完整度判据是否共用同一「看暂存区」假设"
closure_criteria:
  - "check-gate.py P4 对「阶段工作已 commit、暂存区空」场景不再 exit 1（多提交阶段 + 回退后推进两个回归用例）"
  - "agate-next.py 在该场景正常推进 P4→P5，无需手动 _advance"
  - "P4 之外的 phase 完整度判据已同类核查，结论落盘"
  - "全量 pytest 全绿 + consistency 0 ERROR"
source: retrospective
created_at: 2026-09-09
task_id: null
```

## DEBT0038

```yaml
id: DEBT0038
category: protocol
title: "check-judge-verdict.py 信息隔离黑/白名单扫描误判 P6.5 dispatch-context——阶段卡片引用 / 角色文件路径 / P6-evidence 裸文件名三处假阳性"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md
    note: "TAG0033 复盘「问题 2」+「agate 反馈」条 2：P6.5 judge verdict 本体（30/30 passed）已通过，卡在 dispatch-context 措辞，主 Agent 重写后转绿"
  - ref: agate/scripts/check-judge-verdict.py
    note: "_check_blacklist：`p6-acceptance.md` 子串纯匹配命中 agate/phase-cards/P6-acceptance.md（阶段规格卡片，非 verifier 自述）——无 agate/phase-cards/ 路径豁免"
  - ref: agate/scripts/check-judge-verdict.py
    note: "_check_whitelist：白名单不含角色定义文件路径，与「每个 dispatch-context『输入文件』节都列角色文件」的通用惯例冲突；P6-evidence/ 目录白名单不认目录下裸文件名（如 real-machine-p6.md）"
  - ref: agate/dispatch-protocol.md
    note: "「Judge 信息隔离」节未写明 P6.5 dispatch-context 是「不列角色文件」的唯一例外"
impact: "P6.5 dispatch-context 按通用惯例列角色文件 / 引用阶段卡片 / 用 P6-evidence 裸文件名，均触发信息隔离拦截 → judge 已产出正确 verdict 仍需返工重写 dispatch-context；每个走 P6.5 的任务都可能踩"
recommendation: "① 黑名单 p6-acceptance.md 匹配加 agate/phase-cards/ 路径豁免；② 白名单显式允许角色定义文件路径，或在派发模板 / P6 卡片写明「P6.5 dispatch-context『输入文件』节不列角色文件（派发机制注入）」；③ P6-evidence/ 目录白名单认「目录下裸文件名」。落点 check-judge-verdict.py（_check_blacklist / _check_whitelist）+ dispatch-protocol.md「Judge 信息隔离」节 + P6 卡片"
closure_criteria:
  - "check-judge-verdict.py 对「dispatch-context 引用 agate/phase-cards/P6-acceptance.md」不再假阳性（回归用例）"
  - "角色定义文件路径 + P6-evidence/ 目录裸文件名两类引用不再被白名单拦截，或派发模板 / P6 卡片显式写明 P6.5 例外惯例"
  - "dispatch-protocol.md「Judge 信息隔离」节说明 P6.5 dispatch-context 的输入文件惯例"
  - "全量 pytest 全绿 + consistency 0 ERROR"
source: retrospective
created_at: 2026-09-09
task_id: null
```

## DEBT0039

```yaml
id: DEBT0039
category: protocol
title: "dispatch_plan 批次「执行阶段」标注易把「补协议文档正文」误标到 P7——architect 把 protocol-docs 批标 P7、主 Agent 判定后拉回 P4"
status: closed
priority: low
evidence:
  - path: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/retrospective.md
    note: "TAG0033 复盘「做得好」第 4 条 + 「agate 反馈」条 4：architect 原把 protocol-docs 批（补 platform-notes.md Codex 章 + SETUP.md 小节）标「P7 执行」；主 Agent 比照 TAG0030（doc-assertion 审计 P3 写红、内容 P4 补绿）拉回 P4，避免 P5/P6 带 6 条 by-design 红推进"
  - ref: agate/assets/execution-roles/architect.md
    note: "「批次设计」节未写明「补协议文档正文 = P4 实现工作」的边界"
  - ref: agate/dispatch-protocol.md
    note: "「派发编排机制」未区分「author 文档内容（P4）」vs「跨文件一致性验证（P7）」"
  - path: agate-workspace/tasks/TAG0034-dispatch-routing/P6-acceptance.md
    note: "closure：DEBT0039 并入 TAG0034（用户批准 2026-09-09）。P4a 落地 architect.md「批次设计」节含「补协议文档正文 = P4 实现工作、批次执行阶段标 P4」显式边界 + dispatch-protocol.md「派发编排机制」区分 author 内容（P4）vs 跨文件一致性验证（P7）（附 TAG0030 / TAG0033 先例）；三条 closure_criteria = BDD-48 / BDD-49 / BDD-50，P6 逐条 PASS"
  - path: agate-workspace/tasks/TAG0034-dispatch-routing/P7-consistency.md
    note: "closure：P7 consistency `check-protocol-consistency.py --strict-errors-only` 0 ERROR（第三条 closure_criteria）；P7 approved / deviation_critical_count 0"
impact: "架构师把「补协议文档正文」误标 P7 → 若主 Agent 未纠正，P5/P6 会带着 by-design 红（文档正文未补）推进，或 P7 阶段做了本属 P4 的实现工作、越权 author 内容"
recommendation: "在 architect 角色文件「批次设计」节 + dispatch-protocol.md「派发编排机制」写明：补协议文档正文（platform-notes / SETUP / phase-cards 等）= P4 实现工作，批次执行阶段标 P4；P7 只做跨文件一致性验证、不 author 文档内容。可附 TAG0030 / TAG0033 两处先例"
closure_criteria:
  - "architect.md「批次设计」节含「补协议文档正文 = P4」的显式边界说明"
  - "dispatch-protocol.md「派发编排机制」区分 author 内容（P4）vs 一致性验证（P7）"
  - "consistency 0 ERROR"
source: retrospective
created_at: 2026-09-09
task_id: TAG0034
closed_at: 2026-09-10
```

## DEBT0040

```yaml
id: DEBT0040
category: protocol
title: "append-only 事件账本（gate-events.jsonl）的写入测试无 tmp 隔离强制——单测真实调用 agate_common.append_event 写进仓库内 fixture 账本，跑测污染已提交文件"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0034-dispatch-routing/retrospective.md
    note: "TAG0034 复盘「三、发现的问题」条 1 +「agate 反馈」条 1：P6.5 judge 在 fresh context 跑全量 pytest 复核，测试用例真实调用 append_event，把 judge_verdict 事件追加进已提交的 fixture 账本 agate-workspace/tasks/TAG003{0,2,3}/gate-events.jsonl（非 TAG0034 目录）；发现后 git checkout 复原"
  - ref: agate/scripts/agate_common.py
    note: "append_event(task_dir, event) 按 task_dir 定位 gate-events.jsonl 并追加 + 更新 hash 链；测试若把 task_dir 指向仓库内真实/fixture 账本而非 tmp_path，写入落在版本控制文件上"
  - ref: agate/scripts/check-events.py
    note: "账本审计器不校验「跑测前后账本零新增」——测试副作用无 gate 兜底"
  - path: agate-workspace/tasks/TAG0030-acceptance-blindspot/P1-requirements.md
    note: "RM-AG0057 测试副作用 / 环境还原 gate 已存在，但覆盖的是创建型 E2E 清理钩子，未覆盖 append-only 账本这类写入污染"
impact: "跑一次全量 pytest 就可能改动 3 个历史任务的 committed 账本（重复 judge_verdict 事件 + hash 链错位）；污染需人工发现并 git checkout 复原，漏掉则错误账本被提交、破坏 hash 链可审计性；CI 若在脏工作树跑亦可能误判"
recommendation: "① test-designer.md / implementer.md 补硬规则：任何直接或间接调用 agate_common.append_event / 写 gate-events.jsonl 的测试必须把 task_dir 指向 tmp_path，禁止指向仓库内真实或 fixture 账本；② CI 加兜底步 `git diff --exit-code agate-workspace/tasks/*/gate-events.jsonl`（pytest 之后），非零即 fail；③ 可选：agate_common.append_event 在检测到目标路径位于 git 跟踪的 fixture 目录且非 tmp 时 warn"
closure_criteria:
  - "test-designer.md + implementer.md 含 append-only 账本测试 tmp 隔离的显式条文"
  - "存在回归用例：把 append_event 目标指向仓库内账本的测试形态被 lint / fixture 约束拦截"
  - "CI 有 `git diff --exit-code` 账本兜底步（或等效机制），故意污染能被 CI 捕获"
  - "全量 pytest 全绿 + consistency 0 ERROR"
source: retrospective
created_at: 2026-09-10
task_id: null
```

## DEBT0041

```yaml
id: DEBT0041
category: protocol
title: "agate-md-field-set 支持字段集与 check-p6-provenance.py 必备 frontmatter 字段集不同源——P3-test-cases.md 的 agent 字段落在缝里，P6→P7 被 exit 2 挡住"
status: open
priority: medium
evidence:
  - path: agate-workspace/tasks/TAG0034-dispatch-routing/retrospective.md
    note: "TAG0034 复盘「三、发现的问题」条 2 +「agate 反馈」条 2：P6→P7 被 check-p6-provenance.py exit 2 挡（P3-test-cases.md 缺 agent 字段）；releaser 用 agate-md-field-set 只能写 test_code_dir，该工具不支持给 P3 写 agent 字段，最终手工补整段标准 frontmatter header"
  - ref: agate/scripts/agate-md-field-set.py
    note: "字段白名单未覆盖 P3-test-cases.md 的 agent"
  - ref: agate/scripts/check-p6-provenance.py
    note: "约 573 行 sys.exit(2) when warning_found——对 P3-test-cases.md 缺 agent 字段判 WARNING 并 exit 2，阻断 P6→P7"
impact: "结构化字段写入工具与 provenance 检查器对「阶段产出必备 frontmatter 字段」认知不一致 → 主 Agent 需绕过工具手写 frontmatter（违反 RM-AG0048「同源铁律 / 消灭手写 frontmatter」初衷），且手写易漏字段再次触发 exit 2"
recommendation: "① 把 P3-test-cases.md 的 agent 加入 agate-md-field-set 支持字段；或 ② check-p6-provenance.py 对 P3-test-cases.md 的 agent 缺失降级为 WARNING 不 exit 2（P3 是 test-designer 唯一产出，agent 恒定）；根治向：两者共读同一份「阶段产出必备 frontmatter 字段」权威表（rules/ 下），消除字段集漂移"
closure_criteria:
  - "agate-md-field-set 能为 P3-test-cases.md 写 agent 字段，或 check-p6-provenance.py 不再因该字段缺失 exit 2"
  - "存在回归用例锁定该场景（releaser 正常流程不需手写 frontmatter）"
  - "全量 pytest 全绿 + consistency 0 ERROR"
source: retrospective
created_at: 2026-09-10
task_id: null
```
