#!/usr/bin/env python3
"""agate-next.py — 阶段推进 CLI（TAG0027 §3.4 D4-A 定案，BDD-6/7/8/9/11；exit2fix pass_set 重写）

用法：
  agate-next.py [TASK_DIR]        # TASK_DIR 缺省 = 当前目录

语义（消费 check-gate.py exit 三态 + phases.yaml gate_pass_exit，不改 gate 返回约定；BDD-13）：
  * .state.yaml phase ∈ {PAUSED, READY, DONE} → 提示不推进，exit 0
  * 读 phases.yaml 当前 phase 的 gate_pass_exit（pass_set）+ next/retreat
  * 子进程跑 check-gate.py {phase} {TASK_DIR}，按 pass_set 三态判定：
    - exit ∈ gate_pass_exit（通过，直推候选）：普通 phase 查 next（Pn+1 建议 / null 转
      READY 提示）——**不预写**下一阶段：不写 .state.yaml 的 phase、不 git add，
      仅 append_event state_transition 作为「推进已发生」证据（TAG0042 批 1：phase 只表示
      「本 commit 的产出阶段」，由后续在该阶段的产出 commit 写入）；
      P6（exit 2 ∈ pass_set）走 A1 条件式裁决（§3.1）：provenance exit 0 +
      judge 未启用（gate_p65 早退 0）或启用但 check-gate P6.5 exit 0 → 消费 next: P7；
      gate_p65 exit 1 → 停留 P6 有指引不推进——exit 2 正常通过码不落盘 resolution
      （CRITICAL-1）
    - exit 1（未通过）→ 查 phases.yaml `retreat`：
        retreat: Pt  → 调用 agate-retreat-to.py {TASK_DIR} {Pt} "gate exit 1 按转移表回退"
                       （retreat-to 内部逐阶归档 + retry 记录 + 独立 commit；
                        CLI 不预判 diff——P6→P4 diff=2 亦委托，表值存在即委托）
        retreat: null/缺失 → 提示重试本阶段（retry+1 由主 Agent 走既有流程），不推进
    - exit ∉ gate_pass_exit 且 ≠ 1（真暂停/异常，协议实际极少）→ 通用暂停语义：
        不推进，落盘 {phase}-exit2-resolution.md（§3.3 模板；已存在则提示更新），
        输出暂停转主 Agent 提示，exit 0

可观测证据（BDD-11）：每次推进 append_event state_transition（from/to/ts），
账本 + git log 双面可查；真暂停分支不产生 retry 记录（硬中断不自动 retry）。

平台无关：显式 utf-8；无系统临时目录字面量；解释器一律 sys.executable 子进程。
Python 3.8+（禁 match / str.removeprefix）。
"""

import os
import subprocess
import sys
from datetime import datetime, timezone

try:
    import yaml
except ImportError:
    yaml = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# 公共库（同目录；agate_common 缺失时降级为本地最小实现）
try:
    sys.path.insert(0, SCRIPT_DIR)
    from agate_common import (
        read_rules_yaml,
        read_state_phase,
        requirement_active,
        resolve_rules_root,
    )
except Exception:  # pragma: no cover - 独立副本降级
    read_state_phase = None
    read_rules_yaml = None
    requirement_active = None
    resolve_rules_root = None

# check-gate 入口：**受控覆盖**（RM-AG0111 / DEBT0050）——测试可用合成 gate 制造
# 「exit ∉ pass_set 且 ≠ 1」以恢复 `agate-next` 真暂停分支的**端到端**覆盖
# （原先该分支经真实 gate 不可达 ⇒ BDD-8 只能直调落盘函数）。
# ⚠️ 仅作测试/诊断入口，**不改变**默认行为（未设 env 时与既有逐字一致）。
CHECK_GATE = os.environ.get("AGATE_CHECK_GATE") or os.path.join(SCRIPT_DIR, "check-gate.py")
RETREAT_TO = os.path.join(SCRIPT_DIR, "agate-retreat-to.py")
CHECK_PROVENANCE = os.path.join(SCRIPT_DIR, "check-p6-provenance.py")

# 非推进终态（不消费 next/retreat）
_TERMINAL_PHASES = {"PAUSED", "READY", "DONE"}

# P6.5 gate 子进程入口（同 check-gate.py main 分发语义）
# 通过 check-gate.py P6.5 统一消费（内部调 check-judge-verdict + check-events）


def _log(msg):
    sys.stderr.write("AGATE NEXT: " + msg + "\n")


def _resolve_rules():
    """解析 AGATE_ROOT/rules 目录（env → 版本链 → 脚本路径上溯，agate_common 归口）。"""
    if resolve_rules_root is not None:
        try:
            return resolve_rules_root(__file__)
        except Exception:
            pass
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return os.path.join(env_root, "rules")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rules")


def _load_phase_table(rules_root):
    """读 phases.yaml → {phase_id: phase_dict}；缺失/解析失败 → {}。"""
    if read_rules_yaml is None:
        return {}
    data = read_rules_yaml(rules_root, "phases")
    if not isinstance(data, dict):
        return {}
    out = {}
    for ph in data.get("phases", []) or []:
        if isinstance(ph, dict) and ph.get("id"):
            out[str(ph["id"])] = ph
    return out


def _read_state_dict(task_dir):
    """读 task_dir/.state.yaml 为 dict；缺失/解析失败 → None。"""
    state_file = os.path.join(task_dir, ".state.yaml")
    if not os.path.isfile(state_file) or yaml is None:
        return None
    try:
        with open(state_file, encoding="utf-8", errors="replace") as fh:
            data = yaml.safe_load(fh)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _run_cmd(cmd, task_dir=None):
    """子进程运行（解释器一致 sys.executable；返回 returncode + 合并流）。"""
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=task_dir,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except OSError as exc:
        return 127, f"subprocess 启动失败: {exc}"


def _repo_root(task_dir):
    """定位 task_dir 所在 git 仓库根（`git -C task_dir rev-parse --show-toplevel`）。

    无 git / task_dir 不在仓库内 → None（git 操作降级为 no-op，非阻断）。
    """
    try:
        proc = subprocess.run(
            ["git", "-C", task_dir, "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    out = (proc.stdout or "").strip()
    return out or None


def _advance(task_dir, state, target, repo_root):
    """输出「下一阶段建议」；**不预写**下一阶段、**不写事件**（TAG0050 A3）。

    phase 语义统一为「本 commit 的产出阶段」：推进时**不**把 target 写入 .state.yaml 的
    phase，也**不** git add——phase 由后续在该阶段的产出 commit 时用 `agate-state-set` 写入。
    TAG0050 A3 起：`agate-next` **不再追加** `state_transition`（消除与 pre-commit 的重复
    记录，TAG0042 实施评审 I-6）——`state_transition` 由 pre-commit 统一写入；本函数只打印
    `agate-state-set` 建议命令。

    `repo_root` 参数保留以兼容既有调用点（本函数不做 git 操作）。
    """
    old = state.get("phase", "")
    state_set = os.path.join(SCRIPT_DIR, "agate-state-set.py")
    _log(f"{old} → 建议下一阶段 {target}：.state.yaml phase **未预写**（保持 {old}）。"
         f"下一步：python3 {state_set} {task_dir} phase {target}")


def _write_exit2_resolution(task_dir, phase, state, gate_rc):
    """落盘 {phase}-exit2-resolution.md（§3.3 D3-A 模板，frontmatter + 正文三节）。

    已存在 → 提示更新（不覆盖用户留痕）。
    gate_rc：触发落盘的真实 check-gate exit code（真暂停分支 exit ∉ pass_set 且 ≠ 1，
    正文"触发命令"须记实际 exit 值而非写死 2——REV-3）。
    """
    task_id = state.get("task_id", "")
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = os.path.join(task_dir, f"{phase}-exit2-resolution.md")
    if os.path.isfile(path):
        _log(f"{phase} gate exit {gate_rc}：{os.path.basename(path)} 已存在——请人工更新解决留痕后继续")
        return
    body = (
        "---\n"
        f"phase: {phase}\n"
        f"task_id: {task_id}\n"
        "type: exit2-resolution\n"
        "parent: .state.yaml\n"
        f"created: {now_ts}\n"
        "agent: main-agent\n"
        "---\n"
        f"# {phase} exit2-resolution\n"
        "\n"
        "## 触发\n"
        f"- 时间: {now_ts}\n"
        f"- 触发命令: check-gate.py {phase}（exit {gate_rc}）\n"
        "- gate 输出摘要: <非空证据 / FAIL 计数等客观证据>\n"
        "\n"
        "## 客观证据\n"
        "- <exit 依据：如 check-gate 输出、provenance exit code、证据文件清单>\n"
        "\n"
        "## 解决\n"
        "- 解决人: <主 Agent / 角色名>\n"
        "- 结论: <继续 / 回退 / 修正后重验>\n"
        "- 依据: <客观证据交叉引用>\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(body)
    _log(f"{phase} 真暂停（gate exit {gate_rc} ∉ pass_set 且 ≠ 1）：已落盘 {os.path.basename(path)}"
         "（机器可读，frontmatter + 触发/客观证据/解决三节）")


# check-p6-provenance.py 的退出码契约（见 agate/scripts/README.md）：
#   0 = 通过 / 1 = 审计失败 / 2 = WARNING（协作规范类，**不阻塞**）
_P6_PROVENANCE_PASS = (0, 2)


def _p6_pass(state, task_dir):
    """P6 前进特例判定：check-p6-provenance 是否**通过**。

    **判据含 exit 2**（DEBT0045）：该脚本对「缺 agent 字段（协作规范，**不阻塞**）」
    经 stderr 告警后 `exit 2`，而本函数原先只认 `rc == 0` ⇒ **一条自称不阻塞的警告把
    P6→P7 卡住**，且表现为"验收异常"（不指出真因），并落盘占位
    `P6-exit2-resolution.md`（易被 `git add <任务目录>` 一并提交——TAG0036 实测）。
    现按脚本 README 的既定契约消费：**2 = WARNING = 通过**；只有 1（审计失败）才拦。
    exit 1 的拦截语义由下方 `else` 分支保持（不推进 + 提示），未被放宽。
    """
    rc, out = _run_cmd([sys.executable, CHECK_PROVENANCE, task_dir])
    _p6_relay_provenance(rc, out)
    return rc in _P6_PROVENANCE_PASS


def _p6_relay_provenance(rc, out):
    """把 provenance 的具体原因行转达给主 Agent（**exit 1 与 exit 2 都转达**）。

    DEBT0045 的 closure_criteria 第 2 条要求「暂停信息含 provenance 的具体原因行」——
    原先**两条分支都不转达**：exit 2 只打"验收异常"、exit 1 同样只打"验收异常"，
    主 Agent 必须手动再跑一次 provenance 才知道原因（债的 impact 原文即此）。

    **不做截断**（初版只转达第一条且不告知总数 ⇒ 多警告时信息丢失）：列出全部非空行，
    行数多时给总数提示。
    """
    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    if not lines:
        return
    tag = {1: "provenance 审计失败", 2: "provenance WARNING"}.get(rc, f"provenance exit {rc}")
    if len(lines) == 1:
        _log(f"  [{tag}] {lines[0]}")
    else:
        _log(f"  [{tag}] 共 {len(lines)} 条：")
        for ln in lines:
            _log("    " + ln)


def _p6_judge_advance(task_dir, state, phases, repo_root):
    """P6 exit 2 ∈ pass_set 条件式推进分支（A1 裁决 §3.1/§3.4）：judge 启用与否的推进裁决。

    返回 True = 已推进（或已提示停留）；调用方无需再走通用暂停。
    """
    p6_entry = phases.get("P6", {})
    next_phase = p6_entry.get("next")
    # TAG0050 批 A1（设计 §2.5）：非 legacy 任务的 judge 由**契约**决定
    # （requirement_active(task_dir, "judge", "P6")），不读可被改写的 judge.enabled；
    # legacy 任务（返回 None）回退旧逻辑。与 check-gate / pre-commit 的既有改法一致。
    judge_enabled = None
    if requirement_active is not None:
        req = requirement_active(task_dir, "judge", "P6")
        if req is not None:
            judge_enabled = bool(req)
    if judge_enabled is None:
        judge = state.get("judge")
        judge_enabled = bool(isinstance(judge, dict) and judge.get("enabled"))
    if not judge_enabled:
        # 历史任务 / judge 未启用 → gate_p65 早退 0 → 裁决成立，直推 P7
        if next_phase:
            _log("P6 验收通过（provenance exit 0）；judge 未启用（历史任务）→ 直推 " + str(next_phase))
            _advance(task_dir, state, str(next_phase), repo_root)
        else:
            _log("P6 验收通过但 phases.yaml P6.next 缺失——请人工处理")
        return True
    # judge 启用 → 子进程跑 check-gate.py P6.5（= verdict 存在 + 双脚本 exit 0）
    rc, out = _run_cmd([sys.executable, CHECK_GATE, "P6.5", task_dir])
    if rc == 0:
        _log("P6.5 judge 复核通过（check-gate P6.5 exit 0）→ 消费 next:" + str(next_phase))
        if next_phase:
            _advance(task_dir, state, str(next_phase), repo_root)
        else:
            _log("P6 推进裁决成立但 phases.yaml P6.next 缺失——请人工处理")
    else:
        _log("judge 复核未过：缺 verdict 或 verdict 校验失败/账本审计未过"
             "（judge.rounds ≤2，超限人工接管）→ 停留 P6，不推进、不落盘 exit2-resolution")
        if out:
            for line in out.splitlines()[:6]:
                _log("  " + line.strip())
    return True


def _delegate_retreat(task_dir, target_phase, repo_root):
    """委托 agate-retreat-to.py 逐阶回退（CLI 不预判 diff——表值存在即委托）。

    retreat-to 内部 git 操作从 cwd 运行 → 必须在其所在仓库根跑（-C 语义由
    _repo_root 定位；无仓库时仍按绝对路径调脚本，git 步失败由 retreat-to 自行处理）。
    """
    reason = "gate exit 1 按转移表回退"
    try:
        proc = subprocess.run(
            [sys.executable, RETREAT_TO, task_dir, target_phase, reason],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=repo_root or None,
        )
        rc = proc.returncode
        out = (proc.stdout or "") + (proc.stderr or "")
    except OSError as exc:
        rc = 127
        out = f"subprocess 启动失败: {exc}"
    _log(f"已委托 agate-retreat-to.py → {target_phase}（逐阶归档 + retry 记录 + 独立 commit）")
    if out:
        for line in out.splitlines()[:10]:
            _log("  " + line.strip())
    return rc


def main():
    args = sys.argv[1:]
    task_dir = args[0] if args else os.getcwd()

    state = _read_state_dict(task_dir)
    if state is None:
        sys.stderr.write(f"AGATE NEXT: {os.path.join(task_dir, '.state.yaml')} 缺失或解析失败\n")
        sys.exit(1)
    phase = str(state.get("phase", ""))
    if not phase:
        sys.stderr.write("AGATE NEXT: .state.yaml 缺 phase 字段\n")
        sys.exit(1)
    if phase in _TERMINAL_PHASES:
        _log(f"当前 phase={phase}（终态，不推进）")
        sys.exit(0)

    rules_root = _resolve_rules()
    phases = _load_phase_table(rules_root)
    repo_root = _repo_root(task_dir)

    entry = phases.get(phase, {})
    pass_exit = entry.get("gate_pass_exit")

    # 数据面守卫：phases.yaml 未声明当前 phase 的通过出口码 → 不自动推进（fail-safe，
    # 不把模糊数据当"通过"直推；BDD-26 数据面断言保证真实树必含此键）。
    # 注意：此分支 exit 0 且不落盘 exit2-resolution，与"真暂停"（exit ∉ pass_set 且 ≠ 1，
    # 落盘 resolution）不同——属数据面异常，非真暂停，需主 Agent 修 phases.yaml 后重跑。
    if pass_exit not in (0, 2):
        _log(f"{phase} phases.yaml 缺 gate_pass_exit（数据面异常，非真暂停——exit 0 且不落盘 "
             "resolution）→ 暂停转主 Agent 修正 phases.yaml 后重跑，不推进")
        sys.exit(0)
    pass_set = {int(pass_exit)}

    # 子进程跑 check-gate.py {phase} {TASK_DIR}（消费 exit 三态，不改返回约定）
    rc, out = _run_cmd([sys.executable, CHECK_GATE, phase, task_dir])
    if out:
        for line in out.splitlines()[:10]:
            _log("  gate: " + line.strip())

    if rc in pass_set:
        # exit ∈ gate_pass_exit（通过，直推候选）——exit 2 正常通过码也在此分支（CRITICAL-1）
        if phase == "P6":
            # P6 条件式推进特例（A1，§3.1/§3.4）：gate exit 2 ∈ pass_set + provenance exit 0
            # 才进入裁决；provenance exit 1（验收异常）→ 真暂停落盘 resolution
            if not _p6_pass(state, task_dir):
                # 原因行已在 _p6_pass → _p6_relay_provenance 里转达（DEBT0045 closure #2）
                _write_exit2_resolution(task_dir, phase, state, rc)
                _log(f"{phase} gate exit 2 ∈ pass_set 但 check-p6-provenance **审计失败**（非警告）→ "
                     "暂停转主 Agent 决策（不推进；硬中断不自动 retry）；"
                     "**具体原因见上方 provenance 行**")
            else:
                _p6_judge_advance(task_dir, state, phases, repo_root)
            sys.exit(0)
        next_phase = entry.get("next")
        if next_phase is None or next_phase == "":
            _log(f"{phase} gate exit {rc} ∈ pass_set 但无自动后继（next: null）→ "
                 "转 READY/发布流程由人处理，不推进")
            sys.exit(0)
        _advance(task_dir, state, str(next_phase), repo_root)
        sys.exit(0)

    if rc == 1:
        # exit 1（未通过）→ 按 retreat 表值委托
        retreat = entry.get("retreat")
        if retreat is None or retreat == "":
            _log(f"{phase} gate exit 1 且无 retreat 表值 → 提示重试本阶段（retry+1 由主 Agent 走既有流程），不推进")
            sys.exit(0)
        _delegate_retreat(task_dir, str(retreat), repo_root)
        sys.exit(0)

    # exit ∉ gate_pass_exit 且 ≠ 1（真暂停/异常，协议实际极少）→ 落盘 resolution 转主 Agent
    _write_exit2_resolution(task_dir, phase, state, rc)
    _log(f"{phase} gate exit {rc} ∉ pass_set（{sorted(pass_set)}）且 ≠ 1 → 暂停转主 Agent 决策"
         "（不推进；硬中断不自动 retry）")
    sys.exit(0)


if __name__ == "__main__":
    main()
