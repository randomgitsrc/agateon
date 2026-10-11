# P4 progress — implementer R-A（修复轮 retry 1：脚本/CI 硬化）

范围（只改这三个文件）：
- `agate/scripts/agate-release.py`（SEC-01 / SEC-09 / SEC-02 + 文档注释）
- `.github/workflows/release.yml`（SEC-03 / SEC-07 —— 注释级，不改行为）
- `docs/design-notes/r6-differential-prepare.sh`（SEC-04 路径硬化 + A8 #5 after 侧修正）

已读输入：implementer.md；`P4-dispatch-context-implementer-R-A.md`（强制指引）；
`P4-review-cso.md`（SEC-01..09 + §4 实测）；`docs/reviews/agate-alignment-review-2026-10-11-TAG0051-P4.md`（A8 #5）；
`P2-design.md`（§1.1 M11/M12、§5 P5_r6、决策 2/3/8）；`r6-differential.sh`（`--after` 语义）；
`test_release_gate.py`（P3 夹具）；`r6-allowlist.yaml`。状态：[PROD_NOT_TOUCHED]

## 2026-10-11 实现

### ① SEC-01 本地发布门 fail-closed（最高优先）
`agate-release.py::_cmd_gate`：取到 runs 后若 `not runs` ⇒ **非 0**（`fail-closed`），并打印可操作提示
（成因：required 解析为空＝env 未设 + 读不到分支保护；处理：确认 CI 已跑 or 显式设 `AGATE_RELEASE_REQUIRED_CHECKS`）。
`docs`：gate 子命令 docstring 增「fail-closed 契约」段（required 空 + 零 check-run ⇒ 非 0）。

### ② SEC-09
`_cmd_gate` 开头：`--sha` 为空串 ⇒ 显式非 0，**不再** `args.sha or "HEAD"` 静默回退；后续统一用 `sha`。

### ③ SEC-02（成本低，已实现）
`_gh_check_runs` 增**可信上报 App 过滤**：缺省只认 `github-actions`（可经 env `AGATE_RELEASE_TRUSTED_APPS` 覆盖）；
被过滤者若 name 恰为 required ⇒ 按「缺失」合成非 success（fail-closed）。**仅作用于缺省 gh 路径**，
不影响注入路径 ⇒ P3 夹具（注入）不受影响（实测见下）。

### ④ SEC-03 / SEC-07（注释级，不改行为）
`release.yml` 门步骤注释写明：required 列表**硬编码**、分支保护每新增 required 必须同步（SEC-03）；
门步骤**未传 `--task`** ⇒ RM-AG0043 反查在 CI backstop 不生效、完整口径以本地门（带 `--task`）为准（SEC-07）。

### ⑤ SEC-04 `--dst` 硬化（`r6-differential-prepare.sh`）
- **物理归一化**：`_realpath`（`realpath -m` → `readlink -f` → 纯语法折叠）后比「等于/在 src 内 / 是 src 祖先」；
- **允许前缀**：`--dst` 须**严格**位于 `$TMP/opencode`（可经 `R6_PREPARE_ALLOW_PREFIX` 覆盖）；
- **拒绝**已存在且为软链的 `--dst`；拒绝等于前缀根；拒绝根 `/`；
- 全部校验在 `rm -rf` **之前** ⇒ 负例**不删任何东西**。

### ⑥ A8 #5 R6 证据"空转"修正 → **选取方案 1（`--after` 显式指向真实工作树）**
`r6-differential.sh` 的 `--after` **可显式指定**（`--after <dir>`），故 wrapper 现在注入
`--after <src>/agate`；corpus 只承担 `--before`（干净基线）+ 任务数据来源。脚本头部注释写明「证据成立前提」。
运行者若显式传 `--after` 则尊重之（不再注入）。

## 自查实测（≠ P5 gate）

### SEC-01 / SEC-09（rc 实测）
```
env -u AGATE_RELEASE_REQUIRED_CHECKS python3 agate/scripts/agate-release.py gate \
    --ci-cmd '<py> empty_ci.py' --consistency-cmd '<py> rc0.py' --repo .
   ⇒ "发布门失败——目标提交 HEAD 无任何可校验的 check-run（fail-closed）…"  rc=1   # 零 check-run
同命令但 --ci-cmd 返回 1 项 success ⇒ rc=0                                        # control
--sha '' ⇒ "发布门失败——--sha 不得为空串（显式拒绝，不回退 HEAD）"            rc=1   # SEC-09
```

### wrapper 负例（均 rc=2，且 sentinel 文件 / 软链本体存活 = 未删任何东西）
| 负例 | rc |
|------|----|
| `--dst ""` | 2 |
| `--dst relative-corpus` | 2 |
| `--dst <src>/sub`（src 内）| 2 |
| `--dst <src>`（== src）| 2 |
| `--dst <src 祖先>` | 2 |
| `--dst /home/kity/oclab`（祖先 + 前缀外）| 2 |
| `--dst /tmp/r6-elsewhere`（前缀外，非祖先）| 2 |
| `--dst /tmp/opencode`（= 前缀根）| 2 |
| `--dst <已存在软链>` | 2 |
| `--dst <link→src>/sub`（软链绕过「在 src 内」）| 2 |

### wrapper 正例冒烟（after 侧 = 真实工作树，含未提交改动）
```
bash docs/design-notes/r6-differential-prepare.sh --src . --dst /tmp/opencode/tag0051-r6-corpus
r6-differential-prepare: src=/home/kity/oclab/agateon  dst=/tmp/opencode/tag0051-r6-corpus  allow_prefix=/tmp/opencode
r6-differential-prepare: after 侧 = /home/kity/oclab/agateon/agate（真实工作树，含未提交改动；非 corpus）
r6-differential: before=581369fc…  after=/home/kity/oclab/agateon/agate  allow=…/r6-allowlist.yaml
r6-differential: legacy 任务 39 个，差异 2 条，未匹配 2 条   ⇒ rc=1
```
**这正是"空转"被修好的证据**：after 侧现为 `/home/kity/oclab/agateon/agate`（真实工作树），
差异不再是 0 条；两条差异 = `check-gate:P8` 成功消息删掉「④ 从 P2 packages 验证 version 文件路径」
（rc 2→2，文本级）。真实仓库跑前/跑后核验：**除 TAG0051 自身外无任何任务被改动，
`gate-events.jsonl` 零改动**（`git status --porcelain` 实测）。

### lint / 测试
- `bash -n` rc=0；`shellcheck docs/design-notes/r6-differential-prepare.sh` **rc=0**。
- `~/.venvs/agate-dev/bin/ruff check agate/` → **All checks passed!**（rc=0，无新增错误）。
- `python3 -m pytest agate/tests/unit/test_release_gate.py -q` → **10 passed**（SEC-02 未影响注入夹具）。
- `python3 -m pytest agate/tests/unit/test_tag0051_r6_harness.py agate/tests/unit/test_agate_release.py -q` → **52 passed**。

## [SCOPE+]

> [SCOPE+] A8 #5 修正后 R6 证据**成立且非空转**，暴露一个**早先被空转掩盖的兼容差异**：
> `check-gate:P8` 的**成功消息**（`GATE P8: 脚本化检查通过…`）被 `r6-differential.sh::_error_lines`
> 采集为「行集合」元素（因该行以 `GATE ` 开头），而本任务从该消息删掉了「④ 从 P2 packages 验证
> version 文件路径」⇒ 对 `TAG0042` / `TAG0050` 两个 legacy 任务产生 `rc 2→2` 的**文本级**差异，
> 现无 allowlist 规则匹配（实测 `未匹配 2 条`，rc=1）。⇒ `P5_r6` 将因此**非 0**。
> **根因不在我这 3 个文件内**：需在 `docs/design-notes/r6-allowlist.yaml` 增一条规则
> （如 `kind: rc_change` / `gate: "check-gate:P8"` / `task_scope: legacy` /
> `match: {patterns: ["脚本化检查通过"], rc_from: 2, rc_to: 2}`），
> **或**收紧 `r6-differential.sh::_error_lines` 使**成功消息**不计入差异集（该文件属 TAG0050）。
> 二者均**不在** R-A（3 文件）/R-B（5 文档）/R-C（测试）的划定面内 ⇒ 请主 Agent 裁定归属后回补。

[PROD_NOT_TOUCHED]
