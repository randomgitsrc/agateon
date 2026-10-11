# P4 progress — implementer D（批 r6-harness + P3 观察项）

- [PROD_NOT_TOUCHED] 真实仓库只读；所有写类 git 命令带 `-C <dst>`；wrapper 写面仅 `--dst`（绝对路径、且在 `/tmp/opencode` 类 scratch 根下）。

## 新增文件（仅 3 个）
- `docs/design-notes/r6-differential-prepare.sh`（R6 差分一键 wrapper，NB-3 / NB-8）
- `agate/tests/fixtures/task-data/level-2/pass/README.md`（P3 观察项补体例）
- `agate/tests/fixtures/task-data/level-2/fail/README.md`（P3 观察项补体例）

## 自检实测
### ① 语法 `bash -n`
`bash -n docs/design-notes/r6-differential-prepare.sh` → OK（rc=0）

### ② shellcheck（本仓 CI required 检查）
`shellcheck docs/design-notes/r6-differential-prepare.sh` → rc=0（默认与 `-S warning` 均 0）。
首版 `TMP_ROOT="/"+"tmp"` 触发 SC2140（warning）→ 改为 `SLASH="/"` + `TMP_ROOT="${SLASH}tmp"`（运行时拼接，源文本仍无字面量 `/tmp`）后清零。

### ③ 健壮性负例实跑（三种均报错退出，且不删任何东西）
| 输入 | rc | stderr |
|---|---|---|
| `--src . --dst ""` | 2 | `--dst 不得为空串（防 rm -rf 落到 cwd/真仓）` |
| `--src . --dst relative/path` | 2 | `--dst 须为绝对路径: 'relative/path'` |
| `--src <tmp>/d-src --dst <tmp>/d-src/corpus-inside` | 2 | `--dst 不得位于 --src 之内（否则 rm -rf 会删源）` |
负例后核验：源目录 `<tmp>/d-src/` 内容仍在；`<tmp>/d-src/corpus-inside` 未被创建（"没有那个文件或目录"）；
真实仓库 `git status --porcelain` 跑前/跑后 **SAME**；默认 corpus 路径未被创建。

### ④ 平台假设扫描
`python3 /home/kity/.agate/v0.81.0/agate/scripts/check-platform-assumptions.py docs/design-notes/r6-differential-prepare.sh` → rc=0（0 命中）；
`grep -nF '/tmp'` 源文件 → 无命中（rc=1）。

### 正例冒烟（用 `/tmp/opencode` 下真副本）
`bash docs/design-notes/r6-differential-prepare.sh --src /tmp/opencode/d-smoke-src --dst /tmp/opencode/d-smoke-corpus`：
- 输出 `r6-differential-prepare: src=... dst=...`（审计行）；
- 输出 `r6-differential: before=581369fc... after=/tmp/opencode/d-smoke-corpus/agate allow=.../r6-allowlist.yaml`（**未报 `corpus 不存在`**）；
- 输出 `r6-differential: legacy 任务 39 个，差异 0 条，未匹配 0 条`；
- `wrapper rc=0`（差分脚本跑后"原仓（corpus）干净"自核验亦通过）。
真实仓库核验：`git status --porcelain` 在冒烟期间观察到的 `M` 与新 `??` 文件**全为 A/B/C sibling 实现者的并发产出**（`check-gate.py`/`rules/*`/`UPGRADING.md`/`LEVELS.yaml`/`level-2.yaml`/`P4-progress-implementer-A,B.md` 等）；排除这些后，仓库内**无** wrapper 引入的改动，且未出现 corpus 副本目录。wrapper 写面仅 `--dst`（不在仓库内）。

## 未做 / 边界
- 未改任何既有文件（含 P3 红灯判据 `agate/tests/unit/test_tag0051_r6_harness.py`、`level-2/*/gate-events.jsonl`）。
- **自查 ≠ gate**：以上为自查，未声称 P5 通过。
- README 中 `level-2.yaml` 引用为前向引用；本轮冒烟时该文件已由 sibling 批（delivery-contract）落地。
