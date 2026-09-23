# tests/unit/test_platform_setup.py — 平台接入命令 + 适配层去漂移守护（2026-09-21）
#
# 背景：SETUP.md 此前是逐平台**手工步骤**（ln -sf / cp），且各平台配置物形态不同
# （Claude Code / OpenCode = agent md；DSH = preset + skill；Codex = skill）。
# 新增 `agate/scripts/agate-setup.py` 把这些步骤命令化——不再让 agent 照文档手工执行。
#
# 同时守护**适配层不复制协议内容**：DSH 的 persona 曾复制「会话开始步骤 + 职责边界」，
# 与 orchestrator-template.md 两处维护 → TAG0037 改了模板的协议根回退路径、DSH 副本
# 未跟（实测把版本根 ~/.agate 当协议根）。适配层只做「指向 + 平台差异」。
#
# 平台无关原则：
#   1. 不用系统临时目录——一律 pytest tmp_path
#   2. 不假设符号链接语义——注册用例只断言「目标可读」，不断言 islink；
#      复制模式分支由 AGATE_HOOK_COPY_MODE=1 显式驱动（跨平台确定性）
#   3. 不触碰真实 HOME——run_cli 默认隔离 HOME；假平台目录建在 tmp_path 内
#   4. 不调用真实平台 CLI——只断言文件落地与内容


import importlib.util
import json
import os
import shutil
import sys

import pytest
import yaml

from conftest import PROTOCOL_RULE_MARKERS

_MISSING = object()  # sys.modules 哨兵（区分「不存在」与「值为 None」）

SETUP_PY = ("scripts", "agate-setup.py")
CODEX_TEMPLATE = ("assets", "templates", "codex", "SKILL.md")


# ── Codex 适配层 ─────────────────────────────────────────────────────────────


def _codex_skill(agate_root):
    p = agate_root.joinpath(*CODEX_TEMPLATE)
    assert p.is_file(), f"Codex 适配层缺失: {p}"
    return p.read_text(encoding="utf-8")


def test_codex_skill_frontmatter_valid(agate_root):
    """Codex 适配层须为可发现的 skill（frontmatter name/description 非空）。"""
    text = _codex_skill(agate_root)
    assert text.startswith("---"), "缺 frontmatter 块"
    fm = yaml.safe_load(text.split("---")[1])
    assert fm.get("name") == "agate-protocol", "frontmatter name 应为 agate-protocol"
    assert fm.get("description"), "frontmatter 缺 description"


def test_codex_skill_states_explicit_dispatch_requirement(agate_root):
    """Codex 特有硬约束：multi_agent 默认禁止派发，适配层必须显式写明「要求派发」。

    实测（2026-09-21，codex-cli 0.153.4）`codex debug prompt-input` 输出的会话上下文含
    `<multi_agent_mode>`：「Do not spawn sub-agents unless the user or applicable
    AGENTS.md/skill instructions explicitly ask for sub-agents...」。
    Agateon 的整个模型建立在主 Agent 派发 subagent 之上——不显式要求则**静默不派发**，
    P0-P8 直接失效。故该要求必须成文，且必须点出 `spawn_agent` 与 multi_agent 语义。
    """
    text = _codex_skill(agate_root)
    assert "multi_agent" in text, "须说明 Codex 的 multi_agent 默认语义"
    assert "spawn_agent" in text, "须点名 Codex 的派发工具 spawn_agent"


def test_codex_skill_points_to_template_and_carries_mapping(agate_root):
    """Codex 适配层：不复述协议规则，且**必须**自带工具映射（Codex 无 persona 层）。

    与 DSH 的判据差异是**架构差异而非两套标准**（理由见 test_dsh_preset 模组级注释）：
    DSH 有 persona 层 → 映射单一来源在 persona，其 SKILL.md **不得**再有映射表；
    Codex 无 agent 注册机制（无 persona 层）→ 映射在本 skill 内（这一点由人读文档保证，
    机械判据只做否定断言：不得复述协议规则句）。

    锚点集与本仓 DSH 侧共享（`PROTOCOL_RULE_MARKERS` 同源词表），消除"同一原则两套标准"。
    """
    text = _codex_skill(agate_root)
    assert "orchestrator-template.md" in text, "须指向 orchestrator-template.md"
    # 协议规则句：与 DSH 侧同一锚点集（模板中真实存在、旧适配层逐字复述过）
    for forbidden in PROTOCOL_RULE_MARKERS:
        assert forbidden not in text, (
            f"Codex 适配层复述了协议规则「{forbidden}」——单一来源在模板"
        )


# ── agate-setup.py：平台身份注册 ─────────────────────────────────────────────


def _fake_homes(tmp_path):
    """建四个平台的假全局目录（判定"平台已装"的探测点）。"""
    home = tmp_path / "home"
    for rel in (".claude", ".config/opencode", ".dsh", ".codex"):
        (home / rel).mkdir(parents=True, exist_ok=True)
    # Codex 的 skill 落到 ~/.agents（跨工具共享根），也需存在
    (home / ".agents").mkdir(parents=True, exist_ok=True)
    return home


def _run_setup(run_cli, python_exe, agate_scripts, home, agate_root, *extra, copy_mode=False):
    env = {"HOME": str(home), "USERPROFILE": str(home), "AGATE_ROOT": str(agate_root)}
    if copy_mode:
        env["AGATE_HOOK_COPY_MODE"] = "1"
    return run_cli(python_exe, str(agate_scripts / "agate-setup.py"), *extra, env=env)


REGISTERED = (
    ".claude/agents/orchestrator.md",
    ".config/opencode/agents/orchestrator.md",
    ".dsh/.agent-presets/agate/agent.cordis.yml",
    ".dsh/.agent-presets/agate/preset.yml",
    ".dsh/skills/agate-protocol/SKILL.md",
    ".agents/skills/agate-protocol/SKILL.md",
)


def test_setup_registers_all_detected_platforms(run_cli, python_exe, agate_scripts,
                                                agate_root, tmp_path):
    """四平台身份注册：目标须**可读**（断链会让平台静默找不到 orchestrator）。"""
    home = _fake_homes(tmp_path)
    result = _run_setup(run_cli, python_exe, agate_scripts, home, agate_root, "--scope", "global")
    assert result.returncode == 0, result.stderr
    for rel in REGISTERED:
        target = home / rel
        assert target.exists(), f"未注册或断链: {rel}"
        assert target.read_text(encoding="utf-8").strip(), f"注册物为空: {rel}"


def test_setup_is_idempotent(run_cli, python_exe, agate_scripts, agate_root, tmp_path):
    """幂等：重跑不报错、不产生重复备份（已存在的是软链 → 非"非本工具文件"）。"""
    home = _fake_homes(tmp_path)
    for _ in range(2):
        r = _run_setup(run_cli, python_exe, agate_scripts, home, agate_root, "--scope", "global")
        assert r.returncode == 0, r.stderr
    backups = list(home.rglob("*.bak.*"))
    assert not backups, f"幂等重跑不应产生备份文件: {backups}"


def test_setup_copy_mode_when_no_symlink_permission(run_cli, python_exe, agate_scripts,
                                                    agate_root, tmp_path):
    """Windows 无符号链接权限 → 退化为复制，内容仍可读（跨平台确定性由 env 驱动）。"""
    home = _fake_homes(tmp_path)
    r = _run_setup(run_cli, python_exe, agate_scripts, home, agate_root,
                   "--platform", "claude-code", "--scope", "global", copy_mode=True)
    assert r.returncode == 0, r.stderr
    target = home / ".claude/agents/orchestrator.md"
    assert target.exists() and not target.is_symlink(), "复制模式应产生实体文件"
    assert "orchestrator" in target.read_text(encoding="utf-8")


def test_setup_backs_up_existing_foreign_file(run_cli, python_exe, agate_scripts,
                                              agate_root, tmp_path):
    """既有非本工具文件先备份再覆盖（不静默丢用户内容）。"""
    home = _fake_homes(tmp_path)
    target = home / ".claude/agents/orchestrator.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("my own custom agent\n", encoding="utf-8")
    r = _run_setup(run_cli, python_exe, agate_scripts, home, agate_root,
                   "--platform", "claude-code", "--scope", "global")
    assert r.returncode == 0, r.stderr
    backups = list(target.parent.glob("orchestrator.md.bak.*"))
    assert backups, "应备份既有非本工具文件"
    assert "my own custom agent" in backups[0].read_text(encoding="utf-8")


def test_setup_dry_run_writes_nothing(run_cli, python_exe, agate_scripts, agate_root, tmp_path):
    home = _fake_homes(tmp_path)
    r = _run_setup(run_cli, python_exe, agate_scripts, home, agate_root,
                   "--scope", "global", "--dry-run")
    assert r.returncode == 0, r.stderr
    for rel in REGISTERED:
        assert not (home / rel).exists(), f"dry-run 不应落盘: {rel}"


def test_setup_unknown_platform_exit_2(run_cli, python_exe, agate_scripts, agate_root, tmp_path):
    home = _fake_homes(tmp_path)
    r = _run_setup(run_cli, python_exe, agate_scripts, home, agate_root,
                   "--platform", "nope", "--scope", "global")
    assert r.returncode == 2, f"未知平台应 exit 2（用法错误），实际 {r.returncode}"


def test_setup_unresolvable_root_fail_closed(run_cli, python_exe, agate_scripts, tmp_path):
    """无 current/latest 指针且无 AGATE_ROOT → fail-closed（exit 1），不静默降级。"""
    home = tmp_path / "home"
    home.mkdir()
    # 显式给一个不存在的 AGATE_ROOT → 解析失败
    r = run_cli(python_exe, str(agate_scripts / "agate-setup.py"), "--scope", "global",
                env={"HOME": str(home), "USERPROFILE": str(home),
                     "AGATE_ROOT": str(tmp_path / "nonexistent")})
    assert r.returncode == 1, f"协议根解析失败应 exit 1，实际 {r.returncode}"


def test_setup_hook_failure_propagates_nonzero(run_cli, python_exe, agate_scripts,
                                               agate_root, tmp_path):
    """hook 安装失败须冒泡为非 0（回归：曾漏，硬失败被报成"完成"+exit 0）。

    hook 是 gate 的兜底层（adr.md ADR-004）——静默失败会让用户以为"已接入"而实际无兜底。
    构造：在**非 git 仓库**目录跑 `--scope project`（身份注册到项目侧 + 装 hook）→ hook 必失败。
    """
    home = _fake_homes(tmp_path)
    notgit = tmp_path / "not-a-repo"
    notgit.mkdir()
    # cwd 指向非 git 目录 → install-hook.py 必然失败
    r = run_cli(python_exe, str(agate_scripts / "agate-setup.py"),
                "--platform", "claude-code", "--scope", "project",
                cwd=str(notgit),
                env={"HOME": str(home), "USERPROFILE": str(home), "AGATE_ROOT": str(agate_root)})
    assert r.returncode != 0, (
        f"非 git 目录下 hook 装不上，命令须 exit != 0（曾静默 exit 0）；实际 {r.returncode}"
    )
    assert "未完成" in (r.stdout + r.stderr), "失败时不应打印「完成」，须给出明确失败收尾语"


# ── 卸载（2026-09-21）────────────────────────────────────────────────────────
#
# 设计要点（详见 agate-setup.py 的卸载节注释）：
#   · **对称**：装什么卸什么（平台接入物 + hook）
#   · **归属验证**：删前按事实验证"这是本安装装的"，台账只作索引
#   · **用户数据红线**：agate-workspace/ 等只报告不删
#   · **对称回滚**：还原安装时备份的用户原 hook

_ENTRY_SCRIPTS = (
    "agate-setup.py", "install-hook.py", "agate_common.py", "agate_package.py",
    "resolve-entry.py", "agate-install.py",
    "pre-commit-gate.sh", "commit-msg-self-gate.sh", "pre-push-gate.sh",
)


def _fake_install_root(tmp_path, agate_root):
    """假安装根（AGATE_HOME）：`v9.9.9/agate`（协议根）+ `scripts/`（入口副本）+ 指针。

    必须做出**真实布局**——`resolve_version_root` 与 `--purge` 守卫都按真实结构判定，
    简化夹具会"因错误的原因通过"（例如协议根缺 `scripts/` 时两形态探测回退到错误路径）。
    """
    home = tmp_path / "home"
    iroot = home / ".agate"
    scripts = iroot / "scripts"
    scripts.mkdir(parents=True)
    for name in _ENTRY_SCRIPTS:
        src = agate_root / "scripts" / name
        if src.is_file():
            shutil.copyfile(src, scripts / name)
    vroot = iroot / "v9.9.9" / "agate"
    shutil.copytree(agate_root / "assets", vroot / "assets")
    shutil.copyfile(agate_root / "orchestrator-template.md", vroot / "orchestrator-template.md")
    # 协议根下也要有 scripts/（`_install_hook` 经 `<协议根>/scripts/install-hook.py` 调用，
    # 且两形态探测需要该目录存在——空目录会让 setup fail-closed）
    vscripts = vroot / "scripts"
    vscripts.mkdir(parents=True)
    for name in _ENTRY_SCRIPTS:
        src = agate_root / "scripts" / name
        if src.is_file():
            shutil.copyfile(src, vscripts / name)
    (iroot / "latest").write_text("v9.9.9\n", encoding="utf-8")
    (iroot / "current").write_text("latest\n", encoding="utf-8")
    return home, iroot


def _env(home, iroot):
    """隔离环境：假 HOME + AGATE_HOME。

    **必须清空 AGATE_ROOT**：它在解析链里优先于 AGATE_HOME，若从外环境（本机/CI 常设）
    继承进来，协议根会指向真实仓库而非假安装根——那样产物软链就不在假 home 内，
    归属校验会（正确地）拒绝删除，测试表现为莫名其妙的失败。
    """
    return {"HOME": str(home), "USERPROFILE": str(home),
            "AGATE_HOME": str(iroot), "AGATE_ROOT": ""}


def _setup(run_cli, python_exe, agate_scripts, home, iroot, *extra,
           cwd=None, copy_mode=False, extra_env=None):
    env = _env(home, iroot)
    if copy_mode:
        env["AGATE_HOOK_COPY_MODE"] = "1"
    if extra_env:
        env.update(extra_env)
    return run_cli(python_exe, str(agate_scripts / "agate-setup.py"), *extra, env=env, cwd=cwd)


def test_uninstall_removes_installed_artifacts(run_cli, python_exe, agate_scripts,
                                               agate_root, tmp_path):
    """装→卸对称：全局接入物全部清除。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    # 只装全局（不涉 hook）——本用例聚焦"接入物对称清除"，不引入 git 依赖
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "global").returncode == 0
    installed = [f for f in REGISTERED if (home / f).exists()]
    assert len(installed) == len(REGISTERED), f"前置：应全部装上，实际 {installed}"

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "global")
    assert result.returncode == 0, result.output
    left = [f for f in REGISTERED if os.path.lexists(home / f)]
    assert not left, f"卸载后不应残留接入物: {left}\n{result.output}"


def test_uninstall_preserves_foreign_file(run_cli, python_exe, agate_scripts,
                                          agate_root, tmp_path):
    """**安全拒绝**：产物路径上是用户自己的文件（内容与模板不符）→ 不删 + 报告。

    这是卸载最重要的安全性：宁可不删（用户可手动清），也不能误删用户的东西。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    target = home / ".claude/agents/orchestrator.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# 我的自定义内容\n", encoding="utf-8")

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "global")
    assert result.returncode == 0, "保留不是失败（安全拒绝）——退出码应为 0"
    assert target.is_file(), "非本安装的文件不得被删"
    assert target.read_text(encoding="utf-8") == "# 我的自定义内容\n", "内容须原样"
    assert "保留" in result.output, f"须如实报告保留及理由:\n{result.output}"


def test_uninstall_preserves_user_work_data(run_cli, python_exe, agate_scripts,
                                            agate_root, git_repo, tmp_path):
    """**红线**：用户工作数据（任务成果 / 钉版声明 / 项目文档）绝不被删。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    (proj / "agate-workspace" / "tasks").mkdir(parents=True)
    (proj / "agate-workspace" / "tasks" / "t1.md").write_text("我的成果\n", encoding="utf-8")
    (proj / ".agate-version").write_text("agate: v9.9.9\n", encoding="utf-8")
    (proj / "AGENTS.md").write_text("# 我的项目文档\n", encoding="utf-8")

    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  cwd=str(proj)).returncode == 0
    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--all-projects", cwd=str(proj))
    assert result.returncode == 0, result.output
    for rel in ("agate-workspace/tasks/t1.md", ".agate-version", "AGENTS.md"):
        assert (proj / rel).is_file(), f"用户数据不得被删: {rel}"
    assert "不删" in result.output, f"须明确告知用户数据被保留:\n{result.output}"


@pytest.mark.windows_smoke
def test_uninstall_restores_user_hook_backup(run_cli, python_exe, agate_scripts,
                                             agate_root, git_repo, tmp_path):
    """**对称回滚**：安装时备份的用户原 hook，卸载时还原（不留 next-worse 状态）。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    hook = proj / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho 我原有的 hook\n", encoding="utf-8")

    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  cwd=str(proj)).returncode == 0
    assert hook.read_text(encoding="utf-8") != "#!/bin/sh\necho 我原有的 hook\n", \
        "前置：hook 应已被 agateon 接管"

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--all-projects", cwd=str(proj))
    assert result.returncode == 0, result.output
    assert hook.is_file() and not hook.is_symlink(), "应还原为实体文件"
    assert "我原有的 hook" in hook.read_text(encoding="utf-8"), \
        f"须还原用户原 hook:\n{result.output}"


def test_project_install_records_ledger(run_cli, python_exe, agate_scripts,
                                        agate_root, git_repo, tmp_path):
    """项目侧安装**必须登记台账**——否则卸载无从知道项目在哪（散落问题的根因）。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  cwd=str(proj)).returncode == 0

    ledger = iroot / "installed-projects.json"
    assert ledger.is_file(), "应写台账"
    data = json.loads(ledger.read_text(encoding="utf-8"))
    paths = [e["path"] for e in data["projects"]]
    assert str(proj.resolve()) in paths or str(proj) in paths, \
        f"台账应含该项目: {paths}"


def test_uninstall_all_projects_uses_ledger(run_cli, python_exe, agate_scripts,
                                            agate_root, tmp_path):
    """**核心场景**：全局装一次 + 两个项目装了 hook → 一次卸载全部清干净。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    from conftest import GitRepo
    repos = [GitRepo(tmp_path / f"proj{i}") for i in (1, 2)]
    for r in repos:
        assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                      cwd=str(r.path)).returncode == 0
    hooks = [r.path / ".git" / "hooks" / "pre-push" for r in repos]
    assert all(os.path.lexists(h) for h in hooks), "前置：两个项目都应装上 hook"

    # 在第三个目录执行卸载——证明靠**台账**而非 cwd 定位
    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--all-projects", cwd=str(tmp_path))
    assert result.returncode == 0, result.output
    for h in hooks:
        assert not os.path.lexists(h), f"台账里的项目应被清: {h}\n{result.output}"
    data = json.loads((iroot / "installed-projects.json").read_text(encoding="utf-8"))
    assert data["projects"] == [], "卸载后台账应清空"


def test_uninstall_drops_missing_ledger_project(run_cli, python_exe, agate_scripts,
                                                agate_root, tmp_path):
    """台账指向已删除的目录 → 报告并从台账移除（不留死条目）。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    gone = tmp_path / "gone-proj"
    (iroot / "installed-projects.json").write_text(
        json.dumps({"schema": 1, "projects": [{"path": str(gone), "first_seen": "x",
                                               "last_seen": "x", "platforms": [],
                                               "scope": "project"}]}),
        encoding="utf-8")

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--all-projects")
    assert result.returncode == 0, result.output
    assert str(gone) in result.output, "应报告该目录已不存在"
    data = json.loads((iroot / "installed-projects.json").read_text(encoding="utf-8"))
    assert data["projects"] == [], "死条目应被移除"


def test_uninstall_dry_run_removes_nothing(run_cli, python_exe, agate_scripts,
                                           agate_root, tmp_path):
    """--dry-run 只报告不落盘（卸载是不可逆操作，必须先能预览）。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "global").returncode == 0
    before = sorted(f for f in REGISTERED if os.path.lexists(home / f))

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "global", "--dry-run")
    assert result.returncode == 0, result.output
    after = sorted(f for f in REGISTERED if os.path.lexists(home / f))
    assert before == after, "--dry-run 不得改动任何文件"


def test_purge_refuses_when_not_install_root(run_cli, python_exe, agate_scripts,
                                             agate_root, tmp_path):
    """--purge 守卫：AGATE_HOME 指到不像安装根的目录 → 拒绝删除（防误删）。"""
    home = _fake_homes(tmp_path)
    _fake_install_root(tmp_path, agate_root)   # 建出正常安装根（本用例只用到 bogus）
    bogus = tmp_path / "not-a-root"
    bogus.mkdir()
    (bogus / "重要文件.txt").write_text("别删我\n", encoding="utf-8")

    result = _setup(run_cli, python_exe, agate_scripts, home, bogus,
                    "--uninstall", "--purge")
    assert result.returncode == 1, "不像安装根时应 fail-closed"
    assert bogus.is_dir() and (bogus / "重要文件.txt").is_file(), "拒绝后不得删任何东西"


def test_list_reports_installed_state(run_cli, python_exe, agate_scripts,
                                      agate_root, git_repo, tmp_path):
    """--list 只读：报告已装接入物 + 台账项目，且退出码 0。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  cwd=str(git_repo.path)).returncode == 0

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot, "--list")
    assert result.returncode == 0, result.output
    assert "全局接入物" in result.output
    assert str(git_repo.path) in result.output, f"应列出台账项目:\n{result.output}"


def test_custom_agate_home_install_and_uninstall(run_cli, python_exe, agate_scripts,
                                                agate_root, tmp_path):
    """**自定义安装根**（`AGATE_HOME`）：装/列/卸都跟随该根，不误指 `~/.agate`。

    这条守的是本轮修的硬编码缺口：`AGATE_HOME` 早在 DEBT0042 就支持，但安装/R提示里
    写死 `~/.agate`（覆盖时给出不存在的命令）、`install-hook.py` 默认根也写死
    `~/.agate`（覆盖时装到错的地方）。用**非默认**根名（`custom-root`）确保任何残留的
    `~/.agate` 硬编码都会暴露。
    """
    home = _fake_homes(tmp_path)                    # 平台探测点
    # 非默认根名（刻意不用 .agate）——硬编码 ~/.agate 的实现在此必然失败
    iroot = home / "custom-root"
    iroot.mkdir()
    scripts = iroot / "scripts"
    scripts.mkdir()
    for name in _ENTRY_SCRIPTS:
        src = agate_root / "scripts" / name
        if src.is_file():
            shutil.copyfile(src, scripts / name)
    vroot = iroot / "v9.9.9" / "agate"
    shutil.copytree(agate_root / "assets", vroot / "assets")
    shutil.copyfile(agate_root / "orchestrator-template.md", vroot / "orchestrator-template.md")
    (vroot / "scripts").mkdir(parents=True)
    for name in _ENTRY_SCRIPTS:
        src = agate_root / "scripts" / name
        if src.is_file():
            shutil.copyfile(src, vroot / "scripts" / name)
    (iroot / "latest").write_text("v9.9.9\n", encoding="utf-8")
    (iroot / "current").write_text("latest\n", encoding="utf-8")

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot, "--scope", "global")
    assert result.returncode == 0, result.output
    # 接入物必须指向**自定义根**内的模板（指向 ~/.agate 即硬编码未除）
    target = os.path.realpath(home / ".claude/agents/orchestrator.md")
    assert str(iroot) in target, f"接入物应指向自定义安装根，实际 {target}"

    # --list 报告的也是自定义根
    listed = _setup(run_cli, python_exe, agate_scripts, home, iroot, "--list")
    assert str(iroot) in listed.output, f"--list 应报告真实安装根:\n{listed.output}"

    # 卸载同样按自定义根清
    un = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                "--uninstall", "--scope", "global")
    assert un.returncode == 0, un.output
    assert not os.path.lexists(home / ".claude/agents/orchestrator.md"), \
        f"自定义根下的接入物应被清除:\n{un.output}"


def test_install_hook_direct_call_follows_agate_home(run_cli, python_exe, agate_scripts,
                                                    agate_root, git_repo, tmp_path):
    """**直调 `install-hook.py`**（`agate/AGENTS.md` 教用户这么用）也要跟随 `AGATE_HOME`。

    为什么要单测这条路径：`agate-setup.py` 会**显式传**安装根给 install-hook，所以
    install-hook 自身的"默认根"分支不被它覆盖——那条分支此前写死 `~/.agate`
    （`AGATE_HOME` 覆盖时装到错的地方）。本用例**不带参数**直调，专打该分支。
    """
    home = _fake_homes(tmp_path)
    iroot = home / "custom-root"
    (iroot / "scripts").mkdir(parents=True)
    for name in ("install-hook.py", "resolve-entry.py", "agate_common.py", "agate_package.py",
                 "pre-commit-gate.sh", "commit-msg-self-gate.sh", "pre-push-gate.sh"):
        src = agate_root / "scripts" / name
        if src.is_file():
            shutil.copyfile(src, iroot / "scripts" / name)

    env = {"HOME": str(home), "USERPROFILE": str(home),
           "AGATE_HOME": str(iroot), "AGATE_ROOT": ""}
    result = run_cli(python_exe, str(iroot / "scripts" / "install-hook.py"),
                     env=env, cwd=str(git_repo.path))
    assert result.returncode == 0, result.output
    hook = git_repo.path / ".git" / "hooks" / "pre-commit"
    assert os.path.lexists(hook), f"hook 应已安装:\n{result.output}"
    if hook.is_symlink():
        target = os.path.realpath(hook)
        assert str(iroot) in target, f"hook 应指向自定义安装根，实际 {target}"
    else:
        # 复制模式：`.agate-root` 标记须记自定义根（运行时靠它恢复 AGATE_ROOT）
        marker = git_repo.path / ".git" / "hooks" / ".agate-root"
        assert marker.is_file(), "复制模式应写 .agate-root 标记"
        assert str(iroot) in marker.read_text(encoding="utf-8"), \
            "标记应记自定义安装根（写死 ~/.agate 会暴露）"


def test_uninstall_never_removes_platform_root(run_cli, python_exe, agate_scripts,
                                               agate_root, tmp_path):
    """**平台自有目录绝不被删**：`~/.dsh` 等即使清空后也不能动。

    2026-09-21 自查发现的越界：原 `_prune_empty_dirs` 只以 `$HOME` 为界，会把
    `~/.dsh`（DSH 自己的目录，agateon 只是在其下放了文件）在空掉后一并删除。
    所有权边界应到**平台根**为止。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "global").returncode == 0
    assert (home / ".dsh").is_dir(), "前置：平台目录存在"

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "global")
    assert result.returncode == 0, result.output
    for rel in (".dsh", ".claude", ".agents", ".config/opencode"):
        assert (home / rel).is_dir(), f"平台自有目录不得被删: {rel}\n{result.output}"
    # agateon 在平台下的专属目录可以清（那是它的命名空间）
    assert not (home / ".dsh/.agent-presets/agate").exists(), "agateon 专属目录应清掉"


def test_all_projects_clears_project_scoped_artifacts(run_cli, python_exe, agate_scripts,
                                                      agate_root, tmp_path):
    """**BLK-1 回归**：`--all-projects` 必须清掉项目侧**平台接入物**（不只 hook）。

    审查实测的缺陷：`_uninstall_project` 未把 `project_root` 传给 `_uninstall_platforms`，
    后者按**进程 cwd** 解析 project 侧相对路径 → 从第三个目录执行时**0 项被删却报告成功**，
    每个项目留下断链 orchestrator 软链（平台静默找不到 orchestrator）。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    from conftest import GitRepo
    repos = [GitRepo(tmp_path / f"pp{i}") for i in (1, 2)]
    for r in repos:
        res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                     "--scope", "project", "--platform", "claude-code", cwd=str(r.path))
        assert res.returncode == 0, res.output
    arts = [r.path / ".claude/agents/orchestrator.md" for r in repos]
    assert all(os.path.lexists(a) for a in arts), "前置：两个项目都应有项目侧接入物"

    # 在**第三个目录**执行——证明路径解析以 project_root 为基准，而非 cwd
    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--all-projects", cwd=str(tmp_path))
    assert result.returncode == 0, result.output
    for a in arts:
        assert not os.path.lexists(a), (
            f"项目侧平台接入物应被清（BLK-1：按 cwd 解析会漏掉）: {a}\n{result.output}"
        )
    assert "已删除 0 项" not in result.output, f"计数不得为 0:\n{result.output}"


@pytest.mark.windows_smoke
def test_hook_with_marker_but_not_agate_is_kept(run_cli, python_exe, agate_scripts,
                                                agate_root, git_repo, tmp_path):
    """**BLK-2 回归**：`.agate-root` 标记存在，但 hook 内容不是 agate 的 → **必须保留**。

    审查实测的 fail-open：用户后来把自己的 hook 写回该路径，标记仍在 → 原实现照删且无备份。
    修复后标记只作**报告级**证据，不授予删除权。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    hook_dir = proj / ".git" / "hooks"
    hook_dir.mkdir(parents=True, exist_ok=True)
    (hook_dir / ".agate-root").write_text(str(iroot) + "\n", encoding="utf-8")
    hook = hook_dir / "pre-commit"
    hook.write_text("#!/bin/sh\necho 用户自己的东西\n", encoding="utf-8")

    # 用 --scope project（按 cwd 的 git 根定位）——**不能**用 --all-projects：
    # 未先安装则台账为空、项目根本不被处理，测试会"因错误的原因通过"（2026-09-21 自查）。
    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "project", cwd=str(proj))
    assert result.returncode == 0, result.output
    assert hook.is_file(), f"仅凭 marker 不得删用户 hook:\n{result.output}"
    assert "用户自己的东西" in hook.read_text(encoding="utf-8"), "内容须原样"


@pytest.mark.windows_smoke
def test_hook_mentioning_agate_only_in_comment_is_kept(run_cli, python_exe, agate_scripts,
                                                      agate_root, git_repo, tmp_path):
    """**BLK-2 回归**：内容仅在**注释**里提到 agate 字样 → 不得据此删除。

    审查实测：项目从未装过 agate，用户的 pre-commit 注释里写了 `pre-commit-gate`，
    原实现（子串指纹一票通行）把它删了。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    hook = proj / ".git" / "hooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    hook.write_text(
        "#!/bin/sh\n# 参考过 pre-commit-gate 与 resolve-entry.py 的思路\necho 我的检查\n",
        encoding="utf-8",
    )

    # 同上：必须走 --scope project（按 cwd 定位），否则台账为空 → 假绿
    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "project", cwd=str(proj))
    assert result.returncode == 0, result.output
    assert hook.is_file(), f"仅凭注释里的字样不得删用户 hook:\n{result.output}"
    assert "我的检查" in hook.read_text(encoding="utf-8"), "内容须原样"


def test_artifact_backup_restored_on_uninstall(run_cli, python_exe, agate_scripts,
                                               agate_root, tmp_path):
    """**OPT-2 回归**：安装时备份的用户原产物（`*.bak.<epoch>`）卸载时应**还原**。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    target = home / ".claude/agents/orchestrator.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# 我原来的 orchestrator 配置\n", encoding="utf-8")

    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "global").returncode == 0
    assert list(target.parent.glob("orchestrator.md.bak.*")), "前置：安装时应备份"

    result = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                    "--uninstall", "--scope", "global")
    assert result.returncode == 0, result.output
    assert target.is_file(), f"应还原为实体文件:\n{result.output}"
    assert "我原来的 orchestrator 配置" in target.read_text(encoding="utf-8"), \
        f"应还原用户原内容:\n{result.output}"


def test_purge_refuses_lookalike_dir(run_cli, python_exe, agate_scripts,
                                     agate_root, tmp_path):
    """**OPT-1 回归**：把入口脚本复制进无关目录**不足以**骗过 purge 守卫。

    审查实测：原守卫只判 `scripts/agate-install.py` 存在 → 复制该脚本进 lookalike/
    即被放行并 rmtree 掉整个目录（含其中无关文件）。
    """
    home = _fake_homes(tmp_path)
    _fake_install_root(tmp_path, agate_root)
    look = tmp_path / "lookalike"
    (look / "scripts").mkdir(parents=True)
    shutil.copyfile(agate_root / "scripts" / "agate-install.py", look / "scripts" / "agate-install.py")
    (look / "重要文件.txt").write_text("别删我\n", encoding="utf-8")

    result = _setup(run_cli, python_exe, agate_scripts, home, look,
                    "--uninstall", "--purge")
    assert result.returncode == 1, f"仅凭入口脚本不应放行:\n{result.output}"
    assert (look / "重要文件.txt").is_file(), "拒绝后不得删任何东西"


def test_project_install_from_subdir_uses_git_root(run_cli, python_exe, agate_scripts,
                                                   agate_root, git_repo, tmp_path):
    """**X1 回归**：在仓库**子目录**里 `--scope project` 安装 → 落点应是 **git 根**，且能卸掉。

    复核实测的不对称：安装按**进程 cwd**（`abspath`）解析、而台账/卸载按 **git 根** →
    在 `<repo>/sub/deep` 安装会把产物落到 `sub/deep/.claude/…`，之后**任何**位置卸载都
    报"已删除 0 项"，那些产物永远清不掉（pre-fix 反而能删到，属修复引入的回归）。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    sub = proj / "sub" / "deep"
    sub.mkdir(parents=True)

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code", cwd=str(sub))
    assert res.returncode == 0, res.output
    at_root = proj / ".claude/agents/orchestrator.md"
    at_sub = sub / ".claude/agents/orchestrator.md"
    assert os.path.lexists(at_root), (
        f"子目录安装的产物应落在 git 根（与台账/卸载基准一致）:\n{res.output}"
    )
    assert not os.path.lexists(at_sub), f"不应落在 cwd 下:\n{res.output}"

    # 从**第三个目录**卸载也必须清掉（靠台账 + git 根基准）
    un = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                "--uninstall", "--all-projects", cwd=str(tmp_path))
    assert un.returncode == 0, un.output
    assert not os.path.lexists(at_root), f"应能清掉:\n{un.output}"
    assert "已删除 0 项" not in un.output, f"计数不得为 0:\n{un.output}"


def test_copy_mode_hook_is_executable(run_cli, python_exe, agate_scripts,
                                      agate_root, git_repo, tmp_path):
    """**既有缺陷回归**：复制模式装出的 hook 必须**可执行**（否则 git 静默忽略 → gate 失效）。

    复核发现（本分支未引入）：`shutil.copyfile` **不携带权限位** → POSIX 复制模式装出
    0644，git 因"钩子不可执行"**静默忽略**且 exit 0 → **gate 兜底无声失效**。
    修法：复制两分支后都补执行位。
    """
    if os.name == "nt":  # Windows 无 POSIX 执行位语义
        pytest.skip("Windows 无 POSIX 执行位语义")
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    proj = git_repo.path
    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code",
                 cwd=str(proj), copy_mode=True)
    assert res.returncode == 0, res.output
    hook = proj / ".git" / "hooks" / "pre-commit"
    assert hook.is_file() and not hook.is_symlink(), f"应为复制形态:\n{res.output}"
    assert os.access(hook, os.X_OK), (
        f"复制模式的 hook 必须可执行（否则 git 静默忽略 → gate 失效）: "
        f"mode={oct(hook.stat().st_mode)[-3:]}\n{res.output}"
    )


# ── 回归：hook 目录必须问 git（git worktree / core.hooksPath，2026-09-23）────────
#
# dogfooding 标准流程（`docs/guides/worktree-dogfooding-guide.md`）就是在 git worktree 里
# 干活，而 worktree 的 `.git` 是**文件**（指向 `<主 checkout>/.git/worktrees/<name>`），
# 真正生效的 hooks 目录是**共享**的 `<主 checkout>/.git/hooks`。两侧原来都硬编码
# `<repo_root>/.git/hooks`：
#   · 安装侧 → `os.makedirs(<wt>/.git/hooks)` 抛 NotADirectoryError（**命令直接崩**）
#   · 卸载侧 → `os.path.lexists` 恒 False → **静默跳过**，报"已删除 0 项"而 hook 还在
# 即"装不上、也卸不掉"，而 worktree 正是 dogfooding 的工作目录。
# `core.hooksPath` 覆盖时同理（git 只看该目录，硬编码路径会让 gate 静默失效）。

_HOOK_NAMES = ("pre-commit", "commit-msg", "pre-push")


def _add_worktree(git_repo, tmp_path, name="wt"):
    """在主仓库旁挂一个链接 worktree；返回其路径。"""
    wt = tmp_path / name
    r = git_repo.git("worktree", "add", "-q", str(wt), "-b", name)
    assert r.returncode == 0, f"前置：建 worktree 失败: {r.stderr}"
    assert (wt / ".git").is_file(), "前置：链接 worktree 的 .git 应是**文件**"
    return wt


def _shared_hooks(repo):
    """主 checkout 的共享 hooks 目录（worktree 真正生效的那处）。"""
    return repo / ".git" / "hooks"


def test_install_hook_from_worktree_targets_shared_hooks_dir(run_cli, python_exe, agate_scripts,
                                                             agate_root, git_repo, tmp_path):
    """**回归**：在链接 worktree 里装 hook → 必须落进**共享** hooks 目录，且命令不得崩。

    pre-fix 实测：`NotADirectoryError: '/…/wt/.git/hooks'`（`.git` 是文件），
    即 dogfooding 标准流程里 `agate-setup.py` 在 worktree 内**根本跑不通**。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    wt = _add_worktree(git_repo, tmp_path)

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code", cwd=str(wt))
    assert res.returncode == 0, f"worktree 内安装不应失败:\n{res.output}"
    shared = _shared_hooks(repo)
    for name in _HOOK_NAMES:
        assert os.path.lexists(shared / name), (
            f"hook 应装在共享目录 {shared}（worktree 生效处），缺 {name}:\n{res.output}"
        )
    assert not (wt / ".git" / "hooks").exists(), "不应在 worktree 的 .git 文件下造出目录"
    # 上面那条在 `.git` 为文件时恒真（ENOTDIR）——补一条**有鉴别力**的：git 自己指出
    # 的 hooks 目录必须正是我们断言的那处（pre-fix 它会指向 `<wt>/.git/hooks`）。
    r = git_repo.git("-C", str(wt), "rev-parse", "--git-path", "hooks")
    assert r.returncode == 0, r.stderr
    assert os.path.realpath(os.path.join(str(wt), r.stdout.strip())) == os.path.realpath(shared), (
        f"git 认为的 hooks 目录应就是共享目录: {r.stdout.strip()}"
    )


def test_uninstall_from_worktree_removes_shared_hooks(run_cli, python_exe, agate_scripts,
                                                      agate_root, git_repo, tmp_path):
    """**回归**：从链接 worktree 里卸载 → 必须清掉共享 hooks（pre-fix 静默漏删）。

    pre-fix 实测：卸载报"已删除 0 项"，而三个 hook 仍留在主 checkout 的共享目录里——
    卸载后 gate 继续生效（用户以为已卸干净）且**无从再清**。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "project", "--platform", "claude-code",
                  cwd=str(repo)).returncode == 0
    shared = _shared_hooks(repo)
    assert all(os.path.lexists(shared / n) for n in _HOOK_NAMES), "前置：主 checkout 应已装 hook"
    wt = _add_worktree(git_repo, tmp_path)

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--uninstall", cwd=str(wt))
    assert res.returncode == 0, res.output
    left = [n for n in _HOOK_NAMES if os.path.lexists(shared / n)]
    assert not left, f"从 worktree 卸载应清掉共享 hooks，残留 {left}:\n{res.output}"


@pytest.mark.windows_smoke
def test_hook_dir_follows_core_hooks_path(run_cli, python_exe, agate_scripts,
                                          agate_root, git_repo, tmp_path):
    """`core.hooksPath` 指向别处时，hook 必须装到**那里**——git 只看那个目录。

    硬编码 `<repo>/.git/hooks` 会把 hook 装进 git **不会执行**的地方 → gate 静默失效
    （与复制模式不可执行同一个失效模式：装了但没生效）。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    custom = tmp_path / "custom-hooks"
    r = git_repo.git("config", "core.hooksPath", str(custom))
    assert r.returncode == 0, r.stderr

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code", cwd=str(repo))
    assert res.returncode == 0, res.output
    for name in _HOOK_NAMES:
        assert os.path.lexists(custom / name), (
            f"core.hooksPath 生效时 hook 应装在 {custom}，缺 {name}:\n{res.output}"
        )


def test_worktree_install_ledgers_hook_owner_so_hooks_stay_reachable(
        run_cli, python_exe, agate_scripts, agate_root, git_repo, tmp_path):
    """**回归**：在 worktree 里安装 → 台账须**同时**登记宿主根，否则删掉 worktree 后共享 hook 失联。

    hook 装在共享目录（宿主 repo 的 `.git/hooks`），所以"装了 agateon 的仓库"是**宿主**；
    只登记 worktree 路径的话，`git worktree remove` 之后台账里只剩一条"目录已不存在"的死条目，
    而**共享 hooks 仍然生效**却再也定位不到（用户以为卸干净了）。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    wt = _add_worktree(git_repo, tmp_path)

    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "project", "--platform", "claude-code",
                  cwd=str(wt)).returncode == 0
    data = json.loads((iroot / "installed-projects.json").read_text(encoding="utf-8"))
    paths = {os.path.realpath(e["path"]) for e in data["projects"]}
    assert os.path.realpath(str(wt)) in paths, f"worktree 自身应登记: {paths}"
    assert os.path.realpath(str(repo)) in paths, (
        f"宿主根（hook 真身所在）也必须登记，否则 worktree 删除后 hook 失联: {paths}"
    )

    # 端到端：worktree 目录消失后，仅凭台账仍能清掉共享 hooks
    r = git_repo.git("worktree", "remove", "--force", str(wt))
    assert r.returncode == 0, r.stderr
    un = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                "--uninstall", "--all-projects", cwd=str(tmp_path))
    assert un.returncode == 0, un.output
    left = [n for n in _HOOK_NAMES if os.path.lexists(_shared_hooks(repo) / n)]
    assert not left, f"worktree 已删，共享 hooks 仍应能经宿主条目清掉，残留 {left}:\n{un.output}"


def test_install_hook_direct_call_in_worktree_uses_shared_dir(run_cli, python_exe,
                                                              agate_scripts, agate_root,
                                                              git_repo, tmp_path):
    """**直调 `install-hook.py`** 在 worktree 里也要落共享目录（`agate/AGENTS.md` 教用户这么用）。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    wt = _add_worktree(git_repo, tmp_path)

    result = run_cli(python_exe, str(iroot / "scripts" / "install-hook.py"),
                     env=_env(home, iroot), cwd=str(wt))
    assert result.returncode == 0, result.output
    shared = _shared_hooks(repo)
    for name in _HOOK_NAMES:
        assert os.path.lexists(shared / name), f"缺 {name}:\n{result.output}"
    assert str(shared) in result.output, f"应显式报告落点目录:\n{result.output}"


def test_git_dir_env_does_not_redirect_the_hooks_dir(run_cli, python_exe, agate_scripts,
                                                    agate_root, tmp_path):
    """**回归**：环境里有 `GIT_DIR` 时，hook 目录查询不得被它劫持到别的仓库。

    复核实测：`git rev-parse --show-toplevel` 在 `GIT_DIR=<B>/.git` 下仍按 **cwd**
    返回 A（所以 `_git_root()` 认为是 A），而 `git rev-parse --git-path hooks` 被 GIT_DIR 劫持
    返回 **B** 的 hooks → 卸载 A 时删掉的其实是 B 的 hook：**A 的 gate 原样留下（并被 forget
    失去线索）**，B 被静默剥掉。这正是本次要消灭的"静默残留"，且是**新引入**的
    （改前是纯路径拼接、不跑 git）。修法：这些查询用去掉 `GIT_DIR`/`GIT_WORK_TREE`/
    `GIT_COMMON_DIR` 的净化环境。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    from conftest import GitRepo
    repo_a = GitRepo(tmp_path / "repo-a")
    repo_b = GitRepo(tmp_path / "repo-b")
    for r in (repo_a, repo_b):
        assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                      "--scope", "project", "--platform", "claude-code",
                      cwd=str(r.path)).returncode == 0
    a_hooks, b_hooks = _shared_hooks(repo_a.path), _shared_hooks(repo_b.path)
    assert all(os.path.lexists(a_hooks / n) for n in _HOOK_NAMES), "前置：A 应装有 hook"
    assert all(os.path.lexists(b_hooks / n) for n in _HOOK_NAMES), "前置：B 应装有 hook"

    # 在 A 里卸载，但环境被 GIT_DIR 污染指向 B（低可达性 / 高爆炸半径——静默删错仓库）
    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--uninstall", "--scope", "project", cwd=str(repo_a.path),
                 extra_env={"GIT_DIR": str(repo_b.path / ".git")})
    assert res.returncode == 0, res.output
    left_a = [n for n in _HOOK_NAMES if os.path.lexists(a_hooks / n)]
    assert not left_a, f"A 的 hook 应被清（GIT_DIR 不得劫持）: 残留 {left_a}\n{res.output}"
    left_b = [n for n in _HOOK_NAMES if os.path.lexists(b_hooks / n)]
    assert left_b == list(_HOOK_NAMES), (
        f"B 未被卸载，其 hook 不得被动: {left_b}\n{res.output}"
    )


def test_uninstall_warns_when_hooks_path_may_be_shared_across_repos(run_cli, python_exe,
                                                                   agate_scripts, agate_root,
                                                                   git_repo, tmp_path):
    """`core.hooksPath` 覆盖下卸载 = **跨仓库**动作，必须显式告警（不得静默）。

    复核实测：repoA、repoB 都用 `core.hooksPath=<shared>`，在 A 里卸载会把三个
    hook 全删 → B 的 gate 同时消失。删除对象确实是 agate 自有文件（归属校验拦得住用户文件），
    但"仓库级动作"的提示原先只覆盖 worktree→宿主，**没覆盖 hooksPath→跨仓库**。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    shared = tmp_path / "shared-hooks"
    assert git_repo.git("config", "core.hooksPath", str(shared)).returncode == 0
    assert _setup(run_cli, python_exe, agate_scripts, home, iroot,
                  "--scope", "project", "--platform", "claude-code",
                  cwd=str(repo)).returncode == 0

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--uninstall", "--scope", "project", cwd=str(repo))
    assert res.returncode == 0, res.output
    assert "core.hooksPath" in res.output and "其他仓库" in res.output, (
        f"hooksPath 覆盖下卸载必须提示可能影响其他仓库:\n{res.output}"
    )


def test_tilde_core_hooks_path_is_not_flagged_as_cwd_relative(run_cli, python_exe, agate_scripts,
                                                             agate_root, git_repo, tmp_path):
    """`core.hooksPath=~/x` **不是** cwd 相对——不得误报"位置随运行目录变"。

    复核实测（OP-1）：git 会展开 `~`（`~kity/x` 亦然），`--git-path hooks` 返回**绝对路径**，
    位置并不随 cwd 变。原判据 `os.path.isabs(config)` 对它误报，且顺带压掉了 worktree 提示。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    assert git_repo.git("config", "core.hooksPath", "~/tilde-hooks").returncode == 0

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code", cwd=str(repo))
    assert res.returncode == 0, res.output
    assert "按**运行目录**解析" not in res.output and "按运行目录解析" not in res.output, (
        f"`~/x` 不随 cwd 漂移，不应误报相对路径:\n{res.output}"
    )
    assert os.path.lexists(home / "tilde-hooks" / "pre-commit"), (
        f"应装到 git 展开后的 ~ 目录:\n{res.output}"
    )


def test_git_shared_hook_owner_ignores_non_worktree_gitdir(agate_scripts, tmp_path):
    """`--separate-git-dir` / submodule 的"主工作树"其实是 **gitdir**，不得当宿主项目登记。

    复核实测（OP-2）：`git worktree list --porcelain` 首行对这类布局返回的是 git 内部目录
    （如 `<repo>/.git` 或 `<sup>/.git/modules/...`）而非工作树，`record_project` 会把它当项目
    登记 → `--list` 显示 git 内部目录。判据补一条：宿主必须是**真工作树**（其下 `.git` 存在，
    文件或目录皆可）。
    """
    import subprocess as sp

    gd = tmp_path / "gd"
    work = tmp_path / "work"
    work.mkdir()
    r = sp.run(["git", "init", "-q", f"--separate-git-dir={gd}", str(work)],
               capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert (work / ".git").is_file(), "前置：separate-git-dir 下 .git 应是文件"
    for args in (["config", "user.email", "t@t"], ["config", "user.name", "t"]):
        sp.run(["git", "-C", str(work), *args], capture_output=True)
    (work / "a.txt").write_text("a\n", encoding="utf-8")
    sp.run(["git", "-C", str(work), "add", "-A"], capture_output=True)
    sp.run(["git", "-C", str(work), "commit", "-qm", "i"], capture_output=True)

    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    # 前置：确实是"首行给 gitdir"的布局（否则本用例测不到目标分支）
    rc, out = agate_common.run_git(["worktree", "list", "--porcelain"], cwd=str(work))
    assert rc == 0 and out.startswith("worktree "), out
    first = out.splitlines()[0][len("worktree "):].strip()
    assert not os.path.lexists(os.path.join(first, ".git")), (
        f"前置：该布局首行应是 gitdir（其下无 .git），实际 {first}"
    )

    assert agate_common.git_shared_hook_owner(str(work)) is None, (
        "separate-git-dir 的 host 是 gitdir，不是工作树，不得作为宿主项目"
    )


def test_is_bare_repo_uses_config_key_not_computed_flag(agate_scripts, tmp_path):
    """裸仓库判据读 **配置键** `core.bare`，不用 `--is-bare-repository` 的计算值。

    **为什么**（复核 C1-edge 实测）：`--is-bare-repository` 是 cwd/gitdir 敏感的**计算值**——
    `--separate-git-dir` 的 **gitdir** 在 `core.bare` 键缺失时会被算成 `true`，于是那个 git
    内部目录会被重新当成"宿主项目"登记进台账（OP-2 症状回归：`--list` 显示 git 内部目录）。
    git 自建布局都显式写 `core.bare`，故读键既准确又不误纳。
    """
    import subprocess as sp

    def _git(*args, cwd=None):
        return sp.run(["git", *args], capture_output=True, text=True, cwd=cwd)

    gd = tmp_path / "gd"
    work = tmp_path / "work"
    work.mkdir()
    assert _git("init", "-q", f"--separate-git-dir={gd}", str(work)).returncode == 0
    for kv in (("user.email", "t@t"), ("user.name", "t")):
        _git("config", *kv, cwd=str(work))
    (work / "a.txt").write_text("a\n", encoding="utf-8")
    _git("add", "-A", cwd=str(work))
    _git("commit", "-qm", "i", cwd=str(work))
    wt = tmp_path / "wt"
    assert _git("worktree", "add", "-q", str(wt), "-b", "wtb", cwd=str(work)).returncode == 0

    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    # 前置：默认布局下该 gitdir 的键是 false（本条主要防"键缺失"这一边界）
    assert agate_common._is_bare_repo(str(gd)) is False, "前置：separate-git-dir gitdir 非裸仓库"

    # 键缺失 → 计算值会变 true，但判据必须仍为 False（否则 gitdir 被当宿主）
    assert _git("config", "--unset", "core.bare", cwd=str(gd)).returncode == 0
    rc_flag, flag_out = agate_common.run_git(["rev-parse", "--is-bare-repository"], cwd=str(gd),
                                            clean_location_env=True)
    assert flag_out.strip() == "true", (
        f"前置：该边界下计算值应为 true（否则本用例测不到目标分支）: {rc_flag} {flag_out!r}"
    )
    assert agate_common._is_bare_repo(str(gd)) is False, (
        "键缺失时不得认定为裸仓库（否则 separate-git-dir 的 gitdir 会被当宿主项目）"
    )
    assert agate_common.git_shared_hook_owner(str(wt)) is None
    assert agate_common.git_shared_hook_owner(str(work)) is None


def test_install_hook_fallback_copies_match_primary(agate_scripts, tmp_path):
    """`install-hook.py` 的**降级副本**必须与 `agate_common` 主实现行为一致（防漂移）。

    为什么单测这条：pyyaml 缺失时 install-hook 会走 `except (ImportError, SystemExit)` 里的
    本地副本（安装器不依赖 pyyaml）。这些副本是**手工维护的第二/第三份实现**——复核已实测
    它们与主实现存在过差异（缺空值守卫）。本用例按三种布局**逐一比对两者的返回值**，
    让任何一份漂移立刻变红（同 `test_protocol_root_dual_impl` 的守护思路）。
    """
    import subprocess as sp

    def _git(*args, cwd=None):
        return sp.run(["git", *args], capture_output=True, text=True, cwd=cwd)

    # 布局 1：普通仓库（含 core.hooksPath 覆盖）2：链接 worktree 3：裸仓库宿主
    plain = tmp_path / "plain"
    plain.mkdir()
    _git("init", "-q", ".", cwd=str(plain))
    custom = tmp_path / "custom-hooks"
    _git("config", "core.hooksPath", str(custom), cwd=str(plain))
    linked = tmp_path / "linked"
    _git("worktree", "add", "-q", str(linked), "-b", "linked-b", cwd=str(plain))
    bare, bare_wt = _bare_host_with_worktree(tmp_path)

    primary_dir = agate_scripts
    # `agate_common` 必须能被**主实现**导入（且下面的自检也要用它），先把 scripts 目录上 path
    if str(primary_dir) not in sys.path:
        sys.path.insert(0, str(primary_dir))
    import agate_common as _ac

    # 独立加载"降级副本"：只放 install-hook.py（无 agate_common）→ 必走 except 分支
    fallback_dir = tmp_path / "fallback-scripts"
    fallback_dir.mkdir()
    shutil.copyfile(primary_dir / "install-hook.py", fallback_dir / "install-hook.py")

    def _load_primary(name):
        """加载**主实现**：`agate_common` 正常可导入，故模块级 try 走 import 分支。"""
        spec = importlib.util.spec_from_file_location(
            f"primary_{name}", primary_dir / "install-hook.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return getattr(mod, name)

    def _load_fallback(name):
        """加载**降级副本**：临时把 `agate_common` 置为不可导入（`sys.modules[x] = None`
        是 import 失败的官方语义），强制走 `except (ImportError, SystemExit)` 分支。

        ⚠️ 不这样做该用例是**假绿**（2026-09-23 自查实测）：`agate_common` 在 sys.path 上
        可导入时，`install-hook.py` 的模块级 try 永远成功，降级副本**从不被执行**——无论副本
        怎么漂移都测不出来。
        """
        saved = sys.modules.get("agate_common", _MISSING)
        sys.modules["agate_common"] = None  # → `import agate_common` 抛 ImportError
        try:
            spec = importlib.util.spec_from_file_location(
                f"fallback_{name}", fallback_dir / "install-hook.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return getattr(mod, name)
        finally:
            if saved is _MISSING:
                sys.modules.pop("agate_common", None)
            else:
                sys.modules["agate_common"] = saved

    # 前置自检：降级副本确实走的是 except 分支（否则该用例无鉴别力）
    fb_impl = _load_fallback("git_hooks_dir")
    assert fb_impl is not _ac.git_hooks_dir, (
        "前置：降级副本未被真正加载（agate_common 仍可导入）——该用例会是假绿"
    )

    for layout, root in (("plain+hooksPath", str(plain)), ("linked", str(linked)),
                         ("bare-host-wt", str(bare_wt))):
        got_p = _load_primary("git_hooks_dir")(root)
        got_f = _load_fallback("git_hooks_dir")(root)
        assert got_p == got_f, f"[{layout}] git_hooks_dir 主实现与降级副本不一致"
        owner_p = _load_primary("git_shared_hook_owner")(root)
        owner_f = _load_fallback("git_shared_hook_owner")(root)
        assert owner_p == owner_f, f"[{layout}] git_shared_hook_owner 不一致"
        cfg_p = _load_primary("git_hooks_path_config")(root)
        cfg_f = _load_fallback("git_hooks_path_config")(root)
        assert cfg_p == cfg_f, f"[{layout}] git_hooks_path_config 不一致"

    # **GIT_DIR 被污染**的布局（复核 C3-gap）：降级副本的 `run_git` 若丢掉
    # `clean_location_env`，上面三条"无污染环境"的比对**全绿**——该依赖必须被显式打到。
    other = tmp_path / "other-repo"
    other.mkdir()
    _git("init", "-q", ".", cwd=str(other))
    polluted = {"GIT_DIR": str(other / ".git")}
    old_env = {k: os.environ.get(k) for k in polluted}
    os.environ.update(polluted)
    try:
        got_p = _load_primary("git_hooks_dir")(str(linked))
        got_f = _load_fallback("git_hooks_dir")(str(linked))
        assert got_p == got_f, "[GIT_DIR 污染] git_hooks_dir 主实现与降级副本不一致"
        owner_p = _load_primary("git_shared_hook_owner")(str(linked))
        owner_f = _load_fallback("git_shared_hook_owner")(str(linked))
        assert owner_p == owner_f, "[GIT_DIR 污染] git_shared_hook_owner 不一致"
        # 且两者都**没有**被 GIT_DIR 劫持到 other（否则中性化形同虚设）
        assert got_p == _ac.git_hooks_dir(str(linked)), got_p
        assert os.path.realpath(got_p) != os.path.realpath(str(other / ".git" / "hooks")), (
            f"GIT_DIR 不得劫持 hook 目录: {got_p}"
        )
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    del bare


def test_git_hooks_dir_falls_back_outside_a_repo(agate_scripts, tmp_path):
    """`git_hooks_dir` 在非仓库目录下不得抛异常（`.git/hooks` 兜底）。

    卸载会在任意 cwd 被调用（`--all-projects` 尤其如此），兜底路径保证"问不到 git"时
    退化为旧语义而不是崩在半路。
    """
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    stray = tmp_path / "not-a-repo"
    stray.mkdir()
    assert agate_common.git_hooks_dir(str(stray)) == os.path.join(str(stray), ".git", "hooks")
    assert agate_common.git_shared_hook_owner(str(stray)) is None

    # 兜底必须与 git 对**真仓库**的答案一致，否则"回退旧语义"等价于回到缺陷。
    # ⚠️ 必须用**答案不等于 `<repo>/.git/hooks`** 的布局（core.hooksPath 覆盖）——
    # 普通仓库下两者按定义相等，任何生产代码改动都不会让该断言变红（复核 OP-3 实测）。
    from conftest import GitRepo
    repo = GitRepo(tmp_path / "real-repo")
    custom = tmp_path / "elsewhere-hooks"
    assert repo.git("config", "core.hooksPath", str(custom)).returncode == 0
    rc, out = agate_common.run_git(["rev-parse", "--git-path", "hooks"], cwd=str(repo.path))
    assert rc == 0, out
    resolved = os.path.realpath(os.path.join(str(repo.path), out.strip()))
    assert resolved != os.path.realpath(os.path.join(str(repo.path), ".git", "hooks")), (
        "前置：该布局下 git 的答案应与硬编码路径不同，否则断言无鉴别力"
    )
    assert agate_common.git_hooks_dir(str(repo.path)) == resolved


def _bare_host_with_worktree(tmp_path):
    """建 `host.git`（裸仓库）+ 其链接 worktree `wt`；返回 (bare, wt)。"""
    import subprocess as sp

    def _git(*args, cwd=None):
        return sp.run(["git", *args], capture_output=True, text=True, cwd=cwd)

    src = tmp_path / "src"
    src.mkdir()
    assert _git("init", "-q", ".", cwd=str(src)).returncode == 0
    for kv in (("user.email", "t@t"), ("user.name", "t")):
        _git("config", *kv, cwd=str(src))
    (src / "a.txt").write_text("a\n", encoding="utf-8")
    _git("add", "-A", cwd=str(src))
    _git("commit", "-qm", "i", cwd=str(src))

    bare = tmp_path / "host.git"
    assert _git("clone", "-q", "--bare", str(src), str(bare)).returncode == 0
    wt = tmp_path / "wt"
    r = _git("worktree", "add", "-q", str(wt), "HEAD", cwd=str(bare))
    assert r.returncode == 0, r.stderr
    return bare, wt


def test_git_shared_hook_owner_accepts_bare_host(agate_scripts, tmp_path):
    """**回归**：宿主是**裸仓库**时也必须登记它——裸仓库目录下没有 `.git`，但它就是 git 目录。

    复核实测：worktree 的宿主可为裸仓库（`git clone --bare` + `worktree add`），此时
    宿主目录里**没有** `.git`。若只按"其下有 `.git`"判工作树，宿主判定为 None → 只登记
    worktree 自身 → `git worktree remove` 后共享 hooks **仍在**却失去台账线索，而推荐的补救
    （"从该仓库重跑 --uninstall"）在裸目录里**不可执行**（`rev-parse --show-toplevel` 直接
    fatal："该操作必须在一个工作区中运行"）→ 正是本系列要消灭的静默残留。
    """
    bare, wt = _bare_host_with_worktree(tmp_path)

    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    assert not os.path.lexists(bare / ".git"), "前置：裸仓库目录下没有 .git"
    owner = agate_common.git_shared_hook_owner(str(wt))
    assert owner is not None, "裸仓库宿主必须被识别（否则 worktree 删除后 hook 失联）"
    assert os.path.realpath(owner) == os.path.realpath(str(bare)), owner
    # 且宿主与 worktree 确实共用同一 hooks 目录（判定前提）
    assert agate_common.git_hooks_dir(owner) == agate_common.git_hooks_dir(str(wt))


def test_bare_host_worktree_install_ledgers_host_and_can_uninstall(
        run_cli, python_exe, agate_scripts, agate_root, tmp_path):
    """端到端：裸仓库宿主 + worktree 安装 → 台账含宿主；删掉 worktree 后仍能清共享 hooks。"""
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    bare, wt = _bare_host_with_worktree(tmp_path)

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code", cwd=str(wt))
    assert res.returncode == 0, res.output
    for name in _HOOK_NAMES:
        assert os.path.lexists(bare / "hooks" / name), f"缺 {name}:\n{res.output}"
    data = json.loads((iroot / "installed-projects.json").read_text(encoding="utf-8"))
    paths = {os.path.realpath(e["path"]) for e in data["projects"]}
    assert os.path.realpath(str(bare)) in paths, (
        f"裸仓库宿主须登记（hook 真身所在）: {paths}"
    )

    import subprocess as sp
    r = sp.run(["git", "worktree", "remove", "--force", str(wt)],
               capture_output=True, text=True, cwd=str(bare))
    assert r.returncode == 0, r.stderr
    un = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                "--uninstall", "--all-projects", cwd=str(tmp_path))
    assert un.returncode == 0, un.output
    left = [n for n in _HOOK_NAMES if os.path.lexists(bare / "hooks" / n)]
    assert not left, f"worktree 已删，裸仓库宿主条目仍应能清掉共享 hooks: {left}\n{un.output}"


def test_relative_core_hooks_path_is_reported(run_cli, python_exe, agate_scripts,
                                              agate_root, git_repo, tmp_path):
    """**相对** `core.hooksPath` → 必须告警（git 按 cwd 解析它，位置随运行目录变）。

    实测（git 2.43）：同一仓库里，从 worktree 提交触发 `<worktree>/<hooksPath>`，从主 checkout
    提交触发 `<主 checkout>/<hooksPath>`——即"装一次全仓库生效"的承诺在相对路径下**不成立**。
    工具无法单方面消除该语义，必须如实说明并给出出路（改绝对路径），否则用户以为已接入而实际
    换个目录提交 gate 就静默失效。
    """
    home = _fake_homes(tmp_path)
    _home, iroot = _fake_install_root(tmp_path, agate_root)
    repo = git_repo.path
    r = git_repo.git("config", "core.hooksPath", "my-relative-hooks")
    assert r.returncode == 0, r.stderr

    res = _setup(run_cli, python_exe, agate_scripts, home, iroot,
                 "--scope", "project", "--platform", "claude-code", cwd=str(repo))
    assert res.returncode == 0, res.output
    assert "相对路径" in res.output and "core.hooksPath" in res.output, (
        f"应告警相对 core.hooksPath 的 cwd 语义:\n{res.output}"
    )
    # 仍按 git 的解析结果安装（不假装支持不了就不装）
    assert os.path.lexists(repo / "my-relative-hooks" / "pre-commit"), res.output
