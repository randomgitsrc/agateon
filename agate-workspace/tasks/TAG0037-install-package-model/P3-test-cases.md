---
phase: P3
task_id: TAG0037
parent: P2-design.md
trace_id: TAG0037-P3-20260920
test_code_dir: agate/tests
agent: test-designer
---
# P3 测试用例清单（总索引）— TAG0037 安装与多版本模型统一

> 本文件是 P3 **总索引**，由第 1 组（A：打包库 + 共享夹具 + Release CLI + workflow + 三路径）test-designer 创建；后续 B（安装 / 离线 / legacy 代码面）、C（文档 / 回归 / 平台）组设计师在下方对应小节追加各自的 BDD→测试映射与 `tests_filter`，**不要改写本组已登记的内容**。
> 测试代码根目录：`agate/tests`（frontmatter `test_code_dir`）。

## 0. 共享夹具（B / C 组必读）

**导入方式**：`agate/tests/helpers_tag_repo.py`（与 `conftest.py` 同目录；pytest prepend 导入模式下任意测试文件 `import helpers_tag_repo as H` 即可）。不放进 conftest，避免测试文件为使用 fixture 而 `from ... import fixture` 触发 ruff F811；测试文件各自写 1 行薄 fixture：

```python
@pytest.fixture(scope="module")
def synth(tmp_path_factory):
    return H.get_shared_synthetic_repo(tmp_path_factory)   # 会话级缓存，只读
```

| 名称 | 用途 |
|------|------|
| `make_synthetic_tag_repo(tmp, extra_files=None)` / `get_shared_synthetic_repo(tmp_path_factory)` | P2 T-1：合成上游 bare 仓库（`.url` 为 `file://`，可直接作 `AGATE_REPO_URL`）。tag：`MAIN_TAG=v0.73.0`（轻量，最高严格版本，`latest` 选中）、`ANNOTATED_TAG=v0.72.5`（附注，tag 对象 SHA≠commit SHA）、`PRERELEASE_TAG=v0.73.0-tagtest.1`（CHANGELOG 仅 `[Unreleased]`+`[0.72.0]`）、`OLD_TAG=v0.48.0`（无 `.gitattributes` 的老 tag）、`NEWER_OLD_TAG=v0.49.0`（CHANGELOG 缺 `[0.49.0]` 段）、`NO_NOTICES_TAG=v0.8.0`（缺 NOTICES.md）、`MALFORMED_TAG=v0.1.0`（无 `agate/scripts/`）。树含 `agate/`（含 `tests/`、故意入库的 `__pycache__`/`*.pyc`/`*.pyo`、`run.sh` 100755、二进制 CRLF blob）、全部噪声顶层（`agate-workspace/` `docs/` `site/` `archived/` `.github/` `HANDOFF-X.md` `README*` 等）、`.gitattributes`（`*.md text eol=crlf`，BDD-15 ③ 的 EOL 陷阱）；`agate/scripts/` 内嵌 **真实脚本拷贝，含 `agate_package.py`**（`SCRIPTS_TO_COPY`，eng N-1，存在才拷）。blob 字节由夹具直接给定（`synth.files(tag)`），`synth.expected_package(tag)` 是**独立 oracle**（不 import `agate_package`）。**共享实例只读**：要 `git worktree add` / 改 ref 的测试先 `H.clone_bare(synth.bare, dest)`。 |
| `make_custom_tag_repo(tmp, files, ...)` | 单 tag 自定义树（畸形成员：`.git*`、`:`、软链 120000、子模块 160000、大小写冲突、非 UTF-8 名……）。 |
| `make_pip_shim(dir)` + `tool_env(home, agate_home=, shim_dir=, pip_log=)` + `run_tool(argv, env)` | T-11/T-15：PATH 内 `pip` 打桩（`pip download` 写占位 wheel、`pip install` 成功；`AGATE_TEST_PIP_MODE=fail-download|fail-install` 注入失败；`AGATE_TEST_PIP_WHEEL_CASE=upper` 复现 `PyYAML-…` 大写文件名；`AGATE_TEST_PIP_LOG` 记录 argv；`read_pip_log`）。**禁止全局 patch `subprocess.run`**（会吞掉 `--adopt` 子进程）。仅 POSIX（Windows 用例先 skip）；`tool_env` 清除 `AGATE_ROOT`/`AGATE_HOME`/`PYTHONDONTWRITEBYTECODE` 等继承项。 |
| `make_legacy_worktree_bundle(tmp, upstream_bare, tag, platform)` + `assert_real_bundle_layout(bundle)` | T-2「旧行为构造器」（真实 `git worktree add` 整仓检出，manifest 自洽无 `files`）与 BDD-11 sentinel 断言函数（新格式通过；旧格式必抛 `AssertionError`）。B 组用它写 BDD-11 变异用例与 BDD-12。 |
| `snapshot_tree` / `file_set` / `total_bytes` / `expected_component_sha256` / `extract_tar` / `host_platform_label` / `load_project_module` / `copy_real_scripts` / `ls_tree_sizes` / `git_blob` / `run_git` | 通用工具。比较口径默认忽略字节码（D-13）。`load_project_module` 缺文件抛 `ModuleNotFoundError`（B 类红灯）。 |

夹具自守卫（有意应绿，位于 `test_agate_package.py`）：`test_fixture_guard_*`（`SCRIPTS_TO_COPY` 含 `agate_package.py`、合成仓库形状、旧格式构造器 + sentinel）。

**跨组保护用例（本组写、B/E/C 组使其转绿）**：`test_agate_package.py::test_eng_n1_fixtures_that_copy_agate_common_also_copy_agate_package` —— 5 个既有夹具文件（`unit/test_hook_resolve_entry.py`、`integration/test_pre_commit_hook.py`、`unit/test_dispatch_context_warning.py`、`unit/test_agate_version_install.py`、`integration/test_version_lifecycle_e2e.py`）必须在各自拷 `agate_common.py` 的位置同时拷 `agate_package.py`（P2 §6 T-10；批 E/B1a 追加验收）。P3 已用 `grep -rn 'agate_common.py' agate/tests` 再核一遍，命中的其余文件（`test_agate_workspace_resolve.py` 只是运行 `agate_common.py` 本身，`test_check_protocol_consistency.py`、`test_mvwu_protocol_docs.py` 只引用路径字符串，`test_agate_common.py` 为注释）不拷入合成目录，不需改。

## 1. A 组（本组）范围与边界

BDD 范围（dispatch-context）：BDD-2、3、4、13、14、15、16、20（仅"workflow 静态契约与本地可测部分"）、21、22、23、24（仅 ② 畸形 tag 的库层判定，及 ① 历史 tag 的库层集合）。边界说明（以 P2 §5 批次表"批内验收"列为准）：

- BDD-17/18 中打包 / 无 git 环境部分、BDD-24 ① 的安装器端到端（`.agate-version` 钉版 + 指针不变）、BDD-22 的在线安装端到端（`agate-install.py latest` 落盘）、T-14 四入口软链守卫、T-16 换位失败注入、T-23 清扫只删自己的、T-19 P 集合对账、T-20 adopt 失败路径：**归 B 组**（本组只写库层 / 三路径同构中的 H1/H2 部分）。`agate_package.py` 中 `make_work_dir/sweep_stale/recover_backups/swap_in/rollback_swap/snapshot_pointers/restore_pointers/discard_backup` 不在本组测试内，由 B 组（B2 批）覆盖。
- BDD-1 / 3 ③ / 19 / 21 的文档面（UPGRADING / AGENTS.md 读取）归 C 组（F1a / F2）；本组只写库层：常量、`boundary_lines()`、`agate-release.py boundary` 与库一致。BDD-3 ③ 的"文档块条目集合 == `boundary_lines()`"由 C 组写（可用 `agate-release.py boundary` 输出或 `agate_package.boundary_lines()` 对比 UPGRADING fenced 块）。BDD-21 归 C 组（读 AGENTS.md 发布清单；资产口径见 P2 T-13）。
- BDD-20 真实 CI 实跑 / actionlint：属 P5/P6，本组不写；本组以 T-8 静态契约覆盖其"本地可测部分"（`test_release_workflow.py`）与 BDD-13 ⑥ 的不可变历史证据判定。BDD-13 ⑤ 的"资产名"在 `agate-release.py build` 上验证（workflow 只调脚本、内零打包逻辑，由静态用例锁定）。
- `test_release_workflow.py` 的 BDD-13 ⑥（既有 4 个 workflow 不受影响）以"改过 `release.yml` 的每个非合并提交都未同时改这 4 个文件 + 工作区无改动"判定（不可变历史证据，不会因日后合法修改这些 workflow 而假红）。

## 2. A 组 BDD → 测试映射

文件缩写：`PKG` = `agate/tests/unit/test_agate_package.py`；`REL` = `agate/tests/unit/test_agate_release.py`；`WF` = `agate/tests/unit/test_release_workflow.py`；`TP` = `agate/tests/integration/test_install_three_paths.py`。参数化 BDD 逐子场景一个参数化用例（全或无）。

| BDD / T | 测试（文件::用例，方括号为参数子场景） |
|---------|----------------------------------------|
| BDD-1（库层：常量 / 边界行 / stdlib-only / 不写字节码；文档面归 C 组） | `PKG::test_bdd_1_constants_and_boundary_lines`、`PKG::test_agate_package_is_stdlib_only_and_never_writes_bytecode`、`REL::test_boundary_subcommand_prints_library_lines` |
| BDD-2（F_pkg 逐项 ①–④） | `PKG::test_bdd_2_list_package_equals_expected_set_on_synthetic_tag`、`PKG::test_bdd_2_is_packaged_true_for_body_and_registered_root_files[*]`、`PKG::test_bdd_2_is_packaged_false_for_excluded_and_unregistered[*]`、`PKG::test_bdd_2_verify_dir_*`、`TP::test_bdd_4_online_install_matches_library_package_set` |
| BDD-3 ①② [参数化] | `PKG::test_bdd_3_default_deny_and_auto_include[bdd3-1-unregistered-top-level / bdd3-2-new-file-under-agate]`；③ 库层 `PKG::test_bdd_1_constants_and_boundary_lines` + `REL::test_boundary_subcommand_prints_library_lines`（文档块比对归 C 组） |
| BDD-4（三路径同构；T-4） | `TP::test_bdd_4_h1_online_and_h2_offline_produce_same_structure`（H1 vs H2，无文档依赖）、`TP::test_bdd_4_all_three_paths_produce_same_structure_including_portable`（+H3，依赖 F1a，波次末转绿）、`TP::test_bdd_4_online_install_matches_library_package_set` |
| BDD-13（workflow 静态 ①–⑥） | ① `WF::test_bdd_13_1_trigger_is_only_push_tags_v_star`；② `WF::test_bdd_13_2_permissions_only_contents_write`；③ `WF::test_bdd_13_3_no_secrets_reference_only_github_token`；④ `WF::test_bdd_13_4_zero_third_party_actions`；⑤ `REL::test_bdd_13_5_build_produces_exactly_the_documented_assets`、`REL::test_bdd_13_5_and_20_prerelease_build_uses_tag_verbatim_and_strict_manifest_version`、`WF::test_bdd_13_workflow_contains_no_packaging_logic_only_calls_repo_script`；⑥ `WF::test_bdd_13_6_release_workflow_change_does_not_touch_existing_workflows`；T-8 增补：`WF::test_t8_*`、`WF::test_d15_*`、`WF::test_bdd_13_release_job_shape` |
| BDD-14（notes；T-9） | ① `REL::test_bdd_14_1_formal_tag_extracts_exactly_its_section`；② `REL::test_bdd_14_2_formal_tag_missing_section_fails_closed_without_output`、`…_2b_formal_tag_with_empty_section_body_also_fails_closed`、`REL::test_bdd_14_formal_tag_never_falls_back_to_unreleased`、`REL::test_bdd_14_2_build_fails_closed_for_formal_tag_without_changelog_section`；③ `REL::test_bdd_14_3_real_changelog_v0_72_0`；④ [参数化] `REL::test_bdd_14_4_prerelease_tag_rule_and_fallback[bdd14-4-A-has-0.73.0-section / bdd14-4-B-only-unreleased-falls-back]`、`REL::test_bdd_14_4_prerelease_without_any_usable_section_fails_closed`；直接可调用 `REL::test_bdd_14_extract_notes_is_directly_callable_without_ci`；T-9：`REL::test_t9_notes_header_states_integrity_limits[*]`、`REL::test_bdd_14_and_15_build_notes_for_formal_tag` |
| BDD-15（本体 tarball ①–④；T-6 / T-18） | `REL::test_bdd_15_body_tarball_matches_tag_and_members_are_safe`、`REL::test_bdd_15_and_s11_tarball_metadata_is_deterministic`、`REL::test_bdd_15_skip_offline_builds_only_body_and_sums`、`REL::test_t18_two_builds_of_same_tag_have_identical_hashes`、`REL::test_s11_sha256sums_is_verifiable_and_sorted`、`REL::test_t18_real_tag_v0_72_0_body_tarball_matches_git_blobs`；库层 `PKG::test_t6_*`（成员安全 / 排序 / 归零 / gzip 头 / 拒软链与 FIFO / 前缀 / 确定性）、`PKG::test_bdd_15_materialize_*`、`PKG::test_d16_materialize_refuses_existing_files_and_never_follows_symlinks`、`PKG::test_s11_*`；`--expect-sha`：`REL::test_t18_expect_sha_covers_lightweight_and_annotated_tags[light-commit-sha / annotated-tag-object-sha / annotated-commit-sha / light-wrong-sha / annotated-wrong-sha]`；`REL::test_t22_is_prerelease_exit_codes[*]`（T-22）；`REL::test_t17_build_rejects_invalid_tag_names[*]`、`REL::test_d13_*` |
| BDD-16 [参数化 平台] | `REL::test_bdd_16_offline_tarball_layout_and_manifest[linux-x86_64 / windows-x86_64]`、`REL::test_bdd_16_offline_tarball_install_and_resolve_end_to_end`（bundle 内入口 + shim + resolve，T-15） |
| BDD-20（本地可测部分） | 静态契约同 BDD-13（`WF::*`）；CI/本地一致性的本地对应 `REL::test_t18_two_builds_of_same_tag_have_identical_hashes`；预发布 tag 的资产名 / notes / manifest：`REL::test_bdd_13_5_and_20_prerelease_build_*`。真实 CI 实跑、`gh` 清理、actionlint：P5/P6，不在 P3 |
| BDD-21 | 归 C 组（文档面）；本组仅按 C-1 口径固定资产集合：`REL::test_bdd_13_5_build_produces_exactly_the_documented_assets` |
| BDD-22（库层） | `PKG::test_bdd_22_library_set_equals_materialized_directory`、`PKG::test_bdd_24_historical_tags_only_get_body[*]`；在线安装端到端归 B 组（`TP` 的 H1 部分已覆盖同构） |
| BDD-23 | `PKG::test_bdd_23_synthetic_ratio_uses_same_formula`、`PKG::test_bdd_23_real_head_package_is_small_and_clean`、`PKG::test_bdd_23_v0_72_0_baseline_matches_p1_numbers`（B=1,864,871 B、153 文件、S≤2,331,088 B）；真实 `agate-install.py` 实测归 P5/P6 |
| BDD-24（库层） | ② `PKG::test_bdd_24_malformed_tag_without_agate_scripts_is_rejected`、`REL::test_bdd_24_2_build_of_malformed_tag_fails_without_assets`；① 库层 `PKG::test_bdd_24_historical_tags_only_get_body[old-tag-without-notices / old-tag-without-any-exclusion-config]`（① 安装器端到端归 B 组） |
| T-6 / T-17 / T-21 / T-7 / D-13 / D-14 / D-16（库） | `PKG::test_t6_*`、`PKG::test_t17_*`（`parse_release_ref` 表驱动、`is_strict_version`、`list_package` 拒 15 类畸形成员 + 包区外不误伤 + `tests` casefold）、`PKG::test_t21_*`（`compute_sha256` 字节码免疫；改的是 `agate_common.py`，属批 E）、`PKG::test_t7_tripwire_*`、`PKG::test_d14_*`（软链基址规范化 6 种变体 + 6 种合法路径 + `agate_home()`）、`PKG::test_d13_verify_dir_bytecode_policy_and_extra_top`、`REL::test_d13_*`（脚本顶部先设不写字节码；从脚本副本运行 build 后无 `__pycache__`） |
| T-15（本批部分） | `TP::test_t15_bundle_internal_entry_leaves_no_bytecode`、`TP::test_t15_pack_never_uses_worktree_metadata_in_bundle`、`TP::test_t15_real_tree_smoke_pack_install_resolve`（`git clone --bare --local` 真实 HEAD + 临时 tag `v9.9.9`，读**已提交**的 HEAD） |

## 3. 各批 `tests_filter`（A 组回填；P2 §5 文件名沿用，实际对应如下）

| 批 | 命令 | 说明 |
|----|------|------|
| A-package-lib | `python3 -m pytest agate/tests/unit/test_agate_package.py -q -k "not eng_n1 and not t21_compute_sha256_directory_ignores_bytecode"` | 排除 2 个跨批用例：`eng_n1`（B/E 组改既有夹具后转绿）、`t21_compute_sha256_directory_ignores_bytecode`（改 `agate_common.py`，批 E）。波次末用不带 `-k` 的完整命令：`python3 -m pytest agate/tests/unit/test_agate_package.py -q`。 |
| C1-release-cli | `python3 -m pytest agate/tests/unit/test_agate_release.py agate/tests/integration/test_install_three_paths.py -q -k "not all_three_paths_produce_same_structure_including_portable"` | 依赖 A、B2（`--ref`、manifest `files`、bundle 内入口）、E。H3（portable）用例读 UPGRADING 文档命令，属 F1a，波次末转绿：`python3 -m pytest agate/tests/integration/test_install_three_paths.py -q`。`test_t15_real_tree_smoke_*` 读**已提交** HEAD，须 A/B/E 各批已 commit。 |
| C2-release-workflow | `python3 -m pytest agate/tests/unit/test_release_workflow.py -q` | 批内全绿。 |
| F1a（波次末，本组相关） | `python3 -m pytest agate/tests/integration/test_install_three_paths.py::test_bdd_4_all_three_paths_produce_same_structure_including_portable -q` | portable 小节命令即验收脚本。 |

## 4. 红灯自证（`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <file> -q --no-header -p no:cacheprovider`）

| 文件 | 用例数 | 失败 / 通过 | 失败原因（均为 B 类：项目内模块缺失 / 行为未实现） |
|------|--------|-------------|------------------------------------------------------|
| `unit/test_agate_package.py` | 129 | 124 失败 / 5 通过 | 122 × `ModuleNotFoundError: No module named 'agate_package'`；2 × 断言失败：`t21` 目录哈希被字节码改变（`agate_common.compute_sha256` 未免疫）、`eng_n1` 5 个既有夹具未拷 `agate_package.py`。5 个有意应绿：3 个夹具自守卫、`t21` 反面（内容变化仍改变哈希，既有行为）、`t7` tripwire（当前 19 项 `agate/` 顶层）。 |
| `unit/test_agate_release.py` | 47 | 47 失败 / 0 通过 | 45 × `ModuleNotFoundError: No module named 'agate_release'`（脚本未实现）；2 × `agate_package` 缺失（模块级 fixture 内不抛，留给用例断言处抛，不会变成 ERROR）。 |
| `unit/test_release_workflow.py` | 12 | 12 失败 / 0 通过 | 12 × `AssertionError: 缺 .github/workflows/release.yml`。 |
| `integration/test_install_three_paths.py` | 6 | 6 失败 / 0 通过 | 旧 packer 产出 `bundle/agate/agate/scripts` 双层嵌套（P0 BUG 复现）→ bundle 内 `install-offline.py` 不存在 → 3 × `h2 应成功: rc=2`、`bundle/agate/scripts 缺失`、real-tree 冒烟找不到 bundle 内入口；1 × `agate_package` 缺失。 |

无 SyntaxError、无第三方 import 失败；`ruff check`（`~/.venvs/agate-dev/bin/ruff`）全绿。共 194 用例，189 红灯 / 5 有意应绿。

**对照实现验证（防"测试与数据 / 设计矛盾"，T075 教训）**：在 scratchpad 依 P2 §3.2–§3.6 写了一份**参考实现**（`agate_package.py` / `agate-release.py` / 新 `agate-pack-offline.py` / `install-offline.py`、`agate-install.py --adopt`、P2 §3.6 workflow 草案；不入仓库），用环境变量 `AGATE_ROOT`（换 `agate_scripts`）与 `AGATE_TEST_SCRIPTS_SRC`（换夹具内嵌的真实脚本来源，`helpers_tag_repo.py` 内的只读调试开关，缺省即仓库 `agate/scripts`）把本组测试指向它：`test_agate_package.py` 128 / 129 通过（仅跨批 `eng_n1` 仍红，符合预期）、`test_agate_release.py` 47 / 47、`test_release_workflow.py` 12 / 12、`test_install_three_paths.py` H1/H2/H3 全部通过（H3 用 P2 §3.5 文档命令经临时 pytest 插件注入；real-tree 冒烟读已提交 HEAD，不可用参考实现验证）。说明每条断言与 P2 契约自洽、可被正确实现满足。

## 5. 数据安全与隔离

全部测试在 `tmp_path` / `tmp_path_factory` 内建 bare 仓库、`AGATE_HOME`、`HOME`；不触碰真实 `~/.agate`、开发 checkout（`git clone --bare --local` 真实 HEAD 只读，写入落在 tmp）、真实 origin；不推 tag、不发 Release；无 `rm -rf`、无删除既有文件；仓库内新增文件仅：`agate/tests/helpers_tag_repo.py`、4 个测试文件、本文件（含 `P3-progress.md` 追加）。`pip` 一律 PATH shim，无网络依赖。

## 6. B 组

### 6.1 范围与边界

BDD 范围（dispatch-context B）：BDD-5、6、7、8、10、11、12、18、25、26、27、28、29、30、31、32、33、34、35、36、38、47、51、52；另按 P2 §5 批次表"批内验收"补写 B 侧独有子场景：BDD-9（离线安装 + 解析，A 组只写库层与三路径 H2）、BDD-17（**仅** adopt / 无 git 的命令部分；文档命令实跑归 C / TP 的 H3）、BDD-22 / 24 ① ②（在线安装端到端）、T-14 / T-16 / T-19 / T-20 / T-23、`agate_package` 换位 / 清扫 8 个库函数（A 组 §1 明确归 B2 批）。BDD-23 的真实仓库实测仍归 P5 / P6（A 组已写库层公式）。

文件缩写：`ADOPT`=`unit/test_agate_install_adopt.py`（新）；`SH`=`unit/test_install_sh.py`（新）；`DUAL`=`regression/test_protocol_root_dual_impl.py`（新）；`OFF`=`unit/test_install_offline.py`；`PACK`=`unit/test_agate_pack_offline.py`；`RT`=`regression/test_offline_bundle_roundtrip.py`；`RES`=`unit/test_agate_version_resolve.py`；`WS`=`unit/test_agate_workspace_resolve.py`；`SUM`=`unit/test_agate_summary.py`；`INST`=`unit/test_agate_version_install.py`；`UNINST`=`unit/test_agate_install_uninstall.py`；`HOOK`=`unit/test_hook_resolve_entry.py`（后 8 个及 DUAL / SH / ADOPT 之外均为既有文件，改动见 6.5）。参数化 BDD 逐子场景各一个参数化用例（全或无）。

### 6.2 BDD → 测试映射

| BDD / T | 测试（文件::用例，方括号为参数子场景） |
|---------|----------------------------------------|
| BDD-5 [参数化 ①–④] | `RES::test_bdd_5_old_worktree_form_version_dir_still_resolves[bdd5-1-resolve / bdd5-2-resolve-declared / bdd5-3-hook-root / bdd5-4-summary]`（旧形态由真实 `git worktree add --detach` 显式构造，保留在测试中；有意应绿） |
| BDD-6 | `DUAL::test_bdd_6_scripts_at_vdir_wins_over_agate_scripts`、`…_new_contract_shape_hits_probe_order_2`、`…_neither_form_returns_vdir_unchanged`（有意应绿）；"既有两用例源码未改 / `_protocol_root` 函数体零 diff"是一次性交付事实，**不写永久 pytest**（否则日后合法修改即假红），改列 P5/P6 命令，见 6.6 |
| BDD-7 [参数化 ①②] | `RES::test_bdd_7_old_and_new_form_versions_coexist[bdd7-1-current-is-new-form / bdd7-2-pinned-old-form]`（新形态由新安装器装出，Given 断言其无 `.git`；旧形态用真实 worktree） |
| BDD-8 | `DUAL::test_bdd_8_both_impls_return_expected_and_equal[bdd8-1…bdd8-5]`（五夹具：仅 `vdir/scripts` / 仅 `vdir/agate/scripts` / 两者皆有 / 两者皆无 / 新契约形态）、`DUAL::test_bdd_8_guard_catches_a_one_sided_probe_order_change`（变异自证："只改一处必被拦截"）；降级副本经"强制 agate_common 导入失败"加载 agate-install.py 取得（有意应绿） |
| BDD-9（B 侧） | `OFF::test_bdd_9_offline_install_from_bundle_internal_entry_then_resolve`（bundle 内入口 T-15 → resolve exit 0，无 `agate/agate`，`_protocol_root(vdir)` ≠ vdir，安装前后 bundle 无字节码）、`PACK::test_bdd_9_and_11_real_pack_bundle_is_body_not_whole_repo`、`PACK::test_bdd_9_bundle_has_no_bytecode_no_worktree_metadata_and_source_repo_untouched`、`PACK::test_bdd_9_manifest_files_lists_package_set_and_root_file_components` |
| BDD-10 | `OFF::test_bdd_10_dest_defaults_to_agate_home_and_fills_version_root_structure`、`PACK::test_bdd_10_default_repo_follows_agate_home` |
| BDD-11 | ①`OFF::_make_bundle`（经真实 pack 入口生成 + 立即断言 sentinel）、`PACK::test_bdd_11_offline_test_helpers_no_longer_forge_the_body_by_hand`（三处助手文件静态扫描，正则 `\(agate\w* / "WORKFLOW.md"\).write_text`）；②`OFF::test_bdd_11_bundle_helper_output_is_body_not_whole_repo`、`PACK::test_bdd_9_and_11_real_pack_…`；③`RT::test_bdd_2_pack_install_uninstall_roundtrip_no_behavior_change`（末尾新增 `agate-resolve` exit 0 + AGATE_ROOT）；④红灯回放：`OFF::test_bdd_11_t2_replay_old_packer_layout_fails_the_sentinel`（T-2 永久变异测试，旧 packer 构造器 → sentinel 抛 AssertionError）+ 一次性证据见 6.4（P4 前真实 pack 上 BDD-9 / sentinel 全红） |
| BDD-12 [2 子场景] | `OFF::test_bdd_12_old_format_bundle_rejected_and_nothing_written[bdd12-1-dest-absent / bdd12-2-dest-empty-dir]`（旧格式 = `H.make_legacy_worktree_bundle`，校验和自洽；断言 exit 1、stderr 含 `agate/agate/scripts` 与"重新打包"、dest 快照不变） |
| BDD-17（adopt 部分） | `ADOPT::test_bdd_17_adopt_registers_pointers_and_root_scripts_without_git[bdd17-1-git-tripwire / bdd17-2-no-git]`、`…_adopt_is_idempotent_and_does_not_modify_version_dir`、`…_adopt_old_worktree_form_dir_skips_contract_verification`、`ADOPT::test_d13_adopt_from_version_dir_entry_writes_no_bytecode` |
| BDD-18 [参数化 ①②③] | `ADOPT::test_bdd_18_1_portable_check_without_git_exit_0_with_hint`、`…_18_2_portable_check_missing_pyyaml_fails_with_fix_guidance`、`…_18_3_default_check_without_git_still_fails_listing_git`（③ 有意应绿；既有 `test_bdd_7` / `test_bdd_8` 源码未改） |
| BDD-22（在线端到端） | `INST::test_bdd_22_online_install_latest_installs_body_only` |
| BDD-24 ① ②（安装器端到端） | `INST::test_bdd_24_1_install_historical_tag_gets_body_only_and_pointers_unchanged[bdd24-1-old-tag-without-exclusion-config / bdd24-2-old-tag-without-notices]`、`INST::test_bdd_24_2_malformed_tag_without_agate_scripts_fails_closed`、`PACK::test_bdd_24_old_tag_missing_notices_is_tolerated`、`PACK::test_bdd_24_malformed_tag_without_agate_scripts_fails_without_manifest` |
| BDD-25 [参数化 ①②③] | `UNINST::test_bdd_25_1a_uninstall_new_form_with_repo_unpointed_version`、`…_1b_uninstall_pointed_version_repoints_to_latest_valid`（①）、`…_2_uninstall_new_form_without_repo`（②）、`…_3_uninstall_old_worktree_form_leaves_no_registration`（③，旧形态显式构造）、`…_4_uninstall_reference_protection_unchanged`、`…_5_uninstall_prunes_stale_worktree_registration_of_replaced_dir`（eng m-4） |
| BDD-26 | `INST::test_bdd_26_online_reinstall_is_idempotent_and_does_not_pollute_source`、`SH::test_bdd_26_install_sh_rerun_is_idempotent_and_does_not_pollute_source`；既有 `test_bdd_3`（见 6.5 DESIGN_GAP-B1）/ `test_tag0032_bdd_3/4/5` / `test_tag0032_bdd_13/14` 保持通过 |
| BDD-27 | `RES::test_bdd_27_symlink_home_fail_closed`（原 `test_bdd_30_legacy_symlink_direct_root` 改写，windows_smoke 保留）、`RES::test_debt0042_agate_home_symlink_fail_closed`（原 `test_debt0042_agate_home_legacy_symlink` 改写）、`RES::test_bdd_27_t14_resolve_symlink_home_fail_closed_with_migration_hint[t14-0-L … t14-4-Lsdd]`（T-14，resolve 入口） |
| BDD-28 [参数化 a–e] | `RES::test_bdd_28_resolution_chain_has_only_three_layers[bdd28-a … bdd28-e]`、`RES::test_bdd_28_use_legacy_is_gone_and_no_symlink_target_as_root_branch`（`inspect.signature` 无 `use_legacy`、源码无 `realpath(base)` 作根）、`RES::test_bdd_28_resolve_info_reports_symlink_base_including_env_branch`（eng m-6）、`WS::test_bdd_28_workspace_resolve_unaffected_by_symlink_agate_home` |
| BDD-29 [参数化 ①②] | `SH::test_bdd_29_install_sh_enters_version_layout[bdd29-1-no-args / bdd29-2-versions-alias]`、`SH::test_bdd_29_both_entries_produce_identical_tree`、`SH::test_bdd_29_install_sh_has_no_symlink_logic`、`SH::test_bdd_29_unknown_argument_rejected_with_usage_exit_2` |
| BDD-30 | `SH::test_bdd_30_deprecated_env_warns_and_creates_nothing`、`…_no_warning_when_deprecated_env_unset`、`…_install_sh_header_and_usage_no_longer_reference_deprecated_names`、`…_test_files_no_longer_reference_agate_repo_dir`（一次性交付项，仅对两个指定文件的当前内容断言；已绿） |
| BDD-31 [参数化 ①② × T-14] | `SH::test_bdd_31_install_sh_symlink_home_fail_closed[bdd31-1-no-args / bdd31-2-versions × t14-0-L … t14-4-Lsdd]`（10 例；断言 exit 1、三步片段（`L/..` 断言拒绝 `..` 分量）、目标金丝雀 / 物理父目录不变、git 包装器日志不存在 = 无 clone） |
| BDD-32 [参数化 × T-14] | `INST::test_bdd_32_t14_agate_install_symlink_home_fail_closed[bdd32-1-no-args / bdd32-2-latest / bdd32-3-version × t14-0 … t14-4]`（15 例）；`ADOPT::test_t14_adopt_symlink_home_fail_closed[5]`（--adopt 入口）；既有 `test_tag0032_bdd_1/2` 零改动保留 |
| BDD-33 [T-14] | `OFF::test_bdd_33_offline_install_symlink_dest_fail_closed[bdd33-1-dest-root / bdd33-2-agate-home × t14-0 … t14-4]`（10 例）、`OFF::test_bdd_33_regular_dest_root_is_not_rejected[bdd33-3-existing-dir / bdd33-4-new-dir]`（不误伤） |
| BDD-34 | `SUM::test_bdd_34_summary_symlink_home_prints_migration_hint_instead_of_silent_failure` |
| BDD-35 | `INST::test_bdd_35_migration_steps_consistent_across_all_entries`（install.sh / agate-install.py / install-offline.py / agate_common.py / UPGRADING.md 五处三片段逐一相等，用既有 `_migration_steps`）、`INST::test_bdd_35_runtime_stderr_steps_identical_between_installer_and_resolver`；既有 `test_debt0034_*` 两个保留不动 |
| BDD-36 | `SH::test_bdd_36_migration_three_steps_walk_through`（三步命令取自 install.sh 自身拒绝文案并真实执行；结果满足 BDD-29 结构、resolve exit 0、`.agate.bak` 软链完好、以改名验证可回滚，不删任何内容） |
| BDD-38 | ① `RES` 两处改写（见 BDD-27 行）；② `INST::test_tag0032_bdd_1/2` 零改动；③ 撞名 `test_bdd_30*` 函数体零改动 / ④ 见 6.6 验收命令（一次性交付事实，不写永久 pytest）；C 组负责 `test_upgrading_lifecycle.py::test_tag0032_bdd_10_*` |
| BDD-47 | `HOOK::test_bdd_47_new_form_version_dir_hook_chain_resolves_and_runs_gate`（红灯：`agate_package.py` 未实现）、`HOOK::test_bdd_47_symlink_agate_home_does_not_make_the_link_target_the_hook_root`、`HOOK::test_bdd_47_copy_mode_agate_root_marker_recovery_kept`（后两条有意应绿，锁 S-17 兜底）、`WS::test_bdd_47_workspace_resolve_runs_from_minimal_scripts_dir_with_agate_package`；既有 `HOOK` 全部用例 + `test_pre_commit_hook.py::test_agate_root_self_locate_worktree`（含 `_build_probe_workflow_root` 两处夹具）保持通过（夹具增拷 `agate_package.py`，见 6.5） |
| BDD-51 | ① `RES::test_bdd_51_1_symlink_to_full_version_root_resolves_via_current_chain`、`SUM::test_bdd_51_summary_symlink_to_full_version_root_prints_no_migration_hint`（eng N-4：不打印迁移提示）；② `INST::test_bdd_51_2_install_into_symlinked_full_version_root_is_refused_with_resolution_note`（文案含"解析仍可用"） |
| BDD-52 | `SUM::test_bdd_52_scripts_inside_the_body_package_without_agate_tests_have_no_traceback`（真实 HEAD 经 `agate_package.materialize` 解包，无 agate/tests；四脚本无 Traceback；risk-score 覆盖无参与 TASK_DIR 两种调用，C-2） |
| T-16 换位失败注入 | `OFF::test_t16_swap_failure_keeps_old_version_complete_and_pointers_unchanged[t16-1-step1-backup-rename / t16-2-step2-final-rename]`、`…_fresh_install_final_rename_failure_leaves_no_half_install`、`…_adopt_failure_restores_old_directory_and_partially_written_pointers`（真实 CLI，current 位置是真实目录使 adopt 失败）、`…_pip_install_failure_leaves_dest_untouched`；`OFF::test_replace_existing_version_dir_recovers_a_damaged_install`（S-16）；`ADOPT::test_t20_adopt_pointer_position_is_real_directory_exit_1_no_traceback_and_restores[t20-4 / t20-5]` |
| T-19 P 集合对账 / G-5 | `OFF::test_t19_p_set_reconciliation_rejects_and_leaves_dest_unchanged[t19-1-extra / t19-2-missing / t19-3-renamed]`（多 / 少变体重算目录哈希，使拒绝只能来自对账）、`…_bundle_top_level_file_outside_contract_is_not_copied`（extra.sh 不拷 + 告警）、`OFF::test_t6_bundle_with_symlink_member_is_rejected[t6-1 / t6-2]`（软链内容与原文件逐字节相同，只有软链检查能拒绝） |
| T-20 adopt 失败路径 | `ADOPT::test_t20_adopt_rejects_non_conforming_new_form_dir[t20-1-symlink-member / t20-2-extra-top-level-entry / t20-3-tests-dir]`、`…_pointer_position_is_real_directory…[t20-4 / t20-5]`、`ADOPT::test_adopt_rejects_invalid_version_strings[5]`、`…_missing_version_dir_and_missing_protocol_scripts_exit_1` |
| T-23 清扫只删自己的 | `OFF::test_t23_install_sweeps_only_own_expired_containers_and_keeps_everything_else`（CLI 端到端）；库层 `OFF::test_lib_sweep_stale_only_removes_marked_expired_tmp_containers`、`…_lib_recover_backups_only_renames_and_never_deletes`、`…_lib_discard_backup_refuses_directories_it_did_not_create` |
| agate_package 换位 / 清扫库函数 | `OFF::test_lib_make_work_dir_creates_marked_private_container`、`…_lib_swap_in_fresh_replace_rollback_and_discard`、`…_lib_snapshot_and_restore_pointers_roundtrip[ptr-symlink / ptr-text-file / ptr-absent]`（含上述 sweep / recover / discard 三条） |
| P2 §3.3–§3.4 其它 | `INST::test_online_install_rejects_invalid_version_strings[4]`、`OFF::test_manifest_version_must_be_strict_fullmatch[3]`、`OFF::test_bdd_26b_checksum_mismatch_message_says_corrupt_or_replaced_not_tampered`（cso F-4）、`PACK::test_pack_ref_prerelease_tag_content_with_strict_manifest_version`、`PACK::test_pack_pins_pyyaml_and_finds_wheel_case_insensitively[2]`（cso F-2 / E-16） |

### 6.3 各批 `tests_filter`（B 组回填；P2 §5 文件名沿用，实际对应如下）

| 批 | 命令 | 说明 |
|----|------|------|
| B1a-online-install-core | `python3 -m pytest agate/tests/unit/test_agate_version_install.py agate/tests/unit/test_agate_install_uninstall.py -q -k "not bdd_35"` | 依赖 A。`bdd_35` 两条需 E（install.sh / agate_common / resolve）+ B2（install-offline.py 迁移文案），归波次末；其余批内转绿。 |
| E-legacy-removal-code | `python3 -m pytest agate/tests/unit/test_agate_version_resolve.py agate/tests/unit/test_agate_summary.py agate/tests/unit/test_agate_workspace_resolve.py agate/tests/unit/test_install_sh.py agate/tests/regression/test_protocol_root_dual_impl.py -q -k "not test_bdd_52 and not test_bdd_7_old_and_new"` + 追加验收（P2 §5 备注）：`python3 -m pytest agate/tests/unit/test_hook_resolve_entry.py agate/tests/integration/test_pre_commit_hook.py agate/tests/unit/test_dispatch_context_warning.py -q` | 依赖 A。`test_install_sh.py` 用合成上游内嵌的**真实** `agate-install.py`（`latest`）——须 B1a 已合并（P2 序 A → B1a ∥ E，故 install.sh 各用例在 B1a 之后转绿）；`test_bdd_7_old_and_new` 同理依赖 B1a；`test_bdd_52` 读**已提交** HEAD（`materialize(REPO_ROOT, "HEAD")`），须 A / E 已 commit。 |
| B1b-adopt-check | `python3 -m pytest agate/tests/unit/test_agate_install_adopt.py -q` | 依赖 B1a；批内全绿（版本目录手工搭建，不经 agate_package 构建器）。 |
| B2-offline-pack-install | `python3 -m pytest agate/tests/unit/test_install_offline.py agate/tests/unit/test_agate_pack_offline.py agate/tests/regression/test_offline_bundle_roundtrip.py -q` | 依赖 A、B1b（`--adopt`）、E（`compute_sha256` 字节码免疫；`test_bdd_9_offline_install…` 的 resolve 段）。 |
| 波次末（本组相关） | `python3 -m pytest agate/tests/unit/test_agate_version_install.py agate/tests/unit/test_install_sh.py agate/tests/unit/test_agate_version_resolve.py agate/tests/unit/test_agate_summary.py -q` | 补跑上面被 `-k` 排除的 `bdd_35` / `test_bdd_52` / `test_bdd_7_old_and_new`。 |

### 6.4 红灯自证与对照实现验证

红灯运行：`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <file> -q --no-header -p no:cacheprovider --tb=line`（本机 Python 3.12 / git 2.43；无 SyntaxError、无第三方 import 失败、无 ERROR；`ruff check` 全绿）。

| 文件 | 失败 / 通过 | 失败原因（均为 B 类） |
|------|-------------|------------------------|
| `ADOPT` | 22 失败 / 2 通过 | 22 × 断言失败：`--adopt` 未识别（用法退出 2 ≠ 期望）、`--check --portable` 缺 git 仍 exit 1；2 有意应绿：`bdd18-2`（缺 pyyaml 默认口径已 exit 1 + 指引）、`bdd18-3`（默认口径不变，既有行为） |
| `SH` | 19 失败 / 2 通过 | 19 × 断言失败：旧 install.sh 无参走单软链旧路径（git 包装器拦截 http 克隆，退出 97）、无 WARNING、无规范化 / `..` 拒绝；2 通过：`bdd31-2-versions-t14-0-L`（既有 `--versions` 软链守卫）、`test_bdd_30_test_files_no_longer_reference_agate_repo_dir`（一次性交付项，本组已清理） |
| `DUAL` | 9 通过 / 0 失败 | 有意应绿（永久回归：锁既有行为，含变异自证） |
| `OFF` | 52 失败 / 4 通过 | 44 × 断言失败：真实 pack 产物仍是旧整仓格式（`bundle/agate/scripts` 缺失，P0 BUG 复现）/ 无软链守卫 / 无 `files` 对账等；8 × `ModuleNotFoundError: agate_package`（库函数用例）；4 通过：TAG0031 R1 三用例 + `test_bdd_11_t2_replay…`（有意应绿：T-2 永久变异测试） |
| `PACK` | 10 失败 / 6 通过 | 6 × 断言失败（旧 packer 整仓检出、`.git` 指针、缺缺省 `--repo`、未知 `--ref`）；2 × `KeyError: 'files'`（manifest 无 files 清单）；2 × `ModuleNotFoundError: agate_package`；6 通过：`bdd23`、`bdd24 tag_missing / pip_network / wheel_missing`（既有行为）、`bdd1 compute_sha256`、`test_bdd_11_offline_test_helpers…`（三处助手已改，已绿） |
| `RT` | 1 失败 | 断言失败：sentinel `bundle/agate/scripts` 缺失（旧 pack 产物） |
| `RES` | 13 失败 / 26 通过 | 12 × 断言失败（软链仍被直通解析 exit 0 / 无三步迁移片段 / `use_legacy` 仍在签名 / 新形态未产出；其中 1 例断言点在探针子进程内的 `KeyError: 'symlink_base'`）+ 1 × 用例内直接 `KeyError: 'symlink_base'`；有意应绿：BDD-5 ×4、BDD-28 a/b/c/e |
| `WS` | 1 失败 / 11 通过 | `test_bdd_47_…`：`agate_package.py` 缺失；`test_bdd_28_workspace…` 有意应绿 |
| `SUM` | 4 失败 / 7 通过 | 3 × 断言失败（无迁移提示、仍硬编码 `~/.agate/AGENTS.md`、BDD-51 提示逻辑）；1 × `ModuleNotFoundError: agate_package`（BDD-52） |
| `INST` | 21 失败 / 23 通过 | 21 × 断言失败：旧安装器仍 `git worktree add`（版本目录含整仓 / `.git`）、无 `--adopt`、软链守卫被 `L/` `L//` `L/.` `L/..` 绕过、`v0.73.0\n` 被放行、迁移文案缺入口；23 通过（既有 TAG0008 / TAG0032 / DEBT0034 + 有意应绿的 `L` 变体、非法版本字符串三例） |
| `UNINST` | 2 失败 / 6 通过 | `bdd25-1a / 1b` 因新形态由新安装器产出而失败；②③④⑤ 锁既有行为，有意应绿 |
| `HOOK` | 1 失败 / 8 通过 | `test_bdd_47_new_form_…`：`agate_package.py` 缺失；其余（含 2 条新增守卫）有意应绿 |
| `E2E`（e2e）/ `DISP`（dispatch_context_warning） | 全绿 | 仅夹具增拷；用例逐字不变 |

合计：本组 12 个文件共 250 个用例，146 红灯 / 104 有意应绿；A 组 `test_eng_n1_fixtures_that_copy_agate_common_also_copy_agate_package` 因本组夹具修改已转绿。**红灯 = "被测新行为 / 模块未实现"，无一为"断言与测试数据矛盾"（T075 教训）**。

**对照实现验证（防"测试与数据 / 设计矛盾"）**：在 scratchpad（`refB-1/`，不入仓库）依 P2 §3.2–§3.7 写了一份参考实现（`agate_package.py` 含 `make_work_dir / sweep_stale / recover_backups / swap_in / rollback_swap / snapshot_pointers / restore_pointers / discard_backup / copy_files`；新 `agate-pack-offline.py` / `install-offline.py`（含 `files` 对账、换位 + 兄弟安装器 `--adopt` + 回滚）；`agate-install.py`（`--adopt` / `--check --portable` / 软链守卫 / 事务化指针 / 卸载 prune）；`agate_common.py`（删 `use_legacy`、`symlink_base`、迁移提示）；`agate-resolve.py` / `agate-summary.py`；新 `install.sh`），用 `AGATE_ROOT` 与 `AGATE_TEST_SCRIPTS_SRC` 把本组测试指向它：**250 / 250 通过**（含 3 个读真实仓库 `install.sh` / 测试文件文本的静态用例：`test_bdd_29_install_sh_has_no_symlink_logic`、`test_bdd_30_install_sh_header_and_usage_…`、`test_bdd_30_test_files_…`——前两者对参考 `install.sh` 用同一判定逻辑单独验证通过）。验证中据此修正了 2 处**测试**缺陷（`test_lib_swap_in…` 回滚后旧目录内容断言与"首次换位写入 new.txt"矛盾）与发现 1 处**设计缺口**（DESIGN_GAP-B1，见 6.5）。

### 6.5 既有测试修改登记、DESIGN_GAP 与 P4 实现提示

**[DESIGN_GAP-B1]（需主 Agent 知悉 / 确认）**：P2 §6 T-10 / BDD-26 称既有 `test_bdd_3_reinstall_idempotent` 等"函数体不改且保持通过"，但 TAG0008 的三个用例断言的是**旧 git worktree 形态**：`test_bdd_2_version_dir_worktree_of_tag`（版本目录登记在 `repo/` worktree list 且 HEAD == tag 提交）、`test_bdd_3_reinstall_idempotent`（worktree list 中版本目录恰出现 1 次）、`test_bdd_6_uninstall_rejected_when_referenced`（拒绝卸载后版本目录仍登记在 worktree list）。新契约（D-1 git plumbing 构建器取代 `git worktree add`、BDD-22 只装本体）下版本目录**不再是 worktree**，这三条**不可能**在保持原断言的前提下通过（对照实现实测：3 条均失败于 `worktree list` 断言）。处置（最小、等价、可逆）：只替换这些**过时的 worktree 断言**为新形态等价判据（`bdd_2`：非 worktree、无 `.git`、内容取自 tag blob；`bdd_3`：二次安装后版本目录快照逐字节不变、不重复建、无遗留工作容器；`bdd_6`：被拒绝卸载的版本目录快照不变），其余语句 / 前半断言逐字不变；`test_bdd_2…` 因名字含 "worktree" 改名为 `test_bdd_2_version_dir_is_tag_body_not_worktree`。这属对 T-10 "test_bdd_3 函数体不改"的**有意例外**（受保护的是"不弱化"，此处是被新契约推翻的旧假设）。若主 Agent 不同意，须在 P2 另行裁决（例如改 T-10 或改设计），否则 P4 无法使这三条既有用例保持通过。

| 文件 | 修改 | 原因 / 依据 |
|------|------|-------------|
| `INST` | `_tag_upstream` 拷贝清单增 `agate_package.py`（存在才拷） | P2 §6 T-10 / eng N-1；A 组 `eng_n1` 守卫 |
| `INST` | `test_tag0032_bdd_5_…` 删除预置 `prep-repo` 与 `AGATE_REPO_DIR` env（断言未动） | BDD-30（P1 明示："对 AGATE_REPO_DIR 的引用与 pre-P4 legacy 分支快速失败注释一并清理"）；install.sh `--versions` 分支从不读它，删后仍绿 |
| `INST` | `test_bdd_2 / 3 / 6` 过时 worktree 断言替换（改名 1 处） | **DESIGN_GAP-B1**，见上 |
| `E2E` | `_tag_meta_upstream` 拷贝清单增 `agate_package.py`（存在才拷）；`_enter_version_layout` 去掉 `AGATE_REPO_DIR` env、`_prep_fastfail_repo` 改为占位（调用点原样保留，受保护用例 `test_tag0032_bdd_13/14` 函数体零改动） | T-10 / eng N-1；BDD-30 |
| `HOOK` | `_make_fake_root` 拷贝清单增 `agate_package.py`（存在才拷） | T-10 / eng N-1（批 E 追加验收） |
| `test_pre_commit_hook.py` | `test_agate_root_self_locate_worktree` 内与 `_build_probe_workflow_root` 两处拷贝循环增 `agate_package.py`（存在才拷） | T-10 / eng N-1（P2 点名 `:1235` `:1415`）；用例断言未动 |
| `test_dispatch_context_warning.py` | `_FAKE_SCRIPTS` 增 `agate_package.py`；拷贝循环仅对它容忍缺失 | T-10 / eng N-1 |
| `RES` | `test_bdd_30_legacy_symlink_direct_root` → 改写为 `test_bdd_27_symlink_home_fail_closed`；`test_debt0042_agate_home_legacy_symlink` → 改写为 `test_debt0042_agate_home_symlink_fail_closed`（fail-closed 断言，沿用原 fixture） | BDD-38 ①（软链直通解析行为被删除，断言相反）；撞名 `test_bdd_30*` 其余函数体零改动（本组未触及） |
| `OFF` | `_make_bundle` 改经真实 pack 入口 + sentinel；`test_bdd_27 / 28 / 28b / 29 / 29b` 的 mock `subprocess.run` 改 PATH pip shim、删 `.installed-version`、`--skip-python` → "`vX.Y.Z/python` 恒不存在"、copy-mode → 验证 `--adopt` 结果；`test_bdd_1_verify_checksums…` 样本文件名去"WORKFLOW.md"伪装 | BDD-11 ①、T-11（D-7 / R-9 / R-10）；`test_bdd_25 / 26`、`test_manifest_*_rejected`、R1 两用例断言逻辑未动 |
| `PACK` | `_fake_artifacts_side_effect` 等 mock 助手删除，`test_bdd_22 / 23 / 24 ×3` 改经真实 pack 入口 + pip shim（`bdd_24 wheel_missing` 用本地空 pip shim）；`test_bdd_22` 因依赖 POSIX shim 去掉 `windows_smoke`，`test_bdd_24_fail_tag_missing`（不依赖 pip）保留该标记 | BDD-11 ①、T-1 / T-11；Windows 冒烟净减 1（`test_bdd_25_platform_mismatch_reject` 标记保留，但其 `_make_bundle` 在 Windows 上 skip） |
| `RT` | `_fake_pack_artifacts` 删除；链路改真实 pack → sentinel → install → **resolve（新增，BDD-11 ③）** → 经根 scripts 卸载；`.installed-version` 断言删除；迁移锚点（`compute_sha256` 同一函数对象）保留 | BDD-11、T-11 / D-7 |

删 / 改名对账（供 BDD-48 的 D / A）：改名 3（`test_bdd_30_legacy_symlink_direct_root`、`test_debt0042_agate_home_legacy_symlink`、`test_bdd_2_version_dir_worktree_of_tag`），净删 0；本组新增测试函数 95 个（含上述 3 个改名后的新名）。

**P4 实现提示（测试对实现的隐含假设，显式写明以免转绿时误判）**：
1. **软链守卫须对"原始"基址判定**：`AGATE_HOME=L/..` 经 env 传入时，`agate_home()` 返回规范化路径会丢失"物理与文本解析不一致"的信息——`agate-install.py` / `install-offline.py` / `agate_common._resolve_version_info` 须对**未规范化的原始值**（env 原值 / `--dest-root` 参数）调用 `is_symlink_base`（T-14 五变体 × 四入口均断言 exit 1）。`install.sh` 对含 `..` 分量的基址直接拒绝（本组只断言 exit 1 + stderr 含 `..`，不断言三步片段）。
2. **T-16 注入方式**：`OFF::test_t16_*`（in-process `main`）对"涉及 dest_root 的第 N 次 `os.rename` / `os.replace`"注入 `OSError`：换位序列须为——已存在旧目录时第 1 次 rename = 旧目录 → 备份容器、第 2 次 = 新 pkg → 目标；全新安装时第 1 次 = pkg → 目标；且此前 dest_root 内不得有别的 rename（`shutil.move` 也经 `os.rename`，可用）。
3. **`--adopt` 失败注入用真实场景**：`current` 位置是真实目录（T-20）——要求 `_register` 先 `snapshot_pointers`、写 `latest` 后写 `current` 失败即 `restore_pointers`、OSError 转 stderr + exit 1（无 Traceback）；install-offline 在子进程非 0 时打印含"还原"的说明。
4. **库函数签名**取自 P2 §3.2：`make_work_dir(root, version) -> 容器路径`（容器内 `pkg/` 由调用方建）、`swap_in(container, final) -> 备份容器 | None`（备份容器内 `old/`、带 `kind=bak` 标记；换位后空工作容器被删除）、`rollback_swap(backup, final)`、`discard_backup(backup)`（拒绝方式不限：抛异常或静默忽略均可，测试只断言目录原样保留）、`snapshot_pointers / restore_pointers`（软链目标 / 文本内容 / 不存在三态）、`sweep_stale` / `recover_backups` 规则同 R-8（标记文件名 `.agate-installer-owned`、首行 `agate-package/1 kind=tmp|bak …`、前缀 `.agate-tmp-` / `.agate-bak-<ver>-`、`recover_backups` 版本缺失时改名挪回、存在时 stderr 提示备份容器名）。
5. **manifest**：`files`（排序的包集合相对路径）、登记根文件各一个文件组件（`path` == 文件名）、`source_ref`；`version` 恒严格 `vX.Y.Z`（fullmatch）。缺省 `--repo` = `AGATE_HOME/repo`；pack 不得写源仓库（bare 克隆快照前后逐项相同）。
6. **`install-offline` 对契约外顶层文件**（如 `extra.sh`）：不拷 + stderr 含该文件名的告警，仍 exit 0；对账不一致 / 软链成员 / 旧格式 → exit 1 且 dest 不变（`not dest.exists()`）。
7. **`agate-summary`**：root 为 None 且软链基址 → 追加含三步片段的提示行，输出 `AGATE_ROOT：（无可用 AGATE_ROOT）`；root 可解析 → `读 {root}/AGENTS.md`，且软链基址经 current 链解析（BDD-51）时**不**打印迁移提示。

### 6.6 P5 / P6 验收命令（一次性交付事实——不写成永久 pytest，避免日后合法修改假红）

| 判定 | 命令（工作区根，基线 `75a8102` = P1 启动 HEAD） | 期望 |
|------|--------------------------------------------------|------|
| BDD-6 既有两用例源码未改、`_protocol_root` 函数体零 diff | `python3 - <<'PY'`：对 `agate/tests/unit/test_agate_version_resolve.py` 的 `test_tag0032_bdd_6_meta_repo_resolve_returns_agate_subdir` / `test_tag0032_bdd_7_rootproto_resolve_semantics_unchanged` 与 `agate/scripts/agate_common.py::_protocol_root`，比较 `git show 75a8102:<路径>` 与工作区版本的 `ast.dump(FunctionDef)` | 全部相等 |
| BDD-18 ③ / BDD-38 ③ / T-10 受保护函数体 | 同上方法比较 `test_bdd_7`、`test_bdd_8`、`test_tag0032_bdd_3/4/13/14`、`test_debt0034_*`（`INST` / `E2E`）与全部名字前缀 `test_bdd_30` 的函数（除已改写的 `test_bdd_30_legacy_symlink_direct_root`）| 全部相等（已知例外：`test_tag0032_bdd_5`（BDD-30 清理）、`test_bdd_3`（DESIGN_GAP-B1））；P3 时点已核对：本组改动的函数集 = 6.5 表所列，无其它 |
| BDD-48 D / A 对账 | `bash agate/tests/scripts/count-tests.sh` + 6.5 末尾改名 / 新增计数 | `A − D ≥ 0` |
| BDD-26 既有用例仍绿 | `python3 -m pytest agate/tests/unit/test_agate_version_install.py agate/tests/integration/test_version_lifecycle_e2e.py -q` | 全绿 |

### 6.7 数据安全与隔离

[PROD_NOT_TOUCHED]

本组全部用例：`AGATE_HOME` / `HOME` / `--dest-root` / 合成 bare 仓库 / bundle 均在 `tmp_path` / `tmp_path_factory` 下；不触碰真实 `~/.agate`、开发 checkout（BDD-52 只对真实 HEAD 做 `materialize` 读取，写入落在 tmp；`_source_pollution` 只读 `git status`）、真实 origin（`install.sh` 用例的 PATH 前置 git 包装器**拦截任何 http(s) 克隆**）；不推 tag / 不发 Release；pip 一律 PATH shim，无网络。**无 `rm -rf`、无清空重建**：仅有的删除发生在测试自建的 tmp 拷贝内（T-19 missing-file 删 `agate/UPGRADING.md` 拷贝、T-6 把 tmp 拷贝里的成员换成软链）；软链回滚验证（BDD-36）用 `os.rename`，不删任何内容；仓库内无临时 / 备份 / 日志文件（新增文件仅：`test_agate_install_adopt.py`、`test_install_sh.py`、`test_protocol_root_dual_impl.py` 与上表 12 个既有测试文件的修改，及本小节）。

## 7. C 组

文件缩写：`UC` = `agate/tests/unit/test_upgrading_contract_doc.py`；`UL` = `agate/tests/unit/test_upgrading_lifecycle.py`（既有，已改 1 处）；`SD` = `agate/tests/unit/test_setup_agate_dir.py`；`DS` = `agate/tests/unit/test_doc_sweep.py`；`NLR` = `agate/tests/regression/test_no_legacy_residue.py`；`OOS` = `agate/tests/regression/test_tag0037_out_of_scope_untouched.py`；`PNG` = `agate/tests/integration/test_portable_no_git.py`；`OR` = `agate/tests/integration/test_offline_real_pack_resolve.py`。

### 7.1 范围与边界

BDD 范围（dispatch-context C）：1、3 ③、9（补 A/B 间的缺口，见对账）、17（无 git PATH 端到端，补 A 的 H3 与 B 的"不含文档命令部分"之间的缺口）、19、21、37、39、40、41、42、43、44、45、46，以及 38 ④、49 ④、50 ①（可判定且不易腐的部分）；BDD-20（真实 CI 实跑）、23（真实仓库实测）、48、49 ①②③、50 其余项、H-1 **不写 pytest**，改为 §7.5 的验收命令 + 判定。

**永久回归 vs 一次性交付事实（TAG0025 判据）的取舍**：

- `NLR`（BDD-37）是长期不变量（旧称只允许出现在有限白名单）→ 直接断言当前状态；白名单 W 12 项 / 清零集合 R 12 项照 P1 落成 `(路径, 理由)`；
- BDD-46 是一次性交付事实（"本任务不许碰这些文件"）→ **不**断言 `git diff 75a8102..HEAD`（别的任务日后合法改 hook 会使其假性变红），而断言**不可变历史证据**：区间内**主题含 `TAG0037` 的非合并提交**逐个 `diff-tree`；
- BDD-39 ⑤"历史版本节原文保留"→ 以不可变基线提交 `75a8102` 为参照逐节比对（历史节内容本就不再变）；
- BDD-50 ① CHANGELOG 断言取「`[0.73.0]` 段，若尚无则 `[Unreleased]` 段」→ 发版重命名后仍成立，下个版本累积不会使其变红；版本号 / badge 一致性交给 consistency 脚本（CHECK 7 / 13），不在 pytest 里写死版本号。

### 7.2 BDD → 测试映射

| BDD | 测试（文件::用例，方括号为参数子场景） |
|-----|----------------------------------------|
| BDD-1 (a)–(d) | `UC::test_bdd_1_exactly_one_contract_section_in_whole_document`、`…_a_version_root_tree_lists_all_entries`、`…_b_top_level_entry_set_and_violation_rule`、`…_c_body_directory_name_is_fixed`、`…_d_single_source_file_path`；P2 §3.1 增补：`…_states_install_state_vs_post_run_state`、`…_protocol_root_sentence_corrected`（订正"整仓形态协议根为 `<版本目录>/`"的错误表述）；库层见 A 组 §2 |
| BDD-3 ③ | `UC::test_bdd_3_3_contract_block_equals_boundary_lines`（契约小节里恰一个 `include/exclude/root-file` fenced 块 ⇄ `agate_package.boundary_lines()` 集合相等）；①② 归 A 组 |
| BDD-9 | `OR::test_bdd_9_real_pack_then_offline_install_resolves`、`OR::test_bdd_9_no_double_nesting_and_protocol_root_not_returned_verbatim`（真实 pack → bundle 内入口 install-offline → `agate-resolve.py`）；A 组 `TP` 的 H2 同构断言为互补证据 |
| BDD-17 | `PNG::test_bdd_17_test_path_really_has_no_git`（T-5 前提）、`PNG::test_bdd_17_documented_commands_run_without_git_and_produce_contract_layout`（UPGRADING 文档命令块逐条实跑，PATH 无 git）、`PNG::test_bdd_17_resolve_and_summary_work_without_git`、`PNG::test_bdd_17_check_portable_passes_without_git`；`UC::test_bdd_17_portable_section_command_block_shape`（文档命令块结构 + 完整性局限如实写明）；B 组 `test_agate_install_adopt.py` 覆盖不含文档命令的部分；A 组 `TP` H3 覆盖有 git 的三路径同构 |
| BDD-19 | `UC::test_bdd_19_no_zero_dependency_claim[README.md / README.zh-CN.md / agate/UPGRADING.md / agate/SETUP.md]`（4 参数，现状即绿：负向约束）、`UC::test_bdd_19_portable_section_declares_real_dependencies` |
| BDD-21 | `DS::test_bdd_21_checklist_verifies_release_and_its_assets`、`…_has_remediation_for_tag_pushed_but_release_missing`、`…_g5_final_verification_includes_release_existence`；P2 §3.6 增补：`DS::test_p2_release_checklist_recommends_tag_protection`；资产集合口径（T-13）见 A 组 `REL::test_bdd_13_5_build_produces_exactly_the_documented_assets`，不重复 |
| BDD-37 | `NLR::test_bdd_37_1_use_legacy_has_zero_hits_except_closed_debt_narrative`、`…_2_other_pattern_hits_are_subset_of_whitelist`、`…_3_clear_set_file_has_zero_hits[R 12 个文件各一]`、`…_4_original_p0_grep_has_no_residue_outside_whitelist`；自守卫（现状即绿）：`…_scan_scope_filter[13 例]`、`…_pattern_semantics_case_insensitive_and_no_collateral[9 例]`、`…_whitelist_and_clear_set_shape` |
| BDD-38 ④ | 既有 `UL::test_tag0032_bdd_10_update_commands_aligned_and_idempotent` 已按 P2 §6 / BDD-38 ④ 改写（见 §7.6）；改写后口径由 `UC::test_bdd_39_1_*` 承接 |
| BDD-39 ①–⑤ | `UC::test_bdd_39_1_lifecycle_table_is_single_layout_with_migration_steps`、`…_2_resolution_priority_is_three_layers`、`…_3_legacy_no_behavior_change_promise_rewritten`、`…_4_v0730_section_content`、`…_5_section3_history_note_and_history_sections_preserved` |
| BDD-39 ⑥⑦⑧⑨ | ⑥ `DS::test_bdd_39_6_readme_quick_start_enters_versioned_layout[README.md / README.zh-CN.md]`；⑦ `DS::test_bdd_39_7_adr_009_marked_as_superseded_by_v0730`（其余文件的旧称由 ⑨ 逐文件核对）；⑧ `DS::test_bdd_39_8_existing_tests_header_and_docstring_wording_updated`（`test_dsh_preset.py:222` 由 ⑨ 核对）；⑨ `NLR::test_bdd_37_3_*`（R 集合 12 个文件全部 0 命中） |
| BDD-40 | 静态 `DS::test_bdd_40_no_stale_protocol_root_paths_outside_history`、`…_handoff_template_uses_agate_dir_or_current_path`、`…_orchestrator_template_fallback_is_current_agate`；动态 `SD::test_bdd_40_summary_startup_advice_uses_resolved_root`（隔离布局跑 `agate-summary.py`，第 2 条启动建议 == `<解析出的根>/AGENTS.md` 且存在） |
| BDD-41 | `SD::test_bdd_41_agate_dir_command_has_no_legacy_fallback`（取值命令无 `\|\| echo "$HOME/.agate"`；对照表 ≤ 1 行）、`SD::test_bdd_41_agate_dir_command_resolves_current_and_fails_loudly_without_it`（隔离 HOME 实跑：`$AGATE_DIR == $HOME/.agate/current/agate` 且模板可读；`current` 缺失时明确失败提示且不落到 `$HOME/.agate`） |
| BDD-42 | `SD::test_bdd_42_claude_code_registration_commands_and_frontmatter`（不调用 claude CLI；链接可读、目标在隔离 AGATE_HOME 内、frontmatter `yaml.safe_load` 含 `name: orchestrator`、真实 `~/.agate` 元数据指纹不变） |
| BDD-43 | `SD::test_bdd_43_opencode_registration_and_debug_agent`（SETUP 字面命令建链接 → 真实 `opencode debug agent orchestrator`；`mode == "primary"`、`tools.task is True`；缺 CLI = FAIL，见 §7.9 G-1） |
| BDD-44 | `SD::test_bdd_44_dsh_links_and_summary_reports_no_drift`（SETUP DSH 命令块 = `mkdir -p` + 三条 `ln -sf` 实跑，`install-hook` 行不执行；三链接可读；`agate-summary.py` exit 0 且无漂移 / 未安装警告；既有 `test_dsh_preset.py` 字面命令锁定不动） |
| BDD-45 | `SD::test_bdd_45_codex_template_readable_and_multi_agent_enabled`（模板可读；真实 `codex features list` exit 0 且 `multi_agent` 行为 stable / true；不执行 `codex exec`；缺 CLI = FAIL） |
| BDD-46 | `OOS::test_bdd_46_task_commits_do_not_touch_out_of_scope_files`、`…_resolve_entry_semantics_unchanged_ignoring_comments_and_docstrings`、`…_resolve_hook_root_only_docstring_and_legacy_kwarg_may_change`、自守卫 `…_norm_helpers_ignore_comments_docstrings_and_kwarg_but_catch_semantic_changes`（负向约束，**现状即绿**，P4 误触受保护文件才转红） |
| BDD-49 ④ | `DS::test_bdd_49_4_new_scripts_registered_in_scripts_readme[agate_package.py / agate-release.py]`；①②③ 为命令验收（§7.5） |
| BDD-50 ① | `UC::test_bdd_50_1_changelog_marks_breaking_and_points_to_migration_guide`；其余为 P8 命令 / 人工验收（§7.5） |

### 7.3 覆盖对账（BDD 1–52 → 测试文件；A 组见 §2，B 组以其 dispatch 范围 + `P3-dispatch-context-test-designer-B.md` 为准，B 组落地映射见 §6）

| BDD | 归属 / 文件 | BDD | 归属 / 文件 |
|-----|-------------|-----|-------------|
| 1 | A 库层（`PKG`/`REL`）+ **C** `UC` | 27 | B（`test_agate_version_resolve.py`，T-14 参数化） |
| 2 | A `PKG` / `TP` | 28 | B（`test_agate_version_resolve.py`，`inspect.signature`） |
| 3 | A ①②（`PKG`）+ **C** ③（`UC`） | 29 | B（`test_install_sh.py`） |
| 4 | A（`TP`） | 30 | B（`test_install_sh.py` + 两既有文件清理） |
| 5 | B（旧形态 fixture：`test_agate_version_resolve.py` / e2e） | 31 | B（`test_install_sh.py`，T-14） |
| 6 | B（`test_agate_version_resolve.py`，既有 tag0032_bdd_6/7 零改动 + 新增优先级用例） | 32 | B（`test_agate_version_install.py`，T-14） |
| 7 | B（同上，共存） | 33 | B（`test_install_offline.py`，T-14） |
| 8 | B（`regression/test_protocol_root_dual_impl.py`） | 34 | B（`test_agate_summary.py`） |
| 9 | A（`TP` H2 同构）+ **C** `OR`（直接用例，补可追溯性） | 35 | B（DEBT0034 跨入口比对扩展） |
| 10 | B（`test_install_offline.py`） | 36 | B（迁移三步实跑） |
| 11 | B（三处假 bundle 助手 + sentinel + 红灯回放） | 37 | **C** `NLR` |
| 12 | B（`test_install_offline.py`） | 38 | B ①②③ + **C** ④（`UL` 改写 + `UC`） |
| 13 | A（`WF` / `REL`） | 39 | **C** ①–⑤ `UC`，⑥⑦⑧ `DS`，⑨ `NLR` |
| 14 | A（`REL`） | 40 | **C** `DS` 静态 + `SD` 动态 |
| 15 | A（`REL` / `PKG`） | 41 | **C** `SD` |
| 16 | A（`REL`） | 42–45 | **C** `SD`（43 / 45 缺 CLI = FAIL，见 G-1） |
| 17 | **C** `PNG` + `UC` 命令块结构；A 的 H3；B 的 adopt（非文档部分） | 46 | **C** `OOS`（+ §7.5 人工等价命令） |
| 18 | B（`test_agate_install_adopt.py`） | 47 | B（既有 hook 用例 + 回归） |
| 19 | **C** `UC` | 48 | 命令验收（§7.5，P5 报告 D/A 对账） |
| 20 | A 静态契约（`WF`）；真实 CI 实跑 = P5/P6（§7.5，需用户当次许可） | 49 | ④ **C** `DS`；①②③ 命令验收（§7.5） |
| 21 | **C** `DS`；资产集合 A `REL` | 50 | ① **C** `UC`；②–⑥ P8 命令 / 人工（§7.5） |
| 22 | A（`PKG` 库层 + `TP` H1）+ B（`test_agate_version_install.py` 安装侧） | 51 | B（`test_agate_version_resolve.py` ① / `test_agate_version_install.py` ②） |
| 23 | A（`PKG` 合成 / v0.72.0 基线）；真实仓库实测 = P5/P6（§7.5） | 52 | B（包内脚本冒烟，含 C-2 两种调用形态） |
| 24 | A ②（`PKG` / `REL`）+ B ①（安装器端到端） | | |
| 25 / 26 | B（`test_agate_install_uninstall.py` / `test_agate_version_install.py`） | | |

对账结论：**A、B 的显式范围之间仅发现 2 处缺口并补测**——BDD-9（A 的 §2 与 B 的范围均未列其编号，仅靠 `TP` H2 同构隐含覆盖 → 补 `OR`）；BDD-17（A 的 H3 用带 git 的 PATH，B 声明"不含文档命令部分" → "在无 git 的 PATH 下逐条实跑文档命令"无人覆盖 → 补 `PNG`）。其余 BDD 均有归属；B 组的实际落地映射以 §6 为准，若 §6 出现"某 BDD 无用例"以 §6 为准回退给 B 组补。

### 7.4 各批 `tests_filter`（C 组回填；批次沿用 P2 §5）

| 批 | 命令 | 说明 |
|----|------|------|
| F1a-docs-upgrading | `python3 -m pytest agate/tests/unit/test_upgrading_lifecycle.py agate/tests/unit/test_upgrading_contract_doc.py -q` | 依赖 A（`boundary_lines()`，BDD-3 ③）；批内即可全绿（`UC` 读 UPGRADING / CHANGELOG，不依赖 F2）。 |
| F1a 波次末（BDD-17 / 4 H3） | `python3 -m pytest agate/tests/integration/test_portable_no_git.py agate/tests/integration/test_install_three_paths.py::test_bdd_4_all_three_paths_produce_same_structure_including_portable -q` | 依赖 A / B1b（`--adopt`、`--check --portable`）/ C1（build）/ F1a 文档命令块。 |
| F2-docs-sweep | `python3 -m pytest agate/tests/unit/test_setup_agate_dir.py agate/tests/unit/test_doc_sweep.py -q` | BDD-40 动态用例还依赖批 E 的 `agate-summary.py`；BDD-43 / 45 需 `opencode` / `codex` 在 PATH（本机已装，耗时约 15 s）。 |
| BDD-37 波次末 | `python3 -m pytest agate/tests/regression/test_no_legacy_residue.py -q` | 依赖 E（`use_legacy` 删除）、F1a / F2（R 集合 12 文件改写，含 `test_dsh_preset.py` 注释）、B（W 内测试文件无新增非白名单旧称）——只能在全部代码 / 文档批之后转绿。 |
| B2 批（BDD-9） | `python3 -m pytest agate/tests/integration/test_offline_real_pack_resolve.py -q` | 依赖 A、B2（新 pack / 新 install-offline / `--adopt`）、E（`compute_sha256` 字节码免疫）。 |
| 全程守卫（BDD-46） | `python3 -m pytest agate/tests/regression/test_tag0037_out_of_scope_untouched.py -q` | 现状即绿；每批提交后都应保持绿。 |

C 组整体：`python3 -m pytest agate/tests/unit/test_upgrading_contract_doc.py agate/tests/unit/test_upgrading_lifecycle.py agate/tests/unit/test_setup_agate_dir.py agate/tests/unit/test_doc_sweep.py agate/tests/regression/test_no_legacy_residue.py agate/tests/regression/test_tag0037_out_of_scope_untouched.py agate/tests/integration/test_portable_no_git.py agate/tests/integration/test_offline_real_pack_resolve.py -q`

### 7.5 非 pytest 的验收命令与判定（二值；证据由 P5 / P6 留存）

| BDD | 命令 | 判定 |
|-----|------|------|
| 20（P6，需用户当次许可推测试 tag） | 按 P2 §11：`gh -R "$REPO" run list --workflow=release.yml` / `gh -R "$REPO" release view v0.73.0-tagtest.N` / 逐资产下载核对 / 清理 | ① run `conclusion == success`；② prerelease + 首行标注 + 资产名 tag 原样；③ 本体 asset 与本地 `agate-release.py build` 逐成员字节一致、offline `manifest.version` 严格 `v0.73.0` 且 sha256 通过；④ 清理后 release / 远端 tag / 本地 tag 零残留且 `git describe --tags --abbrev=0` 不返回它 |
| 23（P5 / P6） | 隔离 `AGATE_HOME` 下对 v0.72.0 或 HEAD 执行 `agate-install.py latest`，`du -sb <AGATE_HOME>/vX.Y.Z` 与 `agate_package` 求和 B 比较 | `S ≤ 1.25 × B`（v0.72.0：`S ≤ 2,331,089 B`） |
| 46（人工等价） | `git diff --stat 75a8102..HEAD -- agate/scripts/pre-commit-gate.sh agate/scripts/pre-commit-gate.py agate/scripts/commit-msg-self-gate.sh agate/scripts/commit-msg-self-gate.py agate/scripts/pre-push-gate.sh agate/scripts/pre-push-gate.py SELF-GATE.md agate/scripts/install-hook.py agate/scripts/check-state-yaml.py agate/scripts/agate-state-yaml-check.py agate/rules/` | 输出为空；`agate/scripts/resolve-entry.py` 的 diff 仅含注释 / docstring（`OOS` 已用 AST 归一化自动判定）。`install-hook.py` 层次差别（协议根 vs 版本根基址）只在 UPGRADING 点明——人工核对，不写 pytest（措辞不可判定） |
| 48（P5） | `python3 -m pytest agate/tests/ --reruns 1 -n auto`；`bash agate/tests/scripts/count-tests.sh`；删除 / 新增用例对账：`git diff 75a8102..HEAD -U0 -- agate/tests \| grep -cE '^-(async )?def test_'` 与 `… '^\+(async )?def test_'` | failed 0；`passed ≥ 1842`；`A − D ≥ 0`（4 个真旧软链测试为"改写"而非净删）；skipped：本机 = 0 新增（`opencode` / `codex` 在 PATH）；**GitHub Actions 上 `SD` 的 BDD-43 / 45 会 skip（+2），见 G-1** |
| 49 ①②③（P5） | `python3 agate/scripts/check-protocol-consistency.py --strict-errors-only`；`~/.venvs/agate-dev/bin/ruff check agate/`；`shellcheck -S warning install.sh agate/scripts/*.sh` | 0 ERROR / 0 error / 0 warning（`check-protocol-consistency` 的 count-tests 数字文档漂移属 P4 / P5 同步，P3 不改文档） |
| 50 ②–⑥（P8） | ① 三处版本一致 + CHECK 7 / 13：`git tag v0.73.0` **之后**跑 consistency；② README badge 不为 1.0；③ PR 描述如实列出 release workflow 触发 `on: push tags v*` 与权限 `contents: write` 及 BDD-20 实测的连带触发 workflow；④ `roadmap.md` RM-AG0066 = done；⑤ HANDOFF-TAG0037.md 归档到 `agate-workspace/archived/plans/`；⑥ v0.73.0 推送后 `gh release view v0.73.0` 含本体 + 两平台 offline（+ SHA256SUMS） | 全部满足；⑥ 为 release workflow 首次真实运行 |
| H-1（P6 人工，非 BDD） | `claude --agent orchestrator -p "echo test"`（联网 / 真实凭据；仅 AGATE_HOME / `$AGATE_DIR` 指隔离布局） | 选中 orchestrator 并返回、不报 `Failed to parse agent`；结果记 P6 证据 |

### 7.6 修改既有测试登记

| 文件 | 修改 | 依据 |
|------|------|------|
| `agate/tests/unit/test_upgrading_lifecycle.py` | `test_tag0032_bdd_10_update_commands_aligned_and_idempotent`：删除旧布局侧断言（`"git pull" in sec` 与"legacy 布局更新指令"注释 / 断言消息），docstring 说明改写原因，并把 `install-hook.py` 断言消息去旧布局措辞；**保留** 版本布局侧 `agate-install latest` + `幂等` 与 hook 判定口径断言。其余 6 个用例函数体零改动。 | P1 BDD-38 ④ / P2 §5 F1a 批（"允许调整"）：UPGRADING 对照表去旧布局列，该断言属被删除语义。未弱化任何仍成立的断言；改后 7 / 7 通过（现状与落地后均绿）。 |

### 7.7 红灯自证（`PYTHONDONTWRITEBYTECODE=1 python3 -m pytest <file> -q --no-header -p no:cacheprovider`）

| 文件 | 用例数 | 失败 / 通过 | 失败原因（均为 B 类：断言失败；无 SyntaxError、无第三方 import 失败、无 fixture ERROR） |
|------|--------|-------------|--------------------------------------------------------------------------------------|
| `unit/test_upgrading_contract_doc.py` | 20 | 16 / 4 | UPGRADING 尚无契约 / portable / `### v0.73.0` 节，对照表仍有旧布局列，`[Unreleased]` 无 BREAKING，`agate_package` 缺失不会在此抛（`UC` 用例先断言"契约小节存在"）；4 个有意应绿 = BDD-19 四文件"零依赖"负向约束 |
| `unit/test_upgrading_lifecycle.py` | 7 | 0 / 7 | 既有文件，改后 7 / 7 绿（有意应绿，见 §7.6） |
| `unit/test_setup_agate_dir.py` | 7 | 3 / 4 | 3 红：SETUP 取值命令仍含旧 fallback（×2）、`agate-summary.py` 仍硬编码 `~/.agate/AGENTS.md`（BDD-40）。4 个有意应绿 = BDD-42–45（"接入链路无回归"守卫：对既有布局与旧取值命令同样成立；`opencode` / `codex` 在本机 PATH，真实实跑 ≈ 13 s） |
| `unit/test_doc_sweep.py` | 13 | 13 / 0 | README 仍写旧装法、ADR-009 无取代注记、`test_agate_version_resolve.py` 头注含旧称、两处遗留 `~/.agate` 协议根路径、发布清单无 Release 步骤、scripts/README 未登记新脚本 |
| `regression/test_no_legacy_residue.py` | 38 | 15 / 23 | 残留未清零（命中 23 个文件 = R 12 + W 11）：`use_legacy` 仍在 `agate_common.py`、R 集合 12 文件各 1 红、非白名单命中 ×1、原口径残留 ×1；23 个有意应绿 = 扫描器自守卫（范围过滤 13 + 模式语义 9 + 白名单形态 1） |
| `regression/test_tag0037_out_of_scope_untouched.py` | 4 | 0 / 4 | 负向约束，现状即绿（有意应绿） |
| `integration/test_portable_no_git.py` | 4 | 3 / 1 | `agate-release.py` 尚不存在 → build rc=2 → 断言失败；1 有意应绿 = 受限 PATH 确实无 git（前提自守卫） |
| `integration/test_offline_real_pack_resolve.py` | 2 | 2 / 0 | 旧 pack 产物 `bundle/agate/agate/scripts` 双层嵌套 → bundle 内 `install-offline.py` 不存在 → 断言失败（P0 BUG 复现） |

合计 95 用例：**52 红灯（均 B 类）/ 43 有意应绿**（BDD-19 ×4、既有 `UL` ×7、BDD-42–45 ×4、`NLR` 自守卫 ×23、`OOS` ×4、`PNG` 前提 ×1）。`ruff check`（`~/.venvs/agate-dev/bin/ruff`）对本组 8 个文件全绿。

**对照实现验证（防"测试与数据 / 设计矛盾"，T075 教训）**：在 scratchpad `c-ref-1/repo`（`git clone --local` 当前工作树，不入仓库）里按 P2 §3.1 / §3.5 / §3.7 / §3.8 手写了一份**参考落地**（UPGRADING 契约 / portable / `### v0.73.0` 小节 + 对照表 / 解析优先级表改写、SETUP `$AGATE_DIR` 命令、README / ADR / 模板 / AGENTS.md 发布清单 / scripts README 改写、`agate-summary.py` 启动建议、R 集合旧称清零），并叠加 A 组的参考脚本（`agate_package.py` / `agate-release.py` / 新 pack / `install-offline.py` / `--adopt`；`--check --portable` 仅补最小改动）：本组 8 个文件 **95 / 95 通过**——每条断言与 P2 契约自洽、可被正确实现满足。验证中发现并修正 2 个**测试自身缺陷**：① `UC` 历史节数量下限写成 40（基线实测 34）→ 改 ≥ 30；② `PNG` 用裸 `bash` 在受限 PATH 下无法解析 → 改绝对路径（并在受限 PATH 放入 `bash`，因 `--check` 把 bash 列为必备项，BDD-17 的变量是"无 git"而非"无 bash"）。

### 7.8 数据安全与隔离

全部在 `tmp_path` / `tmp_path_factory` 内；`SD` 的隔离布局是当前工作树 `agate/`（不含 `tests/`）的**拷贝**（不写工作树）；BDD-43 / 45 的 HOME 保持真实仅供 CLI 读自身配置，AGATE_HOME / `$AGATE_DIR` 指隔离布局，前后以**只读 lstat 元数据指纹**核对真实 `~/.agate` 不变（不读文件内容、不写、不跟随软链）；文档命令实跑前经白名单（`mkdir` / `ln` / 注释 / `AGATE_DIR=` 赋值 / `test`；`install-hook` 行跳过），含其它命令即拒绝执行；`OOS` / `NLR` / `DS` / `UC` 只读（`git ls-files` / `git log` / `git show` / 读文件）；不推 tag、不发 Release；无 `rm -rf`、无删除既有文件；仓库内新增 / 修改仅：本节列出的 7 个新增测试文件、`test_upgrading_lifecycle.py` 的 1 处改写、本节自身（含 `P3-progress.md` 追加）。

### 7.9 需主 Agent 知悉 / 跨组约束

- **G-1（需主 Agent / 用户裁决，[DESIGN_GAP]）P1 BDD-43 / 45"缺 CLI 于 PATH 判 FAIL、不得跳过"与既有 CI 冲突**：`protocol-tests.yml`（GitHub Actions 通用 runner）没有 `opencode` / `codex`，而 BDD-13 ⑥ 又禁止改现有 4 个 workflow。本组实现：**仅 `GITHUB_ACTIONS=true` 时缺 CLI 记为 skip（显式原因）；本地 / P5 / P6 缺 CLI 仍 `pytest.fail`**。若按字面要求"任何环境缺 CLI 都 FAIL"，则 CI 必红。副作用：CI 口径 `skipped ≤ 2`（BDD-48）在 Actions 上会 +2；本机 P5 不受影响。请确认此折中，或改判据（例如 43 / 45 只在 P6 人工跑）。
- **G-2 命名 / 结构约定（P4 文档批须遵守，否则本组红灯不会转绿）**：UPGRADING 契约小节标题含「结构契约」且全文恰一处、位于「版本管理生命周期」节内；边界 fenced 块每行以 `include` / `exclude` / `root-file` 起头且**只此一块**；portable 小节标题含「portable 安装」、第一个 bash 代码块即可执行的验收命令（A 组 H3 与 `PNG` 共用）；`### v0.73.0` 标题以 `v0.73.0` 起头；SETUP「先取协议根路径」节第一个 bash 块只含 `AGATE_DIR=` 赋值 / `test` / 注释；四平台命令块只含 `mkdir` / `ln`（DSH 另含被跳过的 `install-hook` 行）。
- **G-3 旧称字面量约束（对 A / B 及后续 P4 新增文件同样生效）**：`NLR` 对**所有被 git 跟踪的文件**扫描四种旧称；新增文件（测试 / 脚本 / 文档）不得直接写出 `use_legacy`、`legacy[ _-]?(软链|symlink|layout)`、`单软链`、`软链兜底`，除非该文件在 W 白名单内；测试需引用时用字符串拼接构造（本组已如此）。`DS::test_bdd_40_no_stale_protocol_root_paths_outside_history` 同理禁止直接写出 `~/.agate/(AGENTS|orchestrator-template|WORKFLOW|assets|phase-cards|rules)` 字面量（历史叙事文件白名单：`CHANGELOG.md`、`agate/UPGRADING.md`、`agate/adr.md`、`tech-debt.md`、`worktree-dogfooding-guide.md` 的反例说明）。P3 已核对 A 组 4 个测试文件 + `helpers_tag_repo.py` 与本组文件均无命中。
- **G-4 BDD-39 ⑧ 依赖 B 组文件**：`test_agate_version_resolve.py` 头注（前 10 行）与 `test_resolve_terminal_failure_fail_closed` docstring 须去掉旧布局字样——这是 P1 明确列出的改写项，`DS` 会拦截；B 组在改写 BDD-30 用例时请一并处理（该文件在 W 白名单内，故 `NLR` 不会替它兜底）。
- **G-5 BDD-46 依赖提交主题约定**：`OOS` 以"主题含 `TAG0037`"识别本任务提交；P4 各批提交须沿用 `wf(TAG0037-…)` / `feat(TAG0037-…)` 等含任务号的主题（项目既有约定），否则该用例对未标注的提交是空检；§7.5 的 `git diff 75a8102..HEAD` 人工命令是等价的兜底。
- **G-6 BDD-17 的 PATH 含 bash**：见 §7.7 对照实现验证第 ② 点；若 P1 意图"PATH 内连 bash 都没有"，请回复，需连同 `--check --portable` 的必备项口径（P2 §3.3）一起澄清。
- **G-7 BDD-3 ① ② / 23 / 20 等**仍以 A 组 §2 为准；本组未改动 A / B 组任何内容。

## 8. 总对账与裁决记录

> P3 收尾（A / B / C 三组落地后）由 test-designer 对 **BDD-1..52** 逐条与实际测试函数名 / docstring 交叉核对（脚本按 `bdd_N` / `BDD-N` 检索各文件）；核对结果：**无 BDD 缺测试**；48、49 ①②③、50 ②–⑥、20（真实 CI 实跑）、23（真实 `agate-install.py` 实测）、6 / 38 ③ / 46 的"函数体零 diff"命令面是**一次性交付事实**，按 §6.6 / §7.5 以 P5 / P6 / P8 命令验收，不写永久 pytest（TAG0025 判据）。一处订正：§2 的 BDD-2 行曾列 `TP::test_bdd_4_online_install_matches_library_package_set`，该用例实际归 BDD-4 ① / BDD-22，BDD-2 的测试以 `PKG` 为准。

### 8.1 BDD → 测试文件总表（相对 `agate/tests/`）

| BDD | 测试文件（主承载，用例见 §2 / §6.2 / §7.2） | 组 |
|-----|--------------------------------------------|----|
| 1 | `unit/test_upgrading_contract_doc.py`（文档面 a–d）；`unit/test_agate_package.py`、`unit/test_agate_release.py`（常量 / 边界行 / boundary CLI） | C + A |
| 2 | `unit/test_agate_package.py` | A |
| 3 | ①② `unit/test_agate_package.py`；③ `unit/test_upgrading_contract_doc.py` | A + C |
| 4 | `integration/test_install_three_paths.py`（H3 用例依赖 F1a，波次末转绿） | A |
| 5 | `unit/test_agate_version_resolve.py` | B |
| 6 | `regression/test_protocol_root_dual_impl.py`；"既有用例源码未改 / 函数体零 diff"= §6.6 命令 | B |
| 7 | `unit/test_agate_version_resolve.py` | B |
| 8 | `regression/test_protocol_root_dual_impl.py` | B |
| 9 | `unit/test_install_offline.py`、`unit/test_agate_pack_offline.py`、`integration/test_offline_real_pack_resolve.py`；互补 `integration/test_install_three_paths.py`（H2） | B + C + A |
| 10 | `unit/test_install_offline.py`、`unit/test_agate_pack_offline.py` | B |
| 11 | `unit/test_install_offline.py`、`unit/test_agate_pack_offline.py`、`regression/test_offline_bundle_roundtrip.py` | B |
| 12 | `unit/test_install_offline.py` | B |
| 13 | `unit/test_release_workflow.py`（①–④ ⑥）、`unit/test_agate_release.py`（⑤ 资产名） | A |
| 14 | `unit/test_agate_release.py` | A |
| 15 | `unit/test_agate_release.py`、`unit/test_agate_package.py` | A |
| 16 | `unit/test_agate_release.py` | A |
| 17 | `integration/test_portable_no_git.py`、`unit/test_agate_install_adopt.py`；H3 见 BDD-4 | C + B |
| 18 | `unit/test_agate_install_adopt.py` | B |
| 19 | `unit/test_upgrading_contract_doc.py` | C |
| 20 | 本地可测部分 `unit/test_release_workflow.py`、`unit/test_agate_release.py`；真实 CI 实跑 = P6（§7.5，需用户当次许可） | A |
| 21 | `unit/test_doc_sweep.py`；资产集合口径 `unit/test_agate_release.py` | C + A |
| 22 | `unit/test_agate_package.py`（库层）、`integration/test_install_three_paths.py`（H1）、`unit/test_agate_version_install.py`（安装侧） | A + B |
| 23 | `unit/test_agate_package.py`；真实 `agate-install.py` 实测 = P5 / P6 | A |
| 24 | ② `unit/test_agate_package.py`、`unit/test_agate_release.py`；① `unit/test_agate_version_install.py`、`unit/test_agate_pack_offline.py` | A + B |
| 25 | `unit/test_agate_install_uninstall.py` | B |
| 26 | `unit/test_agate_version_install.py`、`unit/test_install_sh.py` | B |
| 27 | `unit/test_agate_version_resolve.py` | B |
| 28 | `unit/test_agate_version_resolve.py`、`unit/test_agate_workspace_resolve.py` | B |
| 29 | `unit/test_install_sh.py` | B |
| 30 | `unit/test_install_sh.py` | B |
| 31 | `unit/test_install_sh.py`（T-14） | B |
| 32 | `unit/test_agate_version_install.py`（T-14）、`unit/test_agate_install_adopt.py` | B |
| 33 | `unit/test_install_offline.py`（T-14） | B |
| 34 | `unit/test_agate_summary.py` | B |
| 35 | `unit/test_agate_version_install.py` | B |
| 36 | `unit/test_install_sh.py` | B |
| 37 | `regression/test_no_legacy_residue.py`、`unit/test_doc_sweep.py` | C |
| 38 | ①②③ `unit/test_agate_version_resolve.py`、`unit/test_agate_version_install.py`（③ 命令面 §6.6）；④ `unit/test_upgrading_lifecycle.py`、`unit/test_upgrading_contract_doc.py` | B + C |
| 39 | `unit/test_upgrading_contract_doc.py`（①–⑤）、`unit/test_doc_sweep.py`（⑥–⑧）、`regression/test_no_legacy_residue.py`（⑨） | C |
| 40 | `unit/test_doc_sweep.py`、`unit/test_setup_agate_dir.py`、`unit/test_agate_summary.py` | C + B |
| 41 | `unit/test_setup_agate_dir.py` | C |
| 42 | `unit/test_setup_agate_dir.py` | C |
| 43 | `unit/test_setup_agate_dir.py`（G-1 CI 例外见 8.2 (b)） | C |
| 44 | `unit/test_setup_agate_dir.py` | C |
| 45 | `unit/test_setup_agate_dir.py`（G-1 CI 例外见 8.2 (b)） | C |
| 46 | `regression/test_tag0037_out_of_scope_untouched.py`（不可变历史证据）；人工等价命令 §7.5 | C |
| 47 | `unit/test_hook_resolve_entry.py`、`integration/test_pre_commit_hook.py`、`unit/test_agate_workspace_resolve.py`、`regression/test_tag0037_out_of_scope_untouched.py` | B + C |
| 48 | 无 pytest：P5 gate（全量、D / A 对账，§7.5） | P5 |
| 49 | ④ `unit/test_doc_sweep.py`；①②③ P5 命令（consistency / ruff / shellcheck，§7.5） | C + P5 |
| 50 | ① `unit/test_upgrading_contract_doc.py`；②–⑥ P8 命令 / 人工（§7.5） | C + P8 |
| 51 | `unit/test_agate_version_resolve.py`（①）、`unit/test_agate_summary.py`、`unit/test_agate_version_install.py`（②） | B |
| 52 | `unit/test_agate_summary.py`（含 C-2 两种调用形态） | B |

共享夹具与保护用例：`helpers_tag_repo.py`（A，被 B / C 复用）；`unit/test_agate_package.py::test_eng_n1_*`（跨组，B 组修改既有夹具后已转绿）。

### 8.2 裁决记录（主 Agent 裁决，P3 收尾）

**(a) [DESIGN_GAP: B1 已采纳为对 P2 §6 T-10 的合法例外]**　既有 `test_agate_version_install.py::test_bdd_2 / 3 / 6`（TAG0008 时代）断言旧 `git worktree` 形态（版本目录登记在 `repo/` worktree list、HEAD == tag 提交 / 恰出现 1 次 / 拒绝卸载后仍登记），新契约（D-1：git plumbing 构建器取代 `git worktree add`；BDD-22：只装本体）下版本目录不再是 worktree，这三条无法在保持原断言下成立。处置：仅替换过时的 worktree 断言为新形态等价判据（其余语句逐字不变；`test_bdd_2_version_dir_worktree_of_tag` 改名 `test_bdd_2_version_dir_is_tag_body_not_worktree`）。详见 §6.5。裁决：**接受**，作为 T-10「函数体不改」的有意例外，非"弱化断言"。**P7 须补一条配对的 REVIEWED 条目**（DESIGN_GAP ↔ REVIEWED 配对，P7 一致性核对时检查）。

**(b) [G-1 已采纳]**　BDD-43 / 45（opencode / codex 接入命令实跑）**仅当 `GITHUB_ACTIONS=true` 且对应 CLI 缺失时**才 skip（显式原因）；本地、P5、P6 运行缺 CLI 仍判 FAIL（`pytest.fail`）。理由：GitHub 通用 runner 未预装这两个 CLI，而修改现有 workflow 属本任务 out-of-scope（BDD-13 ⑥）。副作用：Actions 上 `skipped` 口径 +2，本机 P5 不受影响。已在 P1-requirements.md 的 BDD-43 / 45 处以 `[BASELINE_CHANGE: ...]` 注解记录（仅注解，未改 Given / When / Then）。
