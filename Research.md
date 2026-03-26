# 个人网站深度研究报告

## 一、项目概览

| 维度 | 说明 |
|------|------|
| **模板来源** | [al-folio](https://github.com/alshedivat/al-folio) — 面向学术研究者的 Jekyll 主题 |
| **技术栈** | Jekyll + Liquid + SCSS + Bootstrap 4 + jQuery + MDBootstrap |
| **部署方式** | GitHub Actions → GitHub Pages |
| **Ruby 版本** | 3.2.2 |
| **内容类型** | 学术个人主页（论文、项目、奖项、新闻） |
| **多语言** | 英文（默认） + 中文（`/cn/` 目录，不完整） |
| **博客状态** | 框架已配置，`_posts/` 为空，未启用 |

---

## 二、架构分析

### 2.1 当前目录结构

```
yu-changqian.github.io/
├── _bibliography/          # BibTeX 论文数据 (papers.bib, 16 篇论文)
├── _data/                  # YAML 数据 (cv, coauthors, repositories, venues)
├── _includes/              # Liquid 模板片段 (24 个文件)
│   ├── cv/                 # 简历组件
│   ├── repository/         # GitHub 仓库卡片
│   ├── resume/             # 简历模板
│   └── scripts/            # JS 脚本引入 (18 个文件)
├── _layouts/               # 布局模板 (14 个)
├── _news/                  # 新闻集合 (6 条)
├── _pages/                 # 页面内容 (14 个 Markdown)
├── _plugins/               # 自定义插件
├── _posts/                 # 博客文章 ⚠️ 空
├── _projects/              # 项目集合 (9 个) ⚠️ 全为模板示例
├── _sass/                  # SCSS 样式模块
│   ├── font-awesome/       # Font Awesome 完整库
│   └── tabler-icons/       # Tabler Icons 完整库
├── assets/
│   ├── css/                # 编译后 CSS (13 个文件 + source maps)
│   ├── fonts/              # 自托管字体
│   ├── img/                # 图片 (20MB!) — 含 14MB 的 prof_pic_color.png
│   ├── js/                 # JavaScript (50+ 文件)
│   ├── json/               # 简历 JSON
│   ├── jupyter/            # Jupyter 示例
│   ├── pdf/                # CV 等 PDF
│   └── webfonts/           # Web 字体
├── cn/                     # 中文页面 (5 个，不完整)
├── bin/                    # 构建脚本
├── lighthouse_results/     # Lighthouse 报告
└── .github/workflows/      # CI/CD
```

### 2.2 页面与导航

| 页面 | 路径 | 导航 | 状态 |
|------|------|------|------|
| About (首页) | `/` | ✅ | 已定制 |
| Publications | `/publications/` | ✅ | 已定制，16 篇论文 |
| Projects | `/projects/` | ✅ | ⚠️ 全为模板示例 |
| Repositories | `/repositories/` | ✅ | 已定制，5 个仓库 |
| Awards | `/awards/` | ✅ | 已定制 |
| Blog | `/blog/` | ❌ | ⚠️ 未启用 |
| CV | `/cv/` | ❌ | 已配置 |
| News | `/news/` | ❌ | 仅首页显示 |

---

## 三、核心问题诊断

### 3.1 架构过重 — 根本性问题

al-folio 的设计理念与需求不匹配。它是为"需要自动化论文管理的学术研究者"设计的重型主题，而网站的实际需求是"简洁的个人品牌展示 + 博客输出"。

**量化对比：**

| 维度 | al-folio 现状 | 实际需要 |
|------|-------------|---------|
| Layout 文件 | 14 个 | 3-4 个 |
| Include 文件 | 24 个 | 5-8 个 |
| Jekyll 插件 | 20 个 | 4-5 个 |
| JS 脚本模块 | 18 个 (50+ 文件) | < 5 个 |
| CDN 外部库 | 23+ 个 | 2-3 个 |
| CSS 框架 | Bootstrap + MDB + FA + Tabler (~500KB) | 自写 SCSS (~20KB) |
| `_config.yml` | 640 行 | < 50 行 |
| 构建依赖 | Ruby + Python + ImageMagick | 仅 Ruby |

**核心矛盾：** 高度耦合的模板系统导致"删一处要改三处"，做减法比从零搭建更痛苦。

### 3.2 内容问题

1. **Projects 全为示例** — 9 个项目文件全部是 al-folio 默认内容
2. **图片资源浪费** — `prof_pic_color.png` 14MB、`prof_pic.jpg` 2.3MB、示例图 `1.jpg`~`12.jpg`
3. **中文版不完整** — `cn/index.html` 已删除，双语维护成本高
4. **博客未启用** — 完整框架闲置

### 3.3 设计与美观

- 传统学术排版，缺乏现代感和留白
- 色彩单调（亮色 `#00369f`，暗色 `#2698ba`）
- 首页布局拥挤（photo + text 并排 + news 表格 + 论文列表）
- 卡片组件缺乏层次
- 暗色模式下部分组件配色未独立适配

### 3.4 技术债务

- jQuery 依赖（2026 年应使用原生 JS）
- Bootstrap 4 已停止维护
- 冗余浏览器前缀 (`-moz-`, `-ms-`, `-o-`)
- IP 地理定位自动语言跳转（体验差、隐私问题）
- Source Maps 泄露到生产环境

---

## 四、决策结论

### 方案选择：抛弃 al-folio，从零搭建极简架构

**决策依据：**

1. Jekyll Scholar（BibTeX 自动论文管理）对用户属于"有最好但非必需"，论文列表变化不大
2. 博客需求（每月 1-2 篇）需要清晰简洁的写作体验
3. 用户偏好"逻辑清晰好维护"的中等复杂度
4. 目标风格是"现代专业风"，al-folio 的 HTML/CSS 结构不适合此风格

**保留决策：**

- ✅ 保留 Jekyll 框架（GitHub Pages 原生支持）
- ✅ 保留 SCSS 预处理器
- ✅ 保留 GitHub Actions 部署
- ❌ 抛弃 al-folio 模板体系（layouts, includes, plugins）
- ❌ 抛弃 Bootstrap / MDBootstrap / jQuery
- ❌ 抛弃 Jekyll Scholar（BibTeX → YAML 手动管理）
- ❌ 抛弃多语言（简化为单语言英文）

---

## 五、需迁移的核心内容

### 5.1 个人信息（from `_pages/about.md` & `_config.yml`）

- 姓名：Changqian Yu
- 头衔：Senior Research Scientist @ Kunlun Tech
- 研究方向：Semantic/Panoptic Segmentation, Trajectory Prediction, VLM
- 教育：HUST PhD 2021, Adelaide 访问学者
- 经历：昆仑万维、美团、MSRA、旷视
- 荣誉：CSIG 优秀博士学位论文奖（全国优博）

### 5.2 论文列表（from `_bibliography/papers.bib`，16 篇）

需从 BibTeX 转为 YAML 数据文件 `_data/publications.yml`，保留：
- title, authors, venue, year, abbr
- 链接：html, arxiv, code
- 标记：selected, award, preview image

### 5.3 奖项与服务（from `_pages/awards.md`）

- 14 项奖项
- 11 项竞赛成绩
- 学术服务
- 5 次学术演讲

### 5.4 新闻（from `_news/`，6 条）

### 5.5 GitHub 仓库（from `_data/repositories.yml`）

- TorchSeg, Lite-HRNet, ContextPrior, CondNet, FluxMusic

### 5.6 静态资源

- `assets/img/bio_pic.jpg` — 压缩后保留
- `assets/pdf/cv.pdf` — 保留
- 论文预览图 — 保留有用的
- 社交链接：CV, LinkedIn, Google Scholar, GitHub, X, 知乎

---

## 六、总结

网站基于 al-folio 构建，核心内容优秀但架构过重、设计陈旧、博客缺失。经评估决定抛弃 al-folio 模板体系，在 Jekyll 上从零搭建极简架构，实现现代专业风格设计，同时新增博客功能。

详细实施方案见 **[Plan.md](./Plan.md)**。
