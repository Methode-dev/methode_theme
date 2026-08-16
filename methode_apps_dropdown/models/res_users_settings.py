from odoo import api, fields, models


class ResUsersSettings(models.Model):
    _inherit = 'res.users.settings'

    methode_apps_favorite_menu_ids = fields.Json(
        string="Pinned Apps", default=list,
        help="Ordered list of ir.ui.menu ids pinned by the user in the Apps "
             "launcher.")

    # A Json list rather than a Many2many('ir.ui.menu') on purpose:
    #  * it preserves the user's pin order, which an m2m does not;
    #  * set_res_users_settings does a plain write() and guards on
    #    `new_settings[f] != self[f]`; comparing a [[6, 0, ids]] command list
    #    against a recordset is always True, so an m2m would write on every call.
    #
    # No ACL or SELF_WRITEABLE_FIELDS work is needed: base already grants each
    # user full CRUD on their own res.users.settings row
    # (base/security/base_security.xml, res_users_settings_rule_user), and
    # _res_users_settings_format already emits every non-magic field into
    # session_info. The client writes through user.setUserSettings().

    def write(self, vals):
        if 'methode_apps_favorite_menu_ids' in vals:
            vals = dict(
                vals,
                methode_apps_favorite_menu_ids=self._sanitize_favorite_menu_ids(
                    vals['methode_apps_favorite_menu_ids']
                ),
            )
        return super().write(vals)

    @api.model
    def _sanitize_favorite_menu_ids(self, value):
        """Coerce whatever the client sent into a de-duplicated list of ids of
        root menus the user can actually see.

        The field is user-writable, so it is the one place a client can put
        arbitrary JSON into the database. Order is preserved because it is the
        user's pin order.
        """
        if not isinstance(value, (list, tuple)):
            return []
        visible_ids = set(self.env['ir.ui.menu'].get_user_roots().ids)
        seen = set()
        result = []
        for item in value:
            if not isinstance(item, int) or isinstance(item, bool):
                continue
            if item in seen or item not in visible_ids:
                continue
            seen.add(item)
            result.append(item)
        return result
