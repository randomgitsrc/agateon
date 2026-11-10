# 主 Agent 轮询 subagent 事故：根因与结论（2026-11-10）

> 状态：**部分修复已落地（文档层），判据层待决策**。本文是研判记录，不是立项文档。

## 事故

主 Agent 在 DSH 上并行派发两个 P4 评审后，7 次 `sleep 260~295; ls <产出文件> || echo "not yet"; date`，
累计约 38 分钟。期间一个评审已于 22:35 `approved`，却到 23:10 才被读取——**35 分钟等待一份已到手的结果**。

## 根因分级（三位专家独立研判后的裁定）

### ① 条文失实（已修）

`agate/dispatch-protocol.md:133` 原写「当前平台不支持 subagent 活动检测」，与**同文件 `:1045`**
（检测已由命令流机制承担，RM-AG0055 已落地）在同一文件内自相矛盾。这是无可争辩的事实错误。

`agate/dispatch-protocol.md:135` 原写「空返回后检查中间产物文件」——分诊专家核查后认定条文本身
**没写错**（`:133` 节标题、`:111` 均限定「空返回后」），是被挪了语境用于等待期。但原文无防，
已加限定语明确其为**一次性事后取证**。

### ② 判据缺陷（未修，须立项）

`agate-cmdstream-detect.py` 的 SPIN 判据 = `(cmd, exit, output_hash)` 三元组重复。可复现：

| 场景 | 判定 |
|---|---|
| 事故命令带 `date +%H:%M:%S`（输出每次不同）| **NORMAL**（理由："结果签名在变化（合法迭代特征）"）|
| 同一命令去掉 `date`（输出恒定）| SPIN，但被追加"可能是合法轮询循环" |

**这不是实现 bug**：`docs/design-notes/260903-.../…-v5-….md:168` 明文写「防误杀判据：结果签名在变化
→ 不触发空转」，BDD-15/16 已钉成断言。**洞在判据的假定本身**——"输出在变⇒有实质进展"被带时间戳
轮询证伪。

`_looks_like_polling()`（detect.py:252）把 `sleep` 列入合法轮询特征
`("watch","poll","checks --watch","sleep")`，任何带 sleep 的轮询触发 SPIN 后必被洗白为"可能合法"。

### ③ 结构性障碍（这是"必须立项"的实质原因）

事故场景与 BDD-16 的用例在 IR 层面**完全同构**：

| 场景 | 唯一命令 | 唯一 exit | 唯一 out |
|---|---|---|---|
| 事故（7 次）| 1 | 1 | 7 |
| BDD-16（5 次，被定义为合法迭代）| 1 | 1 | 5 |

唯一区分手段 = 输出归一化（剥离时间戳/耗时/pid）后比对，而 `CommandRecord` 只存 `output_hash`
不存明文 ⇒ 归一化必须在**三个 adapter 各自哈希之前**完成 ⇒ 改判据必然跨 `detect` 与 `adapters`
两个模块，且须推翻 BDD-15/16 既有断言。**hotfix 三条件不满足，须立项 + 独立评审。**

### ④ agent 个体失误（协议管不到的部分）

即使条文正确、机制有效，主 Agent 仍可能"等一份已到手的结果"。这属 harness 已内建能力
（DSH 工具描述原文："notifies you when it finishes"、"no need to keep checking its status"）。

## 附：适配器定位缺陷（已实测，本批**不修**）

`DSHAdapter.list_sessions(cwd)` 实为 `os.walk(cwd)`（扫项目目录），与 docstring 声明的
`~/.dsh/sessions/<sanitized-cwd>/` 矛盾 ⇒ 真实仓库上返回 **0**，而该项目平台会话目录下有 172 个
`.jsonl.zstd`。

**不修的理由不是不重要，而是单独修是净负**：`detect()` 的 `now` 取墙钟，已完成会话的最后活动
必然超阈值 ⇒ 修完立刻产出 **151 条假 FROZEN**（172 个会话实测），比现在静默 0 条更坏——假警报会
淹掉后续真信号。要修须三件同批：①会话选择器 ②活性前提（lock mtime/pid，未验证）③三平台契约
统一（Codex 有 `cwd or 默认根` 兜底，DSH/ClaudeCode 没有）= 定位机制重设计。

## 平台事实（跨平台专家核实）

| 平台 | 派发调用返回时 | 能否轮询 |
|---|---|---|
| DSH | 立即返回 id，完成时主动通知 | 能（但无意义）|
| Claude Code 2.1.301 | **默认后台，立即返回** | 能 |
| Codex 0.153.4 | 立即返回，`FINAL_ANSWER` 进父频道 | 能 |
| OpenCode | 前台默认阻塞；`background=true` 立即返回 | 能（后台模式）|

⇒ 只改 DSH 适配层会漏掉 3 个平台，且 Claude Code / OpenCode 是**逐调用**选择语义 ⇒
`executor_env` 能力字段无法表达该轴（P0 声明的平台属性在任务中途就会失真）。

## 未验证

- `session.lock` 可否作会话活性判据（119 个目录**全部**带该文件，长期存在）
- Claude Code「默认后台」的运行时门控标识
- Codex `spawn_agent` 在任何配置下是否阻塞

## 待决

1. 判据缺陷（D-b/D-c）是否立项 P0–P8。
2. 行为面落点：`~/.dsh/AGENTS.md` 第 12 条「后台 job」是否扩为「后台 job / subagent」（原句内替换，
   属新增内容，须用户许可）。

---

## 附二：根因诊断专家追加查出的三个实现缺陷（已逐条独立复核）

> 这三条是**实现 bug**，与上面的"判据设计缺陷"性质不同——它们让检测机制在事故现场
> 既看不见、看见了也判错。全部经我独立复测确认。

### 新-1｜SPIN 窗口取「会话最早 10 条」，不是最近 10 条

`agate-cmdstream-adapters.py:597` 的 DSH 适配器 `return records[::-1]`（**最新在前**，注释明写
"监控视角：最新事件在前"）→ CLI 按该序建事件 → `detect.py:220` `window = completed[-10:]`
取到列表尾部 = **时间最早**的 10 条。

实测（会话 `session-1f8a656d`，1773 条记录）：
- `recs[0].ts_start = 1789954478681`、`recs[-1].ts_start = 1787723626854` ⇒ 确为最新在前
- `completed[-10:]` 时间范围 = `1787723626854~1787723644772`，而全记录范围到 `1789954478681`
  ⇒ **窗口落在会话开头**

后果：对主会话跑 detect 得到 SPIN，理由是 `('',0,'da39a3ee…')` 重复——`da39a3ee…` 是
**空字符串 sha1**，命中的是会话开头 `command=""` 的 read/skill 调用。**与轮询无关的假阳性。**

附带：`--now` 对 SPIN 分支完全不生效（`now` 只在 FROZEN 分支用到），⇒ 该判据无法回答
"此刻是否在空转"。

### 新-2｜DSH 适配器丢失全部 exit code（真实失败被吞）

`agate-cmdstream-adapters.py:573` 取 `first.get("isError")`，其中 `first = message.content[0]`。
实测 DSH 真实结构（`tool/result`）：

```
data.message.content = [{"type":"text","text":"...---exit:0---\n"}]
data.message.isError = false
```

`content[0]` 只有 `type`/`text`，**没有 `isError`**。抽样统计（8 个会话、314 条 tool/result）：
- `content[0]` 含 `isError` 的条数：**0 / 314**
- `message.isError` 为 true 的条数：**4**

⇒ 全部记录 `exit=0`、`exit_signal=""`，**4 条真实失败被静默吞掉**。SPIN 签名的 exit 维度恒为 0。

（另注：输出文本自带 `---exit:N---` 标记，是比 `isError` 更直接的信号，可作为主判据。）

### 新-3｜`delegationDepth` 过滤从未实现

`adapters.py:26` / `:402` 三处 docstring 宣称"子 agent = delegationDepth>0 独立 session 文件"，
但 `list_sessions` 实现只有 `os.walk` + 后缀匹配，**无 depth 过滤**。
⇒ 该机制并不排斥主会话；它读不到主会话的唯一原因是 cwd 语义错配（见附一 D-a）。

## 事故记录的更正（专家实测，采信）

| 原记录 | 实测 |
|---|---|
| 7 次 sleep / 2295s | P4 窗口 **13 次 / 3765s**；全会话 **110 次 / 29490s** ⇒ 轮询是该会话**默认等待实现**，个案纠正无效 |
| backend approved 后 35 分钟「没启动实现」| 「没读它」成立（全会话未触及该文件）；「没启动实现」**不成立**——P4 五批 21:53 已全完，backend 0 CRITICAL 无需返工，需返工的 F-1~F-4 来自 23:08 才落盘的 design-review |

⇒ 真实损失 = 3765s + 13 轮往返、信息量≈0（6 次输出就是 `not yet`）。定性为**纯空转**，
不是"错过窗口"。这把"个体失误"的比重压低、"适配层遗漏"抬高。

---

## 已落地的修复（2026-11-10，未提交）

| 文件 | 改动 | 性质 |
|---|---|---|
| `agate/dispatch-protocol.md` | `:133` 删「当前平台不支持活动检测」失实句；`:135` 加「收到返回之后」「一次性事后取证，不是等待手段」 | 文档事实/歧义 |
| `agate/scripts/agate-cmdstream-adapters.py` | `isError` 改读 `message` 层级（content[0] 仅兜底）；文本补取 `content[0].text`；`exit` 优先解析输出内 `---exit:N---` 标记 | 实现 bug（新-2）|
| `agate/scripts/agate-cmdstream-detect.py` | SPIN 窗口按 `ts` 排序后取最近 N 条，不再依赖调用方列表顺序 | 实现 bug（新-1）|
| `agate/tests/unit/test_agate_cmdstream_adapters.py` | 新增真实结构回归用例（message 层级 isError） | 守护 |
| `agate/tests/unit/test_agate_cmdstream_detect.py` | 新增「列表顺序与时间反序」回归用例 | 守护 |

**回归测试有效性已验证**：两处修复都做了「临时回退 → 测试须红 → 恢复 → 转绿」的对照，
避免写出恒绿的空测试（第一版窗口测试曾恒绿，原因是构造数据里两种取法结果相同，已重做）。

**真实数据验证**（8 个会话 / 314 条记录）：
- 修复前：全部 `exit=0`，4 条真实失败被吞
- 修复后：310 条 `exit=0` + 4 条带 `exit_signal='Error:'`，与原始 `message.isError=true` 计数吻合

**门禁**：全量 pytest 3024 passed / 2 skipped；consistency 0 ERROR；ruff clean；用例数 3029。

## 仍未修（须决策）

- **D-a**（适配器定位）：见附一，单独修是净负，须与选择器/活性前提/三平台契约同批。
- **新-3**（`delegationDepth` 过滤未实现）：docstring 宣称、实现缺失。因 D-a 不修时该过滤
  无实际影响（反正扫不到跨项目会话），建议与 D-a 同批。
- **D-b/D-c**（判据可被时间戳绕过 + `sleep` 被当合法特征）：须推翻 BDD-15/16 假定，
  且归一化必须在 adapter 哈希前完成（跨模块），**须立项**。
- **事故记录更正**：真实损失 3765s/13 次（非 2295s/8 次），且「35 分钟没启动实现」不成立
  （当时无待启动工作）。轮询是该会话**默认等待实现**（全会话 110 次/29490s）⇒ 个案纠正无效。
