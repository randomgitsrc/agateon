# Agateon 开发指引

> 面向**修改 Agateon 协议/脚本的开发者**。协议使用者看 `agate/AGENTS.md`。
> 新会话/新开发者先读 `docs/guides/project-map.md`（整仓导航地图）。
> 本文件只收录"不读就不知道"的内容——项目特定规则、本机环境事实、历史教训。能从仓库自己读到的
> （目录结构、依赖、命令、CI 配置、协议正文）不重复，见各权威源（`agate/AGENTS.md`、
> `pyproject.toml`、`.github/workflows/`、`agate/tests/README.md`）。
> 不写死可从仓库自主发现的时变数字统计（用例数 / commit 数 / 条目数 / HEAD 日期）——需要时用命令或权威源指针替代。文档选材与保鲜完整原则见 `docs/guides/doc-freshness-guide.md`。

## 仓库四块

- `<仓库根>/`：开发资料（README / CHANGELOG / docs/ / archived/）+ 本文件。**开发 checkout**——正常改动走 worktree（见下方「hotfix 通道」的例外）
- `agate/`：协议本体。改它触发 SELF-GATE（见下）。**运行时稳定版来自 `~/.agate/current/agate/`**（版本管理布局，与开发 checkout 解耦，见「本机稳定版布局」）
- `agate-workspace/`：任务数据（tasks/、roadmap/、debt/、reviews/ 等）。roadmap 回写 `done` 是 P8 gate 硬校验（RM-AG0043）
- `site/`：产品 Web 层（VitePress 站点源码：首页/博客）。属于产品对外内容，**在协议 gate 治理之外**——改它不触发 SELF-GATE，detect-docs-only 视其改动为 docs-only（跳过全量 pytest/shellcheck）。唯一硬校验 = `npm run build` 通过。品牌唯一权威源在 `docs/brand/`，`site/public/` 是构建快照（`npm run sync:brand` + `sync-covers.mjs` 生成，不入库；博客封面同步到 `public/covers/` 供列表页引用）。**接博客任务先读**：文档索引 `site/guides/README.md`，机械流程见 `site/guides/CONTRIBUTING.md`，质量标准见 `site/guides/BLOG-STANDARDS.md`（发布前必须过独立评审）

## 改动通道：worktree 优先，hotfix 例外

> **默认**：任何改动走 worktree（隔离、可回滚、gate 完整）+ PR。**这一条覆盖绝大多数场景**。
>
> **hotfix 通道**：满足**全部**下列条件时，**可不开 worktree**（直接在开发 checkout 改 → 分支 → PR）：
>
> | # | 条件 | 判据 |
> |---|------|------|
> | 1 | **改动面极小** | ≤2 个文件，且无跨模块影响 |
> | 2 | **不触发 SELF-GATE** | 不碰 `agate/scripts/*`、`agate/*.md`、`agate/**/*.md`、`agate/rules/*.yaml`、**`AGENTS.md`**、**`README.md`**（后两者也在 hook 触发面内，见 `commit-msg-self-gate.py` 正则） |
> | 3 | **不产生阶段产出** | 无 P0-brief/.state.yaml/P1-P8 产物（即：不是 agate 任务，是一次性修复） |
> | 4 | **可快速验证** | 有明确判据（如单测 + 目标命令 exit code），不需多轮评审 |
>
> **典型 hotfix**：配置 key 对齐上游 schema、文案修正、单文件 bug 修复、CI 配置微调。
>
> **不适用 hotfix**（必须走 worktree）：
> - 任何 `agate/` 协议本体或脚本改动（触发 SELF-GATE，需独立评审）
> - 需要阶段产出/看板登记/roadmap 回写的改动（= agate 任务）
> - 改动跨多个子系统或需探索性设计
>
> **hotfix 也走 PR**（不直接推 main——main 受保护），只是不开 worktree、不建任务目录。

## 本机稳定版布局（`~/.agate`）

`~/.agate` 是**版本管理根目录**（非软链），与开发 checkout **解耦**：

```
~/.agate/
├── repo/              # 从 origin clone 的独立仓库副本
├── vX.Y.Z/            # 各已安装版本目录（含 agate/ 与 agate-workspace/）
├── latest → vX.Y.Z    # 指针：最新已安装版
├── current → latest   # 指针：当前使用版
└── scripts/           # 单源副本（随安装/升级刷新，非软链）
```

**关键含义**（对开发者的影响）：

| 事实 | 说明 |
|------|------|
| **稳定版来源** = `~/.agate/current/` | **不是**开发 checkout——改开发 checkout 的 `agate/` **不影响** hook/工具链判定（避免"用未验证的新 gate 判自己"） |
| hook 是**固定解析入口** | `.git/hooks/*` → `~/.agate/scripts/resolve-entry.py`，运行时按项目 `.agate-version` 解析版本再 exec——**切版本无需重装 hook** |
| 项目可**钉版本** | 项目根 `.agate-version` 写 `agate: vX.Y.Z`；不写则用 `current`。⚠️ 声明未安装版本 → **警告 + 回退全局**（exit 0），须用 `agate-resolve.py` 确认实际解析 |

**安装 / 迁移 / 更新 / 回退 / hook 重装时机 / 根 `scripts/` 维护语义** → 权威源 `agate/UPGRADING.md`「版本管理生命周期」节（单一权威口径），本文件不重复。

**历史**：本机 2026-09-18 起使用版本管理布局（稳定版与开发 checkout 解耦）；软链形态的 `~/.agate` 自 v0.73.0 起不再支持，迁移指引见 `agate/UPGRADING.md`「v0.73.0」节。

## 改脚本的工作流

0. **新增 CHECK 上线前先全量扫描存量**：新增 CHECK/规则前，先对既有协议文档与数据面做全量扫描，确认新规则不误伤存量条文（DEBT0025）
1. **先加失败测试确认红** → 改脚本转绿
2. `python3 agate/scripts/check-protocol-consistency.py` 必须 0 ERROR（`--strict` 连 WARNING 都阻断；`--strict-errors-only` 只按 ERROR 判失败，docs-only PR 用它）
3. `bash agate/tests/scripts/count-tests.sh` 确认用例数未漂移
4. 新 bug 先写 `regression/` 测试再修
5. 暂存区含 self-gate 触发文件时，commit message 须含 `self-gate-review:` 路径或 `self-gate-skip:` 理由（commit-msg hook 检查，WARNING 不拦截）；触发文件面见 `SELF-GATE.md`

## Gate 脚本分层

- 所有 `git diff` 用 `--cached`，不用 `HEAD~1`——pre-commit hook 运行时 commit 还没创建
- `grep -c || echo 0` 后必须 `| tail -1`——grep 无匹配 exit 1，`|| echo 0` 产生双行
- `printf '%b' "$VAR"`，不用 `printf '%s'`（不解释 `\n`）也不用 `printf "$VAR"`（SC2059）
- Python 调用用 `os.environ`，不用 `open('$VAR')`——shell 注入风险
- 所有脚本 `set -euo pipefail`
- `agate_common.py` 是公共函数库（被 import，不直接执行）：`write_gate_result` / `read_state_phase` / `read_state_task_id` / `resolve_workspace` 等
- 3 个 hook 是 sh 薄壳（`pre-commit-gate.sh` / `commit-msg-self-gate.sh` / `pre-push-gate.sh`），只做 AGATE_ROOT 自定位 + python 探测 + exec py 主程序；python 探测支持 `AGATE_PYTHON` 显式覆盖（Windows Store python3 占位符规避，DEBT0014）

## 依赖

运行 Agateon 只需系统 `python3` + `pyyaml`；开发 Agateon 本体另需 `ruff`（CI 锁 `ruff==0.16.4`）。完整清单与版本锁定见 `pyproject.toml` + `.github/workflows/protocol-tests.yml`，不在此重复。

## 测试约定（平台无关是硬约束）

- 测试**不得硬编码单平台假设**：不裸 `PATH="/usr/bin:/bin"`、不裸 `python3`（探测 `python3|python`）、不假设 POSIX symlink 语义（Windows `ln -sf` 退化为复制）、不用 `/tmp`（用 pytest `tmp_path` fixture）
- 平台差异场景**按平台分支断言**（Linux 断软链，Windows 断"复制模式 + WARNING"）或用模拟环境覆盖
- Linux 全量覆盖；Windows CI 只跑 `-m windows_smoke` 冒烟（每文件第 1 个用例 + 平台敏感关键词用例）
- fixture 细节读 `agate/tests/conftest.py`；CI 无 `~/.agate`，conftest 用 `AGATE_ROOT` env 覆盖（本地可设）或从 tests/ 上溯反推

## dogfooding 工作流（Agateon 自身改造任务必读）

> **触发块**：任何 Agateon 自身改造任务（TAG0004+）需要隔离 worktree 时，**必须先读**：
> - 构建流程：`docs/guides/worktree-dogfooding-guide.md`（10 步标准流程）
> - 交接单模板：`agate/assets/templates/handoff-template.md`（复制到 worktree 根 `HANDOFF-{Txxx}.md` 填写）

- **双工作区**：改造对象 = worktree 的 `agate/`；开发工具 = `~/.agate`（稳定版，**勿动**）。跑 gate/读卡片用 `~/.agate`，改代码/跑测试在 worktree
- **gate 工具 ≠ 检查对象**：commit hook 用 `~/.agate`（稳定版）判定；但 `check-protocol-consistency.py` **必须用 worktree 自己的**（`python3 agate/scripts/check-protocol-consistency.py`——检查对象是 worktree 里的协议文件；用 `~/.agate` 的会扫到稳定版目录 `~/.agate/current/`，而非你的改动）
- **编排/派发类工具一律用 `~/.agate/scripts/` 稳定版**：`agate-inject-card.py` / `agate-render-dispatch-prompt.py` / `agate-next-card.py` 等有 AGATE_ROOT 自解析逻辑，worktree 相对路径调用会读到 worktree 正在修改的协议卡片，把未发布的新机制注入任务（TAG0016 教训）
- `~/.agate` 脚本显示**稳定版上下文**（`agate-summary.py` 显示 `AGATE_ROOT=~/.agate/vX.Y.Z/agate` + 版本号，**不是**你的 worktree/开发 checkout 状态——后者用 `git log`/`git status` 看）

**工具纪律（本环境实战验证，T001/TAG0004 起）**：
- bash 一律加 `timeout`（外层 `timeout N cmd`，N 按预期耗时 30-90s），工具 timeout 参数同步设——无 timeout 的 bash 多次被 abort/挂起
- 单步串行不并行 bash（并行是 abort 高危）；卡住就换路不重试同一 bash，改用 read/grep/glob 工具（不走 bash 通道）
- 全量 pytest 分 unit/regression/integration 片跑、每片大 timeout、片内加 `-n auto` 并行（约 3.5x 提速；套件按隔离设计可安全并行）。**完整 CI 口径**（含 flaky 兜底的 `--reruns` 与所需插件）见 `agate/tests/README.md`——本机验证前先对齐，否则可能把已知 flaky 当新缺陷追；gate/consistency 单跑
- 输出控制在几十行内；先看全输出再分析，不用 tail 截断（count-tests 教训：数字被 tail 吞掉误判）
- commit 前检查 hook 会跑什么：pre-commit 按 .state.yaml phase 跑 check-gate，commit 时 phase 应与本次产出一致（P1 产出 → phase=P1 再 commit），否则 hook 拦截
- hook 在共享 git 目录：worktree 的 `.git/hooks` 为空，hook 实际在 `<主 checkout>/.git/hooks/`（pre-commit / commit-msg / pre-push 软链已装），改 hook 装那里。权威取值 `git rev-parse --git-path hooks`（`core.hooksPath` 覆盖时也认）——`install-hook.py` / `agate-setup.py` 据此安装与卸载，故 **worktree 内可直接跑接入/卸载命令，无需按 worktree 各装一次**；反之在 worktree 里 `--uninstall` 会清掉主 checkout 的 gate（仓库级动作，多任务并行别顺手卸）
- CI 等待用 `gh pr checks <PR> --watch [--fail-fast]`，不手写 jq 轮询（2026-08-18 教训）
- **docs/site 改动走快路径、不被全量 CI 卡死的机理与准则**：见 `docs/guides/ci-docs-only-playbook.md`（2026-08-26：`on:[push,pull_request]` 双跑 + 建分支 push 的 `before` 全零致 fast-pass 失效，已修为 detect-docs-only 对全零 before 回退 diff 对 origin/main）
- git 脚本不在 bash PATH 时用绝对路径：`/home/kity/bin/git-to-pr` / `/home/kity/bin/git-to-main`（非交互 shell 不读 bashrc，2026-08-18 确认）

## 版本发布清单（教训浓缩）

1. pytest 全绿 + 0 consistency ERROR + 0 shellcheck error（用例数以 `count-tests.sh` 为准）
2. 更新 `README.md` version badge + `CHANGELOG.md` [Unreleased] → 新版本号
3. **更新 `agate/UPGRADING.md` 新增本版本章节**——无破坏性变更也写"（无破坏性变更）"（v0.62.0 教训：漏写章节）
4. `git tag vN.N.0 && git push origin vN.N.0`——`git push` 不带 tag **默认不推送 tag**（v0.51.0 教训）；推送后 `git ls-remote --tags origin vN.N.0` 验证远端到达
5. CHECK 7（version badge vs git tag）自动通过；CI ruff job 绿（`ruff==0.16.4`，与本地 `~/.venvs/agate-dev/bin/ruff` 对齐，RM-AG0037 required check）
5a. **Release 校验（tag 与 Release 双轨，TAG0037）**：推送 `vN.N.0` 后 `.github/workflows/release.yml` 自动构建并创建 GitHub Release；`gh release view vN.N.0` 须存在，且资产至少含 3 个 tarball——本体 `agateon-vN.N.0.tar.gz` 与两平台 offline 包（`agateon-vN.N.0-offline-linux-x86_64.tar.gz`、`agateon-vN.N.0-offline-windows-x86_64.tar.gz`），另有 `SHA256SUMS`（仅防下载损坏，不认证发布者）。
   - **补救（tag 已推而 Release 缺失）**：release workflow 没有 `workflow_dispatch`，无法手动重跑——本地用同一打包脚本重建：`python3 agate/scripts/agate-release.py build --tag vN.N.0 --repo . --outdir <dist> --notes-out <notes.md> --expect-sha <tag 提交 SHA>`，再 `gh release create vN.N.0 <dist>/* --verify-tag --title vN.N.0 --notes-file <notes.md>`。Release 已存在时重跑会失败，须先确认其属本次创建再 `gh release delete`。
   - **建议（非代码项）**：为 `v*` tag 启用 GitHub tag Ruleset / tag 保护，只允许维护者创建 tag（release workflow 以 tag push 为唯一触发器）。
6. **release PR 合并后最终验证（G-5）**：`git fetch origin && git describe --tags origin/main` == vN.N.0；`git merge-base --is-ancestor vN.N.0 origin/main` 返回 0；合并后 push 的 CI 全绿；`gh release view vN.N.0` 显示 Release 存在且含上述资产

**版本引用文件清单（Agateon 仓库特有，通用 P8 卡不覆盖）**：README badge / CHANGELOG / UPGRADING 章节 / 稳定版引用（文档优先写"稳定版"不写死版本号）。

**CI 一致性失败诊断（E-3，v0.51.0 教训）**：本地绿 CI 红 → 先拉 CI job 完整日志（`gh api repos/{owner}/{repo}/actions/jobs/{id}/logs`）看真实 FAIL 的 `CHECK N` 归属，**禁止臆测根因**；CHECK 7 FAIL 第一排查项 `git ls-remote --tags origin vN.N.N`。

**release PR 必须普通 merge（`--no-ff`），禁止 squash**：CHECK 7（`check_version_badge`）与 G-5 验证都用 `git describe --tags --abbrev=0` 取最新 tag；squash 生成内容相同但 SHA 不同的新提交，tag 与 main 分叉、describe 回退旧版（v0.31.0 事故）。若确实用了 squash：`git tag -f vN.N.0 <main-commit> && git push origin vN.N.0 --force`。
