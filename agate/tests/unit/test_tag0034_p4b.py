# tests/unit/test_tag0034_p4b.py — TAG0034 P4b 批新增用例
#   M5 dispatch_once 端到端 / I1 try_and_fall 白名单化 / I2 presence-parse 落 produced_files 侧
#   / I3 write_event 签名桥接 / I5 reason 自校 / BDD-42 routed_away_verdict_location
#
# 不改 P3 既有断言（test_tag0034_{tryfall,subprocess,...}.py）——本文件是 P4b 的**新增**覆盖。
#
# 被测：agate/scripts/agate_dispatch_route.py（P4b 追加：dispatch_once / presence_parse_ok
#   / routed_away_verdict_location / DispatchContractError；try_and_fall 白名单化 + reason 自校）
#
# CI 不真调 CLI：dispatch_once 的子进程 spawn 全部注入 mock `run`（喂结构化输出样本 /
#   fixture），不起 claude/codex/opencode 真进程。

import importlib
import sys

import pytest

_CC = "tag0034_claude_code"
_CX = "tag0034_codex"
_OC = "tag0034_opencode"


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def _fx(agate_root, *parts):
    return (agate_root / "tests" / "fixtures").joinpath(*parts).read_text(encoding="utf-8")


def _fake_run(stdout="", exit_code=0, killed_reason=None):
    def _run(argv, *, timeout_s=None):  # 签名匹配 _default_subprocess_run
        return stdout, exit_code, killed_reason
    return _run


# ───────────────────────── M5：dispatch_once 端到端 ─────────────────────────


def test_dispatch_once_native_is_has_output_placeholder(agate_scripts):
    """native / default / 未知 cli → 路由脚本不 spawn，返回 HAS_OUTPUT 占位（驱动会话代发）。
    `run` 不应被调用。"""
    mod = _mod(agate_scripts)
    sentinel = {"called": False}

    def _boom(argv, *, timeout_s=None):
        sentinel["called"] = True
        raise AssertionError("native 不应 spawn 子进程")

    for cli in ("native", "default", "something-unknown", None):
        o = mod.dispatch_once({"cli": cli, "model": "m"}, "P4-dispatch-context-x.md",
                              run=_boom)
        assert o.kind == "HAS_OUTPUT"
        assert o.reason is None
    assert sentinel["called"] is False


def test_dispatch_once_codex_turn_completed_with_produced_file_has_output(agate_scripts, agate_root, tmp_path):
    """codex 子进程：turn.completed 结构化输出 + 约定产出文件 presence-parse 通过 → HAS_OUTPUT。"""
    mod = _mod(agate_scripts)
    art = tmp_path / "P4-implementation.md"
    art.write_text("---\nagent: implementer\n---\n\n## 改动清单\n内容\n", encoding="utf-8")
    o = mod.dispatch_once(
        {"cli": "codex", "model": "gpt-5.6-terra"}, "P4-dispatch-context-x.md",
        expected_output=str(art), required_anchors=["## 改动清单"],
        run=_fake_run(stdout=_fx(agate_root, _CX, "turn_completed_ok.jsonl"), exit_code=0),
    )
    assert o.kind == "HAS_OUTPUT"
    assert o.reason is None


def test_dispatch_once_opencode_provider_auth_error_infra(agate_scripts, agate_root, tmp_path):
    """opencode 子进程：ProviderAuthError 结构化输出 → INFRA_ERROR（即便约定产出文件缺失）。"""
    mod = _mod(agate_scripts)
    o = mod.dispatch_once(
        {"cli": "opencode", "model": "x/y"}, "P4-dispatch-context-x.md",
        expected_output=str(tmp_path / "missing.md"),
        run=_fake_run(stdout=_fx(agate_root, _OC, "provider_auth_error.jsonl"), exit_code=1),
    )
    assert o.kind == "INFRA_ERROR"
    assert o.reason == "infra_error"


def test_dispatch_once_empty_return_no_parseable_output(agate_scripts, agate_root, tmp_path):
    """opencode 纯空返回 + 无约定产出文件 → NO_PARSEABLE_OUTPUT。"""
    mod = _mod(agate_scripts)
    o = mod.dispatch_once(
        {"cli": "opencode", "model": "x/y"}, "P4-dispatch-context-x.md",
        expected_output=str(tmp_path / "missing.md"),
        run=_fake_run(stdout=_fx(agate_root, _OC, "empty_return.jsonl"), exit_code=0),
    )
    assert o.kind == "NO_PARSEABLE_OUTPUT"
    assert o.reason == "no_parseable_output"


def test_dispatch_once_spawn_oserror_launch_fail(agate_scripts):
    """子进程 spawn OSError（run 报 killed_reason=spawn_oserror）→ LAUNCH_FAIL。"""
    mod = _mod(agate_scripts)
    o = mod.dispatch_once(
        {"cli": "codex", "model": "m"}, "P4-dispatch-context-x.md",
        run=_fake_run(stdout="", exit_code=None, killed_reason="spawn_oserror"),
    )
    assert o.kind == "LAUNCH_FAIL"
    assert o.reason == "launch_fail"


def test_dispatch_once_wait_timeout_infra_error(agate_scripts):
    """子进程挂死被杀（run 报 killed_reason=wait_timeout）→ INFRA_ERROR（N6）。"""
    mod = _mod(agate_scripts)
    o = mod.dispatch_once(
        {"cli": "claude-code", "model": "m"}, "P4-dispatch-context-x.md",
        run=_fake_run(stdout="", exit_code=None, killed_reason="wait_timeout"),
    )
    assert o.kind == "INFRA_ERROR"
    assert o.reason == "infra_error"


# ───────────────────────── I2：presence-parse 落 produced_files 侧 ─────────────────────────


def test_presence_parse_ok_variants(agate_scripts, tmp_path):
    mod = _mod(agate_scripts)
    missing = tmp_path / "nope.md"
    assert mod.presence_parse_ok(str(missing)) is False

    empty = tmp_path / "empty.md"
    empty.write_text("   \n", encoding="utf-8")
    assert mod.presence_parse_ok(str(empty)) is False

    unclosed = tmp_path / "unclosed.md"
    unclosed.write_text("---\nagent: x\n\n## 标题\n正文\n", encoding="utf-8")
    assert mod.presence_parse_ok(str(unclosed)) is False  # frontmatter 未闭合

    ok = tmp_path / "ok.md"
    ok.write_text("---\nagent: x\n---\n\n## 改动清单\n正文\n", encoding="utf-8")
    assert mod.presence_parse_ok(str(ok)) is True
    assert mod.presence_parse_ok(str(ok), required_anchors=["## 改动清单"]) is True
    assert mod.presence_parse_ok(str(ok), required_anchors=["## 缺席锚点"]) is False

    no_fm = tmp_path / "nofm.md"
    no_fm.write_text("# 纯正文无 frontmatter\n内容\n", encoding="utf-8")
    assert mod.presence_parse_ok(str(no_fm)) is True


def test_dispatch_once_i2_empty_produced_file_is_no_parseable_output(agate_scripts, tmp_path):
    """约定产出文件存在但为空 → presence-parse 不过 → produced_files 空 → NO_PARSEABLE_OUTPUT。
    结构完整度判断落在 produced_files 填充处，不在 classify_outcome。"""
    mod = _mod(agate_scripts)
    art = tmp_path / "P4-implementation.md"
    art.write_text("", encoding="utf-8")
    o = mod.dispatch_once(
        {"cli": "codex", "model": "m"}, "P4-dispatch-context-x.md",
        expected_output=str(art),
        run=_fake_run(stdout="turn.completed", exit_code=0),
    )
    assert o.kind == "NO_PARSEABLE_OUTPUT"


def test_classify_outcome_no_parseable_branch_has_no_structure_check(agate_scripts):
    """R1 / I2：classify_outcome 的 NO_PARSEABLE_OUTPUT 分支不含结构完整度判断——
    produced_files 一旦非空（哪怕内容是垃圾），即 HAS_OUTPUT、交 gate、不回落。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "claude-code", stdout="任意非结构化文本、无 frontmatter、无锚点",
        exit_code=0, produced_files=["junk-but-nonempty.md"],
    )
    assert o.kind == "HAS_OUTPUT"
    assert o.reason is None


# ───────────────────────── I1：try_and_fall 白名单化 ─────────────────────────


def test_try_and_fall_raises_on_non_contract_kind(agate_scripts):
    """I1：dispatch_once 返回白名单外的「非 HAS_OUTPUT」kind → DispatchContractError
    （契约违例大声失败，不静默当回落信号换候选）。"""
    mod = _mod(agate_scripts)

    def _bogus(cand, ctx):
        return mod.Outcome("SURPRISE_KIND", "weird")

    with pytest.raises(mod.DispatchContractError):
        mod.try_and_fall(
            [{"cli": "codex", "model": "A"}, {"cli": "opencode", "model": "B"}],
            dispatch_context_path="P2-dispatch-context-architect.md",
            dispatch_once=_bogus, write_event=lambda *a, **k: None,
        )


def test_try_and_fall_raises_on_none_kind(agate_scripts):
    """I1：dispatch_once 返回无 .kind 的对象 → DispatchContractError。"""
    mod = _mod(agate_scripts)

    class _Nothing:
        pass

    with pytest.raises(mod.DispatchContractError):
        mod.try_and_fall(
            [{"cli": "codex", "model": "A"}],
            dispatch_context_path="P2-dispatch-context-architect.md",
            dispatch_once=lambda c, p: _Nothing(), write_event=lambda *a, **k: None,
        )


def test_try_and_fall_i5_raises_on_bad_reason_for_fallback_kind(agate_scripts):
    """I5：回落 kind（白名单内）携带非法 reason（不在 _VALID_REASONS）→ 写事件前自校失败
    → DispatchContractError。"""
    mod = _mod(agate_scripts)

    def _bad_reason(cand, ctx):
        return mod.Outcome("INFRA_ERROR", "gate_fail")  # 非法 reason

    with pytest.raises(mod.DispatchContractError):
        mod.try_and_fall(
            [{"cli": "codex", "model": "A"}],
            dispatch_context_path="P2-dispatch-context-architect.md",
            dispatch_once=_bad_reason, write_event=lambda *a, **k: None,
        )


def test_try_and_fall_whitelist_still_falls_back_on_three_infra_kinds(agate_scripts):
    """I1 加固不误伤：三类基础设施 kind 仍正常回落 → 全落空 → default。"""
    mod = _mod(agate_scripts)
    seq = iter(["LAUNCH_FAIL", "INFRA_ERROR", "NO_PARSEABLE_OUTPUT"])
    reasons = {"LAUNCH_FAIL": "launch_fail", "INFRA_ERROR": "infra_error",
               "NO_PARSEABLE_OUTPUT": "no_parseable_output"}

    def _once(cand, ctx):
        k = next(seq)
        return mod.Outcome(k, reasons[k])

    events = []
    res = mod.try_and_fall(
        [{"cli": "codex"}, {"cli": "opencode"}, {"cli": "claude-code"}],
        dispatch_context_path="P2-dispatch-context-architect.md",
        dispatch_once=_once,
        write_event=lambda phase, tried, final: events.append((tried, final)),
    )
    assert res.final == {"cli": "default"}
    assert [t["reason"] for t in res.tried] == ["launch_fail", "infra_error", "no_parseable_output"]
    assert len(events) == 1


# ───────────────────────── I3：write_event 位置回调 ↔ kw-only 写入器桥接 ─────────────────────────


def test_i3_write_event_adapter_bridges_positional_to_kwonly(agate_scripts, task_dir):
    """I3：try_and_fall 以 write_event(phase, tried, final) 位置参数回调；
    write_dispatch_route_event(task_dir, phase, *, tried, final, task_id) 为 kw-only。
    适配层闭包桥接后，一次回落的派发落 1 条合法 dispatch_route 事件。"""
    mod = _mod(agate_scripts)
    import json

    td = task_dir()

    def _write_event(phase_, tried_, final_):
        mod.write_dispatch_route_event(
            str(td), phase_, tried=tried_, final=final_, task_id="TAG0034",
        )

    seq = iter(["INFRA_ERROR", None])

    def _once(cand, ctx):
        k = next(seq)
        if k is None:
            return mod.Outcome("HAS_OUTPUT", None)
        return mod.Outcome(k, "infra_error")

    res = mod.try_and_fall(
        [{"cli": "codex", "model": "A"}, {"cli": "claude-code", "model": "B"}],
        dispatch_context_path="P4-dispatch-context-implementer.md",
        dispatch_once=_once, write_event=_write_event, phase="P4",
    )
    assert res.final == {"cli": "claude-code", "model": "B"}
    lines = (td / "gate-events.jsonl").read_text(encoding="utf-8").splitlines()
    routes = [json.loads(x) for x in lines if x.strip() and json.loads(x).get("event") == "dispatch_route"]
    assert len(routes) == 1
    ev = routes[0]
    assert ev["phase"] == "P4"
    assert ev["final"] == {"cli": "claude-code", "model": "B"}
    assert [c.get("reason") for c in ev["candidates_tried"] if c.get("result") == "failed"] == ["infra_error"]


# ── SELF-GATE alignment A1：classify_outcome per-CLI 信号细分对齐 P2-design §3.7 / M10 ──


def test_classify_claude_code_api_error_is_infra_error(agate_scripts, agate_root):
    """§3.7 Claude Code INFRA_ERROR 行含「API error status」——夹具 api_error.json
    （stop_reason:"error" + api_error_status:401 + is_error:true），exit_code 传 0
    仍须判 INFRA_ERROR（此前无对应信号 → 误落 NO_PARSEABLE_OUTPUT）。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "claude-code", stdout=_fx(agate_root, _CC, "api_error.json"),
        exit_code=0, produced_files=[],
    )
    assert o.kind == "INFRA_ERROR"
    assert o.reason == "infra_error"


def test_classify_opencode_unknown_error_is_no_parseable_output(agate_scripts, agate_root):
    """§3.7 OpenCode NO_PARSEABLE_OUTPUT 行含「{"type":"error","name":"UnknownError"}」
    （MV6b）——夹具 unknown_error.jsonl，exit_code=1 仍须判 NO_PARSEABLE_OUTPUT
    （裸 type:error 不再对 opencode 生效；此前误落 INFRA_ERROR）。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "opencode", stdout=_fx(agate_root, _OC, "unknown_error.jsonl"),
        exit_code=1, produced_files=[],
    )
    assert o.kind == "NO_PARSEABLE_OUTPUT"
    assert o.reason == "no_parseable_output"


def test_classify_codex_bare_top_error_still_infra_error(agate_scripts):
    """守 Codex 不回归：裸顶层 {"type":"error","status":400}（MV3）对 cli=="codex"
    仍判 INFRA_ERROR（不依赖退出码——此处 exit_code=0）。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "codex",
        stdout='{"type":"error","status":400,"error":{"message":"model not supported"}}',
        exit_code=0, produced_files=[],
    )
    assert o.kind == "INFRA_ERROR"
    assert o.reason == "infra_error"


# ───────────────────────── BDD-42：routed_away_verdict_location ─────────────────────────


def test_routed_away_verdict_location_always_task_dir(agate_scripts):
    mod = _mod(agate_scripts)
    for cli in ("codex", "opencode", "claude-code", "native", "default"):
        assert mod.routed_away_verdict_location(cli) == "TASK_DIR"
