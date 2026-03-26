---
layout: default
title: Publications
description: "Full list of academic publications by Changqian Yu — CVPR, ECCV, ICCV, NeurIPS, IJCV and more."
permalink: /publications/
---
{% assign lang = page.lang | default: "en" %}
{% assign t = site.data.i18n[lang].publications %}
<div class="container">
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
