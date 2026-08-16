# -*- coding: utf-8 -*-
from odoo import api, fields, models


class HomeWidget(models.Model):
    _name = 'theme.home.widget'
    _description = 'Home Dashboard Widget Row'
    _order = 'position asc, id asc'

    user_id = fields.Many2one(
        'res.users', required=True, ondelete='cascade',
        default=lambda self: self.env.user
    )
    widget_id = fields.Char('Widget Key', required=True)
    position = fields.Integer('Position', default=0)
    col_span = fields.Selection(
        [('1', '1 column'), ('2', '2 columns'), ('3', 'Full width')],
        string='Width', default='1', required=True
    )
    config_json = fields.Text('Widget Config (JSON)', default='{}')
    active = fields.Boolean(default=True)

    _user_widget_unique = models.Constraint(
        'UNIQUE(user_id, widget_id)',
        'This widget is already on the dashboard for this user.',
    )

    @api.model
    def get_user_widgets(self):
        widgets = self.search([('user_id', '=', self.env.uid), ('active', '=', True)])
        if not widgets:
            # If the user has no active widgets but has historical rows
            # (inactive), keep the dashboard empty as requested.
            any_rows = self.with_context(active_test=False).search(
                [('user_id', '=', self.env.uid)],
                limit=1,
            )
            if any_rows:
                return self.browse()
            widgets = self._create_defaults()
        return widgets

    @api.model
    def _default_widget_values(self):
        installed = {
            m.name for m in self.env['ir.module.module'].sudo().search([('state', '=', 'installed')])
        }
        defaults = [
            {'widget_id': 'quick_actions', 'position': 0, 'col_span': '3'},
            {'widget_id': 'stats',         'position': 1, 'col_span': '3'},
            {'widget_id': 'activities',    'position': 2, 'col_span': '2'},
            {'widget_id': 'focus',         'position': 3, 'col_span': '1'},
        ]
        if 'account' in installed:
            defaults.append({'widget_id': 'invoices', 'position': len(defaults), 'col_span': '2'})
        defaults.append({'widget_id': 'recent', 'position': len(defaults), 'col_span': '1'})
        if 'crm' in installed:
            defaults.append({'widget_id': 'pipeline', 'position': len(defaults), 'col_span': '3'})
        return defaults

    @api.model
    def restore_default_widgets(self):
        """Reset current user's dashboard to exactly the default widget set."""
        defaults = self._default_widget_values()
        default_ids = {d['widget_id'] for d in defaults}

        all_rows = self.with_context(active_test=False).search([('user_id', '=', self.env.uid)])
        by_widget = {row.widget_id: row for row in all_rows}

        # Remove any user-added widgets from the active dashboard on reset.
        extras = all_rows.filtered(lambda row: row.widget_id not in default_ids and row.active)
        if extras:
            extras.write({'active': False})

        # Ensure defaults exist, are active, and are back in default order/sizing.
        for d in defaults:
            existing = by_widget.get(d['widget_id'])
            values = {
                'position': d['position'],
                'col_span': d['col_span'],
                'active': True,
            }
            if existing:
                existing.write(values)
            else:
                self.create({**d, 'user_id': self.env.uid})

        return self.search([('user_id', '=', self.env.uid), ('active', '=', True)])

    def _create_defaults(self):
        defaults = self._default_widget_values()

        all_rows = self.with_context(active_test=False).search([('user_id', '=', self.env.uid)])
        by_widget = {row.widget_id: row for row in all_rows}

        created = self.browse()
        for d in defaults:
            existing = by_widget.get(d['widget_id'])
            values = {
                'position': d['position'],
                'col_span': d['col_span'],
                'active': True,
            }
            if existing:
                existing.write(values)
            else:
                created |= self.create({**d, 'user_id': self.env.uid})

        return self.search([('user_id', '=', self.env.uid), ('active', '=', True)])
