import DefaultTheme from 'vitepress/theme'
import { h } from 'vue'
import './index.css'
import './blog.css'
import SiteFooter from './components/SiteFooter.vue'
import ArticleMeta from './components/ArticleMeta.vue'
import PostNav from './components/PostNav.vue'

// 默认主题 + 三个注入位：
//   layout-bottom      → 富 footer（全站，替代默认两行 footer）
//   doc-top            → 文章 meta 条（ArticleMeta 自判是否博文路径）
//   doc-footer-before  → prev/next 双卡（PostNav 自判）
export default {
  extends: DefaultTheme,
  Layout: () =>
    h(DefaultTheme.Layout, null, {
      'layout-bottom': () => h(SiteFooter),
      'doc-top': () => h(ArticleMeta),
      'doc-footer-before': () => h(PostNav),
    }),
}
