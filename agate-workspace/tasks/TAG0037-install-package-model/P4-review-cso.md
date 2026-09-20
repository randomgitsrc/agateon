---
phase: P4
task_id: TAG0037
type: review
parent: P4-implementation.md
trace_id: TAG0037-P4-cso-20260920-r1
created: '2026-09-20'
status: approved
agent: cso
---
# P4-review-cso — TAG0037 安装与多版本模型统一：P4 实现的供应链 + 安装器安全评审

[PROD_NOT_TOUCHED]

> 评审对象：工作区未提交的 P4 实现（`agate_package.py`、`agate-install.py`、`install-offline.py`、`agate-pack-offline.py`、`agate-release.py`、`agate_common.py` / `agate-resolve.py` / `agate-summary.py` 的 diff、`install.sh`、`.github/workflows/release.yml`、UPGRADING / README / AGENTS 等文档面）。
> 方法：逐行读代码，对照 P2 §14（含 §14.4）与 `P2-review-cso.md` 的 F-1…F-14、N-1…N-7；所有结论均经实测（scratchpad 新建目录 `cso-p4-1` … `cso-p4-6`，全部 HOME / AGATE_HOME 指向 scratchpad，未触碰真实 `~/.agate`、开发 checkout、git 分支 / tag；未 commit / add；仓库文件除本文件外零改动）。
> 已裁决项（S-1…S-19、C-1、install.sh 不 git pull、CI workflow 授权、G-1、DESIGN_GAP-B1、F2 授权改 4 个测试文件字面量）不再异议，只审实现是否忠实。

## 0. 结论

**结论：approved。** 无 CRITICAL、无 HIGH（无 BLOCKER）。P2 阶段 cso 的 F-1（HIGH）与 N-1（数据安全）在实现里落实到位并经实测：

- 所有删除类调用的对象都严格限于"本工具自己创建且带专用标记（或本进程刚 mkdtemp 出）的容器 / 目录"；`sweep_stale` / `recover_backups` / `discard_backup` / `rollback_swap` 永不按名字模式删除，`vX.Y.Z.bak-*`、`vX.Y.Z.tmp-*`、无标记的 `.agate-tmp-*`、软链均原样保留（实测 + T-23 用例真实覆盖）。
- 软链基址守卫对 `L` / `L/` / `L//` / `L/.` / `L/./` / `L/.//` / `L/..`（经软链的 `..`）/ `L/sub/..` / `sub/ln/` / `ln2/..` / 相对路径变体，在 `agate-install`（install / latest / vX.Y.Z / --adopt）、`install-offline`（--dest-root）、`install.sh` 全部拒绝，目标目录零变化；`agate-resolve` 全部变体 fail-closed 并附迁移提示。
- release.yml 的静态契约全部满足（见 §4）。

复审新发现 **0 项 CRITICAL / 0 项 HIGH / 0 项 MEDIUM / 8 项 LOW**（另有 2 项 INFO），均为纵深防御或文档口径，不阻塞发布，可在 P4 修订或 backlog 中吸收。

| 严重级别 | 数量 |
|----------|------|
| CRITICAL | 0 |
| HIGH（BLOCKER） | 0 |
| MEDIUM | 0 |
| LOW | 8（L-1…L-8） |
| INFO | 2（I-1、I-2） |

是否阻塞发布：否。

---

## 1. 数据安全：删除点清单（重中之重）

对新增 / 改动的全部脚本 grep `rmtree|unlink|os.remove|os.rmdir|shutil.move|os.replace|os.rename|rm` 后逐处核对。未发现 `shell=True` / `os.system` / `eval` / `exec`；`rm` 类 shell 命令只出现在文档文本中（无，见 §5）。

| 位置（文件:行） | 操作与对象 | 保护条件 | 判定 |
|-----------------|-----------|----------|------|
| `agate_package.py:639,641` `_release_container` | `unlink(<容器>/标记)` + `rmdir(容器)` | 只删标记与**空**容器（不 rmtree）；容器里有别的内容则 rmdir 失败被 suppress，原样保留 | 安全 |
| `agate_package.py:655` `make_work_dir` 失败分支 | `rmdir(刚 mkdtemp 的容器)` | 仅空目录、仅本次创建 | 安全 |
| `agate_package.py:682` `sweep_stale` | `rmtree(.agate-tmp-* 容器)` | 名字前缀 `.agate-tmp-` + `lstat` 真实目录（不跟随软链）+ 标记 `lstat` 为普通文件且首行 `agate-package/1 kind=tmp` + 标记 mtime > 3600s；**不按 `vX.Y.Z.*` 模式**，不碰 `.agate-bak-*` | 安全（实测，见下） |
| `agate_package.py:760` `rollback_swap`（backup=None） | `rmtree(final)` | 仅在 `swap_in` 刚把**本进程**新目录换位、且 `--adopt` 失败时调用；`_is_real_dir` 校验；`final` 之前不存在（否则会有 backup） | 安全（并发不支持，已文档化） |
| `agate_package.py:770-773` `rollback_swap`（有 backup） | `rename(final → backup/failed-new)` 后 `rmtree(failed-new)`；`rename(backup/old → final)` | 备份容器须：真实目录 + 标记 kind=bak + `realpath ∈ _CREATED_BACKUPS`（本进程创建）；`failed-new` 位于自己的备份容器内 | 安全 |
| `agate_package.py:790` `discard_backup` | `rmtree(备份容器)` | basename 前缀 `.agate-bak-` + 真实目录 + 标记 kind=bak + 本进程创建集合；否则返回 False 并保留（实测拒绝删除用户预置的同名带标记目录） | 安全 |
| `agate_package.py:500` / `:497` `write_dir_tarball` | `unlink(本次 mkstemp 的 .part 临时文件)` / `os.replace(tmp → out_path)` | 仅本次创建的临时文件；`os.replace` 覆盖 `out_path`（调用方传入的产物路径，见 L-6） | 安全 |
| `agate_package.py:835` `restore_pointers` | `unlink(latest/current)` 后重建 | 只针对固定名 `latest` / `current`；目录形态指针不删（"other"跳过；位置上是目录 → 抛错不删） | 安全（实测：`latest/` 目录含用户数据，adopt 失败后完整保留） |
| `agate-install.py:107,123` `_write_pointer` / `_remove_pointer` | `unlink(latest/current)` | 固定指针名，`os.path.lexists`；既有行为 | 安全 |
| `agate-install.py:204` `_cleanup_container` | `rmtree(工作容器)` | 前缀 `.agate-tmp-` + 直属版本根 + 真实目录 + 非软链；且该路径来自本进程 `make_work_dir` 返回值 | 安全 |
| `agate-install.py:492,494` `--uninstall` | `unlink(软链版本目录)` / `rmtree(vX.Y.Z)` | 版本号 `fullmatch` 严格 `vX.Y.Z`；用户显式 `--uninstall`；仅当前版本目录；引用保护扫描在前；软链版本目录只 unlink | 安全，但见 L-1（无软链基址守卫） |
| `install-offline.py:354` `_cleanup_own_container` | `rmtree(工作容器)` | 同 `_cleanup_container`（前缀 + 直属 dest + 真实目录 + 非软链） | 安全 |
| `install-offline.py:393` | `rmdir(dest_root)` | 仅当本次刚建（`root_preexisted=False`）且为空才成功 | 安全 |
| `agate-pack-offline.py:129` `_cleanup_own_container` | `rmtree(工作容器)` | 同上（前缀 + 直属 outdir + 真实目录 + 非软链）；输出目录已存在时**拒绝覆盖**而非清空重建 | 安全 |
| `agate-release.py:268` `shutil.move` | 暂存 → outdir | outdir 事先校验"不存在或为空目录"、非软链；`--notes-out` 不得落在 outdir 内 | 安全 |
| `agate-release.py:273` | `rmtree(work)` | `work` 由本次 `tempfile.mkdtemp(".agate-release-")` 创建 | 安全 |
| `install.sh` | 无任何删除类命令 | — | 安全 |
| `release.yml` | 无 `gh release delete` / `git push --delete` / `rm` | — | 安全 |

### 实测（`cso-p4-2/t.py`，直接调用 `agate_package`）

版本根内预置：`v0.1.0.bak-20260920`、`v0.1.0.bak-before-upgrade`、`v0.1.0.tmp-abcd1234`、`.agate-tmp-user-dir`（无标记）、`.agate-bak-v0.1.0-abcd1234`（无标记）、`v0.1.0`（含用户文件）、标记 kind=bak 却前缀为 `.agate-tmp-` 的目录、标记为**软链**（指向内容合法的外部文件）的 `.agate-tmp-*`、`.agate-tmp-*` **软链**指向含合法标记的外部目录、不足 1 小时的有效容器；另一个"合法 > 1h 容器"内部含指向外部目录的软链。

- `sweep_stale` 仅删除那个合法的过期容器（内部软链只被 unlink，外部目录及 `precious` 文件完整）；其余全部保留。
- `recover_backups` 对上述条目零改动；`discard_backup` 对用户预置的带前缀目录返回 False 并打印警告、目录与内容保留；真实 `swap_in` → `rollback_swap` 后旧目录内容还原、备份容器清除。
- CLI 层（`cso-p4-3/attack.py` 场景 H）：版本根内预置 `v1.2.3.bak-user` / `v1.2.3.tmp-abcd1234` / `.agate-tmp-x`，`install-offline` 重装同版本成功，三者原样保留。
- adopt 失败注入（场景 I，`latest/` 是含用户数据的目录）：rc=1，"版本目录与 latest/current 指针均已还原"，`latest/precious` 完整，未留半成品版本目录。

### T-23 是否真覆盖

`test_install_offline.py::test_t23_install_sweeps_only_own_expired_containers_and_keeps_everything_else`（CLI 端到端，含外部软链目标哈希不变）+ 三个库层用例（`sweep_stale` / `recover_backups` / `discard_backup`）。读了断言：预置对象覆盖名字模式陷阱、无标记、标记软链、内容不符、软链目录、`.agate-bak-*`、<1h 有效容器，且逐项比对内容哈希。覆盖真实，非形式。

---

## 2. 软链 fail-closed 守卫（cso F-1 HIGH）

实测矩阵（`cso-p4-1/run.sh`，17 个绝对变体 + 4 个相对变体 × 4 入口，共 84 组；每组前后对 `target/` 全树做快照比对）：

| 入口 | 结果 |
|------|------|
| `agate-install.py latest` / `--adopt` | `L`、`L/`、`L//`、`L/.`、`L/./`、`L/.//`、`L/././.`、`L/sub/..`、`L/sub/../`、`sub/ln/`、`sub/ln/.`、`ln2/..`、`ln2/../`、`ln2/../.`、`sub/../L`、`sub/../L/`、`./L/` 全部 rc=1，stderr 含"检测到的软链"行 + 三步，**目标目录零变化** |
| `install-offline.py --dest-root` | 同上全部 rc=1（守卫先于 manifest 读取与任何写入） |
| `install.sh` | 尾斜杠 / `/.` 循环剥离后 `-L` 命中；含 `..` 分量一律 exit 1；目标零变化 |
| `agate-resolve.py`（`cso-p4-5`） | `L2`、`L2/`、`L2//`、`L2/.`、`L2/./`、`ln3/..`、`ln3/../` 全部 exit 1 + 迁移提示 |

唯一"未拒绝"的变体是 `L/..`：该夹具中 `L` 位于 `S/L`、目标在 `S/target`，`L/..` 物理与文本解析都是 `S`（真实目录），属正常放行，不是绕过（我的夹具选择所致，已通过 `L/sub/..` 与 `ln2/..` 这类"物理 ≠ 文本"的变体验证歧义检测有效）。

`normalize_home` 的歧义检测（`realpath(原始) != realpath(规范化)`）+ 对**原始文本与规范化路径两者**分别判定（`_reject_symlink_home` / `_reject_symlink_dest` 的 `for candidate in (raw, normalized)`）是实现里最关键的一步，做对了。T-14 参数化用例（`test_bdd_31/32/33/27_t14_*`、`test_t14_adopt_*`）共 5 变体 × 各入口，我另加的变体全部通过，未发现绕过。

不属绕过、但值得记录的边角：`--uninstall` 不带守卫（L-1）；portable 文档片段的 shell 守卫不处理 `/.`（L-2）。

---

## 3. tarball / 包集合安全

**`list_package` 硬化**（`cso-p4-4/t.py`、`t2.py` 用真实 git 对象 + `git mktree` 构造畸形树实测）：软链（mode 120000）、子模块（160000）、`agate/.git/…`、`agate/.GITMODULES`（casefold）、含 `:`、结尾空格 / 点、仅大小写不同、含换行 / 控制字符、含反斜杠、非 UTF-8、`agate/..`、根登记文件被换成软链、缺 `agate/scripts/` → 全部 `PackageError`；`agate/Tests/`、`__pycache__`、`*.pyc`、包区外的怪名字（`docs/a:b `）不影响结果。

**`parse_release_ref`**（17 个用例）：`v1.2.3\n`、Unicode 数字 `v１.2.3`、`v1.2.3-`、`v1.2.3-.x`、`-a..b`、`-a.`、`-a.lock`、含 `/`、空格、大写 `V`、NUL、前导空格、非 ASCII 后缀全部拒绝；`fullmatch` + `re.ASCII` 正确。`v01.2.3`（前导零）被接受，属 INFO（I-1）。

**写侧**（`write_dir_tarball`）：源目录含 FIFO / 软链 → 在**任何写入之前** `PackageError`（实测 `out1.tgz` 不存在，无 `.part` 残留）；硬链接文件在磁盘上以普通成员写出（无 hardlink 成员）；setuid 位被归一为 0755；uid/gid=0、uname/gname 为空、mtime 固定；成员集合实测无 `tests` / `__pycache__` / `.git` / `.pyc`。
**读侧**（`install-offline` bundle 校验，`cso-p4-3/attack.py`）：bundle 内软链成员、FIFO 成员、`manifest.files` 含 `agate/../../evil` 或 `/etc/passwd`、`manifest.version` 为 `v1.2.3\n` / `v1.2.3-rc.1` / Unicode 数字 / 两段 / 含 `/../`、`source_ref` 含换行 / ESC / `..` → 全部 rc=1，且**dest 根目录都不曾被创建**（守卫先于任何写入）；bundle 顶层夹带 `extra.sh` → 告警且不安装（实测未出现在安装结果里）；重装同版本、fresh 安装均成功，`vX.Y.Z/` 权限 0755（N-3 已吸收）。

**portable 路径的读侧**（用户手工 `tar -xzf`）见 L-3。

**软链 / 特殊文件的两侧**：`materialize` 与 `copy_files` 落盘均 `O_EXCL|O_NOFOLLOW`、逐级 `os.mkdir`（不用 `makedirs(exist_ok)`）、越界检测；`copy_files` 对源每级 `lstat`。未发现路径穿越或经预置软链写出目的地外的途径。

---

## 4. `release.yml`

`yaml.safe_load` 解析后逐项核对 + 静态审读（`cso-p4-6` 另实跑 `agate-release.py`）：

| 检查项 | 结果 |
|--------|------|
| 触发 | `on.push.tags: ['v*']` 唯一；无 `pull_request` / `workflow_dispatch` / `workflow_run` |
| 权限 | 顶层 `permissions: {contents: write}`，job 级无覆盖 |
| `uses:` | 0 处（零第三方 action） |
| `secrets.*` | 0 处 |
| `GH_TOKEN` | 仅 Publish 步骤 `env`（`${{ github.token }}`）；Clone / Deps / Build 步骤不持有令牌；无 `actions/checkout`（无持久化凭据） |
| `run:` 中的 `${{` | 0 处（解析后逐个 `run` 检查）；`TAG` 走 job 级 `env`，`${{ }}` 仅出现在 `env` 与 `concurrency.group` |
| `--verify-tag` | 有（`gh release create … --verify-tag`） |
| `--expect-sha` | 有（`"$GITHUB_SHA"`）；实测两侧 `^{commit}` 剥壳，tag 提交 ≠ 期望提交时 rc=1 且 outdir 未创建 |
| `is-prerelease` | `case "$rc"` 三分支：0 → `--prerelease`；1 → 正式；其他（含 2）→ `exit "$rc"`。实测 `v0.72`、`vfoo`、`v0.72.0\n`、`v1.2.3-`、`-x`、`v0.72.0/../x` 均 rc=2（失败而非当正式发布） |
| pyyaml 固定 | `PYYAML_PIN` 由 `agate-release.py pyyaml-pin` 提供，`--only-binary=:all:`，与 pack-offline 同源 |
| 完整性局限 | notes 头部、UPGRADING portable 小节、AGENTS 发布清单均如实写明 "`SHA256SUMS` 只防损坏、不认证发布者"；offline 包用 `pip download` 不带 `--require-hashes`，已按 R-7 / F-2 登记为 backlog，同意 |
| 误发布 / 误删 | 无任何删除 Release / tag 的步骤；`gh release create` 遇已存在 Release 直接失败；`concurrency` 对同 tag 串行 |
| 缺 CHANGELOG 段 | `notes` 正式 tag 缺段 exit 1 且先于任何产物写入（实测 `v9.9.9` rc=1）；预发布回落 `[Unreleased]` |

`agate-release.py build` 实测：`--outdir` 已存在且非空 → 拒绝；`--notes-out` 落在 outdir 内 → 拒绝；`--expect-sha` 不符 → 拒绝；产物 `agateon-v0.72.0.tar.gz` 无 `tests` / 字节码 / `.git`，成员 `0/0` 归一，`SHA256SUMS` 与 `sha256sum -c` 一致。

发现 1 项纵深防御建议：Publish 步骤（持有令牌）执行了被克隆 tag 内的 `agate/scripts/agate-release.py is-prerelease`，见 L-4。

---

## 5. 迁移提示 / 文档命令

- 全部新增 / 改动文档中，`rm` / `mv` 类命令只有迁移三步里的 `mv ~/.agate ~/.agate.bak` + `mkdir -p ~/.agate` + `install.sh --versions`，以及 AGENTS 发布清单的 `gh release delete`（"须先确认其属本次创建"）。未出现 `rm -rf`、`--force`、`sudo`、`chmod`、`--cleanup-tag` 或 `git push --delete`。
- 运行时输出（agate-install / install-offline / install.sh / resolve 同源）先打印动态"检测到的软链：`<规范化路径> → <readlink 目标>`；若它不是 `~/.agate`，请把下列命令中的 `~/.agate` 替换为它"（F-8 已吸收）。但 README / UPGRADING / SETUP 里的静态迁移文案仍硬编码 `~/.agate`（L-5）。
- 迁移三步是"改名 + 新建 + 重装"，不含删除，最坏情形是命名冲突而非数据丢失。

---

## 6. 发现（分级 + 可执行修改建议 + BDD 引用）

### L-1 [LOW] `--uninstall` 无软链基址守卫，会穿透软链对目标内 `vX.Y.Z` 目录 `rmtree`
- **BDD**：32 / 51 ②（安装侧一律拒绝）；P2 §3.3（守卫只写在 `_cmd_install` / `_cmd_adopt`）。
- **证据**：`cso-p4-1`：`AGATE_HOME=L`（软链）、目标内预置 `v9.9.9/userfile`，`agate-install.py --uninstall v9.9.9` → rc=0，"已卸载 v9.9.9"，`target/v9.9.9` 被删除。`_cmd_uninstall` 无 `_reject_symlink_home`。
- **影响面**：被删对象限于软链目标内**恰好名为 `vX.Y.Z`** 的条目，且为用户显式命令；旧软链布局（目标为仓库 `agate/`）里通常没有此类条目；BDD-51 允许"软链 → 完整版本根"解析，卸载在这种情形下可能本就是期望行为。故仅 LOW，属实现忠实于设计，但"最危险的动词没有最强的守卫"。
- **建议**：`_cmd_uninstall` 入口对**规范化后的**基址判 `is_symlink_base`，且仅在"软链目标不是有效版本根（无 `latest` / `current` 指针链）"时拒绝；或统一拒绝并在文案说明"对软链目标直接执行"。补一个 T-14 参数化用例（`--uninstall` 入口）。可放 backlog。

### L-2 [LOW] portable 文档片段的 shell 守卫未处理 `/.`，`mkdir` / `tar` 会在第二道守卫（`--adopt`）之前写入软链目标（P2 cso N-5 未吸收）
- **BDD**：17 / 32；`agate/UPGRADING.md` "portable 安装"命令块；P2 §3.5。
- **证据**：`cso-p4-5`：片段前三行对 `AGATE_HOME=<L>` 与 `<L>/` 命中（"guard caught"），对 `<L>/.` 与 `<L>/./` **未命中**（"guard MISSED"），随后 `mkdir "$AGATE_HOME/vX.Y.Z"` 在软链目标里创建了目录（只新增、不覆盖：`mkdir` 无 `-p`）。`install.sh` 已有 `/.` 剥离与 `..` 拒绝，文档片段与之不一致。
- **建议**：片段第 2 行改为与 `install.sh` 同款循环（`case … ?*/) … ?*/.) …`）并拒绝含 `..` 的值；片段加 `export AGATE_HOME`（否则用户仅设 shell 局部变量时 `python3 … --adopt` 读到的是默认 `~/.agate`，安全失败但易困惑）。BDD-17 的命令实跑测试随之更新。
  
### L-3 [LOW] portable 用系统 `tar -xzf` 解压：解压期软链写出无法被事后 `--adopt` 校验拦截；字节码盲区（P2 cso N-7 未吸收）
- **BDD**：15 ④、17、19。
- **证据**：文档片段 `tar -xzf agateon-vX.Y.Z.tar.gz -C "$AGATE_HOME/vX.Y.Z"` 后才 `--adopt`，`verify_dir` 拦得住软链 / 多余顶层条目，但拦不住"解压那一刻已经经软链写出去"；`verify_dir` / 哈希忽略 `__pycache__/*.pyc`，而 Python 即使 `-B` 也会读取已存在的 `.pyc`。官方 tarball 由 `write_dir_tarball` 生成（我实测无软链 / 硬链 / 字节码 / 特殊成员），第三方恶意 tarball 本就可直接带恶意 `.py`，故**不构成新的提权面**，仅是口径完整性。
- **建议**：portable 小节在 `tar -xzf` 前加一行 `tar -tvzf agateon-vX.Y.Z.tar.gz | grep -E '^[lhcbp]|__pycache__|\.py[co]$'` 应为空；`verify_dir` 在 `--adopt` 时对新形态（无 `.git`）多做一步"含字节码则告警"；旧形态判定改为"`.git` 存在且 `repo/.git/worktrees/` 里有对应登记"（避免放一个 `.git` 文件绕过校验，N-7 后半）。

### L-4 [LOW] Publish 步骤（持有 `contents: write` 令牌）执行被克隆 tag 内的仓库脚本
- **BDD**：20；`release.yml` Publish 步骤。
- **证据**：`python3 -B agate/scripts/agate-release.py is-prerelease "$TAG"` 在 `working-directory: src`（tag 内容）且 `env: GH_TOKEN` 的步骤中运行。任何能推送 `v*` tag 的人，其 tag 内容里的 `agate-release.py` 都会以令牌运行——与推 tag 权限相比增量很小（且 AGENTS 已建议对 `v*` tag 启用 Ruleset），但违背"令牌步骤不跑仓库代码"的最小暴露原则；`Build` 步骤（无令牌）同样跑仓库代码，那里没问题。
- **建议**：把 `is-prerelease` 判定挪到 Build 步骤（无令牌），把结果（`0`/`1`/`2` 或空文件标志）写入 `$RUNNER_TEMP/prerelease`；Publish 步骤只 `read` 该文件并调用 `gh`，不再执行 `src/` 内任何脚本。`test_release_workflow.py` 的静态契约同步："含 `GH_TOKEN` 的步骤不含 `python`"。

### L-5 [LOW] 静态迁移文案硬编码 `~/.agate`，与 `AGATE_HOME` 自定义软链场景不一致（F-8 仅覆盖运行时输出）；`mv` 遇已存在的 `~/.agate.bak` 会嵌套
- **BDD**：27 / 31 / 32 / 33 / 35。
- **证据**：README / README.zh-CN / UPGRADING v0.73.0 节 / SETUP 里的三步命令固定 `~/.agate`；运行时输出才带"检测到的软链 … 请替换"首行。`mv ~/.agate ~/.agate.bak` 若 `~/.agate.bak` 已是目录，则软链被移入其内（`~/.agate.bak/.agate`），第 2 步 `mkdir` 仍成功，状态混乱但不丢数据；若 `~/.agate.bak` 是普通文件，`mv` 会覆盖它。
- **建议**：静态文案在三步前加一句"若你的软链在 `$AGATE_HOME` 指向的自定义路径，请替换命令里的 `~/.agate`（运行任一安装类命令会打印检测到的路径）"；第 1 步文案加"若 `~/.agate.bak` 已存在，请换个名字"。三步片段的正则（`_migration_steps`）不受影响。

### L-6 [LOW] `agate-release.py notes --out` / `build --notes-out` 静默覆盖既有文件
- **BDD**：20。
- **证据**：`_write_text` 用 `open(path, "w")`，目标存在则覆盖；`build` 只校验 notes 不在 outdir 内。
- **建议**：`_write_text` 用 `O_EXCL` 语义或在目标存在时 exit 1（与"outdir 已存在且非空则拒绝"同一口径），需要覆盖时显式 `--force`。CI 场景 `notes.md` 在 `RUNNER_TEMP`，不受影响。

### L-7 [LOW] 离线重装同一版本成功后静默丢弃旧版本目录内容（含本地改动）
- **BDD**：10 / 16；D-6；S-16。
- **证据**：`cso-p4-3` 场景 H：`v1.2.3/old_local_change` 在重装成功后消失（旧目录先移入带标记的备份容器，`--adopt` 成功后 `discard_backup` 删除）。这是 S-16 的既定语义（幂等重装），备份删除也严格限于本进程创建的容器，属预期；但 UPGRADING / `install-offline` 输出没有提示"旧版本目录将被替换（含本地修改）"。
- **建议**：`install-offline` 在 `swap_in` 返回非 None 备份时打印一行"已替换既有 vX.Y.Z（旧目录已按安全流程移除；如需保留本地修改请先自行备份）"；UPGRADING 离线小节加一句。可 backlog。

### L-8 [LOW] AGENTS 发布清单的补救命令 `gh release delete` 未带 `-R` / 未强调不加 `--cleanup-tag`
- **BDD**：21；P2 cso N-2（§11 已加 `-R "$REPO"`，AGENTS 清单未同步）。
- **建议**：清单写成 `gh release delete vN.N.0 -R <owner>/<repo>`（先 `gh release view -R … --json tagName,createdAt` 回显确认），并注明"不要加 `--cleanup-tag`（会删 tag）"。

### I-1 [INFO] `VERSION_RE` 接受前导零（`v01.2.3`）
`v01.2.3` 与 `v1.2.3` 会成为两个不同目录名，`int()` 比较视为同版本。无安全影响；可在 `is_strict_version` 加 `(0|[1-9][0-9]*)` 收紧，但会改 BDD-15 / 既有夹具口径，不建议本任务处理。

### I-2 [INFO] Windows 目录联接（junction）不被 `os.path.islink` 识别（Python < 3.12）
`is_symlink_base` 对 junction 基址放行。旧布局在 Windows 上是复制模式（无软链权限），实际风险接近零；如要闭环，Python ≥ 3.12 可加 `os.path.isjunction`。仅记录。

---

## 7. STRIDE 矩阵

| 面 | S 欺骗 | T 篡改 | R 抵赖 | I 信息泄露 | D 拒绝服务 | E 提权 | 最高级别 |
|----|--------|--------|--------|-----------|-----------|--------|----------|
| 删除 / 清扫 / 回滚（`agate_package`、三个入口） | — | 前缀 + 标记 + 本进程集合三重限定，用户目录与软链实测原样保留 | — | — | 崩溃残留只留标记容器（不误删）；并发不支持已文档化 | — | 无发现 |
| 软链基址守卫（install / adopt / offline / sh / resolve） | 规范化 + 歧义检测，实测 84 组无绕过 | 目标目录零变化 | 拒绝时打印检测到的软链 + 三步 | — | — | `--uninstall` 无守卫（L-1）；portable shell 片段 `/.`（L-2） | LOW |
| 包集合 / 打包 / bundle 校验 | manifest `version` / `source_ref` 严格 fullmatch，仅信息性、不入路径 | `O_EXCL|O_NOFOLLOW`、`lstat` 逐级、对账 `manifest.files`、tar 成员先验后写 | — | — | 单个巨大 blob 全读内存（上游信任，忽略） | 解压期软链 / 字节码盲区（L-3） | LOW |
| release.yml / `agate-release.py` | tag 移动由 `--expect-sha` 两侧剥壳拦截 | 产物确定性；无 `uses:`；`SHA256SUMS` 局限如实披露 | 无 | 令牌仅 Publish 步骤 | `concurrency` 串行、20 分钟超时 | Publish 步骤跑仓库脚本（L-4）；`--notes-out` 覆盖（L-6） | LOW |
| 迁移提示 / 文档 | — | `mv` 嵌套 / 覆盖 bak（L-5）；`gh release delete` 未带 `-R`（L-8） | — | — | — | 无诱导 `rm -rf` / `--force` / 提权命令 | LOW |

---

## 8. 对 P2 cso 处置（F-1…F-14、N-1…N-7）的实现忠实度

| 编号 | 实现落点 | 判定 |
|------|---------|------|
| F-1 HIGH 软链尾斜杠绕过 | `normalize_home` / `is_symlink_base` / `agate_home`；三入口对原始 + 规范化各判一次；`install.sh` 循环剥离 + 拒绝 `..` | **已落实（实测）** |
| F-2 token + 依赖固定 | `GH_TOKEN` 仅 Publish；`PYYAML_PIN` 同源；`--only-binary=:all:` | 已落实（Publish 步骤跑仓库脚本见 L-4） |
| F-3 tag 移动 | `--expect-sha`；两侧 `^{commit}`（N-6 已吸收，实测） | 已落实 |
| F-4 完整性局限 | notes 头 / UPGRADING / AGENTS 如实披露；checksum 文案"损坏或被替换" | 已落实 |
| F-5 换位 / 回滚 / 残留 | `swap_in` / `rollback_swap` / `discard_backup` / `recover_backups`；备份路径 `<容器>/old`（N-3 已吸收）；`copy_files` / `materialize` 收尾 `chmod`（N-3 已吸收，`vX.Y.Z` 实测 0755） | 已落实 |
| F-6 根入口 / P 集合 / `--adopt` 校验 | `lstat` + `os.walk(followlinks=False)` + `manifest.files` 对账；`--adopt` 调 `verify_dir` | 已落实（旧形态判定盲区见 L-3） |
| F-7 测试 tag 清理 | 属人工 §11 清单；未见任何删除 tag / Release 的代码路径 | 已落实（N-2 的 `-R` 在 §11 已加；AGENTS 清单见 L-8） |
| F-8 迁移提示硬编码 | 运行时动态首行已加；静态文档未加 | 部分（L-5） |
| F-9 正则 `$` 换行 | `fullmatch` + `re.ASCII`；17 例表驱动实测 | 已落实 |
| F-10 `is-prerelease` exit 2 | `case "$rc"` 三分支；实测 | 已落实 |
| F-11 路径硬化 | `_validate_relpath` + casefold 冲突 + `O_EXCL|O_NOFOLLOW`；畸形树实测 | 已落实 |
| F-12 portable 命令鲁棒性 | 默认值 / `mkdir` 无 `-p` / `sha256sum -c` / 解压前守卫 | 大体落实（`/.` 缺口 L-2） |
| F-13 / F-14 | `git clone --`、`OSError` 转 stderr、workflow 静态断言（`test_release_workflow.py` 12 例） | 已落实 |
| N-1 数据安全 `sweep_stale` | 专属前缀 + 标记 + 1h + 真实目录；永不按名字删；`recover_backups` 只改名；`discard_backup` 只删本进程创建 | **已落实（实测 + T-23）** |
| N-2 `gh -R` | §11 已写；AGENTS 补救命令未带 | 部分（L-8） |
| N-3 平台细节 | 备份容器 `<容器>/old`；`chmod` | 已落实 |
| N-4 adopt 回滚含指针 | `snapshot_pointers` / `restore_pointers`；实测目录形态 `latest/` 保留 | 已落实 |
| N-5 portable `/.` 与 `export` | 未吸收 | 未落实（L-2） |
| N-6 `--expect-sha` 归一化 | 两侧剥壳 | 已落实 |
| N-7 字节码 / `.git` 判形态 | 未吸收 | 未落实（L-3） |

---

## 9. 测试与实测记录

- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest agate/tests/unit/test_agate_package.py test_install_offline.py test_agate_version_install.py test_agate_install_adopt.py test_install_sh.py test_release_workflow.py test_agate_release.py test_agate_version_resolve.py -q -p no:cacheprovider` → **372 passed**（安全相关八个文件；全量 2291 passed / 1 failed 的唯一失败 `test_t15_real_tree_smoke_pack_install_resolve` 读已提交 HEAD，属预期，不在本评审范围内重复）。
- `ruff check`（`agate_package.py` / `agate-release.py` / `install-offline.py`）通过；`shellcheck -S style install.sh` 无输出。
- 自测脚本与夹具（均在 scratchpad，未入仓）：`cso-p4-1/run.sh`（软链矩阵 84 组）、`cso-p4-2/t.py`（sweep / recover / discard / rollback）、`cso-p4-3/{mk,attack}.py`（离线安装攻击 bundle 10 类 + 重装 + adopt 失败）、`cso-p4-4/{t,t2}.py`（`parse_release_ref` + `list_package` 畸形树 + tarball 写侧）、`cso-p4-5`（portable shell 守卫与 resolve 变体）、`cso-p4-6`（`agate-release.py` 实跑）。

## 10. 返回摘要（给主 Agent）

approved；最高严重级别 LOW（无 CRITICAL / HIGH / MEDIUM；LOW 8 项、INFO 2 项，均非阻塞）。数据安全重点确认：所有删除点均限于本工具创建且带标记的容器，用户 `vX.Y.Z.bak-*` 等目录实测原样保留；软链守卫 84 组变体无绕过。新建 scratchpad 目录：`cso-p4-1` … `cso-p4-6`（位于 `/tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/`）。
