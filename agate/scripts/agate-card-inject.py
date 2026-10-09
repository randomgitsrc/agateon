#!/usr/bin/env python3
"""把卡片内容注入 dispatch-context 的 AGATE_CARD 占位符之间（py 抽离批次 5）。

从 DC_FILE / CARD_FILE env 读路径。替换后写回 DC_FILE。
无占位符 → stderr 提示 + exit 1（由 bash 调用方处理）。
"""

import os
import re
import sys

dc = os.environ["DC_FILE"]
with open(dc, encoding="utf-8") as f:
    text = f.read()
with open(os.environ["CARD_FILE"], encoding="utf-8") as f:
    card = f.read()
try:
    from agate_common import AGATE_CARD_PLACEHOLDER_RE as pattern  # 单源（RM-AG0104）
except ImportError:  # 独立副本降级：与 agate_common 同口径
    pattern = r"(<!-- AGATE_CARD_START -->\n)(.*?)(<!-- AGATE_CARD_END -->)"
if not re.search(pattern, text, flags=re.DOTALL):
    sys.stderr.write(f"AGATE_CARD 注入失败: {os.path.basename(dc)} 中未找到 AGATE_CARD_START/END 占位符\n")
    sys.exit(1)


def _repl(m):
    return m.group(1) + card.rstrip("\n") + "\n" + m.group(3)


new_text = re.sub(pattern, _repl, text, flags=re.DOTALL)
with open(dc, "w", encoding="utf-8") as f:
    f.write(new_text)
