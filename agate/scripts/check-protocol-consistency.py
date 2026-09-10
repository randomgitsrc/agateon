#!/usr/bin/env python3
"""
agate 协议结构一致性检查 (P3-1)
================================

回应 LIMITATIONS.md「局限 5：协议文档自身的内部一致性不在流程内」。

设计原则：只做**结构**一致性（机器可判定），不碰**语义**一致性（不可判定）。
覆盖本仓评审 agate-review-20260626-1.md 第 1-2 章里可机器化的缺陷类型：

  CHECK 1  所有 ```yaml 代码块可被 yaml.safe_load 解析            (对应 P0-3)
  CHECK 2  协议文件内引用的 docs/assets/scripts 路径真实存在        (对应 P0-4, P1-3)
  CHECK 3  协议文件内的硬编码行号引用 `xxx.md L123`               (对应 P1-4)
  CHECK 4  跨文件字段集一致：gate_commands 键集合                  (对应 P1-2)
   CHECK 6  README LICENSE 徽章指向的文件存在 + gstack MIT 归属保留  (对应 P0-2)
   CHECK 7  README version badge 与最新 git tag 一致
   CHECK 8  v0.6 关键词存在性（DESIGN_GAP / design_trivial / model_tier / --cached）
   CHECK 9  协议-脚本结构对齐（锚点表：文档声明的规则 vs 脚本关键词存在性）
  CHECK 10  协议文档脚本名引用漂移（白名单形状对照 agate/scripts/ 实际文件）
  CHECK 11  UI/UX 机制条文跨文档一致（分类框架 / 形态适配 / 三态分档 / 证据按形态选择）
  CHECK 12  权威数值/规则跨文件一致性（防复发，锚点表：重试上限表 vs 指针文件/内联值）  (对应 BDD-9, BDD-10)
  CHECK 13  CHANGELOG 最新版本 ↔ UPGRADING.md §3 章节对应（防发布漏写章节，RM-AG0052）
  CHECK 14  markdown 叙述段落平台名扫描（护栏 1 机械化，BDD-16/22/24：结构性判据，无文件名单）
  CHECK 15  数据面（rules/*.yaml + rules/schema/*.json）平台名扫描（BDD-15：词边界 + 豁免词典机械生成）

 退出码：0 = 全过；1 = 有 ERROR；2 = 仅有 WARNING（可配置是否失败）。

用法：
  python3 scripts/check-protocol-consistency.py            # 从仓库根运行
  python3 scripts/check-protocol-consistency.py --strict   # WARNING 也判失败
  python3 scripts/check-protocol-consistency.py --json     # 机器可读输出
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Windows 下中文 print 在 cp1252 编码会崩 UnicodeEncodeError——强制 stdout 用 UTF-8
# （Python 3.7+；Linux UTF-8 环境无副作用，CI ubuntu job 行为不变）
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import yaml
except ImportError:
    print("ERROR: 需要 pyyaml。请运行: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# ── 仓库结构定义 ──────────────────────────────────────────────────────────

# 「协议文件」= 主 Agent / subagent 在运行时真正遵循的规范文件。
# 对这些文件做严格检查（行号引用、死链一律 ERROR）。
PROTOCOL_FILES = {
    "agate/WORKFLOW.md",
    "agate/dispatch-protocol.md",
    "agate/state-machine.md",
    "agate/role-system.md",
    "agate/loop-orchestration.md",
    "agate/git-integration.md",
    "agate/platform-notes.md",
    "agate/LIMITATIONS.md",
    "README.md",
    "agate/orchestrator-template.md",
    "agate/SETUP.md",
}
PROTOCOL_DIRS = ("agate/assets/", "agate/phase-cards/", "agate/rules/")  # 角色/模板/阶段卡/状态机规则均属协议文件

# 「叙事文件」= 历史评审 / 计划 / 决策记录。它们经常**引述**别处的旧问题
# （含已修复的行号引用），不应被当作活引用严格检查。仅做 YAML 解析等无害检查。
# 任务产出目录（v2.0 起在工作区 tasks/，即 agate-workspace/tasks/；旧布局 docs/tasks/ 已迁移，
# 保留旧值仅兼容尚未迁移的存量项目）P0-P8 阶段文档含示例引用/归档路径/已修复缺陷的叙事引用，
# 是编排状态而非协议本体——与 docs/plans|reviews 同待遇，宽松检查。
# v0.43.0（TAG0001）：工作区迁移后任务产物位于 {AGATE_WORKSPACE}/tasks/，
# 若此处不豁免，CI（干净 checkout，路径不含 .worktrees）会误扫任务产出触发 CHECK 1/2 误报。
NARRATIVE_DIRS = ("docs/plans/", "docs/reviews/", "docs/design-notes/", "docs/tasks/", "archived/", "agate-workspace/tasks/", "CHANGELOG.md")

# 引用扫描中要忽略的占位 / 示例 / 运行时生成路径（非仓库实文件）。
PATH_IGNORE_SUBSTRINGS = (
    "...",                      # docs/...md 之类省略写法
    "xxx",                      # {role_id}.md 示例
    "{",                        # 含占位符 {Txxx} / {agate_root} / {AGATE_WORKSPACE}
    "agate-workspace/",         # v2.0 工作区运行时目录（tasks/agents/archived/reviews/...）
    "docs/agents/",             # 旧布局项目侧 project.md 位置（v2.0 起迁移到工作区 agents/）
    "docs/converse/",           # 项目侧示例
    "docs/notes/lessons.md",    # 运行时由 P8 生成
    "docs/process/",            # 历史路径示例
    "docs/design/",             # 项目侧设计稿示例
    "docs/decisions/",          # 项目侧决策记录示例
    "tests/",                   # 项目侧测试目录示例
    "backend/", "src/", "app/", # 项目侧源码示例
)

# CHECK 5（协议文件计数声明）已删除：8 文件必读框架不再适用，Phase Card 取代它作为默认入口。
# 历史锚点：
#   - orchestrator-template.md 期望 8 文件列表
#   - state-machine.md 期望 8 文件列表
# 两个锚点都基于"必读清单"假设——这个清单已降级为 reference，不再是协议不变量。

# ── 工具函数 ──────────────────────────────────────────────────────────────

class Report:
    def __init__(self) -> None:
        self.errors: list[dict] = []
        self.warnings: list[dict] = []
        self.passed: list[str] = []

    def error(self, check: str, msg: str, loc: str = "") -> None:
        self.errors.append({"check": check, "msg": msg, "loc": loc})

    def warn(self, check: str, msg: str, loc: str = "") -> None:
        self.warnings.append({"check": check, "msg": msg, "loc": loc})

    def ok(self, check: str) -> None:
        self.passed.append(check)


def _env_skip_dir_prefixes():
    """[SCOPE+] M15（RM-AG0041/BDD-9）opt-in 排除钩子：解析 env
    `AGATE_CONSISTENCY_SKIP_DIRS=<相对根路径列表>`（分隔符 os.pathsep，正斜杠归一），
    返回分量前缀元组（如 "skip-dir" → (("skip-dir",),)）。

    - 默认未设置 / 空值 → () → iter_md_files 行为逐字节不变（R6）。
    - call-time 读取：避免 import 时刻缓存导致后注入的环境变量不生效
      （测试对 import-time / call-time 两种实现均稳健，P3 §5 契约注解 3）。
    - 分隔符 os.pathsep（POSIX ':' / Windows ';'），沿用仓库既有
      `os.environ.get("AGATE_*", 默认)` 解析惯例，无 Unix 路径假设。
    """
    raw = os.environ.get("AGATE_CONSISTENCY_SKIP_DIRS", "")
    out = []
    for entry in raw.split(os.pathsep):
        normalized = entry.strip().replace(os.sep, "/")
        if not normalized:
            continue
        out.append(tuple(normalized.split("/")))
    return tuple(out)


def iter_md_files(root: Path):
    skip_prefixes = _env_skip_dir_prefixes()
    for p in sorted(root.rglob("*.md")):
        # 用相对 root 的路径判断排除项——绝对路径判断在 worktree 开发场景会把
        # worktree 自身（路径含 .worktrees/）的所有文件误排除，导致 consistency 空转
        # （本地 0 ERROR ≠ CI 0 ERROR，TAG0010/0011 实战暴露）
        rel_parts = p.relative_to(root).parts
        if ".git" in rel_parts:
            continue
        if "archived" in rel_parts or ".archived" in rel_parts:
            continue
        if ".worktrees" in rel_parts:
            continue
        if ".opencode" in rel_parts or ".claude" in rel_parts:
            continue
        if "node_modules" in rel_parts:
            continue
        # bats 框架自身（CI 克隆到仓库根的 bats/ 目录，含自带 docs/README 引用非 agate 文件）
        if "bats" in rel_parts:
            continue
        # [SCOPE+] M15（RM-AG0041/BDD-9）：opt-in 排除钩子——env AGATE_CONSISTENCY_SKIP_DIRS
        # 声明的相对根路径按分量前缀命中即跳过，与既有 rel_parts 排除链同层（均相对 root
        # 判定；绝对路径判定在 worktree 场景会误排除含 .worktrees/ 的路径）。分量级匹配
        # 避免 "foo" 误伤 "foobar.md"；默认未设置 → 空元组 → 行为逐字节不变（R6）。
        if any(rel_parts[: len(sp)] == sp for sp in skip_prefixes):
            continue
        yield p


def rel(root: Path, p: Path) -> str:
    # Windows 下 Path.relative_to 返回反斜杠路径，NARRATIVE_DIRS/PROTOCOL_DIRS 白名单
    # （正斜杠）匹配失败 → 统一为正斜杠（Linux 下无变化）
    return str(p.relative_to(root)).replace(os.sep, "/")


def is_protocol_file(relpath: str) -> bool:
    if relpath in PROTOCOL_FILES:
        return True
    return any(relpath.startswith(d) for d in PROTOCOL_DIRS)


def is_narrative_file(relpath: str) -> bool:
    return any(relpath.startswith(d) for d in NARRATIVE_DIRS)


def extract_code_blocks(text: str, lang: str):
    """返回 [(起始行号, 代码内容), ...]，匹配 ```{lang} ... ``` 块。"""
    blocks = []
    pattern = re.compile(rf"```{lang}\n(.*?)\n```", re.S)
    for m in pattern.finditer(text):
        start_line = text[: m.start()].count("\n") + 1
        blocks.append((start_line, m.group(1)))
    return blocks


# ── CHECK 1: YAML 代码块可解析 ────────────────────────────────────────────

def _sanitize_placeholders(code: str) -> str:
    """把 YAML 里的占位符替换成合法标量值，使含占位符的块也能被解析，
    从而仍能抓住缩进/结构错误（占位符本身不是错误，缩进才是）。"""
    # {Txxx} / {agate_root} / {任意中文或英文占位} → 用引号字符串包裹整个值有风险，
    # 改为把裸占位符替换成一个合法 token。仅替换花括号占位，不动其余内容。
    return re.sub(r"\{[^}]*\}", "PLACEHOLDER", code)


def _is_yaml_fragment(code: str) -> bool:
    """判断一个 yaml 块是否是「不该被整体解析的片段」，应跳过。

    跳过条件（任一命中）：
      - 含文档分隔符 --- / ... （是多文档或 frontmatter 片段，非单文档）
      - 全是注释 / 空行（说明性片段）
      - 首个非空非注释行就带缩进（是从某个上层 key 里截出来的子片段，无顶层 key）

    注意：含 {占位符} 不再直接跳过——改为在解析前 sanitize，以便仍能校验缩进。
    """
    lines = code.splitlines()
    for ln in lines:
        if ln.strip() in ("---", "..."):
            return True
    first_effective = None
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        first_effective = ln
        break
    if first_effective is None:
        return True
    return first_effective[:1] in (" ", "\t")


def check_yaml_parseable(root: Path, rep: Report) -> None:
    found_any = False
    bad = 0
    for p in iter_md_files(root):
        relpath = rel(root, p)
        narrative = is_narrative_file(relpath)
        text = p.read_text(encoding="utf-8")
        for start_line, code in extract_code_blocks(text, "yaml"):
            if _is_yaml_fragment(code):
                continue
            found_any = True
            parse_target = _sanitize_placeholders(code)
            try:
                list(yaml.safe_load_all(parse_target))
            except yaml.YAMLError as e:
                first = str(e).splitlines()[0][:100]
                loc = f"{relpath}:{start_line}"
                # 「说明性示例」里的非致命瑕疵（YAML 保留字符 @ ` 作标量首字符等）
                # 降级为 WARNING。但缩进类错误（block mapping/scanning）即使在示例里
                # 也是真结构问题，保持 ERROR。
                indent_err = ("block mapping" in str(e)
                              or "block collection" in str(e)
                              or "mapping values" in str(e))
                illustrative = (("@" in code or "`" in code) or narrative) and not indent_err
                if illustrative:
                    rep.warn("CHECK1-yaml",
                             f"示例 YAML 不严格可解析（建议给含 @/特殊字符的标量加引号）: {first}",
                             loc)
                else:
                    bad += 1
                    rep.error("CHECK1-yaml",
                              f"YAML 代码块无法解析: {first}", loc)
    if found_any and bad == 0:
        rep.ok("CHECK1-yaml")


# ── CHECK 2: 仓库内文件引用真实存在 ──────────────────────────────────────

REF_RE = re.compile(r"(?<![\w/])((?:docs|assets|scripts)/[A-Za-z0-9_./\-]+\.(?:md|sh|ya?ml|py))")

def check_internal_refs(root: Path, rep: Report) -> None:
    broken = 0
    for p in iter_md_files(root):
        relpath = rel(root, p)
        # 叙事文件里的引用经常是引述别处，宽松处理：死链降级为 WARNING
        narrative = is_narrative_file(relpath)
        text = p.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in REF_RE.finditer(line):
                ref = m.group(1)
                if any(s in ref for s in PATH_IGNORE_SUBSTRINGS):
                    continue
                # 跨仓引用：同行注明「非本仓」则跳过
                if "非本仓" in line:
                    continue
                target = root / ref
                # 重构后兼容：协议文件内容引用可在 agate/ 子目录下
                if not target.exists() and not (root / "agate" / ref).exists():
                    loc = f"{relpath}:{lineno}"
                    if narrative:
                        rep.warn("CHECK2-refs",
                                 f"引用的文件不存在（叙事文件，可能是引述旧问题）: {ref}", loc)
                    else:
                        broken += 1
                        rep.error("CHECK2-refs",
                                  f"协议文件引用了不存在的文件: {ref}", loc)
    if broken == 0:
        rep.ok("CHECK2-refs")


# ── CHECK 3: 协议文件中的硬编码行号引用 ──────────────────────────────────

LINEREF_RE = re.compile(r"([A-Za-z0-9_\-]+\.md)\s+L\d+(?:-\d+)?")

def check_line_refs(root: Path, rep: Report) -> None:
    found = 0
    for p in iter_md_files(root):
        relpath = rel(root, p)
        # 只严格检查协议文件；叙事文件（评审/计划）引述行号是正常的
        if not is_protocol_file(relpath):
            continue
        text = p.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in LINEREF_RE.finditer(line):
                found += 1
                rep.error("CHECK3-lineref",
                          f"协议文件含硬编码行号引用 '{m.group(0)}' "
                          f"（应改用节标题引用，见 dispatch-protocol.md「输入导航原则」）",
                          f"{relpath}:{lineno}")
    if found == 0:
        rep.ok("CHECK3-lineref")


# ── CHECK 4: gate_commands 键集合跨文件一致 ──────────────────────────────

def _extract_gate_keys(text: str) -> set[str]:
    """从一个文件中抽出 gate_commands 块下的**直接子键**（P5/P5_e2e/P6...）。

    关键：只收集缩进**深于** gate_commands: 那一行、且是其直接子级的 'KEY:' 行，
    一旦缩进回到 gate_commands 同级或更浅，立即停止——否则会误吞后续的
    minimal_validation / files_to_read 等兄弟字段的子键。
    """
    keys: set[str] = set()
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^(\s*)gate_commands:\s*$", lines[i])
        if not m:
            i += 1
            continue
        base_indent = len(m.group(1))
        child_indent = None
        j = i + 1
        while j < len(lines):
            line = lines[j]
            if not line.strip():           # 空行：跳过但不终止
                j += 1
                continue
            indent = len(line) - len(line.lstrip())
            if indent <= base_indent:       # 回到同级/更浅 → 块结束
                break
            if child_indent is None:
                child_indent = indent       # 锁定直接子级缩进
            if indent == child_indent:      # 只收直接子键
                km = re.match(r"\s*([A-Za-z0-9_]+):", line)
                if km:
                    keys.add(km.group(1))
            j += 1
        i = j
    return keys

def check_gate_commands_keys(root: Path, rep: Report) -> None:
    sources = {
        "agate/assets/execution-roles/architect.md": None,   # 权威来源
        "agate/assets/templates/task-files.md": None,
        "agate/assets/templates/dispatch-prompt.md": None,
    }
    for relpath in list(sources):
        f = root / relpath
        if f.exists():
            sources[relpath] = _extract_gate_keys(f.read_text(encoding="utf-8"))

    present = {k: v for k, v in sources.items() if v}
    if "agate/assets/execution-roles/architect.md" not in present:
        rep.warn("CHECK4-gatekeys", "未找到 architect.md 的 gate_commands，跳过比对")
        return

    authoritative = present["agate/assets/execution-roles/architect.md"]
    mismatched = False
    for relpath, keys in present.items():
        if relpath == "agate/assets/execution-roles/architect.md":
            continue
        missing = authoritative - keys
        # 只对「权威里有、它没有」报警（缺字段才是 P1-2 那类 bug）；额外字段不报
        # P5_e2e 标注「ui_affected 时必填」，模板必须含它
        if missing:
            mismatched = True
            rep.error("CHECK4-gatekeys",
                      f"gate_commands 键集合不一致：{relpath} 缺少 "
                      f"{sorted(missing)}（权威来源 architect.md 含 {sorted(authoritative)}）",
                      relpath)
    if not mismatched:
        rep.ok("CHECK4-gatekeys")


# ── CHECK 6: LICENSE 徽章 + gstack 归属 ──────────────────────────────────

def check_license(root: Path, rep: Report) -> None:
    ok = True
    readme = root / "README.md"
    if readme.exists():
        rtext = readme.read_text(encoding="utf-8")
        # 抓徽章里链接的目标 [...](LICENSE)
        for m in re.finditer(r"\!\[license[^\]]*\]\([^)]*\)\]\(([^)]+)\)", rtext):
            target = m.group(1).strip()
            if target.startswith("http"):
                continue
            if not (root / target).exists():
                ok = False
                rep.error("CHECK6-license",
                          f"README LICENSE 徽章指向不存在的文件: {target}", "README.md")

    lic = root / "LICENSE"
    if not lic.exists():
        ok = False
        rep.error("CHECK6-license", "仓库根目录缺少 LICENSE 文件", "LICENSE")
    else:
        ltext = lic.read_text(encoding="utf-8")
        if "MIT" not in ltext:
            ok = False
            rep.error("CHECK6-license", "LICENSE 未包含 MIT 声明", "LICENSE")
        # gstack 归属检查：LICENSE 保持纯 MIT（GitHub 识别），
        # 概念启发致谢在独立 NOTICES.md（Inspirations 区）
        review_dir = root / "agate" / "assets" / "review-roles"
        uses_gstack = review_dir.exists() and any(
            "gstack" in f.read_text(encoding="utf-8")
            for f in review_dir.glob("*.md")
        )
        notices = root / "NOTICES.md"
        if uses_gstack and not notices.exists():
            ok = False
            rep.error("CHECK6-license",
                      "review-roles 受 gstack(MIT) 概念启发，但 NOTICES.md 不存在（致谢须保留）",
                      "NOTICES.md")
        if uses_gstack and notices.exists() and "gstack" not in notices.read_text(encoding="utf-8"):
            ok = False
            rep.error("CHECK6-license",
                      "NOTICES.md 未保留 gstack(MIT) 概念启发致谢",
                      "NOTICES.md")
    if ok:
        rep.ok("CHECK6-license")


# ── CHECK 7: README version badge 与最新 git tag 一致 ────────────────────────

def check_version_badge(root: Path, rep: Report) -> None:
    readme = root / "README.md"
    if not readme.exists():
        return
    rtext = readme.read_text(encoding="utf-8")
    m = re.search(r"badge/version-v(\d+\.\d+\.\d+)", rtext)
    if not m:
        rep.warn("CHECK7-version", "README.md 未找到 version badge", "README.md")
        return
    badge_ver = m.group(1)
    import subprocess
    try:
        tag = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, check=True, cwd=str(root),
        ).stdout.strip()
        tag_ver = tag.lstrip("v")
    except (subprocess.CalledProcessError, FileNotFoundError):
        rep.warn("CHECK7-version", "无法获取最新 git tag（仓库可能无 tag）", "README.md")
        return
    if badge_ver != tag_ver:
        rep.error("CHECK7-version",
                  f"README version badge v{badge_ver} != 最新 tag v{tag_ver}",
                  "README.md")
    else:
        rep.ok("CHECK7-version")


# ── CHECK 8: v0.6 关键词存在性 ──────────────────────────────────────────────

V06_KEYWORD_ASSERTIONS = [
    ("DESIGN_GAP", "agate/assets/execution-roles/implementer.md", "implementer 角色文件"),
    ("DESIGN_GAP", "agate/assets/execution-roles/architect.md", "architect 角色文件"),
    ("DESIGN_GAP", "agate/scripts/check-gate.py", "P7 gate 脚本"),
    ("P2 不可裁剪", "agate/scripts/check-pruning.py", "裁剪检查脚本"),
    ("P2 不可裁剪", "agate/state-machine.md", "状态机文档"),
    ("model_tier", "agate/assets/templates/task-files.md", "任务文件模板"),
    ("--cached", "agate/scripts/check-gate.py", "P4/P8 gate 脚本"),
    ("--cached", "agate/scripts/check-pruning.py", "裁剪检查脚本"),
]


def check_v06_keywords(root: Path, rep: Report) -> None:
    for keyword, rel_path, description in V06_KEYWORD_ASSERTIONS:
        fpath = root / rel_path
        if not fpath.exists():
            rep.warn("CHECK8-v06", f"{description} ({rel_path}) 不存在", loc=rel_path)
            continue
        text = fpath.read_text(encoding="utf-8")
        if keyword not in text:
            rep.error("CHECK8-v06", f"{description} ({rel_path}) 缺少 v0.6 关键词 '{keyword}'", loc=rel_path)
        else:
            rep.ok("CHECK8-v06")


# ── CHECK 9: 协议-脚本结构对齐 ────────────────────────────────────────────

# 锚点表：文档声明的规则 → 对应脚本应含的关键词。
# 白名单式，只盯死已知锚点。
#
# 局限性：关键词存在 ≠ 语义一致（见 plan §2.4 三类假阳性）。
# 本检查只做结构兜底，语义对齐由 LLM 审查层（protocol-alignment-review）保证。
SCRIPT_ALIGNMENT_ANCHORS = [
    {
        "desc": "P2 不可裁剪（design_trivial / follows_existing_pattern 可简化不可省略）",
        "script": "agate/scripts/check-pruning.py",
        "keywords": ["P2 不可裁剪"],
    },
    {
        "desc": "裁剪 P3 条件（risk_level）",
        "script": "agate/scripts/check-pruning.py",
        "keywords": ["risk_level"],
    },
    {
        "desc": "P6 不可裁剪（no_behavior_change 可简化不可省略）",
        "script": "agate/scripts/check-pruning.py",
        "keywords": ["P6 不可裁剪"],
    },
    {
        "desc": "裁剪 P7 coupling_checklist 声明",
        "script": "agate/scripts/check-pruning.py",
        "keywords": ["coupling_checklist"],
    },
    {
        "desc": "裁剪 P7 条件（源码文件数）",
        "script": "agate/scripts/check-pruning.py",
        "keywords": ["源码文件数"],
    },
    {
        "desc": "裁剪 P8 条件（internal_only）",
        "script": "agate/scripts/check-pruning.py",
        "keywords": ["internal_only"],
    },
    {
        "desc": "重试上限检查（MAX_RETRY）",
        "script": "agate/scripts/check-state-transition.py",
        "keywords": ["MAX_RETRY"],
    },
    {
        "desc": "回退跳变检测",
        "script": "agate/scripts/check-state-transition.py",
        "keywords": ["diff", "phase_num"],
    },
    {
        "desc": "门槛失败事件↔retries 对应性校验（RM-AG0042 BDD-1~4）",
        "script": "agate/scripts/check-state-transition.py",
        "keywords": ["RM-AG0042"],
    },
    {
        "desc": "PROD_TOUCHED 检测",
        "script": "agate/scripts/pre-commit-gate.sh",
        "keywords": ["PROD_TOUCHED", "PROD_NOT_TOUCHED"],
    },
    {
        "desc": "NEED_CONFIRM 三值声明",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["NEED_CONFIRM", "NO_NEED_CONFIRM", "SUGGEST"],
    },
    {
        "desc": "SCOPE+ 追踪",
        "script": "agate/scripts/check-scope-resolved.py",
        "keywords": ["SCOPE_RESOLVED"],
    },
    {
        "desc": "DESIGN_GAP 配对",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["DESIGN_GAP"],
    },
    {
        "desc": "P8 roadmap done 反查（RM-AG0043）",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["_check_roadmap_done"],
    },
    {
        "desc": "P6 evidence UI 检查",
        "script": "agate/scripts/check-p6-evidence.py",
        "keywords": ["ui_affected"],
    },
    {
        "desc": "P6 截图去重（md5）",
        "script": "agate/scripts/check-p6-evidence.py",
        "keywords": ["md5", "去重"],
    },
    {
        "desc": "P6 provenance 审计",
        "script": "agate/scripts/check-p6-provenance.py",
        "keywords": ["EVIDENCE_DIR"],
    },
    {
        "desc": "复盘提醒",
        "script": "agate/scripts/check-retrospective.py",
        "keywords": ["retries"],
    },
    {
        "desc": "P8 CHANGELOG 检查",
        "script": "agate/scripts/check-changelog.py",
        "keywords": ["CHANGELOG"],
    },
    {
        "desc": "state.yaml 格式校验（py 入口）",
        "script": "agate/scripts/check-state-yaml.py",
        "keywords": ["state.yaml"],
    },
    {
        "desc": "state.yaml 格式校验（校验逻辑含 task_id）",
        "script": "agate/scripts/agate-state-yaml-check.py",
        "keywords": ["task_id"],
    },
    {
        "desc": "TDD 红灯检查",
        "script": "agate/scripts/check-tdd-red.py",
        "keywords": ["formatter", "pytest"],
    },
    {
        "desc": "P2 agent=main 硬拦截",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["agent=main"],
    },
    {
        "desc": "P1 review agent≠main 检查",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["P1", "agent=main"],
    },
    {
        "desc": "P7 consistency-reviewer 实质锚点",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["DESIGN_GAP_REVIEWED"],
    },
    {
        "desc": "dispatch-context 派发指引节",
        "script": "agate/dispatch-protocol.md",
        "keywords": ["dispatch-context", "dispatch_guide"],
    },
    {
        "desc": "dispatch-context provenance 审计引用",
        "script": "agate/scripts/check-p6-provenance.py",
        "keywords": ["dispatch-context"],
    },
    {
        "desc": "dispatch-context role frontmatter",
        "script": "agate/assets/templates/dispatch-context.md",
        "keywords": ["role:"],
    },
    {
        "desc": "dispatch-context XML 标记",
        "script": "agate/assets/templates/dispatch-context.md",
        "keywords": ["<dispatch_guide>", "<objective_info>"],
    },
    {
        "desc": "PAUSED 语义翻转（正确路由）",
        "script": "agate/WORKFLOW.md",
        "keywords": ["PAUSED 不是失败", "正确路由"],
    },
    {
        "desc": "PAUSED 语义翻转（dispatch-protocol）",
        "script": "agate/dispatch-protocol.md",
        "keywords": ["正确路由", "非认输"],
    },
    {
        "desc": "P6 格式自动修复",
        "script": "agate/scripts/check-p6-format.py",
        "keywords": ["--fix", "--check"],
        "callers": ["agate/phase-cards/P6-acceptance.md", "agate/dispatch-protocol.md", "agate/scripts/pre-commit-gate.py"],
    },
    {
        "desc": "证据日志 EXIT_CODE 格式约定（文档侧）",
        "script": "agate/assets/templates/dispatch-prompt.md",
        "keywords": ["EXIT_CODE"],
    },
    {
        "desc": "证据日志 EXIT_CODE 一致性检测（脚本侧）",
        "script": "agate/scripts/check-p6-provenance.py",
        "keywords": ["EXIT_CODE"],
    },
    {
        "desc": "CI 平台探测（Gitea/GitLab/GitHub）",
        "script": "agate/scripts/ci-gate-backstop.py",
        "keywords": ["detect_ci_platform", "GITEA_ACTIONS", "GITLAB_CI"],
        "callers": [".github/workflows/protocol-tests.yml"],
    },
    {
        "desc": "pre-push alignment-review 阈值（决定 7：install-hook.sh 保留豁免，单独加锚点）",
        "script": "agate/scripts/pre-push-gate.sh",
        "keywords": ["AGATE_ALIGNMENT_REVIEW_THRESHOLD"],
    },
    {
        "desc": "截图像素方差检测（M3.1）",
        "script": "agate/scripts/check-p6-evidence.py",
        "keywords": ["variance_warning", "AGATE_SKIP_IMAGE_CHECKS"],
    },
    {
        "desc": "截图 average hash 相似度检测（M3.2）",
        "script": "agate/scripts/check-p6-evidence.py",
        "keywords": ["ahash_list", "ahash_dupes"],
    },
    {
        "desc": "P1 BDD 编号格式检查（标准 #### BDD-NN: 格式）",
        "script": "agate/scripts/check-gate.py",
        "keywords": ["BDD-[0-9]"],
    },
    {
        "desc": "frontmatter schema 校验",
        "script": "agate/scripts/check-frontmatter.py",
        "keywords": ["frontmatter"],
        "callers": ["agate/scripts/pre-commit-gate.py"],
    },
    {
        "desc": "tech-debt schema 校验 + 回退覆盖比对（DEBT 条目）",
        "script": "agate/scripts/check-debt.py",
        "keywords": ["debt", "retreat"],
    },
    {
        "desc": "平台假设静态扫描器（TAG0009：Unix 假设检出 + CI 阻断）",
        "script": "agate/scripts/check-platform-assumptions.py",
        "keywords": ["平台假设", "R1", "R2"],
    },
    {
        "desc": "ceremony 路由校验（fail-closed：thin 四要素 + 声明 vs 算分单向，git_ok:false 兜底）",
        "script": "agate/scripts/check-routing.py",
        "keywords": ["ceremony", "git_ok"],
        "callers": ["agate/scripts/pre-commit-gate.py"],
    },
    {
        "desc": "judge verdict 门槛判定（P6.5）",
        "script": "agate/scripts/check-judge-verdict.py",
        "keywords": ["criteria_total", "judge"],
        "callers": ["agate/scripts/check-gate.py", "agate/scripts/pre-commit-gate.py", "agate/scripts/ci-gate-backstop.py"],
    },
    {
        "desc": "事件账本审计（append-only 哈希链）",
        "script": "agate/scripts/check-events.py",
        "keywords": ["prev_hash", "GENESIS"],
        "callers": ["agate/scripts/check-gate.py", "agate/scripts/pre-commit-gate.py", "agate/scripts/ci-gate-backstop.py"],
    },
    {
        "desc": "rules/*.yaml 对 schema 校验（TAG0021 结构化层 M0，S-5 校验器）",
        "script": "agate/scripts/check-yaml-schema.py",
        "keywords": ["draft-07", "rules/schema"],
    },
    {
        "desc": "协议结构一致性 S-1~S-6 双向 gate（TAG0021 结构化层 M0，YAML↔md↔cards↔scripts↔schema↔引用完整性）",
        "script": "agate/scripts/check-structure-consistency.py",
        "keywords": ["S-1", "check-yaml-schema.py"],
    },
    {
        "desc": "维护性反模式检测（RM-AG0046，TAG0026：god-file 跨越 + fuzzy-boundary，P4 三重门槛数据源）",
        "script": "agate/scripts/check-maintainability.py",
        "keywords": ["god_file_count", "fuzzy_boundary_count"],
        "callers": ["agate/scripts/check-gate.py"],
    },
    {
        "desc": "dispatch-routing schema 静态校验（TAG0034 / RM-AG0060：cli/effort 枚举 + tier/candidates 互斥 + fallback 非法）",
        "script": "agate/scripts/check-dispatch-routing.py",
        "keywords": ["VALID_CLI", "VALID_EFFORT", "fallback"],
    },
]


def check_script_alignment(root: Path, rep: Report) -> None:
    for anchor in SCRIPT_ALIGNMENT_ANCHORS:
        script_path = root / anchor["script"]
        if not script_path.exists():
            rep.error("CHECK9-align",
                      f"{anchor['desc']}: 脚本不存在 {anchor['script']}",
                      loc=anchor["script"])
            continue
        text = script_path.read_text(encoding="utf-8")
        for kw in anchor["keywords"]:
            if kw not in text:
                rep.warn("CHECK9-align",
                         f"{anchor['desc']}: 脚本 {anchor['script']} 缺少关键词 '{kw}'"
                         "（可能未实现，或措辞差异——需 LLM 审查确认）",
                         loc=anchor["script"])
            else:
                rep.ok("CHECK9-align")
        callers = anchor.get("callers")
        if callers:
            script_basename = Path(anchor["script"]).name
            found_caller = False
            for caller_path in callers:
                full = root / caller_path
                if full.exists() and script_basename in full.read_text(encoding="utf-8"):
                    found_caller = True
                    break
            if not found_caller:
                rep.warn("CHECK9-callers",
                         f"{anchor['desc']}: 脚本 {anchor['script']} 未被任何流程文件调用"
                         f"（应出现在 {', '.join(callers)} 之一）"
                         "——脚本存在但无调用路径 = 死代码",
                         loc=anchor["script"])
            else:
                rep.ok("CHECK9-callers")


# 工具类脚本白名单——无 gate 逻辑，不需要锚点
GATE_SCRIPT_EXEMPT = {
    "agate/scripts/check-protocol-consistency.py",  # 自身无锚点，但命中 check-*.py glob，必须豁免（否则 CHECK9-coverage WARNING）
    "agate/scripts/pre-commit-gate.py",  # 调度编排脚本，不承载单一 gate 判定逻辑，不需要锚点
}


def check_anchor_coverage(root: Path, rep: Report) -> None:
    """反向检查：每个 gate 脚本（check-*.py + pre-commit-gate.{sh,py} + ci-gate-backstop.py）至少在一条锚点里被引用。

    锚点表本身可能漏——有人加了 check-newrule.py 忘了加锚点，
    正向检查（CHECK 9 主逻辑）只能盯死锚点表里有的，无法发现"该有但没列"。
    本检查做反向兜底：遍历 gate 脚本目录，确认每个都在锚点表里有对应锚点。
    """
    scripts_dir = root / "agate" / "scripts"
    if not scripts_dir.exists():
        return
    gate_scripts = sorted(
        str(p.relative_to(root))
        for p in scripts_dir.glob("check-*.py")
        if p.is_file()
    )
    pre_commit = root / "agate" / "scripts" / "pre-commit-gate.sh"
    if pre_commit.exists():
        gate_scripts.append("agate/scripts/pre-commit-gate.sh")
    pre_commit_py = root / "agate" / "scripts" / "pre-commit-gate.py"
    if pre_commit_py.exists():
        gate_scripts.append("agate/scripts/pre-commit-gate.py")
    ci_backstop = root / "agate" / "scripts" / "ci-gate-backstop.py"
    if ci_backstop.exists():
        gate_scripts.append("agate/scripts/ci-gate-backstop.py")

    covered = {anchor["script"] for anchor in SCRIPT_ALIGNMENT_ANCHORS}
    for script in gate_scripts:
        if script in GATE_SCRIPT_EXEMPT:
            continue
        if script not in covered:
            rep.warn("CHECK9-coverage",
                     f"gate 脚本 {script} 未纳入 CHECK 9 锚点表"
                     "——新增 gate 脚本需在 SCRIPT_ALIGNMENT_ANCHORS 加对应锚点",
                     loc=script)


# ── CHECK 10: 协议文档脚本名引用漂移 ─────────────────────────────────────
# 扫描协议文档面的脚本名引用（裸名 / scripts/ 前缀 / agate/scripts/·~/.agate/scripts/ 全路径），
# 对照 agate/scripts/ 实际文件报"引用了不存在的脚本"漂移。防止脚本改名/退役后协议文档漏检
# （REF_RE 只匹配 docs/assets/scripts 前缀，phase-cards/rules 的裸名引用完全漏检）。
# 白名单形状：check-* / agate-*（连字符与下划线两形，覆盖库文件 agate_common.py）/ 3 hook 薄壳 /
#   install-hook / install-offline / resolve-entry / count-tests.sh / ci-gate-backstop.py。
#   formatters 名（pytest.sh 等）天然不匹配 → 豁免②。

SCRIPT_REF_RE = re.compile(
    r"\b(check-[a-z0-9-]+\.(?:py|sh)|agate-[a-z0-9-]+\.(?:py|sh)|agate_[a-z0-9-]+\.(?:py|sh)|"
    r"install-hook\.(?:py|sh)|install-offline\.(?:py|sh)|resolve-entry\.(?:py|sh)|"
    r"pre-commit-gate\.(?:py|sh)|commit-msg-self-gate\.(?:py|sh)|"
    r"pre-push-gate\.(?:py|sh)|count-tests\.sh|ci-gate-backstop\.py)\b"
)

# 扫描面 = 协议文档面：PROTOCOL_FILES + 根级 README/AGENTS + agate 侧入口文档 + scripts 索引。
# 不含 docs/ 与 agate-workspace/（项目开发资料/任务产出，非协议文件，不扫 = 无 ERROR）。
SCRIPT_REF_SCAN_FILES = PROTOCOL_FILES | {
    "AGENTS.md",
    "agate/AGENTS.md",
    "agate/CONTEXT.md",
    "agate/UPGRADING.md",
    "agate/scripts/README.md",
}
SCRIPT_REF_SCAN_DIRS = PROTOCOL_DIRS  # 复用扩展后的协议目录（assets/ phase-cards/ rules/）

# 豁免③：3 个 hook 薄壳（防未来薄壳改型）；豁免⑤：scripts/README.md 退役名（历史说明）
HOOK_SHELL_NAMES = {"pre-commit-gate.sh", "commit-msg-self-gate.sh", "pre-push-gate.sh"}
SCRIPTS_README_RETIRED_NAMES = {"gate-result.sh", "agate-workspace-resolve.sh", "check-windows-smoke.sh"}


def _iter_script_ref_scan_files(root: Path):
    """CHECK 10 扫描面迭代：显式文件集 + 协议目录 rglob（rel 统一正斜杠）。
    CHANGELOG.md 单独加入作叙事文件（降级为聚合 WARNING，防历史名刷屏）。"""
    seen = set()
    for relpath in sorted(SCRIPT_REF_SCAN_FILES | {"CHANGELOG.md"}):
        if relpath in seen:
            continue
        seen.add(relpath)
        p = root / relpath
        if p.is_file():
            yield relpath, p
    for scan_dir in SCRIPT_REF_SCAN_DIRS:
        d = root / scan_dir
        if not d.is_dir():
            continue
        for p in sorted(d.rglob("*.md")):
            relpath = rel(root, p)
            if relpath in seen:
                continue
            seen.add(relpath)
            yield relpath, p


# ── CHECK 11: UI/UX 机制条文跨文档一致（TAG0006，BDD-1/2/5/6/9/11/12/13/16/17） ──
# UI/UX 验收机制的文档条文是一组跨文件强耦合锚点：analyst 声明分类框架/形态、architect
# 兼任产出 UI 设计节、plan-design-review 审视觉/交互/渲染维度、verifier/P6 卡片分档消费
# 证据（三态 / 输入态复核 / 证据按形态选择）——任一处漂移都会让"文档条文 + gate 脚本 + 单测"
# 三件套失效。本检查按 (文件 → 关键词集合) 白名单式断言条文存在性（0 ERROR）。
# I14（三处形态声明一致）的同类机制：三份文件都须含"渲染形态"锚点，构成协议侧互相印证。
UIUX_DOC_ANCHORS = [
    ("agate/assets/execution-roles/analyst.md",
     ("分类框架", "渲染形态", "渲染正确性", "动效时序", "可量化判据", "手势交互", "特效")),
    ("agate/phase-cards/P1-requirements.md",
     ("分类框架", "渲染形态", "渲染正确性", "动效时序")),
    ("agate/assets/execution-roles/architect.md",
     ("UI 设计", "兼任")),
    ("agate/role-system.md",
     ("UI 设计节由 architect 兼任产出",)),
    ("agate/assets/review-roles/plan-design-review.md",
     ("视觉设计", "交互设计", "渲染正确性与时序")),
    ("agate/assets/templates/dispatch-prompt.md",
     ("视觉能力", "获取指引", "能力自查", "先自查能否调用视觉能力")),
    ("agate/dispatch-protocol.md",
     ("视觉能力",)),
    ("agate/assets/execution-roles/verifier.md",
     ("available", "supplementable", "GAP", "人工复核", "输入态",
      "帧序列", "时序截图", "渲染输出对比", "渲染形态")),
    ("agate/phase-cards/P6-acceptance.md",
     ("真实视觉分析", "人工复核", "输入态", "帧序列", "时序截图", "渲染输出对比", "渲染形态")),
    ("agate/phase-cards/P2-design.md",
     ("UI 设计", "渲染形态")),
]


def check_uiux_doc_anchors(root: Path, rep: Report) -> None:
    errors = 0
    for rel_path, keywords in UIUX_DOC_ANCHORS:
        fpath = root / rel_path
        if not fpath.exists():
            rep.error("CHECK11-uiux", f"UI/UX 条文锚点文件不存在: {rel_path}", loc=rel_path)
            errors += 1
            continue
        text = fpath.read_text(encoding="utf-8")
        for kw in keywords:
            if kw not in text:
                rep.error("CHECK11-uiux",
                          f"{rel_path} 缺少 UI/UX 机制条文锚点 '{kw}'（文档-脚本-单测三件套漂移）",
                          loc=rel_path)
                errors += 1
    if errors == 0:
        rep.ok("CHECK11-uiux")


def check_script_name_refs(root: Path, rep: Report) -> None:
    """CHECK 10：协议文档面脚本名引用漂移检查。豁免①-⑤ + 叙事文件聚合 WARNING。"""
    scripts_dir = root / "agate" / "scripts"
    actual_names = (
        {p.name for p in scripts_dir.iterdir() if p.is_file()} if scripts_dir.is_dir() else set()
    )
    formatters_dir = root / "agate" / "assets" / "formatters"
    formatter_names = (
        {p.name for p in formatters_dir.iterdir() if p.is_file()} if formatters_dir.is_dir() else set()
    )
    count_tests_sh = root / "agate" / "tests" / "scripts" / "count-tests.sh"

    errors = 0
    narrative_warned = set()
    for relpath, p in _iter_script_ref_scan_files(root):
        if relpath == "agate/UPGRADING.md":
            continue  # 豁免①：UPGRADING 整文件（历史迁移文档，对照表行 + 散文行旧名无检查意义）
        text = p.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), 1):
            for m in SCRIPT_REF_RE.finditer(line):
                token = m.group(0)
                if token in actual_names:
                    continue
                if token == "count-tests.sh" and count_tests_sh.exists():
                    continue  # 豁免④：同名不同目录（真实位置 agate/tests/scripts/）
                if token in HOOK_SHELL_NAMES:
                    continue  # 豁免③：hook 薄壳
                if token in formatter_names:
                    continue  # 豁免②：formatters 名（forward-defense——formatter 名天然不匹配白名单，当前不可达）
                if relpath == "agate/scripts/README.md" and token in SCRIPTS_README_RETIRED_NAMES:
                    continue  # 豁免⑤：scripts/README 退役名
                loc = f"{relpath}:{lineno}"
                if is_narrative_file(relpath):
                    if relpath not in narrative_warned:
                        narrative_warned.add(relpath)
                        rep.warn("CHECK10-scriptref",
                                 f"叙事文件含无法解析的脚本名引用（聚合提醒）: {token}", loc)
                else:
                    errors += 1
                    rep.error("CHECK10-scriptref", f"引用了不存在的脚本: {token}", loc)
    if errors == 0 and not narrative_warned:
        rep.ok("CHECK10-scriptref")


# ── CHECK 12: 权威数值/规则跨文件一致性（防复发，BDD-9/10，TAG0016 RM-AG0025）──
# 延续 CHECK 4/9/11 的白名单式提取-比对模式（非文本相似度）：从声明的权威文件里提取
# 具名数值 → 比对指针文件"未重复声明表格 + 含指针短语"、内联值文件"数值与权威表一致"。
# 设计依据：P2-design.md §2（候选 2：结构化权威锚点扫描）。

_RETRY_TABLE_ROW_RE = re.compile(r"\|\s*(P\d+)\s*\|\s*(\d+)\s*\|")

RETRY_LIMIT_HEADING = "## 重试上限"


def extract_section(text: str, heading: str) -> str | None:
    """定位 `heading`（如 "## 重试上限"）标题下的小节正文（到下一个同级 `## ` 标题或文件
    末尾为止），未找到该标题返回 None。

    被 `extract_md_table_int_column`（权威文件取数）与 `check_authoritative_values`
    （指针文件误报防护，P4-review CRITICAL-2 修复）共用同一套小节裁剪逻辑，避免两处实现
    漂移。
    """
    m = re.search(r"^" + re.escape(heading) + r"\s*$", text, re.M)
    if not m:
        return None
    section = text[m.end():]
    next_heading = re.search(r"^## ", section, re.M)
    if next_heading:
        section = section[: next_heading.start()]
    return section


def extract_md_table_int_column(path: Path) -> dict[str, int]:
    """从「## 重试上限」小节的 markdown 表格里提取 {阶段: 数值} 映射。

    只扫描该小节文本，不对整个文件做无范围扫描——避免误吞同格式但语义无关的表格行
    （如任务追踪表里的 "| P4 | 0 | ... |"）。
    """
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    section = extract_section(text, RETRY_LIMIT_HEADING)
    if section is None:
        return {}
    result: dict[str, int] = {}
    for row in _RETRY_TABLE_ROW_RE.finditer(section):
        result[row.group(1)] = int(row.group(2))
    return result


def redeclares_table(text: str, authoritative: dict[str, int]) -> bool:
    """判定文本是否重新声明了权威表格。

    统计文本里能同时匹配权威表 (phase, value) 组合的行数，≥3 组同时命中即判定
    "重新声明了完整表格"（阈值 3 而非"任意 1 组"，容忍正文偶尔提及某一阶段的具体
    数字而不逐条列出全表——见 P2-design.md §2.3 附注）。

    调用方（P4-review CRITICAL-2 修复）须先用 `extract_section` 把待扫描文本裁剪到
    与权威表同名的小节内，再传入本函数——本函数自身不做小节裁剪，只做行匹配计数，
    避免全文无范围扫描误吞同形态但语义无关的表格行（如指针文件里另一张与重试上限
    无关的表格，恰好命中 ≥3 组同值行）。
    """
    hits = 0
    for row in _RETRY_TABLE_ROW_RE.finditer(text):
        phase, value = row.group(1), int(row.group(2))
        if authoritative.get(phase) == value:
            hits += 1
    return hits >= 3


AUTHORITATIVE_VALUE_ANCHORS = [
    {
        "id": "retry-max",
        "desc": "阶段重试上限（MAX_RETRY）",
        "authoritative_file": "agate/state-machine.md",
        "extract_authoritative": extract_md_table_int_column,
        "pointer_files": [
            {
                "file": "agate/rules/state-transitions.md",
                "must_not_redeclare_table": True,
                "must_contain_any": ["权威源", "详见", "见 agate/state-machine.md"],
            },
        ],
        "inline_value_files": [
            {"glob": "agate/phase-cards/P*-*.md", "extract": r"MAX=(\d+)", "phase_from": "filename"},
        ],
    },
]


def check_authoritative_values(root: Path, rep: Report) -> None:
    errors = 0
    for anchor in AUTHORITATIVE_VALUE_ANCHORS:
        authoritative = anchor["extract_authoritative"](root / anchor["authoritative_file"])
        for pf in anchor.get("pointer_files", []):
            fpath = root / pf["file"]
            if not fpath.exists():
                rep.error("CHECK12-authval",
                          f"{pf['file']} 不存在（权威锚点 {anchor['id']} 声明的指针文件缺失）",
                          pf["file"])
                errors += 1
                continue
            text = fpath.read_text(encoding="utf-8")
            # P4-review CRITICAL-2 修复：redeclares_table 只扫描指针文件里与权威表同名的
            # 小节（如「## 重试上限」），不做全文无范围扫描——防止指针文件里另一处与权威
            # 表无关的表格（恰好命中 ≥3 组同值行）被误判为"重新声明了权威表格"。若指针文件
            # 根本没有该级别标题，退化为对全文扫描（与既有行为一致，不引入新的漏报）。
            scan_section = extract_section(text, RETRY_LIMIT_HEADING)
            scan_text = scan_section if scan_section is not None else text
            # INFO-1 修复：must_not_redeclare_table 此前声明但从未被读取（死配置）——
            # 现实际读取该 key（默认 True，向后兼容既有唯一一条 pointer_files 记录）。
            if pf.get("must_not_redeclare_table", True) and redeclares_table(scan_text, authoritative):
                rep.error("CHECK12-authval",
                          f"{pf['file']} 重新声明了权威表格（应改为指向 "
                          f"{anchor['authoritative_file']} 的指针）",
                          pf["file"])
                errors += 1
            elif not any(p in text for p in pf["must_contain_any"]):
                rep.error("CHECK12-authval",
                          f"{pf['file']} 缺少指向权威源 {anchor['authoritative_file']} 的指针短语",
                          pf["file"])
                errors += 1
        for ivf in anchor.get("inline_value_files", []):
            for f in sorted(root.glob(ivf["glob"])):
                pm = re.match(r"(P\d+)-", f.name)
                if not pm:
                    continue
                phase = pm.group(1)
                if phase not in authoritative:
                    continue
                vm = re.search(ivf["extract"], f.read_text(encoding="utf-8"))
                if vm and int(vm.group(1)) != authoritative[phase]:
                    rep.error("CHECK12-authval",
                              f"{f.name} 内联 MAX={vm.group(1)} 与权威表 "
                              f"{phase}={authoritative[phase]} 不一致",
                              f"agate/phase-cards/{f.name}")
                    errors += 1
    if errors == 0:
        rep.ok("CHECK12-authval")


# ── CHECK 13: CHANGELOG 最新版本 ↔ UPGRADING 章节对应性（RM-AG0052） ─────────
# 背景：v0.62.0/v0.63.0 连续两次发布漏写 UPGRADING.md 版本章节（发布清单第 3 步
# 纯人工兜底失效）。只查"最新已发布版本"：历史版本在 §3 本就不全（0.53-0.56 等无章节），
# 全量核对会在存量数据上误报；发布时点的拦截只需盯最新版本。

def check_upgrading_section(root: Path, rep: Report) -> None:
    changelog = root / "CHANGELOG.md"
    upgrading = root / "agate" / "UPGRADING.md"
    if not changelog.exists() or not upgrading.exists():
        return
    ctext = changelog.read_text(encoding="utf-8")
    # 第一个匹配到的已发布版本条目（[Unreleased] 不含三段版本号，自然跳过）
    m = re.search(r"^## \[(\d+\.\d+\.\d+)\]", ctext, re.MULTILINE)
    if not m:
        rep.warn("CHECK13-upgrading",
                 "CHANGELOG.md 未找到已发布版本条目（## [X.Y.Z]），跳过对应性检查",
                 "CHANGELOG.md")
        return
    latest = m.group(1)
    utext = upgrading.read_text(encoding="utf-8")
    if re.search(rf"^### v{re.escape(latest)}\b", utext, re.MULTILINE):
        rep.ok("CHECK13-upgrading")
    else:
        rep.error("CHECK13-upgrading",
                  f"CHANGELOG 最新版本 [{latest}] 在 agate/UPGRADING.md §3 无对应章节"
                  f"（发布清单第 3 步：无破坏性变更也须写'（无破坏性变更）'章节）",
                  "agate/UPGRADING.md")


# ── CHECK 14/15: 护栏 1 机械化（TAG0027 B3b，BDD-15/16/22/24）────────────────
# 背景：编排心智统一文档化（design-orchestration-semantics v3b §4.3 护栏 1）——协议层不发明
# "workflow 模式 / ralph 模式 / goal 模式" 这类以平台工具命名的概念；平台名（OpenCode / Claude
# Code / DSH / workflow / ralph / goal / task）只允许出现在挂「实现注记」标记（`> 实现注记：`
# 标记行）的段落，或平台适配权威源（platform-notes.md/SETUP.md 整文件）等豁免结构里。
# 机械化 = 结构性判据（按标题/空行切段 + 代码围栏跳过），**不维护文件名单**——新增叙述文档
# 自动被覆盖（BDD-24）。
#
# CHECK 14（markdown 叙述段落平台名扫描，P2-design §3.8 定案 D8-A）：
#   扫描面 = 语义叙述面 = agate/ 顶层协议 md（BDD-16 Given `agate/*.md`；BDD-24 新顶层叙述文档
#   自动覆盖）。assets/ 角色/模板、phase-cards、rules 属协议区但**非叙述面**——它们已是固定结构
#   （模板/卡片），不含自由叙述段，B3a 清理时按命中段挂注记处理，不进本扫描（避免固定结构里
#   的字段名/固定动作引用（如 "task 调用" 是平台派发工具的动作描述）被误判为叙述污染）。
#   豁免结构：platform-notes.md / SETUP.md 整文件（平台适配权威源）+ WORKFLOW.md「已知适用
#   环境」表行（节内 | 开头行）+ 段落内带 `> 实现注记：` 标记行。
#   段落判据：标题行（^#{1,6} ）切节 + 空行保持原样（同节内注记覆盖全节——B3a 注记均挂节首）；
#   代码围栏整体跳过；词边界（左右不含字母数字下划线连字符）大小写敏感。
# CHECK 15（数据面平台名扫描，P2-design §3.8 定案 D8-A + §6②）：
#   对象 = rules/*.yaml + rules/schema/*.json（含注释）；词边界大小写敏感；豁免词典机械生成
#   （解析 schema property 名 ∪ 各 yaml 既有键名——task_fields/task_id 等既有键不误报；
#   键定义行豁免 + 词边界双保险，裸平台词仍 ERROR）。

# 平台词表（护栏 1 BDD-15 禁词清单，大小写敏感，契约原文大小写）
PLATFORM_TOKEN_RE = re.compile(
    r"(?<![\w-])(?:OpenCode|Claude Code|DSH|workflow|ralph|goal|task)(?![\w-])"
)

# 整文件豁免（平台适配权威源 / 导航元信息——B3a AGENTS.md 判定记录）
_MD14_WHOLE_FILE_EXEMPT = {
    "agate/platform-notes.md",
    "agate/SETUP.md",
    "agate/AGENTS.md",
    "agate/CONTEXT.md",
}

_NOTE_MARKER_RE = re.compile(r"^>\s*实现注记：")
_HEADING_RE = re.compile(r"^#{1,6}\s")
_FENCE_OPEN_RE = re.compile(r"^```")
_FENCE_CLOSE_RE = re.compile(r"^`{3,}\s*$")


def _split_md_sections(lines: list[str]) -> list[list[tuple[int, str, bool]]]:
    """按标题行切节，返回 [[(lineno, line, in_fence), ...], ...]。

    代码围栏按 CommonMark 语义处理：` ``` ` 开（info string 行不闭）→ ` ``` `（纯围栏行）闭。
    围栏内行标记 in_fence=True（整段跳过，不做平台名扫描）。节边界 = 标题行（^#{1,6} ）；
    空行不切节（同节内注记覆盖整节——B3a 各文件注记挂节首覆盖节内全部命中，BDD-22 注记豁免
    用例的注记行与命中行同属一个 `## 某节`）。
    """
    sections: list[list[tuple[int, str, bool]]] = []
    cur: list[tuple[int, str, bool]] | None = None
    in_fence = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if in_fence:
            if _FENCE_CLOSE_RE.match(stripped):
                in_fence = False
            if cur is not None:
                cur.append((i + 1, line, True))
            continue
        if _FENCE_OPEN_RE.match(stripped):
            in_fence = True
            if cur is not None:
                cur.append((i + 1, line, True))
            continue
        if _HEADING_RE.match(line):
            if cur:
                sections.append(cur)
            cur = [(i + 1, line, False)]
        elif cur is not None:
            cur.append((i + 1, line, False))
    if cur:
        sections.append(cur)
    return sections


def check_md_platform_paragraphs(root: Path, rep: Report) -> None:
    """CHECK 14：agate/ 顶层协议 md 叙述段落平台名扫描（结构性判据，无文件名单）。"""
    md_dir = root / "agate"
    if not md_dir.is_dir():
        return
    errors = 0
    for p in sorted(md_dir.glob("*.md")):
        relpath = rel(root, p)
        if relpath in _MD14_WHOLE_FILE_EXEMPT:
            continue
        text = p.read_text(encoding="utf-8")
        for section in _split_md_sections(text.split("\n")):
            # 节内任一行带 `> 实现注记：` → 整节豁免（段落级判据：命中段有注记即豁免）
            if any(_NOTE_MARKER_RE.match(ln) for _, ln, _ in section):
                continue
            # 「已知适用环境」节内表行豁免（平台适配元信息，WORKFLOW.md 豁免结构）
            env_table = any("已知适用环境" in ln for _, ln, _ in section)
            for lineno, line, in_fence in section:
                if in_fence:
                    continue
                if env_table and line.strip().startswith("|"):
                    continue
                if PLATFORM_TOKEN_RE.search(line):
                    errors += 1
                    rep.error(
                        "CHECK14-platform",
                        "叙述段落含平台名/平台工具名（OpenCode / Claude Code / DSH / "
                        "workflow / ralph / goal / task）但段内无 `> 实现注记：` 标记——"
                        "协议语义叙述面平台名仅限挂实现注记段落出现（护栏 1，BDD-16/22）",
                        f"{relpath}:{lineno}",
                    )
    if errors == 0:
        rep.ok("CHECK14-platform")


def _iter_rules_files(root: Path):
    """CHECK 15 数据面文件：rules/*.yaml + rules/schema/*.json。

    双基路径：真实仓库布局 agate/rules/；测试夹具可能用仓库根 rules/（同 rules 相对树形）。
    """
    for base in (root / "rules", root / "agate" / "rules"):
        if not base.is_dir():
            continue
        for p in sorted(base.glob("*.yaml")):
            yield p
        schema_dir = base / "schema"
        if schema_dir.is_dir():
            for p in sorted(schema_dir.glob("*.json")):
                yield p


def _collect_rule_exempt_tokens(root: Path) -> set[str]:
    """CHECK 15 豁免词典机械生成：解析 schema property 名 + 各 yaml 既有键名。

    目标：task_fields/task_id/task 等**既有键名/字段值**不误报（BDD-15 回归守卫语义）——键名
    本身因词边界（下划线是词字符）天然不命中 task，但豁免词典兜底未来新增的裸键名/字段值引用，
    且避免把 key: task 这类字段定义误判。豁免清单从 schema + rules 解析生成，不手抄
    （P2-design §3.8/§6②：豁免词典从 schema + rules 机械生成，防"新键加入后误报"）。
    """
    exempt: set[str] = set()
    json_key_re = re.compile(r'^\s*"([A-Za-z0-9_]+)"\s*:\s*', re.M)  # JSON property 名
    yaml_key_re = re.compile(r"^\s*([A-Za-z0-9_]+):", re.M)  # YAML 键（顶层/嵌套）
    for p in _iter_rules_files(root):
        text = p.read_text(encoding="utf-8")
        if p.suffix == ".json":
            for m in json_key_re.finditer(text):
                exempt.add(m.group(1))
        else:
            for m in yaml_key_re.finditer(text):
                exempt.add(m.group(1))
    return exempt


def check_rules_platform_tokens(root: Path, rep: Report) -> None:
    """CHECK 15：数据面（rules/*.yaml + rules/schema/*.json）平台名命中数 = 0。

    豁免词典机械生成（schema property 名 ∪ yaml 既有键名）——task_fields/task_id 等既有键
    不误报（词边界 + 键定义行豁免）；裸平台词（注释/字符串值里独立的 task/DSH 等）仍 ERROR。
    """
    exempt = _collect_rule_exempt_tokens(root)
    errors = 0
    checked = 0
    for p in _iter_rules_files(root):
        checked += 1
        text = p.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.split("\n"), 1):
            stripped = line.strip()
            # 键定义行（xxx: / "xxx":）且键名属既有键 → 整行豁免（豁免词典：键定义不误报）
            m = re.match(r'^"([A-Za-z0-9_]+)"\s*:', stripped) or re.match(
                r"^([A-Za-z0-9_]+):", stripped
            )
            if m and m.group(1) in exempt:
                continue
            # 其余行做词边界平台词扫描（含注释/字符串值里的裸平台名）
            for tok_match in PLATFORM_TOKEN_RE.finditer(line):
                tok = tok_match.group(0)
                errors += 1
                rep.error(
                    "CHECK15-rules",
                    f"数据面（rules/schema）出现平台名/平台工具名 '{tok}'——数据面禁平台名"
                    "（护栏 1 BDD-15：平台差异只在 markdown 实现注记段落/豁免源出现）",
                    f"{rel(root, p)}:{lineno}",
                )
    if checked and errors == 0:
        rep.ok("CHECK15-rules")


# ── 主流程 ────────────────────────────────────────────────────────────────

def run_all_checks(root: Path, rep: Report) -> None:
    """按顺序跑所有 CHECK。CHECK 9 拆成两步：先正向锚点对齐，再反向锚点覆盖。"""
    for name, fn in CHECKS:
        fn(root, rep)
        if name.startswith("CHECK 9"):
            check_anchor_coverage(root, rep)


CHECKS = [
    ("CHECK 1  YAML 代码块可解析", check_yaml_parseable),
    ("CHECK 2  仓库内文件引用存在", check_internal_refs),
    ("CHECK 3  协议文件无硬编码行号", check_line_refs),
    ("CHECK 4  gate_commands 键集合一致", check_gate_commands_keys),
    ("CHECK 6  LICENSE 与 gstack 归属", check_license),
    ("CHECK 7  version badge 与 git tag", check_version_badge),
    ("CHECK 8  v0.6 关键词存在性", check_v06_keywords),
    ("CHECK 9  协议-脚本结构对齐", check_script_alignment),
    ("CHECK 10 协议文档脚本名引用漂移", check_script_name_refs),
    ("CHECK 11 UI/UX 机制条文跨文档一致", check_uiux_doc_anchors),
    ("CHECK 12 权威数值/规则跨文件一致性", check_authoritative_values),
    ("CHECK 13 CHANGELOG↔UPGRADING 章节对应", check_upgrading_section),
    ("CHECK 14 md 叙述段落平台名扫描", check_md_platform_paragraphs),
    ("CHECK 15 数据面平台名扫描", check_rules_platform_tokens),
]


def main() -> int:
    ap = argparse.ArgumentParser(description="agate 协议结构一致性检查")
    ap.add_argument("--root", default=".", help="仓库根目录（默认当前目录）")
    strict_group = ap.add_mutually_exclusive_group()
    strict_group.add_argument("--strict", action="store_true", help="WARNING 也判失败")
    strict_group.add_argument(
        "--strict-errors-only",
        action="store_true",
        help="仅 ERROR 判失败，WARNING 不视为失败（与 --strict 互斥）",
    )
    ap.add_argument("--json", action="store_true", help="JSON 输出")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not (root / "agate" / "WORKFLOW.md").exists():
        print(f"ERROR: {root} 看起来不是 agate 仓库根（缺 agate/WORKFLOW.md）", file=sys.stderr)
        return 1

    rep = Report()
    run_all_checks(root, rep)

    if args.json:
        print(json.dumps({
            "passed": rep.passed,
            "warnings": rep.warnings,
            "errors": rep.errors,
        }, ensure_ascii=False, indent=2))
    else:
        print("=" * 64)
        print("  agate 协议结构一致性检查 (P3-1)")
        print("=" * 64)
        for title, _ in CHECKS:
            key = "CHECK" + title.split()[1]
            status = "✅ PASS"
            # report id 形如 CHECK1-yaml / CHECK9-align / CHECK10-scriptref；用 "-" 切分精确匹配，
            # 避免 startswith 前缀碰撞（"CHECK10-scriptref".startswith("CHECK1") 为 True）
            if any(e["check"].split("-")[0] == key for e in rep.errors):
                status = "❌ FAIL"
            elif any(w["check"].split("-")[0] == key for w in rep.warnings):
                status = "⚠️  WARN"
            print(f"  {status}  {title}")
        print("-" * 64)
        if rep.errors:
            print(f"\n  ERROR ({len(rep.errors)}):")
            for e in rep.errors:
                loc = f" [{e['loc']}]" if e["loc"] else ""
                print(f"    ❌ {e['msg']}{loc}")
        if rep.warnings:
            print(f"\n  WARNING ({len(rep.warnings)}):")
            for w in rep.warnings:
                loc = f" [{w['loc']}]" if w["loc"] else ""
                print(f"    ⚠️  {w['msg']}{loc}")
        print()
        if not rep.errors and not rep.warnings:
            print("  🎉 全部检查通过，协议结构一致性无问题。")
        elif not rep.errors:
            print(f"  仅有 {len(rep.warnings)} 个 WARNING，无 ERROR。")
        print()

    if rep.errors:
        return 1
    if args.strict_errors_only:
        return 0
    if rep.warnings and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
