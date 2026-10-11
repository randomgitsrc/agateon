# agate/tests/unit/test_tag0051_state_machine.py — TAG0051 P3 红灯（状态机发布授权）
#
# 覆盖 BDD（P1-requirements.md）：18。
#   * BDD-18：`state-machine.md` 显式声明「发布由**独立流程** + **人工授权入口**
#     （当前实现为 `workflow_dispatch`）触发」，且**不引入**第二套与既有 `PAUSED` /
#     NEED_CONFIRM 并行的阻塞确认语义。
#
# 现行为（改动前）：`state-machine.md` 无发布授权说明、无 `workflow_dispatch`
#   ⇒ 断言失败 = B 类红灯。
#
# 平台无关：只读仓库文本 + agate_root fixture；不裸 python3；不写字面系统临时目录。

_SM = "state-machine.md"

# 「发布由独立流程 + 人工授权入口触发」的语义方向标记（方向性断言，不绑定具体句子）。
_AUTH_MARKERS = ("独立流程", "发布授权", "人工授权", "人工触发")
# 不允许出现的「第二套阻塞确认语义」新标记（与既有 PAUSED / NEED_CONFIRM 并行）。
_FORBIDDEN_NEW_MARKERS = ("RELEASE_CONFIRM", "PAUSED_RELEASE", "RELEASE_PAUSED", "RELEASE_NEED_CONFIRM")


def test_bdd_18_state_machine_declares_release_authorization(agate_root):
    """BDD-18：state-machine.md 显式发布授权（独立流程 + workflow_dispatch 人工入口）。"""
    text = (agate_root / _SM).read_text(encoding="utf-8")
    assert "workflow_dispatch" in text, (
        "BDD-18：state-machine.md 未声明发布的人工授权入口 `workflow_dispatch`"
    )
    assert any(m in text for m in _AUTH_MARKERS), (
        "BDD-18：state-machine.md 未显式声明「发布由独立流程 + 人工授权触发」的语义"
    )


def test_bdd_18_state_machine_no_second_blocking_semantics(agate_root):
    """BDD-18：不引入第二套与既有 PAUSED / NEED_CONFIRM 并行的阻塞确认语义。"""
    text = (agate_root / _SM).read_text(encoding="utf-8")
    offenders = [m for m in _FORBIDDEN_NEW_MARKERS if m in text]
    assert not offenders, (
        "BDD-18：state-machine.md 引入了第二套阻塞确认语义标记（应与既有 PAUSED / "
        f"NEED_CONFIRM 复用）：{offenders}"
    )
