#!/usr/bin/env python3
"""check-ledger-pollution.py — 账本/状态文件**事后**污染兜底（DEBT0040 ③）

用法：
    python3 agate/scripts/check-ledger-pollution.py [REPO_ROOT]   # 默认 .

判据：`git status --porcelain -- <STATE_PATHS>` 输出为空 ⇒ 干净。

背景（TAG0034 复盘实测）：测试真实调用 `agate_common.append_event` 且 `task_dir` 指向
**仓库内**已提交账本，把事件追加进历史任务的 `gate-events.jsonl`，污染需人工 `git checkout`
复原。三族状态文件（`gate-events.jsonl` / `active-tasks.md` / `.state.yaml`）的仓库内落点有两处：
`agate-workspace/`（63 个）与 `agate/tests/fixtures/`（5 个夹具副本），共 68 个。
本脚本是该污染的**事后独立观测**兜底——与「静态源码判据」（`test_t42_*` 扫测试源码禁止把
仓库内路径传给写函数）互补：静态判据拦根因、本脚本验结果，两者都不依赖测试执行顺序。

设计取舍（四点都是实测/论证后的选择，勿随手简化）：
  1. **pathspec 必须精确到「状态文件名」，不能用目录**：初版用目录（`agate-workspace`、
     `agate/tests/fixtures`），结果把**任何**改到该子树下文档的提交都判成污染——包括
     `agate-workspace/debt/tech-debt.md`（本债自己的闭合记录！）与 roadmap/tasks 下的正常编辑。
     那种写法**只在「本来就没有任何东西需要检查」的树上才绿**，等于零覆盖（独立评审实测复现：
     该提交自己让兜底 exit 1）。现用 git magic glob 精确到三族文件名，正常文档编辑不再误报。
  2. **用 `status` 而非 `diff`**：`git diff --exit-code` 只报**已跟踪**文件的改动，会漏掉
     跑测**新建**的未跟踪账本（评审实测：新建未跟踪账本时 `diff` rc=0、`status` 能捕获）。
  3. **`-uall`（hardening）**：`status` 默认 `normal` 会把未跟踪目录折叠成一条 `?? dir/`；
     显式 `-uall` 保证逐文件列出，避免未来某处 git 配置（如 `status.showUntrackedFiles=no`）
     让新账本静默不可见。
  4. **放在 CI 的 `pytest` job 内**（而非 `gate-backstop` 等独立 job）：GitHub Actions 每个
     job 各有独立 runner 与独立 checkout，独立 job 看到的是全新干净工作树，**在结构上不可能**
     观测到 pytest 的副作用。放错位置只会得到「看起来有兜底」的假象。

**已知边界（据实说明）**：① 本脚本只在 `pytest` job 内跑，**没有 push/合并后**的对应检查——
若状态文件被**提交**，CI 会在该 PR 上红，但合并后不再复查；② 被 `.gitignore` 覆盖的运行时产物
（`.gate-result.json` / `.gate-history.jsonl`）不可见，也**不可能污染已提交内容**，故有意排除。

退出码：0 = 干净；1 = 发现污染（打印被污染路径）；2 = 无法判定（非 git 仓 / git 不可用）。
**2 是 fail-closed 语义**：调用方须把非 0 一律视为失败，不得把 2 当「跳过」——
无法判定时声称「通过」正是本仓 DEBT0040 要治的那类真空通过。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# 三族已提交状态文件（gate-events.jsonl / active-tasks.md / .state.yaml）在**两个落点**下的
# 精确文件名匹配（git magic glob）。**刻意不用目录 pathspec**——那会把同子树下的正常文档编辑
# （debt / roadmap / tasks）误判为污染，见模块 docstring 取舍 1。
# 新增第三处落点或第四族状态文件时须同步本常量，并更新
# agate/tests/unit/test_t43_ledger_pollution_backstop.py。
STATE_PATHS = (
    ":(glob)agate-workspace/**/gate-events.jsonl",
    ":(glob)agate-workspace/**/active-tasks.md",
    ":(glob)agate-workspace/**/.state.yaml",
    ":(glob)agate/tests/fixtures/**/gate-events.jsonl",
    ":(glob)agate/tests/fixtures/**/active-tasks.md",
    ":(glob)agate/tests/fixtures/**/.state.yaml",
)

_GIT_TIMEOUT = 120


def _run_git(args: list[str], cwd: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_GIT_TIMEOUT,
    )


def find_toplevel(root: Path) -> str | None:
    """返回 root 所属仓库的顶层目录；非 git 仓 / git 不可用 / 超时 → None。"""
    try:
        proc = _run_git(["rev-parse", "--show-toplevel"], cwd=str(root))
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    top = proc.stdout.strip()
    return top or None


def find_pollution(toplevel: str) -> list[str] | None:
    """返回污染路径列表（空 = 干净）；无法判定 → None。

    单次 `git status --porcelain -uall`，pathspec 精确到状态文件名（见模块 docstring 取舍 1/3）。
    """
    try:
        proc = _run_git(["status", "--porcelain", "-uall", "--", *STATE_PATHS], cwd=toplevel)
    except (OSError, subprocess.SubprocessError):
        return None
    if proc.returncode != 0:
        return None
    return [ln for ln in proc.stdout.splitlines() if ln.strip()]


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    root = Path(args[0] if args else ".").resolve()

    toplevel = find_toplevel(root)
    if toplevel is None:
        print(
            f"GATE LEDGER: 无法判定——{root} 不是 git 仓库，或 git 不可用"
            "（fail-closed：调用方须按失败处理，不得当作跳过）",
            file=sys.stderr,
        )
        return 2

    pollution = find_pollution(toplevel)
    if pollution is None:
        print(
            "GATE LEDGER: 无法判定——`git status --porcelain` 执行失败"
            "（fail-closed：调用方须按失败处理）",
            file=sys.stderr,
        )
        return 2

    if not pollution:
        print("GATE LEDGER: 干净（三族状态文件在两个落点下均无改动）")
        return 0

    # 判定结果与命中的路径走 **stdout**（与仓内 `check-*.py` 一致：发现走 stdout，
    # 环境性失败走 stderr）——CI 与调用方据此解析。
    print(
        "GATE LEDGER: 检测到状态文件/账本污染——跑测写脏了仓库内已提交文件"
        "（DEBT0040；须让测试把 task_dir 指向 tmp_path，而非仓库内真实或 fixture 账本）："
    )
    for line in pollution:
        print(f"  {line}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
