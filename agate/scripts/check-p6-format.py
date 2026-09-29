#!/usr/bin/env python3
"""check-p6-format.py — P6-acceptance.md 行格式检查/归一化（P4 批次 1b）

从 check-p6-format.sh 迁移（TAG0010 批次 1b）。CLI 契约与 sh 版等价：
  check-p6-format.py [--fix|--check] FILE
exit 0/1 语义与 stderr 输出格式逐字节保留。

- --check：逐条结果行须严格匹配行首 `- PASS|FAIL BDD-N`（大写、紧跟一个空格、
  带 BDD 编号）；候选行（疑似 PASS/FAIL 声明，大小写不敏感、含全角/半角冒号变体，
  用词边界 \\b 排除 "failure" 等非目标词）不达标即报格式偏差（exit 1）。
- --fix：归一化 sed 等价实现（pass/fail 大小写 + 前导空白剥离 + 总结行
  **Summary** 化），frontmatter/正文切分语义与 sh 版逐字节对齐。
"""

import os
import re
import sys

# --check 候选行：疑似 PASS/FAIL 逐条声明（大小写不敏感，\\b 排除 "failure"）
_CANDIDATE = re.compile(r"^\s*-\s+(pass|fail)\b", re.IGNORECASE)
# --check 严格格式：行首 `- PASS|FAIL BDD-N`（大写、紧跟一个空格、带 BDD 编号）
_STRICT = re.compile(r"^\s*-\s+(?:PASS|FAIL)\s+BDD-[0-9]+")

# --fix 归一化正则（与 sh 版 sed -E 管道逐字节等价，按行应用）
_FIX_PASS_FAIL = [
    (re.compile(r"^(\s*)-\s+(pass)(\s|:|：|$)"), r"\1- PASS\3"),
    (re.compile(r"^(\s*)-\s+(fail)(\s|:|：|$)"), r"\1- FAIL\3"),
    (re.compile(r"^(\s*)(pass)(\s|:|：|$)"), r"\1- PASS\3"),
    (re.compile(r"^(\s*)(fail)(\s|:|：|$)"), r"\1- FAIL\3"),
]
_FIX_DEDENT = (re.compile(r"^\s+(- (?:PASS|FAIL) )"), r"\1")
_FIX_SUMMARY = (re.compile(r"^-\s+(PASS|FAIL)\s*(:|：)\s*([0-9]+)\s*$"), r"**Summary**: \1: \3")


def _apply_line_patterns(lines, patterns):
    """把归一化模式逐行应用（等价 sh 的 sed 管道；锚点 ^/$ 不跨行）。"""
    changed = False
    out = []
    for line in lines:
        cur = line
        for pat, repl in patterns:
            cur = pat.sub(repl, cur)
        if cur != line:
            changed = True
        out.append(cur)
    return out, changed


def main():
    mode = "check"
    file = ""
    for arg in sys.argv[1:]:
        if arg == "--fix":
            mode = "fix"
        elif arg == "--check":
            mode = "check"
        else:
            file = arg

    if not file or not os.path.isfile(file):
        sys.stderr.write(f"GATE SKIP: check-p6-format: 目标文件不存在（{file}），未校验\n")
        sys.exit(0)
    if os.path.basename(file) != "P6-acceptance.md":
        sys.stderr.write(f"GATE SKIP: check-p6-format: 非 P6-acceptance.md（{os.path.basename(file)}），未校验\n")
        sys.exit(0)

    with open(file, encoding="utf-8") as f:
        content = f.read()

    if mode == "check":
        invalid = 0
        for line in content.splitlines():
            if _CANDIDATE.search(line) and not _STRICT.search(line):
                invalid += 1
        if invalid > 0:
            sys.stderr.write(
                f"P6 format deviations found (use --fix to auto-fix): {invalid} 行不符合 '- PASS|FAIL BDD-N:' 逐条格式（总结行/小写/全角均须归一化）\n"
            )
            sys.exit(1)
        sys.exit(0)

    # --fix：frontmatter/正文切分（sh 版语义：首行恰为 "---"，其后第一条以 "---"
    # 起始的行视为闭合边界；找不到 → 无 frontmatter 块，全文本按正文处理）
    body = content.rstrip("\n")
    lines = body.split("\n")
    fm_part = ""
    body_part = body
    if lines and lines[0] == "---":
        close = None
        for idx in range(1, len(lines)):
            if lines[idx].startswith("---"):
                close = idx
                break
        if close is not None:
            fm_part = "\n".join(lines[: close + 1])
            body_part = "\n".join(lines[close + 1:])

    body_lines = body_part.split("\n")
    fixed, changed = _apply_line_patterns(body_lines, _FIX_PASS_FAIL)
    fixed, c = _apply_line_patterns(fixed, [_FIX_DEDENT])
    changed = changed or c
    fixed, c = _apply_line_patterns(fixed, [_FIX_SUMMARY])
    changed = changed or c
    fixed_body = "\n".join(fixed)

    full_fixed = (fm_part + "\n" + fixed_body if fixed_body else fm_part) if fm_part else fixed_body

    if changed:
        with open(file, "w", encoding="utf-8") as f:
            f.write(full_fixed)
    sys.exit(0)


if __name__ == "__main__":
    main()
