// gateway_redirect.js — auto-submit the JazzCash gateway form.
// Extracted from an inline <script> so strict CSP (no 'unsafe-inline')
// doesn't block the auto-submit.
document.addEventListener('DOMContentLoaded', function() {
    var form = document.getElementById('gatewayForm');
    if (form) {
        // Auto-submit after 2 seconds. If JS is disabled, the <noscript>
        // fallback shows a real submit button inside the form.
        setTimeout(function() {
            form.submit();
        }, 2000);
    }
});
