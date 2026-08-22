import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";
import { AppsLauncher } from "@methode_apps_dropdown/apps_launcher/apps_launcher";

/**
 * Move the navigation cursor one visual row up (dy = -1) or down (dy = +1).
 *
 * The Dropdown navigator (@web/core/navigation/navigation) is linear over
 * `.o-navigable` in DOM order, so its stock arrowdown/arrowup step one *tile*,
 * which in a 3-column grid reads as "move right". We resolve the target
 * geometrically instead of assuming a column count, so partial last rows and
 * section headings are handled for free.
 *
 * @param {import("@web/core/navigation/navigation").Navigator} navigator
 * @param {-1|1} dy
 */
function moveByRow(navigator, dy) {
    const items = navigator.items;
    if (!items.length) {
        return;
    }
    if (!navigator.hasActiveItem) {
        (dy > 0 ? items[0] : items.at(-1)).setActive();
        return;
    }

    const current = navigator.activeItem;
    const from = current.el.getBoundingClientRect();
    const fromX = from.left + from.width / 2;
    const fromY = from.top + from.height / 2;

    let best = null;
    let bestScore = Infinity;
    for (const item of items) {
        if (item === current) {
            continue;
        }
        const rect = item.el.getBoundingClientRect();
        const deltaY = rect.top + rect.height / 2 - fromY;
        if (dy > 0 ? deltaY <= 1 : deltaY >= -1) {
            continue; // not in the requested direction
        }
        // Row distance dominates; horizontal distance only breaks ties.
        const score = Math.abs(deltaY) * 1000 + Math.abs(rect.left + rect.width / 2 - fromX);
        if (score < bestScore) {
            bestScore = score;
            best = item;
        }
    }

    // Wrap around at the extremities.
    (best || (dy > 0 ? items[0] : items.at(-1))).setActive();
}

patch(NavBar, {
    components: { ...NavBar.components, AppsLauncher },
});

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.appsLauncher = this.env.services.methode_apps_launcher;

        // MUST be a stable object. Dropdown reads props.navigationOptions once,
        // in setup(), and hands it to useNavigation; a getter returning a fresh
        // object on every render would simply be ignored after the first one.
        //
        // Dropdown deep-merges this over the Navigator defaults, so home / end /
        // enter / tab / shift+tab / escape are all preserved key by key. We only
        // replace the four arrows and add space.
        this.appsLauncherNavigation = {
            // The Navigator defaults this to true, which makes item.target the
            // closest child input/button - here, the pin. Enter on a tile would
            // then toggle the favorite instead of opening the app, and the focus
            // ring would land on the star.
            shouldFocusChildInput: false,
            hotkeys: {
                arrowdown: {
                    callback: (navigator) => moveByRow(navigator, 1),
                    bypassEditableProtection: true,
                },
                arrowup: {
                    callback: (navigator) => moveByRow(navigator, -1),
                    bypassEditableProtection: true,
                },
                arrowright: {
                    isAvailable: () => true,
                    callback: (navigator) => navigator.next(),
                },
                arrowleft: {
                    isAvailable: () => true,
                    callback: (navigator) => navigator.previous(),
                },
                space: {
                    isAvailable: ({ navigator }) => Boolean(navigator.activeItem),
                    callback: (navigator) => {
                        const menuId = Number(navigator.activeItem?.el?.dataset?.section);
                        if (menuId) {
                            this.appsLauncher.toggleFavorite(menuId);
                        }
                    },
                },
            },
        };
    },

    // The homepage has no sub-navigation of its own, so the mobile sidebar
    // skips the "current app" section when it is the current app.
    get isHomepageApp() {
        return this.currentApp?.xmlid === 'methode_theme.menu_home_dashboard_root';
    },
});
