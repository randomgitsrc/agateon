# tests/unit/test_tag0034_native.py — TAG0034 cli:native 各平台执行 + effort 各平台映射
#   BDD-8 / BDD-9 / BDD-10 / BDD-31 / BDD-32
#
# 被测：agate/scripts/agate_dispatch_route.py（importable helper，P4a/P4b 建）
#   - build_dispatch_command(candidate, *, ctx_path, effort_supported) -> list[str]
#       构造某候选的派发命令 argv（子进程形式）。effort_supported 为 Claude Code 能力探测结果
#       （claude --help 是否含 --effort），仅影响 claude-code 分支。
#   - resolve_native_target(candidate, *, current_model) -> dict
#       cli:native 形式解析出的目标描述（model / effort / opencode 命名 agent 名等）。
#
# TDD 红灯语义（P3）：agate_dispatch_route 模块尚未实现 → import 在测试体内触发
#   ModuleNotFoundError（项目内模块缺失 = B 类）。BDD-10 的 platform-notes.md 注明部分是
#   doc-assertion（当前红，P4 author 正文后转绿）。

import importlib
import sys

import pytest


def _mod(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    return importlib.import_module("agate_dispatch_route")


def test_bdd_8_effort_maps_to_codex_reasoning_flag(agate_scripts):
    """BDD-8：候选 {cli: codex, model: A, effort: high} → 子进程命令含
    `-c model_reasoning_effort=high`（native 形式：spawn_agent(reasoning_effort="high")）。"""
    mod = _mod(agate_scripts)
    cmd = mod.build_dispatch_command(
        {"cli": "codex", "model": "A", "effort": "high"},
        ctx_path="ctx/dispatch-context.md", effort_supported=True,
    )
    joined = " ".join(cmd)
    assert "model_reasoning_effort=high" in joined


def test_bdd_9_effort_maps_to_opencode_variant_flag(agate_scripts):
    """BDD-9：候选 {cli: opencode, model: provider/M, effort: high} → 命令含 `--variant high`
    或等价 `provider/M#high` 后缀。"""
    mod = _mod(agate_scripts)
    cmd = mod.build_dispatch_command(
        {"cli": "opencode", "model": "provider/M", "effort": "high"},
        ctx_path="ctx/dispatch-context.md", effort_supported=True,
    )
    joined = " ".join(cmd)
    assert ("--variant high" in joined) or ("provider/M#high" in joined)


def test_bdd_10_effort_claude_code_capability_probe_supported_branch(agate_scripts):
    """BDD-10（[BASELINE_CHANGE]）：候选 {cli: claude-code, model: haiku, effort: high}，
    探测到 `--effort` → 命令含 `--effort high`。"""
    mod = _mod(agate_scripts)
    cmd = mod.build_dispatch_command(
        {"cli": "claude-code", "model": "haiku", "effort": "high"},
        ctx_path="ctx/dispatch-context.md", effort_supported=True,
    )
    assert "--effort" in cmd
    assert "high" in cmd


def test_bdd_10_effort_claude_code_capability_probe_absent_branch(agate_scripts):
    """BDD-10（[BASELINE_CHANGE]）：未探测到 `--effort`（旧版本）→ 命令不含任何
    effort/reasoning flag、不报错、无非零退出；仍正常派发。"""
    mod = _mod(agate_scripts)
    cmd = mod.build_dispatch_command(
        {"cli": "claude-code", "model": "haiku", "effort": "high"},
        ctx_path="ctx/dispatch-context.md", effort_supported=False,
    )
    joined = " ".join(cmd)
    assert "--effort" not in joined
    assert "reasoning_effort" not in joined
    # 仍是一条可派发的 claude 命令
    assert any("claude" in part for part in cmd)


@pytest.mark.windows_smoke
def test_bdd_10_platform_notes_records_effort_probe(agate_root):
    """BDD-10（doc-assertion）：platform-notes.md 如实注明 Claude Code effort 按能力探测——
    「2.1.266 有 / 2.1.263 无 / 引入版本未核实」措辞（当前红，P4 author 正文后转绿）。"""
    content = (agate_root / "platform-notes.md").read_text(encoding="utf-8")
    assert "--effort" in content
    assert "能力探测" in content
    assert "引入版本未核实" in content


def test_bdd_31_native_claude_code_target_model_fully_resolved(agate_scripts):
    """BDD-31：候选 {cli: native, model: haiku}，主 Agent 在 Claude Code 平台 → 决策层算出的
    目标 model 与候选 model 经档位/别名解析后一致，且非父会话继承 model；驱动会话侧无自由裁量
    （目标 model 由决策层全量算好）。"""
    mod = _mod(agate_scripts)
    target = mod.resolve_native_target({"cli": "native", "model": "haiku"},
                                       current_model="claude-sonnet-parent")
    assert target["model"] == "haiku"
    assert target["model"] != "claude-sonnet-parent"


def test_bdd_32_native_opencode_named_subagent_indirect_route(agate_scripts):
    """BDD-32：候选 {cli: native, model: provider/M-pro}，主 Agent 在 OpenCode 平台 →
    存在 phase→预配命名 agent 的映射 + 预注册机制，使被派命名 agent 的 agents.<name>.model
    = provider/M-pro（子代理跑该配置 model，非父会话 model）。MVP 约定命名 agate-route-{tier}。"""
    mod = _mod(agate_scripts)
    target = mod.resolve_native_target(
        {"cli": "native", "model": "provider/M-pro"},
        current_model="provider/parent", platform="opencode", tier="deep",
    )
    assert target["model"] == "provider/M-pro"
    assert target["named_agent"] == "agate-route-deep"
