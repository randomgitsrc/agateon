# tests/unit/test_doc_sweep.py — TAG0037 P3 组 C（批 F2：文档面清扫 + 发布清单 + 脚本索引）
# 被测：README.md / README.zh-CN.md / agate/adr.md / agate/orchestrator-template.md / agate/assets/templates/handoff-template.md /
#       根 AGENTS.md「版本发布清单」/ agate/scripts/README.md / 两处既有测试的头注与 docstring。
# BDD 映射：BDD-39 ⑥⑦⑧（⑨ 的 R 清零集合由 regression/test_no_legacy_residue.py 逐文件断言）、
#           BDD-40 静态部分（遗留的 `~/.agate` 协议根路径改为解析出的根；动态部分见 test_setup_agate_dir.py）、
#           BDD-21（tag 与 Release 双轨：发布清单含 Release 校验与补救步骤，口径见 P2 T-13）、
#           BDD-49 ④（新增脚本已登记 agate/scripts/README.md 脚本索引；consistency / ruff / shellcheck 三条是命令验收，见 P3-test-cases.md §7）。
# 口径：断言关键词 / 结构 / 不含某模式，不写死易变文案；旧称字面量一律拼接构造（本文件不属 BDD-37 白名单，源码不得直接含旧称字面量）。
# 平台无关：纯文本 + git ls-files 只读。
# 当前红灯（B 类，断言失败）：README 仍写"clone 后把 ~/.agate 指向协议本体"；summary / handoff 模板仍写死 ~/.agate/…；发布清单无 Release 步骤；
#   scripts/README.md 尚未登记 agate_package.py / agate-release.py。

import ast
import re
import subprocess

import pytest

import helpers_tag_repo as H

ROOT = H.REPO_ROOT
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_OLD_TERMS = ("use_" + "legacy", "legacy" + " 软链", "单" + "软链", "软链" + "兜底")


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def _section(text, title_pat, level):
    lines = text.splitlines()
    in_fence, heads = False, []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        m = None if in_fence else _HEADING.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    for idx, (ln, lv, title) in enumerate(heads):
        if lv == level and re.search(title_pat, title):
            end = len(lines)
            for ln2, lv2, _t in heads[idx + 1 :]:
                if lv2 <= lv:
                    end = ln2
                    break
            return "\n".join(lines[ln:end])
    return ""


# ---------------------------------------------------------------------------
# BDD-39 ⑥  README / README.zh-CN 首推装法改为版本管理布局
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "rel,title_pat,layout_word",
    [
        ("README.md", r"^Quick start", r"[Vv]ersion"),
        ("README.zh-CN.md", r"^快速开始", r"版本管理"),
    ],
)
def test_bdd_39_6_readme_quick_start_enters_versioned_layout(rel, title_pat, layout_word):
    """BDD-39 ⑥：README 首推装法改为版本管理布局——`curl | bash` 仍写，且步骤 1 注明其语义为进入版本管理布局；
    不再写"把 ~/.agate 指向协议本体"的旧装法（旧称清零由 BDD-37 R 集合逐文件核对）。"""
    sec = _section(_read(rel), title_pat, 2)
    assert sec, f"{rel} 缺快速上手章节"
    step1 = re.split(r"\n\s*2\.\s", sec, maxsplit=1)[0]
    assert re.search(r"curl[^\n]*install\.sh", step1), "一键安装命令 curl … install.sh 应保留"
    assert re.search(layout_word, step1), f"步骤 1 应注明 install.sh 进入版本管理布局（/{layout_word}/）"
    assert not re.search(r"point\s+`?~/\.agate`?\s+at|指向协议本体|指向仓库", step1), "不应再写把 ~/.agate 指向协议本体 / 仓库的旧装法"


# ---------------------------------------------------------------------------
# BDD-39 ⑦⑧  其余文件的表述
# ---------------------------------------------------------------------------


def test_bdd_39_7_adr_009_marked_as_superseded_by_v0730():
    """BDD-39 ⑦ / BDD-37 W：ADR-009 历史条目保留，并加「已被 v0.73.0 取代」注记（旧布局部分）。"""
    sec = _section(_read("agate/adr.md"), r"^ADR-009", 2)
    assert sec, "agate/adr.md 缺 ADR-009"
    assert "v0.73.0" in sec and "取代" in sec, "ADR-009 应注记旧软链布局部分已被 v0.73.0 取代"


def test_bdd_39_8_existing_tests_header_and_docstring_wording_updated():
    """BDD-39 ⑧：test_agate_version_resolve.py 头注与 test_resolve_terminal_failure_fail_closed 的 docstring 不再含旧布局字样。
    （test_dsh_preset.py:222 注释的旧称由 BDD-37 R 集合断言。）"""
    src = _read("agate/tests/unit/test_agate_version_resolve.py")
    header = "\n".join(src.splitlines()[:10])
    for term in _OLD_TERMS:
        assert term not in header, f"test_agate_version_resolve.py 头注仍含旧称 {term!r}"
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "test_resolve_terminal_failure_fail_closed"), None)
    assert fn is not None, "test_resolve_terminal_failure_fail_closed 应保留（BDD-28 (d) 终态 fail-closed）"
    doc = ast.get_docstring(fn) or ""
    assert not re.search("legacy", doc, re.I), f"docstring 仍含旧布局字样 legacy: {doc!r}"


# ---------------------------------------------------------------------------
# BDD-40  「~/.agate 当协议根」的遗留路径改为解析出的根（静态部分）
# ---------------------------------------------------------------------------

_LEGACY_ROOT_PATH = re.compile(r"~/\.agate/(AGENTS|orchestrator-template|WORKFLOW|assets|phase-cards|rules)")
# 历史 / 叙事 / 反例说明文件（允许保留旧路径字面量，理由逐项列出）
_ROOT_PATH_WHITELIST = {
    "CHANGELOG.md": "append-only 发布记录",
    "agate/UPGRADING.md": "历史版本节",
    "agate/adr.md": "历史决策记录",
    "agate-workspace/debt/tech-debt.md": "已 closed 债务叙事",
    "docs/guides/worktree-dogfooding-guide.md": "明确解释「为什么不能直接写该路径」的反例说明",
}
_EXCLUDED_COMPONENTS = ("archived", "node_modules")
_EXCLUDED_PREFIXES = ("agate-workspace/tasks/", "docs/reviews/", "docs/design-notes/")


def _tracked_text_files():
    proc = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, timeout=120)
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")
    for rel in proc.stdout.decode("utf-8", "surrogateescape").split("\0"):
        if not rel:
            continue
        parts = rel.split("/")
        if any(p in _EXCLUDED_COMPONENTS for p in parts[:-1]) or any(rel.startswith(p) for p in _EXCLUDED_PREFIXES):
            continue
        if parts[-1] in ("package-lock.json",):
            continue
        try:
            raw = (ROOT / rel).read_bytes()
        except OSError:
            continue
        if b"\0" in raw[:8192]:
            continue
        yield rel, raw.decode("utf-8", "replace")


def test_bdd_40_no_stale_protocol_root_paths_outside_history():
    """BDD-40：grep `~/.agate/(AGENTS|orchestrator-template|WORKFLOW|assets|phase-cards|rules)` 在非历史叙事文件中 0 命中
    （版本布局下这些路径不存在；协议根是 $AGATE_DIR 或 ~/.agate/current/agate）。"""
    offenders = sorted(
        rel for rel, text in _tracked_text_files() if rel not in _ROOT_PATH_WHITELIST and _LEGACY_ROOT_PATH.search(text)
    )
    assert offenders == [], f"遗留的 ~/.agate 协议根路径: {offenders}"


def test_bdd_40_handoff_template_uses_agate_dir_or_current_path():
    """BDD-40：handoff-template 的 orchestrator 注册行改用 $AGATE_DIR（或 ~/.agate/current/agate）。"""
    text = _read("agate/assets/templates/handoff-template.md")
    assert "~/.agate/" + "orchestrator-template.md" not in text
    assert "$AGATE_DIR" in text or "~/.agate/current/agate" in text


def test_bdd_40_orchestrator_template_fallback_is_current_agate():
    """BDD-40：orchestrator-template 的 {agate_root} 兜底为 ~/.agate/current/agate（不再是「默认 ~/.agate」）。"""
    text = _read("agate/orchestrator-template.md")
    assert "~/.agate/current/agate" in text
    assert not re.search(r"默认\s*`?~/\.agate`?(?![/\w])", text), "不应再写「脚本不可用则默认 ~/.agate」"


# ---------------------------------------------------------------------------
# BDD-21  tag 与 Release 双轨不失配（AGENTS.md「版本发布清单」）
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def release_checklist():
    return _section(_read("AGENTS.md"), r"版本发布清单", 2)


def test_bdd_21_checklist_verifies_release_and_its_assets(release_checklist):
    """BDD-21：发布清单在 push tag 之后含 Release 校验步骤（`gh release view v<版本>`）并断言 3 个 tarball 资产
    （本体 + 两平台 offline；口径 T-13：3 个 tarball 名 ⊆ 资产集合，另有 SHA256SUMS，不断言总数恰为 3）。"""
    assert release_checklist, "AGENTS.md 缺「版本发布清单」"
    assert re.search(r"gh release view\s+v", release_checklist), "缺 `gh release view v<版本>` 校验步骤"
    for token in ("offline", "linux-x86_64", "windows-x86_64"):
        assert token in release_checklist, f"发布清单应列出资产 {token}"
    assert re.search(r"agateon-v\S*\.tar\.gz", release_checklist), "应给出本体资产名 agateon-v<版本>.tar.gz"
    # 顺序：Release 校验位于 push tag 步骤之后
    assert release_checklist.index("git push origin") < release_checklist.index("gh release view")


def test_bdd_21_checklist_has_remediation_for_tag_pushed_but_release_missing(release_checklist):
    """BDD-21：含"tag 已推而 Release 缺失"的补救步骤——用本地打包脚本重建并 gh release create（workflow 无 workflow_dispatch）。"""
    assert "gh release create" in release_checklist
    assert "agate-release.py" in release_checklist
    assert "workflow_dispatch" in release_checklist, "应说明补救原因：release workflow 无 workflow_dispatch"


def test_bdd_21_g5_final_verification_includes_release_existence(release_checklist):
    """BDD-21：G-5 最终验证条目同步含 Release 存在性。"""
    g5 = [ln for ln in release_checklist.splitlines() if "G-5" in ln]
    assert g5, "发布清单应保留 G-5 条目"
    assert re.search(r"gh release view|Release[^\n]{0,6}(存在|资产)|(存在|资产)[^\n]{0,6}Release", g5[0]), (
        f"G-5 条目应含 Release 存在性校验（gh release view / Release 存在）: {g5[0]!r}"
    )


def test_p2_release_checklist_recommends_tag_protection(release_checklist):
    """P2 §3.6 / cso F-14：发布清单建议为 v* tag 启用保护 / Ruleset（只允许维护者创建；非代码项，文档如实记录）。"""
    assert re.search(r"Ruleset|tag 保护|tag protection", release_checklist, re.I)


# ---------------------------------------------------------------------------
# BDD-49 ④  新增脚本已登记 scripts/README.md 脚本索引
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("script", ["agate_package.py", "agate-release.py"])
def test_bdd_49_4_new_scripts_registered_in_scripts_readme(script):
    """BDD-49 ④：本任务新增脚本（打包库 / Release CLI）登记在 agate/scripts/README.md 脚本索引表。
    （其余 BDD-49 项 = 命令验收：consistency --strict-errors-only / ruff / shellcheck，见 P3-test-cases.md §7。）"""
    text = _read("agate/scripts/README.md")
    assert re.search(r"^\|\s*`" + re.escape(script) + r"`", text, re.M), f"scripts/README.md 脚本索引缺 `{script}` 行"
