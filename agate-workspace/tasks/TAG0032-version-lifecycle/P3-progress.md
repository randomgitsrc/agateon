
## P3 test-designer 进度（trace TAG0032-P3-20260907）

### 输入文件已读
- 角色定义 test-designer.md：BDD→测试 1:1，红灯 B 类，永久回归判据（长期不变量 vs 一次性事实）
- P3-dispatch-context：14 条 BDD→测试文件映射表；BDD-9 无独立用例；命名前缀 test_tag0032_bdd_N_
- P1-requirements.md：§3 14 条 BDD 全文（BDD-1~5 断点一 / BDD-6~9 断点二 / BDD-10~12 文档面 / BDD-13~14 端到端）
- P2-design.md：决策 A1（_protocol_root 增量探测，agate_common.py）+ 决策 B1（根 scripts/ copytree 副本）；M1-M15 落点；§4.4 元仓库 fixture 形态
- conftest.py：run_cli / python_exe / bash / git_repo(=GitRepo(tmp_path)) / agate_scripts / py_path fixture 契约
- test_agate_version_install.py：_run_install（HOME+USERPROFILE+AGATE_REPO_URL）/ _tag_upstream（已是 agate/scripts/ 元仓库形态，仅 README）
- test_agate_version_resolve.py：_make_home / _resolve_env / _write_version_decl / test_bdd_30 os.symlink→skip 模式
- test_hook_resolve_entry.py：_STUB_GATE marker 模式 / _make_home 建 vX/scripts/ 直含
- test_pre_commit_hook.py：integration 层结构参考
- agate_common.py：_resolve_version_info L166（.agate-version ok 分支 L180-183 + current 链分支 L188-190）——_protocol_root 插入点
- agate-install.py：_cmd_install L269-288（M1 守卫首行 + M2 副本落地）；当前 `latest` 非法版本号→exit2；无 --help 根副本
- resolve-entry.py:49 gate_path = os.path.join(root, "scripts", gate_py)——元仓库形态取不到→exit1
- install.sh：无 --versions 分支；当前忽略 $1，走 clone/pull

### 当前行为核对（红灯依据）
- BDD-1/2：agate-install.py 无 os.path.islink 守卫 → 软链布局 install 会 exit 0（应 exit≠0）
- BDD-4/5：agate-install.py 全程不建根 ~/.agate/scripts/
- BDD-6/8：_protocol_root 不存在 → resolve 返回 vdir（非 vdir/agate）
- BDD-10/11/12：UPGRADING.md 无「版本管理生命周期」节（现有节：## 1 通用升级步骤 / ### v0.50.0）
- BDD-13/14：install.sh 无 --versions；agate-install.py latest 非法版本号 exit 2

### 已写测试文件
- test_agate_version_install.py（追加 BDD-1~5）
- test_agate_version_resolve.py（追加 BDD-6/7 + _make_home_meta/_make_home_rootproto）
- test_hook_resolve_entry.py（追加 BDD-8 meta fixture）
- test_upgrading_lifecycle.py（新增 BDD-10/11/12 + BDD-4 判据3）
- integration/test_version_lifecycle_e2e.py（新增 BDD-13/14 + _tag_meta_upstream）

### 自跑红灯确认（2026-09-07）
- `pytest <5 文件> -k tag0032` => 18 failed, 25 deselected in 1.11s
- 逐条 B 类：全 AssertionError（install 无守卫 / 根 scripts 未建 / _protocol_root helper 未实现 /
  resolve 返回 vdir / UPGRADING 无生命周期节 / README 无 install.sh --versions / install.sh 无 --versions 分支）
- 无 A 类（无 SyntaxError / 无第三方 import 失败）；py_compile 全过
- `-k "not tag0032"` => 25 passed（TAG0008 既有用例无回归）
- `pytest agate/tests/ --co` => 1508 tests collected（无收集错误）
- e2e 首步 install.sh --versions exit 1 快速失败（AGATE_REPO_DIR 预置 git 仓库，不触网络）

### 产出
- P3-test-cases.md 已写 + agate-md-field-set.py 填 test_code_dir=agate/tests/（frontmatter）
- [PROD_NOT_TOUCHED] 主 checkout 未动；隔离 HOME 全程 tmp_path
