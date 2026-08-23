/**
 * Normalise an app entry from `menuService.getApps()` into something renderable.
 *
 * Mirrors the two ends of the existing contract:
 *  - odoo/addons/web/models/ir_ui_menu.py::load_web_menus (producer)
 *  - web/static/src/webclient/menus/menu_providers.js (the apps command provider,
 *    which does exactly this normalisation for `web.AppIconCommand`)
 *
 * Two mutually exclusive cases, per load_web_menus:
 *  - webIconData set   -> a "data:<mime>;base64,..." URI, or the literal fallback
 *                         "/web/static/img/default_icon_app.png"
 *  - webIconData falsy -> webIcon is "iconClass,color,backgroundColor" (3 parts),
 *                         i.e. a font-awesome tile
 *
 * @param {object} app an entry of menuService.getApps()
 * @returns {{src: string}|{iconClass: string, color: string, backgroundColor: string}}
 */
export function getAppIcon(app) {
    if (app.webIconData) {
        const data = app.webIconData;
        if (data.startsWith("data:image") || data.startsWith("/")) {
            return { src: data };
        }
        // Defensive: a bare base64 payload. load_web_menus already prefixes the
        // URI, but menu_providers.js keeps this branch, so we stay byte-for-byte
        // compatible with it.
        const prefix = data.startsWith("P")
            ? "data:image/svg+xml;base64,"
            : "data:image/png;base64,";
        return { src: prefix + data.replace(/\s/g, "") };
    }

    const [iconClass, color, backgroundColor] = (app.webIcon || "").split(",");
    if (backgroundColor !== undefined) {
        return { iconClass, color, backgroundColor };
    }
    return { src: "/web/static/img/default_icon_app.png" };
}
