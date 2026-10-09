# agate/tests/unit/test_agate_ci_verify.py
# TAG0042 批 5（CI 与诊断）红灯测试 —— BDD-16。
#
# 目标语义（P1 BDD-16，P2-design §4.4 + §1.1 M13/M15）：
#   * BDD-16：`agate-ci-verify` 替换 `ci-gate-backstop`——它**实际重跑** gate 判定
#     （不再是「永远 SKIP 却显示绿」的假绿），无适用场景时**显式声明「跳过 + 原因」**，
#     且「跳过」与「通过」在输出上**可区分**。
#   * CHECK 10 方向（P2 §4.4）：退役 `ci-gate-backstop.py` 时，workflow 与协议文档的引用
#     须同步更新，否则 `CHECK10-scriptref` 会新增 ERROR。
#
# 现行为（改动前）：`agate/scripts/agate-ci-verify.py` **不存在**；
#   `.github/workflows/protocol-tests.yml` 仍调 `ci-gate-backstop.py`；
#   多个协议文档仍引用 `ci-gate-backstop.py` ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：红灯原因须为「被测模块未实现」——脚本文件缺失（B 类）
#   与断言失败（行为未改 = B 类），而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 平台无关：tmp_path / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；不写仓库内已提交文件（全在 tmp_path / git_repo 内）。

import importlib.util
import re
import shutil
from pathlib import Path

# 被测 CLI（批 5 新增；当前不存在 ⇒ 红灯 = 模块未实现）
_CI_VERIFY_SCRIPT = "agate-ci-verify.py"

# 被替换/退役的现状实现（批 5 退役对象）
_RETIRED_BACKSTOP = "ci-gate-backstop.py"

# 退役脚本的裸名（协议文档引用面：CHECK10 只报 `.py` 形式，但退役后文档亦不应再引用其名）
_RETIRED_BACKSTOP_NAME = "ci-gate-backstop"

# CI workflow（批 5 M15：gate-backstop job 改调 agate-ci-verify.py）
_WORKFLOW = ".github/workflows/protocol-tests.yml"

# CHECK10-scriptref 扫描面（非豁免协议文件）中当前引用被退役脚本的文件：
# 退役后须同步更新引用（否则 CHECK10-scriptref 新增 ERROR）。
# 说明：`agate/UPGRADING.md` 整文件豁免、`CHANGELOG.md` 属叙事文件降级 WARNING，
# 均不在本断言面；`agate/scripts/README.md` 另有「退役名豁免」通道，亦不列入。
_PROTOCOL_REFS_TO_SYNC = (
    "agate/WORKFLOW.md",
    "agate/state-machine.md",
    "agate/platform-notes.md",
    "agate/dispatch-protocol.md",
    "agate/phase-cards/P3-tdd.md",
    "agate/assets/templates/retrospective-template.md",
)


def _run_ci_verify(agate_scripts, python_exe, run_cli, *args, cwd=None, env=None):
    """运行 agate-ci-verify.py。当前脚本不存在 ⇒ subprocess 返回非 0 + 'No such file'。"""
    return run_cli(
        python_exe,
        str(agate_scripts / _CI_VERIFY_SCRIPT),
        *args,
        cwd=cwd,
        env=env,
    )


def _setup_failing_gate_repo(git_repo):
    """构造一个 gate 判定**会失败**的 agate 项目。

    phase=P1 且任务目录**缺** `P1-review.md` ⇒ `check-gate.py P1` 返回 1（失败）。
    同时提供仓库根 `.state.yaml`（现状 ci-gate-backstop 的定位约定）与任务级
    `.state.yaml`（agate 任务状态的实际存放位置），使替换实现无论按哪种约定定位都能命中。
    """
    repo = git_repo.path
    # 固定协议版本：使回放能真正跑到 gate 判定（未写 `.agate-version` 的使用者项目会先被判 FAIL，
    # 那是 BDD-31 的口径；本用例要验的是"回放 gate 失败 → FAIL"，故须先钉版本）。
    (repo / ".agate-version").write_text("agate: v0.79.0\n", encoding="utf-8")
    task = repo / "agate-workspace" / "tasks" / "T001"
    task.mkdir(parents=True)
    state = "task_id: T001\nphase: P1\nstatus: active\nretries: {}\n"
    (repo / ".state.yaml").write_text(state, encoding="utf-8")
    (task / ".state.yaml").write_text(state, encoding="utf-8")
    (task / "P1-requirements.md").write_text(
        "---\nagent: test\n---\n#### BDD-1: x\n- Given a\n- When b\n- Then c\n",
        encoding="utf-8",
    )
    git_repo.commit("p1 failing gate")
    return repo, task


# ── BDD-16：agate-ci-verify 替换 ci-gate-backstop 且无假绿 ──────────────────
#
# Given 一次 push / PR
# When 运行 `agate-ci-verify`
# Then 它**实际重跑** gate 判定（不再是永远 SKIP 却显示绿），无适用场景时显式声明
#      「跳过 + 原因」（「跳过」与「通过」在输出上可区分）


def test_bdd_16_ci_verify_script_exists(agate_scripts):
    """BDD-16：批 5 新增 `agate-ci-verify.py`（替换 ci-gate-backstop）。

    Given 批 5 的实现对象
    When 检查脚本文件
    Then `agate-ci-verify.py` 存在。

    现行为：脚本不存在 ⇒ 红灯（模块未实现）。
    """
    script = agate_scripts / _CI_VERIFY_SCRIPT
    assert script.is_file(), (
        f"BDD-16：{_CI_VERIFY_SCRIPT} 不存在（批 5 未实现）——"
        "它是替换 ci-gate-backstop 的 CI 兜底实现"
    )


def test_bdd_16_ci_verify_reruns_gate_and_reports_failure(
    git_repo, agate_root, agate_scripts, python_exe, run_cli
):
    """BDD-16（无假绿）：gate 判定失败时，ci-verify 必须**如实失败**（非 0 + FAIL）。

    Given 一个 gate 判定会失败的项目（phase=P1，缺 P1-review.md）
    When 以 `--base <前序提交>` 逐提交回放（TAG0050 A2 口径）
    Then rc≠0 且输出含 FAIL（证明它**实际回放了** gate，而非永远 SKIP 显示绿）。
    """
    repo, _task = _setup_failing_gate_repo(git_repo)
    base = git_repo.git("rev-parse", "HEAD~1").stdout.strip()
    result = _run_ci_verify(
        agate_scripts, python_exe, run_cli, "--base", base, cwd=repo,
        env={"AGATE_ROOT": str(agate_root)},
    )
    assert result.returncode != 0, (
        "BDD-16（无假绿）：gate 判定失败时 ci-verify 须 rc≠0；"
        f"当前 rc={result.returncode}（假绿）\n{result.output[:400]}"
    )
    assert "FAIL" in result.output, (
        f"BDD-16：gate 失败须以 FAIL 明确报出；实际输出 {result.output[:300]!r}"
    )


def test_bdd_16_ci_verify_skip_declared_with_reason(
    git_repo, agate_scripts, python_exe, run_cli
):
    """BDD-16（跳过可区分）：无适用场景时**显式声明「跳过 + 原因」**，不静默显示绿。

    Given 一个**有提交、无任务目录**的仓库（真跑到「回放范围未改动任务目录」这条 SKIP 路径——
    此前该用例在空仓库上跑，实际走的是「无法解析 HEAD」分支，属碰巧通过，评审 A4 指出）
    When 以 `--base HEAD` 运行 `agate-ci-verify`（`--base` 必填，见 TAG0050 评审 M-1 配套）
    Then 输出显式含「跳过」标识**且**给出原因（不再是「永远 SKIP 却显示绿」的无声绿）。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()
    result = _run_ci_verify(
        agate_scripts, python_exe, run_cli, "--base", base, cwd=repo
    )
    assert re.search(r"SKIP|跳过", result.output), (
        "BDD-16：无适用场景须**显式**声明「跳过」（不再静默假绿）；"
        f"实际输出 {result.output[:300]!r}"
    )
    assert re.search(
        r"原因|reason|未改动|无|not|absent|non-agate", result.output, re.IGNORECASE
    ), (
        "BDD-16：跳过须附**原因**（「跳过」与「通过」可区分）；"
        f"实际输出 {result.output[:300]!r}"
    )


def test_bdd_16_ci_verify_source_reruns_gate(agate_scripts):
    """BDD-16（实际回放）：ci-verify 源码确实回放本地 hook（pre-commit-gate.py）。

    Given agate-ci-verify.py
    When 检查其判定路径
    Then 它引用 `pre-commit-gate.py`（= 实际逐提交回放本地 hook，TAG0050 A2），
         而非无条件恒绿。
    """
    script = agate_scripts / _CI_VERIFY_SCRIPT
    assert script.is_file(), (
        f"BDD-16：{_CI_VERIFY_SCRIPT} 不存在（批 5 未实现）——重跑 gate 路径无从检查"
    )
    src = script.read_text(encoding="utf-8")
    assert re.search(r"pre-commit-gate\.py", src), (
        "BDD-16：ci-verify 须实际回放本地 hook（引用 pre-commit-gate.py），"
        "而非「永远 SKIP 却显示绿」"
    )


def test_bdd_16_ci_verify_workflow_invokes_new_script(agate_root):
    """BDD-16（M15）：CI workflow 的 gate-backstop job 改调 `agate-ci-verify.py`。

    Given `.github/workflows/protocol-tests.yml`
    When 检查 gate-backstop job 的调用
    Then 它调用 `agate-ci-verify.py`，**不再**调用退役的 `ci-gate-backstop.py`。

    现行为：workflow 仍调 `ci-gate-backstop.py` ⇒ 红灯（引用未同步）。
    """
    workflow = agate_root.parent / _WORKFLOW
    assert workflow.is_file(), f"BDD-16：找不到 workflow {_WORKFLOW}"
    text = workflow.read_text(encoding="utf-8")
    assert _CI_VERIFY_SCRIPT in text, (
        f"BDD-16（M15）：workflow 须调用新脚本 {_CI_VERIFY_SCRIPT}（替换 ci-gate-backstop）"
    )
    assert _RETIRED_BACKSTOP not in text, (
        f"BDD-16（M15）：workflow 不应再调用退役的 {_RETIRED_BACKSTOP}"
        "（引用须同步更新）"
    )


def test_m1_pr_job_runs_both_invocations(agate_root):
    """TAG0050 评审 M-1 配套：PR 事件下 gate-backstop 须**同时**跑两条口径。

    Given `.github/workflows/protocol-tests.yml`
    When 检查 gate-backstop job
    Then PR 分支同时给 `--base`（PR 口径）与 `--push --base`（push 口径）——脚本里这是两条
         独立的范围/协议根解析路径，只跑一条有路径特异性盲区（TAG0050 P8 事故根因）。
    """
    workflow = agate_root.parent / _WORKFLOW
    assert workflow.is_file(), f"BDD-16：找不到 workflow {_WORKFLOW}"
    text = workflow.read_text(encoding="utf-8")
    assert re.search(r'args="--base \$PR_BASE"', text), (
        "PR 事件须跑 `--base $PR_BASE`（PR 口径）"
    )
    assert re.search(r'extra_args="--push --base \$PR_BASE"', text), (
        "PR 事件须**同时**跑 `--push --base $PR_BASE`（push 口径）——"
        "否则「PR 绿 ⇔ 合并后 main 绿」不成立（TAG0050 P8 事故根因）"
    )


def test_bdd_16_ci_verify_protocol_refs_synced(agate_root):
    """BDD-16（CHECK10-scriptref 方向）：退役后协议文档引用须同步更新。

    Given 退役 `ci-gate-backstop.py` 的批 5
    When 检查 CHECK10-scriptref 扫描面（非豁免协议文件）
    Then 这些文件**不再**引用已退役的 `ci-gate-backstop.py`（否则 CHECK10 新增 ERROR）。

    现行为：协议文档仍引用 `ci-gate-backstop.py` ⇒ 红灯（引用未同步）。
    """
    offenders = []
    for rel in _PROTOCOL_REFS_TO_SYNC:
        path = agate_root.parent / rel
        if path.is_file() and _RETIRED_BACKSTOP_NAME in path.read_text(encoding="utf-8"):
            offenders.append(rel)
    assert not offenders, (
        "BDD-16（CHECK10-scriptref）：退役 ci-gate-backstop.py 后下列协议文件仍引用它，"
        f"须同步更新引用：{offenders}"
    )


# ── 回归：push-to-main 时协议根须取回放基准 base，而非 HEAD 新协议 ────────────
#
# 合并后 main CI 真缺陷（TAG0050 P8-ci-fix3）：`_resolve_protocol` 曾用
# `merge-base HEAD origin/<默认分支>` 选协议根——push 到 main 时 HEAD 就是
# origin/main，merge-base = HEAD 自己 ⇒ 用刚合并的新协议回放历史提交 ⇒ 卡片
# hash 按旧协议注入、回放误报 FAIL。修法：协议根改由主流程算好的**回放基准 base**
# 推导（协议仓库中 `merge-base(base, HEAD)` 处的 agate/）。


def _load_ci_verify_module(agate_scripts):
    """以文件路径加载 `agate-ci-verify.py` 模块（文件名含 `-`，不能普通 import）。"""
    path = agate_scripts / _CI_VERIFY_SCRIPT
    spec = importlib.util.spec_from_file_location("agate_ci_verify_under_test", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_push_to_main_protocol_root_uses_base_not_head(git_repo, agate_scripts):
    """push-to-main：`_resolve_protocol` 须取 `base` 处的协议，而非 HEAD 的新协议。

    Given 一个**仓库本体含协议**的仓库：base 提交处协议为旧版，HEAD 提交处协议为新版；
          且 `origin/main` 指向 HEAD（模拟 push 到 main：`merge-base(HEAD, origin/main)` = HEAD）
    When 以 `base` 为回放基准解析协议根（无 AGATE_ROOT，走「仓库本体」分支）
    Then 协议根取 `base` 处的**旧**协议，note 写明回放基准 `base`——而非 HEAD 的新协议。

    判别力：改动前用 `merge-base HEAD origin/main` = HEAD ⇒ 会返回 HEAD 的新协议 ⇒ 断言转红。
    """
    repo = git_repo.path
    proto = repo / "agate" / "scripts"
    proto.mkdir(parents=True)
    gate = proto / "pre-commit-gate.py"
    gate.write_text("# OLD protocol\n", encoding="utf-8")
    git_repo.commit("old protocol")
    base = git_repo.git("rev-parse", "HEAD").stdout.strip()

    gate.write_text("# NEW protocol\n", encoding="utf-8")
    git_repo.commit("new protocol")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()
    # 模拟 push 到 main：origin/main == HEAD ⇒ merge-base(HEAD, origin/main) == HEAD
    git_repo.git("update-ref", "refs/remotes/origin/main", head)
    git_repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    mod = _load_ci_verify_module(agate_scripts)
    root, cleanup, note = mod._resolve_protocol(str(repo), "", base)
    try:
        assert root is not None, "push-to-main：须解析出协议根（仓库本体分支）"
        content = Path(root, "scripts", "pre-commit-gate.py").read_text(encoding="utf-8")
        assert content == "# OLD protocol\n", (
            "push-to-main：协议根须取 base 处协议（旧），而非 HEAD 新协议——"
            f"实际取到 {content!r}"
        )
        assert base[:8] in note, (
            f"push-to-main：note 须写明回放基准 base（{base[:8]}）；实际 {note!r}"
        )
    finally:
        if cleanup:
            proto_repo, wt = cleanup
            mod._git(["worktree", "remove", "--force", wt], proto_repo)
            shutil.rmtree(wt, ignore_errors=True)


def test_resolve_protocol_falls_back_when_base_absent(agate_scripts, git_repo):
    """回归：`base` 不在协议仓库（测试夹具合成仓库）时**回退当前 HEAD 的协议**且 note 不静默。

    与上一条互补：真实 CI 的 `base` 在协议仓库内（须取 base 处协议）；测试夹具的 `base`
    是另一个仓库的 SHA（不在协议仓库）⇒ 回退当前 HEAD 的协议，并在 note 写明回退原因。
    """
    repo = git_repo.path
    proto = repo / "agate" / "scripts"
    proto.mkdir(parents=True)
    (proto / "pre-commit-gate.py").write_text("# CURRENT protocol\n", encoding="utf-8")
    git_repo.commit("current protocol")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()

    mod = _load_ci_verify_module(agate_scripts)
    bogus = "f" * 40  # 不在本仓库的 SHA（合成夹具场景）
    root, cleanup, note = mod._resolve_protocol(str(repo), "", bogus)
    try:
        assert root is not None, "base 缺失时须回退当前 HEAD 的协议根（非 None）"
        content = Path(root, "scripts", "pre-commit-gate.py").read_text(encoding="utf-8")
        assert content == "# CURRENT protocol\n", "回退须用当前 HEAD 的协议"
        assert bogus[:8] in note, f"回退须在 note 写明原因（含基准 {bogus[:8]}）；实际 {note!r}"
    finally:
        if cleanup:
            proto_repo, wt = cleanup
            mod._git(["worktree", "remove", "--force", wt], proto_repo)
            shutil.rmtree(wt, ignore_errors=True)
    assert head, "sanity：HEAD 可解析"


def test_m1_base_required_no_inference(git_repo, agate_scripts, python_exe, run_cli):
    """TAG0050 评审 M-1 配套：缺 `--base` **不得静默推断**，须 FAIL。

    Given 一个**有提交**的仓库（HEAD 可解析——与空仓库的「无法解析 HEAD」SKIP 区分）
    When 不传 `--base` 运行 agate-ci-verify
    Then rc≠0 且输出指明 `--base` 必填（原行为：静默推断 `merge-base HEAD origin/<默认分支>`，
         push 到默认分支时该值 = HEAD 自己 ⇒ 用新协议回放历史提交致误报 FAIL）。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    result = _run_ci_verify(agate_scripts, python_exe, run_cli, cwd=repo)
    assert result.returncode != 0, (
        f"缺 --base 须 FAIL（不得推断），实际 rc={result.returncode}\n{result.output[:300]}"
    )
    assert "--base" in result.output, (
        f"失败原因须指明 --base 必填；实际输出 {result.output[:300]!r}"
    )


def test_rm_ag0112_push_before_unresolvable_falls_back(
    git_repo, agate_scripts, python_exe, run_cli
):
    """RM-AG0112：push 的 `before` **不可解析**（对象缺失——rebase / 强推后旧 head 不再挂在
    任何 ref，而 CI 的 fetch refspec 只取 `refs/heads/*` + tags）时不得判 FAIL（**假红**）。

    2026-10-09 实测：PR #422 rebase 后强推 ⇒ CI clone 里 `before` 对象不存在 ⇒
    `FAIL: rev-list 7c419e93..ac93f22c 失败`（job 113733056770）；该 check 已升 required
    ⇒ PR 被 BLOCKED。

    ⚠️ 评审 r1 澄清：`rev-list A..B` **不要求** A 是祖先（A 存在即成功）——故失败源是
    **不可解析**，不是「非祖先」。本用例用不可解析 sha 复现真缺陷。

    Given 一个有 `origin/main` 的仓库（默认分支可解析）
    When 以 `--push --base <不可解析 sha>` 运行
    Then 不得 FAIL；须**显式** NOTE 说明回退 `merge-base(HEAD, origin/main)`。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()
    git_repo.git("update-ref", "refs/remotes/origin/main", head)
    git_repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    bogus = "f" * 40  # 不可解析（对象缺失）——等价于 rebase 后旧 head 在 clone 中不存在
    result = _run_ci_verify(
        agate_scripts, python_exe, run_cli, "--push", "--base", bogus, cwd=repo
    )
    assert result.returncode == 0, (
        f"before 不可解析时不得 FAIL（假红）；rc={result.returncode}\n{result.output[:400]}"
    )
    assert "不可解析" in result.output, (
        f"回退须**显式** NOTE（不静默）；实际输出 {result.output[:400]!r}"
    )


def test_rm_ag0112_push_before_non_ancestor_keeps_diff_semantics(
    git_repo, agate_scripts, python_exe, run_cli
):
    """RM-AG0112 附：`before` 可解析但**非**祖先（历史改写、旧对象仍在）——`rev-list`
    本身能成功（差集语义），**不回退**，但保留显式 NOTE 便于诊断。"""
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    (repo / "a.txt").write_text("a\n", encoding="utf-8")
    git_repo.stage("a.txt")
    git_repo.commit("c1")
    stale = git_repo.git("rev-parse", "HEAD").stdout.strip()
    git_repo.git("reset", "--hard", "HEAD~1")
    (repo / "b.txt").write_text("b\n", encoding="utf-8")
    git_repo.stage("b.txt")
    git_repo.commit("c2")
    head = git_repo.git("rev-parse", "HEAD").stdout.strip()
    git_repo.git("update-ref", "refs/remotes/origin/main", head)
    git_repo.git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")

    result = _run_ci_verify(
        agate_scripts, python_exe, run_cli, "--push", "--base", stale, cwd=repo
    )
    assert result.returncode == 0, f"不得 FAIL；rc={result.returncode}\n{result.output[:400]}"
    assert "不是 HEAD 的祖先" in result.output, (
        f"须保留显式 NOTE（差集语义、不回退）；实际输出 {result.output[:400]!r}"
    )


def test_rm_ag0112_push_before_unresolvable_no_default_branch_fails(
    git_repo, agate_scripts, python_exe, run_cli
):
    """RM-AG0112：`before` 不可解析**且**无法解析 `merge-base HEAD origin/<默认分支>` 时，
    须 FAIL（信息清晰）——不得静默放行（回退无从谈起）。

    Given 一个**无 origin** 的仓库（默认分支不可解析）
    When 以 `--push --base <不可解析 sha>` 运行
    Then rc≠0 且输出含「不可解析」与「无法确定回放范围」。
    """
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    bogus = "f" * 40
    result = _run_ci_verify(
        agate_scripts, python_exe, run_cli, "--push", "--base", bogus, cwd=repo
    )
    assert result.returncode != 0, (
        f"不可解析且无默认分支须 FAIL；rc={result.returncode}\n{result.output[:400]}"
    )
    assert "不可解析" in result.output and "无法确定回放范围" in result.output, (
        f"FAIL 信息须清晰；实际输出 {result.output[:400]!r}"
    )
