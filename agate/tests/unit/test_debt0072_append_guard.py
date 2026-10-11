# agate/tests/unit/test_debt0072_append_guard.py
# DEBT0072 回归：`agate-md-field-set.py` 的 **append/upsert/remove** 路径对「由脚本/角色产出」
# 字段（系统/证据字段）施加与 `set` **同一判据**的守卫（`_key_capability == "script"` 单源，
# ADR-014）。改前实证：`append pass text=probe` ⇒ OK（可把 `pass`/`fail` 写坏，污染 P6 判据输入面）。
#
# 映射：
#   ① 面穷尽：对每个 basename 的「由脚本/角色产出」字段集，append 一律被拒
#      （依据 check-frontmatter.py::SCHEMAS 全部条目 + 契约 files 节，见下方静态表）；
#   ② 展示↔行为一致：--list 标为「由脚本/角色产出」的键，set 与 append **均被拒**；
#   ③ 防过宽：合法 append 目标（scope_resolved / need_confirm / results）仍成功。
# 平台无关：tmp_path + python_exe + run_cli；不写字面系统临时目录。

import importlib.util
import re

import pytest

_MD_SET = "agate-md-field-set.py"

# 面穷尽表（DEBT0072 闭合判据「面穷尽后再启用」）。
# 「由脚本/角色产出」= `_evidence_fields(get_mod)` ∪ 契约 `writer: system` 字段，逐 basename：
#   * P1-requirements.md：无（schema 无证据字段，无 files 契约）
#   * P2-design.md      ：无
#   * P6-acceptance.md  ：pass, fail（契约 writer:system + 证据字段）、regression_pass（证据字段）
#   * P7-consistency.md ：blocker_count, deviation_critical_count（另具契约 writer:system）+
#                         deviation_count, design_gap_count, design_gap_reviewed_count,
#                         code_map_new_files_count, code_map_reviewed_count（证据字段）
_SCRIPT_FIELDS_BY_BASENAME = {
    "P1-requirements.md": {
        "header": (
            "agent: analyst\nrisk_level: high\nphases: [P1]\n"
            "packages: [agate]\ndomains: [backend]\n"
        ),
        "fields": [],
    },
    "P2-design.md": {
        "header": (
            "agent: architect\ncandidate_count: 1\npackages: [agate]\n"
            "domains: [backend]\nui_affected: false\n"
        ),
        "fields": [],
    },
    "P6-acceptance.md": {
        "header": "agent: verifier\npass: 1\nfail: 0\nui_affected: false\n",
        "fields": ["pass", "fail", "regression_pass"],
    },
    "P7-consistency.md": {
        "header": (
            "agent: reviewer\nblocker_count: 0\ndeviation_count: 0\n"
            "deviation_critical_count: 0\ndesign_gap_count: 0\n"
            "design_gap_reviewed_count: 0\n"
        ),
        "fields": [
            "blocker_count",
            "deviation_count",
            "deviation_critical_count",
            "design_gap_count",
            "design_gap_reviewed_count",
            "code_map_new_files_count",
            "code_map_reviewed_count",
        ],
    },
}

# 展示标为「由脚本/角色产出」的 basename（--list 上确实会列出 script 键者）。
_LISTED_SCRIPT_BASENAMES = ["P6-acceptance.md", "P7-consistency.md"]

_LABEL_TO_CAP = {
    "可 set": "set",
    "不可 set；需 append": "append",
    "由脚本/角色产出，不可 set": "script",
    "仅登记，不可写入": "none",
}
_GROUP_LABEL_TO_CAP = {
    "其它可 set 的 schema 合法字段": "set",
    "仅登记/需 append（不可 set）": "append",
    "由脚本/角色产出（不可 set）": "script",
    "仅登记，不可写入": "none",
}


def _run(run_cli, python_exe, agate_scripts, md_file, *args):
    return run_cli(
        python_exe, str(agate_scripts / _MD_SET), *args, env={"FILE": str(md_file)}
    )


def _make(tmp_path, basename, header):
    f = tmp_path / basename
    f.write_text(f"---\n{header}---\n\nbody\n", encoding="utf-8")
    return f


def _load_mod(agate_scripts):
    path = agate_scripts / _MD_SET
    spec = importlib.util.spec_from_file_location("agate_md_field_set_debt0072", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_list_capabilities(output):
    """从 --list 输出解析 {key: 展示宣称的能力}（task_fields 行 + 各分组行）。"""
    caps = {}
    for ln in output.splitlines():
        m = re.match(r"^  - (.+?): 当前值 = .*（(.+)）$", ln)
        if m and m.group(2) in _LABEL_TO_CAP:
            caps[m.group(1)] = _LABEL_TO_CAP[m.group(2)]
            continue
        head, _, rest = ln.partition(": ")
        if head in _GROUP_LABEL_TO_CAP:
            for k in (x.strip() for x in rest.split(",") if x.strip()):
                caps[k] = _GROUP_LABEL_TO_CAP[head]
    return caps


@pytest.mark.parametrize("basename", sorted(_SCRIPT_FIELDS_BY_BASENAME))
def test_debt0072_script_fields_append_rejected(
    tmp_path, agate_scripts, python_exe, run_cli, basename
):
    """① 面穷尽：每个 basename 的「由脚本/角色产出」字段，append 一律被拒。

    改前：P6 的 pass/fail、P7 的 blocker_count/deviation_critical_count 可被 append 写入
    （本用例转红）。
    """
    spec = _SCRIPT_FIELDS_BY_BASENAME[basename]
    for key in spec["fields"]:
        f = _make(tmp_path, basename, spec["header"])
        r = _run(run_cli, python_exe, agate_scripts, f, "append", key, "text=probe")
        assert r.returncode != 0, (
            f"[{basename}] {key} 是「由脚本/角色产出」字段，append 须被拒，实际 {r.output!r}"
        )
        assert key in r.output, (
            f"[{basename}] {key} 的拒绝信息须含字段名，实际 {r.output!r}"
        )
        # 字段结构不得被写坏：文件内容不变
        assert "text: probe" not in f.read_text(encoding="utf-8"), (
            f"[{basename}] {key} 被拒后不得落盘任何追加项"
        )


@pytest.mark.parametrize("basename", _LISTED_SCRIPT_BASENAMES)
def test_debt0072_list_script_keys_set_and_append_both_rejected(
    tmp_path, agate_scripts, python_exe, run_cli, basename
):
    """② 展示↔行为一致：--list 标为「由脚本/角色产出」的键，set 与 append 均被拒。"""
    spec = _SCRIPT_FIELDS_BY_BASENAME[basename]
    listed = _make(tmp_path, basename, spec["header"])
    out = _run(run_cli, python_exe, agate_scripts, listed, "--list")
    assert out.returncode == 0, out.output
    caps = _parse_list_capabilities(out.output)
    script_keys = sorted(k for k, c in caps.items() if c == "script")
    assert script_keys, f"[{basename}] 预期 --list 至少有一个「由脚本/角色产出」键，实际 {out.output!r}"

    for key in script_keys:
        case = _make(tmp_path, basename, spec["header"])
        s = _run(run_cli, python_exe, agate_scripts, case, "set", key, "1")
        assert s.returncode != 0, (
            f"[{basename}] {key} 展示「由脚本/角色产出」但 set 成功：{s.output!r}"
        )
        a = _run(run_cli, python_exe, agate_scripts, case, "append", key, "text=probe")
        assert a.returncode != 0, (
            f"[{basename}] {key} 展示「由脚本/角色产出」但 append 成功：{a.output!r}"
        )


def test_debt0072_script_universe_matches_single_source(agate_scripts):
    """白盒：静态面穷尽表 ≡ 判据单源 `_key_capability == "script"`（防表与判据漂移）。"""
    mod = _load_mod(agate_scripts)
    gm = mod._fm_get()
    for basename, spec in _SCRIPT_FIELDS_BY_BASENAME.items():
        for key in spec["fields"]:
            cap = mod._key_capability(str(agate_scripts / basename), key, gm)
            assert cap == "script", f"[{basename}] {key} 应判为 script，实际 {cap!r}"


@pytest.mark.parametrize(
    "basename,key,pair",
    [
        ("P1-requirements.md", "scope_resolved", "id=NC1"),
        ("P1-requirements.md", "need_confirm", "text=foo"),
        ("P6-acceptance.md", "results", "bdd=1 verdict=PASS evidence=ev.log"),
    ],
)
def test_debt0072_legit_append_targets_still_succeed(
    tmp_path, agate_scripts, python_exe, run_cli, basename, key, pair
):
    """③ 防过宽：合法 append 目标仍成功（守卫不得误伤非脚本字段）。"""
    spec = _SCRIPT_FIELDS_BY_BASENAME[basename]
    f = _make(tmp_path, basename, spec["header"])
    r = _run(run_cli, python_exe, agate_scripts, f, "append", key, pair)
    assert r.returncode == 0, f"[{basename}] 合法目标 {key} 的 append 须成功，实际 {r.output!r}"
    assert key in f.read_text(encoding="utf-8"), (
        f"[{basename}] {key} append 后须落盘，实际 {f.read_text(encoding='utf-8')!r}"
    )
