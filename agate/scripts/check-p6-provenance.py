#!/usr/bin/env python3
"""check-p6-provenance.py — P6 验收客观行为审计（P2.1/P2.10 降级方案 v2）

从 check-p6-provenance.sh 迁移（TAG0010 批次 2d）。CLI 契约与 sh 版等价：
  check-p6-provenance.py TASK_DIR
exit 0 = 通过; exit 1 = 审计不通过; exit 2 = WARNING（不阻塞）

独立 CLI 模式（TAG0016 修复 A1-c，供 P8 场景单独取审计 7 判定结果）：
  check-p6-provenance.py --audit7-only TASK_DIR
只跑审计 7（audit7_p5_evidence_reuse），不跑其余六道审计。三态结果打印到 stdout，
一行，格式固定为 `AUDIT7_RESULT: <reuse_allowed|reuse_blocked|no_reuse_claim_possible>`，
供调用方 grep 提取。exit code：reuse_allowed → 0；reuse_blocked → 1；
no_reuse_claim_possible → 0（字段缺失是"无法声明复用"而非"错误"，与主流程审计 7 的静默
回退语义一致，不算失败退出码）。不带 `--audit7-only` 时的既有行为不变。

七道客观审计 + agent 字段协作规范：
  1. 证据-结论对应（1a PASS 行证据引用路径必须存在 / 1b PASS 数 ≤ 证据文件数，
     空证据拦截 / 1c 证据文件必须被至少一条 PASS 行引用，空 png 充数拦截）
  2. dispatch-context 内容约束（不含 PASS/FAIL 验收结论预判）
  3. BDD 总数自动化对照（P6 PASS+FAIL 数 ≥ P1 BDD 标题数，挑验拦截）
  4. UI vision YAML 引用（ui_affected=true 时含截图引用的 PASS 行须同时含
     (vision: ...) 引用 + YAML 存在 + summary.blocker_count == 0）
  5. 日志 EXIT_CODE 与 PASS/FAIL 声明一致性（M1.3a 约定）
  6. evidence JSON 与 P6-acceptance.md PASS/FAIL 声明一致性（P2.57）
  7. P6 引用 P5 证据的无改动校验（audit7_p5_evidence_reuse，TAG0016 BDD-12/13：读取
     .state.yaml 可选字段 p5_pass_commit，判定 p5_pass_commit..HEAD 间是否存在
     EXCLUDE_PRODUCE_PREFIX 前缀外的改动；已声明"引用 P5 证据"但判定 reuse_blocked → 拦截）

- grep -cE '^\\s*- PASS\\b' → 逐行 re.search 计数（PASS_COUNT / P6_BODY_STRICT /
  P1_BDD 均同模式）
- sed '(vision:...) 剥离 / 行末括号组提取 / 前缀 P6-evidence 剥离' → re.sub /
  re.search('\\\\([^)]+\\\\)$') / 逐前缀 re.sub
- find ... -type f -not -name '.*'（递归）→ _find_files（os.walk，隐藏名跳过）
- 依赖既有 py：agate-md-field-get.py（env FILE）/ agate-vision-blocker.py
  （env YAML_PATH）/ agate-evidence-consistency.py（env EVIDENCE_DIR + env P6_FILE），
  均 sys.executable subprocess + $(...) 剥尾换行 → .rstrip("\\n")
- get_risk_level（sh 版定义但从未调用，死代码）未迁移
"""

import glob
import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

try:
    from agate_common import (
        extract_evidence_refs,
        read_vision_tri_state,
        resolve_evidence,
        strip_fenced_blocks,
    )
except ImportError:
    read_vision_tri_state = None
    resolve_evidence = None
    extract_evidence_refs = None
    strip_fenced_blocks = None

_SKIP_AGENT_CHECK = (
    r"-dispatch-context\.md$",
    r"-dispatch-context-[^/]*\.md$",
    r"-dispatch-prompt-[^/]*\.md$",
    r"-progress\.md$",
    r"-paused-resolution\.md$",
)

# --- 审计 7：P6 引用 P5 证据的无改动校验（BDD-12/13，TAG0016 RM-AG0026）---
# P2-design.md §3.5：EXCLUDE_PRODUCE_PREFIX 已用真实 git 命令验证不匹配任何源码路径
# （agate/scripts/、agate/*.md 等协议本体路径），只匹配任务编排产出目录。
EXCLUDE_PRODUCE_PREFIX = "agate-workspace/tasks/"


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


# --- 心跳文件审计豁免登记（RM-AG0055 / TAG0028 BDD-26）---
# `.heartbeat*` 心跳文件（任务级 .heartbeat、子任务级 .heartbeat.child-{n}，命名规范见
# dispatch-protocol.md「心跳文件生命周期」节）落入 {TASK_DIR}/ 协议命名空间，但下方
# _find_files 的隐藏文件过滤（if name.startswith("."): continue）**天然跳过**以 `.` 开头
# 的文件——心跳文件不进入审计 1/6 的枚举面。此豁免为**显式登记确认**（不能仅靠"默认不扫"
# 假设），而非新增过滤逻辑：_find_files 行为未改动，7 道审计结构未改动。
HEARTBEAT_AUDIT_EXEMPTION = "confirmed"  # 登记值（供审计追溯引用，不参与判定）


def _find_files(base):
    """find base -type f -not -name '.*'（递归，排除隐藏名文件）等价。

    RM-AG0055 心跳豁免：以 `.` 开头的心跳文件（.heartbeat / .heartbeat.child-{n}）
    由本隐藏文件过滤天然跳过，登记确认见上方 HEARTBEAT_AUDIT_EXEMPTION。
    """
    files = []
    for _root, _dirs, names in os.walk(base):
        for name in names:
            if name.startswith("."):
                continue
            files.append(os.path.join(_root, name))
    return files


def _find_log_files(base):
    """find base -name '*.log'（递归）等价（含名称以 .log 结尾的条目）。"""
    if not os.path.isdir(base):
        return []
    files = []
    for root, _dirs, names in os.walk(base):
        for name in names:
            if name.endswith(".log"):
                files.append(os.path.join(root, name))
    return files


def get_agent(file):
    """sed -n '/^---$/,/^---$/p' | grep '^agent:' | sed 's/^agent:\\s*//' | head -1 等价。"""
    if not os.path.isfile(file):
        return ""
    try:
        with open(file, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return ""
    in_fm = False
    for line in lines:
        if line == "---":
            if not in_fm:
                in_fm = True
            else:
                break
            continue
        if in_fm:
            m = re.match(r"^agent:\s*(.*)", line)
            if m:
                return m.group(1)
    return ""


def _is_skipped_agent_check(localname):
    """sh 版 case 模式（*-dispatch-context*.md / *-dispatch-prompt-*.md / *-progress.md /
    *-paused-resolution.md）等价判定。"""
    return any(re.search(p, localname) for p in _SKIP_AGENT_CHECK)


def _run_git(task_dir, args):
    """在 task_dir 所在 git 仓库中运行 git 命令（`-C task_dir`，git 自动向上发现仓库根），
    返回 (stdout, returncode)。task_dir 不存在/非 git 仓库时返回空串 + 非 0。"""
    try:
        proc = subprocess.run(
            ["git", "-C", str(task_dir), *list(args)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return "", 1
    return proc.stdout or "", proc.returncode


def p6_declares_reuse(task_dir):
    """P6-acceptance.md 是否声明"引用 P5 证据、不重跑"（M21 落地的产出规格判定）。"""
    p6_file = os.path.join(task_dir, "P6-acceptance.md")
    if not os.path.isfile(p6_file):
        return False
    try:
        with open(p6_file, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return False
    return bool(re.search(r"引用\s*P5\s*证据", text))


def audit7_p5_evidence_reuse(task_dir, state_yaml):
    """审计 7：P6 引用 P5 证据的无改动校验（P2-design.md §3.5，BDD-12/13）。

    state_yaml 为已解析的 .state.yaml dict（读取可选字段 p5_pass_commit）。返回三态字符串：
      "no_reuse_claim_possible" — p5_pass_commit 字段缺失（存量任务兼容，静默回退强制重跑，不报错）
      "reuse_blocked"           — p5_pass_commit..HEAD 间存在非产出文件改动（BDD-13，不可复用）；
                                   或 git diff 命令本身失败（fail-closed，见下方 CRITICAL-1 修复）
      "reuse_allowed"           — 排除 EXCLUDE_PRODUCE_PREFIX 前缀后 diff 为空（BDD-12，可复用）

    若 P6-acceptance.md 已声明"引用 P5 证据、不重跑"但判定为 reuse_blocked，向 stderr 报
    GATE PROVENANCE 错误（不在此处 sys.exit，由调用方按需处理，函数本身只负责判定+提示）。

    P4-review CRITICAL-1 修复（TAG0016 P4-review-20260819）：`_run_git` 返回 (stdout, returncode)，
    此前调用方只用了 stdout、从未检查 returncode——当 p5_commit 是 git diff 无法解析的哈希
    （历史被 rebase/squash 移除、.state.yaml 手工写错、CI 浅克隆导致该 commit 不在本地历史）时，
    git diff 失败会向 stderr 打印 fatal 并以非 0 退出，同时 stdout 为空，被误判为"无改动"→
    reuse_allowed（本该强制重跑的场景被静默放行）。fail-closed：returncode != 0 时不进入"无改动"
    分支，直接判定 reuse_blocked，并写清楚区分"git 命令本身失败"与"确实检测到改动"的诊断信息
    （两者是不同性质的失败，不合并进同一条 stderr 消息）。
    """
    p5_commit = (state_yaml or {}).get("p5_pass_commit")
    if not p5_commit:
        return "no_reuse_claim_possible"

    out, rc = _run_git(task_dir, ["diff", f"{p5_commit}..HEAD", "--name-only"])
    if rc != 0:
        sys.stderr.write(
            f"GATE PROVENANCE: git diff {p5_commit}..HEAD 命令本身执行失败（returncode={rc}），"
            "无法判定 p5_pass_commit 与 HEAD 间是否存在改动（可能原因：commit 已被 rebase/squash "
            "移除、.state.yaml 手工写错哈希、CI 浅克隆导致该 commit 不在本地历史）。"
            "fail-closed：按 reuse_blocked 处理，强制重跑 P5\n"
        )
        return "reuse_blocked"

    changed = [line for line in out.splitlines() if line and not line.startswith(EXCLUDE_PRODUCE_PREFIX)]

    if changed:
        if p6_declares_reuse(task_dir):
            sys.stderr.write(
                "GATE PROVENANCE: 声明引用 P5 证据但检测到非产出文件改动，须重跑 P5：" + ", ".join(changed) + "\n"
            )
        return "reuse_blocked"
    return "reuse_allowed"


def _load_state_yaml(task_dir):
    """读取 task_dir/.state.yaml，返回 dict（文件缺失/无 pyyaml/解析失败 → 静默回退空 dict，
    等价于 audit7 的 no_reuse_claim_possible 静默回退语义）。"""
    state_yaml_path = os.path.join(task_dir, ".state.yaml")
    state_yaml = {}
    if os.path.isfile(state_yaml_path):
        try:
            import yaml
            with open(state_yaml_path, encoding="utf-8", errors="replace") as f:
                state_yaml = yaml.safe_load(f) or {}
        except Exception:
            state_yaml = {}
    return state_yaml


def _run_audit7_only(task_dir):
    """--audit7-only TASK_DIR：只跑审计 7，三态结果打印到 stdout 供 grep 提取。"""
    state_yaml = _load_state_yaml(task_dir)
    reuse_result = audit7_p5_evidence_reuse(task_dir, state_yaml)
    print(f"AUDIT7_RESULT: {reuse_result}")
    if reuse_result == "reuse_blocked":
        sys.exit(1)
    sys.exit(0)


def main():
    if len(sys.argv) >= 2 and sys.argv[1] == "--audit7-only":
        if len(sys.argv) < 3:
            sys.stderr.write("用法: check-p6-provenance.py --audit7-only TASK_DIR\n")
            sys.exit(1)
        _run_audit7_only(sys.argv[2])
        return

    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-p6-provenance.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]
    p1_file = os.path.join(task_dir, "P1-requirements.md")
    p6_file = os.path.join(task_dir, "P6-acceptance.md")
    evidence_dir = os.path.join(task_dir, "P6-evidence")

    p6_exists = os.path.isfile(p6_file)
    if not p6_exists:
        # 六道审计全部以 P6-acceptance.md / P6-evidence/ 为对象；对象缺席时此前**静默 exit 0**，
        # 与「已审计且通过」不可区分——且本脚本位于 agate-next.py 的 P6→P7 推进路径上
        # （RM-AG0077 子批 A：独立评审指出的逃逸站点）。仅加可见性，exit code 不变。
        sys.stderr.write(
            "GATE SKIP: check-p6-provenance: 无 P6-acceptance.md，六道审计无对象，未校验\n"
        )
    p6_text = ""
    p6_lines = []
    pass_lines = []
    if p6_exists:
        try:
            with open(p6_file, encoding="utf-8", errors="replace") as f:
                p6_text = f.read()
        except OSError:
            p6_text = ""
        p6_lines = p6_text.splitlines()
        pass_lines = [line for line in p6_lines if re.search(r"^\s*- PASS\b", line)]

    # --- 审计 1：证据-结论对应 ---
    # 只在 P6-acceptance.md 存在时运行（C1 修复：不阻塞非 P6 阶段的 commit）
    if p6_exists:
        # 1a: PASS 行里的证据引用路径必须存在
        # I3 修复：取行末最后一个括号组（证据引用在行末），避免前置括号干扰
        # R1b 兼容：先剥离 (vision: ...) 引用，避免把它当证据文件路径
        # R1c 修复：优先精确提取 screenshots/ 路径，避免嵌套括号（如 nth(1)）截断
        missing_refs = 0
        missing_details = ""
        unparsed_refs = 0
        unparsed_details = ""
        for line in pass_lines:
            # 提取走**单源**（设计 §3.2）：任意位置、全角/半角、逗号分隔多文件，
            # 且排除类含全角括号（原 `screenshots/[^ ),]+` 会把 `）` 截进路径）。
            refs = extract_evidence_refs(line)
            if not refs:
                # **不得静默跳过**（B2）：取不到就放行，等于把「解析失败」当成「通过」。
                # 与 check-p6-evidence 的「缺引用」检查构成双重防线。
                unparsed_refs += 1
                unparsed_details += f"  PASS行: {line}"
                continue
            for ref in refs:
                ref_path = resolve_evidence(task_dir, ref)
                if not ref_path:
                    missing_refs += 1
                    missing_details += (
                        f"  PASS行: {line}\n  缺失路径: {ref}（已尝试剥前缀后相对 "
                        f"{os.path.basename(evidence_dir)}/ 解析）\n")

        if unparsed_refs > 0:
            sys.stderr.write(
                f"GATE PROVENANCE: 有 {unparsed_refs} 条 PASS 行**未能提取证据引用**——"
                "引用须写在括号内（全角/半角均可），可在行中或行末\n")
            if unparsed_details:
                sys.stderr.write(unparsed_details)
            sys.exit(1)

        if missing_refs > 0:
            sys.stderr.write(f"GATE PROVENANCE: P6-acceptance.md 有 {missing_refs} 条 PASS 引用的证据文件不存在\n")
            if missing_details:
                sys.stderr.write(missing_details)
            sys.exit(1)

        # 1b: 证据目录非空检查（多条 PASS 可共享同一证据文件）
        # I5 修复：排除隐藏文件（.gitkeep, .DS_Store 等）
        pass_count = len(pass_lines)
        evidence_count = len(_find_files(evidence_dir)) if os.path.isdir(evidence_dir) else 0

        if pass_count > 0 and evidence_count == 0:
            sys.stderr.write(f"GATE PROVENANCE: 有 {pass_count} 条 PASS 但 P6-evidence/ 为空或不存在\n")
            sys.exit(1)

        # 1c: 证据文件必须被至少一条 PASS 行引用（空 png 充数拦截）
        # C2 修复：用括号上下文精确匹配，防止子字符串假阴性
        # C3 修复：只在 PASS 行里搜索，不在整个文件里搜索
        # I4 修复：匹配时考虑子目录路径（evidences/ screenshots/ 等），固定字符串匹配
        if evidence_count > 0 and os.path.isdir(evidence_dir):
            unreferenced = 0
            for ev_file in _find_files(evidence_dir):
                ev_basename = os.path.basename(ev_file)
                if not any(ev_basename in line for line in pass_lines):
                    unreferenced += 1
            if unreferenced > 0:
                sys.stderr.write(f"GATE PROVENANCE: {unreferenced} 个证据文件未被 P6-acceptance.md PASS 行引用（可能为充数文件）\n")
                sys.exit(1)

    # --- 审计 2：dispatch-context 内容约束 ---
    # P6 阶段的 dispatch-context 不能含验收结论预判
    # Exclude AGATE_CARD embedded block + 文件顶部第一对 "---" 定界的 frontmatter 块
    # T001 v2.0 流 B（P2-design.md §3.2.3）：P6 结果入 frontmatter 后，frontmatter
    # 样例块也须排除，避免字段示例被误判为验收结论预判。
    # TAG0027 §3.6 双锚点剥离（A2 定案 (a)）：渲染产物含块外 CARD-SOURCE 来源标记
    # （`<!-- CARD-SOURCE: agate-dispatch.py {phase} -->`，置于 AGATE_CARD_START 之前）——
    # ① CARD-SOURCE 优先：自 CARD-SOURCE 行起至匹配 AGATE_CARD_END 止整段剥离
    #   （CARD-SOURCE 行 + START + 卡片正文一起剥——渲染产物块 = "从 CARD-SOURCE 行起的
    #   物理块"，剥离后文件体不含 CARD-SOURCE/START/END/卡片）；
    # ② 物理块兜底：无 CARD-SOURCE 时走既有 AGATE_CARD_START → AGATE_CARD_END 剥离
    #   （手工 + inject-card 注入路径，BDD-21）。
    for dispatch_ctx in sorted(glob.glob(os.path.join(task_dir, "P6-dispatch-context-*.md"))):
        try:
            with open(dispatch_ctx, encoding="utf-8", errors="replace") as f:
                lines = f.read().splitlines()
        except OSError:
            lines = []
        stripped = []
        in_card = False
        from_source = False
        for line in lines:
            if from_source:
                # CARD-SOURCE 优先剥离区间：至匹配 AGATE_CARD_END 止（含 END 行整段剥）
                if "<!-- AGATE_CARD_END -->" in line:
                    from_source = False
                continue
            if not in_card and "<!-- CARD-SOURCE: agate-dispatch.py" in line:
                # 渲染产物块剥离起点 = CARD-SOURCE 行（该行 + START + 卡片正文整段剥）；
                # 仅在物理块外触发（卡片正文内若含同名子串不误触发）
                from_source = True
                continue
            if "<!-- AGATE_CARD_START -->" in line:
                in_card = True
                continue
            if "<!-- AGATE_CARD_END -->" in line:
                in_card = False
                continue
            if not in_card:
                stripped.append(line)
        # 只剥离**文件顶部第一对** `---` 定界的 frontmatter（原实现「遇到 `---` 就向后
        # 配对下一个 `---`」在 **奇数个 `---`** 时会让最后一个 `---` 吞掉其后**至 EOF**
        # → 尾部区间静默逃过本审计，同一违规因**位置不同判定相反**（RM-AG0077 子批 C）。
        # 爆炸半径实测：706 个存量 dispatch-context 中 11 个含奇数 `---`，本修复后
        # **新增命中 0** ⇒ 不改动任何既有判定。
        filtered = list(stripped)
        if filtered and filtered[0] == "---":
            for _j in range(1, len(filtered)):
                if filtered[_j] == "---":
                    filtered = filtered[_j + 1:]
                    break
            else:
                # 找不到闭合对 ⇒ **不剥离**（宁可多审，不可吞正文）并显式告警
                sys.stderr.write(
                    "GATE PROVENANCE: frontmatter 起始 `---` 无闭合对，未剥离（避免吞掉正文）\n"
                )
        # 审计 2：**围栏代码块先行剥离**（M3）——与 judge 侧同源，
        # 否则派发指引里的格式示例会被判预判（假红）。
        filtered, _fence_warn = strip_fenced_blocks(filtered)
        if _fence_warn:
            sys.stderr.write(f"GATE PROVENANCE: {_fence_warn}\n")
        prejudice = sum(1 for line in filtered if re.search(r"^\s*- (PASS|FAIL)\b", line))
        if prejudice > 0:
            sys.stderr.write(f"GATE PROVENANCE: {os.path.basename(dispatch_ctx)} 含 {prejudice} 处验收结论预判\n")
            sys.exit(1)

    # --- 审计 3：BDD 总数自动化对照 ---
    # P6 的 PASS+FAIL 数 ≥ P1 的 BDD 标题数（挑验拦截）
    # T001 v2.0 流 B（BDD-17/18，P2-design.md §3.2.1）：计数口径改从严格式
    # `grep -cE '^\s*- (PASS|FAIL) BDD-[0-9]'`；新格式（frontmatter 声明 pass+fail）
    # 优先用该结构化汇总为总数，无 frontmatter 汇总（旧格式）→ 回退从严正文 grep。
    # FIND-6：新格式下 frontmatter 汇总与正文从严行数不一致 → WARNING（exit 仍 0）。
    if p6_exists and os.path.isfile(p1_file):
        p1_text = ""
        try:
            with open(p1_file, encoding="utf-8", errors="replace") as f:
                p1_text = f.read()
        except OSError:
            p1_text = ""
        p1_lines = p1_text.splitlines()
        p1_bdd = sum(1 for line in p1_lines if re.search(r"^#### BDD-[0-9]", line))
        p6_body_strict = sum(1 for line in p6_lines if re.search(r"^\s*- (PASS|FAIL) BDD-[0-9]", line))

        pass_fm = ""
        out, rc = _run_script("agate-md-field-get.py", ["pass"], {"FILE": p6_file})
        if rc == 0:
            pass_fm = out
        fail_fm = ""
        out, rc = _run_script("agate-md-field-get.py", ["fail"], {"FILE": p6_file})
        if rc == 0:
            fail_fm = out

        if pass_fm != "" and fail_fm != "":
            try:
                p6_total = int(pass_fm) + int(fail_fm)
            except ValueError:
                sys.stderr.write(f"GATE PROVENANCE: P6-acceptance.md frontmatter pass/fail 非数字（{pass_fm} / {fail_fm}）\n")
                sys.exit(1)
            if p6_total != p6_body_strict:
                sys.stderr.write(f"GATE PROVENANCE WARNING: P6-acceptance.md frontmatter 声明 pass+fail={p6_total}，正文逐条 '- PASS|FAIL BDD-N' 行数={p6_body_strict}，两者不一致，请复核\n")
        else:
            p6_total = p6_body_strict

        if p1_bdd == 0:
            sys.stderr.write("GATE PROVENANCE: P1-requirements.md 未使用标准 #### BDD-NN: 格式（或没有 BDD），标准化后必须使用该格式\n")
            sys.exit(1)
        if p6_total < p1_bdd:
            sys.stderr.write(f"GATE PROVENANCE: P6 结果数({p6_total}) < P1 BDD 条目数({p1_bdd})，挑验不通过\n")
            sys.exit(1)

    # --- 审计 4：UI vision 证据（R1b：T045 评审 v5，TAG0006 增 GAP 放宽）---
    # ui_affected: true 时，含截图引用的 PASS 行：
    #   * P1 vision status=GAP（能力缺失，走降级链）→ 不强制 vision YAML，改为要求
    #     每条截图 PASS 附 (manual-review: <file>) 引用且文件存在（人工复核记录）
    #   * P1 显式 available/supplementable 或**无声明**（默认 available 语义，兼容回归
    #     anchor：无声明任务 P6 行为与基线完全一致）→ 保留既有强制：
    #     (vision: ...) 引用 + YAML 存在 + summary.blocker_count == 0
    if p6_exists and os.path.isfile(p1_file):
        p2_file = os.path.join(task_dir, "P2-design.md")
        ui_affected = ""
        if os.path.isfile(p2_file):
            out, rc = _run_script("agate-md-field-get.py", ["ui_affected"], {"FILE": p2_file})
            if rc == 0:
                ui_affected = out

        if ui_affected == "true":
            vision_state = read_vision_tri_state(p1_file) if read_vision_tri_state is not None else None
            is_gap = vision_state == "GAP"

            if is_gap:
                gap_review_missing = 0
                for line in pass_lines:
                    if re.search(r"\(screenshots/", line) and not re.search(r"\(manual-review:\s*[^)]+\)", line):
                        gap_review_missing += 1

                if gap_review_missing > 0:
                    sys.stderr.write(
                        f"GATE PROVENANCE: ui_affected=true 且 P1 vision=GAP（降级链）但有 {gap_review_missing} 条含截图的 PASS 缺人工复核记录引用（manual-review: <file>）\n"
                    )
                    sys.exit(1)

                for ref in re.findall(r"\(manual-review:\s*[^)]+\)", p6_text):
                    review_file = re.sub(r"^.*manual-review:\s*", "", ref).replace(")", "").strip()
                    if not os.path.isfile(os.path.join(task_dir, review_file)):
                        sys.stderr.write(f"GATE PROVENANCE: 人工复核记录文件不存在: {review_file}\n")
                        sys.exit(1)
                # GAP 降级链放行（仅本轮审计 4）：vision 能力缺失任务的截图证据以
                # "人工复核记录"为终态证据，不要求 vision YAML / blocker_count
                # （那是 available 分支的强制项）。只跳过 vision 相关强制，不整脚本退出，
                # 随后正常落入审计 5（日志 EXIT_CODE 一致性）、协作规范与审计 6
                # （evidence JSON 一致性）——这些是非 vision 硬检查，GAP 任务同样适用。
                sys.stderr.write("GATE PROVENANCE: P1 vision=GAP（降级链），截图 PASS 已附人工复核记录，R1b 本轮 vision 检查放行\n")
            else:
                vision_missing = 0
                for line in pass_lines:
                    if re.search(r"\(screenshots/", line) and not re.search(r"\(vision:\s*[^)]+\)", line):
                        vision_missing += 1

                if vision_missing > 0:
                    sys.stderr.write(f"GATE PROVENANCE: ui_affected=true 但有 {vision_missing} 条含截图的 PASS 缺 vision YAML 引用\n")
                    sys.exit(1)

                refs = sorted({
                    m
                    for line in p6_lines
                    for m in re.findall(r"\(vision:\s*[^)]+\)", line)
                })
                for ref in refs:
                    yaml_file = re.sub(r"^.*vision:\s*", "", ref).replace(" ", "").replace(")", "")
                    yaml_path = os.path.join(task_dir, yaml_file)
                    if not os.path.isfile(yaml_path):
                        sys.stderr.write(f"GATE PROVENANCE: vision YAML 引用的文件不存在: {yaml_file}\n")
                        sys.exit(1)
                    blocker_count, rc = _run_script("agate-vision-blocker.py", [], {"YAML_PATH": yaml_path})
                    if rc != 0:
                        blocker_count = "-1"
                    if blocker_count != "0":
                        sys.stderr.write(f"GATE PROVENANCE: vision YAML {yaml_file} 的 blocker_count={blocker_count}（须为 0）\n")
                        sys.exit(1)

    # --- 审计 5：日志 EXIT_CODE 与 PASS/FAIL 声明一致性（依赖 M1.3a 约定）---
    if p6_exists:
        for log_file in _find_log_files(os.path.join(task_dir, "P6-evidence")):
            try:
                with open(log_file, encoding="utf-8", errors="replace") as f:
                    content = f.read()
            except OSError:
                content = ""
            log_lines = content.splitlines()
            last_line = log_lines[-1] if log_lines else ""
            if re.match(r"^EXIT_CODE: [0-9]+$", last_line):
                log_exit = re.search(r"[0-9]+$", last_line).group(0)
                log_basename = os.path.basename(log_file)
                if log_basename in p6_text and log_exit != "0":
                    sys.stderr.write(f"GATE PROVENANCE: {log_basename} 声明 PASS 但日志 EXIT_CODE={log_exit}（矛盾）\n")
                    sys.exit(1)
            else:
                sys.stderr.write(f"GATE PROVENANCE: {os.path.basename(log_file)} 缺少标准 EXIT_CODE 尾行，跳过一致性核验（不阻塞）\n")

    # --- 协作规范：agent 字段 ---
    # 不做硬拦截（自报数据不可信），缺字段降级为 WARNING
    # 安全审计（1/2/3）用 ERROR，协作规范用 WARNING——符合「不把自报字段当安全边界」原则
    # WARNING 不立即 exit——记变量继续往下跑审计 6，最后统一判断 exit code
    warning_found = 0

    if p6_exists:
        agent = get_agent(p6_file)
        if not agent:
            sys.stderr.write("GATE PROVENANCE: P6-acceptance.md 缺 agent 字段（协作规范，不阻塞）\n")
            warning_found = 1

    # 所有阶段产出文件 agent 字段存在性（格式校验）
    if p6_exists:
        for f in sorted(glob.glob(os.path.join(task_dir, "P[0-8]-*.md"))):
            if not os.path.isfile(f):
                continue
            localname = os.path.basename(f)
            if localname == "P0-brief.md":
                continue
            if _is_skipped_agent_check(localname):
                continue
            agent = get_agent(f)
            if not agent:
                sys.stderr.write(f"GATE PROVENANCE: {localname} 缺 agent 字段（协作规范，不阻塞）\n")
                warning_found = 1

    # 审计 6: evidence JSON 与 P6 PASS/FAIL 声明一致性（P2.57）
    if os.path.isdir(evidence_dir):
        inconsistency, rc = _run_script(
            "agate-evidence-consistency.py", [],
            {"EVIDENCE_DIR": evidence_dir, "P6_FILE": os.path.join(task_dir, "P6-acceptance.md")},
        )
        if rc != 0:
            inconsistency = ""
        if inconsistency != "":
            sys.stderr.write("GATE PROVENANCE: evidence JSON 与 P6-acceptance.md 声明不一致：\n")
            for line in inconsistency.splitlines():
                sys.stderr.write(f"  - {line}\n")
            sys.exit(1)

    # --- 审计 7：P6 引用 P5 证据的无改动校验（BDD-12/13，TAG0016）---
    # .state.yaml 缺失/无 p5_pass_commit 字段/无 pyyaml → 静默回退（no_reuse_claim_possible
    # 语义），不阻塞；只有"P6 已声明复用但判定为 reuse_blocked"时才拦截（错误信息已在
    # audit7_p5_evidence_reuse 内部写 stderr）。
    if p6_exists:
        state_yaml = _load_state_yaml(task_dir)
        reuse_result = audit7_p5_evidence_reuse(task_dir, state_yaml)
        if reuse_result == "reuse_blocked" and p6_declares_reuse(task_dir):
            sys.exit(1)

    if warning_found == 1:
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
