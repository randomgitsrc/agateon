#!/usr/bin/env python3
"""agate-changelog-quality.py — CHANGELOG 条目「过程日志化」判据（RM-AG0117）

CHANGELOG 是给**读者**看的：读者要判断「这个版本会不会影响我、我要做什么」。
它**不是**工作过程记录——「第一版判断错了」「三轮独立评审指出」「变异实验转红」
「31 passed」这类内容对读者没有决策价值，属 commit message、PR 描述或 `docs/reviews/`
的职责。

**为什么需要机械判据**（而不是只写规范）：本仓实证——纯 WARNING 级约束会被无视
（`SELF-GATE.md` 自陈「WARNING 不拦截……强制力依赖主 Agent 自觉」；且本仓同款纯 warning
机制复犯 6 次后才靠 CI 阻断级守卫收住）。存量证据：v0.78.0 段 248 行、v0.77.0 段 191 行，按本判据分别命中 21 / 25 处、3 类
——均由人眼 review 放行。

**为什么不用「行数」当判据**：行数是间接指标，反例成立——v0.81.0 段 240 行但过程痕迹命中
**0** 次（长是真的因为变更多）。该拦的是「过程痕迹」，不是长度。

判据（A1/A2/A4/A5/A6/A7 六类词表；计数 ≥3 **且** 类别 ≥2 才 FIRE）：
  · 单类反复出现（如通篇「实测」）不判——那是写法习惯，不必然是过程日志；
  · 两类以上混合出现才是「工作日志」的形态特征。
  · A3（「评审指出 / 发现」）**只进提示、不计数**：它能抓到「本版修复了独立评审发现的 X」
    这类**正当**表述（该句是在说修了什么，不是过程），计数会误伤。

扫描面 = `[Unreleased]` + **最新一个已发布段**：存量历史条目不动
（`docs/guides/doc-freshness-guide.md` §3 已把「CHANGELOG 已发布版本的条目」定为历史快照、
保留不动）⇒ 对存量仓库零影响，无需豁免清单。

退出码：0 = 通过（含「无 CHANGELOG」「无 Unreleased」等不适用情形）；1 = 命中（阻断）；
        2 = 命中但以提示模式运行（`--warn-only`）。

用法：
  python3 agate-changelog-quality.py [CHANGELOG.md]
  python3 agate-changelog-quality.py --warn-only [CHANGELOG.md]
"""

import os
import re
import sys

# ── 词表 ──────────────────────────────────────────────────────────────────────
# 设计原则：每条正则只匹配「作者向读者交代自己怎么干活」的语言，而非技术内容。
# 谨慎处（见下方 _HINT_ONLY）：「评审指出/发现」可以是正当的变更说明，故不计数。
_CATEGORIES = (
    # A1 第一人称：作者在讲自己的动作/判断
    ("A1-first-person", re.compile(
        r"(我们发现|我判断|我原先|我第一版|我错|我漏|我的|我写|我先|我认为|"
        r"\bI (?:had|was|originally|first|wrongly)\b)", re.IGNORECASE)),
    # A2 评审轮次：第 N 轮 / N 轮评审 / 二轮三轮
    ("A2-review-rounds", re.compile(
        r"(第\s*[一二三四五六七八九十\d]+\s*轮|"
        r"[一二三四五六七八九十\d]+\s*轮(?:独立)?(?:评审|审查|复核)|"
        r"独立评审(?:第|共)?\s*[一二三四五六七八九十\d]+\s*(?:轮|次))")),
    # A4 测试计数：N passed / N failed / N 组断言 / 用例数
    ("A4-test-counts", re.compile(
        r"(\d+\s*passed|\d+\s*failed|[一二三四五六七八九十\d]+\s*组断言|"
        r"用例数|测试计数)")),
    # A5 变异实验：只认「作者做了实验」的说法。
    # ⚠️ **不要**加裸 `转红`：它在技术正文里是正当表述（v0.81.0 实测误伤 5 处，如
    # 「不得以『会让测试转红』为由回退」「实测 35 个用例转红」——说的是测试行为，不是作者过程）。
    ("A5-mutation", re.compile(
        r"(变异实验|变异验证|做(?:过|了)变异|(?:回退|改动)(?:即|后)转红)")),
    # A6 教训/勘误/复犯：向读者交代「我学到什么」。
    # ⚠️ **不要**加裸 `自我更正`：它在技术正文里可指「审计口径自我更正」
    #（v0.81.0 实测误伤 1 处），说的是规格口径而非作者心态。
    ("A6-lessons", re.compile(
        r"(教训|勘误|复犯|事后复盘)")),
    # A7 版本迭代痕迹：第一版 / 原先写 / 上一版
    ("A7-revisions", re.compile(
        r"(第一版(?:判断|写|实现|是)|原先(?:写|实现|判断|以为)|上一版(?:的|写))")),
)

# 只提示、不计数（避免误伤正当的变更说明）
_HINT_ONLY = re.compile(r"(评审(?:指出|发现|报出)|审查(?:指出|发现))")

FIRE_MIN_TOTAL = 3
FIRE_MIN_CATEGORIES = 2


def _read(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def target_sections(text):
    """取出 `[Unreleased]` 与**最新一个已发布**段（其余历史段不扫）。

    返回 [(标题行, 正文), ...]。找不到 `[Unreleased]` 时只返回最新已发布段；
    连已发布段都没有（如全新文件）则返回空——判据不适用，由调用方 exit 0。
    """
    if not text:
        return []
    lines = text.splitlines()
    heads = [(i, ln) for i, ln in enumerate(lines) if re.match(r"^## \[", ln)]
    if not heads:
        return []

    picked = []
    for idx, ln in heads:
        if "[Unreleased]" in ln:
            end = next((j for j, _ in heads if j > idx), len(lines))
            picked.append((ln, "\n".join(lines[idx + 1:end])))
            break

    # 最新一个已发布段 = 首个非 Unreleased 的 `## [` 段
    for idx, ln in heads:
        if "[Unreleased]" in ln:
            continue
        end = next((j for j, _ in heads if j > idx), len(lines))
        picked.append((ln, "\n".join(lines[idx + 1:end])))
        break

    return picked


_CODE_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)

# 「在讨论判据本身」的行——比单纯命中某个词严得多，防「加个词就整行豁免」。
# 必须**同时**满足「提到判据/词表」**且**「是元讨论的句式」，而非「出现某词」。
_META_DISCUSSION = re.compile(
    r"(本判据|该判据|判据本体|判据规则|词表|阈值|扫描面|自检|误伤|过程痕迹等|等\s*\d+\s*类)"
)


def _strip_non_prose(body):
    """剥掉**不该参与判定**的两类文本：

    ① **围栏代码块**：里面是示例 YAML/shell，不是作者叙述。

    ② **在讨论判据自身的句子**：写「本判据检查…」「词表包含…」这类**元讨论**时，其中的词是
       被**引用**的（作为举例），不是作者在讲自己的过程。实测：RM-AG0117 自己那条变更说明
       因此命中 2 处，属误伤。

    ⚠️ **判据刻意从严**：只剥「同时提到判据/词表**且**用了元讨论句式」的行。早期版本用
    「行内含『判据/命中/词表』任一即剥」，被实测证伪——在坏条目任意一行加「（判据）」二字
    即可让该行全部豁免，`total` 从 5 直接归零。宁可保留少量误伤（作者可换个写法），
    也不能留「加个词就绕过」的口子。
    """
    body = _CODE_FENCE.sub("", body)
    return "\n".join(ln for ln in body.splitlines() if not _META_DISCUSSION.search(ln))


def scan(text):
    """返回 (total, [{category, hits}, ...], hints)。

    total 只累加 `_CATEGORIES` 的命中数；`_HINT_ONLY` 的命中进 hints（不参与判定）。
    """
    sections = target_sections(text)
    body = _strip_non_prose("\n".join(b for _, b in sections))
    found = []
    total = 0
    for name, rx in _CATEGORIES:
        hits = [m.group(0) for m in rx.finditer(body)]
        if hits:
            found.append({"category": name, "hits": hits})
            total += len(hits)
    hints = [m.group(0) for m in _HINT_ONLY.finditer(body)]
    return total, found, hints


def main():
    args = list(sys.argv[1:])
    warn_only = "--warn-only" in args
    args = [a for a in args if a != "--warn-only"]
    path = args[0] if args else os.environ.get("CHANGELOG_FILE", "CHANGELOG.md")

    text = _read(path)
    if text is None:
        # 无 CHANGELOG → 判据不适用（与 check-changelog.py 的「GATE SKIP」同取向）
        return 0

    total, found, hints = scan(text)
    fires = total >= FIRE_MIN_TOTAL and len(found) >= FIRE_MIN_CATEGORIES
    if not fires:
        return 0

    detail = "；".join(
        f"{c['category']}×{len(c['hits'])}（{', '.join(c['hits'][:3])}…）"
        for c in found
    )
    sys.stderr.write(
        "GATE CHANGELOG-QUALITY: 版本条目像是在写「工作过程」而非「变更记录」"
        f"（命中 {total} 处 / {len(found)} 类：{detail}）\n"
        "  CHANGELOG 的读者要判断「是否影响我、我要做什么」。请只保留：\n"
        "    发生了什么 / 影响是什么 / 怎么修（含升级动作）\n"
        "  以下内容请移到 commit message、PR 描述或 docs/reviews/：\n"
        "    我是怎么发现的、评审了几轮、变异实验、N passed、自我勘误、第一版写错了\n"
        "  写法见 CHANGELOG.md 顶部「怎么写一条变更」；自证：\n"
        "    python3 agate/scripts/agate-changelog-quality.py CHANGELOG.md\n"
    )
    if hints:
        sys.stderr.write(
            f"  （另命中「评审指出/发现」{len(hints)} 处——这类若是在说明**修了什么**属正当，未计入）\n"
        )
    return 2 if warn_only else 1


if __name__ == "__main__":
    sys.exit(main())
