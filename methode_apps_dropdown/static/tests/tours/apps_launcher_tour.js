import { registry } from "@web/core/registry";

/**
 * End-to-end check of the launcher: it is the only layer that exercises the real
 * pipeline (methode.apps.category records -> session_info -> grouping -> pin ->
 * set_res_users_settings write -> reload -> favorite still pinned).
 *
 * Driven by tests/test_apps_launcher_tour.py.
 */
registry.category("web_tour.tours").add("methode_apps_launcher_tour", {
    url: "/odoo",
    steps: () => [
        {
            content: "Open the apps launcher",
            trigger: ".o_navbar_apps_menu button[data-hotkey=h]",
            run: "click",
        },
        {
            content: "The tiled panel is rendered",
            trigger: ".o_mad_panel",
        },
        {
            content: "Apps are grouped under at least one category heading",
            trigger: ".o_mad_section_title",
        },
        {
            content: "Tiles keep data-menu-xmlid, which other tours rely on",
            trigger: ".o_mad_grid .o_mad_tile[data-menu-xmlid='mail.menu_root_discuss']",
        },
        {
            content: "Tiles keep a real href",
            trigger: ".o_mad_tile[data-menu-xmlid='mail.menu_root_discuss'][href^='/odoo/']",
        },
        {
            content: "Pin Discuss. The click must not navigate nor close the dropdown.",
            trigger: ".o_mad_tile[data-menu-xmlid='mail.menu_root_discuss'] .o_mad_pin",
            run: "click",
        },
        {
            content: "A Favorites section appears, with Discuss in it",
            trigger:
                ".o_mad_section:first-child .o_mad_tile[data-menu-xmlid='mail.menu_root_discuss']",
        },
        {
            content: "The dropdown is still open and Discuss is still in its category too",
            trigger: ".o_mad_panel .o_mad_section:nth-child(2) .o_mad_tile",
        },
        {
            content: "Clicking a tile opens the app",
            trigger: ".o_mad_tile[data-menu-xmlid='mail.menu_root_discuss']",
            run: "click",
        },
        {
            content: "Discuss opened and the launcher closed",
            trigger: ".o_menu_brand:contains(Discuss)",
        },
        {
            trigger: "body:not(:has(.o_mad_panel))",
        },
    ],
});

/**
 * Second tour, run after a reload, asserting the pin survived the round trip
 * through res.users.settings.
 */
registry.category("web_tour.tours").add("methode_apps_launcher_favorite_persisted_tour", {
    url: "/odoo",
    steps: () => [
        {
            content: "Re-open the launcher after a full reload",
            trigger: ".o_navbar_apps_menu button[data-hotkey=h]",
            run: "click",
        },
        {
            content: "Discuss is still pinned in the Favorites section",
            trigger:
                ".o_mad_section:first-child .o_mad_tile[data-menu-xmlid='mail.menu_root_discuss'] .fa-star",
        },
    ],
});
