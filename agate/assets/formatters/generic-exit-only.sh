#!/usr/bin/env bash
set -euo pipefail

EXIT_CODE="${1:-1}"
# 本 formatter **不使用**测试输出（只回传 exit_code）——故不建临时文件，
# 仅排空 stdin（避免写端 EPIPE）。此前把整份输出 `export` 进环境，
# 足以让下面 python3 的 execve 因 E2BIG 失败（RM-AG0077 子批 D）。
cat > /dev/null
export EXIT_CODE

python3 <<'PYEOF'
import sys, json, os

exit_code = int(os.environ.get("EXIT_CODE", "1"))

result = {
    "exit_code": exit_code,
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": 0,
    "failed_tests": [],
    "import_errors": [],
    "syntax_errors": []
}

print(json.dumps(result, separators=(",", ":")))
PYEOF
