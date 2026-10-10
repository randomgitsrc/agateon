#!/usr/bin/env python3
"""check-routing.py — ceremony 路由校验（TAG0019 D3，BDD-6..10）

校验 P1-requirements.md 的 ceremony 声明（仪式深度）是否满足 fail-closed 条件，
与 check-pruning.py（裁剪条件检查）正交，二者都在 pre-commit-gate 链上（2j / 2j.1）。

CLI 契约：
  check-routing.py TASK_DIR
  exit 0 = 通过（不声明 ceremony = standard / thin 四要素全过且算分非薄 / standard|full 更保守声明合法）
  exit 1 = 校验不满足（fail-closed：thin 缺要素 / 声明薄于算分 / 非法值 / 算分异常 git_ok:false）
  exit 2 = 无 P1 文件（对齐同链 check-pruning 的 exit 2 语义，破损目录交人工判断）

判定流程（P2-design §2.3）：
  ceremony 空 → exit 0（不声明 = standard，BDD-8；存量任务不被拦）
  → 非法值（非 thin/standard/full）→ exit 1（兜底，BDD-6）
  → thin →
      ├─ 四要素缺任一（coupling_checklist 流式 + 跳过风险: + phases 含 P5/P6）→ exit 1 回退 standard（BDD-7）
      ├─ score_task(task_dir).git_ok == false → exit 1（算分客观信号不可用时 thin 不通过，NB-2②）
      ├─ score_task(task_dir).tier ∈ {standard, full} → exit 1（声明薄于算分，单向 fail-closed，BDD-9）
      └─ 全过 → exit 0
  → standard / full → exit 0（更保守声明合法，BDD-9 反向不拦；full 强制项由 C8 评审映射消费，BDD-14）

同源复用（R1/BDD-10）：importlib 加载 check-pruning.py 复用 _md_field / _read_p1 /
_staged_source_count 与 coupling_checklist 流式判据（^coupling_checklist:\\s*\\[）/ 跳过风险判据
（"跳过风险:" in text）——无第二份实现；算分经 importlib 加载 agate-risk-score.py 调
score_task(task_dir)（不 subprocess，避免输出解析脆弱 + 平台无关）。
"""

import importlib.util
import os
import re
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

_CACHE = {}


def _load_script(name, module_name=None):
    """importlib 加载同目录脚本（带连字符模块名无法直接 import）。"""
    key = name
    if key not in _CACHE:
        path = os.path.join(SCRIPT_DIR, name + ".py")
        spec = importlib.util.spec_from_file_location(
            module_name or name.replace("-", "_"), path
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _CACHE[key] = mod
    return _CACHE[key]


# --- 同源复用（BDD-10）：check-routing 自身暴露 check-pruning 同源函数，无独立重写 ---
_check_pruning = _load_script("check-pruning")
_md_field = _check_pruning._md_field
_p1_field = _check_pruning._p1_field
_read_p1 = _check_pruning._read_p1
_staged_source_count = _check_pruning._staged_source_count

# --- 算分调用（与 agate-risk-score.py 的耦合）：importlib，不 subprocess ---
_risk_score = _load_script("agate-risk-score")
score_task = _risk_score.score_task

_VALID_CEREMONY = ("thin", "standard", "full")


def main():
    if len(sys.argv) < 2:
        sys.stderr.write("用法: check-routing.py TASK_DIR\n")
        sys.exit(1)
    task_dir = sys.argv[1]
    p1_file = os.path.join(task_dir, "P1-requirements.md")

    # ① P1 缺失分支：exit 2（对齐同链 check-pruning；与"不声明=standard"的 exit 0 明确区分）
    if not os.path.isfile(p1_file):
        sys.stderr.write(
            "GATE SKIP: check-routing: 无 P1-requirements.md，ceremony 路由未校验（exit 2，交人工）\n"
        )
        sys.exit(2)

    ceremony = _md_field("ceremony", p1_file).strip()

    # 不声明 ceremony（存量/新任务缺字段）→ standard，不拦截（BDD-8）
    if not ceremony:
        sys.stderr.write("GATE SKIP: check-routing: P1 未声明 ceremony（按 standard 处理），未做路由校验\n")
        sys.exit(0)

    # 非法值兜底（frontmatter-check enums 已先拦，此处双保险，BDD-6）
    if ceremony not in _VALID_CEREMONY:
        sys.stderr.write(
            f"GATE ROUTING: ceremony 非法值 {ceremony!r}（仅 thin/standard/full）\n"
        )
        sys.exit(1)

    # 更保守声明合法（BDD-9 反向不拦；full 强制项由 C8 评审映射消费，BDD-14）
    if ceremony in ("standard", "full"):
        sys.exit(0)

    # --- ceremony: thin → 四要素校验（fail-closed，BDD-7）---
    p1_text = _read_p1(p1_file)
    errors = []

    # 要素 2：coupling_checklist 流式声明（复用 check-pruning:142 判据）
    if not re.search(r"^coupling_checklist:\s*\[", p1_text, re.MULTILINE):
        errors.append("thin 需 coupling_checklist: [...] 逐信号 checklist（^coupling_checklist:\\s*\\[ 判据）")

    # 要素 3：跳过风险: 声明（复用 check-pruning:156 判据）
    if "跳过风险:" not in p1_text:
        errors.append("thin 需 '跳过风险:' 跳过风险评估声明")

    # 要素 4：phases 含 P5 与 P6（薄化仪式不薄化验证；check-pruning 检查 3/5 双闸兜底）
    # RM-AG0113：`phases` 走**与 check-pruning 恒检 / check-state-transition 同代码路径**的读取器
    # （同源复用 `check-pruning._p1_field`）——不再用 `_md_field`（其回退扫全文，口径不同）。
    phases = _p1_field(_read_p1(p1_file), "phases").split()
    if "P5" not in phases or "P6" not in phases:
        errors.append("thin 需 phases 含 P5 与 P6（P5/P6 保留，薄化仪式不薄化验证）")

    if errors:
        sys.stderr.write("GATE ROUTING: ceremony: thin 四要素不满足，回退 standard：\n")
        for line in errors:
            sys.stderr.write(f"  - {line}\n")
        sys.exit(1)

    # --- 算分对拍（单向 fail-closed，BDD-9 / NB-2②）---
    score = score_task(task_dir)

    # ② 算分异常分支：git 通道不可用（run_git 失败 / agate_common 不可导入）→ thin 不通过
    if not score.get("git_ok", False):
        sys.stderr.write(
            "GATE ROUTING: ceremony: thin 但算分 git 通道不可用（git_ok: false），"
            "fail-closed 回退 standard\n"
        )
        sys.exit(1)

    # 声明薄于算分：算分 tier=standard/full 而声明 thin → 拦截
    tier = score.get("tier")
    if tier in ("standard", "full"):
        sys.stderr.write(
            f"GATE ROUTING: ceremony: thin 但算分 tier={tier}，声明薄于算分，回退 standard\n"
        )
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
