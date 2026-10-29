// payment_processing.js — auto-refresh the page to check if payment completed.
// Extracted from inline <script> for strict CSP compliance.

document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh every 5 seconds to check if the webhook has recorded
    // the payment and changed the challan status to PAID.
    var challanStatus = document.querySelector('[data-challan-status]');
    var isPaid = challanStatus && challanStatus.dataset.challanStatus === 'paid';
    if (!isPaid) {
        setTimeout(function() {
            window.location.reload();
        }, 5000);
    }
});
