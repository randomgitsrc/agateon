# TAG0050 G2 复审（第 2 轮整改后）进度留痕

- 起手：`rm -f docs/reviews/tag0050-g2-rereview-01.progress.md`（按 dispatch 要求）。
- 角色/范围：`review`；只核 B1/H1/M1/M2/L1/L2/L5/L3/L4/L6 闭合 + 新阻断。
- 环境：仓外可丢弃副本 `/tmp/opencode/G2rerev/`（rsync 排除 __pycache__/.pytest_cache，含 .git）。[PROD_NOT_TOUCHED]

## 已读
- `agate/assets/review-roles/review.md`、`P4-dispatch-context-review-G2-rereview.md`、`P0-brief.md`
- `P4-review-G2.md`（首轮）、`P4-review-cso-G2.md`（首轮）、`P4-dispatch-context-implementer-G2-fix2.md`、`P4-implementation-G2.md`、`P4-progress.md`
- 本次 diff：agate-md-field-get/set、pre-commit-gate、check-frontmatter、agate-config、level-1.yaml、markers.yaml、测试文件
- `helpers_tag0050.py` / `conftest.py`（构造非 legacy 任务夹具）

## 独立验证（命令 + 输出）

### B1（伪造 pass 值 → 现算）
```
$ FILE=…/scratch_b1/TAG0001/P6-acceptance.md AGATE_ROOT=…/agate python3 agate/scripts/agate-md-field-get.py pass
2        # 伪造文件值 999 被忽略，返回现算 2
$ … fail → 1
$ legacy 任务 → 999（旧行为保留）
$ 负向控制（禁用 derive 分支）→ 999（test_bdd_46 改前红）；恢复 RESTORED_OK
$ check-gate.py P6 …/scratch_b1/TAG0001 → GATE P6: FAIL=1, TOTAL=3；rc=1
```

### H1（非 P6 主产出照抄修复命令 → 转绿）
```
$ AGATE_ROOT=…/agate git commit -m "probe missing prod_touched"
GATE: 主产出 P4-implementation.md 缺 prod_touched 字段…修复命令: FILE=… agate-md-field-set.py set prod_touched false
      （若未触达生产…）        # 注解与命令分行
RC=1
$ FILE=… agate-md-field-set.py set prod_touched false → OK…rc=0
$ AGATE_ROOT=…/agate git commit -m "after fix" → GATE P4 (TAG0001): 通过；RC=0
```

### M1
```
$ set（无声明文件）→ rc=0 且 NOT_CREATED_OK
$ init→set→get=python→show 含 python→explain 当前值 python→unset→get 空→raw grep python=0
```

### M2 / L1 / L2 / L3 / L4 / L5 / L6
- M2：`P4-implementation-G2.md:164` DESIGN_GAP 显式登记待办；`grep traps|downgrade scripts/*.py` 零命中。
- L1：`check-frontmatter._declaration_files` 用 `task_level`（回退 current_level），与 pre-commit-gate 同口径。
- L2：结构面/时间面注释 + `P4-implementation-G2.md:159` 声明。
- L5：`test_l5_frontmatter_type_error_json_type_names` 断言「应为 integer」，实测通过。
- L3/L4/L6：`P4-implementation-G2.md:160/161/162` 显式声明。

## 回归面
- 焦点 3 文件 → 19 passed；pre_commit_hook → 62 passed。
- 全量 `-n auto --reruns 1`（CI 口径）→ 8 failed / 2725 passed / 3 skipped（8 = 登记预期红灯 BDD-43/59/60/63/66/69/71/76）。
- regression → 81 passed；consistency → 0 ERROR；count-tests → 2839；platform-assumptions → rc=0。
- 观察（非阻断）：首轮全量并行曾现一次 `test_it8` 失败，未复现（单跑/本文件并行/二次全量/CI 口径均绿）→ xdist 既有 flake。

## 新引入问题
- F-2/F-3（cso）随附闭合；F-3 真实卡片块 hash MATCH、P5/P8 卡片标记行不命中锚定正则（无假阳性）。
- 未发现新阻断。

## 产出
- `agate-workspace/tasks/TAG0050-task-data-contract/P4-review-rereview-G2.md`（status: approved）
- [PROD_NOT_TOUCHED]
