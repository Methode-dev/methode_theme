import { Component, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { getAppIcon } from "@methode_apps_dropdown/utils/app_icon";

export class AppsLauncher extends Component {
    static template = "methode_apps_dropdown.AppsLauncher";
    static components = { DropdownItem };
    static props = {
        apps: { type: Array }, // menuService.getApps(), in server order
        getMenuItemHref: { type: Function }, // NavBar.getMenuItemHref, bound
    };

    setup() {
        this.menuService = useService("menu");
        this.launcher = useService("methode_apps_launcher");
        // Subscribe this component to the service store directly. We do not rely
        // on the Dropdown -> popoverRefresher round trip, which only exists to
        // propagate *parent* renders into the popover's separate Owl context.
        this.favorites = useState(this.launcher.state);
    }

    /**
     * @returns {{id: string, name: string, tiles: object[]}[]}
     *
     * Ordering contract, single source of truth:
     *  - sections: Favorites first, then methode.apps.category in the order the
     *    server delivered them (sequence, id). No client-side sort.
     *  - tiles: the order of menuService.getApps(), i.e. ir.ui.menu.sequence, so
     *    an admin reorders apps in exactly one place.
     *  - favorites: the user's own pin order.
     *
     * Empty categories are dropped. Apps whose category is unknown are NOT
     * dropped -- they fall into the fallback bucket, or a trailing "Other"
     * section if the server sent no fallback. This matters right after a module
     * install, when menuService can still be serving apps from its localStorage
     * cache that the freshly-built session payload does not know about yet.
     */
    get sections() {
        const currentAppId = this.menuService.getCurrentApp()?.id;
        const favoriteIds = this.favorites.favoriteIds;
        const { categoryByMenuId, fallbackCategoryId } = this.launcher;

        const toTile = (app) => ({
            id: app.id,
            name: app.name,
            xmlid: app.xmlid,
            href: this.props.getMenuItemHref(app),
            icon: getAppIcon(app),
            isCurrent: app.id === currentAppId,
            isFavorite: favoriteIds.includes(app.id),
            menu: app,
        });

        const appById = new Map(this.props.apps.map((app) => [app.id, app]));
        const appsByCategory = new Map();
        for (const app of this.props.apps) {
            const categoryId = categoryByMenuId.get(app.id) ?? fallbackCategoryId ?? null;
            if (!appsByCategory.has(categoryId)) {
                appsByCategory.set(categoryId, []);
            }
            appsByCategory.get(categoryId).push(app);
        }

        const sections = [];

        const favoriteApps = favoriteIds.map((id) => appById.get(id)).filter(Boolean);
        if (favoriteApps.length) {
            sections.push({
                id: "favorites",
                name: _t("Favorites"),
                tiles: favoriteApps.map(toTile),
            });
        }

        for (const category of this.launcher.categories) {
            const apps = appsByCategory.get(category.id);
            if (apps?.length) {
                sections.push({
                    id: `category-${category.id}`,
                    name: category.name,
                    tiles: apps.map(toTile),
                });
            }
        }

        // Only reachable when the server sent no fallback category, or when it
        // sent one that is not in `categories`.
        const orphans = appsByCategory.get(null) || [];
        if (fallbackCategoryId && !this.launcher.categories.some((c) => c.id === fallbackCategoryId)) {
            orphans.push(...(appsByCategory.get(fallbackCategoryId) || []));
        }
        if (orphans.length) {
            sections.push({ id: "other", name: _t("Other"), tiles: orphans.map(toTile) });
        }

        return sections;
    }

    onAppSelected(tile) {
        this.menuService.selectMenu(tile.menu);
    }

    toggleFavorite(tile) {
        this.launcher.toggleFavorite(tile.id);
    }

    pinTitle(tile) {
        return tile.isFavorite ? _t("Remove from favorites") : _t("Add to favorites");
    }

    /**
     * The pin is aria-hidden (a focusable control inside role="menuitem" is an
     * ARIA violation), so the pinned state is surfaced here instead.
     */
    tileAriaLabel(tile) {
        return tile.isFavorite ? _t("%s (favorite)", tile.name) : tile.name;
    }
}
