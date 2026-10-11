# 留痕（HOTFIX-DEBT0074 发布门口径修正）——原始痕迹

- [读] `/home/kity/.agate/v0.82.0/agate/assets/review-roles/protocol-alignment-review.md`（角色定义，147 行）——A1-A8 + A4b，三态结论，只读纪律 RM-AG0081。
- [读] `git status --porcelain` → 3 改动文件（release.yml / agate-release.py / test_release_gate.py），分支 `hotfix/debt0074-gate-concurrent-runs`。
- [读] `git diff` → agate-release.py 仅动 header(17-19) 与 `_non_success_names`(453-479)；未动 `_gh_check_runs`(SEC-02)、`_required_checks`、`_cmd_gate --task`(SEC-07)。
- [读] agate-release.py:400-479 → `_gh_check_runs` 过滤可信 App + 合成 missing（SEC-02）；`_non_success_names` 新逻辑按 name 归组、只看 `conclusion is not None` 的已完成结论。
- [读] agate-release.py:549-646 → `_cmd_gate`：SEC-09 空 sha、SEC-01 `if not runs: return 1`（未改）；③ CI 判定调 `_non_success_names`。
- [读] agate-release.py:626-637 → SEC-01 零 check-run 路径未改。
- [读] test_release_gate.py 全 513 行 → 新增 3 用例（214-274），`_OK_RUNS` 夹具。
- [读] .github/workflows/release.yml:85-89 → 注释已同步为新口径；`AGATE_RELEASE_REQUIRED_CHECKS` 硬编码 6 项，未传 `--task`（SEC-07 有意）。
- [读] agate/scripts/agate-release.py:1-42 header → gate 自述已同步（17-19）。
- [读] agate-workspace/debt/tech-debt.md DEBT0074（3207+）→ status: open；evidence 记 run 38141030366 假失败 / 38141340966 绕过；recommendation (a)/(b)。
- [读] CHANGELOG.md → [Unreleased] 空（11-12 行）；[0.82.0] 含 DEBT0065/0066/0067/0069/0072，无 DEBT0074。
- [读] agate/scripts/README.md:149、agate/tests/README.md:97 → gate 索引行「CI success + consistency 0 ERROR + check-gate.py P8」（粗口径，仍真）。agate/UPGRADING.md:308、agate/adr.md:692 同为粗口径「CI success / 机械发布门 fail-closed」（仍真，且属已发布历史，不应回改）。
- [探针1] 函数级对比（/tmp/opencode/debt0074probe2，同次 bash 内创建→清理）：当前实现 vs 旧实现（git show HEAD 逐条版）跑 11 个对抗输入。
  结果：仅 F(`success+in_progress`)、H(`success+queued`) 两例由「失败」变「通过」（DIFFER）；A(仅 in-flight)、B(同名 success+done failure)、C(done failure+in-flight)、D(另一 required 名 missing)、G(混入非 dict)、J(success+done cancelled)、K 均仍判非 success。E(空)→ 空（交 `not runs` 拦截）。
- [探针2] CLI 端到端（/tmp/opencode/debt0074cli，同次 bash 创建→清理）：gate --sha HEAD --repo <tmp git repo> --ci-cmd ... --consistency-cmd ok.py
  `[]` → rc=1（SEC-01）；success+inflight → rc=0；success+done failure → rc=1；仅 inflight → rc=1；全 success → rc=0。全部符合预期。
- [实跑] `python3 -m pytest agate/tests/unit/test_release_gate.py -q` → 18 passed in 2.13s。
- [读] `git show --stat cd0ffd6e`（DEBT0072 收口）→ CHANGELOG.md + tech-debt.md + 脚本 + test + 两份评审报告。⇒ 债务收口 hotfix 的既有模板含 CHANGELOG 与 debt 关单。
- [读] `grep -rn 逐条/required...` → 除本改动三处外，无其他文档描述旧「逐条 conclusion != success」口径；SEC-01 零 check-run 路径**无**单测（先存缺口，非本次回归）。
- 结论：核心语义改动窄且保守，未发现可掩盖真实失败的场景；唯一 MISALIGNED = A5（CHANGELOG [Unreleased] 与 DEBT0074 关单未随本改动落盘）。

## 增量复审（retry 1，commit 7d3cdeb7 → 已并入 main Merge 47901872）
- [读] `git show --stat 7d3cdeb7` → 7 文件：3 实现/文档 + CHANGELOG.md + tech-debt.md + 2 报告。
- [读] `git show 7d3cdeb7 -- CHANGELOG.md` → [Unreleased] 新增 `### 修复` 条目（15-23 行）。
- [读] `git show 7d3cdeb7 -- agate-workspace/debt/tech-debt.md` → DEBT0074: status closed / closed_at 2026-10-11 / task_id hotfix-debt0074-gate-concurrent-runs / 两条新 evidence / closure_note（含「真机复验延后」如实登记）。
- [读] CHANGELOG.md:11-23 → 条目逐句核：无「已线上验证」式过度声称；「并发重跑不再假失败」为机制描述。
- [实跑] `check-debt.py agate-workspace/debt/tech-debt.md` → rc=0。
- [实跑] `check-protocol-consistency.py --strict-errors-only` → rc=0（0 ERROR，CHECK 7/13 PASS）。
- [实跑] `grep -c '^## DEBT'`=74 / `grep -c '^status: open'`=1 / awk open id=DEBT0073 → 「74/open 1」属实。
- [读] `.github/workflows/protocol-tests.yml:34-37` → closure_note 所引「不改为 push 只限 main（PR #222 自引用零 run）」属实。
- [读] `agate-debt-check.py:158-173` → closed 机械准入 = task_id 非空 + evidence 序列化文本含 task_id + closed_at ⇒ 均满足。
- 裁决：关单**可接受**（机制层满足第一条实质意图 + 遗留如实登记 + 下次发版自动 fail-closed 复验）；A5 闭合；终态 approved。

## 重写（记录对齐，非新评审）
- 主 Agent 用 `git reset --hard origin/main` 把 retry 1 的 approved 更新冲掉 ⇒ 仓内该文件回退为 r0（needs-revision），与事实不符。
- 本次**仅重写**本报告为自洽终态（结论 approved，保留 r0 历史 + 完整 retry 1 节），并追加本条留痕。
- 复核实：CHANGELOG [Unreleased] 条目仍在 / DEBT0074 status=closed / check-debt rc=0 / consistency rc=0（CHECK 7/13 PASS）/ 74-open1 —— 均与 retry 1 一致。
