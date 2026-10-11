---
role: cso
agent: cso
task_id: TAG0051
phase: P4
c8_domain: security
retry: 2
status: approved
reviewed_at: 2026-10-11
scope: "TAG0051 P4 最终增量复审（retry 2，工作区未提交）：**只复核 wrapper 面**——docs/design-notes/r6-differential-prepare.sh 建 corpus 由 cp -a 改为 git clone --local --no-hardlinks 后的 SEC-04（--dst 删除前防护）面。其余（agate-release.py gate / release.yml / R6 allowlist / 测试）沿用 retry 1 结论。"
method: "OWASP Top 10 + STRIDE；信任边界定标；SEC-04 负例自复跑（桩化 rm 计数 + 哨兵文件）+ git clone 新边界实测"
verdict: "无 CRITICAL/HIGH/BLOCKER——approved。SEC-04 删除前校验**未因换实现放松**（10 负例全部 rc=2 且 rm 调用数=0、哨兵完好）；git clone 换实现未引入新的可删除/可写路径，且较 cp -a 收窄了面（不拷源 hooks、--no-hardlinks 无 inode 共享）。最高严重级 MEDIUM（1 项残余 SEC-03，沿用 retry 1），本轮新增 INFO 2 项，均不阻塞。"
---

# P4 安全评审（CSO）— TAG0051 release-decoupling（retry 2 增量）

> **本轮范围极窄**：只复核 `docs/design-notes/r6-differential-prepare.sh` 的 **wrapper `--dst` 防护面**（= retry 1 的 **SEC-04**）——因为 R-F 把建 corpus 的实现从 `cp -a <src> <dst>`（+ `checkout` + `clean -fdx`）换成 **`git clone --local --no-hardlinks <src> <dst>`**。
> **其余全部沿用 retry 1 结论**（SEC-01/02/04/09 已闭合；SEC-03 MEDIUM 有据接受；SEC-05/06/10/11 残余 LOW/INFO；STRIDE 非 wrapper 行、`agate-release.py gate` 与 `release.yml` 的结论**不重述、不改判**）。
> 标尺不变：改的是**不可逆对外动作（tag/Release）的授权与门禁**，问题是「**新流程的信任边界是否比旧流程更弱**」。

---

## 1. 变更隔离核验（先确认「只改了该改的」）

- `git status` 实测：`r6-differential-prepare.sh` 为**未跟踪新文件**（`??`），无 git 基线可 diff。
- **逐行读全文**：`--dst` 校验块（**空 / 绝对 / 允许前缀绝对 / `--src` 是目录 / 物理归一化 / 根 / 已存在软链 / ==src / src 内 / src 祖先 / 前缀根 / 前缀外**）**与 retry 1 复核时逐字一致**——`rm -rf` 仍在**全部校验之后**（`rm -rf -- "$DST_REAL"` 是唯一的破坏性动作，位于校验块之后）。
- 变更**仅在**建 corpus 段（原 `rm -rf + cp -a + checkout -- . + clean -fdx` → 现 `rm -rf + mkdir -p dirname + git clone --local --no-hardlinks --quiet`），外部契约（`--src/--dst/--after` 同名同义、corpus 干净、真仓只读）不变。R-F `P4-progress-implementer-R-F.md` ④ 自述与实测一致（自检仅覆盖 3 负例 = 空/相对/src 内，**未**覆盖祖先/前缀/软链 ⇒ 正是本轮要补的）。

---

## 2. SEC-04 复核：删除前防护**未放松**（自复跑，不采信自述）

**方法**：一次性副本 `/tmp/opencode/cso-r2`、`cso-r3`、`cso-r5`；将 wrapper 与其同目录 `r6-differential.sh` **桩化**（stub 只 echo 参数、exit 0，避免触发真实差分）；向 `PATH` 前置一个 **`rm` shim**（记录每次调用后透传真 `rm`）⇒「rm 调用数=0」即证明**删除前已退出**。另放**哨兵文件**（`repo/sub/SENTINEL`、根 `SENTINEL`）证人证物。

### 负例（期望 rc≠0、且**未删任何东西**）

| # | 负例 | rc | rm_calls | 结果 |
|---|------|----|----------|------|
| N1 | `--dst ""`（空） | **2** | **0** | 「--dst 不得为空串（防 rm -rf 落到 cwd/真仓）」 |
| N2 | `--dst relative/x`（相对） | **2** | **0** | 「--dst 须为绝对路径」 |
| N3 | `--dst <src>/sub`（在 src 内） | **2** | **0** | 「不得位于 --src 之内」；哨兵 `repo/sub/SENTINEL` 完好 |
| N4 | `--dst == --src` | **2** | **0** | 「不得等于 --src」 |
| N5 | `--dst <src 祖先>` | **2** | **0** | 「不得为 --src 的祖先目录」；根哨兵 `SENTINEL` 完好、src 完好 |
| N6 | `--dst /tmp/cso-outside-zzz`（前缀外绝对路径） | **2** | **0** | 「须位于允许前缀之下」 |
| N7 | `--dst /`（根） | **2** | **0** | 「不得为根目录 '/'」 |
| N8 | `--dst /tmp/opencode`（**允许前缀根**；src 置于前缀外以触发该分支） | **2** | **0** | 「不得为允许前缀根目录本身」 |
| N9 | `--dst <已存在软链>` | **2** | **0** | 「已存在且为软链，拒绝（防经软链误删）」；软链仍 `-L` 为真 |
| N10 | `--dst <link→src>/sub`（**软链绕过**） | **2** | **0** | 物理归一化落到 src 内 ⇒ 「不得位于 --src 之内」 |

**结论**：**10 负例全部在删除任何东西之前 `rc=2`、`rm` 调用数=0、哨兵/源/软链完好**。retry 1 认定的最危险三项——**src 祖先（N5）/ 前缀外任意绝对路径（N6）/ 软链绕过（N10）**——**换实现后仍被拒**。**无任何校验被放松。**

### 正例（期望 rc=0，确认**无过度拒绝**）

| 正例 | 结果 |
|------|------|
| 常规 src ⇒ `--dst` 前缀内 | **rc=0**；rm 目标 = 归一化绝对路径 `/tmp/opencode/cso-r3/corpus`（非原始 `--dst`）；stub 收到 `--corpus <dst> --after <src>/agate` |
| `--src .`（默认相对 src，cwd=仓库） | **rc=0**，corpus 生成 |
| `R6_PREPARE_ALLOW_PREFIX=relative/pfx`（前缀非绝对） | **rc=2**（正确拒绝） |

### git clone 换实现的**新边界**（本轮新增关注）

| 关注点 | 实测 | 判定 |
|--------|------|------|
| **`--src` 非 git 仓库** | `git clone` 失败 **rc=128**；注意此时 `rm -rf -- "$DST_REAL"` **已发生**（rm_calls=1），但目标 `--dst` 已过全量校验（前缀内、非 src、非祖先）⇒ **仅删可弃置的 corpus**；**src 完好**、corpus 未建 | 非安全回归（见 SEC-12，robustness INFO） |
| **`--src` 是另一个 worktree** | `git clone --local` **rc=0**，corpus 生成；`--after` 正确指向 `<worktree>/agate` | 通过 |
| **`--src` 含未提交改动** | clone 检出 = **HEAD 干净树**；未跟踪文件 / 修改均**不进 corpus**；`git -C corpus status --porcelain` 空、HEAD == src HEAD；after 侧仍由 `--after <src>/agate` 承担工作树口径 | 通过（口径与 retry 1 一致） |
| **`--local` 的硬链/权限** | `--no-hardlinks` 生效：src 与 corpus 的对象文件 **inode 不同**（无硬链共享）⇒ corpus 内写操作**不会**经 inode 反向污染 src `.git/objects` | 通过（**安全正收益**） |
| **源仓库自定义 hooks 是否被复制** | clone 后 `corpus/.git/hooks` **仅 `*.sample`**，源的自定义 `post-checkout` **未复制**（`cp -a` 会整拷 `.git/hooks`）⇒ 较旧实现**收窄**了「corpus 内 git 操作触发源 hook」的面 | 通过（**较 cp -a 更窄**） |
| **`uploadpack.packObjectsHook`（源 `.git/config` 命令执行向量）** | 在 git 2.43.0 上：`--local`（含 `--no-hardlinks`）/ 默认硬链 / `--no-local` **三种 clone 均未触发**该 hook | 通过（本环境无此向量；`--src` 由操作者选定，默认 `.`） |
| **clone 是否写 `--src`** | clone 前后 `src/.git` 全文件签名（`find -printf '%p %s %T@'` 哈希）**完全一致**；`src` 工作树 `status --porcelain` 空 | 通过（**src 只读**） |
| **空仓库 src（无 commit）** | clone **rc=0** 但 corpus 无 HEAD ⇒ 下游 `r6-differential.sh` 会失败 | robustness INFO（见 SEC-12） |

**总判**：`git clone --local --no-hardlinks` **未引入任何新的可删除 / 可写路径**；`rm` 面、路径校验面与 retry 1 完全相同，且实现较 `cp -a` **收窄**（不拷源 hooks、无 inode 共享）。**SEC-04 维持 closed。**

---

## 3. 只读纪律核验（RM-AG0081）

- 全部实验在 `/tmp/opencode/cso-r2|r3|r4|r5` 内、`trap cleanup EXIT` **同一 bash 调用**内创建→操作→清理；破坏性动作经 `rm` shim 登记**未**落真仓。
- 真实仓库 `git status --porcelain` 跑前/跑后 **逐行一致**（sha256 `1366a50b5d86…`，79 行；HEAD `d4e32f4f`）——**零写入**。
- **未**执行任何真实外部动作（无 `workflow_dispatch` / tag / Release / 写类 `gh`）。

---

## 4. 本轮发现（增量）

### 沿用 retry 1（不重述，仅列 ID 与状态）

- **SEC-03（T，required 集合漂移）— MEDIUM，有据接受残余**（注释级缓解，未引入需 admin 的 API）。
- **SEC-05**（门步令牌最小权限，部分收敛）、**SEC-06**（`workflow_dispatch` 授权语义 = 与旧 tag-push 同级，非回归）、**SEC-10**（安全控制缺自动回归锁）、**SEC-11**（`R6_PREPARE_ALLOW_PREFIX` 可放宽为 `/`）——均 **LOW/INFO，不阻塞**。

> SEC-10 再确认：`test_tag0051_r6_harness.py` 仍**只覆盖 3 负例**（空 / 相对 / src 内）+ 「非法参数不触碰真仓」，**未覆盖** 祖先 / 前缀外 / 前缀根 / 已存在软链 / 软链绕过 五类 ⇒ 回归锁缺口**仍在**（建议按本文件 §2 负例补 5 条单测）。

### 新增（本轮）

**SEC-12（R，`--src` 无效时 corpus 先生后败；INFO/robustness，非安全缺陷）**：`--src` 非 git 仓库（或空仓库无 HEAD）时，`git clone` 失败于 `rm -rf -- "$DST_REAL"` **之后** ⇒ `--dst` 已被删、命令非 0 退出。因 `--dst` 已过全量校验（前缀内、非 src、非祖先），**只会删可弃置的 corpus，不触及 src 或前缀外**，故无安全影响；与旧 `cp -a`（非 git 源会先成功拷贝、更晚才在差分侧失败）相比仅**提前失败**。可选硬化（不阻塞）：`rm` 前先 `git -C "$SRC_REAL" rev-parse --git-dir` 探活，fail-fast 且不销毁 dst。

**SEC-13（信息/一致性，INFO）**：wrapper 头部 §「R6 证据成立前提」仍写「本 wrapper 的 **⑤ 会 `clean -fdx`** 掉副本里未跟踪的新文件」——该步**已被移除**（改为 clone）。结论（after 侧须显式指向真实工作树）**仍成立**（clone 亦为 HEAD 干净树），仅该句所指**机制已不存在**，建议同步措辞。非安全项，不阻塞。

---

## 5. STRIDE 矩阵（**仅 wrapper 资产进行增量更新**；其余行沿用 retry 1）

| STRIDE | 资产/交互 | 本轮观察 | 级别 | 编号 | 状态 |
|--------|-----------|----------|------|------|------|
| **T**ampering | `r6-differential-prepare.sh --dst`（`rm -rf` 面） | 换 `git clone` 后校验块逐字不变；10 负例 rc=2、rm_calls=0、哨兵完好 | — | SEC-04 | **closed（维持）** |
| **T**ampering | corpus ↔ src 写隔离 | `--no-hardlinks` 无 inode 共享 ⇒ corpus 写不回灌 src | — | — | 通过（正收益） |
| **T**ampering | corpus 内 git 操作触发源 hook | clone 只留 `*.sample`，源自定义 hooks 未复制（较 cp -a **收窄**） | — | — | 通过（正收益） |
| **E**levation（`--src` 可信性） | `uploadpack.packObjectsHook` 等源端 config | git 2.43.0 三种 clone 均未触发；`--src` 由操作者选定（默认 `.`） | INFO | — | 通过 |
| **R**epudiation | `--src` 无效 → dst 先生后败 | 只删已校验的可弃置 corpus，src/前缀外无触 | INFO | SEC-12 | 非阻塞 |
| **I**nformation | wrapper 头部注释 ⑤ `clean -fdx` 已不存在 | 措辞与实现不一致（结论仍成立） | INFO | SEC-13 | 非阻塞 |

（`workflow_dispatch` / gate 判据 / token 面 / DoS 等非 wrapper 行**沿用 retry 1 矩阵**，本轮不改判。）

---

## 6. 结论与门槛判定

- **CRITICAL / HIGH / BLOCKER：0** ⇒ **不阻塞发布**。
- **SEC-04（wrapper `--dst` 删除前防护）：closed 维持**——换实现**未放松任何一项校验**；最危险的 src 祖先 / 前缀外 / 软链绕过三类自复跑仍 `rc=2` 且**零删除**。
- `git clone --local --no-hardlinks` **未引入新的可删除/可写路径**，并较 `cp -a` **收窄**了信任面（不拷源 hooks、无 inode 共享、src 经实测只读）。
- 残余：**MEDIUM×1（SEC-03，沿用）**；**LOW/INFO**：SEC-05/06/10/11（沿用）+ SEC-12/13（新增，均 INFO、不阻塞）。
- 分级映射（无 BLOCKER → approved）。**状态：`approved`**。建议（不阻塞）：按 §2 补 5 条 wrapper 负例单测（并入 SEC-10）；§SEC-12/13 属可选硬化与措辞同步。
