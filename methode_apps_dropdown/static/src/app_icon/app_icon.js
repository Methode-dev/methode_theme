import { Component } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { APP_GLYPHS, APP_GLYPH_BY_MODULE, APP_GLYPH_BY_XMLID } from "./app_glyphs";

/**
 * Resolve an app to its glyph.
 *
 * Two lookups, most specific first: the root menu's full xmlid (for the menus
 * `base` declares, which the module key alone cannot tell apart), then the
 * module that declares it.
 *
 * @param {object} app an entry of menuService.getApps() (needs `xmlid`)
 * @returns {string[]|null} path `d` attributes, or null when the set has no
 *      drawing for this app - the caller falls back to a monogram.
 */
export function getAppGlyph(app) {
    const xmlid = app?.xmlid || "";
    const key = APP_GLYPH_BY_XMLID[xmlid] || APP_GLYPH_BY_MODULE[xmlid.split(".", 1)[0]];
    return (key && APP_GLYPHS[key]) || null;
}

/**
 * First character of the app name, for the no-glyph fallback.
 *
 * Spread rather than `name[0]`: an emoji or an accented composed character is
 * more than one UTF-16 code unit, and slicing one in half renders a tofu box.
 * Not upper-cased - a customer who named their app "iOS Sync" gets "i", which
 * is what they wrote.
 *
 * @param {object} app
 * @returns {string}
 */
export function getAppMonogram(app) {
    return [...(app?.name || "").trim()][0] || "?";
}

/**
 * One app icon: a tinted, ink-outlined chip with a stroke glyph in it.
 *
 * Deliberately NOT the app's own `webIconData` PNG - see the long note at the
 * top of app_glyphs.js for why the launcher draws its own set.
 *
 * The chip's fill is not set here. The component only exposes the app's launcher
 * category as `data-app-category`, and app_icon.scss maps codes to the brand
 * tints, so the palette stays in SCSS next to the rest of the theme's colour
 * decisions and a customer can retint the launcher with CSS alone.
 *
 * Size is contextual too (44px in the desktop grid, 34px in the mobile sidebar):
 * the caller sets --AppIcon-size on any ancestor rather than passing a prop, so
 * one component serves both without growing a variant API.
 */
export class AppIcon extends Component {
    static template = "methode_apps_dropdown.AppIcon";
    static props = {
        app: { type: Object }, // an entry of menuService.getApps()
    };

    setup() {
        this.launcher = useService("methode_apps_launcher");
    }

    get paths() {
        return getAppGlyph(this.props.app) || [];
    }

    get monogram() {
        return getAppMonogram(this.props.app);
    }

    /**
     * The launcher category CODE, not its id: codes are the stable technical key
     * (see methode.apps.category.code) and are what the stylesheet keys on.
     */
    get categoryCode() {
        return this.launcher.categoryCodeOf(this.props.app.id);
    }
}
