#!/usr/bin/env python3
"""agate-dispatch.py — 渲染时注入 dispatch-context（新主路径，BDD-18/25）

从模板骨架渲染 {phase}-dispatch-context-{role}.md（TAG0027 P2-design §3.5 定案 D5-A）：
  1. 读 assets/templates/dispatch-context.md 模板骨架（frontmatter 占位 + dispatch_guide
     引导节 + AGATE_CARD_START/END 卡片占位）。
  2. Lazy Injection：子进程调 agate-next-card.py {phase} 取当前阶段卡片全文（正式卡片
     原样 / 裸模板卡片 M3 渲染），渲染时拼装 + CARD-SOURCE 来源标记。
  3. 渲染文件写入 {phase}-dispatch-context-{role}.md（TASK_DIR 指定目录 / 缺省当前目录），
     frontmatter 保持 phase / generated_by: agate-dispatch.py + 主 Agent / task_id / role。

渲染产物结构（§3.5）：
  ---
  phase: {phase}
  generated_by: agate-dispatch.py + 主 Agent
  task_id: {Txxx}
  role: {role}
  ---
  <dispatch_guide>…（模板骨架 + guide 注入）…</dispatch_guide>

  <!-- CARD-SOURCE: agate-dispatch.py {phase} -->   ← 渲染层来源标记，在 AGATE_CARD_START
                                                     ← **之前**（块外）——不进 _extract_card
                                                     ← 抽取区间 → pre-commit 2p hash 不受影响
  <!-- AGATE_CARD_START -->
  {agate-next-card.py {phase} stdout 全文逐字}
  <!-- AGATE_CARD_END -->

CARD-SOURCE 与卡片正文的分隔 = START 标记行（A2 机制，BDD-25 转绿依据）。审计侧
（check-p6-provenance.py 审计 2 / check-judge-verdict.py _strip_card）以 CARD-SOURCE
行起物理块剥离（§3.6 双锚点）。

exit 0 = 成功（文件已写，卡片块与 agate-next-card stdout 一致）；exit 1 = 失败
（参数缺失 / phase 非法 / 模板缺失 / 角色空 / 任务目录不可写 / next-card 不可用或
输出为空 / 模板缺占位符）。

与既有链关系（§3.5 第 5 条）：不替代 agate-inject-card.py（手工兜底保留，BDD-19）；
agate-card-inject.py 仅被 inject-card 调用，不动；agate-render-dispatch-prompt.py 独立
场景（dispatch-prompt 模板渲染）不动（BDD-23）；agate-next-card.py 被本脚本以子进程复用。

平台无关（BDD-16）：无裸解释器、无 /tmp、无软链假设；文本 I/O 显式 utf-8。
"""

import os
import re
import subprocess
import sys

try:
    from agate_common import resolve_agate_root as _agate_common_resolve
except (ImportError, SystemExit):
    _agate_common_resolve = None

_PHASES = ("P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8")

_START_MARKER = "<!-- AGATE_CARD_START -->"
_END_MARKER = "<!-- AGATE_CARD_END -->"
_SOURCE_MARKER = "<!-- CARD-SOURCE: agate-dispatch.py"


def _resolve_agate_root():
    """AGATE_ROOT 解析：归口 agate_common.resolve_agate_root（env → 项目声明 → current 链
    → 脚本路径上溯）；agate_common 不可用时（独立副本场景）回退 env → 脚本真实路径上溯。"""
    if _agate_common_resolve is not None:
        return _agate_common_resolve(os.path.abspath(__file__))
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return env_root
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def _next_card_content(agate_root, phase):
    """调 agate-next-card.py 取卡片全文（$(...) 剥尾换行 → .rstrip("\n")）。

    脚本不可用 / 输出为空 / 非零退出 → 返回 None（调用方 exit 1）。
    返回内容保留 agate-next-card stdout 的既有字节面：末行剥一个尾换行（等价
    bash $(...) 命令替换语义——inject-card 同款），供 START..END 逐字嵌入。
    """
    next_card = os.path.join(agate_root, "scripts", "agate-next-card.py")
    if not os.path.isfile(next_card):
        return None
    try:
        proc = subprocess.run(
            [sys.executable, next_card, phase],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").rstrip("\n")


def _render_dispatch_context(template, phase, role, task_id, guide, card_content):
    """模板骨架 → 渲染产物（§3.5 结构；纯字符串变换，字节稳定无时间戳）。

    变换（全部行级字面替换，模板既有结构保留）：
      1. frontmatter 占位：{P1-P8} → phase；agate-inject-card.py + 主 Agent →
         agate-dispatch.py + 主 Agent（机器来源字段）；{Txxx} → task_id；
         {角色名，如 ...} → role。
      2. guide 骨架替换：<dispatch_guide> 之后首个 "{一句话：...}" → 注入的 guide
         行（保留 dispatch_guide 结构 + 模板其余节——模板骨架占位未替换处由主 Agent
         后续手填，语义同 render-dispatch-prompt 的 parent_note 提示）。
      3. 卡片块：AGATE_CARD_START 前一行插入 CARD-SOURCE 注释（块外，不进抽取区间）；
         START..END 之间占位内容整体替换为 next-card stdout（含卡片 header + 正文，
         逐字）。
    """
    lines = template.splitlines()

    # 1. frontmatter 占位替换
    lines = [line.replace("{P1-P8}", phase) for line in lines]
    lines = [
        line.replace("agate-inject-card.py + 主 Agent", "agate-dispatch.py + 主 Agent")
        for line in lines
    ]
    lines = [line.replace("{Txxx}", task_id) for line in lines]
    lines = [line.replace("{角色名，如 analyst / requirements-review / implementer}", role) for line in lines]
    lines = [line.replace("{角色名}", role) for line in lines]

    # 2. guide 骨架替换（首个「{一句话：...}」占位行 → 注入 guide）
    guide_re = re.compile(r"^\{一句话：本角色在本阶段要产出什么\}$")
    if guide and guide.strip():
        replaced = False
        for i, line in enumerate(lines):
            if guide_re.match(line):
                lines[i] = guide.strip().replace("\r", "")
                replaced = True
                break
        if not replaced:
            # 占位行不存在（模板改版）→ 在 </dispatch_guide> 前追加（保持骨架可用）
            for i in range(len(lines) - 1, -1, -1):
                if lines[i].strip() == "</dispatch_guide>":
                    lines.insert(i, guide.strip().replace("\r", ""))
                    break

    # 3. 卡片块：START 前插 CARD-SOURCE（块外）+ START..END 内容替换
    start_idx = None
    end_idx = None
    for i, line in enumerate(lines):
        if start_idx is None and _START_MARKER in line:
            start_idx = i
        elif start_idx is not None and end_idx is None and _END_MARKER in line:
            end_idx = i
            break
    if start_idx is None or end_idx is None:
        return None  # 模板缺卡片占位符 → 调用方 exit 1（不可渲染）

    out = []
    for i, line in enumerate(lines):
        if i == start_idx:
            # 块外来源标记行（与 START 之间无空行——START 即 CARD-SOURCE 与卡片正文分隔）
            out.append(f"{_SOURCE_MARKER} {phase} -->")
            out.append(line)
            for card_line in card_content.split("\n"):
                out.append(card_line)
        elif i == end_idx:
            out.append(line)
        elif start_idx < i < end_idx:
            continue  # 原占位内容整体替换
        else:
            out.append(line)
    return "\n".join(out) + "\n"


def _route_main(argv_rest):
    """agate-dispatch.py route PHASE ROLE [TASK_DIR] —— 派发路由决策子命令（TAG0034）。

    读 dispatch-routing.yaml + dispatch-tiers.yaml → resolve(phase, role) → stdout 输出
    单行 target 描述 JSON {"cli","model","effort","form","dispatch_context"[,"chain"]}。
    无 `route` 参数时 main() 的既有渲染路径逐字节不变——本函数是纯新增分支。

    P4b（M5）：form == "chain" 且首候选为子进程形态（claude-code / codex / opencode）
    时，本函数端到端跑 try_and_fall（逐候选 dispatch_once → 三类基础设施理由码回落 →
    HAS_OUTPUT 即停、写 dispatch_route 事件、输出实际 final）。首候选为 native 时仍只
    输出路由计划 JSON（native 由驱动会话代发，与 P4a DESIGN_GAP 一致）。
    I3：try_and_fall 的 write_event(phase, tried, final) 位置参数回调 ↔
    write_dispatch_route_event(task_dir, phase, *, tried, final, task_id) kw-only 写入器
    —— 在本函数内以适配层闭包桥接（两处签名各自不动）。
    """
    import json

    if len(argv_rest) < 2:
        sys.stderr.write("用法: agate-dispatch.py route PHASE ROLE [TASK_DIR]\n")
        sys.exit(1)
    phase = argv_rest[0]
    role = argv_rest[1]
    task_dir = argv_rest[2] if len(argv_rest) > 2 else os.getcwd()

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        import agate_dispatch_route as adr
    except ImportError as exc:
        sys.stderr.write(f"agate-dispatch.py route: 无法 import agate_dispatch_route: {exc}\n")
        sys.exit(1)

    agate_root = _resolve_agate_root()
    project_root = os.getcwd()
    workspace = os.path.join(project_root, "agate-workspace")
    try:
        from agate_common import resolve_workspace

        workspace = resolve_workspace(project_root)[0]
    except Exception:
        pass

    routes, tier_bindings = adr.load_config(workspace)
    _tier_names, factory_defaults = adr.load_factory_defaults(agate_root)
    current_model = os.environ.get("AGATE_CURRENT_MODEL", "")

    resolved = adr.resolve(
        phase, role,
        routes=routes, tier_bindings=tier_bindings,
        factory_defaults=factory_defaults, current_model=current_model,
    )

    safe_role = re.sub(r"[^a-zA-Z0-9_-]", "_", role)
    ctx_path = os.path.join(task_dir, f"{phase}-dispatch-context-{safe_role}.md")

    if resolved["form"] == "default":
        out = {
            "cli": "default", "model": resolved["model"], "effort": None,
            "form": "default", "dispatch_context": ctx_path,
        }
    elif resolved["chain"][0].get("cli") == "native":
        first = resolved["chain"][0]
        out = {
            "cli": "native", "model": first.get("model"),
            "effort": first.get("effort"), "form": "native",
            "chain": resolved["chain"], "dispatch_context": ctx_path,
        }
    else:
        # 子进程形态首候选 → 端到端 try-and-fall（M5 / I3 桥接）。
        import functools

        task_id = os.path.basename(os.path.abspath(task_dir))
        effort_supported = os.environ.get("AGATE_EFFORT_SUPPORTED", "") == "1"
        expected_output = os.environ.get("AGATE_DISPATCH_EXPECT") or None

        def _write_event(phase_, tried_, final_):
            adr.write_dispatch_route_event(
                task_dir, phase_, tried=tried_, final=final_, task_id=task_id,
            )

        _once = functools.partial(
            adr.dispatch_once, effort_supported=effort_supported,
            expected_output=expected_output, task_dir=task_dir,
        )
        try:
            result = adr.try_and_fall(
                resolved["chain"], dispatch_context_path=ctx_path,
                dispatch_once=_once, write_event=_write_event, phase=phase,
            )
        except adr.DispatchContractError as exc:
            sys.stderr.write(f"agate-dispatch.py route: 派发契约违例: {exc}\n")
            sys.exit(1)

        final = result.final
        form = "default" if final.get("cli") == "default" else "subprocess"
        out = {
            "cli": final.get("cli"), "model": final.get("model"),
            "effort": final.get("effort"), "form": form,
            "chain": resolved["chain"], "final": final, "tried": result.tried,
            "dispatch_context": ctx_path,
        }

    sys.stdout.write(json.dumps(out, ensure_ascii=False) + "\n")
    sys.exit(0)


def main():
    # CLI: agate-dispatch.py PHASE ROLE [TASK_DIR] [--guide FILE]
    args = sys.argv[1:]
    if args and args[0] == "route":
        _route_main(args[1:])
        return
    if len(args) < 2:
        sys.stderr.write("用法: agate-dispatch.py PHASE ROLE [TASK_DIR] [--guide FILE]\n")
        sys.exit(1)

    phase = args[0]
    role = args[1]

    if phase not in _PHASES:
        sys.stderr.write(f"agate-dispatch.py: phase '{phase}' 不在 P1-P8 范围内\n")
        sys.exit(1)
    if not role:
        sys.stderr.write("agate-dispatch.py: ROLE 不能为空\n")
        sys.exit(1)

    task_dir = os.getcwd()
    guide = None
    i = 2
    while i < len(args):
        if args[i] == "--guide" and i + 1 < len(args):
            guide = args[i + 1]
            i += 2
        else:
            task_dir = args[i]
            i += 1
    if not os.path.isdir(task_dir):
        sys.stderr.write(f"agate-dispatch.py: 任务目录不存在: {task_dir}\n")
        sys.exit(1)

    # role 文件名安全化（输出文件名不能含路径分隔符；镜像 render-dispatch-prompt 的 sanitize）
    safe_role = re.sub(r"[^a-zA-Z0-9_-]", "_", role)

    agate_root = _resolve_agate_root()
    template_path = os.path.join(agate_root, "assets", "templates", "dispatch-context.md")
    if not os.path.isfile(template_path):
        sys.stderr.write(f"agate-dispatch.py: 模板文件不存在: {template_path}\n")
        sys.exit(1)
    try:
        with open(template_path, encoding="utf-8") as f:
            template = f.read()
    except OSError as exc:
        sys.stderr.write(f"agate-dispatch.py: 模板读取失败: {exc}\n")
        sys.exit(1)

    task_id = os.path.basename(os.path.abspath(task_dir))

    guide_text = None
    if guide is not None:
        if not os.path.isfile(guide):
            sys.stderr.write(f"agate-dispatch.py: guide 文件不存在: {guide}\n")
            sys.exit(1)
        try:
            with open(guide, encoding="utf-8") as f:
                guide_text = f.read().rstrip("\n")
        except OSError as exc:
            sys.stderr.write(f"agate-dispatch.py: guide 文件读取失败: {exc}\n")
            sys.exit(1)

    card_content = _next_card_content(agate_root, phase)
    if not card_content:
        sys.stderr.write(f"agate-dispatch.py: agate-next-card.py {phase} 输出为空或不可用\n")
        sys.exit(1)

    rendered = _render_dispatch_context(
        template, phase, safe_role, task_id, guide_text, card_content
    )
    if rendered is None:
        sys.stderr.write("agate-dispatch.py: 模板缺 AGATE_CARD_START/END 卡片占位符，不可渲染\n")
        sys.exit(1)

    output_file = os.path.join(task_dir, f"{phase}-dispatch-context-{safe_role}.md")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(rendered)
    except OSError as exc:
        sys.stderr.write(f"agate-dispatch.py: 写入失败: {exc}\n")
        sys.exit(1)
    sys.stdout.write(f"已渲染 {os.path.basename(output_file)}（卡片来源: agate-next-card.py {phase}）\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
