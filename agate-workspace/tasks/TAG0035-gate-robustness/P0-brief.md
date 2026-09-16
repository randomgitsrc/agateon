# P0-brief — TAG0035 gate 健壮性批（RM-AG0062 归并 + RM-AG0064 并入）

> 主 Agent 亲自填写（P0 产出）。RM-AG0062（`agate-workspace/roadmap/roadmap.md`，backlog→scheduled）+ **RM-AG0064 并入本条**（原条目改为 cancelled 并注明并入 RM-AG0062）。
> **归并性质**：一个 task 内分子批交付（参照 **TAG0023**「RM-AG0042-45 机制校验补强批」/ **TAG0031**「DEBT 存量修复批」先例）。**均需 SELF-GATE + 设计决策，非 chore**——同簇 gate / check-script / test-infra 健壮性。
> **来源**：TAG0030/0033/0034 复盘登记的 DEBT0037·0038·0040·0041（2026-09-10 会话逐条评估归并）+ RM-AG0064（2026-09-16 编排模型演进分析 §5.3 实测发现）。
> **设计依据**：`docs/design-notes/design-orchestration-evolution-analysis.md`（v6.2，PR #319）§5.3、附录 B 证据索引。
> **DM 前置**：无。本批全部为既有脚本改造，无外部依赖。
> **与 TAG0036 的排序关系（已裁定）**：本批**先启动**——① 文件冲突：本批改 `check-gate.py`，而 TAG0036 阶段 2（批级 gate）同样要改它，本批先做可把既有判据问题清干净 ② 依赖方向：TAG0036 阶段 2 新增 gate 分支时，若本批未修，会踩到同类 fail-open / 判据假设 ③ 确定性：本批验证为确定性（exit code + regression），TAG0036 阶段 1 为探索性（Q1/Q2/Q3）。**两批文件面不重叠**（本批改既有脚本，TAG0036 阶段 1 新建 `check-mvwu.py` + 改 frontmatter 约定），故**可并行**。

## task

"在 agate 协议层修复 gate / check-script 的**健壮性缺陷**——把会**静默通过**或**静默失效**的判据改为**响亮失败**（fail-closed），并补齐多提交 / 回退场景下的判据假设。一个 task 内分 4 个子批串行交付。"

### scope

**子批 A：gate 对未知阶段 fail-open（RM-AG0064）**

- **问题（实测）**：`agate/scripts/check-gate.py` 的 phase 分派：
  ```python
  handlers = {"P0": gate_p0, ..., "P8": gate_p8}
  func = handlers.get(phase)
  if func is None:
      sys.stderr.write(f"未知阶段: {phase}\n")
      sys.exit(2)      # ← exit 2 = P0/P1/P2/P3/P5/P6/P8 的「通过」码
  ```
  **实测证据**：`python3 agate/scripts/check-gate.py P99 <task_dir>` → `exit=2`（与真实阶段 P8 相同）；`check-gate.py:1486-1489`。
- **后果链（实测）**：未知阶段 → `exit 2` → `pre-commit-gate.py:354` 记录 `write_gate_result(exit=2)` → `ci-gate-backstop.py:209-211` 比对「记录值 == CI 重跑值」（`if recorded_exit != ci_exit`；205-208 是 phase 比对）（两者都是 2）→ **PASS**。**CI 验证的是一致性，不是正确性**——两边错得一样就都通过。
- **修复方向**：① 未知阶段改为 **exit 1**（fail-closed）② 新增 regression 测试（构造未知 phase → 断言 exit 1 且 stderr 含阶段名）。
- **参照**：agateon 其他处的 fail-closed 取向（DSH preset 挂载失败拒绝建会话）。

**子批 B：三处数字序号假设致非数字阶段名静默失效**

- **问题（实测）**：三处用 `re.search(r"[0-9]+", phase)` 推导阶段序，非数字阶段名（如 `p-alpha`）无匹配时不报错：
  | 位置 | 形态 | 失效方式 |
  |------|------|---------|
  | `check-gate.py:1465-1466` | `re.search(r"[0-9]+", ...)` | 回退抵达检测恒不触发（`if old_num and new_num` 短路） |
  | `check-state-transition.py:212-215`（`return ... if m else 0` 在 215） | `phase_num()` 无匹配 `return 0` | 非数字阶段名全部映射为 0 → 转移判定错乱 |
  | `pre-commit-gate.py:82,192-195`（`return m.group(0) if m else None` 在 195；静默跳过在调用点 577 `if not out_phase: continue`） | `_P_NUM_RE = re.compile(r"P[0-8]")`（**不同模式**，大小写敏感） | 无匹配返回 `None` → 调用点 `if not out_phase: continue` 静默跳过 |
- **修复方向（两案，P2 定案）**：
  - **最小案**：非数字阶段名在回退检测中**显式报错**（而非静默短路）——纯判据修复，**不碰 `phases.yaml` 语义**，与本批 out-of-scope 无冲突
  - **完整案**：建立**显式阶段序**（`phases.yaml` 加 `order:`/`predecessors:`，需先解 `additionalProperties: false`）→ 三处改为查表
  - ⚠ **范围澄清（独立评审）**：完整案实质是**阶段语义声明式化**，而本批 out-of-scope 写「不做 phase 语义重构」——**两者冲突**。**建议本批采用最小案**（纯判据修复）；完整案作为**独立议题**（见分析报告 §5.4 的落地路径，含 schema 改动 + 存量兼容）。
- **与子批 A 的关系**：同属"非 P0-P8 阶段名会静默坏掉"，**建议一并修**。

**子批 C：DEBT0037（check-gate.py P4 完整度判据）**

- **问题**：`_gate_p4` 完整度判据「暂存区含非 md/yaml 代码文件」在两种场景 **exit 1**：① 一个 phase 跨多个 commit ② P5→P4 回退后修复 commit。`agate-next.py` 据此拒绝推进 → 主 Agent 手动 `_advance`（TAG0033 P4→P5 两次实证）。
- **修复方向**：判据放宽为「本 phase 任一 commit 引入过代码 diff」（`git log` 扫 phase 起点..HEAD 的非 md/yaml），或显式识别「回退后再推进」（`.state.yaml` `retries[P4]` 非空 + 已有 `wf(TAGxxxx-P4)` commit）。
- **同类核查**：其它 phase 完整度判据是否共用「看暂存区」假设。

**子批 D：DEBT0038（judge 信息隔离黑白名单假阳性）**

> ⚠ **范围修正（独立评审 MUST-FIX，2026-09-16）**：原 D 含 DEBT0038 + DEBT0040 + DEBT0041 三条。评审指出：
> ① **DEBT0040（账本测试隔离）含 CI workflow 改动**（`.github/workflows` 加 `git diff --exit-code` 兜底步）——按仓库 `AGENTS.md` 规则 5，**改 CI 配置需用户明确许可**，不应静默包含在本批内
> ② **DEBT0041（字段集同源）与"gate 健壮性"仅名义相关**——它改的是 `agate-md-field-set` 与 `check-p6-provenance.py` 的**字段集定义**，属"数据契约一致性"而非 gate 判据健壮性
> ③ 且 **DEBT0041 与 TAG0036 的 `tests_filter` 读同一字段族**（`agate-md-field-get.py` 的 `JSON_FIELDS`）→ 两批文件面**并非完全不重叠**，P0 不宜断言
>
> **故：DEBT0038 保留在本批（它与 gate 判据同簇——都是"check 脚本的判据误判"）；DEBT0040/DEBT0041 移出**，建议各自独立立项或并入他批。

**DEBT0038（medium/protocol）：`check-judge-verdict.py` 信息隔离黑/白名单扫描 3 处假阳性**

| # | 问题 | 修复方向 |
|---|------|---------|
| ① | 黑名单 `p6-acceptance.md` 子串命中 `agate/phase-cards/P6-acceptance.md`（阶段规格卡片，非 verifier 自述）——缺路径豁免 | `check-judge-verdict.py` 的 `_check_blacklist` |
| ② | 白名单不含角色定义文件路径（与"每个 dispatch-context 列角色文件"通用惯例冲突，P6.5 是唯一例外但派发模板 / P6 卡未写明） | `_check_whitelist` + `dispatch-protocol.md`「Judge 信息隔离」节 + P6 卡 |
| ③ | `P6-evidence/` 目录白名单不认目录下裸文件名 | `_check_whitelist` |

### out-of-scope

- **不做**：`check-gate.py` 的 phase 语义重构（本批只修判据健壮性，不重写 gate 逻辑）
- **不做**：`handlers` 字典的声明式化（即"把 10 个手写 `gate_pN` 改成 YAML 驱动"——属独立议题，见分析 §5.4）
- **不做**：TAG0036（MVWU 试点）的任何内容——**两批文件面不重叠，可并行但互不包含**
- **不做**：DAG 相关（已定为 Research Trigger，`E_pipeline` 超阈值才研究）

### 交付物（预期）

| # | 交付 | 触发 SELF-GATE |
|---|------|--------------|
| 1 | `check-gate.py`：未知阶段 exit 1 + 三处数字假设修复 | ✅ |
| 2 | `check-state-transition.py` / `pre-commit-gate.py`：阶段序查表 | ✅ |
| 3 | `phases.yaml`：`order`/`predecessors` 声明（如采用显式阶段序方案） | ✅ |
| 4 | `_gate_p4` 判据放宽（DEBT0037） | ✅ |
| 5 | `check-judge-verdict.py` 黑白名单 3 处修正（DEBT0038） | ✅ |
| 6 | regression 测试若干 | — |

## known_risks

- **多提交阶段任务的自指风险（范围收窄，独立评审修正）**：`_gate_p4` 仅在 `git diff --cached --name-only` **无任何非 md/yaml 文件**时 `return 1`（`check-gate.py:951-961`）。本批 3 个子批（A/B/D）各含 `.py` 改动，**每个 commit 都不会命中**；**只有纯 md/yaml 的 commit 才会命中**（如仅改文档/协议 md 的子批）。**缓解**：拆批时确保每个 commit 含至少一个代码文件；P2 明确拆批与提交策略。
- **`phases.yaml` schema 变更的破坏性**：`additionalProperties: false`，加 `order`/`predecessors` 必须改 schema；存量任务（以命令计数）+ 下游项目需兼容（**默认值 = 现状行为**，不得改变既有阶段判定）。
- **失败模式**：判据放宽（DEBT0037）若过宽会削弱 gate 拦截力——需明确"放宽后仍能拦住什么"的边界，并在 P3 设计对应红灯用例。
- ~~子批 D 的字段集统一（DEBT0041）可能牵出隐含依赖~~ —— **已随范围收窄移除**（见上文「范围修正」：DEBT0041 已移出本批，与 TAG0036 `tests_filter` 同字段族，独立评审判定不宜与 gate 健壮性合并）。此条保留删除线仅作历史留痕，不构成本批风险。

## env_constraints

- 运行 agateon 只需系统 `python3` + `pyyaml`
- 全部改动命中 SELF-GATE 触发面（`agate/scripts/*.py` / `agate/rules/*.yaml`）→ 需 `protocol-alignment-review` + 全量 pytest + consistency 0 ERROR
- 测试须平台无关（Windows 只跑 `-m windows_smoke`）

## executor_env

- 仓库：`/home/kity/oclab/agateon`（主 checkout 禁止改动；worktree 开发）
- 稳定版工具：`~/.agate/scripts/`（勿动）
- 相关证据：`docs/design-notes/design-orchestration-evolution-analysis.md` §5.3 + 附录 B；`agate-workspace/debt/tech-debt.md` 的 DEBT0037/0038/0040/0041
- 先例参照：`TAG0023-mechanism-checks`（机制校验补强批）/ `TAG0031-debt-cleanup`（DEBT 存量修复批）
- **worktree**：`.worktrees/agate-TAG0035`（分支 `feat/TAG0035-gate-robustness`），构建流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0035.md` 按模板全 9 节填写
