# agate/tests/unit/test_agate_config.py
# TAG0042 批 2（agate-config 声明层）红/绿灯测试 —— BDD-3 / BDD-4 / BDD-7 / BDD-8。
#
# 目标语义（P1 BDD-3/4/7/8，P2-design §4.1 + §1.1 M4/M7/M8）：
#   * BDD-3：项目形态由项目根 `agate.config.yaml` 声明描述，协议 gate/推进/证据路径**读取声明**
#     决定行为，**不**对「产品是 md」这一形态做硬编码假设。
#   * BDD-4：`agate-config` 读/校验/查询子命令输出客观值（可被脚本消费），退出码 0=成功 / 非 0=失败。
#   * BDD-7：`agate-setup` / `install-hook` 接入时自动 `init` 声明，且不覆盖既有声明（幂等）。
#   * BDD-8：声明文件缺失时 gate_p0 行为与引入前一致（恒 return 2=通过码）+ 显眼 WARNING；
#     UPGRADING.md 写明该硬切「未排期」+ `RM-AG0102`（TAG0050 起协议不预告实施版本号）。
#
# 现行为（改动前）：`agate/scripts/agate-config.py` **不存在**；`agate_common.read_project_config`
#   **不存在**；`gate_p0` 无条件 return 2（无 validate 调用、不打印 WARNING）；setup/install-hook
#   不 init 声明 ⇒ 本文件当前红灯。
#
# 红灯分类（check-tdd-red）：本批红灯原因须为「被测模块/行为未实现」，即
#   `agate-config.py` 缺失（本项目内 import/文件探测失败 = B 类）与断言失败（行为未改 = B 类），
#   而非 SyntaxError / 第三方 import 失败（A 类）。
#
# 平台无关：tmp_path / task_dir / git_repo fixtures；run_cli(python_exe, ...)（不裸 python3）；
#   显式 encoding="utf-8"；需要「系统临时目录」字面量时**运行时拼接**（仓库既有惯例，R4 平台扫描）；
#   不写仓库内已提交文件（全在 tmp_path/git_repo）。

import importlib.util
import re

import pytest

# 被测 CLI（批 2 新增；当前不存在 ⇒ 红灯 = 模块未实现）
_CONFIG_SCRIPT = "agate-config.py"
_SETUP_SCRIPT = "agate-setup.py"
_INSTALL_HOOK_SCRIPT = "install-hook.py"

# 声明文件名（P2-design §4.1：项目根 agate.config.yaml）
_CONFIG_FILE = "agate.config.yaml"

# R4 平台扫描规避：需要「系统临时目录」字面量时运行时拼接（仓库既有惯例）。
_TMP = "/" + "tmp"

# 合法声明的最小内容（字段名取自 P2-design §4.1 示意；值全部为「非 agateon」以证不写死技术栈）。
_VALID_CONFIG = (
    "schema_version: 1\n"
    "project:\n"
    "  language: go\n"
    "  package_manager: go-mod\n"
    "verify:\n"
    "  commands:\n"
    "    - 'go test ./...'\n"
    "    - 'helm lint chart/'\n"
    "release:\n"
    "  preset: semver-changelog-tag\n"
    "paths:\n"
    "  evidence: .agate-evidence\n"
)


def _dump_yaml(data):
    """把 dict 落为 YAML 字符串（用 pyyaml，避免手写缩进出错）。"""
    import yaml

    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def _write_config(root, data):
    """在项目根写 agate.config.yaml。"""
    (root / _CONFIG_FILE).write_text(_dump_yaml(data), encoding="utf-8")


def _run_config(agate_scripts, python_exe, run_cli, *args, cwd=None, env=None):
    """运行 agate-config.py 子命令。当前脚本不存在 ⇒ subprocess 返回非 0 + 'No such file'。"""
    return run_cli(
        python_exe,
        str(agate_scripts / _CONFIG_SCRIPT),
        *args,
        cwd=cwd,
        env=env,
    )


def _load_common(agate_scripts):
    """import agate_common（用于断言 read_project_config 唯一读取函数的存在性/语义）。"""
    import sys

    scripts_dir = str(agate_scripts)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "agate_common_b2", str(agate_scripts / "agate_common.py")
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _has_read_project_config(agate_scripts):
    """探测 agate_common 是否已实现 read_project_config（批 2 新增；当前无 ⇒ 红灯根源之一）。"""
    src = (agate_scripts / "agate_common.py").read_text(encoding="utf-8")
    return re.search(r"^def read_project_config\b", src, re.M) is not None


def _isolated_agate_env(tmp_path, agate_root):
    """把 `AGATE_HOME` 指向 tmp，隔离 `installed-projects.json` 台账写入。

    背景（测试隔离缺陷）：`agate-setup.py` / `install-hook.py` 会经
    `agate_common.record_project()` 写 `<agate_home()>/installed-projects.json`；
    `agate_home()` 读 `AGATE_HOME`（未设则 `~/.agate`）。若测试不显式把 `AGATE_HOME`
    钉到 tmp，台账会落到真实位置（曾实测落 `installed-projects.json` 于仓库根），
    违反「测试不得写仓库内/真实环境文件」（test-designer.md 交付前自查 3）。

    返回 env dict：`AGATE_HOME` = tmp 下的独立目录（台账落此），`AGATE_ROOT` = 传入的协议根
    （避免解析链受环境干扰）。**同时作用于 AGATE_HOME 的其它消费方**（任何读
    `agate_home()` 的脚本），确保测试期间无真实写入。
    """
    isolated_home = tmp_path / "isolated-agate-home"
    isolated_home.mkdir(parents=True, exist_ok=True)
    return {
        "AGATE_HOME": str(isolated_home),
        "AGATE_ROOT": str(agate_root),
    }


# ── BDD-3：项目形态由声明文件描述，协议不写死技术栈 ────────────────────────
#
# Given 一个使用者项目，其形态（语言/包管理器/验证命令/发版方式等）与 agateon 不同
#       （如 GitLab + Go + Helm）
# When 该项目用 `agate-config init` 生成声明文件并填写自身形态
# Then 协议的 gate / 推进 / 证据路径**读取该声明**决定行为，**不**再对「产品是 md」
#       这一形态做硬编码假设


@pytest.mark.windows_smoke
def test_bdd_3_init_generates_declaration_file(git_repo, agate_scripts, python_exe, run_cli):
    """BDD-3：`agate-config init` 在使用者项目根生成 `agate.config.yaml`。

    现行为：`agate-config.py` 不存在 ⇒ 子进程 rc≠0、文件未生成 ⇒ 红灯。
    目标：init 退出码 0，且项目根出现声明文件。
    """
    repo = git_repo.path
    result = _run_config(agate_scripts, python_exe, run_cli, "init", cwd=repo)
    assert result.returncode == 0, (
        f"BDD-3：`agate-config init` 应成功（rc=0）；rc={result.returncode}\n{result.output[:400]}"
    )
    assert (repo / _CONFIG_FILE).is_file(), (
        f"BDD-3：`agate-config init` 应在项目根生成 {_CONFIG_FILE}（当前未生成，声明层缺失）"
    )


def test_bdd_3_declared_form_is_readback_not_hardcoded(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-3：形态值来自**声明**（Go + go-mod），而非协议里写死的「产品是 md」。

    Given 一份声明 language=go / package_manager=go-mod / verify=go+helm
    When `agate-config get project.language` / `get project.package_manager`
    Then 输出与声明一致的值（证明读取的是声明，不是硬编码的 agateon 形态）。

    现行为：agate-config.py 不存在 ⇒ get 无法运行 ⇒ 红灯。
    """
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": ["go test ./...", "helm lint chart/"]},
        "release": {"preset": "semver-changelog-tag"},
    })
    lang = _run_config(agate_scripts, python_exe, run_cli, "get", "project.language", cwd=tmp_path)
    assert lang.returncode == 0, (
        f"BDD-3：`agate-config get project.language` 应成功；rc={lang.returncode}\n{lang.output[:400]}"
    )
    assert lang.stdout.strip() == "go", (
        f"BDD-3：形态值须来自声明（期望 'go'），实际 {lang.stdout.strip()!r}"
        "——若返回 agateon 的 md 形态即为硬编码"
    )

    pm = _run_config(agate_scripts, python_exe, run_cli, "get", "project.package_manager",
                     cwd=tmp_path)
    assert pm.stdout.strip() == "go-mod", (
        f"BDD-3：project.package_manager 须来自声明（期望 'go-mod'），实际 {pm.stdout.strip()!r}"
    )


def test_bdd_3_protocol_does_not_hardcode_md_product_shape(agate_scripts):
    """BDD-3：协议读取路径**不写死**单一项目形态（无 md/pytest 硬编码的形态假设）。

    Given 批 2 落地后
    When 扫描 agate-config.py 的形态读取路径
    Then 其中**不出现**对单一技术栈的字面假设（如把 `pytest` / `.md` / `agateon`
         写死为唯一形态）。此用例在脚本缺失时红灯（被测模块未实现）。

    说明：这是 BDD-20 在**声明读取路径**上的收窄断言（dispatch-context 明确）——
    只约束新声明层不引入单项目规则，不约束全仓既有历史文案。
    """
    config_path = agate_scripts / _CONFIG_SCRIPT
    assert config_path.is_file(), (
        f"BDD-3：{_CONFIG_SCRIPT} 不存在（批 2 声明层未实现）——读取路径无从进行形态无关性检查"
    )
    src = config_path.read_text(encoding="utf-8")
    offenders = []
    for token in ("pytest", "agateon", "python3"):
        if token in src:
            offenders.append(token)
    assert not offenders, (
        "BDD-3/BDD-20：agate-config 声明读取路径写死了单一项目形态 token："
        + ", ".join(offenders)
    )


# ── BDD-4：agate-config 子命令提供完整读写能力 ─────────────────────────────
#
# Given 已存在声明文件
# When 运行 `agate-config` 的读/校验/查询子命令
# Then 输出项目形态的客观值（可被脚本消费），且子命令退出码语义固定（0=成功，非 0=失败）


def test_bdd_4_get_outputs_consumable_value(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-4：`get <field>` 输出单一字段客观值（stdout，可被脚本消费），退出码 0。"""
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "rust", "package_manager": "cargo"},
        "verify": {"commands": ["cargo test"]},
    })
    r = _run_config(agate_scripts, python_exe, run_cli, "get", "project.language", cwd=tmp_path)
    assert r.returncode == 0, f"BDD-4：get 应 rc=0；rc={r.returncode}\n{r.output[:400]}"
    assert r.stdout.strip() == "rust", (
        f"BDD-4：get 须输出客观值（期望 'rust'，可被脚本消费），实际 {r.stdout.strip()!r}"
    )


def test_bdd_4_list_and_show_output_declaration(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-4：`list` 列出全部字段 / `show` 展示完整声明，均 rc=0 且有可消费输出。"""
    _write_config(tmp_path, {
        "schema_version": 1,
        "project": {"language": "go", "package_manager": "go-mod"},
        "verify": {"commands": ["go test ./..."]},
        "release": {"preset": "semver-changelog-tag"},
    })
    listed = _run_config(agate_scripts, python_exe, run_cli, "list", cwd=tmp_path)
    assert listed.returncode == 0, f"BDD-4：list 应 rc=0；rc={listed.returncode}\n{listed.output[:400]}"
    assert "language" in listed.stdout, (
        "BDD-4：list 应列出声明字段（至少含 language）；当前输出为空即为未实现"
    )

    shown = _run_config(agate_scripts, python_exe, run_cli, "show", cwd=tmp_path)
    assert shown.returncode == 0, f"BDD-4：show 应 rc=0；rc={shown.returncode}\n{shown.output[:400]}"
    assert "go" in shown.stdout, (
        "BDD-4：show 应展示完整声明内容（含 project.language=go）"
    )


def test_bdd_4_get_missing_field_is_nonzero(tmp_path, agate_scripts, python_exe, run_cli):
    """BDD-4：`get` 对**合法但不存在**的字段 → 退出码非 0（失败语义固定）。

    先证明脚本可运行（`list` 成功 = 脚本已实现），再断言读不存在字段返回非 0——
    否则脚本缺失时的 rc≠0 只是「找不到文件」，不能证明退出码语义正确。
    """
    _write_config(tmp_path, {"schema_version": 1, "project": {"language": "go"}})

    listed = _run_config(agate_scripts, python_exe, run_cli, "list", cwd=tmp_path)
    assert listed.returncode == 0, (
        f"BDD-4：前置——agate-config list 应成功（证明脚本已实现）；rc={listed.returncode}"
        f"\n{listed.output[:400]}"
    )

    r = _run_config(agate_scripts, python_exe, run_cli, "get", "project.no_such_field",
                    cwd=tmp_path)
    assert r.returncode != 0, (
        "BDD-4：读不存在字段应以非 0 退出（失败语义固定）；当前 rc=0 即违规"
        f"\n{r.output[:400]}"
    )


# ── BDD-7：agate-setup / install-hook 自动 init 声明 ─────────────────────
#
# Given 一个尚未有声明文件的项目
# When 运行 `agate-setup`（或 `install-hook`）接入协议
# Then 自动生成（init）初始声明文件，且不覆盖既有声明（幂等）


def test_bdd_7_install_hook_auto_inits_declaration(tmp_path, git_repo, agate_scripts, python_exe, run_cli):
    """BDD-7：`install-hook.py` 接入项目时自动 init 声明文件。

    Given 一个尚无 agate.config.yaml 的 git 项目
    When 运行 install-hook.py（传入协议根）
    Then 项目根出现 agate.config.yaml。

    现行为：install-hook.py 不调 agate-config init ⇒ 文件未生成 ⇒ 红灯。

    隔离：`AGATE_HOME` 钉到 tmp（install-hook 经 record_project 写
    `installed-projects.json` 台账；不隔离会落真实仓库根）。
    """
    repo = git_repo.path
    agate_root = agate_scripts.parent
    assert not (repo / _CONFIG_FILE).exists(), "前置：项目尚无声明文件"
    result = run_cli(
        python_exe, str(agate_scripts / _INSTALL_HOOK_SCRIPT), str(agate_root),
        cwd=repo,
        env=_isolated_agate_env(tmp_path, agate_root),
    )
    assert result.returncode == 0, (
        f"BDD-7：install-hook 应成功接入；rc={result.returncode}\n{result.output[:400]}"
    )
    assert (repo / _CONFIG_FILE).is_file(), (
        "BDD-7：install-hook 接入时应自动 init 声明文件（当前未生成）"
    )


def test_bdd_7_install_hook_init_is_idempotent(tmp_path, git_repo, agate_scripts, python_exe, run_cli):
    """BDD-7：已在的声明文件**不被覆盖**（幂等）——重跑后内容保持不变。

    前置：先证明「接入本会 init」——对一个无声明的新项目跑 install-hook，若未生成声明
    即说明 auto-init 未实现（红灯），再谈幂等。

    隔离：`AGATE_HOME` 钉到 tmp（台账 `installed-projects.json` 不落真实仓库根）。
    """
    repo = git_repo.path
    agate_root = agate_scripts.parent
    env = _isolated_agate_env(tmp_path, agate_root)

    # ① 前置：无声明项目接入后应生成声明（auto-init 已实现）
    first = run_cli(
        python_exe, str(agate_scripts / _INSTALL_HOOK_SCRIPT), str(agate_root),
        cwd=repo,
        env=env,
    )
    assert first.returncode == 0, (
        f"BDD-7：install-hook 应成功接入；rc={first.returncode}\n{first.output[:400]}"
    )
    assert (repo / _CONFIG_FILE).is_file(), (
        "BDD-7：install-hook 接入时应自动 init 声明文件（auto-init 未实现）"
    )

    # ② 幂等：用户改写声明后重跑，内容不得被覆盖
    custom = "# user-custom\n" + _VALID_CONFIG
    (repo / _CONFIG_FILE).write_text(custom, encoding="utf-8")
    result = run_cli(
        python_exe, str(agate_scripts / _INSTALL_HOOK_SCRIPT), str(agate_root),
        cwd=repo,
        env=env,
    )
    assert result.returncode == 0, (
        f"BDD-7：install-hook 重跑应成功；rc={result.returncode}\n{result.output[:400]}"
    )
    after = (repo / _CONFIG_FILE).read_text(encoding="utf-8")
    assert after == custom, (
        "BDD-7：init 幂等——既有声明不得被覆盖/改写；当前内容已变（覆盖违规）"
    )


def test_bdd_7_setup_source_invokes_config_init(agate_scripts):
    """BDD-7：`agate-setup.py` 接入流程须调用 `agate-config init`（自动 init 声明）。

    Given agate-setup 源码
    When 检查其接入流程
    Then 出现对 `agate-config init` 的调用/引用（auto-init 的接入点）。
    现行为：setup 无该调用 ⇒ 红灯（行为未改）。
    """
    src = (agate_scripts / _SETUP_SCRIPT).read_text(encoding="utf-8")
    assert re.search(r"agate-config(\.py)?\b.*\binit\b|\binit\b.*agate-config", src), (
        "BDD-7：agate-setup.py 应调用 agate-config init 自动生成声明（当前无该接入点）"
    )


# ── BDD-8：声明文件缺失时行为与现状一致且给 WARNING（迁移期） ──────────────
#
# Given 一个存量项目**没有**声明文件（未迁移）
# When 运行 gate_p0（调 `validate`）或任意消费声明的 gate 路径
# Then 行为与引入 `agate-config` **之前一致**，并输出显眼 WARNING（**不** exit 1），
#       且 `UPGRADING.md` 写明「到截止版本改 exit 1」及该截止版本号


def test_bdd_8_gate_p0_missing_declaration_keeps_passing_exit(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-8：存量项目（无声明的任务目录）跑 gate_p0 → **仍 return 2（通过码）**，不 exit 1。

    给定 task_dir（无项目根声明文件），运行 check-gate.py P0。
    目标：行为与引入 agate-config 之前一致（恒 2）。

    前置：先证明 gate_p0 **已接入声明校验**（batch2 落地）——否则「恒 2」只是现状、
    无法区分「迁移兼容做对了」与「根本没接」。因此本用例一并断言 gate_p0 输出了
    声明缺失 WARNING（接入的证据），再断言通过码未变。
    """
    td = task_dir(phases=["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"])
    # ⚠️ 显式 cwd = **自带项目根**（task_dir 的上级）：`agate-config.py validate` 按 **cwd** 找
    # `agate.config.yaml`，不显式传就会拿 pytest 进程的 cwd（= **agateon 仓库根**）——那样
    # 「仓库有没有声明」会决定本用例红绿（本仓 2026-10-11 加了自己的 agate.config.yaml 后即被
    # CI 抓出）。用例要断言的语义是「**该项目**没有声明」，故必须自带项目根。
    _project = td.parent.parent
    result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P0", str(td), cwd=str(_project)
    )
    assert "WARNING" in result.output and _CONFIG_FILE in result.output, (
        "BDD-8：前置——gate_p0 应已接入声明校验并输出声明缺失 WARNING；"
        f"当前无该 WARNING（校验未接入）\n{result.output[:500]}"
    )
    assert result.returncode == 2, (
        "BDD-8：声明文件缺失时 gate_p0 行为须与现状一致（通过码 = 2），"
        f"不得 exit 1；实际 rc={result.returncode}\n{result.output[:500]}"
    )


def test_bdd_8_gate_p0_missing_declaration_emits_warning(task_dir, agate_scripts, python_exe, run_cli):
    """BDD-8：声明文件缺失时 gate_p0 须输出**显眼 WARNING**（迁移期提示，不阻断）。

    现行为：gate_p0 只打印「立项阶段无需脚本 gate」的说明，**无**声明缺失 WARNING
    ⇒ 红灯。
    """
    td = task_dir(phases=["P0", "P1", "P2", "P3", "P4", "P5", "P6", "P7", "P8"])
    # 同上：显式 cwd = 自带项目根（不依赖仓库根是否有声明）
    result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P0", str(td),
        cwd=str(td.parent.parent),
    )
    assert "WARNING" in result.output and _CONFIG_FILE in result.output, (
        "BDD-8：声明文件缺失时 gate_p0 应输出含声明文件名的显眼 WARNING（迁移期）；"
        f"当前输出缺少该 WARNING\n{result.output[:500]}"
    )


def test_bdd_8_upgrading_documents_cutoff_version(agate_root):
    """BDD-8：UPGRADING.md 须记载声明文件迁移，且该硬切声明为「未排期」并指向 RM-AG0102。

    TAG0050 起：协议不预告实施版本号（原 TAG0042 约定「须写明截止版本号」已由 RM-AG0102 承接）。
    断言限定在**批 2（声明层）小节**内，避免被全文其它版本号 / 无关内容满足。
    """
    upgrading = (agate_root / "UPGRADING.md").read_text(encoding="utf-8")
    assert _CONFIG_FILE in upgrading, (
        f"BDD-8：UPGRADING.md 应记载 {_CONFIG_FILE} 的迁移说明（声明层缺省行为）"
    )
    assert re.search(r"exit\s*1", upgrading), (
        "BDD-8：UPGRADING.md 应写明该硬切将改为 exit 1"
    )
    start = upgrading.index("批 2（声明层")
    end = upgrading.index("批 4（关卡层", start)
    section = upgrading[start:end]
    assert "未排期" in section, (
        "BDD-8：批 2 小节应声明该硬切「未排期」（TAG0050 起协议不预告实施版本号）"
    )
    assert "RM-AG0102" in section, (
        "BDD-8：批 2 小节应指向承接该欠账的 RM-AG0102"
    )


def test_debt0066_gate_p0_uses_task_project_root_not_cwd(
    tmp_path, agate_scripts, python_exe, run_cli
):
    """DEBT0066：`gate_p0` 的声明校验须以**目标任务所属项目根**为基准，而不是调用方 cwd。

    构造：项目 **A**（任务所在，**无**声明）+ 项目 **B**（**有**声明）；从 **B** 调用
    （`cwd=B`）对 **A 的任务**跑 gate_p0 ⇒ 须按 **A** 判定（即**出**声明缺失 WARNING）。
    修前行为：`agate-config.py validate` 按 cwd 找 ⇒ 读到 B 的声明 ⇒ **漏报**。
    """
    a = tmp_path / "A"
    task = a / "agate-workspace" / "tasks" / "T001"
    task.mkdir(parents=True)
    (task / ".state.yaml").write_text("task_id: TXX0001\nphase: P0\n", encoding="utf-8")
    b = tmp_path / "B"
    b.mkdir()
    (b / "agate.config.yaml").write_text(
        "schema_version: 1\nproject:\n  language: python\n", encoding="utf-8"
    )

    result = run_cli(
        python_exe, str(agate_scripts / "check-gate.py"), "P0", str(task), cwd=str(b)
    )
    assert "WARNING" in result.output and "agate.config.yaml" in result.output, (
        "DEBT0066：须按**任务所属项目（A，无声明）**判定并出 WARNING；"
        f"不得被调用方 cwd（B，有声明）掩盖\n{result.output[:600]}"
    )
