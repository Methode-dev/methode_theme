/**
 * The launcher icon set: one drawing language for every app.
 * ============================================================================
 *
 * WHY THIS EXISTS
 * ---------------
 * Odoo ships every app's icon as a PNG on its root menu (`webIconData`), drawn
 * by whoever wrote the module. Put thirty of them in one grid and you get thirty
 * illustration styles at once - flat, gradient, drop-shadowed, 3D-ish, some with
 * their own baked-in background, some transparent. The launcher was the only
 * place in the backend showing them all side by side, so it was also the only
 * place where that inconsistency was impossible to miss.
 *
 * So the launcher stops rendering `webIconData` and draws the app itself:
 *
 *   GLYPH  one 24x24 grid, stroke-only, 1.75 stroke, round caps and joins, ink
 *          coloured. No fills, no gradients, no per-icon colour - the SHAPE is
 *          the identity.
 *   CHIP   a rounded square with the brand's 1px ink outline and a flat tint
 *          fill. The tint comes from the app's launcher CATEGORY, not from the
 *          app, so a section reads as one colour block and the colour means
 *          something (see CATEGORY_FILL in app_icon.js).
 *
 * That is where "colourful but unified" is resolved: colour is systematic and
 * carries the taxonomy, the drawing is uniform, and both come out of the brand
 * palette rather than from thirty unrelated PNGs.
 *
 * ⚠ Do NOT reintroduce per-glyph colour. The moment one icon paints its own
 * shape, every other icon has to be re-checked against it and the set stops
 * being a set.
 *
 * DRAWING RULES (follow these when adding a glyph)
 * ------------------------------------------------
 *  - 24x24 viewBox, live area ~3..21. Nothing touches the edge.
 *  - Stroke only. `fill="none"` is set on the <svg>; never set `fill` on a path.
 *  - One visual weight: rely on the shared stroke-width, never fake a heavier
 *    line by doubling paths.
 *  - A dot is `M<x> <y>h.01` - a zero-length segment rendered by the round cap.
 *    (Same trick the Lucide/Feather sets use; it keeps every mark stroke-based.)
 *  - Circles are written as two arcs so a glyph stays a flat list of <path d>.
 *  - Keep each glyph under ~6 paths. These render at 26-44px; detail beyond that
 *    turns into mush, and mush is what makes an icon set look amateur.
 *
 * Drawn by hand on the grid, in the idiom of the Lucide set that
 * aura_backend_theme already vendors (static/src/img/*.svg) - so the two agree
 * if a customer ever runs that theme's navbar instead of this launcher.
 */

/**
 * Glyph key -> the `d` attribute of each path, in paint order.
 *
 * Keys are semantic ("box", "receipt"), never app names: several apps share a
 * drawing, and an app can be re-pointed at a different glyph without renaming
 * anything. APP_GLYPH_BY_MODULE below is the only place apps are named.
 *
 * @type {Object<string, string[]>}
 */
export const APP_GLYPHS = {
    // --- structure / places ------------------------------------------------
    home: [
        "M3 10.75 12 3.5l9 7.25",
        "M5.5 9.75V20.5h13V9.75",
        "M9.75 20.5v-5.25h4.5v5.25",
    ],
    grid: ["M4 4.5h6v6H4Z", "M14 4.5h6v6h-6Z", "M4 14.5h6v6H4Z", "M14 14.5h6v6h-6Z"],
    dashboard: ["M3.5 3.5h7v7h-7Z", "M13.5 3.5h7v4.5h-7Z", "M13.5 11h7v9.5h-7Z", "M3.5 13h7v7.5h-7Z"],
    globe: [
        "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
        "M3.2 12h17.6",
        "M12 3a13.5 13.5 0 0 1 0 18 13.5 13.5 0 0 1 0-18Z",
    ],
    pin: [
        "M19 10.5c0 5.2-7 11-7 11s-7-5.8-7-11a7 7 0 1 1 14 0Z",
        "M14.5 10.5a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0Z",
    ],

    // --- money / trade -----------------------------------------------------
    trend: ["M3.5 16.5 9.5 10.5l4 4 7-7", "M15.5 7.5H21V13"],
    receipt: [
        "M6.5 3.5h11v17l-2.75-1.6L12 20.5l-2.75-1.6L6.5 20.5Z",
        "M9.5 8.5h5",
        "M9.5 12.5h5",
    ],
    cart: [
        "M3 4.5h2.2l2.4 10.5h9.3l2-7.5H6.3",
        "M10.9 18.8a1.4 1.4 0 1 1-2.8 0 1.4 1.4 0 0 1 2.8 0Z",
        "M17.9 18.8a1.4 1.4 0 1 1-2.8 0 1.4 1.4 0 0 1 2.8 0Z",
    ],
    bag: ["M5.5 7.5h13l1 13h-15Z", "M8.5 10.5V7a3.5 3.5 0 0 1 7 0v3.5"],
    banknote: [
        "M2.5 6.5h19v11h-19Z",
        "M14.5 12a2.5 2.5 0 1 1-5 0 2.5 2.5 0 0 1 5 0Z",
        "M6 10v4",
        "M18 10v4",
    ],
    wallet: [
        "M4 6.5h13.5a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a1 1 0 0 1-1-1v-11a1 1 0 0 1 1-1Z",
        "M15.5 11.5h4v5h-4a2.5 2.5 0 0 1 0-5Z",
        "M16.6 14h.01",
    ],
    monitor: ["M3.5 5h17v10.5h-17Z", "M12 15.5V19", "M8.5 19h7"],
    gift: [
        "M4 11.5h16v9H4Z",
        "M3 7.5h18v4H3Z",
        "M12 7.5v13",
        "M12 7.5C10.4 7.5 7 7.3 7 5.4A2.2 2.2 0 0 1 12 5.4a2.2 2.2 0 0 1 5 0c0 1.9-3.4 2.1-5 2.1Z",
    ],
    repeat: ["m17 2.5 3.5 3.5L17 9.5", "M3.5 11.5v-1.5a4 4 0 0 1 4-4h13", "m7 21.5-3.5-3.5L7 14.5", "M20.5 12.5v1.5a4 4 0 0 1-4 4h-13"],
    target: [
        "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
        "M16.5 12a4.5 4.5 0 1 1-9 0 4.5 4.5 0 0 1 9 0Z",
        "M12 12h.01",
    ],

    // --- logistics / production -------------------------------------------
    box: ["M12 3.2 3.5 7.6v8.8L12 20.8l8.5-4.4V7.6Z", "M3.5 7.6 12 12l8.5-4.4", "M12 12v8.8"],
    truck: [
        "M2.5 6h10.5v11H2.5Z",
        "M13 10h3.9l2.6 3.1V17H13",
        "M8.6 18.5a1.6 1.6 0 1 1-3.2 0 1.6 1.6 0 0 1 3.2 0Z",
        "M18.6 18.5a1.6 1.6 0 1 1-3.2 0 1.6 1.6 0 0 1 3.2 0Z",
    ],
    factory: [
        "M2.5 20.5v-9.2l5.5 3.4v-3.4l5.5 3.4V6.5h5.5l1 14Z",
        "M6 17.5h.01",
        "M11.5 17.5h.01",
        "M17 17.5h.01",
    ],
    wrench: [
        "M20.5 4.6 17 8.1a1.2 1.2 0 0 1-1.7 0l-1.4-1.4a1.2 1.2 0 0 1 0-1.7l3.5-3.5a6 6 0 0 0-7.7 7.7l-6.4 6.4a2.1 2.1 0 0 0 3 3l6.4-6.4a6 6 0 0 0 7.8-7.6Z",
    ],
    // A hammer was tried here and dropped: at 44px a head-on-a-shaft is a
    // pushpin, and `pin` is two rows away in the same panel. A toolbox has an
    // outline nothing else in the set shares.
    toolbox: [
        "M3.5 9.5h17v9a1.5 1.5 0 0 1-1.5 1.5H5a1.5 1.5 0 0 1-1.5-1.5Z",
        "M9 9.5V7a1.5 1.5 0 0 1 1.5-1.5h3A1.5 1.5 0 0 1 15 7v2.5",
        "M3.5 13.8h17",
        "M12 12.3v3",
    ],
    shieldCheck: [
        "M12 3.2 4.8 6v6.1c0 4.3 3 7.5 7.2 8.7 4.2-1.2 7.2-4.4 7.2-8.7V6Z",
        "m8.9 12 2.3 2.3 4.2-4.4",
    ],
    barcode: ["M4 6.5v11", "M7.5 6.5v11", "M11 6.5v11", "M14.5 6.5v11", "M17.5 6.5v11", "M20 6.5v11"],
    cpu: [
        "M7 7h10v10H7Z",
        "M4.5 9.5H7M4.5 14.5H7M17 9.5h2.5M17 14.5h2.5",
        "M9.5 4.5V7M14.5 4.5V7M9.5 17v2.5M14.5 17v2.5",
    ],

    // --- work / planning ---------------------------------------------------
    board: ["M3.5 4.5h17v15h-17Z", "M7.5 8.5v7", "M12 8.5v4.5", "M16.5 8.5v5.5"],
    gantt: ["M3.5 4.6v14.8", "M6.5 8.4h7.5", "M9.5 12.4h9", "M7 16.4h5.5"],
    clock: ["M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z", "M12 6.8V12.4l3.4 2"],
    calendar: ["M4.5 5.5h15v14h-15Z", "M4.5 10h15", "M8.5 3.5v4", "M15.5 3.5v4"],
    calendarCheck: [
        "M4.5 5.5h15v14h-15Z",
        "M4.5 10h15",
        "M8.5 3.5v4",
        "M15.5 3.5v4",
        "m9 14.8 2 2 4-4",
    ],
    checklist: ["M4 6.5h4.5V11H4Z", "m4.6 16.4 1.8 1.8 3.4-3.4", "M12 8.5h8", "M13 17h7"],
    clipboard: [
        "M9 4.5H7.4a1.9 1.9 0 0 0-1.9 1.9v12.2a1.9 1.9 0 0 0 1.9 1.9h9.2a1.9 1.9 0 0 0 1.9-1.9V6.4A1.9 1.9 0 0 0 16.6 4.5H15",
        "M9 3.2h6v3H9Z",
        "M9 11h6",
        "M9 15h6",
    ],
    buoy: [
        "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z",
        "M15.5 12a3.5 3.5 0 1 1-7 0 3.5 3.5 0 0 1 7 0Z",
        "m5.6 5.6 3.4 3.4",
        "m15 15 3.4 3.4",
        "m18.4 5.6-3.4 3.4",
        "m9 15-3.4 3.4",
    ],
    chart: ["M3.5 20.5h17", "M6.5 20.5v-6", "M11.5 20.5V7.5", "M16.5 20.5v-9"],

    // --- people ------------------------------------------------------------
    users: [
        "M15.5 20.5v-1.9a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1.9",
        "M12.6 7.4a3.35 3.35 0 1 1-6.7 0 3.35 3.35 0 0 1 6.7 0Z",
        "M21 20.5v-1.9a4 4 0 0 0-3-3.9",
        "M16.4 4.2a4 4 0 0 1 0 6.3",
    ],
    userPlus: [
        "M14 20.5v-1.9a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v1.9",
        "M11.4 7.4a3.35 3.35 0 1 1-6.7 0 3.35 3.35 0 0 1 6.7 0Z",
        "M19 7.5v6",
        "M22 10.5h-6",
    ],
    userCheck: [
        "M14 20.5v-1.9a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v1.9",
        "M11.4 7.4a3.35 3.35 0 1 1-6.7 0 3.35 3.35 0 0 1 6.7 0Z",
        "m16 10.5 2 2 4-4",
    ],
    contactCard: [
        "M6.5 3.5h11a1.5 1.5 0 0 1 1.5 1.5v14a1.5 1.5 0 0 1-1.5 1.5h-11Z",
        "M6.5 7.5H4M6.5 12H4M6.5 16.5H4",
        "M14.9 10.4a2.2 2.2 0 1 1-4.4 0 2.2 2.2 0 0 1 4.4 0Z",
        "M16 16.5a3.3 3.3 0 0 0-6.6 0",
    ],
    umbrella: [
        "M12 3.4a8.6 8.6 0 0 1 8.6 8.6H3.4A8.6 8.6 0 0 1 12 3.4Z",
        "M12 12v5.9a2.6 2.6 0 0 0 5.2 0",
    ],
    award: [
        "M17 9.2a5 5 0 1 1-10 0 5 5 0 0 1 10 0Z",
        "m8.7 13.4-1.3 7.1 4.6-2.6 4.6 2.6-1.3-7.1",
    ],
    car: [
        "m6.6 12.2 1.6-3.7a1.8 1.8 0 0 1 1.7-1.1h4.2a1.8 1.8 0 0 1 1.7 1.1l1.6 3.7",
        "M3.4 16.6V14a1.8 1.8 0 0 1 1.8-1.8h13.6A1.8 1.8 0 0 1 20.6 14v2.6Z",
        "M9 17.4a1.6 1.6 0 1 1-3.2 0 1.6 1.6 0 0 1 3.2 0Z",
        "M19.8 17.4a1.6 1.6 0 1 1-3.2 0 1.6 1.6 0 0 1 3.2 0Z",
    ],
    utensils: [
        "M6.5 3.5v6a2.5 2.5 0 0 0 5 0v-6",
        "M9 9.5v11",
        "M17.5 3.5c-1.6 1.1-2.4 2.9-2.4 4.9 0 1.8.8 3 2.4 3.5v8.6",
    ],

    // --- communication / content -------------------------------------------
    chat: ["M4 6.4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v7.7a2 2 0 0 1-2 2H9l-5 4Z"],
    chatCircle: ["M20.5 11.6a8 8 0 0 1-11.7 7.1L3.5 20.5l1.9-5.2A8 8 0 1 1 20.5 11.6Z"],
    mail: ["M3.5 6h17v12h-17Z", "m3.5 7 8.5 6 8.5-6"],
    megaphone: ["m3.5 10.5 17-5.5v14l-17-5.5Z", "M3.5 10.5v3", "M11.4 16.9a3 3 0 1 1-5.7-1.6"],
    share: [
        "M20.5 5.5a2.9 2.9 0 1 1-5.8 0 2.9 2.9 0 0 1 5.8 0Z",
        "M8.9 12a2.9 2.9 0 1 1-5.8 0 2.9 2.9 0 0 1 5.8 0Z",
        "M20.5 18.5a2.9 2.9 0 1 1-5.8 0 2.9 2.9 0 0 1 5.8 0Z",
        "m8.6 13.4 6.5 3.8",
        "m15.1 6.8-6.5 3.8",
    ],
    ticket: [
        "M3.5 8.6V7a1.1 1.1 0 0 1 1.1-1.1h14.8A1.1 1.1 0 0 1 20.5 7v1.6a2.6 2.6 0 0 0 0 6.8V17a1.1 1.1 0 0 1-1.1 1.1H4.6A1.1 1.1 0 0 1 3.5 17v-1.6a2.6 2.6 0 0 0 0-6.8Z",
        "M14 6.5v2M14 11v2M14 15.5v2",
    ],
    book: [
        "M12 7.6C12 6 9.8 4.6 6.6 4.6H3.5v11.9H7c2.8 0 5 1.2 5 2.6",
        "M12 7.6c0-1.6 2.2-3 5.4-3h3.1v11.9H17c-2.8 0-5 1.2-5 2.6",
        "M12 7.6v11.5",
    ],
    cap: [
        "m12 4 9.5 4.4L12 12.8 2.5 8.4Z",
        "M6.6 10.6v5.1c0 1.5 2.4 2.7 5.4 2.7s5.4-1.2 5.4-2.7v-5.1",
    ],
    folder: ["M3.5 6.6a1.1 1.1 0 0 1 1.1-1.1h4.3l2 2.6h8.5a1.1 1.1 0 0 1 1.1 1.1v9.3a1.1 1.1 0 0 1-1.1 1.1H4.6a1.1 1.1 0 0 1-1.1-1.1Z"],
    pen: ["m15.6 3.9 4.5 4.5-9.9 9.9-6 1.5 1.5-6Z", "m13.4 6.1 4.5 4.5", "M4.2 21.5h15.6"],
    gear: [
        "M19 12a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z",
        "M14.7 12a2.7 2.7 0 1 1-5.4 0 2.7 2.7 0 0 1 5.4 0Z",
        "M12 3.1v1.9M12 19v1.9M3.1 12h1.9M19 12h1.9",
        "m5.7 5.7 1.35 1.35M16.95 16.95l1.35 1.35M18.3 5.7l-1.35 1.35M7.05 16.95 5.7 18.3",
    ],
    sliders: ["M4 7h16", "M4 12h16", "M4 17h16", "M9 4.6v4.8", "M15.5 9.6v4.8", "M7.5 14.6v4.8"],
};

/**
 * Odoo module -> glyph key.
 *
 * Keyed on the MODULE of the root menu's xmlid (`sale.sale_menu_root` -> `sale`),
 * not on the xmlid itself: a root menu gets renamed or re-parented across
 * versions far more often than the module that declares it does, and one entry
 * then covers every menu that module owns.
 *
 * An unlisted app is NOT an error - it falls back to a monogram chip in the same
 * frame, which is why installing a module the set has never heard of still looks
 * deliberate. Add a line here (and a glyph above) to promote one.
 *
 * @type {Object<string, keyof APP_GLYPHS>}
 */
export const APP_GLYPH_BY_MODULE = {
    // Méthode
    methode_theme: "home",

    // Sales & Finance
    sale: "trend",
    sale_management: "trend",
    sale_subscription: "repeat",
    crm: "target",
    account: "receipt",
    account_accountant: "receipt",
    om_account_accountant: "receipt",
    accounting_pdf_reports: "chart",
    purchase: "cart",
    point_of_sale: "monitor",
    pos_restaurant: "utensils",
    delivery: "truck",
    stock_delivery: "truck",
    loyalty: "gift",
    website_sale: "bag",
    sales_team: "trend",

    // Operations
    stock: "box",
    stock_barcode: "barcode",
    barcodes: "barcode",
    mrp: "factory",
    mrp_workorder: "factory",
    maintenance: "wrench",
    repair: "toolbox",
    quality: "shieldCheck",
    quality_control: "shieldCheck",
    project: "board",
    project_todo: "checklist",
    hr_timesheet: "clock",
    timesheet_grid: "clock",
    planning: "gantt",
    helpdesk: "buoy",
    industry_fsm: "pin",
    field_service: "pin",
    appointment: "calendarCheck",

    // Human Resources
    hr: "users",
    hr_holidays: "umbrella",
    hr_expense: "wallet",
    hr_recruitment: "userPlus",
    hr_attendance: "userCheck",
    hr_appraisal: "award",
    hr_referral: "megaphone",
    hr_payroll: "banknote",
    om_hr_payroll: "banknote",
    fleet: "car",
    lunch: "utensils",

    // Marketing & Website
    website: "globe",
    mass_mailing: "mail",
    marketing_automation: "share",
    social: "megaphone",
    survey: "clipboard",
    event: "ticket",
    im_livechat: "chatCircle",
    website_slides: "cap",

    // Productivity
    mail: "chat",
    calendar: "calendar",
    contacts: "contactCard",
    note: "checklist",
    knowledge: "book",
    documents: "folder",
    dms: "folder",
    document_configuration_methode: "folder",
    sign: "pen",
    sign_oca: "pen",
    spreadsheet_dashboard: "dashboard",
    board: "dashboard",
    iot: "cpu",

    // Administration
    base: "gear",
    base_setup: "sliders",
    queue_job: "sliders",
};

/**
 * Root-menu xmlid -> glyph key, for the handful of menus their own module cannot
 * describe. `base` declares both Settings and Apps, so the module key alone
 * cannot tell them apart; these win over APP_GLYPH_BY_MODULE.
 *
 * @type {Object<string, keyof APP_GLYPHS>}
 */
export const APP_GLYPH_BY_XMLID = {
    "base.menu_administration": "gear",
    "base.menu_management": "grid",
};
