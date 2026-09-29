#!/usr/bin/env bash
# pytest.sh —— bash 薄壳：把测试输出经 stdin 交给同目录 pytest.py 解析。
# 解析实现与平台注意事项见 pytest.py 头部 docstring。
# 调用契约不变：`pytest.sh <exit_code>`，测试原始输出走 stdin。
set -euo pipefail
exec python3 "$(dirname "$0")/pytest.py" "${1:-1}"
