# BDD-20 real CI evidence (verifier g1, 2026-09-20T18:41:43+08:00)
# All commands read-only. No tag/Release deleted, nothing pushed by verifier.

## 1. $ gh -R randomgitsrc/agateon run view 35505427563

✓ v0.73.0-tagtest.1 Release · 35505427563
Triggered via push about 7 minutes ago

JOBS
✓ release in 10s (ID 106064303770)

ANNOTATIONS
- "The ubuntu-latest label will migrate to Ubuntu 26 beginning October 19, 2026. For more information, see https://github.com/actions/runner-images/issues/14748"
release: .github#1


For more information about the job, try: gh run view --job=106064303770
View this run on GitHub: https://github.com/randomgitsrc/agateon/actions/runs/35505427563

## 1b. run json (conclusion/headSha/jobs/steps)
{"conclusion":"success","event":"push","headBranch":"v0.73.0-tagtest.1","headSha":"d6dd3cb007a414f7dd5011c4031aa44326335a00","status":"completed","url":"https://github.com/randomgitsrc/agateon/actions/runs/35505427563","workflowName":"Release"}
job release success
  step 1 Set up job success
  step 2 Clone tag success
  step 3 Python deps (pinned pyyaml) success
  step 4 Build assets success
  step 5 Publish success
  step 6 Complete job success

## 2. $ gh run list --commit d6dd3cb... (chained workflows triggered by the same tag push)
{'conclusion': 'success', 'databaseId': 35505427551, 'event': 'push', 'headBranch': 'v0.73.0-tagtest.1', 'workflowName': 'Site Check'}
{'conclusion': 'failure', 'databaseId': 35505427522, 'event': 'push', 'headBranch': 'v0.73.0-tagtest.1', 'workflowName': 'Docs Check'}
{'conclusion': 'success', 'databaseId': 35505427563, 'event': 'push', 'headBranch': 'v0.73.0-tagtest.1', 'workflowName': 'Release'}
{'conclusion': 'failure', 'databaseId': 35505427554, 'event': 'push', 'headBranch': 'v0.73.0-tagtest.1', 'workflowName': 'Protocol Tests'}

## 3. $ gh release view v0.73.0-tagtest.1
tagName = v0.73.0-tagtest.1
name = v0.73.0-tagtest.1
isPrerelease = True
isDraft = False
targetCommitish = main
url = https://github.com/randomgitsrc/agateon/releases/tag/v0.73.0-tagtest.1
notes first line: '预发布测试（v0.73.0-tagtest.1）——非正式发布'
assets:
   agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz 1479669
   agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz 836404
   agateon-v0.73.0-tagtest.1.tar.gz 676262
   SHA256SUMS 341
--- notes (full) ---
预发布测试（v0.73.0-tagtest.1）——非正式发布

## 下载与校验说明

- 推荐下载 `agateon-v0.73.0-tagtest.1.tar.gz`（本体）：解压即得版本目录内容（`agate/` 与登记根文件）。
- GitHub 自动生成的 "Source code" 压缩包是整仓（整个仓库的快照），不是安装包，请勿用于安装。
- `agateon-v0.73.0-tagtest.1-offline-<平台>.tar.gz` 为离线安装包（含依赖 wheel），面向 Python 3.11。
- `SHA256SUMS` 仅用于发现下载损坏，不认证发布者：它与资产同处一个 Release，发布者账号被攻破时无法防护；
  需要更强保证请从 git tag 自行构建（`agate-release.py build`）后逐成员比对，或经第二渠道核对哈希。

> **BREAKING（TAG0037，将随 v0.73.0 发布）**：删除旧单软链布局支持。迁移指引见 `agate/UPGRADING.md` 的 `### v0.73.0`（软链用户三步：`mv ~/.agate ~/.agate.bak` → `mkdir -p ~/.agate` → `install.sh --versions`）。

### BREAKING（TAG0037：安装与多版本模型统一，RM-AG0066）

- **删除 legacy 软链布局支持**：`~/.agate` 是软链时，`agate-install.py` / `agate-resolve.py` / `install-offline.py` / `install.sh` 一律 fail-closed 并打印同一段迁移三步；版本解析链由五层收敛为三层（`AGATE_ROOT` > `AGATE_HOME` → `.agate-version` → `current`），移除"软链目标即协议根"兜底。仅影响仍使用软链布局的存量用户，已在版本管理布局的用户无需动作。
- **`install.sh` 无参语义变更**：无参与 `--versions` 等价（进入版本管理布局），其他参数 → 用法 + exit 2；`AGATE_REPO_DIR` / `AGATE_SYMLINK` 已废弃且被忽略（设置时 stderr 一行 WARNING）。

### 新增

- **版本目录结构契约**：新装 `vX.Y.Z/` 为"本体包"形态（`agate/` + 登记根文件 `CHANGELOG.md` / `LICENSE` / `NOTICES.md`），不再是整仓检出；契约与边界清单成文于 `agate/UPGRADING.md`，边界清单单一来源 `agate/scripts/agate_package.py`（`boundary_lines()`）。已装的整仓形态版本目录继续可解析，不迁移。
- **三条安装路径同构**：在线（`agate-install.py`）、离线（`agate-pack-offline.py` / `install-offline.py`）、portable（Release tarball + `agate-install.py --adopt`）产出同一结构；新增 `agate-install.py --adopt vX.Y.Z` 与 `--check --portable`（无需 git）。
- **Release 流水线**：新增 `agate/scripts/agate-release.py`（确定性构建本体 tarball、各平台离线包、`SHA256SUMS` 与发布说明）与 `.github/workflows/release.yml`。`SHA256SUMS` 只防下载损坏、不认证发布者。
- **文档**：`UPGRADING.md` 新增「版本目录结构契约」「portable 安装」小节与 `### v0.73.0` 节（BREAKING 标注、影响面、迁移三步、`install.sh` 无参语义、废弃 env、两步升级说明）；「安装 / 迁移 / 更新 / 回退对照表」去 legacy 列、解析优先级表改三层；历史版本节保留原文并在 §3 顶部加历史注记。

### 变更

- `agate_common.py`：`compute_sha256` 目录分支忽略字节码（`__pycache__` / `*.pyc` / `*.pyo`），安装态与运行后态哈希一致。

来源：TAG0037（RM-AG0066）。版本段标题与日期在 P8 发版时重命名。

## offline 包内 wheel（文件名与 sha256）

**linux-x86_64**

- `pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl`  sha256 `b8bb0864c5a28024fac8a632c443c87c5aa6f215c0b126c449ae1a150412f31d`

**windows-x86_64**

- `pyyaml-6.0.3-cp311-cp311-win_amd64.whl`  sha256 `9f3bfb4965eb874431221a3ff3fdcddc7e74e3b07799e0e84ca4a0f867d449bf`


## 4. $ gh release list
v0.73.0-tagtest.1	Pre-release	v0.73.0-tagtest.1	2026-09-20T10:34:08Z

## 5. $ git ls-remote --tags origin v0.73.0-tagtest.1  (remote tag still present -> pending USER manual cleanup)
d6dd3cb007a414f7dd5011c4031aa44326335a00	refs/tags/v0.73.0-tagtest.1

## 6. $ git tag -l 'v0.73.0*'   (LOCAL tags; empty = no local tag)
(end of output)
$ git describe --tags --abbrev=0  (local CHECK 7 basis)
v0.72.0

## 7. $ cd dl && sha256sum -c SHA256SUMS  (downloaded via gh release download, scratchpad)
总计 2944
drwxr-xr-x 2 kity kity    4096  9月 20 18:40 .
drwxr-xr-x 7 kity kity    4096  9月 20 18:41 ..
-rw-r--r-- 1 kity kity 1479669  9月 20 18:40 agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz
-rw-r--r-- 1 kity kity  836404  9月 20 18:40 agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz
-rw-r--r-- 1 kity kity  676262  9月 20 18:40 agateon-v0.73.0-tagtest.1.tar.gz
-rw-r--r-- 1 kity kity     341  9月 20 18:40 SHA256SUMS
agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz: 成功
agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz: 成功
agateon-v0.73.0-tagtest.1.tar.gz: 成功
rc=0
--- SHA256SUMS ---
2ca9c60248bdf175d5a364955a7fb487988f08182e58e72dd3c4b5faaebb85f6  agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz
4a6616c7d2ab85c9753c1d158e718c2c7eda5228cb16767aa8ee69b190671f6d  agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz
03d38d2c34813e35743f7f9caad9870df2795ea60764c1ac2b58ff1602a42a27  agateon-v0.73.0-tagtest.1.tar.gz

## 8. local reference build of the same commit d6dd3cb (scratch clone + tag in scratchpad clone only):
$ agate-release.py build --tag v0.73.0-tagtest.1 --expect-sha d6dd3cb... --repo <scratch clone> --skip-offline
总计 676
drwxr-xr-x 2 kity kity   4096  9月 20 18:40 .
drwxr-xr-x 7 kity kity   4096  9月 20 18:41 ..
-rw-r--r-- 1 kity kity 676262  9月 20 18:40 agateon-v0.73.0-tagtest.1.tar.gz
-rw-r--r-- 1 kity kity     99  9月 20 18:40 SHA256SUMS
03d38d2c34813e35743f7f9caad9870df2795ea60764c1ac2b58ff1602a42a27  /tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/g1-02-release/local-dist/agateon-v0.73.0-tagtest.1.tar.gz
03d38d2c34813e35743f7f9caad9870df2795ea60764c1ac2b58ff1602a42a27  /tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad/g1-02-release/dl/agateon-v0.73.0-tagtest.1.tar.gz

## 9. member-level comparison + manifest/sha256 checks
OK   body: CI member set == local build member set (155 members)
OK   body: every member bytes identical between CI asset and local build (diff=[])
OK   body: no absolute/../link/device members (bad=[])
body top-level entries: ['CHANGELOG.md', 'LICENSE', 'NOTICES.md', 'agate']
OK   body: no wrapping directory; top-level == {agate, CHANGELOG.md, LICENSE, NOTICES.md}
OK   body: 155 regular members equal git blob bytes of d6dd3cb (mismatch=[])
OK   body: no agate/tests, __pycache__, *.pyc
OK   offline-linux-x86_64: single wrapping dir agateon-v0.73.0-tagtest.1-offline-linux-x86_64/ (P2 design)
OK   offline-linux-x86_64: has manifest.json
OK   offline-linux-x86_64: has agate/ and wheels/
OK   offline-linux-x86_64: no unsafe members
offline-linux-x86_64 manifest keys: ['components', 'files', 'platform', 'source_ref', 'version']
offline-linux-x86_64 manifest version='v0.73.0' platform='linux-x86_64'
OK   offline-linux-x86_64: manifest.version strictly 'v0.73.0'
OK   offline-linux-x86_64: manifest.platform == linux-x86_64
OK   offline-linux-x86_64: agate/ files == body tarball agate/ files (bytes, 152 files)
offline-linux-x86_64 manifest component section: {"agate": {"path": "agate", "sha256": "8d764f1efae2f2383d7864d23f2cd4b70314a0ff14cfa5616f2c55dcc67a4f55"}, "CHANGELOG.md": {"path": "CHANGELOG.md", "sha256": "a777caac901ea26d1d1465215907e754bff63bec74c5512693925705750f3fb6"}, "LICENSE": {"path": "LICENSE", "sha256": "3149a918e95809b5886a0a52fe4e0d7d05430e64dbda7d36e462e2297a341334"}, "NOTICES.md": {"path": "NOTICES.md", "sha256": "9dd5b08257113f73c704f9521b1f1e15390ff27cd0730630a39f213658f5d941"}, "wheels": {"path": "wheels", "sha256": "1c92d744ce616c89ee9788a14567bd4fa52f2b43544cf28b444865ad62ee1ac8"}, "pyyaml": {"path": "wheels/pyyaml-6.0.3
  wheel wheels/pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl sha256=b8bb0864c5a28024fac8a632c443c87c5aa6f215c0b126c449ae1a150412f31d
OK   offline-windows-x86_64: single wrapping dir agateon-v0.73.0-tagtest.1-offline-windows-x86_64/ (P2 design)
OK   offline-windows-x86_64: has manifest.json
OK   offline-windows-x86_64: has agate/ and wheels/
OK   offline-windows-x86_64: no unsafe members
offline-windows-x86_64 manifest keys: ['components', 'files', 'platform', 'source_ref', 'version']
offline-windows-x86_64 manifest version='v0.73.0' platform='windows-x86_64'
OK   offline-windows-x86_64: manifest.version strictly 'v0.73.0'
OK   offline-windows-x86_64: manifest.platform == windows-x86_64
OK   offline-windows-x86_64: agate/ files == body tarball agate/ files (bytes, 152 files)
offline-windows-x86_64 manifest component section: {"agate": {"path": "agate", "sha256": "8d764f1efae2f2383d7864d23f2cd4b70314a0ff14cfa5616f2c55dcc67a4f55"}, "CHANGELOG.md": {"path": "CHANGELOG.md", "sha256": "a777caac901ea26d1d1465215907e754bff63bec74c5512693925705750f3fb6"}, "LICENSE": {"path": "LICENSE", "sha256": "3149a918e95809b5886a0a52fe4e0d7d05430e64dbda7d36e462e2297a341334"}, "NOTICES.md": {"path": "NOTICES.md", "sha256": "9dd5b08257113f73c704f9521b1f1e15390ff27cd0730630a39f213658f5d941"}, "wheels": {"path": "wheels", "sha256": "c91c69261cea2467ee7eb11f06edb2d736438cadec19f455f689a9db8ee63286"}, "pyyaml": {"path": "wheels/pyyaml-6.0.3
  wheel wheels/pyyaml-6.0.3-cp311-cp311-win_amd64.whl sha256=9f3bfb4965eb874431221a3ff3fdcddc7e74e3b07799e0e84ca4a0f867d449bf
RESULT ALL OK
EXIT_CODE(check_assets): 0
linux-x86_64 source_ref: v0.73.0-tagtest.1 | top-level: ['CHANGELOG.md', 'LICENSE', 'NOTICES.md', 'agate', 'manifest.json', 'wheels']
OK    linux-x86_64 component agate agate 8d764f1efae2f238 recomputed 8d764f1efae2f238
OK    linux-x86_64 component CHANGELOG.md CHANGELOG.md a777caac901ea26d recomputed a777caac901ea26d
OK    linux-x86_64 component LICENSE LICENSE 3149a918e95809b5 recomputed 3149a918e95809b5
OK    linux-x86_64 component NOTICES.md NOTICES.md 9dd5b08257113f73 recomputed 9dd5b08257113f73
OK    linux-x86_64 component wheels wheels 1c92d744ce616c89 recomputed 1c92d744ce616c89
OK    linux-x86_64 component pyyaml wheels/pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl b8bb0864c5a28024 recomputed b8bb0864c5a28024
files section entries: 155
windows-x86_64 source_ref: v0.73.0-tagtest.1 | top-level: ['CHANGELOG.md', 'LICENSE', 'NOTICES.md', 'agate', 'manifest.json', 'wheels']
OK    windows-x86_64 component agate agate 8d764f1efae2f238 recomputed 8d764f1efae2f238
OK    windows-x86_64 component CHANGELOG.md CHANGELOG.md a777caac901ea26d recomputed a777caac901ea26d
OK    windows-x86_64 component LICENSE LICENSE 3149a918e95809b5 recomputed 3149a918e95809b5
OK    windows-x86_64 component NOTICES.md NOTICES.md 9dd5b08257113f73 recomputed 9dd5b08257113f73
OK    windows-x86_64 component wheels wheels c91c69261cea2467 recomputed c91c69261cea2467
OK    windows-x86_64 component pyyaml wheels/pyyaml-6.0.3-cp311-cp311-win_amd64.whl 9f3bfb4965eb8744 recomputed 9f3bfb4965eb8744
files section entries: 155
RESULT ALL OK
EXIT_CODE(check_components): 0

## 10. chained workflow failure causes on the tag commit (informational; not BDD-20 criteria)
Protocol Tests 35505427554: 10 failed / 2276 passed / 8 skipped:
E               ❌ README version badge v0.72.0 != 最新 tag v0.73.0-tagtest.1 [README.md]
E             ❌ README version badge v0.72.0 != 最新 tag v0.73.0-tagtest.1 [README.md]
runner git: 2.55.0 ; local git: git version 2.43.0
EXIT_CODE: 0

# ===== ADDENDUM (re-verification at HEAD 043181d, 2026-09-20T18:55:47+08:00) =====
Scope ruling: P1 BDD-20 now carries a [BASELINE_CHANGE] annotation (annotation only): Then 4 (cleanup) is done manually by the user; P6 scope = items 1-3 + precise cleanup list; item 4 is re-checked read-only before the PR in P8.
Code delta since the evidence above (d6dd3cb..HEAD): agate/tests/helpers_tag_repo.py only; release/pack scripts and release.yml unchanged, so items 1-3 (real CI asset vs tag d6dd3cb) stay valid.

## Precise cleanup list (to be executed by the USER; verifier does not delete)
 - GitHub Release  v0.73.0-tagtest.1  (prerelease; assets: agateon-v0.73.0-tagtest.1.tar.gz, agateon-v0.73.0-tagtest.1-offline-linux-x86_64.tar.gz, agateon-v0.73.0-tagtest.1-offline-windows-x86_64.tar.gz, SHA256SUMS)
 - remote tag      refs/tags/v0.73.0-tagtest.1 -> d6dd3cb007a414f7dd5011c4031aa44326335a00
 - suggested (user): gh -R randomgitsrc/agateon release delete v0.73.0-tagtest.1 --cleanup-tag --yes
 - local tag: none exists (nothing to delete locally)

## Read-only state now (item 4 baseline; to be re-checked at P8 before the PR)
$ gh release list
v0.73.0-tagtest.1	Pre-release	v0.73.0-tagtest.1	2026-09-20T10:34:08Z
$ git ls-remote --tags origin v0.73.0-tagtest.1
d6dd3cb007a414f7dd5011c4031aa44326335a00	refs/tags/v0.73.0-tagtest.1
$ git tag -l 'v0.73.0*'
(end)
$ git describe --tags --abbrev=0
v0.72.0

## Chained workflows triggered by the same tag push on d6dd3cb (also section 2 / 10 above)
Release 35505427563 success | Site Check 35505427551 success | Docs Check 35505427522 FAILURE | Protocol Tests 35505427554 FAILURE (10 failed / 2276 passed / 8 skipped) | deploy-pages not triggered
Root cause A (tag-induced, 5 tests + Docs Check): CHECK 7 'README version badge v0.72.0 != latest tag v0.73.0-tagtest.1' (git describe does not filter semver; foreseen by P1 BDD-20 Given). Affected: Docs Check job; test_consistency.py::test_con_1_check_1_yaml_parseable, ::test_con_6_check_7_version_badge_sync, test_env_adapt_docs.py::test_bdd_25_consistency_zero_error, test_tag0027_b1_phases_transfer_fields.py::test_bdd_5_consistency_worktree_still_green_regression, test_tag0034_docs.py::test_bdd_50_consistency_zero_error_after_task_changes. Disappears when the tag is removed.
Root cause B (fixture, 5 tests): git 2.55 fast-import rejects hostile paths (agate/.git/config, agate/.GIT/y, agate/sub/.GiT, agate/../z, docs/.git/config) in agate/tests/helpers_tag_repo.py:130. Fixed by 895a10c (see bdd-15-hostile-members-ci-vs-fixed.md); verified on git 2.43 only, git 2.55 behaviour argued not observed; next PR CI run confirms.

EXIT_CODE: 0
