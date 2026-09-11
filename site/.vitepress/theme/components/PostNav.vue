<script setup lang="ts">
// 文章底部 prev/next 双卡（doc-footer-before 注入，只在博文路径渲染）。
// 列表按最新在前排序：index-1 = 较新，index+1 = 较旧。
import { useData, useRoute } from 'vitepress'
import { computed } from 'vue'
import { data as enPosts } from '../../blog.data.ts'
import { data as zhPosts } from '../../zh-blog.data.ts'

const { localeIndex } = useData()
const route = useRoute()
const zh = computed(() => localeIndex.value === 'zh')

const nav = computed(() => {
  const path = route.path.replace(/\.html$/, '')
  const list = zh.value ? zhPosts : enPosts
  const i = list.findIndex((p) => p.url === path)
  if (i === -1) return null
  return { older: list[i + 1] ?? null, newer: list[i - 1] ?? null }
})
</script>

<template>
  <nav v-if="nav && (nav.older || nav.newer)" class="post-nav" :aria-label="zh ? '博客导航' : 'Blog navigation'">
    <a v-if="nav.older" class="pn-card pn-prev" :href="nav.older.url">
      <span class="pn-label">← {{ zh ? '上一篇' : 'Previous' }}</span>
      <span class="pn-title">{{ nav.older.title }}</span>
      <span class="pn-date">{{ nav.older.date }}</span>
    </a>
    <span v-else class="pn-card pn-spacer" aria-hidden="true"></span>
    <a v-if="nav.newer" class="pn-card pn-next" :href="nav.newer.url">
      <span class="pn-label">{{ zh ? '下一篇' : 'Next' }} →</span>
      <span class="pn-title">{{ nav.newer.title }}</span>
      <span class="pn-date">{{ nav.newer.date }}</span>
    </a>
    <span v-else class="pn-card pn-spacer" aria-hidden="true"></span>
  </nav>
</template>
