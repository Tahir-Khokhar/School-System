// app.js — shared JavaScript for all pages.
// Loaded by base.html via {% static 'js/app.js' %}
// All inline <script> blocks have been moved here for strict CSP compliance.

document.addEventListener('DOMContentLoaded', function() {

    // ---- Generic data-confirm handler (also used for document deletes) ----
    // Any form with data-confirm="message" will show a confirm dialog before submitting.
    // Works for: academic year activation, document deletes, phone deletes, etc.
    // NOTE: documents.js was deleted to avoid double-confirm. All confirmations
    // go through this single handler.
    document.querySelectorAll('form[data-confirm]').forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var msg = form.getAttribute('data-confirm') || 'Are you sure?';
            if (!window.confirm(msg)) {
                e.preventDefault();
            }
        });
    });

    // ---- Toast auto-hide ----
    // Toasts with data-auto-hide="5000" will auto-dismiss after 5 seconds.
    document.querySelectorAll('.toast[data-auto-hide]').forEach(function(t) {
        var delay = parseInt(t.getAttribute('data-auto-hide')) || 5000;
        setTimeout(function() {
            var toast = new bootstrap.Toast(t);
            toast.hide();
        }, delay);
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
    var sidebarCloseBtn = document.getElementById('sidebarCloseBtn');
    if (sidebarCloseBtn && mainWrapper) {
        sidebarCloseBtn.addEventListener('click', function() {
            mainWrapper.classList.remove('sidebar-open');
        });
    }

    // ---- Active sidebar link highlighting ----
    // Highlights the nav link whose href matches the current page URL.
    var currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar-nav .nav-link, .portal-sidebar a').forEach(function(link) {
        var href = link.getAttribute('href');
        if (href && href !== '#' && currentPath.indexOf(href) === 0 && href !== '/') {
            link.classList.add('active');
        } else if (href === currentPath) {
            link.classList.add('active');
        }
    });

    // ---- Global search (Ctrl+K) ----
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            var search = document.getElementById('globalSearchInput');
            if (search) search.focus();
        }
    });

    // ---- Theme toggle (writes BOTH cookie and localStorage) ----
    var themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            var html = document.documentElement;
            var current = html.getAttribute('data-bs-theme');
            var newTheme = current === 'dark' ? 'light' : 'dark';
            html.setAttribute('data-bs-theme', newTheme);
            // Write localStorage for JS reads.
            localStorage.setItem('theme', newTheme);
            // Write cookie so server-side template (base.html) reads it
            // on the NEXT page load — prevents the "light flash" on dark-mode users.
            document.cookie = 'theme=' + newTheme + ';path=/;max-age=31536000';
        });
        // Restore saved theme from cookie (preferred) or localStorage.
        var cookieMatch = document.cookie.match(/theme=(dark|light)/);
        var saved = cookieMatch ? cookieMatch[1] : localStorage.getItem('theme');
        if (saved) {
            document.documentElement.setAttribute('data-bs-theme', saved);
        }
    }

    // ---- Mark All Present button (attendance page) ----
    var markAllBtn = document.getElementById('markAllPresentBtn');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', function() {
            document.querySelectorAll('select[name^="form-"][name$="-status"]').forEach(function(s) {
                s.value = 'present';
            });
        });
    }

    // ---- Landing page nav toggle ----
    var navToggle = document.getElementById('mainNavToggle');
    var mainNav = document.getElementById('mainNav');
    if (navToggle && mainNav) {
        navToggle.addEventListener('click', function() {
            mainNav.classList.toggle('open');
        });
    }
});
