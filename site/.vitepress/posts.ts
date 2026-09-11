// site/.vitepress/posts.ts
// 博客文章清单的单一权威源：扫描 site/blog/（en）与 site/zh/blog/（zh）下的文章。
// 供 config.mts（sidebar）与 blog.data.ts / zh-blog.data.ts（主页/索引页）共用。
// 从此发博客只需新增文章文件（中文版由 i18n-translate.mjs 自动生成），索引/侧边栏/主页全部自动。
import { readdirSync, readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import path from 'node:path'

export type Locale = 'en' | 'zh'

export interface Post {
  title: string
  url: string
  date: string // YYYY-MM-DD
  description?: string
  cover?: string // 封面图 web 路径（存在 images/cover.svg 时）
  readingMinutes?: number
}

// 构建永远从 site/ 目录发起（本地与 CI 均如此，见 deploy-pages.yml 的 working-directory: site）。
// 用 import.meta.url 定位本文件所在目录更稳（不依赖 cwd），失败再回退 cwd。
let siteRoot: string
try {
  siteRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
} catch {
  siteRoot = process.cwd()
}

function blogRootFor(locale: Locale): string {
  return locale === 'zh' ? path.join(siteRoot, 'zh/blog') : path.join(siteRoot, 'blog')
}

// 极简 frontmatter 解析（够用即可：title/date/description 均为单行标量）
function parseFrontmatter(src: string): Record<string, string> {
  const m = src.match(/^---\r?\n([\s\S]*?)\r?\n---/)
  if (!m) return {}
  const out: Record<string, string> = {}
  for (const line of m[1].split(/\r?\n/)) {
    const kv = line.match(/^([A-Za-z_][\w-]*):\s*(.*)$/)
    if (kv) out[kv[1]] = kv[2].trim().replace(/^["']|["']$/g, '')
  }
  return out
}

function walkPosts(dir: string, baseRoot: string, prefix: string, acc: Post[]): void {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) {
      walkPosts(full, baseRoot, prefix, acc)
    } else if (entry.isFile() && entry.name.endsWith('.md') && !entry.name.startsWith('index')) {
      const src = readFileSync(full, 'utf8')
      const fm = parseFrontmatter(src)
      if (!fm.date) continue // 无 date 的不是文章页
      // 相对路径以语言级 blog 根为基准，保留日期目录（YYYYMMDD/post-XX-slug）
      const rel = path.relative(baseRoot, full).replace(/\\/g, '/').replace(/\.md$/, '')
      // 封面：列表页/首页精选卡统一走 public/covers/（构建前 sync-covers.mjs
      // 同步，命名 <日期>-<文章目录>.svg / zh-<日期>-<文章目录>.svg）——
      // 正文内引用的 SVG 会被 Vite 内联/改名，post 路径下拿不到稳定 URL。
      let cover: string | undefined
      try {
        readFileSync(path.join(dir, 'images/cover.svg'))
        const dashed = rel.replace(/\//g, '-')
        cover = prefix.startsWith('/zh')
          ? `/covers/zh-${dashed}.svg`
          : `/covers/${dashed}.svg`
      } catch {
        /* 无封面就不带 */
      }
      // 阅读时长：EN 按词数 /  ~220 wpm，zh 按字数 ~ 400 cpm（frontmatter 之后算）
      const body = src.replace(/^[\s\S]*?\n---\r?\n/, '')
      const zhChars = (body.match(/[\u4e00-\u9fff]/g) || []).length
      const words = body
        .replace(/```[\s\S]*?```/g, ' ')
        .split(/\s+/)
        .filter(Boolean).length
      const minutes = Math.max(
        1,
        Math.round(zhChars > words ? zhChars / 400 : words / 220),
      )
      acc.push({
        title: fm.title || rel,
        url: `${prefix}/${rel}`,
        date: fm.date,
        description: fm.description || undefined,
        cover,
        readingMinutes: minutes,
      })
    }
  }
}

// 全部文章，最新在前（date 字典序即时间序；同日期内 post-XX 号大的在前）
export function getAllPosts(locale: Locale = 'en'): Post[] {
  const root = blogRootFor(locale)
  const prefix = locale === 'zh' ? '/zh/blog' : '/blog'
  const posts: Post[] = []
  if (!exists(root)) return posts
  walkPosts(root, root, prefix, posts)
  return posts.sort((a, b) =>
    a.date === b.date ? (a.url < b.url ? 1 : -1) : a.date < b.date ? 1 : -1,
  )
}

function exists(p: string): boolean {
  try {
    return readdirSync(p).length >= 0
  } catch {
    return false
  }
}
