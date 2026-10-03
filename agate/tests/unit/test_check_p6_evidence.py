# tests/unit/test_check_p6_evidence.py — P6 证据链检查（check-p6-evidence.py）
# （check-p6-evidence.bats 30 用例迁移，TAG0011 批次 9a）
# 被测：agate/scripts/check-p6-evidence.py TASK_DIR（exit 0/1/2；P6-acceptance.md 缺失 exit 2）。
# 流语义（P2 BLOCKER-1）：GATE P6-EVIDENCE 消息经 sys.stderr.write → 断言一律用合并流
#   result.output（等价 bats $output），未映射 .stdout。
# Pillow 可选：本批 30 用例全部 Pillow 无关——check-p6-evidence.py 调 agate-image-check.py
#   variance/ahash，缺 Pillow 时 SKIP_NO_PILLOW 走 WARNING 分支（不阻断），exit code 判定
#   不随 Pillow 安装状态变化（与 bats 原文一致，bats 也无 Pillow skip）。
# 随机字节文件用 os.urandom + write_bytes（平台无关，不写字面命中行，BDD-5）。

import base64
import os

import pytest


def _run_evidence(agate_scripts, python_exe, run_cli, td):
    return run_cli(python_exe, str(agate_scripts / "check-p6-evidence.py"), str(td))


def _write_p6(td, text):
    (td / "P6-acceptance.md").write_text(text, encoding="utf-8")


def _write_ui_p2(td, value):
    (td / "P2-design.md").write_text(
        f"---\nagent: test\n---\nui_affected: {value}\n", encoding="utf-8"
    )


@pytest.mark.windows_smoke
def test_e_1_no_p6_file_exit_2(tmp_path, agate_scripts, python_exe, run_cli):
    td = tmp_path / "task"
    td.mkdir()
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 2


def test_e_2_no_bdd_entries_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "无 BDD\n")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "无 BDD 条目" in result.output


def test_e_3_pass_missing_file_ref_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1\n")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "未能提取证据引用" in result.output


def test_e_4_pass_with_ref_and_file_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_e_5_evidence_dir_missing_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "P6-evidence" in result.output


def test_e_6_evidence_dir_empty_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    (td / "P6-evidence").mkdir()
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_e_7_normal_pass_no_ui_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result1.json)\n- PASS BDD-2 (result2.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result1.json").write_text("log\n", encoding="utf-8")
    (ev / "result2.json").write_text("log\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_e_8_ui_true_screenshots_dir_missing_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "screenshots" in result.output


def test_e_9_ui_screenshot_lt_1kb_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "login.png").write_bytes(os.urandom(100))
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "1KB" in result.output


def test_e_10_ui_screenshot_ge_1kb_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "login.png").write_bytes(os.urandom(5000))
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_e_11_multiple_extensions_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(
        td,
        "- PASS BDD-1 (result.log)\n"
        "- PASS BDD-2 (data.json)\n"
        "- PASS BDD-3 (page.html)\n"
        "- PASS BDD-4 (notes.txt)\n"
        "- PASS BDD-5 (config.yaml)\n",
    )
    ev = td / "P6-evidence"
    ev.mkdir()
    for ext in ("log", "json", "html", "txt", "yaml"):
        (ev / ("file." + ext)).write_text("content\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_e_12_ui_duplicate_screenshots_md5_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n- PASS BDD-2 (screenshots/dashboard.png)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    content = base64.b64encode(os.urandom(5000)).decode("ascii")
    (shots / "login.png").write_text(content, encoding="utf-8")
    (shots / "dashboard.png").write_text(content, encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "md5" in result.output or "重复" in result.output


def test_e_14_pass_ref_with_extra_content_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (result.png, vision: OK)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.png").write_text("log\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_evid_ext_1_pdf_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (report.pdf)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "report.pdf").write_text("pdf content\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_evid_ext_2_jpeg_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1 (photo.jpeg)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "photo.jpeg").write_text("jpeg content\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_evid_ext_3_comma_separated_refs_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: works (screenshots/a.png, screenshots/b.png)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "a.png").write_text("a\n", encoding="utf-8")
    (shots / "b.png").write_text("b\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_evid_ext_4_nested_parens_annotation_is_boundary(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: works (screenshots/b07.png — element: .katex nth(1))\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "b07.png").write_text("img\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    # 决策 A1（独立评审裁定）：组内容「path — 注释」整体不是路径 ⇒ 整组丢弃 ⇒ 判缺引用。
    # 实测依据：两仓含内层括号的括号组 26 处，逐一 isfile 复核 **26/26 命中 0**；
    # 评审三次构造反例均失败 ⇒ A2（加规则覆盖）实测收益为 0。
    assert result.returncode == 1, "A1：注释组不构成引用 ⇒ 该行应判缺引用"
    assert "未能提取证据引用" in result.output


def test_evid_ext_5_version_parens_not_a_reference(task_dir, agate_scripts, python_exe, run_cli):
    """版本号括号 `(v2.0)` **不是**证据引用 ⇒ 该行判缺引用（exit 1）。

    **2026-10-03 改名并反转断言**（随「决策 B1：放弃宽松匹配」）：
    原用例名 `..._exit_0` 且断言 exit 0，其成立前提是**旧正则**
    `\\([^()]*[^()\\s]\\.[a-zA-Z0-9]+[^)]*\\)` —— 它只要求括号内有「某段.扩展名」形态，
    **对 `(v2.0)` 也命中**（实测 `命中=True`）。那是**过宽**：`v2.0` 是版本号，不是证据。

    **实测依据**：两仓真实数据中「括号内像版本号且被旧正则命中」的有 **18 处**——
    旧规则把这些行当作"已有证据引用"而放行。新规则要求扩展名**以字母开头**
    （排除 `v2.0` / `v0.99.0` / `EC.16`），这 18 处不再被误认为引用。

    本用例现与既有兄弟用例 `test_evid_ext_6_no_path_exit_1`（无引用 ⇒ exit 1）同向。
    """
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: upgraded (v2.0)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("some evidence\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1, "版本号不是证据引用 ⇒ 该行应判缺引用"
    assert "未能提取证据引用" in result.output


def test_evid_ext_6_no_path_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "---\nagent: test\n---\n- PASS BDD-1: works (no reference here)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("some evidence\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "未能提取证据引用" in result.output


def test_evid_ext_7_existing_extensions_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(
        td,
        "---\nagent: test\n---\n"
        "- PASS BDD-1 (result.png)\n"
        "- PASS BDD-2 (photo.jpg)\n"
        "- PASS BDD-3 (output.log)\n"
        "- PASS BDD-4 (data.json)\n"
        "- PASS BDD-5 (page.html)\n"
        "- PASS BDD-6 (notes.txt)\n"
        "- PASS BDD-7 (config.yaml)\n"
        "- PASS BDD-8 (config2.yml)\n",
    )
    ev = td / "P6-evidence"
    ev.mkdir()
    for f in (
        "result.png", "photo.jpg", "output.log", "data.json",
        "page.html", "notes.txt", "config.yaml", "config2.yml",
    ):
        (ev / f).write_text("content\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_e_13_ui_different_screenshots_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n- PASS BDD-2 (screenshots/dashboard.png)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "login.png").write_bytes(os.urandom(5000))
    (shots / "dashboard.png").write_bytes(os.urandom(5000))
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_evidence_no_ref_detail_1_has_specific_pass_lines(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1\n- PASS BDD-2 (result.json)\n- PASS BDD-3\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text("log\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "  - - PASS BDD-1" in result.output
    assert "  - - PASS BDD-3" in result.output


def test_evidence_empty_detail_1_has_basename(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/tiny.txt)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    (shots / "tiny.txt").write_bytes(os.urandom(100))
    (td / "P6-evidence" / "real.json").write_text('{"ok":true}\n', encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "  - tiny.txt" in result.output


def test_evidence_md5_detail_1_has_basenames(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/a.png)\n- PASS BDD-2 (screenshots/b.png)\n")
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    content = base64.b64encode(os.urandom(5000)).decode("ascii")
    (shots / "a.png").write_text(content, encoding="utf-8")
    (shots / "b.png").write_text(content, encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "  - a.png" in result.output
    assert "  - b.png" in result.output


def test_evidence_md5_detail_2_same_content_reported(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(
        td,
        "- PASS BDD-1 (screenshots/login-page.png)\n"
        "- PASS BDD-2 (screenshots/dashboard-view.png)\n",
    )
    shots = td / "P6-evidence" / "screenshots"
    shots.mkdir(parents=True)
    content = base64.b64encode(os.urandom(5000)).decode("ascii")
    (shots / "login-page.png").write_text(content, encoding="utf-8")
    (shots / "dashboard-view.png").write_text(content, encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "  - login-page.png" in result.output
    assert "  - dashboard-view.png" in result.output


def test_e_15_ui_true_all_text_exit_1(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (analysis.md)\n- PASS BDD-2 (notes.txt)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "analysis.md").write_text("source code analysis\n", encoding="utf-8")
    (ev / "notes.txt").write_text("manual notes\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "全是纯文本" in result.output


def test_e_16_ui_true_has_json_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (result.json)\n- PASS BDD-2 (notes.txt)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text('{"status":"pass"}\n', encoding="utf-8")
    (ev / "notes.txt").write_text("supplementary notes\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_e_17_ui_false_all_text_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_ui_p2(td, "false")
    _write_p6(td, "- PASS BDD-1 (analysis.md)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "analysis.md").write_text("text analysis\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_9_chinese_filename_exit_0(task_dir, agate_scripts, python_exe, run_cli):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (截图验证通过.png)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "截图验证通过.png").write_text("img\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_bdd_10_no_extension_still_blocked_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_p6(td, "- PASS BDD-1 (见截图)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "截图.png").write_text("img\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1
    assert "未能提取证据引用" in result.output


# ========== 批次 9c：TAG0006 UI/UX 机制 P6 证据用例（BDD-9/10/13/14/17） ==========
# 新增行为（P4 实现后落于 check-p6-evidence.py）：
#   * P1 vision 三态读取：vision=GAP 时校验"人工复核记录文件"被 PASS 引用（BDD-9，§2.8）
#   * 证据形式按渲染形态识别：shape=render_component → frames/renders/-tN 目录/后缀识别 +
#     渲染输出对比缺 diff.json 拦截（BDD-17，§2.16）
#   * avg-hash 雷同从 WARNING 升级为"降级待复核"：有"雷同截图复核/人工复核记录"放行、
#     无则 exit 1（BDD-14，§2.13）+ 时序截图 -tN 按同 BDD 组（bdd-id 前缀）豁免相邻样本（BDD-17）
# 平台无关：PNG 用 PIL 生成且 pytest.importorskip("PIL.Image") 包裹（无 Pillow 整函数 skip）；
# 随机字节证据 os.urandom + write_bytes；tmp_path 由 task_dir 提供。
# 前置门禁（P2 §2.13）：ahash 用例的 PNG 必须 >1KB 且像素方差 ≥50——_png_ok() 显式断言。


def _write_vision_p1(td, status=None, shape=None):
    """P1-requirements.md：frontmatter 形态字段（可选） + capability_requirements yaml 围栏块（可选）。"""
    fm = "---\nagent: test\n---\n"
    if shape:
        fm = fm.replace("---\n", f"---\nui_render_shape: {shape}\n", 1)
    body = fm + "\n"
    if status is not None:
        body += (
            "```yaml\n"
            "capability_requirements:\n"
            "  - need: visual-analysis\n"
            f"    status: {status}\n"
            "```\n"
        )
    (td / "P1-requirements.md").write_text(body, encoding="utf-8")


def _write_review_file(td, name="review-gap1.md"):
    (td / name).write_text(
        "复核人: 张三\n复核时间: 2026-08-17\n结论: 人工复核通过\n", encoding="utf-8"
    )


def _make_png(path, seed, size=(96, 96), compress=6):
    """PIL 生成非纯色噪声 PNG（同 seed 同像素；不同 compress_level → md5 不同、ahash 相同）。"""
    from PIL import Image as PILImage

    rng = __import__("random").Random(seed)
    img = PILImage.new("RGB", size)
    img.putdata(
        [(rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255)) for _ in range(size[0] * size[1])]
    )
    img.save(path, format="PNG", compress_level=compress)


def _png_ok(path):
    """验证 ahash 前置门禁：文件 >1KB 且像素方差 ≥50（P2 §2.13）。"""
    from PIL import Image as PILImage

    if os.path.getsize(path) <= 1024:
        return False
    img = PILImage.open(path).convert("L")
    px = list(img.tobytes())
    mean = sum(px) / len(px)
    variance = sum((p - mean) ** 2 for p in px) / len(px)
    return variance >= 50


def test_vision_gap_1_evidence_manual_review_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, status="GAP")
    _write_ui_p2(td, "true")
    _write_p6(
        td,
        "- PASS BDD-1 (screenshots/login.png) (manual-review: review-gap1.md)\n",
    )
    ev = td / "P6-evidence"
    (ev / "screenshots").mkdir(parents=True)
    (ev / "screenshots" / "login.png").write_bytes(os.urandom(5000))
    _write_review_file(td)
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_vision_gap_2_evidence_missing_review_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, status="GAP")
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (screenshots/login.png)\n")
    ev = td / "P6-evidence"
    (ev / "screenshots").mkdir(parents=True)
    (ev / "screenshots" / "login.png").write_bytes(os.urandom(5000))
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_vision_docs_1_verifier_has_triple_state(agate_root):
    content = (agate_root / "assets" / "execution-roles" / "verifier.md").read_text(encoding="utf-8")
    assert "available" in content
    assert "supplementable" in content
    assert "GAP" in content


def test_vision_docs_2_p6_card_real_analysis(agate_root):
    content = (agate_root / "phase-cards" / "P6-acceptance.md").read_text(encoding="utf-8")
    assert "真实视觉分析" in content


def test_vision_docs_3_input_state_review(agate_root):
    verifier = (agate_root / "assets" / "execution-roles" / "verifier.md").read_text(encoding="utf-8")
    p6_card = (agate_root / "phase-cards" / "P6-acceptance.md").read_text(encoding="utf-8")
    assert "人工复核" in verifier
    assert "输入态" in verifier
    assert "人工复核" in p6_card
    assert "输入态" in p6_card


def test_render_evid_1_frame_sequence_recognized_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, shape="render_component")
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-16 (frames/bdd16-01.png, frames/bdd16-02.png)\n")
    frames = td / "P6-evidence" / "frames"
    frames.mkdir(parents=True)
    (frames / "bdd16-01.png").write_bytes(os.urandom(2000))
    (frames / "bdd16-02.png").write_bytes(os.urandom(2000))
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_render_evid_2_render_output_compare_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, shape="render_component")
    _write_ui_p2(td, "true")
    _write_p6(
        td,
        "- PASS BDD-1 (renders/bdd1-a-actual.png, renders/bdd1-a-diff.json)\n",
    )
    renders = td / "P6-evidence" / "renders"
    renders.mkdir(parents=True)
    (renders / "bdd1-a-actual.png").write_bytes(os.urandom(2000))
    (renders / "bdd1-a-diff.json").write_text(
        '{"pixel_diff_ratio": 0.05, "average_hash_distance": 4}\n', encoding="utf-8"
    )
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_render_evid_3_frame_seq_pure_text_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, shape="render_component")
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-16 (analysis.md)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "analysis.md").write_text("text analysis\n", encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_render_evid_4_shape_decl_layout_no_frames_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, shape="layout")
    _write_ui_p2(td, "true")
    _write_p6(td, "- PASS BDD-1 (result.json)\n")
    ev = td / "P6-evidence"
    ev.mkdir()
    (ev / "result.json").write_text('{"status": "pass"}\n', encoding="utf-8")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_render_diff_1_missing_diff_json_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, shape="render_component")
    _write_ui_p2(td, "true")
    _write_p6(
        td,
        "- PASS BDD-1 (renders/bdd1-a-actual.png, renders/bdd1-a-reference.png)\n",
    )
    renders = td / "P6-evidence" / "renders"
    renders.mkdir(parents=True)
    (renders / "bdd1-a-actual.png").write_bytes(os.urandom(2000))
    (renders / "bdd1-a-reference.png").write_bytes(os.urandom(2000))
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_render_diff_2_diff_json_with_metric_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    td = task_dir()
    _write_vision_p1(td, shape="render_component")
    _write_ui_p2(td, "true")
    _write_p6(
        td,
        "- PASS BDD-1 (renders/bdd1-a-actual.png, renders/bdd1-a-reference.png, renders/bdd1-a-diff.json)\n",
    )
    renders = td / "P6-evidence" / "renders"
    renders.mkdir(parents=True)
    (renders / "bdd1-a-actual.png").write_bytes(os.urandom(2000))
    (renders / "bdd1-a-reference.png").write_bytes(os.urandom(2000))
    (renders / "bdd1-a-diff.json").write_text(
        '{"pixel_diff_ratio": 0.05}\n', encoding="utf-8"
    )
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def _write_ahash_case(td, pass_lines, review_record=None):
    """构造 PASS 行 + 可选复核记录（截图目录建立；文件由调用方显式生成）。"""
    shots_dir = td / "P6-evidence" / "screenshots"
    shots_dir.mkdir(parents=True)
    lines = pass_lines.splitlines()
    if review_record:
        lines.append(review_record)
    _write_p6(td, "\n".join(lines) + "\n")


def _make_duplicate_pair(shots, name_a, name_b):
    """同 seed（同视觉内容）不同 compress（不同字节 md5）→ ahash 相同、md5 不同。"""
    _make_png(shots / name_a, seed=7, compress=1)
    _make_png(shots / name_b, seed=7, compress=9)


def test_ahash_1_duplicate_with_review_record_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    pytest.importorskip("PIL.Image")
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_ahash_case(
        td,
        "- PASS BDD-1 (screenshots/bdd1-shot.png)\n- PASS BDD-2 (screenshots/bdd2-shot.png)",
        review_record="- 雷同截图复核: 已人工复核，确为不同操作但视觉相近",
    )
    shots = td / "P6-evidence" / "screenshots"
    _make_duplicate_pair(shots, "bdd1-shot.png", "bdd2-shot.png")
    assert _png_ok(shots / "bdd1-shot.png")
    assert _png_ok(shots / "bdd2-shot.png")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "人工复核记录" in result.output


def test_ahash_2_duplicate_no_review_record_exit_1(
    task_dir, agate_scripts, python_exe, run_cli
):
    pytest.importorskip("PIL.Image")
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_ahash_case(
        td,
        "- PASS BDD-1 (screenshots/bdd1-shot.png)\n- PASS BDD-2 (screenshots/bdd2-shot.png)",
    )
    shots = td / "P6-evidence" / "screenshots"
    _make_duplicate_pair(shots, "bdd1-shot.png", "bdd2-shot.png")
    assert _png_ok(shots / "bdd1-shot.png")
    assert _png_ok(shots / "bdd2-shot.png")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 1


def test_ahash_3_no_duplicate_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    pytest.importorskip("PIL.Image")
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_ahash_case(
        td,
        "- PASS BDD-1 (screenshots/bdd1-shot.png)\n- PASS BDD-2 (screenshots/bdd2-shot.png)",
    )
    shots = td / "P6-evidence" / "screenshots"
    _make_png(shots / "bdd1-shot.png", seed=1, compress=1)
    _make_png(shots / "bdd2-shot.png", seed=2, compress=1)
    assert _png_ok(shots / "bdd1-shot.png")
    assert _png_ok(shots / "bdd2-shot.png")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0


def test_time_seq_1_adjacent_time_shots_exempt_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    pytest.importorskip("PIL.Image")
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_ahash_case(td, "- PASS BDD-7 (screenshots/bdd7-t1.png, screenshots/bdd7-t2.png)")
    shots = td / "P6-evidence" / "screenshots"
    _make_png(shots / "bdd7-t1.png", seed=7, compress=1)
    _make_png(shots / "bdd7-t2.png", seed=7, compress=9)
    assert _png_ok(shots / "bdd7-t1.png")
    assert _png_ok(shots / "bdd7-t2.png")
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "average hash 相同" not in result.output


# B2 回归（TAG0006 修复轮）：screenshots/ 混入 >1KB 非图片文件（.log）且其文件名排序落在
# 两个同 BDD 时序样本之间时，avg-hash 文件名↔哈希必须仍一一对应（统一 _is_image 过滤口径）。
# 修复前 zip(sorted(glob), ahash_lines) 会因非图片无 ahash 行而错位：.log 顶掉真样本，
# 使同 BDD 时序样本（应豁免）被误判为跨组雷同 → 对合法渲染/时序任务误 exit 1。
# 本测试：修复后真时序重复对被正确豁免（exit 0）；修复前会误拦（exit 1）。
def test_ahash_4_nonimage_file_misalign_temporal_exempt_exit_0(
    task_dir, agate_scripts, python_exe, run_cli
):
    pytest.importorskip("PIL.Image")
    td = task_dir()
    _write_ui_p2(td, "true")
    _write_ahash_case(td, "- PASS BDD-7 (screenshots/bdd7-t1.png, screenshots/bdd7-t2.png)")
    shots = td / "P6-evidence" / "screenshots"
    _make_png(shots / "bdd7-t1.png", seed=7, compress=1)
    _make_png(shots / "bdd7-t2.png", seed=7, compress=9)
    (shots / "bdd7-t1a.log").write_bytes(os.urandom(3600))
    assert _png_ok(shots / "bdd7-t1.png")
    assert _png_ok(shots / "bdd7-t2.png")
    assert os.path.getsize(shots / "bdd7-t1a.log") > 1024
    result = _run_evidence(agate_scripts, python_exe, run_cli, td)
    assert result.returncode == 0
    assert "average hash 相同" not in result.output
