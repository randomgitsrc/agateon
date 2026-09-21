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


import json
import os
import shutil

import pytest
import yaml

from conftest import PROTOCOL_RULE_MARKERS

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


def _setup(run_cli, python_exe, agate_scripts, home, iroot, *extra, cwd=None, copy_mode=False):
    env = _env(home, iroot)
    if copy_mode:
        env["AGATE_HOOK_COPY_MODE"] = "1"
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
