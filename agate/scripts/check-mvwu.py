#!/usr/bin/env python3
"""check-mvwu.py — MVWU 阶段 1 观测器（TAG0036，RM-AG0063）

对任务目录的 `P2-design.md` 中 `dispatch_plan.batches` 的每一批，读取
`P4-evidence/<id>.log`（逐行 `key: value` 的证据日志），做六项静态检查并给出
四态 verdict（PASS / FAIL / EXPECTED_RED / UNKNOWN）。这是**观测器**：不挂 gate、
不挂 hook、不进 CI，任何 verdict 都不阻断任何流程。

用法：
  check-mvwu.py <task_dir>              默认模式：每批一行契约行
  check-mvwu.py --observe <task_dir>    观察表模式：每批一行 7 列 markdown 表格行

契约行（stdout，每批一行）：
  MVWU_RESULT: <VERDICT> batch=<id>[ reason=<token>]
  reason 词表：tests_filter / command / evidence / exit_code / git_head / expected_red
  （未 PASS 的行才带 reason；多故障并存时按上述检查顺序取首个命中者）。
  无可判定批（P2 缺失 / 无 dispatch_plan / 无 batches）时输出一行
  `MVWU_RESULT: UNKNOWN batch=- reason=tests_filter`。
  批 id 不合规（不匹配 [A-Za-z0-9._-]+）时按 UTF-8 字节把每个不合规字节编码为 \\xNN，
  非字符串/空 id 打印 `?`，保证每批恰一行且可按空白分词。

观察表行（--observe，stdout）：
  | MVWU | tests_filter | 耗时 | evidence | commit 形态 | boundary | verdict |
  无表头；诊断信息（含 git 基线不可确定的原因）只走 stderr。commit 形态 / boundary
  仅在任务分支相对默认分支的提交区间内统计，且**不参与 verdict**（阶段 1 口径）。

六项检查（判定顺序 = reason 优先级）：
  1 tests_filter 存在  2 evidence 存在  3 command 首词可解析  4 exit_code 可解析
  5 git_head 可关联  6 expected_red 核对
  verdict：exit_code=0 -> PASS；非零且无 expected_red -> FAIL；非零且 failed_tests
  非空、全部命中 expected_red -> EXPECTED_RED；预期外红灯 -> FAIL；无法核对 -> UNKNOWN。

退出码：0 = 任一 verdict（verdict 只经 stdout 契约行表达，永不令 commit/gate 失败）；
2 = 用法错误或目标目录不存在。脚本只读：除 stdout/stderr 外不写任何文件；
从不执行 command / tests_filter（只做 PATH / 可执行位的静态探测）。

已知局限（字面声明，固定锚点）：
  - 检查 3 仅检查首词：跳过前导 NAME=value 环境变量赋值后，只判第一个词是否可解析；
    复合命令（&& / || / ; / |）其后的命令不检查；cd/export/set/source/. 内建视为可解析。
  - 不比对 command 与 tests_filter：证据里实际执行的命令与 P2 声明是否一致不在观测范围。
  - UNKNOWN 不等价于 PASS，不得作为放行依据：UNKNOWN 只表示"证据不足以判定"。
"""

import argparse
import contextlib
import os
import re
import shlex
import shutil
import sys

import yaml

from agate_common import resolve_workspace, run_git, split_frontmatter

ID_RE = re.compile(r"[A-Za-z0-9._-]+")
SHA_RE = re.compile(r"(?:[0-9a-fA-F]{40}|[0-9a-fA-F]{64})")
ENV_ASSIGN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
KV_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$")
INT_RE = re.compile(r"[-+]?[0-9]+")
DURATION_RE = re.compile(r"[0-9]{1,15}(?:\.[0-9]{1,15})?")
BUILTINS = frozenset({"cd", "export", "set", "source", "."})

EVIDENCE_DIR = "P4-evidence"
MISSING = "MISSING"
CORRUPT = "CORRUPT"

NO_BATCH_LINE = "MVWU_RESULT: UNKNOWN batch=- reason=tests_filter"


def _warn(msg):
    sys.stderr.write(f"check-mvwu: {msg}\n")


# ---------------------------------------------------------------- P2 读取


def _load_batches(task_dir):
    """读 P2-design.md 的 dispatch_plan.batches；无可判定批返回 None。"""
    path = os.path.join(task_dir, "P2-design.md")
    try:
        with open(path, "rb") as f:
            text = f.read().decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    text = text.lstrip("\ufeff").replace("\r\n", "\n")
    fm, _ = split_frontmatter(text)
    if not isinstance(fm, dict):
        return None
    plan = fm.get("dispatch_plan")
    if not isinstance(plan, dict):
        return None
    batches = plan.get("batches")
    if not isinstance(batches, list) or not batches:
        return None
    return batches


# ---------------------------------------------------------------- 输出编码


def _encode_id(bid):
    """批 id 打印形态（口径 D）：合规原样；不合规字节 -> \\xNN；非字符串/空 -> ?。"""
    if not isinstance(bid, str) or not bid:
        return "?"
    out = []
    for byte in bid.encode("utf-8", "replace"):
        ch = chr(byte)
        if byte < 0x80 and ID_RE.fullmatch(ch):
            out.append(ch)
        else:
            out.append(f"\\x{byte:02x}")
    return "".join(out)


_CELL_MAP = {"\\": "\\\\", "|": "\\|", "`": "\\`", "\n": "\\n", "\r": "\\r"}


def _escape_cell(value):
    """markdown 表格单元转义（口径 D）：缺/空/非字符串 -> `-`。"""
    if not isinstance(value, str) or not value:
        return "-"
    out = []
    for ch in value:
        if ch in _CELL_MAP:
            out.append(_CELL_MAP[ch])
        elif ord(ch) < 0x20 or ord(ch) in (0x7F, 0x85):
            out.append(f"\\x{ord(ch):02x}")
        elif ord(ch) in (0x2028, 0x2029):
            out.append(f"\\u{ord(ch):04x}")
        else:
            out.append(ch)
    return "".join(out)


def _fmt_duration(raw):
    if not isinstance(raw, str) or not DURATION_RE.fullmatch(raw):
        return "-"
    try:
        if "." not in raw:
            return f"{int(raw)}s"
        val = float(raw)
        if val == int(val):
            return f"{int(val)}s"
        return f"{val:.1f}s"
    except (ValueError, OverflowError):
        return "-"


# ---------------------------------------------------------------- 证据读取


def _under(base, path):
    try:
        base_n, path_n = os.path.normcase(base), os.path.normcase(path)
        return os.path.commonpath([base_n, path_n]) == base_n
    except ValueError:
        return False


def _parse_evidence(text):
    """逐行 key: value；重复键后者覆盖；无任何 key: value 行 -> None。"""
    kv = {}
    for line in text.replace("\r", "").split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = KV_RE.match(stripped)
        if m:
            kv[m.group(1)] = m.group(2).strip()
    return kv or None


def _read_evidence(task_dir, bid):
    """返回 (exists, state)；state 为 MISSING / CORRUPT / dict。仅对合规 id 读文件。"""
    if not isinstance(bid, str) or not ID_RE.fullmatch(bid):
        return False, MISSING
    path = os.path.join(task_dir, EVIDENCE_DIR, bid + ".log")
    if not os.path.isfile(path):
        return False, MISSING
    base = os.path.join(os.path.realpath(task_dir), EVIDENCE_DIR)
    if not _under(base, os.path.realpath(path)):
        return True, CORRUPT  # 符号链接逃逸：不读取
    try:
        with open(path, "rb") as f:
            text = f.read().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return True, CORRUPT
    kv = _parse_evidence(text)
    return True, (kv if kv is not None else CORRUPT)


def _parse_list(raw):
    """单行 YAML flow 序列（元素须为 str）；键缺省 -> []；不可解析 -> None。"""
    if raw is None:
        return []
    if not (raw.startswith("[") and raw.endswith("]")):
        return None
    try:
        val = yaml.safe_load(raw)
    except Exception:
        return None
    if isinstance(val, list) and all(isinstance(x, str) for x in val):
        return val
    return None


# ---------------------------------------------------------------- git / 命令探测


class GitCtx:
    """git 顶层与 commit 存在性查询（懒计算、缓存）。"""

    def __init__(self, task_dir):
        self.task_dir = task_dir
        self._top = False

    @property
    def toplevel(self):
        if self._top is False:
            rc, out = run_git(["rev-parse", "--show-toplevel"], cwd=self.task_dir)
            self._top = out.strip() if rc == 0 and out.strip() else None
        return self._top

    def commit_exists(self, sha):
        if self.toplevel is None or not SHA_RE.fullmatch(sha):
            return False
        rc, _ = run_git(["cat-file", "-e", sha.lower() + "^{commit}"], cwd=self.toplevel)
        return rc == 0


def _first_word_ok(command, base):
    """口径 F：跳过前导 NAME=value，首词须可解析。永不执行命令。"""
    try:
        words = shlex.split(command, posix=(os.name != "nt"))
    except ValueError:
        return False
    while words and ENV_ASSIGN_RE.match(words[0]):
        words.pop(0)
    if not words:
        return False
    word = words[0]
    if word in BUILTINS:
        return True
    if "/" in word or (os.sep in word) or (os.altsep and os.altsep in word):
        cand = word if os.path.isabs(word) else os.path.join(base, word)
        return os.path.isfile(cand) and os.access(cand, os.X_OK)
    return shutil.which(word) is not None


# ---------------------------------------------------------------- 判定


def judge_batch(batch, ev_state, git, dup):
    """六步流水线，返回 (verdict, reason)；取首个命中的故障。"""
    tf = batch.get("tests_filter") if isinstance(batch, dict) else None
    if not isinstance(tf, str) or not tf.strip():
        return "UNKNOWN", "tests_filter"
    if dup or not isinstance(ev_state, dict):
        return "UNKNOWN", "evidence"
    command = ev_state.get("command")
    base = git.toplevel or git.task_dir
    if not command or not _first_word_ok(command, base):
        return "UNKNOWN", "command"
    raw_exit = ev_state.get("exit_code")
    if raw_exit is None or not INT_RE.fullmatch(raw_exit):
        return "UNKNOWN", "exit_code"
    exit_code = int(raw_exit)
    expected = _parse_list(ev_state.get("expected_red"))
    failed = _parse_list(ev_state.get("failed_tests"))
    if exit_code == 0 and failed:
        return "UNKNOWN", "exit_code"
    head = ev_state.get("git_head")
    if head is None or not git.commit_exists(head):
        return "UNKNOWN", "git_head"
    if expected is None or failed is None:
        return "UNKNOWN", "expected_red"
    if exit_code == 0:
        return "PASS", None
    if not expected:
        return "FAIL", None
    if not failed:
        return "UNKNOWN", "expected_red"
    if all(t in set(expected) for t in failed):
        return "EXPECTED_RED", None
    return "FAIL", None


def render_contract(bid, verdict, reason):
    line = f"MVWU_RESULT: {verdict} batch={_encode_id(bid)}"
    return line + (" reason=" + reason if reason else "")


# ---------------------------------------------------------------- --observe：commit 形态 / boundary


def _default_branch_base(cwd):
    """口径 E：返回 (base_sha, None) 或 (None, 原因)。"""
    cands = []
    rc, out = run_git(["symbolic-ref", "-q", "refs/remotes/origin/HEAD"], cwd=cwd)
    if rc == 0 and out.strip():
        cands.append(out.strip())
    cands += ["refs/heads/main", "refs/heads/master"]
    for ref in cands:
        rc, _ = run_git(["rev-parse", "--verify", "-q", ref + "^{commit}"], cwd=cwd)
        if rc != 0:
            continue
        rc, out = run_git(["merge-base", "HEAD", ref], cwd=cwd)
        base = out.strip()
        if rc != 0 or not base:
            return None, "baseline: no merge-base"
        rc, out = run_git(["rev-list", "--count", base + "..HEAD"], cwd=cwd)
        if rc != 0 or out.strip() in ("", "0"):
            return None, "baseline: empty range"
        return base, None
    return None, "baseline: no default branch (origin/HEAD, main, master)"


def _collect_range(cwd, base):
    """单趟读取区间内非合并提交的文件集：[(sha, set(files))]；失败 -> None。"""
    rc, out = run_git(
        ["-c", "core.quotepath=false", "log", "--no-merges", "--no-renames",
         "--name-only", "-z", "--format=%x01%H", base + "..HEAD"],
        cwd=cwd,
    )
    if rc != 0:
        return None
    commits = []
    for chunk in out.split("\x01"):
        parts = chunk.split("\x00")
        if not parts[0]:
            continue
        files = [p for p in parts[1:] if p]
        if files and files[0].startswith("\n"):
            files[0] = files[0][1:]
        commits.append((parts[0], set(files)))
    return commits


def _tasks_prefix(toplevel):
    """当前 workspace 的 tasks 目录相对顶层的 posix 前缀（含结尾 /）；顶层外 -> None。"""
    try:
        _, tasks_dir = resolve_workspace(toplevel)
        rel = os.path.relpath(tasks_dir, os.path.realpath(toplevel)).replace("\\", "/")
    except (OSError, ValueError):
        return None
    if rel == "." or rel.startswith(".."):
        return None
    return rel.rstrip("/") + "/"


def _norm_output(batch):
    out = batch.get("output") if isinstance(batch, dict) else None
    if not isinstance(out, list) or not out or not all(isinstance(x, str) and x for x in out):
        return None
    norm = set()
    for item in out:
        path = item.replace("\\", "/")
        while path.startswith("./"):
            path = path[2:]
        norm.add(path)
    return norm


def _forms_and_boundaries(batches, git):
    """返回 [(commit_form, boundary)]，与 batches 同序。"""
    unknown = ("UNKNOWN", "UNKNOWN")
    result = [unknown] * len(batches)
    top = git.toplevel
    if top is None:
        _warn("baseline: not a git repository")
        return result
    base, why = _default_branch_base(top)
    if base is None:
        _warn(why)
        return result
    commits = _collect_range(top, base)
    if commits is None:
        _warn("baseline: cannot read commit range")
        return result
    outputs = [_norm_output(b) for b in batches]
    touched = []
    for out in outputs:
        touched.append(set() if out is None else {sha for sha, files in commits if files & out})
    prefix = _tasks_prefix(top)
    files_of = dict(commits)
    for i, out in enumerate(outputs):
        if out is None or len(touched[i]) != 1:
            continue
        sha = next(iter(touched[i]))
        if any(j != i and sha in touched[j] for j in range(len(batches))):
            result[i] = ("merged", "UNKNOWN")
            continue
        changed = {f for f in files_of[sha] if not (prefix and f.startswith(prefix))}
        result[i] = ("per-batch", "exact" if changed == out else "mismatch")
    return result


def render_observe_row(cells):
    return "| " + " | ".join(cells) + " |"


# ---------------------------------------------------------------- main


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="check-mvwu.py",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("task_dir", help="任务目录（含 P2-design.md 与 P4-evidence/）")
    parser.add_argument("--observe", action="store_true", help="输出 7 列观察表行（每批一行）")
    return parser


def _run(task_dir, observe):
    batches = _load_batches(task_dir)
    if batches is None:
        if observe:
            print(render_observe_row(["-", "-", "-", "no", "UNKNOWN", "UNKNOWN", "UNKNOWN"]))
        else:
            print(NO_BATCH_LINE)
        return
    ids = [b.get("id") if isinstance(b, dict) else None for b in batches]
    counts = {}
    for bid in ids:
        if isinstance(bid, str):
            counts[bid] = counts.get(bid, 0) + 1
    git = GitCtx(task_dir)
    judged = []
    for batch, bid in zip(batches, ids):
        dup = isinstance(bid, str) and counts[bid] > 1
        exists, state = _read_evidence(task_dir, bid)
        try:
            verdict, reason = judge_batch(batch, state, git, dup)
        except Exception as exc:  # 意外异常：该批 UNKNOWN，不带 traceback
            _warn(f"internal error: {type(exc).__name__}: {exc}")
            verdict, reason = "UNKNOWN", "evidence"
        judged.append((verdict, reason, exists, state, dup))
    if not observe:
        for bid, (verdict, reason, _e, _s, _d) in zip(ids, judged):
            print(render_contract(bid, verdict, reason))
        return
    try:
        shapes = _forms_and_boundaries(batches, git)
    except Exception as exc:
        _warn(f"baseline: internal error: {type(exc).__name__}: {exc}")
        shapes = [("UNKNOWN", "UNKNOWN")] * len(batches)
    for batch, bid, (verdict, _r, exists, state, dup), (form, bound) in zip(batches, ids, judged, shapes):
        try:
            tf = batch.get("tests_filter") if isinstance(batch, dict) else None
            dur = _fmt_duration(state.get("duration_seconds")) if isinstance(state, dict) and not dup else "-"
            row = render_observe_row([
                _encode_id(bid), _escape_cell(tf), dur, "yes" if exists else "no", form, bound, verdict,
            ])
        except Exception as exc:  # 单行渲染意外异常：仅该批降级为 UNKNOWN 行，其余批不受影响
            _warn(f"internal error: {type(exc).__name__}: {exc}")
            row = render_observe_row([_encode_id(bid), "-", "-", "no", "UNKNOWN", "UNKNOWN", "UNKNOWN"])
        print(row)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            with contextlib.suppress(OSError, ValueError):
                stream.reconfigure(encoding="utf-8", errors="replace")
    args = _build_parser().parse_args(argv)
    if not os.path.isdir(args.task_dir):
        _warn(f"目标目录不存在 (does not exist): {args.task_dir}")
        return 2
    try:
        _run(args.task_dir, args.observe)
    except BrokenPipeError:
        pass
    except Exception as exc:  # 兜底：无 traceback，仍给出诚实 UNKNOWN 行
        _warn(f"internal error: {type(exc).__name__}: {exc}")
        print(NO_BATCH_LINE if not args.observe else
              render_observe_row(["-", "-", "-", "no", "UNKNOWN", "UNKNOWN", "UNKNOWN"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
