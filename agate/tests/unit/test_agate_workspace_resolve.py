# tests/unit/test_agate_workspace_resolve.py — 工作区路径解析器单元测试
# （agate-workspace-resolve.bats 10 用例迁移，TAG0011 批次 0）
# 被测：agate/scripts/agate_common.py（resolve_workspace 执行模式）
# 接口契约：python3 agate_common.py [PROJECT_ROOT]，输出两行
#   AGATE_WORKSPACE=<绝对路径> 与 AGATE_TASKS_DIR=<绝对路径>
# 解析优先级：.agate.env 显式配置 > 环境变量 AGATE_TASKS_DIR > 默认 agate-workspace/

import os
import shutil
from pathlib import Path

import pytest

import helpers_tag_repo as H


def _ws_out(result):
    """从合并流提取 AGATE_WORKSPACE 值（bats ws_out 等价，grep ^AGATE_WORKSPACE=）。"""
    for line in result.output.splitlines():
        if line.startswith("AGATE_WORKSPACE="):
            return line[len("AGATE_WORKSPACE="):]
    return ""


def _tasks_out(result):
    """从合并流提取 AGATE_TASKS_DIR 值（bats tasks_out 等价）。"""
    for line in result.output.splitlines():
        if line.startswith("AGATE_TASKS_DIR="):
            return line[len("AGATE_TASKS_DIR="):]
    return ""


def _realpath(path):
    """realpath -m 等价：规范化绝对路径（目标可不存在）。"""
    return os.path.realpath(str(path))


def _resolve(agate_scripts, python_exe, run_cli, project, env=None):
    return run_cli(python_exe, str(agate_scripts / "agate_common.py"), str(project), env=env)


@pytest.mark.windows_smoke
def test_wr_1_bdd_2_default_workspace_location(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    assert _ws_out(result) == _realpath(project / "agate-workspace")
    assert _tasks_out(result) == _realpath(project / "agate-workspace" / "tasks")


def test_wr_2_bdd_4_no_env_file_uses_default(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    assert _ws_out(result).endswith("/agate-workspace")
    assert _tasks_out(result).endswith("/agate-workspace/tasks")


def test_wr_3_bdd_3_env_file_absolute_external(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    ext_ws = tmp_path / "ext"
    ext_ws.mkdir()
    (project / ".agate.env").write_text(f"AGATE_WORKSPACE={ext_ws}\n", encoding="utf-8")
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    assert _ws_out(result) == _realpath(ext_ws)
    assert _tasks_out(result) == _realpath(ext_ws / "tasks")
    assert not (project / "agate-workspace").exists()


def test_wr_4_bdd_3_env_file_relative_to_project(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    (project / ".agate.env").write_text("AGATE_WORKSPACE=my-ws\n", encoding="utf-8")
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    assert _ws_out(result) == _realpath(project / "my-ws")
    assert _tasks_out(result) == _realpath(project / "my-ws" / "tasks")


def test_wr_5_bdd_5_path_with_spaces(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    (project / ".agate.env").write_text(
        "AGATE_WORKSPACE=My Project/agate-workspace\n", encoding="utf-8"
    )
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    assert _ws_out(result) == _realpath(project / "My Project" / "agate-workspace")
    assert _tasks_out(result) == _realpath(project / "My Project" / "agate-workspace" / "tasks")


def test_wr_6_bdd_13_env_var_agate_tasks_dir_secondary_source(
    agate_scripts, python_exe, run_cli, tmp_path
):
    project = tmp_path / "ws"
    project.mkdir()
    tasks_base = _realpath(project / "legacy-tasks")
    result = _resolve(agate_scripts, python_exe, run_cli, project, env={"AGATE_TASKS_DIR": tasks_base})
    assert result.returncode == 0
    assert _tasks_out(result) == tasks_base


def test_wr_7_bdd_13_env_file_wins_over_env_var(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    (project / ".agate.env").write_text("AGATE_WORKSPACE=env-wins\n", encoding="utf-8")
    result = _resolve(
        agate_scripts,
        python_exe,
        run_cli,
        project,
        env={"AGATE_TASKS_DIR": _realpath(project / "ignored-tasks")},
    )
    assert result.returncode == 0
    assert _ws_out(result) == _realpath(project / "env-wins")
    assert _tasks_out(result) == _realpath(project / "env-wins" / "tasks")


def test_wr_8_bdd_11_project_md_anchor(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    ws = Path(_ws_out(result))
    assert str(ws) != ""
    assert _realpath(ws / "agents" / "project.md") == _realpath(
        project / "agate-workspace" / "agents" / "project.md"
    )


def test_wr_9_bdd_12_tasks_board_anchor(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    tasks = Path(_tasks_out(result))
    assert str(tasks) != ""
    assert _realpath(tasks / "active-tasks.md") == _realpath(
        project / "agate-workspace" / "tasks" / "active-tasks.md"
    )


@pytest.mark.windows_smoke
def test_bdd_18_crlf_does_not_pollute_workspace(agate_scripts, python_exe, run_cli, tmp_path):
    project = tmp_path / "ws"
    project.mkdir()
    (project / ".agate.env").write_bytes(b"AGATE_WORKSPACE=ws-crlf\r\n")
    result = _resolve(agate_scripts, python_exe, run_cli, project)
    assert result.returncode == 0
    assert _ws_out(result) == _realpath(project / "ws-crlf")


# ============================================================
# TAG0037 P3 组 B（批 E）：agate_common 现依赖 agate_package.py（from agate_package import agate_home）——
#   BDD-47（hook / 解析入口不受影响）代码面：仅拷 agate_common.py + agate_package.py 的最小 scripts 目录（贴近"版本目录 / 拷贝复制模式"
#   的真实形态）里，工作区解析执行模式照常工作；BDD-28：AGATE_HOME 指向软链不影响工作区解析（它只关心 PROJECT_ROOT，不是版本根）。
# ============================================================


def test_bdd_47_workspace_resolve_runs_from_minimal_scripts_dir_with_agate_package(agate_scripts, python_exe, run_cli, tmp_path):
    """BDD-47：把 agate_common.py 与它的新依赖 agate_package.py 拷入一个最小目录后运行工作区解析——exit 0、两行输出照常。
    （agate_package.py 不存在 = P4 前的 B 类红灯；拷贝漏带它则 agate_common 会 ModuleNotFoundError，eng N-1。）"""
    minimal = tmp_path / "minimal-scripts"
    minimal.mkdir()
    for name in ("agate_common.py", "agate_package.py"):
        src = agate_scripts / name
        assert src.is_file(), f"{name} 缺失（被测模块未实现）"
        shutil.copy2(str(src), str(minimal / name))
    project = tmp_path / "ws"
    project.mkdir()
    result = run_cli(python_exe, str(minimal / "agate_common.py"), str(project))
    assert result.returncode == 0, result.output
    assert "ModuleNotFoundError" not in result.output
    assert _ws_out(result) == _realpath(project / "agate-workspace")
    assert _tasks_out(result) == _realpath(project / "agate-workspace" / "tasks")


@pytest.mark.skipif(os.name == "nt", reason="软链断言仅 POSIX")
def test_bdd_28_workspace_resolve_unaffected_by_symlink_agate_home(agate_scripts, python_exe, run_cli, tmp_path):
    """BDD-28：AGATE_HOME 指向软链（版本根基址概念）不影响工作区解析——工作区只随 PROJECT_ROOT / .agate.env（与解析链无关）。"""
    real = tmp_path / "some-root"
    real.mkdir()
    link = tmp_path / "link-home"
    try:
        os.symlink(str(real), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("当前平台无法创建软链")
    project = tmp_path / "ws"
    project.mkdir()
    result = _resolve(agate_scripts, python_exe, run_cli, project, env={"AGATE_HOME": str(link)})
    assert result.returncode == 0, result.output
    assert _ws_out(result) == _realpath(project / "agate-workspace")
    assert H.snapshot_tree(real) == {}, "不得往软链目标写任何内容"


# ── RM-AG0084 / DEBT0028：resolve_workspace_from_task_dir（三处消费方共用的单源实现）─────

def _load_agate_common(agate_scripts):
    """以文件路径加载 agate_common 模块（文件名无 `-`，但为与其它测试一致仍用 importlib）。

    `agate_common` 依赖**同目录**的兄弟模块（`agate_package` 等）⇒ 加载前把 scripts 目录
    加入 `sys.path`。
    """
    import importlib.util
    import sys

    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "_ac_ws_resolve_test", agate_scripts / "agate_common.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["_ac_ws_resolve_test"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_rm_ag0084_from_task_dir_default_layout(tmp_path, agate_scripts):
    """默认布局：`<root>/agate-workspace/tasks/T1` → 工作区 = `<root>/agate-workspace`。"""
    root = tmp_path / "proj"
    task = root / "agate-workspace" / "tasks" / "T1"
    task.mkdir(parents=True)

    mod = _load_agate_common(agate_scripts)
    got = mod.resolve_workspace_from_task_dir(str(task))
    assert _realpath(got) == _realpath(root / "agate-workspace"), got


def test_rm_ag0084_from_task_dir_env_override(tmp_path, agate_scripts):
    """`.agate.env` 的 `AGATE_WORKSPACE=` 覆盖：旧的两级 dirname 会算错，本实现须算对。"""
    root = tmp_path / "proj"
    (root / "agate-workspace" / "tasks" / "T1").mkdir(parents=True)
    (root / ".agate.env").write_text("AGATE_WORKSPACE=custom-ws\n", encoding="utf-8")
    (root / "custom-ws" / "tasks" / "T1").mkdir(parents=True)

    mod = _load_agate_common(agate_scripts)
    got = mod.resolve_workspace_from_task_dir(str(root / "agate-workspace" / "tasks" / "T1"))
    assert _realpath(got) == _realpath(root / "custom-ws"), got


def test_rm_ag0084_from_task_dir_external_workspace_not_double_nested(tmp_path, agate_scripts):
    """**外部工作区**（`AGATE_WORKSPACE=` 指向项目外）+ task_dir 在 git 仓库外：
    须返回工作区本身，**不得**多套一层 `agate-workspace/`。

    这是 SELF-GATE r2 实测到的回归：用 `git rev-parse --show-toplevel` 取项目根时，
    该场景 `show-toplevel` 失败 ⇒ 把回退值（= 工作区本身）再喂 `resolve_workspace`
    ⇒ 得到 `<ws>/agate-workspace/debt/tech-debt.md`（错）⇒ gate_p7 `return 1` 误阻断。
    """
    ext = tmp_path / "ext-ws"
    task = ext / "tasks" / "T1"
    task.mkdir(parents=True)
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / ".agate.env").write_text(f"AGATE_WORKSPACE={ext}\n", encoding="utf-8")

    mod = _load_agate_common(agate_scripts)
    got = mod.resolve_workspace_from_task_dir(str(task))
    assert _realpath(got) == _realpath(ext), got
    assert not got.endswith(os.path.join("agate-workspace", "").rstrip(os.sep)), got
