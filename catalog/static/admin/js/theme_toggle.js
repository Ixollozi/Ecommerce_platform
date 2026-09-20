/**
 * Admin theme toggle — light / dark (no OS auto).
 */
(function () {
  'use strict';

  function getTheme() {
    var saved = localStorage.getItem('admin-theme');
    if (saved === 'dark' || saved === 'light') return saved;
    return 'light';
  }

  function applyTheme(theme) {
    var next = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    document.documentElement.classList.add('fs-admin');
    localStorage.setItem('admin-theme', next);
    localStorage.setItem('theme', next);
  }

  function toggleTheme() {
    applyTheme(getTheme() === 'dark' ? 'light' : 'dark');
  }

  applyTheme(getTheme());

  document.addEventListener('DOMContentLoaded', function () {
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.addEventListener('click', toggleTheme);
  });
})();
