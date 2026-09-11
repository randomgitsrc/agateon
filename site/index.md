---
layout: home

hero:
  name: Agateon
  text: Agents on the gate.
  tagline: Run your software task through orchestrated agents and machine-checked gates — you get a verified result out, not a story about how it should work.
  image:
    src: /hero-terminal.svg
    alt: A terminal running agate next — three gates pass, exit 0, the state machine advances.
  actions:
    - theme: brand
      text: Get started
      link: https://github.com/randomgitsrc/agateon
    - theme: alt
      text: Read the blog
      link: /blog/
---

<div class="feature-grid">
  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M4 4v16M20 4v16M4 4h16"/>
      <path d="M9 13l3 3 5-6"/>
    </svg>
    <h3>Task in, verified result out</h3>
    <p>Hand the task to the orchestrator. Eight phases — requirements, design, test-first, implementation, verification, acceptance, consistency, release — each must pass a machine-checkable gate before the state machine advances. What comes out is tested, documented, verifiable work.</p>
  </div>

  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M12 3l7 3v5c0 4-3 7-7 9-4-2-7-5-7-9V6z"/>
      <path d="M9 12l2 2 4-4"/>
    </svg>
    <h3>Gates are hard boundaries</h3>
    <p>Progress is decided by objective signals — test exit codes, git log, BDD counts — not by “looks about right.” A failed gate bounces the phase back; nothing advances until the signal is real.</p>
  </div>

  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <path d="M6 3h8l4 4v14H6z"/>
      <path d="M14 3v4h4"/>
      <path d="M9 12h6M9 16h4"/>
    </svg>
    <h3>State survives crashes</h3>
    <p>All progress lives in version-controlled Markdown. A killed session resumes where it left off, and every step is auditable from git history.</p>
  </div>

  <div class="feature-card">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
      <rect x="3" y="7" width="5" height="10" rx="1.5"/>
      <rect x="9.5" y="7" width="5" height="10" rx="1.5"/>
      <rect x="16" y="7" width="5" height="10" rx="1.5"/>
    </svg>
    <h3>Roles separated by design</h3>
    <p>One orchestrator plans and dispatches; independent subagents execute; gates judge. The agent doing the work never signs off on its own work.</p>
  </div>
</div>

## Quick start

Install and run Agateon from a fresh checkout:

```bash
curl -sSL https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh | bash
```

No runtime, no daemon. The protocol is a set of Markdown cards plus gate scripts, stored in version control alongside your work.

## Built with Agateon

<div class="callout-band">

This repository is its own first customer: every task in [`agate-workspace/tasks/`](https://github.com/randomgitsrc/agateon/tree/main/agate-workspace/tasks) — 26 of them, including the fixes for its own failures, like the [independent&nbsp;judge](https://github.com/randomgitsrc/agateon/tree/main/agate-workspace/tasks/TAG0020-independent-judge) — was produced by running Agateon on itself. The gates you'd rely on are the same gates that built this site.

</div>

## Latest from the blog

<script setup>
import { data as posts } from './.vitepress/blog.data.ts'
import { withBase } from 'vitepress'

// 最新一篇精选卡（文章清单自动生成，见 .vitepress/posts.ts）
const latest = posts[0]
</script>

<a class="home-featured" :href="withBase(latest.url)">
  <img v-if="latest.cover" :src="withBase(latest.cover)" alt="" />
  <div class="hf-body">
    <p class="hf-kicker">Latest · {{ latest.date }} · {{ latest.readingMinutes }} min read</p>
    <p class="hf-title">{{ latest.title }}</p>
    <p class="hf-desc">{{ latest.description }}</p>
    <span class="hf-more">Read the post →</span>
  </div>
</a>

[Read all posts →](/blog/)
