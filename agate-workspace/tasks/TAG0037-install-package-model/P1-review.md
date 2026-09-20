---
agent: requirements-review
phase: P1
task_id: TAG0037
type: review
parent: P1-requirements.md
trace_id: TAG0037-P1-review-20260920-r1
created: '2026-09-20'
status: approved
---

# P1-review — TAG0037 需求基线评审（requirements-review，复审 #1）

> 结论：**approved**。首轮 4 项 MAJOR（M-1…M-4）与 11 条 MINOR 均已真实修复（逐条对照 P1-requirements.md 正文与实测，而非仅看 §10 处置表）；新增 BDD-51/52 可二值判定、未越出 P0-brief 范围、与既有 BDD 无新矛盾。无 BLOCKER、无 MAJOR。仅余 4 条 MINOR（非阻塞，建议 P2 前顺手订正，见末节）。
> 说明：`agent` 字段在创建文件时按派发指令预置为 `requirements-review`（`agate-md-field-set` 永久拒绝写 `agent`），其余字段与 `status` 均经 set 写入。本次未修改 P1-requirements.md，未 git commit。`[PROD_NOT_TOUCHED]`（仅只读 grep / git / `git archive` 到 scratchpad / 本地 CLI 探测，未触碰真实 `~/.agate`）。

## 首轮发现复核（逐条）

| 发现 | 复核方法 | 结论 |
|------|---------|------|
| M-1 多场景未拆 | 读 §4 头部"全或无规则"（`:126`）；`grep '\[参数化\]'` 标题 | 已解决。规则明确（任一子场景失败整体 FAIL、逐子场景留证、P6 仍以编号条数计）；标注覆盖 BDD-3/5/7/14/18/24/25/28/29/31/32/51（首轮列的 9 条全在，另多标 3 条）。残余见 m-A |
| M-2 BDD-14 ↔ BDD-20 矛盾 / 资产名 / S-9 | 读 BDD-13 ⑤、BDD-14 ④、BDD-20 Given/Then、§7 S-9 | 已解决。BDD-14 ④ 用夹具 B（仅 `[Unreleased]` + `[0.72.0]`，恰为 BDD-20 执行时状态）定义预发布 tag 回落规则且"只对预发布 tag 生效，正式 tag 仍 fail-closed"；资产名定为"tag 名原样"，offline `manifest.version` 恒为严格 `vX.Y.Z`（与 `install-offline.py:47` `_VERSION_RE` 一致）；S-9 已更正（CHECK 7 用 `git describe`，核实 `check-protocol-consistency.py:462`），BDD-20 写入"④ 清理后才可跑 CHECK 7 / BDD-49"的强制先后顺序与 tag push 连带触发 workflow 的副作用声明 |
| M-3 BDD-37 白名单 | **自行实扫**：`git ls-files` 剔除任意层级 `archived/`、`agate-workspace/tasks/`、`docs/reviews/`、`docs/design-notes/`、`node_modules`、`package-lock.json`，四模式 `re.I` | 已解决且**落地即绿**。实扫命中 **23** 个文件，与 BDD-37 ③ 所称"现状命中 23"一致；W(12)∪R(12) 覆盖全部命中（不在 W∪R 的命中 = 0；R 12 项均现有命中；W 中仅预登记的 `install-offline.py` 现状无命中）。`use_legacy` 命中仅 `agate_common.py`（4 行，属 BDD-28 删除对象）与 `tech-debt.md`（唯一例外）。`platform-notes.md:250` 已移入 R 清零并与 §5 扫描 C 对齐 |
| M-4 BDD-42/43/45 | 读 BDD-42/43/45 与 §6 H-1；本机实测命令输出 | 已解决。BDD-42 不再调用 `claude`（真实模型调用降为 P6 人工项 H-1，不计入 BDD 总数，§6 写明用真实 HOME 凭据、仅 `AGATE_HOME` / `$AGATE_DIR` 指隔离布局）；判据改为链接可读 + frontmatter 可 `yaml.safe_load` 且含 `name: orchestrator`（实测 `orchestrator-template.md` 满足）；BDD-43/45 "不在 PATH → FAIL"，第三态消除；`HOME` 保持真实仅供 CLI 读自身配置且断言真实 `~/.agate` 哈希不变，与文首隔离口径的例外已在 `:124` 声明。实测：`opencode debug agent orchestrator` 输出含 `"mode": "primary"`、`"task": true` ✓；`codex features list` 含 `multi_agent  stable  true` ✓ |
| m-1 SUGGEST 悬挂 | 检索 BDD 区（`:121-400`）"推荐值 / P2 定案" | 已解决。T-1 与 BDD-2/12/13/18/23/27/30 已转为基线值；BDD 区仅余 BDD-6 / 39 / 47 中三处 `[SUGGEST: S-16/S-18/S-17]` 引注，其判定值本身已确定（见 m-D） |
| m-2 §8 矛盾 | 读 §8 | 已解决（改为"主 Agent 授权手写"）；frontmatter 完好（`ceremony: full`、`phases` 含 P7，`check-frontmatter.py` rc=0） |
| m-3 体积 | 复算 `git ls-tree -r -l v0.72.0`（agate 3,309,321 / tests 1,608,842 / B 1,864,871） | 已解决，数字与首轮实测逐字节一致，上限 2,331,089 B 算式正确 |
| m-4 基线 | BDD-46 | 已解决（`git diff 75a8102..HEAD`） |
| m-5 BDD-27 ↔ 28 | BDD-28 末句 | 已解决（改为"不存在把软链目标当 `AGATE_ROOT` 返回的分支"，检测 + 迁移提示分支明确允许） |
| m-6 软链基址 + 有效 current | 新增 BDD-51 | 已解决（见下） |
| m-7 blob 字节口径 | BDD-15 ③ | 已解决 |
| m-8 P1 纯净性 | BDD-14 / 15 | 已解决（改写为"逻辑可在无 CI 下被测试调用""CI 与本地逐成员字节一致"，承载形态留 P2） |
| m-9 BDD-7 ③ 重叠 | BDD-7 | 已解决（卸载统一归 BDD-25） |
| m-10 历史 tag | BDD-24 ② | 已解决（畸形 tag `v0.1.0` → exit 1、无半装、指针不变） |
| m-11 缺 tests 冒烟 | 新增 BDD-52；实测见下 | 已解决（一处措辞需订正，见 m-B） |

## 新增 BDD-51 / BDD-52 评审

- BDD-51（软链基址但目标是完整版本根）：可判定（① exit 0 + `AGATE_REASON=全局 current` + `AGATE_ROOT` 为目标内 `vX.Y.Z/agate`；② `agate-install.py latest` exit 1 并按 BDD-32 拒绝）；[参数化] 标注 ✓。与 BDD-27（目标为协议本体目录、无 `current` → 失败）以"有无可用 `current` 链"互斥，与 BDD-28(e)（env 覆盖）、BDD-31/32/33（安装侧一律拒绝软链）不矛盾；规则落在子批 E（删 legacy 的边界定义）内，无越界。数据✗ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-52（缺 `agate/tests/` 的包内脚本冒烟）：实质成立——我在 `git archive` 出的无 `agate/tests/` 目录树上实测：`check-platform-assumptions.py` 输出 `FATAL: 目标不存在`、rc=2、无 Traceback ✓；`agate-summary.py` / `agate-resolve.py`（设 `AGATE_ROOT`）rc=0、无 Traceback ✓；`agate-risk-score.py` 带 TASK_DIR 时无 Traceback ✓。范围属子批 A/D（S-1 的直接后果），未越界。仅一处措辞问题见 m-B。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓

## BDD 评审（52 条，覆盖维度）

编号核对：`grep '^#### BDD-'` 得 1–52 连续、无跳号，格式 `#### BDD-NN:` ✓。`domains: [backend, security]`，无 frontend，前端维度对全部 BDD 记 N/A；无需 UX 类别 BDD / `ui_render_shape` / vision 声明（`capability_requirements: []` 相符）。

- BDD-1（契约成文）：可判定。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-2（边界落到包内文件集合）：可判定，③ 已改基线值。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-3（来源单一 + 默认拒绝）：可判定，[参数化]。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-4（三路径同构）：可判定。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-5（旧形态可解析）：可判定，[参数化]，旧安装器同款 fixture ✓。数据✓ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-6（`_protocol_root` 探测序不变）：可判定（既有用例 diff 空 + 函数体无删改）。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-7（新旧共存）：可判定，[参数化]。数据✗ 前端N/A 多端✗ 边界✗ 兼容✓
- BDD-8（双实现一致）：可判定。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-9（真实 pack 产物离线安装后解析）：可判定。数据✓ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-10（基址同源 + 补齐结构）：可判定。数据✓ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-11（假 bundle 助手修正 + 红灯回放）：可判定。数据✓ 前端N/A 多端✗ 边界✗ 兼容✗
- BDD-12（旧格式 bundle 拒绝）：可判定。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-13（workflow 静态契约）：可判定，⑤ 资产名 / manifest 版本口径已补。数据✗ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-14（notes 取段）：可判定，[参数化]，与 BDD-20 已自洽。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-15（本体 tarball 一致 + 成员安全）：可判定，blob 字节口径已定。数据✓ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-16（offline tarball 可消费）：可判定。数据✓ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-17（portable 无 git）：可判定，"文档即验收脚本"。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-18（`--check` portable 口径）：可判定，[参数化]。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-19（不宣称零依赖）：可判定。数据✗ 前端N/A 多端✗ 边界✗ 兼容✗
- BDD-20（测试 tag CI 实跑）：可判定，预发布回落 / 命名 / 清理顺序 / 连带触发均已自洽；许可与降级口径完整。数据✓ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-21（tag 与 Release 双轨）：可判定。数据✗ 前端N/A 多端✓ 边界✓ 兼容✗
- BDD-22（在线只装本体）：可判定。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-23（冗余量化）：可判定，数值已校正。数据✓ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-24（历史 tag + 畸形 tag）：可判定，[参数化]。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-25（卸载新旧形态）：可判定，[参数化]。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-26（幂等 + 不污染源仓库）：可判定。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-27（resolve 软链 fail-closed）：可判定。数据✗ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-28（解析链仅三层）：可判定，[参数化]，措辞已澄清。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-29（install.sh 无参进版本布局）：可判定，[参数化]。数据✓ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-30（废弃 env 处置）：可判定。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-31（install.sh 软链 fail-closed）：可判定，[参数化]。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-32（agate-install 软链 fail-closed）：可判定，[参数化]。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-33（install-offline 软链守卫）：可判定。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-34（summary 软链提示）：可判定。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-35（迁移文案跨入口一致）：可判定。数据✓ 前端N/A 多端✓ 边界✗ 兼容✗
- BDD-36（迁移三步可走通）：可判定。数据✓ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-37（全仓 grep 回归）：可判定，白名单经实扫验证（见 M-3）。数据✗ 前端N/A 多端✗ 边界✓ 兼容✗
- BDD-38（4 个真 legacy 测试处置）：可判定。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-39（文档面改写）：可判定，⑧⑨ 已补。数据✗ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-40（协议根遗留路径）：可判定。数据✗ 前端N/A 多端✗ 边界✗ 兼容✓
- BDD-41（SETUP `$AGATE_DIR` 去 fallback）：可判定。数据✗ 前端N/A 多端✓ 边界✓ 兼容✓
- BDD-42（Claude Code 接入，agate 侧）：可判定（去除模型调用）。数据✗ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-43（OpenCode 接入）：可判定，二值。数据✗ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-44（DSH 接入）：可判定。数据✗ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-45（Codex 接入）：可判定，二值（措辞见 m-C）。数据✗ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-46（out-of-scope 零 diff）：可判定，基线已写死。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-47（hook 解析不受影响）：可判定。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-48（pytest 不减反增）：可判定；基线 1842 + 2 skipped（首轮已用 `pytest --collect-only` 复核 1844 collected）。数据✗ 前端N/A 多端✗ 边界✓ 兼容✓
- BDD-49（consistency / ruff / shellcheck）：可判定。数据✗ 前端N/A 多端✗ 边界✗ 兼容✗
- BDD-50（发布物 / v0.73.0 / BREAKING）：可判定，③ 已补连带 workflow。数据✗ 前端N/A 多端✓ 边界✗ 兼容✓
- BDD-51：见上。
- BDD-52：见上。

**跨条一致性**：exit 码 BDD-12/27/28(d)/31/32/33/51② 均为 1；BDD-27（无 `current` 的软链 → 失败）与 BDD-51①（有 `current` 的软链 → 放行）以"有无可用 `current` 链"划界，无冲突；BDD-14 ④ ↔ BDD-20 已自洽；BDD-28 ↔ BDD-27 措辞已协调。保护优先级：env 覆盖优先于软链检测（BDD-28(e)）已显式。

## 判据 1–11 ↔ BDD 覆盖（复核）

| 判据 | BDD | 结论 |
|------|-----|------|
| 1 结构契约 + 精确边界 | 1、2、3 | 覆盖 |
| 2 三路径同构 | 4（+10、16、17） | 覆盖 |
| 3 离线安装解析成功 | 9（+12） | 覆盖 |
| 4 `_make_bundle` 反映真实布局 | 11 | 覆盖，含红灯回放 |
| 5 Release 自动创建 + assets | 13、14、15、16、20、21 | 覆盖，矛盾已消除 |
| 6 portable 不依赖 git | 17、18、19 | 覆盖 |
| 7 只装本体，冗余量化 | 22、23（+24、52） | 覆盖 |
| 8 已装旧形态仍可解析 | 5、6、7 | 覆盖，独立 BDD |
| 9 pytest + consistency | 48、49 | 覆盖 |
| 10 legacy 彻底删除 | 27、28、36、37、38、39（+51、29~35、40） | 覆盖，白名单已实扫验证 |
| 11 4 平台接入 | 41、42、43、44、45（+ 人工项 H-1） | 覆盖；Claude 侧真实 `-p` 调用作为 P6 人工项而非 BDD，属合理降级，已写明凭据与隔离口径 |

兼容红线：`_protocol_root` 探测序不改（BDD-6）、已装旧形态可解析（BDD-5）、共存（BDD-7）、双实现一致（BDD-8）——四条独立可判定 ✓。

## 隐含需求覆盖

- 数据维度：覆盖（隐藏元数据登记 BDD-1/3/4、tarball 成员安全 BDD-15、notes 抽取 BDD-14、体积量化 BDD-23）；遗漏：无。
- 前端维度：N/A（无 frontend domain）。
- 多端维度：覆盖（在线 / 离线 / portable / Release 四路径 BDD-4/16/17；4 平台 41–45；软链基址 + 有效 `current` BDD-51）；遗漏：无。
- 边界维度：覆盖（缺段 BDD-14 ②、畸形 tag BDD-24 ②、旧格式 bundle BDD-12、无 git 17/18、无 `repo/` 25、幂等 26、软链穿透 31–33、缺 tests 目录 52）；遗漏：无。
- 兼容维度：覆盖（5/7/25/24/18/30/12/51）；遗漏：无。
- §3 隐含需求 1–12 全部落到 BDD；范围纪律：用户三项裁决按裁决写入；分析师衍生项（BDD-8/10/18/21/33/34/40/51/52）已在 §3 末段声明子批归属，均在子批 A–E 边界内，无需 `[SCOPE+]`，未发现越界项。

## 同类扫描 / P0_STALE / SUGGEST

- 同类扫描：本轮未变更命中清单；BDD-37 的实扫数据（23 = W∪R）已与 §5 扫描 C、`platform-notes.md` 的处置对齐。
- P0_STALE 三条（v0.72.0 已发布 / `agate/CLAUDE.md` 不存在 / 测试路径 `regression/`）首轮已核实，未变。
- SUGGEST：S-1…S-6、S-8…S-19 已转基线值；无 SUGGEST 实为需人定夺的业务方向 / 破坏性变更（破坏性变更本身由用户裁决）。`suggest_resolved` 需主 Agent 补写（`agate-md-field-set` 不接受该键，analyst 已声明）。

## 审声明（风险分级 / 裁剪声明 vs diff 证据）

- 暂存区仍无代码 / 文档 diff（P1 阶段仅未跟踪任务文件；`git diff --cached --stat` 为空）；以需求所定改动面对照：`agate/scripts/*.py`、`install.sh`、新增 `.github/workflows/*.yml`、`agate/**/*.md`、`README*`、`CHANGELOG.md`、`docs/guides/*`、大量 `agate/tests/`；文件类型跨脚本 / 文档 / CI / 测试，规模大，域 backend + security。
- `risk_level: high`、`domains: [backend, security]`、`packages` 五项：与改动面匹配 ✓。`ceremony: full` 且 `phases` 含 P1–P8（含 P7，逐信号核对：协议文档多文件交叉 + 发布物三处一致，P7 不可裁）✓；无阶段裁剪，无需裁剪理由评审。声明与改动面**匹配**。

## 遗留 MINOR（非阻塞，建议主 Agent 转告 analyst 在 P2 前顺手订正，不影响 approved）

- **m-A 标注一致性**：BDD-52（四个脚本、各有独立退出码契约）与 BDD-33（含"`--dest-root` 指向普通目录不误伤"第二场景）含多子场景却未带 `[参数化]`，与 §4 自订"未带该标签的均为单一 Given-When-Then"不一致。建议补标签。
- **m-B BDD-52 对 `agate-risk-score.py` 的调用描述不准确**：该脚本无参数时是**用法错误（打印用法、rc=1）**，不会走 `git_ok: false` 降级路径（我实测：无参 → `用法: agate-risk-score.py TASK_DIR`，rc=1；给 TASK_DIR 时无 Traceback）。建议把 When 改为"传入一个 TASK_DIR 运行"，Then 相应改为"无 Traceback，输出按既有降级契约"。"退出码落在各自既有契约内"也宜给出可判定的期望值，避免 P3 写测试时自行解释。
- **m-C BDD-45 匹配歧义**：`codex features list` 输出含 `multi_agent`、`multi_agent_mode`（removed）、`multi_agent_v2`（stable / false）三行前缀相同的条目（实测），"含 `multi_agent` 行"应写为"第一列恰为 `multi_agent` 的行"，避免误命中 `multi_agent_mode`。
- **m-D 残留引注**：BDD-6 尾部"若 P2 论证需增量探测序 3…"、BDD-39 ⑤ / BDD-47 的 `[SUGGEST: S-16/S-18/S-17]` 引注仍留在 BDD 正文。判定值本身已确定（函数体无删改 / 历史节原文保留 / 保留兜底），不构成浮动；建议改为"基线 S-16"式引注，与其它 BDD 一致，并让 BDD-6 明确"增加探测序 3 不在本任务范围"。
