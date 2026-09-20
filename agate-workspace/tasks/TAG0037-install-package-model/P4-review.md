---
agent: review
phase: P4
task_id: TAG0037
type: review
parent: P4-implementation.md
trace_id: TAG0037-P4-review-lead-20260920
created: '2026-09-20'
status: approved
---
# P4-review — TAG0037 安装与多版本模型统一（P4 实现评审，专家组组长汇总）

[PROD_NOT_TOUCHED] 组长只汇总，不发表新意见；仅读取两份专家评审，除本文件外未改任何仓库文件，未 git add / commit，未删除任何文件。

**汇总结论：approved（全票通过，无 BLOCKER，无专家组分歧）。**

## 1. 两位专家最终结论（已核对 frontmatter 真实值）

| 专家 | 文件 | frontmatter status | frontmatter agent | BLOCKER（CRITICAL/HIGH） | 其余发现 |
|------|------|--------------------|-------------------|--------------------------|----------|
| review（代码评审） | P4-review-code.md | approved | review | 0 | MAJOR 0；MINOR 5（M-1…M-5）；INFO 3（I-1…I-3） |
| cso（供应链与安装器安全） | P4-review-cso.md | approved | cso | 0（无 CRITICAL / HIGH / MEDIUM） | LOW 8（L-1…L-8）；INFO 2（I-1、I-2） |

规则核对：两份文件 status 均为 approved，均无 BLOCKER，两位结论一致 → 统一 approved。
review 的 M-3（rollback_swap 无备份分支缺来源校验）与 cso 对同一函数"安全（并发不支持已文档化）"的判定，在严重度上是同向（均非阻塞），属评价角度差异（review 关注库函数的公开性与两分支不对称，cso 关注当前调用链），不构成结论分歧。

## 2. [DESIGN_GAP] 四项裁定

| 项 | review 裁定 | cso 裁定 | 汇总 |
|----|-------------|----------|------|
| discard_backup 拒绝路径返回 False + stderr 警告 | 可接受：adopt 成功后的清理不应使已成功安装报错；目录原样保留（宁留不删）；遗留带标记备份容器由 recover_backups 提示 | 安全：实测对用户预置同名带标记目录返回 False 并警告，目录与内容保留；仅删本进程创建集合内、带标记的容器 | 一致接受 |
| rollback_swap 语义（移入 failed-new 后删除；仅备份为本进程创建且标记有效才回滚） | 可接受，附 M-3（无备份分支 rmtree(final) 缺来源校验，建议 swap_in 记录 st_dev/st_ino 集合） | 安全：带备份分支三重限定，无备份分支仅对本进程刚换位的目录调用，并有真实目录校验；实测旧目录内容还原、备份容器清除、adopt 失败时 latest/ 目录保留 | 一致接受；M-3 为加固建议，非阻塞 |
| make_work_dir 根目录不存在时创建 | 可接受：离线安装到全新 --dest-root 所需；软链守卫在所有入口先于它；失败路径仅 os.rmdir 回收本次新建的空根 | 安全：失败分支仅 rmdir 刚 mkdtemp 的空容器；install-offline 仅当 root_preexisted=False 且为空才 rmdir(dest_root)；bundle 校验失败时 dest 根目录未被创建 | 一致接受 |
| pack 输出目录已存在则拒绝覆盖 | 可接受：同一 --outdir 二次打包 exit 1；agate-release build 每平台用全新 pack 目录，CI 与本地补救不受影响；建议 P8 CHANGELOG 补一句（I-2） | 安全：拒绝覆盖而非清空重建，无误删面 | 一致接受 |

## 3. cso 删除点清单结论（数据安全）

cso 对新增 / 改动脚本 grep 全部删除类调用（rmtree / unlink / os.remove / os.rmdir / shutil.move / os.replace / rename）逐处核对，全部判定"安全"：删除对象严格限于本工具创建且带专用标记（或本进程刚 mkdtemp 出）的容器 / 目录；sweep_stale / recover_backups / discard_backup / rollback_swap 永不按名字模式删除；install.sh 与 release.yml 无任何删除类命令；无 shell=True / os.system / eval / exec。实测预置的 vX.Y.Z.bak-\*、vX.Y.Z.tmp-\*、无标记的 .agate-tmp-\*、标记软链、目录软链、不足 1 小时的有效容器均原样保留，外部软链目标哈希不变；adopt 失败注入后 latest/ 用户数据完整保留、未留半成品版本目录（锚点 BDD-10 / BDD-16 / BDD-32 / BDD-51，T-23）。review 独立复核了同一批 rmtree 点，结论一致（无按名字模式删除）。
软链基址守卫：cso 实测 84 组变体（4 入口）无绕过，目标目录零变化（锚点 BDD-27 / BDD-31 / BDD-32 / BDD-33，F-1 HIGH 已落实）。

## 4. 其他核心事实（来自 review 实测，供后续阶段引用）

全量测试 2291 passed / 1 failed / 2 skipped；唯一失败 test_t15_real_tree_smoke_pack_install_resolve 读已提交 HEAD 内的旧 install-offline.py，review 在克隆中模拟提交后 46 passed，判定提交后必转绿，P5 复核即可。真实 pack 产物上 P0 真 BUG 修复成立（BDD-9 / BDD-11）；三路径产物逐字节同构（BDD-2 / BDD-3 / BDD-4）；_protocol_root 函数体零改动、已装旧形态可解析（BDD-5 / BDD-7）；ruff、shellcheck、check-protocol-consistency 均通过。

## 5. 遗留发现与后续处置建议（汇总，不新增意见）

| 编号（来源） | 级别 | 摘要 | 关联 BDD | 建议处置 |
|--------------|------|------|----------|----------|
| M-1（review） | MINOR | agate/scripts/README.md 三行脚本索引仍描述旧机制（worktree、缺 --adopt / --ref、install-offline 旧流程） | BDD-37 / BDD-39 | P4 提交前吸收（文档，5 分钟）或 P5 前修 |
| M-4（review） | MINOR | F2 改名测试后 P3-test-cases.md:120 旧名与"改名 3"对账计数（应为 4，净删仍 0）未同步 | BDD-38 / BDD-48 | 主 Agent 在 P4 提交时追溯订正；P5 复核 D / A 对账 |
| M-2（review） | MINOR | 私有符号跨模块引用；三份"本进程容器清理"守卫重复 | BDD-22…24 | 可 P4 内重构或入 backlog（P8 后） |
| M-3（review） | MINOR | rollback_swap 无备份分支缺来源校验 | D-6 | 加固可选，或入 backlog（cso 判定当前调用链安全） |
| M-5（review） | MINOR | workflow 中 pip 走 PATH 而非 venv | BDD-20 | P5 / P6 BDD-20 真实 CI 首跑时确认；可选 GITHUB_PATH 修补 |
| L-1（cso） | LOW | --uninstall 无软链基址守卫 | BDD-32 / BDD-51 | backlog；或 P4 修订补守卫与 T-14 用例 |
| L-2（cso） | LOW | portable 文档 shell 守卫未处理 /.（N-5 未吸收） | BDD-17 / BDD-32 | P4 修订（文档片段）或 backlog；P5 / P6 若实跑 BDD-17 命令须知 |
| L-3（cso） | LOW | portable tar -xzf 解压期软链与字节码盲区（N-7 未吸收） | BDD-15 / BDD-17 / BDD-19 | 文档加固或 backlog，非新增提权面 |
| L-4（cso） | LOW | Publish 步骤（持令牌）执行克隆 tag 内脚本 | BDD-20 | backlog 或 P4 修订（把 is-prerelease 挪到无令牌的 Build 步骤）；P6 复核 |
| L-5（cso） | LOW | 静态迁移文案硬编码 ~/.agate；mv 遇已存在 .bak 嵌套 | BDD-27 / BDD-35 | 文档措辞补一句，P7 或 P4 修订 |
| L-6（cso） | LOW | agate-release notes --out / build --notes-out 静默覆盖既有文件 | BDD-20 | backlog |
| L-7（cso） | LOW | 离线重装同版本静默丢弃旧目录（含本地改动），无提示 | BDD-10 / BDD-16 | backlog（输出提示一行 + UPGRADING 一句） |
| L-8（cso） | LOW | AGENTS 发布清单 gh release delete 缺 -R 与"勿加 --cleanup-tag" | BDD-21 | P4 修订（文档）或 P8 前 |
| I-1…I-3（review）；I-1、I-2（cso） | INFO | --skip-offline 时 notes 头文案；行为收紧建议进 CHANGELOG（pack 目录拒覆盖、1h 阈值、并发不支持）；agate-install 已装版本仍先走 _ensure_repo（既有行为）；CODE-MAP 已声明 CODE_MAP_EXEMPT 交 P7；VERSION_RE 前导零；Windows junction | BDD-15 / BDD-27 | I-2（review）在 P8 CHANGELOG 变更节补记；CODE-MAP 由 P7 核对；其余仅记录 |

阶段归属小结：P5 关注 t15 提交后复跑转绿、BDD-48 的 D / A 对账、BDD-20 真实 CI 首跑前须获用户许可；P6 复核 L-4 / M-5 与 release.yml 首跑；P7 核对 CODE-MAP 豁免与文档陈旧项（M-1 / L-5）；P8 在 CHANGELOG 补记行为收紧项与 backlog 登记。以上均不阻塞 P5，无需回派 implementer 即可放行。

## 6. 引用锚点

BDD-2、BDD-3、BDD-4、BDD-5、BDD-7、BDD-9、BDD-10、BDD-11、BDD-15、BDD-16、BDD-17、BDD-19、BDD-20、BDD-21、BDD-22、BDD-27、BDD-31、BDD-32、BDD-33、BDD-35、BDD-37、BDD-38、BDD-48、BDD-51。
输入文件：P4-review-code.md（status: approved, agent: review）、P4-review-cso.md（status: approved, agent: cso）。
