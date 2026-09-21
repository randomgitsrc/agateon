# agate/tests/conftest.py — pytest 全局 fixture 体系（TAG0011 批次 0）
# 替代 tests/helpers/{load,fixtures,git-helper}.bash。
# 行为等价约定（P2-design.md §3.1 / P3-test-cases.md §5.1）：
#   * CommandResult.output = stdout + stderr 合并流（等价 bats $output，BLOCKER-1）
#   * 所有文本 I/O 显式 encoding="utf-8"（BDD-7）
#   * fixture 内容运行时构造，不写字面命中行（BDD-5）

import atexit
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest


class CommandResult:
    """subprocess 运行结果，等价 bats `run` 的 $status/$output/$stderr。

    .output 为 stdout + stderr 合并流（bats $output 语义，P2 BLOCKER-1）。
    """

    def __init__(self, returncode, stdout, stderr):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    @property
    def output(self):
        return self.stdout + self.stderr


DEFAULT_PHASES = ["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"]


def _resolve_agate_root(start):
    """load.bash `_resolve_agate_root` 等价：从 start 上溯找最近含 scripts/+assets/ 的目录。"""
    d = Path(start).resolve()
    while True:
        if (d / "scripts").is_dir() and (d / "assets").is_dir():
            return d
        parent = d.parent
        if parent == d:
            return None
        d = parent


def _write_utf8(path, text):
    path.write_text(text, encoding="utf-8")


def _isolated_home():
    """测试子进程的默认隔离 HOME：**每进程一份**的空目录（含 .agate 不存在 → 解析链失败）。

    为什么需要（DEBT0042 同族，2026-09-18）：被测脚本（resolve_agate_root /
    resolve_hook_root 等）的版本解析链**优先查 `~/.agate` 的 current/latest 指针**，
    只有解析失败才回退"脚本路径上溯"。若子进程继承真实 HOME，则本机装了稳定版
    （`~/.agate/vX.Y.Z/`）时会解析到稳定版目录，而非测试所在仓库——导致同一份代码
    在本机红、在 CI（无 `~/.agate`）绿，测试反馈不可信。

    隔离后 `~/.agate` 不存在 → 解析链失败 → 回退脚本路径上溯 → 指向测试仓库，
    与 CI 行为一致。需要验证版本解析链自身的测试显式传 `HOME`（见
    test_agate_version_resolve.py 的 `_resolve_env`），显式值覆盖本默认值。

    **实现要点**：
    - **每进程一份（惰性创建、缓存复用）**：并行跑时各 xdist worker 是独立进程，
      互不共享；同进程内复用同一目录（避免每次调用都建目录的开销与泄漏）。
    - **atexit 自动清理**：用 mkdtemp 建唯一目录并注册清理，跑完不留残渣
      （早期版本用固定路径 + PID 命名且不清理，实测泄漏 495 个目录）。
    - 缓存挂在函数属性上（避免 `global`，ruff PLW0603）。
    """
    cached = getattr(_isolated_home, "_cached", None)
    if cached is None:
        cached = tempfile.mkdtemp(prefix="_agate_test_home_")
        atexit.register(shutil.rmtree, cached, ignore_errors=True)
        _isolated_home._cached = cached
    return cached


def _user_site_packages():
    """当前解释器的用户级 site-packages（`~/.local/lib/pythonX.Y/site-packages`）。

    隔离 HOME 会**连带切断**用户 site-packages 的可见性（它经 `~` 定位），导致装在
    `~/.local` 的第三方包（如 Pillow）在子进程里 import 失败——实测
    `test_img_4_ahash_valid_image_64bit` 报 SKIP_NO_PILLOW。故隔离时经 PYTHONPATH
    显式带回该目录（不含 ~/.agate 相关路径，隔离目标不受影响）。
    """
    try:
        import site as _site
        cand = _site.getusersitepackages()
    except Exception:
        return None
    return cand if cand and os.path.isdir(cand) else None


def _run_cli_impl(*args, cwd=None, input=None, env=None):
    """等价 bats `run`：subprocess 封装，返回 CommandResult。

    参数：cwd=（等价 bats `cd`）、input=（等价 stdin 管道）、env=（附加环境变量）。

    **默认隔离 HOME**：子进程不再继承真实 HOME，避免被测脚本经 `~/.agate` 解析到
    本机稳定版（本机与 CI 结果分歧的根因）。同时经 PYTHONPATH 带回用户 site-packages，
    避免切断 `~/.local` 下第三方包的可见性。显式 `env` 中的 HOME/USERPROFILE/PYTHONPATH
    覆盖默认值——需要构造假 `~/.agate` 布局的测试照常传自己的 HOME。

    **同时中和 `AGATE_HOME`**（DEBT0042 新增的基址 env）：它是解析链里比 `~/.agate`
    更高优先的一层，若外环境设了它，隔离 HOME 就形同虚设——同一类"本机环境决定红绿"
    会经新变量复发（实测未中和时 20 failed / 53 passed）。需要显式指定基址的测试
    在 `env=` 里传自己的值（在下方 update 时覆盖本行的删除）。
    """
    cmd = [str(a) for a in args]
    full_env = os.environ.copy()
    full_env.pop("AGATE_HOME", None)
    # HOME 与 USERPROFILE 同时设（Windows 的 expanduser 读 USERPROFILE）
    full_env["HOME"] = _isolated_home()
    full_env["USERPROFILE"] = full_env["HOME"]
    user_site = _user_site_packages()
    if user_site:
        existing = full_env.get("PYTHONPATH", "")
        full_env["PYTHONPATH"] = (user_site + os.pathsep + existing) if existing else user_site
    if env:
        full_env.update(env)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd is not None else None,
        input=input,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=full_env,
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def create_task_dir(
    base_dir,
    phases=None,
    risk_level="medium",
    with_evidence=False,
    no_state_yaml=False,
    legacy_fields=False,
):
    """fixtures.bash create_task_dir 等价，返回 base_dir 下新建的任务目录。"""
    if phases is None:
        phases = list(DEFAULT_PHASES)
    base = Path(base_dir)
    base.mkdir(parents=True, exist_ok=True)
    task_dir = Path(tempfile.mkdtemp(prefix="task-", dir=str(base)))

    if not no_state_yaml:
        first_phase = phases[0] if phases else "P1"
        _write_utf8(
            task_dir / ".state.yaml",
            f"task_id: T001\nphase: {first_phase}\nstatus: active\nretries: {{}}\n",
        )

    _write_utf8(
        task_dir / "P0-brief.md",
        'task: "test task"\n'
        "known_risks: []\n"
        "executor_env:\n"
        '  platform: "opencode"\n'
        "  has_task_tool: true\n"
        "  has_local_runtime: true\n"
        '  network: "full"\n'
        "env_constraints:\n"
        '  debug_env: "echo debug"\n',
    )

    phases_csv = ",".join(phases)
    p1_body = (
        "### 主流程\n\n"
        "#### BDD-1: test\n"
        "- Given test precondition\n"
        "- When test action\n"
        "- Then test result\n"
    )
    if legacy_fields:
        p1 = f"---\nagent: test\n---\nrisk_level: {risk_level}\nphases: [{phases_csv}]\n\n{p1_body}"
    else:
        p1 = (
            f"---\nagent: test\nrisk_level: {risk_level}\nphases: [{phases_csv}]\n---\n\n"
            f"{p1_body}"
        )
    _write_utf8(task_dir / "P1-requirements.md", p1)

    for p in phases:
        if p == "P2":
            (task_dir / "P2-design.md").touch()
        elif p == "P3":
            (task_dir / "P3-test-design.md").touch()
        elif p == "P4":
            (task_dir / "P4-implementation.md").touch()
        elif p == "P5":
            (task_dir / "P5-verification.md").touch()
        elif p == "P6":
            _write_utf8(task_dir / "P6-acceptance.md", "---\nagent: test\n---\n")
        elif p == "P7":
            (task_dir / "P7-consistency.md").touch()
        elif p == "P8":
            (task_dir / "P8-release.md").touch()

    for f in sorted(task_dir.glob("P[1-8]-*.md")):
        if not f.is_file():
            continue
        head = f.read_text(encoding="utf-8").splitlines()[:3]
        if any(line == "---" for line in head):
            continue
        _write_utf8(f, "---\nagent: test\n---\n\n" + f.read_text(encoding="utf-8"))

    if with_evidence:
        (task_dir / "P6-evidence").mkdir(parents=True, exist_ok=True)

    return task_dir


def add_agent_field(file_path):
    """给 .md 文件加 frontmatter `agent: test`（如果没有）。"""
    p = Path(file_path)
    if p.is_file():
        head = p.read_text(encoding="utf-8").splitlines()[:3]
        if not any(line == "---" for line in head):
            _write_utf8(p, "---\nagent: test\n---\n\n" + p.read_text(encoding="utf-8"))


def add_given_line(file_path):
    """在 P1 加一个 Given 行（如果还没有）。"""
    p = Path(file_path)
    text = p.read_text(encoding="utf-8")
    if not re.search(r"^\s*-\s*Given\b", text, re.M):
        _write_utf8(p, text + "- Given test precondition\n")


def add_frontmatter_field(file_path, field, value):
    """在文件的 frontmatter 块内插入/更新一个顶层 key（v2.0 流 A）。"""
    p = Path(file_path)
    line = f"{field}: {value}"
    if not p.exists():
        _write_utf8(p, f"---\n{line}\n---\n")
        return
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()
    if lines and lines[0] == "---":
        end_idx = None
        for i in range(1, len(lines)):
            if lines[i] == "---":
                end_idx = i
                break
        if end_idx is not None and end_idx > 1:
            pattern = re.compile(rf"^{re.escape(field)}:")
            replaced = False
            for i in range(1, end_idx):
                if pattern.match(lines[i]):
                    lines[i] = line
                    replaced = True
            if not replaced:
                lines.insert(end_idx, line)
            _write_utf8(p, "\n".join(lines) + "\n")
            return
    _write_utf8(p, f"---\n{line}\n---\n{text}")


def add_pruning_excuse(task_dir, phase, reason, risk):
    """声明裁剪某阶段 + 写裁剪理由 + 跳过风险。"""
    p1 = Path(task_dir) / "P1-requirements.md"
    text = p1.read_text(encoding="utf-8")
    text = text.replace(phase + ",", "").replace("," + phase, "").replace(phase, "")
    text += f"\n裁剪 {phase}: {reason}\n跳过风险: {risk}\n"
    _write_utf8(p1, text)


def add_p1_field(task_dir, field, value):
    """在 P1-requirements.md 的 frontmatter 块加/改顶层字段。"""
    add_frontmatter_field(Path(task_dir) / "P1-requirements.md", field, value)


def add_p2_candidate_count(task_dir, count):
    """在 P2-design.md 的 frontmatter 块加/改 candidate_count 字段。"""
    add_frontmatter_field(Path(task_dir) / "P2-design.md", "candidate_count", str(count))


def add_p2_review(task_dir, status="approved", agent="reviewer-subagent"):
    """创建一个合规的 P2-review.md。"""
    p = Path(task_dir) / "P2-review.md"
    _write_utf8(p, f"---\nstatus: {status}\nagent: {agent}\n---\nP2 review approved.\n")


def add_evidence_file(task_dir, rel_path, content, size=None):
    """在 P6-evidence/ 放文件，可指定大小（用于空 png 测试）。"""
    full = Path(task_dir) / "P6-evidence" / rel_path
    full.parent.mkdir(parents=True, exist_ok=True)
    if size is not None:
        data = base64.b64encode(os.urandom(int(size))).decode("ascii")[: int(size)]
        _write_utf8(full, data)
    else:
        _write_utf8(full, content)


def add_p6_pass(task_dir, bdd_id, evidence_ref):
    with open(Path(task_dir) / "P6-acceptance.md", "a", encoding="utf-8") as fh:
        fh.write(f"- PASS {bdd_id} ({evidence_ref})\n")


def add_p6_fail(task_dir, bdd_id, evidence_ref=None):
    with open(Path(task_dir) / "P6-acceptance.md", "a", encoding="utf-8") as fh:
        line = f"- FAIL {bdd_id}" if evidence_ref is None else f"- FAIL {bdd_id} ({evidence_ref})"
        fh.write(line + "\n")


def add_p6_need_confirm(task_dir, bdd_id):
    with open(Path(task_dir) / "P6-acceptance.md", "a", encoding="utf-8") as fh:
        fh.write(f"- NEED_CONFIRM {bdd_id}\n")


def add_p1_bdd(task_dir, desc="test"):
    """在 P1-requirements.md 末尾追加 `#### BDD-NN:` 标题行，NN 为当前最大编号 +1。"""
    p1 = Path(task_dir) / "P1-requirements.md"
    text = p1.read_text(encoding="utf-8")
    n = len(re.findall(r"^#### BDD-[0-9]", text, re.M))
    _write_utf8(p1, text + f"#### BDD-{n + 1}: {desc}\n")


class GitRepo:
    """git-helper.bash git_init/git_commit/git_stage/git_staged_diff/git_staged_files 等价封装。"""

    def __init__(self, path):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self._git("init", "-q")
        self._git("config", "user.email", "test@test.local")
        self._git("config", "user.name", "Test")
        self._git("config", "commit.gpgsign", "false")

    def _git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.path)] + [str(a) for a in args],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )

    def git(self, *args):
        """运行任意 git 命令，返回 CommandResult 等价对象。"""
        return self._git(*args)

    def commit(self, message, files=None):
        if files:
            for f in files:
                self.stage(f)
        else:
            self._git("add", "-A")
        self._git("commit", "-q", "-m", message)

    def stage(self, path):
        self._git("add", str(path))

    def staged_diff(self):
        return self._git("diff", "--cached").stdout

    def staged_files(self):
        return self._git("diff", "--cached", "--name-only").stdout


@pytest.fixture(scope="session")
def agate_root():
    """AGATE_ROOT 解析：AGATE_ROOT env 覆盖优先，否则从 tests/ 上溯反推；失败 fail-closed。"""
    env_root = os.environ.get("AGATE_ROOT")
    root = Path(env_root).resolve() if env_root else _resolve_agate_root(Path(__file__).resolve().parent)
    if root is None or not (root / "scripts").is_dir() or not (root / "assets").is_dir():
        pytest.fail(f"FATAL: AGATE_ROOT={root} 下找不到 scripts/ 或 assets/")
    return root


@pytest.fixture(scope="session")
def agate_scripts(agate_root):
    return agate_root / "scripts"


@pytest.fixture(scope="session")
def agate_assets(agate_root):
    return agate_root / "assets"


_GIT_BASH_CANDIDATES = (
    r"C:\Program Files\Git\bin\bash.exe",
    r"C:\Program Files (x86)\Git\bin\bash.exe",
)


def _is_wsl_bash(path):
    """System32 下的 bash.exe 是 WSL 入口（无分发版时输出 UTF-16 错误），必须排除。"""
    system32 = os.path.normcase(
        os.path.join(os.environ.get("SYSTEMROOT", r"C:\Windows"), "System32", "bash.exe")
    )
    return os.path.normcase(str(path)) == system32


@pytest.fixture(scope="session")
def bash():
    """bash 解释器：Linux 返回 "bash"（不改变行为）；Windows 探测 Git Bash 完整路径。

    Windows 上 PATH 里裸 "bash" 解析到 System32\\bash.exe（WSL 入口），无 WSL 分发版时
    输出 UTF-16 错误导致测试误判——优先已知 Git Bash 安装位置，再 shutil.which 排除 System32。
    """
    if sys.platform != "win32":
        return "bash"
    for candidate in _GIT_BASH_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    for name in ("bash", "bash.exe"):
        found = shutil.which(name)
        if found and not _is_wsl_bash(found):
            return found
    pytest.fail("Windows 上找不到 Git Bash（System32 的 WSL bash 已排除）")


@pytest.fixture(scope="session")
def python_exe():
    """python3 → python 回退探测（等价 detect_python/probe_python）；无则 fail-closed。"""
    for name in ("python3", "python"):
        found = shutil.which(name)
        if found:
            return found
    pytest.fail("找不到 python3/python 解释器")


@pytest.fixture
def run_cli():
    """run_cli fixture：测试请求该 fixture 后以 run_cli(python_exe, ...) 调用。"""
    return _run_cli_impl


@pytest.fixture
def task_dir(tmp_path):
    """create_task_dir 等价 factory，默认全阶段 P0-P8 + .state.yaml。"""

    def _make(
        phases=None,
        risk_level="medium",
        with_evidence=False,
        no_state_yaml=False,
        legacy_fields=False,
    ):
        return create_task_dir(
            tmp_path,
            phases=phases,
            risk_level=risk_level,
            with_evidence=with_evidence,
            no_state_yaml=no_state_yaml,
            legacy_fields=legacy_fields,
        )

    return _make


@pytest.fixture
def git_repo(tmp_path):
    return GitRepo(tmp_path)


@pytest.fixture(scope="session")
def load_fixture(agate_root):
    """静态夹具加载：load_fixture(name) → agate_root/tests/fixtures/name 绝对路径。"""

    def _load(name):
        return agate_root / "tests" / "fixtures" / name

    return _load


@pytest.fixture
def py_path():
    """路径转换：Windows 下 cygpath -m，Linux 恒等返回。"""

    def _convert(path):
        cygpath = shutil.which("cygpath")
        if cygpath:
            result = subprocess.run(
                [cygpath, "-m", str(path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            converted = result.stdout.strip()
            return converted or str(path)
        return str(path)

    return _convert

# ── 适配层去漂移共享判据（2026-09-21）────────────────────────────────────────
#
# **为何放 conftest 而非某个测试文件**：该判据要守护**两个不同测试文件**里守护的
# 三类载体（dsh/agent.cordis.yml 的 persona、dsh/SKILL.md、codex/SKILL.md）。
# 若各自在本文件内写字面量，改一处词表另一处不跟随——正是本 PR 要消的"两套标准"形态。
# 单一来源在此，两处 import。
#
# **锚点选取标准（硬要求）**：必须在被守护文件的**改动前版本**（main `77e33da`）中
# 真实出现过，否则是"死判据"（对旧文件不变红 = 不是回归测试）。计数实测：
#   `只有你能写的文件` persona(旧)=1 模板=1 ／ `你不是 gate` persona(旧)=0 模板=1
#   `会话开始时` persona(旧)=1 模板=2
#
# **已知限制（如实登记，勿高估本判据）**：这是**关键词**判据，不是语义判据——把协议规则
# 做**同义改写**（例："你负责的产出文件只有这些；判定交给脚本，你不做判定"）即可绕过。
# 真正防住复述靠**人工评审**（本仓协议改动本就须过 protocol-alignment-review）；本判据的
# 价值是让**逐字复述 / 照抄表头**这类最常见的漂移形态在 CI 变红，而非穷尽语义等价。
# 该上限已登记为 **DEBT0049**（`agate-workspace/debt/tech-debt.md`：含"改用结构性判据"
# 的备选方向与关闭判据）——本注释**不暗示**已封堵改写路径。
PROTOCOL_RULE_MARKERS = (
    "只有你能写的文件",   # 模板「只有你能写的文件」表名
    "你不是 gate",        # 模板规则段
    "会话开始时",         # 模板步骤节标题（旧 persona 逐字复述过）
)

# persona 专属：协议内部文件名/变量——persona 职责只是"指向模板"，点名内部文件即复述步骤。
# （旧 persona 逐条列过 active-tasks.md / phase-cards / {AGATE_WORKSPACE}）
PERSONA_INTERNAL_NAME_MARKERS = ("active-tasks.md", "phase-cards", "{AGATE_WORKSPACE}")

# 工具映射表的**行特征**（映射单一来源判据用；DSH 有 persona 层，其 SKILL 不得再有映射表）。
# 用正则容忍空格变体（复审实测 `|读状态|` 会绕过字面量）。
MAPPING_ROW_RE = re.compile(r"^\|\s*(读状态|派发 subagent|跑 gate|更新状态)\s*\|", re.MULTILINE)
