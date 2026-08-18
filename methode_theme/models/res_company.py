from odoo import fields, models

# HOMEPAGE_DASHBOARD_PLAN §2.4: "Thresholds are configuration, not constants — a
# business with 90-day terms does not want a 30-day alarm."  These are the
# defaults, not the rule.
DEFAULT_OVERDUE_DAYS = 30
DEFAULT_STALLED_DAYS = 7


class ResCompany(models.Model):
    """Company-level thresholds for the dashboard's insight banners.

    On the company rather than per user: "when is a receivable late" is a
    property of how the business bills, not of who is looking at the screen.
    """

    _inherit = 'res.company'

    methode_dashboard_overdue_days = fields.Integer(
        string="Overdue Invoice Alert (days)",
        default=DEFAULT_OVERDUE_DAYS,
        help="An unpaid customer invoice raises a dashboard banner once it is "
             "this many days past its due date.")
    methode_dashboard_stalled_days = fields.Integer(
        string="Stalled Deal Alert (days)",
        default=DEFAULT_STALLED_DAYS,
        help="An open opportunity with no update for this many days raises a "
             "dashboard banner.")
