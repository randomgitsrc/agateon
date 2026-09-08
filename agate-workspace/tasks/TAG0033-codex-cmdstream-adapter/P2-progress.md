# TAG0033 P2 progress (architect)

## 2026-09-09 启动
- 读 P2-dispatch-prompt-architect.md + P2-dispatch-context-architect.md：完成
- 读 P1-requirements.md + P0-brief.md：完成
  - 核心：CodexAdapter 5 设计点、3 SUGGEST 已采纳、零改动硬约束、candidate_count>=2
  - P1 §4 spike 已定事实：rollout JSONL 目录/格式、CommandExecution 源、exit_code 有数字、子会话独立文件
- 下一步：读 adapters.py DSHAdapter / ir.py / detect.py / test 文件 / fixtures / platform-notes / SETUP / phase-card / architect role

## 读码完成（adapters/ir/detect/test_adapters）
- adapters.py：DSHAdapter line 394-618（probe=endswith .jsonl.zstd；list_sessions=os.walk sorted；_detect_truncated 双信号 line 468-496；_build_record line 565-618）
- ir.py：CommandRecord 十字段 dataclass line 31-44，不改；from_dict 类型校验
- detect.py：ADAPTERS = _load_adapters().ADAPTERS line 96；CLI choices=sorted(ADAPTERS.keys()) 动态；阈值常量 line 42-50
- test_agate_cmdstream_adapters.py:317 `assert registered == {"claude-code","opencode","dsh"}`（test_bdd_6_detect_consumes_registry_zero_change）—— 确认精确等值，需改包含式
  - :298 已是 `>=` 包含式（test_bdd_6_adapter_registry_contract）不用改
  - :326 test_bdd_7_fixture_sanitized 脱敏清单需加 codex-session.jsonl

## 读码完成（detect test / fixtures / platform-notes / SETUP / architect role / AGENTS）
- test_agate_cmdstream_detect.py:371 test_bdd_24 负向断言 `("claude","opencode","dsh")` — 可选加 "codex"
- dsh-session.jsonl fixture 结构范式已读
- platform-notes.md:43-45 Codex「待补充」；:53-70 Hardening-roadmap 跨平台表已有 Codex 列 + :67-70 max_depth=1 注记
- SETUP.md:144-175 DSH 小节范式（安装/hook/版本敏感提示）
- architect.md：影响面梳理三部分 / 批次设计强制节 / minimal_validation 规格
- AGENTS.md:17-24 改脚本 TDD 工作流；:54 check-protocol-consistency 必须用 worktree 自己的

## minimal_validation 已执行（真实 ~/.codex/sessions/ 23 rollout 文件）
- 行信封键恒 {ordinal,payload,timestamp,type}；首行恒 session_meta
- CommandExecution item_completed：payload {completed_at_ms,item,started_at_ms,thread_id,turn_id,type}
  - started_at_ms/completed_at_ms = epoch ms int（样例 1788868081170/…171）
  - item 键含 command(数组 ["/bin/bash","-lc",...])/exit_code(int 0)/status("completed")/aggregated_output(str,最长5442,无截断标记)
- 主会话 session_meta.payload: id==session_id；thread_source=="user"；cli_version=="0.153.4"；originator=="codex-tui"
- 子会话 session_meta.payload（2 样例）: id=子自身；session_id=父；thread_source=="subagent"；parent_thread_id/forked_from_id=父；source.subagent.thread_spawn.depth==1 → 证实设计点3 取 basename 不取 payload.session_id
- apply_patch→FileChange item / web__run→Extension item（非 CommandExecution）→ BDD-8 由源过滤天然满足
- 无 item_started CommandExecution 样例（命令秒级完成）→ pending 形态仍 [未实测]，走双判据易收敛形式

## 下一步：写 P2-design.md

## P2-design.md 写完 + frontmatter 校验
- 452 行；影响面梳理节（2.1 改什么 / 2.2 不改什么 / 2.3 风险 R1-R10）写在 5 设计点之前
- 5 设计点每点候选(3)+权衡+定论；candidate_count=3；follows_existing_pattern=[adapters.py]
- frontmatter：agate-md-field-set 逐字段写入（packages/domains 用空格分隔值修正了首次方括号误写）
- check-frontmatter.py P2-design.md → EXIT=0
- gate_commands：P3 / P5 / P5_consistency(worktree 路径) / P5_shellcheck；无 P3_xxx / 无 && / 无 P5_e2e
- dispatch_plan: static-batch, parallel_limit 2, batches [adapter-core(medium), protocol-docs(low)]
- 范围外发现：无（未触发 P1 §5 逃生阀）
- [PROD_NOT_TOUCHED]

---
## [plan-eng-review] 独立工程评审启动 (2026-09-09, trace_id=TAG0033-P2-review-20260909)
- 已读: P2-dispatch-prompt-plan-eng-review.md / P2-dispatch-context-plan-eng-review.md / review-roles/plan-eng-review.md
- 8 项必核维度已明确
- 下一步: 读 P2-design.md (受评对象)

## [plan-eng-review] 已读 P2-design.md(452行) / P2-progress.md / P1-requirements.md / P0-brief.md
- 下一步: 独立读码核实 — adapters.py (契约+DSHAdapter+ADAPTERS) / ir.py / detect.py / test 文件 / fixtures

## [plan-eng-review] 独立核实完成 (2026-09-09)
- 读码: adapters.py(契约+3适配器+DSHAdapter全段+ADAPTERS) / ir.py(CommandRecord十字段) / detect.py(阈值+detect()+CLI record→event 转换) / check-tdd-red.py / agate-read-gate-commands.py(key=="P3"精确) / check-protocol-consistency.py(AUTHORITATIVE_VALUE_ANCHORS只含retry-max, platform-notes/SETUP整文件豁免) / test_agate_cmdstream_adapters.py(:317精确等值, :298已>=) / test_agate_cmdstream_detect.py(:371负向)
- 跑: python3 -c shlex.join([/bin/bash,-lc,echo

## [plan-eng-review] 独立核实完成 (2026-09-09)
- 读码: adapters.py(契约+3适配器+DSHAdapter全段+ADAPTERS) / ir.py(CommandRecord十字段) / detect.py(阈值+detect()+CLI record->event 转换) / check-tdd-red.py / agate-read-gate-commands.py(key=='P3'精确匹配) / check-protocol-consistency.py(AUTHORITATIVE_VALUE_ANCHORS只含retry-max; platform-notes/SETUP整文件豁免) / test_agate_cmdstream_adapters.py(:317精确等值,:298已>=) / test_agate_cmdstream_detect.py(:371负向断言)
- 跑 shlex.join(bash -lc echo hi) => 结果为  /bin/bash -lc 后跟带引号的 echo hi ；子串判定 'echo hi' in 结果 => True（BDD-4 判据满足，无双重转义破坏"含"判据的问题）
- grep 全测试树: 唯一会被第四键打破的精确等值断言 = test_agate_cmdstream_adapters.py:317（已被 BDD-19 覆盖, 位于 P3 锁定的两文件之一内）
- probe 未在任何脚本中被调用（仅 BDD 隔离测试用）→ 与 ClaudeCodeAdapter.probe 的 .jsonl 扩展名重叠为无害（不用于自动派发）
- list_sessions: 既有适配器把 cwd 直接喂给 os.walk, 无 expanduser fallback; CLI 的 cwd 为必填位置参数（恒为字符串）
- 结论: status=approved; 4 条非阻塞观察 (N1 list_sessions fallback 依据待建组件 RM-AG0060 / N2 sorted 表述与 DSH 实际(逐目录)不精确 / N3 test_bdd_7 对 Codex 连字符 uuid 脱敏覆盖偏弱, 建议同批补负向断言 / N4 ts_start:int 类型提示 vs 设计的 None 兜底 -- 与 DSHAdapter 既有行为一致, detect CLI 已跳过 ts_start is None)
- 下一步: 写 P2-review.md

## [plan-eng-review] P2-review.md 已产出 (2026-09-09)
- 路径: agate-workspace/tasks/TAG0033-codex-cmdstream-adapter/P2-review.md
- status: approved (agent=plan-eng-review, agent != main)
- frontmatter 经 agate-md-field-set 写 status=approved; 其余 phase/task_id/parent/trace_id/created/agent 按 dispatch-context 值写入 (对照 TAG0030/TAG0031 P2-review.md 惯例一致); --list 提示的 candidate_count/packages/domains/ui_affected/gate_commands 是 P2-design.md 字段, 不适用于 review 文件
- 预跑 check-gate.py P2 => EXIT=2 (= 全部硬校验通过, 仅剩 gate_commands 动态读取由主 Agent 判定; 非失败)
- 8 维度全部 PASS; 无 BLOCKER; 4 条非阻塞观察 N1-N4
- [PROD_NOT_TOUCHED]
