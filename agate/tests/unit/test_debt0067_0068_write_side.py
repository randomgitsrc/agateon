# agate/tests/unit/test_debt0067_0068_write_side.py
# hotfix DEBT0067 + DEBT0068 回归：写侧（agate-md-field-set）与校验侧
# （agate-frontmatter-check）口径一致。
#
# 映射（r1 的 4 正 1 负 + r2 解耦新增）：
#   ① DEBT0067 `set ceremony full` 成功（改前：ERROR: 非法 key 'ceremony'）
#   ② DEBT0067 `set dispatch_plan <flow yaml>` 成功 + agate-md-field-get 读回合法 JSON
#   ③ DEBT0068 含 batches[].output（深度 4）的 P2 frontmatter 通过 check-frontmatter（改前 exit 1）
#   ④ DEBT0067 P8 的 delivery / debt_check 可写
#   ⑤ 负例（防放宽）：未知 key 仍被拒
#   ⑥ DEBT0067 r2：7 个 P1 schema 合法字段逐个可写（白名单第三来源 = SCHEMAS）
#   ⑦ DEBT0067 r2：「剩余缺失」语义守护——可选字段不得被报成缺失
#   ⑧ DEBT0067 r2：append-only 三键不与「可写清单」混列（展示面区分）
# 平台无关：tmp_path + python_exe + run_cli；不写字面系统临时目录。

import json
import re

import pytest

_MD_SET = "agate-md-field-set.py"
_MD_GET = "agate-md-field-get.py"

_P2_REQUIRED = "candidate_count: 2\npackages: [agate]\ndomains: [backend]\nui_affected: false\n"
_P1_REQUIRED = "risk_level: high\nphases: [P1]\npackages: [agate]\ndomains: [backend]\n"


def _run_set(agate_scripts, python_exe, run_cli, args, md_file):
    return run_cli(
        python_exe,
        str(agate_scripts / _MD_SET),
        *args,
        env={"FILE": str(md_file)},
    )


# ① DEBT0067：P1 的 ceremony 可写（读侧 SCHEMAS 早已认定合法，写侧此前分叉拒写）
def test_debt0067_p1_ceremony_writable(agate_scripts, python_exe, run_cli, tmp_path):
    p1 = tmp_path / "P1-requirements.md"
    p1.write_text(
        "---\nagent: analyst\nrisk_level: high\nphases: [P1]\npackages: [agate]\n"
        "domains: [backend]\n---\nbody\n",
        encoding="utf-8",
    )
    result = _run_set(agate_scripts, python_exe, run_cli, ["ceremony", "full"], p1)
    assert result.returncode == 0, result.output
    assert "ceremony: full" in p1.read_text(encoding="utf-8")


# ② DEBT0067：dispatch_plan 可写（此前被「追加/嵌套字段」直接拒写）+ get 读回合法 JSON
def test_debt0067_dispatch_plan_writable_and_readback_json(
    agate_scripts, python_exe, run_cli, tmp_path
):
    p2 = tmp_path / "P2-design.md"
    p2.write_text("---\nagent: architect\n" + _P2_REQUIRED + "---\nbody\n", encoding="utf-8")
    flow = "{mode: static-batch, parallel_limit: 3, batches: [{id: B1, complexity: medium}]}"
    result = _run_set(agate_scripts, python_exe, run_cli, ["dispatch_plan", flow], p2)
    assert result.returncode == 0, result.output

    got = run_cli(
        python_exe,
        str(agate_scripts / _MD_GET),
        "dispatch_plan",
        env={"FILE": str(p2)},
    )
    assert got.returncode == 0, got.output
    parsed = json.loads(got.stdout)  # 读回值须为合法 JSON（改前写入侧直接拒，无从谈起）
    assert parsed["mode"] == "static-batch"
    assert parsed["batches"][0]["id"] == "B1"


# ③ DEBT0068：含 dispatch_plan.batches[].output（深度 4）的 P2 frontmatter 通过校验
def test_debt0068_dispatch_plan_output_depth_passes(
    agate_scripts, python_exe, run_cli, tmp_path
):
    p2 = tmp_path / "P2-design.md"
    p2.write_text(
        "---\nagent: architect\n"
        + _P2_REQUIRED
        + "dispatch_plan:\n"
        "  mode: static-batch\n"
        "  parallel_limit: 3\n"
        "  batches:\n"
        "    - id: B1\n"
        "      complexity: medium\n"
        "      output: [src/a.py, src/b.py]\n"
        "---\n# P2 design\n",
        encoding="utf-8",
    )
    result = run_cli(
        python_exe, str(agate_scripts / "check-frontmatter.py"), str(p2)
    )
    assert result.returncode == 0, result.output
    assert "嵌套深度" not in result.output

    # 防放宽：豁免仅限 dispatch_plan——其它字段的深度校验不受影响（深度 4 仍 ERROR）。
    p2_bad = tmp_path / "P2-design.md"
    p2_bad.write_text(
        "---\nagent: architect\n"
        + _P2_REQUIRED
        + "coupling_checklist:\n"
        "  level1:\n"
        "    level2:\n"
        "      level3:\n"
        "        level4: too-deep\n"
        "---\n# P2 design\n",
        encoding="utf-8",
    )
    bad = run_cli(python_exe, str(agate_scripts / "check-frontmatter.py"), str(p2_bad))
    assert bad.returncode == 1, bad.output
    assert "coupling_checklist" in bad.output


# ④ DEBT0067：P8 的 delivery / debt_check 可写
def test_debt0067_p8_delivery_and_debt_check_writable(
    agate_scripts, python_exe, run_cli, tmp_path
):
    p8 = tmp_path / "P8-release.md"
    p8.write_text("---\nagent: implementer\nbump_type: patch\n---\nbody\n", encoding="utf-8")

    d = _run_set(
        agate_scripts, python_exe, run_cli,
        ["delivery", "{method: local, ref: [pkg-a], reason: 交付到本地}"], p8,
    )
    assert d.returncode == 0, d.output
    n = _run_set(agate_scripts, python_exe, run_cli, ["debt_check", "none"], p8)
    assert n.returncode == 0, n.output

    text = p8.read_text(encoding="utf-8")
    assert "debt_check: none" in text
    assert "method: local" in text


# ⑤ 负例（防放宽）：未知 key 仍被拒，且报「非法 key」
def test_debt0067_unknown_key_still_rejected(agate_scripts, python_exe, run_cli, tmp_path):
    p1 = tmp_path / "P1-requirements.md"
    p1.write_text("---\nagent: analyst\n---\nbody\n", encoding="utf-8")
    result = _run_set(agate_scripts, python_exe, run_cli, ["no_such_key", "1"], p1)
    assert result.returncode != 0
    assert "非法 key" in result.output


# ⑥ DEBT0067 r2：7 个 P1 schema 合法字段逐个可写（白名单第三来源 = SCHEMAS.migrated_keys）
_P1_SCHEMA_FIELDS = {
    "override": "handled-by-p1",
    "coupling_checklist": "api-schema checked",
    "internal_only": "true",
    "internal_only_reason": "no external deps",
    "跳过风险": "low-risk internal change",
    "design_trivial": "true",
    "follows_existing_pattern": "agate/scripts/sibling.py",
}


@pytest.mark.parametrize("field", sorted(_P1_SCHEMA_FIELDS.keys()))
def test_debt0067_r2_p1_schema_fields_writable(
    agate_scripts, python_exe, run_cli, tmp_path, field
):
    p1 = tmp_path / "P1-requirements.md"
    p1.write_text("---\nagent: analyst\n" + _P1_REQUIRED + "---\nbody\n", encoding="utf-8")
    result = _run_set(
        agate_scripts, python_exe, run_cli, [field, _P1_SCHEMA_FIELDS[field]], p1
    )
    assert result.returncode == 0, result.output
    assert field in p1.read_text(encoding="utf-8")


# ⑦ DEBT0067 r2：「剩余缺失」语义守护——task_fields 恢复原值后，可选字段不得被报成缺失
def test_debt0067_r2_optional_fields_not_reported_missing(
    agate_scripts, python_exe, run_cli, tmp_path
):
    # 必填四字段齐全 + 写一个可选字段；--list 不应再出现「剩余缺失」
    p1 = tmp_path / "P1-requirements.md"
    p1.write_text("---\nagent: analyst\n" + _P1_REQUIRED + "---\nbody\n", encoding="utf-8")
    assert _run_set(agate_scripts, python_exe, run_cli, ["ceremony", "full"], p1).returncode == 0

    listed = _run_set(agate_scripts, python_exe, run_cli, ["--list"], p1)
    assert listed.returncode == 0, listed.output
    assert "剩余缺失" not in listed.output, listed.output

    # 缺一个必填（domains）时：缺失面只含必填项，**不含**任何可选 schema 字段
    p1b = tmp_path / "P1-requirements.md"
    p1b.write_text(
        "---\nagent: analyst\nrisk_level: high\nphases: [P1]\npackages: [agate]\n---\nbody\n",
        encoding="utf-8",
    )
    listed2 = _run_set(agate_scripts, python_exe, run_cli, ["--list"], p1b)
    assert listed2.returncode == 0, listed2.output
    missing_line = next(
        (ln for ln in listed2.output.splitlines() if ln.startswith("剩余缺失")), ""
    )
    assert "domains" in missing_line
    for optional in ("ceremony", "implicit_coupling", "override", "ui_render_shape"):
        assert optional not in missing_line, missing_line


# ⑧ DEBT0067 r2：append-only 三键不与「可写清单」混列（展示面区分「可写」与「仅登记/需 append」）
def test_debt0067_r2_append_only_keys_not_in_writable_listing(
    agate_scripts, python_exe, run_cli, tmp_path
):
    p1 = tmp_path / "P1-requirements.md"
    p1.write_text("---\nagent: analyst\n" + _P1_REQUIRED + "---\nbody\n", encoding="utf-8")
    result = _run_set(agate_scripts, python_exe, run_cli, ["no_such_key", "1"], p1)
    assert result.returncode != 0
    writable_line = next(
        (ln for ln in result.output.splitlines() if "合法 key 清单" in ln), ""
    )
    for k in ("need_confirm_resolved", "suggest_resolved", "scope_resolved"):
        assert k not in writable_line, f"{k} 不应出现在可写清单里"
    # 但须在「仅登记/需 append」提示里出现（可发现性不丢）
    assert "仅登记/需 append" in result.output

    # set 该三键仍被拒（保留 append 语义，不放宽为可写）
    for k in ("need_confirm_resolved", "suggest_resolved", "scope_resolved"):
        r = _run_set(agate_scripts, python_exe, run_cli, [k, "x"], p1)
        assert r.returncode != 0 and "append" in r.output, r.output


# ⑨ DEBT0067 r3：展示分区**必须由实际守卫派生**——对 --list 里出现的**每个** key，
# 断言「展示宣称 ↔ 真实 set/append 行为」一致（机械化守护，防未来漂移）。
# 覆盖三类曾经的漂移：证据字段被标「可 set」（应 script）、无 append 能力的字段被标「需 append」
# （应 none）、以及真正的可 set / 需 append / 仅登记三类。

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


def _load_set_module(agate_scripts):
    import importlib.util

    path = agate_scripts / _MD_SET
    spec = importlib.util.spec_from_file_location("agate_md_field_set_r3", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _parse_list_capabilities(output):
    """从 --list 输出解析 {key: 展示宣称的能力}（task_fields 行 + 各分组行）。"""
    caps = {}
    for ln in output.splitlines():
        m = re.match(r"^  - (.+?): 当前值 = .*（(.+)）$", ln)
        if m:
            caps[m.group(1)] = _LABEL_TO_CAP[m.group(2)]
            continue
        head, _, rest = ln.partition(": ")
        if head in _GROUP_LABEL_TO_CAP:
            for k in (x.strip() for x in rest.split(",") if x.strip()):
                caps[k] = _GROUP_LABEL_TO_CAP[head]
    return caps


def _valid_set_value(mod, basename, key):
    """给 key 造一个 `set` 应接受的合法值（据真 schema/enum/类型派生）。"""
    schema = mod._fm_check().SCHEMAS.get(basename) or {}
    enums = schema.get("enums") or {}
    if key in enums:
        return next(iter(enums[key]))
    gm = mod._fm_get()
    t = (schema.get("types") or {}).get(key)
    if t is bool or key in gm.BOOL_FIELDS or key in gm.NO_FALLBACK_BOOL_FIELDS:
        return "true"
    if t is int or key in gm.INT_FIELDS or key in gm.NO_FALLBACK_INT_FIELDS:
        return "2"
    if t is list or key in gm.LIST_FIELDS or key in gm.NO_FALLBACK_LIST_FIELDS:
        return "a b"
    return "x"


def _append_pair(mod, file_path, key):
    """给 key 造一个 append 用的 k=v（主键名取自 spec；无 spec → 任意键）。"""
    spec = mod._field_spec(str(file_path), key)
    if spec is None:
        spec = mod._declaration_fields(str(file_path)).get(key)
    pk = spec.get("key") if isinstance(spec, dict) else None
    return f"{pk}=V1" if pk else "x=1"


@pytest.mark.parametrize(
    "basename,header",
    [
        pytest.param(
            "P1-requirements.md",
            "agent: analyst\nrisk_level: high\nphases: [P1]\n",
            id="P1",
        ),
        pytest.param(
            "P6-acceptance.md",
            "agent: verifier\npass: 1\nfail: 0\nui_affected: false\n",
            id="P6",
        ),
    ],
)
def test_debt0067_r3_list_partition_matches_real_behavior(
    agate_scripts, python_exe, run_cli, tmp_path, basename, header
):
    mod = _load_set_module(agate_scripts)

    listing_dir = tmp_path / "listing"
    listing_dir.mkdir()
    listed_file = listing_dir / basename
    listed_file.write_text(f"---\n{header}---\nbody\n", encoding="utf-8")
    listed = _run_set(agate_scripts, python_exe, run_cli, ["--list"], listed_file)
    assert listed.returncode == 0, listed.output
    caps = _parse_list_capabilities(listed.output)
    assert caps, listed.output

    for idx, (key, cap) in enumerate(sorted(caps.items())):
        # 每个 key 用**基名相同**的独立副本（schema/能力按 basename 分派）
        case_dir = tmp_path / f"case-{basename}-{idx}"
        case_dir.mkdir()
        f = case_dir / basename
        f.write_text(f"---\n{header}---\nbody\n", encoding="utf-8")

        value = _valid_set_value(mod, basename, key)
        s = _run_set(agate_scripts, python_exe, run_cli, ["set", key, value], f)

        if cap == "set":
            assert s.returncode == 0, f"[{basename}] {key} 展示「可 set」但 set 失败：{s.output}"
        elif cap == "script":
            assert s.returncode != 0, f"[{basename}] {key} 展示「脚本产出」但 set 成功"
        elif cap == "append":
            assert s.returncode != 0, f"[{basename}] {key} 展示「需 append」但 set 成功"
            a = _run_set(
                agate_scripts, python_exe, run_cli,
                ["append", key, _append_pair(mod, f, key)], f,
            )
            assert a.returncode == 0, f"[{basename}] {key} 展示「需 append」但 append 失败：{a.output}"
        else:  # none
            assert s.returncode != 0, f"[{basename}] {key} 展示「仅登记」但 set 成功"
            a = _run_set(
                agate_scripts, python_exe, run_cli,
                ["append", key, _append_pair(mod, f, key)], f,
            )
            assert a.returncode != 0, f"[{basename}] {key} 展示「仅登记」但 append 成功：{a.output}"

