[PROD_NOT_TOUCHED]

# P5 其余 gate / 额外核对（HEAD 895a10c，重跑 #1；命令串行、均带外层 timeout、PYTHONDONTWRITEBYTECODE=1）

| 项 | 命令 | exit | 关键输出 | 判定 |
|---|---|---|---|---|
| P5_consistency | python3 agate/scripts/check-protocol-consistency.py --strict-errors-only | 0 | 「仅有 367 个 WARNING，无 ERROR」 | 通过（0 ERROR） |
| P5_ruff | ~/.venvs/agate-dev/bin/ruff check agate/ | 0 | All checks passed! | 通过 |
| P5_shellcheck | shellcheck -S warning install.sh agate/scripts/*.sh | 0 | 无输出 | 通过 |
| P5_release_build | python3 agate/scripts/agate-release.py build --tag v0.72.0 --repo . --outdir $SCRATCH/p5-release-2 --notes-out $SCRATCH/p5-release-2.notes.md --skip-offline | 0 | 产出 SHA256SUMS + agateon-v0.72.0.tar.gz，耗时约 1s | 通过 |
| sha256sum -c | 在 p5-release-2 内 sha256sum -c SHA256SUMS | 0 | agateon-v0.72.0.tar.gz: 成功 | 通过 |
| agate-install --check | AGATE_HOME=$SCRATCH/p5-home-2 python3 agate/scripts/agate-install.py --check | 0 | python3/pyyaml/git/bash 全部可用；隔离 home 保持为空 | 通过 |
| count-tests | bash agate/tests/scripts/count-tests.sh | 0 | 总计 2294（collect-only），与 pytest 2292+2 skipped 一致 | 通过（无漂移，见备注） |
| t15 | pytest agate/tests -k test_t15_real_tree_smoke_pack_install_resolve -v | 0 | agate/tests/integration/test_install_three_paths.py::test_t15_real_tree_smoke_pack_install_resolve PASSED，1 passed | 转绿，通过 |

$SCRATCH = /tmp/claude-1000/-home-kity-oclab-agateon--worktrees-agate-TAG0037/9e4aedbc-aa1a-42f7-9d40-57703b1a2c96/scratchpad

## release build 产物
- tarball 字节数：647370；成员数：153（tar tzf 行数）；成员未压缩字节合计 1864871（与 P2 R-12 记录的 B = 1,864,871 一致）。
- 成员内 `.git/` 条目数 0。sha256：d94ea4f32c0dc548573f1db44cbf5c2bbd88d86519b94c5cf5348f05606b055d
- notes 文件已生成（首节为「下载与校验说明」）。

## 需主 Agent 知悉的观察（非失败）
1. 本地已存在 tag v0.72.0，指向 a8012a2（TAG0036-P8，是 HEAD 的祖先，HEAD 领先该 tag 多个提交）。build 依 --tag 从该 tag 构建，故产物不含 P4 新增内容（tarball 中 agate_package 出现 0 次）；即该冒烟验证的是构建入口对真实 tag 可运行，未覆盖 HEAD 上的新文件。P4 新增内容由 t15 与全量测试覆盖。
2. count-tests.sh 只输出总数与「>= 749」基线判据；仓库文档（README/AGENTS/docs 非 workspace）中未检索到 2294 等具体计数，故无可比对的文档数字，判定无可检出的漂移。
3. consistency 的 367 条 WARNING 均为叙事文件旧引用类，不含 ERROR。

## 仓库状态对比
重跑前后 git status 对比：仅 P5-progress.md（本人追加进度行）与 P5-test-results/ 覆盖写入有差异；未 git add/commit/push/tag，未触碰 ~/.agate。

## 重跑 #1 备注
各项结果与首轮一致（consistency 367 WARNING/0 ERROR；ruff/shellcheck 0；t15 PASSED；sha256 与字节数、成员数 153、未压缩 1864871 均同首轮；--check exit 0 且隔离 home 为空；count-tests 2294）。
