
/*
 * Dashboard chart rendering.
 *
 * Reads chart data from Django json_script elements.
 * Compatible with strict Content Security Policy (CSP).
 */

(function () {
    "use strict";

    /**
     * Read and validate JSON array data from a script element.
     */
    function readJsonArray(elementId) {
        const element = document.getElementById(elementId);

        if (!element) {
            console.warn(`Dashboard chart data not found: ${elementId}`);
            return [];
        }

        try {
            const data = JSON.parse(element.textContent);

            if (!Array.isArray(data)) {
                console.error(
                    `Invalid chart data: ${elementId} must contain an array.`
                );
                return [];
            }

            return data;

        } catch (error) {
            console.error(
                `Unable to parse dashboard chart data: ${elementId}`,
                error
            );

            return [];
        }
    }

    /**
     * Prevent duplicate Chart.js instances on the same canvas.
     */
    function createChart(canvas, config) {
        const existingChart = Chart.getChart(canvas);

        if (existingChart) {
            existingChart.destroy();
        }

        return new Chart(canvas, config);
    }

    /**
     * Initialize dashboard charts.
     */
    function initializeDashboardCharts() {

        const feeCanvas = document.getElementById("feeChart");
        const enrollmentCanvas = document.getElementById("enrollChart");

        // Check whether Chart.js is available.
        if (!window.Chart) {
            console.error(
                "Chart.js is not loaded. Dashboard charts cannot render."
            );
            return;
        }

        // --------------------------------------------------
        // FEE COLLECTION CHART
        // --------------------------------------------------

        if (feeCanvas && feeCanvas.dataset.enabled === "true") {

            const labels = readJsonArray("fee-chart-labels");
            const values = readJsonArray("fee-chart-values");

            const validFeeData =
                labels.length === values.length &&
                labels.every(label => typeof label === "string") &&
                values.every(
                    value =>
                        typeof value === "number" &&
                        Number.isFinite(value)
                );

            if (!validFeeData) {
                console.error(
                    "Invalid fee collection chart data."
                );
            } else {

                createChart(feeCanvas, {
                    type: "line",

                    data: {
                        labels: labels,

                        datasets: [{
                            label: "Collection",
                            data: values,
                            borderColor: "#4f46e5",
                            backgroundColor: "rgba(79, 70, 229, 0.08)",
                            fill: true,
                            tension: 0.35,
                            pointRadius: 4,
                            pointHoverRadius: 6
                        }]
                    },

                    options: {
                        responsive: true,

                        plugins: {
                            legend: {
                                display: false
                            }
                        },

                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
            }
        }

        // --------------------------------------------------
        // STUDENT ENROLLMENT CHART
        // --------------------------------------------------

        if (enrollmentCanvas) {

            const enrollment = readJsonArray("enrollment-data");

            const validEnrollmentData = enrollment.every(
                item =>
                    item &&
                    typeof item.name === "string" &&
                    typeof item.count === "number" &&
                    Number.isFinite(item.count)
            );

            if (!validEnrollmentData) {
                console.error(
                    "Invalid student enrollment chart data."
                );
            } else {

                createChart(enrollmentCanvas, {
                    type: "bar",

                    data: {
                        labels: enrollment.map(item => item.name),

                        datasets: [{
                            label: "Students",

                            data: enrollment.map(item => item.count),

                            backgroundColor: "#4f46e5",

                            borderRadius: 5
                        }]
                    },

                    options: {
                        responsive: true,

                        indexAxis: "y",

                        plugins: {
                            legend: {
                                display: false
                            }
                        },

                        scales: {
                            x: {
                                beginAtZero: true,
                                ticks: {
                                    precision: 0
                                }
                            }
                        }
                    }
                });
            }
        }
    }

    // Support both normal page loading and dynamically loaded scripts.
    if (document.readyState === "loading") {
        document.addEventListener(
            "DOMContentLoaded",
            initializeDashboardCharts,
            { once: true }
        );
    } else {
        initializeDashboardCharts();
    }

})();
