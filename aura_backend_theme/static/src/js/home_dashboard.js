/** @odoo-module **/

import { Component, useState, onMounted, onPatched, onWillUnmount, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { cookie } from "@web/core/browser/cookie";

// ── helpers ───────────────────────────────────────────────────────────────────

function fmtAmount(amount, currencySymbol = "", currencyPosition = "before") {
    if (amount == null) return "—";
    const formatted = amount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    if (!currencySymbol) return formatted;
    return currencyPosition === "after" ? `${formatted} ${currencySymbol}` : `${currencySymbol} ${formatted}`;
}

function debounce(fn, ms) {
    let timer;
    return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), ms); };
}

export function openDashboardTarget(actionService, target) {
    if (!target || target === "#") return;
    if (typeof target === "object") {
        actionService.doAction(target);
        return;
    }
    if (typeof target === "string" && target.startsWith("/web#")) {
        const params = new URLSearchParams(target.slice(target.indexOf("#") + 1));
        const model = params.get("model");
        if (model) {
            const resId = Number(params.get("id"));
            const viewType = params.get("view_type") || (resId ? "form" : "list");
            actionService.doAction({
                type: "ir.actions.act_window",
                name: model,
                res_model: model,
                res_id: resId || undefined,
                views: [[false, viewType]],
                target: "current",
            });
            return;
        }
    }
    window.location.href = target;
}

class DashboardComponent extends Component {
    setup() {
        this.actionService = useService("action");
    }

    navigate(target) {
        openDashboardTarget(this.actionService, target);
    }
}

const DEFAULT_STATS_KEYS = ["invoices_open", "bills_overdue", "activities_due", "pipeline_value"];
const STAT_CARD_DEFS = [
    { key: "invoices_open", label: "Factures ouvertes", group: "Accounting", module: "account" },
    { key: "bills_overdue", label: "Factures fournisseurs en retard", group: "Accounting", module: "account" },
    { key: "accounting_cashflow", label: "Trésorerie", group: "Accounting", module: "account" },
    { key: "accounting_aged_receivables", label: "Créances anciennes", group: "Accounting", module: "account" },
    { key: "inventory_reorder", label: "Alertes de réapprovisionnement", group: "Inventory", module: "stock" },
    { key: "inventory_receipts", label: "Réceptions en attente", group: "Inventory", module: "stock" },
    { key: "sales_quotations", label: "Devis", group: "Sales", module: "sale" },
    { key: "sales_to_invoice", label: "Commandes à facturer", group: "Sales", module: "sale" },
    { key: "project_tasks", label: "Mes tâches", group: "Project", module: "project" },
    { key: "project_deadlines", label: "Échéances", group: "Project", module: "project" },
    { key: "mrp_production", label: "Ordres de fabrication", group: "Manufacturing", module: "mrp" },
    { key: "hr_leaves", label: "Demandes de congé", group: "Human Resources", module: "hr" },
    { key: "hr_attendance", label: "Présences du jour", group: "Human Resources", module: "hr" },
    { key: "activities_due", label: "Mes activités", group: "General", module: null },
    { key: "pipeline_value", label: "Pipeline", group: "General", module: "crm" },
];
const STAT_CARD_MAP = Object.fromEntries(STAT_CARD_DEFS.map((entry) => [entry.key, entry]));
function normalizeStatKeys(rawValue) {
    const seen = new Set();
    const values = (rawValue || "").split(",").map((value) => value.trim()).filter(Boolean);
    const result = [];
    for (const value of values) {
        if (!STAT_CARD_MAP[value] || seen.has(value)) continue;
        seen.add(value);
        result.push(value);
    }
    for (const fallback of DEFAULT_STATS_KEYS) {
        if (result.length >= 4) break;
        if (!seen.has(fallback)) {
            seen.add(fallback);
            result.push(fallback);
        }
    }
    return result.slice(0, 4);
}

// ── QuickActionsBar ───────────────────────────────────────────────────────────

class QuickActionsBar extends DashboardComponent {
    static template = "aura_backend_theme.QuickActionsBar";
    static props = ["actions"];
}

// ── InsightBanners ────────────────────────────────────────────────────────────

class InsightBanners extends DashboardComponent {
    static template = "aura_backend_theme.InsightBanners";
    static props = ["insights"];
}

// ── StatCard ──────────────────────────────────────────────────────────────────

class StatCard extends DashboardComponent {
    static template = "aura_backend_theme.StatCard";
    static props = ["label", "value", "meta", "color", "icon", "viewUrl", "createUrl", "viewAction", "createAction", "trend", "monetary", "currencySymbol", "currencyPosition"];

    get displayValue() {
        const { value, monetary, currencySymbol, currencyPosition } = this.props;
        if (monetary) {
            return fmtAmount(value, currencySymbol, currencyPosition);
        }
        return fmtAmount(value);
    }

    get trendClass() { return this.props.trend == null ? "" : this.props.trend >= 0 ? "hd-trend-up" : "hd-trend-down"; }
    get trendIcon()  { return this.props.trend == null ? "" : this.props.trend >= 0 ? "fa-arrow-up" : "fa-arrow-down"; }
    get trendLabel() {
        const t = this.props.trend;
        return t == null ? "" : `${t >= 0 ? "+" : ""}${t}%`;
    }
}

// ── DashboardStatsRow ─────────────────────────────────────────────────────────

class DashboardStatsRow extends Component {
    static template = "aura_backend_theme.DashboardStatsRow";
    static props = ["stats", "config"];
    static components = { StatCard };

    get enabledStats() {
        const { stats, config } = this.props;
        const enabled = normalizeStatKeys(config.stats_modules);
        const cards = stats?.cards || {};
        return enabled
            .map((key) => {
                const card = cards[key];
                if (!card) return null;
                return {
                    key,
                    label: card.label || STAT_CARD_MAP[key]?.label || key,
                    value: card.value,
                    meta: card.meta,
                    color: card.color,
                    icon: card.icon,
                    viewUrl: card.viewUrl,
                    createUrl: card.createUrl,
                    viewAction: card.viewAction,
                    createAction: card.createAction,
                    trend: card.trend,
                    monetary: Boolean(card.monetary),
                    currencySymbol: card.currency_symbol || "",
                    currencyPosition: card.currency_position || "before",
                };
            })
            .filter(Boolean);
    }
}

// ── DashboardTopBar ───────────────────────────────────────────────────────────

class DashboardTopBar extends Component {
    static template = "aura_backend_theme.DashboardTopBar";
    static props = ["user", "onOpenConfig", "onOpenPicker", "onOpenCustomWidget", "onToggleEdit", "onToggleMenu", "editMode", "menuOpen"];

    greeting() {
        const h = new Date().getHours();
        if (h < 12) return "Bonjour";
        if (h < 18) return "Bon après-midi";
        return "Bonsoir";
    }
}

// ── WidgetActivities ──────────────────────────────────────────────────────────

class WidgetActivities extends DashboardComponent {
    static template = "aura_backend_theme.WidgetActivities";
    static props = ["activities", "config", "onDone"];

    get groups() {
        return [
            { key: "overdue",  label: "En retard",  items: this.props.activities.filter(a => a.days_overdue > 0),  urgent: true },
            { key: "today",    label: "Aujourd'hui",    items: this.props.activities.filter(a => a.days_overdue === 0), urgent: false },
            { key: "upcoming", label: "À venir", items: this.props.activities.filter(a => a.days_overdue < 0),  urgent: false },
        ].filter(g => g.items.length > 0);
    }

    badgeClass(days) {
        if (days > 0) return "hd-badge hd-badge-overdue";
        if (days === 0) return "hd-badge hd-badge-today";
        return "hd-badge hd-badge-soon";
    }

    daysLabel(days) {
        if (days > 0) return `${days}d overdue`;
        if (days === 0) return "Today";
        return `in ${Math.abs(days)}d`;
    }
}

// ── WidgetInvoices ────────────────────────────────────────────────────────────

class WidgetInvoices extends DashboardComponent {
    static template = "aura_backend_theme.WidgetInvoices";
    static props = ["invoices", "config", "onFilterChange"];

    badgeClass(statusLabel) {
        return { Overdue: "hd-badge hd-badge-overdue", Posted: "hd-badge hd-badge-posted", Draft: "hd-badge hd-badge-draft", Paid: "hd-badge hd-badge-soon" }[statusLabel] || "hd-badge hd-badge-draft";
    }
}

// ── WidgetPipeline ────────────────────────────────────────────────────────────

class WidgetPipeline extends DashboardComponent {
    static template = "aura_backend_theme.WidgetPipeline";
    static props = ["pipeline", "config"];

    oppClass(priority) { return `hd-opp priority-${priority}`; }

    staleClass(days) {
        if (days > 14) return "hd-stage-badge hd-stage-stale";
        if (days > 7)  return "hd-stage-badge hd-stage-warn";
        return "hd-stage-badge";
    }
}

// ── WidgetRecent ──────────────────────────────────────────────────────────────

class WidgetRecent extends DashboardComponent {
    static template = "aura_backend_theme.WidgetRecent";
    static props = ["recent", "config"];

    timeAgo(isoStr) {
        if (!isoStr) return "";
        const diff = Date.now() - new Date(isoStr).getTime();
        const mins = Math.floor(diff / 60000);
        if (mins < 1) return "à l'instant";
        if (mins < 60) return `il y a ${mins} min`;
        const hrs = Math.floor(mins / 60);
        if (hrs < 24) return `il y a ${hrs} h`;
        return `il y a ${Math.floor(hrs / 24)} j`;
    }
}

// ── TodaysFocus ───────────────────────────────────────────────────────────────

class TodaysFocus extends DashboardComponent {
    static template = "aura_backend_theme.TodaysFocus";
    static props = ["activities", "insights", "onDone"];

    get urgentItems() {
        if (!this.props.activities) return [];
        return this.props.activities.filter(a => a.days_overdue >= 0).slice(0, 5);
    }

    get hasAnything() {
        return this.urgentItems.length > 0 || (this.props.insights && this.props.insights.length > 0);
    }

    badgeClass(days) { return days > 0 ? "hd-badge hd-badge-overdue" : "hd-badge hd-badge-today"; }
}

// ── DashboardConfigPanel ──────────────────────────────────────────────────────

class DashboardConfigPanel extends Component {
    static template = "aura_backend_theme.DashboardConfigPanel";
    static props = ["config", "stats", "open", "onClose", "onSave"];

    setup() {
        this.debouncedSave = debounce((field, val) => this.props.onSave({ [field]: val }), 500);
    }

    onToggle(field, ev) { this.props.onSave({ [field]: ev.target.checked }); }
    onNumber(field, ev) { const v = parseInt(ev.target.value, 10); if (!isNaN(v)) this.debouncedSave(field, v); }
    onSelect(field, ev) { this.props.onSave({ [field]: ev.target.value }); }
    onRadio(field, val) { this.props.onSave({ [field]: val }); }
    onStep(field, delta, min, max) {
        const current = parseInt(this.props.config[field], 10);
        const safeCurrent = Number.isFinite(current) ? current : min;
        const next = Math.max(min, Math.min(max, safeCurrent + delta));
        this.props.onSave({ [field]: next });
    }

    get moduleSlots() {
        const keys = normalizeStatKeys(this.props.config.stats_modules);
        return keys.map((key, index) => {
            const otherKeys = keys.filter((_, otherIndex) => otherIndex !== index);
            const options = STAT_CARD_DEFS.map((entry) => ({
                ...entry,
                labelText: `${entry.group} - ${entry.label}`,
                available: !!this.props.stats?.cards?.[entry.key],
            })).filter((entry) => entry.key === key || !otherKeys.includes(entry.key));
            return {
                index,
                value: key,
                options,
            };
        });
    }

    onModuleSlotChange(index, ev) {
        const keys = normalizeStatKeys(this.props.config.stats_modules);
        keys[index] = ev.target.value;
        this.props.onSave({ stats_modules: keys.join(",") });
    }
}

// ── WidgetPicker ──────────────────────────────────────────────────────────────

class WidgetPicker extends Component {
    static template = "aura_backend_theme.WidgetPicker";
    static props = ["open", "widgets", "onClose", "onAdd", "onRemove", "onRestoreDefaults"];

    setup() {
        this.state = useState({ search: "" });
    }

    get groups() {
        const s = this.state.search.toLowerCase();
        const filtered = this.props.widgets.filter(w =>
            !s || w.label.toLowerCase().includes(s) || w.description.toLowerCase().includes(s)
        );
        const groupMap = {};
        for (const w of filtered) {
            if (!groupMap[w.group]) groupMap[w.group] = [];
            groupMap[w.group].push(w);
        }
        return Object.entries(groupMap).map(([name, items]) => ({ name, items }));
    }
}

// ── WidgetUnavailable ────────────────────────────────────────────────────────

class WidgetUnavailable extends Component {
    static template = "aura_backend_theme.WidgetUnavailable";
    static props = ["widget", "onRemove"];
}

// ── WidgetSettingsModal ─────────────────────────────────────────────────────

class WidgetSettingsModal extends Component {
    static template = "aura_backend_theme.WidgetSettingsModal";
    static props = ["open", "widget", "draft", "error", "onClose", "onSave", "onDraftChange"];
}

// ── CustomModelWidget ───────────────────────────────────────────────────────

class CustomModelWidget extends DashboardComponent {
    static template = "aura_backend_theme.CustomModelWidget";
    static props = ["data"];

    formatValue(value) {
        if (typeof value === "number") {
            return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
        }
        return value || "";
    }
}

// ── CustomWidgetBuilder ─────────────────────────────────────────────────────

class CustomWidgetBuilder extends Component {
    static template = "aura_backend_theme.CustomWidgetBuilder";
    static props = ["open", "models", "fields", "draft", "error", "loading", "onClose", "onSave", "onDraftChange", "onModelChange"];

    get numericFields() {
        return (this.props.fields || []).filter((field) => field.numeric);
    }

    update(field, value) {
        this.props.onDraftChange({ ...this.props.draft, [field]: value });
    }

    onModelChange(ev) {
        this.props.onModelChange(ev.target.value);
    }

    onWidgetTypeChange(ev) {
        this.update("widget_type", ev.target.value);
    }

    onLimitChange(ev) {
        const value = parseInt(ev.target.value, 10);
        this.update("limit", Number.isFinite(value) ? value : 5);
    }

    onAggregationChange(ev) {
        this.update("aggregation", ev.target.value);
    }

    onMeasureChange(ev) {
        this.update("measure_field", ev.target.value);
    }

    onFieldToggle(fieldName, ev) {
        const current = this.props.draft.fields || [];
        const next = ev.target.checked
            ? [...current.filter((name) => name !== fieldName), fieldName].slice(0, 6)
            : current.filter((name) => name !== fieldName);
        this.update("fields", next);
    }

    fieldChecked(fieldName) {
        return (this.props.draft.fields || []).includes(fieldName);
    }
}

// ── Widget registry ───────────────────────────────────────────────────────────
// Maps widget_id → { component, getProps(data, callbacks) }
// Future app widgets (Phase 2+) extend this registry.

const HOME_WIDGET_DEFS = {
    quick_actions: {
        component: QuickActionsBar,
        getProps: (data) => ({ actions: data.quick_actions || [] }),
        isHidden: (data) => !data.quick_actions || !data.quick_actions.length,
    },
    stats: {
        component: DashboardStatsRow,
        getProps: (data) => ({ stats: data.stats, config: data.config }),
        isHidden: (data) => !data.config.show_stats_row || !data.stats,
    },
    activities: {
        component: WidgetActivities,
        getProps: (data, cb) => ({ activities: data.activities || [], config: data.config, onDone: cb.onDone }),
        isHidden: (data) => !data.config.show_activities || !data.activities,
    },
    focus: {
        component: TodaysFocus,
        getProps: (data, cb) => ({ activities: data.activities, insights: data.insights, onDone: cb.onDone }),
    },
    invoices: {
        component: WidgetInvoices,
        getProps: (data, cb) => ({ invoices: data.invoices || [], config: data.config, onFilterChange: cb.onFilterChange }),
        isHidden: (data) => !data.config.show_invoices || !data.invoices,
    },
    pipeline: {
        component: WidgetPipeline,
        getProps: (data) => ({ pipeline: data.pipeline || [], config: data.config }),
        isHidden: (data) => !data.config.show_pipeline || !data.pipeline,
    },
    recent: {
        component: WidgetRecent,
        getProps: (data) => ({ recent: data.recent || [], config: data.config }),
        isHidden: (data) => !data.config.show_recent || !data.recent,
    },
};

// External app widgets (Phase 2+) register here:
export const homeWidgetRegistry = registry.category("aura_home_widgets");

// ── Root component ────────────────────────────────────────────────────────────

class HomeDashboardClientAction extends Component {
    static template = "aura_backend_theme.HomeDashboard";
    static components = {
        DashboardTopBar,
        WidgetPicker,
        WidgetUnavailable,
        WidgetSettingsModal,
        CustomWidgetBuilder,
        InsightBanners,
        DashboardConfigPanel,
    };
    static props = ["*"];

    setup() {
        this.notification = useService("notification");
        this.widgetGridRef = useRef("widgetGrid");
        this.masonryRaf = 0;
        this.masonryObserver = null;
        this.masonryObserved = new WeakSet();
        this.onMasonryResize = () => this.scheduleMasonryLayout();
        this.state = useState({
            loading: true,
            error: null,
            data: null,
            widgetRows: [],
            availableWidgets: [],
            editMode: false,
            topbarMenuOpen: false,
            configOpen: false,
            pickerOpen: false,
            settingsOpen: false,
            settingsWidget: null,
            settingsDraft: "{}",
            settingsError: null,
            customBuilderOpen: false,
            customModels: [],
            customFields: [],
            customDraft: {
                title: "",
                model: "",
                widget_type: "table",
                fields: [],
                aggregation: "count",
                measure_field: "",
                limit: 5,
            },
            customError: null,
            customLoading: false,
            savingConfig: false,
            dragging: null,
            dragOver: null,
        });
        onMounted(() => {
            this.loadAll();
            window.addEventListener("resize", this.onMasonryResize);
        });
        onPatched(() => this.scheduleMasonryLayout());
        onWillUnmount(() => {
            window.removeEventListener("resize", this.onMasonryResize);
            if (this.masonryRaf) {
                cancelAnimationFrame(this.masonryRaf);
            }
            if (this.masonryObserver) {
                this.masonryObserver.disconnect();
            }
        });
    }

    // ── data loading ─────────────────────────────────────────────────────────

    async loadAll() {
        this.state.loading = true;
        this.state.error = null;
        try {
            const [data, widgetData] = await Promise.all([
                rpc("/web/home_dashboard/data", {}),
                rpc("/web/home_dashboard/widgets", {}),
            ]);
            this.state.data = data;
            this.state.widgetRows = widgetData.active;
            this.state.availableWidgets = widgetData.available;
        } catch {
            this.state.error = "Failed to load dashboard. Please refresh the page.";
        } finally {
            this.state.loading = false;
        }
    }

    async reloadData() {
        try {
            const data = await rpc("/web/home_dashboard/data", {});
            this.state.data = data;
        } catch {
            // Non-critical: dashboard data stays stale until next full load.
        }
    }

    async reloadWidgets() {
        const widgetData = await rpc("/web/home_dashboard/widgets", {});
        this.state.widgetRows = widgetData.active;
        this.state.availableWidgets = widgetData.available;
    }

    get isDarkMode() {
        return cookie.get("color_scheme") === "dark";
    }

    get normalizedThemeName() {
        return "aura";
    }

    get normalizedThemeMode() {
        const mode = this.state.data?.config?.theme_mode || "auto";
        if (mode !== "auto" && mode !== "manual") {
            return "auto";
        }
        if (mode === "auto") {
            return this.isDarkMode ? "dark" : "bright";
        }
        return this.state.data?.config?.effective_theme_mode === "dark" ? "dark" : "bright";
    }

    get dashboardRootClass() {
        const classes = ["o_home_dashboard"];
        const density = this.state.data?.config?.layout_density;
        if (density === "compact") classes.push("hd-compact");
        if (density === "spacious") classes.push("hd-spacious");
        classes.push(`hd-theme-${this.normalizedThemeName}`);
        classes.push(this.normalizedThemeMode === "dark" ? "hd-mode-dark" : "hd-mode-bright");
        if (this.state.editMode) classes.push("hd-edit-mode");
        return classes.join(" ");
    }

    // ── widget grid ──────────────────────────────────────────────────────────

    scheduleMasonryLayout() {
        if (this.masonryRaf) {
            cancelAnimationFrame(this.masonryRaf);
        }
        this.masonryRaf = requestAnimationFrame(() => {
            this.masonryRaf = 0;
            this.layoutMasonryGrid();
        });
    }

    layoutMasonryGrid() {
        const grid = this.widgetGridRef.el;
        if (!grid) return;

        const cells = [...grid.querySelectorAll(".hd-widget-cell, .hd-widget-add-cell")];
        if (!cells.length) return;

        if (!this.masonryObserver && typeof ResizeObserver !== "undefined") {
            this.masonryObserver = new ResizeObserver(this.onMasonryResize);
        }
        if (this.masonryObserver && !this.masonryObserved.has(grid)) {
            this.masonryObserver.observe(grid);
            this.masonryObserved.add(grid);
        }

        const styles = getComputedStyle(grid);
        const rowHeight = parseFloat(styles.getPropertyValue("grid-auto-rows")) || 8;
        const rowGap = parseFloat(styles.getPropertyValue("row-gap")) || 0;

        for (const cell of cells) {
            cell.style.gridRowEnd = "auto";
            if (this.masonryObserver && !this.masonryObserved.has(cell)) {
                this.masonryObserver.observe(cell);
                this.masonryObserved.add(cell);
            }
        }

        for (const cell of cells) {
            const height = cell.getBoundingClientRect().height;
            const span = Math.max(1, Math.ceil((height + rowGap) / (rowHeight + rowGap)));
            cell.style.gridRowEnd = `span ${span}`;
        }
    }

    get renderedWidgets() {
        if (!this.state.data || !this.state.widgetRows.length) return [];
        const data = this.state.data;
        const cb = {
            onDone: (id) => this.markActivityDone(id),
            onFilterChange: (f) => this.onInvoiceFilterChange(f),
        };
        const result = [];
        for (const row of this.state.widgetRows) {
            // Check built-in registry first, then external registry
            let def = HOME_WIDGET_DEFS[row.widget_id];
            if (!def && row.custom) {
                def = {
                    component: CustomModelWidget,
                    useWidgetData: true,
                    getProps: (_data, widgetData) => ({ data: widgetData || {} }),
                };
            }
            if (!def) {
                try { def = homeWidgetRegistry.get(row.widget_id); } catch { continue; }
            }
            const isMissing = row.missing === true;
            if (!def && !isMissing) continue;
            if (def && def.isHidden && def.isHidden(data) && !isMissing) continue;
            const component = def ? def.component : WidgetUnavailable;
            const props = def
                ? (def.useWidgetData ? def.getProps(data, row.data, cb) : def.getProps(data, cb))
                : {};
            if (row.data?.viewAction) {
                props.viewAction = row.data.viewAction;
            }
            if (row.data?.createAction) {
                props.createAction = row.data.createAction;
            }
            result.push({
                widget_id: row.widget_id,
                col_span: row.col_span,
                component,
                missing: isMissing,
                widget: row,
                widgetConfig: row.config || {},
                props,
            });
        }
        return result;
    }

    // ── actions ──────────────────────────────────────────────────────────────

    async markActivityDone(activityId) {
        try {
            await rpc("/web/dataset/call_kw", {
                model: "mail.activity",
                method: "action_feedback",
                args: [[activityId]],
                kwargs: { feedback: "" },
            });
            // Only the dashboard data (activities, stats) needs refreshing — not the widget layout.
            await this.reloadData();
        } catch {
            this.notification.add("Could not mark activity as done.", { type: "danger" });
        }
    }

    async saveConfig(values) {
        this.state.savingConfig = true;
        try {
            await rpc("/web/home_dashboard/save_config", { values });
            await this.loadAll();
        } catch {
            this.notification.add("Could not save settings.", { type: "danger" });
        } finally {
            this.state.savingConfig = false;
        }
    }

    async onInvoiceFilterChange(filter) {
        await this.saveConfig({ invoice_filter: filter });
    }

    toggleEditMode() {
        this.state.editMode = !this.state.editMode;
        if (!this.state.editMode) {
            this.state.pickerOpen = false;
            this.closeWidgetSettings();
            this.state.dragging = null;
            this.state.dragOver = null;
        }
    }

    toggleTopbarMenu() {
        this.state.topbarMenuOpen = !this.state.topbarMenuOpen;
    }

    closeTopbarMenu() {
        this.state.topbarMenuOpen = false;
    }

    openEditModeFromMenu() {
        this.toggleEditMode();
        this.closeTopbarMenu();
    }

    openWidgetsFromMenu() {
        if (!this.state.editMode) {
            this.toggleEditMode();
        }
        this.state.pickerOpen = true;
        this.closeTopbarMenu();
    }

    async openCustomWidgetFromMenu() {
        if (!this.state.editMode) {
            this.toggleEditMode();
        }
        this.closeTopbarMenu();
        this.state.customBuilderOpen = true;
        this.state.customError = null;
        this.state.customDraft = {
            title: "",
            model: "",
            widget_type: "table",
            fields: [],
            aggregation: "count",
            measure_field: "",
            limit: 5,
        };
        if (!this.state.customModels.length) {
            this.state.customLoading = true;
            try {
                const response = await rpc("/web/home_dashboard/custom/models", {});
                this.state.customModels = response.models || [];
            } catch {
                this.state.customError = "Could not load models.";
            } finally {
                this.state.customLoading = false;
            }
        }
    }

    openSettingsFromMenu() {
        this.toggleConfig();
        this.closeTopbarMenu();
    }

    toggleConfig() { this.state.configOpen = !this.state.configOpen; }
    togglePicker() {
        if (!this.state.editMode) {
            this.notification.add("Enable edit mode to change widgets.", { type: "warning" });
            return;
        }
        this.state.pickerOpen = !this.state.pickerOpen;
    }

    closeCustomWidgetBuilder() {
        this.state.customBuilderOpen = false;
        this.state.customError = null;
    }

    updateCustomDraft(values) {
        this.state.customDraft = { ...this.state.customDraft, ...values };
        this.state.customError = null;
    }

    async onCustomModelChange(model) {
        this.state.customDraft = {
            ...this.state.customDraft,
            model,
            fields: [],
            measure_field: "",
        };
        this.state.customFields = [];
        if (!model) return;
        this.state.customLoading = true;
        try {
            const response = await rpc("/web/home_dashboard/custom/fields", { model });
            this.state.customFields = response.fields || [];
            const defaultFields = this.state.customFields
                .map((field) => field.name)
                .filter((name) => ["display_name", "name", "state", "date", "write_date"].includes(name))
                .slice(0, 3);
            this.state.customDraft = { ...this.state.customDraft, fields: defaultFields };
        } catch {
            this.state.customError = "Could not load fields for this model.";
        } finally {
            this.state.customLoading = false;
        }
    }

    async saveCustomWidget() {
        const draft = this.state.customDraft;
        if (!draft.model) {
            this.state.customError = "Choose a model first.";
            return;
        }
        if (!draft.title.trim()) {
            this.state.customError = "Give the widget a title.";
            return;
        }
        if (draft.widget_type === "table" && !(draft.fields || []).length) {
            this.state.customError = "Choose at least one table field.";
            return;
        }
        this.state.customLoading = true;
        try {
            const response = await rpc("/web/home_dashboard/widgets/custom_create", { config: draft });
            if (!response.success) {
                this.state.customError = response.error || "Could not create widget.";
                return;
            }
            this.closeCustomWidgetBuilder();
            await this.reloadWidgets();
        } catch {
            this.state.customError = "Could not create widget.";
        } finally {
            this.state.customLoading = false;
        }
    }

    // ── picker actions ───────────────────────────────────────────────────────

    async addWidget(widgetId) {
        if (!this.state.editMode) return;
        try {
            await rpc("/web/home_dashboard/widgets/add", { widget_id: widgetId });
            await this.reloadWidgets();
        } catch {
            this.notification.add("Could not add widget.", { type: "danger" });
        }
    }

    async restoreDefaultWidgets() {
        if (!this.state.editMode) return;
        try {
            await rpc("/web/home_dashboard/widgets/restore_defaults", {});
            await this.reloadWidgets();
        } catch {
            this.notification.add("Could not restore default widgets.", { type: "danger" });
        }
    }

    async removeWidget(widgetId) {
        if (!this.state.editMode) return;
        try {
            await rpc("/web/home_dashboard/widgets/remove", { widget_id: widgetId });
            await this.reloadWidgets();
        } catch {
            this.notification.add("Could not remove widget.", { type: "danger" });
        }
    }

    async resizeWidget(widgetId, colSpan) {
        if (!this.state.editMode) return;
        try {
            await rpc("/web/home_dashboard/widgets/resize", { widget_id: widgetId, col_span: String(colSpan) });
            await this.reloadWidgets();
        } catch {
            this.notification.add("Could not resize widget.", { type: "danger" });
        }
    }

    async shrinkWidget(widgetId, colSpan) {
        const nextSpan = Math.max(1, Number(colSpan) - 1);
        await this.resizeWidget(widgetId, nextSpan);
    }

    async expandWidget(widgetId, colSpan) {
        const nextSpan = Math.min(3, Number(colSpan) + 1);
        await this.resizeWidget(widgetId, nextSpan);
    }

    openWidgetSettings(widget) {
        if (!this.state.editMode) return;
        if (!widget) return;
        this.state.settingsWidget = widget;
        this.state.settingsDraft = JSON.stringify(widget.config || {}, null, 2);
        this.state.settingsError = null;
        this.state.settingsOpen = true;
    }

    updateWidgetSettingsDraft(value) {
        this.state.settingsDraft = value;
        this.state.settingsError = null;
    }

    closeWidgetSettings() {
        this.state.settingsOpen = false;
        this.state.settingsWidget = null;
        this.state.settingsDraft = "{}";
        this.state.settingsError = null;
    }

    async saveWidgetSettings() {
        if (!this.state.settingsWidget) return;
        let parsed;
        try {
            parsed = JSON.parse(this.state.settingsDraft || "{}");
        } catch {
            this.state.settingsError = "Configuration must be valid JSON.";
            return;
        }

        try {
            await rpc("/web/home_dashboard/widgets/configure", {
                widget_id: this.state.settingsWidget.widget_id,
                config: parsed,
            });
            this.closeWidgetSettings();
            await this.reloadWidgets();
        } catch {
            this.notification.add("Could not save widget settings.", { type: "danger" });
        }
    }

    // ── drag-and-drop reorder ────────────────────────────────────────────────

    onDragStart(widgetId) {
        if (!this.state.editMode) return;
        this.state.dragging = widgetId;
    }

    onDragOver(widgetId) {
        if (!this.state.editMode) return;
        if (widgetId !== this.state.dragging) {
            this.state.dragOver = widgetId;
        }
    }

    onDragEnd() {
        if (!this.state.editMode) return;
        const dragging = this.state.dragging;
        const dragOver = this.state.dragOver;
        this.state.dragging = null;
        this.state.dragOver = null;

        if (!dragging || !dragOver || dragging === dragOver) return;

        const rows = [...this.state.widgetRows];
        const fromIdx = rows.findIndex(r => r.widget_id === dragging);
        const toIdx = rows.findIndex(r => r.widget_id === dragOver);
        if (fromIdx === -1 || toIdx === -1) return;

        // Snapshot for rollback if the RPC fails.
        const originalRows = [...this.state.widgetRows];

        const [moved] = rows.splice(fromIdx, 1);
        rows.splice(toIdx, 0, moved);

        // Optimistically update UI
        this.state.widgetRows = rows.map((r, i) => ({ ...r, position: i }));

        // Persist to server; rollback on failure.
        rpc("/web/home_dashboard/widgets/reorder", {
            order: rows.map((r, i) => ({ widget_id: r.widget_id, position: i, col_span: r.col_span })),
        }).catch(() => {
            this.state.widgetRows = originalRows;
            this.notification.add("Could not save order.", { type: "warning" });
        });
    }
}

if (!registry.category("actions").contains("aura_home_dashboard")) {
  registry.category("actions").add("aura_home_dashboard", HomeDashboardClientAction);
}
