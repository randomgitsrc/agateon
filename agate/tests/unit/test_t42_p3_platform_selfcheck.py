# tests/unit/test_t42_p3_platform_selfcheck.py — P3 交付前的平台假设自查（DEBT0048）
#
# 缺陷形态：P3 gate 只查「红灯对不对」（check-tdd-red + P3-test-cases.md 存在），
# **不跑平台假设扫描** ⇒ test-designer 交付的测试文件里的平台假设（最常见 = 注释里的
# 系统临时目录字面量）直到 **P4 全量 pytest** 才由 `check-platform-assumptions.py`
# 的 bdd-8（tests/ 全树 0 命中）抓出 ⇒ 多一个「收口小修」回合。
#
# 实测反复性：本仓 2026-09-29 两个批次（TAG0039 / TAG0041）的新测试**各自又踩一次**。
#
# 本组测试**守护文档与派发链三处落点**（P3 卡推进条件 / 派发模板 P3 自检 /
# test-designer 角色文件），使「P3 阶段就该自查」不因后续编辑而丢失。



import re


def _read(p):
    return p.read_text(encoding="utf-8")


def test_t42_p3_card_requires_platform_scan(agate_root):
    """P3 卡「推进条件」须含平台假设扫描自查（含脚本名）。"""
    card = _read(agate_root / "phase-cards" / "P3-tdd.md")
    cond = card.split("## 推进条件", 1)
    assert len(cond) == 2, "P3 卡结构已变：找不到「推进条件」节"
    body = cond[1].split("\n## ", 1)[0]
    assert "check-platform-assumptions.py" in body, (
        "P3 卡推进条件未要求平台假设扫描（DEBT0048 会复发）"
    )
    assert "0 命中" in body, "未给出可判定判据（0 命中）"


def test_t42_dispatch_prompt_p3_selfcheck_mentions_scan(agate_root):
    """派发模板的 P3 自检节须提平台假设扫描，并点明「注释里的字面量也算」。"""
    tpl = _read(agate_root / "assets" / "templates" / "dispatch-prompt.md")
    sec = tpl.split("## P3 自检（强制）", 1)
    assert len(sec) == 2, "派发模板结构已变：找不到 P3 自检节"
    body = sec[1].split("\n## ", 1)[0]
    assert "check-platform-assumptions.py" in body, "P3 自检未要求平台假设扫描"
    assert "注释里" in body, "未点明「注释里的字面量同样计命中」（最常踩的那个）"


def test_t42_test_designer_role_has_precheck(agate_root):
    """test-designer 角色文件须有「交付前自查」节，且含扫描与写入隔离两条。"""
    role = _read(agate_root / "assets" / "execution-roles" / "test-designer.md")
    assert "交付前自查" in role, "角色文件缺交付前自查节"
    assert "check-platform-assumptions.py" in role, "自查未含平台假设扫描"
    assert "tmp_path" in role or "隔离" in role, "自查未含写入隔离（账本污染，DEBT0040）"


def test_t42_scan_is_runnable_and_clean_on_repo(agate_root, agate_scripts, python_exe, run_cli):
    """行为验证：本仓 `tests/` 全树扫描须 0 命中（自查命令真的可跑且当前干净）。

    与上三条（文档断言）合起来才完整：文档要求 + 命令真能跑通、当前真的干净。
    若本仓自己都命中，则该自查会变成噪声（`bdd-8` 会先红）。
    """
    result = run_cli(
        python_exe, str(agate_scripts / "check-platform-assumptions.py"), str(agate_root / "tests")
    )
    assert result.returncode == 0, f"本仓 tests/ 扫描非 0 命中：{result.output[:400]}"


# ---- DEBT0040 防复发：测试不得把**仓库内路径**当账本目录 ----
#
# 缺陷形态（TAG0034 实测）：某测试真实调用 `agate_common.append_event`，且 `task_dir` 指向
# **仓库内**路径，把事件追加进**别的任务**已提交的 `gate-events.jsonl`——judge 在 fresh
# context 跑全量 pytest 时污染了 TAG0030/0032/0033 的账本。
#
# ⚠️ **设计教训（独立评审实测指出，初版因此失效）**：初版哨兵用
# `git status --porcelain` 读**当前**脏状态——那是**快照式**检查，在 CI 口径 `-n auto`
# （xdist 多 worker）下**哨兵常先于污染者执行** ⇒ 污染发生时它仍 PASS（实测复现）。
# 快照式检查的两个后果：① 顺序依赖，不可作为 CI 兜底；② 只认 `gate-events.jsonl`
# 一种文件名，注入 `active-tasks.md` / `.state.yaml` 变脏时**均漏报**（评审实测）。
#
# 现改为**静态检查**（与执行顺序无关）：扫测试源码，禁止把**仓库内路径**直接传给
# 账本/状态写入函数。这才是可稳定兜底的判据。
#
# 范围（按评审建议如实收窄，不再声称"等价于关闭 DEBT0040"）：本检查覆盖
# 「测试以仓库内路径调用写函数」这一**根因**；已提交状态文件共 68 个
# （`gate-events.jsonl` / `active-tasks.md` / `.state.yaml` 三族），其**事后**是否被写脏，
# 自 DEBT0040 ③ 起由 CI 兜底承担（`agate/scripts/check-ledger-pollution.py`，挂 pytest job 内、
# 全量测试之后）——本文件只负责**根因**侧（静态扫描），两者互补、不重复。

# 会把内容写进 `task_dir` 的函数（改这些函数的 task_dir 即可能写脏仓库）
_WRITER_FNS = ("append_event", "write_state_yaml", "write_gate_result")


def test_t42_tests_do_not_pass_repo_paths_to_state_writers(agate_root):
    """测试源码不得把**仓库内路径**传给账本/状态写入函数（静态判据，不受执行顺序影响）。

    允许的写法：`tmp_path` 派生路径（`td` / `tmp_path / ...`）。
    禁止的写法：把仓库根/任务目录常量（含 `agate_root`）直接传给写函数。
    """
    tests_dir = agate_root / "tests"
    offenders = []
    for py in sorted(tests_dir.rglob("*.py")):
        text = _read(py)
        for fn in _WRITER_FNS:
            for m in re.finditer(rf"{fn}\(\s*([^,)]+)", text):
                arg = m.group(1).strip()
                # 仓库内路径特征：引用 agate_root / agate_workspace / ROOT 常量，或用 ".." 上溯
                if re.search(r"agate_root|agate_workspace|\bREPO_ROOT\b|\bROOT\b", arg) or ".." in arg:
                    offenders.append(f"{py.relative_to(agate_root)}: {fn}({arg})")
    assert not offenders, (
        "以下测试把仓库内路径传给写函数（会污染已提交状态文件，DEBT0040）：\n  "
        + "\n  ".join(offenders)
    )
