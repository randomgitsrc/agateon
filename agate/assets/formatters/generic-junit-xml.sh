#!/usr/bin/env bash
set -euo pipefail

EXIT_CODE="${1:-1}"
# 数据经 **fd 3** 直连 python 的 stdin（`3<&0` 把原始 stdin 复制到 fd3，随后
# heredoc 只占用 fd0）——**零临时文件、零环境变量承载**：
#  · 经 env 传输出会超 execve 的 MAX_ARG_STRLEN(128KB) → python3 启动即 E2BIG；
#  · 经临时文件则**新增 TMPDIR 可写依赖**（只读 /tmp 下创建失败 → set -e 中止，
#    反而复活本批要消灭的「回退 raw_output → 误判 A 类假红灯」路径）。
# 调用契约不变：`<formatter>.sh <exit_code>`，测试输出仍走 stdin。
export EXIT_CODE

python3 - 3<&0 <<'PYEOF'
import sys, json, re, os

exit_code = int(os.environ.get("EXIT_CODE", "1"))
with os.fdopen(3, "r", encoding="utf-8", errors="replace") as fh:
    output = fh.read()

def extract_attr(pattern):
    m = re.search(pattern, output)
    return int(m.group(1)) if m else 0

total = extract_attr(r'tests="(\d+)"')
failures = extract_attr(r'failures="(\d+)"')
errors = extract_attr(r'errors="(\d+)"')
passed = total - failures - errors

failed_tests = []
for m in re.finditer(r"<testcase[^>]*>.*?<(?:failure|error)", output, re.DOTALL):
    name_match = re.search(r'name="([^"]*)"', m.group(0))
    cls_match = re.search(r'classname="([^"]*)"', m.group(0))
    name = name_match.group(1) if name_match else ""
    cls = cls_match.group(1) if cls_match else ""
    failed_tests.append(cls + "::" + name if cls else name)

result = {
    "exit_code": exit_code,
    "total": total,
    "passed": passed,
    "failed": failures,
    "errors": errors,
    "failed_tests": failed_tests,
    "import_errors": [],
    "syntax_errors": []
}

print(json.dumps(result, separators=(",", ":")))
PYEOF
