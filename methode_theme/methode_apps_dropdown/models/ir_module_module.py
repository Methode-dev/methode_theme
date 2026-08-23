from odoo import api, fields, models

MANIFEST_KEY = 'apps_dropdown_category'


class IrModuleModule(models.Model):
    _inherit = 'ir.module.module'

    methode_app_category_code = fields.Char(
        string="Launcher Category Key", readonly=True, copy=False,
        help="Value of the 'apps_dropdown_category' manifest key, persisted when "
             "the module list is refreshed.")

    @api.model
    def update_list(self):
        # Also fires for Apps > Update Apps List. It does NOT fire at boot: the
        # core call site in odoo/modules/loading.py runs when only `base` is in
        # the registry, so this override does not exist yet. First install is
        # covered by post_init_hook, and later installs/upgrades by
        # methode.apps.category._register_hook.
        res = super().update_list()
        self._sync_apps_dropdown_keys()
        return res

    @api.model
    def _sync_apps_dropdown_keys(self, module_names=None):
        """Persist the ``apps_dropdown_category`` manifest key onto the modules,
        creating any category it names that does not exist yet.

        Only ever called from read/write cursors (``post_init_hook``,
        ``_register_hook``, ``update_list``, the *Resync manifests* button), never
        from the ``session_info`` read path.

        :return: whether anything changed
        :rtype: bool
        """
        Category = self.env['methode.apps.category'].sudo()

        domain = [('name', 'in', list(module_names))] if module_names else []
        modules = self.sudo().with_context(active_test=False).search(domain)

        categories = Category.search([])
        by_code = {c.code: c for c in categories}
        by_name = {c.name: c for c in categories}

        changed = False
        for module in modules:
            # get_module_info returns a Manifest (a Mapping) or {}, so .get() is
            # safe against Manifest.__getitem__ raising KeyError.
            key = (self.get_module_info(module.name).get(MANIFEST_KEY) or '').strip()
            if key and key not in by_code and key not in by_name:
                created = Category.create({
                    'name': key,
                    'code': key,
                    'sequence': 500,
                })
                by_code[created.code] = created
                by_name[created.name] = created
            # Normalise to the category's code, so resolution only ever has to
            # look the key up in one index.
            resolved = by_code.get(key) or by_name.get(key) if key else None
            value = resolved.code if resolved else False
            if module.methode_app_category_code != value:
                module.methode_app_category_code = value
                changed = True

        if changed:
            self.env.registry.clear_cache()
        return changed
