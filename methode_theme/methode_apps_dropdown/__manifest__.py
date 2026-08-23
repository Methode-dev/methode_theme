{
    'name': 'Apps Launcher - Methode',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Tiled Apps menu, grouped by business category, with favorites',
    'description': """
Apps Launcher
=============

Replaces the plain Apps dropdown in the navbar with a tiled launcher:

* app tiles, 3 per row, in stacked sections
* apps grouped by *business* category rather than Odoo's technical one
* a per-user Favorites section pinned at the top

Categories are resolved per app, highest priority first:

1. the manual override on the app's root menu (``Launcher Category``)
2. the ``apps_dropdown_category`` manifest key of the declaring module
3. the module's ``ir.module.category``, walked up until it hits a mapped one
4. the ``Other`` fallback category

Only the stock ``web`` navbar is supported. The backend themes shipped in this
template (``aura_backend_theme``, ``pine_backend_theme``) replace the whole
navbar header, so the launcher will not appear when one of them is installed.
""",
    'author': 'Methode',
    'website': 'https://methode.dev',
    'license': 'LGPL-3',
    'depends': ['web'],
    'data': [
        'security/ir.model.access.csv',
        'data/methode_apps_category_data.xml',
        'views/methode_apps_category_views.xml',
        'views/ir_ui_menu_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            # Listed dependency-first for readability; the module loader resolves
            # ES-module deps by name, so JS order does not affect correctness.
            'methode_apps_dropdown/static/src/utils/app_icon.js',
            'methode_apps_dropdown/static/src/services/apps_launcher_service.js',
            'methode_apps_dropdown/static/src/apps_launcher/apps_launcher.js',
            'methode_apps_dropdown/static/src/apps_launcher/apps_launcher.xml',
            'methode_apps_dropdown/static/src/navbar/navbar_patch.js',
            # XML order DOES matter: registerTemplateExtension() blocks are applied
            # in bundle order. This must land after web's navbar.xml, which
            # depends=['web'] guarantees.
            'methode_apps_dropdown/static/src/navbar/navbar_apps_menu.xml',
            # SCSS last so it wins the cascade at equal specificity.
            'methode_apps_dropdown/static/src/apps_launcher/apps_launcher.scss',
        ],
        'web.assets_unit_tests': [
            'methode_apps_dropdown/static/tests/**/*.test.js',
        ],
        'web.assets_tests': [
            'methode_apps_dropdown/static/tests/tours/*.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
