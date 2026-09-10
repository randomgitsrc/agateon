# tests/unit/test_tag0034_docs.py — TAG0034 doc-assertion 审计（grep 关键措辞）
#   BDD-41 / BDD-46 / BDD-47 / BDD-48 / BDD-49 / BDD-50 / BDD-52 / BDD-53
#
# 模式：与 agate/tests/unit/test_tag0030_assertions.py 同款「doc-assertion 审计 P3 写红、
#   正文 P4 author 后补绿」（DEBT0039 / TAG0030 先例）。断言的关键串锚定语义短语，
#   不锚定会漂移的整句排版。当前红（措辞未写入）；P4 author 正文后转绿；条文被删即转红。
#
# 平台无关：仅 read_text + `in` / `not in`，无 shell grep、无 /tmp、无裸 python3。

import pytest


def _read(agate_root, rel):
    return agate_root.joinpath(rel).read_text(encoding="utf-8")


def _read_repo(agate_root, rel):
    """仓库根（agate_root.parent）下相对路径——docs/ 与 agate-workspace/ 在仓库根。"""
    return agate_root.parent.joinpath(rel).read_text(encoding="utf-8")


@pytest.mark.windows_smoke
def test_bdd_41_dispatch_protocol_gate_decoupling_and_invariants(agate_root):
    """BDD-41：dispatch-protocol.md 新节含「gate 判定只认产出文件 + exit code，不认谁生产的」
    + 「候选回落 ≠ 状态机 retry」+ 「gate FAIL 绝不换候选」两条完整性不变量 + 「查表 → 派首选 →
    （基础设施失败）逐级回落 → 再派发」步位于铁律 1 之前。"""
    c = _read(agate_root, "dispatch-protocol.md")
    assert "不认谁生产的" in c
    assert "候选回落 ≠ 状态机 retry" in c
    assert "gate FAIL 绝不换候选" in c
    assert "铁律 1" in c


@pytest.mark.windows_smoke
def test_bdd_46_designnote_config_location_and_core_loop_rewritten(agate_root):
    """BDD-46：design-note 头部「做什么」+ §2.1 + §2.2——配置落点不再写
    agate/rules/dispatch-routing.yaml（改三层落点、项目级文件在 agate-workspace/）；
    核心循环不再写「按序探测」（改 try-and-fall）。"""
    c = _read_repo(agate_root, "docs/design-notes/design-dispatch-routing.md")
    assert "try-and-fall" in c
    assert "agate-workspace/dispatch-routing.yaml" in c
    assert "dispatch-tiers.yaml" in c


@pytest.mark.windows_smoke
def test_bdd_47_roadmap_rm_ag0060_old_wording_rewritten(agate_root):
    """BDD-47：roadmap RM-AG0060 长描述——不再含 rules/dispatch-routing.yaml 与「按序探测」
    字样；与 design-note 定案一致（try-and-fall + 两轴 + 项目级落点）。"""
    text = _read_repo(agate_root, "agate-workspace/roadmap/roadmap.md")
    rm_lines = [ln for ln in text.splitlines() if "RM-AG0060" in ln and ln.lstrip().startswith("|")]
    assert rm_lines, "未找到 RM-AG0060 表行"
    line = rm_lines[0]
    assert "按序探测" not in line
    assert "try-and-fall" in line


@pytest.mark.windows_smoke
def test_bdd_48_architect_batch_design_doc_content_is_p4_boundary(agate_root):
    """BDD-48：architect.md「批次设计」节含显式说明「补协议文档正文（platform-notes.md /
    SETUP.md / phase-cards 等）= P4 实现工作，批次执行阶段标 P4；P7 只做跨文件一致性验证、
    不 author 文档内容」。"""
    c = _read(agate_root, "assets/execution-roles/architect.md")
    assert "补协议文档正文" in c
    assert "跨文件一致性验证" in c


@pytest.mark.windows_smoke
def test_bdd_49_dispatch_protocol_author_vs_consistency_boundary(agate_root):
    """BDD-49：dispatch-protocol.md「派发编排机制」节含显式区分「author 文档内容 = P4 /
    跨文件一致性验证 = P7」；节标题「派发编排机制」仍存在。"""
    c = _read(agate_root, "dispatch-protocol.md")
    assert "## 派发编排机制" in c
    assert "author 文档内容" in c
    assert "跨文件一致性验证" in c


def test_bdd_50_consistency_zero_error_after_task_changes(agate_scripts, python_exe, run_cli):
    """BDD-50（回归）：本任务全部改动就位后 `check-protocol-consistency.py --strict-errors-only`
    → exit 0（0 ERROR）。P3 红属预期：BDD-48/49 文档修订未就位 + 既有 P2-design.md ```yaml
    fence 解析 ERROR 待 P4/P7 处理（[P2_DESIGN_YAML_FENCE] 见 P3-progress）。P4/P7 后转绿。"""
    result = run_cli(
        python_exe, str(agate_scripts / "check-protocol-consistency.py"), "--strict-errors-only"
    )
    assert result.returncode == 0


@pytest.mark.windows_smoke
def test_bdd_52_designnote_two_axes_key_and_mitigation_labels(agate_root):
    """BDD-52：design-note 含 tier + effort 两正交轴 + (phase,role) key（role 可选）；
    cli: native 明确标为弱缓解、跨 CLI 起子进程标为强缓解；含「自动化不对称」说明。"""
    c = _read_repo(agate_root, "docs/design-notes/design-dispatch-routing.md")
    assert "正交轴" in c
    assert "(phase,role)" in c
    assert "弱缓解" in c
    assert "强缓解" in c
    assert "自动化不对称" in c


@pytest.mark.windows_smoke
def test_bdd_53_designnote_integrity_invariants_and_per_machine(agate_root):
    """BDD-53：design-note 含「候选回落 ≠ 状态机 retry」与「gate FAIL 绝不换候选」两条完整性
    不变量的显式表述；含「routing 是 per-machine 机会式、不追求跨机可复现（只有抽象
    (phase,role)→档位映射可 commit 共享）」的显式声明。"""
    c = _read_repo(agate_root, "docs/design-notes/design-dispatch-routing.md")
    assert "候选回落 ≠ 状态机 retry" in c
    assert "gate FAIL 绝不换候选" in c
    assert "不追求跨机可复现" in c
