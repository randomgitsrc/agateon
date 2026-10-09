#!/usr/bin/env python3
"""check-state-transition.py — 状态转移合法性检查（Phase 2A: P2.3-P2.5）

从 check-state-transition.sh 迁移（TAG0010 批次 2b）。CLI 契约与 sh 版等价：
  check-state-transition.py [STATE_FILE]   # 默认 .state.yaml
exit 0 = 合法; exit 1 = 非法

P2.3 phase 跳变合法性
P2.4 重试超限 -> phase 必须是 PAUSED（按阶段差异化 MAX）
P2.5 回退跳变 >= 2 -> 强制 PAUSED（恢复 exit 1，T019 教训）

迁移说明：MAX_RETRY_MAP 从 agate_common 导入（单一数据源，环境变量覆盖仍有效）；
git show | agate-state-get.py phase_stdin 管道 → run_git + sys.executable subprocess
（stdin 传入，$(...) 剥尾换行 → .rstrip("\n")）；git diff --cached 的 tr -d '\r' 剥离 →
逐行 .rstrip("\r")；grep -oE 提取首个数字 → 正则等价。
"""

import os
import re
import subprocess
import sys
from pathlib import Path

try:
    from agate_common import MAX_RETRY_MAP as _DEFAULT_MAX_RETRY_MAP
    from agate_common import run_git, split_frontmatter, task_level
except ImportError:
    _DEFAULT_MAX_RETRY_MAP = "P1:3,P2:3,P3:2,P4:3,P5:2,P6:2,P7:2,P8:2"
    run_git = None
    task_level = None
    split_frontmatter = None

try:
    import yaml
except ImportError:
    yaml = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGATE_STATE_GET = os.path.join(SCRIPT_DIR, "agate-state-get.py")

MAX_RETRY_MAP = os.environ.get("MAX_RETRY_MAP", _DEFAULT_MAX_RETRY_MAP)

_CONTROL_PHASES = ("PAUSED", "READY", "DONE")

# 不可跳过/不可裁剪阶段集（P1 需求基线 / P2 方案设计 / P4 实现 / P5 技术验证 / P6 验收）。
# ⚠️ 与 `agate/scripts/check-pruning.py::NON_PRUNABLE_PHASES` **逐字一致**
# （ADR-014 判据单源；等价守护见 agate/tests/unit/test_non_prunable_phases_guard.py）。
NON_PRUNABLE_PHASES = frozenset({"P1", "P2", "P4", "P5", "P6"})

_STALE_OUTPUTS = {
    "P1": ["P1-requirements.md", "P1-review.md"],
    "P2": ["P2-design.md", "P2-review.md"],
    "P6": ["P6-acceptance.md"],
    "P7": ["P7-consistency.md"],
}

# RM-AG0042（BDD-1~4，P2-design.md §2.1 候选A D6）：门槛失败事件 ↔ retries 对应性校验
# BDD-1 事件源：评审角色重试/复评 dispatch-context 文件（C8 已知评审角色 token 精确枚举，
# 非文件名含 "review" 子串的宽松通配——P2 重试 #2 收紧，已用 34 个真实历史文件核实排除
# implementer-review-fix / consistency-reviewer 两个已知假阳性）
_BDD1_REVIEW_RETRY_RE = re.compile(
    r"^P(\d+)-dispatch-context-"
    r"(requirements-review|plan-eng-review|plan-design-review|plan-ceo-review|"
    r"cso|review|design-review|review-eng|review-cso)-(retry|rev)\d+\.md$"
)

# BDD-3 事件源：子代理空返回重派信号（自由文本关键词扫描，简单包含判断即可，见 P2-design.md §2.1）
_BDD3_EMPTY_RETURN_KEYWORDS = ("空返回", "重派")
_PHASE_PREFIX_RE = re.compile(r"^P(\d+)-")
# 阶段卡片块定界（RM-AG0101）：dispatch-context 内嵌卡片的正文含"重派"等词，与
# "子代理空返回重派"信号无关，扫描 BDD-3 关键词时须排除该块。
_AGATE_CARD_START = "<!-- AGATE_CARD_START -->"
_AGATE_CARD_END = "<!-- AGATE_CARD_END -->"


def _strip_agate_card_blocks(text):
    """剔除 `<!-- AGATE_CARD_START -->`…`<!-- AGATE_CARD_END -->` 块（RM-AG0101）。

    卡片正文（常见错误清单、卡片模板说明）含"重派"/"空返回"等词，会把每个内嵌卡片的
    dispatch-context 误判为"子代理空返回重派"信号——故 BDD-3 关键词扫描前先剥离卡片块。
    定界行本身及其间内容一并剔除（保守：整行丢弃）。
    """
    kept = []
    in_card = False
    for line in text.splitlines(keepends=True):
        if not in_card and _AGATE_CARD_START in line:
            in_card = True
            continue
        if in_card:
            if _AGATE_CARD_END in line:
                in_card = False
            continue
        kept.append(line)
    return "".join(kept)


def _run_state_get(args, env, input_text=None):
    """调 agate-state-get.py（等价 sh 的 python3 ... 2>/dev/null || echo ""；
    $(...) 剥尾换行 → .rstrip("\n")）。"""
    try:
        proc = subprocess.run(
            [sys.executable, AGATE_STATE_GET, *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env=env, input=input_text,
        )
    except OSError:
        return ""
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").rstrip("\n")


def get_old_phase(state_file, state_basename):
    """HEAD 版本（commit 前旧版本）。任务级 .state.yaml 用 git ls-files 取仓库规范
    相对路径（TAG0003 v2.0 去硬编码，不用 realpath --relative-to——Git for Windows
    的 --show-toplevel 返回 C:/... 而 realpath -m 返回 /c/...，混用会算错路径致
    git show 失败）。git show 失败回退空。"""
    if run_git is None:
        return ""
    git_path = state_basename
    state_dir = str(Path(os.path.dirname(state_file)).resolve())
    rc, repo_root = run_git(["rev-parse", "--show-toplevel"], cwd=state_dir)
    repo_root = repo_root.rstrip("\n").strip() if rc == 0 else ""
    cwd = repo_root or None
    if repo_root:
        rc, tracked = run_git(["ls-files", "--full-name", "--", state_file], cwd=repo_root)
        first = tracked.splitlines()[0].rstrip("\r") if tracked.splitlines() else ""
        if first:
            git_path = first
    rc, shown = run_git(["show", "HEAD:" + git_path], cwd=cwd)
    if rc != 0:
        return ""
    env = dict(os.environ)
    return _run_state_get(["phase_stdin"], env, input_text=shown)


def get_new_phase(state_file):
    """当前暂存版本 phase；文件不存在回退空。"""
    if not os.path.isfile(state_file):
        return ""
    env = dict(os.environ)
    env["STATE_FILE"] = state_file
    return _run_state_get(["phase"], env)


def _yaml_safe_load(text):
    """安全解析 yaml 文本 → dict；yaml 不可用/解析失败/非 dict 结果一律回退空 dict
    （不抛异常，供 retries 对应性校验容错读取，RM-AG0042）。"""
    if yaml is None or text is None:
        return {}
    try:
        data = yaml.safe_load(text)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _load_current_state_yaml(state_file):
    """读取当前（暂存/工作区）.state.yaml 内容并解析；不存在/解析失败回退空 dict。"""
    if not os.path.isfile(state_file):
        return {}
    try:
        with open(state_file, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return {}
    return _yaml_safe_load(text)


def _retries_len(data, phase):
    """从已解析的 .state.yaml dict 中取 retries[phase] 的列表长度；缺失该键/非列表回退 0。"""
    retries = data.get("retries", {}) if isinstance(data, dict) else {}
    if not isinstance(retries, dict):
        return 0
    attempts = retries.get(phase, [])
    return len(attempts) if isinstance(attempts, list) else 0


def get_old_retries_len(state_file, state_basename, phase):
    """HEAD 版本（commit 前旧版本）retries[phase] 列表长度。对称于 get_old_phase() 的
    git-show-HEAD 范式（RM-AG0042 BDD-2，P2-design.md §2.1）。HEAD 版本不存在/解析失败回退 0。"""
    if run_git is None:
        return 0
    git_path = state_basename
    state_dir = str(Path(os.path.dirname(state_file)).resolve())
    rc, repo_root = run_git(["rev-parse", "--show-toplevel"], cwd=state_dir)
    repo_root = repo_root.rstrip("\n").strip() if rc == 0 else ""
    cwd = repo_root or None
    if repo_root:
        rc, tracked = run_git(["ls-files", "--full-name", "--", state_file], cwd=repo_root)
        first = tracked.splitlines()[0].rstrip("\r") if tracked.splitlines() else ""
        if first:
            git_path = first
    rc, shown = run_git(["show", "HEAD:" + git_path], cwd=cwd)
    if rc != 0:
        return 0
    return _retries_len(_yaml_safe_load(shown), phase)


def _scan_bdd1_review_retry_phase(task_dir):
    """扫描 task_dir 下文件名精确匹配评审角色重试/复评正则（_BDD1_REVIEW_RETRY_RE）的文件，
    返回命中阶段号集合 "Pn"（正则组1，参照 _scan_bdd3_keyword_phases 的 set 收集模式）；
    无命中返回空集合（RM-AG0042 BDD-1，P2-design.md §2.1 D6）。P4-review.md CRITICAL 3：
    此前只 return 排序后首个匹配，一个任务同时有多个阶段各自命中评审重试文件时（如本任务
    自己的 task_dir 同时有 P1 与 P2 的 review-retry 文件），后面阶段的命中会被永久忽略。"""
    hits = set()
    if not os.path.isdir(task_dir):
        return hits
    for name in sorted(os.listdir(task_dir)):
        m = _BDD1_REVIEW_RETRY_RE.match(name)
        if m:
            hits.add(f"P{m.group(1)}")
    return hits


def _scan_bdd3_keyword_phases(task_dir):
    """扫描 task_dir 下 P{n}-progress*.md（含分批命名如 P4-progress-batchA.md，
    P4-review.md CRITICAL 4 修复）或该阶段 dispatch-context 文件，检查是否含
    "空返回"/"重派" 关键词信号；返回命中关键词的阶段号集合（RM-AG0042 BDD-3，P2-design.md §2.1）。
    阶段号取自文件名前缀（如 P2-progress.md → P2），不依赖 old_phase/new_phase。"""
    hits = set()
    if not os.path.isdir(task_dir):
        return hits
    for name in sorted(os.listdir(task_dir)):
        if not name.endswith(".md"):
            continue
        m = _PHASE_PREFIX_RE.match(name)
        if not m:
            continue
        rest = name[len(m.group(0)):]
        if not (rest.startswith("progress") or "dispatch-context-" in name):
            continue
        path = os.path.join(task_dir, name)
        if not os.path.isfile(path):
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        # RM-AG0101：剔除内嵌阶段卡片块——卡内"重派"不是子代理空返回信号
        if any(kw in _strip_agate_card_blocks(text) for kw in _BDD3_EMPTY_RETURN_KEYWORDS):
            hits.add(f"P{m.group(1)}")
    return hits


def phase_num(text):
    """提取首个数字序列；无法解析回退 None（TAG0035 BDD-5：0 不再是"无法解析"的哨兵值，
    调用方需显式判空处理，"无前序阶段"的合法空串场景由调用方 main() 特判为 0，不进入本函数）。"""
    m = re.search(r"[0-9]+", text)
    return int(m.group(0)) if m else None


def _find_stale(old_phase, task_dir):
    """检查被跨过阶段的自撰产出是否仍在原位（列表须与
    agate-archive-stale-outputs.py 的 _OUTPUTS 保持一致）。"""
    for name in _STALE_OUTPUTS.get(old_phase, []):
        if os.path.isfile(os.path.join(task_dir, name)):
            return name
    return ""


def _declares_internal_only(state_file):
    """P1-requirements.md 是否声明 `internal_only`（TAG0042 批0 X9）。

    语义：`internal_only` 表示本任务**不产出对外交付物** ⇒ 协议允许**裁掉 P8（发布）**
    ⇒ 转 READY 的合法前序可以是 P7 而非 P8。
    读取面：与任务同目录的 `P1-requirements.md` 的 frontmatter / 顶层键（`^internal_only:`）。
    读不到 / 解析失败 ⇒ 返回 False（**从严**：要求 P8，不因读不到而放宽）。
    """
    task_dir = os.path.dirname(os.path.abspath(state_file))
    p1 = os.path.join(task_dir, "P1-requirements.md")
    if not os.path.isfile(p1):
        return False
    try:
        with open(p1, encoding="utf-8") as fh:
            for line in fh:
                if re.match(r"^internal_only:\s*true\b", line.rstrip("\r\n")):
                    return True
    except OSError:
        return False
    return False


def _p1_pruned_and_declared(task_dir):
    """读 P1-requirements.md 的结构化 frontmatter → (declared:set, pruned:set)。

    declared = frontmatter `phases`（list 或空格分隔字符串，归一化为 "Pn" 集合）；
    pruned   = frontmatter `pruned` 各条目的 `phase`。
    读不到 / 解析失败 → (None, None)（调用方按 fail-closed 处理）。
    **不得**用 `^phases:\\s*\\[` 正则匹配正文（TAG0050 评审 M-1 明确要求）。
    """
    p1 = os.path.join(task_dir, "P1-requirements.md")
    if not os.path.isfile(p1) or split_frontmatter is None:
        return None, None
    try:
        with open(p1, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return None, None
    fm, _body = split_frontmatter(text)
    if not isinstance(fm, dict):
        return None, None
    phases = fm.get("phases")
    if isinstance(phases, list):
        declared = {str(p).strip() for p in phases if str(p).strip()}
    elif isinstance(phases, str):
        declared = {p for p in phases.split() if p}
    else:
        declared = set()
    pruned = set()
    pruned_raw = fm.get("pruned")
    if isinstance(pruned_raw, list):
        for item in pruned_raw:
            if isinstance(item, dict) and item.get("phase"):
                pruned.add(str(item["phase"]).strip())
    return declared, pruned


def _emit_retry_warnings(task_dir, current_state_data):
    """RM-AG0042 BDD-1/BDD-3：门槛失败事件 ↔ retries 对应性 WARNING（不阻断）。"""
    for bdd1_phase in sorted(_scan_bdd1_review_retry_phase(task_dir)):
        if _retries_len(current_state_data, bdd1_phase) == 0:
            sys.stderr.write(
                f"GATE STATE WARNING: 检测到 {bdd1_phase} 评审重试/复评派发文件，"
                f"但 retries[{bdd1_phase}] 无对应记录（RM-AG0042 BDD-1，不阻断）\n"
            )
    for kw_phase in sorted(_scan_bdd3_keyword_phases(task_dir)):
        if _retries_len(current_state_data, kw_phase) == 0:
            sys.stderr.write(
                f"GATE STATE WARNING: 检测到 {kw_phase} 阶段子代理空返回重派信号，"
                f"但 retries[{kw_phase}] 无对应记录（RM-AG0042 BDD-3，不阻断）\n"
            )


def check_transition(old_phase, new_phase, task_dir, state_file=None, state_basename=None,
                     state_data=None):
    """状态转移合法性**纯函数**（TAG0050 批 A3，设计 §2.7）。

    `main()` 与 `agate-state-set.py` 共用此函数：main() 以 HEAD/暂存 diff 的 old_phase
    调用；state-set 以 **HEAD 版本**为 old_phase、并传入**拟写入**的 `state_data`（含回退时
    已追加的 retries），使"工具当时判定合法"与"提交时判定合法"一致。

    :returns: 阻断性错误消息列表（空 = 合法）。信息性 WARNING（BDD-1/BDD-3）直接写 stderr。
    """
    errors = []
    state_basename = state_basename or (
        os.path.basename(state_file) if state_file else ".state.yaml")

    # TAG0050 批 A1（设计 §2.3 规则 6）：legacy 任务不可重开——从 READY/DONE 回到 Pn
    # → ERROR（提示 --adopt 或新建任务）。非 legacy 任务（有创建事件）不受限。
    if old_phase in ("READY", "DONE") and re.match(r"^P[0-8]$", new_phase or ""):
        _lvl = None
        if task_level is not None:
            try:
                _lvl = task_level(task_dir)
            except Exception:
                _lvl = None
        if _lvl is None:
            errors.append(
                f"legacy 任务不可从 {old_phase} 回到 {new_phase}（账本无创建事件）——"
                "请用 agate-task-init.py --adopt 迁入（at_phase 记为重开的阶段），或新建任务"
            )
            return errors

    # X9（TAG0042 批0）：转 READY 须有已提交的 P8 前序（否则 gate_p8 从不运行）。
    if new_phase == "READY":
        _allowed = ("P8",) if not _declares_internal_only(state_file) else ("P8", "P7")
        if old_phase not in _allowed:
            errors.append(
                f"转为 READY 前须先以 phase=P8 提交发布产出"
                f"（当前前序 phase={old_phase or '(无)'}"
                f"{'；P1 声明 internal_only 时允许 P7' if 'P7' in _allowed else ''}）"
                f"——否则 gate_p8 不会运行；请改为「以 P8 提交产出，再单独提交 READY」"
            )
        return errors

    # M-1：DONE 亦须校验前序（否则 X9 可绕过）。
    if new_phase == "DONE":
        _allowed_done = ("READY", "P8") if not _declares_internal_only(state_file) \
            else ("READY", "P8", "P7")
        if old_phase not in _allowed_done:
            errors.append(
                f"转为 DONE 前的前序 phase 须为 READY 或 P8"
                f"（当前 phase={old_phase or '(无)'}"
                f"{'；P1 声明 internal_only 时允许 P7' if 'P7' in _allowed_done else ''}）"
                f"——否则说明 P8/READY 收尾流程被跳过；请先走「以 P8 提交产出 → 单独提交 READY」"
            )
        return errors

    if new_phase in ("", "PAUSED"):
        return errors

    # old_phase 为空字符串或控制态（PAUSED/READY/DONE）→ 视为"无数字前序阶段"的合法 0。
    old_num = 0 if (not old_phase or old_phase in _CONTROL_PHASES) else phase_num(old_phase)
    new_num = phase_num(new_phase)
    if new_num is None or (old_phase and old_phase not in _CONTROL_PHASES and old_num is None):
        errors.append(f"无法解析阶段序号（old_phase={old_phase!r}, new_phase={new_phase!r}）")
        return errors

    # 检查 1：回退跳变 >= 2（T019 教训）；保留 old_num > 0 守卫（PAUSED→Pn 恢复不误拦）。
    if old_num > 0 and new_num > 0 and old_num - new_num >= 2:
        errors.append(f"回退跳变 P{old_num}→P{new_num}（差 {old_num - new_num}），强制 PAUSED")
        return errors

    # 检查 2：重试超限（P2.4，按阶段差异化 MAX）。
    if state_file and os.path.isfile(state_file):
        env = dict(os.environ)
        env["STATE_FILE"] = state_file
        retries_json = _run_state_get(["retries_over", MAX_RETRY_MAP], env)
        if retries_json and new_phase != "PAUSED":
            errors.append(f"{retries_json}，phase 应为 PAUSED")
            return errors

    current_state_data = state_data if state_data is not None \
        else _load_current_state_yaml(state_file)
    _emit_retry_warnings(task_dir, current_state_data)

    # BDD-2：回退（含单步 diff==1）且暂存/拟写入版本 retries[new_phase] 未超过 HEAD 长度 → 阻断。
    if old_num > 0 and new_num > 0 and old_num > new_num:
        old_retries_len = get_old_retries_len(state_file, state_basename, new_phase) \
            if state_file else 0
        new_retries_len = _retries_len(current_state_data, new_phase)
        if new_retries_len <= old_retries_len:
            errors.append(
                f"回退 P{old_num}->P{new_num}，但 retries[{new_phase}] "
                f"未同步新增记录（RM-AG0042 BDD-2）"
            )
            return errors

    # 检查 4：回退时被跨过阶段是 self-authored 产出阶段且产出未归档 → 拦截。
    if old_num > 0 and new_num > 0 and old_num - new_num == 1 and old_phase in _STALE_OUTPUTS:
        stale_found = _find_stale(old_phase, task_dir)
        if stale_found:
            errors.append(
                f"回退 P{old_num}->P{new_num}，但 {old_phase} 的自撰产出（{stale_found}）仍在原位"
            )
            errors.append(
                f"退回前须先跑：python3 agate/scripts/agate-archive-stale-outputs.py "
                f"{old_phase} {task_dir}"
            )
            return errors

    # 检查 5（TAG0050 评审 M-1）：前向跨阶（delta >= 2）——非 legacy 任务不得跨过
    # 未裁剪/不可裁剪阶段。legacy 任务（task_level 为 None）保持既有行为不变。
    if (old_phase and old_phase not in _CONTROL_PHASES
            and new_phase not in _CONTROL_PHASES and new_num is not None):
        _lvl = None
        if task_level is not None:
            try:
                _lvl = task_level(task_dir)
            except Exception:
                _lvl = None
        if _lvl is not None and old_num is not None and new_num - old_num >= 2:
            skipped = {f"P{i}" for i in range(old_num + 1, new_num)}
            # 不可跳过阶段（见模块级 NON_PRUNABLE_PHASES 与 state-machine.md「不可跳过的阶段」）。
            # 注：P7 可裁剪（`P6--[P6 gate]-->P8`，见 state-machine.md「可跳过的阶段」），
            # 故 P6→P8 是合法前向跳（被跨 P7 已在 pruned 中声明时放行）。
            non_prunable = skipped & NON_PRUNABLE_PHASES
            declared, pruned = _p1_pruned_and_declared(task_dir)
            # 被跨阶段须「已从 P1 phases 移除」**且**「在 pruned 中声明」——两个方向都判
            # （评审 M-1 原型口径）。对合法任务二者等价（check-pruning 强制 phases ∩ pruned = ∅），
            # 对未过裁剪校验的任务则更稳。
            still_declared = skipped & (declared or set())
            not_pruned = skipped - (pruned or set())
            if non_prunable or still_declared or not_pruned:
                reasons = []
                if non_prunable:
                    reasons.append(f"不可跳过阶段 {'/'.join(sorted(non_prunable))}")
                if still_declared:
                    reasons.append(f"仍在 P1 phases 中声明 {'/'.join(sorted(still_declared))}")
                if not_pruned:
                    reasons.append(f"未在 P1 pruned 中声明 {'/'.join(sorted(not_pruned))}")
                errors.append(
                    f"前向跨阶 P{old_num}→P{new_num} 被拒绝（被跨过：{'/'.join(sorted(skipped))}）："
                    + "；".join(reasons)
                    + "。若确为裁剪，请从 P1 phases 移除对应阶段并在 pruned 中声明；否则请逐阶推进。"
                )
                return errors

    return errors


def main():
    state_file = sys.argv[1] if len(sys.argv) > 1 else ".state.yaml"
    state_basename = os.path.basename(state_file)

    # 只在 .state.yaml 有暂存变更时检查
    # tr -d '\r'：Git for Windows 的 diff 输出文件名可能带 CRLF 行尾，grep -qF 精确匹配会失败
    if run_git is None:
        sys.stderr.write("GATE SKIP: check-state-transition: agate_common 不可导入（git 通道不可用），未校验\n")
        sys.exit(0)
    rc, name_only = run_git(["diff", "--cached", "--name-only"])
    if rc != 0:
        sys.stderr.write("GATE SKIP: check-state-transition: git diff --cached 失败，未校验\n")
        sys.exit(0)
    lines = [line.rstrip("\r") for line in name_only.splitlines()]
    if not any(state_basename in line for line in lines):
        sys.stderr.write(f"GATE SKIP: check-state-transition: 暂存区无 {state_basename}，未校验\n")
        sys.exit(0)

    old_phase = get_old_phase(state_file, state_basename)
    new_phase = get_new_phase(state_file)
    task_dir = os.path.dirname(state_file) or "."

    errors = check_transition(old_phase, new_phase, task_dir, state_file, state_basename)
    if errors:
        for msg in errors:
            sys.stderr.write(f"GATE STATE: {msg}\n")
        sys.exit(1)

    if new_phase == "READY":
        sys.stderr.write(
            f"GATE OK: check-state-transition: P8 前序已就位（old_phase={old_phase}）→ READY\n"
        )
    elif new_phase == "DONE":
        sys.stderr.write(
            f"GATE OK: check-state-transition: 收尾前序已就位（old_phase={old_phase}）→ DONE\n"
        )
    elif new_phase in ("", "PAUSED"):
        sys.stderr.write(
            f"GATE SKIP: check-state-transition: 非推进场景（new_phase={new_phase!r}），未校验\n"
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
