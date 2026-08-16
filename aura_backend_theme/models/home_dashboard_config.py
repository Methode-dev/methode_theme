# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HomeDashboardConfig(models.Model):
    _name = 'theme.home.dashboard.config'
    _description = 'Home Dashboard Widget Configuration'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        'res.users', string='User', required=True, ondelete='cascade',
        default=lambda self: self.env.user
    )

    # Widget visibility toggles
    show_stats_row = fields.Boolean('Show Overview Stats', default=True)
    show_activities = fields.Boolean('Show My Activities', default=True)
    show_invoices = fields.Boolean('Show Top Invoices', default=True)
    show_pipeline = fields.Boolean('Show My Pipeline (CRM)', default=True)
    show_recent = fields.Boolean('Show Recently Opened', default=True)
    show_shortcuts = fields.Boolean('Show Quick Access', default=True)

    # Widget-level options
    invoice_limit = fields.Integer('Max invoices to show', default=5)
    invoice_filter = fields.Selection(
        [('all', 'All'), ('overdue', 'Overdue'), ('this_month', 'This Month')],
        string='Invoice Filter', default='all'
    )
    activity_limit = fields.Integer('Max activities to show', default=5)
    pipeline_stages_limit = fields.Integer('Max pipeline stages shown', default=4)
    recent_limit = fields.Integer('Max recent records', default=6)
    shortcut_ids = fields.Many2many('ir.ui.menu', string='Pinned Menu Shortcuts')

    # Layout options
    layout_density = fields.Selection(
        [('comfortable', 'Comfortable'), ('compact', 'Compact'), ('spacious', 'Spacious')],
        string='Layout Density', default='spacious'
    )
    dashboard_theme = fields.Selection(
        [
            ('aura', 'Aura'),
            ('minimalistic', 'Minimalistic'),
            ('colorful', 'Colorful'),
            ('classic', 'Classic'),
            ('ocean', 'Ocean'),
            ('sunset', 'Sunset'),
            ('midnight', 'Midnight'),
        ],
        string='Dashboard Theme', default='aura'
    )
    theme_mode = fields.Selection(
        [
            ('auto', 'Auto (follow Odoo appearance)'),
            ('manual', 'Manual'),
        ],
        string='Theme Mode',
        default='auto',
    )
    stats_modules = fields.Char(
        'Stats to show',
        default='invoices_open,bills_overdue,activities_due,pipeline_value'
    )

    _user_id_unique = models.Constraint(
        'UNIQUE(user_id)',
        'A dashboard config already exists for this user.',
    )

    @api.model
    def get_or_create_for_user(self):
        config = self.search([('user_id', '=', self.env.uid)], limit=1)
        if not config:
            try:
                config = self.create({'user_id': self.env.uid})
            except Exception:
                # Concurrent request already created it; fetch the existing record.
                self.env.cr.rollback()
                config = self.search([('user_id', '=', self.env.uid)], limit=1)
        return config
