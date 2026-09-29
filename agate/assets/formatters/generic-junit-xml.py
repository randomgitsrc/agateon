"""Agateon 内置测试 formatter：generic-junit-xml.sh 的解析实现。

由同目录 `generic-junit-xml.sh`（bash 薄壳）经 `exec python3 <本文件> <exit_code>` 调用；
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
