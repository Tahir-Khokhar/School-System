// landing.js — landing page specific JavaScript.
// Extracted from inline <script> in landing.html for strict CSP.

document.addEventListener('DOMContentLoaded', function() {
    // Mobile nav toggle — close on link click
    document.querySelectorAll('.lps-navbar .nav-links a').forEach(function(link) {
        link.addEventListener('click', function() {
            var mainNav = document.getElementById('mainNav');
            if (mainNav) mainNav.classList.remove('open');
        });
    });

    // Active nav highlight on scroll
    var sections = document.querySelectorAll('section[id]');
    var navLinks = document.querySelectorAll('.lps-navbar .nav-links a');
    window.addEventListener('scroll', function() {
        var current = '';
        sections.forEach(function(sec) {
            if (window.scrollY >= (sec.offsetTop - 100)) current = sec.id;
        });
        navLinks.forEach(function(link) {
            link.classList.remove('active');
            if (link.getAttribute('href') === '#' + current) link.classList.add('active');
        });
    });
});
