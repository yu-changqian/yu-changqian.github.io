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

  // --- Showcase Lightbox ---
  var lightbox = null;
  function closeLightbox() {
    if (lightbox) {
      lightbox.hidden = true;
    }
  }

  document.addEventListener("click", function (e) {
    var shot = e.target.closest("[data-lightbox-src]");
    if (!shot) return;
    if (!lightbox) {
      lightbox = document.createElement("div");
      lightbox.className = "showcase-lightbox";
      lightbox.setAttribute("role", "dialog");
      lightbox.setAttribute("aria-modal", "true");
      lightbox.innerHTML =
        '<img alt=""><div class="showcase-lightbox__caption"></div>';
      lightbox.addEventListener("click", closeLightbox);
      document.body.appendChild(lightbox);
    }
    var img = lightbox.querySelector("img");
    var cap = lightbox.querySelector(".showcase-lightbox__caption");
    img.src = shot.dataset.lightboxSrc;
    img.alt = shot.dataset.lightboxCaption || "";
    cap.textContent = shot.dataset.lightboxCaption || "";
    cap.hidden = !cap.textContent;
    lightbox.hidden = false;
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") closeLightbox();
  });
})();
