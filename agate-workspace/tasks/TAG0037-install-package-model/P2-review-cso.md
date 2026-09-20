---
agent: cso
phase: P2
task_id: TAG0037
type: review
parent: P2-design.md
trace_id: TAG0037-P2-cso-20260920-r1
created: '2026-09-20'
status: approved
---
# P2-review-cso — TAG0037 安装与多版本模型统一：供应链 + 安装器安全评审（复审 #1）

[PROD_NOT_TOUCHED]

> 复审对象：修订后的 `P2-design.md`（含 §14 处置表）。方法：逐条对照首轮 F-1…F-14 与设计正文（不只看 §14 自述）；对 F-1 的修复规则在新建 scratchpad `cso2/` 按 §3.2 / §3.7 / §3.5 字面实现原型并实测；检查修订本身（含 eng 评审引出的修订）是否新引入问题。未触碰真实 `~/.agate`、未改任何仓库文件（仅本输出文件与 progress 追加）、未 commit。
> 已裁决项（S-1…S-19、C-1、install.sh 不 git pull、CI workflow 授权）不再异议。

## 0. 结论

**结论：approved。** 首轮 1 项 HIGH（F-1）与 6 项 MEDIUM（F-2…F-7）均已真实解决（设计正文落点存在，F-1 经实测验证）；7 项 LOW 中 5 项采纳、2 项部分不采纳且理由成立。复审新发现 0 项 CRITICAL / HIGH，2 项 MEDIUM（N-1、N-2）与 5 项 LOW；均为设计文本的小幅补充，可在 P3 用例 / P4 实现清单中直接吸收，不需要再回到 P2 review。

| 严重级别 | 首轮未解决 | 复审新增 |
|----------|-----------|----------|
| CRITICAL | 0 | 0 |
| HIGH（BLOCKER） | 0 | 0 |
| MEDIUM | 0 | 2（N-1、N-2） |
| LOW | 0（F-13 两项不采纳，见 §1） | 5（N-3…N-7） |

是否阻塞发布：否。

---

## 1. 首轮发现逐条核对

| 编号 | 首轮级别 | 复审结论 | 依据（设计正文落点 / 实测） |
|------|----------|----------|------------------------------|
| F-1 软链守卫尾斜杠绕过 | HIGH | **已解决（实测）** | D-14 / §3.2 `normalize_home`（`abspath(expanduser)` 去尾 `/`、`/.`、多余斜杠、文本 `..` + `realpath(原始)≠realpath(规范化)` 歧义检测）/ `is_symlink_base`；§3.3、§3.4 步骤 1、§3.7 三入口与 `agate_common` 统一走规范化；T-14 参数化 `L / L/ / L// / L/. / L/..` 四入口断言目标文件哈希不变。**实测**（`cso2/proto.py`，按 §3.2 字面实现）：`L`、`L/`、`L//`、`L/.`、`L/./`、`L/.//`、`./L/`、`sub/ln2/`、`sub/ln2/.`、`L/..`、`L/scripts/..`、`L/scripts/../` 全部被拒；`repo/agate`、`repo/agate/`、`sub`、`home` 均不误拒。cso 首轮提出的"含 `.git` 祖先目录则拒绝"的纵深项**不采纳**——理由成立（`$HOME` 为 dotfiles git 仓库的用户会被误拒 `~/.agate`），主修复已消除绕过，同意 |
| F-2 token 暴露 + 依赖未固定 | MEDIUM | **已解决** | §3.6 workflow 草案：job 级 `env` 仅 `TAG`；`GH_TOKEN` 仅在 Publish 步骤；`PYYAML_PIN = 6.0.3` + `--only-binary=:all:`，workflow 与 `agate-pack-offline` 经 `pyyaml-pin` 子命令同源；notes 列 wheel 文件名与 sha256；E-16 联网核对两平台 wheel 可下载。`--require-hashes` 与 build/publish 拆 job 列 backlog / 不采纳（后者违反零 action），同意，残余风险已在 R-7 如实登记 |
| F-3 tag 被移动 | MEDIUM | **已解决** | `build --expect-sha "$GITHUB_SHA"`（`git rev-parse "refs/tags/T^{commit}"` 必须相等，否则 exit 1）；T-18。小注见 N-6 |
| F-4 完整性局限 / 校验步骤 | MEDIUM | **已解决** | D-15、R-16、§3.5（portable 增 `sha256sum -c` 与"只防损坏、不认证发布者"说明）、§3.6 notes 头、`install-offline` 文案改"不一致（损坏或被替换）"；manifest `files` 清单使路径名纳入校验（弥补目录哈希不含路径名）。来源证明列 backlog，同意 |
| F-5 换位回滚 / 并发 / 残留 | MEDIUM | **已解决（并发文档化）** | D-6、R-8、R-15；§3.2 `swap_in` / `rollback_swap` / `discard_backup` / `sweep_stale` + `mkdtemp`；§3.4 步骤 5–9（先拷贝到临时目录、pip 在换位前、adopt 成功后才删备份、失败回滚）；E-17（注入第二步失败仍保持旧版完整）；T-16。并发锁不实现、改文档声明——同意（单用户工具）。新的边角见 N-1、N-3 |
| F-6 根入口 / P 集合 / `--adopt` 校验 | MEDIUM | **已解决** | §3.4 步骤 3：`lstat` 校验 `bundle/agate` 与每个登记根文件、`os.walk(followlinks=False)`、manifest `files` 与磁盘对账（多 / 少 / 改名均 exit 1，契约外文件不拷）；`copy_files` 逐个 `lstat`；`--adopt` 新形态调 `verify_dir`；`copytree(symlinks=True)`；T-6 / T-19 / T-20。小注见 N-7 |
| F-7 测试 tag 清理竞态 / 污染 | MEDIUM | **已解决（含一处补充）** | §11 重写：fork 演练首选；轮询到全部 `completed`（超时先 `gh run cancel`）才清理；名称精确匹配 `^v0\.73\.0-tagtest\.[0-9]+$`、无通配符、只读列出并回显确认、仅删本次创建；副作用向用户披露。补充见 N-2（`gh` 命令未显式指定目标仓库） |
| F-8 迁移提示硬编码 | LOW | 已解决 | §3.3 / §3.7 三步片段前增动态"检测到的软链"行，不影响 `_migration_steps` 正则 |
| F-9 正则 `$` 换行 | LOW | 已解决 | `fullmatch` + `re.ASCII`；E-15 表驱动（含 `v1.2.3\n`、Unicode 数字）；T-17 |
| F-10 `is-prerelease` exit 2 被吞 | LOW | 已解决 | §3.6 Publish 步骤 `case "$rc"` 三分支；T-8 / T-22 |
| F-11 路径硬化 | LOW | 已解决 | D-16 / §3.2 `list_package` 规则（`.git*`、`:`、结尾空格或点、控制字符、casefold 冲突、`tests` casefold 排除）+ `O_EXCL|O_NOFOLLOW`；E-13（69 tag、7127 文件 0 违规） |
| F-12 portable 命令鲁棒性 | LOW | 大体已解决 | §3.5 增默认值、解压前软链守卫、`mkdir` 无 `-p`、`sha256sum -c`；残余见 N-5 |
| F-13 其余小项 | LOW | 部分采纳，理由成立 | 采纳：`_cmd_adopt` 的 `OSError` 转 stderr、`git clone --`。不采纳：`pip` 改 `sys.executable -m pip`、`install.sh` `$SCRIPT_DIR` 回退——既有行为 + 范围锁定，已列 §13 backlog，同意 |
| F-14 workflow 静态测试增补 | LOW | 已解决 | §3.6 静态契约与 T-8：`run:` 不含 `${{`、`GH_TOKEN` 只在 Publish env、触发面限定、`set -euo pipefail`、`case` 三分支；tag 保护建议写入 AGENTS.md 发布清单 |

---

## 2. 复审新发现（修订引入 / 修订后才可见）

### N-1 [MEDIUM] `sweep_stale` 的匹配模式可能误删用户自建目录

- **BDD**：4 / 10 / 16；D-6、R-8、§3.2 `sweep_stale`、§3.3 `_install_version`、§3.4 步骤 5。
- **发现**：每次安装（在线与离线）开头执行 `sweep_stale(root)`，清扫版本根直属条目中匹配 `^v\d+\.\d+\.\d+\.(tmp|bak)-` 者，目录用 `rmtree`。该模式**只按名字判定**。实测（`cso2/proto.py`）：`v0.72.0.bak-20260920`、`v0.72.0.bak-before-upgrade` 均匹配；而"升级前手工备份一份版本目录，名字带日期后缀"（恰好是 `mkdtemp` 的 8 位随机后缀长度）是自然习惯。命中即被静默 `rmtree`，且发生在用户没有任何"删除"意图的 `install` 命令里。版本目录虽可重装，但旧 worktree 形态下用户可能在其中有本地改动。
- **相关的次要缺口**：换位第二步之前崩溃会留下"`vX.Y.Z` 缺失 + 备份存在"；下一次 `sweep_stale` 会直接删掉这份备份，而不是先把它还原。
- **建议**（设计文字补充即可，落入 §3.2 / R-8 与 T-16）：
  1. `mkdtemp` 创建的每个 `.tmp-` / `.bak-` 目录写入固定标记文件（如 `.agate-installer-scratch`），`sweep_stale` 只清扫**同时满足**名字模式、含标记、且 mtime 早于某阈值（如 1 小时）的目录；无标记者一律不动。
  2. 名字改用不易与手工命名冲突的前缀（如 `.agate-tmp-vX.Y.Z-` / `.agate-bak-vX.Y.Z-`，隐藏点前缀），并把模式收紧到 `mkdtemp` 的字符集与长度（`[a-z0-9_]{8}\Z`）。
  3. `sweep_stale` 遇到"`vX.Y.Z` 缺失且存在带标记的 `.bak-`"时先还原再继续（并打印一行说明）。
  4. T-16 增一条：版本根下预置 `v0.1.0.bak-20260920`（无标记）与 `v0.1.0.bak-before-upgrade`，安装后断言二者仍在。

### N-2 [MEDIUM] §11 的 `gh` 命令未显式指定目标仓库，fork 演练时清理命令可能指向 origin

- **BDD**：20；§11 步骤 1 / 6。
- **发现**：§11 首选 fork 演练，`git` 侧命令都带 `<remote>`，但 `gh release view "$TAG"`、`gh release delete "$TAG" --cleanup-tag --yes`、`gh run list/cancel` 均**不带 `-R`**。`gh` 在克隆目录里解析的是默认仓库（通常是 `origin` 即上游）。若演练在 fork 上做，这些命令实际打向上游：步骤 1 的"不存在"检查、步骤 6.1 的只读列出、步骤 6.2 的**删除**都可能作用于错误仓库；只有恰好上游也存在同名对象时才会误删，概率低，但这是本设计里唯一的远端删除动作，且"回显确认"看到的也是错仓库的结果。
- **建议**：§11 引入变量 `REPO=<owner>/<repo>`（演练仓库），所有 `gh` 命令显式带 `-R "$REPO"`；步骤 1 先 `gh repo view -R "$REPO" --json nameWithOwner` 回显并与用户确认，步骤 6.1 的回显同时打印 `$REPO`；同时断言 `git remote get-url <remote>` 与 `$REPO` 一致。T 侧无需用例（属人工执行清单），写入 §11 与 AGENTS.md 发布清单即可。

### N-3 [LOW] 换位实现的两个平台细节

- `swap_in` 备份用"`mkdtemp` 建目录，再 `os.rename(final, 该目录)`"：POSIX 上可以（已实测把目录改名到已存在的空 `mkdtemp` 目录上成功，`cso2/proto.py`），但 **Windows 的 `os.rename` 目标存在即失败**——按设计"Windows rename 失败即整体失败并回滚"，则 Windows 上"重装已存在版本"（S-16 的恢复路径）永远走不通。建议 `mkdtemp` 建一个**父目录**，备份为 `<父目录>/old`（目标名不存在）。
- `mkdtemp` 目录权限为 0700（实测）；设计只对 `materialize` 写了"完成后 `chmod(dest, 0o777 & ~umask)`"，`copy_files` 路径（离线安装）未写，换位后 `vX.Y.Z/` 会是 0700。建议 `copy_files` 同样收尾 `chmod`，并在 T-4 顺带断言三路径 `vdir` 的目录权限一致。

### N-4 [LOW] adopt 失败回滚不含指针

`rollback_swap` 只还原目录；`_register` 若已写 `latest`、随后写 `current` / 同步根 scripts 失败，全新安装（无旧目录可还原）时回滚删除新目录会留下悬空 `latest`。建议 `_register` 先做全部前置校验再写指针（写指针放最后一步、且只剩 `symlink` / 文本写两个原子动作），或回滚时对本次移动过的指针一并还原。属边角，非阻塞。

### N-5 [LOW] portable 文档守卫仍有一个字面缺口

§3.5 的 shell 守卫只循环剥离尾部 `/`。实测（`cso2/`）：`AGATE_HOME=<L>/.` 与 `<L>/./` 不会被 `[ -L ]` 捕获（`<L>` 与 `<L>/` 已捕获）。此时 `mkdir "$AGATE_HOME/vX.Y.Z"` 与 `tar -xzf` 会在第二道守卫（`--adopt`）之前把新目录建进软链目标——只新增目录、不覆盖既有文件（`mkdir` 无 `-p`），影响远小于首轮 F-1。建议文档片段与 `install.sh` 用同一段剥离（`/` 与 `/.` 循环）并拒绝含 `..` 的值；另外该片段中的 `AGATE_HOME` 为 shell 局部变量，若用户原本只是 shell 变量未 `export`，随后 `python3 … --adopt` 读到的是默认 `~/.agate`，两者不一致——片段里加 `export AGATE_HOME`。

### N-6 [LOW] `--expect-sha` 两侧归一化

`build` 只对 tag 一侧做 `^{commit}` 归一化。`GITHUB_SHA` 对附注 tag 是否为提交而非 tag 对象，设计与本次复审均未在 GitHub Actions 上验证（已在 not_validated 类似项覆盖）。建议实现时对 `--expect-sha` 也执行 `git rev-parse "$SHA^{commit}"`（对象在浅克隆内可解析），失败时给出明确文案；否则最坏情形是**安全失败**（附注 tag 发布被误拒），不是放行，故只记 LOW。

### N-7 [LOW] 字节码"忽略"口径的两个盲区

- 校验 / 比较一律忽略字节码（D-13）是为解决 eng B-1，方向正确；但 Python 即使带 `-B` 也会**读取**已存在的 `.pyc`（`-B` 只禁写）。portable 路径中 tarball 若夹带 `__pycache__/*.pyc`，`tar` 会原样解出，`--adopt` 的 `verify_dir(ignore_bytecode=True)` 与哈希都看不见，而 `agate_common` / `agate_package` 的导入会优先使用它。官方 tarball 由 `write_dir_tarball` 生成、不含字节码，且第三方恶意 tarball 本就可直接带恶意 `.py`，故不构成新的提权面，仅是"源码审阅 / 哈希看不到的执行体"这一点应在文档写明。建议 portable 小节在 `tar` 之前加 `tar -tzf agateon-vX.Y.Z.tar.gz | grep -E '__pycache__|\.py[co]$'` 应为空的一行检查，`install-offline` 对 bundle 内出现字节码打印告警。
- `--adopt` 以"无 `.git`"判定新形态才跑 `verify_dir`，形态由被检目录自己声明（放一个 `.git` 文件即可跳过校验）。同样只在不可信 tarball 场景有意义，影响限于绕过成员校验（`copytree(symlinks=True)` 已把软链当链接复制，不会读出目录外内容）。建议旧形态判定改为"`.git` 存在且 `repo/.git/worktrees/` 里有对应登记"。

---

## 3. STRIDE 复核（仅列相对首轮有变化的面）

| 面 | 变化 | 剩余 |
|----|------|------|
| 软链基址守卫（三入口 + `agate_common`） | 规范化 + 歧义检测，实测覆盖尾斜杠 / `/.` / 多斜杠 / 经软链的 `..` | portable 文档片段 `/.`（N-5） |
| 打包 / 拷贝 | `.git*`、`:`、结尾点空格、casefold 冲突、`O_EXCL|O_NOFOLLOW`、`lstat` 校验、manifest `files` 对账 | 字节码盲区（N-7） |
| 换位 | `mkdtemp` 临时 / 备份、失败回滚、adopt 后才删备份 | 清扫误删（N-1）、Windows 与权限（N-3）、指针回滚（N-4） |
| Release workflow | 令牌局部化、依赖固定、`--expect-sha`、`case` 三分支、静态断言增补 | `--expect-sha` 归一化（N-6）；`--require-hashes` / 来源证明 / tag 保护属 backlog 或文档建议，残余风险已在 R-7 / R-16 如实登记 |
| §11 测试 tag | fork 优先、等 run 完成、精确匹配、只读回显、副作用披露 | `gh -R`（N-2） |

## 4. 覆盖的 BDD

1 2 3 4 9 10 11 12 13 14 15 16 17 18 19 20 21 22 24 27 28 31 32 33 35 36 51（安全相关落点复核）；新增发现涉及 4 / 10 / 16（N-1、N-3、N-4）、20（N-2、N-6）、17 / 19（N-5、N-7）。

## 5. 建议的吸收方式（不需回 P2 review）

1. P3 用例：T-16 增"无标记的 `.bak-` 同名手工目录不被清扫"（N-1）；T-14 已覆盖 F-1，可再加 `L/./`（N-5 对应的 shell 侧）。
2. P4 实现：`sweep_stale` 标记文件 + 阈值（N-1）；`swap_in` 备份路径不预建（N-3）；`copy_files` 收尾 `chmod`（N-3）；`_register` 写指针置于最后（N-4）；`--expect-sha` 两侧归一化（N-6）。
3. 文档批（F1a / F2）：portable 片段同步 install.sh 的剥离与 `export`、增字节码列表检查（N-5、N-7）；§11 / AGENTS.md 发布清单写明 `-R "$REPO"`（N-2）。

## 6. 返回摘要（给主 Agent）

approved；最高严重级别 MEDIUM（2 项新增，非阻塞）；CRITICAL 0、HIGH 0；首轮 F-1（HIGH）经实测确认已修复。新建 scratchpad 目录：`.../scratchpad/cso2/`（`cso1/` 为首轮所建）。
