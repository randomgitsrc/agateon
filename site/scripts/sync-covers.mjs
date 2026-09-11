// 把每篇博文的封面（blog/<日期>/<文章>/images/cover.svg）同步到 public/covers/。
// 为什么需要：正文内引用的 SVG 会被 Vite 按大小内联成 data URI 或改名进 assets/，
// 列表页/首页精选卡的 <img> 拿不到稳定 URL——列表页统一走 public/covers/。
// 命名约定（与 .vitepress/posts.ts 的 cover 字段一致）：
//   EN: covers/<日期>-<文章目录名>.svg   zh: covers/zh-<日期>-<文章目录名>.svg
// 幂等：每次先清空 covers/ 再拷贝（删掉的文章不留尸体）。
import { cpSync, mkdirSync, readdirSync, rmSync, existsSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join, resolve } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const siteDir = resolve(here, '..')
const coversDir = resolve(siteDir, 'public/covers')

rmSync(coversDir, { recursive: true, force: true })
mkdirSync(coversDir, { recursive: true })

// [博客根, 目标前缀]
const roots = [
  [resolve(siteDir, 'blog'), ''],
  [resolve(siteDir, 'zh/blog'), 'zh-'],
]

let n = 0
for (const [root, prefix] of roots) {
  if (!existsSync(root)) continue
  for (const dateDir of readdirSync(root)) {
    const datePath = join(root, dateDir)
    if (!/^\d{8}$/.test(dateDir)) continue
    const cover = join(datePath, 'images/cover.svg')
    if (!existsSync(cover)) continue
    // 目录结构：blog/<日期>/post-XX-slug.md + images/cover.svg（一日期一 post 一封面）。
    // 一目录多 post 时封面归属有歧义 → 跳过（宁缺毋错）。
    const posts = readdirSync(datePath).filter((f) => /^post-.*\.md$/.test(f))
    if (posts.length !== 1) continue
    const postBase = posts[0].replace(/\.md$/, '')
    cpSync(cover, join(coversDir, `${prefix}${dateDir}-${postBase}.svg`))
    n++
  }
}

console.log(`synced ${n} post covers → site/public/covers`)
