# TAG0050 G3 复审（第 2 轮整改后）· 进度留痕

- 角色：review（P4 阶段门槛 · 聚焦复审）
- 对象：TAG0050 批 G3（D+E+F）第 2 轮整改（fix2），HEAD `b746d07d`，未提交
- 范围：**只核** BLOCKER-1 + MINOR-2/3/4 是否闭合 + 是否引入新阻断
- 只读纪律：被评审文件零编辑；独立复现只在**仓外可丢弃副本**（`/tmp/opencode/g3rerev*`）

## 步骤

1. 读 dispatch-context（G3-rereview）、首轮 `P4-review-G3.md`、`P4-implementation-G3.md`、fix2 dispatch、UPGRADING/CHANGELOG。
2. 读实现落点：`agate_common.read_judge_verdict`（透传 criteria）、`check-judge-verdict.py`（校验后移）、
   `check-gate.py` D7/D8 + `_gate_p7_structured` 枚举。
3. **独立复现 BLOCKER-1**（`/tmp/opencode/g3rerev/`，手工构造非 legacy 任务，非跑其用例）：
   - 声明 `criteria` 且 `status: passed` → **exit 0**（P6→P7 不再死锁）。
   - 缺 `criteria` → **exit 1**（文案「须在 frontmatter 声明 criteria」）。
   - 回退 `read_judge_verdict` 的 criteria 透传 → 正向用例转红（证明用例判别力）。
4. **新用例改前红判别力**（`/tmp/opencode/g3rerev2/` 副本内逐一回退实现后跑新用例）：
   - MINOR-2：回退弱化 D8 → 2/3 用例转红。
   - MINOR-3：回退单向 D7 → 2/4 用例转红（形态类）。
   - MINOR-4：删枚举校验 → 2/2 用例转红。
5. 目标 5 文件副本跑测（107 passed；3 条 cross_batch 失败为副本缺仓库根 docs/CHANGELOG 的环境假象）。
6. 真实仓库只读：`check-protocol-consistency.py` 0 ERROR/412 WARNING；level-1.yaml LF 归一 sha256
   `6ace03c9…` == LEVELS.yaml 登记；`count-tests.sh` 2866。

## 结论
BLOCKER-1 闭合（独立验证）；MINOR-2/3/4 闭合（有判别力用例）；未发现新阻断。
`[PROD_NOT_TOUCHED]`
