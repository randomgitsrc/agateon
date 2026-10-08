# agate/tests/unit/test_tag0050_declarations.py
# TAG0050 批 E（成对声明）红灯测试。
#
# 映射：BDD-61..BDD-66（P1-requirements.md §4；设计 §6、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

_MD_SET = "agate-md-field-set.py"


@pytest.mark.windows_smoke
def test_bdd_61_f2_blocker_count_not_covering_prose(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-61：F2 转红（P7 汇总值盖不住 BLOCKER）。"""
    d = h.init_task_via_conftest(tmp_path)
    p7 = d / "P7-consistency.md"
    p7.write_text(
        "---\nagent: test\nblocker_count: 0\n---\n\n- [BLOCKER] 未解决\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-61：计数为系统字段，不被汇总值盖住，实际 rc={r.returncode}"


def test_bdd_62_cross_file_declaration_aggregation(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-62：P2-review 与 P4 分文件中的声明都被聚合。"""
    d = h.init_task_via_conftest(tmp_path)
    # 清掉 init_task 的 P4 散文缺口，隔离本用例的判别面（跨文件结构化聚合）。
    (d / "P4-implementation.md").write_text("---\nagent: impl\n---\nbody\n", encoding="utf-8")
    (d / "P2-review.md").write_text(
        "---\nagent: reviewer\nneed_confirm: []\n---\nreview\n", encoding="utf-8"
    )
    (d / "P4-implementation-batch1.md").write_text(
        "---\nagent: impl\ndesign_gaps:\n  - {id: DG1, text: x}\n---\nbody\n", encoding="utf-8"
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-62：跨文件聚合须覆盖 P4 分文件声明，实际 rc={r.returncode}"
    # 判别性：确实聚合到 P4-implementation-batch1.md 的 DG1（被报为悬空），而非无关失败。
    assert "DG1" in r.output or "悬空" in r.output, r.output


def test_bdd_63_parallel_ids_no_collision(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-63：并行写入不撞号（ID = <相对路径去 .md>:<前缀><n>）。"""
    d = h.init_task_via_conftest(tmp_path)
    f = d / "P4-implementation-batch1.md"
    f.write_text("---\nagent: impl\n---\nbody\n", encoding="utf-8")
    r = run_cli(
        python_exe,
        str(agate_scripts / _MD_SET),
        "append",
        "design_gaps",
        "text=x",
        env={"FILE": str(f)},
    )
    assert r.returncode == 0, f"BDD-63：append 自动编号须可用，实际 rc={r.returncode}"
    assert "P4-implementation-batch1" in f.read_text(encoding="utf-8"), (
        "BDD-63：ID 须带相对路径前缀，每文件独立编号"
    )


def test_bdd_64_set_mismatch_or_dangling_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-64：集合不相等或悬空 id 判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-64：悬空 id/集合不等须 ERROR，实际 rc={r.returncode}"
    assert "散文" in r.output or "design_gap_reviews" in r.output, r.output


def test_bdd_65_resolved_missing_evidence_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-65：resolved 缺证据判 ERROR（构造 findings 中 resolved 缺 resolution/evidence）。"""
    d = h.init_task_via_conftest(tmp_path)
    # P7 声明一条 resolved 但缺 resolution/evidence 的 finding。
    (d / "P7-consistency.md").write_text(
        "---\nagent: test\nfindings:\n"
        "  - {id: F1, severity: note, text: x, status: resolved}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode != 0, f"BDD-65：resolved 缺 resolution/evidence 须 ERROR，实际 rc={r.returncode}"
    assert "resolved" in r.output and "evidence" in r.output, r.output


def test_bdd_66_followup_debt_backref_required(agate_scripts):
    """BDD-66：followup:DEBT<n> 中 DEBT 不存在或无回指判 ERROR。"""
    src = (agate_scripts / "agate-debt-check.py").read_text(encoding="utf-8")
    assert "source_ref" in src, (
        "BDD-66：tech-debt 须新增 source_ref 字段并校验双向回指（<task_id>:<DG id>）"
    )


def test_gap8_review_file_requires_frontmatter(tmp_path, agate_scripts, python_exe, run_cli):
    """GAP-8：`declaration_files` 扩展到 `*-review.md`——非 legacy 任务缺 frontmatter 判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    (d / "P2-review.md").write_text("no frontmatter here\n", encoding="utf-8")
    r = run_cli(
        python_exe, str(agate_scripts / "check-frontmatter.py"), str(d / "P2-review.md")
    )
    assert r.returncode == 1, f"GAP-8：P2-review.md 缺 frontmatter 须 ERROR，rc={r.returncode}"


def test_gap8_p4_implementation_glob_frontmatter(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """GAP-8：`P4-implementation-*.md` 命中声明 glob——缺 frontmatter 判 ERROR。"""
    d = h.init_task_via_conftest(tmp_path)
    f = d / "P4-implementation-batch1.md"
    f.write_text("no frontmatter\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(f))
    assert r.returncode == 1, f"GAP-8：P4-implementation-*.md 缺 frontmatter 须 ERROR，rc={r.returncode}"


# ── C8 整改（第 2 轮）新增用例：MINOR-4 / cso F-2 / cso F-4 ─────────────────────


def _p4_with_reviews(d, review_lines):
    """重写 P4-implementation.md：结构化 design_gaps + design_gap_reviews（无散文缺口）。"""
    (d / "P4-implementation.md").write_text(
        "---\nagent: impl\n"
        "design_gaps:\n  - {id: DG1, text: x}\n"
        "design_gap_reviews:\n" + review_lines + "---\nbody\n",
        encoding="utf-8",
    )


def test_minor4_verdict_enum_out_of_range_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-4：design_gap_reviews.verdict 越界 → ERROR（限定 accepted|rejected|followup）。"""
    d = h.init_task_via_conftest(tmp_path)
    _p4_with_reviews(
        d,
        "  - {gap: DG1, verdict: bogus, checked_against: [P2-design.md], basis: in_bdd}\n",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode == 1 and "verdict" in r.output and "越界" in r.output, r.output


def test_minor4_basis_enum_out_of_range_errors(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """MINOR-4：design_gap_reviews.basis 越界 → ERROR（in_bdd|out_of_scope|followup:DEBT<n>）。"""
    d = h.init_task_via_conftest(tmp_path)
    _p4_with_reviews(
        d,
        "  - {gap: DG1, verdict: accepted, checked_against: [P2-design.md], basis: bogus}\n",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P7", str(d))
    assert r.returncode == 1 and "basis" in r.output and "越界" in r.output, r.output


def test_cso_f2_p4_implementation_subdir_requires_frontmatter(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """cso F-2：`P4-implementation/**/*.md` 的**直接子文件**缺 frontmatter → ERROR。

    （改前：frontmatter 强制面用 fnmatch，`P4-implementation/direct.md` 逃逸。）
    """
    d = h.init_task_via_conftest(tmp_path)
    direct = d / "P4-implementation" / "direct.md"
    direct.parent.mkdir(parents=True, exist_ok=True)
    direct.write_text("no frontmatter\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(direct))
    assert r.returncode == 1, f"cso F-2：子目录声明文件缺 frontmatter 须 ERROR，rc={r.returncode}"


def test_cso_f2_nested_subdir_requires_frontmatter(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """cso F-2：`P4-implementation/sub/nested.md` 缺 frontmatter → ERROR（深层同样强制）。"""
    d = h.init_task_via_conftest(tmp_path)
    nested = d / "P4-implementation" / "sub" / "nested.md"
    nested.parent.mkdir(parents=True, exist_ok=True)
    nested.write_text("no frontmatter\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(nested))
    assert r.returncode == 1, f"cso F-2：深层子目录声明文件缺 frontmatter 须 ERROR，rc={r.returncode}"


def test_cso_f4_p7_blocker_count_is_system_field(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """cso F-4：P7 `blocker_count` 登记为系统字段——md-field-get 按 findings 现算（非文件值）。"""
    d = h.init_task_via_conftest(tmp_path)
    p7 = d / "P7-consistency.md"
    p7.write_text(
        "---\nagent: test\nblocker_count: 0\n"
        "findings:\n"
        "  - {id: F1, severity: blocker, text: x, status: open}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(
        python_exe,
        str(agate_scripts / "agate-md-field-get.py"),
        "blocker_count",
        env={"FILE": str(p7)},
    )
    assert r.returncode == 0, r.output
    assert r.output.strip() == "1", (
        f"cso F-4：blocker_count 须按 findings 现算（1），非文件值 0，实际 {r.output!r}"
    )
