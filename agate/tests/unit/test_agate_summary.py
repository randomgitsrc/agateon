# tests/unit/test_agate_summary.py — agate-summary.py 版本显示语义迁移（resolve-chain 批次）
# 被测：agate/scripts/agate-summary.py（TAG0008 语义迁移：从"仓库自身 git describe"→"项目解析到的版本 + 原因"）。
# P3 阶段该迁移未实现 → 红灯（断言失败：输出为旧 git-describe 语义，不包含项目解析版本）。
# BDD 映射：BDD-20（.agate-version 锁定 + 原因）、BDD-21（全局 current 回退 + 原因）。
# 平台无关：假 HOME 经 HOME+USERPROFILE env 指向 tmp_path；current/latest 用文本指针（Windows-safe）。

import os
import re
import sys

import pytest

import helpers_tag_repo as H


def _resolve_env(home):
    return {"AGATE_ROOT": "", "HOME": str(home), "USERPROFILE": str(home)}


def _make_home(tmp_path, versions=("v0.43.0", "v0.44.0"), current="latest", latest="v0.44.0"):
    home = tmp_path / "home"
    for v in versions:
        (home / ".agate" / v).mkdir(parents=True, exist_ok=True)
    (home / ".agate" / "latest").write_text(latest + "\n", encoding="utf-8")
    (home / ".agate" / "current").write_text(current + "\n", encoding="utf-8")
    return home


@pytest.mark.windows_smoke
def test_bdd_20_summary_resolved_version_and_reason(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    (project / ".agate-version").write_text("agate: v0.43.0\n", encoding="utf-8")

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-summary.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.43.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.43.0" in result.output
    assert ".agate-version" in result.output  # 原因说明引用 .agate-version


def test_bdd_21b_symlink_pointer_shows_actual_version(run_cli, python_exe, agate_scripts, tmp_path):
    """rev2 CRITICAL-1：软链指针布局下 summary 显示实际版本号（BDD-21 current 回退语义）。

    回归用例：软链布局下 `_resolve_pointer_chain` isdir 短路会把 version 显示成
    "current"/"latest" 而非实际版本号（agate-summary 误导）。
    """
    home = tmp_path / "home"
    for v in ("v0.43.0", "v0.44.0"):
        (home / ".agate" / v).mkdir(parents=True, exist_ok=True)
    try:
        os.symlink("v0.44.0", str(home / ".agate" / "latest"))
        os.symlink("latest", str(home / ".agate" / "current"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，软链指针布局无法构建")

    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-summary.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.44.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.44.0" in result.output
    assert "版本：v0.44.0" in result.output, "软链布局下显示版本应为实际版本号，而非 current/latest"


def test_bdd_21_summary_global_current_reason(run_cli, python_exe, agate_scripts, tmp_path):
    home = _make_home(tmp_path)  # current→latest→v0.44.0
    project = tmp_path / "project"
    project.mkdir()

    result = run_cli(
        python_exe,
        str(agate_scripts / "agate-summary.py"),
        cwd=str(project),
        env=_resolve_env(home),
    )
    expected_root = str((home / ".agate" / "v0.44.0").resolve())
    assert result.returncode == 0
    assert expected_root in result.output
    assert "v0.44.0" in result.output
    assert "current" in result.output  # 原因说明：全局 current 回退


# --- DSH 安装产物链接校验（防软链指向非权威副本的静默漂移复发）---
# 背景（2026-08-26）：~/.dsh/skills/agate-protocol/SKILL.md 曾被安装成指向
# dsh-workspace/agate-copy（测试用临时副本）而非 ~/.agate 权威链，静默存活 5 天
# 穿过 v0.64.0 发布。机制缺口：安装后无任何校验。本组测试覆盖修复。

_DSH_ARTIFACTS = (
    (".agent-presets/agate/preset.yml", "preset.yml"),
    (".agent-presets/agate/agent.cordis.yml", "agent.cordis.yml"),
    ("skills/agate-protocol/SKILL.md", "SKILL.md"),
)


def _symlink_or_skip(target, link_path):
    try:
        os.symlink(str(target), str(link_path))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，无法构建 DSH 链接布局")


def test_dsh_links_no_dsh_dir_no_warning(run_cli, python_exe, agate_scripts, tmp_path):
    """无 ~/.dsh（未装 DSH）→ 校验整体跳过，无 DSH 相关警告。"""
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe, str(agate_scripts / "agate-summary.py"),
        cwd=str(project), env=_resolve_env(home),
    )
    assert result.returncode == 0
    assert "DSH 安装产物" not in result.output


@pytest.mark.windows_smoke
def test_dsh_links_canonical_chain_no_warning(run_cli, python_exe, agate_scripts, agate_assets, tmp_path):
    """三个产物软链均指向权威模板（{agate_root}/assets/templates/dsh/）→ 无警告。"""
    home = _make_home(tmp_path)
    tpl_dir = agate_assets / "templates" / "dsh"
    for rel, name in _DSH_ARTIFACTS:
        link = home / ".dsh" / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        _symlink_or_skip(tpl_dir / name, link)
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe, str(agate_scripts / "agate-summary.py"),
        cwd=str(project), env=_resolve_env(home),
    )
    assert result.returncode == 0
    assert "DSH 安装产物" not in result.output


def test_dsh_links_stale_target_warns_with_fix(run_cli, python_exe, agate_scripts, tmp_path):
    """软链指向非权威副本（真实 bug 复现）→ WARNING 指明产物 + 给出 ln -sf 修复命令。"""
    home = _make_home(tmp_path)
    stale_dir = tmp_path / "stale-copy"
    stale_dir.mkdir()
    for rel, name in _DSH_ARTIFACTS:
        stale_file = stale_dir / name
        stale_file.write_text("stale\n", encoding="utf-8")
        link = home / ".dsh" / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        _symlink_or_skip(stale_file, link)
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe, str(agate_scripts / "agate-summary.py"),
        cwd=str(project), env=_resolve_env(home),
    )
    assert result.returncode == 0
    assert "DSH 安装产物" in result.output
    assert "SKILL.md" in result.output
    assert "ln -sf" in result.output  # 附带一条命令即可修复


def test_dsh_links_missing_artifact_warns_not_installed(run_cli, python_exe, agate_scripts, agate_assets, tmp_path):
    """~/.dsh 存在但部分产物缺失 → 提示未安装（含 SETUP.md 指引），不误报为漂移。"""
    home = _make_home(tmp_path)
    tpl_dir = agate_assets / "templates" / "dsh"
    rel, name = _DSH_ARTIFACTS[0]
    link = home / ".dsh" / rel
    link.parent.mkdir(parents=True, exist_ok=True)
    _symlink_or_skip(tpl_dir / name, link)  # 只装 1 个，其余 2 个缺失
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(
        python_exe, str(agate_scripts / "agate-summary.py"),
        cwd=str(project), env=_resolve_env(home),
    )
    assert result.returncode == 0
    assert "未安装" in result.output
    assert "SETUP.md" in result.output


# --- Claude Code / OpenCode 产物校验（2026-09-21 补齐：四平台全覆盖）---
#
# 缺口实证：`agate-setup.py` 支持四个平台，而漂移检测此前只覆盖 DSH（后加 Codex）——
# CC/OC 的 orchestrator.md 漂移无人发现，而它恰是**最易漂**的产物之一（指向协议根的
# 模板文件，路径随版本布局变动）。本组锁定两平台的检测在位。


def _install_orch(home, tpl, platform_dir, *, symlink, content=None):
    link = home / platform_dir / "agents" / "orchestrator.md"
    link.parent.mkdir(parents=True, exist_ok=True)
    if symlink:
        _symlink_or_skip(tpl, link)
    else:
        link.write_bytes(content if content is not None else tpl.read_bytes())


@pytest.mark.parametrize("label,platform_dir", [
    ("Claude Code", ".claude"),
    ("OpenCode", ".config/opencode"),
])
def test_cc_oc_orchestrator_canonical_chain_no_warning(
        run_cli, python_exe, agate_scripts, agate_root, tmp_path, label, platform_dir):
    """CC/OC 的 orchestrator.md 软链指向权威模板 → 无警告。"""
    home = _make_home(tmp_path)
    _install_orch(home, agate_root / "orchestrator-template.md", platform_dir, symlink=True)
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert f"{label} 安装产物" not in result.output


@pytest.mark.parametrize("label,platform_dir", [
    ("Claude Code", ".claude"),
    ("OpenCode", ".config/opencode"),
])
def test_cc_oc_orchestrator_stale_target_warns(
        run_cli, python_exe, agate_scripts, tmp_path, label, platform_dir):
    """CC/OC 产物指向非权威副本 → 警告（回归：此前这两平台完全不在检测表内）。"""
    home = _make_home(tmp_path)
    stale = tmp_path / "stale-orch"
    stale.mkdir()
    (stale / "orchestrator.md").write_text("stale\n", encoding="utf-8")
    _install_orch(home, stale / "orchestrator.md", platform_dir, symlink=True)
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert f"{label} 安装产物" in result.output
    assert "orchestrator-template.md" in result.output  # 修复命令给出权威目标


# --- Codex 安装产物校验（2026-09-21：Codex 此前不在检测表内，产物漂移无人发现）---

_CODEX_ARTIFACTS = (("skills/agate-protocol/SKILL.md", "SKILL.md"),)


def _install_codex(home, tpl_dir, *, symlink, content=None):
    """按指定形态安装 Codex 产物：symlink=True 建软链，False 复制（可指定内容）。"""
    for rel, name in _CODEX_ARTIFACTS:
        link = home / ".agents" / rel
        link.parent.mkdir(parents=True, exist_ok=True)
        if symlink:
            _symlink_or_skip(tpl_dir / name, link)
        else:
            link.write_bytes(content if content is not None else (tpl_dir / name).read_bytes())


def _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path):
    project = tmp_path / "project"
    project.mkdir(exist_ok=True)
    return run_cli(
        python_exe, str(agate_scripts / "agate-summary.py"),
        cwd=str(project), env=_resolve_env(home),
    )


def test_codex_links_canonical_chain_no_warning(run_cli, python_exe, agate_scripts, agate_assets, tmp_path):
    """Codex 产物软链指向权威模板 → 无警告（回归：Codex 此前不在检测表内）。"""
    home = _make_home(tmp_path)
    _install_codex(home, agate_assets / "templates" / "codex", symlink=True)
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert "Codex 安装产物" not in result.output


def test_codex_links_stale_target_warns_with_fix(run_cli, python_exe, agate_scripts, tmp_path):
    """Codex 产物软链指向非权威副本 → 警告 + `ln -sf` 修复命令。"""
    home = _make_home(tmp_path)
    stale = tmp_path / "stale-codex"
    stale.mkdir()
    (stale / "SKILL.md").write_text("stale\n", encoding="utf-8")
    _install_codex(home, stale, symlink=True)
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert "Codex 安装产物" in result.output
    assert "SKILL.md" in result.output
    assert "ln -sf" in result.output


def test_codex_links_missing_artifact_warns_not_installed(run_cli, python_exe, agate_scripts, tmp_path):
    """`~/.agents` 存在但产物缺失 → 提示未安装（含 SETUP.md 指引），不误报为漂移。"""
    home = _make_home(tmp_path)
    (home / ".agents").mkdir(parents=True, exist_ok=True)
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert "Codex 安装产物未安装" in result.output
    assert "SETUP.md" in result.output


# --- 复制形态判定（2026-09-21 修：原实现只比 realpath，对复制产物必然误报）---
#
# 为什么必须测：Windows 无符号链接权限 / AGATE_HOOK_COPY_MODE=1 时产物是**复制**，
# 其 realpath 天然不等于模板路径 → 旧实现会把正常安装报成"漂移"。此前靠
# `os.name == "nt"` 整体跳过掩盖（Linux 复制模式则会误报）。复制模式的正确判据是
# **内容一致**，且它恰好也是"模板升级后副本变旧"这一固有风险的唯一检出方式。


def test_copy_mode_identical_content_no_warning(run_cli, python_exe, agate_scripts, agate_assets, tmp_path):
    """复制形态且内容与权威模板一致 → 无警告（回归：旧实现必然误报漂移）。"""
    home = _make_home(tmp_path)
    _install_codex(home, agate_assets / "templates" / "codex", symlink=False)
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert "Codex 安装产物" not in result.output, (
        f"复制形态内容一致时不得报警（旧实现比 realpath 会误报漂移）:\n{result.output}"
    )


def test_copy_mode_stale_content_warns_outdated(run_cli, python_exe, agate_scripts, agate_assets, tmp_path):
    """复制形态但内容已旧（模板升级未重跑 setup）→ 警告"已过期" + 修复命令。"""
    home = _make_home(tmp_path)
    _install_codex(home, agate_assets / "templates" / "codex", symlink=False,
                   content=b"# outdated copy\n")
    result = _run_summary(run_cli, python_exe, agate_scripts, home, tmp_path)
    assert result.returncode == 0
    assert "Codex 安装产物已过期" in result.output
    assert "agate-setup.py" in result.output  # 修复命令是重跑接入命令，不是 ln -sf


# ============================================================
# TAG0037 P3 组 B（批 E）：软链基址迁移提示（BDD-34）、协议入口路径取自解析出的根（BDD-40 代码面）、
#   软链 → 完整版本根不打印迁移提示（BDD-51 / eng N-4）、包内脚本冒烟（BDD-52，排除 agate/tests/ 后缺目录无 Traceback）。
#   被测：agate-summary.py（P4 批 E：root 为 None 且 symlink_base 才追加迁移提示行；启动建议 2 取 {root}/AGENTS.md）。
# ============================================================

# 拼接构造：BDD-40 全仓 grep 不许非历史文件源码直接含该字面量
_STALE_ENTRY = "~/.agate/" + "AGENTS.md"

_STEP_RES = {
    "backup": re.compile(r"mv\s+~?/?\.agate\s+\S*\.bak"),
    "mkdir": re.compile(r"mkdir\s+-p\s+~?/?\.agate"),
    "install": re.compile(r"install\.sh\s+--versions"),
}


def _symlink_home(tmp_path, with_versions=False):
    target = tmp_path / "src" / "agate"
    if with_versions:
        (target / "v0.73.0" / "agate" / "scripts").mkdir(parents=True)
        os.symlink("v0.73.0", str(target / "latest"))
        os.symlink("latest", str(target / "current"))
    else:
        (target / "scripts").mkdir(parents=True)
        (target / "assets").mkdir()
    (target / "canary.txt").write_text("canary\n", encoding="utf-8")
    home = tmp_path / "home"
    home.mkdir()
    try:
        os.symlink(str(target), str(home / ".agate"))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链，软链布局无法构建")
    return home, target


def test_bdd_34_summary_symlink_home_prints_migration_hint_instead_of_silent_failure(run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-34：软链 ~/.agate（存量用户 git pull 后每会话启动跑 agate-summary 的场景）——进程不崩溃；AGATE_ROOT 行明确为"无可用"；
    输出含一行迁移提示（含 mv ~/.agate ~/.agate.bak）；启动建议不再硬编码用户主目录下的旧协议入口路径；软链目标内容不变。"""
    home, target = _symlink_home(tmp_path)
    before = H.snapshot_tree(target)
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(python_exe, str(agate_scripts / "agate-summary.py"), cwd=str(project), env=_resolve_env(home))
    assert result.returncode == 0, result.output
    assert "Traceback" not in result.output
    assert "AGATE_ROOT：（无可用 AGATE_ROOT）" in result.output
    assert "mv ~/.agate ~/.agate.bak" in result.output
    for key, rx in _STEP_RES.items():
        assert rx.search(result.output), f"迁移提示缺三步片段 {key}"
    assert _STALE_ENTRY not in result.output, f"启动建议不得硬编码 {_STALE_ENTRY}（BDD-40）"
    assert "legacy" not in result.output.lower()
    assert H.snapshot_tree(target) == before


def test_bdd_40_summary_startup_suggestion_uses_resolved_root(run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-40（代码面）：启动建议中的协议入口路径取自解析出的根（`读 {AGATE_ROOT}/AGENTS.md`），不再是硬编码的用户主目录旧入口路径。"""
    home = _make_home(tmp_path)
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(python_exe, str(agate_scripts / "agate-summary.py"), cwd=str(project), env=_resolve_env(home))
    assert result.returncode == 0, result.output
    root = str((home / ".agate" / "v0.44.0").resolve())
    assert f"读 {root}/AGENTS.md" in result.output
    assert _STALE_ENTRY not in result.output


@pytest.mark.skipif(sys.platform == "win32", reason="软链断言仅 POSIX")
def test_bdd_51_summary_symlink_to_full_version_root_prints_no_migration_hint(run_cli, python_exe, agate_scripts, tmp_path):
    """BDD-51 / eng N-4：软链基址但经 current 链正常解析（目标是完整版本根）——summary exit 0、版本正确、**不**打印迁移提示（不是 legacy 布局）；
    启动建议取解析出的根。"""
    home, target = _symlink_home(tmp_path, with_versions=True)
    project = tmp_path / "project"
    project.mkdir()
    result = run_cli(python_exe, str(agate_scripts / "agate-summary.py"), cwd=str(project), env=_resolve_env(home))
    assert result.returncode == 0, result.output
    root = str((target / "v0.73.0" / "agate").resolve())
    assert "版本：v0.73.0" in result.output
    assert f"读 {root}/AGENTS.md" in result.output
    assert "mv ~/.agate ~/.agate.bak" not in result.output


def test_bdd_52_scripts_inside_the_body_package_without_agate_tests_have_no_traceback(tmp_path, agate_scripts):
    """BDD-52：按 BDD-2 基线值生成的本体包（真实仓库 HEAD 经 agate_package.materialize，**不含** agate/tests/）解出的目录树作 AGATE_ROOT，
    在其中运行 check-platform-assumptions.py（无参，默认扫描 agate/tests/）、agate-risk-score.py（无参与传入一个 TASK_DIR 两种调用，C-2）、
    agate-summary.py、agate-resolve.py——输出均不含 Traceback；退出码落在各自既有契约内：
    check-platform-assumptions 非 0 且含"目标不存在"；risk-score 为 0 / 1（用法或 git_ok:false 降级输出）；summary / resolve 为 0。"""
    pkg = H.load_project_module(agate_scripts, "agate_package.py", "agate_package")
    tree = tmp_path / "pkgtree"
    tree.mkdir()
    pkg.materialize(str(H.REPO_ROOT), "HEAD", str(tree))
    assert not (tree / "agate" / "tests").exists(), "Given：包内不含 agate/tests/"
    scripts = tree / "agate" / "scripts"
    home = tmp_path / "isolated-home"
    home.mkdir()
    task_dir = tmp_path / "task-dir"
    task_dir.mkdir()
    env = H.tool_env(home, extra={"AGATE_ROOT": str(tree / "agate")})

    def run(name, *args):
        return H.run_tool([sys.executable, "-B", scripts / name, *args], env=env, cwd=tree)

    plat = run("check-platform-assumptions.py")
    assert "Traceback" not in plat.stdout + plat.stderr
    assert plat.returncode != 0 and "目标不存在" in plat.stdout + plat.stderr
    for args in ((), (task_dir,)):
        risk = run("agate-risk-score.py", *args)
        assert "Traceback" not in risk.stdout + risk.stderr, risk.stderr
        assert risk.returncode in (0, 1)
    # summary / resolve：包内无 current 指针，走 AGATE_ROOT env 覆盖 → exit 0
    for name in ("agate-summary.py", "agate-resolve.py"):
        r = run(name)
        assert "Traceback" not in r.stdout + r.stderr, r.stderr
        assert r.returncode == 0, r.stdout + r.stderr
