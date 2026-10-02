#!/usr/bin/env python3
"""agate-mark.py — 正文标记**生成器**（形态单源的写入侧）

配套 agate_markers.py（读取/判定侧）：本脚本负责**生成**合法写法，使「按格式写」不再靠人记。

设计依据 docs/design-notes/design-marker-single-source.md §3.3。
**为什么不落盘**（D2 决策 = 只输出 stdout）：工具替 agent 写产出是越界；且 agent 需要把内容
与自己的叙述组织在一起，直接复制粘贴比让工具 append 更可控。

CLI：
  agate-mark.py --list                      列出全部标记 + 用途 + 适用阶段 + 示例
  agate-mark.py --check FILE                校验文件内标记形态（复用单源判据）
  agate-mark.py NAME [参数...]              生成一条标记写法（stdout）
  agate-mark.py --json NAME                 生成并输出结构化信息（供程序消费）

退出码：0 = 成功；1 = 用法/参数错误（fail-closed，不生成非法写法）。
"""

import json
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import agate_markers  # noqa: E402

USAGE = (
    "用法:\n"
    "  agate-mark.py --list                列出全部已登记标记\n"
    "  agate-mark.py --check FILE          校验文件内标记形态\n"
    "  agate-mark.py NAME [参数...]        生成一条标记写法\n"
    "  agate-mark.py --json NAME [参数...]  生成结构化结果\n"
)


def cmd_list():
    for n in agate_markers.names():
        sys.stdout.write(agate_markers.describe(n) + "\n")
    return 0


def cmd_check(path):
    if not os.path.isfile(path):
        sys.stderr.write(f"GATE ERROR: 文件不存在: {path}\n")
        return 1
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    total = 0
    for n in agate_markers.names():
        for hit in agate_markers.find(text, n):
            sys.stdout.write(f"{path}:{hit['line_no']}: {hit['raw']}\n")
            total += 1
    sys.stdout.write(f"# {os.path.basename(path)}: 共 {total} 条标记声明\n")
    return 0


def cmd_render(name, params, as_json):
    try:
        spec = agate_markers.spec(name)
        rendered = agate_markers.render(name, params)
    except KeyError as exc:
        sys.stderr.write(f"GATE ERROR: {exc}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"GATE ERROR: {exc}\n")
        return 1

    if as_json:
        sys.stdout.write(json.dumps({
            "name": name,
            "rendered": rendered,
            "purpose": spec["purpose"],
            "phases": spec["phases"],
            "params": spec["params"],
        }, ensure_ascii=False) + "\n")
    else:
        sys.stdout.write(rendered + "\n")
    return 0


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write(USAGE)
        return 1
    if args[0] in ("-h", "--help"):
        sys.stdout.write(USAGE)
        return 0
    if args[0] == "--list":
        return cmd_list()
    if args[0] == "--check":
        if len(args) < 2:
            sys.stderr.write("用法: agate-mark.py --check FILE\n")
            return 1
        return cmd_check(args[1])
    if args[0] == "--json":
        if len(args) < 2:
            sys.stderr.write("用法: agate-mark.py --json NAME [参数...]\n")
            return 1
        return cmd_render(args[1], " ".join(args[2:]) or None, as_json=True)
    return cmd_render(args[0], " ".join(args[1:]) or None, as_json=False)


if __name__ == "__main__":
    sys.exit(main())
