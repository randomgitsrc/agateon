---
layout: home

hero:
  name: Agateon
  text: Agents on the gate.
  tagline: 把软件任务交给编排好的 agents，每一阶段用机器可校验的 gate 把关——交回来的是验证过的成果，而不是一份“应该能行”的自述。
  image:
    src: /hero-terminal.svg
    alt: 终端里跑着 agate next——三道 gate 通过，exit 0，状态机前进。
  actions:
    - theme: brand
      text: 快速开始
      link: https://github.com/randomgitsrc/agateon
    - theme: alt
      text: 阅读博客
      link: /zh/blog/
---

<div class="feature-grid">
  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M4 4v16M20 4v16M4 4h16"/>
      <path d="M9 13l3 3 5-6"/>
    </svg>
    <h3>任务进，验证过的成果出</h3>
    <p>把任务交给编排者。八个 phase——需求、设计、测试先行、实现、验证、验收、一致性、发布——每一阶段都必须通过机器可校验的 gate 才能前进。交回来的是有测试、有文档、可验证的成果。</p>
  </div>

  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4-3 7-7 9-4-2-7-5-7-9V6z"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
    <h3>gate 是硬边界</h3>
    <p>进度由客观信号裁决——测试 exit code、git log、BDD 计数——而不是“看起来差不多”。gate 失败会把阶段打回；信号不真实，就不会推进。</p>
  </div>

  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M6 3h8l4 4v14H6z"/>
      <path d="M14 3v4h4"/>
      <path d="M9 12h6M9 16h4"/>
    </svg>
    <h3>状态能扛过崩溃</h3>
    <p>所有进度都落在版本控制的 Markdown 里。会话中断可从断点恢复，每一步都能从 git 历史审计。</p>
  </div>

  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="3" y="7" width="5" height="10" rx="1.5"/>
      <rect x="9.5" y="7" width="5" height="10" rx="1.5"/>
      <rect x="16" y="7" width="5" height="10" rx="1.5"/>
    </svg>
    <h3>角色按设计隔离</h3>
    <p>一个编排者规划与派发，独立 subagent 执行，gate 评判。干活的那个 agent 永远不会给自己写的东西盖章。</p>
  </div>
</div>

## 快速开始

从全新的 checkout 安装并运行 Agateon：

```bash
curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
```

无需运行时，无需守护进程。协议是一组 Markdown 卡片加 gate 脚本，和你的工作代码一起存在版本控制里。

## 用 Agateon 构建的 Agateon

<div class="callout-band">

这个仓库就是自己的第一个用户：[`agate-workspace/tasks/`](https://github.com/randomgitsrc/agateon/tree/main/agate-workspace/tasks) 里的每一个任务——包括修复自己失败的那些，比如[独立裁判](https://github.com/randomgitsrc/agateon/tree/main/agate-workspace/tasks/TAG0020-independent-judge)——都是用 Agateon 跑自己产出的。清单本身就是证据，随任务增长。你将要依赖的那些 gate，正是构建这个站点的同一批 gate。

</div>

## 博客最新动态

<script setup>
import { data as posts } from '../.vitepress/zh-blog.data.ts'
import { withBase } from 'vitepress'

// 最新一篇精选卡（中文文章清单自动生成，见 .vitepress/posts.ts）
const latest = posts[0]
</script>

<a class="home-featured" :href="withBase(latest.url)">
  <img v-if="latest.cover" :src="withBase(latest.cover)" alt="" />
  <div class="hf-body">
    <p class="hf-kicker">最新 · {{ latest.date }} · 约 {{ latest.readingMinutes }} 分钟</p>
    <p class="hf-title">{{ latest.title }}</p>
    <p class="hf-desc">{{ latest.description }}</p>
    <span class="hf-more">阅读全文 →</span>
  </div>
</a>

[阅读全部文章 →](/zh/blog/)
