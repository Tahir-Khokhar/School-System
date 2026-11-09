/*
 * test_sidebar.js — jsdom test for the mobile sidebar toggle.
 *
 * This test loads app.js into a simulated DOM and clicks the real ☰
 * button. It catches the event-bubbling bug where the toggle handler
 * adds `sidebar-open` and the document-level close handler immediately
 * removes it on the same click.
 *
 * Run: node test_sidebar.js
 * Exit code 0 = all tests passed; non-zero = a test failed.
 */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

// --- Load app.js source ---
const appJsPath = path.resolve(
    __dirname,
    "..",
    "..",
    "static",
    "js",
    "app.js"
);
const appJsSource = fs.readFileSync(appJsPath, "utf-8");

// --- DOM structure mirroring base.html ---
// The sidebar is a SIBLING of .main-wrapper (not nested inside it),
// and #sidebarToggle lives INSIDE .main-wrapper. This is the structure
// that broke the old .main-wrapper.sidebar-open .sidebar selector.
const HTML = `
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
  <aside class="sidebar" id="sidebar">
    <button id="sidebarCloseBtn" aria-label="Close sidebar">✕</button>
    <nav class="sidebar-nav">
      <a class="nav-link" href="/dashboard/">Dashboard</a>
    </nav>
  </aside>
  <div class="main-wrapper" id="main-wrapper">
    <nav class="navbar">
      <button id="sidebarToggle" aria-label="Toggle sidebar">☰</button>
    </nav>
    <main class="content-wrapper">
      <p>Main content area.</p>
    </main>
  </div>
  <script>${appJsSource}</script>
</body>
</html>
`;

let passCount = 0;
let failCount = 0;

function assert(label, condition) {
    if (condition) {
        passCount++;
        console.log("  ✓ " + label);
    } else {
        failCount++;
        console.error("  ✗ " + label);
    }
}

async function runTests() {

    const dom = new JSDOM(HTML, {
        runScripts: "dangerously",
        url: "http://localhost:8000/dashboard/",
        pretendToBeVisual: true,
    });

    // Wait for DOMContentLoaded so initializeApp has run and the
    // event listeners are registered.
    await new Promise((resolve) => {
        if (dom.window.document.readyState === "complete") {
            resolve();
        } else {
            dom.window.document.addEventListener(
                "DOMContentLoaded",
                resolve,
                { once: true }
            );
        }
    });
    // jsdom fires DOMContentLoaded asynchronously; give it a tick.
    await new Promise((r) => setTimeout(r, 50));

    const { document } = dom.window;
    const body = document.body;
    const toggle = document.getElementById("sidebarToggle");
    const closeBtn = document.getElementById("sidebarCloseBtn");
    const content = document.querySelector(".content-wrapper");

    console.log("\n--- Mobile sidebar toggle tests ---");

    // 1. Click the ☰ button → body must get `sidebar-open`.
    //    This is the test that catches the bubble bug: if the toggle
    //    click bubbles into the close handler, the class is removed
    //    before this assertion runs.
    toggle.click();
    assert(
        "clicking ☰ opens the sidebar (body has sidebar-open)",
        body.classList.contains("sidebar-open")
    );
    assert(
        "☰ button sets aria-expanded=true",
        toggle.getAttribute("aria-expanded") === "true"
    );

    // 2. Click the ☰ button again → sidebar closes (toggle).
    toggle.click();
    assert(
        "clicking ☰ again closes the sidebar (toggle off)",
        !body.classList.contains("sidebar-open")
    );
    assert(
        "☰ button sets aria-expanded=false",
        toggle.getAttribute("aria-expanded") === "false"
    );

    // 3. Open via ☰, then close via the close button.
    toggle.click();
    assert("sidebar opened for close-button test", body.classList.contains("sidebar-open"));
    closeBtn.click();
    assert(
        "close button (#sidebarCloseBtn) closes the sidebar",
        !body.classList.contains("sidebar-open")
    );

    // 4. Open via ☰, then press Escape → sidebar closes.
    toggle.click();
    assert("sidebar opened for Escape test", body.classList.contains("sidebar-open"));
    document.dispatchEvent(
        new dom.window.KeyboardEvent("keydown", { key: "Escape" })
    );
    assert(
        "Escape key closes the sidebar",
        !body.classList.contains("sidebar-open")
    );

    // 5. Open via ☰, then click on the content area (outside sidebar)
    //    → sidebar closes (tap-to-close).
    toggle.click();
    assert("sidebar opened for tap-outside test", body.classList.contains("sidebar-open"));
    content.click();
    assert(
        "clicking content area (outside sidebar) closes the drawer",
        !body.classList.contains("sidebar-open")
    );

    // 6. Open via ☰, then click inside the sidebar → stays open.
    toggle.click();
    assert("sidebar opened for inside-click test", body.classList.contains("sidebar-open"));
    document.querySelector(".sidebar-nav .nav-link").click();
    assert(
        "clicking inside the sidebar does NOT close it",
        body.classList.contains("sidebar-open")
    );

    // 7. The toggle does not use the old .main-wrapper class.
    const wrapper = document.getElementById("main-wrapper");
    assert(
        "main-wrapper never gets sidebar-open class (old bug gone)",
        !wrapper.classList.contains("sidebar-open")
    );

    dom.window.close();

    console.log(
        "\n" + passCount + " passed, " + failCount + " failed"
    );
    process.exit(failCount === 0 ? 0 : 1);
}

runTests().catch((err) => {
    console.error("Test harness error:", err);
    process.exit(2);
});
