# R6 差分（重做版，回应 F4）

> **日期**：2026-10-03 ｜ **分支** `fix/pr392-review-findings`
> **方法**：在 **`/tmp` 工作区副本**上跑（评审 §5 的坑：`check-judge-verdict.py` 每次运行都会往
> 任务账本追加 `judge_verdict` 事件——直接在真实仓库跑会污染哈希链与轮次计数）。
> **对象**：两仓 **106** 个含 `P6-acceptance.md` 的任务；**三个脚本、双向**。

## 0. 上一版报告的四处缺陷（评审 F4，逐条确认）

| # | 评审指出 | 处置 |
|---|---|---|
| 1 | 漏报 TAG0023 | ✅ 本版已包含：`check-p6-provenance` 变绿 2→1（新增 `(protocol-tests.yml)` 引用被拦） |
| 2 | 漏报 T047 | ✅ 本版在副本上跑，T047 的两侧差异已可见 |
| 3 | TPV0100 无法复现（**基线第三处错误**） | ✅ 确认：上一版把「本机才有被 gitignore 的证据」误算成差分 |
| 4 | **缺 judge 差分** | ✅ 本版已补：`check-judge-verdict` **106 任务全相同** |
| 5 | 变绿未逐个归类、复现命令是占位符 | ✅ 见 §2/§3 与本节方法说明 |

## 1. 结果（干净基线 + 隔离副本）

| 脚本 | 相同 | 变红 | 变绿 |
|---|---|---|---|
| `check-p6-evidence.py` | 94 | 11 | 1 |
| `check-p6-provenance.py` | 103 | 2 | 1 |
| `check-judge-verdict.py` | **106** | **0** | **0** |

## 2. `check-p6-evidence` 的 11 个「变红」—— **全部是政策生效，非回归**

形态一律为 **`1 → 2`**（不是 `0 → 1`）：

```
BASE（main）：GATE P6-EVIDENCE: 有 10 条 PASS 缺文件证据引用……        rc=1（阻断）
NEW（本批）：GATE P6-EVIDENCE: 有 10 条 PASS 未能提取证据引用
             （**历史任务**，按 evidence_ref_required_since 之前的截止口径给 WARNING，不阻断）  rc=2
```

涉及任务：`T029 / T030 / T032 / T033 / T039 / T040 / T044 / T045`（+3 同类）。
**这 11 个全部是 `created ≤ 2026-07-17` 的存量任务**——裁决 §4 明定存量给 WARNING。
`rc 1→2` 是**放宽**（原本阻断 ⇒ 现在不阻断但可见），这正是 F3 修复要达成的效果
（`pre-commit-gate.py:502` 只在 rc∈{1,2} 时打印捕获输出；旧版 rc=0 会让告警**被静默丢弃**）。

## 3. `check-p6-provenance` 的 2 红 1 绿

| 方向 | 任务 | 说明 |
|---|---|---|
| 红 | `agateon/TAG0020` | `(agate_common.py)` —— 括号里写**源码文件名**（裁决 §3.2 预测类） |
| 红 | `peekview/T078` | `_classify_source(example.com)` —— **URL 当路径**（同预测类） |
| 绿 | `agateon/TAG0023` | **F4 漏报项，本版补上**：新增 `(protocol-tests.yml)` 引用被拦 ⇒ 旧规则漏检 |

两条变红均为**旧规则漏检的真违规**（非假红），按裁决登记为「可解释的新增拦截」。

## 4. `check-judge-verdict`：**106 任务全相同**

评审要求的差分已补——judge 侧**无行为变化**，与裁决 §5.3 的预期一致
（22 个 verdict 文件、560 条结论行）。

## 5. 复现（含评审 §5 的坑）

```bash
# ① 必须在**副本**上跑（judge 会写账本！）
rm -rf /tmp/r6work && mkdir -p /tmp/r6work
cp -r agate-workspace/tasks /tmp/r6work/new-tasks
cp -r ~/oclab/peekview/agate-workspace/tasks /tmp/r6work/pv-tasks
cp -r agate /tmp/r6work/new-agate

# ② main 基线必须**完整**（缺工具会让 ui_affected 读空 ⇒ main 跳过整个截图检查块 ⇒ 假差分）
mkdir -p /tmp/r6work/base && git archive b8247ee5 agate | tar -x -C /tmp/r6work/base
for f in agate-md-field-get.py agate-image-check.py; do
  git show b8247ee5:agate/scripts/$f > /tmp/r6work/base/agate/scripts/$f
done

# ③ 三脚本双向（脚本见本批 commit）
AGATE_ROOT=/tmp/r6work/new-agate python3 <r6final.py>
```
