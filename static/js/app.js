
/*
 * app.js — shared JavaScript for all pages.
 *
 * Loaded by base.html.
 * External JavaScript only — compatible with strict CSP.
 */

(function () {
    "use strict";

    /**
     * Initialize shared application functionality.
     */
    function initializeApp() {

        // --------------------------------------------------
        // FORM CONFIRMATION
        // --------------------------------------------------

        // Handle all forms using data-confirm.
        document.querySelectorAll("form[data-confirm]").forEach(function (form) {

            form.addEventListener("submit", function (event) {

                const message =
                    form.getAttribute("data-confirm") || "Are you sure?";

                if (!window.confirm(message)) {
                    event.preventDefault();
                }

            });

        });


        // --------------------------------------------------
        // TOAST AUTO-HIDE
        // --------------------------------------------------

        const toastElements = document.querySelectorAll(
            '.toast[data-auto-hide]'
        );

        toastElements.forEach(function (toastElement) {

            const rawDelay = Number.parseInt(
                toastElement.getAttribute("data-auto-hide"),
                10
            );

            const delay = Number.isFinite(rawDelay) && rawDelay > 0
                ? rawDelay
                : 5000;

            // Ensure Bootstrap Toast is available.
            if (
                !window.bootstrap ||
                !window.bootstrap.Toast
            ) {
                console.warn(
                    "Bootstrap Toast is unavailable. Toast auto-hide skipped."
                );
                return;
            }

            const toast = window.bootstrap.Toast.getOrCreateInstance(
                toastElement,
                { delay: delay }
            );

            window.setTimeout(function () {
                toast.hide();
            }, delay);

        });


        // --------------------------------------------------
        // MOBILE SIDEBAR
        // --------------------------------------------------

        const sidebarToggle = document.getElementById("sidebarToggle");
        const sidebarCloseBtn = document.getElementById("sidebarCloseBtn");
        const mainWrapper = document.getElementById("main-wrapper");

        function closeSidebar() {

            if (!mainWrapper) {
                return;
            }

            mainWrapper.classList.remove("sidebar-open");

            if (sidebarToggle) {
                sidebarToggle.setAttribute("aria-expanded", "false");
            }

        }

        if (sidebarToggle && mainWrapper) {

            sidebarToggle.addEventListener("click", function () {

                const isOpen = mainWrapper.classList.toggle("sidebar-open");

                sidebarToggle.setAttribute(
                    "aria-expanded",
                    String(isOpen)
                );

                sidebarToggle.setAttribute(
                    "aria-controls",
                    "main-wrapper"
                );

            });

        }

        if (sidebarCloseBtn) {

            sidebarCloseBtn.addEventListener("click", closeSidebar);

        }

        // Close the mobile sidebar using the Escape key.
        document.addEventListener("keydown", function (event) {

            if (event.key === "Escape" && mainWrapper) {
                closeSidebar();
            }

        });


        // --------------------------------------------------
        // ACTIVE SIDEBAR NAVIGATION
        // --------------------------------------------------

        const currentPath = window.location.pathname;

        const sidebarLinks = document.querySelectorAll(
            ".sidebar-nav .nav-link, .portal-sidebar a"
        );

        sidebarLinks.forEach(function (link) {

            const href = link.getAttribute("href");

            if (!href || href === "#" || href.startsWith("javascript:")) {
                return;
            }

            try {

                const linkUrl = new URL(href, window.location.origin);

                // Ignore external links.
                if (linkUrl.origin !== window.location.origin) {
                    return;
                }

                const linkPath = linkUrl.pathname;

                // Match exact paths or complete parent paths.
                const isExactMatch = currentPath === linkPath;

                const isParentMatch =
                    linkPath !== "/" &&
                    currentPath.startsWith(
                        linkPath.endsWith("/")
                            ? linkPath
                            : linkPath + "/"
                    );

                if (isExactMatch || isParentMatch) {
                    link.classList.add("active");
                }

            } catch (error) {

                console.warn(
                    "Unable to process sidebar link:",
                    href,
                    error
                );

            }

        });


        // --------------------------------------------------
        // GLOBAL SEARCH (CTRL + K)
        // --------------------------------------------------

        document.addEventListener("keydown", function (event) {

            if (
                (event.ctrlKey || event.metaKey) &&
                event.key.toLowerCase() === "k"
            ) {

                const searchInput = document.getElementById(
                    "globalSearchInput"
                );

                if (searchInput) {

                    event.preventDefault();
                    searchInput.focus();

                }

            }

        });


        // --------------------------------------------------
        // THEME MANAGEMENT
        // --------------------------------------------------

        const themeToggle = document.getElementById("themeToggle");
        const htmlElement = document.documentElement;

        /**
         * Read a cookie by its exact name.
         */
        function getCookie(name) {

            const cookies = document.cookie
                ? document.cookie.split(";")
                : [];

            for (const cookie of cookies) {

                const separatorIndex = cookie.indexOf("=");

                if (separatorIndex === -1) {
                    continue;
                }

                const cookieName = cookie
                    .slice(0, separatorIndex)
                    .trim();

                if (cookieName === name) {
                    return cookie.slice(separatorIndex + 1).trim();
                }

            }

            return null;
        }

        /**
         * Read saved theme safely.
         */
        function getSavedTheme() {

            const cookieTheme = getCookie("theme");

            if (
                cookieTheme === "light" ||
                cookieTheme === "dark"
            ) {
                return cookieTheme;
            }

            try {

                const storedTheme = window.localStorage.getItem("theme");

                if (
                    storedTheme === "light" ||
                    storedTheme === "dark"
                ) {
                    return storedTheme;
                }

            } catch (error) {

                console.warn(
                    "Local storage is unavailable for theme preferences."
                );

            }

            return null;
        }

        /**
         * Apply theme and save the preference.
         */
        function setTheme(theme) {

            if (theme !== "light" && theme !== "dark") {
                return;
            }

            htmlElement.setAttribute("data-bs-theme", theme);

            // Save preference in localStorage.
            try {

                window.localStorage.setItem("theme", theme);

            } catch (error) {

                console.warn(
                    "Unable to save theme in local storage.",
                    error
                );

            }

            // Save preference in cookie.
            const secureFlag = window.location.protocol === "https:"
                ? ";Secure"
                : "";

            document.cookie =
                "theme=" + theme +
                ";path=/" +
                ";max-age=31536000" +
                ";SameSite=Lax" +
                secureFlag;

        }

        // Restore theme even if the toggle button is unavailable.
        const savedTheme = getSavedTheme();

        if (savedTheme) {
            htmlElement.setAttribute("data-bs-theme", savedTheme);
        }

        if (themeToggle) {

            themeToggle.addEventListener("click", function () {

                const currentTheme =
                    htmlElement.getAttribute("data-bs-theme");

                const newTheme =
                    currentTheme === "dark" ? "light" : "dark";

                setTheme(newTheme);

            });

        }


        // --------------------------------------------------
        // ATTENDANCE: MARK ALL PRESENT
        // --------------------------------------------------

        const markAllBtn = document.getElementById(
            "markAllPresentBtn"
        );

        if (markAllBtn) {

            markAllBtn.addEventListener("click", function () {

                const attendanceFields = document.querySelectorAll(
                    'select[name^="form-"][name$="-status"]'
                );

                attendanceFields.forEach(function (select) {

                    select.value = "present";

                    // Notify other scripts about the value change.
                    select.dispatchEvent(
                        new Event("change", { bubbles: true })
                    );

                });

            });

        }


        // --------------------------------------------------
        // LANDING PAGE NAVIGATION
        // --------------------------------------------------

        const navToggle = document.getElementById("mainNavToggle");
        const mainNav = document.getElementById("mainNav");

        if (navToggle && mainNav) {

            navToggle.addEventListener("click", function () {

                const isOpen = mainNav.classList.toggle("open");

                navToggle.setAttribute(
                    "aria-expanded",
                    String(isOpen)
                );

            });

        }

    }


    // --------------------------------------------------
    // DOCUMENT INITIALIZATION
    // --------------------------------------------------

    // Supports both normal and dynamically loaded scripts.
    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializeApp,
            { once: true }
        );

    } else {

        initializeApp();

    }

})();
