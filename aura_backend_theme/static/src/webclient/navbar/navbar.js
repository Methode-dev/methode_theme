/** @odoo-module **/
/**
 * Aura Backend Theme - Community Edition — NavBar patch
 *
 * Adds to the stock Odoo NavBar:
 *   1. Collapsible left sidebar  (persisted in localStorage)
 *   2. Mobile off-canvas drawer  (hamburger open/close + backdrop)
 *   3. Global search popover     (menu/user commands with history)
 *   4. Sidebar quick links        (apps, settings, profile)
 *   5. Top sub-menu strip        (current app sections)
 *   6. Per-app icon resolution   (webIconData → img src)
 *
 * All state is local to the component — no Odoo models required.
 * Rename every `tbt_` prefix to your own namespace.
 */

import { patch }      from '@web/core/utils/patch';
import { registry }   from '@web/core/registry';
import { browser }    from '@web/core/browser/browser';
import { user }       from '@web/core/user';
import { NavBar }     from '@web/webclient/navbar/navbar';
import { ThemeSettingsDialog } from '../theme_settings/theme_settings_dialog';
import {
    onMounted,
    onPatched,
    onWillStart,
    onWillUnmount,
    useRef,
    useState,
} from '@odoo/owl';

// ─── Storage keys (change to your module prefix if you fork) ──────────────────
const STORAGE_SIDEBAR_COLLAPSED = 'tbt.sidebar_collapsed';
const STORAGE_SEARCH_HISTORY    = 'tbt.search_history';
const MAX_SEARCH_HISTORY        = 8;
const MAX_SEARCH_RESULTS        = 12;

// ─── Apps that should NOT show a sub-nav tree in the sidebar ─────────────────
const NO_SUBNAV_XMLIDS = new Set([
    'spreadsheet_dashboard.spreadsheet_dashboard_menu_root',
]);

// ─── App icon overrides ──────────────────────────────────────────────────────
// Provide these SVG files under aura_backend_theme/static/src/img/<name>.svg.
const ICON_PATH = {
    accounting: '/aura_backend_theme/static/src/img/accounting.svg',
    apps: '/aura_backend_theme/static/src/img/apps.svg',
    calendar: '/aura_backend_theme/static/src/img/second_icons/calendar.svg',
    contacts: '/aura_backend_theme/static/src/img/contacts.svg',
    crm: '/aura_backend_theme/static/src/img/crm.svg',
    documents: '/aura_backend_theme/static/src/img/second_icons/documents.svg',
    discuss: '/aura_backend_theme/static/src/img/discuss.svg',
    event: '/aura_backend_theme/static/src/img/second_icons/event.svg',
    fleet: '/aura_backend_theme/static/src/img/second_icons/fleet.svg',
    hr: '/aura_backend_theme/static/src/img/hr.svg',
    hrAttendance: '/aura_backend_theme/static/src/img/second_icons/hr_attendance.svg',
    hrExpense: '/aura_backend_theme/static/src/img/second_icons/hr_expense.svg',
    hrHolidays: '/aura_backend_theme/static/src/img/second_icons/hr_holidays.svg',
    hrRecruitment: '/aura_backend_theme/static/src/img/second_icons/hr_recruitment.svg',
    inventory: '/aura_backend_theme/static/src/img/inventory.svg',
    knowledge: '/aura_backend_theme/static/src/img/second_icons/knowledge.svg',
    maintenance: '/aura_backend_theme/static/src/img/second_icons/maintenance.svg',
    marketingAutomation: '/aura_backend_theme/static/src/img/second_icons/marketing_automation.svg',
    massMailing: '/aura_backend_theme/static/src/img/second_icons/mass_mailing.svg',
    mail: '/aura_backend_theme/static/src/img/second_icons/mail.svg',
    mrp: '/aura_backend_theme/static/src/img/second_icons/mrp.svg',
    planning: '/aura_backend_theme/static/src/img/second_icons/planning.svg',
    pointOfSale: '/aura_backend_theme/static/src/img/second_icons/point_of_sale.svg',
    project: '/aura_backend_theme/static/src/img/project.svg',
    purchase: '/aura_backend_theme/static/src/img/purchase.svg',
    quality: '/aura_backend_theme/static/src/img/second_icons/quality.svg',
    repair: '/aura_backend_theme/static/src/img/second_icons/repair.svg',
    sale: '/aura_backend_theme/static/src/img/second_icons/sale.svg',
    sales: '/aura_backend_theme/static/src/img/sales.svg',
    settings: '/aura_backend_theme/static/src/img/settings.svg',
    social: '/aura_backend_theme/static/src/img/second_icons/social.svg',
    spreadsheetDashboard: '/aura_backend_theme/static/src/img/second_icons/spreadsheet_dashboard.svg',
    stock: '/aura_backend_theme/static/src/img/second_icons/stock.svg',
    survey: '/aura_backend_theme/static/src/img/second_icons/survey.svg',
    website: '/aura_backend_theme/static/src/img/second_icons/website.svg',
};

// Highest priority: exact XMLID mapping.
const APP_ICON_OVERRIDES = {
    'base.menu_administration': ICON_PATH.settings,
    'base.menu_management': ICON_PATH.apps,
    'base.menu_apps': ICON_PATH.apps,
    'base.menu_custom': ICON_PATH.contacts,
    'contacts.menu_contacts': ICON_PATH.contacts,
    'crm.crm_menu_root': ICON_PATH.crm,
    'hr.menu_hr_root': ICON_PATH.hr,
    'mail.menu_root_discuss': ICON_PATH.discuss,
    'project.menu_main_pm': ICON_PATH.project,
    'purchase.menu_purchase_root': ICON_PATH.purchase,
    'sale.sale_menu_root': ICON_PATH.sales,
    'stock.menu_stock_root': ICON_PATH.inventory,
    'account.menu_finance': ICON_PATH.accounting,
    'account_accountant.menu_finance': ICON_PATH.accounting,
};

// Second priority: module-prefix mapping to scale to many apps.
const APP_ICON_BY_XMLID_PREFIX = {
    account: ICON_PATH.accounting,
    account_accountant: ICON_PATH.accounting,
    base: ICON_PATH.apps,
    calendar: ICON_PATH.calendar,
    contacts: ICON_PATH.contacts,
    crm: ICON_PATH.crm,
    documents: ICON_PATH.documents,
    event: ICON_PATH.event,
    fleet: ICON_PATH.fleet,
    hr: ICON_PATH.hr,
    hr_attendance: ICON_PATH.hrAttendance,
    hr_expense: ICON_PATH.hrExpense,
    hr_holidays: ICON_PATH.hrHolidays,
    hr_recruitment: ICON_PATH.hrRecruitment,
    knowledge: ICON_PATH.knowledge,
    mail: ICON_PATH.mail,
    maintenance: ICON_PATH.maintenance,
    marketing_automation: ICON_PATH.marketingAutomation,
    mass_mailing: ICON_PATH.massMailing,
    mrp: ICON_PATH.mrp,
    planning: ICON_PATH.planning,
    point_of_sale: ICON_PATH.pointOfSale,
    pos_sale: ICON_PATH.pointOfSale,
    project: ICON_PATH.project,
    purchase: ICON_PATH.purchase,
    quality: ICON_PATH.quality,
    repair: ICON_PATH.repair,
    sale: ICON_PATH.sale,
    social: ICON_PATH.social,
    spreadsheet_dashboard: ICON_PATH.spreadsheetDashboard,
    stock: ICON_PATH.stock,
    survey: ICON_PATH.survey,
    website: ICON_PATH.website,
};

// Last resort: app-name keyword mapping.
const APP_ICON_BY_NAME_KEYWORD = [
    ['account', ICON_PATH.accounting],
    ['invoice', ICON_PATH.accounting],
    ['billing', ICON_PATH.accounting],
    ['sale', ICON_PATH.sales],
    ['purchase', ICON_PATH.purchase],
    ['inventory', ICON_PATH.inventory],
    ['warehouse', ICON_PATH.inventory],
    ['manufact', ICON_PATH.inventory],
    ['discuss', ICON_PATH.discuss],
    ['chat', ICON_PATH.discuss],
    ['crm', ICON_PATH.crm],
    ['lead', ICON_PATH.crm],
    ['contact', ICON_PATH.contacts],
    ['hr', ICON_PATH.hr],
    ['employee', ICON_PATH.hr],
    ['recruit', ICON_PATH.hr],
    ['project', ICON_PATH.project],
    ['task', ICON_PATH.project],
    ['setting', ICON_PATH.settings],
    ['dashboard', ICON_PATH.apps],
    ['app', ICON_PATH.apps],
];

function resolveOverrideIcon(app) {
    const xmlid = app?.xmlid || '';
    const exact = APP_ICON_OVERRIDES[xmlid];
    if (exact) return exact;

    const modulePrefix = xmlid.split('.')[0];
    const byPrefix = APP_ICON_BY_XMLID_PREFIX[modulePrefix];
    if (byPrefix) return byPrefix;

    const appName = (app?.name || '').toLowerCase();
    const keywordRule = APP_ICON_BY_NAME_KEYWORD.find(([keyword]) => appName.includes(keyword));
    return keywordRule ? keywordRule[1] : null;
}

function normalizeOdooPath(pathname) {
    if (!pathname) return '';
    return pathname.endsWith('/') && pathname.length > 1
        ? pathname.slice(0, -1)
        : pathname;
}

function buildMenuHref(menu) {
    if (!menu || (!menu.actionPath && !menu.actionID)) return '';
    return `/odoo/${menu.actionPath || `action-${menu.actionID}`}`;
}

function findMenuPathById(tree, targetId, acc = []) {
    if (!tree) return null;
    const next = [...acc, tree];
    if (tree.id === targetId) {
        return next;
    }
    for (const child of tree.childrenTree || []) {
        const found = findMenuPathById(child, targetId, next);
        if (found) {
            return found;
        }
    }
    return null;
}

// ─────────────────────────────────────────────────────────────────────────────
patch(NavBar.prototype, {
    setup() {
        super.setup();

        // Reuse the stock web services directly from the environment.
        this.menuService   = this.env.services.menu;
        this.actionService = this.env.services.action;
        this.dialogService = this.env.services.dialog;
        this.orm = this.env.services.orm;
        this.tbtUser = user;
        this.tbtAccess = useState({ isSystemAdmin: false });

        onWillStart(async () => {
            this.tbtAccess.isSystemAdmin = await this.orm.call(
                'res.users',
                'has_group',
                [user.userId, 'base.group_system']
            );
        });

        // ── 1. Mobile off-canvas sidebar ─────────────────────────────────────
        this.mobileSidebarState = useState({ isOpen: false });
        this.toggleMobileSidebar = () => {
            this.mobileSidebarState.isOpen = !this.mobileSidebarState.isOpen;
        };
        this.closeMobileSidebar = () => {
            this.mobileSidebarState.isOpen = false;
        };
        this.topbarMenuState = useState({ mobileOpen: false });
        this.viewportState = useState({ isMobile: typeof window !== 'undefined' ? window.innerWidth < 992 : false });
        this.toggleMobileTopbarMenu = () => {
            this.topbarMenuState.mobileOpen = !this.topbarMenuState.mobileOpen;
        };
        this.closeMobileTopbarMenu = () => {
            this.topbarMenuState.mobileOpen = false;
        };

        // ── 2. Sidebar collapse (desktop) ─────────────────────────────────────
        this.sidebarState = useState({ collapsed: false });
        this._applySidebarClass = () => {
            document
                .querySelector('.o_web_client')
                ?.classList.toggle('tbt_sidebar_collapsed', this.sidebarState.collapsed);
        };
        this.toggleSidebarCollapse = () => {
            this.sidebarState.collapsed = !this.sidebarState.collapsed;
            this._applySidebarClass();
            try {
                browser.localStorage.setItem(
                    STORAGE_SIDEBAR_COLLAPSED,
                    this.sidebarState.collapsed ? '1' : '0'
                );
            } catch (_) { /* ignore */ }
        };
        // Restore persisted state
        try {
            this.sidebarState.collapsed =
                browser.localStorage.getItem(STORAGE_SIDEBAR_COLLAPSED) === '1';
        } catch (_) {
            this.sidebarState.collapsed = false;
        }

        // Classic top submenu: collapsed by default, open on click.
        this.topSubmenuState = useState({ openSectionId: null, openSubItemId: null, panelLeft: 0 });
        this.topSubmenuRef = useRef('topSubmenu');
        this.isTopSectionOpen = (sectionId) =>
            this.topSubmenuState.openSectionId === sectionId;
        this.getOpenTopSection = () =>
            this.currentAppSections.find(s => s.id === this.topSubmenuState.openSectionId) || null;
        this.toggleTopSection = (section, ev) => {
            const nextId = section?.id;
            const closing = this.topSubmenuState.openSectionId === nextId;
            this.topSubmenuState.openSectionId = closing ? null : nextId;
            this.topSubmenuState.openSubItemId = null;
            if (!closing && ev?.currentTarget) {
                const bar = this.topSubmenuRef.el;
                const btn = ev.currentTarget;
                const barRect = bar.getBoundingClientRect();
                const btnRect = btn.getBoundingClientRect();
                this.topSubmenuState.panelLeft = btnRect.left - barRect.left;
            }
        };
        this.isSubItemOpen = (itemId) =>
            this.topSubmenuState.openSubItemId === itemId;
        this.toggleSubItem = (item) => {
            const nextId = item?.id;
            this.topSubmenuState.openSubItemId =
                this.topSubmenuState.openSubItemId === nextId ? null : nextId;
        };
        this.onTopSubmenuItemSelection = (menu) => {
            this.topSubmenuState.openSectionId = null;
            this.topSubmenuState.openSubItemId = null;
            this.onNavBarDropdownItemSelection(menu);
        };
        this.onTopSectionLeafClick = (section) => {
            this.topSubmenuState.openSectionId = null;
            this.topSubmenuState.openSubItemId = null;
            this.onNavBarDropdownItemSelection(section);
        };

        // ── 3. Global search ──────────────────────────────────────────────────
        this.searchState = useState({
            open:       false,
            mobileOpen: false,
            query:      '',
            results:    [],
            loading:    false,
            history:    [],
        });
        this.searchContainerRef    = useRef('searchContainer');
        this.searchInputRef        = useRef('searchInput');
        this.searchInputMobileRef  = useRef('searchInputMobile');
        this.topbarMenuRef         = useRef('topbarMenu');
        this._searchRequestId      = 0;

        // history helpers
        this._loadSearchHistory = () => {
            try {
                const raw = browser.localStorage.getItem(STORAGE_SEARCH_HISTORY);
                const arr = raw ? JSON.parse(raw) : [];
                this.searchState.history = Array.isArray(arr)
                    ? arr.slice(0, MAX_SEARCH_HISTORY)
                    : [];
            } catch (_) {
                this.searchState.history = [];
            }
        };
        this._saveSearchHistory = (term) => {
            term = (term || '').trim();
            if (!term) return;
            const next = [term, ...this.searchState.history.filter(h => h !== term)]
                .slice(0, MAX_SEARCH_HISTORY);
            this.searchState.history = next;
            try {
                browser.localStorage.setItem(STORAGE_SEARCH_HISTORY, JSON.stringify(next));
            } catch (_) { /* ignore */ }
        };
        this._loadSearchHistory();

        // Command-palette footer tips (namespace shortcuts like /, @, #)
        this.searchFooterTips = registry
            .category('command_setup')
            .getEntries()
            .map(([ns, cfg]) => ({ namespace: ns, name: cfg.name }))
            .filter(t => t.name);

        // ── 4. Logo / company helpers ─────────────────────────────────────────
        this.getCompanyLogo = () => {
            const id = this.currentCompany?.id || '';
            return `/web/binary/company_logo?company=${id}`;
        };
        this.getUserAvatarUrl = () => {
            const userId = this.tbtUser?.userId;
            return userId
                ? `/web/image?model=res.users&id=${userId}&field=avatar_128`
                : '/web/static/img/default_icon_app.png';
        };
        this.onLogoClick = () => {
            browser.location.href = '/odoo/dashboards';
        };
        this.openMyProfile = () => {
            this.actionService.doAction('base.action_res_users_my');
        };

        // Topbar label: show only the active app name.
        this.getTopbarAppName = () => {
            const app = this.currentApp;
            return app?.name || '';
        };
        this.isMobileDiscussContext = () => {
            if (!this.viewportState?.isMobile) return false;
            const app = this.currentApp || {};
            const xmlid = (app.xmlid || "").toLowerCase();
            const name = (app.name || "").toLowerCase();
            return (
                xmlid === "mail.menu_root_discuss"
                || xmlid.startsWith("mail.")
                || name.includes("discuss")
                || name.includes("message")
                || name.includes("chat")
            );
        };

        // ── 5. App helpers ─────────────────────────────────────────────────────
        // this.menuService.getApps() is the correct Odoo 19 Community API.
        // It returns the top-level "app" menu items (root's direct children).
        this.isAppWithoutSubnav = () =>
            NO_SUBNAV_XMLIDS.has(this.currentApp?.xmlid);

        this.getApps = () => {
            return this.menuService.getApps().filter(a =>
                a.xmlid !== 'base.menu_administration' &&
                a.xmlid !== 'base.menu_management'
            );
        };
        this.getSettingsApp = () =>
            this.menuService.getApps()
                .find(a => a.xmlid === 'base.menu_administration' || a.name === 'Settings');
        this.getSystrayMobileLabel = (item) => {
            const key = item?.key || "";
            const keyLc = key.toLowerCase();
            if (keyLc.includes("messaging") || keyLc.includes("mail")) return "Messages";
            if (keyLc.includes("activity")) return "Activities";
            if (keyLc.includes("user")) return "Profile";
            if (keyLc.includes("company")) return "Company";
            if (keyLc.includes("debug")) return "Debug";
            return "Menu";
        };
        this.getAppsApp = () =>
            this.menuService.getApps()
                .find(a =>
                    a.xmlid === 'base.menu_management' ||
                    a.xmlid === 'base.menu_apps' ||
                    a.name === 'Apps'
                );

        this.openAppsMenu = () => {
            const apps = this.getAppsApp();
            if (apps) {
                this.onNavBarDropdownItemSelection(apps);
                return;
            }
            browser.location.href = '/odoo/apps/modules';
        };

        this.openSettingsMenu = () => {
            const settings = this.getSettingsApp();
            if (settings) {
                this.onNavBarDropdownItemSelection(settings);
                return;
            }
            browser.location.href = '/odoo/settings';
        };

        this.openThemeSettings = () => {
            if (!this.tbtAccess.isSystemAdmin) {
                return;
            }
            this.dialogService.add(ThemeSettingsDialog, {});
        };

        // Resolve an app's icon to a usable URL
        this.getAppIcon = (app) => {
            if (!app) return '/web/static/img/default_icon_app.png';
            const override = resolveOverrideIcon(app);
            if (override) {
                return override;
            }
            const data = app.webIconData;
            if (data) {
                if (data.startsWith('data:image') || data.startsWith('/')) return data;
                const prefix = data.startsWith('P')
                    ? 'data:image/svg+xml;base64,'
                    : 'data:image/png;base64,';
                return prefix + data.replace(/\s/g, '');
            }
            return '/web/static/img/default_icon_app.png';
        };

        // ── 6. Overflow tracking for the sidebar scroll area ──────────────────
        this.sidebarScrollRef  = useRef('sidebarScroll');
        this._updateOverflow   = () => {
            const el = this.sidebarScrollRef?.el;
            if (!el) return;
            el.parentElement?.classList.toggle(
                'tbt_sidebar_overflowing',
                el.scrollHeight > el.clientHeight + 1
            );
        };
        this._updateViewport = () => {
            this.viewportState.isMobile = window.innerWidth < 992;
            if (!this.viewportState.isMobile) {
                this.topbarMenuState.mobileOpen = false;
            }
        };

        // ── 7. Document-level listeners for closing popups on outside click ───
        this._onDocumentClick = (ev) => {
            const container = this.searchContainerRef?.el;
            if (!container) return;
            if (this.searchState.mobileOpen) return;
            if (this.searchState.open && !container.contains(ev.target)) {
                this.searchState.open = false;
            }

            const submenu = this.topSubmenuRef?.el;
            if (this.topSubmenuState.openSectionId && submenu && !submenu.contains(ev.target)) {
                this.topSubmenuState.openSectionId = null;
            }
            const topbarMenu = this.topbarMenuRef?.el;
            if (this.topbarMenuState.mobileOpen && topbarMenu && !topbarMenu.contains(ev.target)) {
                this.topbarMenuState.mobileOpen = false;
            }
        };
        this._onDocumentKeydown = (ev) => {
            if (ev.key !== 'Escape') return;
            if (this.searchState.open)      this.searchState.open      = false;
            if (this.searchState.mobileOpen) this.searchState.mobileOpen = false;
            if (this.topSubmenuState.openSectionId) this.topSubmenuState.openSectionId = null;
            if (this.topbarMenuState.mobileOpen) this.topbarMenuState.mobileOpen = false;
        };

        // ── Lifecycle ──────────────────────────────────────────────────────────
        onMounted(() => {
            this._applySidebarClass();
            this._updateViewport();
            this._updateOverflow();
            document.addEventListener('click',   this._onDocumentClick);
            document.addEventListener('keydown', this._onDocumentKeydown);
            window.addEventListener('resize',    this._updateOverflow);
            window.addEventListener('resize',    this._updateViewport);
        });
        onPatched(() => {
            this._updateOverflow();
            if (this.topSubmenuState.openSectionId && !this.getOpenTopSection()) {
                this.topSubmenuState.openSectionId = null;
            }
        });
        onWillUnmount(() => {
            document.querySelector('.o_web_client')
                ?.classList.remove('tbt_sidebar_collapsed');
            document.removeEventListener('click',   this._onDocumentClick);
            document.removeEventListener('keydown', this._onDocumentKeydown);
            window.removeEventListener('resize',    this._updateOverflow);
            window.removeEventListener('resize',    this._updateViewport);
        });
    },

    // ── Search ─────────────────────────────────────────────────────────────────

    toggleSearchPopover(ev) {
        ev?.stopPropagation();
        // On very small screens open the full-screen mobile overlay instead
        if (window.innerWidth < 540) {
            this.searchState.open       = false;
            this.searchState.mobileOpen = true;
            requestAnimationFrame(() => this.searchInputMobileRef?.el?.focus?.());
            if (this.searchState.query) this.runSearch();
            return;
        }
        this.searchState.open = !this.searchState.open;
        if (this.searchState.open) {
            requestAnimationFrame(() => this.searchInputRef?.el?.focus?.());
            if (this.searchState.query) this.runSearch();
        }
    },

    closeMobileSearch() {
        this.searchState.mobileOpen = false;
    },

    onSearchInput(ev) {
        this.searchState.query = ev?.target?.value || '';
        if (!this.searchState.open) this.searchState.open = true;
        this.runSearch();
    },

    onHistorySelect(term) {
        this.searchState.query = term;
        const input = this.searchInputMobileRef?.el || this.searchInputRef?.el;
        if (input) {
            input.value = term;
            input.focus();
            input.setSelectionRange(term.length, term.length);
        }
        this.runSearch();
    },

    applySearchNamespace(namespace) {
        this.searchState.query = namespace;
        const input = this.searchState.mobileOpen
            ? this.searchInputMobileRef?.el
            : this.searchInputRef?.el;
        if (input) {
            input.value = namespace;
            input.focus();
        }
        this.runSearch();
    },

    _parseSearchNamespaces(query) {
        const trimmed = (query || '').trimStart();
        const prefix  = trimmed[0];
        if (['/', '@', '#'].includes(prefix)) {
            return { namespaces: [prefix], searchValue: trimmed.slice(1).trimStart() };
        }
        return { namespaces: ['/', '@'], searchValue: trimmed };
    },

    async runSearch() {
        const { namespaces, searchValue } = this._parseSearchNamespaces(this.searchState.query);
        if (!searchValue) {
            this.searchState.results = [];
            this.searchState.loading = false;
            return;
        }
        const requestId = ++this._searchRequestId;
        this.searchState.loading = true;

        const providers = registry.category('command_provider').getAll();
        const matching  = providers.filter(p =>
            namespaces.includes(p.namespace || 'default')
        );
        const batches   = await Promise.all(
            matching.map(p => p.provide(this.env, { searchValue }))
        );
        if (requestId !== this._searchRequestId) return;

        this.searchState.results = batches.flat()
            .map((cmd, i) => ({
                id:      cmd.id || `${cmd.name}-${i}`,
                name:    cmd.name,
                href:    cmd.href,
                action:  cmd.action,
                iconUrl: cmd?.props?.imgUrl || cmd?.props?.webIconData,
            }))
            .slice(0, MAX_SEARCH_RESULTS);
        this.searchState.loading = false;
    },

    onSearchSelect(command) {
        this._saveSearchHistory(this.searchState.query);
        this.searchState.open       = false;
        this.searchState.mobileOpen = false;
        if (command?.action)          command.action();
        else if (command?.href)       browser.location.href = command.href;
    },

    getSearchFooterTips() {
        return this.searchFooterTips;
    },

    // ── Computed ───────────────────────────────────────────────────────────────

    get currentCompany() {
        return user.activeCompany;
    },
});
