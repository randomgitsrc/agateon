# 独立评审：cmdstream 修复批（2026-11-11）

> 评审对象：PR #477（`fix/cmdstream-exit-and-spin-window`，4 个 commit）。
> 结论：**REQUEST-CHANGES** → 5 项必修（C1/C2/M1/M2/M4，M5 文档一致性）已全部处理。
> 本文是留痕记录：按 `SELF-GATE.md`，本批改动触及脚本行为与判定结果，须按正常档留痕。

## 评审发现的必修项与处置

| 编号 | 评审结论 | 处置 |
|---|---|---|
| **C1** | D-b 修法对**事故命令原样形态无效**：真实 `date` 输出是 `2026年 11月 11日 星期三 14:52:17 CST`（zh_CN）/ `Wed Nov 11 14:52:17 CST 2026`（C locale），第 1 版只认 `HH:MM:SS`/ISO ⇒ 裸 `date` 逃逸，修完仍判 NORMAL | **已修**：`_LINE_DECOR_TIME_PATTERNS` 补 zh_CN 与 C locale 两种 date 形态。端到端复验：事故命令原样（两种 locale）均判 SPIN |
| **C2** | 位置判据引入新假阴性：`h("2026-11-09\n2026-11-10\n2026-11-11") == h("…\n2026-11-12")` → True（逐行日期被压平） | **部分修 + 记录为已知边界**：改为"只把整行时间当装饰"，行内一律保留；逐行纯日期列表仍会压平（单凭输出形态不可区分"日志装饰"与"表格数据"）。选择保留该漏判，放宽到行内会产生更严重的假阴性 |
| **M1** | exit 优先级反了：`---exit:N---` 无条件优先于 `isError` ⇒ `isError=true` + 输出含字面量 `---exit:0---` 会把失败报成成功；且该标记真实数据极罕见（评审实测 0/1336，我复测 3/15709）| **已修**：`isError=true` 优先，文本标记仅在成功侧兜底；矛盾时以 `isError` 为准。四种组合已逐一验证 |
| **M2** | exit 回归测试没守住 claim #1：只回退 `message.isError` 时测试仍绿（fixture 里的 `---exit:1---` 顶替了） | **已修**：fixture 失败用例去掉 `---exit:1---`，改断言 `exit != 0`（`isError` 不带具体码，故允许 None）。复验：仅回退 `message.isError` → 测试红 |
| **M4** | 轻量档不成立：`SELF-GATE.md:43-44` 要求"无判据语义、脚本行为、契约数据变化"，本批三条全中；`:57` 明写"同批还改了脚本/契约 ⇒ 按最重的走" | **已修**：本批按正常档留痕（本文即评审记录）；此前三个 commit 的 `self-gate-skip:` 判定错误，记录于此 |
| **M5** | 同一 diff 里的新文档自相矛盾（`docs/reviews/…root-cause.md` 写"未修/须立项"，而本分支正是修它） | **已修**：改为"已修"，并更正"须推翻 BDD-15/16"的错误判断（实测那些测试手工注入哈希，不经 `_sha1_hex`） |
| **m1** | 死代码 `_hash_fn()` | 已删 |
| **m2** | `_looks_like_polling` 的 `"poll"` 子串过宽（`cat poll.txt` 等会命中） | 已收窄为 `--watch` / `-watch` / `checks --watch` |
| **m3** | IR 契约语义未落文档：`output_hash` 归一化后不再是纯"内容哈希" | **已修**：`agate-cmdstream-ir.py` 字段注释补充归一化语义 |

## 评审确认有效的部分

- **回退对照全部有效**（评审亲自复验）：`_sha1_hex` 去归一化 → 2 红；`sleep` 加回 → 1 红；
  SPIN 窗口改回 `completed[-N:]` → 红；`c051b7b0` 改回全局正则 → 3 红（含 `keeps_inline_time_as_data`）。
- **claim #1 成立**（`content[0].isError` 0 条 vs `message.isError` 28 条，评审样本）。
- `_LINE_IS_ONLY_TIME` 的多行处理正确（空行+时刻、CRLF、行尾换行均 ✓，`test_bdd_4` 不破）。
- `pid` 边界不误伤 `rapid=5`/`torpid 9`。

## 未验证项（如实记录）

- 评审未跑全量 pytest；我跑了（3030 passed / 2 skipped）。
- 抽样规模不同：评审 3 会话 / 1336 条，我 4 会话 / 15709 条。两者都观察到
  `message.isError=true` 存在；`content[0].isError` 的存在性两者结论不同
  （评审 0 条、我 6403 条），说明**两种格式在不同会话版本里都存在** ——
  现行实现 `message` 优先 + `content[0]` 兜底正好覆盖。
