# agate/tests/unit/test_config_schema.py
# TAG0042 批 2（agate-config 声明层）红/绿灯测试 —— BDD-5 / BDD-6 / BDD-20（批 2 面）。
#
# 目标语义（P1 BDD-5/6/20，P2-design §1.1 M5/M6 + §4.1 + §1.4）：
#   * BDD-5：`agate/rules/schema/project-config.schema.json` 校验声明；非法字段名或非法枚举值
#     → `agate-config validate` 返回非 0 并指出非法字段/值；合法声明返回 0。
#   * BDD-6：`agate_common.read_project_config()` 是**唯一读取函数**；全部消费方经它取值
#     （无第二个独立解析实现），且等价守护测试可验证「两处取值同源」。
#   * BDD-20（批 2 面）：声明读取路径不硬编码任何单一项目名/技术栈（R6 差分的设计层断言）。
#
# 现行为（改动前）：`agate/rules/schema/project-config.schema.json` **不存在**；
#   `agate_common.read_project_config` **不存在** ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：红灯原因为「被测模块/行为未实现」（schema 文件缺失、
#   read_project_config 函数缺失、validate 子命令不可用 = B 类），非 SyntaxError / 第三方 import 失败。
#
# 平台无关：tmp_path fixtures；run_cli(python_exe, ...)（不裸 python3）；显式 encoding="utf-8"；
#   不写仓库内已提交文件（全在 tmp_path）。schema 扫描只读协议根既有文件。

import importlib.util
import json
import re
import sys

import pytest

_CONFIG_SCRIPT = "agate-config.py"
_CONFIG_FILE = "agate.config.yaml"
_SCHEMA_REL = ("rules", "schema", "project-config.schema.json")

# 既有 4 个 schema（P2-design §1.2 N6：新 schema 须与之同构）。
_EXISTING_SCHEMAS = (
    "dispatch.schema.json",
    "markers.schema.json",
    "phases.schema.json",
    "roles.schema.json",
)


def _dump_yaml(data):
    import yaml

    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def _write_config(root, data):
    (root / _CONFIG_FILE).write_text(_dump_yaml(data), encoding="utf-8")


def _write_config_raw(root, text):
    (root / _CONFIG_FILE).write_text(text, encoding="utf-8")


def _run_config(agate_scripts, python_exe, run_cli, *args, cwd=None):
    return run_cli(python_exe, str(agate_scripts / _CONFIG_SCRIPT), *args, cwd=cwd)


def _load_common(agate_scripts):
    """import agate_common（断言 read_project_config 存在与语义）。"""
    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "agate_common_schema", str(agate_scripts / "agate_common.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _schema_path(agate_root):
    return agate_root.joinpath(*_SCHEMA_REL)


# ── BDD-5：agate-config 声明 schema 校验拒绝非法形态 ───────────────────────
#
# Given 一份声明文件含非法字段名或非法枚举值
# When 运行 `agate-config validate`
# Then 返回非 0 并指出非法字段/值；合法声明返回 0


@pytest.mark.windows_smoke
def test_bdd_5_schema_file_exists_and_is_isomorphic(agate_root):
    """BDD-5：`rules/schema/project-config.schema.json` 须存在，且与既有 4 个 schema 同构。

    同构判据（P2-design §1.2 N6 / §1.4）：draft-07 子集，含 `$schema` / `title` / `type`
    / `properties` 顶层键，`type == object`。

    现行为：该 schema 文件不存在 ⇒ 红灯（模块未实现）。
    """
    schema_file = _schema_path(agate_root)
    assert schema_file.is_file(), (
        f"BDD-5：schema 文件不存在：{schema_file}（批 2 声明层未实现）"
    )
    data = json.loads(schema_file.read_text(encoding="utf-8"))

    existing = agate_root.joinpath("rules", "schema")
    for name in _EXISTING_SCHEMAS:
        ref = existing / name
        assert ref.is_file(), f"前置：既有 schema 缺失 {name}（结构漂移，需同步判据）"
        ref_data = json.loads(ref.read_text(encoding="utf-8"))
        for key in ("$schema", "title", "type", "properties"):
            assert key in data, (
                f"BDD-5：project-config.schema.json 缺顶层键 {key!r}"
                f"（既有 {name} 含该键，须同构）"
            )
        assert data.get("type") == ref_data.get("type") == "object", (
            "BDD-5：project-config.schema.json 的 type 须与既有 schema 同构（object）"
        )


def test_bdd_5_validate_rejects_illegal_enum_value(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-5：声明含**非法枚举值**（非法 preset）→ validate 返回非 0 并指出非法值。

    Given release.preset = "not-a-real-preset"（不在允许枚举内）
    When `agate-config validate`
    Then rc≠0 且输出指出非法字段/值。
    """
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": ["go test ./..."]},
        "release": {"preset": "not-a-real-preset"},
    })
    r = _run_config(agate_scripts, python_exe, run_cli, "validate", cwd=tmp_path)
    assert r.returncode != 0, (
        "BDD-5：非法枚举值应使 validate 返回非 0；当前 rc=0（校验未生效）"
        f"\n{r.output[:400]}"
    )
    assert "preset" in r.output or "not-a-real-preset" in r.output, (
        "BDD-5：validate 应指出非法字段/值（preset / not-a-real-preset）"
        f"\n{r.output[:400]}"
    )


def test_bdd_5_validate_rejects_unknown_top_level_field(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-5：声明含**非法字段名**（未知顶层字段）→ validate 返回非 0。"""
    _write_config_raw(
        tmp_path,
        "schema_version: 1\n"
        "project:\n"
        "  language: go\n"
        "bogus_field: surprise\n",
    )
    r = _run_config(agate_scripts, python_exe, run_cli, "validate", cwd=tmp_path)
    assert r.returncode != 0, (
        "BDD-5：未知字段应使 validate 返回非 0（拒绝非法形态）；当前 rc=0"
        f"\n{r.output[:400]}"
    )
    assert "bogus_field" in r.output, (
        "BDD-5：validate 应指出非法字段名 bogus_field"
        f"\n{r.output[:400]}"
    )


def test_bdd_5_validate_accepts_legal_declaration(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-5：合法声明 → validate 返回 0。"""
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": ["go test ./..."]},
        "release": {"preset": "semver-changelog-tag"},
        "paths": {"evidence": ".agate-evidence"},
    })
    r = _run_config(agate_scripts, python_exe, run_cli, "validate", cwd=tmp_path)
    assert r.returncode == 0, (
        f"BDD-5：合法声明应 validate rc=0；实际 rc={r.returncode}\n{r.output[:400]}"
    )


# ── BDD-6：唯一读取函数保证声明单源 ───────────────────────────────────────
#
# Given 声明文件与 schema 就位
# When 任意消费方读取某形态字段
# Then 全部消费方经**同一读取函数**取值（无第二个独立解析实现），且等价守护测试可验证
#       「两处取值同源」


def test_bdd_6_read_project_config_exists(agate_scripts):
    """BDD-6：`agate_common.read_project_config` 唯一读取函数须存在。

    现行为：agate_common.py 无该函数 ⇒ 红灯（模块未实现）。
    """
    src = (agate_scripts / "agate_common.py").read_text(encoding="utf-8")
    assert re.search(r"^def read_project_config\b", src, re.M), (
        "BDD-6：agate_common 应提供唯一读取函数 read_project_config()（当前不存在）"
    )


def test_bdd_6_read_project_config_returns_declared_values(tmp_path, agate_scripts):
    """BDD-6：read_project_config(root) 返回声明中的客观值（dict）。"""
    common = _load_common(agate_scripts)
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": ["go test ./..."]},
    })
    cfg = common.read_project_config(str(tmp_path))
    assert isinstance(cfg, dict), "BDD-6：read_project_config 应返回 dict"
    assert cfg.get("project", {}).get("language") == "go", (
        f"BDD-6：读取函数应返回声明值 language=go，实际 {cfg!r}"
    )


def test_bdd_6_read_project_config_malformed_yaml_is_graceful(tmp_path, agate_scripts):
    """BDD-6（C8 C1 回归）：文件存在但 YAML **非法** → `read_project_config` 优雅返回，不抛异常。

    Given 项目根 `agate.config.yaml` 含语法非法 YAML（flow sequence 未闭合）
    When 经唯一读取函数 read_project_config 读取
    Then **不抛异常**，`present is False`，`parse_error` 非空（与 docstring 契约一致）。

    回归背景（C8 review C1）：`yaml.safe_load` 对非法 YAML 抛 `yaml.YAMLError`（如
    `ParserError`），其**不继承** `ValueError`/`OSError`；修复前 `except (OSError, ValueError)`
    漏捕 → 抛未捕获 traceback。本用例锁定「优雅返回」契约。
    """
    common = _load_common(agate_scripts)
    # 非法 YAML：flow sequence 未闭合（safe_load 抛 ParserError）。
    _write_config_raw(tmp_path, "not: [a mapping\n")
    cfg = common.read_project_config(str(tmp_path))  # 不得抛异常
    assert isinstance(cfg, dict), "BDD-6：非法 YAML 仍应返回 dict（优雅降级）"
    assert cfg.get("present") is False, (
        f"BDD-6：非法 YAML 应 present=False；实际 {cfg.get('present')!r}"
    )
    assert cfg.get("parse_error"), (
        "BDD-6：非法 YAML 应给出非空 parse_error 说明；当前为空"
    )


def test_bdd_6_two_readers_agree_single_source(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-6（等价守护）：`agate-config get` 与 `read_project_config` **两处取值同源**。

    Given 同一份声明
    When 分别经 CLI（agate-config get）与库函数（read_project_config）读取 project.language
    Then 两者取值**完全一致**——证明无第二处独立解析实现（声明单源）。

    现行为：read_project_config 不存在 / agate-config 不存在 ⇒ 红灯。
    """
    common = _load_common(agate_scripts)
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": ["go test ./..."]},
    })
    via_lib = common.read_project_config(str(tmp_path)).get("project", {}).get("language")
    via_cli = _run_config(agate_scripts, python_exe, run_cli, "get", "project.language",
                          cwd=tmp_path)
    assert via_cli.returncode == 0, (
        f"BDD-6：CLI 读取应成功；rc={via_cli.returncode}\n{via_cli.output[:400]}"
    )
    assert via_lib == via_cli.stdout.strip() == "go", (
        "BDD-6：两处取值须同源（都经唯一读取函数）——"
        f"lib={via_lib!r}, cli={via_cli.stdout.strip()!r}"
    )


def test_bdd_6_no_second_independent_yaml_parser_in_config(agate_scripts):
    """BDD-6：`agate-config.py` 不得含**第二个独立 YAML 解析实现**（须复用唯一读取函数）。

    判据：若脚本内直接对声明文件做旁路 `yaml.safe_load` 解析（而非委托
    `agate_common.read_project_config`），即出现「第二处解析实现」⇒ 违反声明单源。

    现行为：脚本不存在 ⇒ 红灯（模块未实现）。
    """
    config_path = agate_scripts / _CONFIG_SCRIPT
    assert config_path.is_file(), (
        f"BDD-6：{_CONFIG_SCRIPT} 不存在（批 2 声明层未实现）"
    )
    src = config_path.read_text(encoding="utf-8")
    # 唯一读取路径的正向证据：须引用 agate_common 的读取函数
    assert "read_project_config" in src, (
        "BDD-6：agate-config.py 应经 agate_common.read_project_config 取值"
        "（当前未见引用 ⇒ 存在第二处解析实现的风险）"
    )
    # 负向证据：脚本自身不应直接 yaml.safe_load 项目根声明文件
    direct_parse = re.search(
        r"yaml\.safe_load\s*\(\s*(open\(|Path\(|.*" + re.escape(_CONFIG_FILE) + ")",
        src,
    )
    assert direct_parse is None, (
        "BDD-6：agate-config.py 含旁路 YAML 解析（第二处解析实现），违反声明单源"
    )


# ── BDD-20（批 2 面）：项目形态声明化不引入只适用于单一项目的规则 ─────────
#
# Given 每批的 R6 双向差分在临时目录副本上再加一份 peekview 只读副本
# When 对副本运行该批改动后的 consistency + 相关 gate
# Then 无「只适用于 agateon 一个项目」的规则引入
#
# P3 设计层收窄断言（dispatch-context 明确）：声明读取路径不硬编码任何单一项目名/技术栈。


def test_bdd_20_read_project_config_not_project_specific(agate_scripts):
    """BDD-20（批 2 面）：唯一读取函数 `read_project_config` 不硬编码单一项目名/技术栈。

    扫描 `read_project_config` 函数体，其中不得出现 agateon/pytest/peekview/md 等
    单项目形态字面量（声明读取应完全由声明文件驱动）。

    现行为：函数不存在 ⇒ 红灯（模块未实现）。
    """
    src = (agate_scripts / "agate_common.py").read_text(encoding="utf-8")
    m = re.search(r"^def read_project_config\(.*?\n(?=^def |\Z)", src, re.M | re.S)
    assert m is not None, (
        "BDD-20：agate_common.read_project_config 不存在——无法验证声明读取路径的项目无关性"
    )
    body = m.group(0)
    offenders = [tok for tok in ("agateon", "peekview", "pytest") if tok in body]
    assert not offenders, (
        "BDD-20：read_project_config 函数体硬编码了单一项目/技术栈 token："
        + ", ".join(offenders)
    )


def test_bdd_20_config_read_path_is_declaration_driven(tmp_path, agate_scripts):
    """BDD-20（批 2 面）：读取函数对**任意**形态声明都返回声明值（不因项目不同而变）。

    用一份「GitLab + Go + Helm」声明与一份「Python + Poetry」声明分别读取，
    返回值应各自忠实反映声明（证明读取由声明驱动，非单一项目规则）。

    现行为：函数不存在 ⇒ 红灯。
    """
    common = _load_common(agate_scripts)
    proj_a = tmp_path / "a"
    proj_b = tmp_path / "b"
    proj_a.mkdir()
    proj_b.mkdir()
    _write_config(proj_a, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
    })
    _write_config(proj_b, {
        "schema_version": 1,
        "project": {"language": "python", "package_manager": "poetry"},
    })
    cfg_a = common.read_project_config(str(proj_a))
    cfg_b = common.read_project_config(str(proj_b))
    assert cfg_a.get("project", {}).get("language") == "go", (
        "BDD-20：声明 A 应读回 go（读取由声明驱动）"
    )
    assert cfg_b.get("project", {}).get("language") == "python", (
        "BDD-20：声明 B 应读回 python（不得写死单一项目形态）"
    )
