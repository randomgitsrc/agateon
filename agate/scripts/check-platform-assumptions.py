#!/usr/bin/env python3
"""check-platform-assumptions.py — 平台假设静态扫描器（TAG0009 BDD-1~9）

从 check-platform-assumptions.sh 迁移（TAG0010 Python 化）。扫描测试代码
（agate/tests/ 全树）中的 Unix 平台假设，CI 接入阻断新假设。逐行扫描（不依赖
grep/find 子进程），仅用 Python 标准库，Linux 与 MSYS2 双平台行为一致（BDD-1）。

相较 bash 版的三处变更：
  * 扩展名过滤新增 *.py（tests/ 下 Python 测试同受监管）
  * R2 新增 docstring 豁免（BLOCKER-1 决策：docstring 是文档非可执行代码，
    与 # 注释同类豁免）
  * R4 补上 bash 版头注释声明但扫描逻辑未实现的 BATS_TEST_TMPDIR 豁免

用法：check-platform-assumptions.py [target...]
  target 为文件或目录；目录 target 递归扫描 *.bats / *.bash / *.sh / *.py
  无参数时默认扫描 agate/tests/

规则（行级豁免见 _r2_comment_exempt / _docstring_state / _r4_exempt）：
  R1 硬编码 PATH（/usr 或 /bin 字面赋值）
  R2 命令位置裸 python3（豁免 command -v 探测 / env 形式 / shebang / @test 标题 /
     注释行 / docstring 块）
  R3 方括号形式 -L 单平台 symlink 断言（[[ -L ... ]] 或 [ -L ... ]）
  R4 临时目录字面量（豁免 BATS_TEST_TMPDIR 变量行与含 "# scan-exempt:" 标记的行）
  R5 命令位置裸外部工具（bc 已登记；模式集可扩充 seq/timeout 等）

输出：命中行形如 `R{n} <file>:<line> <text>`（stderr）；无命中无输出
退出：0 = 无命中；1 = 有命中；2 = 目标不存在
"""

import os
import re
import sys
from pathlib import Path

# (规则号, 编译正则, 行级豁免类型)。Python re 对应 sh POSIX ERE；R5 按 sh
# 语义近似翻译（尾随 alternation 保留 [空白 | 行尾 | 管道]）。
_RULES = (
    ("R1", re.compile(r"PATH=\S*(/usr|/bin)"), None),
    ("R2", re.compile(r"(^|[\s=(\'\"])python3([\s]|$)"), "r2"),
    ("R3", re.compile(r"(^|[\s])\[\[?[\s]+-L[\s]"), None),
    ("R4", re.compile(r"/tmp([\s/\"']|$)"), "r4"),
    ("R5", re.compile(r"(^|[\s=|(])bc([\s]|$|[|])"), None),
    # R6（RM-AG0105 / DEBT0058）是**调用级**检查，不在此行级规则表内——见
    # `_r6_text_without_encoding_hits()`（文本模式与 `encoding=` 常**分行**书写，
    # 行级判定会大面积误报：实测本仓多数调用分行）。
)


def _r6_text_without_encoding_hits(text):
    """R6（RM-AG0105 / DEBT0058）：`subprocess.*` 调用用了**文本模式**
    （`text=True` / `universal_newlines=True`）却**未在整次调用内**出现 `encoding=` → 命中行号。

    **调用级**（非行级）：文本模式与 `encoding=` 常**分行**书写，行级判定会大面积误报
    （实测本仓多数调用分行）。实现：从含 `subprocess.` 的行起做**括号配平**取整次调用文本。
    局限：不做 AST 解析（**同一行**多调用 / 字符串或注释内的括号属已知近似，见 README 判据边界）。
    """
    hits = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if "subprocess." not in ln:
            continue
        depth = 0
        started = False
        chunk = []
        for j in range(i, min(len(lines), i + 40)):
            chunk.append(lines[j])
            for ch in lines[j]:
                if ch == "(":
                    depth += 1
                    started = True
                elif ch == ")":
                    depth -= 1
            if started and depth <= 0:
                break
        call = "\n".join(chunk)
        if ("text=True" in call or "universal_newlines=True" in call) and "encoding=" not in call:
            hits.append(i + 1)
    return hits


_FIXTURE_EXEMPT_DIRS = {"agate/tests/fixtures/"}


def _is_fixture_exempt(path):
    """M4 fixture 目录声明豁免（P2-design §3.4，BDD-7/BDD-8）：连续路径段包含判定。

    规范化路径中出现 `agate/tests/fixtures` 连续三段即豁免（posix 归一化，
    Windows 反斜杠兼容）；禁用字符串 startswith 相对前缀（tmp_path 绝对路径
    下同名相对结构同样豁免）。仅 R2 数据面使用。
    """
    normalized = str(path).replace("\\", "/")
    segments = [seg for seg in normalized.split("/") if seg]
    for exempt in _FIXTURE_EXEMPT_DIRS:
        want = [seg for seg in exempt.replace("\\", "/").split("/") if seg]
        if not want:
            continue
        for i in range(len(segments) - len(want) + 1):
            if segments[i:i + len(want)] == want:
                return True
    return False


def _r2_comment_exempt(text):
    """R2 注释/探测形态豁免（等价 sh r2_exempt 的 case 与 command -v/env 判定）。"""
    trimmed = text.lstrip()
    if trimmed.startswith("#") or trimmed.startswith("@test"):
        return True
    if "command -v python3" in text or "command -v python" in text:
        return True
    return "env python3" in text


def _docstring_state(text, in_docstring):
    """docstring 块状态推进（仅识别三双引号形式，不处理 r''' 原始串）。

    返回 (本行是否处于 docstring, 下一行状态)。行内 `\"\"\"` 出现奇数次切换
    状态（进入或闭合），偶数次（单行 `\"\"\"...\"\"\"`）整行是 docstring 但
    状态不切换。
    """
    count = text.count('"""')
    if count == 0:
        return in_docstring, in_docstring
    if in_docstring:
        return True, count % 2 != 1
    return True, count % 2 == 1


def _r4_exempt(text):
    """R4 行级豁免：BATS_TEST_TMPDIR 变量行 / "# scan-exempt:" 标记行。"""
    return "BATS_TEST_TMPDIR" in text or "# scan-exempt:" in text


def _scan_file(path, hits):
    """扫描单个文件：逐行跑 R1-R5 正则 + 行级豁免判定，命中追加到 hits。"""
    in_docstring = False
    fixture_exempt = _is_fixture_exempt(path)
    try:
        with open(path, encoding="utf-8") as fh:
            for line_no, line in enumerate(fh, 1):
                text = line.rstrip("\n")
                effective_ds, in_docstring = _docstring_state(text, in_docstring)
                for rule, regex, exempt in _RULES:
                    if exempt == "r2" and fixture_exempt:
                        continue
                    if regex.search(text) is None:
                        continue
                    if exempt == "r2" and (_r2_comment_exempt(text) or effective_ds):
                        continue
                    if exempt == "r4" and _r4_exempt(text):
                        continue
                    hits.append((rule, str(path), line_no, text))
    except OSError:
        pass  # 等价 sh 的 grep 2>/dev/null || true：不可读文件静默跳过

    # R6（调用级，RM-AG0105 / DEBT0058）：`subprocess` 文本模式缺 `encoding=`
    try:
        with open(path, encoding="utf-8") as fh:
            _text = fh.read()
        _lines = _text.splitlines()
        for _ln in _r6_text_without_encoding_hits(_text):
            hits.append(("R6", str(path), _ln, _lines[_ln - 1].strip() if _ln - 1 < len(_lines) else ""))
    except OSError:
        pass


def _scan_target(target, hits):
    """扫描 target：目录递归（*.bats/*.bash/*.sh/*.py）或单个文件；不存在 exit 2。"""
    p = Path(target)
    if p.is_dir():
        for root, dirs, files in os.walk(target):
            dirs.sort()
            for name in sorted(files):
                if name.endswith((".bats", ".bash", ".sh", ".py")):
                    _scan_file(os.path.join(root, name), hits)
    elif p.is_file():
        _scan_file(str(p), hits)
    else:
        sys.stderr.write(f"FATAL: 目标不存在: {target}\n")
        sys.exit(2)


def main():
    targets = sys.argv[1:]
    if not targets:
        script_dir = Path(os.path.realpath(__file__)).parent
        targets = [str(script_dir.parent / "tests")]

    hits = []
    for target in targets:
        _scan_target(target, hits)

    for rule, file, line_no, text in hits:
        sys.stderr.write(f"{rule} {file}:{line_no} {text}\n")
    sys.exit(1 if hits else 0)


if __name__ == "__main__":
    main()
