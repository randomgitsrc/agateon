# tests/unit/test_t43_check_registration_surface.py — DEBT0046（RM-AG0068 另一半）
# 被测：新增 `agate/scripts/check-*.py` 的「登记面」是否有权威清单，且清单是否与真实
#       gate 行为一致（而不是靠 P1/P2 同类扫描凭推理回忆）。
#
# 背景（DEBT0046 原文）：凡是新增 check 脚本的任务都会踩同一坑——协议没有「新增脚本要同步
#   哪些登记面」的权威清单（原文点名 7 处：脚本 README、tests README 计数、CHANGELOG、
#   CONTEXT、CHECK 9 锚点/豁免、CHECK 10 引用、SG.6），只能靠同类扫描人工回忆。
#
# ⚠️ 本测试的设计前提是**实测复核**（2026-09-29 用探针脚本 check-zzprobe.py 实跑），
#   实测结论与原文点名的 7 处有出入——原文把「约定」与「机械门禁」混为一谈：
#     ① SG.6（integration/test_protocol_alignment_review.py）——**真门禁**，会红；
#        但它当时的断言 `name in consistency_text` 是**子串判定**，与它自称的
#        「锚点表覆盖」不等价：在 check-protocol-consistency.py 里写一行**注释**提及
#        脚本名即可让 SG.6 变绿，而 CHECK9-coverage 仍告警 ⇒ 两处判据互相矛盾（实测复现）。
#     ② CHECK9-coverage（check-protocol-consistency.py）——**真门禁**，但仅 WARNING；
#        满足方式有**两种**（进 SCRIPT_ALIGNMENT_ANCHORS 锚点表 / 进 GATE_SCRIPT_EXEMPT
#        豁免集），原文的告警文案只说了前者 ⇒ 按文案照做会对「观测型脚本」产生误配。
#     ③ CHECK 10（check_script_name_refs）——**方向相反，不是登记面**：它只报「协议文档
#        引用了不存在的脚本」，新增脚本文件本身**不会**触发它（不加引用即可）。原文列举
#        有误。改名/退役才会踩。
#     ④ scripts/README.md 脚本索引——**非机械门禁**：实测当前 7 个 check-*.py 无索引行
#        （check-events / check-judge-verdict / check-yaml-schema / check-maintainability /
#        check-structure-consistency / check-dispatch-routing / check-protocol-consistency）
#        而全量 pytest + consistency 全绿 ⇒ 它是**约定**，不是门禁。
#     ⑤ tests/README 用例计数——**不是登记面**：count-tests.sh 是**下界**语义
#        （「目标：≥ 749」），新增测试只会抬高数字，永不因新增脚本转红。
#     ⑥ CHANGELOG / CONTEXT——无「每个脚本一行」的机械校验（CHANGELOG 只校验
#        [Unreleased] 含 task_id），属任务级约定。
#
# 故本测试锚定**可机械判定的那一部分**，并把「实测而非推理」写成断言：
#   - 真门禁的**唯一不变量** = 每个 gate 脚本 ∈ (锚点表 ∪ 豁免集)，且该不变量由
#     **单一函数** `uncovered_gate_scripts()` 表达，供 gate（check_anchor_coverage）
#     与测试（SG.6 / 本文件）**共用同一判据** ⇒ 从结构上消灭「测试与 gate 判据不一致」
#     这一实测发现的空洞。
#   - 权威清单落盘在 agate/scripts/README.md（原文 recommendation 的第二条路），
#     且必须**写明哪几条是门禁、哪几条只是约定**（否则清单会像原文一样误导）。
#   - P1 同类扫描 / P2 影响面梳理 / architect.md 要求「对既有测试是否被新增文件触发」
#     做**实测**（原文 closure_criteria 第 2 条）。
#
# 平台无关：纯文本读取 + importlib 加载被测模块；不硬编码单平台路径，不使用临时目录字面量。

import importlib.util
import os
from pathlib import Path

import pytest

# ── 权威清单位置（唯一权威源；本测试据此断言，不另立第二份清单） ──
SCRIPTS_README_REL = "agate/scripts/README.md"


def _repo_root(agate_root: Path) -> Path:
    """agate_root 是 <仓库根>/agate ⇒ 上溯一层得仓库根。"""
    return Path(agate_root).parent


def _read(agate_root: Path, rel: str) -> str:
    return (_repo_root(agate_root) / rel).read_text(encoding="utf-8")


def _load_cpc(agate_scripts: Path):
    path = os.path.join(str(agate_scripts), "check-protocol-consistency.py")
    spec = importlib.util.spec_from_file_location("cpc_t43", path)
    cpc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cpc)
    return cpc


# ---------------------------------------------------------------------------
# 1. 单一判据函数存在（消灭「测试与 gate 判据不一致」的结构性空洞）
# ---------------------------------------------------------------------------


def test_t43_1_uncovered_gate_scripts_helper_exists(agate_scripts):
    """check-protocol-consistency.py 暴露 uncovered_gate_scripts(root)，供 gate 与测试共用同一判据。

    实测背景：SG.6 用子串判定、check_anchor_coverage 用集合判定，两者可同时给出相反结论
    （注释提及即满足前者、仍触发后者）。修法是让两者共用同一个函数，而不是各写一份。
    """
    cpc = _load_cpc(agate_scripts)
    assert hasattr(cpc, "uncovered_gate_scripts"), (
        "check-protocol-consistency.py 缺 uncovered_gate_scripts()：gate 与测试各写一份判据"
        "会再次产生「SG.6 绿而 CHECK9-coverage 告警」的矛盾"
    )
    assert callable(cpc.uncovered_gate_scripts)


def test_t43_2_real_repo_zero_uncovered_gate_scripts(agate_root, agate_scripts, tmp_path):
    """不变量：仓库现存的每个 gate 脚本都已在锚点表或豁免集中（实测应为空）。

    ⚠️ 独立评审指出（2026-09-29）：本用例单独看是**真空型**——把判据改成永远返回 `[]`
    它照样通过，与我在 SG.6 里修掉的正是同一模式。故此处先做**非真空自证**：
    在同构合成树上确认判据**确实能报出**未登记脚本，再对真实仓库断空。
    """
    cpc = _load_cpc(agate_scripts)

    # —— 非真空自证：判据必须能报出未登记脚本（否则下面的 == [] 毫无意义）——
    probe_root = Path(tmp_path)
    (probe_root / "agate" / "scripts").mkdir(parents=True)
    (probe_root / "agate" / "scripts" / "check-t43probe.py").write_text("# probe\n", encoding="utf-8")
    assert "agate/scripts/check-t43probe.py" in cpc.uncovered_gate_scripts(probe_root), (
        "判据被架空（对未登记脚本返回空）——本用例的 == [] 断言即真空"
    )

    uncovered = cpc.uncovered_gate_scripts(_repo_root(agate_root))
    assert uncovered == [], (
        f"以下 gate 脚本既不在 SCRIPT_ALIGNMENT_ANCHORS 也不在 GATE_SCRIPT_EXEMPT：{uncovered}"
    )


def test_t43_3_new_gate_script_is_reported_uncovered(agate_scripts, tmp_path):
    """负向：合成树上放一个未登记的新 check 脚本 → 必须被报为未覆盖（判据不真空）。"""
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    (root / "agate" / "scripts").mkdir(parents=True)
    (root / "agate" / "scripts" / "check-newgate.py").write_text("# synthetic\n", encoding="utf-8")

    uncovered = cpc.uncovered_gate_scripts(root)
    assert "agate/scripts/check-newgate.py" in uncovered, (
        "未登记的新 check 脚本未被 uncovered_gate_scripts 报出——判据真空，无法拦截 DEBT0046 场景"
    )


def test_t43_4_comment_mention_alone_is_not_coverage(agate_scripts, tmp_path):
    """注释里提及脚本名不构成「已登记」——把该形态固化为回归判据。

    ⚠️ 范围声明（独立评审指出后收窄，2026-09-29）：本用例**不执行**旧版 SG.6 的断言，
    因此它**不证明**「旧子串判据会被注释骗过」。旧判据已被改掉、无法在测试内复现，
    当时的复现证据是**一次性探针实测**（见 DEBT0046 closure_note）。
    本用例只做一件事：确认当前判据 `uncovered_gate_scripts()` 对
    「文本里有该名字、但未进锚点表/豁免集」的脚本判为**未覆盖**（即不退回子串语义）。
    """
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    scripts = root / "agate" / "scripts"
    scripts.mkdir(parents=True)
    # 合成一致性脚本：正文**只有注释提及** check-t43probe.py（即实测中骗过旧 SG.6 的形态）
    consistency_text = (
        "# mention: check-t43probe.py\nSCRIPT_ALIGNMENT_ANCHORS = []\nGATE_SCRIPT_EXEMPT = set()\n"
    )
    (scripts / "check-protocol-consistency.py").write_text(consistency_text, encoding="utf-8")
    (scripts / "check-t43probe.py").write_text("# probe\n", encoding="utf-8")

    uncovered = cpc.uncovered_gate_scripts(root)
    assert "agate/scripts/check-t43probe.py" in uncovered, (
        "注释里提及脚本名被当成了「已登记」——判据退回子串语义，SG.6/CHECK9-coverage 会再次互相矛盾"
    )


# ---------------------------------------------------------------------------
# 2. 门禁自身：告警文案必须点名「两种」满足方式（原文只说了一种，会误配）
# ---------------------------------------------------------------------------


def test_t43_5_coverage_warning_names_both_satisfaction_paths(agate_scripts, tmp_path):
    """CHECK9-coverage 的告警文案须同时点名锚点表与豁免集两条路（原文仅前者，会误配）。

    用**实跑**而非正则匹配源码：在合成树上放一个未登记脚本，跑 check_anchor_coverage，
    断言真实产生的告警文案。这样断言的是行为，不是某行文字的写法。
    """
    cpc = _load_cpc(agate_scripts)
    root = Path(tmp_path)
    (root / "agate" / "scripts").mkdir(parents=True)
    (root / "agate" / "scripts" / "check-newgate.py").write_text("# synthetic\n", encoding="utf-8")

    rep = cpc.Report()
    cpc.check_anchor_coverage(root, rep)
    warnings = [w for w in rep.warnings if w["check"] == "CHECK9-coverage"]
    assert len(warnings) == 1, f"预期 1 条未覆盖告警，实得 {len(warnings)}"

    msg = warnings[0]["msg"]
    assert "SCRIPT_ALIGNMENT_ANCHORS" in msg, "告警未点名锚点表这条满足路径"
    assert "GATE_SCRIPT_EXEMPT" in msg, (
        "告警未点名豁免集这条满足路径：观测型脚本按原文只加锚点会误配（实测 DEBT0046 场景二）"
    )
    assert "scripts/README.md" in msg, "告警未指向登记面权威清单（读者仍要凭记忆）"


# ---------------------------------------------------------------------------
# 3. 权威清单落盘：scripts/README.md「登记面」表 + 诚实标注门禁/约定之分
# ---------------------------------------------------------------------------


def test_t43_6_scripts_readme_has_registration_surface_section(agate_root):
    """agate/scripts/README.md 含「新增脚本登记面」权威节与指针。"""
    text = _read(agate_root, SCRIPTS_README_REL)
    assert "登记面" in text, f"{SCRIPTS_README_REL} 缺「登记面」权威清单（DEBT0046 recommendation 第二路）"
    assert "CHECK9-coverage" in text or "CHECK 9" in text, "登记面表未点名 CHECK 9 覆盖门禁"
    assert "SG.6" in text, "登记面表未点名 SG.6（真门禁之一，实测会红）"


def test_t43_7_registration_surface_table_distinguishes_gate_from_convention(agate_root):
    """登记面表必须标出「门禁」与「约定」之分——否则会像 DEBT0046 原文一样误导。

    实测：原文点名的 7 处里只有 2 处是真门禁；③ CHECK 10 方向相反、④ README 行无校验、
    ⑤ 计数是下界、⑥ CHANGELOG/CONTEXT 属任务级约定。
    """
    text = _read(agate_root, SCRIPTS_README_REL)
    for token in ("门禁", "约定"):
        assert token in text, f"{SCRIPTS_README_REL} 登记面表未区分「{token}」"

    # 诚实性：必须写明 CHECK 10 不是「新增脚本」的登记面（方向相反）
    assert "CHECK 10" in text or "CHECK10" in text, "登记面表未提及 CHECK 10 的方向说明"


def test_t43_8_registration_surface_points_at_single_judgement_function(agate_root):
    """登记面表须指向单一判据函数，避免读者另写一份记忆版清单。"""
    text = _read(agate_root, SCRIPTS_README_REL)
    assert "uncovered_gate_scripts" in text, (
        f"{SCRIPTS_README_REL} 登记面表未指向 uncovered_gate_scripts（单一判据函数）"
    )


# ---------------------------------------------------------------------------
# 4. 流程侧：P1 同类扫描 / P2 影响面梳理 / architect.md 要求「实测」
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rel", ["agate/phase-cards/P1-requirements.md", "agate/phase-cards/P2-design.md"])
def test_t43_9_p1_p2_cards_require_empirical_verification(agate_root, rel):
    """P1 同类扫描 / P2 影响面梳理须要求对「既有测试是否被新增文件触发」做实测，非推理。"""
    text = _read(agate_root, rel)
    assert "实测" in text, f"{rel} 未要求实测（DEBT0046: P1 凭推理判『不处理』，P2 评审实测才发现）"
    assert "登记面" in text, f"{rel} 未指向「登记面」清单"
    assert "scripts/README.md" in text, f"{rel} 未给出登记面权威源的路径指针"


def test_t43_9b_p2_card_names_all_three_closure_criteria_surfaces(agate_root):
    """DEBT0046 的 closure_criteria 第 1 条要求点名 **SG.6 / CHECK 9 / CHECK 10** 三处。

    独立评审指出（2026-09-29）：初版只在 `scripts/README.md` 点名了 CHECK 10，
    而 criterion 指定的位置是「P2 卡**或** architect.md」⇒ 字面未满足。
    本用例把该 criterion 固化为机械判据（P2 卡须三处齐名）。
    """
    text = _read(agate_root, "agate/phase-cards/P2-design.md")
    assert "SG.6" in text, "P2 卡未点名 SG.6（closure_criteria 第 1 条要求三处齐名）"
    assert "CHECK 9" in text or "CHECK9" in text, "P2 卡未点名 CHECK 9"
    assert "CHECK 10" in text or "CHECK10" in text, (
        "P2 卡未点名 CHECK 10（closure_criteria 指定的位置是 P2 卡或 architect.md）"
    )


def test_t43_10_architect_role_points_at_registration_surface(agate_root):
    """architect.md（P2 设计角色文件）须指向登记面清单。"""
    text = _read(agate_root, "agate/assets/execution-roles/architect.md")
    assert "登记面" in text, "architect.md 未提及「登记面」"
    assert "scripts/README.md" in text, "architect.md 未给出登记面权威源路径指针"
