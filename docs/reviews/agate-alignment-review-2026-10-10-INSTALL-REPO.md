---
review_date: 2026-10-10
reviewer: protocol-alignment-review
change_summary: install.sh 遇 repo/ 已存在时新增 `git pull --ff-only` 更新已存在的主克隆（RM-AG0069 升级自举缺口）
files_changed: [install.sh, agate/tests/unit/test_install_sh.py]
---

# 协议-脚本对齐审查（RM-AG0069 / install.sh repo 更新）

**审查对象**：分支 `hotfix/install-repo-update`（**未提交**，改动在工作区）。
**改动集**：`install.sh`（+9 行：`else` 分支 `git pull --ff-only`）、`agate/tests/unit/test_install_sh.py`（+48 行：新增 `test_rm_ag0069_rerun_updates_existing_repo`）。
**权威源**：`agate-workspace/roadmap/roadmap.md:91`（RM-AG0069）、`install.sh`、`agate/UPGRADING.md`（`### v0.73.0` 第 7 条 / 「版本管理生命周期」节）、`agate/scripts/agate-install.py::_ensure_repo`。
**只读纪律**：全程只读仓库；所有写类/变异操作在副本 `/tmp/opencode/instrepo`（`cp -a` 含未提交改动）上跑，跑后原仓 `git status` 仅含本报告与留痕文件。

---

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **ALIGNED** |
| A2 | 脚本→文档对齐 | **MISALIGNED** |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** |
| A4 | 测试覆盖 | **ALIGNED** |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**（空清单，经实测） |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** |
| A6 | 锚点表覆盖 | **ALIGNED**（N/A） |
| A7 | 设计原则一致性 | **ALIGNED** |
| A8 | 声称-命令绑定 | **ALIGNED**（一处数字按实测更正） |

**是否可 commit**：**否**——先处理 A2/A3/A5 的文档/roadmap/CHANGELOG 缺口，并建议采纳「重点 1」的诊断改进；修完重审。
（核心代码改动本身**正确且安全**，测试**有判别力**，不构成阻断；上述缺口均为**文档面**，可小改完成。）

---

## 逐项审查

### A1: 文档→脚本对齐 — ALIGNED

**文档声明**（`roadmap.md:91`，RM-AG0069「拟做」）：
> `repo/` 已存在时先 `git pull --ff-only`（失败降级为 WARNING、不阻断、不改写本地历史），使重跑 `install.sh` 即可获得最新安装器

**脚本实现**（`install.sh:70-80`）：
```bash
if [ ! -d "$AGATE_VER_ROOT/repo/.git" ]; then
    git clone -- "${AGATE_REPO_URL:-https://github.com/randomgitsrc/agateon}" "$AGATE_VER_ROOT/repo"
else
    if ! git -C "$AGATE_VER_ROOT/repo" pull --ff-only >/dev/null 2>&1; then
        echo "警告: 更新 $AGATE_VER_ROOT/repo 失败（网络或本地改动/分叉？）——继续用现有副本（RM-AG0069）" >&2
    fi
fi
```

逐条核对：`repo/` 已存在时先 `pull` ✓；`--ff-only`（不改写本地历史，见 A1 安全性分析）✓；失败仅 `echo` 到 stderr、**无 `exit`** ⇒ 不阻断（`set -euo pipefail` 下 `if !` 已吞掉非零，不触发 `set -e`）✓。

**结论**：ALIGNED。语义与 roadmap 一致。
（注：WARNING 文案本身不含 git 失败真因——这是**诊断质量**问题，记在「重点 1」，不在 A1 语义面。）

### A2: 脚本→文档对齐 — MISALIGNED

**变更引入的新行为**：重跑 `install.sh` 现在会 `git pull --ff-only` **更新已存在的 `repo/`**（`install.sh:72-79`）。这使「重跑新 `install.sh`」即可获得最新安装器，从而**消解**了旧安装器场景下「两步升级」的必要性（对本改动所覆盖的新 `install.sh` 路径而言）。

**应被同步、但 diff 未含的文档**：

1. `agate/UPGRADING.md:809`（`### v0.73.0` 第 7 条）标题即 **「升级说明（两步升级，仅文档）」**，正文称「该次安装会把根 `scripts/` 同步为 v0.73.0 自带的新安装器，此后经根 `scripts/` 执行的安装……才只装本体」——**未提**「重跑新 `install.sh` 会先 `pull repo/` 拿到最新安装器」。代码注释（`install.sh:74`）自述理由为「仅靠文档说明「两步升级」不足」⇒ 作者的意图正是**以代码补文档之不足**，但文档未随之更新。第 7 条的字面范围（**旧安装器**）仍成立，故非「文本为假」，而是**新行为缺记 + 「仅文档」措辞已不完整**。
2. `agate/UPGRADING.md:57`（「版本管理生命周期」安装行）仅描述 `install.sh` 建 `repo/` + 首个版本 + 指针 + 根 `scripts/`，**未提**重跑更新 `repo/`。
3. `install.sh:1-12`（脚本头注释，本身是「行为文档」）未提 `repo/` 已存在时的更新行为。

**结论**：MISALIGNED。**建议**（最小改动，择一或并取）：
- 在 `UPGRADING.md:809` 第 7 条补一句：「用**新版 `install.sh`**（`curl … | bash`）重跑时会先 `git pull --ff-only` 更新 `repo/`，从而直接取到新版安装器，无需手动两步」；
- 在 `UPGRADING.md:57` 安装行或 `install.sh` 头注释补一句「重跑会 `--ff-only` 更新已存在的 `repo/`，失败仅 WARNING」。

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a（已知衍生改动）**：本改动不触碰任何 gate / `check-*.py` / 契约字段，无链式衍生改动。**ALIGNED**。

**A3b（主动推断的「应被影响但未列在 diff」的文件）**——逐条验证：

| 反向传播候选 | 是否属本条 | 验证结论 |
|---|---|---|
| `_sync_root_scripts` 条件同步（钉老版本时不回退根 `scripts/`，eng m-5） | **否**——`roadmap.md:91` 明确标为「**相关联 backlog**」，与 RM-AG0069 的「拟做」（仅 `git pull`）分列 | 正确**未**纳入本 hotfix。ALIGNED（无误漏） |
| `agate/UPGRADING.md` `### v0.73.0` 第 7 条「两步升级」 | **是**（新行为使其不完整） | **未更新** → MISALIGNED（同 A2） |
| `README.md` / `README.zh-CN.md` 安装段（`:34-44`） | 弱相关——README 是面向新用户的快速上手，描述「进入版本管理布局」，无需叙述重跑细节 | 可不改。ALIGNED |
| `agate-workspace/roadmap/roadmap.md` RM-AG0069 状态 | **是**——roadmap 是本条的**权威源**，当前状态仍为 `backlog`，描述的是「`install.sh` 遇 `repo/` 已存在时**不更新**」这一**待修缺陷**；修复后仍留 `backlog` = 权威源仍把已修缺陷记为未修 | **未更新** → MISALIGNED。roadmap 有 `done` 状态（82 条），且本改动自带回归锁（新用例），满足 RM-AG0096「`done` 须行为可观测 + 有回归锁」；应回写 `done` + 更新「更新」日期 |
| `RM-AG0070`（`latest` 从 Release asset 取包） | **否**——另一条 backlog；其取舍「**保留** `repo/` 以支持装任意历史 tag」与本改动（保持 `repo/` 新鲜）**互补不冲突** | 正确**未**纳入。ALIGNED |

**结论**：MISALIGNED。需补：roadmap RM-AG0069 状态回写 `done`（+日期）；`UPGRADING` 第 7 条 / 安装行更新（同 A2）。`_sync_root_scripts` 与 RM-AG0070 经核**不属本条**，未纳入是正确的。

### A4: 测试覆盖 — ALIGNED

**新测试**：`test_rm_ag0069_rerun_updates_existing_repo`（`test_install_sh.py:340-385`），三段式：首装 → 上游新增提交后重跑须 ff（`NEW-MARKER` 断言）→ `repo/` 内本地提交致 ff 失败须 WARNING 且 rc=0。

**判别力（独立变异实测，副本 `/tmp/opencode/instrepo`）**：
- 变异①：删除新 `else` 分支 ⇒ 新用例**转红**（`AssertionError: repo/ 已存在时重跑须 git pull --ff-only 更新`，`:368`）。
- 变异②：保留 `pull` 但把 WARNING `echo` 换成 `:`（抑制）⇒ 新用例**转红**（`r3` 输出无 `RM-AG0069`，`:385`）⇒ 证明「ff 失败 ⇒ WARNING」分支**确被触发**（分叉场景真使 `--ff-only` 失败）。

**全量 pytest 实跑**（副本，CI 口径 `--reruns 1 -n auto`）：
```
1 failed, 2911 passed, 3 skipped, 1 rerun in 87.85s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
唯一 failed 为**环境性**：本机 `opencode` CLI 无 `debug agent` 子命令（报 `Unknown subcommand "agent"`），与本次改动无关（`test_setup_agate_dir.py:308`）。`count-tests.sh` collect-only = 2915（= 2911+1+3，自洽）。

**结论**：ALIGNED。

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED

**既有用例转红清单：空**——经全量实跑，除上述**环境性** `test_bdd_43_opencode_registration_and_debug_agent` 外**无既有用例转红**；该失败在基线（无本改动）同样发生（与 `install.sh`/`repo` 无任何关联，属本机 CLI 版本）。
**夹具更新清单：空**——新用例复用现有夹具（`agate_scripts` / `bash` / `run_cli` / `synth` / `tmp_path`），自建**每用例独立上游**（`synth` 为 session 级共享、不可写，新用例 `git clone` 出独立 `upstream`），未改任何共享夹具。
另经 `grep` 全 `agate/tests/`：无既有用例 pin 住「`install.sh` 重跑/repo 更新」行为或 `UPGRADING` 第 7 条文本（唯一命中即新用例）⇒ 改文档不会连带转红既有断言。

**结论**：ALIGNED（空清单，已显式写出）。

### A5: 下游影响 + 文档传播 — MISALIGNED

- **gate 行为影响**：无。`install.sh` 不在 pre-commit/commit-msg/pre-push 的判定面内；不改 `.state.yaml` schema / 契约 / 审计链。**非破坏性变更**。
- **CHANGELOG**：`CHANGELOG.md` `[Unreleased]` 有「### 修复」节，列了 RM-AG0082/0084/0090/0091/0092/0112 等条目，**未含本次用户可见行为变更**。建议补一条（`install.sh` 重跑更新 `repo/`；失败降级 WARNING）。先例：`28293d8b fix(DEBT0042)` 改 `install.sh`+`UPGRADING` **未**改 CHANGELOG ⇒ 非硬性，但本次是用户可见行为修复，建议补。
- **文档传播**：`UPGRADING` 第 7 条 / 安装行未同步（见 A2/A3b）。

**结论**：MISALIGNED。建议补 CHANGELOG `[Unreleased]` 修复条目 + `UPGRADING` 同步。

### A6: 锚点表覆盖 — ALIGNED（N/A）

`install.sh` **不在** CHECK 9 锚点表内（`grep` 全 `agate/scripts/` 无 `check-protocol-consistency.py` 对 `install.sh` 的锚定）；本改动**未新增协议规则**，无需更新锚点表。

**结论**：ALIGNED（N/A）。

### A7: 设计原则一致性 — ALIGNED

`adr.md:479` 已记录 `install.sh --versions` bootstrap 分支（TAG0008/TAG0037）；本改动是对同一入口的**行为细化**（`repo/` 已存在时的更新语义），**未引入新的架构决策**，无需新增 ADR。与既有原则（fail-closed 软链守卫在前、`AGATE_REPO_URL` 可覆盖上游、版本管理布局）一致。

**结论**：ALIGNED。

### A8: 声称-命令绑定

本改动**未在协议/数据面新增数字或结论类声称**（新代码注释与测试 docstring 的定性声称见下表）。以下为本次审查所核的声称 → 命令 → 结论：

| 声称 | 命令 | 结论 |
|---|---|---|
| `check-protocol-consistency.py` **0 ERROR** | `python3 agate/scripts/check-protocol-consistency.py`（副本） | ✓ rc=0，`仅有 432 个 WARNING，无 ERROR`（432 全为冻结文件 WARNING） |
| 全量 pytest **2912 passed** | `python3 -m pytest agate/tests/ --reruns 1 -n auto`（副本） | **按实测更正**：本机 `2911 passed, 1 failed(环境), 3 skipped`。「2912」对应环境用例（`opencode debug agent`）通过的机器；本机该用例失败 ⇒ 2911。**不称「全绿」** |
| **shellcheck** 通过 | `shellcheck install.sh`（副本） | ✓ rc=0 |
| **ruff** 通过 | `~/.venvs/agate-dev/bin/ruff check agate/`（CI 口径，副本） | ✓ `All checks passed!` rc=0（注：`ruff check .` 全仓有 36 个 ERROR，**全在 `agate-workspace/`、`docs/`**，CI 只扫 `agate/`，预先存在，与本改动无关） |
| 「`--ff-only` **不改写本地历史**」 | 分叉场景实测 `git pull --ff-only` → rc≠0，`git rev-list --merges` = 0 | ✓ 成立 |
| 「失败降级为 **WARNING、不阻断**」 | 变异②抑制 WARNING ⇒ 新用例红；正常跑 rc=0 | ✓ 成立 |

**结论**：ALIGNED（一处数字按实测更正，无无据声称）。

---

## 重点结论

### 重点 1：`git pull --ff-only` 的正确性与安全性 — **安全**，但诊断信息被吞

**安全性矩阵**（副本 `/tmp/opencode/ffexp` 独立实测 `git pull --ff-only`）：

| 情形 | rc | 行为 |
|---|---|---|
| detached HEAD | 1 | `您当前不在一个分支上`——**不动作，无损** |
| 无 upstream 跟踪分支 | 1 | `当前分支没有跟踪信息`——**不动作，无损**（注：`install.sh` 首装 `git clone` 默认建 `origin/<branch>` 跟踪，正常路径有跟踪） |
| 真浅克隆（`file://`，`--depth 1`） | 0 | 正常 ff（仍浅）；不删内容 |
| 本地未提交改动**与上游冲突** | 1 | `本地修改将被合并操作覆盖`——**中止，本地改动保留** |
| 本地未提交改动/未跟踪文件**不冲突** | 0 | 两者**均保留** |
| 本地提交致**分叉** | ≠0 | **中止，本地提交保留，`--merges` = 0**（不产生 merge commit） |

⇒ **`--ff-only` 的保证边界成立**：只做「fetch + merge --ff-only」，**永不 reset、永不产生 merge commit、永不改写本地历史**；任何会被覆盖的本地改动都会使命令**中止**（rc≠0）而非覆盖。`repo/` 虽为「用户资产」（可被手工改动），但**无场景误删/改写用户内容**——分叉/冲突一律走 WARNING 分支继续用现有副本。**无破坏风险。**

**诊断信息被吞（建议改进）**：`git ... pull --ff-only >/dev/null 2>&1`（`install.sh:77`）把 git 的**真实失败原因**（网络 / 分叉 / 本地改动）一并丢弃，WARNING 只能给出**带问号的猜测**「网络或本地改动/分叉？」。这与同仓 `_ensure_repo`（`agate-install.py:191-199`）的做法**不一致**——后者**捕获并输出 stderr 首行**，其 docstring 明确记录了 2026-10-02 教训「**fail-open ≠ fail-silent**」：

> `agate-install.py:180-185`：`为什么 fail-open 但必须出声`……`但 fail-open ≠ fail-silent。原实现丢弃 fetch 的 rc 与 stderr，导致可复现的误导链`

**建议**：改为捕获 stderr（如 `err=$(git -C "$AGATE_VER_ROOT/repo" pull --ff-only 2>&1 >/dev/null)`）并把首行拼进 WARNING，与 `_ensure_repo` 对齐。**严重度：minor**（不影响正确性/安全，仅诊断质量）。

### 重点 2：测试判别力 — **有判别力**（独立变异已复现）

- 抽掉 `else` 分支 ⇒ 新用例**红**（`NEW-MARKER` 断言失败）。
- 抑制 WARNING `echo` ⇒ 新用例**红**（`r3` 无 `RM-AG0069`）⇒ 证明「ff 失败 ⇒ WARNING」分支**真被触发**（非空跑）。
- 均在 `/tmp/opencode/instrepo` 副本独立复现，未采信派发方结论。

### 重点 3：是否遗漏关联项

- **`_sync_root_scripts` 条件同步**：**不属本条**——`roadmap.md:91` 明标为「**相关联 backlog**」，与 RM-AG0069「拟做」分列；本 hotfix 未纳入是正确的。
- **`UPGRADING` 第 7 条「两步升级」**：新行为使其**不完整**（「仅文档」措辞已不足，代码注释自述以代码补文档）⇒ **应更新**（A2/A3b，MISALIGNED）。
- **`README.md` 安装段**：弱相关，可不改。
- **`RM-AG0070`**：**另一条** backlog（Release asset），与本改动**互补不冲突**，不属本条。
- **roadmap RM-AG0069 状态**：仍 `backlog` ⇒ 应回写 `done`（+日期）。
- **CHANGELOG**：未补 ⇒ 建议补 `[Unreleased]` 一条。

### 重点 4：A4b + A8 数字（实跑）

- 全量 `pytest agate/tests/ --reruns 1 -n auto`：**`1 failed, 2911 passed, 3 skipped, 1 rerun`**；1 failed = **环境性** `test_bdd_43_opencode_registration_and_debug_agent`（本机 `opencode` 无 `debug agent`）——**不称「全绿」**。
- `check-protocol-consistency.py`：**0 ERROR**（432 冻结文件 WARNING）。
- `shellcheck install.sh`：rc=0。
- `ruff check agate/`（CI 口径）：`All checks passed!`（`ruff check .` 全仓 36 ERROR 全在 CI 扫描面外，预先存在）。
- A4b：既有用例转红清单 **空**；夹具更新清单 **空**。

---

## 闭环建议（给主 Agent）

| 项 | 动作 |
|---|---|
| A2/A3b | 更新 `agate/UPGRADING.md` `### v0.73.0` 第 7 条（+ 可选：安装行 / `install.sh` 头注释），反映「重跑新 `install.sh` 会 `--ff-only` 更新 `repo/`」 |
| A3b | `agate-workspace/roadmap/roadmap.md:91` RM-AG0069 状态 `backlog` → `done`，更新「更新」日期（已有回归锁，满足 RM-AG0096） |
| A5 | `CHANGELOG.md` `[Unreleased]` 补一条「`install.sh` 重跑更新 `repo/`（失败降级 WARNING）」 |
| 重点 1（建议） | `install.sh:77` 捕获 git stderr 首行拼进 WARNING，对齐 `_ensure_repo` 的 fail-open≠fail-silent |

上述均为**文档/诊断面**小改，**不触碰本次核心逻辑**；改完重跑本审查即可判定可 commit。若人工裁定「第 7 条字面范围（旧安装器）仍成立、无需改文档」，则需在报告上打 `[HUMAN_CONFIRMED: 日期 确认：理由]` 后放行。
