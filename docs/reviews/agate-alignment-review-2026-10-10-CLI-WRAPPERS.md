---
review_date: 2026-10-10
reviewer: protocol-alignment-review
change_summary: agate-install.py 新增 ensure_cli_wrappers（在 <AGATE_HOME>/bin 生成 agate-<x> sh/.cmd 包装，让 agate-* 成为真命令）；并把协议文档里的空格简写（agate next / agate advance / agate dispatch route）改为真命令形态
files_changed: [CHANGELOG.md, agate/CONTEXT.md, agate/SETUP.md, agate/WORKFLOW.md, agate/assets/templates/codex/SKILL.md, agate/dispatch-protocol.md, agate/loop-orchestration.md, agate/orchestrator-template.md, agate/platform-notes.md, agate/scripts/agate-install.py, agate/state-machine.md, agate/tests/unit/test_agate_version_install.py, agate/tests/unit/test_mvwu_protocol_docs.py]
---

# 协议-脚本对齐审查 — CLI PATH 包装 + 文档简写统一

> **审查对象**：`hotfix/cli-path-wrappers` 意图的两件改动，以**工作区未提交**形态存在。
> ⚠️ **环境事实更正**：`git branch --show-current` = **`main`**（非任务描述所称的 `hotfix/cli-path-wrappers`）；改动 13 个文件全在工作区、`git diff` 可见、未 commit。开始前已确认成果文件不存在。
> **只读纪律**：全部 scratch 实验（包装实跑、合成安装）在 `/tmp/opencode/` 副本上进行；未改任何协议/脚本/测试，未 commit/push。跑完后 `git status --porcelain` 仅见原 13 个改动文件 + 本报告留痕文件。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED**（Windows `.cmd` 无法沿 `current` 文本指针解析 → 与 SETUP/CHANGELOG 的「版本无关 / Windows 可用」声明不符） |
| A2 | 脚本→文档对齐 | **NEEDS_HUMAN_REVIEW**（`agate/scripts/README.md` 的 `agate-install.py` 行未记 CLI 包装生成；`agate-doctor.py` 不诊断 PATH） |
| A3 | 一致性连锁 + 反向传播 | **NEEDS_HUMAN_REVIEW**（portable/离线 ✓ 已覆盖；`--uninstall` 不清 `<home>/bin`；残留简写见下）|
| A4 | 测试覆盖 | **ALIGNED**（`1 failed, 2914 passed, 2 skipped`；唯一 failed 为环境性，与本改动无关） |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **ALIGNED**（0 既有用例因本改动转红；1 处夹具更新：`_CONTEXT_BASELINE_TERMS`） |
| A5 | 下游影响 + 文档传播 | **NEEDS_HUMAN_REVIEW**（CHANGELOG 已标注；但「共 10 个文件」与实测 9 不符；Windows 声明过高） |
| A6 | 锚点表覆盖 | **ALIGNED**（CHECK 9/10 无新锚点需求；consistency 0 ERROR） |
| A7 | 设计原则一致性 | **NEEDS_HUMAN_REVIEW**（`<AGATE_HOME>/bin` 版本无关包装是新安装产物/决策，adr.md 未记；ADR-009/ADR-012 未覆盖） |
| A8 | 声称-命令绑定 | **NEEDS_HUMAN_REVIEW**（「2914 passed」/「0 ERROR」/「幂等」/「两条入口一致」均可复现；「共 10 个文件」不可复现） |

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**文档声明**
- `agate/SETUP.md:80-97`（新增「把 agate CLI 加入 PATH」节）：
  > `- **版本无关**：包装随 `current` 指针走，装新版本**不用**重建 PATH（升级后自动指向新版）。`
  > `- **Windows**：同一目录下另有 `.cmd` 包装；把 `%USERPROFILE%\.agate\bin` 加入 PATH 即可。`
- `CHANGELOG.md:205-213`：
  > `解析 AGATE_ROOT env → <home>/current/agate 回退；**幂等**…、**版本无关**（随 current 指针走，升级无需重建 PATH）`
  > `⇒ agate-next / agate-run / agate-summary 等可直接调用。`

**脚本实现**（`agate/scripts/agate-install.py`）
- `_CLI_WRAPPER_SH:411-412`：`home="$(cd "$(dirname "$0")/.." && pwd)"` / `root="${AGATE_ROOT:-$home/current/agate}"`
- `_CLI_WRAPPER_CMD:422-423`：`set "root=%AGATE_ROOT%"` / `if "%root%"=="" set "root=%~dp0..\current\agate"`
- 指针写入 `_write_pointer:108-111`：`if os.name == "nt":` 写**文本指针文件**；POSIX 才 `os.symlink(name)`。

**差异（实测）**：
1. **Windows 默认路径不可用（硬缺陷）**。Windows 下 `_write_pointer` **恒**把 `current` 写成**普通文件**（内容 `latest`），`latest` 同为文本文件——`<home>\current` 不是目录。而 `.cmd` 回退把 root 设为 `%~dp0..\current\agate` ⇒ 指向 `…\current\agate`（路径穿过一个文件）⇒ 必然失败。我以「`current` 为文本文件」在 Linux 复现同一解析：包装输出 `找不到协议根 … exit 127`；只有 `AGATE_ROOT` env 在场才可跑。⇒ SETUP.md「Windows：把 `%USERPROFILE%\.agate\bin` 加入 PATH 即可」与 CHANGELOG「版本无关」在 Windows 上**为假**。
2. **软链调用 home 推错（稳健性）**。`$(dirname "$0")/..` 取的是**调用路径**的父目录；若用户把 `<home>/bin/agate-next` 软链到 `~/.local/bin/agate-next` 再由 PATH 调用，home 被推成软链所在目录的上级（实测：解析成 `/tmp/…/current/agate`，缺一层 `home/`）⇒ 找不到协议根。SETUP.md 只文档了「把 `<home>/bin` 直接加 PATH」，**未把软链调用列为支持用法**；但 `_CLI_WRAPPER_SH:409-410` 注释自称「可搬迁」，需澄清或改 `readlink -f`。
3. **`ensure_cli_wrappers:434` 硬编码 `<vdir>/agate/scripts`**，未走 `_protocol_root` 两形态探测（`agate_common.py:288-300`）。标准安装（`agate_package.materialize`→`<vdir>/agate/scripts`）✓ 正确；但 `--adopt` 一个「根即协议」形态（`<vdir>/scripts`）的版本目录时，`_sync_root_scripts` 能成功而 `ensure_cli_wrappers` 静默返回 0（不生成包装）——两处口径不一致（edge case）。

**已核实为正确的部分**（POSIX 主路径）：
- 直呼（`sh`/`dash`/`bash`，`$0` 为真实路径）home 推导正确；`AGATE_ROOT` **空串**与**未设**均正确回退（`${AGATE_ROOT:-…}` 对空串取默认）；`PATH` 内仅 basename 调用亦正确。
- **真实安装独立验证**：合成 `file://` 仓库 + `install.sh --versions` ⇒ `/…/.agate/bin/` 生成 8 个包装（4×`agate-*.py`×sh/.cmd），`agate-next` 实跑 `NEXT-OK`。
- **幂等真实**：二次 `ensure_cli_wrappers` 返回 0，`agate-next` mtime 不变。

**建议**（择一，二选一并落到 A1/A5 文案）：
- 让包装跟随文本/软链两种指针：`.cmd` 侧改为读 `<home>\current` 文本再拼路径（或退而用 `agate-resolve.py`）；或
- 明确把 CLI 包装的**自动默认**限定为 POSIX，Windows 走 `.cmd` 时要求 `AGATE_ROOT`（并在 SETUP/CHANGELOG 里如实写明）。

**结论**：MISALIGNED
**差异**：Windows 默认（无 `AGATE_ROOT`）路径必然失败，与文档「版本无关 / Windows 可用」矛盾。
**建议**：如上（实现修正或把 Windows 声明降级为「需设 AGATE_ROOT」）。

### A2: 脚本→文档对齐 — NEEDS_HUMAN_REVIEW

- 新增行为（`ensure_cli_wrappers`：生成 `<AGATE_HOME>/bin/agate-*`）在 `agate/SETUP.md`（新增节）与 `CHANGELOG.md` 已同步 ✓。
- 但**工具目录未同步**：`agate/scripts/README.md:142` 的 `agate-install.py` 行逐条描述其行为（安装/卸载/adopt/check/symlink 守卫），**未提**安装时生成 `<home>/bin` CLI 包装。属软性登记遗漏（非 CHECK 可判；函数非新文件，不触发「新增脚本登记面」硬门禁）。
- `agate-doctor.py`（项目接入诊断）**不诊断**「`agate-*` 是否在 PATH」——SETUP.md 已把「加入 PATH」作为推荐步骤，诊断器不覆盖该步骤属可选增强（NEEDS_HUMAN_REVIEW，非必须）。

**结论**：NEEDS_HUMAN_REVIEW（README 工具行补一句为最低要求；doctor 诊断为建议）

### A3: 一致性连锁 + 反向传播 — NEEDS_HUMAN_REVIEW

**A3a 连锁（已验证到位）**：
| 应传播项 | 状态 | 证据 |
|---|---|---|
| portable / 离线安装（`install-offline.py`）| ✓ 已覆盖 | `install-offline.py:357-364` `_run_adopt` → 调同目录 `agate-install.py --adopt vX.Y.Z` → `_cmd_adopt:584` → `_register` → `ensure_cli_wrappers` |
| 信息性输出走 stdout | ✓ | `_register:517-524` 用 `sys.stdout.write`；离线 `_run_adopt` 转发 `proc.stdout`（`install-offline.py:422-423`），`--skip-*` 的 stderr 静默契约不受影响（全量 pytest 通过佐证） |
| `agate-pack-offline.py` | 不适用 | 只打包/取 `<AGATE_HOME>/repo`，不安装、不生成包装 |
| 两条安装入口树一致 | ✓ | 见「重点 2」 |

**A3b 反向传播（主动推断，未在 diff 中）**：
| 应被影响项 | 现状 | 判定 |
|---|---|---|
| `agate/scripts/README.md`（工具清单）| 未改 | 遗漏（见 A2） |
| `agate-setup.py --uninstall` 清 `<home>/bin` | **未清**（仅 `--purge` 走 `shutil.rmtree(home)` `:842` 连带删除）| 轻微缺口：`agate-install.py --uninstall <最后一个版本>` 后 `current` 被移除，残留 `bin/` 包装成悬空（调用 exit 127，报错清晰、不静默） |
| `agate-doctor.py` PATH 诊断 | 无 | 建议项（见 A2） |
| **残留简写（全仓 grep）** | 见下 | 需判断 |
| `UPGRADING.md` | 未动（有意）| ✓ 符合「历史节不可改写」 |

**残留简写清单**（`agate next` / `agate advance` / `agate dispatch route` 空格形态）：
- `agate/UPGRADING.md:881,1029,1030` —— **有意保留**（历史记录，`test_bdd_39_5` 守护）✓
- `agate/scripts/agate-advance.py:191` —— 运行时 reason 串 `"agate advance 按转移表单步回退"`（**非文档**，无测试引用；未在「文档统一」范围内，但仍是 `agate/` 树内空格形态）
- `agate/tests/unit/test_tag0027_b*.py` 文件头注释/文档串 —— 测试注释，非文档
- `docs/guides/project-map.md:69` —— **活文档**（整仓导航图，维护者随协议更新）仍写 `` `agate next` / `agate advance` ``，**建议纳入本批或明确 follow-up**
- `docs/brand/hero-terminal.svg:9,12` —— 品牌 hero 源（终端图显示 `$ agate next`）；改它须 `sync:brand` 重生成 `site/public` 快照。**建议判断**（品牌图 vs 真命令一致性）
- `agate-workspace/roadmap/roadmap.md:73`、`tasks/active-tasks.md:46` —— 看板/`done` RM 记录（历史性，惯例不改）
- `site/.vitepress/dist/*`、`site/blog` 散文、`docs/reviews/*` 历史评审 —— 构建产物 / 冻结内容，**不改**
- `.worktrees/blog-post11/` —— 另一 worktree 的旧快照，与本改动无关

**误改核查**：`agate/dispatch-protocol.md:677` 把 `agate dispatch prompt 模板` 改为 `` `dispatch-prompt` 模板``——**非**「简写→命令」，而是**术语归一**（与同文件 `:475,488,491` 已在用的 `assets/templates/dispatch-prompt.md` 一致），**判定为合规修正、非误改**。

**结论**：NEEDS_HUMAN_REVIEW

### A4: 测试覆盖 — ALIGNED

`agate/tests/unit/test_agate_version_install.py::test_rm_ag0102_cli_wrappers_generated_and_runnable`（新增，`:859-907`）覆盖：① 只对 `agate-*.py` 生成；② POSIX sh 包装**可执行且真能跑**（行为验证，`AGATE_ROOT` env 快路径）；③ `.cmd` 一并生成；④ **幂等**（二次返回 0）。

**最近一次全量实跑**（本机，`/tmp/opencode/pytest-full.log`）：
```
$ python3 -m pytest agate/tests/ -n auto -q -p no:cacheprovider
1 failed, 2914 passed, 2 skipped in 75.72s
FAILED agate/tests/unit/test_setup_agate_dir.py::test_bdd_43_opencode_registration_and_debug_agent
```
**唯一 failed 为环境性、与本改动无关**：用例执行 `opencode debug agent orchestrator`，本机 `opencode` 已把子命令改名为 `debug agents`（复数），`rc=1 Unknown subcommand "agent"`。该测试文件**不在**本改动 diff 内，改动面（`agate-install.py` 包装 + 文档）不触及 opencode 注册逻辑。
> 按纪律**不称「全绿」**：`2914 passed` 属实，另有 1 条环境性 failed。

**结论**：ALIGNED

### A4b: 闭合后既有测试转红 + 夹具更新清单 — ALIGNED

- **本次变更使既有用例转红**：**经实测无**（全量唯一 failed 为上述环境性 `test_bdd_43`，与本改动无因果；其余 2914 全过）。
- **需更新的夹具（1 处，已更新）**：`agate/tests/unit/test_mvwu_protocol_docs.py:219` 的 `_CONTEXT_BASELINE_TERMS`——条目 `"agate next / agate advance"` → `"agate-next / agate-advance"`，与 `agate/CONTEXT.md` 术语表改名**配对**（该用例断言每个基线词条出现在 CONTEXT.md，故 CONTEXT 改名**必须**联动此夹具）。
- **新增用例**：`test_rm_ag0102_cli_wrappers_generated_and_runnable`（见 A4）。
- **守护用例**：`test_bdd_29_both_entries_produce_identical_tree`（`:145`）与 `test_bdd_39_5`（`test_upgrading_contract_doc.py:288`）在本批**保持绿**。

**结论**：ALIGNED（空转红清单 + 1 处夹具更新，均显式列出）

### A5: 下游影响 + 文档传播 — NEEDS_HUMAN_REVIEW

- **CHANGELOG 已标注**（`CHANGELOG.md:205-213`，`[Unreleased]`）✓。改动为**新增能力**（安装时多生成 `bin/` 包装）+ 文档用词统一，对既有项目 gate 行为**无破坏性**（未配置/未加入 PATH = 逐字节现状），故不属 BREAKING。
- **文档传播缺口**：`SETUP.md` 已加节；但 `agate/scripts/README.md` 未同步（A2）；且 CHANGELOG/SETUP 对 **Windows 的可用性声明过高**（A1）。
- **版本引用文件**：本改动不涉及 `README` badge / `UPGRADING` 章节 / 版本号，无关。

**结论**：NEEDS_HUMAN_REVIEW

### A6: 锚点表覆盖 — ALIGNED

`python3 agate/scripts/check-protocol-consistency.py` → `rc=0`，**0 ERROR**，433 WARNING（全部落在「冻结文件」bucket：`CHECK1-yaml` 2 / `CHECK10-scriptref` 1 / `CHECK2-refs` 430，来源为 `tasks/`、`reviews/`、`CHANGELOG` 等按设计不改的历史文件）。本改动未新增/变更协议规则，未触碰 CHECK 9 锚点表；`ensure_cli_wrappers` 是函数（非新脚本文件），不触发脚本登记门禁。

**结论**：ALIGNED

### A7: 设计原则一致性 — NEEDS_HUMAN_REVIEW

- 与 **ADR-009**（`~/.agate` 版本管理根 + 固定解析入口）、**ADR-012**（版本目录两形态 `_protocol_root` 探测序 + 根 `~/.agate/scripts/` 单源副本）方向一致：包装放 `<AGATE_HOME>/bin`、内容与安装路径无关、随 `current` 走。
- 但「**安装时生成版本无关的 `<home>/bin` CLI 包装**」是一个**新的安装产物与决策**（位置选型、sh/.cmd 双形态、幂等策略、与指针解析的关系）。`agate/adr.md` 无对应记录（全文无 `<home>/bin` / CLI 包装条目）。建议补一条短 ADR，或在 ADR-012 追加说明，使该决策可追溯（设计原则是指导性的，标 NEEDS_HUMAN_REVIEW 而非 MISALIGNED）。

**结论**：NEEDS_HUMAN_REVIEW

### A8: 声称-命令绑定

| 声称 | 命令 | 结论 |
|---|---|---|
| `2914 passed`（A4/任务口径）| `python3 -m pytest agate/tests/ -n auto -q -p no:cacheprovider` | ✅ `1 failed, 2914 passed, 2 skipped`（failed 为环境性） |
| `0 ERROR`（consistency）| `python3 agate/scripts/check-protocol-consistency.py` | ✅ `rc=0`，0 ERROR（433 frozen WARNING） |
| ruff 通过 | `~/.venvs/agate-dev/bin/ruff check agate/scripts/agate-install.py agate/tests/unit/test_agate_version_install.py agate/tests/unit/test_mvwu_protocol_docs.py` | ✅ `ruff 0.16.4 All checks passed!` |
| 「幂等（内容相同不重写）」| 二次 `ensure_cli_wrappers` | ✅ 返回 0；`agate-next` mtime 不变 |
| 「两条安装入口产出的树逐字节一致」| `install.sh`（无参/`--versions`）+ `test_bdd_29_…` | ✅ 见「重点 2」 |
| 「全仓无真实调用形态」| `grep -rn -E "['\"]agate (next\|advance\|dispatch route)" --include=*.py --include=*.sh` | ✅ 无**调用**；仅 `agate-advance.py:191` 一处 reason **输出串**（非调用） |
| **「文档简写统一…共 10 个文件」**| `git diff --name-only -- 'agate/**/*.md'`（命令化替换面）| ❌ 实测 **9** 个协议 md（`CONTEXT/SETUP/WORKFLOW/codex SKILL/dispatch-protocol/loop-orchestration/orchestrator-template/platform-notes/state-machine`）。若把 `test_mvwu_protocol_docs.py` 夹具更新也计入则凑成 10，但那是**测试夹具**而非「被统一的文档」。任务口径亦为 **9**。 |

**结论**：NEEDS_HUMAN_REVIEW——「10 个文件」应改为「9 个文件」或注明含 1 处测试夹具更新；其余声称全部可复现。

## 五项重点结论

1. **包装正确性**
   - ✅ POSIX 主路径正确：直呼/`PATH` 调用下 `$(dirname "$0")/..` 正确推 home（`sh`/`dash`/`bash` 实测一致）；`AGATE_ROOT` **空串**与**未设**均按预期回退；`sh` 包装为纯 POSIX 语法（本机无 `zsh`，未实测，但语法无 bash 专有构造）。
   - ✅ **幂等为真**（内容相同不重写、mtime 不变）。
   - ❌ **Windows `.cmd`（`%~dp0..\current\agate`）在默认态不可用**：`_write_pointer` 在 `nt` 下把 `current` 写成**文本文件**，路径穿过文件 → 必失败（已在 Linux 以文本指针复现 `exit 127`）。与 SETUP/CHANGELOG 的 Windows/版本无关声明矛盾 ⇒ **A1 MISALIGNED 主因**。
   - ⚠️ **软链调用 home 推错**（非文档支持用法；包装自称「可搬迁」，需澄清或用 `readlink -f`）。
   - ⚠️ `ensure_cli_wrappers` 未走 `_protocol_root` 两形态（`--adopt` 扁平形态 edge case）。

2. **两条入口树一致（`test_bdd_29_both_entries_produce_identical_tree`）——不变量理由稳固**
   - 该测试比较两个隔离 HOME（`h-noarg` / `h-versions`）下 `<home>/.agate` 的结构树；`_shape` 用 `helpers_tag_repo.snapshot_tree`（`:653-668`），对文件取 **sha256 内容**、对软链取 **target**。
   - 独立性**理由**成立：包装内容只由模板 + `{name}` 决定，**不含任何安装绝对路径**（home 于运行时由 `$0`/`%~dp0` 推导）⇒ 换 home 路径 / 换机器后两棵树（含 `bin/` 内容）**逐字节相同**。故该不变量不依赖偶然而稳固。
   - 我另以**真实安装**独立复核（合成仓库 + `install.sh --versions`）：`<home>/bin/` 生成 8 个包装且 `agate-next` 实跑成功——确认标准安装路径**确实**产出 `bin/`（非「两处都漏生成所以相等」的假绿）。

3. **`UPGRADING.md` 未动 + 残留简写**
   - ✅ `UPGRADING.md` **不在** `git status` 改动集；`test_bdd_39_5`（历史节相对基线 `75a8102` 不可改写）在 `2914 passed` 内为绿。
   - **残留简写**（见 A3b 清单）：活文档 `docs/guides/project-map.md:69`、品牌源 `docs/brand/hero-terminal.svg:9,12`、运行时串 `agate-advance.py:191`；其余为有意（`UPGRADING.md`）或冻结（`agate-workspace/`、`docs/reviews/`、`site/` dist/blog）。
   - **未发现误改**：`dispatch-protocol.md:677` 的 `agate dispatch prompt` → `dispatch-prompt` 属**术语归一**（与同文件既有 `dispatch-prompt.md` 用法一致），非误改。

4. **遗漏项**
   - portable/离线：✓ **已覆盖**（`install-offline.py:357-364` → `--adopt` → `_register` → 生成包装）。
   - `agate-setup.py --uninstall`：**不清 `<home>/bin`**（仅 `--purge` 经 `shutil.rmtree(home):842` 连带）；轻微空缺（悬空包装报错清晰）。
   - `agate/scripts/README.md`：**未记** `ensure_cli_wrappers`/`<home>/bin`（软登记遗漏）。
   - `agate-doctor.py`：**不诊断** PATH（建议项）。

5. **A4b + A8 数字**：见上——`1 failed(环境性) / 2914 passed / 2 skipped`；`0 ERROR`；`ruff All checks passed!`；「9 个文件」为实测（CHANGELOG 写 10 不可复现）。

## 是否可 commit

**否——需先处置后复审**（按闭环规则）：

- **MISALIGNED（必须修复）**：A1 —— Windows `.cmd` 默认态不可用 vs 文档「版本无关 / Windows 可用」。修脚本（沿 `current` 文本指针解析）或修文档（Windows 降级为「需设 `AGATE_ROOT`」/ 明确 POSIX-only），二者对齐后重审。
- **NEEDS_HUMAN_REVIEW（须 `[HUMAN_CONFIRMED: …]` 配对方可 commit）**：
  - A2：`agate/scripts/README.md` 工具行补记包装生成（最低）；doctor PATH 诊断（可选）。
  - A3：`--uninstall` 是否清 `bin/`；残留简写处置（`project-map.md` 是否纳入本批、品牌 hero 图是否改）。
  - A5：Windows 声明与 CHANGELOG 口径一致化。
  - A7：为 `<home>/bin` 版本无关包装补 ADR 或并入 ADR-012。
  - A8：CHANGELOG「共 10 个文件」→ 实测 **9**（或注明含测试夹具）。
- 可先在 `007`（clearly correct）的部分保留：POSIX 主路径、幂等、两入口一致、测试与一致性检查均为绿。

> 另注（非本审查判据）：改动触及 SELF-GATE 触发面（`agate/scripts/*.py`），commit message 须含 `self-gate-review:` 路径或 `self-gate-skip:` 理由（commit-msg hook 检查）。
