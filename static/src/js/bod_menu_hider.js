/** @odoo-module **/

function injectHideStyle() {
    let style = document.getElementById("bod-menu-hider");
    if (!style) {
        style = document.createElement("style");
        style.id = "bod-menu-hider";
        style.textContent = `
            a[data-menu-xmlid="peepl_weekly_report.menu_peepl_weekly_report"] {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    }
}

// Check if current page has Department Reports menu (BOD only)
function checkAndHideMenu() {
    const deptReportsMenu = document.querySelector(
        'a[data-menu-xmlid="peepl_weekly_report.menu_peepl_departments_bod"]'
    );

    if (deptReportsMenu) {
        injectHideStyle();
        return true;
    }
    return false;
}

/* =========================
   INSTANT OBSERVER
   ========================= */
const observer = new MutationObserver(() => {
    if (checkAndHideMenu()) {
        observer.disconnect(); // stop once done
    }
});

// Observe ASAP, even before menu visible
observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
});

// Fallback (safety, very early)
checkAndHideMenu();
