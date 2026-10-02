#!/usr/bin/env python3
"""agate_markers.py — 正文标记形态单源库（唯一权威 = rules/markers.yaml）

职责：把「一个正文标记该怎么写」这件事收敛到**一处**，消费方**取值**而非复制正则。

为什么需要（设计依据 docs/design-notes/design-marker-single-source.md）：
  本仓曾有三套互不相同的「行首」正则实现（check-scope-resolved.py 接受粗体/星号列表符；
  agate_common.py 的 DESIGN_GAP 不接受）——逐形态实测 6 种里 3 种分叉，且**静默**：
  粗体 `**[DESIGN_GAP: x]**` 在 DESIGN_GAP 侧计 0、不报错、不告警。

消费方契约（**强制**）：
  · 取值用本模块：`pattern(name)` / `find(text, name)` / `is_declaration(line, name)`
  · **不得**自带 `r"\\[SCOPE\\+]"` 类字面正则副本 —— 由 test_marker_single_source.py::mk_1 机械守护
  · 若确有例外，须在注册表加字段（如 `accept_backtick`），**不得**在消费方写 `if name == ...`

与 agate_common.py 同款约定：公共库，被 import，不直接执行（但支持 `--list` 供人查看）。
Python 3.8+（禁 match / str.removeprefix）。
"""

import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_AGATE_ROOT = os.path.dirname(SCRIPT_DIR)
MARKERS_YAML = os.path.join(_AGATE_ROOT, "rules", "markers.yaml")

try:
    import yaml
except ImportError:
    sys.stderr.write("agate_markers: 需要 pyyaml。pip install pyyaml\n")
    sys.exit(1)

# 模块级缓存：用**可变容器**而非 `global` 重新赋值
# （沿用 check-routing.py:38 的既有模式；PLW0603 禁 global 语句）。
_CACHE = {}


def _load():
    """读取并缓存注册表。返回 dict（含 lead / lead_variants / exclude / markers）。"""
    if "data" not in _CACHE:
        with open(MARKERS_YAML, encoding="utf-8") as fh:
            _CACHE["data"] = yaml.safe_load(fh)
    return _CACHE["data"]


def reload():
    """清缓存（测试用：临时改注册表后重新读取）。"""
    _CACHE.clear()


def names():
    """全部已登记标记名（按注册表顺序）。"""
    return [m["name"] for m in _load()["markers"]]


def spec(name):
    """取单个标记的注册表条目；未登记 → KeyError（fail-closed，不静默返回空）。"""
    for m in _load()["markers"]:
        if m["name"] == name:
            return m
    raise KeyError(
        f"标记 {name!r} 未登记在 rules/markers.yaml。"
        f"已登记：{', '.join(names())}——新增标记请先登记（设计 §3.4 按需增量）"
    )


def lead_for(name):
    """该标记的行首前缀。

    lead_variant 为 str → 取 lead_variants[该名]；为 list → 返回**多个前缀的联合**
    （如 DESIGN_GAP 的 P7/P4 两套口径都真实在用）。
    'default' 或未声明 → 注册表顶层 lead。
    """
    m = _load()
    variant = spec(name).get("lead_variant", "default")
    if variant == "default":
        return [m["lead"]]
    keys = [variant] if isinstance(variant, str) else list(variant)
    out = []
    for k in keys:
        if k == "default":
            out.append(m["lead"])
        else:
            if k not in m["lead_variants"]:
                raise KeyError(f"lead_variant {k!r} 未在 markers.yaml::lead_variants 定义")
            out.append(m["lead_variants"][k])
    return out


def _body(name):
    """标记本体正则。

    **关键：两个标记的参数语义本来就不一样**（等价性硬约束，批次 B 门禁）：

    | params | 本体正则 | 语义 |
    |---|---|---|
    | `none` | `\\[NAME\\]` | **`]` 必须紧跟**。故 `[SCOPE+ 观察]` / `[SCOPE+: x]` **不命中** |
    | `optional_text` / `required_text` | `\\[NAME($|[^a-z])` | **不要求紧跟 `]`**，且允许跨行 |

    实测依据（PR #387 的既有行为，必须逐字节保留）：
      · `[SCOPE+]` 用 `\\[SCOPE\\+]` —— 精确闭合
      · `[SCOPE_RESOLVED]` 用 `\\[SCOPE_RESOLVED($|[^a-z])` —— **不闭合**，因此
        `[SCOPE_RESOLVED: 跨多行的长参数…]` 能被计数（判据：标记**起始行不含 `]`**；
        此口径全仓 **3 处**：TAG0027/P7:48、TAG0031/P1:371、TAG0031/P7:60——
        换更宽口径会得到 5/11/98 等数字，**引用必须附判据**）。
      · 若给 `none` 也加 `($|[^a-z])`，`[SCOPE+ 观察]` 会被误计（实测 +2 任务改变判定）。

    参数捕获仅作用于带参形态（供 `find()` 的 `params` 字段）。

    **⚠️ HIGH-1 等价性修复（2026-10-02，独立评审查出）**：初版 `pattern("DESIGN_GAP")` 与
    `agate_common.count_design_gap` **不等价**，逐 P7 文件对账 **59 vs 121（2.05×）**。
    两个成因，**载荷点经「分约束变异 + 全仓计数」实测确认**（基准 116）：

      · 两者都有（现状）→ 116 ✅ 等价
      · 只去 `(?!\\w)`     → 116（边界在本语料上**非载荷**）
      · 只去「冒号必填」   → **124** ❌ **冒号必填才是载荷点**

    · **载荷点**：`required_text` 分支冒号必填——`agate_common` 用字面 `\\[DESIGN_GAP:`，
      故 `[DESIGN_GAP]`（无参）应计 0，冒号可选会误计。
    · **`(?!\\w)` 是防御性冗余**：防"未来新增 `DESIGN_GAP_XXX` 型前缀标记"这一类**尚未发生**
      的情况（`DESIGN_GAP_REVIEWED` 现已被冒号约束挡住）。保留，但**不得说成主因**。

    等价性由 `mk_6a`（标记名两两互斥）+ `mk_6b`（与 agate_common 真实语料计数相等）机械守护。
    """
    s = spec(name)
    esc = re.escape(name)
    params = s["params"]
    # 三个分支的差异是**实质语义**（逐条对齐既有实现，非风格选择）：
    #   none          → `]` 必须紧跟（如 [SCOPE+]）
    #   required_text → **冒号必填**（如 agate_common 的 `\[DESIGN_GAP:` —— 故 [DESIGN_GAP] 计 0）
    #   optional_text → 冒号可选（如 SCOPE_RESOLVED / DESIGN_GAP_REVIEWED）
    #   带参两支均**不要求闭合 `]`**，允许跨行续写（存量 SCOPE_RESOLVED 3 处）
    if params == "none":
        core = r"\[" + esc + r"\]"
    elif params == "required_text":
        core = r"\[" + esc + r"\s*:\s*(.*?)($|[^a-z]|-->)"
    else:  # optional_text
        core = r"\[" + esc + r"(?::\s*(.*?))?($|[^a-z])"
    # 名称边界：标记名后不得再接词字符（防 A 吞并 A_B 型前缀标记；
    # 注意 `($|[^a-z])` 里的 `_`/`1`/`X` 都算词字符，故必须显式加此约束）。
    core += r"(?!\w)"
    if s.get("accept_backtick"):
        # 反引号包裹在**标记本体**这一层表达（行首层是全局排除项）
        core = r"`?" + core + r"`?"
    return core

def pattern(name, multiline=True):
    """该标记的**完整**正则（行首前缀 + 排除项 + 本体）。

    行首前缀取 lead_for(name) 的联合；排除项由 exclude 表驱动（backtick 在行首层排除，
    故 negative lookahead；heading 同理）。accept_backtick=true 的标记不受行首反引号排除约束。
    """
    m = _load()
    leads = lead_for(name)
    accepts_bt = bool(spec(name).get("accept_backtick"))
    body = _body(name)
    # 行首反引号排除：lead 之后再出现反引号视为引述（若该标记接受反引号则不加此约束）
    neg = "" if accepts_bt else r"(?!" + re.escape(m["exclude"]["backtick"]) + r")"
    alt = "|".join("(?:" + L + ")" for L in leads)
    flags = re.MULTILINE if multiline else 0
    return re.compile("(?:" + alt + ")" + neg + body, flags)


def find(text, name):
    """返回该标记的全部**声明**（已排除「提及」形态）。每项为 dict。

    {'name','line_no','raw','params','is_declaration': True}
    """
    rx = pattern(name)
    out = []
    for lineno, line in enumerate(text.replace("\r\n", "\n").splitlines(), 1):
        for mm in rx.finditer(line):
            out.append({
                "name": name,
                "line_no": lineno,
                "raw": mm.group(0),
                "params": (mm.group(1) or "").strip() if mm.re.groups else "",
                "is_declaration": True,
            })
    return out


def is_declaration(line, name):
    """单行是否构成该标记的**声明**（而非提及/引述）。"""
    return bool(pattern(name, multiline=False).search(line))


def count(text, name):
    """声明计数（等价旧 `grep -cE` 语义，但走单源判据）。"""
    return len(find(text, name))


def has(text, name):
    """是否含至少一条声明。"""
    return bool(pattern(name).search(text))


def render(name, params=None):
    """**生成**合法写法（供 agate-mark.py / 测试 mk_3 闭环用）。

    带参标记缺参、无参标记给参 → ValueError（fail-closed，不生成非法写法）。
    保证：render() 的产物必被 pattern(name) 命中（mk_3）。
    """
    s = spec(name)
    mode = s["params"]
    text = (params or "").strip()

    if mode == "none":
        if text:
            raise ValueError(f"标记 {name} 不接受参数（params=none），但收到 {text!r}")
        return "[" + name + "]"
    if not text:
        raise ValueError(f"标记 {name} 需要参数（params={mode}），但未提供")
    return "[" + name + ": " + text + "]"


def describe(name):
    """人类可读的单条说明（供 --list）。"""
    s = spec(name)
    ph = "/".join(s["phases"]) if s["phases"] else "不限"
    pair = ""
    if s.get("paired_with"):
        pair = f"  配对: {s['paired_with']}"
    if s.get("resolves"):
        pair = f"  消解: {s['resolves']}"
    judged = ", ".join(s.get("judged_by") or []) or "（无机械判据）"
    return (f"{name:22} {s['purpose']}\n"
            f"{'':22} 阶段: {ph}   参数: {s['params']}{pair}\n"
            f"{'':22} 判据消费方: {judged}\n"
            f"{'':22} 示例: {render(name, '示例内容' if s['params'] != 'none' else None)}")


def main():
    """极简 CLI（供人与调试）：--list / --check FILE / <name> [params]"""
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.stderr.write(__doc__ + "\n用法: agate_markers.py --list | --check FILE | <NAME> [params]\n")
        return 0 if args else 1
    if args[0] == "--list":
        for n in names():
            sys.stdout.write(describe(n) + "\n")
        return 0
    if args[0] == "--check":
        if len(args) < 2:
            sys.stderr.write("用法: agate_markers.py --check FILE\n")
            return 1
        path = args[1]
        if not os.path.isfile(path):
            sys.stderr.write(f"GATE ERROR: 文件不存在: {path}\n")
            return 1
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        total = 0
        for n in names():
            for hit in find(text, n):
                sys.stdout.write(f"{path}:{hit['line_no']}: {hit['raw']}\n")
                total += 1
        sys.stdout.write(f"# 共 {total} 条声明\n")
        return 0
    name = args[0]
    try:
        params = args[1] if len(args) > 1 else None
        sys.stdout.write(render(name, params) + "\n")
    except (KeyError, ValueError) as exc:
        sys.stderr.write(f"GATE ERROR: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
