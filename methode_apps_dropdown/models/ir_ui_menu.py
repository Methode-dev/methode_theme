from odoo import fields, models


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    methode_app_category_id = fields.Many2one(
        'methode.apps.category', string="Launcher Category",
        ondelete='set null', index='btree_not_null',
        help="Forces this app into a given category in the Apps launcher. Takes "
             "precedence over every automatic rule. Only meaningful on a root "
             "menu, i.e. an app.")

    # No create/write override needed to bust the launcher cache: core ir.ui.menu
    # already calls self.env.registry.clear_cache() on create, write and unlink.
