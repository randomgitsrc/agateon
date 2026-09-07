# 博客发布 Checklist（agent 照此逐项打勾，漏一步 = 不允许上线）

> **硬 gate：第 12 项「独立评审 PASS」之前，一切免谈。**
> 本清单是机械流程，质量标准看 `BLOG-STANDARDS.md`，细节命令看 `CONTRIBUTING.md`。
> 状态标记：`[ ]` 未做 / `[x]` 完成 / `[-]` 不适用。
> **2026-09-05 起执行活人感管线**：EN 定稿前过 voice pass（§2.1），zh 正文人工重写
> 不机翻（§9，i18n 脚本已改造为不碰正文）。

## A. 写稿与配图

- [ ] 1. 建目录 `site/blog/YYYYMMDD/post-XX-slug.md`（`YYYYMMDD`=发布日期，`XX`=当日序号）
- [ ] 2. frontmatter 四件套齐全：`title` / `date`（=目录日期）/ `description` / `tags`（3-4 个）
- [ ] 3. 开头 hook ≤3 句；长文（>800 词）有 TL;DR
- [ ] 4. 关键概念一图一意：封面（1200×630，必须）+ 正文插图（~900×520）/ mermaid
- [ ] 5. 每张图过了 vision OCR 质检（文字完整、无错字、无溢出、色板内）：
  `python3 ~/.dsh/skills/vision-engine/scripts/vision-analyze.py -i <png> -r ocr -f text`
- [ ] 6. 每个外链 / 内链实测存在（`curl -s -o /dev/null -w "%{http_code}" -L <url>` → 200；内链对应文件存在）

## B. 本地与评审

- [ ] 7. `cd site && npm run build` 通过、无 mermaid 报错
- [ ] 8. 术语首现必解释（gate / rung / BDD 等，对齐同系列文章的措辞）
- [ ] 9. 风格自检：诚实、无营销腔、主动暴露局限（对照 BLOG-STANDARDS §2）+
       **voice pass**（§2.1 活人感硬规则：警句 ≤2、节奏起伏、第一人称现场、列表克制）
- [ ] 10. 中文版：**zh 正文人工重写**（§9——i18n 脚本已不机翻正文，只处理配图与索引：
       `bash -lc 'node scripts/i18n-translate.mjs'`），zh 配图文案人工过词感
- [ ] 11. 中文版 build 通过（`zh/` 页面产出、`html lang="zh-CN"`）+
       zh 重写稿按 §9.2 自查（无翻译腔、数字与 EN 一致、站内链接指 /zh/blog/）

## C. 评审 gate（硬 gate）

- [ ] 12. **独立评审 PASS**：全新 subagent（无作者上下文）按 BLOG-STANDARDS §7 逐项核验；
       FAIL → 按意见迭代 → 复核，直到 PASS 才允许提交。

## D. 上线

- [ ] 13. `git add site/` → `/home/kity/bin/git-to-pr -m "docs(site): ..."` → `/home/kity/bin/git-to-main`
- [ ] 14. 线上验证：en 与 zh 页面 URL 均 HTTP 200 且标题/关键内容正确

## E. cross-post（合并后，可选但流程默认做）

- [ ] 15. **节奏检查：今天是否已 cross-post 过自己的内容？**（一天最多 1 条，见 CONTRIBUTING C）
       `[-]` 若今天已发过 → 顺延到第二天。
- [ ] 16. dev.to：`bash -lc 'cd site && DEV_TO_API_KEY=... node scripts/crosspost-devto.mjs post-XX-slug'`
       （先 `--dry-run` 验 body；缺英文 PNG 会自动渲染+提交；`--update <id>` 改已发布的）
- [ ] 17. HN：普通链接提交（不加 Show HN），title 用文章标题，url 用 dev.to 链接
- [ ] 18. 微信群：短文案（痛点开场 + 求讨论）

---

**2026-08-28 记录（post-03 evidence-ladder）**：A1-9 ✓ 10-11 ✓ 12 ✓（评审 FAIL→迭代→PASS）13-14 ✓
15 今日 post-02 已发 dev.to → **cross-post 顺延** 16 待 08-28 执行（dry-run 已验 body）17-18 待同日。

**2026-08-30 记录（post-04 right-to-look-away）**：A1-9 ✓ 10-11 ✓（zh 图 OCR 过；zh title 混入 "#" 已修+管道加防）12 ✓
（评审 FAIL 2 项：thin 路径方向写反+ceremony 未解释 → 复核 PASS）13-14 ✓（双语 200）
15 当日未 cross-post 过 → 可发 16 ✓（dev.to id 见仓库）17-18 待手动。

**2026-08-31 记录（post-05 we-break-our-own-gates）**：A1-9 ✓ 10-11 ✓ 12 ✓（评审 FAIL 1 项：
hook 4 句超限 → 修复+可选 ceremony 释义 → 复核 PASS）13-14 ✓（双语 200）15 当日未发 → 16 今日发。

**2026-09-03 记录（post-06 you-cant-delegate-what-you-cant-verify，愿景北极星篇）**：A1-9 ✓ 10-11 ✓（zh 图 OCR 双过）12 ✓（评审 PASS→修正 A1 事实口径/A2 语气越界/A4 断句/A5 与 post-04 归属 → 复核 PASS）13-14 ✓（双语 200，站点日期 20260903）15 当日未 cross-post 过 → 可发 16 ✓（dev.to id 4557758，canonical→agateon.com）17-18 待手动。

**2026-09-05 记录（post-07 give-your-ai-agent-a-flight-recorder，数字复盘·重构版）**：A1-9 ✓（写稿前数据核读：2 次 exit-1 归属 TAG0027 P4 + git 零痕迹验证 + 零回退修正 + PAUSED 仪表盲区发现）10-11 ✓（zh 图 OCR 双过）12 ✓（首轮 FAIL 2 必修：TL;DR 72%→74% 数字事故 + gate 首现定义；2 建议采纳：时间精度 + TAG0027 账本复现链接 → 复核 PASS，含 raw 账本 grep "exit":1=2 自洽验证）13-14 ✓（双语 200，站点日期 20260905）15 当日未 cross-post 过 → 可发 16 ✓（dev.to id 4579285，canonical→agateon.com）17-18 待手动。

**2026-09-05 补记（活人感管线落地 + post-07 zh 重做）**：用户反馈 blog 有 AI 味、zh 机翻腔重 → 三处固化：① i18n 脚本正文停用机翻（缺失/过期只告警，绝不生成绝不覆盖，死代码 translateMarkdown/chunk 机制清除）② BLOG-STANDARDS 新增 §2.1 活人感硬规则（警句 ≤2/节奏起伏/第一人称现场/列表克制）+ §9 中文重写规范（禁用词表/链接指 /zh/blog//数字零漂移）+ §7 评审加活人感与翻译腔两项 ③ publish-checklist 9/10/11 项更新。post-07 zh 正文按 §9 人工重写（机翻稿弃用）、zh 双图文案人工润色重渲染 OCR 过、build 过。

**2026-09-05 补记二（存量 zh 重写批次）**：post-01~06 六篇 zh 版按 §9 全部人工重写（6 并行 subagent，重写不翻译），13 张 zh SVG 文案润色+重渲染+OCR 双过。我方 QC（禁用词 0/内链全通/占位符 0/build 过）+ 批量独立评审 PASS（6/6，代码块与外链零漂移；3 处数字多集差异均判定为拼写转换非漂移）。9 处意见全采纳：P1 gate 补释义、P2/P3 内链锚统一为目标篇 zh 标题（P6→P5 经核 EN 锚本为行文变体，保持）、P3 语气词降到 2、TL;DR 引导符统一"——"、P6 凭空第一人称经历泛指化（评审正确拦截虚构作者经历）。

**2026-09-07 记录（post-08 no-agent-grades-its-own-homework，角色分离机制篇）**：A1-9 ✓（写稿前事实批重跑：TAG0027 链 23:31:44/23:33:00→02:56:45 + P4-review 三轮链 + retries 17/32 + MAX_JUDGE_VERDICT_EVENTS=2 + T016 三次空返回教训）10-11 ✓（双图 OCR+布局质检；cover 墙标签与副标题重叠已修）12 ✓（评审三轮：FAIL 插图未插正文+警句 5 超配额+术语首现 → FAIL 剩 L42 一句 → PASS；**期间事故：并行会话 git clean 清掉未提交的 20260907 目录，凭上下文全量重建，此后改完即 commit**）13-14 ✓（双语 200，站点日期 20260907）15 当日未 cross-post 过 → 可发 16 ✓（dev.to id 4597664，canonical→agateon.com，公开 200）17-18 待手动。流程教训：①插图引用进 md 后才 grep dist 双图（曾二犯 post-07 同款漏插）②共享 checkout 上未提交产物随时可能被并行会话清掉。
