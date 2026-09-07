
## P1 requirements-review progress (2026-09-07)
- [step] 读完 dispatch-context 派发指引 + requirements-review.md 角色定义 + P1 阶段卡片全文。本任务非 frontend（domains=[backend,cli]），跳过 UI/UX 机制与 vision 能力检查。审声明特别说明：P1 暂存区无非 md/yaml 改动，改为核对 risk_level/ceremony/phases/implicit_coupling 与 P0-brief scope + P1 §1/§4 改动性质是否匹配。
- [step] 读完 P1-requirements.md（294 行，14 条 BDD）+ P0-brief.md（scope 三段 / out-of-scope 四项 / known_risks 四条）+ P1-progress.md（analyst 12 步留痕）+ .state.yaml（phase=P1，judge.enabled=true）+ HANDOFF-TAG0032.md（双工作区纪律 + 隔离 HOME 纪律 + 三断点实测证据）。
- [step] 代码核对 resolve-entry.py:49 = `gate_path = os.path.join(root, "scripts", gate_py)` —— BDD-8 命中点属实（文件 68 行）。
- [step] 代码核对 agate-install.py:134 = `os.makedirs(agate_home, exist_ok=True)`（_ensure_repo 内）—— §4 扫描 1 软链穿透源属实；全文 arg 解析仅 --help/--uninstall/无参/版本号，无 --versions 模式（BDD-5 待补属实）。
- [step] 代码核对 agate_common.py:166 `_resolve_version_info`：.agate-version 分支（L183）返回 `version=declared`（已是 vX.Y.Z，root 改 vdir/agate 不影响）；current 指针链分支（L190）返回 `version=os.path.basename(cur)`（root 改 vdir/agate 会回归成 "agate"）—— I-1 风险识别方向正确，BDD-6 锁 AGATE_VERSION 不回归对应。resolve_rules_root（L677）= `os.path.join(root, "rules")` 属实。
- [step] 实跑 `check-protocol-consistency.py --strict-errors-only` → EXIT=0，329 WARNING / 0 ERROR（基线已 0 ERROR）。发现：BDD-12 的「0 ERROR」子判据在基线已恒真，只是回归防护，不验证 doc/reality 矛盾（UPGRADING.md L546 表格声称 ~/.agate 根含 scripts/）是否真收敛 → BDD-12 二值判定弱，需补可枚举判据。
- [step] 核对 UPGRADING.md L546 表格「~/.agate/ = 版本管理根目录：... + scripts/（版本管理工具）」—— I-4 声称的 doc/reality mismatch 属实（文档承诺根 scripts/，install 未实现）。
- [step] 审声明核对：risk_level=high（改 3 核心解析脚本 + 5 文档面 + 新增测试，resolve 返回值语义牵动 ~10 消费方）匹配；ceremony=standard（未薄化，fail-closed 默认）匹配；phases=[P1..P8] §6 逐阶段理由、不裁任何阶段匹配；implicit_coupling=true（多消费方 + 文档多文件交叉）匹配 P7 不可裁理由。声明与改动性质一致 → 非 rejected 触发。
- [step] 结论 needs-revision：3 项需修 —— (1) BDD-12 机械判据弱（0 ERROR 基线恒真，未锁 doc 矛盾收敛）；(2) BDD-2 「建目录根 / 装版本」仅「可定位关键点」，判据松于「备份软链」的命令片段级；(3) I-3（根 scripts 副本 vs 软链维护语义须单测锁定 + 写 UPGRADING）无 BDD 绑定，BDD-4 只验入口命令可执行、BDD-11 未含该维护语义。次要（不阻塞）：BDD-7 未对称锁 AGATE_VERSION；BDD-13 「每一步 exit 符合预期」未逐步枚举；§4 行号轻微漂移（:551→L546）。

## 复评轮（re-review-1）— 2026-09-07 — trace_id: TAG0032-P1review-re1-20260907

**结论：approved**（原地覆盖 P1-review.md）

3 项必修逐条核对：
- 必修 1（BDD-12 机械判据恒真）：PASS — 重写为 4 条「已收敛到新口径 / 已标注为版本历史叙事保留」二选一无第三态 checklist，锚定 UPGRADING L551（根含 scripts/ 承诺）、L552（升级入口）、v0.60-0.62 vs v0.66-0.68（hook 重装口径分歧）、README×2+SETUP L244；check-protocol-consistency 0 ERROR 明确降为「附加回归项（非主判据）」。复评实跑：EXIT=0 / 329 WARNING / 0 ERROR，基线属实。单一 Given/When/Then 外壳保留。
- 必修 2（I-3 无 BDD 绑定）：PASS — BDD-4 判据 2/3（单测锁定所选建立方式维护语义 + 与 UPGRADING 一致）+ BDD-11 判据 3（写入生命周期节维护语义条目）交叉锁；§2 I-3 行补「对应 BDD」列；二值可判（grep 用例 / grep 文档条目）；P1 未越界决策副本/软链（均写「随 P2-design 选定」）。
- 必修 3（BDD-2 判据宽严不一）：PASS — 建目录根（mkdir -p ~/.agate）、装版本（agate-install.py + latest/v<X.Y.Z>/--versions）均收敛到命令片段级，与备份软链同粒度；Then 明确「每项判据同粒度，不留裁量」，三者缺一即 FAIL 可机械 grep。

回归确认：
- BDD-1..14 连续、#### BDD-NN: 格式合规（grep 实测 14 条）。
- 改动仅落 §3（BDD-2/4/7/11/12/13）+ §2 I-3 行 + §4 扫描 4 行号；frontmatter 未动；§1/§5/§6/§7/§8 未动。
- 首轮已确认合规项（同类扫描四类、纯增量红线 BDD-7 探测顺序、时效性质疑、范围锁定 out-of-scope）无误伤。
- 建议项 3 项全采纳（BDD-7 补 AGATE_VERSION、BDD-13 逐步枚举 exit、§4 行号校正），均收紧/校正无副作用。
- 无新增断点、无悄悄扩范围。

审声明复核：frontmatter 未改，7 项声明与改动性质仍一致，ceremony: full P7 逐信号核对不适用（standard，P7 走 implicit_coupling），rejection 触发未命中。

check-frontmatter P1-requirements.md：EXIT=0。
[PROD_NOT_TOUCHED]
