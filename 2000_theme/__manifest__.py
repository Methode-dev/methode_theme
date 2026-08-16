{
    'name': '2000 Theme',
    'version': '19.0.1.0.0',
    'category': 'Themes/Backend',
    'summary': 'Enhanced UX theme with improved readability and ergonomics',
    'description': """
        2000 Theme - Enhanced User Experience
        ======================================

        This theme improves Odoo's default UI with:
        - Input fields with bottom border only (primary color on focus)
        - Dropdown fields with visible arrow indicator in read mode
        - Buttons with consistent padding and square corners
        - Clear chatter separation with left border
        - Outlined page tabs with primary color on active tab
        - List headers with subtle drop shadow
        - Clean white navbar
    """,
    'author': 'Interport',
    'depends': ['web'],
    'data': [],
    'assets': {
        'web.assets_backend': [
            # 1. Variables (must be first)
            '2000_theme/static/src/scss/primary_variables_custom.scss',
            '2000_theme/static/src/scss/secondary_variables_custom.scss',
            '2000_theme/static/src/scss/css_variables_override.scss',
            # 2. Base components
            '2000_theme/static/src/scss/inputs.scss',
            # '2000_theme/static/src/scss/buttons.scss',
            # 3. Layout components
            '2000_theme/static/src/scss/navbar.scss',
            '2000_theme/static/src/scss/forms.scss',
            '2000_theme/static/src/scss/list_view.scss',
            # 4. Extras
            '2000_theme/static/src/scss/fields_extra_custom.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
