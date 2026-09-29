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

def extract_count(pattern):
    m = re.search(pattern, output)
    return int(m.group(1)) if m else 0

failed = extract_count(r"Tests\s+(\d+)\s+failed")
passed = extract_count(r"Tests\s+(\d+)\s+passed")
errors = extract_count(r"Failed Suites\s+(\d+)")
total = passed + failed + errors

failed_tests = re.findall(r"^FAIL\s+(\S+)", output, re.MULTILINE)

import_errors = []
for m in re.finditer(r"Cannot find (?:module|package) ['\"]([^'\"]+)", output):
    import_errors.append({"module": m.group(1), "message": m.group(0)})

syntax_errors = []
# 逐行扫描：与 MULTILINE 下 `.*(?:X).*` 的「整行匹配」语义**逐字等价**
#（`.` 不跨 `\n`），但**线性**——`.*X.*` 在超长单行上退化为 O(n²)：实测 32KB
# 单行 2.1s、2× 尺寸 4× 耗时；本仓量级（1.8MB 单行）≈1.8 小时 → formatter 挂死
# 且无超时兜底（RM-AG0077 子批 D 暴露：修好 E2BIG 后输出才第一次真正到达 python）。
for raw in output.split("\n"):
    if not ("SyntaxError" in raw or "ParseError" in raw or "Unexpected token" in raw):
        continue
    line = raw.strip()
    file_match = re.search(r"(\S+\.(?:js|ts|jsx|tsx|mjs|cjs))", line)
    file = file_match.group(1) if file_match else ""
    syntax_errors.append({"file": file, "message": line})

result = {
    "exit_code": exit_code,
    "total": total,
    "passed": passed,
    "failed": failed,
    "errors": errors,
    "failed_tests": failed_tests,
    "import_errors": import_errors,
    "syntax_errors": syntax_errors
}

print(json.dumps(result, separators=(",", ":")))
PYEOF
