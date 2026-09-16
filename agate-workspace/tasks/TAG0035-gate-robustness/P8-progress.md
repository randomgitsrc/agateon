
## P8 releaser 完成记录（2026-09-16）

- 读取 P0-brief.md / P2-design.md / debt/tech-debt.md（DEBT0037/DEBT0038 全文）/ roadmap.md（RM-AG0062/RM-AG0064）/ CHANGELOG.md / agate/UPGRADING.md / P4-implementation{,-B,-C,-D}.md / P6-acceptance.md / P1-requirements.md（14 条 BDD 标题核实性质）
- bump_type 判定：patch（v0.71.0 → v0.71.1）——14 条 BDD 逐条核实均为判据修复，无新增功能
- debt_check：DEBT0037 4 条 closure_criteria 逐条核对（3 条直接满足，1 条"设计推导+退出码契约验证"满足，如实标注非直接 agate-next.py CLI 集成测试）；DEBT0038 4 条 closure_criteria 全部直接满足；结论建议两条均可 closed
- CHANGELOG/README badge（行号+旧新值）/roadmap 确认/UPGRADING 草稿/临时资源清单（无）/P5 复用确认+per-package 命令说明（协议本体单包，无独立命令）均已写入 P8-release.md
- Lessons Learned 3 条已写入
- frontmatter 字段用 agate-md-field-set 逐个写入（phase/task_id/parent/trace_id/type/created/status/bump_type），agent/debt_check 两字段该工具白名单不含（非 phases.yaml P8 task_fields、非 GENERIC_HEADER_KEYS 可写集合），手工写入 frontmatter，check-frontmatter.py 校验 exit 0
- 产出文件：agate-workspace/tasks/TAG0035-gate-robustness/P8-release.md
