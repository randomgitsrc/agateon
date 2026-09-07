# tests/unit/test_hook_resolve_entry.py — hook 解析入口 resolve-entry（resolve-chain 批次）
# 被测：agate/scripts/resolve-entry.py（TAG0008 新组件，固定解析入口）+ 3 hook 薄壳的 exec 目标改造
#       + install-hook.py 的固定入口安装契约（P4 实现）。P3 阶段 resolve-entry.py 不存在 → 红灯（B 类）。
# BDD 映射：BDD-15（装固定解析入口，不直接指具体版本 gate py）、BDD-16（A/B 版本隔离）、
#       BDD-17（resolve 失败回退 current 跑 gate，不静默放行）、BDD-18（切版本不用重装 hook）、
#       BDD-19（Windows 复制模式经 .agate-root 恢复仍可解析）。
# 平台无关（AGENTS.md 测试约定）：
#   * 假 HOME 经 HOME+USERPROFILE env 指向 tmp_path；current/latest 用文本指针（Windows-safe）
#   * 复制模式用 AGATE_HOOK_COPY_MODE=1 模拟（test_install_hook.py 既有模式），不依赖真实 Windows 无权限
#   * 版本目录内含 stub gate（写标记到 stdout），断言 hook 执行链跑到了哪个版本的 gate
# Given 契约：
#   resolve-entry 每次运行读 cwd 向上找的 .agate-version → 得 AGATE_ROOT → exec <root>/scripts/{gate}.py；
#   gate-name→gate py 映射：pre-commit→pre-commit-gate.py / commit-msg→commit-msg-self-gate.py /
#   pre-push→pre-push-gate.py（P2-review 决策点 2，薄壳保留、exec 目标变 resolve-entry）。

import shutil

import pytest


def _resolve_env(home):
    return {"AGATE_ROOT": "", "HOME": str(home), "USERPROFILE": str(home)}


def _write_version_decl(project, version):
    (project / ".agate-version").write_text(f"agate: {version}\n", encoding="utf-8")


_STUB_GATE = 'import sys\nsys.stdout.write("{marker}\\n")\n'


def _make_home(tmp_path, versions=("v0.43.0", "v0.44.0"), current="latest", latest="v0.44.0"):
    """构造假 ~/.agate：版本目录（已装）+ 每版本一个 stub pre-commit gate + 文本指针。

    marker = GATE-V + 主版本.次版本（去点），如 v0.43.0 → GATE-V043（与 P3-test-cases-resolve.md
    声明的 GATE-V043/GATE-V044 标记一致；v.replace(".","") 会把 v0.43.0 算成 v0430 → 修正）。
    """
    home = tmp_path / "home"
    for v in versions:
        vdir = home / ".agate" / v
        (vdir / "scripts").mkdir(parents=True, exist_ok=True)
        marker = "GATE-V" + v[1:].rsplit(".", 1)[0].replace(".", "")
        (vdir / "scripts" / "pre-commit-gate.py").write_text(
            _STUB_GATE.format(marker=marker), encoding="utf-8"
        )
    (home / ".agate" / "latest").write_text(latest + "\n", encoding="utf-8")
    (home / ".agate" / "current").write_text(current + "\n", encoding="utf-8")
    return home


def _make_fake_root(tmp_path, agate_scripts):
    """等价 test_install_hook.py _make_fake_root：cp hook 薄壳到 fake/scripts/。

    额外复制 agate_common.py（resolve-entry 运行依赖）与 resolve-entry.py（P3 不存在 → 红灯；
    P4 存在 → 复制模式下 hook 执行链可全链跑通）。
    """
    fake = tmp_path / "agate-fake"
    (fake / "scripts").mkdir(parents=True)
    for name in ("pre-commit-gate.sh", "commit-msg-self-gate.sh", "pre-push-gate.sh", "agate_common.py"):
        src = agate_scripts / name
        if src.is_file():
            shutil.copy2(str(src), str(fake / "scripts" / name))
    entry = agate_scripts / "resolve-entry.py"
    if entry.is_file():
        shutil.copy2(str(entry), str(fake / "scripts" / "resolve-entry.py"))
    return fake


def _run_install_copy_mode(run_cli, python_exe, agate_scripts, repo, fake):
    env = {"AGATE_ROOT": str(fake), "AGATE_HOOK_COPY_MODE": "1"}
    return run_cli(
        python_exe,
        str(agate_scripts / "install-hook.py"),
        str(fake),
        cwd=str(repo),
        env=env,
    )


@pytest.mark.windows_smoke
def test_bdd_15_install_fixed_resolve_entry(git_repo, agate_scripts, python_exe, run_cli, tmp_path):
    repo = git_repo.path
    fake = _make_fake_root(tmp_path, agate_scripts)

    result = _run_install_copy_mode(run_cli, python_exe, agate_scripts, repo, fake)
    assert result.returncode == 0

    hook = repo / ".git" / "hooks" / "pre-commit"
    assert hook.is_file()
    content = hook.read_text(encoding="utf-8")
    exec_lines = [line for line in content.splitlines() if "exec" in line]
    # 固定入口：hook 执行链经 resolve-entry（不随版本变），而非直接 exec 具体版本 gate py
    assert any("resolve-entry.py" in line for line in exec_lines)
    assert not any("pre-commit-gate.py" in line for line in exec_lines)


def test_bdd_16_ab_isolated_versions(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    proj_a = tmp_path / "proj-a"
    proj_a.mkdir()
    _write_version_decl(proj_a, "v0.43.0")
    proj_b = tmp_path / "proj-b"
    proj_b.mkdir()  # 无声明 → current → latest → v0.44.0

    r_a = run_cli(
        python_exe, str(agate_scripts / "resolve-entry.py"), "pre-commit",
        cwd=str(proj_a), env=_resolve_env(home),
    )
    r_b = run_cli(
        python_exe, str(agate_scripts / "resolve-entry.py"), "pre-commit",
        cwd=str(proj_b), env=_resolve_env(home),
    )
    assert r_a.returncode == 0
    assert r_b.returncode == 0
    assert "GATE-V043" in r_a.output  # 项目 A 锁旧版
    assert "GATE-V044" not in r_a.output
    assert "GATE-V044" in r_b.output  # 项目 B 走 current 新版
    assert "GATE-V043" not in r_b.output


def test_bdd_17_resolve_failure_fallback_not_silent(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.99.0")  # 声明未安装版本

    result = run_cli(
        python_exe, str(agate_scripts / "resolve-entry.py"), "pre-commit",
        cwd=str(project), env=_resolve_env(home),
    )
    assert result.returncode == 0
    assert "v0.99.0" in result.output  # 解析失败不静默：警告指出未安装版本
    assert "GATE-V044" in result.output  # 回退 current（v0.44.0）gate 照常执行，不静默跳过


def test_bdd_18_switch_version_no_reinstall(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.43.0")

    r1 = run_cli(
        python_exe, str(agate_scripts / "resolve-entry.py"), "pre-commit",
        cwd=str(project), env=_resolve_env(home),
    )
    assert "GATE-V043" in r1.output

    _write_version_decl(project, "v0.44.0")  # 直接改声明，不重跑 install-hook
    r2 = run_cli(
        python_exe, str(agate_scripts / "resolve-entry.py"), "pre-commit",
        cwd=str(project), env=_resolve_env(home),
    )
    assert "GATE-V044" in r2.output  # 切版本即生效


@pytest.mark.windows_smoke
def test_bdd_19_copy_mode_resolve_entry(
    git_repo, agate_scripts, python_exe, run_cli, bash, tmp_path
):
    repo = git_repo.path
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.43.0")
    fake = _make_fake_root(tmp_path, agate_scripts)

    install = _run_install_copy_mode(run_cli, python_exe, agate_scripts, repo, fake)
    assert install.returncode == 0
    marker = repo / ".git" / "hooks" / ".agate-root"
    assert marker.is_file()
    assert marker.read_text(encoding="utf-8").strip() == str(fake)

    hook = repo / ".git" / "hooks" / "pre-commit"
    result = run_cli(bash, str(hook), cwd=str(project), env=_resolve_env(home))
    # 复制模式下经 .agate-root 恢复 AGATE_ROOT → 仍按项目版本解析并跑 gate，不因复制模式失效
    assert "GATE-V043" in result.output


# ============================================================
# TAG0032 版本管理生命周期可用性批 — 断点二：钉版后 hook gate 路径可解析
#   BDD-8（1:1 映射 P1-requirements.md §3.2）
#   命名前缀 test_tag0032_bdd_N_（区分 TAG0008 既有 test_bdd_15..19）
#   被测行为由 P4 实现（决策 A1：_protocol_root → resolve-entry.py:49 的 gate 路径
#   拼接自然命中 vX/agate/scripts/）——P3 当前红灯（B 类：resolve 返回 vX，
#   gate_path = vX/scripts/pre-commit-gate.py 不存在 → resolve-entry.py:50-52 exit 1）。
#   fixture 铁律（I-5）：元仓库形态——gate 脚本在 <version>/agate/scripts/，
#   <version>/scripts/ 不建。
# ============================================================


def _make_home_meta_hook(tmp_path, version="v0.50.0", marker="GATE-META-050"):
    """元仓库形态隔离 HOME：~/.agate/<version>/agate/scripts/pre-commit-gate.py（stub 打 marker），
    <version>/scripts/ 不建。"""
    home = tmp_path / "home"
    gdir = home / ".agate" / version / "agate" / "scripts"
    gdir.mkdir(parents=True)
    (gdir / "pre-commit-gate.py").write_text(
        _STUB_GATE.format(marker=marker), encoding="utf-8"
    )
    return home


def test_tag0032_bdd_8_meta_repo_hook_gate_path_resolves(
    run_cli, python_exe, agate_scripts, tmp_path
):
    """BDD-8：元仓库形态版本 + 项目钉版 → resolve-entry.py pre-commit 解析出的 gate 路径
    <root>/scripts/pre-commit-gate.py（root = vX/agate）存在并被 exec，不因 gate 缺失 exit 1。"""
    home = _make_home_meta_hook(tmp_path, "v0.50.0", marker="GATE-META-050")
    project = tmp_path / "project"
    project.mkdir()
    _write_version_decl(project, "v0.50.0")

    result = run_cli(
        python_exe,
        str(agate_scripts / "resolve-entry.py"),
        "pre-commit",
        cwd=str(project),
        env=_resolve_env(home),
    )
    assert result.returncode == 0, (
        "元仓库形态下 gate 路径应命中 vX/agate/scripts/，不因『gate 脚本不存在』exit 1"
    )
    assert "GATE-META-050" in result.output, "解析出的版本 gate 应被 exec"
