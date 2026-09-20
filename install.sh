#!/usr/bin/env bash
# install.sh — Agateon 协议安装脚本（版本管理布局）
# 用法：install.sh [--versions]   （无参与 --versions 等价；其他参数 → 用法 + exit 2）
#
# 行为：把 $AGATE_HOME（默认 ~/.agate）建成版本管理布局的目录根——含 repo/ 主克隆、
# 本体包形态的 vX.Y.Z/ 版本目录、latest/current 指针与根 scripts/ 入口副本。
# 版本根基址可经 AGATE_HOME 覆盖；主克隆的上游可经 AGATE_REPO_URL 覆盖。
#
# ~/.agate 是旧软链布局时拒绝并给出迁移三步（fail-closed，先于任何 git 调用）。
# 后续升级 / 钉版本 / 回退用版本管理工具：
#   python3 ~/.agate/scripts/agate-install.py            # 装最新版
#   python3 ~/.agate/scripts/agate-install.py <vX.Y.Z>   # 预装指定版本

set -euo pipefail

# 废弃环境变量：任一被设置 → 一行 WARNING，然后忽略（不创建其指向的路径）。
if [ -n "${AGATE_REPO_DIR+x}" ] || [ -n "${AGATE_SYMLINK+x}" ]; then
    echo "WARNING: 环境变量 AGATE_REPO_DIR / AGATE_SYMLINK 已废弃且被忽略（v0.73.0 起不再有单软链安装路径；版本根用 AGATE_HOME 指定）。" >&2
fi

# 参数：无参或 --versions（等价）；其他 → 用法 + exit 2
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--versions" ]; }; then
    echo "用法: install.sh [--versions]   （无参与 --versions 等价）" >&2
    exit 2
fi

# 变量名用 AGATE_VER_ROOT 而非 AGATE_HOME——后者已是环境变量（版本根基址，DEBT0042），
# 同名会把环境变量遮蔽为本地赋值，造成"设了 env 却被忽略"的静默分叉。
AGATE_VER_ROOT="${AGATE_HOME:-$HOME/.agate}"

# 规范化：循环剥离尾部 `/` 与 `/.`（`[ -L "L/" ]` 为假会绕过软链守卫）；含 `..` 分量则拒绝。
while :; do
    case "$AGATE_VER_ROOT" in
        ?*/) AGATE_VER_ROOT="${AGATE_VER_ROOT%/}" ;;
        ?*/.) AGATE_VER_ROOT="${AGATE_VER_ROOT%/.}" ;;
        *) break ;;
    esac
done
case "/$AGATE_VER_ROOT/" in
    */../*)
        echo "错误: AGATE_HOME（$AGATE_VER_ROOT）含 .. 分量——软链守卫无法可靠判定，请使用不含 .. 的规范路径。" >&2
        exit 1
        ;;
esac

if [ -L "$AGATE_VER_ROOT" ]; then
    echo "检测到的软链：$AGATE_VER_ROOT → $(readlink "$AGATE_VER_ROOT" || true)" >&2
    cat >&2 <<'EOF'
错误: ~/.agate 是旧软链布局，v0.73.0 起不再支持；install.sh 会穿透软链把 repo/ 与 vX.Y.Z/ 静默建进源仓库，已拒绝（fail-closed）。
迁移到版本管理布局（三步）：
  1. 备份软链:  mv ~/.agate ~/.agate.bak
  2. 建目录根:  mkdir -p ~/.agate
  3. 装版本:    install.sh --versions
               # 迁移完成后亦可: python3 ~/.agate/scripts/agate-install.py latest
EOF
    exit 1
fi

PY=""
for c in python3 python; do
    if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
    echo "错误: install.sh 需要 python3（未找到 python3/python）" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$AGATE_VER_ROOT"
if [ ! -d "$AGATE_VER_ROOT/repo/.git" ]; then
    git clone -- "${AGATE_REPO_URL:-https://github.com/randomgitsrc/agateon}" "$AGATE_VER_ROOT/repo"
fi
# 优先用刚 clone 的 repo 副本内的安装器（curl … | bash 场景下
# $SCRIPT_DIR 是当前工作目录、无 agate/scripts/）；仅 repo 缺失时回退 $SCRIPT_DIR。
INSTALLER="$AGATE_VER_ROOT/repo/agate/scripts/agate-install.py"
[ -f "$INSTALLER" ] || INSTALLER="$SCRIPT_DIR/agate/scripts/agate-install.py"
exec "$PY" "$INSTALLER" latest
