# 留痕 HOTFIX-DEBT0067-0068 (2026-10-11)

- 角色文件读取：`~/.agate/v0.81.0/agate/assets/review-roles/protocol-alignment-review.md`；dispatch-context：`/tmp/opencode/hotfix-0067-0068-review-context.md`。
- git status：4 M + 1 untracked test（branch hotfix/debt0067-0068-write-side）。
- diff 读取：phases.yaml(P1/P8 task_fields) / agate-frontmatter-check.py(+_DEPTH_EXEMPT_FIELDS) / agate-md-field-set.py(_STRUCTURED_SET_KEYS + writable ∪ JSON_FIELDS) / test_agate_md_field_set.py + 新 test_debt0067_0068_write_side.py。
- 读了：P2 卡 L115-151、P8 卡 L67-91、P1 卡 L68-131、task-files.md L133-207、SCHEMAS(frontmatter-check L39-133)、agate-md-field-get 字段集 L96-178、check-structure-consistency L414-459、check-protocol-consistency CHECK9 L573-792、adr.md ADR-014 L533-586、design-md-field-set.md L50-119/L300-339、DEBT0067/0068 条目 tech-debt L2770-2871、CHANGELOG [Unreleased] L11-51。
- [A3b] grep task_fields 代码消费方：agate-md-field-set.py(L103,257,465) + **check-structure-consistency.py S-4 L421**（allowed_fields 扩展面）⇒ 主 Agent「唯一消费方」声称不准确。
- [A3b] check-structure-consistency 无「task_fields ⊆ 快照」子集检查。
- [F4/实测] resolve_rules_root（无 AGATE_ROOT）→ stable `~/.agate/v0.81.0/agate/rules`；带 `AGATE_ROOT=$PWD/agate` → 工作树。测试经 conftest 隔离 HOME 迫使回退脚本路径 → 工作树（故测试有效）。
- [F4/实测] stable 引擎对 P2(dispatch_plan output 深4) 打出 `P2-design.md:dispatch_plan: 嵌套深度超过 3 层`；worktree 引擎不打（豁免生效）。负例：coupling_checklist 深4 在 worktree 仍报错（未放宽）。注意：直接调 `agate-frontmatter-check.py` 恒 rc=0（判定在 stdout 非空，由 check-frontmatter.py 薄壳判失败）——印证「rc=0 ≠ 通过」。
- [F1/实测] `set ceremony full` OK；但「剩余缺失」列出 8 个可选字段；`set coupling_checklist`/`internal_only`/`override` 仍报「非法 key」；错误信息「合法 key 清单」却包含 need_confirm_resolved/scope_resolved/suggest_resolved，而 `set`/`append` 这三者均拒写（追加/嵌套字段）。
- [F5/实测] `set delivery none` → 落盘 `delivery: none`，yaml 读回字符串 'none'（无误解析）；`set delivery {method:..., reason:...}` → 落盘块映射，读回 dict。
- [A4] 实跑 `pytest test_debt0067_0068_write_side.py test_agate_md_field_set.py -q` → **40 passed**。
- [A8] 实跑 `check-protocol-consistency.py` → 仅 433 WARNING（冻结历史文件），**0 ERROR**；`ruff check` 两脚本 → All checks passed。
- [F6] CHANGELOG [Unreleased] 未见 DEBT0067/0068 条目（近期 hotfix DEBT0065/0066 均有条目）。

## r2 增量复审 (2026-10-11 16:41:58)
- r2 diff 读取：phases.yaml(仅 P8 hunk，P1 已恢复) / agate-frontmatter-check.py(同 r1 豁免) / agate-md-field-set.py(+_schema_legal_keys 第三来源、_cmd_list 分区、_cmd_set 文案、_cmd_explain 来源分支) / P2 卡 +深度豁免段 / CHANGELOG +2 条 / design-md-field-set §2.3·§4·§5.3·§6.1 / 测试 +⑥⑦⑧。
- [A4] 实跑 49 passed（r1 40 → +9）。
- [A8] consistency 0 ERROR / ruff All checks passed（复跑）。
- [闭合实测] P1 --list：可填=4 必填；其它可 set 的 schema 合法字段=12；仅登记/需 append=3；set ceremony 不再报假缺失；7 个 P1 字段 7/7 set rc=0；未知 key 清单不再含三键；append-only 单独提示。
- [负例实测] coupling_checklist 深4 → check-frontmatter.py rc=1 报「嵌套深度超过 3 层」；dispatch_plan output 深4 → rc=0；未知 key → 非法 key rc=1。
- [P8 裁决核] SCHEMAS 无 P8-release.md（grep -c=0）；level-1 files 无 P8 ⇒ 恢复 task_fields 会使 set delivery 非法；delivery/debt_check 为 P8 必填（卡 :85-86）⇒ 报缺失语义正确。裁决依据成立。
- [A2 残余-新] P6 --list「其它可 set 的 schema 合法字段: regression_pass」但 set regression_pass → 「证据字段」拒绝（rc=1）⇒ swing 假宣称（r2 新增）。
- [A2 残余] set scope_resolved/need_confirm_resolved/suggest_resolved 统一提示「请改用 append 子命令」，但实测仅 scope_resolved 可 append（declaration_field）；need_confirm_resolved/suggest_resolved/mechanism_issues append 均 rc=1 ⇒ 4/5 假指引。explain scope_resolved 亦打印不可执行的 set 命令。

## r3 增量复审 (2026-10-11 17:05:32)
- r3 diff：agate-md-field-set.py(+_CAPABILITY/_LIST_GROUP/_ERROR_GROUP 标签 + _evidence_fields/_append_only_fields/_writable_set/_is_script_field/_append_spec/_key_capability/_relevant_keys；--list 与错误分组改由 _key_capability 派生；_cmd_set writable 改用 _writable_set)；测试 +⑨；design-md-field-set §5.3 新注；DEBT0072。
- [闭合实测] P1 --list：4 必填(可 set)+12「其它可 set」+ scope_resolved「需 append」+ need_confirm_resolved/suggest_resolved「仅登记不可写入」；P6 --list：pass/fail「脚本产出」+ ui_affected/p5_evidence_reuse「可 set」+ regression_pass「脚本产出」；P6 错误清单已不含 pass/fail/regression_pass。
- [逐类对拍] set scope_resolved 拒 / append scope_resolved OK；set regression_pass 拒（证据）；set override/ui_render_shape OK。逐键一致 ✔。
- [同源核] _key_capability 复用 _evidence_fields/_append_only_fields/_writable_set/_is_script_field/_append_spec（= _cmd_set/_cmd_append 同一判据），次序一致，无第二份。
- [A4] 实跑 51 passed（r2 49 +⑨ 2）。变异：副本去掉证据分支 → 守护测试 [P6] 1 failed（判别力证实）。
- [负例] unknown key 拒；coupling_checklist 深4 ERROR rc=1；dispatch_plan output 深4 rc=0。
- [A8] consistency 0 ERROR / ruff All checks passed（复跑）。
- [DEBT0072 核] append pass text=probe → OK（逐字一致）；append regression_pass 拒；append blocker_count(P7) OK ⇒ 面未穷尽吻合。登记如实。
