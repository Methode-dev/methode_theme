/** @odoo-module **/

/**
 * Phase 2 — App-specific widgets.
 * Each widget registers itself into homeWidgetRegistry.
 * The registry entry shape:
 *   { component, getProps(dashboardData, widgetData, callbacks), useWidgetData: true }
 *
 * widgetData is the `data` key returned by the server-side fetcher for that widget.
 */

import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { homeWidgetRegistry, openDashboardTarget } from "./home_dashboard";

function registerHomeWidget(key, spec) {
    if (!homeWidgetRegistry.contains(key)) {
        homeWidgetRegistry.add(key, spec);
    }
}

// ── shared helper ─────────────────────────────────────────────────────────────

function fmt(amount, symbol = "") {
    if (amount == null) return "—";
    const n = amount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    return symbol ? `${symbol} ${n}` : n;
}

// ── Base widget mixin ─────────────────────────────────────────────────────────
// Returns a Component subclass with shared navigate() and fmt() methods.
// Using a mixin avoids creating a bare Component that has no template.

const AppWidget = (Base) => class extends Base {
    setup() {
        if (super.setup) {
            super.setup(...arguments);
        }
        this.actionService = useService("action");
    }

    navigate(target) { openDashboardTarget(this.actionService, target); }
    fmt(amount, symbol) { return fmt(amount, symbol); }
};

// ── InventoryReorderWidget ────────────────────────────────────────────────────

class InventoryReorderWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.InventoryReorderWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    stockClass(qtyOnHand) {
        if (qtyOnHand <= 0) return "aw-stock aw-stock--empty";
        return "aw-stock aw-stock--low";
    }
}

registerHomeWidget("inventory_reorder", {
    component: InventoryReorderWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── InventoryReceiptsWidget ───────────────────────────────────────────────────

class InventoryReceiptsWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.InventoryReceiptsWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    lateClass(daysLate) {
        return daysLate > 0 ? "hd-badge hd-badge-overdue" : "hd-badge hd-badge-soon";
    }
}

registerHomeWidget("inventory_receipts", {
    component: InventoryReceiptsWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── PurchaseRFQWidget ─────────────────────────────────────────────────────────

class PurchaseRFQWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.PurchaseRFQWidget";
    static props = ["items", "count", "viewAction", "createAction"];
}

registerHomeWidget("purchase_rfq", {
    component: PurchaseRFQWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── PurchaseOrdersWidget ──────────────────────────────────────────────────────

class PurchaseOrdersWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.PurchaseOrdersWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    invoiceClass(status) {
        return status === "to invoice" ? "hd-badge hd-badge-today" : "hd-badge hd-badge-draft";
    }

    invoiceLabel(status) {
        return { "to invoice": "To Invoice", "invoiced": "Invoiced", "nothing_to_bill": "Nothing to bill" }[status] || status;
    }
}

registerHomeWidget("purchase_orders", {
    component: PurchaseOrdersWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── SaleQuotationsWidget ──────────────────────────────────────────────────────

class SaleQuotationsWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.SaleQuotationsWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    stateClass(state) {
        return state === "sent" ? "hd-badge hd-badge-today" : "hd-badge hd-badge-draft";
    }
}

registerHomeWidget("sale_quotations", {
    component: SaleQuotationsWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── SaleToInvoiceWidget ───────────────────────────────────────────────────────

class SaleToInvoiceWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.SaleToInvoiceWidget";
    static props = ["items", "count", "viewAction", "createAction"];
}

registerHomeWidget("sale_to_invoice", {
    component: SaleToInvoiceWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── HRLeavesWidget ───────────────────────────────────────────────────────────

class HRLeavesWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.HRLeavesWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    dateRange(item) {
        if (!item.date_from && !item.date_to) return "";
        if (!item.date_to || item.date_from === item.date_to) return item.date_from || item.date_to || "";
        return `${item.date_from} → ${item.date_to}`;
    }
}

registerHomeWidget("hr_leaves", {
    component: HRLeavesWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── HRAttendanceWidget ──────────────────────────────────────────────────────

class HRAttendanceWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.HRAttendanceWidget";
    static props = ["items", "count", "viewAction", "createAction"];
}

registerHomeWidget("hr_attendance", {
    component: HRAttendanceWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── ProjectTasksWidget ───────────────────────────────────────────────────────

class ProjectTasksWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.ProjectTasksWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    priorityClass(priority) {
        return { "3": "hd-badge hd-badge-overdue", "2": "hd-badge hd-badge-today", "1": "hd-badge hd-badge-soon" }[priority] || "hd-badge";
    }
}

registerHomeWidget("project_tasks", {
    component: ProjectTasksWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── ProjectDeadlinesWidget ──────────────────────────────────────────────────

class ProjectDeadlinesWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.ProjectDeadlinesWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    deadlineClass(daysLeft) {
        if (daysLeft <= 1) return "hd-badge hd-badge-overdue";
        if (daysLeft <= 3) return "hd-badge hd-badge-today";
        return "hd-badge hd-badge-soon";
    }
}

registerHomeWidget("project_deadlines", {
    component: ProjectDeadlinesWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── MRPProductionWidget ─────────────────────────────────────────────────────

class MRPProductionWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.MRPProductionWidget";
    static props = ["items", "count", "viewAction", "createAction"];

    stateClass(state) {
        return { confirmed: "hd-badge hd-badge-today", progress: "hd-badge hd-badge-soon" }[state] || "hd-badge";
    }
}

registerHomeWidget("mrp_production", {
    component: MRPProductionWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
    }),
});

// ── AccountAgedReceivablesWidget ────────────────────────────────────────────

class AccountAgedReceivablesWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.AccountAgedReceivablesWidget";
    static props = ["buckets", "items", "count", "currencySymbol", "viewAction", "createAction"];

    bucketClass(key) {
        return {
            "0_30": "aw-icon-green",
            "31_60": "aw-icon-blue",
            "61_90": "aw-icon-orange",
            "90_plus": "aw-icon-red",
        }[key] || "aw-icon-gray";
    }
}

registerHomeWidget("account_aged_recv", {
    component: AccountAgedReceivablesWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        buckets: widgetData?.buckets || [],
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
        currencySymbol: widgetData?.currency_symbol || "",
    }),
});

// ── AccountCashflowWidget ───────────────────────────────────────────────────

class AccountCashflowWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.AccountCashflowWidget";
    static props = ["bankBalance", "expectedIn", "expectedOut", "net", "items", "count", "currencySymbol", "viewAction", "createAction"];

    directionClass(direction) {
        return direction === "in" ? "hd-badge hd-badge-soon" : "hd-badge hd-badge-overdue";
    }
}

registerHomeWidget("account_cashflow", {
    component: AccountCashflowWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        bankBalance: widgetData?.bank_balance || 0,
        expectedIn: widgetData?.expected_in || 0,
        expectedOut: widgetData?.expected_out || 0,
        net: widgetData?.net || 0,
        items: widgetData?.items || [],
        count: widgetData?.count || 0,
        currencySymbol: widgetData?.currency_symbol || "",
    }),
});

// ── ActivityTrendWidget ──────────────────────────────────────────────────────

class ActivityTrendWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.ActivityTrendWidget";
    static props = ["points", "total", "viewAction"];

    barHeight(value) {
        const max = Math.max(...(this.props.points || []).map((p) => p.value || 0), 1);
        return `${Math.max(12, Math.round(((value || 0) / max) * 100))}%`;
    }

    pointClass(color) {
        return `aw-chart-bar aw-chart-bar--${color || "gray"}`;
    }
}

registerHomeWidget("activity_trend", {
    component: ActivityTrendWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        points: widgetData?.points || [],
        total: widgetData?.total || 0,
    }),
});

// ── SalesTrendWidget ─────────────────────────────────────────────────────────

class SalesTrendWidget extends AppWidget(Component) {
    static template = "aura_backend_theme.SalesTrendWidget";
    static props = ["points", "totalAmount", "currencySymbol", "viewAction", "createAction"];

    barHeight(amount) {
        const max = Math.max(...(this.props.points || []).map((p) => p.amount || 0), 1);
        return `${Math.max(12, Math.round(((amount || 0) / max) * 100))}%`;
    }
}

registerHomeWidget("sales_trend", {
    component: SalesTrendWidget,
    useWidgetData: true,
    getProps: (_, widgetData) => ({
        points: widgetData?.points || [],
        totalAmount: widgetData?.total_amount || 0,
        currencySymbol: widgetData?.currency_symbol || "",
    }),
});
