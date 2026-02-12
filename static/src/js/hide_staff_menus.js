/** @odoo-module **/

function injectHideStyle() {
    let style = document.getElementById("staff-menu-hider");
    if (!style) {
        style = document.createElement("style");
        style.id = "staff-menu-hider";
        style.textContent = `
            a[data-menu-xmlid="peepl_weekly_report.menu_peepl_dashboard_main"],
            a[data-menu-xmlid="peepl_weekly_report.menu_peepl_pic_overview_main"] {
                display: none !important;
            }
        `;
        document.head.appendChild(style);
    }
}

function checkAndHideMenu() {
    const weeklyReportsMenu = document.querySelector(
        'a[data-menu-xmlid="peepl_weekly_report.menu_peepl_weekly_report"]'
    );
    const deptReportsMenu = document.querySelector(
        'a[data-menu-xmlid="peepl_weekly_report.menu_peepl_departments_bod"]'
    );
    const dashboardMenu = document.querySelector(
        'a[data-menu-xmlid="peepl_weekly_report.menu_peepl_dashboard_main"]'
    );

    // Staff = ada Weekly Reports, tidak ada Department Reports, tidak ada Dashboard (karena groups)
    if (weeklyReportsMenu && !deptReportsMenu && !dashboardMenu) {
        injectHideStyle();
        return true;
    }
    return false;
}

const observer = new MutationObserver(() => {
    checkAndHideMenu();
});

observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
});

checkAndHideMenu();
