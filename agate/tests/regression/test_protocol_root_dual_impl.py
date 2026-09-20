# tests/regression/test_protocol_root_dual_impl.py — `_protocol_root` 双实现一致性回归（TAG0037 P3 组 B，批 E）
# 覆盖：BDD-8（agate_common._protocol_root 与 agate-install.py 内 pyyaml 缺失时的降级副本，五夹具逐一相等）、
#       BDD-6（探测序语义不变：vdir/scripts 优先 → vdir/agate/scripts → 原样；新契约形态命中探测序 2；两者皆有返回 vdir）。
# 背景：TAG0031 hash 双实现合并的同类隐患——两份探测逻辑，探测序改动只改一处必须被本测试拦截。
# 说明：本文件是**永久回归**（长期不变量：两份实现在五夹具上行为相同；探测序 1 优先于 2），不含"一次性交付事实"断言；
#       P4 后本文件应保持全绿（有意应绿，P3 阶段即为绿：它锁的是既有行为，不是新行为）。
# 隔离：全部在 tmp_path 下建目录夹具；不触碰真实 ~/.agate。

import importlib.util
import os
import sys

import pytest

_CASES = {
    "bdd8-1-only-vdir-scripts": ("scripts",),
    "bdd8-2-only-vdir-agate-scripts": ("agate/scripts",),
    "bdd8-3-both": ("scripts", "agate/scripts"),
    "bdd8-4-neither": (),
    "bdd8-5-new-contract-shape": ("agate/scripts", "agate/rules", "CHANGELOG.md", "LICENSE", "NOTICES.md"),
}

# 期望返回值（相对 vdir；""=vdir 本身）：探测序 1（vdir/scripts）先于探测序 2（vdir/agate/scripts），皆无原样返回。
_EXPECT = {
    "bdd8-1-only-vdir-scripts": "",
    "bdd8-2-only-vdir-agate-scripts": "agate",
    "bdd8-3-both": "",
    "bdd8-4-neither": "",
    "bdd8-5-new-contract-shape": "agate",
}


def _build(vdir, entries):
    vdir.mkdir(parents=True)
    for rel in entries:
        target = vdir / rel
        if rel.endswith((".md", "LICENSE")) or rel in ("CHANGELOG.md", "LICENSE", "NOTICES.md"):
            target.write_text("x\n", encoding="utf-8")
        else:
            target.mkdir(parents=True, exist_ok=True)


def _agate_common(agate_scripts):
    p = str(agate_scripts)
    if p not in sys.path:
        sys.path.insert(0, p)
    import agate_common

    return agate_common


def _installer_fallback_impl(agate_scripts, monkeypatch):
    """加载 agate-install.py 并强制走 pyyaml/agate_common 缺失时的降级分支，返回降级副本 `_protocol_root`。"""
    monkeypatch.syspath_prepend(str(agate_scripts))
    monkeypatch.setitem(sys.modules, "agate_common", None)  # `from agate_common import …` → ImportError → 降级分支
    name = "agate_install_fallback_dual_impl"
    spec = importlib.util.spec_from_file_location(name, str(agate_scripts / "agate-install.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    fn = module._protocol_root
    assert fn.__module__ == name, "agate-install.py 应保留降级副本 _protocol_root（agate_common 缺失时本地定义）"
    return fn


def _diff_impls(fn_a, fn_b, tmp_path):
    """五夹具下两实现返回值不一致的夹具名列表（空 = 逐一相等）。"""
    diffs = []
    for name, entries in _CASES.items():
        vdir = tmp_path / name / "v0.73.0"
        _build(vdir, entries)
        if os.path.normpath(fn_a(str(vdir))) != os.path.normpath(fn_b(str(vdir))):
            diffs.append(name)
    return diffs


@pytest.mark.parametrize("case", list(_CASES))
def test_bdd_8_both_impls_return_expected_and_equal(case, agate_scripts, tmp_path, monkeypatch):
    """BDD-8：五夹具下 agate_common._protocol_root 与 agate-install.py 降级副本返回值逐一相等（且等于探测序期望）。"""
    common = _agate_common(agate_scripts)
    fallback = _installer_fallback_impl(agate_scripts, monkeypatch)
    vdir = tmp_path / "v0.73.0"
    _build(vdir, _CASES[case])
    expected = os.path.normpath(str(vdir / _EXPECT[case]) if _EXPECT[case] else str(vdir))
    assert os.path.normpath(common._protocol_root(str(vdir))) == expected
    assert os.path.normpath(fallback(str(vdir))) == expected
    assert os.path.normpath(common._protocol_root(str(vdir))) == os.path.normpath(fallback(str(vdir)))


def test_bdd_8_guard_catches_a_one_sided_probe_order_change(agate_scripts, tmp_path, monkeypatch):
    """BDD-8 变异自证：把降级副本的探测序颠倒（只改一处）——一致性判定函数必须报出差异（"必被该测试拦截"）。"""
    common = _agate_common(agate_scripts)
    fallback = _installer_fallback_impl(agate_scripts, monkeypatch)
    assert _diff_impls(common._protocol_root, fallback, tmp_path / "ok") == []

    def swapped(vdir):  # 探测序颠倒：先 vdir/agate/scripts，后 vdir/scripts
        sub = os.path.join(vdir, "agate")
        if os.path.isdir(os.path.join(sub, "scripts")):
            return sub
        if os.path.isdir(os.path.join(vdir, "scripts")):
            return vdir
        return vdir

    assert _diff_impls(common._protocol_root, swapped, tmp_path / "mut") == ["bdd8-3-both"]


def test_bdd_6_scripts_at_vdir_wins_over_agate_scripts(agate_scripts, tmp_path):
    """BDD-6 新增用例：同时含 vdir/scripts 与 vdir/agate/scripts → 探测序 1 优先，返回 vdir。"""
    common = _agate_common(agate_scripts)
    vdir = tmp_path / "v0.73.0"
    _build(vdir, _CASES["bdd8-3-both"])
    assert os.path.normpath(common._protocol_root(str(vdir))) == os.path.normpath(str(vdir))


def test_bdd_6_new_contract_shape_hits_probe_order_2(agate_scripts, tmp_path):
    """BDD-6：新契约形态（vdir/agate/ + 根登记文件，无 vdir/scripts）零改动命中探测序 2 → vdir/agate。"""
    common = _agate_common(agate_scripts)
    vdir = tmp_path / "v0.73.0"
    _build(vdir, _CASES["bdd8-5-new-contract-shape"])
    assert not (vdir / "scripts").exists()
    assert os.path.normpath(common._protocol_root(str(vdir))) == os.path.normpath(str(vdir / "agate"))


def test_bdd_6_neither_form_returns_vdir_unchanged(agate_scripts, tmp_path):
    """BDD-6：两形态皆无 → 原样返回 vdir（下游维持既有 fail-closed）。"""
    common = _agate_common(agate_scripts)
    vdir = tmp_path / "v0.73.0"
    _build(vdir, ())
    assert os.path.normpath(common._protocol_root(str(vdir))) == os.path.normpath(str(vdir))
