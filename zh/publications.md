---
layout: default
title: 学术论文
description: "余长千学术论文完整列表 — CVPR, ECCV, ICCV, NeurIPS, IJCV 等。"
lang: zh
permalink: /zh/publications/
---
<div class="container">
  {% assign t = site.data.i18n.zh.publications %}
  <div class="page-header">
    <h1>{{ t.title }}</h1>
    <p>{{ t.see }} <a href="https://scholar.google.com/citations?user={{ site.social.scholar }}&hl=en">Google Scholar</a> {{ t.subtitle }}</p>
  </div>

  {% assign pubs_by_year = site.data.publications | group_by: "year" | sort: "name" | reverse %}
  {% for year_group in pubs_by_year %}
  <div class="year-group">
    <div class="year-group__label">{{ year_group.name }}</div>
    <div class="year-group__list">
      {% for pub in year_group.items %}
        {% include publication.html pub=pub %}
      {% endfor %}
    </div>
  </div>
  {% endfor %}
</div>
