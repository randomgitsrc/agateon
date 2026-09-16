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
    from agate_common import run_git
except ImportError:
    _DEFAULT_MAX_RETRY_MAP = "P1:3,P2:3,P3:2,P4:3,P5:2,P6:2,P7:2,P8:2"
    run_git = None

try:
    import yaml
except ImportError:
    yaml = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
AGATE_STATE_GET = os.path.join(SCRIPT_DIR, "agate-state-get.py")

MAX_RETRY_MAP = os.environ.get("MAX_RETRY_MAP", _DEFAULT_MAX_RETRY_MAP)

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
        if any(kw in text for kw in _BDD3_EMPTY_RETURN_KEYWORDS):
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


def main():
    state_file = sys.argv[1] if len(sys.argv) > 1 else ".state.yaml"
    state_basename = os.path.basename(state_file)

    # 只在 .state.yaml 有暂存变更时检查
    # tr -d '\r'：Git for Windows 的 diff 输出文件名可能带 CRLF 行尾，grep -qF 精确匹配会失败
    if run_git is None:
        sys.exit(0)
    rc, name_only = run_git(["diff", "--cached", "--name-only"])
    if rc != 0:
        sys.exit(0)
    lines = [line.rstrip("\r") for line in name_only.splitlines()]
    if not any(state_basename in line for line in lines):
        sys.exit(0)

    old_phase = get_old_phase(state_file, state_basename)
    new_phase = get_new_phase(state_file)

    if new_phase in ("", "PAUSED", "READY", "DONE"):
        sys.exit(0)

    # old_phase 为空字符串（get_old_phase 的 git-show 失败回退）或控制态
    # PAUSED/READY/DONE（与上面 new_phase 特判同一组字面量，PAUSED 恢复场景的
    # 合法前序态）时，视为"无数字前序阶段"的合法 0，不进入 phase_num() 解析、
    # 不触发下面的判空报错（DESIGN_GAP：dispatch-context 给出的判空条件原文只
    # 特判了空字符串，未覆盖 old_phase=PAUSED 场景；PAUSED→Pn 恢复是既有回归用例
    # test_st_15/test_st_19 覆盖的既有行为，若不补此特判会在这两个已有测试上产生
    # 新回归——按 old_num>0 判据的既有语义，控制态本就等价于"无前序数字阶段"）。
    old_num = 0 if (not old_phase or old_phase in ("PAUSED", "READY", "DONE")) else phase_num(old_phase)
    new_num = phase_num(new_phase)
    if new_num is None or (old_phase and old_phase not in ("PAUSED", "READY", "DONE") and old_num is None):
        sys.stderr.write(
            f"GATE STATE: 无法解析阶段序号（old_phase={old_phase!r}, new_phase={new_phase!r}）\n"
        )
        sys.exit(1)

    # 检查 1：回退跳变 >= 2（T019 教训）
    # 协议规定"不依赖 commit message 格式"（state-machine.md L371-373）
    # .gate-history.jsonl 的 PAUSED 验证功能已被 HEAD/staged diff 机制隐式覆盖
    # （PAUSED 单独 commit 时 HEAD=PAUSED → 早退 exit 0）
    # 保留 old_num > 0 守卫：PAUSED→Pn 恢复（old_num=0）不被误拦
    if old_num > 0 and new_num > 0:
        diff = old_num - new_num
        if diff >= 2:
            sys.stderr.write(
                f"GATE STATE: 回退跳变 P{old_num}→P{new_num}（差 {diff}），强制 PAUSED\n"
            )
            sys.exit(1)

    # 检查 2：重试超限（P2.4，按阶段差异化 MAX）
    # .state.yaml 的 retries[Pn] 是列表（每次重试一个对象），不是整数
    # 按 retries dict 的 key 逐阶段查 MAX_RETRY，不是按 new_phase
    if os.path.isfile(state_file):
        env = dict(os.environ)
        env["STATE_FILE"] = state_file
        retries_json = _run_state_get(["retries_over", MAX_RETRY_MAP], env)

        if retries_json and new_phase != "PAUSED":
            sys.stderr.write(f"GATE STATE: {retries_json}，phase 应为 PAUSED\n")
            sys.exit(1)

    # 检查 3：门槛失败事件 ↔ retries 对应性校验（RM-AG0042 BDD-1~4，P2-design.md §2.1 候选A）
    # 校验强度分层（D1）：BDD-1/BDD-3 高优 WARNING（不阻断，信号源置信度较低）；
    # BDD-2 阻断（结构化数值比较，误报率低）。
    task_dir = os.path.dirname(state_file)
    current_state_data = _load_current_state_yaml(state_file)

    # BDD-1：评审角色重试/复评 dispatch-context 文件存在 + retries[Pn] 为空/缺失 → 高优 WARNING
    # （逐个命中阶段分别检查，参照 BDD-3 分支已有的 for 循环写法，CRITICAL 3 修复）
    for bdd1_phase in sorted(_scan_bdd1_review_retry_phase(task_dir)):
        if _retries_len(current_state_data, bdd1_phase) == 0:
            sys.stderr.write(
                f"GATE STATE WARNING: 检测到 {bdd1_phase} 评审重试/复评派发文件，"
                f"但 retries[{bdd1_phase}] 无对应记录（RM-AG0042 BDD-1，不阻断）\n"
            )

    # BDD-3：子代理空返回重派关键词信号 + retries[Pn] 为空/缺失 → 高优 WARNING
    for kw_phase in sorted(_scan_bdd3_keyword_phases(task_dir)):
        if _retries_len(current_state_data, kw_phase) == 0:
            sys.stderr.write(
                f"GATE STATE WARNING: 检测到 {kw_phase} 阶段子代理空返回重派信号，"
                f"但 retries[{kw_phase}] 无对应记录（RM-AG0042 BDD-3，不阻断）\n"
            )

    # BDD-2：回退（含单步 diff==1，现有检查1的 diff>=2 不覆盖这种情况）且暂存版本
    # retries[new_phase] 长度未超过 HEAD 版本长度（本次 commit 没有为这次回退追加记录）
    # → 阻断。按 P1-requirements.md BDD-2 原文字面语义实现：不要求"该阶段此前必须已有过
    # 记录"这一前提——RM-AG0042 立项证据本身（复盘中四任务 retries 全为 {}）就是"从未记录过"
    # 的首次单步回退场景，若保留该前提则本任务修不到自己的立项场景（P4-review.md CRITICAL 1，
    # 主 Agent 范围决策：采用方案 A，去掉 old_retries_len>0 守卫）。
    if old_num > 0 and new_num > 0 and old_num > new_num:
        old_retries_len = get_old_retries_len(state_file, state_basename, new_phase)
        new_retries_len = _retries_len(current_state_data, new_phase)
        if new_retries_len <= old_retries_len:
            sys.stderr.write(
                f"GATE STATE: 回退 P{old_num}->P{new_num}，但 retries[{new_phase}] "
                f"未同步新增记录（RM-AG0042 BDD-2）\n"
            )
            sys.exit(1)

    # 检查 4：回退时若被跨过阶段是 self-authored 产出阶段（P1/P2/P6/P7），
    # 且该阶段的产出文件仍在原位（未归档）-> 拦截，要求先跑 agate-archive-stale-outputs.py
    # （self-authored gate 产出不能跨重试静默复用，见 LIMITATIONS.md self-authored 分类）
    if old_num > 0 and new_num > 0:
        diff = old_num - new_num
        if diff == 1 and old_phase in _STALE_OUTPUTS:
            task_dir = os.path.dirname(state_file)
            stale_found = _find_stale(old_phase, task_dir)
            if stale_found:
                sys.stderr.write(
                    f"GATE STATE: 回退 P{old_num}->P{new_num}，但 {old_phase} 的自撰产出（{stale_found}）仍在原位\n"
                )
                sys.stderr.write(
                    f"  退回前须先跑：python3 agate/scripts/agate-archive-stale-outputs.py {old_phase} {task_dir}\n"
                )
                sys.stderr.write(
                    "  （self-authored gate 产出不能跨重试静默复用，见 LIMITATIONS.md self-authored 分类）\n"
                )
                sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
