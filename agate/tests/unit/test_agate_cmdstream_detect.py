# tests/unit/test_agate_cmdstream_detect.py — 命令流检测引擎（TAG0028 P3，RM-AG0055）
# 被测（P4 才新建，本文件当前必须全红）：
#   - agate/scripts/agate-cmdstream-detect.py（检测引擎：FROZEN 调用冻结 expected×2+兜底 300/900、
#     FROZEN 活动冻结 60/300、SPIN 窗口 10 重复≥5、NORMAL 含 REPEAT_UNIQUE_MIN=3 信息级、截断排除、
#     轮询误报标注；输出平台无关"证据+触发核查"；阈值从 maintainability.yaml 读取全兜底）
#
# 覆盖 P1-requirements.md BDD-8~24（17 条，1:1 映射）。
#
# 接口假设（P4 实现须提供，均有 P2-design.md §3.2 + verify_cmdstream_detection.py 判据依据）：
#   - detect(events, now, config=None) -> (verdict, reasons)
#     verdict ∈ {"FROZEN", "SPIN", "NORMAL"}；reasons 为字符串列表（阈值依据 + 级别 alert/suspect）
#   - events：活动事件 dict 列表，字段与 verify 脚本 Event 同构——
#     {"ts": int, "kind": "think"|"out"|"call"|"result", "id"?: str, "cmd"?: str,
#      "exit"?: int, "out"?: str, "expected"?: int, "truncated"?: bool}
#   - config：可选；dict（阈值显式覆盖，BDD-19）或路径字符串（maintainability.yaml 路径，
#     缺失/损坏兜底协议默认值不报错，BDD-20/21）；None 时读取默认配置源
#   - 阈值常量同源 verify 脚本：CALL_EXPECT_MULT=2 / CALL_FLOOR=30 / CALL_ALERT_FALLBACK=300 /
#     CALL_SUSPECT_FALLBACK=900 / ACTIVITY_ALERT=60 / ACTIVITY_SUSPECT=300 / SPIN_THRESHOLD=5 /
#     REPEAT_WINDOW=10 / REPEAT_UNIQUE_MIN=3
#   - reasons 须含级别关键字（"alert" / "suspect"）与阈值依据；SPIN 附重复组合与次数；
#     轮询误报场景附"轮询"标注（BDD-18）；输出不得含自动终止指令（BDD-23）与平台工具名（BDD-24）
#
# 红灯性质：被测脚本当前不存在——_load_script 检查文件存在性后 pytest.fail（B 类红灯）。
# BDD-22（verify 脚本 9 场景全 PASS 保持）为长期不变量：断言脚本存在 + 运行 exit 0 结论串
# （TAG0025 教训：不断言"Unreleased 段是否存在"类一次性事实）。

import importlib.util
import json

import pytest


def _load_detect(agate_scripts):
    """importlib 加载 agate-cmdstream-detect.py；缺失时 pytest.fail（B 类红灯）。"""
    path = agate_scripts / "agate-cmdstream-detect.py"
    if not path.is_file():
        pytest.fail(f"被测模块未实现: {path}（TDD 红灯，P4 实现后转绿）")
    spec = importlib.util.spec_from_file_location("agate_cmdstream_detect", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ev(ts, kind, **kw):
    """构造活动事件 dict（verify Event 同构）。"""
    ev = {"ts": ts, "kind": kind}
    ev.update(kw)
    return ev


def _run_detect(agate_scripts, events, now, config=None):
    """统一调用 detect 并断言返回 (verdict, reasons) 二元组结构（不判死锚）。"""
    mod = _load_detect(agate_scripts)
    result = mod.detect(events, now, config=config)
    assert isinstance(result, tuple) and len(result) == 2, (
        f"detect 返回结构应为 (verdict, reasons)，实际 {type(result)}"
    )
    verdict, reasons = result
    assert verdict in ("FROZEN", "SPIN", "NORMAL")
    assert isinstance(reasons, list)
    return verdict, reasons


# ================= BDD-8: 调用冻结·主信号（expected×2） =================


def test_bdd_8_call_freeze_expected_x2(agate_scripts):
    """BDD-8：未结束 call + expected 声明 → 距今超过 max(expected×2, 30s) → FROZEN（调用冻结），
    原因注明 expected×2 主信号来源。"""
    events = [
        _ev(0, "call", id="c0", cmd="setup", expected=200),
        _ev(100, "call", id="c1", cmd="long_cmd", expected=200),
    ]
    # c1 距今 401s > max(200×2, 30)=400 → 调用冻结
    verdict, reasons = _run_detect(agate_scripts, events, now=501)
    assert verdict == "FROZEN"
    joined = "\n".join(reasons)
    assert "expected" in joined  # 主信号来源（expected×2）
    assert "c1" in joined


# ================= BDD-9: 调用冻结·兜底 alert（300s） =================


def test_bdd_9_call_freeze_fallback_alert_300(agate_scripts):
    """BDD-9：未结束 call 无 expected → 距今超过 300s 但未超 900s → FROZEN（alert 级提示核查）。"""
    events = [_ev(0, "call", id="c1", cmd="network_call_no_timeout")]
    verdict, reasons = _run_detect(agate_scripts, events, now=301)
    assert verdict == "FROZEN"
    joined = "\n".join(reasons)
    assert "alert" in joined  # 级别标注
    assert "300" in joined  # 兜底阈值依据


# ================= BDD-10: 调用冻结·兜底 suspect（900s） =================


def test_bdd_10_call_freeze_fallback_suspect_900(agate_scripts):
    """BDD-10：未结束 call 无 expected → 距今超过 900s → FROZEN（suspect 级考虑中止提示）。"""
    events = [_ev(0, "call", id="c1", cmd="network_call_no_timeout")]
    verdict, reasons = _run_detect(agate_scripts, events, now=901)
    assert verdict == "FROZEN"
    joined = "\n".join(reasons)
    assert "suspect" in joined  # 级别标注
    assert "900" in joined  # 兜底阈值依据


# ================= BDD-11: 活动冻结·alert（60s） =================


def test_bdd_11_activity_freeze_alert_60(agate_scripts):
    """BDD-11：无未结束调用 → 最后活动事件距今超过 60s 但未超 300s → FROZEN（alert 级活动冻结）。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
    ]
    verdict, reasons = _run_detect(agate_scripts, events, now=61)
    assert verdict == "FROZEN"
    joined = "\n".join(reasons)
    assert "alert" in joined
    assert "60" in joined


# ================= BDD-12: 活动冻结·suspect（300s） =================


def test_bdd_12_activity_freeze_suspect_300(agate_scripts):
    """BDD-12：无未结束调用 → 最后活动事件距今超过 300s → FROZEN（suspect 级活动冻结）。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
    ]
    verdict, reasons = _run_detect(agate_scripts, events, now=301)
    assert verdict == "FROZEN"
    joined = "\n".join(reasons)
    assert "suspect" in joined
    assert "300" in joined


# ================= BDD-13: 三类活动信号均计入、长时间思考不误杀 =================


def test_bdd_13_long_thinking_no_false_freeze(agate_scripts):
    """BDD-13：subagent 20 分钟未调工具但 think 事件持续流动（最后活动 <60s）→ NORMAL；
    活动冻结看"任何一类活动事件"而非最后一条命令。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
        _ev(10, "think"),
        _ev(300, "think"),
        _ev(600, "think"),
        _ev(900, "think"),
        _ev(1190, "think"),
    ]
    verdict, reasons = _run_detect(agate_scripts, events, now=1200)
    assert verdict == "NORMAL"
    joined = "\n".join(reasons)
    assert "正常" in joined or "NORMAL" in joined


def test_bdd_13_output_activity_counts(agate_scripts):
    """BDD-13 补充：三类活动信号（思考/输出/工具）均计入活动——仅 output 事件持续流动也判 NORMAL。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
        _ev(500, "out"),
        _ev(1100, "out"),
    ]
    verdict, _ = _run_detect(agate_scripts, events, now=1150)
    assert verdict == "NORMAL"


# ================= BDD-14: 无效重复检测（SPIN） =================


def test_bdd_14_spin_repeat_signature(agate_scripts):
    """BDD-14：窗口 10 内同一 (命令, exit, 输出哈希) 组合重复 ≥5（截断输出除外）→ SPIN，
    附重复组合与重复次数。"""
    events = []
    for i in range(10):
        events.append(_ev(i * 2, "call", id=f"r{i}", cmd="retry_convert"))
        events.append(_ev(i * 2 + 1, "result", id=f"r{i}", cmd="retry_convert", exit=1, out="h_fail"))
    verdict, reasons = _run_detect(agate_scripts, events, now=20)
    assert verdict == "SPIN"
    joined = "\n".join(reasons)
    assert "retry_convert" in joined  # 重复组合
    assert "10" in joined  # 重复次数（窗口 10 内同组合 10 次 ≥5）


# ================= BDD-15: 结果签名变化不误报 =================


def test_bdd_15_signature_change_no_spin(agate_scripts):
    """BDD-15：命令名重复但 exit 或输出哈希在变化（合法测试-修复-迭代）→ NORMAL，不触发空转。"""
    events = [
        _ev(0, "call", id="1", cmd="run_test"), _ev(1, "result", id="1", cmd="run_test", exit=1, out="h_fail1"),
        _ev(2, "call", id="2", cmd="apply_fix"), _ev(3, "result", id="2", cmd="apply_fix", exit=0, out="h_fix1"),
        _ev(4, "call", id="3", cmd="run_test"), _ev(5, "result", id="3", cmd="run_test", exit=1, out="h_fail2"),
        _ev(6, "call", id="4", cmd="apply_fix"), _ev(7, "result", id="4", cmd="apply_fix", exit=0, out="h_fix2"),
        _ev(8, "call", id="5", cmd="run_test"), _ev(9, "result", id="5", cmd="run_test", exit=0, out="h_pass"),
    ]
    verdict, _ = _run_detect(agate_scripts, events, now=10)
    assert verdict == "NORMAL"


# ================= BDD-16: 唯一命令数 <3 信息级提示 =================


def test_bdd_16_unique_cmd_lt3_info(agate_scripts):
    """BDD-16：窗口 10 内唯一命令数 <3 且结果签名在变化 → 不判空转（NORMAL），附信息级提示。"""
    events = []
    for i in range(5):
        events.append(_ev(i * 2, "call", id=f"a{i}", cmd="run_test"))
        events.append(_ev(i * 2 + 1, "result", id=f"a{i}", cmd="run_test", exit=1, out=f"h_fail{i}"))
    verdict, reasons = _run_detect(agate_scripts, events, now=10)
    assert verdict == "NORMAL"
    joined = "\n".join(reasons)
    assert "唯一命令数" in joined or "3" in joined  # 信息级提示（REPEAT_UNIQUE_MIN=3）


# ================= BDD-17: 截断输出不参与无效重复哈希比对 =================


def test_bdd_17_truncated_not_in_hash_compare(agate_scripts):
    """BDD-17：窗口内多条命令输出均 truncated 且截断后哈希相同 → 不参与 (命令, exit, 输出哈希)
    比对 → NORMAL（不误判空转）。"""
    events = []
    for i in range(6):
        events.append(_ev(i * 2, "call", id=f"t{i}", cmd="fail_task"))
        events.append(_ev(i * 2 + 1, "result", id=f"t{i}", cmd="fail_task",
                          exit=1, out="h_trunc", truncated=True))
    verdict, _ = _run_detect(agate_scripts, events, now=12)
    assert verdict == "NORMAL"


def test_bdd_17_truncated_still_in_freeze_detect(agate_scripts):
    """BDD-17 补充：truncated 记录仍参与冻结检测——未结束的 truncated call 超阈值 → FROZEN。"""
    events = [
        _ev(0, "call", id="t1", cmd="long_task"),
    ]
    verdict, _ = _run_detect(agate_scripts, events, now=301)
    assert verdict == "FROZEN"


# ================= BDD-18: 轮询循环误报标注（合法轮询不判死） =================


def test_bdd_18_polling_loop_annotated(agate_scripts):
    """BDD-18：`gh pr checks --watch` 类合法轮询重复相同签名超过阈值 → 信号定位为核查提示
    （不自动判定/自动终止），附注轮询误报类标注。"""
    events = []
    for i in range(5):
        events.append(_ev(i * 2, "call", id=f"p{i}", cmd="gh pr checks --watch"))
        events.append(_ev(i * 2 + 1, "result", id=f"p{i}", cmd="gh pr checks --watch",
                          exit=0, out="h_poll"))
    _, reasons = _run_detect(agate_scripts, events, now=10)
    # 轮询重复同签名 → 可能触发 SPIN，但必须附轮询误报类标注（核查提示而非自动终止）
    joined = "\n".join(reasons)
    assert "轮询" in joined or "poll" in joined.lower()
    assert "终止" not in joined and "kill" not in joined.lower()


# ================= BDD-19: 阈值显式覆盖生效 =================


def test_bdd_19_threshold_override_config(agate_scripts):
    """BDD-19：config 显式覆盖活动冻结 alert 为 120s → 按覆盖值判定（61s 不冻结、121s 冻结），
    不使用协议默认 60s。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
    ]
    config = {"activity_alert": 120}
    # 距今 61s：默认 60s 会冻结，覆盖 120s 后 NORMAL
    verdict_normal, _ = _run_detect(agate_scripts, events, now=62, config=config)
    assert verdict_normal == "NORMAL"
    # 距今 121s：超过覆盖值 120s → FROZEN
    verdict_frozen, _ = _run_detect(agate_scripts, events, now=122, config=config)
    assert verdict_frozen == "FROZEN"


# ================= BDD-20: 阈值配置缺失兜底默认值 =================


def test_bdd_20_config_missing_fallback(agate_scripts, tmp_path):
    """BDD-20：阈值配置文件缺失（不存在路径）→ 兜底协议默认值（60s），正常运行不报错。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
    ]
    missing = str(tmp_path / "no-such-maintainability.yaml")
    # 距今 61s：默认 60s → FROZEN（兜底生效）；不抛异常
    verdict, _ = _run_detect(agate_scripts, events, now=61, config=missing)
    assert verdict == "FROZEN"


# ================= BDD-21: 阈值配置损坏兜底默认值 =================


def test_bdd_21_config_corrupt_fallback(agate_scripts, tmp_path):
    """BDD-21：阈值配置文件存在但损坏（YAML 解析失败）→ 兜底协议默认值，正常运行不报错、
    不静默跳过检测。"""
    events = [
        _ev(0, "call", id="c1", cmd="setup"),
        _ev(1, "result", id="c1", cmd="setup", exit=0, out="h1"),
    ]
    corrupt = tmp_path / "maintainability.yaml"
    corrupt.write_text("cmdstream_detection: [unclosed-bracket\n", encoding="utf-8")
    # 损坏配置 → 兜底默认 60s → 距今 61s FROZEN；不报错、不跳过
    verdict, reasons = _run_detect(agate_scripts, events, now=61, config=str(corrupt))
    assert verdict == "FROZEN"
    assert reasons  # 有判定输出（不静默跳过）


# ================= BDD-22: verify 脚本 9 场景全 PASS 保持 =================


def test_bdd_22_verify_script_all_pass(agate_root, python_exe, run_cli):
    """BDD-22（长期不变量）：verify_cmdstream_detection.py 存在且运行 exit 0，输出结论串
    「全部断言通过——命令流日志可机械区分九种状态」。TAG0025：断言脚本存在 + 运行结论，不断言
    一次性交付事实。"""
    verify = (
        agate_root.parent / "docs" / "design-notes"
        / "260903-design-subagent-liveness-and-self-dispatch"
        / "verify-heartbeat-cmdstream" / "verify_cmdstream_detection.py"
    )
    assert verify.is_file(), f"verify 脚本不存在: {verify}"
    result = run_cli(python_exe, str(verify))
    assert result.returncode == 0, f"verify 脚本非 0 退出: {result.returncode}\n{result.output}"
    assert "全部断言通过——命令流日志可机械区分九种状态" in result.output


# ================= BDD-23: 检测定位"证据 + 触发核查，不自动判死" =================


def test_bdd_23_evidence_no_auto_kill(agate_scripts):
    """BDD-23：FROZEN/SPIN 输出仅为客观证据（判定类别 + 原因 + 阈值依据），不含任何自动终止/
    自动中止 subagent 的动作指令。"""
    frozen_events = [_ev(0, "call", id="c1", cmd="network_call_no_timeout")]
    verdict_frozen, reasons_frozen = _run_detect(agate_scripts, frozen_events, now=901)
    assert verdict_frozen == "FROZEN"
    joined = "\n".join(reasons_frozen)
    # 证据形态：判定类别 + 原因 + 阈值依据
    assert "FROZEN" in joined or "冻结" in joined
    assert "900" in joined
    # 无自动动作指令（不判死）
    for word in ("kill", "terminate", "abort", "stop --force", "终止子任务"):
        assert word not in joined.lower(), f"检测输出含自动终止指令: {word}"

    spin_events = []
    for i in range(5):
        spin_events.append(_ev(i * 2, "call", id=f"r{i}", cmd="retry_convert"))
        spin_events.append(_ev(i * 2 + 1, "result", id=f"r{i}", cmd="retry_convert", exit=1, out="h_fail"))
    verdict_spin, reasons_spin = _run_detect(agate_scripts, spin_events, now=10)
    assert verdict_spin == "SPIN"
    joined_spin = "\n".join(reasons_spin)
    assert "SPIN" in joined_spin or "空转" in joined_spin
    for word in ("kill", "terminate", "abort", "终止子任务"):
        assert word not in joined_spin.lower(), f"检测输出含自动终止指令: {word}"


# ================= BDD-24: 检测/派发输出平台无关 =================


def test_bdd_24_output_platform_agnostic(agate_scripts):
    """BDD-24：检测输出为平台无关指令形态（判定类别 + 原因 + 阈值依据 + 建议动作方向），
    不含具体平台工具名/平台命令调用——同一输出可被三平台食谱原样消费。"""
    events = [_ev(0, "call", id="c1", cmd="network_call_no_timeout")]
    verdict, reasons = _run_detect(agate_scripts, events, now=901)
    assert verdict == "FROZEN"
    joined = "\n".join(reasons)
    for platform_word in ("claude", "opencode", "dsh"):
        assert platform_word not in joined.lower(), f"检测输出绑定平台: {platform_word}"


# ================= fix1（P4-review CRITICAL-1/3）补充测试：CLI detect 通路 =================


def _write_claude_session(tmp_path, lines):
    """写 claude-code JSONL 会话文件，返回路径（CLI detect 输入）。"""
    session = tmp_path / "cli-session.jsonl"
    session.write_text("".join(lines), encoding="utf-8")
    return session


def test_bdd_11_cli_detect_seconds_unit_no_false_freeze(agate_scripts, tmp_path, capsys):
    """BDD-11 补充（CRITICAL-1 复现场景）：CLI detect 时间单位归一——events ts 毫秒与
    --now 毫秒在 CLI 层统一转秒后，3 秒无活动不得误报 FROZEN「距今 3000s ≥ 300s」。
    修复前 ts/now 毫秒直接比对秒级阈值 → 3 秒无活动误报活动冻结。"""
    mod = _load_detect(agate_scripts)
    # 完成一次调用：ts_start=1788400860000ms（2026-09-03T02:01:00.000Z），结束同刻
    session = _write_claude_session(
        tmp_path,
        [
            '{"type":"tool_use","id":"toolu_cli_1","name":"Bash",'
            '"timestamp":"2026-09-03T02:01:00.000Z",'
            '"input":{"command":"env python3 -m pytest -q tests/unit"}}\n',
            '{"tool_use_id":"toolu_cli_1","type":"tool_result",'
            '"timestamp":"2026-09-03T02:01:00.000Z",'
            '"content":"Exit code 0\\n=== 12 passed ===","is_error":false}\n',
        ],
    )
    # --now 传毫秒（13 位）：距最后活动 3 秒 → 归一为 3s < 60s → NORMAL
    rc = mod.main(["detect", str(session), "--platform", "claude-code",
                   "--now", "1788400863000"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERDICT: NORMAL" in out, f"3 秒无活动不得误报冻结（CRITICAL-1），输出:\n{out}"
    assert "FROZEN" not in out


def test_bdd_9_cli_detect_unfinished_call_frozen(agate_scripts, tmp_path, capsys):
    """BDD-9 补充（CRITICAL-3）：CLI 通路未结束 call 可触发调用冻结——适配器产出
    exit=None/ts_end=None 记录 + CLI 事件 id 加序号保证唯一 → unresolved 不再被坍缩，
    距今超 300s 兜底 → FROZEN。修复前 claude/dsh CLI 通路 unresolved 恒空。"""
    mod = _load_detect(agate_scripts)
    # 同会话同命令两次调用：一次已结束（距今 10s）、一次未结束（距今 400s）
    session = _write_claude_session(
        tmp_path,
        [
            '{"type":"tool_use","id":"toolu_cli_2","name":"Bash",'
            '"timestamp":"2026-09-03T02:01:00.000Z",'
            '"input":{"command":"env python3 -m pytest -q tests/unit"}}\n',
            '{"tool_use_id":"toolu_cli_2","type":"tool_result",'
            '"timestamp":"2026-09-03T02:01:00.300Z",'
            '"content":"Exit code 0\\n=== 12 passed ===","is_error":false}\n',
            # 未结束 call（无配对 result），距今 400s
            '{"type":"tool_use","id":"toolu_cli_3","name":"Bash",'
            '"timestamp":"2026-09-03T02:05:00.000Z",'
            '"input":{"command":"env python3 -m pytest -q tests/unit"}}\n',
        ],
    )
    # 未结束 call ts=1788401100000ms（02:05:00.000Z）；now = ts + 400s = 1788401500000ms
    rc = mod.main(["detect", str(session), "--platform", "claude-code",
                   "--now", "1788401500000"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERDICT: FROZEN" in out, f"CLI 通路未结束 call 应触发调用冻结（CRITICAL-3），输出:\n{out}"
    assert "调用冻结" in out
    assert "300" in out  # 兜底阈值依据


def test_bdd_8_cli_detect_expected_signal(agate_scripts, tmp_path, capsys):
    """BDD-8 补充（CRITICAL-3 ③）：CLI --expected 注入事件 → expected×2 主信号可达
    （未结束 call 距今 350s：--expected 200 → 阈值 400s → 不冻结；无 expected → 兜底
    300s → FROZEN——两路径区分证明 expected 已接入 CLI 事件）。"""
    mod = _load_detect(agate_scripts)
    session = _write_claude_session(
        tmp_path,
        [
            '{"type":"tool_use","id":"toolu_cli_4","name":"Bash",'
            '"timestamp":"2026-09-03T02:05:00.000Z",'
            '"input":{"command":"full_pytest_xdist"}}\n',
        ],
    )
    # 未结束 call ts=1788401100000ms（02:05:00.000Z）；now = ts + 350s = 1788401450000ms
    now_ms = "1788401450000"
    # 无 expected → 距今 350s ≥ 兜底 300s → FROZEN
    rc = mod.main(["detect", str(session), "--platform", "claude-code", "--now", now_ms])
    assert rc == 0
    out1 = capsys.readouterr().out
    assert "VERDICT: FROZEN" in out1, f"无 expected 兜底应冻结（350s≥300s），输出:\n{out1}"
    # --expected 200 → 阈值 max(200×2,30)=400s → 350s 不冻结
    rc2 = mod.main(["detect", str(session), "--platform", "claude-code",
                    "--now", now_ms, "--expected", "200"])
    out2 = capsys.readouterr().out
    assert rc2 == 0
    assert "VERDICT: NORMAL" in out2, f"expected=200 时 350s < 400s 不应冻结（CRITICAL-3③），输出:\n{out2}"
    assert "expected=200s" in out2, "原因应注明 expected×2 主信号来源"


# ================= TAG0033: 检测引擎对 Codex 会话判三态（BDD-13~17，检测引擎零改动） =================
# 被测（P4 才新增，本节当前必须全红）：agate-cmdstream-adapters.py 的 class CodexAdapter。
# 范式：比照本文件既有三态确定性试验——CodexAdapter.read_commands 解析 Codex rollout →
#   记录转活动事件 dict（比照 agate-cmdstream-detect.py CLI 转换层 :343-369）→ detect(events, now)。
# 阈值用 RM-AG0055 §3.4.3 既有值（调用冻结 suspect 900s / 活动冻结 suspect 300s / SPIN 阈值 5），
#   不新造（见 test_bdd_21_detect_thresholds_unchanged 守护）。
# 红灯性质（B 类）：adapters.CodexAdapter 触发 AttributeError（模块无该属性）。仅 stdlib + pytest。

_CX_META = (
    '{"timestamp":"2026-09-08T21:01:55.000Z","ordinal":0,"type":"session_meta",'
    '"payload":{"id":"demo0000-0000-7000-a000-000000000abc",'
    '"session_id":"demo0000-0000-7000-a000-000000000abc","thread_source":"user",'
    '"cli_version":"0.153.4","originator":"codex-tui"}}\n'
)


def _load_cmdstream_adapters(agate_scripts):
    """importlib 加载 agate-cmdstream-adapters.py；缺失时 pytest.fail（B 类红灯）。"""
    path = agate_scripts / "agate-cmdstream-adapters.py"
    if not path.is_file():
        pytest.fail(f"被测模块未实现: {path}（TDD 红灯，P4 实现后转绿）")
    spec = importlib.util.spec_from_file_location(
        "agate_cmdstream_adapters_codextest", str(path)
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cx_exec(item_id, cmd, exit_code, out, t0, t1, truncated=False):
    """构造一行 event_msg/item_completed CommandExecution（rollout 封套形态）。"""
    item = {
        "type": "CommandExecution", "id": item_id,
        "command": ["/bin/bash", "-lc", cmd],
        "exit_code": exit_code, "status": "completed",
        "aggregated_output": out,
    }
    if truncated:
        item["output_truncated"] = True
        item["aggregated_output"] = out + " ...[output truncated]"
    payload = {"type": "item_completed", "started_at_ms": t0, "completed_at_ms": t1,
               "item": item}
    return json.dumps({"timestamp": "2026-09-08T21:02:00.000Z", "ordinal": 1,
                       "type": "event_msg", "payload": payload}) + "\n"


def _cx_started(item_id, cmd, t0):
    """构造一行 event_msg/item_started CommandExecution（未结束命令，无对应 item_completed）。"""
    payload = {"type": "item_started", "started_at_ms": t0,
               "item": {"type": "CommandExecution", "id": item_id,
                        "command": ["/bin/bash", "-lc", cmd],
                        "status": "in_progress", "aggregated_output": ""}}
    return json.dumps({"timestamp": "2026-09-08T21:02:00.000Z", "ordinal": 1,
                       "type": "event_msg", "payload": payload}) + "\n"


def _write_cx_rollout(tmp_path, lines, name="rollout-demo.jsonl"):
    p = tmp_path / name
    p.write_text(_CX_META + "".join(lines), encoding="utf-8")
    return p


def _records_to_events(records, expected=None):
    """比照 agate-cmdstream-detect.py CLI 转换层（:343-369）：CommandRecord → 活动事件 dict。"""
    events = []
    for idx, r in enumerate(records):
        if r.ts_start is None:
            continue
        ev_id = f"{r.session_id}:{r.tool}:{r.command}#{idx}"
        events.append({"ts": r.ts_start // 1000, "kind": "call", "id": ev_id,
                       "cmd": r.command, "expected": expected})
        if r.exit is not None or r.ts_end is not None:
            ts_end = (r.ts_end if r.ts_end is not None else r.ts_start) // 1000
            events.append({"ts": ts_end, "kind": "result", "id": ev_id, "cmd": r.command,
                           "exit": r.exit, "out": r.output_hash, "truncated": r.truncated})
    return events


# ---- BDD-13: Codex 会话调用冻结 → FROZEN ----


def test_bdd_13_codex_call_freeze_frozen(agate_scripts, tmp_path):
    """BDD-13：Codex 会话含未结束命令、无 expected，观察时刻距其 ts_start > 900s →
    verdict == "FROZEN"，reasons 含"调用冻结"字样。"""
    detect_mod = _load_detect(agate_scripts)
    adapters = _load_cmdstream_adapters(agate_scripts)

    t0 = 1788400000000
    session = _write_cx_rollout(tmp_path, [
        _cx_exec("done1", "setup step", 0, "ok\n", t0, t0 + 1000),
        _cx_started("hang1", "network_call_no_timeout", t0 + 2000),
    ])
    records = adapters.CodexAdapter().read_commands(str(session))
    events = _records_to_events(records)
    # 未结束命令 ts_start=(t0+2000)//1000=1788400002 秒；距今 901s > 兜底 suspect 900s
    verdict, reasons = detect_mod.detect(events, now=1788400002 + 901)
    assert verdict == "FROZEN"
    assert "调用冻结" in "\n".join(reasons)


# ---- BDD-14: Codex 会话活动冻结 → FROZEN ----


def test_bdd_14_codex_activity_freeze_frozen(agate_scripts, tmp_path):
    """BDD-14：Codex 会话所有命令均已结束，最后活动事件距观察时刻 > 300s →
    verdict == "FROZEN"，reasons 含"活动冻结"字样。"""
    detect_mod = _load_detect(agate_scripts)
    adapters = _load_cmdstream_adapters(agate_scripts)

    t0 = 1788400000000
    session = _write_cx_rollout(tmp_path, [
        _cx_exec("i1", "step one", 0, "a\n", t0, t0 + 1000),
        _cx_exec("i2", "step two", 0, "b\n", t0 + 2000, t0 + 3000),
    ])
    records = adapters.CodexAdapter().read_commands(str(session))
    events = _records_to_events(records)
    # 最后活动 = (t0+3000)//1000 = 1788400003 秒；距今 301s > 活动冻结 suspect 300s
    verdict, reasons = detect_mod.detect(events, now=1788400003 + 301)
    assert verdict == "FROZEN"
    assert "活动冻结" in "\n".join(reasons)


# ---- BDD-15: Codex 会话无效重复 → SPIN ----


def test_bdd_15_codex_invalid_repeat_spin(agate_scripts, tmp_path):
    """BDD-15：Codex 会话窗口内同 (command, exit, output_hash) 组合重复 ≥ 5 次
    （exit_code 与 aggregated_output 均不变、无截断）→ verdict == "SPIN"。"""
    detect_mod = _load_detect(agate_scripts)
    adapters = _load_cmdstream_adapters(agate_scripts)

    t0 = 1788400000000
    lines = [_cx_exec(f"r{i}", "retry_convert", 1, "same failure\n",
                      t0 + i * 2000, t0 + i * 2000 + 1000) for i in range(6)]
    session = _write_cx_rollout(tmp_path, lines)
    records = adapters.CodexAdapter().read_commands(str(session))
    events = _records_to_events(records)
    last = (t0 + 5 * 2000 + 1000) // 1000
    verdict, reasons = detect_mod.detect(events, now=last + 5)
    assert verdict == "SPIN"
    assert "retry_convert" in "\n".join(reasons)


# ---- BDD-16: Codex 会话正常推进 → NORMAL（不误报） ----


def test_bdd_16_codex_normal_progress_no_false_positive(agate_scripts, tmp_path):
    """BDD-16：Codex 会话命令持续推进、结果签名（exit 或输出哈希）在变化、无未结束调用
    悬挂超阈值 → verdict == "NORMAL"。"""
    detect_mod = _load_detect(agate_scripts)
    adapters = _load_cmdstream_adapters(agate_scripts)

    t0 = 1788400000000
    lines = [
        _cx_exec("n1", "run_test", 1, "fail A\n", t0, t0 + 1000),
        _cx_exec("n2", "apply_fix", 0, "patched A\n", t0 + 2000, t0 + 3000),
        _cx_exec("n3", "run_test", 1, "fail B\n", t0 + 4000, t0 + 5000),
        _cx_exec("n4", "apply_fix", 0, "patched B\n", t0 + 6000, t0 + 7000),
        _cx_exec("n5", "run_test", 0, "all pass\n", t0 + 8000, t0 + 9000),
    ]
    session = _write_cx_rollout(tmp_path, lines)
    records = adapters.CodexAdapter().read_commands(str(session))
    events = _records_to_events(records)
    last = (t0 + 9000) // 1000
    verdict, _ = detect_mod.detect(events, now=last + 5)
    assert verdict == "NORMAL"


# ---- BDD-17: Codex 会话截断输出不误判 SPIN ----


def test_bdd_17_codex_truncated_repeat_not_spin(agate_scripts, tmp_path):
    """BDD-17：Codex 会话同命令、同 exit、输出均被截断（truncated=True → output_hash=None）
    重复 ≥ 5 次 → verdict != "SPIN"（截断输出不参与哈希比对）。"""
    detect_mod = _load_detect(agate_scripts)
    adapters = _load_cmdstream_adapters(agate_scripts)

    t0 = 1788400000000
    lines = [_cx_exec(f"t{i}", "fail_task", 1, "partial", t0 + i * 2000,
                      t0 + i * 2000 + 1000, truncated=True) for i in range(6)]
    session = _write_cx_rollout(tmp_path, lines)
    records = adapters.CodexAdapter().read_commands(str(session))
    events = _records_to_events(records)
    last = (t0 + 5 * 2000 + 1000) // 1000
    verdict, _ = detect_mod.detect(events, now=last + 5)
    assert verdict != "SPIN"


# ---- BDD-21: 守护测试（非红灯）——检测引擎阈值常量零改动 ----


def test_bdd_21_detect_thresholds_unchanged(agate_scripts):
    """BDD-21 守护（当前绿）：Codex 三态试验用 RM-AG0055 §3.4.3 既有阈值常量，不新造。
    P4 若改这些常量本测试转红。"""
    mod = _load_detect(agate_scripts)
    assert mod.CALL_ALERT_FALLBACK == 300
    assert mod.CALL_SUSPECT_FALLBACK == 900
    assert mod.ACTIVITY_ALERT == 60
    assert mod.ACTIVITY_SUSPECT == 300
    assert mod.SPIN_THRESHOLD == 5
    assert mod.REPEAT_WINDOW == 10
