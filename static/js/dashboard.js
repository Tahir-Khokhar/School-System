// dashboard.js — chart rendering for dashboard/home.html
// Extracted from inline <script> for strict CSP compliance.
// Reads chart data from <script type="application/json" id="…"> elements
// (rendered by Django's json_script template tag) instead of inline data
// attributes — prevents XSS from class names containing apostrophes.

document.addEventListener('DOMContentLoaded', function() {
    // Fee collection chart
    var feeCtx = document.getElementById('feeChart');
    if (feeCtx && window.Chart && feeCtx.dataset.enabled === 'true') {
        var labelsEl = document.getElementById('fee-chart-labels');
        var valuesEl = document.getElementById('fee-chart-values');
        var labels = labelsEl ? JSON.parse(labelsEl.textContent) : [];
        var values = valuesEl ? JSON.parse(valuesEl.textContent) : [];
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
        var enrollmentEl = document.getElementById('enrollment-data');
        var enrollment = enrollmentEl ? JSON.parse(enrollmentEl.textContent) : [];
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
                indexAxis: 'y',
                plugins: { legend: { display: false } },
                scales: { x: { beginAtZero: true } }
            }
        });
    }
});
