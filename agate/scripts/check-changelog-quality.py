#!/usr/bin/env python3
"""check-changelog-quality.py — CHANGELOG 条目「过程日志化」判据（RM-AG0117）

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
    # A6 教训/复犯：向读者交代「我学到什么」。
    # ⚠️ **不要**加 `勘误` 与裸 `自我更正`：
    #   · `勘误` 是 CHANGELOG 的**正当用法**（"勘误：上一版的版本号写错了"是在说**修了什么**）。
    #     实测：A6 含 `勘误` + A7 含 `上一版` 叠加 ⇒ 两条纯正当的勘误行 total=4/cats=2，
    #     端到端 pre-commit rc=1 **误阻断**（评审 B-2）。
    #   · `自我更正` 可指「审计口径自我更正」（规格口径，非作者心态；v0.81.0 实测误伤）。
    ("A6-lessons", re.compile(
        r"(教训|复犯|事后复盘)")),
    # A7 **作者自述**的版本迭代痕迹。只认「作者在讲自己怎么改的」的句式。
    # ⚠️ **不要**加 `上一版(的|写)` / `原先写`：它们既可用于正当勘误，也是误伤主源（见 A6 注）。
    ("A7-revisions", re.compile(
        r"(第一版(?:判断|写|实现|是)|原先(?:实现|判断|以为)|我(?:原先|本来|一开始))")),
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

    返回 [(标题行, 正文, is_unreleased), ...]。

    ⚠️ **两段的处置不同**（评审判定 B-3）：
      · `[Unreleased]` 是**作者正在写**的 ⇒ 命中即 `exit 1` 阻断，让他改。
      · 最新**已发布**段是**历史快照** ⇒ 命中只报 `exit 2`（提示），**不阻断**。
        理由：已发布段的原则上是"保留不动"（`docs/guides/doc-freshness-guide.md` §3），
        若对它硬阻断，唯一出路是改写历史快照——与那条既有纪律直接冲突，且会让
        "升级协议后第一次提交就被卡住"（存量仓库里已发布段本就可能有过程痕迹）。
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
            picked.append((ln, "\n".join(lines[idx + 1:end]), True))
            break

    # 最新一个已发布段 = 首个非 Unreleased 的 `## [` 段
    for idx, ln in heads:
        if "[Unreleased]" in ln:
            continue
        end = next((j for j, _ in heads if j > idx), len(lines))
        picked.append((ln, "\n".join(lines[idx + 1:end]), False))
        break

    return picked


_CODE_FENCE = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)


def _strip_code_fences(body):
    """只剥**围栏代码块**——里面是示例 YAML/shell，不是作者叙述。

    ⚠️ **不要再加「行级元讨论豁免」**（曾经的 `_META_DISCUSSION`）：它按「行内含某词」整行
    跳过，于是**在坏条目里插一个词就能让整行免检**。实测 11 个词里 6 个仍能绕过
    （加「（阈值）/（自检）/（词表）/（扫描面）/（误伤）/（本判据）」均使 total 5→0）。
    这类「按词豁免」本质上是把判据的键交给被检对象，**不可靠**。

    代价（接受）：若作者在变更说明里**列举**本判据的词表，那些词会被计入，可能误报。
    缓解办法不是加豁免，而是**别在 CHANGELOG 里复述词表**（写成「见判据脚本」即可）——
    把责任放在文档写法上，而不是让判据开一个任意豁免的口。
    """
    return _CODE_FENCE.sub("", body)


def scan(text):
    """返回 (total, [{category, hits}, ...], hints)。

    total 只累加 `_CATEGORIES` 的命中数；`_HINT_ONLY` 的命中进 hints（不参与判定）。
    """
    sections = target_sections(text)
    unreleased = _strip_code_fences("\n".join(b for _, b, u in sections if u))
    released = _strip_code_fences("\n".join(b for _, b, u in sections if not u))

    def _collect(body):
        found, total = [], 0
        for name, rx in _CATEGORIES:
            hits = [m.group(0) for m in rx.finditer(body)]
            if hits:
                found.append({"category": name, "hits": hits})
                total += len(hits)
        return total, found

    total, found = _collect(unreleased)
    rel_total, rel_found = _collect(released)
    hints = [m.group(0) for m in _HINT_ONLY.finditer(unreleased + "\n" + released)]
    return total, found, hints, (rel_total, rel_found)


def _format_detail(total, found):
    cats = "；".join(
        f"{c['category']}×{len(c['hits'])}（{', '.join(c['hits'][:3])}…）"
        for c in found
    )
    return f"命中 {total} 处 / {len(found)} 类：{cats}"


_GUIDANCE = (
    "  CHANGELOG 的读者要判断「是否影响我、我要做什么」。请只保留：\n"
    "    发生了什么 / 影响是什么 / 怎么修（含升级动作）\n"
    "  以下内容请移到 commit message、PR 描述或 docs/reviews/：\n"
    "    我是怎么发现的、评审了几轮、变异实验、N passed、自我勘误、第一版写错了\n"
    "  写法见 CHANGELOG.md 顶部「怎么写一条变更」；自证：\n"
    "    python3 agate/scripts/agate-changelog-quality.py CHANGELOG.md\n"
)


def main():
    args = list(sys.argv[1:])
    warn_only = "--warn-only" in args
    args = [a for a in args if a != "--warn-only"]
    path = args[0] if args else os.environ.get("CHANGELOG_FILE", "CHANGELOG.md")

    text = _read(path)
    if text is None:
        # 无 CHANGELOG → 判据不适用（与 check-changelog.py 的「GATE SKIP」同取向）
        return 0

    total, found, hints, (rel_total, rel_found) = scan(text)

    # ── [Unreleased]：作者正在写的内容，命中即阻断 ──
    fires = total >= FIRE_MIN_TOTAL and len(found) >= FIRE_MIN_CATEGORIES
    # ── 最新已发布段：历史快照，命中只提示（见 target_sections 的说明） ──
    rel_fires = rel_total >= FIRE_MIN_TOTAL and len(rel_found) >= FIRE_MIN_CATEGORIES

    if not fires and not rel_fires:
        return 0

    if fires:
        sys.stderr.write(
            "GATE CHANGELOG-QUALITY: `[Unreleased]` 条目像是在写「工作过程」而非「变更记录」"
            f"（{_format_detail(total, found)}）\n" + _GUIDANCE
        )
    if rel_fires:
        sys.stderr.write(
            "NOTE CHANGELOG-QUALITY: 最新**已发布**段也含过程痕迹"
            f"（{_format_detail(rel_total, rel_found)}）\n"
            "  该段属历史快照（`doc-freshness-guide.md` §3：保留不动）⇒ **不阻断**，仅提示。\n"
            "  若你正在为下一版写内容，请确认它们写在 `[Unreleased]` 而不是续写已发布段。\n"
        )
    if hints:
        sys.stderr.write(
            f"  （另命中「评审指出/发现」{len(hints)} 处——这类若是在说明**修了什么**属正当，未计入）\n"
        )

    if fires:
        return 2 if warn_only else 1
    # 只有已发布段命中 ⇒ 仅提示；`--warn-only` 语义下同样是 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
