---
phase: P4
task_id: TAG0035
parent: P2-design.md
trace_id: TAG0035-P4-D-20260916
agent: implementer
type: implementation
created: 2026-09-16
status: draft
implementation_dir: agate/scripts
---

# P4-implementation-D — TAG0035 子批 D（judge 信息隔离黑/白名单假阳性修复）

## 改动清单

### 代码：`agate/scripts/check-judge-verdict.py`

1. 新增常量 `_PROTOCOL_SPEC_DIR_RE = re.compile(r"(?:^|/)phase-cards/")`（紧邻 `_BLACKLIST_DC_RE`）。
2. `_check_blacklist(section_lines)` 改造：由"basename 整段子串包含"改为"正则捕获紧邻 basename 之前的最长路径 token，token 含 `phase-cards/` 路径段则豁免（`continue`），否则计入 `hits` 并 `break`（同一 `exact` 一次真实命中即够）"。`_BLACKLIST_DC_RE`/`_BLACKLIST_DIR_RE` 两处不变。
3. 新增常量 `_ROLE_DIR_RE = re.compile(r"(?:^|/)(?:execution-roles|review-roles)/")`。
4. 新增函数 `_p6_evidence_basenames(task_dir)`（放在 `_is_whitelisted` 之前）：读取 `task_dir/P6-evidence/` 目录下真实存在的文件 basename 小写集合，目录不存在或 `OSError` 均返回空集。
5. `_is_whitelisted(tok, evidence_basenames=frozenset())` 改造：新增签名参数；新增 `_ROLE_DIR_RE.search(tok)` 豁免分支；basename 判定改为 `base in _WHITELIST_MD or base in evidence_basenames`。
6. `_check_whitelist_outside(section_lines, evidence_basenames=frozenset())` 改造：签名加 `evidence_basenames` 形参，透传给 `_is_whitelisted`。
7. `main()` 调用点（原第 501 行）改为 `_check_whitelist_outside(section_lines, _p6_evidence_basenames(task_dir))`（复用第 486 行已有的 `task_dir` 变量）。

### 文档同步（BDD-12）

- `agate/dispatch-protocol.md`「Judge 信息隔离」节「白名单输入」段：补一句"角色定义文件路径（`execution-roles/`、`review-roles/` 目录前缀）不受此白名单限制，任意角色文件路径均视为合法引用"。
- `agate/phase-cards/P6-acceptance.md`（P6.5 流程条目，第 24 行）：在既有"见 dispatch-protocol.md「Judge 信息隔离」节"指针式写法上补"含角色定义文件路径豁免"六字提示，不重复枚举细节（沿用该卡片已有指针式写法，避免双源漂移）。

## 关联 BDD

- **BDD-11**（黑名单豁免 `phase-cards/` 路径引用）：`_check_blacklist` 改造直接对应，2 个参数化实例（p6-acceptance.md / p4-implementation.md）均验证 `hits` 不含对应 basename。
- **BDD-12**（白名单补齐角色定义文件路径）：`_is_whitelisted` 新增 `_ROLE_DIR_RE` 分支 + 2 处文档同步，2 个参数化实例（execution-roles/ / review-roles/）均验证全流程 CLI exit 0。
- **BDD-13**（`P6-evidence/` 裸文件名识别）：新增 `_p6_evidence_basenames` + `_is_whitelisted`/`_check_whitelist_outside` 透传，验证裸文件名（`extra-notes.md`，无 `P6-evidence/` 前缀）在该文件真实存在于 `P6-evidence/` 目录时全流程 CLI exit 0。
- **BDD-14**（红灯边界防御性回归）：裸引用任务自己的 `P6-acceptance.md`（无路径前缀，混入合规角色路径引用）仍判黑名单命中，exit 1——确认未被约束1的改动误伤。

## 自测结果

- `timeout 60 python3 -m pytest agate/tests/unit/test_check_judge_verdict.py -q`：**38 passed**（含 `tag0035_bdd_11/12/13/14` 全部参数化实例 + 既有 TAG0020 `test_bdd_1..9` 系列，无回归）。
- `timeout 90 python3 -m pytest agate/tests/unit/ -q -n auto --tb=short`：1506 passed, 2 skipped, **1 failed**——`test_env_adapt_docs.py::test_bdd_34_shellcheck_three_hook_shells_and_ruff`，失败原因是 `agate/scripts/check-gate.py:225`（ruff PLW2901，`for` 循环变量 `commit_hash` 被同名赋值覆盖）。该文件属**子批 C**改动范围（`_gate_p4_has_prior_code_commit`），非本批（子批 D）触碰的文件，`check-judge-verdict.py` 单独跑 `ruff check` 结果为 `All checks passed!`，与本批改动无关，如实上报供主 Agent 汇总处理。
- `timeout 90 python3 -m pytest agate/tests/regression/ -q -n auto --tb=short`：30 passed, **1 failed**——`test_tag0034_zero_change.py::test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change`（`agate/scripts/check-gate.py` 字节面基线校验），同样是子批 A/B/C 对 `check-gate.py` 的改动导致该零字节基线过期，非子批 D 引入，本批未改动 `check-gate.py` 任何字节。
- `timeout 90 python3 -m pytest agate/tests/integration/ -q -n auto --tb=short`：**96 passed**，无失败。
- `timeout 60 python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`：exit 0，**0 ERROR**（仅 365 个既有 WARNING，与本批改动无关）。
- `git diff --stat` 确认改动范围：`agate/scripts/check-judge-verdict.py`（+43/-10）、`agate/dispatch-protocol.md`（+1/-1）、`agate/phase-cards/P6-acceptance.md`（+1/-1），与前三批文件（`check-gate.py`/`check-state-transition.py`/`pre-commit-gate.py`）完全不重叠。

## 可选加固决定：不采纳

P3-test-cases.md §4.1 登记说明提到"可选加固——在 `_is_whitelisted` 一并加 `_PROTOCOL_SPEC_DIR_RE` 豁免，供 `phase-cards/` 路径在 `_check_whitelist_outside` 检查点也被豁免，避免真实 `P6.5-dispatch-context-judge.md` 场景整体判定仍为 exit 1"。本批**未采纳**，理由：

1. **P2-design.md §3.4② `_is_whitelisted` 的完整代码明确只给出 `p6-evidence/` + 角色目录两处豁免**，未包含 `_PROTOCOL_SPEC_DIR_RE`；按最小实现原则（implementer.md「只实现 P2 方案里的东西，不擅自扩大范围」），不应在派发指引未明确要求时额外添加。
2. **BDD-11 的测试设计（P3-test-cases.md §4.1 本身已论证）明确白盒直连 `_check_blacklist`，不断言整体 exit code**——P3-test-cases.md 原文已指出"若断言整体 exit==0 会把两个独立检查点的行为混在一起，既不符合 BDD-11 原文精确措辞，也会让测试在 P4 implementer 严格按 P2-design 实现后仍然是假红"。这说明 P1/P2/P3 三阶段的既有设计已经共识：BDD-11 的验收范围不包含"整体 exit 0"，只包含"`_check_blacklist` 本身不再误判"。
3. **该项被 P3-test-cases.md 原文明确标注为"可选"且"若不做需说明理由，供 P5/P6 核实"**，本决定即满足该要求：真实 `P6.5-dispatch-context-judge.md` 在其"上游关联"节引用 `agate/phase-cards/*.md` 路径时，`_check_whitelist_outside` 仍会将其判为"白名单外任务路径引用"（因为该检查点判定 basename 是否在 `_WHITELIST_MD`/`evidence_basenames`/角色目录前缀内，`phase-cards/` 前缀不在此列），整体 exit 仍为 1——**这是已知的残留行为，非本批引入的新回归**（修复前该场景本就 exit 1，修复后仍 exit 1，只是拦截点从"黑名单误判"变为"白名单外误判"，行为对最终用户可观察结果不变）。建议 P5/P6 阶段实测确认：若真实场景中 `P6.5-dispatch-context-judge.md` 的"上游关联"节确实需要引用 `phase-cards/` 路径且应被放行，需在后续任务（或本任务追加 SCOPE+）中把 `_PROTOCOL_SPEC_DIR_RE` 同步接入 `_is_whitelisted`；当前 P1 BDD 硬性范围（14 条 BDD 逐条验证命令）不要求这一点，故本批不做。

## 已知无关失败（供主 Agent 汇总，非本批范围）

- `test_bdd_34_shellcheck_three_hook_shells_and_ruff`（ruff PLW2901，`check-gate.py:225` `commit_hash` 变量覆盖）——子批 C 代码，需子批 C 或主 Agent 汇总时处理。
- `test_bdd_39_gate_state_machine_phases_yaml_zero_byte_change`（`check-gate.py` 字节面基线过期）——子批 A/B/C 对 `check-gate.py` 的合法改动导致基线需要更新，需主 Agent 在全部 4 批完成后统一处理（更新基线 sha256 或该测试本身的适用范围）。

## DESIGN_GAP / SCOPE+ / CLARIFY

无。本批严格按 P2-design.md §3.4 给出的完整代码实现，无自主决策偏离。
