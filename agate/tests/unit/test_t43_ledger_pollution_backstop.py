# tests/unit/test_t43_ledger_pollution_backstop.py — DEBT0040 ③（CI 账本污染兜底）
#
# 缺陷形态（TAG0034 复盘实测）：测试真实调用 `agate_common.append_event` 且 `task_dir` 指向
# **仓库内**已提交账本，把 judge_verdict 事件追加进历史任务的 `gate-events.jsonl`（非本次任务
# 目录），事后需人工 `git checkout` 复原。已提交状态文件共 68 个（`gate-events.jsonl` /
# `active-tasks.md` / `.state.yaml` 三族，其中 5 个是 `agate/tests/fixtures/` 下的夹具副本）。
#
# DEBT0040 的 closure_criteria 第 ③ 条要求「CI 有 `git diff --exit-code` 账本兜底步（或等效
# 机制），故意污染能被 CI 捕获」。①②（角色文件条文 + 静态 lint）已在 TAG0042 批完成，
# 本条长期空着——因为 CI 改动需用户许可。
#
# ⚠️ **架构约束（本组测试的核心理由）**：兜底**必须放在 `pytest` job 内**、在全量测试**之后**。
#    因为 GitHub Actions 每个 job 各有独立 runner 与独立 checkout —— 放在 `gate-backstop`
#    这类独立 job 里，它看到的是**全新干净工作树**，永远观测不到 `pytest` job 的副作用，
#    只会有「看起来有兜底」的假象（本仓高发的「声称有、实际无」）。故「位于 pytest job 内
#    且在全量测试步骤之后」被固化为机械判据。
#
# ⚠️ **为什么不是快照式断言**：TAG0042 的初版哨兵用 `git status` 读**当前脏状态**，在
#    `-n auto` 下因执行顺序**静默漏报**（评审实测复现）。本批改走**事后独立观测**（CI 步骤）
#    + **静态源码判据**（已有 `test_t42_*`），二者互补，均不依赖测试执行顺序。
#
# 平台无关：YAML 用 pyyaml 解析；合成仓用既有 `git_repo` fixture；不使用临时目录字面量。

import importlib.util
import os
from pathlib import Path

import pytest
import yaml

WORKFLOW_REL = ".github/workflows/protocol-tests.yml"
SCRIPT_REL = "agate/scripts/check-ledger-pollution.py"

# 本批的兜底路径面：三族状态文件的**仓库内**落点（含 fixtures 副本）
STATE_SURFACES = ("agate-workspace", "agate/tests/fixtures")


def _repo_root(agate_root: Path) -> Path:
    return Path(agate_root).parent


def _load_workflow(agate_root: Path) -> dict:
    return yaml.safe_load((_repo_root(agate_root) / WORKFLOW_REL).read_text(encoding="utf-8"))


def _job_steps(wf: dict, job: str) -> list:
    return wf["jobs"][job]["steps"]


def _step_index_containing(steps: list, needle: str) -> int:
    for i, step in enumerate(steps):
        if needle in (step.get("run") or ""):
            return i
    return -1


def _load_backstop(agate_scripts: Path):
    path = os.path.join(str(agate_scripts), "check-ledger-pollution.py")
    spec = importlib.util.spec_from_file_location("lbp", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# 1. workflow 定位：必须在 pytest job 内、且在全量测试之后（架构约束）
# ---------------------------------------------------------------------------


@pytest.mark.windows_smoke
def test_t43lb_1_backstop_step_lives_in_pytest_job(agate_root):
    """兜底步必须在 `pytest` job 内——独立 job 的 checkout 观测不到 pytest 的副作用。

    这是本组的**核心判据**：放错 job 会让兜底**在结构上不可能生效**，却看起来已就位。
    """
    wf = _load_workflow(agate_root)
    assert "pytest" in wf["jobs"], "workflow 结构已变：找不到 pytest job"
    steps = _job_steps(wf, "pytest")
    idx = _step_index_containing(steps, "check-ledger-pollution.py")
    assert idx >= 0, (
        f"pytest job 内没有调用 {SCRIPT_REL} 的步骤——DEBT0040③ 未落实。"
        "注意**不可**放进 gate-backstop 等独立 job：独立 runner 的干净 checkout "
        "观测不到 pytest job 的副作用，那样只是「看起来有兜底」"
    )


def test_t43lb_2_backstop_runs_after_full_suite(agate_root):
    """兜底步必须排在全量 pytest **之后**（否则观测不到污染）。"""
    steps = _job_steps(_load_workflow(agate_root), "pytest")
    suite_idx = _step_index_containing(steps, "-m pytest agate/tests/ --reruns 1 -n auto")
    assert suite_idx >= 0, "找不到全量测试步骤（workflow 已变，请同步本测试）"
    backstop_idx = _step_index_containing(steps, "check-ledger-pollution.py")
    assert backstop_idx > suite_idx, (
        f"兜底步（#{backstop_idx}）须排在全量测试（#{suite_idx}）之后，否则看不到跑测副作用"
    )


def test_t43lb_3_backstop_respects_docs_only_fast_pass(agate_root):
    """兜底步须与同 job 其他步骤一致地处理 docs-only 快路径，避免纯文档 PR 误红。"""
    steps = _job_steps(_load_workflow(agate_root), "pytest")
    idx = _step_index_containing(steps, "check-ledger-pollution.py")
    assert idx >= 0, (
        "找不到兜底步——**不要**让本断言在缺失时退化成 steps[-1]（那会命中同样含 docs_only 的"
        "其他步骤而真空通过；本用例初版即踩此坑）"
    )
    run = steps[idx]["run"]
    assert "docs_only" in run, "兜底步未处理 docs-only 快路径（纯文档 PR 会因历史账本误红）"


# ---------------------------------------------------------------------------
# 2. 脚本行为：非真空（合成仓上正/负向都验）
# ---------------------------------------------------------------------------


def test_t43lb_4_script_exists_and_is_importable(agate_scripts):
    mod = _load_backstop(agate_scripts)
    assert callable(getattr(mod, "main", None)), f"{SCRIPT_REL} 缺 main()"
    assert hasattr(mod, "STATE_PATHS"), f"{SCRIPT_REL} 未暴露 STATE_PATHS（可测的路径面）"


def test_t43lb_5_clean_repo_passes(agate_scripts, git_repo, python_exe, run_cli):
    """干净仓（状态文件已提交、未改动）→ exit 0（不误报）。"""
    d = git_repo.path / "agate-workspace" / "tasks" / "T0001"
    d.mkdir(parents=True)
    (d / "gate-events.jsonl").write_text('{"event":"x"}\n', encoding="utf-8")
    git_repo.commit("seed")

    r = run_cli(python_exe, str(agate_scripts / "check-ledger-pollution.py"), str(git_repo.path))
    assert r.returncode == 0, f"干净仓被误报：stdout={r.stdout!r} stderr={r.stderr!r}"


def test_t43lb_6_modified_tracked_ledger_is_caught(agate_scripts, git_repo, python_exe, run_cli):
    """负向：已提交账本被追加一行 → exit 1 且报出路径（DEBT0040 的原始形态）。"""
    d = git_repo.path / "agate-workspace" / "tasks" / "T0001"
    d.mkdir(parents=True)
    ledger = d / "gate-events.jsonl"
    ledger.write_text('{"event":"x"}\n', encoding="utf-8")
    git_repo.commit("seed")
    with ledger.open("a", encoding="utf-8") as fh:
        fh.write('{"event":"judge_verdict"}\n')

    r = run_cli(python_exe, str(agate_scripts / "check-ledger-pollution.py"), str(git_repo.path))
    assert r.returncode == 1, f"账本污染未被捕获：rc={r.returncode} out={r.stdout!r}"
    assert "gate-events.jsonl" in r.stdout, "未报出被污染文件路径"


def test_t43lb_7_new_untracked_state_file_is_caught(agate_scripts, git_repo, python_exe, run_cli):
    """负向：跑测**新建**的未跟踪账本也要捕获（`git diff` 单独用会漏这类）。"""
    (git_repo.path / "README.md").write_text("seed\n", encoding="utf-8")
    git_repo.commit("seed")
    newdir = git_repo.path / "agate-workspace" / "tasks" / "TNEW"
    newdir.mkdir(parents=True)
    (newdir / "gate-events.jsonl").write_text('{"event":"new"}\n', encoding="utf-8")

    r = run_cli(python_exe, str(agate_scripts / "check-ledger-pollution.py"), str(git_repo.path))
    assert r.returncode == 1, f"新建未跟踪账本未被捕获：rc={r.returncode} out={r.stdout!r}"


def test_t43lb_8_fixture_copy_pollution_is_caught(agate_scripts, git_repo, python_exe, run_cli):
    """负向：`agate/tests/fixtures/` 下的夹具副本被写脏也要捕获（DEBT0040 明列的面）。"""
    d = git_repo.path / "agate" / "tests" / "fixtures" / "full-task"
    d.mkdir(parents=True)
    st = d / ".state.yaml"
    st.write_text("phase: P1\n", encoding="utf-8")
    git_repo.commit("seed")
    st.write_text("phase: P6\n", encoding="utf-8")

    r = run_cli(python_exe, str(agate_scripts / "check-ledger-pollution.py"), str(git_repo.path))
    assert r.returncode == 1, f"fixture 副本污染未被捕获：rc={r.returncode} out={r.stdout!r}"


def test_t43lb_9_non_git_dir_is_fail_closed(agate_scripts, tmp_path, python_exe, run_cli):
    """无法判定（非 git 目录）→ exit 2，不得静默报"通过"。"""
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    r = run_cli(python_exe, str(agate_scripts / "check-ledger-pollution.py"), str(plain))
    assert r.returncode == 2, f"非 git 目录应 exit 2（fail-closed，不静默通过），实得 {r.returncode}"


def test_t43lb_11_normal_workspace_doc_edit_is_not_pollution(agate_scripts, git_repo, python_exe, run_cli):
    """回归（独立评审 2026-09-29 MAJOR）：`agate-workspace/` 下的**正常文档编辑**不得判为污染。

    初版用**目录** pathspec（`agate-workspace`），于是任何改到 debt/roadmap/tasks 文档的提交都被
    判成污染——**包括本债自己的闭合记录** `agate-workspace/debt/tech-debt.md`。后果是该兜底
    「只在本来就没有任何东西需要检查的树上才绿」，等于**零覆盖**（且会让引入它的那个 PR 自己红）。
    现 pathspec 精确到三族状态文件名，故正常文档编辑必须 exit 0。
    """
    d = git_repo.path / "agate-workspace" / "debt"
    d.mkdir(parents=True)
    doc = d / "tech-debt.md"
    doc.write_text("# 技术债\n", encoding="utf-8")
    # 同时放一个**真实**状态文件，确认它不因"目录里还有别的文件"而被牵连
    task = git_repo.path / "agate-workspace" / "tasks" / "T0001"
    task.mkdir(parents=True)
    (task / "gate-events.jsonl").write_text('{"event":"x"}\n', encoding="utf-8")
    git_repo.commit("seed")

    with doc.open("a", encoding="utf-8") as fh:
        fh.write("\n## DEBT9999\n新登记一条债务（正常文档编辑）\n")

    r = run_cli(python_exe, str(agate_scripts / "check-ledger-pollution.py"), str(git_repo.path))
    assert r.returncode == 0, (
        f"正常文档编辑被误判为账本污染（DEBT0040③ 的零覆盖形态）：rc={r.returncode} out={r.stdout!r}"
    )


def test_t43lb_12_state_paths_are_filename_scoped_not_directory(agate_scripts):
    """判据固化：pathspec 必须是**状态文件名**级（含 magic glob），不得退化为目录级。

    目录级写法会误报同子树下的文档编辑（见 t43lb_11）。本断言防有人"简化"回目录。
    """
    mod = _load_backstop(agate_scripts)
    paths = tuple(mod.STATE_PATHS)
    assert paths, "STATE_PATHS 为空"
    assert all(":(glob)" in p for p in paths), (
        f"pathspec 未使用 magic glob（可能被退回目录级写法，会误报文档编辑）：{paths}"
    )
    for fam in ("gate-events.jsonl", "active-tasks.md", ".state.yaml"):
        assert any(fam in p for p in paths), f"pathspec 未覆盖状态文件族：{fam}"
    # 目录级写法特征：某个 pathspec 恰为裸目录名（无 glob、无文件名）
    assert not any(p in ("agate-workspace", "agate/tests/fixtures") for p in paths), (
        "存在裸目录 pathspec——这正是被评审判定为零覆盖的写法"
    )


def test_t43lb_10_state_paths_cover_three_families(agate_scripts):
    """路径面须覆盖 workspace 与 fixtures 两处（三族状态文件的仓库内落点）。"""
    mod = _load_backstop(agate_scripts)
    paths = tuple(mod.STATE_PATHS)
    assert any("agate-workspace" in p for p in paths), "路径面未覆盖 agate-workspace/"
    assert any("fixtures" in p for p in paths), "路径面未覆盖 agate/tests/fixtures/"

