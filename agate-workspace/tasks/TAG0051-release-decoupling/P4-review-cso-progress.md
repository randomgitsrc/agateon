# P4-review-cso-progress — TAG0051（CSO 安全评审）

- [x] 读角色文件 `/home/kity/.agate/v0.81.0/agate/assets/review-roles/cso.md`
- [x] 读强制输入 `P4-dispatch-context-cso.md`（STRIDE 6 项重点 + 只读纪律）
- [x] `git status` 确认改动**全部未提交**（20 M + 新增文件），分支 `task/TAG0051-release-decoupling`
- [x] 读核心落点：`agate-release.py` diff（新增 `gate` 子命令）、`.github/workflows/release.yml` diff（`workflow_dispatch` + backstop）、`r6-differential-prepare.sh`
- [x] 读 `P2-design.md` 决策 1-3/8 + §7 env_constraints + §8 minimal_validation；`P1` BDD-8/9/10/11/12/13/23
- [x] 读 `check-gate.py` / `LEVELS.yaml` / `level-2.yaml` / obligations / phases 增量
- [x] 定标：按**信任边界**审（新流程 vs 旧流程授权面/校验面），非「有无新代码」
- [x] 核 GitHub 权限模型（官方文档）：`workflow_dispatch` 需 **write access**（与 tag push 同类）
- [x] 实测（`/tmp/opencode/cso-exp` 一次性副本）：
  - A：required 空 + 零 check-runs ⇒ 门 rc=0（SEC-01 fail-open 复现）
  - B：注入 failure 结论 ⇒ 门 rc=1（fail-closed 正向确认）
  - C：`--sha ""` 静默回退 HEAD（SEC-09）
  - D：`r6-differential-prepare.sh` 校验桩化 —— 任意绝对 `--dst` 放行、软链绕过「在 src 内」（SEC-04）
- [x] 只读纪律核验：真实仓库 `git status --porcelain` 跑前/跑后一致（恒 39 项）
- [x] 产出 `P4-review-cso.md`（STRIDE 矩阵 + 严重性分级），Header `status: approved`

## 结论速览
- 0 CRITICAL / 0 BLOCKER；MEDIUM×4（SEC-01..04）、LOW/INFO×5（SEC-05..09），均非阻塞
- 信任边界：授权面等价旧流程、校验面更强 ⇒ 无回归
- status = `approved`

---

## retry 1（增量复审，2026-10-11）

- [x] 读 `P4-dispatch-context-cso-retry1.md`（逐条复核闭合 + 查新破坏 + 更新分级）
- [x] **自复跑关键负例**（`/tmp/opencode/cso-exp2` 一次性副本、桩化破坏性命令、真仓库零写入）
  - **SEC-01 闭合**：required 空 + 零 check-run ⇒ rc=1；control（1 success）⇒ rc=0
  - **SEC-09 闭合**：`--sha ""` ⇒ rc=1（显式拒绝，不回退 HEAD）
  - **SEC-02 闭合**（mocked `gh`）：evil-app 冒名 success 被滤除并合成 missing ⇒ rc=1；github-actions ⇒ rc=0
  - **SEC-04 闭合**：11 负例全部 rc=2 且 rm 调用数=0；软链绕过经物理归一化被拒；正例无过度拒绝
- [x] 新破坏排查：`workflow_dispatch` 输入的 `${{ }}` 仅在 env（非 run 插值）；dispatch 路径 `GITHUB_SHA`
  语义由 `build --expect-sha` 收口 ⇒ 无新绕过窗口；`checks: read` 为最小必要新增、无权限扩散
- [x] 新发现：**SEC-10**（本轮安全修复缺自动回归锁，LOW）、**SEC-11**（`R6_PREPARE_ALLOW_PREFIX` 可放宽为 `/`，LOW）
- [x] 安全相关测试 `test_release_gate.py` + `test_release_workflow.py` + `test_tag0051_r6_harness.py` ⇒ 33 passed（无缓存写入）
- [x] 只读纪律核验：真实仓库 `git status --porcelain` 跑前/跑后逐行一致（67 行 diff 为空）
- [x] **覆盖更新** `P4-review-cso.md`，Header `status: approved`

### retry 1 结论速览
- 0 CRITICAL / 0 BLOCKER；**SEC-01/02/04/09 已闭合**；SEC-03 为有据接受残余（MEDIUM）
- 残余 LOW：SEC-05（部分收敛）、SEC-06、SEC-10（新）、SEC-11（新）
- 信任边界无回归、无新绕过窗口 ⇒ status = `approved`（不阻塞发布）

---

## retry 2（最终增量复审，2026-10-11，**仅复核 wrapper 面**）

- [x] 读 `P4-dispatch-context-cso-retry2.md`；确认范围 = **只**复核 `r6-differential-prepare.sh` 的 SEC-04（`--dst` 删除前防护）面（R-F 把建 corpus 由 `cp -a` 换成 `git clone --local --no-hardlinks`）
- [x] 变更隔离核验：未跟踪新文件、无 git 基线；**逐行读全文**确认 `--dst` 校验块与 retry 1 逐字一致、`rm -rf` 仍在全部校验之后；变更仅在建 corpus 段
- [x] **SEC-04 自复跑**（`/tmp/opencode/cso-r2|r3|r5` 一次性副本；wrapper+差分脚本桩化；`rm` shim 计数；哨兵文件）
  - **10 负例全部 rc=2 且 rm_calls=0**：空 / 相对 / src 内 / ==src / **src 祖先** / **前缀外** / 根 / **前缀根** / 已存在软链 / **软链绕过**——哨兵与源完好 ⇒ **未放松任何校验**
  - 正例 rc=0（rm 目标 = 归一化绝对路径）；相对 `R6_PREPARE_ALLOW_PREFIX` rc=2；`--src .` rc=0
- [x] **git clone 新边界实测**：src 非 git ⇒ rc=128（dst 先生后败，src 完好）；src=worktree ⇒ rc=0；src 含未提交改动 ⇒ corpus 为 HEAD 干净树；`--no-hardlinks` **无 inode 共享**；源自定义 hooks **未复制**（较 cp -a 收窄）；`uploadpack.packObjectsHook` 在 git 2.43 未触发；src `.git` 签名跑前后一致（只读）
- [x] 新发现：**SEC-12**（src 无效 ⇒ dst 先生后败，INFO/robustness）、**SEC-13**（头部注释仍称「⑤ clean -fdx」，机制已移除，INFO）
- [x] 只读纪律核验：真实仓库 `git status --porcelain` 跑前/跑后 sha256 一致（`1366a50b…`，79 行；HEAD `d4e32f4f`）＝零写入；未执行任何真实外部动作
- [x] **覆盖更新** `P4-review-cso.md`，Header `status: approved`

### retry 2 结论速览
- 0 CRITICAL/HIGH/BLOCKER；**SEC-04 closed 维持**（换实现未放松校验、最危险三类仍拒）
- `git clone --local --no-hardlinks` 未引入新的可删除/可写路径，较 `cp -a` 收窄信任面 ⇒ 无安全回归
- 残余：MEDIUM×1（SEC-03，沿用）；LOW/INFO 沿用 SEC-05/06/10/11 + 新增 INFO SEC-12/13
- status = `approved`（其余沿用 retry 1 结论）
