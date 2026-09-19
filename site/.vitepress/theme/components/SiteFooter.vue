<script setup lang="ts">
// 全站富 footer（layout-bottom 注入）：品牌块 + 三列链接 + 底栏。
// 背景固定 ink 深底（明暗两版都用深色 footer 收尾，页面不"戛然而止"）。
import { useData } from 'vitepress'
import { computed, onMounted, onUnmounted, ref } from 'vue'

const { localeIndex } = useData()
const footerEl = ref<HTMLElement | null>(null)
let raf = 0

// 文章页左侧 sidebar 是 fixed(top:0;bottom:0)，滚动到底会盖住 footer。
// 监听滚动：footer 进入视口时把 sidebar 底部收缩到 footer 顶部上方。
// sidebar 每次滚动时实时查询（layout-bottom 挂载可能早于 sidebar 渲染）。
function updateSidebarBottom() {
  const sidebar = document.querySelector('.VPSidebar')
  if (!footerEl.value || !sidebar) return
  const ft = footerEl.value.getBoundingClientRect()
  const vh = window.innerHeight
  if (ft.top < vh) {
    sidebar.style.bottom = Math.max(0, vh - ft.top) + 'px'
  } else {
    sidebar.style.bottom = ''
  }
}

function onScroll() {
  if (raf) cancelAnimationFrame(raf)
  raf = requestAnimationFrame(updateSidebarBottom)
}

onMounted(() => {
  // 总是注册监听（layout-bottom 挂载时 sidebar 可能尚未渲染，
  // updateSidebarBottom 内部每次查询，sidebar 出现后自然生效）
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onScroll, { passive: true })
  updateSidebarBottom()
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
  if (raf) cancelAnimationFrame(raf)
})
const zh = computed(() => localeIndex.value === 'zh')
const year = new Date().getFullYear()

const cols = computed(() =>
  zh.value
    ? [
        {
          head: '产品',
          items: [
            { text: '快速开始', link: 'https://github.com/randomgitsrc/agateon' },
            { text: '一行安装', link: 'https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh' },
            { text: '版本发布', link: 'https://github.com/randomgitsrc/agateon/releases' },
          ],
        },
        {
          head: '文章',
          items: [
            { text: '博客（EN）', link: '/blog/' },
            { text: '博客（中文）', link: '/zh/blog/' },
            { text: 'dev.to', link: 'https://dev.to/agateon' },
          ],
        },
        {
          head: '项目',
          items: [
            { text: 'GitHub', link: 'https://github.com/randomgitsrc/agateon' },
            { text: 'Issue 区', link: 'https://github.com/randomgitsrc/agateon/issues' },
            { text: 'MIT 许可证', link: 'https://github.com/randomgitsrc/agateon/blob/main/LICENSE' },
          ],
        },
      ]
    : [
        {
          head: 'Product',
          items: [
            { text: 'Get started', link: 'https://github.com/randomgitsrc/agateon' },
            { text: 'One-line install', link: 'https://raw.githubusercontent.com/randomgitsrc/agateon/main/install.sh' },
            { text: 'Releases', link: 'https://github.com/randomgitsrc/agateon/releases' },
          ],
        },
        {
          head: 'Writing',
          items: [
            { text: 'Blog', link: '/blog/' },
            { text: '博客中文', link: '/zh/blog/' },
            { text: 'dev.to', link: 'https://dev.to/agateon' },
          ],
        },
        {
          head: 'Project',
          items: [
            { text: 'GitHub', link: 'https://github.com/randomgitsrc/agateon' },
            { text: 'Issues', link: 'https://github.com/randomgitsrc/agateon/issues' },
            { text: 'MIT License', link: 'https://github.com/randomgitsrc/agateon/blob/main/LICENSE' },
          ],
        },
      ],
)
</script>

<template>
  <footer ref="footerEl" class="site-footer">
    <div class="sf-inner">
      <div class="sf-brand">
        <img src="/logo-mark-dark-bg.svg" alt="" width="34" height="34" />
        <p class="sf-name">Agateon</p>
        <p class="sf-tag">
          {{ zh ? '像构建系统验证编译器一样验证 AI Agent。' : 'Verify AI agents the way a build system verifies a compiler.' }}
        </p>
        <p class="sf-mit">MIT · open source</p>
      </div>
      <nav v-for="col in cols" :key="col.head" class="sf-col" :aria-label="col.head">
        <p class="sf-head">{{ col.head }}</p>
        <a v-for="item in col.items" :key="item.text" :href="item.link"
           :target="item.link.startsWith('http') ? '_blank' : undefined"
           :rel="item.link.startsWith('http') ? 'noopener' : undefined">{{ item.text }}</a>
      </nav>
    </div>
    <div class="sf-bottom">
      <span>© {{ year }} Agateon</span>
      <span class="sf-dot">·</span>
      <a href="https://github.com/randomgitsrc/agateon" target="_blank" rel="noopener">GitHub</a>
    </div>
  </footer>
</template>
