# P6 Progress — TAG0033 (P6 重做)

## Step 0: 启动 (2026-09-09)
- 工作目录: /home/kity/oclab/agateon/.worktrees/agate-TAG0033
- git status: gate-events.jsonl (M), P6-dispatch-context-verifier.md (??), P6-dispatch-prompt-verifier.md (??)
- codex-cli: 0.153.4
- 已读: P6-dispatch-context-verifier.md, verifier.md (P6 模式), P1-requirements.md (§6 30 BDD + §7 V1-V8)

## 待办
- [ ] 读 P3-test-cases.md / P4-implementation.md / P5-test-results/ / P2-design.md / archived real-machine-p6.md
- [ ] pytest --collect-only 拿 test id
- [ ] BDD-1~30 逐条实跑
- [ ] V6 三态真机
- [ ] V7/V2 复核
- [ ] 写 P6-acceptance.md + frontmatter
- [ ] 预检 gate 脚本

## Step 1: BDD 逐条实跑完成 (2026-09-09)
- BDD-1~17: 全部 pytest -v PASSED（adapters.py 12 条 + detect.py 5 条；含 BDD-5 guard、BDD-2 N1 fallback）
- BDD-18: full `pytest agate/tests/unit/ -q` → 1390 passed / 0 failed / 2 skipped (110.47s, exit 0)
- BDD-19: test_bdd_6_detect_consumes_registry_zero_change PASSED；git diff 证 `assert registered == {...}` → `.issubset()` + `assert "codex" in registered`
- BDD-20: check-protocol-consistency.py --strict-errors-only → exit 0 / 0 ERROR / 329 WARNING
- BDD-21: git diff main...HEAD detect.py+ir.py = 空；adapters.py = 252 insertions / 0 deletions（纯新增 CodexAdapter + _codex_* helper + import shlex；既有三 class 无删除行）；两守护测试 PASSED
- BDD-22~27: test_codex_platform_docs.py::test_bdd_22~27 全 PASSED + platform-notes.md/SETUP.md grep 锚词命中
- BDD-28: self-gate-review:/self-gate-skip: 前缀行在 main..HEAD commit body 中存在；3 个 alignment review (r0/r2/r3) 均 reviewer=protocol-alignment-review (agent≠main)；consistency 0 ERROR
- BDD-29/30: test_bdd_29/30 PASSED + P1 §7 V1-V8 四要素 + verification_env_budget + 穷尽 schema 项已登记
- 30/30 BDD 逐条 PASS（自查，非 gate）

## 待办
- [ ] V6 三态真机（① FROZEN ② NORMAL ③ SPIN）
- [ ] V7/V2 引用首轮 + 简短复核
- [ ] post-test 残留检查
- [ ] 写 P6-acceptance.md + frontmatter
- [ ] gate 预检

## Step 2: 真机 V6 三态 (2026-09-09, codex-cli 0.153.4 + ChatGPT)
- ① FROZEN: rollout-2026-09-09T12-07-54-01a08459-d4cb (codex exec sleep 600 前台, ~40s 后 SIGINT)
  → CommandExecution status="failed" exit_code=-1 + completed_at_ms
  → read-commands: 1 条 exit=-1 / exit_signal="exit_code=-1" / ts_end 非 None (F1: status=failed 判已结束)
  → detect --now ts_start+950s → VERDICT: FROZEN (活动冻结 suspect 919s≥300s); --now +30s → NORMAL
- ② NORMAL: rollout-2026-09-09T12-04-09-01a08456-640d (5 条秒级命令, 输出各异)
  → read-commands: 5 条 exit=0, output_hash 各异
  → detect --now last+30s → VERDICT: NORMAL; --now last+400s → FROZEN (活动冻结, 对照)
- ③ SPIN: rollout-2026-09-09T12-04-58-01a08457-242f (ls /demo/p6spin-nonexistent-xyz ×7)
  → read-commands: 7 条 status=failed → exit=2 / exit_signal="exit_code=2" / output_hash 恒定 67d40ac7 / ts_end 非 None
  → detect --now first+5s → VERDICT: SPIN (窗口10内重复7次≥5)
- V6 三态齐 = 完整通过 (① FROZEN ② NORMAL ③ SPIN)

## Step 3: V7 / V2 复核
- V7: attempt1 嵌套 grandchild "collaboration tool unavailable"(模型行为噪声); attempt2 成功
  → grandchild rollout depth=2, agent_path=/root/p6redo2_child/p6redo2_grand; child depth=1
  → 与 archived 首轮结论一致: 嵌套 spawn_agent 生效, depth 1→2 递增, 孙会话独立 rollout 同扁平目录
- V2: 本轮 spawn_agent function_call arguments 键 = {task_name,message,model,reasoning_effort,fork_turns}
  → 与 archived 首轮 9 次调用键并集一致, 无 background/timeout/permission 新键
- **V7 finding**: platform-notes.md 现「嵌套深度未测(归 P6 V7)」/「max_depth=1 待 V7 复核」已过时
  (P6 redo 实测 depth=2 可用) → 属待回写发现, 报告主 Agent, P6 不改 agate/

## Step 4: post-test 残留检查
- 无 codex/sleep 残留进程
- git status -- agate/ 完全干净 [PROD_NOT_TOUCHED]
- ~/.agate 近 40 分钟无文件改动
- gate-events.jsonl: 19 行 (HEAD 17 + 2 行 ts 03:56Z 会话前既有台账), 我的验证未追加

## 待办
- [ ] 写 real-machine-p6.md
- [ ] 写 P6-acceptance.md + frontmatter
- [ ] gate 预检

## Step 5: 产出 + gate 预检完成 (2026-09-09)
- P6-acceptance.md 写就: 30 PASS 行 + 交叉核对节(§2.1~2.6) + [PROD_NOT_TOUCHED] + Summary 30/30
- frontmatter: phase=P6 task_id=TAG0033 type=acceptance agent=verifier pass=30 fail=0 ui_affected=false
  (pass/fail 为证据字段脚本产出, 手写 30/0 与 PASS 行一致; ui_affected 经 agate-md-field-set.py 写入)
- P6-evidence/: bdd-01~30.log (含 EXIT_CODE 尾行) + real-machine-v6-{frozen,normal,spin}.log
  + real-machine-v7-v2.log + real-machine-p6.md  (35 文件)
- gate 预检 (自查, 非 gate):
  - check-p6-format.py --fix → exit 0
  - check-p6-evidence.py → exit 0 (30 条 BDD, 证据非空)
  - check-p6-provenance.py → exit 0 (EXIT_CODE 尾行补齐后无 warning)
  - check-gate.py P6 → exit 2 (P6 正常通过码, FAIL=0 NC=0 P6_TOTAL=30)
  - check-frontmatter.py → exit 0
- post-test 残留: agate/ CLEAN, 无 codex/sleep 进程, ~/.agate 无改动, .state.yaml 未动,
  gate-events.jsonl 仅既有台账痕迹(会话前), 我的验证未追加
- V7 finding 已写入 real-machine-p6.md + P6-acceptance.md §2.4 + BDD-25/BDD-24 行, 报告主 Agent
