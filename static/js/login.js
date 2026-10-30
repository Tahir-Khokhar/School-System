// login.js — password show/hide toggle + portal tab active state.
// Extracted from inline <script> in two_factor/core/login.html for strict CSP.

document.addEventListener('DOMContentLoaded', function() {
    // Password show/hide toggle
    var toggle = document.getElementById('togglePw');
    var pw = document.getElementById('id_auth-password');
    if (toggle && pw) {
        toggle.addEventListener('click', function() {
            if (pw.type === 'password') {
                pw.type = 'text';
                var icon = toggle.querySelector('i');
                if (icon) { icon.classList.remove('bi-eye'); icon.classList.add('bi-eye-slash'); }
            } else {
                pw.type = 'password';
                var icon = toggle.querySelector('i');
                if (icon) { icon.classList.remove('bi-eye-slash'); icon.classList.add('bi-eye'); }
            }
        });
    }

    // Auto-set portal tab active based on ?next= param
    var next = params.get('next') || '';
    var tabs = document.querySelectorAll('.aps-portal-tab');
    if (tabs.length && next) {
        // Remove active from ALL tabs first (the default "student" tab
        // has active in the HTML; without removing it, two tabs light up).
        tabs.forEach(function(t) { t.classList.remove('active'); });
        tabs.forEach(function(t) {
            var portal = t.getAttribute('data-portal');
            if (portal && next.indexOf(portal) !== -1) {
                t.classList.add('active');
            }
        });
    }
});
