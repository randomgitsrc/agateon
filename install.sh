#!/usr/bin/env bash
# install.sh — agate 协议安装脚本（单软链布局，兼容保留）
# 默认把仓库克隆到 $HOME/oclab/agate，创建 ~/.agate 软链接
# 可通过环境变量 AGATE_REPO_DIR 自定义安装目录
#
# ⚠️ 兼容保留说明（TAG0008）：本脚本保持"单软链"形态，存量用户升级路径不破坏。
# 需要按项目锁定版本时，改用版本管理工具（TAG0008 起）：
#   python3 ~/.agate/scripts/agate-install.py            # 装最新版（vX.Y.Z/ 版本目录 + latest/current 指针）
#   python3 ~/.agate/scripts/agate-install.py v0.48.0    # 装指定版本
# 版本管理布局下 ~/.agate 变为目录，legacy 软链直接解析为 AGATE_ROOT（向后兼容，见 UPGRADING v0.50.0）。

set -euo pipefail

# --versions：进入「版本管理布局」（TAG0032）。~/.agate 变目录根，含 repo/ 主克隆 +
# vX.Y.Z/ 版本 worktree + latest/current 指针 + 根 scripts/ 入口副本。原无参「单软链」路径不变。
if [ "${1:-}" = "--versions" ]; then
    AGATE_HOME="$HOME/.agate"
    if [ -L "$AGATE_HOME" ]; then
        cat >&2 <<'EOF'
错误: ~/.agate 是 legacy 软链布局，install.sh --versions 会穿透软链把 repo/ 与 vX.Y.Z/ 静默建进源仓库，已拒绝（fail-closed）。
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
        echo "错误: install.sh --versions 需要 python3（未找到 python3/python）" >&2
        exit 1
    fi
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    mkdir -p "$AGATE_HOME"
    if [ ! -d "$AGATE_HOME/repo/.git" ]; then
        git clone "${AGATE_REPO_URL:-https://github.com/randomgitsrc/agateon}" "$AGATE_HOME/repo"
    fi
    # 优先用刚 clone 的 repo 副本内的安装器（curl … | bash -s -- --versions 场景下
    # $SCRIPT_DIR 是当前工作目录、无 agate/scripts/）；仅 repo 缺失时回退 $SCRIPT_DIR。
    INSTALLER="$AGATE_HOME/repo/agate/scripts/agate-install.py"
    [ -f "$INSTALLER" ] || INSTALLER="$SCRIPT_DIR/agate/scripts/agate-install.py"
    exec "$PY" "$INSTALLER" latest
fi

INSTALL_DIR="${AGATE_REPO_DIR:-$HOME/oclab/agate}"
LINK_TARGET="$INSTALL_DIR/agate"
LINK_NAME="${AGATE_SYMLINK:-$HOME/.agate}"

if [ -d "$INSTALL_DIR/.git" ]; then
    echo "仓库已存在: $INSTALL_DIR"
    cd "$INSTALL_DIR" && git pull
else
    echo "克隆仓库到: $INSTALL_DIR"
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone https://github.com/randomgitsrc/agateon.git "$INSTALL_DIR"
fi

if [ -L "$LINK_NAME" ]; then
    CURRENT=$(readlink "$LINK_NAME")
    if [ "$CURRENT" = "$LINK_TARGET" ]; then
        echo "软链接已正确: $LINK_NAME -> $LINK_TARGET"
    else
        echo "更新软链接: $LINK_NAME (原指向 $CURRENT)"
        ln -sfn "$LINK_TARGET" "$LINK_NAME"
    fi
elif [ -d "$LINK_NAME" ]; then
    echo "错误: $LINK_NAME 是现有目录（非软链接），请手动处理" >&2
    echo "建议: mv $LINK_NAME ${LINK_NAME}.bak && ln -s $LINK_TARGET $LINK_NAME" >&2
    exit 1
else
    ln -s "$LINK_TARGET" "$LINK_NAME"
    echo "创建软链接: $LINK_NAME -> $LINK_TARGET"
fi

echo ""
echo "安装完成。"
echo "  仓库: $INSTALL_DIR"
echo "  软链接: $LINK_NAME -> $LINK_TARGET"
echo ""
echo "自定义位置:"
echo "  AGATE_REPO_DIR=/path/to/clone bash install.sh   # 指定仓库路径"
echo "  AGATE_SYMLINK=/path/to/symlink bash install.sh # 指定软链接路径"
echo ""
echo "下一步:"
echo "  在项目里按 $LINK_NAME/SETUP.md 的步骤把 orchestrator 注册成"
echo "  OpenCode/Claude Code 能调用的 agent（含装 hook 那一步）"
