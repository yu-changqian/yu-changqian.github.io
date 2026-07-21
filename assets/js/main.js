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
  var hamburger = document.getElementById("nav-toggle");

  if (navToggle && navMenu) {
    navToggle.addEventListener("click", function () {
      var isOpen = navMenu.classList.toggle("open");
      if (hamburger) {
        hamburger.classList.toggle("open", isOpen);
        hamburger.setAttribute("aria-expanded", String(isOpen));
      }
    });

    document.addEventListener("click", function (e) {
      if (!navMenu.contains(e.target) && !navToggle.contains(e.target)) {
        navMenu.classList.remove("open");
        if (hamburger) {
          hamburger.classList.remove("open");
          hamburger.setAttribute("aria-expanded", "false");
        }
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
  var zhPages = ["/", "/publications/", "/blog/", "/awards/"];

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

  // --- Scroll Reveal Animations ---
  if ("IntersectionObserver" in window) {
    var reveals = document.querySelectorAll(
      ".section, .pub-card, .post-preview"
    );
    var revealObserver = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            revealObserver.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.08 }
    );
    reveals.forEach(function (el) {
      el.classList.add("reveal");
      revealObserver.observe(el);
    });
  }
})();
