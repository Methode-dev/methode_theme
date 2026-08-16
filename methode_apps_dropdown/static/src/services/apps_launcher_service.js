import { reactive } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { session } from "@web/session";
import { user } from "@web/core/user";

export const FAVORITES_KEY = "methode_apps_favorite_menu_ids";

/**
 * Holds the launcher taxonomy and the user's pinned apps.
 *
 * This is a service and not component state because `DropdownPopover` is created
 * on open and destroyed on close, so `AppsLauncher` is a brand new instance every
 * single time the menu opens. Favorites have to outlive it.
 */
export const appsLauncherService = {
    dependencies: ["menu"],
    start() {
        // Read `session` inside start(), never at module scope, so tests can
        // patchWithCleanup(session, ...) before the env is made.
        const payload = session.methode_apps_dropdown || {};

        // JSON object keys are strings; menu ids from menuService are numbers.
        const categoryByMenuId = new Map(
            Object.entries(payload.category_by_menu_id || {}).map(([k, v]) => [Number(k), v])
        );

        const state = reactive({
            // user.settings returns a fresh shallow copy on every access, so copy
            // the array out rather than holding a reference to it.
            favoriteIds: [...(user.settings?.[FAVORITES_KEY] || [])],
        });

        // Writes are serialised rather than debounced.
        //
        // A debounce loses the write outright when the user pins an app and then
        // immediately navigates -- the timer dies with the page, and the pin is
        // silently forgotten. Pinning is a rare, deliberate action, so one small
        // RPC per toggle is the right trade. Chaining keeps them ordered, and
        // because each call sends the COMPLETE list, last-write-wins is correct.
        let pending = Promise.resolve();
        const persist = (ids, rollback) => {
            pending = pending
                .catch(() => {}) // a previous failure must not block later writes
                .then(() => user.setUserSettings(FAVORITES_KEY, ids))
                .catch((error) => {
                    state.favoriteIds = rollback;
                    throw error; // let the error service surface it
                });
            return pending;
        };

        return {
            categories: payload.categories || [], // pre-sorted server side
            categoryByMenuId,
            fallbackCategoryId: payload.fallback_category_id || null,
            state,
            isFavorite(menuId) {
                return state.favoriteIds.includes(menuId);
            },
            toggleFavorite(menuId) {
                const rollback = state.favoriteIds;
                state.favoriteIds = rollback.includes(menuId)
                    ? rollback.filter((id) => id !== menuId)
                    : [...rollback, menuId]; // append, so pin order is preserved
                persist(state.favoriteIds, rollback);
            },
        };
    },
};

registry.category("services").add("methode_apps_launcher", appsLauncherService);
