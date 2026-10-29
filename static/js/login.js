// login.js — password show/hide toggle for the login page.
// Extracted from inline <script> for strict CSP compliance.

document.addEventListener('DOMContentLoaded', function() {
    var toggle = document.getElementById('passwordToggle');
    var passwordField = document.getElementById('id_password');
    if (!toggle || !passwordField) {
        // Try two_factor field names
        passwordField = document.querySelector('input[name="auth-password"]');
        toggle = document.getElementById('passwordToggle');
    }
    if (toggle && passwordField) {
        toggle.addEventListener('click', function() {
            var type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
            passwordField.setAttribute('type', type);
            var icon = toggle.querySelector('i');
            if (icon) {
                icon.classList.toggle('bi-eye');
                icon.classList.toggle('bi-eye-slash');
            }
        });
    }
});
