from odoo import Command, api, fields, models, tools
from odoo.exceptions import UserError

FALLBACK_CODE = 'other'

# Root menus whose declaring module mis-attributes them. `base.menu_administration`
# ("Settings"), `base.menu_management` ("Apps") and `base.menu_tests` all resolve,
# through ir.model.data, to module `base`, whose category is the invisible
# "Technical" one. Applied at priority 2, i.e. an admin can still override them.
#
# These live in Python rather than as seeded <record id="base.menu_administration">
# rows on purpose: the ir_model_data row belongs to `base` with noupdate=False, and
# _build_update_xmlids_query does not carry our noupdate="1" into the upsert, so a
# data row would silently re-apply on every upgrade of this module and stomp any
# admin edit.
MENU_XMLID_CATEGORY_CODE = {
    'base.menu_administration': 'admin',
    'base.menu_management': 'admin',
    'base.menu_tests': 'admin',
}

# ir.module.category records created at runtime by odoo/modules/db.py::create_categories
# rather than declared in base/data/ir_module_category_data.xml. They have no static
# declaration anywhere, so a `ref=` on them in a data file would hard-fail on a lean
# addons path -- hence Python with raise_if_not_found=False.
#
# Several are ORPHAN ROOTS: create_categories looks the xmlid up first and, when it
# already exists, never sets parent_id. Because base declares e.g.
# `module_category_sales_sign` without a parent, the "Sales/Sign" path is never wired
# up and parent-climbing alone would drop `sign`, `helpdesk`, `hr_appraisal` and
# `dms` into the fallback. Mapping the leaves explicitly is the fix.
DYNAMIC_MODULE_CATEGORY_MAPPING = {
    'sales': [
        'base.module_category_sales_sales',
        'base.module_category_sales_crm',
        'base.module_category_sales_point_of_sale',
        'base.module_category_sales_delivery',
        'base.module_category_supply_chain_purchase',
        'base.module_category_accounting_localizations',
        'base.module_category_point_of_sale',          # orphan root
        'base.module_category_invoicing_management',   # orphan root
        'base.module_category_website_sale',           # orphan root
        'base.module_category_account',                # lowercase orphan root
    ],
    'operations': [
        'base.module_category_supply_chain_inventory',
        'base.module_category_supply_chain_manufacturing',
        'base.module_category_supply_chain_maintenance',
        'base.module_category_supply_chain_repair',
        'base.module_category_services_project',
        'base.module_category_services_timesheets',
        'base.module_category_services_appointment',
        'base.module_category_services_field_service',
        'base.module_category_project',                # orphan root
    ],
    'hr': [
        'base.module_category_human_resources_employees',
        'base.module_category_human_resources_fleet',
        'base.module_category_human_resources_expenses',
        'base.module_category_human_resources_time_off',
        'base.module_category_human_resources_recruitment',
        'base.module_category_human_resources_payroll',
        'base.module_category_human_resources_attendances',
        'base.module_category_human_resources_lunch',
    ],
    'marketing': [
        'base.module_category_marketing_events',
        'base.module_category_marketing_email_marketing',
        'base.module_category_marketing_social_marketing',
        'base.module_category_marketing_surveys',
        'base.module_category_website_website',
        'base.module_category_website_live_chat',
        'base.module_category_website_elearning',
    ],
    'productivity': [
        'base.module_category_productivity_discuss',
        'base.module_category_productivity_calendar',
        'base.module_category_productivity_to_do',
        'base.module_category_productivity_dashboard',
        'base.module_category_document_management',    # orphan root (dms-methode)
        'base.module_category_agreement',              # orphan root
        'base.module_category_master_data',            # orphan root
    ],
    'admin': [
        'base.module_category_technical',
        'base.module_category_technical_settings',
        'base.module_category_hidden_tools',
        'base.module_category_hidden_tests',
        'base.module_category_tools',
        'base.module_category_extra_tools',
        'base.module_category_themes',
        'base.module_category_administration_administration',
    ],
    FALLBACK_CODE: [
        'base.module_category_uncategorized',
    ],
}


class MethodeAppsCategory(models.Model):
    _name = 'methode.apps.category'
    _description = 'Apps Launcher Category'
    _order = 'sequence, name, id'

    name = fields.Char(required=True, translate=True)
    code = fields.Char(
        required=True, copy=False,
        help="Stable technical key. Used by the 'apps_dropdown_category' manifest "
             "key and by the code; unlike the name it is never translated.")
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    module_category_ids = fields.Many2many(
        'ir.module.category',
        'methode_apps_category_module_category_rel',
        'apps_category_id', 'module_category_id',
        string="Odoo Categories",
        help="Odoo technical categories feeding this business category. "
             "Resolution walks up the parent chain, so mapping a parent covers "
             "all of its children.")

    menu_ids = fields.One2many(
        'ir.ui.menu', 'methode_app_category_id', string="Manual Overrides",
        domain=[('parent_id', '=', False)])

    app_count = fields.Integer(compute='_compute_app_count')

    _code_uniq = models.Constraint(
        'unique (code)',
        "The category code must be unique.",
    )

    def _compute_app_count(self):
        resolved = self._resolve_app_categories()
        counts = {}
        for category_id in resolved.values():
            counts[category_id] = counts.get(category_id, 0) + 1
        for category in self:
            category.app_count = counts.get(category.id, 0)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_fallback(self):
        if any(category.code == FALLBACK_CODE for category in self):
            raise UserError(self.env._(
                "The fallback category %(code)s cannot be deleted: apps that "
                "match no other category are placed in it.",
                code=FALLBACK_CODE,
            ))

    # -------------------------------------------------------------------------
    # Cache invalidation
    #
    # ir.ui.menu already calls registry.clear_cache() on create/write/unlink, so
    # the per-app override field is covered for free. Nothing invalidates on OUR
    # writes though, so the taxonomy has to bust its own cache.
    # -------------------------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        self.env.registry.clear_cache()
        return records

    def write(self, vals):
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        res = super().unlink()
        self.env.registry.clear_cache()
        return res

    def _register_hook(self):
        super()._register_hook()
        # loading.py calls this once per Registry.new(), on the load_modules rw
        # cursor, after every module is loaded. registry.updated_modules is
        # non-empty ONLY on a boot that actually installed or upgraded something,
        # so a plain worker boot costs nothing and multi-worker is safe.
        if self.env.registry.updated_modules:
            self.env['methode.apps.category']._seed_dynamic_module_category_mapping()
            self.env['ir.module.module']._sync_apps_dropdown_keys()

    # -------------------------------------------------------------------------
    # Resolution
    # -------------------------------------------------------------------------
    @api.model
    def _resolve_app_categories(self):
        """Map every app the current user can see to a business category.

        :return: ``{root_menu_id: methode.apps.category id}``
        :rtype: dict

        Everything below runs sudo(): ``ir.module.category`` is readable only by
        ``base.group_erp_manager`` and ``ir.module.module`` only by
        ``base.group_system``, but the launcher has to work for a plain user.
        """
        roots = self.env['ir.ui.menu'].get_user_roots()
        if not roots:
            return {}

        categories = self.sudo().search([])
        by_code = {c.code: c.id for c in categories}
        fallback_id = by_code.get(FALLBACK_CODE, False)

        # ir.module.category id -> our category id. Iterating a recordset ordered
        # by (sequence, name, id) with setdefault means the lowest-sequence bucket
        # wins deterministically when two buckets claim the same Odoo category.
        reverse_map = {}
        for category in categories:
            for module_category in category.module_category_ids:
                reverse_map.setdefault(module_category.id, category.id)

        # Flat parent chain, one query, ~100 rows.
        parent_of = {
            row['id']: row['parent_id'][0] if row['parent_id'] else False
            for row in self.env['ir.module.category'].sudo().search_read([], ['parent_id'])
        }

        def climb(module_category_id):
            """Walk up until a mapped category is found. Guarded against loops:
            ir.module.module._update_category logs 'ancestry loop has been
            detected and fixed', so they do occur in the wild."""
            seen = set()
            while module_category_id and module_category_id not in seen:
                seen.add(module_category_id)
                if module_category_id in reverse_map:
                    return reverse_map[module_category_id]
                module_category_id = parent_of.get(module_category_id)
            return False

        xmlids = roots._get_menuitems_xmlids()
        module_of = {
            menu_id: xmlid.split('.', 1)[0]
            for menu_id, xmlid in xmlids.items() if xmlid
        }

        modules = self.env['ir.module.module'].sudo().with_context(
            active_test=False,
        ).search_read(
            [('name', 'in', list(set(module_of.values())))],
            ['name', 'category_id', 'methode_app_category_code'],
        )
        module_by_name = {module['name']: module for module in modules}

        def from_module(module_name):
            module = module_by_name.get(module_name)
            if not module:
                return False
            key = module['methode_app_category_code']
            if key:
                category_id = by_code.get(key)
                if category_id:
                    return category_id
            if module['category_id']:
                return climb(module['category_id'][0])
            return False

        result = {}
        for menu in roots:
            # 1. manual override on the root menu
            category_id = menu.methode_app_category_id.id
            # 2. hardcoded fix for mis-attributed core root menus
            if not category_id:
                code = MENU_XMLID_CATEGORY_CODE.get(xmlids.get(menu.id, ''))
                category_id = by_code.get(code) if code else False
            # 3. manifest key, then 4. the module's Odoo category, climbed
            if not category_id and menu.id in module_of:
                category_id = from_module(module_of[menu.id])
            # 5. fallback
            result[menu.id] = category_id or fallback_id
        return result

    # -------------------------------------------------------------------------
    # Client payload
    # -------------------------------------------------------------------------
    @api.model
    @tools.ormcache('self.env.uid', 'self.env.lang')
    def _get_launcher_payload_cached(self):
        """Immutable form of the payload.

        ormcache hands the SAME object to every caller, so this must return
        nothing mutable -- otherwise one caller mutating the result silently
        corrupts the cache for every other request.

        Keyed on uid (visible root menus differ per user) and lang (``name`` is
        translatable).
        """
        categories = self.sudo().search([])
        return (
            tuple((c.id, c.code, c.name, c.sequence) for c in categories),
            tuple(sorted(self._resolve_app_categories().items())),
            self.sudo().search([('code', '=', FALLBACK_CODE)], limit=1).id,
        )

    @api.model
    def _get_launcher_payload(self):
        """Payload injected into ``session_info``. Read-only: it must never write,
        because ``/web/session/get_session_info`` runs on a read-only cursor."""
        categories, app_categories, fallback_id = self._get_launcher_payload_cached()
        return {
            'categories': [
                {'id': cid, 'code': code, 'name': name, 'sequence': sequence}
                for (cid, code, name, sequence) in categories
            ],
            # Keys become strings through JSON; the client coerces with Number().
            'category_by_menu_id': dict(app_categories),
            'fallback_category_id': fallback_id,
        }

    # -------------------------------------------------------------------------
    # Seeding
    # -------------------------------------------------------------------------
    @api.model
    def _seed_dynamic_module_category_mapping(self):
        """Link the runtime-created ir.module.category records.

        Additive and idempotent: it only ever links what is missing, so an admin
        who moved a category between two buckets keeps their change.
        """
        for code, xmlids in DYNAMIC_MODULE_CATEGORY_MAPPING.items():
            category = self.sudo().search([('code', '=', code)], limit=1)
            if not category:
                continue
            module_category_ids = []
            for xmlid in xmlids:
                record = self.env.ref(xmlid, raise_if_not_found=False)
                if record:
                    module_category_ids.append(record.id)
            missing = set(module_category_ids) - set(category.module_category_ids.ids)
            if missing:
                category.module_category_ids = [Command.link(mc_id) for mc_id in missing]

    def action_sync_manifests(self):
        """Re-read the 'apps_dropdown_category' manifest key of every module.

        Note that odoo.modules.Manifest caches parsed manifests in a process-level
        lru_cache, so a manifest edited on disk only becomes visible after the
        Odoo service restarts.
        """
        self.env['ir.module.module']._sync_apps_dropdown_keys()
        self.env.registry.clear_cache()
        return True

    def action_restore_default_mapping(self):
        """Re-link the shipped defaults without discarding customisations."""
        self._seed_dynamic_module_category_mapping()
        return True
