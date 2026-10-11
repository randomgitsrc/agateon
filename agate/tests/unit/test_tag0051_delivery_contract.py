# agate/tests/unit/test_tag0051_delivery_contract.py — TAG0051 P3 红灯（delivery 取值域）
#
# 覆盖 BDD（P1-requirements.md）：16 / 17。
#   * BDD-16：非 legacy 任务 `delivery.method` 取契约声明的**合法枚举值** ⇒ `check-gate.py P8` exit 2。
#   * BDD-17（反例）：取**枚举外非空值** ⇒ exit 1。
#
# 前置（P2-design §9.1）：枚举校验只在「非 legacy **且** `task_level ≥ 2`」任务生效——
#   本仓当前唯一非 legacy 任务是 TAG0051 自身（level 1，无 `method_enum` ⇒ no-op）
#   ⇒ **须构造 level-2 夹具**方能先红。夹具沿用黄金 fixture 账本形态（`task_created.contract_level: 2`）。
#
# 现行为（改动前）：`level-2.yaml`（含 `delivery.method_enum`）尚未落地、`gate_p8` 无枚举校验
#   ⇒ 合法/非法取值**都** exit 2 ⇒ BDD-17 断言失败 = B 类红灯（BDD-16 为正向控制，当前即绿）。
#
# 平台无关：tmp_path；run_cli(python_exe, ...)（不裸 python3）；显式 encoding；
#   不写仓库内已提交文件（夹具**只读**复制到 tmp_path）。不写字面系统临时目录。

import shutil

_LEVEL2_FIXTURE = "task-data/level-2/pass/gate-events.jsonl"
_P8_PASS_EXIT = 2


def _p8_body(method):
    return (
        "---\n"
        "bump_type: minor\n"
        "debt_check: none\n"
        "delivery:\n"
        f"  method: {method}\n"
        "  ref:\n"
        "    - CHANGELOG.md\n"
        "---\n\n"
        "# P8 交付收尾（level-2 fixture）\n"
    )


def _level2_task(tmp_path, load_fixture, method, task_id="TAG9002"):
    """建一个 `task_level == 2` 的最小任务夹具（账本取自 level-2 黄金 fixture）。"""
    td = tmp_path / "task"
    td.mkdir(parents=True, exist_ok=True)
    (td / ".state.yaml").write_text(
        f"task_id: {task_id}\nphase: P8\nretries: {{}}\n", encoding="utf-8"
    )
    shutil.copyfile(str(load_fixture(_LEVEL2_FIXTURE)), str(td / "gate-events.jsonl"))
    (td / "P8-release.md").write_text(_p8_body(method), encoding="utf-8")
    return td


def _run_p8(td, agate_scripts, python_exe, run_cli, cwd):
    return run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P8", str(td), cwd=str(cwd)
    )


def test_level2_fixture_encodes_contract_level_2(load_fixture):
    """非真空前置：level-2 黄金 fixture 的账本确以 `contract_level: 2` 定格 task_level。"""
    text = load_fixture(_LEVEL2_FIXTURE).read_text(encoding="utf-8")
    assert '"contract_level": 2' in text or '"contract_level":2' in text, (
        "P2-design §9.1：level-2 黄金 fixture 须以 contract_level=2 定格 task_level（否则 BDD-16/17 真空）"
    )


def test_bdd_16_delivery_method_valid_enum_exit_2(
    tmp_path, load_fixture, agate_scripts, python_exe, run_cli
):
    """BDD-16：level-2 任务 `delivery.method` 取合法枚举值 ⇒ exit 2。"""
    td = _level2_task(tmp_path, load_fixture, "release-notes")
    result = _run_p8(td, agate_scripts, python_exe, run_cli, tmp_path)
    assert result.returncode == _P8_PASS_EXIT, (
        f"BDD-16：合法枚举 method 应通过（rc={_P8_PASS_EXIT}），实际 rc={result.returncode}"
    )


def test_bdd_17_delivery_method_out_of_enum_exit_1(
    tmp_path, load_fixture, agate_scripts, python_exe, run_cli
):
    """BDD-17（反例）：level-2 任务 `delivery.method` 取枚举外非空值 ⇒ exit 1。"""
    td = _level2_task(tmp_path, load_fixture, "definitely-not-in-enum")
    result = _run_p8(td, agate_scripts, python_exe, run_cli, tmp_path)
    assert result.returncode == 1, (
        "BDD-17：枚举外非空 method 应被拦截（exit 1），"
        f"实际 rc={result.returncode}（枚举校验应读 level-2 快照 delivery.method_enum）"
    )
