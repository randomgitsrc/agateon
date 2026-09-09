# tests/unit/test_tag0034_p4c.py — TAG0034 tmux 观测层（P4c）新增用例
#   BDD-37 / BDD-38 的断言在 test_tag0034_tmux.py（P3，不改）——本文件是 P4c 的**新增**覆盖：
#     - build_subprocess_launch / tmux_cleanup_action 纯逻辑边界（noop 分支 / 精确边界 /
#       裸路径身份保持 / 倒计时可配）
#     - _maybe_tmux_wrap 默认关 = 逐字节现状；开关 + which tmux 成功才包裹（命名空间 session）
#     - P4b-I1：_default_subprocess_run 透传子进程 stderr 到诊断面、不并入判定文本
#     - P4b-I2：except OSError 仍捕获 FileNotFoundError（其子类）
#     - P4b-I3（部分闭合）：以 _route_main 相同组合（functools.partial + 适配层闭包 + 真
#       append_event 哈希链账本）跑 try_and_fall，断言一次回落落 1 条合法 dispatch_route 事件
#
# CI 不起真 tmux / 真 CLI：shutil.which 与 subprocess.run 全部 mock。

import functools
import importlib
import json
import sys


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


# ───────────────────────── build_subprocess_launch 边界 ─────────────────────────


def test_build_subprocess_launch_bare_preserves_cmd_identity(agate_scripts):
    mod = _mod(agate_scripts)
    cmd = ["codex", "exec", "--json", "ctx.md"]
    out = mod.build_subprocess_launch(
        cmd, capture_path="c.log", tmux_available=False, session_name="s",
    )
    assert out == cmd
    assert out is not cmd  # 返回新 list，不别名调用方的 cmd
    assert "tmux" not in " ".join(out)


def test_build_subprocess_launch_wrap_has_countdown_and_tee(agate_scripts):
    mod = _mod(agate_scripts)
    out = mod.build_subprocess_launch(
        ["claude", "-p"], capture_path="cap/d.log",
        tmux_available=True, session_name="agate-T-P4-42",
    )
    assert out[:5] == ["tmux", "new-session", "-d", "-s", "agate-T-P4-42"]
    shell = out[5]
    assert shell.startswith("claude -p | tee cap/d.log")
    assert "sleep 15" in shell  # wrapper 末尾自带 N 秒退出倒计时（默认 15）


def test_build_subprocess_launch_countdown_configurable(agate_scripts):
    mod = _mod(agate_scripts)
    out = mod.build_subprocess_launch(
        ["x"], capture_path="c", tmux_available=True, session_name="s", countdown_n=30,
    )
    assert "sleep 30" in out[5]


# ───────────────────────── tmux_cleanup_action 边界 ─────────────────────────


def test_tmux_cleanup_action_noop_on_empty_session(agate_scripts):
    mod = _mod(agate_scripts)
    assert mod.tmux_cleanup_action(
        "", has_clients=True, elapsed_s=99, countdown_n=15, margin_s=10,
    ) == "noop"


def test_tmux_cleanup_action_boundary_inclusive(agate_scripts):
    mod = _mod(agate_scripts)
    # elapsed 恰等于 N + margin（25）→ 仍让倒计时收尾（<= 边界）
    assert mod.tmux_cleanup_action(
        "s", has_clients=True, elapsed_s=25, countdown_n=15, margin_s=10,
    ) == "let_countdown"
    # 越过边界一点点 → 兜底强杀
    assert mod.tmux_cleanup_action(
        "s", has_clients=True, elapsed_s=25.001, countdown_n=15, margin_s=10,
    ) == "force_kill"


# ───────────────────────── _maybe_tmux_wrap：默认关 = 现状 ─────────────────────────


def test_maybe_tmux_wrap_default_off_returns_bare(agate_scripts, monkeypatch):
    mod = _mod(agate_scripts)
    monkeypatch.delenv("AGATE_DISPATCH_TMUX", raising=False)
    argv = ["claude", "-p", "ctx.md"]
    launch, cap, sess = mod._maybe_tmux_wrap(argv)
    assert launch == argv
    assert cap is None and sess is None


def test_maybe_tmux_wrap_off_when_tmux_absent(agate_scripts, monkeypatch):
    mod = _mod(agate_scripts)
    monkeypatch.setenv("AGATE_DISPATCH_TMUX", "1")
    monkeypatch.setattr(mod.shutil, "which", lambda _name: None)
    launch, cap, sess = mod._maybe_tmux_wrap(["a", "b"])
    assert launch == ["a", "b"]
    assert cap is None and sess is None


def test_maybe_tmux_wrap_on_wraps_with_namespaced_session(agate_scripts, monkeypatch, tmp_path):
    mod = _mod(agate_scripts)
    monkeypatch.setenv("AGATE_DISPATCH_TMUX", "1")
    monkeypatch.setenv("AGATE_DISPATCH_TASK_ID", "TAG0034")
    monkeypatch.setenv("AGATE_DISPATCH_PHASE", "P4")
    monkeypatch.setenv("AGATE_DISPATCH_CAPTURE", str(tmp_path / "d.log"))
    monkeypatch.setattr(mod.shutil, "which", lambda _name: "/usr/bin/tmux")
    launch, cap, sess = mod._maybe_tmux_wrap(["codex", "exec"])
    assert launch[0] == "tmux" and launch[1] == "new-session"
    assert sess.startswith("agate-TAG0034-P4-")  # 带命名空间（任务-阶段-短时间戳）
    assert cap == str(tmp_path / "d.log")
    assert "codex exec | tee" in launch[5]


# ───────────────────────── _default_subprocess_run：P4b-I1 / I2 ─────────────────────────


class _FakeProc:
    def __init__(self, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def test_default_subprocess_run_forwards_stderr(agate_scripts, monkeypatch, capsys):
    """P4b-I1：只往 stderr 打印的基础设施错误透传到路由脚本 stderr 供人排查。"""
    mod = _mod(agate_scripts)
    monkeypatch.delenv("AGATE_DISPATCH_TMUX", raising=False)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: _FakeProc(stdout='{"stop_reason":"end_turn"}',
                                  stderr="ProviderAuthError: not logged in\n"),
    )
    stdout, rc, killed = mod._default_subprocess_run(["claude", "-p"], timeout_s=5)
    assert stdout == '{"stop_reason":"end_turn"}'
    assert rc == 0 and killed is None
    assert "ProviderAuthError" in capsys.readouterr().err


def test_default_subprocess_run_stderr_not_merged_into_stdout(agate_scripts, monkeypatch):
    """P4b-I1 边界：stderr 仅诊断面透传，**不并入** classify_outcome 的判定文本
    （判定输入与裸跑一致 → R1 完整性不破）。"""
    mod = _mod(agate_scripts)
    monkeypatch.delenv("AGATE_DISPATCH_TMUX", raising=False)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: _FakeProc(stdout="clean stdout", stderr="turn.failed noise"),
    )
    stdout, _rc, _killed = mod._default_subprocess_run(["x"], timeout_s=5)
    assert stdout == "clean stdout"


def test_default_subprocess_run_filenotfound_is_spawn_oserror(agate_scripts, monkeypatch):
    """P4b-I2：`except OSError` 仍捕获 FileNotFoundError（其子类）→ spawn_oserror。"""
    mod = _mod(agate_scripts)
    monkeypatch.delenv("AGATE_DISPATCH_TMUX", raising=False)

    def _boom(*a, **k):
        raise FileNotFoundError("no such binary: claude")

    monkeypatch.setattr("subprocess.run", _boom)
    assert mod._default_subprocess_run(["claude"], timeout_s=5) == ("", None, "spawn_oserror")


# ───────────────────────── P4b-I3：_route_main 组合的桥接端到端 ─────────────────────────


def _fake_once(cand, ctx, *, effort_supported=False, expected_output=None,
               task_dir=None, _outcomes=None):
    return next(_outcomes)


def test_route_bridge_end_to_end_writes_single_dispatch_route_event(agate_scripts, tmp_path):
    """P4b-I3（部分闭合）：以 `_route_main` 相同的组合——`functools.partial` 绑定
    `dispatch_once` 额外 kwargs + 适配层闭包桥接到 kw-only 写入器 + 真 `append_event`
    哈希链账本——跑 `try_and_fall`。mock 子进程候选链（首候选 INFRA_ERROR 回落、次候选
    HAS_OUTPUT），断言：一次回落落 **1 条** 合法 `dispatch_route` 事件、`candidates_tried`
    的 result / reason 正确、`final` == 成功候选。

    完整 `_route_main` 进程级调用（连字符模块名 + 无 dispatch-routing.yaml 恒走
    form=default + 真 CLI spawn）仍留待真机——见 P4-implementation-P4c.md 残留缺口注记。
    """
    mod = _mod(agate_scripts)
    outcomes = iter([
        mod.Outcome("INFRA_ERROR", "infra_error"),
        mod.Outcome("HAS_OUTPUT", None),
    ])
    chain = [
        {"cli": "codex", "model": "gpt-x"},
        {"cli": "opencode", "model": "prov/y"},
    ]
    once = functools.partial(
        _fake_once, effort_supported=False, expected_output=None,
        task_dir=str(tmp_path), _outcomes=outcomes,
    )

    def _write_event(phase_, tried_, final_):
        mod.write_dispatch_route_event(
            str(tmp_path), phase_, tried=tried_, final=final_, task_id="TAG0034",
        )

    result = mod.try_and_fall(
        chain, dispatch_context_path="P4-dispatch-context-implementer.md",
        dispatch_once=once, write_event=_write_event, phase="P4",
    )
    assert result.final == {"cli": "opencode", "model": "prov/y"}

    events = [
        json.loads(ln)
        for ln in (tmp_path / "gate-events.jsonl").read_text(encoding="utf-8").splitlines()
        if ln.strip()
    ]
    routed = [e for e in events if e.get("event") == "dispatch_route"]
    assert len(routed) == 1
    tried = routed[0]["candidates_tried"]
    assert tried[0]["result"] == "failed" and tried[0]["reason"] == "infra_error"
    assert tried[1]["result"] == "success"
    assert routed[0]["final"] == {"cli": "opencode", "model": "prov/y"}
    assert routed[0]["phase"] == "P4"
