---
phase: P4
task_id: TAG0037
type: implementation
parent: P2-design.md
trace_id: TAG0037-P4-20260920
status: draft
created: '2026-09-20'
implementation_dir: agate/scripts
agent: implementer
---

# P4 实现记录 — TAG0037 安装与多版本模型统一

## 批 A-package-lib

**改动文件清单**：新增 `agate/scripts/agate_package.py`（stdlib-only 共享模块）；新建本文件 `P4-implementation.md`。未改任何既有文件、未改测试。

**实现要点**（P2 §3.2 接口逐一落地）：边界常量与 `is_packaged` / `boundary_lines` / `parse_release_ref`（fullmatch + re.ASCII，拒 `v1.2.3\n` 与 Unicode 数字）/ `is_strict_version`；`list_package`（`ls-tree -r -z --full-tree`，软链 / 子模块 / 路径硬化 / casefold 冲突 / 非 UTF-8 / 缺 `agate/scripts/` → `PackageError`）；`materialize`（`cat-file --batch` 原始 blob，校验对象类型与哈希，`O_EXCL|O_NOFOLLOW` 逐文件创建，`os.mkdir` 不用 `makedirs(exist_ok)`，越界检测）；`copy_files`（lstat 校验、忽略字节码）；`commit_mtime`；`write_dir_tarball`（先校验后写入、PAX、mode/uid/gid 归一、手写 gzip 头 FNAME=0/MTIME=0/OS=255，与 Python 版本无关、临时文件 + `os.replace`）；`verify_dir`；`normalize_home` / `is_symlink_base` / `agate_home`；`make_work_dir` / `sweep_stale`（仅「前缀 + 真实目录 + 有效标记 + 标记 >1h」，永不按名字模式删）/ `recover_backups`（只改名）/ `swap_in` / `rollback_swap` / `discard_backup`（仅本进程创建的备份容器，否则返回 False 并保留）/ `snapshot_pointers` / `restore_pointers`。模块顶部 `sys.dont_write_bytecode = True`。

**tests_filter**：`python3 -m pytest agate/tests/unit/test_agate_package.py -q -k "not eng_n1 and not t21_compute_sha256_directory_ignores_bytecode"`（`PYTHONDONTWRITEBYTECODE=1`）→ **127 passed / 0 failed**（2 deselected：批 E/B 组夹具用例）。
附加自查：`ruff check agate/scripts/agate_package.py` 通过；`test_install_offline.py -k test_lib_`（B2 组对本批换位 / 清扫 / 指针库函数的用例）8 项全绿；同文件 `t23_install_...` 集成用例因依赖 B2 批 `install-offline.py` 改造仍红（预期，非本批范围）。

**标注**：无 `[TEST_BUG]`；无 `[SCOPE+]`。
[DESIGN_GAP: P2 §3.2 未指定 discard_backup 拒绝路径的表现形式，实现为返回 False 并向 stderr 打印警告（不抛异常，避免 adopt 成功后的清理步骤崩溃），测试接受异常或忽略两种]
[DESIGN_GAP: P2 §3.2 未指定 rollback_swap 对「新目录」的处置，实现为将其移入备份容器 failed-new/ 后删除（属本进程刚创建，且要求无遗留容器）；仅在备份容器为本进程创建且标记有效时才回滚]
[DESIGN_GAP: P2 §3.2 `make_work_dir` 未指定根目录不存在时的行为，实现为 `os.makedirs(root, exist_ok=True)`（离线安装到全新 --dest-root 需要）；软链基址守卫由调用方入口负责]

**SELF-GATE 触发说明**：本批新增 `agate/scripts/agate_package.py`（协议本体脚本），改动路径落在 SELF-GATE 监管的 `agate/` 内；本批未 commit，SELF-GATE 提示 / self-gate-review 由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 未动。

## 批 B1a-online-install-core

**改动文件清单**：仅 `agate/scripts/agate-install.py`（未改测试、未碰 `agate_common.py` / `agate-resolve.py` / `agate-summary.py` / `install.sh`）。

**实现要点**（P2 §3.3）：入口顶部 `sys.dont_write_bytecode = True` 先于 `import agate_package`；`_agate_home` 委托 `agate_package.agate_home()`；`_VERSION_RE = agate_package.VERSION_RE` 全部改 `fullmatch`（版本号校验前移到任何 clone / 写盘之前，非法 → exit 2）；`git clone -- <url>`；`_install_version` 改为 `sweep_stale` / `recover_backups` → `list_package`（失败 exit 1 且未建目录）→ `make_work_dir` → `materialize` → `swap_in`，异常只清理本进程创建的 `.agate-tmp-` 容器（`_worktree_add` 已删除）；软链守卫 `_reject_symlink_home` 同时检查原始 `AGATE_HOME` 文本与规范化路径（覆盖 `L/` `L//` `L/.` `L/..`），文案 `_SYMLINK_HOME_MSG` = 动态首行 + 三步迁移（片段与 install.sh 逐字一致）+ BDD-51 附句；`_register(move_pointers)`（指针写入含快照 / 失败还原）+ `_sync_root_scripts`（忽略字节码、`symlinks=True`）；`--uninstall`：仅旧形态（含 `.git`）且 `repo/` 存在才 `git worktree remove`，新形态直接移除，`repo/` 存在即 `git worktree prune`。未实现 `--adopt` / `--check --portable`（属 B1b）。

**tests_filter**：`python3 -m pytest agate/tests/unit/test_agate_version_install.py agate/tests/unit/test_agate_install_uninstall.py -q -k "not bdd_35"`（`PYTHONDONTWRITEBYTECODE=1`）→ **50 passed / 0 failed**（2 deselected）。不加 `-k` 的全量：51 passed / 1 failed —— 失败项 `test_bdd_35_migration_steps_consistent_across_all_entries` 因 `install-offline.py` 缺三步迁移片段（波次末转绿，依赖 B2 批；`agate_common.py` / UPGRADING 片段依赖 E / F1a）；`test_bdd_35_runtime_stderr_steps_identical_between_installer_and_resolver` 已绿。
附加自查：`test_repo_url_no_stale_rename.py` / `test_protocol_root_dual_impl.py` / `test_install_sh.py` / `test_version_lifecycle_e2e.py` 43 passed；`ruff check agate/` 通过。

**标注**：无 `[TEST_BUG]` / `[DESIGN_GAP]` / `[SCOPE+]`。

**SELF-GATE 触发说明**：改动 `agate/scripts/agate-install.py`（协议本体脚本，落在 SELF-GATE 监管的 `agate/` 内）；本批未 commit，SELF-GATE / self-gate-review 由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 函数体未动。

## 批 E-legacy-removal-code

**改动文件清单**：`agate/scripts/agate_common.py`、`agate/scripts/agate-resolve.py`、`agate/scripts/agate-summary.py`、`install.sh`（未改测试、未碰 `agate-install.py`）。

**实现要点**（P2 §3.7、D-8）：
- `agate_common.py`：`from agate_package import _is_bytecode, agate_home, is_symlink_base`；`_resolve_version_info(start_dir=None)` 去 `use_legacy` 与 `realpath(base)` 分支，基址取 `agate_home()`（规范化单源），返回 dict 恒含 `symlink_base`（AGATE_ROOT env 早返回分支恒 False；否则对原始 `AGATE_HOME`/`~/.agate` 判 `is_symlink_base`，保证 `L/..` 变体也能识别）；新增 `symlink_migration_hint(base=None)`（动态「检测到的软链」行 + 规范三步，与 install.sh 同源手写，由 `_migration_steps` 正则跨入口比对）；`resolve_version_root` 文档改三层，`resolve_hook_root` 仅去掉 `use_legacy=False` 实参并清 docstring 措辞（脚本路径上溯 + `.agate-root` 兜底保持）；`compute_sha256` 目录分支跳过字节码（复用 `agate_package._is_bytecode`）。`_protocol_root` 函数体零改动。
- `agate-resolve.py`：终态失败 stderr 原句去 legacy 表述，`symlink_base` 为真时追加 `symlink_migration_hint()`；exit 1；stdout 无 `AGATE_ROOT=`。
- `agate-summary.py`：仅当 `root` 为 None 且 `symlink_base` 时追加迁移提示（BDD-51 软链→完整版本根不打印，eng N-4）；启动建议 2 改 `读 {root}/AGENTS.md`（无根时为「先按上方提示修复安装」）；`changelog_hint` 去 legacy 措辞。
- `install.sh`：重写为无参 = `--versions` 别名（其他参数 → 用法 + exit 2）；删单软链分支与 `INSTALL_DIR/LINK_*`；废弃 env `AGATE_REPO_DIR`/`AGATE_SYMLINK` 任一被设置 → stderr WARNING 后忽略；`AGATE_HOME` 规范化（循环剥离尾 `/`、`/.`，含 `..` 分量 exit 1）后软链守卫前置（动态「检测到的软链」行 + heredoc 三步，先于任何 git 调用）；`git clone --`；头注/末尾不再引用两个废弃变量。

**tests_filter**（`PYTHONDONTWRITEBYTECODE=1`）：`python3 -m pytest agate/tests/unit/test_agate_version_resolve.py agate/tests/unit/test_agate_workspace_resolve.py agate/tests/unit/test_agate_summary.py agate/tests/unit/test_install_sh.py agate/tests/regression/test_protocol_root_dual_impl.py agate/tests/unit/test_hook_resolve_entry.py agate/tests/integration/test_pre_commit_hook.py agate/tests/unit/test_dispatch_context_warning.py -q` → **159 passed / 0 failed**；`python3 -m pytest agate/tests/unit/test_agate_package.py -q` → **129 passed / 0 failed**（含 t21 / eng_n1）。`shellcheck -S warning install.sh` 干净；`ruff check` 三个 py 文件通过。
（说明：首轮全量跑时 `test_install_sh` 的 BDD-29/30/36 与 `test_bdd_7_..._coexist` 曾依赖并行批 B1a 的 `agate-install.py` 产出契约形态版本目录，B1a 落盘后重跑全绿。）
附加自查：`test_agate_common.py`、`test_check_protocol_consistency.py`、`test_mvwu_protocol_docs.py`、`test_tag0037_out_of_scope_untouched.py` 全绿；`integration/test_offline_real_pack_resolve.py` 2 例红（`install-offline.py` 打包布局，属批 B2 范围，非本批）。

**标注**：无 `[TEST_BUG]`；无 `[SCOPE+]`；无 `[DESIGN_GAP]`。

**SELF-GATE 触发说明**：改动落在 SELF-GATE 监管的 `agate/scripts/` 与仓库根 `install.sh`；本批未 commit，SELF-GATE 提示 / self-gate-review 由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 未动。

## 批 B1b-adopt-check

**改动文件清单**：仅 `agate/scripts/agate-install.py`（未改测试、未碰其他批文件）。

**实现要点**（P2 §3.3 / §3.5）：
- 新增 `_cmd_adopt`：版本号 `fullmatch`（非法 exit 2，先于任何文件系统操作）→ `_reject_symlink_home`（原始 + 规范化，覆盖 `L/` `L//` `L/.` `L/..`）→ 版本目录须存在 → 新形态（无 `.git`）走 `agate_package.verify_dir`（软链 / 顶层多余条目 / `agate/tests/` → 逐条列出违约 + exit 1；旧 worktree 形态跳过）→ `_protocol_root(vdir)/scripts` 须存在 → `_register(move_pointers=True)`。不调用 git、不改写版本目录；执行主体即调用方所在目录的兄弟安装器（M-2）。
- 事务化（eng N-2）：复用 B1a 的 `_register`（`snapshot_pointers` → 写指针 → OSError 时 `restore_pointers` 还原 → stderr + exit 1，无 Traceback）；仅把还原处的 `suppress` 扩到 `(OSError, PackageError)`，避免目录形态指针的还原异常泄漏。根 `scripts/` 同步在指针之后，失败仅 WARNING。
- `--check --portable`（opt-in，S-12）：`_cmd_check(portable)`，必需项仅 python3 + pyyaml；git / bash 缺失时打印「提示: … 仅在线安装 / 装历史 tag / agate-changes.py 需要 git；安装 hook 需要 bash」，不计缺项；默认口径不变（缺 git 仍 exit 1，既有 test_bdd_7/8 通过）。`--check` 带其他参数 exit 2。
- `_usage` / `main` / 模块文档串：增 `--adopt`、`--check [--portable]`；`--adopt` 参数个数校验（非 2 个 exit 2）。

**tests_filter**（`PYTHONDONTWRITEBYTECODE=1`）：`python3 -m pytest agate/tests/unit/test_agate_install_adopt.py agate/tests/unit/test_agate_version_install.py agate/tests/unit/test_agate_install_uninstall.py -q` → **75 passed / 1 failed**。唯一失败 `test_bdd_35_migration_steps_consistent_across_all_entries`：`install-offline.py` 缺三步迁移片段（依赖 B2 批；UPGRADING 片段依赖 F1a），与 B1a 记录一致，非本批范围。`test_agate_install_adopt.py` 全部通过。
附加自查：`test_install_sh.py` / `test_protocol_root_dual_impl.py` / `test_agate_version_resolve.py` / `test_agate_package.py` 共 198 passed；`ruff check agate/` 通过。

**标注**：无 `[TEST_BUG]` / `[DESIGN_GAP]` / `[SCOPE+]`。

**SELF-GATE 触发说明**：改动 `agate/scripts/agate-install.py`（协议本体脚本，落在 SELF-GATE 监管的 `agate/` 内）；本批未 commit，SELF-GATE / self-gate-review 由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 函数体未动。

## 批 B2-offline-pack-install

**改动文件清单**：`agate/scripts/agate-pack-offline.py`、`agate/scripts/install-offline.py`（未改测试、未碰其他批文件；`agate_package.py` 仅调用，未修改）。

**实现要点**（P2 §3.4）：
- pack：入口 `sys.dont_write_bytecode = True`；`pack_offline(..., ref=None)` 用 `list_package` + `materialize` 取代 `git worktree add`（bundle 顶层 = `agate/` + 登记根文件 + `wheels/` + `manifest.json`）；构建在本工具专属工作容器（`make_work_dir`）中，成功后 `os.rename` 换位为最终目录，失败只清理本次创建的容器、不产 manifest；输出目录已存在则拒绝覆盖（不删除任何既有内容）；pyyaml 用 `agate_package.PYYAML_PIN`（`pyyaml==6.0.3`）且 wheel 查找大小写无关；manifest 增登记根文件组件、`files`（排序）、`source_ref`；`version` 恒严格 `vX.Y.Z`；`_default_repo()` 运行时取 `AGATE_HOME/repo`；CLI 增 `--ref`。
- install：入口 `sys.dont_write_bytecode = True`；软链基址守卫（原始 + 规范化 dest，三步迁移文案与 agate-install 逐字一致）先于任何写入；`_validate_manifest` 走 `is_strict_version` / `parse_release_ref`（`source_ref` 校验后才展示、不入路径）；`_check_bundle_layout`：旧格式（`agate/agate/scripts`）拒绝、缺本体 / 缺 `files` fail-closed、`os.lstat`+`os.walk(followlinks=False)` 拒软链与特殊文件、磁盘 `agate/**` ∪ 登记根文件与 `manifest.files` 对账、契约外顶层条目仅告警不拷；checksum 文案改"不一致（损坏或被替换）"；`sweep_stale` / `recover_backups` → `make_work_dir` → `copy_files`（只拷 `manifest.files`）→ `verify_dir` → `install_wheels` → `snapshot_pointers` → `swap_in` → 同目录兄弟 `agate-install.py --adopt`（`-B`，`AGATE_HOME=dest`）；adopt 失败 `rollback_swap` + `restore_pointers` 并提示"版本目录与 latest/current 指针均已还原"；成功才 `discard_backup`（仅本次创建的备份容器）。任何失败只 `rmtree` 本次创建且前缀 / 直属 / 真实目录校验通过的工作容器，不做清空重建；不再写 `.installed-version` / `.agate-root`；嵌入式 python 组件仅打印说明。

**tests_filter**（`PYTHONDONTWRITEBYTECODE=1`）：`python3 -m pytest agate/tests/unit/test_install_offline.py agate/tests/unit/test_agate_pack_offline.py agate/tests/regression/test_offline_bundle_roundtrip.py agate/tests/integration/test_offline_real_pack_resolve.py -q` → **75 passed / 0 failed**（含数据安全 T-23 `test_t23_install_sweeps_only_own_expired_containers_and_keeps_everything_else` 与库层 `test_lib_*`）。
附加自查：`ruff check agate/` 通过；`test_agate_version_install.py`（含 `test_bdd_35_migration_steps_consistent_across_all_entries`）/ `test_agate_install_adopt.py` / `test_agate_package.py` 全绿；剩余红灯均不属本批：`test_no_legacy_residue.py` R 清零集合（F2 文档扫除）、`test_install_three_paths.py` 2 例（依赖 C1 `agate-release.py` build 与 F1a portable 文档，`build 应成功 rc=2`）、`test_agate_release.py`（C1 批未实现）。仓库内无遗留 `.agate-tmp-*` / 备份 / 临时文件。

**标注**：无 `[TEST_BUG]`；无 `[SCOPE+]`。
[DESIGN_GAP: P2 §3.4 未指定 pack 输出目录已存在时的行为，实现为拒绝覆盖并报错（数据安全：不清空 / 不删除既有内容）；每次打包需使用新的 `--outdir` 或先自行移走旧 bundle]

**SELF-GATE 触发说明**：本批改动 `agate/scripts/agate-pack-offline.py` 与 `agate/scripts/install-offline.py`（协议本体脚本，落在 SELF-GATE 监管的 `agate/` 内）；本批未 commit，SELF-GATE 提示 / self-gate-review 由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 未动。

## 批 C1-release-cli

**改动文件**：`agate/scripts/agate-release.py`（新增，stdlib-only；入口顶部 `sys.dont_write_bytecode = True` 先于 `import agate_package`；`agate_common` 仅在 build 内延迟导入）。子命令 `boundary` / `pyyaml-pin` / `notes` / `is-prerelease` / `build`；库函数 `extract_notes(text, tag, wheels=None)`。构建流程：先在 `mkdtemp` 暂存目录构建（本体 tar 经 `list_package`→`materialize`→`write_dir_tarball`；offline 经 `python -B agate-pack-offline.py` 子进程 + `write_dir_tarball(arc_prefix=...)`；`SHA256SUMS` 排序、哈希走 `agate_common.compute_sha256`），全部成功才落到 outdir（失败不留半成品）；`--expect-sha` 两侧 `^{commit}` 剥壳；notes 取自 tag 内的 CHANGELOG，缺段 fail-closed 且先于任何产物写入；outdir 已存在且非空 / `--notes-out` 落在 outdir 内则拒绝。

**tests_filter**：`python3 -m pytest agate/tests/unit/test_agate_release.py agate/tests/integration/test_install_three_paths.py -q -k "not all_three_paths_produce_same_structure_including_portable"` → 51 通过 / 1 失败 / 1 deselected。唯一失败 `test_install_three_paths.py::test_t15_real_tree_smoke_pack_install_resolve`：该用例读**已提交** HEAD（HEAD 尚无 `agate_package.py`，bundle 内旧 `install-offline.py` 报 checksum 失败），需提交后转绿（P5 复核）；非本批实现问题。附加：`test_agate_package.py` / `test_agate_pack_offline.py` / `test_install_offline.py` 201 通过；`ruff check agate/` 通过。

**真实构建冒烟**：`agate-release.py build --tag v0.72.0 --repo . --outdir <scratchpad>/c1-smoke-1/dist --notes-out <scratchpad>/c1-smoke-1/notes.md --skip-offline` rc=0，产出仅本体 tar + `SHA256SUMS`（`sha256sum -c` 通过），notes 有下载/完整性头部；产物全部在 scratchpad，仓库无遗留文件。

**标注**：无 `[TEST_BUG]` / `[DESIGN_GAP]` / `[SCOPE+]`。scripts/README.md 登记由 F2 批负责（本批不改）。

**SELF-GATE 触发说明**：新增 `agate/scripts/agate-release.py`（协议本体脚本，落在 SELF-GATE 监管的 `agate/` 内）；本批未 commit，SELF-GATE 提示由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 未动。

## 批 C2-release-workflow

**改动文件**：`.github/workflows/release.yml`（新增，按 P2 §3.6 草案落成）。`on.push.tags: ['v*']` 唯一触发；顶层 `permissions: {contents: write}`；`concurrency.group: release-${{ github.ref_name }}`（cancel-in-progress false）；单 job（ubuntu-latest，timeout 20 分钟），`TAG` 经 job 级 env 传入；4 个步骤 Clone tag / Python deps（pyyaml-pin + `--only-binary=:all:`）/ Build assets（`agate-release.py build --expect-sha "$GITHUB_SHA"`）/ Publish（`GH_TOKEN` 仅此步骤 env；`is-prerelease` 的 rc 走 `case` 三分支，exit 2 及其它显式失败；`gh release create --verify-tag --notes-file`，预发布加 `--prerelease`）；零 `uses:`、无 `secrets.` 引用、所有 `run:` 不含 `${{`。现有 4 个 workflow 文件零改动。

**tests_filter**：`python3 -m pytest agate/tests/unit/test_release_workflow.py -q` → 12 通过 / 0 失败；`yaml.safe_load` 自检通过（`on` 解析为 `{'push': {'tags': ['v*']}}`）。

**未做**：未推 tag、未触发真实 CI、未创建 Release（BDD-20 真实实跑属 P5/P6，需另行获得用户许可）；未跑 actionlint（属 P5 降级路径）。

**标注**：无 `[TEST_BUG]` / `[DESIGN_GAP]` / `[SCOPE+]`。

**SELF-GATE 触发说明**：本批仅新增 `.github/workflows/release.yml`，不在 `agate/` 协议本体内，不触发 SELF-GATE 监管路径；未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py。本批未 commit。

## 批 F1a-docs-upgrading

**改动文件**：`agate/UPGRADING.md`、`CHANGELOG.md`（仅此二文件；未碰 F2 的 README / SETUP / AGENTS / WORKFLOW / adr 等）。
- `UPGRADING.md`：生命周期节新增 `### 版本目录结构契约`（结构树 (a)–(d)、顶层条目集合 + 未登记即违约、目录名固定、单一来源 `agate/scripts/agate_package.py`、`boundary_lines()` 渲染的 fenced 边界块、安装态 vs 运行后态 `__pycache__`、不支持并发安装）与 `### portable 安装（Release tarball，无需 git）`（命令块即验收脚本，含软链守卫 / `sha256sum -c` / `tar -xzf` / `python3 -B ... --adopt` / `--check --portable`；`-B` 原因、依赖 python3+pyyaml、无需 git 但 agate-changes.py 等不可用、SHA256SUMS 完整性局限、Source code=整仓提示；不含"零依赖"类措辞）；对照表改单布局（去 legacy 列，"迁移"行三步，更新统一 `agate-install.py latest`）；解析优先级表 5→3 层（删第 5 行，`五层`→`三层`）；订正"整仓形态协议根为 `<版本目录>/`"一句（按 `_protocol_root` 真实探测序改写）；§1 / 核心原则的升级命令由 `git pull` 改为 `agate-install.py latest`；v0.50.0 节三处红线承诺（原 `:809` `:810` `:841`）改写为"legacy 已移除（v0.73.0 BREAKING）+ 指向迁移指引"，其余历史节原文未动（`:825` 行含 `legacy 软链兜底` 措辞，测试只允许改 `单软链|legacy 兜底` 行，故保留）；§3 顶部加历史注记；新增 `### v0.73.0` 节（BREAKING、影响面、迁移三步、解析链 5→3、`install.sh` 无参语义、废弃 env、本体包形态、Release + portable、两步升级 R-1、钉老版本副作用 eng m-5、tests 不入包）。
- `CHANGELOG.md`：`[Unreleased]` 补 BREAKING 条目（含 UPGRADING 指针）+ 新增 / 变更条目；版本段重命名留 P8。

**tests_filter**（`PYTHONDONTWRITEBYTECODE=1`）：`python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py agate/tests/unit/test_upgrading_contract_doc.py agate/tests/integration/test_install_three_paths.py agate/tests/integration/test_portable_no_git.py -q` → **36 passed / 1 failed**。唯一失败 `test_install_three_paths.py::test_t15_real_tree_smoke_pack_install_resolve`（"checksum 校验失败: agate"）：该用例从真实仓库 **HEAD 提交**打包，bundle 内自带的 `install-offline.py` / `agate_common.py` 是 HEAD 的旧版（代码批 A–E 尚未 commit，旧 `compute_sha256` 不忽略字节码），非文档面问题；代码批 commit 后应转绿（需主 Agent 在批 commit 后复跑确认）。`test_portable_no_git.py` 全绿（文档命令块在无 git PATH 下逐条实跑通过）、`test_install_three_paths.py` 其余含 H3 portable 同构用例全绿。
附加自查：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → 0 ERROR（367 WARNING，既有）；`test_agate_version_install.py`（含 BDD-35 迁移三步跨入口一致）/ `test_check_changelog.py` / `test_agate_changelog_unreleased.py` / `test_mvwu_protocol_docs.py` 全绿。同扫时的其它红灯均属 F2 / 其他批（`test_no_legacy_residue.py` BDD-37 ①②④：`test_agate_version_resolve.py` / `test_hook_resolve_entry.py` / `test_install_sh.py`；`test_doc_sweep.py` BDD-40：`test_agate_summary.py`），与本批两文件无关。

**标注**：无 `[TEST_BUG]` / `[DESIGN_GAP]` / `[SCOPE+]`。

**SELF-GATE 触发说明**：`agate/UPGRADING.md` 位于 `agate/` 协议本体内（SELF-GATE 监管路径）；本批未 commit，SELF-GATE 提示由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 未动。仓库内无新增临时 / 备份文件。

## 批 F2-docs-sweep

**改动文件**（均为文档 / 注释，无代码行为改动）：`README.md`、`README.zh-CN.md`（步骤 1 首推 `curl | bash` 并注明进入版本管理布局、无参 = `--versions`、软链 fail-closed 指向 UPGRADING v0.73.0 节）；`agate/SETUP.md`（前置说明 + `$AGATE_DIR="$HOME/.agate/current/agate"` 去 fallback、`current` 缺失明确失败提示、布局表整表删除、DSH 节 / `agate_root` 默认值 / 更新口径去旧称）；根 `AGENTS.md`（`:62` 历史句去旧称；版本发布清单增 5a Release 校验：`gh release view` + 3 个 tarball 资产 + `SHA256SUMS`、tag 已推而 Release 缺失的本地补救（`agate-release.py build` + `gh release create`，因无 `workflow_dispatch`）、tag Ruleset 建议；G-5 条目含 Release 存在性）；`agate/AGENTS.md`（`:4` 改写、卸载节去旧布局、`tests/README.md` 引用加"仅仓库开发者可用"注记，S-1）；`agate/CONTEXT.md`（同注记）；`agate/WORKFLOW.md:41`；`agate/adr.md`（ADR-009 状态节加"v0.73.0 部分被取代"注记，旧叙述保留；`:431` 补指针）；`agate/orchestrator-template.md:20`（兜底改 `~/.agate/current/agate`）；`agate/assets/templates/handoff-template.md:37`（`$AGATE_DIR`）；`agate/platform-notes.md:250`（去旧称）；`agate/scripts/README.md`（登记 `agate_package.py`、`agate-release.py` 两行，去 resolve / resolve-entry 行的 legacy 兜底表述）；`docs/guides/project-map.md`、`docs/guides/worktree-dogfooding-guide.md`（去旧称、`$AGATE_DIR` 去 fallback、REASON 三层）；两处既有测试的注释 / docstring 清理（BDD-39 ⑧）：`agate/tests/unit/test_agate_version_resolve.py`（头注 + `test_resolve_terminal_failure_fail_closed` docstring + `:351` 优先级注释，仅文本）、`agate/tests/unit/test_dsh_preset.py:222` 注释。未碰 `agate/UPGRADING.md`、`CHANGELOG.md`（F1a）。

**BDD-38 的 4 个真 legacy 测试**：批 E / P3 已处置——`test_bdd_30_legacy_symlink_direct_root`、`test_debt0042_agate_home_legacy_symlink` 已改写为 fail-closed 断言（现存于 `test_agate_version_resolve.py`，docstring 记录改写来源）；`test_tag0032_bdd_1_*` / `bdd_2_*` 保留。本批**未删除任何文件、未改动任何撞名 `bdd_30` 测试函数体**。

**测试计数文档同步**：`bash agate/tests/scripts/count-tests.sh` = 2294（pytest collect-only 口径）；扫描 README / AGENTS / tests/README / CONTEXT / platform-notes / docs/guides 无硬编码用例总数，无需同步。

**tests_filter**：`python3 -m pytest agate/tests/unit/test_doc_sweep.py agate/tests/regression/test_no_legacy_residue.py agate/tests/unit/test_setup_agate_dir.py agate/tests/regression/test_tag0037_out_of_scope_untouched.py -q` → 62 通过 / 0 失败（初跑 58 / 4，4 个失败为 P3 测试文件自身违反 BDD-37 / BDD-40 grep 口径，已按授权修复，见下）。附带自查：`test_agate_version_resolve.py` + `test_dsh_preset.py` 与上述四文件合跑通过（修复后）；`check-protocol-consistency.py --strict-errors-only` 0 ERROR（367 个既有叙事 WARNING）；`ruff check agate/` 通过。

**标注（TEST_BUG 已由主 Agent 授权修复）**：P3 测试文件自身违反 BDD-37 / BDD-40 grep 口径的 4 处，`fixed by orchestrator authorization`（纯文本改动，断言语义不变，未动白名单与 BDD-37 逻辑）：
- `agate/tests/unit/test_agate_version_resolve.py`：BDD-28 用例内 `use_legacy` 改为运行时拼接 `removed_param = "use_" + "legacy"`（两处 assert 语义不变）；`:534` 注释改述；**函数名字面量含该旧称无法拼接，故重命名** `test_bdd_28_use_legacy_is_gone_…` → `test_bdd_28_legacy_switch_param_is_gone_and_no_symlink_target_as_root_branch`（P3-test-cases.md 若按名引用该用例需主 Agent 同步）。
- `agate/tests/unit/test_install_sh.py`：头注 / assert 消息 / docstring 中的旧称改为等义表述。
- `agate/tests/unit/test_hook_resolve_entry.py`：`:309` docstring 旧称改述。
- `agate/tests/unit/test_agate_summary.py`：新增模块常量 `_STALE_ENTRY = "~/.agate/" + "AGENTS.md"`，两处 `not in` 断言改用它；docstring 改述。
- 复跑：tests_filter 四文件 62 通过 / 0 失败；主 Agent 指定的六文件命令（residue / doc_sweep / version_resolve / install_sh / hook_resolve_entry / agate_summary）131 通过 / 0 失败；ruff 通过。无 `[DESIGN_GAP]` / `[SCOPE+]`。

**SELF-GATE 触发说明**：改动落在 `agate/` 协议本体文档（SETUP / AGENTS / CONTEXT / WORKFLOW / adr / orchestrator-template / handoff-template / platform-notes / scripts/README）与两个既有测试的注释，属 SELF-GATE 监管路径；本批未 commit，SELF-GATE 提示由主 Agent 在批次 commit 时按 AGENTS.md 处理。未改 hook 三件套 / SELF-GATE / .state.yaml schema / rules/*.yaml / install-hook.py，`_protocol_root` 未动。CODE-MAP：`agate/scripts/README.md` 已登记两新增脚本（回应批 A 核对表中"由 F2 统一登记"的备注）。

## 新增文件核对表

P2-skeleton.md 未采用；`agate-workspace/agents/CODE-MAP.md` 存在（机制已采用）。各批各自追加自己的新增文件行：

| 新增文件路径 | 骨架归属 | CODE-MAP 处理 |
|------------|---------|--------------|
| agate/scripts/agate_package.py | within agate/scripts（P2 §3.2 指定目录；无骨架文件） | [CODE_MAP_EXEMPT: 本批"只改本批文件"约束未含 CODE-MAP.md；CODE-MAP 的 scripts 段为家族级描述、不逐文件登记，新增脚本的索引由 F2 批统一登记，请 P7 核对] |

## 修复批 t17-fixture-fix

- 缺陷：GitHub runner（git 2.55.0）上 `git fast-import` 写树时拒绝含 `.git` / `..` 分量的路径（`fatal: invalid path 'agate/.git/config'`），使 T-17 的 5 个用例（dot-git-dir / dot-GIT-uppercase / dot-GiT-mixed-file / dotdot-segment / outside-package-region）在夹具构造阶段失败；本机 git 2.43.0 不拒绝故本地全绿。
- 改动（仅测试夹具）：`agate/tests/helpers_tag_repo.py` 的 `build_bare_repo` 在任一 spec 含危险分量（`.git` 大小写不敏感 / `.` / `..` / 空分量）时改走新增的 `_plumbing_import`（手工序列化 tree 字节 → `git hash-object -w -t tree --literally --stdin`，commit / annotated tag 同样 `hash-object --literally`，再 `update-ref`）；fast-import 失败时同样回落到该路径；其余用例仍走 fast-import。`agate_package.py` 与断言未改。
- 论证：`hash-object --literally` 明确用于写入"可能不满足 fsck 的畸形对象"，不经路径校验，且 `update-ref` / `ls-tree` / `cat-file` 只处理对象字节，不校验树内路径分量，故对新版 git 同样可构造恶意树；在 2.43.0 上验证 plumbing 生成的 tree sha 与 fast-import 对默认 spec 逐 tag 完全一致。
- 验证（本机 git 2.43.0）：test_agate_package.py 129 passed；引用 helpers_tag_repo 的全部测试文件 485 passed；ruff、check-platform-assumptions（0 命中）、test_agate_scripts_encoding 均通过。
