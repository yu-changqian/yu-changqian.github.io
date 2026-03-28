---
layout: default
title: Publications
description: "Full list of academic publications by Changqian Yu — CVPR, ECCV, ICCV, NeurIPS, IJCV and more."
permalink: /publications/
---
{% assign lang = page.lang | default: "en" %}
{% assign t = site.data.i18n[lang].publications %}
{% assign stats = site.data.scholar_stats %}
<div class="container">
  <div class="page-header">
    <h1>{{ t.title }}</h1>
    <p>{{ t.see }} <a href="https://scholar.google.com/citations?user={{ site.social.scholar }}&hl=en">Google Scholar</a> {{ t.subtitle }}</p>
  </div>

  {% if stats %}
  <div class="scholar-stats">
    <span class="scholar-badge"><span class="scholar-badge__label">{{ t.total_citations }}</span><span class="scholar-badge__value">&gt; {{ stats.total_citations | plus: 0 }}</span></span>
    <span class="scholar-badge"><span class="scholar-badge__label">{{ t.total_papers }}</span><span class="scholar-badge__value">&gt; {{ stats.total_papers }}</span></span>
    <span class="scholar-badge"><span class="scholar-badge__label">{{ t.max_citations }}</span><span class="scholar-badge__value">&gt; {{ stats.max_citations | plus: 0 }}</span></span>
  </div>
  {% endif %}

  {% assign pubs = site.data.publications | concat: site.data.publications_all %}
  {% assign pubs_by_year = pubs | group_by: "year" | sort: "name" | reverse %}

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
