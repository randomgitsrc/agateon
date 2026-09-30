# tests/integration/test_protocol_alignment_review.py — self-gate 机制测试
# （integration/protocol-alignment-review.bats 8 用例迁移，TAG0011 批次 14）
# 被测：agate/assets/review-roles/protocol-alignment-review.md（角色文件）+ 仓库根 SELF-GATE.md
#   + check-protocol-consistency.py 锚点表覆盖 + commit-msg-self-gate.sh 可执行。
# bats `$BATS_TEST_DIRNAME/../../../SELF-GATE.md` = 仓库根 SELF-GATE.md（= agate_root.parent）。
# windows_smoke：SG.1（文件首 @test，P3 §5.2 每文件第 1 用例打标）。

import importlib.util
import os
import re
from pathlib import Path

import pytest


def _role_file(agate_root):
    return agate_root / "assets" / "review-roles" / "protocol-alignment-review.md"


def _selfgate_file(agate_root):
    return agate_root.parent / "SELF-GATE.md"


@pytest.mark.windows_smoke
def test_sg_1_role_file_exists_with_required_frontmatter(agate_root):
    """SG.1：角色文件 protocol-alignment-review.md 存在且含必需 frontmatter。"""
    role_file = _role_file(agate_root)
    assert role_file.is_file()
    text = role_file.read_text(encoding="utf-8")
    assert re.search(r"^role_id: protocol-alignment-review", text, re.MULTILINE)
    assert re.search(r"^type: review", text, re.MULTILINE)
    assert re.search(r"^phases:", text, re.MULTILINE)
    assert re.search(r"^agent:", text, re.MULTILINE)


def test_sg_2_role_file_has_a1_a8_checklist(agate_root):
    """SG.2：角色文件含 A1-A8 审查清单。

    **2026-09-29（RM-AG0094）扩为 A1..A8**：原版只查 A1–A6，而角色文件当时已有 A7 ⇒
    **既有守护本身漏了一项**（实测函数名即 `..._a1_a6_checklist`）。新增 A8 时一并补齐，
    避免「同类守护两套标准」（独立评审建议：不再单开 SG.10）。
    """
    text = _role_file(agate_root).read_text(encoding="utf-8")
    # **断言主清单表的表格行**（2026-09-29 两轮加固）：
    # ① 初版用 `marker in text` → 删掉 A8 整行后**仍绿**（「A1-A8」引用里就含 "A8"）；
    # ② 改为宽匹配 `^\|\s*A<N>\s*\|` 后仍不够——**输出格式汇总表**也有一行 `| A8 | ... |`，
    #    故**只删主清单的 A8 行时依旧绿**（独立评审复现）。⇒ 先切出主清单表区段再逐项断言。
    main = re.search(
        r"^\|\s*#\s*\|\s*审查项\s*\|\s*说明\s*\|.*?(?=\n\n)",
        text, re.MULTILINE | re.DOTALL,
    )
    assert main, "角色文件主清单表（表头含「说明」）结构已变——请同步本测试"
    block = main.group(0)
    for n in range(1, 9):
        marker = f"A{n}"
        assert re.search(rf"^\|\s*{marker}\s*\|", block, re.MULTILINE), (
            f"角色文件**主清单表**缺审查项 {marker}（汇总表里有不算——那会让主清单行悄悄消失）"
        )


def test_sg_2b_a8_mentions_command_binding(agate_root):
    """SG.2b：A8 条文须点名「命令」与「删除」两个要点（防只写个空标题）。

    边界：本条只证明**条文在**，不证明 A8 被执行——后者不可机械化（设计 §3.3）。
    """
    text = _role_file(agate_root).read_text(encoding="utf-8")
    # **必须限定到「主清单表」**（表头含「说明」的那张）——初版用宽匹配 `^\|\s*A8\s*\|`，
    # 实测**只删主清单的 A8 行时它仍绿**：因为输出格式**汇总表**也有一行 `| A8 | ... |`
    # （独立评审 2026-09-29 复现）。故先切出主清单表区段再在其中找 A8 行。
    main = re.search(
        r"^\|\s*#\s*\|\s*审查项\s*\|\s*说明\s*\|.*?(?=\n\n)",
        text, re.MULTILINE | re.DOTALL,
    )
    assert main, "角色文件主清单表（表头含「说明」）结构已变——请同步本测试"
    m = re.search(r"^\|\s*A8\s*\|(.*)$", main.group(0), re.MULTILINE)
    assert m, "主清单表缺 A8 行（A8 = 声称-命令绑定；汇总表里有不算）"
    row = m.group(1)
    assert "命令" in row, "A8 未点名「命令」（核心要求：声称须指向产出它的命令）"
    assert "删除" in row, "A8 未点名「删除」（无法给出命令的声称应删除，而非标注「不可复核」）"


def test_sg_3_role_file_has_needs_human_review_loop(agate_root):
    """SG.3：角色文件含 NEEDS_HUMAN_REVIEW 闭环规则 + HUMAN_CONFIRMED 标记。"""
    text = _role_file(agate_root).read_text(encoding="utf-8")
    assert "NEEDS_HUMAN_REVIEW" in text
    assert "HUMAN_CONFIRMED" in text


def test_sg_4_selfgate_has_dispatch_template(agate_root):
    """SG.4：SELF-GATE.md 含派发模板。"""
    selfgate_file = _selfgate_file(agate_root)
    assert selfgate_file.is_file()
    text = selfgate_file.read_text(encoding="utf-8")
    assert "protocol-alignment-review" in text
    assert "审查清单" in text
    assert "配套文件提示" in text


def test_sg_5_selfgate_has_checklist(agate_root):
    """SG.5：SELF-GATE.md 含检查清单。"""
    selfgate_file = _selfgate_file(agate_root)
    assert selfgate_file.is_file()
    text = selfgate_file.read_text(encoding="utf-8")
    assert "protocol-alignment-review" in text
    # 检查清单引用 check-protocol-consistency 的结构 CHECK 集（不写死上界——CHECK 数会增长）
    assert "check-protocol-consistency.py" in text
    assert "CHECK" in text
    assert "HUMAN_CONFIRMED" in text


def test_sg_6_check9_anchor_table_covers_all_gate_scripts(agate_root, agate_scripts, tmp_path):
    """SG.6：CHECK 9 锚点表覆盖全部 gate 脚本（check-*.py + pre-commit-gate 薄壳）。

    每个 gate 脚本都应已在 CHECK 9 锚点表**或** GATE_SCRIPT_EXEMPT 豁免集中。

    ⚠️ 2026-09-29（DEBT0046）修正判据：旧版断言 `name in consistency_text` 是**子串**判定，
    与本节自称的「锚点表覆盖」不等价——在 check-protocol-consistency.py 里写一行**注释**
    提及脚本名即可让本测试变绿，而 CHECK9-coverage 仍告警（实测复现，两处结论相反）。
    现改为消费被测脚本自己导出的单一判据 `uncovered_gate_scripts()`，与 gate 共用同一函数，
    使「测试绿而 gate 告警」不可能再出现。

    ⚠️ 但「共用同一函数」引入新的**真空风险**（2026-09-29 负向实测发现）：若该函数被改成
    永远返回 `[]`，本测试会**静默变绿**。故先做**非真空自证**——在同构的合成树上确认判据
    确实能报出未登记脚本；判据被架空时本测试与
    `test_t43_3/4/5`（合成树负向）会一起红。
    """
    consistency_script = agate_scripts / "check-protocol-consistency.py"
    assert consistency_script.is_file()
    spec = importlib.util.spec_from_file_location("cpc_sg6", consistency_script)
    cpc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cpc)
    assert hasattr(cpc, "uncovered_gate_scripts"), (
        "check-protocol-consistency.py 缺 uncovered_gate_scripts()——SG.6 与 CHECK9-coverage "
        "须共用同一判据，否则会再出现「本测试绿而 gate 告警」的矛盾（DEBT0046 实测）"
    )

    # —— 非真空自证：同构合成树上，未登记的 check-*.py 必须被判据报出 ——
    probe_root = Path(tmp_path)
    (probe_root / "agate" / "scripts").mkdir(parents=True)
    (probe_root / "agate" / "scripts" / "check-sg6probe.py").write_text("# probe\n", encoding="utf-8")
    assert "agate/scripts/check-sg6probe.py" in cpc.uncovered_gate_scripts(probe_root), (
        "uncovered_gate_scripts 对未登记脚本返回了空——判据被架空（真空），SG.6 本身就失去意义"
    )

    uncovered = cpc.uncovered_gate_scripts(Path(agate_root).parent)
    assert uncovered == [], (
        f"FAIL: 以下 gate 脚本既不在 CHECK 9 锚点表、也不在豁免集中：{uncovered}"
    )


def test_sg_7_commit_msg_self_gate_exists_executable(agate_scripts):
    """SG.7：commit-msg-self-gate.sh 存在且可执行。"""
    hook_script = agate_scripts / "commit-msg-self-gate.sh"
    assert hook_script.is_file()
    assert os.access(hook_script, os.X_OK)


def test_sg_8_selfgate_has_recursion_termination(agate_root):
    """SG.8：SELF-GATE.md 含递归终止条件。"""
    selfgate_file = _selfgate_file(agate_root)
    assert selfgate_file.is_file()
    text = selfgate_file.read_text(encoding="utf-8")
    assert "递归终止" in text
    assert "ALIGNED" in text


# ---------------------------------------------------------------------------
# SG.9 —— 评审角色的「只读纪律」（RM-AG0081，2026-09-29 实证数据丢失事故）
# ---------------------------------------------------------------------------
#
# 缺陷形态（实测事故）：某次 SELF-GATE 评审的 scratch 目录**跨调用落空**（受限 harness 的
# 临时目录为逐调用重建），评审者遂在**被评审的仓库内**执行 `git checkout -- .` ——
# **丢弃了尚未提交的改动集**，并产生游离提交；主 Agent 据 `git reflog` 才定位，
# 且恢复不完整（事故后又发生的 3 处改动一并丢失）。
#
# 两个独立缺口，本组各锁一个：
#   ① 评审角色文件**没有只读约束**（未禁破坏性 git 命令）；
#   ② 「scratch 目录跨调用不保留」这条 harness 事实**只写给执行角色**，评审角色未继承。
#
# 判据取「条文存在 + 点名到具体命令/具体机制」——仅断言"有只读二字"会被空话满足。


def test_sg_9a_dispatch_template_has_readonly_discipline(agate_root):
    """SG.9a：共享派发模板的 Review 角色指令节含**只读纪律**，且点名声明的禁止命令。"""
    tpl = agate_root / "assets" / "templates" / "dispatch-prompt.md"
    assert tpl.is_file()
    sec = tpl.read_text(encoding="utf-8").split("### Review 角色特别指令", 1)
    assert len(sec) == 2, "派发模板结构已变：找不到「Review 角色特别指令」节"
    body = sec[1].split("\n### ", 1)[0]
    assert "只读" in body, "Review 角色指令未声明只读纪律（RM-AG0081）"
    # 必须点名具体禁止命令——否则「禁止写仓」这种泛化表述会被绕过式满足
    for cmd in ("checkout", "reset", "stash", "clean"):
        assert cmd in body, f"只读纪律未点名禁止命令 `git {cmd}`（清单一漏就有缺口）"
    # 必须含「同一次调用」的 scratch 用法（缺口②）
    assert "同一次" in body, "未说明 scratch 的建/用/清须在**同一次调用**内（跨调用不保留）"


def test_sg_9d_readonly_block_is_inside_a_code_fence(agate_root):
    """SG.9d：只读纪律必须落在**代码围栏内**（它是要注入 subagent 的 prompt 块）。

    ⚠️ 本条来自一次真实自伤（2026-09-29）：初版把只读条文写成 `### 只读纪律` 小节，
    而模板自身用 `### ` 作为「阶段特定提示」的节分隔符 ⇒ 解析在标题处即截断，
    条文**掉到围栏外**（prompt 里根本不会带上它），而 SG.9a 只查文本存在、照样绿。
    ⇒ 判据补上「在围栏内」这一维度：**存在 ≠ 生效**。
    """
    tpl = agate_root / "assets" / "templates" / "dispatch-prompt.md"
    lines = tpl.read_text(encoding="utf-8").splitlines()
    # 找「### Review 角色特别指令」后的第一个 ``` 开栏，与配对的闭栏
    start = next(i for i, ln in enumerate(lines) if ln.startswith("### Review 角色特别指令"))
    open_idx = next(i for i in range(start, len(lines)) if lines[i].startswith("```"))
    close_idx = next(i for i in range(open_idx + 1, len(lines)) if lines[i].startswith("```"))
    inside = "\n".join(lines[open_idx + 1 : close_idx])
    assert "只读" in inside, (
        "只读纪律不在「Review 角色特别指令」的代码围栏内——它不会被注入 subagent 的 prompt"
        "（初版曾误写成 `### 小节`，被模板的 `### ` 节分隔约定截断；存在 ≠ 生效）"
    )
    assert "checkout" in inside, "围栏内的只读纪律未点名禁止命令"


def test_sg_9b_selfgate_role_file_has_readonly_discipline(agate_root):
    """SG.9b：SELF-GATE 评审角色文件本身也须含只读纪律（它就是出事故的那个角色）。"""
    role = _role_file(agate_root)
    text = role.read_text(encoding="utf-8")
    assert "只读" in text, "protocol-alignment-review 角色文件未含只读纪律（RM-AG0081）"
    assert "checkout" in text, "未点名禁止 `git checkout`（正是事故命令）"
    assert "未提交" in text or "尚未提交" in text, (
        "未说明**为什么**只读——须讲清「被评审的改动集可能尚未提交，写仓会销毁他人工作」"
    )


def test_sg_9c_platform_notes_has_cross_call_scratch_rule(agate_root):
    """SG.9c：`platform-notes.md` 受限 harness 节须含「跨调用不保留 ⇒ 建/用/清同一次调用」约定。"""
    text = (agate_root / "platform-notes.md").read_text(encoding="utf-8")
    sec = text.split("## 受限 harness 通用约束", 1)
    assert len(sec) == 2, "platform-notes 结构已变：找不到「受限 harness 通用约束」节"
    body = sec[1].split("\n## ", 1)[0]
    assert "同一次调用" in body, (
        "受限 harness 节未含「建/用/清须在同一次调用内」（RM-AG0081 缺口②：该事实未覆盖评审角色）"
    )
    assert "评审" in body, (
        "该节未说明**同样适用于评审角色**——初版只写给执行角色，评审角色未继承而踩坑"
    )
