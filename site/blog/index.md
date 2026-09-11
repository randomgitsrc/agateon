---
title: Blog
description: Engineering notes and retrospectives from building Agateon.
---

<script setup>
import { data as posts } from '../.vitepress/blog.data.ts'
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
    <p class="kicker">The Agateon Blog</p>
    <h1>Engineering notes from inside the gate</h1>
    <p class="blog-sub">How we orchestrate AI agents — and how we know when to trust them. Mechanisms, retrospectives, and the failures that shaped them.</p>
  </header>

  <a class="featured-post" :href="withBase(featured.url)">
    <img v-if="featured.cover" :src="withBase(featured.cover)" alt="" />
    <div class="fp-body">
      <p class="fp-kicker">Latest · {{ featured.date }} · {{ featured.readingMinutes }} min read</p>
      <h2>{{ featured.title }}</h2>
      <p class="fp-desc">{{ featured.description }}</p>
      <span class="fp-read">Read the post →</span>
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
          <span class="pr-min">{{ p.readingMinutes }} min</span>
        </a>
      </li>
    </ul>
  </section>
</div>
