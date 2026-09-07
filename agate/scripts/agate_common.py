#!/usr/bin/env python3
"""agate_common.py — agate 脚本公共函数库（P4 批次 0）

替代 gate-result.sh + agate-workspace-resolve.sh 的函数库，并承载 3 个 hook 薄壳
共用的定位/探测工具（P2-design.md §3.1）。

- 数据流函数（迁移自 gate-result.sh）：write_gate_result / read_state_phase /
  read_state_task_id / has_staged_phase_change / has_staged_phase_output /
  resolve_formatter / run_test_with_formatter
- 工作区解析函数（迁移自 agate-workspace-resolve.sh）：resolve_workspace
  （执行模式 main 输出 AGATE_WORKSPACE=/AGATE_TASKS_DIR= 两行，bats 直调契约）
- hook 公共工具：resolve_agate_root / probe_python / run_git
- 版本解析（TAG0008）：resolve_version_root（四层，agate-resolve/summary 用）/
  resolve_hook_root（hook 入口用，返回 warnings）/ _find_project_declaration（.agate-version 向上查找）

约定：所有文本读写显式 encoding="utf-8"；pyyaml 缺失时 fail-closed（同
agate-state-get.py）。Python 3.8+（禁 match / str.removeprefix）。
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.stderr.write("agate_common: 需要 pyyaml。pip install pyyaml\n")
    sys.exit(1)

_AGATE_ROOT = Path(__file__).resolve().parent.parent


# ---------- MAX_RETRY_MAP（单一数据源） ----------
# 按阶段差异化 MAX_RETRY（P3/P5/P6/P7/P8=2，其他=3）。
# 供 check-state-transition.py / agate-retreat-to.py 共享（原 check-state-transition.sh
# 的字面值 + check-retrospective.py 的模块级常量，TAG0010 批次 2b 统一于此）；
# 两脚本仍支持环境变量覆盖（MAX_RETRY_MAP=... 优先，同 sh 版 ${MAX_RETRY_MAP:-...} 语义）。
MAX_RETRY_MAP = "P1:3,P2:3,P3:2,P4:3,P5:2,P6:2,P7:2,P8:2"


# ---------- run_git / 通用工具 ----------


def run_git(args, cwd=None):
    """git subprocess 封装。

    encoding="utf-8" + errors="replace"（Windows 代码页差异不崩溃），返回
    (returncode, stdout)。git 不可用时按失败处理（同 sh 侧 2>/dev/null 语义）。
    """
    try:
        proc = subprocess.run(
            ["git", *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=cwd,
        )
        return proc.returncode, proc.stdout
    except OSError:
        return 1, ""


def probe_python():
    """探测可用 python 解释器：python3 → python（shutil.which 顺序，替代 detect_python）。

    返回解析到的可执行路径；均不可用时返回 None（调用方须 fail-closed 阻断）。
    """
    for name in ("python3", "python"):
        path = shutil.which(name)
        if path:
            return path
    return None


def is_gate_meta_key(key):
    """gate_commands key 是否为元信息 key（非待执行命令）（DEBT0010/TAG0017）。

    仅精确匹配两个已知固定后缀 `_formatter` / `_timeout_seconds`，不做通配/正则
    宽松匹配（P1 R3 风险条目：防止把真正需要核实/计入的 key 一并放宽排除）。
    供 agate-read-gate-commands.py / agate-gate-missing-cmds.py /
    agate-gate-p5-count.py / agate-read-p5-commands.py 共用（P2-design.md §1.1）。
    """
    return key.endswith(("_formatter", "_timeout_seconds"))


# ---------- 版本解析（TAG0008，resolve-chain 批次） ----------
# 四层解析语义（P2-design.md §4.1）：
#   env 最高 → 项目声明（.agate-version，asdf 模式 cwd 向上）→ current/latest 指针链
#   → legacy 软链兜底（或脚本路径上溯，视调用方）。current/latest 为文本指针
#   （内容 = 目标名），Windows 复制模式指针形态；版本目录存在即视为已安装。

_AGATE_VERSION_RE = re.compile(r"^\s*agate\s*:\s*(v[0-9]+\.[0-9]+\.[0-9]+)\s*$")


def _find_project_declaration(start_dir=None):
    """cwd 向上找 .agate-version（asdf 模式，BDD-10）。

    返回 (status, version)：status ∈ {"none"（无文件）、"invalid"（文件格式非法）、
    "ok"（合法声明）}；version 仅 ok 时非空。非法格式（含空文件/未知前缀）→ invalid
    （BDD-14）。
    """
    d = os.path.abspath(start_dir) if start_dir else os.path.abspath(os.getcwd())
    while True:
        vf = os.path.join(d, ".agate-version")
        if os.path.isfile(vf):
            try:
                with open(vf, encoding="utf-8") as f:
                    content = f.read()
            except OSError:
                content = ""
            m = _AGATE_VERSION_RE.match(content)
            if m:
                return "ok", m.group(1)
            return "invalid", None
        parent = os.path.dirname(d)
        if parent == d:
            return "none", None
        d = parent


def _resolve_pointer_chain(base, name, seen=None):
    """current/latest 指针链解析：目录即根；软链 readlink 目标名继续追；文本指针内容=目标名继续追；防环。

    兼容目录即版本根（无指针时的直接版本目录）、POSIX 软链指针（`os.symlink`）与
    文本指针（Windows-safe）三种形态。先判 `os.path.islink` 再判 `os.path.isdir`——
    软链指向版本目录时 `isdir` 恒为 True，若先判 isdir 会把软链路径自身当终态
    （返回 "current"/"latest" 而非实际版本目录名），导致版本号解析/指针修复失效。
    """
    if seen is None:
        seen = set()
    if not name or name in seen:
        return None
    seen.add(name)
    p = os.path.join(base, name)
    if os.path.islink(p):
        try:
            target = os.readlink(p)
        except OSError:
            return None
        if not target or target in seen:
            return None
        if os.path.isabs(target):
            t = os.path.normpath(target)
            if os.path.isdir(t):
                return t
            return _resolve_pointer_chain(base, t, seen)
        return _resolve_pointer_chain(base, target, seen)
    if os.path.isdir(p):
        return p
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8") as f:
            content = f.read().replace("\r", "").strip()
    except OSError:
        return None
    if not content or content == name:
        return None
    return _resolve_pointer_chain(base, content, seen)


def _protocol_root(vdir):
    """版本目录命中后定位协议根：根即协议（探测序 1）→ 元仓库形态（探测序 2）→ 原样。

    探测顺序不可颠倒（纯增量红线，TAG0032 决策 A1）：
    - `vdir/scripts` 存在 → 返回 `vdir` 本身（「根即协议」部署方零回归，BDD-7）。
    - 否则 `vdir/agate/scripts` 存在 → 返回 `vdir/agate`（元仓库整仓形态，BDD-6/8）。
    - 两形态皆无 → 返回 `vdir` 原样，下游维持既有 fail-closed。
    """
    if os.path.isdir(os.path.join(vdir, "scripts")):
        return vdir
    sub = os.path.join(vdir, "agate")
    if os.path.isdir(os.path.join(sub, "scripts")):
        return sub
    return vdir


def _resolve_version_info(start_dir=None, use_legacy=True):
    """版本解析核心：env → 项目声明 → current 链 → legacy 软链兜底。

    返回 dict {root, version, reason, warnings}。root 为 None = 终态失败（调用方须
    fail-closed）。env 覆盖返回 env 原值（不 resolve，与既有契约一致，兼容字面盘符路径）。
    声明未安装 / 格式非法 → warnings 加警告 + 回退 current（绝不静默禁用，BDD-13/14）。
    """
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return {"root": env_root, "version": "", "reason": "AGATE_ROOT 环境变量覆盖", "warnings": []}

    base = os.path.expanduser("~/.agate")
    warnings = []
    status, declared = _find_project_declaration(start_dir)
    if status == "ok":
        vdir = os.path.join(base, declared)
        if os.path.isdir(vdir):
            return {"root": _protocol_root(vdir), "version": declared, "reason": "引用 .agate-version", "warnings": warnings}
        warnings.append(f"警告: .agate-version 声明的版本 {declared} 未安装，回退全局 current")
    elif status == "invalid":
        warnings.append("警告: .agate-version 格式非法（应为 agate: vX.Y.Z），回退全局 current")

    cur = _resolve_pointer_chain(base, "current")
    if cur:
        # 顺序不可倒（I-1 红线）：version 从 cur 取，root 从 _protocol_root(cur) 取——两条独立。
        version = os.path.basename(cur)
        root = _protocol_root(cur)
        return {"root": root, "version": version, "reason": "全局 current", "warnings": warnings}

    if use_legacy and os.path.islink(base):
        return {"root": os.path.realpath(base), "version": "", "reason": "legacy 软链布局（无版本指针）", "warnings": warnings}

    return {"root": None, "version": None, "reason": "无可用 AGATE_ROOT", "warnings": warnings}


def resolve_version_root(start_dir=None):
    """版本解析四层（env → 项目声明 → current 链 → legacy 软链兜底）。

    供 agate-resolve.py / agate-summary.py 复用（P2 §4.1/§4.6）。root 为 None =
    终态失败（调用方 fail-closed，exit 非 0）。
    """
    return _resolve_version_info(start_dir=start_dir, use_legacy=True)


def resolve_hook_root(script_path):
    """hook 解析入口（resolve-entry.py）用：env → 项目声明 → current 链 → 脚本路径上溯兜底。

    返回 (root, warnings)。root 恒非空（脚本路径上溯 + 复制模式 .agate-root 标记恢复兜底，
    兼容既有 hook 自定位契约），调用方再校验 gate 脚本存在（fail-closed）。
    """
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return env_root, []
    info = _resolve_version_info(use_legacy=False)
    if info["root"]:
        return info["root"], info["warnings"]
    real = str(Path(script_path).resolve())
    agate_root = os.path.dirname(os.path.dirname(real))
    if not os.path.isdir(os.path.join(agate_root, "scripts")):
        marker = os.path.join(os.path.dirname(real), ".agate-root")
        if os.path.isfile(marker):
            with open(marker, encoding="utf-8") as f:
                content = f.read().replace("\r", "").strip()
            if content:
                return content, info["warnings"]
    return agate_root, info["warnings"]


def resolve_agate_root(script_path):
    """解析 AGATE_ROOT：env 优先 → 项目版本解析（.agate-version / current 链）→
    软链 readlink 上溯 → 复制模式 .agate-root 标记恢复。

    AGATE_ROOT 环境变量优先（返回原值）。项目声明命中已安装版本或全局 current 指针链
    命中时返回版本根；否则回退既有脚本路径上溯语义（做加法不改既有契约）。
    """
    root, _warnings = resolve_hook_root(script_path)
    return root


# ---------- 数据流函数（gate-result.sh 迁移） ----------


def write_gate_result(phase, task_id, exit_code, output):
    """写 .gate-result.json（结构不变）+ 追加 .gate-history.jsonl。

    output 用 json.dumps 转义（替代 agate-json-get.py escape）；prev_commit_sha 用
    git rev-parse HEAD（失败回退 "pre-commit"——pre-commit hook 在 commit 创建前
    运行，HEAD 是上一个 commit）。
    """
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rc, head = run_git(["rev-parse", "HEAD"])
    prev_commit_sha = head.strip() if rc == 0 and head.strip() else "pre-commit"

    result = {
        "phase": phase,
        "task_id": task_id,
        "exit_code": int(exit_code),
        "timestamp": ts,
        "output": output,
        "runner": "pre-commit-hook",
        "prev_commit_sha": prev_commit_sha,
    }
    with open(".gate-result.json", "w", encoding="utf-8") as f:
        f.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")

    history = {
        "phase": phase,
        "task_id": task_id,
        "exit_code": int(exit_code),
        "timestamp": ts,
        "prev_commit_sha": prev_commit_sha,
    }
    with open(".gate-history.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(history, separators=(",", ":"), ensure_ascii=True) + "\n")


def _read_state(state_file):
    """读 .state.yaml 为 dict；文件不存在/解析失败返回 None（调用方按空处理）。"""
    if not os.path.isfile(state_file):
        return None
    try:
        with open(state_file, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception:
        return None


def read_state_phase(state_file):
    """读 .state.yaml 的 phase；文件不存在/解析失败返回 ""。"""
    data = _read_state(state_file)
    return data.get("phase", "") if data else ""


def read_state_task_id(state_file):
    """读 .state.yaml 的 task_id；文件不存在/解析失败返回 ""。"""
    data = _read_state(state_file)
    return data.get("task_id", "") if data else ""


# ---------- 事件账本（TAG0020：P6.5 独立 Judge 机制） ----------
# append-only 哈希链账本 gate-events.jsonl（P2-design §3.2）：每行 JSON 事件，
# prev_hash = sha256(上一行原始文本 UTF-8).hexdigest()，首行 = GENESIS_HASH。
# append_event 是唯一写路径（hook/gate 统一走它）；check-events.py 审计链完整性。
GENESIS_HASH = hashlib.sha256(b"").hexdigest()


def append_event(task_dir, event):
    """向 {task_dir}/gate-events.jsonl 追加一条事件（append-only 哈希链账本）。

    - 自动补 ts（UTC ISO8601 微秒）与 prev_hash：首行 = GENESIS_HASH，
      后续行 = sha256(上一行原始文本 UTF-8).hexdigest()（行间哈希链，防改写）
    - ts 单调兜底：尾行 ts 晚于当前时刻时沿用尾行 ts（同格式字符串比较，
      保证单调不减；check-events 判定用 <= 放宽微秒精度，P2 R7）
    - 文件不存在/为空 → 直接写首事件（prev_hash = GENESIS_HASH）
    - 失败（IOError 等）→ stderr WARNING 不抛：gate 主判定不依赖写账本成功，
      账本审计是辅助防线（P2-design §3.2；judge_verdict 事件写入失败也仅告警）
    """
    try:
        path = os.path.join(task_dir, "gate-events.jsonl")
        prev_hash = GENESIS_HASH
        tail_ts = None
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    raw_lines = f.read().splitlines()
            except OSError:
                raw_lines = []
            if raw_lines:
                # 链始终接续到文件尾行原始文本（即使尾行 JSON 损坏，防改写链不破）
                prev_hash = hashlib.sha256(raw_lines[-1].encode("utf-8")).hexdigest()
                try:
                    tail_ts = json.loads(raw_lines[-1]).get("ts")
                except Exception:
                    tail_ts = None
        now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        ts = now_ts
        if tail_ts and tail_ts > now_ts:
            ts = tail_ts
        row = dict(event)
        row.pop("prev_hash", None)
        row["ts"] = ts
        row["prev_hash"] = prev_hash
        line = json.dumps(row, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as exc:
        sys.stderr.write(
            f"agate_common: append_event WARNING: 账本事件写入失败（不阻断主判定）: {exc}\n"
        )


def read_judge_verdict(task_dir):
    """解析 {task_dir}/P6.5-judge-verdict.md 的 frontmatter（--- 块）。

    返回 dict {status, criteria_total, criteria_passed, verdict_evidence, partial}；
    文件缺失 / 无 frontmatter / 解析失败 → None（调用方按缺失处理，fail-closed）。
    partial 为可选降级标记字段：缺省 False（BDD-5 必需字段仅
    status/criteria_total/criteria_passed/verdict_evidence 四项）。
    """
    path = os.path.join(task_dir, "P6.5-judge-verdict.md")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    m = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not m:
        return None
    try:
        data = yaml.safe_load(m.group(1))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return {
        "status": data.get("status"),
        "criteria_total": data.get("criteria_total"),
        "criteria_passed": data.get("criteria_passed"),
        "verdict_evidence": data.get("verdict_evidence"),
        "partial": bool(data.get("partial", False)),
    }


def read_vision_tri_state(p1_file):
    """读取 P1-requirements.md 声明的能力三态（available/supplementable/GAP）中的视觉条目状态。

    TAG0006（DEBT0005）统一解析：capability_requirements yaml 代码围栏块内
    need/name 含 visual|vision 的条目，其 status 即该任务的视觉能力声明。
    返回该 status 字符串；文件不存在 / 无视觉条目 / 解析失败 → 返回 None
    （调用方按"无声明默认 available 语义"处理——TAG0006 P2 §2.8 兼容回归锚点）。
    平台无关：纯文件文本解析，无路径/进程假设，gate/P6 多脚本复用同一口径。
    """
    if not os.path.isfile(p1_file):
        return None
    try:
        with open(p1_file, encoding="utf-8", errors="replace") as f:
            text = f.read()
    except OSError:
        return None
    for m in re.finditer(r"```(?:yaml|yml)\s*\n(.*?)```", text, re.DOTALL):
        try:
            data = yaml.safe_load(m.group(1))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        reqs = data.get("capability_requirements")
        if not isinstance(reqs, list):
            continue
        for item in reqs:
            if not isinstance(item, dict):
                continue
            need = item.get("need") or item.get("name")
            if need and re.search(r"visual|vision", str(need), re.IGNORECASE):
                return item.get("status")
    return None


def has_staged_phase_change(state_file):
    """暂存区中 state 文件含 phase 字段变更。

    git diff --cached --name-only + CRLF 剥离（line.rstrip("\\r")）判断文件已暂存，
    再对该文件 diff 检查 ^\\+.*phase:（替代 tr -d '\\r' + grep，TAG0009）。
    """
    basename = os.path.basename(state_file)
    rc, name_only = run_git(["diff", "--cached", "--name-only"])
    if rc != 0:
        return False
    staged = [line.rstrip("\r") for line in name_only.splitlines()]
    if basename not in staged:
        return False
    rc, diff = run_git(["diff", "--cached", "--", basename])
    if rc != 0:
        return False
    return any(re.match(r"^\+.*phase:", line.rstrip("\r")) for line in diff.splitlines())


def has_staged_phase_output():
    """暂存区文件名匹配阶段产出（P{n}-*.md|yaml）。"""
    rc, name_only = run_git(["diff", "--cached", "--name-only"])
    if rc != 0:
        return False
    return any(re.search(r"P[0-9]+-.*\.(md|yaml)$", line.rstrip("\r")) for line in name_only.splitlines())


def resolve_formatter(fmt, task_dir=None, agate_root=None):
    """formatter 路径解析，优先级：绝对路径 → $task_dir/.agate/formatters/ → $agate_root/assets/formatters/。

    返回存在路径；找不到返回 None（调用方按空处理，同 sh 侧 exit 1 语义）。
    """
    if agate_root is None:
        agate_root = _AGATE_ROOT
    if fmt.startswith("/"):
        if os.path.isfile(fmt):
            return fmt
        return None
    if task_dir:
        p = os.path.join(task_dir, ".agate", "formatters", fmt)
        if os.path.isfile(p):
            return p
    p = os.path.join(str(agate_root), "assets", "formatters", fmt)
    if os.path.isfile(p):
        return p
    return None


def _timeout_json():
    return json.dumps({
        "exit_code": 124,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "failed_tests": [],
        "import_errors": [],
        "syntax_errors": [],
    })


def _fallback_json(exit_code, output):
    return json.dumps({
        "exit_code": exit_code,
        "total": 0,
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "failed_tests": [],
        "import_errors": [],
        "syntax_errors": [],
        "name_errors": [],
        "raw_output": output,
    })


def run_test_with_formatter(cmd, fmt_path, timeout_secs=None):
    """跑测试命令并输出 JSON 结果（TDD 语义，P2 §3.1）。

    用 subprocess timeout（替代 GNU timeout 二进制），保留 exit 124 超时语义；
    stdout/stderr 合并（2>&1）。fmt_path 为空或 formatter 失败时回退 raw_output JSON。
    """
    if timeout_secs is None:
        timeout_secs = int(os.environ.get("AGATE_TDD_TIMEOUT", "120"))
    output = ""
    exit_code = 0
    try:
        proc = subprocess.run(
            cmd, shell=True, executable="bash",
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            timeout=timeout_secs,
        )
        output = proc.stdout or ""
        exit_code = proc.returncode
    except subprocess.TimeoutExpired as exc:
        output = exc.stdout or ""
        exit_code = 124

    if exit_code == 124:
        sys.stderr.write(f"TDD_CHECK: 测试命令超时（{timeout_secs}s），请手动运行确认：{cmd}\n")
        return _timeout_json()

    if not fmt_path:
        return _fallback_json(exit_code, output)

    try:
        fmt_proc = subprocess.run(
            ["bash", fmt_path, str(exit_code)],
            input=output, capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return _fallback_json(exit_code, output)
    if fmt_proc.returncode != 0:
        return _fallback_json(exit_code, output)
    return fmt_proc.stdout or _fallback_json(exit_code, output)


# ---------- 工作区解析函数（agate-workspace-resolve.sh 迁移） ----------


def _resolve_abs(base, p):
    """相对路径相对 base 归一 / 绝对路径原样，Path.resolve() 替代 realpath -m。"""
    if os.path.isabs(p):
        return str(Path(p).resolve())
    return str(Path(base, p).resolve())


def resolve_workspace(project_root):
    """解析工作区 → (AGATE_WORKSPACE, AGATE_TASKS_DIR)。

    优先级：.agate.env(AGATE_WORKSPACE=) → env AGATE_TASKS_DIR → 默认
    {project_root}/agate-workspace。.agate.env 读取 utf-8 + CRLF 剥离（bdd-18 契约），
    取最后一条匹配行。解析器不创建任何目录。
    """
    project_root = str(Path(project_root).resolve())

    ws_value = ""
    env_file = os.path.join(project_root, ".agate.env")
    if os.path.isfile(env_file):
        with open(env_file, encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.replace("\r", "")
                if line.startswith("AGATE_WORKSPACE="):
                    ws_value = line[len("AGATE_WORKSPACE="):].rstrip("\n")

    if ws_value:
        workspace = _resolve_abs(project_root, ws_value)
        tasks_dir = os.path.join(workspace, "tasks")
    else:
        env_tasks = os.environ.get("AGATE_TASKS_DIR", "")
        if env_tasks:
            tasks_dir = _resolve_abs(project_root, env_tasks)
            workspace = os.path.dirname(tasks_dir)
        else:
            workspace = os.path.join(project_root, "agate-workspace")
            tasks_dir = os.path.join(workspace, "tasks")
    return workspace, tasks_dir


def compute_sha256(path):
    """sha256 hex：文件=内容哈希；目录=排序逐文件 hash 拼接再整体 hash（TAG0031 DEBT0002，
    从 agate-pack-offline.py / install-offline.py 迁移的共享单实现，逐字节保留现状排序键
    `f.relative_to(p).as_posix()` 字典序约定，跨平台路径排序一致）。"""
    p = Path(path)
    if p.is_dir():
        digests = []
        for f in sorted(p.rglob("*"), key=lambda f: f.relative_to(p).as_posix()):
            if f.is_file():
                digests.append(hashlib.sha256(f.read_bytes()).hexdigest())
        return hashlib.sha256("".join(digests).encode("utf-8")).hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ---------- M1 对账（TAG0021，BDD-6/7；P2-design §3.4） ----------
# 双跑对账：现行 grep/md 读取路径（保退出码语义 0/2 不变，不新增阻断）+ 结构化读取路径
# （frontmatter YAML / rules/*.yaml 声明）对比。差异可观测出口（BDD-6）：
#   stderr `RECONCILE WARNING: <op> <field>: grep=<grep_val> structured=<structured_val>` +
#   `RECONCILE SUMMARY: N mismatches across M fields`（可重定向进日志、可计数审计）。
# 开关：AGATE_RECONCILE 缺省 on（CI/批处理可设 off/0/false 降噪，P2-design §3.4）。
# 归一化口径（R10）：与 agate-md-field-get 的 BOOL/LIST 归一化一致（list 空格连接、
# bool 小写）；正文内联/块式 list 与 frontmatter list 语义等价 → 0 差异（P3 BDD-8）。
# 对账是叠加层：任何异常/失败均不阻断调用方原判定（fail-open），对账计数不改变退出码。

_RECONCILE_STATE = {"mismatches": 0, "fields": 0}

_RECONCILE_OFF_VALUES = frozenset({"", "0", "off", "false", "no", "disable"})


def reconcile_enabled():
    """对账开关：AGATE_RECONCILE 缺省 on；显式关闭值（off/0/false/no/空）才关闭。"""
    return os.environ.get("AGATE_RECONCILE", "1").strip().lower() not in _RECONCILE_OFF_VALUES


def _reconcile_norm(value):
    """对账归一化：str 化 + 剥首尾空白 + 折叠内部空白（list 空格连接后统一）。"""
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def reconcile_field(op, field, grep_val, structured_val):
    """字段级对账（BDD-6）：grep/md 读取值 vs 结构化读取值不一致 → stderr WARNING + 计数。

    返回 True=一致 / False=不一致。对账不改变调用方退出码语义（原判定 0/2 不变）；
    对账关闭时不做任何输出并恒返回 True。
    """
    if not reconcile_enabled():
        return True
    _RECONCILE_STATE["fields"] += 1
    if _reconcile_norm(grep_val) != _reconcile_norm(structured_val):
        _RECONCILE_STATE["mismatches"] += 1
        sys.stderr.write(
            f"RECONCILE WARNING: {op} {field}: grep={grep_val!s} structured={structured_val!s}\n"
        )
        return False
    return True


def reconcile_summary():
    """对账汇总行（BDD-6）：`RECONCILE SUMMARY: N mismatches across M fields`。"""
    if not reconcile_enabled():
        return
    sys.stderr.write(
        f"RECONCILE SUMMARY: {_RECONCILE_STATE['mismatches']} mismatches across {_RECONCILE_STATE['fields']} fields\n"
    )


def read_rules_yaml(rules_root, name):
    """读 {rules_root}/{name}.yaml（pyyaml）；缺失/解析失败 → None（调用方按数据缺失处理）。"""
    path = os.path.join(rules_root, name + ".yaml")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    except Exception:
        return None


def resolve_rules_root(script_path):
    """解析 AGATE_ROOT 协议根下 rules/ 目录（env → 版本链 → 脚本路径上溯兜底）。

    与 check-structure-consistency._resolve_root 同口径：env AGATE_ROOT 优先（返回原值），
    否则 agate_common 版本解析（resolve_agate_root），失败回退脚本路径上溯。
    """
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        root = env_root
    else:
        try:
            root = resolve_agate_root(script_path)
        except Exception:
            root = os.path.dirname(os.path.dirname(os.path.abspath(script_path)))
    return os.path.join(root, "rules")


_DEFAULT_PHASE_IDS = frozenset({"P0", "P1", "P2", "P3", "P4", "P5", "P6", "P6.5", "P7", "P8"})


def known_phase_ids(rules_root):
    """已知阶段 id 集：phases.yaml phases[].id ∪ 内置 {P0..P8, P6.5}（YAML 缺失回退内置）。"""
    phases = read_rules_yaml(rules_root, "phases")
    if isinstance(phases, dict) and isinstance(phases.get("phases"), list):
        ids = {str(p.get("id")) for p in phases["phases"] if isinstance(p, dict) and p.get("id")}
        if ids:
            return ids
    return _DEFAULT_PHASE_IDS


def is_legal_gate_key(key, phase_ids=None):
    """gate_commands key 合法性（P2-review 发现 #3 + 阶段集约束）。

    合法 = project_module 特判 / is_gate_meta_key（`_formatter`/`_timeout_seconds` 后缀）/
    裸或带自定义后缀的 `P{阶段}` 键（阶段 ∈ phases.yaml id ∪ 内置 P0-P8）。未声明 key
    （如 P9_custom——P9 非合法阶段）→ False → 对账 WARNING（BDD-6/7）。
    """
    if key == "project_module":
        return True
    if is_gate_meta_key(key):
        return True
    if phase_ids is None:
        phase_ids = _DEFAULT_PHASE_IDS
    m = re.match(r"^P([0-9]+(?:\.[0-9]+)?)(?:_[A-Za-z0-9_]*)?$", key)
    return bool(m) and ("P" + m.group(1)) in phase_ids


def split_frontmatter(text):
    """拆 frontmatter 块与正文：返回 (fm_dict_or_None, body_text)。

    只认文件头 `---` 块（与 agate-md-field-get._read_frontmatter 同规则）；
    无块 / 解析失败 → (None, 原文本)（正文含全部文本，供 grep 侧读取）。
    """
    if not text.startswith("---\n"):
        return None, text
    end = text.find("\n---", 4)
    if end < 0:
        return None, text
    fm_text = text[4:end]
    body = text[end + 4:]
    try:
        fm = yaml.safe_load(fm_text)
    except Exception:
        fm = None
    return fm, body


def _body_scalar_value(body, pattern):
    """正文标量字段 grep 值（pattern 须含一个捕获组）；无匹配 → ""。"""
    m = re.search(pattern, body)
    return m.group(1).strip() if m else ""


def _body_list_value(body, field):
    """正文 list 字段 grep 值（与 agate-md-field-get._regex_list 同归一化：空格连接）。

    兼容内联 `[a, b, c]` 与块式 `- item` 两种形态；无匹配 → ""。
    """
    m = re.search(re.escape(field) + r":\s*\[([^\]]+)\]", body)
    if m:
        items = [p.strip() for p in m.group(1).split(",") if p.strip()]
        return " ".join(items)
    m = re.search(re.escape(field) + r":\s*\n((?:[ \t]+-[ \t]+\S+[ \t]*\n)+)", body)
    if m:
        items = re.findall(r"-\s+(\S+)", m.group(1))
        return " ".join(items)
    return ""


def body_field_value(body, field):
    """正文 grep 字段值（与 agate-md-field-get._regex_fallback 同归一化口径）。

    list 字段（phases/packages/domains）空格连接、bool（ui_affected）小写、标量原值。
    """
    if field in ("phases", "packages", "domains"):
        return _body_list_value(body, field)
    if field == "ui_affected":
        return _body_scalar_value(body, r"ui_affected:\s*(true|false)")
    if field == "candidate_count":
        return _body_scalar_value(body, r"candidate_count:\s*(\d+)")
    if field == "risk_level":
        return _body_scalar_value(body, r"risk_level:\s*(low|medium|high)")
    return ""


def fm_field_value(fm, field):
    """frontmatter 结构化字段值（与 agate-md-field-get._format_value 同归一化口径）。

    list 空格连接 / bool（ui_affected）小写 / 其余 str 化；字段缺失或 null → ""。
    """
    if not isinstance(fm, dict) or field not in fm or fm[field] is None:
        return ""
    val = fm[field]
    if field in ("phases", "packages", "domains"):
        return " ".join(str(v) for v in val) if isinstance(val, list) else str(val)
    if field == "ui_affected":
        return str(val).lower()
    return str(val)


# ---------- M2 共享解析（TAG0021，BDD-9；P2-design §3.4/§3.5 M2-1） ----------
# 已迁移解析点（P1 §4.1 A 组四字段行正则 + B 组 gate_commands 块正则）从三消费脚本
# （agate-read-gate-commands / check-pruning / check-gate）抽到公共库单点：BDD-9 要求
# 这些已迁移模式在消费脚本源码中字面命中数 = 0，共享解析落在 agate_common（不在
# _MIGRATED_SCRIPTS 扫描清单内）。行为与原内联实现逐字节等价：
#   * gate_commands 块只认列 0 的 `gate_commands:` 标题行 + 二空格缩进的 `key: value` 行
#     （空行吞入块边界，与既有 5 处同源实现的块正则一致）
#   * 四字段计数 = 全文（frontmatter + 正文）列 0 声明行数（`^(packages|domains|
#     ui_affected|gate_commands):`），与 check-gate.py P2 分支既有计数语义一致

_GATE_COMMANDS_BLOCK_RE = re.compile(r"^gate_commands:[ \t]*\n((?:  .*\n|\s*\n)*)", re.MULTILINE)
_GATE_KEY_LINE_RE = re.compile(r"^  (\w+):\s*(.+)$", re.MULTILINE)
_P2_FIELD_LINE_RE = re.compile(r"^(packages|domains|ui_affected|gate_commands):")


def parse_gate_commands_block(text):
    """解析 gate_commands 多行块 → (has_block, [(key, value), ...])。

    M2 起 agate-read-gate-commands.py / check-gate.py 共用（BDD-9：块正则不在消费脚本
    字面出现，落在公共库单点，防"同一规则多处实现"漂移）。无块/空块 → (False, [])。
    """
    if not text.endswith("\n"):
        text += "\n"
    m = _GATE_COMMANDS_BLOCK_RE.search(text)
    if not m:
        return False, []
    return True, _GATE_KEY_LINE_RE.findall(m.group(1))


def count_p2_declared_fields(text):
    """统计 P2 四字段（packages/domains/ui_affected/gate_commands）声明行数（列 0 匹配）。

    M2 起 check-gate.py P2 分支用（BDD-9：四字段行正则不在消费脚本字面出现）。
    语义与原内联 `sum(1 for line in text.splitlines() if re.match(...))` 等价——
    frontmatter 与正文都算（真实 P2-design.md 四字段散落两处）。
    """
    return sum(1 for line in text.splitlines() if _P2_FIELD_LINE_RE.match(line))


# ---------- M2-0038：task md 共享读取器（TAG0022 RM-AG0038，BDD-3/4/5） ----------
# 已迁移解析点（P1 §4.2 B/C/D 组）从 check-gate.py 抽到公共库单点（对齐 M2 的
# parse_gate_commands_block 先例）：BDD-3 静态扫描（test_md_parse_scan.py）要求这些
# 模式在消费脚本（check-gate.py）非注释代码行中字面命中数 = 0，共享解析落在本库
# （不在扫描清单内）。行为与原内联实现逐字节等价（well-formed 输入口径）：
#   * B 组 = P1 行首标记（RM-AG0001 可选反引号前缀）+ 计数/描述提取
#   * C 组 = 任务产出格式判定（BDD 标题 / UI 节 / 候选数 / P6/P7 计数 / DESIGN_GAP /
#            CODE_MAP / fail-list / known-failures / 关键词 presence）
#   * D 组 = md 内嵌 ```yaml/```yml 围栏块提取

# B 组：P1 行首标记（与 sh grep -cE 逐行语义一致；`*-? `* = 可选反引号 + dash 前缀，
# RM-AG0001：反引号包裹标记不再漏计，含 - `[..]` 反引号在 dash 之后的形态）。
_NC_RE = re.compile(r"^\s*`*-?\s*`*\[NEED_CONFIRM\]")
_SUGGEST_RE = re.compile(r"^\s*`*-?\s*`*\[SUGGEST:")
_NO_NEED_RE = re.compile(r"^\s*`*-?\s*`*\[NO_NEED_CONFIRM\]")

# P1 流 C 描述提取（sed -E s/^...// 等价）：NEED_CONFIRM 单段剥离（含后续空白）；
# SUGGEST 三连 s/// 等价：剥离前缀 → 剥尾部反引号+空白 → 剥尾部 ]。
_NC_DESC_RE = re.compile(r"^\s*`*-?\s*`*\[NEED_CONFIRM\]\s*")
_SUGGEST_DESC_RE = re.compile(r"^\s*`*-?\s*`*\[SUGGEST:\s*")
_SUGGEST_TAIL_BT_RE = re.compile(r"`\s*$")
_SUGGEST_TAIL_BRACKET_RE = re.compile(r"\]\s*$")


def count_markers(text, kind):
    """P1 正文行首标记计数（kind ∈ NC/SUGGEST/NO_NEED）；未知 kind → 0。

    M2-0038 B 组：原 check-gate gate_p1 `sum(1 for line in lines if _X_RE.search(line))`
    逐行语义等价（splitlines 剥尾 \\r，与 check-gate _lines 同）。
    """
    if not text:
        return 0
    lines = text.splitlines()
    if kind == "NC":
        return sum(1 for line in lines if _NC_RE.search(line))
    if kind == "SUGGEST":
        return sum(1 for line in lines if _SUGGEST_RE.search(line))
    if kind == "NO_NEED":
        return sum(1 for line in lines if _NO_NEED_RE.search(line))
    return 0


def has_marker(line, kind):
    """单行是否含 P1 行首标记（kind ∈ NC/SUGGEST/NO_NEED）。"""
    if kind == "NC":
        return bool(_NC_RE.search(line))
    if kind == "SUGGEST":
        return bool(_SUGGEST_RE.search(line))
    if kind == "NO_NEED":
        return bool(_NO_NEED_RE.search(line))
    return False


def extract_marker_desc(line, kind):
    """提取 P1 标记行描述：NC = 剥离前缀（含后续空白）；SUGGEST = 三连剥离；其他原样。"""
    if kind == "NC":
        return _NC_DESC_RE.sub("", line)
    if kind == "SUGGEST":
        desc = _SUGGEST_DESC_RE.sub("", line)
        desc = _SUGGEST_TAIL_BT_RE.sub("", desc)
        desc = _SUGGEST_TAIL_BRACKET_RE.sub("", desc)
        return desc
    return line


# C 组：任务产出格式判定读取器

def extract_bdd_titles(text):
    """提取 md BDD 标题行（`##`~`#####` 级 `BDD-N:` 标题）→ 换行连接字符串。

    P1 UI 维度合法性判定用（维度扩展名须在 UX 类别 BDD 标题出现）。与原内联
    `"\n".join(re.findall(r"^#{2,5}\\s+BDD-[0-9]+.*$", text, re.MULTILINE))` 等价。
    """
    return "\n".join(re.findall(r"^#{2,5}\s+BDD-[0-9]+.*$", text, re.MULTILINE))


def parse_ui_design_section(text):
    """解析 P2-design.md UI 设计节 → (ui_block, shape_line, dim_line)。

    无 `#{2,3} UI 设计` 节标题 → (None, "", "")。ui_block = 节标题起全文（含标题行）；
    shape_line / dim_line = 节内首条 `渲染形态:` / `适用维度:` 声明行内容（剥 list 前缀）。
    """
    m = re.search(r"^#{2,3}\s+UI 设计", text, re.MULTILINE)
    if not m:
        return None, "", ""
    ui_block = text[m.start():]
    shape_line = ""
    dim_line = ""
    for line in ui_block.splitlines():
        mm = re.match(r"^\s*[-*]?\s*渲染形态\s*[:：]\s*(.+)$", line)
        if mm and not shape_line:
            shape_line = mm.group(1).strip()
        mm = re.match(r"^\s*[-*]?\s*适用维度\s*[:：]\s*(.+)$", line)
        if mm and not dim_line:
            dim_line = mm.group(1).strip()
    return ui_block, shape_line, dim_line


def candidate_count_value(line):
    """扫描 P2-design.md `candidate_count:` 行首声明 → 行内首个数字串 int。

    行首不匹配 → None；匹配但无数字 → 0（与原 check-gate P2 分支内联循环
    `if re.match(...): m = re.search(...); if m: candidate_count = int(...)` + break 等价）。
    """
    if re.match(r"^candidate_count:", line):
        m = re.search(r"[0-9]+", line)
        return int(m.group(0)) if m else 0
    return None


def design_trivial_declared(line):
    """P1-requirements.md 行首 `design_trivial:` / `follows_existing_pattern:` 声明 presence。"""
    return bool(re.search(r"^(design_trivial|follows_existing_pattern):\s*\S", line))


def has_keyword(text, kind):
    """任务产出关键词 presence 判定（kind ∈ tradeoff / choice_and_reason / design_gap）。"""
    if kind == "tradeoff":
        return bool(re.search(r"权衡|选择理由|取舍|考量|trade-?off|理由与权衡", text))
    if kind == "choice_and_reason":
        return bool(re.search(r"选择", text) and re.search(r"理由|原因|因为", text))
    if kind == "design_gap":
        return bool(re.search(r"设计偏差|design gap|未列入|gap:", text, re.IGNORECASE))
    return False


def count_p6_pass_fail(text):
    """P6-acceptance.md 旧格式正文行首 PASS/FAIL 计数（须含 BDD 编号，大小写不敏感）。

    返回 (total, fail)。与原 check-gate gate_p6 旧格式回退两行 sum 等价。
    """
    lines = text.splitlines()
    total = sum(
        1 for line in lines
        if re.search(r"^\s*- (PASS|FAIL)\b.*BDD-[0-9]", line, re.IGNORECASE)
    )
    fail = sum(
        1 for line in lines
        if re.search(r"^\s*- FAIL\b.*BDD-[0-9]", line, re.IGNORECASE)
    )
    return total, fail


def count_p7_markers(text):
    """P7-consistency.md 旧格式正文 BLOCKER/DEVIATION-CRITICAL 计数 → (blockers, devcrit)。

    排除 `[BLOCKER]: N 条` / `[DEVIATION-CRITICAL]: N 条` 汇总行（M4：[:：] 全角冒号
    alternation，POSIX locale 不匹配全角冒号的问题）。
    """
    lines = text.splitlines()
    blockers = 0
    devcrit = 0
    for line in lines:
        if re.search(r"^\s*-?\s*\[BLOCKER\]", line) and not re.search(
            r"\[BLOCKER\](:|：)?\s*[0-9]+\s*条?\s*$", line
        ):
            blockers += 1
        if re.search(r"^\s*-?\s*\[DEVIATION-CRITICAL\]", line) and not re.search(
            r"\[DEVIATION-CRITICAL\](:|：)?\s*[0-9]+\s*条?\s*$", line
        ):
            devcrit += 1
    return blockers, devcrit


def count_design_gap(text, allow_blockquote=True):
    """P7/P4 正文 DESIGN_GAP / DESIGN_GAP_REVIEWED 行首标记计数 → (count, reviewed)。

    allow_blockquote=True（P7 口径）：`^\\s*>?\\s*-?\\s*\\[DESIGN_GAP:`（含 blockquote
    前缀）；False（P4 转抄核对口径）：仅 `^\\s*-?\\s*\\[DESIGN_GAP:`（与 grep -cE 等价）。
    """
    pattern = r"^\s*>?\s*-?\s*\[DESIGN_GAP:" if allow_blockquote else r"^\s*-?\s*\[DESIGN_GAP:"
    count = sum(1 for line in text.splitlines() if re.search(pattern, line))
    reviewed = sum(
        1 for line in text.splitlines()
        if re.search(r"^\s*>?\s*-?\s*\[DESIGN_GAP_REVIEWED", line)
    )
    return count, reviewed


def count_code_map_lines(text):
    """P4-implementation.md 正文 [CODE_MAP_UPDATED]/[CODE_MAP_EXEMPT] 行首标记计数。"""
    return sum(
        1 for line in text.splitlines()
        if re.search(r"^\s*-?\s*\[CODE_MAP_UPDATED\]", line)
        or re.search(r"^\s*-?\s*\[CODE_MAP_EXEMPT", line)
    )


def parse_fail_list_block(text):
    """解析 pre-task-baseline.md ```fail-list 代码块 → 行列表（剥首尾 ``` 与空行）。

    等价 sed -n '/```fail-list/,/```/p' | sed '1d;$d' | grep -v '^$'。
    """
    lines = text.splitlines()
    start = next((i for i, line in enumerate(lines) if "```fail-list" in line), None)
    if start is None:
        return []
    end = next((i for i in range(start + 1, len(lines)) if "```" in lines[i]), None)
    end = len(lines) if end is None else end + 1
    pre = lines[start:end]
    if len(pre) > 0:
        pre = pre[1:]
    if len(pre) > 0:
        pre = pre[:-1]
    return [line for line in pre if line]


def count_kf_entries(text):
    """known-failures.md 登记表条目计数（行首 `| N |`）。"""
    return sum(1 for line in text.splitlines() if re.search(r"^\|\s*[0-9]+\s*\|", line))


# D 组：md 内嵌 yaml/yml 围栏块提取（read_vision_tri_state 与 check-gate 兜底共用单点）
_EMBEDDED_YAML_BLOCK_RE = re.compile(r"```(?:yaml|yml)\s*\n(.*?)```", re.DOTALL)


def extract_embedded_yaml_blocks(text):
    """提取 md 内嵌 ```yaml/```yml 围栏块内容列表（含 content，不含围栏）。

    与原 check-gate `_gate_p1_vision_capability` 兜底 `re.finditer(...)` 循环同正则单点。
    """
    return [m.group(1) for m in _EMBEDDED_YAML_BLOCK_RE.finditer(text)]


if __name__ == "__main__":
    project_root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    workspace, tasks_dir = resolve_workspace(project_root)
    print(f"AGATE_WORKSPACE={workspace}")
    print(f"AGATE_TASKS_DIR={tasks_dir}")
