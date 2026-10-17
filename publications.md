---
layout: default
title: Publications
description: "Full list of academic publications by Changqian Yu — CVPR, ECCV, ICCV, NeurIPS, IJCV and more."
permalink: /publications/
---
{% assign lang = page.lang | default: "en" %}
{% assign t = site.data.i18n[lang].publications %}
{% assign stats = site.data.scholar_stats %}
<div class="container publications-page">
  <header class="page-header page-header--editorial">
    <span class="page-header__eyebrow">{{ t.eyebrow }}</span>
    <h1>{{ t.title }}</h1>
    <p>{{ t.subtitle }}</p>
    <a href="https://scholar.google.com/citations?user={{ site.social.scholar }}&hl=en" class="page-header__link" target="_blank" rel="noopener">{{ t.scholar_profile }}</a>
  </header>

  {% if stats %}
  <div class="scholar-stats" aria-label="Google Scholar statistics">
    <div class="scholar-stat"><span class="scholar-stat__value">{{ stats.total_citations | plus: 0 }}+</span><span class="scholar-stat__label">{{ t.total_citations }}</span></div>
    <div class="scholar-stat"><span class="scholar-stat__value">{{ stats.total_papers }}</span><span class="scholar-stat__label">{{ t.total_papers }}</span></div>
    <div class="scholar-stat"><span class="scholar-stat__value">{{ stats.max_citations | plus: 0 }}+</span><span class="scholar-stat__label">{{ t.max_citations }}</span></div>
  </div>
  {% endif %}

  <div class="publication-search">
    <label for="publication-search">{{ t.search_label }}</label>
    <div class="publication-search__field">
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"></circle><path d="m20 20-4-4"></path></svg>
      <input id="publication-search" type="search" placeholder="{{ t.search_placeholder }}" autocomplete="off">
    </div>
  </div>

  {% assign pubs = site.data.publications | concat: site.data.publications_all %}
  {% assign pubs_by_year = pubs | group_by: "year" | sort: "name" | reverse %}

  <div id="publication-list">
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
  <p class="publication-empty" id="publication-empty" hidden>{{ t.no_results }}</p>
</div>
