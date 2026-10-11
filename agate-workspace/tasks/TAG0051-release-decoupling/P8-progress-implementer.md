## P8 progress (implementer/releaser)
### 输入已读
- 角色文件 implementer.md / P8-dispatch-context-implementer.md ✓
- P2-design.md（packages 9 / gate_commands）/ P6-acceptance.md（23 PASS）/ P6.5-judge（23/23 passed）/ P7-consistency（blocker 0）✓
### 产出
- P8-release.md（新建）/ CHANGELOG.md [Unreleased] 新增 TAG0051 变更条目 / roadmap RM-AG0103 scheduled->done
### 自检
- check-changelog.py TAG0051 exit 0; roadmap NF!=9 计数 0; stable v0.81.0 check-gate.py P8 exit 2（仅 version/CHANGELOG 暂存区 WARNING）
- ④ verify.commands: consistency=0 / pytest=1(仅预存 test_bdd_43) / count=0(2961) / ruff=0
[PROD_NOT_TOUCHED]
