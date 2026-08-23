/**
 * Two-row navbar (§5.4). The split itself is in navbar.xml; this file adds the
 * search control and the company fallback the app row needs when no app is open.
 */

import { Component } from "@odoo/owl";
import { isMacOS } from "@web/core/browser/feature_detection";
import { _t } from "@web/core/l10n/translation";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { NavBar } from "@web/webclient/navbar/navbar";

export class NavBarSearch extends Component {
    static template = "methode_theme.NavBarSearch";
    static props = {};

    setup() {
        this.command = useService("command");
        this.hotkey = isMacOS() ? "⌘K" : "Ctrl K";
        this.title = _t("Search (%s)", this.hotkey);
    }

    open() {
        this.command.openMainPalette();
    }
}

patch(NavBar, {
    components: { ...NavBar.components, NavBarSearch },
});

patch(NavBar.prototype, {
    get companyName() {
        return user.activeCompany?.name || "";
    },
});
