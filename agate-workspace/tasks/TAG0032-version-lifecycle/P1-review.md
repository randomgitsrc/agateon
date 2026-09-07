---
phase: P1
task_id: TAG0032
type: review
parent: P1-requirements.md
trace_id: TAG0032-P1review-re1-20260907
status: approved
created: 2026-09-07
agent: requirements-review
---

# P1-review — TAG0032 版本管理生命周期可用性批（RM-AG0058 整合 epic）· 复评轮（re-review-1）

[PROD_NOT_TOUCHED]

**评审对象**：`P1-requirements.md`（14 条 BDD，risk_level: high，domains: [backend, cli]，[NO_NEED_CONFIRM]；check-frontmatter EXIT=0）
**本轮性质**：P1 复评轮（首轮 needs-revision，analyst 已回改）——只核查 3 项必修是否真正落地 + 回归确认，不重走全量评审。
**结论**：**approved** — 3 项必修全部落地且可机械判定，回归无新问题，审声明复核仍一致。

复评核对锚点（read/grep，未改任何文件）：
- `UPGRADING.md` L551 = v0.50.0 §① 布局变化表格「迁移后」列「`~/.agate/` = 版本管理根目录：… + `scripts/`（版本管理工具）」—— BDD-12 checklist 1 引用属实（在其声明的「约 L549-L553」范围内）
- `UPGRADING.md` L552 = 同表「升级 = `python3 ~/.agate/scripts/agate-install.py`（装最新版…）」—— BDD-12 checklist 2 引用的「约 L552」精确命中
- `UPGRADING.md` v0.62.0 L280 / v0.61.0 L315 / v0.60.0 L377 =「通用升级动作：`git pull` + 重跑 `install-hook.py`」；v0.66.0 L171-172 / v0.67.x L117-118,L138-139,L155-156 / v0.68.0 L95-96 =「无需重跑 `install-hook.py`（软链布局 `git pull` 即生效）」—— BDD-12 checklist 3 引用的口径分歧属实，行号对得上
- `README.md` L40-42 / `README.zh-CN.md` L40-42 = `agate-install.py` 版本管理命令块（呈现为版本布局入口）；`agate/SETUP.md` L244「## 升级 Agateon 之后」节 —— BDD-12 checklist 4 引用属实（README 行号为版本管理块，非独立「git pull 升级」段，属可接受的近似指代）
- 实跑 `check-protocol-consistency.py --strict-errors-only` → EXIT=0，329 WARNING / **0 ERROR（基线仍 0 ERROR）** —— 佐证 BDD-12 把该项降为「附加回归项（非主判据）」的措辞事实成立
- BDD 编号 `#### BDD-1` … `#### BDD-14` 连续不跳号，格式 `#### BDD-NN:` 合规（grep 实测 14 条）

---

## 三项必修逐条核对

### 必修 1 — BDD-12 机械判据在基线恒真 → **PASS（已落地）**

首轮问题：BDD-12 的 Then 子判据「`check-protocol-consistency` 0 ERROR」在修复前基线即恒真，另一半「所有表述指向统一口径」是无可枚举锚点的人工判断，两者都不验证 I-4 的「doc/reality 矛盾是否收敛」。

回改后（§3.3 BDD-12，L157-165）落地情况：
- **标题改写**：从「无互相矛盾的残留表述」改为「的具体矛盾表述逐条收敛」，指向可枚举对象。
- **(a) checklist ≥3 条具体矛盾表述、每条二选一无第三态**：**满足** — 4 条 checklist，Then 明确「每条命中『已收敛到新口径』或『已标注为版本历史叙事保留』二者之一（无第三态），任一条两者皆不满足即 FAIL」。4 条分别锚定：① v0.50.0 §① 表格「根含 `scripts/`」行（L551，doc/reality mismatch）② 同表「升级 = `agate-install.py`」行（L552）③ v0.60-0.62 vs v0.66-0.68 hook 重装口径分歧 ④ README ×2 + SETUP 升级节。
- **(b) `0 ERROR` 明确降为附加回归项**：**满足** — L165 单列「**附加回归项**（非主判据，仅防新增 ERROR）」，正文写明「基线即 0 ERROR，本项只保证本任务不引入新 ERROR，不作为『矛盾是否收敛』的判据」。复评实跑确认基线确为 0 ERROR，措辞属实。
- **(c) 每条断言可机械判定**：**满足** — checklist 1 = 「install 后隔离 HOME 装完实测 `~/.agate/scripts/` 存在」（与 BDD-4 判据 1 同源，正是 dispatch-context 给出的「可判」样例）；checklist 3 = grep 生命周期节是否含统一判定口径 + diff v0.60-0.62 历史节未被逐条改写；checklist 2/4 的 FAIL 条件是「口径冲突且无指向生命周期节的指针」——「指针存在性」可 grep，非主观。
- **单一 Given/When/Then 外壳保留**：Given（L158）/ When（L159）/ Then（L160）齐备，checklist 作为 Then 的可枚举判据项，`#### BDD-12:` 标题不变。

### 必修 2 — I-3 无 BDD 绑定 → **PASS（已落地）**

首轮问题：I-3 自述「所选（根 `scripts/` 副本 vs 软链）语义须有单测锁定 + 写入 UPGRADING」，但 BDD-4 只验入口命令可执行、BDD-11 四动作清单未含该维护语义条目，均未承接。

回改后落地情况：
- **BDD-4（L107-113）**：When 增「再在 `agate/tests/` 内检索针对根 `scripts/` 建立方式维护语义的用例」；Then 从单判据扩为三项判据「全 PASS，缺一即 FAIL」——判据 2 = 「`agate/tests/` 内存在至少一条用例，断言 P2-design 所选建立方式（副本 vs 软链）在『升级 / 重跑 install latest』后根入口仍解析到当前版本工具」（= I-3「所选维护语义有单测锁定」，两分支各自的断言内容已写明）；判据 3 = 「该用例断言的维护语义与 UPGRADING『版本管理生命周期』节所写一致」（与 BDD-11 交叉锁）。
- **BDD-11（L149-155）**：Then 判据 3 = 「该节含一条『根 `~/.agate/scripts/` 建立方式的维护语义』条目：随 P2-design 选定副本或软链后填实，明确升级期是否需重跑 `agate-install`、以及 repo 被删 / 版本目录切换对该入口的影响」（= I-3「写入 UPGRADING 生命周期节」，与 BDD-4 判据 2/3 交叉锁）。
- **§2 I-3 行（L70）**：末尾补「**对应 BDD**：BDD-4 判据 2/3（单测锁定 + 与 UPGRADING 一致）+ BDD-11 判据 3（写入生命周期节）」。
- **二值可判**：判据 2 = grep `agate/tests/` 是否存在该用例（yes/no）；判据 3 / BDD-11 判据 3 = grep 生命周期节是否含该维护语义条目、且与用例断言一致。BDD-4 判据 3 与 BDD-11 判据 3 交叉一致、方向一致（一个锁「用例↔文档一致」、一个锁「文档含条目」），不自相矛盾。
- **P1 未越界**：两处均写「P2-design 所选 / 随 P2-design 选定副本或软链后填实」，P1 只锁「所选语义须有单测 + 落文档」的验收行为，未替 P2 决策副本/软链。

### 必修 3 — BDD-2 判据宽严不一 → **PASS（已落地）**

首轮问题：「备份软链」判据具体到命令片段（`mv ~/.agate ~/.agate.bak`），「建目录根」「装版本」仅要求「可定位关键点」，把「什么算定位到」的裁量权留给检查者。

回改后（BDD-2，L94-100）落地情况：
- Then 前缀改为「以下三段**可 grep 的命令片段级**迁移指引，三者缺一即 FAIL（**每项判据同粒度，均为命令片段匹配，不留『什么算定位到』的裁量**）」。
- 判据 1 备份软链：`mv ~/.agate ~/.agate.bak`（或 `mv ~/.agate ` + `.bak`/`.old` 备份后缀）。
- 判据 2 建目录根：**已收敛到命令片段级** —`mkdir -p ~/.agate`（或 `mkdir ` + `~/.agate`）。
- 判据 3 装版本：**已收敛到命令片段级** —`agate-install.py` 且带版本标识（`latest` / `v<X.Y.Z>` / `--versions` 三者其一），形如 `python3 ~/.agate/scripts/agate-install.py latest` 或 `install.sh --versions`。
- 三项现同粒度，均可机械 grep，「三者缺一即 FAIL」真正可二值判定。

---

## 回归确认（未引入新问题）

- **BDD 编号连续性 / 格式**：grep 实测 `#### BDD-1` … `#### BDD-14` 连续不跳号，`#### BDD-NN:` 格式合规。**无回归。**
- **改动范围**：改动落在 §3（BDD-2 收敛、BDD-4 增判据 2/3、BDD-7 对称补 `AGATE_VERSION`、BDD-11 增判据 3、BDD-12 重写为 checklist、BDD-13 逐步枚举 exit）+ §2 I-3 行「对应 BDD」列 + §4 扫描 4 行号校正。frontmatter（risk_level: high / ceremony: standard / phases: [P1..P8] / domains: [backend, cli] / implicit_coupling: true / capability_requirements: []）**未动**。§1 需求复述、§5 环境能力声明、§6 裁剪说明、§7 时效性质疑、§8 待确认清单**未动**。
- **首轮已确认合规项未误伤**：同类扫描四类（§4 扫描 1/2/3/4 标题与结论结构完整）、纯增量红线 BDD-7 探测顺序（`vdir/scripts` 先、`vdir/agate/scripts` 后，L130 保留且对称补了 `AGATE_VERSION`）、时效性质疑「已核对无漂移」逐条对照严重判据 3 条、范围锁定 out-of-scope（pack-offline / Windows 复制模式 / `.state.yaml` schema / agateon 仓库形态重构均未触碰）—— **均无回归**。
- **BDD-12 外壳**：checklist 重写后仍是单一 Given/When/Then，checklist 作为 Then 的可枚举判据项，无第二组 Given/When/Then。**合规。**
- **建议项采纳**：BDD-7 Then 补「`AGATE_VERSION` 仍为 `v<X.Y.Z>`（与 BDD-6 对称）」（L130）；BDD-13 Then 逐步枚举 5 步 exit 期望 + 幂等复跑 exit 0 且不重复建目录（L172-178）；§4 扫描 4 行号校正为「约 L551 / L552，以 `### v0.50.0` §① 表格为准」（L242-246）。三项建议全采纳，均属收紧/校正，无副作用。
- **无新增断点、无悄悄扩范围**：3 项必修均在既有 BDD / 隐含需求（I-2 / I-3 / I-4）范围内微调；BDD-4 新增的「须有单测」是承接 §2 已声明的 I-3，非新范围。

---

## 审声明复核（一句话）

frontmatter 未改动，首轮已核对的 7 项声明（risk_level: high / ceremony: standard / phases: [P1..P8] / implicit_coupling: true / domains: [backend, cli] / capability_requirements: [] / `.state.yaml` judge.enabled: true）与 P0-brief `scope` + §1/§4 描述的改动性质仍一致，`ceremony: full` P7 逐信号核对不适用（本任务 standard，P7 走 `implicit_coupling: true` 保留），rejection 触发条件未命中。

---

## 结论

**status: approved**

3 项必修全部落地、可机械判定，回归确认无新问题，审声明复核仍一致：

- **必修 1（BDD-12）**：PASS — 重写为 4 条二选一无第三态 checklist（锚定 UPGRADING L551 / L552 / v0.60-0.62 vs v0.66-0.68 / README×2+SETUP），`check-protocol-consistency 0 ERROR` 明确降为附加回归项；复评实跑确认基线 0 ERROR，措辞属实。
- **必修 2（I-3）**：PASS — BDD-4 判据 2/3 + BDD-11 判据 3 交叉锁「所选建立方式的维护语义有单测锁定 + 写入 UPGRADING 生命周期节」，二值可判（grep 用例 / grep 文档条目），P1 未越界决策副本/软链。
- **必修 3（BDD-2）**：PASS — 三项判据（备份软链 / 建目录根 / 装版本）全部收敛到命令片段级、同粒度，「三者缺一即 FAIL」可机械 grep。

覆盖维度（首轮已详评，本轮无变化）：数据 ✓（I-9 + BDD-6/13）｜前端 N/A（domains=[backend, cli]，dispatch-context 明确跳过 UI/UX 与 vision）｜多端 ✓（I-10 + BDD-3/6/8/10/13，`AGATE_REPO_URL` 注入契约）｜边界 ✓（I-11 + BDD-1/7/8/13，穿透污染阻断 / 探测顺序 / fail-closed 维持 / 幂等复跑）｜兼容 ✓（I-1/I-7/I-12 + BDD-6/7/9，纯增量红线 / 版本号不回归 / 全量 pytest 底线）。首轮标记的两处遗漏（I-3 未绑定 BDD、I-4 对应 BDD-12 判据恒真）本轮均已消除。

**P1 需求基线复评通过，可进入 P2。**
