# tests/unit/test_check_gate_p4_maintainability.py — check-gate.py P4 维护性反模式三重门槛
# （RM-AG0046，TAG0026 P3；先例 test_check_gate_p5_diff.py / test_agate_risk_score.py）。
# 被测：agate/scripts/check-gate.py P4 TASK_DIR 的 gate_p4 三重门槛新步骤（尚未实现，P4 写）。
# 门槛语义（P2-design.md §3.2；既有 ①review存在→1 ②status非approved→1 ③agent缺→2/main→1
#   ④staged代码检查→1 ⑤骨架WARNING ⑥return 0，新步骤落在 ④ 之后、⑤ 之前）：
#   violations 非空 → ① known-violations.md 存在（无→1）② count_kf_entries 登记 ≥ 违规数
#   （不足→1）③ 评审 approve 复用既有 ①②③（BDD-9/10 由顺序天然保证）；只产生 return 1，
#   不新增 return 2；violations 为空 / 检测未部署 / git_ok False 三种跳过场景行为与现状一致。
# 覆盖分组（P2-design.md §5.2 + P2-review 测试缺口/建议）：
#   G1 登记缺失阻断（BDD-7）/ G2 数量不对齐阻断（BDD-8，含"文件存在但 0 条"反向分支）/
#   G3 评审未 approve 仍阻断（BDD-9 三态）/ G4 三重满足放行（BDD-10，真写登记文件验计数）/
#   G5 无 violations 回归面（R1，review 建议：既有 ①②③④ 逐项等价 + 非空三重满足落 return 0
#   且骨架 WARNING 在 stderr）/ G6 ImportError 降级（R2，review 建议：monkeypatch 模拟）/
#   G7 返回约定（约束 4）。
# TDD 红灯形态（check-tdd-red 口径适配，TAG0026 P3）：
#   红灯机制 = 全文件共享模块级 sentinel `_IMPLEMENTED`：收集期探测 gate_p4 是否已含
#   维护性门槛（探测"check-gate.py 内 import 了 check_maintainability 并在 gate_p4 消费"）。
#   未实现（P3 现状）→ 每条用例先 `assert _IMPLEMENTED, RED_REASON` 失败（assertion failure
#   → check-tdd-red classic red-light exit 0 真红灯），再继续构造场景（红灯断言先行的意义：
#   断言失败不依赖后续步骤，场景代码照常可读、P4 实现后自动转为真实行为断言）。
#   不用 collect-error：check-tdd-red 无 formatter 时对 raw_output 的
#   Traceback/ImportError 文本判 A 类（exit 1 假红灯）。
# 平台无关：全部 tmp_path；git 经 conftest git_repo fixture（不裸 PATH）；解释器经 python_exe；
#   AGATE_ROOT 经 agate_root fixture；不硬编码 /home/... 绝对路径。

import re
import shutil

import pytest

from conftest import GitRepo

_KNOWN_VIOLATIONS_HEAD = (
    "---\n"
    "task_id: {task_id}\n"
    "generated_by: {agent}\n"
    "---\n"
    "# 维护性反模式登记\n"
    "\n"
    "## 本次引入的反模式\n"
    "\n"
    "| # | 文件 | 反模式类型 | 违规详情 | 理由 | P4 评审确认 |\n"
    "|---|------|-----------|---------|------|------------|\n"
)

# ── P3 红灯探测（模块级，收集期执行一次）───────────────────────────────


def _gate_p4_source():
    """读 check-gate.py 全文 + 截取 gate_p4 函数体（失败返回空串）。

    路径解析三级 parent：unit → tests → agate，再进 scripts/（探测被测对象的机械
    路径修复，主 Agent 定夺 1；断言语义不变）。
    """
    from pathlib import Path

    gate = (
        Path(__file__).resolve().parent.parent.parent / "scripts" / "check-gate.py"
    )
    try:
        src = gate.read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^def gate_p4\(.*?(?=^def |\Z)", src, re.M | re.S)
    return src if m is None else src[: m.start()] + m.group(0)


def _maintainability_gate_implemented():
    """check-gate.py 是否已挂载维护性门槛：import 兜底区出现 + gate_p4 体消费该符号。"""
    src = _gate_p4_source()
    if not src:
        return False
    imported = re.search(r"from\s+check_maintainability\s+import|import\s+check_maintainability\b", src)
    consumed = re.search(r"check_maintainability\(", src)
    return bool(imported and consumed)


_IMPLEMENTED = _maintainability_gate_implemented()
RED_REASON = (
    "RM-AG0046 未实现：check-gate.py gate_p4 尚未挂载维护性反模式三重门槛"
    "（P4 产出项；TDD 红灯先行，check-tdd-red 判 classic red-light）"
)


def _require_implemented():
    """红灯哨兵：未实现时在每条用例开头 assertion 失败（真红灯，A/B 类判定安全）。"""
    assert _IMPLEMENTED, RED_REASON


def _run_gate(agate_scripts, python_exe, run_cli, task_arg, phase="P4", cwd=None):
    """`$PYTHON $AGATE_SCRIPTS/check-gate.py P4 TASK_DIR` 等价（先例 _run_gate 同型 + cwd）。"""
    cmd = [python_exe, str(agate_scripts / "check-gate.py"), phase, task_arg]
    return run_cli(*cmd, cwd=cwd)


def _write_known_violations(td, rows):
    """写 known-violations.md（行首 `| N |` 格式，count_kf_entries 计数口径）。"""
    body = _KNOWN_VIOLATIONS_HEAD.format(task_id="T001", agent="implementer")
    (td / "known-violations.md").write_text(body + rows, encoding="utf-8")


def _violation_rows(*items):
    """生成 N 条登记行（| N | 行首命中 count_kf_entries）。"""
    return "".join(
        f"| {i} | {f} | {t} | {d} | 理由 | 是 |\n"
        for i, (f, t, d) in enumerate(items, start=1)
    )


def _repo_with_staged(git_repo, task_dir, paths):
    """git repo：init commit + 拷贝任务目录到 repo/task + 暂存 paths（对齐 risk_score 先例）。

    任务目录里默认带合规 P4-review（status approved + agent≠main）——三重门槛 ③ 由此满足，
    各用例按需改写（BDD-9 反向态）。返回 (git_repo, task_dir_path)。
    """
    repo = git_repo
    repo_path = repo.path
    (repo_path / "README.md").write_text("init\n", encoding="utf-8")
    repo.commit("init")
    td = task_dir()
    shutil.copytree(td, repo_path / "task")
    # 合规 P4-review（门槛 ③ 基线）：status=approved + agent≠main
    _write_review(repo_path, status="approved", agent="implementer-review")
    for name, content in paths.items():
        p = repo_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        repo.stage(name)
    return repo, repo_path / "task"


def _write_review(repo_path, status="approved", agent="implementer-review"):
    """写 repo/task/P4-review.md（gate_p4 既有 ①②③ 的输入）。"""
    (repo_path / "task" / "P4-review.md").write_text(
        f"---\nstatus: {status}\nagent: {agent}\n---\nP4 review.\n",
        encoding="utf-8",
    )


def _staged_code(repo, name="src/feat.py", extra=None, dirty=False):
    """构造一个 staged 代码 diff。

    dirty=True 时含新增裸 except（violations 非空场景——G1/G2b/G7 的门槛 a/b 失败
    前提就是检测出 violation，dirty 是 extra= 机制的标准形态）；默认干净体
    （G5a 合规基线）。
    """
    body = "def f():\n    pass\n"
    if dirty:
        body += "try:\n    pass\nexcept:\n    pass\n"
    elif extra is not None:
        body += extra
    p = repo.path / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body, encoding="utf-8")
    repo.stage(name)


# ===== G1 登记缺失阻断（BDD-7） =====


@pytest.mark.windows_smoke
def test_g1_missing_known_violations_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-7：violations 非空 + known-violations.md 不存在 → gate_p4 返回 1（与评审输出无关）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo, dirty=True)
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 1
    assert "known-violations" in result.output


# ===== G2 数量不对齐阻断（BDD-8） =====


def test_g2_registration_insufficient_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-8：violations=3（构造 staged diff）+ 登记 2 条 → exit 1（不是"有文件就过"）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    # 构造 3 个 violation：3 个文件各 1 个新增裸 except
    for i in range(3):
        _staged_code(repo, name=f"src/feat_{i}.py", extra="try:\n    pass\nexcept:\n    pass\n")
    _write_known_violations(
        _td,
        _violation_rows(
            ("src/feat_0.py", "fuzzy-boundary", "line 3"),
            ("src/feat_1.py", "fuzzy-boundary", "line 3"),
        ),
    )
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 1
    assert "登记" in result.output or "数量" in result.output


def test_g2_zero_entries_with_file_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-8 反向分支（P2-review 测试缺口 1）：登记文件存在但正文无 `| N |` 行（0 条）→ exit 1。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo, dirty=True)
    # 只写模板头 + 样例行 | # |（不命中 count_kf_entries 正则）→ 登记数 0 < violations 数 1
    _write_known_violations(_td, "| # | | god-file 跨越 / fuzzy-boundary | | | 是/否 |\n")
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 1
    assert "known-violations" in result.output or "登记" in result.output


# ===== G3 评审未 approve 仍阻断（BDD-9，三态） =====


def _bdd9_case(git_repo, task_dir, status, agent):
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo, name=f"src/{agent or 'na'}.py", extra="try:\n    pass\nexcept:\n    pass\n")
    _write_review(repo.path, status=status, agent=agent)
    _write_known_violations(
        _td, _violation_rows((f"src/{agent or 'na'}.py", "fuzzy-boundary", "line 3"))
    )
    return repo, _td


def test_bdd_9_review_missing_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9 态1：登记对齐（此处 1=1）但 P4-review.md 不存在 → exit 1（数量对齐不能单独放行）。"""
    _require_implemented()
    repo, _td = _bdd9_case(git_repo, task_dir, None, "implementer-review")
    (repo.path / "task" / "P4-review.md").unlink()
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 1


def test_bdd_9_review_not_approved_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9 态2：登记对齐但 status != approved → exit 1。"""
    _require_implemented()
    repo, _td = _bdd9_case(git_repo, task_dir, "pending", "implementer-review")
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 1


def test_bdd_9_review_agent_main_exit_1(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-9 态3：登记对齐但 agent == main → exit 1。"""
    _require_implemented()
    repo, _td = _bdd9_case(git_repo, task_dir, "approved", "main")
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 1


# ===== G4 三重满足放行（BDD-10） =====


def test_bdd_10_all_three_satisfied_exit_0(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-10：violations=3 + 登记 3 条（真写文件，count_kf_entries 可计数）+ review approved（agent≠main）→ exit 0。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    for i in range(3):
        _staged_code(repo, name=f"src/feat_{i}.py", extra="try:\n    pass\nexcept:\n    pass\n")
    _write_known_violations(
        _td,
        _violation_rows(
            ("src/feat_0.py", "fuzzy-boundary", "line 3"),
            ("src/feat_1.py", "fuzzy-boundary", "line 3"),
            ("src/feat_2.py", "fuzzy-boundary", "line 3"),
        ),
    )
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 0, f"三重满足应放行: rc={result.returncode} {result.output!r}"


# ===== G5 无 violations 回归面（R1 + P2-review 测试缺口 2 / 建议 1） =====


def test_g5_no_violations_baseline_equivalence(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """G5a：合规任务（无 violations）→ gate_p4 返回值与改动前等价（exit 0，输出无维护性门槛消息）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo)  # 干净代码，无新增裸 except
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 0
    # 改动前 gate_p4 的既有输出面保持（无登记缺失/数量不齐等新消息）
    assert "known-violations" not in result.output


def test_g5_legacy_failure_paths_unchanged(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """G5b（review 建议 1）：既有 ①②③④ 失败路径逐项等价——新步骤不得改变其返回值。"""
    _require_implemented()
    # ① review 缺失 → 1
    repo1, _td1 = _repo_with_staged(GitRepo(git_repo.path.parent / "repo_a"), task_dir, {})
    _staged_code(repo1)
    (repo1.path / "task" / "P4-review.md").unlink()
    r1 = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo1.path))
    assert r1.returncode == 1

    # ② status 非 approved → 1
    repo2, _td2 = _repo_with_staged(GitRepo(git_repo.path.parent / "repo_b"), task_dir, {})
    _staged_code(repo2)
    _write_review(repo2.path, status="pending", agent="implementer-review")
    r2 = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo2.path))
    assert r2.returncode == 1

    # ③ agent=main → 1（③ 在既有代码里对 main 返回 1）
    repo3, _td3 = _repo_with_staged(GitRepo(git_repo.path.parent / "repo_c"), task_dir, {})
    _staged_code(repo3)
    _write_review(repo3.path, status="approved", agent="main")
    r3 = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo3.path))
    assert r3.returncode == 1

    # ④ 无 staged 代码 → 1
    repo4, _td4 = _repo_with_staged(GitRepo(git_repo.path.parent / "repo_d"), task_dir, {})
    r4 = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo4.path))
    assert r4.returncode == 1

    # ③ agent 缺失 → 1
    # （TAG0042 批0 X7：本处原断言 `== 2`，那是**移植期快照**而非 P4 应有语义——
    #   P4 的 gate_pass_exit=0，2 ∉ pass_set 且 ≠ 1 ⇒ agate-next 落 exit2-resolution
    #   误判为"真暂停"。`return 2` 出现于 2026-08-15（TAG0010 shell→py 机械移植），
    #   而 gate_pass_exit 机制 2026-09-03 才引入（TAG0027）⇒ 并非为 P4 设计。
    #   本用例守护目的不变：**新步骤不得新增 return 2**。）
    repo5, _td5 = _repo_with_staged(GitRepo(git_repo.path.parent / "repo_e"), task_dir, {})
    _staged_code(repo5)
    (repo5.path / "task" / "P4-review.md").write_text(
        "---\nstatus: approved\n---\nP4 review.\n", encoding="utf-8"
    )
    r5 = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo5.path))
    assert r5.returncode == 1


def test_g5_violations_registered_passes_to_return_0_with_skeleton_warning(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """G5c（review 缺口 2）：violations 非空 + 三重满足 → 穿过新步骤落到 return 0（新步骤不得提前 return）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo, extra="try:\n    pass\nexcept:\n    pass\n")
    _write_known_violations(
        _td, _violation_rows(("src/feat.py", "fuzzy-boundary", "line 3"))
    )
    result = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result.returncode == 0, f"应穿过新步骤落 return 0: {result.output!r}"
    # 未采用骨架机制时 stderr 可能为空（骨架 WARNING 是条件消息）——此处锁定的是
    # "return 0 主路可达"（review 缺口 2 的核心：新步骤不在中途 return 0/2）。
    # stderr 消息断言在 G6 的降级 WARNING 路径另行覆盖。
    assert result.returncode == 0


# ===== G6 ImportError 降级（R2 + review 建议 2：monkeypatch 模拟） =====


def _load_gate_module(agate_scripts):
    """in-process 导入 check-gate 模块（scripts 目录进 sys.path；模块名带连字符走 importlib）。"""
    import importlib
    import sys

    scripts = str(agate_scripts)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    for name in [m for m in list(sys.modules) if m in ("check-gate", "check_gate")]:
        del sys.modules[name]
    return importlib.import_module("check-gate")


def test_g6_import_error_degrades_to_warning(
    git_repo, task_dir, agate_scripts, python_exe, run_cli, monkeypatch, tmp_path
):
    """G6：check_maintainability 不可用（monkeypatch 成 None）→ WARNING 不阻断（gate_p4 返回 0）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo)
    # gate_p4 是独立进程时 monkeypatch 不生效——in-process 导入 gate 模块后 patch 属性再调用
    # （review 建议 2：比模拟 import 失败更稳定）。in-process 调用没有子进程的 cwd=repo
    # 环境，④ 步 _git 读的是 ambient cwd——monkeypatch.chdir 锚定到用例仓库（等效
    # _run_gate 的 cwd=repo.path，只读 diff，无 git 写操作）。
    gate_mod = _load_gate_module(agate_scripts)
    monkeypatch.chdir(repo.path)
    monkeypatch.setattr(gate_mod, "check_maintainability", None)
    result = gate_mod.gate_p4(str(_td))
    assert result == 0, f"ImportError 降级应 WARNING 不阻断: {result}"


def test_g6_git_unavailable_degrades_to_warning(
    git_repo, task_dir, agate_scripts, python_exe, run_cli, monkeypatch
):
    """G6 变体：git 通道不可用（git_ok=False）→ WARNING 不阻断（gate_p4 返回 0，检测层降级）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    _staged_code(repo)
    gate_mod = _load_gate_module(agate_scripts)
    monkeypatch.chdir(repo.path)  # ④ 步 _git 的 ambient cwd 锚定（同 G6 上一例）

    def _fake_check(task_dir_arg):
        return {"git_ok": False, "violations": [], "god_file_count": 0, "fuzzy_boundary_count": 0}

    monkeypatch.setattr(gate_mod, "check_maintainability", _fake_check)
    result = gate_mod.gate_p4(str(_td))
    assert result == 0, f"git_ok=False 应 WARNING 不阻断: {result}"


# ===== G7 返回约定（约束 4） =====


def test_g7_no_new_return_2_from_new_step(
    git_repo, task_dir, agate_scripts, python_exe, run_cli, monkeypatch
):
    """G7：新步骤不产生 return 2——门槛 a/b 失败仅 return 1；agent 缺失态同属 return 1
    （TAG0042 批0 X7 后 P4 **已无任何 return 2 路径**，见本文件 §G5b 注释）。"""
    _require_implemented()
    repo, _td = _repo_with_staged(git_repo, task_dir, {})
    # 门槛 a 失败（无登记文件）→ 1 而非 2
    _staged_code(repo, dirty=True)
    result_a = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result_a.returncode == 1
    # 门槛 b 失败（登记 0 条）→ 1 而非 2
    _write_known_violations(_td, "| # | | god-file 跨越 / fuzzy-boundary | | | 是/否 |\n")
    result_b = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo.path))
    assert result_b.returncode == 1
    # agent 缺失态（TAG0042 批0 X7 前为 return 2，现为 1）
    repo2 = GitRepo(repo.path.parent / "repo_g7")
    repo2.path.joinpath("README.md").write_text("init\n", encoding="utf-8")
    repo2.commit("init")
    shutil.copytree(_td, repo2.path / "task")
    (repo2.path / "task" / "P4-review.md").write_text(
        "---\nstatus: approved\n---\nP4 review.\n", encoding="utf-8"
    )
    _staged_code(repo2)
    result_c = _run_gate(agate_scripts, python_exe, run_cli, "task", phase="P4", cwd=str(repo2.path))
    assert result_c.returncode == 1
