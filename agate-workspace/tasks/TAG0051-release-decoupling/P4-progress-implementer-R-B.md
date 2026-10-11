# P4 修复轮 retry 1 — implementer R-B progress

- [start] 已读 role(implementer.md) + dispatch-context(R-B) + SELF-GATE 报告。
- [scope] 仅改 5 文件：state-machine.md / WORKFLOW.md / rules/phases.yaml / UPGRADING.md / adr.md。
- [取证] S-3b 复现：`env AGATE_ROOT=<repo>/agate python3 agate/scripts/check-structure-consistency.py`
  → `S3-cards: ERROR ... ['check-changelog.py','check-protocol-consistency.py'] 未在 phases.yaml P8 gates[].check 声明`，rc=1。
  ⚠️ 注意：**不带 AGATE_ROOT** 时脚本解析到稳定版 `~/.agate/v0.81.0/agate`（本仓无 .agate-version）→ 假 OK。
  必须用 `AGATE_ROOT=<repo>/agate` 指向本 checkout 才是有效自检。
- [MISALIGNED-3 判定依据失效] P2 当初把 WORKFLOW.md 列入 Not-Modify 依据是 `grep "git tag"` 零命中，
  但 WORKFLOW.md:327 用的是 `git log v{prev_version}` / `version 文件` / `双路径` ⇒ 模式选得过窄导致漏检。

## 改动完成（5 文件）
- state-machine.md：P8 与 READY 说明（:323）、概念表（:327/:328）、多包交付（:330）、手工 gate P8 判定规格（:403-406）全部改为 canonical 口径（bump_type 意图 / CHANGELOG [Unreleased] 含 task_id（载体 check-changelog.py）/ roadmap RM 反查 / **不含 version bump / tag**）。
- WORKFLOW.md:327：P8 门槛单元格删除全部被删块（bump 后重跑 / git log v{prev_version} / version 文件路径 / version 双路径 / CHANGELOG 双路径），改为新语义。
- rules/phases.yaml：P8 gates[].check 删旧 `version/CHANGELOG/tag` + 旧 DEBT0013 行；**增补** `check-changelog.py <task_id>` 与 `check-protocol-consistency.py` 两条声明 → 闭 S-3b。未动结构键。
- UPGRADING.md：TAG0051 节标题由「无破坏性变更」改为「面向新任务的准入行为变化」，新增破坏半径段（current_level 1→2 ⇒ 所有非 legacy 新任务须等级 2；既有/存量不受影响）。
- adr.md：新增 ADR-016（发布与任务解耦），按既有条目格式（状态/语境/决策/理由/后果 + 关联）。文末无索引表，无需同步。

## 自检实测（本 checkout = AGATE_ROOT=<repo>/agate）
① `env AGATE_ROOT=<repo>/agate python3 agate/scripts/check-structure-consistency.py`
   → 修复前：`S3-cards: ERROR ... ['check-changelog.py','check-protocol-consistency.py'] ...`，rc=1
   → 修复后：S1..S6 全 OK，rc=0（**S-3b 闭合**）
   ⚠️ 不带 AGATE_ROOT 时脚本解析到稳定版 v0.81.0 → 假 OK；必须以 AGATE_ROOT 指向本 checkout 为有效自检。
② `env AGATE_ROOT=<repo>/agate python3 agate/scripts/check-protocol-consistency.py`
   → `仅有 432 个 WARNING，无 ERROR`，rc=0（W 数按实测，非派发指引的 433）。
③ 残留 grep 清单（state-machine.md / WORKFLOW.md），逐条判定：
   - state-machine.md:165/167/168/169 → **canonical 本体**（READY 前置 + 发布独立），保留。
   - state-machine.md:323/327/328/330 → 本次改写后的新语义，保留。
   - state-machine.md:404/406 → 本次改写的 P8 判定规格（bump_type 意图 / 不含 version bump / tag），保留。
   - state-machine.md:284 `[{task_id}] READY — {task_name} {version}` 与 :288 `下一步：make publish（人工触发）`
     → **交付小结模板**，权威源在 `dispatch-protocol.md`「任务完成小结」（同文本，本次未改，不在 MISALIGNED 清单）；
       保留以维持两处逐字一致，避免制造新漂移。
   - WORKFLOW.md:10 `当前版本见 git describe --tags 或 README.md badge` → 通用版本指引，与 P8 无关，保留。
   - （`stage` 等含子串 `tag` 的误命中已排除。）
④ check-frontmatter.py：本次 5 文件**均无 YAML frontmatter**（首行分别为 `# ...`），不适用。

## 自查（非 gate）
- `pytest test_check_structure_consistency.py::test_bdd_26...` → 1 passed（真实树副本跑全量 S-1~S-6 exit 0）。
- `pytest agate/tests/unit/test_check_structure_consistency.py agate/tests/unit/test_tag0051_p8_gate.py -q` → 25 passed。
- `pytest agate/tests/integration/test_dispatch_context_card.py -q` → 8 passed（dc_2..dc_7 因 S-3b 阻断恢复而转绿）。
  （全量 pytest / 其余转红用例归属 R-C 测试面，未在本轮处理。）
- 未改脚本/CI/测试/卡片/AGENTS.md；未执行 git add/commit；未做不可逆外部动作。
[PROD_NOT_TOUCHED]
