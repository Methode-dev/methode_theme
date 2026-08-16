from psycopg2.errors import UniqueViolation

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

from ..models.methode_apps_category import FALLBACK_CODE


@tagged('post_install', '-at_install')
class TestAppsDropdown(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Category = cls.env['methode.apps.category']
        cls.other = cls.env.ref('methode_apps_dropdown.apps_category_other')
        cls.admin_category = cls.env.ref('methode_apps_dropdown.apps_category_admin')

    # -------------------------------------------------------------------------
    # Resolution
    # -------------------------------------------------------------------------
    def test_installed_apps_are_categorised(self):
        """No installed application should land in the fallback bucket.

        A new orphan ir.module.category root is a data bug: add it to
        DYNAMIC_MODULE_CATEGORY_MAPPING rather than relaxing this test.
        """
        resolved = self.Category._resolve_app_categories()
        roots = self.env['ir.ui.menu'].get_user_roots()
        xmlids = roots._get_menuitems_xmlids()

        uncategorised = []
        for menu in roots:
            xmlid = xmlids.get(menu.id, '')
            if not xmlid:
                continue  # hand-created menus legitimately fall through
            module = self.env['ir.module.module'].sudo().search([
                ('name', '=', xmlid.split('.', 1)[0]),
                ('state', '=', 'installed'),
                ('application', '=', True),
            ], limit=1)
            if module and resolved.get(menu.id) == self.other.id:
                uncategorised.append(f'{menu.name} ({xmlid})')

        self.assertFalse(
            uncategorised,
            "These installed applications fall into the fallback category: "
            f"{uncategorised}",
        )

    def test_core_admin_menus_are_admin(self):
        """Settings and Apps both resolve to module `base` -> the invisible
        Technical category, so they need the hardcoded fix."""
        resolved = self.Category._resolve_app_categories()
        for xmlid in ('base.menu_administration', 'base.menu_management'):
            menu = self.env.ref(xmlid)
            self.assertEqual(
                resolved.get(menu.id), self.admin_category.id,
                f'{xmlid} should resolve to the Administration category',
            )

    def test_manual_override_wins(self):
        menu = self.env.ref('base.menu_administration')
        target = self.env.ref('methode_apps_dropdown.apps_category_productivity')
        menu.methode_app_category_id = target
        self.assertEqual(
            self.Category._resolve_app_categories().get(menu.id), target.id,
            'The per-app override must beat the hardcoded mapping',
        )

    def test_climb_survives_ancestry_loop(self):
        """ir.module.module._update_category logs 'ancestry loop has been
        detected and fixed', so loops do happen. Resolution must terminate."""
        ModuleCategory = self.env['ir.module.category'].sudo()
        first = ModuleCategory.create({'name': 'Loop A'})
        second = ModuleCategory.create({'name': 'Loop B', 'parent_id': first.id})
        self.env.cr.execute(
            'UPDATE ir_module_category SET parent_id = %s WHERE id = %s',
            (second.id, first.id),
        )
        ModuleCategory.invalidate_model(['parent_id'])
        # Must return rather than spin.
        self.Category._resolve_app_categories()

    # -------------------------------------------------------------------------
    # Payload
    # -------------------------------------------------------------------------
    def test_payload_shape(self):
        payload = self.Category._get_launcher_payload()
        self.assertIn('categories', payload)
        self.assertIn('category_by_menu_id', payload)
        self.assertEqual(payload['fallback_category_id'], self.other.id)
        sequences = [c['sequence'] for c in payload['categories']]
        self.assertEqual(sequences, sorted(sequences),
                         'Categories must reach the client pre-sorted')

    def test_payload_creates_no_records(self):
        """/web/session/get_session_info runs on a read-only cursor, so the
        payload path must never write. In particular, a manifest key naming an
        unknown category must fall through rather than lazily create it."""
        self.env.flush_all()
        self.env.registry.clear_cache()

        def counts():
            return (
                self.Category.sudo().search_count([]),
                self.env['ir.module.category'].sudo().search_count([]),
            )

        before = counts()
        self.Category._get_launcher_payload()
        self.env.flush_all()
        self.assertEqual(before, counts(), 'The payload path created records')

    def test_payload_readable_by_plain_user(self):
        """ir.module.category is group_erp_manager and ir.module.module is
        group_system, so the whole resolution path has to be sudo()."""
        plain = self.env['res.users'].create({
            'name': 'Launcher Plain User',
            'login': 'launcher_plain_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        payload = self.Category.with_user(plain)._get_launcher_payload()
        self.assertTrue(payload['categories'])

    def test_cache_busted_on_category_write(self):
        target = self.env.ref('methode_apps_dropdown.apps_category_productivity')
        menu = self.env.ref('base.menu_administration')

        before = self.Category._get_launcher_payload()['category_by_menu_id']
        self.assertEqual(before[menu.id], self.admin_category.id)

        # Writing on our own model must clear the ormcache; nothing does it for us.
        menu.methode_app_category_id = target
        after = self.Category._get_launcher_payload()['category_by_menu_id']
        self.assertEqual(after[menu.id], target.id)

        target.write({'sequence': target.sequence})
        self.assertTrue(self.Category._get_launcher_payload()['categories'])

    # -------------------------------------------------------------------------
    # Taxonomy guards
    # -------------------------------------------------------------------------
    def test_fallback_cannot_be_deleted(self):
        with self.assertRaises(UserError):
            self.other.unlink()

    def test_code_is_unique(self):
        with self.assertRaises(UniqueViolation), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.Category.create({'name': 'Dup', 'code': FALLBACK_CODE})
                self.env.flush_all()

    def test_seeding_is_idempotent_and_additive(self):
        category = self.env.ref('methode_apps_dropdown.apps_category_operations')
        custom = self.env['ir.module.category'].sudo().create({'name': 'Custom Bucket'})
        category.module_category_ids = [(4, custom.id)]
        before = set(category.module_category_ids.ids)

        self.Category._seed_dynamic_module_category_mapping()
        self.Category._seed_dynamic_module_category_mapping()

        after = set(category.module_category_ids.ids)
        self.assertTrue(before <= after, 'Seeding must never drop an admin link')
        self.assertIn(custom.id, after)

    # -------------------------------------------------------------------------
    # Favorites
    # -------------------------------------------------------------------------
    def test_favorites_roundtrip_as_plain_user(self):
        plain = self.env['res.users'].create({
            'name': 'Launcher Favorite User',
            'login': 'launcher_favorite_user',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        Settings = self.env['res.users.settings'].with_user(plain)
        settings = Settings._find_or_create_for_user(plain).with_user(plain)

        roots = self.env['ir.ui.menu'].with_user(plain).get_user_roots()
        self.assertTrue(roots, 'The test user needs at least one visible app')
        wanted = roots[:2].ids

        # No sudo: base already grants each user CRUD on their own settings row.
        settings.set_res_users_settings({'methode_apps_favorite_menu_ids': wanted})
        self.assertEqual(settings.methode_apps_favorite_menu_ids, wanted,
                         'Pin order must be preserved')

    def test_favorites_are_sanitised(self):
        settings = self.env['res.users.settings']._find_or_create_for_user(self.env.user)
        visible = self.env['ir.ui.menu'].get_user_roots()[0].id
        settings.write({'methode_apps_favorite_menu_ids': [
            visible, visible, -1, 'not-an-id', None, True,
        ]})
        self.assertEqual(
            settings.methode_apps_favorite_menu_ids, [visible],
            'Duplicates, invisible menus and non-integers must be dropped',
        )
