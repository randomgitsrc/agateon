---
review_date: 2026-10-09
reviewer: protocol-alignment-review
round: 2
change_summary: 批 A / RM-AG0109 round 2——仅复验 r1 阻塞项（AGENTS.md 指针调用形式与脚本接口不一致）是否已修
files_changed: [AGENTS.md]  # 工作区改动（commit 448a154a 之后未 amend）
supersedes_blocker_of: docs/reviews/agate-alignment-review-2026-10-09-A0109-ASSET.md
---

# 协议-脚本对齐审查（A0109-ASSET r2）

> 只验 r1 的阻塞项。只读审查——未改任何协议/脚本/测试，未 commit/push。
> 改动位于**工作区**（`git diff AGENTS.md`），commit `448a154a` 之后**未 amend**。留痕见 `.progress.md`。

## 结论汇总

| # | 验证项 | 结论 |
|---|--------|------|
| 1 | 新指针与 `r6-differential.sh:37-47` 参数解析逐条一致 | ✅ ALIGNED |
| 2 | 实跑 `--corpus <副本>` 不再报「未知参数」 | ✅ ALIGNED |
| 3 | A8 三条声称逐条复现 | ✅ 全部成立 |
| 4 | 是否可 commit | ✅ **可 commit** |

**r1 阻塞项（A1/A2/A8-④）已修复**；r1 的非阻塞建议（阶段卡片记录、固定资产位置/机械守护）不构成本轮阻塞。

---

## 1. 指针 ↔ 脚本参数解析（逐条）

**新指针**（`AGENTS.md:107-110`，工作区）：

```bash
bash docs/design-notes/r6-differential.sh --corpus <副本仓库路径> [--allow <允许差异清单>]
```
> （脚本**只认选项** `--before/--after/--corpus/--allow`；`--allow` 缺省即用同目录的
> `r6-allowlist.yaml`。⚠️ 该脚本位于 `docs/design-notes/`，**不在** `agate/scripts/` 的
> CHECK 9/CHECK 10 扫描面内 ⇒ 其接口正确性**无机械守护**，改动后请手动核对本节。）

**脚本**（`docs/design-notes/r6-differential.sh:37-47` + `:31-35`）：

| 项 | 脚本事实 | 指针表述 | 一致 |
|---|---|---|---|
| 选项名 | `--before` / `--after` / `--allow` / `--corpus` | 「只认选项 `--before/--after/--corpus/--allow`」 | ✅ |
| 传参形式 | 每选项 `shift 2`（选项 + 值） | `--corpus <值>` / `--allow <值>` | ✅ |
| `--corpus` | 缺省 `.`；可多次 | 作为**主参数**给出副本路径（正确用法） | ✅ |
| `--allow` | 缺省 `$SCRIPT_DIR/r6-allowlist.yaml`（`:34`，即 `docs/design-notes/`） | 「缺省即用**同目录**的 `r6-allowlist.yaml`」 | ✅ |
| `--allow` 必需性 | 可选（有缺省） | `[--allow …]`（方括号=可选） | ✅ |
| 位置参数 | `*)` → `未知参数` exit 2 | 已**不再**给位置参数形式 | ✅ |

**唯一措辞细节（不阻断）**：脚本另接受 `-h|--help`（`:43-44`），指针的枚举「只认选项 `--before/--after/--corpus/--allow`」未含 `--help`。这是帮助开关、非实质选项，不影响可用性，**不判为缺陷**。

**结论：ALIGNED。** r1 的「位置参数 vs 选项」不一致**已消除**。

## 2. 实跑验证（不再「未知参数」）

在 `/tmp/opencode/` 自建 scratch 副本（git repo，`--before HEAD`），运行**新文档形式**：

```
$ bash docs/design-notes/r6-differential.sh --corpus <scratch> --before HEAD
r6-differential: before=HEAD  after=<scratch>/agate  allow=<repo>/docs/design-notes/r6-allowlist.yaml
r6-differential: legacy 任务 1 个，差异 0 条，未匹配 0 条
exit=0
```

- **无「未知参数」**——参数被正确解析，脚本进入主体（导出 before 协议、解析 after、加载 allow、跑差分、打印汇总）。
- 含真实任务目录时亦正常（`legacy 任务 1 个，差异 0 条，未匹配 0 条`，exit 0）。
- 对照：**旧**位置参数形式仍 `exit 2`（`未知参数: /tmp/x`）——确认修复确为「改调用形式」而非「改脚本」。

**scratch 插曲（属设置，非缺陷）**：一次 scratch **未带 `.gitignore`** 时，`post-run` 自核验报 `?? agate/scripts/__pycache__/` 脏并 exit 1——因 `check-gate.py` 运行时生成 `__pycache__`，而该 scratch 未忽略之。真仓 `.gitignore:14-15` 已忽略 `__pycache__/` / `*.pyc`（`git ls-files` 确认其未被跟踪）⇒ **正常克隆副本不会触发**。此现象反而**证明脚本的跑后自核验在工作**。

**结论：ALIGNED。** 自建 scratch 已删除；真实仓仅剩本审查文件。

## 3. A8 声称逐条复现

| 声称 | 命令 | 结论 |
|---|---|---|
| `check-protocol-consistency.py` 0 ERROR | `python3 agate/scripts/check-protocol-consistency.py` | ✅ exit 0；`仅有 427 个 WARNING，无 ERROR`（CHECK 9 PASS，CHECK 10 WARN=frozen） |
| roadmap 列数 0 异常 | 按 `check-gate.py:2144+` 逻辑扫 `roadmap.md`（`len(split("|"))!=9` 且 `^\|\s*RM-`） | ✅ `anomalies= 0` |
| 指针与脚本用法一致 | `bash … --corpus <scratch>`（新）/ `bash … /tmp/x`（旧） | ✅ 新形式 exit 0；旧形式 exit 2——**指针现与脚本一致** |

**结论：三条声称全部成立。**

## 4. 是否可 commit

**可 commit。**

- r1 阻塞项（A1/A2/A8-④：指针形式与脚本接口不一致）**已修复并实测**：新形式进入脚本主体、exit 0；旧形式对照仍失败。
- A8 三条声称均成立；`0 ERROR` 仍成立（本批为 docs-only，未触 `agate/scripts/*`，CHECK 10 正则亦不匹配 `r6-differential.sh`，故无新增告警）。
- 无新增回归风险（docs-only；r1 的 `test_bdd_43` 环境性失败与本批无关，不受本次工作区改动影响）。

**非阻塞提醒**（r1 已记，供合并后跟进，不影响本 commit）：
- `docs/design-notes/` 语义为「决策记录索引」，固定资产置于此与目录语义不完全吻合，且不在 CHECK 9/10 扫描面 ⇒ 接口无机械守护（新指针的补注已**显式**写明这一点，属恰当的自我提示）。
- RM-AG0109 ② 记录只引 `state-machine.md`，未提阶段卡片（roadmap 原文点名）；阶段卡片无字面「手写 phase」指引，不阻断。

## 审查者声明

- 只读：未改协议/脚本/测试，未 commit/push；scratch 仅在 `/tmp/opencode/` 且已清理；真实仓 `git status` 仅含本审查文件。
- 留痕：`docs/reviews/agate-alignment-2026-10-09-A0109-ASSET-02.progress.md`。
