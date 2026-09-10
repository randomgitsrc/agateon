#!/usr/bin/env python3
"""check-dispatch-routing.py — 派发路由 schema 静态校验器（TAG0034 / RM-AG0060）

CLI: check-dispatch-routing.py <dispatch-routing.yaml 路径>
  exit 0 = schema 合法（或无可校验对象）
  exit 1 = schema 非法

校验口径（P2-design §3.6）：
  * 顶层 key：tier_bindings（可选 dict）/ routes（可选 dict）/ machine_routes
    （文档化保留字，放行、不作任何语义校验）/ schema_version；其它顶层 key → WARNING。
  * routes 条目值：tier: 与 candidates: 互斥（同现 → exit 1）。
  * tier: 值 ∈ dispatch-tiers.yaml 的 tiers: key 集（交叉核，读同目录 ../rules/
    dispatch-tiers.yaml；该文件缺失 / 不可读 → 降级为「非空字符串即放行」+ WARNING）；
    未知 tier → exit 1。
  * candidates: 非空 list，每项 {cli, model, effort?}：
      cli ∈ {native, claude-code, codex, opencode} 否则 exit 1；
      model 为字符串或 null（放行）；
      effort（可选）∈ {low, medium, high} 否则 exit 1。
  * effort: 亦可写在 route 层（与 tier: 并列），同枚举校验。
  * 任意层出现 fallback: → exit 1（schema 无 fallback 字段——终点回落恒为默认派发）。
  * tier_bindings 条目：key ∈ tiers（含 standard → WARNING，不 exit 1）；值 = 有序候选
    list（同 candidates 项校验）。
  * 坏 YAML / 文件不存在 / 顶层非 mapping → exit 0（无可校验对象，与全兜底运行时一致）。

平台无关：纯文件文本解析，显式 encoding="utf-8"；无裸解释器、无 /tmp。
Python 3.8+。
"""

import os
import sys

VALID_CLI = {"native", "claude-code", "codex", "opencode"}
VALID_EFFORT = {"low", "medium", "high"}
KNOWN_TOP = {"schema_version", "tier_bindings", "routes", "machine_routes"}
_ROUTE_SPEC_KEYS = ("tier", "candidates", "effort", "fallback")

_ERRORS = []
_WARNINGS = []


def _err(msg):
    _ERRORS.append(msg)


def _warn(msg):
    _WARNINGS.append(msg)


def _load_tier_names():
    """读同目录 ../rules/dispatch-tiers.yaml 的 tiers: key 集；不可读 → None（降级）。"""
    try:
        import yaml
    except ImportError:
        return None
    path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "rules", "dispatch-tiers.yaml"
    )
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("tiers"), dict):
        return None
    return set(data["tiers"].keys())


def _scan_fallback(obj, where):
    if isinstance(obj, dict):
        if "fallback" in obj:
            _err(
                f"{where}: 出现非法字段 fallback（schema 无 fallback 字段——"
                "终点回落恒为默认派发、不可配、不需声明）"
            )
        for k, v in obj.items():
            _scan_fallback(v, f"{where}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _scan_fallback(v, f"{where}[{i}]")


def _check_effort(value, where):
    if value is not None and value not in VALID_EFFORT:
        _err(f"{where}: effort={value!r} 非法（须 ∈ {sorted(VALID_EFFORT)}）")


def _check_candidate(cand, where):
    if not isinstance(cand, dict):
        _err(f"{where}: 候选项须为 mapping")
        return
    if cand.get("cli") not in VALID_CLI:
        _err(f"{where}: cli={cand.get('cli')!r} 非法（须 ∈ {sorted(VALID_CLI)}）")
    if "model" in cand:
        model = cand["model"]
        if model is not None and not isinstance(model, str):
            _err(f"{where}: model 须为字符串或 null")
    _check_effort(cand.get("effort"), where)


def _check_candidates_list(cands, where):
    if not isinstance(cands, list) or not cands:
        _err(f"{where}: candidates 须为非空 list")
        return
    for i, cand in enumerate(cands):
        _check_candidate(cand, f"{where}[{i}]")


def _check_route_spec(spec, where, tier_names):
    if not isinstance(spec, dict):
        _err(f"{where}: route 条目须为 mapping")
        return
    has_tier = "tier" in spec
    has_candidates = "candidates" in spec
    if has_tier and has_candidates:
        _err(f"{where}: tier: 与 candidates: 互斥，不能同时出现")
    if has_tier:
        tier = spec["tier"]
        if tier_names is None:
            if not (isinstance(tier, str) and tier):
                _err(f"{where}: tier 须为非空字符串")
            else:
                _warn(
                    f"{where}: 无法交叉核对 tier（dispatch-tiers.yaml 不可读），仅校验非空"
                )
        elif tier not in tier_names:
            _err(
                f"{where}: tier={tier!r} 未定义（dispatch-tiers.yaml tiers: "
                f"{sorted(tier_names)}）"
            )
    if has_candidates:
        _check_candidates_list(spec["candidates"], f"{where}.candidates")
    if "effort" in spec:
        _check_effort(spec["effort"], where)


def _check_routes(routes, tier_names):
    if not isinstance(routes, dict):
        _err("routes: 须为 mapping")
        return
    for pkey, pval in routes.items():
        if not isinstance(pval, dict):
            _err(f"routes.{pkey}: 须为 mapping")
            continue
        if any(k in pval for k in _ROUTE_SPEC_KEYS):
            # phase 级直接条目（Pn 或 Pn.role 点分 key）
            _check_route_spec(pval, f"routes.{pkey}", tier_names)
        else:
            # 嵌套 role map：Pn: {role: {...}}
            for rkey, rval in pval.items():
                _check_route_spec(rval, f"routes.{pkey}.{rkey}", tier_names)


def _check_tier_bindings(bindings, tier_names):
    if not isinstance(bindings, dict):
        _err("tier_bindings: 须为 mapping")
        return
    for tkey, tval in bindings.items():
        if tkey == "standard":
            _warn(
                "tier_bindings.standard: standard 档不经 tier_bindings 展开"
                "（恒等于默认派发），此绑定不会生效"
            )
        elif tier_names is not None and tkey not in tier_names:
            _warn(
                f"tier_bindings.{tkey}: 未在 dispatch-tiers.yaml tiers 中定义"
                "（运行时该 tier 引用将回落默认派发）"
            )
        _check_candidates_list(tval, f"tier_bindings.{tkey}")


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-dispatch-routing.py <dispatch-routing.yaml 路径>\n")
        sys.exit(1)
    path = sys.argv[1]

    try:
        import yaml
    except ImportError:
        sys.stderr.write("check-dispatch-routing WARNING: pyyaml 不可导入，跳过校验（放行）\n")
        sys.exit(0)

    if not os.path.isfile(path):
        sys.stderr.write(
            f"check-dispatch-routing: 文件不存在，无可校验对象（放行）: {path}\n"
        )
        sys.exit(0)

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f)
    except Exception as exc:
        sys.stderr.write(
            f"check-dispatch-routing: YAML 解析失败，无可校验对象（放行）: {exc}\n"
        )
        sys.exit(0)

    if data is None:
        sys.stderr.write("check-dispatch-routing: 空文件（放行）\n")
        sys.exit(0)
    if not isinstance(data, dict):
        sys.stderr.write("check-dispatch-routing: 顶层非 mapping，无可校验对象（放行）\n")
        sys.exit(0)

    tier_names = _load_tier_names()

    for key in data:
        if key not in KNOWN_TOP:
            _warn(f"未知顶层 key: {key}")

    _scan_fallback(data, "<root>")

    if "routes" in data:
        _check_routes(data["routes"], tier_names)
    if "tier_bindings" in data:
        _check_tier_bindings(data["tier_bindings"], tier_names)
    # machine_routes: 文档化保留字——放行、不作任何语义校验。

    for warning in _WARNINGS:
        sys.stderr.write(f"check-dispatch-routing WARNING: {warning}\n")

    if _ERRORS:
        for error in _ERRORS:
            sys.stderr.write(f"check-dispatch-routing ERROR: {error}\n")
        sys.exit(1)

    sys.stderr.write(f"check-dispatch-routing: schema 校验通过: {path}\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
