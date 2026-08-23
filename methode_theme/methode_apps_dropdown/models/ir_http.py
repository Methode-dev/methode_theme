from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        """Ship the launcher taxonomy with the session.

        session_info is rebuilt on every webclient load and is never cached
        client-side, so there is no invalidation story to get wrong -- unlike
        load_menus, whose payload sits in localStorage keyed on registry_hash and
        would go stale the moment an admin edited a category.
        """
        result = super().session_info()
        if result.get('uid') and self.env.user._is_internal():
            result['methode_apps_dropdown'] = \
                self.env['methode.apps.category']._get_launcher_payload()
        return result
