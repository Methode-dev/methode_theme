{
  'name': 'Méthode Theme',
  'version': '19.0.1.0.0',
  'category': 'Themes/Backend',
  'summary': 'Méthode brand identity for the Odoo backend',
  'author': 'Méthode - Progiciel sur mesure',
  'website': 'https://methode.dev',
  'license': 'LGPL-3',
  # aura_backend_theme is NOT a functional dependency. It is declared solely to
  # guarantee asset load order — methode_theme must win the cascade over what
  # remains of Aura. Drop it the day Aura goes away. See THEME_PLAN.md §9.1.
  'depends': ['web', 'aura_backend_theme'],
  'assets': {
      'web._assets_primary_variables': [
          ('before', 'web/static/src/scss/primary_variables.scss',
           'methode_theme/static/src/scss/brand_variables.scss'),
      ],
      'web.assets_backend': [],
  },
  'installable': True,
  'application': False,
  'auto_install': False,
}