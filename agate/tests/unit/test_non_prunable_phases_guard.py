# agate/tests/unit/test_non_prunable_phases_guard.py
# 等价守护（TAG0050 实施评审 A7 / ADR-014 判据单源）：
# 「不可裁剪阶段集」当前在两脚本各存一份——check-pruning.py 与 check-state-transition.py。
# 本测试防其漂移（评审实证：二者曾分叉，P1 只出现在 check-state-transition.py）。
# 平台无关：只用 pathlib + importlib；不写临时目录、不依赖外部命令。

import importlib.util
import sys
from pathlib import Path


def _load_module(name, path):
    """按路径加载脚本模块（模块级只有常量与 def，无副作用）。"""
    scripts_dir = str(Path(path).resolve().parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_non_prunable_phases_single_source(agate_scripts):
    """两脚本的不可裁剪阶段集须一致，且均含 P1（评审 A7 实证分叉点）。"""
    pruning = _load_module("_guard_check_pruning", agate_scripts / "check-pruning.py")
    trans = _load_module(
        "_guard_check_state_transition", agate_scripts / "check-state-transition.py"
    )

    assert hasattr(pruning, "NON_PRUNABLE_PHASES"), (
        "check-pruning.py 须有模块级 NON_PRUNABLE_PHASES（判据单源）"
    )
    assert hasattr(trans, "NON_PRUNABLE_PHASES"), (
        "check-state-transition.py 须有模块级 NON_PRUNABLE_PHASES（判据单源）"
    )

    pruning_set = {str(p) for p in pruning.NON_PRUNABLE_PHASES}
    trans_set = {str(p) for p in trans.NON_PRUNABLE_PHASES}
    assert pruning_set == trans_set, (
        "不可裁剪阶段集在两脚本已分叉（ADR-014 判据单源）："
        f"check-pruning={sorted(pruning_set)} vs check-state-transition={sorted(trans_set)}"
    )
    assert "P1" in pruning_set, "P1（需求基线）须在不可裁剪阶段集内（state-machine.md「不可跳过的阶段」）"
