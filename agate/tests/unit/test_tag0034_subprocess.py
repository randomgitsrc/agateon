# tests/unit/test_tag0034_subprocess.py — TAG0034 跨 CLI 子进程 spawn + 结构化输出解析
#   BDD-33 / BDD-34 / BDD-35 / BDD-36 + BDD-42
#
# 被测：agate/scripts/agate_dispatch_route.py 的 classify_outcome(...)（importable helper，P4b 建）
#   fixture = P2 §5 真机样本收敛（scratchpad mv/ 复制到 committed 夹具）：
#     agate/tests/fixtures/tag0034_claude_code/{ok_end_turn,empty_result,api_error}.json
#     agate/tests/fixtures/tag0034_codex/{turn_completed_ok,turn_failed_exit0,item_failed_turn_completed}.jsonl
#     agate/tests/fixtures/tag0034_opencode/{step_finish_stop_ok,provider_auth_error,unknown_error,empty_return}.jsonl
#   fixture 是静态样本文件，CI 不真调 CLI。
#
# TDD 红灯语义（P3）：agate_dispatch_route 模块尚未实现 → import 在测试体内触发
#   ModuleNotFoundError（项目内模块缺失 = B 类）。
#
# P2-design §3.7 判定表锚：
#   Claude Code：stop_reason=="end_turn" + result 非空 + 产出文件非空骨架可解析 → HAS_OUTPUT
#   Codex：turn.completed 且无 turn.failed / 无顶层 error → HAS_OUTPUT（退出码不可靠、以事件流为准）
#          item 级 status:"failed" 永不触发回落（turn 层为准，BDD-35）
#   OpenCode：step_finish 且 part.reason=="stop" + 有 text part → HAS_OUTPUT
#            ProviderAuthError → infra_error；纯空返回 → no_parseable_output

import importlib
import sys

import pytest

_FX = "fixtures"


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def _fx(agate_root, *parts):
    return (agate_root / "tests" / "fixtures").joinpath(*parts).read_text(encoding="utf-8")


def test_bdd_33_claude_code_json_output_parsed_for_success(agate_scripts, agate_root):
    """BDD-33：spawn claude -p --output-format json，用 stop_reason == "end_turn" 判正常结束、
    modelUsage 确认实际 model；stop_reason 非 end_turn 或输出为空 → 判失败进回落。"""
    mod = _mod(agate_scripts)
    ok = mod.classify_outcome(
        "claude-code",
        stdout=_fx(agate_root, "tag0034_claude_code", "ok_end_turn.json"),
        exit_code=0, produced_files=["P2-design.md"],
    )
    assert ok.kind == "HAS_OUTPUT"

    empty = mod.classify_outcome(
        "claude-code",
        stdout=_fx(agate_root, "tag0034_claude_code", "empty_result.json"),
        exit_code=0, produced_files=[],
    )
    assert empty.kind == "NO_PARSEABLE_OUTPUT"
    assert empty.reason == "no_parseable_output"


def test_bdd_34_codex_success_judged_by_event_stream_not_exit_code(agate_scripts, agate_root):
    """BDD-34：构造「进程 exit 0 但实际失败」样本（不支持的 model → turn.failed{status:400}）→
    依据 turn.completed vs turn.failed 判成败（不依据退出码）；该样本被正确判为失败并进回落。"""
    mod = _mod(agate_scripts)
    # turn_failed 样本：即便传 exit_code=0 也须判 INFRA_ERROR
    o = mod.classify_outcome(
        "codex",
        stdout=_fx(agate_root, "tag0034_codex", "turn_failed_exit0.jsonl"),
        exit_code=0, produced_files=[],
    )
    assert o.kind == "INFRA_ERROR"
    assert o.reason == "infra_error"

    ok = mod.classify_outcome(
        "codex",
        stdout=_fx(agate_root, "tag0034_codex", "turn_completed_ok.jsonl"),
        exit_code=0, produced_files=["P2-design.md"],
    )
    assert ok.kind == "HAS_OUTPUT"


def test_bdd_35_codex_item_status_failed_vs_turn_failed_two_layers(agate_scripts, agate_root):
    """BDD-35：某 payload.item.status == "failed"（携 exit_code）但该 turn 整体 turn.completed →
    按 P2 定死的 turn 层判定；构造样本已知正确 verdict = 「该 turn 整体成功」——解析结论须等于该
    verdict（不因某 item status:failed 就换候选、也不误判整条 turn 为失败）。"""
    mod = _mod(agate_scripts)
    o = mod.classify_outcome(
        "codex",
        stdout=_fx(agate_root, "tag0034_codex", "item_failed_turn_completed.jsonl"),
        exit_code=0, produced_files=["P2-design.md"],
    )
    assert o.kind == "HAS_OUTPUT"
    assert o.reason is None


def test_bdd_36_opencode_step_finish_and_empty_return(agate_scripts, agate_root):
    """BDD-36：用 step_finish.part.reason == "stop" 判正常；空返回（无 text part / 结构化 Error JSON）
    被判失败并进回落。ProviderAuthError → infra_error；纯空返回 → no_parseable_output。"""
    mod = _mod(agate_scripts)
    ok = mod.classify_outcome(
        "opencode",
        stdout=_fx(agate_root, "tag0034_opencode", "step_finish_stop_ok.jsonl"),
        exit_code=0, produced_files=["P2-design.md"],
    )
    assert ok.kind == "HAS_OUTPUT"

    auth = mod.classify_outcome(
        "opencode",
        stdout=_fx(agate_root, "tag0034_opencode", "provider_auth_error.jsonl"),
        exit_code=1, produced_files=[],
    )
    assert auth.kind == "INFRA_ERROR"
    assert auth.reason == "infra_error"

    empty = mod.classify_outcome(
        "opencode",
        stdout=_fx(agate_root, "tag0034_opencode", "empty_return.jsonl"),
        exit_code=0, produced_files=[],
    )
    assert empty.kind == "NO_PARSEABLE_OUTPUT"
    assert empty.reason == "no_parseable_output"


@pytest.mark.windows_smoke
def test_bdd_42_routed_away_judge_verdict_platform_independent(agate_scripts, agate_root):
    """BDD-42：P6.5 judge 被路由到 codex/opencode 子进程，verdict + 证据写入 TASK_DIR →
    check-gate.py P6.5 平台无关通过（两校验器纯 TASK_DIR 文件解析、不读平台 transcript）。
    断言 (a) 回归护栏：check-judge-verdict.py / check-p6-provenance.py 源码不含平台 transcript
    路径（~/.codex/sessions / ~/.claude）——本任务零改动这两个脚本；
    (b) 功能红：agate_dispatch_route 声明 routed-away judge 的 verdict 落点 = TASK_DIR。"""
    for name in ("check-judge-verdict.py", "check-p6-provenance.py"):
        src = (agate_scripts / name).read_text(encoding="utf-8")
        assert ".codex/sessions" not in src
        assert ".claude/projects" not in src
    mod = _mod(agate_scripts)
    assert mod.routed_away_verdict_location("codex") == "TASK_DIR"
