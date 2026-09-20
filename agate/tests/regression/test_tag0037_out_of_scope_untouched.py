# tests/regression/test_tag0037_out_of_scope_untouched.py — TAG0037 P3 组 C：out-of-scope 文件零 diff（BDD-46，负向）
#
# BDD-46：本任务全部提交不得改动 hook 三件套（pre-commit-gate / commit-msg-self-gate / pre-push-gate 的 .sh 与 .py）、
# SELF-GATE 机制（SELF-GATE.md、commit-msg-self-gate.py 的 _SELF_GATE_RE）、.state.yaml schema 校验脚本、agate/rules/ 权威源、
# install-hook.py；resolve-entry.py 与 agate_common.resolve_hook_root 仅允许改注释 / docstring / 删除 legacy 实参（函数语义不变）。
# 验收命令（人工口径，等价）：`git diff 75a8102..HEAD -- <上述文件>` 为空。
#
# 为什么不直接断言 `git diff 75a8102..HEAD`（永久回归 vs 一次性交付事实，TAG0025 教训）：
#   "这些文件相对本任务基线无 diff"是一次性交付事实——任务合并之后别的任务合法修改 hook 会使其假性变红。
#   故本测试断言**不可变历史证据**：区间 75a8102..HEAD 内**主题含 TAG0037 的非合并提交**（= 本任务自己的提交）逐个 diff-tree，
#   不得触及受保护路径（resolve-entry.py / resolve_hook_root 例外见上，用 AST 归一化比较：去 docstring 与 legacy 实参后必须相同）。
#   本任务的提交集合在历史中固定，别的任务之后再改这些文件不会影响本用例。
# 当前（P4 前）本用例即应绿——它是"不许碰"的负向约束，无法在实现前红灯（有意应绿）；P4 若误触受保护文件则转红。
# 依赖：完整 git 历史（CI 已 fetch-depth: 0）；基线提交不可达时明确失败（不静默跳过）。
# 只读：仅 git log / diff-tree / show。

import ast
import re
import subprocess

import pytest

import helpers_tag_repo as H

BASE = "75a8102"
ROOT = H.REPO_ROOT

# 严格零 diff：文件路径（精确）
STRICT_FILES = (
    "agate/scripts/pre-commit-gate.sh",
    "agate/scripts/pre-commit-gate.py",
    "agate/scripts/commit-msg-self-gate.sh",
    "agate/scripts/commit-msg-self-gate.py",
    "agate/scripts/pre-push-gate.sh",
    "agate/scripts/pre-push-gate.py",
    "SELF-GATE.md",
    "agate/scripts/install-hook.py",
    "agate/scripts/check-state-yaml.py",
    "agate/scripts/agate-state-yaml-check.py",
)
# 严格零 diff：目录前缀（agate/rules/*.yaml 权威源 + schema）
STRICT_PREFIXES = ("agate/rules/",)
# 语义不变即可：注释 / docstring 可改
SEMANTIC_FILE = "agate/scripts/resolve-entry.py"
SEMANTIC_FUNC = ("agate/scripts/agate_common.py", "resolve_hook_root")

_LEGACY_KW = "use_" + "legacy"


def _git(*args, check=True):
    proc = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, timeout=180)
    if check and proc.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} 失败: {proc.stderr.decode('utf-8', 'replace')}")
    return proc


def _norm_source(src):
    """整文件 AST 归一化：去 docstring（模块 / 类 / 函数）与 legacy 关键字实参；忽略注释与空白。"""
    return ast.dump(_strip(ast.parse(src)), include_attributes=False)


def _norm_func(src, name):
    tree = _strip(ast.parse(src))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.dump(node, include_attributes=False)
    raise AssertionError(f"函数 {name} 不存在")


def _strip(tree):
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
                node.body = body[1:] or [ast.Pass()]
        if isinstance(node, ast.Call):
            node.keywords = [kw for kw in node.keywords if kw.arg != _LEGACY_KW]
    return tree


@pytest.fixture(scope="module")
def task_commits():
    """区间 BASE..HEAD 内主题含 TAG0037 的非合并提交（本任务自己的提交；不可变历史证据）。"""
    assert _git("cat-file", "-e", f"{BASE}^{{commit}}", check=False).returncode == 0, (
        f"基线提交 {BASE} 不可达（CI 需 fetch-depth: 0）"
    )
    out = _git("log", "--no-merges", "--format=%H%x00%s", f"{BASE}..HEAD").stdout.decode("utf-8", "replace")
    commits = []
    for line in out.splitlines():
        sha, _sep, subject = line.partition("\0")
        if re.search(r"TAG0037", subject):
            commits.append((sha, subject))
    return commits


def _changed(sha):
    out = _git("diff-tree", "--no-commit-id", "--name-only", "-r", "-z", sha).stdout.decode("utf-8", "surrogateescape")
    return [p for p in out.split("\0") if p]


def _show(rev, path):
    proc = _git("show", f"{rev}:{path}", check=False)
    return proc.stdout.decode("utf-8") if proc.returncode == 0 else None


def test_bdd_46_task_commits_do_not_touch_out_of_scope_files(task_commits):
    """BDD-46：本任务提交不得触及 hook 三件套 / SELF-GATE / install-hook.py / .state.yaml schema 脚本 / agate/rules/。"""
    offenders = []
    for sha, subject in task_commits:
        for path in _changed(sha):
            if path in STRICT_FILES or path.startswith(STRICT_PREFIXES):
                offenders.append((sha[:8], subject[:60], path))
    assert offenders == [], f"out-of-scope 文件被本任务提交修改: {offenders}"


def test_bdd_46_resolve_entry_semantics_unchanged_ignoring_comments_and_docstrings(task_commits):
    """BDD-46 例外：resolve-entry.py 只允许改注释 / docstring（gate 映射与 exec 语义不变，AST 归一化后相同）。"""
    for sha, subject in task_commits:
        if SEMANTIC_FILE not in _changed(sha):
            continue
        old, new = _show(f"{sha}^", SEMANTIC_FILE), _show(sha, SEMANTIC_FILE)
        assert old is not None and new is not None, f"{sha[:8]} 新增 / 删除了 {SEMANTIC_FILE}"
        assert _norm_source(old) == _norm_source(new), f"{sha[:8]} ({subject[:50]}) 改变了 resolve-entry.py 的语义（不只是注释 / docstring）"


def test_bdd_46_resolve_hook_root_only_docstring_and_legacy_kwarg_may_change(task_commits):
    """BDD-46 / BDD-47：agate_common.resolve_hook_root 仅允许改 docstring 与删除 legacy 实参（脚本路径上溯 + .agate-root 恢复兜底不变）。"""
    path, func = SEMANTIC_FUNC
    for sha, subject in task_commits:
        if path not in _changed(sha):
            continue
        old, new = _show(f"{sha}^", path), _show(sha, path)
        assert old is not None and new is not None
        assert _norm_func(old, func) == _norm_func(new, func), f"{sha[:8]} ({subject[:50]}) 改变了 {func} 的语义"


# ---------------------------------------------------------------------------
# 归一化助手自守卫（有意应绿：锁定"注释 / docstring / legacy 实参可改，语义改动必被发现"）
# ---------------------------------------------------------------------------


def test_bdd_46_norm_helpers_ignore_comments_docstrings_and_kwarg_but_catch_semantic_changes():
    base = f'def f(x):\n    """doc"""\n    # note\n    return g(x, {_LEGACY_KW}=False)\n'
    same = 'def f(x):\n    """另一段 docstring"""\n    return g(x)\n'
    changed = 'def f(x):\n    """doc"""\n    return g(x, 1)\n'
    assert _norm_func(base, "f") == _norm_func(same, "f")
    assert _norm_source(base) == _norm_source(same)
    assert _norm_func(base, "f") != _norm_func(changed, "f")
    with pytest.raises(AssertionError):
        _norm_func(base, "missing")
