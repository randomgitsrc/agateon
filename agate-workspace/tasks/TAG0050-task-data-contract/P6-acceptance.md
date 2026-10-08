---
phase: P6
task_id: TAG0050
type: acceptance
parent: P5-verification.md
trace_id: TAG0050-P6-20261009
status: draft
created: 2026-10-09
agent: verifier
# ── v2.0 机器汇总 ──
pass: 77
fail: 0
ui_affected: false
p5_evidence_reuse: false
---

# TAG0050 P6 验收报告 — 任务数据契约：结构化判定、可信写入与任务版本

> **验收对象**：HEAD `a87f2bd5`（P4 全部批次 + P5 已完成提交），协议 v0.79.0。
> **验收方式**：verifier subagent 逐条实跑 `P1-requirements.md` §4 的 BDD-01..77，结果只允许 PASS/FAIL，
> 每条 PASS 引用 `P6-evidence/` 下的实际输出（各批验收测试实跑日志 / 脚本实跑输出 / R6 差分 / 负向对照）。
> 只读验收：未修改任何被验收文件，未 `git add/commit`；有写副作用的 R6 差分与「改坏即红」对照均在
> `/tmp/opencode` 的**仓外副本**上跑。
> **环境隔离**：`[PROD_NOT_TOUCHED]` 本阶段仅在 agateon 本 checkout 与 `/tmp/opencode` 只读副本上运行，未接触生产环境。
> **本任务非 UI**（`ui_affected: false`）：无截图/vision 证据要求。
>
> **口径说明**：TAG0050 自身账本首行不是 `task_created`（该任务早于 A1 机制创建）⇒ 按 **legacy 任务**走既有
> P6 口径（正文逐条 PASS 行 + frontmatter `pass`/`fail` 汇总；provenance 审计 1/3/5/6 生效）。本任务引入的
> **非 legacy 结构化判据面 D1–D10** 由 BDD-56 用例在 `conftest.init_task()` 构造的非 legacy 任务上单独验证
> （见 `P6-evidence/batch-tests/test_tag0050_evidence.log`）。
>
> **post-test 环境残留检查（强制）**：验收测试全部在 pytest `tmp_path`/`git_repo` fixture 内创建临时资源
> （git 仓库、任务目录、账本、证据文件），随 fixture 自动清理；脚本类证据在 `mktemp -d` 副本内运行
> （`r6-differential.sh` 自带运行前+运行后 `git status --porcelain` 自核验）。跑完后真实仓库
> `git status --porcelain` 仅剩本 P6 自身产出（`.state.yaml` M + `P6-dispatch-context-verifier.md` +
> `P6-evidence/`），**无测试/脚本残留**（见 `P6-evidence/post-test-residue.log`）。R6 两个 corpus 副本
> （agateon / peekview）跑后 `git status --porcelain` 为空。

## 批次 A0 — hotfix（F8；check-gate 不存在目录 rc=1）

- PASS BDD-01: PAUSED 下写入 `[PROD_TOUCHED]` 时账本真实追加 `prod_touched_in_paused` 事件（可 grep 到），非静默丢弃（修复 F8）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-02: `check-gate.py <phase> <不存在的目录>` 退出码为 1（P7/P5/P0 三例参数化，不再返回 0 假 PASS）(batch-tests/test_tag0050_a0_a1_ledger.log)

## 批次 A1 — 契约等级与账本完整性

- PASS BDD-03: 含 `task_created`（等级 1）的账本追加降级事件判 ERROR (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-04: 第 2 条 `task_created` 判 ERROR (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-05: `task_created` 不在第 1 行判 ERROR (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-06: `contract_level` 不在 `LEVELS.yaml` 登记集合内判 ERROR (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-07: 手写低于当前等级的 `contract_level` 新任务本地提交判 ERROR (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-08: 回填或删除 P1 `created` 后 judge 强制仍生效（修复 F3a）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-09: P6 改 `judge.enabled:false` 后 P6.5 仍阻断（判定读契约 `requires`，修复 F3b）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-10: 回填 `created` 不改变 evidence_ref 强制级别（仍 rc=1，修复 F3c）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-11: 新增无创建事件目录判 ERROR，`agate-task-init.py --existing` 补写后转绿 (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-12: `git mv` legacy 目录后仍为 legacy 且不报错 (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-13: 改写/删除已有创建事件的账本判 ERROR（含同目录改名与移入别目录两个负向锚）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-14: legacy 任务从 DONE 回到 P1 判 ERROR（提示 `--adopt` 或新建）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-15: 修改已发布快照判 consistency CHECK 16 ERROR（sha256 不一致），未登记新快照同样拦截；改坏即红对照 (batch-tests/test_tag0050_fitness.log, consistency.log, consistency-tamper.log)
- PASS BDD-16: 每个已登记等级含 pass/fail 黄金 fixture 且非空，CI 对全部等级回归 (batch-tests/test_tag0050_fitness.log, contract-artifacts.txt)
- PASS BDD-17: 任务等级高于运行中协议最大等级时 fail-closed 并提示升级 (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-18: legacy 任务只暂存产出未改 phase 时也做 PROD_TOUCHED 扫描 (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-19: 非 legacy 任务按被暂存产出所属阶段重跑 gate（含 HEAD=READY）(batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-20: P7 迁入任务的 P4 散文缺口仍由旧读取器计数，未覆盖判 ERROR (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-21: 连续两次升级时各阶段取各自 `level(Pk)` (batch-tests/test_tag0050_a0_a1_ledger.log)
- PASS BDD-22: R6 双向差分交付物（`r6-differential.sh`+`r6-allowlist.yaml`）；agateon 与 agateon+peekview 两轮差分均 0 差异 0 未匹配、跑后 corpus 干净；删必需规则负向变红 (batch-tests/test_tag0050_a0_a1_ledger.log, r6-differential-agateon.log, r6-differential-both.log, r6-negative-control.log)

## 批次 A2 — CI 回放（可信锚点，修复 F15）

- PASS BDD-23: PR 口径逐提交回放 TAG0042 的 16 个非合并提交全部 PASS（协议取 merge-base）(batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-24: push 口径回放同样全部 PASS（`rev-list --no-merges`，合并提交跳过）(batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-25: `--no-verify` 违规提交判 FAIL 并指出提交，push 口径同样 FAIL (batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-26: READY 之后只改产出的 `[PROD_TOUCHED]` 提交判 FAIL（安全门覆盖不改 phase 的提交）(batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-27: 缺 self-gate trailer 的协议本体提交判 FAIL（含 commit-msg 回放）(batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-28: 删除已有创建事件账本判 FAIL；legacy 目录改名判 PASS (batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-29: 手写低等级 `task_created` 并 `--no-verify` 提交判 FAIL (batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-30: 在途分支跨协议升级不误报（merge-base 等级检查）(batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-31: 使用者项目未写 `.agate-version` 判 FAIL 并给提示 (batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-32: PR 降级 `.agate-version` 判 FAIL（单调不降被违反）(batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-33: PR 中途正常升级 `.agate-version` 不误报 (batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-34: 未改动任务目录的 PR 输出 SKIP 并附原因；squash 仓库 push 只做账本前缀与事件规则检查 (batch-tests/test_tag0050_ci_replay.log)
- PASS BDD-35: 回放接口记录被回放提交数与耗时（E4）(batch-tests/test_tag0050_ci_replay.log)

## 批次 A3 — state-set 与状态事实

- PASS BDD-36: `agate-state-set.py phase` 以 HEAD 为基准拒绝非法转换；提交时判定与工具当时一致 (batch-tests/test_tag0050_state_set.log)
- PASS BDD-37: 回退时同时写入 `retries[...]`，满足转移规则 (batch-tests/test_tag0050_state_set.log)
- PASS BDD-38: 进入 READY/PAUSED 写 `state_transition`（随本次提交入库）；`agate-next` 通过时只打印建议不再追加事件 (batch-tests/test_tag0050_state_set.log)
- PASS BDD-39: 非 legacy 任务写 `status` 判 ERROR；读取方 status 由 phase/cancelled 现算 (batch-tests/test_tag0050_state_set.log)

## 批次 A4 — 义务执行方式机械核验（修复 F13）

- PASS BDD-40: `check-obligations.py` 对 F13 的 4 条不在必经路径的 M 报 ERROR；60 条 M 义务的 `enforced_at` 机械落点核验全过 (batch-tests/test_tag0050_obligations.log, batch-tests/test_tag0050_obligations_enforcement.log, check-obligations.log)
- PASS BDD-41: M 项缺 `test` 字段或其 pytest 节点不存在判 ERROR (batch-tests/test_tag0050_obligations.log)
- PASS BDD-42: 负向控制——mutation 删掉判据分支使 `test` 转红 (batch-tests/test_tag0050_obligations.log, batch-tests/test_tag0050_obligation_behavior.log)
- PASS BDD-43: 缺 `review_output` 的 R 判 ERROR；找不到合格评审产出的 R 改标为 C (batch-tests/test_tag0050_obligations.log, check-obligations.log)
- PASS BDD-44: 改标并 `baseline.reset` 后转绿；之后 M 占比下降仍 FAIL（只增不减）(batch-tests/test_tag0050_obligations.log, check-obligations.log)

## 批次 B — 写入工具与契约单源

- PASS BDD-45: `agate-md-field-set.py` 7 操作（set/append/upsert/remove/--list/explain/render）与 `agate-config.py` set/unset/explain 往返用例全部通过 (batch-tests/test_tag0050_write_tools.log)
- PASS BDD-46: `writer: system` 字段拒写并说明来源；md-field-get 返回按 `derive` 现算值 (batch-tests/test_tag0050_write_tools.log)
- PASS BDD-47: 非 legacy 任务声明文件缺 frontmatter 判 ERROR（不回退正文正则，修复 F10）(batch-tests/test_tag0050_write_tools.log)
- PASS BDD-48: `<!-- AGATE:RENDER ... -->` 渲染块被手改判 ERROR 并给修复命令；CRLF 规范化为 LF 后逐字节比较一致 (batch-tests/test_tag0050_write_tools.log)
- PASS BDD-49: 报错附带的修复命令照抄执行后重新校验转绿 (batch-tests/test_tag0050_write_tools.log)
- PASS BDD-50: 只剩 1 个递归 schema 校验实现（三处统一调用 `agate_schema.py`，降级副本门控在单源不可用时）(batch-tests/test_tag0050_write_tools.log)
- PASS BDD-51: T1 绊线 E3 误报为 0 或已落实 P7/P8 评审稿降 WARNING 的降级方案 (batch-tests/test_tag0050_write_tools.log)

## 批次 C — 生产接触

- PASS BDD-52: 主产出 frontmatter 缺 `prod_touched` 判 ERROR 并附修复命令 (batch-tests/test_tag0050_prod_touched.log)
- PASS BDD-53: `prod_touched: true` 且不在 PAUSED 时中止提交 (batch-tests/test_tag0050_prod_touched.log)
- PASS BDD-54: 正文粗体 `**[PROD_TOUCHED]**` 而字段 `prod_touched: false` 仍中止（T4 优先于字段；含非声明文件面）(batch-tests/test_tag0050_prod_touched.log)
- PASS BDD-55: 否定写法 `- [PROD_TOUCHED]: 无` 仍中止并给专门指引（修复 F4，fail-safe）(batch-tests/test_tag0050_prod_touched.log)

## 批次 D — 验收结论与证据绑定

- PASS BDD-56: F1 的 A/B/C 三种篡改全部转红（D1/D2 结构化判据在非 legacy 任务上生效）(batch-tests/test_tag0050_evidence.log)
- PASS BDD-57: 证据引用指向被 `.gitignore` 忽略的文件判 ERROR（pre-commit 中还要求已跟踪或已暂存，修复 F9）(batch-tests/test_tag0050_evidence.log)
- PASS BDD-58: PASS 条目引用的日志带 `EXIT_CODE` 尾行且值非 0 判 ERROR (batch-tests/test_tag0050_evidence.log)
- PASS BDD-59: `run:<k>` 引用的日志 sha256 与 `cmd_run` 事件记录不一致判 ERROR（事件缺失亦 fail-closed）(batch-tests/test_tag0050_evidence.log)
- PASS BDD-60: `agate-extract-context.py` 计数等于按字段现算的值 (batch-tests/test_tag0050_evidence.log)

## 批次 E — 成对声明

- PASS BDD-61: F2 转红（P7 正文追加 BLOCKER 而 frontmatter 写 `blocker_count: 0`，计数为系统字段不被盖住）(batch-tests/test_tag0050_declarations.log)
- PASS BDD-62: P2-review 与 P4 分文件 frontmatter 中的声明都被跨文件聚合 (batch-tests/test_tag0050_declarations.log)
- PASS BDD-63: 多个 `P4-implementation-*.md` 并行写入不撞号（ID 格式 `<相对路径去 .md>:<前缀><n>`）(batch-tests/test_tag0050_declarations.log)
- PASS BDD-64: 集合不相等或悬空 id 判 ERROR (batch-tests/test_tag0050_declarations.log)
- PASS BDD-65: `resolved` 的 blocker/deviation_critical 缺 `resolution` 或 `evidence` 判 ERROR (batch-tests/test_tag0050_declarations.log)
- PASS BDD-66: `basis: followup:DEBT<n>` 中 DEBT 不存在或无 `source_ref` 回指判 ERROR (batch-tests/test_tag0050_declarations.log)

## 批次 F — 代理判定（RM-AG0085 / RM-AG0087 / F12）

- PASS BDD-67: P2 `ui_design.dimensions.<维度>` 标 `status: na` 但无 `reason` 判 ERROR (batch-tests/test_tag0050_proxy_judgment.log)
- PASS BDD-68: P1-review 的 `reviewed_bdds` 与 P1 的 BDD 集合不相等判 ERROR (batch-tests/test_tag0050_proxy_judgment.log)
- PASS BDD-69: 骨架判定改为标题级匹配——正文仅散文提及「## 骨架声明」不再被误判为标题已存在（RM-AG0085）(batch-tests/test_tag0050_proxy_judgment.log)
- PASS BDD-70: `set(phases) ∪ set(pruned.phase)` 不等于 `phase_universe` 或两者相交判 ERROR（RM-AG0087）(batch-tests/test_tag0050_proxy_judgment.log)
- PASS BDD-71: T2 绊线拦下 `### BDD-1:` 等非规范标题并指向 `#### BDD-N:` (batch-tests/test_tag0050_proxy_judgment.log)
- PASS BDD-72: 按 F12 方式篡改 P8 delivery（删字段、正文写「暂不声明 delivery: 方式」）转红（结构化字段取代子串判定）(batch-tests/test_tag0050_proxy_judgment.log)

## 跨批通用验收

- PASS BDD-73: 每批独立 PR/gate/评审并登记快照（`LEVELS.yaml` 登记 `level-1.yaml`，见契约交付物实测）(contract-artifacts.txt, batch-tests/test_tag0050_cross_batch.log)
- PASS BDD-74: legacy 任务的 gate 退出码与 ERROR 集合不变，差异仅限设计 §8 十二项（allowlist D01..D12）；双向 R6 差分 107 个 legacy 任务 0 差异 0 未匹配 (batch-tests/test_tag0050_cross_batch.log, contract-artifacts.txt, r6-differential-both.log)
- PASS BDD-75: 全量 pytest 2863 passed/1 failed（唯一失败为本机 opencode CLI 漂移的预存失败，与本任务无关）/2 skipped；consistency 0 ERROR；count-tests 2866 用例（下界 749 未击穿）；跑后无环境残留 (full-pytest.log, consistency.log, count-tests.log, tag0050-collect.txt, post-test-residue.log)
- PASS BDD-76: A4 义务基线一次性重设写入 CHANGELOG（`baseline.reset: {from: "60/123", to: "56/119"}`）(changelog-baseline.log, batch-tests/test_tag0050_cross_batch.log)
- PASS BDD-77: 新增 `agate-task-init.py`/`agate-state-set.py`/`agate_schema.py` 不触发既有测试转红（consistency + SG.6 + 登记面测试 36 passed）(registration-tests.log, contract-artifacts.txt, batch-tests/test_tag0050_cross_batch.log)

**Summary**: 77/77 PASS, 0 FAIL（PASS 数 = P1 BDD 数 77，无挑验、无遗漏）。

## 证据-结论对照说明

- 各批 BDD 的功能验证来自对应验收测试的**实跑输出**（`batch-tests/*.log`，均 `passed`、尾行 `EXIT_CODE: 0`）。
- 跨批/脚本类 BDD（15/16/22/40–44/73–77）另附脚本实跑输出：`consistency.log`（0 ERROR，CHECK 16 通过）、
  `consistency-tamper.log`（改快照即红）、`count-tests.log`（2866）、`check-obligations.log`（M 占比不低于基线）、
  `r6-differential-*.log`（双向差分 0 差异）、`r6-negative-control.log`（删必需规则即红）、
  `changelog-baseline.log`、`registration-tests.log`、`contract-artifacts.txt`、`tag0050-collect.txt`、`full-pytest.log`。
- 预存失败：`agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent`
  ——本机 opencode CLI 子命令漂移（`debug agent`→`debug agents`），与本任务无关（`known-failures.md` 已登记）。
