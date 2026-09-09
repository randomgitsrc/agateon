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
  * presence_parse_ok(path, *, required_anchors=None) -> bool
      约定产出文件的 presence 级校验（P4b / N7）——文件非空 + frontmatter 可解析 +
      必需锚点标题存在；**不含**内容完整度 / 质量判断（那些交 gate）。I2：此判据
      落在 produced_files 填充处（dispatch_once），**不进** classify_outcome。
  * dispatch_once(candidate, dispatch_context_path, *, effort_supported=False,
      expected_output=None, required_anchors=None, run=None, timeout_s=None,
      task_dir=None) -> Outcome
      单候选端到端派发（P2-design §3.1 step 2.3 / §3.7 / M5）。cli ∈ {native, default}
      或未知 → 返回 HAS_OUTPUT 占位（native 由驱动会话代发，路由脚本不 spawn）；
      cli ∈ {claude-code, codex, opencode} → 真子进程 spawn → 探测产出文件
      （presence_parse_ok）→ classify_outcome。
  * routed_away_verdict_location(cli) -> str
      P6.5 judge 路由到 codex/opencode 子进程时 verdict + 证据的落点——恒 "TASK_DIR"
      （铁律 2/3 不变；check-judge-verdict.py / check-p6-provenance.py 平台无关照常通过，
      本任务零改动这两个脚本，BDD-42）。
  * try_and_fall(chain, *, dispatch_context_path, dispatch_once, write_event) -> result
      逐级回落循环（无 probe，P2-design §3.7）。result.final / result.tried。
      I1：回落**只**在 kind ∈ {LAUNCH_FAIL, INFRA_ERROR, NO_PARSEABLE_OUTPUT} 白名单
      触发；其它「非 HAS_OUTPUT」kind → raise DispatchContractError（契约违例大声失败）。
  * write_dispatch_route_event(task_dir, phase, *, tried, final) -> None
      写 dispatch_route 事件，复用 agate_common.append_event 哈希链。
  * should_consult_routing_table(dispatch_kind) -> bool
  * route_is_noop(executor_env) -> bool
  * build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name)
      -> list[str]
      tmux 观测层（P4c / P2-design §3.10）——tmux_available=True 时把子进程命令包成
      `tmux new-session -d -s <ns> '<cmd> | tee <capture>; <收尾倒计时>'`（人看 pane、
      路由脚本读 capture 文件取结构化流）；False 时返回裸 cmd。纯逻辑、无 IO。
  * tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n, margin_s)
      -> str ∈ {"kill_now", "let_countdown", "force_kill", "noop"}
      路由脚本对 tmux session 的清理动作判定（P2-design §3.10）——`list-clients` 空 →
      kill_now；有人 attach 且未超 N+余量 → let_countdown；超过 → force_kill。纯逻辑。

tmux 包裹在 _default_subprocess_run 内接入（_maybe_tmux_wrap），**默认关**——
`AGATE_DISPATCH_TMUX=1` 且 `which tmux` 成功才启用；目标环境代表性未定（R10 / 外部
评审 W2）→ 默认关、待落地验证。包裹 / 裸跑两路径经 tee 的 capture 内容与裸跑 stdout
一致 → classify_outcome 判定逐字节一致（BDD-37 / R1）。

完整性不变量（P2-design R1）：回落**只**在 LAUNCH_FAIL / INFRA_ERROR /
NO_PARSEABLE_OUTPUT 三类基础设施信号触发；gate 判定不是 Outcome.kind 的取值、
不进 candidates_tried[].reason、不触发换候选。

平台无关：纯逻辑 + 标准库；文本 I/O 显式 encoding="utf-8"。Python 3.8+。
"""

import os
import shutil
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# gate 判定绝不触发换候选——机械强制的完整性不变量（P2-design R1）。
GATE_FAIL_TRIGGERS_FALLBACK = False

# 对外契约常量：dispatch_route 事件 candidates_tried[].reason 的合法枚举
# （== check-events.py:DISPATCH_ROUTE_REASONS，无 gate_fail 值）。try_and_fall 写事件
# 前用它自校 reason（P4a-review I5）。
_VALID_REASONS = ("launch_fail", "infra_error", "no_parseable_output")

# try_and_fall 回落白名单——只有这三类基础设施信号才 continue（P4a-review I1）。
_FALLBACK_KINDS = frozenset({"LAUNCH_FAIL", "INFRA_ERROR", "NO_PARSEABLE_OUTPUT"})

# 真子进程 spawn 的 CLI；其余（native / default / 未知）由驱动会话代发，路由脚本不 spawn。
_SUBPROCESS_CLIS = ("claude-code", "codex", "opencode")


class DispatchContractError(RuntimeError):
    """dispatch_once 返回了不符合契约的 Outcome —— try_and_fall 大声失败、不静默当回落信号
    （P4a-review I1：白名单化，防未来误加 kind 被当成换候选触发）。"""

# killed_reason 中判为「启动失败」的取值；其余非空 killed_reason 一律 INFRA_ERROR
# （挂死被杀 / wait 超时 / 命令流阈值 / kill -0 探测失活，P2-design §3.7 N6）。
_LAUNCH_KILLED = {
    "spawn_oserror", "launch_fail", "oserror", "enoent", "executable_not_found",
}

# 结构化输出里的基础设施失败签名——三平台通用子串（auth / 网络 / 429 / Codex turn 层
# 失败），P2-design §3.7 判定表。**不含**裸顶层 `{"type":"error"}`——那按 cli 细分见下。
_INFRA_SIGNALS = (
    "turn.failed",
    "ProviderAuthError",
    "AuthenticationError",
    "not logged in",
    "Invalid API key",
    "ECONNREFUSED",
    "ENOTFOUND",
)

# 裸顶层 error 事件——**仅对 cli == "codex"** 视为 INFRA_ERROR（Codex MV3：
# `{"type":"error","status":400}` 顶层错误）。OpenCode 的
# `{"type":"error","error":{"name":"UnknownError"}}`（MV6b）无 ProviderAuth → 归
# NO_PARSEABLE_OUTPUT（§3.7 OpenCode 行），故裸 type:error 不进通用集。
_BARE_TOP_ERROR_SIGNALS = ('"type":"error"', '"type": "error"')

# Claude Code turn 层失败签名（§3.7 Claude Code INFRA_ERROR 行：API error status /
# stop_reason == "error" / is_error == true）。`api_error_status` 需后跟非 null 数字，
# 单独判（见 _claude_api_error）。
_INFRA_SIGNALS_CLAUDE_ONLY = (
    '"stop_reason":"error"', '"stop_reason": "error"',
    '"is_error":true', '"is_error": true',
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


def _claude_api_error(text):
    """Claude Code `--output-format json` 的 `api_error_status` 后跟非 null 数字
    （如 `401`）→ turn 层 API 错误（§3.7 Claude Code INFRA_ERROR）。`null` 不算。"""
    for marker in ('"api_error_status":', '"api_error_status" :'):
        idx = text.find(marker)
        while idx != -1:
            tail = text[idx + len(marker):].lstrip()
            if tail[:1].isdigit():
                return True
            idx = text.find(marker, idx + len(marker))
    return False


def classify_outcome(cli, *, stdout, exit_code, produced_files, killed_reason=None):
    """P2-design §3.7 判定表 + HAS_OUTPUT「presence 级格式合法」定死（N7）。

    HAS_OUTPUT = 约定产出文件非空（presence 级）；内容完整度 / 质量判断一律交
    gate，走同候选 retry（不回落）。结构完整度校验**不得**塞进
    NO_PARSEABLE_OUTPUT 分支。

    基础设施失败信号按 cli 细分对齐 §3.7（SELF-GATE alignment A1）：
      * 通用（_INFRA_SIGNALS）：auth / 网络 / 429 / Codex `turn.failed`。
      * 仅 codex：裸顶层 `{"type":"error"}`（MV3 `status:400`）。
      * 仅 claude-code：`stop_reason == "error"` / `is_error == true` / `api_error_status`
        非 null 数字（MV1 反例，fixture api_error.json）。
      * opencode 的顶层 `{"type":"error"}` 无 ProviderAuth（MV6b UnknownError）→
        NO_PARSEABLE_OUTPUT，**不**被「非零退出」通用兜底误升为 INFRA_ERROR。
    """
    text = stdout or ""
    files = [f for f in (produced_files or []) if f]

    # 1. 启动失败 / 挂死被杀（P2-design §3.7 N6：挂死 → INFRA_ERROR）。
    if killed_reason:
        if killed_reason in _LAUNCH_KILLED:
            return Outcome("LAUNCH_FAIL", "launch_fail")
        return Outcome("INFRA_ERROR", "infra_error")

    # 2. 基础设施失败信号（按 cli 细分，§3.7）。
    infra = _has_any(text, _INFRA_SIGNALS)
    if not infra and cli == "codex" and _has_any(text, _BARE_TOP_ERROR_SIGNALS):
        infra = True
    if (
        not infra
        and cli not in ("codex", "opencode")
        and (_has_any(text, _INFRA_SIGNALS_CLAUDE_ONLY) or _claude_api_error(text))
    ):
        infra = True
    if infra:
        return Outcome("INFRA_ERROR", "infra_error")

    # 2b. OpenCode 顶层 error 事件但非 ProviderAuth/auth/network（MV6b UnknownError）→
    #     无可解析产出（§3.7 OpenCode NO_PARSEABLE_OUTPUT 行）；早于「非零退出」兜底返回。
    if cli == "opencode" and _has_any(text, _BARE_TOP_ERROR_SIGNALS):
        return Outcome("NO_PARSEABLE_OUTPUT", "no_parseable_output")

    # 2c. 非零退出且无产出无成功签名 → INFRA_ERROR（退出码弱佐证兜底）。
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


# ───────────────────────── dispatch_once（端到端单候选派发，M5） ─────────────────────────


def presence_parse_ok(path, *, required_anchors=None):
    """约定产出文件的 presence 级校验（P4b / P2-design §3.7 N7）。

    通过条件：文件存在且非空；若有 frontmatter（`---` 起始）则该块须闭合且至少一行
    `key: value`；`required_anchors` 里的每个锚点串都出现在正文。

    **不含**内容完整度 / BDD 覆盖度 / 质量判断——那些一律 gate 负责、走同候选 retry
    （BDD-26）。I2 硬约束：此判据只在 produced_files 填充处（dispatch_once）调用，
    **不得**塞进 classify_outcome 的 NO_PARSEABLE_OUTPUT 分支。
    """
    try:
        if not os.path.isfile(str(path)):
            return False
        with open(str(path), encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError:
        return False
    if not text.strip():
        return False
    if text.startswith("---\n") or text.startswith("---\r\n"):
        rest = text.split("\n", 1)[1] if "\n" in text else ""
        end = rest.find("\n---")
        if end == -1:
            return False                                   # frontmatter 未闭合 → 不可解析
        fm = rest[:end]
        if not any(":" in ln for ln in fm.splitlines() if ln.strip()):
            return False
    return all(anchor in text for anchor in (required_anchors or []))


# ───────────────────────── tmux 观测层（P4c，纯逻辑 helper） ─────────────────────────


def build_subprocess_launch(cmd, *, capture_path, tmux_available, session_name,
                            countdown_n=15):
    """子进程派发命令的 launch argv（P2-design §3.10 / BDD-37）。

    tmux_available=True → `["tmux","new-session","-d","-s",<session_name>,
      "<cmd 串> | tee <capture_path>; <收尾: 打结束标记 + N 秒倒计时后 wrapper 自退>"]`
      —— 人 `tmux attach` 看 pane；路由脚本读 capture 文件取结构化流。经 tee 的 capture
      内容 == 裸跑 stdout（`tee` 只旁路一份、不改字节）→ gate 判定逐字节一致（R1）。
    tmux_available=False → `list(cmd)` 原样裸跑（现状）。

    纯逻辑、无 IO——`which tmux` 由调用方判定后传 tmux_available。
    """
    if not tmux_available:
        return list(cmd)
    inner = " ".join(str(c) for c in cmd)
    wrapper = (
        f"{inner} | tee {capture_path}; "
        f"echo '=== 派发结束 ==='; "
        f"echo '本窗口将在 {countdown_n} 秒后关闭…（Ctrl+b d 可提前离开）'; "
        f"sleep {countdown_n}"
    )
    return ["tmux", "new-session", "-d", "-s", str(session_name), wrapper]


def tmux_cleanup_action(session_name, *, has_clients, elapsed_s, countdown_n,
                        margin_s):
    """路由脚本对 tmux session 的清理动作（P2-design §3.10 / BDD-38）。

    返回值 ∈ {"kill_now", "let_countdown", "force_kill", "noop"}：
      * session_name falsy → "noop"（无可清理对象）。
      * has_clients=False → "kill_now"（没人 attach，`list-clients` 空 → 直接
        `kill-session` 跳倒计时）。
      * has_clients=True 且 elapsed_s <= countdown_n + margin_s → "let_countdown"
        （有人 attach，不强杀，让 wrapper 的 N 秒倒计时收尾——被瞬间踢出突兀）。
      * has_clients=True 且 elapsed_s > countdown_n + margin_s → "force_kill"
        （倒计时脚本本身挂死、超过 N + 余量仍在 → 兜底强杀，session 不久留）。

    纯逻辑、无 IO；elapsed_s 语义 = 子进程命令已结束、进入收尾倒计时后经过的秒数
    （P2-design §3.10：余量 = 10s，N 默认 15s）。
    """
    if not session_name:
        return "noop"
    if not has_clients:
        return "kill_now"
    if elapsed_s <= countdown_n + margin_s:
        return "let_countdown"
    return "force_kill"


def _tmux_teardown(session_name):
    """强制收尾一个 tmux session——先 `has-session` 判断、容忍 `kill-session` 对已消失
    session 的 exit 1（MV11 实测）。IO helper，仅 tmux 包裹路径调用。"""
    import subprocess

    try:
        alive = subprocess.run(
            ["tmux", "has-session", "-t", str(session_name)],
            capture_output=True, text=True,
        ).returncode == 0
        if alive:
            subprocess.run(
                ["tmux", "kill-session", "-t", str(session_name)],
                capture_output=True, text=True,
            )
    except OSError:
        pass


def _tmux_collect(session_name, capture_path, *, countdown_n=15, margin_s=10,
                  poll_s=0.5, hard_cap_s=1800.0):
    """`tmux new-session -d` 立即返回后，轮询 session 生命周期并收 capture 文件内容。

    子进程命令跑完（capture 出现成功 / 基础设施失败签名）后进入收尾倒计时——按
    tmux_cleanup_action 决定：没人 attach → 立即 `kill-session` 跳倒计时；有人 attach
    → 让倒计时走完；倒计时脚本挂死超过 N + 余量 → 兜底强杀。返回 capture 文件全文
    （== 裸跑 stdout）。IO helper，仅 tmux 包裹路径调用。
    """
    import subprocess

    start = time.time()
    done_at = None

    def _slurp():
        try:
            with open(str(capture_path), encoding="utf-8", errors="replace") as fh:
                return fh.read()
        except OSError:
            return ""

    while True:
        try:
            alive = subprocess.run(
                ["tmux", "has-session", "-t", str(session_name)],
                capture_output=True, text=True,
            ).returncode == 0
        except OSError:
            break
        if not alive:
            break

        now = time.time()
        text = _slurp()
        cmd_done = _has_any(text, _SUCCESS_SIGNALS) or _has_any(text, _INFRA_SIGNALS)
        if cmd_done and done_at is None:
            done_at = now

        if done_at is not None:
            clients = subprocess.run(
                ["tmux", "list-clients", "-t", str(session_name)],
                capture_output=True, text=True,
            )
            has_clients = bool((clients.stdout or "").strip())
            action = tmux_cleanup_action(
                str(session_name), has_clients=has_clients,
                elapsed_s=now - done_at, countdown_n=countdown_n, margin_s=margin_s,
            )
            if action in ("kill_now", "force_kill"):
                _tmux_teardown(session_name)
                break

        if now - start > hard_cap_s:
            _tmux_teardown(session_name)
            break
        time.sleep(poll_s)

    return _slurp()


def _maybe_tmux_wrap(argv_str):
    """P4c 默认关：`AGATE_DISPATCH_TMUX=1` 且 `which tmux` 成功 → 用 build_subprocess_launch
    把子进程命令包成 `tmux new-session -d`（stdout 经 `| tee <capture>` 落文件、人可
    attach 看 pane、路由脚本读 capture 取结构化流）。否则返回裸 argv——与现状逐字节一致。

    session 名 = `agate-{task_id}-{phase}-{int(time.time())}`（带命名空间，P2-design §3.10）。
    目标环境代表性未定（R10 / 外部评审 W2）→ 默认关、待落地验证。
    返回 (launch_argv, capture_path 或 None, session_name 或 None)。
    """
    if os.environ.get("AGATE_DISPATCH_TMUX") != "1" or not shutil.which("tmux"):
        return list(argv_str), None, None
    task_id = os.environ.get("AGATE_DISPATCH_TASK_ID", "task")
    phase = os.environ.get("AGATE_DISPATCH_PHASE", "P")
    session_name = f"agate-{task_id}-{phase}-{int(time.time())}"
    capture_path = os.environ.get("AGATE_DISPATCH_CAPTURE") or os.path.join(
        tempfile.gettempdir(), session_name + ".log"
    )
    launch = build_subprocess_launch(
        list(argv_str), capture_path=capture_path,
        tmux_available=True, session_name=session_name,
    )
    return launch, capture_path, session_name


def _default_subprocess_run(argv, *, timeout_s=None):
    """裸 subprocess 跑候选命令，收 (stdout, exit_code, killed_reason)。

    P4c：tmux 观测层包裹在此接入（_maybe_tmux_wrap，**默认关**——`AGATE_DISPATCH_TMUX=1`
    且 `which tmux` 成功才启用；目标环境代表性未定 R10 / W2 → 默认关、待落地验证）。
    包裹 / 裸跑两路径经 tee 的 capture 内容与裸跑 stdout 一致 → classify_outcome 判定
    逐字节一致（BDD-37 / R1）。RM-AG0055 命令流阈值卡死检测仍留后续接入位。
    宽超时兜底（P2-design §3.7 N6「宁宽勿紧」）。
    """
    import subprocess

    if timeout_s is None:
        try:
            timeout_s = float(os.environ.get("AGATE_DISPATCH_TIMEOUT_S", "1800"))
        except ValueError:
            timeout_s = 1800.0

    launch, tmux_capture, tmux_session = _maybe_tmux_wrap([str(a) for a in argv])

    try:
        proc = subprocess.run(
            launch, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout_s,
        )
    except OSError:                                         # FileNotFoundError ⊂ OSError（P4b-I2）
        return "", None, "spawn_oserror"
    except subprocess.TimeoutExpired as exc:
        if tmux_capture:
            _tmux_teardown(tmux_session)
        return (exc.stdout or ""), None, "wait_timeout"

    # P4b-I1：透传子进程 stderr 供人排查（诊断面）——**不并入** classify_outcome 的判定
    # 文本，判定输入与裸跑保持一致 → R1 完整性不破。
    if proc.stderr and proc.stderr.strip():
        sys.stderr.write(proc.stderr)

    if tmux_capture:
        # tmux new-session -d 立即返回 → 轮询 session 生命周期 + 收 capture 文件。
        # 退出码不经 tmux 透出 → None（Codex 退出码本不可靠、判定走结构化流，§3.7）。
        return _tmux_collect(
            tmux_session, tmux_capture, hard_cap_s=timeout_s,
        ), None, None

    return (proc.stdout or ""), proc.returncode, None


def dispatch_once(candidate, dispatch_context_path, *, effort_supported=False,
                  expected_output=None, required_anchors=None, run=None,
                  timeout_s=None, task_dir=None):
    """单候选端到端派发（P2-design §3.1 step 2.3 / §3.7 判定表 / M5）。

    - cli ∈ {native, default} 或未知 → 返回 HAS_OUTPUT 占位：native 由驱动会话代发，
      路由脚本不 spawn（_route_main 首候选 native 时输出路由计划 JSON 即止，与 P4a
      DESIGN_GAP 一致）。
    - cli ∈ {claude-code, codex, opencode} → build_dispatch_command 构造命令 → run 收
      stdout / exit_code / killed_reason → 探测约定产出文件（presence_parse_ok，I2：
      presence-parse 落在 produced_files 侧）→ classify_outcome（四值判定表 + 挂死 →
      INFRA_ERROR）。

    `run` 缺省 _default_subprocess_run（真 spawn）；单测注入 mock 喂结构化输出样本。
    `task_dir` 目前仅供未来 hook（本批未用），保留形参以稳定契约。
    """
    candidate = candidate or {}
    cli = candidate.get("cli")

    if cli not in _SUBPROCESS_CLIS:
        # native / default / 未知 cli：路由脚本不 spawn，交驱动会话代发（占位 HAS_OUTPUT）。
        return Outcome("HAS_OUTPUT", None)

    argv = build_dispatch_command(
        candidate, ctx_path=dispatch_context_path, effort_supported=effort_supported,
    )
    runner = run or _default_subprocess_run
    stdout, exit_code, killed_reason = runner(argv, timeout_s=timeout_s)

    # I2：约定产出文件 presence-parse 落在 produced_files 填充处（不进 classify_outcome）。
    produced_files = []
    if expected_output and presence_parse_ok(
        expected_output, required_anchors=required_anchors
    ):
        produced_files = [expected_output]

    return classify_outcome(
        cli, stdout=stdout, exit_code=exit_code,
        produced_files=produced_files, killed_reason=killed_reason,
    )


def routed_away_verdict_location(cli):
    """P6.5 judge 被路由到 codex/opencode 子进程时，verdict + 证据的落点（BDD-42）。

    `cli` 形参为对外契约保留（判据平台无关、恒 TASK_DIR，不按 cli 分流）。

    恒返回 "TASK_DIR"：judge 子进程产出的 verdict + 证据仍写 TASK_DIR（铁律 2/3 不变）
    → check-judge-verdict.py / check-p6-provenance.py 纯 TASK_DIR 文件解析、不读平台
    transcript（~/.codex/sessions / ~/.claude/projects），本任务零改动这两个脚本即平台
    无关照常通过。**不落**平台 transcript 位置。
    """
    return "TASK_DIR"


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

    I1（白名单化）：显式判 kind ∈ _FALLBACK_KINDS 才回落；其它「非 HAS_OUTPUT」kind
    （含 None / 未来误加的枚举）→ raise DispatchContractError（契约违例大声失败，绝不
    静默当回落信号换候选）。I5：写事件前用 _VALID_REASONS 自校回落候选的 reason。
    """
    tried = []
    for cand in chain:
        outcome = dispatch_once(cand, dispatch_context_path)
        kind = getattr(outcome, "kind", None)
        if kind == "HAS_OUTPUT":
            success = dict(cand)
            success["result"] = "success"
            tried.append(success)
            write_event(phase, tried, dict(cand))
            return TryFallResult(final=dict(cand), tried=tried)
        if kind not in _FALLBACK_KINDS:                     # I1：白名单外的非 HAS_OUTPUT
            raise DispatchContractError(
                f"dispatch_once 返回非契约 outcome.kind={kind!r}"
                f"（既非 HAS_OUTPUT 也非三类基础设施信号 {sorted(_FALLBACK_KINDS)}）"
            )
        reason = getattr(outcome, "reason", None)
        if reason not in _VALID_REASONS:                    # I5：写事件前自校 reason
            raise DispatchContractError(
                f"回落 outcome.kind={kind!r} 携带非法 reason={reason!r}"
                f"（合法枚举 {_VALID_REASONS}）"
            )
        failed = dict(cand)
        failed["result"] = "failed"
        failed["reason"] = reason
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
