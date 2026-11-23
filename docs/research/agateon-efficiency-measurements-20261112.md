# Agateon 效率：实测机制数据（2026-11-12）

> **本文只记录可复核的测量结果，不含决策与建议。**
> 决策走 `docs/design-notes/` 与 `agate-workspace/roadmap/`。
> 证据强度标注沿用本目录图例：`[实测]` = 可复核。

## 调查方式与环境

- 数据源：DSH 会话日志 `~/.dsh/sessions/**/session*.jsonl.zstd`（逐帧解压读 `usage` 字段）
  + 两仓 `agate-workspace/tasks/*/gate-events.jsonl` 与 `.state.yaml`
- 样本：peekview 的 subagent 会话（`delegationDepth > 0`，短/中/长任务混合）；
  两仓全部任务的 `retries` 与 `gate_run` 事件
- 环境：DSH（deepseek-harness），本机 2026-11-11/12；被观测项目 peekview（Vue + Vitest）
- **口径限制**：单个模型、单个项目、单机。样本量小，凡标 `[推断]` 者未经独立复现，不得单独引用

> **本文的计数只写量级，不写绝对值。** 任务数、事件数、分桶 n、相关系数会随仓库增长单向漂移，
> 写死即过期。凡"具体多少"都用现场命令取，正文只保留不随增长失效的部分：**机制**与**方向**。
> （同一取向的先例：`agate/rules/phases.yaml` 在 gate 表一处注明「此处不写各 gate 的行号——行号是
> 必然漂移的数字，历史上已过期多次」，需要时现场 `grep -n` 取。）

## 1. 时间构成：模型推理占绝对多数 `[实测]`

| 指标 | 量级 |
|---|---|
| `step/start` → `assistant/message` 累计占比 | **中位约 97%**；约八成会话 >90%（少数会话相反，见下） |
| `tool/call` → `tool/result` 累计占比 | 与上互补，中位 **个位数百分比** |
| 单次 bash 执行耗时中位 | **亚秒级** |
| 每步（每 assistant message）耗时 | **十几秒**量级 |

⚠️ **不是所有会话都以思考为主**：实测存在工具占比高达八九成的会话（多为密集跑测试/构建的
子会话）。所以「时间主要花在思考」是**中位情形**，不是普遍规律——改造前应先确认目标场景落在哪一侧。

**推论边界**：对中位情形，任何以「优化工具调用开销」为目标的改动，时间收益上限就是那个个位数百分比。

现场取值：

```bash
python3 - <<'PY'
import json, glob, statistics, zstandard as zstd
subs=[]
for p in glob.glob('/home/kity/.dsh/sessions/*/*/session.v4.jsonl.zstd'):
    try:
        with open(p,'rb') as fh: head=zstd.ZstdDecompressor().stream_reader(fh).read(4000)
        if json.loads(head.decode('utf-8','replace').splitlines()[0]).get('delegationDepth',0)>0:
            subs.append(p)
    except Exception: pass
R=[]
for p in subs:
    with open(p,'rb') as fh: data=zstd.ZstdDecompressor().stream_reader(fh).read()
    ev=[]
    for l in data.decode('utf-8','replace').splitlines():
        if not l.strip(): continue
        try: o=json.loads(l)
        except Exception: continue
        if isinstance(o.get('time'),(int,float)): ev.append((o['time'],o.get('type')))
    ev.sort()
    th=tl=0.0; ps=pt=None
    for t,k in ev:
        if k=='step/start': ps=t
        elif k=='assistant/message' and ps: th+=t-ps; ps=None
        elif k=='tool/call': pt=t
        elif k=='tool/result' and pt: tl+=t-pt; pt=None
    tot=(th+tl)/1000
    if tot<60: continue      # 只取有效计算时间 >=60s 的会话，排除空闲/挂起
    R.append(th/(th+tl)*100)
print(f'sessions={len(R)} think% median={statistics.median(R):.1f} '
      f'| >90% 的会话占比={sum(1 for x in R if x>90)/len(R)*100:.0f}%')
PY
```

> ⚠️ **分母必须是「思考 + 工具」的累计，不能是会话墙钟跨度**。会话可跨天挂起（实测有单会话
> 跨度达 77 天），用墙钟做分母会算出 `think% = 95571` 这类不可能的数字。

## 2. 上下文增长与每步耗时**无正相关** `[实测]`

| 指标 | 量级 |
|---|---|
| `cacheReadTokens` 起点 | 每次会话固定（系统前言大小） |
| 首步 `totalTokens`（固定前言） | **数万** token |
| 单会话累计 `cacheReadTokens` | **百万级**（极值可达上亿） |
| 累计 `cacheRead` : 累计 `output` | **数十 : 1**（读取远多于生成） |
| 每步耗时 vs `cacheReadTokens` | **近零相关**（r < 0.1） |
| 每步耗时 vs 步数 | 中等正相关（r ≈ 0.6） |

反例（同批样本内）：一个会话上下文涨到 350k 时每步约 7 秒；另一个上下文仅 125k 的会话
每步约 28 秒——上下文小 3 倍，每步反而慢 4 倍。

**结论**：上下文线性膨胀，但**每步耗时由任务推理难度而非上下文长度决定**。
成本随步数呈二次增长（固定前言被重读 S 次），延迟随步数线性增长——两者是不同维度。

> ⚠️ `r ≈ 0.6`（每步耗时 vs 步数）是**组内**相关：会话内步数越多，后面步子越慢。
> 它与「上下文越长越慢」不矛盾——真正随时间增长的是步序，不是 token 量。

现场取值：

```bash
# 从会话日志取 usage（cacheReadTokens/totalTokens）与每步耗时，计算相关系数
python3 - <<'PY'
import json, glob, statistics, zstandard as zstd
xs=[]; ys=[]; steps=[]
for p in glob.glob('/home/kity/.dsh/sessions/*/*/session.v4.jsonl.zstd'):
    with open(p,'rb') as fh: data=zstd.ZstdDecompressor().stream_reader(fh).read()
    ps=None; n=0
    for l in data.decode('utf-8','replace').splitlines():
        if not l.strip(): continue
        try: o=json.loads(l)
        except Exception: continue
        t=o.get('time'); k=o.get('type')
        if k=='step/start' and isinstance(t,(int,float)): ps=t
        elif k=='assistant/message' and ps:
            u=(o.get('data') or {}).get('usage') or {}
            if u.get('cacheReadTokens'):
                xs.append(u['cacheReadTokens']); ys.append((t-ps)/1000); n+=1
            ps=None
    if n: steps.append(n)
def r(a,b):
    ma,mb=statistics.mean(a),statistics.mean(b)
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**0.5
    return num/den if den else 0
print(f'per-step vs cacheRead r={r(xs,ys):.3f}  samples={len(xs)}')
PY
```

## 3. 派发次数不随改动规模等比下降 `[实测]`

**测量方法**（可重跑）：按生产代码行数分组（`git show --numstat` 累加该 task_id 全部提交，
排除 `test/tests/spec/__tests__`、`*.md/*.mdx`、`*_test.*/*.test.*/*.spec.*`），
统计每任务的 `*dispatch-context*.md` 份数。**分母只含至少派发过 1 次的任务**——
0 派发的任务多为 P0 未启动或遗留，属「没跑」而非「跑得快」，混入会稀释结论。

**结论**：生产代码规模跨约 **100 倍**（≤100 行 → 1001–10000 行）时，平均派发份数只跨
约 **2.7 倍**（≈7 → ≈20）。⇒ 派发次数随规模增长，但**远低于线性**；小任务不因体量小
而显著减少派发。各分桶的 n 与均值见下方现场取值。

<details><summary>现场取值（计数会漂移，仅供核对量级）</summary>

```bash
python3 - <<'PY'
import glob, os, re, subprocess, statistics, collections
rows=[]
for repo in ['agateon','peekview']:
    root=os.path.expanduser('~/oclab/'+repo)
    for tdir in glob.glob(root+'/agate-workspace/tasks/*'):
        if not os.path.isdir(tdir): continue
        nd=len(glob.glob(tdir+'/*dispatch-context*.md'))
        if nd==0: continue
        shas=subprocess.run(['git','log','--all','--format=%H','--grep',
                             os.path.basename(tdir).split('-')[0]],
                            cwd=root,capture_output=True,text=True).stdout.split()
        prod=0
        for sha in shas:
            out=subprocess.run(['git','show','--numstat','--format=',sha],
                               cwd=root,capture_output=True,text=True).stdout
            for line in out.splitlines():
                p=line.split('\t')
                if len(p)<3: continue
                if re.search(r'(^|/)(test|tests|spec|__tests__)|\.(md|mdx)$|_test\.|\.test\.|\.spec\.',p[2]): continue
                try: prod+=int(p[0])
                except ValueError: pass
        rows.append((nd,prod))
b=collections.defaultdict(list)
for nd,prod in rows:
    k='<=100' if prod<=100 else ('101-1000' if prod<=1000 else ('1001-10000' if prod<=10000 else '>10000'))
    b[k].append(nd)
for k in ['<=100','101-1000','1001-10000','>10000']:
    if b[k]: print(f'{k:12s} n={len(b[k]):3d} mean={statistics.mean(b[k]):.1f}')
PY
```
</details>

## 4. gate 的低红率来自 retries 位于其上游 `[实测]`

**机制**（不写计数，故不随仓库增长失效）：

| 事实 | 现场复核命令 |
|---|---|
| `gate_run` 在 **commit 时**追加，每次提交一条 —— 不是每次评审尝试一条 | `grep -n '"event": "gate_run"' agate/scripts/pre-commit-gate.py` |
| `exit ∈ {0,2}` 都可能是**正常通过**：exit 2 是多数阶段（P0-P3/P5/P6/P8）的通过码，exit 0 是 P4/P7/P6.5 的通过码 | `grep -n 'gate_pass_exit' -B4 agate/rules/phases.yaml` |
| 只有 `exit 1` 是未通过，且它 `sys.exit(1)` 中止本次提交 | `grep -n 'gate_exit == 1' -A4 agate/scripts/pre-commit-gate.py` |
| `exit 1` 的事件在 abort **之前**已 append + `git add`，随**下一次成功提交**入库 ⇒ 账本里 exit 1 条数少于实际发生次数 | 同上（`append_event` 在 `sys.exit(1)` 之前） |
| `retries` 记在 `.state.yaml`，与 `gate_run` 无共同计数口径（前者按评审轮，后者按提交） | `grep -n 'retries' agate-workspace/tasks/*/.state.yaml` |

**结论**：`gate_run` 计数 ≈ **提交次数**，不是尝试次数；评审打回表现为 `retries`，
发生在 gate **之前**。⇒ **低红率不构成「gate 无判别力」的证据**——被 gate 拦下的样本
进不了这个分母。

**量级**（只用于判断方向，会漂移）：`retries` 合计比 `gate_run` 的 `exit 1` 条数多**一个数量级**。
现场取值：

```bash
# retries 合计（在各自仓库根执行；两仓需各跑一次）
python3 -c "import glob,yaml;print('retries',sum(len(v) for f in glob.glob('agate-workspace/tasks/*/.state.yaml') for v in ((yaml.safe_load(open(f)) or {}).get('retries') or {}).values()))"
# gate_run 按 exit 分桶（同上）
cat agate-workspace/tasks/*/gate-events.jsonl | python3 -c "import sys,json,collections;c=collections.Counter(d.get('exit_code',d.get('exit')) for d in map(json.loads,filter(str.strip,sys.stdin)) if d.get('event')=='gate_run');print('gate_run',c)"
```

## 5. 四条降级/分流通道的消费状态 `[实测]`

**三条零消费，一条已消费**（`phases:` 裁剪有机械判据，见末行）——不要把四条一并当作「待接线」。

| 通道 | 定义位置 | 消费情况 |
|---|---|---|
| `ceremony: thin` | `agate/WORKFLOW.md`「ceremony 档位」节、`agate/phase-cards/P1-requirements.md`「ceremony fail-closed 声明 checklist」节 | 全仓任务 frontmatter 中 `ceremony: thin` 声明 **0 次**（`TAG0019`/`TAG0022` 的命中均为正文 BDD 描述）；`check-routing.py` 只校验四要素格式，**无任何脚本按 thin 档位减少阶段或派发** |
| `gate_layer.commit_types` | `agate/rules/phases.yaml` 的 `gate_layer.commit_types` 键 | `grep -n "gate_layer\|commit_types" agate/scripts/*.py` = **0 命中** |
| 派发路由 | `agate-workspace/dispatch-routing.yaml` | 两仓 `dispatch_route` 事件 = **0** |
| `phases:` 裁剪 | P1 frontmatter | **已被机械消费**（非零消费）：`pre-commit-gate.py` 每次提交调 `check-pruning.py`，后者读 frontmatter `phases` 校验不可裁剪阶段（P1/P2/P4/P5/P6）与裁剪条件，`exit 1` 即中止提交；`check-state-transition.py` 走同一读取链判跨阶 |

**`phases:` 一项的复核命令**（判定接线必须查 gate 调用链，只 grep 脚本名会误判）：

```bash
grep -n 'check-pruning.py' agate/scripts/pre-commit-gate.py
grep -n 'non_prunable_phases\|_p1_pruned_and_declared' agate/scripts/check-pruning.py agate/scripts/check-state-transition.py
```

## 6. token / 步数的可得性 `[实测]`

`agate-summary.py` 输出「token / 步数**不可得**（harness 不报）——本工具不猜、不编造」
（定位：`grep -n 'token / 步数' agate/scripts/agate-summary.py`）。

实测：`~/.dsh/sessions/**/session*.jsonl.zstd` 内每条 `assistant/message` 带
`usage: {inputTokens, outputTokens, totalTokens, cacheReadTokens}`。
`agate-cmdstream-adapters.py` 的 `DSHAdapter._decompress` 已能解压同一批文件，
但 `CommandRecord`（`agate-cmdstream-ir.py` 十字段契约）未含 usage 字段。

**结论**：该数据在 DSH 平台可得；当前工具未采集。其他平台未核实。

## 7. 每消息工具调用数 `[实测]`

**量级**：中位约 **1.2 次**（即绝大多数 assistant 消息只发一个工具调用）。
**结论**：串行是现状的默认形态，并行工具调用未被使用。

现场取值（同时给出中位数与众数分布，避免只看均值）：

```bash
python3 - <<'PY'
import json, glob, statistics, zstandard as zstd
per=[]
for p in glob.glob('/home/kity/.dsh/sessions/*/*/session.v4.jsonl.zstd'):
    try:
        with open(p,'rb') as fh: head=zstd.ZstdDecompressor().stream_reader(fh).read(4000)
        if json.loads(head.decode('utf-8','replace').splitlines()[0]).get('delegationDepth',0)<=0: continue
    except Exception: continue
    with open(p,'rb') as fh: data=zstd.ZstdDecompressor().stream_reader(fh).read()
    am=tc=0
    for l in data.decode('utf-8','replace').splitlines():
        if not l.strip(): continue
        try: o=json.loads(l)
        except Exception: continue
        if o.get('type')=='assistant/message': am+=1
        elif o.get('type')=='tool/call': tc+=1
    if am: per.append(tc/am)
print(f'sessions={len(per)} median={statistics.median(per):.2f} mean={statistics.mean(per):.2f}')
PY
```

## 8. 工具构成（单个 P1 analyst 会话样本）`[实测]`

**观察**：在该样本中 bash 占绝大多数工具调用，其中读文件与搜内容两类合计超过八成。
`agate/assets/templates/dispatch-prompt.md` 与 `agate/assets/execution-roles/` 下各角色文件
**未对「用 read 工具还是 bash 读文件」作出规定**（`grep` 0 命中）；
`agate/assets/templates/dsh/SKILL.md` 有该规定（理由为「避免 bash 挂起」，**未提时间成本**；
定位：`grep -n 'bash 纪律' agate/assets/templates/dsh/SKILL.md`）。

**注意**：此为单会话观察，不构成「用 read 工具能提速」的证据——§1 已示工具耗时占比为个位数。

## 9. 与前沿材料的对照（供引用，非决策）

见下表的**机制主张**，不带各材料的实验数字（那些数字属于各自论文的样本，非本仓可复核事实）。

| 材料 | 机制要点 | 与本仓的关系 |
|---|---|---|
| [Anthropic《Building effective agents》](https://www.anthropic.com/engineering/building-effective-agents) | 可分解任务优先 workflow；程序化 gate 优于 LLM 自评 | 与 agateon 的 workflow 定位一致 |
| [Cognition《Multi-Agents: What's Actually Working》](https://cognition.com/blog/multi-agents-working) | clean-context reviewer 因 attention 机制更专注；反对共享上下文的自由协作 | `dispatch-protocol.md` 铁律 3（subagent 只返回路径+摘要）与 Anthropic「输出落 filesystem」同构；**已符合** |
| [Anthropic《How we built our multi-agent research system》](https://www.anthropic.com/engineering/multi-agent-research-system) | 多 agent 的 token 成本显著高于单 agent；同步执行是瓶颈 | 本仓同为串行同步派发，该项成本适用 |
| [Anthropic《Effective context engineering》](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) | context rot、attention budget、compaction、structured note-taking、subagent 返回短摘要 | 这些**机制本仓均无实现**（见下方 grep）。⚠️ 「未实现」≠「未提及」：`compaction` 有文档提及 |
| [arXiv:2512.08296](https://arxiv.org/abs/2512.08296)（DeepMind & MIT） | 多 agent 的开销主要是 **trace 级协调开销**，非错误率放大；集中式协调开销显著低于自由协作 | **支持** agateon 这种集中式形态。**不可**表述为「多 agent 放大错误 17.2 倍」 |
| [arXiv:2603.16244《More Rounds, More Noise》](https://ar5iv.labs.arxiv.org/html/2603.16244) | 跨上下文评审**最优轮数 = 1**；多轮产生假阳性压力与评审目标漂移；并行独立评审 + 多数投票优于串行多轮 | 与 `agate/phase-cards/P4-implementation.md`「review 不通过 → 再 review」的串行迭代模式**冲突**。⚠️ 适用性未在本仓验证（该论文为单模型、注入错误、韩语；且 agateon 每轮是**新**评审者，与论文的同评审者多轮不是同一设置） |
| [arXiv:2601.04748](https://arxiv.org/abs/2601.04748) | 可把多 agent 流程编译为单 agent 的 skill library，降低 token 与延迟 | 方向可参考，但**不建议照搬**：arXiv:2604.01608 报告 pipeline guidance 类内容存在反向效果 |

**本仓缺失（tracked 文件中 `git grep` 0 命中）**：`context rot`、`structured note-taking`、
`just-in-time`、skill library、semantic caching、按难度路由。

⚠️ `compaction` **不是** 0 命中——`docs/design-notes/subagent-context-mechanism.md` 与
`agate-workspace/archived/reviews/agate-improvement-guide.md` 均有提及（描述 OpenCode 的父会话压缩）。
"未实现"与"未提及"是两件事，勿混。复核：

```bash
git grep -l "compaction" -- '*.md' '*.py' '*.yaml'
git grep -l "context rot\|structured note-taking\|just-in-time\|semantic caching" -- '*.md' '*.py' '*.yaml'
```

## 10. 时效性复核清单

- **本文的计数一律不写绝对值**，只写量级 + 现场命令。复核的是**结论方向**（机制是否成立、
  有无机械消费、比例的数量级），不是把数字对回某个历史值——任务数与事件数只增不减地漂移
- 会话日志格式依赖 DSH 版本（`usage` 字段位置）；平台升级后需复核 §2、§6
- `gate_run` 写入时机依赖 `pre-commit-gate.py`；若改写入点，§4 的机制表需重测
- §3 的分组依赖 git 提交信息含 task_id；分母限定为「至少派发过 1 次」的任务
- §5 的结论随脚本接线变化，复核命令已在表内；**接线判定须查 gate 调用链**，不能只 grep 脚本名
  （`phases:` 一项曾因只查 `agate-next.py` 而误判为零消费）
- **行号一律不写**（同一取向的先例：`agate/rules/phases.yaml` 在 gate 表一处注明「此处不写各 gate
  的行号——行号是必然漂移的数字」）；需要定位时用文中的 `grep -n` 命令现场取
