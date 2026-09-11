---
title: 博客
description: 构建 Agateon 的工程笔记与复盘。
---

<script setup>
import { data as posts } from '../../.vitepress/zh-blog.data.ts'
import { withBase } from 'vitepress'

const [featured, ...rest] = posts
const groups = []
for (const p of rest) {
  const y = p.date.slice(0, 4)
  const g = groups.find((x) => x[0] === y)
  if (g) g[1].push(p)
  else groups.push([y, [p]])
}
</script>

<div class="blog-home">
  <header class="blog-header">
    <p class="kicker">AGATEON 博客</p>
    <h1>门内的工程笔记</h1>
    <p class="blog-sub">我们如何编排 AI agent——以及如何判断什么时候可以信它们。机制、复盘，和塑造这些机制的那些失败。</p>
  </header>

  <a class="featured-post" :href="withBase(featured.url)">
    <img v-if="featured.cover" :src="withBase(featured.cover)" alt="" />
    <div class="fp-body">
      <p class="fp-kicker">最新 · {{ featured.date }} · 约 {{ featured.readingMinutes }} 分钟</p>
      <h2>{{ featured.title }}</h2>
      <p class="fp-desc">{{ featured.description }}</p>
      <span class="fp-read">阅读全文 →</span>
    </div>
  </a>

  <section v-for="[year, list] in groups" :key="year" class="year-group">
    <h3 class="year-mark">{{ year }}</h3>
    <ul class="post-rows">
      <li v-for="p in list" :key="p.url">
        <a :href="withBase(p.url)">
          <span class="pr-date">{{ p.date.slice(5) }}</span>
          <span class="pr-main">
            <span class="pr-title">{{ p.title }}</span>
            <span class="pr-desc">{{ p.description }}</span>
          </span>
          <span class="pr-min">约 {{ p.readingMinutes }} 分钟</span>
        </a>
      </li>
    </ul>
  </section>
</div>
