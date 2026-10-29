// documents.js — delete confirmation for documents list.
// Replaces inline onsubmit="return confirm(...)" for strict CSP compliance.

document.addEventListener('DOMContentLoaded', function() {
    // Find all delete forms in the documents list
    var deleteForms = document.querySelectorAll('form[data-delete-confirm]');
    deleteForms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            var msg = form.getAttribute('data-delete-confirm') || 'Are you sure?';
            if (!window.confirm(msg)) {
                e.preventDefault();
            }
        });
    });
});
