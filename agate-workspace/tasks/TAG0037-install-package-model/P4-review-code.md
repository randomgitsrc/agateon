---
agent: review
phase: P4
task_id: TAG0037
type: review
parent: P4-implementation.md
trace_id: TAG0037-P4-review-code-20260920
created: '2026-09-20'
status: approved
---
# P4-review-code — TAG0037 安装与多版本模型统一（实现评审）

[PROD_NOT_TOUCHED] 只读评审：未改任何仓库文件（本文件除外）、未 git add / commit、未触碰真实 `~/.agate` / 开发 checkout / git 分支与 tag；未追加 `P4-progress.md`（用户指令"除输出文件外不改仓库文件"优先于 dispatch-prompt 的落盘约定）。全部实验在 scratchpad `rv-01`…`rv-04`（见文末），HOME / AGATE_HOME 均重定向到 scratchpad；无删除类操作（仅对本轮自己创建的实验目录不做任何清理）。

**结论：approved。0 个 BLOCKER / 0 个 MAJOR / 5 个 MINOR / 3 个 INFO。**
实现忠实于 P2 设计与抽查的 BDD；P0 真 BUG（离线安装解析失效）在**真实 pack 产物结构**上修复成立；兼容红线成立；[DESIGN_GAP] 四项均可接受。MINOR 均为文档陈旧 / 可维护性 / 追溯类，不阻塞 P5，建议在 P4 提交前顺手吸收。

## 0. 实测证据（可复现）

| 项 | 命令 / 方法 | 结果 |
|----|------------|------|
| 全量测试 | `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest agate/tests -q -p no:cacheprovider`（rv-01） | **2291 passed / 1 failed / 2 skipped**；唯一失败 `test_t15_real_tree_smoke_pack_install_resolve`（与 dispatch 所述一致） |
| t15 提交后转绿的独立验证 | 把 HEAD 克隆到 scratchpad（`rv-03/clone`，`git clone --no-hardlinks` 只读源），rsync 工作区改动进克隆并**在克隆内**提交，再跑 `test_install_three_paths.py` + `test_offline_real_pack_resolve.py` + `test_no_legacy_residue.py` | **46 passed**：失败原因确为「bundle 内自带的 HEAD 旧 `install-offline.py`」（报错文案仍是旧的"被篡改或损坏"），提交后必转绿，P5 复核即可 |
| ruff | `ruff check agate/` | All checks passed |
| shellcheck | `shellcheck -S warning install.sh agate/scripts/*.sh` | 0 告警 |
| 协议一致性 | `check-protocol-consistency.py --strict-errors-only` | 0 ERROR（367 既有 WARNING） |
| Python 3.8 语法 | `ast.parse(feature_version=(3,8))` 八个脚本 | 通过 |
| maintainability | `check-maintainability.py` 是 diff（staged）驱动，当前无暂存 → "git 通道不可用"；改为人工核对：新增文件 849 / 523 / 365 行（< 1000），`agate_common.py` 1077→1107（存量已超线，非"跨越"），新增代码 `except:` / `# type: ignore` 命中 0 | 无 violation 预期；无需 `known-violations.md`（文件不存在，符合 RM-AG0046 三重门槛） |
| import 开销 | `python3 -X importtime -c "import agate_package"` | 累计约 13 ms（`agate_common` 现在硬依赖它，可忽略） |

## 1. 实现是否忠实于设计与 52 BDD（抽查）

真实链路实验（rv-02：把当前工作区 `agate/` + 登记根文件提交进合成仓库并打 tag `v9.9.9`（轻量）/ `v9.9.10`（附注）/ `v9.9.10-rc.1`，PATH 前置 pip shim，其余全部为**真实执行**）：

| BDD | 实测 / 读码结论 |
|-----|----------------|
| BDD-9 / 11（P0 真 BUG） | 真实 `agate-pack-offline.py` → bundle 顶层 = `agate/` + `CHANGELOG.md LICENSE NOTICES.md` + `wheels/` + `manifest.json`（**无** `agate/agate/` 双层）；以 **bundle 内入口** `<bundle>/agate/scripts/install-offline.py` 安装 → `agate-resolve.py` exit 0，`AGATE_ROOT=<dest>/v9.9.9/agate`，`AGATE_VERSION=v9.9.9`。bundle 运行后 `find -name __pycache__` 为空（`dont_write_bytecode` 生效）。不是假 bundle。 |
| BDD-2 / 3 / 4 | 三路径同构：在线安装的 `v9.9.10/`、离线安装的 `v9.9.9/`、Release 本体 tarball 解压物三者 `diff -r` 逐字节一致（`SAME_AS_OFFLINE` / `SAME_AS_ONLINE`）；顶层仅 `agate/ CHANGELOG.md LICENSE NOTICES.md`；无 `docs/ site/ agate/tests`。 |
| BDD-12 | 篡改 bundle（加 `agate/zz.txt`）→ `install-offline` exit 1，报"磁盘多出（manifest.files 未登记）"；旧格式与缺 `files` 读码为 fail-closed。 |
| BDD-14 / 15 | `build --tag v9.9.10`（CHANGELOG 无 `[9.9.10]` 段）→ exit 1 且**未创建 outdir**（fail-closed 先于任何写入）；预发布 `v9.9.10-rc.1` 回落 `[Unreleased]` 并带"预发布测试"首行；`SHA256SUMS` `sha256sum -c` 通过；同 tag 连续构建两次 tarball `cmp` 一致（`DETERMINISTIC`）；tar 成员 uid/gid 0、mode 归一。 |
| BDD-22 / 23 / 24 | 读码：`_validate_relpath`（`.git*` / `:` / 尾空格与点 / 控制字符 / casefold 冲突）、`list_package` 拒软链 / 子模块（仅 100644/100755 blob）、`materialize` 用 `cat-file --batch` 原始 blob + 哈希复核 + `O_EXCL|O_NOFOLLOW`；`is_packaged` 默认拒绝；老 tag 缺登记根文件被容忍。 |
| BDD-27 / 28 / 51 | 软链→协议本体（旧 legacy）：`agate-resolve` exit 1 + 迁移三步（首行动态"检测到的软链"）；`agate-summary` 无根且软链时打印迁移提示；软链→完整版本根：`AGATE_ROOT` 正常解析（exit 0）。`_resolve_version_info` 已无 `use_legacy`、无 `realpath(base)` 作根分支。 |
| BDD-29 / 30 / 31 | `install.sh`：无参 = `--versions`、废弃 env WARNING、其他参数 exit 2；`AGATE_HOME=…/L2/..`（经软链的 `..`）被 `*/../*` 分支 exit 1（先于任何 git 调用）。 |
| BDD-32 / 33 | 软链守卫：本人对 `install-offline` 实测 `L` / `L/` / `L//` / `L/.` 均 exit 1（其余入口的 T-14 五变体参数化由既有测试覆盖且全绿）；**经软链的 `..`（`L2/..`，L2 → `real/deep`，物理位置 `real` ≠ 文本位置）**对 `install-offline` 与 `agate-install --adopt` 均 exit 1 并打印"物理位置"，源仓库树无写入。（注：我最初用的 `L → real` 夹具中 `L/..` 物理与文本重合，属夹具退化，不是缺陷，已改用 `L2` 复测。） |
| BDD-34 / 35 | `agate_common.symlink_migration_hint`、`agate-install`、`install-offline`、`install.sh` 四处三步文本逐行相同（目检 + `test_bdd_35_*` 跨入口比对通过）。 |
| BDD-37 / 38 | `use_legacy` 仓库内（除 debt 叙事与任务目录）0 命中；`AGATE_REPO_DIR/AGATE_SYMLINK` 仅 `install.sh` WARNING 一处与历史文档。BDD-38 的 4 个 legacy 测试处置见 §4。 |

## 2. 兼容红线

- **`agate_common._protocol_root` 函数体零改动**：用 `ast.get_source_segment` 对比 HEAD 与工作区，`True`；`git diff -U0` 的 hunk 起点（`@@ -182,2 +184,28`）也在该函数之后。`agate-install.py` 内降级副本同样 `True`。探测序（`vdir/scripts` → `vdir/agate/scripts`）未变。
- **已装旧形态可解析（BDD-5 / 7）**：rv-04 手工构造旧 worktree 形态（`v0.60.0/{agate,docs,agate-workspace,.git}` + 文本指针）：`agate-resolve` exit 0，`AGATE_ROOT=…/v0.60.0/agate`；`--adopt` 对含 `.git` 的旧形态跳过 `verify_dir` 正常纳管；`agate-install.py v0.60.0` 走"已安装，跳过（幂等）"。
- `resolve_hook_root` 兜底（脚本路径上溯 + `.agate-root`）保持（S-17），仅去掉 `use_legacy=False` 实参与措辞。
- hook 三件套 / SELF-GATE / `.state.yaml` schema / `rules/*.yaml` / `install-hook.py` / 现有 4 个 workflow 均无 diff（`git status` 核对）。
- `agate_common` 现在模块级 `from agate_package import …`：所有把 `agate_common.py` 拷到别处的生产路径均拷整个 `scripts/`（`_sync_root_scripts` 单次 copytree；hook 只拷薄壳、解析入口在 `<root>/scripts/`），无生产缺口；测试夹具缺口已由 P3/F2 补齐（全量绿）。

## 3. 代码质量

**3.1 单一来源成立**：全仓 `tarfile` / `ls-tree` / `cat-file` / `git archive` 只出现在 `agate_package.py`（`check-mvwu.py` / `pre-commit-gate.py` 的同名 git 调用与本任务无关）；`git worktree add` 已从两处代码中删除；三路径都经 `list_package → materialize → write_dir_tarball`。workflow 内零打包逻辑。stdlib-only、Python 3.8 语法、显式 UTF-8、平台无关（`_O_NOFOLLOW`/`_O_BINARY` 兜底、`os.name == "nt"` 文本指针）。

**3.2 换位 / 回滚 / 指针一致性（eng M-2 / N-2、D-6）**：实测两条关键事务。
- 旧目录被"脏"覆盖后重装：`v9.9.9/agate/extra.txt` 被替换掉，备份容器与工作容器均已收尾，dest 下无 `.agate-*` 残留。
- adopt 失败回滚：预置 `latest/` 为**目录**（令 `_write_pointer` 抛 `IsADirectoryError`）、`current` 为文本文件、`v9.9.9/` 含 `old.txt`：`install-offline` exit 1，stderr 明示"版本目录与 latest/current 指针均已还原"；事后 `v9.9.9/agate/scripts/old.txt` 仍在、`current` 内容仍为 `cur`、`latest/` 目录未被删除、无遗留备份容器。
- 数据安全：全部 `rmtree` 点已逐个核对——`agate-install._cleanup_container` / `install-offline._cleanup_own_container` / `agate-pack-offline._cleanup_own_container`（前缀 + 直属根 + 真实目录，且仅对本进程刚建的容器调用）、`sweep_stale`（前缀 + 真实目录 + 有效标记 + 标记 >1h）、`discard_backup`（前缀 + 标记 + 本进程 `_CREATED_BACKUPS`）、`rollback_swap`（见 M-3）、`agate-release.build` 的 `mkdtemp` 暂存目录。无按名字模式删除。

## 4. legacy 删除完整性 / [DESIGN_GAP] 裁定

- `use_legacy` 清除；解析链仅三层（`AGATE_REASON` 取值集合 ⊆ {env, `.agate-version`, `全局 current`}）；`resolve_hook_root` 兜底保留。
- 文档：UPGRADING 的契约小节 / portable 小节 / `### v0.73.0` / 解析表 5→3 层 / v0.50.0 三处红线承诺改写，与 BDD-37 / 39 / 40 一致；`agate/SETUP.md` 去 fallback 后 `$AGATE_DIR="$HOME/.agate/current/agate"` 缺失时明确失败。
- BDD-38：`test_bdd_30_legacy_symlink_direct_root` / `test_debt0042_agate_home_legacy_symlink` 已改写为 `test_bdd_27_symlink_home_fail_closed` / `test_debt0042_agate_home_symlink_fail_closed`（fail-closed 断言）；`test_tag0032_bdd_1_*` / `bdd_2_*` 保留；撞名 `test_bdd_30_*`（`test_tag0034_events.py`、`test_codex_platform_docs.py`、`test_install_sh.py` 新增的三个）函数体未动；F2 授权改动的四个测试文件 diff 只有字面量拼接 / docstring / 一个函数改名，断言语义不变（`removed_param = "use_" + "legacy"`、`_STALE_ENTRY`），未削弱。

[DESIGN_GAP] 裁定：

| 项 | 裁定 | 理由 |
|----|------|------|
| `discard_backup` 拒绝路径返回 False + stderr 警告 | **可接受** | adopt 成功之后的清理步骤不应因此使已成功的安装报错；目录原样保留，符合"宁留不删"；install-offline 调用处忽略返回值可接受（仅遗留一个带标记的备份容器，`recover_backups` 会提示）。 |
| `rollback_swap` 对新目录的处置（移入 `failed-new/` 后删除，且仅备份为本进程创建且标记有效时回滚） | **可接受，附 M-3** | 与 D-6"旧版完整或新版完整"一致；无备份分支的 `rmtree(final)` 缺来源校验，见 M-3。 |
| `make_work_dir` 根目录不存在时 `makedirs` | **可接受** | 离线安装到全新 `--dest-root` 的必要行为；软链守卫在所有入口均先于它；`install-offline` 失败路径只 `os.rmdir(dest_root)`（仅空目录才成功）回收本次刚建的根，实现正确。 |
| `pack` 输出目录已存在则拒绝覆盖 | **可接受** | 实测同一 `--outdir` 二次打包 exit 1、提示换目录；`agate-release build` 每平台用全新 `pack-<platform>` 目录，CI / 本地补救均不受影响。行为变化已写入 `P4-implementation.md`，建议 P8 前在 CHANGELOG 变更节补一句（见 I-2）。 |

## 5. Release workflow / release CLI

- `on.push.tags: ['v*']` 唯一触发；`permissions: contents: write` 唯一权限；零 `uses:`；`GH_TOKEN` 仅 Publish 步骤 env；`--verify-tag` + `--expect-sha "$GITHUB_SHA"`（两侧 `^{commit}` 剥壳，轻量 / 附注 tag 均对）；`is-prerelease` 的 rc 走 `case` 三分支，exit 2 显式失败；`--depth 1` 浅克隆下 `refs/tags/<TAG>`、`ls-tree`、`git show tag:CHANGELOG.md`、`git log -1 --format=%ct` 均可用；`--notes-out` 禁止落在 `--outdir` 内；outdir 非空拒绝。实现与 P2 §3.6 草案一致。
- 静态可判定部分无问题；真实 CI 首跑（BDD-20）属 P5 / P6，需用户许可后用 `v0.73.0-tagtest.N` 或 fork 演练——本评审未推 tag、未触发 CI。

## 6. 发现清单

### BLOCKER
无。

### MAJOR
无。

### MINOR

**M-1 `agate/scripts/README.md` 脚本索引仍描述旧机制（文档陈旧）**
`agate/scripts/README.md:71`（`agate-install.py` 行）仍写"repo 单克隆 + **worktree add tag**""`--uninstall` = 删版本目录 + **worktree remove**"，且缺 `--adopt` / `--check --portable`；`:73`（`agate-pack-offline.py` 行）缺 `--ref`；`:75`（`install-offline.py` 行）仍写"建 `~/.agate/vX.Y.Z/` + hook/orchestrator 指向 + 验证闭环"，与现实现（本体包 + 兄弟 `--adopt` + 换位回滚，不再写 `.installed-version` / `.agate-root`）不符。F2 已登记两个新脚本并去掉 legacy 兜底表述，但漏了这三行的机制描述。
Fix：`agate-install.py` 行改为"…`vX.Y.Z` = 装指定版本（git plumbing 构建本体包，非 worktree；幂等）；`--adopt vX.Y.Z` = 纳管已就位版本目录；`--uninstall`（旧形态才 worktree remove）；`--check [--portable]`"；`agate-pack-offline.py` 行补 `[--ref REF]` 与"bundle 顶层 = `agate/` + 登记根文件 + `wheels/` + `manifest.json`（含 `files` 清单）"；`install-offline.py` 行改为"manifest.files 对账 → 拷本体包到 `.agate-tmp-*` → pip → 换位 → 兄弟 `agate-install.py --adopt`，失败回滚目录与指针"。

**M-2 私有符号跨模块引用 + 三处重复的"本进程容器清理"守卫（可维护性）**
`agate_common.py` `from agate_package import _is_bytecode`、`install-offline.py` 用 `agate_package._is_bytecode`、`agate-pack-offline.py` 用 `agate_package._release_container`、`agate-release.py` 用 `agate_package._git`——都是下划线私有名，改名会静默断三个消费方。另 `_cleanup_container`（agate-install）/ `_cleanup_own_container`（install-offline、agate-pack-offline）是同一个"前缀 + 直属根 + 真实目录才 rmtree"守卫的三份拷贝，属于安全关键逻辑，本应与 `sweep_stale` 同处单一来源；软链守卫的 `_symlink_home_detail` / `_reject_*` 在两脚本中也各有一份（三步文本重复由设计明示并有跨入口测试锁定，可接受，但 Python 侧本可从 `agate_package` 共享）。
Fix（不改行为）：在 `agate_package.py` 增公开 `is_bytecode`、`git_output`（或 `run_git`）、`release_container`、`remove_own_container(root, container)`；三处调用改用之。属重构，可延后到 P8 后 backlog，但 P4 内做最省事。

**M-3 `rollback_swap(backup=None, final)` 的无来源校验 `rmtree`（数据安全，低概率）**
`agate_package.py:758-761`：无备份分支对 `final` 直接 `shutil.rmtree`，仅校验"是真实目录"。当前调用链里它确为刚 `swap_in` 出来的目录，但函数本身是公开库函数，日后被别处调用即可误删。带备份分支已有"本进程创建 + 标记有效"守卫，两个分支不对称。
Fix：`swap_in` 在返回前把 `final` 的 `(st_dev, st_ino)` 记入模块级集合（如 `_SWAPPED_IN`），`rollback_swap` 无备份分支要求 `final` 命中该集合，否则抛 `PackageError("拒绝回滚：不是本次换位创建的目录")`。

**M-4 F2 把测试函数改名后，P3 追溯文件未同步**
`P3-test-cases.md:120` 仍以旧名 `test_bdd_28_use_legacy_is_gone_and_no_symlink_target_as_root_branch` 引用该用例，现名为 `test_bdd_28_legacy_switch_param_is_gone_and_no_symlink_target_as_root_branch`；P3 §6.5 的"改名 3"对账也应改为 4（BDD-48 的 D / A 对账口径：净删仍为 0，不影响 `A − D ≥ 0`）。`P4-implementation.md` 已自陈"需主 Agent 同步"。
Fix：主 Agent 在 P4 提交时把 `P3-test-cases.md:120` 与对账行的名字 / 计数同步（P3 产物已是 approved，属追溯性订正，不重开 P3）。

**M-5 workflow 里 `pip` 走 PATH 而非 venv（确定性 / 待 BDD-20 实跑确认）**
Build 步骤用 `$RUNNER_TEMP/venv/bin/python` 运行 `agate-release.py`，其子进程 `agate-pack-offline.py`（`sys.executable` = venv python）内部调用的是裸 `pip download …`——解析到的是 runner 的系统 `pip`，不是刚装了固定 pyyaml 的 venv 的 `pip`。`pip download` 本身与解释器无关，功能上不受影响；`pip` 取自 PATH 已被 P2 §1.2 / F-13 明确接受并列 backlog，故只作 MINOR。需要在 BDD-20 真实首跑时确认 hosted runner 上存在 `pip` 可执行文件（存在 `pip3` 但无 `pip` 的镜像会在打包 offline 时以"pip download 失败"退出）。
Fix（可选，最小改动）：Build 步骤前加 `echo "$RUNNER_TEMP/venv/bin" >> "$GITHUB_PATH"`（或在 Build 步骤 `env: PATH: …`），使 `pip` 稳定解析为 venv 的 pip；不引入 action。

### INFO

**I-1** `agate-release.py` 生成的 notes 头部固定写"`agateon-<tag>-offline-<平台>.tar.gz` 为离线安装包"，在 `--skip-offline`（本地补救 / 冒烟）时头部提到了并不存在的资产。仅影响本地冒烟构建，CI 不带 `--skip-offline`；不必改。

**I-2** pack 输出目录已存在则拒绝覆盖、`sweep_stale` 1 小时阈值、"不支持并发安装同一版本根"三项行为收紧，建议在 P8 的 CHANGELOG 变更节各补一行（UPGRADING 契约小节已写并发一项）。

**I-3** `agate-install.py <已装版本>` 仍先走 `_ensure_repo`（无 `repo/` 则联网 clone、有则 fetch），即"已安装，跳过"之前就有网络副作用——这是**既有行为**、非本任务引入（rv-04 复测时它对默认上游做了一次真实 clone，落在 scratchpad 的 `rv-04/h/repo`，未触碰真实 `~/.agate`）。若要让"已装版本幂等无网络"，需把存在性判断前移到 `_ensure_repo` 之前，超出本任务范围锁定，列 backlog 即可。另 `agate-workspace/agents/CODE-MAP.md` 未登记两个新脚本，`P4-implementation.md` 已声明 `[CODE_MAP_EXEMPT]` 并交 P7 核对，此处无异议。

## 7. 回派建议

无需回派 implementer 即可放行 P5。若主 Agent 愿意在 P4 提交前顺手吸收：M-1（文档，5 分钟）、M-4（追溯订正）优先；M-2 / M-3 / M-5 可入 backlog 或本次一并做。P5 需关注：t15 提交后复跑转绿；BDD-20 真实 CI 首跑时留意 M-5；`BDD-48` 的 D / A 对账（改名 4、净删 0）。

## 8. 本次新建的 scratchpad 目录（均在 `/tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/` 下）

`rv-01`（全量 pytest 输出）、`rv-02`（合成仓库 + 在线 / 离线 / release 真实链路 + 软链 / 回滚实验）、`rv-03`（HEAD 克隆 + 模拟提交，验证 t15 转绿）、`rv-04`（旧 worktree 形态兼容实验）。
