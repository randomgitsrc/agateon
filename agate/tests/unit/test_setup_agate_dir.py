# tests/unit/test_setup_agate_dir.py — TAG0037 P3 组 C（批 F2：SETUP.md `$AGATE_DIR` 去 fallback + 四平台接入命令二值判定）
# 被测：agate/SETUP.md「先取协议根路径」节 + 四个平台小节的**字面命令**（文档即验收脚本：从文档抽取后原样在隔离环境实跑）；
#       agate/scripts/agate-summary.py 启动建议的协议入口路径（BDD-40 动态部分）。
# BDD 映射：BDD-41（$AGATE_DIR 取值命令无 legacy fallback）、BDD-42（Claude Code 接入 agate 侧命令）、
#           BDD-43（OpenCode 接入命令实跑）、BDD-44（DSH 接入命令实跑）、BDD-45（Codex 接入命令实跑）、
#           BDD-40（启动建议里的协议入口 == <解析出的 AGATE_ROOT>/AGENTS.md，动态部分）。
# 隔离：布局建在 tmp_path 下的隔离 HOME（`<HOME>/.agate/{v9.9.9/agate → 当前工作树 agate/ 的拷贝（不含 tests/）, latest, current}`）；
#       BDD-43 / 45 的 HOME 保持真实**仅供 opencode / codex 读自身配置**，AGATE_HOME 与 $AGATE_DIR 指隔离布局，命令不读不写真实 ~/.agate
#       （前后以只读元数据指纹核对不变）；BDD-42 不调用 claude CLI（真实模型调用降为 P6 人工项 H-1）。
# 安全：只执行从 SETUP 抽取且经白名单校验（mkdir / ln / 注释 / AGATE_DIR 赋值 / test）的命令；install-hook.py 等行不执行。
# 二值规则（P1 BDD-43 / 45，P2 T-12）：opencode / codex 不在 PATH → 判 FAIL（不跳过）。
#   唯一例外：GitHub Actions（GITHUB_ACTIONS=true）的通用 runner 上没有这两个 CLI，而现有 protocol-tests workflow 不允许修改
#   （BDD-13 ⑥），故仅该环境下缺 CLI 记为 skip（显式原因）；本地 / P5 / P6 验证环境缺 CLI 仍是 FAIL。
# 平台：POSIX 专用（bash + 符号链接）；Windows CI 只跑 windows_smoke，本文件不带该标记。
# 当前（P4 前）：BDD-41 两个用例与 BDD-40 动态用例红灯（SETUP 仍含旧 fallback；summary 仍硬编码用户主目录下的旧路径），均为断言失败；
#   BDD-42–45 是"接入链路无回归"守卫，对既有布局与旧取值命令同样成立，故当前即应绿（有意应绿）。

import contextlib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

import helpers_tag_repo as H

pytestmark = pytest.mark.skipif(not H.posix_shim_supported(), reason="SETUP 命令实跑仅 POSIX（bash + 符号链接）")

SETUP = H.REPO_ROOT / "agate" / "SETUP.md"
AGATE_SRC = H.REPO_ROOT / "agate"
VERSION_DIR = "v9.9.9"
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


# ---------------------------------------------------------------------------
# SETUP.md 命令抽取
# ---------------------------------------------------------------------------


def _section(text, title_pat, level):
    lines = text.splitlines()
    in_fence, heads = False, []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        m = None if in_fence else _HEADING.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2)))
    for idx, (ln, lv, title) in enumerate(heads):
        if lv == level and re.search(title_pat, title):
            end = len(lines)
            for ln2, lv2, _t in heads[idx + 1 :]:
                if lv2 <= lv:
                    end = ln2
                    break
            return "\n".join(lines[ln:end])
    return ""


def _bash_blocks(section_text):
    return re.findall(r"^```(?:bash|sh)\n(.*?)^```", section_text, re.S | re.M)


def _setup_section(title_pat, level):
    sec = _section(SETUP.read_text(encoding="utf-8"), title_pat, level)
    assert sec, f"SETUP.md 缺章节 /{title_pat}/（level {level}）"
    return sec


_ALLOWED_LINE = re.compile(r"^(#|mkdir\s|ln\s|AGATE_DIR=|test\s|python3\s+\S*install-hook\.py)")


def _runnable_lines(block, skip_install_hook=True):
    """抽取可执行行：只放行白名单命令（防止实跑文档里的联网 / 破坏性命令）；install-hook 行不执行。"""
    out = []
    for raw in block.splitlines():
        line = raw.strip()
        if not line:
            continue
        assert _ALLOWED_LINE.match(line), f"SETUP 命令块含非白名单命令，测试拒绝实跑: {line!r}"
        if line.startswith("#"):
            continue
        if skip_install_hook and "install-hook" in line:
            continue
        out.append(raw)
    return "\n".join(out)


def _bash_env(home, extra=None):
    env = dict(os.environ)
    # **`DSH_HOME` 必须一起中和**（2026-09-24 实测事故）：它会让被测的 `agate-setup.py`
    # 绕开假 HOME 去读写**开发者真实的 `~/.dsh`**——本地全量跑一次就把真实 DSH profile 的
    # 声明块装了又卸（并留下一串 `.bak.*`）。与 `AGATE_HOME`（DEBT0042）同一类泄漏。
    for key in ("AGATE_ROOT", "AGATE_HOME", "AGATE_DIR", "DSH_HOME"):
        env.pop(key, None)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    if extra:
        env.update(extra)
    return env


def _run_bash(bash, script, home, cwd, extra=None, timeout=60):
    return subprocess.run(
        [bash, "-c", script],
        cwd=str(cwd),
        env=_bash_env(home, extra),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def _eval_agate_dir(bash, home, cwd):
    """在隔离 HOME 下实跑 SETUP「先取协议根路径」节的取值命令，返回 (AGATE_DIR, CompletedProcess)。"""
    block = _bash_blocks(_setup_section(r"先取协议根路径", 2))
    assert block, "SETUP「先取协议根路径」节缺 bash 命令块"
    script = _runnable_lines(block[0]) + '\nprintf "\\nAGATE_DIR_VALUE=%s\\n" "${AGATE_DIR-}"\n'
    proc = _run_bash(bash, script, home, cwd)
    m = re.search(r"^AGATE_DIR_VALUE=(.*)$", proc.stdout, re.M)
    return (m.group(1) if m else None), proc


# ---------------------------------------------------------------------------
# 隔离版本管理布局
# ---------------------------------------------------------------------------


def _ignore(dirpath, names):
    ignored = {n for n in names if n == "__pycache__" or n.endswith((".pyc", ".pyo"))}
    if os.path.realpath(dirpath) == os.path.realpath(str(AGATE_SRC)) and "tests" in names:
        ignored.add("tests")
    return ignored


def _build_layout(home):
    """<home>/.agate/{v9.9.9/agate（当前工作树 agate/ 拷贝，无 tests/）, latest → v9.9.9, current → latest}。"""
    root = Path(home) / ".agate"
    vdir = root / VERSION_DIR
    shutil.copytree(str(AGATE_SRC), str(vdir / "agate"), ignore=_ignore)
    os.symlink(VERSION_DIR, str(root / "latest"))
    os.symlink("latest", str(root / "current"))
    return SimpleNamespace(
        home=Path(home),
        root=root,
        agate=vdir / "agate",
        expected_dir=str(Path(home) / ".agate" / "current" / "agate"),
    )


@pytest.fixture(scope="module")
def layout(tmp_path_factory):
    home = tmp_path_factory.mktemp("setup_layout_home")
    return _build_layout(home)


@pytest.fixture
def project(tmp_path):
    proj = tmp_path / "project"
    proj.mkdir()
    return proj


def _real_agate_fingerprint():
    """真实 ~/.agate 的只读元数据指纹（路径 / 类型 / 大小 / mtime_ns / 链接目标）；不存在 → 固定占位。
    只 lstat，不读文件内容、不写、不跟随软链。"""
    root = os.path.join(os.path.expanduser("~"), ".agate")
    if not os.path.lexists(root):
        return "absent"
    digest = hashlib.sha256()
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            st = os.lstat(cur)
        except OSError:
            digest.update(f"gone:{cur}\n".encode())
            continue
        target = os.readlink(cur) if os.path.islink(cur) else ""
        digest.update(f"{os.path.relpath(cur, root)}|{st.st_mode}|{st.st_size}|{st.st_mtime_ns}|{target}\n".encode())
        if os.path.isdir(cur) and not os.path.islink(cur):
            with contextlib.suppress(OSError):
                stack.extend(sorted(os.path.join(cur, n) for n in os.listdir(cur)))
    return digest.hexdigest()


@pytest.fixture
def real_agate_canary():
    """测试前后真实 ~/.agate 元数据指纹必须一致（BDD-42 / 43 / 44 / 45 的隔离证据）。"""
    before = _real_agate_fingerprint()
    yield
    assert _real_agate_fingerprint() == before, "测试触碰了真实 ~/.agate（内容指纹变化）"


def _cli_or_fail(name):
    path = shutil.which(name)
    if path:
        return path
    if os.environ.get("GITHUB_ACTIONS") == "true":
        pytest.skip(f"GitHub Actions 通用 runner 无 {name} CLI（本地 / P5 / P6 缺 CLI 判 FAIL，见文件头二值规则说明）")
    pytest.fail(f"{name} 不在 PATH：环境未就绪，BDD 判 FAIL（P1 BDD-43/45 二值规则；不得跳过 / 记为通过）")


# ---------------------------------------------------------------------------
# BDD-41  $AGATE_DIR 取值命令去 legacy fallback
# ---------------------------------------------------------------------------


def test_bdd_41_agate_dir_command_has_no_legacy_fallback():
    """BDD-41：「先取协议根路径」节的取值命令不含 `|| echo "$HOME/.agate"` 式 fallback；布局对照表只剩版本管理一行。"""
    sec = _setup_section(r"先取协议根路径", 2)
    blocks = _bash_blocks(sec)
    assert blocks, "该节应含取值命令块"
    cmd = blocks[0]
    assert not re.search(r"\|\|\s*echo\s+[\"']?\$\{?HOME\}?/\.agate[\"']?", cmd), f"取值命令仍含 fallback: {cmd!r}"
    assert "current" in cmd, "取值命令应基于 ~/.agate/current"
    table_rows = [
        ln for ln in sec.splitlines()
        if ln.strip().startswith("|") and not re.fullmatch(r"\|[\s:\-|]+\|?", ln.strip())
    ]
    data_rows = table_rows[1:]  # 去表头
    assert len(data_rows) <= 1, f"布局对照表只应剩版本管理一行（或整表删除），实得 {len(data_rows)} 行: {data_rows}"


def test_bdd_41_agate_dir_command_resolves_current_and_fails_loudly_without_it(bash, tmp_path, layout):
    """BDD-41：隔离 HOME 下实跑取值命令——布局完整时 $AGATE_DIR == $HOME/.agate/current/agate 且模板可读；
    `current` 缺失时给出明确失败提示，并且不静默落到 $HOME/.agate。"""
    ok_dir, ok = _eval_agate_dir(bash, layout.home, tmp_path)
    assert ok.returncode == 0, ok.stderr
    assert ok_dir == layout.expected_dir, f"AGATE_DIR={ok_dir!r}"
    assert (Path(ok_dir) / "orchestrator-template.md").is_file() and os.access(Path(ok_dir) / "orchestrator-template.md", os.R_OK)
    assert "✅" in ok.stdout, "模板可读时应给出成功提示"

    bare_home = tmp_path / "bare_home"
    (bare_home / ".agate" / VERSION_DIR).mkdir(parents=True)  # 版本目录在但没有 current 指针
    bad_dir, bad = _eval_agate_dir(bash, bare_home, tmp_path)
    assert bad_dir != str(bare_home / ".agate"), "current 缺失时不得静默落到 $HOME/.agate（legacy fallback）"
    assert not (bad_dir and (Path(bad_dir) / "orchestrator-template.md").is_file())
    assert bad.stdout.strip() and "✅" not in bad.stdout, f"current 缺失应给出明确失败提示，实际输出: {bad.stdout!r} / {bad.stderr!r}"


# ---------------------------------------------------------------------------
# BDD-42  Claude Code 接入（agate 侧命令）
# ---------------------------------------------------------------------------


def test_bdd_42_claude_code_registration_commands_and_frontmatter(bash, layout, project, real_agate_canary):
    """BDD-42：按 SETUP「Claude Code」节命令建链接——链接存在且目标可读、目标位于隔离 AGATE_HOME 内；
    目标 frontmatter 可被 yaml.safe_load 解析且含 name: orchestrator（两类静默失败）；真实 ~/.agate 指纹不变。不调用 claude CLI。"""
    agate_dir, proc = _eval_agate_dir(bash, layout.home, project)
    assert agate_dir == layout.expected_dir, proc.stderr
    block = _bash_blocks(_setup_section(r"^Claude Code", 3))
    assert block, "SETUP「Claude Code」节缺注册命令块"
    run = _run_bash(bash, _runnable_lines(block[0]), layout.home, project, extra={"AGATE_DIR": agate_dir})
    assert run.returncode == 0, run.stderr
    link = project / ".claude" / "agents" / "orchestrator.md"
    assert link.is_symlink(), "应建立文件级符号链接"
    assert os.access(link, os.R_OK) and link.read_text(encoding="utf-8"), "链接目标应可读"
    assert os.path.realpath(link).startswith(os.path.realpath(str(layout.root))), "链接目标应位于隔离 AGATE_HOME 内"
    text = link.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, "目标文件应以 YAML frontmatter 起头"
    front = yaml.safe_load(m.group(1))
    assert isinstance(front, dict) and front.get("name") == "orchestrator", front


# ---------------------------------------------------------------------------
# BDD-43  OpenCode 接入命令实跑
# ---------------------------------------------------------------------------


def test_bdd_43_opencode_registration_and_debug_agent(bash, layout, project, real_agate_canary):
    """BDD-43：按 SETUP「OpenCode」节命令建 .opencode/agents/orchestrator.md 链接，再在项目目录跑
    `opencode debug agent orchestrator`——exit 0，输出可解析为 JSON，mode == primary 且 tools.task == true。
    opencode 不在 PATH → FAIL（GitHub Actions 除外，见文件头）。HOME 保持真实仅供 opencode 读自身配置；AGATE_HOME 指隔离布局。"""
    opencode = _cli_or_fail("opencode")
    sec = _setup_section(r"^OpenCode", 3)
    assert "opencode debug agent orchestrator" in sec, "SETUP「OpenCode」节应含验证命令 opencode debug agent orchestrator"
    agate_dir, proc = _eval_agate_dir(bash, layout.home, project)
    assert agate_dir == layout.expected_dir, proc.stderr
    run = _run_bash(bash, _runnable_lines(_bash_blocks(sec)[0]), layout.home, project, extra={"AGATE_DIR": agate_dir})
    assert run.returncode == 0, run.stderr
    assert (project / ".opencode" / "agents" / "orchestrator.md").is_symlink()
    env = dict(os.environ)
    for key in ("AGATE_ROOT", "AGATE_DIR"):
        env.pop(key, None)
    env["AGATE_HOME"] = str(layout.root)  # 真实 HOME 不变；协议根指隔离布局
    out = subprocess.run(
        [opencode, "debug", "agent", "orchestrator"],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    assert out.returncode == 0, f"rc={out.returncode}\nstdout={out.stdout[-500:]}\nstderr={out.stderr[-500:]}"
    body = out.stdout[out.stdout.index("{"):] if "{" in out.stdout else out.stdout
    info = json.loads(body)
    assert info.get("mode") == "primary", info.get("mode")
    assert (info.get("tools") or {}).get("task") is True, info.get("tools")


# ---------------------------------------------------------------------------
# BDD-44  DSH 接入命令实跑（agate 侧）
# ---------------------------------------------------------------------------


def test_bdd_44_dsh_declarative_block_and_summary_reports_no_drift(layout, project, tmp_path):
    """BDD-44（2026-09-24 改写）：SETUP「步骤 2-DSH」节的**手工兜底块**须与实现生成的一致，
    且实跑接入后 `agate-summary.py` 无漂移/未安装信号。

    **为什么改写**：旧用例跑 `mkdir -p` + 三条 `ln -sf` 到 `~/.dsh/.agent-presets/agate/`——
    那套载体 DSH ≥0.1.7-alpha.1 起**已不被读取**（上游 skill 原文 "Nothing reads that
    directory any more."）。旧用例把死形态固化成"正确"，正是"工具长期报 ✅ 而 DSH 里根本没有
    该模式"无人发现的原因之一（实测 2026-09-20 之后零 agate 会话）。
    新判据对准 DSH **真正读取**的位置：profile 的 `cordis.patch.yml` 声明块。

    本用例仍满足 BDD-44 的原意（"按 SETUP 的说明操作后，DSH 侧确实接入且 summary 不报异常"），
    只是载体换成了现行形态；同时新增"文档里的兜底块 == 实现生成的块"这一**防漂移**判据。
    """
    home = tmp_path / "dsh_home"
    home.mkdir()
    lay = _build_layout(home)

    # ① 手工兜底块必须是**真块**（含定界符与声明三要素）
    sec = _setup_section(r"步骤 2-DSH", 3)
    assert "cordis.patch.yml" in sec, "SETUP DSH 章节须说明落点是 profile patch"
    assert "@deepseek-ai/dsh-agent-preset" in sec, "SETUP DSH 章节缺声明插件名"
    assert "preset-agate" in sec, "SETUP DSH 章节缺 loader 行 id"

    # ② 文档**不重复**整块（否则必漂移）——它给出形状，并指向唯一不会漂移的来源
    assert "dsh_preset_block" in sec, (
        "SETUP 应指向生成器（唯一不漂移的来源），而不是手抄整块"
    )
    assert "sed -n" in sec, "SETUP 应给出读取真实块内容的命令"
    # 形状片段必须属实：定界符 + 关键字段
    for frag in ("# >>> agateon: preset-agate", "# <<< agateon: preset-agate <<<",
                 "id: agate", "plugins:"):
        assert frag in sec, f"SETUP DSH 兜底片段缺 {frag!r}"
    # 且**不得**再出现旧死形态的安装路径
    assert ".agent-presets/agate/agent.cordis.yml" not in sec

    # ③ 实跑一次真实接入（假 DSH_HOME + 假 HOME），再让 summary 判定
    patch = home / ".dsh" / "profiles" / "web" / "cordis.patch.yml"
    patch.parent.mkdir(parents=True, exist_ok=True)
    patch.write_text("# 用户自己的 patch\n", encoding="utf-8")
    env = _bash_env(home, {"DSH_HOME": str(home / ".dsh")})
    proc = subprocess.run(
        [sys.executable, str(lay.agate / "scripts" / "agate-setup.py"),
         "--scope", "global", "--platform", "dsh"],
        cwd=str(project), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    written = patch.read_text(encoding="utf-8")
    assert "preset-agate" in written and "@deepseek-ai/dsh-agent-preset" in written, written
    assert "# 用户自己的 patch" in written, "接入不得丢弃用户原有内容"

    summary = subprocess.run(
        [sys.executable, str(lay.agate / "scripts" / "agate-summary.py")],
        cwd=str(project), env=env, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120,
    )
    assert summary.returncode == 0, summary.stderr
    out = summary.stdout + summary.stderr
    assert "DSH 接入产物漂移" not in out, out
    assert "DSH" not in out or "未安装或不完整" not in out, out


# ---------------------------------------------------------------------------
# BDD-45  Codex 接入命令实跑
# ---------------------------------------------------------------------------


def test_bdd_45_codex_template_readable_and_multi_agent_enabled(bash, layout, project, real_agate_canary):
    """BDD-45：$AGATE_DIR/orchestrator-template.md 可读；SETUP「步骤 2-Codex」验证命令 `timeout 60s codex features list`
    exit 0 且输出含 multi_agent 行，状态值为 stable 或 true。codex 不在 PATH → FAIL（GitHub Actions 除外）。
    不执行需登录 / 联网的 codex exec。HOME 保持真实仅供 codex 读自身配置。"""
    codex = _cli_or_fail("codex")
    sec = _setup_section(r"步骤 2-Codex", 3)
    assert "codex features list" in sec, "SETUP「步骤 2-Codex」节应含验证命令 codex features list"
    agate_dir, proc = _eval_agate_dir(bash, layout.home, project)
    assert agate_dir == layout.expected_dir, proc.stderr
    template = Path(agate_dir) / "orchestrator-template.md"
    assert template.is_file() and template.read_text(encoding="utf-8"), "模板应可读"
    env = dict(os.environ)
    for key in ("AGATE_ROOT", "AGATE_DIR"):
        env.pop(key, None)
    env["AGATE_HOME"] = str(layout.root)
    out = subprocess.run(
        [codex, "features", "list"],
        cwd=str(project),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    assert out.returncode == 0, f"rc={out.returncode}\nstderr={out.stderr[-500:]}"
    rows = [ln.split() for ln in out.stdout.splitlines() if ln.split()[:1] == ["multi_agent"]]
    assert rows, f"输出应含 multi_agent 行:\n{out.stdout[:600]}"
    tokens = rows[0]
    assert "stable" in tokens[1:] or tokens[-1] == "true", f"multi_agent 状态应为 stable / true: {tokens}"


# ---------------------------------------------------------------------------
# BDD-40（动态部分）  启动建议里的协议入口取自解析出的根
# ---------------------------------------------------------------------------


def test_bdd_40_summary_startup_advice_uses_resolved_root(tmp_path, layout, project):
    """BDD-40：版本管理布局（隔离）运行 agate-summary.py——启动建议中的协议入口路径 == <解析出的 AGATE_ROOT>/AGENTS.md
    且该文件存在；输出不再硬编码用户主目录下的旧路径（版本布局下该文件不存在）。"""
    proc = subprocess.run(
        [sys.executable, str(layout.agate / "scripts" / "agate-summary.py")],
        cwd=str(project),
        env=_bash_env(layout.home),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert proc.returncode == 0, proc.stderr
    m = re.search(r"^AGATE_ROOT：(.+)$", proc.stdout, re.M)
    assert m, proc.stdout
    root = m.group(1).strip()
    assert os.path.isfile(os.path.join(root, "AGENTS.md")), f"解析出的根下应有 AGENTS.md: {root}"
    advice = [ln for ln in proc.stdout.splitlines() if re.match(r"^2\.\s", ln)]
    assert advice, f"启动建议应含第 2 条:\n{proc.stdout}"
    assert os.path.join(root, "AGENTS.md") in advice[0], f"启动建议应指向 {root}/AGENTS.md，实得: {advice[0]!r}"
    assert "~/.agate/" + "AGENTS.md" not in proc.stdout, "不应再硬编码旧路径"
