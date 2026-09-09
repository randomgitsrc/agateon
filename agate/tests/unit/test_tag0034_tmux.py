# tests/unit/test_tag0034_tmux.py — TAG0034 tmux 观测层（P4c，不通过不影响 P4a/P4b）
#   BDD-37 / BDD-38
#
# 被测：agate/scripts/agate_dispatch_route.py 的 tmux wrapper helper（importable，P4c 建）
#   - build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name)
#       -> list[str]（tmux 可用 → tmux new-session -d -s <ns> '<cmd> | tee <capture>'；
#          不可用 → 裸 cmd）
#   - tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s)
#       -> str ∈ {"kill_now", "let_countdown", "force_kill", "noop"}
#
# TDD 红灯语义（P3）：agate_dispatch_route 模块尚未实现 → import 在测试体内触发
#   ModuleNotFoundError（项目内模块缺失 = B 类）。
#
# P2-design §3.10 锚（测试据此写预期）：
#   session 名 = agate-{task_id}-{phase}-{短时间戳}（带命名空间）
#   list-clients 为空 → 直接 kill-session（跳倒计时）；非空 → 不强杀、让倒计时收尾
#   wrapper 异常未退出且超过 N + 余量（N 默认 15s、余量 10s）→ 兜底强杀
#   两路径（包裹 / 裸跑）的 dispatch_route 留痕 + gate 结果逐字节一致

import importlib
import sys


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def test_bdd_37_which_tmux_decides_wrap_or_bare(agate_scripts):
    """BDD-37：子进程形式派发，which tmux 成功 → tmux new-session -d -s <命名空间-task-phase-ts>
    '<cmd> | tee <capture>'，capture 文件被脚本 tail；失败 → 直接裸跑子进程。"""
    mod = _mod(agate_scripts)
    base_cmd = ["claude", "-p", "--output-format", "json"]

    wrapped = mod.build_subprocess_launch(
        base_cmd, capture_path="cap/dispatch.log", tmux_available=True,
        session_name="agate-TAG0034-P4-1730000000",
    )
    joined = " ".join(wrapped)
    assert "tmux" in joined and "new-session" in joined
    assert "-s agate-TAG0034-P4-1730000000" in joined
    assert "tee" in joined and "cap/dispatch.log" in joined

    bare = mod.build_subprocess_launch(
        base_cmd, capture_path="cap/dispatch.log", tmux_available=False,
        session_name="agate-TAG0034-P4-1730000000",
    )
    assert "tmux" not in " ".join(bare)
    assert bare[:4] == base_cmd


def test_bdd_38_countdown_and_no_force_kill_with_client(agate_scripts):
    """BDD-38：tmux 包裹的子进程已跑完，wrapper 进入 N 秒退出倒计时（N 默认 ≈15）。
    list-clients 为空 → kill_now；非空（有人 attach）→ 不强杀、让倒计时收尾；
    wrapper 异常未退出且超过 N + 余量（余量 10s）→ 兜底强杀。"""
    mod = _mod(agate_scripts)

    assert mod.tmux_cleanup_action(
        "s", has_clients=False, elapsed_s=1, countdown_n=15, margin_s=10,
    ) == "kill_now"

    assert mod.tmux_cleanup_action(
        "s", has_clients=True, elapsed_s=5, countdown_n=15, margin_s=10,
    ) == "let_countdown"

    # 有人 attach 但 wrapper 异常未退出、已超过 N + 余量（15 + 10 = 25s）→ 兜底强杀
    assert mod.tmux_cleanup_action(
        "s", has_clients=True, elapsed_s=26, countdown_n=15, margin_s=10,
    ) == "force_kill"
