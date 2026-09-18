# tests/unit/test_agate_inject_card.py — agate-inject-card.py 注入校验
# （agate-inject-card.bats 11 用例迁移，TAG0011 批次 3）
# 被测：agate/scripts/agate-inject-card.py（把 agate-next-card.py 卡片全文注入
#       TASK_DIR 下 {PHASE}-dispatch-context-{role}.md 的 AGATE_CARD 占位块）
# 语义：注入块 sha256 == agate-next-card.py 全文 sha256（CRLF 归一化 tr -d '\r' 等价）；
#       IC_IDEMPOTENT.2 会临时改写真实 phase-cards/P3-tdd.md（try/finally 必还原，
#       等价 bats 的 cp 备份 + 恢复，bats 源注释不变）

import hashlib
import os
import shutil

import pytest

_START_MARKER = "<!-- AGATE_CARD_START -->"
_END_MARKER = "<!-- AGATE_CARD_END -->"

_ANALYST_DC = """\
---
phase: P1
generated_by: agate-inject-card.sh + 主 Agent
task_id: T001
role: analyst
---

<dispatch_guide>
### 目标
分析需求
</dispatch_guide>

<!-- AGATE_CARD_START -->
{占位}
<!-- AGATE_CARD_END -->

<objective_info>
- 环境状态：test
</objective_info>
"""

_DESIGNER_DC = """\
---
phase: P3
generated_by: agate-inject-card.sh + 主 Agent
task_id: T001
role: test-designer
---

<dispatch_guide>
### 目标
写测试用例

### 约束
基于 P2 的接口契约
</dispatch_guide>

<!-- AGATE_CARD_START -->
{占位}
<!-- AGATE_CARD_END -->

<objective_info>
- 关键标识：test
</objective_info>
"""

_SIMPLE_DC = """\
<!-- AGATE_CARD_START -->
旧
<!-- AGATE_CARD_END -->
"""

_NO_PLACEHOLDER_DC = """\
---
phase: P1
task_id: T001
role: analyst
---

<dispatch_guide>
### 目标
无占位符文件
</dispatch_guide>
"""

_MISSING_DC = """\
---
phase: P1
task_id: T001
role: analyst
---

<dispatch_guide>
### 目标
完全没有占位符
</dispatch_guide>
"""


def _make_link(src, dst):
    """平台分支：Linux 真软链；Windows（ln -sf 退化为复制）用 copytree/copy2。"""
    if os.name == "nt":
        if os.path.isdir(str(src)):
            shutil.copytree(str(src), str(dst))
        else:
            shutil.copy2(str(src), str(dst))
    else:
        os.symlink(str(src), str(dst))


def _run_inject(agate_scripts, python_exe, run_cli, tmp_path, *args, env=None):
    """跑注入工具。

    HOME 隔离（TAG0032 版本管理布局引入）：agate-inject-card.py 经 resolve_agate_root
    解析 AGATE_ROOT，解析链会查 ~/.agate 的 current/latest 指针。不隔离 HOME 时，本机
    会解析到稳定版目录（~/.agate/vX.Y.Z/agate）而非本测试所在仓库——导致"改本仓卡片 →
    断言注入哈希变化"类用例失败（卡片来自稳定版，未变）。隔离后解析链失败 → 回退脚本
    路径上溯 → 指向本仓，还原测试原意。

    env=（可选）：附加/覆盖环境变量（如 AGATE_ROOT 指向隔离假协议树）。
    """
    full = {"HOME": str(tmp_path)}
    if env:
        full.update(env)
    return run_cli(
        python_exe,
        str(agate_scripts / "agate-inject-card.py"),
        *args,
        env=full,
    )


def _between_markers(text):
    """sed -n '/START/,/END/p' | sed '1d;$d' 等价：取占位块内内容（不含标记行）。"""
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines) if _START_MARKER in line)
    end = next(i for i in range(start + 1, len(lines)) if _END_MARKER in lines[i])
    return "\n".join(lines[start + 1:end])


def _before_marker(text, marker):
    lines = text.splitlines()
    idx = next(i for i, line in enumerate(lines) if marker in line)
    return "\n".join(lines[:idx])


def _after_marker(text, marker):
    lines = text.splitlines()
    idx = next(i for i, line in enumerate(lines) if marker in line)
    return "\n".join(lines[idx + 1:])


def _sha256_utf8(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@pytest.mark.windows_smoke
def test_icb_1_block_sha256_matches_card(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    dc = task_dir / "P1-dispatch-context-analyst.md"
    dc.write_text(_ANALYST_DC, encoding="utf-8")
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert result.returncode == 0
    injected = _between_markers(dc.read_text(encoding="utf-8"))
    expected = run_cli(
        python_exe, str(agate_scripts / "agate-next-card.py"), "P1"
    ).output.rstrip("\n")
    # tr -d '\r'：Windows checkout 的 phase-cards 是 CRLF，注入文件是 LF——归一化后比 hash
    assert _sha256_utf8(injected.replace("\r", "")) == _sha256_utf8(
        expected.replace("\r", "")
    )


def test_icb_2_other_content_unchanged(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    dc = task_dir / "P3-dispatch-context-test-designer.md"
    dc.write_text(_DESIGNER_DC, encoding="utf-8")
    before_guide = _before_marker(dc.read_text(encoding="utf-8"), _START_MARKER)
    before_info = _after_marker(dc.read_text(encoding="utf-8"), _END_MARKER)
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P3", str(task_dir))
    assert result.returncode == 0
    after_guide = _before_marker(dc.read_text(encoding="utf-8"), _START_MARKER)
    after_info = _after_marker(dc.read_text(encoding="utf-8"), _END_MARKER)
    assert before_guide == after_guide
    assert before_info == after_info


def test_icb_3_multiple_role_files_all_injected(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    (task_dir / "P1-dispatch-context-analyst.md").write_text(_SIMPLE_DC, encoding="utf-8")
    (task_dir / "P1-dispatch-context-review.md").write_text(_SIMPLE_DC, encoding="utf-8")
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert result.returncode == 0
    assert "P1-dispatch-context-analyst.md" in result.output
    assert "P1-dispatch-context-review.md" in result.output
    analyst_text = (task_dir / "P1-dispatch-context-analyst.md").read_text(encoding="utf-8")
    review_text = (task_dir / "P1-dispatch-context-review.md").read_text(encoding="utf-8")
    assert "旧" not in analyst_text
    assert "旧" not in review_text


def test_icb_4_no_dispatch_context_exit_1(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task_empty"
    task_dir.mkdir()
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert result.returncode == 1
    assert "不存在" in result.output


def test_icb_5_no_args_exit_1(agate_scripts, python_exe, run_cli, tmp_path):
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path)
    assert result.returncode == 1


def test_icb_6_missing_task_dir_exit_1(agate_scripts, python_exe, run_cli, tmp_path):
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1")
    assert result.returncode == 1


def test_icb_7_legacy_format_injectable(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task"
    task_dir.mkdir()
    dc = task_dir / "P1-dispatch-context.md"
    dc.write_text(_SIMPLE_DC, encoding="utf-8")
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert result.returncode == 0
    assert "AGATE_CARD 已注入" in result.output
    assert "旧" not in dc.read_text(encoding="utf-8")


def test_icb_8_no_placeholder_exit_1(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task_no_placeholder"
    task_dir.mkdir()
    dc = task_dir / "P1-dispatch-context-analyst.md"
    dc.write_text(_NO_PLACEHOLDER_DC, encoding="utf-8")
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert result.returncode == 1
    assert ("未找到" in result.output) or ("占位符" in result.output)


def test_icb_idempotent_1_unchanged_card_exit_0(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task_idem1"
    task_dir.mkdir()
    dc = task_dir / "P1-dispatch-context-analyst.md"
    dc.write_text(_SIMPLE_DC, encoding="utf-8")
    first = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert first.returncode == 0
    second = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert second.returncode == 0
    assert "AGATE_CARD 已注入" in second.output


def test_icb_idempotent_2_changed_card_updates(
    agate_scripts, python_exe, run_cli, agate_root, tmp_path
):
    """卡片变化后重新注入 → 块内容更新（哈希变化）。

    **隔离假协议树（2026-09-18 修 flaky）**：本用例原先直接改**真实仓库**的
    `agate/phase-cards/P3-tdd.md` 再恢复——并行跑（`-n auto`）时会与同时读该文件
    算哈希的用例（test_agate_next_card.py::test_nc_cross_checkout_paths_hash_consistent）
    竞争，导致 "phase P3 hash mismatch" 的间歇失败（实测约 1/3 概率）。
    改为在 tmp_path 下建独立协议树（软链 scripts/ + 真实 rules/、可写 phase-cards/），
    经 AGATE_ROOT 指向它——不改仓库任何文件，并行安全。
    """
    task_dir = tmp_path / "task_idem2"
    task_dir.mkdir()
    dc = task_dir / "P3-dispatch-context-test-designer.md"
    dc.write_text(_SIMPLE_DC, encoding="utf-8")

    # 隔离协议树：scripts/ 软链到真实（复用被测脚本与其依赖），rules/ 复制真实，
    # phase-cards/ 为可写副本（本用例唯一需要改动的部分）
    proto = tmp_path / "proto"
    proto.mkdir()
    _make_link(agate_root / "scripts", proto / "scripts")
    shutil.copytree(str(agate_root / "rules"), str(proto / "rules"))
    (proto / "phase-cards").mkdir()
    card_src = proto / "phase-cards" / "P3-tdd.md"
    shutil.copy2(str(agate_root / "phase-cards" / "P3-tdd.md"), str(card_src))

    env = {"AGATE_ROOT": str(proto)}

    first = _run_inject(
        agate_scripts, python_exe, run_cli, tmp_path, "P3", str(task_dir), env=env
    )
    assert first.returncode == 0
    first_hash = _sha256_utf8(_between_markers(dc.read_text(encoding="utf-8")))

    with open(card_src, "a", encoding="utf-8") as fh:
        fh.write("\n## 临时测试追加内容\n")

    second = _run_inject(
        agate_scripts, python_exe, run_cli, tmp_path, "P3", str(task_dir), env=env
    )
    assert second.returncode == 0

    second_hash = _sha256_utf8(_between_markers(dc.read_text(encoding="utf-8")))
    assert first_hash != second_hash


def test_icb_missing_1_no_placeholder_exit_1(agate_scripts, python_exe, run_cli, tmp_path):
    task_dir = tmp_path / "task_missing1"
    task_dir.mkdir()
    dc = task_dir / "P1-dispatch-context-analyst.md"
    dc.write_text(_MISSING_DC, encoding="utf-8")
    result = _run_inject(agate_scripts, python_exe, run_cli, tmp_path, "P1", str(task_dir))
    assert result.returncode == 1
