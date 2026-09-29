# tests/unit/test_t43_debt0014_store_placeholder.py — DEBT0014 的**源码级**互补守护
#
# ⚠️ **本文件的价值边界（2026-09-29 经独立评审更正，勿高估）**：
# DEBT0014 的**行为级**回归**早已存在**于
# `agate/tests/integration/test_pre_commit_hook.py`——
#   * `test_bdd_10_probe_skips_unexecutable_candidate`（**parametrize 覆盖 3 个 hook**，用
#     `_make_broken_python3_stub`（`#!/bin/sh\nexit 49`）模拟 Store 占位符，断言回退到真实解释器）
#   * `test_bdd_11_agate_python_explicit_override_skips_probe_loop`
# 二者**比本文件更强**（真跑 hook 并断言运行标记）。我初版曾把本文件当"唯一行为锁"，
# 那是错的——错因是 `grep | head -6` 截断了命中（详见 tech-debt.md 的 DEBT0014「方法失误」）。
#
# 故本文件**只保留一个互补判据**：在**源码层**断言 **3 个**薄壳都写了 `-c ""` 形式的
# 逐候选可执行性测试。它与既有行为测试的分工——
#   * 行为测试（既有）：证明「回退逻辑**确实生效**」（端到端，最强）；
#   * 本判据：证明「**3 个**薄壳都改了」（防"只改 pre-commit、漏掉另两个"——行为测试虽也 parametrize
#     3 个 hook，但其失败只会告诉你"某个 hook 回退失败"，本判据直接指出"哪个 shell 没写探测"）。
# 属"低成本冗余"，非独立保障。
#
# 平台无关：纯读文件，不用临时目录。

import stat  # noqa: F401  (保留导入以便将来扩回行为用例时无需改 import 块)

HOOKS = ("pre-commit-gate.sh", "commit-msg-self-gate.sh", "pre-push-gate.sh")


def test_t43_d14_all_three_hook_shells_have_executability_probe(agate_scripts):
    """3 个薄壳**都**须有可执行性小测试（DEBT0014 说的是 3 薄壳，不只 pre-commit）。

    源码级判据（与上面两条行为判据互补）：断言每个薄壳的探测循环里有 `-c ""` 形式的
    可执行性测试调用，而非仅 `command -v`。
    """
    missing = []
    for name in HOOKS:
        text = (agate_scripts / name).read_text(encoding="utf-8")
        has_probe = '-c ""' in text or "-c ''" in text
        has_cmdv = "command -v" in text
        if not (has_probe and has_cmdv):
            missing.append(f"{name}(probe={has_probe}, command_v={has_cmdv})")
    assert missing == [], (
        "以下薄壳缺「逐候选可执行性小测试」（只靠 command -v 会选中 Store 占位符，DEBT0014）："
        + ", ".join(missing)
    )
