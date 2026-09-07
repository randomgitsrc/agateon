# P0-brief — TAG0032 版本管理生命周期可用性批（RM-AG0058 整合 epic）

> 本文件由主 Agent 亲自填写（P0 阶段产出）。来源：RM-AG0058（2026-09-03 官方指引实机验证失败 + 2026-09-07 生命周期分析）。
> 三个断点同属"版本管理生命周期"一条链（入口 → 安装形态 → 更新）——**整合单 task**（拆开则每段都依赖前段闭环才能端到端验收）。

## task

"修复版本管理（TAG0008 v1）生命周期的三个断点，使'全新机器 → 版本布局 → 项目钉版 → 更新'全链路真实可用：① **入口断链**——legacy 软链布局下按官方指引跑 `agate-install` 会穿透软链，把 `repo/` 主克隆与 `vX.Y.Z` worktree **静默建进源仓库 agate/ 目录内部**（2026-09-07 隔离 HOME 实测：repo 实体落 `src/agate/repo`，污染源仓库且无任何提示）；先删软链再装则 `~/.agate/scripts` 不存在（install 不建根 scripts，版本工具只在 `repo/agate/scripts/`）→ README 入口命令直接 No such file——**两条进入路径均死路**；② **元仓库 gap（RM-AG0058 本体）**——装出的版本目录 = agateon 整仓（协议在 `agate/` 子目录），resolve 命中版本后返回 vdir（仓库根），gate 消费方找 `vdir/scripts/pre-commit-gate.py` 不存在（实际在 `vdir/agate/scripts/`）→ 项目钉 `.agate-version` 后 commit 被阻断（TAG0008 测试用'根即协议'模拟 repo，从未覆盖元仓库形态，2026-09-03 实测复现）；③ **无 update 入口**——legacy 升级 = 手动 git pull（无文档指引）、版本布局升级 = agate-install latest（入口又是断链），hook 是否随版本重装散落在 UPGRADING 各版本节。"

### scope

- **Phase 1（入口断链修复）**：`agate-install.py` 检测 agate_home 为软链时 **fail-closed 拒绝**并输出可操作迁移指引（防穿透污染源仓库）；install 完成后**建立根 scripts/**（版本工具副本或软链到 repo/agate/scripts——副本 vs 软链的维护语义差异在 P2-design 决策并写入 UPGRADING），消除"装完 README 入口命令不存在"死路；`install.sh` 补 `--versions` 模式（或等价文档指引）让新机器有官方路径从零进入版本布局
- **Phase 2（元仓库 gap 修复，RM-AG0058 本体）**：resolve 命中版本目录后探测 `vdir/agate/scripts` 存在则返回 `vdir/agate`（元仓库形态适配），**或** install 在 worktree 检出后把 `agate/` 内容提升为版本根——二选一在 P2-design 决策；验收锚 = agateon 元仓库钉 `.agate-version` 后 hook gate 实跑可用（2026-09-03 实测失败场景转绿）
- **Phase 3（update 统一入口）**：文档面对齐两种布局的生命周期指令（legacy = git pull、版本布局 = agate-install latest 幂等）；UPGRADING 增补"版本管理生命周期"节（安装/迁移/更新/回退一张图）；hook 重装时机写明（薄壳固定 + resolve-entry 机制下通常无需随版本重装）
- **测试**：`agate/tests/` 新增 pytest——软链状态 install 拒绝（exit 非 0 + 指引文案）；根 scripts/ 建立（装后 `~/.agate/scripts/agate-install.py` 可执行）；resolve 对 `vdir/agate` 探测（元仓库形态新用例）；**端到端**：真实 clone 形态（元仓库）装 → 钉版 → resolve → gate 路径存在（模拟根即协议 repo 保留作对照）

### out-of-scope

- agate-pack-offline / install-offline 离线链路适配（除非 Phase 1/2 改动波及其接口，波及时最小兼容）
- Windows 复制模式专项（解析链已有 .agate-root 标记兜底；本任务不改复制模式语义）
- `.state.yaml` schema 扩元数据字段 + 看板渲染/命令族（RM-AG0059 任务管理命令化，独立 epic）
- agateon 仓库形态重构（把 agate/ 提升为仓库根——影响面远超本任务，仅在 P2-design 作为备选记录不采纳理由）

## known_risks

- "resolve 返回 `vdir/agate` 是解析语义变更：hook 消费方（resolve-entry gate 路径拼接）与 agate-summary/next 等全走 agate_common 归口——须先 grep 全部消费方确认无直接拼 `vdir/scripts` 的旁路（DEBT0016 教训：dirname 推导散点）；'根即协议'部署方（版本目录直接含 scripts/）必须继续可用——探测顺序：`vdir/scripts` 先、`vdir/agate/scripts` 后，行为纯增量"
- "install 软链拒绝是行为变更：现网 legacy 软链用户（含本机 ~/.agate → 主 checkout agate/）按文档升级会撞新拒绝——拒绝信息必须给可操作迁移路径（备份软链 → 建目录根 → 装版本），否则自断升级路；本机环境是现网案例，验收时用隔离 HOME 不动真实 ~/.agate"
- "根 scripts/ 建立方式二选一有维护语义差异：副本随 install 刷新（升级需重跑 install）、软链跟随 repo 更新（repo 删则断）——P2-design 决策并写 UPGRADING，单测锁定所选语义"
- "端到端验收必须用真实 GitHub 仓库形态（元仓库），不能用根即协议模拟 repo 代替——TAG0008 教训：模拟 repo 测不出元仓库 gap；CI 无网环境则该用例标记 skip + 本地验收记录补证"

## env_constraints

- 本任务改 `agate/scripts/`（agate-install.py / agate_common.py / resolve-entry.py）+ 文档面（README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md / install.sh）→ **触发 SELF-GATE**，commit message 须含 `self-gate-review:` 或 `self-gate-skip:`
- 用系统 python（`/usr/bin/python3`）跑 pytest/pyyaml；ruff 用 `~/.venvs/agate-dev/bin/ruff`
- 基线验证用 `--strict-errors-only`（DEBT0012）；编排/派发类工具用 `~/.agate` 稳定版，不用 worktree 相对路径（TAG0016 教训）
- 本机 `~/.agate` 是 legacy 软链（指向主 checkout agate/）——**开发与验收全程不得破坏**；涉及安装路径的验证一律用隔离 HOME（mktemp -d 级别），测完清理

## executor_env

- worktree：`.worktrees/agate-TAG0032`（分支 `feat/TAG0032-version-lifecycle`），构建流程见 `docs/guides/worktree-dogfooding-guide.md`，交接单 `HANDOFF-TAG0032.md` 按模板全 9 节填写
- 任务目录：`agate-workspace/tasks/TAG0032-version-lifecycle/`
- **merge 模式**：单 task 串行，完成 PR 后 worktree 自行 git-to-main（PR 提出后主 Agent review 复核）
