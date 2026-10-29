// app.js — shared JavaScript for all pages.
// Loaded by base.html via {% static 'js/app.js' %}
// All inline <script> blocks have been moved here for strict CSP compliance.

document.addEventListener('DOMContentLoaded', function() {
    // ---- Toast auto-hide ----
    var toasts = document.querySelectorAll('.toast');
    toasts.forEach(function(t) {
        setTimeout(function() {
            t.classList.remove('show');
            setTimeout(function() { t.remove(); }, 300);
        }, 5000);
    });

    // ---- Sidebar toggle (mobile) ----
    var sidebarToggle = document.getElementById('sidebarToggle');
    var mainWrapper = document.getElementById('main-wrapper');
    if (sidebarToggle && mainWrapper) {
        sidebarToggle.addEventListener('click', function() {
            mainWrapper.classList.toggle('sidebar-open');
        });
    }

    // ---- Sidebar close button (mobile) ----
    var sidebarClose = document.querySelector('.sidebar .btn-close, .sidebar button.bi-x-lg');
    if (sidebarClose && mainWrapper) {
        // Find the close button by its onclick or class
        var closeBtn = document.querySelector('.sidebar button[onclick*="sidebar"]');
        if (closeBtn) {
            closeBtn.removeAttribute('onclick'); // Remove inline handler
            closeBtn.addEventListener('click', function() {
                mainWrapper.classList.remove('sidebar-open');
            });
        }
    }

    // ---- Global search (Ctrl+K) ----
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            var search = document.getElementById('globalSearchInput');
            if (search) search.focus();
        }
    });

    // ---- Theme toggle ----
    var themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            var html = document.documentElement;
            var current = html.getAttribute('data-bs-theme');
            html.setAttribute('data-bs-theme', current === 'dark' ? 'light' : 'dark');
            localStorage.setItem('theme', html.getAttribute('data-bs-theme'));
        });
        // Restore saved theme
        var saved = localStorage.getItem('theme');
        if (saved) document.documentElement.setAttribute('data-bs-theme', saved);
    }
});
