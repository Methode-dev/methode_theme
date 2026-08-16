from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestResCompany(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def test_default_theme_settings(self):
        """Test default theme settings for a company."""
        # Create a new company to test defaults
        company = self.env['res.company'].create({'name': 'Test Theme Company'})
        self.assertEqual(company.tbt_brand_color, '#242424')
        self.assertEqual(company.tbt_sidebar_dark_color, '#1E2433')
        self.assertEqual(company.tbt_topbar_bg, '#ffffff')
        self.assertEqual(company.tbt_content_bg, '#f6f6f6')

    def test_hex_color_validation(self):
        """Test validation for hex colors."""
        with self.assertRaises(ValidationError):
            self.company.write({'tbt_brand_color': 'invalid'})
        
        with self.assertRaises(ValidationError):
            self.company.write({'tbt_brand_color': '#12345'})

        # valid ones should not raise
        self.company.write({'tbt_brand_color': '#00ff00'})
        self.assertEqual(self.company.tbt_brand_color, '#00ff00')

    def test_compute_tbt_brand_palette(self):
        """Test the computation of related brand colors"""
        self.company.write({'tbt_brand_color': '#ff0000'})
        # Should be rgb triplet
        self.assertEqual(self.company.tbt_brand_color_rgb, '255,0,0')
        # Darkened color should be correctly computed (we don't need exact match unless we check the factor)
        self.assertTrue(self.company.tbt_brand_color_dark.startswith('#'))
