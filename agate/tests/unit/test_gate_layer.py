# agate/tests/unit/test_gate_layer.py
# TAG0042 批 4（关卡层分级）红灯测试 —— BDD-14 / BDD-21。
#
# 目标语义（P1 BDD-14/21，P2-design §4.3 + §1.1 M11/M12/M19）：
#   * BDD-14：关卡层按**提交类型**（纯代码 / 纯文档 / 发版）分级——按提交类型选择对应关卡集合
#     （不同类型走不同关卡），且转换表含 `paused_from`；`gate_pass_exit` / `next` / `retreat`
#     语义**不变**（避免批 0 刚修的判据回归）。
#   * BDD-21：第 4 批删除协议里的发版逻辑**之前**，先提供等价物 `preset: semver-changelog-tag`
#     （一行声明即保持现状）；声明文件缺失而仓库存在发版痕迹（CHANGELOG / 版本文件 / `v*` tag）时
#     给显眼 WARNING；`UPGRADING.md` 写明迁移方式与该硬切「未排期」+ `RM-AG0102`
#     （TAG0050 起协议不预告实施版本号）。
#
# 现行为（改动前）：`agate/rules/phases.yaml` **无**「提交类型 → 关卡集合」映射、**无**转换表 /
#   `paused_from`；协议内**无** `semver-changelog-tag` preset（仅在批 2 的 P3 测试里出现）；
#   `UPGRADING.md` **无**该迁移章节与截止版本；`agate-config.py`（批 2 新增）尚不存在
#   ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：本批红灯原因须为「被测结构/行为未实现」——`paused_from` 字面缺席、
#   phases.yaml 无分级映射、UPGRADING 无迁移章节、`agate-config.py` 缺失（本项目内文件探测 /
#   子进程运行失败 = B 类），而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 平台无关：tmp_path / task_dir / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；不写仓库内已提交文件（全在 tmp_path / git_repo）。
#
# [DESIGN_GAP]（P2-design §11 预留，见 P3-test-cases-batch4.md §2）：
#   批 4 的「提交类型 → 关卡集合」映射与转换表**具体键名设计未定** ⇒ 本文件对 BDD-14 的断言
#   落在**键名无关的可观察契约**上（结构上存在 ≥3 个提交类型各映射到 phase 集合、其中 ≥2 个集合
#   不同；转换表字面含 `paused_from`），不臆造内部键名。P4 须按 BDD 落定契约，若表示法不同则对齐本断言。

import re
import shutil

import yaml

# phases.yaml 相对协议根（agate_root fixture）的路径段（不用字符串拼接绝对路径）。
_PHASES_PARTS = ("rules", "phases.yaml")

# BDD-14「语义不变」回归基线：gate_pass_exit 现状值（改动前实测，P2 §4.3 明确不得回归）。
_EXPECTED_GATE_PASS_EXIT = {
    "P0": 2, "P1": 2, "P2": 2, "P3": 2, "P4": 0, "P5": 2,
    "P6": 2, "P6.5": 0, "P7": 0, "P8": 2,
}

# phase id 形态（含 P6.5 挂载子阶段）。
_PHASE_ID_RE = re.compile(r"^P[0-9]+(\.5)?$")


def _load_phases(agate_root):
    """加载 agate/rules/phases.yaml（数据面权威源）。"""
    return yaml.safe_load((agate_root.joinpath(*_PHASES_PARTS)).read_text(encoding="utf-8"))


def _collect_phase_set_groups(node):
    """递归收集「同一容器下 ≥3 个 phase-id 列表值」的分组（键名无关，只看结构）。

    BDD-14 要求「按提交类型选择对应关卡集合」——其可观察形态是：某个容器（dict）下
    有 ≥3 个提交类型各映射到一个 phase id 列表。本函数不假设容器/键名，只识别结构，
    从而对 BDD-14 的契约做键名无关的断言。
    """
    groups = []
    if isinstance(node, dict):
        phase_lists = []
        for value in node.values():
            if isinstance(value, (list, tuple)) and value and all(
                isinstance(x, str) and _PHASE_ID_RE.match(x) for x in value
            ):
                phase_lists.append(list(value))
        if len(phase_lists) >= 3:
            groups.append(phase_lists)
        for value in node.values():
            groups.extend(_collect_phase_set_groups(value))
    elif isinstance(node, (list, tuple)):
        for value in node:
            groups.extend(_collect_phase_set_groups(value))
    return groups


# ── BDD-14：关卡层按提交类型分级（转换表含 paused_from） ──────────────────────
#
# Given 一次提交属于某提交类型（如纯代码 / 纯文档 / 发版）
# When 关卡层判定该提交
# Then 按提交类型选择对应关卡集合（转换表可查），不同类型走不同关卡，且转换表含 paused_from


def test_bdd_14_phases_yaml_selects_gate_sets_by_commit_type(agate_root):
    """BDD-14：phases.yaml 含「提交类型 → 关卡集合」映射，且不同类型走不同关卡集合。

    Given phases.yaml（关卡层数据面权威源）
    When 解析其结构
    Then 存在一个容器，其下 ≥3 个提交类型各映射到一个 phase id 列表（关卡集合），
         且其中 ≥2 个集合**不同**（证「不同类型走不同关卡」，非同一集合换个名字）。

    现行为：phases.yaml 无该分级结构 ⇒ 红灯（结构未实现）。
    """
    data = _load_phases(agate_root)
    groups = _collect_phase_set_groups(data)
    assert groups, (
        "BDD-14：phases.yaml 须含「提交类型 → 关卡集合」映射"
        "（至少一个容器下 ≥3 个提交类型各映射到一个 phase id 列表）；当前未发现该结构"
    )
    has_distinct = any(
        len({tuple(sorted(set(grp))) for grp in group}) >= 2 for group in groups
    )
    assert has_distinct, (
        "BDD-14：不同提交类型须走**不同**关卡集合（同一容器下至少两个集合不同）；"
        f"当前各级映射集合均相同：{groups}"
    )

    # BDD-14 附加约束：分级不得改变既有 gate_pass_exit 语义（P2 §4.3「语义不变」）。
    by_id = {p["id"]: p for p in data["phases"]}
    for pid, expected in _EXPECTED_GATE_PASS_EXIT.items():
        assert by_id[pid]["gate_pass_exit"] == expected, (
            f"BDD-14：{pid} 的 gate_pass_exit 语义不得因分级改变"
            f"（期望 {expected}，实际 {by_id[pid].get('gate_pass_exit')}）"
        )


def test_bdd_14_transition_table_includes_paused_from(agate_root):
    """BDD-14：关卡层转换表**含 `paused_from`**。

    Given phases.yaml（关卡层数据面权威源）
    When 检查其转换表定义
    Then 出现 `paused_from` 字面键（转换表承载暂停来源语义）。

    现行为：全仓 `paused_from` 零命中 ⇒ 红灯（结构未实现）。
    """
    text = agate_root.joinpath(*_PHASES_PARTS).read_text(encoding="utf-8")
    assert "paused_from" in text, (
        "BDD-14：关卡层转换表须含 `paused_from`（P1 验收条件明列）；当前 phases.yaml 零命中"
    )


# ── BDD-21：删除发版逻辑前先提供等价 preset（semver-changelog-tag） ─────────
#
# Given 第 4 批将删除协议里的发版逻辑
# When 提供 `preset: semver-changelog-tag`（把现有发版检查原样搬进声明）
# Then 使用者一行声明即保持现状；文件缺失时有发版痕迹时给显眼 WARNING；
#      UPGRADING.md 写明迁移方式与截止版本


def test_bdd_21_release_preset_is_declarable(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-21：`release.preset: semver-changelog-tag` 可作为声明被接受（一行声明即保持现状）。

    Given 一份声明文件声明 `release.preset: semver-changelog-tag`
    When 运行 `agate-config validate`
    Then rc=0（该 preset 是合法、被识别的等价物，使用者一行声明即保持现状）。

    现行为：`agate-config.py` 不存在（批 2 新增）⇒ rc≠0 ⇒ 红灯（模块未实现）。
    """
    cfg = tmp_path / "agate.config.yaml"
    cfg.write_text(
        "schema_version: 1\n"
        "release:\n"
        "  preset: semver-changelog-tag\n",
        encoding="utf-8",
    )
    result = run_cli(
        python_exe, str(agate_scripts / "agate-config.py"), "validate", cwd=tmp_path
    )
    assert result.returncode == 0, (
        "BDD-21：声明 `release.preset: semver-changelog-tag` 须被 validate 接受（rc=0）；"
        f"当前 rc={result.returncode}\n{result.output[:400]}"
    )


def test_bdd_21_upgrading_documents_preset_migration_and_cutoff(agate_root):
    """BDD-21：`UPGRADING.md` 写明发版逻辑迁移（`semver-changelog-tag`），且该硬切声明为「未排期」+ RM-AG0102。

    Given agate/UPGRADING.md（迁移兼容权威文档）
    When 检查批 4 的发版逻辑删除章节
    Then 出现 `semver-changelog-tag`（迁移方式：一行声明保持现状）且该硬切「未排期」并指向 RM-AG0102。

    TAG0050 起：协议不预告实施版本号（原 TAG0042 约定「须写明截止版本」已由 RM-AG0102 承接）。
    断言限定在**批 4（关卡层分级）小节**内，避免「截止版本」字样被无关内容（历史节 / judge 截止）满足。
    """
    text = (agate_root / "UPGRADING.md").read_text(encoding="utf-8")
    start = text.index("批 4（关卡层")
    end = text.index("批 3（执行层", start)
    section = text[start:end]
    assert "semver-changelog-tag" in section, (
        "BDD-21：批 4 小节须写明发版逻辑迁移到 `preset: semver-changelog-tag`；当前零命中"
    )
    assert "未排期" in section, (
        "BDD-21：批 4 小节应声明该硬切「未排期」（TAG0050 起协议不预告实施版本号）"
    )
    assert "RM-AG0102" in section, (
        "BDD-21：批 4 小节应指向承接该欠账的 RM-AG0102"
    )


def test_bdd_21_missing_declaration_with_release_traces_warns(
    git_repo, task_dir, agate_scripts, python_exe, run_cli
):
    """BDD-21：声明文件缺失但仓库有发版痕迹时，给**显眼 WARNING**（不静默失去保护）。

    Given 一个 git 仓库有发版痕迹（CHANGELOG.md / 版本文件），但**无** `agate.config.yaml`
    When 运行 P8 gate（发版相关判定路径）
    Then 输出含指向声明缺失 / preset 迁移的显眼 WARNING（不静默通过）。

    现行为：P8 gate 只对 version/CHANGELOG/tag 出 WARNING，无声明/preset 迁移提示 ⇒ 红灯（行为未改）。

    [DESIGN_GAP]：WARNING 的具体消费入口（gate_p8 / agate-config validate / 专门检查脚本）与
    措辞由 P4 按 BDD 落定；本用例断言输出**可观察到**该 WARNING 主题（semver-changelog-tag /
    release.preset / agate.config.yaml），不绑定具体命令或精确句子。
    """
    td = task_dir()
    (td / "P8-release.md").write_text(
        "bump_type: minor\ndebt_check: none\ndelivery: package-release\n", encoding="utf-8"
    )
    repo = git_repo.path
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    git_repo.commit("init")
    shutil.copytree(td, repo / "task")

    # 发版痕迹：版本文件 + CHANGELOG（已暂存），且**无** agate.config.yaml。
    (repo / "package.json").write_text('{"version": "0.1.0"}\n', encoding="utf-8")
    (repo / "CHANGELOG.md").write_text("## [Unreleased]\n", encoding="utf-8")
    git_repo.stage("package.json")
    git_repo.stage("CHANGELOG.md")

    result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P8", "task", cwd=str(repo)
    )
    assert re.search(
        r"semver-changelog-tag|release\.preset|agate\.config\.yaml", result.output
    ), (
        "BDD-21：声明文件缺失而存在发版痕迹时，须给指向声明/preset 迁移的显眼 WARNING"
        f"（不静默）；实际输出 {result.output[:400]!r}"
    )
