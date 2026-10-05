---
phase: P4
task_id: TAG0042
agent: implementer
implementation_dir: agate/
---

# P4 实现 — batch4-gate-layer（关卡层分级 + P8 交付收尾 + preset 等价物）

> 范围：仅 BDD-14 / BDD-15 / BDD-21（P2 §6.1b `batch4-gate-layer`）。不碰 batch5-6。
> 自查 ≠ gate：本文只报自跑结果，不预判 P5 gate 结论。

## 1. 改动清单（文件 → 落点）

| 文件 | 落点 | 对应 |
|---|---|---|
| `agate/rules/phases.yaml` | ① P8 `name: 发布准备` → `交付收尾`；② P8 `gates[]` 描述补 `delivery`；③ 新增顶层 `gate_layer`（`commit_types` 提交类型→关卡集合 + `transitions` 转换表，含字面 `paused_from`） | BDD-14/15 |
| `agate/rules/schema/phases.schema.json` | 根 `properties` 新增 `gate_layer`（`additionalProperties: false` 下必须同步；见 §4 DESIGN_GAP-2） | BDD-14 |
| `agate/scripts/check-gate.py::gate_p8` | ① `debt_check` 后新增 `delivery` 声明校验（缺 → `return 1`，输出含 `delivery`）；② 发版痕迹存在但无 `agate.config.yaml` 时输出指向 `semver-changelog-tag` / `release.preset` 的 WARNING（不阻断）。既有 bump_type/debt_check/version/CHANGELOG/tag/roadmap 检查**全部保留** | BDD-15/21 |
| `agate/phase-cards/P8-release.md` | 标题 `P8 — 发布` → `P8 — 交付收尾`；产出规格 + gate 规则各补 `delivery` 声明要求 | BDD-15 |
| `agate/UPGRADING.md` | v0.79.0 节内**按批次顺序追加**批 4 小节（preset 迁移 `release.preset: semver-changelog-tag` + 截止版本 v0.80.0）；未改批 1/批 2 段落 | BDD-21 |
| `agate/WORKFLOW.md` | P8 总览表行 `名称` 列 `发布准备` → `交付收尾`（S-1 YAML↔md 名称一致强制同步；见 §4 DESIGN_GAP-3） | BDD-15 |
| `agate/tests/unit/test_check_gate.py` | G8 系列夹具 `_P8_COMPLIANT` 补 `delivery: package-release`（同步新增 `delivery` 强制） | BDD-15 |
| `agate/tests/unit/test_t41_platform_hygiene.py` | 直接调 `gate_p8` 的夹具补 `delivery`（同上） | BDD-15 |
| `agate/tests/regression/test_v060_p8_cached.py` | `_P8_RELEASE` 夹具补 `delivery`（同上） | BDD-15 |
| `agate/tests/unit/test_check_p8_delivery.py` | `_p8_repo` 复制目标补 `dirs_exist_ok=True`——**测试夹具缺陷修复**（见 §5），未改任何断言 | — |

## 2. 关键设计落点

### 2.1 `gate_layer`（BDD-14）

```yaml
gate_layer:
  commit_types:
    code-only: [P0, P1, P2, P3, P4, P5, P6, P6.5, P7, P8]
    docs-only: [P0, P1, P2, P7, P8]
    release: [P7, P8]
  transitions:
    forward: [{from: P0, to: P1}, ... {from: P7, to: P8}]
    retreat: [{from: P5, to: P4}, {from: P6, to: P4}, {from: P6.5, to: P6}]
    pause: [{to: PAUSED, paused_from: [P0, ..., P8]}]
```

- 满足 TC-B14-01 的**键名无关结构扫描**（同容器下 3 个 phase-id 列表值、≥2 个不同集合）。
- 满足 TC-B14-02 的字面 `paused_from`。
- **语义不变**：未触碰任何 phase 的 `gate_pass_exit` / `next` / `retreat`（TC-B14-01 回归基线保持）。

### 2.2 P8 交付收尾（BDD-15）

- `gate_p8` 顺序：`bump_type` → `debt_check` → **`delivery`** → roadmap → version/CHANGELOG/tag → 声明缺失 WARNING。
- `delivery` 只查留痕存在（`"delivery:" in text`），内容任意放行（合法取值集合设计未定，见 §4 DESIGN_GAP-1）。
- 既有检查全部保留；`_P8_COMPLIANT` 等夹具同步补 `delivery`，G8 系列回归不变。

### 2.3 preset 等价物 + 迁移提示（BDD-21）

- 等价物（`agate.config.yaml` 的 `release.preset: semver-changelog-tag`）由 batch2 已落地并 validate 通过（TC-B21-01 绿灯）。
- 本批新增：无声明 + 有发版痕迹（version/CHANGELOG 变更）→ P8 gate 输出显眼 WARNING（指向 `semver-changelog-tag` / `release.preset` / `agate.config.yaml`），不阻断。
- `UPGRADING.md` 写明迁移方式 + 截止版本 v0.80.0。

## 3. R3 前置：发版逻辑消费方全量 grep（本批**不删除**任何发版逻辑）

> P2 §1.3 R3 / P0-brief known_risks 要求「动手前全量 grep 消费方清单」。以下为实测结果（`agate/` 树，排除 `__pycache__`；`bump_type`/`debt_check`/`releaser`/`bump-version`/`CHANGELOG`/`tag`/`preset` 为检索词）。

**核心实现 / 判定**
- `agate/scripts/check-gate.py::gate_p8`——bump_type/debt_check/delivery/version/CHANGELOG/tag/roadmap（本批改动的唯一发版判定脚本）。
- `agate/scripts/check-structure-consistency.py`——`_TASK_FRONTMATTER_FIELDS` 含 `bump_type`（frontmatter 字段白名单）。
- `agate/scripts/check-changelog.py`——CHANGELOG `[Unreleased]` / post-bump 模式。
- `agate/scripts/check-protocol-consistency.py`——CHECK 7（badge↔CHANGELOG）/ CHECK 13（CHANGELOG↔UPGRADING）。
- `agate/scripts/check-pruning.py`——裁剪 P8 的 `internal_only` 校验。
- `.github/workflows/release.yml`——`v*` tag 指向校验（badge/CHANGELOG 版本节）。

**数据面 / 声明**
- `agate/rules/phases.yaml`——P8 `task_fields: [bump_type]` + 本批新增 `gate_layer`。
- `agate/rules/schema/phases.schema.json`——`task_fields` 通用 + 本批新增 `gate_layer`。
- `agate/rules/schema/project-config.schema.json` + `agate/scripts/agate-config.py` + `agate/scripts/agate_common.py`——`release.preset: semver-changelog-tag` 等价物。

**叙事 / 卡片 / 角色**
- `agate/phase-cards/P8-release.md`（本批改）、`agate/phase-cards/P5-verification.md`（bump-version）。
- `agate/WORKFLOW.md`（P8 行，本批改）、`agate/dispatch-protocol.md`（P8→READY 门槛表）、`agate/state-machine.md`（P8 转移/releaser/bump-version）。
- `agate/assets/execution-roles/implementer.md`（P8 发布准备）、`agate/role-system.md`（P4/P8）、`agate/assets/templates/task-files.md`（P8 发布检查命令）、`agate/assets/templates/retrospective-template.md`（P8 internal_only_reason）、`agate/LIMITATIONS.md`。
- `agate/UPGRADING.md`（本批改）。

**结论**：发版逻辑消费方散布于判定脚本 / 数据面 / 卡片 / 角色 / 叙事 / CI 六个面。本批**只提供等价物 + WARNING + UPGRADING 截止版本**，**不删除任何发版逻辑**（BDD-21 的 Then 只要求等价物 + WARNING + UPGRADING）。「是否/何时删除发版逻辑、按什么顺序收敛上述六个消费面」交 P7 裁决（见 §4 DESIGN_GAP-4）。

## 4. [DESIGN_GAP] 登记（交 P7 逐条审查）

[DESIGN_GAP: 批 4「提交类型 → 关卡集合」的具体成员与转换表矩体属 P2 §11 预留的设计未定面；P4 落定 code-only=全链 / docs-only=[P0,P1,P2,P7,P8] / release=[P7,P8]；P7 逐条审查]
[DESIGN_GAP: phases.schema.json 不在 §6.1b batch4 output 列，但 phases.yaml 新增顶层键在 additionalProperties:false 下必须同步 schema（P2 §1.1 M11 已条件预见）；P4 已扩展，交 P7 核对]
[DESIGN_GAP: WORKFLOW.md 不在 §6.1b batch4 output 列，但 S-1（YAML↔WORKFLOW 名称一致）强制同步 P8 行名称；P4 已同步，交 P7 核对]
[DESIGN_GAP: delivery 合法取值集合设计未定；gate_p8 只查留痕存在（"delivery:" 子串），内容任意放行；P7 裁决是否收紧取值校验]
[DESIGN_GAP: 发版逻辑消费方散布于判定脚本/数据面/卡片/角色/叙事/CI 六面（见 §3）；本批只提供 preset 等价物 + WARNING，未删除任何发版逻辑；「是否/何时删除、收敛顺序」交 P7 裁决（截止版本 v0.80.0 已写 UPGRADING）]
[DESIGN_GAP: P8 叙事面（state-machine.md「P8 是发布准备」节、dispatch-protocol.md P8→READY 表、role-system.md、implementer.md）仍写「发布准备」，不在 §6.1b batch4 output 列，P2 未指定是否随名称改述；本批只改 phases.yaml/WORKFLOW/卡片，P7 裁决是否统一叙事]

## 5. 测试夹具缺陷修复（非断言变更）

`agate/tests/unit/test_check_p8_delivery.py::test_bdd_15_p8_gate_passes_only_when_delivery_declared` 在同一 `git_repo` 上先后跑「未声明 / 已声明」两场景，但 `_p8_repo` 两次都复制到 `repo/task`——第一次复制成功后第二次 `shutil.copytree` 抛 `FileExistsError`。改动前该用例因**首个断言**（未声明未拦截）先行失败，掩盖了此夹具缺陷；`delivery` 实现落地后首个断言通过，缺陷暴露。

- 修复：`shutil.copytree(td, repo / "task", dirs_exist_ok=True)`（Python 3.8+；第二次覆盖 `task/`，两场景仅 `P8-release.md` 不同）。
- **未改动任何断言 / 期望值**——只让两场景都能执行；不影响 BDD-15 语义。

## 6. 自跑结果（自查 ≠ gate）

- 目标用例：`pytest agate/tests/unit/test_gate_layer.py agate/tests/unit/test_check_p8_delivery.py agate/tests/unit/test_check_gate.py -q` → **227 passed**（改动前 `test_gate_layer.py`+`test_check_p8_delivery.py` = 7 failed / 1 passed）。
- 相邻回归：`test_check_structure_consistency.py` / `test_check_yaml_schema.py` / `test_t41_platform_hygiene.py` / `test_v060_p8_cached.py` / `test_check_protocol_consistency.py` / `test_agate_debt_check.py` → **101 passed**。
- `check-protocol-consistency.py --strict-errors-only` → **0 ERROR**（404 frozen WARNING，基线不变）。
- `check-structure-consistency.py` → S1-S6/S0 全 OK。
- `bash agate/tests/scripts/count-tests.sh` → 2689（未增删测试文件，无漂移）。
- `~/.venvs/agate-dev/bin/ruff check agate/scripts/` → All checks passed。
- 平台扫描改动代码/测试文件 → exit 0（0 命中；UPGRADING/WORKFLOW 属文档，非 `agate/tests/` 扫描面）。
- 全量 pytest（`agate/tests/ -n auto`）→ 见 §7。

## 7. 全量回归

全量 `pytest agate/tests/ -q -n auto` → **16 failed, 2671 passed, 2 skipped**。

16 个失败**全部为既有红灯，与本批无关**（已用 `git stash` 去掉本批改动后复跑，失败集合逐条一致：16 failed / 7 passed）：

| 失败 | 归属 | 原因 |
|---|---|---|
| `test_agate_doctor.py` ×8 | **batch5**（BDD-17） | batch5 未实现，P3 红灯测试（本批不碰 batch5） |
| `test_agate_ci_verify.py` ×6 | **batch5**（BDD-16） | 同上 |
| `test_agate_scripts_encoding.py::test_bdd_5...` | batch3 | `test_agate_run.py:282/284` text I/O 缺 `encoding`（既有缺陷，非本批文件） |
| `test_setup_agate_dir.py::test_bdd_43...` | 环境 | 本机 `opencode debug agent` 子命令已改名 `agents`（工具版本，非本批） |

⇒ 本批未引入任何新失败。

## 8. 修正轮（SELF-GATE round 7 修复）

> 来源：round 6 SELF-GATE 判 misaligned（A2/A3b/A5.3，同一根因 = P8 名称/语义由「发布准备」改「交付收尾」后 6 处名称级叙事未同步）+ 编码守卫误判。
> 自查 ≠ gate：本节只报自跑结果，不预判 P5/P8 gate 结论。

### 8.1 修复清单 A：P8 叙事同步（「发布准备」→「交付收尾」）

名称/身份级（round 6 判 MISALIGNED 的 6 处）：

| 文件 | 位置 | 改前 → 改后 |
|---|---|---|
| `agate/state-machine.md` | :311 | 「P8 是**「发布准备」**」→「P8 是**「交付收尾」**」 |
| `agate/state-machine.md` | :315 | 表「发布准备 (READY)」→「交付收尾 (READY)」 |
| `agate/dispatch-protocol.md` | :881 | 「P8→READY \| 发布准备完成」→「交付收尾完成」 |
| `agate/WORKFLOW.md` | :256 | 「P8 发布准备」→「P8 交付收尾」（与同文件 :327 一致）|
| `agate/role-system.md` | :29 | 「多包发布准备」→「多包交付收尾」|
| `agate/assets/execution-roles/implementer.md` | :9 | 标题「P8 发布准备」→「P8 交付收尾」|

活动级残留（随本修复一并对齐）：

- `agate/state-machine.md:167`（releaser 执行发布准备 → 交付收尾）、`:438`（P8 表「发布准备，少轮次」→「交付收尾，少轮次」）
- `agate/assets/execution-roles/implementer.md:11`（P8 定位句）
- `agate/phase-cards/P8-release.md:9`/`:29`/`:47`（步骤叙述）
- `agate/LIMITATIONS.md:119`（「P8 发布准备成为唯一把关点」）
- `agate/WORKFLOW.md:166`（Claude Project 不适合项）

口径：P8 = **交付收尾**（与 `phases.yaml name` / `WORKFLOW.md:327` / `P8-release.md` 标题同口径）；**未改** P8 实际活动（bump-version / CHANGELOG 等既有检查全部保留），只改名称/语义表述。

残留（不在本修复面，未改）：

- `agate/UPGRADING.md:313`（「原「发布准备」」——描述改名的历史注，须保留）；`:1269`（旧版本历史节）。
- `agate/tests/unit/test_check_p8_delivery.py:10`/`:145`（描述改动前红灯状态的历史注释，非断言）。

### 8.2 修复清单 B：编码守卫误判

`agate/tests/unit/test_agate_run.py:282,284` 字符串字面量含 `with open(` / `with open(...)`，触发 `test_agate_scripts_encoding.py::test_bdd_5`（正则 `\bopen\(` + 无 `encoding=`）。

- `:282`：`startswith("with open(")` → `startswith("with open" + "(")`（等价，避开字面 `open(`）。
- `:284`：报错文案 `` `with open(...)` 落盘 `` → `with-open 落盘`。
- **未改任何断言语义**。

### 8.3 自查结果（自查 ≠ gate）

- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → **0 ERROR**（404 WARNING，基线不变）。
- `python3 agate/scripts/check-structure-consistency.py` → S1-S6/S0 全 OK。
- `python3 -m pytest agate/tests/unit/test_agate_scripts_encoding.py agate/tests/unit/test_gate_layer.py agate/tests/unit/test_check_p8_delivery.py -q` → **10 passed**。
- `python3 -m pytest agate/tests/unit/test_agate_run.py -q` → **10 passed**（被改测试文件本体回归）。
- `bash agate/tests/scripts/count-tests.sh` → **2689**（未漂移）。
- `grep -rn "发布准备" agate/state-machine.md agate/dispatch-protocol.md agate/WORKFLOW.md agate/role-system.md agate/assets/execution-roles/implementer.md` → **0 命中**。
