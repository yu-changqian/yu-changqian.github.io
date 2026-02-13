// Language handling logic

(function () {
  const cnPath = '/cn/';
  const enPath = '/';

  // Function to get current language based on URL
  function getCurrentLang() {
    return window.location.pathname.startsWith(cnPath) ? 'cn' : 'en';
  }

  // Function to switch language
  // Function to switch language
  window.toggleLanguage = function () {
    const currentPath = window.location.pathname;
    let newPath;
    let newLang;

    if (currentPath.startsWith('/cn/')) {
      // Switch to EN
      newPath = currentPath.replace('/cn/', '/');
      newLang = 'en';
    } else {
      // Switch to CN
      newPath = '/cn' + currentPath;
      newLang = 'cn';
    }

    // Save preference
    localStorage.setItem('lang_pref', newLang);

    // Redirect
    window.location.href = newPath;
  };

  // Auto-detect and redirect logic
  function checkAndRedirect() {
    const pref = localStorage.getItem('lang_pref');
    const currentLang = getCurrentLang();

    // If user has a preference, respect it (unless they are already on the right page)
    if (pref) {
      if (pref === 'cn' && currentLang !== 'cn') {
        // Only redirect if explicitly preferred CN but on EN page
        // However, we shouldn't force redirect if they manually navigated? 
        // Let's keep it simple: if pref implies a different root, we might want to redirect, 
        // but that can be annoying. 
        // Better strategy: Only auto-redirect on landing if NO preference is set.
        return;
      }
      return;
    }

    // No preference, check IP
    // Only run this check on the root english page to avoid loops or unnecessary checks
    if (window.location.pathname === enPath || window.location.pathname === '/' || window.location.pathname === '/index.html') {
      fetch('https://ipapi.co/json/')
        .then(response => response.json())
        .then(data => {
          if (data.country_code === 'CN') {
            // Redirect to Chinese version
            window.location.href = cnPath;
          }
        })
        .catch(error => console.log('IP check failed', error));
    }
  }

  // Run check on load
  document.addEventListener('DOMContentLoaded', checkAndRedirect);
})();
