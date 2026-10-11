# P4 progress — Impl-B（批 delivery-contract + obligations-sync + p8-rules-roles 的 rules 部分）

- 范围（只改这些）：`agate/rules/task-data/level-2.yaml`(新增)、`agate/rules/task-data/LEVELS.yaml`、
  `agate/UPGRADING.md`、`agate/rules/obligations.yaml`、
  `agate/tests/unit/test_tag0050_obligations_enforcement.py`、`agate/rules/phases.yaml`、
  `agate/rules/state-transitions.md`。
- 已读输入：implementer 角色文件；P4-dispatch-context-implementer-B.md（含 P4 卡）；
  P2-design.md（§1.1/§1.1.1/§3 决策4·6/§4/§9.1）；P2-review.md（§1.1/§1.2/NB-6、§5 锁定）；
  P1-requirements.md（BDD-16/17/19/21）；level-1.yaml / LEVELS.yaml / obligations.yaml /
  test_tag0050_obligations_enforcement.py / test_tag0050_obligation_behavior.py /
  phases.yaml / state-transitions.md / agate_common.py（load_contract/task_level）/ 
  check-obligations.py（棘轮 :320）/ check-protocol-consistency.py（CHECK16 冻结）/ UPGRADING.md。
- 确认 anchor 节仍在：`P8-release.md#gate 规则`(:78) 与 `#如果是首次进入本阶段`(:7) 均存在（未被动过）。

## 落地改动（仅本支范围）

1. **`agate/rules/task-data/level-2.yaml`（新增）**：`level: 2` / `extends: 1`；
   `delivery` 节**重述完整**（`required: [method]` / `none_requires_reason: true` /
   `non_none_requires_ref: true`）+ **新增** `method_enum: [release-notes, tag-release, none]`。
   （理由：`load_contract` 顶层键整体覆盖，仅 `requires` 浅合并。）
2. **`agate/rules/task-data/LEVELS.yaml`**：登记 `{level: 2, file: level-2.yaml,
   sha256: 741afaf7ef2e33436573b67139f959e8cdf75ae5d36f1dc31c6c354f0bbb2b34}`（落盘后实测值）。
3. **`agate/UPGRADING.md`**：§3 顶部加 `### 未发布 — TAG0051 任务与发布解耦：delivery.method 收紧 + P8 去 tag/version（**无破坏性变更**）`
   （沿用 `未发布` 既有小节惯例；**未预告任何未来版本号**）。
4. **`agate/rules/obligations.yaml`**：OBL-P8-04 **就地重挂**（statement → `delivery.method 枚举校验`
   （读快照 `delivery.method_enum`，缺省 no-op）；`disposition` 保持 **M**；`enforced_at` →
   `gate_p8`；test 复用既有节点；anchor 不变）；OBL-P8-05/08/13 仅 statement 改述；其余 10 条不动。
   **未删条目、未改判、未加 `baseline.reset`**。
5. **`agate/tests/unit/test_tag0050_obligations_enforcement.py`**：`M_IDS` 保持含 `OBL-P8-04`（零改动）；
   **新增 BDD-21 两条机械断言**（`test_bdd_21_obl_p8_statements_have_no_version_tag_residue` +
   `test_bdd_21_obl_p8_04_rehomed_to_method_enum`）。为解 NB-6「黑名单可绕过」，改用**词根+词界**
   正则（`版本号` / `\bbump\b` / `\btag\b` / `双路径` / `version\s*文件`）——既拦「CHANGELOG 写入版本号」
   「打 tag 前置校验」「执行 bump」，又不误伤 `bump_type`（已全量扫十四条 + 绕过样例实测：零误伤、非真空）。
6. **`agate/rules/phases.yaml`**：P8 `gates` 删「version/CHANGELOG/tag 检查」表述与
   「先 tag 后重跑（DEBT0013）」行；改为 `bump_type / debt_check 字段 + 结构化 delivery（method 枚举校验）
   + roadmap 关联条目反查`。结构键（gate_pass_exit/retry_cap/outputs/task_fields）未动。
7. **`agate/rules/state-transitions.md`**：P8→READY 行删 tag/version 条件——改为
   「交付物齐备 + CHANGELOG `[Unreleased]` 含 task_id + bump_type 意图 + 交付收尾 + 各 package 发布检查 exit 0」
   ／「READY 收尾检查：测试环境清理 / 开发环境还原」。

## 自检实测（非 gate）

- `python3 agate/scripts/check-obligations.py` → **`M 类占比: 56/121 = 0.4628（基线 56/121 = 0.4628）`**，
  `CHECK-OBLIGATIONS: OK`，**EXIT=0**（核心凭证；M 计数未降）。
- `python3 agate/scripts/check-gate.py P2 <task>` → `EXIT=2`（P2 通过码，未因本支改动转红）。
- `python3 -m pytest agate/tests/unit/test_tag0050_obligations_enforcement.py agate/tests/unit/test_tag0050_obligation_behavior.py -q`
  → **68 passed**（原 66 + 新增 BDD-21 2 条；`test_tag0050_obligation_behavior.py` 未改）。
- `python3 agate/scripts/check-protocol-consistency.py` → **0 ERROR**（CHECK 16 任务数据契约快照冻结 **PASS**，
  证明 level-2 与 LEVELS 登记同批一致）。
- BDD-21 断言可判定性：绕过样例（`CHANGELOG 写入版本号`/`打 tag 前置校验`/`执行 bump`）均命中、
  `bump_type` 不命中 ⇒ 非真空、零误伤。
- `check-frontmatter.py`：本支改动文件**均无 frontmatter**（level-2/LEVELS/obligations/phases 为 YAML，
  state-transitions/UPGRADING 为 md 无 frontmatter，test 为 py）⇒ 不适用。

`[PROD_NOT_TOUCHED]`：本支只改上述 7 个文件，未执行任何写生产/不可逆外部动作。
