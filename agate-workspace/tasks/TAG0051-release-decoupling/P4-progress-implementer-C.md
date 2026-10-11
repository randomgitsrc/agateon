# P4-progress — implementer-C (TAG0051)

- [读取] implementer.md 角色文件 + P4-dispatch-context-implementer-C.md（强制指令）。
- [读取] P2-design.md §1.1（M2/M3/M13/M14/M15/M16 落点）+ §3 决策 5 + §4 批表。
- [范围] 只改：agate/phase-cards/P8-release.md、agate/state-machine.md、agate/dispatch-protocol.md、agate/assets/execution-roles/implementer.md、AGENTS.md、agate/git-integration.md。不新增文件。
- [实测-约束] P3 红灯测试 agate/tests/unit/test_tag0051_docs_consistency.py 定义 BDD-1 禁用字面清单：
  - 非 P8 卡五处（state-machine/dispatch-protocol/implementer/…）：`git tag` / `tag 已创建` / `tag 创建` / `tag 检查` / `先 tag` / `commit + tag` / `tag 由主 Agent` / `VERSION_TAG_PREFIX` 不得出现。
  - P8-release.md 专用：`git tag 已创建` / `git commit/tag` / `git commit / git tag` / `同一 commit + tag` / `bump-version / git commit / git tag` 不得出现。
  - BDD-14：AGENTS.md 与 git-integration.md 中**首个 `git tag`** 必须出现在**首个**「合并后 / main CI 绿 / CI 全绿」标记之后（或整体无 `git tag`）。
  - BDD-15：AGENTS.md（+release.yml）须含「回退」「重打」「外部消费/已被消费」，且「回退」索引 < 「补丁」索引。
- [实测-anchor] obligations.yaml（Impl-B 已改）引用 P8-release.md 的节标题 `#产出规格` / `#gate 规则` / `#READY 收尾检查（P8 gate 通过后）` / `#如果是首次进入本阶段`，state-machine.md 的 `#READY 收尾检查（P8 gate 通过后、标记 READY 前）` ⇒ 这些标题**原样保留**。

## 改动落地（6 文件）
- `agate/phase-cards/P8-release.md`（M2）：删两处 `- [ ] git tag 已创建`；`git commit/tag`、`git commit / git tag`、`同一 commit + tag`、`bump-version / git commit / git tag` 四类字面全部消除；CHANGELOG 载体改为 `check-changelog.py <task_id>`；删「版本号变更确认 / 暂存区 version 变更 / git log v{prev}..HEAD / 从 P2 packages 验证 version 文件路径」；`## gate 规则` 与 `## 如果是首次进入本阶段`（+`## 产出规格`/`## READY 收尾检查（P8 gate 通过后）`）标题**原样保留**。
- `agate/state-machine.md`（M3）：P8→READY 转移删 `git tag` / version 双路径 / `git tag -l "${VERSION_TAG_PREFIX}..."`；READY 收尾删 `git tag 已创建`；新增发布授权说明（独立流程 + 人工授权入口 `workflow_dispatch`；不引第二套阻塞语义；任务止于 READY）。
- `agate/dispatch-protocol.md`（M15）：`:881` P8→READY 行改写为 canonical 口径 + `check-changelog.py` 载体；顺带把「全量重跑点审计」表内 `P8 bump-version 后重跑` → `P8 交付收尾后重跑`（一致性）。
- `agate/assets/execution-roles/implementer.md`（M16）：`:101` 去 tag（只禁 commit）+ 内嵌 canonical。
- `AGENTS.md`（M13）：清单首加「发布不在任务状态机内 + canonical + 不可逆动作须授权」说明；第 4 步改为「先合 release PR → 合并后 main CI 绿 → 再打 tag」；5a 补救改为「已支持 `workflow_dispatch` 可人工重跑」（Impl-A 已在 release.yml 落 `workflow_dispatch`）；普通 merge 条与新顺序对齐；**新增「发布失败处置」小节**（先回退 tag/Release 重打，仅已被外部消费才出补丁）。
- `agate/git-integration.md`（M14）：release PR 普通 merge + G-5 tag 时点与 AGENTS.md 统一（含「合并后 main CI 绿」标记在前）。

## 自检实测（命令输出）
`for f in <4 语料文件>; do grep -n "git tag" "$f"; grep -n "tag 已创建" "$f"; done` → **四文件均 0 命中（无输出）**：
```
agate/state-machine.md                      git_tag=0  tag_created=0
agate/phase-cards/P8-release.md             git_tag=0  tag_created=0
agate/dispatch-protocol.md                  git_tag=0  tag_created=0
agate/assets/execution-roles/implementer.md git_tag=0  tag_created=0
```
- `python3 -m pytest agate/tests/unit/test_tag0051_docs_consistency.py -q` → **4 passed**（BDD-1 六处语料 + BDD-14 AGENTS.md/git-integration.md + BDD-15 失败处置）。
- `python3 -m pytest agate/tests/unit/test_tag0050_obligations_enforcement.py -q` → 全绿（anchor 无悬空）。
- `python3 agate/scripts/check-obligations.py` → `M 类占比: 56/121 = 0.4628`（= 基线，OK）。
- `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**（仅 432 个冻结历史文件 WARNING，非本次改动文件）。
- 回归：`test_protocol_dedup_audit / test_agate_render_dispatch_prompt / test_tag0050_obligation_behavior / test_tag0050_fitness / test_doc_sweep / test_docs_assertions / ...` → 159 + 110 passed。
- `python3 agate/scripts/check-gate.py`… 未跑（非本批 gate；P4 gate 由主 Agent 跑）。

## 说明 / 判断点（供主 Agent / 评审）
- [PROD_NOT_TOUCHED]：本次为文档/协议文本改动，未触发任何写操作。
- 越界防护：未改 `agate/rules/**`、`agate/scripts/**`、`.github/**`、`agate/tests/**`、`docs/**`、`agate/UPGRADING.md`；未新增文件。
- 小幅超出 M15 明确落点：`dispatch-protocol.md:504`（P8 重跑点）的 `bump-version 后` → `交付收尾后`——为与 canonical 一致；无禁字面/测试影响。
- `AGENTS.md` 5a 补救行：原说「release workflow 没有 `workflow_dispatch`」，Impl-A 已在 `.github/workflows/release.yml` 落 `workflow_dispatch` ⇒ 同步更正为「已支持、可人工重跑」，避免与新 workflow 自相矛盾。
- `AGENTS.md` 3a（公告约束）**原文未动**——遵守「不得预告未排期能力的实施版本号」。
- 未把「发布」写成 agent 自动动作：AGENTS.md / state-machine.md 均显式「不可逆外部动作须用户授权、由人工触发」。
