#!/usr/bin/env python3
"""E3 抽样：T1 绊线在两仓语料命中行的随机抽样（TAG0050 批 B，BDD-51）。

口径：只用 markers.yaml 的 `default` lead（lead_variant=default），排除 `exclude`
（行首反引号 / 标题）。T1 标记表**不含 PROD_TOUCHED**（由 T4 承担）。
"""
import os
import random
import re
import sys

LEAD = r"^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?"
BACKTICK_NEG = r"(?!`)"

T1 = [
    "SCOPE+", "SCOPE_RESOLVED", "DESIGN_GAP", "DESIGN_GAP_REVIEWED",
    "NEED_CONFIRM", "SUGGEST", "BLOCKER", "DEVIATION-CRITICAL",
    "CODE_MAP_UPDATED", "CODE_MAP_EXEMPT",
]
# 带参标记 params 口径（与 agate_markers._body 同构）：
TEXTY = {"SCOPE_RESOLVED", "DESIGN_GAP", "DESIGN_GAP_REVIEWED", "SUGGEST",
         "BLOCKER", "DEVIATION-CRITICAL", "CODE_MAP_UPDATED", "CODE_MAP_EXEMPT"}
NONE_PARAM = {"SCOPE+", "NEED_CONFIRM"}


def body(name):
    esc = re.escape(name)
    if name in NONE_PARAM:
        return r"\[" + esc + r"\](?![A-Za-z0-9_])"
    if name == "DESIGN_GAP":
        return r"\[" + esc + r"\s*:\s*(.*?)($|[^a-z]|-->)"
    return r"\[" + esc + r"(?::\s*(.*?))?($|[^a-z])"


def collect(root):
    hits = []
    pats = [(n, re.compile(LEAD + BACKTICK_NEG + body(n))) for n in T1]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", ".venv", "__pycache__")]
        for fn in filenames:
            if not fn.endswith(".md"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    text = fh.read().replace("\r\n", "\n")
            except OSError:
                continue
            in_card = False
            for i, line in enumerate(text.splitlines(), 1):
                if "<!-- AGATE_CARD_START -->" in line:
                    in_card = True
                    continue
                if "<!-- AGATE_CARD_END -->" in line:
                    in_card = False
                    continue
                if in_card:
                    continue
                for name, rx in pats:
                    if rx.search(line):
                        hits.append((os.path.relpath(path, root), i, name, line.strip()))
                        break
    return hits


def main():
    root = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 20261008
    hits = collect(root)
    print(f"# corpus={root} total_hits={len(hits)}")
    random.seed(seed)
    sample = random.sample(hits, min(n, len(hits)))
    sample.sort()
    for path, i, name, line in sample:
        print(f"{path}:{i}: [{name}] {line[:160]}")


if __name__ == "__main__":
    main()
