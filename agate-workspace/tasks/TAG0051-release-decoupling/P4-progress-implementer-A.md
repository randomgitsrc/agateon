# P4 progress — implementer A（批 `ready-no-tag` + `release-gate`）

范围（只改这三个文件）：
- `agate/scripts/check-gate.py`（M1：P8 去 tag/version + `delivery.method` 枚举校验）
- `agate/scripts/agate-release.py`（M11：新增 `gate` 子命令）
- `.github/workflows/release.yml`（M12：`workflow_dispatch` + gate backstop）

## 2026-10-11 已读输入
- implementer.md 角色定义；P4-dispatch-context-implementer-A.md（强制指令）
- P2-design.md（§1.1 M1/M11/M12 落点与行号、§3 决策、§4 批表、§9 完成标准）
- P3 红灯测试：`test_tag0051_p8_gate.py`、`test_release_gate.py`、`test_tag0051_delivery_contract.py`
- 落点代码：`check-gate.py::gate_p8`（:2236-2453）、`agate-release.py`（全文 365 行）、`release.yml`（95 行）
- 依赖：`agate_common.py`（`load_contract` :2032 / `task_level` :2084 / `default_branch` :1291）、
  `conftest.py` fixtures（`git_repo`/`agate_scripts`/`run_cli`/`load_fixture`）

## 关键事实
- P3 提供三个红灯文件：`test_tag0051_p8_gate.py`（BDD-2/3/4/5/6/7/19）、
  `test_release_gate.py`（BDD-8/9/10/11/12/13/23）、`test_tag0051_delivery_contract.py`（BDD-16/17）。
- `check-gate.py P8` 通过退出码 = **2**（`_P8_PASS_EXIT`）；缺 `bump_type` → 1；RM 非 done → 1。
- `level-2` 快照（含 `delivery.method_enum`）由 Impl-B 落地；本批按其「缺省 no-op」处理。
- 状态：[PROD_NOT_TOUCHED]（未触发任何 push/PR/merge/tag/Release 等不可逆外部动作）。

## 2026-10-11 实现完成

### M1 `agate/scripts/check-gate.py::gate_p8`
- **删** 四个 WARNING 块：version 双路径（原 :2317-2337）、CHANGELOG 暂存区 diff（:2339-2356）、
  迁移期 `agate.config.yaml` 提示（:2358-2374）、tag 存在性（:2376-2389）；`VERSION_TAG_PREFIX` 使用随之移除。
- **新增** `delivery.method` 枚举校验（在结构化 delivery 分支内、`required`/`none`/`ref` 之后）：
  读 `_delivery_spec(task_dir)["method_enum"]`；快照无该键 → no-op；枚举外非空 → exit 1。
  legacy 走 :2288 子串路径（**未动**，OBL-P8-02 变异锚点保持）。
- **保留** `bump_type` / `debt_check` / 结构化 `delivery` / RM-AG0043 反查。
- 收尾消息去掉已废的「④ 从 P2 packages 验证 version 文件路径」（决策 5「version 文件检查 → 移除」的直接残留）。

### M11 `agate/scripts/agate-release.py`
- 新增 `gate` 子命令（`_cmd_gate` + `_run_cmd`/`_git_toplevel`/`_gh_json`/`_repo_slug`/
  `_required_checks`/`_gh_check_runs`/`_ci_runs`/`_non_success_names`）。
- 串起 ① check-gate.py P8（给 `--task` 时）② check-protocol-consistency.py 0 ERROR
  ③ 目标提交 CI success（fail-closed：任一 required 非 success/缺失 → 非 0）。
- CI/consistency 均**可注入**（`--ci-cmd` / `--consistency-cmd` / 同名 env）；缺省用真 `gh`，
  经 `_repo_slug`+`default_branch`（agate_common，RM-AG0116）解析仓库/分支，**不写死 main**；
  无 `sleep`/无界轮询。既有子命令行为不变（argparser 仅在 `build` 后追加 `gate`）。

### M12 `.github/workflows/release.yml`
- `on:` 追加 `workflow_dispatch`（带可选 `tag` 输入），与 `push: tags:['v*']` **并存**；
  `TAG` 解析改为 `inputs.tag || ref_name`。
- 新增 `Release gate (fail-closed backstop)` 步——**只调用** `agate-release.py gate`，不内联逻辑；
  `permissions` 增 `checks: read`；显式 `AGATE_RELEASE_REQUIRED_CHECKS`（6 项 required contexts）。
- 既有「Verify tag points to matching commit」步**保持不动**（BDD-11 回归锁）。

## 自查（≠ P5 gate）
- ✅ `test_tag0051_p8_gate.py` **8/8 全绿**（BDD-2/3/19 由红转绿；BDD-4/5/6/7 回归锁）。
- ✅ `test_tag0051_delivery_contract.py` **3/3 全绿**（BDD-16/17 由红转绿——依赖 Impl-B 已落地的 level-2.yaml）。
- ⚠️ `test_release_gate.py`：BDD-8/11/23（5 用例）**绿**；BDD-9/10/12/13（5 用例）**红**，
  但**红因是测试夹具缺陷**（见下 `[SCOPE+]`），**非我的实现**——已用等价探针（`/tmp/opencode/ga_probe.py`，
  以正确的 `GENESIS_HASH` 构造账本）逐一复现：CI ok→0、CI in_progress/failure→非 0、consistency rc1→非 0、
  RM scheduled→非 0、`gate --help`→0，**全部符合预期**。
- ✅ `ruff check agate/` 全绿（我改的两个 .py 无新增错误）。
- ✅ `check-protocol-consistency.py` **0 ERROR**（CHECK 8 `--cached` 锚点仍在：4 处；CHECK 9/16 PASS）。
- ✅ 实测 `check-gate.py P8 <fixture>` → exit **2**，stderr 无 `tag` / `version 文件变更` / `agate.config.yaml`（BDD-2/3/19 完成标准 1）。
- 其它 implementer 面（未越界、仅记录）：`test_tag0051_obligations_sync.py` 2 红（OBL-P8-04 未重挂）＝ Impl-B 面。

## [SCOPE+]
> [SCOPE+] `agate/tests/unit/test_release_gate.py` 的 `_ledger()` 用了 `H.GENESIS_HASH`（`H = helpers_tag_repo`），
> 但 `GENESIS_HASH` 只定义在 `helpers_tag0050.py`，`helpers_tag_repo.py` **无该属性** ⇒
> BDD-9/10/12/13 五条用例在**夹具构造期**即 `AttributeError`（A 类），无法验证发布门实现。
> 修复属 `agate/tests/**`（我**不得**触碰）；我的实现已用等价探针独立验证通过。
> 建议：由 P3 侧修（改 `import helpers_tag0050 as H5` 并用 `H5.GENESIS_HASH`，或 `H` 增补常量）。

[PROD_NOT_TOUCHED]
