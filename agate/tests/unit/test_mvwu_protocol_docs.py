# tests/unit/test_mvwu_protocol_docs.py — TAG0036（MVWU 阶段 1 试点）文档 / 字段链路 / 守护类断言
# 覆盖 P1 BDD-1/2/3/5/6/7/8/9/10/11/12/59-71（映射见任务目录 P3-test-cases-docs.md）。
# 形式：
#   * 文档类 BDD：读 agate/ 下目标文件，按 P1「字面标记」逐字断言（section 提取 + `in` / 正则）；
#   * 字段链路（BDD-1/2）：agate-md-field-get.py / check-gate.py P2 只读运行（tmp_path 任务目录）；
#   * 守护类：B2（agate-read-p5-commands 读回不抛 ValueError）、B3（P5_history_untouched 读回命令
#     在 tmp_path 临时 git 仓库执行）、同源对拍（field-get vs split_frontmatter）——现即为绿的回归守护；
#   * git 基线依赖型断言（BDD-3/5/9/12/67/68② 的 `git diff <内核基线>` 部分）不在本文件：
#     由 P5 gate_commands（P5_kernel_diff / P5_kernel_diff_wt / P5_roles_diff / P5_history_untouched）
#     承担，避免"一次性交付事实"被写成永久回归测试后假性变红（TAG0025 教训；P2 R5）。
# 平台无关（AGENTS.md「测试约定」）：tmp_path、sys.executable、pathlib、显式 utf-8、无 /tmp 字面量。

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from conftest import add_p2_review

REPO = Path(__file__).resolve().parents[3]  # agate/tests/unit/x.py -> 仓库根
AGATE = REPO / "agate"
SCRIPTS = AGATE / "scripts"
TASK_DIR = REPO / "agate-workspace" / "tasks" / "TAG0036-mvwu-pilot"
P2_DESIGN = TASK_DIR / "P2-design.md"

P2_CARD = AGATE / "phase-cards" / "P2-design.md"
P4_CARD = AGATE / "phase-cards" / "P4-implementation.md"
P7_CARD = AGATE / "phase-cards" / "P7-consistency.md"
ARCHITECT = AGATE / "assets" / "execution-roles" / "architect.md"
TASK_FILES = AGATE / "assets" / "templates" / "task-files.md"
ROLE_SYSTEM = AGATE / "role-system.md"
ADR = AGATE / "adr.md"
CONTEXT = AGATE / "CONTEXT.md"
SCRIPTS_README = SCRIPTS / "README.md"
TESTS_README = AGATE / "tests" / "README.md"
CHANGELOG = REPO / "CHANGELOG.md"
TECH_DEBT = REPO / "agate-workspace" / "debt" / "tech-debt.md"
CONSISTENCY = SCRIPTS / "check-protocol-consistency.py"


# ───────────────────────────── helpers ─────────────────────────────


def _read(path):
    return Path(path).read_text(encoding="utf-8")


_HEAD_RE = re.compile(r"^(#{1,6})\s+(.*)$")


def _section(text, title_re):
    """取第一个标题匹配 title_re 的节（含其子节），至下一个同级或更高级标题前；围栏内 # 不算标题。无 → ""。"""
    lines = text.splitlines()
    in_fence = False
    start = None
    level = 0
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = _HEAD_RE.match(line)
        if not m:
            continue
        lv = len(m.group(1))
        if start is None:
            if re.search(title_re, m.group(2)):
                start = i
                level = lv
        elif lv <= level:
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:]) if start is not None else ""


def _missing(text, markers):
    """markers 中的每项为 str（字面 in）或已编译 re.Pattern（search）；返回缺失项列表。"""
    out = []
    for mk in markers:
        if isinstance(mk, re.Pattern):
            if not mk.search(text):
                out.append(mk.pattern)
        elif mk not in text:
            out.append(mk)
    return out


def _same_line(*needles):
    """同一行同时出现所有 needles 的正则（保证'X 为可选'类标记不是散落在不同位置的巧合）。"""
    lookaheads = "".join(f"(?=[^\\n]*{re.escape(n)})" for n in needles)
    return re.compile(r"^" + lookaheads + r"[^\n]*$", re.M)


def _text_files_under(root, suffixes, exclude_dirs=()):
    for p in sorted(Path(root).rglob("*")):
        if not p.is_file() or p.suffix not in suffixes:
            continue
        if "__pycache__" in p.parts:
            continue
        if any(ex in p.parents for ex in exclude_dirs):
            continue
        yield p


def _clean_git_env():
    env = os.environ.copy()
    for k in list(env):
        if k.startswith("GIT_"):
            env.pop(k)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(repo, *args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=str(repo),
        check=check,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        env=_clean_git_env(),
    )


def _md_field_get(run_cli, op, md_file):
    return run_cli(
        sys.executable,
        str(SCRIPTS / "agate-md-field-get.py"),
        op,
        env={"FILE": str(md_file)},
    )


def _yaml_dq(s):
    """YAML 双引号标量（flow 风格内）编码。"""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _p2_with_plan(dispatch_line):
    return (
        "---\nagent: test\ncandidate_count: 2\n"
        f"dispatch_plan: {dispatch_line}\n"
        "---\n"
        "# P2 design\n"
        "### 候选方案 A：方案一\n"
        "### 候选方案 B：方案二\n"
        "## 权衡\n"
        "A 更简单，B 更稳健。\n"
        "packages: [pkg-a]\n"
        "domains: [backend]\n"
        "ui_affected: false\n"
        "gate_commands: {}\n"
    )


def _p5_commands(run_cli):
    """经仓库内 agate-read-p5-commands.py 读回本任务 P2-design.md 的 gate_commands.P5* 命令。"""
    assert P2_DESIGN.is_file(), f"本任务 P2-design.md 不存在：{P2_DESIGN}"
    res = run_cli(
        sys.executable,
        str(SCRIPTS / "agate-read-p5-commands.py"),
        env={"P2_DESIGN": str(P2_DESIGN)},
    )
    assert res.returncode == 0, res.output
    return json.loads(res.stdout)["commands"]


def _table_rows(text):
    """`| ` 开头的 markdown 表格数据行 → [(原行, 首列文本)]（含表头；分隔行 `|---` 不含）。"""
    rows = []
    for line in text.splitlines():
        if line.startswith("| "):
            m = re.match(r"\|\s*(.+?)\s*\|", line)
            rows.append((line, m.group(1) if m else ""))
    return rows


_PLATFORM_TOKEN_RE = re.compile(
    r"(?<![\w-])(?:OpenCode|Claude Code|DSH|workflow|ralph|goal|task)(?![\w-])"
)


def _platform_token_hits(section_text):
    """CHECK 14 同口径（词边界、大小写敏感、跳过代码围栏）：返回命中的 (行, 词) 列表。"""
    hits = []
    in_fence = False
    for line in section_text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in _PLATFORM_TOKEN_RE.finditer(line):
            hits.append((line.strip()[:60], m.group(0)))
    return hits


def _doc_sections():
    """两处文档各自的 tests_filter/批切分相关节（P1 BDD-6/9/61/63 的读取范围）。"""
    return {
        "p2_card": _section(_read(P2_CARD), r"^dispatch_plan 机器字段"),
        "architect": _section(_read(ARCHITECT), r"^批次设计"),
    }


# BDD-59：CONTEXT.md 基线（efb113b）28 个既有术语行的"术语"列（嵌入为不可变基线，避免依赖 git 历史）
_CONTEXT_BASELINE_TERMS = [
    "gate", "裁剪", "机制交叉", "声明性改动", "行为逻辑改动", "BDD", "NEED_CONFIRM", "SCOPE+",
    "SCOPE_GAP", "C8 域", "agent 字段", "PAUSED", "READY", "dispatch-context", "PROD_TOUCHED",
    "DESIGN_GAP", "自审", "裁剪说明", "风险等级", "ceremony", "P6.5 / judge",
    "gate-events.jsonl（事件账本）", "命令流日志（cmdstream）", "agate next / agate advance",
    "派发路由 / tier", "pytest", "windows_smoke marker", "conftest",
]

# BDD-7：architect.md「批次设计」既有四条「硬规则」（基线逐字；须原样保留且相邻）
_ARCHITECT_HARD_RULES = [
    "- **high 复杂度必须拆分**——工作量评估任一维度 high → 必须设计拆批（模式 2/3/4/5），不允许单发",
    "- **批次粒度受工作量评估约束**——单批的产出文件数 / 输入文件数仍遵守「派发编排机制」任务粒度基准（产出 ≤3 / 输入 ≤3，每并行 subagent 适用）",
    "- 无法预先确定拆分方案（结构不明）→ 选模式 4（recon-then-split），设计侦察 subagent 产出拆分方案",
    "- 多包时合并语义（BDD 全局编号、包归属去重）在设计节声明，见「派发编排机制」模式 4 流程",
]


# ═════════════════ ① tests_filter：字段链路（BDD-1/2/3/5，回归守护，现即为绿）═════════════════


@pytest.mark.windows_smoke
def test_bdd_1_tests_filter_roundtrip_via_md_field_get(run_cli, tmp_path):
    """BDD-1：P1 原样例——含空格的双引号 tests_filter 经 agate-md-field-get dispatch_plan 逐字节读回。"""
    value = "python -m pytest tests/auth/test_token.py -q"
    p2 = tmp_path / "P2-design.md"
    p2.write_text(
        "---\nagent: test\n"
        "dispatch_plan: {mode: static-batch, batches: [{id: auth-token-parser, complexity: medium, "
        f'tests_filter: "{value}"}}]}}\n'
        "---\nbody\n",
        encoding="utf-8",
    )
    res = _md_field_get(run_cli, "dispatch_plan", p2)
    assert res.returncode == 0, res.output
    plan = json.loads(res.stdout.strip())
    got = plan["batches"][0]["tests_filter"]
    assert got == value
    assert got.encode("utf-8") == value.encode("utf-8")


@pytest.mark.parametrize(
    "value",
    [
        "python -m pytest tests/a.py -q",  # 空格
        "python -m pytest tests/a.py -q | cat",  # 管道
        'python -m pytest tests/a.py -k "x or y" -q',  # 转义引号
        "python -m pytest tests/a.py::test_x[a,b-1] -q",  # 参数化 id：逗号 + 方括号
        "python -m pytest tests/a.py -q  # 中文注释：不落地",  # '#' 与中文
    ],
    ids=["spaces", "pipe", "escaped-quote", "param-id", "hash-cjk"],
)
def test_bdd_1_tests_filter_special_values_passthrough(run_cli, tmp_path, value):
    """BDD-1（等价类）：含空格 / `|` / 转义引号 / 逗号方括号的值原样透传。"""
    p2 = tmp_path / "P2-design.md"
    p2.write_text(
        "---\nagent: test\n"
        "dispatch_plan: {mode: static-batch, batches: ["
        f"{{id: b1, complexity: low, tests_filter: {_yaml_dq(value)}}}, "
        "{id: b2, complexity: low}]}\n"
        "---\nbody\n",
        encoding="utf-8",
    )
    res = _md_field_get(run_cli, "dispatch_plan", p2)
    assert res.returncode == 0, res.output
    plan = json.loads(res.stdout.strip())
    assert plan["batches"][0]["tests_filter"] == value
    assert "tests_filter" not in plan["batches"][1]  # 可选键逐批独立


def test_bdd_2_gate_p2_accepts_tests_filter_same_as_without(task_dir, run_cli):
    """BDD-2：每批含 tests_filter 的合法 dispatch_plan，P2 gate 结果与'删去全部 tests_filter'相同（均放行 exit 2）。"""
    plan_with = (
        "{mode: static-batch, parallel_limit: 3, batches: ["
        '{id: b1, complexity: medium, tests_filter: "python -m pytest tests/a.py -q"}, '
        '{id: b2, complexity: low, tests_filter: "python -m pytest tests/b.py -q | cat"}]}'
    )
    plan_without = (
        "{mode: static-batch, parallel_limit: 3, batches: ["
        "{id: b1, complexity: medium}, {id: b2, complexity: low}]}"
    )
    results = []
    for plan in (plan_with, plan_without):
        td = task_dir()
        (td / "P2-design.md").write_text(_p2_with_plan(plan), encoding="utf-8")
        add_p2_review(td)
        res = run_cli(sys.executable, str(SCRIPTS / "check-gate.py"), "P2", str(td))
        results.append((res.returncode, res.output.replace(str(td), "<TD>")))
    assert results[0][0] == results[1][0] == 2, results
    assert results[0][1] == results[1][1]
    assert "dispatch_plan" not in results[0][1]


def test_bdd_2_gate_p2_still_rejects_invalid_plan_with_tests_filter(task_dir, run_cli):
    """BDD-2（对照）：带 tests_filter 的批若缺 complexity，gate 仍照旧拒绝——证明只是未知键被忽略、非 fail-open。"""
    td = task_dir()
    plan = '{mode: static-batch, batches: [{id: b1, tests_filter: "python -m pytest a.py -q"}]}'
    (td / "P2-design.md").write_text(_p2_with_plan(plan), encoding="utf-8")
    add_p2_review(td)
    res = run_cli(sys.executable, str(SCRIPTS / "check-gate.py"), "P2", str(td))
    assert res.returncode == 1, res.output
    assert "GATE P2" in res.output


@pytest.mark.parametrize(
    "rel",
    [
        "agate/tests/unit/test_dispatch_orchestration.py",
        "agate/tests/unit/test_check_gate.py",
        "agate/tests/unit/test_agate_md_field_get.py",
    ],
)
def test_bdd_3_existing_gate_test_files_present(rel):
    """BDD-3：既有三个 gate/field-get 测试文件仍在且含用例（未被删除）。空 diff / 全绿由 P5_kernel_diff + 全量 P5 承担。"""
    p = REPO / rel
    assert p.is_file(), f"既有测试文件被删除：{rel}"
    assert len(re.findall(r"^def test_", _read(p), re.M)) >= 5


def test_bdd_5_debt_entry_registers_gate_p2_fail_open():
    """BDD-5：tech-debt.md 含一条同时含 `_gate_p2_dispatch_plan` 与"静默放行"（或 `return None`）的 DEBT 条目。"""
    blocks = re.findall(r"```yaml\n(.*?)\n```", _read(TECH_DEBT), re.S)
    hits = [
        b
        for b in blocks
        if "_gate_p2_dispatch_plan" in b and ("静默放行" in b or "return None" in b)
    ]
    assert hits, "tech-debt.md 无同时含 `_gate_p2_dispatch_plan` 与 静默放行/return None 的 DEBT 条目"
    assert any(re.search(r"^id:\s*DEBT\d+", b, re.M) for b in hits)


def test_bdd_5_check_debt_passes_on_tech_debt(run_cli):
    """BDD-5（回归守护，现即绿）：check-debt.py 校验 tech-debt.md exit 0。"""
    res = run_cli(sys.executable, str(SCRIPTS / "check-debt.py"), str(TECH_DEBT), cwd=REPO)
    assert res.returncode == 0, res.output


# ═════════════════ ④ 字段落地路径：P2 卡片 + architect（BDD-6/7/8/9）═════════════════


def test_bdd_6_p2_card_documents_tests_filter():
    """BDD-6：P2 卡「dispatch_plan 机器字段」节含 tests_filter 写法与约束的全部字面标记。"""
    sec = _section(_read(P2_CARD), r"^dispatch_plan 机器字段")
    assert sec, "P2 卡缺「dispatch_plan 机器字段」节"
    markers = [
        _same_line("tests_filter", "可选"),
        "双引号",
        "禁止全量",
        "expected_red",
        "P4-evidence/{batch}.log",
        "[A-Za-z0-9._-]+",
        "缺省",
        "python -m pytest",
    ]
    assert not _missing(sec, markers), f"缺字面标记：{_missing(sec, markers)}"


def test_bdd_7_architect_documents_tests_filter_selection():
    """BDD-7：architect.md「批次设计」节含 tests_filter 选取法、与 P3 分工、expected_red 字面标记。"""
    sec = _section(_read(ARCHITECT), r"^批次设计")
    assert sec, "architect.md 缺「批次设计」节"
    markers = [
        "tests_filter",
        "禁止全量",
        "gate_commands.P3",
        "红灯基线",
        "绿灯确认",
        "expected_red",
    ]
    assert not _missing(sec, markers), f"缺字面标记：{_missing(sec, markers)}"


def test_bdd_7_architect_four_hard_rules_verbatim_and_adjacent():
    """BDD-7（回归守护，现即绿）：「批次设计」既有『硬规则』四条逐字保留且相邻（基线 efb113b 字面）。"""
    sec_lines = _section(_read(ARCHITECT), r"^批次设计").splitlines()
    assert "**硬规则**：" in sec_lines
    idx = sec_lines.index(_ARCHITECT_HARD_RULES[0]) if _ARCHITECT_HARD_RULES[0] in sec_lines else -1
    assert idx >= 0, "硬规则第 1 条被改动或删除"
    assert sec_lines[idx : idx + 4] == _ARCHITECT_HARD_RULES


def test_bdd_8_no_bare_python3_inside_tests_filter_examples():
    """BDD-8：agate/（不含 agate/tests/）内 `tests_filter: "…python3…"` 示例值 0 命中（P1 原正则）。"""
    pat = re.compile(r'tests_filter: *"[^"]*\bpython3\b')
    offenders = []
    for p in _text_files_under(
        AGATE, {".md", ".py", ".sh", ".yaml", ".yml", ".json", ".txt"}, exclude_dirs=(AGATE / "tests",)
    ):
        for n, line in enumerate(p.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if pat.search(line):
                offenders.append(f"{p.relative_to(REPO)}:{n}")
    assert not offenders, f"tests_filter 示例值含裸 python3：{offenders}"


@pytest.mark.parametrize("doc", ["p2_card", "architect"])
def test_bdd_8_docs_state_platform_neutral_constraint(doc):
    """BDD-8：P2 卡与 architect.md 均含平台中立约束字样（AGATE_PYTHON / DEBT0014 / 不裸 python3 之一）。"""
    text = _read(P2_CARD if doc == "p2_card" else ARCHITECT)
    assert any(t in text for t in ("AGATE_PYTHON", "DEBT0014", "不裸 python3")), f"{doc} 缺平台中立约束字样"


@pytest.mark.parametrize("doc", ["p2_card", "architect"])
def test_bdd_9_output_optional_key_documented(doc):
    """BDD-9：二处均说明 output 为可选键、仅供 --observe、不新增 gate 校验。frontmatter-check/structure-consistency 空 diff 由 P5_kernel_diff 承担。"""
    sec = _doc_sections()[doc]
    assert sec, f"{doc} 缺目标节"
    markers = [
        _same_line("`output`", "可选"),
        "--observe",
        "不新增 gate 校验",
    ]
    assert not _missing(sec, markers), f"缺字面标记：{_missing(sec, markers)}"


# ═════════════════ ② P4-evidence 落点（BDD-10/11/12）═════════════════


def test_bdd_10_p4_card_documents_evidence_landing():
    """BDD-10：P4 卡含 P4-evidence/{batch}.log 一节：路径、键集、node id/双引号、不阻断、filename-safe、不进 judge 白名单。"""
    sec = _section(_read(P4_CARD), r"P4-evidence")
    assert sec, "P4 卡缺标题含 P4-evidence 的节"
    markers = [
        "P4-evidence/{batch}.log",
        "key: value",
        "command",
        "exit_code",
        "git_head",
        "全长",
        "timestamp",
        "expected_red",
        "duration_seconds",
        "failed_tests",
        "node id",
        "双引号",
        "不阻断",
        "filename-safe",
        "judge",
    ]
    assert not _missing(sec, markers), f"缺字面标记：{_missing(sec, markers)}"


def test_bdd_11_task_files_registers_p4_evidence_and_tests_filter_comment():
    """BDD-11：task-files.md 阶段产出表含 P4 行登记 P4-evidence/{batch}.log；dispatch_plan 示例注释含 tests_filter 可选说明。"""
    text = _read(TASK_FILES)
    rows = [ln for ln in text.splitlines() if ln.startswith("|") and "P4-evidence/{batch}.log" in ln]
    assert any(re.match(r"\|\s*P4\s*\|", ln) for ln in rows), "阶段产出表缺 P4 行登记 P4-evidence/{batch}.log"
    comment_lines = [ln for ln in text.splitlines() if ln.lstrip().startswith("#") and "tests_filter" in ln]
    assert any("可选" in ln for ln in comment_lines), "dispatch_plan 示例注释缺 tests_filter 可选键说明"


def test_bdd_12_no_p4_evidence_in_rules_dispatch_protocol_or_judge():
    """BDD-12：agate/rules/ 下 grep P4-evidence 0 命中；dispatch-protocol.md 与 judge.md 亦不登记（不进 judge 白名单/黑名单）。相关 kernel 文件空 diff 由 P5_kernel_diff 承担。"""
    offenders = []
    for p in _text_files_under(AGATE / "rules", {".md", ".yaml", ".yml", ".json", ".txt", ".py"}):
        if "P4-evidence" in p.read_text(encoding="utf-8", errors="replace"):
            offenders.append(str(p.relative_to(REPO)))
    for extra in (AGATE / "dispatch-protocol.md", AGATE / "assets" / "review-roles" / "judge.md"):
        if extra.is_file() and "P4-evidence" in _read(extra):
            offenders.append(str(extra.relative_to(REPO)))
    assert not offenders, f"P4-evidence 出现在不应登记的面：{offenders}"


# ═════════════════ ⑤-a 术语补录（BDD-59）═════════════════

_NEW_TERM_KEYS = ["MVWU", "tests_filter", "P4-evidence", "verdict", "boundary"]


def _context_new_rows():
    """CONTEXT.md 术语表中不属于基线 28 条的新增行 → {term_key: (行, cells)}（按 _NEW_TERM_KEYS 首列包含匹配）。"""
    found = {}
    for line, first in _table_rows(_read(CONTEXT)):
        if first == "术语" or first in _CONTEXT_BASELINE_TERMS:
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]
        for key in _NEW_TERM_KEYS:
            if key in first and key not in found:
                found[key] = (line, cells)
    return found


def test_bdd_59_context_five_new_terms_three_columns_with_literals():
    """BDD-59：CONTEXT.md 新增 MVWU / tests_filter / P4-evidence / 四态 verdict / boundary 五行，三列格式，定义含字面标记。"""
    found = _context_new_rows()
    assert set(found) == set(_NEW_TERM_KEYS), f"缺失新增术语行：{set(_NEW_TERM_KEYS) - set(found)}"
    for key, (line, cells) in found.items():
        assert len(cells) == 3, f"{key} 行不是三列：{line[:80]}"
        assert all(cells), f"{key} 行存在空列"
    assert "最小可验证工作单元" in found["MVWU"][0]
    verdict_line = found["verdict"][0]
    for word in ("PASS", "FAIL", "EXPECTED_RED", "UNKNOWN"):
        assert word in verdict_line, f"四态 verdict 行缺 {word}"
    assert "UNKNOWN 不等价于 PASS" in verdict_line
    assert "I1" in found["boundary"][0]


def test_bdd_59_new_terms_in_order_and_locations_exist():
    """BDD-59：五行依次出现（MVWU、tests_filter、P4-evidence、verdict、boundary）；'首次定义位置'指向仓库中存在的文件。"""
    found = _context_new_rows()
    assert set(found) == set(_NEW_TERM_KEYS), f"缺失新增术语行：{set(_NEW_TERM_KEYS) - set(found)}"
    lines = _read(CONTEXT).splitlines()
    order = [lines.index(found[k][0]) for k in _NEW_TERM_KEYS]
    assert order == sorted(order), "五个新术语行未按 MVWU→tests_filter→P4-evidence→verdict→boundary 顺序"
    for key, (_line, cells) in found.items():
        m = re.search(r"[\w./-]+\.(?:md|py|yaml|yml|json|sh)", cells[2])
        assert m, f"{key} 行'首次定义位置'无文件路径：{cells[2]}"
        rel = m.group(0)
        assert (REPO / rel).is_file() or (AGATE / rel).is_file(), f"{key} 行首次定义位置不存在：{rel}"


def test_bdd_59_baseline_28_term_rows_still_present():
    """BDD-59（回归守护，现即绿）：基线 28 条既有术语行的'术语'列均仍在（只增不删）。行文逐字未变 / 恰 5 行新增由 P6 证据 git diff 承担。"""
    firsts = [first for _line, first in _table_rows(_read(CONTEXT))]
    missing = [t for t in _CONTEXT_BASELINE_TERMS if t not in firsts]
    assert not missing, f"既有术语行被删除/改名：{missing}"


# ═════════════════ ⑤-b/c/d 审查锚点与批切分三判据（BDD-60..64）═════════════════


def test_bdd_60_role_system_review_anchor_section():
    """BDD-60：role-system.md 新增标题含"审查锚点"的节，含 浅化 / 执行顺序 / 资源地图 / 正交 及审查对象，且无"已生效"字样。"""
    sec = _section(_read(ROLE_SYSTEM), r"审查锚点")
    assert sec, "role-system.md 缺标题含「审查锚点」的节"
    markers = ["角色文件", "阶段卡片", "浅化", "执行顺序", "资源地图", "正交"]
    assert not _missing(sec, markers), f"缺字面标记：{_missing(sec, markers)}"
    assert "已生效" not in sec and "已验证生效" not in sec


def test_bdd_60_new_section_has_no_bare_platform_tokens():
    """BDD-60（R3 / CHECK 14 预防）：新增审查锚点节不含裸 task/goal/workflow/DSH/OpenCode/Claude Code/ralph。"""
    sec = _section(_read(ROLE_SYSTEM), r"审查锚点")
    assert sec, "role-system.md 缺标题含「审查锚点」的节"
    assert not _platform_token_hits(sec)


@pytest.mark.parametrize("doc", ["p2_card", "architect"])
def test_bdd_61_tracer_bullet_criterion(doc):
    """BDD-61：判据一 Tracer Bullet 在 architect.md 与 P2 卡片二处成文（触发条件 / 冒烟 / 目的 / 与 P3 红灯批的边界）。"""
    sec = _doc_sections()[doc]
    assert sec
    markers = [
        "Tracer Bullet",
        "端到端",
        "关键路径",
        re.compile(r"(≥\s*2|>=\s*2|至少\s*2|2\s*个及以上|两个及以上)"),
        "冒烟",
        "管道",
        "P3 红灯批",
    ]
    assert not _missing(sec, markers), f"{doc} 缺字面标记：{_missing(sec, markers)}"


def test_bdd_62_walking_skeleton_absorb_reject_record():
    """BDD-62：architect.md 判据一处含 Walking Skeleton 的吸收/拒绝记录、ADR-003 依据、与 P2-skeleton.md 消歧；无"已生效"。"""
    sec = _section(_read(ARCHITECT), r"^批次设计")
    assert sec
    markers = ["Walking Skeleton", "吸收", "拒绝", "ADR-003", "P2-skeleton.md", "不是同一机制"]
    assert not _missing(sec, markers), f"缺字面标记：{_missing(sec, markers)}"
    new_arch = _section(_read(ARCHITECT), r"批切分判据与 tests_filter 写法")
    assert new_arch, "architect.md 缺 P2 设计 M5 新增的「批切分判据与 tests_filter 写法」小节"
    assert "已生效" not in new_arch
    new_p2 = _section(_read(P2_CARD), r"^batches\[\] 可选键")
    assert new_p2, "P2 卡缺 P2 设计 M2 新增的「batches[] 可选键…」小节"
    assert "已生效" not in new_p2


@pytest.mark.parametrize("doc", ["p2_card", "architect"])
def test_bdd_63_vertical_slice_criterion(doc):
    """BDD-63：判据二 Vertical Slice 二处成文（业务能力优先 / 按技术层须写明理由 / 批 id 判据式表述 / 与判据一的关系）。"""
    sec = _doc_sections()[doc]
    assert sec
    markers = [
        "Vertical Slice",
        "业务能力",
        "写明理由",
        "这个批交付了什么能力",
        "动了哪层代码",
        "判据一",
    ]
    assert not _missing(sec, markers), f"{doc} 缺字面标记：{_missing(sec, markers)}"


@pytest.mark.parametrize("doc", ["p2_card_gate_commands", "architect"])
def test_bdd_64_fitness_functions_criterion(doc):
    """BDD-64：判据三 Fitness Functions 二处成文（适应度 / ≥3 个示例维度 / 由项目自选 / 本任务无架构适应度检查）。"""
    if doc == "architect":
        sec = _section(_read(ARCHITECT), r"^批次设计")
    else:
        sec = _section(_read(P2_CARD), r"^gate_commands 声明")
    assert sec
    markers = ["Fitness Functions", "适应度", "由项目自选", "本任务无架构适应度检查"]
    assert not _missing(sec, markers), f"{doc} 缺字面标记：{_missing(sec, markers)}"
    dims = ["依赖方向", "分层边界", "循环依赖", "公共 API 稳定性"]
    assert sum(1 for d in dims if d in sec) >= 3, f"{doc} 示例维度不足 3 项（{dims}）"


def test_bdd_64_no_mandatory_arch_tool_requirement_in_protocol_docs():
    """BDD-64：agate/ 协议文档中出现 ArchUnit/dependency-cruiser/import-linter 的段落须带"示例"或"由项目自选"（无强制要求）。"""
    tools = ("ArchUnit", "dependency-cruiser", "import-linter")
    offenders = []
    for p in _text_files_under(AGATE, {".md"}, exclude_dirs=(AGATE / "tests",)):
        for para in re.split(r"\n\s*\n", _read(p)):
            if any(t in para for t in tools) and not ("示例" in para or "由项目自选" in para):
                offenders.append(str(p.relative_to(REPO)))
    assert not offenders, f"对架构检查工具的表述缺'示例/由项目自选'限定：{offenders}"


# ═════════════════ ⑤-e 决策复审机制（BDD-65/66）═════════════════


def _adr_header():
    text = _read(ADR)
    idx = text.find("\n## ADR-")
    return text[:idx] if idx >= 0 else text


def test_bdd_65_adr_header_recheck_triggers():
    """BDD-65：adr.md 头部（首个 ## ADR- 之前）新增复审触发条件：已过时+取代 / 不删除 / 复审 / P7 / 新增 ADR 时复核；无自动过期/强制复审 gate。"""
    hdr = _adr_header()
    markers = ["已过时", "取代", "不删除", "复审", "P7", "新增 ADR", "复核"]
    assert not _missing(hdr, markers), f"adr.md 头部缺字面标记：{_missing(hdr, markers)}"
    assert "自动过期" not in hdr and "强制复审" not in hdr


def test_bdd_65_adr_header_has_no_bare_platform_tokens():
    """BDD-65（R3 / CHECK 14 预防）：adr.md 头部新增文字不含裸 task/goal/workflow 等平台词。"""
    assert not _platform_token_hits(_adr_header())


def test_bdd_65_existing_adrs_still_present():
    """BDD-65（回归守护，现即绿）：ADR-001..005 标题仍在（过时不删；逐行零删除 diff 由 P6 证据 git diff 承担）。"""
    text = _read(ADR)
    for n in range(1, 6):
        assert re.search(rf"^## ADR-00{n}\b", text, re.M), f"ADR-00{n} 标题丢失"


def test_bdd_66_p2_card_decisions_landing_and_reading():
    """BDD-66：P2 卡含跨任务架构决策落 decisions/、P2 开始前读取既有决策、前提被证伪就地标已过时；无"必须拦截"式 gate 表述。"""
    text = _read(P2_CARD)
    markers = ["decisions/", "既有决策", "已过时"]
    assert not _missing(text, markers), f"P2 卡缺字面标记：{_missing(text, markers)}"
    assert "必须拦截" not in text


def test_bdd_66_write_timing_stated_in_p2_or_p7_card():
    """BDD-66：P2 卡与 P7 卡至少一处写明写入决策的时机（同一行含 decisions/ 与 写入）；P7 卡含 decisions/ 核对项。"""
    p2, p7 = _read(P2_CARD), _read(P7_CARD)
    pat = _same_line("decisions/", "写入")
    assert pat.search(p2) or pat.search(p7), "P2/P7 卡均未写明写入 decisions/ 的时机"
    assert "decisions/" in p7, "P7 卡无 decisions/ 落点核对项"
    assert "必须拦截" not in p7


def test_bdd_66_check_gate_does_not_read_decisions_dir():
    """BDD-66（回归守护，现即绿）：check-gate.py 不出现对 decisions/ 的读取（长期不变量：不挂 gate）。"""
    assert "decisions" not in _read(SCRIPTS / "check-gate.py")


# ═════════════════ 负向与收口（BDD-67..71）═════════════════


def test_bdd_67_kernel_files_exist_for_p5_diff_gate():
    """BDD-67：零内核改动的 `git diff <内核基线>` 空断言由 P5_kernel_diff / P5_kernel_diff_wt 承担（P2 R5）；
    本用例只守护该 gate key 已登记且覆盖 P1 BDD-67 清单全部路径（防 P2 gate_commands 漏项）。"""
    text = _read(P2_DESIGN)
    must = [
        "agate/scripts/check-gate.py", "agate/rules/phases.yaml", "agate/rules/schema",
        "agate/scripts/pre-commit-gate.py", "agate/scripts/pre-commit-gate.sh",
        "agate/scripts/commit-msg-self-gate.py", "agate/scripts/commit-msg-self-gate.sh",
        "agate/scripts/pre-push-gate.py", "agate/scripts/pre-push-gate.sh",
        "agate/scripts/check-state-yaml.py", "agate/scripts/agate-state-yaml-check.py",
        "agate/scripts/check-state-transition.py", "agate/scripts/check-events.py",
        "agate/scripts/agate_common.py", "agate/scripts/check-p6-provenance.py",
        "agate/scripts/check-judge-verdict.py",
    ]
    line = next((ln for ln in text.splitlines() if ln.startswith("  P5_kernel_diff:")), "")
    assert line, "P2-design.md 未声明 P5_kernel_diff"
    assert not [m for m in must if m not in line], [m for m in must if m not in line]
    # 命名的路径必须真实存在（防 gate 命令里的路径拼写漂移成永远空 diff）
    for m in must:
        assert (REPO / m).exists(), f"P5_kernel_diff 引用的路径不存在：{m}"


def test_bdd_68_check_mvwu_not_registered_in_gate_hook_ci_surfaces():
    """BDD-68①：check-mvwu 不在 agate/rules、check-gate.py、pre-commit-gate.py、ci-gate-backstop.py、agate-summary.py、.github/ 登记（长期不变量：观测脚本不挂 gate）。"""
    targets = [SCRIPTS / n for n in ("check-gate.py", "pre-commit-gate.py", "ci-gate-backstop.py", "agate-summary.py")]
    files = [p for p in targets if p.is_file()]
    files += list(_text_files_under(AGATE / "rules", {".md", ".yaml", ".yml", ".json", ".txt", ".py"}))
    gh = REPO / ".github"
    if gh.is_dir():
        files += [p for p in sorted(gh.rglob("*")) if p.is_file()]
    hits = [str(p.relative_to(REPO)) for p in files if "check-mvwu" in p.read_text(encoding="utf-8", errors="replace")]
    assert not hits, f"check-mvwu 被登记到 gate/hook/CI 面：{hits}"


def test_bdd_69_scripts_readme_row_for_check_mvwu():
    """BDD-69：scripts/README.md 脚本表含 check-mvwu.py 行：观测/不阻断/--observe/exit 0 与 2 约定。"""
    rows = [ln for ln in _read(SCRIPTS_README).splitlines() if ln.startswith("|") and "check-mvwu.py" in ln]
    assert rows, "scripts/README.md 无 check-mvwu.py 行"
    row = rows[0]
    for lit in ("观测", "不阻断", "--observe", "verdict"):
        assert lit in row, f"check-mvwu.py 行缺 {lit!r}"
    assert re.search(r"\b0\s*=", row) and re.search(r"\b2\s*=", row), "行内缺 exit 0=/2= 约定"


def test_bdd_69_tests_readme_row_matches_collected_count():
    """BDD-69：tests/README.md 映射表含 check-mvwu 测试文件行，用例数 = pytest --collect-only 实数。count-tests.sh 总数 ≥ 1668+N 由 P5_count 承担。"""
    tfile = AGATE / "tests" / "unit" / "test_check_mvwu.py"
    assert tfile.is_file(), "agate/tests/unit/test_check_mvwu.py 不存在（script 半边产出）"
    rows = [ln for ln in _read(TESTS_README).splitlines() if ln.startswith("|") and "test_check_mvwu.py" in ln]
    assert rows, "tests/README.md 无 test_check_mvwu.py 行"
    cells = [c.strip() for c in rows[0].strip().strip("|").split("|")]
    nums = [c for c in cells if c.isdigit()]
    assert nums, f"行内无用例数列：{rows[0]}"
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", "-o", "addopts=", str(tfile)],
        cwd=str(REPO),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        env=env,
    )
    collected = sum(1 for ln in proc.stdout.splitlines() if "::" in ln)
    assert collected > 0, proc.stdout + proc.stderr
    assert int(nums[-1]) == collected, f"README 用例数 {nums[-1]} != 实际收集 {collected}"


def test_bdd_69_changelog_mentions_tag0036():
    """BDD-69：CHANGELOG.md 含 TAG0036（[Unreleased] 转正后仍成立——不断言 Unreleased 段本身，TAG0025 教训）。"""
    assert "TAG0036" in _read(CHANGELOG)


def test_bdd_70_gate_script_exempt_contains_check_mvwu():
    """BDD-70 / M18（B1）：check-protocol-consistency.py::GATE_SCRIPT_EXEMPT 含 agate/scripts/check-mvwu.py（使 test_sg_6 为绿、CHECK9-coverage 0 新增）。"""
    text = _read(CONSISTENCY)
    m = re.search(r"GATE_SCRIPT_EXEMPT\s*=\s*\{(.*?)\n\}", text, re.S)
    assert m, "找不到 GATE_SCRIPT_EXEMPT 定义"
    assert '"agate/scripts/check-mvwu.py"' in m.group(1)
    # 既有两条豁免逐字保留
    assert '"agate/scripts/check-protocol-consistency.py"' in m.group(1)
    assert '"agate/scripts/pre-commit-gate.py"' in m.group(1)


def test_bdd_71_p4_protocol_alignment_review_exists_with_conclusion():
    """BDD-71：任务目录存在 P4-protocol-alignment-review.md，agent ≠ main 且含结论。P4 提交信息含 self-gate-review: 由 P6 证据（git log）承担。"""
    f = TASK_DIR / "P4-protocol-alignment-review.md"
    assert f.is_file(), "缺 P4-protocol-alignment-review.md"
    text = _read(f)
    sys.path.insert(0, str(SCRIPTS))
    try:
        import agate_common
    finally:
        sys.path.pop(0)
    fm, _body = agate_common.split_frontmatter(text)
    assert isinstance(fm, dict), "无合法 frontmatter"
    agent = str(fm.get("agent", "")).strip()
    assert agent and agent != "main", f"agent 非法：{agent!r}"
    assert "结论" in text


# ═════════════════ 守护类（P2 §13；B1 登记 + B2/B3/同源对拍，现即为绿的回归守护）═════════════════


def test_guard_b1_sg6_exists_in_alignment_review_tests():
    """B1 守护（登记，P4 前应已绿）：test_protocol_alignment_review.py::test_sg_6_check9_anchor_table_covers_all_gate_scripts 仍存在。
    该用例本身不新增，P5 全量 pytest 中它必须保持绿；本用例仅防它被误删。"""
    text = _read(AGATE / "tests" / "integration" / "test_protocol_alignment_review.py")
    assert "def test_sg_6_check9_anchor_table_covers_all_gate_scripts(" in text


def test_guard_b2_p5_commands_shlex_split_and_no_quote_residue(run_cli):
    """B2 守护（回归守护，现即绿）：agate-read-p5-commands 读回本任务 P2-design.md 的每条 cmd 均 shlex.split 不抛 ValueError，末 token 无引号残留。"""
    cmds = _p5_commands(run_cli)
    assert len(cmds) >= 10
    for entry in cmds:
        try:
            argv = shlex.split(entry["cmd"])
        except ValueError as exc:  # 引号不闭合
            pytest.fail(f"P5{entry['suffix']} 读回命令 shlex.split 失败：{exc}；cmd={entry['cmd']!r}")
        assert argv, f"P5{entry['suffix']} 读回命令为空"
        last = argv[-1]
        assert not last.startswith(("'", '"')) and not last.endswith(("'", '"')), f"末 token 引号残留：{last!r}"
        assert entry["cmd"] == entry["cmd"].strip()
        assert not entry["cmd"].endswith(("'", '"'))


_HIST_PATHSPECS = ["agate-workspace/tasks/TAG00[0-2]*", "agate-workspace/tasks/TAG003[0-5]*"]


def _history_cmd_argv(run_cli):
    cmds = _p5_commands(run_cli)
    hit = [c for c in cmds if c["suffix"] == "_history_untouched"]
    assert len(hit) == 1, "P2-design.md 未声明（或重复声明）P5_history_untouched"
    return shlex.split(hit[0]["cmd"])


def test_guard_b3_history_untouched_pathspec_is_literal_glob(run_cli):
    """B3 守护：P5_history_untouched 读回 shlex.split 的 pathspec 为字面通配（非已展开的目录名）；revspec 为三点 main...HEAD。"""
    argv = _history_cmd_argv(run_cli)
    assert argv[:3] == ["git", "diff", "--exit-code"]
    assert "main...HEAD" in argv
    assert "--" in argv
    assert argv[argv.index("--") + 1 :] == _HIST_PATHSPECS
    assert argv.index("main...HEAD") < argv.index("--")


def _make_history_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    hooks = tmp_path / "nohooks"
    hooks.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "t")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "core.hooksPath", str(hooks))
    tasks = repo / "agate-workspace" / "tasks"
    for name in ("TAG0010-x", "TAG0011-x", "TAG0031-x", "TAG0032-x", "TAG0036-x"):
        (tasks / name).mkdir(parents=True)
        (tasks / name / "f.txt").write_text(name + "\n", encoding="utf-8")
    (repo / "README.md").write_text("r\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "branch", "-M", "main")
    _git(repo, "checkout", "-q", "-b", "feat")
    return repo


def _mutate(repo, kind):
    tasks = repo / "agate-workspace" / "tasks"
    if kind == "delete_TAG0010":
        shutil.rmtree(tasks / "TAG0010-x")
    elif kind == "delete_TAG0031":
        shutil.rmtree(tasks / "TAG0031-x")
    elif kind == "delete_two_TAG0010_TAG0031":
        shutil.rmtree(tasks / "TAG0010-x")
        shutil.rmtree(tasks / "TAG0031-x")
    elif kind == "delete_two_TAG0011_TAG0032":
        shutil.rmtree(tasks / "TAG0011-x")
        shutil.rmtree(tasks / "TAG0032-x")
    elif kind == "modify_TAG0011":
        with open(tasks / "TAG0011-x" / "f.txt", "a", encoding="utf-8") as fh:
            fh.write("edit\n")
    elif kind == "modify_TAG0032":
        with open(tasks / "TAG0032-x" / "f.txt", "a", encoding="utf-8") as fh:
            fh.write("edit\n")
    elif kind == "add_TAG0012":
        (tasks / "TAG0012-y").mkdir()
        (tasks / "TAG0012-y" / "f.txt").write_text("new\n", encoding="utf-8")
    elif kind == "add_TAG0033":
        (tasks / "TAG0033-y").mkdir()
        (tasks / "TAG0033-y" / "f.txt").write_text("new\n", encoding="utf-8")
    elif kind == "modify_TAG0036":
        with open(tasks / "TAG0036-x" / "f.txt", "a", encoding="utf-8") as fh:
            fh.write("edit\n")
    elif kind == "add_TAG0037":
        (tasks / "TAG0037-y").mkdir()
        (tasks / "TAG0037-y" / "f.txt").write_text("new\n", encoding="utf-8")
    elif kind == "modify_TAG0036_and_add_TAG0037":
        _mutate(repo, "modify_TAG0036")
        _mutate(repo, "add_TAG0037")
    else:
        raise AssertionError(kind)


@pytest.mark.parametrize(
    "kind,expected_rc",
    [
        ("delete_TAG0010", 1),
        ("delete_TAG0031", 1),
        ("delete_two_TAG0010_TAG0031", 1),
        ("delete_two_TAG0011_TAG0032", 1),
        ("modify_TAG0011", 1),
        ("modify_TAG0032", 1),
        ("add_TAG0012", 1),
        ("add_TAG0033", 1),
        ("modify_TAG0036", 0),
        ("add_TAG0037", 0),
        ("modify_TAG0036_and_add_TAG0037", 0),
    ],
)
def test_guard_b3_history_untouched_command_in_tmp_repo(run_cli, tmp_path, kind, expected_rc):
    """B3 守护：读回的 P5_history_untouched 命令在 tmp_path 临时仓库执行——删除（含同删两个）/ 修改 / 新增历史目录 rc=1，改 TAG0036/0037 rc=0。"""
    argv = _history_cmd_argv(run_cli)
    repo = _make_history_repo(tmp_path)
    _mutate(repo, kind)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "change")
    res = subprocess.run(
        argv,
        cwd=str(repo),
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
        env=_clean_git_env(),
    )
    assert res.returncode == expected_rc, f"{kind}: rc={res.returncode}\n{res.stdout}{res.stderr}"


def test_guard_same_source_md_field_get_vs_split_frontmatter(run_cli, tmp_path):
    """同源对拍：同一份 P2 样例经 agate-md-field-get dispatch_plan 与 agate_common.split_frontmatter 得同一 JSON（方案 A 同源性的保险）。"""
    sys.path.insert(0, str(SCRIPTS))
    try:
        import agate_common
    finally:
        sys.path.pop(0)
    sample = tmp_path / "P2-design.md"
    sample.write_text(
        _p2_with_plan(
            "{mode: static-batch, parallel_limit: 6, batches: ["
            '{id: b1, complexity: medium, tests_filter: "python -m pytest tests/a.py -k \\"x or y\\" -q | cat", '
            'output: ["agate/scripts/x.py"]}, {id: b2, complexity: low}]}'
        ),
        encoding="utf-8",
    )
    for src in (sample, P2_DESIGN):
        res = _md_field_get(run_cli, "dispatch_plan", src)
        assert res.returncode == 0, res.output
        fm, _body = agate_common.split_frontmatter(src.read_text(encoding="utf-8"))
        assert isinstance(fm, dict) and "dispatch_plan" in fm
        assert res.stdout.strip() == json.dumps(fm["dispatch_plan"], ensure_ascii=False)
        assert json.loads(res.stdout) == fm["dispatch_plan"]
