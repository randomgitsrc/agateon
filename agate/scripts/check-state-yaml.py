#!/usr/bin/env python3
"""check-state-yaml.py — .state.yaml 格式校验（P2.15）

从 check-state-yaml.sh 迁移（TAG0010 批次 1a）。CLI 契约与 sh 版等价：
exit 0 = 格式正确; exit 1 = 格式错误; exit 2 = 无 .state.yaml。
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _run_check(state_file):
    """调 agate-state-yaml-check.py（env STATE_FILE 传参，subprocess + sys.executable）。

    等价 sh 的 `STATE_FILE=... python3 agate-state-yaml-check.py 2>/dev/null || true`：
    解析错误信息输出到 stdout（ERRORS 捕获）；子进程崩溃（pyyaml 缺失等）静默降级为空。
    """
    env = dict(os.environ)
    env["STATE_FILE"] = state_file
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "agate-state-yaml-check.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return proc.stdout or ""


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-state-yaml.py STATE_FILE\n")
        sys.exit(1)
    state_file = args[0]

    if not os.path.isfile(state_file):
        sys.stderr.write(
            f"GATE SKIP: check-state-yaml: .state.yaml 不存在（{state_file}），未校验（exit 2）\n"
        )
        sys.exit(2)

    errors = _run_check(state_file)
    if errors:
        sys.stderr.write("GATE STATE-YAML: .state.yaml 格式错误：\n")
        for line in errors.splitlines():
            if line:
                sys.stderr.write(f"  - {line}\n")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
