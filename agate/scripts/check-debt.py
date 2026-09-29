#!/usr/bin/env python3
"""check-debt.py — tech-debt.md 条目 schema 校验 + 回退覆盖比对（TAG0001 D3）

从 check-debt.sh 迁移（TAG0010 批次 2a）。CLI 契约与 sh 版等价：
  用法：
    check-debt.py FILE                    # FILE 模式：schema 校验（fail-closed）
    check-debt.py --retreat-coverage      # 回退覆盖比对（只读 WARNING）
exit 0 = 通过（FILE 模式：schema 合法 / 文件不存在 / 无 yaml 块；覆盖模式：比对完成无缺失，
    或无 retreat 提交等有意跳过分支）
exit 1 = FILE 模式：schema 非法或校验器异常（fail-closed）
exit 2 = 覆盖模式：依赖加载失败（agate_common 不可导入），需主 Agent 自判

迁移说明：source agate-workspace-resolve.sh → agate_common.resolve_workspace；
git log 提取 retreat 提交 → agate_common.run_git（同 2>/dev/null || true 语义）；
$(...) 剥尾换行 → .rstrip("\n")；agate-debt-check.py --covered-hashes 子进程 →
sys.executable subprocess；fail-closed 薄壳（python 非零退出 / stdout 错误行）等价复刻。
"""

import os
import subprocess
import sys

try:
    from agate_common import resolve_workspace, run_git
except ImportError:
    resolve_workspace = None
    run_git = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGATE_DEBT_CHECK = os.path.join(SCRIPT_DIR, "agate-debt-check.py")


def _covered_hashes(debt_file):
    """调 agate-debt-check.py --covered-hashes（$(...) 剥尾换行 + 失败回退空集合）。
    返回 evidence 中已覆盖的 hex token 集合。"""
    try:
        proc = subprocess.run(
            [sys.executable, AGATE_DEBT_CHECK, "--covered-hashes", debt_file],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return set()
    if proc.returncode != 0:
        return set()
    return set((proc.stdout or "").splitlines())


def _short_hash(full, cwd):
    """调 `git rev-parse --short {full}` 得到运行环境下的真实 short hash 长度
    （TAG0023 RM-AG0044，BDD-8/9）。固定 7 位前缀切片在 CI runner（git 2.55.0）与
    本地（git 2.43.0）下的 auto-abbrev 算法计算长度可能不一致，导致 mismatch
    （PR #188 实证：CI 双 run 一过一挂）。git 调用失败时回退固定 7 位前缀，
    不让辅助计算的异常掩盖原有比对能力。"""
    rc, out = run_git(["rev-parse", "--short", full], cwd=cwd)
    if rc == 0 and out.strip():
        return out.strip()
    return full[:7]


def _retreat_coverage(repo_root):
    """回退覆盖比对：git log 提取 retreat 提交，与 tech-debt.md 中 source: retreat
    条目的 evidence 引用比对，缺失打 WARNING。依赖加载失败 → exit 2（需主 Agent 自判）。"""
    if resolve_workspace is None:
        sys.stderr.write(
            "GATE DEBT: 缺少 agate_common.py（resolve_workspace），无法解析工作区，回退覆盖比对无法执行\n"
        )
        sys.exit(2)

    workspace, _tasks = resolve_workspace(repo_root)
    debt_file = os.path.join(workspace, "debt", "tech-debt.md")

    # 提取 retreat 提交（只读比对，零新增埋点；--grep='^retreat:' 同 agate-retreat-to.sh 提交格式）
    rc, retreats = run_git(
        ["log", "--all", "--format=%H%x09%s", "--grep=^retreat:"], cwd=repo_root
    )
    if rc != 0 or not retreats.strip():
        sys.stderr.write("GATE SKIP: check-debt(--retreat-coverage): 无 retreat 提交，未核对\n")
        return 0

    covered = _covered_hashes(debt_file)

    for line in retreats.splitlines():
        if not line:
            continue
        parts = line.split("\t", 1)
        full = parts[0]
        subject = parts[1] if len(parts) > 1 else ""
        short = _short_hash(full, repo_root)
        if short not in covered and full not in covered:
            sys.stderr.write(
                f"GATE DEBT WARNING: retreat 提交 {short}（{subject}）未登记为 source: retreat DEBT 条目"
                f"（evidence 须引用该提交，文件 {debt_file}）\n"
            )
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-debt.py FILE 或 check-debt.py --retreat-coverage\n")
        sys.exit(1)
    mode = args[0]

    if mode == "--retreat-coverage":
        repo_root = args[1] if len(args) > 1 else os.getcwd()
        sys.exit(_retreat_coverage(repo_root))

    file_path = mode
    if not os.path.isfile(file_path):
        # 此处**有意保持静默**：BDD-10 明文规定「无文件 → exit 0 无输出」为向后兼容契约
        # （存量项目可能尚无 debt 文件），故不按 RM-AG0077 子批 A 的通则加跳过声明。
        # 代价：登记簿路径配错时无人察觉——已作为已知局限登记在 RM-AG0077，留待显式决策。
        sys.exit(0)

    # fail-closed 薄壳（同 check-frontmatter.sh）：校验器非零退出（自身崩溃）→ exit 1；
    # 正常退出但 stdout 有错误行 → exit 1；两条件均不满足 → 真无错误，exit 0。
    env = dict(os.environ)
    env["FILE"] = file_path
    try:
        proc = subprocess.run(
            [sys.executable, AGATE_DEBT_CHECK],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        sys.stderr.write(
            f"GATE DEBT: {file_path} tech-debt 校验器异常退出（exit 1），fail-closed 拦截：\n"
        )
        sys.exit(1)

    if proc.returncode != 0:
        sys.stderr.write(
            f"GATE DEBT: {file_path} tech-debt 校验器异常退出（exit {proc.returncode}），fail-closed 拦截：\n"
        )
        if proc.stderr:
            sys.stderr.write(proc.stderr)
        sys.exit(1)

    errors = (proc.stdout or "").rstrip("\n")
    if errors:
        sys.stderr.write(f"GATE DEBT: {file_path} tech-debt 条目格式错误：\n")
        for line in errors.splitlines():
            if line:
                sys.stderr.write(f"  - {line}\n")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
