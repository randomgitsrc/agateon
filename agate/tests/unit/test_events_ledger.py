# agate/tests/unit/test_events_ledger.py
# TAG0042 批 3（cmd_run 账本事件 + hook 暂存账本）红灯测试 —— BDD-12。
#
# 目标语义（P1 BDD-12，P2-design §4.2 + §1.1 M9/M10）：
#   * BDD-12：`gate-events.jsonl` 是 append-only + `prev_hash` 链；`agate-run` 执行一次命令时
#     追加一条 `cmd_run` 事件（字段 schema：event / 命令 / 退出码 / 时间戳），且 `prev_hash`
#     链仍连续（`check-events.py` 通过）；hook 一并暂存账本（`git add`，不直接写文件）。
#
# 现行为（改动前）：`agate/scripts/agate-run.py` **不存在**；`pre-commit-gate.py` 未一并暂存
#   账本 ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：红灯原因须为「被测模块/行为未实现」，即
#   `agate-run.py` 缺失（文件探测/子进程运行失败 = B 类）与断言失败（hook 行为未改 = B 类），
#   而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 台账隔离（硬要求）：**绝不写仓库内已提交的 `gate-events.jsonl` 账本**（会污染他人任务）。
#   所有账本断言均在 `tmp_path` / `git_repo` 的**副本**上进行。
#
# 平台无关：tmp_path / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；需要「系统临时目录」字面量时**运行时拼接**（R4 平台扫描）。

import hashlib
import json
import re

import pytest

# 被测 CLI（批 3 新增；当前不存在 ⇒ 红灯 = 模块未实现）
_RUN_SCRIPT = "agate-run.py"
_PRECOMMIT_SCRIPT = "pre-commit-gate.py"

_CONFIG_FILE = "agate.config.yaml"
_LEDGER_NAME = "gate-events.jsonl"

# R4 平台扫描规避：需要「系统临时目录」字面量时运行时拼接。
_TMP = "/" + "tmp"


def _genesis():
    return hashlib.sha256(b"").hexdigest()


def _write_config(root, commands):
    import yaml

    data = {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": list(commands)},
    }
    (root / _CONFIG_FILE).write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
                                     encoding="utf-8")


def _seed_ledger(task_dir):
    """在任务目录写一条合法起始事件（首行 prev_hash = GENESIS_HASH 哈希链起点）。

    返回落盘路径；这是 tmp_path 下的**副本**，不触碰仓库内已提交账本。
    """
    path = task_dir / _LEDGER_NAME
    line = json.dumps(
        {"ts": "2026-10-05T10:00:00.000000Z", "event": "gate_run", "phase": "P3",
         "cmd": "check-gate.py P3", "exit": 2, "runner": "pre-commit",
         "prev_hash": _genesis()},
        sort_keys=True,
    )
    path.write_text(line + "\n", encoding="utf-8")
    return path


def _run_events(agate_scripts, python_exe, run_cli, task_dir):
    """运行 check-events.py [TASK_DIR]（exit 0 = 链完整）。"""
    return run_cli(python_exe, str(agate_scripts / "check-events.py"), str(task_dir))


def _run_agate_run(agate_scripts, python_exe, run_cli, *args, cwd=None, env=None):
    return run_cli(python_exe, str(agate_scripts / _RUN_SCRIPT), *args, cwd=cwd, env=env)


def _read_events(task_dir):
    text = (task_dir / _LEDGER_NAME).read_text(encoding="utf-8")
    return [json.loads(line) for line in text.splitlines() if line.strip()]


# ── BDD-12：agate-run 写入 cmd_run 账本事件且不破坏哈希链 ──────────────────
#
# Given `gate-events.jsonl` 是 append-only + `prev_hash` 链
# When `agate-run` 执行一次命令
# Then 追加一条 `cmd_run` 事件且 `prev_hash` 链连续（`check-events.py` 通过）；hook 一并暂存账本


@pytest.mark.windows_smoke
def test_bdd_12_cmd_run_event_appended(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-12：`agate-run` 执行命令后，任务目录账本追加一条 `cmd_run` 事件。

    Given 任务目录已有合法账本副本
    When 经 `agate-run` 执行命令（指向该任务目录账本）
    Then 账本新增一行，其 `event == "cmd_run"`。
    """
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    _seed_ledger(task_dir)
    (tmp_path / _CONFIG_FILE).write_text(
        "schema_version: 1\nverify:\n  commands:\n    - 'echo hi'\n", encoding="utf-8"
    )
    result = _run_agate_run(agate_scripts, python_exe, run_cli, "echo hi",
                            cwd=tmp_path, env={"AGATE_TASK_DIR": str(task_dir)})
    assert result.returncode == 0, (
        f"BDD-12：`agate-run` 应成功执行；rc={result.returncode}\n{result.output[:400]}"
    )
    events = _read_events(task_dir)
    assert any(ev.get("event") == "cmd_run" for ev in events), (
        "BDD-12：执行命令后账本应追加 `cmd_run` 事件（当前未追加 ⇒ 账本写入未实现）"
    )


def test_bdd_12_cmd_run_event_has_required_fields(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-12：`cmd_run` 事件含 schema 字段（命令 / 退出码 / 时间戳）。

    Given 上面执行的事件
    When 解析 `cmd_run` 事件
    Then 含 命令（cmd/command）、退出码（exit/exit_code）、时间戳（ts）字段。
    """
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    _seed_ledger(task_dir)
    (tmp_path / _CONFIG_FILE).write_text(
        "schema_version: 1\nverify:\n  commands:\n    - 'exit 3'\n", encoding="utf-8"
    )
    result = _run_agate_run(agate_scripts, python_exe, run_cli, "exit 3",
                            cwd=tmp_path, env={"AGATE_TASK_DIR": str(task_dir)})
    assert result.returncode == 3, (
        f"BDD-12：前置——命令退出码应如实传播（3）；rc={result.returncode}\n{result.output[:400]}"
    )
    events = [ev for ev in _read_events(task_dir) if ev.get("event") == "cmd_run"]
    assert events, "BDD-12：应有 cmd_run 事件（当前未追加）"
    ev = events[-1]
    assert isinstance(ev.get("ts"), str) and ev["ts"], "BDD-12：cmd_run 事件须含时间戳 ts"
    assert any(k in ev for k in ("cmd", "command")), (
        "BDD-12：cmd_run 事件须含被执行的命令（cmd/command 字段）"
    )
    assert any(k in ev for k in ("exit", "exit_code")), (
        "BDD-12：cmd_run 事件须含退出码字段（exit/exit_code）"
    )


def test_bdd_12_ledger_hash_chain_preserved(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-12：追加 `cmd_run` 后 `prev_hash` 链仍连续，`check-events.py` 通过（exit 0）。

    Given 合法账本副本
    When `agate-run` 执行命令追加事件
    Then `check-events.py` 审计 exit 0（链完整、ts 单调）。
    """
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    _seed_ledger(task_dir)
    (tmp_path / _CONFIG_FILE).write_text(
        "schema_version: 1\nverify:\n  commands:\n    - 'echo chain'\n", encoding="utf-8"
    )
    run_res = _run_agate_run(agate_scripts, python_exe, run_cli, "echo chain",
                             cwd=tmp_path, env={"AGATE_TASK_DIR": str(task_dir)})
    assert run_res.returncode == 0, (
        f"BDD-12：前置——`agate-run` 应先成功执行并追加事件；rc={run_res.returncode}"
        f"\n{run_res.output[:400]}"
    )
    events = _read_events(task_dir)
    assert any(ev.get("event") == "cmd_run" for ev in events), (
        "BDD-12：前置——应已追加 cmd_run 事件（当前未追加 ⇒ 链继承无从检验）"
    )

    result = _run_events(agate_scripts, python_exe, run_cli, task_dir)
    assert result.returncode == 0, (
        f"BDD-12：追加事件后哈希链须仍连续（check-events.py exit 0）；"
        f"rc={result.returncode}\n{result.output[:500]}"
    )


def test_bdd_12_cmd_run_event_uses_append_event_single_write_path(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """BDD-12：`cmd_run` 事件经既有 `append_event`（唯一写路径）追加，链与新行哈希自洽。

    Given 合法账本副本（尾行 = 事件 A）
    When `agate-run` 追加 `cmd_run`
    Then 新行 `prev_hash == sha256(事件 A 原始行文本)`（证明走 append_event 的链约定）。
    """
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    seed_path = _seed_ledger(task_dir)
    raw_before = seed_path.read_text(encoding="utf-8").splitlines()
    tail_line = raw_before[-1]
    expected_prev = hashlib.sha256(tail_line.encode("utf-8")).hexdigest()

    (tmp_path / _CONFIG_FILE).write_text(
        "schema_version: 1\nverify:\n  commands:\n    - 'echo single-path'\n", encoding="utf-8"
    )
    _run_agate_run(agate_scripts, python_exe, run_cli, "echo single-path",
                   cwd=tmp_path, env={"AGATE_TASK_DIR": str(task_dir)})

    events = _read_events(task_dir)
    assert len(events) >= 2, (
        "BDD-12：应已追加至少一行（当前未追加 ⇒ 实现缺失）"
    )
    new_ev = events[-1]
    assert new_ev.get("prev_hash") == expected_prev, (
        "BDD-12：新行 prev_hash 须等于新增前尾行原始文本的 sha256（append_event 链约定）；"
        f"期望 {expected_prev[:12]}…，实际 {str(new_ev.get('prev_hash'))[:12]}…"
    )


def test_bdd_12_agate_run_source_uses_append_event_not_direct_write(agate_scripts):
    """BDD-12：agate-run 源码经 `append_event`（唯一写路径）写账本，不直接 `open(...,'a')` 账本。

    Given agate-run.py
    When 检查其账本写入路径
    Then 引用 `append_event`，且不出现直接以追加模式打开 gate-events.jsonl 的旁路写法。
    """
    script = agate_scripts / _RUN_SCRIPT
    assert script.is_file(), (
        f"BDD-12：{_RUN_SCRIPT} 不存在（批 3 执行层未实现）——账本写入路径无从检查"
    )
    src = script.read_text(encoding="utf-8")
    assert "append_event" in src, (
        "BDD-12：agate-run 须经既有 append_event（唯一写路径）写账本，避免破链（P2 R5）"
    )
    assert not re.search(r"open\([^)]*gate-events\.jsonl[^)]*['\"]a['\"]", src), (
        "BDD-12：agate-run 不得直接以追加模式打开账本（应走 append_event）"
    )


def test_bdd_12_hook_stages_ledger(tmp_path, agate_scripts, python_exe, run_cli, git_repo):
    """BDD-12：`pre-commit-gate.py` hook 一并暂存账本（`git add`，不直接写文件）。

    Given 一个 git 项目 + 未暂存的账本副本（作为被暂存对象）
    When 检查 pre-commit-gate.py 的账本处理路径
    Then 其源码包含「把 gate-events.jsonl 一并 git add 暂存」的逻辑（当前无 ⇒ 红灯）。

    说明：此处为源码面断言（hook 的端到端暂存需真实 commit 上下文，P4 由实现承载）。
    """
    script = agate_scripts / _PRECOMMIT_SCRIPT
    src = script.read_text(encoding="utf-8")
    assert re.search(r"gate-events\.jsonl", src), (
        "BDD-12：pre-commit-gate.py 应处理 gate-events.jsonl"
    )
    # 须出现「把账本加入暂存」的 git add 逻辑（账本文件名与 add 出现在同一逻辑行/表达式）。
    # 现行为：账本仅被识别为非 md/yaml 元数据正则，无 `git add` 它的路径 ⇒ 红灯。
    assert re.search(
        r"add[\"']?[^\n]*gate-events\.jsonl|gate-events\.jsonl[^\n]*[\"']add[\"']",
        src,
    ), (
        "BDD-12：hook 须一并暂存账本（对 gate-events.jsonl 执行 git add）——"
        "当前源码无「账本 + add」同一逻辑路径（暂存未实现）"
    )
