# agate/tests/unit/test_check_mvwu.py — check-mvwu.py 行为契约测试（TAG0036 P3，TDD 红灯）
#
# 被测对象：agate/scripts/check-mvwu.py（MVWU 阶段 1 观测器：六项检查 + 四态 verdict + --observe）。
# 权威来源：P1-requirements.md「口径 A-H」+ BDD-4（check-mvwu 侧）、BDD-13 ~ BDD-55、BDD-57、BDD-58；
#   BDD-56（真实任务目录 --observe 跑通）是 P6 真实证据，不在此写单测。
# 测试命名：test_bdd_<N>_<slug>，参数化的等价类共享同一 BDD 编号。
# 隔离（DEBT0040）：一切 git 仓库/任务目录都建在 pytest tmp_path，不触碰仓库内 agate-workspace。
# 红灯性质：check-mvwu.py 尚不存在时，所有用例经 MvwuRepo.run() 的"脚本存在"断言失败（项目内缺失，B 类）。
# 平台无关：子进程解释器一律 sys.executable；git 命令 check=True + 超时；显式 utf-8；符号链接用例按平台 skip。

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

AGATE_DIR = Path(__file__).resolve().parents[2]
SCRIPT = AGATE_DIR / "scripts" / "check-mvwu.py"
CHECK_GATE = AGATE_DIR / "scripts" / "check-gate.py"
FIELD_GET = AGATE_DIR / "scripts" / "agate-md-field-get.py"

VERDICTS = ("PASS", "FAIL", "EXPECTED_RED", "UNKNOWN")
DEFAULT_TF = "python -m pytest tests/a -q"
GOOD_CMD = "git status --short"  # 首词 git 在 PATH 上可解析（测试本身依赖 git）
BAD_CMD = "no-such-runner-xyz tests/"
LEGACY_HEAD = "1234567890abcdef1234567890abcdef12345678"  # 40 位十六进制，仓库中不存在

# --observe 七列（口径 H）
COL_MVWU, COL_TF, COL_DUR, COL_EVID, COL_FORM, COL_BOUND, COL_VERDICT = range(7)


# ---------------------------------------------------------------- 仓库 / 任务目录构造 helper


class MvwuRepo:
    """tmp_path 内的临时 git 仓库 + 任务目录（`<ws>/tasks/T1`）。

    默认分支 main 上有两个提交：初始提交（src/a.py src/b.py src/c.py）与 main-2（再改 src/a.py，
    充当"区间外的更早历史提交"，口径 E）。git 命令统一 check=True + 超时。
    """

    def __init__(self, tmp_path, ws="agate-workspace", branch="main"):
        self.root = tmp_path / "repo"
        self.root.mkdir()
        home = tmp_path / "home"
        home.mkdir()
        env = dict(os.environ)
        for key in ("AGATE_TASKS_DIR", "AGATE_WORKSPACE", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            env.pop(key, None)
        env.update(
            {
                "HOME": str(home),
                "USERPROFILE": str(home),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CEILING_DIRECTORIES": str(tmp_path),
                "PYTHONIOENCODING": "utf-8",
                "PYTHONUTF8": "1",
            }
        )
        self.env = env
        self.ws = ws
        self.git("init", "-q")
        self.git("symbolic-ref", "HEAD", f"refs/heads/{branch}")
        self.git("config", "user.name", "MVWU Test")
        self.git("config", "user.email", "mvwu@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        if ws != "agate-workspace":
            (self.root / ".agate.env").write_bytes(f"AGATE_WORKSPACE={ws}\n".encode())
        self.task = self.root / ws / "tasks" / "T1"
        self.task.mkdir(parents=True)
        self.commit("init", {"src/a.py": "v0\n", "src/b.py": "v0\n", "src/c.py": "v0\n", "README.md": "r\n"})
        self.commit("main-2", {"src/a.py": "v1\n"})

    # -- git
    def git(self, *args, cwd=None):
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.root),
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            env=self.env,
        )
        return proc.stdout.strip()

    def commit(self, msg, files):
        for rel, text in files.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(text.encode("utf-8"))
        self.git("add", "--", *files)
        self.git("commit", "-q", "-m", msg)

    def commit_all(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def checkout_new(self, branch):
        self.git("checkout", "-q", "-b", branch)

    def head(self):
        return self.git("rev-parse", "HEAD")

    # -- 任务目录
    def write_plan(self, batches, task=None):
        write_plan(task or self.task, batches)

    def write_evidence(self, bid, **over):
        over.setdefault("git_head", self.head())
        return write_evidence(self.task, bid, **over)

    def setup(self, entries):
        """entries: [(batch_dict, evidence_overrides | None)]；None 表示不写证据。"""
        self.write_plan([b for b, _ in entries])
        written = set()
        for batch, ev in entries:
            bid = batch.get("id")
            if ev is not None and isinstance(bid, str) and bid not in written and safe_id(bid):
                written.add(bid)
                self.write_evidence(bid, **ev)

    # -- 运行被测脚本
    def run(self, *flags, target=None, cwd=None):
        assert SCRIPT.is_file(), f"agate/scripts/check-mvwu.py 尚未实现（TDD 红灯：项目内缺失）: {SCRIPT}"
        args = [sys.executable, str(SCRIPT), *flags]
        if target is not False:
            args.append(str(target or self.task))
        return subprocess.run(
            args,
            cwd=str(cwd or self.root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            env=self.env,
        )

    def rows(self, *flags):
        """运行并解析契约行（断言 exit 0、无 traceback、每行可按空白分词）。"""
        res = self.run(*flags)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "Traceback" not in res.stderr, res.stderr
        return contract_rows(res.stdout)

    def obs(self, n=None):
        res = self.run("--observe")
        assert res.returncode == 0, res.stdout + res.stderr
        assert "Traceback" not in res.stderr, res.stderr
        return observe_rows(res.stdout, n)


def safe_id(bid):
    return re.fullmatch(r"[A-Za-z0-9._-]+", bid) is not None


def batch(bid, tf=DEFAULT_TF, **extra):
    b = {"id": bid, "complexity": "low", "tests_filter": tf}
    b.update(extra)
    return b


def bare_batch(bid, **extra):
    """无 tests_filter 键的批。"""
    b = {"id": bid, "complexity": "low"}
    b.update(extra)
    return b


def write_plan(task_dir, batches):
    plan = {"mode": "static-batch", "parallel_limit": 9, "batches": batches}
    text = "---\nphase: P2\ntask_id: T1\ndispatch_plan: " + json.dumps(plan) + "\n---\n# P2\n"
    Path(task_dir).mkdir(parents=True, exist_ok=True)
    (Path(task_dir) / "P2-design.md").write_bytes(text.encode("utf-8"))


def evidence_text(head, **over):
    """默认合法证据（PASS）；over[key] = None 表示省略该键，否则为该键的原始文本值。"""
    fields = {
        "command": GOOD_CMD,
        "exit_code": "0",
        "git_head": head,
        "timestamp": "2026-09-19T00:00:00Z",
        "expected_red": "[]",
        "failed_tests": "[]",
        "duration_seconds": "8",
    }
    fields.update(over)
    return "".join(f"{k}: {v}\n" for k, v in fields.items() if v is not None)


def write_evidence(task_dir, bid, git_head=None, raw=None, **over):
    """写 P4-evidence/<bid>.log；raw 为 bytes 时原样写入（损坏/CRLF 用例）。"""
    path = Path(task_dir) / "P4-evidence" / f"{bid}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = raw if raw is not None else evidence_text(git_head, **over).encode("utf-8")
    path.write_bytes(data)
    return path


# ---------------------------------------------------------------- 输出解析 helper


def out_lines(stdout):
    """按 \n 切行（不用 splitlines：它会把 \\x0b/\\x1c/\\x85 等也当行界）。"""
    parts = stdout.split("\n")
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def contract_rows(stdout):
    """契约行 → [(VERDICT, batch_token, reason|None)]；断言每行恰按空白分为 3 或 4 词。"""
    rows = []
    for line in out_lines(stdout):
        words = line.split()
        assert words[0] == "MVWU_RESULT:", line
        assert len(words) in (3, 4), line
        assert words[1] in VERDICTS, line
        assert words[2].startswith("batch="), line
        reason = None
        if len(words) == 4:
            assert words[3].startswith("reason="), line
            reason = words[3][len("reason="):]
        rows.append((words[1], words[2][len("batch="):], reason))
    return rows


def split_gfm_row(line):
    """按 GFM 表格规则切分一行（`\\` 转义下一字符，不作分隔）；返回去首尾空白的单元格。"""
    line = line.strip()
    assert line.startswith("|") and line.endswith("|"), line
    body = line[1:-1]
    cells, cur, i = [], [], 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body):
            cur.append(body[i:i + 2])
            i += 2
            continue
        if ch == "|":
            cells.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur))
    return [c.strip() for c in cells]


def observe_rows(stdout, n=None):
    lines = out_lines(stdout)
    if n is not None:
        assert len(lines) == n, lines
    rows = [split_gfm_row(line) for line in lines]
    for row in rows:
        assert len(row) == 7, row
    return rows


def one(repo, entry_batch=None, **evidence):
    """单批快捷路径：写一批 + 证据 → 返回唯一一行 (verdict, batch, reason)。"""
    repo.setup([(entry_batch or batch("A"), evidence)])
    rows = repo.rows()
    assert len(rows) == 1, rows
    return rows[0]


def snapshot(root):
    snap = {}
    for p in sorted(root.rglob("*")):
        if ".git" in p.relative_to(root).parts or not p.is_file():
            continue
        snap[p.relative_to(root).as_posix()] = p.read_bytes()
    snap["<git-index>"] = (root / ".git" / "index").read_bytes()
    return snap


# ================================================================ 基本契约


@pytest.mark.windows_smoke
def test_bdd_13_basic_contract_two_batches_in_declared_order(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {}), (batch("B"), {})])
    res = repo.run()
    assert res.returncode == 0, res.stdout + res.stderr
    lines = out_lines(res.stdout)
    assert len(lines) == 2, lines
    rows = contract_rows(res.stdout)
    assert [r[1] for r in rows] == ["A", "B"]
    assert all(r[0] in VERDICTS for r in rows)


def test_bdd_4_mixed_tests_filter_batches_are_independent(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {}), (bare_batch("B"), {})])
    # gate 侧：含/不含 tests_filter 的混合批不被 _gate_p2_dispatch_plan 拒绝
    spec = importlib.util.spec_from_file_location("check_gate_for_mvwu_test", str(CHECK_GATE))
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    assert gate._gate_p2_dispatch_plan(str(repo.task / "P2-design.md")) is None
    # check-mvwu 侧：B 缺 tests_filter；A 的输出不受 B 影响
    mixed = repo.rows()
    assert mixed[1] == ("UNKNOWN", "B", "tests_filter")
    repo.setup([(batch("A"), {})])
    alone = repo.rows()
    assert mixed[0] == alone[0]


# ================================================================ 检查 1-5


@pytest.mark.parametrize(
    "case",
    ["missing", "empty-string", "non-string-int", "non-string-list"],
)
def test_bdd_14_check1_tests_filter_missing_or_invalid_is_unknown(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    if case == "missing":
        b = bare_batch("A")
    else:
        b = batch("A", tf={"empty-string": "", "non-string-int": 5, "non-string-list": ["x"]}[case])
    assert one(repo, b) == ("UNKNOWN", "A", "tests_filter")


@pytest.mark.parametrize(
    "command",
    [BAD_CMD, None, "", 'pytest "unclosed', "FOO=1"],
    ids=["unresolvable-first-word", "missing-key", "empty", "unbalanced-quote", "only-env-assignment"],
)
def test_bdd_15_check2_command_first_word_unresolvable_or_missing_is_unknown(tmp_path, command):
    repo = MvwuRepo(tmp_path)
    assert one(repo, command=command) == ("UNKNOWN", "A", "command")


def test_bdd_16_check2_leading_env_assignment_is_skipped(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (batch("A"), {"command": "FOO=1 git status --short"}),
            (batch("B"), {"command": "FOO=1 no-such-runner-xyz tests/b"}),
        ]
    )
    assert repo.rows() == [("PASS", "A", None), ("UNKNOWN", "B", "command")]


def test_bdd_17_check2_compound_command_only_first_word_is_checked(tmp_path):
    repo = MvwuRepo(tmp_path)
    assert one(repo, command="cd sub && no-such-runner-xyz tests/") == ("PASS", "A", None)
    assert "仅检查首词" in doc_text(repo)


def test_bdd_18_command_is_not_compared_with_tests_filter(tmp_path):
    repo = MvwuRepo(tmp_path)
    got = one(repo, batch("A", "python -m pytest tests/a -q"), command="git log -1")
    assert got == ("PASS", "A", None)
    assert "不比对 command 与 tests_filter" in doc_text(repo)


@pytest.mark.parametrize("mode", ["default", "observe"])
def test_bdd_19_never_executes_command_or_tests_filter(tmp_path, mode):
    repo = MvwuRepo(tmp_path)
    sentinel_cmd = tmp_path / "sentinel-command"
    sentinel_tf = tmp_path / "sentinel-tests-filter"
    repo.setup(
        [
            (
                batch("A", f'git init "{sentinel_tf.as_posix()}"'),
                {"command": f'git init "{sentinel_cmd.as_posix()}"'},
            )
        ]
    )
    res = repo.run(*(["--observe"] if mode == "observe" else []))
    assert res.returncode == 0, res.stdout + res.stderr
    assert len(out_lines(res.stdout)) == 1
    assert not sentinel_cmd.exists()
    assert not sentinel_tf.exists()


def test_bdd_20_check3_evidence_missing_is_unknown(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), None)])
    assert repo.rows() == [("UNKNOWN", "A", "evidence")]


@pytest.mark.parametrize(
    "bid,candidate",
    [
        ("../escape", "escape.log"),
        ("a b", "P4-evidence/a b.log"),
        ("a/b", "P4-evidence/a/b.log"),
        ("a\\b", "P4-evidence/a\\b.log"),
    ],
    ids=["dotdot", "space", "slash", "backslash"],
)
def test_bdd_21_unsafe_batch_id_is_unknown_and_external_file_not_read(tmp_path, bid, candidate):
    repo = MvwuRepo(tmp_path)
    marker = "OUTSIDE-CANDIDATE-MARKER-7731"
    cand = repo.task / candidate
    cand.parent.mkdir(parents=True, exist_ok=True)
    cand.write_bytes(evidence_text(repo.head(), command=f"git {marker}").encode("utf-8"))
    repo.write_plan([batch(bid)])
    res = repo.run()
    assert res.returncode == 0, res.stdout + res.stderr
    rows = contract_rows(res.stdout)
    assert len(rows) == 1 and rows[0][0] == "UNKNOWN" and rows[0][2] == "evidence", rows
    assert marker not in res.stdout + res.stderr


def test_bdd_22_unsafe_batch_id_print_form_is_machine_readable(tmp_path):
    repo = MvwuRepo(tmp_path)
    ids = ["a b", "x|y", "../e", "ok-1.2_3", ""]
    repo.write_plan([batch(i) for i in ids])
    repo.write_evidence("ok-1.2_3")
    res = repo.run()
    assert res.returncode == 0, res.stdout + res.stderr
    lines = out_lines(res.stdout)
    assert lines == [
        "MVWU_RESULT: UNKNOWN batch=a\\x20b reason=evidence",
        "MVWU_RESULT: UNKNOWN batch=x\\x7cy reason=evidence",
        "MVWU_RESULT: UNKNOWN batch=..\\x2fe reason=evidence",
        "MVWU_RESULT: PASS batch=ok-1.2_3",
        "MVWU_RESULT: UNKNOWN batch=? reason=evidence",
    ]
    for line in lines:
        assert len(line.split()) in (3, 4)


@pytest.mark.parametrize(
    "raw_id,token",
    [
        ("a b", "a\\x20b"),
        ("x|y", "x\\x7cy"),
        ("../e", "..\\x2fe"),
        ("a\\b", "a\\x5cb"),
        ("é", "\\xc3\\xa9"),
        ("", "?"),
        (5, "?"),
        (None, "?"),
    ],
    ids=["space", "pipe", "dotdot-slash", "backslash", "non-ascii-utf8-bytes", "empty", "int-id", "null-id"],
)
def test_bdd_22_unsafe_id_encoding_equivalence_classes(tmp_path, raw_id, token):
    repo = MvwuRepo(tmp_path)
    repo.write_plan([batch(raw_id)])
    assert repo.rows() == [("UNKNOWN", token, "evidence")]


@pytest.mark.parametrize(
    "exit_code",
    ["__missing__", "ok", "", "1.5"],
    ids=["missing", "non-integer-word", "empty", "float"],
)
def test_bdd_23_check4_exit_code_missing_or_non_integer_is_unknown(tmp_path, exit_code):
    repo = MvwuRepo(tmp_path)
    val = None if exit_code == "__missing__" else exit_code
    assert one(repo, exit_code=val) == ("UNKNOWN", "A", "exit_code")


@pytest.mark.parametrize(
    "case",
    ["nonexistent-full-sha", "short-sha", "branch-name", "HEAD", "missing-key"],
)
def test_bdd_24_check5_git_head_invalid_is_unknown_even_when_green(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    real = repo.head()
    head = {
        "nonexistent-full-sha": LEGACY_HEAD,
        "short-sha": real[:7],
        "branch-name": "main",
        "HEAD": "HEAD",
        "missing-key": None,
    }[case]
    assert one(repo, exit_code="0", git_head=head) == ("UNKNOWN", "A", "git_head")


def test_bdd_24_check5_task_dir_outside_git_repo_is_unknown(tmp_path):
    repo = MvwuRepo(tmp_path)
    plain = tmp_path / "plain" / "T1"
    write_plan(plain, [batch("A")])
    write_evidence(plain, "A", git_head=repo.head())
    res = repo.run(target=plain, cwd=tmp_path)
    assert res.returncode == 0, res.stdout + res.stderr
    assert contract_rows(res.stdout) == [("UNKNOWN", "A", "git_head")]


def test_bdd_24_check5_uppercase_full_sha_is_valid(tmp_path):
    repo = MvwuRepo(tmp_path)
    assert one(repo, git_head=repo.head().upper()) == ("PASS", "A", None)


# ================================================================ 四态 verdict


def test_bdd_25_verdict_pass(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {"exit_code": "0"})])
    res = repo.run()
    assert out_lines(res.stdout) == ["MVWU_RESULT: PASS batch=A"]


def test_bdd_26_verdict_fail_nonzero_exit_without_expected_red(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {"exit_code": "1", "expected_red": "[]"})])
    res = repo.run()
    assert out_lines(res.stdout) == ["MVWU_RESULT: FAIL batch=A"]


def test_bdd_27_verdict_fail_unexpected_red(tmp_path):
    repo = MvwuRepo(tmp_path)
    got = one(
        repo,
        exit_code="1",
        expected_red='["t/a.py::t_a"]',
        failed_tests='["t/a.py::t_a", "t/a.py::t_b"]',
    )
    assert got == ("FAIL", "A", None)


def test_bdd_28_verdict_expected_red(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (
                batch("A"),
                {
                    "exit_code": "1",
                    "expected_red": '["t/a.py::t_a", "t/a.py::t_b"]',
                    "failed_tests": '["t/a.py::t_a"]',
                },
            )
        ]
    )
    res = repo.run()
    assert out_lines(res.stdout) == ["MVWU_RESULT: EXPECTED_RED batch=A"]


@pytest.mark.parametrize("failed_tests", [None, "[]"], ids=["failed-tests-missing", "failed-tests-empty"])
def test_bdd_29_expected_red_not_verifiable_is_unknown_not_guessed(tmp_path, failed_tests):
    repo = MvwuRepo(tmp_path)
    got = one(repo, exit_code="1", expected_red='["t/a.py::t_a"]', failed_tests=failed_tests)
    assert got == ("UNKNOWN", "A", "expected_red")


@pytest.mark.parametrize(
    "expected_red,failed_tests",
    [
        ('["tests/a/test_x.py::test_x[a,b-1]", "tests/a/test_y.py::test_y"]', '["tests/a/test_x.py::test_x[a,b-1]"]'),
        (r'["t/a.py::t[\"q\"]"]', r'["t/a.py::t[\"q\"]"]'),
        (r'["t/a.py::t[a\\b]"]', r'["t/a.py::t[a\\b]"]'),
    ],
    ids=["comma-and-brackets-in-param-id", "escaped-double-quote", "escaped-backslash"],
)
def test_bdd_30_quoted_node_ids_with_commas_brackets_parse_correctly(tmp_path, expected_red, failed_tests):
    repo = MvwuRepo(tmp_path)
    got = one(repo, exit_code="1", expected_red=expected_red, failed_tests=failed_tests)
    assert got == ("EXPECTED_RED", "A", None)


def test_bdd_31_element_equality_is_exact_node_id(tmp_path):
    repo = MvwuRepo(tmp_path)
    got = one(
        repo,
        exit_code="1",
        expected_red='["tests/a/test_x.py::test_x[a,b-1]"]',
        failed_tests='["tests/a/test_x.py::test_x[a,b-2]"]',
    )
    assert got == ("FAIL", "A", None)


@pytest.mark.parametrize(
    "expected_red,failed_tests,exit_code",
    [
        ("t_a", "[]", "1"),
        ("t_a", "[]", "0"),
        ("[t_a, ", "[]", "1"),
        ("[1, 2]", "[]", "0"),
        ("[]", "t_a", "1"),
        ("[]", "[1, 2]", "0"),
    ],
    ids=[
        "bare-scalar-exit1",
        "bare-scalar-exit0",
        "unclosed-flow-seq",
        "non-string-elements-expected-red",
        "bare-scalar-failed-tests",
        "non-string-elements-failed-tests",
    ],
)
def test_bdd_32_unparseable_expected_red_or_failed_tests_is_unknown(tmp_path, expected_red, failed_tests, exit_code):
    repo = MvwuRepo(tmp_path)
    got = one(repo, exit_code=exit_code, expected_red=expected_red, failed_tests=failed_tests)
    assert got == ("UNKNOWN", "A", "expected_red")


def test_bdd_33_exit_zero_with_nonempty_failed_tests_is_unknown_exit_code(tmp_path):
    repo = MvwuRepo(tmp_path)
    got = one(repo, exit_code="0", failed_tests='["t/a.py::t_a"]')
    assert got == ("UNKNOWN", "A", "exit_code")


def test_bdd_34_multi_fault_reason_uses_fixed_order(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (bare_batch("P"), None),
            (batch("Q"), {"command": BAD_CMD, "exit_code": "ok"}),
            (batch("R"), {"exit_code": "ok", "git_head": LEGACY_HEAD}),
            (batch("S"), {"git_head": LEGACY_HEAD, "expected_red": "[t_a, "}),
            (batch("dup"), {}),
            (batch("dup"), {}),
        ]
    )
    assert repo.rows() == [
        ("UNKNOWN", "P", "tests_filter"),
        ("UNKNOWN", "Q", "command"),
        ("UNKNOWN", "R", "exit_code"),
        ("UNKNOWN", "S", "git_head"),
        ("UNKNOWN", "dup", "evidence"),
        ("UNKNOWN", "dup", "evidence"),
    ]


def test_bdd_35_unknown_is_never_pass_and_documents_it(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (bare_batch("b14"), {}),
            (batch("b15"), {"command": BAD_CMD}),
            (batch("b20"), None),
            (batch("../b21"), None),
            (batch("b23"), {"exit_code": None}),
            (batch("b24"), {"git_head": "abc1234"}),
            (batch("b29"), {"exit_code": "1", "expected_red": '["t/a.py::t_a"]', "failed_tests": None}),
        ]
    )
    res = repo.run()
    assert res.returncode == 0, res.stdout + res.stderr
    lines = out_lines(res.stdout)
    assert len(lines) == 7
    for line in lines:
        words = line.split()
        assert words[1] == "UNKNOWN", line
        assert "PASS" not in words, line
    assert "UNKNOWN 不等价于 PASS，不得作为放行依据" in doc_text(repo)


# ================================================================ exit code / 只读 / 边界输入


def test_bdd_36_every_verdict_exits_zero_without_traceback(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (batch("p"), {}),
            (batch("f"), {"exit_code": "1"}),
            (batch("e"), {"exit_code": "1", "expected_red": '["t::a"]', "failed_tests": '["t::a"]'}),
            (batch("u"), None),
        ]
    )
    for flags in ((), ("--observe",)):
        res = repo.run(*flags)
        assert res.returncode == 0, res.stdout + res.stderr
        assert "Traceback" not in res.stderr
    assert [r[0] for r in repo.rows()] == ["PASS", "FAIL", "EXPECTED_RED", "UNKNOWN"]


@pytest.mark.parametrize(
    "case",
    ["no-args", "missing-dir", "missing-dir-observe", "observe-only"],
)
def test_bdd_37_usage_or_target_error_exits_2(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    missing = str(tmp_path / "no-such-task-dir")
    if case == "no-args":
        res = repo.run(target=False)
    elif case == "missing-dir":
        res = repo.run(target=missing)
    elif case == "missing-dir-observe":
        res = repo.run("--observe", target=missing)
    else:
        res = repo.run("--observe", target=False)
    assert res.returncode == 2, res.stdout + res.stderr
    assert "MVWU_RESULT" not in res.stdout
    assert "Traceback" not in res.stderr
    assert re.search(r"usage|用法|不存在|not exist|does not exist|not found", res.stderr, re.IGNORECASE), res.stderr


@pytest.mark.parametrize("flags", [(), ("--observe",)], ids=["default", "observe"])
def test_bdd_38_read_only_no_state_written(tmp_path, flags):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {}), (batch("B"), {"exit_code": "1"}), (batch("C"), None)])
    (repo.task / ".state.yaml").write_bytes(b"task_id: T1\nphase: P4\nstatus: active\nretries: {}\n")
    (repo.task / "gate-events.jsonl").write_bytes(b'{"event": "x"}\n')
    repo.commit_all("task files")
    status_before = repo.git("status", "--porcelain")
    snap_before = snapshot(repo.root)
    res = repo.run(*flags)
    assert res.returncode == 0, res.stdout + res.stderr
    assert snapshot(repo.root) == snap_before
    assert repo.git("status", "--porcelain") == status_before


@pytest.mark.parametrize(
    "case",
    ["p2-missing", "bad-yaml", "no-dispatch-plan", "single-mode-no-batches"],
)
def test_bdd_39_no_judgeable_batch_gives_honest_unknown_line(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    p2 = repo.task / "P2-design.md"
    if case == "bad-yaml":
        p2.write_bytes(b"---\nphase: P2\ndispatch_plan: {mode: [unclosed\n---\n# x\n")
    elif case == "no-dispatch-plan":
        p2.write_bytes(b"---\nphase: P2\ntask_id: T1\n---\n# x\n")
    elif case == "single-mode-no-batches":
        p2.write_bytes(b"---\nphase: P2\ndispatch_plan: {mode: single}\n---\n# x\n")
    res = repo.run()
    assert res.returncode == 0, res.stdout + res.stderr
    assert "Traceback" not in res.stderr
    assert out_lines(res.stdout) == ["MVWU_RESULT: UNKNOWN batch=- reason=tests_filter"]


def test_bdd_39_observe_no_judgeable_batch_gives_single_row_with_dash_first_column(tmp_path):
    repo = MvwuRepo(tmp_path)
    (repo.task / "P2-design.md").write_bytes(b"---\nphase: P2\ndispatch_plan: {mode: single}\n---\n# x\n")
    rows = repo.obs(1)
    assert rows[0][COL_MVWU] == "-"


@pytest.mark.parametrize(
    "content",
    [b"", b"   \n\n", b"\xff\xfe\x00command: x\n\x80\x81\n", b"just some text\nno key value here\n"],
    ids=["empty-file", "whitespace-only", "non-utf8-bytes", "no-key-value-lines"],
)
def test_bdd_40_corrupt_evidence_is_unknown_and_does_not_crash(tmp_path, content):
    repo = MvwuRepo(tmp_path)
    repo.write_plan([batch("A"), batch("B")])
    write_evidence(repo.task, "A", raw=content)
    repo.write_evidence("B")
    assert repo.rows() == [("UNKNOWN", "A", "evidence"), ("PASS", "B", None)]


def test_bdd_41_batches_are_judged_independently(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (batch("A"), {"exit_code": "0"}),
            (batch("B"), {"exit_code": "1", "expected_red": "[]"}),
            (batch("C"), None),
        ]
    )
    assert repo.rows() == [("PASS", "A", None), ("FAIL", "B", None), ("UNKNOWN", "C", "evidence")]


def test_bdd_42_boundary_and_commit_form_do_not_affect_verdict(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    repo.commit("both", {"src/a.py": "v2\n", "src/b.py": "v2\n"})
    repo.setup(
        [
            (batch("A", output=["src/a.py"]), {"exit_code": "0"}),
            (batch("B", output=["src/b.py"]), {"exit_code": "0"}),
        ]
    )
    default_rows = repo.rows()
    assert default_rows == [("PASS", "A", None), ("PASS", "B", None)]
    obs = repo.obs(2)
    for row in obs:
        assert row[COL_VERDICT] == "PASS"
        assert row[COL_BOUND] == "UNKNOWN"
    assert [r[COL_VERDICT] for r in obs] == [r[0] for r in default_rows]


# ================================================================ --observe 各列


def test_bdd_43_observe_seven_column_rows_one_per_batch(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {}), (bare_batch("B"), {})])
    res = repo.run("--observe")
    assert res.returncode == 0, res.stdout + res.stderr
    lines = out_lines(res.stdout)
    assert len(lines) == 2
    assert all(line.startswith("|") for line in lines)
    rows = observe_rows(res.stdout, 2)
    assert rows[0][COL_MVWU] == "A" and rows[1][COL_MVWU] == "B"
    assert rows[0][COL_TF] == DEFAULT_TF
    assert rows[1][COL_TF] == "-"
    assert rows[0][COL_VERDICT] in VERDICTS and rows[1][COL_VERDICT] in VERDICTS


def test_bdd_44_observe_escapes_pipe_backtick_backslash_newline(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (batch("A", "python -m pytest tests/a -q | tail -n 5"), {}),
            (batch("B", "python -m pytest -k `x` C:\\t"), {}),
            (batch("C", "python -m pytest tests/c\n-q"), {}),
        ]
    )
    rows = repo.obs(3)  # 恰 3 行：换行未产生额外行；每行恰 7 列（由 observe_rows 断言）
    assert rows[0][COL_TF] == r"python -m pytest tests/a -q \| tail -n 5"
    assert rows[1][COL_TF] == r"python -m pytest -k \`x\` C:\\t"
    assert rows[2][COL_TF] == r"python -m pytest tests/c\n-q"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("8", "8s"),
        ("8.5", "8.5s"),
        ("0", "0s"),
        (None, "-"),
        ("abc", "-"),
        ("-1", "-"),
        ("", "-"),
    ],
    ids=["integer", "fractional-one-decimal", "zero", "missing", "not-a-number", "negative", "empty"],
)
def test_bdd_45_duration_column_from_duration_seconds(tmp_path, raw, expected):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {"duration_seconds": raw})])
    row = repo.obs(1)[0]
    assert row[COL_DUR] == expected
    assert row[COL_VERDICT] == "PASS"


def test_bdd_46_evidence_column_reflects_log_file_existence(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {}), (batch("B"), None)])
    rows = repo.obs(2)
    assert rows[0][COL_EVID] == "yes"
    assert rows[1][COL_EVID] == "no"


def _two_output_batches(repo):
    repo.setup(
        [
            (batch("A", output=["src/a.py"]), {}),
            (batch("B", output=["src/b.py"]), {}),
        ]
    )


def test_bdd_47_commit_form_per_batch(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    repo.commit("feat-a", {"src/a.py": "v2\n"})
    repo.commit("feat-b", {"src/b.py": "v2\n"})
    _two_output_batches(repo)
    rows = repo.obs(2)
    assert [r[COL_FORM] for r in rows] == ["per-batch", "per-batch"]


def test_bdd_48_commit_form_merged(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    repo.commit("feat-both", {"src/a.py": "v2\n", "src/b.py": "v2\n"})
    _two_output_batches(repo)
    rows = repo.obs(2)
    assert [r[COL_FORM] for r in rows] == ["merged", "merged"]


@pytest.mark.parametrize("case", ["no-output", "never-modified-in-range", "scattered-over-commits"])
def test_bdd_49_commit_form_unattributable_is_unknown(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    repo.commit("feat-a", {"src/a.py": "v2\n"})
    if case == "scattered-over-commits":
        repo.commit("feat-b", {"src/b.py": "v2\n"})
        repo.commit("feat-a2", {"src/a.py": "v3\n"})
    extra = {
        "no-output": {},
        "never-modified-in-range": {"output": ["src/c.py"]},
        "scattered-over-commits": {"output": ["src/a.py"]},
    }[case]
    repo.setup([(batch("A", **extra), {})])
    assert repo.obs(1)[0][COL_FORM] == "UNKNOWN"


@pytest.mark.parametrize("case", ["no-default-branch", "head-is-default-tip"])
def test_bdd_50_undeterminable_baseline_gives_unknown_and_diagnostic(tmp_path, case):
    # no-default-branch：仅有 trunk（无 origin/HEAD、无 main/master）；head-is-default-tip：HEAD 即 main 尖端，区间为空
    repo = MvwuRepo(tmp_path, branch="trunk" if case == "no-default-branch" else "main")
    repo.setup([(batch("A", output=["src/a.py"]), {})])
    res = repo.run("--observe")
    assert res.returncode == 0, res.stdout + res.stderr
    row = observe_rows(res.stdout, 1)[0]
    assert row[COL_FORM] == "UNKNOWN"
    assert row[COL_BOUND] == "UNKNOWN"
    assert row[COL_VERDICT] == "PASS"
    assert "baseline" in res.stderr


def test_bdd_51_boundary_exact_excludes_default_workspace_tasks_prefix(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    repo.setup([(batch("A", output=["src/a.py"]), {})])
    ev = (repo.task / "P4-evidence" / "A.log").read_bytes().decode("utf-8")
    repo.commit("feat-a", {"src/a.py": "v2\n", "agate-workspace/tasks/T1/P4-evidence/A.log": ev})
    row = repo.obs(1)[0]
    assert row[COL_FORM] == "per-batch"
    assert row[COL_BOUND] == "exact"


def test_bdd_52_boundary_exclusion_prefix_follows_workspace_config(tmp_path):
    repo = MvwuRepo(tmp_path, ws="my-ws")
    repo.checkout_new("feat")
    repo.setup(
        [
            (batch("A", output=["src/a.py"]), {}),
            (batch("B", output=["src/b.py"]), {}),
        ]
    )
    ev = (repo.task / "P4-evidence" / "A.log").read_bytes().decode("utf-8")
    repo.commit("feat-a", {"src/a.py": "v2\n", "my-ws/tasks/T1/P4-evidence/A.log": ev})
    repo.commit("feat-b", {"src/b.py": "v2\n", "agate-workspace/tasks/T1/note.md": "n\n"})
    rows = repo.obs(2)
    assert rows[0][COL_BOUND] == "exact"
    assert rows[1][COL_BOUND] == "mismatch"


@pytest.mark.parametrize("case", ["undeclared-file-changed", "declared-file-not-changed"])
def test_bdd_53_boundary_mismatch(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    if case == "undeclared-file-changed":
        repo.commit("feat-a", {"src/a.py": "v2\n", "config/x.yaml": "k: v\n"})
        output = ["src/a.py"]
    else:
        repo.commit("feat-a", {"src/a.py": "v2\n"})
        output = ["src/a.py", "src/b.py"]
    repo.setup([(batch("A", output=output), {})])
    row = repo.obs(1)[0]
    assert row[COL_FORM] == "per-batch"
    assert row[COL_BOUND] == "mismatch"


@pytest.mark.parametrize("case", ["merged-commit-with-output", "no-output"])
def test_bdd_54_boundary_unknown_for_merged_or_no_output(tmp_path, case):
    repo = MvwuRepo(tmp_path)
    repo.checkout_new("feat")
    if case == "merged-commit-with-output":
        repo.commit("feat-both", {"src/a.py": "v2\n", "src/b.py": "v2\n"})
        _two_output_batches(repo)
        rows = repo.obs(2)
        assert [r[COL_BOUND] for r in rows] == ["UNKNOWN", "UNKNOWN"]
    else:
        repo.commit("feat-a", {"src/a.py": "v2\n"})
        repo.setup([(batch("A"), {})])
        assert repo.obs(1)[0][COL_BOUND] == "UNKNOWN"


def test_bdd_55_observe_verdicts_match_default_and_stay_read_only(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup(
        [
            (batch("v25"), {"exit_code": "0"}),
            (batch("v26"), {"exit_code": "1", "expected_red": "[]"}),
            (batch("v27"), {"exit_code": "1", "expected_red": '["t::a"]', "failed_tests": '["t::a", "t::b"]'}),
            (batch("v28"), {"exit_code": "1", "expected_red": '["t::a", "t::b"]', "failed_tests": '["t::a"]'}),
            (batch("v29"), {"exit_code": "1", "expected_red": '["t::a"]', "failed_tests": None}),
        ]
    )
    (repo.task / ".state.yaml").write_bytes(b"task_id: T1\nphase: P4\nstatus: active\nretries: {}\n")
    repo.commit_all("task files")
    snap_before = snapshot(repo.root)
    default_verdicts = [r[0] for r in repo.rows()]
    observe_verdicts = [r[COL_VERDICT] for r in repo.obs(5)]
    assert default_verdicts == ["PASS", "FAIL", "FAIL", "EXPECTED_RED", "UNKNOWN"]
    assert observe_verdicts == default_verdicts
    assert snapshot(repo.root) == snap_before


# ================================================================ 单测自身合规（BDD-57 / BDD-58）


def test_bdd_57_test_file_covers_required_bdds_and_windows_smoke_first(tmp_path):
    assert SCRIPT.is_file(), f"被测脚本尚未实现（项目内缺失）: {SCRIPT}"
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    funcs = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
    names = " ".join(f.name + "_" for f in funcs)
    required = [4, *range(13, 56), 58]
    missing = [n for n in required if f"test_bdd_{n}_" not in names]
    assert not missing, f"缺少 BDD 用例: {missing}"
    first = funcs[0]
    marks = [ast.dump(d) for d in first.decorator_list]
    assert any("windows_smoke" in m for m in marks), marks


def test_bdd_58_windows_smoke_selects_and_passes(tmp_path):
    assert SCRIPT.is_file(), f"被测脚本尚未实现（项目内缺失）: {SCRIPT}"
    base = [sys.executable, "-m", "pytest", str(Path(__file__).resolve()), "-m", "windows_smoke", "-p", "no:cacheprovider"]
    coll = subprocess.run(
        [*base, "--collect-only", "-q"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    selected = [ln for ln in coll.stdout.splitlines() if "::" in ln]
    assert len(selected) >= 1, coll.stdout + coll.stderr
    run = subprocess.run(
        [*base, "-q"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120,
    )
    assert run.returncode == 0, run.stdout + run.stderr


# ================================================================ 补充守护（P2 §13：R9 / R10 / 覆盖键 / CRLF / 同源）


def test_supplement_symlink_escape_evidence_is_not_read(tmp_path):
    repo = MvwuRepo(tmp_path)
    outside = tmp_path / "outside.log"
    outside.write_bytes(evidence_text(repo.head()).encode("utf-8"))
    ev_dir = repo.task / "P4-evidence"
    ev_dir.mkdir()
    try:
        (ev_dir / "A.log").symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("平台不支持创建符号链接")
    repo.write_plan([batch("A")])
    assert repo.rows() == [("UNKNOWN", "A", "evidence")]


def test_supplement_unreadable_evidence_falls_back_without_traceback(tmp_path):
    if not hasattr(os, "geteuid") or os.geteuid() == 0 or os.name == "nt":
        pytest.skip("需要非 root 的 POSIX 权限语义")
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("A"), {}), (batch("B"), {})])
    log = repo.task / "P4-evidence" / "A.log"
    log.chmod(0)
    try:
        res = repo.run()
    finally:
        log.chmod(0o644)
    assert res.returncode == 0, res.stdout + res.stderr
    assert "Traceback" not in res.stderr
    assert contract_rows(res.stdout) == [("UNKNOWN", "A", "evidence"), ("PASS", "B", None)]


def test_supplement_duplicate_evidence_key_last_one_wins(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.write_plan([batch("A")])
    text = evidence_text(repo.head(), exit_code="1") + "exit_code: 0\n"
    write_evidence(repo.task, "A", raw=text.encode("utf-8"))
    assert repo.rows() == [("PASS", "A", None)]


def test_supplement_crlf_evidence_file_is_parsed(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.write_plan([batch("A")])
    text = evidence_text(repo.head(), exit_code="1", expected_red='["t::a"]', failed_tests='["t::a"]')
    write_evidence(repo.task, "A", raw=text.replace("\n", "\r\n").encode("utf-8"))
    assert repo.rows() == [("EXPECTED_RED", "A", None)]


def test_supplement_batches_match_agate_md_field_get_source(tmp_path):
    repo = MvwuRepo(tmp_path)
    repo.setup([(batch("first", "python -m pytest tests/a::x[a,b-1] -q"), {}), (bare_batch("second"), {})])
    env = dict(repo.env)
    env["FILE"] = str(repo.task / "P2-design.md")
    got = subprocess.run(
        [sys.executable, str(FIELD_GET), "dispatch_plan"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60, env=env,
    )
    assert got.returncode == 0, got.stderr
    ids = [b["id"] for b in json.loads(got.stdout)["batches"]]
    rows = repo.obs(len(ids))
    assert [r[COL_MVWU] for r in rows] == ids
    assert rows[0][COL_TF] == "python -m pytest tests/a::x[a,b-1] -q"


def doc_text(repo):
    """模块 docstring + --help 输出（口径：已知局限声明须出现在其中之一）。"""
    res = repo.run("--help")
    assert res.returncode == 0, res.stdout + res.stderr
    src = SCRIPT.read_text(encoding="utf-8")
    doc = ast.get_docstring(ast.parse(src)) or ""
    return doc + "\n" + res.stdout
