
/*
 * login.js — password visibility toggle and portal tab selection.
 *
 * Extracted from two_factor/core/login.html for strict CSP compliance.
 */

(function () {
    "use strict";

    function initializeLogin() {

        // --------------------------------------------------
        // PASSWORD SHOW / HIDE TOGGLE
        // --------------------------------------------------

        const toggle = document.getElementById("togglePw");
        const passwordInput = document.getElementById("id_auth-password");

        if (toggle && passwordInput) {

            toggle.addEventListener("click", function (event) {

                // Prevent accidental form submission.
                event.preventDefault();

                const showPassword = passwordInput.type === "password";

                passwordInput.type = showPassword ? "text" : "password";

                const icon = toggle.querySelector("i");

                if (icon) {
                    icon.classList.toggle("bi-eye", !showPassword);
                    icon.classList.toggle("bi-eye-slash", showPassword);
                }

                // Improve accessibility.
                toggle.setAttribute(
                    "aria-label",
                    showPassword ? "Hide password" : "Show password"
                );

                toggle.setAttribute(
                    "aria-pressed",
                    String(showPassword)
                );

            });

        }


        // --------------------------------------------------
        // PORTAL TAB ACTIVE STATE
        // --------------------------------------------------

        // Read URL query parameters.
        const params = new URLSearchParams(window.location.search);

        const next = params.get("next") || "";

        const tabs = document.querySelectorAll(".aps-portal-tab");

        if (tabs.length && next) {

            let nextPath = next;

            // Normalize the requested destination.
            try {
                nextPath = new URL(
                    next,
                    window.location.origin
                ).pathname;
            } catch (error) {
                console.warn(
                    "Unable to parse the requested portal URL.",
                    error
                );
            }

            const normalizedPath = nextPath.toLowerCase();

            // Find the matching portal tab.
            let activeTab = null;

            tabs.forEach(function (tab) {

                const portal = (
                    tab.getAttribute("data-portal") || ""
                ).trim().toLowerCase();

                if (
                    portal &&
                    normalizedPath.includes(portal)
                ) {
                    activeTab = tab;
                }

            });

            // Change active tab only when a match exists.
            // Otherwise, preserve the default HTML selection.
            if (activeTab) {

                tabs.forEach(function (tab) {
                    tab.classList.remove("active");
                });

                activeTab.classList.add("active");

            }

        }

    }


    // --------------------------------------------------
    // DOCUMENT INITIALIZATION
    // --------------------------------------------------

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializeLogin,
            { once: true }
        );

    } else {

        initializeLogin();

    }

})();
