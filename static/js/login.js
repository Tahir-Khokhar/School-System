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
    var params = new URLSearchParams(window.location.search);
    var next = params.get('next') || '';
    if (next.indexOf('/portal/student') !== -1) {
        var studentTab = document.querySelector('[data-portal="student"]');
        if (studentTab) studentTab.classList.add('active');
    } else if (next.indexOf('/portal/parent') !== -1) {
        var parentTab = document.querySelector('[data-portal="parent"]');
        if (parentTab) parentTab.classList.add('active');
    } else if (next.indexOf('/portal/teacher') !== -1) {
        var teacherTab = document.querySelector('[data-portal="teacher"]');
        if (teacherTab) teacherTab.classList.add('active');
    }
});
