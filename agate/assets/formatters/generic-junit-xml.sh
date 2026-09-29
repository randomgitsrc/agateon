#!/usr/bin/env bash
# generic-junit-xml.sh —— bash 薄壳：把测试输出经 stdin 交给同目录 generic-junit-xml.py 解析。
# 解析实现与平台注意事项见 generic-junit-xml.py 头部 docstring。
# 调用契约不变：`generic-junit-xml.sh <exit_code>`，测试原始输出走 stdin。
set -euo pipefail
exec python3 "$(dirname "$0")/generic-junit-xml.py" "${1:-1}"
