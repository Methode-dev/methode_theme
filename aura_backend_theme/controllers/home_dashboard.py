# -*- coding: utf-8 -*-
import logging
from collections import defaultdict
from datetime import date, timedelta, datetime
from odoo import _, http
from odoo.http import request

from .home_widgets import (
    _fetch_hr_attendance,
    _fetch_hr_leaves,
    _fetch_inventory_receipts,
    _fetch_inventory_reorder,
    _fetch_mrp_production,
    _fetch_project_deadlines,
    _fetch_project_tasks,
    _fetch_sale_quotations,
    _fetch_sale_to_invoice,
    _fetch_account_cashflow,
    _fetch_account_aged_receivables,
)

_logger = logging.getLogger(__name__)

ALLOWED_THEME_MODES = {'auto', 'manual'}


def _list_action(name, model, domain=None, context=None, views=None):
    return {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': model,
        'views': views or [[False, 'list'], [False, 'form']],
        'domain': domain or [],
        'context': context or {},
        'target': 'current',
    }


def _form_action(name, model, res_id):
    return {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': model,
        'res_id': res_id,
        'views': [[False, 'form']],
        'target': 'current',
    }


def _create_action(name, model, context=None):
    return {
        'type': 'ir.actions.act_window',
        'name': name,
        'res_model': model,
        'views': [[False, 'form']],
        'context': context or {},
        'target': 'current',
    }


class HomeDashboardController(http.Controller):

    def _get_installed_modules(self):
        mods = request.env['ir.module.module'].sudo().search([('state', '=', 'installed')])
        return {m.name for m in mods}

    def _get_effective_theme(self, config_rec):
        theme_mode = config_rec.theme_mode or 'auto'
        if theme_mode not in ALLOWED_THEME_MODES:
            theme_mode = 'auto'
        dashboard_theme = 'aura'
        color_scheme = (request.httprequest.cookies.get('color_scheme') or '').strip().lower()
        is_dark = color_scheme == 'dark'
        effective_theme_mode = 'dark' if (theme_mode == 'auto' and is_dark) else 'bright'
        effective_theme_name = dashboard_theme
        return {
            'theme_mode': theme_mode,
            'dashboard_theme': dashboard_theme,
            'effective_theme_mode': effective_theme_mode,
            'effective_theme_name': effective_theme_name,
        }

    @http.route('/web/home_dashboard/data', type='jsonrpc', auth='user')
    def get_dashboard_data(self):
        env = request.env
        uid = env.uid
        config_rec = env['theme.home.dashboard.config'].get_or_create_for_user()
        theme_meta = self._get_effective_theme(config_rec)

        config = {
            'show_stats_row': config_rec.show_stats_row,
            'show_activities': config_rec.show_activities,
            'show_invoices': config_rec.show_invoices,
            'show_pipeline': config_rec.show_pipeline,
            'show_recent': config_rec.show_recent,
            'show_shortcuts': config_rec.show_shortcuts,
            'invoice_limit': config_rec.invoice_limit,
            'invoice_filter': config_rec.invoice_filter,
            'activity_limit': config_rec.activity_limit,
            'pipeline_stages_limit': config_rec.pipeline_stages_limit,
            'recent_limit': config_rec.recent_limit,
            'layout_density': config_rec.layout_density,
            'dashboard_theme': theme_meta['dashboard_theme'],
            'theme_mode': theme_meta['theme_mode'],
            'effective_theme_mode': theme_meta['effective_theme_mode'],
            'effective_theme_name': theme_meta['effective_theme_name'],
            'stats_modules': config_rec.stats_modules or '',
            'shortcut_ids': config_rec.shortcut_ids.ids,
        }

        user = env['res.users'].browse(uid)
        user_data = {
            'id': uid,
            'name': user.name,
            'avatar_url': f'/web/image/res.users/{uid}/avatar_128',
            'company_name': user.company_id.name,
            'lang': user.lang or 'en_US',
        }

        # Single query to check all required modules at once.
        installed = self._get_installed_modules()
        has_account = 'account' in installed
        has_crm = 'crm' in installed
        has_sale = 'sale' in installed
        has_project = 'project' in installed
        has_stock = 'stock' in installed
        has_hr = 'hr_holidays' in installed or 'hr_attendance' in installed
        has_mrp = 'mrp' in installed

        stats = self._get_stats(uid, config, has_account, has_crm, has_sale, has_project, has_stock, has_hr, has_mrp)
        activities = self._get_activities(uid, config) if config['show_activities'] else None
        invoices = self._get_invoices(uid, config, has_account) if config['show_invoices'] else None
        pipeline = self._get_pipeline(uid, config, has_crm) if config['show_pipeline'] else None
        recent = self._get_recent(uid, config, has_account, has_crm, has_sale, has_project) if config['show_recent'] else None
        shortcuts = self._get_shortcuts(config_rec) if config['show_shortcuts'] else None
        insights = self._get_insights(uid, has_account, has_crm)
        quick_actions = self._get_quick_actions(has_account, has_crm, has_sale, has_project)

        return {
            'config': config,
            'user': user_data,
            'stats': stats,
            'activities': activities,
            'invoices': invoices,
            'pipeline': pipeline,
            'recent': recent,
            'shortcuts': shortcuts,
            'insights': insights,
            'quick_actions': quick_actions,
            'modules': {
                'account': has_account,
                'crm': has_crm,
                'sale': has_sale,
                'project': has_project,
                'stock': has_stock,
                'hr': has_hr,
                'mrp': has_mrp,
            },
        }

    def _get_stats(self, uid, config, has_account, has_crm, has_sale, has_project, has_stock, has_hr, has_mrp):
        env = request.env
        today = date.today()
        first_this_month = today.replace(day=1)
        first_last_month = (first_this_month - timedelta(days=1)).replace(day=1)
        company_currency = env.company.currency_id

        stats = {
            'open_invoices_amount': 0.0,
            'open_invoices_count': 0,
            'open_invoices_trend': None,
            'overdue_bills_amount': 0.0,
            'overdue_bills_count': 0,
            'activities_due_today': 0,
            'activities_overdue': 0,
            'pipeline_value': None,
            'pipeline_delta_pct': None,
            'cards': {},
        }

        if has_account:
            Move = env['account.move']
            inv_domain = [
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_user_id', '=', uid),
            ]
            [(inv_amount, inv_count)] = Move._read_group(inv_domain, [], ['amount_residual:sum', '__count'])
            stats['open_invoices_amount'] = inv_amount or 0.0
            stats['open_invoices_count'] = inv_count

            this_month_count = Move.search_count(inv_domain + [
                ('invoice_date', '>=', str(first_this_month))
            ])
            last_month_count = Move.search_count(inv_domain + [
                ('invoice_date', '>=', str(first_last_month)),
                ('invoice_date', '<', str(first_this_month)),
            ])
            if last_month_count:
                stats['open_invoices_trend'] = round((this_month_count - last_month_count) / last_month_count * 100, 1)

            # Overdue bills are scoped to currently selected companies.
            bill_domain = [
                ('company_id', 'in', env.companies.ids),
                ('move_type', '=', 'in_invoice'),
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', str(today)),
            ]
            [(bill_amount, bill_count)] = Move._read_group(bill_domain, [], ['amount_residual:sum', '__count'])
            stats['overdue_bills_amount'] = bill_amount or 0.0
            stats['overdue_bills_count'] = bill_count

            cashflow = _fetch_account_cashflow(env, uid)
            aged = _fetch_account_aged_receivables(env, uid)
            inv_count = stats['open_invoices_count']
            bill_count = stats['overdue_bills_count']
            stats['cards']['invoices_open'] = {
                'value': stats['open_invoices_amount'],
                'meta': _('%(n)d facture', n=inv_count) if inv_count == 1 else _('%(n)d factures', n=inv_count),
                'label': _('Factures ouvertes'),
                'color': 'blue',
                'icon': 'fa-file-invoice-dollar',
                'viewUrl': '/odoo/accounting/customer-invoices',
                'createUrl': '/odoo/accounting/customer-invoices/new',
                'viewAction': _list_action(_('Factures ouvertes'), 'account.move', inv_domain),
                'createAction': _create_action(_('Nouvelle facture'), 'account.move', {'default_move_type': 'out_invoice'}),
                'trend': stats['open_invoices_trend'],
                'monetary': True,
                'currency_symbol': company_currency.symbol or '',
                'currency_position': company_currency.position or 'before',
            }
            stats['cards']['bills_overdue'] = {
                'value': stats['overdue_bills_amount'],
                'meta': _('%(n)d facture fournisseur', n=bill_count) if bill_count == 1 else _('%(n)d factures fournisseurs', n=bill_count),
                'label': _('Factures fournisseurs en retard'),
                'color': 'red',
                'icon': 'fa-exclamation-triangle',
                'viewUrl': '/odoo/accounting/vendor-bills',
                'createUrl': None,
                'viewAction': _list_action(_('Factures fournisseurs en retard'), 'account.move', bill_domain),
                'createAction': None,
                'trend': None,
                'monetary': True,
                'currency_symbol': company_currency.symbol or '',
                'currency_position': company_currency.position or 'before',
            }
            stats['cards']['accounting_cashflow'] = {
                'value': cashflow.get('net', 0.0),
                'meta': _('Banque %(sym)s%(bal)d', sym=cashflow.get('currency_symbol', ''), bal=cashflow.get('bank_balance', 0.0)),
                'label': _('Trésorerie'),
                'color': 'green',
                'icon': 'fa-sack-dollar',
                'viewUrl': '/web#model=account.move&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Trésorerie'), 'account.move'),
                'createAction': None,
                'trend': None,
                'monetary': True,
                'currency_symbol': cashflow.get('currency_symbol', '') or company_currency.symbol or '',
                'currency_position': company_currency.position or 'before',
            }
            aged_total = sum(bucket.get('amount', 0.0) for bucket in aged.get('buckets', []))
            stats['cards']['accounting_aged_receivables'] = {
                'value': aged.get('count', 0),
                'meta': _('%(sym)s%(amt)d à recevoir', sym=aged.get('currency_symbol', ''), amt=aged_total),
                'label': _('Créances anciennes'),
                'color': 'red',
                'icon': 'fa-file-invoice-dollar',
                'viewUrl': '/web#model=account.move&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Créances anciennes'), 'account.move', [
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('invoice_user_id', '=', uid),
                ]),
                'createAction': None,
                'trend': None,
            }

        Activity = env['mail.activity']
        stats['activities_due_today'] = Activity.search_count([
            ('user_id', '=', uid), ('date_deadline', '=', str(today)),
        ])
        stats['activities_overdue'] = Activity.search_count([
            ('user_id', '=', uid), ('date_deadline', '<', str(today)),
        ])

        if has_crm:
            Lead = env['crm.lead']
            base_domain = [
                ('user_id', '=', uid),
                ('type', '=', 'opportunity'),
                ('active', '=', True),
                ('probability', '<', 100),
            ]
            this_group = Lead._read_group(base_domain, [], ['expected_revenue:sum'])
            this_val = this_group[0][0] if this_group else 0.0
            stats['pipeline_value'] = this_val or 0.0

            last_domain = base_domain + [
                ('date_deadline', '>=', str(first_last_month)),
                ('date_deadline', '<', str(first_this_month)),
            ]
            last_group = Lead._read_group(last_domain, [], ['expected_revenue:sum'])
            last_val = last_group[0][0] if last_group else 0.0
            last_val = last_val or 0.0
            if last_val:
                delta = (stats['pipeline_value'] - last_val) / last_val * 100
                stats['pipeline_delta_pct'] = round(delta, 1)

        act_total = stats['activities_due_today'] + stats['activities_overdue']
        act_overdue = stats['activities_overdue']
        stats['cards']['activities_due'] = {
            'value': act_total,
            'meta': (_('%(n)d en retard', n=act_overdue) if act_overdue > 0
                     else _('%(n)d dues aujourd’hui', n=stats['activities_due_today'])),
            'label': _('Mes activités'),
            'color': 'orange',
            'icon': 'fa-calendar-check',
            'viewUrl': '/odoo/todos',
            'createUrl': None,
            'viewAction': _list_action(_('Mes activités'), 'mail.activity', [
                ('user_id', '=', uid),
                ('date_deadline', '<=', str(today)),
            ]),
            'createAction': None,
            'trend': None,
        }
        pipeline_delta = stats['pipeline_delta_pct']
        stats['cards']['pipeline_value'] = {
            'value': stats['pipeline_value'] if stats['pipeline_value'] is not None else 0.0,
            'meta': (_('%(delta)+.1f%% vs mois dernier', delta=pipeline_delta) if pipeline_delta is not None
                     else _('Aucune donnée CRM')),
            'label': _('Pipeline'),
            'color': 'green',
            'icon': 'fa-chart-line',
            'viewUrl': '/odoo/crm',
            'createUrl': '/odoo/crm/new',
            'viewAction': _list_action(_('Mon pipeline'), 'crm.lead', base_domain if has_crm else []),
            'createAction': _create_action(_('Nouvelle piste'), 'crm.lead', {'default_type': 'opportunity'}),
            'trend': pipeline_delta,
            'monetary': True,
            'currency_symbol': company_currency.symbol or '',
            'currency_position': company_currency.position or 'before',
        }

        if has_stock:
            reorder = _fetch_inventory_reorder(env, uid)
            receipts = _fetch_inventory_receipts(env, uid)
            stats['cards']['inventory_reorder'] = {
                'value': reorder.get('count', 0),
                'meta': _('Produits au niveau ou sous le stock minimum'),
                'label': _('Alertes de réapprovisionnement'),
                'color': 'orange',
                'icon': 'fa-boxes',
                'viewUrl': '/odoo/inventory/products',
                'createUrl': None,
                'viewAction': _list_action(_('Produits à réapprovisionner'), 'stock.warehouse.orderpoint'),
                'createAction': None,
                'trend': None,
            }
            stats['cards']['inventory_receipts'] = {
                'value': receipts.get('count', 0),
                'meta': _('Réceptions à venir'),
                'label': _('Réceptions en attente'),
                'color': 'blue',
                'icon': 'fa-truck',
                'viewUrl': '/odoo/inventory/receipts',
                'createUrl': None,
                'viewAction': _list_action(_('Réceptions en attente'), 'stock.picking', [
                    ('picking_type_code', '=', 'incoming'),
                    ('state', '=', 'assigned'),
                ]),
                'createAction': None,
                'trend': None,
            }

        if has_sale:
            quotations = _fetch_sale_quotations(env, uid)
            to_invoice = _fetch_sale_to_invoice(env, uid)
            stats['cards']['sales_quotations'] = {
                'value': quotations.get('count', 0),
                'meta': _('Devis brouillons et envoyés'),
                'label': _('Devis'),
                'color': 'blue',
                'icon': 'fa-file-alt',
                'viewUrl': '/odoo/sales',
                'createUrl': '/odoo/sales/new',
                'viewAction': _list_action(_('Devis'), 'sale.order', [
                    ('state', 'in', ['draft', 'sent']),
                    ('user_id', '=', uid),
                ]),
                'createAction': _create_action(_('Nouveau devis'), 'sale.order'),
                'trend': None,
            }
            stats['cards']['sales_to_invoice'] = {
                'value': to_invoice.get('count', 0),
                'meta': _('Commandes confirmées à facturer'),
                'label': _('Commandes à facturer'),
                'color': 'green',
                'icon': 'fa-file-invoice',
                'viewUrl': '/odoo/sales',
                'createUrl': None,
                'viewAction': _list_action(_('Commandes à facturer'), 'sale.order', [
                    ('invoice_status', '=', 'to invoice'),
                    ('user_id', '=', uid),
                ]),
                'createAction': None,
                'trend': None,
            }

        if has_project:
            tasks = _fetch_project_tasks(env, uid)
            deadlines = _fetch_project_deadlines(env, uid)
            stats['cards']['project_tasks'] = {
                'value': tasks.get('count', 0),
                'meta': _('Tâches ouvertes qui vous sont assignées'),
                'label': _('Mes tâches'),
                'color': 'green',
                'icon': 'fa-tasks',
                'viewUrl': '/web#model=project.task&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Mes tâches'), 'project.task', [
                    ('user_ids', 'in', [uid]),
                    ('stage_id.fold', '=', False),
                ]),
                'createAction': None,
                'trend': None,
            }
            stats['cards']['project_deadlines'] = {
                'value': deadlines.get('count', 0),
                'meta': _('Tâches dues sous 7 jours'),
                'label': _('Échéances'),
                'color': 'orange',
                'icon': 'fa-hourglass-half',
                'viewUrl': '/web#model=project.task&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Échéances projet'), 'project.task', [
                    ('user_ids', 'in', [uid]),
                    ('stage_id.fold', '=', False),
                    ('date_deadline', '>=', str(today)),
                    ('date_deadline', '<=', str(today + timedelta(days=7))),
                ]),
                'createAction': None,
                'trend': None,
            }

        if has_hr:
            leaves = _fetch_hr_leaves(env, uid)
            attendance = _fetch_hr_attendance(env, uid)
            stats['cards']['hr_leaves'] = {
                'value': leaves.get('count', 0),
                'meta': _('Demandes de congé à valider'),
                'label': _('Demandes de congé'),
                'color': 'orange',
                'icon': 'fa-calendar-minus',
                'viewUrl': '/web#model=hr.leave&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Demandes de congé'), 'hr.leave', [('state', '=', 'confirm')]),
                'createAction': None,
                'trend': None,
            }
            stats['cards']['hr_attendance'] = {
                'value': attendance.get('count', 0),
                'meta': _('Présences du jour'),
                'label': _('Présences du jour'),
                'color': 'blue',
                'icon': 'fa-user-clock',
                'viewUrl': '/web#model=hr.attendance&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Présences du jour'), 'hr.attendance', [
                    ('check_in', '>=', str(today)),
                    ('check_in', '<', str(today + timedelta(days=1))),
                ]),
                'createAction': None,
                'trend': None,
            }

        if has_mrp:
            production = _fetch_mrp_production(env, uid)
            stats['cards']['mrp_production'] = {
                'value': production.get('count', 0),
                'meta': _('Ordres de fabrication en cours'),
                'label': _('Ordres de fabrication'),
                'color': 'purple',
                'icon': 'fa-industry',
                'viewUrl': '/web#model=mrp.production&view_type=list',
                'createUrl': None,
                'viewAction': _list_action(_('Ordres de fabrication'), 'mrp.production', [
                    ('state', 'in', ['confirmed', 'progress']),
                ]),
                'createAction': None,
                'trend': None,
            }

        return stats

    def _get_activities(self, uid, config):
        today = date.today()
        activities = request.env['mail.activity'].search(
            [('user_id', '=', uid)],
            order='date_deadline asc',
            limit=config['activity_limit']
        )
        result = []
        for act in activities:
            deadline = act.date_deadline
            days_overdue = (today - deadline).days if deadline else 0
            result.append({
                'id': act.id,
                'activity_type_name': act.activity_type_id.name or '',
                'activity_type_icon': act.activity_type_id.icon or 'fa-tasks',
                'summary': act.summary or '',
                'note': act.note or '',
                'date_deadline': str(deadline) if deadline else '',
                'days_overdue': days_overdue,
                'res_model': act.res_model or '',
                'res_id': act.res_id,
                'res_name': act.res_name or '',
                'record_url': f'/odoo/{act.res_model}/{act.res_id}' if act.res_model and act.res_id else '#',
                'action': _form_action(act.res_name or _('Enregistrement'), act.res_model, act.res_id) if act.res_model and act.res_id else None,
            })
        return result

    def _get_invoices(self, uid, config, has_account):
        if not has_account:
            return None
        today = date.today()
        first_month = today.replace(day=1)
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('invoice_user_id', '=', uid),
            ('state', 'not in', ['cancel']),
        ]
        invoice_filter = config.get('invoice_filter', 'all')
        if invoice_filter == 'overdue':
            domain += [
                ('state', '=', 'posted'),
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', str(today)),
            ]
        elif invoice_filter == 'this_month':
            domain += [('invoice_date', '>=', str(first_month))]

        moves = request.env['account.move'].search(
            domain, order='amount_total desc', limit=config['invoice_limit']
        )
        result = []
        for move in moves:
            due = move.invoice_date_due
            is_overdue = due and due < today and move.payment_state in ('not_paid', 'partial')
            days_overdue = (today - due).days if is_overdue and due else 0
            if move.payment_state == 'paid':
                status_label = 'Paid'
            elif is_overdue:
                status_label = 'Overdue'
            elif move.state == 'draft':
                status_label = 'Draft'
            else:
                status_label = 'Posted'

            result.append({
                'id': move.id,
                'name': move.name or '',
                'partner_name': move.partner_id.name or '',
                'amount_total': move.amount_total,
                'amount_residual': move.amount_residual,
                'currency_symbol': move.currency_id.symbol or '',
                'invoice_date_due': str(due) if due else '',
                'days_overdue': days_overdue,
                'state': move.state,
                'payment_state': move.payment_state or '',
                'status_label': status_label,
                'record_url': f'/odoo/accounting/customer-invoices/{move.id}',
                'action': _form_action(move.display_name or _('Facture'), 'account.move', move.id),
            })
        return result

    def _get_pipeline(self, uid, config, has_crm):
        if not has_crm:
            return None
        today = date.today()
        Lead = request.env['crm.lead']
        domain = [
            ('user_id', '=', uid),
            ('type', '=', 'opportunity'),
            ('active', '=', True),
            ('probability', '<', 100),
        ]
        stage_groups = Lead._read_group(
            domain,
            ['stage_id'],
            ['expected_revenue:sum', '__count'],
            order='stage_id asc',
            limit=config['pipeline_stages_limit'],
        )
        if not stage_groups:
            return []

        stage_ids = [stage.id for (stage, _rev, _cnt) in stage_groups if stage]

        # Single query for all leads across all stages (no N+1).
        all_leads = Lead.search(
            domain + [('stage_id', 'in', stage_ids)],
            order='stage_id asc, expected_revenue desc',
        )
        leads_by_stage = defaultdict(list)
        for lead in all_leads:
            leads_by_stage[lead.stage_id.id].append(lead)

        result = []
        for (stage, rev_sum, count) in stage_groups:
            stage_id = stage.id if stage else None
            stage_name = stage.name if stage else _('Inconnu')
            stage_leads = leads_by_stage.get(stage_id, [])[:5]
            leads_data = []
            for lead in stage_leads:
                days_in_stage = (today - lead.write_date.date()).days if lead.write_date else 0
                leads_data.append({
                    'id': lead.id,
                    'name': lead.name or '',
                    'expected_revenue': lead.expected_revenue,
                    'currency_symbol': lead.company_currency.symbol or '',
                    'priority': lead.priority or '0',
                    'partner_name': lead.partner_id.name or '',
                    'days_in_stage': days_in_stage,
                    'record_url': f'/odoo/crm/{lead.id}',
                    'action': _form_action(lead.display_name or _('Opportunité'), 'crm.lead', lead.id),
                })
            result.append({
                'stage_id': stage_id,
                'stage_name': stage_name,
                'leads': leads_data,
                'total_value': rev_sum or 0.0,
                'count': count,
            })
        return result

    def _get_recent(self, uid, config, has_account, has_crm, has_sale, has_project):
        env = request.env
        recent = []

        def _fetch(model, url_prefix=''):
            if not env['ir.model'].sudo().search_count([('model', '=', model)]):
                return
            try:
                records = env[model].search(
                    [('write_uid', '=', uid)],
                    order='write_date desc',
                    limit=3
                )
                model_label = env['ir.model'].sudo().search([('model', '=', model)], limit=1).name or model
                for rec in records:
                    recent.append({
                        'model': model,
                        'model_description': model_label,
                        'res_id': rec.id,
                        'display_name': rec.display_name or '',
                        'last_opened': str(rec.write_date) if rec.write_date else '',
                        'record_url': f'{url_prefix}/{rec.id}' if url_prefix else f'/odoo/{model}/{rec.id}',
                        'action': _form_action(rec.display_name or model_label, model, rec.id),
                    })
            except Exception:
                _logger.warning('Failed to fetch recent records for model %s', model, exc_info=True)

        if has_account:
            _fetch('account.move', url_prefix='/odoo/accounting/customer-invoices')
        if has_crm:
            _fetch('crm.lead', url_prefix='/odoo/crm')
        if has_sale:
            _fetch('sale.order', url_prefix='/odoo/sales')
        if has_project:
            _fetch('project.task', url_prefix='/web#model=project.task&view_type=form&id')

        recent.sort(key=lambda r: r['last_opened'], reverse=True)
        return recent[:config['recent_limit']]

    def _get_shortcuts(self, config_rec):
        result = []
        for menu in config_rec.shortcut_ids:
            action = menu.action
            action_str = f'{action._name},{action.id}' if action else ''
            result.append({
                'id': menu.id,
                'name': menu.name or '',
                'action': action_str,
                'icon_class': menu.web_icon or 'fa fa-th',
            })
        return result

    def _get_insights(self, uid, has_account, has_crm):
        env = request.env
        today = date.today()
        insights = []

        if has_crm:
            stuck_cutoff = datetime.now() - timedelta(days=7)
            try:
                stuck = env['crm.lead'].search_count([
                    ('user_id', '=', uid),
                    ('type', '=', 'opportunity'),
                    ('active', '=', True),
                    ('probability', '<', 100),
                    ('write_date', '<', stuck_cutoff.strftime('%Y-%m-%d %H:%M:%S')),
                ])
                if stuck:
                    insights.append({
                        'type': 'warning',
                        'icon': 'fa-clock',
                        'message': _('%(n)d affaire sans mise à jour depuis plus de 7 jours', n=stuck) if stuck == 1
                                   else _('%(n)d affaires sans mise à jour depuis plus de 7 jours', n=stuck),
                        'action_label': _('Voir le pipeline'),
                        'action_url': '/odoo/crm',
                        'action': _list_action(_('Opportunités manquées'), 'crm.lead', [
                            ('user_id', '=', uid),
                            ('type', '=', 'opportunity'),
                            ('active', '=', True),
                            ('probability', '<', 100),
                            ('write_date', '<', stuck_cutoff.strftime('%Y-%m-%d %H:%M:%S')),
                        ]),
                    })
            except Exception:
                _logger.warning('Failed to compute stuck CRM leads insight', exc_info=True)

        if has_account:
            cutoff_30 = today - timedelta(days=30)
            try:
                long_overdue = env['account.move'].search_count([
                    ('move_type', '=', 'out_invoice'),
                    ('invoice_user_id', '=', uid),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('invoice_date_due', '<', str(cutoff_30)),
                ])
                if long_overdue:
                    insights.append({
                        'type': 'danger',
                        'icon': 'fa-exclamation-circle',
                        'message': _('%(n)d facture en retard de plus de 30 jours', n=long_overdue) if long_overdue == 1
                                   else _('%(n)d factures en retard de plus de 30 jours', n=long_overdue),
                        'action_label': _('Voir les factures'),
                        'action_url': '/odoo/accounting/customer-invoices',
                        'action': _list_action(_('Factures en retard de plus de 30 jours'), 'account.move', [
                            ('move_type', '=', 'out_invoice'),
                            ('invoice_user_id', '=', uid),
                            ('state', '=', 'posted'),
                            ('payment_state', 'in', ['not_paid', 'partial']),
                            ('invoice_date_due', '<', str(cutoff_30)),
                        ]),
                    })
            except Exception:
                _logger.warning('Failed to compute overdue invoices insight', exc_info=True)

        return insights

    def _get_quick_actions(self, has_account, has_crm, has_sale, has_project):
        actions = []
        if has_account:
            actions.append({
                'label': _('Nouvelle facture'),
                'icon': 'fa-file-invoice-dollar',
                'url': '/odoo/accounting/customer-invoices/new',
                'action': _create_action(_('Nouvelle facture'), 'account.move', {'default_move_type': 'out_invoice'}),
                'color': 'blue',
            })
        if has_crm:
            actions.append({
                'label': _('Nouvelle piste'),
                'icon': 'fa-bullseye',
                'url': '/odoo/crm/new',
                'action': _create_action(_('Nouvelle piste'), 'crm.lead', {'default_type': 'opportunity'}),
                'color': 'green',
            })
        if has_sale:
            actions.append({
                'label': _('Nouvelle commande'),
                'icon': 'fa-shopping-cart',
                'url': '/odoo/sales/new',
                'action': _create_action(_('Nouvelle commande'), 'sale.order'),
                'color': 'purple',
            })
        if has_project:
            actions.append({
                'label': _('Nouvelle tâche'),
                'icon': 'fa-tasks',
                'url': '/odoo/project',
                'action': _create_action(_('Nouvelle tâche'), 'project.task'),
                'color': 'orange',
            })
        actions.append({
            'label': _('Mes activités'),
            'icon': 'fa-calendar-check',
            'url': '/odoo/todos',
            'action': _list_action(_('Mes activités'), 'mail.activity', [('user_id', '=', request.env.uid)]),
            'color': 'teal',
        })
        return actions

    @http.route('/web/home_dashboard/save_config', type='jsonrpc', auth='user')
    def save_config(self, values=None):
        if not values:
            return {'success': False}
        config = request.env['theme.home.dashboard.config'].get_or_create_for_user()
        safe_fields = {
            'show_stats_row', 'show_activities', 'show_invoices', 'show_pipeline',
            'show_recent', 'show_shortcuts', 'invoice_limit', 'invoice_filter',
            'activity_limit', 'pipeline_stages_limit', 'recent_limit',
            'layout_density', 'theme_mode', 'stats_modules', 'shortcut_ids',
        }
        filtered = {k: v for k, v in values.items() if k in safe_fields}
        if 'theme_mode' in filtered and filtered['theme_mode'] not in ALLOWED_THEME_MODES:
            filtered.pop('theme_mode')
        if filtered:
            config.write(filtered)
        return {'success': True}
