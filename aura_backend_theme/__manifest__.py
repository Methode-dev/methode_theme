# -*- coding: utf-8 -*-
{
    'name': 'Aura Backend Theme - Community Edition',
    'version': '19.0.1.5.0',
    'category': 'Themes/Backend',
    'summary': 'Premium backend theme for Odoo 19 Community',
    'description': """
Aura Backend Theme - Community Edition
======================
A premium backend theme for Odoo 19 Community Edition.

Covers:
- Login page
- Top navigation bar
- App menu
- Form views
- List views
- Kanban views
- Buttons, badges, alerts
- Typography and icons
    """,
    'author': 'LATI',
    'website': 'https://latitibabu.com',
    'live_test_url': 'https://aurademoform.latitibabu.com',
    'support': 'support@latitibabu.com',
    'price': 49.99,
    'currency': 'USD',
    'depends': ['web', 'base_setup', 'mail', 'auth_signup'],
    'data': [
        'security/ir.model.access.csv',
        # Loads the FA6 webfont that fa_v6_shim.scss assumes is present, and
        # server-renders the :root palette so the page paints on-brand before
        # theme_bootstrap.js runs.  Dropped by mistake alongside the login and
        # dashboard templates; THEME_PLAN §3.2 keeps it.
        'views/web_assets.xml',
        # Theme Settings block on Settings > General Settings. Replaces the
        # systray + ThemeSettingsDialog entry point (§9.7).
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'aura_backend_theme/static/src/js/theme_bootstrap.js',

            'aura_backend_theme/static/src/scss/fa_v6_shim.scss',

            'aura_backend_theme/static/src/webclient/loading/loading_style.js',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.js',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.xml',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.scss',
        ],
    },
    'images': [
        'static/description/banner.png',
        'static/description/theme_screenshot.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'license': 'OPL-1',
}
