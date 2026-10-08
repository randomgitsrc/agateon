# P1 gate 诊断 — TAG0050

> 主 Agent 亲自填写。触发：`check-gate.py P1 agate-workspace/tasks/TAG0050-task-data-contract` 返回 **rc=1**（预期 rc=2）。

## 现象

```
GATE P1 WARNING: 3 个 SUGGEST 项（主 Agent 可自行采纳，不阻塞）
GATE P1: 不合规的 NEED_CONFIRM 标记格式（须用行首 [NEED_CONFIRM]、[SUGGEST: ...] 或 [NO_NEED_CONFIRM] 声明）
rc=1
```

## 定位（机械判据）

`check-gate.py:742`：

```python
if "[NEED_CONFIRM]" in p1_text and nc_blocking == 0:
    sys.stderr.write("GATE P1: 不合规的 NEED_CONFIRM 标记格式…\n")
```

- `nc_blocking == 0` 为真（无行首 `[NEED_CONFIRM]`）——符合预期（本任务无阻塞项）。
- 但 `P1-requirements.md` **第 548 行**正文含**字面量** `` `[NEED_CONFIRM]` ``：
  `> 以上均为倾向项，不阻塞推进；**无未决 \`[NEED_CONFIRM]\`**。`
- 全文唯一命中：`grep -nF "[NEED_CONFIRM]"` → 仅 548 行。
- 第 542 行 `` `[NO_NEED_CONFIRM]` `` 被 gate 正常识别（RM-AG0001 反引号前缀口径），无告警。

## 结论

**非实质缺陷**：声明本身正确（§5 已写 `[NO_NEED_CONFIRM]`），仅**收尾散文里复述了带方括号的标记字面量**，被 gate 的「任意字面量命中」判据当成不合规标记。修法 = 把 548 行改写成不含 `[NEED_CONFIRM]` 字面量的等价表述（如「无未决阻塞项（NEED_CONFIRM = 0）」）。

## 处置

- **不改 P1 的 BDD 与声明语义**（评审已 approved，本次仅去歧义）⇒ 不触发 re-review。
- 由 analyst 重试修改（主 Agent 不写阶段产出）→ 重跑 `check-gate.py P1`。
- 不占用额外设计变更：属 gate 判定面与正文书写面的一处口径错位。

## 备注（供后续批次参考，不在本任务修复范围）

这是设计 §0 F5「否定写法被正则当成声明」的**同一族**现象（gate 用字面量扫描，判断不了散文语义）。本任务批 B/F 的绊线与结构化字段正是要收敛这类歧义——但本 P1 文件的措辞仍须当下改正。
