#!/usr/bin/env python3
"""pre-commit-gate.py — pre-commit hook 入口（TAG0010 批次 3a 主程序）

从 pre-commit-gate.sh（404 行）迁移调度逻辑。sh 版将保留为薄壳（批次 3d，只做
「AGATE_ROOT 自定位 + python 探测 + exec py + 失败阻断」），本 py 承载全部 gate
调度判定。

结构（与 sh 版逐段对应）：
- REPO_ROOT / AGATE_ROOT / 工作区解析（resolve_workspace）
- 收集所有暂存的 .state.yaml（根 + 任务级，S1 数组化：空格路径不再切词）
- 每个 state file：格式校验 → phase 变更检测 → 状态转移 → OLD_PHASE →
  反推 TASK_DIR → phase-产出一致性 WARNING → PROD_TOUCHED 三步检测 →
  frontmatter schema → P6 格式归一化 → check-gate → write_gate_result →
  P6 provenance / pruning / scope → dispatch-context hash 校验 → retrospective →
  CHANGELOG（P8）→ P6 evidence（P6/P7）→ B3 / E3 → gate 结果处理
- 扫描暂存 P{n}-*.md（无 .state.yaml 变更的任务也检查一致性）

子脚本调度：全部已 py 化 → sys.executable <x>.py（12 个子脚本 + agate-state-get.py
helper）。fail-closed：py 主程序不可用/执行失败 → GATE ERROR + exit 1（阻断 commit，
不运行 sh 兜底）。

AGATE_ROOT 用 agate_common.resolve_agate_root（env 优先 → 脚本真实路径上溯 →
复制模式 .agate-root 恢复）；write_gate_result / read_state_phase / read_state_task_id /
run_git / resolve_workspace 均从 agate_common import。公共库 import 失败（缺 pyyaml /
agate_common.py 缺失）→ fail-closed 阻断。

CLI 契约：hook 无参数运行；exit 0/1；输出 `GATE P{n} ...` 格式（全部写 stderr，同 sh）。

Python 3.8+（无 match / str.removeprefix）；所有文本读写显式 encoding="utf-8"。
"""

import glob
import hashlib
import os
import re
import subprocess
import sys

# SCRIPT_DIR 用 realpath 解析（hook 软链场景：git 经 .git/hooks/pre-commit 软链调起时
# __file__ 指向软链路径，不解析会导致子脚本/公共库定位失败——与 sh 的 readlink -f 语义一致）
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
# 软链调起时 sys.path[0] 是软链所在目录（.git/hooks），agate_common 在真实 scripts 目录——
# 显式插入 SCRIPT_DIR，保证 import 稳定（正常直调时该路径已在 sys.path，重复插入无害）
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

try:
    from agate_common import (
        append_event,
        read_state_phase,
        read_state_task_id,
        resolve_agate_root,
        resolve_workspace,
        run_git,
        write_gate_result,
    )
except Exception as exc:
    # 注意：agate_common 缺 pyyaml 时自身会打印提示并 sys.exit(1)（SystemExit 不在此
    # 捕获，仍 fail-closed exit 1）；此处捕获 ImportError（agate_common.py 本体缺失，
    # 如脚本被独立复制到缺公共库的目录）。
    sys.stderr.write(
        f"GATE ERROR: 无法加载 agate_common.py（公共库缺失，需 python3 + pyyaml）: {exc}\n"
    )
    sys.exit(1)

# 各阶段产出文件（2p dispatch-context 缺失强制检查用，sh case 等价）
_PHASE_OUTPUT = {
    "P1": r"P1-requirements\.md",
    "P2": r"P2-design\.md",
    "P3": r"P3-test-cases\.md",
    "P6": r"P6-acceptance\.md",
    "P7": r"P7-consistency\.md",
    "P8": r"P8-release\.md",
}
_PHASE_OUTPUT_DIR = {"P5": "P5-test-results"}

# E3 证据文件例外前缀（sh grep -vE "^${TASK_REL}/(P[0-9]-evidence/|evidences/)"）
# gate-events.jsonl（TAG0020 事件账本）与 .state.yaml 同类 = gate 元数据文件：
# 随任务目录落库（audit trail），不应被 2n.2/2p 的"非 md/yaml 源码文件"判定误拦。
_NON_MD_YAML_RE = re.compile(r"\.(md|yaml)$|^\.state|gate-events\.jsonl$")
_P_OUTPUT_RE = re.compile(r"P[0-8]-.*\.md$")
_P_NUM_RE = re.compile(r"P[0-8]")
# 宽松探测正则（TAG0035 BDD-6）：不限定数字阶段号（P[0-8]），用于在窄口径
# _P_OUTPUT_RE 过滤之外并行探测"看起来是阶段产出但阶段名非标准数字"的文件
# （如 p-alpha-notes.md）。只用于差集 WARNING 提示，不参与既有一致性判定分支，
# 不改变 _P_OUTPUT_RE/_P_NUM_RE/_phase_num 本身的匹配范围（BDD-7 回归要求）。
_P_OUTPUT_ANY_RE = re.compile(r"(?:^|/)[Pp][^/]*-.*\.md$")
_STATE_YAML_SUFFIX = ".state.yaml"


# ---------- 通用工具 ----------


def _staged_name_only(diff_filter=None):
    """git diff --cached [--diff-filter=A] --name-only（tr -d '\r' 逐行等价）。

    sh 的 DIFF_CACHED 统一 tr -d '\r'（Git for Windows CRLF 行尾）；每处调用都是独立
    git 子进程（sh 同样每处重跑 git diff --cached），此处保持一致。
    """
    args = ["diff", "--cached"]
    if diff_filter:
        args.append("--diff-filter=" + diff_filter)
    args.append("--name-only")
    rc, out = run_git(args)
    if rc != 0:
        return []
    return [line.rstrip("\r") for line in out.splitlines() if line.strip()]


def _run_script_rc(script, args, suppress_stderr=False):
    """调 agate/scripts/{script}（sys.executable），仅取 exit code。

    等价 sh `bash "$AGATE_ROOT/scripts/x.sh" args`（stdout/stderr 透传）或
    `... 2>/dev/null`（suppress_stderr）。脚本缺失/执行失败 → 1（fail-closed）。
    """
    path = os.path.join(SCRIPT_DIR, script)
    if not os.path.isfile(path):
        return 1
    stderr = subprocess.DEVNULL if suppress_stderr else None
    try:
        proc = subprocess.run([sys.executable, path, *args], stderr=stderr)
    except OSError:
        return 1
    return proc.returncode


def _run_script_capture(script, args, merge=False, suppress_stderr=False, input_text=None):
    """调 agate/scripts/{script}（sys.executable），返回 (rc, stdout)。

    merge=True → stderr 并入 stdout（sh 的 2>&1）；suppress_stderr=True → stderr 丢弃
    （sh 的 2>/dev/null）；input_text → 写入子进程 stdin（sh 的管道 `git show | agate-state-get`）。
    脚本缺失/执行失败 → (1, "")。
    """
    path = os.path.join(SCRIPT_DIR, script)
    if not os.path.isfile(path):
        return 1, ""
    stdout_pipe = subprocess.PIPE
    if merge:
        stderr = subprocess.STDOUT
    elif suppress_stderr:
        stderr = subprocess.DEVNULL
    else:
        stderr = subprocess.PIPE
    try:
        proc = subprocess.run(
            [sys.executable, path, *args],
            stdout=stdout_pipe, stderr=stderr,
            text=True, encoding="utf-8", errors="replace",
            input=input_text,
        )
    except OSError:
        return 1, ""
    return proc.returncode, (proc.stdout or "")


def _judge_enabled(task_dir):
    """读 .state.yaml 的 judge.enabled（TAG0020 P6.5 注入条件，BDD-2 历史兼容）。

    缺失/无 judge 块/解析失败 → False（历史任务全链跳过 P6.5，不要求 judge 产物）。
    """
    state_file = os.path.join(task_dir, ".state.yaml")
    if not os.path.isfile(state_file):
        return False
    try:
        import yaml
        with open(state_file, encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f)
    except Exception:
        return False
    if not isinstance(data, dict):
        return False
    judge = data.get("judge")
    return bool(isinstance(judge, dict) and judge.get("enabled"))


def _extract_card(file_path):
    """sed -n '/<!-- AGATE_CARD_START -->/,/<!-- AGATE_CARD_END -->/p' 区间抽取等价。

    返回两标记之间的行（不含标记行），CR 剥离（sh sed '1d;$d' + tr -d '\r' 语义）；
    无 END 时读到文件尾（sed 语义）；未闭合块读到 EOF。
    """
    with open(file_path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    out = []
    in_block = False
    for line in lines:
        if not in_block:
            if "<!-- AGATE_CARD_START -->" in line:
                in_block = True
            continue
        if "<!-- AGATE_CARD_END -->" in line:
            break
        out.append(line.replace("\r", ""))
    return "\n".join(out)


def _phase_num(phase_text):
    """提取首个 P[0-8]；无匹配返回 None（sh grep -oE 'P[0-8]' | head -1）。"""
    m = _P_NUM_RE.search(phase_text or "")
    return m.group(0) if m else None


def _is_processed_dir(processed_dirs, candidate):
    """PROCESSED_DIRS 成员判断（S1 数组化：空格目录不再切词拆段）。"""
    return candidate in processed_dirs


# ---------- 主流程 ----------


def main():
    # REPO_ROOT = 当前 git 仓库根（项目仓库或 agate 仓库本身）
    # realpath -m 归一（Git for Windows 的 --show-toplevel 返回 C:/...，统一归一）
    rc, out = run_git(["rev-parse", "--show-toplevel"])
    repo_root = out.strip() if rc == 0 and out.strip() else os.getcwd()
    repo_root = os.path.realpath(repo_root)

    # AGATE_ROOT = 协议本体路径（env 优先 → 脚本真实路径上溯 → 复制模式 .agate-root 恢复）
    resolve_agate_root(os.path.abspath(__file__))

    # 工作区路径单点解析（TAG0003 v2.0）：.agate.env > env AGATE_TASKS_DIR > 默认
    # agate-workspace/。resolve_workspace 等价 agate-workspace-resolve.sh 的 source 语义。
    _workspace, tasks_dir = resolve_workspace(repo_root)

    # 1. 收集所有暂存的 .state.yaml 文件（根 + 任务级）
    staged_all = _staged_name_only()
    state_files = [
        os.path.join(repo_root, f) for f in staged_all if f.endswith(_STATE_YAML_SUFFIX)
    ]

    # 2. 对每个暂存的 .state.yaml：格式校验 + 状态转移 + gate
    for state_file in state_files:
        if not os.path.isfile(state_file):
            continue

        # 2a. 格式校验（任何变更都触发）
        if _run_script_rc("check-state-yaml.py", [state_file]) != 0:
            sys.exit(1)

        # 2b. 检测 phase 是否变更
        state_rel = os.path.relpath(state_file, repo_root)
        phase_changed = False
        if os.sep != "/":
            state_rel = state_rel.replace(os.sep, "/")
        rc, diff_out = run_git(["diff", "--cached", "--", state_rel])
        if rc == 0:
            for line in diff_out.splitlines():
                if re.match(r"^\+.*phase:", line.rstrip("\r")):
                    phase_changed = True
                    break

        # 2c. 状态转移检查（phase 变更时）
        if phase_changed and _run_script_rc("check-state-transition.py", [state_file]) != 0:
            sys.exit(1)

        # 2d. 读取状态
        phase = read_state_phase(state_file)
        task_id = read_state_task_id(state_file)
        if not phase:
            continue
        if not task_id:
            continue

        # 2d.1 读取 HEAD（commit 前）版本的 phase，供 check-gate 判断是否为回退抵达
        # git show HEAD:STATE_REL | agate-state-get.py phase_stdin；失败/缺失 → 留空
        # （同 sh || echo "" 语义，OLD_PHASE 空时 check-gate 行为与不传完全一致）
        old_phase = ""
        if state_rel:
            _rc_show, shown = run_git(["show", "HEAD:" + state_rel])
            if _rc_show == 0:
                _rc3, old_phase = _run_script_capture(
                    "agate-state-get.py", ["phase_stdin"],
                    suppress_stderr=True, input_text=shown)
                if _rc3 != 0:
                    old_phase = ""
                old_phase = old_phase.rstrip("\n")

        # 2e. 反推 TASK_DIR
        state_dir = os.path.dirname(state_file)
        task_dir = os.path.join(tasks_dir, task_id) if state_dir == repo_root else state_dir

        # 2f. phase-产出一致性检查（WARNING，不拦截）
        task_rel = os.path.relpath(task_dir, repo_root)
        if os.sep != "/":
            task_rel = task_rel.replace(os.sep, "/")
        prefix = task_rel + "/"
        staged_outputs = [
            f for f in _staged_name_only()
            if f.startswith(prefix) and _P_OUTPUT_RE.search(f)
        ]
        staged_added = [
            f for f in _staged_name_only("A")
            if f.startswith(prefix) and _P_OUTPUT_RE.search(f)
        ]
        for out_file in staged_outputs:
            out_phase = _phase_num(out_file)
            if out_phase and out_phase != phase:
                out_num = out_phase[1:]
                phase_num = phase[1:]
                if out_num.isdigit() and phase_num.isdigit() \
                        and int(out_num) < int(phase_num) and out_file in staged_added:
                    continue
                sys.stderr.write(
                    f"GATE WARNING: 暂存了 {out_phase} 产出但 phase={phase}（{task_id}）——请确认是否需要更新 phase\n"
                )

        # 2f.1 宽松探测差集扫描（TAG0035 BDD-6）：命中 _P_OUTPUT_ANY_RE 但未命中
        # 窄口径 _P_OUTPUT_RE 的文件（非标准数字阶段名产出），不参与上面的一致性
        # 判定，只做提示，不影响 exit code。
        staged_any_outputs = [
            f for f in _staged_name_only()
            if f.startswith(prefix) and _P_OUTPUT_ANY_RE.search(f) and not _P_OUTPUT_RE.search(f)
        ]
        for any_out_file in staged_any_outputs:
            sys.stderr.write(
                f"GATE WARNING: 无法识别该产出文件的阶段号，一致性检查未覆盖: {any_out_file}\n"
            )

        # 2g. 跳过非 gate 阶段
        if phase in ("PAUSED", "READY", "DONE"):
            continue
        if not os.path.isdir(task_dir):
            continue

        # 2g.1 PROD_TOUCHED 检测（P1.2）——仅扫任务目录下的暂存 diff
        # 三步检测（正向→中止 / 不合规→中止 / 缺失→静默通过）+ 只扫新增行
        if any(f.startswith(prefix) for f in _staged_name_only()):
            _rc_diff, diff_raw = run_git(["diff", "--cached", "--", task_rel])
            diff_added = []
            in_card = False
            for raw_line in (diff_raw or "").splitlines():
                if not (len(raw_line) >= 2 and raw_line[0] == "+" and raw_line[1] != "+"):
                    continue
                line = raw_line[1:]
                if not in_card and "<!-- AGATE_CARD_START -->" in line:
                    in_card = True
                    continue
                if in_card:
                    if "<!-- AGATE_CARD_END -->" in line:
                        in_card = False
                    continue
                diff_added.append(line)
            if any(re.match(r"^\s*-?\s*\[PROD_TOUCHED\]", ln) for ln in diff_added):
                sys.stderr.write(
                    f"GATE: [PROD_TOUCHED] 检测到生产环境接触（{task_id}），commit 中止\n")
                sys.exit(1)
            if any(re.match(r"^\s*-?\s*\[PROD_TOUCHED\]\s*$", ln) for ln in diff_added):
                sys.stderr.write(
                    f"GATE: 不合规的 PROD_TOUCHED 标记格式（{task_id}），须用行首 [PROD_TOUCHED] 或 [PROD_NOT_TOUCHED] 声明\n")
                sys.exit(1)

        # 2g.2 frontmatter schema 校验（P2-design.md §3.1.3，BDD-8 挂载点）
        # 与 2a 同机制：扫描本任务暂存的 P1/P2/P6/P7 产出文件，逐个跑 check-frontmatter
        if os.path.isfile(os.path.join(SCRIPT_DIR, "check-frontmatter.py")):
            for fm_name in ("P1-requirements.md", "P2-design.md", "P6-acceptance.md", "P7-consistency.md"):
                if (task_rel + "/" + fm_name) in _staged_name_only() and _run_script_rc("check-frontmatter.py", [os.path.join(task_dir, fm_name)]) != 0:
                    sys.exit(1)

        # 2h. P6 格式自动归一化（①）——verifier 产出后、gate 前
        if phase == "P6" and os.path.isfile(os.path.join(task_dir, "P6-acceptance.md")):
            _run_script_rc("check-p6-format.py", ["--fix", os.path.join(task_dir, "P6-acceptance.md")])
            run_git(["add", os.path.join(task_dir, "P6-acceptance.md")])

        # 2h.1 运行 gate（P1.1）——2>&1 合并捕获（sh $() 语义，剥尾换行）
        _gc_rc, gate_output = _run_script_capture(
            "check-gate.py", [phase, task_dir, old_phase], merge=True)
        gate_exit = _gc_rc
        gate_output = gate_output.rstrip("\n")

        # 2h.1 写 gate 结果（供 CI backstop 检测 --no-verify 绕过）
        write_gate_result(phase, task_id, gate_exit, gate_output)

        # 2h.1b 事件账本写入（TAG0020 BDD-7：gate_run 事件，append-only 哈希链单点）
        # append_event 内部失败仅 WARNING；此处再兜一层异常，确保任何意外都不阻断 commit
        try:
            append_event(task_dir, {
                "event": "gate_run",
                "phase": phase,
                "cmd": "check-gate.py " + phase,
                "exit": gate_exit,
                "runner": "pre-commit",
            })
        except Exception as exc:
            sys.stderr.write(f"GATE WARNING: gate_run 事件写入失败（不阻断 commit）: {exc}\n")

        # 2h.1c 状态转移事件（TAG0020 BDD-7：phase 变更时记 state_transition；.state.yaml
        # 仍为权威状态源，事件只记录不改写——双写语义，P2 §3.2 R1）
        if phase_changed:
            try:
                append_event(task_dir, {
                    "event": "state_transition",
                    "phase": phase,
                    "from": old_phase or "",
                    "to": phase,
                })
            except Exception as exc:
                sys.stderr.write(f"GATE WARNING: state_transition 事件写入失败（不阻断 commit）: {exc}\n")

        # 2i. P6 客观行为审计（P2.1/P2.10）
        if gate_exit != 1 and _run_script_rc("check-p6-provenance.py", [task_dir]) == 1:
            sys.exit(1)

        # 2i.1 P6.5 judge 复核 + 事件账本审计（TAG0020，commit-time 硬边界；P2 §3.5 候选 1）
        # judge 启用（.state.yaml judge.enabled == true）且 verdict 已产出 → 依次调
        # check-judge-verdict + check-events，任一 exit 1 → 阻断 commit。
        # enforcement 与 commit 位置解耦（注入条件不依赖 phase 值）：verdict 落库的
        # 任何后续 commit（含 P7 commit）都会重验；历史任务（无 judge.enabled）天然跳过。
        if (gate_exit != 1
                and _judge_enabled(task_dir)
                and os.path.isfile(os.path.join(task_dir, "P6.5-judge-verdict.md"))
                and (_run_script_rc("check-judge-verdict.py", [task_dir]) == 1
                     or _run_script_rc("check-events.py", [task_dir]) == 1)):
            sys.exit(1)

        # 2j. 裁剪条件检查（P2.7-P2.9）
        if gate_exit != 1 and _run_script_rc("check-pruning.py", [task_dir]) == 1:
            sys.exit(1)

        # 2j.1. ceremony 路由校验（TAG0019 D3，BDD-7/9）：与 2j check-pruning 并列；
        # 无 ceremony 声明 exit 0 不拦截（向后兼容，BDD-8）
        if gate_exit != 1 and _run_script_rc("check-routing.py", [task_dir]) == 1:
            sys.exit(1)

        # 2j.2 结构一致性 gate（TAG0021 M2，BDD-10）：与 check-gate 并列独立 step，不短路——
        # 协议漂移（rules/*.yaml ↔ 协议 md）与任务 gate 独立判定。脚本缺失（旧版协议 /
        # 测试 fake 根未复制该脚本）→ fail-open 跳过（feature 未就位不阻断既有流程）；
        # 存在且 exit 1（S-1~S-6 漂移 ERROR）→ 阻断 commit。check-structure-consistency.py
        # 自身 --strict-errors-only 常开（P2-design §3.3）。
        if os.path.isfile(os.path.join(SCRIPT_DIR, "check-structure-consistency.py")) and _run_script_rc(
            "check-structure-consistency.py", []
        ) == 1:
            sys.stderr.write(
                "GATE: 结构一致性漂移（check-structure-consistency.py exit 1）——"
                "rules/*.yaml 与协议 md 不一致，阻断 commit（TAG0021 BDD-10）\n"
            )
            sys.exit(1)

        # 2k. SCOPE+ 追踪检查（P2.11）
        if gate_exit != 1 and _run_script_rc("check-scope-resolved.py", [task_dir]) == 1:
            sys.exit(1)

        # 2p. dispatch-context 卡片 hash 校验（防漂移：嵌入卡片是当前版本）
        # 所有 P1-P8 阶段统一强制 dispatch-context 存在
        if os.path.isfile(os.path.join(SCRIPT_DIR, "agate-next-card.py")):
            dc_files = sorted(glob.glob(os.path.join(task_dir, phase + "-dispatch-context-*.md")))
            if dc_files:
                expected_rc, expected_out = _run_script_capture(
                    "agate-next-card.py", [phase], suppress_stderr=True)
                expected = expected_out if expected_rc == 0 else ""
                if expected:
                    # Windows checkout 的 dispatch-context 是 CRLF（autocrlf），卡片源是 LF——
                    # 提取的 EMBEDDED 归一化行尾再比 hash，否则恒 mismatch（TAG0009）
                    expected_hash = hashlib.sha256(
                        expected.replace("\r", "").rstrip("\n").encode("utf-8")).hexdigest()
                    for dc_file in dc_files:
                        embedded = _extract_card(dc_file)
                        embedded_hash = hashlib.sha256(embedded.encode("utf-8")).hexdigest()
                        if embedded_hash != expected_hash:
                            sys.stderr.write(
                                f"GATE: {os.path.basename(dc_file)} 卡片内容与 CLI 输出不一致（hash mismatch）\n")
                            sys.stderr.write(f"      期望 sha256: {expected_hash}\n")
                            sys.stderr.write(f"      实际 sha256: {embedded_hash}\n")
                            sys.stderr.write(
                                f"      提示：重新调 agate-next-card.py {phase} 复制到 dispatch-context 文件\n")
                            sys.exit(1)
            else:
                # 仅当暂存了该阶段的产出文件时才强制要求 dispatch-context
                # 中间 commit / legacy 任务 / 裁剪跳阶 → 不强制
                staged_in_task = [f for f in _staged_name_only() if f.startswith(prefix)]
                has_output = False
                phase_output = _PHASE_OUTPUT.get(phase)
                if phase_output and any(re.search(phase_output, f) for f in staged_in_task):
                    has_output = True
                phase_output_dir = _PHASE_OUTPUT_DIR.get(phase)
                if phase_output_dir and os.path.isdir(os.path.join(task_dir, phase_output_dir)):
                    has_output = True
                if has_output:
                    sys.stderr.write(
                        f"GATE: subagent 派发阶段产出 commit 需提供 {phase}-dispatch-context-{{role}}.md（至少一个，当前阶段卡片嵌入）\n")
                    sys.stderr.write(
                        f"      提示：调 agate-next-card.py {phase} 嵌入 dispatch-context 模板\n")
                    sys.exit(1)
                # P4: 用代码文件判断
                if phase == "P4" and any(
                        not _NON_MD_YAML_RE.search(f) for f in staged_in_task):
                    sys.stderr.write(
                        f"GATE: subagent 派发阶段产出 commit 需提供 {phase}-dispatch-context-{{role}}.md（至少一个，当前阶段卡片嵌入）\n")
                    sys.stderr.write(
                        f"      提示：调 agate-next-card.py {phase} 嵌入 dispatch-context 模板\n")
                    sys.exit(1)

        # 2l. 复盘异常触发（P2.12）——只提醒不中止（sh 2>/dev/null || true）
        _run_script_rc(
            "check-retrospective.py", [task_dir, state_file], suppress_stderr=True)

        # 2m. CHANGELOG 检查（P1.6）——仅 P8 phase 检查，其他阶段不触发
        if phase == "P8" and _run_script_rc("check-changelog.py", [task_id], suppress_stderr=True) != 0:
            sys.stderr.write(
                f"GATE CHANGELOG: 警告 — [Unreleased] 未记录 {task_id}\n")

        # 2n. P6 证据格式检查（P1.7）——exit 1 拦截 / exit 2 仅提示
        if phase in ("P6", "P7"):
            evidence_rc, evidence_output = _run_script_capture(
                "check-p6-evidence.py", [task_dir], merge=True)
            if evidence_rc == 1:
                sys.stderr.write(evidence_output)
                sys.exit(1)
            elif evidence_rc == 2:
                sys.stderr.write(evidence_output)

        # 2n.1 dispatch-context missing WARNING (B3)
        # Only warn when 2p hash check is not active (agate-next-card.py not available)
        if not os.path.isfile(os.path.join(SCRIPT_DIR, "agate-next-card.py")):
            staged_output_in_task = [
                f for f in _staged_name_only()
                if f.startswith(prefix) and _P_OUTPUT_RE.search(f)
            ]
            if staged_output_in_task and not glob.glob(os.path.join(task_dir, phase + "-dispatch-context-*.md")):
                # Check if old format exists in HEAD (transitional)
                has_dc_in_head = False
                rc_ls, ls_out = run_git(["ls-tree", "HEAD", task_rel + "/"])
                if rc_ls == 0:
                    has_dc_in_head = any(
                        re.search(phase + r"-dispatch-context-.*\.md$", line)
                        for line in ls_out.splitlines()
                    )
                if not has_dc_in_head:
                        sys.stderr.write(
                            f"GATE WARNING: {phase} 产出已暂存但 {phase}-dispatch-context-*.md 不存在——是否忘记先写 dispatch-context？\n")

        # 2n.2 non-phase code staging WARNING/BLOCK (E3, P6 self-authored gate 区分证据/源码)
        all_nonmd = [f for f in _staged_name_only() if not _NON_MD_YAML_RE.search(f)]
        non_evidence_files = [
            f for f in all_nonmd
            if not re.search(r"^" + re.escape(task_rel) + r"/(P[0-9]-evidence/|evidences/)", f)
        ]
        if non_evidence_files:
            if phase in ("P4", "P5"):
                pass  # 外部产出 gate：代码变更是预期行为
            elif phase == "P6":
                sys.stderr.write("GATE: phase=P6 暂存了项目源码/非证据文件（不在 P6-evidence/ 下）——\n")
                sys.stderr.write("  P6 是 self-authored gate 的验收阶段，不应直接改代码。\n")
                sys.stderr.write("  若验收发现问题，应退回至实现阶段重新派发 implementer，而非在 P6 自行修复。\n")
                sys.stderr.write("  （见 LIMITATIONS.md「主 Agent 遇到困难时倾向于自行解决」已知风险模式，\n")
                sys.stderr.write("   退回步骤见 agate/rules/state-transitions.md 回退规则）\n")
                sys.exit(1)
            else:
                sys.stderr.write(
                    f"GATE WARNING: phase={phase} 但暂存了代码文件——主 Agent 是否在非实现阶段直接改代码？\n")

        # 2o. gate 结果处理
        if gate_exit == 0:
            sys.stderr.write(f"GATE {phase} ({task_id}): 通过\n")
        elif gate_exit == 1:
            sys.stderr.write(f"GATE {phase} ({task_id}): 未通过\n")
            sys.stderr.write(gate_output + "\n")
            sys.exit(1)
        elif gate_exit == 2:
            sys.stderr.write(f"GATE {phase} ({task_id}): 需主 Agent 手动判断\n")
            sys.stderr.write(gate_output + "\n")

    # 3. 扫描暂存的 P{n}-*.md 产出文件（无 .state.yaml 变更的任务也检查一致性）
    # 只做 WARNING，不拦截——覆盖"产出了但忘改 phase"的场景
    processed_dirs = []
    for sf in state_files:
        if not os.path.isfile(sf):
            continue
        state_dir = os.path.dirname(sf)
        if state_dir == repo_root:
            continue
        processed_dirs.append(state_dir)

    staged_added_all = [
        f for f in _staged_name_only("A") if _P_OUTPUT_RE.search(f)
    ]
    for staged_file in staged_all:
        if not _P_OUTPUT_RE.search(staged_file):
            continue
        m = re.match(r"^(.*)/P[0-8]-[^/]+\.md$", staged_file)
        if not m:
            continue
        task_dir_rel = m.group(1)
        if not task_dir_rel:
            continue
        if _is_processed_dir(processed_dirs, os.path.join(repo_root, task_dir_rel)):
            continue
        task_state = os.path.join(repo_root, task_dir_rel, _STATE_YAML_SUFFIX)
        if not os.path.isfile(task_state):
            continue
        task_phase = read_state_phase(task_state)
        if not task_phase:
            continue
        out_phase = _phase_num(staged_file)
        if not out_phase:
            continue
        if out_phase != task_phase:
            out_num = out_phase[1:]
            phase_num = task_phase[1:]
            if out_num.isdigit() and phase_num.isdigit() \
                    and int(out_num) < int(phase_num) and staged_file in staged_added_all:
                continue
            sys.stderr.write(
                f"GATE WARNING: 暂存了 {out_phase} 产出但 phase={task_phase}（{os.path.basename(task_dir_rel)}）——请确认是否需要更新 phase\n")

    # 3.1 宽松探测差集扫描（TAG0035 BDD-6，与 2f.1 同一机制，覆盖全局 staged_all
    # 候选列表）：命中 _P_OUTPUT_ANY_RE 但未命中窄口径 _P_OUTPUT_RE 的文件，
    # 不参与上面的一致性判定，只做提示，不影响 exit code。
    staged_any_all = [
        f for f in staged_all
        if _P_OUTPUT_ANY_RE.search(f) and not _P_OUTPUT_RE.search(f)
    ]
    for any_staged_file in staged_any_all:
        sys.stderr.write(
            f"GATE WARNING: 无法识别该产出文件的阶段号，一致性检查未覆盖: {any_staged_file}\n"
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
