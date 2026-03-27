# yu-changqian.github.io

Personal academic website built with Jekyll. Bilingual (EN/ZH), auto-deployed to GitHub Pages.

## Quick Start

```bash
# Install dependencies (requires Ruby 3.x)
bundle install

# Local development with live reload
bundle exec jekyll serve --livereload

# Build for production
JEKYLL_ENV=production bundle exec jekyll build
```

Site runs at `http://localhost:4000`. Push to `main` branch triggers automatic deployment via GitHub Actions.

## Project Structure

```
.
├── _config.yml            # Site metadata, author info, social links, plugins
├── _data/
│   ├── about.yml          # ★ Personal info, tagline, bio, career timeline, open source
│   ├── publications.yml   # ★ Publication list (auto-updated citations)
│   ├── news.yml           # ★ News/updates on homepage
│   ├── awards.yml         # ★ Awards, challenges, services, talks
│   └── i18n.yml           # UI text translations (EN/ZH)
├── _includes/
│   ├── hero.html          # Hero section (reads from about.yml)
│   ├── timeline.html      # Career timeline (reads from about.yml)
│   ├── publication.html   # Single publication card component
│   ├── nav.html           # Navigation bar
│   ├── head.html          # <head> meta, fonts, JSON-LD, theme script
│   ├── footer.html        # Site footer
│   ├── social-icon.html   # SVG icon component
│   └── awards-content.html
├── _layouts/
│   ├── default.html       # Base layout (nav + main + footer + JS)
│   ├── page.html          # Generic page layout
│   └── post.html          # Blog post layout
├── _sass/
│   ├── _variables.scss    # Design tokens (colors, fonts, spacing)
│   ├── _base.scss         # Reset, typography, global styles
│   ├── _dark.scss         # Dark mode overrides
│   ├── _layout.scss       # Nav, footer, container, sections
│   ├── _components.scss   # Cards, tags, buttons, news list
│   ├── _home.scss         # Hero, timeline, open source, pub grid
│   ├── _blog.scss         # Blog list and post page
│   └── _awards.scss       # Awards page
├── _posts/                # Blog posts (Markdown)
├── assets/
│   ├── css/main.scss      # SCSS entry point
│   ├── js/main.js         # Theme toggle, mobile nav, scroll effects
│   └── img/               # Images (bio photo, favicons, timeline logos, pub previews)
├── index.html             # English homepage
├── zh/                    # Chinese versions of all pages
│   ├── index.html
│   ├── publications.md
│   ├── blog.html
│   └── awards.html
└── .github/workflows/
    ├── deploy.yml         # Auto-deploy on push to main
    └── update-citations.yml  # Weekly citation count updates
```

## How to Update Content

### Personal Info (name, tagline, bio)

Edit `_data/about.yml`:

```yaml
name:
  en: "Your Name"
  zh: "你的名字"

tagline:
  en: "One-liner about what you do"
  zh: "一句话介绍"

bio:
  en:
    - "A paragraph in **Markdown** with [links](). Rendered via markdownify."
  zh:
    - "对应的中文段落。"
```

### Career Timeline

Edit the `timeline` section in `_data/about.yml`:

```yaml
timeline:
  - period: "2025 –"
    logo: "/assets/img/logos/kuaishou.svg"   # optional
    logo_alt: "Kuaishou"                     # optional
    en: "Narrative paragraph with **bold** and [links](url)."
    zh: "对应的中文叙事。"
  - period: "2023 – 2025"
    en: "..."
    zh: "..."
```

Tips:
- Write in first person, narrative style (not bullet points)
- Bold product names: `**Kling-Image-O1**`
- Use `[text](url)` for links; leave `()` empty as placeholder
- Entries render top-to-bottom; put most recent first
- Timeline logos are loaded from `assets/img/logos/` (SVG preferred)

### Open Source Projects

Edit the `open_source` section in `_data/about.yml`:

```yaml
open_source:
  - name: "ProjectName"
    url: "https://github.com/..."
    paper: "https://arxiv.org/..."   # optional
    desc:
      en: "Short description."
      zh: "简短描述。"
```

### Publications

Edit `_data/publications.yml`. Each entry:

```yaml
- key: author2024title          # unique ID
  title: "Paper Title"
  authors: "Author A, <strong>Your Name</strong>, Author B"
  venue: CVPR                   # used for colored tag (tag--cvpr)
  venue_full: "CVPR 2024"
  year: 2024
  selected: true                # shows on homepage if true
  google_scholar_id: "xxx"      # for auto citation updates
  citations: 42                 # auto-updated weekly by GitHub Action
  links:
    arxiv: "2401.12345"
    code: "https://github.com/..."
    paper: "https://..."
  preview: filename.png         # image in assets/img/publication_preview/
```

Citation counts are auto-updated every Monday by `.github/workflows/update-citations.yml`.

### News

Edit `_data/news.yml`:

```yaml
- year: 2024
  en: 'Plain text or <strong>HTML</strong> with <a href="url">links</a>.'
  zh: '对应的中文。'
```

### Awards

Edit `_data/awards.yml`. Has four sections: `awards`, `challenges`, `services`, `talks`. See file for format.

### Blog Posts

Create a new file in `_posts/` named `YYYY-MM-DD-slug.md`:

```markdown
---
layout: post
title: "Post Title"
date: 2026-03-26
description: "Short description for preview cards."
tags: [AI, Research]
---

Post content in Markdown.
```

### UI Text (i18n)

All UI labels (nav items, section titles, button text) are in `_data/i18n.yml`. Each key has `en` and `zh` values.

### Site Metadata

`_config.yml` controls:
- `title`, `description`, `url` — SEO and meta tags
- `author.name`, `author.email`, `author.title` — used by jekyll-seo-tag
- `social.*` — GitHub, Scholar, LinkedIn, Twitter, Zhihu handles

## Adding a New Page

1. Create `pagename.html` (English) and `zh/pagename.html` (Chinese)
2. Add front matter with `layout`, `title`, `permalink`, and `lang` (for Chinese)
3. Add nav link in `_includes/nav.html` and i18n key in `_data/i18n.yml`
4. Add the path to the hreflang list in `_includes/head.html`
5. Add the path to `zhPages` array in `assets/js/main.js` (for auto language redirect)

## Design System

### Theming

Colors are defined as SCSS variables in `_sass/_variables.scss` and mapped to CSS custom properties in `_sass/_base.scss`. Dark mode overrides in `_sass/_dark.scss`.

### Key Design Tokens

| Token | Light | Dark |
|-------|-------|------|
| `--bg-primary` | `#ffffff` | `#0f172a` |
| `--text-primary` | `#0f172a` | `#f1f5f9` |
| `--accent` | `#2563eb` | `#60a5fa` |
| `--border` | `#e2e8f0` | `#334155` |

### Breakpoints

- Mobile: `≤ 640px`
- Tablet: `641px – 960px`
- Desktop: `> 960px`

### Fonts

- Sans: Inter (Google Fonts, with `fonts.loli.net` fallback for China)
- Mono: JetBrains Mono

## Deployment

Push to `main` → GitHub Actions builds with Jekyll → deploys to GitHub Pages.

The workflow is defined in `.github/workflows/deploy.yml`. No manual steps needed.

## Notes

- **No CV/resume file** in the repo — intentionally excluded for privacy
- **Images**: Publication preview images go in `assets/img/publication_preview/`; timeline logos go in `assets/img/logos/`; bio photo is `assets/img/bio_pic.jpg`
- **Career timeline is the source of truth**: Experience content lives in `_data/about.yml` (`timeline` section), not in a separate projects page
- **Language auto-redirect**: First-time visitors with Chinese browser locale are redirected to `/zh/` for whitelisted pages (configured in `main.js`)
- **Sass compilation**: `sass.style: compressed` in `_config.yml` for production minification
