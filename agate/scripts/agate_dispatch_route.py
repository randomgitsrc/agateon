#!/usr/bin/env python3
"""agate_dispatch_route.py — 派发路由决策 helper（TAG0034 / RM-AG0060）

importable 模块（下划线命名，不直接执行）——被 agate-dispatch.py 的 `route` 子命令
import。暴露：

  * resolve(phase, role, *, routes, tier_bindings, factory_defaults, current_model)
      -> {"form", "chain", "model", "effort"}
      三层配置优先级解析（P2-design §3.3）。form ∈ {"default", "chain"}。
  * load_config(workspace_dir) -> (routes, tier_bindings)
      读 <workspace_dir>/dispatch-routing.yaml，全兜底（范式逐字参考
      check-maintainability.py:_load_config）。
  * classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None)
      -> Outcome(.kind, .reason)
      单次派发结果分类（P2-design §3.7 判定表）。kind ∈
      {"LAUNCH_FAIL", "INFRA_ERROR", "NO_PARSEABLE_OUTPUT", "HAS_OUTPUT"}。
  * build_dispatch_command(candidate, *, ctx_path, effort_supported) -> list[str]
      构造子进程 / native 派发命令 argv（P2-design §3.4 effort 映射）。
  * resolve_native_target(candidate, *, current_model, platform=None, tier=None) -> dict
      cli:native 形式的目标描述。
  * try_and_fall(chain, *, dispatch_context_path, dispatch_once, write_event) -> result
      逐级回落循环（无 probe，P2-design §3.7）。result.final / result.tried。
  * write_dispatch_route_event(task_dir, phase, *, tried, final) -> None
      写 dispatch_route 事件，复用 agate_common.append_event 哈希链。
  * should_consult_routing_table(dispatch_kind) -> bool
  * route_is_noop(executor_env) -> bool

完整性不变量（P2-design R1）：回落**只**在 LAUNCH_FAIL / INFRA_ERROR /
NO_PARSEABLE_OUTPUT 三类基础设施信号触发；gate 判定不是 Outcome.kind 的取值、
不进 candidates_tried[].reason、不触发换候选。

平台无关：纯逻辑 + 标准库；文本 I/O 显式 encoding="utf-8"。Python 3.8+。
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# gate 判定绝不触发换候选——机械强制的完整性不变量（P2-design R1）。
GATE_FAIL_TRIGGERS_FALLBACK = False

_VALID_REASONS = ("launch_fail", "infra_error", "no_parseable_output")

# killed_reason 中判为「启动失败」的取值；其余非空 killed_reason 一律 INFRA_ERROR
# （挂死被杀 / wait 超时 / 命令流阈值 / kill -0 探测失活，P2-design §3.7 N6）。
_LAUNCH_KILLED = {
    "spawn_oserror", "launch_fail", "oserror", "enoent", "executable_not_found",
}

# 结构化输出里的基础设施失败签名（三平台通用子串，P2-design §3.7 判定表）。
_INFRA_SIGNALS = (
    "turn.failed",
    '"type":"error"',
    '"type": "error"',
    "ProviderAuthError",
    "AuthenticationError",
    "not logged in",
    "Invalid API key",
    "ECONNREFUSED",
    "ENOTFOUND",
)

# 结构化输出里的成功签名——仅用于避免把「非零退出但明显跑成功」误判为 INFRA_ERROR。
_SUCCESS_SIGNALS = (
    "turn.completed",
    '"stop_reason":"end_turn"',
    '"stop_reason": "end_turn"',
    '"reason":"stop"',
    '"reason": "stop"',
    "step_finish",
)

_ROUTE_SPEC_MARKERS = ("tier", "candidates", "effort")


# ───────────────────────── resolve（三层配置优先级） ─────────────────────────


def _is_route_spec(node):
    return isinstance(node, dict) and any(k in node for k in _ROUTE_SPEC_MARKERS)


def _lookup_route_entry(routes, phase, role):
    """(phase,role) 命中优先于 phase 级（P2-design §3.3）。

    支持三种写法：routes["Pn.role"]（点分 key）/ routes["Pn"]["role"]（嵌套）/
    routes["Pn"]（phase 级直接条目）。
    """
    if not isinstance(routes, dict):
        return None
    dotted = routes.get(f"{phase}.{role}")
    if _is_route_spec(dotted):
        return dotted
    pnode = routes.get(phase)
    if isinstance(pnode, dict):
        rnode = pnode.get(role)
        if _is_route_spec(rnode):
            return rnode
        if _is_route_spec(pnode):
            return pnode
    return None


def _default_result(current_model):
    return {"form": "default", "chain": None, "model": current_model, "effort": None}


def resolve(phase, role, *, routes, tier_bindings, factory_defaults, current_model):
    """完整优先级解析（P2-design §3.3，BDD-7/11~18 + T1/N2 定死）。

    优先级序：项目级直接值 candidates: > 项目级档位映射 tier: > 机器级绑定
    tier_bindings 展开 > 出厂默认 factory_defaults → standard。
    """
    entry = _lookup_route_entry(routes, phase, role)

    raw_chain = None
    tier = None
    effort_override = None

    if entry is not None and "candidates" in entry:
        raw_chain = entry.get("candidates")                # 【优先级 1】项目级直接值
    elif entry is not None and "tier" in entry:
        tier = entry.get("tier")                           # 【优先级 2】项目级档位映射
        effort_override = entry.get("effort")
    else:
        fd = factory_defaults if isinstance(factory_defaults, dict) else {}
        tier = (
            fd.get(f"{phase}.{role}")
            or fd.get(phase)
            or "standard"
        )                                                 # 【优先级 4】出厂默认

    # standard 短路（不变量锚，BDD-14/40）——不经 tier_bindings 展开、等价未启用。
    if tier == "standard":
        return _default_result(current_model)

    if raw_chain is None:                                  # 来自 tier 引用
        raw_chain = tier_bindings.get(tier) if isinstance(tier_bindings, dict) else None
        if not isinstance(raw_chain, list) or not raw_chain:
            # 配了 tier 但本机未绑该 tier → 回落默认派发（机会式，BDD-16/17 精神）。
            return _default_result(current_model)

    if not isinstance(raw_chain, list) or not raw_chain:
        return _default_result(current_model)

    chain = []
    for cand in raw_chain:
        if not isinstance(cand, dict):
            continue
        merged = dict(cand)
        # effort 合并（正交轴）：候选自带 effort 优先，否则 route 层 effort。
        merged["effort"] = merged.get("effort") or effort_override
        chain.append(merged)
    if not chain:
        return _default_result(current_model)

    return {"form": "chain", "chain": chain, "model": None, "effort": None}


# ───────────────────────── load_config（全兜底） ─────────────────────────


def load_config(workspace_dir):
    """读 <workspace_dir>/dispatch-routing.yaml 的 routes: 与 tier_bindings: 两顶层 key。

    全兜底（check-maintainability.py:_load_config 范式）：目录 / 文件不存在 →
    ({}, {})；pyyaml 不可导入 → ({}, {}) + stderr；解析失败 / 非 dict → ({}, {})
    + stderr WARNING；某键类型坏 → 该键默认 {} + stderr WARNING。
    """
    routes, tier_bindings = {}, {}

    try:
        import yaml
    except ImportError:
        sys.stderr.write(
            "agate_dispatch_route WARNING: pyyaml 不可导入，路由配置使用出厂默认\n"
        )
        return routes, tier_bindings

    path = os.path.join(str(workspace_dir), "dispatch-routing.yaml")
    if not os.path.isfile(path):
        return routes, tier_bindings

    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            cfg = yaml.safe_load(f)
    except Exception:
        sys.stderr.write(
            f"agate_dispatch_route WARNING: dispatch-routing.yaml 解析失败，使用出厂默认: {path}\n"
        )
        return routes, tier_bindings

    if not isinstance(cfg, dict):
        return routes, tier_bindings

    raw_routes = cfg.get("routes")
    if isinstance(raw_routes, dict):
        routes = raw_routes
    elif raw_routes is not None:
        sys.stderr.write(
            "agate_dispatch_route WARNING: routes 类型坏（期望 mapping），使用出厂默认\n"
        )

    raw_tb = cfg.get("tier_bindings")
    if isinstance(raw_tb, dict):
        tier_bindings = raw_tb
    elif raw_tb is not None:
        sys.stderr.write(
            "agate_dispatch_route WARNING: tier_bindings 类型坏（期望 mapping），使用出厂默认\n"
        )

    return routes, tier_bindings


def load_factory_defaults(agate_root=None):
    """读 agate/rules/dispatch-tiers.yaml 的 tiers: / defaults:；全兜底。

    返回 (tier_names:set, defaults:dict)。文件缺失 / 损坏 → 内建
    ({"bulk","standard","deep"}, {})。
    """
    tier_names = {"bulk", "standard", "deep"}
    defaults = {}
    try:
        import yaml
    except ImportError:
        return tier_names, defaults
    root = agate_root or os.path.dirname(_HERE)
    path = os.path.join(str(root), "rules", "dispatch-tiers.yaml")
    if not os.path.isfile(path):
        return tier_names, defaults
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            data = yaml.safe_load(f)
    except Exception:
        return tier_names, defaults
    if not isinstance(data, dict):
        return tier_names, defaults
    if isinstance(data.get("tiers"), dict) and data["tiers"]:
        tier_names = set(data["tiers"].keys())
    if isinstance(data.get("defaults"), dict):
        defaults = data["defaults"]
    return tier_names, defaults


# ───────────────────────── classify_outcome ─────────────────────────


class Outcome:
    """单次派发结果分类（P2-design §3.7）。"""

    __slots__ = ("kind", "reason")

    def __init__(self, kind, reason):
        self.kind = kind
        self.reason = reason

    def __repr__(self):
        return f"Outcome(kind={self.kind!r}, reason={self.reason!r})"


def _has_any(text, needles):
    return any(n in text for n in needles)


def classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None):
    """P2-design §3.7 判定表 + HAS_OUTPUT「presence 级格式合法」定死（N7）。

    HAS_OUTPUT = 约定产出文件非空（presence 级）；内容完整度 / 质量判断一律交
    gate，走同候选 retry（不回落）。结构完整度校验**不得**塞进
    NO_PARSEABLE_OUTPUT 分支。
    """
    text = stdout or ""
    files = [f for f in (produced_files or []) if f]

    # 1. 启动失败 / 挂死被杀（P2-design §3.7 N6：挂死 → INFRA_ERROR）。
    if killed_reason:
        if killed_reason in _LAUNCH_KILLED:
            return Outcome("LAUNCH_FAIL", "launch_fail")
        return Outcome("INFRA_ERROR", "infra_error")

    # 2. 基础设施失败信号（结构化输出签名 / 非零退出且无产出无成功签名）。
    if _has_any(text, _INFRA_SIGNALS):
        return Outcome("INFRA_ERROR", "infra_error")
    if (
        exit_code is not None
        and exit_code != 0
        and not files
        and not _has_any(text, _SUCCESS_SIGNALS)
    ):
        return Outcome("INFRA_ERROR", "infra_error")

    # 3. 有 gate 能评的产出（presence 级——文件非空即可）。
    if files:
        return Outcome("HAS_OUTPUT", None)

    # 4. 跑了但无可解析产出（约定产出文件缺失或空 / 结构化空返回）。
    return Outcome("NO_PARSEABLE_OUTPUT", "no_parseable_output")


# ───────────────────────── build_dispatch_command ─────────────────────────


def build_dispatch_command(candidate, *, ctx_path, effort_supported):
    """构造某候选的派发命令 argv（P2-design §3.4）。

    effort 映射：Codex `-c model_reasoning_effort=<e>`；OpenCode `--variant <e>`；
    Claude Code 按 effort_supported 布尔——True 加 `--effort <e>`、False 省略
    （不报错，BDD-10 [BASELINE_CHANGE]，能力探测由调用方按 `claude --help` 得出）。
    model 为 None → 不传 --model。
    """
    candidate = candidate or {}
    cli = candidate.get("cli")
    model = candidate.get("model")
    effort = candidate.get("effort")
    ctx = str(ctx_path)

    if cli == "codex":
        cmd = [
            "codex", "exec", "--json", "--skip-git-repo-check",
            "--dangerously-bypass-approvals-and-sandbox",
        ]
        if model is not None:
            cmd += ["-m", str(model)]
        if effort:
            cmd += ["-c", f"model_reasoning_effort={effort}"]
        cmd.append(ctx)
        return cmd

    if cli == "opencode":
        cmd = ["opencode", "run", "--format", "json", "--auto"]
        if model is not None:
            cmd += ["-m", str(model)]
        if effort:
            cmd += ["--variant", str(effort)]
        cmd.append(ctx)
        return cmd

    if cli in ("claude-code", "native"):
        cmd = [
            "claude", "-p", "--output-format", "json",
            "--dangerously-skip-permissions",
        ]
        if model is not None:
            cmd += ["--model", str(model)]
        if effort and effort_supported:
            cmd += ["--effort", str(effort)]
        cmd.append(ctx)
        return cmd

    # 未知 cli：不作平台假设（调用方 / schema 校验器负责拦非法 cli）。
    cmd = [str(cli or "")]
    if model is not None:
        cmd += ["--model", str(model)]
    cmd.append(ctx)
    return cmd


def resolve_native_target(candidate, *, current_model, platform=None, tier=None):
    """cli:native 形式解析出的目标描述（P2-design §3.4）。

    model 为 None → 取 current_model（该 CLI 当前默认）。OpenCode native 无 model
    参数 → 走命名 subagent 间接路（MVP 约定命名 agate-route-{tier}）。
    """
    candidate = candidate or {}
    model = candidate.get("model")
    resolved_model = current_model if model is None else model
    target = {
        "cli": "native",
        "model": resolved_model,
        "effort": candidate.get("effort"),
    }
    if platform == "opencode":
        target["named_agent"] = f"agate-route-{tier}" if tier else "agate-route"
    return target


# ───────────────────────── try-and-fall 循环 ─────────────────────────


class TryFallResult:
    __slots__ = ("final", "tried")

    def __init__(self, final, tried):
        self.final = final
        self.tried = tried

    def __repr__(self):
        return f"TryFallResult(final={self.final!r}, tried={self.tried!r})"


def try_and_fall(chain, *, dispatch_context_path, dispatch_once, write_event, phase=None):
    """逐候选派发 → 三类基础设施信号 continue（记 reason）→ HAS_OUTPUT 即停、写事件、
    return；候选耗尽 → 写事件 final={"cli":"default"}、return DEFAULT（P2-design §3.7）。

    无 probe（BDD-19）；回落只在 LAUNCH_FAIL / INFRA_ERROR / NO_PARSEABLE_OUTPUT
    三类基础设施信号（BDD-24：产出质量差归 HAS_OUTPUT、不回落）。
    """
    tried = []
    for cand in chain:
        outcome = dispatch_once(cand, dispatch_context_path)
        if getattr(outcome, "kind", None) == "HAS_OUTPUT":
            success = dict(cand)
            success["result"] = "success"
            tried.append(success)
            write_event(phase, tried, dict(cand))
            return TryFallResult(final=dict(cand), tried=tried)
        failed = dict(cand)
        failed["result"] = "failed"
        failed["reason"] = getattr(outcome, "reason", None)
        tried.append(failed)

    write_event(phase, tried, {"cli": "default"})
    return TryFallResult(final={"cli": "default"}, tried=tried)


# ───────────────────────── dispatch_route 事件写入 ─────────────────────────


def write_dispatch_route_event(task_dir, phase, *, tried, final, task_id=None):
    """写 dispatch_route 事件——复用 agate_common.append_event（哈希链 prev_hash =
    sha256(上一行原始文本) / ts 由既有逻辑填）。不写 state_transition、不动 retries
    （BDD-28）。
    """
    from agate_common import append_event

    event = {
        "event": "dispatch_route",
        "phase": phase,
        "candidates_tried": list(tried),
        "final": final,
    }
    if task_id is not None:
        event["task_id"] = task_id
    append_event(str(task_dir), event)


# ───────────────────────── 与既有派发机制的交互 ─────────────────────────


def should_consult_routing_table(dispatch_kind):
    """RM-AG0055 自主再派发的子任务不走路由表（BDD-44），继承父的实际 cli/model。"""
    return dispatch_kind == "phase_role_dispatch"


def route_is_noop(executor_env):
    """单 Agent 模式（has_task_tool: false）→ 无派发动作、路由 no-op（BDD-45）。"""
    return not bool((executor_env or {}).get("has_task_tool", False))
