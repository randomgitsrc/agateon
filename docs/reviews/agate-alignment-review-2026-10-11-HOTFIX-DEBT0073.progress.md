# 留痕 — HOTFIX-DEBT0073 协议-脚本对齐审查（原始痕迹，不整理）

- [角色文件] /home/kity/.agate/v0.82.0/.../protocol-alignment-review.md — A1-A8(+A4b) 清单、只读纪律、BDD-8 写前检查。
- [git status] 初始只显示 2 文件（SELF-GATE.md / test_tag0051_self_gate.py）；复跑后为 4 文件（+ CHANGELOG.md / agate-workspace/debt/tech-debt.md）→ 主 Agent 在旁补关单件，diff 在演进。
- [git rev-parse] HEAD == origin/main == ba9438a1 ⇒ 本批全部为未提交工作树改动（`origin/main..HEAD` 为空）。
- [git diff] SELF-GATE.md: +3 行（CI 判据与轻量档同口径 + 指 DEBT0073）。test 文件：导入 hook 正则、`_bdd_22_violations` 接受 skip、+4 用例 +1 守护用例（5 样例参数化）。CHANGELOG.md: +9 行 DEBT0073 修复条目。tech-debt.md: status closed + 关单证据 + closure_note。
- [读 hook] agate/scripts/commit-msg-self-gate.py：`_SKIP_RE=^self-gate-skip:\s*\S+`(L43, MULTILINE)、`_REVIEW_RE=^self-gate-review:[ \t]*(.+)$`(L46)；`_check_review_path`(L112-140) 只对 `_is_report_reference` 的 token 判存在；main：skip 命中即 return(L170-171)、review 命中才查路径(L172-175)、否则 WARNING(L177-183)。import 期仅 try/except 降级 run_git（无副作用、不改正则）。
- [读 helpers] load_project_module(L772-789)：脚本缺失 raise ModuleNotFoundError；把 scripts_dir 插 sys.path；exec 模块。判据模块级导入 hook → hook 缺失=整文件收集失败（B 类红，可接受）。
- [读 judge] test_tag0051_self_gate.py：L39-40 `_REVIEW_RE=_HOOK._REVIEW_RE` / `_SKIP_RE=_HOOK._SKIP_RE`；grep 确认文件内无第二份 review/skip 正则字面量（只剩 `_TRIGGER_RE` L26-29 独立字面量=触发面，不在本批口径面内）。
- [commit 历史] `git show origin/main:test_tag0051_self_gate.py` grep：base 只有 `_REVIEW_RE`（L23），**无** `_SKIP_RE` ⇒ 注释「判据曾用只含空格/制表的写法」不符 base（base 是「无 skip 分支=拒所有 skip」）；该注释实指未提交的 r1 迭代。
- [实测] `pytest agate/tests/unit/test_tag0051_self_gate.py -q` → **15 passed**。
- [实测] `ruff check agate/` → **All checks passed!**
- [实测] `check-protocol-consistency.py` → **0 ERROR，433 冻结 WARNING**（未增）。
- [实跑探针 /tmp/opencode，同调用内建→清] 导入 hook+judge，`_REVIEW_RE is` → True；`_SKIP_RE is` → True。合成仓对拍（judge `_bdd_22_violations` vs hook 子进程）：
  - 5 样例（同行理由/冒号后空/纯空格/换行接理由/换行接非空行）→ 逐个 agree ✓（与主 Agent 结论一致）。
  - **分叉 1**：`self-gate-skip: 有理由\n\nself-gate-review: agate/scripts/ghost_probe.py` → judge=拒绝、hook=接受（judge 先查 review 路径；hook 见 skip 即 return）。
  - **分叉 2**：`prefix self-gate-review: ...`（非行首）→ judge=接受、hook=拒绝（judge 用子串判定触发 review 分支，`_REVIEW_RE.findall` 无命中⇒missing=[]⇒放行）。
  - **分叉 3**：行首 `self-gate-review: agate/scripts/ghost_probe.py`（非 reviews/ 报告路径）→ judge=拒绝、hook=接受（hook `_is_report_reference` 排除非报告 token）。
  - ⇒ 「接受集与 hook 逐个一致 / 分叉数 0（全局）/ 结构上不可分叉」被证伪；3 分叉均源于**周围逻辑**差异（非正则），且为**既有**（base 同样存在），本批未引入、但本批声称已消除。
- [路径核对] `.githooks/commit-msg-self-gate.sh` **不存在**（`.githooks/` 只有 `pre-commit-local`）；真实文件 `agate/scripts/commit-msg-self-gate.sh`(+.py)。该错路径出现在 CHANGELOG:15、tech-debt:3172、test 注释 L264。
- [A5 传播 grep] AGENTS.md:134 已正确（两留痕皆接受）；SELF-GATE.md:9/46 已正确；docs/guides/worktree-dogfooding-guide.md 三处只提 `self-gate-review:`（未提 skip，pre-existing，非本批引入）。
- [ADR] ADR-014(L533-585)：判据单源；L581「声明单源 ≠ 已经单源…必须与既有实现逐条对账并加等价回归守护」。ADR-015(L620-659)：判据分叉=实质必拦；措辞过期/错路径=非实质不拦。
- [BDD-8 写前检查] `docs/reviews/` 无同名 `*HOTFIX-DEBT0073*` 报告 ⇒ 直接新建。

--- r2 增量复审 ---
- [① 闭合核验] `grep -rn "\.githooks/commit-msg-self-gate" CHANGELOG.md agate/tests agate-workspace/debt` → **空**。三处（CHANGELOG / test 注释 / tech-debt evidence ref）均已改为 `agate/scripts/commit-msg-self-gate.py`。全仓仅剩本审查的报告（记录）。① 闭合 ✓。
- [② 闭合核验] CHANGELOG 现「正则定义真单源」+ 5 组样例 + 「不构成穷尽证明 + 另有 2 处既有差异」；SELF-GATE.md 同；test 注释/docstring 同。但 `tech-debt.md` closure_note 仍「接受集**真单源**…分叉样例 0」——未随其余四处收窄 ⇒ A5 传播缺口。
- [③ 自跑探针 /tmp/opencode 同调用建→清] `_SKIP_RE is`/`_REVIEW_RE is` = True。6 场景对拍：
  - C1 skip+幽灵review → judge 拒 / hook 接 → 分叉（judge 更严）
  - C2 非行首 review → judge 接 / hook 拒 → 分叉（hook 更严）
  - C3 非 reviews/ **真实文件** → 接/接 → 一致（= 你方条件）
  - C3' 非 reviews/ **不存在**路径 → judge 拒 / hook 接 → **分叉（第 3 类）**
  - C4 reviews/ 真实报告 → 接/接；C5 reviews/ 幽灵报告 → 拒/拒
  ⇒ 我 r1 第 3 条的**标签不精确**（不是"非 reviews/ 路径"本身，而是"路径不存在且 hook 不视其为报告指向"）；你方「真实文件 → 一致」成立，但「不存在 → 仍分叉」。⇒ 残留差异实为 **3 类**，docs「2 处」应更正。
- [复跑验证] `pytest agate/tests/unit/test_tag0051_self_gate.py -q` → 15 passed；`ruff check agate/` → All checks passed；consistency → 0 ERROR / 433 WARNING。
- [r2 结论] ①② 主体闭合（4/5 处）；残留 A5（tech-debt closure_note 未收窄）+ A8（计数 2→3、test 注释 ③「未复现」不精确）。⇒ needs-revision（文字层，一行级；实现/测试无需改）。

--- r3 最终确认 ---
- [① 核] `tech-debt.md:3220-3225` closure_note 已收窄为「**正则定义**已真单源（is 同一对象）+ 5 组样例一致 + 负例仍全判违规 ⇒ 成因消除」+「⚠️ 如实限定：接受集尚未逐例一致，另有 **3 类**既有差异另立 DEBT0075」✓
- [② 核] 三处「2 处」→「3 类」：`CHANGELOG.md:24`、`SELF-GATE.md:13`、`test_tag0051_self_gate.py:342`，第 ③ 类含「不存在且非 reviews/」+「真实存在则一致」对照 ✓；残留强声称 grep（逐个一致/结构上不可分叉/接受集真单源/结构上不再可能）改动面无命中；错路径限定面 grep 空 ✓
- [③ 核] `## DEBT0075` 新增：open/medium，3 类逐例复现（方向：①③ 判据更严、② hook 更严）+「此前误作 2 处已更正」+ recommendation (a)/(b) + 两条 closure_criteria ✓
- [计数] `grep -c '^## DEBT'`=75、`grep -c '^status: open'`=1（唯一 open=DEBT0075）✓
- [实测] `check-debt.py agate-workspace/debt/tech-debt.md` rc=0；consistency 0 ERROR/433 WARNING；pytest 15 passed；ruff All checks passed ✓
- [自更正] 我 r1 第 3 条标签不精确（应为「不存在且非 reviews/」而非「非 reviews/」）；r3 已在产出文件更正 ✓
- [r3 结论] 全部据实闭合 ⇒ approved（MISALIGNED 0）。本批未引入放松、正则真单源、残差 3 类属既有并另立 DEBT0075。
