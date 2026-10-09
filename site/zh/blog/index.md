---
title: 博客
description: 构建 Agateon 的工程笔记与复盘。
---

# 博客

构建 Agateon 的工程笔记与复盘。

<script setup>
import { data as posts } from '../../.vitepress/zh-blog.data.ts'
import { withBase } from 'vitepress'
</script>

<ul class="post-list">
  <li v-for="post in posts" :key="post.url">
    <a :href="withBase(post.url)">{{ post.title }}</a>
    <span class="post-date">— {{ post.date }}</span>
  </li>
</ul>
