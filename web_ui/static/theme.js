// Спільна логіка перемикання теми (використовується і на головній сторінці, і на сторінці Coins)
(function () {
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sizes_theme', theme);
  }

  const saved = localStorage.getItem('sizes_theme');
  applyTheme(saved === 'light' ? 'light' : 'dark');

  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }
})();