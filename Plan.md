# 实施计划：个人网站重建

> 目标：抛弃 al-folio 模板体系，在 Jekyll 上从零搭建极简架构。  
> 风格：现代专业风 — 简洁、留白、卡片化、精致排版。  
> 功能：个人展示 + 论文列表 + 博客。

---

## Phase 0: 架构设计

### 新目录结构

```
yu-changqian.github.io/
├── _config.yml             # 极简配置 (~40 行)
├── _data/
│   └── publications.yml    # 论文数据 (从 BibTeX 转换)
├── _includes/
│   ├── head.html           # <head> 标签
│   ├── nav.html            # 导航栏
│   ├── footer.html         # 页脚
│   └── publication.html    # 单篇论文卡片组件
├── _layouts/
│   ├── default.html        # 全局框架
│   ├── page.html           # 通用页面
│   └── post.html           # 博客文章
├── _posts/                 # 博客文章
│   └── 2026-02-26-hello-world.md  # 示例文章
├── _sass/
│   ├── _variables.scss     # 设计变量（色彩、字体、间距）
│   ├── _base.scss          # 基础样式（reset、排版）
│   ├── _layout.scss        # 布局系统（nav、footer、容器）
│   ├── _components.scss    # 组件（卡片、标签、按钮）
│   ├── _home.scss          # 首页专属样式
│   ├── _blog.scss          # 博客样式
│   └── _dark.scss          # 暗色模式
├── assets/
│   ├── css/
│   │   └── main.scss       # SCSS 入口
│   ├── js/
│   │   └── main.js         # 极简 JS (暗色模式切换等)
│   ├── img/                # 仅保留必要图片（压缩后）
│   └── pdf/
│       └── cv.pdf
├── index.html              # 首页
├── publications.md         # 论文列表页
├── blog.html               # 博客列表页
├── awards.md               # 奖项页
├── Gemfile                 # 精简依赖
├── .github/
│   └── workflows/
│       └── deploy.yml      # 简化部署流程
├── CNAME                   # 自定义域名（如有）
└── .nojekyll               # GitHub Pages 配置
```

### 技术选型对比

| 维度 | al-folio (旧) | 新架构 |
|------|-------------|--------|
| **框架** | Jekyll + al-folio 主题 | Jekyll (无主题) |
| **CSS** | Bootstrap 4 + MDBootstrap + 2 图标库 | 自写 SCSS (零框架) |
| **JS** | jQuery + 18 脚本模块 + 23 CDN 库 | 原生 JS, < 200 行 |
| **字体** | Google Fonts CDN (Roboto) + 自托管 | Google Fonts CDN (Inter) |
| **图标** | Font Awesome + Tabler Icons (完整库) | 内联 SVG (仅需要的) |
| **论文管理** | Jekyll Scholar (BibTeX 自动化) | `_data/publications.yml` |
| **插件** | 20 个 | 4 个 (`feed`, `sitemap`, `seo-tag`, `paginate`) |
| **部署** | Ruby + Python + ImageMagick | 仅 Ruby |
| **总 CSS** | ~500KB (压缩前) | ~15-20KB |
| **总 JS** | ~200KB+ (不含 CDN) | < 5KB |

---

## Phase 1: 基础骨架搭建

### 1.1 清理项目

**删除 al-folio 相关文件：**

```
删除目录：
  _bibliography/          → 内容迁移到 _data/publications.yml
  _includes/              → 重写
  _layouts/               → 重写
  _plugins/               → 不再需要
  _projects/              → 全为模板示例，删除
  _sass/font-awesome/     → 改用内联 SVG
  _sass/tabler-icons/     → 改用内联 SVG
  _site/                  → 构建产物，git 已忽略
  assets/css/*.map         → source maps
  assets/js/ (大部分)     → 重写为 main.js
  assets/jupyter/          → 未使用
  bin/                     → 不需要
  cn/                      → 放弃多语言
  lighthouse_results/      → 不需要
  readme_preview/          → 不需要
  purgecss.config.js       → 不再需要

删除文件：
  Dockerfile, docker-compose*.yml
  package.json, package-lock.json
  .prettierrc
  CONTRIBUTING.md, CUSTOMIZE.md, FAQ.md, INSTALL.md
  各种不需要的 _pages/ 文件 (teaching, profiles, repositories, cv, 404 等)
```

**保留并迁移的内容：**

```
保留：
  assets/img/bio_pic.jpg    → 压缩到 < 200KB
  assets/img/publication/   → 论文预览图 (保留有用的)
  assets/pdf/cv.pdf         → 保留
  _news/                    → 内容提取到首页
  .github/workflows/        → 简化

迁移：
  _bibliography/papers.bib  → _data/publications.yml
  _pages/about.md           → index.html (内容)
  _pages/awards.md          → awards.md (内容)
```

### 1.2 新建 `_config.yml`

```yaml
title: Changqian Yu
description: >
  Senior Research Scientist at Kunlun Tech.
  Expert in Computer Vision and AI.
url: https://yu-changqian.github.io
baseurl: ""

author:
  name: Changqian Yu
  email: y-changqian@outlook.com
  title: Senior Research Scientist @ Kunlun Tech
  bio: >
    Leading the development of large multimodal models,
    with a focus on Diffusion and VLM technologies.

social:
  github: yu-changqian
  scholar: Hv-vj2sAAAAJ
  linkedin: yu-changqian
  twitter: ChangqianYu
  zhihu: yu-chang-qian

markdown: kramdown
highlighter: rouge
permalink: /blog/:year/:title/
sass:
  style: compressed

plugins:
  - jekyll-feed
  - jekyll-sitemap
  - jekyll-seo-tag
  - jekyll-paginate

paginate: 10
paginate_path: "/blog/page/:num/"

defaults:
  - scope:
      path: ""
      type: posts
    values:
      layout: post
```

### 1.3 新建 `Gemfile`

```ruby
source 'https://rubygems.org'

gem 'jekyll', '~> 4.3'
gem 'webrick'

group :jekyll_plugins do
  gem 'jekyll-feed'
  gem 'jekyll-sitemap'
  gem 'jekyll-seo-tag'
  gem 'jekyll-paginate'
end
```

### 1.4 数据迁移 — `_data/publications.yml`

从 `papers.bib` 转换为结构化 YAML，示例：

```yaml
- key: yu2018bisenet
  title: "BiSeNet: Bilateral Segmentation Network for Real-time Semantic Segmentation"
  authors: "Changqian Yu*, Jingbo Wang*, Chao Peng, Changxin Gao†, Gang Yu, Nong Sang"
  venue: ECCV
  year: 2018
  selected: true
  award: "ECCV 2018 Top-10 Influential Papers"
  citations: "2500+"
  links:
    paper: "https://openaccess.thecvf.com/content_ECCV_2018/html/..."
    arxiv: "1808.00897"
    code: "https://github.com/yu-changqian/TorchSeg/tree/master/model/bisenet"
  preview: bisenet_preview.png

- key: yu2021bisenet
  title: "BiSeNet V2: Bilateral Network with Guided Aggregation..."
  # ... (16 篇论文全部转换)
```

---

## Phase 2: 页面模板实现

### 2.1 `_layouts/default.html` — 全局框架

```
<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  {% include head.html %}
</head>
<body>
  {% include nav.html %}
  <main>{{ content }}</main>
  {% include footer.html %}
  <script src="/assets/js/main.js"></script>
</body>
</html>
```

**要点：**
- `data-theme` 属性驱动暗色模式
- 零外部 JS 依赖
- `jekyll-seo-tag` 自动处理 SEO meta

### 2.2 `_includes/nav.html` — 导航栏

**设计：**
- 左侧：名字 (Changqian Yu)
- 右侧：Publications / Blog / Awards
- 最右：暗色模式切换按钮
- 固定顶部，滚动时加 subtle backdrop-blur 效果
- 移动端：汉堡菜单

### 2.3 `index.html` — 首页

**布局设计（从上到下）：**

```
┌──────────────────────────────────────────────────┐
│  Nav: [Changqian Yu]     Pubs | Blog | Awards  🌙│
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌────────┐                                      │
│  │        │  Changqian Yu                        │
│  │  照片  │  Senior Research Scientist           │
│  │        │  @ Kunlun Tech                       │
│  └────────┘                                      │
│  简介文字...                                      │
│  [GitHub] [Scholar] [LinkedIn] [X] [知乎] [CV]   │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Selected Publications                           │
│  ┌──────────────────┐ ┌──────────────────┐       │
│  │ 🏆 BiSeNet       │ │ ⭐ BiSeNetV2     │       │
│  │ ECCV 2018        │ │ IJCV 2021        │       │
│  │ 2500+ citations  │ │ 1000+ citations  │       │
│  │ [Paper] [Code]   │ │ [Paper] [Code]   │       │
│  └──────────────────┘ └──────────────────┘       │
│  ┌──────────────────┐ ┌──────────────────┐       │
│  │ DFNet            │ │ Lite-HRNet       │       │
│  │ CVPR 2018        │ │ CVPR 2021        │       │
│  └──────────────────┘ └──────────────────┘       │
│                                     → View all   │
│                                                  │
├──────────────────────────────────────────────────┤
│                                                  │
│  Latest Posts                                    │
│  ┌──────────────────────────────────────────┐    │
│  │ 文章标题                        Feb 2026 │    │
│  │ 摘要描述文字...                          │    │
│  └──────────────────────────────────────────┘    │
│                                     → View all   │
│                                                  │
├──────────────────────────────────────────────────┤
│  News                                            │
│  • 2024 — Rank 1 in Argoverse...                │
│  • 2023 — Top 2% most-cited scientists...        │
│                                                  │
├──────────────────────────────────────────────────┤
│  Footer: © 2026 · social icons · theme toggle    │
└──────────────────────────────────────────────────┘
```

### 2.4 `publications.md` — 论文完整列表

**设计：**
- 按年份分组（2024 → 2018）
- 每篇论文以卡片展示：标题、作者（自己高亮）、会议标签、奖项标签
- 链接按钮：Paper / arXiv / Code
- 可选：预览缩略图

### 2.5 `blog.html` — 博客列表

**设计：**
- 文章卡片：标题、日期、摘要、阅读时间、标签
- 分页（每页 10 篇）
- 简洁优雅，参考 Medium 风格

### 2.6 `_layouts/post.html` — 博客文章

**设计：**
- 最大宽度 ~680px（舒适阅读）
- 文章头部：标题、日期、阅读时间、标签
- 优秀的代码高亮
- 文章底部：作者卡片、相关文章链接（可选）
- 社交分享按钮（可选）

### 2.7 `awards.md` — 奖项页

**设计：**
- 分节：Awards / Challenges / Services / Talks
- 时间轴风格或简洁列表
- 竞赛排名用标签高亮（Rank 1 金色、Rank 2 银色等）

---

## Phase 3: 设计系统

### 3.1 色彩系统 (`_sass/_variables.scss`)

```scss
// === Light Theme ===
$bg-primary:       #ffffff;
$bg-secondary:     #f8fafc;
$bg-tertiary:      #f1f5f9;
$text-primary:     #0f172a;
$text-secondary:   #475569;
$text-tertiary:    #94a3b8;
$accent:           #2563eb;       // 蓝色主调
$accent-hover:     #1d4ed8;
$border:           #e2e8f0;
$card-shadow:      0 1px 3px rgba(0, 0, 0, 0.06);
$card-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.1);

// === Dark Theme ===
$dark-bg-primary:     #0f172a;
$dark-bg-secondary:   #1e293b;
$dark-bg-tertiary:    #334155;
$dark-text-primary:   #f1f5f9;
$dark-text-secondary: #94a3b8;
$dark-text-tertiary:  #64748b;
$dark-accent:         #60a5fa;
$dark-border:         #334155;

// === Typography ===
$font-sans:  'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
$font-mono:  'JetBrains Mono', 'Fira Code', monospace;

$text-xs:    0.75rem;    // 12px
$text-sm:    0.875rem;   // 14px
$text-base:  1rem;       // 16px
$text-lg:    1.125rem;   // 18px
$text-xl:    1.25rem;    // 20px
$text-2xl:   1.5rem;     // 24px
$text-3xl:   1.875rem;   // 30px
$text-4xl:   2.25rem;    // 36px

// === Spacing ===
$content-width:   720px;
$wide-width:      960px;
$nav-height:      64px;

// === Transitions ===
$transition-fast:  150ms ease;
$transition-base:  250ms ease;
$transition-slow:  400ms ease;
```

### 3.2 排版系统

```scss
body {
  font-family: $font-sans;
  font-size: $text-base;
  line-height: 1.7;
  color: var(--text-primary);
  background: var(--bg-primary);
  -webkit-font-smoothing: antialiased;
}

h1 { font-size: $text-4xl; font-weight: 700; line-height: 1.2; letter-spacing: -0.02em; }
h2 { font-size: $text-2xl; font-weight: 600; line-height: 1.3; letter-spacing: -0.01em; }
h3 { font-size: $text-xl;  font-weight: 600; line-height: 1.4; }
```

### 3.3 组件设计

**论文卡片：**
- 白色/暗色背景 + 细边框 + 微阴影
- hover 时 shadow 加深 + 微上移 (translateY -2px)
- 左侧：会议/期刊彩色标签
- 中间：标题（加粗）+ 作者（灰色，自己名字蓝色高亮）
- 右侧/底部：Paper / arXiv / Code 链接按钮
- 奖项以小 badge 显示

**博客文章卡片：**
- 大标题 + 日期 + 摘要预览
- 标签以 pill 形状展示
- 底部：阅读时间

**社交链接按钮：**
- 内联 SVG 图标 (16x16 或 20x20)
- hover 变色 + scale 微放大
- 排列为水平行，间距均匀

### 3.4 暗色模式

```scss
:root {
  --bg-primary: #{$bg-primary};
  --bg-secondary: #{$bg-secondary};
  --text-primary: #{$text-primary};
  --text-secondary: #{$text-secondary};
  --accent: #{$accent};
  --border: #{$border};
  // ...
}

[data-theme="dark"] {
  --bg-primary: #{$dark-bg-primary};
  --bg-secondary: #{$dark-bg-secondary};
  --text-primary: #{$dark-text-primary};
  --text-secondary: #{$dark-text-secondary};
  --accent: #{$dark-accent};
  --border: #{$dark-border};
  // ...
}
```

**切换方式：** 原生 JS 切换 `data-theme` 属性 + `localStorage` 持久化 + 尊重 `prefers-color-scheme`。

---

## Phase 4: JavaScript (极简)

### `assets/js/main.js` — 全部功能

```javascript
// 1. 暗色模式切换
//    - 读取 localStorage / prefers-color-scheme
//    - 切换 html[data-theme]
//    - 保存偏好

// 2. 移动端导航
//    - 汉堡菜单 toggle
//    - 点击外部关闭

// 3. 导航栏滚动效果
//    - 向下滚动时添加 backdrop-blur 类

// 总代码量目标: < 100 行，零依赖
```

---

## Phase 5: 部署配置

### `.github/workflows/deploy.yml`

```yaml
name: Deploy
on:
  push:
    branches: [main, master]

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
          bundler-cache: true
      - run: bundle exec jekyll build
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

**对比旧流程：** 移除 Python/Jupyter 安装、PurgeCSS 步骤，构建时间大幅缩短。

---

## Phase 6: 博客功能

### 文章格式

```markdown
---
layout: post
title: "文章标题"
date: 2026-02-26
description: "一句话摘要"
tags: [AI, VLM, Diffusion]
---

正文内容...
```

### 功能清单

| 功能 | 实现方式 | 优先级 |
|------|---------|--------|
| 文章列表 | `blog.html` + `jekyll-paginate` | P0 |
| 标签 | 文章 front matter + 标签页面 | P0 |
| RSS | `jekyll-feed` 自动生成 | P0 |
| SEO | `jekyll-seo-tag` | P0 |
| 代码高亮 | Rouge (Jekyll 内置) | P0 |
| 阅读时间 | Liquid 计算 `content | number_of_words / 200` | P1 |
| 评论 | Giscus (后续配置) | P2 |
| 搜索 | 轻量前端搜索 (后续) | P3 |

---

## 实施顺序与检查清单

### Step 1: 基础骨架 ⬜
- [ ] 备份当前项目 (git branch)
- [ ] 清理所有 al-folio 文件
- [ ] 创建新 `_config.yml`
- [ ] 创建新 `Gemfile`
- [ ] 创建 `_data/publications.yml` (BibTeX → YAML)
- [ ] 创建 `_layouts/default.html`
- [ ] 创建 `_includes/head.html`
- [ ] 创建 `_includes/nav.html`
- [ ] 创建 `_includes/footer.html`
- [ ] 验证 `bundle exec jekyll serve` 能跑通

### Step 2: 设计系统 ⬜
- [ ] 创建 `_sass/_variables.scss` (色彩、字体、间距)
- [ ] 创建 `_sass/_base.scss` (reset、排版、全局样式)
- [ ] 创建 `_sass/_layout.scss` (nav、footer、容器)
- [ ] 创建 `_sass/_dark.scss` (暗色模式)
- [ ] 创建 `assets/css/main.scss` (SCSS 入口)
- [ ] Google Fonts 引入 Inter

### Step 3: 首页 ⬜
- [ ] 创建 `index.html`
- [ ] Hero / Profile section
- [ ] Selected Publications section (从 `_data/publications.yml` 读取)
- [ ] Latest Posts section (从 `_posts` 读取)
- [ ] News section
- [ ] 社交链接 (内联 SVG 图标)
- [ ] 创建 `_sass/_home.scss`

### Step 4: 论文页面 ⬜
- [ ] 创建 `publications.md`
- [ ] 创建 `_includes/publication.html` (论文卡片组件)
- [ ] 按年份分组展示
- [ ] 作者高亮、会议标签、奖项 badge
- [ ] 链接按钮 (Paper / arXiv / Code)
- [ ] 创建 `_sass/_components.scss`

### Step 5: 博客 ⬜
- [ ] 创建 `blog.html` (文章列表)
- [ ] 创建 `_layouts/post.html` (文章详情)
- [ ] 分页功能
- [ ] 标签展示
- [ ] 阅读时间
- [ ] 代码高亮样式
- [ ] 创建 `_sass/_blog.scss`
- [ ] 创建示例文章 `_posts/2026-02-26-hello-world.md`

### Step 6: 奖项页面 ⬜
- [ ] 创建 `awards.md`
- [ ] Awards / Challenges / Services / Talks 分节

### Step 7: JavaScript ⬜
- [ ] 创建 `assets/js/main.js`
- [ ] 暗色模式切换
- [ ] 移动端导航
- [ ] 导航栏滚动效果

### Step 8: 部署与优化 ⬜
- [ ] 更新 `.github/workflows/deploy.yml`
- [ ] 图片压缩 (bio_pic.jpg < 200KB)
- [ ] 清理 `assets/img/` 无用图片
- [ ] Lighthouse 性能检查
- [ ] 移动端兼容测试

---

## 风险与应对

| 风险 | 影响 | 应对 |
|------|------|------|
| 现有 URL 失效 (SEO) | 搜索引擎已索引旧 URL | 保持 `/publications/`, `/awards/` 等路径不变 |
| 论文数据迁移遗漏 | 缺少论文信息 | 逐条对比 BibTeX 和 YAML |
| GitHub Pages 构建失败 | 网站下线 | 先在分支开发，测试通过再合并 |
| 暗色模式闪烁 (FOUC) | 首屏白闪 | JS 在 `<head>` 中同步执行主题检测 |

---

## 预期成果

| 指标 | al-folio (现状) | 新架构 (预期) |
|------|---------------|-------------|
| CSS 体积 | ~500KB | ~15KB |
| JS 体积 | ~200KB+ | < 5KB |
| 外部请求 | 23+ CDN | 1 (Google Fonts) |
| 首屏加载 | ~3-4s | < 1s |
| Lighthouse Performance | 未知 | 95+ |
| 文件总数 | 200+ | ~30 |
| `_config.yml` 行数 | 640 | ~40 |
| Jekyll 插件 | 20 | 4 |
| 构建时间 | ~30s+ | < 5s |
| 新增功能 | — | 博客 ✅ |
