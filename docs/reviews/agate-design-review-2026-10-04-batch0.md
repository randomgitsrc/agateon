---
review_date: 2026-10-04
reviewer: independent-adversarial (design review)
change_summary: TAG0042 第 0 批 9 项缺陷修复设计的实现前对抗式评审
files_changed: [docs/design-notes/design-tag0042-batch0-defects.md]
reviewed_object_sha256: aa60dc29e8dcd0cd1f7bf648b186c535979828fbb8d85ad3366e784e363d8b35
reviewed_object_commit: f5e4c31
branch: design/tag0042-batch0
status: needs-revision
---

# 独立对抗式设计评审：TAG0042 第 0 批（9 项缺陷修复）

## 0. 锚定与「对象漂移」声明（**必读**）

### 0.1 锚定核验

| 项 | 值 |
|---|---|
| 被评审 commit（任务指定） | `f5e4c31` |
| 该 commit 中文件 sha256 | `aa60dc29e8dcd0cd1f7bf648b186c535979828fbb8d85ad3366e784e363d8b35` |
| 工作区文件 sha256（实测） | `aa60dc29e8dcd0cd1f7bf648b186c535979828fbb8d85ad3366e784e363d8b35` |

命令与输出（实测）：

```
$ git show f5e4c31:docs/design-notes/design-tag0042-batch0-defects.md | sha256sum
aa60dc29e8dcd0cd1f7bf648b186c535979828fbb8d85ad3366e784e363d8b35  -
$ sha256sum docs/design-notes/design-tag0042-batch0-defects.md
aa60dc29e8dcd0cd1f7bf648b186c535979828fbb8d85ad3366e784e363d8b35  docs/design-notes/design-tag0042-batch0-defects.md
```

**⇒ 指定对象内部一致，无漂移。** 但见 0.2。

### 0.2 ⚠️ 分支内漂移：存在比被评审对象更新的版本（**不停止评审，但必须记录**）

任务只要求「工作区 vs `f5e4c31`」比对，两者一致。但**同一分支上 HEAD 已前进一个 commit**：

```
$ git log --oneline -3
fa2fc3d design(TAG0042-批0): 更正 X7——问题不是「与 P1 不一致」而是「返回了通过码」
f5e4c31 design(TAG0042-批0): 9 个「现在就是错的」缺陷修复设计（待独立评审）
bdfe8b6 Merge pull request #398 from randomgitsrc/task/TAG0042-config-and-enforcement
```

但工作区文件哈希 = `f5e4c31` 版本，**不等于** `fa2fc3d` 版本：

```
$ git show fa2fc3d:docs/design-notes/design-tag0042-batch0-defects.md | sha256sum
9160b219e2844babf47b8a1d391f923b717e093624767d22718bc43ea3b2424b  -
```

**⇒ 工作区/被评审对象落后于分支 HEAD。** 这不是任务定义的「对象漂移」（那指工作区 ≠ 指定 commit），
但它是**更严重的评审隐患**：`fa2fc3d` 把 **X7 整节改写**了，改写的正是本任务点名要求裁定的一节。

| | `f5e4c31`（被评审对象） | `fa2fc3d`（分支 HEAD） |
|---|---|---|
| X7 标题 | 「P2-review 缺 `agent` 放行（exit 2），P1 同类却 exit 1（**不一致**）」 | 「P2-review 缺 `agent` 返回**通过码**（**真 fail-open**）」 |
| X7 理由 | 「同一概念两种判定」 | 「`return 2` **不是 WARNING，是通过**」（引用 `phases.yaml` `gate_pass_exit`） |
| V7 锚 | 「统一 exit 1（与 P1 一致）」 | 「**不得等于 `gate_pass_exit`**」 |

**裁定**：本报告**以 `f5e4c31` 为正式评审对象**（按任务锚定），但**同时核验 `fa2fc3d` 的 X7 改写**——
因为若不核验，评审结论会在 HEAD 上失效。**两者都见 §1.X7 与 §2.X7。**

> **给主 Agent 的行动项**：实现前必须**先明确以哪一版为准**。若按 HEAD 实现，`f5e4c31` 的 X7/V7
> 措辞已作废；本报告对 X7 的裁定对**两版均适用**（见 §2.X7，结论相同）。

---

## 1. 逐项事实核验（X1–X9）

> 方法：逐条直接读源码；凡「设计贴的片段」都回原文比对；凡设计未贴的实现细节都补读。
> 所有 `python3`/`git` 探针均在 `mktemp -d` 一次性副本内「建→用→清」同一调用完成。

### 汇总表

| 项 | 设计声称 | 核验结论 |
|---|---|---|
| X1 | `continue` 在 PROD_TOUCHED 扫描之前 | **属实**（但「改法能达到目标」**不成立**，见 §2.X1） |
| X2 | `read_state_phase` 读工作区；4 个调用方 | **半属实**——读工作区属实；**「4 个调用方」不实**（实测 2 个生产调用点） |
| X3 | 只读仓库根 ⇒ 永远 SKIP；exit 0 是有意设计 | **属实**，且设计对 CI 注释 ①–③ 的引用**逐字准确** |
| X4 | 只认中文 `引用\s*P5\s*证据` | **属实**（无其他分支） |
| X5 | `bash` 无 `-o pipefail` | **属实**（但**设计给的改法字面不可实现**，见 §2.X5） |
| X6 | `design_trivial` 按存在判 | **属实**，且**设计漏掉了该 fix 的反向破坏**（见 §2.X6，**本报告最重要的新发现**） |
| X7 | P2-review 缺 `agent` 返回 2（放行），P1 返回 1 | **属实**，且 `fa2fc3d` 的「2 = 通过码」改写**也属实**；但设计对 exit 2 语义的**结论方向错了**（见 §2.X7） |
| X8 | `not os.path.islink(hook_file)` 排除软链 | **属实** |
| X9 | P8 卡要求「以 READY 提交」⇒ gate_p8 跑不到 | **属实**（卡片原文 + `--follow` 统计 38/16 逐字复现） |

---

### X1 — `continue` 在 PROD_TOUCHED 扫描之前：**属实**

`agate/scripts/pre-commit-gate.py`（实测行号）：

```
319:         # 2g. 跳过非 gate 阶段
320:         if phase in ("PAUSED", "READY", "DONE"):
321:             continue
322:         if not os.path.isdir(task_dir):
323:             continue
324:
325:         # 2g.1 PROD_TOUCHED 检测（P1.2）——仅扫任务目录下的暂存 diff
```

**⇒ 设计的引用逐字属实**：`continue`（L320-321）确实在扫描（L325+）之前。

**扫描是否在别处也做了？——做了，但只覆盖另一个面且只发 WARNING。**
`pre-commit-gate.py` 全文只有一处 `PROD_TOUCHED` 判定逻辑（L343/L347）。其他命中在别处：

```
$ grep -n "PROD_TOUCHED" agate/scripts/pre-commit-gate.py
343, 347   （即 2g.1 扫描本体）
```

**⇒ 无第二处阻断扫描。** 但注意一个设计**完全没提**的结构事实（见 §2.X1）：

```
327:         if any(f.startswith(prefix) for f in _staged_name_only()):
```

扫描**只在「有任务目录下的文件被暂存」时才运行**。这使「所有阶段都扫描」这个目标**即使解耦
`continue` 也达不到**——见 §2.X1 的反例。

---

### X2 — `read_state_phase` 读工作区：**读工作区属实，「4 个调用方」不实**

`agate/scripts/agate_common.py`：

```
469: def read_state_phase(state_file):
470:     """读 .state.yaml 的 phase；文件不存在/解析失败返回 ""。"""
471:     data = _read_state(state_file)
472:     return data.get("phase", "") if data else ""
```

`_read_state` 走 `open(state_file)`（工作区路径）——**读工作区属实**。

**但设计的「4 个调用方」与实测不符**（实测生产调用点）：

```
$ grep -rn "read_state_phase" agate/ --include=*.py --include=*.sh | grep -v tests/
agate/scripts/agate-advance.py:76:def _read_state_phase(task_dir):      ← 本地重实现，不 import 公共库
agate/scripts/agate-next.py:52:        read_state_phase,                ← 仅 import，实测未调用
agate/scripts/pre-commit-gate.py:50:        read_state_phase,               ← import
agate/scripts/pre-commit-gate.py:257:        phase = read_state_phase(state_file)   ← 调用点 ①
agate/scripts/pre-commit-gate.py:590:        task_phase = read_state_phase(task_state) ← 调用点 ②
```

**⇒ 结论**：
- 真实调用点 **2 个**，都在 `pre-commit-gate.py`（L257 主判定、L590 一致性 WARNING 扫描）。
- `agate-advance.py:76` 是**同名本地函数**（`_read_state_phase`），与公共库**无关**，设计把它算进「调用方」是**错误归并**。
- `agate-next.py:52` 只 import、未调用（`grep -n` 全文件无调用点）。

**对设计的影响**：设计说「新增 `read_staged_state_phase`，避免改动 4 个调用方的语义」——
**「4 个」这个数字不实**，但不影响其**策略正确性**（2 个调用点里也确实不应全改）。
**风险在于**：设计若照「4 个」去核对消费方，会**漏检 `agate-advance.py` 的同名函数**，
以及**漏掉 L590 这个真正的第二调用点**（设计只提「hook 的调用点」，未区分 L257 与 L590）。

> **补记（设计未提，实测发现）**：`pre-commit-gate.py` 的 L590 是 **phase-产出一致性 WARNING 扫描**
> 的输入。若只把 L257 改成暂存区读取、L590 仍读工作区，则同一次 commit 内**两个 phase 可能来自
> 不同来源** ⇒ 出现「主判定用暂存 phase、一致性 WARNING 用工作区 phase」的**新不一致**。
> 设计**未识别这个耦合**。

---

### X3 — `ci-gate-backstop` 只读仓库根 `.state.yaml`：**属实；设计的修订核实为准确**

`agate/scripts/ci-gate-backstop.py`：

```python
repo_root = Path.cwd()
state_file = repo_root / ".state.yaml"
...
if not state_file.exists():
    print("SKIP: 无 .state.yaml，非 agate 项目")
    return 0
```

仓库根无 `.state.yaml`（实测）：

```
$ ls -la .state.yaml
ls: 无法访问 '.state.yaml': 没有那个文件或目录
$ python3 -c "...resolve_workspace(...)"
('/home/kity/oclab/agateon/agate-workspace', '/home/kity/oclab/agateon/agate-workspace/tasks')
```

**⇒「永远 SKIP」属实**：任务状态在 `agate-workspace/tasks/`，仓库根没有 ⇒ 恒走 SKIP + `return 0`。

**核验设计的修订（关键）**：设计称「`gate-backstop` 是 required check，CI 注释记明
skipped ⇒ 永久 BLOCK，故 exit 0 是有意设计」。逐条比对 `.github/workflows/protocol-tests.yml` 头部：

```
③ 本次修法（当前实现）：4 个 required job（pytest/shellcheck/consistency/gate-backstop）
   不再有 job 级 if——job 始终运行，把 docs-only 判断内嵌进各检查 run step 开头
   （docs_only=true 时 echo + exit 0 → job conclusion="success"），分支保护即满足。
① ...6 个 required checks（pytest×2/shellcheck×2/consistency/gate-backstop）无 check-run
   → 分支保护按 "pending" 处理 → 永久 BLOCK（PR #193 实证 "6 of 6 required ..."）。
② ...job 级 if 跳过 → check conclusion="skipped"，而 GitHub 分支保护对 skipped 的
   required check 同样 BLOCK（mergeable_state="blocked"）。
```

**⇒ 设计的引用逐字准确，`gate-backstop` 确在 4 个 required job 之列（L280-298）。**
**设计据此把「改为 exit 1」撤回、改为「保留 exit 0 + 显眼 WARNING」，这个裁决是正确的**
——见 §2.X3。

**但设计遗漏一处**：`ci-gate-backstop.py` 还有**第二个 SKIP 面**（平台未识别，L127-130）
与**第三个 SKIP 面**（`phase ∈ PAUSED/READY/DONE`，`return 0`）。
设计只处理了「无 `.state.yaml`」与「平台未识别」两个，**漏了 phase 跳过面**。
`fa2fc3d` 也未补。**⇒ 遗漏项**，见 §3。

---

### X4 — 只认中文 `引用\s*P5\s*证据`：**属实，无其他分支**

`agate/scripts/check-p6-provenance.py:174-184`：

```python
174: def p6_declares_reuse(task_dir):
175:     """P6-acceptance.md 是否声明"引用 P5 证据、不重跑"（M21 落地的产出规格判定）。"""
...
184:     return bool(re.search(r"引用\s*P5\s*证据", text))
```

**⇒ 属实**：单一正则、单一中文短语、大小写与中英文变体均不认。
`grep -n "引用" agate/scripts/check-p6-provenance.py` 无第二处声明识别分支。

**设计的自我限定也属实**：它与同批/近期的 `extract_evidence_refs`（证据引用提取）**确实是两码事**
——前者判「是否声明复用」，后者提「引用路径」。设计说「两者不同，不共用判据」**核实为正确**。

**但设计的「消费方」分析有缺口**：`p6_declares_reuse` 的调用方是 `audit7_p5_evidence_reuse`
（L187+），而审计 7 又被 **`check-p6-provenance.py --audit7-only`** 暴露为 CLI
（L248-254），该 CLI 被 **`agate/phase-cards/P8-release.md:84`** 明确要求主 Agent 执行：

```
84:   跑 `python3 agate/scripts/check-p6-provenance.py --audit7-only $TASK_DIR`，读 stdout 的
85:   `AUDIT7_RESULT: <reuse_allowed|reuse_blocked|no_reuse_claim_possible>` 行判定：
```

**⇒ 放宽 X4 的识别 → 会改变 `AUDIT7_RESULT` 三态分布 → 会改变 P8 卡片要求主 Agent 执行的动作**
（原本 `no_reuse_claim_possible` 可能变成 `reuse_allowed`，从而**跳过 P5 重跑**）。
设计**只扫了「P6-acceptance 存量」**，**未把 P8 卡片的 audit7 消费链列为受影响文档**。见 §3。

---

### X5 — `bash` 无 `-o pipefail`：**属实**

`agate/scripts/agate_common.py:712-717`（函数 `run_test_with_formatter`，L701 起）：

```python
712:         proc = subprocess.run(
713:             cmd, shell=True, executable="bash",
714:             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
715:             text=True, encoding="utf-8", errors="replace",
716:             timeout=timeout_secs,
717:         )
```

**⇒ 属实**，且这是全仓**唯一**的 `shell=True` 站点：

```
$ grep -rn "shell=True" agate/scripts/*.py
agate/scripts/agate_common.py:713:            cmd, shell=True, executable="bash",
```

**消费方（实测 2 个）**：`check-tdd-red.py:224`、`agate-capture-env-baseline.py:129`。

**缺陷可复现**（一次性副本内实测）：

```
cmd='exit 3 | tail -1'      plain bash -> rc=0     bash -o pipefail -> rc=3
cmd='echo hi | tail -1'     plain bash -> rc=0     bash -o pipefail -> rc=0
cmd='pytest foo | tail -20' plain bash -> rc=0     bash -o pipefail -> rc=127
```

**⇒ 设计声称的失败吞噬确实存在，且确实可被 `pipefail` 修复。** 但**设计的改法字面不可实现**——见 §2.X5。

---

### X6 — `design_trivial` 按存在判而非值判：**属实，但设计对 fix 方向的理解有误（重要）**

`agate/scripts/check-gate.py:870-876`：

```
871:     min_candidates = 2
872:     if os.path.isfile(p1_file):
873:         p1_lines = _lines(_read_text(p1_file))
874:         if any(design_trivial_declared(line) for line in p1_lines):
875:             min_candidates = 1
```

`agate/scripts/agate_common.py:1389-1391`：

```python
1389: def design_trivial_declared(line):
1390:     """P1-requirements.md 行首 `design_trivial:` / `follows_existing_pattern:` 声明 presence。"""
1391:     return bool(re.search(r"^(design_trivial|follows_existing_pattern):\s*\S", line))
```

**⇒「按存在判」属实**，实测该正则的行为：

```
'design_trivial: false'        presence=True     ← 设计的指控成立
'design_trivial: true'         presence=True
'design_trivial:'              presence=False    ← ★ 空值不匹配
'follows_existing_pattern:'    presence=False    ← ★ 空值不匹配
```

**★ 关键发现（设计完全未提）**：该正则是 `:\s*\S`——**要求冒号后至少一个非空白字符**。
而 `follows_existing_pattern` 在**真实存量**里用的是 **YAML 块列表形式**（键行无值）：

```
$ for f in agate-workspace/tasks/*/P1-requirements.md; do grep -Hn "^\(design_trivial\|follows_existing_pattern\):" "$f"; done
agate-workspace/tasks/TAG0018-dsh-platform/P1-requirements.md:16:design_trivial: true        # P0 已锁定接入方案...
agate-workspace/tasks/TAG0018-dsh-platform/P1-requirements.md:17:follows_existing_pattern:
```

L17 实测 `presence=False`——**即「块列表形式的 `follows_existing_pattern` 现在就已经不被识别」**。

**⇒ 这是本批最严重的发现**：设计把 X6 描述成单向的「假绿（false 被当 true）」，
但同一正则**另有反向缺陷（合法声明被漏认）**。而设计提出的 fix「按值判断（`true` 才降为 1）」
**只会加剧反向缺陷**——见 §2.X6 的反例。

---

### X7 — P2-review 缺 `agent` 返回 2：**属实；两版设计的语义判定都需修正**

`agate/scripts/check-gate.py:891-897`：

```
891:     agent = _md_field_get("agent", p2_review)
892:     if not agent:
893:         sys.stderr.write("GATE P2: P2-review.md status:approved 但缺 agent 字段（向后兼容 WARNING）\n")
894:         return 2
895:     if agent == "main":
896:         sys.stderr.write("GATE P2: P2-review.md status:approved 但 agent=main（主 Agent 不可自行批准评审）\n")
897:         return 1
```

P1 对应处（L649-654）：

```
649:     agent = _md_field_get("agent", p1_review)
650:     if not agent:
651:         sys.stderr.write("GATE P1: P1-review.md status:approved 但缺 agent 字段\n")
652:         return 1
```

**⇒「P2 返回 2、P1 返回 1」属实。**

**exit 2 的真实语义（查约定）**——`agate/scripts/check-gate.py` 头部：

```
exit 0 = gate 通过; exit 1 = gate 未通过; exit 2 = 多数 phase 正常通过码（含动态
gate_commands 或语义判断后的"通过"出口）——pass 判定以 phases.yaml gate_pass_exit 为准：
P0-P3/P5/P6/P8 的通过码是 exit 2（... p2 L883 ... return 2）
```

`agate/rules/phases.yaml:61`：P2 块 `gate_pass_exit: 2`（实测 P2 块内确认）。
`agate/adr.md:59`：`gate 通过/不通过由脚本 exit code 决定（0=通过，1=不通过，2=需人工判断）`。

**⇒ 两个语义层并存，且 P2 的 `gate_pass_exit` 是 2**。这意味着：

- 对 `check-gate.py P2` 的**直接消费方**（`pre-commit-gate.py` L558-560）：`exit 2` → 打印
  「需主 Agent 手动判断」**但不 `sys.exit(1)`** ⇒ **commit 不被阻断**。**设计说的「放行」成立。**
- 对 `agate-next.py`：`exit 2 ∈ pass_set` ⇒ **直推下一阶段**（`phases.yaml` L17-19 注释）。

**⇒ 关键裁定**：`exit 2` 在 P2 **语义上确实是「通过」（gate_pass_exit）**，因此在
`if not agent: return 2` 这个位置，它**不是 WARNING，是 fail-open 放行**。

**⇒ 因此**：
- `f5e4c31` 版把问题描述为「**与 P1 不一致**」——**只对了一半**，它没识别「2 = 通过码」这个要害。
- `fa2fc3d` 版把问题改述为「**返回了通过码 ⇒ 真 fail-open**」——**这个改写是正确的**，
  且与源码/`phases.yaml`/`adr.md` 三方一致（本报告独立核实）。

**⇒ 任务提问「若 2 的语义本就是 WARNING 不阻断，统一起 1 是否过度？」的答案**：
`2` 在**这个 returning site 的实际效果**是「不阻断 + `agate-next` 直推」，
但它的**命名语义是 gate_pass_exit**。二者并不矛盾——**2 的「不阻断」恰恰因为它是通过码**。
因此**不存在「过度」问题**：把缺 `agent` 从「通过码」改成 `1`（未通过码）是**修正 fail-open**，
不是「把 WARNING 升级为阻断」。**设计的 fix 方向正确**。

**但有一个设计未评估的点（见 §2.X7）**：`agent == "main"` 已是 `return 1`（阻断），
而**缺字段**却走通过码——**攻击面是「删掉 agent 行」比「写 agent: main」更省事**。
这个「同一防线两个出口强弱倒挂」的论证，**两版设计都没写**，而它才是本项最强的立论。

---

### X8 — `install-hook._backup` 用 `not os.path.islink` 排除软链：**属实**

`agate/scripts/install-hook.py:130-135`：

```python
130: def _backup(hook_file, label):
131:     """已有非软链 hook → 备份为 {hook_file}.bak.{epoch}（cp 语义，sh set -e 下失败即退）。"""
132:     if os.path.isfile(hook_file) and not os.path.islink(hook_file):
133:         backup = hook_file + ".bak." + str(int(time.time()))
134:         shutil.copyfile(hook_file, backup)
135:         print(f"已备份现有 {label} hook")
```

**⇒ 属实**。且安装路径 `_ln_sf`（L103-127）**无条件 `os.unlink(link_path)`** 覆盖既有文件/软链
（L111-113），**覆盖前唯一守卫就是 `_backup`** ⇒ 软链被 `_backup` 排除后**直接丢失**。
设计的「数据丢失风险」定性**成立**。

**补充实测**：`os.path.isfile()` 对**指向常规文件的软链返回 True** ⇒ 若无
`not os.path.islink` 这一条，软链本**会**被 `shutil.copyfile` 按**目标内容**备份
（即丢失「它是个链」这一事实）。所以 `not islink` 的原意很可能正是「软链备份没意义」——
**设计的「记录链接目标而非复制内容」是对症下药**，见 §2.X8。

---

### X9 — P8 卡要求「以 READY 提交」⇒ `gate_p8` 跑不到：**属实（三重复现）**

**① 卡片原文**（`agate/phase-cards/P8-release.md:15`）：

```
15:    ⚠️ 此时 .state.yaml 的 phase 保持 READY，不要提前写 DONE——phase = 本 commit 的产出阶段；终态 DONE 收尾随任务终态 commit 一起
```

**② hook 跳过序**（`pre-commit-gate.py:320`）：`if phase in ("PAUSED", "READY", "DONE"): continue`

**⇒ 以 `phase: READY` 提交 ⇒ `continue` ⇒ 2h.1 的 `check-gate.py P8` 永不执行。冲突属实。**

**③ 实证统计复现**（用设计分析附录的同款 `--follow` 命令）：

```
$ n=0; p8=0; for f in $(git ls-tree -r --name-only HEAD | grep "tasks/[^/]*/\.state\.yaml$"); do
    ph=$(git show HEAD:$f | grep "^phase:" | awk '{print $2}')
    case $ph in READY|DONE) n=$((n+1)); git log --follow -p --format= -- $f | grep -qE "^\+phase: *P8" && p8=$((p8+1));; esac
  done; echo "$n $p8"
READY_DONE=38 P8_EVER=16
```

**⇒ 38/16 逐字复现**，与设计声称及外部 §5 一致。

**④ 但「gate_p8 跑不到」需要限定**（设计未做此限定，实测补充）——`gate_p8` 有**两条替代路径**：
- `gate_p8` 的 version/CHANGELOG 检查是**双路径**（`cached` + `HEAD~5..HEAD` 回看）
  ⇒ 若 bump/CHANGELOG 在**前 5 个 commit 内**，检查仍会命中；
- 现实提交序列（实测 TAG0037 / TAG0028）显示**发布产出 commit（`phase: P8`）+ READY 收尾 commit 是两次**：

```
TAG0037  59aeaeb phase=READY   wf(TAG0037-P8): READY——收尾（...）
         30e2354 phase=P8      wf(TAG0037-P8): 发布 v0.73.0 —— ...
TAG0028  837fc52 phase=READY   wf(TAG0028-P8): RM-AG0055 发布——v0.67.0 ...
```

**⇒ 所以「跑不到」的准确表述是**：卡片 L15 的**指令**导致**当次 commit** 不被 gate_p8 检查；
而**实践中有项目自发拆成两次 commit**（16/38 走了 P8 态）。
`gate_p8` 的**完整刚性**（`bump_type`/`debt_check`/roadmap done 回写）在 READY 提交上**确实不生效`**。
**设计的缺陷定性成立，但「永不运行」措辞过强**（对 16/38 不成立）。见 §2.X9。

---

## 2. 目标行为裁定

### X1 — **应拒绝（需重新设计）**

**裁定：`应拒绝`**。设计的「扫描移到 `continue` 之前 + PAUSED 只扫不阻断」**方向对，但实现描述不足，
且完全不覆盖真正的覆盖面缺陷。**

**反例 ①（覆盖面，实测）**：扫描被 `if any(f.startswith(prefix) for f in _staged_name_only()):`
（L327）门控——**只有「任务目录下有文件被暂存」时才扫**。一次性副本实测：

```
staged: ['app.py']
any staged under task dir? False
=> scan would run? False
```

**⇒ 在 `phase: P4`（一个「会被 gate」的阶段）下，把 `[PROD_TOUCHED]` 写进 `app.py`（非任务目录文件）
也完全不被扫描。** 把 `continue` 下移**一点也改变不了这一点**。

**⇒ 结论**：设计声称的目标「**所有阶段都扫描**」**无法由它给出的改动达成**——
它达成的是「所有阶段的**任务目录内**文件都扫描」。**目标表述与实际改动不匹配**，
这是**必须修的设计缺陷**（要么改目标为「所有阶段的任务目录 diff 都扫」，要么同时放宽 L327 门控——
但后者是**扩大扫描面**，属**跨模块影响**，不属「第 0 批小改动」）。

**反例 ②（连带行为，实测）**：设计的改动必然要把 L322-323 的
`if not os.path.isdir(task_dir): continue` 一起考虑——`continue` 跳过的是 **2g → 2o 一整段**
（frontmatter schema L352、P6 归一化 L359、`check-gate` L365、`write_gate_result` L371、
`append_event` L373、以及 2i-2o 的 provenance/pruning/scope/retrospective/CHANGELOG/evidence）。
**任务问「改成扫描移到 continue 之前会不会连带改变其他行为」——答案是不会，只要移动的粒度是
「把 2g.1 整体上移」而不是「删掉 continue」**。设计此处的表述（「把跳过 gate 与是否扫描解耦」）
**恰好就是这个正确粒度**，**这一点设计是对的**。

**反例 ③（PAUSED 可行性，实测）**：任务问「PAUSED 的处理是否真的可行」。**可行**，理由：
`state-machine.md:98` 定义 `任意阶段 --[出现 PROD_TOUCHED]--> PAUSED`，
即 **PROD_TOUCHED 本身是通往 PAUSED 的转移**。因此「PAUSED 时只扫不阻断」在语义上自洽：
任务已因生产接触被人工接管，hook 不该再叠加阻断。
**但设计未说明一个后果**：PAUSED 提交时扫描若**发现新 PROD_TOUCHED**，**只打印不阻断**——
按 `state-machine.md:255`（`PAUSED --[人工确认/决策]--> 恢复到 PAUSED 前的阶段`），
这条信息**没有任何机械消费方**。**⇒ 建议**：PAUSED 分支应至少 `append_event`
（或写 WARNING 到帐本），否则「只扫描不阻断」等于**只打印到 stderr**，**无留痕**。

---

### X2 — **可接受（但需补两处）**

**裁定：`可接受`**（策略正确：新增 `read_staged_state_phase` 而不改既有 `read_state_phase`，
避免 2 个调用点语义漂移）。**但需补**：

1. **必须补「调用点」精度**：真实调用点是 L257 **和 L590**。设计只提「hook 的调用点」（单数）。
   **L590 是第二调用点**，若不一起改，会出现**同一次 commit 内两处 phase 来源不一致**
   （见 §1.X2）。**⇒ 需修改。**
2. **「4 个调用方」的数字必须更正为实测 2 个**（`agate-advance.py` 是同名本地函数，非消费方）。
3. **暂存区读取的失败语义未定义**：`git show :<path>` 在**文件是新加（未在 HEAD）**、
   **路径含空格/非 ASCII**、**index 锁定**等情形下的行为，设计**未定义回退**。
   建议（`需修改`）：明确「暂存区读取失败 → 回退工作区 + 打 WARNING」并**给测试**。

---

### X3 — **可接受（裁定：设计对 CI 机制的理解正确，撤回 exit 1 是对的）**

**裁定：`可接受`**。理由（**独立核实**，非采信设计自述）：
- `protocol-tests.yml` 头部注释 ①–③ **逐字**支持「skipped/unchecked required check ⇒ 永久 BLOCK」；
- `gate-backstop` 确在 4 个 required job 内（L280）；
- 因此把 `return 0` 改成 `return 1` **会让本仓每次非-agate-task 的 PR 都红**，
  而它**本来就 detection 不到对象**——那是**把「没查」变成「查了且失败」的假信号**，
  **比假绿更糟**。

**⇒ 设计的「保留 exit 0 + 让未生效醒目可见」符合 `adr.md` 手段②「让错误可见」，裁定可接受。**

**但两点必补（`需修改`）**：
1. **漏了第三个 SKIP 面**：`phase ∈ ("PAUSED","READY","DONE")` 也 `return 0`（同一假绿形态）。
   设计只列了「无 `.state.yaml`」与「平台未识别」两行。**⇒ 必须补。**
2. **V3 的判据不够强**：设计写「输出含 WARNING 与『backstop 未生效』字样」——
   **这是关键词匹配，不是行为判据**，且**没有负向控制**。
   建议改为：断言 **exit 0 且新增输出 ≠ 原 `SKIP:` 单行**（结构化块），
   并加**「改坏即红」**用例（把 WARNING 删掉 ⇒ 测试红）。

---

### X4 — **可接受（但必须补消费方传播）**

**裁定：`可接受`**（三写法识别是正确方向）。**但**：

- **必须把 P8 卡片的 audit7 消费链加入影响面**（见 §1.X4）。放宽识别 ⇒ `AUDIT7_RESULT` 三态分布变化
  ⇒ **`P8-release.md:84-88` 的分支（重跑 P5 vs 复用）会改变行为**。
  设计**只扫 P6-acceptance 存量是不够的**。**⇒ 需修改。**
- **英文别名的具体词表未给**（设计只说「英文别名」）。**无词表 = 无法写测试 = 无法机械校验 V4。**
  **⇒ 需修改**（须在设计中列出确切的别名集合，或改判为「结构化字段 + 中文短语」两项，
  把英文别名降为可选）。
- **放宽 = fail-open 方向**（原本不识别 ⇒ 不触发 audit7 拦截；识别后 ⇒ 触发拦截）。
  设计说「放宽后可能让原本被拦的案例通过」——**说反了**：识别**更多**写法会让 audit7
  **更多**进入「已声明复用」分支，从而**更可能**判 `reuse_blocked` ⇒ **更多拦截**，
  不是「更多通过」。**⇒ 设计的风险方向描述错误，需更正**（不改变 fix 本身）。

---

### X5 — **可接受，但设计给的改法字面不可实现（须修正表述）**

**裁定：`可接受`（开 pipefail 正确），但设计的实现指引有硬错误。**

**实测反例（一次性副本）**：`subprocess.run(..., executable="bash -o pipefail")` **直接抛异常**：

```
FileNotFoundError: [Errno 2] No such file or directory: 'bash -o pipefail'
```

`executable=` 是**可执行文件路径**，不是命令行——**不能塞参数**。实际可行的三种写法（实测）：

```
cmd='exit 3 | tail -1'    plain=0   SHELLOPTS-env=3   'set -o pipefail;'-prefix=3
cmd='pytest foo | tail -20' plain=0 SHELLOPTS-env=127 'set -o pipefail;'-prefix=127
```

**⇒ 设计 §X5 写「改为 `bash -o pipefail`」是错的**，需明确为：
`executable` 保持 `"bash"`，改为 **`cmd = "set -o pipefail; " + cmd`** 或 **`env["SHELLOPTS"]="pipefail"`**。
（二者语义略有差异：`SHELLOPTS` 受 readonly 影响；**推荐前者**，且**须加测试**。）

**存量影响（任务点名要求实测）——已跑**：

```
total gate_commands entries: 107   with pipe: 1
  TAG0003-workspace-architecture  P5 :: bats --formatter tap ... 2>&1 | tail -30
```

**⇒ 全仓 107 条 `gate_commands` 中仅 1 条含管道**，且是 `2>&1 | tail -30`
（`2>&1` 不是管道段，`bats` 是唯一起作用段）。**⇒ X5 的存量转红风险≈0**（远低于设计担心的「可能有」）。

**⚠️ 但设计漏了真正的风险面**：`pipefail` 影响的是 **`check-tdd-red.py` 的 P3 红灯判定**——
它的语义是「**非 0 = 红灯 = 符合 TDD**」。加了 pipefail 后，**原本 rc=0（假绿）的用例会变 rc≠0**，
在 P3 语境下**这是「更红」而不是「更红转绿」**——
**⇒ X5 可能让 P3 的 `check-tdd-red` 从「绿灯=违反TDD=FAIL」变成「真红灯=PASS」**，
即 **方向是放宽 P3 gate**，不是收紧。**设计把 X5 的风险描述为「由绿转红」，
方向很可能相反（对 P3 消费方而言）。这是设计未评估的语义耦合。⇒ 需修改。**

---

### X6 — **应拒绝（fix 会破坏一个现存合法用例；设计漏掉同函数的反向缺陷）**

**裁定：`应拒绝`**。这是本报告**最强的反对意见**，构造了**具体反例**。

**反例（实测，真实存量 TAG0018）**：

```
L16: design_trivial: true        # P0 已锁定接入方案...
L17: follows_existing_pattern:
```

```
$ probe: design_trivial_declared(line) 逐行
L16: presence=True   key/val=('design_trivial', 'true')
L17: presence=False  key/val=('follows_existing_pattern', '')
```

**⇒ 三个独立结论**：

1. **设计的 fix（「按值判断，`true` 才降为 1」）会漏掉块列表形式**：
   L17 的 `follows_existing_pattern:`（YAML 块列表，`agate-frontmatter-check.py:54` 的 schema
   **明确声明它是 `list` 类型**）**值不是 `true`** ⇒ 按值判会**判为未声明**。
   而它对 TAG0018 的**降为 1** 之所以今天「生效」，**只是因为同文件 L16 的 `design_trivial: true`**。
   **⇒ 反例：一个只声明了 `follows_existing_pattern`（块列表）的任务，今天「碰巧」因
   `:\s*\S` 而（错误地）不算数、改后仍不算数 ⇒ 该任务 `candidate_count: 1` 会被判红。**
   设计**未识别 `follows_existing_pattern` 是 list 类型**这一事实。

2. **设计把 X6 描述成单向「假绿」，实际是双向缺陷**：
   `design_trivial: false` → 被误当声明（**设计已指出**）；
   `follows_existing_pattern:`（块列表）→ **合法声明不被识别**（**设计未指出**，且 fix 会强化它）。

3. **正确 fix 方向**：**不能只「按值判」**，必须**同时**：
   - `design_trivial`：`_md_field_get("design_trivial", p1_file)` 走既有 bool 解析通道
     （`agate-md-field-get.py:230` 已有 `_regex_scalar(text, r"design_trivial:\s*(true|false)")`），
     **判 `== "true"`**；
   - `follows_existing_pattern`：**presence 语义**（它有值即为 block list，**不存在 true/false**）
     ⇒ 应为 `re.match(r"^follows_existing_pattern:\s*$", line)` **或**非空值，**两者都算声明**。
   **⇒ 即：两个键语义不同，必须分开判，不能合并成一条「按值」规则。**
   设计把它们合并在同一条 `design_trivial_declared` 里讨论，是**概念错误**。

**存量影响（实测）**：全仓**仅 1 个任务**命中该正则（TAG0018），
且其 `candidate_count: 1`（实测唯一 `<2` 的任务）。**⇒ 若按设计原样实现，TAG0018 会由绿转红**
（因为它靠 `design_trivial: true` 降为 1——若保留该路径则不转红；若按「按值」并**正确处理**
则也不转红。**但若实现者忽略 `follows_existing_pattern` 的 list 语义，就会转红**）。
**⇒ 设计必须写明这两键的分别处理，否则本批会制造一个真实的存量转红。**

---

### X7 — **可接受（方向正确），但两版设计都缺最强论据，且 `fa2fc3d` 版遗留一个未决问题**

**裁定：`可接受`**。理由已在 §1.X7 给出：`exit 2` 在该 site **实际就是通过码**
（`phases.yaml` P2 `gate_pass_exit: 2` + `check-gate.py` 头部 + `adr.md:59` 三方一致），
故 `return 2` = fail-open 放行，改 `return 1` 是**修正**而非「过度收紧」。

**对任务提问「统一起 1 是否过度」的直接回答：不过度。**
判据：`pre-commit-gate.py:558-560` 对 `gate_exit == 2` **只打印不 `sys.exit(1)`**，
`agate-next.py` 对 `2 ∈ pass_set` **直推下一阶段**。⇒ 2 的「不阻断」**正是因为它是通过码**。
若真的想表达「WARNING 不阻断」，正确写法是 `return 2` **之外**另走告警通道——
而**P2 的 pass_set 就是 {2}**，**没有既 WARNING 又不通过码的中间态可用**。
**⇒ 设计的两个选项（「一次性转红」vs「另择机制」）中，一次性转红是正确的**，
因为它**没有存量**（见下）。

**✅ 存量扫描结论（实测，完全支持设计的 fix）**：

```
=== P2-review.md status/agent 扫描（37 个任务）===
全部 status=approved，全部 agent=<非空>（plan-eng-review / review）
missing agent: 0
=== 交叉核对 ===
P1-review   total=37  missing agent=0
P4-review   total=37  missing agent=0
P6-acceptance total=37 missing agent=0
```

**⇒ 存量 37 个任务的 P2-review `agent` 字段 100% 齐备 ⇒ 改为 `return 1` 的真实转红数 = 0。**
**`fa2fc3d` 担心的「若存量大量缺 agent，是否该给迁移期」——实测答案是不需要。**
（设计分析称该分支「向后兼容」**暗示有存量**——**实测证伪：该暗示没有事实依据**。）
**⇒ 这直接消解了 `fa2fc3d` 自认「本项最需要评审裁定的点」。裁定：无需迁移期，直接改。**

**⇒ 但两版都必须补的一条（`需修改`）**：**最强的立论是「强弱倒挂」**——
`agent == "main"` ⇒ `return 1`（阻断），而**缺字段** ⇒ 通过码。
**⇒ 绕过这道防线的最省事路径是「把 agent 行删掉」，比写 `agent: main` 更简单。**
两版设计都没有写这个论证，而它才是本项不可辩驳的理由（「统一为 exit 1」本身不是理由，
`f5e4c31` 的原始表述会被「P1/P2 本就该不同」轻易反驳）。

---

### X8 — **可接受（但设计的做法不是最简，且遗漏一个既有 bug）**

**裁定：`可接受`**（「所有 hook 都备份」是最小可逆改动，理由成立）。
「不选链式调用（属第 4 批）」的取舍**正确**——链式调用会改**执行语义**，
把 `install-hook` 从「安装」变成「编排」，确实属关卡层。

**但两点（`需修改`）**：

1. **任务问「记录链接目标是否有更简做法」——有。**
   设计把「备份软链」复杂化为「记录链接目标」。更简且**语义更正确**的做法：
   **保留软链本身**——把 `os.unlink(link_path)`（L111-113）改为
   **「若既有目标是软链且不指向本安装 ⇒ 先 `os.rename` 到 `.bak.<epoch>`（rename 保留 inode/链属性），
   或在备份文件中写入 `-> <target>` 的一行文本」**。
   关键点：**软链的「内容」就是它的 target 字符串** ⇒ **`os.readlink()` 一行即可**，
   不需要任何新格式。「记录链接目标」如果指的是这个，则应**明写 `os.readlink`**；
   若指别的格式，需给样例。**⇒ 设计表述模糊，需具体化（含备份文件的确切格式与样例）。**
2. **遗漏既有 bug（实测）**：`_backup` 的 `os.path.isfile(hook_file)` **对悬空软链（dangling symlink）
   返回 False** ⇒ **悬空软链既不备份、又被 `os.unlink` 删除**。
   这比设计指出的「软链不备份」**更严重**（至少软链还指向有效目标时用户能自己恢复）。
   **⇒ 建议并入本批**（同函数同主题）。见 §3「第 10 项」。

---

### X9 — **需修改（改卡片的结论对，但设计对「改哪儿」定位不足，且未验证可拆分性）**

**裁定：`需修改`**。任务问「只改卡片文字使之与 hook 行为一致，不改 `agate-next`——这与卡片现状哪个对？」

**⇒ 实测裁定：设计（改卡片）对，卡片现状错。** 依据（**独立读取语义定义**，非采信设计）：

- `agate/git-integration.md:33`：**`phase` = 本 commit 提交的产出阶段，不得提前写下一阶段**。
- `agate/phase-cards/P8-release.md:15` 却写「phase 保持 READY」——
  而 **P8 的产出（`P8-release.md` + bump + CHANGELOG）正是本 commit 要提交的产出**
  ⇒ **按 L33 的定义，本 commit 的产出阶段是 P8，phase 就该写 P8。卡片 L15 自相矛盾。**
- 外部 §2.1 已指出同一冲突；`agate/git-integration.md` 的 phase 语义是**权威源**，
  卡片 L15 是**违背权威源的表述**。**⇒ 改卡片 = 向权威源对齐。裁定：设计正确。**

**"以 P8 提交产出、再单独提交 READY" 是否可行？——可行，且实证已成惯例：**

```
TAG0037  30e2354 phase=P8    wf(TAG0037-P8): 发布 v0.73.0 —— ...
         59aeaeb phase=READY  wf(TAG0037-P8): READY——收尾（...）
```

**⇒ 拆分路径真实存在**（16/38 走过），无脚本依赖「以 READY 一次性提交」——
`gate_p8` 只读暂存区/`HEAD~5`，**不要求 phase==P8**（它拿 phase 由 hook 决定，
hook 在 READY 时**根本不调它**）。**⇒ 无其他卡片/脚本依赖「以 READY 提交」。**

**但设计的三处不足（`需修改`）**：

1. **「不改 `agate-next`」的理由不成立**：实测 `agate-next.py` 的行为是
   **「`.state.yaml` phase ∈ {PAUSED, READY, DONE} → 提示不推进，exit 0」**（文件头注释 L8）。
   即 `agate-next` **本来就不会把 phase 预写成 READY**。**⇒ 设计说「不改 agate-next 的预写行为」
   是打空靶**——`agate-next` 没有被指称的那个行为。**须更正理由。**
2. **未处理「`gate_p8` 要求的 tag 尚未创建」的时序**：卡片 L89-93（DEBT0013）明确
   **P5 重跑须在 tag 之后**。若改为「以 P8 提交」，则 **`phase: P8` 的 commit 里 tag 还没打**
   ⇒ `gate_p8` 的 roadmap/version/CHANGELOG 检查**与 tag 相关的部分时序更紧**。
   设计**未评估**这条既有 DEBT0013 交互。**⇒ 需修改（至少写明不受影响的依据）。**
3. **V9 的判据是「卡片文字与 hook 行为一致」——不可机械校验**（对文档做语义判定）。
   建议改为**可机械校验**的形态：断言卡片**不含**「phase 保持 READY」字样
   **且含**「以 `phase: P8` 提交 P8 产出」字样（`check-protocol-consistency.py` 风格）。

---

## 3. 遗漏项

### 3.1 对照外部 §5：X1–X9 **齐全，无遗漏**

逐条比对 `https://peek.gsis.top/ccyvim`（`analysis-declare-and-enforce.md`，文件 sha 未锚定，
抓取于 2026-10-04，`http=200 size=46519`）§5 表格与设计 X1–X9：
**9 项一一对应，编号、文件、行号全部对上**（外部 §5 X3 的 `ci-gate-backstop`、
X5 的「约 :706」（实测 :713，**行号已漂移，内容一致**）、X7 的 `:893`/`:651`（实测 `:894`/`:652`，
**同样漂移 1 行**））。**⇒ 无「漏了一项」的情况。**

**⇒ 但外部 §7 第 0 批的范围与设计**不完全一致**，这是**范围遗漏**：
外部 §7 写第 0 批 = 「§5 的 X1、X3–X9 + X2 中『phase 从暂存区读取』这一部分」。
设计**没有列 X2 之外的差异**——实际**一致**。**⇒ 范围无遗漏。**（本项为**已核实**，非推断。）

### 3.2 §2 四个「特别关注点」的覆盖情况

任务点名要求核验外部 §2 的四个特别关注点（2.1 phase 语义 / 2.4 关卡层分级 /
2.5 交付验证时点 / 2.6 复核层）。设计对它们的处理：

| 外部 § | 设计处理 | 评价 |
|---|---|---|
| §2.1 phase 语义 | 只在 X2/X9 触及，且**明确推给第 1 批** | **合理**（设计 §7 已声明分工） |
| §2.4 关卡层分级 | **推给第 4 批**（X2「按提交类型分级」） | **合理**，但见下 |
| §2.5 交付验证时点 | **完全未提** | **合理**（属第 4 批 `delivery`） |
| §2.6 复核层 | **完全未提** | **合理**（属第 5 批 `agate-ci-verify`） |

**⇒ 第 0 批不覆盖 §2.4/§2.5/§2.6 是**正确的**——它们都需要新机制，不是「现在就是错的」。
设计的分批纪律**成立**。**

**⚠️ 但 §2.4 有一处**被设计漏掉的第 0 批级联动**：外部 §2.4 的「每一次提交」行写明
**「PROD_TOUCHED 扫描（PAUSED 只扫描不阻断）」**——这正是 **X1 的目标行为**。
**⇒ 设计 X1 与外部 §2.4 是同一机制的两次描述，设计未指出这一归属**。
影响：**第 4 批实现关卡层分级时，会再次改 X1 所在的同一段代码**。
**⇒ 设计应在 §7「与主体的关系」里**显式声明 X1 与第 4 批的边界**（正如它对 X9 与第 1 批所做的那样）。
设计对 X9 做了这个声明，**对 X1 漏了**。**⇒ 遗漏项。**

### 3.3 消费方遗漏（逐项）

| 项 | 设计列的消费方 | 实测遗漏 |
|---|---|---|
| X2 | 「4 个调用方」 | **实测 2 个**；**漏 L590 第二调用点**；**误把 `agate-advance.py` 同名本地函数计入** |
| X4 | 只扫 P6-acceptance 存量 | **漏 `P8-release.md:84-88` 的 `--audit7-only` CLI 消费链** |
| X5 | 未列 | **漏 `check-tdd-red.py` 的 P3 红灯语义**（反向影响，见 §2.X5）；**漏 `agate-capture-env-baseline.py`** |
| X6 | 未列 | **漏 `agate-md-field-get.py:230` / `agate-frontmatter-check.py:54`（`follows_existing_pattern: list`）** |
| X7 | 未列 | **漏 `agate-next.py` 的 `pass_set` 直推路径**（这正是「2=通过」的证据链） |
| X9 | 未列 | **漏卡片 L89-93 的 DEBT0013 时序** |

### 3.4 「第 10 项」建议

**建议并入第 10 项（同族，同函数、同主题）：`install-hook._backup` 对悬空软链的漏处理。**

实测依据：`os.path.isfile()` 对 dangling symlink 返回 `False`
⇒ 该软链**既不备份**（L132 条件不满足）**又被 `os.unlink` 删除**（L111-113）。
与 X8 是**同一函数的同一缺陷族**（「备份判据用 `isfile`」），
且**风险更高**（连「软链还在」这个恢复线索都没了）。
**⇒ 并入 X8 一起修，边际成本≈0**（同函数、同测试）。

**不建议并入的（避免批次膨胀）**：
- X1 的 L327 门控放宽（扩大扫描面，跨模块，见 §2.X1）；
- X3 的 `agate-ci-verify` 替换（设计已正确推给第 5 批）。

---

## 4. 风险缓解充分性（§4.2 全量扫描的可行性）

**裁定：`不充分`——设计说「须先扫描」，但**没有说清每项怎么扫**，且 4 项中有 2 项的扫描**不可行**。

设计 §4.2 只给了「须扫描」与「预期」，**未给命令**。逐项可行性与实测结果：

| 项 | 设计说 | 扫描可行性 | 我的实测 |
|---|---|---|---|
| X1 | 「存量任务的收尾提交 diff 是否含 `[PROD_TOUCHED]`」 | **不可行**（如设计所述） | 「收尾提交 diff」需逐 commit 重放 hook——**成本高且是写操作风险**。**替代**：扫 `[PROD_TOUCHED]` **字面量**分布即可（实测 209 个文件命中，全部在 P1/P4/P6 产出与 evidence 里）——**但这不能回答「收尾提交会不会被拦」** ⇒ **设计的方法不可操作** |
| X5 | 「存量 `gate_commands` 是否含管道」 | **可行**，已实测 | **107 条中仅 1 条含管道** ⇒ **风险≈0**（见 §2.X5） |
| X6 | 「存量 P1 是否写了 `design_trivial: false`」 | **可行，但设计问错了问题** | 全仓**仅 1 个任务命中**（TAG0018），且是 `design_trivial: true`。**真正的风险不是 `false`，是块列表形式的 `follows_existing_pattern`**（见 §2.X6） |
| X7 | 「存量 P2-review 是否缺 `agent`」 | **可行**，已实测 | **37/37 齐备，missing=0** ⇒ **转红数 = 0**，**无需迁移期** |

**⇒ 结论**：
1. **X5/X6/X7 的扫描我已实际执行，结果都支持合并**（且 X7 的扫描直接消解了 `fa2fc3d` 的未决问题）。
2. **X1 的扫描方法不可操作**——设计必须给出**替代判据**（否则 V10「无未解释的转红」无法验收）。
   **建议替代**：`git log -p --all -- agate-workspace/tasks/*/` 中**新增行含 `[PROD_TOUCHED]`
   且该 commit 的 `.state.yaml` phase ∈ {READY,DONE,PAUSED}** 的 commit 列表。
   **这个可以机械跑出来，设计应写明。**
3. **X6 的扫描问题问错了**（应扫 `follows_existing_pattern:` 块列表与 `design_trivial: false` **两者**）。
4. **V10 缺判据强度**：「无未解释的转红」**未定义「解释」的标准** ⇒ 无法机械校验。
   **建议**：V10 改为**附扫描命令 + 原始输出 + 逐条裁决**，而非「列出说明」。

**另：设计 §4.2 正确引用了 `AGENTS.md` 工作流 0a（只在副本上跑）——这一点设计做对了**，
本报告全部实测也遵守了同一纪律（`mktemp -d` 一次性副本，建→用→清同一调用）。

---

## 5. hotfix 正当性裁定

**裁定：`成立（可走 hotfix）`——但有一个重要的限定条件。**

按 `AGENTS.md`「hotfix 通道」三条判据逐条核（**修订版判据，文件数不作条件**）：

| # | 判据 | 裁定 | 依据 |
|---|---|---|---|
| 1 | **单一主题**（一个自洽目标 + **无跨模块影响**） | **⚠️ 有保留地成立** | 主题自洽（「修既有缺陷」，设计 §6 已申明）。**但「无跨模块影响」不完全成立**：X1 的完整目标（所有阶段扫描）**必须放宽 L327 门控**（跨到 diff 覆盖面）；X4 会传播到 P8 卡片的 audit7 链；X9 改**协议正文文本**，影响**所有使用 agateon 的项目** |
| 2 | **不是 agate 任务** | **成立** | 无 P0-brief/`.state.yaml`/P1-P8 产物；本批是「一次性修复」 |
| 3 | **可快速验证** | **⚠️ 部分成立** | X3/X5/X7/X8 有明确判据；**但 X1/X4/X6/X9 的验收锚（V1/V4/V6/V9）是关键词或语义判定，无法机械校验** ⇒ 不满足「不需多轮评审」 |

**⇒ 结论**：
- **不因「7 个文件 + 6 个脚本 + 1 个卡片」而否定 hotfix**——`AGENTS.md` **已明确删除文件数条件**
  （2026-10-03 据 `#390` 实证更正），**设计引用该修订版判据是正确的**。
- **但判据 1「无跨模块影响」与判据 3「可快速验证」当前不满足**，**原因不是文件数，是 §2 里那四项的
  目标行为尚不可机械验证**。
- **⇒ 裁定**：**修完 §2 的指定项后，hotfix 成立**。
  若**拒绝**修 §2（例如坚持 X1 原样、X6 原样），则**应转为立项**——
  因为那时改动会**同时**（a）扩大扫描面、（b）制造存量转红，**不再是「一次性修复」**。
- **必须留痕**：碰 `agate/` 脚本面 ⇒ **须独立评审 + commit message 含 `self-gate-review:`**
  （设计 §6 提到了 hotfix 判据，**但未提 `self-gate-review:` 留痕义务** ⇒ **补**）。
  且按 `AGENTS.md`，改动面 >5 文件 ⇒ **PR 描述里一句话说明为何不立项**（设计 §6 已承诺，**正确**）。

---

## 6. 总体判定

### **`NEEDS-REVISION`**

**⇒ 能否开始实现：`不能`——须先修订设计（清单见下）。**

理由汇总（按严重度）：

1. **X6 的 fix 会制造真实的存量转红**（`follows_existing_pattern:` 块列表被按值判漏认）——
   **应拒绝，须重设计**（两键语义不同，须分别处理）。
2. **X1 的目标行为无法由其改动达成**（L327 门控）——「所有阶段都扫描」是**虚假承诺**，
   且要达到真目标就**跨出第 0 批范围** ⇒ **须改目标表述或改批次划分**。
3. **X5 的实现指引字面不可执行**（`executable="bash -o pipefail"` 抛 `FileNotFoundError`）
   ⇒ **须改写法**（`set -o pipefail;` 前缀）。
4. **X2 的「4 个调用方」不实**（实测 2 个），且**漏 L590 第二调用点** ⇒ 会引入新的 phase 来源不一致。
5. **X4 的消费方遗漏 P8 卡片 audit7 链**，且**英文别名无词表** ⇒ V4 不可机械校验。
6. **X9 的「不改 agate-next」理由打空靶**（`agate-next` 本就无该预写行为），且**漏 DEBT0013 时序**。
7. **X3 漏第三个 SKIP 面**（phase ∈ PAUSED/READY/DONE）。
8. **§4.2 的 X1 扫描方法不可操作**、X6 扫描问错问题、V10 无判据强度。

**✅ 设计做对、经独立核实应予保留的部分**（不要因为上述问题一并推翻）：

- **X3 撤回 exit 1 的裁决**——对 CI required check 机制的理解**逐字准确**，是本次评审中
  **最有价值的一处自我修正**；
- **X7 的方向（改 `return 1`）**——**存量实测 37/37 齐备 ⇒ 转红数 0，无需迁移期**；
  `fa2fc3d` 的「2 = 通过码」改写**正确**；
- **X8 选「所有 hook 都备份」而非链式调用**——批次纪律正确；
- **X2 选「新增函数」而非改既有 `read_state_phase`**——避免语义漂移，策略正确；
- **§7 对 X9/第 1 批分工的显式声明**——正确的防重复改设计；
- **§4.2 对 `AGENTS.md` 0a（副本上跑）的引用**——正确；
- **hotfix 判据用修订版**（文件数不作条件）——引用正确。

---

## 7. 已实测 vs 推断（严格区分）

### 7.1 **已实测**（命令与输出在本报告中给出）

| # | 内容 |
|---|---|
| 1 | 文件 sha256 双版本（`f5e4c31` / 工作区 = `aa60dc…`；`fa2fc3d` = `9160b2…`） |
| 2 | X1 的 `continue`（L320-321）在扫描（L325+）之前；**扫描被 L327 门控**（`app.py` 反例） |
| 3 | X2 的 `read_state_phase` 实现与**全部调用点（2 个生产点）**；`agate-advance.py` 为同名本地函数 |
| 4 | X3 仓库根无 `.state.yaml`；`resolve_workspace` 返回 `agate-workspace/` |
| 5 | X3 CI 注释 ①–③ 原文；`gate-backstop` 在 4 个 required job 内（L280-298） |
| 6 | X4 单一中文正则（L184），无第二分支 |
| 7 | X5 唯一 `shell=True` 站点（L713）；**107 条 `gate_commands` 中仅 1 条含管道**；`pipefail` 三写法实测 rc 差异；`executable="bash -o pipefail"` 抛 `FileNotFoundError` |
| 8 | X6 `design_trivial_declared` 正则行为（4 个变体）；**TAG0018 L17 块列表 `presence=False`**；全仓仅 1 任务命中；`candidate_count<2` 仅 TAG0018；`follows_existing_pattern: list` schema |
| 9 | X7 `return 2`/`return 1` 行号与效果；`phases.yaml` P2 `gate_pass_exit: 2`；`check-gate.py` 头部 + `adr.md:59`；**P2-review/P1-review/P4-review/P6-acceptance 各 37 个，missing agent = 0** |
| 10 | X8 `_backup` 的 `isfile and not islink`（L132）+ `_ln_sf` 的 `os.unlink`（L111-113） |
| 11 | X9 卡片 L15 原文；`pre-commit-gate.py:320`；**38/16 统计复现**；TAG0037/TAG0028 的 `P8`→`READY` 两次提交实测 |
| 12 | X9 `gate_p8` 的 version/CHANGELOG **双路径**（cached + `HEAD~5`） |
| 13 | `gate_p8` 只读暂存区/HEAD，**不要求 phase==P8** |
| 14 | 外部 §5 表格 9 项与设计一一对应；外部行号部分漂移（`:706`→`:713`，`:893`→`:894`） |

### 7.2 **推断**（未实测，须后续验证）

| # | 推断 | 置信度 |
|---|---|---|
| 1 | `return 2` 的「不阻断」**因其是 pass_set 成员**；若改成 1，`agate-next` 会走 retreat 分支 | 高（源码 + YAML 注释一致），但**未实跑 `agate-next` 端到端** |
| 2 | X5 加 pipefail 对 `check-tdd-red.py`（P3 红灯语义）**方向是放宽** | 中——**未构造 P3 端到端反例**（需 TDD 红灯场景） |
| 3 | X4 放宽 ⇒ audit7 更多判 `reuse_blocked` ⇒ P8 卡片分支改变 | 中——**未跑 `--audit7-only` 构造用例** |
| 4 | X1 的 `[PROD_TOUCHED]` 存量 209 命中中，**无一处位于 READY/DONE 收尾提交** | 中——**未做逐 commit phase 重放**（成本高） |
| 5 | `install-hook` 的 dangling symlink 漏备份 | 高（Python 语义确定），**未实跑 install-hook** |
| 6 | X6 修正后**不会**造成 TAG0018 转红 | 高（若按本报告 §2.X6 的分别处理），**未写代码验证** |

### 7.3 未能完成的事项（如实上报）

- **外部设计分析的 sha256 未锚定**：该文档由 PeekView 提供（`https://peek.gsis.top/ccyvim`，
  `curl` 得 JSON 包络，正文为 `files[0].content`，26148 字符），**无独立哈希可比**。
  本报告对它的引用基于**本次抓取的内容**（抓取时间 2026-10-04，`http=200 size=46519`）。
  **⇒ 若该页面后续被编辑，§3 的比对结论会失效。**
- **未跑全量 pytest**（按只读纪律要求）。本报告的全部结论**不依赖**测试套件运行。
- **未实跑 `pre-commit-gate.py` / `install-hook.py` 端到端**（会写真实仓库/账本）。
  X1 的扫描门控通过**独立复现同一条件表达式**验证，非端到端。

---

## 8. 给主 Agent 的行动清单（按优先级）

**P0（不修不能实现）**：
1. **X6 重设计**：`design_trivial` 按 `== "true"` 判；`follows_existing_pattern` 保持 **presence**
   （块列表也算）；**不能合并成一条按值规则**。
2. **X1 改目标表述**：明确为「所有阶段的**任务目录 diff** 都扫描」；
   若要真「所有阶段所有文件」，**须显式声明这属第 4 批**（与外部 §2.4 同源）。
3. **X5 改实现指引**：写成 `cmd = "set -o pipefail; " + cmd`（**不可** `executable="bash -o pipefail"`）；
   并**评估对 `check-tdd-red.py` P3 语义的反向影响**。

**P1（须补，否则验收不成立）**：
4. **X2**：调用点改为「2 个（L257 + L590）」，删掉「4 个」；定义暂存区读取失败的回退。
5. **X4**：补 P8 卡片 audit7 消费链；给英文别名**确切词表**；**更正风险方向**（放宽 ⇒ 更多拦截）。
6. **X9**：更正「不改 agate-next」的理由；评估 DEBT0013 时序；V9 改机械判据。
7. **X3**：补第三个 SKIP 面（phase ∈ PAUSED/READY/DONE）；V3 加强为「输出结构变化」判据。
8. **X8**：把「记录链接目标」具体化为 `os.readlink` + 备份文件格式样例；
   **并入 dangling symlink 用例（第 10 项）**。
9. **X7**：补「强弱倒挂」论证（缺字段比 `agent: main` 更易绕过）；
   **写死在设计中：存量扫描 37/37 齐备 ⇒ 无需迁移期**。

**P2（流程）**：
10. **§7 补 X1 与第 4 批的边界声明**（同 X9 与第 1 批的做法）。
11. **§4.2 补每项的扫描命令**，特别是 X1 的替代判据；**V10 加判据强度**。
12. **§6 补 `self-gate-review:` 留痕义务**。
13. **明确实现基线**：`f5e4c31` 还是 `fa2fc3d`（X7 两版措辞不同，见 §0.2）。

---

*评审性质：独立对抗式设计评审（设计未实现，无代码改动）*
*只读纪律：全程未执行任何写仓 git 命令；未编辑任何文件（本报告除外）；未切换分支；*
*所有探针在 `mktemp -d` 一次性副本内「建→用→清」同一 bash 调用完成；未跑全量 pytest。*
