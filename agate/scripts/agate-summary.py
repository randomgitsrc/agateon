#!/usr/bin/env python3
"""agate-summary.py — 输出项目解析到的 agate 版本 + 原因 + 防护状态

TAG0008（批次 resolve-chain）语义迁移：从"仓库自身 git describe"→"项目解析到的版本 +
原因"（.agate-version 声明或全局 current，P2 §4.6 / BDD-20/21）。复用
agate_common.resolve_version_root，不重复实现。

用法：
  python3 ~/.agate/scripts/agate-summary.py

用途：agent 启动时快速知道当前项目用什么协议版本，是否需要升级等。
exit 0：成功（输出到 stdout）；解析警告写 stderr；终态无可用根时 stderr 提示但
不退出（显示占位），版本解析失败不阻断启动信息。

迁移说明：TAG0010 批次 1d 迁移保留防护机制/漂移检测；git-describe 版本显示被
resolve_version_root 替换（worktree .git 是文件非目录时 _find_git_root 失效，
新语义不再依赖 git repo）。
"""

import os
import sys
from pathlib import Path

try:
    from agate_common import resolve_version_root
except (ImportError, SystemExit):
    sys.stderr.write("agate-summary: agate_common 不可用（缺 pyyaml？），版本解析不可用\n")
    sys.exit(1)

_GUARD_SCRIPTS = [
    "check-state-yaml.py",
    "check-gate.py",
    "check-changelog.py",
    "check-p6-evidence.py",
    "check-p6-provenance.py",
    "check-state-transition.py",
    "check-pruning.py",
    "check-scope-resolved.py",
    "check-retrospective.py",
]

_DRIFT_SCRIPTS = [
    "check-tdd-red.py",
    "check-gate.py",
    "check-pruning.py",
    "agate-risk-score.py",
    "check-routing.py",
    "check-judge-verdict.py",
    "check-events.py",
    "check-maintainability.py",
]


def _build_guards(script_dir):
    """防护机制清单（等价 sh 的 GUARDS 拼接 + printf '%b' 解释 \\n）。"""
    parts = []
    for script in _GUARD_SCRIPTS:
        if os.path.isfile(os.path.join(script_dir, script)):
            parts.append("  ✓ " + script)
    pre_commit = os.path.join(script_dir, "pre-commit-gate.sh")
    if os.path.isfile(pre_commit) and os.access(pre_commit, os.X_OK):
        parts.append("  ✓ pre-commit-gate.sh（hook 入口）")
    ci_backstop = os.path.join(script_dir, "ci-gate-backstop.py")
    if os.path.isfile(ci_backstop) and os.access(ci_backstop, os.X_OK):
        parts.append("  ✓ ci-gate-backstop.py（CI 兜底）")
    if not parts:
        return ""
    return "\n".join(parts)


def _files_identical(a, b):
    """cmp -s 等价：逐字节比较。"""
    try:
        with open(a, "rb") as f1, open(b, "rb") as f2:
            return f1.read() == f2.read()
    except OSError:
        return False


def _check_copy_drift(script_dir):
    """检测项目 scripts/ 本地副本与权威版本漂移（等价 sh 的 _check_copy_drift）。

    权威版本 = script_dir（agate/scripts/）；项目副本 = 当前目录的 scripts/。
    """
    for script in _DRIFT_SCRIPTS:
        local = os.path.join("scripts", script)
        auth = os.path.join(script_dir, script)
        if os.path.isfile(local) and os.path.isfile(auth) and not _files_identical(local, auth):
            sys.stderr.write(
                f"⚠️  scripts/{script} 与 agate 权威版本不一致——本地副本可能已过期，建议改用 "
                "{agate_root}/scripts/ 或转发脚本\n"
            )


_DSH_LINK_ARTIFACTS = (
    (".agent-presets/agate/preset.yml", "preset.yml"),
    (".agent-presets/agate/agent.cordis.yml", "agent.cordis.yml"),
    ("skills/agate-protocol/SKILL.md", "SKILL.md"),
)


def _check_dsh_links(script_dir):
    """校验 DSH 安装产物软链指向权威链（防指向非权威副本的静默漂移）。

    背景（2026-08-26）：~/.dsh/skills/agate-protocol/SKILL.md 曾被安装成指向测试用
    临时副本而非 ~/.agate 权威链，静默存活穿过一次发布——安装后无校验所致。
    权威目标 = {agate_root}/assets/templates/dsh/ 下同名文件（script_dir 上溯一层）。
    无 ~/.dsh（未装 DSH）或 Windows（无 DSH 部署）→ 整体跳过。
    """
    if os.name == "nt":
        return
    dsh_home = os.path.join(os.path.expanduser("~"), ".dsh")
    if not os.path.isdir(dsh_home):
        return
    tpl_dir = os.path.join(os.path.dirname(script_dir), "assets", "templates", "dsh")
    for rel, name in _DSH_LINK_ARTIFACTS:
        link = os.path.join(dsh_home, *rel.split("/"))
        expected = os.path.join(tpl_dir, name)
        if not os.path.isfile(expected):
            continue  # 本版本无该权威模板 → 无从校验
        if not os.path.lexists(link):
            sys.stderr.write(
                f"⚠️  DSH 安装产物未安装: {link}（如需 DSH 接入见 agate/SETUP.md 步骤 2-DSH）\n"
            )
            continue
        if os.path.realpath(link) != os.path.realpath(expected):
            sys.stderr.write(
                f"⚠️  DSH 安装产物漂移: {link} 指向非权威副本（{os.path.realpath(link)}）\n"
                f"    修复: ln -sf {expected} {link}\n"
            )


def main():
    script_real = os.path.realpath(__file__)
    script_dir = os.path.dirname(script_real)
    if not script_dir:
        sys.stderr.write("GATE: 无法解析脚本路径（非 git 仓库或非标准安装？）\n")
        sys.exit(1)

    info = resolve_version_root()
    for w in info["warnings"]:
        sys.stderr.write(w + "\n")

    guards = _build_guards(script_dir)
    _check_copy_drift(script_dir)
    _check_dsh_links(script_dir)

    version = info["version"] or "（未解析到版本）"
    reason = info["reason"] or "（无原因）"
    root = str(Path(info["root"]).resolve()) if info["root"] else "（无可用 AGATE_ROOT）"

    # CHANGELOG 在仓库根，不在 agate/ 协议本体下（legacy 单软链 ~/.agate → <clone>/agate，
    # CHANGELOG 是 <clone>/CHANGELOG.md；版本布局整仓形态下 <vdir>/CHANGELOG.md）。探测两处。
    changelog_hint = "~/.agate/../CHANGELOG.md（仓库根）"
    if info["root"]:
        rp = Path(info["root"]).resolve()
        for cand in (rp.parent / "CHANGELOG.md", rp / "CHANGELOG.md"):
            if cand.is_file():
                changelog_hint = str(cand)
                break

    lines = [
        "=== agate 当前状态 ===",
        "",
        f"版本：{version}",
        f"原因：{reason}",
        f"AGATE_ROOT：{root}",
        "",
        "防护机制（pre-commit + CI）：",
        guards,
        "",
        "快速版本对比：python3 ~/.agate/scripts/agate-changes.py [since-tag]",
        "默认输出自上一个 tag 起的 commit + 受影响的协议文件。",
        "查远端更新：python3 ~/.agate/scripts/agate-changes.py --check-upstream",
        "",
        "=== 启动时建议 ===",
        "",
        "1. 第一行：上面这一段（确认协议版本 + 防护机制就位）",
        "2. 读 ~/.agate/AGENTS.md（协议本体入口指引）",
        f"3. 读 {changelog_hint}（了解自上次会话以来发生了什么）",
        "4. 按 orchestrator-template.md mapping 表读当前阶段卡片，按需查阅 Fallback reference 节",
        "",
    ]
    out = "\n".join(lines) + "\n"
    sys.stdout.buffer.write(out.encode("utf-8"))


if __name__ == "__main__":
    main()
