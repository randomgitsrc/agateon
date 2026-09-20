# agate/tests/helpers_tag_repo.py — TAG0037 P3 共享夹具模块（非测试模块，pytest 不收集；
# 与 conftest.py 同目录，pytest prepend 导入模式下所有测试文件可直接 `import helpers_tag_repo`）。
#
# 交付内容（P2-design §6 T-1 / T-2 / T-15 的夹具部分；后续 B / C 组测试复用）：
#   * make_synthetic_tag_repo(tmp)  合成上游 tag 仓库（bare，file:// 可 clone）：git plumbing（fast-import）
#                                   一次性构建，多个 tag：正常 / 更老无 agate/scripts 的畸形 tag / 缺 NOTICES 的老 tag /
#                                   预发布测试 tag / 附注 tag。blob 字节全部由本模块直接给定（不经任何 eol / 属性转换），
#                                   `.gitattributes` 含 `*.md text eol=crlf`（BDD-15 ③ 的 EOL 陷阱）。
#   * get_shared_synthetic_repo(tmp_path_factory)  会话级缓存版（只读使用！要改动 / 跑 worktree 的测试用 clone_bare 复制）
#   * make_custom_tag_repo(tmp, files, ...)  单 tag 自定义树（路径硬化 / 软链 / 子模块等畸形成员）
#   * make_pip_shim(dir)  PATH 内 `pip` 打桩（pip download 写占位 wheel、pip install 记录并成功），无网络依赖
#   * make_legacy_worktree_bundle(...)  T-2「旧行为构造器」：真实 `git worktree add` 整仓检出到 bundle/agate
#   * assert_real_bundle_layout(bundle)  BDD-11 sentinel 断言函数（新格式 bundle 通过、旧格式 AssertionError）
#   * SCRIPTS_TO_COPY  合成 tag 的 agate/scripts 内嵌的真实脚本清单——必须含 agate_package.py（eng N-1）
#
# 夹具不含任何网络依赖；所有目录都在调用方给定的 tmp 之下；不触碰真实 ~/.agate / 开发 checkout / 真实 origin。

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# AGATE_TEST_SCRIPTS_SRC：仅供 P3/P4 对照验证时把"被拷入合成 tag 的真实脚本"换成另一份实现；缺省即仓库内 agate/scripts。
REAL_SCRIPTS = Path(os.environ.get("AGATE_TEST_SCRIPTS_SRC") or (REPO_ROOT / "agate" / "scripts"))

# 合成 tag 的 agate/scripts/ 内嵌的真实脚本（存在才拷；agate_package.py / agate-release.py 在 P4 落地前尚不存在）。
# ⚠ eng N-1：agate_common.py 现 `from agate_package import agate_home`，任何拷 agate_common.py 的夹具都必须同时拷 agate_package.py。
SCRIPTS_TO_COPY = (
    "agate-install.py",
    "agate_common.py",
    "agate_package.py",
    "agate-resolve.py",
    "agate-summary.py",
    "install-offline.py",
    "agate-pack-offline.py",
    "agate-release.py",
)

# ---- 合成仓库的 tag 名（测试引用常量，不写魔法字符串） ----
MAIN_TAG = "v0.73.0"  # 轻量 tag，最高严格版本（`agate-install.py latest` 选中它）
ANNOTATED_TAG = "v0.72.5"  # 附注 tag（tag 对象 SHA != commit SHA），CHANGELOG 含 [0.72.5]
PRERELEASE_TAG = "v0.73.0-tagtest.1"  # 预发布测试 tag，CHANGELOG 仅 [Unreleased] + [0.72.0]（BDD-20 真实状态）
OLD_TAG = "v0.48.0"  # 早于任何"排除机制文件"的老 tag（无 .gitattributes）
NEWER_OLD_TAG = "v0.49.0"  # 正式 tag 但 CHANGELOG 缺 [0.49.0] 段（build 须 fail-closed）
NO_NOTICES_TAG = "v0.8.0"  # 缺 NOTICES.md 的老 tag（登记根文件缺失须容忍）
MALFORMED_TAG = "v0.1.0"  # 树内无 agate/scripts/ 的畸形 tag

# ---- 独立 oracle（刻意不 import agate_package，避免测试自证） ----
ORACLE_ROOT_FILES = ("CHANGELOG.md", "LICENSE", "NOTICES.md")
ORACLE_TOP_LEVEL = frozenset({"agate", "CHANGELOG.md", "LICENSE", "NOTICES.md"})

# CHANGELOG 段正文哨兵（BDD-14 / T-9 断言"含 / 不含"）
SENT_UNRELEASED = "SENTINEL-UNRELEASED-BODY"
SENT_0_73_0 = "SENTINEL-0.73.0-BODY"
SENT_0_72_5 = "SENTINEL-0.72.5-BODY"
SENT_0_72_0 = "SENTINEL-0.72.0-BODY"
SENT_0_48_0 = "SENTINEL-0.48.0-BODY"


class TreeEntry:
    """带模式的树条目：默认 100644；100755 可执行；120000 软链（data=目标路径）；160000 子模块（data=40 位十六进制）。"""

    def __init__(self, data, mode="100644"):
        self.data = data if isinstance(data, bytes) else data.encode("utf-8")
        self.mode = mode


def oracle_in_package(path):
    """独立 oracle：路径是否属于本体包（P1 §3.1 T-1 基线）。"""
    if isinstance(path, bytes):
        path = path.decode("utf-8", "surrogateescape")
    parts = path.split("/")
    if len(parts) == 1:
        return path in ORACLE_ROOT_FILES
    if parts[0] != "agate":
        return False
    if parts[1].casefold() == "tests":
        return False
    if "__pycache__" in parts:
        return False
    return not path.endswith((".pyc", ".pyo"))


def is_bytecode_path(rel):
    rel = str(rel).replace("\\", "/")
    return "__pycache__" in rel.split("/") or rel.endswith((".pyc", ".pyo"))


# ---------------------------------------------------------------------------
# git 基础设施
# ---------------------------------------------------------------------------

_FIXTURE_IDENT = "Fixture <fixture@example.invalid>"


def git_env(extra=None):
    """隔离的 git 环境：不读全局 / 系统配置，固定身份。"""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
        }
    )
    if extra:
        env.update(extra)
    return env


def run_git(repo, *args, input=None, check=True, env=None):
    """在 repo（bare 或 work tree）上运行 git，字节 I/O；返回 CompletedProcess。"""
    proc = subprocess.run(
        ["git", "-C", str(repo), *[str(a) for a in args]],
        input=input,
        capture_output=True,
        env=env if env is not None else git_env(),
        timeout=180,
    )
    if check and proc.returncode != 0:
        raise RuntimeError(f"git {' '.join(str(a) for a in args)} 失败: {proc.stderr.decode('utf-8', 'replace')}")
    return proc


def git_text(repo, *args):
    return run_git(repo, *args).stdout.decode("utf-8").strip()


def git_blob(repo, ref, path):
    """`git cat-file blob <ref>:<path>` 的原始字节（不受 eol / attribute 转换影响）。"""
    return run_git(repo, "cat-file", "blob", f"{ref}:{path}").stdout


def _b(path):
    return path if isinstance(path, bytes) else path.encode("utf-8")


class TagSpec:
    def __init__(self, name, files, time, annotated=False):
        self.name = name
        self.files = dict(files)
        self.time = time
        self.annotated = annotated

    def entries(self):
        """path(str) -> TreeEntry（TreeEntry 之外的值当作 100644 普通文件）。"""
        out = {}
        for path, val in self.files.items():
            out[path] = val if isinstance(val, TreeEntry) else TreeEntry(val)
        return out


def _fast_import_stream(specs):
    """把多个 TagSpec 编成一条 fast-import 流：线性历史（每个 commit deleteall 后给出完整树），blob 按内容去重。"""
    out = bytearray()
    blob_marks = {}
    counter = [0]

    def next_mark():
        counter[0] += 1
        return counter[0]

    def blob_mark(data):
        mark = blob_marks.get(data)
        if mark is None:
            mark = next_mark()
            blob_marks[data] = mark
            out.extend(b"blob\nmark :%d\ndata %d\n" % (mark, len(data)))
            out.extend(data)
            out.extend(b"\n")
        return mark

    for spec in specs:
        entries = spec.entries()
        marks = {path: blob_mark(e.data) for path, e in entries.items() if e.mode != "160000"}
        commit_mark = next_mark()
        message = f"release {spec.name}".encode()
        out.extend(b"commit refs/heads/main\nmark :%d\n" % commit_mark)
        out.extend(b"committer %s %d +0000\n" % (_FIXTURE_IDENT.encode(), spec.time))
        out.extend(b"data %d\n" % len(message))
        out.extend(message + b"\n")
        out.extend(b"deleteall\n")
        for path in sorted(entries, key=_b):
            entry = entries[path]
            if entry.mode == "160000":
                out.extend(b"M 160000 " + entry.data + b" " + _b(path) + b"\n")
            else:
                out.extend(b"M %s :%d " % (entry.mode.encode(), marks[path]) + _b(path) + b"\n")
        out.extend(b"\n")
        if spec.annotated:
            tag_msg = f"annotated {spec.name}".encode()
            out.extend(b"tag %s\nfrom :%d\n" % (spec.name.encode(), commit_mark))
            out.extend(b"tagger %s %d +0000\n" % (_FIXTURE_IDENT.encode(), spec.time))
            out.extend(b"data %d\n" % len(tag_msg))
            out.extend(tag_msg + b"\n")
        else:
            out.extend(b"reset refs/tags/%s\nfrom :%d\n\n" % (spec.name.encode(), commit_mark))
    return bytes(out)


def build_bare_repo(bare, specs):
    """在 bare 路径建仓并导入全部 TagSpec；HEAD → main（末个 commit）。返回 bare。"""
    bare = Path(bare)
    bare.mkdir(parents=True, exist_ok=True)
    run_git(bare, "init", "--bare", "-q")
    run_git(bare, "symbolic-ref", "HEAD", "refs/heads/main")
    if any(_has_dangerous_component(path) for spec in specs for path in spec.files):
        # 含 `.git` / `..` 等危险分量：新版 git（>= 2.4x 系列，CI runner 为 2.55）的 fast-import 写树时拒绝，
        # 改用对象层 plumbing（hash-object --literally 不做 fsck 路径校验）直接落盘。
        _plumbing_import(bare, specs)
        return bare
    try:
        run_git(bare, "fast-import", "--quiet", input=_fast_import_stream(specs))
    except RuntimeError:
        # 兜底：fast-import 拒绝其它新版才校验的路径时，同样回落到 plumbing 构建（旧 git 上不会走到这里）。
        _plumbing_import(bare, specs)
    return bare


def _has_dangerous_component(path):
    """路径含新版 git 会在写树阶段拒绝的分量：`.git`（大小写不敏感）/ `.` / `..` / 空分量。"""
    return any(part.lower() in (b".git", b".", b"..", b"") for part in _b(path).split(b"/"))


def _write_object(bare, kind, data):
    """`git hash-object -w -t <kind> --literally --stdin`：原样写入对象字节（不经 fsck / 路径校验），返回 40 位十六进制 sha。"""
    proc = run_git(bare, "hash-object", "-w", "-t", kind, "--literally", "--stdin", input=data)
    return proc.stdout.decode("ascii").strip()


def _tree_sort_key(item):
    name, (mode, _sha) = item
    return name + b"/" if mode == b"40000" else name


def _write_tree(bare, node, blob_shas):
    """node = {name(bytes): TreeEntry | dict(子目录)}；递归写 tree 对象，条目按 git 顺序（目录名视作带尾部 '/'）序列化。"""
    items = {}
    for name, child in node.items():
        if isinstance(child, dict):
            items[name] = (b"40000", _write_tree(bare, child, blob_shas))
        else:
            mode = child.mode.encode("ascii")
            sha = child.data.decode("ascii") if mode == b"160000" else blob_shas[child.data]
            items[name] = (mode, sha)
    raw = b"".join(
        mode + b" " + name + b"\0" + bytes.fromhex(sha) for name, (mode, sha) in sorted(items.items(), key=_tree_sort_key)
    )
    return _write_object(bare, "tree", raw)


def _plumbing_import(bare, specs):
    """与 _fast_import_stream 语义等价的对象层构建：每个 spec 一个 commit（线性历史），轻量 / 附注 tag，HEAD 指向 main。"""
    blob_shas = {}
    parent = None
    for spec in specs:
        root = {}
        for path, entry in spec.entries().items():
            if entry.mode != "160000" and entry.data not in blob_shas:
                blob_shas[entry.data] = _write_object(bare, "blob", entry.data)
            parts = _b(path).split(b"/")
            node = root
            for part in parts[:-1]:
                node = node.setdefault(part, {})
            node[parts[-1]] = entry
        tree_sha = _write_tree(bare, root, blob_shas)
        ident = b"%s %d +0000" % (_FIXTURE_IDENT.encode(), spec.time)
        head = b"tree %s\n" % tree_sha.encode()
        if parent:
            head += b"parent %s\n" % parent.encode()
        commit = head + b"author %s\ncommitter %s\n\nrelease %s\n" % (ident, ident, spec.name.encode())
        parent = _write_object(bare, "commit", commit)
        ref = f"refs/tags/{spec.name}"
        if spec.annotated:
            tag = b"object %s\ntype commit\ntag %s\ntagger %s\n\nannotated %s\n" % (
                parent.encode(),
                spec.name.encode(),
                ident,
                spec.name.encode(),
            )
            run_git(bare, "update-ref", ref, _write_object(bare, "tag", tag))
        else:
            run_git(bare, "update-ref", ref, parent)
    run_git(bare, "update-ref", "refs/heads/main", parent)


def clone_bare(src, dest, hardlinks=False):
    """独立复制一份 bare 仓库（默认不与 src 共享对象，避免写入污染共享夹具）；hardlinks=True 用于克隆大型真实仓库（只读用途）。"""
    mode = "--local" if hardlinks else "--no-hardlinks"
    run_git(Path(src).parent, "clone", "--bare", mode, "-q", str(src), str(dest))
    return Path(dest)


# ---------------------------------------------------------------------------
# 合成 tag 仓库
# ---------------------------------------------------------------------------


def changelog_text(sections):
    """按 Keep-a-Changelog 风格生成 CHANGELOG：sections = [(标题, 正文哨兵)]；尾部带链接定义行。"""
    lines = ["# Changelog", "", "All notable changes.", ""]
    for title, sentinel in sections:
        head = "## [Unreleased]" if title == "Unreleased" else f"## [{title}] - 2026-09-20"
        lines += [head, "", "### Added", f"- {sentinel}", ""]
    for title, _s in sections:
        lines.append(f"[{title}]: https://example.invalid/compare/{title}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def _real_script_files():
    out = {}
    for name in SCRIPTS_TO_COPY:
        src = REAL_SCRIPTS / name
        if src.is_file():
            out[f"agate/scripts/{name}"] = src.read_bytes()
    return out


def _noise_files():
    big = (b"noise-line-0123456789abcdef\n" * 8000)  # ~216KB
    return {
        "agate-workspace/tasks/TAG0001-x/P1-requirements.md": b"# task data\n" + big,
        "docs/reviews/review-1.md": b"# review\n" + big,
        "site/index.md": b"# site\n",
        "site/assets/big.bin": bytes(range(256)) * 900,
        "archived/old.md": b"# archived\n" + big,
        ".github/workflows/ci.yml": b"name: ci\non: push\njobs: {}\n",
        "HANDOFF-X.md": b"# handoff\n",
        "README.md": b"# readme\n",
        "README.zh-CN.md": b"# readme zh\n",
        "pyproject.toml": b"[tool.ruff]\n",
        "SELF-GATE.md": b"# self gate\n",
        "AGENTS.md": b"# root dev guide\n",
        "CLAUDE.md": b"# claude\n",
        "install.sh": b"#!/bin/sh\n",
        ".gitignore": b"__pycache__/\n",
        ".gitattributes": b"*.md text eol=crlf\n*.bin binary\n*.py text eol=lf\n",
    }


def _agate_body(with_scripts=True):
    files = {
        "agate/AGENTS.md": b"# agate protocol entry\n",
        "agate/WORKFLOW.md": b"# workflow\n",
        "agate/orchestrator-template.md": b"# orchestrator\n",
        "agate/UPGRADING.md": b"# upgrading\n",
        "agate/phase-cards/P1-requirements.md": b"# P1\n",
        "agate/rules/phases.yaml": b"phases: []\n",
        "agate/assets/templates/dispatch-prompt.md": b"# prompt\n",
        "agate/assets/execution-roles/analyst.md": b"# role\n",
        "agate/data.bin": b"\x00\xffAB\r\n\x01\r\n" * 40,
        "agate/tests/conftest.py": b"# tests conftest\n",
        "agate/tests/unit/test_x.py": b"def test_x():\n    pass\n",
        "agate/tests/big-fixture.txt": b"test-only-data\n" * 20000,
    }
    if with_scripts:
        files["agate/scripts/README.md"] = b"# scripts\n"
        files["agate/scripts/run.sh"] = TreeEntry(b"#!/bin/sh\necho run\n", "100755")
        files.update(_real_script_files())
    return files


def _root_files(changelog, notices=True):
    files = {"CHANGELOG.md": changelog, "LICENSE": b"MIT License\n"}
    if notices:
        files["NOTICES.md"] = b"# notices\n"
    return files


def _tracked_bytecode():
    """故意入库的字节码噪声（真实仓库跟踪数为 0，但契约要求显式排除，BDD-2 ②）。"""
    return {
        "agate/scripts/__pycache__/agate_common.cpython-312.pyc": b"\x00pyc",
        "agate/scripts/stale.pyc": b"\x00pyc",
        "agate/scripts/old.pyo": b"\x00pyo",
        "agate/assets/deep/__pycache__/m.txt": b"not-bytecode-name-but-in-pycache\n",
    }


def default_specs(extra_files=None):
    """合成仓库全部 TagSpec（按提交先后）。extra_files 追加到 MAIN_TAG 的树（BDD-3 新增未登记内容）。"""
    t0 = 1_700_000_000
    step = 100_000
    specs = []

    # 畸形 tag：树内无 agate/scripts/（BDD-24 ②）
    files = {"agate/README.md": b"# only readme\n", **_root_files(changelog_text([("Unreleased", SENT_UNRELEASED)]))}
    files.update({"docs/x.md": b"# d\n", "HANDOFF-OLD.md": b"# h\n"})
    specs.append(TagSpec(MALFORMED_TAG, files, t0))

    # 缺 NOTICES.md 的老 tag（登记根文件缺失须容忍）
    files = {**_agate_body(), **_root_files(changelog_text([("Unreleased", SENT_UNRELEASED)]), notices=False)}
    files.update({"docs/x.md": b"# d\n", "HANDOFF-OLD.md": b"# h\n", "site/index.md": b"# s\n"})
    specs.append(TagSpec(NO_NOTICES_TAG, files, t0 + step))

    # 早于"排除机制"的老 tag：无 .gitattributes、含 agate/ + 噪声顶层
    changelog = changelog_text([("Unreleased", SENT_UNRELEASED), ("0.48.0", SENT_0_48_0)])
    files = {**_agate_body(), **_root_files(changelog)}
    files.update({"docs/reviews/r.md": b"# r\n", "site/index.md": b"# s\n", "README.md": b"# r\n"})
    files.update({"agate-workspace/tasks/TAG0001-x/P1.md": b"# t\n", "archived/a.md": b"# a\n"})
    specs.append(TagSpec(OLD_TAG, files, t0 + 2 * step))

    # 较新的正式 tag，但 CHANGELOG 缺 [0.49.0] 段（build 须 fail-closed）
    changelog = changelog_text([("Unreleased", SENT_UNRELEASED), ("0.48.0", SENT_0_48_0)])
    files = {**_agate_body(), **_root_files(changelog)}
    files.update({"docs/reviews/r.md": b"# r\n", "HANDOFF-49.md": b"# h\n"})
    specs.append(TagSpec(NEWER_OLD_TAG, files, t0 + 3 * step))

    def full_tree(changelog):
        tree = {**_agate_body(), **_tracked_bytecode(), **_root_files(changelog), **_noise_files()}
        return tree

    # 附注 tag（tag 对象 SHA != commit SHA）
    changelog = changelog_text([("Unreleased", SENT_UNRELEASED), ("0.72.5", SENT_0_72_5), ("0.72.0", SENT_0_72_0)])
    specs.append(TagSpec(ANNOTATED_TAG, full_tree(changelog), t0 + 4 * step, annotated=True))

    # 预发布测试 tag：CHANGELOG 仅 [Unreleased] + [0.72.0]（BDD-20 执行时分支 CHANGELOG 的真实状态）
    changelog = changelog_text([("Unreleased", SENT_UNRELEASED), ("0.72.0", SENT_0_72_0)])
    specs.append(TagSpec(PRERELEASE_TAG, full_tree(changelog), t0 + 5 * step))

    # 主 tag（轻量）：含全部登记根文件与噪声
    changelog = changelog_text([("Unreleased", SENT_UNRELEASED), ("0.73.0", SENT_0_73_0), ("0.72.0", SENT_0_72_0)])
    main = full_tree(changelog)
    if extra_files:
        main.update(extra_files)
    specs.append(TagSpec(MAIN_TAG, main, t0 + 6 * step))
    return specs


class SyntheticTagRepo:
    """合成上游仓库句柄。bare = bare 仓库路径；url = file:// URI（AGATE_REPO_URL）。"""

    def __init__(self, bare, specs):
        self.bare = Path(bare)
        self.url = self.bare.resolve().as_uri()
        self.specs = {s.name: s for s in specs}

    def files(self, tag):
        """作者给定的原始字节：{path: bytes}（不含模式信息）。"""
        return {p: e.data for p, e in self.specs[tag].entries().items()}

    def entries(self, tag):
        return self.specs[tag].entries()

    def expected_package(self, tag):
        """独立 oracle：该 tag 应入包的相对路径集合（F_pkg）。"""
        return {p for p in self.specs[tag].files if oracle_in_package(p)}

    def commit_time(self, tag):
        return self.specs[tag].time

    def commit_sha(self, tag):
        return git_text(self.bare, "rev-parse", f"refs/tags/{tag}^{{commit}}")

    def tag_object_sha(self, tag):
        return git_text(self.bare, "rev-parse", f"refs/tags/{tag}")

    def blob(self, tag, path):
        return git_blob(self.bare, f"refs/tags/{tag}", path)


def make_synthetic_tag_repo(tmp, extra_files=None, name="upstream.git"):
    """P2 §6 T-1：在 tmp 下建合成上游 tag 仓库并返回 SyntheticTagRepo。"""
    bare = build_bare_repo(Path(tmp) / name, default_specs(extra_files))
    return SyntheticTagRepo(bare, default_specs(extra_files))


_SHARED = {}


def get_shared_synthetic_repo(tmp_path_factory):
    """会话级（每 xdist worker 进程一份）缓存的合成仓库。**只读使用**：不得对其 worktree add / 推送 / 改 ref。"""
    if "repo" not in _SHARED:
        base = tmp_path_factory.mktemp("synthetic_tag_repo")
        _SHARED["repo"] = make_synthetic_tag_repo(base)
    return _SHARED["repo"]


def make_custom_tag_repo(tmp, files, tag=MAIN_TAG, time=1_700_000_000, name="custom.git"):
    """单 tag 自定义树（畸形成员用）：files = {path(str|bytes): bytes|TreeEntry}。默认自动补 agate/scripts/README.md。"""
    files = dict(files)
    if not any(_b(p).startswith(b"agate/scripts/") for p in files):
        files["agate/scripts/README.md"] = b"# scripts\n"
    spec = TagSpec(tag, files, time)
    bare = build_bare_repo(Path(tmp) / name, [spec])
    return SyntheticTagRepo(bare, [spec])


# ---------------------------------------------------------------------------
# 子进程 / 环境 / PATH shim
# ---------------------------------------------------------------------------


def host_platform_label():
    """当前机器对应的 offline 平台标签；不支持的平台返回 None（调用方据此 skip / 换标签）。"""
    import platform as _platform

    if sys.platform == "win32":
        return "windows-x86_64"
    if _platform.machine().lower() in ("x86_64", "amd64"):
        return "linux-x86_64"
    return None


def posix_shim_supported():
    return sys.platform != "win32"


def _user_site():
    try:
        import site as _site

        cand = _site.getusersitepackages()
    except Exception:
        return None
    return cand if cand and os.path.isdir(cand) else None


def tool_env(home, agate_home=None, shim_dir=None, pip_log=None, extra=None):
    """被测脚本子进程环境：隔离 HOME、不继承 AGATE_ROOT / AGATE_HOME / 字节码开关；shim 目录置于 PATH 前部。"""
    env = dict(os.environ)
    for key in (
        "AGATE_ROOT",
        "AGATE_HOME",
        "AGATE_REPO_URL",
        "AGATE_HOOK_COPY_MODE",
        "PYTHONDONTWRITEBYTECODE",
        "AGATE_TEST_PIP_LOG",
        "AGATE_TEST_PIP_MODE",
    ):
        env.pop(key, None)
    env["HOME"] = str(home)
    env["USERPROFILE"] = str(home)
    site_dir = _user_site()
    if site_dir:
        existing = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = site_dir + os.pathsep + existing if existing else site_dir
    if agate_home is not None:
        env["AGATE_HOME"] = str(agate_home)
    if shim_dir is not None:
        env["PATH"] = str(shim_dir) + os.pathsep + env.get("PATH", "")
    if pip_log is not None:
        env["AGATE_TEST_PIP_LOG"] = str(pip_log)
    if extra:
        env.update(extra)
    return env


def run_tool(argv, env, cwd=None, timeout=240):
    """运行被测脚本，文本 I/O（UTF-8）；始终带超时。"""
    return subprocess.run(
        [str(a) for a in argv],
        cwd=str(cwd) if cwd is not None else None,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


_PIP_SHIM_PY = '''\
import json
import os
import sys

args = sys.argv[1:]
log = os.environ.get("AGATE_TEST_PIP_LOG")
if log:
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(args) + "\\n")
mode = os.environ.get("AGATE_TEST_PIP_MODE", "")
if not args:
    sys.exit(0)
if args[0] == "download":
    if mode == "fail-download":
        sys.stderr.write("pip shim: download 被注入失败\\n")
        sys.exit(1)
    dest = args[args.index("-d") + 1]
    os.makedirs(dest, exist_ok=True)
    upper = os.environ.get("AGATE_TEST_PIP_WHEEL_CASE", "lower") == "upper"
    for tok in args:
        low = tok.lower()
        if low.startswith("pyyaml"):
            ver = tok.split("==", 1)[1] if "==" in tok else "0.0.0"
            name = ("PyYAML" if upper else "pyyaml") + "-" + ver + "-py3-none-any.whl"
        elif low.startswith("pillow"):
            ver = tok.split("==", 1)[1] if "==" in tok else "0.0.0"
            name = "Pillow-" + ver + "-py3-none-any.whl"
        else:
            continue
        with open(os.path.join(dest, name), "wb") as fh:
            fh.write(b"placeholder wheel " + name.encode("utf-8") + b"\\n")
    sys.exit(0)
if args[0] == "install":
    if mode == "fail-install":
        sys.stderr.write("pip shim: install 被注入失败\\n")
        sys.exit(1)
    sys.exit(0)
sys.exit(0)
'''


def make_pip_shim(shim_dir):
    """在 shim_dir 里建 PATH 内 `pip`（POSIX sh 包装 + python 实现）。返回 shim_dir。仅 POSIX 可用（Windows 用例应先 skip）。

    行为：`pip download ... -d DIR pyyaml==X [Pillow==Y]` → 写占位 wheel（文件名大小写由 AGATE_TEST_PIP_WHEEL_CASE 控制，
    默认小写 `pyyaml-…`；upper 复现 6.0.2 的 `PyYAML-…`）；`pip install …` → exit 0；每次调用把 argv 以 JSON 行追加到
    AGATE_TEST_PIP_LOG；AGATE_TEST_PIP_MODE=fail-download|fail-install 注入失败。
    """
    shim_dir = Path(shim_dir)
    shim_dir.mkdir(parents=True, exist_ok=True)
    impl = shim_dir / "pip_shim_impl.py"
    impl.write_text(_PIP_SHIM_PY, encoding="utf-8")
    launcher = shim_dir / "pip"
    launcher.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{impl}" "$@"\n', encoding="utf-8")
    launcher.chmod(0o755)
    return shim_dir


def make_python3_wrapper(shim_dir):
    """在 shim_dir 里建 `python3` 包装（exec 当前解释器，保留 venv 语义），供执行文档中的 `python3 -B ...` 命令。"""
    shim_dir = Path(shim_dir)
    shim_dir.mkdir(parents=True, exist_ok=True)
    wrapper = shim_dir / "python3"
    wrapper.write_text(f'#!/bin/sh\nexec "{sys.executable}" "$@"\n', encoding="utf-8")
    wrapper.chmod(0o755)
    return shim_dir


def read_pip_log(log):
    log = Path(log)
    if not log.is_file():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.strip()]


# ---------------------------------------------------------------------------
# 目录快照 / tar 工具
# ---------------------------------------------------------------------------


def snapshot_tree(root, ignore_bytecode=True):
    """递归快照 {相对路径(posix): sha256 | ('link', target)}；不跟随软链；默认忽略字节码（三路径比较口径，D-13）。"""
    root = str(root)
    out = {}
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for name in list(dirnames) + filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            if ignore_bytecode and is_bytecode_path(rel):
                continue
            if os.path.islink(full):
                out[rel] = ("link", os.readlink(full))
            elif os.path.isfile(full):
                with open(full, "rb") as fh:
                    out[rel] = hashlib.sha256(fh.read()).hexdigest()
    return out


def file_set(root, ignore_bytecode=True):
    """递归**文件**相对路径集合（不含目录项，忽略字节码）。"""
    root = str(root)
    out = set()
    for dirpath, _dirs, filenames in os.walk(root, followlinks=False):
        for name in filenames:
            rel = os.path.relpath(os.path.join(dirpath, name), root).replace(os.sep, "/")
            if ignore_bytecode and is_bytecode_path(rel):
                continue
            out.add(rel)
    return out


def total_bytes(root, ignore_bytecode=True):
    total = 0
    for dirpath, _dirs, filenames in os.walk(str(root), followlinks=False):
        for name in filenames:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, str(root)).replace(os.sep, "/")
            if ignore_bytecode and is_bytecode_path(rel):
                continue
            total += os.path.getsize(full)
    return total


def expected_component_sha256(path):
    """独立 oracle：与 compute_sha256 目录约定一致——文件=内容哈希；目录=按相对 posix 路径排序逐文件 sha256 拼接再整体
    sha256（仅普通文件；调用方保证目录内无字节码）。"""
    p = Path(path)
    if p.is_dir():
        digests = [
            hashlib.sha256(f.read_bytes()).hexdigest()
            for f in sorted(p.rglob("*"), key=lambda f: f.relative_to(p).as_posix())
            if f.is_file()
        ]
        return hashlib.sha256("".join(digests).encode("utf-8")).hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def extract_tar(tar_path, dest):
    """解 tar.gz 到 dest（对 py3.8–3.12 兼容：有 filter 参数就用 data 过滤）。"""
    Path(dest).mkdir(parents=True, exist_ok=True)
    with tarfile.open(str(tar_path), "r:gz", encoding="utf-8") as tf:
        if hasattr(tarfile, "data_filter"):
            tf.extractall(str(dest), filter="data")
        else:  # pragma: no cover  (旧 Python)
            tf.extractall(str(dest))
    return Path(dest)


def sha256_of(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# T-2：旧行为构造器 + BDD-11 sentinel
# ---------------------------------------------------------------------------


def assert_real_bundle_layout(bundle):
    """BDD-11 sentinel：bundle/agate/ 必须是**本体**（含 scripts/ 与 WORKFLOW.md，不含整仓噪声 / 双层嵌套）。
    旧格式（bundle/agate 为整仓检出）上必须抛 AssertionError（T-2 变异测试依赖这一点）。"""
    agate = Path(bundle) / "agate"
    assert (agate / "scripts").is_dir(), f"bundle/agate/scripts 缺失: {agate}"
    assert (agate / "WORKFLOW.md").is_file(), f"bundle/agate/WORKFLOW.md 缺失: {agate}"
    for noise in ("agate-workspace", "docs", "site", "archived", ".github", ".git"):
        assert not (agate / noise).exists(), f"bundle/agate 内出现整仓噪声 {noise}（应为本体而非整仓树）"
    assert not (agate / "agate").exists(), "bundle/agate/agate 双层嵌套（旧格式）"


def make_legacy_worktree_bundle(tmp, upstream_bare, tag, platform, wheel_pin="6.0.3"):
    """T-2「旧行为构造器」：复现旧 packer——真实 `git worktree add` 整仓检出到 bundle/agate（自洽 manifest，无 `files`）。

    在 upstream 的独立 clone 上操作（worktree add 会写 worktrees/ 元数据，不污染共享夹具）。返回 bundle 路径。
    manifest 哈希用独立 oracle 计算，保证「旧格式但校验和自洽」（BDD-12 Given）。
    """
    tmp = Path(tmp)
    scratch = clone_bare(upstream_bare, tmp / "legacy-src.git")
    bundle = tmp / "legacy-out" / f"agate-{tag}-{platform}"
    (bundle / "wheels").mkdir(parents=True, exist_ok=True)
    run_git(scratch, "worktree", "add", "--detach", str(bundle / "agate"), tag)
    wheel = bundle / "wheels" / f"pyyaml-{wheel_pin}-py3-none-any.whl"
    wheel.write_bytes(b"placeholder wheel legacy\n")
    manifest = {
        "version": tag,
        "platform": platform,
        "components": {
            "agate": {"path": "agate", "sha256": expected_component_sha256(bundle / "agate")},
            "wheels": {"path": "wheels", "sha256": expected_component_sha256(bundle / "wheels")},
            "pyyaml": {"path": f"wheels/{wheel.name}", "sha256": sha256_of(wheel)},
        },
    }
    (bundle / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return bundle


# ---------------------------------------------------------------------------
# 项目脚本加载（被测模块尚未实现 → ModuleNotFoundError = B 类红灯）
# ---------------------------------------------------------------------------


def load_project_module(agate_scripts, filename, module_name):
    """按脚本路径加载 agate/scripts/<filename>（连字符文件名用 importlib）；缺失 → ModuleNotFoundError（B 类红灯）。"""
    import importlib.util

    path = Path(agate_scripts) / filename
    if not path.is_file():
        raise ModuleNotFoundError(f"No module named '{module_name}' (被测模块未实现: {filename})")
    cached = sys.modules.get(module_name)
    if cached is not None and getattr(cached, "__file__", None) == str(path):
        return cached
    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def copy_real_scripts(dest):
    """把 agate/scripts/*.py 拷到 dest（模拟"从版本目录 / bundle 内运行"；含 agate_package.py 若已存在）。"""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for src in sorted(REAL_SCRIPTS.glob("*.py")):
        shutil.copy2(str(src), str(dest / src.name))
    return dest


def ls_tree_sizes(repo, ref):
    """`git ls-tree -r -l -z <ref>` → [(path(str), size(int))]（仅 blob）。"""
    raw = run_git(repo, "ls-tree", "-r", "-l", "-z", "--full-tree", ref).stdout
    out = []
    for rec in raw.split(b"\0"):
        if not rec:
            continue
        meta, _tab, path = rec.partition(b"\t")
        _mode, otype, _sha, size = meta.split()
        if otype == b"blob":
            out.append((path.decode("utf-8", "surrogateescape"), int(size)))
    return out
