
## P1 analyst progress (2026-09-07)
- [step] 读完 dispatch-context + analyst.md 角色定义。三断点：①入口断链(agate-install.py 软链穿透) ②元仓库 gap(RM-AG0058 本体, resolve 命中 vdir 缺 agate/ 层) ③update 统一入口(文档面)。
- [step] 读完 P0-brief + .state.yaml。scope 三段锁定；out-of-scope=离线链路/Windows复制/state.yaml schema/agateon重构。known_risks 4 条(resolve语义变更/install软链拒绝/根scripts副本vs软链/端到端真实元仓库)。judge.enabled=true 已置。立项与启动同为 2026-09-07，需时效性核对。
- [step] 读完 HANDOFF-TAG0032.md + roadmap RM-AG0058 全文。RM-AG0058 scheduled, 关联 TAG0032, 创建 2026-09-03 / 更新 2026-09-07。交接单确认双工作区纪律 + 隔离 HOME 纪律 + 三断点实测证据(repo 实体落 src/agate/repo)。
- [step] 读完 agate-install.py(435 行)。软链穿透点确认：_ensure_repo() L134 os.makedirs(agate_home, exist_ok=True) —— agate_home=~/.agate，若为软链则 makedirs 跟随软链视作已存在(不报错)，随后 git clone 落入 <软链目标>/repo。全文仅此 1 处 makedirs/exist_ok。无根 scripts/ 建立逻辑。无 --versions 模式(install.sh 待查)。无软链检测。
- [step] 扫描 resolve 消费链完成。归口函数：_resolve_version_info(core) → resolve_version_root(agate-resolve/summary) / resolve_hook_root(resolve-entry) / resolve_agate_root(pre-commit-gate/dispatch/render/inject/next-card/check-structure/check-yaml/rules_root)。断点精确位：resolve-entry.py:49 os.path.join(root,"scripts",gate_py) + agate_common.py:677 os.path.join(root,"rules")。元仓库形态下 root=vdir(仓库根)，实际协议在 vdir/agate/。无直接拼 vdir/scripts 旁路(除 resolve-entry 经归口 root，安全)。注意点：_resolve_version_info dict 有独立 version 字段；pointer chain 分支 version=basename(cur)，若 root 改 vdir/agate 需保 version 仍为 vX.Y.Z(P2 细节，P1 BDD 锁 AGATE_VERSION 不回归)。
- [step] 同类扫描①makedirs/exist_ok：9 处命中。安装路径相关：agate-install.py:134(本次处理,软链穿透源) / install-offline.py:204 copytree dirs_exist_ok + _DEFAULT_DEST=~/.agate 同类穿透风险(out-of-scope 离线链路,本次不处理→记 roadmap 候选)。其余 archive/env-baseline/migrate/pack-offline/install-hook 均非 ~/.agate 根建目录,不同类。
- [step] 文档面扫描完成。断链现场：README.md:36-44 / README.zh-CN.md:36-44(curl install.sh → 紧接 agate-install.py，穿透污染)。install.sh 仅产 legacy 软链，无 --versions 模式。UPGRADING.md:551 表格已声称 ~/.agate 版本根含 scripts/(文档已承诺但 install 未实现——doc/reality mismatch)。UPGRADING.md:552 升级=agate-install.py。SETUP.md:5 两形态并列 / :244 升级节仅"符号链接什么都不用做"。
- [step] 同类扫描④文档面 update/升级指引：git pull 命中 UPGRADING ~40 处(逐版本节 + §1 通用步骤 L16/24) + SETUP:244节 + install.sh:20。agate-install 命中 README×2 / UPGRADING v0.50节 + §1无 / SETUP:26,54。重装 hook 指引散落 UPGRADING 各版本节(v0.60/0.61/0.62 要求重跑,v0.66/0.67/0.68 声明不需要)。收敛点：UPGRADING §1 通用升级步骤 + 新增"版本管理生命周期"节;README 快速上手;SETUP 升级节。
- [step] 读完既有测试。为何元仓库 gap 没被测出：test_agate_version_install.py::_tag_upstream 用元仓库形态源(agate/scripts/)但只断言 worktree HEAD/指针；test_hook_resolve_entry.py::_make_home + test_agate_version_resolve 全用 vX.Y.Z/scripts/ 直挂("根即协议")fixture。install(元仓库形态)与 resolve/gate(根即协议 fixture)从未串成一条端到端链。
- [step] 同类扫描②resolve 消费方：归口 _resolve_version_info。消费 root 后拼子目录的点：resolve-entry.py:49(scripts) / agate_common.py:677 resolve_rules_root(rules) / agate-dispatch:78,199 + inject-card:53 + render-dispatch:118,128 + next-card:166(scripts/assets/phase-cards，编排类走稳定版) / agate-summary 仅显示。无直接拼 vdir/scripts 旁路。返回 vdir/agate 后全部子目录拼接自然命中(元仓库 agate/ 下齐全)。
- [step] 同类扫描③解析链 marker：.agate-version 归口 _find_project_declaration(agate_common:99)。.agate-root 2 producer(install-hook:125 / install-offline:232) + 2 consumer(resolve_hook_root:222 / pre-commit copy 模式)。.installed-version 仅 install-offline 写。离线包/Windows 复制模式经同一 _resolve_pointer_chain → resolve 核心增量修复自然覆盖其解析侧；打包侧形态属 out-of-scope。
- [step] P0-brief 时效性核对：三条严重判据均不命中——①三断点在当前代码仍复现(agate-install.py:134 makedirs / resolve-entry.py:49 / 无根 scripts) ②Linux+worktree+python3/pytest 平台前提成立 ③known_risks 均前瞻性、无"已解决前提"。无漂移。
- [step] 写完 P1-requirements.md（294 行，14 条 BDD）。frontmatter：risk_level=high / ceremony=standard / phases=P1-P8 全走 / packages=[agate-scripts,agate-docs,agate-tests] / domains=[backend,cli] / implicit_coupling=true / capability_requirements=[] + verification_env(端到端隔离HOME+元仓库clone,止损2轮)。check-frontmatter.py EXIT=0。field-set --list 四必填字段就位。BDD 分组：①入口断链 BDD-1~5 ②元仓库 gap BDD-6~9 ③update 入口 BDD-10~12 ④端到端 BDD-13~14。同类扫描 4 类结论入正文 §4。P0-brief 时效性 §7「已核对无漂移」逐条。无行首 NEED_CONFIRM / 无 status:GAP。[PROD_NOT_TOUCHED]

---
## P1 修复轮 retry#1 (analyst-fix1) — 2026-09-07

- 已读：analyst.md 角色定义 / P1-dispatch-context-analyst-fix1.md 派发指引 + P1 卡片
- 已读：P1-review.md 结论节 — 3 项必修（BDD-12 机械判据恒真 / I-3 无 BDD 绑定 / BDD-2 判据宽严不一）+ 3 建议项
- 已读：P1-requirements.md（修改对象，14 条 BDD）
- 已核对 UPGRADING.md：
  - v0.50.0 节 §① 布局表格（实读 L549-L553）：L551 承诺 `~/.agate/` 根含 `scripts/`（doc/reality mismatch）；L552 升级=`agate-install.py`
  - hook 重装口径分歧：v0.60.0(L377-379)/v0.61.0(L315)/v0.62.0(L280) = `git pull`+重跑 `install-hook.py`；v0.66.0(L171-172)/v0.67.x(L117-118/L138-139/L155-156)/v0.68.0(L95-96) = 「无需重跑 install-hook.py，软链布局 git pull 即生效」
  - 行号漂移：review 锚点写 L546，实读 L551 → 采纳建议项改为节锚（`### v0.50.0` §① 表格）不写死行号
- 待落地：BDD-12 重写为可枚举 checklist（4 条矛盾表述二值断言）+ 0 ERROR 降附加回归项；BDD-4/BDD-11 承接 I-3（单测锁定 + 写入 UPGRADING）；BDD-2 三项判据统一到命令片段级；建议项 BDD-7/BDD-13/§4 行号全采纳

- 落地完成（原地改 P1-requirements.md）：
  - BDD-12：重写为 4 条可枚举 checklist（L551 根 scripts 承诺 / L552 升级入口 / v0.60-0.62 vs v0.66-0.68 hook 重装分歧 / README+SETUP 升级表述），每条二值断言「已收敛 / 已标注版本历史叙事保留」；0 ERROR 降为附加回归项。保留单一 Given/When/Then 外壳。
  - I-3：BDD-4 Then 加判据 2/3（agate/tests 单测锁定所选建立方式升级期语义 + 与 UPGRADING 一致）；BDD-11 Then 加判据 3（生命周期节含维护语义条目）；§2 表 I-3/I-4 行补「对应 BDD」。
  - BDD-2：三项判据统一到命令片段级（mv ~/.agate ~/.agate.bak / mkdir -p ~/.agate / agate-install.py + 版本标识），可 grep 机械判定。
  - 建议项全采纳：BDD-7 补 AGATE_VERSION 断言；BDD-13 逐步枚举 5 步期望 exit 0 + 幂等复跑不重复建目录；§4 扫描 4 + §2 行号改为节锚（`### v0.50.0` §① 表格），不写死行号。
  - check-frontmatter EXIT=0；BDD-1..14 连续，`#### BDD-NN:` 合规；frontmatter 未动；未新增断点；已确认合规项未动。
