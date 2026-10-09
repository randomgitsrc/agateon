#!/usr/bin/env python3
"""check-maintainability.py — 维护性反模式检测器（RM-AG0046，TAG0026）。

god-file 跨越 + fuzzy-boundary 两类 G0 反模式检测，diff 驱动（git diff --cached），
只在代码 staged 时判定有意义（挂载在 P4，BDD-13——P6 挂载即死代码）。

契约（P2-design.md §3.1）：
    check_maintainability(task_dir) -> dict，四键严格：
        {"git_ok": bool, "violations": [...], "god_file_count": N, "fuzzy_boundary_count": M}
    violation 条目：
        god-file       → {"type": "god-file", "file": <norm_rel>, "detail": "before=.. after=.. threshold=.."}
        fuzzy-boundary → {"type": "fuzzy-boundary", "file": <norm_rel>, "line": N, "detail": "matched pattern: .."}
    git_ok 语义对齐 agate-risk-score.score_task：git 通道不可用 → git_ok=False（fail-closed，不静默降级）。
    配置：{repo_root}/agate-workspace/maintainability.yaml（god_file_threshold / fuzzy_patterns），
    缺失 / yaml 不可导入 / 单键缺失 / 单键类型坏 → 该键用默认值，不抛错不静默跳过（BDD-6）。
    CLI：python3 check-maintainability.py TASK_DIR
        exit 0 = 无 violation（或 git 通道不可用，WARNING 语义）；exit 1 = 有 violation。
        判定唯一依据 exit code（P6 复跑自查可读输出）。

阈值 N=1000 无实证依据（来自 Cursor skill 经验值），默认值仅供参考可配置——
配置缺失时使用默认值不构成"协议断言该阈值"。

移动代码假阳性（BDD-12）：纯 diff 层面"删除行 + 新增行"中的新增行照判 violation——
已知行为非 bug，靠 known-violations 登记吸收，不引入跨行移动检测。

**「设计强制改动越阈」的既定出口（RM-AG0106 / DEBT0056）**：当越阈是**设计要求**（如协议 §3.1
强制在既有大文件上新增逻辑）而非实现自选时，**既定出口 = `known-violations.md` 登记 + 评审确认**——
逐条写明「文件 / before / after / 阈值 / **理由**」，经评审确认后长期留存。
⚠️ **准确口径**：该出口是「**机械可查的登记/计数路径 + 人工评审确认**」——机械面只到
「`known-violations.md` 文件存在 + 条目数 ≥ violation 数」（`gate_p4`），**不判**「是否设计强制」
（那是**评审**的判断）。本脚本**不**为此引入机械豁免：无法从 diff 区分「设计强制」与「实现自选」，
self-declaration 会被滥用（ADR-015 门禁只用于实质错误）。
fuzzy 正则集只覆盖 Python/TS；其它扩展名只做 god-file 行数判定，不做 fuzzy（P0 out-of-scope）。
"""

import importlib.util
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

# 复用链单源（P2-design §2.1 候选 A）：agate_common 原语 + agate-risk-score 的 _norm_rel。
# ImportError 降级兜底（先例 check-gate.py:32-41 / agate-risk-score.py:57-59）。
try:
    from agate_common import count_kf_entries, run_git
except ImportError:  # pragma: no cover - 仅独立部署缺库时触发
    count_kf_entries = None
    run_git = None


def _load_script(name, module_name=None):
    """importlib 加载同目录脚本（带连字符模块名无法直接 import，agate-risk-score.py:46-54 同源）。"""
    path = os.path.join(SCRIPT_DIR, name + ".py")
    spec = importlib.util.spec_from_file_location(
        module_name or name.replace("-", "_"), path
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


try:
    _norm_rel = _load_script("agate-risk-score")._norm_rel
except Exception:
    def _norm_rel(path):
        """repo 相对路径统一 / 分隔（Windows 反斜杠归一，BDD-11；单源在 agate-risk-score）。"""
        return path.replace("\\", "/")


# ---------- 默认值（协议参考实现，配置可覆盖；BDD-6 全兜底） ----------

DEFAULT_GOD_FILE_THRESHOLD = 1000
DEFAULT_FUZZY_PATTERNS = {
    "python": [r"^\s*except\s*:", r"#\s*type:\s*ignore"],
    "typescript": [r":\s*any\b", r"\bas\s+any\b"],
}

# 按扩展名路由 fuzzy 正则组（P2-design §3.1）；其它扩展名不做 fuzzy 只做 god-file。
_FUZZY_LANG_BY_EXT = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "typescript",
    ".jsx": "typescript",
}

# god-file 判定只看 .py/.ts/.tsx/.js/.jsx（检测器按扩展名路由，md/state 等天然不参与）。
_GOD_FILE_EXTS = set(_FUZZY_LANG_BY_EXT)

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def _load_config(repo_root):
    """读 {repo_root}/agate-workspace/maintainability.yaml，全兜底（BDD-6）。

    文件不存在 → 全默认值；yaml 不可导入 → 全默认值 + stderr 提示；
    单键缺失 / 类型坏 → 该键默认值。任何配置问题不报错、不静默跳过。
    返回 (threshold:int, patterns:{"python": [...], "typescript": [...]})。
    """
    threshold = DEFAULT_GOD_FILE_THRESHOLD
    patterns = {lang: list(rules) for lang, rules in DEFAULT_FUZZY_PATTERNS.items()}

    try:
        import yaml  # 延迟导入，缺失时走默认值
    except ImportError:
        sys.stderr.write(
            "check-maintainability WARNING: pyyaml 不可导入，维护性检测配置使用默认值\n"
        )
        return threshold, patterns

    config_path = os.path.join(
        repo_root, "agate-workspace", "maintainability.yaml"
    )
    if not os.path.isfile(config_path):
        return threshold, patterns

    try:
        with open(config_path, encoding="utf-8", errors="replace") as f:
            cfg = yaml.safe_load(f)
    except Exception:
        sys.stderr.write(
            f"check-maintainability WARNING: 配置文件解析失败，使用默认值: {config_path}\n"
        )
        return threshold, patterns

    if not isinstance(cfg, dict):
        return threshold, patterns

    raw_threshold = cfg.get("god_file_threshold")
    if isinstance(raw_threshold, int) and not isinstance(raw_threshold, bool) and raw_threshold > 0:
        threshold = raw_threshold
    elif raw_threshold is not None:
        sys.stderr.write(
            "check-maintainability WARNING: god_file_threshold 类型坏（期望正整数），"
            f"使用默认值 {DEFAULT_GOD_FILE_THRESHOLD}\n"
        )

    raw_patterns = cfg.get("fuzzy_patterns")
    if isinstance(raw_patterns, dict):
        for lang in ("python", "typescript"):
            rules = raw_patterns.get(lang)
            if isinstance(rules, list) and all(isinstance(r, str) for r in rules):
                patterns[lang] = rules
            elif rules is not None:
                sys.stderr.write(
                    f"check-maintainability WARNING: fuzzy_patterns.{lang} 类型坏（期望字符串列表），使用默认值\n"
                )
    elif raw_patterns is not None:
        sys.stderr.write(
            "check-maintainability WARNING: fuzzy_patterns 类型坏（期望 dict），使用默认值\n"
        )

    return threshold, patterns


def _count_lines(text):
    """文本行数（与 wc -l 对齐：以换行符个数计；空文本 = 0）。"""
    if not text:
        return 0
    return text.count("\n")


def _god_file_check(repo_root, staged_files, threshold):
    """god-file 跨越检测：before < N and after >= N（跨越阈值线才报，存量不误伤，BDD-2）。

    before = `git show HEAD:{path}` 行数（新增文件 / HEAD 不存在 → 0）；
    after = `git show :{path}` 行数（staged 版本，与"判定本次 commit"自洽）。
    所有 git 调用统一 cwd=repo_root（rev:path 的 path 按仓库根解析，diff pathspec
    按 cwd 相对解析——anchor 到仓库根才能正确命中 task_dir 为子目录的场景）。
    """
    violations = []
    for rel in staged_files:
        ext = os.path.splitext(rel)[1].lower()
        if ext not in _GOD_FILE_EXTS:
            continue
        rc, head_text = run_git(["show", "HEAD:" + rel], cwd=repo_root)
        before = _count_lines(head_text) if rc == 0 else 0
        rc, staged_text = run_git(["show", ":" + rel], cwd=repo_root)
        if rc != 0:
            # staged 版本读不到（异常状态）→ 该文件跳过行数判定
            continue
        after = _count_lines(staged_text)
        if before < threshold <= after:
            violations.append(
                {
                    "type": "god-file",
                    "file": _norm_rel(rel),
                    "detail": f"before={before} after={after} threshold={threshold}",
                }
            )
    return violations


def _fuzzy_boundary_check(repo_root, rel, patterns):
    """fuzzy-boundary 检测：`git diff --cached -U0 -- {path}` 新增行逐行匹配正则组。

    只取 '+' 前缀且非 '+++' 行；行号取 @@ -a,b +c,d @@ 的 c 列（新文件行号）。
    cwd=repo_root：diff 的 pathspec 按 cwd 相对解析（git 子目录语义实证），
    task_dir 为仓库子目录时 pathspec 会解析不到——统一锚定仓库根。
    """
    violations = []
    rc, diff_text = run_git(["diff", "--cached", "-U0", "--", rel], cwd=repo_root)
    if rc != 0:
        return violations
    cur_line = None
    for raw in diff_text.splitlines():
        line = raw.rstrip("\r")
        if line.startswith("@@"):
            m = _HUNK_HEADER_RE.match(line)
            cur_line = int(m.group(1)) if m else None
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if not line.startswith("+"):
            continue
        content = line[1:]
        matched = None
        for pattern in patterns:
            try:
                if re.search(pattern, content):
                    matched = pattern
                    break
            except re.error:
                # 配置中的坏正则跳过该 pattern（配置兜底原则：不抛错）
                continue
        if matched is not None and cur_line is not None:
            violations.append(
                {
                    "type": "fuzzy-boundary",
                    "file": _norm_rel(rel),
                    "line": cur_line,
                    "detail": f"matched pattern: {matched}",
                }
            )
        if cur_line is not None:
            cur_line += 1
    return violations


def check_maintainability(task_dir):
    """维护性反模式检测主入口（契约见模块 docstring）。"""
    if run_git is None:
        return {"git_ok": False, "violations": [], "god_file_count": 0, "fuzzy_boundary_count": 0}

    rc, out = run_git(["rev-parse", "--show-toplevel"], cwd=task_dir)
    if rc != 0:
        return {"git_ok": False, "violations": [], "god_file_count": 0, "fuzzy_boundary_count": 0}
    repo_root = out.rstrip("\r\n").strip()
    if not repo_root:
        return {"git_ok": False, "violations": [], "god_file_count": 0, "fuzzy_boundary_count": 0}

    rc, out = run_git(["diff", "--cached", "--name-status"], cwd=task_dir)
    if rc != 0:
        return {"git_ok": False, "violations": [], "god_file_count": 0, "fuzzy_boundary_count": 0}
    # 只处理 A/M，跳过 D（删除文件无 after 行数、无新增行；R3）
    staged_files = []
    for raw in out.splitlines():
        line = raw.rstrip("\r")
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2 and parts[0].strip() in ("A", "M"):
            staged_files.append(parts[1].strip())

    threshold, patterns = _load_config(repo_root)

    violations = []
    violations.extend(_god_file_check(repo_root, staged_files, threshold))
    for rel in staged_files:
        ext = os.path.splitext(rel)[1].lower()
        lang = _FUZZY_LANG_BY_EXT.get(ext)
        if lang is None:
            continue
        violations.extend(_fuzzy_boundary_check(repo_root, rel, patterns.get(lang, [])))

    return {
        "git_ok": True,
        "violations": violations,
        "god_file_count": sum(1 for v in violations if v["type"] == "god-file"),
        "fuzzy_boundary_count": sum(1 for v in violations if v["type"] == "fuzzy-boundary"),
    }


def main():
    """CLI 薄壳：打印 violations 摘要（P6 复跑自查可读），exit code 唯一判定。"""
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-maintainability.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]
    result = check_maintainability(task_dir)
    if not result["git_ok"]:
        sys.stderr.write("check-maintainability WARNING: git 通道不可用，本轮跳过维护性检测\n")
        sys.exit(0)
    god_files = [v for v in result["violations"] if v["type"] == "god-file"]
    fuzzy = [v for v in result["violations"] if v["type"] == "fuzzy-boundary"]
    print(f"god_file_count: {result['god_file_count']}")
    print(f"fuzzy_boundary_count: {result['fuzzy_boundary_count']}")
    for v in god_files:
        print(f"god-file: {v['file']} ({v['detail']})")
    for v in fuzzy:
        print(f"fuzzy-boundary: {v['file']}:{v['line']} ({v['detail']})")
    if result["violations"]:
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
