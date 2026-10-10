---
review_date: 2026-10-09
reviewer: protocol-alignment-review
change_summary: RM-AG0113 r3 复核——核实 r2 的 3 处残留（state-transitions.md:93 自相矛盾 / DEBT0041 尾部陈旧段 / roadmap _md_field 引用）+ 新分叉（check-routing 未随 _p1_field）+ fm 非 dict 分叉的处置
files_changed: [CHANGELOG.md, agate-workspace/debt/tech-debt.md, agate-workspace/roadmap/roadmap.md, agate/rules/state-transitions.md, agate/scripts/check-pruning.py, agate/scripts/check-routing.py, agate/scripts/check-state-transition.py, agate/tests/unit/test_agate_md_field_set.py, agate/tests/unit/test_check_pruning.py]
---

# 协议-脚本对齐审查（r3）

> 批次：批 A2 / RM-AG0113（分支 `hotfix/batch-a2-single-source`，未提交；`git diff` **9 文件** + 留痕文件）。
> 前轮：r1 `...-SINGLE.md`、r2 `...-SINGLE-r2.md`。只读审查，未改任何协议/脚本/测试，未 commit/push；scratch 在 `/tmp/opencode/a2r3`。

## 审查结论汇总

| # | 审查项 | r3 结论 |
|---|--------|---------|
| A1 | 文档→脚本对齐 | **ALIGNED**（`state-transitions.md:93` 已改为「同代码路径」口径，与 `:91` 一致，无「不用正文正则」残留） |
| A2 | 脚本→文档对齐 | **ALIGNED**（`roadmap` 改 `_p1_field`；`CHANGELOG` 改「同代码路径」） |
| A3 | 一致性连锁 + 反向传播 | **ALIGNED**（`check-routing.py` 已同源复用 `check-pruning._p1_field`；反向传播清单无剩余缺口） |
| A4 | 测试覆盖 | **ALIGNED**（3 处口径逐例一致；判别力用例仍成立；全量 `-n auto` = **2909 passed / 1 failed(环境性) / 2 skipped**） |
| A4b | **闭合后既有测试转红 + 夹具更新清单** | **空清单**（实测无既有用例转红；diff 9 文件，无既有夹具改动） |
| A5 | 下游影响 + 文档传播 | **ALIGNED**（CHANGELOG/roadmap/debt 均随改；存量 43 任务全 legacy ⇒ 零影响） |
| A6 | 锚点表覆盖 | **ALIGNED** |
| A7 | 设计原则一致性 | **ALIGNED**（ADR-014 判据单源：三处 `phases` 读取现收敛到同一对函数） |
| A8 | 声称-命令绑定 | **ALIGNED**（`0 ERROR`/`145 passed`/`2909 passed`/`check-debt rc=0`/`roadmap 0 异常`/`ruff` 逐条可复现；`2909 passed` 伴 1 环境性 failed，**非「全绿」**） |

**是否可 commit**：**可 commit（唯一人裁项见下；批次已按协议变更程序显式留痕）**。

---

## 5 项改正逐条核实

| # | 改正 | 证据 | 结论 |
|---|------|------|------|
| 1 | `state-transitions.md:93` 括注与新 `:91` 自相矛盾 | `:93` 现为「`declared` 读法与 `check-pruning.py::_p1_field` **同代码路径**：frontmatter 结构化值优先，**缺失时**回退 `agate_common.body_field_value`…**M-1 读法修订见上**；`pruned` 恒为 frontmatter 结构化字段」；`grep 不用正文正则` **零命中** | ✅ 已修，同节一致 |
| 2 | `tech-debt.md` DEBT0041 yaml 外陈旧段 | 段首改「⚠️ 本段后经 2026-10-09 二次复核，结论已再变——见段末」；段末追加「推翻本段②…本债已关单…本段保留为历史留痕」；`grep 本债仍 open` **零命中** | ✅ 已修（② 原文保留但已显式标注被推翻，属历史留痕） |
| 3 | `roadmap` 的 `_md_field` 引用陈旧 | `roadmap.md` RM-AG0113 done 注改「与 `check-pruning.py` 恒检的 **`_p1_field`** **同代码路径**」；`CHANGELOG.md:113` 改「同代码路径：`check-pruning._p1_field` 与 `check-state-transition` 均用 `fm_field_value` 优先、缺失时回退 `body_field_value`」 | ✅ 已修 |
| 4 | 新分叉 `check-routing.py:113` | `check-routing.py:58` 新增 `_p1_field = _check_pruning._p1_field`；`:116` `phases = _p1_field(_read_p1(p1_file), "phases").split()`；`ceremony`（`:83`）**保留** `_md_field` | ✅ 已修（同源复用，无重复赋值） |
| 5 | `_p1_field` fm 非 dict 仍分叉 | `check-pruning.py:108-112`：`if not isinstance(fm, dict): return ""`（与 `check-state-transition` 的 fail-closed 对齐） | ✅ 已修（见下 P/S 实测） |

## 口径逐例一致（三处：check-pruning / check-state-transition / check-routing）

`/tmp/opencode/a2r3/cmp3way.py`（真函数，含 r1/r2 全部反例）：

| 输入 | prune `_p1_field` | cst `declared` | routing `_p1_field` | 一致 |
|------|------|------|------|:--:|
| A fm list / B fm 串 / C 正文内联 / D 正文块式 / E 两者都有(fm 胜) / F 都无 / G 引号 / I fm=null+正文 / O 正文 | 同 | 同 | 同 | ✅ |
| **H** fm 注释 `# phases: [P1, P2]` | `∅` | `∅` | `∅` | ✅ |
| **N** fm 未知键 `pruned_phases: [P1, P2]` | `∅` | `∅` | `∅` | ✅ |
| **Q** fm 串值 `note: "see phases: [P9]"` | `∅` | `∅` | `∅` | ✅ |
| **R** fm `phases: 3`（int） | `{"3"}` | `{"3"}` | `{"3"}` | ✅ |
| **P** 坏 YAML + 正文 phases | `∅` | `None`→有效 `∅` | `∅` | ✅ |
| **S** 无 frontmatter + 正文 phases | `∅` | `None`→有效 `∅` | `∅` | ✅ |

**16/16 一致**（有效 `declared` 集相同）。r1/r2 的 6 个反例（H/N/Q/R/P/S）**全部收口**。
**微差（非阻断）**：fm 非 dict 时 cst 返回 `None`（fail-closed 哨兵），prune/routing 返回 `∅`——调用方 `declared or set()` 映射为同一有效值，**判据结论一致**。

## check-routing 回归核查

- 同源复用未破坏 `ceremony`：`ceremony` 仍走 `_md_field`（`:83`），`phases` 改走 `_p1_field`（`:116`）。
- 实跑 `test_check_routing.py` + `test_check_pruning.py` + `test_check_state_transition.py` + `test_agate_md_field_set.py` = **145 passed**（含 check-routing 全部 ceremony 用例）；全量 = **2909 passed / 1 failed(环境性) / 2 skipped**。⇒ **无回归**。

## DEBT0041 段内自相矛盾核查

- yaml `status: closed` + `closed_at` + `closure_note`（判据①②③）；yaml 外段首已标注「结论已再变」、段末「推翻本段②…本债已关单…本段保留为历史留痕」；`本债仍 open` **零命中**。⇒ **无自相矛盾**（② 原文作为历史留痕保留，已显式标注被推翻）。
- `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` → **rc=0**。

## A8 声称-命令绑定

| 声称 | 命令 | 结论 |
|------|------|------|
| `0 ERROR` | `python3 agate/scripts/check-protocol-consistency.py` | ✅ rc=0（仅 429 冻结 WARNING） |
| `145 passed` | `pytest test_check_routing test_check_pruning test_check_state_transition test_agate_md_field_set -n auto -q` | ✅ 145 passed |
| `2909 passed` | `python3 -m pytest agate/tests -n auto -q` | ✅ **2909 passed**，伴 `1 failed`（环境性 `test_bdd_43`）+`2 skipped` ⇒ **非「全绿」** |
| `check-debt rc=0` | `python3 agate/scripts/check-debt.py agate-workspace/debt/tech-debt.md` | ✅ rc=0 |
| `roadmap 0 异常` | 复刻 `_ROADMAP_EXPECTED_COLS=9` 扫 `^\|\s*RM-` | ✅ 111 行，malformed=0 |
| `ruff` | `~/.venvs/agate-dev/bin/ruff check <5 文件>` | ✅ All checks passed |
| 判别力用例（旧红/新绿、变异锁定） | HEAD 版变异 + `- {'agent'}` 变异 | ✅（r2 已复现，r3 未变） |

---

## 剩余人裁项

1. **M-1 窄解读**（唯一）：`check-state-transition.py` docstring 与 `state-transitions.md:91` 均称「**M-1 禁止的是『用 `^phases:\s*\[` 正则匹配正文』这一写法，非『读正文』本身**」。这是对 M-1 的**窄解读**（依据 M-1 hotfix 写入的 docstring 措辞）；而 M-1 的**宽记录**（commit `7430b905` 信息 / `state-transitions.md` 原文）为「读结构化 frontmatter，不用正文正则」。批次已把该解读**显式化并留痕**（协议文档 + docstring + CHANGELOG，且 `:93` 已同步）——**已按协议变更程序落盘**。属**设计口径裁定**，交人工确认：若认可，无需再改；若不认可，应回退为 frontmatter-only 并重走 RM-AG0113。

> 说明：该项是「解读正确性」的判断，不是文档/代码不一致（二者已一致）。批次未隐藏、已如实标注为「读法修订」，符合留痕要求。

## 是否可 commit

**可 commit。** r2 的 3 处残留 + 1 处新分叉 + fm 非 dict 分叉**全部收口**；A1-A8 全 ALIGNED、A4b 空清单、A8 逐条可复现（1 条环境性 failed，不构成「全绿」误述）。

- **条件**：唯一人裁项（M-1 窄解读）建议人工确认；批次已将其作为「读法修订」在 `agate/rules/state-transitions.md` 显式留痕——若人工无异议，可直接 commit。
- **非阻断微项（可选）**：`check-pruning.py:99` `_p1_field` docstring「两处共用同一对函数 ⇒ **结论必一致**」——fm 非 dict 时 cst 返回 `None`、prune 返回 `∅`（有效值同，类型不同），措辞可加「（有效 `declared` 一致）」；`check-pruning.py:181` 区仍多一个空行（ruff 不报）。

---

## 附：只读与复现纪律

- 全程只读；仅写入本报告与 `docs/reviews/agate-alignment-2026-10-09-A2-0113-SINGLE-03.progress.md`。
- scratch 均在 `/tmp/opencode/a2r3`（三处口径逐例对比 `cmp3way.py`）；跑测试前后 `git status --porcelain` 一致（9 个已改文件 + 前轮留痕文件）。
