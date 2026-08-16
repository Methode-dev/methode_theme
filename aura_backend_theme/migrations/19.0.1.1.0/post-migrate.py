# -*- coding: utf-8 -*-
"""Seed the Méthode palette onto companies that predate it (THEME_PLAN §9.2).

Changing ``default=`` on a field only affects rows created afterwards, so
without this every existing company keeps Aura's slate/grey palette.  Because
``theme_bootstrap.js`` writes those stored values as inline styles on
``<html>``, and inline custom properties beat every stylesheet rule, a stale
row silently defeats the whole brand with no error to explain why.

Only rows still holding Aura's *old default* are rewritten.  A colour someone
deliberately changed is left alone — this migration is not entitled to discard
a customer's customisation, and it stays idempotent on re-run.
"""

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# field -> (old Aura default, new Méthode default)
PALETTE_MIGRATION = {
    'tbt_brand_color': ('#242424', '#FAA140'),
    'tbt_topbar_bg': ('#ffffff', '#E9DBCA'),
    'tbt_topbar_text': ('#0c0f0f', '#000000'),
    'tbt_content_bg': ('#f6f6f6', '#FDFAF6'),
    'tbt_card_bg': ('#ffffff', '#FFFFFF'),
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].sudo().search([])
    if not companies:
        return

    migrated = 0
    for company in companies:
        values = {}
        for fname, (old_default, new_default) in PALETTE_MIGRATION.items():
            current = (company[fname] or '').strip()
            # NULL/empty rows fall through to the new default too: they would
            # otherwise hit the hardcoded fallbacks in ir_http.py.
            if not current or current.lower() == old_default.lower():
                if current != new_default:
                    values[fname] = new_default
        if values:
            company.write(values)
            migrated += 1

    # tbt_brand_color feeds a stored compute (brand_rgb, brand_dark, the whole
    # sidebar ramp).  write() triggers it, but companies whose brand colour was
    # customised never got written above and may still hold a NULL ramp from an
    # install that predated the field.
    companies._compute_tbt_brand_palette()
    companies.flush_recordset()

    _logger.info(
        "Méthode palette seeded on %s/%s companies (customised colours preserved)",
        migrated, len(companies),
    )
