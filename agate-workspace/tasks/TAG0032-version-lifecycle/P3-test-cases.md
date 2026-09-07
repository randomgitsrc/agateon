---
phase: P3
task_id: TAG0032
type: test-design
parent: P2-design.md
trace_id: TAG0032-P3-20260907
status: draft
created: 2026-09-07
agent: test-designer
test_code_dir: agate/tests/
---

# P3-test-cases — TAG0032 版本管理生命周期可用性批（TDD 红灯）

[NO_NEED_CONFIRM]
[PROD_NOT_TOUCHED]

P1 的 14 条 `#### BDD-NN` 1:1 转测试用例（BDD-9 除外，见 §4）。当前**全部红灯**，逐条为
**B 类**（断言失败 / 项目内 helper 未实现）——被测行为由 P4 实现。测试代码写进 worktree
既有测试树（P2-design M12-M15 指定文件），与既有用例同目录同 runner。

## test_code_dir

```yaml
test_code_dir: agate/tests/
```

分布（命名前缀 `test_tag0032_bdd_N_`，区分 TAG0008 既有 `test_bdd_*`）：

| 文件 | 状态 | 覆盖 BDD |
|------|------|----------|
| `agate/tests/unit/test_agate_version_install.py` | 追加 | BDD-1 ~ BDD-5 |
| `agate/tests/unit/test_agate_version_resolve.py` | 追加（新 fixture `_make_home_meta` / `_make_home_rootproto`） | BDD-6, BDD-7 |
| `agate/tests/unit/test_hook_resolve_entry.py` | 追加（新 fixture `_make_home_meta_hook`） | BDD-8 |
| `agate/tests/unit/test_upgrading_lifecycle.py` | 新增 | BDD-10, BDD-11, BDD-12, BDD-4 判据 3 |
| `agate/tests/integration/test_version_lifecycle_e2e.py` | 新增（helper `_tag_meta_upstream`） | BDD-13, BDD-14 |

## BDD → 用例映射（1:1）

| BDD | 测试函数 | 断言要点 | 当前红灯原因（B 类） |
|-----|----------|----------|---------------------|
| BDD-1 | `test_tag0032_bdd_1_legacy_symlink_install_fail_closed` | `~/.agate` 为软链 → `agate-install.py` exit≠0；软链目标内无新建 `repo/` / `vX.Y.Z/`。`os.symlink` 失败 → `pytest.skip` | `agate-install.py` 无 `os.path.islink` 守卫 → 穿透软链 exit 0（断言 exit≠0 失败） |
| BDD-2 | `test_tag0032_bdd_2_legacy_symlink_rejection_migration_hint` | stderr 三段命令片段逐段 grep：`mv ~/.agate …bak` / `mkdir -p ~/.agate` / `agate-install.py latest`\|`install.sh --versions`，缺一即 FAIL | 无守卫 → 无迁移指引文案（断言缺『备份软链』指引失败） |
| BDD-3 | `test_tag0032_bdd_3_plain_dir_not_falsely_rejected` | 普通目录 → `agate-install.py v0.48.0` exit 0 + `~/.agate/v0.48.0/` 建立；**附加 M2**：指定版本路径也建根 `~/.agate/scripts/` 入口副本 | 守卫不误伤部分当前已满足；红灯落在 M2 附加断言（根 `scripts/` 未建）——见 §5 说明 |
| BDD-4 判据1 | `test_tag0032_bdd_4_root_scripts_established_and_executable` | 装 latest 后 `~/.agate/scripts/agate-install.py` 存在 + `--help` exit 0 | `agate-install.py` 全程不建根 `scripts/`（断言路径存在失败） |
| BDD-4 判据2 | `test_tag0032_bdd_4b_root_scripts_copy_refreshed_on_reinstall` | 新增更高 tag（协议 `scripts/` 含 sentinel）→ 重跑 latest → 根 `~/.agate/scripts/` 出现 sentinel（决策 B1 副本随 current 刷新单测锁） | 同上（根 `scripts/` 不存在） |
| BDD-4 判据3 | `test_tag0032_bdd_4_root_scripts_copy_semantics_documented`（upgrading 文件） | UPGRADING「版本管理生命周期」节含『副本』+『升级期须重跑 agate-install』+『repo/ 被删对副本入口影响』（与 BDD-11 判据 3 交叉锁） | 该节不存在（断言 `版本管理生命周期` in text 失败） |
| BDD-5 | `test_tag0032_bdd_5_install_sh_versions_bootstrap` | 隔离 HOME + `AGATE_REPO_URL` → `install.sh --versions` → 产出 `repo/` + `vX.Y.Z/` + `current`/`latest` + 根 `scripts/`；worktree `git status --porcelain` 无 `repo/` / `vX.Y.Z/` | `install.sh` 无 `--versions` 分支 → 走 legacy 分支 exit 1（断言 exit 0 失败）。`AGATE_REPO_DIR` 预置 git 仓库令 pre-P4 快速失败，不触网络 |
| BDD-6 | `test_tag0032_bdd_6_meta_repo_resolve_returns_agate_subdir` | `_make_home_meta`（`vX/agate/scripts/` 建、`vX/scripts/` 不建）+ 项目钉 `vX` → `agate-resolve.py` → `AGATE_ROOT` == `…/vX/agate` + `AGATE_VERSION == vX` | `_protocol_root` 未实现 → resolve 返回 `vdir`（断言 `AGATE_ROOT=…/vX/agate` 失败） |
| BDD-7 | `test_tag0032_bdd_7_rootproto_resolve_semantics_unchanged` | `agate_common._protocol_root(vdir)`（`vdir/scripts` 存在）== `vdir`（探测序 1 红线）；`_make_home_rootproto` → `agate-resolve.py` → `AGATE_ROOT` == `…/vX`（不进 `/agate` 分支）+ `AGATE_VERSION == vX`（对称断言） | `agate_common` 无 `_protocol_root` helper（断言 `hasattr(..., "_protocol_root")` 失败）。CLI 层现状已满足对照断言——红线由 helper 存在性承载，见 §5 |
| BDD-8 | `test_tag0032_bdd_8_meta_repo_hook_gate_path_resolves` | 元仓库形态 meta fixture（gate 在 `vX/agate/scripts/`）+ 项目钉版 → `resolve-entry.py pre-commit` exit 0 + stub gate marker（`GATE-META-050`）被 exec | resolve 返回 `vX` → `resolve-entry.py:49` 拼 `vX/scripts/pre-commit-gate.py` 不存在 → `:50-52` exit 1（断言 exit 0 失败） |
| BDD-9 | —（无独立用例） | 见 §4 | — |
| BDD-10 | `test_tag0032_bdd_10_update_commands_aligned_and_idempotent` | UPGRADING「版本管理生命周期」节：legacy = `git pull`（含 `install-hook.py` 判定口径）；版本布局 = `agate-install latest` + `幂等` | 该节不存在（文本检索失败） |
| BDD-11 | `test_tag0032_bdd_11_lifecycle_section_covers_four_actions` | 该节存在 + 四动作（安装/迁移/更新/回退）+ hook 重装时机口径（薄壳固定 / resolve-entry / 通常无需）+ 根 `~/.agate/scripts/` 『副本』维护语义条目 | 该节不存在（文本检索失败） |
| BDD-12 | `test_tag0032_bdd_12_doc_contradiction_converged`（参数化 4 条 checklist） | ① v0.50.0 §① 表格『根含 scripts/』行留存 + 加『版本管理生命周期』指针；② 『升级 = agate-install.py』行加指针；③ 生命周期节给 hook 重装统一口径（含『复制模式』/『.sh 薄壳』）；④ README×2 补 `install.sh --versions` + SETUP 升级节加生命周期节指针 | M7-M11 未落地（各条文本检索失败）。附加回归项 `check-protocol-consistency.py --strict-errors-only` EXIT 0 由 P2 §6 `gate_commands.P5_consistency` 常驻，不新增始终绿用例 |
| BDD-13 | `test_tag0032_bdd_13_full_lifecycle_new_machine_to_update` | 隔离 HOME + `_tag_meta_upstream`（`agate/` 子目录 + `v0.43.0`/`v0.50.0` tag）→ `install.sh --versions` → 钉 `.agate-version` → `resolve-entry.py pre-commit`（exit 0 + marker）→ `agate-install.py latest`（幂等：版本目录数量不变）。逐步 exit 断言 | `install.sh` 无 `--versions` → 步骤1 exit 1（断言 exit 0 失败）。无网时不依赖 GitHub（本地 fixture 即默认路径，I-6）；无 git → `pytest.skip` |
| BDD-14 | `test_tag0032_bdd_14_e2e_no_source_pollution` | 同 BDD-13 全链路后：worktree `git status --porcelain` 无 `repo/` / `vX.Y.Z/`；`agate/` 内无 `repo/` 主克隆、无 `vX.Y.Z/` worktree | 同 BDD-13（步骤1 exit 1） |

## §4 BDD-9 说明（无独立用例，回归锁）

BDD-9（两形态下现有全量 pytest 均全绿，无旁路漏改）**不单独写用例**：其语义是「新增的
元仓库形态 fixture（`_make_home_meta` / `_make_home_meta_hook`）与『根即协议』形态 fixture
（`_make_home_rootproto`）双常驻用例，在两形态并存下全量 pytest 全绿」。这一判据由 P5 全量
回归（`gate_commands.P5`：`python3 -m pytest agate/tests/unit/ agate/tests/regression/
agate/tests/integration/ -q --tb=no -n auto`）承接——本批新增的 BDD-6/7/8 双 fixture 用例即
BDD-9 的常驻回归载体，P4 实现后随全量套件一起转绿并长期看护 DEBT0016 dirname 散点回归。

## §5 设计取舍说明（永久回归判据 / 纯增量红线）

- **BDD-3 的红灯落点**：P1 BDD-3「Then」本体（普通目录 → exit 0 + 版本目录建立）在当前
  实现下**部分已满足**（`os.path.islink` 对普通目录为 False，install 不误伤）。为使该用例在
  本 TDD 批中构成有效红灯，附加断言 P2-design **M2**（「装 latest / 指定版本两条路径都落地
  根 `scripts/` 副本」）——指定版本安装路径也须建根 `~/.agate/scripts/` 入口副本。该附加
  断言与 BDD-3 同属 `_cmd_install` 成功路径（P4 M1 守卫 + M2 副本落在同一函数），红灯为
  B 类（根 `scripts/` 未建）。
- **BDD-7 的红灯落点**：「根即协议」部署方解析语义**不变**是长期不变量（TAG0025 教训：
  长期不变量可断言当前状态）。CLI 层 `agate-resolve.py` 对 rootproto 布局现状已返回 `vdir`，
  故该用例的 CLI 断言（`AGATE_ROOT` 结尾 `/vX`、不进 `/agate` 分支、`AGATE_VERSION == vX`）
  作为纯增量红线的**长期看护**保留。红灯由**决策 A1 的机制存在性**承载：
  `assert hasattr(agate_common, "_protocol_root")`（探测序 1 = `vdir/scripts` 先命中 → 返回
  `vdir`，M3）——P4 未实现该 helper → B 类断言失败。P4 落地后 helper 存在 + CLI 断言仍成立，
  两者一起转绿并常驻。
- **BDD-12 永久回归判据**：断言的是「文档口径长期不变量」（生命周期节存在且口径一致、
  v0.50.0 历史叙事保留 + 加指针），不断言「最近一次 commit 改了什么」。`check-protocol-
  consistency.py --strict-errors-only` EXIT 0 是「非主判据、仅防新增 ERROR」，基线即 0 ERROR，
  由 P5 gate 常驻，不在 P3 新增始终绿的用例（P3 全部新增用例须红灯）。

## §6 环境隔离与平台无关（自检记录）

- 涉及安装路径 / `~/.agate` 的用例一律隔离 HOME：`HOME` + `USERPROFILE` 双 env → `tmp_path`
  子目录（`_run_install` / `_resolve_env`），**绝不动真实 `~/.agate`**（本机 legacy 软链）。
  主 checkout 未改动。状态标记 `[PROD_NOT_TOUCHED]`。
- 平台无关：`tmp_path` / `python_exe` fixture（不裸 `python3`）；`install.sh` 经 conftest
  `bash` fixture 调用；`os.symlink` 失败 → `pytest.skip`（BDD-1/2，同既有 `test_bdd_30`）；
  无 `/tmp` 字面量；git 路径 `shutil.which("git")`；无 git → e2e `pytest.skip`。
- 元仓库形态 fixture 铁律（I-5）：`_make_home_meta` / `_make_home_meta_hook` /
  `_tag_meta_upstream` 严格「协议在 `agate/` 子目录、`vX/scripts/` 不存在」；不用「根即协议」
  模拟 repo 代替。`_make_home_rootproto` 保留作 BDD-7 对照。
- 资源清理：隔离 HOME + `~/.agate` 目录均在 `tmp_path` 下，pytest 自动清理；e2e 的
  `AGATE_REPO_DIR` 预置仓库、upstream repo 同样落 `tmp_path`。

## §7 自跑红灯记录（强制自检）

```
$ /usr/bin/python3 -m pytest \
    agate/tests/unit/test_agate_version_install.py \
    agate/tests/unit/test_agate_version_resolve.py \
    agate/tests/unit/test_hook_resolve_entry.py \
    agate/tests/unit/test_upgrading_lifecycle.py \
    agate/tests/integration/test_version_lifecycle_e2e.py \
    -p no:cacheprovider -k tag0032
=> 18 failed, 25 deselected in 1.11s
```

逐条失败原因（`--tb=line` 摘录，均为 **B 类** = AssertionError / 项目内 helper 未实现，
无 A 类 SyntaxError / 第三方 import 失败）：

| 用例 | 失败原因 |
|------|----------|
| bdd_1 | `AssertionError: 软链布局下 install 应 fail-closed（exit 非 0）` |
| bdd_2 | `AssertionError: 缺『备份软链』指引` |
| bdd_3 | `AssertionError: M2：指定版本安装路径也应建立根 ~/.agate/scripts/ 入口副本` |
| bdd_4 | `AssertionError: README 快速上手入口 ~/.agate/scripts/agate-install.py 应存在` |
| bdd_4b | `AssertionError: assert False`（根 `scripts/agate-install.py` 不存在） |
| bdd_5 | `AssertionError: install.sh --versions 应成功进入版本管理布局`（exit 1） |
| bdd_6 | `AssertionError: 元仓库形态应返回 vdir/agate（协议子目录），而非 vdir` |
| bdd_7 | `AssertionError: 决策 A1：agate_common 应新增 _protocol_root helper（P4 未实现）` |
| bdd_8 | `AssertionError: 元仓库形态下 gate 路径应命中 vX/agate/scripts/，不因『gate 脚本不存在』exit 1` |
| bdd_10 | `AssertionError`（`版本管理生命周期` 节不存在） |
| bdd_11 | `AssertionError`（同上） |
| bdd_4_…_documented | `AssertionError`（同上） |
| bdd_12[v050_root_scripts_row_pointer] | `AssertionError`（v0.50.0 节无生命周期节指针） |
| bdd_12[v050_upgrade_row_pointer] | `AssertionError`（同上） |
| bdd_12[hook_reinstall_unified…] | `AssertionError`（生命周期节不存在） |
| bdd_12[readme_setup_aligned] | `AssertionError: assert 'install.sh --versions' in <README.md>` |
| bdd_13 | `AssertionError: 步骤1 install.sh --versions 应 exit 0`（exit 1） |
| bdd_14 | `AssertionError: assert 1 == 0`（install.sh exit 1） |

既有 TAG0008 用例回归：`-k "not tag0032"` → `25 passed`（无回归）。全量收集
`pytest agate/tests/ --co` → `1508 tests collected`（无收集错误）。

## §8 范围锁定

只为 14 条 BDD 写用例。未给 out-of-scope 写用例：`install-offline.py` 离线链路 /
Windows 复制模式专项 / `.state.yaml` schema 扩字段 / agateon 仓库形态重构。
