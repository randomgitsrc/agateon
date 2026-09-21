#!/usr/bin/env python3
"""install-hook.py — 安装 pre-commit / commit-msg / pre-push hook（TAG0010 批次 3b + TAG0008 批次 resolve-chain）

迁移自 install-hook.sh（93 行）：把 agate 的三个 hook 薄壳软链到当前 git 仓库的
.git/hooks/ 下（Windows 无符号链接权限时退化为复制 + 写 .agate-root 兜底标记），
并做 chmod +x、既有 hook 备份、.gitignore 对 .state.yaml 的忽略检测。

TAG0008：hook 薄壳是固定解析入口（运行时经 resolve-entry.py 解析项目 .agate-version
→ 对应版本 gate py），不直接安装具体版本脚本——切版本不用重装 hook（BDD-18）。
安装时校验 resolve-entry.py 存在（缺失仅 WARNING，不阻断——复制模式 fake 根可无它）。

用法：
  python3 install-hook.py                       # 默认 agate_home()（尊重 AGATE_HOME 覆盖）
  python3 install-hook.py /path/to/agate_root   # 或环境变量 AGATE_ROOT

AGATE_ROOT 解析保持 sh 原优先级：argv[1] > 环境变量 AGATE_ROOT > ~/.agate。
（不用 agate_common.resolve_agate_root——其 env 优先 + 脚本路径上溯语义与本安装器
「默认 agate_home()（尊重 AGATE_HOME 覆盖） 稳定版」契约不同，此处逐行保留 sh 语义。）

CLI 契约：可选 1 个参数；非 git 仓库 / AGATE_ROOT 缺脚本 → stderr + exit 1；提示写
stdout；成功 exit 0。Python 3.8+（无 match / str.removeprefix）；所有文本读写显式
encoding="utf-8"。
"""

import contextlib
import os
import re
import shutil
import subprocess
import sys
import time

try:
    from agate_common import run_git
except (ImportError, SystemExit):
    # 公共库依赖缺失时降级本地 subprocess 实现（安装器不依赖 pyyaml）。
    def run_git(args, cwd=None):
        try:
            proc = subprocess.run(
                ["git", *args], capture_output=True, text=True,
                encoding="utf-8", errors="replace", cwd=cwd,
            )
            return proc.returncode, proc.stdout
        except OSError:
            return 1, ""


_STATE_YAML_RE = re.compile(r"^\s*[*]*\.state\.yaml")


def _ln_sf(source, link_path):
    """`ln -sf` 等价：先移除既有目标（文件或软链）再建软链。

    Windows 无符号链接权限时 os.symlink 抛 OSError → 退化为复制（模拟 Git Bash 的
    ln → cp 退化）。返回是否建了软链（调用方用 os.path.islink 判定，同 sh `[ -L ]`）。
    AGATE_HOOK_COPY_MODE=1 时强制走复制分支（测试用，模拟 Windows 无权限场景——
    等价于 sh 版在 PATH 前插 mock ln 使其退化为 cp）。
    """
    if os.path.lexists(link_path):
        with contextlib.suppress(OSError):
            os.unlink(link_path)
    if os.environ.get("AGATE_HOOK_COPY_MODE") == "1":
        with contextlib.suppress(OSError):
            shutil.copyfile(source, link_path)
        return
    try:
        os.symlink(source, link_path)
    except OSError:
        with contextlib.suppress(OSError):
            shutil.copyfile(source, link_path)


def _backup(hook_file, label):
    """已有非软链 hook → 备份为 {hook_file}.bak.{epoch}（cp 语义，sh set -e 下失败即退）。"""
    if os.path.isfile(hook_file) and not os.path.islink(hook_file):
        backup = hook_file + ".bak." + str(int(time.time()))
        shutil.copyfile(hook_file, backup)
        print(f"已备份现有 {label} hook")


def _chmod_x(path):
    """`chmod +x` 等价：在既有权限上追加执行位（Windows 无 chmod 语义，失败忽略）。"""
    try:
        st = os.stat(path)
        os.chmod(path, st.st_mode | 0o111)
    except OSError:
        pass


def main():
    # 默认根用 agate_home()（尊重 AGATE_HOME 覆盖）——此前写死 ~/.agate，
    # 覆盖安装时会指错（2026-09-21 修）。
    if len(sys.argv) > 1:
        agate_root = sys.argv[1]
    elif os.environ.get("AGATE_ROOT"):
        agate_root = os.environ["AGATE_ROOT"]
    else:
        import agate_package
        agate_root = agate_package.agate_home()

    rc, out = run_git(["rev-parse", "--show-toplevel"])
    if rc != 0 or not out.strip():
        sys.stderr.write("不在 git 仓库中\n")
        sys.exit(1)
    repo_root = out.strip()

    hook_dir = os.path.join(repo_root, ".git", "hooks")

    # pre-commit hook
    hook_file = os.path.join(hook_dir, "pre-commit")
    source = os.path.join(agate_root, "scripts", "pre-commit-gate.sh")

    if not os.path.isfile(source):
        sys.stderr.write(f"错误: {source} 不存在（AGATE_ROOT={agate_root}）\n")
        sys.exit(1)

    os.makedirs(hook_dir, exist_ok=True)

    # 固定解析入口校验（TAG0008）：薄壳运行时经 resolve-entry 解析版本。缺失仅 WARNING
    # 不阻断（兼容仅含薄壳的 fake 安装根测试场景；真安装缺失时 hook 运行时 fail-closed）。
    resolve_entry = os.path.join(agate_root, "scripts", "resolve-entry.py")
    if not os.path.isfile(resolve_entry):
        print(f"⚠️  {resolve_entry} 不存在——hook 将无法经 resolve-entry 解析版本，请检查安装")

    _backup(hook_file, "pre-commit")
    _ln_sf(source, hook_file)
    _chmod_x(source)
    if os.path.islink(hook_file):
        print(f"pre-commit hook 已安装: {hook_file} -> {source}")
    else:
        # 复制模式（Windows 无符号链接权限）：写入 AGATE_ROOT 兜底标记。
        # pre-commit-gate 复制模式（readlink 解析不到本体）读取该标记恢复 AGATE_ROOT。
        with open(os.path.join(hook_dir, ".agate-root"), "w", encoding="utf-8") as f:
            f.write(agate_root + "\n")
        print(f"pre-commit hook 已安装（复制模式，Windows 无符号链接权限）: {hook_file}")
        print("  ⚠️  升级 agate 后需重跑 python3 install-hook.py（复制不自动跟随源文件）")

    # 安装 commit-msg hook（self-gate 强制触发）
    commit_msg_hook = os.path.join(hook_dir, "commit-msg")
    commit_msg_source = os.path.join(agate_root, "scripts", "commit-msg-self-gate.sh")
    if os.path.isfile(commit_msg_source):
        _backup(commit_msg_hook, "commit-msg")
        _ln_sf(commit_msg_source, commit_msg_hook)
        _chmod_x(commit_msg_source)
        if os.path.islink(commit_msg_hook):
            print(f"commit-msg hook 已安装: {commit_msg_hook} -> {commit_msg_source}")
        else:
            print(f"commit-msg hook 已安装（复制模式）: {commit_msg_hook}")
    else:
        print(f"提示: {commit_msg_source} 不存在，跳过 commit-msg hook 安装")

    # 安装 pre-push hook（协议文件大改动自动提示 alignment-review）
    # 备份已有 pre-push hook（与 pre-commit/commit-msg 一致：仅备份非软链的既有 hook）
    pre_push_hook = os.path.join(hook_dir, "pre-push")
    pre_push_source = os.path.join(agate_root, "scripts", "pre-push-gate.sh")
    _backup(pre_push_hook, "pre-push")

    if not os.path.isfile(pre_push_source):
        sys.stderr.write(f"错误: {pre_push_source} 不存在（AGATE_ROOT={agate_root}）\n")
        sys.exit(1)
    _ln_sf(pre_push_source, pre_push_hook)
    _chmod_x(pre_push_source)
    if os.path.islink(pre_push_hook):
        print(f"pre-push hook 已安装: {pre_push_hook} -> {pre_push_source} (协议文件大改动自动提示)")
    else:
        print(f"pre-push hook 已安装（复制模式）: {pre_push_hook}")

    # .gitignore 检测：.state.yaml 被忽略时提醒用 git add -f
    gitignore = os.path.join(repo_root, ".gitignore")
    if os.path.isfile(gitignore):
        state_yaml_ignored = False
        with open(gitignore, encoding="utf-8", errors="replace") as f:
            for line in f:
                if _STATE_YAML_RE.match(line):
                    state_yaml_ignored = True
                    break
        if state_yaml_ignored:
            print("")
            print("⚠️  .gitignore 中忽略了 .state.yaml")
            print("    agate 需要 git add -f 强制暂存 .state.yaml（否则 git add agate-workspace/tasks/ 不会暂存它）")
            print("    建议：从 .gitignore 移除 .state.yaml，或在每次 git add 时记得加 -f")
    # 项目台账登记（2026-09-21）：供 `agate-setup.py --uninstall --all-projects` 定位
    # 装了 hook 的项目。本脚本是 hook 的唯一安装者，直接调它的场景（见 agate/AGENTS.md）
    # 也要能被卸载发现。登记失败不阻断安装（台账是辅助索引，非 gate）。
    try:
        import agate_common
        agate_common.record_project(repo_root)
    except Exception as exc:  # 台账非关键路径，任何失败都不应让装 hook 失败
        print(f"提示: 项目台账登记跳过（{exc}）")




if __name__ == "__main__":
    main()
