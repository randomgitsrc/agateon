#!/usr/bin/env python3
"""agate-setup.py — Agateon 接入命令：平台身份注册（L2 全局）+ git hook（L3 项目侧）。

**为什么需要（2026-09-21）**：SETUP.md 此前是逐平台手工步骤（`ln -sf` / `cp`），
且各平台的配置物形态不同（Claude Code / OpenCode = agent md；DSH = preset + skill；
Codex = skill），用户须逐条执行、跨平台易漏、Windows 需自行改走复制分支。
本命令把这些步骤自动化——**不再让 agent 照文档手工执行**。

**同时修复的漂移**：DSH/Codex 适配文件曾**复制协议内容**（会话开始步骤、职责边界），
与 `orchestrator-template.md` 形成两处维护——TAG0037 改了模板的路径表述，DSH 副本
未跟（实测失实：把版本根 `~/.agate` 当协议根）。现适配层只做「**指向 + 平台差异**」，
协议内容单一来源仍在模板。

**层次（勿混）**：

| 层 | 内容 | 位置 | 谁装 |
|----|------|------|------|
| L1 协议本体 | `agate/` + 登记根文件 | `~/.agate/vX.Y.Z/` | `agate-install.py` |
| L2 平台身份 | 让平台能调起 orchestrator | 各平台全局配置目录 | **本命令** |
| L3 项目绑定 | git hook / `agate-workspace/` / `.agate-version` | 项目内 | 本命令（hook）+ 协议运行时 |

用法：
    python3 agate-setup.py                      # 自动探测已装平台：全局注册 + 装 hook
    python3 agate-setup.py --platform dsh,codex # 指定平台
    python3 agate-setup.py --scope global       # 只注册平台身份（不装 hook）
    python3 agate-setup.py --scope project      # 只装 hook（不注册平台身份）
    python3 agate-setup.py --dry-run            # 只显示将做什么

设计约束：幂等（可反复跑）；已存在的**非本工具**文件先备份再覆盖；Windows 无符号链接
权限时退化为复制（同 `install-hook.py` 的 `_ln_sf` 语义）。
"""

import argparse
import contextlib
import os
import shutil
import subprocess
import sys
import time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import agate_common  # noqa: E402  （同目录公共库，与 agate-resolve.py 同惯例）

# 各平台配置物：{平台名: {"probe": 探测路径, "global": [...], "project": [...]}}
#   源相对协议根；目标 `~` 展开（global）或相对项目根（project）。
#   probe 存在 → 视为该平台已装（用于 --platform auto）。
#   project 为空 = 该平台无项目侧注册形态（DSH 只有全局 preset/skill；Codex 只有 skill，
#   项目侧身份靠项目自己的 AGENTS.md，不由本命令改写——那是用户文件）。
PLATFORMS = {
    "claude-code": {
        "probe": "~/.claude",
        "global": [("orchestrator-template.md", "~/.claude/agents/orchestrator.md")],
        "project": [("orchestrator-template.md", ".claude/agents/orchestrator.md")],
    },
    "opencode": {
        "probe": "~/.config/opencode",
        "global": [("orchestrator-template.md", "~/.config/opencode/agents/orchestrator.md")],
        "project": [("orchestrator-template.md", ".opencode/agents/orchestrator.md")],
    },
    "dsh": {
        "probe": "~/.dsh",
        "global": [
            ("assets/templates/dsh/agent.cordis.yml", "~/.dsh/.agent-presets/agate/agent.cordis.yml"),
            ("assets/templates/dsh/preset.yml", "~/.dsh/.agent-presets/agate/preset.yml"),
            ("assets/templates/dsh/SKILL.md", "~/.dsh/skills/agate-protocol/SKILL.md"),
        ],
        "project": [],
    },
    "codex": {
        # Codex 无 agent 注册机制，身份靠 skill（~/.agents/skills/ 是其共享 skill 根）。
        "probe": "~/.codex",
        "global": [("assets/templates/codex/SKILL.md", "~/.agents/skills/agate-protocol/SKILL.md")],
        "project": [],
    },
}


def _ln_sf(source, link_path, copy_mode=False):
    """`ln -sf` 等价：先移除既有目标再建软链；无权限时退化复制（同 install-hook.py）。

    返回 True = 建立了软链，False = 退化复制。
    """
    if os.path.lexists(link_path):
        with contextlib.suppress(OSError):
            os.unlink(link_path)
    if copy_mode:
        shutil.copyfile(source, link_path)
        return False
    try:
        os.symlink(source, link_path)
        return True
    except OSError:
        shutil.copyfile(source, link_path)
        return False


def _backup(path):
    """已存在的**非软链**文件 → 备份为 `{path}.bak.{epoch}`（不静默丢用户内容）。"""
    if os.path.isfile(path) and not os.path.islink(path):
        backup = f"{path}.bak.{int(time.time())}"
        shutil.copyfile(path, backup)
        print(f"  已备份现有文件 → {backup}")


def _detect_platforms():
    """探测已装平台：probe 路径存在即纳入。"""
    return [n for n, cfg in PLATFORMS.items()
            if os.path.isdir(os.path.expanduser(cfg["probe"]))]


def _protocol_root():
    """解析协议根（复用 agate_common 三层解析，与 agate-resolve.py 同一契约）。"""
    info = agate_common.resolve_version_root()
    root = info.get("root")
    if not root:
        sys.stderr.write(
            "错误: 协议根解析失败（无 current/latest 指针；软链布局自 v0.73.0 起不再支持）\n"
            "       先跑 bash install.sh 进入版本管理布局\n"
        )
        sys.exit(1)
    # env 覆盖层（AGATE_ROOT / AGATE_HOME）不校验存在性——显式指定错路径时
    # resolve 仍返回该路径。本命令要在其下找 orchestrator-template.md / assets/，
    # 故在此 fail-closed，避免"全部源文件不存在→逐个跳过"的误导性输出。
    if not os.path.isdir(root) or not os.path.isfile(os.path.join(root, "orchestrator-template.md")):
        sys.stderr.write(
            f"错误: 协议根无效: {root}\n"
            f"       （须是含 orchestrator-template.md 的目录；检查 AGATE_ROOT/AGATE_HOME 是否指错）\n"
        )
        sys.exit(1)
    return root, info.get("version", ""), info.get("reason", "")


def _install_hook(proto_root, dry_run):
    """装 git hook（L3 项目侧）——复用唯一安装脚本，不重复实现。"""
    installer = os.path.join(proto_root, "scripts", "install-hook.py")
    if not os.path.isfile(installer):
        sys.stderr.write(f"错误: {installer} 不存在（协议根={proto_root}）\n")
        sys.exit(1)
    if dry_run:
        print("  [dry-run] 将执行: python3 <协议根>/scripts/install-hook.py")
        return
    # 不传 agate_root：install-hook.py 默认 ~/.agate（根 scripts/ 副本，稳定入口）
    proc = subprocess.run(
        [sys.executable, installer],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    for line in (proc.stdout or "").splitlines():
        print(f"  {line}")
    if proc.returncode != 0:
        sys.stderr.write((proc.stderr or "") + "\n")
        sys.stderr.write("⚠️  hook 安装失败（不在 git 仓库？）——平台身份注册不受影响\n")


def _register_platform(name, proto_root, scope, dry_run, copy_mode):
    """注册单个平台身份。scope ∈ {global, project}。返回 (成功数, 失败数)。"""
    links = PLATFORMS[name][scope]
    if not links:
        print(f"  （{name} 无 {scope} 侧注册形态，跳过）")
        return 0, 0
    ok = fail = 0
    for src_rel, dst_spec in links:
        src = os.path.join(proto_root, src_rel)
        dst = os.path.expanduser(dst_spec) if dst_spec.startswith("~") else os.path.abspath(dst_spec)
        if not os.path.isfile(src):
            sys.stderr.write(f"  ⚠️  源不存在，跳过: {src}\n")
            fail += 1
            continue
        if dry_run:
            print(f"  [dry-run] {dst}  →  {src}")
            ok += 1
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        _backup(dst)
        linked = _ln_sf(src, dst, copy_mode=copy_mode)
        kind = "软链" if linked else "复制（无符号链接权限）"
        print(f"  ✅ {dst}  →  {src}  [{kind}]")
        ok += 1
    return ok, fail


def main():
    ap = argparse.ArgumentParser(
        description="Agateon 接入：平台身份注册（全局）+ git hook（项目侧）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--platform", default="auto",
                    help=f"逗号分隔的平台名，或 auto 探测（可选: {', '.join(PLATFORMS)}）")
    ap.add_argument("--scope", choices=("all", "global", "project"), default="all",
                    help="all=平台身份+hook（默认）；global=只注册全局身份；project=只注册项目侧+hook")
    ap.add_argument("--dry-run", action="store_true", help="只显示将做什么，不落盘")
    args = ap.parse_args()

    proto_root, version, reason = _protocol_root()
    print(f"协议根: {proto_root}")
    print(f"版本: {version or '(未标注)'}  原因: {reason}\n")

    rc = 0

    # ── L2 平台身份注册 ───────────────────────────────────────────────────
    #   all（默认）/global = 全局配置目录，一次装好所有项目可用（模板跨项目一致，ADR-008）
    #   project            = 项目内目录（.claude/ / .opencode/），适合按项目钉不同版本的场景
    #   all 用 global 而非"两者都注册"——两个 scope 同时存在时项目侧会遮蔽全局，纯冗余。
    id_scope = "project" if args.scope == "project" else "global"
    if args.platform == "auto":
        targets = _detect_platforms()
        if not targets:
            print("未探测到已装平台（~/.claude / ~/.config/opencode / ~/.dsh / ~/.codex 均不存在）")
            print("如平台装在他处，用 --platform 显式指定\n")
    else:
        targets = [p.strip() for p in args.platform.split(",") if p.strip()]
        unknown = [p for p in targets if p not in PLATFORMS]
        if unknown:
            sys.stderr.write(f"错误: 未知平台 {unknown}（可选: {', '.join(PLATFORMS)}）\n")
            sys.exit(2)
    for name in targets:
        print(f"平台 {name}（{id_scope}）:")
        _ok, fail = _register_platform(
            name, proto_root, id_scope, args.dry_run,
            copy_mode=os.environ.get("AGATE_HOOK_COPY_MODE") == "1",
        )
        if fail:
            rc = 1
    if targets:
        print()

    # ── L3 项目侧：git hook ───────────────────────────────────────────────
    if args.scope in ("all", "project"):
        print("项目侧 git hook:")
        _install_hook(proto_root, args.dry_run)
        print()

    if args.dry_run:
        print("（dry-run：未做任何改动）")
    else:
        print("完成。新开平台会话即可用「Agateon 编排者」身份启动。")
        print("项目侧还需（按需）：.agate-version 钉版本；协议文档见 <协议根>/SETUP.md")
    return rc


if __name__ == "__main__":
    sys.exit(main())
