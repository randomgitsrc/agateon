#!/usr/bin/env python3
"""agate-release.py — Release 构建 CLI（TAG0037 批 C1；P2 §3.6）

release workflow 内零打包逻辑：全部走本 CLI，因此本地（无 CI）可复现 CI 产物、可被单元测试直接调用。

子命令：
  boundary                          打印本体包边界规则（UPGRADING 契约块的生成源，== agate_package.boundary_lines()）
  pyyaml-pin                        打印 offline 包 / workflow 共用的 pyyaml 固定版本（agate_package.PYYAML_PIN）
  notes --tag T [--changelog F] --out FILE
                                    从 CHANGELOG 提取 T 的发布说明（正式 tag：缺段 / 段体为空 → exit 1 且不写文件；
                                    预发布 tag：取去后缀版本段，缺段回落 [Unreleased]，首行为预发布标注）
  is-prerelease T                   exit 0 = 预发布；exit 1 = 正式；exit 2 = 非法 tag
  build --tag T --repo R --outdir D --notes-out F [--expect-sha SHA] [--platforms p1,p2] [--skip-offline]
                                    确定性构建 agateon-<T>.tar.gz（本体）+ 每平台 offline 包 + SHA256SUMS + notes；
                                    先在暂存目录构建、全部成功后才落到 outdir（失败不留半成品）
  gate [--task TASK_DIR] [--sha SHA] [--repo DIR] [--ci-cmd CMD] [--consistency-cmd CMD]
                                    发布门（TAG0051 M11）：目标提交 CI success（fail-closed：非 success
                                    含 pending/queued/missing → 非 0）+ check-protocol-consistency.py
                                    0 ERROR +（给出 --task 时）复用 check-gate.py P8。CI/consistency
                                    查询走**可注入命令**（--ci-cmd / --consistency-cmd / 同名 env），
                                    使本地可用 fixture/mock 验证；CI 内缺省用真 `gh`（不写死分支）。
                                    发布流由项目 `agate.config.yaml` 的 `release.preset` 决定（DEBT0069
                                    的真实消费点）：声明已知流（**单源于 schema enum**，当前 =
                                    `semver-changelog-tag`）⇒ 按既有检查集；未声明 ⇒ 回落默认（不阻断）；声明未知流 ⇒ fail-closed 非 0。

发布门 fail-closed 契约（TAG0051 P4 修复轮 SEC-01 / SEC-09）：
  * required 检查列表解析为空（env `AGATE_RELEASE_REQUIRED_CHECKS` 未设**且**读不到分支保护）
    **且**目标提交零 check-run ⇒ 门**非 0**（无可校验收敛即视为未通过），并给出可操作提示——
    禁止「required 空 + 零 check-run = 静默放行」的 fail-open。
  * `--sha ""` **显式拒绝**（非 0），不得静默回退 `HEAD`（SEC-09）。
  * required 校验**信任前提**（SEC-02）：门按 check-run 的 `name` 与 required 比对，并过滤上报 App
    （缺省仅认 `github-actions`）——第三方具 `checks:write` 的已安装 App 不得以同名 check-run 冒充。
  * RM-AG0043 反查（roadmap `done`）仅在给出 `--task` 时生效：本地 runbook 门会执行；
    `release.yml` 的 backstop 步**未传** `--task` ⇒ 该反查在 CI backstop 不生效（SEC-07，见 workflow 注释）。
  * 项目声明的 `release.preset` 未知（不在已知发布流内）⇒ 门**非 0**（DEBT0069）；
    未声明则回落默认已知流、不阻断（缺该键不得 fail-closed）。

契约：Python 3.8+；stdlib-only（agate_common 仅在 build / gate 内延迟导入）；文本 I/O 显式 UTF-8；
SHA256SUMS 只防下载损坏、不认证发布者（notes 头部如实标注）。
"""

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile

# 本脚本自身不产生字节码（D-13）：须先于任何 `import agate_*`。
sys.dont_write_bytecode = True

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agate_package  # noqa: E402  stdlib-only

DEFAULT_PLATFORMS = ("linux-x86_64", "windows-x86_64")
_PACK_TIMEOUT = 900
_SECTION_HEAD_RE = re.compile(r"^## \[([^\]]+)\]")
_LINK_DEF_RE = re.compile(r"^\[[^\]]+\]:\s*\S")
_SHA_RE = re.compile(r"[0-9a-fA-F]{7,64}")

# 发布门的已知发布流 preset **不在本文件手抄**——运行时从 schema 的
# `release.preset.enum` **单源派生**（ADR-014 判据单源；见 `_known_release_presets`）。
# schema 是「哪些 preset 有效」的权威源；DEBT0069 只把该权威值消费进发布门，不新增副本。


class ReleaseError(RuntimeError):
    """发布构建失败信号（main 转 stderr + exit 1）。"""


class NotesError(ReleaseError):
    """CHANGELOG 无可用段（正式 tag 缺段 / 段体为空；预发布回落后仍缺）。"""


# ---------------------------------------------------------------------------
# notes
# ---------------------------------------------------------------------------


def _split_sections(text):
    """CHANGELOG 文本 → {段名: [行]}（段名取 `## [名]` 的方括号内容；同名首次出现优先；不含标题行）。

    `## ` 开头的任何行都结束上一段（`###` 不结束）；非 `## [x]` 形式的 `## ` 行只做分隔。
    """
    sections = {}
    current = None
    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if line.startswith("## "):
            m = _SECTION_HEAD_RE.match(line)
            if m and m.group(1) not in sections:
                current = m.group(1)
                sections[current] = []
            else:
                current = None
            continue
        if current is not None:
            sections[current].append(line)
    return sections


def _clean_body(lines):
    """去首部空行、尾部空行与 Keep-a-Changelog 链接定义行；全空 → None。"""
    body = list(lines)
    while body and (not body[-1].strip() or _LINK_DEF_RE.match(body[-1])):
        body.pop()
    while body and not body[0].strip():
        body.pop(0)
    return "\n".join(body) if body else None


def _lookup(sections, name):
    for key, lines in sections.items():
        norm = key[1:] if key.startswith("v") else key
        if norm == name:
            return _clean_body(lines)
    return None


def _header(tag, prerelease):
    lines = []
    if prerelease:
        lines += [f"预发布测试（{tag}）——非正式发布", ""]
    lines += [
        "## 下载与校验说明",
        "",
        f"- 推荐下载 `agateon-{tag}.tar.gz`（本体）：解压即得版本目录内容（`agate/` 与登记根文件）。",
        '- GitHub 自动生成的 "Source code" 压缩包是整仓（整个仓库的快照），不是安装包，请勿用于安装。',
        f"- `agateon-{tag}-offline-<平台>.tar.gz` 为离线安装包（含依赖 wheel），面向 Python 3.11。",
        "- `SHA256SUMS` 仅用于发现下载损坏，不认证发布者：它与资产同处一个 Release，发布者账号被攻破时无法防护；",
        "  需要更强保证请从 git tag 自行构建（`agate-release.py build`）后逐成员比对，或经第二渠道核对哈希。",
        "",
    ]
    return lines


def extract_notes(text, tag, wheels=None):
    """从 CHANGELOG 文本生成 `tag` 的发布说明（头部说明 + 版本段正文 [+ offline wheel 清单]）。

    正式 tag：取 `[X.Y.Z]` 段，缺段或段体为空 → NotesError（绝不回落 [Unreleased]）。
    预发布 tag：取去后缀版本段，缺段回落 `[Unreleased]`，仍缺 → NotesError；首行为预发布标注。
    `wheels`：{平台: [(wheel 文件名, sha256)]}，给出则附 offline 包内 wheel 清单。tag 非法 → ValueError。
    """
    strict, prerelease = agate_package.parse_release_ref(tag)
    sections = _split_sections(text)
    ver = strict[1:]
    body = _lookup(sections, ver)
    if body is None and prerelease:
        body = _lookup(sections, "Unreleased")
    if body is None:
        if prerelease:
            raise NotesError(f"CHANGELOG 既无 [{ver}] 段也无可用的 [Unreleased] 段（或均为空），预发布 tag {tag} 无法生成 notes")
        raise NotesError(f"CHANGELOG 缺少 [{ver}] 段（或段体为空），正式 tag {tag} 不可发布：请先在 CHANGELOG 写入该版本段")
    out = _header(tag, prerelease)
    out.append(body)
    if wheels:
        out += ["", "## offline 包内 wheel（文件名与 sha256）", ""]
        for plat in sorted(wheels):
            out.append(f"**{plat}**")
            out.append("")
            out += [f"- `{name}`  sha256 `{digest}`" for name, digest in sorted(wheels[plat])]
            out.append("")
    return "\n".join(out).rstrip("\n") + "\n"


def _write_text(path, text):
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------


def _rev_commit(repo, rev):
    return agate_package._git(repo, ["rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}"]).decode("ascii", "replace").strip()


def _check_expect_sha(repo, tag, sha):
    """两侧都剥成 commit：轻量 / 附注 tag、`GITHUB_SHA` 为 commit 或 tag 对象 SHA 均正确。"""
    if not _SHA_RE.fullmatch(sha):
        raise ReleaseError(f"--expect-sha 不是合法的十六进制 SHA: {sha!r}")
    try:
        tag_commit = _rev_commit(repo, f"refs/tags/{tag}")
        want_commit = _rev_commit(repo, sha)
    except agate_package.PackageError as exc:
        raise ReleaseError(f"无法解析 tag / SHA: {exc}") from exc
    if tag_commit != want_commit:
        raise ReleaseError(
            f"tag {tag} 指向提交 {tag_commit}，与 --expect-sha 提交 {want_commit} 不一致（tag 被移动，或来源与触发提交不一致）"
        )


def _sha256(path):
    from agate_common import compute_sha256  # 延迟导入：仅 build 需要（其顶层依赖 pyyaml）

    return compute_sha256(path)


def _build_offline(tag, repo, platform, work):
    """子进程调用 agate-pack-offline.py（-B + PYTHONDONTWRITEBYTECODE）；返回 bundle 目录。"""
    strict, _pre = agate_package.parse_release_ref(tag)
    out = os.path.join(work, f"pack-{platform}")
    os.mkdir(out)
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "agate-pack-offline.py")
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [sys.executable, "-B", script, strict, "--ref", tag, "--platform", platform, "--outdir", out, "--repo", str(repo)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env, timeout=_PACK_TIMEOUT
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"offline 打包子进程失败（{platform}）: {exc}") from exc
    if proc.returncode != 0:
        raise ReleaseError(f"offline 打包失败（{platform}, rc={proc.returncode}）: {proc.stderr.strip()}")
    bundle = os.path.join(out, f"agate-{strict}-{platform}")
    if not os.path.isdir(bundle):
        raise ReleaseError(f"offline 打包未产出预期目录: {bundle}")
    return bundle


def _is_within(path, base):
    path = os.path.realpath(path)
    base = os.path.realpath(base)
    try:
        return os.path.commonpath([path, base]) == base
    except ValueError:
        return False


def build(tag, repo, outdir, notes_out, expect_sha=None, platforms=DEFAULT_PLATFORMS, skip_offline=False):
    """确定性构建全部发布资产；失败不留半成品（先暂存、全部成功后才落到 outdir 与 notes_out）。返回资产名列表。"""
    _strict, _pre = agate_package.parse_release_ref(tag)  # 非法 → ValueError
    if not skip_offline:
        for plat in platforms:
            if plat not in DEFAULT_PLATFORMS:
                raise ValueError(f"不支持的平台标签: {plat}（应为 {' / '.join(DEFAULT_PLATFORMS)}）")
    if _is_within(notes_out, outdir):
        raise ReleaseError("--notes-out 不得位于 --outdir 内（outdir 的全部文件会被公开为 Release 资产）")
    if os.path.lexists(outdir) and (os.path.islink(outdir) or not os.path.isdir(outdir) or os.listdir(outdir)):
        raise ReleaseError(f"--outdir 已存在且非空（或不是真实目录），拒绝覆盖: {outdir}")

    if expect_sha:
        _check_expect_sha(repo, tag, expect_sha)
    try:
        entries = agate_package.list_package(repo, tag)  # 畸形 tag 在此失败（先于任何写入）
        mtime = agate_package.commit_mtime(repo, tag)
        changelog = agate_package._git(repo, ["show", f"{tag}:CHANGELOG.md"]).decode("utf-8")
    except agate_package.PackageError as exc:
        raise ReleaseError(f"无法从 {tag} 取得构建输入: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise ReleaseError(f"{tag} 的 CHANGELOG.md 不是合法 UTF-8: {exc}") from exc
    extract_notes(changelog, tag)  # fail-closed：缺段在产生任何文件前失败（wheel 清单稍后补入）

    work = tempfile.mkdtemp(prefix=".agate-release-")
    try:
        stage = os.path.join(work, "assets")
        os.mkdir(stage)
        names = []

        body_name = f"agateon-{tag}.tar.gz"
        pkg_dir = tempfile.mkdtemp(prefix="pkg-", dir=work)
        agate_package.materialize(repo, tag, pkg_dir, entries)
        agate_package.write_dir_tarball(pkg_dir, os.path.join(stage, body_name), mtime)
        names.append(body_name)

        wheels = {}
        if not skip_offline:
            for plat in platforms:
                bundle = _build_offline(tag, repo, plat, work)
                wheel_dir = os.path.join(bundle, "wheels")
                wheels[plat] = [
                    (f, _sha256(os.path.join(wheel_dir, f)))
                    for f in sorted(os.listdir(wheel_dir))
                    if f.lower().endswith(".whl")
                ]
                prefix = f"agateon-{tag}-offline-{plat}"
                agate_package.write_dir_tarball(bundle, os.path.join(stage, f"{prefix}.tar.gz"), mtime, arc_prefix=prefix)
                names.append(f"{prefix}.tar.gz")

        sums = "".join(f"{_sha256(os.path.join(stage, n))}  {n}\n" for n in sorted(names))
        _write_text(os.path.join(stage, "SHA256SUMS"), sums)
        names.append("SHA256SUMS")
        notes = extract_notes(changelog, tag, wheels=wheels)

        # 全部成功：落盘（outdir 此前不存在或为空目录）
        os.makedirs(outdir, exist_ok=True)
        for n in names:
            dst = os.path.join(outdir, n)
            shutil.move(os.path.join(stage, n), dst)
            os.chmod(dst, 0o644)  # mkstemp 产物为 0600
        _write_text(notes_out, notes)
        return sorted(names)
    finally:
        shutil.rmtree(work, ignore_errors=True)  # 仅本次 mkdtemp 创建的暂存目录


# ---------------------------------------------------------------------------
# gate（发布门，TAG0051 M11）
# ---------------------------------------------------------------------------


def _run_cmd(cmd, cwd, timeout=300):
    """按 `shlex.split` 执行命令（**无 shell**，便于注入 mock）；返回 CompletedProcess。"""
    argv = shlex.split(cmd)
    if not argv:
        raise ReleaseError("命令为空")
    try:
        return subprocess.run(
            argv, cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"命令执行失败（{cmd!r}）: {exc}") from exc


def _git_toplevel(cwd):
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=str(cwd),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise ReleaseError("无法确定仓库根（git rev-parse --show-toplevel 失败）")
    return proc.stdout.strip()


def _gh_json(sub_args, cwd):
    """`gh <args>` 输出解析为 JSON；gh 不可用 / 非 0 → ReleaseError。"""
    try:
        proc = subprocess.run(
            ["gh", *sub_args], cwd=str(cwd), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReleaseError(f"gh 执行失败（{' '.join(sub_args)}）: {exc}") from exc
    if proc.returncode != 0:
        raise ReleaseError(f"gh {' '.join(sub_args)} 失败: {proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout or "null")
    except ValueError as exc:
        raise ReleaseError(f"gh {' '.join(sub_args)} 输出非 JSON: {exc}") from exc


def _repo_slug(repo_root):
    """仓库 owner/name——经 `gh` 解析（不写死仓库 / 分支，RM-AG0116）；gh 不可用回退 origin URL。"""
    try:
        data = _gh_json(["repo", "view", "--json", "nameWithOwner"], repo_root)
        name = data.get("nameWithOwner") if isinstance(data, dict) else None
        if isinstance(name, str) and "/" in name:
            return name
    except ReleaseError:
        pass
    proc = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=str(repo_root),
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", (proc.stdout or "").strip())
    if not m:
        raise ReleaseError(f"无法解析仓库 owner/name（origin={(proc.stdout or '').strip()!r}）")
    return m.group(1)


def _required_checks(repo_root, repo):
    """required 检查名列表：env `AGATE_RELEASE_REQUIRED_CHECKS`（逗号分隔）优先，
    否则 best-effort 读分支保护（`GITHUB_TOKEN` 无 admin 权限时静默回退 `[]`，即不过滤）。

    信任前提（SEC-02）：本函数只取**名字**（`contexts`），不取上报 App；调用方 `_gh_check_runs`
    据此进一步按上报 App 过滤（缺省仅认 `github-actions`），以免第三方 App 冒名。
    漂移风险（SEC-03）：`release.yml` 内 required 列表是**硬编码**的、与分支保护可能漂移
    （新增 required 未同步 ⇒ 门不校验该项）；workflow 注释已声明「新增 required 须同步该列表」。
    """
    env_list = os.environ.get("AGATE_RELEASE_REQUIRED_CHECKS", "")
    if env_list.strip():
        return [c.strip() for c in env_list.split(",") if c.strip()]
    try:
        from agate_common import default_branch

        branch = default_branch(repo_root)
        data = _gh_json(["api", f"repos/{repo}/branches/{branch}/protection"], repo_root)
    except (ReleaseError, ValueError, ImportError, OSError):
        return []
    if not isinstance(data, dict):
        return []
    ctxs = ((data.get("required_status_checks") or {}).get("contexts")) or []
    return [c for c in ctxs if isinstance(c, str)]


def _gh_check_runs(repo_root, sha):
    """缺省 CI 查询：目标提交的 check-runs（过滤 required；缺失 required ⇒ 合成非 success 项）。

    信任边界（SEC-02）：只认**可信上报 App**（缺省 `github-actions`，可经 env
    `AGATE_RELEASE_TRUSTED_APPS` 覆盖为逗号分隔列表）——GitHub 分支保护按「name + app」判定 required，
    门若只按 name 匹配，则任意具 `checks:write` 的已安装 App 可上报同名 check-run 冒充。
    被过滤掉的上报者若其 name 恰为 required，按「缺失」合成非 success 项（fail-closed）。

    排除**当前 release run 自身**的 check-run（其 `details_url` 含 `GITHUB_RUN_ID`）——避免
    「release 作业仍在 in_progress」自指致假失败。全部结论由调用方 fail-closed 判定。
    """
    repo = _repo_slug(repo_root)
    required = _required_checks(repo_root, repo)
    data = _gh_json(["api", f"repos/{repo}/commits/{sha}/check-runs"], repo_root)
    raw = data.get("check_runs", []) if isinstance(data, dict) else []
    self_run = os.environ.get("GITHUB_RUN_ID", "")
    trusted = {
        a.strip()
        for a in os.environ.get("AGATE_RELEASE_TRUSTED_APPS", "github-actions").split(",")
        if a.strip()
    }
    out = []
    for r in raw:
        if not isinstance(r, dict):
            continue
        name = r.get("name")
        if required and name not in required:
            continue
        app_slug = (r.get("app") or {}).get("slug") if isinstance(r.get("app"), dict) else None
        if trusted and app_slug not in trusted:
            continue  # SEC-02：不认非可信 App 上报的 check-run（避免同名冒充）
        if self_run and f"/runs/{self_run}/" in str(r.get("details_url", "")):
            continue
        out.append({"name": name, "status": r.get("status"), "conclusion": r.get("conclusion")})
    if required:
        present = {r["name"] for r in out}
        for ctx in required:  # 缺失的 required 检查 ⇒ 视为非 success（fail-closed）
            if ctx not in present:
                out.append({"name": ctx, "status": "missing", "conclusion": None})
    return out


def _ci_runs(args, repo_root, sha):
    """目标提交待校验的 check-runs（list[{name,status,conclusion}]）。注入命令优先，缺省查 GitHub。"""
    cmd = args.ci_cmd or os.environ.get("AGATE_RELEASE_CI_CMD")
    if cmd:
        proc = _run_cmd(cmd, repo_root)
        if proc.returncode != 0:
            raise ReleaseError(f"CI 查询命令失败（rc={proc.returncode}）: {proc.stderr.strip()}")
        try:
            runs = json.loads(proc.stdout or "[]")
        except ValueError as exc:
            raise ReleaseError(f"CI 查询命令输出非 JSON: {exc}") from exc
        if not isinstance(runs, list):
            raise ReleaseError("CI 查询命令输出应为 JSON 数组（check-runs：[{name,status,conclusion}]）")
        return runs
    return _gh_check_runs(repo_root, sha)


def _non_success_names(runs):
    """check-runs 中结论 != success 的名称（含 None/缺失/pending/queued）。"""
    bad = []
    for r in runs:
        if not isinstance(r, dict):
            bad.append(repr(r))
        elif r.get("conclusion") != "success":
            bad.append(str(r.get("name") or "<unnamed>"))
    return bad


def _schema_path():
    """项目声明 schema 的绝对路径（`agate/rules/schema/project-config.schema.json`）。"""
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.pardir,
        "rules",
        "schema",
        "project-config.schema.json",
    )


def _known_release_presets():
    """已知发布流集合——运行时从 schema 的 `release.preset.enum` **单源派生**（ADR-014 判据单源）。

    「哪些 preset 有效」的**权威源** = `agate/rules/schema/project-config.schema.json` 的
    `release.preset.enum`；本函数**不手抄任何 preset 值**，故 schema 增删值即门行为随之变化，
    令二者**结构上不可能分叉**。schema 缺失 / 结构异常 ⇒ `ReleaseError`（fail-closed，不得
    静默回退到空集或自带副本——那会重现「无消费方 / 判据分叉」）。
    """
    path = _schema_path()
    try:
        with open(path, encoding="utf-8") as fh:
            schema = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ReleaseError(f"无法读取发布流 schema（{path}）: {exc}") from exc
    node = schema
    for key in ("properties", "release", "properties", "preset", "enum"):
        if not isinstance(node, dict):
            node = None
            break
        node = node.get(key)
    if not isinstance(node, list) or not node or not all(isinstance(v, str) for v in node):
        raise ReleaseError(f"发布流 schema 的 release.preset.enum 非法（应为非空字符串数组）: {node!r}")
    return tuple(node)


def _project_release_preset(repo_root):
    """解析项目声明的发布流 `release.preset`（DEBT0069：该键的真实消费点）。

    消费语义：
      * 声明**已知**发布流（`_known_release_presets()`，单源于 schema enum）⇒ 返回之，门按其检查集执行；
      * 声明**未知**发布流 ⇒ `ReleaseError`（fail-closed，错误信息含 preset 名）；
      * **未声明** ⇒ 回落声明层默认（`PROJECT_CONFIG_DEFAULTS`）⇒ **不阻断**、保持现行为
        （缺键不得 fail-closed）。

    解析只经 `agate_common.read_project_config`（BDD-6 唯一读取函数），不另写旁路 YAML 解析；
    「已知集」经 `_known_release_presets()` 从 schema enum 单源取（ADR-014），本处不手抄副本。
    """
    from agate_common import PROJECT_CONFIG_DEFAULTS, read_project_config  # 延迟导入：本脚本顶层 stdlib-only

    cfg = read_project_config(repo_root)
    release = cfg.get("release")
    raw = release.get("preset") if isinstance(release, dict) else None
    declared = raw is not None
    if declared:
        known = _known_release_presets()
        if not isinstance(raw, str) or raw not in known:
            raise ReleaseError(f"未知发布流（release.preset={raw!r}）；已知：{', '.join(known)}")
        preset = raw
    else:
        # 未声明（或显式 null）⇒ 回落声明层默认、不阻断（缺键不得 fail-closed）。
        preset = PROJECT_CONFIG_DEFAULTS["release"]["preset"]
    note = "" if declared else "（未声明，按默认）"
    sys.stderr.write(f"agate-release: 发布门发布流 preset={preset}{note}\n")
    return preset


def _cmd_gate(args):
    """发布门：① check-gate.py P8（给出 --task 时）② consistency 0 ERROR ③ 目标提交 CI success。

    ⓪ 先解析项目 `release.preset`（DEBT0069）：未知发布流 ⇒ 立即 fail-closed；已声明已知 /
    未声明（回落默认）⇒ 按既有检查集执行（并在 stderr 回显所用 preset，可审计）。

    fail-closed 不变量（SEC-01 / SEC-09）：
      * `--sha` 为**空串** ⇒ 显式非 0（不得 `args.sha or "HEAD"` 静默回退）；
      * 目标提交**零 check-run**（含 required 解析为空 + 无任何 check-run）⇒ 显式非 0，
        禁止「required 空 + 零 check-run = 静默放行」。
    """
    # SEC-09：显式拒绝空 sha（argparse 缺省为 HEAD，但它不是空串）
    sha = args.sha
    if sha is None or not sha.strip():
        sys.stderr.write(
            "agate-release: 发布门失败——--sha 不得为空串（显式拒绝，不回退 HEAD；"
            "请传入目标提交 SHA / HEAD）\n"
        )
        return 1

    cwd = args.repo or os.getcwd()
    try:
        repo_root = _git_toplevel(cwd)
    except ReleaseError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 1

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    # ⓪ 发布流 preset（DEBT0069：`release.preset` 的真实消费点）——未知 ⇒ fail-closed；
    #    已声明已知 / 未声明（回落默认）⇒ 按既有检查集执行。
    try:
        preset = _project_release_preset(repo_root)
    except ReleaseError as exc:
        sys.stderr.write(f"agate-release: 发布门失败——{exc}\n")
        return 1

    # ① check-gate.py P8（RM done / delivery / bump_type；判据单源）
    if args.task:
        proc = subprocess.run(
            [sys.executable, "-B", os.path.join(scripts_dir, "check-gate.py"), "P8", args.task],
            cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=120,
        )
        if proc.returncode != 2:
            sys.stderr.write(
                f"agate-release: 发布门失败——check-gate.py P8 rc={proc.returncode}（应 2）：\n"
                f"{proc.stderr.strip()}\n"
            )
            return 1

    # ② check-protocol-consistency.py 0 ERROR（CHECK 7/13）
    try:
        ccmd = args.consistency_cmd or os.environ.get("AGATE_RELEASE_CONSISTENCY_CMD")
        if ccmd:
            cproc = _run_cmd(ccmd, repo_root)
        else:
            cproc = subprocess.run(
                [sys.executable, "-B", os.path.join(scripts_dir, "check-protocol-consistency.py")],
                cwd=repo_root, capture_output=True, text=True, encoding="utf-8",
                errors="replace", timeout=_PACK_TIMEOUT,
            )
    except ReleaseError as exc:
        sys.stderr.write(f"agate-release: 发布门失败——{exc}\n")
        return 1
    if cproc.returncode != 0:
        sys.stderr.write(
            f"agate-release: 发布门失败——check-protocol-consistency.py rc={cproc.returncode}（应 0）\n"
        )
        sys.stderr.write((cproc.stderr or cproc.stdout or "")[-2000:] + "\n")
        return 1

    # ③ 目标提交 CI success（fail-closed：任一 required 非 success → 非 0）
    try:
        runs = _ci_runs(args, repo_root, sha)
    except ReleaseError as exc:
        sys.stderr.write(f"agate-release: 发布门失败——{exc}\n")
        return 1
    if not runs:
        # SEC-01：无可校验收敛即未通过。两种成因都不放行：
        #   (a) required 解析为空（env 未设 + 读不到分支保护）且目标提交零 check-run；
        #   (a') 注入的 --ci-cmd 返回空数组。
        sys.stderr.write(
            f"agate-release: 发布门失败——目标提交 {sha} 无任何可校验的 check-run（fail-closed）。\n"
            "  成因：required 检查列表解析为空（env AGATE_RELEASE_REQUIRED_CHECKS 未设，且当前令牌\n"
            "  读不到分支保护），且该提交/注入结果不含任何 check-run。\n"
            "  处理：① 确认该提交的 CI 已运行并产生 check-runs 后重跑；或\n"
            "        ② 无法读分支保护时，显式设置 AGATE_RELEASE_REQUIRED_CHECKS=<逗号分隔检查名> 后重跑。\n"
        )
        return 1
    bad = _non_success_names(runs)
    if bad:
        sys.stderr.write(
            "agate-release: 发布门失败——目标提交 CI 非 success（fail-closed，"
            f"含 pending/queued/missing）。非 success 项：{', '.join(bad)}\n"
        )
        return 1
    sys.stderr.write(f"agate-release: 发布门通过（sha={sha}，preset={preset}，CI {len(runs)} 项 success）\n")
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _default_changelog():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, os.pardir, "CHANGELOG.md")


def _cmd_notes(args):
    try:
        with open(args.changelog or _default_changelog(), "rb") as fh:
            text = fh.read().decode("utf-8")
        notes = extract_notes(text, args.tag)
    except ValueError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 2
    except (OSError, NotesError) as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 1
    _write_text(args.out, notes)
    return 0


def _cmd_is_prerelease(args):
    try:
        _strict, pre = agate_package.parse_release_ref(args.tag)
    except ValueError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 2
    return 0 if pre else 1


def _cmd_build(args):
    platforms = tuple(p for p in args.platforms.split(",") if p) if args.platforms else DEFAULT_PLATFORMS
    if not platforms:
        sys.stderr.write("agate-release: --platforms 为空\n")
        return 2
    try:
        names = build(
            args.tag, args.repo, args.outdir, args.notes_out,
            expect_sha=args.expect_sha, platforms=platforms, skip_offline=args.skip_offline,
        )
    except ValueError as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 2
    except (ReleaseError, agate_package.PackageError, OSError) as exc:
        sys.stderr.write(f"agate-release: {exc}\n")
        return 1
    for n in names:
        print(n)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="agate-release", description="agate Release 构建 CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("boundary", help="打印本体包边界规则")
    sub.add_parser("pyyaml-pin", help="打印 pyyaml 固定版本")
    p_notes = sub.add_parser("notes", help="从 CHANGELOG 提取发布说明")
    p_notes.add_argument("--tag", required=True)
    p_notes.add_argument("--changelog", default=None)
    p_notes.add_argument("--out", required=True)
    p_pre = sub.add_parser("is-prerelease", help="退出码：0 预发布 / 1 正式 / 2 非法")
    p_pre.add_argument("tag")
    p_build = sub.add_parser("build", help="确定性构建发布资产")
    p_build.add_argument("--tag", required=True)
    p_build.add_argument("--repo", required=True)
    p_build.add_argument("--outdir", required=True)
    p_build.add_argument("--notes-out", required=True)
    p_build.add_argument("--expect-sha", default=None)
    p_build.add_argument("--platforms", default=None)
    p_build.add_argument("--skip-offline", action="store_true")
    p_gate = sub.add_parser("gate", help="发布门：release.preset + CI success + consistency 0 ERROR + check-gate P8")
    p_gate.add_argument("--task", default=None, help="待发布任务目录（给出时复用 check-gate.py P8 判据）")
    p_gate.add_argument("--sha", default="HEAD", help="目标提交（默认 HEAD）")
    p_gate.add_argument("--repo", default=None, help="仓库根目录（默认当前工作目录）")
    p_gate.add_argument("--ci-cmd", default=None, help="注入的 CI 查询命令（stdout=check-runs JSON 数组）；缺省查 GitHub")
    p_gate.add_argument("--consistency-cmd", default=None, help="注入的 consistency 命令（退出码即结论）；缺省跑 check-protocol-consistency.py")
    args = parser.parse_args(argv)

    if args.cmd == "boundary":
        print("\n".join(agate_package.boundary_lines()))
        return 0
    if args.cmd == "pyyaml-pin":
        print(agate_package.PYYAML_PIN)
        return 0
    if args.cmd == "notes":
        return _cmd_notes(args)
    if args.cmd == "is-prerelease":
        return _cmd_is_prerelease(args)
    if args.cmd == "gate":
        return _cmd_gate(args)
    return _cmd_build(args)


if __name__ == "__main__":
    sys.exit(main())
