(function () {
  "use strict";

  // --- Theme Toggle ---
  var themeToggle = document.getElementById("theme-toggle");
  var iconSun = document.getElementById("icon-sun");
  var iconMoon = document.getElementById("icon-moon");

  function getTheme() {
    var saved = localStorage.getItem("theme");
    if (saved) return saved;
    return window.matchMedia("(prefers-color-scheme: dark)").matches
      ? "dark"
      : "light";
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (iconSun && iconMoon) {
      iconSun.style.display = theme === "dark" ? "none" : "block";
      iconMoon.style.display = theme === "dark" ? "block" : "none";
    }
    if (themeToggle) {
      themeToggle.setAttribute(
        "aria-label",
        theme === "dark" ? "Switch to light mode" : "Switch to dark mode"
      );
    }
  }

  applyTheme(getTheme());

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme");
      var next = current === "dark" ? "light" : "dark";
      localStorage.setItem("theme", next);
      applyTheme(next);
    });
  }

  window
    .matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", function (e) {
      if (!localStorage.getItem("theme")) {
        applyTheme(e.matches ? "dark" : "light");
      }
    });

  // --- Mobile Nav ---
  var navToggle = document.getElementById("nav-toggle");
  var navMenu = document.getElementById("nav-menu");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      var isOpen = navMenu.classList.toggle("open");
      navToggle.classList.toggle("open", isOpen);
      navToggle.setAttribute("aria-expanded", String(isOpen));
    });

    document.addEventListener("click", function (e) {
      if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
        navMenu.classList.remove("open");
        navToggle.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  // --- Nav scroll effect ---
  var nav = document.getElementById("nav");
  if (nav) {
    window.addEventListener(
      "scroll",
      function () {
        var scrollTop =
          window.pageYOffset || document.documentElement.scrollTop;
        if (scrollTop > 10) {
          nav.classList.add("scrolled");
        } else {
          nav.classList.remove("scrolled");
        }
      },
      { passive: true }
    );
  }

  // --- Language auto-detection (browser-based) ---
  var zhPages = ["/", "/publications/", "/awards/"];

  function detectLanguage() {
    if (localStorage.getItem("lang_pref")) return;

    var path = window.location.pathname;
    var isEnglishPage = !path.startsWith("/zh");
    if (!isEnglishPage) return;

    var lang = (navigator.language || navigator.userLanguage || "").toLowerCase();
    if (lang.startsWith("zh") && zhPages.indexOf(path) !== -1) {
      localStorage.setItem("lang_pref", "zh");
      window.location.href = "/zh" + path;
    } else {
      localStorage.setItem("lang_pref", "en");
    }
  }

  var langBtn = document.getElementById("lang-toggle");
  if (langBtn) {
    langBtn.addEventListener("click", function () {
      var targetLang = window.location.pathname.startsWith("/zh") ? "en" : "zh";
      localStorage.setItem("lang_pref", targetLang);
    });
  }

  detectLanguage();

  // --- Back to Top ---
  var backToTop = document.getElementById("back-to-top");
  if (backToTop) {
    window.addEventListener(
      "scroll",
      function () {
        var scrollTop =
          window.pageYOffset || document.documentElement.scrollTop;
        if (scrollTop > 400) {
          backToTop.classList.add("visible");
        } else {
          backToTop.classList.remove("visible");
        }
      },
      { passive: true }
    );
    backToTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // --- Publication Search & Filter Chips ---
  var publicationSearch = document.getElementById("publication-search");
  var publicationEmpty = document.getElementById("publication-empty");
  var filterChips = Array.prototype.slice.call(
    document.querySelectorAll("[data-pub-filter]")
  );

  if (publicationSearch || filterChips.length > 0) {
    var publicationCards = Array.prototype.slice.call(
      document.querySelectorAll("[data-publication]")
    );
    var yearGroups = Array.prototype.slice.call(
      document.querySelectorAll(".year-group")
    );
    var activeFilter = "all";

    function updatePublications() {
      var query = publicationSearch
        ? publicationSearch.value.trim().toLowerCase()
        : "";
      var visibleCount = 0;

      publicationCards.forEach(function (card) {
        var matchesSearch =
          !query || (card.dataset.search || "").indexOf(query) !== -1;
        var matchesFilter = true;
        if (activeFilter === "selected") {
          matchesFilter = card.dataset.selected === "true";
        } else if (activeFilter !== "all") {
          var v = card.dataset.venue || "";
          matchesFilter = v === activeFilter || v.indexOf(activeFilter) === 0;
        }
        var show = matchesSearch && matchesFilter;
        card.hidden = !show;
        if (show) visibleCount += 1;
      });

      yearGroups.forEach(function (group) {
        group.hidden = !group.querySelector("[data-publication]:not([hidden])");
      });

      if (publicationEmpty) {
        publicationEmpty.hidden = visibleCount !== 0;
      }
    }

    if (publicationSearch) {
      publicationSearch.addEventListener("input", updatePublications);
    }

    filterChips.forEach(function (chip) {
      chip.addEventListener("click", function () {
        activeFilter = chip.dataset.pubFilter || "all";
        filterChips.forEach(function (c) {
          c.classList.toggle("is-active", c === chip);
        });
        updatePublications();
      });
    });
  }

  // --- Copy BibTeX ---
  document.addEventListener("click", function (e) {
    var btn = e.target.closest("[data-copy-bib]");
    if (!btn) return;
    var card = btn.closest(".pub-card");
    var tpl = card ? card.querySelector(".pub-card__bib") : null;
    if (!tpl) return;

    var raw = (tpl.textContent || tpl.innerHTML || "").trim();
    var decodeEl = document.createElement("textarea");
    decodeEl.innerHTML = raw;
    var bib = decodeEl.value;

    function markCopied() {
      var original = btn.dataset.label || "BibTeX";
      var copiedText = btn.dataset.copied || "Copied";
      btn.textContent = copiedText;
      btn.classList.add("is-copied");
      clearTimeout(btn._copyTimer);
      btn._copyTimer = setTimeout(function () {
        btn.textContent = original;
        btn.classList.remove("is-copied");
      }, 1600);
    }

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(bib).then(markCopied);
    } else {
      decodeEl.style.position = "fixed";
      decodeEl.style.opacity = "0";
      document.body.appendChild(decodeEl);
      decodeEl.select();
      try {
        document.execCommand("copy");
        markCopied();
      } finally {
        document.body.removeChild(decodeEl);
      }
    }
  });

  // --- Editorial Gallery Drawer & Darkroom Carousel ---
  document.addEventListener("click", function (e) {
    var toggle = e.target.closest("[data-gallery-toggle]");
    if (!toggle) return;
    var root = toggle.closest("[data-editorial-gallery]");
    var drawer = root ? root.querySelector("[data-gallery-drawer]") : null;
    if (!drawer) return;

    var willExpand = drawer.hidden;
    if (willExpand) {
      Array.prototype.forEach.call(
        drawer.querySelectorAll("img[data-lazy-src]"),
        function (img) {
          if (!img.getAttribute("src")) {
            img.setAttribute("src", img.getAttribute("data-lazy-src"));
          }
        }
      );
    }
    drawer.hidden = !willExpand;
    toggle.setAttribute("aria-expanded", String(willExpand));
    toggle.textContent = willExpand
      ? toggle.dataset.collapseLabel
      : toggle.dataset.expandLabel;
  });

  var lightbox = null;
  var gallerySources = [];
  var galleryIndex = 0;

  function pad2(n) {
    return n < 10 ? "0" + n : String(n);
  }

  function renderLightbox() {
    if (!lightbox || !gallerySources.length) return;
    var img = lightbox.querySelector(".showcase-lightbox__img");
    var counter = lightbox.querySelector(".showcase-lightbox__counter");
    img.src = gallerySources[galleryIndex];
    counter.textContent =
      pad2(galleryIndex + 1) + " / " + pad2(gallerySources.length);
  }

  function stepLightbox(delta) {
    if (!lightbox || lightbox.hidden || !gallerySources.length) return;
    galleryIndex =
      (galleryIndex + delta + gallerySources.length) % gallerySources.length;
    renderLightbox();
  }

  function closeLightbox() {
    if (lightbox) {
      lightbox.hidden = true;
    }
  }

  document.addEventListener("click", function (e) {
    var tile = e.target.closest("[data-gallery-open]");
    if (!tile) return;
    var root = tile.closest("[data-editorial-gallery]") || document;
    var allTiles = Array.prototype.slice.call(
      root.querySelectorAll("[data-gallery-open]")
    );
    gallerySources = allTiles.map(function (el) {
      return el.dataset.gallerySrc;
    });
    galleryIndex = parseInt(tile.dataset.galleryOpen, 10) || 0;

    if (!lightbox) {
      lightbox = document.createElement("div");
      lightbox.className = "showcase-lightbox";
      lightbox.setAttribute("role", "dialog");
      lightbox.setAttribute("aria-modal", "true");
      lightbox.innerHTML =
        '<button type="button" class="showcase-lightbox__close" aria-label="Close">&times;</button>' +
        '<button type="button" class="showcase-lightbox__nav showcase-lightbox__nav--prev" aria-label="Previous">&#8249;</button>' +
        '<img class="showcase-lightbox__img" alt="Kling Image 4.0 visual output">' +
        '<button type="button" class="showcase-lightbox__nav showcase-lightbox__nav--next" aria-label="Next">&#8250;</button>' +
        '<div class="showcase-lightbox__counter"></div>';
      lightbox.addEventListener("click", function (ev) {
        if (
          ev.target === lightbox ||
          ev.target.closest(".showcase-lightbox__close")
        ) {
          closeLightbox();
        } else if (ev.target.closest(".showcase-lightbox__nav--prev")) {
          stepLightbox(-1);
        } else if (ev.target.closest(".showcase-lightbox__nav--next")) {
          stepLightbox(1);
        }
      });
      document.body.appendChild(lightbox);
    }

    renderLightbox();
    lightbox.hidden = false;
  });

  document.addEventListener("keydown", function (e) {
    if (!lightbox || lightbox.hidden) return;
    if (e.key === "Escape") closeLightbox();
    else if (e.key === "ArrowLeft") stepLightbox(-1);
    else if (e.key === "ArrowRight") stepLightbox(1);
  });
})();
