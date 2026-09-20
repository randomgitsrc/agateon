[P2 architect] 已读 dispatch-prompt/context/architect角色/P0-brief/P1-requirements(52 BDD)。下一步：读脚本+测试，做排除机制实测
[P2] 已读 install.sh/agate-install.py/install-offline.py/agate-pack-offline.py。关键观察：离线 bundle 顶层需 agate/(本体)+根级登记文件+wheels+manifest；安装器只拷 P=agate/+登记根文件；初步倾向候选3(自写Python构建器+git plumbing，规则常量在 agate_package.py)，待实测；拟新增 agate-install.py --adopt 统一指针+根scripts
[P2] 实测完成：git archive 在 autocrlf=true/属性下会做 EOL 转换(违反BDD-15③)；export-ignore 会掏空 GitHub 源码包(153/3390)；老tag缺根文件时 git archive fatal；自写 cat-file 构建器字节一致+确定性(两次sha相同)+0.11s。选候选3
[P2] 已读 agate_common/resolve/summary/install.sh、UPGRADING生命周期节、SETUP、AGENTS发布清单、consistency CHECK10。实测：无git PATH下 portable 包(无tests)可 resolve/summary；--check 默认口径缺git exit1(符合预期)；risk-score 无参打印用法rc1(P1 BDD-52 表述需澄清)；actionlint 本机未装。开始写 P2-design.md 前的收尾核查
[P2] P2-design.md 已写成，frontmatter 已设置(agent/dispatch_plan 手写)，check-frontmatter 已跑
[P2] 已按主Agent三项裁决修订(C-1记入§4/§6,去SCOPE+/pull,C-2为P3提示)
- [eng-review] start: reading P2-design
[cso] start: reading P2-design (timeout 10s)
- [eng-review] read P2-design.md fully; next: P1 BDDs + source code
[cso] read P2-design.md fully; next: source code (install.sh, agate-install.py, install-offline.py, pack-offline, agate_common)
- [eng-review] read P1 BDDs; next: source
- [eng-review] read install.sh/agate-install/install-offline/pack-offline/agate_common(110-260); next: experiments (pycache pollution, all-tag mode scan), agate-resolve/summary, tests
[cso] read install.sh/agate-install.py/install-offline.py; next: pack-offline, agate_common, workflows, then scratchpad experiments (trailing-slash islink, tar extract, mv, gzip filename) (short cmds, timeout<=30s)
- [eng-review] running full pytest timing in bg (timeout 480s) -> scratchpad/eng/pytest.out
[cso] experiments done: F-1 trailing-slash islink bypass CONFIRMED (overwrote repo/agate/scripts/a.py via agate-install.py in scratchpad); tar 1.35 safe; gzip FNAME leak confirmed w/o filename=''; regex $ newline confirmed. next: write P2-review-cso.md
[cso] output written P2-review-cso.md status=rejected (F-1 HIGH)
[P2 retry#1] 开始：读 eng/cso 评审
[P2 retry#1] 已读两份评审；实验目录 exp-1(F-1软链守卫复现+规范化)、exp-2(pyc/哈希/换位回滚)、exp-3(regex/gzip/tag扫描)；注意：曾误在仓库根 mkdir exp-1..3 三个空目录，已用 rmdir(非递归)移除，仓库无残留
[P2 retry#1] 实验结论：F-1 复现(islink('link/')=False)且规范化(abspath+realpath歧义检测)修复有效；B-1 复现(pyc使dir哈希变)且 dont_write_bytecode/-B/PYTHONDONTWRITEBYTECODE 有效、子进程不继承 sys.dont_write_bytecode；哈希跳过pyc后相等；换位回滚原型通过；69 tag 7127 文件硬化规则 0 违规；autocrlf=false 可缓解 autocrlf 分支(属性分支仍在)；pyyaml 6.0.2 wheel 名为大写 PyYAML-(现 glob pyyaml-* 会漏)，6.0.3 小写，两平台可下载→pin 6.0.3+大小写无关查找。开始改 P2-design.md
[P2 retry#1] 已改完 §0-§14 与 dispatch_plan，开始自检(consistency/yaml/check-frontmatter)
[P2 retry#1] 完成：自检通过(consistency 0 ERROR, yaml 4块OK, frontmatter OK)。scratchpad 新建目录 exp-1 exp-2 exp-3 exp-4
[cso] retry1 start: reading dispatch-context-cso-retry1 + P2-design §14
[cso] retry1 done: approved (0 HIGH; N-1,N-2 MEDIUM); new scratchpad: cso2
[P2 增补] 已应用 cso N-1/N-2、eng N-1..N-4，consistency 0 ERROR；新建 scratchpad exp-5
[review-lead] start: reading eng/cso reviews + design §14 (short cmds)
[review-lead] read both reviews + §14; now grep-verifying design landing points
[review-lead] P2-review.md written status=approved
