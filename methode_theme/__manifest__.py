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
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}