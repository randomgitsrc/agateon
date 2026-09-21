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
    python3 agate-setup.py --list               # 查看已装内容（全局 + 台账登记的项目）
    python3 agate-setup.py --uninstall          # 卸载：全局接入物 + 当前项目（含 hook）
    python3 agate-setup.py --uninstall --all-projects   # 卸载：全局 + 台账里**每个**项目
    python3 agate-setup.py --uninstall --purge  # 再删版本根本体（收尾，命令自删）
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
import agate_package  # noqa: E402  （安装根解析 agate_home()，与安装侧同源）

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
        return 0
    # 显式传**安装根**（而非协议根）：hook 脚本住在 `<安装根>/scripts/`（单源副本，
    # 稳定入口）。**必须显式传**——install-hook.py 的默认值是 `~/.agate`，AGATE_HOME
    # 覆盖时会指错（2026-09-21 修）。
    proc = subprocess.run(
        [sys.executable, installer, agate_package.agate_home()],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    for line in (proc.stdout or "").splitlines():
        print(f"  {line}")
    if proc.returncode != 0:
        # 必须冒泡为命令失败：hook 是 gate 的兜底层（ADR-004），静默失败会让用户
        # 以为"已接入"而实际无 gate 兜底——与模板「不要静默失败」相悖。
        sys.stderr.write((proc.stderr or "") + "\n")
        sys.stderr.write(
            "错误: hook 安装失败（常见原因：当前目录不是 git 仓库）——"
            "gate 兜底未生效；平台身份注册的结果见上方各行\n"
        )
        return proc.returncode
    return 0


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


# ── 卸载（2026-09-21）────────────────────────────────────────────────────────
#
# **对称性**：本命令装了「平台身份 + git hook」，卸载就负责清掉这两类。
# **归属验证**：删任何文件前先按**事实**证明"这是本安装装的"——台账只说"去哪找"。
#   · 软链 → realpath 落在本安装根内
#   · 复制 → 内容与权威模板一致；hook 另有 `.agate-root` 标记与指纹兜底（旧版副本）
# **用户数据红线**：`agate-workspace/`（用户的任务/复盘成果）、`.agate-version`、
#   `.agate.env`、`AGENTS.md` 等**一律不删**，只报告——删它们等于删用户的活。
# **对称回滚**：安装时把用户原有 hook 备份为 `*.bak.<epoch>`，卸载时**还原最新的那个**。

HOOK_MAP = {                       # hook 名 → 安装根 scripts/ 下的权威脚本
    "pre-commit": "pre-commit-gate.sh",
    "commit-msg": "commit-msg-self-gate.sh",
    "pre-push": "pre-push-gate.sh",
}

# 用户工作数据：只报告不删（红线）
USER_DATA = (
    ("agate-workspace", "任务 / roadmap / 技术债 / 复盘——**你的工作成果**"),
    (".agate-version", "项目钉版本声明"),
    (".agate.env", "工作区位置配置"),
    (".claude/settings.json", "可能含 orchestrator 选择，由你/团队决定"),
    ("AGENTS.md", "项目文档"),
    ("CLAUDE.md", "项目文档"),
)


def _under(path, root):
    """path 是否位于 root 之内（都按 realpath 归一；防前缀误判 /a 与 /ab）。"""
    p, r = os.path.realpath(path), os.path.realpath(root)
    return p == r or p.startswith(r + os.sep)


def _same_content(a, b):
    try:
        with open(a, "rb") as f1, open(b, "rb") as f2:
            return f1.read() == f2.read()
    except OSError:
        return False


def _read_text(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _installed_template_matches(home, src_rel, dst):
    """复制形态：内容与**任一已装版本**的权威模板一致 → 本安装所装。

    为什么要遍历各版本（而非只比 current）：产物是**装的时候**那一版的副本，升级后
    内容自然与新版不同——只比 current 会把"旧版副本"误判为"非本安装所有"而不敢删。
    """
    if not os.path.isdir(home):
        return False
    for name in sorted(os.listdir(home)):
        cand = os.path.join(home, name, "agate", *src_rel.split("/"))
        if os.path.isfile(cand) and _same_content(dst, cand):
            return True
    return False


def _owned_artifact(dst, home, src_rel):
    """平台接入产物归属判定 → (是否本安装所有, 形态说明)。"""
    if os.path.islink(dst):
        target = os.path.realpath(dst)
        if _under(target, home):
            return True, f"软链 → {target}"
        return False, f"软链指向本安装之外（{target}）"
    if _installed_template_matches(home, src_rel, dst):
        return True, "复制（内容与已装版本模板一致）"
    return False, "实体文件（内容与任何已装版本模板都不一致，可能已被你改作他用）"


def _hook_owned(hook_file, home, marker_ok):
    """hook 归属判定 → (是否本安装所有, 形态说明)。

    四级判据（从强到弱）——复制模式在 Windows 无软链语义，故不能只看 islink：
      ① 软链 → 目标落在本安装根内
      ② `.agate-root` 标记存在且指向本安装根（复制模式安装时写的兜底标记）
      ③ 内容与安装根 `scripts/` 下同名脚本一致
      ④ 内容含 agate 指纹（旧版副本，升级后内容已不同）——**保守但必要**，
         否则升级后旧副本会被判为"非本安装"，卸载就漏掉它。
    """
    if os.path.islink(hook_file):
        target = os.path.realpath(hook_file)
        if _under(target, home):
            return True, f"软链 → {target}"
        return False, f"软链指向本安装之外（{target}）"
    name = os.path.basename(hook_file)
    src = os.path.join(home, "scripts", HOOK_MAP.get(name, ""))
    if os.path.isfile(src) and _same_content(hook_file, src):
        return True, "复制（与安装根脚本一致）"
    text = _read_text(hook_file)
    if marker_ok or "resolve-entry.py" in text or "pre-commit-gate" in text:
        return True, "复制（agate 指纹 / .agate-root 标记）"
    return False, "实体文件（无 agate 指纹，是你自己的 hook）"


def _restore_backup(hook_file, dry_run):
    """还原 agateon 安装时备份的**最新**用户原 hook（`*.bak.<epoch>`）。返回说明或 None。"""
    parent = os.path.dirname(hook_file)
    base = os.path.basename(hook_file) + ".bak."
    try:
        cands = [e for e in os.listdir(parent) if e.startswith(base) and e[len(base):].isdigit()]
    except OSError:
        return None
    if not cands:
        return None
    newest = max(cands, key=lambda e: int(e[len(base):]))
    src = os.path.join(parent, newest)
    if dry_run:
        return f"将还原你原有的 hook: {newest}"
    try:
        os.replace(src, hook_file)
        return f"已还原你原有的 hook（来自 {newest}）"
    except OSError as exc:
        return f"⚠️ 还原备份失败: {exc}"


def _uninstall_platforms(home, scope, dry_run):
    """卸载平台接入物。scope ∈ {global, project}。返回 (删除数, 保留数)。"""
    removed = kept = 0
    for name, cfg in PLATFORMS.items():
        for src_rel, dst_spec in cfg.get(scope) or []:
            dst = (os.path.expanduser(dst_spec) if dst_spec.startswith("~")
                   else os.path.abspath(dst_spec))
            if not os.path.lexists(dst):
                continue
            owned, why = _owned_artifact(dst, home, src_rel)
            if not owned:
                # 不删——可能已被用户改作他用；如实报告并交给人判断
                print(f"  ⏭️  [{name}] 保留 {dst}\n      理由: {why}")
                kept += 1
                continue
            if dry_run:
                print(f"  [dry-run] [{name}] 将删除 {dst}（{why}）")
            else:
                try:
                    os.unlink(dst)
                    print(f"  ✅ [{name}] 已删除 {dst}（{why}）")
                except OSError as exc:
                    sys.stderr.write(f"  ⚠️  [{name}] 删除失败 {dst}: {exc}\n")
                    kept += 1
                    continue
            removed += 1
            _prune_empty_dirs(os.path.dirname(dst), home, dry_run)
    return removed, kept


# agateon 在平台目录下的**专属命名空间**——只有这些目录（空了才）可被清。
# 为什么不向上递归清理：所有权边界不可靠——`~/.agents`（Codex 的共享 skill 根）
# 与 `~/.dsh/.agent-presets`（DSH 的 preset 命名空间）都不是 agateon 的目录，
# "清空后顺手删掉"属于越界（2026-09-21 自查 + 测试双重确认）。留一个空目录无害，
# 删掉用户/平台的目录有害。
_OWNED_DIR_NAMES = frozenset({"agate", "agate-protocol"})


def _prune_empty_dirs(path, home, dry_run):
    """仅清理**空掉的 agateon 专属目录**（`…/agate` / `…/agate-protocol`），不向上递归。

    保守取向：宁留空目录，不越界删平台/用户目录（见 `_OWNED_DIR_NAMES` 的理由）。
    """
    if os.path.basename(os.path.realpath(path)) not in _OWNED_DIR_NAMES:
        return
    cur = os.path.realpath(path)
    try:
        if os.listdir(cur):
            return
    except OSError:
        return
    if dry_run:
        print(f"  [dry-run] 将删除空目录 {cur}")
        return
    with contextlib.suppress(OSError):
        os.rmdir(cur)
        print(f"  ✅ 已删除空目录 {cur}")


def _uninstall_project(project_root, home, dry_run):
    """卸载单个项目侧接入物（平台产物 + hook）。**不碰用户数据。**"""
    print(f"\n项目 {project_root}:")
    _uninstall_platforms(home, "project", dry_run)

    hook_dir = os.path.join(project_root, ".git", "hooks")
    marker = os.path.join(hook_dir, ".agate-root")
    marker_ok = os.path.isfile(marker) and _under(_read_text(marker).strip(), home)
    touched_hook = False
    for hook_name in HOOK_MAP:
        hook_file = os.path.join(hook_dir, hook_name)
        if not os.path.lexists(hook_file):
            continue
        owned, why = _hook_owned(hook_file, home, marker_ok)
        if not owned:
            print(f"  ⏭️  保留 {hook_file}\n      理由: {why}")
            continue
        if dry_run:
            print(f"  [dry-run] 将删除 {hook_file}（{why}）")
        else:
            try:
                os.unlink(hook_file)
                print(f"  ✅ 已删除 {hook_file}（{why}）")
            except OSError as exc:
                sys.stderr.write(f"  ⚠️  删除失败 {hook_file}: {exc}\n")
                continue
        touched_hook = True
        restored = _restore_backup(hook_file, dry_run)
        if restored:
            print(f"      {restored}")
    if touched_hook and os.path.lexists(marker) and marker_ok and not dry_run:
        with contextlib.suppress(OSError):
            os.unlink(marker)
            print(f"  ✅ 已删除 {marker}（复制模式标记）")

    # 用户数据：只报告（红线——删这些等于删用户的活）
    present = [f"{rel}（{desc}）" for rel, desc in USER_DATA
               if os.path.lexists(os.path.join(project_root, rel))]
    if present:
        print("  ℹ️  以下属于**你的工作数据**，卸载不删（如需清理请自行处理）:")
        for item in present:
            print(f"      · {item}")


def _list_installed(home):
    """列出已装内容：全局接入物 + 台账登记的项目。"""
    print(f"安装根: {home}\n")
    print("全局接入物:")
    found = False
    for name, cfg in PLATFORMS.items():
        for src_rel, dst_spec in cfg.get("global") or []:
            dst = os.path.expanduser(dst_spec)
            if not os.path.lexists(dst):
                continue
            owned, why = _owned_artifact(dst, home, src_rel)
            mark = "✅" if owned else "⚠️ 非本安装"
            print(f"  {mark} [{name}] {dst}  ({why})")
            found = True
    if not found:
        print("  （无）")

    entries = agate_common.read_projects()
    print(f"\n台账登记的项目（{len(entries)} 个，位于 {agate_common.project_ledger_path()}）:")
    if not entries:
        print("  （无——用 --scope project 安装时会自动登记）")
    for e in entries:
        state = "存在" if os.path.isdir(e["path"]) else "⚠️ 目录已不存在"
        plats = ", ".join(e.get("platforms") or []) or "-"
        print(f"  · {e['path']}  [{state}] 平台: {plats}  最近: {e.get('last_seen', '-')}")


def _git_root():
    """当前目录所在 git 仓库根（不在仓库返回 None）。"""
    rc, out = agate_common.run_git(["rev-parse", "--show-toplevel"])
    return out.strip() if rc == 0 and out.strip() else None


def _run_uninstall(args):
    """卸载入口。返回进程退出码。"""
    home = agate_package.agate_home()
    if not os.path.isdir(home):
        sys.stderr.write(f"错误: 安装根不存在: {home}\n")
        return 1
    print(f"安装根: {home}")
    if args.dry_run:
        print("（dry-run：不会真的删除）")
    print()

    removed = kept = 0
    # ── 全局接入物 ──
    if args.scope in ("all", "global"):
        print("全局接入物:")
        r, k = _uninstall_platforms(home, "global", args.dry_run)
        removed += r
        kept += k
        if not (r or k):
            print("  （无）")

    # ── 项目侧 ──
    projects = []
    if args.all_projects:
        projects = [e["path"] for e in agate_common.read_projects()]
        missing = [p for p in projects if not os.path.isdir(p)]
        projects = [p for p in projects if os.path.isdir(p)]
        if not projects and not missing:
            print("\n台账为空（无项目侧安装记录）")
        for p in missing:
            print(f"\n项目 {p}: ⚠️ 目录已不存在，从台账移除")
            if not args.dry_run:
                agate_common.forget_project(p)
    elif args.scope in ("all", "project"):
        root = _git_root()
        if root:
            projects = [root]
        else:
            print("\n当前目录不是 git 仓库——项目侧跳过（要清全部项目用 --all-projects）")

    for proj in projects:
        _uninstall_project(proj, home, args.dry_run)
        if not args.dry_run:
            agate_common.forget_project(proj)

    # ── 汇总 + 本体收尾 ──
    print()
    if kept:
        print(f"⚠️  有 {kept} 项**未删除**（无法证明归属本安装，见上方理由）——请人工确认。")
    verb = "将删除" if args.dry_run else "已删除"
    print(f"接入物：{verb} {removed} 项，保留 {kept} 项。")

    if args.purge:
        # 守卫：只在"确实像 agate 安装根"时才删（防 AGATE_HOME 指错而清掉无关目录）
        looks_like_root = os.path.isfile(os.path.join(home, "scripts", "agate-install.py"))
        if not looks_like_root:
            sys.stderr.write(
                f"⚠️  拒绝 --purge：{home} 不像 agate 安装根"
                f"（缺 scripts/agate-install.py）——请检查 AGATE_HOME\n"
            )
            return 1
        if args.dry_run:
            print(f"[dry-run] 将删除安装根 {home}（含 repo/ 与各版本目录）")
        else:
            print(f"删除安装根 {home}（含 repo/ 与各版本目录）…")
            try:
                shutil.rmtree(home)
                print("✅ 安装根已删除——agateon 已完全卸载。")
            except OSError as exc:
                sys.stderr.write(f"⚠️  安装根删除失败: {exc}（可手动: rm -rf {home}）\n")
                return 1
    else:
        print(f"如需连本体一起删（收尾）: python3 {home}/scripts/agate-setup.py --uninstall --purge")
        print(f"  或手动: rm -rf {home}")

    # 退出码恒 0：「保留」是**安全拒绝**（无法证明归属就不删），不是失败；
    # 真失败（rmtree 出错 / 安装根不存在）已在上面各自 return 1。
    return 0


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
    ap.add_argument("--list", action="store_true", help="列出已装内容（全局 + 台账项目），不落盘")
    ap.add_argument("--uninstall", action="store_true", help="卸载：清本命令装过的接入物")
    ap.add_argument("--all-projects", action="store_true",
                    help="配合 --uninstall：卸载台账里**每个**项目的接入物（解决多项目散落）")
    ap.add_argument("--purge", action="store_true",
                    help="配合 --uninstall：清完接入物后再删版本根本体（收尾；命令会自删）")
    args = ap.parse_args()

    # ── 只读模式：--list ──────────────────────────────────────────────────
    if args.list:
        _list_installed(agate_package.agate_home())
        return 0

    # ── 卸载模式 ──────────────────────────────────────────────────────────
    if args.uninstall:
        return _run_uninstall(args)

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
        if _install_hook(proto_root, args.dry_run) != 0:
            rc = 1
        print()

    # ── 台账登记（项目侧安装才需要：卸载时要知道项目在哪）──────────────────
    if not args.dry_run and args.scope in ("all", "project"):
        project_root = _git_root()
        if project_root:
            if agate_common.record_project(project_root, targets, scope="project"):
                print(f"已登记到安装台账: {project_root}")
            else:
                print(f"⚠️  台账登记失败（不影响本次安装）: {agate_common.project_ledger_path()}")
        else:
            print("提示: 当前目录不是 git 仓库，hook 未装、台账未登记")

    if args.dry_run:
        print("（dry-run：未做任何改动）")
    elif rc == 0:
        home = agate_package.agate_home()
        print("完成。新开平台会话即可用「Agateon 编排者」身份启动。")
        print("项目侧还需（按需）：.agate-version 钉版本；协议文档见 <协议根>/SETUP.md")
        # 打印**真实**路径（AGATE_HOME 覆盖时 ~/.agate 是错的）+ 卸载入口，
        # 免用户装完不知装到哪、也不知怎么卸（2026-09-21）。
        print(f"安装根: {home}")
        print(f"卸载:   python3 {home}/scripts/agate-setup.py --uninstall --all-projects")
    else:
        print("⚠️  部分步骤失败（见上方 stderr）——未完成，修复后重跑本命令（幂等）。")
    return rc


if __name__ == "__main__":
    sys.exit(main())
