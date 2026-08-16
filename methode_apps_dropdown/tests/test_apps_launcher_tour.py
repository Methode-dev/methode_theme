from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestAppsLauncherTour(HttpCase):

    def test_apps_launcher_tour(self):
        """Renders, groups, pins without navigating, and navigates on tile click."""
        self.start_tour('/odoo', 'methode_apps_launcher_tour', login='admin')

    def test_favorite_persists_across_reload(self):
        """The pin written by the first tour must survive a full page reload,
        i.e. it really went through res.users.settings and came back in
        session_info."""
        self.start_tour('/odoo', 'methode_apps_launcher_tour', login='admin')
        self.start_tour(
            '/odoo', 'methode_apps_launcher_favorite_persisted_tour', login='admin',
        )
