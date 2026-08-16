# -*- coding: utf-8 -*-
{
    'name': 'Aura Backend Theme - Community Edition',
    'version': '19.0.1.0.2',
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
        'security/home_dashboard_security.xml',
        'views/web_assets.xml',
        'views/login_templates.xml',
        'views/res_config_settings_views.xml',
        'views/home_dashboard_templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'aura_backend_theme/static/src/js/theme_bootstrap.js',

            'aura_backend_theme/static/src/scss/home_dashboard.scss',
            'aura_backend_theme/static/src/scss/home_widget_grid.scss',
            'aura_backend_theme/static/src/xml/home_dashboard.xml',
            'aura_backend_theme/static/src/js/home_dashboard.js',

            'aura_backend_theme/static/src/scss/app_widgets.scss',
            'aura_backend_theme/static/src/xml/app_widgets.xml',
            'aura_backend_theme/static/src/js/app_widgets.js',

            'aura_backend_theme/static/src/scss/fa_v6_shim.scss',

            'aura_backend_theme/static/src/webclient/loading/loading_style.js',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.js',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.xml',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.scss',
        ],
        # 'web.assets_frontend' removed entirely — login.scss/signup.scss/rtl.scss are gone.
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
