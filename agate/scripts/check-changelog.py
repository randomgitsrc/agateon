#!/usr/bin/env python3
"""check-changelog.py — CHANGELOG [Unreleased] 含 task_id 检查（P1.6）

从 check-changelog.sh 迁移（TAG0010 批次 1a）。CLI 契约与 sh 版等价：
exit 0 = 通过; exit 1 = 未记录; 无 CHANGELOG 文件时 exit 0。
"""

import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _unreleased_content(changelog_file):
    """调 agate-changelog-unreleased.py 提取 [Unreleased] 区域（subprocess + sys.executable）。

    等价 sh 的 `CHANGELOG_FILE=... python3 agate-changelog-unreleased.py 2>/dev/null || echo ""`：
    子进程非零退出（如 python 不可用/脚本崩溃）→ 返回空串。
    """
    env = dict(os.environ)
    env["CHANGELOG_FILE"] = changelog_file
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "agate-changelog-unreleased.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    # sh 命令替换剥掉尾部换行（$(...) 语义）；剥后空串表示无 [Unreleased] 区域
    return (proc.stdout or "").rstrip("\n")


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-changelog.py TASK_ID\n")
        sys.exit(1)
    task_id = args[0]
    changelog_file = os.environ.get("CHANGELOG_FILE", "CHANGELOG.md")

    # v2.0 流 D（BDD-27）：不截取短前缀，直接用完整 task_id 作为搜索关键词。
    # 新格式 task_id（如 TAG0001）本身就是完整短标识（check-changelog.sh 迁移源保留此语义）。
    if not os.path.isfile(changelog_file):
        sys.stderr.write(f"GATE SKIP: check-changelog: CHANGELOG 不存在（{changelog_file}），未校验\n")
        sys.exit(0)

    # 问题6 (T090)：post-bump 模式（bump-version 调用时）——检查新版本段落非空，而非 [Unreleased]
    if os.environ.get("CHECK_CHANGELOG_MODE", "normal") == "post-bump":
        latest_section = ""
        with open(changelog_file, encoding="utf-8") as f:
            for line in f:
                if re.match(r"^## \[", line):
                    latest_section = line
                    break
        if not latest_section:
            sys.stderr.write("GATE CHANGELOG: 无版本段落\n")
            sys.exit(1)
        sys.exit(0)

    unreleased = _unreleased_content(changelog_file)
    if not unreleased:
        sys.stderr.write(f"GATE CHANGELOG: {changelog_file} 无 [Unreleased] 区域\n")
        sys.exit(1)

    # grep -qE "(^|[^0-9])${TASK_ID}( |:|$|,|-)" 的 re 等价：单词边界保护，
    # 防 TAG0001 被 TAG00012 这类"更长编号任务"的条目误判为匹配（BDD-27 / CL.7）。
    if re.search(
        rf"(^|[^0-9]){re.escape(task_id)}( |:|$|,|-)",
        unreleased,
        flags=re.M,
    ):
        sys.exit(0)

    sys.stderr.write(
        f"GATE CHANGELOG: [Unreleased] 区域未找到 {task_id}（或 {task_id}）\n"
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
