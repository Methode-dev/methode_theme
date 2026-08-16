from odoo.tests.common import TransactionCase

class TestHomeDashboardConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ConfigModel = cls.env['theme.home.dashboard.config']
        cls.user = cls.env.user

    def test_default_config_creation(self):
        """Test default config values for users."""
        config = self.ConfigModel.create({'user_id': self.user.id})
        
        self.assertTrue(config.show_stats_row)
        self.assertTrue(config.show_activities)
        self.assertEqual(config.invoice_limit, 5)
        self.assertEqual(config.layout_density, 'spacious')
        self.assertEqual(config.dashboard_theme, 'aura')
