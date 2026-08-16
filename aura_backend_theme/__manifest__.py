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
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
             'aura_backend_theme/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            # must be first — applies CSS vars from session_info before any component renders
            'aura_backend_theme/static/src/js/theme_bootstrap.js',

            'aura_backend_theme/static/src/scss/home_dashboard.scss',
            'aura_backend_theme/static/src/scss/home_widget_grid.scss',
            'aura_backend_theme/static/src/xml/home_dashboard.xml',
            'aura_backend_theme/static/src/js/home_dashboard.js',

            'aura_backend_theme/static/src/scss/fonts.scss',
            'aura_backend_theme/static/src/scss/fa_v6_shim.scss',

            'aura_backend_theme/static/src/scss/navbar.scss',

            'aura_backend_theme/static/src/webclient/navbar/navbar.js',
            'aura_backend_theme/static/src/webclient/navbar/navbar.xml',

            'aura_backend_theme/static/src/webclient/loading/loading_style.js',

            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.js',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.xml',
            'aura_backend_theme/static/src/webclient/theme_settings/theme_settings_dialog.scss',
            'aura_backend_theme/static/src/webclient/home_menu/apps_menu.xml',
            'aura_backend_theme/static/src/webclient/switch_company_menu/switch_company_menu.xml',

            'aura_backend_theme/static/src/webclient/settings_form_view/settings_form_view.js',
            'aura_backend_theme/static/src/webclient/settings_form_view/settings_form_view.xml',
            'aura_backend_theme/static/src/webclient/settings_form_view/settings_app.xml',

            'aura_backend_theme/static/src/scss/views.scss',

            'aura_backend_theme/static/src/views/list_view/list_view.xml',
            'aura_backend_theme/static/src/views/discuss/discuss.xml',
            'aura_backend_theme/static/src/views/chatter/chatter.xml',
            'aura_backend_theme/static/src/views/status_bar/status_bar.xml',
            'aura_backend_theme/static/src/views/form_view/form_view.scss',
            'aura_backend_theme/static/src/views/list_view/list_view.scss',
            'aura_backend_theme/static/src/views/kanban_view/kanban_view.scss',
            'aura_backend_theme/static/src/views/activity_view/activity_view.scss',
            'aura_backend_theme/static/src/views/search_panel/search_panel.scss',
            'aura_backend_theme/static/src/views/discuss/discuss.scss',
            'aura_backend_theme/static/src/views/chatter/chatter.scss',
            'aura_backend_theme/static/src/views/others/others.scss',
            'aura_backend_theme/static/src/views/calendar_view/calendar_view.scss',
            'aura_backend_theme/static/src/views/chatter/chatter.js',
            'aura_backend_theme/static/src/views/status_bar/status_bar.scss',
            'aura_backend_theme/static/src/views/status_bar/status_bar.js',

            'aura_backend_theme/static/src/scss/app_widgets.scss',
            'aura_backend_theme/static/src/xml/app_widgets.xml',
            'aura_backend_theme/static/src/js/app_widgets.js',

            'aura_backend_theme/static/src/scss/buttons.scss',
            'aura_backend_theme/static/src/scss/misc.scss',
            'aura_backend_theme/static/src/scss/rtl.scss',
        ],

        'web.assets_frontend': [
            'aura_backend_theme/static/src/scss/login.scss',
            'aura_backend_theme/static/src/scss/signup.scss',
            'aura_backend_theme/static/src/scss/rtl.scss',
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
