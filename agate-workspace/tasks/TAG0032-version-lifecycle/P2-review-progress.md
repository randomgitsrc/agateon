# P2-review-progress — TAG0032 · plan-eng-review

## 2026-09-07 — 输入读取
- [read] 角色定义 plan-eng-review.md + P2-dispatch-context-plan-eng-review.md（8 项重点核查项）
- [read] P2-design.md（407 行，4 候选 A1/A2/B1/B2 + 影响面梳理 + §6 gate_commands + §7 files_to_read + §9 minimal_validation）
- [read] P0-brief.md（scope 三段 + out-of-scope 四项）/ P1-requirements.md（14 BDD + §4 四类扫描 + I-1~I-12）/ P1-review.md（re-review approved，3 必修落地）
- [read] agate_common.py:90-268（_find_project_declaration / _resolve_pointer_chain / _resolve_version_info / resolve_*）+ :663-677（resolve_rules_root）
- [read] resolve-entry.py（68 行，:45 resolve_hook_root，:49 join(root,scripts,gate_py)，:50-52 fail-closed）
- [read] agate-install.py（435 行，_ensure_repo:129-147 makedirs:134，_cmd_install:269-288，_install_version:177-184，_cmd_uninstall:290-328 用 worktree remove/prune）
- [read] agate-resolve.py（归口 resolve_version_root）
- [read] test_agate_version_resolve.py / test_agate_version_install.py / test_hook_resolve_entry.py / conftest.py（fixture 契约）
- [read] P2-progress.md（architect 留痕）

## 核查发现
- [grep] 消费方归口复核：resolve_version_root/resolve_hook_root/resolve_agate_root/resolve_rules_root 全部 → _resolve_version_info；
  check-structure-consistency.py:_resolve_root()(L107-113) → resolve_agate_root(__file__)；check-yaml-schema.py:_resolve_root()(L139-145) → resolve_agate_root(__file__)；
  agate-dispatch.py/_resolve_agate_root + agate-inject-card.py/_agate_root → resolve_agate_root。
  grep os.path.dirname × "scripts" join：无 os.path.dirname(vdir)+"/scripts" 旁路。check-protocol-consistency.py:812 硬编码 root/"agate"/"scripts" 属仓库根 git-tree 检查器，非版本解析链，不受影响。
  → §1.2 + §9 note 2 的归口声明【属实】。§9 行号 528/545/155 相对实际（528✓ / 547 / 151+157）有轻微漂移，实质正确。
- [bash] 隔离 HOME 复现断点一：islink(base)=True 且 isdir(base)=True；os.makedirs(base,exist_ok=True) 穿透软链无报错；repo/ realpath 落软链目标内部 → minimal_validation result=confirmed【可信】。[PROD_NOT_TOUCHED]
- [bash] check-protocol-consistency.py --strict-errors-only → EXIT=0，329 WARNING / 0 ERROR（§4.3 checklist 5 / R6 基线声明属实）
- [bash] shellcheck -S warning install.sh → rc=0；shellcheck -S warning agate/scripts/*.sh → rc=0（P5_shellcheck_root 基线属实）
- [bash] ls agate/tests/scripts/count-tests.sh → 存在（dispatch 指引的 agate/tests/tests/scripts/ 不存在，§6 校正属实）
- [check] M1 守卫落点：_cmd_install() 首行 → 在 _ensure_repo(:271) → os.makedirs(:134) 之前，覆盖 main() 两处调用（无参 L415 / 版本号 L427）。正确。
- [check] version 推导：current 链 L190 os.path.basename(cur) 从 cur 取；M4 .agate-version 分支 version=declared 恒定。I-1 守住。
- [gap-nonblock] M2 copytree 源：指定版本分支（agate-install.py vX.Y.Z，L281-286 不写 current 指针）时「当前 current 版本」可能不存在，源未锁死。
- [gap-nonblock] install.sh --versions 未声明读 AGATE_REPO_URL；BDD-5 无 skip 条款 → 离线不可验。
- [hygiene] M12/M13/M14 新增用例名 test_bdd_N 与既有 TAG0008 用例名冲突域。

## 结论
status: approved，阻塞级架构问题 0，非阻塞 4（详见 P2-review.md）。
