// dashboard.js — chart rendering for dashboard/home.html
// Extracted from inline <script> for strict CSP compliance.

document.addEventListener('DOMContentLoaded', function() {
    // Fee collection chart
    var feeCtx = document.getElementById('feeChart');
    if (feeCtx && window.Chart && feeCtx.dataset.enabled === 'true') {
        var labels = JSON.parse(feeCtx.dataset.labels || '[]');
        var values = JSON.parse(feeCtx.dataset.values || '[]');
        new Chart(feeCtx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Collection',
                    data: values,
                    borderColor: '#4f46e5',
                    backgroundColor: 'rgba(79,70,229,.08)',
                    fill: true,
                    tension: .35,
                    pointRadius: 4
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }

    // Enrollment by class chart
    var enrollCtx = document.getElementById('enrollChart');
    if (enrollCtx && window.Chart) {
        var enrollment = JSON.parse(enrollCtx.dataset.enrollment || '[]');
        new Chart(enrollCtx, {
            type: 'bar',
            data: {
                labels: enrollment.map(function(e) { return e.name; }),
                datasets: [{
                    label: 'Students',
                    data: enrollment.map(function(e) { return e.count; }),
                    backgroundColor: '#4f46e5',
                }]
            },
            options: {
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    }
});
