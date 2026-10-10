#!/usr/bin/env python3
"""解析 P2-design.md 的 gate_commands.P5 块，输出 JSON 对象。

从 agate-capture-env-baseline.sh 内联 python 抽离（py 抽离批次 3）。
值传递走环境变量 P2_DESIGN（文件路径）。输出：
  {"commands":[{"cmd":...,"formatter":...,"suffix":...}]}
无 gate_commands.P5 块时输出空（供 bash [ -z "$P5_DATA" ] 判定跳过）。

注：无 `gate_commands:` 块时输出空；有块但仅 formatter 键（无 P5 命令键）时输出
{"commands": []}（非空）——均与内联 ORIG 行为一致。
"""

import json
import os
import re
import sys

from agate_common import is_gate_meta_key
from agate_common import strip_paired_quotes as _strip_paired_quotes

content = open(os.environ["P2_DESIGN"], encoding="utf-8").read()
if not content.endswith(chr(10)):
    content += chr(10)
m = re.search(r"^gate_commands:[ \t]*\n((?:  .*\n|\s*\n)*)", content, re.MULTILINE)
if not m:
    sys.exit(0)
block = m.group(1)
entries = []
for line in re.findall(r"^  (P5\w*):\s*(.+)$", block, re.MULTILINE):
    key = line[0]
    val = _strip_paired_quotes(line[1].strip())
    if is_gate_meta_key(key):
        continue
    suffix = key[2:] if len(key) > 2 else ""
    fmt_key = "P5" + suffix + "_formatter"
    fmt_val = ""
    for line2 in re.findall(r"^  (" + re.escape(fmt_key) + r"):\s*(.+)$", block, re.MULTILINE):
        fmt_val = _strip_paired_quotes(line2[1].strip())
    entries.append({"cmd": val, "formatter": fmt_val, "suffix": suffix})
print(json.dumps({"commands": entries}))
