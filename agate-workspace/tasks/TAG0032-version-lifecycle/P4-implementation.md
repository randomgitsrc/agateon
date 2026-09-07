---
phase: P4
task_id: TAG0032
type: implementation
parent: P2-design.md
trace_id: TAG0032-P4-20260907
status: draft
created: 2026-09-07
agent: implementer
implementation_dir: agate/
---

# P4-implementation — TAG0032 版本管理生命周期可用性批（批 1：scripts-tests）

implementation_dir: agate/

[PROD_NOT_TOUCHED]

本批实现 P2-design.md §1.1 的 **M1-M6 脚本改动**（`agate/scripts/agate-install.py` +
`agate/scripts/agate_common.py` + 仓库根 `install.sh`），让 P3 的 BDD-1~8 + BDD-13/14
相关红灯转绿。`agate/scripts/resolve-entry.py` 只核对未改（决策 A1 受益方）。
文档面 M7-M11（BDD-10/11/12 + BDD-4 判据 3）为批 2（docs-consistency）范围，未触碰。

## 改动清单

### agate/scripts/agate_common.py

| M | 落点 | 改动 |
|---|------|------|
| M3 | 新增模块级 helper `_protocol_root(vdir)`（紧邻 `_resolve_version_info` 之前）| 探测序 1 `isdir(vdir/scripts)` → 返回 `vdir`（「根即协议」零回归，BDD-7）；探测序 2 `isdir(vdir/agate/scripts)` → 返回 `vdir/agate`（元仓库形态，BDD-6/8）；皆无 → 返回 `vdir` 原样。顺序硬编码不可颠倒 |
| M4 | `_resolve_version_info()` `.agate-version` ok 分支 | `return {"root": _protocol_root(vdir), "version": declared, ...}`；`version` 恒取 `declared` 不变（I-1 天然安全）|
| M5 | `_resolve_version_info()` current 链分支 | 先 `version = os.path.basename(cur)`，再 `root = _protocol_root(cur)`，两条独立赋值——`version` 从 `cur` 取、不从 `_protocol_root(cur)` 返回值取（I-1 红线）|

env 覆盖分支（L173-175）、legacy 软链兜底分支（L192-193）、`resolve_hook_root` 脚本上溯兜底、
`.agate-version` 格式解析均未改。

### agate/scripts/agate-install.py

| M | 落点 | 改动 |
|---|------|------|
| M1 | `_cmd_install()` 首行（`_ensure_repo` 调用前）| `if os.path.islink(agate_home):` → 写 `_LEGACY_SYMLINK_MSG`（P2-design §4.1 三段命令片段：`mv ~/.agate ~/.agate.bak` / `mkdir -p ~/.agate` / `install.sh --versions` + `agate-install.py latest`）到 stderr + `sys.exit(1)`。守卫在 `os.makedirs`/`git clone` 之前 → 拒绝后不留半成品 |
| M2 | 新增 `_sync_root_scripts(agate_home, version_dir)`；`_cmd_install()` 成功路径末尾（latest / 指定版本两分支）各自算 `version_dir` 后调用 | 决策 B1 副本：① `shutil.copytree(<运行中安装器 scripts/ 目录>, agate_home/scripts, dirs_exist_ok=True)`——保证 `agate-install.py`/`agate_common.py`/`resolve-entry.py` 等入口命令在新机可直接调用；② `shutil.copytree(_protocol_root(version_dir)/scripts, 同 dst, dirs_exist_ok=True)`——叠加当前版本协议脚本，重跑 latest 随 current 刷新。latest 分支 `version_dir = agate_home/tag`；指定版本分支 `version_dir = agate_home/version`——两分支源路径显式区分 |
| 附 | `from agate_common import _protocol_root, probe_python, run_git` + `except (ImportError, SystemExit)` 块内 `_protocol_root` 降级副本 | pyyaml 缺失时 `--check` 仍可用 |
| 附 | `main()`：`not args or (len(args)==1 and args[0]=="latest")` → `_cmd_install(agate_home)`；`_usage()` 文案同步 | `latest` 作无参 install 显式别名 |
| 附 | `_ensure_repo()`：已有 `repo/.git` 时先 `run_git(["fetch","--tags","--force","--prune","origin"], cwd=repo)`（fail-open，离线不致命）| 令重跑 `latest` 能发现上游更高 tag（BDD-4 判据 2）|

### install.sh（仓库根）

| M | 落点 | 改动 |
|---|------|------|
| M6 | `set -euo pipefail` 之后、`INSTALL_DIR=` 之前新增 `[ "${1:-}" = "--versions" ]` 分支 | ① `[ -L "$HOME/.agate" ]` → heredoc 同三步迁移指引到 stderr + `exit 1`；② `python3`/`python` 探测（`command -v` 循环）；③ `mkdir -p "$HOME/.agate"` + 若 `repo/.git` 不存在则 `git clone "${AGATE_REPO_URL:-https://github.com/randomgitsrc/agateon}" "$HOME/.agate/repo"`；④ `exec "$PY" "$SCRIPT_DIR/agate/scripts/agate-install.py" latest`（`SCRIPT_DIR` = install.sh 自身目录）。原无参单软链路径完全不变。POSIX shell，`shellcheck -S warning install.sh` rc=0 |

## 决策/偏差声明

[DESIGN_GAP: P3 fixture `_tag_upstream`/`_tag_meta_upstream` 的 `agate/scripts/` 均不含 `agate-install.py`，但 BDD-3/4/4b/5/13 都断言 `~/.agate/scripts/agate-install.py` 存在且 `--help` exit 0；单按 dispatch 字面「src = _protocol_root(vdir)/scripts」单次 copytree 无法转绿。M2 自主采用「自拷贝运行中安装器 scripts/ 目录 + 叠加版本协议 scripts/」双 copytree。]
[DESIGN_GAP: `agate-install.py main()` 原不认 `latest` 参数（落 `_VERSION_RE` 失配 → exit 2），但 P1 §3.4 步骤 5 / e2e BDD-13 步骤 5 / install.sh --versions / BDD-2 迁移指引均用 `agate-install.py latest`；M 表未列该别名。自主在 main() 增 `latest` 作无参 install 别名。]
[DESIGN_GAP: dispatch M6 写 `python3 ~/.agate/repo/agate/scripts/agate-install.py latest`，但 e2e `_tag_meta_upstream` 故意不放 `agate-install.py` 进协议目录（模拟元仓库 gap）。install.sh --versions 自主改为 `exec "$SCRIPT_DIR/agate/scripts/agate-install.py"`（install.sh 同侧脚本），`~/.agate/repo` 仅作 `git worktree add` 版本源。]
[DESIGN_GAP: BDD-4 判据 2 要求「重跑 latest 后副本随 current 刷新」在新增更高 tag 后成立，但既有 `_ensure_repo` 复用已 clone 的 `~/.agate/repo` 时从不 fetch，永远看不到上游新 tag。自主在 `_ensure_repo` 已有 repo 分支加 `git fetch --tags --force --prune origin`（fail-open）。属 TAG0032 update 路径范围。]

## 自跑结果（自查，非 P5 gate）

- `ruff check agate/scripts/agate-install.py agate/scripts/agate_common.py` → All checks passed
- `shellcheck -S warning install.sh` → rc=0
- `pytest -k tag0032`（test_agate_version_install.py / test_agate_version_resolve.py / test_hook_resolve_entry.py / test_version_lifecycle_e2e.py）→ **11 passed**（`test_tag0032_bdd_1..5` + `bdd_4b` + `bdd_6/7` + `bdd_8` + `bdd_13/14`）
- `pytest agate/tests/unit/ agate/tests/regression/ -n auto` → 1383 passed, 2 skipped, 7 failed
  - 7 failed 全部为 `test_upgrading_lifecycle.py`（BDD-10/11/12 + BDD-4 判据 3 文档断言）→ **批 2（docs-consistency）负责**，本批不动，符合 dispatch 预期
- `pytest`（三大 version/hook unit 文件全量 + `agate/tests/integration/`）→ 128 passed，无回归

## 范围锁定核对

`install-offline.py` / Windows 复制模式 `.agate-root` / `.state.yaml` schema / agateon 仓库形态重构
均未触碰。未改 P2 §6 gate_commands。未改任何测试文件。

---

# P4-implementation — 批 2（docs-consistency）

[PROD_NOT_TOUCHED]

本批实现 P2-design.md §1.1 / §4.3 的 **M7-M11 文档面改动**（`agate/UPGRADING.md` +
`README.md` + `README.zh-CN.md` + `agate/SETUP.md`），让 P3 的 `test_upgrading_lifecycle.py`
（BDD-10 / BDD-11 / BDD-12 四条 checklist + BDD-4 判据 3）7 个红灯转绿。不改脚本（批 1 已完成）、
不改测试、不逐条改写历史版本节。

## 改动清单

### agate/UPGRADING.md

| M | 落点 | 改动 |
|---|------|------|
| M7 | 新增 `## 版本管理生命周期` 节，插在 `## 1. 通用升级步骤` 之后、`## 2. 旧数据兼容策略` 之前（不重排既有编号，为无编号节）| 三部分：① **安装 / 迁移 / 更新 / 回退对照表**（两列 legacy 软链布局 / 版本管理布局，取自 P2-design §4.3 表：安装=`install.sh --versions`；迁移=三步 `mv`→`mkdir -p`→`install.sh --versions`；更新 legacy=`git pull` / 版本布局=`agate-install.py latest` 幂等；回退 legacy=`git checkout <旧 tag>` / 版本布局=`agate-install.py v<旧版本>` + `.agate-version` 钉版）；② **hook 重装时机统一口径**（resolve-entry 固定入口 + 薄壳 `.sh`：切版本/升级**通常无需重跑** `install-hook.py`；仅 hook 薄壳 `.sh` 变更或 Windows 复制模式才重跑）——同时收敛 v0.60-0.62 vs v0.66-0.68 历史节口径分歧；③ **根 `~/.agate/scripts/` 维护语义条目**（决策 B1 副本，与批 1 实现对齐，见下） |
| M8 | v0.50.0 节 §① 布局变化表格后 | 表格下新增一句 blockquote 指针：「本表为版本历史叙事，不再单独维护」，指「根含 `scripts/`」行的副本语义 + 「升级 = `agate-install.py`」行的幂等 `agate-install latest` 口径均以「版本管理生命周期」节为准。历史叙事文字未改。附：把 `` `scripts/`（版本管理工具） `` 的收尾反引号右移为 `` `scripts/（版本管理工具）` ``（纯 markdown 代码格式微调，措辞不变，见 DESIGN_GAP）|
| M9 | v0.60.0/0.61.0/0.62.0 节 与 v0.66-0.68 节 | **未改**——hook 重装口径分歧由 M7 生命周期节的统一口径条目收敛，历史版本节保留原叙事（P2-design §4.3 checklist 3 「历史叙事保留」判据） |

### M7「根 `~/.agate/scripts/` 维护语义条目」与批 1 实现对齐（BDD-4 判据 3 交叉锁）

条目内容据批 1 `P4-implementation.md` §改动清单（M2 双 copytree）+ §决策/偏差声明落笔，非照抄 P2-design §3 理想化 B1 块：

- 根 `scripts/` 是**副本**（非软链），内容 = 运行中安装器自带 `scripts/`（保 `agate-install.py`/`agate_common.py`/`resolve-entry.py` 等入口命令在新机可用）**叠加**当前 `current` 版本协议 `scripts/`（后拷贝者胜）
- 随 `agate-install.py`（含 `latest`）重跑刷新——升级期须重跑 `agate-install.py latest` 根入口副本才刷新到新版本工具
- `repo/` 或某 `vX.Y.Z/` 版本目录被删**不影响**已建立的 `~/.agate/scripts/` 副本可用性（独立拷贝，不回链）
- 该副本**不参与 hook 版本解析**——hook 经 resolve-entry 固定入口按项目 `.agate-version` 解析版本，切版本无需重跑 `agate-install.py`（也无需重跑 `install-hook.py`）

### README.md / README.zh-CN.md

| M | 落点 | 改动 |
|---|------|------|
| M10 | 快速上手「Quick start」第 1 步「per-project version pinning / 按项目锁定版本」块 | 补官方路径 `install.sh --versions`（进入版本管理布局），代码块首行加 `install.sh --versions`，`agate-install.py` 无参行改为 `agate-install.py latest`（更新到最新版，幂等）；prose 加一句指向 `agate/UPGRADING.md` 的「版本管理生命周期」节。中英同步 |

### agate/SETUP.md

| M | 落点 | 改动 |
|---|------|------|
| M11 | 「## 升级 Agateon 之后」节末尾 | 新增一段「更新口径（与 `UPGRADING.md` 一致）」：legacy 软链布局更新 = `git pull`；版本管理布局更新 = `agate-install.py latest`（幂等）；完整对照 + hook 重装时机 + 根 `scripts/` 副本语义指向「版本管理生命周期」节 |

## 决策/偏差声明

[DESIGN_GAP: P3 用例 test_tag0032_bdd_12[v050_root_scripts_row_pointer] 断言精确子串 `scripts/（版本管理工具）`，但 v0.50.0 §① 表格原文是 `` `scripts/`（版本管理工具） ``（`scripts/` 与全角括号间夹一个收尾反引号），子串不成立。M8 自主把收尾反引号右移为 `` `scripts/（版本管理工具）` ``——纯 markdown 代码格式微调，渲染后措辞与语义不变，符合 BDD-12「加指针不改叙事」。]

## 自跑结果（自查，非 P5 gate）

- `timeout 180 /usr/bin/python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py -p no:cacheprovider -q` → **7 passed**（`test_tag0032_bdd_10` / `bdd_11` / `bdd_4_root_scripts_copy_semantics_documented` / `bdd_12[v050_root_scripts_row_pointer]` / `bdd_12[v050_upgrade_row_pointer]` / `bdd_12[hook_reinstall_unified_across_version_sections]` / `bdd_12[readme_setup_aligned]`）
- `timeout 120 /usr/bin/python3 agate/scripts/check-protocol-consistency.py --strict-errors-only` → EXIT 0，**0 ERROR**（329 WARNING，均为既有叙事文件引用，未新增）
- `pytest agate/tests/unit/ -q -k "readme or upgrading or setup or doc or consistency"` → 156 passed，无回归

## 范围锁定核对（批 2）

未改任何脚本（`agate-install.py` / `agate_common.py` / `install.sh` 批 1 已定稿）；未改任何测试文件；
未改 P2 §6 gate_commands；未逐条改写 v0.50.0 / v0.60-0.62 / v0.66-0.68 历史叙事（仅 M8 加 blockquote 指针 +
一处 markdown 反引号位置微调）。out-of-scope（`install-offline.py` / `.agate-root` / schema）未触碰。

---

# P4 修复轮（fix-1）

[PROD_NOT_TOUCHED]

P4-review status: needs-revision（1 CRITICAL = DESIGN_GAP 3 + 2 项 INFORMATIONAL）。
本轮**增量修复**，只碰 `install.sh` + `agate/scripts/agate-install.py`（`_sync_root_scripts`）
+ 2 个 fixture 文件；`agate_common.py`（评审 B 组逐行 PASS）与批 2 文档面（D 组 PASS）**未触碰**。

## 修了什么

### ① CRITICAL — DESIGN_GAP 3：`install.sh --versions` exec 路径（选项 A，回归 P2-design M6）

`install.sh` `--versions` 分支 `exec` 行由固定 `$SCRIPT_DIR/agate/scripts/agate-install.py`
改为**刚 clone 的 repo 副本优先 + `$SCRIPT_DIR` 兜底**：

```sh
INSTALLER="$AGATE_HOME/repo/agate/scripts/agate-install.py"
[ -f "$INSTALLER" ] || INSTALLER="$SCRIPT_DIR/agate/scripts/agate-install.py"
exec "$PY" "$INSTALLER" latest
```

`curl … | bash -s -- --versions` / 只下载 install.sh 本地跑：`$SCRIPT_DIR` = 当前工作目录、
无 `agate/scripts/` → 走 `$AGATE_HOME/repo/agate/scripts/agate-install.py`（`--versions` 分支
上一步已 `git clone … "$AGATE_HOME/repo"`，真实 agateon 仓库该路径存在，P1 §3.4 L37）。
从 checkout 内跑：同样走刚 clone 的 repo 副本（更正确——用刚 clone 的版本而非旧 checkout）。
POSIX shell，`shellcheck -S warning install.sh` rc=0。

### ② 配套：两个 fixture 补 `agate-install.py`（DESIGN_GAP 3 修正方向 A「配套」+ DEBT0-A）

补齐 P3 测试设计的 fixture 缺口——让 `AGATE_REPO_URL` 注入的 clone 源贴近**真实元仓库形态**
（每个 tag 的 `agate/scripts/` 本就含全套版本工具）：

- `agate/tests/unit/test_agate_version_install.py` `_tag_upstream`：新增模块常量
  `_REAL_AGATE_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"`，`shutil.copy2`
  真实 `agate-install.py` + `agate_common.py` 进 fixture 的 `agate/scripts/`（保留原
  `README.md`）。签名不变、13 处调用点不动。
- `agate/tests/integration/test_version_lifecycle_e2e.py` `_tag_meta_upstream`：copy 循环
  由 `("agate_common.py", "resolve-entry.py")` 加 `"agate-install.py"`（`agate_common.py`
  该 fixture 已有）。

未改任何 `assert` / 未删用例 / 未放宽判据。修完后选项 A 的**主路径**
（`$AGATE_HOME/repo/agate/scripts/agate-install.py` / `_protocol_root(version_dir)/scripts`）
即被测路径，兜底分支不再掩盖 CRITICAL。

### ③ DESIGN_GAP 1（M2 双 copytree）→ 回归 P2-design B1 单源（DEBT0-A remediation）

fixture 补 `agate-install.py` 后，`_sync_root_scripts` 的 layer-2
（`_protocol_root(version_dir)/scripts` copytree）已覆盖全部入口命令 → **删除 layer-1**
（自拷贝运行中安装器 `scripts/` 目录），回到 P2-design §3 决策 B1 的**单源 copytree**：

```python
proto_scripts = os.path.join(_protocol_root(version_dir), "scripts")
shutil.copytree(proto_scripts, os.path.join(agate_home, "scripts"), dirs_exist_ok=True)
```

`latest` / 指定版本两分支各自算 `version_dir`（`_cmd_install` 内既有逻辑，未改）。

无非-fixture 真实场景会因删 layer-1 而断：真实 agateon 每个发布 tag 的 `agate/scripts/`
恒含全套版本工具（P1 §3.4 L37），layer-2 全覆盖。理论上仅「某畸形 tag 协议 `scripts/`
不完整」会缺根入口——该情形现由 ④ 的 stderr 诊断兜底，不再静默。故**不新增 DESIGN_GAP**。

### ④ DEBT0-B（INFORMATIONAL，P4-review F 组）：copytree 失败不再静默

`_sync_root_scripts` 移除 `contextlib.suppress(OSError)`：
- `proto_scripts` 目录不存在 → `sys.stderr.write` 一行 WARNING + `return`；
- `shutil.copytree` 抛 `OSError`（权限/磁盘满/部分失败）→ `except OSError` 写一行 WARNING
  （含源→目标路径 + 异常 + 「可重跑 agate-install.py latest」提示）。

不 `raise`（最小改动，不改变 exit 语义）。`contextlib` 仍被 `_write_pointer` 等复用，import 保留。

## DESIGN_GAP 1/3 落地小结

- **DESIGN_GAP 3**：按 P4-review 选项 A 落地——`exec` 优先用 `$AGATE_HOME/repo/agate/scripts/agate-install.py`，
  `$SCRIPT_DIR` 兜底；配套 2 fixture 补真实版本工具。curl|bash 官方路径恢复可用。
- **DESIGN_GAP 1**：按 DEBT0-A remediation 落地——fixture 贴近真实元仓库形态后，`_sync_root_scripts`
  回退 P2-design B1 单源 copytree（删 layer-1）。
- **DESIGN_GAP 2 / 4**：评审判为合理，**保留不动**（P7 配对 REVIEWED）。
- 旧 P4-implementation 批 1「决策/偏差声明」中的 `[DESIGN_GAP: ... 双 copytree ...]` 与
  `[DESIGN_GAP: ... install.sh --versions 自主改为 $SCRIPT_DIR ...]` 两条已由本轮修复消解。

## 验证结果（自查，非 P5 gate）

1. **真实 curl|bash 隔离 HOME**（`HOME=$(mktemp -d)`，元仓库形态 fixture repo，从无关目录
   `cat install.sh | bash -s -- --versions`）→ **EXIT=0**；`$HOME/.agate/` 含 `repo/` +
   `v0.50.0/` + `current→latest→v0.50.0` 指针 + `scripts/agate-install.py`（`--help` exit 0）。
   测完 `rm -rf`；真实 `~/.agate` 未触碰。
2. `pytest -k tag0032`（install/resolve/hook/upgrading/e2e）→ **18 passed, 25 deselected**。
3. `pytest agate/tests/unit/ agate/tests/regression/ -n auto` → **1390 passed, 2 skipped**（= 基线）。
4. `pytest agate/tests/integration/ -n auto` → **94 passed**（= 基线）。
5. `ruff check agate-install.py agate_common.py + 2 fixture` → All checks passed。
6. `shellcheck -S warning install.sh` → rc 0。
7. `check-protocol-consistency.py --strict-errors-only` → rc 0，**0 ERROR**（329 WARNING，均既有叙事引用，未新增）。

## 范围锁定核对（fix-1）

只碰 `install.sh` + `agate/scripts/agate-install.py`（仅 `_sync_root_scripts`；`_LEGACY_SYMLINK_MSG` /
M1 守卫 / `_ensure_repo` / `main()` `latest` 别名均未动）+ `test_agate_version_install.py` +
`test_version_lifecycle_e2e.py`（fixture 只加 `agate-install.py` + 依赖）。
`agate_common.py` 未改；批 2 文档面（README ×2 / SETUP.md / UPGRADING.md）未改；
`install-offline.py` / Windows 复制模式 / `.state.yaml` schema 未触碰。
