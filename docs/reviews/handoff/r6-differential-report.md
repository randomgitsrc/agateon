# R6 差分报告（裁决 §5.3 合并条件 3）

> **日期**：2026-10-03 ｜ **分支** `feat/gate-robustness-single-source`（未 push）
> **方式**：author 本机（peekview 被 gitignore 的证据只在那里）
> **对象**：两仓 **106** 个含 `P6-acceptance.md` 的任务

## 0. 先记我自己的两次测量错误（如实登记）

| # | 错误 | 后果 | 修正 |
|---|---|---|---|
| 1 | **基线不纯**：把**新版** `agate_common.py` 拷进 main 基线目录 | 结果无效（新旧实现混用） | 重取 `git show b8247ee:` 全部依赖 |
| 2 | **基线不全**：`/tmp/mainver` 缺 `agate-md-field-get.py` | `ui_affected` 读成空 ⇒ main **跳过整个截图检查块** ⇒ 假报 **8 个「新增变红」** | 补齐基线工具集，重跑 |

> 教训：**"改前/改后"对比里，"改前"那一侧必须是一个完整、可运行的环境**——
> 否则测出来的差异是脚手架缺陷，不是代码差异。这与我此前"按模式计数当结论"是同一类病。

## 1. 结果（干净基线）

| 脚本 | 相同 | 新增变红 | 新增变绿 |
|---|---|---|---|
| `check-p6-evidence.py` | 97 | **0** | 9 |
| `check-p6-provenance.py` | 95 | **2** | 9 |

## 2. 新增变红 2 条 —— 均为裁决 §3.2 **预测**的类别（真违规，非假红）

| 任务 | 引用 | 形态 | 归类 |
|---|---|---|---|
| `agateon/TAG0020-independent-judge` | `agate_common.py` | 括号里写**源码文件名** | ② 旧规则漏检的真违规 |
| `peekview/T078-read-tracking-hardening` | `example.com` | `_classify_source(example.com)` 的**函数参数** | ② 同上 |

裁决已明示：**不为它们加排除规则**（会误伤真证据组），登记为「可解释的新增拦截」，不回改历史任务。

## 3. 新增变绿 9 条 —— **解除假红**

`T029 / T030 / T032 / T033 / T039 / T040 / T045 / T046 / T073`（evidence）
`T075 / T076 / T080 / T081 / T084 / T085 / TPV0094 / TPV0099 / TPV0100`（provenance）

成因：旧规则取到行末括号（多为**散文**，如 T030 的 `(Escape closes, focus returns)`）却判"不存在"；
新规则下或解析成功、或不构成引用 ⇒ 不再误报。

## 4. 政策双路径实测

| P1 `created` | 判定 | 实测 |
|---|---|---|
| `2026-01-01`（< 截止） | 历史任务 | **WARNING，rc=0** ✅ |
| `2026-10-10`（≥ 截止） | 新任务 | **exit 1** ✅ |

## 5. 复现

```bash
# 干净基线（务必补齐依赖，否则跳过截图检查块）
mkdir -p /tmp/mainver
for f in check-p6-evidence.py check-p6-provenance.py check-judge-verdict.py \
         agate_common.py agate_markers.py agate-md-field-get.py agate-image-check.py; do
  git show b8247ee:agate/scripts/$f > /tmp/mainver/$f
done
git show b8247ee:agate/rules/markers.yaml > /tmp/mainver/markers.yaml

# 逐任务双向对比（两仓 106 个任务）
AGATE_ROOT=$PWD/agate python3 <对比脚本>   # 见本批 commit d76b3cd 描述
```
