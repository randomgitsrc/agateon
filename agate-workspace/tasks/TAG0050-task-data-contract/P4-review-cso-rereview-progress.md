# P4-review-cso-rereview-progress — TAG0050 批 A1 C8 安全面复评留痕

- 角色：cso（安全官）
- 阶段：P4；任务：TAG0050；批：A1-cso-rereview
- 环境隔离：[PROD_NOT_TOUCHED]（全部验证在 `/tmp/opencode/cso-rereview/` 仓外可丢弃副本上进行；真实仓库只读）

## 步骤
1. 读角色定义 `agate/assets/review-roles/cso.md` + 复评 dispatch-context + 原 `P4-review-cso.md` + 整改指引 `P4-dispatch-context-implementer-A1-cso-fix.md`。
2. 读未提交 diff：`agate/scripts/pre-commit-gate.py`（规则 4 处理 R、`_is_task_dir_rename`/`_dir_moved_away`、F-3 跳过条件收紧）、`test_tag0050_a0_a1_ledger.py`（BDD-23..26）、`docs/design-notes/{design,r6-allowlist,r6-differential}`、`P4-implementation.md` §10。
3. 建仓外副本：`cp -a agate docs agate-workspace /tmp/opencode/cso-rereview/`；另用 `git archive HEAD` 取 pre-fix 协议树 `agate-head/`。
4. 独立复现（不依赖被测用例）：
   - F-1a 同目录 `.bak` 改名 → rc=1；F-1b 移入别任务目录 → rc=1；F-1c 整目录改名 → rc=0；F-1d 改名到同任务子目录 → rc=1；F-1e 改名+改内容（D+A）→ rc=1。
   - F-3 `git rm .state.yaml` + 目录内 `[PROD_TOUCHED]` → rc=1；对照（正常暂存 .state.yaml + marker）→ rc=1。
   - 回归：正常提交（暂存 .state.yaml、无 marker）→ rc=0。
5. 跑被测新增用例：BDD-23/24/25/26 = **4 passed**（副本内）。
6. 残留探针：源任务目录索引被清空（`git rm --cached .state.yaml`）+ 账本移入既有别任务目录 → **rc=0**；提交后 `task_level` 1→None。用 pre-fix 协议树对照：同样 rc=0 ⇒ 非本次整改新引入，属旧洞残留。
7. 确认 G2/G3/F-4/F-5/F-6 声明与登记：设计 §8 第 12 项归属段 + `r6-allowlist.yaml` 可达性声明 + `P4-implementation.md` §10 均到位且口径一致。
8. 真实仓库 `git status --porcelain` 复评前后逐行一致（48 行）；未编辑任何被评审文件、未写仓。

## 结论
F-1（指定两形态）已闭合、F-3 已闭合、G2 声明到位；发现一处**非阻塞**残留（F-1R，豁免判据过宽），已给可复现证据与加固建议。
