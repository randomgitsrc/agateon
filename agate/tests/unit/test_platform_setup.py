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


import yaml

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
    assert "显式" in text, "须写明「必须显式要求派发」这一约束"


def test_codex_skill_points_to_template_not_duplicates(agate_root):
    """适配层只指向模板，不复制协议正文（同 DSH persona 的薄身份约束）。"""
    text = _codex_skill(agate_root)
    assert "orchestrator-template.md" in text, "须指向 orchestrator-template.md"
    # 只禁「协议过程」类内容（会话开始步骤 / 职责边界）——工具映射表里点名
    # state 文件（如 active-tasks.md）是**平台差异**的合法表述，不算复制协议正文。
    for forbidden in ("你永远不亲自写阶段产出物", "会话开始时", "{AGATE_WORKSPACE}"):
        assert forbidden not in text, (
            f"Codex 适配层复制了协议内容「{forbidden}」——协议内容单一来源在模板"
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
