# P4-progress — TAG0032 批 1（scripts-tests）

## 已读输入
- implementer.md 角色定义
- P4-dispatch-context-implementer-batch1.md（M1-M6 落点表 + 转绿目标 + 约束）
- P2-design.md（§1.1 M 表 / §2 候选 A1 / §3 候选 B1 / §4.1 fail-closed 文案 / §4.2 install.sh --versions / §6 gate_commands / §7 files_to_read）
- 代码片段：agate-install.py（imports / _agate_home / _ensure_repo / _install_version / _cmd_install / main / _usage）
- agate_common.py L120-239（_resolve_pointer_chain / _resolve_version_info / resolve_hook_root）
- install.sh 全文（55 行）
- resolve-entry.py:30-59（gate_path 拼接）
- agate-resolve.py 全文（AGATE_ROOT/AGATE_VERSION 输出契约）
- 测试：test_agate_version_install.py（tag0032 bdd_1..5 + _tag_upstream）/ test_agate_version_resolve.py（tag0032 bdd_6/7 + _make_home_meta/_make_home_rootproto）/ test_hook_resolve_entry.py（tag0032 bdd_8）/ test_version_lifecycle_e2e.py（bdd_13/14 + _tag_meta_upstream）
- conftest.py（_run_cli_impl / CommandResult.output=stdout+stderr / bash / py_path fixture）

## 关键发现（影响实现，已判定）
1. [DESIGN_GAP] `_tag_upstream` / `_tag_meta_upstream` fixture 的 `agate/scripts/` 均**不含 agate-install.py**，
   但 bdd_3/4/4b/5/e2e-13 都断言 `~/.agate/scripts/agate-install.py` 存在且 `--help` exit 0。
   => M2 必须「自拷贝运行中安装器所在 scripts/ 目录」+「叠加当前版本协议 scripts/ 副本」双 copytree
   （dirs_exist_ok=True）。仅按 dispatch 字面「src = _protocol_root(vdir)/scripts」单拷贝无法转绿。
2. [DESIGN_GAP] `agate-install.py main()` 不认 `latest` 参数（落 `len(args)==1` → `_VERSION_RE` 失配 → exit 2）。
   P1 §3.4 步骤 5 + e2e bdd_13 步骤 5 + install.sh --versions + BDD-2 迁移指引均用 `agate-install.py latest`。
   => main() 增 `latest` 作无参 install 别名。M 表未列此项。
3. [DESIGN_GAP] dispatch M6 写 `python3 ~/.agate/repo/agate/scripts/agate-install.py latest`，但 e2e
   `_tag_meta_upstream` 故意不放 agate-install.py 进协议目录（模拟元仓库 gap）。
   => install.sh --versions 改为 exec `$SCRIPT_DIR/agate/scripts/agate-install.py`（install.sh 同侧脚本），
   `~/.agate/repo` 仅作 `git worktree add` 的版本源。

## 实现落地（批 1）
- M3 agate_common.py：新增 `_protocol_root(vdir)`（探测序 vdir/scripts → vdir/agate/scripts → 原样），紧邻 `_resolve_version_info`
- M4 agate_common.py：`.agate-version` ok 分支 `root = _protocol_root(vdir)`，version 仍取 declared
- M5 agate_common.py：current 链分支——先 `version = os.path.basename(cur)` 再 `root = _protocol_root(cur)`（两条独立，I-1 红线）
- M1 agate-install.py：`_cmd_install` 首行 `os.path.islink(agate_home)` → `_LEGACY_SYMLINK_MSG` + exit 1（在 `_ensure_repo` 前，不建目录）
- M2 agate-install.py：新增 `_sync_root_scripts(agate_home, version_dir)`——自拷贝安装器 scripts/ + 叠加 `_protocol_root(version_dir)/scripts`（双 copytree dirs_exist_ok=True）；latest/指定版本两分支各自算 version_dir 后调用
- agate-install.py：`from agate_common import _protocol_root, ...`（含 ImportError 降级副本）；main() `latest` 作无参 install 别名；`_usage()` 同步；`_ensure_repo` 已有 repo 时 `git fetch --tags --force --prune origin`（fail-open，令重跑 latest 跟随更高 tag，BDD-4 判据 2）
- M6 install.sh：`$1 == "--versions"` 分支——软链 fail-closed 同三步指引；python 探测；`mkdir -p ~/.agate` + `git clone ${AGATE_REPO_URL:-<default>} ~/.agate/repo`（已存在则跳）+ `exec $SCRIPT_DIR/agate/scripts/agate-install.py latest`。原无参单软链路径不变

## 自跑结果（自查，非 gate）
- ruff check agate/scripts/agate-install.py agate/scripts/agate_common.py → All checks passed
- shellcheck -S warning install.sh → rc=0
- pytest -k tag0032（install/resolve/hook/e2e 四文件）→ 11 passed（bdd_1..8 + bdd_13/14）
- pytest agate/tests/unit/ agate/tests/regression/ -n auto → 1383 passed, 2 skipped, 7 failed
  失败均为 test_upgrading_lifecycle.py（BDD-10/11/12 + BDD-4 判据 3 文档面）——批 2（docs-consistency）负责，本批不动
- pytest 三大 version/hook unit 文件全量 + integration/ → 128 passed
[PROD_NOT_TOUCHED]

---

## 批 2（docs-consistency）落地

- M7 agate/UPGRADING.md：新增 `## 版本管理生命周期` 节（插在 `## 1.` 之后，无编号节）——对照表 + hook 重装统一口径 + 根 `~/.agate/scripts/` 副本维护语义（与批 1 M2 双 copytree 实现对齐）
- M8 agate/UPGRADING.md：v0.50.0 §① 表格后加 blockquote 指针；`` `scripts/`（版本管理工具） `` → `` `scripts/（版本管理工具）` ``（反引号位置微调，DESIGN_GAP）
- M9：v0.60-0.62 / v0.66-0.68 历史节未改（口径由 M7 收敛）
- M10 README.md + README.zh-CN.md：快速上手补 `install.sh --versions` 官方路径 + `agate-install.py latest` 更新口径 + 指向生命周期节（中英同步）
- M11 agate/SETUP.md：「升级 Agateon 之后」节加「更新口径」段 + 指向「版本管理生命周期」节

## 自跑结果（批 2，自查非 gate）
- pytest agate/tests/unit/test_upgrading_lifecycle.py → 7 passed（原 7 failed 全绿）
- check-protocol-consistency.py --strict-errors-only → EXIT 0 / 0 ERROR（329 WARNING 未新增）
- pytest -k "readme or upgrading or setup or doc or consistency" → 156 passed
[PROD_NOT_TOUCHED]

---

## P4 修复轮（fix-1）进度

- [x] 读 dispatch-context-implementer-fix1 + P4-review「结论」+ A 组 DESIGN_GAP 1/3 + DEBT 登记建议 + 角色定义
- [x] ① install.sh:39-45 `--versions` 分支 exec —— 选项 A：`INSTALLER=$AGATE_HOME/repo/agate/scripts/agate-install.py`，`[ -f ] ||` 回退 `$SCRIPT_DIR/...`，`exec "$PY" "$INSTALLER" latest`
- [x] ② 两个 fixture 补 agate-install.py：
  - `test_agate_version_install.py` `_tag_upstream` —— 新增 `_REAL_AGATE_SCRIPTS` 模块常量，copy2 `agate-install.py` + `agate_common.py` 进 fixture `agate/scripts/`
  - `test_version_lifecycle_e2e.py` `_tag_meta_upstream` —— copy 循环加 `agate-install.py`（agate_common.py 已在）
- [x] ③ `_sync_root_scripts` 删 layer-1（self_scripts 自拷贝），回归单源 copytree（`_protocol_root(version_dir)/scripts`）
- [x] ④ DEBT0-B：copytree 失败改 `sys.stderr.write` 一行诊断（proto 缺失 warn + return；OSError warn），不再 `contextlib.suppress` 静默
- [ ] 验证清单 7 项

### fix-1 验证结果（全绿）

1. 真实 curl|bash 隔离 HOME（`HOME=$(mktemp -d)` + `cat install.sh | bash -s -- --versions`，从无关目录、元仓库形态 fixture）→ **EXIT=0**；`$HOME/.agate/` 含 `repo/` + `v0.50.0/` + `current→latest→v0.50.0` + `scripts/agate-install.py`（`--help` exit 0）。测完 rm -rf；真实 `~/.agate` 未触碰 [PROD_NOT_TOUCHED]
2. `pytest -k tag0032`（install/resolve/hook/upgrading/e2e）→ **18 passed, 25 deselected**
3. `pytest agate/tests/unit/ agate/tests/regression/ -n auto` → **1390 passed, 2 skipped**（= 基线）
4. `pytest agate/tests/integration/ -n auto` → **94 passed**（= 基线）
5. `ruff check agate-install.py agate_common.py + 2 fixture` → All checks passed
6. `shellcheck -S warning install.sh` → rc 0
7. `check-protocol-consistency.py --strict-errors-only` → rc 0，0 ERROR（329 WARNING 均既有叙事引用）

---

## SELF-GATE fix-1（文档传播缺口修复）— 进度

- [x] 读 dispatch-context + alignment-review A2/A3/A5/A7 + 闭环建议 + implementer.md 角色定义
- [x] 读 5 改动对象 + P4-implementation.md + P2-design §2/§3 + adr.md（现有最大编号 = ADR-011 → 新增 ADR-012）+ test_upgrading_lifecycle.py tag0032 断言（无「叠加/后拷贝者胜」子串匹配，单源口径安全）
- [x] 修复 1：agate/scripts/README.md L5 机制段（补 latest/--versions/元仓库形态/单源副本 + 指向 UPGRADING 权威）+ agate-install.py 工具行（无参 / `latest` = 装 latest 指针，幂等）
- [x] 修复 2：agate/AGENTS.md 版本管理形态块（补 install.sh --versions + agate-install.py latest 行 + 元仓库形态/单源副本 blockquote，权威指向 UPGRADING）
- [x] 修复 3：agate/adr.md 新增 ADR-012（现有最大为 ADR-011，故 +1 = 012；记录版本目录两形态 + _protocol_root 探测序不可颠倒红线 + 决策 B1 单源 copytree 副本；格式对齐 ADR-009；关联扩展 ADR-009）
- [x] 修复 4：agate/UPGRADING.md L72-73 双 copytree（「运行中安装器 scripts/ 叠加 current 版本协议 scripts/，后拷贝者胜」）→ 单源 copytree 口径；其余 3 子条目未动
- [x] 修复 5：agate/platform-notes.md 指针形态节补一句（install.sh --versions POSIX shell + 决策 B1 拷贝规避 Windows 符号链接权限，无文本退化形态）
- [x] 验证：check-protocol-consistency.py --strict-errors-only → EXIT 0 / 0 ERROR / 329 WARNING（既有基线）
- [x] 验证：pytest test_upgrading_lifecycle.py -k tag0032 → 7 passed（无「叠加/后拷贝者胜」子串断言，无 DESIGN_GAP）
- [x] 验证：git diff --stat → 5 文档/ADR 文件 + P4-progress.md（分阶段落盘）；无代码/测试
- [x] 追加 P4-implementation.md `## SELF-GATE fix-1（文档传播）` 节
- fix-1 完成。
