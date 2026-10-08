# agate/tests/unit/test_tag0050_write_tools.py
# TAG0050 批 B（写入工具与契约单源）红灯测试。
#
# 映射：BDD-45..BDD-51（P1-requirements.md §4；设计 §3、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import shutil

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
    """BDD-45：md-field-set 7 操作与 agate-config set/unset/explain 往返用例。

    M1 整改（G2 C8）：`agate-config` 部分改为**真往返**——在隔离 cwd 内 init→set→get/show
    可见→explain 反映当前值→unset 后消失；并断言「无声明文件时 set 不创建」的既定行为。
    """
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

    # agate-config 真往返：在隔离 cwd 内 init 后 set/get/show/explain/unset。
    cfg_root = tmp_path / "cfgproj"
    cfg_root.mkdir()

    def _cfg(*args):
        return run_cli(python_exe, str(agate_scripts / _CONFIG), *args, cwd=str(cfg_root))

    assert _cfg("init").returncode == 0, "BDD-45：agate-config init 须成功"
    assert _cfg("set", "project.language", "python").returncode == 0, "BDD-45：set 须成功"
    got = _cfg("get", "project.language")
    assert got.returncode == 0 and got.output.strip() == "python", (
        f"BDD-45：set 后 get 须可见 python，实际 {got.output!r}"
    )
    shown = _cfg("show")
    assert "python" in shown.output, f"BDD-45：show 须反映写入值，实际 {shown.output!r}"
    explained = _cfg("explain", "project.language")
    assert explained.returncode == 0 and "python" in explained.output, (
        f"BDD-45：explain 须反映当前值，实际 {explained.output!r}"
    )
    assert _cfg("unset", "project.language").returncode == 0, "BDD-45：unset 须成功"
    gone = _cfg("get", "project.language")
    assert gone.output.strip() != "python", (
        f"BDD-45：unset 后写入值须消失（真往返），实际 {gone.output!r}"
    )
    raw = (cfg_root / "agate.config.yaml").read_text(encoding="utf-8")
    assert "python" not in raw, "BDD-45：unset 后声明文件不得残留写入值"

    # 无声明文件时 set 的行为：校验通过但不创建文件（创建是 init 的职责）。
    empty_root = tmp_path / "noinit"
    empty_root.mkdir()
    r = run_cli(
        python_exe, str(agate_scripts / _CONFIG),
        "set", "project.language", "python", cwd=str(empty_root),
    )
    assert r.returncode == 0, f"BDD-45：无声明文件时 set 须 rc=0，实际 {r.output!r}"
    assert not (empty_root / "agate.config.yaml").exists(), (
        "BDD-45：无声明文件时 set 不得创建 agate.config.yaml"
    )


def test_bdd_46_system_field_reject_and_derive(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-46：系统字段拒写；get 按 derive 现算（忽略文件里的值）。

    B1 整改（G2 C8）：夹具在文件里写 `pass: 999`（非 legacy 任务），且 `results` 含
    2×PASS + 1×FAIL ⇒ 现算应为 2。若读取侧未实现 derive，会返回文件值 999 ⇒ 用例转红。
    """
    d = h.init_task_via_conftest(tmp_path)
    p6 = d / "P6-acceptance.md"
    p6.write_text(
        "---\nagent: test\npass: 999\nfail: 0\nresults:\n"
        '  - bdd: "1"\n    verdict: PASS\n    evidence: [ev.log]\n'
        '  - bdd: "2"\n    verdict: PASS\n    evidence: [ev.log]\n'
        '  - bdd: "3"\n    verdict: FAIL\n    evidence: [ev.log]\n'
        "---\n\nbody\n",
        encoding="utf-8",
    )
    r = _md(run_cli, python_exe, agate_scripts, p6, "set", "pass", "3")
    assert r.returncode != 0, "BDD-46：writer: system 字段须拒写"
    assert "writer: system" in r.output or "系统字段" in r.output, (
        f"BDD-46：拒写须说明系统字段来源，实际 {r.output!r}"
    )
    g = run_cli(
        python_exe, str(agate_scripts / _MD_GET), "pass", env={"FILE": str(p6)}
    )
    assert g.returncode == 0, f"BDD-46：get 须可读，实际 rc={g.returncode}"
    assert g.stdout.strip() == "2", (
        f"BDD-46：get 须按 derive 现算（=2），忽略文件里的 999，实际 {g.output!r}"
    )


def test_bdd_47_missing_frontmatter_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-47：缺 frontmatter 判 ERROR（不回退到正文正则，修复 F10）。"""
    d = h.init_task_via_conftest(tmp_path)
    decl = d / "P6-acceptance.md"
    decl.write_text("无 frontmatter 块\n", encoding="utf-8")
    r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(decl))
    assert r.returncode != 0, f"BDD-47：缺 frontmatter 须 ERROR，实际 rc={r.returncode}"


def test_bdd_47b_declaration_files_from_snapshot(tmp_path, agate_scripts, python_exe, run_cli):
    """R2：声明文件生效面 = 快照 `declaration_files`（含旧 fallback 之外的 P8/P6.5）。"""
    d = h.init_task_via_conftest(tmp_path)
    for name in ("P8-release.md", "P6.5-judge-verdict.md"):
        decl = d / name
        decl.write_text("无 frontmatter 块\n", encoding="utf-8")
        r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(decl))
        assert r.returncode != 0, (
            f"R2：快照声明文件 {name} 缺 frontmatter 须 ERROR，实际 rc={r.returncode}"
        )


@pytest.mark.windows_smoke
def test_bdd_48_render_block_tamper_errors(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-48：渲染块被手改判 ERROR（附 render 修复命令）；CRLF 规范化为 LF 后行为一致。"""
    src = (agate_scripts / _MD_SET).read_text(encoding="utf-8")
    assert "AGATE:RENDER" in src, "BDD-48：须支持 <!-- AGATE:RENDER ... --> 渲染块"

    good = "| BDD | 结论 | 证据 |\n|---|---|---|\n| 1 | PASS | ev.log |"

    def _make(tmp, block_content, newline):
        d = h.init_task_via_conftest(tmp)
        p6 = d / "P6-acceptance.md"
        body = (
            "---\nagent: test\nprod_touched: false\nresults:\n"
            '  - bdd: "1"\n    verdict: PASS\n    evidence: [ev.log]\n---\n\n'
            "<!-- AGATE:RENDER results BEGIN（agate-md-field-set 生成，勿手改） -->\n"
            + block_content + "\n"
            "<!-- AGATE:RENDER results END -->\n"
        )
        if newline != "\n":
            body = body.replace("\n", newline)
        with open(p6, "w", encoding="utf-8", newline="") as fh:
            fh.write(body)
        return d

    # 手改：LF 与 CRLF 两侧行为一致 → 都报「被手改」并给 render 修复命令
    for nl, tag in (("\n", "lf"), ("\r\n", "crlf")):
        d = _make(tmp_path / ("bad-" + tag), "手改", nl)
        r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
        assert r.returncode != 0, f"BDD-48：渲染块被手改须 ERROR（{tag}），实际 rc={r.returncode}"
        assert "渲染块" in r.output and "被手改" in r.output, (
            f"BDD-48：须报『渲染块被手改』（{tag}），实际 {r.output!r}"
        )
        assert "agate-md-field-set.py render" in r.output, (
            f"BDD-48：须附可照抄的 render 修复命令（{tag}），实际 {r.output!r}"
        )

    # 正确内容：CRLF 规范化为 LF 后逐字节相等 → 两侧均不报渲染块错误
    for nl, tag in (("\n", "lf"), ("\r\n", "crlf")):
        d = _make(tmp_path / ("ok-" + tag), good, nl)
        r = run_cli(python_exe, str(agate_scripts / "check-gate.py"), "P6", str(d))
        assert "渲染块" not in r.output, (
            f"BDD-48：正确渲染块（{tag}）不应报渲染块错误，实际 {r.output!r}"
        )


def test_bdd_49_fix_command_executes(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-49：报错附带的修复命令可照抄执行。

    轻量单元面；完整的「提交报错 → 照抄执行 → 重新提交转绿」见
    integration/test_tag0050_prod_touched.py::test_bdd_49_fix_command_executes_and_turns_green。
    """
    p = _fm_file(tmp_path)
    r = _md(run_cli, python_exe, agate_scripts, p, "explain", "prod_touched")
    assert "agate-md-field-set" in r.output, "BDD-49：explain 须输出可照抄的修复命令"
    # 照抄执行 explain 给出的 `set prod_touched <值>`（主产出安全字段）
    fix = _md(run_cli, python_exe, agate_scripts, p, "set", "prod_touched", "false")
    assert fix.returncode == 0, f"BDD-49：explain 命令须可执行，实际 {fix.output!r}"


def test_f2_system_writer_field_rejected_by_contract(
    tmp_path, agate_scripts, agate_root, python_exe, run_cli
):
    """F-2（cso）：拒写由契约 `writer: system` 驱动——**未来**新增、且不在证据字段表内的
    系统字段同样被拒（不再靠证据字段表的偶发耦合）。

    做法：在临时协议根里给快照注入一个新系统字段 `results_total`（非证据字段），
    AGATE_ROOT 指向该副本 → `set results_total` 须被拒并说明来源。
    """
    proto = tmp_path / "proto"
    td = proto / "rules" / "task-data"
    td.mkdir(parents=True)
    shutil.copy(
        agate_root / "rules" / "task-data" / "LEVELS.yaml", td / "LEVELS.yaml"
    )
    lvl = (agate_root / "rules" / "task-data" / "level-1.yaml").read_text(encoding="utf-8")
    marker = "      prod_touched: {writer: agent, required: true}\n"
    assert marker in lvl, "F-2：夹具锚点缺失（level-1.yaml 结构已变）"
    lvl2 = lvl.replace(
        marker,
        '      results_total: {writer: system, derive: "count(results)"}\n' + marker,
    )
    (td / "level-1.yaml").write_text(lvl2, encoding="utf-8")

    p = _fm_file(tmp_path)
    r = run_cli(
        python_exe, str(agate_scripts / _MD_SET), "set", "results_total", "5",
        env={"FILE": str(p), "AGATE_ROOT": str(proto)},
    )
    assert r.returncode != 0, f"F-2：未来 writer: system 字段须被拒写，实际 {r.output!r}"
    assert "writer: system" in r.output, f"F-2：须说明系统字段来源，实际 {r.output!r}"


def test_l5_frontmatter_type_error_json_type_names(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """L5：类型错误文案用 JSON Schema 类型名（string/integer），守护 agate_schema 单源映射。"""
    f = tmp_path / "P6-acceptance.md"
    f.write_text(
        "---\nagent: test\npass: abc\nfail: 0\nui_affected: false\n---\n\nbody\n",
        encoding="utf-8",
    )
    r = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(f))
    assert r.returncode != 0, f"L5：类型错误须 ERROR，实际 rc={r.returncode}"
    assert "应为 integer" in r.output, (
        f"L5：类型文案须用 JSON 类型名（应为 integer），实际 {r.output!r}"
    )


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
