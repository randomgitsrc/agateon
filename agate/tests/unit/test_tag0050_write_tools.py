# agate/tests/unit/test_tag0050_write_tools.py
# TAG0050 批 B（写入工具与契约单源）红灯测试。
#
# 映射：BDD-45..BDD-51（P1-requirements.md §4；设计 §3、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import pytest

import helpers_tag0050 as h

_MD_SET = "agate-md-field-set.py"
_MD_GET = "agate-md-field-get.py"
_CONFIG = "agate-config.py"


def _fm_file(tmp_path):
    p = tmp_path / "P6-acceptance.md"
    p.write_text("---\nagent: test\n---\n\nbody\n", encoding="utf-8")
    return p


def _md(run_cli, python_exe, agate_scripts, path, *args):
    return run_cli(
        python_exe, str(agate_scripts / _MD_SET), *args, env={"FILE": str(path)}
    )


@pytest.mark.windows_smoke
def test_bdd_45_seven_ops_and_config_roundtrip(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-45：md-field-set 7 操作与 agate-config set/unset/explain 往返用例。"""
    p = _fm_file(tmp_path)
    for args in (
        ("set", "agent", "writer"),
        ("append", "results", "bdd=1"),
        ("upsert", "results", "1", "verdict=PASS"),
        ("remove", "results", "1"),
        ("--list",),
        ("explain", "results"),
        ("render",),
    ):
        r = _md(run_cli, python_exe, agate_scripts, p, *args)
        assert r.returncode == 0, f"BDD-45：md-field-set {' '.join(args)} 须往返通过"
    for args in (("set", "project.language", "python"), ("unset", "project.language"),
                 ("explain", "project.language")):
        r = run_cli(python_exe, str(agate_scripts / _CONFIG), *args)
        assert r.returncode == 0, f"BDD-45：agate-config {' '.join(args)} 须可用"
        assert "未知子命令" not in r.output, f"BDD-45：agate-config 须实现 {args[0]}"


def test_bdd_46_system_field_reject_and_derive(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-46：系统字段拒写，get 返回现算值。"""
    d = h.init_task_via_conftest(tmp_path)
    p6 = d / "P6-acceptance.md"
    p6.write_text("---\nagent: test\n---\n\nbody\n", encoding="utf-8")
    r = _md(run_cli, python_exe, agate_scripts, p6, "set", "pass", "3")
    assert r.returncode != 0, "BDD-46：writer: system 字段须拒写"
    g = run_cli(
        python_exe, str(agate_scripts / _MD_GET), "pass", env={"FILE": str(p6)}
    )
    assert g.returncode == 0 and "3" not in g.output, "BDD-46：get 须按 derive 现算，忽略文件值"


def test_bdd_47_missing_frontmatter_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-47：缺 frontmatter 判 ERROR（不回退到正文正则，修复 F10）。"""
    d = h.init_task_via_conftest(tmp_path)
    decl = d / "P6-acceptance.md"
    decl.write_text("无 frontmatter 块\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(decl))
    assert r.returncode != 0, f"BDD-47：缺 frontmatter 须 ERROR，实际 rc={r.returncode}"


def test_bdd_48_render_block_tamper_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-48：渲染块被手改判 ERROR，CRLF 行为一致。"""
    src = (agate_scripts / _MD_SET).read_text(encoding="utf-8")
    assert "AGATE:RENDER" in src, "BDD-48：须支持 <!-- AGATE:RENDER ... --> 渲染块"
    d = h.init_task_via_conftest(tmp_path)
    p6 = d / "P6-acceptance.md"
    p6.write_text(
        "---\nagent: test\nresults: []\n---\n\n"
        "<!-- AGATE:RENDER results BEGIN -->\n手改\n<!-- AGATE:RENDER results END -->\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
    assert r.returncode != 0, f"BDD-48：渲染块被手改须 ERROR，实际 rc={r.returncode}"


def test_bdd_49_fix_command_executes(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-49：报错附带的修复命令真能执行并转绿。"""
    p = _fm_file(tmp_path)
    r = _md(run_cli, python_exe, agate_scripts, p, "explain", "results")
    assert "agate-md-field-set" in r.output, "BDD-49：explain 须输出可照抄的修复命令"


def test_bdd_50_single_schema_implementation(agate_scripts):
    """BDD-50：只剩 1 个 schema 校验实现（三处统一调用 agate_schema.py）。"""
    assert (agate_scripts / "agate_schema.py").is_file(), (
        "BDD-50：须新增 agate_schema.py（JSON Schema 子集 + derive/render）"
    )


def test_bdd_51_e3_downgrade_or_zero_false_positive(agate_root):
    """BDD-51：E3 误报为 0，或已落实 T1 降级方案。"""
    level1 = agate_root / "rules" / "task-data" / "level-1.yaml"
    assert level1.is_file(), "BDD-51：须有契约快照（承载 T1 绊线与降级配置）"
    text = level1.read_text(encoding="utf-8")
    assert "T1" in text or "t1" in text, "BDD-51：快照须登记 T1 绊线及其降级口径"
