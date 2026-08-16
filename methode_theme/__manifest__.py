{
    'name': 'Méthode Theme',
    'version': '19.0.1.0.0',
    'category': 'Themes/Backend',
    'summary': 'Méthode brand identity for the Odoo backend',
    'author': 'Méthode - Progiciel sur mesure',
    'website': 'https://methode.dev',
    'license': 'LGPL-3',
    'depends': ['web', 'aura_backend_theme'],
    'assets': {
        'web._assets_primary_variables': [
            ('before', 'web/static/src/scss/primary_variables.scss',
            'methode_theme/static/src/scss/brand_variables.scss'),
        ],
        'web.assets_backend': [
            'methode_theme/static/src/webclient/theme_settings/theme_settings_systray.js',
            'methode_theme/static/src/webclient/theme_settings/theme_settings_systray.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}