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
    from agate_common import (
        _protocol_root,
        resolve_version_root,
        symlink_migration_hint,
    )
    from agate_package import agate_home
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


# 平台安装产物清单：{平台名: (平台 home 目录, ((产物相对路径, 模板相对协议根路径), ...), 备注)}
#   末位字段当前未在输出中使用（未接入提示已聚合为一行、统一指 SETUP.md 步骤 2）；
#   保留以记录各平台接入步骤编号，供人工排查时对照。
#   覆盖 `agate-setup.py` 支持的**全部四个平台**——清单与 PLATFORMS 表须同步：漏一个，
#   该平台的产物漂移就无人检测（Codex 曾缺席；Claude Code / OpenCode 亦曾缺席，2026-09-21 补齐）。
#   仅覆盖**全局**形态（`--scope project` 的项目内产物不在此列：它随项目走、且项目目录各异，
#   其一致性由项目自身的版本控制保证）。
_PLATFORM_ARTIFACTS = (
    ("Claude Code", ".claude", (
        ("agents/orchestrator.md", "orchestrator-template.md"),
    ), "2"),
    ("OpenCode", ".config/opencode", (
        ("agents/orchestrator.md", "orchestrator-template.md"),
    ), "2"),
    ("DSH", ".dsh", (
        (".agent-presets/agate/preset.yml", "assets/templates/dsh/preset.yml"),
        (".agent-presets/agate/agent.cordis.yml", "assets/templates/dsh/agent.cordis.yml"),
        ("skills/agate-protocol/SKILL.md", "assets/templates/dsh/SKILL.md"),
    ), "2-DSH"),
    ("Codex", ".agents", (
        ("skills/agate-protocol/SKILL.md", "assets/templates/codex/SKILL.md"),
    ), "2-Codex"),
)


def _installed_version_proto_roots():
    """**已安装版本**的协议根集合（机器级；**不**含项目 `.agate-version` 钉版的影响）。

    为什么权威判据是"已安装版本集合"而非"当前解析根或 current"（2026-09-21 修正）：
      本函数服务的 `_PLATFORM_ARTIFACTS` 全是 **HOME 级全局产物**。它们的正当性标准是
      "**指向某个已安装版本**"，而不是"跟随项目钉的版本"或"跟随 current"——
      - 用 `resolve_version_root()`（层序含**项目声明**）当权威：在钉了旧版的项目里，
        指向 current 的全局产物会被误报漂移；按建议"修复"后，非钉版目录又报漂移
        → **双向振荡**（对齐审查实测，2026-09-21）。
      - 用"已安装版本集合"当权威：dev checkout / 测试临时副本（**不在任何已装版本树内**）
        仍被报出——这正是本检测的原始缺陷类（历史上 SKILL.md 曾指向测试临时副本、
        静默穿过一次发布）。
    取镜像目录时不跟随软链（`latest`/`current` 是指针软链，不是版本目录）；Windows 下
    它们是文本文件，`isdir` 自然排除。
    """
    base = agate_home()
    roots = []
    if os.path.isdir(base):
        for name in sorted(os.listdir(base)):
            vdir = os.path.join(base, name)
            if os.path.islink(vdir) or not os.path.isdir(vdir):
                continue
            roots.append(_protocol_root(vdir))
    return roots


def _check_platform_artifacts(script_dir):
    """校验各平台安装产物与权威模板一致（防静默漂移 / 防复制模式过期）。

    背景（2026-08-26）：~/.dsh/skills/agate-protocol/SKILL.md 曾被安装成指向测试用
    临时副本而非 ~/.agate 权威链，静默存活穿过一次发布——安装后无校验所致。

    **两种安装形态都要正确判定**（2026-09-21 补，随 Codex 检测一并修）：
      - **软链**（Linux/macOS 标准）：目标须指向权威模板 → 比对 `realpath`。
      - **复制**（Windows 无符号链接权限 / `AGATE_HOOK_COPY_MODE=1`）：内容须与权威模板
        一致 → **比对内容**。复制模式的固有风险是"模板升级后副本变旧"，只有比内容才检得出；
        且此前的 `realpath` 比对对复制产物**必然不等**，会把正常安装误报为漂移
        （此前靠 Windows 整体跳过掩盖，Linux 复制模式则会误报）。

    无该平台目录（未装该平台）或本版本无对应权威模板 → 跳过，不误报。
    """
    home = os.path.expanduser("~")
    installed = _installed_version_proto_roots()
    not_installed = []          # 聚合待报（见函数末：一行汇总，避免逐平台刷屏）
    for name, platform_dir, artifacts, _setup_step in _PLATFORM_ARTIFACTS:
        if not os.path.isdir(os.path.join(home, platform_dir)):
            continue
        for rel, tpl_rel in artifacts:
            link = os.path.join(home, platform_dir, *rel.split("/"))
            # 权威候选 = **任一已安装版本**里的同名模板（见 _installed_version_proto_roots）
            candidates = [os.path.join(r, *tpl_rel.split("/")) for r in installed]
            candidates = [c for c in candidates if os.path.isfile(c)]
            if not candidates:
                continue  # 无任何已安装版本含该模板 → 无从校验
            if not os.path.lexists(link):
                # 「已装该平台但未接入 agate」是**正常状态**（用户可能不需要），
                # 故只做**一行汇总**提示，不逐产物刷屏——本机四平台目录都在时，
                # 逐条会一次打出 3 行噪声（2026-09-21 对齐审查指出）。
                not_installed.append(name)
                continue
            if os.path.islink(link):
                target = os.path.realpath(link)
                if target not in {os.path.realpath(c) for c in candidates}:
                    sys.stderr.write(
                        f"⚠️  {name} 安装产物漂移: {link}\n"
                        f"    实指 {target}\n"
                        f"    不在任何已安装版本树内（权威模板: {candidates[-1]}）\n"
                        # 修复命令用**稳定入口**而非上面那行路径：本脚本可能正从
                        # worktree/开发 checkout 运行，此时候选路径指向未发布树，
                        # 照抄会把安装指到那里。
                        f"    修复: python3 ~/.agate/scripts/agate-setup.py\n"
                    )
            elif not any(_files_identical(link, c) for c in candidates):
                # 复制形态且内容与**所有**已安装版本都不一致 = 副本已旧或来自异物
                sys.stderr.write(
                    f"⚠️  {name} 安装产物已过期: {link} 内容与任何已安装版本的模板都不一致"
                    f"（复制模式不自动同步）\n"
                    f"    修复: python3 ~/.agate/scripts/agate-setup.py\n"
                )
    if not_installed:
        # 去重保序（DSH 三产物只报一次平台名）。措辞保留「未安装」与 SETUP.md 指引
        # （既有 BDD 断言锚定这两个子串），只是把 N 行合并为 1 行。
        names = list(dict.fromkeys(not_installed))
        sys.stderr.write(
            # 措辞覆盖两种情形：完全未接入 / 部分产物缺失（后者不应说"未安装"）
            f"ℹ️  平台接入产物未安装或不完整: {' / '.join(names)}"
            f"（接入: python3 ~/.agate/scripts/agate-setup.py；"
            f"平台差异见 agate/SETUP.md 步骤 2）\n"
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
    _check_platform_artifacts(script_dir)

    version = info["version"] or "（未解析到版本）"
    reason = info["reason"] or "（无原因）"
    root = str(Path(info["root"]).resolve()) if info["root"] else "（无可用 AGATE_ROOT）"

    # CHANGELOG 在版本根 <vdir>/CHANGELOG.md（契约形态，root=<vdir>/agate 的上一层）或协议根内。探测两处。
    changelog_hint = "<版本根>/CHANGELOG.md"
    if info["root"]:
        rp = Path(info["root"]).resolve()
        for cand in (rp.parent / "CHANGELOG.md", rp / "CHANGELOG.md"):
            if cand.is_file():
                changelog_hint = str(cand)
                break

    # 软链迁移提示：仅在没有任何根可解析且基址是软链时打印（软链 → 完整版本根经 current 链正常解析，不算旧布局，eng N-4）
    migration = []
    if not info["root"] and info.get("symlink_base"):
        migration = ["", *symlink_migration_hint().rstrip("\n").split("\n")]

    entry = f"读 {root}/AGENTS.md（协议本体入口指引）" if info["root"] else "先按上方提示修复安装（无可用 AGATE_ROOT）"

    lines = [
        "=== agate 当前状态 ===",
        "",
        f"版本：{version}",
        f"原因：{reason}",
        f"AGATE_ROOT：{root}",
        *migration,
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
        f"2. {entry}",
        f"3. 读 {changelog_hint}（了解自上次会话以来发生了什么）",
        "4. 按 orchestrator-template.md mapping 表读当前阶段卡片，按需查阅 Fallback reference 节",
        "",
    ]
    out = "\n".join(lines) + "\n"
    sys.stdout.buffer.write(out.encode("utf-8"))


if __name__ == "__main__":
    main()
