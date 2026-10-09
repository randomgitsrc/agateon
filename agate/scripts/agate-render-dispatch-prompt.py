#!/usr/bin/env python3
"""agate-render-dispatch-prompt.py — 渲染 dispatch-prompt 模板为具体派发实例

从 agate-render-dispatch-prompt.sh 迁移（TAG0010 批次 1c）。用法：
  agate-render-dispatch-prompt.py PHASE ROLE TASK_DIR [--rollback]

PHASE: P1-P8
ROLE: subagent 角色名（如 analyst, architect, implementer 等）
TASK_DIR: 任务目录路径（含 P0-brief.md 等）
--rollback: 可选，P4 回退派发时使用（选"P4 回退派发追加"而非"P4 派发追加"）

输出：
  1. 渲染后的完整文本写入 TASK_DIR/P{N}-dispatch-prompt-{role}.md（持久化存档）
  2. 同时打印到 stdout（主 Agent 复制作为 Task 工具调用的 prompt）

exit 0：成功；exit 1：参数个数错误；exit 2：phase 不在 P1-P8 / 任务目录、
模板或角色文件不存在。

迁移说明：sed 管道（范围打印 + 行删除 + 首个 ``` 代码块抽取）→ 正则范围扫描 +
围栏块提取；sed s 替换 → str.replace 字面替换（esc_repl 的 &|/\\ 转义在字面替换
下不再需要，语义等价）；$(...) 剥尾换行 → 代码块内容 rstrip("\\n")。
"""

import os
import re
import sys
from datetime import date

try:
    from agate_common import resolve_agate_root as _agate_common_resolve
    from agate_common import (
        resolve_workspace_from_task_dir as _agate_common_resolve_workspace_from_task_dir,
    )
except (ImportError, SystemExit):
    _agate_common_resolve = None
    _agate_common_resolve_workspace_from_task_dir = None

_PHASES = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")


def _resolve_agate_root():
    """AGATE_ROOT 解析：归口 agate_common.resolve_agate_root（env → 项目声明 → current 链
    → 脚本路径上溯）；agate_common 不可用时（独立副本场景）回退 env → 脚本真实路径上溯。"""
    if _agate_common_resolve is not None:
        return _agate_common_resolve(os.path.abspath(__file__))
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return env_root
    script_real = os.path.realpath(__file__)
    return os.path.dirname(os.path.dirname(script_real))


def _resolve_workspace(task_dir):
    """由 task_dir 解析工作区（RM-AG0084 / DEBT0028）——委托 `agate_common` 的**单源实现**
    （`resolve_workspace_from_task_dir`，三处消费方共用）；`agate_common` 不可用时回退
    旧的两级 dirname 推导，保持既有行为。"""
    if _agate_common_resolve_workspace_from_task_dir is not None:
        return _agate_common_resolve_workspace_from_task_dir(task_dir)
    return os.path.dirname(os.path.dirname(os.path.abspath(str(task_dir).rstrip(os.sep))))


def _range(lines, start_re, end_re):
    """sed -n '/START/,/END/p' 等价：START 起（含）到其后首个匹配 END 行止（含）。

    END 从 START 之后的下一行开始找（GNU sed 实测语义：START 行自身匹配 END 时
    范围仍延伸到下一处 END）；无 END 匹配则到 EOF。
    """
    start_idx = None
    for i, line in enumerate(lines):
        if start_re.search(line):
            start_idx = i
            break
    if start_idx is None:
        return []
    end_idx = None
    for i in range(start_idx + 1, len(lines)):
        if end_re.search(lines[i]):
            end_idx = i
            break
    if end_idx is None:
        return lines[start_idx:]
    return lines[start_idx:end_idx + 1]


def _drop(lines, drop_re):
    """sed '/DROP/d' 等价：删除匹配行。"""
    return [line for line in lines if not drop_re.search(line)]


def _extract_code_block(lines):
    """awk extract_first_code_block 等价：取首个 ``` 围栏块内容（不含围栏行）。"""
    started = False
    out = []
    for line in lines:
        if line == "```":
            if not started:
                started = True
            else:
                break
        elif started:
            out.append(line)
    # $(...) 剥尾换行：围栏块内末尾空行不保留
    return "\n".join(out).rstrip("\n")


def _section_block(lines, start_re, end_re, drop_re):
    """sed 管道（范围打印 | 行删除 | 代码块抽取）的整体等价。"""
    return _extract_code_block(_drop(_range(lines, start_re, end_re), drop_re))


def main():
    args = sys.argv[1:]
    if len(args) < 3 or len(args) > 4:
        sys.stderr.write("用法: agate-render-dispatch-prompt.py PHASE ROLE TASK_DIR [--rollback]\n")
        sys.exit(1)

    phase = args[0]
    role = args[1]
    task_dir = args[2]
    rollback = args[3] if len(args) > 3 else ""

    if phase not in _PHASES:
        sys.stderr.write(f"agate-render-dispatch-prompt.py: phase '{phase}' 不在 P1-P8 范围内\n")
        sys.exit(2)

    if not os.path.isdir(task_dir):
        sys.stderr.write(f"agate-render-dispatch-prompt.py: 任务目录不存在: {task_dir}\n")
        sys.exit(2)

    agate_root = _resolve_agate_root()
    template = os.path.join(agate_root, "assets", "templates", "dispatch-prompt.md")
    if not os.path.isfile(template):
        sys.stderr.write(f"agate-render-dispatch-prompt.py: 模板文件不存在: {template}\n")
        sys.exit(2)

    task_id = os.path.basename(task_dir)
    phase_num = phase[1:]
    today = date.today().strftime("%Y-%m-%d")
    trace_id = "{}-{}-{}".format(task_id, phase, today.replace("-", ""))

    exec_role = os.path.join(agate_root, "assets", "execution-roles", role + ".md")
    review_role = os.path.join(agate_root, "assets", "review-roles", role + ".md")
    if os.path.isfile(review_role) and not os.path.isfile(exec_role):
        role_dir = "review-roles"
    elif not os.path.isfile(review_role) and not os.path.isfile(exec_role):
        sys.stderr.write(
            f"agate-render-dispatch-prompt.py: 角色文件不存在: {role} (checked execution-roles/ and review-roles/)\n"
        )
        sys.exit(2)
    else:
        role_dir = "execution-roles"

    safe_role = re.sub(r"[^a-zA-Z0-9_-]", "_", role)
    output_file = os.path.join(task_dir, f"P{phase_num}-dispatch-prompt-{safe_role}.md")

    with open(template, encoding="utf-8") as f:
        tpl_lines = f.read().splitlines()

    head_end = re.compile(r"^## 阶段特定提示")
    main_block = _extract_code_block(_drop(_range(tpl_lines, re.compile(r"^"), head_end), head_end))

    review_appendix = ""
    if role_dir == "review-roles":
        review_appendix = _section_block(
            tpl_lines,
            re.compile(r"^### Review 角色特别指令$"),
            re.compile(r"^### "),
            re.compile(r"^### "),
        )

    appendix = ""
    if phase == "P2":
        appendix = _section_block(
            tpl_lines, re.compile(r"^### P2 派发追加$"), re.compile(r"^### "), re.compile(r"^### ")
        )
    elif phase == "P3":
        appendix = _section_block(
            tpl_lines, re.compile(r"^### P3 派发追加$"), re.compile(r"^### "), re.compile(r"^### ")
        )
    elif phase == "P4":
        if rollback == "--rollback":
            appendix = _section_block(
                tpl_lines, re.compile(r"^### P4 回退派发追加"), re.compile(r"^### "), re.compile(r"^### ")
            )
        else:
            appendix = _section_block(
                tpl_lines, re.compile(r"^### P4 派发追加$"), re.compile(r"^### "), re.compile(r"^### ")
            )
    elif phase in ("P5", "P6"):
        appendix = _section_block(
            tpl_lines, re.compile(r"^### P5/P6 派发追加$"), re.compile(r"^### "), re.compile(r"^### ")
        )
    elif phase == "P8":
        appendix = _section_block(
            tpl_lines, re.compile(r"^### P8 派发追加$"), re.compile(r"^### "), re.compile(r"^### ")
        )

    rendered = main_block
    if review_appendix:
        rendered += "\n\n" + review_appendix
    if appendix:
        rendered += "\n\n" + appendix

    workspace_render = _resolve_workspace(task_dir)

    # sed s 替换（原顺序逐个字面替换；esc_repl 转义在此不再需要）
    replacements = [
        ("{agate_root}", agate_root),
        ("{AGATE_WORKSPACE}", workspace_render),
        ("{execution-roles|review-roles}", role_dir),
        ("{阶段 Pn}", phase),
        ("{Pn}", phase),
        ("P{N}", "P" + phase_num),
        ("{角色名}", role),
        ("{role}", role),
        ("{Txxx}", task_id),
        ("{YYYY-MM-DD}", today),
        ("{YYYYMMDD}", today.replace("-", "")),
        ("{完整 task_id，如 T002-fix-db-migration}", task_id),
        (f"{{Txxx}}-{phase}-{{YYYYMMDD}}", trace_id),
    ]
    for pattern, repl in replacements:
        rendered = rendered.replace(pattern, repl)

    parent_note = ""
    if "{上一阶段文件名}" in rendered:
        parent_note = (
            "\n\n> ⚠️ 上述 parent 字段（{上一阶段文件名}）需要主 Agent 手动填写："
            "渲染脚本无法自动推断上一阶段产出文件名。请复制渲染结果后补全此字段。"
        )

    header = "> 本文件是 agate-render-dispatch-prompt.py 的渲染产物，不是协议模板。修改本文件不会影响模板。"
    final = header + "\n\n" + rendered + parent_note

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final + "\n")
    sys.stdout.write(final + "\n")
    sys.stderr.write(f"已写入 {output_file}\n")


if __name__ == "__main__":
    main()
