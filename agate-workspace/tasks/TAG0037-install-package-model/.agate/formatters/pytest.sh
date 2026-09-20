#!/usr/bin/env bash
set -euo pipefail

EXIT_CODE="${1:-1}"
# TAG0037 任务级覆盖（同名，resolve_formatter 优先取 $task_dir/.agate/formatters/）：
# 与稳定版 pytest.sh 逻辑逐行相同，仅把 pytest 输出经临时文件（而非环境变量）传给 python——
# 全量套件红灯输出 >128KB 时环境变量会触发 "参数列表过长"（MAX_ARG_STRLEN），使 formatter 失败并回退 raw 判定。
OUT_TMP="$(mktemp)"
trap 'rm -f "$OUT_TMP"' EXIT
cat > "$OUT_TMP"
export EXIT_CODE OUT_TMP

python3 <<'PYEOF'
import sys, json, re, os

exit_code = int(os.environ.get("EXIT_CODE", "1"))
with open(os.environ["OUT_TMP"], encoding="utf-8", errors="replace") as _fh:
    output = _fh.read()

def extract_count(pattern):
    m = re.search(pattern, output)
    return int(m.group(1)) if m else 0

passed = extract_count(r"(\d+) passed")
failed = extract_count(r"(\d+) failed")
errors = extract_count(r"(\d+) error")
total = passed + failed + errors

failed_tests = re.findall(r"^FAILED (\S+)", output, re.MULTILINE)
failed_tests += [m.group(1) for m in re.finditer(r"^(\S+) FAILED", output, re.MULTILINE)]

import_errors = []
for m in re.finditer(r".*(?:ImportError|ModuleNotFoundError).*", output):
    line = m.group(0).strip()
    mod_match = re.search(r"cannot import name \S+ from ['\"](\S+?)['\"]", line)
    if not mod_match:
        mod_match = re.search(r"No module named ['\"](\S+?)['\"]", line)
    if not mod_match:
        mod_match = re.search(r"from ['\"](\S+?)['\"]", line)
    module = mod_match.group(1) if mod_match else ""
    import_errors.append({"module": module, "message": line})

syntax_errors = []
for m in re.finditer(r".*(?:SyntaxError|IndentationError).*", output):
    line = m.group(0).strip()
    file_match = re.search(r'File "([^"]+)"', line)
    if not file_match:
        file_match = re.search(r"(\S+\.py)", line)
    file = file_match.group(1) if file_match else ""
    syntax_errors.append({"file": file, "message": line})

name_errors = []
for m in re.finditer(r".*NameError: name '([^']+)' is not defined.*", output):
    line = m.group(0).strip()
    symbol = m.group(1)
    module = symbol.rpartition('.')[0]
    name_errors.append({"symbol": symbol, "module": module, "message": line})

result = {
    "exit_code": exit_code,
    "total": total,
    "passed": passed,
    "failed": failed,
    "errors": errors,
    "failed_tests": failed_tests,
    "import_errors": import_errors,
    "syntax_errors": syntax_errors,
    "name_errors": name_errors
}

print(json.dumps(result, separators=(",", ":")))
PYEOF
