[09:43:51Z] 读 dispatch-context + review-role；评审对象=分支 hotfix/debt0069-release-preset-consumer 未提交 diff（4 文件）
[读] git status: M agate/UPGRADING.md / agate/scripts/agate-release.py / tests/unit/test_agate_config.py / test_release_gate.py；分支 head=1a707fc1
[读] agate/rules/schema/project-config.schema.json:43-55 → release.preset 有 enum=["semver-changelog-tag"]（非任意字符串）
[读] agate/scripts/agate_schema.py:103-104 → iter_errors 实现并判定 enum（code=enum）
[读] agate-config.py:342-153 validate 走 _validate_node→agate_schema.iter_errors（enum 生效）
[读] agate_common.py:915-960 PROJECT_CONFIG_DEFAULTS.release.preset=semver-changelog-tag；read_project_config 深拷贝打底+顶层浅合并
[读] agate-release.py:64-67 KNOWN_RELEASE_PRESETS + _DEFAULT_RELEASE_PRESET 两处硬编码；:464-490 _project_release_preset；:520-527 门内调用
[读] agate/tests/unit/test_config_schema.py:112 test_bdd_5_validate_rejects_illegal_enum_value（非法 preset→validate 非 0 已是既有契约）
[探针] /tmp/opencode/d69probe：validate preset=bogus-preset → rc=1，报「不在允许枚举 ['semver-changelog-tag']」；preset=known → rc=0
[探针] /tmp/opencode/d69gate（临时 git 仓）：gate known→rc0+回显；unknown→rc1(错误含名)；缺键→rc0；显式 null→rc0(「未声明，按默认」)——四条行为独立复现
[探针] /tmp/opencode/d69sch：删 schema preset 属性后 agate_schema.validate 报「未知字段 preset（additionalProperties=false）」→ UPGRADING 删键破坏性声称成立
[跑] pytest test_release_gate.py+test_agate_config.py → 27 passed；再跑 config_schema/tag0051_p8_gate/gate_layer/agate_release/release_workflow → 89 passed（无既有用例转红）
[读] agate/scripts/README.md:149 agate-release.py 索引行「发布门：CI success + consistency 0 ERROR + check-gate.py P8」——未含新增 preset 消费（A2 陈旧）
[读] CHANGELOG.md [Unreleased]「修复」节逐条含 DEBT0065/0066/0067/0068 → DEBT0069 缺条目（A5）；[Unreleased]「变更」TAG0051 条目列举发布门但未含 preset
[读] agate/adr.md:533-585 ADR-014①判据必须单源；:589-659 ADR-015「判据分叉=实质必拦」
[读] git grep HEAD agate/scripts preset → 仅 agate_common.py:919 + agate-config.py:49（均非读值）→「此前无值消费方」声称成立
[判] 重点裁决：unknown preset fail-closed 恰当（schema enum 已使其非法，无新破坏）；MISALIGNED=3 (A2/A3b/A5)；A7=NEEDS_HUMAN_REVIEW
[09:43:51Z] 留痕完成

===== H2-r2 增量复审（10:08:42Z）=====
[读] diff：新增 _known_release_presets()（:474 起，从 schema enum 派生）；删 KNOWN_RELEASE_PRESETS/_DEFAULT_RELEASE_PRESET；README:149、CHANGELOG:64-69 已补
[grep] agate/**/*.py 内 KNOWN_RELEASE_PRESETS/_DEFAULT_RELEASE_PRESET 零残留；semver-changelog-tag 代码字面仅剩 schema(权威)+agate_common:919+agate-config:49(既有默认/init)+agate-release docstring
[跑] pytest test_release_gate.py+test_agate_config.py → 29 passed（r1 为 27，+2 单源测试）
[跑] config_schema/tag0051_p8_gate/gate_layer/agate_release/release_workflow/doc_sweep → 102 passed
[探针 d69r2/d69r3] A) schema 缺失→rc1+明确路径；B) 非法 JSON→rc1；C) enum=[]→rc1「应为非空字符串数组」；D) 隔离根 enum 加 custom-flow→门 rc0+回显（真随 schema 变）
[探针 d69r3] 工作树脚本：known→rc0；unknown→rc1(含名)；absent→rc0；validate(known)→rc0；_known_release_presets()==('semver-changelog-tag',)
[读] _schema_path 基于 __file__ 相对（scripts/../rules/schema），不依赖 AGATE_ROOT → 隔离根走工作树 schema（实测）
[跑] check-protocol-consistency.py --strict-errors-only → 0 ERROR（433 frozen WARNING，CHECK10-scriptref 1 条属 frozen 历史文件，非本次改动面）
[判] A2/A3b/A5/A7 均真闭合；无新破坏；MISALIGNED=0 → approved
