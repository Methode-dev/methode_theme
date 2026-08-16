import json
from odoo.tests.common import HttpCase, tagged

@tagged('post_install', '-at_install', 'aura_backend_theme')
class TestHomeDashboardController(HttpCase):

    def setUp(self):
        super().setUp()
        self.user = self.env.ref('base.user_admin')

    def test_01_dashboard_data_endpoint(self):
        """Test the dashboard data JSON-RPC endpoint"""
        self.authenticate('admin', 'admin')
        
        # Fire request to the jsonrpc route
        response = self.url_open(
            '/web/home_dashboard/data',
            data=json.dumps({
                "jsonrpc": "2.0",
                "method": "call",
                "params": {},
                "id": 1
            }),
            headers={"Content-Type": "application/json"}
        )
        
        self.assertEqual(response.status_code, 200, "Dashboard route should return 200 OK")
        res_data = response.json()
        
        self.assertIn('result', res_data, "Response should have a RPC result")
        
        result = res_data['result']
        self.assertIn('config', result)
        self.assertIn('user', result)
        self.assertIn('modules', result)
        self.assertEqual(result['user']['id'], self.user.id)
        
    def test_02_theme_config_endpoint(self):
        """Verify the payload configurations to ensure themes load appropriately."""
        self.authenticate('admin', 'admin')
        
        response = self.url_open(
            '/web/home_dashboard/data',
            data=json.dumps({
                "jsonrpc": "2.0",
                "method": "call",
                "params": {},
                "id": 2
            }),
            headers={"Content-Type": "application/json"}
        )
        res_data = response.json()
        result = res_data['result']
        config = result['config']
        
        self.assertIn('dashboard_theme', config)
        self.assertIn('theme_mode', config)
        self.assertTrue(config.get('show_stats_row'))
