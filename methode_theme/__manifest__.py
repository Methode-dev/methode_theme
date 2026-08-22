{
    'name': 'Méthode Theme',
    'version': '19.0.1.0.0',
    'category': 'Themes/Backend',
    'summary': 'Méthode brand identity for the Odoo backend',
    # Set explicitly, and keep it set.  Odoo's load_manifest() falls back to
    # slurping README.md into `description` whenever this key is empty, then
    # renders it as reStructuredText — so a Markdown README produces a burst of
    # docutils "Undefined substitution referenced" errors on every module load.
    # The README is developer documentation and is not valid RST by design.
    'description': 'Methode brand identity for the Odoo backend. '
                   'See README.md in this module for the design system.',
    'author': 'Méthode - Progiciel sur mesure',
    'website': 'https://methode.dev',
    'license': 'LGPL-3',
    'depends': ['web', 'aura_backend_theme'],
    # The module was assets-only until the login rebrand (§3.3 / §15.2 B9).
    'data': [
        'views/login_templates.xml',
        # Must be server-side QWeb: it has to paint before OWL exists (P8e).
        'views/boot_loader_templates.xml',
        # --- Home dashboard, P8a ------------------------------------------
        # Security first: the record rule is the only thing separating one
        # user's layout from another's (see dashboard_security.xml).
        'security/ir.model.access.csv',
        'security/dashboard_security.xml',
        'data/dashboard_widget_type_data.xml',
        # Dashboard alert thresholds, on the General Settings page (§2.4).
        'views/res_config_settings_views.xml',
        # ⚠ Must load AFTER the component exists in the bundle: it creates a menu
        # pointing at client action tag `methode_theme.home_dashboard`, and a
        # menu whose tag is unregistered throws when clicked rather than
        # degrading.  The tag is registered in static/src/dashboard/dashboard.js.
        'views/dashboard_actions.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
            'methode_theme/static/src/scss/brand_variables.scss'),
        ],
        'web.assets_backend': [
            # Order is load-bearing (§5.3): brand tokens -> base/typography ->
            # components -> views -> fixes.  Tokens must come first so every
            # later sheet can read them.
            'methode_theme/static/src/scss/css_tokens.scss',
            'methode_theme/static/src/scss/typography.scss',
            'methode_theme/static/src/scss/buttons.scss',
            'methode_theme/static/src/scss/forms.scss',
            'methode_theme/static/src/scss/cards.scss',
            'methode_theme/static/src/scss/surfaces.scss',
            'methode_theme/static/src/scss/navbar.scss',
            # Two-row navbar (§5.4).  The template MOVES stock nodes into two
            # rows; web.NavBar.AppsMenu is left alone for methode_apps_dropdown.
            'methode_theme/static/src/navbar/navbar.js',
            'methode_theme/static/src/navbar/navbar.xml',
            # The in-app loading snackbar.  ⚠ The BOOT loader's CSS is NOT here —
            # it is inlined in views/boot_loader_templates.xml, because this
            # bundle is a megabyte of render-blocking CSS and the mark has to
            # paint before it is parsed.  See that file for the measurement.
            'methode_theme/static/src/scss/loader.scss',
            'methode_theme/static/src/js/boot_loader.js',
            'methode_theme/static/src/js/loading_indicator.js',
            # --- Home dashboard, P8a ------------------------------------------
            # The client action tag `methode_theme.home_dashboard` is registered
            # in dashboard.js; views/dashboard_actions.xml depends on it existing.
            'methode_theme/static/src/dashboard/dashboard.js',
            'methode_theme/static/src/dashboard/dashboard.xml',
            'methode_theme/static/src/dashboard/dashboard.scss',
            # Views come after components: they tune what the component sheets
            # above establish, so they must be able to win at equal specificity.
            'methode_theme/static/src/scss/views/list_view.scss',
            'methode_theme/static/src/scss/views/form_view.scss',
            'methode_theme/static/src/scss/views/kanban_view.scss',
            'methode_theme/static/src/scss/views/status_bar.scss',
            'methode_theme/static/src/scss/views/settings_view.scss',
            # Theme settings live on the Settings page, not in a systray popup —
            # see aura_backend_theme/views/res_config_settings_views.xml.
        ],
        # The login page (§3.3).  This is NOT optional polish: brand_variables
        # lives in _assets_primary_variables, which the frontend bundle also
        # includes, so the frontend CSS already says `font-family: Nunito` —
        # but the @font-face that actually fetches the woff2 is in
        # typography.scss.  Without it the login page asks for a font it never
        # loads and silently falls back to system sans, with no error anywhere.
        # Keep these three in sync with the backend list above.
        'web.assets_frontend': [
            'methode_theme/static/src/scss/css_tokens.scss',
            'methode_theme/static/src/scss/typography.scss',
            'methode_theme/static/src/scss/buttons.scss',
            # .m-tree-loader + its keyframes, for qcm_guest_walkthrough's final
            # step to reuse the same animated mark as the backend boot loader.
            # The rest of this sheet (.m-boot-loader, .o_loading_indicator)
            # matches nothing on the login page — inert there, not dead code.
            'methode_theme/static/src/scss/loader.scss',
            # Frontend-ONLY, deliberately — its selectors exist only on the
            # login page, so shipping it to the backend too would be dead CSS.
            # The "add it to both bundles" warning above is about sheets the
            # login page NEEDS; see the header comment in login.scss.
            'methode_theme/static/src/scss/login.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}