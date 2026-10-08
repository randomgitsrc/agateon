#!/usr/bin/env python3
"""agate-ci-verify.py — CI 逐提交回放（TAG0050 批 A2，设计 §2.4；修复 F15）

不再"重跑当前 phase 的 gate"，改为**在 hook 当时的条件下逐提交回放本地 hook**
（`pre-commit-gate.py` + `commit-msg-self-gate.py`）。本地账本无密钥，`commit --amend`
或 `reset --soft` 之后改写账本本地规则发现不了；可信锚点是受保护分支上的 CI 回放。

回放范围（合并提交一律跳过）：
  * GitHub PR（`--base <sha>`）：`rev-list --no-merges <merge-base(base,HEAD)>..HEAD`
  * GitHub push（`--push --base <sha>`）：`rev-list --no-merges <before>..HEAD`
  * 本地缺省：`merge-base HEAD origin/<默认分支>`
只回放**改动了任一任务目录**的提交；没有这类提交 → `SKIP:` + 原因。

回放方法（每个提交 C，临时 worktree）：`worktree add --detach <wt> C` → `clean -fdx`
→ `reset --soft C^1` → 依次跑 `pre-commit-gate.py` + `commit-msg-self-gate.py <msgfile>`；
任一 rc ≠ 0 → FAIL + 输出提交 SHA + 原因。回放模式 `AGATE_REPLAY=1`。

回放协议版本（设计 §2.4）：② 未固定但**仓库本身含协议本体**（agateon-like）→ merge-base
处的 `agate/`；或 `AGATE_ROOT` 环境提供协议 → 其仓库 merge-base 处的 `agate/`；
③ 其他未固定版本的项目 → FAIL（提示写 `.agate-version`）。
① 按逐提交 `.agate-version` 定位/安装对应版本目录**未实现**（依赖 CI 安装各版本，见
`P4-implementation-G1.md` 的 DESIGN_GAP）——`.agate-version` 目前只用于「单调不降」检查
（降级判 FAIL），**不用于选协议根**。
判定分支③只认「仓库里的 `.agate-version`」或「仓库本身含协议本体」——`AGATE_ROOT` 环境变量
只是回放时**提供**协议根的输入，不作为"项目固定了版本"的证据（使用者项目即便 CI 里设了它，
未写 `.agate-version` 仍须 FAIL）。
**已知绕过面（F-5 影响 2，本批显式降级）**：对**某提交缺失** `.agate-version`（非仓库本体、
merge-base 处曾有）的情形，单调不降检查返回 `None → continue`，**不判 FAIL**——即一次删除
`.agate-version` 的提交可让项目不再钉版本。设计 §2.4 只写「不低于 merge-base」，未写「删除」，
本批**不实现**该判据，留待后续批次/DEBT（见 `P4-implementation-G1.md` 的 DESIGN_GAP）。

只在 CI 做的额外检查（与逐提交回放**解耦**，不依赖 `--no-merges` 过滤后的提交列表，
**无条件执行**——即使范围内没有改动任务目录的提交也照常）：
  1. 对 `<base>..HEAD` 中**全部**变化过的账本（含合并提交引入的）做**最终状态**检查
     （含创建事件的账本被删除/截空/改写 → FAIL；`check_ledger_events` 事件规则 → FAIL）；
     枚举用 `diff --name-status --no-renames`，以同时取到改名时被摘除的**源路径**。
  2. 新增任务目录的 `contract_level` 必须 ≥ **merge-base**（= `<base>`）处 `LEVELS.yaml`
     的最大已登记等级（设计 §2.4 第 4 点；分支在途跨越协议升级时 merge-base 仍是旧等级，
     故不误报）。

退出码：0 = 通过 / 显式跳过；1 = 判定失败（FAIL）。
平台无关：显式 utf-8；无系统临时目录字面量（tempfile）；Python 3.8+。
"""

import argparse
import contextlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

_AGATE_ROOT_DEFAULT = os.path.dirname(SCRIPT_DIR)
_TASKS_PREFIX = "agate-workspace/tasks/"
_LEDGER_NAME = "gate-events.jsonl"

try:
    from agate_common import check_ledger_events as _check_ledger_events
except Exception:  # pragma: no cover - 安装破损时降级（CI 账本事件规则检查跳过）
    _check_ledger_events = None

_VERSION_RE = re.compile(r"agate:\s*v?([0-9]+)\.([0-9]+)\.([0-9]+)")


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _git(args, cwd, env=None):
    try:
        proc = subprocess.run(
            ["git", *args], cwd=cwd, capture_output=True, text=True,
            encoding="utf-8", errors="replace", env=env,
        )
        return proc.returncode, proc.stdout, proc.stderr
    except OSError:
        return 127, "", ""


def _git_out(args, cwd):
    rc, out, _ = _git(args, cwd)
    return out.strip() if rc == 0 else ""


def _git_show(repo, rev, path):
    """`git show <rev>:<path>` 文本；失败（路径不存在）返回 None。"""
    rc, out, _ = _git(["show", f"{rev}:{path}"], repo)
    return out if rc == 0 else None


def _norm(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def _default_branch(repo):
    rc, out, _ = _git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], repo)
    if rc == 0 and out.strip():
        return out.strip().split("/")[-1]
    for name in ("main", "master"):
        if _git_out(["rev-parse", "--verify", f"origin/{name}"], repo):
            return name
    return "main"


def _merge_base(repo, a="HEAD", b=None):
    b = b or ("origin/" + _default_branch(repo))
    return _git_out(["merge-base", a, b], repo)


def _is_zero_sha(sha):
    """全零 SHA（GitHub push 事件的 `before` 在新建分支时全零）。"""
    return bool(sha) and set(sha) == {"0"}


def _is_legacy_commit(repo, sha):
    """该提交改动的任务目录是否均为 legacy（账本无创建/迁入事件）。"""
    dirs = _changed_task_dirs(repo, sha)
    if not dirs:
        return False
    for d in dirs:
        text = _git_show(repo, sha, d + "/" + _LEDGER_NAME)
        if text is not None and _ledger_has_origin(text):
            return False
    return True


def _parse_version(text):
    m = _VERSION_RE.search(text or "")
    return tuple(int(x) for x in m.groups()) if m else None


def _version_in_commit(repo, rev):
    return _parse_version(_git_show(repo, rev, ".agate-version"))


def _repo_has_protocol_body(repo):
    return bool(_git_out(["rev-parse", "--verify", "HEAD:agate/scripts/pre-commit-gate.py"], repo))


def _agate_root_repo(agate_root):
    """`AGATE_ROOT`（…/agate）→ 其所在仓库根；否则返回 AGATE_ROOT 本身。"""
    root = agate_root.rstrip("/\\")
    if os.path.basename(root) == "agate":
        return os.path.dirname(root)
    return root


def _make_protocol_worktree(repo, rev):
    """在 repo 的 rev 处建临时 worktree，返回其路径（含 agate/）；失败返回 None。"""
    wt = tempfile.mkdtemp(prefix="agate-proto-")
    rc, _, _ = _git(["worktree", "add", "--detach", wt, rev], repo)
    if rc != 0:
        shutil.rmtree(wt, ignore_errors=True)
        return None
    if not os.path.isdir(os.path.join(wt, "agate", "scripts")):
        _git(["worktree", "remove", "--force", wt], repo)
        shutil.rmtree(wt, ignore_errors=True)
        return None
    return wt


def _resolve_protocol(repo, agate_root_env):
    """回放协议根 → (protocol_root, cleanup, note)。

    `cleanup` 为 `(proto_repo, worktree_path)` 或 None——协议 worktree 建在
    `proto_repo`（AGATE_ROOT 所在仓库 / 仓库本体）中，故清理必须回到**同一个仓库**执行。
    """
    # ② agateon-like：AGATE_ROOT 环境提供协议 → 用其仓库 merge-base 处的 agate/
    if agate_root_env and os.path.isdir(os.path.join(agate_root_env, "scripts")):
        proto_repo = _agate_root_repo(agate_root_env)
        mb = _merge_base(proto_repo)
        if mb:
            wt = _make_protocol_worktree(proto_repo, mb)
            if wt:
                return os.path.join(wt, "agate"), (proto_repo, wt), f"merge-base {mb[:8]} 的 agate/"
        return agate_root_env, None, "AGATE_ROOT 环境"
    if _repo_has_protocol_body(repo):
        mb = _merge_base(repo)
        if mb:
            wt = _make_protocol_worktree(repo, mb)
            if wt:
                return os.path.join(wt, "agate"), (repo, wt), f"merge-base {mb[:8]} 的 agate/"
    return None, None, None


def _changed_task_dirs(repo, sha):
    """该提交改动的任务目录集合（tasks 下含 .state.yaml 的直接子目录）。"""
    rc, out, _ = _git(["diff-tree", "--no-commit-id", "--name-only", "-r", sha], repo)
    if rc != 0:
        return set()
    dirs = set()
    for line in out.splitlines():
        f = line.strip()
        if not f.startswith(_TASKS_PREFIX):
            continue
        rest = f[len(_TASKS_PREFIX):]
        if "/" in rest:
            dirs.add(_TASKS_PREFIX + rest.split("/", 1)[0])
    return dirs


def _is_task_ledger_path(path):
    """路径是否为**任务账本**（`agate-workspace/tasks/<task>/gate-events.jsonl`）。

    与 `_changed_task_dirs` 的 `_TASKS_PREFIX` 口径一致——只有 tasks 下的**直接子目录**里的
    `gate-events.jsonl` 才是任务账本。排除测试夹具等非任务账本路径（如
    `agate/tests/fixtures/.../gate-events.jsonl`，其内容可能故意非法，供 fail 用例断言判 FAIL），
    否则故意非法的黄金夹具会被当真实账本误判 FAIL。
    """
    if not path.startswith(_TASKS_PREFIX) or not path.endswith(_LEDGER_NAME):
        return False
    parts = path[len(_TASKS_PREFIX):].split("/")
    return len(parts) == 2 and parts[1] == _LEDGER_NAME


def _replay_commit(repo, sha, protocol_root):
    """在临时 worktree 中回放单个提交的 pre-commit + commit-msg hook。

    返回 (ok, reason)。
    """
    wt = tempfile.mkdtemp(prefix="agate-replay-")
    rc, _, err = _git(["worktree", "add", "--detach", wt, sha], repo)
    if rc != 0:
        shutil.rmtree(wt, ignore_errors=True)
        return False, f"worktree add 失败：{err.strip()}"
    msgfile = None
    try:
        _git(["clean", "-fdx"], wt)
        parent = _git_out(["rev-parse", f"{sha}^1"], repo)
        if parent:
            _git(["reset", "--soft", parent], wt)
        env = dict(os.environ)
        env["AGATE_ROOT"] = protocol_root
        env["AGATE_REPLAY"] = "1"

        proc = subprocess.run(
            [sys.executable, os.path.join(protocol_root, "scripts", "pre-commit-gate.py")],
            cwd=wt, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            return False, (proc.stderr or proc.stdout).strip()[-800:]

        rc_msg, msg, _ = _git(["log", "-1", "--format=%B", sha], repo)
        msg = msg if rc_msg == 0 else ""
        fd, msgfile = tempfile.mkstemp(prefix="agate-msg-", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(msg)
        # commit-msg 用**当前**协议（SCRIPT_DIR）执行：SELF-GATE 留痕是版本无关的策略，
        # 且其回放模式（AGATE_REPLAY=1 时缺 trailer 判 FAIL）由本版本引入（设计 §2.4 边界）。
        proc2 = subprocess.run(
            [sys.executable, os.path.join(SCRIPT_DIR, "commit-msg-self-gate.py"), msgfile],
            cwd=wt, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        if proc2.returncode != 0:
            return False, (proc2.stderr or proc2.stdout).strip()[-800:]
        return True, ""
    finally:
        if msgfile and os.path.exists(msgfile):
            os.remove(msgfile)
        _git(["worktree", "remove", "--force", wt], repo)
        shutil.rmtree(wt, ignore_errors=True)


def _ledger_has_origin(text):
    import json as _json
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            ev = _json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict) and ev.get("event") in ("task_created", "task_adopted"):
            return True
    return False


def _check_one_ledger_text(text):
    """对账本文本跑 `check_ledger_events`（经临时任务目录）。返回错误列表。"""
    if _check_ledger_events is None:
        return []
    tmp = tempfile.mkdtemp(prefix="agate-ledger-")
    try:
        with open(os.path.join(tmp, _LEDGER_NAME), "w", encoding="utf-8") as fh:
            fh.write(text)
        return list(_check_ledger_events(tmp))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _ci_ledger_checks(repo, base, head):
    """`<base>..HEAD` 中每个变化过的账本做**最终状态**检查（设计 §2.4 第 4 点）：
    含创建/迁入事件的账本被删除/截空/改写 → FAIL；事件规则（`check_ledger_events`）→ FAIL。

    只检查**任务账本**（`_is_task_ledger_path`）——非任务账本路径（如测试夹具）不计入，否则
    故意非法的黄金夹具会被当真实账本误判 FAIL。

    与逐提交回放**解耦**：枚举 `rev-list <base>..<head>` 的**全部**提交（**含合并提交**），
    故合并提交（evil merge）引入的账本变化同样被检查；不依赖调用方按 `--no-merges` 过滤后的
    提交列表。每个提交用 `diff --name-status --no-renames <parent> <c>` 枚举变化账本——
    `--no-renames` 保证改名时**同时**输出被删除的源路径与新增的目标路径（git 默认改名检测
    只输出目标路径，会漏掉源账本被摘除）。
    """
    errors = []
    seen = set()
    rc, out, _ = _git(["rev-list", f"{base}..{head}"], repo)
    if rc != 0:
        return errors
    for c in [ln.strip() for ln in out.splitlines() if ln.strip()]:
        parent = _git_out(["rev-parse", f"{c}^1"], repo)
        if not parent:
            continue
        rc, out2, _ = _git(["diff", "--name-status", "--no-renames", parent, c], repo)
        if rc != 0:
            continue
        for line in out2.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            path = parts[-1].strip()
            if not _is_task_ledger_path(path):
                continue
            if (c, path) in seen:
                continue
            seen.add((c, path))
            parent_text = _git_show(repo, parent, path)
            cur_text = _git_show(repo, c, path)
            if (parent_text is not None and _ledger_has_origin(parent_text)
                    and (cur_text is None or not _norm(cur_text).startswith(_norm(parent_text)))):
                errors.append(
                    f"{path}: 含创建/迁入事件的账本被删除/截空/改写（防降回 legacy）")
                continue
            if cur_text is not None:
                for msg in _check_one_ledger_text(cur_text):
                    errors.append(f"{path}: {msg}")
    return errors


def _levels_max_at(repo, rev):
    """`rev` 处 `agate/rules/task-data/LEVELS.yaml` 的最大已登记等级；缺失/非法 → None。"""
    text = _git_show(repo, rev, "agate/rules/task-data/LEVELS.yaml")
    if text is None:
        return None
    try:
        import yaml
        data = yaml.safe_load(text)
    except Exception:
        return None
    if not isinstance(data, list):
        return None
    levels = [item["level"] for item in data
              if isinstance(item, dict) and isinstance(item.get("level"), int)]
    return max(levels) if levels else None


def _task_origin_level(repo, rev, task_dir):
    """`rev` 处 task_dir 账本首个创建/迁入事件的 contract_level；无 → None。"""
    text = _git_show(repo, rev, task_dir + "/" + _LEDGER_NAME)
    if text is None:
        return None
    import json as _json
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            ev = _json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict) and ev.get("event") in ("task_created", "task_adopted"):
            lvl = ev.get("contract_level")
            return lvl if isinstance(lvl, int) else None
    return None


def _ci_level_checks(repo, base, head):
    """设计 §2.4 第 4 点：新增任务目录的 `contract_level` ≥ merge-base 处 LEVELS.yaml 最大等级。

    merge-base 即本函数的 `base`（PR/push 口径下 `base` 已是 merge-base）。分支在途中跨越协议
    升级时 merge-base 处仍是旧等级，故不误报（BDD-30）。新任务目录 = `<base>..<head>` 中
    以 A（新增）状态出现的任务目录。
    """
    errors = []
    max_level = _levels_max_at(repo, base)
    if max_level is None:
        return errors
    rc, out, _ = _git(["diff", "--name-status", "--no-renames", base, head], repo)
    if rc != 0:
        return errors
    new_dirs = set()
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        status, path = parts[0].strip(), parts[-1].strip()
        if not status.startswith("A") or not path.startswith(_TASKS_PREFIX):
            continue
        rest = path[len(_TASKS_PREFIX):]
        if "/" in rest:
            new_dirs.add(_TASKS_PREFIX + rest.split("/", 1)[0])
    for d in sorted(new_dirs):
        lvl = _task_origin_level(repo, head, d)
        if lvl is None:
            continue
        if lvl < max_level:
            errors.append(
                f"{d}: 新任务 contract_level={lvl} < merge-base 处 LEVELS.yaml 最大等级 {max_level}")
    return errors


def _skip(reason):
    print("=" * 66)
    print(f"SKIP: {reason}")
    print("  ⇒ 本次**未实际回放** gate（不是「跑了且通过」）")
    print("=" * 66)
    return 0


def _fail(reason):
    print(f"FAIL: {reason}")
    return 1


def main():
    _force_utf8()
    ap = argparse.ArgumentParser(description="CI 逐提交回放（TAG0050 A2）")
    ap.add_argument("--base", default=None, help="PR/push 的 base（before）提交")
    ap.add_argument("--push", action="store_true", help="push 口径（before..HEAD）")
    args = ap.parse_args()

    repo = os.path.realpath(os.getcwd())
    if not _git_out(["rev-parse", "--show-toplevel"], repo):
        return _skip("非 git 仓库（cwd 无 .git）")
    repo = _git_out(["rev-parse", "--show-toplevel"], repo)
    agate_root_env = os.environ.get("AGATE_ROOT", "")
    started = time.time()

    head = _git_out(["rev-parse", "HEAD"], repo)
    if not head:
        return _skip("无法解析 HEAD")

    # 回放范围
    if args.base:
        if args.push:
            # push 口径：before 为全零（新建分支）→ 回退 merge-base HEAD origin/<默认分支>
            base = _merge_base(repo, "HEAD") if _is_zero_sha(args.base) else args.base
            if not base:
                return _skip(
                    f"push 的 before 为全零且无法解析 merge-base HEAD "
                    f"origin/{_default_branch(repo)}")
        else:
            base = _git_out(["merge-base", args.base, head], repo) or args.base
    else:
        base = _merge_base(repo, "HEAD")
        if not base:
            return _skip(f"无法解析 merge-base HEAD origin/{_default_branch(repo)}（本地缺省口径）")
    rc, out, _ = _git(["rev-list", "--no-merges", f"{base}..{head}"], repo)
    if rc != 0:
        return _fail(f"rev-list {base[:8]}..{head[:8]} 失败")
    commits = [ln.strip() for ln in out.splitlines() if ln.strip()]
    commits.reverse()  # 旧→新

    # CI-only 额外检查（设计 §2.4 第 4 点）：与逐提交回放**解耦**，**无条件执行**——
    # 即使范围内没有改动任务目录的提交（squash push / evil merge）也照常检查。合并提交引入
    # 的账本变化由 `_ci_ledger_checks` 内部的 `rev-list`（含合并）覆盖。
    ledger_errors = _ci_ledger_checks(repo, base, head)
    level_errors = _ci_level_checks(repo, base, head)
    for err in ledger_errors:
        print(f"  FAIL 账本: {err}")
    for err in level_errors:
        print(f"  FAIL 等级: {err}")
    ci_extra_failed = bool(ledger_errors or level_errors)

    # 协议版本检查（设计 §2.4 第 3 点）：逐提交读 C 树，单调不降
    base_ver = _version_in_commit(repo, base)
    prev = base_ver
    any_ver = base_ver is not None
    for c in commits:
        v = _version_in_commit(repo, c)
        if v is None:
            continue
        any_ver = True
        if prev is not None and v < prev:
            return _fail(
                f".agate-version 降级于提交 {c[:8]}（{'.'.join(map(str, prev))} → "
                f"{'.'.join(map(str, v))}）：单调不降被违反")
        prev = v

    # 只回放改动了任一任务目录的提交
    task_commits = [c for c in commits if _changed_task_dirs(repo, c)]
    if not task_commits:
        # 无任务提交本应 SKIP，但 CI-only 额外检查（账本/等级）**无条件**先行——有 FAIL 即判失败
        # （evil merge 删账本正是靠这条在 SKIP 之前被拦下）。
        if ci_extra_failed:
            print(f"CI-only 额外检查失败（{len(ledger_errors)} 账本 / {len(level_errors)} 等级）"
                  f"，回放范围 {base[:8]}..{head[:8]} 未改动任务目录")
            return 1
        return _skip(f"回放范围 {base[:8]}..{head[:8]} 未改动任务目录（{len(commits)} 个提交）")

    # 需要回放 ⇒ 必须有可信的协议版本：① 仓库里的 `.agate-version`；② 仓库本身含协议本体
    # （agateon-like）。`AGATE_ROOT` 环境变量只是回放时**提供**协议根，不作为"项目固定了版本"
    # 的证据——使用者项目即便 CI 里设了它，未写 `.agate-version` 仍须 FAIL（设计 §2.4 分支③）。
    if not any_ver and not _repo_has_protocol_body(repo):
        return _fail("未固定协议版本，无法可信回放；请写 .agate-version（agate: vX.Y.Z）")

    protocol_root, cleanup, note = _resolve_protocol(repo, agate_root_env)
    if not protocol_root:
        return _fail("未固定协议版本，无法可信回放；请写 .agate-version（agate: vX.Y.Z）")

    try:
        print(f"回放: {len(commits)} 个非合并提交（协议：{note}）")
        failures = []
        for c in commits:
            ok, reason = _replay_commit(repo, c, protocol_root)
            if ok:
                print(f"  回放 {c[:8]}: PASS")
            else:
                print(f"  回放 {c[:8]}: FAIL")
                if reason:
                    print("    " + reason.replace("\n", "\n    "))
                failures.append((c, reason))

        # 设计 §8 第 12 项（G2 补记）：legacy 任务因「未暂存 .state.yaml 也做
        # PROD_TOUCHED 扫描」可能出现新的 ERROR——**单独统计并逐条列出 SHA**。
        prod_touched_legacy = [
            (c, reason) for c, reason in failures
            if "PROD_TOUCHED" in (reason or "") and _is_legacy_commit(repo, c)
        ]
        if prod_touched_legacy:
            print(f"  §8-12 legacy 新增 PROD_TOUCHED ERROR：{len(prod_touched_legacy)} 条")
            for c, _ in prod_touched_legacy:
                print(f"    - {c}")

        elapsed = time.time() - started
        print(f"回放完成：{len(commits)} 个提交，失败 {len(failures)} 个，耗时 {elapsed:.2f}s")
        if failures or ci_extra_failed:
            return 1
        print("PASS: 逐提交回放全部通过")
        return 0
    finally:
        if cleanup:
            proto_repo, proto_wt = cleanup
            _git(["worktree", "remove", "--force", proto_wt], proto_repo)
            shutil.rmtree(proto_wt, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
