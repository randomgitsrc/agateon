<script setup lang="ts">
// 文章页 meta 条（doc-top 注入，只在博文路径渲染）：
// 日期 · 阅读时长 · tags chips，位于 h1 之上的 editorial kicker。
import { useData, useRoute } from 'vitepress'
import { computed } from 'vue'
import { data as enPosts } from '../../blog.data.ts'
import { data as zhPosts } from '../../zh-blog.data.ts'

const { frontmatter, localeIndex } = useData()
const route = useRoute()
const zh = computed(() => localeIndex.value === 'zh')

const post = computed(() => {
  const path = route.path.replace(/\.html$/, '')
  const list = zh.value ? zhPosts : enPosts
  return list.find((p) => p.url === path) ?? null
})

const tags = computed(() => {
  const t = frontmatter.value.tags
  return Array.isArray(t) ? (t as string[]) : []
})

const dateLabel = computed(() => (post.value?.date ? post.value.date.replace(/-/g, '.') : ''))

</script>

<template>
  <div v-if="post" class="article-meta">
    <span class="am-date">{{ dateLabel }}</span>
    <span v-if="post.readingMinutes" class="am-sep">·</span>
    <span v-if="post.readingMinutes" class="am-min">{{
      zh ? `约 ${post.readingMinutes} 分钟` : `${post.readingMinutes} min read`
    }}</span>
    <span v-if="tags.length" class="am-tags">
      <span v-for="t in tags" :key="t" class="am-tag">#{{ t }}</span>
    </span>
  </div>
</template>
