#!/usr/bin/env python3
"""agate-inject-card.py — 自动注入 AGATE_CARD 到 dispatch-context 文件

从 agate-inject-card.sh 迁移（TAG0010 批次 2a）。CLI 契约与 sh 版等价：
用法: agate-inject-card.py P{N} TASK_DIR
取 agate-next-card.py 输出的当前阶段卡片全文，逐个注入
${PHASE}-dispatch-context-*.md（无匹配时回退旧格式 ${PHASE}-dispatch-context.md）。

M3 渲染化（TAG0021，P2-design §3.6 + BDD-12/13）：卡片内容经 agate-next-card.py
输出——正式卡片原样透传（git 管理渲染产物）；裸模板卡片由 next-card 内嵌渲染器
从 AGATE_ROOT 解析的 rules/phases.yaml 渲染可判定节（产出/派发/gate/retry）。
注入的卡片块与 YAML 渲染结果一致；渲染只读 resolve_agate_root 解析到的 YAML
（稳定版隔离：worktree 未发布 rules/*.yaml 不污染 ~/.agate 稳定版注入）。

exit 0 = 全部注入完成；exit 1 = 参数缺失 / agate-next-card.py 不可用或输出为空 /
    dispatch-context 不存在 / 占位符缺失（agate-card-inject.py 非零退出）。

迁移说明：readlink -f + dirname → os.path.realpath；$(...) 剥尾换行 → .rstrip("\n")；
mktemp → tempfile.mkstemp（显式 encoding="utf-8" 写卡片）；AGATE_CARD 替换仍复用
agate-card-inject.py（env DC_FILE / CARD_FILE 契约不变）。
"""

import contextlib
import glob
import os
import subprocess
import sys
import tempfile

try:
    from agate_common import resolve_agate_root as _agate_common_resolve
except (ImportError, SystemExit):
    _agate_common_resolve = None

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CARD_INJECT = os.path.join(SCRIPT_DIR, "agate-card-inject.py")


def _agate_root():
    """AGATE_ROOT 解析：归口 agate_common.resolve_agate_root（env → 项目声明 → current 链
    → 脚本路径上溯）；agate_common 不可用时（独立副本场景）回退 env → 脚本真实路径上溯。"""
    if _agate_common_resolve is not None:
        return _agate_common_resolve(os.path.abspath(__file__))
    env_root = os.environ.get("AGATE_ROOT", "")
    if env_root:
        return env_root
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def _next_card_content(agate_root, phase):
    """调 agate-next-card.py 取卡片全文（$(...) 剥尾换行 → .rstrip("\n")）。
    脚本不可用或输出为空 → 返回 None（调用方 exit 1）。"""
    next_card = os.path.join(agate_root, "scripts", "agate-next-card.py")
    if not os.path.isfile(next_card):
        return None
    try:
        proc = subprocess.run(
            [sys.executable, next_card, phase],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return (proc.stdout or "").rstrip("\n")


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        sys.stderr.write("用法: agate-inject-card.py PHASE TASK_DIR\n")
        sys.exit(1)
    phase = args[0]
    task_dir = args[1]

    agate_root = _agate_root()
    card_content = _next_card_content(agate_root, phase)
    if not card_content:
        sys.stderr.write(f"GATE: agate-next-card.py {phase} 输出为空\n")
        sys.exit(1)

    dc_files = sorted(glob.glob(os.path.join(task_dir, phase + "-dispatch-context-*.md")))
    if not dc_files:
        dc_files = [os.path.join(task_dir, phase + "-dispatch-context.md")]

    if not os.path.isfile(dc_files[0]):
        sys.stderr.write(f"GATE: {phase}-dispatch-context-{{role}}.md 不存在\n")
        sys.exit(1)

    failures = []
    for dc_file in dc_files:
        fd, card_file = tempfile.mkstemp()
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(card_content)
            env = dict(os.environ)
            env["DC_FILE"] = dc_file
            env["CARD_FILE"] = card_file
            try:
                proc = subprocess.run(
                    [sys.executable, CARD_INJECT],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    env=env,
                )
            except OSError:
                proc = None
            if proc is None or proc.returncode != 0:
                # 透传 agate-card-inject.py 的错误消息（占位符缺失等）——sh 版 stderr 直通终端
                if proc is not None and proc.stderr:
                    sys.stderr.write(proc.stderr)
                # RM-AG0104 / DEBT0052：**不早退**——继续处理其余文件，末尾汇总失败清单并非零退出。
                # 原实现在首个失败处 `sys.exit(1)` ⇒ 排序其后**全部文件静默不注入**
                # （实测：一个缺占位符的文件导致其后 13 个 dispatch-context 全部丢失，人工才发现）。
                failures.append(os.path.basename(dc_file))
                continue
        finally:
            with contextlib.suppress(OSError):
                os.remove(card_file)
        sys.stdout.write(f"AGATE_CARD 已注入: {os.path.basename(dc_file)}\n")

    if failures:
        sys.stderr.write(
            f"GATE: {len(failures)}/{len(dc_files)} 个 dispatch-context 注入失败"
            f"（RM-AG0104 / DEBT0052）：{', '.join(failures)}\n"
            "  其余文件已继续注入（不再早退）；请修复上述文件后重跑本命令。\n"
        )
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
