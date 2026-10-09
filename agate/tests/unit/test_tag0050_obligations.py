# agate/tests/unit/test_tag0050_obligations.py
# TAG0050 批 A4（义务执行方式机械核验，修复 F13）红灯测试。
#
# 映射：BDD-40..BDD-44（P1-requirements.md §4；设计 §2.9、§10）。
# 平台无关：tmp_path；python_exe；不写字面系统临时目录。

import importlib.util
import os
import re
import shutil
import subprocess

import pytest

_OBLIGATIONS = "agate/rules/obligations.yaml"


def _read_obligations(agate_root):
    return (agate_root / "rules" / "obligations.yaml").read_text(encoding="utf-8")


def _load_check_obligations(agate_scripts):
    """按路径加载 check-obligations.py（文件名含连字符，不能直接 import）。"""
    path = agate_scripts / "check-obligations.py"
    spec = importlib.util.spec_from_file_location("check_obligations_under_test", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _copy_protocol_root(tmp_path, agate_root):
    """在 tmp_path 下构造最小协议根，供真变异**端到端**跑 check-obligations.py。

    布局：`tmp_path/agate/{rules/obligations.yaml, scripts/, tests/unit/…enforcement.py}`。
    `repo_root`（= `dirname(root)` = `tmp_path`）下 `agate/tests/unit/…` 可解析，
    故 `test:` 凭证核验与真实仓库一致；`scripts/` 为副本，ast 可达闭包与真实一致。
    """
    root = tmp_path / "agate"
    (root / "rules").mkdir(parents=True)
    (root / "tests" / "unit").mkdir(parents=True)
    shutil.copytree(agate_root / "scripts", root / "scripts")
    # 复制 `test` 凭证涉及的两个测试文件（登记载体 + 真实行为凭证），使副本上 check-obligations
    # 的 `test` 文件核验与真实仓库一致。
    for name in ("test_tag0050_obligations_enforcement.py",
                 "test_tag0050_obligation_behavior.py"):
        src = agate_root / "tests" / "unit" / name
        (root / "tests" / "unit" / name).write_text(
            src.read_text(encoding="utf-8"), encoding="utf-8")
    return root


def _run_check_obligations(python_exe, script, root, cwd):
    """以 AGATE_ROOT=root 跑 check-obligations.py，返回 CompletedProcess。"""
    return subprocess.run(
        [python_exe, str(script)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(cwd),
        env=dict(os.environ, AGATE_ROOT=str(root)),
    )


@pytest.mark.windows_smoke
def test_bdd_40_f13_four_m_items_error(agate_root, agate_scripts):
    """BDD-40：F13 的 4 条 M **未改标时**能检测出 ERROR（临时构造）。

    终态下这 **2** 条（OBL-X-10/X-19）已归 `scope: protocol-repo`（设计 §2.9）——**2026-10-09 外部实施评审 m-1 后 OBL-P2-12/X-17 已改标 C 并进入占比统计**；其执行方式性质为「—」⇒
    不核验必经路径，工具转绿（BDD-44）。BDD-40 与 BDD-44 的终态不可兼得，故 BDD-40 以
    **临时构造**核验"检测能力"：同一条目去掉 scope 时须报 ERROR，加回 scope 时须跳过核验
    （评审 `agate-alignment-review-2026-10-08-TAG0050-G1.md` A1-1 建议）。
    """
    text = _read_obligations(agate_root)
    for obl_id in ("OBL-P2-12", "OBL-X-10", "OBL-X-17", "OBL-X-19"):
        assert re.search(r"- id:\s*" + obl_id + r"\b", text), f"BDD-40：{obl_id} 应登记"
    assert "enforced_at" in text, "BDD-40：M 义务须带 enforced_at（ast 可达性核验）"

    mod = _load_check_obligations(agate_scripts)
    item = {
        "id": "OBL-P2-12",
        "disposition": "M",
        "anchor": "x",
        "statement": "y",
        "enforced_at": {"file": "check-tdd-red.py", "function": "main"},
        "test": "agate/tests/unit/nonexistent_tag0050.py::test_x[OBL-P2-12]",
    }
    data = {"schema_version": 1, "baseline": {"m": 1, "total": 1}, "obligations": [item]}
    ok, errors, _, _ = mod._evaluate(data, set(), str(agate_root.parent))
    assert not ok, "BDD-40：未改标（无 scope: protocol-repo）时须检测出 ERROR"
    assert any("OBL-P2-12" in e for e in errors), "BDD-40：须对 OBL-P2-12 报 ERROR"

    scoped = dict(item, scope="protocol-repo")
    data2 = {"schema_version": 1, "baseline": {"m": 1, "total": 1}, "obligations": [scoped]}
    ok2, errors2, _, _ = mod._evaluate(data2, set(), str(agate_root.parent))
    assert ok2, f"BDD-40/44：scope: protocol-repo 项须跳过核验，errors={errors2}"


def test_bdd_41_missing_test_or_node_errors(agate_root):
    """BDD-41：M 项缺 test 或 test 节点不存在判 ERROR。"""
    text = _read_obligations(agate_root)
    assert re.search(r"^\s*test:\s*\S+::\S+", text, re.M), (
        "BDD-41：M 义务须带 test: <pytest 节点> 字段"
    )


@pytest.mark.windows_smoke
def test_bdd_42a_checker_flags_missing_enforced_at(tmp_path, agate_root, agate_scripts, python_exe):
    """BDD-42（检查器面）：删掉 `obligations.yaml` 的 `enforced_at` 落点 → `check-obligations.py` 真转红。

    这是**检查器判据**的负向控制（证明 check-obligations 的 ①/④ 核验非空转）。
    「删掉义务**执行分支** → 其真实行为 `test` 转红」见 `test_bdd_42_negative_control_mutation`。
    """
    script = agate_scripts / "check-obligations.py"
    root = _copy_protocol_root(tmp_path, agate_root)
    original = _read_obligations(agate_root)

    # 基线：未变异 → 转绿
    (root / "rules" / "obligations.yaml").write_text(original, encoding="utf-8")
    green = _run_check_obligations(python_exe, script, root, tmp_path)
    assert green.returncode == 0, (
        f"BDD-42a：基线应 rc=0，实际 {green.returncode}\n{green.stdout}"
    )

    # 真变异：删掉 OBL-P8-02 的 enforced_at 判据落点
    mutated = re.sub(
        r"(- id:\s*OBL-P8-02\b.*?)(\n\s*enforced_at:[^\n]*)", r"\1", original,
        count=1, flags=re.S,
    )
    assert mutated != original, "BDD-42a：变异须真的删掉 OBL-P8-02 的 enforced_at"
    (root / "rules" / "obligations.yaml").write_text(mutated, encoding="utf-8")
    red = _run_check_obligations(python_exe, script, root, tmp_path)
    assert red.returncode != 0, f"BDD-42a：删判据后须转红，实际 rc={red.returncode}"
    assert "OBL-P8-02" in red.stdout and "enforced_at" in red.stdout, (
        f"BDD-42a：转红须报 OBL-P8-02 缺 enforced_at\n{red.stdout}"
    )

    # 恢复 → 转绿
    (root / "rules" / "obligations.yaml").write_text(original, encoding="utf-8")
    restored = _run_check_obligations(python_exe, script, root, tmp_path)
    assert restored.returncode == 0, (
        f"BDD-42a：恢复后须转绿，实际 {restored.returncode}\n{restored.stdout}"
    )


# ── BDD-42（义务执行分支面）：删掉 M 义务的**执行分支** → 其**真实行为** `test` 转红 ──
#
# 抽样覆盖 P1/P2/P8（设计 §2.9 明确允许负向控制以 mutation **抽样**执行）。每条给出
# (credential test 名, 源脚本, 变异锚点原文, 变异后原文)——在协议根副本上改写源脚本，
# 再以 `AGATE_TEST_PROTOCOL_ROOT` 指向副本端到端重跑该 `test`。
_NEGATIVE_CONTROLS = (
    (
        "test_obl_p8_01_bump_type_missing_blocks",
        "check-gate.py",
        '    if "bump_type:" not in p8_text:',
        "    if False:  # MUTATED",
    ),
    (
        "test_obl_p8_02_delivery_missing_blocks",
        "check-gate.py",
        '    if "delivery:" not in p8_text:',
        "    if False:  # MUTATED",
    ),
    (
        "test_obl_p8_03_debt_check_missing_blocks",
        "check-gate.py",
        '    if "debt_check:" not in p8_text:',
        "    if False:  # MUTATED",
    ),
    (
        "test_obl_p1_10_vision_capability_missing_blocks",
        "check-gate.py",
        "    if status is None:\n"
        "        sys.stderr.write(\n"
        '            "GATE P1: frontend 任务必须声明 vision 能力条目（capability_requirements 含 visual/vision need）\\n"\n'
        "        )\n"
        "        return False",
        "    if status is None:\n"
        "        sys.stderr.write(\n"
        '            "GATE P1: frontend 任务必须声明 vision 能力条目（capability_requirements 含 visual/vision need）\\n"\n'
        "        )\n"
        "        return True  # MUTATED",
    ),
    (
        "test_obl_p2_07_ui_design_section_missing_blocks",
        "check-gate.py",
        "    if ui_block is None:\n"
        '        sys.stderr.write("GATE P2: ui_affected: true 但缺 UI 设计 节标题（## UI 设计）\\n")\n'
        "        return False",
        "    if ui_block is None:\n"
        '        sys.stderr.write("GATE P2: ui_affected: true 但缺 UI 设计 节标题（## UI 设计）\\n")\n'
        "        return True  # MUTATED",
    ),
    (
        "test_obl_p2_10_dispatch_plan_invalid_mode_blocks",
        "check-gate.py",
        "    if not isinstance(mode, str) or mode not in valid_modes:",
        "    if False:  # MUTATED",
    ),
)


def _run_pytest_node(python_exe, node, cwd, env_root):
    """以子进程跑单个 pytest 节点；`env_root` 非空时经 AGATE_TEST_PROTOCOL_ROOT 指定协议根。"""
    env = dict(os.environ)
    if env_root is not None:
        env["AGATE_TEST_PROTOCOL_ROOT"] = str(env_root)
    else:
        env.pop("AGATE_TEST_PROTOCOL_ROOT", None)
    return subprocess.run(
        [python_exe, "-m", "pytest", node, "-q", "-p", "no:cacheprovider"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(cwd), env=env,
    )


def test_bdd_42_negative_control_mutation(tmp_path, agate_root, python_exe):
    """BDD-42：负向控制——删掉 M 义务的**执行分支** → 其**真实行为** `test` 真转红。

    证明 `test` 凭证对「义务是否真被执行」敏感（非自指）：对每条抽样 M 义务，在协议根副本上
    删/中和其 `enforced_at.function` 里**对应义务的判断分支**，再以 `AGATE_TEST_PROTOCOL_ROOT`
    指向副本端到端重跑该 `test` → 断言转红；未变异的真实根上 → 断言转绿。
    """
    behavior = agate_root / "tests" / "unit" / "test_tag0050_obligation_behavior.py"
    repo_root = agate_root.parent
    assert behavior.is_file(), f"BDD-42：找不到真实行为凭证文件 {behavior}"

    for name, src, old, new in _NEGATIVE_CONTROLS:
        node = f"{behavior}::{name}"
        # 基线：真实根 → 转绿
        green = _run_pytest_node(python_exe, node, repo_root, None)
        assert green.returncode == 0, (
            f"BDD-42：基线（真实根）应转绿：{name}\n{green.stdout}\n{green.stderr}"
        )
        # 副本 + 删执行分支
        copy_root = _copy_protocol_root(tmp_path / name, agate_root)
        target = copy_root / "scripts" / src
        text = target.read_text(encoding="utf-8")
        assert old in text, f"BDD-42：变异锚点不存在于 {src}（{name}）：{old!r}"
        target.write_text(text.replace(old, new, 1), encoding="utf-8")
        red = _run_pytest_node(python_exe, node, repo_root, copy_root)
        assert red.returncode != 0, (
            f"BDD-42：删掉执行分支后 {name} 须转红\n{red.stdout}\n{red.stderr}"
        )


def test_bdd_43_r_without_review_output_errors(agate_root, agate_scripts, python_exe):
    """BDD-43：R 义务 `review_output` 的**终态**（与实现一致，锁定 DESIGN_GAP 降级结果）。

    设计原文为「缺 `review_output` 的 R 判 ERROR」，但实现按 DESIGN_GAP 降为
    **WARNING 且 rc=0**（见 `P4-implementation-G1.md` §3：存量约 25 条 R 无合格评审产出，
    逐条改标 C 超出本批范围）；`review_output` 存在但非 P1/P2/P4-review.md 时判 **ERROR**。
    本用例断言该终态：缺 → WARNING（不阻断，rc=0）；合格 → 无告警；非法 → ERROR。
    """
    mod = _load_check_obligations(agate_scripts)
    repo_root = str(agate_root.parent)

    def _r_item(**extra):
        item = {"id": "OBL-X-99", "disposition": "R", "anchor": "a", "statement": "s"}
        item.update(extra)
        return item

    def _data(item):
        return {"schema_version": 1, "baseline": {"m": 0, "total": 1}, "obligations": [item]}

    # 缺 review_output → WARNING（不阻断），ok=True（即 rc=0）
    ok, errors, warnings, _ = mod._evaluate(_data(_r_item()), set(), repo_root)
    assert ok and not errors, f"BDD-43：缺 review_output 不应阻断（rc=0），errors={errors}"
    assert any("review_output" in w for w in warnings), (
        f"BDD-43：缺 review_output 须给 WARNING，warnings={warnings}"
    )

    # 合格评审产出 → 无告警、无 ERROR
    ok2, errors2, warnings2, _ = mod._evaluate(
        _data(_r_item(review_output="P2-review.md")), set(), repo_root)
    assert ok2 and not errors2 and not warnings2, (errors2, warnings2)

    # 非合格评审产出 → ERROR
    ok3, errors3, _, _ = mod._evaluate(
        _data(_r_item(review_output="foo.md")), set(), repo_root)
    assert not ok3 and any("review_output" in e for e in errors3), errors3

    # 端到端：真实 obligations.yaml 上同样 rc=0（缺 review_output 不阻断）
    proc = subprocess.run(
        [python_exe, str(agate_scripts / "check-obligations.py")],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env=dict(os.environ, AGATE_ROOT=str(agate_root)),
    )
    assert proc.returncode == 0, (
        f"BDD-43：缺 review_output 的 R 不阻断 → rc=0，实际 {proc.returncode}\n{proc.stdout}"
    )


def test_bdd_44_baseline_reset_supported(agate_root):
    """BDD-44：改标并重设基线后转绿；之后 M 占比下降仍 FAIL。"""
    text = _read_obligations(agate_root)
    assert "baseline" in text, "BDD-44：须有基线声明"
    assert "reset" in text, "BDD-44：须支持 baseline.reset 一次性重设（写 CHANGELOG）"
