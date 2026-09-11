import { defineConfig } from 'vitepress'
import { withMermaid } from 'vitepress-plugin-mermaid'
import { getAllPosts } from './posts'

// site/ 是产品 Web 层，在协议 gate 治理之外（见根 AGENTS.md「仓库四块」）。
// 唯一硬校验 = `npm run build` 通过（site-check.yml + deploy-pages.yml）。
//
// base：已绑自定义域名 agateon.com（2026-08-31），站点在域名根路径提供 → '/'。
// 改域名时同步改三处：base、head 里 og:image、语言跳转脚本里的 base。
//
// i18n：root = 英文（/），zh = 中文（/zh/）。中文内容由 site/scripts/i18n-translate.mjs
// 自动生成（Gemini free 翻译引擎，限额保护），发博客无需手工维护中文版。
export default withMermaid(
  defineConfig({
    base: '/',
    cleanUrls: true,
    srcExclude: ['guides/**'],
    head: [
      ['link', { rel: 'icon', href: '/favicon.svg', type: 'image/svg+xml' }],
      ['link', { rel: 'icon', href: '/favicon.ico', sizes: '32x32' }],
      ['link', { rel: 'apple-touch-icon', href: '/apple-touch-icon.png' }],
      // 浏览器语言自动跳转：首次访问且系统语言为中文 → 自动进 /zh/（只跳一次，
      // 之后用户用导航里的语言切换器自主选择，互不干扰）。
      [
        'script',
        {
          children: `(function(){try{
            var p=location.pathname;
            if(p.indexOf('/zh/')!==-1)return;
            if(localStorage.getItem('agateon_locale_seen'))return;
            var langs=navigator.languages||[navigator.language]||[];
            var prefersZh=langs.some(function(l){return (l||'').toLowerCase().indexOf('zh')===0});
            localStorage.setItem('agateon_locale_seen','1');
            if(prefersZh){var base='';location.replace(p.replace(new RegExp('^'+base+'(?=/|$)'),base+'/zh'));}
          }catch(e){}})();`,
        },
      ],
    ],
    locales: {
      root: {
        label: 'English',
        lang: 'en-US',
        title: 'Agateon',
        description: 'Verify AI agents the way a build system verifies a compiler.',
        head: [
          ['meta', { property: 'og:title', content: 'Agateon' }],
          [
            'meta',
            {
              property: 'og:description',
              content:
                'An open-source orchestration protocol that gates every phase of an agent\'s work with objective, machine-checkable signals.',
            },
          ],
          ['meta', { property: 'og:image', content: '/social-preview.png' }],
        ],
        themeConfig: {
          nav: [
            { text: 'Home', link: '/' },
            { text: 'Blog', link: '/blog/' },
            { text: 'GitHub', link: 'https://github.com/randomgitsrc/agateon' },
          ],
          sidebar: {
            '/blog/': [
              {
                text: 'Blog',
                // 文章清单自动生成（见 .vitepress/posts.ts），发博客无需手工登记 sidebar
                items: getAllPosts('en').map((p) => ({ text: p.title, link: p.url })),
              },
            ],
          },
          footer: {
            message: 'Verify AI agents the way a build system verifies a compiler.',
            copyright: 'Agateon',
          },
        },
      },
      zh: {
        label: '中文',
        lang: 'zh-CN',
        title: 'Agateon',
        description: '像构建系统验证编译器一样验证 AI Agent。',
        head: [
          ['meta', { property: 'og:title', content: 'Agateon' }],
          [
            'meta',
            {
              property: 'og:description',
              content:
                '一个开源编排协议：像构建系统验证编译器一样，用客观、可机器校验的信号给 AI Agent 的每个阶段把关。',
            },
          ],
          ['meta', { property: 'og:image', content: '/social-preview.png' }],
        ],
        themeConfig: {
          nav: [
            { text: '首页', link: '/' },
            { text: '博客', link: '/zh/blog/' },
            { text: 'GitHub', link: 'https://github.com/randomgitsrc/agateon' },
          ],
          sidebar: {
            '/zh/blog/': [
              {
                text: '博客',
                items: getAllPosts('zh').map((p) => ({ text: p.title, link: p.url })),
              },
            ],
          },
          footer: {
            message: '像构建系统验证编译器一样验证 AI Agent。',
            copyright: 'Agateon',
          },
        },
      },
    },
    themeConfig: {
      logo: { light: '/logo-mark.svg', dark: '/logo-mark-dark-bg.svg' },
      socialLinks: [
        { icon: 'github', link: 'https://github.com/randomgitsrc/agateon' },
      ],
      search: { provider: 'local' },
    },
  }),
)
