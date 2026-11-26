---
review_date: 2026-11-27
reviewer: protocol-alignment-review
change_summary: DSH 0.2.x 语义对齐——修正 persona 委派语义、显式声明 tool-subagent-control.interrupt、补 [NEED_CONFIRM] 工具落点、记入 --dump-config-schema 判据陷阱
files_changed: [agate/assets/templates/dsh/agent.cordis.yml, agate/platform-notes.md, agate/assets/templates/dsh/SKILL.md, agate/tests/unit/test_dsh_preset.py, CHANGELOG.md]
verdict: MISALIGNED
---

# 协议-脚本对齐审查（DSH 0.2.3 对齐批）

**一句话结论**：作者的核心判断「**无硬性不兼容**」**不成立**。三处陈述修正本身有据、方向正确，
但漏掉了一处**真实的硬性不兼容**：模板里 `tool-subagent-list-agents` 使用的包子路径
`@deepseek-ai/dsh-tool-subagent-control/list-agents` 自 DSH **0.2.2-rc.5** 起已从 `exports` 中移除
（上游有明文迁移指南要求删该行，agateon 未跟进）⇒ **agate preset 挂载失败、会话无法以 Agateon
编排者身份创建**。作者的判据「真启动 web profile 零错误零告警」无法发现它——preset 的挂载错误是
**异步登记**的，启动日志干净而 registry 里 `broken` 非空。

## 审查结论汇总

| # | 审查项 | 结论 |
|---|--------|------|
| A1 | 文档→脚本对齐 | **MISALIGNED** — 模板声明的插件行与上游 0.2.3 的包导出面不一致（见 A1 详情） |
| A2 | 脚本→文档对齐 | **MISALIGNED** — platform-notes / CHANGELOG 的「无硬性不兼容」无脚本支撑，且被实测证伪；SKILL.md 编号顺延在 roadmap 留有一处失效序号（MINOR） |
| A3 | 一致性连锁 + 反向传播 | **MISALIGNED** — A3a：`test_t41_platform_hygiene.py:144` 断言该行**必须存在**，与修复直接冲突；A3b：UPGRADING.md 缺章节、SETUP.md 未提该包迁移 |
| A4 | 测试覆盖 | **MISALIGNED** — 3 条新用例均为关键词级；其中 1 条经变异实测为**弱断言**（见 A4）；且**没有任何用例**守护「preset 行包名可解析」这一真实故障面 |
| A4b | 闭合后既有测试转红 + 夹具更新清单 | **MISALIGNED** — 本次新增未使既有用例转红（29 passed），但**正确修复**（删该行）必使 `test_t41_preset_mounts_delegation_in_preset_scope` 转红，需同步更新夹具 |
| A5 | 下游影响 + 文档传播 | **MISALIGNED** — 用户侧需重跑 `agate-setup.py` 才能刷新已写入 profile 的块，属行为变化，UPGRADING.md 必须有章节 |
| A6 | 锚点表覆盖 | ALIGNED — 未改 `agate/scripts/*.py` 的 gate 逻辑，无需新锚点 |
| A7 | 设计原则一致性 | ALIGNED — 不违反 ADR-002 / ADR-014 增补；`interrupt: true` 属平台取舍，非协议语义 |
| A8 | 声称-命令绑定 | **MISALIGNED** — 两处数字失准（「空 patch 5 条 / 加最小 preset 6 条」实测为 **4 / 5**）；核心结论「无硬性不兼容」**无命令可产出**（且实测为假） |

> 按 `AGENTS.md`「变更分诊」：本次问题均**改变判定**（会话能否创建）且**有真实使用面**（本机 +
  任何 DSH ≥ 0.2.2-rc.5 的 agateon 用户），**不可降级为呈现类**。A1/A2/A3/A4b/A5/A8 为真
  MISALIGNED，须修完再复审。

---

## 逐项审查

### A1: 文档→脚本对齐 — MISALIGNED

**模板声明**（`agate/assets/templates/dsh/agent.cordis.yml:187-188`）：

```yaml
    - id: tool-subagent-list-agents
      name: '@deepseek-ai/dsh-tool-subagent-control/list-agents'
```

**上游实现**（`packages/subagent/tool-subagent-control/package.json`，各 tag 实测）：

| DSH 版本 | `exports["./list-agents"]` |
|---|---|
| 0.1.7-rc.2 / 0.2.0-rc.2 / 0.2.1-alpha.1 / 0.2.1-alpha.5 / **0.2.1-rc.2** | **存在** |
| **0.2.2-rc.5** / **0.2.3-alpha.2** | **已移除**（只剩 `.`、`./src/*`、`./package.json`、`./locale/*.json`） |

命令：
```bash
for t in dsh-v0.2.1-rc.2 dsh-v0.2.2-rc.5 dsh-v0.2.3-alpha.2; do
  git show $t:packages/subagent/tool-subagent-control/package.json \
  | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['version'],'./list-agents' in d.get('exports',{}))"
done
# 0.2.1-rc.2 True / 0.2.2-rc.5 False / 0.2.3-alpha.2 False

node -e "require.resolve('@deepseek-ai/dsh-tool-subagent-control/list-agents',{paths:['/home/kity/.dsh/profiles/web']})"
# ERR_PACKAGE_PATH_NOT_EXPORTED
```

**上游有明文迁移指南**（`docs/upgrade-guide/v0.2.1-rc.1/subagent-control-tools/guide.zh.md` 第 3 条）：

> 「将 `/list-agents` 配置行替换为每个工具作用域一条 `@deepseek-ai/dsh-tool-subagent-control`，已有该行时则删除它们。**移除针对已停用的 `tool-subagent-list-agents` 行的 patch**。」

而 `list_agents` 现由根入口 `apply()` 内 `registerListAgents(ctx)` 注册
（`packages/subagent/tool-subagent-control/src/index.ts:42`）⇒ 该行**早已冗余**，官方
`base` / `standard` / `cordis` / `ptc` preset 均只有根入口一行。

**实机后果（不是理论风险）**：用 `runProfile()` 载入 profile 后读 `ctx.get('agentPresets').list()`：

```
agate    broken = "tool-subagent-list-agents (@deepseek-ai/dsh-tool-subagent-control/list-agents): never started"
standard broken = null
ptc      broken = null
minimal  broken = null
cordis   broken = null
```

`mount()` 复现同一失败：
```
MOUNT_FAIL code=agent-preset/invalid msg=tool-subagent-list-agents (...): never started
```

`agent-preset-registry/src/index.ts:253-259` 的 `retain()` 对 `broken !== undefined` **直接抛
`agent-preset/invalid`** ⇒ 用户在会话选择器选「Agateon 编排者」建会话会**失败**。UI 侧该卡片会显示
`brokenBadge` 且 `aria-disabled="true"`（`client/ui-agent-preset/src/client/AgentPresetSection.tsx:118-141`）。

**这与用户的原始报告一致**：「DSH 升级到 0.2.3-* 后 agateon 不兼容了」——**用户是对的**，
作者的「无硬性不兼容」结论错了。

**建议修法**：删掉模板第 187-188 两行（`list_agents` 仍由 `tool-subagent-control` 根入口提供，
工具面不缺）。已实测：删除后 `agate broken = null`，与 4 个官方 preset 齐平。

---

### A2: 脚本→文档对齐 — MISALIGNED

**文档声明**（`agate/platform-notes.md:137`）：

> 「**版本核验（2026-11-27，DSH v0.2.3-alpha.2，实机复验）**：真启动 web profile **零错误零告警**，
> 声明式 preset 块正常加载」

**实测**：真启动日志确实只有一行 URL、无 error/warn——但这是**不充分的判据**。preset 的挂载失败
被 `AgentPresetRegistry.activate()` 捕获后**降级为 `record.broken` 并只 `logger.warn`**
（`index.ts:132-136`），而 CLI 的 startup exporter 只在**启动失败**路径上把 logs 挂进
`StartupError`（`packages/boot/app-boot/src/index.ts:1279-1286` + `1316-1318`）⇒ **成功启动时
warn 不落 stdout/stderr**。

**反证实验**（故意的破坏也能「启动干净」）：把 persona 的必填 key `prefix` 改成 `notprefix`：

```
真启动日志：dsh web: http://127.0.0.1:45825/?token=...   （零错误零告警）
registry：  agate broken = "persona (@deepseek-ai/dsh-persona): invalid config:
                              - $.prefix missing required value (at prefix)"
```

⇒ 「真启动零错误」**不能**作为兼容性判据。这一点恰恰**削弱了**本次新增的「判据陷阱」节的说服力：
它正确指出不能信 `--dump-config-schema`，却把一个**同样不可靠**的判据（真启动看日志）
立为唯一权威。

**建议修法**：platform-notes 的版本核验节与 `agent.cordis.yml` 文件头，把判据改为
「`--dump-config` 载入后查 `agentPresets.list()` 的 `broken` 为空」或「真建一次会话」，
并写明「启动日志干净 ≠ preset 可用」。

**A2 反向（SKILL.md 编号顺延）**：全仓 grep `第 N 条 / 平台注意第 N 条`，唯一指错处是
`agate-workspace/roadmap/roadmap.md:96`（RM-AG0076）写「`SKILL.md` **平台注意第 7 条**显式声明
不要启用 agent-team」——agent-team 现已顺延为**第 8 条**。roadmap 是 done 历史记录（frozen），
非本次引入，记为 **MINOR**，建议顺手改为「平台注意『不要启用 agent-team 组合包』条」以免再随编号失效。
`SKILL.md` 自身内部引用的是「第 2 条 / 第 5 条」（未顺延），仍正确。

---

### A3: 一致性连锁 + 反向传播 — MISALIGNED

**A3a 连锁（已知衍生改动，与修复冲突）**：

`agate/tests/unit/test_t41_platform_hygiene.py:139-147`：

```python
    granted = set(re.findall(r"^\s+- id: (tool-subagent\S*)", tail, re.MULTILINE))
    assert granted == {
        "tool-subagent",
        "tool-subagent-control",
        "tool-subagent-fork",
        "tool-subagent-list-agents",     # ← 被钉为「必须存在」
    }, ...
```

该断言把 `tool-subagent-list-agents` 写进**必须存在的授权集合**。删该行修复 ⇒ 该用例必红。
须同步改为三项集合，并在注释里记录「该子路径行已于 0.2.2-rc.x 移除，`list_agents` 由根入口注册」。

**A3b 反向传播（应被影响但不在 diff 中）**：

| 文件 | 为何应改 | 现状 |
|---|---|---|
| `agate/UPGRADING.md` | 用户已装 profile 里的旧块含该行；删行后必须重跑 `agate-setup.py` 才生效 ⇒ 属**行为变化**，按发布清单第 3 条须有章节 | **缺** |
| `agate/SETUP.md:266` | 「迁移旧副本时的已知陷阱」只写了 `workflow-worker-thread → workflow-ptc` 一次包改名；`list-agents` 子路径移除是**同类第二例** | 未提 |
| `agate/assets/templates/dsh/SKILL.md` | 工具映射「单一来源在 persona」；修复后 persona 若删掉 `list_agents` 的独立行说明，SKILL 无需改（它不复述）；但若保留 `list_agents` 字样需确认指的是**根入口提供的工具**而非该行 | 已核实第 48 行说的是工具名，无需改 |
| `agate/platform-notes.md:182` | agent-team 段提到 preset 挂 `list_agents` —— 说的是**工具面**，修复后仍成立 | 无需改 |

`agate/phase-cards/*.md`、`agate/dispatch-protocol.md`、`agate/assets/templates/dsh/preset.yml`
经 grep 无同款「默认后台」或过时 DSH 描述（phase-cards 只有 P5 一处讲受限 harness 进程回收，
与本次无关）⇒ 作者改两个文件的范围本身**不足以**覆盖真正的缺陷，但就已改的三处陈述而言，
波及面判断是对的。

---

### A4: 测试覆盖 — MISALIGNED

**3 条新用例**（`test_dsh_preset.py:844/870/889`），实测 `grep -c '^def test_'`：HEAD=26、staged=29
⇒「新增 3 条」成立。

**变异实测**（副本 `/tmp/MUTAG`，`AGATE_ROOT` 指向副本）：

| 变异 | 预期 | 实测 |
|---|---|---|
| M1 删 `config: {interrupt: true}` | 红 | **红** ✓ |
| M2 把「默认后台」加回 persona | 红 | **红** ✓ |
| M3 删 persona 的 `ask_user_question` 行（plan-mode 段仍含同名工具） | 红 | **红** ✓（首版假绿确已修好） |
| **M5 删 persona 里的「activation-only」字样、其余说明保留** | 红 | **绿** ✗ |

**M5 是弱断言**：`test_preset_persona_does_not_claim_delegation_is_background` 断言
`"activation-only" in block`，但该词在块内**还出现在 delegation 组的死键注释**（块行 174：
「activation-only，后台语义由运行时统一保证」）⇒ 删掉 persona 内那处后仍绿。这与作者自述的
「全块 grep 被别处同名内容满足」是**同一类假绿**，只是换了个词。

**修法**：与 `ask_user_question` 那条一样，**限定在 persona 的 prefix 内**断言：

```python
persona = next(p for p in ... if p["id"] == "persona")
prefix = persona["config"]["prefix"]
mapping = prefix.split("## 平台注意")[0]
assert "activation-only" in mapping
assert "run_in_background" in mapping
```

**更根本的缺口**：本次真实故障（preset 行包名不可解析）**零用例守护**。现有 30 条用例全部是
「读模板文本 / 读生成块文本」的关键词断言，没有一条检查**行 `name` 是否是当前 DSH 上可解析的模块**。
建议补一条反向契约（与既有 `DSH_PACKAGE_REMOVED_KEYS` 同思路）：
`DSH_PACKAGE_REMOVED_SUBPATHS = {"@deepseek-ai/dsh-tool-subagent-control/list-agents"}`，
断言生成块不含；或（更强，但需 DSH）对每行 `name` 做 `createRequire(...).resolve()`。

---

### A4b: 闭合后既有测试转红 + 夹具更新清单

- **本批新增**：经实测**无既有用例转红**——`test_dsh_preset.py` 29 passed（含既有 26 条），
  `test_t41_platform_hygiene.py` 8 passed / 1 skipped。
- **但正确修复会转红 1 条**（须同步更新夹具）：

| 用例 | 位置 | 处置 |
|---|---|---|
| `test_t41_preset_mounts_delegation_in_preset_scope` | `agate/tests/unit/test_t41_platform_hygiene.py:139-147` | 从 `granted` 期望集合中删 `tool-subagent-list-agents`，改注释说明该子路径已移除、`list_agents` 由根入口注册 |

其它夹具（`conftest.py`、`test_platform_setup.py` 等）不涉及。

---

### A5: 下游影响 + 文档传播 — MISALIGNED

- **影响面**：所有已接入 DSH ≥ 0.2.2-rc.5 的 agateon 用户。其 profile patch 的托管块里已有该行，
  **DSH 一升级就失效**（用户报告的正是这个）。
- **是否需要用户动作**：**是**——块内容不跟随模板（`SETUP.md:269`：「块内容是复制进 profile 的，
  不跟随源文件——升级协议根后重跑一次 `agate-setup.py` 即刷新」）。故修复后须重跑 `agate-setup.py`。
- **CHANGELOG**：`[Unreleased]` 已记录本次改动（+25 行），但**内容建立在错误前提上**（「无硬性不兼容」），
  须整段改写。
- **UPGRADING.md**：**缺章节**。发布清单第 3 条要求「无破坏性变更也写『（无破坏性变更）』」；
  本项有明确的用户动作要求，更须写。

---

### A6: 锚点表覆盖 — ALIGNED

本批未新增/修改 `agate/scripts/*.py`，`_DSH_PLUGIN_RENAMES`（`agate_common.py:1093`）未动
（`dsh-workflow-worker-thread → dsh-workflow-ptc` 映射在 0.2.3 仍必要且正确，实测生成块
`workflow-ptc` 可解析）。CHECK 9 无需新锚点。

> 备注：`dsh-workflow-worker-thread` 在**本机** `require.resolve` 报 `MODULE_NOT_FOUND`
> （该软链是 19 个断链之一，指向开发 checkout 的旧路径），但生成块使用的是改名后的
> `dsh-workflow-ptc`，可正常解析 ⇒ 与作者的「映射无需改动」结论一致。

---

### A7: 设计原则一致性 — ALIGNED

- 符合 **ADR-002（可判定性）**：新增用例都是机器可判的断言；但注意它们只到关键词层，
  真正的故障面（模块可解析性）未被覆盖（见 A4）。
- 符合 **ADR-014 增补（2026-09-21b）**：适配层只做「指向 + 平台差异」，本次未把协议正文抄进模板。
- `interrupt: true` **不违反任何 ADR**：它是平台接入取舍，与协议语义正交。

无新增架构决策，无需补 ADR。

---

### A8: 声称-命令绑定

| # | 声称 | 产出命令 | 结论 |
|---|---|---|---|
| 1 | 「真启动 web profile 零错误零告警」 | `DSH_HOME=$W node .../bin.js --profile web --no-open --port 0 > run.log 2>&1`；`grep -Ei 'error\|warn' run.log` | **成立**（日志仅一行 URL）。但**不充分**（见 A2） |
| 2 | 「声明式 preset 块被正常加载」 | `--profile web --dump-config \| grep -n preset-agate` → 命中 | 成立（块进合成树） |
| 3 | **「无硬性不兼容」** | — | **无命令可产出，且实测为假**。`agentPresets.list()` 显示 `agate.broken` 非空；`mount()` 抛 `agent-preset/invalid` |
| 4 | 「`workflow-ptc` 在册、旧名 0.2.3 已不存在」 | `ls packages/workflow/workflow-ptc`；`grep -rn 'dsh-workflow-worker-thread' --include=package.json`（0 命中） | **成立** |
| 5 | 「`_DSH_PLUGIN_RENAMES` 映射无需改动」 | `dsh_preset_block()` 生成块实测含 `@deepseek-ai/dsh-workflow-ptc` | **成立** |
| 6 | **「空 patch 已有 5 条、加最小 preset 变 6 条」** | `--dump-config-schema 2>&1 \| grep -c '^dsh: error'`：patch 缺失=**4**、patch=`[]`=**4**、`[]`+最小 preset=**5**、真实 patch=**5** | **失准：各多 1**（实测 **4 / 5**） |
| 7 | 「19 个断链软链」 | `find ~/.dsh/profiles/node_modules/@deepseek-ai -maxdepth 1 -xtype l \| wc -l` → **19**（总条目 245） | **成立** |
| 8 | 「v0.2.3-alpha.2」 | `python3 -c "import json;print(json.load(open('$HOME/.dsh/profiles/node_modules/@deepseek-ai/dsh/package.json'))['version'])"` → `0.2.3-alpha.2`；DSH checkout HEAD `4b399c39a6` 亦为 0.2.3-alpha.2 release merge | **成立** |
| 9 | 「`ask_user_question` 是提问落点」 | `grep -n "name: 'ask_user_question'" packages/interaction/tool-ask-user/src/index.ts` → :40；三个官方 preset 均有 `- id: tool-ask-user` 行 | **成立** |
| 10 | 「官方 preset 设 `interrupt: false`，插件默认 `true`」 | `grep -n interrupt packages/bundle/base/cordis.patch.yml` → :400 `false`；`web-app/presets/{standard,cordis,ptc}.patch.yml` 各 1 处 `interrupt: false`；`tool-subagent-control/src/index.ts:32` `z.boolean().default(true)` | **成立** |
| 11 | 「新增 3 条用例」 | `git show HEAD:...test_dsh_preset.py \| grep -c '^def test_'` = 26；staged = 29 | **成立** |
| 12 | 「每条都做过变异，回退即转红」 | 见 A4 表 | **部分成立**：3 条中 2 条强、1 条弱（M5 仍绿） |

**须删除/改正的无据声称**：第 3 条（核心结论）与第 6 条（数字）。

---

## 重点问题的逐条回答

**1. 「无硬性不兼容」是否成立？** — **不成立**。真启动确实零错误零告警（这一点作者没测错），
但那是**不充分的判据**。preset 挂载失败被降级为 registry 的 `broken` 字段且日志不落盘，只有查
`agentPresets.list()` 或真建会话才暴露。实测 agate preset `broken` 非空、`mount()` 抛
`agent-preset/invalid` ⇒ **用户报告的「不兼容」是真的**，根因是 `list-agents` 子路径在
0.2.2-rc.5 被移出 `exports`。19 个断链软链确为环境残留，与本次故障**无关**（已交叉验证：
4 个官方 preset 在同一环境 `broken` 全 null）。

**2. 三处修复是否都有 0.2.3 的事实依据？** — **是，三条都有据**：
- activation-only / 无 `run_in_background`：`docs/upgrade-guide/v0.2.1-alpha.1/subagent-activations/guide.md` 明文；`tool-subagent/src/index.ts:267` render 就是 `started subagent ${value.name}`（字面串准确）。
- interrupt 默认值：`v0.2.2-rc.1/subagent-interrupt-default/guide.zh.md` + base/preset 源码 + 插件 schema 三方一致。
- `ask_user_question`：工具名在 `interaction/tool-ask-user/src/index.ts:40`，preset 里 `tool-ask-user` 行在位 ⇒ 映射成立。
（有据 ≠ 足够：这三处都是**描述**修正，没触及真正的**机制**故障。）

**3. `interrupt: true` 是否正确？** — **(a) 合理**。理由：
① 协议**明确要求**主 Agent 能中止——`dispatch-protocol.md:1050`「检测输出定位证据 + 触发核查、
**不自动判死**，主 Agent 据证据决定是否中止/重派」，没有 `interrupt_agent` 这个决定无法落地；
② 显式声明优于依赖插件默认值（上游已把「默认 true」改成「preset 显式 false」，说明默认值是会变的
实现细节）；
③ 无协议层风险。
两点提醒（不构成 MISALIGNED）：
- 注释里「见 dispatch-protocol『subagent 超时判定』」**锚点指偏**——那节（:774-805）讲的是
  **subagent 内部 Node 脚本自设硬超时**，不是主 Agent 中止 subagent；应指向 :1050「存活检查」。
- 本机真实 profile 有一条**顶层** `tool-subagent-control / interrupt: true` 覆盖
  （`cordis.patch.yml:147-150`），实测该顶层行 `disabled: True` ⇒ 该覆盖是 **no-op**
  （上游指南原话：「顶层以 `tool-subagent-control` 为目标的 patch 无法修改 preset 内的子行，
  只会修改已禁用的 Host 行」）。作者把 `interrupt: true` 加在**模板的 preset 作用域内**是
  **正确位置**；但若那条 home 覆盖是作者得出该结论的起点，建议核对理解并清理（属用户侧文件，
  非本仓改动范围）。

**4. A8 声称-命令绑定** — 见上表。三处重点：**「5 条 / 6 条」实测为 4 / 5**（各多 1）；
「19 个断链」**正确**；「v0.2.3-alpha.2」**正确**。核心结论「无硬性不兼容」**无法给出产出命令**。

**5. 测试是否假绿？** — `ask_user_question` 那条**已真修好**（M3 变异转红 ✓，确实只在
persona 工具映射节内断言）。但**同一文件里 `does_not_claim` 那条是同款弱断言**：`activation-only`
在块内还出现于 delegation 组注释，M5 变异后**仍绿**。建议按同样方式收紧到 persona prefix 内。

**6. A2 反向（编号顺延）** — 全仓 grep 后唯一失效序号在
`agate-workspace/roadmap/roadmap.md:96`（「SKILL.md 平台注意**第 7 条**」→ 现为第 8 条）。
frozen 历史记录，**MINOR**。

**7. 是否漏了该改的地方？** — 已 grep `SETUP.md` / `dispatch-protocol.md` / `phase-cards/*.md` /
`preset.yml`：**没有**同款「默认后台」或过时 DSH 描述。但漏了**别的东西**：
`UPGRADING.md`（缺章节）、`SETUP.md:266`（包改名陷阱清单应加 `list-agents` 第二例）、
`test_t41_platform_hygiene.py:144`（与修复冲突）。就「三处陈述」而言范围够；就「真实不兼容」而言，
**范围完全没覆盖到**。

**8. `--dump-config-schema` 判据陷阱是否准确？** — **实质成立、数字失准**。
四组实测（`grep -c '^dsh: error'` = `grep -c unrecognized`）：

| 场景 | unrecognized 条数 |
|---|---|
| patch 文件缺失 | **4**（`[/211..214]`，对应 standard/ptc/minimal/cordis） |
| patch = `[]` | **4** |
| `[]` + 1 个最小合法 preset | **5**（多 `[/217]`） |
| 真实 patch（含 agate 块，块内外共 2 个 preset 条目） | **5**（多 `[/220]`） |

⇒ 结论「官方自带 preset 同样报、不是 agateon 不兼容」**正确**；但作者写的
「空 patch 5 条、加最小 preset 6 条」**各多 1**。
另附两个容易踩的细节：① patch 写成 **0 字节空文件**时报的是
`must be a top-level YAML array of loader patch entries`（不是 unrecognized）——「空 patch」必须是 `[]`；
② `--dump-config-schema` 一旦有 error 就 **exit=1 且 stdout 为空**。

---

## 实测记录（可复现）

所有实验都在 `mktemp -d` / `/tmp/<dir>` 的**副本**上做，`DSH_HOME` 与 `HOME` 均指向副本；
真实 `~/.dsh` 全程只读（仅 `cp -r` 读取）。结束后 `git status --porcelain` 复核：除本人新增的
留痕/成果两个文件外，工作区与暂存区**与本轮开始时一致**。

| 实验 | 做法 | 结果 |
|---|---|---|
| E1 真启动 | 副本 profile，块替换为新模板生成块，`node bin.js --profile web --no-open --port 0` | 日志仅 1 行 URL，零 error/warn |
| E2 载入验证 | 同副本 `--profile web --dump-config` | exit=0，1625 行，`- id: preset-agate` 在 :1439 |
| E3 **registry 检查** | `runProfile()` → `ctx.get('agentPresets').list()` | **agate.broken 非空**；4 个官方 preset 全 null |
| E4 **mount 复现** | `reg.mount(new Context(), 'agate')` | `agent-preset/invalid: ... never started` |
| E5 **修复验证** | 副本删该 2 行后重跑 E3 | **agate.broken = null**（与官方齐平） |
| E6 对照组 | 全新 profile（无 patch） | 只有 4 个官方 preset，全 null |
| E7 判据反证 | 故意改坏 persona `prefix` | **启动日志仍干净**，registry 报 `$.prefix missing required value` ⇒ 启动日志不是判据 |
| E8 schema 数字 | 4 种 patch 场景跑 `--dump-config-schema` | 4 / 4 / 5 / 5（作者称 5 / 6） |
| E9 模块可解析性 | `createRequire(...).resolve()` 逐行核 | `list-agents` 子路径 `ERR_PACKAGE_PATH_NOT_EXPORTED`；其余行 OK |
| E10 变异测 | 副本上 M1/M2/M3/M5 | 红/红/红/**绿** |
| E11 测试与一致性 | `pytest test_dsh_preset.py` / `test_t41_*` / `check-protocol-consistency --strict-errors-only` / `count-tests.sh` | 29 passed / 8 passed 1 skipped / **0 ERROR**（434 frozen WARNING）/ 3060 |

### 复现 E3/E5 的最小脚本

```js
// probe.mjs —— 用 profile 自己的 boot 链载入，再问 registry 每个 preset 是否可用
const { runProfile } = await import('<DSH>/lib/profile-boot.js')
const { loadLayeredEnv } = await import('<DSH>/dsh-app-boot/lib/index.js')
const { ctx } = await runProfile({
  environment: loadLayeredEnv('dsh'), profile: 'web',
  patchFiles: [], args: ['--no-open', '--port', '0'],
})
const list = await ctx.get('agentPresets').list()
console.log(JSON.stringify(list.map(p => ({ id: p.id, broken: p.broken ?? null })), null, 1))
process.exit(0)
```
（`DSH_HOME` 指向副本；真实环境请勿直接跑，会写 `storages/`、`.credentials.yaml` 等。）

---

## 结论与处置

**MISALIGNED — 必须修复后复审。** 修复清单（按优先级）：

| # | 级别 | 文件:行 | 修法 |
|---|---|---|---|
| 1 | **BLOCKER** | `agate/assets/templates/dsh/agent.cordis.yml:187-188` | 删掉 `tool-subagent-list-agents` 两行（`list_agents` 由 `tool-subagent-control` 根入口提供，工具面不缺）。已实测删后 `broken = null` |
| 2 | **BLOCKER** | `agate/tests/unit/test_t41_platform_hygiene.py:139-147` | 期望集合去掉 `tool-subagent-list-agents`，注释记录理由（否则 #1 的修复使该用例转红） |
| 3 | **BLOCKER** | `CHANGELOG.md:15-40` | 整段改写：前提从「无硬性不兼容」改为「发现并修掉一处硬性不兼容（`list-agents` 子路径移除）」，保留三处陈述修正（有据） |
| 4 | BLOCKER | `agate/platform-notes.md:137-149` | 同上改写；并把「判据 = 真启动看日志」更正为「查 registry `broken` / 真建会话」，写明启动日志干净≠preset 可用（E7 反证） |
| 5 | BLOCKER | `agate/assets/templates/dsh/agent.cordis.yml:18-25` | 文件头「已实机复验…零错误零告警」与判据陷阱段同步更正 |
| 6 | BLOCKER | `agate/UPGRADING.md` | 新增版本章节：已接入用户须重跑 `agate-setup.py` 刷新型块；说明 `list-agents` 行移除与 `interrupt` 显式声明 |
| 7 | MINOR | `agate/platform-notes.md:145` 与 `CHANGELOG.md` | 「空 patch 5 条 / 最小 preset 6 条」→ **4 / 5**（或补上计数口径） |
| 8 | MINOR | `agate/tests/unit/test_dsh_preset.py:889-903`（`does_not_claim`） | `activation-only` / `job_output` 断言限定在 persona prefix 内（现被 delegation 组注释满足，M5 仍绿） |
| 9 | MINOR | `agate-workspace/roadmap/roadmap.md:96` | 「平台注意第 7 条」→ 按标题引用，避免再随编号失效 |
| 10 | MINOR | `agate/SETUP.md:266` | 包变更陷阱清单加 `list-agents` 子路径第二例 |
| 11 | 建议 | `agate/tests/unit/test_dsh_preset.py` | 新增反向契约守护「不得使用已移除的包子路径」（本次故障零用例覆盖） |

**关于「作者的判断是否错了」**：三处**陈述**的修正判断正确、依据充分、修法也对；但**关于兼容性的
核心判断错了**，且用的判据（真启动看日志）本身不可靠——这是本批最需要修正的一点：不是「修错了
地方」，而是**在正确的三处之外漏掉了一处真故障，并用一个弱判据为「无硬性不兼容」背书**。
