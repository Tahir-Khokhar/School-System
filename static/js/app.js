// School ERP - app.js
(function(){
    'use strict';

    // Theme toggle (light/dark/system)
    function applyTheme(theme){
        const html = document.documentElement;
        html.setAttribute('data-bs-theme', theme);
        document.cookie = 'theme=' + theme + ';path=/;max-age=31536000';
        const icon = document.querySelector('#themeToggle i');
        if (icon){
            icon.className = theme === 'dark' ? 'bi bi-moon-stars-fill' :
                             theme === 'light' ? 'bi bi-sun-fill' : 'bi bi-circle-half';
        }
    }
    const themeBtn = document.getElementById('themeToggle');
    if (themeBtn){
        themeBtn.addEventListener('click', function(){
            const current = document.documentElement.getAttribute('data-bs-theme') || 'light';
            applyTheme(current === 'dark' ? 'light' : 'dark');
        });
    }
    // Initial theme detection
    const saved = (document.cookie.match(/theme=([^;]+)/) || [])[1];
    if (saved) applyTheme(saved);

    // Mobile sidebar toggle
    const sb = document.getElementById('sidebarToggle');
    if (sb){
        sb.addEventListener('click', function(){
            document.getElementById('main-wrapper').classList.toggle('sidebar-open');
        });
    }

    // Active sidebar link
    const path = window.location.pathname;
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(function(a){
        const href = a.getAttribute('href');
        if (href && href !== '#' && path.indexOf(href) === 0 && href !== '/'){
            a.classList.add('active');
        }
    });

    // Global search shortcut: Ctrl+K
    document.addEventListener('keydown', function(e){
        if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || e.key === 'K')){
            e.preventDefault();
            const input = document.getElementById('globalSearchInput');
            if (input) input.focus();
        }
    });

    // Auto-dismiss toasts handled in template; add dismiss-on-click
    document.addEventListener('click', function(e){
        const t = e.target.closest('.toast');
        if (t){
            const bs = bootstrap.Toast.getInstance(t);
            if (bs) bs.hide();
        }
    });

    // Confirm delete / destructive actions
    document.querySelectorAll('[data-confirm]').forEach(function(btn){
        btn.addEventListener('click', function(e){
            if (!confirm(btn.dataset.confirm)) e.preventDefault();
        });
    });
})();
