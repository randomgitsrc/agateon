# agate/tests/unit/test_non_prunable_phases_guard.py
# 判据单源守护（TAG0050 评审 A7 → RM-AG0110 落地）：不可裁剪阶段集由**阶段注册表**
# `rules/phases.yaml` 的顶层键 `non_prunable_phases` 承载，`check-pruning.py` 与
# `check-state-transition.py` **共读** `agate_common.non_prunable_phases()`。
# 本测试防「脚本又各自硬编码副本」的回归（历史：二者曾各存一份且已分叉——P1 只在后者）。
# 平台无关：只用 pathlib + importlib + 字符串断言；不写临时目录、不依赖外部命令。

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
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_non_prunable_phases_single_source(agate_scripts, agate_root, monkeypatch):
    """① 注册表 `rules/phases.yaml` 顶层键 `non_prunable_phases` 存在且为 {P1,P2,P4,P5,P6}；
    ② 两脚本**均经 `agate_common.non_prunable_phases()` 取**（不再各自硬编码副本）。"""
    common = _load_module("_guard_agate_common", agate_scripts / "agate_common.py")

    # `resolve_rules_root` 解析链 = env AGATE_ROOT → 版本链（~/.agate/current）→ 脚本路径兜底。
    # 本机存在 ~/.agate ⇒ 不设 env 会读到**已安装稳定版**的 rules（非本仓）⇒ 显式指向本仓。
    monkeypatch.setenv("AGATE_ROOT", str(agate_root))
    _sp = str(Path(agate_scripts) / "agate_common.py")

    # ① 注册表单源
    assert hasattr(common, "non_prunable_phases"), (
        "agate_common 须提供 non_prunable_phases()（RM-AG0110 判据单源）"
    )
    got = {str(x) for x in common.non_prunable_phases(script_path=_sp)}
    assert got == {"P1", "P2", "P4", "P5", "P6"}, (
        f"注册表 rules/phases.yaml 的 non_prunable_phases 须为 P1/P2/P4/P5/P6；实际 {got}"
    )
    assert "P1" in got, (
        "P1（需求基线）须在不可裁剪阶段集内（state-machine.md「不可跳过的阶段」）"
    )
    # 回退默认集（唯一定义处）必须与注册表**同值**——否则注册表改了而回退没改会静默漂移
    assert hasattr(common, "NON_PRUNABLE_PHASES_DEFAULT"), (
        "agate_common 须定义 NON_PRUNABLE_PHASES_DEFAULT（回退集唯一定义处，RM-AG0110）"
    )
    assert {str(x) for x in common.NON_PRUNABLE_PHASES_DEFAULT} == got, (
        f"回退默认集 {common.NON_PRUNABLE_PHASES_DEFAULT} 与注册表值 {got} 不一致"
    )
    for _n in ("check-pruning.py", "check-state-transition.py"):
        _src = (Path(agate_scripts) / _n).read_text(encoding="utf-8")
        assert '"P1", "P2", "P4", "P5", "P6"' not in _src and "'P1', 'P2', 'P4', 'P5', 'P6'" not in _src, (
            f"{_n} 不得自带回退集副本（须引 agate_common.NON_PRUNABLE_PHASES_DEFAULT）"
        )
    phases_yaml = (Path(agate_root) / "rules" / "phases.yaml").read_text(encoding="utf-8")
    assert "non_prunable_phases" in phases_yaml, (
        "rules/phases.yaml 须含顶层键 non_prunable_phases（RM-AG0110 判据单源）"
    )

    # ② 两脚本共读（源码断言：经 helper 取，且不再有各自的模块级硬编码集）
    for name in ("check-pruning.py", "check-state-transition.py"):
        src = (Path(agate_scripts) / name).read_text(encoding="utf-8")
        assert "non_prunable_phases(" in src, (
            f"{name} 须经 agate_common.non_prunable_phases() 读取不可裁剪集（RM-AG0110）"
        )
        assert "NON_PRUNABLE_PHASES = " not in src, (
            f"{name} 不应再保留模块级硬编码不可裁剪集（判据单源，RM-AG0110）"
        )
