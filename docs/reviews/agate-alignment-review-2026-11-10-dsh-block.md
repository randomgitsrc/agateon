---
review_date: 2026-11-10
reviewer: protocol-alignment-review
change_summary: DSH 声明块过期检测假阳性（语义比对替代逐字比对）+ 重写时保留块内外来条目 + 修掉升级路径重复 insert 回归
files_changed: [agate/scripts/agate_common.py, agate/scripts/agate-setup.py, agate/scripts/agate-summary.py, agate/tests/unit/test_dsh_preset.py, agate/tests/unit/test_agate_summary.py, CHANGELOG.md]
---

# 协议-脚本对齐审查 — DSH 声明块过期检测修复

> 审查对象：分支 `fix/dsh-list-false-positive`（基线 `62f41ad0`）的暂存改动面，6 文件 +434/-9。
> 审查方式：两轮独立上下文评审（第二轮为按首轮结论修复后的复审），均**实跑判据**而非只读代码。
> 走 hotfix 通道（单一主题、无跨模块影响、可快速验证），不立项。

## 背景

`agate-setup.py --list` 与 `agate-summary.py` 对 DSH profile 的 `preset-agate` 托管块
报「与任何已装版本都不一致 / 漂移」是**误报**。根因：DSH 会把
`~/.dsh/profiles/*/cordis.patch.yml` 解析后**重新序列化**——

1. `>-` 折叠标量重折行（实测同版本差 62 行）；
2. DSH 自己的顶层条目 `- id: agent-preset-registry` 被写进我们的定界符**之内**
   （实测包名集合 27 vs 26）。

⇒ 任何「逐字文本相等」判据在该文件上**天然恒假**。

**更严重的是原引导**：告警写「重跑接入刷新」，而原 `dsh_apply_block` 是「删光两定界符之间
再追加」⇒ 照做会**删掉 DSH 的注册条目**（preset 可能不再可选）。这是真损坏，不是误报级别。

## 审查结论汇总

| # | 审查项 | 首轮 | 复审（修复后） |
|---|--------|------|----------------|
| A1 | 文档→脚本对齐 | MISALIGNED | FIXED |
| A2 | 脚本→文档对齐 | ALIGNED | FIXED（文案同源） |
| A3 | 一致性连锁 + 反向传播 | ALIGNED | ALIGNED |
| A4 | 测试覆盖 | MISALIGNED（2 处假绿） | FIXED |
| A5 | 下游影响 + 文档传播 | ALIGNED（已补 CHANGELOG） | ALIGNED |
| A6 | 锚点表覆盖 | N/A（无新协议规则） | N/A |
| A7 | 设计原则一致性 | ALIGNED | ALIGNED |
| A8 | 声称-命令绑定 | ALIGNED | ALIGNED |

## 首轮发现的问题与处置

### ① 阻断：`dsh_block_matches` 过度放宽（假阴性）

`return gen <= inst` 是 **set 超集** ⇒ 块内出现**两个** `- insert:` 仍判一致。
而 insert=2 正是旧实现的破坏性产物（实测 v0.83.0 的块重写后 insert count = 2）。
若不查重复，这类用户会一直看到 ✅、**永远不被告知重跑可修**。

**处置**：加 `sum(1 for i in inst_items if _dsh_is_ours(i)) == 1`。实测：
重复 insert → `False`；正常块 → `True`（双向都成立，未一刀切）。
补 `test_dsh_block_matches_detects_duplicate_insert` 固化。

### ② 建议：`_dsh_is_ours` 缺右边界

`id: preset-agate-custom` / `preset-agate2` 会被误判为"我们的"而删除。

**处置**：改用 `re.search(rf"id: preset-{re.escape(DSH_PRESET_ID)}(?![\w-])", norm)`。
实测：`preset-agate-custom` → False、`preset-agate2` → False、`preset-agate` → True、
DSH 的 `agent-preset-registry` → False。

**已知取舍（复审确认不阻断）**：`norm.startswith("- insert:")` 作为先行判据，使右边界对
insert 形态失效（`- insert:` + `id: preset-agate-custom` 仍判 True）。可辩护理由：
① 定界符之间是**已声明托管区**，手改被覆盖是文档化预期（有专门测试固化）；
② 实测 DSH 外来条目形态是 `- id: ...` 而非 `- insert:`，右边界在真实外来形态上有效。
按仓库「变更分诊三问」第 1 问（只能人为凑出的输入不管）不阻断。

### ③ 建议：两处告警文案不同源

`agate-summary.py` 仍写「与任何已安装版本的**权威模板**都不一致」（模板相等口径已废）。

**处置**：改为「与本机已装版本生成的条目**不一致**（缺条目、被改或重复）」+
「重跑接入会**按当前版本重写块内内容**（块内 DSH 自己的条目会保留）」，与
`agate-setup.py --list` 同义。

### ④ 测试假绿 1：折叠标量用例无鉴别力

原 `re.sub(r"(\n\s+)(?=\S)", " ", block, count=3)` 把**缩进本身**吞掉 ⇒ 构造的是
"YAML 已非法"的输入，断言 True 证明不了折叠等价。

**处置**：改为 `_fold_scalar()`，只在 `>-` 块标量内折叠**同缩进**内容行（更深的续行保留换行）；
先断言 `folded != block`（有鉴别力），再断 True；并**新增反向断言**「缩进被破坏 ⇒ 判 False」。

### ⑤ 测试假绿 2：`--list` 告警用源码子串断言

只证某短语不存在，文案写错/缺失仍绿。

**处置**：改为**实跑 `--list`**，断言真实输出含「不一致」、不含「重跑接入刷新」、含「重写块内内容」。

## 另修：升级路径重复 insert 回归（作者自查发现）

上一轮实现按「归一化后**不在本次生成集合**里 ⇒ 外来」判归属。但**版本升级**时旧块里
**我们自己的** `- insert:` 文本必然与新版不同（插件增删/改名）⇒ 被误判为外来而保留
⇒ 块内出现**两个** `- insert:`（实测 v0.83.0 → insert count = 2，preset 重复注册）。

**处置**：改用**锚点身份** `_dsh_is_ours`（`- insert:` 前缀 或 `id: preset-agate` 带右边界），
含锚点的条目一律由新块替换。实测三条升级路径 v0.80.2 / v0.83.0 / v0.83.1 块内
`- insert:` 均 == 1。

**不拿包名当锚点**：`@deepseek-ai/dsh-agent-preset` 是 DSH 注册项包名
`...-preset-registry` 的**严格前缀** ⇒ 子串判据必删 DSH 条目。
**不走 YAML 解析**：块内含 `!!js` 自定义标签（`disabled: !!js process.platform === 'win32'`），
标准解析器直接报错。

## 实测证据（A8 声称-命令绑定）

| 声称 | 命令 | 结论 |
|---|---|---|
| 真实 profile 判一致 | `dsh_block_matches(dsh_extract_block(profile), gen)` | True |
| `--list` 误报消失 | `python3 agate/scripts/agate-setup.py --list` | ✅（无 ⚠️） |
| `summary` 误报消失 | `python3 agate/scripts/agate-summary.py` | 无 DSH 漂移行 |
| 真损坏仍检出 | 删掉 `- id: tool-web` 后跑上述两条 | `--list` 报 ⚠️ / summary 报漂移 |
| 重复 insert 检出 | 块体放两遍后跑 `--list` | 报 ⚠️ |
| 升级不重复 | v0.80.2/v0.83.0/v0.83.1 旧块 → 新 `dsh_apply_block` | 块内 insert 均 == 1 |
| 重写保留外来条目 | 真实 profile 重写 | `agent-preset-registry` 仍在块内，块外内容逐字不变 |
| 单测 | `pytest test_dsh_preset.py` | 26 passed |
| 单测 | `pytest test_agate_summary.py` | 37 passed |
| 全量 | `pytest agate/tests/ -n auto` | 3015 passed / 3 failed（见下） |
| 一致性 | `check-protocol-consistency.py` | 0 ERROR（433 冻结 WARNING） |
| Lint | `ruff check agate/` | All checks passed |

**3 个既有失败**（已用 `git stash` 在**干净基线**复现同样失败，与本次改动无关，属环境问题）：

- `test_agate_cmdstream_adapters.py::test_bdd_4_dsh_multi_frame_container_returns_all_records`
- `test_agate_version_install.py::test_rm_ag0102_cli_wrappers_generated_and_runnable`
- `test_install_three_paths.py::test_t15_real_tree_smoke_pack_install_resolve`
  （`git clone --local` 跨设备链接）

另 `test_bdd_43_opencode_registration_and_debug_agent` 因 `opencode` 不在 PATH 失败（已知环境问题）。

## A4b 闭合后既有测试转红清单

经实测**无既有用例转红**。相关既有用例 `test_dsh_declarative_block_stale_warns`
（改 `order: 1` → `order: 99` 模拟过期）在新判据下仍正确报漂移，无需更新夹具。

## 总结论

**可提交。** 核心方向（语义超集比对 + 保留外来条目 + 列 0 兄弟项）经两轮评审确认正确，
不需重设计。首轮 1 项阻断 + 2 项建议 + 2 处测试假绿均已修复并由复审逐条实测确认。
