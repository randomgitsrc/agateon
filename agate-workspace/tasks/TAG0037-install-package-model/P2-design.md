---
phase: P2
task_id: TAG0037
type: design
parent: P1-requirements.md
trace_id: TAG0037-P2-20260920
status: draft
created: '2026-09-20'
candidate_count: 3
packages:
- agate-scripts
- agate-docs
- agate-tests
- ci-workflows
- install-sh
domains:
- backend
- security
ui_affected: false
agent: architect
dispatch_plan: {mode: serial, parallel_limit: 3, batches: [{id: A-package-lib, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_agate_package.py -q"}, {id: B1a-online-install-core, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_agate_version_install.py agate/tests/unit/test_agate_install_uninstall.py -q"}, {id: E-legacy-removal-code, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_agate_version_resolve.py agate/tests/unit/test_agate_summary.py agate/tests/unit/test_install_sh.py agate/tests/regression/test_protocol_root_dual_impl.py -q"}, {id: B1b-adopt-check, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_agate_install_adopt.py -q"}, {id: B2-offline-pack-install, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_install_offline.py agate/tests/unit/test_agate_pack_offline.py agate/tests/regression/test_offline_bundle_roundtrip.py -q"}, {id: C1-release-cli, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_agate_release.py agate/tests/integration/test_install_three_paths.py -q"}, {id: C2-release-workflow, complexity: low, tests_filter: "python3 -m pytest agate/tests/unit/test_release_workflow.py -q"}, {id: F1a-docs-upgrading, complexity: medium, tests_filter: "python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py agate/tests/unit/test_upgrading_contract_doc.py -q"}, {id: F2-docs-sweep, complexity: low, tests_filter: "python3 -m pytest agate/tests/regression/test_no_legacy_residue.py agate/tests/unit/test_setup_agate_dir.py -q"}]}
---
# P2-design — TAG0037 安装与多版本模型统一（RM-AG0066）

[PROD_NOT_TOUCHED]

> 上游：`P1-requirements.md`（52 条 BDD，approved；§7 S-1…S-19 已被用户采纳为基线）、`P0-brief.md`、`HANDOFF-TAG0037.md`、`docs/design-notes/design-rename-execution.md` §8.1。
> 本文件只产出**方案设计 + 实现导航**（不含步骤脚本）。所有实测在 scratchpad（对本仓库 `git clone` 的副本 + 合成仓库）内完成，未触碰真实 `~/.agate`、未 `git commit`。
> **重试 #1（评审 eng 1 BLOCKER + 5 MAJOR、cso 1 HIGH + 6 MEDIUM）**：已逐条处置，见 §14「评审处置表」；新增实验记录见 §10 E-9…E-19（scratchpad `exp-1`…`exp-5`）。

## 0. 一页摘要（决策清单）

| # | 决策 | 一句话理由 |
|---|------|-----------|
| D-1 | 本体边界机制 = **显式规则常量 + 自写构建器（git plumbing：`ls-tree -r -z` + `cat-file --batch`）**，落在新增 stdlib-only 模块 `agate/scripts/agate_package.py` | 选择理由三点（实测，§2）：① 老 tag 缺登记根文件时 `git archive` 整条命令 fatal；② F_pkg 必须在纯函数层可判定（`ls-tree` 不接受 exclude magic）；③ 确定性打包 + blob 字节一致（`export-ignore` 另会掏空 GitHub 源码包、对无属性的老 tag 失效）。EOL 转换中「仅 autocrlf」一支可用 `-c core.autocrlf=false` 缓解，树内 `eol` 属性一支无解 |
| D-2 | **构建入口只有一份**：`agate_package.materialize(repo, ref, dest)`（git → 目录）+ `agate_package.write_dir_tarball(dir, out, mtime)`（目录 → 确定性 tar.gz）。在线安装 / `agate-pack-offline` / Release workflow 三处都调它们，workflow 内**零打包逻辑** | TAG0031 hash 双实现教训；BDD-3、约束 5 |
| D-3 | 新增 CLI `agate/scripts/agate-release.py`（子命令 `boundary` / `notes` / `is-prerelease` / `build`），workflow 只调用它 | notes 提取（BDD-14）与本地打包入口（BDD-15/20）需在无 CI 下可测 |
| D-4 | `agate-install.py` 新增 `--adopt vX.Y.Z`（校验版本目录 → 写 `latest`/`current→latest` + 同步根 `scripts/`，不碰 git）；**执行主体 = 调用方同目录的兄弟安装器**（`install-offline` 用自己所在目录的 `agate-install.py`，不用被装版本自带的）；portable 文档步骤复用它 | 指针 / 根 scripts 逻辑只有一份；bundle 版本与安装器版本解耦（eng M-2）；Windows 文本指针自动正确；portable 全程无 git |
| D-5 | 离线 bundle 顶层 = `agate/`（**本体目录内容**，非整仓）+ 登记根文件 + `wheels/` + `manifest.json`；manifest 新增 `files`（包集合 P 的相对路径清单）。`install-offline` 只拷 manifest `files` 所列且与磁盘对账一致的文件，绝不拷 `wheels/`、`manifest.json`、`python/` 及未登记文件 | BDD-4 ①、BDD-9/11/12；cso F-4/F-6（路径名纳入校验、P 集合对账） |
| D-6 | `install-offline` 对已存在的 `vX.Y.Z/` **替换**：带标记的工作容器内构建 → pip → 换位（旧目录移入带标记的备份容器）→ `--adopt` 成功后才删备份，任一步失败则回滚（还原备份**与 `latest`/`current` 指针**）；在线路径保持"已存在即跳过" | S-16：受损旧安装"重装即恢复"；eng m-4 / N-2、cso F-5：任何时刻"旧版完整或新版完整"，指针与目录一致 |
| D-7 | 契约不登记任何隐藏元数据：**删除** `.installed-version`（全仓无读取方）与 `install-offline` 写的 `dest/.agate-root`（无读取方）；嵌入式 `python/` 不再落入 `vX.Y.Z/` | BDD-1/2/4 的「顶层集合逐一相等」 |
| D-8 | legacy 删除 = `_resolve_version_info` **不再特判软链**；软链基址走普通 env→声明→current 链，终态失败时若基址是软链则附迁移提示。BDD-51（软链指向完整版本根）因此天然放行 | 删一个分支比"加分支再删分支"更少代码；BDD-27/28/51 同一机制 |
| D-9 | `install.sh`：无参 = `--versions` 别名；软链守卫前置；废弃 env 打 WARNING（仅此三项；**不**对已有 `repo/` 做 `git pull`，主 Agent 裁决范围锁定） | P0-brief 范围锁定；升级自举缺口仅以文档覆盖（§1.3 R-1、§13 backlog 建议） |
| D-10 | Release workflow：`on.push.tags: v*`、`permissions: contents: write`（唯一）、零 action、`git clone` 取源、`gh release create --verify-tag` | S-10；`github.token` 而非 `secrets.*`（BDD-13 ③） |
| D-11 | 采纳 S-11：Release 附 `SHA256SUMS`，打包确定性（固定 mtime = tag 提交时间、排序、uid/gid 归零、gzip 无时间戳） | 主 Agent 裁决 C-1：4 个资产，口径见 §4 / §6 |
| D-12 | `--check --portable`（opt-in）：必需项 = python3 + pyyaml；git / bash 降为提示 | S-12；BDD-19 只声明两项依赖 |
| D-13 | **字节码策略**：`agate-install.py` / `install-offline.py` / `agate-pack-offline.py` / `agate-release.py` 入口最顶部（先于任何 `import agate_*`）设 `sys.dont_write_bytecode = True`；子进程一律 `[sys.executable, "-B", …]` 并设 `PYTHONDONTWRITEBYTECODE=1`；拷贝一律忽略 `__pycache__` / `*.pyc` / `*.pyo`（复用 `agate_package.EXCLUDE_*`，不写第二套）；`compute_sha256` 目录分支跳过字节码（共享单实现）；`verify_dir` 与三路径比较口径**忽略字节码**；portable 文档命令用 `python3 -B` | eng B-1（实测 X-1/X-2 + 本轮 E-9…E-11：字节码使目录哈希变化、checksum 误报） |
| D-14 | **软链基址守卫规范化**：`agate_package.normalize_home()` 统一去尾 `/`、`/.`、多余斜杠与文本 `..`，并检测"物理解析与文本解析不一致"（经软链的 `..`）；`agate_home()` 返回规范化路径；三处 Python 入口（`agate-install`、`install-offline`、`agate_common`）与 `install.sh`（shell 等价实现，含 `..` 分量拒绝）都在**规范化后**判 `islink` | cso F-1（HIGH）：本轮 E-12 复现 `os.path.islink("link/")` 为 False 的绕过并验证修复 |
| D-15 | Release 加固：`GH_TOKEN` 只在 Publish 步骤 `env`；`pyyaml` 用 `agate_package.PYYAML_PIN`（当前 `6.0.3`）固定并 `--only-binary=:all:`，workflow 与 `agate-pack-offline` 同源取值；`build --expect-sha "$GITHUB_SHA"` 校验 tag 未被移动；`is-prerelease` 的 exit 2 显式失败；notes 与文档如实标注 SHA256SUMS 只防损坏、不防发布者被攻破 | cso F-2/F-3/F-4/F-10 |
| D-16 | 包成员与路径硬化：`list_package` 额外拒绝 `.git`/`.gitmodules` 分量（大小写不敏感）、含 `:`、以空格或 `.` 结尾的分量、控制字符、仅大小写不同的冲突路径；`agate/` 下 `tests` 目录排除按 `casefold` 比较；`materialize`/`copy_files` 以 `O_EXCL|O_NOFOLLOW` 逐文件创建 | cso F-11；本轮 E-13：69 个真实 tag、7127 个包内文件 0 违规，不误伤 |

主 Agent 裁决已纳入（详见 §13）：**C-1 已采纳**——Release 共 4 个资产（3 个 tarball + `SHA256SUMS`），BDD-13 ⑤ / 20 ② / 21 / 50 ⑥ 读作"至少这 3 个 tarball 名 ∈ 资产集合，另有 `SHA256SUMS`"，不改 P1；**升级自举缺口不作代码改动**，仅 UPGRADING 文档覆盖，"install.sh 重跑时拉取 `repo/`"列 backlog 建议；**C-2 已采纳**为 P3 提示。评审处置总表见 §14。

---

## 1. 影响面梳理（Modify / Not Modify / Risk）

> 依据：读过的消费方代码 + grep 命中（承接 P1 §5 扫描 A–J，关键命中已重跑核验）。核验记录：`use_legacy` 仅 `agate_common.py:182/219/231/243` 四行代码命中（与 P1 一致）；`AGATE_REPO_DIR|AGATE_SYMLINK` 活跃命中仅 `install.sh` + 两个测试文件（其余为 CHANGELOG / 历史文档）；`git worktree add|remove` 在 `agate/scripts` 下仅 `agate-install.py`、`agate-pack-offline.py`（+ scripts/README 说明）；`.installed-version` 仅 `install-offline.py` 与 3 处测试；`dest/.agate-root` 无读取方（`resolve_hook_root` 读的是 hook 脚本旁的同名标记，位置不同）；v0.72.0 tag 包区树内 **0 个软链 / 0 个 submodule**（341 个 100644 + 29 个 100755）。

### 1.1 Modify（改什么）

| 文件 | 落点（函数 / 小节） | 关联 BDD |
|------|--------------------|----------|
| `agate/scripts/agate_package.py`（**新增**，stdlib-only） | 规则常量 `PKG_DIR` / `ROOT_FILES` / `EXCLUDE_*` / `PYYAML_PIN`；`is_packaged` `list_package` `materialize` `copy_files` `write_dir_tarball` `verify_dir` `boundary_lines` `parse_release_ref` `is_strict_version` `normalize_home` `is_symlink_base` `agate_home` `commit_mtime` `swap_in` `rollback_swap` `discard_backup` `sweep_stale` | 1 2 3 4 15 22 23 24 31 32 33 |
| `agate/scripts/agate-install.py` | 入口顶部 `sys.dont_write_bytecode = True`；删 `_worktree_add`；`_install_version` 改 `mkdtemp` 构建 + `os.rename`；`_ensure_repo` 的 `git clone` 加 `--`；新增 `_register`（指针 + 根 scripts，`copytree` 忽略字节码且 `symlinks=True`）、`_cmd_adopt`（软链守卫 → `verify_dir`（新形态）→ 注册；`OSError` 转 stderr + exit 1）、`_cmd_check(portable)`；`_LEGACY_SYMLINK_MSG` 重命名并改文案（含 BDD-51 附句 + 动态"检测到的软链"行）；`_cmd_uninstall` 旧形态才 `worktree remove`，`repo/` 存在即 `worktree prune`；`_VERSION_RE` 改 `fullmatch` 口径；`_agate_home` 委托 `agate_package.agate_home()`；`_usage` / `main` 增 `--adopt`、`--check --portable`；`_protocol_root` 降级副本**不改** | 4 8 17 18 22 24 25 26 31 32 51 |
| `agate/scripts/agate-pack-offline.py` | 入口顶部 `sys.dont_write_bytecode = True`；`pack_offline`：以 `agate_package.list_package` + `materialize` 取代 `git worktree add`；新增 `ref` 形参（预发布 tag）；manifest 增登记根文件组件、`files` 清单与 `source_ref`；pyyaml 用 `PYYAML_PIN` 且 wheel 查找大小写无关（实测 6.0.2 的文件名是大写 `PyYAML-…`，现 `glob("pyyaml-*")` 会漏）；`_DEFAULT_REPO` 改 `_default_repo()`（读 `AGATE_HOME`）；CLI 增 `--ref` | 9 10 11 15 16 20 |
| `agate/scripts/install-offline.py` | 入口顶部 `sys.dont_write_bytecode = True`（先于 `import agate_common`）；`_DEFAULT_DEST` 改运行时 `agate_package.agate_home()`；`main` 增规范化后软链守卫；新增 `_check_bundle_layout`（旧格式拒绝 / 缺本体 / `lstat` 成员安全 / manifest `files` 对账）；`install_bundle` 重写为「`copy_files` 到 `mkdtemp` → pip → `swap_in` → 同目录兄弟 `agate-install.py --adopt`（`-B`）→ 成功后 `discard_backup`，失败 `rollback_swap`」；`_validate_manifest` 版本校验改 `parse_release_ref`；报错文案"不一致（损坏或被替换）"；删 `.installed-version`、`.agate-root`、`current` 直指逻辑、`_copy_tree.exclude_names` | 4 9 10 12 16 33 |
| `agate/scripts/agate-release.py`（**新增**） | 入口顶部 `sys.dont_write_bytecode = True`；`boundary` / `notes`（`extract_notes`，头部含完整性局限说明与 offline wheel 清单）/ `is-prerelease` / `pyyaml-pin` / `build`（`--expect-sha`；本体 tar + 每平台 offline tar + `SHA256SUMS` + notes 文件） | 13 14 15 16 20 21 |
| `.github/workflows/release.yml`（**新增**） | 触发 / 权限 / 步骤（§3.6） | 13 20 21 |
| `agate/scripts/agate_common.py` | `_resolve_version_info`：删 `use_legacy` 参数（`:182`）、删软链兜底分支（`:219-220`）、返回 dict 增 `symlink_base`（**含 `AGATE_ROOT` env 早返回分支**，默认 False）；基址取 `agate_package.agate_home()`（单源，规范化）；`resolve_version_root`（`:231`）与 `resolve_hook_root`（`:243` 仅去掉 `use_legacy=False` 实参）；新增 `symlink_migration_hint()`；`compute_sha256` 目录分支跳过 `__pycache__` / `*.pyc` / `*.pyo`（复用 `agate_package.EXCLUDE_*`）；`_protocol_root` **零改动** | 6 27 28 34 46 47 51 |
| `agate/scripts/agate-resolve.py` | 头注 `legacy` 表述；终态失败分支附迁移提示 | 27 28 35 |
| `agate/scripts/agate-summary.py` | 协议入口路径取 `{AGATE_ROOT}/AGENTS.md`；`changelog_hint` 去 legacy 注释；软链基址时输出迁移提示行 | 34 40 |
| `install.sh` | 重写（§3.7）：删无参软链分支与 `INSTALL_DIR/LINK_*`；无参 = `--versions` 别名；`AGATE_HOME` 规范化（去尾 `/` `/.`、拒绝 `..` 分量）后软链守卫前置；动态"检测到的软链"行；废弃 env WARNING（不含 `git pull`）；`git clone` 加 `--` | 26 29 30 31 35 36 |
| 文档面（P4 批 F1a / F2） | `agate/UPGRADING.md`（契约小节 / portable 小节 / 对照表去 legacy 列 / 解析表 5→3 层 / `:809` `:841` 红线改写 / `### v0.73.0` / §3 顶部注记）、`CHANGELOG.md`（`[Unreleased]` 写 BREAKING 条目）、`README.md`、`README.zh-CN.md`、`agate/SETUP.md`（`$AGATE_DIR`、布局表）、根 `AGENTS.md`（`:62` 历史句、版本发布清单增 Release 校验）、`agate/AGENTS.md`（`:4` `:104`）、`agate/WORKFLOW.md:41`、`agate/adr.md`、`agate/orchestrator-template.md:20`、`agate/assets/templates/handoff-template.md:37`、`agate/platform-notes.md:250`、`agate/CONTEXT.md` 与包内对 `agate/tests/README.md` 的引用加"仅仓库开发者可用"注记（S-1 代价）、`agate/scripts/README.md`（新增脚本索引 + 测试映射）、`docs/guides/project-map.md:114`、`docs/guides/worktree-dogfooding-guide.md` | 1 17 19 21 35 38 39 40 41 50 |
| 测试面（P3 写、P4 使其转绿） | 见 §6；**夹具助手**的拷贝清单须加入 `agate_package.py`（eng M-3 / N-1）：`test_agate_version_install.py::_tag_upstream`、`test_version_lifecycle_e2e.py::_tag_meta_upstream`，以及**所有把 `agate_common.py` 拷入合成目录的夹具**——因 `agate_common` 现 `from agate_package import agate_home`，漏拷即 `ModuleNotFoundError`：`test_hook_resolve_entry.py`（`:59` 处拷贝循环）、`test_pre_commit_hook.py`（`:1235`、`:1415` 两处）、`test_dispatch_context_warning.py`（`:17` 拷贝清单） | 全部 |

### 1.2 Not Modify（看似该改、决定不改）

| 范围 | 理由 |
|------|------|
| `agate_common._protocol_root`（`agate_common.py:166`） | 新契约形态 `vdir/agate/scripts` 就是既有探测序 2；不增第 3 序（S-16）。BDD-6 断言其函数体零 diff |
| `.gitattributes` | 未选 `export-ignore`（§2）；不加任何 attribute。BDD-15 ③ 也要求打包不受 attribute 影响 |
| hook 三件套、SELF-GATE（`SELF-GATE.md`、`commit-msg-self-gate.py`）、`.state.yaml` schema、`agate/rules/*.yaml`、`install-hook.py` | out-of-scope；BDD-46 零 diff。`resolve-entry.py` 也**不改**（连注释都不动，省去例外条款） |
| `install.sh` 对已有 `repo/` 的更新（`git pull`） | 主 Agent 裁决：超出 P0 范围锁定，不做；列 §13 backlog 建议 |
| `agate-install.py --uninstall` 不加软链守卫；`_sync_root_scripts` 的"恒同步被装版本的 scripts"语义（eng m-5：钉老版本会回退根 scripts） | 前者：卸载只删 `AGATE_HOME` 下版本目录，BDD-51 要求软链→完整版本根仍可用；后者：既有语义，超出范围锁定，仅在 UPGRADING v0.73.0 节写明并列 §13 backlog |
| `pip` 取自 `PATH`（改 `sys.executable -m pip`）、`install.sh` 的 `$SCRIPT_DIR` 回退（cso F-13 后两项） | 既有行为，范围锁定；且改 `pip` 调用方式会使 eng G-1/G-2 建议的 PATH-shim 测试手法失效；列 §13 backlog |
| `resolve_hook_root` 的脚本路径上溯 + `.agate-root` 恢复兜底 | S-17：hook 自定位契约，不属 legacy |
| `_resolve_pointer_chain`（`agate_common.py:124`）、`_write_pointer` / `_resolve_pointer` | 指针机制保留，与 legacy 无关（P1 扫描 D） |
| 现有 4 个 workflow（deploy-pages / docs-check / protocol-tests / site-check） | BDD-13 ⑥ 零 diff；连带触发行为只记录不修改 |
| `site/` 博客与首页文案 | 带日期历史文章不改；`curl \| bash` 命令仍有效（P1 扫描 G） |
| `agate-changes.py` 依赖 git 仓库、offline 固定 `--python-version 311`、`latest` 改从 Release asset 取包 | P1 扫描 I：既有缺陷 / 范围外，只在文档如实声明 |
| `agate-install.py` 的 `repo/` 全量 clone（59MB） | 用户决策 ②：保留 `repo/`；不做 partial clone 优化 |
| `pip download --python-version 311` 等 offline wheel 策略 | 范围外；Release notes 注明 |

### 1.3 Risk（风险 → 缓解）

| # | 风险 | 缓解 |
|---|------|------|
| R-1 | **升级自举缺口**：≤v0.72 的用户用旧安装器（`~/.agate/scripts/agate-install.py` 或 `repo/` 里克隆时的旧 HEAD）安装 v0.73.0 时，装出的 v0.73.0 是旧整仓形态（`git worktree add`）；`install.sh` 不更新 `repo/` 中的安装器 | **仅文档覆盖，不改代码**（主 Agent 裁决：P0 范围锁定，扩范围须用户确认）：UPGRADING v0.73.0 节写明——v0.72 用户用旧安装器升级时 v0.73.0 自身为旧整仓形态（仍可解析，BDD-5/7 保证），之后经同步后的根 `scripts/` 执行的安装均为只装本体；"install.sh 重跑时拉取 `repo/`"列 §13 backlog 建议 |
| R-2 | `_resolve_version_info` 返回 dict 新增 `symlink_base` 键，消费者是否有严格键集断言 | 已读消费者：`agate-resolve.py` / `agate-summary.py` / `resolve_hook_root` 均按键取值；P3 用 grep 核 `_resolve_version_info` / `resolve_version_root` 调用点 |
| R-3 | 双源同步：`agate-install.py` 内 `_protocol_root` 降级副本与 `agate_common` 权威实现 | 保留（`--check` 需 pyyaml 缺失时可运行）；BDD-8 五夹具一致性测试锁定。`agate_home()` 改为**单源** `agate_package.agate_home()`：`agate-install` 委托、`install-offline`/`pack` 直接用、`agate_common` 也 `from agate_package import agate_home`（eng m-3）；`test_debt0042_*` 继续锁定行为 |
| R-4 | 边界"默认拒绝"只到仓库根一层；`agate/` 内部是"默认放行、显式排除" | BDD-3 ② 明确要求 `agate/zz-new.md` 自动入包。加 tripwire 测试：真实 HEAD 上 `agate/` 顶层条目集合与已知集合逐一比对，新增子目录须有意识地入包或加排除（§6 T-7） |
| R-5 | 确定性只对同一 Python 主次版本成立（PAX 头随版本略有差异） | 只承诺"同 tag + 同 Python 次版本 → 同哈希"；BDD-20 ③ 判的是逐成员字节一致，不依赖整包哈希；offline 资产另含 pip 下载的 wheel（PyPI 上 pyyaml 版本漂移则哈希变），文档写明 |
| R-6 | workflow 首次真实运行发生在 v0.73.0 正式 tag（自引用限制） | BDD-20 合并前用 `v0.73.0-tagtest.1` 实跑（§11）；不许可时降级 + P8 后验；`actionlint` 本机未装，P5 需 `pip install actionlint-py` 或下载二进制 |
| R-7 | 供应链：`contents: write` 高危 | 触发仅 tag push；零 action；`GH_TOKEN` 只在 Publish 步骤 env（cso F-2）；tag 名经 `parse_release_ref`（`fullmatch` + ASCII）校验后才入文件名；`--verify-tag` + `--expect-sha`（cso F-3）；`pyyaml` 固定版本 + `--only-binary`；PR 描述如实列出触发 / 权限。**残余风险（已知并接受）**：PyPI 上被固定版本的 wheel 本身被替换（未启用 `--require-hashes`，列 §13 backlog）；有 tag 写权限者可触发发布（建议仓库启用 `v*` tag 保护，写入 AGENTS.md 发布清单） |
| R-8 | 临时 / 备份目录残留、预置符号链接诱导；**清理误删用户目录（cso N-1，数据安全）** | 工作 / 备份目录由本工具**专属命名 + 专属标记文件**识别：`agate_package.make_work_dir(root, ver)` = `tempfile.mkdtemp(prefix=".agate-tmp-<ver>-", dir=<版本根>)`（0700、`O_EXCL` 语义，名字以点开头且不匹配 `_VERSION_RE`），创建后立即在其中写入标记文件 `.agate-installer-owned`（内容 `agate-package/1 kind=tmp version=<ver> pid=<pid>`，`O_EXCL` 创建）；构建产物放在容器内的 `pkg/` 子目录，换位时 `rename(<容器>/pkg → vX.Y.Z)`，因此标记文件**不会**进入版本目录。**`sweep_stale` 绝不按目录名模式删除**：仅当条目同时满足 ① 名字以 `.agate-tmp-` 开头 ② `os.lstat` 为真实目录（非软链，不跟随）③ 其中标记文件为普通文件且首行等于 `agate-package/1 kind=tmp` ④ 标记 mtime 早于 1 小时（避开并发安装的活跃临时目录）时才 `rmtree` 该容器，其余一律不动；**永不触碰** `vX.Y.Z.bak-*`、`vX.Y.Z.tmp-*`、`.agate-tmp-*` 但无标记者、软链、以及任何用户目录。备份容器 `.agate-bak-<ver>-XXXX`（同样带标记 `kind=bak`，旧版本目录在其 `old/` 内）**不被 `sweep_stale` 删除**——它可能是崩溃后唯一完整的旧版本：`recover_backups(root)` 只做改名（`vX.Y.Z` 缺失时把 `old/` 挪回；否则仅 stderr 提示遗留备份路径，由用户确认后手动删除）；`discard_backup` 只在 adopt 成功后删除**本次进程自己创建**的备份容器（校验标记与路径）。**不支持并发安装同一版本根**（文档声明，未实现锁：单用户工具，跨平台文件锁复杂度不成比例） |
| R-9 | 离线 `--include-python` 语义变化（不再落入 `vX.Y.Z/python/`） | 嵌入式 Python 下载本就是半成品（Linux 侧下载的是 `.tgz` 源码包，不可直接运行）；bundle 内保留、安装时打印一行说明；P3 调整既有 `--skip-python` 用例 |
| R-10 | `AGATE_HOOK_COPY_MODE=1` 不再影响离线安装的 `current`（POSIX 下改为软链） | 该变量是 hook 复制模式概念，从未属于版本根指针；解析链两形态都支持；P3 调整既有 copy-mode 用例 |
| R-11 | 旧格式 bundle 拒绝（S-13）可能打断"手头已有旧包"的用户 | 已知实例 0；错误信息给出重打包命令 |
| R-12 | 冗余阈值 S ≤ 1.25×B 对真实仓库成立与否 | 已实测（§10 E-5）：B = 1,864,871 B，整 tag 36,976,767 B，本体包 5.0%；P5/P6 用真实 `agate-install.py` 复测 |
| R-13 | **运行即污染安装目录**（eng B-1）：从 `vX.Y.Z/agate/scripts/` 启动的 Python 会写 `__pycache__`，破坏目录哈希 / 三路径同构比较 / `verify_dir` | D-13：安装器自身不产生；拷贝与哈希忽略；比较口径显式忽略字节码；测试以 bundle 内入口执行并在"H2/H3 运行过 `agate-resolve.py` 之后"再比较一次（§6 T-4、T-15） |
| R-14 | 软链守卫被尾斜杠 / `/.` / 经软链的 `..` 绕过，导致覆盖源仓库文件（cso F-1） | D-14；§6 T-14 参数化 `["L", "L/", "L//", "L/.", "L/.."]` × 四入口，断言 exit 1 且源仓库文件哈希不变 |
| R-15 | 换位半装 / 悬空指针（cso F-5；eng N-2） | D-6：备份改名 + 回滚（目录**与指针**）；测试对每一步 `monkeypatch os.rename` 注入失败，断言"旧版完整或新版完整"且 `latest`/`current` 指针与回滚后的目录一致（§6 T-16）；pip 已装 wheel 不回滚（系统级、幂等，文档说明）；根 `scripts/` 覆盖同步不可回滚，故 `_register` 把它放在指针写入**之后**且失败仅 WARNING（既有行为），不影响 adopt 成败 |
| R-16 | SHA256SUMS / manifest 校验被误读为防篡改（cso F-4） | notes 头、UPGRADING portable / offline 小节、`install-offline` 报错文案如实标注"只防损坏、不认证发布者"；来源证明（sigstore / `gh attestation`）需 `id-token: write` 与官方 action，与"零 action / 唯一权限"冲突，列 backlog；manifest `files` 清单使路径名纳入校验（目录哈希不含路径名的局限由此弥补） |

---

## 2. 排除机制候选方案（含实测比对）

`candidate_count: 3`。实测环境：本仓库 `git clone` 到 scratchpad（68 tag，含 v0.72.0 / v0.48.0 / v0.8.0），git 2.43.0，Python 3.12.3，Linux（WSL2）。

### 候选 A：`.gitattributes` `export-ignore` + `git archive`

`/* export-ignore` 再 `/agate -export-ignore` 反向放行（`-` 取消属性）+ `/agate/tests export-ignore` + `__pycache__` / `*.pyc`。

- 优点：零新代码；属性随 tag 走。
- 实测硬伤（scratchpad 内提交了一份带属性的副本 tag 验证）：
  1. **掏空 GitHub 自动「Source code」包**：`git archive` 对带属性 tag 输出 153 个文件（tag 共跟踪 3390 个）——`export-ignore` 对所有 archive 消费者生效（GitHub 源码包基于同一语义；未在 GitHub 上实测，属 git 语义推断，但与 P0 known_risks 已写明的担忧一致）。会让 `docs/` `site/` 等对二次分发者不可见，并使 BDD-14 ③ 向用户声明的"Source code 为整仓"失真。
  2. **历史 tag 不生效**：v0.48.0 树内无该属性 → `git archive` 输出 1203 个文件（全量）。虽可经 `$GIT_DIR/info/attributes` 补救（实测得 111+3 个文件），但那要求安装器改写 `repo/.git/info/`——隐式全局副作用，且 `--worktree-attributes` 语义随版本变化。违反 BDD-24（老 tag 同样只装本体）。
  3. **EOL 转换**（与候选 B 共有）：见下。
  4. 无 git 环境：属性只能由 git 读取（构建期需要 git，消费期不需要，与 B/C 同）。

### 候选 B：`git archive <tag> -- <pathspec 白名单 + :(exclude)…>`

规则由单一来源生成 pathspec：`git archive v0.72.0 -- agate LICENSE NOTICES.md CHANGELOG.md ':(exclude)agate/tests' ':(exclude,glob)**/__pycache__/**' ':(exclude,glob)**/*.pyc'`。

- 优点：不依赖 tag 内配置（老 tag 同样适用）；默认拒绝天然成立（只列白名单）；不影响 GitHub 源码包；一次 fork 0.02s。实测 v0.72.0 得 153 个成员，与预期集合完全一致，且 `agate/tests` 命中 0。
- 实测硬伤：
  1. **EOL 转换破坏 BDD-15 ③**：合成仓库（`*.md text eol=crlf`）里 `git archive` 输出 CRLF 而 blob 是 LF；**仅 `core.autocrlf=true`（Windows 默认）**时也转成 CRLF（`GIT_CONFIG_COUNT` 强制配置复现）。**订正（eng m-2，本轮 E-14 复现）**：后一支可用 `git -c core.autocrlf=false archive` 关闭；**树内 `eol` 属性一支无法用命令行关闭**——本仓库 `.gitattributes` 现仅对 `*.sh/*.py/…` 设 `eol=lf`（不含 `*.md`），所以这是**潜在**而非当前的差异，但契约要求"打包不受任何 attribute 影响"，B 无法保证。
  2. **登记根文件缺失于历史 tag 时整条命令 fatal**：`git archive v0.8.0 -- NOTICES.md …` 报"路径规格未匹配任何文件"并整体失败（v0.8.0 无 NOTICES.md）。要容忍就得先 `ls-tree` 探测再拼命令——等于回到候选 C 的一半。
  3. F_pkg（文件集合）无法在不产出 tar 的情况下得到，BDD-2 / BDD-3 要在纯函数层判定集合；`ls-tree` 不接受 `exclude` magic。
  4. 输出带 `pax_global_header`（提交 SHA 注释）、mtime 取提交时间但 uid/mode 由 git 定（受 `tar.umask` 配置影响），确定性要再处理一遍。

### 候选 C（选定）：显式规则常量 + 自写构建器（git plumbing）

`git ls-tree -r -z --full-tree <ref>` 枚举 → 纯函数 `is_packaged(path)` 过滤 → `git cat-file --batch` 按 SHA 取 **原始 blob 字节** → 写目录 / 确定性 tar。规则常量在 `agate_package.py` 中，UPGRADING 契约小节由 `agate-release.py boundary` 生成并由单元测试锁等。

实测（原型 `proto_pkg.py`，scratchpad）：

| 项 | 结果 |
|----|------|
| 集合 | v0.72.0：153 文件，与候选 B 输出的成员集合逐一相同；v0.8.0（缺 NOTICES.md）：50 文件，缺失的登记根文件被容忍 |
| 字节 | 153 / 153 成员与 `git show v0.72.0:<path>` 字节相同；`GIT_CONFIG_COUNT` 强制 `core.autocrlf=true` + 仓库带 `eol=crlf` 属性下，输出仍是 LF blob（`git archive` 同条件下是 CRLF） |
| 体积 | B = 1,864,871 B（与 P1 T-1 基线一致）；tar.gz 647,370 B；整 tag 36,976,767 B（本体 = 5.0%） |
| 确定性 | 间隔 1s 连续构建两次 → SHA256 相同 |
| 速度 | v0.72.0 约 0.11s（`git archive` 0.02s，均可忽略） |
| 系统 tar | `tar -xzf … -C 空目录` 得 `agate/ CHANGELOG.md LICENSE NOTICES.md`，无包裹目录 |
| 无 git | 见 §10 E-6：把包解到目录、手建指针后，`agate-resolve.py` / `agate-summary.py` 在无 git 的 `PATH` 下 exit 0（本体包不含 tests 也正常） |
| 硬化扫描（本轮 E-13） | 对全部 69 个 tag 的包区跑 D-16 规则（`.git*` 分量 / `:` / 结尾空格或点 / 大小写冲突 / `Tests` 大小写变体）：7127 个包内文件，0 违规，不会误伤真实历史 tag；68 个 tag 上 mode 仅 100644 / 100755，无软链、无 submodule（与 eng X-5 一致） |

### 权衡比对矩阵

| 维度 | A export-ignore | B git archive + pathspec | **C 规则常量 + plumbing** |
|------|-----------------|--------------------------|---------------------------|
| 默认拒绝（S-6） | 可（`/*` + 反向放行），但靠属性优先级技巧，易被后续属性行破坏 | 可（白名单） | 可（`is_packaged` 仅放行 `agate/**` 与登记根文件） |
| 对其他 archive 消费者 | **有害**（GitHub 源码包被掏空） | 无 | 无 |
| 三路径单一来源（BDD-3） | 需另写逻辑读属性以支持老 tag | 三处各拼一次 pathspec，需共享生成函数 | 单函数 `materialize`，三处直接调用 |
| 机械可验证 | 需解析属性 | 集合需先产出 tar | 纯函数可直接断言集合；`verify_dir` 可验证已装目录 |
| 历史 tag（BDD-24） | **失败**（无属性） | 成立，但登记根文件缺失时 fatal | 成立，缺失文件容忍 |
| blob 字节一致（BDD-15 ③） | 失败（EOL 转换） | **失败**（EOL 转换，Windows 默认配置即触发） | 成立 |
| 确定性打包（S-11） | 需后处理 | 需后处理 | 自带（固定 mtime / 顺序 / 归零 owner） |
| Windows | 可 | 可，但 EOL 问题在此暴露最严重 | 可（二进制管道；exec 位在 Windows 上无意义，维护者应在 POSIX / CI 打包） |
| 无 git 环境 | 构建需 git | 构建需 git | 构建需 git；消费（portable）无需 git |
| 代码量 | 0 | ~30 行 | ~200 行（含校验与 tar 写入）+ 测试 |

**选择理由（重心，eng m-2）**：① 老 tag 缺登记根文件时 B 整条命令 fatal（要容忍就得先 `ls-tree` 探测，等于回到 C 的一半）；② BDD-2 / BDD-3 要求 F_pkg 在纯函数层可判定（`ls-tree` 不接受 exclude magic）；③ 确定性打包 + 不受树内 attribute 影响的 blob 字节一致。A 另有"掏空 GitHub 源码包 / 对无属性的老 tag 失效"两个硬伤。以下为原比较记录：A 与 B 分别在"影响 GitHub 源码包 / 老 tag 失效"与"EOL 转换致字节不一致"上有实测确认的硬伤，且都无法在纯函数层给出 F_pkg；C 多出的代码量换来 BDD-2/3/15/24 全部可直接单测。代价（Windows 维护者本地构建 exec 位丢失、~200 行新代码）已在风险表登记，且 CI 在 Linux 上构建。

> 稻草人检查：B 不是陪衬——若不追求 blob 字节一致与老 tag 缺文件容忍，B 是代码量最小的方案；它落选的理由来自实测而非偏好。

---

## 3. 选定方案设计

### 3.1 版本目录结构契约（子批 A 核心，权威源：`agate/UPGRADING.md` 新增 `### 版本目录结构契约` 小节）

```
~/.agate/                      # 版本根（AGATE_HOME 指向这一层）；必须是实体目录（不是软链）
├── vX.Y.Z/                    # 一个已安装版本；顶层条目集合固定（下）
│   ├── agate/                 # 本体，目录名固定 `agate/`（design-rename-execution.md §8.1），协议根
│   ├── CHANGELOG.md           # 登记根文件（agate-summary 会话启动探测 <root>/../CHANGELOG.md）
│   ├── LICENSE                # 登记根文件（MIT 要求所有副本带许可声明）
│   └── NOTICES.md             # 登记根文件（role-system.md 引用）
├── latest  → vX.Y.Z           # 指针（POSIX 软链 / Windows 文本指针）
├── current → latest           # 指针
├── scripts/                   # 根入口副本（agate-install 从版本协议根 scripts/ 同步）
└── repo/                      # 可选：仅在线安装存在（git 对象库，用于装任意历史 tag；离线 / portable 无）
```

- `vX.Y.Z/` 顶层条目集合 = {`agate/`} ∪ {`CHANGELOG.md` `LICENSE` `NOTICES.md`} ∪ 已登记隐藏元数据（**当前为空**）。未登记的顶层条目 = 违约（`verify_dir` 可机械判定）。
- **安装态与运行后态（eng B-1）**：契约约束的是"安装器交付的内容"。运行 `vdir/agate/scripts/*.py`（含 hook 正常运行）会由 Python 运行时写入 `__pycache__/*.pyc`，这不属违约：`verify_dir` 与全部\"文件集合比较\"（BDD-2 ④ / BDD-4 ①、T-4）**忽略 `__pycache__` 目录与 `*.pyc` / `*.pyo`**；安装器自身不产生字节码（D-13）。
- 包内路径规则（=`agate_package` 常量，`boundary_lines()` 渲染进 UPGRADING）：`include agate/`；`exclude agate/tests/`（大小写不敏感）；`exclude **/__pycache__/`；`exclude *.pyc *.pyo`；`root-file CHANGELOG.md LICENSE NOTICES.md`；其余一律不入包（README* / pyproject / SELF-GATE / 根 AGENTS.md / CLAUDE.md / install.sh / .gitignore / .gitattributes / HANDOFF-*.md / `.github` `site` `docs` `archived` `agate-workspace`）。
- 边界清单单一来源文件：`agate/scripts/agate_package.py`。UPGRADING 小节含一个 fenced 块（`boundary` 渲染结果）；单元测试断言"块内条目集合 == `boundary_lines()`"，且小节 grep `可配置|可扩展|manifest 声明` 无命中（BDD-1 (c)、BDD-3 ③）。
- **旧形态兼容**：已装 `vX.Y.Z/{agate,agate-workspace,docs,…}`（`git worktree` 整仓形态，含 `.git` 指针文件）仍由 `_protocol_root` 探测序 2 命中 `vdir/agate`；新旧共存靠 `.agate-version` 钉版或 `current` 指向（BDD-5/7）。不迁移、不归一化。
- 契约与 `_protocol_root` 的关系：新契约形态 = 既有探测序 2；`vdir/scripts` 优先于 `vdir/agate/scripts` 保持（BDD-6）。UPGRADING 现有"整仓形态下协议根为 `<版本目录>/`"一句（`:103`）与真实语义不符，一并订正。

### 3.2 `agate/scripts/agate_package.py`（批 A）

stdlib-only（不 import `agate_common`——后者模块级 `import yaml` 缺失即 `sys.exit(1)`，而 `agate-install.py --check`、`install-offline.py` 都要在 pyyaml 缺失时可运行）。Python 3.8+，文本 I/O 显式 UTF-8。**模块本身及所有入口脚本顶部先设 `sys.dont_write_bytecode = True`**（D-13）。

```python
PKG_DIR = "agate"
ROOT_FILES = ("CHANGELOG.md", "LICENSE", "NOTICES.md")   # 登记根文件（可缺失于历史 tag）
HIDDEN_METADATA = ()                                      # 登记的隐藏元数据
EXCLUDE_PKG_SUBDIRS = ("tests",)                          # agate/ 下整目录排除（casefold 比较）
EXCLUDE_DIR_NAMES = ("__pycache__",)                      # 任意层级
EXCLUDE_SUFFIXES = (".pyc", ".pyo")
TMP_PREFIX, BAK_PREFIX = ".agate-tmp-", ".agate-bak-"                       # 本工具专属目录前缀
MARKER_NAME = ".agate-installer-owned"                                  # 专属标记文件（首行 agate-package/1 kind=tmp|bak ...）
TOP_LEVEL = tuple(sorted((PKG_DIR, *ROOT_FILES, *HIDDEN_METADATA)))
VERSION_RE = re.compile(r"v[0-9]+\.[0-9]+\.[0-9]+", re.ASCII)                 # 一律 fullmatch
RELEASE_REF_RE = re.compile(r"(v[0-9]+\.[0-9]+\.[0-9]+)(?:-([0-9A-Za-z][0-9A-Za-z.-]*))?", re.ASCII)
PYYAML_PIN = "6.0.3"          # workflow 与 agate-pack-offline 同源取值（agate-release.py pyyaml-pin）

class PackageError(RuntimeError): ...
PackageEntry = namedtuple("PackageEntry", "path mode sha")

def is_packaged(relpath) -> bool          # 纯函数；默认拒绝：非 agate/** 且非 ROOT_FILES → False
def list_package(repo, ref) -> [PackageEntry]
    # ls-tree -r -z --full-tree；过滤、排序；校验：mode ∈ {100644,100755}（软链/submodule → PackageError）；
    # 路径：无 ".." / 空段 / 反斜杠 / 绝对路径 / 控制字符 / ":"；分量不得为 .git/.gitmodules（casefold）、
    # 不得以空格或 "." 结尾；casefold 后路径冲突 → PackageError；UTF-8 可解码；
    # 必须含 agate/scripts/（否则 PackageError，BDD-24 ②）
def materialize(repo, ref, dest, entries=None) -> [PackageEntry]
    # dest 必须是调用方刚 mkdtemp 出的空目录；cat-file --batch 取 blob 原始字节；逐条核对 header 类型 blob + size；
    # 逐文件 os.open(O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW(若有), 0o644/0o755)，目录 os.mkdir（不用 makedirs(exist_ok)）；
    # 越界（commonpath）检测；完成后 chmod(dest, 0o777 & ~umask)
def copy_files(src_root, relpaths, dest) -> None
    # 离线安装用：逐个 os.lstat(src)，非普通文件（软链 / 设备 / FIFO / socket）→ PackageError；
    # 同样 O_EXCL|O_NOFOLLOW 落盘；忽略 EXCLUDE_* 命中的字节码
def commit_mtime(repo, ref) -> int
def write_dir_tarball(src_dir, out_path, mtime, arc_prefix="") -> None
    # 仅普通文件；按 arcname 排序；mode 归一 0644/0755；uid/gid=0、uname/gname=""；PAX 格式；
    # gzip.GzipFile(mtime=0, filename="")（FNAME 位 0、MTIME 0，实测 E-15）；遇软链/特殊文件 → PackageError；忽略字节码
def verify_dir(root, extra_top=(), ignore_bytecode=True) -> [str]
    # 纯文件系统：顶层 ⊆ TOP_LEVEL ∪ extra_top、无 tests、无软链；字节码按 ignore_bytecode 忽略；返回违约描述
def boundary_lines() -> [str]
def parse_release_ref(tag) -> (strict_version, is_prerelease)     # RELEASE_REF_RE.fullmatch；后缀含 ".." → ValueError
def is_strict_version(s) -> bool                                   # VERSION_RE.fullmatch
def normalize_home(path) -> (norm, ambiguous)
    # norm = abspath(expanduser(path))（去尾 "/"、"/."、多余斜杠、文本 ".."）；
    # ambiguous = realpath(原始) != realpath(norm)（原始路径经软链的 ".." 物理解析与文本解析不一致）
def is_symlink_base(path) -> bool                                  # islink(norm) or ambiguous
def agate_home() -> str                                            # AGATE_HOME 优先，否则 ~/.agate；返回 norm（规范化）
def make_work_dir(root, version) -> container                   # mkdtemp(prefix='.agate-tmp-<ver>-')；立即写标记 .agate-installer-owned（kind=tmp）；产物放 <container>/pkg
def sweep_stale(root)                                              # 仅删「.agate-tmp- 前缀 + 真实目录 + 标记有效 + 标记 >1h」的容器；绝不按名字模式删，绝不动 .agate-bak-/vX.Y.Z.bak-*/无标记目录/软链（cso N-1，见 R-8）
def recover_backups(root)                                          # 只改名不删：vX.Y.Z 缺失则把 .agate-bak-*/old 挪回；否则仅提示遗留备份
def swap_in(container, final) -> backup_or_None                   # final 存在则先移入 .agate-bak-<ver>-XXXX/old（带标记），再 rename(<container>/pkg→final)、删空容器；第二步失败自动还原
def rollback_swap(backup, final)                                   # adopt 失败时：把已换位的新目录挪走并还原备份
def snapshot_pointers(root) -> snap                                # 记录 latest/current 的存在性与形态（软链目标 / 文本内容 / 无）
def restore_pointers(root, snap)                                   # 按快照还原（先删现状再重建，软链或文本指针）
def discard_backup(backup)                                         # 仅删本次进程创建、标记与路径校验通过的备份容器
```

- `write_dir_tarball` 先于任何写入校验每个成员，防止把软链 / 设备文件打进包（BDD-15 ④）。
- 在线安装与打包都是「`list_package` → `materialize` 到目录」，tar 只是目录的确定性打包——**没有第二套枚举 / 过滤逻辑**。
- `agate_home()` 的规范化使"装到哪"与"解析到哪"共用同一实现（`agate_common` 改为从这里 import，eng m-3）。

### 3.3 在线安装（批 B1a / B1b）：`agate-install.py`

- 入口最顶部 `sys.dont_write_bytecode = True`（先于 `import agate_common` / `agate_package`）。
- `_install_version(agate_home, repo, version)`：版本目录已存在 → "已安装，跳过"（幂等，含旧形态目录）；否则 `sweep_stale` / `recover_backups`（仅按 R-8 的标记规则，绝不按名字模式删除）→ `list_package`（失败 → stderr 指明缺 `agate/scripts/` 等，exit 1，未创建任何目录）→ `make_work_dir` → `materialize` 到 `<容器>/pkg` → `os.rename(<容器>/pkg → vX.Y.Z)` → 删空容器。任何异常只清理**本次进程创建**的容器并 exit 1。`git clone` 与 `git worktree` 相关调用一律 `git … -- <url>` 形式（cso F-13）。
- `_register(agate_home, version, move_pointers)`：`move_pointers` 时写 `latest → version`、`current → latest`；恒调用 `_sync_root_scripts`（源仍为 `_protocol_root(version_dir)/scripts`；`copytree` 忽略 `__pycache__` / `*.pyc` 且 `symlinks=True`——复制链接自身而非目标）。`latest`（无参）= 装最新 tag + 指针；`vX.Y.Z` = 只预装 + 刷根 scripts（既有契约不变，BDD-24 ①）。
- `--adopt vX.Y.Z`（B1b）：版本号 `fullmatch` 校验 → **规范化后**软链基址检查（拒）→ 版本目录存在，且**新形态**（无 `.git`）时 `verify_dir(vdir)` 无违约（顶层多余条目 / tests / 软链 → exit 1；旧 worktree 形态跳过以保兼容）→ `_protocol_root(vdir)/scripts` 存在 → `_register(move_pointers=True)`；`_register` 先 `snapshot_pointers`，写指针过程中任何 `OSError`（含 `_write_pointer` 遇目录）→ `restore_pointers` 还原快照 → stderr + exit 1，不出 Traceback（eng N-2：adopt 自身事务化）。根 `scripts/` 同步放在指针写入之后，失败仅 WARNING。**不碰 git**。执行主体规则：调用方总是用**自己所在目录**的 `agate-install.py`（M-2）。
- `--uninstall`：仅当版本目录含 `.git`（旧 worktree 形态）且 `repo/` 存在时才 `git worktree remove` / `--force`；否则直接 `rmtree`；只要 `repo/` 存在就 `git worktree prune`（幂等，清掉被替换旧形态遗留的 `repo/.git/worktrees/<vX.Y.Z>` 登记，eng m-4）。引用保护与指针修复不变。
- `--check --portable`：必需 = python3 + pyyaml；git / bash 缺失仅打印提示行（"仅在线安装 / 装历史 tag / `agate-changes.py` 需要 git；安装 hook 需要 bash"）。默认口径不变（缺 git exit 1，`test_bdd_7/8` 源码不改）。
- 软链基址：`_cmd_install` / `_cmd_adopt` 入口 `agate_package.is_symlink_base(agate_home)` → 拒绝（exit 1）；`agate_home` 已是规范化路径（`_agate_home` 委托 `agate_package.agate_home()`）。文案 `_SYMLINK_HOME_MSG`：首行动态"检测到的软链：`<规范化路径>` → `<readlink 目标>`；若它不是 `~/.agate`，请把下列命令中的 `~/.agate` 替换为它"（cso F-8），随后三步迁移（三个命令片段与其他入口逐字相同，保 `_migration_steps` 正则 `mv\s+~?/?\.agate\s+\S*\.bak` / `mkdir\s+-p\s+~?/?\.agate` / `install\.sh\s+--versions` 抽取一致）+ BDD-51 附句。
- 安装器选择不变：`install.sh` 与根 `scripts/` 各自使用其所在位置的安装器，本任务**不**新增"先更新 `repo/` 再安装"逻辑（主 Agent 裁决）；因此旧安装器装 v0.73.0 得旧整仓形态，由 UPGRADING 文档说明（R-1）。
- 保持：`_ensure_repo`（clone / fetch --tags）、`_latest_tag`（严格 `vX.Y.Z` 过滤，预发布 tag 被忽略）、`_find_references`、`_repair_pointers`、`_protocol_root` 降级副本。`_VERSION_RE` 改 `fullmatch` 口径（`agate_package.VERSION_RE`）。

### 3.4 离线 pack / install（批 B2）

**pack 侧** `pack_offline(version, platform, out_dir, repo_dir, ..., ref=None)`：

1. `ref = ref or version`；校验平台标签；`entries = list_package(repo_dir, ref)`（`PackageError` → `PackOfflineError`）。
2. bundle 布局（= 版本目录布局 + 安装输入物）：

```
agate-<version>-<platform>/
├── agate/            # 本体内容（materialize 落盘；顶层含 scripts/ WORKFLOW.md …；不含 agate/agate/、agate-workspace/、docs/…）
├── CHANGELOG.md LICENSE NOTICES.md   # 登记根文件（历史 tag 缺则缺）
├── wheels/           # pip download（pyyaml==PYYAML_PIN；wheel 查找大小写无关）
└── manifest.json     # version 恒为严格 vX.Y.Z；source_ref（预发布 tag 原样，仅信息性）；files（包集合 P 的相对路径清单，排序）
```

3. manifest 组件：`agate`（目录哈希，跳过字节码）、每个存在的登记根文件各一个文件组件、`wheels`、`pyyaml`（[+ `pillow`、`python`]）；`files` = `[e.path for e in entries]`。哈希仍走 `agate_common.compute_sha256`（单实现）。
4. `_default_repo()` 运行时取 `agate_package.agate_home() + "/repo"`（BDD-10 缺省 `--repo`）；CLI 增 `--ref`。

**install 侧** `install-offline.py` 主流程顺序（**先校验后有副作用；任何时刻旧版完整或新版完整**）：

0. 入口最顶部 `sys.dont_write_bytecode = True`（先于 `import agate_common`——真实用法是内网机器上直接运行 `bundle/agate/scripts/install-offline.py`，若产生 pyc 会污染 bundle 的 `agate` 组件哈希，eng B-1 / 实测 X-2）。
1. 参数解析；`dest_root` 缺省 `agate_package.agate_home()`；**规范化后** `is_symlink_base(dest_root)` → 三步迁移文案 exit 1（BDD-33；`--dest-root` 指向普通目录 / 不存在的新目录不受影响）。
2. manifest 读取 / 校验（`_validate_manifest`，版本改 `parse_release_ref` 严格分支；`source_ref` 仅在通过 `parse_release_ref` 且无控制字符后才展示，绝不参与路径拼接）+ 平台核对。
3. `_check_bundle_layout(bundle)`：
   - `bundle/agate/agate/scripts` 是目录 → 旧格式，stderr "bundle 为旧格式（`agate/agate/scripts` 双层嵌套），请用新版 `agate-pack-offline.py` 重新打包"，exit 1，**未写任何目录**（BDD-12）；
   - `bundle/agate/scripts` 不存在 → 缺本体，exit 1；manifest 缺 `files` → exit 1（fail-closed）；
   - 对 `bundle/agate`、每个登记根文件先 `os.lstat`：软链 / 非普通文件（设备 / FIFO / socket）→ exit 1；`os.walk(followlinks=False)` 逐项判定（BDD-15 ④ 在解包入口的对应防护，cso F-6）；
   - **对账**：磁盘上 `agate/**` ∪ 顶层登记根文件（忽略字节码）的路径集合 == manifest `files`；多 / 少 / 改名 → exit 1（含 bundle 顶层出现契约外文件如 `extra.sh`：不在 `files` 中则不拷，且给出告警）。
4. `verify_checksums`（组件哈希；文案"不一致（损坏或被替换）"，不断言"被篡改"）。
5. `sweep_stale(dest_root)` / `recover_backups(dest_root)`（R-8 的标记规则）；`copy_files(bundle, manifest["files"], make_work_dir(dest_root, version) + "/pkg")`——**只拷 manifest 已登记且已对账的文件**；此时尚无任何对 `dest_root` 既有内容的改动。
6. `install_wheels`（pip；有系统副作用，故排在拷贝之后、换位之前；失败则丢弃临时目录，exit 1，`dest_root` 不变）。
7. `snap = snapshot_pointers(dest_root)`；`backup = swap_in(container, vdir)`（已存在则旧目录移入带标记的备份容器；第二步失败自动还原）。
8. 子进程 `[sys.executable, "-B", <本脚本所在目录>/agate-install.py, "--adopt", version]`，env `AGATE_HOME=dest_root`、`PYTHONDONTWRITEBYTECODE=1`（M-2：兄弟安装器；bundle 版本与安装器版本解耦）。失败（含子进程被杀 / 非 0 退出，此时指针可能已被子进程部分写入）→ `rollback_swap(backup, vdir)` **并 `restore_pointers(dest_root, snap)`**，再 exit 1（stderr："版本目录与 latest/current 指针均已还原，请修复后重跑"）（eng N-2）。
9. 成功 → `discard_backup(backup)`（仅本次自己创建的备份容器）。嵌入式 `python/` 组件：不安装，打印一行说明（R-9）。`.installed-version`、`.agate-root` 不再写（D-7）。

### 3.5 portable（批 F1a 文档 + 批 B1b 命令）

UPGRADING 新增 `### portable 安装（Release tarball，无需 git）`，**所列命令即验收脚本**（BDD-17 逐条实跑，变量替换；测试 `PATH` 目录须含 `sha256sum`）：

```bash
AGATE_HOME="${AGATE_HOME:-$HOME/.agate}"
while [ "${AGATE_HOME%/}" != "$AGATE_HOME" ]; do AGATE_HOME="${AGATE_HOME%/}"; done
[ ! -L "$AGATE_HOME" ] || { echo "AGATE_HOME 是软链，请先按迁移三步处理"; false; }
sha256sum -c SHA256SUMS --ignore-missing          # macOS：shasum -a 256 -c SHA256SUMS
mkdir -p "$AGATE_HOME" && mkdir "$AGATE_HOME/vX.Y.Z"   # 已存在则失败：先 --uninstall 该版本或换目录
tar -xzf agateon-vX.Y.Z.tar.gz -C "$AGATE_HOME/vX.Y.Z"
python3 -B "$AGATE_HOME/vX.Y.Z/agate/scripts/agate-install.py" --adopt vX.Y.Z
python3 -B "$AGATE_HOME/scripts/agate-install.py" --check --portable
```

- `-B` 的原因（写入 UPGRADING）：避免从版本目录内运行脚本时留下 `__pycache__`；首行两条 shell 守卫在解压**之前**挡住软链基址（`--adopt` 内的守卫是第二道，晚于 `mkdir` / `tar`，cso F-12）。
- 依赖声明写 `python3` + `pyyaml`；写明"无需 git，但 `agate-changes.py` 等依赖 agate git 仓库的工具不可用；安装 hook 需 bash"；全文不得出现 BDD-19 的"零依赖"类词。
- **完整性说明（cso F-4，文档如实写入）**：`SHA256SUMS` 与资产同处一个 Release，**只能发现下载损坏，不提供发布者身份认证**；需要更强保证请从 git tag 自行构建（`agate-release.py build` 的产物可与资产逐成员比对）或经第二渠道核对哈希。offline 小节同口径。
- 下载指引：推荐 `agateon-<tag>.tar.gz`（本体），GitHub 自动生成的 Source code 为整仓。

### 3.6 Release workflow + `agate-release.py`（批 C1 / C2）

**`agate-release.py`**（stdlib + 延迟导入 `agate_common`；入口顶部 `sys.dont_write_bytecode = True`）：

| 子命令 | 行为 |
|--------|------|
| `boundary` | 打印 `boundary_lines()`（UPGRADING 契约块的生成源） |
| `pyyaml-pin` | 打印 `agate_package.PYYAML_PIN`（workflow 安装依赖与 `agate-pack-offline` 同源） |
| `notes --tag T [--changelog F] --out FILE` | `extract_notes(text, tag)`：按 `^## \[([^\]]+)\]` 切段（到下一个 `## ` 止，去尾部空行与 Keep-a-Changelog 链接定义行）。正式 tag：取 `[X.Y.Z]` 段，**缺段或段体为空 → stderr + exit 1 且不写输出文件**。预发布 tag：取去后缀版本段，缺段回落 `[Unreleased]`，仍缺 → exit 1；输出**首行**为"预发布测试（<tag 原样>）——非正式发布"。所有 notes 头部含：推荐下载 `agateon-<tag>.tar.gz`（本体）；GitHub 自动生成的 Source code 包为整仓；offline 面向 Python 3.11；**`SHA256SUMS` 仅防下载损坏、不认证发布者**；offline 包内 wheel 的文件名与 sha256 清单 |
| `is-prerelease T` | exit 0 = 预发布（合法且非严格 semver），exit 1 = 正式；非法 tag exit 2 |
| `build --tag T --repo R --outdir D --notes-out F [--expect-sha SHA] [--platforms p1,p2] [--skip-offline]` | ① `parse_release_ref`；② 若给 `--expect-sha`：`git rev-parse "refs/tags/T^{commit}"` 必须等于 `git rev-parse "<SHA>^{commit}"`（**两侧都剥成 commit**，故轻量 tag、附注 tag、以及 `GITHUB_SHA` 恰为 tag 对象 SHA 的情形均正确，eng N-3），不等则 exit 1（cso F-3，产物来源与触发提交一致）；③ `materialize` 到临时目录 → `write_dir_tarball` → `agateon-<T>.tar.gz`；④ 每平台：子进程 `[sys.executable, "-B", agate-pack-offline.py, <strict>, "--ref", T, "--platform", p, "--outdir", <tmp>, "--repo", R]` → `write_dir_tarball(bundle, agateon-<T>-offline-<p>.tar.gz, arc_prefix=agateon-<T>-offline-<p>)`；⑤ `notes`；⑥ `SHA256SUMS`（`<hex>  <name>` 排序，可被 `sha256sum -c` 校验，哈希走 `agate_common.compute_sha256`） |

tar 的 mtime 统一取 `commit_mtime(repo, tag)`，故同 tag 同 Python 次版本 → 同哈希（R-5）。offline tar 加一层 `agateon-<T>-offline-<p>/` 包裹目录（防解包散落；BDD-16 解包目录即该目录），本体 tar 不包裹（BDD-15 ②）。

**`.github/workflows/release.yml`**（设计草案，P4 落成；**令牌只在 Publish 步骤**）：

```yaml
name: Release
on:
  push:
    tags: ['v*']
permissions:
  contents: write            # 唯一权限
concurrency:
  group: release-${{ github.ref_name }}
  cancel-in-progress: false
jobs:
  release:
    runs-on: ubuntu-latest
    timeout-minutes: 20
    env:
      TAG: ${{ github.ref_name }}
    steps:
      - name: Clone tag           # 无 action、无令牌；私有仓库时需加 http.extraheader
        run: |
          set -euo pipefail
          git clone --depth 1 --branch "$TAG" -- "https://github.com/${GITHUB_REPOSITORY}.git" src
      - name: Python deps (pinned pyyaml)
        working-directory: src
        run: |
          set -euo pipefail
          python3 -m venv "$RUNNER_TEMP/venv"
          PIN="$(python3 -B agate/scripts/agate-release.py pyyaml-pin)"
          "$RUNNER_TEMP/venv/bin/pip" install --quiet --only-binary=:all: "pyyaml==${PIN}"
      - name: Build assets        # 只调仓库脚本，workflow 内零打包逻辑；无令牌
        working-directory: src
        run: |
          set -euo pipefail
          "$RUNNER_TEMP/venv/bin/python" -B agate/scripts/agate-release.py build \
            --tag "$TAG" --expect-sha "$GITHUB_SHA" --repo . \
            --outdir "$RUNNER_TEMP/dist" --notes-out "$RUNNER_TEMP/notes.md"
      - name: Publish
        working-directory: src
        env:
          GH_TOKEN: ${{ github.token }}      # 不写 secrets.*（BDD-13 ③）；仅此步骤持有令牌
        run: |
          set -euo pipefail
          rc=0; python3 -B agate/scripts/agate-release.py is-prerelease "$TAG" || rc=$?
          PRE=()
          case "$rc" in 0) PRE=(--prerelease);; 1) ;; *) exit "$rc";; esac
          gh release create "$TAG" "$RUNNER_TEMP"/dist/* --verify-tag --title "$TAG" \
            --notes-file "$RUNNER_TEMP/notes.md" "${PRE[@]}"
```

- 静态契约（BDD-13，T-8）：触发器仅 `push.tags: v*`；`permissions` 仅 `contents: write`；无 `uses:`（零第三方 action；若日后引入须 40 位 SHA）；无 `secrets.`；无 `workflow_dispatch` / `pull_request*` / `workflow_run`；**所有 `run:` 字符串不含 `${{`**（表达式只出现在 `env:` 与 `concurrency.group`，杜绝脚本注入）；`GH_TOKEN` 只出现在 Publish 步骤 env；含多语句的 `run:` 首行 `set -euo pipefail`。PyYAML 把键 `on` 解析成布尔 `True`——P3 静态断言须用 `doc.get(True, doc.get("on"))`。
- 资产名（BDD-13 ⑤）：`agateon-<tag 原样>.tar.gz`、`agateon-<tag 原样>-offline-linux-x86_64.tar.gz`、`agateon-<tag 原样>-offline-windows-x86_64.tar.gz`，外加 `SHA256SUMS`（C-1 口径）。预发布 tag 时 `manifest.version` 为严格 `vX.Y.Z`（`parse_release_ref` 去后缀）。
- 失败面：`gh release create` 是最后一步，之前任一步失败则无 Release，可用 `agate-release.py build` 本地重建后手工 `gh release create`（因无 `workflow_dispatch`，写进 AGENTS.md 发布清单，BDD-21）。Release 已存在时重跑会失败，须先 `gh release delete`（仅限已确认属本次创建者）。建议（写入 AGENTS.md 发布清单，非代码）：仓库为 `v*` 启用 tag 保护 / Ruleset，只允许维护者创建。

### 3.7 legacy 软链彻底删除（批 E）

- **`agate_common.py`**：`_resolve_version_info(start_dir=None)` 无 `use_legacy` 参数、无 `realpath(base)` 分支；基址取 `agate_package.agate_home()`（规范化，单源）；返回 dict 增 `"symlink_base": agate_package.is_symlink_base(base)`——**含 `AGATE_ROOT` env 早返回分支**（该分支恒 `False`，消费者不必 `.get`，eng m-6）；新增 `symlink_migration_hint()` 返回规范三步文案（含动态"检测到的软链"行）。软链基址走普通链：BDD-51（软链 → 完整版本根，`current` 链有效）放行，BDD-27（软链 → 协议本体、无 `current`）落到终态失败 + 提示，BDD-28(e)（`AGATE_ROOT` 与软链 `AGATE_HOME` 同设）env 优先——**三者是同一条代码路径的三种输入**，无需为它们分别写分支。`resolve_version_root` 文档改"三层"，`resolve_hook_root` 仅去掉 `use_legacy=False` 实参。`compute_sha256` 目录分支跳过字节码（D-13）。
- **`agate-resolve.py`**：终态失败（本就仅在无根可解析时才会走到）→ stderr 原句 + `symlink_base` 为真时追加迁移提示；exit 1（S-15）；stdout 无 `AGATE_ROOT=`。
- **`agate-summary.py`**：`AGATE_ROOT` 行"（无可用 AGATE_ROOT）"不变；**仅当没有任何根可解析（`info["root"]` 为 None）且 `symlink_base` 为真时**才追加一行含 `mv ~/.agate ~/.agate.bak` 的提示（软链基址但经 `current` 链正常解析的 BDD-51 场景**不**打印，eng N-4）；启动建议 2 改 `读 {root}/AGENTS.md`（root 为 None 时改为"先按上方提示修复安装"）；`changelog_hint` 注释去 legacy。
- **`install.sh`**（仅三项行为变化 + 守卫规范化）：① 废弃变量 `AGATE_REPO_DIR` / `AGATE_SYMLINK` 任一被设置 → stderr 一行 WARNING 说明"已废弃且被忽略"（不创建其指向路径）；② 参数：无参或 `--versions` 合法（等价），其他 → 用法 + exit 2；③ `AGATE_VER_ROOT="${AGATE_HOME:-$HOME/.agate}"` 后**规范化**：循环剥离尾部 `/` 与 `/.`（实测 E-12：`[ -L "L/" ]` 为假、剥离后为真），含 `..` 分量则拒绝（exit 1，提示"请使用不含 `..` 的规范路径"）；随后 `[ -L "$AGATE_VER_ROOT" ]` → heredoc 迁移文案（首行动态"检测到的软链：`$AGATE_VER_ROOT` → `$(readlink …)`"）exit 1（先于任何 clone）；其余沿用现有 `--versions` 分支：探测 python3 / python；`mkdir -p`；`repo/.git` 缺 → `git clone -- "${AGATE_REPO_URL:-…}" …`；`exec "$PY" "$INSTALLER" latest`（`repo/` 已存在时**不**更新，保持现状）。头注与末尾提示不再引用两个废弃变量（WARNING 文案是唯一出处）。`shellcheck -S warning` 须干净。
- **软链文案单源问题**：`install.sh`（bash heredoc）无法 import，故沿用 DEBT0034 的"多处手写 + `_migration_steps` 正则跨入口比对"，把新增入口（`install-offline.py`、`agate_common.py`）纳入该测试（BDD-35）；动态"检测到的软链"行放在三步片段之前，不影响正则抽取。

### 3.8 文档面

按批次归属见 §5；关键口径：UPGRADING 对照表单布局（含"迁移"行三步）；解析优先级表 3 行（env `AGATE_ROOT` > `AGATE_HOME` → 项目声明 → current）；`:809` `:841`「存量单软链用户行为不变（红线，BDD-30）」改写为"legacy 已移除（v0.73.0 BREAKING）+ 迁移指引"；`### v0.73.0` 节含 BREAKING 标注、影响面（仅软链用户；已知存量 1 = 本机已迁移）、迁移三步、`install.sh` 无参语义变化、废弃 env、Release / portable 新增、**升级说明（R-1，仅文档）**：v0.72 用户用旧安装器升级时 v0.73.0 自身为旧整仓形态（仍可解析），之后经同步后的根 `scripts/` 执行的安装均只装本体；**另写明（eng m-5）**：`agate-install.py vX.Y.Z` 钉老版本会把根 `scripts/` 同步为该老版本的安装器，其后 `latest` 可能再走旧安装路径——需先 `agate-install.py latest`（用新版本重新同步）或直接用 `repo/` 的最新安装器；§3 顶部加"v0.73.0 起 legacy 软链布局不再支持，下列历史节中软链布局表述仅作历史记录"；契约小节写明"安装态 vs 运行后态"（§3.1）与 SHA256SUMS 完整性局限（§3.5）。SETUP `$AGATE_DIR`：

```bash
AGATE_DIR="$HOME/.agate/current/agate"
test -r "$AGATE_DIR/orchestrator-template.md" && echo "✅ 模板可读" || echo "❌ 协议根不可用：$HOME/.agate/current 缺失或版本目录不完整，请先 bash install.sh"
```

（不含 `|| echo "$HOME/.agate"` 式 fallback；`current` 缺失时明确失败提示。）

### 3.9 兼容红线核对

| 红线 | 结论 |
|------|------|
| `_protocol_root` 函数体不改 | 不改（BDD-6 零 diff；BDD-8 锁双实现） |
| 已装旧形态可解析 | 探测序 2 命中 `vdir/agate`；BDD-5/7 用显式 worktree fixture |
| `vdir/scripts` 优先于 `vdir/agate/scripts` | 不动；BDD-6 新增两者皆有用例 |
| 目录名固定 `agate/` | 契约常量 `PKG_DIR`；BDD-1 (c) grep 断言 |
| 打包逻辑一份 | `materialize` + `write_dir_tarball`；workflow 无内联；BDD-3 |
| 升级自举（旧安装器装出旧形态） | 不改代码，仅 UPGRADING v0.73.0 节说明；backlog 建议见 §13 |
| 不改项 | §1.2 |

---

## 4. BDD → 设计落点映射（52 条，每条至少一个落点）

| BDD | 落点 |
|-----|------|
| 1 | §3.1 UPGRADING 契约小节（树 + 顶层集合 + `verify_dir` + 单一来源路径 `agate_package.py`） |
| 2 | §3.2 `list_package` / `is_packaged` / `verify_dir`（忽略字节码）；测试直接对 F_pkg 断言 |
| 3 | §3.2 常量单一来源 + `agate-release.py boundary` + 文档一致性单测；`is_packaged` 默认拒绝 |
| 4 | §3.3 / §3.4 / §3.5 三路径共用 `materialize` / `copy_files`；指针与根 scripts 共用 `_register`；比较口径忽略字节码（D-13），且在 H2 / H3 运行过 `agate-resolve.py` **之后**再比较一次（T-4） |
| 5 | §3.1 旧形态兼容；测试显式构造 worktree 整仓 fixture |
| 6 | §1.2 / §3.9：`_protocol_root` 不改；新增优先级用例（仅测试） |
| 7 | §3.1 共存；无代码改动（既有解析链） |
| 8 | 仅测试：两份 `_protocol_root` 五夹具一致 |
| 9 | §3.4 pack 用 `materialize`（bundle/agate 即本体）；install 只拷 manifest `files` 对账后的文件；测试以 **bundle 内入口**执行（T-15） |
| 10 | §3.4 `_default_repo` / `agate_home()`；install 经 `--adopt` 得 `latest`、`current→latest`、根 `scripts/` |
| 11 | §6：三处助手改走真实 pack 入口；sentinel；round-trip 末尾加 resolve；红灯回放（§6 T-2） |
| 12 | §3.4 install 步骤 3（旧格式拒绝，先于任何写入） |
| 13 | §3.6 workflow 草案 + 静态断言（`on`→`True` 注意）；⑤ 资产口径见 BDD-21 行（C-1） |
| 14 | §3.6 `extract_notes`（可被测试直接调用） |
| 15 | §3.2 `write_dir_tarball`（成员安全 + 确定性）+ `agate-release.py build` |
| 16 | §3.6 offline tar + §3.4 install 步骤；测试以 bundle 内 `install-offline.py` 为入口，`pip` 用 PATH shim（T-15） |
| 17 | §3.5 portable 命令（含 `-B`、软链 / sha256 守卫）+ `--adopt`；无 git PATH 测试 |
| 18 | §3.3 `--check --portable` |
| 19 | §3.5 / 文档批；grep 测试 |
| 20 | §11 CI 验证策略 |
| 21 | §3.6 失败面 + AGENTS.md 发布清单（文档批 F2）；**口径（主 Agent 裁决 C-1）**：BDD-13 ⑤ / 20 ② / 21 / 50 ⑥ 的"3 个资产"读作"至少这 3 个 tarball 名 ∈ 资产集合，另有 `SHA256SUMS`"（共 4 个资产），不改 P1 |
| 22 | §3.3 `_install_version` → `materialize`；`_sync_root_scripts` 不变 |
| 23 | §10 E-5；P5/P6 真实仓库实测 |
| 24 | §3.3：老 tag 靠安装器侧规则；畸形 tag `list_package` 失败前不建目录 |
| 25 | §3.3 `--uninstall` 新旧形态分支 |
| 26 | §3.3 幂等 + 不污染源仓库（`repo/` 只在 AGATE_HOME 下） |
| 27 | §3.7 `agate_common` + `agate-resolve.py` |
| 28 | §3.7 删 `use_legacy` / `realpath(base)` 分支；`inspect.signature` 断言 |
| 29 | §3.7 `install.sh` 重写 |
| 30 | §3.7 WARNING；测试清理两文件的 `AGATE_REPO_DIR` 引用 |
| 31 | §3.7 软链守卫前置 + 规范化（D-14）；T-14 参数化 |
| 32 | §3.3 `_SYMLINK_HOME_MSG` 保留既有拒绝逻辑 + 规范化（D-14）；T-14 |
| 33 | §3.4 install 步骤 1（规范化后守卫）；T-14 |
| 34 | §3.7 `agate-summary.py` |
| 35 | §3.3 / §3.7 多入口三片段一致；扩展 DEBT0034 测试 |
| 36 | 仅测试（三步真实走通） |
| 37 | 仅测试 + 文档批（R 集合 12 文件清零，W 白名单显式） |
| 38 | 测试批：4 个 legacy 测试改写 / 删除；`test_bdd_30*` 撞名零改动 |
| 39 | 文档批 F1a / F2 |
| 40 | §3.7 `agate-summary.py` + 文档批（handoff-template / orchestrator-template） |
| 41 | §3.8 SETUP `$AGATE_DIR` |
| 42 / 43 / 44 / 45 | 文档批不改 SETUP 四平台命令本身；测试按 SETUP 字面命令实跑（43/45 真实 CLI，缺则 FAIL） |
| 46 | §1.2 Not Modify；`git diff 75a8102..HEAD` 零 diff 断言 |
| 47 | §1.2：`resolve_hook_root` 兜底保留；仅去 `use_legacy` 实参 |
| 48 | §7 P5 gate；P5 报告列 (D, A) 对账 |
| 49 | §7 `P5_consistency` / `P5_ruff` / `P5_shellcheck` + README 索引 |
| 50 | P8：版本三处一致、PR 描述如实列出触发 / 权限（文档批不含 P8） |
| 51 | §3.7（同一路径天然放行）+ §3.3（安装侧一律拒绝） |
| 52 | 仅测试 + 边界（`agate/tests` 不入包）；C-2 |

---

## 5. 批次设计（`dispatch_plan`）

文件面互不冲突，共享文件归属单一：`agate-install.py`→B1a、B1b（**同一文件的两个串行批**，B1b 依赖 B1a，不并行——"同文件不跨批改两轮"清单项的目的是避免并行合并冲突，串行依赖下不成立；拆开是为满足"high 必须拆分"）；`agate_common.py` / `install.sh` / `agate-resolve.py` / `agate-summary.py`→E；`UPGRADING.md` / `CHANGELOG.md`→F1a；`agate/scripts/README.md`（新增脚本索引）→F2。补协议文档正文属 **P4 实现**（DEBT0039），P7 只做跨文件一致性核对。

| 批 | id | 产出 | 复杂度 | 依赖 | 批内验收（`tests_filter`，P3 文件名可调整，须回填对应关系） |
|----|----|------|--------|------|------|
| 1 | `A-package-lib` | `agate/scripts/agate_package.py` | medium | — | `unit/test_agate_package.py`：BDD-2/3(①②)/22 集合 / 23 / 24 ② / 15 ④（成员安全）/ 路径硬化 / 规范化守卫函数 / gzip 头 / `parse_release_ref` 表驱动 |
| 2 | `B1a-online-install-core` | `agate/scripts/agate-install.py`（安装 / 卸载 / `_register` / 软链守卫与文案 / `-B` / 临时目录） | medium | A | `unit/test_agate_version_install.py`、`unit/test_agate_install_uninstall.py`：BDD-22 / 24 / 25 / 26 / 32 / 35(py 侧) / 51②；T-14（agate-install 入口） |
| 3 | `E-legacy-removal-code` | `agate_common.py`、`agate-resolve.py`、`agate-summary.py`、`install.sh` | medium | A | `unit/test_agate_version_resolve.py`、`unit/test_agate_summary.py`、`unit/test_install_sh.py`、`regression/test_protocol_root_dual_impl.py`：BDD-6 / 8 / 27 / 28 / 29 / 30 / 31 / 34 / 40 / 51①；T-14（resolve / install.sh 入口）；`compute_sha256` 字节码免疫 |
| 4 | `B1b-adopt-check` | `agate/scripts/agate-install.py`（`--adopt`、`--check --portable`、`_usage` / `main`） | medium | B1a | `unit/test_agate_install_adopt.py`：BDD-17（不含文档命令部分）/ 18；adopt 的 `verify_dir` / 指针写入失败路径 |
| 5 | `B2-offline-pack-install` | `agate-pack-offline.py`、`install-offline.py` | medium | A、B1b、E | `unit/test_install_offline.py`、`unit/test_agate_pack_offline.py`、`regression/test_offline_bundle_roundtrip.py`：BDD-9 / 10 / 11 / 12 / 33；T-2 / T-15 / T-16 / T-19 / T-23 |
| 6 | `C1-release-cli` | `agate/scripts/agate-release.py` | medium | A、B2 | `unit/test_agate_release.py`、`integration/test_install_three_paths.py`：BDD-4 / 14 / 15 / 16 / 17（命令部分依赖 F1a 的文档，见下）/ T-4 / T-9 / T-18 / T-22 |
| 7 | `C2-release-workflow` | `.github/workflows/release.yml` | low | C1 | `unit/test_release_workflow.py`：BDD-13 / T-8 |
| 8 | `F1a-docs-upgrading` | `agate/UPGRADING.md`、`CHANGELOG.md` | medium | A、B1b、B2、C1、E | `unit/test_upgrading_lifecycle.py`、`unit/test_upgrading_contract_doc.py`：BDD-1 / 3 ③ / 19 / 38 ④ / 39 ①–⑤；BDD-17 文档命令实跑（T-4 H3） |
| 9 | `F2-docs-sweep` | `README.md`、`README.zh-CN.md`、`agate/SETUP.md`、根 `AGENTS.md`、`agate/AGENTS.md`、`WORKFLOW.md`、`adr.md`、`orchestrator-template.md`、`handoff-template.md`、`platform-notes.md`、`CONTEXT.md`、`agate/scripts/README.md`、`docs/guides/project-map.md`、`docs/guides/worktree-dogfooding-guide.md`，及两处测试注释 | low | A、C1、E | `regression/test_no_legacy_residue.py`、`unit/test_setup_agate_dir.py`：BDD-37 / 39 ⑥–⑨ / 40 / 41 / 42–45 |

**批 E 的追加验收（eng N-1）**：`agate_common` 现 `from agate_package import agate_home`，凡把 `agate_common.py` 拷入合成目录的夹具都须同时拷 `agate_package.py`；批 E 的批内验收除 frontmatter `tests_filter` 外，还须跑 `unit/test_hook_resolve_entry.py`、`integration/test_pre_commit_hook.py`、`unit/test_dispatch_context_warning.py`（frontmatter 不改，故写在此处，P3 回填对应关系）。

**批内 vs 波次末验收（eng M-4）**：BDD-1 / 3 ③ / 17 / 19 读 UPGRADING（F1a 产出），BDD-37 读 F1a / F2 全部产物——这些**只能在文档批之后转绿**，属"波次末合并后"验收（P5 全量为准）；其余 BDD 在各自批内转绿。`check-mvwu.py` 观测器按批读取 `tests_filter`，故 frontmatter 已给每批一条批内命令（只覆盖该批交付面，不含全量）。

**批次 9（F2）产出 >3 的说明（任务粒度兜底）**：均为机械性措辞替换 / 单段注记（每文件改动 ≤ 约 10 行），由 BDD-37 的 grep 回归测试逐文件验收；拆成更多并行批只会增加交叉引用的合并冲突，且低复杂度纯文档，不拆（eng M-4 同意合并 F1b 与 F2）。

**复杂度（eng M-4）**：原 B1 / C 单批标 medium 偏低——已按文件面与依赖拆为 B1a / B1b、C1 / C2，拆后每批 medium 或 low，无 high 单发。

**执行顺序（`mode: serial` 的串行依赖链；相邻且互不依赖的批可并发，并发 ≤ 3，资源密集型批不并发）**：A → (B1a ∥ E) → B1b → B2 → C1 → C2 → (F1a ∥ F2)。依赖：B2 依赖 B1b（`--adopt`）与 E（`compute_sha256` 字节码免疫）；C1 依赖 B2（`--ref`、manifest `files`）；文档批依赖全部代码批。`parallel_limit: 3` 即实际并发上限，不再为凑数放大。各批由主 Agent 逐批 commit。

---

## 6. 测试策略提示（供 P3）

**P3 测试文件规划**：新增 `unit/test_agate_package.py`、`unit/test_agate_release.py`、`unit/test_release_workflow.py`、`unit/test_install_sh.py`、`unit/test_agate_install_adopt.py`、`unit/test_upgrading_contract_doc.py`、`unit/test_setup_agate_dir.py`、`integration/test_install_three_paths.py`、`regression/test_no_legacy_residue.py`、`regression/test_protocol_root_dual_impl.py`；修改既有 `unit/test_agate_version_install.py`、`unit/test_agate_install_uninstall.py`、`unit/test_install_offline.py`、`unit/test_agate_pack_offline.py`、`unit/test_agate_version_resolve.py`、`unit/test_upgrading_lifecycle.py`、`regression/test_offline_bundle_roundtrip.py`、`integration/test_version_lifecycle_e2e.py`、`unit/test_dsh_preset.py`（注释）。

- **T-1 真实 pack 产物**：共享 fixture `make_synthetic_tag_repo(tmp)`（含 `agate/`（含 `tests/`）、噪声顶层目录、`CHANGELOG.md` `LICENSE` `NOTICES.md`、`HANDOFF-X.md`，多个 tag：正常 / 更老无 `agate/scripts` 的畸形 tag / 缺 NOTICES 的老 tag），`AGATE_REPO_URL=file://…`；pack 的 git 步骤真实执行，仅 `pip download` / `pip install` stub。**合成 tag 内不必内嵌安装器**：`--adopt` 由 `install-offline` 同目录的兄弟安装器执行（M-2）。
- **T-2 BDD-11 红灯回放（永久变异测试）**：保留一个"旧行为构造器"（真实 `git worktree add` 整仓检出到 `bundle/agate`），断言 sentinel 断言函数在其上 `pytest.raises(AssertionError)`，且 `install-offline` 对其 exit 1（BDD-12）。P3 另留一次性证据：对 P4 前代码跑 BDD-9 / sentinel 必红。
- **T-3 BDD-37**：`agate/tests/regression/` 永久 grep 测试，`git ls-files` 范围、任意层级 `archived/` 与 tasks / reviews / design-notes 排除、`re.I`、四模式；白名单 W（12 项）以 `(路径, 理由)` 列出；R 集合 12 文件须清零。
- **T-4 三路径同构（BDD-2/4，eng G-4）**：H1 在线 / H2 离线 / H3 portable 三个独立 `AGATE_HOME`，比较 `vX.Y.Z/` 递归文件集合逐一相等（**显式忽略 `__pycache__` / `*.pyc` / `*.pyo`**）、`verify_dir` 无违约、`agate-resolve.py` 结果一致；**在 H2、H3 都运行过 `agate-resolve.py` 之后再比较一次**（模拟真实使用后状态，此时字节码可能已出现，比较仍须相等）。H3 直接执行 UPGRADING portable 小节命令（解析文档 fenced 块，变量替换）。
- **T-5 无 git 环境（BDD-17/18）**：构造仅含 `python3`（含 pyyaml）+ coreutils（含 `sha256sum`）符号链接的 `PATH` 目录，先断言 `shutil.which("git", path=P) is None`；Windows 上跳过（symlink 权限）。
- **T-6 tarball 安全（BDD-15 ④）**：对产物 `tarfile` 逐成员断言 `isreg()`，无绝对路径 / `..`；另构造含软链的 bundle 断言 `install-offline` 拒绝、`write_dir_tarball` 拒绝；**gzip 头断言（cso §3 T-3）**：FLG 的 FNAME 位为 0、MTIME 为 0、OS 字节固定；**补 G-5**：bundle 顶层出现契约外文件（如 `bundle/extra.sh`）不被拷入 vdir。
- **T-7 tripwire**：真实 HEAD 上 `agate/` 顶层条目集合与已知集合逐一比对，新增子目录必须有意识处理（R-4）。
- **T-8 workflow 静态**：`yaml.safe_load`；`on` 键取值用 `doc.get(True, doc.get("on"))`；`permissions == {"contents": "write"}`；无 `uses:`、无 `secrets.`；4 个既有 workflow `git diff` 为空；**cso F-14 增补**：所有 `run:` 字符串不含 `${{`；`GH_TOKEN` 只出现在 Publish 步骤 env；触发面仅 `push.tags`（无 `branches` / `pull_request*` / `workflow_dispatch` / `workflow_run`）；含多语句的 `run:` 出现 `set -euo pipefail`；Publish 步骤对 `is-prerelease` 的 rc 有 `case` 三分支（0 / 1 / 其他 exit）。
- **T-9 notes**：夹具 A/B（BDD-14 ④）+ 真实 CHANGELOG 取 v0.72.0；缺段 exit 1 且 `--out` 文件不存在；notes 头含"SHA256SUMS 仅防损坏、不认证发布者"。
- **T-10 既有用例保护（eng M-3 澄清）**：`test_tag0032_bdd_6/7`（`_protocol_root`）、`test_bdd_7/8`（`--check`）、`test_bdd_3`、`test_tag0032_bdd_3/4/5/13/14`、`test_debt0034_*` 的**测试函数体不改**（仅在其上扩展新增入口的新用例）；**但夹具助手允许增拷文件**：`_tag_upstream`（`test_agate_version_install.py`）与 `_tag_meta_upstream`（`test_version_lifecycle_e2e.py`）把 `agate-install.py` 拷入合成 tag 的 `agate/scripts/`，其拷贝清单须加入 `agate_package.py`（否则 `install.sh --versions` 与 e2e 的根 `scripts/agate-install.py` 会 `ModuleNotFoundError`）；**同理，所有把 `agate_common.py` 拷入合成目录的夹具**（eng N-1，已核对：`test_hook_resolve_entry.py`、`test_pre_commit_hook.py`（两处）、`test_dispatch_context_warning.py`，另有已列的两个）都要加拷 `agate_package.py`——这些用例归批 E 的批内验收（E 的 `tests_filter` 之外另跑这三个文件，见 §5 备注）；P3 用 `grep -rn 'agate_common.py' agate/tests` 再核一遍，不依赖本清单。`test_bdd_30*` 撞名函数零改动，仅 `test_bdd_30_legacy_symlink_direct_root` 改写。
- **T-11 需调整的既有断言**（因 D-7）：3 处 `.installed-version` 断言删除；`--skip-python` 用例改为"任一情况下 `vX.Y.Z/python` 均不存在"；离线 copy-mode 用例改为验证 `--adopt` 结果。这些是契约收紧带来的有意变更，非回归。`test_install_offline.py::test_bdd_28*` 等**禁止全局 `mock.patch("subprocess.run")`**（会把 `--adopt` 子进程一并吞掉，eng G-2）：pip 用 PATH 内 `pip` shim 或 `monkeypatch` `install_wheels` 本身。
- **T-12 BDD-43/45**：真实 `opencode` / `codex` 缺 PATH → 该 BDD 判 FAIL（不跳过）。BDD-52 的 `agate-risk-score.py` 用例见 C-2。
- **T-13 资产口径（C-1，主 Agent 已裁决）**：BDD-13 ⑤ / 20 ② / 21 / 50 ⑥ 的测试与验收断言写作"3 个 tarball 名（本体 + 两平台 offline）⊆ 资产集合 且 `SHA256SUMS` ∈ 资产集合"，不断言资产总数恰为 3；P6 证据同口径。
- **T-14 软链守卫参数化（cso F-1，BLOCKER 级）**：BDD-31 / 32 / 33 对 `AGATE_HOME` / `--dest-root` 参数化 `["L", "L/", "L//", "L/.", "L/.."]`（`L` 为指向"含金丝雀文件的源仓库 `agate/`"的软链），四入口（`install.sh`、`agate-install.py`、`install-offline.py`、`agate-resolve.py` 的迁移提示）全部断言：exit 1、软链目标目录列表与金丝雀文件哈希不变；`L/..` 因"物理与文本解析不一致"同样被拒。
- **T-15 bundle 内入口（eng B-1 / G-1 / G-3）**：对真实 pack 产物 `subprocess.run([python, str(bundle/"agate/scripts/install-offline.py"), str(bundle), "--dest-root", …])`（**即真实内网机器的调用方式**），`pip` 用 PATH shim；装完断言 `bundle/agate` 与 `vdir/agate` 均无 `__pycache__`、checksum 通过。另留 1 条"真实树冒烟"：`git clone --local` 当前 worktree 到 tmp、打临时 tag，走 pack → install-offline → `agate-resolve.py`，仅 `pip` 打桩（可同时覆盖真实 `agate/` 内容里未来出现的新顶层目录）。
- **T-16 换位失败注入（cso F-5）**：`monkeypatch os.rename` 在 `swap_in` 第一步 / 第二步、`--adopt` 失败三处分别注入失败，断言"旧版本完整（或新版本完整），绝不出现两者皆缺"，且 **`latest` / `current` 指针与回滚后的目录一致**（adopt 子进程部分写入指针后失败的情形必须还原，eng N-2）；本工具遗留的 `.agate-tmp-*` 容器（有标记且 >1h）被下次安装清扫，遗留 `.agate-bak-*` 只提示 / 还原、不删除。
- **T-17 表驱动（eng G-6 / m-1、cso F-9 / F-11）**：`parse_release_ref` 拒绝 `v1.2.3\n`、`v١.٢.٣`（Unicode 数字）、`v1.2`、`vfoo`、`v1.2.3-`、`v1.2.3-a..b`，接受 `v0.73.0`、`v0.73.0-tagtest.1`；`list_package` 拒绝 `.git` / `.GIT` 分量、含 `:`、结尾空格或 `.`、大小写冲突、控制字符；`agate/Tests/` 与 `agate/tests/` 同样被排除。
- **T-18 CI/本地一致**：`agate-release.py build` 对合成 tag 与 v0.72.0 的产物与 `git show` blob 逐成员一致；同 tag 两次构建 SHA256 相同；`--expect-sha` 不匹配 exit 1；**`--expect-sha` 用例覆盖轻量 tag 与附注 tag 两种（附注 tag 的 tag 对象 SHA ≠ commit SHA），并断言传入 tag 对象 SHA 与传入 commit SHA 两种 `<SHA>` 均判等**（eng N-3）。
- **T-19 P 集合对账**：bundle 内多一个 / 少一个 / 改名一个 `agate/**` 文件，manifest `files` 对账均使 `install-offline` exit 1 且 `dest_root` 不变。
- **T-20 adopt 失败路径（cso F-6 / F-13）**：新形态版本目录含软链 / 顶层多余条目 / `tests/` → `--adopt` exit 1；`latest` 或 `current` 位置已是真实目录 → exit 1 且无 Traceback。
- **T-21 `compute_sha256` 字节码免疫（eng B-1 (b)）**：同一目录树在有 / 无 `__pycache__` 时哈希相同；`test_agate_common.py` 现有目录哈希用例保持通过（提供证据，因为这是共享单实现）。
- **T-22 `is-prerelease` / `build` 退出码**：`is-prerelease` 对正式 / 预发布 / 非法 tag 分别 exit 1 / 0 / 2（cso F-10）。
- **T-23 清扫只删自己的（cso N-1，数据安全，必测）**：版本根内预置以下条目，跑一次安装（触发 `sweep_stale` / `recover_backups`）后**全部原样保留**（内容哈希不变）：用户目录 `v0.73.0.bak-user`、`v0.73.0.tmp-x`、`.agate-tmp-user`（前缀相同但**无标记文件**）、`.agate-tmp-fake`（标记文件是软链或内容不符）、指向外部目录的软链 `.agate-tmp-link`、`.agate-bak-*` 备份容器（有标记也**不删**）；只有"前缀 + 真实目录 + 有效标记 + 标记 mtime >1h"的本工具容器被清扫（用 `os.utime` 把标记调成 2 小时前），且清扫后其外部无任何变化。另断言 `discard_backup` 拒绝路径不在版本根内 / 标记不符的目录。

---

## 7. gate_commands

说明：P3 只用裸 `P3`；P3 超时走 `AGATE_TDD_TIMEOUT`（全量套件建议 P3 阶段设为 300，不属 `_timeout_seconds`）；`P5_release_build` 用真实 tag v0.72.0 走真实构建入口（`--skip-offline` 免联网），输出落 /tmp；各键均为单条命令，无 `&&` 串联。

gate_commands:
  P3: "python3 -m pytest agate/tests/ -n auto"
  P3_formatter: "pytest.sh"
  P5: "python3 -m pytest agate/tests/ --reruns 1 -n auto"
  P5_timeout_seconds: 300
  P5_consistency: "python3 agate/scripts/check-protocol-consistency.py --strict-errors-only"
  P5_consistency_timeout_seconds: 120
  P5_ruff: "~/.venvs/agate-dev/bin/ruff check agate/"
  P5_ruff_timeout_seconds: 120
  P5_shellcheck: "shellcheck -S warning install.sh agate/scripts/*.sh"
  P5_shellcheck_timeout_seconds: 120
  P5_release_build: "python3 agate/scripts/agate-release.py build --tag v0.72.0 --repo . --outdir /tmp/tag0037-release-smoke --notes-out /tmp/tag0037-release-smoke.notes.md --skip-offline"
  P5_release_build_timeout_seconds: 600
---

## 8. files_to_read（P4 实现导航）

> 路径不带行号范围（易漂移，eng m-8）；所有 `why` 值加双引号（值内含冒号 / 方括号时不加引号会使 yaml 不可解析，eng M-1）。

```yaml
files_to_read:
  - path: agate/scripts/agate-install.py
    why: "批 B1a / B1b 主体：_install_version、_sync_root_scripts、_write_pointer、_cmd_check、_cmd_uninstall、_LEGACY_SYMLINK_MSG、降级 _protocol_root（不改）"
  - path: agate/scripts/install-offline.py
    why: "批 B2：main 流程顺序、_validate_manifest、verify_checksums、install_bundle、_ensure_agate_common（保持零依赖启动，入口须先设 dont_write_bytecode）"
  - path: agate/scripts/agate-pack-offline.py
    why: "批 B2：pack_offline、build_manifest（沿用 compute_sha256 目录约定）、pyyaml wheel 查找（改大小写无关）"
  - path: agate/scripts/agate_common.py
    why: "批 E：_resolve_pointer_chain、_protocol_root（不改）、_resolve_version_info、resolve_hook_root、compute_sha256（目录分支跳过字节码）"
  - path: agate/scripts/agate-resolve.py
    why: "批 E：终态失败分支附迁移提示"
  - path: agate/scripts/agate-summary.py
    why: "批 E：changelog_hint、启动建议文案、软链基址提示"
  - path: install.sh
    why: "批 E：重写对象；沿用现有 --versions 分支的软链守卫 heredoc 与 INSTALLER 探测；新增规范化与废弃 env WARNING"
  - path: agate/UPGRADING.md
    why: "批 F1a：版本管理生命周期节（对照表、层次图、解析优先级表、根 scripts 维护语义）；红线承诺（BDD-30 那句）与 v0.72.0 节格式"
  - path: agate/SETUP.md
    why: "批 F2：布局表与 $AGATE_DIR 取值"
  - path: .github/workflows/protocol-tests.yml
    why: "批 C2：workflow 风格参考（注意其 on 为 push 与 pull_request 数组，会被 tag push 连带触发）"
  - path: agate/tests/unit/test_agate_version_install.py
    why: "P3：_migration_steps 与 DEBT0034 跨入口一致性测试；夹具助手 _tag_upstream 的拷贝清单需加入 agate_package.py"
  - path: agate/tests/integration/test_version_lifecycle_e2e.py
    why: "P3：夹具助手 _tag_meta_upstream 的拷贝清单需加入 agate_package.py；AGATE_REPO_DIR 引用清理"
  - path: agate/tests/unit/test_hook_resolve_entry.py
    why: "P3：夹具拷贝 agate_common.py 的循环，须同时拷 agate_package.py（eng N-1）；test_pre_commit_hook.py 的两处拷贝与 test_dispatch_context_warning.py 的拷贝清单同理"
  - path: agate/tests/unit/test_install_offline.py
    why: "P3：_make_bundle 同源假设（待修正）；全局 mock subprocess.run 用法（须改为 PATH shim 或 monkeypatch install_wheels）"
  - path: agate/tests/regression/test_offline_bundle_roundtrip.py
    why: "P3：_fake_pack_artifacts 与 .installed-version 断言（待修正）"
  - path: agate/tests/unit/test_agate_common.py
    why: "P3：compute_sha256 现有目录哈希用例（改共享单实现须保持通过并留证据）"
  - path: agate/scripts/README.md
    why: "批 F2：脚本索引与信任边界段，新增 agate_package / agate-release 行"
  - path: AGENTS.md
    why: "批 F2：版本发布清单（增 Release 校验步骤、tag 保护建议）"
```

---

## 9. env_constraints

```yaml
env_constraints:
  debug_env: "隔离 AGATE_HOME + HOME=tmp_path；版本源用本地 file:// git 上游（AGATE_REPO_URL）；不联网；pip download / pip install 用 PATH 内 shim 或 monkeypatch install_wheels（禁止全局 patch subprocess.run）；BDD-43/45 的 HOME 保持真实仅供 opencode/codex 读自身配置，AGATE_HOME 与 $AGATE_DIR 指隔离布局"
  isolation_check: "测试前后真实 ~/.agate 内容哈希不变（金丝雀）；所有安装类测试的 AGATE_HOME / HOME 均为 tmp_path 子目录；软链守卫测试的金丝雀 = 源仓库文件哈希；BDD-20 推 tag / 删除 tag 与 Release 前须取得用户当次许可（属外部可见且含删除的操作，不在 P2 执行）"
  ci_tools: "actionlint 本机未装：BDD-20 降级路径需 pip install actionlint-py 或下载二进制；gh 已登录（P1 已实测，含 release delete --cleanup-tag --yes、create --verify-tag 标志）；shellcheck 已装"
```

> 边界提醒：`env_constraints` 是声明性字段，不被自动执行。需强制执行的约束均已落入 `gate_commands`（§7）或 P4 / P8 checklist：隔离金丝雀由测试断言承担（T-1 / T-4 / T-14），CI 推 tag 与清理的许可由主 Agent 在 P5/P6 执行前取得（§11）。

---

## 10. minimal_validation

```yaml
minimal_validation:
  environment: "scratchpad 内对本仓库 git clone 副本 + 合成仓库；git 2.43.0 / Python 3.12.3 / Linux(WSL2)；未触碰真实 ~/.agate"
  checks:
    - id: E-1
      assumption: "git archive + pathspec 白名单可作为单一构建入口（候选 B）"
      method: "git archive v0.72.0 -- agate LICENSE NOTICES.md CHANGELOG.md ':(exclude)agate/tests' ':(exclude,glob)**/__pycache__/**' …"
      result: "部分成立：集合正确（153 文件、tests 命中 0）；但见 E-2、E-3"
    - id: E-2
      assumption: "git archive 输出与 blob 字节一致（BDD-15 ③）"
      method: "合成仓库：属性 `*.md text eol=crlf`，及仅设 core.autocrlf=true（GIT_CONFIG_COUNT）两种条件下对比 archive / cat-file / show"
      result: "refuted：两种条件下 archive 均输出 CRLF，cat-file 恒为 LF"
    - id: E-3
      assumption: "登记根文件缺失于历史 tag 时构建不失败"
      method: "git archive v0.8.0 -- NOTICES.md …；自写构建器对 v0.8.0"
      result: "git archive: refuted（fatal 整体失败）；自写构建器: confirmed（50 文件，缺失文件跳过）"
    - id: E-4
      assumption: "export-ignore 方案对 GitHub 源码包 / 历史 tag 的影响（候选 A）"
      method: "副本仓库提交属性后 git archive（近似 GitHub 源码包语义）；对 v0.48.0 裸 archive 与 info/attributes 补救"
      result: "confirmed（有害）：带属性 tag 的 archive = 153/3390 文件；老 tag 裸 archive = 1203 文件（属性缺失）；info/attributes 补救可行但需改写 repo/.git（GitHub 侧行为未实测，属语义推断）"
    - id: E-5
      assumption: "候选 C 自写构建器：集合正确 / 字节一致 / 确定性 / 体积达标 / 速度可接受"
      method: "proto_pkg.py（ls-tree -z + cat-file --batch + tarfile PAX + gzip mtime=0）对 v0.72.0"
      result: "confirmed：153 文件（与 B 集合相同）；153/153 与 git show 字节相同；间隔 1s 两次构建 SHA256 相同；B=1,864,871 B（=P1 T-1 基线），tar.gz 647,370 B；0.11s；tree 内包区 0 软链 / 0 submodule / 无非 ASCII 路径；整 tag 36,976,767 B → 包 = 5.0%，1.25×B = 2,331,088 B"
    - id: E-6
      assumption: "portable（无 tests、无 git）可被解析链与启动摘要使用（BDD-17 前提）"
      method: "把 E-5 的 tar 解到 vroot/v0.72.0/，手建 latest/current、拷根 scripts/；PATH 仅含 python3 + coreutils（`command -v git` 失败）；运行 agate-resolve.py / agate-summary.py / agate-install.py --check"
      result: "confirmed：resolve exit 0，AGATE_ROOT=…/v0.72.0/agate，REASON=全局 current；summary exit 0（CHANGELOG 提示指向 vdir/CHANGELOG.md）；--check 默认口径缺 git → exit 1（符合 S-12 前提：需要 --portable 口径）"
    - id: E-7
      assumption: "排除 agate/tests 后包内脚本冒烟（BDD-52）"
      method: "在 E-6 目录内运行 check-platform-assumptions.py、agate-risk-score.py"
      result: "部分修正：前者 `FATAL: 目标不存在`、exit 2（无 Traceback，符合 BDD-52）；后者无参打印用法并 exit 1（非 git_ok:false 降级输出，见 C-2）"
    - id: E-8
      assumption: "gh 支持所需 release 标志"
      method: "gh release create --help"
      result: "confirmed：--notes-file、--prerelease、--verify-tag、--title 均存在"
    - id: E-9
      assumption: "（eng B-1）从版本目录内运行安装器会生成 __pycache__，防护手段有效"
      method: "exp-2：把 v0.72.0 包解到 4 份目录；分别以 无防护 / python3 -B / 入口顶部 sys.dont_write_bytecode=True（先于 import agate_common）运行 agate-install.py --check"
      result: "confirmed：无防护 → 生成 1 个 __pycache__；-B → 0；脚本顶部置位 → 0"
    - id: E-10
      assumption: "（eng B-1 / M-2）父进程置位 sys.dont_write_bytecode 会被子进程继承"
      method: "exp-2：父进程置位后以子进程运行 agate-install.py，分别 不带 -B 不带环境变量 / 设 PYTHONDONTWRITEBYTECODE=1 / 带 -B"
      result: "refuted（不继承）：无任何标志 → 子进程生成 1 个 __pycache__；环境变量 → 0；-B → 0。故子进程一律 -B 并设环境变量（D-13）"
    - id: E-11
      assumption: "（eng B-1）目录哈希对 pyc 出现敏感，且可通过跳过字节码免疫"
      method: "exp-2：agate_common.compute_sha256 对含 / 不含 __pycache__ 的同一本体目录求哈希；再用跳过 __pycache__ 与 *.pyc|*.pyo 的原型求哈希"
      result: "confirmed：现实现 92311b86… ≠ 5473087… （pyc 使哈希改变，即 install-offline 误报 agate 组件被篡改的机理）；跳过字节码后两者均为 5473087…"
    - id: E-12
      assumption: "（cso F-1）软链守卫可被尾斜杠 / 斜杠点 / 经软链的 .. 绕过，规范化可修复"
      method: "exp-1：legacy 软链 L→repo/agate；对 L、L/、L//、L/.、L/./、sub/ln2、L/scripts/..、L/.. 等变体比较 os.path.islink 原始值与 normalize_home（abspath + realpath 歧义检测）；bash 侧比较 [ -L ]、剥离尾部 / 与 /. 的循环、.. 分量探测"
      result: "confirmed 且已修复：原始 islink 对 L/ L// L/. L/./ 均为 False（守卫被绕过，与 cso 复现一致）；规范化后 norm_islink 全部为 True；L/.. 的 realpath(原始) ≠ realpath(规范化)（ambiguous=True）被拒；合法路径 repo/agate、repo/agate/、sub 均不误拒；bash：[ -L L ] 真、[ -L L/ ] 假，剥离循环后 L/ L// L/. L/./ L/.// 均为真，.. 分量探测可识别 L/.."
    - id: E-13
      assumption: "（cso F-11）新增路径硬化规则不会误伤真实历史 tag"
      method: "exp-3：对 69 个 tag 的包区运行规则（.git/.gitmodules 分量、冒号、结尾空格或点、casefold 冲突、Tests 大小写变体）"
      result: "confirmed：扫描 7127 个包内文件，0 违规"
    - id: E-14
      assumption: "（eng m-2）git archive 的 CRLF 一支可被 -c core.autocrlf=false 缓解，attribute 一支无解"
      method: "exp-3：合成仓库，GIT_CONFIG_COUNT 强制 core.autocrlf=true 时，对无属性 tag 与带 *.md eol=crlf 属性 tag 分别 git -c core.autocrlf=false archive"
      result: "confirmed：无属性 tag → LF（缓解成功）；带 eol=crlf 属性的 tag → 仍 CRLF"
    - id: E-15
      assumption: "（cso F-9 / F-14、T-3）parse_release_ref 用 fullmatch + ASCII 可拒绝换行与 Unicode 数字；gzip 头不泄露文件名 / 时间"
      method: "exp-3：表驱动 9 个 tag 名；GzipFile(mtime=0, filename='') 头字节"
      result: "confirmed：v1.2.3\\n、v١.٢.٣、v1.2、vfoo、v1.2.3-、v1.2.3-a..b 均拒绝；v0.73.0、v0.73.0-tagtest.1、v1.2.3-rc.1 接受；gzip FLG=0（无 FNAME）、MTIME=0、OS=255"
    - id: E-16
      assumption: "（cso F-2）可固定 pyyaml 版本，且 agate-pack-offline 的 wheel 查找与之兼容"
      method: "exp-3：联网 pip download --platform manylinux_2_17_x86_64 / win_amd64 --python-version 311 --only-binary=:all: --no-deps，分别 pyyaml==6.0.2、pyyaml==6.0.3 与不固定"
      result: "confirmed 且发现缺陷：6.0.3 两平台均可下载（当前最新，文件名小写 pyyaml-…）；6.0.2 的文件名是大写 PyYAML-…，现有 glob('pyyaml-*.whl') 在区分大小写的文件系统上会漏——故固定 6.0.3，并把 wheel 查找改为大小写无关"
    - id: E-17
      assumption: "（cso F-5 / eng m-4）备份改名 + 失败还原的换位序列在第二步失败时仍保持旧版完整"
      method: "exp-2：mkdtemp 备份 + 两步 rename 原型；对第二步 rename 注入 OSError"
      result: "confirmed：注入失败 → 回滚，目录仍为旧内容（old.txt）；正常路径 → 新内容，备份保留待 adopt 成功后删除"
    - id: E-18
      assumption: "（eng N-3）两侧 ^{commit} 剥壳后，轻量 tag、附注 tag 与 tag 对象 SHA / commit SHA 四种组合均判等"
      method: "exp-5：克隆合成仓库后创建轻量 tag v0.9.1 与附注 tag v0.9.0；分别把 refs/tags/T^{commit} 与 (tag 对象 SHA)^{commit}、(commit SHA)^{commit} 比较"
      result: "confirmed：附注 tag 的 tag 对象 SHA ≠ commit SHA；四种组合均相等"
    - id: E-19
      assumption: "（cso N-1）基于标记文件的 sweep 只删本工具容器，用户目录与无标记 / 软链 / 备份容器全部保留"
      method: "exp-5：在新建的版本根内预置 v0.73.0.bak-user、v0.73.0.tmp-x、.agate-tmp-user（无标记）、.agate-tmp-fake（标记内容不符）、.agate-bak-*（有标记）、.agate-tmp-link（软链）、未过 1 小时的 .agate-tmp-*（有标记），以及 1 个标记 mtime 为 2 小时前的本工具容器，运行 sweep 原型"
      result: "confirmed：仅那 1 个过期的本工具容器被删除，其余 7 个条目全部保留"
  not_validated:
    - "release workflow 在 GitHub Actions 上的真实运行（含 git clone 取源、pip install pyyaml、gh release create）：首次运行发生在 BDD-20 测试 tag（需用户许可）；本机仅做静态设计"
    - "offline 侧 pip download 的运行时行为（含 --python-version 311 在真实 CI runner 上的表现）：本机已验证 pyyaml==6.0.3 两平台 wheel 可下载（E-16），未在 GitHub runner 上验证"
    - "bsdtar / Windows tar 对含软链成员的解包行为（cso 只验证了 GNU tar 1.35）：设计上不依赖系统 tar 防护，install-offline 与 --adopt 自行 lstat 校验（D-16、§3.4 步骤 3）"
    - "Windows 侧构建器行为（二进制管道 / exec 位）：设计上规避（CI 在 Linux 构建），未实测"
  deps_pure_logic: "其余（is_packaged 规则、notes 提取、_register、install-offline 校验顺序、legacy 删除）为纯代码逻辑，依赖内部函数 agate_common._resolve_version_info / _resolve_pointer_chain / _protocol_root / compute_sha256 与 agate-install 的指针 / 根 scripts 同步。涉及删除分支的验证（T-8 之外）：删除 use_legacy 软链兜底后，原依赖该分支的请求（软链 → 协议本体）流向终态失败分支（root=None → agate-resolve exit 1），已读 _resolve_version_info 全文确认无其它兜底；软链 → 完整版本根经 current 链正常命中（os.path.join(base,'current') 穿过软链，_resolve_pointer_chain 可解析）"
```

---

## 11. CI 验证策略（BDD-20；P2 不执行）

> **⚠ 本节涉及外部可见操作与删除操作，均需主 Agent 在 P5/P6 执行前另行取得用户当次明确许可（一次许可覆盖一个具体清单，不做预授权）；只允许删除"本次创建的、名称精确匹配"的 tag / Release；不使用通配符，不遍历 `gh release list` 删除。**每一条 `gh` 命令都显式带 `-R "$REPO"`（cso N-2）：不带 `-R` 时 `gh` 依据当前目录的默认 remote 选仓库，在同时配置了 origin / fork / upstream 的工作副本里可能落到错误的仓库。**

**执行地点（cso F-7，首选 fork 演练）**：workflow 使用 `GITHUB_REPOSITORY`，天然可在个人 fork 运行——零对 origin 的通知 / Release 污染。**首选**在用户个人 fork 上演练（判定项与 P1 BDD-20 ①–④ 逐条相同，仅把 `origin` 换成 fork 的 remote；该执行地点需主 Agent 向用户确认，属对 BDD-20 "推到 origin"字面的口径澄清；fork 需先在 Actions 页启用 workflows）；**备选**才是 origin 演练（用户明确许可后）。origin 上 workflow 的首次真实运行始终由 v0.73.0 正式 tag 承担并在 P8 验收（BDD-21 / 50 ⑥）。

**目标仓库变量（cso N-2）**：`REPO=<owner/repo>` 由用户明确指定（演练 fork 或 origin），执行前主 Agent 回显并取得用户确认；随后断言 `gh repo view -R "$REPO" --json nameWithOwner --jq .nameWithOwner` 等于 `$REPO`，且 `git remote get-url <remote>` 指向同一仓库；之后**所有** `gh` 子命令（`run list` / `run cancel` / `release view` / `release download` / `release delete` / `release list`）一律写成 `gh … -R "$REPO"`，脚本化时用一个函数 `ghr() { gh "$@" -R "$REPO"; }` 强制统一，禁止裸 `gh`。

**前置**：release workflow 已在分支 HEAD 上（tag push 使用被打 tag 的提交上的 workflow 文件）；分支已推送到演练 remote；`gh auth status` 通过；分支 CHANGELOG 仍只有 `[Unreleased]`（走预发布回落）。

1. **基线与保护**：记录 `SHA=$(git rev-parse HEAD)`；设 `TAG=v0.73.0-tagtest.N` 并断言 `[[ "$TAG" =~ ^v0\.73\.0-tagtest\.[0-9]+$ ]]`；断言该名字在演练 remote **不存在**（`git ls-remote --tags <remote> "refs/tags/$TAG"` 为空、`gh release view "$TAG" -R "$REPO"` 报 not found）——存在则改用 `N+1`，**绝不复用或删除已存在的同名对象**。
2. **许可**：主 Agent 向用户列明将发生的外部可见效果——创建远端 tag、发布公开 prerelease（订阅者会收到通知、出现在 Releases feed）、触发连带 workflow（`protocol-tests.yml` 必触发，其余以实测为准）、产生**不可撤回**的 Actions run 记录——以及将要删除的**确切对象**（该 tag、该 Release）。取得许可后才继续。
3. 推送：`git tag "$TAG" "$SHA" && git push <remote> "refs/tags/$TAG"`。
4. **等待 workflow 结束（cso F-7 竞态）**：`gh run list -R "$REPO" --workflow=release.yml --commit "$SHA" --json databaseId,status,conclusion` 轮询到全部 `completed`（超时 15 分钟）；超时则 `gh run cancel <id> -R "$REPO"` 后继续轮询到 `completed`。**任何 run 仍为 `queued` / `in_progress` 时不得进入清理**。同时用 `gh run list -R "$REPO" --commit "$SHA"` 记录所有被连带触发的 workflow 及结论，写入 PR 描述（BDD-50 ③）。
5. 验证：`conclusion == success`；Release 存在、prerelease 标记、notes 首行为预发布标注；资产含 `agateon-$TAG.tar.gz`、`agateon-$TAG-offline-linux-x86_64.tar.gz`、`agateon-$TAG-offline-windows-x86_64.tar.gz`，另有 `SHA256SUMS`（C-1 口径）；`gh release download "$TAG" -R "$REPO"` 全部成功；`sha256sum -c SHA256SUMS` 通过；本地 `agate-release.py build --tag "$TAG" --repo . --skip-offline …` 的本体 tar 与下载的本体 tar **逐成员字节一致**；offline 资产解包后 `manifest.json` 的 `version == "v0.73.0"`、`source_ref == "$TAG"`、各组件 sha256 与 `files` 清单校验通过；**不**在真实环境跑 `pip install`。
6. **清理（无论上面是否失败都执行，且仅删本次创建的对象）**：
   1. 先**只读列出**将删除的对象（**删除前必列**）：`gh release view "$TAG" -R "$REPO" --json tagName,isPrerelease,createdAt`（断言 `tagName` 与 `$TAG` **字符串完全相等**、`isPrerelease == true`，且 `$TAG` 满足 `^v0\.73\.0-tagtest\.[0-9]+$`）；`git ls-remote --tags <remote> "refs/tags/$TAG"`（断言指向步骤 1 记录的 `$SHA`）；主 Agent 把这两条输出、`$REPO` 以及"将执行的两条命令"回显给用户确认；任何一项断言不成立即中止，不删除；
   2. 确认后逐条执行（无通配符、无循环）：`gh release delete "$TAG" -R "$REPO" --cleanup-tag --yes`（`--cleanup-tag` 与 `--yes` 已核对本机 `gh` 支持；`$TAG` 是单个精确名字，绝不使用通配符、不遍历列表）；`git tag -d "$TAG"`；
   3. 再次核对无复活：`gh release list -R "$REPO"` 无该 tag、`git ls-remote --tags <remote> "refs/tags/$TAG"` 为空、`gh run list -R "$REPO" --commit "$SHA"` 无新增 run（等待 60 秒后复核一次）、本地 `git describe --tags --abbrev=0` 不再返回它。**清理完成后**才可跑 CHECK 7 / BDD-49。
   4. Actions run 记录与已发出的通知**不可撤回**（`gh run delete <id> -R "$REPO"` 属另一项需单独许可的删除，默认不做）。
7. 失败处理：workflow 失败则修复后改用 `N+1`（不复用刚被删除的 tag 名）；同样先走步骤 1–2。
8. 降级（用户不许可推 tag / 演练 remote）：BDD-13~16 本地全链路 + `actionlint`；v0.73.0 正式 tag 的首次真实运行记为 P8 验收项，由主 Agent 提 `[BASELINE_CHANGE]`。

---

## 12. 完成标志（可判定）

1. `agate/UPGRADING.md` 契约小节含且仅含一个，且 fenced 块条目集合 == `agate_package.boundary_lines()`；`agate/scripts/agate_package.py` 存在且 stdlib-only（不 import `agate_common`）。
2. 对合成 tag 与 v0.72.0：`list_package` 得到的集合 == BDD-2 集合；三路径装后 `vX.Y.Z/` 递归文件集合（忽略字节码）逐一相等，且在 H2 / H3 运行过 `agate-resolve.py` 后仍相等；真实仓库 v0.72.0 在线安装后 `S ≤ 1.25×B`（B = 1,864,871 B）。
3. 离线 pack→install（**以 bundle 内 `install-offline.py` 为入口**）→`agate-resolve.py` exit 0，无 `agate/agate/`，安装前后 `bundle/agate` 与 `vdir/agate` 均无 `__pycache__`；旧格式 bundle exit 1 且不写目录；软链目的地（含 `L/`、`L//`、`L/.`、`L/..` 变体）exit 1 不穿透、源仓库文件哈希不变。
4. `agate-release.py build` 在合成 tag 与 v0.72.0 上产出的 tar：成员全为普通文件、无绝对 / `..` / 链接、与 `git show` blob 字节一致、同 tag 两次哈希相同；`--expect-sha` 不匹配 exit 1。
5. release workflow 静态断言全过（含 T-8 增补项）；测试 tag 实跑通过并已按 §11 清理（或降级并登记 `[BASELINE_CHANGE]`）。
6. `_resolve_version_info` 签名无 `use_legacy`；`agate_common.py` 无 `realpath(base)` 作根的分支；BDD-37 grep 测试通过，R 集合 12 文件 0 命中；`git diff 75a8102..HEAD` 对 out-of-scope 文件为空。
7. 全量 pytest（CI 口径）失败 0，`passed ≥ 1842`，`skipped ≤ 2`；consistency（含本文件 yaml 块可解析）/ ruff / shellcheck 全绿；新增脚本已登记 `agate/scripts/README.md`。
8. 换位失败注入（T-16）与软链守卫参数化（T-14）全过；`compute_sha256` 字节码免疫（T-21）且现有哈希用例通过。

---

## 13. 需要主 Agent 知悉 / 处置

**C-1（已采纳）**：Release 共 **4 个资产**（3 个 tarball + `SHA256SUMS`）。BDD-13 ⑤ / 20 ② / 21 / 50 ⑥ 读作"至少这 3 个 tarball 名 ∈ 资产集合，另有 `SHA256SUMS`"，不改 P1；已记入 §4（BDD-21 行）与 §6（T-13）。

**升级自举缺口（不作代码改动，已按裁决降为文档）**：≤v0.72 用户用旧安装器升级得到的 v0.73.0 自身为旧整仓形态（仍可解析），之后经同步后的根 `scripts/` 执行的安装均只装本体——由 UPGRADING `### v0.73.0` 节说明（§3.8、R-1）。`install.sh` 仅保留：无参 = `--versions` 别名、软链守卫（含规范化）、废弃 env WARNING（§3.7）。未新增 BDD。

**C-2（已采纳为 P3 提示）**：BDD-52 写 `agate-risk-score.py`"按其既有 `git_ok: false` 降级输出"。实测（E-7）无参调用打印用法并 exit 1，无 Traceback。P3 用例同时覆盖"无参 → 用法、无 Traceback"与"传入一个 TASK_DIR"两种调用，仍满足 BDD-52 的"无 Traceback + 退出码落在既有契约内"。

**需主 Agent 向用户确认的事项（§11）**：① BDD-20 是否改在个人 fork 上演练（首选，判定项不变）；② 无论 fork 还是 origin，推 tag 与删除该 tag / Release 都需当次明确许可，且删除仅限本次创建、名称精确匹配的对象。

**backlog 建议（不属本任务范围，待用户确认后另立项）**：
- `install.sh` 重跑时对已存在的 `repo/` 做 `git pull --ff-only`（失败仅 WARNING），使随后使用的是最新安装器；如立项需配套一条 BDD 与 packages（install-sh、agate-docs）。
- `_sync_root_scripts` 仅当被装版本 ≥ 当前 `current` 解析出的版本（或本次移动指针）时才同步根 scripts（eng m-5：避免钉老版本回退根安装器）；本任务只在 UPGRADING 写明。
- `pip` 调用改 `sys.executable -m pip`、删除 `install.sh` 的 `$SCRIPT_DIR` 回退（cso F-13 后两项）。
- Release 构建依赖启用 `pip --require-hashes`（带哈希的 requirements）；来源证明（`gh attestation` / sigstore，需 `id-token: write` 与官方 action，与本任务"零 action / 唯一权限"冲突）；`v*` tag 保护 / Ruleset（本任务仅在 AGENTS.md 发布清单写建议）。
- 并发安装文件锁（本任务仅文档声明不支持并发安装同一版本根）。

**frontmatter**：`agent`、`dispatch_plan` 为 `agate-md-field-set` 拒绝的键，已按授权手写；本次重试仅按 eng M-4 调整了 `dispatch_plan` 内容（批次依赖 / 拆批 / `tests_filter` / `mode: serial`），其余键未动。

**已知取舍摘录**：D-7（删 `.installed-version` / `.agate-root` / 嵌入式 python 不入版本目录）与 R-10（`AGATE_HOOK_COPY_MODE` 不再影响版本根指针）会让 P3 需调整少量既有断言（T-11），均因"契约收紧"而非回归。

---

## 14. 评审处置表（重试 #1）

> 状态：已采纳 = 已落入设计（给出章节）；不采纳 = 给出理由 / 证据。BLOCKER / HIGH / MAJOR / MEDIUM 无一"不采纳"。

### 14.1 plan-eng-review（`P2-review-eng.md`）

| 编号 | 处置 | 落点 / 理由 |
|------|------|------------|
| B-1 `__pycache__` 污染 | 已采纳 | D-13、R-13；§3.1（安装态 vs 运行后态）、§3.2、§3.3、§3.4 步骤 0 / 5 / 8、§3.5（`python3 -B`）、§3.6；`compute_sha256` 跳过字节码（§1.1 agate_common 行）；实验 E-9 / E-10 / E-11；测试 T-4 / T-15 / T-21；完成标志 §12(2)(3) |
| M-1 §8 yaml 不可解析 | 已采纳 | §8 全部 `why` 加双引号、去掉行号范围；改完已跑 `check-protocol-consistency.py --strict-errors-only`（见 §14.3） |
| M-2 `--adopt` 执行主体 | 已采纳 | D-4、§3.3（`--adopt` 执行主体规则）、§3.4 步骤 8（兄弟安装器 + `-B` + 环境变量）；T-1（合成 tag 不必内嵌安装器） |
| M-3 夹具不含 `agate_package.py` | 已采纳 | §1.1 测试面行、§6 T-10（澄清"函数体不改、夹具助手允许增拷文件"并点名 `_tag_upstream` / `_tag_meta_upstream`）、§8 files_to_read |
| M-4 批次依赖与验收 | 已采纳 | §5：C 依赖 B2、B2 依赖 B1b 与 E；拆为 B1a/B1b、C1/C2；每批 `tests_filter` 与"批内 vs 波次末"验收；F1b 并入 F2；`mode: serial`、`parallel_limit: 3`（frontmatter 已更新） |
| M-5 同源假设留口子 | 已采纳 | T-15（bundle 内入口 + 真实树冒烟）、T-11（禁止全局 patch `subprocess.run`）、T-19 |
| m-1 `parse_release_ref` 正则 | 已采纳 | §3.2（`fullmatch` + `re.ASCII` + 后缀拒绝 `..`）、`_VERSION_RE` 改 fullmatch 口径（§3.3）；E-15；T-17 |
| m-2 候选 B 证据夸大 | 已采纳 | §2 候选 B 硬伤 1 订正（`-c core.autocrlf=false` 可缓解 autocrlf 一支；attribute 一支无解）；选择理由重心改为三点；E-14 复现 |
| m-3 `agate_home()` 两份实现 | 已采纳 | R-3、§1.1（`agate_common` 改 `from agate_package import agate_home`）、D-14 |
| m-4 换位回滚 / worktree prune | 已采纳 | D-6、§3.4 步骤 7–9、§3.3 `--uninstall`（只要 `repo/` 存在即 `worktree prune`）；E-17；T-16 |
| m-5 老 tag 预装回退根 scripts | 部分采纳 | 不改代码（既有语义、范围锁定）；UPGRADING v0.73.0 节写明（§3.8）；列 §13 backlog |
| m-6 `symlink_base` 键 | 已采纳 | §3.7（env 早返回分支同样带 `symlink_base=False`）、§1.1 |
| m-7 portable 命令合并 / 校验 | 已采纳 | §3.5（`mkdir` 不加 `-p` 使已存在即失败；加 `sha256sum -c`） |
| m-8 `files_to_read` | 已采纳 | §8（去行号、补两个夹具助手与 `test_agate_common.py`） |
| G-1 bundle 内入口 | 已采纳 | T-15 |
| G-2 全局 patch `subprocess.run` | 已采纳 | T-11 |
| G-3 真实树冒烟 | 已采纳 | T-15（第二部分） |
| G-4 使用后再比较 | 已采纳 | T-4 |
| G-5 契约外顶层文件不拷 | 已采纳 | T-6、T-19、§3.4 步骤 3（对账） |
| G-6 `parse_release_ref` 表驱动 | 已采纳 | T-17 |

### 14.2 cso（`P2-review-cso.md`）

| 编号 | 处置 | 落点 / 理由 |
|------|------|------------|
| F-1 HIGH 软链守卫尾斜杠绕过 | 已采纳（实测复现后设计） | D-14、R-14；§3.2（`normalize_home` / `is_symlink_base` / `agate_home` 规范化，覆盖尾 `/`、`/.`、多余斜杠、文本 `..`、经软链的 `..`）；§3.3 / §3.4 步骤 1 / §3.7（`agate_common`、`install.sh` 规范化 + 拒绝 `..`）；实验 E-12（本轮复现绕过并验证修复）；T-14。**部分不采纳**：cso"纵深防御——`realpath(agate_home)` 含 `.git` 祖先目录时拒绝"：`$HOME` 本身是 dotfiles git 仓库的用户会被误拒 `~/.agate`，且 F-1 主修复已消除绕过，故不做 |
| F-2 MEDIUM token 暴露 + 依赖未固定 | 已采纳 | D-15、§3.6（`GH_TOKEN` 仅 Publish 步骤 env；`PYYAML_PIN = 6.0.3` + `--only-binary=:all:`，workflow 与 `agate-pack-offline` 同源；notes 列 wheel 名与 sha256）、R-7；E-16；T-8。build / publish 拆两个 job 不采纳（需 `download-artifact` action，违反零 action，cso 亦不推荐）；`--require-hashes` 列 backlog |
| F-3 MEDIUM tag 移动 | 已采纳 | §3.6 `build --expect-sha "$GITHUB_SHA"`；T-18 |
| F-4 MEDIUM 完整性局限 | 已采纳 | D-15、R-16；§3.5（portable 增 `sha256sum -c` 与局限说明）、§3.6 notes 头；`install-offline` 文案改"不一致（损坏或被替换）"（§3.4 步骤 4）；manifest `files`（路径名纳入校验，弥补目录哈希不含路径名）（D-5、§3.4）；来源证明列 backlog |
| F-5 MEDIUM 换位回滚 / 并发 / 残留 | 已采纳（并发文档化） | D-6、R-8、R-15；§3.2（`swap_in` / `rollback_swap` / `sweep_stale`，`mkdtemp`）、§3.4 步骤 5–9；E-17；T-16。**并发锁不实现**：单用户工具、跨平台文件锁复杂度不成比例，文档声明不支持并发安装同一版本根（R-8，backlog）；Windows rename 失败即整体失败并回滚 |
| F-6 MEDIUM 根入口 / P 集合 / `--adopt` 校验 | 已采纳 | §3.4 步骤 3（`lstat` + `followlinks=False` + manifest `files` 对账）、§3.2 `copy_files`、§3.3（`--adopt` 调 `verify_dir`、`copytree(symlinks=True)` 且忽略字节码）；T-6 / T-19 / T-20 |
| F-7 MEDIUM 测试 tag 清理竞态 | 已采纳 | §11 全文重写：fork 演练首选；等 run 全部 `completed`（或先 `gh run cancel`）才清理；删除前只读列出并回显确认、名称精确匹配 `^v0\.73\.0-tagtest\.[0-9]+$`、无通配符、仅删本次创建；副作用（通知 / run 记录不可撤回）向用户披露 |
| F-8 LOW 迁移提示硬编码 `~/.agate` | 已采纳 | §3.3、§3.7（三步片段前增动态"检测到的软链"行，不影响 `_migration_steps` 正则） |
| F-9 LOW 正则 `$` 换行 | 已采纳 | §3.2、§3.4 步骤 2（`_validate_manifest` 切 `parse_release_ref`；`source_ref` 校验后才展示、不入路径）；T-17 |
| F-10 LOW `is-prerelease` exit 2 被吞 | 已采纳 | §3.6 Publish 步骤 `case "$rc"` 三分支；T-8 / T-22 |
| F-11 LOW 路径硬化 | 已采纳 | D-16；§3.2（`.git*`、`:`、结尾空格/点、控制字符、casefold 冲突、`tests` casefold 排除、`O_EXCL|O_NOFOLLOW`）；E-13（真实历史 0 违规）；T-17 |
| F-12 LOW portable 命令鲁棒性 | 已采纳 | §3.5（`AGATE_HOME` 默认值 + 软链 shell 守卫在解压前、`mkdir` 无 `-p`） |
| F-13 LOW 其余小项 | 部分采纳 | 采纳：`_cmd_adopt` 的 `OSError` 转 stderr + exit 1（§3.3）、`git clone -- <url>`（§3.3、§3.7）。**不采纳**：`pip` 改 `sys.executable -m pip` 与删除 `install.sh` 的 `$SCRIPT_DIR` 回退——既有行为、范围锁定，且改 `pip` 调用会使 eng G-1 / G-2 建议的 PATH-shim 测试手法失效（§1.2）；列 §13 backlog |
| F-14 LOW workflow 静态测试增补 | 已采纳 | §3.6 静态契约、T-8；tag 保护建议写入 AGENTS.md 发布清单（F2 批，§1.1 / §3.6） |

### 14.3 自检记录

- `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`（worktree 自带脚本）：**0 ERROR**（仅 367 个既有 WARNING，rc=0）；本文件全部 4 个 yaml 块（workflow 草案、files_to_read、env_constraints、minimal_validation）经 `yaml.safe_load` 解析通过；`check-frontmatter.py` rc=0；`dispatch_plan` 经 `check-gate.py` 的 `_gate_p2_dispatch_plan` 校验通过（9 批，`mode: serial`）。
- frontmatter 除 `dispatch_plan` 内容外未动；仓库内除本文件与 `P2-progress.md`（追加）外无新增文件。

### 14.4 非阻塞增补项（两位评审均 approved 后的处置）

| 编号 | 处置 | 落点 / 理由 |
|------|------|------------|
| cso N-1（数据安全）`sweep_stale` 不得按名字删除 | 已采纳 | R-8 重写；§3.2（`TMP_PREFIX` / `BAK_PREFIX` / `MARKER_NAME`、`make_work_dir` / `sweep_stale` / `recover_backups` / `discard_backup` 语义）；D-6；§3.3 / §3.4 步骤 5 / 9。**只删本工具创建的临时容器**：专属前缀 `.agate-tmp-` + 真实目录（`lstat`，不跟随软链）+ 内部专属标记文件且首行校验 + 标记 >1h；**永不触碰** `vX.Y.Z.bak-*`、`vX.Y.Z.tmp-*`、无标记的同前缀目录、软链及任何用户目录；备份容器不被 sweep 删除（可能是崩溃后唯一完整的旧版），只由 `recover_backups` 改名还原或提示、由 `discard_backup` 在 adopt 成功后删除本次自己创建的那一份。测试 T-23（用户目录 `v0.73.0.bak-user` 等预置条目全部保留） |
| cso N-2 `gh` 命令显式 `-R` | 已采纳 | §11 新增 `REPO` 变量（用户确认 + `gh repo view` / `git remote get-url` 断言）与 `ghr()` 统一封装；所有 `gh` 子命令带 `-R "$REPO"`；删除前必列对象、`$TAG` 精确匹配 `^v0\.73\.0-tagtest\.[0-9]+$` 且与 `tagName` 字符串全等、单对象命令无通配符 |
| eng N-1 夹具拷贝清单扩展 | 已采纳 | §1.1 测试面行、§6 T-10、§5（批 E 追加验收：`test_hook_resolve_entry.py` / `test_pre_commit_hook.py`（两处）/ `test_dispatch_context_warning.py`）、§8 files_to_read；已用 `grep -rn 'agate_common.py' agate/tests` 核对来源，P3 须再核 |
| eng N-2 adopt 回滚含指针 | 已采纳 | D-6、R-15；§3.2（`snapshot_pointers` / `restore_pointers`）、§3.3（`_register` 自身事务化）、§3.4 步骤 7–8（换位前快照，adopt 失败 `rollback_swap` + `restore_pointers`）；T-16 断言指针与目录一致；根 `scripts/` 同步放在指针之后且失败仅 WARNING（不可回滚项已显式说明） |
| eng N-3 `--expect-sha` 附注 tag 用例 | 已采纳 | §3.6（两侧 `^{commit}` 剥壳比较）；T-18（轻量 / 附注 tag，传 tag 对象 SHA 与 commit SHA 均判等） |
| eng N-4 summary 迁移提示仅在无根时打印 | 已采纳 | §3.7 `agate-summary.py`（`root is None and symlink_base` 才打印；BDD-51 软链→完整版本根不打印） |

**自检（本次增补后重跑）**：`python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` 0 ERROR；frontmatter 未改动；仓库内除本文件与 `P2-progress.md`（追加）外无新增文件；新增 scratchpad 目录 `exp-5`（仅放补丁脚本）。
