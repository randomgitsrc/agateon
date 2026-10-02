#!/usr/bin/env python3
"""check-scope-resolved.py — SCOPE+ 处理追踪（P2.11）

从 check-scope-resolved.sh 迁移（TAG0010 批次 1a）。CLI 契约与 sh 版等价：
检查产出含 [SCOPE+] 时，P1-requirements.md 有对应 [SCOPE_RESOLVED] 标记
exit 0 = 通过; exit 1 = SCOPE+ 未处理; exit 2 = 无 task 目录。

判据形态（2026-10-01 放宽，RM-AG0077⑦ 遗留项）：[SCOPE+] 的**行首声明**按下述形态识别——
裸 `[SCOPE+]` / 列表符 `- [SCOPE+]` / 粗体 `**[SCOPE+]**` / 引用块 `> [SCOPE+]`。
反引号包裹与行中出现视为「提及」，不触发校验（保守边界，理由见下方常量注释）。
"""

import glob
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 行首声明形态（RM-AG0077⑦ 遗留项 hotfix，2026-10-01）：除裸 `[SCOPE+]` / `- [SCOPE+]`
# 外，还认**粗体** `**[SCOPE+]**`（TPV0099 实际写法）与**引用块** `> [SCOPE+]`——
# 原正则 `^\s*-?\s*\[SCOPE\+\]` 对这两种返回 False，导致 scope_found 空、脚本静默早退
# （exit 0），SCOPE_RESOLVED 校验被跳过，与「已闭环」在退出码上不可区分。
#
# **刻意保留的未覆盖面**（如实登记，非遗漏）：
#   ① 行首反引号 `` - `[SCOPE+]` `` **不**算声明。⚠️ **不是「一律是引述」**——存量实测
#      `TAG0004/P4-implementation-group1.md:50` 是行首反引号包裹的**真声明**（TAG0004 的
#      P7-consistency 已登记闭环）；TAG0012/TAG0033/TAG0034 则是「`` `[SCOPE+]` ``：无」类否定。
#      纳入会新增 **5 个任务转红**（1 真声明 : 4 引述/否定）⇒ 取舍而非无代价。
#   ② 标题形态 `## N. [SCOPE+] …` **不**算声明。标题多为「容器」（正文是否定，如 TAG0012:402
#      「无新增隐含需求」），区分「容器标题 vs 声明标题」属判断类问题。纳入会新增 **4 个任务转红**
#      （行首 + 可选 `N.` 编号口径；若放宽成「标题行内任意位置」则 6 个，但那与 ③ 的口径冲突）。
#      **代价**：TAG0004 的真声明至今未被覆盖（行为与本次改动前相同，非新增回归）。
#      ⚠️ TAG0008 **不是**真声明——其标题下正文是「无」，属容器标题（初版误列，已更正）。
#   ③ 行中出现（`本节讨论 [SCOPE+] 的处置`）**不**算声明——纳入会新增 **24 个任务转红**，
#      绝大多数是散文提及。
#      ⇒ 本判据只识别**行首、非反引号包裹、非标题**的声明形态，判定为「提及」的退化为跳过语义
#      （不新增假红）。**判断类语义区分（声明 vs 提及）刻意不做**——实测该类启发式会退化。
_SCOPE_LEAD = r"^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__)?"
SCOPE_PLUS_RE = re.compile(_SCOPE_LEAD + r"\[SCOPE\+\]", re.MULTILINE)
# SCOPE_RESOLVED 侧**必须同步放宽**（RM-AG0077⑦ 的核心教训）：只放宽 SCOPE+ 一侧会让
# 「有 SCOPE+ 但标记写法不匹配」的任务**假红**——TAG0021 正是此形态（其 SCOPE_RESOLVED
# 用反引号包裹）。故此处额外接受反引号包裹（放宽 resolved 只会减少阻断，方向安全）。
SCOPE_RESOLVED_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:>\s*)?(?:\*\*|__|`)?\[SCOPE_RESOLVED($|[^a-z])", re.MULTILINE
)
SKIP_NAME_RE = re.compile(r"dispatch-context|dispatch-prompt|progress")
AGATE_CARD_RE = re.compile(r"<!-- AGATE_CARD_START -->.*?<!-- AGATE_CARD_END -->", re.DOTALL)


def _strip_agate_card(text):
    """移除 AGATE_CARD 嵌入块（等价 sh 的 sed '/START/,/END/d'，卡片模板文本含字面
    SCOPE+ 会触发误报）。"""
    return AGATE_CARD_RE.sub("", text)


def _scan_scope_plus(task_dir):
    """扫描所有顶层 .md 文件找行首 [SCOPE+]（M2 修复：SCOPE+ 可能出现在非 P 前缀文件）。
    返回命中文件 basename 空格连接串（含尾空格，与 sh 版 SCOPE_FOUND 语义一致）。"""
    found = ""
    for f in sorted(glob.glob(os.path.join(task_dir, "*.md"))):
        name = os.path.basename(f)
        if SKIP_NAME_RE.search(name):
            continue
        with open(f, encoding="utf-8") as fh:
            text = fh.read().replace("\r\n", "\n")
        if SCOPE_PLUS_RE.search(_strip_agate_card(text)):
            found += name + " "
    return found


def _scope_resolved_frontmatter(p1_file):
    """读 P1 frontmatter 结构化 scope_resolved（等价 sh 的 FILE=... agate-md-field-get.py
    scope_resolved 2>/dev/null || echo ""）。"""
    env = dict(os.environ)
    env["FILE"] = p1_file
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "agate-md-field-get.py"), "scope_resolved"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    # sh 命令替换剥掉尾部换行（agate-md-field-get 输出空结果时 print 仍打 \n，
    # sh 版 $(...) 收尾后为空串 → 落到正文回退判定）。等价：剥尾后判空。
    return (proc.stdout or "").rstrip("\n")


def _count_resolved_body(p1_file):
    """正文 [SCOPE_RESOLVED] 散文标记计数（等价 sh 的 grep -cE + tail -1，处理 "0\n0"）。"""
    with open(p1_file, encoding="utf-8") as f:
        text = f.read().replace("\r\n", "\n")
    return len(SCOPE_RESOLVED_RE.findall(text))


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-scope-resolved.py TASK_DIR\n")
        sys.exit(1)
    task_dir = args[0]
    p1_file = os.path.join(task_dir, "P1-requirements.md")

    if not os.path.isdir(task_dir):
        sys.exit(2)

    scope_found = _scan_scope_plus(task_dir)
    if not scope_found:
        sys.stderr.write(
            "GATE SKIP: check-scope-resolved: 未检出 [SCOPE+] 行首声明"
            "（裸 / 列表符 / 粗体 / 引用块形态），SCOPE_RESOLVED 校验未执行\n"
        )
        sys.exit(0)

    if not os.path.isfile(p1_file):
        sys.stderr.write(
            f"GATE SCOPE: 产出含 [SCOPE+]（{scope_found}），但无 P1-requirements.md\n"
        )
        sys.exit(1)

    # v2.0 T001 流 C（BDD-22）：优先读 P1 frontmatter 结构化 scope_resolved 列表——
    # 非空列表即已解决 → 直接通过。
    scope_resolved_fm = _scope_resolved_frontmatter(p1_file)
    if scope_resolved_fm:
        count = len([ln for ln in scope_resolved_fm.splitlines() if ln.strip()])
        sys.stderr.write(
            f"GATE SCOPE: {scope_found}有 [SCOPE+]，P1 frontmatter scope_resolved 非空（{count} 项已解决）\n"
        )
        sys.exit(0)

    resolved_count = _count_resolved_body(p1_file)
    if resolved_count == 0:
        sys.stderr.write(
            f"GATE SCOPE: 产出含 [SCOPE+]（{scope_found}），但 P1 无 [SCOPE_RESOLVED] 标记\n"
        )
        sys.exit(1)

    sys.stderr.write(
        f"GATE SCOPE: {scope_found}有 [SCOPE+]，P1 有 {resolved_count} 个 [SCOPE_RESOLVED]\n"
    )
    sys.exit(0)


if __name__ == "__main__":
    main()
