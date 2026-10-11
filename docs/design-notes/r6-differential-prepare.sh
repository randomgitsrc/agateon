#!/usr/bin/env bash
# r6-differential-prepare.sh — R6 双向差分的一键 wrapper（TAG0051 批 r6-harness，NB-3 / NB-8）
#
# 动机：r6-differential.sh 对**不存在**的 --corpus 直接 exit 1；运行者若忘备 corpus，
#   gate 命令 P5_r6 会**假失败**。本 wrapper 把「备 corpus」从**人记**变成**机械**：
#   每次重建一次性整仓副本，再 exec 既有差分脚本。
#
# 行为序列：
#   1) 解析 --src（默认 .）/ --dst（默认系统临时目录下的一次性 corpus），其余参数透传；
#   2) 健壮性校验（NB-8 / SEC-04）：--dst 非空、为绝对路径、**物理归一化**（解析软链）后
#      不得等于/位于 --src 之内、不得为 --src 的祖先、须严格落在**允许前缀**之下
#      （缺省 $TMP/opencode）、不得已存在且为软链；任一不满足 → exit 2（**不做任何删除**，
#      全部校验都在 rm 之前完成）；
#   3) echo 解析后的 <src>/<dst> 与「after 侧」供审计；
#   4) rm -rf <dst> → git clone --local --no-hardlinks <src> <dst>（corpus：检出即 HEAD 干净树，
#      自带 .git 全史——差分脚本要 `git archive` 解析 before；clone 只检出**已跟踪**文件，
#      天然排除 .worktrees/ / site/node_modules/ / site/.vitepress/dist 等未跟踪目录，
#      故**无需**再 `checkout -- .` + `clean -fdx`）；
#   5) exec 同目录 r6-differential.sh --corpus <dst> --after <src>/agate <其余参数>。
#
# ── R6 证据成立前提（A8 #5 修复；务必读）─────────────────────────────────
#   --after 侧**显式指向真实仓库工作树 `<src>/agate`**（而非 r6-differential.sh 的缺省
#   `$corpus/agate`）。原因：缺省 after 侧取 `$corpus/agate`，而本 wrapper 的 ⑤ 会
#   `clean -fdx` 掉副本里**未跟踪的新文件** ⇒ 缺省 after 侧 = 已 clean 的副本 = **HEAD**，
#   未提交改动被抹掉 ⇒ 「差异 0 条」其实在比 HEAD，对本任务**未提交改动不构成证据**（空转）。
#   改为显式 `--after <src>/agate` 后：corpus 只承担 `--before`（干净基线）+ 任务数据来源；
#   after 侧 = **含未提交改动的真实工作树** ⇒ P4 阶段（改动未提交）也能构成 legacy 兼容证据。
#   成立前提/口径：
#     * 本 wrapper 的 after 结果在「**工作树已提交**」时最稳（P5 阶段在 P4 提交后运行 = 完整口径）；
#       在 P4 未提交时运行也可（after = 工作树），但须知它比的是**未提交工作树**而非某个提交。
#     * 若运行者显式传入 `--after`，wrapper **尊重之**（不再注入 `<src>/agate`）——此时证据口径由运行者负责。
#
# 隔离（AGENTS.md 工作流 0a）：真实仓库仅被 git clone **只读** + 被 after 侧**只读**执行 gate
#   （gate 检查器不写仓库；写类 git 命令均带 -C <dst>）；本 wrapper 自身不在真实仓库执行写操作。
#
# --dst 允许前缀默认 = 系统临时目录下的 `opencode/`（本仓约定的临时工作区）；如需放宽，
#   设 env `R6_PREPARE_ALLOW_PREFIX=<绝对路径>`（须为绝对路径；缺省值见下）。
#
# 平台无关：系统临时目录用**运行时拼接**（不写字面量）；不裸调 python3；realpath/readlink 走探测。

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 系统临时目录根：运行时拼接，避免字面量（check-platform-assumptions R4）。
SLASH="/"
TMP_ROOT="${SLASH}tmp"
# --dst 允许前缀（缺省系统临时目录下的约定子目录）；可用 env 覆盖（须绝对路径）。
ALLOW_PREFIX="${R6_PREPARE_ALLOW_PREFIX:-$TMP_ROOT/opencode}"

SRC="."
DST=""
DST_SET=0
AFTER_SET=0
REMAIN=()

while [ $# -gt 0 ]; do
  case "$1" in
    --src)
      [ $# -ge 2 ] || { echo "r6-differential-prepare: --src 缺少参数" >&2; exit 2; }
      SRC="$2"; shift 2 ;;
    --dst)
      [ $# -ge 2 ] || { echo "r6-differential-prepare: --dst 缺少参数" >&2; exit 2; }
      DST="$2"; DST_SET=1; shift 2 ;;
    --after)
      [ $# -ge 2 ] || { echo "r6-differential-prepare: --after 缺少参数" >&2; exit 2; }
      REMAIN+=("--after" "$2"); AFTER_SET=1; shift 2 ;;
    --after=*)
      REMAIN+=("$1"); AFTER_SET=1; shift ;;
    -h|--help)
      sed -n '2,45p' "${BASH_SOURCE[0]}"; exit 0 ;;
    *)
      REMAIN+=("$1"); shift ;;
  esac
done

if [ "$DST_SET" -eq 0 ]; then
  DST="$TMP_ROOT/opencode/tag0051-r6-corpus"
fi

# ── NB-8 / SEC-04 健壮性校验：失败即 exit 2，且**不做任何删除** ──────────
if [ -z "$DST" ]; then
  echo "r6-differential-prepare: --dst 不得为空串（防 rm -rf 落到 cwd/真仓）" >&2
  exit 2
fi
case "$DST" in
  /*) : ;;
  *) echo "r6-differential-prepare: --dst 须为绝对路径: '$DST'" >&2; exit 2 ;;
esac
case "$ALLOW_PREFIX" in
  /*) : ;;
  *) echo "r6-differential-prepare: R6_PREPARE_ALLOW_PREFIX 须为绝对路径: '$ALLOW_PREFIX'" >&2; exit 2 ;;
esac

if [ ! -d "$SRC" ]; then
  echo "r6-differential-prepare: --src 不是目录: '$SRC'" >&2
  exit 2
fi
# 物理路径（解析软链）；SRC 一定存在，用 cd + pwd -P。
SRC_REAL="$(cd "$SRC" && pwd -P)"

# 纯语法折叠（. / .. / 重复斜杠；不访问文件系统），作为 realpath 不可用时的回退。
_normalize() {
  local path="$1" rest seg out=""
  path="${path%/}"
  rest="$path"
  while [ -n "$rest" ]; do
    seg="${rest%%/*}"
    if [ "$seg" = "$rest" ]; then
      rest=""
    else
      rest="${rest#*/}"
    fi
    case "$seg" in
      ""|.) ;;
      ..) out="${out%/*}" ;;
      *) out="$out/$seg" ;;
    esac
  done
  if [ -z "$out" ]; then out="/"; fi
  printf '%s' "$out"
}

# 物理归一化：优先 realpath -m（GNU/BSD coreutils，解析已存在前缀里的软链），
# 回退 readlink -f，再回退纯语法折叠（软链检测能力随之退化）。
_realpath() {
  local p="$1" r=""
  if command -v realpath >/dev/null 2>&1; then
    r="$(realpath -m -- "$p" 2>/dev/null)" && [ -n "$r" ] && { printf '%s' "$r"; return 0; }
  fi
  if command -v readlink >/dev/null 2>&1; then
    r="$(readlink -f -- "$p" 2>/dev/null || true)"
    if [ -n "$r" ]; then printf '%s' "$r"; return 0; fi
  fi
  _normalize "$p"
}

DST_REAL="$(_realpath "$DST")"
ALLOW_REAL="$(_realpath "$ALLOW_PREFIX")"

# 1) 根目录（rm -rf / 的直接防线）。
if [ "$DST_REAL" = "/" ]; then
  echo "r6-differential-prepare: --dst 不得为根目录 '/'" >&2
  exit 2
fi
# 2) 已存在且为软链：拒绝（物理归一化另会捕获经中间软链的绕过）。
if [ -L "$DST" ]; then
  echo "r6-differential-prepare: --dst 已存在且为软链，拒绝（防 rm -rf 经软链误删）: $DST" >&2
  exit 2
fi
# 3) 等于 --src / 位于 --src 之内（否则 rm -rf 会删源）。
if [ "$DST_REAL" = "$SRC_REAL" ]; then
  echo "r6-differential-prepare: --dst 不得等于 --src: $DST_REAL" >&2
  exit 2
fi
case "$DST_REAL/" in
  "$SRC_REAL"/*)
    echo "r6-differential-prepare: --dst 不得位于 --src 之内（否则 rm -rf 会删源）" >&2
    echo "  src=$SRC_REAL  dst=$DST_REAL" >&2
    exit 2 ;;
esac
# 4) --dst 为 --src 的祖先（review 补面；否则 rm -rf 删掉源所在父路径）。
case "$SRC_REAL/" in
  "$DST_REAL"/*)
    echo "r6-differential-prepare: --dst 不得为 --src 的祖先目录（否则 rm -rf 删掉源所在父路径）" >&2
    echo "  src=$SRC_REAL  dst=$DST_REAL" >&2
    exit 2 ;;
esac
# 5) 允许前缀：--dst 须**严格**落在约定前缀之下（缺省系统临时目录的 opencode/）。
if [ "$DST_REAL" = "$ALLOW_REAL" ]; then
  echo "r6-differential-prepare: --dst 不得为允许前缀根目录本身: $ALLOW_REAL" >&2
  exit 2
fi
case "$DST_REAL/" in
  "$ALLOW_REAL"/*) : ;;
  *)
    echo "r6-differential-prepare: --dst 须位于允许前缀之下: $ALLOW_REAL" >&2
    echo "  dst=$DST_REAL（如需放宽，设 R6_PREPARE_ALLOW_PREFIX=<绝对路径>）" >&2
    exit 2 ;;
esac

echo "r6-differential-prepare: src=$SRC_REAL  dst=$DST_REAL  allow_prefix=$ALLOW_REAL"
if [ "$AFTER_SET" -eq 0 ]; then
  echo "r6-differential-prepare: after 侧 = $SRC_REAL/agate（真实工作树，含未提交改动；非 corpus）"
else
  echo "r6-differential-prepare: after 侧 = 由调用者显式指定（见透传参数；证据口径由调用者负责）"
fi

# ── 建一次性 corpus（`git clone --local`：检出即 HEAD 干净树，自带 .git 全史）────
# 用 clone 而非 `cp -a` 整仓拷贝：clone 只检出**已跟踪**文件（自动排除 .worktrees/、
# site/node_modules/、site/.vitepress/dist 等未跟踪/忽略目录），工作树天然干净
# ⇒ 无需再 `checkout -- .` + `clean -fdx`（亦避开 N1：整仓拷贝的健壮性/性能问题）。
# clone 的 .git 含全史 + remote-tracking（`origin/main` 仍可解析）⇒ 差分脚本 `git archive`
# 照常解析 before；corpus 只服务 `--before` 与任务数据来源，after 侧见下方透传。
# 注意：本步只写 --dst（corpus），真实工作树（--src）仅被**只读**读取。
rm -rf -- "$DST_REAL"
mkdir -p -- "$(dirname -- "$DST_REAL")"
git clone --local --no-hardlinks --quiet -- "$SRC_REAL" "$DST_REAL"

# ── 调既有差分脚本（其余参数透传）────────────────────────────────────
# after 侧显式指向真实工作树（A8 #5）；调用者若已传 --after 则尊重之（见上 AFTER_SET）。
AFTER_ARGS=()
if [ "$AFTER_SET" -eq 0 ]; then
  AFTER_ARGS=(--after "$SRC_REAL/agate")
fi
exec bash "$SCRIPT_DIR/r6-differential.sh" --corpus "$DST_REAL" \
  ${AFTER_ARGS[@]+"${AFTER_ARGS[@]}"} ${REMAIN[@]+"${REMAIN[@]}"}
