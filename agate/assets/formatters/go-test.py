"""Agateon 内置测试 formatter：go-test.sh 的解析实现。

由同目录 `go-test.sh`（bash 薄壳）经 `exec python3 <本文件> <exit_code>` 调用；
**测试原始输出经 stdin 传入**（`sys.stdin.read()`）。

为何拆成独立 .py（TAG0039 实测教训，三条路都试过）：
  · 经**环境变量**传输出 → 超 execve 的 MAX_ARG_STRLEN(128KB) 时 python3 启动即
    E2BIG（`参数列表过长`，exit 126）→ 上游 check-tdd-red 回退 raw_output
    → 误判 A 类假红灯；
  · 经**临时文件** → 新增 TMPDIR 可写依赖（只读 /tmp 下创建失败 → set -e 中止
    → 同样复活上述误判路径）；
  · 经 **fd 3 重定向** → 本机 Linux 可行，但 Windows 上 python 打开该 fd 抛
    `OSError: [WinError 6] The handle is invalid`（CI windows-latest 实测）；
  · 经 `-c` + 命令替换 → Windows 下 MSYS2 的 argv 转换对正则里的反斜杠敏感。
独立 .py + stdin 是三平台零特殊机制的标准调用。
"""

import json
import re
import sys

exit_code = int(sys.argv[1]) if len(sys.argv) > 1 else 1
output = sys.stdin.read()

def extract_count(pattern):
    m = re.search(pattern, output)
    return int(m.group(1)) if m else 0

passed = extract_count(r"(\d+)\s+passed")
failed = extract_count(r"(\d+)\s+failed")
total = passed + failed

failed_tests = re.findall(r"--- FAIL:\s+(\S+)", output)
failed_tests += re.findall(r"test\s+(\S+)\s+\.\.\.\s+FAILED", output)

import_errors = []
for m in re.finditer(r'cannot find "([^"]+)"', output):
    import_errors.append({"module": m.group(1), "message": m.group(0)})
for m in re.finditer(r"unresolved import\s+(\S+)", output):
    import_errors.append({"module": m.group(1), "message": m.group(0)})

syntax_errors = []
# 逐行扫描：与 MULTILINE 下 `.*(?:X).*` 的「整行匹配」语义**逐字等价**
#（`.` 不跨 `\n`），但**线性**——`.*X.*` 在超长单行上退化为 O(n²)：实测 32KB
# 单行 2.1s、2× 尺寸 4× 耗时；本仓量级（1.8MB 单行）≈1.8 小时 → formatter 挂死
# 且无超时兜底（RM-AG0077 子批 D 暴露：修好 E2BIG 后输出才第一次真正到达 python）。
for raw in output.split("\n"):
    _low = raw.lower()
    if "syntax error" not in _low and "parse error" not in _low:
        continue
    line = raw.strip()
    file_match = re.search(r"(\S+\.(?:go|rs))", line)
    file = file_match.group(1) if file_match else ""
    syntax_errors.append({"file": file, "message": line})

result = {
    "exit_code": exit_code,
    "total": total,
    "passed": passed,
    "failed": failed,
    "errors": 0,
    "failed_tests": failed_tests,
    "import_errors": import_errors,
    "syntax_errors": syntax_errors
}

print(json.dumps(result, separators=(",", ":")))
