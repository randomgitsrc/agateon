# P7-progress — TAG0032 一致性交叉检查（consistency-reviewer）

- 读 dispatch-context + 角色定义 consistency-reviewer.md + AGENTS.md + P0-brief.md
- 读全部输入（P7 输入数量豁免）：P1-requirements / P2-design / P2-review / P4-implementation
  （批1 + 批2 + fix-1）/ P4-review（复评轮 approved）/ P5 unit.md / P6-acceptance / P6.5-judge-verdict
  / known-failures.md / CODE-MAP.md
- `git diff 3f3cc01..HEAD -- agate/ install.sh README.md README.zh-CN.md`：
  M README×2 / agate/SETUP.md / agate/UPGRADING.md / agate/scripts/agate-install.py /
  agate/scripts/agate_common.py / install.sh / 3 个既有测试文件；A 2 个新测试文件
  （test_version_lifecycle_e2e.py / test_upgrading_lifecycle.py）
- grep `^\[DESIGN_GAP` P4-implementation.md → 5 处（L55/L56/L57/L58 批1 四条 + L118 批2 一条），design_gap_count=5
- 逐条独立核对 DESIGN_GAP 裁决：读 agate_common.py / agate-install.py / install.sh 实际 diff +
  run_git 实现（返回 (rc, stdout) 不抛，fail-open 属实）+ UPGRADING.md diff + test_upgrading_lifecycle.py 断言
- 检查项 1 DESIGN_GAP 配对：5/5 转抄 + REVIEWED
- 检查项 2 SCOPE+：P1/P2/P4 无任何 SCOPE+ / SCOPE_RESOLVED 标记 → N/A
- 检查项 3 跨文件一致性 4 项：packages↔改动面 / P1 14 BDD↔P6 14 PASS↔P6.5 14/14 /
  P4 实现路径↔P2 决策 A1+B1 / 纯增量红线 —— 逐项结论 + 锚点
- 检查项 4 未决项清零：P1 无行首 [NEED_CONFIRM]/[BLOCKER]/[DEVIATION-CRITICAL]（§8 = [NO_NEED_CONFIRM]）
- 检查项 5 CODE-MAP 核对：2 个新增文件均为测试文件 → [CODE_MAP_SYNC:]（测试文件 CODE-MAP 豁免）
- 发现 1 处非关键偏差（deviation_count=1，非 critical）：UPGRADING.md「版本管理生命周期 › 根 scripts/
  维护语义」段仍描述 fix-1 已删除的 layer-1 双 copytree 机制（「运行中安装器自带 scripts/ 叠加 …
  后拷贝者胜」），而代码已回退 P2-design §3 B1 单源 copytree。用户可见承诺不受影响，建议 P8 修订该句。
- 写 P7-consistency.md（frontmatter 结构化计数 + 正文逐条 + 行首标记）→ status: approved

- check-gate.py P7 预跑 → EXIT=0；markers 计数 DESIGN_GAP 5 / DESIGN_GAP_REVIEWED 5 / CODE_MAP_SYNC 2；status: approved
- 完成，返回主 Agent
