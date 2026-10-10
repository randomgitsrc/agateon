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
        AGATE_CARD_PLACEHOLDER_RE,
        append_event,
        check_ledger_events,
        current_level,
        git_hooks_dir,
        load_contract,
        match_declaration_file,
        read_ledger_events,
        read_staged_state_phase,
        read_state_phase,
        read_state_task_id,
        requirement_active,
        resolve_agate_root,
        resolve_workspace,
        run_git,
        split_frontmatter,
        task_level,
        write_gate_result,
    )
except Exception as exc:
    # 注意：agate_common 缺 pyyaml 时自身会打印提示并 sys.exit(1)（SystemExit 不在此
    # 捕获，仍 fail-closed exit 1）；此处捕获 ImportError（agate_common.py 本体缺失，
    # 如脚本被独立复制到缺公共库的目录）。
    sys.stderr.write(
        f"GATE ERROR: 无法加载 agate_common.py（公共库缺失，需 Python 3 + pyyaml）: {exc}\n"
    )
    sys.exit(1)

# 标记单源库（TAG0050 批 C）：缺失时降级到字面正则（安装破损下的 fail-safe，不静默放行）。
try:
    import agate_markers as _agate_markers
except Exception:
    _agate_markers = None

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

# TAG0050 批 A2（设计 §2.4）：回放模式。CI 逐提交回放时设 AGATE_REPLAY=1——
# 跳过所有会改动文件的修正步骤（只校验），且**不写** .gate-result.json / .gate-history.jsonl。
_AGATE_REPLAY = os.environ.get("AGATE_REPLAY") == "1"


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


def _judge_enabled(task_dir, phase=None):
    """judge 是否启用（TAG0020 P6.5 注入条件）。

    非 legacy 任务（TAG0050 A1）：由**契约**决定（快照 requires.judge），不读
    judge.enabled；legacy 任务照旧读 .state.yaml 的 judge.enabled。
    缺失/无 judge 块/解析失败 → False（历史任务全链跳过 P6.5，不要求 judge 产物）。
    """
    req = requirement_active(task_dir, "judge", phase or "P6")
    if req is not None:
        return bool(req)
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


# ---------- 账本与新目录（TAG0050 批 A1，设计 §2.3）----------
#
# 本步骤位于任何**追加写入之前**（2g.0 的 PAUSED 留痕 / 2h.1b 的 gate_run 之前），
# 且**每次提交都运行**，不依赖 .state.yaml 是否被暂存。覆盖规则：
#   ① 新目录必须有创建事件（改名而来的目录除外）；
#   ③ 账本只追加（HEAD 字节须是暂存字节的前缀）；
#   ④ 含创建/迁入事件的账本不可删除；
#   ⑤ 账本事件规则（check_ledger_events）；
#   ⑦ 每个有暂存文件的任务目录都做 PROD_TOUCHED 扫描；非 legacy 任务按被暂存产出
#      所属阶段重跑 gate。

LEDGER_FILENAME = "gate-events.jsonl"
# TAG0050 批 C（P2 §3.1 第 1 点，修复 F4 口径分叉）：安全门正则**取自标记单源**
# `agate_markers.pattern("PROD_TOUCHED")`（注册表 lead_variant 已改为 default），
# 不再自带字面副本。仅在单源库不可用（安装破损）时降级到字面正则（fail-safe）。
if _agate_markers is not None:
    _PROD_TOUCHED_RE = _agate_markers.pattern("PROD_TOUCHED")
else:
    _PROD_TOUCHED_RE = re.compile(r"^\s*-?\s*\[PROD_TOUCHED\]")
# 否定写法专门指引（P2 §3.1 第 4 点：靠指引而非改正则——否定写法继续阻断）。
_PROD_TOUCHED_GUIDANCE = (
    "      疑似否定写法：未触达生产请在主产出写 prod_touched: false，并删除正文中的标记\n"
)

# F-3 整改（cso）：dispatch-context 文件名形态（真实注入卡片的唯一合法载体）。
_DC_FILE_RE = re.compile(r"-dispatch-context-[^/]+\.md$")


def _expected_card_hash(phase):
    """当前阶段卡片（`agate-next-card.py` 输出）的期望 sha256；不可用 → None。

    与 2p 的卡片 hash 校验同源（同一 CLI + 同一归一化：CR 去除、尾换行去除）。
    """
    if not os.path.isfile(os.path.join(SCRIPT_DIR, "agate-next-card.py")):
        return None
    rc, out = _run_script_capture("agate-next-card.py", [phase], suppress_stderr=True)
    if rc != 0 or not out:
        return None
    return hashlib.sha256(out.replace("\r", "").rstrip("\n").encode("utf-8")).hexdigest()


def _card_block_verified(file_rel, block_lines, expected_hash):
    """CARD 块是否为**真实注入**的卡片块：文件名为 dispatch-context 且块内容 sha256 匹配。"""
    if not expected_hash or not _DC_FILE_RE.search(file_rel or ""):
        return False
    embedded = "\n".join(line.replace("\r", "") for line in block_lines)
    return hashlib.sha256(embedded.encode("utf-8")).hexdigest() == expected_hash


def _added_lines_excluding_real_cards(diff_raw, phase):
    """从 diff 新增行中剔除**真实注入**的 AGATE_CARD 块，返回其余新增行。

    F-3 整改（cso）：排除条件由「纯文本 START/END 区间」收紧为「真实注入的卡片块」——
    仅当文件名为 `*-dispatch-context-*.md` 且块内容 sha256 等于当前阶段卡片期望值时排除；
    **伪造 CARD 块 / 非 dispatch-context 文件里的块不排除**（块内行照常参与扫描）。
    未闭合的 START 视为普通行参与扫描（fail-safe，不静默放行）。
    """
    expected = _expected_card_hash(phase)
    current_file = ""
    in_card = False
    block = []
    added = []
    for raw_line in (diff_raw or "").splitlines():
        if raw_line.startswith("+++ b/"):
            current_file = raw_line[6:]
            in_card, block = False, []
            continue
        if not (len(raw_line) >= 2 and raw_line[0] == "+" and raw_line[1] != "+"):
            continue
        line = raw_line[1:]
        if in_card:
            if "<!-- AGATE_CARD_END -->" in line:
                in_card = False
                if _card_block_verified(current_file, block, expected):
                    block = []
                    continue
                added.extend(block)   # 非真实卡片块：块内行参与扫描
                block = []
            else:
                block.append(line)
            continue
        if "<!-- AGATE_CARD_START -->" in line:
            in_card = True
            block = []
            continue
        added.append(line)
    if in_card:
        added.extend(block)           # 未闭合 START：fail-safe 参与扫描
    return added


def _diff_name_status(repo_root):
    """`git diff --cached -M --name-status` → (entries, rename_dests)。

    entries 元素：改名 `("R", old, new)`；其余 `(status, path)`。
    rename_dests：改名目标路径集合（判断"新目录是否由改名而来"）。
    """
    entries = []
    rename_dests = set()
    rc, out = run_git(["diff", "--cached", "-M", "--name-status"], cwd=repo_root)
    if rc != 0:
        return entries, rename_dests
    for raw in out.splitlines():
        parts = raw.rstrip("\r").split("\t")
        if not parts or not parts[0]:
            continue
        status = parts[0]
        if status.startswith("R") and len(parts) >= 3:
            entries.append(("R", parts[1], parts[2]))
            rename_dests.add(parts[2])
        elif len(parts) >= 2:
            entries.append((status, parts[1]))
    return entries, rename_dests


def _head_has_path(repo_root, rel_path):
    """HEAD 树中是否存在该路径（前缀）下的已跟踪文件。"""
    rc, out = run_git(["ls-tree", "-r", "--name-only", "HEAD", "--", rel_path], cwd=repo_root)
    return rc == 0 and bool(out.strip())


def _dir_moved_away(repo_root, task_rel):
    """暂存后该任务目录在索引中是否已不存在（整个目录被改名带走）。

    `git ls-files` 读暂存区（索引）：`git mv <dir> <newdir>` 后源目录下的条目
    全部消失（返回空）⇒ 目录级改名；单文件改名/移走时源目录仍有 `.state.yaml`
    等条目 ⇒ 返回非空。该判据不依赖 git 的 rename 相似度检测，比 `R` 三元组稳健。
    """
    rc, out = run_git(["ls-files", "--", task_rel], cwd=repo_root)
    return rc == 0 and not out.strip()


def _is_task_dir_rename(repo_root, old_task_rel, dst_ledger_path):
    """账本改名是否属「整个任务目录被改名」（规则 1 的目录改名语义）。

    仅当改名目标仍是**某任务目录下的账本路径**、且**源任务目录在暂存后的索引中
    已不存在**（整个目录被 `git mv` 带走）时才豁免——此时账本随目录到新路径、
    仍属同一任务。否则（改名到同目录 `.bak`、移入别的任务目录、改名到子目录等）
    视同把账本移走 ⇒ 按删除判 ERROR（防止降回 legacy）。
    """
    if not dst_ledger_path.endswith("/" + LEDGER_FILENAME):
        return False
    return _dir_moved_away(repo_root, old_task_rel)


def _git_show(repo_root, spec):
    """`git show <spec>` 文本；失败返回 None。"""
    rc, out = run_git(["show", spec], cwd=repo_root)
    return out if rc == 0 else None


def _normalize_newlines(text):
    return (text or "").replace("\r\n", "\n").replace("\r", "\n")


def _parse_ledger_text(text):
    import json as _json
    out = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        try:
            ev = _json.loads(line)
        except Exception:
            continue
        if isinstance(ev, dict):
            out.append(ev)
    return out


def _ledger_has_origin(text):
    return any(ev.get("event") in ("task_created", "task_adopted")
               for ev in _parse_ledger_text(text))


def _task_dirs_with_staged(repo_root, tasks_dir, staged_all):
    """{task_rel: [staged paths]}：tasks 下含 .state.yaml 的直接子目录（有暂存文件）。"""
    tasks_rel = os.path.relpath(tasks_dir, repo_root).replace(os.sep, "/")
    prefix = tasks_rel + "/"
    grouped = {}
    for f in staged_all:
        if not f.startswith(prefix):
            continue
        rest = f[len(prefix):]
        if "/" not in rest:
            continue
        name = rest.split("/", 1)[0]
        grouped.setdefault(prefix + name, []).append(f)
    out = {}
    for task_rel in grouped:
        task_dir = os.path.join(repo_root, task_rel)
        if (os.path.isfile(os.path.join(task_dir, ".state.yaml"))
                or _head_has_path(repo_root, task_rel + "/.state.yaml")):
            out[task_rel] = grouped[task_rel]
    return out


def _check_ledgers_and_new_dirs(repo_root, tasks_dir, staged_all):
    """设计 §2.3 规则 1/3/4/5：新目录创建事件、账本只追加/不可删、事件规则。"""
    entries, rename_dests = _diff_name_status(repo_root)
    task_staged = _task_dirs_with_staged(repo_root, tasks_dir, staged_all)
    # 规则 4：含创建/迁入事件的账本被删除、截空或移走 → ERROR（防止降回 legacy）。
    # 覆盖 D（删除）与 R（改名）：`git mv gate-events.jsonl <非账本名>`（同目录 `.bak`）
    # 或移入**别的任务目录**同样使源任务失去账本 ⇒ 按删除判 ERROR。仅当**整个任务目录**
    # 被改名（账本随目录到新路径、仍属同一任务）才豁免——即规则 1 的目录改名语义
    # （见 `_is_task_dir_rename`）。
    for entry in entries:
        if entry[0] == "R":
            src_path, dst_path = entry[1], entry[2]
        elif entry[0] == "D":
            src_path, dst_path = entry[1], None
        else:
            continue
        if not src_path.endswith("/" + LEDGER_FILENAME):
            continue
        task_rel = src_path[: -len("/" + LEDGER_FILENAME)]
        if task_rel not in task_staged and not _head_has_path(repo_root, task_rel + "/.state.yaml"):
            continue
        if dst_path is not None and _is_task_dir_rename(repo_root, task_rel, dst_path):
            continue
        if _ledger_has_origin(_git_show(repo_root, "HEAD:" + src_path)):
            sys.stderr.write(
                f"GATE: 含创建/迁入事件的账本被删除/移走（{src_path}）——"
                "不得删除/截空/移走（防止降回 legacy）；迁移请用 agate-task-init.py\n")
            sys.exit(1)
    if not task_staged:
        return
    for task_rel in sorted(task_staged):
        task_dir = os.path.join(repo_root, task_rel)
        ledger_rel = task_rel + "/" + LEDGER_FILENAME
        # 规则 1：新目录必须有创建事件（账本由改名而来则沿用原任务）。
        # 例外：控制态（PAUSED/READY/DONE）不加叠加阻断——PAUSED 表示任务已被人工接管
        # （同 2g 段语义），且新建任务本应在 P0 登记；新建即在控制态的合成场景不适用本规则。
        phase = read_state_phase(os.path.join(task_dir, ".state.yaml"))
        if (phase not in ("PAUSED", "READY", "DONE")
                and not _head_has_path(repo_root, task_rel) and ledger_rel not in rename_dests):
            events = read_ledger_events(task_dir)
            if not (events and events[0].get("event") == "task_created"):
                task_id = os.path.basename(task_rel).split("-", 1)[0]
                sys.stderr.write(
                    f"GATE: 新增任务目录 {task_rel} 的账本第 1 行不是 task_created（无创建事件）\n")
                sys.stderr.write(
                    f"      修复：agate-task-init.py {task_id} … 或 agate-task-init.py --existing {task_rel}\n")
                sys.exit(1)
            # 规则 2：新任务的等级必须是当前等级（设计 §2.3 规则 2——**只在本地、仅新任务**判；
            # 不在 check_ledger_events / CI 路径判，避免协议升级后追溯存量非 legacy 任务）。
            lvl = events[0].get("contract_level")
            cur = current_level()
            if cur is not None and lvl != cur:
                task_id = os.path.basename(task_rel).split("-", 1)[0]
                sys.stderr.write(
                    f"GATE: 新增任务目录 {task_rel} 的等级 {lvl!r} ≠ 当前等级 {cur}"
                    "（新任务必须登记当前等级，设计 §2.3 规则 2）\n")
                sys.stderr.write(
                    f"      修复：agate-task-init.py {task_id} … 或 agate-task-init.py --existing {task_rel}\n")
                sys.exit(1)
        # 规则 3：账本只追加（HEAD 字节须是暂存字节的前缀）
        if ledger_rel in task_staged[task_rel]:
            head_text = _git_show(repo_root, "HEAD:" + ledger_rel)
            idx_text = _git_show(repo_root, ":" + ledger_rel)
            if (head_text is not None and idx_text is not None
                    and not _normalize_newlines(idx_text).startswith(_normalize_newlines(head_text))):
                sys.stderr.write(
                    f"GATE: 账本 {ledger_rel} 非只追加（HEAD 内容不是暂存内容的前缀）——禁止改写历史行\n")
                sys.exit(1)
            # 规则 5：事件规则
            errors = check_ledger_events(task_dir)
            if errors:
                sys.stderr.write(f"GATE: 账本事件规则违反（{ledger_rel}）：\n")
                for msg in errors:
                    sys.stderr.write(f"  - {msg}\n")
                sys.exit(1)


def _head_phase(repo_root, task_rel):
    """读 HEAD 版 `.state.yaml` 的 phase（失败回退工作区版）。"""
    text = _git_show(repo_root, "HEAD:" + task_rel + "/.state.yaml")
    if text is not None:
        try:
            import yaml
            data = yaml.safe_load(text)
            if isinstance(data, dict) and isinstance(data.get("phase"), str):
                return data["phase"]
        except Exception:
            pass
    return read_state_phase(os.path.join(repo_root, task_rel, ".state.yaml"))


def _phase_order(phase):
    """P0..P8 → 0..8；控制态/未知 → None。"""
    m = re.match(r"^P([0-8])$", phase or "")
    return int(m.group(1)) if m else None


def _staged_output_phases(repo_root, task_rel):
    """task_rel 下暂存的阶段产出（`P[0-8]-*.md`）所属阶段集合（升序）。"""
    prefix = task_rel + "/"
    phases = set()
    for f in _staged_name_only():
        if not f.startswith(prefix) or not _P_OUTPUT_RE.search(f):
            continue
        p = _phase_num(f)
        if p:
            phases.add(p)
    return sorted(phases)


def _rerun_gates_for_staged_outputs(repo_root, task_rel, task_dir):
    """设计 §2.3 规则 7 后半：非 legacy 任务暂存了阶段产出、却没改 phase 时，
    按**被暂存产出所属的阶段**重跑该阶段的 gate（该阶段须不晚于 HEAD 的 phase；
    HEAD 为 READY/DONE 时同样执行）。任一重跑 exit 1 → 中止 commit。

    legacy 任务不重跑（走旧逻辑）；PAUSED 任务已被人工接管，不叠加阻断。
    """
    if task_level(task_dir) is None:
        return
    head_phase = _head_phase(repo_root, task_rel)
    if head_phase == "PAUSED":
        return
    control = head_phase in ("READY", "DONE")
    head_order = _phase_order(head_phase)
    for out_phase in _staged_output_phases(repo_root, task_rel):
        out_order = _phase_order(out_phase)
        if out_order is None:
            continue
        if not control and (head_order is None or out_order > head_order):
            continue  # 产出阶段晚于 HEAD：属"提前产出"，由 2f WARNING 处理，不重跑
        rc = _run_script_rc("check-gate.py", [out_phase, task_dir])
        if rc == 1:
            sys.stderr.write(
                f"GATE: 非 legacy 任务暂存了 {out_phase} 产出但未改 phase（{task_rel}）——"
                f"按被暂存产出所属阶段重跑 {out_phase} gate 未通过（设计 §2.3 规则 7）\n")
            sys.exit(1)


# 声明文件（设计 §3.6 / 快照 declaration_files；R2 单源）。仅快照不可用时降级到历史四类。
_FALLBACK_DECLARATION_FILES = (
    "P1-requirements.md", "P2-design.md", "P6-acceptance.md", "P7-consistency.md",
)


def _declaration_files(task_dir):
    """声明文件集合：快照 `declaration_files`（按任务等级，回退协议当前等级）；
    快照不可用 → 历史四类文件（安装破损降级）。

    L2 口径说明：本函数与 `_primary_output_for` 取**任务级（最新）快照**——它们回答的是
    「结构面：哪些文件/字段存在」（随任务最新等级走）；而 `_check_prod_touched_primary`
    的门控 `requirement_active(..., phase)` 用 **level_at_phase**——它回答的是「时间面：
    该要求在本阶段是否已生效」（随阶段走）。两者语义不同，**刻意不统一**（设计 §2.5）。
    """
    lvl = task_level(task_dir)
    if lvl is None:
        lvl = current_level(__file__)
    try:
        contract = load_contract(lvl, __file__) if lvl else {}
    except Exception:
        contract = {}
    decl = contract.get("declaration_files") if isinstance(contract, dict) else None
    if isinstance(decl, (list, tuple)) and decl:
        return tuple(str(x) for x in decl)
    return _FALLBACK_DECLARATION_FILES


def _is_declaration_path(file_path, task_dir):
    """file_path 是否命中快照 `declaration_files`（glob 模式；GAP-8 闭合）。

    cso F-2：与 `check-frontmatter._is_declaration_file` 同口径，统一到
    `agate_common.match_declaration_file`（glob 语义单源，含 `**` 递归/零层）。
    """
    return match_declaration_file(file_path, task_dir, _declaration_files(task_dir))


def _primary_output_for(task_dir, phase):
    """当前阶段的主产出相对路径（快照 primary_outputs；不可用 → None）。"""
    lvl = task_level(task_dir)
    if lvl is None:
        return None
    try:
        contract = load_contract(lvl, __file__)
    except Exception:
        contract = {}
    outputs = contract.get("primary_outputs") if isinstance(contract, dict) else None
    if not isinstance(outputs, dict):
        return None
    return outputs.get(phase)


def _check_prod_touched_primary(task_dir, phase):
    """TAG0050 批 C（设计 §4）：非 legacy 任务主产出 frontmatter 的 `prod_touched`。

    - 缺字段 → ERROR（附修复命令）
    - 值为 true 且当前不在 PAUSED → 中止提交
    返回 None（不适用/通过）；命中则 sys.exit(1)。
    """
    if requirement_active(task_dir, "prod_touched", phase) is not True:
        return
    primary = _primary_output_for(task_dir, phase)
    if not primary:
        return
    out_file = os.path.join(task_dir, primary)
    if not os.path.isfile(out_file):
        return
    try:
        with open(out_file, encoding="utf-8", errors="replace") as fh:
            fm, _body = split_frontmatter(fh.read().replace("\r\n", "\n"))
    except Exception:
        fm = None
    fm = fm if isinstance(fm, dict) else {}
    # TAG0050 批 C（设计 §4 / BDD-52）：主产出缺 `prod_touched` → ERROR + 修复命令。
    # （「主产出」按快照 `primary_outputs` 判定；非 legacy 任务必填。）
    if "prod_touched" not in fm:
        sys.stderr.write(
            f"GATE: 主产出 {primary} 缺 prod_touched 字段（非 legacy 任务必填，设计 §4）\n"
            f"      修复命令: FILE={out_file} agate-md-field-set.py set prod_touched false\n"
            f"      （若未触达生产；若已触达请保持 true 并进入 PAUSED）\n"
        )
        sys.exit(1)
    if fm.get("prod_touched") is True and phase != "PAUSED":
        sys.stderr.write(
            f"GATE: 主产出 {primary} 声明 prod_touched: true 且当前不在 PAUSED（{phase}），commit 中止\n"
            f"      修复命令: FILE={out_file} agate-md-field-set.py set prod_touched false\n"
            f"      （若未触达生产；若已触达请进入 PAUSED 而非改写字段）\n"
        )
        sys.exit(1)


def _scan_prod_touched_and_rerun(repo_root, tasks_dir, staged_all, state_files_rel):
    """设计 §2.3 规则 7 的 PROD_TOUCHED 全局面：每个有暂存文件的任务目录都做
    PROD_TOUCHED 扫描（不论是否暂存 .state.yaml），安全门不再依赖"是否改了 phase"。

    并实现规则 7 后半（`_rerun_gates_for_staged_outputs`）：非 legacy 任务按被暂存产出
    所属阶段重跑 gate。两半都不依赖 `.state.yaml` 是否被暂存。
    """
    task_staged = _task_dirs_with_staged(repo_root, tasks_dir, staged_all)
    for task_rel in sorted(task_staged):
        state_rel = task_rel + "/.state.yaml"
        # 有暂存**且工作区仍存在**的 .state.yaml：PROD_TOUCHED 由主循环 2g.0 处理。
        # `.state.yaml` 以**删除**方式暂存时（`git rm`）工作区文件不存在、主循环
        # `os.path.isfile` 为假而跳过 ⇒ 这里**不得**一并跳过，否则该任务目录完全不被
        # PROD_TOUCHED 扫描（评审 F-3：两条路径互相让路的安全门洞）。
        if state_rel in state_files_rel and os.path.isfile(os.path.join(repo_root, state_rel)):
            continue
        task_dir = os.path.join(repo_root, task_rel)
        state_file = os.path.join(task_dir, ".state.yaml")
        phase = read_state_phase(state_file)
        _check_prod_touched_primary(task_dir, phase)
        _rerun_gates_for_staged_outputs(repo_root, task_rel, task_dir)
        _rc, diff_raw = run_git(["diff", "--cached", "-M", "--", task_rel], cwd=repo_root)
        added = _added_lines_excluding_real_cards(diff_raw, phase)
        if any(_PROD_TOUCHED_RE.match(ln) for ln in added):
            task_id = read_state_task_id(state_file)
            if phase == "PAUSED":
                append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})
            else:
                sys.stderr.write(
                    f"GATE: [PROD_TOUCHED] 检测到生产环境接触（{task_id}），commit 中止\n")
                sys.stderr.write(_PROD_TOUCHED_GUIDANCE)
                sys.exit(1)


# ---------- 主流程 ----------


def _run_project_local_hook(repo_root):
    """**项目本地 hook 扩展点**（中立机制）：`<git-common-dir>/hooks/pre-commit-local`
    存在且**可执行** ⇒ 先跑它；**非 0 即中止本次提交**。返回其退出码（无则 0）。

    **为什么不把策略写进协议**：协议**不得假设项目分支/流程**——有的项目允许直接提交并推送到
    `main`，有的用 `master` / `develop` / 自定义默认分支，有的要求先建分支。而「禁止直提 main」
    这类是**项目策略**，应当写在**项目自己的** `pre-commit-local` 里。协议只负责**给它机会跑**：
    内容完全由项目决定（不写 = 无策略，行为与从前逐字节一致）。

    解析用 `git rev-parse --git-path hooks`（尊重 `core.hooksPath` 与共享 git 目录）；找不到 git /
    hook 缺失 / 不可执行 ⇒ **跳过**（不阻断）。
    """
    # 复用**单源** `agate_common.git_hooks_dir`（ADR-014）——它已正确处理：
    # 链接 worktree（`.git` 是文件 ⇒ 共享 hooks 目录）与 `core.hooksPath`（相对路径按 cwd 解析）。
    # 此前本处自己再解析一遍，属重复实现（SELF-GATE r1 指出）。
    try:
        hooks_dir = git_hooks_dir(repo_root)
    except Exception:
        return 0
    if not hooks_dir:
        return 0
    path = os.path.join(hooks_dir, "pre-commit-local")
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        return 0
    try:
        return subprocess.run([path], cwd=repo_root).returncode
    except OSError:
        return 0


def main():
    # REPO_ROOT = 当前 git 仓库根（项目仓库或 agate 仓库本身）
    # realpath -m 归一（Git for Windows 的 --show-toplevel 返回 C:/...，统一归一）
    rc, out = run_git(["rev-parse", "--show-toplevel"])
    repo_root = out.strip() if rc == 0 and out.strip() else os.getcwd()
    repo_root = os.path.realpath(repo_root)

    # 0. 项目本地 hook 扩展点（中立）：项目自己的 pre-commit-local 存在则可执行先跑，非 0 即中止。
    #    协议不内置任何分支/流程策略（有的项目允许直提 main）——策略留在项目。
    if _run_project_local_hook(repo_root) != 0:
        sys.stderr.write(
            "GATE LOCAL: 项目本地 pre-commit-local 未通过 ⇒ 本次提交中止\n"
            "  （该策略由项目自定义；见 <git-common-dir>/hooks/pre-commit-local）\n"
        )
        sys.exit(1)

    # AGATE_ROOT = 协议本体路径（env 优先 → 脚本真实路径上溯 → 复制模式 .agate-root 恢复）
    resolve_agate_root(os.path.abspath(__file__))

    # TAG0050 G3（GAP-6 / D3）：标记本进程为 pre-commit 上下文，供 check-gate.py 的
    # P6 结构化判据 D3 启用「证据须已跟踪或已暂存」附加检查（直接调 check-gate 时不做）。
    os.environ["AGATE_PRECOMMIT_GATE"] = "1"

    # 工作区路径单点解析（TAG0003 v2.0）：.agate.env > env AGATE_TASKS_DIR > 默认
    # agate-workspace/。resolve_workspace 等价 agate-workspace-resolve.sh 的 source 语义。
    _workspace, tasks_dir = resolve_workspace(repo_root)

    # 1. 收集所有暂存的 .state.yaml 文件（根 + 任务级）
    staged_all = _staged_name_only()
    state_files = [
        os.path.join(repo_root, f) for f in staged_all if f.endswith(_STATE_YAML_SUFFIX)
    ]

    # 1.1 账本与新目录（TAG0050 批 A1，设计 §2.3）——位于任何追加写入之前，每次提交都跑。
    state_files_rel = [f for f in staged_all if f.endswith(_STATE_YAML_SUFFIX)]
    _check_ledgers_and_new_dirs(repo_root, tasks_dir, staged_all)
    _scan_prod_touched_and_rerun(repo_root, tasks_dir, staged_all, state_files_rel)

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
        # X2（TAG0042 批0）：phase 取**暂存区**那份，与 2b 的 `--cached` 差分同源——
        # 否则「索引里 phase=P4」+「工作区已改成 P5」时会按 P5 跑 gate，判错对象。
        # 此处 `state_file` 来自暂存清单 ⇒ 回退分支不可达，无需提示（helper 注释有说明）。
        phase, _ = read_staged_state_phase(state_file, repo_root)
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

        # 2g.0 PROD_TOUCHED 检测（P1.2 / TAG0042 批0 X1）——**所有阶段都扫**
        #
        # ⚠️ 本段原先位于 `# 2g. 跳过非 gate 阶段` 的 continue **之后** ⇒
        #    phase ∈ PAUSED/READY/DONE 的收尾提交（正是"准备发布"那个时点）**完全不扫**，
        #    生产安全门在该阶段失效（2026-10-04 实测复现）。
        #    ⇒ 上移到 continue **之前**：所有阶段都扫；**PAUSED 只扫描不阻断**（见下）。
        #    粒度 = 「2g.1 整体上移」，**不是删掉 continue**（后者会连带跳过
        #    frontmatter schema / P6 归一化 / gate / write_gate_result / append_event 等）。
        _prod_touched_hit = False
        if any(f.startswith(prefix) for f in _staged_name_only()):
            _rc_diff, diff_raw = run_git(["diff", "--cached", "--", task_rel])
            diff_added = _added_lines_excluding_real_cards(diff_raw, phase)
            if any(_PROD_TOUCHED_RE.match(ln) for ln in diff_added):
                _prod_touched_hit = True
                if phase != "PAUSED":
                    sys.stderr.write(
                        f"GATE: [PROD_TOUCHED] 检测到生产环境接触（{task_id}），commit 中止\n")
                    sys.stderr.write(_PROD_TOUCHED_GUIDANCE)
                    sys.exit(1)
            if (phase != "PAUSED"
                    and any(re.match(r"^\s*-?\s*\[PROD_TOUCHED\]\s*$", ln) for ln in diff_added)):
                sys.stderr.write(
                    f"GATE: 不合规的 PROD_TOUCHED 标记格式（{task_id}），须用行首 [PROD_TOUCHED] 或 [PROD_NOT_TOUCHED] 声明\n")
                sys.exit(1)

        # 2g.3 主产出 prod_touched 必填/中止（TAG0050 批 C，设计 §4）
        _check_prod_touched_primary(task_dir, phase)

        # 2h.1c 状态转移事件（TAG0050 A3，设计 §2.7）：**前移到 2g 的 continue 之前**，
        # 使进入 PAUSED/READY/DONE 的转换也被记录（现状 2g 在 2h.1c 之前 continue ⇒
        # 这些转换事件从不写入）。`.state.yaml` 仍是权威状态源，事件只记录不改写。
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

        # 2h.1d 一并暂存账本（TAG0042 BDD-12；TAG0050 A3 前移）：把本 hook 已追加的
        # state_transition（进入 PAUSED/READY/DONE 的转换在此后的 2g `continue` 之前写入）
        # `git add`，随本次提交入库。**失败可见**（TAG0050 A3 派生事项②）：检查返回码，
        # 失败给 WARNING。⚠️ 普通阶段下 gate_run（2h.1b）在本步之后才追加，故另有 2h.1e
        # 再次 add 覆盖它（否则 gate_run 不进本次 commit，评审 A1-2）。
        if os.path.isfile(os.path.join(task_dir, "gate-events.jsonl")):
            _rc_add, _ = run_git(["add", os.path.join(task_dir, "gate-events.jsonl")])
            if _rc_add != 0:
                sys.stderr.write(
                    f"GATE WARNING: 账本 {os.path.join(task_dir, 'gate-events.jsonl')} "
                    f"git add 失败（rc={_rc_add}）——本事件可能未随本次提交入库\n")

        # 2g. 跳过非 gate 阶段
        if phase in ("PAUSED", "READY", "DONE"):
            # PAUSED 的特殊语义（设计 §X1）：`state-machine.md:98` 定义
            # `任意阶段 --[出现 PROD_TOUCHED]--> PAUSED` ⇒ 任务已因生产接触被人工接管，
            # 不该再叠加阻断；**但必须留痕**——否则等于"只打印到 stderr、无消费方"。
            if phase == "PAUSED" and _prod_touched_hit:
                sys.stderr.write(
                    f"GATE WARNING: PAUSED 提交扫描到 [PROD_TOUCHED]（{task_id}）——"
                    "本阶段只扫描不阻断（任务已被人工接管）；已记入账本\n")
                try:
                    append_event(task_dir, {"event": "prod_touched_in_paused", "task_id": task_id})
                except Exception:
                    sys.stderr.write("GATE WARNING: 账本留痕失败（不阻断）\n")
            continue
        if not os.path.isdir(task_dir):
            continue

        # 2g.2 frontmatter schema 校验（P2-design.md §3.1.3，BDD-8 挂载点）
        # 与 2a 同机制：扫描本任务暂存的 P1/P2/P6/P7 产出文件，逐个跑 check-frontmatter
        if os.path.isfile(os.path.join(SCRIPT_DIR, "check-frontmatter.py")):
            # GAP-8 闭合（2026-10-08）：`declaration_files` 为 glob 模式——遍历该任务下**已暂存**
            # 且命中声明模式的产出文件逐个校验（不再按字面文件名拼接）。
            for _staged_name in _staged_name_only():
                if not _staged_name.startswith(task_rel + "/"):
                    continue
                _abs = os.path.join(repo_root, _staged_name)
                if not os.path.isfile(_abs):
                    continue
                if not _is_declaration_path(_abs, task_dir):
                    continue
                if _run_script_rc("check-frontmatter.py", [_abs]) != 0:
                    sys.exit(1)

        # 2h. P6 格式自动归一化（①）——verifier 产出后、gate 前。
        # TAG0050 批 D（设计 §5.1）：**非 legacy 任务跳过** check-p6-format（包括 2h 段）——
        # P6 走结构化 results 判据 D1–D10，不再依赖正文格式归一化。
        # 回放模式（AGATE_REPLAY=1）跳过会改文件的修正步骤，只校验（设计 §2.4）。
        if (not _AGATE_REPLAY and phase == "P6" and task_level(task_dir) is None
                and os.path.isfile(os.path.join(task_dir, "P6-acceptance.md"))):
            _run_script_rc("check-p6-format.py", ["--fix", os.path.join(task_dir, "P6-acceptance.md")])
            run_git(["add", os.path.join(task_dir, "P6-acceptance.md")])

        # 2h.1 运行 gate（P1.1）——2>&1 合并捕获（sh $() 语义，剥尾换行）
        _gc_rc, gate_output = _run_script_capture(
            "check-gate.py", [phase, task_dir, old_phase], merge=True)
        gate_exit = _gc_rc
        gate_output = gate_output.rstrip("\n")

        # 2h.1 写 gate 结果（供 CI backstop 检测 --no-verify 绕过）。
        # 回放模式不写 .gate-result.json / .gate-history.jsonl（设计 §2.4）。
        if not _AGATE_REPLAY:
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

        # 2h.1e 再次暂存账本：2h.1d 的 `git add` 在 gate_run 之前，普通阶段下 gate_run
        # 于此后追加 ⇒ 需再 add 一次，确保 `gate_run` 随本次提交入库（TAG0042 BDD-12 /
        # 设计 §8 第 6 项；评审 A1-2）。PAUSED/READY/DONE 在 2g 处 `continue`，不走本步，
        # 其 state_transition 已由 2h.1d 覆盖。
        if os.path.isfile(os.path.join(task_dir, "gate-events.jsonl")):
            _rc_add2, _ = run_git(["add", os.path.join(task_dir, "gate-events.jsonl")])
            if _rc_add2 != 0:
                sys.stderr.write(
                    f"GATE WARNING: 账本 {os.path.join(task_dir, 'gate-events.jsonl')} "
                    f"git add 失败（rc={_rc_add2}）——gate_run 可能未随本次提交入库\n")

        # 2i. P6 客观行为审计（P2.1/P2.10）
        if gate_exit != 1 and _run_script_rc("check-p6-provenance.py", [task_dir]) == 1:
            sys.exit(1)

        # 2i.1 P6.5 judge 复核 + 事件账本审计（TAG0020，commit-time 硬边界；P2 §3.5 候选 1）
        # judge 启用（.state.yaml judge.enabled == true）且 verdict 已产出 → 依次调
        # check-judge-verdict + check-events，任一 exit 1 → 阻断 commit。
        # enforcement 与 commit 位置解耦（注入条件不依赖 phase 值）：verdict 落库的
        # 任何后续 commit（含 P7 commit）都会重验；历史任务（无 judge.enabled）天然跳过。
        if (gate_exit != 1
                and _judge_enabled(task_dir, phase)
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

    # 2y. dispatch-context 占位符存在性校验（RM-AG0104 / DEBT0057）：暂存
    # `{Pn}-dispatch-context-*.md` 时须含 `AGATE_CARD_START` / `AGATE_CARD_END` 占位符对，
    # 否则 `agate-inject-card.py` 无法注入卡片。原缺陷：漏写占位符**无任何 gate 拦截**，
    # 只靠 inject 早退**事后**暴露（且早退使其余文件静默不注入，见 RM-AG0104 主项）。
    for _rel in _staged_name_only():
        _base = os.path.basename(_rel.replace("\\", "/"))
        if re.match(r"^P[0-9]-dispatch-context.*\.md$", _base):
            _abs = os.path.join(repo_root, _rel)
            if os.path.isfile(_abs):
                with open(_abs, encoding="utf-8", errors="replace") as _fh:
                    _txt = _fh.read()
                # **判据单源**（RM-AG0104 评审 A1/r2：与 `agate-card-inject.py` 共用
                # `agate_common.AGATE_CARD_PLACEHOLDER_RE`——校验口径 == 注入口径，既不放行
                # 「注入会失败」的文件（漏放），也不阻断「注入能成功」的文件（误伤）。
                # 原用行级 `^…$` 与 inject 的 DOTALL 正则**口径不一致**，两向都会分歧。）
                if not re.search(AGATE_CARD_PLACEHOLDER_RE, _txt, flags=re.DOTALL):
                    sys.stderr.write(
                        f"GATE: {_rel} 缺 AGATE_CARD_START/END **占位符行**"
                        "（RM-AG0104 / DEBT0057）——agate-inject-card.py 无法注入卡片；"
                        "请补独占一行的占位符对后重试\n")
                    sys.exit(1)

    # 2z. 技术债登记 schema 校验（RM-AG0088 / DEBT0033）——**循环外**（对任何提交都生效）：
    # `tech-debt.md` 被**暂存**时跑 `check-debt.py <file>`，exit 1 → 阻断 commit。
    # 原先 `check-debt.py` **未挂任何 gate/CI**（只被 2026-09-29 的「逐条实测」批手工调用）。
    # ⚠️ 必须置于 `for state_file in state_files:` 循环**之外**——循环体内且在 PAUSED/READY/DONE
    # 的 `continue` 之后 ⇒ 只对「同批暂存 active 阶段 `.state.yaml`」生效，对**纯 `tech-debt.md`
    # 提交完全失效**（SELF-GATE 评审 r1 实测证伪首版放置：仅暂存非法 tech-debt.md → exit 0）。
    # 脚本缺失 → fail-open 跳过（旧版协议 / 测试 fake 根未复制该脚本）。
    if os.path.isfile(os.path.join(SCRIPT_DIR, "check-debt.py")):
        for _rel in _staged_name_only():
            _norm = "/" + _rel.replace("\\", "/")
            if _norm.endswith("/debt/tech-debt.md"):
                _abs = os.path.join(repo_root, _rel)
                if os.path.isfile(_abs) and _run_script_rc("check-debt.py", [_abs]) == 1:
                    sys.stderr.write(
                        "GATE: 技术债登记 schema 非法（check-debt.py exit 1）——阻断 commit"
                        "（RM-AG0088 / DEBT0033）\n")
                    sys.exit(1)

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
