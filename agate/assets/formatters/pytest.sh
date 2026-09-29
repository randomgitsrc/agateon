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

passed = extract_count(r"(\d+) passed")
failed = extract_count(r"(\d+) failed")
errors = extract_count(r"(\d+) error")
total = passed + failed + errors

failed_tests = re.findall(r"^FAILED (\S+)", output, re.MULTILINE)
failed_tests += [m.group(1) for m in re.finditer(r"^(\S+) FAILED", output, re.MULTILINE)]

import_errors = []
# 逐行扫描：与 MULTILINE 下 `.*(?:X).*` 的「整行匹配」语义**逐字等价**
#（`.` 不跨 `\n`），但**线性**——`.*X.*` 在超长单行上退化为 O(n²)：实测 32KB
# 单行 2.1s、2× 尺寸 4× 耗时；本仓量级（1.8MB 单行）≈1.8 小时 → formatter 挂死
# 且无超时兜底（RM-AG0077 子批 D 暴露：修好 E2BIG 后输出才第一次真正到达 python）。
for raw in output.split("\n"):
    if "ImportError" not in raw and "ModuleNotFoundError" not in raw:
        continue
    line = raw.strip()
    mod_match = re.search(r"cannot import name \S+ from ['\"](\S+?)['\"]", line)
    if not mod_match:
        mod_match = re.search(r"No module named ['\"](\S+?)['\"]", line)
    if not mod_match:
        mod_match = re.search(r"from ['\"](\S+?)['\"]", line)
    module = mod_match.group(1) if mod_match else ""
    import_errors.append({"module": module, "message": line})

syntax_errors = []
for raw in output.split("\n"):
    if "SyntaxError" not in raw and "IndentationError" not in raw:
        continue
    line = raw.strip()
    file_match = re.search(r'File "([^"]+)"', line)
    if not file_match:
        file_match = re.search(r"(\S+\.py)", line)
    file = file_match.group(1) if file_match else ""
    syntax_errors.append({"file": file, "message": line})

name_errors = []
for raw in output.split("\n"):
    # 取行内**最后一个**匹配：与旧式 `.*NameError: name '([^']+)' is not defined.*` 的
    # 贪婪语义一致（`.*` 会回溯到末个起点）。若改用 `search`（取首个），单行含两个
    # NameError 时 symbol 会由 `myapp.a` 变成 `x` —— 那是**语义变化**，不是等价替换
    # （RM-AG0077 独立评审发现的反例）。无前置 `.*` 故仍为线性。
    _hits = list(re.finditer(r"NameError: name '([^']+)' is not defined", raw))
    if not _hits:
        continue
    line = raw.strip()
    symbol = _hits[-1].group(1)
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
