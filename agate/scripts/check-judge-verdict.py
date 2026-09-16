#!/usr/bin/env python3
r"""check-judge-verdict.py — P6.5 judge verdict 机械校验（TAG0020，P2-design §3.3）

CLI：check-judge-verdict.py TASK_DIR（exit 0 = 校验通过 / exit 1 = 校验不通过）

校验链（顺序执行，任一 exit 1 即停，全部通过后追加 judge_verdict 账本事件）：
  1. P6.5-judge-verdict.md 存在且非空（BDD-1 fail-closed）
  2. P6.5-dispatch-context-judge.md 存在且非空（缺 → 无法验证信息隔离 → exit 1，BDD-4）
  3. Header 字段：status ∈ {passed, rejected, needs-revision}；criteria_total /
     criteria_passed 为整数；verdict_evidence 存在（BDD-5）
  4. BDD 对照（BDD-3）：criteria_total == P1 `^#### BDD-[0-9]` 标题数（审计 3 计数口径）；
     正文结论条目 `- (PASS|FAIL|NEEDS-REVISION) BDD-NN:` 的编号集与 P1 全集相等，
     条目数 == criteria_total（零挑验，含已 PASS 项重验）
  5. status==passed ⇒ criteria_total == criteria_passed == P1 BDD 数（BDD-5）；
     partial: true ⇒ status ∈ {needs-revision, rejected}（passed+partial → exit 1，BDD-8）
  6. 证据交叉核对（BDD-6）：verdict_evidence 每条 → 存在于 P6-evidence/ 下且非空、
     相互 md5 互异（重复充数拦截）；正文每条 BDD 结论的引用 ⊆ verdict_evidence；
     verdict_evidence 每条被 ≥1 条结论引用（对称，仿审计 1 的 1a/1c）。
     证据核对整体 gate 在 `P6-evidence/` 目录存在的前提下（目录缺失 = 无证据可核，
     不因缺失拦截——该场景由其他检查覆盖；P3 用例固化此口径）
  7. 信息隔离白名单（BDD-4）：对 P6.5-dispatch-context-judge.md：
     - 『输入文件』『上游关联』两节黑名单串扫描（大小写不敏感 + 归一化）：
       P6-acceptance.md / P6|P5|P4-dispatch-context-*.md / P4-implementation.md /
       P4-review.md / P5-test-results/
     - 两节白名单外任务产出路径引用扫描（提取 .md/.yaml 路径 + 目录引用，
       白名单 = P1-requirements.md / P2-design.md / P6-evidence/ / .state.yaml /
       gate-events.jsonl / P6.5-judge-verdict.md）→ 白名单外 → exit 1
     - 全文（排除 AGATE_CARD 块 + frontmatter，复用审计 2 双排除）行首
       `^\s*- (PASS|FAIL)\b` 验收结论预判扫描（继承 audit 2 语义）
  8. 预算交叉（BDD-8）：账本存在 judge_verdict 事件且任一 reason == budget_exhausted
     → verdict 必须 partial: true 且 status == needs-revision（否则 exit 1）
  8.1 exit2-resolution 复核（TAG0027 §3.3，BDD-12，Fix C）：**已存在**的
     {phase}-exit2-resolution.md（= agate-next 真暂停分支落盘产物）须 frontmatter/必填节
     完整；文件不存在（任务从未真暂停，账本 exit:2 全是正常通过码）→ 不要求文件，
     复核通过（不误拦健康任务——CRITICAL-2；P6 自身 exit 2 前进特例豁免，BDD-9）
  9. 全部通过 → append_event(task_dir, {event: judge_verdict, phase: P6.5,
     verdict: status, criteria_total, criteria_passed, partial, [reason]}) → exit 0

哲学红线（BDD-9）：LLM 结论（status: passed）不单独构成放行依据——机械核对
（计数对照/证据引用/白名单/预算交叉）任一 exit 1 → 不放行。

平台无关：纯文件文本解析（显式 encoding="utf-8"），无路径字面量/进程/软链假设。

Python 3.8+（禁 match / str.removeprefix）。
"""

import hashlib
import json
import os
import re
import sys

# 引入同目录公共库：AGATE_CARD/frontmatter 双排除与 BDD 计数口径与 check-p6-provenance
# 同款；append_event 是账本唯一写路径（P2 候选 C1）。
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agate_common import append_event, read_judge_verdict, split_frontmatter

# BDD-5：verdict Header status 合法三值
_VALID_STATUS = {"passed", "rejected", "needs-revision"}

# BDD-4：黑名单路径引用集（P1 §4.2 权威定义；大小写不敏感 + 归一化匹配，R3）
_BLACKLIST_MD = {
    "p6-acceptance.md",
    "p4-implementation.md",
    "p4-review.md",
}
_BLACKLIST_DC_RE = re.compile(r"p[456]-dispatch-context-[^\s]*\.md")
_BLACKLIST_DIR_RE = re.compile(r"p5-test-results/")
# TAG0035 BDD-11：协议规格文档路径引用豁免（`phase-cards/` 路径段），见 _check_blacklist
_PROTOCOL_SPEC_DIR_RE = re.compile(r"(?:^|/)phase-cards/")

# BDD-4：白名单（任务产出路径；P6-evidence/ 为目录前缀匹配）
_WHITELIST_MD = {
    "p1-requirements.md",
    "p2-design.md",
    ".state.yaml",
    "gate-events.jsonl",
    "p6.5-judge-verdict.md",
}

# BDD-3：结论条目行前缀（judge.md 产出规范；脚本只做编号/计数机械核对）
_CONCLUSION_RE = re.compile(r"^\s*-\s*(PASS|FAIL|NEEDS-REVISION)\s+BDD-([0-9]+)\s*:")

# BDD-7：账本路径
LEDGER_NAME = "gate-events.jsonl"


def _read_text(path):
    """读文件全文；缺失/不可读返回 ""。"""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def _p1_bdd_set(p1_text):
    """P1 全部 BDD 编号（审计 3 计数口径 `^#### BDD-[0-9]`）。"""
    return {int(m) for m in re.findall(r"^#### BDD-([0-9]+)", p1_text, re.M)}


def _strip_card(lines):
    """审计 2 同款：删除 AGATE_CARD 注入块。

    双锚点剥离（TAG0027 §3.6 D6-A 定案 (a)）：
    ① CARD-SOURCE 优先——从 `<!-- CARD-SOURCE: agate-dispatch.py {phase} -->` 所在行起、
       至匹配的 `<!-- AGATE_CARD_END -->` 止整段剥离（渲染产物块 = 从 CARD-SOURCE 行起的
       物理块，CARD-SOURCE 行 + START + 卡片正文一起剥）；
    ② 物理块兜底——无 CARD-SOURCE 时走既有 AGATE_CARD_START → AGATE_CARD_END 剥离
       （手工 + inject-card 注入路径，BDD-21）。
    """
    out = []
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
            out.append(line)
    return out


def _strip_frontmatter(lines):
    """审计 2 同款：删除文件顶部第一对 `---` 定界的 frontmatter 块。"""
    if lines and lines[0] == "---":
        for i in range(1, len(lines)):
            if lines[i] == "---":
                return lines[i + 1:]
    return lines


def _two_sections(lines):
    """提取『输入文件』『上游关联』两节内容（自含标题的标题行起，至下个标题止）。

    返回拼接后的列表（两节内容按出现顺序连接）。节标题匹配 = 行首 # 且含
    「输入文件」或「上游关联」（兼容 `### 输入文件（files_to_read，勿乱搜）` 形态）。
    """
    out = []
    current = None
    for line in lines:
        if re.match(r"^\s*#", line):
            if "输入文件" in line or "上游关联" in line:
                current = []
                out.append(current)
            else:
                current = None
        elif current is not None:
            current.append(line)
    return [ln for section in out for ln in section]


def _check_blacklist(section_lines):
    """BDD-4①/BDD-11：两节黑名单串扫描（大小写不敏感 + 归一化）。
    basename 命中时先取紧邻其前的最长路径 token，含 phase-cards/ 路径段则视为
    协议规格文档引用，豁免；裸 basename（无此前缀）仍判命中，保留对真实
    自述场景（BDD-14）的拦截。"""
    low = "\n".join(section_lines).lower()
    hits = []
    for exact in _BLACKLIST_MD:
        for m in re.finditer(r"[\w./\-]*" + re.escape(exact), low):
            token = m.group(0)
            if _PROTOCOL_SPEC_DIR_RE.search(token):
                continue
            hits.append(exact)
            break
    for m in _BLACKLIST_DC_RE.finditer(low):
        hits.append(m.group(0))
    for m in _BLACKLIST_DIR_RE.finditer(low):
        hits.append(m.group(0))
    return hits


# TAG0035 BDD-12：角色定义文件路径（execution-roles/ / review-roles/ 目录前缀）豁免
_ROLE_DIR_RE = re.compile(r"(?:^|/)(?:execution-roles|review-roles)/")


def _p6_evidence_basenames(task_dir):
    """task_dir/P6-evidence/ 目录下真实存在的文件 basename 集合（小写），
    目录不存在返回空集。供裸文件名白名单判定使用（BDD-13：判定与是否
    显式带 P6-evidence/ 前缀无关，只看该文件是否真实存在于该目录）。"""
    evidence_dir = os.path.join(task_dir, "P6-evidence")
    if not os.path.isdir(evidence_dir):
        return frozenset()
    try:
        return frozenset(
            name.lower() for name in os.listdir(evidence_dir)
            if os.path.isfile(os.path.join(evidence_dir, name))
        )
    except OSError:
        return frozenset()


def _is_whitelisted(tok, evidence_basenames=frozenset()):
    """白名单判定（I-1 修复：basename/相对路径归一，防绝对路径误报）。

    - 完整 token 含 `p6-evidence/` 前缀 → 白名单（目录授权前缀，保留在完整 token 上比对）
    - 完整 token 含角色定义文件目录前缀（BDD-12）→ 白名单
    - 其余按 basename 比对（绝对/相对路径统一归一；仓库路径书写惯例两可），
      basename 命中静态白名单或调用方传入的 evidence_basenames（BDD-13）均视为白名单
    """
    if "p6-evidence/" in tok:
        return True
    if _ROLE_DIR_RE.search(tok):
        return True
    base = tok.split("/")[-1]
    return base in _WHITELIST_MD or base in evidence_basenames


def _check_whitelist_outside(section_lines, evidence_basenames=frozenset()):
    """BDD-4②：两节白名单外任务产出路径引用扫描（basename 归一，I-1）。越界 → 返回越界路径列表。"""
    low = "\n".join(section_lines).lower()
    outside = []
    for tok in re.findall(r"[\w./\-]+\.(?:md|yaml)", low):
        stripped = tok.strip()
        if _is_whitelisted(stripped, evidence_basenames):
            continue
        outside.append(stripped)
    for tok in re.findall(r"[\w./\-]+/", low):
        stripped = tok.strip()
        if "p6-evidence/" in stripped:
            continue
        if re.match(r"^p[0-9]", stripped):
            outside.append(stripped)
    return outside


def _check_prediction(lines):
    r"""BDD-4③（继承审计 2）：全文（已排除 AGATE_CARD/frontmatter）行首
    `^\s*- (PASS|FAIL)\b` 验收结论预判扫描。返回命中数。"""
    return sum(1 for line in lines if re.search(r"^\s*- (PASS|FAIL)\b", line))


def _evidence_md5_dedup(evidence_dir, v_evidence):
    """对 verdict_evidence 引用的证据文件求 md5（引用缺失 → 返回 missing 列表 + digests）。

    供 _check_evidence 内的 md5 去重（BDD-6）使用。
    """
    digests = {}
    missing = []
    for ref in v_evidence:
        full = os.path.join(evidence_dir, str(ref))
        if not os.path.isfile(full):
            missing.append(str(ref))
            continue
        try:
            with open(full, "rb") as fh:
                content = fh.read()
        except OSError:
            missing.append(str(ref))
            continue
        digests[str(ref)] = hashlib.md5(content).hexdigest()
    return digests, missing


def _check_evidence(task_dir, verdict_evidence, conclusions_refs):
    """BDD-6 证据交叉核对；返回 (exit_code, stderr_lines)。

    证据核对 gate 在 `P6-evidence/` 目录存在的前提下（目录缺失 → 通过，P3 固化口径）。
    """
    evidence_dir = os.path.join(task_dir, "P6-evidence")
    if not os.path.isdir(evidence_dir):
        return 0, []

    # 6a：每条引用真实存在且非空（digests 仅含存在且非空的文件）
    digests, missing = _evidence_md5_dedup(evidence_dir, verdict_evidence)
    empty = []
    for ref in verdict_evidence:
        full = os.path.join(evidence_dir, str(ref))
        if os.path.isfile(full):
            try:
                with open(full, "rb") as fh:
                    if not fh.read():
                        empty.append(str(ref))
            except OSError:
                missing.append(str(ref))

    # 6b：相互 md5 去重（同一物理内容不得被多条结论引为不同证据）
    dup = []
    seen = {}
    for ref, digest in digests.items():
        if digest in seen:
            dup.append(f"{seen[digest]} / {ref}")
        else:
            seen[digest] = ref

    # 6c：引用对称——结论引用 ⊆ verdict_evidence，且每条被 ≥1 条结论引用
    ref_set = {str(r) for r in verdict_evidence}
    concl_set = set(conclusions_refs)
    refs_not_in_evidence = sorted(concl_set - ref_set)
    evidence_not_referenced = sorted(ref_set - concl_set)

    if missing or empty or dup or refs_not_in_evidence or evidence_not_referenced:
        lines = []
        if missing:
            lines.append(f"GATE JUDGE-VERDICT: verdict_evidence 引用不存在: {', '.join(missing)}")
        if empty:
            lines.append(f"GATE JUDGE-VERDICT: 证据文件为空（充数）: {', '.join(empty)}")
        if dup:
            lines.append(f"GATE JUDGE-VERDICT: 证据 md5 重复（同一内容多条引用）: {', '.join(dup)}")
        if refs_not_in_evidence:
            lines.append(f"GATE JUDGE-VERDICT: 结论引用不在 verdict_evidence 清单: {', '.join(refs_not_in_evidence)}")
        if evidence_not_referenced:
            lines.append(f"GATE JUDGE-VERDICT: verdict_evidence 条目未被任何结论引用: {', '.join(evidence_not_referenced)}")
        return 1, lines
    return 0, []


def _ledger_budget_exhausted(task_dir):
    """账本是否存在 reason == budget_exhausted 的 judge_verdict 事件（BDD-8 交叉）。"""
    for ev in _iter_ledger_events(task_dir):
        if isinstance(ev, dict) and ev.get("event") == "judge_verdict" \
                and ev.get("reason") == "budget_exhausted":
            return True
    return False


def _iter_ledger_events(task_dir):
    """逐行解析 gate-events.jsonl 事件（坏行跳过；缺失/空文件 → 空迭代）。"""
    ledger_path = os.path.join(task_dir, LEDGER_NAME)
    if not os.path.isfile(ledger_path):
        return
    try:
        with open(ledger_path, encoding="utf-8", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return
    for line in lines:
        if not line.strip():
            continue
        try:
            ev = json.loads(line)
        except Exception:
            continue
        yield ev


# TAG0027 §3.3（BDD-12，Fix C）：exit2-resolution 产物复核必填 frontmatter/正文节。
# Fix C 语义（CRITICAL-2 修正）：只校验**已存在**的 resolution 文件——文件存在（= agate-next
# 真暂停分支落过盘）→ 校验 frontmatter/必填节完整；文件不存在（任务从未真暂停；账本里
# P0-P3/P5/P8 的 exit:2 全是正常通过码）→ 不要求文件，judge 复核通过（不误拦健康任务）。
# 机器可读判定 = frontmatter 含 phase/task_id/type=exit2-resolution/parent + 正文含
# 触发/客观证据/解决 三节（与 agate-next.py 落盘模板一致；judge 复核"何时/依据/由谁"）。
_RESOLUTION_REQUIRED_FM = ("phase", "task_id", "type", "parent", "created", "agent")
_RESOLUTION_REQUIRED_SECTIONS = ("## 触发", "## 客观证据", "## 解决")


def _check_exit2_resolution(task_dir):
    """BDD-12 复核（Fix C）：任务目录**已存在**的 {phase}-exit2-resolution.md 文件须
    frontmatter/必填节完整（agate-next 真暂停分支落盘契约 §3.3）；文件不存在（任务从未真
    暂停）→ 不要求文件、不报错（健康任务账本含正常通过 exit:2 事件 + 无 resolution 文件 →
    judge 复核通过，不误拦——CRITICAL-2）。

    P6 自身 exit 2 前进特例（FAIL=0/证据非空 + provenance exit 0 直通 P6.5）不落盘
    （BDD-9）——judge 挂载对 P6 特例豁免，不带 resolution 要求。
    """
    errors = []
    for name in sorted(os.listdir(task_dir)):
        if not name.endswith("-exit2-resolution.md"):
            continue
        ph = name[: -len("-exit2-resolution.md")]
        res_file = os.path.join(task_dir, name)
        text = _read_text(res_file)
        # frontmatter 机器可读性：type=exit2-resolution + 必填字段
        fm, body = split_frontmatter(text)
        if not isinstance(fm, dict):
            errors.append(
                f"GATE JUDGE-VERDICT: {name} frontmatter 缺失/解析失败——"
                f"无法机器读取 exit2-resolution 字段（BDD-12）"
            )
            continue
        if str(fm.get("type", "")) != "exit2-resolution":
            errors.append(
                f"GATE JUDGE-VERDICT: {name} frontmatter type 应为 "
                f"exit2-resolution，实际 {fm.get('type')!r}（BDD-12）"
            )
        missing_fm = [k for k in _RESOLUTION_REQUIRED_FM if k not in fm]
        if missing_fm:
            errors.append(
                f"GATE JUDGE-VERDICT: {name} frontmatter 缺必填字段 "
                f"{', '.join(missing_fm)}（BDD-12）"
            )
        missing_sec = [
            s for s in _RESOLUTION_REQUIRED_SECTIONS if s not in body
        ]
        if missing_sec:
            errors.append(
                f"GATE JUDGE-VERDICT: {name} 正文缺必填节 "
                f"{', '.join(missing_sec)}（BDD-12）"
            )
        if ph:
            # 账本可追溯性（§3.3 第 4 条）：文件 phase 未命中账本任何 gate_run 事件 phase →
            # WARNING 级提示，不阻断（健康任务账本可能不含真暂停事件）。
            ledger_phases = {
                ev.get("phase")
                for ev in _iter_ledger_events(task_dir)
                if isinstance(ev, dict) and ev.get("event") == "gate_run"
            }
            if ledger_phases and ph not in ledger_phases:
                sys.stderr.write(
                    f"GATE JUDGE-VERDICT: {name} phase={ph} 未命中账本 gate_run 事件"
                    "（WARNING：非阻断，仅提示可追溯性）\n"
                )
    return errors


def _verdict_hash(verdict_text):
    """verdict 文件内容 sha256（内容寻址，CRITICAL-1 修复）。

    同一 verdict 文件被多次 gate 执行（手动 check-gate P6.5 / verdict commit /
    P7 commit / CI backstop）重跑时 hash 不变；check-events 按此字段去重轮次计数，
    同一 verdict 重跑不增轮，真实复核（内容变化）才 +1 轮。
    """
    return hashlib.sha256(verdict_text.encode("utf-8")).hexdigest()


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-judge-verdict.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]

    verdict_file = os.path.join(task_dir, "P6.5-judge-verdict.md")
    dc_file = os.path.join(task_dir, "P6.5-dispatch-context-judge.md")

    # 1. verdict 存在且非空（BDD-1 fail-closed）
    verdict_text = _read_text(verdict_file)
    if not verdict_text.strip():
        sys.stderr.write("GATE JUDGE-VERDICT: 缺 P6.5-judge-verdict.md 或文件为空（judge 未产出）\n")
        sys.exit(1)

    # 2. dispatch-context 存在且非空（BDD-4；缺 → 无法验证信息隔离）
    dc_text = _read_text(dc_file)
    if not dc_text.strip():
        sys.stderr.write("GATE JUDGE-VERDICT: 缺 P6.5-dispatch-context-judge.md 或文件为空（无法验证信息隔离）\n")
        sys.exit(1)

    # 3. Header 字段（BDD-5）
    verdict = read_judge_verdict(task_dir)
    if verdict is None:
        sys.stderr.write("GATE JUDGE-VERDICT: P6.5-judge-verdict.md frontmatter 解析失败\n")
        sys.exit(1)
    status = verdict.get("status")
    criteria_total = verdict.get("criteria_total")
    criteria_passed = verdict.get("criteria_passed")
    v_evidence = verdict.get("verdict_evidence")
    partial = verdict.get("partial", False)

    if status not in _VALID_STATUS:
        sys.stderr.write(f"GATE JUDGE-VERDICT: status 非法（{status!r}），须为 passed/rejected/needs-revision\n")
        sys.exit(1)
    if not isinstance(criteria_total, int) or isinstance(criteria_total, bool):
        sys.stderr.write("GATE JUDGE-VERDICT: criteria_total 缺失或非整数\n")
        sys.exit(1)
    if not isinstance(criteria_passed, int) or isinstance(criteria_passed, bool):
        sys.stderr.write("GATE JUDGE-VERDICT: criteria_passed 缺失或非整数\n")
        sys.exit(1)
    if not isinstance(v_evidence, list) or not v_evidence:
        sys.stderr.write("GATE JUDGE-VERDICT: verdict_evidence 缺失或为空\n")
        sys.exit(1)

    # 4. BDD 对照（BDD-3，审计 3 计数口径）
    p1_text = _read_text(os.path.join(task_dir, "P1-requirements.md"))
    p1_ids = _p1_bdd_set(p1_text)
    if not p1_ids:
        sys.stderr.write("GATE JUDGE-VERDICT: P1-requirements.md 未使用标准 #### BDD-NN: 格式（或没有 BDD）\n")
        sys.exit(1)
    if criteria_total != len(p1_ids):
        sys.stderr.write(
            f"GATE JUDGE-VERDICT: criteria_total({criteria_total}) != P1 BDD 标题数({len(p1_ids)})\n")
        sys.exit(1)
    concl_ids = sorted({int(m) for m in re.findall(
        r"^\s*-\s*(?:PASS|FAIL|NEEDS-REVISION)\s+BDD-([0-9]+)\s*:", verdict_text, re.M)})
    if set(concl_ids) != p1_ids:
        sys.stderr.write(
            f"GATE JUDGE-VERDICT: 结论编号集({concl_ids}) != P1 BDD 全集({sorted(p1_ids)})——零挑验违约（含已 PASS 项须全部重验）\n")
        sys.exit(1)
    if len(concl_ids) != criteria_total:
        sys.stderr.write(
            f"GATE JUDGE-VERDICT: 结论条目数({len(concl_ids)}) != criteria_total({criteria_total})\n")
        sys.exit(1)

    # 5. passed 三数全等 + partial 约束（BDD-5/8）
    if status == "passed" and criteria_passed != criteria_total:
        sys.stderr.write(
            f"GATE JUDGE-VERDICT: status=passed 但 criteria_passed({criteria_passed}) != criteria_total({criteria_total})\n")
        sys.exit(1)
    if partial and status == "passed":
        sys.stderr.write("GATE JUDGE-VERDICT: partial: true 但 status=passed（预算超限不得静默放行）\n")
        sys.exit(1)

    # 6. 证据交叉核对（BDD-6）——引用收敛到明确证据路径形态（I-2 修复）：
    #    仅取"括号内容整体为文件路径形态"的组（可逗号分隔多文件），描述中的
    #    任意括号（如 "(as discussed)"）不再被误取为首个引用 token
    _REF_GROUP_RE = re.compile(r"\(([^()]*)\)")
    _REF_PATH_FULL_RE = re.compile(
        r"[\w./\-]+\.[a-zA-Z0-9]+(?:\s*,\s*[\w./\-]+\.[a-zA-Z0-9]+)*")
    concl_refs = []
    for line in verdict_text.splitlines():
        if not _CONCLUSION_RE.match(line):
            continue
        for m in _REF_GROUP_RE.finditer(line):
            content = m.group(1).strip()
            if _REF_PATH_FULL_RE.fullmatch(content):
                concl_refs.extend(part.strip() for part in content.split(","))
    rc6, err6 = _check_evidence(task_dir, v_evidence, concl_refs)
    if rc6 != 0:
        sys.stderr.write("\n".join(err6) + "\n")
        sys.exit(1)

    # 7. 信息隔离白名单（BDD-4）
    dc_lines = _strip_card(dc_text.splitlines())
    dc_lines = _strip_frontmatter(dc_lines)
    section_lines = _two_sections(dc_lines)
    black_hits = _check_blacklist(section_lines)
    if black_hits:
        sys.stderr.write(f"GATE JUDGE-VERDICT: dispatch-context 两节含黑名单路径引用: {', '.join(black_hits)}\n")
        sys.exit(1)
    outside = _check_whitelist_outside(section_lines, _p6_evidence_basenames(task_dir))
    if outside:
        sys.stderr.write(f"GATE JUDGE-VERDICT: dispatch-context 两节含白名单外任务路径引用: {', '.join(outside)}\n")
        sys.exit(1)
    prejudice = _check_prediction(dc_lines)
    if prejudice > 0:
        sys.stderr.write(f"GATE JUDGE-VERDICT: dispatch-context 含 {prejudice} 处行首验收结论预判（- PASS/FAIL）\n")
        sys.exit(1)

    # 8. 预算交叉（BDD-8）
    if _ledger_budget_exhausted(task_dir) and (not partial or status != "needs-revision"):
        sys.stderr.write(
            "GATE JUDGE-VERDICT: 账本存在 budget_exhausted 事件，verdict 必须 partial: true 且 status=needs-revision\n")
        sys.exit(1)

    # 8.1 exit2-resolution 复核（TAG0027 §3.3，BDD-12，Fix C）：已存在的 resolution 文件
    #     frontmatter/必填节非法 → judge 复核不通过；文件不存在（从未真暂停）不要求。
    resolution_errors = _check_exit2_resolution(task_dir)
    if resolution_errors:
        for line in resolution_errors:
            sys.stderr.write(line + "\n")
        sys.exit(1)

    # 9. 全部通过 → 账本自记 judge_verdict 事件（事件写入收敛单点，BDD-8 R8）
    #    事件带 verdict_hash（verdict 全文 sha256，内容寻址）：同一 verdict 被
    #    pre-commit/gate_p65/CI backstop 多次重跑时 hash 相同，check-events 按
    #    hash 去重轮次，轮次计数 ≈ 真实 judge 复核轮次（CRITICAL-1 修复）
    event = {
        "event": "judge_verdict",
        "phase": "P6.5",
        "verdict": status,
        "criteria_total": criteria_total,
        "criteria_passed": criteria_passed,
        "partial": bool(partial),
        "verdict_hash": _verdict_hash(verdict_text),
    }
    if _ledger_budget_exhausted(task_dir):
        event["reason"] = "budget_exhausted"
    append_event(task_dir, event)
    sys.stderr.write(f"GATE JUDGE-VERDICT: 校验通过（status={status}, criteria {criteria_passed}/{criteria_total}），judge_verdict 事件已记账\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
