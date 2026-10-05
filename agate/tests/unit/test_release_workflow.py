# tests/unit/test_release_workflow.py — Release workflow 静态契约（TAG0037 P3 组 A，批 C2-release-workflow）
# 被测：.github/workflows/release.yml（P4 批 C2 新增；当前不存在 → 断言失败 = B 类红灯）。
# 覆盖：BDD-13（触发 / 权限 / 供应链 / 零打包逻辑 / 其余 workflow 不受影响）；P2 §6 T-8（含 cso F-14 增补）与 D-10 / D-15。
# 仅做静态契约（yaml.safe_load + 文本），不联网、不推 tag；BDD-20 的真实 CI 实跑属 P5/P6，actionlint 属 P5 降级路径，不在 P3 写。
# 注意：PyYAML 把键 `on` 解析成布尔 True——一律用 doc.get(True, doc.get("on"))。

import os
import re
import subprocess
import sys

import pytest
import yaml

import helpers_tag_repo as H

WORKFLOWS = H.REPO_ROOT / ".github" / "workflows"
RELEASE_YML = WORKFLOWS / "release.yml"
EXISTING = ("deploy-pages.yml", "docs-check.yml", "protocol-tests.yml", "site-check.yml")


def _load():
    assert RELEASE_YML.is_file(), f"缺 {RELEASE_YML.relative_to(H.REPO_ROOT)}（批 C2 待实现）"
    text = RELEASE_YML.read_text(encoding="utf-8")
    return yaml.safe_load(text), text


def _steps(doc):
    return [s for job in doc["jobs"].values() for s in job.get("steps", [])]


def _publish_step(doc):
    hits = [s for s in _steps(doc) if "gh release create" in str(s.get("run", ""))]
    assert len(hits) == 1, f"应恰有 1 个 `gh release create` 步骤，实际 {len(hits)}"
    return hits[0]


@pytest.mark.windows_smoke
def test_bdd_13_1_trigger_is_only_push_tags_v_star():
    """BDD-13 ①：触发器仅 push.tags 匹配 v*；无 branches / pull_request* / workflow_dispatch / workflow_run / schedule。"""
    doc, _ = _load()
    trig = doc.get(True, doc.get("on"))
    assert isinstance(trig, dict), f"on 应为映射，实际 {trig!r}"
    assert set(trig) == {"push"}, set(trig)
    push = trig["push"]
    assert isinstance(push, dict) and set(push) == {"tags"}, push
    assert push["tags"] == ["v*"]


def test_bdd_13_2_permissions_only_contents_write():
    """BDD-13 ②：permissions 为 contents: write 且仅此一项；任何 job 级 permissions 也不得超出。"""
    doc, _ = _load()
    assert doc["permissions"] == {"contents": "write"}
    for name, job in doc["jobs"].items():
        if "permissions" in job:
            assert job["permissions"] == {"contents": "write"}, name


def test_bdd_13_3_no_secrets_reference_only_github_token():
    """BDD-13 ③：不引用 secrets.*（仅 github.token）。"""
    _doc, text = _load()
    assert "secrets." not in text
    assert "github.token" in text


def test_bdd_13_4_zero_third_party_actions():
    """BDD-13 ④ / D-10：零 action（首选 runner 自带 gh / git / python）——任何步骤都不得有 `uses:`。"""
    doc, text = _load()
    assert not [s for s in _steps(doc) if "uses" in s]
    assert not re.search(r"^\s*-?\s*uses\s*:", text, re.M)


def test_bdd_13_workflow_contains_no_packaging_logic_only_calls_repo_script():
    """D-2 / D-3：workflow 内零打包逻辑，只调用仓库脚本 agate-release.py（build / is-prerelease / pyyaml-pin）。"""
    doc, _ = _load()
    runs = "\n".join(str(s.get("run", "")) for s in _steps(doc))
    assert "agate-release.py" in runs
    assert re.search(r"agate-release\.py\s+build\b", runs)
    assert not re.search(r"\b(tar|zip|gzip|shasum|sha256sum)\b|git\s+archive|git\s+worktree|shutil", runs), runs


def test_t8_no_expression_interpolation_in_run_scripts():
    """T-8 / cso F-14：所有 run 字符串不含 `${{`（表达式只允许出现在 env: 与 concurrency.group，杜绝脚本注入）。"""
    doc, _ = _load()
    for s in _steps(doc):
        for key, val in s.items():
            if key in ("env", "name"):
                continue
            assert "${{" not in str(val), f"步骤 {s.get('name')!r} 的 {key} 含表达式插值"
    conc = doc.get("concurrency", {})
    assert "release-" in str(conc.get("group", ""))
    assert conc.get("cancel-in-progress") is False


def test_t8_gh_token_only_in_publish_step_env():
    """T-8 / cso F-2：GH_TOKEN 只出现在 Publish 步骤的 env（其它步骤、job 级、顶层均不持有令牌）。"""
    doc, text = _load()
    publish = _publish_step(doc)
    assert "GH_TOKEN" in publish.get("env", {})
    assert str(publish["env"]["GH_TOKEN"]).replace(" ", "") == "${{github.token}}"
    holders = [s for s in _steps(doc) if "GH_TOKEN" in str(s) or "GITHUB_TOKEN" in str(s)]
    assert holders == [publish]
    assert "GH_TOKEN" not in yaml.safe_dump({k: v for k, v in doc.items() if k != "jobs"})
    for job in doc["jobs"].values():
        assert "GH_TOKEN" not in yaml.safe_dump(job.get("env", {}))
    assert text.count("GH_TOKEN") >= 1


def test_t8_multi_statement_run_blocks_start_with_strict_shell_flags():
    """T-8：含多语句的 run 首行 `set -euo pipefail`（任一步失败即整体失败，不发出半成品 Release）。"""
    doc, _ = _load()
    checked = 0
    for s in _steps(doc):
        lines = [ln.strip() for ln in str(s.get("run", "")).splitlines() if ln.strip()]
        if len(lines) > 1:
            checked += 1
            assert lines[0] == "set -euo pipefail", f"步骤 {s.get('name')!r} 首行: {lines[0]!r}"
    assert checked >= 3, "clone / deps / build / publish 至少应有 3 个多语句步骤"


def test_d15_publish_step_handles_is_prerelease_exit_codes_explicitly():
    """T-8 / cso F-10 / D-15：Publish 对 `is-prerelease` 的 rc 有 case 三分支（0 预发布 / 1 正式 / 其它显式失败），
    `gh release create` 带 --verify-tag 与 --notes-file。"""
    doc, _ = _load()
    run = str(_publish_step(doc)["run"])
    assert "is-prerelease" in run
    assert re.search(r'case\s+"?\$\{?rc\}?"?\s+in', run), "缺 case \"$rc\" in"
    assert re.search(r"\b0\)", run) and re.search(r"\b1\)", run) and re.search(r"\*\)", run)
    assert "--prerelease" in run and re.search(r"\*\)[^;]*exit", run, re.S), "其它 rc 必须显式 exit"
    assert "--verify-tag" in run and "--notes-file" in run


def test_d15_build_step_pins_source_pyyaml_and_expected_sha():
    """D-15 / cso F-2 / F-3：build 带 --expect-sha "$GITHUB_SHA"；pyyaml 经 pyyaml-pin 固定版本且 --only-binary=:all:；
    源码用 `git clone --depth 1 --branch "$TAG" -- <url>`（tag 名走环境变量，不经表达式插值）。"""
    doc, _ = _load()
    runs = "\n".join(str(s.get("run", "")) for s in _steps(doc))
    assert re.search(r'--expect-sha\s+"?\$GITHUB_SHA"?', runs)
    assert "pyyaml-pin" in runs and "--only-binary=:all:" in runs
    assert re.search(r"git clone[^\n]*--depth 1[^\n]*--branch\s+\"?\$TAG\"?[^\n]* -- ", runs)
    envs = [j.get("env", {}) for j in doc["jobs"].values()]
    assert any("TAG" in e for e in envs), "TAG 应经 job 级 env 传入"


def _tag_verify_step(doc):
    hits = [s for s in _steps(doc) if "Verify tag points to matching commit" in str(s.get("name", ""))]
    assert len(hits) == 1, f"应恰有 1 个「Verify tag points to matching commit」步骤，实际 {len(hits)}"
    return hits[0]


def test_s6_tag_verify_step_shape():
    """§6 / TAG0042 批0 评审 m-a：新 tag 指向校验步骤的静态契约。

    该步骤是「tag 打到无关提交」的**唯一机械防线**，必须有测试锁定其存在与判据形态
    （否则未来编辑可静默删除它）。
    """
    doc, _ = _load()
    step = _tag_verify_step(doc)
    run = str(step["run"])
    # 判据要素：取 tag 版本号（去 v 前缀）、抽 README badge 版本、两者相等性、CHANGELOG 版本节非空
    assert "TAG#v" in run, "须从 TAG 去掉 v 前缀得到期望版本"
    assert "badge/version-v" in run, "须从 README 抽 badge 版本"
    assert "CHANGELOG" in run, "须校验 CHANGELOG 版本节"
    # fail-closed：两处不符都必须 exit 1（不得只打 warning）
    assert run.count("exit 1") >= 2, "badge 缺失 / 不符 / CHANGELOG 空都须显式 exit 1"
    # 该步骤内联 python 校验 CHANGELOG 段落非空
    assert "版本节正文为空" in run or "版本节" in run
    assert step.get("working-directory") == "src", "须在 clone 出的源码树内判定"


def _run_tag_verify(tmp_path, run_script, tag, readme, changelog, python_exe):
    """在 tmp 目录内执行 release.yml 的 tag 校验脚本（真实 shell + python），返回 CompletedProcess。"""
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text(readme, encoding="utf-8")
    (src / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    env = dict(os.environ)
    env["TAG"] = tag
    # 脚本内用裸 `python3`；用 PATH 前置真实解释器目录的 python3 包装保证可移植
    shim = tmp_path / "shim"
    shim.mkdir()
    wrapper = shim / "python3"
    wrapper.write_text(f'#!/bin/sh\nexec "{python_exe}" "$@"\n', encoding="utf-8")
    wrapper.chmod(0o755)
    env["PATH"] = str(shim) + os.pathsep + env.get("PATH", "")
    return subprocess.run(
        ["bash", "-c", run_script],
        cwd=str(src), env=env, capture_output=True, text=True, timeout=60,
    )


@pytest.mark.skipif(sys.platform == "win32", reason="依赖 POSIX bash（仅 ubuntu 的 release note 场景）")
@pytest.mark.parametrize(
    "tag,readme,changelog,expect_rc,label",
    [
        # 正常：tag 与提交内 badge 一致，CHANGELOG 版本节有正文 ⇒ 通过
        ("v1.2.3",
         "![version](https://img.shields.io/badge/version-v1.2.3-blue)\n",
         "# Changelog\n\n## [Unreleased]\n\n## [1.2.3] - 2026-10-05\n\n### Fixed\n\n- real body\n",
         0, "match"),
        # tag 打到 badge 是旧版本的提交（正是 §6 要拦的场景）⇒ exit 1
        ("v1.2.3",
         "![version](https://img.shields.io/badge/version-v1.0.0-blue)\n",
         "# Changelog\n\n## [1.2.3] - 2026-10-05\n\n- body\n",
         1, "tag-points-at-wrong-commit"),
        # README 无 badge ⇒ exit 1
        ("v1.2.3",
         "# readme without badge\n",
         "# Changelog\n\n## [1.2.3] - 2026-10-05\n\n- body\n",
         1, "no-badge"),
        # badge 一致但 CHANGELOG 无该版本节 ⇒ exit 1
        ("v1.2.3",
         "![version](https://img.shields.io/badge/version-v1.2.3-blue)\n",
         "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n- old\n",
         1, "missing-changelog-section"),
        # badge 一致、版本节存在但正文为空 ⇒ exit 1
        ("v1.2.3",
         "![version](https://img.shields.io/badge/version-v1.2.3-blue)\n",
         "# Changelog\n\n## [1.2.3] - 2026-10-05\n\n## [1.0.0] - 2026-01-01\n\n- old\n",
         1, "empty-changelog-section"),
    ],
)
def test_s6_tag_verify_step_executes(tmp_path, python_exe, tag, readme, changelog, expect_rc, label):
    """§6 / 评审 m-a：**实跑** tag 校验步骤内联脚本，逐场景断言结论（positive + 4 负例）。

    仅静态形状不足以证明逻辑正确（评审 I-1 即「静态看着对、实跑漏判」的先例）；
    这里真跑 shell + 内联 python，覆盖 badge 一致/打错位置/缺 badge/缺节/节空 五种。
    """
    doc, _ = _load()
    run = str(_tag_verify_step(doc)["run"])
    proc = _run_tag_verify(tmp_path, run, tag, readme, changelog, python_exe)
    assert proc.returncode == expect_rc, (
        f"[{label}] 期望 rc={expect_rc} 实得 {proc.returncode}\n"
        f"stdout={proc.stdout}\nstderr={proc.stderr}"
    )
    if expect_rc == 1:
        assert "::error::" in proc.stdout, f"[{label}] 失败须给出 ::error:: 提示"


def test_bdd_13_release_job_shape():
    """基本形状：单 job、ubuntu、有超时；触发的 job 数与并发组符合设计（release-<ref>）。"""
    doc, _ = _load()
    assert len(doc["jobs"]) == 1
    job = next(iter(doc["jobs"].values()))
    assert str(job["runs-on"]).startswith("ubuntu")
    assert isinstance(job.get("timeout-minutes"), int) and job["timeout-minutes"] <= 30


def test_bdd_13_6_release_workflow_change_does_not_touch_existing_workflows():
    """BDD-13 ⑥：现有 4 个 workflow 不受影响。

    以**不可变历史证据**判定（避免"最近一次改动"式的永久假红）：引入 / 修改过 release.yml 的每个非合并提交，都没有同时改动
    这 4 个文件；release.yml 尚未提交时，退化为"工作区 / 暂存区相对 HEAD 无改动"。"""
    _load()
    paths = [f".github/workflows/{n}" for n in EXISTING]
    for n in paths:
        assert (H.REPO_ROOT / n).is_file(), n
    log = H.run_git(H.REPO_ROOT, "log", "--no-merges", "--format=%H", "--", ".github/workflows/release.yml")
    commits = [c for c in log.stdout.decode().split() if c]
    for c in commits:
        files = H.run_git(H.REPO_ROOT, "diff-tree", "--no-commit-id", "--name-only", "-r", c).stdout.decode().split()
        touched = set(files) & set(paths)
        assert not touched, f"提交 {c[:8]} 在改 release.yml 的同时改了既有 workflow: {touched}"
    # 工作区退化检查**仅在 release.yml 本身未提交时**适用（见 docstring）：那正是
    # 「引入 release.yml」的开发窗口，此时要求既有 workflow 也干净。release.yml 已提交后，
    # 上面按 commit 的不可变历史检查已完整覆盖该不变量；若此处仍无条件跑，则**任何**合法的
    # 既有 workflow 改动（如本批 m-3 文案修正）都会误红——那不是本断言要防的东西。
    release_dirty = subprocess.run(
        ["git", "-C", str(H.REPO_ROOT), "status", "--porcelain", "--",
         ".github/workflows/release.yml"],
        capture_output=True, text=True, env=H.git_env(), timeout=60,
    ).stdout.strip()
    if not release_dirty:
        return
    status = subprocess.run(
        ["git", "-C", str(H.REPO_ROOT), "status", "--porcelain", "--", *paths],
        capture_output=True,
        text=True,
        env=H.git_env(),
        timeout=60,
    )
    assert status.stdout.strip() == "", f"既有 workflow 有未提交改动:\n{status.stdout}"
