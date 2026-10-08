#!/usr/bin/env python3
"""check-frontmatter.py FILE — frontmatter schema 校验（P1/P2/P6/P7，v2.0 T001 流 A）

从 check-frontmatter.sh 迁移（TAG0010 批次 1a）。CLI 契约与 sh 版等价：
exit 0 = 格式正确（含非目标文件 / 旧格式无 frontmatter）; exit 1 = 格式错误。
"""

import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import agate_common  # noqa: E402

# 非 legacy 任务的「声明文件」：缺 frontmatter 一律 ERROR（TAG0050 批 B，修复 F10，BDD-47）。
# 实际集合 = 契约快照的 `declaration_files` 键（R2：与设计 §3.6 / 快照同源）；
# 仅当快照不可用（安装破损）时退回历史四类文件作降级。
_FALLBACK_DECLARATION_FILES = frozenset({
    "P1-requirements.md", "P2-design.md", "P6-acceptance.md", "P7-consistency.md",
})


def _declaration_files(task_dir=None):
    """声明文件集合：快照 `declaration_files`（L1 整改：按**任务等级**，回退协议当前等级，
    与 `pre-commit-gate._declaration_files(task_dir)` 同口径）；快照不可用 → 历史四类（安装破损降级）。
    """
    try:
        level = None
        if task_dir is not None:
            level = agate_common.task_level(task_dir, __file__)
        if level is None:
            level = agate_common.current_level(__file__)
        contract = agate_common.load_contract(level, __file__) if level else {}
        decl = contract.get("declaration_files") if isinstance(contract, dict) else None
        if isinstance(decl, (list, tuple)) and decl:
            return frozenset(str(x) for x in decl)
    except Exception:
        pass
    return _FALLBACK_DECLARATION_FILES


def _task_is_non_legacy(file_path):
    """文件所在任务目录是否非 legacy（账本有创建/迁入事件）。

    文件不在任务目录下（如测试用裸 tmp 目录）→ False，走旧兼容路径。
    """
    try:
        task_dir = os.path.dirname(os.path.abspath(file_path))
        return agate_common.task_level(task_dir, __file__) is not None
    except Exception:
        return False


def _has_frontmatter(text):
    return text.startswith("---\n") and "\n---" in text[4:]


def _run_check(file_path):
    """调 agate-frontmatter-check.py（env FILE 传参，subprocess + sys.executable）。

    返回 (returncode, stdout, stderr)。用 env 传参避免 shell 变量注入 Python 代码
    （同 check-state-yaml.py 惯例）。
    """
    env = dict(os.environ)
    env["FILE"] = file_path
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "agate-frontmatter-check.py")],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return 1, "", ""
    return proc.returncode, proc.stdout or "", proc.stderr or ""


def main():
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("用法: check-frontmatter.py FILE\n")
        sys.exit(1)
    file_path = args[0]

    if not os.path.isfile(file_path):
        sys.stderr.write(f"GATE SKIP: check-frontmatter: 目标文件不存在（{file_path}），未校验\n")
        sys.exit(0)

    py_exit, errors, py_stderr = _run_check(file_path)

    # P4-review.md CRITICAL fix B（纵深防御）：python 非零退出 = 校验器自己崩了 →
    # fail-closed，exit 1，并把 stderr 打印出来方便排查（不再把"校验器崩溃"误判成 exit 0）。
    if py_exit != 0:
        sys.stderr.write(
            f"GATE FRONTMATTER: {file_path} frontmatter 校验器异常退出（exit {py_exit}），fail-closed 拦截：\n"
        )
        sys.stderr.write(py_stderr)
        sys.exit(1)

    # 非 legacy 任务的声明文件缺 frontmatter → ERROR（TAG0050 批 B，修复 F10；不回退正文正则）。
    # TAG0050 G2 闭合（GAP-2）：本项在 hook 路径同样生效（不再经 AGATE_PRECOMMIT_GATE 跳过）；
    # 既有 pre_commit_hook 夹具已随新契约补 frontmatter（契约驱动的夹具演进）。
    if not errors:
        basename = os.path.basename(file_path)
        task_dir = os.path.dirname(os.path.abspath(file_path))
        if basename in _declaration_files(task_dir) and _task_is_non_legacy(file_path):
            try:
                with open(file_path, encoding="utf-8") as fh:
                    text = fh.read().replace("\r\n", "\n")
            except OSError:
                text = ""
            if not _has_frontmatter(text):
                errors = (
                    f"{basename}: 非 legacy 任务的声明文件缺 frontmatter 块——"
                    f"请补 `---` 块后用 agate-md-field-set.py 写入字段（不回退正文正则）"
                )

    if errors:
        sys.stderr.write(f"GATE FRONTMATTER: {file_path} frontmatter 格式错误：\n")
        for line in errors.splitlines():
            if line:
                sys.stderr.write(f"  - {line}\n")
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
