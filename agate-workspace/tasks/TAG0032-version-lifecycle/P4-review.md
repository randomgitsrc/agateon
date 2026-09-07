---
phase: P4
task_id: TAG0032
type: review
parent: P4-implementation.md
trace_id: TAG0032-P4review-re1-20260907
agent: review
status: approved
created: 2026-09-07
updated: 2026-09-07
---

# P4-review — TAG0032 版本管理生命周期可用性批（偏执 Staff Engineer / 上线前最后一道门）

> **本文件为 P4 复评轮（re-review-1）结论，原地覆盖首轮内容。**
> 首轮 `status: needs-revision`，1 CRITICAL = DESIGN_GAP 3（`install.sh --versions` 弃用 `~/.agate/repo/…` 改用管道下无效的 `$SCRIPT_DIR` → 新机 curl｜bash 官方路径 EXIT=2）。
> implementer 回改见 `P4-implementation.md` `# P4 修复轮（fix-1）` 节。本轮只核查 CRITICAL 是否真正消解 + 无回归 + 无新 DESIGN_GAP，不重走全量评审。

[PROD_NOT_TOUCHED] — 只审不写。curl｜bash 真实场景复现用隔离 HOME（`HOME=$(mktemp -d)`，测完 `rm -rf`），未触碰真实 `~/.agate`（本机 `~/.agate` 为指向 `oclab/agateon/agate` 的 legacy 软链，复现前后一致）。

---

## 结论

**status: approved** — 0 CRITICAL。首轮唯一 CRITICAL（DESIGN_GAP 3）已按 P4-review 首轮**选项 A**真正消解：
`install.sh --versions` 的 `exec` 改为「刚 clone 的 `$AGATE_HOME/repo/agate/scripts/agate-install.py` 优先 + `$SCRIPT_DIR` 仅 `[ -f ]` 兜底」，回归 P2-design §4.2 M6 意图。**独立复现真实 curl｜bash 场景（隔离 HOME，元仓库形态 fixture repo，从无关目录 `cat install.sh | bash -s -- --versions`）→ EXIT=0**，`~/.agate/` 下 `repo/` + `vX.Y.Z/` + `current`/`latest` 指针 + `scripts/agate-install.py`（`--help` exit 0）全部建立，且实走**主路径**（`$SCRIPT_DIR` 为无关工作目录、无 `agate/scripts/` → 兜底分支未触发）。

配套两个 fixture（`_tag_upstream` / `_tag_meta_upstream`）**纯增量**补 `agate-install.py`（+ 依赖），贴近真实元仓库形态——git diff 逐行确认**未改任何 `assert` / 未删用例 / 未放宽判据**。DESIGN_GAP 1（M2 双 copytree）借此回归 P2-design §3 决策 B1 的**单源 copytree**（删 layer-1 自拷贝层），论证成立。DEBT0-B 一并落地（移除 `contextlib.suppress(OSError)`，失败改 stderr WARNING，不 `raise`）。

DESIGN_GAP 2（`latest` 别名）/ DESIGN_GAP 4（`_ensure_repo` fetch）首轮已判合理，本轮确认保留不动（P7 配对 REVIEWED）。范围锁定：fix-1 只碰 `install.sh` + `agate-install.py`（仅 `_sync_root_scripts` + 首轮已 PASS 的 `_protocol_root` import/降级副本）+ 2 fixture；`agate_common.py`（B 组 PASS）与批 2 文档面（D 组 PASS）未触碰；无新 DESIGN_GAP / CLARIFY。

首轮 B/C/D/E/F 六组已 PASS，不重复长篇复核（下方一句话带过）。DEBT0-A / DEBT0-B / DEBT0-C 登记建议见首轮记录（DEBT0-A 已由 fix-1 的 fixture 修复 + 单源 copytree 落地其 remediation；DEBT0-B 已落地；DEBT0-C「三步迁移文案双写」仍留存，属 low，P7 可跟）。

| 核查项 | 结论 |
|--------|------|
| 1. CRITICAL（DESIGN_GAP 3）真正消解 | **PASS** — exec 行 repo 副本优先 + `$SCRIPT_DIR` `[ -f ]` 兜底；独立复现 curl｜bash EXIT=0、走主路径、兜底未触发 |
| 2. fixture 改动是补缺口不是迁就 | **PASS** — 两 fixture 纯增量补 `agate-install.py`（+ 依赖）；无 `assert` 改动 / 无删用例 / 无放宽判据 |
| 3. DESIGN_GAP 1 消解（单源 copytree） | **PASS** — `_sync_root_scripts` 现单段 `copytree(_protocol_root(version_dir)/scripts, dst)`；layer-1 已删；删 layer-1 论证成立（真实 tag 恒含全套工具，畸形 tag 由 ④ stderr 兜底） |
| 4. DEBT0-B 落地 | **PASS** — 移除 `contextlib.suppress(OSError)`；proto 缺失 → stderr WARNING + return；`copytree` `OSError` → `except` 写 WARNING；均不 `raise` |
| 5. 无回归 + 无越界 | **PASS** — fix-1 仅动 `install.sh` + `agate-install.py`（`_sync_root_scripts` 一处）+ 2 fixture；`agate_common.py` / `_LEGACY_SYMLINK_MSG` / M1 守卫 / `_ensure_repo` / `main` `latest` 别名 / 批 2 文档面未动；独立复跑 tag0032 18 passed、version/resolve/hook/upgrading/e2e 43 passed、shellcheck rc 0、consistency 0 ERROR |
| 6. 有无新 DESIGN_GAP / CLARIFY | **PASS** — fix-1 节无新增 `[DESIGN_GAP:` / `[CLARIFY:` 标记；首轮两条 batch-1 标记（双 copytree / `$SCRIPT_DIR` 旁路）已消解；GAP 2/4 保留待 P7 |

---

## 逐条核查（PASS/FAIL + 锚点）

### 核查项 1 — CRITICAL（DESIGN_GAP 3）真正消解 — **PASS**

**exec 行核查（`install.sh` `--versions` 分支，git diff HEAD）**：
```sh
INSTALLER="$AGATE_HOME/repo/agate/scripts/agate-install.py"
[ -f "$INSTALLER" ] || INSTALLER="$SCRIPT_DIR/agate/scripts/agate-install.py"
exec "$PY" "$INSTALLER" latest
```
- `$AGATE_HOME/repo/agate/scripts/agate-install.py`（上一步 `git clone … "$AGATE_HOME/repo"` 刚建立）**优先**；
- `$SCRIPT_DIR/agate/scripts/agate-install.py` 仅在前者 `[ -f ]` 为假时兜底。
- 与 P4-review 首轮**选项 A（推荐，回归 P2-design §4.2 M6）**代码片段逐字一致；与 P2-design M6「用刚 clone 的 `~/.agate/repo` 内安装器」意图对齐。

**独立复现真实 curl｜bash 场景（[PROD_NOT_TOUCHED]）**：
- 隔离 `HOME=$(mktemp -d)`；构造元仓库形态 fixture repo（`agate/scripts/` 内含真实 `agate_common.py` / `resolve-entry.py` / `agate-install.py` + stub gate，根**无** `scripts/`；两 commit + `v0.43.0`/`v0.50.0` tag，仿 `test_version_lifecycle_e2e.py::_tag_meta_upstream`）；
- **从无关目录**（非仓库 checkout）执行 `HOME=<iso> AGATE_REPO_URL=<fixture repo> cat <worktree>/install.sh | bash -s -- --versions`：
  ```
  正克隆到 '<iso>/.agate/repo'... 完成。
  已安装 latest → v0.50.0
  EXIT=0
  ```
- `<iso>/.agate/` 结果：`repo/`（dir）、`v0.50.0/`（dir）、`current -> latest`、`latest -> v0.50.0`、`scripts/`（含 `agate-install.py` / `agate_common.py` / `resolve-entry.py` / `pre-commit-gate.py` / `VERSION.txt`）。
- `HOME=<iso> python3 <iso>/.agate/scripts/agate-install.py --help` → EXIT=0。
- 测完 `rm -rf <iso>`；真实 `~/.agate`（软链）未触碰。

对比首轮同款复现（首轮 EXIT=2、`~/.agate/scripts/` 从未建立）→ **CRITICAL 已消解**。

**主路径 vs 兜底**：复现中 `$SCRIPT_DIR` = 无关工作目录，`$SCRIPT_DIR/agate/scripts/agate-install.py` 不存在 → `[ -f "$INSTALLER" ]` 命中 `$AGATE_HOME/repo/agate/scripts/agate-install.py`（fixture 补齐后存在）→ **实走主路径**，兜底分支未参与。
`test_tag0032_bdd_5`（`test_agate_version_install.py:454`）虽以 worktree 全路径调 `install.sh`（`$SCRIPT_DIR` = worktree 根，兜底路径本也有效），但 fixture 补 `agate-install.py` 后 `$AGATE_HOME/repo/agate/scripts/agate-install.py` 于 clone 后即存在 → 该用例现同样先命中主路径分支。e2e BDD-13（`test_version_lifecycle_e2e.py`）经 `_tag_meta_upstream` 补齐后同理。**兜底分支不再掩盖问题**。

### 核查项 2 — fixture 改动是补缺口不是迁就 — **PASS**

git diff HEAD 逐行：
- `agate/tests/unit/test_agate_version_install.py`：新增模块常量 `_REAL_AGATE_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"`；`_tag_upstream` 内在既有 `README.md` 写入后加 `for name in ("agate-install.py", "agate_common.py"): shutil.copy2(str(_REAL_AGATE_SCRIPTS / name), str(scripts / name))`。**纯增量**，`shutil` / `Path` 已在文件既有 import。
- `agate/tests/integration/test_version_lifecycle_e2e.py`：`_tag_meta_upstream` 的 copy 循环 `("agate_common.py", "resolve-entry.py")` → `("agate_common.py", "resolve-entry.py", "agate-install.py")`，加一个元素。
- 两处均**未改任何 `assert` / 未删用例 / 未新增或放宽判据 / 未改 fixture 形态铁律**（`_tag_meta_upstream` 仍「协议在 `agate/` 子目录、根无 `scripts/`」的 I-5 形态）。

补 `agate-install.py` 贴合 P1-requirements §3.4 L37「版本工具在 `repo/agate/scripts/`」——真实每个发布 tag 的 `agate/scripts/` 本就含全套版本工具，fixture 此前故意缺失才是缺口。属**补缺口**。

### 核查项 3 — DESIGN_GAP 1 消解（`_sync_root_scripts` 单源 copytree） — **PASS**

git diff HEAD（`agate/scripts/agate-install.py` `_sync_root_scripts`）：
```python
dst = os.path.join(agate_home, "scripts")
proto_scripts = os.path.join(_protocol_root(version_dir), "scripts")
if not os.path.isdir(proto_scripts):
    sys.stderr.write("WARNING: 版本协议 scripts/ 不存在（…）…可重跑 agate-install.py latest\n")
    return
try:
    shutil.copytree(proto_scripts, dst, dirs_exist_ok=True)
except OSError as exc:
    sys.stderr.write("WARNING: 根入口副本同步失败（…）…可重跑 agate-install.py latest\n")
```
- **单段 copytree**，`src` = `_protocol_root(version_dir)/scripts`（决策 A1 探测结果），与 P2-design §3 决策 B1（L140-141 / L164-167）「单源 `shutil.copytree(src, …, dirs_exist_ok=True)`」一致。
- **layer-1（自拷贝运行中安装器 `scripts/` 目录）确已删除**——首轮 diff 的第 1 段 `shutil.copytree(<运行中安装器 scripts/>, dst, …)` 在本轮 diff 中不再出现。
- `_cmd_install` 两分支调用点未改：latest 分支 `_sync_root_scripts(agate_home, os.path.join(agate_home, tag))`、指定版本分支 `…, os.path.join(agate_home, version))`。

**删 layer-1 后无真实场景缺根入口——论证成立**：
- P1-requirements §3.4 L37 明确版本工具随协议仓在 `agate/scripts/`，真实 agateon 每个发布 tag 的 `agate/scripts/` 恒含 `agate-install.py` / `agate_common.py` / `resolve-entry.py` → layer-2（现唯一段）`dirs_exist_ok=True` copytree 即全覆盖。
- 唯一残余风险「某畸形 tag 协议 `scripts/` 不完整」：现由核查项 4 的 stderr WARNING 显式诊断（`proto_scripts` 不存在 → WARNING + return；部分失败 → `except OSError` WARNING），不再静默 → 用户可据提示重跑，非事后在「No such file」处才发现。可接受，**不构成新 DESIGN_GAP**。

### 核查项 4 — DEBT0-B 落地 — **PASS**

git diff HEAD：`_sync_root_scripts` 两处 copy 路径**均无 `contextlib.suppress(OSError)` 包裹**：
- `proto_scripts` 目录不存在 → `sys.stderr.write(WARNING …)` + `return`；
- `shutil.copytree` 抛 `OSError`（权限 / 磁盘满 / 部分失败）→ `except OSError as exc: sys.stderr.write(WARNING …含源→目标 + exc + 「可重跑 agate-install.py latest」…)`。
- **均不 `raise`**（最小改动，不改变 `_cmd_install` 的 exit 语义——成功路径仍 `sys.exit(0)`）。
- `contextlib` import 保留（`_write_pointer` 等仍复用），无副作用。

符合首轮 DEBT0-B remediation「失败时至少 stderr 一行」。

### 核查项 5 — 无回归 + 无越界 — **PASS**

- **fix-1 触碰面**（git diff HEAD 代码文件 + P4-implementation.md fix-1 节范围锁定核对）：`install.sh`（exec 行 + 注释）、`agate/scripts/agate-install.py`（仅 `_sync_root_scripts` 函数体；首轮已 PASS 的 `_protocol_root` import 行 / `except` 块降级副本属 batch-1，未再动）、`agate/tests/unit/test_agate_version_install.py`、`agate/tests/integration/test_version_lifecycle_e2e.py`。
- **未触碰**（git diff HEAD 比对）：
  - `agate/scripts/agate_common.py` diff = batch-1 的 M3/M4/M5（`_protocol_root` 新增 + `_resolve_version_info` 两处调用），与首轮 **B 组逐行 PASS** 内容一字不差，fix-1 未再改；
  - `agate-install.py` 的 `_LEGACY_SYMLINK_MSG` 常量 / M1 `os.path.islink(agate_home)` fail-closed 守卫 / `_ensure_repo` 的 `git fetch --tags --force --prune origin`（fail-open）/ `main()` `latest` 别名 / `_usage()` 文案 —— 均为 batch-1 内容，fix-1 diff 中无改动（首轮 C 组 / GAP 2 / GAP 4 已 PASS）；
  - 批 2 文档面 `README.md` / `README.zh-CN.md` / `agate/SETUP.md` / `agate/UPGRADING.md` —— fix-1 未改（首轮 D 组 PASS）；
  - `install-offline.py` / `agate-pack-offline.py` / Windows 复制模式 / `.state.yaml` schema —— 无 diff。
- **DESIGN_GAP 2 / 4 保留不动**：`main()` `latest` 分支、`_ensure_repo` fetch 行在本轮 diff 中未变。
- **独立复跑（本机 `/usr/bin/python3`）**：
  - `pytest agate/tests/ -k tag0032` → **18 passed, 1490 deselected**（1.97s）；
  - `pytest test_agate_version_install.py test_agate_version_resolve.py test_hook_resolve_entry.py test_upgrading_lifecycle.py test_version_lifecycle_e2e.py` → **43 passed**（6.37s）；
  - `shellcheck -S warning install.sh` → **rc 0**；
  - `check-protocol-consistency.py --strict-errors-only` → **rc 0 / 0 ERROR**（329 WARNING，全为既有叙事引用，未新增）。
  - 主 Agent 已复跑全量 unit+regression 1390 passed/2 skipped（= 基线）、integration 94 passed（= 基线）——与本轮抽查一致，diff 无明显回归风险点。

### 核查项 6 — 有无新 DESIGN_GAP / CLARIFY — **PASS**

- `P4-implementation.md` `# P4 修复轮（fix-1）` 节全文扫描：无新增 `[DESIGN_GAP:` / `[CLARIFY:` / `[SCOPE+]` / `[BASELINE_CHANGE:` 行首标记；「③」节明确「故**不新增 DESIGN_GAP**」并给出论证（见核查项 3）。
- 首轮 4 条 DESIGN_GAP 中 2 条（M2 双 copytree、`install.sh --versions` 改 `$SCRIPT_DIR`）本轮消解，节末「DESIGN_GAP 1/3 落地小结」明列旧 batch-1「决策/偏差声明」两条标记已被覆盖。
- 保留 2 条（DESIGN_GAP 2 `latest` 别名 / DESIGN_GAP 4 `_ensure_repo` fetch）——首轮已判合理，P7 配对 REVIEWED。
- 批 2 v0.50.0 反引号微调（首轮 D 组判 INFORMATIONAL / 可接受）不受本轮影响。

---

## 六组复核（首轮 PASS，一句话带过）

| 组 | 复核 |
|----|------|
| B. 决策 A1（`_protocol_root` 探测序 / M4 M5 version 推导顺序） | 首轮逐行 PASS；fix-1 未触碰 `agate_common.py`，git diff 确认与首轮内容一致 → 维持 PASS |
| C. 断点一 fail-closed 守卫（M1 `os.path.islink` 前置 + 三段命令片段） | fix-1 未触碰 `_LEGACY_SYMLINK_MSG` / M1 守卫 → 维持 PASS |
| D. 文档面 M7-M11（UPGRADING / README×2 / SETUP） | fix-1 未触碰文档面；首轮「文档承诺一条不通的路」INFORMATIONAL 随 DESIGN_GAP 3 消解而自动化解 → 维持 PASS |
| E. 范围锁定 + 回归 | 本轮独立复跑绿（见核查项 5）；触碰面比首轮多 2 fixture + `install.sh`/`_sync_root_scripts`，均在 fix-1 授权范围内 → 维持 PASS |
| F. 可维护性 | `check-maintainability` 首轮 0 violations；fix-1 的 DEBT0-B 落地（移除 suppress）反而降债；DEBT0-C（三步文案双写，low）留存待 P7 → 维持 PASS |

---

## 门槛自检

- P4-review.md 原地覆盖、非空、Header `status: approved`、`agent: review`（非 main）、`trace_id: TAG0032-P4review-re1-20260907` ✔
- 正文含 6 项核查逐条 PASS + 独立复现结果（curl｜bash 隔离 HOME EXIT=0）✔
- 结论引用具体锚点（`install.sh` exec 行片段 / `agate-install.py` `_sync_root_scripts` / `_protocol_root` / fixture diff 逐行 / P2-design §3 B1 + §4.2 M6 / P1 §3.4 L37 / 复现 EXIT 值）✔
- CRITICAL 真正消解（复现 EXIT=0，走主路径、兜底未触发）+ fixture 补缺口未迁就（无 assert 改动）+ 无回归（tag0032 18 / 43 passed、shellcheck rc 0、consistency 0 ERROR）+ 无新 DESIGN_GAP → **approved** ✔
