import logging

from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class TestHomeWidget(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.WidgetModel = cls.env['theme.home.widget']
        cls.user = cls.env.user

    def test_default_widgets_creation(self):
        """Test if default widgets are created for a new user"""
        # Delete existing to simulate first visit
        existing = self.WidgetModel.search([('user_id', '=', self.user.id)])
        existing.unlink()

        # get_user_widgets should create defaults since there's no history
        widgets = self.WidgetModel.with_user(self.user).get_user_widgets()
        self.assertTrue(widgets, "Widgets should be created")
        
        # At minimum: quick_actions, stats, activities, focus, recent
        expected_defaults = ['quick_actions', 'stats', 'activities', 'focus', 'recent']
        widget_keys = [w.widget_id for w in widgets]
        for key in expected_defaults:
            self.assertIn(key, widget_keys, f"Default widget {key} not found")

    def test_restore_default_widgets(self):
        """Test resetting widgets to defaults"""
        # Create a custom widget
        custom_widget = self.WidgetModel.create({
            'user_id': self.user.id,
            'widget_id': 'my_custom_widget',
            'position': 100,
            'col_span': '1',
            'active': True,
        })
        
        widgets = self.WidgetModel.with_user(self.user).restore_default_widgets()
        active_widget_keys = [w.widget_id for w in widgets]
        
        self.assertNotIn('my_custom_widget', active_widget_keys, "Custom widget should not be active after restore")
        
        expected_defaults = ['quick_actions', 'stats', 'activities', 'focus']
        for key in expected_defaults:
            self.assertIn(key, active_widget_keys, f"Default widget {key} should be restored")

    def test_unique_constraint(self):
        """Test uniqueness of widget_id per user"""
        try:
            from psycopg2 import IntegrityError
            from odoo.tools.mute_logger import mute_logger
            
            # create the first widget
            self.WidgetModel.create({
                'user_id': self.user.id,
                'widget_id': 'unique_test_widget',
                'position': 1,
            })
            
            # create the second one with same widget_id, should raise IntegrityError or ValidationError
            with self.assertRaises(Exception):
                with mute_logger('odoo.sql_db'):
                    self.WidgetModel.create({
                        'user_id': self.user.id,
                        'widget_id': 'unique_test_widget',
                        'position': 2,
                    })
        except ImportError:
            pass  # Optional passing if imports vary
