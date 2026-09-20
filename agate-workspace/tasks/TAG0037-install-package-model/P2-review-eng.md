---
agent: plan-eng-review
phase: P2
task_id: TAG0037
type: review
parent: P2-design.md
trace_id: TAG0037-P2-review-eng-20260920-r1
created: '2026-09-20'
status: approved
---
# P2-review-eng — TAG0037 安装与多版本模型统一（plan-eng-review，复审 #1）

[PROD_NOT_TOUCHED] 只读评审：未改 `P2-design.md` 及任何仓库文件，未 git add / commit，未触碰真实 `~/.agate`、主 checkout、git 分支 / tag。复审实验只在 scratchpad 新建带序号目录 `eng-r1-1`、`eng-r1-2`（首轮遗留的 `eng/` 未再触碰）；本轮未执行任何删除类操作（`eng-r1-1` 内一处清除的是本轮自己刚生成的 `__pycache__`）。

**结论：approved。0 个 BLOCKER / 0 个 MAJOR。首轮 1 个阻塞 + 5 个 MAJOR + 8 个 MINOR 均已在设计正文中真实落地（不只是 §14 自述）。修订新引入 3 个非阻塞问题（N-1…N-3）与 2 个提示（N-4、N-5），建议 architect / P3 顺手吸收，不作为通过条件。**

## 1. 首轮发现逐条核对

| 首轮编号 | 复核方法 | 结论 |
|---------|----------|------|
| B-1 `__pycache__` 污染 | 读 D-13、R-13、§3.1「安装态 vs 运行后态」、§3.2、§3.3、§3.4 步骤 0/5/8、§3.5 `python3 -B`、§1.1 `compute_sha256` 行；**实测 R-1**：在 `eng-r1-2` 用 v0.72.0 本体树 + 占位 wheel + PATH `pip` shim 组装真实 bundle，只在 `install-offline.py` 最顶部（先于 `import agate_common`）加 `sys.dont_write_bytecode = True`，以真实内网用法 `python3 bundle/agate/scripts/install-offline.py bundle --dest-root …` 运行 | 已解决。首轮同样组装在未防护时 exit 1（checksum 误报）；加顶部置位后 exit 0，`current`/`v0.72.0` 建立，bundle 与 dest 下 `__pycache__` 数为 0。子进程不继承置位（E-10）的处理（`-B` + `PYTHONDONTWRITEBYTECODE=1`）符合 Python 语义。拷贝忽略字节码、`compute_sha256` 跳过字节码、比较口径忽略字节码、T-4 "使用后再比较"、T-15 bundle 内入口，闭环完整 |
| M-1 §8 yaml 不可解析 | 重跑 `check-protocol-consistency.py --strict-errors-only`；对 P2-design.md 全部 4 个 yaml 块 `yaml.safe_load` | 已解决。ERROR 数 0（CHECK 1 由 FAIL 变 WARN，且 WARN 清单无 TAG0037 条目）；4 块均解析通过；`check-frontmatter.py` rc=0；`agate-read-gate-commands.py` / `agate-read-p5-commands.py` 读取正常，无 `&&` 串联 |
| M-2 `--adopt` 执行主体 | 读 D-4、§3.3、§3.4 步骤 8、T-1 | 已解决。`install-offline` 用本脚本所在目录的兄弟 `agate-install.py`，合成 tag 不必内嵌安装器；失败路径改为 `rollback_swap` 且"版本目录未变更" |
| M-3 夹具不含 `agate_package.py` | 读 T-10、§1.1 测试面行、§8 | 部分解决，见 N-1（夹具清单点名的只有 2 处，但 m-3 采纳后 `agate_common.py` 的复制点更多） |
| M-4 批次依赖与验收 | 读 §5 与 frontmatter `dispatch_plan`；YAML 加载校验 | 已解决。C1 依赖 B2、B2 依赖 B1b + E；B1 / C 拆分；每批 `tests_filter`；"批内 vs 波次末"验收写明；`mode: serial` + `parallel_limit: 3`，9 批；文件面单批归属未破 |
| M-5 同源假设留口子 | 读 T-11、T-15、T-19、T-4 | 已解决。bundle 内入口 + 真实树冒烟 + PATH shim 替代全局 `mock.patch("subprocess.run")` |
| m-1 `parse_release_ref` | 读 §3.2、T-17、E-15 | 已解决（`fullmatch` + `re.ASCII` + 后缀拒 `..`，表驱动含 `v1.2.3\n`、Unicode 数字） |
| m-2 候选 B 证据措辞 | 读 §2 候选 B、D-1、E-14 | 已解决，措辞与我首轮 X-7 实测一致 |
| m-3 `agate_home()` 单源 | 读 R-3、§1.1 | 已解决，但引出 N-1 |
| m-4 换位回滚 / prune | 读 D-6、§3.2 `swap_in`/`rollback_swap`/`discard_backup`、§3.3 `--uninstall`、T-16 | 已解决，残余边角见 N-2 |
| m-5 老 tag 预装回退根 scripts | 读 §1.2、§3.8、§13 backlog | 按"文档 + backlog"处置，我首轮已交主 Agent 裁量，接受 |
| m-6 `symlink_base` 键 | 读 §3.7 | 已解决（env 早返回分支恒 False） |
| m-7 portable 命令 | 读 §3.5 | 已解决（`mkdir` 不带 `-p`、`sha256sum -c`、首两行 shell 软链守卫） |
| m-8 `files_to_read` | 读 §8 | 已解决（无行号；补两夹具助手与 `test_agate_common.py`）；16 项体量仍合适 |
| G-1…G-6 | 读 T-4 / T-6 / T-11 / T-15 / T-17 / T-19 | 已全部落入测试策略 |

## 2. 兼容红线复核（修订后仍成立）

- `_protocol_root` 函数体零改动；探测序不变；新契约形态 = 既有探测序 2；`agate-install.py` 内降级副本不动，BDD-8 五夹具比对仍是锁。
- D-8（不再特判软链）、D-7（删 `.installed-version` / `dest/.agate-root`）结论沿用首轮核验，修订未改动这两处。
- 修订新增的 `verify_dir`（`--adopt` 仅对无 `.git` 的新形态生效、旧 worktree 形态跳过）保持"已装旧形态可解析"；`verify_dir` 忽略字节码，不会因 hook 正常运行而使已装版本"违约"。
- D-14 规范化（`abspath` + `realpath` 歧义检测）只在路径含 `..` 时才可能改变判定，不误伤合法路径；不改变 `_resolve_pointer_chain` 语义。

## 3. 修订新引入的问题（均非阻塞）

### N-1（建议 P3 前吸收）`agate_common.py` 改为模块级 `from agate_package import agate_home` 后，复制 `agate_common.py` 的既有测试夹具不止 M-3 点名的两处
grep 命中把 `agate_common.py` 单独拷入"假协议根"再运行的夹具（现状不拷 `agate_package.py`，E 批合入后会 `ImportError`）：
- `agate/tests/unit/test_hook_resolve_entry.py`（`_make_fake_root`，约 :59）
- `agate/tests/integration/test_pre_commit_hook.py`（约 :1235、:1415）
- `agate/tests/unit/test_dispatch_context_warning.py`（`_FAKE_SCRIPTS`，约 :17 / :63）
- 另有 `test_install_hook.py` / `test_pre_push_hook.py` 拷贝 hook 薄壳，需人工确认是否经 `resolve-entry` 触发 `agate_common`。
这些是 BDD-47（"`test_hook_resolve_entry.py` 等既有用例保持通过"）的载体，但不在 E 批 `tests_filter` 内，会拖到 P5 全量才暴露。T-10 目前写的是"找全所有把 `agate-install.py` 拷入合成 tag 的位置"，应改为"找全所有把 `agate_common.py` 或 `agate-install.py` 拷入临时目录的位置"，并把这些 hook 测试文件加进 E 批 `tests_filter`。修法只是夹具拷贝清单加 `agate_package.py`（P3 拥有测试文件，不触碰 hook 三件套，不违反 BDD-46）。生产路径不受影响：hook 薄壳经 `ENTRY_ROOT` 整个 `scripts/` 目录解析，`_sync_root_scripts` 整目录 `copytree`。

### N-2（MINOR）`--adopt` 失败回滚未覆盖指针
`_register` 先写 `latest`、再写 `current`，`rollback_swap` 只还原版本目录。若"全新版本目录 + 既有指向旧版本的 `latest`/`current`"时 `latest` 已改写而 `current` 写入失败（例如该位置是真实目录，T-20 已列此失败路径），回滚会删除新目录，留下 `latest → 新版本（不存在）`，使原本可用的旧安装暂时无法经指针解析。概率低、可手工修复，但与 D-6 的"旧版完整"承诺不完全对齐。建议 `_cmd_adopt` 在写指针前记录旧目标，失败时恢复；或 T-16 增加"adopt 中途失败后旧指针仍可解析"一条断言。

### N-3（MINOR）`--expect-sha "$GITHUB_SHA"` 对带注解 tag 的语义未实测
设计比较 `refs/tags/T^{commit}` 与 `$GITHUB_SHA`。仓库现有 59 个轻量 tag、9 个带注解 tag，发布清单用轻量 tag，所以主路径没问题；但带注解 tag 触发时 `GITHUB_SHA` 是否为剥离后的提交 SHA 我无法在本地验证（本设计的 `not_validated` 也未列出）。建议 `build --expect-sha` 对两侧都做 `git rev-parse "<x>^{commit}"` 再比较；BDD-20 测试 tag 建议同时用一次带注解 tag 演练。

## 4. 提示（不需回应）

- N-4：`agate-summary.py` 的"软链基址追加迁移提示"应仅在根不可用（`root is None`）时输出；BDD-51 的"软链 → 完整版本根"能正常解析，此时再打印迁移提示与"放行"语义相悖。§3.7 文字未限定条件，P3 用 BDD-51① 加一条断言即可。
- N-5：`agate_package.py` 顶部置位 `sys.dont_write_bytecode = True` 会让所有间接 import 它的进程（含经 `agate_common` 的全部 gate 脚本）停止写 pyc。实测冷启动差异约 5ms（39ms vs 44ms，`eng-r1-1`），可忽略；仅提示这是全局副作用，非必要时入口脚本置位即可。

## 5. 复审时的 BDD 覆盖判断

- §4 映射 52 条逐条落点仍成立，无虚挂；首轮列出的"当前设计下无法满足"的条目（BDD-4 ①、9、16、17、2 ④）经 B-1 / M-2 修订后均可满足（已用真实 bundle 用法复现 B-1 的修复）。
- BDD-48 / 49（`passed ≥ 1842`、consistency 0 ERROR）：M-1 已消除设计文件自身造成的 ERROR。首轮我在 worktree 里跑的全量 pytest（39s）有 4 个 consistency 类失败正是该 ERROR 所致，现已随修复消失的前提成立（本轮未重跑全量，仅重跑 consistency 脚本确认 0 ERROR）。
- gate_commands 无变化：P3 只有裸键；`P5_*` 均单条命令，`_timeout_seconds` 均为元键；`P5_timeout_seconds: 300` 相对实测 39s 有富余。

## 6. 锁定决策（复审后）

1. 候选 C（`agate_package.py` 规则常量 + git plumbing）与 `agate-release.py` 接口划分——确认。
2. 字节码策略 D-13（入口置位 + 子进程 `-B` / 环境变量 + 拷贝 / 哈希 / 比较三处忽略）——确认，并已实测有效。
3. `--adopt` 执行主体 = 调用方同目录兄弟安装器（D-4）——确认。
4. 批次串行链 A → (B1a ∥ E) → B1b → B2 → C1 → C2 → (F1a ∥ F2)——确认。
5. 待 P3 携带的三项：N-1 夹具清单扩展、N-2 回滚后指针断言、N-3 `--expect-sha` 剥离比较。
