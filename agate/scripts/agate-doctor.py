#!/usr/bin/env python3
"""agate-doctor.py — 项目接入状态诊断（TAG0042 批 5，BDD-17）

诊断项目接入 agate 的状态，逐维度给出**客观值**，并对异常项给出**可执行修复指引**：

  1. 声明文件：项目根 `agate.config.yaml`（经 `agate_common.read_project_config`
     **唯一读取函数**取值，不另写第二处声明解析——P2-design §4.1）。
  2. git hook：`pre-commit` / `commit-msg` / `pre-push` 是否**存在且生效**。查的是
     **git 实际会执行的目录**（`agate_common.git_hooks_dir`，覆盖链接 worktree 与
     `core.hooksPath`）里的**效力**，不是 `<repo>/.git/hooks` 里的存在性。
  3. 版本解析：报 **gate 实际会用的那个** `AGATE_ROOT`——以 `resolve_hook_root()`（gate 入口
     `resolve-entry.py` 走的同一个函数）为准，并附上 `resolve_version_root()` 的解析链结论
     （版本 / 原因 / warning）；声明未安装、格式非法时把 warning 摊到台面上。
  4. 账本完整性：任务目录 `gate-events.jsonl` 的 append-only 哈希链（`prev_hash`）。

**诊断对象是「效力」不是「存在性」**（2026-11-26 实测修正）：本工具曾在
「三个 hook 都在位但全部不可执行（git 会忽略它们并让 commit 照常成功）」与「链接 worktree 里
hook 明明生效却报未接入」两种情形下给出**与事实相反**的结论。失效模式相同：把「我以为的
位置上有个文件」当成「gate 在这里生效」。位置一律问 git（`--git-path hooks`），版本一律问
gate 真正走的那条解析入口，效力一律判执行位。

**退出码固定**：诊断正常完成 → rc=0（诊断工具报告问题 ≠ 自身执行失败，BDD-17）。
平台无关：显式 utf-8；无系统临时目录字面量；执行位判定仅在 POSIX 生效
（Windows 无该语义，git 也不据它决定是否忽略 hook）。Python 3.8+。
"""

import contextlib
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_AGATE_ROOT = _SCRIPT_DIR.parent
_HOOK_NAMES = ("pre-commit", "commit-msg", "pre-push")


def _exc_note(exc):
    """异常的可读描述。

    `agate_common` 依赖不满足时用 `sys.exit()` 在 import 阶段中止（当前实现是缺 pyyaml）。
    `SystemExit` 的 `str()` 只有退出码（"1"），直接拼进状态行等于什么都没说，故还原成
    可行动的描述。

    **措辞刻意不写「唯一一处 sys.exit」「一定缺 pyyaml」**：那是随 `agate_common` 实现变化
    的事实（今天成立，加一处 `sys.exit` 就变假），写进诊断文案会把一个会漂移的断言固化成
    读者看到的信息。只说到「它在 import 阶段中止、多半是依赖没装」，并给出可行动的下一步。
    """
    if isinstance(exc, SystemExit):
        return f"agate_common 在 import 阶段中止（code={exc.code}；通常是依赖未安装，最常见是 pyyaml）"
    return str(exc)


def _force_utf8():
    for stream in (sys.stdout, sys.stderr):
        with contextlib.suppress(AttributeError, ValueError):
            stream.reconfigure(encoding="utf-8", errors="replace")


def _genesis_hash():
    return hashlib.sha256(b"").hexdigest()


def _tasks_dir(project_root):
    """解析任务目录。返回 (tasks_dir 或 None, 失败原因或 None)。

    **「解析不出来」与「解析成功但没有任务」必须分开**（2026-11-26 二轮评审指出）：
    原实现失败时统一返回 None，而账本维度把 None 当成「无账本可审计」判 **OK**——
    等于 `agate_common` 挂掉时账本审计根本没跑，却报绿。这正是本批要消灭的那类假绿，
    不能由本批自己的修复引入。
    """
    try:
        import agate_common
        _workspace, tasks_dir = agate_common.resolve_workspace(str(project_root))
        return Path(tasks_dir), None
    except (Exception, SystemExit) as exc:
        return None, _exc_note(exc)


def _diagnose_declaration(project_root):
    """维度①：声明文件。返回 (ok, 状态行, 修复指引或 None)。"""
    try:
        import agate_common
        cfg = agate_common.read_project_config(str(project_root))
    except (Exception, SystemExit) as exc:
        # 指引必须按**真因**分流：`agate_common` 不可用（如缺 pyyaml）时让人去查
        # agate.config.yaml 的语法是彻头彻尾的误指路（二轮评审指出）。
        if isinstance(exc, SystemExit):
            return False, f"声明文件: 无法读取（{_exc_note(exc)}）", \
                "先让 agate_common 可用（缺 pyyaml 时 pip install pyyaml）后重跑"
        return False, f"声明文件: 读取失败（{_exc_note(exc)}）", \
            f"检查 {project_root / 'agate.config.yaml'} 的 YAML 语法"
    if cfg.get("present"):
        language = (cfg.get("project") or {}).get("language", "") or "unknown"
        return True, f"声明文件: 存在（agate.config.yaml，language={language}）", None

    # 「文件不存在」与「文件在但读不懂」是**两种不同的病**，修法也不同（本批主题：
    # 报的必须是实际状态）。`read_project_config` 已经用 `parse_error` 区分了后者，
    # 早先这里一律报「缺失」，会让一个被改坏的声明文件看起来像从未创建过
    # ——而按「缺失」给出的 `agate-config.py init` 会覆盖掉用户原有内容。
    # YAML 的 parse_error 是多行的（带 caret 定位），压成一行首句——状态行要能一眼读完，
    # 完整信息可用 `agate-config.py validate` 复现。
    parse_error = " ".join((cfg.get("parse_error") or "").split())
    if parse_error:
        return False, f"声明文件: 存在但无法解析（agate.config.yaml；{parse_error}）", \
            f"修正 {project_root / 'agate.config.yaml'} 的 YAML 语法（**不要**重跑 init，会覆盖现有内容）；" \
            f"或用 {sys.executable} {_SCRIPT_DIR / 'agate-config.py'} validate 定位"
    return False, "声明文件: 缺失（agate.config.yaml 不存在）", \
        f"运行 {sys.executable} {_SCRIPT_DIR / 'agate-config.py'} init 生成声明"


def _diagnose_hooks(project_root):
    """维度②：git hook **效力**。返回 (ok, 状态行, 修复指引或 None)。

    三件事都不能自己猜，必须问 git / 判执行位（2026-11-26 实测修正）：

    * **目录**：问 `git rev-parse --git-path hooks`（`agate_common.git_hooks_dir` 单一实现）。
      写死 `<repo>/.git/hooks` 在两类真实布局下是错的——链接 worktree 的 `.git` 是**文件**
      （hooks 共享主 checkout），`core.hooksPath` 可把 hooks 指到任何目录。两处都由该函数覆盖。
    * **存在**：`is_file()` 之外还要判 `is_symlink()`——软链断链时 `is_file()` 为 False，
      但报「缺失」会掩盖真实原因（应报断链）。
    * **效力**：POSIX 下无执行位的 hook 被 git **静默忽略且 exit 0**（本仓实测；同一失效
      模式在复制模式安装时踩过两次，两次都只修了产生端，消费端无人检查）。故「在位」不等于
      「生效」，须单独判执行位并单独报。
    """
    # **目录来源：优先 agate_common，失败则直接问 git**（三轮评审 A2 指出）。
    # `git rev-parse --git-path hooks` 是**纯 git 查询，不需要 pyyaml** —— 所以
    # 「agate_common 不可用（缺 pyyaml）」根本不构成「无法确认 hooks 目录」。
    # 早先在这种情况下回退到写死的 `<repo>/.git/hooks`，等于在一个**能问到答案**的场景里
    # 主动去猜——那正是本批要消灭的那类缺陷（猜出来的目录 + core.hooksPath 覆盖 = 假绿）。
    hooks_dir = None
    hooks_dir_source = ""
    try:
        import agate_common
        hooks_dir = Path(agate_common.git_hooks_dir(str(project_root)))
        hooks_dir_source = "git rev-parse --git-path hooks（经 agate_common）"
    except (Exception, SystemExit) as exc:
        note = _exc_note(exc)
        try:
            proc = subprocess.run(
                ["git", "rev-parse", "--git-path", "hooks"],
                cwd=str(project_root), capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=30,
            )
            rel = proc.stdout.strip() if proc.returncode == 0 else ""
            if rel:
                hooks_dir = Path(os.path.normpath(os.path.join(str(project_root), rel)))
                hooks_dir_source = f"git rev-parse --git-path hooks（直调；agate_common 不可用：{note}）"
        except (OSError, subprocess.SubprocessError):
            hooks_dir = None
    if hooks_dir is None:
        # 走到这里说明**连 git 都问不到**（非仓库 / git 不在 PATH）——此时如实说"问不到"，
        # 既不用猜的路径冒充答案，也不假装能给出结论。
        return False, "hook: 无法确定 hooks 目录（git rev-parse --git-path hooks 失败；非 git 仓库或 git 不可用）", \
            "确认项目是 git 仓库、且 git 在 PATH 上；再运行 agate-setup.py 安装 hook"
    # agate_common 不可用不影响本维度其余判断（执行位 / 断链 / 在位都不需要它），
    # 但仍记住它——修复建议里不能推荐同样跑不起来的 agate-setup.py。
    hooks_dir_fallback = "agate_common 不可用" in hooks_dir_source
    if not hooks_dir.is_dir():
        fix = ("先让 agate_common 可用（缺 pyyaml 时 pip install pyyaml）后重跑"
               if hooks_dir_fallback else
               "确认项目为 git 仓库；再运行 agate-setup.py 安装 hook")
        # 只陈述事实（这个目录不存在），不替读者推断原因：「非 git 仓库」在链接 worktree 里
        # 是**假**的（`.git` 是文件、仓库完全正常），把猜测写进状态行就是又一处「报的不是实际状态」。
        return False, f"hook: hooks 目录不存在（{hooks_dir}；来源={hooks_dir_source}）", fix

    present = [n for n in _HOOK_NAMES if (hooks_dir / n).is_file()]
    broken_links = [n for n in _HOOK_NAMES
                    if (hooks_dir / n).is_symlink() and not (hooks_dir / n).exists()]
    missing = [n for n in _HOOK_NAMES if n not in present and n not in broken_links]

    # 执行位只在 POSIX 有语义；Windows 下 git 不据此决定是否忽略 hook。
    not_executable = []
    if os.name != "nt":
        not_executable = [n for n in present if not os.access(hooks_dir / n, os.X_OK)]

    if not missing and not broken_links and not not_executable:
        # 注意：**不再**因 `agate_common` 不可用就判「无法确认效力」。目录是直调
        # `git rev-parse --git-path hooks` 得到的，与 agate_common 那条路径同源同义，
        # 所以「在位 + 可执行 + 非断链」这个结论仍然成立（三轮评审 A2：原实现在**能问到
        # 答案**的场景里主动放弃判断，既没问 git 也没下结论，与索引行的承诺不符）。
        #
        # 收窄用词：本维度能证明的只是「git 会执行它」（在位 + 可执行 + 非断链）。
        # 它是否真能**阻断**取决于其内容（空文件、exit 0 的脚本也会被 git 执行却不拦），
        # 那要跑一次真实提交才知道——不在这里替 git 下结论（独立评审 A4 指出）。
        return True, (
            f"hook: 已安装且可执行（{', '.join(_HOOK_NAMES)}）〔{hooks_dir}；来源={hooks_dir_source}〕"
            "——注意：判的是「git 会不会执行它」，不含「其内容是否真能阻断」"
        ), None

    problems = []
    if missing:
        problems.append(f"缺失 {', '.join(missing)}")
    if broken_links:
        problems.append(f"断链 {', '.join(broken_links)}")
    if not_executable:
        problems.append(f"不可执行 {', '.join(not_executable)}（git 会忽略它们，commit 照常成功）")

    fixes = []
    if missing or broken_links:
        # 与上面 hooks_dir 同一判据：agate_common 挂掉时 agate-setup.py 也跑不起来
        # （它同样 import agate_common），给这条建议等于让人去撞同一堵墙（二轮评审 M9：
        # 原来的 hooks_dir_fallback 只用在「目录不存在」分支，真正会报 missing 的这里是死代码）。
        if hooks_dir_fallback:
            fixes.append("先让 agate_common 可用（缺 pyyaml 时 pip install pyyaml）后重跑")
        else:
            fixes.append(
                f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-setup.py'} "
                "--scope project 安装 hook"
            )
    if not_executable:
        fixes.append(f"恢复执行位：chmod +x {' '.join(str(hooks_dir / n) for n in not_executable)}")
    status = f"hook: {'；'.join(problems)}〔{hooks_dir}〕"
    return False, status, "；".join(fixes)


def _diagnose_version(project_root):
    """维度③：版本解析。返回 (ok, 状态行, 修复指引或 None)。

    **必须与 gate 用同一条解析链**（2026-11-26 实测修正）：原实现直接取「env 或脚本自身
    所在目录」，等于把「doctor 住在哪个 checkout」当成「gate 会判定用哪个版本」。实测在
    声明 `agate: v0.80.0`（未安装）的项目里，doctor 报 `<开发 checkout>/agate`，而
    `agate-resolve.py`（hook 实际走的链）报 `~/.agate/v0.83.3/agate`（回退 current）——
    两者指向不同版本目录，且**解析链给出的告警被完全吞掉**。

    **用哪条链**（2026-11-26 独立评审 C1）：gate 实际由 `resolve-entry.py` →
    `resolve_hook_root()` 定位，而 `resolve_hook_root` 比 `resolve_version_root` **多一层
    兜底**——解析链失败时回退「脚本路径上溯 + 复制模式 `.agate-root` 标记」，故它**恒返回非空
    root**。只用 `resolve_version_root` 会在「解析链不可用但 hook 仍能跑」的环境里误报
    「无可用 AGATE_ROOT」——那正是本批要消灭的那类镜像缺陷。

    **喂给它哪个路径**（C1 残余，同批修正）：必须喂**真实安装的 hook 入口**，不能喂本 checkout
    的 `resolve-entry.py`——后者上溯得到的是「doctor 住在哪个 checkout」，multi-worktree 下又是
    同一个错（把「我住哪」当「gate 用哪个」）。取法：`git_hooks_dir()` 下的 pre-commit，
    `Path.resolve()` 穿过软链得到 `~/.agate/scripts/pre-commit-gate.sh` 这类真实入口；
    复制模式（非软链）下该文件即入口本身，语义同样成立。
    """
    declared = ""
    ver_file = project_root / ".agate-version"
    if ver_file.is_file():
        try:
            declared = ver_file.read_text(encoding="utf-8").strip()
        except OSError:
            declared = ""

    try:
        import agate_common
        chain = agate_common.resolve_version_root(str(project_root))
        # 真实 hook 入口：hooks 目录下的 pre-commit 解析掉软链；不存在则退回本 checkout 的
        # resolve-entry.py（此时 hook 也没装，结果只用于「链给出什么」的对比展示）。
        # 注意：hook 未装（或断链）时无从取真实入口，只能退回本 checkout —— 此时 hook 本就不跑，
        # 该值也就没有「gate 实际用什么」的含义。故下面用 hook_entry_is_real 标注出来，
        # 不把「我住哪」冒充「gate 用哪个」（三轮评审 R3 候选①；与本批主题同源）。
        try:
            hook_entry = Path(agate_common.git_hooks_dir(str(project_root))) / "pre-commit"
            if hook_entry.exists():
                hook_entry = hook_entry.resolve()
                hook_entry_is_real = True
            else:
                hook_entry = _AGATE_ROOT / "scripts" / "resolve-entry.py"
                hook_entry_is_real = False
        except (Exception, SystemExit):
            hook_entry = _AGATE_ROOT / "scripts" / "resolve-entry.py"
            hook_entry_is_real = False
        hook_root, hook_warnings = agate_common.resolve_hook_root(str(hook_entry))
    except (Exception, SystemExit) as exc:
        # 同样按真因分流：agate-resolve.py 自己也 import agate_common，让它去跑是死循环建议。
        fix = ("先让 agate_common 可用（缺 pyyaml 时 pip install pyyaml）后重跑"
               if isinstance(exc, SystemExit)
               else f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-resolve.py'} 查看解析链")
        return False, f"版本解析: 解析链不可用（{_exc_note(exc)}）；项目 .agate-version={declared or '（未声明）'}", fix

    warnings = list(chain.get("warnings") or []) + [
        w for w in (hook_warnings or []) if w not in (chain.get("warnings") or [])
    ]
    chain_root = chain.get("root")
    version = chain.get("version") or ""
    reason = chain.get("reason") or ""
    root = chain_root or hook_root
    via_fallback = chain_root is None
    declared_note = declared if declared else "（未声明，使用 current）"

    # 兜底时 **不能** 照抄解析链的 reason（"无可用 AGATE_ROOT"）——那会和下面给出的
    # 实际可用 root 直接矛盾。改成如实说明「链没结果、gate 走了哪条兜底」。
    if via_fallback:
        reason_note = (
            "解析链无结果，gate 实际走脚本路径上溯兜底" if hook_entry_is_real
            else "解析链无结果，且 hook 未安装（无从取真实入口；此值为本工具所在 checkout，"
                 "不代表 gate 会用什么）"
        )
    else:
        reason_note = reason

    detail = f"AGATE_ROOT={Path(root).resolve()}；版本={version or '未标注'}；原因={reason_note}；" \
             f"项目 .agate-version={declared_note}"

    if warnings:
        # 解析链的告警正是「声明未安装 / 格式非法」这类会让判定与你预期不符的事实，
        # 必须摊到台面上——否则 doctor 反而掩盖了它。
        return False, f"版本解析: {' / '.join(warnings)}｜{detail}", \
            "按告警修正 .agate-version 声明，或安装所声明版本；" \
            f"用 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-resolve.py'} 复核"
    if not Path(root).is_dir():
        return False, f"版本解析: AGATE_ROOT 不可用（{root}）｜{detail}", \
            f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-resolve.py'} 查看解析链"
    # **判「gate 跑得起来」，不是判「目录存在」**（三轮评审 A2 第 2 条）：gate 实际由
    # `resolve-entry.py` 定位后校验 `<root>/scripts/<gate>.py` 是否存在，缺失即 fail-closed
    # 阻断提交（`resolve-entry.py:49-52`）。只报「AGATE_ROOT 目录在」会让「版本目录装了一半 /
    # 被手删过」的项目四维全绿，而真实 `git commit` 被拦——那是本批要消灭的那类差。
    gate_py = Path(root) / "scripts" / "pre-commit-gate.py"
    if not gate_py.is_file():
        return False, f"版本解析: {detail}｜**该 root 下缺 gate 脚本**（{gate_py}）", \
            "gate 会 fail-closed 阻断提交：重装所声明的版本（agate-install.py <version>），" \
            f"或用 {sys.executable} {_AGATE_ROOT / 'scripts' / 'agate-resolve.py'} 复核解析结果"
    if via_fallback and not hook_entry_is_real:
        # 判据是「能不能确认」，不是「看起来像不像」：链无结果且没有真实 hook 入口时，
        # 报出来的 root 只是本工具所在 checkout，与 gate 会用什么无关 ⇒ 不能判 OK
        # （否则又是一处「我住哪」冒充「gate 用哪个」）。
        # hook 维度的建议已经覆盖「装 hook」；这里只补版本侧独有的动作，避免同一根因两条重复建议。
        return False, f"版本解析: {detail}", \
            "安装 .agate-version 所声明的版本（或修正该声明）后重跑，以取得与 gate 同源的解析结果"
    return True, f"版本解析: {detail}", None


def _check_chain(ledger):
    """校验单个账本的 append-only 哈希链。返回 (ok, 说明)。"""
    try:
        raw_lines = ledger.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        return False, f"无法读取（{exc}）"
    expected = _genesis_hash()
    for idx, raw in enumerate(raw_lines, 1):
        try:
            event = json.loads(raw)
        except ValueError:
            return False, f"第 {idx} 行非合法 JSON"
        if event.get("prev_hash") != expected:
            return False, f"第 {idx} 行 prev_hash 断链"
        expected = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return True, f"{len(raw_lines)} 条事件，链完整"


def _diagnose_ledger(project_root):
    """维度④：账本完整性。返回 (ok, 状态行, 修复指引或 None)。"""
    tasks_dir, tasks_reason = _tasks_dir(project_root)
    if tasks_dir is None:
        # 解析失败 ≠ 没有任务目录：审计没跑，不能报 OK。
        # 且 check-events.py 同样 import agate_common——同环境下它也跑不起来，
        # 拿它当修复指引是死循环（二轮评审实测四个被建议的脚本 RC 全非 0）。
        return False, f"账本完整性: 无法定位任务目录（{tasks_reason}），审计未执行", \
            "先让 agate_common 可用（缺 pyyaml 时 pip install pyyaml）后重跑"
    if not tasks_dir.is_dir():
        return True, "账本完整性: 未发现任务目录（无账本可审计）", None
    ledgers = sorted(tasks_dir.glob("*/gate-events.jsonl"))
    if not ledgers:
        return True, "账本完整性: 未发现 gate-events.jsonl（无账本可审计）", None
    problems = []
    for ledger in ledgers:
        ok, note = _check_chain(ledger)
        if not ok:
            problems.append(f"{ledger.parent.name}: {note}")
    if problems:
        return False, f"账本完整性: {len(problems)} 个账本异常（{'; '.join(problems)}）", \
            f"运行 {sys.executable} {_AGATE_ROOT / 'scripts' / 'check-events.py'} <任务目录> 定位断链"
    return True, f"账本完整性: {len(ledgers)} 个账本，链完整", None


def main():
    _force_utf8()
    project_root = Path.cwd()

    checks = (
        _diagnose_declaration,
        _diagnose_hooks,
        _diagnose_version,
        _diagnose_ledger,
    )
    print("=" * 66)
    print("agate-doctor — 项目接入状态诊断")
    print(f"项目根: {project_root}")
    print("=" * 66)

    guidance = []
    for check in checks:
        try:
            ok, line, fix = check(project_root)
        except (Exception, SystemExit) as exc:  # 单维度异常不得使诊断整体崩溃（退出码固定）
            ok, line, fix = False, f"{check.__name__}: 诊断异常（{exc}）", "请提交 issue 或人工排查"
        mark = "OK" if ok else "!!"
        print(f"[{mark}] {line}")
        if fix:
            guidance.append(fix)

    if guidance:
        print("-" * 66)
        print("修复建议（异常项的可执行动作）：")
        # 去重保序：多个维度共享同一根因时，同一条建议会出现多次（如缺 pyyaml 时
        # 三个维度都指向「先让 agate_common 可用」），重复展示只是噪音。
        for item in dict.fromkeys(guidance):
            print(f"  - {item}")
    else:
        print("全部维度正常（已接入）。")

    # BDD-17：诊断正常完成 → 退出码固定为 0（报告问题不等于自身执行失败）。
    return 0


if __name__ == "__main__":
    sys.exit(main())
