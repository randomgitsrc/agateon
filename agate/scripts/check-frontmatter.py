#!/usr/bin/env python3
"""check-frontmatter.py FILE — frontmatter schema 校验（P1/P2/P6/P7，v2.0 T001 流 A）

从 check-frontmatter.sh 迁移（TAG0010 批次 1a）。CLI 契约与 sh 版等价：
exit 0 = 格式正确（含非目标文件 / 旧格式无 frontmatter）; exit 1 = 格式错误。
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _run_check(file_path):
    """调 agate-frontmatter-check.py（env FILE 传参，subprocess + sys.executable）。

    返回 (returncode, stdout, stderr)。用 env 传参避免 shell 变量注入 Python 代码
    （同 check-state-yaml.py 惯例）。
    """
    env = dict(os.environ)
    env["FILE"] = file_path
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "agate-frontmatter-check.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return 1, "", ""
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-frontmatter.py FILE\n")
        sys.exit(1)
    file_path = args[0]

    if not os.path.isfile(file_path):
        sys.stderr.write(f"GATE SKIP: check-frontmatter: 目标文件不存在（{file_path}），未校验\n")
        sys.exit(0)

    py_exit, errors, py_stderr = _run_check(file_path)

    # P4-review.md CRITICAL fix B（纵深防御）：python 非零退出 = 校验器自己崩了 →
    # fail-closed，exit 1，并把 stderr 打印出来方便排查（不再把"校验器崩溃"误判成 exit 0）。
    if py_exit != 0:
        sys.stderr.write(
            f"GATE FRONTMATTER: {file_path} frontmatter 校验器异常退出（exit {py_exit}），fail-closed 拦截：\n"
        )
        sys.stderr.write(py_stderr)
        sys.exit(1)

    if errors:
        sys.stderr.write(f"GATE FRONTMATTER: {file_path} frontmatter 格式错误：\n")
        for line in errors.splitlines():
            if line:
                sys.stderr.write(f"  - {line}\n")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
