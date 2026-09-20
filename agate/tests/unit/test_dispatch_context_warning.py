# tests/unit/test_dispatch_context_warning.py — B3 dispatch-context 缺失 WARNING
# （dispatch-context-warning.bats 1 用例迁移，TAG0011 批次 10b）
# 场景等价（bats B3-warning）：AGATE_ROOT_FAKE 复制薄壳——把 scripts/ 下 25 个脚本（薄壳 +
#   被调 py + transitive 依赖）与 assets/ 整树复制到 fake 根，唯独**不复制 agate-next-card.py**
#   （pre-commit-gate.py:414-432：仅当 agate-next-card.py 不可用时才触发 B3 dispatch-context
#   缺失检查）。任务产出（P2-design.md + .state.yaml）已暂存 → 跑 pre-commit-gate.sh →
#   合并流断言 "dispatch-context"（等价 bats `[[ "$output" == *"dispatch-context"* ]]`）。

import shutil

import pytest

_FAKE_SCRIPTS = [
    "pre-commit-gate.sh",
    "resolve-entry.py",  # TAG0008：hook 薄壳经 resolve-entry 解析版本后 exec 对应 gate
    "pre-commit-gate.py",
    "agate_common.py",
    "agate_package.py",  # TAG0037（eng N-1）：agate_common 现依赖它；P4 落地前不存在时下方拷贝循环跳过
    "agate-state-get.py",
    "agate-json-get.py",
    "agate-state-yaml-check.py",
    "agate-frontmatter-check.py",
    "agate-md-field-get.py",
    "agate-gate-missing-cmds.py",
    "agate-gate-p5-count.py",
    "agate-vision-blocker.py",
    "agate-evidence-consistency.py",
    "agate-image-check.py",
    "agate-changelog-unreleased.py",
    "check-state-yaml.py",
    "check-state-transition.py",
    "check-frontmatter.py",
    "check-p6-format.py",
    "check-gate.py",
    "check-p6-provenance.py",
    "check-pruning.py",
    "check-scope-resolved.py",
    "check-retrospective.py",
    "check-changelog.py",
    "check-p6-evidence.py",
]


@pytest.mark.windows_smoke
def test_b3_warning_staged_missing_dispatch_context_warns(
    git_repo, agate_root, run_cli, bash, tmp_path
):
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")

    task_dir = repo / "agate-workspace" / "tasks" / "TAG0001"
    task_dir.mkdir(parents=True)
    (task_dir / "P2-design.md").write_text("content\n", encoding="utf-8")
    (task_dir / ".state.yaml").write_text(
        "task_id: TAG0001\nphase: P2\nstatus: active\nretries: {}\n", encoding="utf-8"
    )
    git_repo.stage("agate-workspace")

    fake = tmp_path / "agate-fake"
    fake_scripts = fake / "scripts"
    fake_scripts.mkdir(parents=True)
    for name in _FAKE_SCRIPTS:
        if name == "agate_package.py" and not (agate_root / "scripts" / name).is_file():
            continue  # TAG0037：P4 落地前该文件尚不存在（仅它可缺；其余脚本缺失仍应炸）
        shutil.copy2(agate_root / "scripts" / name, fake_scripts / name)
    shutil.copytree(agate_root / "assets", fake / "assets")

    result = run_cli(
        bash,
        str(fake_scripts / "pre-commit-gate.sh"),
        cwd=str(repo),
        env={"AGATE_ROOT": str(fake)},
    )
    assert "dispatch-context" in result.output
