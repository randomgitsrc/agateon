#!/usr/bin/env python3
"""check-p6-evidence.py — P6 证据格式检查（P1.7）

从 check-p6-evidence.sh 迁移（TAG0010 批次 2d）。CLI 契约与 sh 版等价：
  check-p6-evidence.py TASK_DIR
exit 0 = 通过; exit 1 = 真失败（证据目录为空 / 无 BDD / md5 重复——应阻断）
exit 2 = WARNING（低方差/小图/无 P6 文件——不阻断，提醒人工确认）

检查 P6-evidence/ 目录非空 + UI 截图实质检查（R1a）。查询类 BDD 可不截图，
但须有断言记录证据（response.json / assert.log 等）。含像素方差检测
（低方差/疑似占位图, WARNING）+ md5 去重（阻断）+ average hash 相似度（WARNING）。

- grep -cE '^\\s*- (PASS|FAIL)' → re.findall(MULTILINE) 计数（逐行语义一致）
- grep -E '^\\s*- PASS\\b' 逐行 + S2 结构判定正则 → re.findall + ref_re.search
- find ... -type f -not -name '.*'（递归）→ _find_files（os.walk，隐藏名跳过）
- stat -c%s / stat -f%z → os.path.getsize（失败回退 0）
- file -b --mime-type（有 file 时）/ magic bytes fallback → _is_image
- md5sum | sort | uniq → hashlib.md5 + Counter 等价
- 依赖既有 py：agate-md-field-get.py（env FILE）/ agate-image-check.py
  （env IMG_PATH / env SCREENSHOTS_DIR），均 sys.executable subprocess +
  $(...) 剥尾换行 → .rstrip("\n")
"""

import glob
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from agate_common import (
        extract_evidence_refs,
        is_new_task_for_evidence_ref,
        read_vision_tri_state,
        resolve_evidence,
    )
except ImportError:
    read_vision_tri_state = None
    resolve_evidence = None
    extract_evidence_refs = None
    is_new_task_for_evidence_ref = None


def _run_script(script, args, env_extra):
    """调既有 py 工具（sys.executable subprocess，env 传参），返回 (stdout 去尾换行, returncode)。

    sh 侧 `$(...) 2>/dev/null || echo ...` 的失败回退语义由调用方按 returncode 决定。
    """
    env = dict(os.environ)
    env.update(env_extra)
    try:
        proc = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, script), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env,
        )
    except OSError:
        return "", 1
    return (proc.stdout or "").rstrip("\n"), proc.returncode


def _find_files(base):
    """find base -type f -not -name '.*'（递归，排除隐藏名文件）等价。"""
    files = []
    for _root, _dirs, names in os.walk(base):
        for name in names:
            if name.startswith("."):
                continue
            files.append(os.path.join(_root, name))
    return files


def _is_image(path):
    """file 命令可用时仅用 mime 判定；否则 magic bytes fallback（PNG/JPEG/GIF/WebP）。"""
    if shutil.which("file"):
        try:
            proc = subprocess.run(
                ["file", "-b", "--mime-type", path],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        except OSError:
            return False
        return proc.stdout.startswith("image/")
    try:
        with open(path, "rb") as f:
            magic = f.read(12)
    except OSError:
        return False
    if magic[:4] == b"\x89PNG":
        return True
    if magic[:2] == b"\xff\xd8":
        return True
    if magic[:4] == b"GIF8":
        return True
    return bool(magic[:4] == b"RIFF" and len(magic) >= 12 and magic[8:12] == b"WEBP")


def _md5_entries(base):
    """find ... -exec md5sum {} \\; 等价（(hash, 全路径) 列表，失败跳过）。"""
    entries = []
    for f in _find_files(base):
        try:
            with open(f, "rb") as fh:
                digest = hashlib.md5(fh.read()).hexdigest()
        except OSError:
            continue
        entries.append((digest, f))
    return entries


def _ahash_group(name):
    """雷同判定分组键 = bdd-id 前缀（P2 §2.16）。

    帧序列 `{bdd-id}-NN.png` 与时序截图 `{bdd-id}-tN.png` 剥掉末尾数字/时刻后缀
    归入同一组（`bdd16-01.png`/`bdd7-t2.png` → `bdd16`/`bdd7`）；无时序后缀的
    证据名（`bdd1-shot.png`）原样返回（独立组）。
    """
    m = re.match(r"^(.*?)-(?:t\d+|\d+)\.\w+$", name)
    if m:
        return m.group(1)
    return name


def _is_temporal_shot(name):
    """是否时序样本（-tN 时刻截图 / -NN 帧号），同 BDD 组内相邻样本豁免雷同判定的依据。"""
    return bool(re.search(r"-(?:t\d+|\d+)\.\w+$", name))



# ── 证据引用政策（最终裁决 §4；F2 修复：判据已抽到 agate_common，两脚本共用）───
# 本地不再重复实现 `_is_new_task_for_evidence_ref` —— 原先两脚本各写一份。
# ⚠️ F3 修复：存量任务的无引用告警以 **exit 2** 收尾（脚本 README 规定 2=WARNING），
#   否则 `pre-commit-gate.py:502` 只在 rc∈{1,2} 时打印捕获的输出 ⇒ 告警**被丢弃**。



def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-p6-evidence.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]
    p6_file = os.path.join(task_dir, "P6-acceptance.md")

    if not os.path.isfile(p6_file):
        sys.stderr.write(
            "GATE SKIP: check-p6-evidence: 无 P6-acceptance.md，证据审计无对象，未校验（exit 2）\n"
        )
        sys.exit(2)

    try:
        with open(p6_file, encoding="utf-8", errors="replace") as f:
            p6_text = f.read()
    except OSError:
        p6_text = ""

    bdd_count = len(re.findall(r"^\s*- (PASS|FAIL)", p6_text, re.MULTILINE))

    if bdd_count == 0:
        sys.stderr.write("GATE P6-EVIDENCE: P6-acceptance.md 无 BDD 条目（- PASS/- FAIL 格式）\n")
        sys.exit(1)

    evidence_dir = os.path.join(task_dir, "P6-evidence")
    _evidence_ref_warnings = []

    # 每条 PASS 行必须含文件引用。
    # **走单源提取器**（S1 + M-A）：不再自持正则——原写法只认 ASCII 括号，
    # 全角 `（）` 会被判"无引用"⇒ 假红，且与 provenance 判据分叉（ADR-014）。
    # 提取器同时覆盖：全角/半角、行中/行末、逗号分隔、以及
    # `(screenshots/b07.png — element: .katex nth(1))` 这类**带内层括号的注释**
    # （test_evid_ext_4 / test_pv_18 锁定）。
    pass_without_ref = 0
    pass_without_ref_details = ""
    for line in re.findall(r"^\s*- PASS\b.*", p6_text, re.MULTILINE):
        if not extract_evidence_refs(line):
            pass_without_ref += 1
            pass_without_ref_details += f"  - {line}\n"

    if pass_without_ref > 0:
        # 最终裁决 §4「无引用政策」：机制后新任务 exit 1，历史任务 WARNING（fail-open）。
        # ⚠️ **不得中途 sys.exit(2)**——那会跳过后面的 md5/截图/frames 检查（裁决明确约束）。
        _new_task = is_new_task_for_evidence_ref(task_dir, __file__)
        if _new_task:
            sys.stderr.write(
                f"GATE P6-EVIDENCE: 有 {pass_without_ref} 条 PASS 未能提取证据引用"
                "（每条 PASS 须引用证据文件，形式不限：截图/日志/JSON/文本）\n"
            )
            sys.stderr.write(pass_without_ref_details + "\n")
            sys.exit(1)
        # 历史任务：告警累积，检查继续跑完（exit code 在末尾统一给）
        _evidence_ref_warnings.append(
            f"GATE P6-EVIDENCE: 有 {pass_without_ref} 条 PASS 未能提取证据引用"
            "（**历史任务**，按 evidence_ref_required_since 之前的截止口径给 WARNING，不阻断）\n"
            + pass_without_ref_details
        )

    def _flush_warnings():
        """F3：任何退出路径前都先输出已累积的存量告警（防后续检查失败时丢失）。"""
        for _w in _evidence_ref_warnings:
            sys.stderr.write(_w + "\n")

    if not os.path.isdir(evidence_dir) or not os.listdir(evidence_dir):
        sys.stderr.write("GATE P6-EVIDENCE: P6-evidence/ 目录不存在或为空\n")
        sys.exit(1)

    sys.stderr.write(f"GATE P6-EVIDENCE: {bdd_count} 条 BDD，证据目录非空\n")

    # UI 截图实质检查（R1a：仅当 P6-acceptance.md 含截图引用时才检查）
    p2_file = os.path.join(task_dir, "P2-design.md")
    ui_affected = ""
    if os.path.isfile(p2_file):
        out, rc = _run_script("agate-md-field-get.py", ["ui_affected"], {"FILE": p2_file})
        if rc == 0:
            ui_affected = out

    if ui_affected == "true":
        # evidence 类型检查：ui_affected=true 时不能全是纯文本（.md/.txt）
        # 防源码分析充数——运行时工具产出天然是 .json/.log/.png/.yaml 等结构化格式
        non_text_count = 0
        for _root, _dirs, names in os.walk(evidence_dir):
            for name in names:
                if name.startswith("."):
                    continue
                if name.endswith(".md") or name.endswith(".txt"):
                    continue
                non_text_count += 1
        if non_text_count == 0:
            sys.stderr.write(
                "GATE P6-EVIDENCE: ui_affected=true 但 evidence 全是纯文本（.md/.txt），缺少运行时数据（.json/.log/.png/.yaml 等）。源码引用不算运行时证据。\n"
            )
            sys.exit(1)

        # TAG0006（BDD-9/17，P2 §2.8/§2.16）：读取 P1 的 vision 三态声明 + 渲染形态，
        # 决定 GAP 降级证据路径与证据形式（帧序列/渲染输出对比/时序截图）合法性。
        vision_state = None
        p1_shape = ""
        p1_file = os.path.join(task_dir, "P1-requirements.md")
        if os.path.isfile(p1_file):
            if read_vision_tri_state is not None:
                vision_state = read_vision_tri_state(p1_file)
            out, rc = _run_script("agate-md-field-get.py", ["ui_render_shape"], {"FILE": p1_file})
            if rc == 0:
                p1_shape = out

        # 证据形式按形态匹配（BDD-17，§2.16）：渲染组件/时序特效形态须含
        # 帧序列（frames/）/ 渲染输出对比（renders/）/ 时序截图（-tN），否则形态与证据不匹配
        if p1_shape in ("render_component", "temporal_effects"):
            has_form_evidence = False
            for f in _find_files(evidence_dir):
                rel_part = os.path.relpath(f, evidence_dir).replace("\\", "/")
                if rel_part.startswith("frames/") or rel_part.startswith("renders/"):
                    has_form_evidence = True
                    break
                if rel_part.startswith("screenshots/") and re.search(r"-t\d+\.\w+$", os.path.basename(rel_part)):
                    has_form_evidence = True
                    break
            if not has_form_evidence:
                sys.stderr.write(
                    "GATE P6-EVIDENCE: 声明渲染组件/时序特效形态（ui_render_shape）但证据不含 帧序列（frames/）/渲染输出对比（renders/）/时序截图（-tN）——证据形式与形态不匹配\n"
                )
                sys.exit(1)

        has_screenshot_ref = sum(
            1 for line in p6_text.splitlines() if "(screenshots/" in line
        )

        if has_screenshot_ref > 0:
            # TAG0006 GAP 降级链（BDD-9，§2.8）：vision=GAP 时截图 PASS 不要求 vision YAML
            # （那是 provenance R1b 的强制），但必须是"人工复核记录"证据路径——每条截图 PASS
            # 引 (manual-review: <file>) 且文件存在；缺失 → exit 1。
            if vision_state == "GAP":
                gap_review_missing = 0
                gap_review_details = ""
                for line in p6_text.splitlines():
                    if "(screenshots/" not in line:
                        continue
                    m = re.search(r"\(manual-review:\s*[^)]+\)", line)
                    if not m:
                        gap_review_missing += 1
                        gap_review_details += f"  - {line}\n"
                        continue
                    review_file = re.sub(r"^.*manual-review:\s*", "", m.group(0)).replace(")", "").strip()
                    if not os.path.isfile(os.path.join(task_dir, review_file)):
                        sys.stderr.write(
                            f"GATE P6-EVIDENCE: vision=GAP 降级路径人工复核记录文件不存在: {review_file}\n"
                        )
                        sys.exit(1)
                if gap_review_missing > 0:
                    sys.stderr.write(
                        f"GATE P6-EVIDENCE: vision=GAP（无视觉能力）降级路径要求截图 PASS 附人工复核记录引用（manual-review: <file>）——有 {gap_review_missing} 条缺复核引用\n"
                    )
                    sys.stderr.write(gap_review_details + "\n")
                    sys.exit(1)

            screenshots_dir = os.path.join(evidence_dir, "screenshots")
            if not os.path.isdir(screenshots_dir) or not _find_files(screenshots_dir):
                sys.stderr.write(
                    "GATE P6-EVIDENCE: ui_affected=true 且 PASS 引用了截图，但 P6-evidence/screenshots/ 目录不存在或为空\n"
                )
                sys.exit(1)

            empty_count = 0
            empty_details = ""
            small_image_warning = 0
            small_image_details = ""
            variance_warning = 0
            skip_checks = os.environ.get("AGATE_SKIP_IMAGE_CHECKS", "0") == "1"
            if skip_checks:
                sys.stderr.write("GATE P6-EVIDENCE WARNING: AGATE_SKIP_IMAGE_CHECKS=1，方差/相似度检测已主动跳过\n")
            else:
                for img in _find_files(screenshots_dir):
                    try:
                        size = os.path.getsize(img)
                    except OSError:
                        size = 0
                    if size <= 1024:
                        if _is_image(img):
                            small_image_warning += 1
                            small_image_details += f"  - {os.path.basename(img)}\n"
                        else:
                            empty_count += 1
                            empty_details += f"  - {os.path.basename(img)}\n"
                    variance, rc = _run_script("agate-image-check.py", ["variance"], {"IMG_PATH": img})
                    if rc != 0:
                        variance = "-1"
                    if variance == "SKIP_NO_PILLOW":
                        sys.stderr.write("GATE P6-EVIDENCE WARNING: Pillow 未安装，方差/相似度检测已跳过\n")
                        break
                    else:
                        try:
                            var_int = int(variance)
                        except ValueError:
                            var_int = -1
                        if 0 <= var_int < 50:
                            variance_warning += 1
                            sys.stderr.write(
                                f"GATE P6-EVIDENCE WARNING: {os.path.basename(img)} 像素方差 {var_int}（<50，疑似纯色/占位图，请确认非充数）\n"
                            )

            if empty_count > 0:
                sys.stderr.write(f"GATE P6-EVIDENCE: P6-evidence/screenshots/ 有 {empty_count} 个非图片文件 ≤ 1KB（疑似充数）\n")
                sys.stderr.write(empty_details + "\n")
                sys.exit(1)
            if small_image_warning > 0:
                sys.stderr.write(f"GATE P6-EVIDENCE WARNING: P6-evidence/screenshots/ 有 {small_image_warning} 个合法图片 ≤ 1KB（元素级小截图，不阻断但请确认非充数）\n")
                sys.stderr.write(small_image_details + "\n")
                sys.exit(2)

            # md5 去重（逐字节相同 → 阻断；时序/帧类跨 BDD 组逐字节相同仍硬阻断，充数防伪不放松）
            md5_entries = _md5_entries(screenshots_dir)
            md5_total = len(md5_entries)
            md5_unique = len({h for h, _ in md5_entries})
            if md5_total > md5_unique:
                md5_dupes = md5_total - md5_unique
                md5_counts = Counter(h for h, _ in md5_entries)
                md5_details = ""
                for h in sorted(h for h, c in md5_counts.items() if c > 1):
                    for path in sorted(p for hh, p in md5_entries if hh == h):
                        md5_details += f"  - {os.path.basename(path)}\n"
                sys.stderr.write(f"GATE P6-EVIDENCE: 有 {md5_dupes} 个截图文件逐字节完全相同（md5 重复，疑似同一物理文件被多条 PASS 引用充数）\n")
                sys.stderr.write(md5_details)
                sys.exit(1)

            # avg-hash 雷同 → 降级待复核（BDD-14，§2.13）：ahash 按"同 BDD 证据组（bdd-id 前缀）"
            # 分组——帧序列 {bdd-id}-NN 与时序截图 {bdd-id}-tN 组内相邻样本豁免（动画/时序正常特性），
            # 跨组/跨 BDD 雷同触发判定：有"雷同截图复核/manual-review"记录 → 放行，无 → exit 1。
            ahash_dupes = 0
            if not skip_checks:
                ahash_list, _ = _run_script("agate-image-check.py", ["ahash"], {"SCREENSHOTS_DIR": screenshots_dir})
                if "SKIP_NO_PILLOW" in ahash_list:
                    sys.stderr.write("GATE P6-EVIDENCE WARNING: Pillow 未安装，相似度检测已跳过\n")
                else:
                    ahash_lines = [ln for ln in ahash_list.splitlines() if ln]
                    # agate-image-check 的 ahash 只对"图片文件"逐行输出 hash（非图片/解码失败被
                    # suppress 不打印行）；故此处须用同一过滤口径，只对图片文件（_is_image）收集
                    # ordered 并与 ahash_lines 按位置一一对应——否则混入 >1KB 非图片文件（.log/.json）
                    # 会导致行数 < 文件数，zip 错位、哈希对错文件名、雷同分组失真。
                    ordered = [f for f in sorted(glob.glob(screenshots_dir + "/*")) if _is_image(f)]
                    groups = {}
                    for f, h in zip(ordered, ahash_lines):
                        groups.setdefault(h, []).append(os.path.basename(f))
                    for _h, names in sorted(groups.items()):
                        if len(names) < 2:
                            continue
                        prefixes = {_ahash_group(n) for n in names}
                        if len(prefixes) == 1 and all(_is_temporal_shot(n) for n in names):
                            continue  # 同 BDD 证据组相邻时刻/相邻帧 → 豁免（动画时序正常特性）
                        ahash_dupes += 1
                    if ahash_dupes > 0:
                        has_manual_review = ("雷同截图复核" in p6_text) or ("manual-review" in p6_text)
                        if not has_manual_review:
                            sys.stderr.write(
                                f"GATE P6-EVIDENCE: 有 {ahash_dupes} 组视觉高度相似截图（average hash 相同但非逐字节相同），未含人工复核记录 → 降级待复核失败\n"
                            )
                            sys.stderr.write("  请在 P6-acceptance.md 记录 雷同截图复核 或 manual-review 引用（复核人/时间/结论）；行为差异类 BDD 截图视觉相同优先改用非截图证据\n")
                            sys.exit(1)
                        sys.stderr.write(
                            f"GATE P6-EVIDENCE: 有 {ahash_dupes} 组视觉高度相似截图（average hash 相同），已降级待复核且含人工复核记录，放行\n"
                        )
            if variance_warning > 0:
                sys.stderr.write(f"GATE P6-EVIDENCE WARNING: 有 {variance_warning} 张截图像素方差 < 50（疑似纯色/占位图，请确认非充数）\n")
                sys.exit(2)

        # 帧序列 / 渲染输出对比证据引用完整性（BDD-17，§2.16）：
        #   frames/：引用文件须存在 + 帧号连续（缺口 → WARNING，verifier 复核时序采样）
        #   renders/：每条 PASS 须引 actual + diff.json（diff 为判定锚点，含量化度量字段）
        for line in p6_text.splitlines():
            if "(frames/" in line:
                frame_nums = []
                for ref in re.findall(r"frames/[^（()）\s,]+\.\w+", line):
                    if not resolve_evidence(task_dir, ref):
                        sys.stderr.write(f"GATE P6-EVIDENCE: 帧序列引用的文件不存在: {ref}\n")
                        sys.exit(1)
                    mnum = re.search(r"-(\d+)\.\w+$", os.path.basename(ref))
                    if mnum:
                        frame_nums.append(int(mnum.group(1)))
                if frame_nums and max(frame_nums) - min(frame_nums) + 1 > len(set(frame_nums)):
                    sys.stderr.write("GATE P6-EVIDENCE WARNING: 帧序列帧号不连续（存在缺口，请 verifier 复核时序采样完整性）\n")
            if "(renders/" in line:
                refs = re.findall(r"renders/[^（()）\s,]+\.\w+", line)
                has_actual = any(
                    "-actual." in os.path.basename(r) and resolve_evidence(task_dir, r)
                    for r in refs
                )
                has_diff = any(
                    "-diff.json" in os.path.basename(r) and resolve_evidence(task_dir, r)
                    for r in refs
                )
                if not (has_actual and has_diff):
                    sys.stderr.write(
                        "GATE P6-EVIDENCE: 渲染输出对比证据须引 actual 图 + diff.json（diff 度量文件为判定锚点，缺其一即不能量化判定渲染正确性）\n"
                    )
                    sys.exit(1)
                for r in refs:
                    if r.endswith("-diff.json") and os.path.isfile(os.path.join(evidence_dir, r)):
                        try:
                            with open(os.path.join(evidence_dir, r), encoding="utf-8") as fh:
                                metric = json.load(fh)
                        except Exception:
                            metric = None
                        if not isinstance(metric, dict) or not any(
                            re.search(r"ratio|diff|distance|metric|similarity|hash", str(k), re.IGNORECASE)
                            for k in metric
                        ):
                            sys.stderr.write(f"GATE P6-EVIDENCE: diff.json 缺量化度量字段（须含 pixel_diff_ratio / average_hash_distance 等）: {r}\n")
                            sys.exit(1)

    # 最终裁决 §4 + F3：存量任务的「无引用」WARNING 在此统一输出。
    # **以 exit 2 收尾**（脚本 README：2 = WARNING 不阻塞但须可见）——
    #   若维持 rc 0，`pre-commit-gate.py:502` 不会打印捕获输出 ⇒ 告警被静默丢弃（F3）。
    if _evidence_ref_warnings:
        for _w in _evidence_ref_warnings:
            sys.stderr.write(_w + "\n")
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
